"""Heed's scripts: inventory facts, the validator's evidence gates, and the renderer.

Each test builds a small throwaway git repo, so nothing depends on the
machine this runs on (except having `git`)."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "skills" / "heed" / "scripts"
sys.path.insert(0, str(SCRIPTS))
import inventory  # noqa: E402
import render  # noqa: E402
import validate  # noqa: E402


def git(repo, *args):
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True,
                   env={"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.com",
                        "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@example.com",
                        "HOME": str(repo), "PATH": "/usr/bin:/bin:/usr/local/bin:/opt/homebrew/bin"})


@pytest.fixture
def repo(tmp_path):
    (tmp_path / "pkg").mkdir()
    (tmp_path / "pkg" / "client.py").write_text("def retry():\n    # FIXME: retries POSTs too\n    return 1\n")
    (tmp_path / "pkg" / "util.py").write_text("def helper():\n    return 2\n")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_client.py").write_text("from pkg.client import retry\n\ndef test_retry():\n    assert retry() == 1\n")
    (tmp_path / "README.md").write_text("# demo\nTODO in prose is not a code marker\n")
    git(tmp_path, "init", "-q", "-b", "main")
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-q", "-m", "init")
    return tmp_path


def sha(repo):
    return subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True, text=True).stdout.strip()


# ── inventory ───────────────────────────────────────────────────────────
def test_inventory_facts(repo):
    inv = inventory.inventory(repo)
    assert inv["structure"]["tracked_files"] == 4
    assert [(m["file"], m["line"], m["tag"]) for m in inv["markers"]["items"]] == [("pkg/client.py", 2, "FIXME")]
    assert inv["markers"]["items"][0]["age_days"] == 0
    assert inv["git"]["commits_90d"] == 1
    assert inv["tests"]["modules_not_referenced_by_tests"] == ["pkg/util.py"]
    assert inv["issues"]["available"] is False or isinstance(inv["issues"]["open"], list)
    json.dumps(inv)                                # serialisable


# ── validator: evidence gates and locators ──────────────────────────────
def doc(finding, **extra):
    return {"version": 1, "areas": [{"id": "pkg", "path": "pkg/", "label": "pkg"}],
            "findings": [finding], "not_promoted": [], **extra}


def finding(priority, evidence, failure_mode="POSTs get retried twice"):
    return {"id": "F1", "title": "t", "area": "pkg", "priority": priority, "summary": "s",
            "failure_mode": failure_mode, "impact": ["checkout"], "evidence": evidence}


OBS_FILE = {"level": "observed", "kind": "todo", "claim": "FIXME", "file": "pkg/client.py", "line": 2}
OBS_TEST = {"level": "observed", "kind": "test", "claim": "no POST test", "file": "tests/test_client.py", "line": 3}
INF = {"level": "inferred", "kind": "reasoning", "claim": "could amplify load"}


def test_valid_high_with_two_observed_kinds(repo):
    assert validate.validate(doc(finding("high", [OBS_FILE, OBS_TEST, INF])), repo) == []


@pytest.mark.parametrize("priority,evidence,needle", [
    ("medium", [INF], "only inferred"),
    ("urgent", [OBS_FILE, OBS_TEST], "urgent needs at least one confirmed"),
    ("high", [OBS_FILE, dict(OBS_FILE, line=1)], "2+ different kinds"),
    ("medium", [dict(OBS_FILE, line=99)], "out of range"),
    ("medium", [dict(OBS_FILE, file="pkg/missing.py")], "file not found"),
    ("medium", [{"level": "observed", "kind": "todo", "claim": "x"}], "needs a locator"),
    ("medium", [{"level": "confirmed", "kind": "command", "claim": "x", "command": "pytest"}], "needs a locator"),
    ("medium", [dict(OBS_FILE, level="certain")], "level must be"),
])
def test_gates_reject(repo, priority, evidence, needle):
    errs = validate.validate(doc(finding(priority, evidence)), repo)
    assert any(needle in e for e in errs), errs


def test_failure_mode_required_above_watch(repo):
    errs = validate.validate(doc(finding("medium", [OBS_FILE], failure_mode="")), repo)
    assert any("needs a failure_mode" in e for e in errs)
    assert validate.validate(doc(finding("watch", [OBS_FILE], failure_mode="")), repo) == []


def test_commit_locator_checked(repo):
    good = {"level": "observed", "kind": "git", "claim": "c", "commit": sha(repo)}
    bad = dict(good, commit="deadbeef")
    assert validate.validate(doc(finding("watch", [good])), repo) == []
    assert any("commit not found" in e for e in validate.validate(doc(finding("watch", [bad])), repo))


def test_undeclared_area_and_not_promoted_reason(repo):
    d = doc(dict(finding("watch", [OBS_FILE]), area="nope"), not_promoted=[{"title": "x"}])
    errs = validate.validate(d, repo)
    assert any("not declared" in e for e in errs) and any("not_promoted" in e for e in errs)


# ── renderer ────────────────────────────────────────────────────────────
def test_render_is_self_contained_and_escapes(repo):
    d = doc(finding("high", [OBS_FILE, OBS_TEST, INF]), repo={"name": "demo", "commit": "abc",
            "web": "https://github.com/o/demo"}, method={"candidates_investigated": 3})
    d["findings"][0]["title"] = "<script>alert(1)</script>"
    html = render.render(d, inventory.inventory(repo))
    assert "<script>alert(1)</script>" not in html and "&lt;script&gt;" in html
    assert 'href="https://github.com/o/demo/blob/abc/pkg/client.py#L2"' in html
    assert "● confirmed · ◐ observed · ○ inferred" in html
    assert html.count("<script") == 1                      # only the tiny inline hash script


def test_example_findings_render():
    ex = json.loads((Path(__file__).parent / "example_findings.json").read_text())
    html = render.render(ex, None)
    assert "What needs attention in typedmem" in html and html.count('class="card"') == len(ex["findings"])


# ── goal mode: project.json ─────────────────────────────────────────────
def project(**over):
    d = {"version": 1, "status": "confirmed", "confirmed_at": "2026-09-27",
         "goal": {"statement": "Retry safely.", "evidence": [OBS_FILE]},
         "target_users": [{"who": "backend devs", "evidence": [INF]}],
         "capabilities": [{"id": "retry", "name": "Retries", "status": "shipped",
                           "evidence": [dict(OBS_FILE, kind="code")]}],
         "boundary": {"in_scope": [], "out_of_scope": []}, "conflicts": [], "open_questions": []}
    d.update(over)
    return d


def test_project_valid(repo):
    assert validate.validate_project(project(), repo) == []


@pytest.mark.parametrize("over,needle", [
    ({"status": "confirmed", "confirmed_at": None}, "confirmed_at"),
    ({"goal": {"statement": "x", "evidence": [INF]}}, "goal: needs at least one observed"),
    ({"capabilities": [{"id": "r", "name": "R", "status": "shipped", "evidence": [OBS_TEST]}]}, "shipped needs an observed or confirmed code item"),
    ({"capabilities": [{"id": "r", "name": "R", "status": "partial", "evidence": [dict(OBS_FILE, kind="code")]}]}, "partial needs a missing note"),
    ({"capabilities": [{"id": "r", "name": "R", "status": "planned", "evidence": [INF]}]}, "planned needs an observed"),
    ({"capabilities": [{"id": "r", "name": "R", "status": "someday", "evidence": [OBS_FILE]}]}, "status must be one of"),
    ({"boundary": {"out_of_scope": [{"item": "NL", "evidence": [INF]}]}}, "needs an observed or confirmed item"),
    ({"conflicts": [{"topic": "t", "a": {"claim": "x", "file": "README.md", "line": 1}, "b": {"claim": "y"}}]}, "conflicts[0].b: needs a locator"),
])
def test_project_gates_reject(repo, over, needle):
    errs = validate.validate_project(project(**over), repo)
    assert any(needle in e for e in errs), errs


def test_render_project_only_and_combined(repo):
    only = render.render(None, None, project())
    assert "What repository is trying to be" in only
    assert "The project" in only and "What needs attention" not in only
    both = render.render(doc(finding("watch", [OBS_FILE])), None, project())
    assert "The project" in both and "What needs attention" in both


def test_example_project_renders():
    ex = json.loads((Path(__file__).parent / "example_project.json").read_text())
    html = render.render(None, None, ex)
    assert "Resolved:" in html and html.count('class="st shipped"') == 7


# ── plan mode: plan.json ────────────────────────────────────────────────
EX_DIR = Path(__file__).parent


def plan_fixture(repo):
    """The TypedMem example plan, re-pointed at the throwaway repo: code/doc
    locators become pkg/client.py:2 so locator checks pass."""
    plan = json.loads((EX_DIR / "example_plan.json").read_text())
    for g in plan["gaps"]:
        for ev in g.get("evidence") or []:
            ev.update(file="pkg/client.py", line=2)
    project = json.loads((EX_DIR / "example_project.json").read_text())
    findings = json.loads((EX_DIR / "example_findings.json").read_text())
    beacon = {"pains": [{"id": f"P{i}"} for i in range(1, 5)]}
    return plan, project, findings, beacon


def test_example_plan_valid(repo):
    plan, project, findings, beacon = plan_fixture(repo)
    assert validate.validate_plan(plan, repo, project, findings, beacon) == []


def _item(plan, iid):
    return next(i for i in plan["items"] if i["id"] == iid)


@pytest.mark.parametrize("mutate,needle", [
    (lambda p: _item(p, "I4").update(bucket="now", why_now="x"), "at most 3"),
    (lambda p: _item(p, "I1").pop("why_now"), "now needs why_now"),
    (lambda p: _item(p, "I9").update(bucket="next"), "rests on something out of scope"),
    (lambda p: _item(p, "I10").update(bucket="later"), "rests on something out of scope"),
    (lambda p: _item(p, "I6").update(because=["goal:goal"]), "opportunity must cite"),
    (lambda p: _item(p, "I1").update(because=["health:F99"]), "no finding F99"),
    (lambda p: _item(p, "I6").update(because=["beacon:P9"]), "no pain P9"),
    (lambda p: _item(p, "I7").update(bucket="now", why_now="x"), "blocked by an owner decision"),
    (lambda p: _item(p, "I7")["because"].append("owner:D1"), "still pending"),
    (lambda p: p["gaps"].pop(), "needs a status"),
    (lambda p: p["gaps"][3].update(boundary="Something invented"), "out-of-scope item of the confirmed project"),
    (lambda p: p["gaps"][0].update(evidence=[]), "shipped needs a code locator"),
])
def test_plan_rules_reject(repo, mutate, needle):
    plan, project, findings, beacon = plan_fixture(repo)
    mutate(plan)
    errs = validate.validate_plan(plan, repo, project, findings, beacon)
    assert any(needle in e for e in errs), errs


def test_plan_needs_confirmed_goal(repo):
    plan, project, findings, beacon = plan_fixture(repo)
    project["status"] = "draft"
    assert any("run /heed goal" in e for e in validate.validate_plan(plan, repo, project, findings, beacon))


def test_render_plan_cockpit_and_map(repo):
    plan, project, findings, beacon = plan_fixture(repo)
    html = render.render(findings, None, project, plan, None)
    assert "relative to its goal?" in html and "Gap map" in html and "Owner decision required" in html
    assert html.count('<td class="gc out_of_scope"') == 10 and "Blocked by" in html
