"""Deterministic repository inventory for Heed (phase 1).

    python3 inventory.py [repo] > .heed/inventory.json

Facts only, no judgement: structure, git activity and churn, TODO-style
markers with their age, tests, CI, open issues, and the largest files.
Reads tracked files (`git ls-files`), so .gitignore'd and vendored build
output stay out. Standard library only. `gh` is optional: without it, the
issues and CI runs sections say why they're empty.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

MARKER = re.compile(r"\b(TODO|FIXME|HACK|XXX)\b[:(\s]?(.*)")
TEST_PATH = re.compile(r"(^|/)(tests?|spec|__tests__)(/|$)|(^|/)test_[^/]+$|_test\.[a-z]+$|\.(test|spec)\.[a-z]+$")
SKIP_EXT = {".png", ".jpg", ".jpeg", ".gif", ".ico", ".pdf", ".zip", ".gz", ".whl", ".lock", ".svg",
            ".woff", ".woff2", ".ttf", ".mp4", ".webp", ".jar", ".so", ".dylib", ".bin", ".pyc"}
CODE_EXT = {".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".rs", ".java", ".kt", ".rb", ".cs", ".cpp", ".c", ".h", ".swift", ".scala"}
GENERATED = re.compile(r"(^|/)(package-lock\.json|yarn\.lock|pnpm-lock\.yaml|poetry\.lock|Cargo\.lock|go\.sum)$|\.min\.(js|css)$")
MAX_MARKERS, MAX_BLAME = 300, 150


def run(args: list[str], cwd: Path, timeout: int = 60) -> tuple[int, str]:
    try:
        p = subprocess.run(args, cwd=cwd, capture_output=True, text=True, timeout=timeout)
        return p.returncode, p.stdout
    except (OSError, subprocess.TimeoutExpired) as e:
        return 1, str(e)


def area_of(path: str) -> str:
    parts = path.split("/")
    return parts[0] if len(parts) > 1 else "(root)"


def text_lines(path: Path) -> list[str] | None:
    if path.suffix.lower() in SKIP_EXT:
        return None
    try:
        data = path.read_bytes()
    except OSError:
        return None
    if b"\0" in data[:4096] or len(data) > 2_000_000:
        return None
    return data.decode("utf-8", errors="replace").splitlines()


def inventory(root: Path) -> dict:
    now = datetime.now(timezone.utc)
    rc, top = run(["git", "rev-parse", "--show-toplevel"], root)
    if rc != 0:
        raise SystemExit(f"not a git repository: {root}")
    root = Path(top.strip())
    _, head = run(["git", "rev-parse", "--short", "HEAD"], root)
    _, branch = run(["git", "branch", "--show-current"], root)
    _, remote = run(["git", "remote", "get-url", "origin"], root)
    m = re.search(r"github\.com[:/]([^/]+/[^/\s]+?)(\.git)?$", remote.strip())
    web = f"https://github.com/{m.group(1)}" if m else None
    _, files_out = run(["git", "ls-files"], root)
    files = [f for f in files_out.splitlines() if f]
    fileset = set(files)

    # structure + markers + sizes
    areas: dict[str, dict] = defaultdict(lambda: {"files": 0, "lines": 0, "test_files": 0})
    sizes, markers = [], []
    ext = Counter()
    for f in files:
        a = areas[area_of(f)]
        a["files"] += 1
        ext[Path(f).suffix.lower() or "(none)"] += 1
        if TEST_PATH.search(f):
            a["test_files"] += 1
        lines = text_lines(root / f)
        if lines is None:
            continue
        a["lines"] += len(lines)
        if not GENERATED.search(f):
            sizes.append((len(lines), f))
        if len(markers) < MAX_MARKERS:
            for i, line in enumerate(lines, 1):
                m = MARKER.search(line)
                if m and not f.endswith((".md", ".rst", ".txt")):      # markers in code, not prose
                    markers.append({"file": f, "line": i, "tag": m.group(1),
                                    "text": line.strip()[:160]})
                    if len(markers) >= MAX_MARKERS:
                        break

    # marker age via blame (bounded)
    for mk in markers[:MAX_BLAME]:
        rc, out = run(["git", "blame", "--porcelain", "-L", f"{mk['line']},{mk['line']}", "--", mk["file"]], root, 20)
        t = re.search(r"^author-time (\d+)", out, re.M) if rc == 0 else None
        if t:
            when = datetime.fromtimestamp(int(t.group(1)), timezone.utc)
            mk["added"] = when.date().isoformat()
            mk["age_days"] = (now - when).days

    # git activity and churn
    def commits_since(days: int) -> int:
        _, out = run(["git", "rev-list", "--count", f"--since={days}.days", "HEAD"], root)
        return int(out.strip() or 0)

    churn: dict[str, dict] = defaultdict(lambda: {"commits": 0, "lines_changed": 0, "authors": set()})
    _, log = run(["git", "log", "--since=90.days", "--numstat", "--format=@@%ae"], root, 120)
    author = None
    for line in log.splitlines():
        if line.startswith("@@"):
            author = line[2:]
            continue
        parts = line.split("\t")
        if len(parts) == 3 and parts[2] in fileset:              # skips renames ("a => b")
            c = churn[parts[2]]
            c["commits"] += 1
            c["lines_changed"] += sum(int(x) for x in parts[:2] if x.isdigit())
            c["authors"].add(author)
    hot = sorted(churn.items(), key=lambda kv: (kv[1]["commits"], kv[1]["lines_changed"]), reverse=True)[:25]

    # tests: a source module counts as referenced when some test file names it
    # (import path or module name as a word). A heuristic, and labelled as one.
    test_files = [f for f in files if TEST_PATH.search(f)]
    test_text = "\n".join("\n".join(text_lines(root / t) or []) for t in test_files) + "\n".join(test_files)
    code = [f for f in files if Path(f).suffix in CODE_EXT and not TEST_PATH.search(f)
            and Path(f).stem not in {"__init__", "index", "main", "setup", "conftest"}]
    def referenced(f: str) -> bool:
        mod = f.rsplit(".", 1)[0].replace("/", ".")
        stem = Path(f).stem
        return mod in test_text or re.search(rf"\b{re.escape(stem)}\b", test_text) is not None
    unreferenced = [f for f in code if not referenced(f)]

    # CI
    workflows = sorted(f for f in files if f.startswith(".github/workflows/"))
    ci_runs: dict = {"available": False}
    rc, out = run(["gh", "run", "list", "--limit", "30", "--json",
                   "name,conclusion,status,headBranch,createdAt,databaseId"], root, 30)
    if rc == 0:
        runs = json.loads(out or "[]")
        ci_runs = {"available": True, "recent": runs[:30],
                   "failures": [r for r in runs if r.get("conclusion") in ("failure", "timed_out")]}
    else:
        ci_runs["reason"] = "gh unavailable or not a GitHub repo"

    # issues
    issues: dict = {"available": False}
    rc, out = run(["gh", "issue", "list", "--state", "open", "--limit", "100", "--json",
                   "number,title,labels,createdAt,comments"], root, 30)
    if rc == 0:
        items = json.loads(out or "[]")
        issues = {"available": True, "open": [
            {"number": i["number"], "title": i["title"], "created": i["createdAt"][:10],
             "labels": [l["name"] for l in i.get("labels", [])],
             "comments": len(i.get("comments", []))} for i in items]}
    else:
        issues["reason"] = "gh unavailable or not a GitHub repo"

    return {
        "tool": "heed inventory v1",
        "generated_at": now.isoformat(timespec="seconds"),
        "repo": {"name": root.name, "commit": head.strip(), "branch": branch.strip(), "web": web},
        "structure": {
            "tracked_files": len(files),
            "areas": {a: v for a, v in sorted(areas.items(), key=lambda kv: -kv[1]["lines"])},
            "top_extensions": ext.most_common(12),
        },
        "git": {
            "commits_30d": commits_since(30), "commits_90d": commits_since(90),
            "hot_files_90d": [{"file": f, "commits": v["commits"], "lines_changed": v["lines_changed"],
                               "authors": len(v["authors"])} for f, v in hot],
        },
        "markers": {"count": len(markers), "capped": len(markers) >= MAX_MARKERS, "items": markers},
        "tests": {"test_files": len(test_files), "sample": test_files[:40],
                  "source_modules": len(code),
                  "modules_not_referenced_by_tests": unreferenced[:60],
                  "note": "heuristic: a module counts as referenced if any test file mentions its import path or name"},
        "ci": {"workflows": workflows, "runs": ci_runs},
        "issues": issues,
        "largest_files": [{"file": f, "lines": n} for n, f in sorted(sizes, reverse=True)[:12]],
    }


if __name__ == "__main__":
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    json.dump(inventory(root), sys.stdout, indent=1, default=list)
    sys.stdout.write("\n")
