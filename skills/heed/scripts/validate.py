"""Validate Heed's outputs: format, evidence gates, and locators.

    python3 validate.py .heed/findings.json [--repo .]
    python3 validate.py --project .heed/project.json [--repo .]

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


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__.strip().splitlines()[2].strip())
        return 2
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
