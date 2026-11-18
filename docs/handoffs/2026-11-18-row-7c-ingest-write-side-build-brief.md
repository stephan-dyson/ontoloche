# Row 7c brief — the ingestion build, write side

**Drafted and opened 2026-11-18 by the supervisor, after row 7b landed (`65418b7..01925f6`, [`7B-RUN.md`](https://github.com/stephan-dyson/ontoloche/blob/main/docs/runs/7B-RUN.md)) and merged into `main`.** The founder said on 2026-11-18 "you don't need my permission to move to the next item on the roadmap". This is the second half of the Phase 3 build split in [row 7b's brief](https://github.com/stephan-dyson/ontoloche/blob/main/docs/handoffs/2026-11-18-row-7b-ingest-read-side-build-brief.md) §0.

---

## 0. What is settled, and what stays open

**Built by row 7b and not reopened here:** `INGEST.md` §1, §2, §3, §5, §6 and §7. That covers primitives 22 and 23, `resolve_instance` with five outcomes, `MatchPolicy`, `Condition`, and 77 `C20` ids, each seen red by mutation. Row 7c builds on them and changes their behaviour only where §4 requires it.

**Settled before this row opens:** everything row 7b's brief §0 lists (R58 to R60, R77, R78, R99, and the supervisor's process calls on Q85, Q88, Q90 and Q93). Q85 applies here too: a shape amendment lands in the change that introduces it, with its code.

**Open and the founder's, built as the default in force and pinned, never decided here:**

- `Q87` → DECISIONS-OPEN item 28. Default `warn`: the propose path does not refuse when `consumers()` returns `known=0`, and it carries `consumers_unregistered`. This row is where proposing lands, so this is where the default gets its pin.
- `Q89` → item 29. Default `allow`: the shipped `review_invocation` does not check that the reviewer differs from the actor. The row drives the review queue (rule 4-6) and pins today's behaviour.
- `Q91` → item 30. Default `unknowable`, built by row 7b and unchanged.
- Item 31 (row 7b): a retired entity with no successor is served as today. If §4 would propose under a tombstone, pin what the code does and record it against item 31. Do not choose.

**Open and not refusals, recorded rather than decided:** `Q86` (does the project ship a matcher) and `Q92` (rules 4-10 and 4-11 assume *same label means same thing*, and `InstanceContext.row_attributes` is inert). Build rules 4-10 and 4-11 as specified, and measure what Q92 predicts on the real `erm2-nwe9` slice: 7a saw `{'proposed': 1044, 'reused': 2298}` over 3,342 rows. Record the number. Fixing Q92 is a design change above this row.

## 1. What the row delivers

1. **The five `ACTIONS.md` amendments in `INGEST.md` §4.4, landed in `ACTIONS.md` and in `ontoloche/actions.py` together**, so `check_spec_drift.py` stays green:
   - **A1:** an `InputSpec.ref` value for a thing that does not exist yet (`CandidateRef`).
   - **A2:** a `results` slot on `Invocation` that carries the minted `InstanceRef` (rule 4-3), never an effect's `why`.
   - **A3:** `record_invocation` takes `approval_mode` and `warnings`, so one invocation can go to `review` (rule 4-5).
   - **A4:** `invocations` can answer rule 4-11's question (who holds an unwritten proposal for this identity) with a completeness answer that is not always incomplete.
   - **A5:** the invocation records which `MatchPolicy` governed (rule 5-7).
   Each amendment changes a printed shape, so each one is red first in the `C19` suite as well as `C20`, and the existing `C19` tests stay green.
2. **§4's 13 rules** (4-1 to 4-13), pinned by `C20-27` to `C20-34`, `C20-69` to `C20-72` and `C20-81`. `check_spec_drift.py` must report all 90 `C20` ids built when the row ends.
3. **`INGEST.md` §8.1a finding 3 (Q92)** measured and recorded as above, not fixed.
4. **Finding 6 (ING11's dual-write curve)** measured against the built propose path. 7a's claim: at 100% dual-written the `ambiguous` rate is 100%, and the queue drains only when the host deletes the predecessor rows. Confirm or refute it against code.
5. **Finding 7:** re-derive `INGEST.md` §13's route table for the eight `I-` cells, and settle route 9's *"or by two concurrent workers"* clause against a constructed concurrent case.
6. **Async mirror regenerated** with `tools/unasync.py`, never by hand.

## 2. Out of scope

- Any change to row 7b's read rules, except where a §4 rule depends on one and the spec says so. A read-side defect found here gets fixed with a test and noted in the run record. A read-side refusal question is routed.
- The non-default answers to Q87, Q89, Q91 or item 31.
- Fixing Q92, and a thirteenth `Condition` term (Q90).
- Connectors, extraction, orchestration (`VISION.md` §6). The host writes the instance row (rule 4-2), and this project performs no write to it.
- Row 7b's recorded minors (§2.6's three build-lens minors). They wait for the next read-side row.
- D14 and B5-1.

## 3. Design tests (standing constraint 7), expected outcomes in §0 before any run

- **UC2 CMS:** an ingest act over real CMS rows proposes for novel labels, reuses for `existing`, puts `ambiguous` proposals in `review` mode with `instance_ambiguous_at_proposal`, and proposes nothing for `unknowable` or `not_an_instance` (rule 4-7).
- **UC3 NYC:** one ingest act over the `erm2-nwe9` slice gives the Q92 measurement, and rule 4-11 stops a second proposal for an identity whose row is not yet written, including after the first proposal is reviewed.
- **Allowlist:** an ingest family that declares `Effect(op="propose_type", kind="predicate")` is refused (rule 4-8).
- **Kill row:** the row pre-registers which doors propose-at-ingest and the five amendments open, starting from 7a's `I-4` and `I-5` records and row 7b's door predictions, and predicts where each shape recurs before any lens runs.

## 4. How the row runs (the project's standing process)

- §0 of `docs/runs/7C-RUN.md` is pre-registered and committed first, before any code or test.
- **Tests red first, then code.** Row 7b wrote most of its code before its tests and had to prove each test with a mutation sweep afterwards. Here, each test is committed red before the code that turns it green, or the run record states per id why not.
- Every `C20` and `C19` id this row touches is shown red by mutation (extend `docs/tools/ingest_mutation_sweep.py`).
- All five gates exit 0: `check_links`, `check_spec_drift`, `check_merge_guard`, `check_capability_matrix`, `check_skip_census`.
- The adversarial loop runs to row 6j's stopping rule (`6J-RUN.md` §5 item 10), with the cap pre-registered in §0.
- A finding that would make the code refuse or hold something is routed to `docs/DECISIONS-OPEN.md` and the default in force is built. Everything else is the row's call, recorded with its reason in `7C-RUN.md`.
