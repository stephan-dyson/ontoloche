# STATUS — where we are, at a glance

**Updated:** 2026-08-29 01:30 (updated by the supervisor at every landing). Detail: [ROADMAP.md](ROADMAP.md) · every doc: [docs/README.md](docs/README.md).

| Roadmap item | Status |
|---|---|
| 0.1 Tenshen archaeology | ✅ done |
| 0.2 HHS pollution question | 🟡 assumed (A1) — office visit refines |
| 0.2b What contractors produce | 🟡 assumed (A2) — office visit refines |
| 0.3 Prior art | ✅ done |
| 0.4 Ingestion question | 🟡 assumed (A3) — office visit refines |
| 0.5 Proposal-quality test | ✅ done |
| #1 `docs/specs/INTERFACE.md` v0 | ✅ done |
| #2 `docs/specs/PACKAGE.md` v0 | ✅ done |
| #3 Phase 2A reference implementation | ✅ done — 229 tests green, both backends |
| 3b Async adapter | ✅ done — 267 tests green, both async backends; generated from the sync source, not forked ([docs/runs/3B-ASYNC.md](docs/runs/3B-ASYNC.md)) |
| Docs folder reorg | ✅ done — `docs/specs` `findings` `runs` `tools` + link checker |
| `docs/USE-CASES.md` — the three validation fixtures | ✅ done |
| 3c Use-case validation pass (UC3 + adversarial loop on INTERFACE/PACKAGE) | ✅ done — kill-criterion mechanism exercised and **held**; 7 contortions recorded, suite 109 → 124, **nine** code defects fixed; **18 review rounds, no clean pass** — closed on an escalation ([`docs/findings/3C-VALIDATION.md`](docs/findings/3C-VALIDATION.md)). **Q1–Q8 ruled as R6–R13** 2026-08-29 |
| 3d Upstream fixes from beacon 21.1 (R5 savepoint transactions, degraded reference leg, attribute projections, doc sync, R8, R12, R13) | ✅ done — **the transaction seam beacon 21.2 builds on**. Borrowed connections use SAVEPOINTs and never commit; a **third** reference leg that is natively degraded, not simulated; a per-leg coverage report (*a conformance claim without its coverage line is not a claim*); suite 124 → **129**, `340 passed` / `374 passed`. **Three adversarial rounds, six reviewers, no clean pass** — closed on the cap with a convergence note; **five BLOCKING** findings, every one of them a lying adapter that had been passing the suite ([`docs/runs/3D-RUN.md`](docs/runs/3D-RUN.md)) |
| #4 `docs/EDGES.md` v0 (now includes type-to-type `equivalent_to` edges, R7) | ⏳ queued (after 3d) |
| 3e v0.1 amendments (R6 cross-namespace lookup, R10 name-level schemas, R11 `reinstate`) | ⏳ queued (after #4) |
| #5 Phase 2B Tenshen migration (beacon) | ⏳ beacon 21.1 spec landed (`6e87d61a`, Draft, founder approval pending); 21.2 build should target 3d for the transaction seam |
| #6 Actions-registry spec | ⬜ not started |
| #7 Phase 3 ingestion / mapping | ⬜ not started |
| Phase 4 generalise | ⬜ not started |

Legend: ✅ done · 🔵 in flight · ⏳ queued · 🟡 assumed, pending evidence · ⬜ not started · 🔴 blocked
