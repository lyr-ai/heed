# Heed plan: where is the project relative to its goal, and what next?

Read `SKILL.md` first for the shared ground rules and evidence levels.

`plan` does not search for new problems and does not research the market.
It **combines evidence that already exists**:

| Input | Required | What it gives |
|---|---|---|
| `.heed/project.json` | yes, with `"status": "confirmed"` | the goal, capabilities and boundary, decided by the owner |
| `.heed/findings.json` | yes, from `/heed health` | what is wrong or risky now |
| `.beacon/launch.json` | optional | outside evidence: pains, audiences (from the Beacon skill) |

If `project.json` is missing or still a draft, stop and tell the user to
run `/heed goal`. If `findings.json` is missing or older than the last
commit, suggest `/heed health` first.

## Phase 1: Promises

Break the confirmed goal into 3–6 **promises**: things the goal commits the
project to. Each links to the goal and to the capabilities that deliver it.
For TypedMem: current state · history · provenance · unresolved conflict.

## Phase 2: Gap map

Choose the **surfaces** through which users meet the project: for example
core, CLI, Python API, HTTP, TypeScript and docs. Only include surfaces that
exist in the repo or are named in the goal.

Fill every promise × surface cell with one status. Each status has its own
proof:

| Cell | Glyph | Needs |
|---|---|---|
| `shipped` | ✓ | a `code` locator (or a `doc` locator for the docs surface) |
| `partial` | △ | a locator, and a `missing` note saying what is missing |
| `missing` | — | a `missing` note; the goal expects it here and nothing is there |
| `out_of_scope` | ○ | a `boundary` reference to an out-of-scope item in `project.json` |

You don't decide scope. If a cell looks missing but the confirmed boundary
excludes it, it is `out_of_scope`, not `missing`.

## Phase 3: Work items

Turn findings, partial and missing cells, and (if present) Beacon pains into
**items**. Put each in one category:

| Category | Meaning |
|---|---|
| `correctness` | something shipped is wrong |
| `credibility` | it works, but users are misled (stale docs, misleading messages, stale metadata) |
| `completeness` | the goal promises it, and a surface doesn't deliver it yet |
| `opportunity` | nothing is broken, but evidence says this would advance the goal |

**Every item has `because`**, a list of references it rests on:
- `health:F1`, a finding;
- `gap:<promise>/<surface>`, a gap-map cell;
- `goal:<capability id>` or `goal:boundary`, the confirmed project;
- `beacon:P1`, a Beacon pain;
- `owner:<decision id>`, a decision the owner has made.

An `opportunity` must cite a `health:` or `beacon:` reference. No free
brainstorming.

## Phase 4: Buckets

| Bucket | Limit | Rule |
|---|---|---|
| `now` | ≤ 3 | Each item states `why_now`: what makes it urgent *now* |
| `next` | ≤ 5 | Clearly advances the goal; not a blocker |
| `later` | any | Reasonable, but not worth attention now |
| `not_now` | any | Each item states `reason`, citing the boundary or the goal |

**Guard against scope creep.** An item that rests on an `out_of_scope` cell
or boundary item can only be `not_now`, unless the owner has decided
otherwise (an `owner:` reference).

Order within `now` by impact on the goal's users, credibility first when
distribution is imminent.

## Phase 5: Owner decisions

When evidence points in different directions and only the owner can
settle it, write a **decision**:
- the question;
- `evidence_for` and `evidence_against`, both as references;
- the items it `blocks`.

A blocked item can't be `now`. Heed never settles a decision itself.

## Phase 6: Write, validate, render, tell

Write `.heed/plan.json` (format: `SKILL_DIR/format.md`, the "plan.json"
section), then:

```bash
python3 "$SKILL_DIR/scripts/validate.py" --plan .heed/plan.json
python3 "$SKILL_DIR/scripts/render.py" --plan .heed/plan.json --project .heed/project.json \
    .heed/findings.json .heed/inventory.json -o .heed/report.html
```

The validator resolves every `because` reference against the real files.
Fix every error. Then tell the user:
- the `now` items, each with its why-now;
- the gap-map summary;
- any owner decisions waiting;
- the `not_now` items, which is how scope creep is refused out loud.
