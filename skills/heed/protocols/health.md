# Heed health: what in the code deserves attention

Read `SKILL.md` first for the shared ground rules and evidence levels.

## Phase 1: Inventory (deterministic)

```bash
mkdir -p .heed
python3 "$SKILL_DIR/scripts/inventory.py" . > .heed/inventory.json
```

Read `.heed/inventory.json`. It holds facts, not judgements:
- **Structure:** tracked files and lines per top-level area.
- **Git activity:** commits in the last 30 and 90 days, the most-churned
  files, and author counts.
- **TODO / FIXME / HACK / XXX** markers, with their age from `git blame`.
- **Tests:** test files, and which areas have none.
- **CI:** workflow files and, when `gh` works, recent run conclusions.
- **Issues:** open issues when `gh` works.
- **Size:** the largest files.

Also read the README and any contributor or architecture docs, so you know
what the project *claims* to do and which paths matter most.

## Phase 2: Candidates

From the inventory and the docs, list 8–15 **candidates**. Each one is a
specific, falsifiable hypothesis tied to the signal that raised it.

- Good: "`retry()` in `net/client.py` may retry non-idempotent POSTs.
  Signal: FIXME at `client.py:88`, 9 changes in the last 90 days, no test
  file for `net/`."
- Bad: "Error handling could be improved."

Prioritise candidates where several signals overlap: churn plus weak tests
plus a TODO or an open issue on the same path.

## Phase 3: Investigate each candidate

For each candidate, collect evidence against this checklist. Not every item
applies. Record what you checked, including when you found nothing.

1. The exact code path (`file:line`) and what it does.
2. Its callers: is this path actually reached from something that matters?
3. Tests: which ones cover it, and does any test exercise the risky case?
4. Related TODO / FIXME / HACK markers, and how old they are.
5. Related open issues or CI failures.
6. Recent changes (`git log -L` or `git log -- <path>`): is it moving now?
7. A concrete **failure mode**: what goes wrong, for whom, when.
8. Optionally, a reproduction: run a relevant existing test, or a safe,
   read-only command that demonstrates the problem.

Label every evidence item `confirmed`, `observed` or `inferred` (see *Evidence levels* in `SKILL.md`).

Never upgrade a level to make a finding look stronger. `inferred` is honest
and useful; it is shown differently in the report, not hidden.

## Phase 4: Decide and rank (evidence-gated)

A candidate becomes a finding only if it has at least one `observed` or
`confirmed` item. Priority is gated by evidence, and `validate.py` enforces
these gates:

| Priority | Requires |
|---|---|
| `urgent` | ≥1 `confirmed` item, and the path matters now (production, security, data loss, or an active regression) |
| `high` | ≥1 `confirmed`, or ≥2 `observed` items from different kinds (e.g. `todo` + `test` + `git`), plus a stated failure mode |
| `medium` | ≥1 `observed` item and a stated failure mode |
| `watch` | a real signal whose consequence is still mostly `inferred` |

Everything else goes to `not_promoted`, with the reason (for example "no
callers found; dead code?" or "covered by `test_retry_backoff`").

For every finding, write:
- **impact:** what the failure would affect, concretely;
- **why now:** recent churn, an open issue, a regression, or rising use.
  If nothing makes it timely, say so, and that alone argues for `watch`.

A number never stands in for these reasons.

Group findings into **areas**: the directories or modules a reader would
recognise. The report's attention map is organised by area.

## Phase 5: Write, validate, render

Write `.heed/findings.json` in the format described in `SKILL_DIR/format.md`,
then validate it:

```bash
python3 "$SKILL_DIR/scripts/validate.py" .heed/findings.json
```

The validator checks the format and the evidence gates, and that every
`file` locator exists with its line in range, every commit sha exists, and
every command item records its exit code. Fix every error; don't loosen a
priority rule to pass. Then render the report and open it:

```bash
python3 "$SKILL_DIR/scripts/render.py" .heed/findings.json .heed/inventory.json -o .heed/report.html
open .heed/report.html        # macOS; xdg-open on Linux
```

## Phase 6: Tell the user

Reply in a few lines:
- the top 3 findings with their priority, and the strongest evidence for each;
- how many candidates you investigated and how many were not promoted;
- the path to the report.

Suggest adding `.heed/` to `.gitignore` if it isn't there. Don't edit
`.gitignore` yourself.
