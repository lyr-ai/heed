# Heed

**What in this repo deserves attention, and the evidence for it.**

Heed is a skill for the coding agent you already use. Run `/heed` in a
repository and the agent follows a fixed investigation protocol:

1. A deterministic inventory of the repo.
2. Specific, checkable candidate concerns.
3. An investigation of each candidate for evidence.
4. A ranking that is gated by that evidence.

It writes a short list of findings and a self-contained visual report.

[![Heed report for typedmem: six findings, with one high-priority item (the docs site never mentions the 0.9 headline feature)](docs/example-typedmem.png)](docs/example-typedmem.png)

*The report from running Heed on [typedmem](https://github.com/lyr-ai/typedmem).*

## Why a protocol, not a prompt

"Analyze this repo and find problems" produces a list of plausible,
uncheckable advice: an **LLM code horoscope**. Heed makes the agent earn
every finding.

- **Inventory first.** A script collects facts with no judgement: structure,
  git churn, TODO/FIXME with their age, tests, CI runs, open issues.
- **Candidates are hypotheses.** For example, "`retry()` may retry POSTs:
  FIXME at `client.py:88`, 9 changes in 90 days, no test for `net/`". Not
  "error handling could be improved".
- **Every evidence item is labelled by certainty.**

  | | Level | Meaning |
  |---|---|---|
  | ● | **confirmed** | The problem is demonstrated: a failing test or command, an open issue reporting it, or docs stating it |
  | ◐ | **observed** | A checkable fact that supports it, with a locator (`file:line`, commit, issue, command output) |
  | ○ | **inferred** | The agent's reasoning, shown as reasoning |

- **Priority is gated by evidence.** `urgent` needs a confirmed item. `high`
  needs a confirmed item, or observed evidence of two different kinds, plus a
  failure mode. A concern with only inferred evidence is not a finding. The
  validator enforces these gates and checks that every file, line and commit
  it cites actually exists.
- **Ranking is explained, not scored.** Each finding states its impact and
  why it matters now.
- **What was set aside is shown.** Candidates that didn't earn a finding are
  listed with the reason.

## Install

Heed is a directory of instructions and three small Python scripts (3.10+,
standard library only). It needs no API key and no service: the agent you
already run does the reading and reasoning.

```bash
git clone https://github.com/lyr-ai/heed ~/src/heed
ln -s ~/src/heed/skills/heed ~/.claude/skills/heed      # Claude Code
```

For other agents that support skills or custom instructions, point them at
`skills/heed/SKILL.md`.

## Use

In any git repository:

```text
/heed
```

Output goes to `.heed/` (add it to `.gitignore`):

| File | What |
|---|---|
| `inventory.json` | The deterministic facts the investigation started from |
| `findings.json` | Findings with their evidence ([format](skills/heed/format.md)) |
| `report.html` | The visual report: an attention map, then findings by priority, with evidence on demand. One file, no server |

Heed is **read-only**. It writes nothing outside `.heed/`, and runs the
project's tests only if they're documented, fast and offline.

On a work repository, check that your company allows the coding agent you
use to read that code. Heed adds no service of its own.

## Status

v0: used by its author on their own repos. The protocol, the evidence gates
and the report format will change as it meets real repositories. Issues with
a finding Heed got wrong, or one it missed, are the most useful kind.

## Also from lyr-ai

[TypedMem](https://github.com/lyr-ai/typedmem) (memory for AI agents when
facts change) · [AgentSeism](https://github.com/lyr-ai/agentseism)
(regression decisions for stochastic AI systems).

MIT licensed.
