# Heed goal: what is this project trying to be?

Read `SKILL.md` first for the shared ground rules and evidence levels.

Later modes judge external demand and plan work *against the project's
goal*. Without a goal they can't tell a real gap from noise. This mode
produces that goal, but **it doesn't decide it.** You draft it from what the
project already says about itself, and the user confirms or corrects it.

## Phase 1: Read what the project says about itself

Read, in this order, whichever exist:

1. The README, all of it. The first screen is the current pitch.
2. The roadmap, vision or "what this is not" sections, anywhere.
3. Design docs, RFCs and ADRs (`design/`, `docs/`, `rfcs/`, `adr/`): their
   status and their decisions.
4. The last three releases in the CHANGELOG: what actually shipped recently.
5. Package metadata (`pyproject.toml`, `package.json`, …) and the GitHub
   repo description and topics (`gh repo view --json description,repositoryTopics`).
6. The docs site sources, if any. Compare their pitch with the README's.

Also run `python3 "$SKILL_DIR/scripts/inventory.py" . > .heed/inventory.json`
if it doesn't exist yet. Capabilities need code locators.

## Phase 2: Draft `.heed/project.json`

The format is in `SKILL_DIR/format.md` (the "project.json" section). Draft:

- **goal:** one or two sentences, in the project's own words where
  possible, with the locators they came from.
- **target_users:** who it is for, each with evidence. Say `inferred` if the
  docs only imply it.
- **capabilities:** what the project can do today. Set the status honestly:

  | Status | Needs |
  |---|---|
  | `shipped` | code (`file:line`), and ideally a test or a documented example |
  | `partial` | code, plus a note saying what is missing |
  | `planned` | a roadmap, design or issue locator; there is no code yet |
  | `out_of_scope` | an explicit statement that the project won't do it |

  Six to twelve capabilities, at the level a user would name them ("keeps
  the current value of a state and its history"), not internals.
- **boundary:** `in_scope` and `out_of_scope` items, with evidence.
- **conflicts:** places where the project's sources disagree about what it
  is, for example the README's pitch against the docs site's, or a design
  note against the code. Give both locators.
- **open_questions:** what the sources don't settle, which only the user
  can answer.

Set `"status": "draft"`.

## Phase 3: Confirm with the user

Show the draft briefly, not the JSON:
- the goal sentence;
- the target users;
- the capability list, with statuses;
- the boundary;
- any conflicts and open questions.

Then ask the user to confirm or correct it. Ask directly and keep it short.
If your agent has a structured-question tool, use it for the open questions.

Apply their answers exactly:
- A correction replaces the draft text. Record it as evidence `{"level":
  "confirmed", "kind": "doc", "claim": "Confirmed by the user", "url":
  "user:<date>"}`.
- For each conflict, record which side the user chose, or that it stays
  open.
- Set `"status": "confirmed"`, `"confirmed_at": "<date>"`.

If the user doesn't confirm, leave it as `draft`. `gaps` and `plan` must
not run on a draft goal.

## Phase 4: Validate, render, tell

```bash
python3 "$SKILL_DIR/scripts/validate.py" --project .heed/project.json
python3 "$SKILL_DIR/scripts/render.py" --project .heed/project.json \
    [.heed/findings.json] [.heed/inventory.json] -o .heed/report.html
```

Fix every validation error. Then tell the user, in a few lines:
- the confirmed goal;
- how many capabilities are shipped, partial or planned;
- the conflicts they resolved and any still open;
- the path to the report.

Conflicts between the project's own sources are often worth acting on
directly: a stale docs site misleads users before any feature does.
