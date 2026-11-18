# Row 7b brief — the ingestion build, read side

**Drafted 2026-11-18 by the supervisor and opened the same day.** The founder said on 2026-11-18 "you don't need my permission to move to the next item on the roadmap", so this replaces Q48's "opening the row is the founder's" for the Phase 3 build. Row 7a wrote the spec ([`INGEST.md`](https://github.com/stephan-dyson/ontoloche/blob/main/docs/specs/INGEST.md) v0, [`7A-RUN.md`](https://github.com/stephan-dyson/ontoloche/blob/main/docs/runs/7A-RUN.md)). No product code for it exists yet, apart from `InstanceRef` in `ontoloche/edges.py`.

---

## 0. Why the build is two rows, and what is already settled

**The split (a process call, the supervisor's).** `INGEST.md` has 90 rules. 77 of them (§1, §2, §3, §5, §6, §7) are reads: resolution over host-held rows, with no write anywhere. The other 13 (§4, propose-at-ingest) cannot run until five amendments land in `ACTIONS.md` (§4.4, A1 to A5), and those change printed, drift-checked shapes backed by `ontoloche/actions.py`. Different doors, different kill-row exposure, different review. So:

- **Row 7b (this row):** the read side. §1, §2, §3, §5, §6, §7.
- **Row 7c (next):** the write side. §4 and amendments A1 to A5.

**Settled before this row opens:**

- R58, R59, R60 (paging with one `known` rule, a tenant-blind protocol, one three-valued `Condition` language), R77 and R78 (instance resolution lives here and the host holds the instances), Q56 ruled `read` (R99).
- **Q85 (supervisor, process):** a reserved value or rule id lands in the change that introduces it, which is R3's plain words. The build row claims the `C20` ids and lands the `instance_*` values as it builds each rule.
- **Q88 (supervisor, process):** the Rule of the ordering extends to Phase 3. Every shape is exercised against the public data (CMS, NYC `uvpi-gqnh` / `erm2-nwe9` / `693u-uax6`) and a conflict with the partner's shape is recorded, never resolved toward the partner. `INGEST.md` was written under it.
- **Q93 (supervisor, process):** the row measures rule 3-19's real read cost and reports it in the run record. No timing is pinned in the spec.
- **Q90:** no thirteenth `Condition` term in this row. R60 makes that a § row with a contract id.

**Open and the founder's, built as the spec's default and pinned, never decided here:**

- `Q87` → [DECISIONS-OPEN item 28](https://github.com/stephan-dyson/ontoloche/blob/main/docs/DECISIONS-OPEN.md). Default `warn` (`consumers_unregistered` on the resolution).
- `Q91` → item 30. Default `unknowable` on a closure hop into changed governed facts (rules 3-18, 5-10, 6-18, 7-5).
- `Q89` → item 29. Not on this row's surface.

**Open and not refusals, recorded rather than decided:** `Q86` (does the project ship a matcher, or require a deployment-supplied resolver) and `Q92` (`InstanceContext.row_attributes` is inert). Build the spec as written. Where either one bites in a design test, record the measurement in the run record as a contortion.

## 1. What the row delivers

1. **§8.1a finding 1 first (E22):** `C20-05` and `C20-08` get a check that can go red, by mutation. Then the rest of §6.9c's eight named mutations from `7A-RUN.md`, each shown red when its rule is removed.
2. **§8.1a finding 2 second (E2):** primitive 22 (`get_instance_checked`) resolves the successor closure and applies the effective entry's predicate. The same identity must not be found under the declared name and absent under the effective one.
3. **The two read primitives (§2)**, each with its capability flag (§2.3), paged per R58 (§2.2), with `host_filter` as a declared filter and `label` a hint that may not narrow (§2.1), and the flat-form guard (§2.4).
4. **`resolve_instance` (§3)** with five outcomes, completeness checked before any of them (Rule U, §3.4), the successor closure (§3.4a) and a countable extent (§3.4b).
5. **The match-vs-propose gate as a governed fact (§5)** with `MatchPolicy` on the entry and no inheritance by a successor (§5.3).
6. **`Condition` (§6)**, twelve terms, three-valued, evaluated by the registry, no inheritance by a successor (§6.3a).
7. **Host obligations (§7)** enforced where the spec makes them enforceable: consumer registration, a successor's governed facts, the host's entity vocabulary and tenancy predicate.
8. **§8.1a findings 4, 5 and 8** handled in this row: measure rule 3-19's cost (Q93), kill or record the thirteen mutation survivors, and reconcile §9's reserved ordinals with `types.WARNING_VALUES`. Findings 3, 6 and 7 belong to row 7c.
9. **Every rule pinned by its `C20` contract id** on all three backends, with `check_spec_drift.py` reporting each one built, not planned.
10. **Async mirror regenerated** with `tools/unasync.py`, never by hand.

## 2. Out of scope

- §4 and amendments A1 to A5 (row 7c). Nothing in this row writes an instance, records an invocation or proposes.
- Any behaviour other than the spec's default at Q87, Q89 or Q91.
- Fixing Q92's inert `row_attributes`. It is a design change above both build rows.
- Connectors, extraction, orchestration (`VISION.md` §6). The host holds the rows.
- The D14 retire-then-alias defect and B5-1 from row 8c.

## 3. Design tests (standing constraint 7), expected outcomes in §0 before any run

- **UC2 CMS:** *"I already know 38 of these"* (§5.2) reproduces through real calls rather than the 7a probe, and the five outcomes are each reached on real CMS labels.
- **UC3 NYC:** the tenancy predicate excludes above the primitive (R59), the CA and CO fixture's retire case answers `unknowable` under the Q91 default, and a truncated scan answers `unknowable`, never `proposal`.
- **Paging:** a guard never reads a page (R58), and an unfinished read cannot reach an outcome (rule 3-6).
- **Kill row:** the row pre-registers which doors the primitives and `resolve_instance` open, starting from the `I-1` to `I-8` instance-surface records in `7A-RUN.md`, and predicts where each record's shape recurs before any lens runs.

## 4. How the row runs (the project's standing process)

- §0 of `docs/runs/7B-RUN.md` is pre-registered and committed first, before any code or test. It holds the design-test expectations, the kill-row door predictions and the review-round cap.
- Tests red first, in the contract suite, on all three backends. The postgres leg needs `oo-pg` on port 55432.
- All five gates exit 0: `check_links`, `check_spec_drift`, `check_merge_guard`, `check_capability_matrix`, `check_skip_census`.
- The adversarial loop runs to row 6j's stopping rule (`6J-RUN.md` §5 item 10), with the cap pre-registered in §0.
- A finding that would make the code refuse or hold something is routed to `docs/DECISIONS-OPEN.md` and the spec's default is built. Everything else is the row's call, recorded with its reason in `7B-RUN.md`.
