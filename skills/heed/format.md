# `.heed/findings.json` format (version 1)

```json
{
  "version": 1,
  "repo": {"name": "typedmem", "commit": "dd8febf", "branch": "main", "scanned_at": "2026-09-27"},
  "areas": [
    {"id": "state", "path": "typedmem/state.py", "label": "State resolution"}
  ],
  "findings": [
    {
      "id": "F1",
      "title": "list() disagrees with get() after a scheduled value takes effect",
      "area": "state",
      "priority": "high",
      "summary": "One or two sentences on what is wrong.",
      "failure_mode": "What goes wrong, for whom, when.",
      "impact": ["An agent listing memories sees a stale current value"],
      "why_now": ["Open issue #7", "state.py changed 4 times in 30 days"],
      "evidence": [
        {"level": "confirmed", "kind": "issue", "claim": "Reported as a known issue", "issue": 7},
        {"level": "observed", "kind": "test", "claim": "A strict xfail test documents it",
         "file": "tests/test_state.py", "line": 251},
        {"level": "observed", "kind": "command", "claim": "The xfail test still fails",
         "command": "pytest -q tests/test_state.py -k scheduled", "exit_code": 0,
         "output": "1 xfailed"},
        {"level": "inferred", "kind": "reasoning", "claim": "Agents that poll list() may act on the old plan"}
      ],
      "next_step": "Make list() resolve states as of now, like get()."
    }
  ],
  "not_promoted": [
    {"title": "Retry logic in the HTTP server", "reason": "Covered by test_server_retries; no callers outside tests"}
  ],
  "method": {"candidates_investigated": 11, "notes": "Ran pytest -q (382 passed)."}
}
```

## Fields

- `priority`: `urgent` | `high` | `medium` | `watch`.
- `evidence[].level`: `confirmed` | `observed` | `inferred`.
- `evidence[].kind`: `code` | `test` | `todo` | `issue` | `git` | `ci` | `command` | `doc` | `reasoning`.
- **Locators.** Every `observed` or `confirmed` item needs at least one of
  these; an `inferred` item needs none.
  - `file` (repo-relative) + `line` (1-based); `end_line` is optional.
  - `commit`: a sha that exists in the repo.
  - `issue`: an issue or PR number.
  - `command` + `exit_code` + `output` (a short excerpt).
  - `url`, for documentation outside the repo.

## Evidence gates (checked by `validate.py`)

| Priority | Needs |
|---|---|
| urgent | ≥1 confirmed |
| high | ≥1 confirmed, or ≥2 observed of different `kind`; plus a non-empty `failure_mode` |
| medium | ≥1 observed or confirmed; plus a non-empty `failure_mode` |
| watch | ≥1 observed or confirmed |

A finding with only `inferred` evidence is not a finding. Put it in
`not_promoted`.

---

# `.heed/project.json` format (version 1), written by `/heed goal`

```json
{
  "version": 1,
  "status": "confirmed",
  "confirmed_at": "2026-09-27",
  "goal": {
    "statement": "Memory for AI agents when facts change: keep the current truth without erasing what used to be true, or where it came from.",
    "evidence": [{"level": "observed", "kind": "doc", "claim": "README tagline", "file": "README.md", "line": 3}]
  },
  "target_users": [
    {"who": "Developers building long-lived agents", "evidence": [
      {"level": "inferred", "kind": "reasoning", "claim": "Every example is an agent's memory"}]}
  ],
  "capabilities": [
    {"id": "state", "name": "Keep one current value per state key, with history", "status": "shipped",
     "summary": "set/get/history; ordered by validity time; conflicts exposed",
     "evidence": [{"level": "observed", "kind": "code", "claim": "resolver", "file": "typedmem/state.py", "line": 168}]}
  ],
  "boundary": {
    "in_scope": [{"item": "Explicit state keys", "evidence": [ ... ]}],
    "out_of_scope": [{"item": "Natural-language extraction of state", "evidence": [ ... ]}]
  },
  "conflicts": [
    {"topic": "Positioning", "a": {"claim": "README: memory when facts change", "file": "README.md", "line": 3},
     "b": {"claim": "Docs site: contract-driven memory", "file": "docs/index.md", "line": 3},
     "resolution": "User: README is current; the docs site is stale"}
  ],
  "open_questions": ["Is the HTTP server a supported surface, or a convenience?"]
}
```

- `status`: `draft` | `confirmed`. Once `confirmed`, `confirmed_at` is required.
- `capabilities[].status`: `shipped` | `partial` | `planned` | `out_of_scope`.
- Evidence items use the same levels, kinds and locators as `findings.json`.
- Gates checked by `validate.py --project`:

  | Field | Needs |
  |---|---|
  | goal | ≥1 observed or confirmed item |
  | shipped / partial capability | ≥1 observed or confirmed `code` item |
  | partial capability | also a `missing` note |
  | planned capability | ≥1 observed or confirmed item |
  | out_of_scope capability or boundary item | ≥1 observed or confirmed item |
  | conflicts | each side has a locator |

---

# `.heed/plan.json` format (version 1), written by `/heed plan`

```json
{
  "version": 1,
  "date": "2026-09-27",
  "promises": [{"id": "current", "text": "One current value per state", "capabilities": ["state"]}],
  "surfaces": [{"id": "python", "label": "Python API"}, {"id": "http", "label": "HTTP"}],
  "gaps": [
    {"promise": "current", "surface": "python", "status": "shipped",
     "evidence": [{"level": "observed", "kind": "code", "claim": "AgentMemory.set", "file": "typedmem/agent.py", "line": 236}]},
    {"promise": "current", "surface": "http", "status": "out_of_scope", "boundary": "States over HTTP and TypeScript (for now)"},
    {"promise": "current", "surface": "docs", "status": "partial", "missing": "No docs page for states",
     "evidence": [{"level": "observed", "kind": "doc", "claim": "Docs home pre-0.9", "file": "docs/index.md", "line": 3}]}
  ],
  "items": [
    {"id": "I1", "title": "Document states on the docs site", "category": "credibility", "bucket": "now",
     "why_now": "Distribution is about to send users to a site that omits the headline feature",
     "because": ["health:F1", "gap:current/docs", "goal:state"]},
    {"id": "I9", "title": "Natural-language state extraction", "category": "opportunity", "bucket": "not_now",
     "reason": "Out of scope in the confirmed goal", "because": ["goal:boundary", "beacon:P1"]}
  ],
  "decisions": [
    {"id": "D1", "question": "Should the pre-0.9 core stay in the pitch?",
     "evidence_for": ["goal:typed"], "evidence_against": ["health:F1"], "blocks": ["I4"]}
  ]
}
```

- `gaps[].status`: `shipped` | `partial` | `missing` | `out_of_scope` (glyphs ✓ △ — ○).
- `items[].category`: `correctness` | `credibility` | `completeness` | `opportunity`.
- `items[].bucket`: `now` (≤3, needs `why_now`) | `next` (≤5) | `later` | `not_now` (needs `reason`).
- `because` references, each resolved by `validate.py --plan` against the real files:

  | Reference | Resolves against |
  |---|---|
  | `health:F<n>` | `findings.json` |
  | `gap:<promise>/<surface>` | this file's `gaps` |
  | `goal:<capability id>`, `goal:boundary`, `goal:goal` | `project.json` |
  | `beacon:P<n>` | `.beacon/launch.json` pains |
  | `owner:<decision id>` | this file's `decisions` |

- Gates:
  - Every promise × surface cell is present exactly once.
  - A shipped cell needs a code (or, on docs, a doc) locator.
  - A partial cell needs a locator and `missing`; a missing cell needs `missing`.
  - An out_of_scope cell's `boundary` must name an out-of-scope item in `project.json`.
  - An opportunity needs a `health:` or `beacon:` reference.
  - An item resting on an out-of-scope cell, or on `goal:boundary`, can't be `now`, `next` or `later` without an `owner:` reference.
  - An item blocked by a decision can't be `now`.
