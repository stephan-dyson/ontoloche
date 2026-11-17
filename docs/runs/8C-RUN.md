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
