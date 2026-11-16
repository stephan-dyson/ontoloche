# 8A-RUN — roadmap row 8a: the Foundry metadata importer

**Status:** **landed** on `row-8a` (local, not pushed). The founder ruled `round 6` on item 26 (2026-11-15) and `fix and land` on item 27 (2026-11-16): round 6's one MAJOR is fixed as `C12-68`, with no further review round, by that ruling. **Opened** by the supervising session on 2026-11-12 under the founder's instruction *"keep the project moving forward"*. **Brief:** [`handoffs/2026-09-22-row-8a-foundry-importer-brief.md`](../handoffs/2026-09-22-row-8a-foundry-importer-brief.md). **Rulings in force:** [R105–R107](../decisions/2026-09-22-founder-rulings-R105-R107.md), [R108](../decisions/2026-09-22-founder-ruling-R108.md), and [R109–R110](../decisions/2026-11-12-founder-rulings-R109-R110.md), which this row asked for before §0 was written. **Evidence:** [`findings/FOUNDRY-PARITY.md`](../findings/FOUNDRY-PARITY.md).

**Worktree:** `row-8a`, cut from `main` at `2e94fe5`. Row 8b runs on `main` at the same time. Properties follow R105's interim `carry` and this row does not anticipate 8b's spec.

Claims are tagged **[Observed]** (seen in this session), **[Inferred]** or **[Assumed]**.

---

## 0. Pre-registration — **written and committed before any importer code**

This section is committed on its own, ahead of `ontoloche/foundry.py`, `Registry.import_foundry` and every test it names, so the predictions are checkable in `git log` rather than asserted.

### 0.1 What was observed before this section was written

These are facts about the inputs, not predictions, and they shaped the predictions below.

1. **The generated fixtures exist.** **[Observed]** `@osdk/faux@0.66.0` from npm, with the test ontologies in `packages/shared.test/src` of https://github.com/palantir/osdk-ts at commit `ee09000147c05d761b893582b04514cbbdf124a4` (both Apache 2.0), produced two `OntologyFullMetadata` documents. `addEmployeeOntology` gives **`employee`** (2 object types, 1 interface, 0 actions). `LegacyFauxFoundry`'s default ontology gives **`legacy`** (10 object types, 3 interfaces, 16 action types, 21 query types, 1 shared property type, 0 value types). The workspace `packages/faux/package.json` at that commit says `0.66.0`, the same version npm serves.
2. **Palantir's own fixtures do not pass Palantir's own SDK model.** **[Observed]** `foundry-platform-sdk==1.111.0`'s `OntologyFullMetadata.model_validate` rejects `employee` with 35 errors and `legacy` with 124. Every `employee` error, and 120 of the `legacy` errors, is a `string_pattern_mismatch` on a `rid` or `linkTypeRid` placeholder (`"rid"`, `"rid.link-type.327"`, `"ri.struct.bio"`). `legacy` adds 3 `missing` `displayName` errors and 1 `union_tag_invalid` on a deliberate `{"type": "unsupportedType"}` data type. So "the SDK parses it" cannot be the shape check as the brief wrote it. The check this row uses is stated in §0.5.
3. **The published API has no `EXAMPLE` status.** **[Observed]** The SDK's `ReleaseStatus` is `Literal['ACTIVE', 'ENDORSED', 'EXPERIMENTAL', 'DEPRECATED']` (`foundry_sdk.v2.core.models`). The brief's defect 2 came from `FOUNDRY-PARITY.md` §2's probe, which fed `status="EXAMPLE"` to `import_types` directly. **[Inferred]** How a type the UI calls *Example* appears in `fullMetadata` is unknown. It may be one of the four values. The fix is still made at `import_types`, where the defect was observed, and `import_foundry` holds any status outside the four rather than guessing.
4. **Link sides carry no description.** **[Observed]** `LinkTypeSideV2`'s fields are `api_name`, `display_name`, `status`, `object_type_api_name`, `cardinality`, `foreign_key_property_api_name` and `link_type_rid`. So under R109 every imported link type is held for a definition unless the caller supplies one.
5. **Neither generated fixture has action logic rules.** **[Observed]** `actionTypesFullMetadata` is `{}` in both. Each action type carries only `operations` (`createObject`, `modifyObject`, `createInterfaceObject`, `deleteInterfaceObject`). No `createLink` or `deleteLink` appears.
6. **UC1 has no Foundry-shaped input.** **[Observed]** `grep -i "foundry\|palantir"` over `docs/USE-CASES.md` and `ontoloche/contract/test_c14_tenshen.py` returns nothing.
7. **The postgres leg had no database.** **[Observed]** At the start of the row `docker ps -a` was empty and `check_merge_guard.py` exited 1 on the untouched branch with `connection timeout expired` on port 55432. The founder approved creating `oo-pg` (`postgres:16`, port 55432). Every gate result in this record is from after that.

### 0.2 The mapping, fixed before the predictions use it

`import_foundry(full_metadata, *, namespace="default", dry_run=True, names=None, definitions=None, imported_by="import:foundry")`. The parsing lives in a new pure module, `ontoloche/foundry.py`. The registry method plans, runs `resolve_type` for look-alikes and, only when `dry_run=False`, hands every planned row to **one** `import_types` call.

| Foundry | ontoloche | Notes |
|---|---|---|
| interface type | `kind="predicate"`, definition = `description` | property contract, links and `extendsInterfaces` carried in `attributes["foundry_interface"]` |
| object type | `kind="entity"`, definition = `description`, predicates = converted `implementsInterfaces` | `visibility` in `attributes`. Properties, `primaryKey` and `titleProperty` carried verbatim in `attributes["foundry_properties"]` with `"validated": false` (R105 `carry`). Every other object type key carried in `attributes["foundry_object_type"]` |
| link type | `kind="edge"`, `level="instance"`, `symmetric=False`, `endpoint_kinds` entity to entity | both sides paired by `linkTypeRid`. Forward side: the one with `foreignKeyPropertyApiName`, else the first by `(objectType apiName, side apiName)`. Name = converted forward side `apiName`, `inverse_label` = converted other side, `None` when unpaired. Cardinality and both sides carried in `attributes["foundry_link"]` |
| action type | `kind="action"`, definition = `description` | **declares none of `ACTIONS.md` §2.2's eight keys** (rule 2.2-1: legal, not yet usable). Foundry gives no reversibility or approval mode, and Rule U forbids guessing them. Parameters and operations carried in `attributes["foundry_action"]`. The `Effect.op` each operation *would* map to is reported, not declared (§0.4, Q4) |
| query types, shared property types, value types | not imported | counted in the report. Value types are out of this row's scope (§0.6) |
| `apiName`, `rid` | `provenance.imported_from` | as `INTERFACE.md` §2.5. **The `apiName` is not written into `aliases`.** An alias is an identity claim that runs every guard at the alias door, and the Foundry name is recoverable from provenance |
| `status` ACTIVE / EXPERIMENTAL / DEPRECATED | as §2.5 | unchanged |
| `status` ENDORSED | `active` plus predicate `endorsed` | defect 1 |
| `status` EXAMPLE, or any other value | held, not written | defect 2 |

**Name conversion.** Insert `_` before an upper-case letter that follows a lower-case letter or digit, and before the last capital of an acronym run followed by a lower-case letter. Lower-case. Replace each run of characters outside `[a-z0-9]` with one `_`. Strip leading and trailing `_`. A result that does not match `^[a-z][a-z0-9_]{0,63}$` is held as `name_invalid`. A `names={apiName: name}` entry replaces the conversion, and is checked the same way. Links are keyed in both maps as `"<objectType apiName>.<link side apiName>"` of the forward side.

**Holds happen before `import_types` and write nothing.** Four reasons: `definition_missing` (R109), `name_collision_after_conversion` (R110, every member of the collision held), `name_invalid`, and `status_not_imported`. Order: predicates, entities, edges, actions, so a predicate exists before the entity declaring it.

### 0.3 Predicted dry-run counts — empty store, no `names`, no `definitions`

| | `employee` | `legacy` |
|---|---|---|
| predicates would write | 1 (`foo_interface`) | 3 (`bar_interface`, `complex_implementation_interface`, `foo_interface`) |
| entities would write | 2 (`employee`, `office`) | 5 (`employee`, `office`, `object_type_with_all_property_types`, `object_with_timestamp_primary_key`, `complex_implementation_object`) |
| edge families planned | 3 (`lead`, `office_link`, `visited_offices`) | 6 (those 3, plus `linked_object_type`, `todos`, `rp`) |
| actions would write | 0 | 11 |
| **would write, total** | **3** | **19** |
| held `definition_missing` | 3 (all 3 edges) | 16 (5 entities: `equipment`, `todo`, `task`, `person`, `bgao_nfl_player`; all 6 edges; 5 actions: `delete_bar_interface`, `action_takes_decimal`, `add_geoshape`, `delete_foo_interface`, `create_foo_interface`) |
| held `name_collision_after_conversion` | 0 | 0 |
| held `name_invalid` | 0 | 0 |
| held `status_not_imported` | 0 | 0 |
| unpaired link sides (no inverse) | 1 (`visited_offices`) | 4 (`visited_offices`, `linked_object_type`, `todos`, `rp`) |
| properties carried | 19 | 75 |
| not imported | 0 query, 0 shared property, 0 value types | 21 query, 1 shared property, 0 value types |
| operations reported as `host_state` / `add_edge` / `retract_edge` | 0 / 0 / 0 | 6 / 0 / 0 |
| look-alikes reported by `resolve_type` | 0 | 0 |
| **adapter write primitives called** | **0** | **0** |

The `legacy` operations figure counts operation entries on the 11 actions that would be written: `promoteEmployee` 1, `promoteEmployeeObject` 1, `createOffice` 1, `moveOffice` 1 and `createOfficeAndEmployee` 2. The six other written actions have no operations, and the three actions carrying interface operations are held for a definition.

**A non-dry import of either fixture on an empty store** writes exactly the "would write" set, with no `import_refused` on any written row, and the predicates carry `predicate_requires_review`.

### 0.4 The four defect fixes, each with its falsifier

Each is fixed at `import_types`, where `FOUNDRY-PARITY.md` §2 observed it, so both doors get it. Each is falsified on **any** leg (sqlite, sqlite-minimal, postgres) and in the async mirror.

1. **`ENDORSED` becomes `active` plus predicate `endorsed`.** *Falsified if* an `endorsed` row is stored with any status other than `active`, or without `endorsed` in its predicates, or `list_types(predicate="endorsed")` omits it on a backend with `indexes_membership`.
2. **`EXAMPLE`, and any status outside `active`/`endorsed`/`experimental`/`deprecated`, is not written and is reported.** *Falsified if* `get_type` finds such a row after the call, or its returned entry lacks `import_refused:foundry_example` (for `example`) or `import_refused:status_unknown` (for anything else). A row with **no** status still imports as `active`, which is today's documented behaviour (`C12-01`'s fixture relies on it). *Also falsified if* that changes.
3. **A name outside `^[a-z][a-z0-9_]{0,63}$` is refused with `import_refused:name_invalid` and never raises.** *Falsified if* `import_types` raises any exception on such a name on any backend, if the row is written, or if a valid row later in the same batch is not written.
4. **A missing or blank definition is not written (R109) and is reported as `import_refused:definition_missing`.** *Falsified if* any row is stored with the definition `"imported from foundry"` or any other text the caller did not supply, or a definition-less row is stored at all. The returned entry is shaped `proposed`, as `_refused_import` already shapes every declined row.

### 0.5 Which guards `import_foundry` inherits — the import door is kill-row group `C12`

**Pre-registered claim: `import_foundry` is not a new door. It is a planner in front of the existing one.**

1. **Its only write is one `import_types` call,** made only when `dry_run=False`. *Falsified if* `import_foundry` or `ontoloche/foundry.py` calls `merge_types`, `retire`, `reinstate`, `approve`, `propose_type`, `add_edge`, `retract_edge`, `amend_edge`, `record_invocation`, `register_consumer`, `record_use` or any adapter write primitive directly.
2. **It writes no `aliases` and no `successor`.** So the alias-door guards (`C12-08`, `C12-14`, `C12-16`, `C12-17`, `C12-23`, the identity guards of §5.10) are **unreachable through it**, not merely passed. *Falsified if* `check_merge_guard.py`'s Part A discovers `import_foundry` or any `foundry.py` function as a new identity writer. In that case the claim is wrong and the function needs a `KNOWN_CALLERS` verdict and a Part B row.
3. **The name-door guards are reachable and inherited unchanged:** `name_previously_retired` (`C12-05`, `C12-26`), `word_previously_retired` (`C12-21`), `import_refused:live_consumers` (`C12-06`), `import_refused:alias_collision` on the row's own name (`C12-12`, `C12-22`), and the edge and action family declaration refusals. *Falsified if* any state that makes `import_types` answer one of these makes `import_foundry` answer differently, or write.
4. **The dry run calls no adapter write primitive.** *Falsified if* a counting adapter double records a call to `put_type`, `put_proposal`, `put_consumer`, `bump_usage`, `append_event`, `put_edge` or `put_attribute_schema` during `import_foundry(dry_run=True)`.
5. **What the dry run cannot say.** It reports what the planner holds and what `resolve_type` says. It does **not** predict a guard refusal inside `import_types`, because evaluating those guards means running the write path. A row the dry run lists as *would write* can still come back `import_refused:<reason>` from the real run. This is stated in the report's docstring and in `INTERFACE.md`, not left for a caller to discover.

**The fixture shape check (R106 route 2), replacing the brief's "parses with the SDK".** A fixture passes when every `foundry-platform-sdk==1.111.0` validation error falls into a pinned allow-list: a `string_pattern_mismatch` on a field named `rid` or `linkTypeRid`, or an error at one of the exact locations listed per fixture (3 `displayName` and 1 `dataType` in `legacy`). Any other error fails the check. The SDK is a test-only dependency under a new `foundry-fixtures` extra, and the check runs as `docs/tools/check_foundry_fixtures.py`, not in the contract suite, because the contract suite is what a third-party backend installs.

### 0.6 Design tests on the three use cases (standing constraint 7)

1. **UC2, CMS.** A hand-written `fullMetadata` that re-expresses the CMS vocabulary as Foundry object types (`Facility`, `Survey`, `Citation`, `DeficiencyTag`) and link types (`issuedDuring`, `conductedAt`, `cites`), with the CMS definitions as descriptions and the edge definitions passed through `definitions=`, imports to **the same 4 entity names and 3 edge family names** `cms_vocabulary()` and `C18` already reproduce. **Prediction: 7 of 7 names match. The 2 CMS value sets do not import, because value types are out of scope.** That is a recorded gap, not a pass.
2. **UC3, NYC.** `street_tree` lives in `dpr` and `service_request` in `oti_311`, and `same_tax_lot` joins them across namespaces. **Prediction:** one Foundry ontology carrying both object types and the link imports into **one** namespace, so the UC3 vocabulary's two-namespace split is **not** reproduced. **[Inferred]** a Foundry link type joins object types in one ontology, so no single `fullMetadata` can carry the cross-namespace shape. This is the evidence for brief question 2.
3. **UC1, Tenshen.** No Foundry-shaped input (§0.1 item 6). Recorded, not tested.

**Fidelity, stated now so it cannot be inflated later.** Routes 1 and 2 prove the published shape, with the caveat in §0.1 item 2. The UC2 and UC3 fixtures are written by this row, so a name match proves the mapping inverts cleanly on shapes this row chose. Neither proves a real customer ontology looks like this. Route 4 (AIP Developer Tier) is the founder's call and is **not attempted**.

### 0.7 The brief's four questions — routed before code

1. **Two apiNames, one converted name.** Decides what the registry refuses. **Ruled R110**, `hold both + names map`.
2. **One ontology, one namespace?** Does not decide a refusal. **Interim:** one call imports one document into one `namespace`, and object type groups do not split it. UC3 (§0.6) is the evidence a later row needs.
3. **Link cardinality before `EDGES.md` has a key.** Does not decide a refusal. **Interim:** carried in `attributes["foundry_link"]["cardinality"]` per side, and listed in the report as a contortion.
4. **Which logic rules map to `Effect.op`.** Does not decide a refusal **in this row**, because imported action families declare no effects. **Interim, reported only:** `createLink` / `addLink` to `add_edge`, `deleteLink` / `removeLink` to `retract_edge`, and every object, interface or function rule to `host_state` with a `why` naming the Foundry rule. Declaring them is a later row's call, and that one does decide refusals.

### 0.8 New contract ids, named before they are written

`C12-30` to `C12-43`, written red first. Group 12 goes from 29 to 43 and the suite from 414 to 428.

| id | what it pins |
|---|---|
| C12-30 | defect 1, `endorsed` |
| C12-31 | defect 2, `example` and unknown statuses held, and no status still means `active` |
| C12-32 | defect 3, a bad name refused at `import_types` on every backend, and the batch continues |
| C12-33 | defect 4, a definition-less row never written (R109) |
| C12-34 | `import_foundry` dry run on `employee`: §0.3's column, and zero write primitives |
| C12-35 | dry run on `legacy`: §0.3's column |
| C12-36 | non-dry import writes exactly the would-write set, and properties carried verbatim with `validated: false` |
| C12-37 | name conversion, a collision held whole (R110), and `names=` resolving it |
| C12-38 | `definitions=` (R109) importing held rows, and links as edge families with `inverse_label` and cardinality carried |
| C12-39 | look-alikes from `resolve_type` in the dry run |
| C12-40 | the inherited name-door guards, through `import_foundry` |
| C12-41 | action types: no family keys declared, and the reported `Effect.op` mapping |
| C12-42 | UC2, CMS as Foundry |
| C12-43 | UC3, NYC as one Foundry ontology into one namespace |

### 0.9 What would make this row stop

1. A §0.4 falsifier fires and the fix cannot be made without changing what another door refuses. That goes to the founder.
2. §0.5 item 2 is falsified by `check_merge_guard.py`. Then `import_foundry` is a door, and it gets a Part B row before the row continues.
3. The adversarial loop's stopping rule (`6J-RUN.md` §5, `Q5` as ruled in `answers-10` §1) is not met by round 5. Then the row stops and brings the finding rather than fixing it.

---

## 1. Results

### 1.1 Predictions against what was measured

**Every §0.3 row matched on both fixtures, after one deviation (§1.2 item 1).** **[Observed]** by `measure.py`, which runs `import_foundry` dry on an empty sqlite store with every adapter write primitive wrapped in a counter, then runs it for real on a second empty store.

| | `employee` predicted | observed | `legacy` predicted | observed |
|---|---|---|---|---|
| would write, total | 3 | 3 | 19 (3 predicates, 5 entities, 11 actions) | 19 (3, 5, 11) |
| held `definition_missing` | 3 | 3 | 16 | 16 |
| other holds | 0 | 0 | 0 | 0 |
| unpaired link sides | 1 | 1 (`visited_offices`) | 4 | 4 |
| properties carried | 19 | 19 | 75 | 75 |
| not imported (query / shared property / value) | 0 / 0 / 0 | 0 / 0 / 0 | 21 / 1 / 0 | 21 / 1 / 0 |
| ops `host_state` / `add_edge` / `retract_edge` | 0 / 0 / 0 | 0 / 0 / 0 | 6 / 0 / 0 | 6 / 0 / 0 |
| look-alikes | 0 | 0, after the filter | 0 | 0, after the filter |
| write primitives during the dry run | 0 | 0 | 0 | 0 |
| real run: written / refused | 3 / 0 | 3 / 0 | 19 / 0 | 19 / 0 |

Every written predicate carries `predicate_requires_review`, and no written row carries an `import_refused` warning. **[Observed]**

**The four §0.4 falsifiers did not fire.** `C12-30` to `C12-33` were red before the code (`06e2d3b`) and are green after it, on all three legs and in the async mirror.

**§0.5 held.** `check_merge_guard.py` Part A discovered no new writer of `aliases` or `successor` (item 2), so `import_foundry` needed no `KNOWN_CALLERS` verdict and §0.9 item 2 did not trip. `C12-34` counts the write primitives (item 4) and `C12-40` drives the name-door guards through `import_foundry` (item 3).

### 1.2 Deviations

1. **Look-alikes are filtered at the namespace's `near_duplicate_threshold`.** §0.3 predicted 0 look-alikes and said nothing about a filter. **[Observed]** `resolve_type`'s `alternatives` carry every scored name down to 0.0, so unfiltered `employee` reported 3 look-alikes and `legacy` 6, every one against the seeded `equivalent_to` at 0.0 to 0.32. The filter uses the policy value the write door already uses (`PACKAGE.md` §2.6, default 0.72), so it adds no new number. **[Observed]** `facilities` against `facility` scores 0.7778 and is still reported. Written into `INTERFACE.md` §2.5a.
2. **`C8-04`'s fixture gained a definition.** Its row had none and was written with the old `"imported from <system>"` placeholder. Under R109 it is refused, so the test's subject (provenance) disappeared. The row now carries `"definition": "a scheduled flight"`, with a comment citing R109. This is a test changing because a ruling changed what the door does, not a test bent to pass.
3. **The definition check runs after every guard, not first.** The first cut checked the definition before the guards, and `C17-09` went red on every capability configuration of `check_capability_matrix`: a definition-less row over a retired name answered `definition_missing` where the guard's `name_previously_retired` is the true answer. The check moved to just before the write, so a guard's reason is never masked.
4. **`FOUNDRY_FIXTURES` is `FIXTURE.parent` in `_support.py`,** not a path built from `__file__` in the test module, because the async mirror's copy of the test lives in another directory and would otherwise look for fixtures that are not there.
5. **Two RIDs differ between generator runs:** the ontology `rid` and `editTodo`'s action `rid`. `@osdk/faux` mints them. Nothing in the importer or the tests keys on either, so the committed fixtures are one run's output and re-running `generate.mts` gives a two-line diff.
6. **The brief's fixture check ("parses with the SDK") was replaced before code,** as §0.1 item 2 and §0.5 record, because Palantir's own fixtures fail Palantir's own model. `check_foundry_fixtures.py` applies the allow-list and exits 0 on all five fixtures. **[Observed]**

7. **§0.5 item 4 names `put_attribute_schema`.** The adapter's primitive is `put_attr_schema`, and the test's list uses the right name. §0 stays as committed, so the stale name is corrected here rather than there.
8. **§0.7 question 3 said cardinality would be "listed in the report as a contortion".** No report field lists contortions. Cardinality is carried per side in `attributes["foundry_link"]`, and `INTERFACE.md` §2.5a names it a contortion in prose. A report field for it was not added.
9. **§0.7 question 4 mapped `addLink` and `removeLink` as link rules.** Neither is a rule type `foundry_sdk.v2.ontologies.models` defines: its link rules are `createLink`, `deleteLink`, `createInterfaceLink` and `deleteInterfaceLink`, in both `operations` (`CreateLinkRule`, `DeleteLinkRule`) and `fullLogicRules` (`*LinkLogicRule`). **[Observed]**, round 4. The two names were removed, so such a rule is `host_state` like any unknown one (`C12-63`). §0 stays as committed.

### 1.3 Use cases

1. **UC2, CMS (`C12-42`).** 7 of 7 names match `cms_vocabulary()`: 4 entities and 3 edge families. The 2 CMS value sets do not import, as predicted, because value types are out of scope. **That is a gap, not a pass.** Value types are where a CMS-shaped customer keeps its controlled vocabularies.
2. **UC3, NYC (`C12-43`).** One Foundry ontology imports into one namespace, so the `dpr` / `oti_311` split is not reproduced, as predicted. This is the evidence brief question 2 asked for. Splitting a document across namespaces is a later row's call.
3. **UC1, Tenshen.** Not tested, as §0.6 said.

### 1.4 Gates and suite

**[Observed]** on `e3411c0`, with `OO_POSTGRES_DSN` set and the `oo-pg` container up. Three legs, both contract directories: **1998 passed, 640 skipped, 0 failed** (22 min 48 s). The postgres leg reports `CONFORMANT: 423 ids exercised, 1 not exercisable`. All five gates exit 0: `check_links`, `check_spec_drift`, `check_merge_guard`, `check_capability_matrix`, `check_skip_census` (5 result-conditioned skips, baseline 5).

**After round 1's fixes** (`C12-44`–`C12-51`): **2040 passed, 646 skipped, 0 failed** (21 min 48 s), postgres `CONFORMANT: 431 ids exercised, 1 not exercisable`, and all five gates exit 0 again, skip census still 5 against a baseline of 5. **[Observed]**

### 1.5 Shared files this row changed, for the merge with row 8b

Row 8b landed on `main` (`586ba1a..22933f8`) while this row ran, adding `INTERFACE.md` §2.10 and changing `check_spec_drift.py`. **This branch was not rebased**, per the supervisor's instruction, so the merge resolves these. Properties stay under R105 `carry`; mapping them under §2.10 is a later row's.

| File | What this row changed | Why |
|---|---|---|
| `docs/specs/INTERFACE.md` §2.5 | two rows added to the status table (`endorsed`; `example` or any other value), and a paragraph after the table on `name_invalid`, `definition_missing`, the definition check's order, retired-over-retired and `fullmatch` | defects 1 to 4 (§0.4), R109, and round 1's `C12-44` / `C12-46` |
| `docs/specs/INTERFACE.md` §2.5a | **new subsection**, inserted between §2.5 and §2.6 (round 3 added the action-maps row, the store-first `unresolved` and the paragraph refusing a document that is not full metadata): `import_foundry`'s signature, mapping table, name rules, holds, the three printed shapes (`FoundryImportReport`, `FoundryItem`, `LookAlike`), `key` / `unresolved` / `unmatched`, the look-alike filter and what a dry run cannot say | the call this row adds. §2.10 sits after §2.9 on `main`, so the two do not overlap in place, only in the hunk offsets |
| `docs/specs/INTERFACE.md` §5.4 | the `import_refused` row of the refusal table names four import-only reasons and cites `C12-31`–`C12-33` | so the closed refusal list matches the code |
| `docs/tools/check_spec_drift.py` | `import_foundry` added to `CALLS`; a `FOUNDRY_SHAPES` dict near `CALLS`; a block in `main()` checking §2.5a's three printed shapes against `ontoloche.foundry` | so §2.5a is held to the code like every other printed shape. Additive: a merge keeps both rows' additions |
| `docs/specs/PACKAGE.md` §6.2 | the total line (414 → 453), the C12 header (29 → 68) and table rows `C12-30`–`C12-68` | the new contract ids. `main` did not touch this file |
| `ontoloche/contract/test_manifest.py` | `12: 68`, `TOTAL = 453` | the manifest checks the counts above. `main` did not touch this file |
| `docs/DECISIONS-OPEN.md` | item **24** (R109–R110, ruled) and the header line | first numbered 23; renumbered after `main` took 19 to 23 for `Q103`–`Q107`. The header's open and ruled counts will need re-adding at the merge, because both rows changed them |

### 1.6 Adversarial loop

**The bar** is `6J-RUN.md` §5's stopping rule as `answers-10` §1 ruled it: the loop ends when a full round finds no in-scope code MAJOR reachable by a shape a contributor would plausibly write, measured by whether that shape, or anything structurally like it, appears in the live suite. Cap 5 rounds (§0.9 item 3). Each round is three fresh reviewers on Sonnet, one lens each, with no knowledge of earlier rounds.

#### Round 1: three lenses, five MAJORs, all fixed

| Lens | Finding | Fix | Id |
|---|---|---|---|
| guards | **A `deprecated` import over a name this deployment retired rewrote the tombstone.** The un-retire guard read `status != "retired"`, so retired-over-retired went straight to `put_type`, and `retire_reason`, `retired_by` and `retired_at` became the import's. That is the ordinary re-run of a migration. **Pre-existing** at `import_types`, and made routine by this row | refused `name_previously_retired`, narrowed to the row the call overwrites, because a retired variant spelling is not touched (`C12-20` caught the first cut) | `C12-44` |
| mapping | **A held interface, or one the document never defines, left a written entity declaring a predicate nobody wrote**, and a held entity left a written edge pointing at it. The item said `written` and nothing else | `detail["unresolved"]` names each, with why. **Reported, not held**, because holding the dependent would decide a refusal | `C12-45` |
| mapping | **A link-name collision could not be lifted from the report.** Foundry's link side `apiName` is unique per object type, so `Task.owner` and `Project.owner` collide, and the item gave `colliding: ["owner", "owner"]` and never the `"Task.owner"` key `names=` takes | every item carries `detail["key"]`, a collision lists keys, and unmatched map keys are reported in `unmatched` | `C12-46` |
| tests | **§0.5 item 1 had no falsifier on a real run.** One `import_types` call per item, a stray second call, or a `register_consumer` after the call all left the suite green | the real run is spied on: one call, kind order, no consumer, and the store gains exactly the written set | `C12-49` |
| tests | **A link's status was never exercised.** Every fixture link is ACTIVE, so dropping the edge row's status left the suite green, and a `DEPRECATED` link would have landed live | the forward side's status governs, stated in §2.5a, and `DEPRECATED` / `EXAMPLE` links are tested | `C12-50` |

**MINORs taken:** a trailing-newline name passed `NAME_RE.match` at both the planner and `import_types`, so it is now `fullmatch` at both (`C12-46`). A non-`str` map value raises `TypeError` naming the key. `implementsInterfaces2` is read, and `createInterfaceLink` / `deleteInterfaceLink` report `add_edge` / `retract_edge` (`C12-47`). A **pre-existing** `import_types` defect, where an action row after a divergence refusal was dropped with no entry, is fixed (`C12-48`). `word_previously_retired` and `alias_collision` are now driven through `import_foundry` (`C12-51`). The two `NAME_RE`s are pinned to one pattern, one word across two kinds is pinned as not a collision, and RIDs, `imported_by` and the ontology are asserted (`C12-49`).

**MINORs declined, on the record:**
- **`extendsInterfaces` is not followed into predicates.** Transitive membership is predicate semantics, which row 8b's spec owns, and the chain is carried in `attributes["foundry_interface"]`.
- **A link is held for a definition by default.** That is R109 applied as ruled. A `displayName` fallback would be a default that decides a refusal, and that is the founder's.
- **The inverse side's status is not reported in `detail`.** It is carried in `attributes["foundry_link"]["sides"]`.
- **The status refusal runs before the retired-name guard.** An `EXAMPLE` row over a retired name answers `foundry_example` rather than `name_previously_retired`. Both refuse and neither writes.
- **`NAME_RE.match` at `propose_type` (`registry.py` 2083, 2621) and `attributes.py` is unchanged.** Those are other doors, and §0.9 item 1 says changing what another door refuses is not this row's. The trailing-newline residual is named here for the row that owns them.
- **The look-alike filter's boundary is not pinned by a test of its own.** `C12-34` kills the unfiltered form.

**Each fix was proven by mutation.** Eight mutations were run against a copy, one per fix: the link status dropped, one call per item, kind order reversed, collision keyed across kinds, `word_previously_retired` unread, the tombstone guard reverted, `unresolved` dropped, and `out[-1]` restored. **All eight were killed.** **[Observed]**




#### Round 2: three fresh lenses, four MAJORs and one defect found while fixing, all fixed

Three new Sonnet reviewers, the same three lenses, the range `2e94fe5..4e3b933`, with round 1's declined list given as settled. Not one lens came back clean, so round 3 runs.

| Lens | Finding | Fix | Test |
|---|---|---|---|
| guards | **A reference to a row `import_types` refused, or to a local tombstone, read as resolved.** `unresolved` was computed before the write from the document alone, and the store check counted any row, retired or not. On the ordinary re-run of a partly retired migration, an edge to a refused or retired entity was written with nothing reported | `Registry._foundry_unresolved` runs after the write. A reference resolves only to a row live after the import, and `why` is `held:<reason>`, `refused:<reason>`, `retired` or `not_in_document`. A dry run reads a referent the document deprecates as `retired` | `C12-52` |
| mapping | **An inverse side's `names=` key renamed the label and was reported in `unmatched`.** Only forward keys were item keys | the key is `detail["inverse_key"]` and counts as matched. An inverse label that is not a legal name holds the family `name_invalid` with `detail["invalid"] = "inverse_label"`, where before it was written unchecked | `C12-54` |
| mapping | **How an object type implements its interfaces was dropped.** `implementsInterfaces2`'s values and `sharedPropertyTypeMapping` sit beside `objectType`, so round 1's carry never reached them (`foundry_sdk.v2.ontologies.models.ObjectTypeFullMetadata`) | every sibling but `objectType` and `linkTypes` is carried in `attributes["foundry_object_type_metadata"]`, not validated | `C12-54` |
| tests | **The `TypeError` on a non-str `definitions=` value had no test.** Dropping that half of the check left the suite green | both maps are exercised, with the message matched | `C12-55` |
| tests (found while fixing) | **An alias match was reported twice in `looks_like`.** `resolution.type` is also `alternatives[0]` at the same score, and both were read. The reviewer flagged the branch as untested; the probe showed it was a duplicate source | one source, the alternatives at or above the namespace threshold | `C12-55` |

**MINORs taken:** a retired row beside a retired row of another kind with the same name is written again, so only the row the call overwrites is protected (`C12-53`). An illegal predicate word is no longer written into an entity's `predicates`, and it stays in `unresolved` (`C12-54`). `operations`' `CreateLinkRule` spells its link `linkTypeApiNameAtoB` (`foundry_sdk.v2.ontologies.models.CreateLinkRule`, checked), and that path now has a test. The look-alike filter's read of `near_duplicate_threshold` is pinned at 0.77 and 0.78 around `facilities`/`facility`'s 0.7778, and §1.1's legacy cell is asserted in `C12-35`. `foundry_status` and `definitions_key` are asserted and listed in §2.5a's `detail`. Three stale docstrings are fixed.

**MINORs declined, on the record:**
- **Interface `links` produce no item, and an effect's `link` is Foundry's link name, not an item key.** Interface links are carried in `attributes["foundry_interface"]`. An interface link is a shape on a predicate, and that is row 8b's predicate semantics. A rule names a link without its object type, so resolving it to a key would be a guess when two object types share a side name.
- **An interface and an object type with the same `apiName` share one `names=` key.** Stated in §2.5a. Separate prefixes would be a second key grammar for a rare shape.

**Each fix was proven by mutation.** Twelve mutations against a copy, one per fix: the refused referent counted as resolved, a store tombstone counted as resolved, the dry-run deprecated case unflagged, the cross-kind narrowing reverted, the inverse key unmatched, the inverse label unchecked, the metadata siblings dropped, the illegal predicate written, the `definitions` check dropped, `linkTypeApiNameAtoB` unread, the threshold hard-coded, and the second look-alike source restored. **All twelve were killed.** **[Observed]**

**Round 2's run.** **[Observed]** The full three-leg suite gave 2062 passed, 646 skipped and 2 failed (19m37s), both failures in `test_manifest.py` and both from subprocesses that could not start: the skip census exited `0xC0000142` with no output, and every capability-matrix configuration after the ninth failed three tests, while the machine was short of memory (Claude Code had reaped the first attempt for low memory). Rerun alone with memory free, `test_manifest.py` gave **7 passed**, and the five gates run alone all exit 0: the capability matrix shows every configuration conformant, `stores_aliases=False` included, and the skip census is 5 against a baseline of 5. An earlier attempt also caught a real gap, fixed before this run: `C12-52` and `C12-55` seeded aliases on a backend that declines `stores_aliases`, so the alias half of `C12-52` is now gated on that capability and `C12-55` uses a variant spelling.

#### Round 3: three fresh lenses, five MAJORs, all fixed

Three new Sonnet reviewers, the same three lenses, the range `2e94fe5..e2b3467`, with rounds 1 and 2's declined lists given as settled. Two of the five MAJORs are the record's own claims, which a narrower mutant passed. Not one lens came back clean, so round 4 runs.

| Lens | Finding | Fix | Test |
|---|---|---|---|
| guards | **A referent the store holds live was reported missing.** `_foundry_unresolved` trusted the plan before the store. A migration re-run without `definitions=` holds a standing interface `definition_missing` while its row stays active, and every entity implementing it was told its predicate was missing | the store is asked first. A live stored row resolves the reference and a retired one reads `retired`. Only an absent row is explained by the plan (`held:<reason>`, `refused:<reason>`, `not_in_document`). A dry run still reads a referent the document deprecates as `retired` | `C12-59` |
| mapping | **An action only in `actionTypesFullMetadata` was dropped**, with no item and no count. That map's `actionType` is a whole `ActionTypeV2` (`foundry_sdk.v2.ontologies.models.ActionTypeFullMetadata`, checked) | an action is the union of both maps | `C12-56` |
| mapping | **`fullLogicRules` were read for the report and never stored.** `ActionTypeV2.operations` has no `function` or interface rule variants, so for those the logic left with the report | carried in `attributes["foundry_action"]["fullLogicRules"]` | `C12-56` |
| mapping | **A document that is not full metadata imported as empty.** A pydantic `model_dump()` without `by_alias=True` gives `object_types`, which read as an empty ontology: a clean dry run, and a real run that wrote nothing | a non-dict raises `TypeError`, and a dict with none of the four type maps raises `ValueError` naming `model_dump(by_alias=True)`. An empty ontology with its keys still imports as empty | `C12-57` |
| tests | **The metadata carry was half pinned.** `C12-54` asserted only `implementsInterfaces2`, `sharedPropertyTypeMapping` and `validated`, so carrying `objectType` or `linkTypes` again, or dropping every other sibling, passed | the whole carried dict is asserted, for a document with an extra sibling | `C12-60` |

**MINORs taken:** a `definitions=` key on a link's inverse side was read as matched and defined nothing. Only an item's own key takes a definition now, and the inverse key goes to `unmatched` (`C12-58`; the tests reviewer also raised it, as a MAJOR against `e2b3467`, and it was already fixed here). A re-run no longer reports a live row as `refused:live_consumers`, or a dependent as `refused:name_previously_retired`, because both are answered by the store first (`C12-59`). An effect now reports `inverse_link` from `linkTypeApiNameBtoA` (`C12-56`). A dry-run deprecation of a referent the store holds live reads `retired`, and Foundry's status is matched in any case. A look-alike at exactly the threshold is reported, and `detail["standing"]` asks the store for the item's own kind (all `C12-60`). The `pop("unresolved")` branch was dead, because `plan` builds `detail` fresh, so it is deleted. `C12-55`'s docstring said five claims and listed four. §1.5's counts were stale at 51/436 and are now current.

**MINORs declined, on the record:**
- **Three or more link sides sharing one `linkTypeRid` cannot be addressed.** The SDK never produces this shape. A link type has two sides, and only hand-built input gives three.
- **A stored `proposed` row reading as resolved is unpinned** (a `!= "active"` mutant survives). No code path in this package persists a `TypeRecord` with `status="proposed"`, because a pending proposal is a row in the proposal store (`ontoloche/registry.py`, the note on the empty-scope report). The mutant is equivalent.
- **The look-alike self-match filter is unpinned.** A probe showed a re-run reports no self look-alike without it, so the mutant is equivalent.

**Each fix was proven by mutation.** Fourteen mutations against a copy: the plan trusted before the store, the full-metadata-only action dropped, `fullLogicRules` not carried, the document check removed, a non-dict accepted, the inverse key matching `definitions`, `inverse_link` unreported, the metadata keeping `linkTypes`, the metadata keeping `objectType`, the metadata carrying two keys only, the dry-run deprecation applied only to an absent row, the status compared case-sensitively, the look-alike compared strictly, and `standing` read without its kind. **All fourteen were killed.** **[Observed]**

**Round 3's run.** **[Observed]** The full three-leg suite with `OO_POSTGRES_DSN` set gave **2094 passed, 646 skipped, 0 failed** (21m05s), postgres `CONFORMANT: 440 ids exercised, 1 not exercisable`. All five gates exit 0, and the skip census is 5 against a baseline of 5.

#### Round 4: three fresh lenses, thirteen MAJORs, all closed

Three new Sonnet reviewers, the same three lenses, the range `2e94fe5..4bcd90d`, with rounds 1 to 3's declined lists given as settled. Eleven of the thirteen MAJORs are the tests lens's: behaviour the code does correctly and the record states, which a single-site mutant could break with the C12 file green. Not one lens came back clean, so round 5, the last the cap allows, runs.

| Lens | Finding | Fix | Test |
|---|---|---|---|
| guards | **A real run wrote over a live local row of the same name and said `written`.** A reviewer seeded `employee` with the predicate `audited`, registered a consumer gating on it, and imported a Foundry `Employee`: the predicate and the local definition were gone, the gate matched nothing, and a dry run said only `standing: True`. `import_types` has always replaced a standing row this way (`INTERFACE.md` §2.5); row 8a makes that door routine | `detail["replaces"]` lists what the write would drop (predicates, aliases, attributes, the definition) and which system wrote the standing row, on the dry run too, and is absent when nothing would be lost. **Reported, not refused**: refusing is a refusal, so it is open as `DECISIONS-OPEN.md` item **25** | `C12-61` |
| mapping | **An action only in `actionTypesFullMetadata` reported `effects: []`.** Round 3 made it an action, but `_effects` read `operations` from `actionTypes` alone | `_effects` reads the merged action's `operations` | `C12-61` |
| tests | **`namespace=`'s read side was unpinned**: `standing`, the look-alike `resolve_type`, the store read behind `unresolved` and `report.namespace` could each read `"default"` | one fixture seeded differently in two namespaces | `C12-62` |
| tests | **`deleteLink`, a retract's `inverse_link` and `source`, and an action's `status` were unpinned** (`C12-50`'s class, fixed for links only). Checking the rule names against the SDK found `addLink` and `removeLink` are not rule types at all (§1.2 item 9) | the two names removed; every SDK link rule, an `EXAMPLE` action held, a `DEPRECATED` action (in either map) written retired | `C12-63` |
| tests | **A held source entity, and a deprecated referent the planner also holds**: only the `dst` half and the unheld case were pinned | both in a dry run and a real run | `C12-63` |
| tests | **Seven mapping claims a narrower mutant passed**: the foreign `rid` for interfaces, edges and actions; the self-link forward side whatever the document order; the acronym rule and the strip in `convert_name`; the `implementsInterfaces` list on its own; an entity's `visibility` through `import_foundry`; `report.entries` | each asserted | `C12-64` |

**MINORs taken:** an unset `visibility: None` is no longer stored (`C12-61`). A repeated `implementsInterfaces` entry is written once (`C12-64`). The inverse label's `fullmatch`, a whitespace-only description held at the planner rather than refused at the door, and a document carrying only some of the type maps are pinned (`C12-64`). §1.1's four unpaired legacy link sides are asserted by name in `C12-35`. §2.5a says a name the store holds exactly gets no look-alike, because `resolve_type` answers an exact match with no alternatives.

**MINORs declined, on the record:**
- **On a re-run without `definitions=`, a row the store already defines is held `definition_missing`**, while `import_types` would keep the stored definition, so a Foundry status change to it is not applied. Lifting a hold R109 placed is the founder's: `DECISIONS-OPEN.md` item 25 (b).
- **A dry run over a type a re-run will refuse `name_previously_retired` says `would_write`.** §2.5a already says a dry run cannot predict a guard's refusal.
- **A link name in an effect is not tied to an edge item**, as round 2 declined.
- **The ontology's `displayName`, `description` and `branch` are neither carried nor counted.** §2.5a states the report keeps `apiName` and `rid`.
- **A `names=` entry is not applied to an edge endpoint whose object type is absent from the document.** Only a partial document reaches it.
- **Hold precedence beyond `definition_missing`, the default `imported_by`, a `None` look-alike score, a link side with no `linkTypeRid`, `properties` duplicated into `foundry_object_type`, `source` on a `host_state` effect, and `carried_properties` on a written item are unpinned.** Each is a hand-built shape or carries no behaviour a caller acts on.

**Each fix was proven by mutation.** Twenty-seven mutations against a copy: the seven for `replaces`, the merged `operations` and `visibility`, and twenty for the tests lens (the four namespace reads, `deleteLink` dropped, `addLink` restored, the action status, the three foreign `rid`s, the `src` ref, the self-link sort, the acronym rule, the strip, the list ignored, a repeat kept, `visibility` dropped, `entries` emptied, the held deprecated referent read as retired, and `match` for `fullmatch`). **All twenty-seven were killed.** **[Observed]**

**Round 4's run.** **[Observed]** The full three-leg suite with `OO_POSTGRES_DSN` set gave **2118 passed, 646 skipped, 0 failed** (21m42s), postgres `CONFORMANT: 444 ids exercised, 1 not exercisable`. All five gates exit 0, and the skip census is 5 against a baseline of 5.

#### Round 5: three fresh lenses, six MAJORs, none fixed — the loop stopped at the cap

Three new Sonnet reviewers, the same three lenses, the range `2e94fe5..ea5b7a7`, with rounds 1 to 4's declined lists given as settled. Every lens found a MAJOR. §0.9 item 3 says the loop stops after round 5 and the finding goes to the founder, so **nothing below is fixed**. The question is `DECISIONS-OPEN.md` item **26**.

**Three of the six are in round 4's own fix, `detail["replaces"]`.** That is the pattern of every round since round 2: each round's fixes carry the next round's MAJORs. The code underneath (holds, refusals, store-first `unresolved`, the mapping) held up under all three lenses.

| # | Lens | Finding | Verified |
|---|---|---|---|
| 1 | guards, mapping (both, independently) | **`replaces` reports a loss on every idempotent re-run of an `EXPERIMENTAL` or `ENDORSED` item** (`predicates_dropped: ["experimental"]`). `import_types` appends the lifecycle predicate after the row `replaces` diffs against is built, so the stored marker looks dropped. Breaks §2.5a's "an idempotent re-run reports nothing" | **[Observed]** by both reviewers' probes; the cause is `ontoloche/registry.py`'s `import_types`, which appends `experimental` / `endorsed` to `predicates` |
| 2 | guards | **`replaces` omits the largest losses**: a live local row turned `retired` by a `DEPRECATED` import, and its provenance (`approved_by: user:sd` becomes `unknown:imported`) | reviewer's probe |
| 3 | mapping | **On a backend with `stores_attributes=False`, everything carried is dropped and every item reads `written` with no warning**: properties, the interface mapping, link sides and cardinality, the action carry. `import_types` and `propose_type` have always been silent here (no `attributes_not_stored` warning exists in the package); the importer routes almost all of its mapping through attributes | reviewer's probe; the absence of a warning checked in `ontoloche/types.py` |
| 4 | tests | **`replaces` is three-quarters unpinned**: `aliases_dropped`, `attributes_dropped`, `imported_from == "foundry"` and the live-only gate each survive a mutant | reviewer's mutants |
| 5 | tests | **A `names=` rename is not pinned on an edge's `src_type` / `dst_type`**, the R110 collision-lift flow | reviewer's mutants; the code is right |
| 6 | tests | **A blank `definitions=` value is not pinned**; loosening the check makes a dry run say `would_write` for a row the real run refuses | reviewer's mutants; the code is right |

**MINORs, not acted on:** `replaces` stays on a real run's `refused` item; a re-run's `name_previously_retired` cannot tell the importer's own earlier write from a local tombstone; a raise inside `import_types` loses the report after a partial write (unprobed for an SDK-shaped document); three effect fields, `LookAlike.kind`, definition precedence and the converse of "every other key" are unpinned; `plan()`'s docstring says two return values, and it returns three.

**No suite was run for round 5**, because nothing changed: `ea5b7a7`'s run (round 4) stands.

#### Round 6: round 5's six MAJORs fixed

The founder ruled **`round 6`** on item 26 (2026-11-15). The ruling did not answer whether round 6 has its own cap, so this run reads it the narrow way: one fresh round of three lenses after the fixes, and a MAJOR it finds goes back to the founder rather than into a seventh round.

| # | Finding (round 5) | Fix | Test |
|---|---|---|---|
| 1 | a false `predicates_dropped: ["experimental"]` or `["endorsed"]` on every idempotent re-run | `replaces` adds the lifecycle predicate `import_types` will add for that status before it diffs | `C12-65` |
| 2 | a live row a `DEPRECATED` import retires, and a human approver overwritten, not reported | `replaces` gains `retires` and `approved_by_replaced` (any approver other than `unknown:imported`) | `C12-65` |
| 3 | on a backend declining `stores_attributes`, everything carried dropped while the item says `written` | `detail["attributes_not_stored"]` lists the keys `Capabilities.stores_attribute` says this backend drops, on a dry run too. Reported, not held. The same silence at `import_types` and `propose_type` is older than this row and is not changed here | `C12-66` |
| 4 | `aliases_dropped`, `attributes_dropped`, `imported_from == "foundry"` and the live-only gate unpinned | each asserted | `C12-65` |
| 5 | a `names=` rename on an edge's `src_type` / `dst_type` unpinned | asserted in `unresolved` and in the stored `foundry_link` | `C12-67` |
| 6 | a blank `definitions=` value unpinned | a blank value holds an edge `definition_missing` on both runs, and falls back to the description for an object type | `C12-67` |

**Red first.** Against `d1e5967`'s code, `C12-65` and `C12-66` fail on both sqlite legs. `C12-67` passes there, as round 5 said: the code was right and only the pin was missing. **[Observed]**

**Each fix was proven by mutation.** Fifteen new mutations against a copy: the lifecycle marker dropped or narrowed to `experimental`, `retires` and `approved_by_replaced` dropped, the approver compared with nothing, `aliases_dropped`, `attributes_dropped` and `imported_from` unread, the live-only gate dropped, `attributes_not_stored` never said, `attribute_projections` ignored, the `src` and `dst` renames ignored, a blank `definitions=` value accepted, and a blank value refusing the description fallback. Round 4's twenty-seven were re-run against the changed code. **All forty-two were killed.** One harness line, `entries emptied`, matched three sites in `registry.py` and was applied by hand to `import_foundry`'s. **A correction to round 4:** `ea5b7a7`'s `registry.py` has the same three sites, so that line could not have been placed then either, and round 4's "all twenty-seven were killed" was twenty-six killed and one not run. It is killed now. **[Observed]**

**Round 6's run.** Full three-leg suite: **2136 passed, 646 skipped, 0 failed** (22m54s). sqlite and postgres CONFORMANT, 447 ids exercised each; sqlite_minimal CONFORMANT, 127 exercised. All five gates exit 0, and `check_skip_census` holds at 5 of baseline 5. **[Observed]**

#### Round 6 review: three fresh lenses, one MAJOR, not fixed

Three new Sonnet reviewers, the same three lenses, each on its own copy of `afab2f4`. The tests and mapping lenses said **SHIP IT**. The guards lens said **NOT YET** with one MAJOR. Under item 26's narrow reading, that MAJOR goes to the founder as `DECISIONS-OPEN.md` item **27**, and nothing below is fixed.

| Lens | Finding | Verified |
|---|---|---|
| guards | **`replaces` compares attribute KEYS, never values**, so a value overwritten under a key both rows carry is not reported. A local `employee` with `visibility: "restricted"` was written as `NORMAL`, and the dry run's `replaces` named only the dropped `groups`. A local edge family's `symmetric: True` became `False`, and `replaces` named only the approver. `inverse_label`, `endpoint_kinds`, `level` and `payload_schema` are silent the same way | **[Observed]**: the first probe re-run by this session in the reviewer's copy, same output. The second is the reviewer's probe; the cause is one line, `attributes_dropped` in `foundry.replaces`, which diffs key sets |

**MINORs, not acted on:**
- **tests:** the `p.reason is None` gate on `replaces` and on `attributes_not_stored` is unpinned, so a held item beside a standing row could report an overwrite that never happens.
- **guards:** `replaces` names the approver but not the proposer or creation time, which `import_types`'s fresh `Provenance` also replaces. Read in code, not probed.
- **mapping:** a dry run says `would_write` for a re-run the real run refuses `name_previously_retired` (round 4 declined this; the reviewer notes the planner already holds the stored row). The dry-run item does not say the resulting status (`retired`, or `active` plus `experimental`/`endorsed`). A `definitions=` override drops the Foundry description from the carry. An effect's `link` is the bare side name, not `"<objectType>.<side>"` (round 2 declined this).

**The mapping lens checked the planner against `foundry_sdk` 1.111's models** and found link direction, side pairing, both action maps, all four statuses and the carried fields as §1.1 states.

#### Item 27: the round 6 MAJOR fixed, and the row lands

The founder ruled **`fix and land`** (2026-11-16), with the recommended scope: a `foundry_*` carry key is left out of `attributes_changed` when the standing row was imported from Foundry, and `visibility`, `groups` and the edge declaration keys are always reported. The founder also said that from now on only refusal rulings go to the founder; a report field, a test, a process or a cap choice is decided here and recorded in this record.

| Finding | Fix | Test |
|---|---|---|
| `replaces` compared attribute keys, never values (round 6, guards) | `attributes_changed`: each key both rows carry whose value the write changes, with the `foundry_*` exception above | `C12-68` |
| the `p.reason is None` gate on `replaces` and `attributes_not_stored` unpinned (round 6 MINOR, tests) | taken under the new instruction: a held item beside a standing row carries neither, on both backends and both runs | `C12-68` |

**Decided here, under the new instruction, and not built:** round 6's other MINORs stay as recorded above. The provenance fields besides the approver, the dry-run status, the overridden description and the effect's link key are each a report field a later row can add. The dry-run `name_previously_retired` and the bare link name were declined in rounds 4 and 2, and nothing in round 6 changes those reasons.

**Red first.** Against `a91aacd`'s code, `C12-68` fails on the sqlite leg (the minimal leg passes there, because its part 1 needs `stores_attributes`). **[Observed]**

**Proven by mutation.** Five mutants against a copy: changed values ignored, the `foundry_*` exception applied always, applied never, `replaces` on a held item, and `attributes_not_stored` on a held item. **All five were killed.** **[Observed]**

**The landing run.** Full three-leg suite: **2142 passed, 646 skipped, 0 failed** (22m18s). sqlite and postgres CONFORMANT, 448 ids exercised each; sqlite_minimal CONFORMANT, 128 exercised. All five gates exit 0, and `check_skip_census` holds at 5 of baseline 5. **[Observed]**

