# 7B-RUN — roadmap row 7b: the ingestion build, read side

**Status:** in flight. **Opened** by the supervising session on 2026-11-18 under the founder's instruction *"you don't need my permission to move to the next item on the roadmap"*. **Brief:** [`handoffs/2026-11-18-row-7b-ingest-read-side-build-brief.md`](https://github.com/stephan-dyson/ontoloche/blob/main/docs/handoffs/2026-11-18-row-7b-ingest-read-side-build-brief.md). **Builds:** [`INGEST.md`](https://github.com/stephan-dyson/ontoloche/blob/main/docs/specs/INGEST.md) v0 §1, §2, §3, §5, §6 and §7, the read side. §4 and amendments A1 to A5 are row 7c's. **Spec run record:** [`7A-RUN.md`](https://github.com/stephan-dyson/ontoloche/blob/main/docs/runs/7A-RUN.md). **Branch:** `agent/row-7b`, cut from `main` at `1760a49`, local only.

**Claim tags:** **[Observed]** seen directly in this repo, in a command's output, or on a page opened this row · **[Inferred]** a reasonable read · **[Assumed]** believed, untested · **[guess]** an inference not checked, used where the global rules ask for it (read it as [Inferred]).

---

## §0 — PRE-REGISTRATION, committed before any code and any test

This section is the first commit of the row. Every prediction below is made from the brief, `INGEST.md` v0, `7A-RUN.md`, the throwaway kit [`docs/tools/ingest_probe_kit.py`](https://github.com/stephan-dyson/ontoloche/blob/main/docs/tools/ingest_probe_kit.py), the shipped code at `1760a49` and the public data as fetched on 2026-11-18. A wrong prediction stays here and is scored as a miss in §1.

### §0.1 — What was observed before this section was written

These are measurements, not predictions, and they shaped the predictions.

1. **Nothing of the read side exists in the package.** **[Observed]** `grep -rn "resolve_instance\|find_instance\|get_instance\|resolves_instances" ontoloche/` returns nothing at `1760a49`. `InstanceRef` exists in `ontoloche/edges.py`, `flat_form_problem` in `ontoloche/actions.py`, `_identity_closure` and `_IDENTITY_CHAIN_CAP = 16` in `ontoloche/registry.py`.
2. **The closed vocabularies have moved since `INGEST.md` §9 was written.** **[Observed]** `len(types.WARNING_VALUES) == 45` (§9 printed 37), `len(types.REFUSAL_REASONS) == 33` (§9 calls `instance_source_absent` the *thirty-second*), `len(adapter.CAPABILITY_FLAGS) == 17`. None of the seven reserved values is in either tuple. This is §8.1a finding 8, and it is now wider than when it was recorded: every ordinal in §9's table is wrong, not only the warnings'.
3. **`INGEST.md` has 90 rule rows and 90 distinct ids**, `C20-01` to `C20-90`. **[Observed]** `grep -cE '^\| [0-9]+-[0-9]+ \|' docs/specs/INGEST.md` → 90, and the ids in those rows' last cell, deduplicated → 90. The suite claims 479 ids in 21 groups and no `C20` id (`test_manifest.py`).
4. **The 7a probes, re-run at `1760a49`.** **[Observed]** `ingest_condition_probe.py` 17/17, `ingest_gate_probe.py` 11/11 (live NYC: `known {'existing': 38}`, `banded {'ambiguous': 23, 'existing': 1}`, `novel {'proposal': 38}`, the 7a numbers exactly), `ingest_act_probe.py` 41/41. `ingest_paging_probe.py` fails before its first check on `CERTIFICATE_VERIFY_FAILED` from the default `urllib` context, and the same URL answers through an explicit `certifi` context, so it is this machine's trust store, not the dataset. `ingest_seam_probe.py` **45/46: its one failure is the pin check**, because the CMS export has been replaced.
5. **The CMS health-citations export is a new file.** **[Observed]** the metastore now serves 165,372,053 bytes (sha256 `15185c61678f9bcc663076de666d5054a0ca34249c97206cf9e0e3f4ae922473`), 418,682 rows, 14,624 CCNs, 14,504 distinct provider names, 95 names shared by more than one CCN, `Processing Date` 2026-10-01. 7a pinned 165,336,194 / 419,479 / 14,627 / 14,498 / 104. **The fixtures the design tests rest on survive:** `BURNS NURSING HOME, INC.` is still one CCN (`015009`), `MILLER'S MERRY MANOR` is still twelve, `745040` (`THE SARAH ROBERTS FRENCH HOME`) and `745057` (`Tuskegee Airmen Texas State Veterans Home`) are both present, and California plus Colorado is still **1,373** facilities (1,164 + 209). This row's design tests run against the new file and say so. They do not claim 7a's figures.

### §0.2 — The build, stated so the predictions have a design to be wrong about

Each choice below is this row's, because none decides what the registry refuses or holds beyond what `INGEST.md`'s rules already say. Recorded with its reason, per the kickoff.

1. **One new module, `ontoloche/ingest.py`**, holding the printed shapes as frozen dataclasses (`InstanceRecord`, `CandidateQuery`, `CandidatePage`, `InstanceContext`, `InstanceCandidate`, `InstanceResolution`, `CandidateRef`, `MatchPolicy`, `Condition`, `ConditionResult`), the twelve-term vocabulary, a pure three-valued `evaluate`, and pure declaration validators returning the first breach or `None`. It imports nothing from `registry.py`, the way `edges.py`, `actions.py` and `properties.py` stand. *Reason:* the precedent keeps shape and validation code out of a 12,108-line registry, and the kit already proved the shapes.
2. **`CandidateRef` lands as a carrier only.** `InstanceResolution.candidate` is printed as `CandidateRef | None`, so the shape must exist for §8's printed `InstanceResolution` to be built. Its rules (4-9, `C20-69`) and every use of `act_id` beyond echoing it are row 7c's and stay planned. *Reason:* a printed field whose type does not exist fails `check_spec_drift.py`, and building the shape writes nothing.
3. **Two capability flags, exactly as §2.3 prints them:** `resolves_instances: bool = False` joins `CAPABILITY_FLAGS` (so C0-01 requires its `why` when False, and `check_capability_matrix.py` declines it one flag at a time), and `instance_filters: frozenset[str] = frozenset()` sits beside `attribute_projections`. Primitives 22 and 23 join the `StorageAdapter` protocol as optional methods, the way the edge and invocation primitives did.
4. **The reference backends read a host-owned table and own none.** `SQLiteAdapter`, `PostgresAdapter` and `MinimalSQLiteAdapter` gain an optional `instance_tables=` binding: per `(namespace, type_name)`, the host's table name, its id column, its label column, the attribute columns it exposes, the filter columns it honours, and an optional host scan cap (R58's third state, the way the kit's `scan_cap` and Socrata's 50,000-row page make it reachable). `migrate()` creates nothing for it and the adapter only `SELECT`s. With no binding, `resolves_instances=False` with a `why`. *Reason:* R78 says the host holds the instances. A migration-created `oo_instance` table would be an instance store under another name, which is §1's own sentence. A binding to a table the host created is exactly *a table the host owns, read through two read-only primitives*, and it lets all three legs run the same tests.
5. **Paging in the reference backends is by offset over a total order**, encoded as an opaque string, ordered by the id column and then every bound column. *Reason, and it is a prediction (§0.7, K3):* keyset paging on `id > :after` is the obvious implementation and silently skips every row sharing the boundary id, which is `I-6`'s shape inside the primitive itself, with `complete=True`.
6. **The governed facts live in the entry's `attributes`**: `match_policy` (`match_at`, `propose_below`, `ambiguity_margin`, `why`) and `instance_condition` (a `Condition`, as a nested mapping). Both are validated at `propose_type`, `approve` and `import_types` for `kind="entity"`, beside the existing `properties.declaration_problem` call, refusing `attributes_schema_violation` (§9's rule: a malformed `Condition` mints nothing) and declining an import row as `import_refused:attributes_schema_violation`. *Reason:* §5 and §6.3 say *declared on the entry and rides propose→approve*, and `attributes` is the shipped carrier for every other governed declaration.
7. **An entry with no `match_policy` answers `unknowable`**, with a `why` naming the missing declaration, never a default threshold. *Reason:* §5's table maps *nothing scored* to `unknowable`, and a registry-chosen threshold is the per-call threshold §5.1 refuses, chosen by the registry instead of by a caller. On `sqlite_minimal`, which declines `stores_attributes`, every entry is in this state, so that leg reaches only `unknowable`, `not_an_instance` and the capability refusal. That is the honest answer for a store that cannot hold a governed fact, and the tests that need a policy skip there with the backend's own `why`.
8. **`readable` (rule 6-4) is per record:** an attribute is readable when the record's `attributes` mapping carries the key, null or not. A key the record does not carry is `unknowable`. *Reason:* §2.3 mints no third flag and says *nothing else*, and a per-record reading needs none. For the reference backends this is exactly the bound attribute columns.
9. **`Registry.resolve_instance(candidate, context, *, type_name, namespace="default", tier, host_filter=None)`** exactly as §3 prints it, built from the kit's ordering: capability, entry, the closure, `not_an_instance`, the exhaustive read, the flat-form guard, distinct ids, the predicate, Rule U's six absorbers **before** any interpretation, then the tied set with its floor, then the bands. One closure function serves it and primitive 22's door.
10. **The closure is a new registry method built ON `_identity_closure`**, adopting its three relations, visited set and cap, and adding the two declines ING12 records: a cycle and a dangling successor are `complete=False` with a `why`, and so are a hop cap reached and a successor name carrying `:` or `#` (rule 3-22). *Reason:* R87 binds a citing document to all of the shipped function, and rebuilding the relations a second time is `I-8`'s origin.
11. **`Registry.get_instance_checked(type_name, instance_id, *, namespace="default")`** is primitive 22's registry door (finding 2). It walks the same closure, looks the id up under every member (rule 3-19's extent), collapses one row under two member names to one (rule 2-17), and applies the **effective** entry's `Condition`. Changed governed facts across any member is undecidable. It returns an `InstanceLookup` (`record`, `ref`, `why`, `governed_by`, `warnings`), so rule 2-15's *"`None` with a why"* has somewhere to put the why, and a `Refusal` when the predicate or the governed facts cannot be decided. `InstanceLookup` is a new printed shape this row adds to `INGEST.md` §8.
12. **Refusal reasons.** Exactly one is minted, `instance_source_absent`, the thirty-fourth. Rule 2-15's undecidable lookup and rule 2-14's flat-form refusal carry it with a `detail.problem` naming which, because that is the kit's executed default and §9 reserves no other value. **This is one word for two facts**, recorded as a contortion here (`ING13`, written in §1) rather than routed, because the founder question is *whether* the registry refuses, and the spec has already answered that.
13. **Warnings.** Four are minted, the read side's: `instance_narrowed_proposal`, `instance_type_succeeded`, `consumers_unregistered`, `no_tenancy_predicate`, and neither of §4's two (`instance_ambiguous_at_proposal`, `instance_proposal_pending`), which stay reserved for row 7c. §9's ordinals are rewritten against the tuples in the commit that mints them (finding 8): refusal 34, warnings 46 to 49, and 7c's two reserved as 50 and 51.
14. **`consumers_unregistered` (Q87's default, warn)** is emitted when `find_consumers(namespace)` returns no consumer. *Reason:* §7.1 and Q87 both speak of a namespace with no registered consumers.
15. **Contract ids.** `C20-01` to `C20-90` as `INGEST.md` numbers them, minus §4's thirteen (`C20-27` to `C20-34`, `C20-69` to `C20-72`, `C20-81`), which stay planned for row 7c. That is **77 ids built here**, each red first on all three backends where the backend can reach it. `check_spec_drift.py` gains `INGEST.md`: the shapes and signatures held to the code, every built id claimed by a test, every planned id named by no test, and §9's reserved table reconciled with the tuples. A fix the loop needs that no `C20` id covers gets `C20-91` onward and is listed in §1.
16. **The mutation sweep is a committed tool, `docs/tools/ingest_mutation_sweep.py`.** Each mutation is a literal `(file, old, new)` source edit applied to a scratch copy of the package. **The sweep fails if `old` is not found exactly once**, so a mutation cannot silently not apply (7A-RUN §6.10e-i, the harness that lied). Each mutation names the contract ids expected to go red, and the run records red or survived.

### §0.3 — Findings 1 and 2 first, in the kickoff's order

**Finding 1 (E22).** The eight rules §6.9c named, each shown red with its rule removed, against the shipped code:

| rule | id | the check | the mutation that must turn it red |
|---|---|---|---|
| 1-1 | `C20-01` | no registry table holds an instance row after a full resolution walk, and every `ref` handed out is a host row's | the registry returns a ref whose id is not a host row's |
| 2-1 | `C20-04` | the adapter protocol's instance surface is exactly two reads | a `put_instance` on the protocol |
| 2-2 | `C20-05` | `get_instance` for an absent id is `None` on every leg, and `get_instance_checked` reports it absent | a backend returning a manufactured record for an absent id |
| 2-5 | `C20-08` | the reference backends' `known` equals `len(records)`, and a page with `known=None, complete=False` resolves `unknowable` | the backend reporting `known=0` on a non-empty page, and the registry's third absorber removed |
| 3-4 | `C20-18` | on `ambiguous`, `known == len(candidates)` and every tied candidate is returned | returning the top candidate with `known` unchanged |
| 3-11 | `C20-25` | `tier` echoed back | dropping it |
| 6-17 | `C20-58` | `CandidateQuery` and primitive 23 take no tenant parameter | adding one |
| 2-12 | `C20-63` | a non-mapping `host_filter` is refused | accepting a string |

**Predicted:** eight of eight red, on every leg that can reach each rule. `C20-05` and `C20-08` are predicted to need the most care, because both are rules on a **backend's** honesty, and a test of the reference backends alone proves only that the reference backends are honest. Each therefore gets two checks: one on the backend's answer and one on the registry's handling of a dishonest-shaped answer through a test double.

**Finding 2 (E2).** `get_instance_checked` resolves the closure and applies the effective entry's predicate. **The check:** after `retire(facility, successor=ltc_facility)` with rows under both names, the same id is found (or found absent) identically under the declared and the effective name, and the predicate applied is the effective entry's. **Predicted:** the kit's construction (found under the declared name, absent under the effective one) reproduces against a naive build that calls primitive 22 once with the declared name, and the closure fix turns it.

### §0.4 — Predictions for each design test (brief §3)

All four run through the shipped `Registry` on SQLite with a host-owned table, in a committed probe, `docs/tools/ingest_build_probe.py`, and the contract suite carries the CMS 400-row sample (`ontoloche/contract/fixtures/cms_sample_400.csv`) on all three legs.

#### UC2 CMS — through real calls, on the 2026-10-01 file

`facility` declared with `match_policy = {match_at: 0.97, propose_below: 0.80, ambiguity_margin: 0.02}`, the kit's figures, the host table one row per CCN (14,624).

| label | predicted outcome |
|---|---|
| `BURNS NURSING HOME, INC.` | `existing`, `ref = cms:entity:facility#015009`, confidence 1.0, `known=1`, `complete=True` |
| `MILLER'S MERRY MANOR` | `ambiguous`, `ref=None`, `known=12`, every one of the twelve returned, confidence 1.0 |
| `THE SARAH ROBERTS FRENCH HOME`, with `745040` held out of the host table | `proposal`, `scanned=14,623`, top score below 0.80 |
| `Provider Name` | `not_an_instance`, `scanned=0` |
| `Tuskegee Airmen Texas State Veterans Home` with a host scan cap one row short of `745057` | `unknowable`, never `proposal`, and the uncapped control `existing` at 1.0 |
| `MILLER'S MERRY MANOR` with a scan cap one row past the first of the twelve | `unknowable`, never `existing` (`I-1`) |

**All five outcomes are reached on real CMS labels.** *"I already know 38 of these"*: the 7a gate probe's 100 live NYC rows (§0.1 item 4) are resolved through `Registry.resolve_instance` instead of the kit, under both host shapes §5.2 prints. **Predicted:** the one-instance-per-address host gives exactly the kit's `known {'existing': 38}`, `banded {'ambiguous': 23, 'existing': 1}`, `novel {'proposal': 38}`, and the un-deduplicated host gives `{'ambiguous': 13, 'existing': 25}` for the known group, as §5.2 prints. A mismatch here is a divergence between the build and the kit and is investigated before it is recorded.

#### UC3 NYC and the CA + CO fixture

1. **The tenancy predicate excludes above the primitive (R59).** `facility` declares `instance_condition = eq(state, "CA")`. Over the 1,373 CA and CO rows in one host table, **no** CO row is a candidate on any of the five labels CA and CO share, primitive 23 is called with no tenant argument, and each read considers all 1,373 rows. Predicted count of CO refs handed to the CA caller: **0**.
2. **The retire case under the Q91 default.** `retire(facility, successor=ltc_facility)` where `ltc_facility` declares a different `instance_condition` or `match_policy`: **every** label answers `unknowable` naming the changed fact. Predicted: 1,373 of 1,373 `unknowable`, as 7a measured, and 0 CO refs visible.
3. **A truncated scan answers `unknowable`, never `proposal`.** Over live `erm2-nwe9` rows behind a host table with a scan cap: 0 `proposal` on any capped read.

#### Paging

1. **A guard never reads a page (R58).** With the host page size forced to 7 rows over the 400-row sample, every outcome equals the unpaged control's on every label.
2. **An unfinished read cannot reach an outcome (rule 3-6).** Every page state R58 names (`complete=True`; `complete=False` with a cursor; `complete=False` without one) is produced by the reference backend and distinguished from the report alone, and no result with `complete=False` carries an outcome other than `unknowable` or `not_an_instance`, over every label the suite resolves.

### §0.5 — The falsifiers

- **F1, the seam (R78), now against code.** Falsified if any outcome needs a row this project stores. **Predicted: not falsified.** Measured by listing every table in the registry's schema after the UC2 walk-through: the reference schema's tables only, with no instance row in any of them.
- **F2, the kit as the reference.** Falsified if the build and the kit disagree on any label of the UC2 table or the gate batch. **Predicted: not falsified**, because the build is written from the kit's ordering. A disagreement is a defect in one of the two and is named.
- **F3, Q86 and Q92 contortions.** Where either bites, the measurement goes into §1 as a contortion. **Predicted:** Q92 bites once, on the un-deduplicated gate host, where `row_attributes` would separate ties it is never asked to.

### §0.6 — Contract ids, named before they are written

`C20-01` to `C20-90` as `INGEST.md`'s tables number them. Built here: §1 (`C20-01` to `03`), §2 (`C20-04` to `14`, `63` to `66`, `75`, `89`), §3 (`C20-15` to `26`, `67`, `68`, `76` to `80`, `86` to `88`), §5 (`C20-35` to `41`, `73`, `74`, `82`, `85`, `90`), §6 (`C20-42` to `58`, `83`) and §7 (`C20-59` to `62`, `84`). **77 ids.** Planned for row 7c, named by no test: `C20-27` to `C20-34`, `C20-69` to `C20-72`, `C20-81`. **13 ids.**

`C20-41` (rule 5-7, *the policy in force is recorded on the invocation*) is predicted to be the hard one: its invocation half has no carrier until amendment A5 (row 7c). This row builds its resolution half, `governed_by`, and pins that under `C20-41` and `C20-85` together, recording that the ledger half is 7c's.

### §0.7 — The kill-row doors the read side opens

Kill row at the start of this row: **twenty-three** trips (`STATUS.md`). The instance surface's eight cells, `I-1` to `I-8` (7A-RUN §6.9b and §6.13a), are the shapes to watch. For each, this row predicts where the shape recurs in the shipped build **before any lens runs**:

| cell | the shape | where this row predicts it recurs | predicted state at landing |
|---|---|---|---|
| `I-1` truncated | decide over a set the read said was partial | **`get_instance_checked`**: a lookup under one closure member that raises `NotSupported` or is refused while another member finds the row. A build that returns the found row has decided over a partial extent | closed by construction, `C20-66` |
| `I-2` mis-walked | the chain followed and reported complete when it was not | **reusing `_identity_closure`'s members as-is**, which continues with `complete=True` on a cycle and a dangling successor (ING12) | closed, `C20-76` to `C20-78` |
| `I-3` mis-written | the read bound by the chain, the write door not | **not opened**: no write door exists on this row. Its read half (rule 3-19, the whole closure) is built | read half closed, `C20-80` |
| `I-4` mis-keyed | the act keys differently from the gate | **not opened**: the act is row 7c's | — |
| `I-5` mis-timed | the guard's window closes early | **not opened**: row 7c's | — |
| `I-6` mis-counted | ids not distinct, two rows collapse | **inside the reference backend's cursor** (§0.2 item 5): keyset paging on a non-unique host id drops the boundary rows with `complete=True`, so the registry's distinctness check never sees the duplicate it exists to catch | closed by offset paging and pinned by a host table with a repeated id across a page boundary, `C20-75` |
| `I-7` mis-governed | the set is right and another entry's facts judge it | **primitive 22's door** (finding 2 itself), and secondarily **the warnings**: `consumers_unregistered` and `no_tenancy_predicate` read from the declared entry while the predicate comes from the effective one | closed, `C20-66`, `C20-79`, `C20-83` |
| `I-8` mis-directed | the closure walked forward only | **`get_instance_checked`** again, if it walks only the forward chain to find the effective entry and looks up under that name alone | closed, `C20-86`, `C20-87` |

**The new doors, listed before any code:**

| # | door | predicted state |
|---|---|---|
| K1 | `resolve_instance` | **not a door to the kill row**: it reads the type store and the host table and writes nothing. Its defects are Rule U defects |
| K2 | `get_instance_checked` | **not a door to the kill row**, same reason; it is where `I-1`, `I-7` and `I-8` are predicted to recur |
| K3 | primitives 22 and 23 in the three reference backends | **not a door**: `SELECT` only, on a table the host created. `check_merge_guard.py` Part A discovers no new identity writer |
| K4 | `match_policy` and `instance_condition` validation at `propose_type`, `approve`, `import_types` | **narrows**: it adds refusals and no write path |
| K5 | `retire(successor=)` and `merge_types` over entries now carrying `match_policy` or `instance_condition` | **inherited, unchanged**: both doors already copy or compare `attributes` as they do today. No new guard is added at either. Whether they *should* compare the new keys is the Q91 family's and is not decided here |
| K6 | the two new capability flags through `DegradedAdapter` and `check_capability_matrix.py` | **narrows**: declining `resolves_instances` produces `instance_source_absent` and nothing else |

**Predicted: zero new kill-row trips.** No door above writes a type row, so none can merge a capability predicate.

### §0.8 — What goes to the founder

**Predicted: nothing that blocks.** Q87 is built as `warn`, Q91 as `unknowable`, Q89 is off this row's surface, and none is decided. If the build meets a choice that makes the code refuse or hold something with no default to build, it goes into `DECISIONS-OPEN.md` as a new item and the row ends `BLOCKED ON FOUNDER`. §0.2 items 7 and 12 are the two places this row expects to come closest, and both have a default the spec already states.

### §0.9 — The stopping rule and the round cap

Row 6j's adopted criterion (`6J-RUN.md` §3.9, §5 item 10, ruled `Q5`): *"The loop ends when a full round finds no in-scope code MAJOR reachable by a shape a contributor would plausibly write — measured as: does the shape, or anything structurally like it, appear anywhere in the live suite?"* For `INGEST.md` text this row edits, row 8b's adaptation applies: a spec MAJOR counts when it is reachable using only calls and shapes `INGEST.md` prints, over UC2, UC3 or the CA + CO fixture. Bound, from `6I-RUN.md` §6.6 and `6J-RUN.md` §4.4: a round that produces a MAJOR or BLOCKING fix is followed by a full round that sees it, the last round sees the final text and code, and nothing reviewed is edited while a lens is running.

**Cap: five rounds**, row 8c's. Each round runs three fresh lenses: the build implementer (code against `INGEST.md` §1 to §3 and §5 to §7), the door adversary (`I-1` to `I-8`, K1 to K6, and the eight rules of §0.3, each by mutation), and the public-data fidelity reviewer (UC2, UC3, the gate batch, recomputing every number in §1). **At the cap:** if round 5 still finds a reachable in-scope MAJOR, the row fixes it and runs one confirming round 6. If round 6 finds one, the row lands not clean with the finding recorded here and in `STATUS.md`, and it goes to the founder only if fixing it would decide a refusal. *Reason:* the founder said on 2026-11-16 and 2026-11-17 that round counts are process and the row's to decide.

### §0.10 — The commands this row will run, named before they are run

```
py docs/tools/ingest_build_probe.py [--assert]
py docs/tools/ingest_mutation_sweep.py
py tools/unasync.py
py -m pytest --pyargs ontoloche.contract ontoloche.aio.contract     # three legs, OO_POSTGRES_DSN set
py docs/tools/check_links.py
py docs/tools/check_spec_drift.py
py docs/tools/check_merge_guard.py
py docs/tools/check_capability_matrix.py
py docs/tools/check_skip_census.py
```

`OO_POSTGRES_DSN=postgresql://postgres:openontology@localhost:55432/open_ontology` (container `oo-pg`). The full suite takes about 23 minutes, so it runs in the background.

---

## §1 — THE BUILD, AND WHAT IT MEASURED

Written after the code, the tests and the probes, against §0's predictions. Every number here is **[Observed]** from a command in §0.10 unless it is tagged otherwise.

### §1.1 — What was built

- **`ontoloche/ingest.py`**: the printed shapes as frozen dataclasses (`CandidateRef`, `MatchPolicy`, `Condition`, `ConditionResult`, `InstanceContext`, `InstanceResolution`, `InstanceCandidate`, `InstanceLookup`), the twelve-term `Condition` vocabulary, a pure three-valued `evaluate`, and the declaration validators. It imports nothing from `registry.py`.
- **`ontoloche/adapter.py`**: `InstanceRecord`, `CandidateQuery` and `CandidatePage`, plus primitives 22 `get_instance` and 23 `find_instance_candidates` on the protocol. It also adds the `resolves_instances` flag (the eighteenth in `CAPABILITY_FLAGS`) and the `instance_filters` projection set.
- **The three reference backends** read a host-owned table through `bind_instance_table(HostInstanceTable(...))` and create none. `migrate()` is unchanged. Paging is by offset over the id column and then every bound column (§0.2 item 5).
- **`Registry.resolve_instance`** and **`Registry.get_instance_checked`**, plus the closure walk built on `_identity_closure` and the `match_policy` / `instance_condition` validation at `propose_type`, `approve` and `import_types`.
- **Vocabulary**:
  - `instance_source_absent` is refusal reason 34.
  - Warnings 46 to 49 are `instance_narrowed_proposal`, `instance_type_succeeded`, `consumers_unregistered` and `no_tenancy_predicate`.
  - §4's two warnings stay reserved, as 50 and 51.
  - `check_spec_drift.py` holds every ordinal against the tuples.
- **77 contract ids** in `ontoloche/contract/test_c20_ingest.py`: `C20-01` to `C20-90` minus §4's thirteen, plus `test_ingest_finding_2_one_id_answers_alike_under_both_names`.
  - The async mirror is generated by `tools/unasync.py`.
  - `test_manifest.py` now counts **556 ids in twenty-two groups** and names the thirteen planned ids, so a test claiming one fails.
- **`docs/tools/ingest_mutation_sweep.py`** (38 mutations at 6891fbb, 49 after round 1, 66 after round 2: §2) and **`docs/tools/ingest_build_probe.py`** (24 checks).

### §1.2 — Findings 1 and 2

**Finding 1 (E22): eight of eight red, as predicted.** Every rule §0.3 named has a mutation in the sweep that removes it, and every one turns its test red.

- `C20-05` is red against a backend that manufactures a record for an absent id.
- `C20-08` has two checks. One is red against the registry with its uncountable check removed. The other runs through `DegradedAdapter(instance_known="zero")`, the dishonest backend that reports `known=0` over a non-empty page. That second check is the one that can go red on a backend's honesty, which a test of the reference backends alone cannot.

**Finding 2 (E2): built, and red without the closure.** The mutation that makes `get_instance_checked` call primitive 22 once, under the declared name, turns `test_ingest_finding_2_...` red. That is the kit's construction reproduced against the shipped code. With the closure, one id answers the same under both names and is judged by the effective entry's predicate.

**The sweep at 6891fbb:** `38 mutations: 38 killed, 0 survived, 0 not applied or broken. Required survivors: 0.` The 38 mutations cover 35 distinct `C20` ids and finding 2 (the first version of this sentence said 34; round 2's fidelity lens recounted). Its first run (37 mutations) found three defects, and all three were fixed rather than recorded:

1. **`2-11` survived, and it was a real defect.** The registry asks primitive 23 for `limit=500`, and the reference backend let `limit` override the host's `page_size`. So a host serving one row a page was read 500 rows at a time, and the cursor-following code was never exercised. Fixed in `_sql.find_instance_candidates`: a page is never larger than `page_size` or `limit`, whichever is smaller. `HostInstanceTable`'s docstring now says `page_size` is the most rows the host serves in one page.
2. **`6-17` did not apply.** Its anchor occurred three times in `adapter.py`, so the sweep refused it. That is the guard §0.2 item 16 built doing its job. The anchor now includes the `host_filter` line.
3. **`6-12` was broken.** `C20-53` takes no adapter, so the sweep's `-k sqlite` filter deselected it. The filter is now `not minimal and not postgres`.

**A fourth defect, from an automated security review, before round 1: `get_instance_checked` failed open on a malformed predicate.** A stored `instance_condition` that fails `condition_problem` (written past validation, through the adapter) made the lookup return the row as if no predicate were declared, while `resolve_instance` answered `unknowable` on the same entry. That is `I-7`'s shape at primitive 22's door. It now refuses `instance_source_absent` with `detail["problem"] = "predicate_undecidable"`. `C20-66` gained the construction, red before the fix **[Observed]**, and the sweep gained the 38th mutation, which reverts the fix and is killed.

### §1.3 — The design tests

`py docs/tools/ingest_build_probe.py --assert` passes **24 of 24 checks** over the 2026-10-01 CMS file (14,624 CCNs), the live NYC fetch included.

**UC2 CMS.** Every prediction in §0.4's table held:

| label | outcome |
|---|---|
| `BURNS NURSING HOME, INC.` | `existing`, `cms:entity:facility#015009`, 1.0, `known=1`, `complete=True` |
| `MILLER'S MERRY MANOR` | `ambiguous`, `ref=None`, `known=12`, all twelve returned |
| `THE SARAH ROBERTS FRENCH HOME`, `745040` held out | `proposal`, `scanned=14,623`, top score 0.6415 |
| `Provider Name` | `not_an_instance`, `scanned=0` |
| `Tuskegee Airmen Texas State Veterans Home`, cap one row short of `745057` | `unknowable`, and the uncapped control `existing` at 1.0 |
| `MILLER'S MERRY MANOR`, cap one row past the first of the twelve | `unknowable`, never `existing` (`I-1`) |

All five outcomes are reached on real labels.

**The gate batch, live.** 400 rows were fetched, with 271 distinct addresses, for a batch of 100. The one-instance-per-address host gave the kit's and 7a's numbers exactly: `known {'existing': 38}`, `banded {'ambiguous': 23, 'existing': 1}`, `novel {'proposal': 38}`. The host's actual rows gave `known {'ambiguous': 13, 'existing': 25}`, as §5.2 prints. A scan cap of 5 over the same host gave 100 of 100 `unknowable` and 0 `proposal`.

**UC3.** Over 1,373 CA and CO rows (1,164 + 209), with `instance_condition = eq(state, "CA")`:

- On the 5 names CA and CO share, 0 CO refs reached the CA caller, and every read considered all 1,373 rows.
- `CandidateQuery` has no tenant field.
- After `retire(facility, successor=ltc_facility)`, where `ltc_facility` declares a different predicate, all 1,373 labels answered `unknowable`, each naming the changed tenancy predicate. No CO ref was handed out.

**Paging.** At a 7-row host page, 802 labels each answered exactly as the unpaged control did. All three of R58's page states are produced and told apart from the report alone. No `complete=False` result carries a decided outcome.

**Departure from §0.4: the paging host.** §0.4 named the 400-row contract sample. That sample is 400 *citation* rows over **10 CCNs**, so a host table of it has 10 rows, and a scan cap of 20 never bites. The probe's first run failed its three-states check for exactly that reason. The paging host is the first 400 CCNs of the full file instead. The contract suite keeps the sample for what it is good for.

### §1.4 — The falsifiers

- **F1, the seam: not falsified.** On all four stores the UC2 walk-through builds (full, 745040 held out, and the two scan caps), every registry table's content digest is unchanged by the resolutions made over it, and no table exists outside the registry's schema and the host's. **[Observed]** Round 1 found the first version compared row counts on one store of four, which cannot see an UPDATE; the check now digests every row (§2.1).
- **F2, the kit as the reference: not falsified.** The build and the kit agree, on outcome and on `known`, on five UC2 labels in seven configurations (the two scan-capped answers included, after round 1 added them). **[Observed]** The gate batch is compared as per-group outcome tallies on the deduplicated host, with no per-label match and no `known`, which is weaker than §0.5's "any label".
- **F3, the Q86 and Q92 contortions: could not be exercised here, so Q92 did not bite where §0.5 predicted.** On the un-deduplicated gate host, each of the 13 `ambiguous` answers is a tie between service requests at one address. The host is narrowed to one ZIP code, so the tied rows share every bound attribute, and `row_attributes` would not have separated them even if it were asked to. Whether Q92 bites on a host whose tied rows *do* differ in a bound attribute is not measured here.

### §1.5 — Q93: rule 3-19's read cost, measured

ING11 said rule 3-19's cost was unmeasured. Over the 14,624 CMS rows, split 7,312 / 7,312 between `facility` and its successor `ltc_facility`, the two-member closure read 14,624 rows. That equals the one-member read over one table, and it found the same answer (`existing`).

**The cost is the extent, not a multiple of it, in rows and in calls.** **[Observed]** The probe counts primitive 23 calls: 30 for the one-member read and 30 for the two-member read. The call count is about ceil(rows / page) per member, so a closure adds at most one call per extra member, for that member's last partial page **[Inferred** from one two-member case**]**. Wall time was 438 ms against 432 ms, one warm run each (round 2's re-run: 485 against 488 ms), so any difference is noise [guess]. The first version of this section said the closure "multiplies the number of calls by its size", which the round-1 fidelity lens measured as false (§2.1). That answers Q93 for a closure whose members partition the rows. A host that stores the same rows under both names would read them twice before rule 2-17 collapses them back to one [guess: not measured here].

### §1.6 — Contortions and departures recorded here, not routed

- **ING13, one refusal word for several facts.** `instance_source_absent` carries the capability refusal, every undecidable lookup from `get_instance_checked`, and `resolve_instance`'s rule 2-14 flat-form refusal (`unfaithful_reference`), with `detail["problem"]` naming which. The values are `capability`, `closure_incomplete`, `lookup_incomplete`, `governed_facts_changed`, `predicate_undecidable` and `unfaithful_reference`.
  - The cost: a caller that branches on `reason` alone cannot tell *"this backend cannot do this"* from *"this lookup could not be decided"*.
  - §0.2 item 12 predicted this. It is not routed, because the founder question would be *whether* the registry refuses, and the spec already answers that.
- **A missing entry or a missing `match_policy` answers `unknowable`.** The kit refused a missing entry with `instance_source_absent`, and its `EntryDeclaration` could not be built without a policy. The build answers `unknowable` with a `why` naming the missing declaration (§0.2 item 7).
  - The reason: §5's table maps *nothing scored* to `unknowable`, and `instance_source_absent` is a capability refusal. A declaration gap is not a capability.
  - The consequence on `sqlite_minimal`, which declines `stores_attributes`: every entry is in this state, so the tests that need a policy skip there, citing the backend's `why`.
- **The page convention is the shipped one, `TypePage`'s.** §0.4's *"three states"* are exactly these:
  - a page with more behind it is `complete=False` with `next_after` set;
  - the last page is `complete=True` with no cursor;
  - a truncated read is `complete=False` with no cursor and a `why`.
- **Code before tests, in part.** The kickoff's order was tests red first. For most of the 77 ids the implementation was written first, from the kit's ordering, and the tests after. **The red evidence is the mutation sweep instead**: every id it covers is shown red with its rule removed (and `C20-66`'s malformed-predicate case was red before its fix), against the shipped code. That was 35 ids at 6891fbb, and is 38 after round 2. **For the other 39 ids there is no recorded red run** (42 at 6891fbb; the first version said 34 and 43). This is a departure from the order, stated rather than hidden.
- **Retire and merge are scaffolding in 21 tests** (eleven at 6891fbb, 16 after round 1; now 20 carry `NEEDS_RETIRE` and 1 `NEEDS_MERGE`).
  - The closure tests need a retired type, and `retire(successor=)` asks for consumer evidence. On a backend that declines `indexes_membership`, those tests do not run, rather than forcing past a guard they are not about.
  - `C20-87` needs `merge_types`, which also needs `stores_events`.
  - Both are marked `requires_capability`, the convention `test_c19_actions.py` uses. `check_capability_matrix.py` failed in every configuration until they were.
- **`host_instances` skips when a double declines `resolves_instances`.** In that case the table is bound and the adapter says it cannot read it, which PACKAGE.md 3.2 calls conformant. The ids whose *subject* is that state, `C20-03` and `C20-12`, do not use the helper.

### §1.7 — Against §0.7 and §0.8

- **Kill row: zero new trips, as predicted.** `check_merge_guard.py` Part A discovers no new identity writer, and K1 to K3 write nothing.
- **Founder: nothing routed.** No choice met on this row made the registry refuse or hold something without a default the spec states.

- **An adapter written before row 7b must now state why it declines `resolves_instances`.** The flag defaults to `False`, and C0-01 asks for the sentence, as it did when 6a and 6b added `stores_edges` and `stores_invocations`. `C19-43` builds exactly such an adapter and failed in every matrix configuration until its fixture carried the `why`. This is a compatibility cost on third-party adapters, the same one 6a and 6b imposed, and it is stated here rather than discovered by an adapter author.
- **`C20-09` and `C20-58` inspect the bound method, not `type(adapter)`.** The matrix's `WithoutAttributeStore` forwards through `__getattr__`, so its class has no `get_instance`. The bound method is the backend's code that actually answers.

### §1.8 — Gates and the suite

Filled at landing, from the final run on the landing commit.

## §2 — THE ADVERSARIAL LOOP

Row 6j's stopping rule (§0.9): three lenses per round, build, door and fidelity, each fresh. The loop stops when a round finds nothing MAJOR, and the round after it confirms. Cap 5 rounds, round 6 confirming. Nothing a lens is reviewing is edited while it runs.

### §2.1 — Round 1, on 6891fbb

**Build lens. 2 MAJOR, 6 minor.**

1. **MAJOR, E10.** `_governed_change` compared the raw mappings, so a reworded `why` stopped the closure, and so did an `in` list in another order. INGEST.md 5.3 says "different" is the three thresholds and the predicate's terms. **Fixed:** `_policy_terms` compares the thresholds as floats, and `_condition_terms` drops `why` at every level and treats `in` / `not_in` values and `all_of` / `any_of` terms as sets. Tests `C20-79` r1 (both directions). Mutation shown red.
2. **MAJOR, rule 2-17.** `resolve_instance` ran the predicate over every copy and collapsed after, so a stale copy that passed decided `existing` where the current copy failed, while `get_instance_checked` collapsed first and excluded the row. The two doors judged different copies. **Fixed:** one helper, `_one_copy_per_identity`, used by both doors before the predicate, keeps the effective name's copy. Where the host holds no copy under the effective name and the copies differ, no copy is current: the read door answers `unknowable` and the lookup door refuses `lookup_incomplete`. Tests `C20-89` r1 (two). Two mutations shown red.
3. **Minor, 3.4's third absorber.** It was `known is None`, which also caught a finished read that cannot count. The spec's absorber is `known=None` and `complete=False` together. **Fixed**, and the `C20-08` "none" branch, which never seeded a policy and so was red for the wrong reason, is replaced by two r1 tests (finished, and not). Mutation shown red.
4. **Minor, rule 2-11.** A cursor handed back twice looped forever. **Fixed:** a seen-cursor set per member ends the read `unknowable`. Test `C20-14` r1. Mutation shown red.
5. **Minor, rules 3-3 and 5-8.** `0.98 - 0.96` is `0.020000000000000018`, outside a 0.02 margin. **Fixed** with a 1e-9 epsilon on float subtraction only. Test `C20-17` r1. Mutation shown red.
6. **Minor, rule 5-9.** The bands were tested on the score rounded to four places, so 226/233 = 0.96996 crossed `match_at` 0.97. **Fixed:** bands read the raw score, rounding is display only. Test `C20-74` r1. Mutation shown red.
7. **Minor, recorded, not fixed and not routed.** A retired entry with no policy whose successor has one is locked out (`unknowable`). That is the Q91 family, and Q91's default (`unknowable`) is in force on this row, so it is a departure under that default, not a new ruling.
8. **Minor, rules 7-1 and 7-4.** `not_an_instance` carried neither `no_tenancy_predicate` nor `consumers_unregistered`, and both rules say every resolution carries them. **Fixed.** Test `C20-62` r1. Mutation shown red for the 7-4 half; the 7-1 half (`consumers_unregistered`) got its mutation in round 2.

**Door lens. 1 MAJOR (the same as build 2), 5 test gaps, 5 near-miss mutations.** K5 and K6 came back clean.

- `I-1` at primitive 22's door was untested: only the successor's table bound gives `lookup_incomplete` (T1), and a CCN on two rows refuses (T2). Tests `C20-66` r1 (two). Mutation shown red for T1.
- `C20-05` never exercised the type-column binding (T5). Test added; mutation on the SQL type-column clause shown red.
- `C20-08` had no over-count. `DegradedAdapter` gained `instance_known="over"`; test added; mutation shown red.
- The seam's `snapshot` (`ontoloche/contract/_support.py`) read five tables. It now also reads attribute observations, edges and invocations, each guarded so a backend without the store is not asked. Test `C20-01` r1.
- `C20-18`'s widest tie was three. Test with eight added.
- The near-misses G, I, J, K and L are guarded by `C20-04` r1, `C20-58` r1, `C20-63` r1, the `C20-89` r1 effective-copy test and `C20-25` r1. No mutation of them is shown red, and all five were green on 6891fbb.

**Fidelity lens. 1 MAJOR, 6 minor.** Every number in §1 except one recomputed exactly.

- **MAJOR.** §1.5 said the closure multiplies primitive 23 calls. The lens measured 30 against 30. **Fixed:** the probe now prints call counts, and §1.5 says what they show.
- F1 compared counts on one store of four (fixed, §1.4). F2 omitted the capped pairs (added). The probe docstring said "gate-batch label" (now "group"). F3 now leads with "could not be exercised". The paging control compares refs and candidate ids too. The Q93 timings are labelled one warm run each.

**After the fixes. [Observed]**

- The 20 r1 tests: 9 were red on 6891fbb before any code change, and the other 11 were green and are kept as guards. Two of the 9 (`C20-08` over-count, `C20-01` snapshot) were red because the test support lacked the double's mode or the snapshot's reads; against the shipped registry with round 1's support, 7 are red (round 2 fidelity lens). All 20 are now green on SQLite, sync and aio.
- The mutation sweep (`docs/tools/ingest_mutation_sweep.py`): 49 mutations, 49 killed. That is 11 new ones for round 1, plus 6 older ones re-anchored because the rewrite moved the text they named.
- The probe (`docs/tools/ingest_build_probe.py --assert`): 24/24 checks pass.
- aio was regenerated with `tools/unasync.py`. Its first run refused a lambda in `snapshot`, which would have needed an `await`; the reads are now written without lambdas.
- **Found by the full SQLite run, not by a lens.** On 6891fbb, `ontoloche/aio/contract/test_manifest.py` still expected `C20-01` to `C20-77` and did not know about `PLANNED_IDS`, so it reported row 7c's twelve ids as missing. That file is hand-written, not generated by unasync. It now uses the sync manifest's `enumerated_ids()`. Both manifest tests pass. **[Observed]** The rest of the run: 1,727 passed, 1,964 skipped (Postgres legs off), 1 failed (this test).

### §2.2 — Round 2, on a27a4df

**Build lens. 2 MAJOR, 4 minor.**

1. **MAJOR, rule 2-2 with standing rule (e).** Primitive 22 compared the stored id with the string it was given, while primitive 23 mints the ref from `str(id)`. An integer 42 in a column that converts nothing was `existing #42` at one door and absent at the other. **Fixed:** `get_instance` compares `CAST(id AS TEXT)`, and the type column the same way at both primitives. The cost is the id column's index [Inferred]. The type-column cast has no test and no mutation of its own. Test `C20-05` r2, on a column typed so the database converts nothing (BLOB on SQLite, whose INTEGER affinity would convert `'42'`; INTEGER on Postgres). Red on a27a4df, mutation shown red.
2. **MAJOR, rule 2-17.** With no copy under the effective name and agreeing copies under two others, the kept copy was the first in closure order, which starts at the caller's declared name: `a#015009` from one caller and `b#015009` from another. **Fixed:** an identity held under more than one member resolves under the effective name, as the rule says. One copy under one name stays that name's row. Test `C20-89` r2. Red on a27a4df, mutation shown red.
3. **Minor, rules 5-8 and 5-9.** Round 1's epsilon was on the thresholds too, so 0.9 counted as at `match_at` 0.9 + 5e-10. **Fixed:** thresholds compare exactly, and the epsilon stays on `top - score` only. Test `C20-73` r2 (a hair below). Red on a27a4df.
4. **Minor, E10.** `_condition_terms` compared `in` members by `repr`, so `not_in [1]` and `not_in [1.0]` differed though `evaluate` treats them as one. It also stripped `why` inside an operand. **Fixed:** members compare by Python equality (the equality `evaluate` uses), and `why` is dropped only from a Condition. Test `C20-79` r2. Red on a27a4df, mutation shown red. The operand case had no test, and the guess that a mapping operand cannot be declared was wrong: round 3's fidelity lens ran `condition_problem` and it accepts one. Round 3 adds `C20-79` r3.
5. **Minor, rule 2-11.** A backend handing back empty pages with a fresh cursor each time was paged without end. **Fixed:** `INSTANCE_READ_PAGES_MAX` (10,000 pages per member) ends the read `unknowable`. Test `C20-14` r2. Red on a27a4df, mutation shown red.
6. **Design note, recorded.** One identity whose copies disagree, none current, makes every resolution over that closure `unknowable`, not only the ones that would score it. This is how rule 2-16 treats an uncountable extent. §3.4b does not state it for 2-17, so it is a departure under the build's reading, not routed: the default (`unknowable`) is the conservative one Rule U already gives.

**Door lens. 9 MAJOR survivors, all test gaps over code that was right.** For each one, the whole C20 file stayed green with the mutation applied.

- The `ambiguity_margin` threshold in rule 3-18's comparison (`C20-79` r2).
- The four exact edges: existing at `match_at` (`C20-73` r2), a second candidate at `match_at` (`C20-17` r2), a top at `propose_below` (`C20-74` r2), and the inclusive floor (`C20-90` r2).
- Rule 6-1 recursively (`C20-42` r2) and rule 6-4 for `is_null` / `is_not_null` (`C20-45` r2).
- Primitive 22's refusals for a dangling closure and for changed governed facts (`C20-66` r2, two).
- Each has a required mutation in the sweep, shown red.

**Door lens minors taken:** the host filter reaching primitive 23 (`C20-64` r2), the disagreeing-copies branch (`C20-89` r2), a scored answer carrying its score (`C20-23` r2), and the host's `page_size` capping a larger `limit` (`C20-11` r2).

**Door lens minors recorded, not acted on:**

- Shape validators no rule row names: thresholds outside [0, 1], `bool` as a number, extra keys, a value on `is_null`, an empty attribute, a null inside `in`, and a `TypeError` in a comparison answered `False`. These are not in INGEST.md's tables, so none is a breach [Inferred]. They are row 7c's or a later row's to tighten.
- Unicode `norm` against the kit's ASCII regex. This is ING3 / K10's recorded departure, and C20 does not test it.
- Survivors in fields the rules do not fix: `unknowable` carrying `()` instead of the top five, a tie-break key, `act_id`, and the `None`-label rendering.
- **The merge guard has no probe of the two instance doors.** `check_merge_guard.py` asks `resolve_type` on its stale axis but neither `resolve_instance` nor `get_instance_checked`. The lens did not build a collapse through them, so this is unverified as a live defect. Round 3's door lens is asked to try.

**Fidelity lens. 1 MAJOR, 2 stale counts, 7 minor, all fixed in place above.**

- **MAJOR:** §1.2 / §1.6 said 34 ids and 43, where it should be 35 and 42.
- **Stale counts:** 38 mutations, and "eleven tests".
- **Minors:** the 9-red nuance, F2's gate comparison, the [Inferred] tag in §1.5, `[guess]` in the legend, ING13 naming both doors, G to L "guarded" rather than "closed", and the 7-1 half's mutation.
- **The lens also confirmed:** every other number in §1 and §2.1 recomputes, every §0 prediction is reported against what happened, and no departure hides a founder ruling.

**After the fixes. [Observed]**

- The 18 r2 tests: 5 were red against a27a4df's code on SQLite (with round 2's test support), and 13 were green and close gaps. All 18 are green on SQLite, sync and aio (21 collected items, with the three that also run on `sqlite_minimal`). The first version of this line said 21 / 16 / 21, counting items, where §2.1 counts functions (round 3 fidelity lens).
- The sweep: 66 mutations, 66 killed. That is 17 new, plus 3 re-anchored where round 2 changed their text.
- The three-leg suite on a27a4df, with round 2's aio `_support.py` regenerated mid-run (SQLite, minimal, Postgres; sync and aio): 2,905 passed, 784 skipped, 3 failed. All 3 are the aio `C20-01` r1 source-inspection test. Round 2 regenerated aio `_support.py` while that run was in flight, so `inspect.getsource` read the new file at the old line numbers [Inferred]. Re-run on stable files, it passes on all three legs (6 passed). The landing run is §1.8.

### §2.3 — Round 3, on 389e632

**Build lens. 1 MAJOR, 2 minor.**

1. **MAJOR, rule 2-2 with standing rule (e): round 2's fix covered integers only.** The ref's id was minted by Python's `str()`, and primitive 22 compared the database's `CAST(id AS TEXT)`. Two different conversions disagreed on REAL and BLOB ids: `1e+20` against `1.0e+20`, `0.30000000000000004` against `0.3`, and `b'015009'` against `015009`. In each case one door handed out a ref the other read back as absent. **Fixed:** the id is selected as `CAST(id AS TEXT)` and minted from that text, so one conversion serves both primitives. Ids the database renders as one text become one id on two rows: rule 2-16 at primitive 23, and the two-row refusal at primitive 22. Tests `C20-05` r3 (REAL ids and, on SQLite, a bytes id) and `C20-16` r3 (`0.1 + 0.2` against `0.3`). `C20-05` r3 was red on 389e632, and its mutation is shown red. On Postgres the test uses a `DOUBLE PRECISION` column, because INTEGER holds neither 1e20 nor bytes. Its first Postgres run failed on construction for exactly that reason. **[Observed]**
2. **Minor, rule 3-18.** A NaN operand was accepted at declaration, and NaN equals nothing, itself included. A predicate carrying one could never equal its own copy, and `eq NaN` holds for no row. **Fixed:** `condition_problem` refuses a non-finite number. Test `C20-47` r3, red on 389e632, mutation shown red.
3. **Note, recorded for row 7c.** A multi-copy identity's ref names the effective type (rule 2-17), which may hold no host row of its own. `get_instance_checked` reads it back through the closure, while raw primitive 22 under that name answers `None`. **Row 7c must re-read a recorded ref through `get_instance_checked`, never through primitive 22 directly.**

**Door lens. 1 live MAJOR, 5 MAJOR test gaps, 2 minor.** The lens listed the 39 ids with no sweep mutation and attacked those first.

- **MAJOR, live, rules 3-21, 2-17 and 5-11: an alias did not move the effective name.**
  - **The construction, public calls only:** `legacy_home` is retired with no successor, then `import_types` writes `facility` with the alias `legacy_home`.
  - **Observed:** `resolve_type("legacy_home")` answered `facility`. The instance doors answered `legacy_home#015009`, `governed_by default:legacy_home`, and proposed under the tombstone, a name `resolve_type` never hands out.
  - **Why:** the forward walk followed `successor` only.
  - **Fixed:** a retired entry with no successor that a live entity entry answers to (`_alias_holder`, the same look `propose_type` uses) is a hop to that entry. A look that cannot finish stops the closure, under Rule U.
  - **Tests:** `C20-89` r3 (both names give one ref and one `governed_by`, and the proposal is under `facility`), red on 389e632 with its mutation shown red. Also `C20-87` r3, which asks that the closure read the alias's table, `scanned == 3`. That was green on 389e632, and its mutation is shown red.
  - **This was also the merge-guard question round 2 left open.** The lens found no other route: entity identities never go stale at `resolve_type`, predicate and action words cannot enter the closure, and successor chains are walked.
- **The test gaps, each now a required mutation shown red:**
  - primitive 22's refusal for a successor declaring no governed facts (`C20-84` r3);
  - `not_in` over null (`C20-46` r3);
  - a host filter never replacing the predicate (`C20-56` r3);
  - an undecidable combinator carrying its `why` (`C20-44` r3).
  - **Fixing `C20-84` r3 surfaced a test-helper defect.** The first version survived its own mutation. `_successor_world` read `new_governed={}` as "use the default", so the successor was never bare. The helper now tests `is None`, and the mutation is killed.
- **Minors taken:** a proposal that scored nothing carries `confidence=None` (`C20-23` r3), and `is_null` refuses terms (`C20-51` r3). Both have mutations, shown red.
- **Minor recorded, not acted on: a door difference no rule row covers.** On a retired entity with no successor and no alias holder, `resolve_type` answers `proposal`, while `resolve_instance` reads the retired entry's host table and can answer `existing old#015009`. INGEST.md 3.4a governs a retired entry only through its successor chain. Reading a tombstone's own table is the build's reading of rules 3-14 and 3-15 [Inferred], and it is recorded here as a departure. It is not routed, because the conservative alternative (`unknowable`) and this behaviour both have a default the spec does not choose between. No refusal or hold is in question.

**Fidelity lens. 1 MAJOR, 5 minor, all fixed in place in §2.2 and the probe.**

- **MAJOR:** the r2 test count was 18 / 13 / 18, not 21 / 16 / 21.
- **Minors:**
  - the operand guess was wrong;
  - the type-column cast is untested;
  - the red claims are SQLite's;
  - the a27a4df suite ran over a mid-run regeneration;
  - the probe strings now say "7 UC2 configurations".
- **Everything else recomputes:** the probe passes 24/24, and the sweep killed 66 of 66 covering 38 ids, with the 17 new and 3 re-anchored as stated. The markers are 20 + 1.

**After the fixes. [Observed]**

- **The 12 r3 test functions, on 389e632's code on SQLite:**
  - **Red:** 3. These are `C20-05` r3, `C20-89` r3 and `C20-47` r3.
  - **Green:** 8, which close gaps. `C20-84` r3 needs the corrected helper to be meaningful.
  - **Skipped:** 1, `C20-16` r3. That code minted the two ids apart, so there was no collision to test.
  - **Now:** every r1, r2 and r3 test passes on sync and aio, on all three legs (222 passed, 78 skipped).
- **The sweep:** 76 mutations, 76 killed. 10 of them are new in round 3.
