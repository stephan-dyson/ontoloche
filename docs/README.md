# open-ontology — document index

Every document, organised by what it is for. Links are GitHub links to `main`. Newest state first: the [roadmap](https://github.com/stephan-dyson/open-ontology/blob/main/ROADMAP.md) says what is done and what is next; the [decisions](#decisions) say why.

## Strategy — read to argue with the venture

| Doc | What it is |
|---|---|
| [VISION.md](https://github.com/stephan-dyson/open-ontology/blob/main/VISION.md) | The thesis, what was observed, what is assumed, what is not validated. Claims tagged [Observed] / [Inferred] / [Assumed]. |
| [STATUS.md](https://github.com/stephan-dyson/open-ontology/blob/main/STATUS.md) | **Where we are, at a glance** — one row per roadmap item, one status each. Updated at every landing. |
| [ROADMAP.md](https://github.com/stephan-dyson/open-ontology/blob/main/ROADMAP.md) | Phases 0–4, kill criteria, standing constraints, and the **"Ordering for the Tenshen rebuild"** table — the live execution order. |
| [USE-CASES.md](https://github.com/stephan-dyson/open-ontology/blob/main/docs/USE-CASES.md) | **The three validation fixtures** every spec and design is tested against — Tenshen (single-writer registry), CMS citations (flat government export), NYC Open Data (many agencies, colliding words) — plus the validation protocol and Wikidata as governance precedent. |
| [WALKTHROUGH.md](https://github.com/stephan-dyson/open-ontology/blob/main/docs/WALKTHROUGH.md) | The product, concretely: a non-technical analyst goes from a spreadsheet to a sent action in five steps. |

## Specs — the contracts being built against

| Doc | Status | What it is |
|---|---|---|
| [INTERFACE.md](https://github.com/stephan-dyson/open-ontology/blob/main/docs/INTERFACE.md) | v0, unstable | The type-registry contract: twelve calls around a proposal→approval loop; `consumers`, `predicates`, lifecycle; the closed fourteen-value `Refusal.reason` vocabulary (§5.12); Tenshen and CMS design tests. |
| [PACKAGE.md](https://github.com/stephan-dyson/open-ontology/blob/main/docs/PACKAGE.md) | v0, unstable | The `open_ontology` package: a fifteen-primitive storage-adapter protocol, SQLite + Postgres backends, `attributes` schema-per-kind, and the **109-test contract suite that defines conformance** (the Phase 2B gate). |

## Findings — evidence, in the order it was produced

| Doc | Roadmap row | Headline |
|---|---|---|
| [FINDINGS-0.1-tenshen-archaeology.md](https://github.com/stephan-dyson/open-ontology/blob/main/docs/FINDINGS-0.1-tenshen-archaeology.md) | 0.1 | Seven vocabularies in one codebase: five are capability predicates, not duplicates; the only shipped incident was a **silent per-consumer drop**. Forced `consumers` and `predicate` into the interface. |
| [0.3-prior-art.md](https://github.com/stephan-dyson/open-ontology/blob/main/docs/0.3-prior-art.md) | 0.3 | No existing interface worth matching call-for-call; Foundry's `status` vocabulary worth matching field-for-field. Migration off Foundry is possible today, onto it is not. |
| [0.5-ground-truth-PREREGISTERED.md](https://github.com/stephan-dyson/open-ontology/blob/main/docs/0.5-ground-truth-PREREGISTERED.md) | 0.5 | Ground truth for the proposal-quality test, committed **before** any proposal was generated. |
| [0.5-RESULTS.md](https://github.com/stephan-dyson/open-ontology/blob/main/docs/0.5-RESULTS.md) | 0.5 | Four blind agents, four model tiers, public CMS data: structure right 4/4; Opus 0 errors in 12 claims; **Haiku silently inverted the CMS severity scale.** Model tier is a product parameter. |

## Run records — what the code actually does

| Doc | Row | Result |
|---|---|---|
| [2A-RUN.md](https://github.com/stephan-dyson/open-ontology/blob/main/docs/2A-RUN.md) | #3 | **229 passed, 0 failed, 0 skipped** in one run — SQLite 113 + Postgres 16.14 113 + 3 backend-independent; CMS design test reproduces every pre-registered count; fourteen recorded deviations. |
| [3B-ASYNC.md](https://github.com/stephan-dyson/open-ontology/blob/main/docs/3B-ASYNC.md) | 3b | **267 passed, 0 failed, 0 skipped** in one run — the **same 109 contract ids, same test-function names**, on async SQLite + async Postgres 16.14; sync suite still green (`229 passed`), both stacks in one process `496 passed`. The async tree is **generated** from the sync source by `tools/unasync.py`, not forked — a stale mirror fails the suite. Fourteen new deviations, the fourteen of 2A inherited. |

## Decisions — assumptions and rulings, each with what would revise it

| Doc | What it settles |
|---|---|
| [2026-08-28-assumptions-in-lieu-of-office-answers.md](https://github.com/stephan-dyson/open-ontology/blob/main/docs/decisions/2026-08-28-assumptions-in-lieu-of-office-answers.md) | A1–A4: assumed answers to the Phase 0 office questions. **A5 (confirmed by the founder):** Tenshen will be rebuilt on top of open-ontology; it may depend on the package once Phase 2A passes contract tests on CMS data. |
| [2026-08-28-package-v0-rulings.md](https://github.com/stephan-dyson/open-ontology/blob/main/docs/decisions/2026-08-28-package-v0-rulings.md) | R1 async adapter is roadmap row 3b — **landed 2026-08-28, and its "mirroring is mechanical" assumption held**; R2 `attribute_census` stays package-local; R3 `Refusal.reason` is a closed vocabulary. |

## Tools and data

| File | Use |
|---|---|
| [make_sample.py](https://github.com/stephan-dyson/open-ontology/blob/main/docs/make_sample.py) | Cuts the 400-row Montana sample from the public CMS citations file. |
| [characterize.py](https://github.com/stephan-dyson/open-ontology/blob/main/docs/characterize.py) | Counts the pathologies over all 419,479 rows (the numbers in 0.5). |

**Standing constraint 0 applies to everything here: no employer data, ever — public CMS data only.**

*Planned tidy-up (after roadmap row 3b lands, so no in-flight commit is disturbed): move files into `docs/specs/`, `docs/findings/`, `docs/runs/`, `docs/tools/` and rewrite the relative links. This index is updated in the same change.*
