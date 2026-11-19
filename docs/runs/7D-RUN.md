# 7D-RUN — roadmap row 7d: the ingestion defect row (ING15 first)

**Status:** in flight. **Opened** by the supervising session on 2026-11-19 under the founder's instructions *"keep the project moving forward"* (2026-11-12) and *"you don't need my permission to move to the next item on the roadmap"* (2026-11-18). **Brief:** [`handoffs/2026-11-19-row-7d-ingest-defects-brief.md`](https://github.com/stephan-dyson/ontoloche/blob/main/docs/handoffs/2026-11-19-row-7d-ingest-defects-brief.md). **Fixes:** [`INGEST.md`](https://github.com/stephan-dyson/ontoloche/blob/main/docs/specs/INGEST.md) ING15 and the minors recorded by [`7B-RUN.md`](https://github.com/stephan-dyson/ontoloche/blob/main/docs/runs/7B-RUN.md) §2.6 and [`7C-RUN.md`](https://github.com/stephan-dyson/ontoloche/blob/main/docs/runs/7C-RUN.md) §2. **Branch:** `agent/row-7d`, cut from `main` at `a6e9d7f`, local only.

**Claim tags:** **[Observed]** seen directly in this repo, in a command's output, or on a page opened this row · **[Inferred]** a reasonable read · **[Assumed]** believed, untested · **[guess]** an inference not checked.

---

## §0 — PRE-REGISTRATION, committed before any code and any test

This section is the row's first commit. Every prediction below is made from the brief, `INGEST.md`, `7B-RUN.md` §2.6, `7C-RUN.md` §2 and the shipped code at `a6e9d7f`. A wrong prediction stays here and is scored as a miss in §1.

### §0.1 — What was observed before this section was written

1. **The defect site.** **[Observed]** `IngestAct._remember` (`ontoloche/registry.py`) appends `(kind, effective, label, answer)` on three branches of `land`: `existing` (the host ref), `proposed` and `pending` (the candidate). The memory does not say which branch wrote an entry.
2. **`_similar_candidate`** runs only after the gate answers `proposal`. It keeps every remembered `CandidateRef` within `match_at` of the label under the same effective entry and returns it when there is exactly one. A candidate from a `pending` landing passes that filter, which is ING15. **[Observed]**
3. **`_recall`** (the exact key) recalls the most recent answer for the same normalised label under the same effective entry, `pending` candidates included. `C20-81` pins that a third landing of a `pending` identity is `reused`, not a second `pending`. **[Observed]**
4. **The CMS triple** (`test_c20_ingest.py`): `EAST`~`WEST` 0.971, `WEST`~`WESTON` 0.972, `EAST`~`WESTON` 0.944, under the suite's `POLICY` (`match_at` 0.97, `propose_below` 0.80, margin 0.02). **[Observed]** in the test's comment, not recomputed yet.
5. **The three 7b minors** are where 7B-RUN §2.6 says: `_fetch_instance_rows` in `ontoloche/backends/_sql.py` matches `"decode"` anywhere in the driver's message, and `_non_finite` in `ontoloche/ingest.py` calls `float(value)` on every `numbers.Real` that is not `Integral` or `Decimal` (so `Fraction(10**400)` overflows) and recurses once per path. **[Observed]**
6. **The sweep** (`docs/tools/ingest_mutation_sweep.py`) has no way to run a subset other than `--required`. **[Observed]**

### §0.2 — The fix for ING15, stated so the predictions have a design to be wrong about

1. **The memory records the branch that wrote it.** Each entry gains an origin: `existing`, `proposed`, or `pending` with the holder's invocation id.
2. **`_similar_candidate` reuses only a candidate this act itself `proposed`.** A `pending` candidate and an `existing` ref are skipped. This is the option 7C §2.8 names. *Reason:* a `proposed` candidate is this act's own unwritten identity, so a label the gate relates to it at `match_at` is held by it exactly as A4 would hold it for a fresh act. A `pending` candidate's identity belongs to another row, the holder, and the gate's relation is not transitive, so a label near the pending one can be distinct from the holder's (`EAST`~`WESTON` 0.944).
3. **The exact-key recall is unchanged.** A repeat of the same normalised label recalls the `pending` candidate, as `C20-81` pins. *Reason:* the exact label is the key the gate itself uses, and a fresh act landing it would be `pending` behind the same holder, so no identity is lost or merged.
4. **The `reused` why names what was recalled.** A recalled `pending` candidate's why says it was landed pending behind the holder's invocation id. The similar-candidate why ("this act already proposed this identity") becomes true by construction. (ING15 MINOR, 7C §2.8 finding 2.)
5. **The invariant the fix is meant to give:** whenever the act lands a label `reused` through the similar step, a fresh act landing the same label against the same ledger would mint nothing either (it lands `pending`). Wherever a fresh act would propose, the act proposes.
6. **No refusal or hold changes.** The fix makes the act record a proposal where it recorded nothing. That is not a ruling on what the registry refuses or holds, so nothing goes to `DECISIONS-OPEN.md`.

### §0.3 — Order, and what "red first" means here

1. This section, committed alone.
2. **ING15:** one commit with the failing test on the CMS triple, then one commit with the fix. Then the Q92 split re-measured with `docs/tools/ingest_write_probe.py`.
3. **ING15's MINORs:** the why test (red first, predicted red because the current why says "already answered" and names no holder), then the `CandidateRef` filter test under `propose_below` 0.96 (predicted **green on arrival**, because the filter exists and works today: the finding is that nothing pins it) plus its mutation.
4. **Row 7b's three minors**, each a failing test then the fix (§0.6).
5. **Row 7c's recorded non-refusal minors** (§0.7), each a test then the fix, or a test green on arrival plus a mutation where the code is already correct, or a recorded reason it is left.
6. Sweep extended, async mirror regenerated with `tools/unasync.py`, full suite and five gates, then the adversarial loop (§0.9).

### §0.4 — Design tests (brief §3), predicted

#### The CMS triple

Over the suite's `POLICY` and a host table holding none of the three labels: act A proposes `EAST`; act B lands `WEST` (`pending`, held by A's row); act B lands `WESTON`.

| | before the fix (`a6e9d7f`) | after the fix |
|---|---|---|
| act B's `WESTON` | `reused` onto `WEST`'s candidate, no row | **`proposed`**, its own row, no `instance_proposal_pending` warning |
| a fresh act C's `WESTON`, after B's | — | **`pending`** behind B's `WESTON` row |
| `invocations(unwritten_for=WESTON)` after B | — | B's `WESTON` row, alone |

**Predicted:** the red run fails on `reused`, for that reason, on sqlite and postgres. The minimal leg skips (no ledger).

#### The Q92 slice

7c measured, on `710e158`, 3,346 rows: 1,029 `proposed`, 2,310 `reused`, 7 `pending` (69.0% reused). **Predicted:** the fix moves only labels whose one similar remembered candidate came from a `pending` landing, and there are at most 7 such candidates, so `reused` falls by a small number, single digits [guess], and the share stays above 68%. **Q92's 60% floor holds.** If the live slice has moved, the share is the prediction, not the counts.

#### Kill row: the doors the fix touches, and where the ING15 shape is predicted to recur

The ING15 shape: **a candidate this act did not itself propose absorbs a label the gate answered `proposal` for**, so the label gets no row and no reviewer sees it.

| # | door | touched? | prediction before any lens runs |
|---|---|---|---|
| D1 | rule 4-10's similar step, `_similar_candidate` | **yes**, the fix | the defect site, closed by §0.2 item 2 |
| D2 | rule 4-10's exact key, `_recall` | reads the new origin for the why only | **not a recurrence**: the exact label is the gate's own key, and a fresh act lands it `pending` behind the same holder |
| D3 | rule 4-11's pending check, A4's exemption in `_unwritten_for` | **no** | closed since 7c round 2 (`C20-71` r2: a pending row is judged against its own label). Predicted to see the fix's `WESTON` row as a holder for a later fresh act, and B's `WEST` pending row as exempt |
| D4 | rule 4-13's per-act memory, `_remember` | **yes**, every call site gains the origin | predicted no new shape: what is written is unchanged, only labelled |
| D5 | after a retire, the similar step's closure read | no | predicted closed: the origin travels with the entry, and the closure is read now, as today |
| D6 | an `ambiguous` landing the act proposed in review mode | no | **predicted not ING15**: the act proposed it, and a fresh act would land a related label `pending` behind that same row, so the act and a fresh act agree (§0.2 item 5) |
| D7 | two concurrent acts (K6, ING14) | no | open as recorded in 7c, out of scope |

**Predicted: zero new trips on the type-identity kill row.** `check_merge_guard.py` Part A finds no new identity writer.

### §0.5 — ING15's two MINORs (7C §2.8 findings 2 and 3), predicted

- **Finding 2, the why.** Test: on the CMS triple, act B lands `WEST` `pending`, then `WEST` again, which is `reused`. Its why names A's invocation id and does not say "proposed". **Predicted red** on the current text.
- **Finding 3, the filter.** Under a policy of `match_at` 0.97 and `propose_below` 0.96, a host row `EAST`: the act lands `WEST` (`existing`, 0.971 to `EAST`), then `WESTON`, which the gate answers `proposal` (0.944 < 0.96). `WESTON` is 0.972 to the remembered `WEST`. **Predicted:** `WESTON` lands `proposed`, green on arrival, and the mutation that skips only `pending` entries (letting the `existing` ref through) is killed with `reused`.

### §0.6 — Row 7b's three minors (7B-RUN §2.6), predicted

| # | minor | the red test | the fix | predicted |
|---|---|---|---|---|
| B1 | `_fetch_instance_rows` reads any message containing "decode" as an id that cannot be rendered | a dropped host table named `host_decode_site_3` must raise the driver's error, as `host_facility_2` does, not `NotSupported` | match the driver's own decode failure (`UnicodeDecodeError` in the chain, or SQLite's "could not decode to utf-8") instead of the bare word | red, then fixed. `C20-05` r6's real non-UTF-8 row stays green |
| B2 | `_non_finite(Fraction(10**400))` raises `OverflowError` | `condition_problem` over an `eq` operand of `Fraction(10**400)` returns no non-finite problem and does not raise | a `numbers.Rational` is finite and returns `False` before `float()` | red, then fixed |
| B3 | the operand walk recurses and walks a shared sub-list once per path | a list nested 5,000 deep is judged without `RecursionError`; a sub-list shared at 20 levels is judged in under a second | an iterative walk that visits each container once and still reports a container that contains itself | red, then fixed |

Each is small and fails closed today. If any fix turns out larger than the walk above, it is left and §1 says why.

### §0.7 — Row 7c's recorded non-refusal minors, and what this row does with each

Taken from 7C §1.6 and §2.1 to §2.5. The refusal questions (items 32 to 34) are not here.

| # | where 7c recorded it | the minor | plan |
|---|---|---|---|
| C1 | §2.1 | `C20-34` covers two of the four allowlist doors in a test, the probe the rest | extend the test to all four doors, green on arrival |
| C2 | §2.1 | no mutation for A4 reading only the oldest page | add the mutation; add a small-page test if it survives |
| C3 | §1.6, §2.1 | `c20_69`'s mutation is a strawman; rule 4-9's "no `id`" is never reached | add a mutation that gives `CandidateRef` an `id`, killed by the existing assertion |
| C4 | §2.1 | a family with extra required inputs is refused at the gate on each landing, not at `ingest_act` | **left**: moving it is a new refusal at a door that accepts today, every landing already refuses and records nothing, so it fails closed. Recorded, not routed, because the registry refuses the same thing either way |
| C5 | §2.1 | rule 4-10's text names the relation by prose, not by the gate's function | reword `INGEST.md` rule 4-10 to name `similar(norm(a), norm(b)) >= match_at` |
| C6 | §2.2 #5 | a compensation of a compensation | **left**: `ACTIONS.md` defines no undo of an undo, and defining one is new behaviour |
| C7 | §2.2 #6, §2.3 #7 | A4's cursor-repeat guard, and A4 at exactly `match_at` | a test for each, green on arrival, plus a mutation |
| C8 | §2.3 #5 | A4 reads the whole ledger per landing | **left**: correct, and §4.4 (iii) asks for exhaustion, not push-down. Push-down is a feature |
| C9 | §2.3 #6, §2.2 #4 | a compensation in another namespace is invisible; a failed undo reads as compensated | **left**: both fail safe and their root, `_compensated_by` and `ACTIONS.md` §9, predates row 7c |
| C10 | §2.3 #7 | nine A4 guards survive mutation | for each, a mutation and the shortest test that kills it, green on arrival. Any guard that needs more than one short test is left with its reason |
| C11 | §2.5 #4 | a recalled `CandidateRef` keeps the type it was recorded under | **left**: rule 4-10's text already states it |
| C12 | §1.6 | `<n>` on rounded scores survives, no fixture sits on a rounding edge | attempted only if a label pair on a four-place rounding edge turns up in the CMS fixture labels; otherwise left |

### §0.8 — What goes to the founder

**Predicted: nothing.** The ING15 fix records a proposal where the act recorded nothing. B1 to B3 change why a read fails, not whether. C4 is the only place that comes near a refusal, and it is left with the default in force (§0.7).

### §0.9 — The stopping rule and the round cap

Row 6j's adopted criterion (`6J-RUN.md` §5 item 10): the loop ends when a full round finds no in-scope code MAJOR reachable by a shape a contributor would plausibly write, measured by whether the shape, or anything structurally like it, appears anywhere in the live suite. For `INGEST.md` text this row edits, row 8b's adaptation applies: a spec MAJOR counts when it is reachable using only calls and shapes the documents print. A round that produces a MAJOR or BLOCKING fix is followed by a full round that sees it, the last round sees the final code, tests and text, and nothing reviewed is edited while a lens is running.

**Cap: three rounds plus a confirming round** (the brief's). Each round runs three fresh lenses: the build implementer (the fix against `INGEST.md` §4 and this section), the door adversary (D1 to D7, each by mutation or construction), and the fidelity reviewer (every number in §1 recomputed, every red commit re-run). **At the cap:** if round 3 finds a reachable in-scope MAJOR, the row fixes it and runs round 4, the confirming round. If round 4 finds one, the row lands not clean with the finding recorded here and in `STATUS.md`. If a fix lands after the last round, §2 says so plainly.

### §0.10 — The commands this row will run

```
py docs/tools/ingest_write_probe.py [--assert]
py docs/tools/ingest_mutation_sweep.py [--only <substring>]
py tools/unasync.py
py -m pytest --pyargs ontoloche.contract ontoloche.aio.contract     # three legs, OO_POSTGRES_DSN set
py docs/tools/check_links.py
py docs/tools/check_spec_drift.py
py docs/tools/check_merge_guard.py
py docs/tools/check_capability_matrix.py
py docs/tools/check_skip_census.py
```

`OO_POSTGRES_DSN=postgresql://postgres:openontology@localhost:55432/open_ontology` (container `oo-pg`). The full suite takes about 21 minutes, so it runs in the background. `--only` is new this row, for running the sweep in batches.

---

## §1 — Results against §0, scored

Every number below is from a command this row ran, and each is **[Observed]** unless it says otherwise. Hits are stated as hits, misses as misses. §0 is left exactly as committed at `ef1406c`.

### §1.1 — Red first, per commit

| step | red commit | what failed, and why | green commit |
|---|---|---|---|
| ING15 | `9b418dc` | `C20-70` d1, `reused` where the act must propose, on sqlite and postgres (minimal skips at the `NEEDS_LEDGER` mark, `stores_attributes=False`; corrected in round 1, §2.1) | `2de6ffb` |
| ING15 minor 2, the why | `9bd1083` | `C20-70` d1 why test: the why said "already answered" and named no holder | `a0e085b` |
| ING15 minor 3, the filter | `9bd1083` | green on arrival, as §0.5 predicted. Its mutation is killed (§1.5) | — |
| 7b B1 to B3 | `21afb8a` | `C20-05` d1 raised `NotSupported` for a dropped table named `host_decode_site_1`; `C20-47` d1 raised `OverflowError` and `RecursionError` | `812c080` |
| 7c minors | `4c5842f` | eight coverage pins (one `C20-34` d1, seven `C20-71` d1; corrected in round 1, §2.1), all green on arrival, because the code they pin is correct. Each has a required mutation of its own (§1.5) | — |

- **Recomputed:** `EAST`~`WEST` 0.9714, `WEST`~`WESTON` 0.9722, `EAST`~`WESTON` 0.9444, so §0.1 item 4's comment numbers hold.
- **Miss (process): `4c5842f` was committed without its async mirror.** `tools/unasync.py` raised a `SyntaxError` on a chained `_act(...).land(...)`, the shape 7C §1.2 recorded, and a `| tail` hid it. This is the same slip as 7C §1.1's `2d8f7bb`. `f96a366` split the chain into two statements and regenerated the mirror, and `unasync.py --check` reports all 27 files current. The sync tests were right in `4c5842f`; only the aio copy was stale.
- **Miss: a result-conditioned skip.** `C20-34` d1 first skipped when `propose_type` returned no pending proposal (the minimal leg approves at once). `check_skip_census` failed on it. `66555ff` replaced the skip with `requires_capability("stores_attributes", "stores_proposals")`.

### §1.2 — The fix against §0.2

- **Hits:** items 1 to 6 are built as stated. Each memory entry is `(kind, effective, label, answer, origin)`, with origin `existing`, `proposed` or `pending:<holder id>`. `_similar_candidate` skips any entry whose origin is not `proposed`. `_recall` returns the origin, and the `reused` why for a `pending` origin names the holder.
- **Kept, and now redundant:** the `isinstance(answer, CandidateRef)` filter stays in front of the origin test. An `existing` origin always carries an `InstanceRef`, so the origin test alone would skip it. The mutation that pins finding 3 therefore removes both and keeps only a *skip pending* test, which is the plausible wrong fix (§1.5).
- **Text:** `INGEST.md` rule 4-10 now names the relation as `similar(norm(a), norm(b)) >= match_at` (C5) and says the similar step reuses only a candidate the act itself proposed. §8's order paragraph says the same, and ING15's row says fixed (`80aa448`).

### §1.3 — Design tests (§0.4)

| test | predicted | observed | score |
|---|---|---|---|
| CMS triple, act B's `WESTON` | `proposed`, no pending warning | `proposed`, no `instance_proposal_pending` warning | hit |
| CMS triple, fresh act C's `WESTON` | `pending` behind B's row | `pending` | hit |
| CMS triple, A4 after B | B's `WESTON` row alone | B's `WESTON` row alone, `complete=True` | hit |
| Q92 slice, the split | `reused` falls by single digits, share above 68%, the 60% floor holds | 3,346 rows: **1,031 `proposed`, 2,310 `reused`, 5 `pending`**, 69.0% reused (`probe_a0e085b.log`, 18 of 18). Against 7c's 1,029, 2,310 and 7 | **share and floor: hit. The direction: miss.** `reused` did not move. Two `pending` landings became `proposed` |

**The Q92 cost, stated.** The fix proposes two more identities in 3,346 rows, and folds none fewer. **[Inferred]** a net zero on `reused` with two from `pending` to `proposed` is what two pairs of this shape give: a label once reused onto a pending candidate now goes to A4 and is proposed (reused −1, proposed +1), and because it is now this act's own proposal, a later label near it that A4 used to hold `pending` is now reused onto it (pending −1, reused +1). That was not traced label by label. The probe ran on `a0e085b`. `registry.py` has not changed since (an empty diff to `8e06847`), but `ingest.py` and `_sql.py` did, in the 7b fixes, so the probe's whole code path is not the same; §2.2 records a run on `70ea408` and §2.4 the run on the final code.

### §1.4 — The minors (§0.5 to §0.7)

| # | outcome |
|---|---|
| ING15 minor 2 | fixed, red first (§1.1) |
| ING15 minor 3 | pinned, green on arrival, mutation killed |
| B1 | fixed: `_is_decode_failure` walks the exception chain for a `UnicodeDecodeError` or SQLite's "could not decode to utf-8". `C20-05` r5 and r6 (the real non-UTF-8 rows) stay green |
| B2 | fixed: a `numbers.Rational` is finite and is never passed to `float()` |
| B3 | fixed: `_non_finite` is an iterative walk that visits each container once and still refuses a container on its own path. 7b's `c20_47_r4` mutation pointed at the old recursive line, and the new `--list` preflight caught it before the sweep ran. It now removes the walk's push |
| C1 | `C20-34` d1 adds `approve` and `import_types`, green on arrival; the allowlist mutation is killed |
| C2 | `C20-71` d1 reads past the first page with `limit=1`; the mutation that stops after one page is killed |
| C3 | the mutation that gives `CandidateRef` an `id` field is killed by `C20-69` |
| C4 | **left**, as §0.7 said |
| C5 | reworded (§1.2) |
| C6 | **left**, as §0.7 said |
| C7 | both pinned: a repeated cursor answers incomplete, and A4 holds at exactly `match_at` (the policy's `match_at` set to EAST ~ WEST itself) |
| C8, C9, C11 | **left**, as §0.7 said |
| C10 | five of nine pinned (the cursor repeat, the proposals filter, the `why_not` branch, a result for an unmatched input, the `CandidateRef` type check). **Four left:** the kind check (every door refuses a candidate whose kind is not `entity`, so a mixed-kind ledger needs a row written past validation) [Inferred]; `_applied_compensation`'s paging (51 compensations of one row to reach its second page, the same paging shape C2 pins for A4); and the holder sort and *the holder is the oldest*, because rows recorded in the same instant order on random ids (7C §2.4) and no rule says which holder the warning names |
| C12 | **left, not attempted.** No search of the CMS file for a pair on a four-place rounding edge was run |

### §1.5 — Mutation sweep

`docs/tools/ingest_mutation_sweep.py` on `f96a366`: **200 mutations, 199 killed, 1 survivor, 0 not applied or broken, 0 required survivors, exit 0** (`sweep_f96a366.log`). The survivor is 7c's non-required `<n>` rounding case (C12). Row 7d added 16 required mutations (184 to 200): three for ING15 and its minors, four for B1 to B3, and nine for the 7c minors. Eight existing targets were retargeted: five moved with the ING15 fix and three with the 7b fixes. *(Round 1 corrected this sentence, which said 19, twelve and seven, §2.1.)* `--only` and `--list` are new; `--list` is the preflight that counts each target once.

### §1.6 — Suite and gates

- **Full suite, three legs** (sqlite, minimal, postgres on `oo-pg` at port 55432) on `f96a366`: **3,414 passed, 1,010 skipped, 0 failed**, in 20m34s (`suite_f96a366.log`).
- **Gates:** `check_links`, `check_spec_drift` and `check_merge_guard` exit 0. `check_skip_census` failed once (§1.1) and exits 0 at `66555ff`. `check_capability_matrix` is recorded in §2.3 (on `1859baf`) and §2.4 (on the final code).

### §1.7 — Kill row (§0.4)

- **D1 closed** by the fix, pinned by `C20-70` d1 and two required mutations.
- **Predicted zero new type-identity trips. Hit:** `check_merge_guard.py` Part A finds no new identity writer. The fix touches no type row.
- D2 to D7 are scored by the rounds (§2).

---

## §2 — Adversarial rounds (§0.9)

### §2.1 — Round 1, on `8e06847`

Three fresh lenses, read-only, each in its own exported copy. Every finding below was reproduced by the lens on the reviewed commit.

| # | lens | severity | finding | ruling |
|---|---|---|---|---|
| 1 | fidelity | MAJOR (record) | §1.5 said 19 new required mutations (twelve for 7c) and seven retargeted. It is 16 (nine for 7c) and eight (five ING15, three 7b) | **fixed** in §1.5. My own edit script holds 16 `Mutation(` rows; the 19 was a miscount |
| 2 | build, door | MAJOR (claim) | **§0.2 item 5's invariant and §0.4 D2's prediction are false when the ledger changes during the act.** The act proposes EAST, an applied row compensates EAST's row (or `record_result` writes it with no host row), and the act's next WEST lands `reused` onto the dead candidate while a fresh act proposes. The same holds for a `pending` label whose holder is undone or written, and for an `existing` ref whose host row is deleted. Identical at `a6e9d7f` | **scored a miss, recorded as `INGEST.md` ING16, not fixed in row 7d.** See below. **[Reversed in round 2, §2.2 #1: ING16 was fixed for remembered candidates.]** |
| 3 | door | MINOR | after #2's undo, the new `reused` why says the holder "holds an unwritten proposal", which is then false | **fixed:** it says *held ... when this act landed it* and names ING16 |
| 4 | build | MINOR | `_non_finite`'s `done` is keyed on `id()` of containers it did not keep alive, so a mapping that builds its values on each read can free one and hand its id to a later container whose NaN is skipped. A regression from 7b's recursive walk | **fixed red first:** `a69acb5` (`C20-47` d1 red at `n = 2` of `[Fresh(1.0) for _ in range(n)] + [Fresh(nan)]`), then the walk keeps each judged container referenced |
| 5 | door | MINOR | the end-of-members sentinel was the module's `_CONTAINERS` tuple, so an operand carrying that tuple stopped the walk before a later NaN | **fixed red first** in the same pair: a private `_END = object()` |
| 6 | build | MINOR | `IngestAct.land`'s docstring still said "the one candidate this act recorded" | **fixed:** "itself proposed ..., never a pending one" |
| 7 | fidelity | MINOR | §1.1 gave the minimal leg's skip as "no invocation events"; it is the `NEEDS_LEDGER` mark (`stores_attributes=False`) | **fixed** in §1.1 |
| 8 | fidelity | MINOR | §1.1 said seven coverage pins; `4c5842f` adds eight | **fixed** in §1.1 |
| 9 | fidelity | MINOR | §1.3's "the act's code has not changed since" holds for `registry.py` only | **fixed** in §1.3 |
| 10 | door | MINOR | the mutation *A4 `unwritten_for=` takes only a CandidateRef* is killed by an `AttributeError`, not by the `ValueError` the test names | **left.** The test asserts `ValueError` and the mutation removes the only line that raises one, so the kill is the rule's own, reached through a crash. No change |

**Why #2 is not fixed here, stated as a choice.** It is not ING15's shape and the fix did not introduce it: it is present at `a6e9d7f`, unchanged. It is what `INGEST.md` §4.3's first principle prescribes (*"every later reference to the same identity in that act reuses it rather than resolving again"*), so the code follows the rule and the rule has the gap. Closing it means re-checking each remembered answer against the ledger (A4 for a candidate, a host read for an `existing` ref) on every recall, which changes rule 4-10's *resolved once* and puts a ledger read on each of Q92's 2,310 recalls. That is a rule change with a cost, and this row pre-registered neither. So it is ING16, and it counts against row 6j's stopping rule as **out of scope** under §0.9's own test (an in-scope code MAJOR is a defect in what the row set out to build). **[Withdrawn in round 2, §2.2: §0.9 holds no such test. I wrote that definition here, and the ruling rested on it.]** §0.2 item 5 and §0.4 D2 are scored **misses**: both were stated without the *against a ledger nothing else writes during the act* condition they need. ~~This is a ruling for the founder only if they want ING16 closed sooner~~ **[Reversed in round 2, §2.2: the ruling is gone, ING16 is fixed for candidates.]** It was never a refusal or a hold, so it was never a DECISIONS-OPEN item (the kickoff's routing). **[Observed]** for the shapes, by both lenses on sqlite and postgres; **[Inferred]** for the cost.

The fixes are `a69acb5` (red) and the commit after it. Round 1 produced a record MAJOR and code fixes, so round 2 is a full round on the fixed head.

### §2.2 — Round 2, on `0da1620`

Three fresh lenses, read-only, each in its own exported copy.

| # | lens | severity | finding | ruling |
|---|---|---|---|---|
| 1 | fidelity | MAJOR (record) | **§2.1's out-of-scope ruling on ING16 cites a test §0.9 does not hold.** §0.9 (and `6J-RUN.md` §5 item 10) never defines *in-scope*; the parenthetical was mine. By §0.2 item 5, the invariant the fix was meant to give, ING16's similar-step shape is what the row set out to build, and its shapes (`C20-71` r1 and r2) are in the live suite | **upheld, and the ruling is reversed.** §2.1's sentence is marked withdrawn. ING16's candidate shapes are fixed in this row (#2) |
| 2 | door | MAJOR | **A remembered candidate is recalled after a retire without the gate.** The act proposes K under `ltc_facility`; `facility`, whose host table holds K, is retired toward `ltc_facility`; the act's K lands `reused` while a fresh act lands `existing` on `facility#H1`, so one host thing gets two identities. No ledger write is involved, so ING16's text did not cover it. Present at `a6e9d7f` **[Observed by the lens]**. 20 of 3,000 fuzzed scenarios hit it, all this shape **[Observed by the lens, not rerun]** | **fixed red first**, with ING16 (below) |
| 3 | build, door | MINOR | a mapping that builds a new mapping on every read never ends the walk, and memory grows (the recursive walk raised `RecursionError`, so neither refused it) | **left.** No shape like it is in the suite, and a bound on the walk is a new rule |
| 4 | door | MINOR | an object both a NaN float and an empty `Mapping` was judged as a container, and passed (the recursive walk judged it as a number) | **fixed red first:** a number that is also a container is judged as the number |
| 5 | build, door | MINOR | rule 4-13 says the memory is written on every branch that records or recalls, and the similar step's `reused` writes nothing. The code is right: remembering it would bring ING15 back by a second route. The door lens adds that one act can then answer one label two ways (M `reused`, later `pending`), with a fresh act agreeing at each step and no identity lost | **text fixed:** rule 4-13 names the `reused` branches as writing nothing, and why. The two answers are left, recorded here |
| 6 | fidelity | MINOR | §2.1 #5's "red first in the same pair" is loose: the committed red run of `a69acb5` fails at the freed-id loop first, so the sentinel assertion is never reached red. The sentinel defect is real at `a69acb5` (`_non_finite([_CONTAINERS, nan])` is `False` there) | **recorded** here; not re-run as its own red commit |
| 7 | fidelity | MINOR | ING16's *[Observed] on sqlite and postgres* covers five shapes and the lens reproduced four; the deleted-host-row shape rests on round 1's door lens alone | **recorded.** That shape is the one ING16 still leaves (below) |
| 8 | build | none | the build lens agreed with §2.1's ruling, on its reasons rather than on the cited test | noted; #1 governs |

**The fix (round 2).** A remembered `CandidateRef` is no longer returned before the gate. `land` returns a remembered host row at once, as before, and holds a remembered candidate until `resolve_instance` answers. On `existing` the gate's ref is the answer (#2). On `proposal` or `ambiguous` the candidate is reused only if `_alive` finds its row still named by A4 for it, read at this landing: the act's own row for `proposed:<id>` (the origin now carries the row id) and the holder for `pending:<id>`. The similar step applies the same check to each candidate within `match_at`. A row undone or written keeps nothing, and the label goes on to A4 as a fresh act's would. (As committed at `70ea408`, an unreadable read kept nothing too. That is the regression the paragraph below fixes: at `1859baf` an unreadable read keeps the act's answer.) The `pending` why now says the holder *still* holds the proposal, which `_alive` has just read. `INGEST.md` rule 4-10, rule 4-13, §4.3's first principle, §8's order paragraph and ING16 say so. **Left in ING16:** a remembered host row whose host row is deleted during the act is still reused before the gate (no suite shape deletes a host row).

**Red first.** `cbd993c` adds `C20-70` d1 *an own proposal that ended is not reused* (compensated and written), *a pending label whose holder ended is landed again* (both), *a candidate remembered before a retire goes to the gate* (exact and banded), and `C20-47` d1 *a number that is also a mapping*. On sqlite and postgres each fails for its stated reason: `reused` where the fresh act's answer is `proposed`, `reused` where it is `existing`, and `False` for the NaN float-mapping. The banded retire case is green on arrival: there the act and a fresh act already mint nothing. The commit after it is the fix. **[Observed]**

**A miss of the same kind as §1.1's.** The first draft of `cbd993c`'s tests chained `_act(...).land(...)`, and `tools/unasync.py` raised its `SyntaxError`. This time the error was read before anything was committed, and the chain was split.

**The sweep.** Four new required mutations (the liveness check, the similar step's liveness, the gate-first order, the number-before-container order), all killed; three row-7d targets moved with the fix and were retargeted, and at `1859baf` a fourth, row 7c's *4-11 an unfinished A4 read proposes nothing*, because `_alive` holds a second `if not held.complete:` (still killed). *4-13 a refused landing writes no memory* (`c20_81`) now survives, because a refused candidate's entry names no live row and so is never reused: it is equivalent under the fix, and it is now non-required with that reason in the sweep file.

**Cost [Inferred until the probe runs on the final code].** Each recall of a candidate now costs a gate read and an A4 read, which Q92's slice does many times. §2's final runs record the probe's time and split.

**A regression the fix introduced, caught by the full suite on `70ea408`.** The suite ran 3,449 passed, 1,022 skipped and **1 failed**: `test_manifest`'s capability matrix, red under `stores_events=False` and `stores_invocation_events=False`. **[Observed]** the failing test is `C20-70`'s own *resolved once* test: on a backend that keeps no invocation events, A4 can never say whether the act's row was written, so `_alive` dropped every memory and the repeat landed `unknowable` where rule 4-10 requires `reused`. **Ruled:** a liveness read that cannot finish leaves the act's own answer standing, and the landing's `why` says the check could not be made; a memory is dropped only when a finished read shows its row ended. Rule 4-10's text says so. The C20 runs under both declined flags and `stores_invocations=False` go green (189, 190 and 162 passed, 0 failed) **[Observed]**. Its mutation (*an unreadable liveness check keeps the act's own answer*) is non-required, because only the matrix's degraded leg kills it and the sweep runs sqlite alone; the matrix gate is what holds it. The fix is the commit after `70ea408`.

**Probe on `70ea408`** (`ingest_write_probe.py --assert`): **18 of 18 checks; Q92 3,346 rows, 1,031 `proposed`, 2,310 `reused`, 5 `pending`, 69.0%**, identical to `a0e085b`. The run took 1,404 s. No earlier run of the probe was timed, so the cost of the two extra reads per recall is not measured against a baseline. **[Observed]** for the split and the time; the comparison is not made.

### §2.3 — Round 3, on `1859baf`

Three fresh lenses, read-only, on exported copies. The capability matrix ran on `1859baf` first: **every configuration conformant, exit 0** (`stores_events=False` 607 passed, 162 skipped, 0 failed; `stores_invocation_events=False` 726/43/0) **[Observed]**, and lens 3 reran it to the same result.

| # | lens | severity | finding | ruling |
|---|---|---|---|---|
| 1 | door (#1) | MAJOR (code) | **A retire can grow the closure without changing its effective entry, and a remembered host row is then still reused before the gate.** The act lands a label `existing` on an `ltc_facility` row, `facility` (whose table holds an exact twin) is retired toward `ltc_facility`, and the repeat lands `reused` where a fresh act gets `ambiguous` and a review-mode proposal. `_recall` sent a host row back to the gate only when the effective name changed. Present at `a6e9d7f` **[Observed by the lens]**, on sqlite and postgres, 62 hits in 3,000 fuzzed runs, every one after a retire. It is the host-row twin of §2.2 #2 | **fixed red first** (below) |
| 2 | build (#1), fidelity (#2) | MAJOR (spec claim) | Rule 4-10 says a reuse whose liveness read cannot finish says so in its `why`. The similar step's `why` did not | **fixed red first** (below) |
| 3 | fidelity (#1), build (#3) | MAJOR (record) | ING16's row, §4.3's first principle and §8 said each shape lands as a fresh act's does, but on a backend that keeps no invocation events the act's repeat of an undone `EAST` lands `reused` where a fresh act lands `unknowable` (§2.2's ruling). Only rule 4-10 stated it | **fixed:** ING16 now lists it as left, case (1); principle 1 and §8 say *or while that cannot be read* |
| 4 | door (#2) | MINOR | The host adds an exact twin to a remembered host row's own table during the act, no retire: the act reuses, a fresh act lands `ambiguous` | **left, recorded** as ING16 case (2) with the deleted host row. No suite shape changes a host table mid-act |
| 5 | build (#2), fidelity (#3, #4, #5, #7) | MINOR (record) | §2.2's *unreadable keeps nothing*, the fourth retarget, §1.3 and §1.6's stale cross-references, §2.1's ruling not fully marked withdrawn, missing tags | **fixed** in this section's commit |
| 6 | build (#4) | MINOR | An unfinished A4 read keeps the answer even when the read already showed the act's own row dead and the gap came from another row | **left**: it mints nothing, and telling "own row seen dead" from "unreadable" needs A4 to report per-row completeness, which it does not. **[Inferred]**, not reproduced |
| 7 | build (#5), fidelity (#6) | MINOR | The sweep's note that *4-13 a refused landing writes no memory* is equivalent holds only where A4 finishes | **fixed:** the note now says so |
| 8 | build (#6) | MINOR | `_alive` treats an A4 refusal as unreadable | **left**: no route to it, since a backend that refuses A4 never records the first proposal **[Inferred]** |

Lens 2 fuzzed 1,500 seeds in each of auto and review mode (three acts, two types, compensations, results, retires, 9,185 `ambiguous` landings). It found **zero** cases where the act proposes and a fresh act pends, zero where it reuses or pends a candidate and a fresh act proposes (#1 is a host-row reuse, which that comparison did not cover), and zero folds onto a candidate whose row A4 does not name. On the declined-capability backends, the only change from `a6e9d7f` was round 2's intended retire fix **[Observed by the lens]**. Lens 3 confirmed §0 byte-identical, round 2's red-first claims, the matrix regression and its fix, and the probe on `1859baf`: 18 of 18 checks, the same split, 1,396 s **[Observed by the lens]**.

**The fixes (round 3).**
1. **The members.** `IngestAct` remembers the closure's members with each entry. A remembered host row goes back to the gate when the members differ, not only the effective name.
2. **The similar step's `why`.** `_similar_candidate` returns the unread reason with its candidate, and the similar step's `why` carries it.

Rule 4-10, ING16, §4.3 principle 1 and §8 say so.

**Red first.** `23c4858` adds `C20-70` d1 *a host row remembered before the closure grew goes to the gate* and *a similar reuse says when its row could not be read*. On sqlite and postgres, sync and aio, they fail for their stated reasons: `reused`, and a `why` with no *could not be read* **[Observed]**. The commit after it is the fix. C20 sync and aio on all three legs: 960 passed, 352 skipped, 0 failed. Under `stores_events`, `stores_invocation_events`, `stores_invocations` and `indexes_membership` declined: 190, 191, 162 and 173 passed, 0 failed **[Observed]**.

**The sweep.** Two new required mutations: the members check and the similar unread note. Both are killed. Two targets moved with the fix and were retargeted, both still killed: round 2's *the similar step reuses only a live proposal* and row 7c's *two distinct remembered answers are an ambiguity the gate decides*. `--list`: 209 mutations, 0 whose old text does not occur once **[Observed]**.

**Cost.** `_remember` now reads the closure once per entry, and `land` already read it, so the cost is one extra closure read per landing that remembers. **[Inferred]** It is small next to the gate's read. The final probe's time is in §2.4.

### §2.4 — Round 4, the confirming round, on `e9900c5`; the row lands not clean

Three fresh lenses, read-only, on exported copies of `e9900c5` (the code, tests and text after round 3, with the README row). **The build and fidelity lenses found no MAJOR. The door lens found one. Under §0.9's cap, row 7d lands not clean.**

| # | lens | severity | finding | ruling |
|---|---|---|---|---|
| 1 | door (#1) | **MAJOR (code)** | **A host row the act remembered is still reused after the effective entry's own governed facts are amended mid-act.** The act lands `Burns Nursing Homes Inc` `existing` on `facility#015009` at 0.9778. `import_types` then re-imports `facility` with `match_at` 0.99, and the act's repeat lands `reused` where a fresh act gets `ambiguous` and records a review-mode proposal. A predicate added after `Mesa Vista Care` landed does the same. Round 3's check compared the closure's members, and an amendment changes none. Present at `a6e9d7f` **[Observed by the lens]**, on sqlite and postgres. The shape is plausible: `C20-28` r3 amends an entry through `import_types` between landings | **fixed red first, after the last round** (below). The lens asked whether the link to DECISIONS-OPEN 19 (Q103, the `import_types` amendment door) puts it out of scope. **Ruled in scope:** the defect is in the act's recall and any amendment door reaches it, and the fix answers nothing item 19 asks |
| 2 | door (#2) | MINOR (record) | ING16 case (2) said "an exact twin in its own table", and the fuzzer hit a host row added NEAR the label in ANOTHER member's table | **fixed:** case (2) now reads "whose closure's host tables gain a row near the label" |
| 3 | fidelity (#1) | MINOR (record) | §2.3's "zero where it reuses or pends and a fresh act proposes" contradicted §2.3 #1 (a host-row reuse where a fresh act proposes) | **fixed:** the sentence now says the fuzz compared candidates |
| 4 | fidelity (#2) | MINOR (spec) | §8's similar-step clause lacked round 3's *or while A4 cannot be read* | **fixed** |
| 5 | fidelity (#3) | MINOR (spec) | §4.3 principle 1 called a remembered candidate *the one* exception, and a remembered host row is another | **fixed** |
| 6 | fidelity (#4), build (#4) | MINOR (record) | §1.3, §1.6, §2.3 and the README row pointed at a §2.4 that did not exist yet, and the README stated a split not measured on the final code | **fixed** by this section and its final runs |
| 7 | build (#1) | MINOR (cost) | `_remember` reads the closure again, though `_recall` already read the same member set in this landing (4 of 33 adapter calls on a proposing landing) **[Observed by the lens]** | **left:** a cost, not a defect. Passing the closure through is a refactor no rule asks for |
| 8 | build (#2) | MINOR | `_remember` now reads after `record_invocation`, so an adapter exception there leaves a recorded row with no memory entry | **left:** the exception still reaches the caller, and the row is the ledger's, which A4 reads. **[Inferred]**, not reproduced |
| 9 | build (#3) | MINOR (spec wording) | Rule 4-10's "goes back to the gate *once*" holds only when the gate's answer is remembered again. After `unknowable`, `not_an_instance` or a similar reuse, every repeat goes to the gate | **left:** it costs reads and mints nothing **[Inferred]** |

The door lens's new fuzzer (three types, repeated retires with and without successors, `reinstate`, `merge_types`, alias adds, compensations and results) ran 6,000 scenarios with host inserts off and 5,000 with sparse host tables. It found **zero** mint differences in either direction **[Observed by the lens]**. On the declined-capability backends the only divergence was ING16 case (1). The fidelity lens confirmed §0 byte-identical, round 3's red-first claims (8 failed at `23c4858`, 8 passed at `93fd865`), §2.3's counts, the sweep diff and all five gates at `e9900c5` **[Observed by the lens]**.

**The fix, after the last round, seen by no lens.** `_members` now remembers, with each entry, the closure's members AND the effective entry's governed facts (its `MatchPolicy` and predicate, deep-copied). A remembered host row goes back to the gate when either differs. Rule 4-10, §4.3 principle 1 and ING16 say so.

**Red first.** `872d17b` adds `C20-70` d1 *a host row remembered before its entry was amended goes to the gate* (`match_at` and `predicate`). On sqlite and postgres, sync and aio, all 8 fail with `reused`, after the test has checked that a fresh resolution is no longer `existing` **[Observed]**. The commit after it is the fix. C20 sync and aio on all three legs: 968 passed, 356 skipped, 0 failed. Under `stores_events`, `stores_invocation_events`, `stores_invocations` and `indexes_membership` declined: 192, 193, 162 and 175 passed, 0 failed **[Observed]**.

**The sweep.** One new required mutation (the governed-facts check) and one retarget (round 3's members check, now the tuple's first half). Both are killed. `--list`: 210 mutations, 0 whose old text does not occur once **[Observed]**.

**What "not clean" means here.** §0.9's stopping rule is not met: round 4, the last round under the cap, found an in-scope reachable MAJOR. The fix is test-first and mutation-held, but no adversarial round has seen it. A fifth round would be over the pre-registered cap, so the row does not run one. `STATUS.md` is the supervisor's, so the finding goes to the supervisor in the row's closing report rather than into that file.
