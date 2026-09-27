---
name: heed
description: Evidence-driven project intelligence for the current repository. `/heed` (or `/heed health`) investigates what in the code deserves attention and writes .heed/findings.json plus a visual report. `/heed goal` drafts the project's goal, target users, capabilities and boundary from its own docs, confirms them with the user, and writes .heed/project.json. Use when the user runs /heed, or asks what needs attention in this repo or what the project is trying to be.
---

# Heed

Heed makes you investigate, not opine. Every conclusion rests on evidence a
reader can check, and every evidence item says how certain it is. A
plausible-sounding claim with no checkable evidence is not a conclusion.

`SKILL_DIR` below means the directory containing this file.

## Modes

Read the protocol for the mode the user asked for, then follow it exactly.

| Command | Mode | Protocol | Output |
|---|---|---|---|
| `/heed`, `/heed health` | What in the code deserves attention | `protocols/health.md` | `.heed/findings.json` |
| `/heed goal` | What the project is trying to be, confirmed by the user | `protocols/goal.md` | `.heed/project.json` |
| `/heed gaps`, `/heed plan` | Not built yet (v0.3–v0.4) | | Say so, and suggest `/heed goal` first |

Every mode ends by rendering `.heed/report.html` from whatever `.heed/` holds.

## Evidence levels (all modes)

| Level | Meaning | Examples |
|---|---|---|
| `confirmed` | The claim itself is demonstrated | a failing test or command you ran (with output); an open issue that reports it; docs or a user that state it |
| `observed` | A checkable fact that supports the claim | the TODO exists at `file:line`; no test references the function; the README says X at line N; 9 commits in 90 days |
| `inferred` | Your reasoning, not directly checkable | "this could amplify retries under load"; "the docs imply this is for agent developers" |

Never upgrade a level to make a claim look stronger. `inferred` is honest
and useful; it is shown differently in the report, not hidden.

**Locators.** Every `observed` or `confirmed` item names where to check it:
- `file` + `line` (repo-relative, 1-based), with an optional `end_line`;
- a `commit` sha;
- an `issue` number;
- a `command` with its `exit_code` and `output`;
- a `url`.

## Ground rules

- **Read-only.** Never edit, format, commit or delete anything in the repo.
  The only files you write are in `.heed/` at the repo root.
- **Safe commands only.** You may read files, grep, and run `git` and `gh`
  read commands. You may run the project's existing test command *only* if it
  is documented (README, CI config, Makefile, pyproject), is expected to be
  fast, and needs no network, credentials or installs. If in doubt, ask the
  user first.
- **Cite, don't assert.** Every OBSERVED or CONFIRMED evidence item needs a
  locator the reader can follow: `file:line`, a commit sha, an issue number,
  or a command with its exit code and output.
- **Say what you couldn't establish.** Every mode has a place for it:
  `not_promoted` in health, `open_questions` in goal. It is part of the
  report, not a failure.
- **Depth beats breadth.** A few well-evidenced conclusions are worth more
  than many thin ones.
