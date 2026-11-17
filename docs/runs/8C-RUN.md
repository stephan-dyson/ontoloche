# 8C-RUN — roadmap row 8c: the properties build row

**Status:** in flight. **Opened** by the supervising session on 2026-11-17 under the founder's instruction *"keep the project moving forward"*, once founder ruling [R111](../decisions/2026-11-17-founder-ruling-R111.md) (`fold into the build row`) and row 8a's merge into `main` (`bf91ae8`) met the brief's §0 gates. **Brief:** [`handoffs/2026-11-12-row-8c-properties-build-brief.md`](../handoffs/2026-11-12-row-8c-properties-build-brief.md). **Builds:** [`INTERFACE.md` §2.10](../specs/INTERFACE.md) under ruling [R108](../decisions/2026-09-22-founder-ruling-R108.md). **Branch:** `agent/row-8c`, cut from `main` at `147d871`, local only.

**Claim tags:** **[Observed]** seen directly in this repo, in a command's output, or on a page opened this row · **[Inferred]** a reasonable read · **[Assumed]** believed, untested.

---

## §0 — PRE-REGISTRATION, committed before any change to `INTERFACE.md`, any code and any test

This section is the first commit of the row. Every prediction below is made from the brief, R108, R111, `INTERFACE.md` §2.10 as landed by row 8b, [`8B-RUN.md`](8B-RUN.md), [`8A-RUN.md`](8A-RUN.md), the shipped code at `147d871` and the fixtures. A wrong prediction stays here and is scored as a miss in §1.

### §0.1 — What was observed before this section was written

These are measurements, not predictions, and they shaped the predictions.

1. **The baseline probe still reproduces row 8b's table.** **[Observed]** `py docs/tools/properties_baseline_probe.py` at `147d871` prints every line 8B-RUN §1.0 to §2.4 recorded, D1 to D14 and C10, with the same values: re-import replaces `attributes` (D7, D7b), `sqlite_minimal` keeps only `primary_key` with no warning (D9), `retire(successor=)` collapses two differing properties with no acknowledgement (D2), a used property and a used value set retire silently (D6, D13), and D14's two live claimants with `reinstate` refused `successor_active`.
2. **The closed vocabularies are where §2.10 says.** **[Observed]** `len(types.WARNING_VALUES) == 39`, 33 refusal reasons, and `types.KINDS == ('entity', 'predicate', 'edge', 'value_set')`.
3. **The contract suite claims 448 ids** and group `C12` ends at `C12-68` **[Observed]** (8A-RUN §1.6's landing run: sqlite and postgres 448 exercised each, `sqlite_minimal` 128). No `C21` id is claimed.
4. **The Foundry fixtures, measured per property** **[Observed]** by reading the committed JSON under `ontoloche/contract/fixtures/`:

   | fixture | object types | properties | no description | shared property types | `sharedPropertyTypeMapping` |
   |---|---|---|---|---|---|
   | `foundry_faux_employee.json` | 2 | 19 | 6 | 0 | `Employee`: `fooSpt` → `fullName` (dangling) |
   | `foundry_faux_legacy.json` | 10 | 75 | 61 | 1 (`fooSpt`, `string`, described `"A foo"`) | `Employee`: `fooSpt` → `fullName` |
   | `foundry_uc2_cms.json` | 4 | 4 | 4 | 0 | none |
   | `foundry_uc3_nyc.json` | 2 | 2 | 2 | 0 | none |
   | `foundry_edge_cases.json` | 10 | 10 | 10 | 0 | none |
   | **total** | **28** | **110** | **83** | **1** | |

   Top-level `opaque` types (§2.10's table): 6 in `employee` (`geopoint`, `geoshape`, `geotimeSeriesReference`, `timeseries` ×2, `vector`) and 13 in `legacy` (`attachment` 2, `cipherText` 1, `geopoint` 2, `geoshape` 2, `geotimeSeriesReference` 1, `mediaReference` 1, `timeseries` 2, `vector` 2). Three arrays have a `struct` sub-type (`Employee.bonusHistory`, `BgaoNflPlayer.addressArray`, `ComplexImplementationObject.multiStructArray`), and no array has an `array` sub-type.
5. **Two statements in §2.10 are stale against the merged row 8a.** **[Observed]** `ontoloche/foundry.py` now reads `implementsInterfaces2` and carries it in `attributes["foundry_object_type_metadata"]` (8A round 2), so §2.10's *"row 8a's importer does not read `implementsInterfaces2` at all"* is false on `main`. And R109's hold lives at `import_types` too (8A defect 4), so a `kind="property"` entry with no definition is **held `definition_missing` today**, which is half of what rule 2.10-21 says Q106 decides. Both are fidelity corrections this row makes in §2.10 (§0.3 item 4), not new decisions.

### §0.2 — The build, stated so the predictions have a design to be wrong about

Each choice below is this row's to make, because none decides what the registry refuses beyond what §2.10's non-reserved rules already say. Recorded with its reason, per the kickoff.

1. **One new module, `ontoloche/properties.py`.** It holds `BASE_TYPES`, the three printed shapes as frozen dataclasses, the two printed view functions, a pure `declaration_problem(kind, attributes)` returning the first breach as `(rule, key, slot)` or `None`, and the rule 2.10-11 reader. It imports nothing from `registry.py`, the way `edges.py` and `actions.py` stand. *Reason:* §2.10 names the module, and the precedent keeps view and validation code out of the 11,856-line registry.
2. **Validation is wired at three doors, `propose_type`, `approve` and `import_types`, for `kind="entity"` and `kind="property"` only**, beside the existing `edges.family_declaration_problem` and `actions.family_declaration_problem` calls, refusing `attributes_schema_violation` with `detail = {rule, key, slot}` and declining a row at import as `import_refused:attributes_schema_violation` (rule 2.10-2). No other door gains a check.
3. **Six warnings are minted, the ones §2.10 reserves:** the five `property_reference_*` values (rule 2.10-10) and `property_declaration_not_stored` (rule 2.10-16). §5.4 goes from 39 to **45**, and `types.WARNING_VALUES` with it, in the commit that emits them. **No refusal reason is minted**: §5.12 stays at 33.
4. **`property` joins `types.KINDS`** (rule 2.10-22, documentary). `actions.PROPOSABLE_KINDS` is unchanged.
5. **The importer's mapping.** `import_foundry` plans, in order, predicates, **shared property types as `kind="property"` entries**, entities, edges, actions, so a shared property is written before an entity names it (rule 2.10-10's import-order note). It still makes one `import_types` call per kind. A shared property type's entry carries `base_type`, `display_name`, `item_type` and `source_type` per §2.10's table, and its `description` as the entry's `definition`, held `definition_missing` under R109 when absent, which is today's behaviour at that door. An object type property becomes one slot under `attributes["properties"]`: a **shared** slot (`name`, `shared`, `display_name`) when the object type's `sharedPropertyTypeMapping` maps a shared property type onto it, and a **local** slot otherwise. `primaryKey` becomes a one-element `primary_key` list and `titleProperty` becomes `title_property`. An absent or blank property description is **omitted from the slot, not filled**: rule 2.10-21 is reserved, and today `import_types` writes such a slot as given, so the build keeps that and the dry run counts it.
6. **R105's carry, narrowed and not deleted.** `attributes["foundry_properties"]` stops carrying what now has a home (data type, display name, description, key, title). It keeps, per property apiName and verbatim, each fact §2.10 gives no field (`typeClasses`, `status`, `visibility`, `valueTypeApiName`, `valueFormatting`, `dataConstraints`, `rid`, and a shared slot's own source `dataType`, which rule 2.10-3 forbids on the slot), still marked `"validated": false`. *Reason:* rule 2.10-3 says such facts are kept outside the slot by the importer, and the brief says nothing is dropped.
7. **The dry-run report gains a `properties` section**: per entity, slots planned (local, shared), `opaque` landings, slots with no description, shared references that resolve to nothing in the plan or the store, and every fact with no home, each with a reason (`interface_property_contract`, `struct_fields`, `array_reducers`, `implements_interfaces2`, `no_slot_field:<key>`). A property is in a planned slot or in that list, never neither.
8. **Rules 2.10-17 to 2.10-21 are built as today's behaviour and pinned by the probe, not by a contract id.** `properties_baseline_probe.py` gains an `--assert` mode that exits 1 when any reserved-rule line differs from the value this record states. *Reason:* a contract id is something a third-party backend certifies, and asking a backend to certify a behaviour the founder has not ruled would make the ruling look like a regression later. The probe is the measurement the brief asks for, and it fails loudly when the behaviour moves.
9. **Contract ids.** `C21-01` to `C21-15` are written as §2.10 numbers them, each red first on all three backends, and `check_spec_drift.py` moves §2.10 from `PLANNED_R31_INTERFACE_SECTIONS` to the implemented table and the three shapes and two functions from planned to held. The importer mapping is pinned in group `C12` as **`C12-69` to `C12-76`**, named in §0.6. A fix in §0.3 that needs its own pin gets the next free `C21` id, starting at `C21-16`, and is listed in §1 when it is written.

### §0.3 — The 14 findings from 8B-RUN §2.5, and the fix each starts from

R111 makes these the row's first task. Each proposed fix is a starting point, not settled. Every fix is reviewed by the loop together with the code.

| # | sev | finding (8B-RUN §2.5) | the fix this row starts from | pinned by |
|---|---|---|---|---|
| 1 | MAJOR | 2.10-11 step 2 has two definitions, and `_alias_holder`'s alias branch ignores kind | step 2 reads: *the live row of kind `k` in the namespace whose name or one of whose aliases has `word` as its `identity_key`*. The reader does its own kind-filtered scan and does not cite `_alias_holder` | `C21-11` |
| 2 | MAJOR | step 1's dead-end chain answers *retired* before step 2 runs | a dead end and a retired row with no successor fall through to step 2, and answer *retired* only at step 3 | `C21-11` |
| 3 | MAJOR | an empty-string description is unclassified | an empty or whitespace-only `description` reads as missing, everywhere a missing one does | `C21-03` |
| 4 | MAJOR | Q106 and 2.10-21 leave out R109's current hold | 2.10-21 and Q106 state today's hold (5 of 10 Legacy object types, all 6 edges and 5 actions `definition_missing`, and a shared property entry with no definition held too, §0.1 item 5) and what `like types` adds | text only, measured by the probe |
| 5 | MAJOR | the array `source_type` rule has two readings | *carries a non-empty `reducers`* | `C12-71` |
| 6 | MINOR | a capped successor walk has no answer | a walk cut off at `_IDENTITY_CHAIN_CAP` answers *unknown* | `C21-11` |
| 7 | MINOR | *undeclared* does not say whether it reads raw attributes or the view | read the view: *undeclared* only when the view's `base_type` is `None` with no `why_absent` entry | `C21-10` |
| 8 | MINOR | the reader takes a declaring `entry` that does not exist at `propose_type`, and `approve`'s recompute is unstated | the reader takes `(namespace, word, k)`; `approve` recomputes the warnings (R38) | `C21-10` |
| 9 | MINOR | `BASE_TYPES` names no module and the checker does not hold its values | name `ontoloche/properties.py`; the checker holds the ten values | `check_spec_drift.py` |
| 10 | MINOR | D14 *"routed to a build row"* names no row | say *unrouted*, as `DECISIONS-OPEN.md` already does; out of this row's scope (brief §2) | text only |
| 11 | MINOR | 2.10-8 cites §2.1 for a conversion §2.1 does not make | cite row 8a's name conversion (`foundry.convert_name`, 8A-RUN §0.2) | text only |
| 12 | MINOR | *"serialises one way"* leaves key spelling, nulls and struct scope open | wire form (the REST API's camelCase keys), null optionals omitted, the whole type object verbatim | `C12-71` |
| 13 | MINOR | §1.13 item 3 incomplete (`bonusHistory`'s struct-field reducer, `skillSetEmbedding`) | correct in this record's §1, since 8B-RUN is landed | text only |
| 14 | MINOR | §1.4's *"dangling reference"* is weak evidence | rescope: within the registry the reference dangles, and an importer reading `FooInterface` could recover the definition; this row's importer does not, and records it | text only |

**Also corrected in §2.10, from §0.1 item 5:** the `implementsInterfaces2` sentence, and the *landed not clean* banner, which comes off only if this row's loop ends clean on the §2.10 text.

### §0.4 — Predictions for each design test (brief §3)

#### UC2 CMS — the 23 columns, through real calls

The test proposes and approves, through `Registry` on all three backends, two value sets (`scope_severity_code`, `deficiency_corrected_status`), one shared property `ccn` (`base_type: str`), and the four entities with the declarations below. The shipped fixture's `primary_key`-only shape (`_support.py`) is left as it is and must still load.

| entity | slots | key | title |
|---|---|---|---|
| `facility` | `ccn` (shared), `provider_name`, `provider_address`, `city_town`, `state`, `zip_code` (`str`) | `["ccn"]` | `provider_name` |
| `survey` | `ccn` (shared), `survey_date` (`date`), `survey_type` (`str`) | `["ccn", "survey_date", "survey_type"]` | absent |
| `deficiency_tag` | `tag_number`, `deficiency_prefix`, `deficiency_category`, `deficiency_description` (`str`) | `["tag_number"]` | `deficiency_description` |
| `citation` | `scope_severity_code` (`str`, value set), `deficiency_corrected` (`str`, value set), `correction_date` (`date`), `inspection_cycle` (`int`), five `bool` flags | absent | absent |

**Predicted:** 21 columns have a home (22 slots, `ccn` used twice through one shared entry), 2 are `not_a_type` (`Location` `redundant_projection`, `Processing Date` `export_artefact`) unchanged. On `sqlite` and `postgres` every write returns **no warning**, and `entity_declaration` returns these slots with an empty `why_absent`. On `sqlite_minimal` each entity write warns `property_declaration_not_stored:properties` (and `:title_property` where declared), the view answers `why_absent == {"properties": "not_stored", "title_property": "not_stored"}` where both are declared, and `primary_key` comes back intact. The shipped `C13` tests pass unmodified. The 1.28% of rows whose correction date precedes the survey date are not caught (rule 2.10-13).

#### UC3 NYC — `status`, `latitude`, `longitude`

1. With `latitude` registered as `kind="property"` in `dot`, `resolve_type("latitude", kind="property")` answers `existing` at 1.0, and an entity slot `{"name": "latitude", "shared": "latitude"}` in `dot` is written with no warning.
2. In `dpr`, where no `latitude` entry exists, the same call answers `proposal` with `kind="property"`, and a `dpr` slot sharing `latitude` warns `property_reference_unregistered`, because the reader never crosses a namespace.
3. `status` stays three things: three local slots in `dpr`, `oti_311`, `dot`, each with a `value_set` in its own namespace, each found. A slot naming a value set that exists only in another namespace warns `property_reference_unregistered`.
4. `merge_types` across namespaces is still refused `cross_namespace_merge`. **No cross-namespace merge succeeds.**

#### UC1 Tenshen

**Predicted: confirmed, option B costs Tenshen nothing, now against code.** Tenshen's entries declare none of the reserved keys, so rule 2.10-1 leaves them unchanged. `test_c14_tenshen.py` is not modified and passes on all three backends. Its write path gains no warning (asserted by a new `C21-01` case over the C14 fixture). Tenshen's shipped adapter lives in the beacon repo and is not run here (8B-RUN §1.7 item 1), so the confirmation covers the shipped registry with the C14 fixture, not beacon's adapter.

#### Foundry — every property in row 8a's fixtures

1. **All 110 properties are accounted for**: each is a slot in an entity the import writes or would write, or a slot inside an entity held under R109 (and listed under that hold in the report), and every fact with no field is in the report's no-home list. **Zero dropped.**
2. `legacy`: `fooSpt` becomes the `kind="property"` entry `foo_spt` (`base_type: str`, definition `"A foo"`), written with no warning, and `Employee.fullName` a shared slot naming it, found, no warning.
3. `employee`: `Employee.fullName` is a shared slot naming `foo_spt`, which does not exist, so the non-dry import warns `property_reference_unregistered:fullName:foo_spt` and writes the slot (§0.1 item 4: Palantir's own dangling mapping).
4. `opaque` landings: 6 top-level in `employee`, 13 in `legacy`, each with a non-empty `source_type` and no warning. Arrays: `list` with an `item_type`; the 3 struct-typed arrays have `item_type: "dict"`.
5. Undescribed slots (83 across the five fixtures) are written with no `description` and **no warning** (rule 2.10-21 as today). The dry run counts them.
6. Every entity written passes rule 2.10-2's checks: **zero `import_refused:attributes_schema_violation`** on any of the five fixtures.
7. The `foundry_uc2_cms.json` import still yields the same 4 entity names and 3 edge family names as `C12-42`, now each entity with its one slot and key declared.

### §0.5 — The falsifiers

- **F1, the carrier (8B-RUN §0.3), now against code.** Falsified if any design test above needs a property fact that `attributes` cannot hold without a second home, or if any shipped contract test changes result because of the reserved keys. **Predicted: not falsified.**
- **F3, the reader.** Rule 2.10-11 as fixed is falsified if, over any design test's store, the reader answers *absent* or *retired* where `resolve_type(word, kind=k, namespace=ns)` answers `existing` at 1.0 for a row of kind `k` reachable by name, alias or a live successor chain, or answers *found* or *redirected* where no such row exists. **Predicted: not falsified**, and `C21-11` carries 8B-RUN §2.5 items 1, 2 and 6's three constructions as cases.

### §0.6 — Contract ids, named before they are written

`C21-01` to `C21-15` as §2.10's table numbers them. `C12-69` to `C12-76` for the importer:

| id | what it pins |
|---|---|
| C12-69 | shared property types import as `kind="property"` entries, before entities, with `definition_missing` held under R109 |
| C12-70 | object type properties map to local and shared slots, `primary_key` and `title_property` |
| C12-71 | §2.10's type table: every Foundry type, `source_type` serialisation (wire keys, nulls omitted, whole object), non-empty `reducers` |
| C12-72 | undescribed properties written with no description and no warning (rule 2.10-21 as today) |
| C12-73 | the narrowed R105 carry: facts with no slot field kept per property, nothing with a home duplicated |
| C12-74 | the dry-run `properties` report: all 110 fixture properties accounted for, the no-home list |
| C12-75 | the dangling `fooSpt` mapping warned `property_reference_unregistered`, written |
| C12-76 | zero `attributes_schema_violation` across the five fixtures, on every backend |

### §0.7 — The kill-row doors the new views and the property mapping open

Kill row at the start of this row: **twenty-three** trips. Row 8b's D1 to D14 are the doors `kind="property"` opened in the spec; their states are rules 2.10-15 to 2.10-22 and the probe (§0.1 item 1). This row opens these, listed before any code:

| # | door | predicted state |
|---|---|---|
| K1 | `import_foundry` writing `kind="property"` entries | **inherited**: it still writes through one `import_types` call per kind and writes no `aliases` or `successor`, so the identity guards stay unreachable through it. `check_merge_guard.py` Part A discovers **no** new identity writer |
| K2 | the two view functions | **not a door**: pure reads of one `TypeEntry` and `Capabilities`, no adapter call, no write |
| K3 | the rule 2.10-11 reader | **not a door**: read-only adapter calls; its answer only chooses a warning. A wrong answer is a Rule U defect, not a trip |
| K4 | the new validation at `propose_type`, `approve`, `import_types` | **narrows**: it adds refusals and no write path. A refusal cannot merge a predicate |
| K5 | a `kind="property"` entry carrying `predicates=` | **inherited**: rule 2.10-22; every property collapse toward a predicate is refused (2.10-15) |
| K6 | two Foundry shared property types converting to one name | **inherited**: R110 holds both, as for every other kind |
| K7 | re-importing a Foundry ontology over active entries now carrying declarations | **open and reserved**: rule 2.10-20, Q103; today's replace-whole-`attributes` behaviour, pinned by the probe |
| K8 | D14 through `import_foundry` | **unreachable**: it writes no `aliases` |

**Predicted: zero new kill-row trips.** No door above can merge a capability predicate.

### §0.8 — What goes to the founder

**Predicted: nothing.** Rules 2.10-17 to 2.10-21 stay reserved under Q103 to Q106 and are built as today's behaviour (§0.2 item 8). If the build meets a choice that makes the code refuse or hold something no ruling covers, it goes into `DECISIONS-OPEN.md` as a new item and the row ends `BLOCKED ON FOUNDER`. Every other choice (report fields, tests, process, rounds) is this row's and is recorded here with its reason.

### §0.9 — The stopping rule and the round cap

Row 6j's adopted criterion (`6J-RUN.md` §3.9, §5 item 10, ruled `Q5`): *"The loop ends when a full round finds no in-scope code MAJOR reachable by a shape a contributor would plausibly write — measured as: does the shape, or anything structurally like it, appear anywhere in the live suite?"* For the §2.10 text this row edits, row 8b's adaptation applies as well: a spec MAJOR counts when it is reachable using only calls and shapes `INTERFACE.md` prints, over UC1, UC2, UC3 or the Foundry fixtures. Bound, from `6I-RUN.md` §6.6 and `6J-RUN.md` §4.4: a round that produces a MAJOR or BLOCKING fix is followed by a full round that sees it, the last round sees the final text and code, and nothing reviewed is edited while a lens is running.

**Cap: five rounds.** Each round runs three fresh lenses: the build implementer (code against §2.10), the door adversary (kill-row doors, K1 to K8 and D1 to D14), and the use-case and Foundry fidelity reviewer. **At the cap:** if round 5 still finds a reachable in-scope MAJOR, the row fixes it and runs one confirming round 6, row 8a's item 26 precedent. If round 6 finds one, the row lands not clean with the finding recorded here and in `STATUS.md`, and it goes to the founder only if fixing it would decide a refusal. *Reason:* the founder said on 2026-11-16 and 2026-11-17 that round counts are process and this row's to decide, and stopping to ask at the cap is the step he called unnecessary.

### §0.10 — The commands this row will run, named before they are run

```
py docs/tools/properties_baseline_probe.py [--assert]
py tools/unasync.py
py -m pytest --pyargs ontoloche.contract ontoloche.aio.contract     # three legs, OO_POSTGRES_DSN set
py docs/tools/check_links.py
py docs/tools/check_spec_drift.py
py docs/tools/check_merge_guard.py
py docs/tools/check_capability_matrix.py
py docs/tools/check_skip_census.py
```

`OO_POSTGRES_DSN=postgresql://postgres:openontology@localhost:55432/open_ontology` (container `oo-pg`). The full suite takes about 23 minutes (8A-RUN §1.6), so it runs in the background.

---

## §1 — RESULTS, scored against §0

Written after the build and before the adversarial loop. Commits `32427f6` (the §0.3 text fixes), `c291657` (C21 red), `fe29ede` (`properties.py`), `dd712ff` (the doors, the reader, the importer), `d620b99` (the spec and checker held as built, `PACKAGE.md` §6.2) and `48f0bd1` (the probe's `--assert`).

### §1.1 — The suite and the gates

**The full suite passes on all three legs** **[Observed]** at `d620b99`, `OO_POSTGRES_DSN` set: `py -m pytest` ran 2404 passed, 660 skipped, 0 failed in 24 min 17 s, sync and async halves. Coverage per leg (ruling R12): `sqlite` and `postgres` **472 ids exercised** each with 1 not exercisable, `sqlite_minimal` **150** with 323 not exercisable, plus 5 backend-independent ids run once (`C12-71` among them). From the 453 ids `PACKAGE.md` §6.2 enumerated at `147d871` (§0.1 item 3's 448 is the per-leg *exercised* count, not the enumeration, corrected in round 2): +25 ids (`C12-69` to `C12-76`, `C21-01` to `C21-17`), so `PACKAGE.md` §6.2 now enumerates **478** in twenty-one groups.

**The five gates exit 0** **[Observed]** at `48f0bd1`: `check_links`, `check_spec_drift` (§5.4 at 45, §5.12 at 33, §2.10's three shapes, two view signatures and ten `BASE_TYPES` held against `ontoloche/properties.py`), `check_merge_guard`, `check_capability_matrix` (every optional capability declined alone conforms) and `check_skip_census`. `properties_baseline_probe.py --assert` exits 0 with all 19 reserved-rule lines at their recorded values, and exits 1 when one is changed (checked by editing one recorded value in memory).

### §1.2 — The design tests

| test | prediction | result |
|---|---|---|
| UC2 | 21 columns with a home, 22 slots, `ccn` shared once; `Location` and `Processing Date` still `not_a_type` | **hit** **[Observed]** `C21-16` on all three legs |
| UC2 | `sqlite` and `postgres`: no warning, empty `why_absent` | **hit** `C21-16` |
| UC2 | `sqlite_minimal`: `property_declaration_not_stored:properties` (and `:title_property` where declared), `primary_key` intact | **hit** `C21-16`, and the probe's D9 line prints `{'primary_key': ['ccn']}` with both warnings |
| UC2 | `C13` passes unmodified | **hit** `test_c13_cms.py` and `_support.py` unchanged since `147d871` (`git diff --stat` is empty), suite green |
| UC3 | items 1 to 4: `latitude` found in `dot`, proposed and `unregistered` in `dpr`, three `status` value sets stay three, no cross-namespace merge | **hit**, all four, `C21-17` |
| UC1 | Tenshen-shaped entries unchanged and unwarned; `C14` unmodified | **hit** `C21-01`'s Tenshen case; `test_c14_tenshen.py` unchanged. Beacon's adapter not run, as §0.4 said |
| Foundry 1 | all 110 properties accounted for, zero dropped | **hit** **[Observed]** dry-run `properties` report: `seen` 110, `slots` 110 (19, 75, 4, 2, 10), held entities' slots included; every other fact in `no_home` (`C12-74`) |
| Foundry 2 | `legacy`: `foo_spt` written clean, `fullName` shared and found | **hit** `C12-69`, `C12-75` |
| Foundry 3 | `employee`: `property_reference_unregistered:fullName:foo_spt`, written | **hit** `C12-75` |
| Foundry 4 | `opaque`: 6 top-level in `employee`, 13 in `legacy`, struct arrays `item_type: "dict"` (3) | **hit**, with one landing §0 did not predict: the report counts `employee` 6 and `legacy` **16**, the extra 3 being `object_type_with_all_property_types`' `attachmentArray`, `geoPointArray` and `geoShapeArray` **[Observed]**, arrays whose item type is opaque, which land `base_type: "list"`, `item_type: "opaque"` with the whole array type in `source_type` (`C12-71`) |
| Foundry 5 | 83 undescribed slots, written, no warning | **miss on the count, hit on the behaviour.** 83 is the number of *properties* with no description. Two of them (`fullName`, in `employee` and `legacy`) are **shared** slots, which by rule 2.10-3 carry no `description` at all, so **81** slots are undescribed (5, 60, 4, 2, 10). All written, no warning (`C12-72`) |
| Foundry 6 | zero `attributes_schema_violation` on the five fixtures | **hit** `C12-76`, all three legs |
| Foundry 7 | `foundry_uc2_cms.json`: the same 4 entities, each with its slot and key | **hit** `C12-76` |

**Score: 18 predictions, 17 hits, 1 miss (the undescribed count), 0 untested.** The miss is §0's arithmetic, not the build: §0.1 item 4 counted properties and §0.4 called them slots.

### §1.3 — Falsifiers

- **F1, the carrier: not falsified.** Every design test above holds its facts in `attributes` under the reserved keys or the narrowed carry, and no shipped contract test changed result because of the reserved keys. The three `C12` tests that changed (below) changed because the importer mapping changed, which §0.2 item 5 and 6 announced.
- **F3, the reader: not falsified** over the design-test stores. `C21-11` carries 8B-RUN §2.5 items 1, 2 and 6 as cases: an alias held by another kind is not a property, a dead end falls through to a live alias holder (the answer `resolve_type` gives at 1.0), and a capped chain answers *unknown*.

### §1.4 — Kill row

**Predicted zero new trips; zero so far.** `check_merge_guard.py` Part A **[Observed]** finds no new writer of `successor` or `aliases` (K1, K8), and the doors K2 to K6 are as §0.7 stated: the views and the reader write nothing, and the new validation only adds refusals. K7 stays open and reserved (Q103), pinned by the probe's D7 and D7b lines. The adversarial loop (§2) is the test of this, not this paragraph.

### §1.5 — Deviations from §0, each with its reason

1. **The rule 2.10-11 reader lives in `registry.py`** (`Registry._property_reference`), not in `properties.py` as §0.2 item 1 said. *Reason:* it needs `get_type`, the successor walk under `_IDENTITY_CHAIN_CAP` and the kind-filtered `_active_page` scan, all of which are adapter reads on `Registry`. Keeping it there leaves `properties.py` pure and importing nothing from the registry, which was item 1's actual purpose.
2. **`properties.py` was written before the `C21` tests ran red against it.** The tests were committed first (`c291657`) and red was shown by running them with the module moved away, not by the commit order alone. Recorded so nobody reads the commit order as stronger evidence than it is.
3. **`import_foundry` makes one mixed `import_types` call, ordered by kind** (predicate, property, entity, edge, action), not one call per kind as §0.2 item 5 said. *Reason:* the shipped importer already made one call (§0.2 item 5 described it wrongly), and `import_types` writes rows in order, so a shared property is still written before the entity that names it, which is all rule 2.10-10's import-order note needs.
4. **Two `no_home` reasons §0.2 item 7 did not list:** `slot_name_invalid` (a property apiName that is not a legal slot name under rule 2.10-4, carried whole and never a slot) and `shared_word_invalid` (a `sharedPropertyTypeMapping` target that does not convert to a legal word). Neither fires on the five fixtures. *Reason:* without them such a property would be dropped, which §0.4 Foundry 1 forbids.
5. **`C12-34`, `C12-35` and `C12-36` were changed deliberately.** They pinned the old R105 carry (properties verbatim in `foundry_properties`) and `not_imported` counting `sharedPropertyTypes`. §0.2 items 5 and 6 replaced both, so the old assertions were wrong by design. They now pin the narrowed carry and the counts without shared property types.
6. **The view returns tuples, and §2.10 now prints `tuple[...]`.** *Reason:* the dataclasses are frozen, and a list field would make a frozen view mutable and unhashable.
7. **`check_spec_drift.py`'s number words stopped at thirty-four**, so §5.4's count had gone unchecked since it passed that number. Extended to fifty, which is how the 45 is now checked. A pre-existing gap, found because this row moved the count.
8. **The `C21` tests' `retire` calls pass `force=True`.** *Reason:* with `indexes_membership` declined, `retire` refuses `no_consumer_evidence` unforced, and `check_capability_matrix.py` showed that configuration failing two `C21` ids. The guard is not those tests' subject (`PACKAGE.md` §8b.5), and `C9`'s own tests force it the same way.
9. **The probe's D7 and D9 seeds changed.** The old seeds declared a slot with no `base_type`, which rule 2.10-3 now refuses, so D7 had silently stopped measuring rule 2.10-20. Both now seed legal declarations.

### §1.6 — Findings 13 and 14 of 8B-RUN §2.5, corrected here

8B-RUN is landed, so these corrections live in this record (§0.3).

- **Finding 13.** 8B-RUN §1.13 item 3 is incomplete. **[Observed]** in `foundry_faux_employee.json`, `Employee.bonusHistory` is an array of `struct` whose `reducers` is `[{"direction": "DESCENDING_NULLS_LAST", "field": "year"}]`, a reducer on a struct field, so array reducers appear on three properties, not two. And the fixture report's *"`vector.embeddingModel` never exercised"* is false: `Employee.skillSetEmbedding` is a `vector` with `embeddingModel: {"type": "lms", "value": "OPENAI_TEXT_EMBEDDING_ADA_002"}`. Both land as §2.10's table says, `bonusHistory` as `list` of `dict` with the reducer kept in `source_type`, and `skillSetEmbedding` as `opaque` with the whole type object in `source_type` (`C12-71`).
- **Finding 14.** 8B-RUN §1.4 called `fooSpt` a dangling reference and used it as the strongest evidence for warn-not-refuse. Rescoped: **within the registry the reference dangles**, because `employee` defines no shared property type `fooSpt`, but `FooInterface.properties.fooSpt` in the same document defines it in full, so an importer reading interface property contracts could recover it. This row's importer does not (an interface's property contract is carried, reason `interface_property_contract`), so the import warns `property_reference_unregistered`. The warn-not-refuse case stands on Palantir's fixture being importable at all, not on the definition being unrecoverable.

### §1.7 — What went to the founder

**Nothing.** No choice in the build decided what the registry refuses or holds beyond §2.10's non-reserved rules. Rules 2.10-17 to 2.10-21 are today's behaviour, pinned by the probe.

## §2 — The adversarial loop

Stopping rule and cap as §0.9: three fresh lenses per round (A, the build implementer; B, the door adversary; C, the use-case and Foundry fidelity reviewer), read-only, each MAJOR backed by a reproduction the lens ran. Nothing reviewed was edited while a lens ran.

### §2.1 — Round 1, at `464579a`

**0 BLOCKING, 0 MAJOR, 17 MINOR.** Every K-door state in §0.7 survived real calls (lens B). `check_merge_guard.py` and `properties_baseline_probe.py --assert` exit 0 (lens B), the async mirror is current (lens A, `unasync.py --check`), and every Foundry number in §0.1 and §1.2 recomputed true except the one in C2 (lens C). Lens C also confirmed against `foundry_sdk` 1.111.0 that all 22 `ObjectPropertyType` variants are mapped and that `sharedPropertyTypeMapping` is read in its declared direction, SPT apiName to property apiName.

| # | lens | finding | disposition |
|---|---|---|---|
| A1 | A | the reader's successor walk stopped one hop short of `resolve_type`'s (16 vs 1 + 16), so a 17-hop chain read *unknown* where `resolve_type` answered the live end | **fixed**: the same bound as `resolve_type` |
| A2 | A | a page-capped scan holding a match answered *redirected* from a partial page, against rule 2.10-11's *"could not finish … unknown"* | **fixed**: `why` is checked before the holders |
| A3 | A | a shared slot carrying a blank `description` was refused, though rule 2.10-3 makes a blank description a missing one at every door | **fixed**, pinned by a new `C21-03` case at `propose_type` and `import_types` |
| A4 | A | on a `kind="property"` entry, `detail.key` named `base_type` for a breach of `item_type`, `source_type` or `value_set` | **fixed**, pinned in `C21-09` |
| A5 | A | rule 2.10-1's *"unchanged in every respect"* contradicted 2.10-9's refusal of `required` on a property entry | **fixed**: 2.10-1 names the exception |
| B1 | B | a shared property type the plan **holds** (R109, R110) still binds an entity's slot to a live, unrelated local `kind="property"` row of the same word, with no warning and an empty `unresolved_shared` | **recorded, not fixed.** It is row 8a's round-3 *"the store first"* rule in `_foundry_unresolved`, inherited unchanged and identical for interfaces. That rule exists because a re-run without `definitions=` holds a standing type while its row stays live, which is the same thing and must resolve. Telling *the same thing re-imported* from *an unrelated local row* needs a provenance comparison this row does not build. No guard is bypassed and both holds stand |
| B2 | B | K6 (R110 holds both colliding shared property types) had no pin | **fixed**: `C12-77` |
| B3 | B | §0.7 K7 names the `attributes` replacement only; an active re-import also drops the property's predicate membership out from under a consumer's gate, reported only in `detail.replaces.predicates_dropped` | **recorded**: K7 is reserved (rule 2.10-20, Q103), and this is §2.5's inherited re-import behaviour, which Q103 covers. Stated here so Q103's answer accounts for it |
| B4 | B | a word held under two kinds also makes `resolve_type` with no `kind` raise `AmbiguousKind`, which 2.10-15 did not list; a Foundry interface and shared property type converting to one word both land, one per kind, with no warning | **fixed** in 2.10-15's text. The safe direction: nothing collapses |
| B5 | B | `check_merge_guard.py` Part A parses `ontoloche/registry.py` only | **fixed**: its scope and why the async mirror and `foundry.py` cannot hide a writer are stated in the tool. Lens B checked by hand that neither adds one |
| C1 | C | `C21-17` never writes the `dpr` slot sharing `latitude` or a slot whose value set exists only in another namespace (§0.4 UC3 items 2 and 3), so §1.2 cited a test that did not observe them | **fixed**: both writes added to `C21-17` |
| C2 | C | §0.1 item 4 and §1.2 count **3** struct arrays; there are **4** struct-array slots, because `Employee.bonusHistory` is in both `employee` and `legacy` (1 and 3) | **corrected here**. §0 is pre-registration and is left as committed, and the Foundry 4 row in §1.2 is scored on it: the prediction counted distinct properties, the build lands 4 slots |
| C3 | C | §2.5a's report paragraph omits each entity's `name`, `no_home` entries on a shared property type or interface, and `property: null` | **fixed** in §2.5a |
| C4 | C | a `primaryKey` or `titleProperty` naming no slot was carried under `$primaryKey` / `$titleProperty` undocumented, and counted in `carried_properties` | **fixed**: documented in §2.5a, and no longer counted |
| C5 | C | §2.10's type table said nothing about an array of arrays | **fixed**: one sentence in the `array` row |
| C6 | C | rule 2.10-21 still said 83 where §1.2 corrected the slot count to 81 | **fixed** |
| C7 | C | the carry keeps `null`s verbatim while `source_type` omits them | **fixed in the text**: §2.5a says the carry is verbatim, nulls included. Nothing is lost, and `no_home` already skips null values |

At `167da18` the full suite ran **2416 passed, 660 skipped, 0 failed** (24 min 27 s; `sqlite` and `postgres` 473 ids exercised each, `sqlite_minimal` 151), and the five gates and `properties_baseline_probe.py --assert` exited 0 **[Observed]**.

### §2.2 — Round 2, at `167da18`

**0 BLOCKING, 2 MAJOR, 10 MINOR.** Lens A (rules 2.10-1 to 2.10-16 and 2.10-22 on three legs, `C21` 83 passed, 7 skipped) and lens B (every K-door state, `check_merge_guard.py` and the probe `--assert` at 0, B1 and B3 confirmed honest) found no MAJOR. Lens C found two. An independent re-implementation of §2.10's table from its text matched the importer on all 110 properties, and every §1.2 number recomputed true. The kill row stays at twenty-three. The round fails the stopping rule, so round 3 runs.

| # | lens | sev | finding | disposition |
|---|---|---|---|---|
| C2-1 | C | **MAJOR** | `unresolved_shared` resolved a shared slot by an exact `get_type`, row 8a's interface logic, while the entity's own rule 2.10-10 warning used rule 2.10-11's reader. A word reaching a live property by alias or by successor was reported `not_in_document` or `retired` beside a warning saying *redirected*, in one call | **fixed**: `_foundry_unresolved` asks the 2.10-11 reader for a shared slot. *found* and *redirected* resolve, *retired* and *unknown* are reported as the reader answers, and only an absent word takes the plan's reason. Pinned by a new `C12-75` case (alias and successor) and stated in §2.5a |
| C2-2 | C | **MAJOR** | §1.1 said *"from 448, +25 ids, now 478"*. 448 + 25 = 473. The 448 is the per-leg exercised count, the enumeration was 453 | **fixed** in §1.1. §0.1 item 3's *"claims 448 ids"* is pre-registration and stays as committed. It names the exercised count |
| C2-3 | C | MINOR | a shared property type's own facts with no field (`typeClasses`, `valueTypeApiName`, `valueFormatting`) were carried but not listed in `no_home` | **fixed**: listed as `no_slot_field:<key>` with `property: null`, pinned by a new `C12-74` case |
| C2-4 | C | MINOR | §2.5a's report paragraph did not name `entities`, put `no_home` per object type, and did not say `opaque` and `undescribed` count local slots | **fixed** in §2.5a |
| C2-5 | C | MINOR | §2.5a's unresolved paragraph showed no `shared` label | **fixed** |
| C2-6 | C | MINOR | a blank or null `displayName` lands nowhere, unstated | **fixed** in §2.5a |
| B2-1 | B | MINOR | rule 2.10-11 said the walk is capped at 16 hops. After A1 it is the first successor plus 16, as `resolve_type` | **fixed** in the rule and the reader's docstring |
| B2-2 | B | MINOR | a document holding only `sharedPropertyTypes` raised *"not an OntologyFullMetadata document"*, failing closed | **fixed**: `sharedPropertyTypes` counts toward `_TYPE_MAPS`, pinned by the new `C12-74` case |
| A2-1 | A | MINOR | on a backend projecting `display_name` but not `base_type`, the view overwrote `not_stored` with `breaches:2.10-9`, a false breach of data valid when written | **fixed**: a `kind="property"` entry with any key `not_stored` is not judged against 2.10-6 to 2.10-9. Pinned in `C21-14` and stated in the view's paragraph |
| A2-2 | A | MINOR | rule 2.10-10 printed `why_absent["base_type"] == "breaches:2.10-9"` as the breach test, but a breach of 2.10-6, -7 or -8 names its own rule | **fixed in the text**: the value starts `breaches:` and names the rule, as the view's paragraph already said. The registry's own test (`not view.why_absent`) was right |
| A2-3 | A | MINOR | on a backend that drops `properties`, reference warnings are still sent for references not kept | **fixed in the text, not the code.** Suppressing them was tried and turned five `sqlite_minimal` cases red per mirror, and would have made the Foundry report and the entity's warning disagree on that leg, the defect C2-1 just closed. The warning describes what the caller declared, and `not_stored` says apart that it was not kept. Rule 2.10-10 now says so, pinned by a `C21-14` case |
| A2-4 | A | MINOR | with slots declared, a duplicate `primary_key` slot was reported as rule 2.10-1 | **fixed**: rule 2.10-5 when `properties` is present, 2.10-1 otherwise. Pinned by a `C21-05` case |

Lens A's postgres probe left one throwaway schema `probe_<8 hex>` in the shared `open_ontology` database. It is not dropped, under the no-delete rule. It holds probe rows only.

### §2.3 — Round 3, at `40bf5f2`

**0 BLOCKING, 2 MAJOR, 5 MINOR.** Lens B found no MAJOR, `check_merge_guard.py` and the probe `--assert` exit 0, and the kill row stays at twenty-three. Lens C confirmed round 2's C2-1 fix: `unresolved_shared` agrees with the entity's warning in every case it ran (found, redirected by alias and by successor, retired, absent and held, absent and refused, absent and not in the document, dry and real), and every §1.2 number and the §6.2 id counts recompute (453, 478, 479). The round fails the stopping rule, so round 4 runs.

The full suite started at `40bf5f2` was stopped at 27%, unread, once round 3 had a MAJOR, so its result never mixed with edited files. §1.1's run at `d620b99` and §2.1's at `167da18` stand, and the suite and gates are run again at round 3's fix commit (lens C finding 4).

| # | lens | sev | finding | disposition |
|---|---|---|---|---|
| A3-1 | A | **MAJOR** | with `properties` a well-formed list, a `title_property` or `primary_key` holding a list or dict made the validator raise `TypeError`, since rule 2.10-5's membership check ran over the raw attributes and was filtered after. `propose_type` and `approve` raised, and `import_types` aborted the batch after earlier rows were written, breaking *"one bad row never fails the whole import"*. Reproduced on all three legs | **fixed**: a key whose shape breached rule 2.10-1 is removed before the membership check. Pinned by a `C21-05` case at `propose_type` and in an `import_types` batch whose good row still comes back written |
| C3-1 | C | **MAJOR** | round 2's B2-2 fixed the code only. §2.5a still said `ValueError` when none of the four maps is present, so a document of shared property types alone, which now imports and writes, contradicted the text. §2.2 called B2-2 *fixed* | **fixed** in §2.5a. §2.2 stays as committed and this row corrects it |
| A3-2 | A | MINOR | round 2's A2-4 test read any non-null `properties` as present, so a non-list `properties` with a duplicate key was labelled 2.10-5 | **fixed**: `isinstance(..., list)`, pinned in the new `C21-05` case |
| B3-1 | B | MINOR | round 2's shared-slot branch dropped the old `dry_run and deprecated` check, so a dry run over a `DEPRECATED` shared property type not yet stored reported the slot resolved while the real run reported `retired` | **fixed**: the check is restored in that branch. Pinned by a `C12-75` dry-and-real case |
| C3-2 | C | MINOR | a shared property type's whitespace `displayName` was written as `display_name`, though a slot's lands nowhere | **fixed**: the same blank test. Pinned in the same `C12-75` case and stated in §2.5a |
| C3-3 | C | MINOR | neither table said a missing or unlisted `dataType` lands `opaque` | **fixed**: one sentence in §2.5a. `source_type` is the wire form, `{}` when absent **[Observed]** `land(None)`, `land({"type": "zzz"})` |
| C3-4 | C | MINOR | §2.2 recorded no full-suite run after round 2's code fixes | **taken**: see the paragraph above |

Lens B also noted B1 (§2.1) now covers the alias case: an unrelated live property aliased to a held shared property type's word resolves the slot, and the entity does warn `property_reference_redirected`. Recorded, no worse than B1. Lens A left one Postgres schema `oo_r3a_aa4f7ec0`, not dropped under the no-delete rule.

**Next:** round 4 runs on the commit that applies these fixes.
