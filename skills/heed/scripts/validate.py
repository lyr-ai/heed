"""Validate Heed's outputs: format, evidence gates, and locators.

    python3 validate.py .heed/findings.json [--repo .]
    python3 validate.py --project .heed/project.json [--repo .]
    python3 validate.py --plan .heed/plan.json [--repo .]

Exit 0 when valid. Otherwise every problem is printed, one per line, and the
exit code is 1. The gates are the rules in SKILL.md: a priority must be
earned by evidence of the right level. Locators are checked against the repo:
the file exists and the line is in range, and the commit exists.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

PRIORITIES = ("urgent", "high", "medium", "watch")
LEVELS = ("confirmed", "observed", "inferred")
KINDS = ("code", "test", "todo", "issue", "git", "ci", "command", "doc", "reasoning")


def has_locator(e: dict) -> bool:
    return bool(e.get("file") or e.get("commit") or e.get("issue") or e.get("url")
                or ("command" in e and "exit_code" in e))


def check_locator(e: dict, repo: Path, where: str) -> list[str]:
    errs = []
    if e.get("file"):
        p = repo / e["file"]
        if not p.is_file():
            errs.append(f"{where}: file not found: {e['file']}")
        elif e.get("line") is not None:
            n = sum(1 for _ in p.open(errors="replace"))
            for key in ("line", "end_line"):
                v = e.get(key)
                if v is not None and not (isinstance(v, int) and 1 <= v <= n):
                    errs.append(f"{where}: {key} {v} out of range for {e['file']} ({n} lines)")
    if e.get("commit"):
        r = subprocess.run(["git", "cat-file", "-e", f"{e['commit']}^{{commit}}"], cwd=repo,
                           capture_output=True)
        if r.returncode != 0:
            errs.append(f"{where}: commit not found: {e['commit']}")
    if e.get("issue") is not None and not isinstance(e["issue"], int):
        errs.append(f"{where}: issue must be a number")
    if "command" in e and ("exit_code" not in e or "output" not in e):
        errs.append(f"{where}: command evidence needs exit_code and output")
    return errs


def validate(doc: dict, repo: Path) -> list[str]:
    errs: list[str] = []
    if doc.get("version") != 1:
        errs.append("version must be 1")
    area_ids = {a.get("id") for a in doc.get("areas", [])}
    seen = set()
    for i, f in enumerate(doc.get("findings", [])):
        w = f"finding {f.get('id', i)}"
        for key in ("id", "title", "area", "priority", "summary", "evidence"):
            if not f.get(key):
                errs.append(f"{w}: missing {key}")
        if f.get("id") in seen:
            errs.append(f"{w}: duplicate id")
        seen.add(f.get("id"))
        if f.get("area") and f["area"] not in area_ids:
            errs.append(f"{w}: area '{f['area']}' is not declared in areas")
        pr = f.get("priority")
        if pr not in PRIORITIES:
            errs.append(f"{w}: priority must be one of {PRIORITIES}")
        if not (f.get("impact") or f.get("why_now")):
            errs.append(f"{w}: give impact or why_now; a priority needs reasons")
        ev = f.get("evidence") or []
        for j, e in enumerate(ev):
            we = f"{w} evidence[{j}]"
            if e.get("level") not in LEVELS:
                errs.append(f"{we}: level must be one of {LEVELS}")
            if e.get("kind") not in KINDS:
                errs.append(f"{we}: kind must be one of {KINDS}")
            if not e.get("claim"):
                errs.append(f"{we}: missing claim")
            if e.get("level") in ("confirmed", "observed"):
                if not has_locator(e):
                    errs.append(f"{we}: {e['level']} evidence needs a locator (file/commit/issue/command/url)")
                errs += check_locator(e, repo, we)
        conf = [e for e in ev if e.get("level") == "confirmed"]
        obs = [e for e in ev if e.get("level") == "observed"]
        hard = conf + obs
        fm = bool((f.get("failure_mode") or "").strip())
        if not hard:
            errs.append(f"{w}: only inferred evidence; move it to not_promoted")
        elif pr == "urgent" and not conf:
            errs.append(f"{w}: urgent needs at least one confirmed item")
        elif pr == "high" and not (conf or len({e.get('kind') for e in obs}) >= 2):
            errs.append(f"{w}: high needs a confirmed item or observed items of 2+ different kinds")
        if pr in ("urgent", "high", "medium") and not fm:
            errs.append(f"{w}: {pr} needs a failure_mode")
    for k, n in enumerate(doc.get("not_promoted", [])):
        if not (n.get("title") and n.get("reason")):
            errs.append(f"not_promoted[{k}]: needs title and reason")
    return errs


CAP_STATUS = ("shipped", "partial", "planned", "out_of_scope")


def check_evidence(items: list, repo: Path, where: str) -> tuple[list[str], list[dict]]:
    """Check level/kind/claim/locators; return (errors, the hard items)."""
    errs, hard = [], []
    for j, e in enumerate(items or []):
        we = f"{where} evidence[{j}]"
        if e.get("level") not in LEVELS:
            errs.append(f"{we}: level must be one of {LEVELS}")
        if e.get("kind") not in KINDS:
            errs.append(f"{we}: kind must be one of {KINDS}")
        if not e.get("claim"):
            errs.append(f"{we}: missing claim")
        if e.get("level") in ("confirmed", "observed"):
            if not has_locator(e):
                errs.append(f"{we}: {e['level']} evidence needs a locator (file/commit/issue/command/url)")
            errs += check_locator(e, repo, we)
            hard.append(e)
    return errs, hard


def validate_project(doc: dict, repo: Path) -> list[str]:
    errs: list[str] = []
    if doc.get("version") != 1:
        errs.append("version must be 1")
    if doc.get("status") not in ("draft", "confirmed"):
        errs.append("status must be draft or confirmed")
    if doc.get("status") == "confirmed" and not doc.get("confirmed_at"):
        errs.append("a confirmed project needs confirmed_at")
    goal = doc.get("goal") or {}
    if not (goal.get("statement") or "").strip():
        errs.append("goal: missing statement")
    e, hard = check_evidence(goal.get("evidence"), repo, "goal")
    errs += e
    if not hard:
        errs.append("goal: needs at least one observed or confirmed item")
    for i, u in enumerate(doc.get("target_users") or []):
        if not u.get("who"):
            errs.append(f"target_users[{i}]: missing who")
        errs += check_evidence(u.get("evidence"), repo, f"target_users[{i}]")[0]
    if not doc.get("capabilities"):
        errs.append("capabilities: list what the project can do today")
    ids = set()
    for i, c in enumerate(doc.get("capabilities") or []):
        w = f"capability {c.get('id', i)}"
        if not (c.get("id") and c.get("name")):
            errs.append(f"{w}: needs id and name")
        if c.get("id") in ids:
            errs.append(f"{w}: duplicate id")
        ids.add(c.get("id"))
        st = c.get("status")
        if st not in CAP_STATUS:
            errs.append(f"{w}: status must be one of {CAP_STATUS}")
        e, hard = check_evidence(c.get("evidence"), repo, w)
        errs += e
        if st in ("shipped", "partial") and not any(x.get("kind") == "code" for x in hard):
            errs.append(f"{w}: {st} needs an observed or confirmed code item")
        if st == "partial" and not (c.get("missing") or "").strip():
            errs.append(f"{w}: partial needs a missing note")
        if st in ("planned", "out_of_scope") and not hard:
            errs.append(f"{w}: {st} needs an observed or confirmed item")
    for side in ("in_scope", "out_of_scope"):
        for i, b in enumerate((doc.get("boundary") or {}).get(side) or []):
            w = f"boundary.{side}[{i}]"
            if not b.get("item"):
                errs.append(f"{w}: missing item")
            e, hard = check_evidence(b.get("evidence"), repo, w)
            errs += e
            if side == "out_of_scope" and not hard:
                errs.append(f"{w}: needs an observed or confirmed item")
    for i, c in enumerate(doc.get("conflicts") or []):
        for side in ("a", "b"):
            loc = c.get(side) or {}
            if not has_locator(loc):
                errs.append(f"conflicts[{i}].{side}: needs a locator")
            errs += check_locator(loc, repo, f"conflicts[{i}].{side}")
    return errs


GAP_STATUS = ("shipped", "partial", "missing", "out_of_scope")
CATEGORIES = ("correctness", "credibility", "completeness", "opportunity")
BUCKETS = ("now", "next", "later", "not_now")
LIMITS = {"now": 3, "next": 5}


def validate_plan(plan: dict, repo: Path, project: dict | None, findings: dict | None,
                  beacon: dict | None) -> list[str]:
    errs: list[str] = []
    if plan.get("version") != 1:
        errs.append("version must be 1")
    if not project or project.get("status") != "confirmed":
        return errs + ["plan needs a confirmed .heed/project.json; run /heed goal first"]
    if findings is None:
        errs.append("plan needs .heed/findings.json; run /heed health first")
    caps = {c.get("id"): c for c in project.get("capabilities") or []}
    oos = {b.get("item") for b in (project.get("boundary") or {}).get("out_of_scope") or []}
    oos |= {c.get("name") for c in caps.values() if c.get("status") == "out_of_scope"}
    finding_ids = {f.get("id") for f in (findings or {}).get("findings") or []}
    pain_ids = {p.get("id") for p in (beacon or {}).get("pains") or []}
    promises = {pr.get("id"): pr for pr in plan.get("promises") or []}
    surfaces = {sf.get("id") for sf in plan.get("surfaces") or []}
    if not 3 <= len(promises) <= 6:
        errs.append("promises: break the goal into 3-6 promises")
    for pid, pr in promises.items():
        for c in pr.get("capabilities") or []:
            if c not in caps:
                errs.append(f"promise {pid}: unknown capability {c}")
    cells = {}
    for g in plan.get("gaps") or []:
        key = f"{g.get('promise')}/{g.get('surface')}"
        w = f"gap {key}"
        if g.get("promise") not in promises or g.get("surface") not in surfaces:
            errs.append(f"{w}: unknown promise or surface")
        if key in cells:
            errs.append(f"{w}: duplicate cell")
        cells[key] = g
        st = g.get("status")
        if st not in GAP_STATUS:
            errs.append(f"{w}: status must be one of {GAP_STATUS}")
        e, hard = check_evidence(g.get("evidence"), repo, w)
        errs += e
        if st == "shipped":
            want = ("code", "doc") if g.get("surface") == "docs" else ("code",)
            if not any(x.get("kind") in want for x in hard):
                errs.append(f"{w}: shipped needs a {' or '.join(want)} locator")
        if st in ("partial", "missing") and not (g.get("missing") or "").strip():
            errs.append(f"{w}: {st} needs a missing note")
        if st == "partial" and not hard:
            errs.append(f"{w}: partial needs a locator")
        if st == "out_of_scope" and g.get("boundary") not in oos:
            errs.append(f"{w}: out_of_scope must name an out-of-scope item of the confirmed project")
    for pid in promises:
        for sid in surfaces:
            if f"{pid}/{sid}" not in cells:
                errs.append(f"gap {pid}/{sid}: every promise x surface cell needs a status")
    decisions = {d.get("id"): d for d in plan.get("decisions") or []}
    blocked = {i for d in decisions.values() for i in d.get("blocks") or []}

    def resolve(ref: str) -> str | None:
        kind, _, val = ref.partition(":")
        if kind == "health":
            return None if val in finding_ids else f"no finding {val} in findings.json"
        if kind == "gap":
            return None if val in cells else f"no gap cell {val}"
        if kind == "goal":
            return None if val in caps or val in ("boundary", "goal") else f"no capability {val} in project.json"
        if kind == "beacon":
            if beacon is None:
                return "no .beacon/launch.json"
            return None if val in pain_ids else f"no pain {val} in .beacon/launch.json"
        if kind == "owner":
            return None if val in decisions else f"no decision {val}"
        return f"unknown reference kind '{kind}'"

    counts = {b: 0 for b in BUCKETS}
    ids = set()
    for it in plan.get("items") or []:
        w = f"item {it.get('id')}"
        if it.get("id") in ids:
            errs.append(f"{w}: duplicate id")
        ids.add(it.get("id"))
        if it.get("category") not in CATEGORIES:
            errs.append(f"{w}: category must be one of {CATEGORIES}")
        b = it.get("bucket")
        if b not in BUCKETS:
            errs.append(f"{w}: bucket must be one of {BUCKETS}")
        else:
            counts[b] += 1
        refs = it.get("because") or []
        if not refs:
            errs.append(f"{w}: needs because references")
        for r in refs:
            why = resolve(r)
            if why:
                errs.append(f"{w}: {r}: {why}")
        if it.get("category") == "opportunity" and not any(r.startswith(("health:", "beacon:")) for r in refs):
            errs.append(f"{w}: an opportunity must cite health: or beacon: evidence")
        if b == "now" and not (it.get("why_now") or "").strip():
            errs.append(f"{w}: now needs why_now")
        if b == "not_now" and not (it.get("reason") or "").strip():
            errs.append(f"{w}: not_now needs a reason")
        out = "goal:boundary" in refs or any(
            r.startswith("gap:") and cells.get(r[4:], {}).get("status") == "out_of_scope" for r in refs)
        if out and b in ("now", "next", "later") and not any(r.startswith("owner:") for r in refs):
            errs.append(f"{w}: rests on something out of scope; only not_now unless the owner decided otherwise")
        if b == "now" and it.get("id") in blocked:
            errs.append(f"{w}: blocked by an owner decision, so it can't be now")
        for r in refs:
            if r.startswith("owner:") and it.get("id") in (decisions.get(r[6:], {}).get("blocks") or []):
                errs.append(f"{w}: cites {r} as a reason, but that decision is still pending and blocks this item")
    for b, n in LIMITS.items():
        if counts[b] > n:
            errs.append(f"bucket {b}: {counts[b]} items; at most {n}")
    for did, d in decisions.items():
        if not d.get("question"):
            errs.append(f"decision {did}: missing question")
        for side in ("evidence_for", "evidence_against"):
            for r in d.get(side) or []:
                why = resolve(r)
                if why:
                    errs.append(f"decision {did}: {r}: {why}")
        for i in d.get("blocks") or []:
            if i not in ids:
                errs.append(f"decision {did}: blocks unknown item {i}")
    return errs


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__.strip().splitlines()[2].strip())
        return 2
    if "--plan" in argv:
        path = Path(argv[argv.index("--plan") + 1])
        repo = Path(argv[argv.index("--repo") + 1]) if "--repo" in argv else path.resolve().parent.parent
        load = lambda q: json.loads(q.read_text()) if q.exists() else None
        plan = load(path)
        errs = validate_plan(plan, repo, load(path.parent / "project.json"), load(path.parent / "findings.json"),
                             load(repo / ".beacon" / "launch.json"))
        for e in errs:
            print(e)
        if not errs:
            items = plan.get("items") or []
            tally = ", ".join(f"{sum(i.get('bucket') == b for i in items)} {b}" for b in BUCKETS)
            gaps = plan.get("gaps") or []
            gt = ", ".join(f"{sum(g.get('status') == s for g in gaps)} {s}" for s in GAP_STATUS)
            print(f"ok: {len(plan.get('promises') or [])} promises x {len(plan.get('surfaces') or [])} surfaces "
                  f"({gt}); items: {tally}; {len(plan.get('decisions') or [])} owner decision(s)")
        return 1 if errs else 0
    project = "--project" in argv
    if project:
        path = Path(argv[argv.index("--project") + 1])
    else:
        path = Path(argv[0])
    repo = Path(argv[argv.index("--repo") + 1]) if "--repo" in argv else path.resolve().parent.parent
    try:
        doc = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as e:
        print(f"cannot read {path}: {e}")
        return 1
    errs = validate_project(doc, repo) if project else validate(doc, repo)
    for e in errs:
        print(e)
    if not errs and project:
        caps = doc.get("capabilities", [])
        tally = ", ".join(f"{sum(c.get('status') == s for c in caps)} {s}" for s in CAP_STATUS
                          if any(c.get("status") == s for c in caps))
        print(f"ok: {doc['status']} goal; {len(caps)} capabilities ({tally}); "
              f"{len(doc.get('conflicts') or [])} conflicts, {len(doc.get('open_questions') or [])} open questions")
    elif not errs:
        n = len(doc.get("findings", []))
        print(f"ok: {n} finding(s), {len(doc.get('not_promoted', []))} not promoted")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
