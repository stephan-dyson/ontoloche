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
| ING15 | `9b418dc` | `C20-70` d1, `reused` where the act must propose, on sqlite and postgres (minimal skips: no invocation events) | `2de6ffb` |
| ING15 minor 2, the why | `9bd1083` | `C20-70` d1 why test: the why said "already answered" and named no holder | `a0e085b` |
| ING15 minor 3, the filter | `9bd1083` | green on arrival, as §0.5 predicted. Its mutation is killed (§1.5) | — |
| 7b B1 to B3 | `21afb8a` | `C20-05` d1 raised `NotSupported` for a dropped table named `host_decode_site_1`; `C20-47` d1 raised `OverflowError` and `RecursionError` | `812c080` |
| 7c minors | `4c5842f` | seven coverage pins, all green on arrival, because the code they pin is correct. Each has a required mutation of its own (§1.5) | — |

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

**The Q92 cost, stated.** The fix proposes two more identities in 3,346 rows, and folds none fewer. **[Inferred]** a net zero on `reused` with two from `pending` to `proposed` is what two pairs of this shape give: a label once reused onto a pending candidate now goes to A4 and is proposed (reused −1, proposed +1), and because it is now this act's own proposal, a later label near it that A4 used to hold `pending` is now reused onto it (pending −1, reused +1). That was not traced label by label. The probe ran on `a0e085b`; the act's code has not changed since, and §2 records the run on the final code.

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

`docs/tools/ingest_mutation_sweep.py` on `f96a366`: **200 mutations, 199 killed, 1 survivor, 0 not applied or broken, 0 required survivors, exit 0** (`sweep_f96a366.log`). The survivor is 7c's non-required `<n>` rounding case (C12). Row 7d added 19 required mutations: three for ING15 and its minors, four for B1 to B3, and twelve for the 7c minors. Seven existing targets moved with the fix and were retargeted. `--only` and `--list` are new; `--list` is the preflight that counts each target once.

### §1.6 — Suite and gates

- **Full suite, three legs** (sqlite, minimal, postgres on `oo-pg` at port 55432) on `f96a366`: **3,414 passed, 1,010 skipped, 0 failed**, in 20m34s (`suite_f96a366.log`).
- **Gates:** `check_links`, `check_spec_drift` and `check_merge_guard` exit 0. `check_skip_census` failed once (§1.1) and exits 0 at `66555ff`. `check_capability_matrix` is recorded in §2 with the final runs.

### §1.7 — Kill row (§0.4)

- **D1 closed** by the fix, pinned by `C20-70` d1 and two required mutations.
- **Predicted zero new type-identity trips. Hit:** `check_merge_guard.py` Part A finds no new identity writer. The fix touches no type row.
- D2 to D7 are scored by the rounds (§2).

---

## §2 — Adversarial rounds (§0.9)

*Written as the rounds run.*
