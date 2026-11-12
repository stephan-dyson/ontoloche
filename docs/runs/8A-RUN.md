# 8A-RUN — roadmap row 8a: the Foundry metadata importer

**Status:** in flight. **Opened** by the supervising session on 2026-11-12 under the founder's instruction *"keep the project moving forward"*. **Brief:** [`handoffs/2026-09-22-row-8a-foundry-importer-brief.md`](../handoffs/2026-09-22-row-8a-foundry-importer-brief.md). **Rulings in force:** [R105–R107](../decisions/2026-09-22-founder-rulings-R105-R107.md), [R108](../decisions/2026-09-22-founder-ruling-R108.md), and [R109–R110](../decisions/2026-11-12-founder-rulings-R109-R110.md), which this row asked for before §0 was written. **Evidence:** [`findings/FOUNDRY-PARITY.md`](../findings/FOUNDRY-PARITY.md).

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
