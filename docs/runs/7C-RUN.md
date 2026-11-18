# 7C-RUN — roadmap row 7c: the ingestion build, write side

**Status:** in flight. **Opened** by the supervising session on 2026-11-18 under the founder's instructions *"keep the project moving forward"* (2026-11-12) and *"you don't need my permission to move to the next item on the roadmap"* (2026-11-18). **Brief:** [`handoffs/2026-11-18-row-7c-ingest-write-side-build-brief.md`](https://github.com/stephan-dyson/ontoloche/blob/main/docs/handoffs/2026-11-18-row-7c-ingest-write-side-build-brief.md). **Builds:** [`INGEST.md`](https://github.com/stephan-dyson/ontoloche/blob/main/docs/specs/INGEST.md) v0 §4 (rules 4-1 to 4-13) and §4.4's amendments A1 to A5, landed in [`ACTIONS.md`](https://github.com/stephan-dyson/ontoloche/blob/main/docs/specs/ACTIONS.md) and `ontoloche/actions.py` together. **Read side:** [`7B-RUN.md`](https://github.com/stephan-dyson/ontoloche/blob/main/docs/runs/7B-RUN.md), merged at `eb91255`. **Branch:** `agent/row-7c`, cut from `main` at `5321b05`, local only.

**Claim tags:** **[Observed]** seen directly in this repo, in a command's output, or on a page opened this row · **[Inferred]** a reasonable read · **[Assumed]** believed, untested · **[guess]** an inference not checked.

---

## §0 — PRE-REGISTRATION, committed before any code and any test

This section is the row's first commit. Every prediction below is made from the brief, `INGEST.md` v0, `ACTIONS.md`, `7A-RUN.md`, `7B-RUN.md`, the throwaway kit [`docs/tools/ingest_probe_kit.py`](https://github.com/stephan-dyson/ontoloche/blob/main/docs/tools/ingest_probe_kit.py) and the shipped code at `5321b05`. A wrong prediction stays here and is scored as a miss in §1.

### §0.1 — What was observed before this section was written

1. **Nothing of §4 exists in the package.** **[Observed]** `CandidateRef` exists in `ontoloche/ingest.py` as a carrier only (7B-RUN §0.2 item 2). `REF_SHAPES == ("type", "instance", "edge")`. `Invocation` has no `results` field. `record_invocation` takes neither `approval_mode` nor `warnings`. `invocations` takes `(family, namespace, actor, outcome, gate_verdict, effect_undeclared, unreviewed, since, limit)` and nothing that names a label, a type or a closure. `declared_policy` holds `approval_mode`, `min_auto_tier`, `reversibility`, `preconditions` and `tier_order`, and no threshold.
2. **The vocabularies.** **[Observed]** `len(types.WARNING_VALUES) == 49`, `len(types.REFUSAL_REASONS) == 34`. `INGEST.md` §9 reserves `instance_ambiguous_at_proposal` and `instance_proposal_pending` as warnings 50 and 51.
3. **The ids.** **[Observed]** `test_manifest.py` counts 556 ids and lists §4's thirteen as planned. `check_spec_drift.py` holds §4 as `PLANNED_R31_INGEST_SECTIONS`. The `C19` group ends at `C19-108`.
4. **Which backends can hold what A2 needs.** **[Observed]** `SQLiteAdapter` and `PostgresAdapter` declare `stores_invocations=True` and `stores_invocation_events=True`. `MinimalSQLiteAdapter` declares both `False`. No shipped backend stores invocations without their events.
5. **The store never rewrites an invocation row** (`INTERFACE.md` §5.8, `ACTIONS.md` §3.5). `reviewed_at`, `reviewed_by` and `compensated_by` are all derived at read time, from an event or from a later row's forward pointer.
6. **`find_invocations` has a keyset cursor** (`after=`) that `invocations` deliberately does not expose (`ACTIONS.md` §6.3, rule 6-8, Q43).

### §0.2 — The build, stated so the predictions have a design to be wrong about

Each choice below is this row's, and each says why. None decides what the registry refuses or holds beyond what `INGEST.md` and `ACTIONS.md` already rule, except where §0.8 says so.

1. **A1, `ref="candidate"`.** `REF_SHAPES` gains a fourth value, `"candidate"`, and `CandidateRef` joins `InputRef`. `ref_shape`, `ref_kind`, `ref_key`, `parse_ref` and `flat_form_problem` each learn it. Both invocation doors validate a `CandidateRef` against its `InputSpec` the way they validate the other three shapes, refusing `input_kind_mismatch`: wrong shape either way, a type whose `kind` is not `entity`, a `resolution` outside `("proposal", "ambiguous")`, an empty `label` or `act_id`. *Reason:* F1's four refusals are the evidence, and `input_kind_mismatch` is already the value for every other shape breach.
2. **The candidate's flat form is canonical JSON**, `{"candidate": {"act_id": ..., "label": ..., "resolution": ..., "type": "<ns>:<kind>:<name>"}}` with sorted keys. `parse_ref` reads a string beginning `{"candidate":` as a `CandidateRef` and raises on anything malformed. *Reason:* a label may carry `:` and `#`, so the `#`-split grammar cannot hold it, and every string the old grammar accepts as valid has a head of exactly three colon-separated segments, which no JSON object carrying four keys has. `flat_form_problem` additionally asks the round trip (`parse_ref(ref_key(ref)) == ref`) for a candidate, which is its existing *ask, do not classify* method (`C19-94`) applied to the fourth shape.
3. **A2, `Invocation.results: dict[str, InputRef]`**, keyed by the input name, default empty. It is **derived at read time** from `invocation_recorded` events carrying `detail["results"]`, which is §3.5's own sentence (*"a correction is an `invocation_recorded` event carrying the correction"*) and the path evidence already rides. The writer is a sixth call, **`record_result(invocation_id, results, *, actor, namespace="default")`**. It refuses `unknown_invocation`, `action_store_absent`, and `cannot_record_override` on a backend that cannot keep the event, exactly as `review_invocation` does. A `CandidateRef` as a result is refused `input_kind_mismatch`, because a result names a thing that exists. A second result for the same name is recorded and the latest wins, because the ledger is append-only and refusing it would destroy evidence (§6.2's argument). *Reason:* the store never rewrites a row, a host writes the instance row **after** the proposal is recorded (rule 4-2 and `I-5`), so the slot has to be filled by a later act, and R73 already argued that a later act is a call, not a parameter.
4. **A3, `record_invocation(approval_mode=None, warnings=())`.** `approval_mode` **raises** the mode of record and never lowers it (strictness `auto` < `review` < `human`). When it raises, `declared_policy["approval_mode"]` is the raised mode and `declared_policy["approval_mode_declared"]` keeps the family's. A looser request is ignored, not refused. `warnings` takes only the values a host can carry from a resolution onto its invocation: the two §4 warnings and the four read-side ones (`instance_narrowed_proposal`, `instance_type_succeeded`, `consumers_unregistered`, `no_tenancy_predicate`). Any other value is a `ValueError`, the way an unknown `outcome` is. *Reason:* rule 4-5 needs one invocation in `review` without moving every later row, and a caller that could pass `effect_undeclared:` or `declaration_amended:` could forge the registry's own detectors.
5. **A4, `invocations(..., unwritten_for: CandidateRef | None = None)`.** With it set, the call is a **scoped, completable read**: it pages the store with the primitive's own cursor until the ledger is exhausted, keeps the rows whose candidate input answers rule 4-10's key (same namespace and kind, the same effective entry under the closure, and `similar(norm(a), norm(b)) >= match_at` of that entry), drops rows that hold nothing (a `results` entry for that input, `outcome != "applied"`, compensated, or carrying `instance_proposal_pending`), and reports `complete=True` only when every page was read and every kept row's events were readable. It refuses to combine with any other filter (`ValueError`), because a combined answer is a floor again. *Reason:* §4.4's A4 row names exactly three asks (unwritten, the closure key under the gate's relation, and not a client-side scan of the oldest 100), and rule 6-8's *"does not page"* stays true of the public, unscoped read.
6. **A5, `record_invocation(match_policy=None, governed_by=None)`**, both or neither (`ValueError` otherwise). They land as `declared_policy["match_policy"] = {"governed_by", "match_at", "propose_below", "ambiguity_margin"}`. *Reason:* rule 5-7's carrier, copied as the gate judged it for rule 3-8's reason, so a later amendment of the entry cannot re-describe an old proposal.
7. **The act is an in-memory object with no store**: `Registry.ingest_act(act_id, *, family, actor, tier, namespace="default", input_name="instance")` returns an `IngestAct`, and `IngestAct.land(label, *, type_name, context=None, confidence=None, source_version=None)` returns an `IngestLanding` (`outcome`, `resolution`, `ref`, `candidate`, `invocation`, `why`) or a `Refusal`. Landing outcomes: `existing`, `proposed`, `pending`, `reused`, `unknowable`, `not_an_instance`, `refused`. It lives in `registry.py` so `tools/unasync.py` mirrors it. *Reason:* rule 4-1 forbids a store and a primitive, not a helper, and rules 4-10 and 4-13 are untestable unless something the package ships holds the per-act memory. The kit's `IngestAct` is the reference order.
8. **`land` in order**, the kit's: rule 4-10's recall over the per-act memory under the gate's relation; `resolve_instance`; `existing` is remembered and returned; `unknowable` and `not_an_instance` propose nothing (rule 4-7); `proposal` and `ambiguous` build the `CandidateRef` under the **effective** type the resolution reports (rule 4-3); `preflight` with that candidate; A4's read; then `record_invocation` with `judged=`, `match_policy=`, `governed_by=`, the resolution's warnings, and on `ambiguous` `approval_mode="review"` plus `instance_ambiguous_at_proposal:<input_name>:<n>`; or, when A4 finds a holder, `instance_proposal_pending:<invocation_id>` and landing outcome `pending`. The memory is written on every branch that answers with a ref or a candidate (rule 4-13).
9. **`ingest_act` refuses a family that cannot carry §4**, with `attributes_schema_violation`: no `InputSpec(ref="candidate")` under `input_name`, no `Effect(op="host_state")` (rule 4-2), or a `propose_type` effect on `kind="predicate"` written past validation (rule 4-8). *Reason:* these are rules 4-2 and 4-8 enforced at the one door the act has. The registry already refuses the last at declaration (`ACTIONS.md` §2.5).
10. **When A4's read cannot finish, `land` proposes nothing** and answers `unknowable` with the read's `why`. *Reason:* Rule U, and §4.4's own sentence that an always-incomplete read *"would have made every propose-at-ingest `unknowable` and recorded nothing"* says that is the model. §0.8 says why this is not routed.
11. **When `preflight` refuses, `land` records nothing** and answers `refused` with the gate's refusal. *Reason:* `preflight` records nothing (rule 6-1) and the host did not act.
12. **Vocabulary.** The two §4 warnings are minted as 50 and 51 in the commit whose code first emits them, and §9's table moves them to *minted*. No refusal reason is minted.
13. **Contract ids.** §4's thirteen `C20` ids, plus six new `C19` ids for the amendments, as new numbered rules in `ACTIONS.md`'s existing tables:

| new `ACTIONS.md` rule | amendment | id |
|---|---|---|
| 3-9 | `Invocation.results` carries what the host reports it minted, keyed by input name, derived from `invocation_recorded` events, never from an effect's `why` and never from `inputs` | `C19-109` |
| 3-10 | `declared_policy["match_policy"]` records which entry's thresholds governed, when supplied, as the gate judged them | `C19-110` |
| 6-14 | `ref="candidate"` is validated at both doors, a candidate where another shape is declared (and the reverse) is `input_kind_mismatch`, and its flat form round-trips through `parse_ref` | `C19-111` |
| 6-15 | `record_invocation(approval_mode=)` raises the mode of record and never lowers it; `warnings=` takes only the caller-reportable values | `C19-112` |
| 6-16 | `invocations(unwritten_for=)` is a scoped read that pages to the end, is `complete=True` when it finished, and holds nothing for a written, refused, compensated or pending row | `C19-113` |
| 6-17 | `record_result` is the slot's only writer and refuses `unknown_invocation`, `action_store_absent`, `cannot_record_override`, and a `CandidateRef` as a result | `C19-114` |

That makes **562 ids**, 90 of them `C20`, and `check_spec_drift.py` moves §4 to `R31_INGEST_SECTIONS`.

### §0.3 — Order, and what "red first" means here

1. For each of A1 to A5, in that order: one commit holding the failing `C19` test and the failing `C20` test (or the `C20` half named in §0.6), with the red run recorded in §1; then one commit holding the code and the doc amendment that turn them green, with the existing `C19` tests green.
2. Then §4's rules in three batches, each red then green: **batch 1** the act's skeleton (4-1, 4-2, 4-4, 4-7, 4-8, 4-9); **batch 2** the review path (4-3, 4-5, 4-6, 4-12); **batch 3** the identity rules (4-10, 4-11, 4-13).
3. **Predicted exceptions to red-first**, named before they happen: `C20-27` (rule 4-1, *no store and no primitive*) and `C20-34` (rule 4-8, the allowlist) are **predicted to pass on the first run**, because both state something the shipped code already guarantees: the protocol has no invocation-store method the act could add, and `ACTIONS.md` §2.5 already refuses `propose_type` on `predicate` at declaration. Each will be committed anyway and shown red by mutation instead. `C20-30` (rule 4-4, *no provenance field is added*) is the same shape and the same prediction.

### §0.4 — Predictions for each design test (brief §3)

All four run through the shipped `Registry` on SQLite, in a committed probe, `docs/tools/ingest_write_probe.py`.

#### UC2 CMS

Over the 2026-10-01 CMS file (7B-RUN §0.1 item 5), `facility` declared with the kit's `match_policy`, one ingest act landing these labels:

| label | predicted landing |
|---|---|
| `BURNS NURSING HOME, INC.` | `existing`, `cms:entity:facility#015009`, no invocation |
| `MILLER'S MERRY MANOR` | `proposed`, invocation in `review` mode carrying `instance_ambiguous_at_proposal:instance:12` |
| `THE SARAH ROBERTS FRENCH HOME` with `745040` held out | `proposed`, invocation in the family's mode (`auto`), no ambiguity warning |
| `Provider Name` | `not_an_instance`, no invocation |
| `Tuskegee Airmen Texas State Veterans Home` under a scan cap one row short | `unknowable`, no invocation |

**Predicted:** five of five as tabled, and `invocations(unreviewed=True)` returns exactly the one `MILLER'S MERRY MANOR` invocation.

#### UC3 NYC

1. **The Q92 measurement.** One act over the live `erm2-nwe9` slice 7a used (`agency=NYPD`, `complaint_type='Illegal Fireworks'`, `incident_zip=10032`, labels from `incident_address`), against a host table holding one other ZIP's rows so that `scanned > 0`. **Predicted:** the landings split into `proposed` and `reused` with `reused` at least 60% of rows, against 7a's `{'proposed': 1044, 'reused': 2298}` over 3,342 rows. The live slice has moved since 7a [guess], so the prediction is the share, not the counts. Every `reused` landing is a service request rule 4-10 never resolved, which is what Q92 says.
2. **Rule 4-11 across acts.** Act 1 proposes an address. Act 2 lands it: `pending`, carrying `instance_proposal_pending:<act 1's id>`. Act 1's proposal is reviewed: act 3 still answers `pending`. The host writes and `record_result` records the ref: act 4 answers `existing`. **Predicted:** exactly that sequence.

#### Allowlist

A family declaring `Effect(op="propose_type", kind="predicate")` is refused at `propose_type`, `approve` and `import_types` (the shipped §2.5 allowlist), and the same row written past validation is refused by `ingest_act` (§0.2 item 9). **Predicted:** four refusals, nothing recorded.

#### Kill row

See §0.7.

### §0.5 — Findings 3, 6 and 7 (brief §1 items 3 to 5), predicted

- **Finding 3 (Q92):** measured as in §0.4 UC3 item 1, recorded, not fixed.
- **Finding 6 (ING11's dual-write curve).** 7a's claim is that at 100% dual-written the `ambiguous` rate is 100%. **Predicted: refuted against the built code for a host that dual-writes under the same instance id**, because row 7b built rule 2-17 (`C20-89`), which collapses one id under two member names of one closure to one candidate. So a same-id dual write is predicted to change **0** outcomes at 0%, 50% and 100% dual-written. **Predicted: confirmed for a host that dual-writes under a new id**, where each dual-written row is two refs and the act's landing becomes a `review`-mode proposal for 100% of dual-written labels that were `existing` before, draining only when the predecessor rows are deleted. Both arms run over 400 CMS labels.
- **Finding 7, route 9's concurrent clause.** Two acts that both run A4's read before either records see no holder and both record. **Predicted: the concurrent case is OPEN against the built code**: two `proposed` landings for one identity, no warning on either. Rule 4-11 is a check, then an act, with no lock, and `ACTIONS.md` §6.2 rules a lock out (*"a locking protocol would put this registry in the execution path, which is 1's first non-goal"*). So route 9 loses *"or by two concurrent workers"*, §10 gains the contortion, and the sequential case stays closed by rule 4-11. **The eight `I-` cells** are re-derived into §13 as the row lands, predicted to add no new route row for `I-1` to `I-3` and `I-6` to `I-8` (all closed on the read side by row 7b), and to restate `I-4` and `I-5` as closed by `C20-70` and `C20-71`.

### §0.6 — Contract ids, named before they are written

| rule | id | the red-first test | predicted first run |
|---|---|---|---|
| 4-1 | `C20-27` | the act adds no protocol method and no table; a landing writes only invocation rows and events | **green** (§0.3 item 3) |
| 4-2 | `C20-28` | `ingest_act` refuses a family without `host_state`; no landing writes a host row | red |
| 4-3 | `C20-29` | after `retire(facility, successor=ltc_facility)`, the candidate's type is `ltc_facility`, and `record_result` puts the minted ref in `results`, not in an effect or an input | red |
| 4-4 | `C20-30` | `InvocationProvenance`'s fields are unchanged and the landing's invocation carries actor, tier, confidence and `source_version` | **green** (§0.3 item 3) |
| 4-5 | `C20-31` | an `ambiguous` landing in an `auto` family is recorded in `review` with `instance_ambiguous_at_proposal:instance:<n>` | red |
| 4-6 | `C20-32` | that invocation is in `invocations(unreviewed=True)` and leaves only through `review_invocation` | red |
| 4-7 | `C20-33` | `unknowable` and `not_an_instance` record nothing | red |
| 4-8 | `C20-34` | the allowlist refuses at three doors and at `ingest_act` | **green at the three doors, red at `ingest_act`** |
| 4-9 | `C20-69` | the candidate has no `id` attribute and the recorded input reads back as a `CandidateRef` | red |
| 4-10 | `C20-70` | two spellings the gate calls one identity (`EXACT` and its typo) in one act give one proposal; the same label under two types gives two | red |
| 4-11 | `C20-71` | the four-act sequence of §0.4 UC3 item 2, on the CMS fixture | red |
| 4-12 | `C20-72` | `<n>` equals `known` over a finished read, and a capped read reaches `unknowable` and records nothing | red |
| 4-13 | `C20-81` | after a `pending` landing, a third land of the same identity in that act is `reused`, not a second `pending` | red |

`C20-41` (rule 5-7) was built by row 7b on its resolution half. Its invocation half is A5, and `C19-110` plus `C20-41`'s new assertion pin it.

### §0.7 — The kill-row doors propose-at-ingest and the five amendments open

Kill row at the start of this row: **twenty-three** trips (`STATUS.md`). Row 7b closed the read side of `I-1`, `I-2`, `I-3` (read half), `I-6`, `I-7` and `I-8`, and left `I-4` and `I-5` unopened because the act was not built (7B-RUN §0.7). 7a's records for both are its round 2 `B3`/`Z2`/`D1` (`I-4`, mis-keyed) and `Z4` (`I-5`, mis-timed), with the kit's mutations `4-10-key` and `4-11-written`.

**Where each shape is predicted to recur in this row's build, before any lens runs:**

| cell | the shape | where this row predicts it recurs | predicted state at landing |
|---|---|---|---|
| `I-1` truncated | decide over a partial set | **A4's read**: a scan of the oldest page (B2) that answers *no holder*. Closed by paging to exhaustion and `complete=False` otherwise | closed, `C19-113`, `C20-71` |
| `I-2` mis-walked | the chain reported complete when it was not | **A4's closure**, if it walks its own chain instead of `_instance_closure` | closed by reuse, `C19-113` |
| `I-3` mis-written | the read bound by the chain, the write not | **the candidate's type**: a host told the declared type writes under a retired name. Closed by rule 4-3 | closed, `C20-29` |
| `I-4` mis-keyed | the act keys differently from the gate | **two places**: the per-act recall and A4's scan. If either keys on the raw label or omits the type, or if they use two functions, the shape is open | closed, `C20-70`, `C19-113` |
| `I-5` mis-timed | the guard's window closes early | **A4's predicate**: *unreviewed* instead of *unwritten*, and a second form this row predicts: a `pending` invocation counted as a holder forever, or a `results` read that fails open on a backend whose events cannot be read | closed, `C20-71`, `C19-113` |
| `I-6` mis-counted | duplicates collapse or inflate | **`<n>` in the ambiguity warning** if counted from anything but the finished resolution's `known` | closed, `C20-72` |
| `I-7` mis-governed | another entry's facts judge the set | **A5**: thresholds copied from the declared entry while the resolution was governed by the effective one | closed, `C19-110`, `C20-41` |
| `I-8` mis-directed | the closure walked one way | **A4's closure**, as `I-2` | closed by reuse |

**The new doors, listed before any code:**

| # | door | predicted state |
|---|---|---|
| K1 | `IngestAct.land` | **a door to the instance surface, not to the type store**: it records invocations and writes no type row |
| K2 | `record_result` | **appends an event**, writes no type row |
| K3 | `record_invocation(approval_mode=, warnings=, match_policy=, governed_by=)` | **narrows**: it can only raise a mode and add a warning from a closed set |
| K4 | `invocations(unwritten_for=)` | a read |
| K5 | `ref="candidate"` at `preflight` and `record_invocation` | **narrows**: a new shape with its own refusals |
| K6 | concurrency at K1 | **open, and recorded** (§0.5 finding 7). It is the instance surface's kill row (*two things answering to one identity*), reached by two hosts, and it needs no defect in any door |

**Predicted: zero new trips on the type-identity kill row.** `check_merge_guard.py` Part A discovers no new identity writer. **K6 is predicted to be constructed open**, and it is recorded against route 9 and §10 rather than counted as a trip, because the register counts type-identity trips and 7a's §6.9b kept the instance cells off the count.

### §0.8 — What goes to the founder

**Predicted: nothing that blocks.**

- **Q87 (item 28):** built as `warn`. `consumers_unregistered` rides from the resolution onto the propose invocation. Pinned by `C20-31`'s fixture, which has no registered consumer.
- **Q89 (item 29):** built as `allow`. A review by the actor who landed the row succeeds. Pinned in `C20-32`.
- **Q91 (item 30):** unchanged.
- **Item 31:** if a landing proposes under a retired type with no successor, the code's behaviour is pinned and recorded against item 31, not chosen.
- **§0.2 items 9 and 10 are the two places this row comes closest to a refusal ruling.** Item 9 enforces rules 4-2 and 4-8 as written. Item 10 holds (proposes nothing) when A4 cannot finish, which is Rule U and §4.4's own model. Neither is routed, because each has a default the spec states.
- **The concurrent case (K6)** asks whether the registry should refuse a second concurrent proposal, which would need a lock or a uniqueness constraint. The default in force is `ACTIONS.md` §6.2's *no lock*, so it is recorded as a contortion and an `INGEST.md` §11 question, not a blocking item.

### §0.9 — The stopping rule and the round cap

Row 6j's adopted criterion (`6J-RUN.md` §5 item 10): the loop ends when a full round finds no in-scope code MAJOR reachable by a shape a contributor would plausibly write, measured by whether the shape, or anything structurally like it, appears anywhere in the live suite. For `INGEST.md` and `ACTIONS.md` text this row edits, row 8b's adaptation applies: a spec MAJOR counts when it is reachable using only calls and shapes the two documents print, over UC2, UC3 or the CA + CO fixture. A round that produces a MAJOR or BLOCKING fix is followed by a full round that sees it, the last round sees the final text and code, and nothing reviewed is edited while a lens is running.

**Cap: five rounds**, row 7b's and row 8c's. Each round runs three fresh lenses: the build implementer (code against `INGEST.md` §4 and the five amendments), the door adversary (`I-1` to `I-8`, K1 to K6, each by mutation), and the fidelity reviewer (the design tests and every number in §1 recomputed). **At the cap:** if round 5 still finds a reachable in-scope MAJOR, the row fixes it and runs one confirming round 6. If round 6 finds one, the row lands not clean with the finding recorded here and in `STATUS.md`, and it goes to the founder only if fixing it would decide a refusal. *Reason:* the founder said on 2026-11-16 and 2026-11-17 that round counts are process and the row's to decide.

### §0.10 — The commands this row will run, named before they are run

```
py docs/tools/ingest_write_probe.py [--assert]
py docs/tools/ingest_mutation_sweep.py
py tools/unasync.py
py -m pytest --pyargs ontoloche.contract ontoloche.aio.contract     # three legs, OO_POSTGRES_DSN set
py docs/tools/check_links.py
py docs/tools/check_spec_drift.py
py docs/tools/check_merge_guard.py
py docs/tools/check_capability_matrix.py
py docs/tools/check_skip_census.py
```

`OO_POSTGRES_DSN=postgresql://postgres:openontology@localhost:55432/open_ontology` (container `oo-pg`). The full suite takes about 22 minutes, so it runs in the background. The mutation sweep runs in batches if memory runs short.
