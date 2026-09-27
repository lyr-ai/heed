# Design 0001: Project Readiness and Asset Gaps

**Status:** Proposed
**Project:** Heed
**Working feature name:** Project Readiness
**Primary integration:** `/heed plan`
**Companion:** Beacon
**Scope:** Project bottleneck diagnosis + missing asset identification
**Non-goal:** GTM channel/message selection

The goal is not to add a video feature to Heed. It is a more general capability:

> **Judge the project's current real bottleneck, and which asset is missing to
> reach the next stage. Once the problem has become distribution, hand off to
> Beacon explicitly.**

---

## 1. Motivation

Heed currently answers three increasingly strategic questions:

```text
/heed health
What deserves attention in the project?

/heed goal
What is this project trying to become?

/heed plan
Given the goal and current evidence,
what should the project do next?
```

In practice, a project eventually reaches a point where the next useful action is
no longer another code feature.

A project may already have:

- correct implementation;
- a coherent product boundary;
- documentation;
- tests;
- external measurement;
- a working demo;
- visual explanation;
- reusable distribution assets.

At that point, continuing to generate engineering work is harmful.

Heed should be able to say:

> **The product is ready enough. Building more is not the current bottleneck.**

Conversely, a project may have a clear product but lack the artifact required to
make its value credible or understandable:

> no benchmark;
> no working demo;
> no visual explanation;
> no case study;
> no portable video/animation.

Heed should identify that gap when evidence supports it.

The feature therefore answers:

> **What is preventing this project from moving to its next stage?**

and:

> **Is there an artifact the project should create before doing more distribution?**

## 2. Core principle

The feature is not a generic launch checklist.

Heed must **not** require every project to have:

```text
README
docs
benchmark
demo
visual
video
case study
blog
```

Different products require different evidence and explanation.

- A CLI utility may need no video.
- A visual product may need no benchmark.
- A low-level performance library may need a benchmark but no animation.
- An unfamiliar semantic abstraction may strongly benefit from an interactive
  explanation.

Therefore:

> **Assets are justified by a project bottleneck, not by a template.**

## 3. Responsibility boundary: Heed vs Beacon

This boundary is a hard design constraint.

### Heed

Heed answers:

> **What does the project need next?**

It may determine:

- correctness is blocking;
- product capability is missing;
- proof is insufficient;
- documentation is misleading;
- users cannot easily understand the value;
- a demo/visual/video/case study is missing;
- distribution is now the dominant bottleneck.

Heed may recommend creating an asset. It does **not** decide how to market that
asset.

### Beacon

Beacon answers:

> **How do we reach the people who should care?**

It owns:

- target audience;
- external pains;
- value proposition;
- channels;
- hooks;
- messaging;
- CTA;
- GTM experiment;
- experiment results.

Beacon may choose among assets Heed says are available.

### Handoff

```text
                         HEED

               What does the project need?
                         │
          ┌──────────────┼───────────────┐
          │              │               │
          ▼              ▼               ▼
       PRODUCT          PROOF        EXPLANATION
          │              │               │
       missing?        missing?         missing?
          │              │               │
          └──────────────┼───────────────┘
                         │
                         ▼
                 PROJECT READY ENOUGH
                         │
                         ▼
             DISTRIBUTION IS BOTTLENECK
                         │
                         ▼
                       BEACON

             Who → Where → Message → CTA
                         │
                         ▼
                  ONE EXPERIMENT
```

## 4. What counts as a bottleneck

Heed should classify the current limiting factor into a small taxonomy.

### 4.1 Correctness

The product does not reliably do what it claims. Examples:

- inconsistent public APIs;
- failing tests;
- known semantic bug;
- data corruption;
- stale behavior across surfaces.

This normally outranks every downstream concern.

### 4.2 Product gap

A capability required by the owner-confirmed project goal is absent or incomplete.

Example:

> Goal promises queryable historical state, but no public API exposes history.

Out-of-scope capabilities do not count as gaps.

### 4.3 Credibility

The product works, but its public surfaces misrepresent it. Examples:

- stale PyPI description;
- docs contradict implementation;
- README makes unsupported claims;
- examples no longer execute;
- current product name differs across surfaces.

### 4.4 Proof

The product claim exists and is implemented, but the evidence is insufficient.

Example:

> "preserves historical state" is implemented and unit-tested, but the existing
> benchmark has never measured the new abstraction.

Possible missing assets:

- benchmark;
- reproducible experiment;
- before/after measurement;
- external case study;
- real-world integration.

### 4.5 Understanding

The product is correct and supported, but its value is difficult to understand
quickly. Evidence might include:

- owner cannot explain first screen clearly;
- README requires substantial architecture knowledge;
- repeated user confusion;
- core behavior is temporal/spatial and difficult to communicate in text;
- Beacon Value Map shows a strong value that current public surfaces bury.

Possible assets:

- simpler example;
- demo;
- static visual;
- interactive visual;
- short explanatory animation.

### 4.6 Trial

A potential user understands the product but cannot easily experience its value.
Examples:

- installation requires substantial setup;
- demo requires credentials;
- no runnable quickstart;
- first useful result takes too long;
- no example project exists.

Possible assets:

- zero-key demo;
- sample repo;
- quickstart;
- sandbox;
- self-contained report.

### 4.7 Distribution

Product, proof and explanation are sufficiently ready, but too few relevant people
encounter them.

At this point Heed must explicitly say:

> **Distribution is now the bottleneck.**

It must not invent another engineering feature merely to keep the roadmap
populated. Ownership passes to Beacon.

## 5. Asset taxonomy

Heed may identify a missing project asset only when it addresses an evidenced
bottleneck. Supported asset classes:

- **Documentation asset** (quickstart, concepts page, API guide, migration guide):
  useful when the problem is comprehension through text/reference.
- **Proof asset** (benchmark, experiment, case study, reproducible evaluation, real
  integration): useful when the bottleneck is credibility or proof.
- **Demo asset** (`tool demo`, sample project, interactive playground,
  self-contained example): useful when users need to experience the behavior.
- **Static visual**: useful when the value is structural (architecture, gap map,
  evidence map, feature/value relationships).
- **Interactive visual**: useful when exploration materially improves
  understanding (time scrubber, capability explorer, evidence drill-down).
- **Motion/video asset**: useful specifically when **change through time is itself
  part of the value**.
  - Good candidates: late information moving into historical time; capability
    collapse; codebase evolution; issue accumulation; state transition.
  - Bad candidates: ordinary feature list; static architecture; configuration
    reference.
  - Heed must not recommend video merely because video is considered useful for
    marketing.
- **Case study**: useful when "Does this work outside the author's own repo?" is
  the blocking question.

## 6. Asset decision rule

Every recommended asset must have this chain:

```text
PROJECT GOAL
      ↓
OBSERVED BOTTLENECK
      ↓
WHY CURRENT ASSETS DON'T RESOLVE IT
      ↓
MISSING ASSET
      ↓
EXPECTED PROJECT OUTCOME
```

Example:

```text
Goal:
Make TypedMem's changing-state model understandable.

Observed bottleneck:
Late-arriving temporal semantics are difficult to understand from text.

Existing assets:
README example exists but requires reading several paragraphs.

Missing asset:
Short motion explanation.

Why motion:
The core distinction is arrival order vs effective-time order.

Expected outcome:
A reader can understand the semantic distinction in seconds.
```

Without that chain, the asset cannot enter the roadmap.

## 7. No speculative asset generation

Heed must reject reasoning such as:

> "Most successful projects have videos."
> "A polished landing page would help."
> "You should write more blog posts."
> "Every OSS project should have a demo."

These are generic recommendations, not project evidence. They should be treated
like any other unevidenced opportunity and refused.

## 8. Readiness model

Heed should produce a compact readiness state. Example:

```text
PROJECT READINESS

Correctness      ✓
Product          ✓
Credibility      ✓
Proof            ✓
Understanding    ✓
Trial            ✓
Distribution     !

Current bottleneck:
DISTRIBUTION
```

However, this is **not a score**. Do not produce `Readiness: 87%`. Do not average
dimensions. Each state is evidence-backed.

Possible states:

```text
✓ ready enough
△ incomplete
— missing
○ intentionally out of scope
! current bottleneck
? insufficient evidence
```

## 9. "Ready enough", not "complete"

Heed must never claim:

> **The product is complete.**

Instead:

> **Ready enough for the current goal and next stage.**

Software always has more possible work. The purpose is to determine whether
additional work is currently more valuable than moving to the next stage.

## 10. Existing asset inventory

Before recommending a new asset, Heed must inspect what already exists. Possible
inventory:

```text
README             ✓
Quickstart          ✓
Docs                ✓
Benchmark           ✓
Demo                ✓
Static visual       ✓
Interactive visual  ✓
Video/GIF           ✓
Case study          —
External proof      —
```

But absence alone does not create a gap. For example, `Case study —` does **not**
mean "Create case study". Only an evidenced bottleneck may activate it.

## 11. Prefer reuse over creation

If an appropriate asset already exists, Heed must not recommend creating another
one. Example, TypedMem:

```text
Temporal Truth Explorer    ✓
GIF                        ✓
MP4                        ✓
Still image                ✓
Benchmark                  ✓
README story               ✓
```

Therefore Heed should conclude:

> **No new explanation asset is required. Existing assets are ready for
> distribution.**

Then:

> **Hand off to Beacon.**

This rule protects the owner from endless polishing.

## 12. Beacon artifact integration

Heed may read Beacon artifacts if available. For example:

```text
.beacon/value.json
.beacon/pains.json
.beacon/experiment.json
```

Beacon evidence can establish:

- users do not understand a value;
- a specific pain is externally repeated;
- current messaging is unsupported;
- distribution is weak;
- an existing asset has or has not generated qualified response.

But Beacon cannot directly insert work into Heed's roadmap. Heed still applies:

> project goal
> scope
> evidence gates
> owner decisions.

## 13. Handoff artifact

When Heed determines that distribution is the current bottleneck, it should write a
small machine-readable handoff. Suggested:

```json
{
  "status": "ready_for_distribution",
  "bottleneck": "distribution",
  "goal": "Get the product in front of developers with the identified problem",
  "available_assets": [
    {"kind": "interactive_visual", "name": "Temporal Truth Explorer"},
    {"kind": "video", "name": "Late-arriving fact animation"},
    {"kind": "proof", "name": "ReliAgent benchmark measurement"}
  ],
  "missing_assets": [],
  "handoff": "beacon"
}
```

Beacon can then consume this rather than rediscovering project readiness.

## 14. Roadmap behavior

The readiness feature participates in `/heed plan`. Example sequence:

1. **NOW:** Fix inconsistent current-state API. No distribution asset should
   outrank this.
2. After it is resolved: measure the headline state/history claim.
3. After proof exists: create an explanation asset for late-arriving temporal
   state.
4. After Explorer/video exist: no project asset gap remains. Distribution is now
   the bottleneck → Beacon.

The roadmap is allowed to have **zero engineering NOW items**. This is an explicit
requirement.

## 15. Visual report

The Heed report should gain a compact **Readiness** scene, not a large dashboard.
Example:

```text
               PROJECT READINESS

CORRECTNESS      ●──────── ready
PRODUCT          ●──────── ready
PROOF            ●──────── ready
UNDERSTANDING    ●──────── ready
TRIAL            ●──────── ready

DISTRIBUTION     ◉──────── BOTTLENECK
                           │
                           ▼
                        BEACON
```

Below:

```text
ASSETS READY

✓ benchmark
✓ quickstart
✓ interactive visual
✓ short video
✓ static image

No new asset recommended.
```

If an asset is missing for a reason:

```text
UNDERSTANDING    ◉──────── BOTTLENECK
                           │
                           ▼
                 Missing: visual explanation

Why:
The product's headline behavior depends on
arrival order vs effective-time order.
```

## 16. Evidence on demand

As with Beacon report v2, the first view should remain visual. Clicking a readiness
dimension reveals:

```text
PROOF · READY

● LongMemEval history: 0/11 → 11/11
● GoodAI: 9/9
● Mode A temporal: 1.00

Sources →
```

Clicking a missing asset:

```text
VIDEO · RECOMMENDED

Why motion:
The user must see a late record arrive now
and move backward into historical time.

Existing alternatives:
README text
static timeline

Why insufficient:
The distinction requires several sentences
to explain in static form.
```

## 17. TypedMem expected behavior

This serves as the first acceptance case. At the current state of TypedMem, Heed
should approximately produce:

```text
Correctness      ✓
Product          ✓
Credibility      ✓
Proof            ✓
Understanding    ✓
Trial            ✓
Distribution     !

Assets:
✓ README
✓ docs
✓ benchmark
✓ quickstart
✓ Temporal Truth Explorer
✓ GIF
✓ MP4
✓ still image

Recommendation:
Do not build another explanation asset.

Current bottleneck:
Distribution.

Next owner:
Beacon.
```

If Heed instead recommends "create a product video", that is a failure, because a
suitable video already exists.

## 18. AgentSeism expected behavior

Potential output:

```text
Correctness      ✓
Product          ✓
Proof            ✓
Understanding    ✓
Trial            △
Distribution     !
```

Existing assets include the Regression Explorer, an animated demo, Stage C
evidence, and real PR examples.

Heed should not recommend another visualization simply because distribution is
weak. It may instead conclude: existing proof/visual assets are sufficient;
distribution or external adoption is the unresolved stage.

## 19. Heed expected behavior

This is a useful contrast. Heed currently has real TypedMem dogfood, a visual
report, and protocol tests, but external proof is still limited. Potential result:

```text
Correctness      ✓
Product          ✓
Credibility      ✓
Proof            △
Understanding    ✓
Distribution     —
```

Recommendation:

> Create 2–3 hand-checked case studies on unfamiliar repositories.

Not:

> make a marketing video.

This demonstrates that asset selection depends on the bottleneck.

## 20. Validation rules

The validator must reject:

- **Unsupported bottleneck:** "Distribution is the bottleneck" without evidence
  that earlier blockers are ready enough.
- **Generic asset advice:** "Create a video because videos perform well."
- **Duplicate asset:** recommending a visual/video that already exists and
  addresses the same need.
- **Out-of-scope work:** an asset intended to advertise a capability the confirmed
  goal excludes.
- **Beacon leakage:** recommendations such as "post the video to Reddit", "use
  this hook", "target LangChain developers" belong to Beacon and must be rejected
  from Heed output.

## 21. Success criteria

The feature succeeds if:

1. Heed can identify when engineering is no longer the bottleneck.
2. It can recommend a missing asset only when evidence justifies it.
3. It does not require every project to have every asset.
4. It prefers reuse of existing assets.
5. It can explicitly produce zero new engineering work.
6. It hands distribution problems to Beacon.
7. Beacon can consume the handoff without re-evaluating project readiness.
8. The visual report makes the bottleneck understandable within 5–10 seconds.
9. The same protocol produces materially different recommendations for TypedMem,
   AgentSeism and Heed.
10. No readiness percentage or synthetic overall score is produced.

## 22. Non-goals

This feature does **not**:

- choose a Reddit community;
- write social posts;
- generate marketing hooks;
- optimize SEO;
- decide audience;
- schedule launches;
- post content;
- measure social engagement;
- predict product-market fit;
- require video;
- automatically generate the recommended asset.

Those belong elsewhere, primarily Beacon.

## 23. Implementation order

Implement conservatively:

1. **Readiness inference.** Add readiness dimensions to `/heed plan` using existing
   goal, health, plan and optional Beacon evidence. No new searching.
2. **Asset inventory.** Detect existing docs / benchmark / demo / visual / video /
   case study, but do not treat absence as a problem automatically.
3. **Bottleneck → asset rule.** Require an explicit evidence chain before
   recommending an asset.
4. **Beacon handoff.** Write a small structured artifact when distribution becomes
   the bottleneck.
5. **Visual report.** Add the compact readiness/bottleneck scene.

## 24. Design principle

The feature should enforce one rule above all:

> **Heed should help the owner know when to stop building.**

A project with a correct product, defensible proof, clear explanation and usable
assets should not receive another synthetic engineering roadmap merely because an
LLM can imagine more work.

At that point Heed's most useful recommendation may simply be:

> **Nothing important is missing.**

---

## Review notes (2026-09-27, checked against the repos; not yet decided)

These are facts found while filing this doc. They don't change the design; three of
them affect the acceptance cases.

1. **§17 TypedMem Credibility ✓ doesn't match the evidence today.** `/beacon value`
   v0.1 lists two open stop-saying claims in the TypedMem README: README:127 "AI
   agents start believing their own hallucinations" and README:215 "Debugging
   hallucinating agents" as a primary use. Under §4.3 ("README makes unsupported
   claims"), the honest state is △, unless the owner decides those lines are
   acceptable. (README:207 and README:281 were fixed in PR #16.)
2. **§11/§17 GIF and MP4 exist, but not where a repo inventory can see them.** The
   Explorer (`docs/explorer/`, live at lyr-ai.github.io/typedmem/explorer/) and
   the still image (`docs/explorer/truth-through-time.png`) are in the repo. The
   GIF and MP4 exist only on the owner's machine (`~/Desktop/truth-through-time/`).
   An inventory that reads the repo would mark video as missing, and could then
   fail §17 by recommending one. The inventory probably needs an
   exists / published / linkable distinction, or an owner-declared asset list.
3. **§12 Beacon file names.** Beacon writes `.beacon/launch.json` (pains, audiences
   and the one experiment together), `.beacon/value.json` and `.beacon/history/`.
   There is no `pains.json` or `experiment.json`.
4. **§16 proof figures.** "LongMemEval history 0/11 → 11/11" is in the committed
   reliagent-bench result (df0ebc6). "GoodAI 9/9" and "Mode A temporal 1.00" still
   need their sources cited before they appear in a report.
5. **Sequencing.** The standing rule is that no new Heed features ship before
   `/heed history` is designed from real runs. The history requirements already
   include "if a plan shows NOW = 0 or only proof/distribution, don't invent
   features; hand ownership to Beacon", which is §14 of this doc. Whether
   readiness comes before, after, or together with history is an owner decision.
