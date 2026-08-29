# STATUS — where we are, at a glance

**Updated:** 2026-08-29 (updated by the supervisor at every landing). Detail: [ROADMAP.md](ROADMAP.md) · every doc: [docs/README.md](docs/README.md).

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
| 3c Use-case validation pass (UC3 + adversarial loop on INTERFACE/PACKAGE) | ✅ done — kill-criterion mechanism exercised and **held**; 7 contortions recorded, suite 109 → 117, two design defects fixed ([`docs/findings/3C-VALIDATION.md`](docs/findings/3C-VALIDATION.md)). **R5–R11 want a ruling** |
| #4 `docs/EDGES.md` v0 | ⏳ queued (after 3c) |
| #5 Phase 2B Tenshen migration (beacon) | ⏳ beacon row 21.1 spec in progress; **21.2 is no longer blocked — 3b landed** |
| #6 Actions-registry spec | ⬜ not started |
| #7 Phase 3 ingestion / mapping | ⬜ not started |
| Phase 4 generalise | ⬜ not started |

Legend: ✅ done · 🔵 in flight · ⏳ queued · 🟡 assumed, pending evidence · ⬜ not started · 🔴 blocked
