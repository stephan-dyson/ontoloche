# FOUNDRY-PARITY — what replacing Foundry's ontology layer takes, and what the import path needs

**Status:** finding, 2026-09-22. Not a spec and not a ruling. Written to re-point the roadmap at the founder's two stated goals, restated 2026-09-22:

1. Be able to replace the **ontology function** of Palantir Foundry, including an easy way to import from that platform.
2. Solve the existing pain points of handling this layer.

**Claim tags:** **[Observed]** seen directly in this repo or on a page opened on 2026-09-22 · **[Inferred]** a reasonable read · **[Assumed]** believed, untested. Every Foundry fact carries the URL it was read from. Palantir pages were read through a fetch tool that converts HTML to markdown, so field names are as that tool reported them, not a byte copy. Where palantir.com did not show a schema, Palantir's own GitHub repos were used and are labelled **[Palantir GitHub]**.

---

## 0. The answer, first

**Goal 1 is not met today, and the gap is mostly the import path and one missing model piece.** ontoloche already has homes for Foundry's object types, link types, action types, interfaces (roughly) and enumerated value types. What it does not have is (a) an importer that reads anything Foundry actually emits, and (b) a model for the **properties** of an entity type, which Foundry treats as core and `INTERFACE.md` §0 currently rules out ("It is not a schema store").

**The shipped importer, `import_types`, has four defects against real Foundry input, [Observed] by running it** (§2). The worst two are silent: Foundry's `ENDORSED` status and its `EXAMPLE` status both import as plain `active` with no warning.

**Goal 2 is where ontoloche is already ahead, but Foundry closed some of the gap in 2026.** Global Branching went GA on 18 May 2026 with per-resource proposals and approval policies. What Foundry still does not document is the part this project was built around: finding the existing word before a duplicate is made, a declared list of the code paths that would silently drop a type, model-tier provenance, evidence and citations on a definition, and a guard against merging two capability sets (§4).

**Recommended next row: a Foundry metadata importer that reads the `fullMetadata` API shape, dry-run first, and fixes the four defects on the way** (§5). One founder decision sits in front of full parity: whether entity properties come into scope (§6).

---

## 1. Foundry concept by concept

Foundry lists ten core concepts (Ontology, Object type, Property, Shared property, Link type, Action type, Roles, Functions, Interfaces, Object Views) at https://www.palantir.com/docs/foundry/ontology/core-concepts/ and adds Object Type Groups and Value Types at https://www.palantir.com/docs/foundry/object-link-types/type-reference/.

| Foundry concept | ontoloche today | Verdict |
|---|---|---|
| **Object type** (apiName, rid, displayName, description, status, visibility, groups, primaryKey, titleProperty, properties, datasources). API shape: https://www.palantir.com/docs/foundry/api/v2/ontologies-v2-resources/object-types/get-object-type/ | `kind="entity"` `TypeEntry` (`INTERFACE.md` §2.1). `rid`/`apiName` land in `provenance.imported_from`, `visibility`/`groups` in `attributes` (`INTERFACE.md` §2.5) | **Have, for the identity half.** Primary key, title key and properties have no home (next row) |
| **Property** (base type, status, visibility, value type, formatting). Base types: https://www.palantir.com/docs/foundry/object-link-types/properties-overview/ | Nothing. `TypeEntry.attributes` is opaque by design, and `AttributeSchema` validates the shape of `attributes`, not the properties of the things a type describes | **Missing, and ruled out by a stated non-goal.** Founder decision, §6 |
| **Shared property type**. https://www.palantir.com/docs/foundry/object-link-types/shared-property-metadata/ | Nothing | **Missing** (depends on the property decision) |
| **Value type** (field type plus constraints: enum, range, regex, uuid; versioned). https://www.palantir.com/docs/foundry/object-link-types/value-types-overview/ | `kind="value_set"` covers the **enum** case only (`INTERFACE.md` §2.2) | **Partial** |
| **Interface** (abstract type, property contract, link constraints, can extend others, implemented by object types). https://www.palantir.com/docs/foundry/interfaces/interface-overview/ | `kind="predicate"`, a named capability set whose membership lives on the member (`INTERFACE.md` §2.3) | **Partial, and a close fit.** `implementedByObjectTypes` maps onto `TypeEntry.predicates`. The property contract has no home |
| **Link type** (two object types, cardinality ONE or MANY, foreign key or join table). https://www.palantir.com/docs/foundry/object-link-types/link-type-metadata/ | `kind="edge"` family with `level`, `symmetric`, `inverse_label`, `endpoint_kinds`, `payload_schema` (`EDGES.md` §2.4) | **Have, minus cardinality.** `EDGES.md` has no cardinality key |
| **Action type** (parameters, rules, submission criteria, webhooks, side effects). https://www.palantir.com/docs/foundry/action-types/overview/ | `kind="action"` family with inputs, preconditions, effects, reversibility, payload_schema, approval_mode (`ACTIONS.md` §2). `preflight` / `record_invocation` | **Have the declaration and the ledger. No executor, by design** (`ACTIONS.md` §0). Foundry's rule set is wider than the four `Effect.op` values (see §3) |
| **Action log** (each submission as an object: user, time, edited objects). https://www.palantir.com/docs/foundry/action-types/action-log/ | `record_invocation` / `invocations` (`ACTIONS.md` §3) | **Have** |
| **Functions** (TypeScript / Python code over objects). https://www.palantir.com/docs/foundry/functions/functions-on-objects/ | Nothing | **Out of scope by design** (`VISION.md` §6: no compute) |
| **Object sets, Object Views, indexing, writeback** | Nothing. The host holds the instances (`INGEST.md`, ruling R78) | **Out of scope by design.** This is the data platform half of Foundry, not the ontology definitions |
| **Object type groups**. https://www.palantir.com/docs/foundry/object-link-types/type-groups/ | `groups` kept in `attributes` on import | **Carried, not modelled** |
| **Statuses** (UI: Promoted, Active, Experimental, Deprecated, Example; API enum: ACTIVE, ENDORSED, EXPERIMENTAL, DEPRECATED). https://www.palantir.com/docs/foundry/object-link-types/metadata-statuses/ | `proposed` / `active` / `retired` plus the `experimental` predicate (`INTERFACE.md` §2.5) | **Partial.** `ENDORSED` and `EXAMPLE` are not mapped, and both import silently as `active` (§2) |
| **Permissions and markings** (project-based permissions, object and property security policies, CBAC). https://www.palantir.com/docs/foundry/object-permissioning/ontology-permissions/ | `namespace` scoping only. Tenancy is the host's predicate (R59) | **Missing, and mostly the host's job.** Row-level security is a data-platform feature |

**[Inferred]** Palantir's docs say the UI's *Promoted* status is the API's `ENDORSED`, but no page says it outright. The UI page describes Promoted as a "core, trusted resource that has been vetted by an ontology owner".

---

## 2. The import path today, and what running it found

**What exists [Observed].** `Registry.import_types` (`ontoloche/registry.py:5533`) performs `INTERFACE.md` §2.5's mapping: `deprecated` becomes `retired` with a reason, `experimental` becomes `active` plus the `experimental` predicate, and `visibility` and `groups` are kept. It guards the kill row at this door too (`PACKAGE.md` §6.2, group `C12`).

**What it takes as input [Observed].** Rows already flattened into ontoloche's own shape. The keys it reads are `name`, `kind`, `definition`, `status`, `predicates`, `attributes`, `aliases`, `created_at`, `namespace` and `source_version`. It parses nothing Foundry emits, so an operator has to hand-convert every object type, and properties, link types and action types have no route in at all. That is the opposite of an easy import.

**What running it on Foundry-shaped rows found [Observed, 2026-09-22, SQLite in-memory store, `main` at `8f2b50f`]:**

| Input row | Result | Problem |
|---|---|---|
| `status="ENDORSED"` | `active`, no predicate, no warning | A vetted, owner-endorsed type is indistinguishable from any other on arrival |
| `status="EXAMPLE"` | `active`, no predicate, no warning | Foundry's demo types enter the vocabulary as live types. That is pollution arriving through the migration door, the exact failure `VISION.md` §1 names |
| `name="NursingHome"` (a camelCase API-name shape) | **raises** `sqlite3.IntegrityError: CHECK constraint failed` | A raw backend exception instead of an `import_refused` entry. `INTERFACE.md` §2.1 requires `^[a-z][a-z0-9_]{0,63}$`, and nothing converts a Foundry name to that shape or refuses it cleanly |
| no `definition` | `active`, definition set to `"imported from foundry"` | `INTERFACE.md` §2.1 says a type without a definition "is how collision starts". Foundry's `description` is optional, so an import can fill the vocabulary with placeholder definitions and nothing warns |

**Why the name defect matters beyond Foundry [Inferred].** Any caller passing a bad name through `import_types` gets a backend-specific exception. The postgres and minimal backends were not probed, so whether they raise the same way is unverified.

---

## 3. What the importer should read

There are three documented ways to get ontology definitions out of Foundry. Only one is a sensible importer input.

| Source | What it is | Use it? |
|---|---|---|
| **`GET /api/v2/ontologies/{ontology}/fullMetadata`** | Whole-ontology metadata: object types, link types, action types (optionally with full logic rules), query types, interface types, shared property types, value types. Takes `branch`. **Public Beta** [Palantir GitHub] https://github.com/palantir/foundry-platform-python/blob/develop/docs/v2/Ontologies/Ontology.md. Response model: https://github.com/palantir/foundry-platform-python/blob/develop/docs/v2/Ontologies/models/OntologyFullMetadata.md | **Yes, the primary input.** A published API model with a Python SDK behind it. The palantir.com page for it returned 404 on 2026-09-22, so its status should be re-checked before the row builds on it |
| **Per-type v2 endpoints** (`objectTypes`, `outgoingLinkTypes`, `actionTypes`, `interfaceTypes`, `valueTypes`), most **Stable**. https://www.palantir.com/docs/foundry/api/v2/ontologies-v2-resources/object-types/list-object-types/ | The same data, fetched piecewise. Shared property types have no endpoint of their own and appear only inside full metadata | **Yes, as the fallback** if `fullMetadata` is unavailable to a customer |
| **Ontology Manager JSON export** (Advanced, then Export). https://www.palantir.com/docs/foundry/ontology-manager/export-import/ | The working state as JSON. Palantir's own page: *"You should not depend on the exported JSON schema as it may change over time."* | **No.** Building an importer on a format the vendor says not to depend on is building on sand |
| **Ontology-as-code (SuperRepo, beta)**. https://www.palantir.com/docs/foundry/superrepo/overview | TypeScript definitions deployed through Marketplace. [Palantir GitHub] maker API: https://github.com/palantir/osdk-ts/blob/main/packages/maker/README.md | **Not now.** Beta, and only customers who already moved to it would have it |

**The metadata API is read-only [Observed].** The API index lists no endpoint that writes ontology definitions: https://www.palantir.com/docs/foundry/api/. So the import is one-way, and a round trip back into Foundry would go through Ontology-as-code or Marketplace. That is out of this row's scope.

### 3.1 Field mapping for the importer (proposed)

| Foundry (API field) | ontoloche | Note |
|---|---|---|
| object type `apiName` | `name`, converted to `^[a-z][a-z0-9_]{0,63}$`; the original kept in `aliases` and `provenance.imported_from.apiName` | A name that cannot convert cleanly, or collides after conversion, is **refused with a reason**, never raised |
| `rid` | `provenance.imported_from.rid` | Already the §2.5 rule |
| `description` | `definition` | **Empty description: import as `proposed`, not `active`, with a warning.** A placeholder definition on a live type is the defect in §2 |
| `status` ACTIVE / EXPERIMENTAL / DEPRECATED | as `INTERFACE.md` §2.5 | unchanged |
| `status` ENDORSED | `active` plus predicate `endorsed` | Mirrors the `experimental` precedent, so the endorsement survives the move |
| UI status Example | skipped by default, reported in the dry run | Demo types should not enter a vocabulary unasked |
| `visibility`, groups | `attributes` | unchanged |
| `properties`, `primaryKey`, `titleProperty` | `attributes.foundry_properties` (carried verbatim) **until §6 is ruled** | Carried so nothing is lost, and marked as not validated |
| `implementsInterfaces` | `predicates` on the object type | An interface imports as `kind="predicate"`. Its property contract goes to `attributes` until §6 |
| link type (`LinkTypeSideV2`: both sides' apiNames, `cardinality`) | `kind="edge"` family, `level="instance"`, `endpoint_kinds` from the two object types | Cardinality needs a key `EDGES.md` does not have. Carried in `attributes` and flagged as a contortion |
| action type (`parameters`, `operations` / `fullLogicRules`) | `kind="action"` family. Parameters to `inputs`. Link rules to `add_edge` / `retract_edge`. Object create / modify / delete to `host_state` with a `why` naming the Foundry rule | Foundry's rule set is wider than `Effect.op`'s four values. `host_state` is the honest bucket, and the loss is recorded rather than hidden. `LogicRule` variants [Palantir GitHub]: https://github.com/palantir/foundry-platform-python/blob/develop/docs/v2/Ontologies/models/LogicRule.md |
| value type with an enum constraint | `kind="value_set"` | Other constraint kinds (range, regex, uuid) are carried in `attributes` |
| shared property types | carried in `attributes` of the types that use them | No home until §6 |
| query types (functions) | not imported, counted in the dry run | Compute is out of scope |

**The import should be dry-run first.** One call that returns a report without writing anything: what maps cleanly, what is carried but not modelled, what is refused and why, and which names collide with the existing vocabulary. `resolve_type` already answers the collision question, so the dry run can tell an operator *"you already have `facility`, and Foundry's `NursingHome` looks like it"* before anything is written. That is the step Foundry's own tooling does not offer, and it is where goal 2 meets goal 1.

---

## 4. The pain points, and what Foundry has shipped since the thesis was written

`VISION.md` §2 records four observed pains: too complex, vendor lock-in (a services dependency rather than a data one), a polluted ontology (too many entities, too many editors), and staff spending about an hour a day each on manual uploads.

**Foundry closed part of the governance gap in 2026, and `VISION.md` should say so rather than argue against the 2025 product [Observed]:**

- **Global Branching is GA as of 18 May 2026**, and object, action, link, interface and shared property types are branchable. https://www.palantir.com/docs/foundry/announcements/2026-05 and https://www.palantir.com/docs/foundry/ontologies/branching-ontology/
- **Proposals are reviewed per resource**, approved or rejected one by one with comments. https://www.palantir.com/docs/foundry/ontologies/review-ontology-proposals/
- **Protected resources and approval policies** set eligible reviewers, the number of approvals and whether self-approval is allowed. https://www.palantir.com/docs/foundry/global-branching/protecting-resources/
- **A Cleanup tool** flags past-deadline deprecations, stale datasources and missing descriptions. https://www.palantir.com/docs/foundry/ontology-manager/cleanup/
- **A Usage view** shows reads, writes and active users per type over 30 days. https://www.palantir.com/docs/foundry/ontology-manager/view-usage/

So *"Foundry has no review step"* is no longer a safe argument. What Foundry still does not document, and what ontoloche ships:

| Pain | What ontoloche does that Foundry's docs do not describe | Where |
|---|---|---|
| Pollution: duplicates | `resolve_type` finds the existing word **before** a proposal is made, including across namespaces, and answers `not_a_type` for a column that should never become a type | `INTERFACE.md` §5.3 |
| Pollution: a new type dies silently in one consumer | `consumers()` lists the **declared** code paths that gate on a type and which would drop it. Foundry's Usage view is 30-day runtime telemetry, which cannot see a path that has not run | `INTERFACE.md` §5.1, §2.3 |
| Pollution: AI-proposed types nobody checked | model tier is recorded on every proposal, and auto-approval is refused below a policy tier | `INTERFACE.md` §2.7 |
| Pollution: wrong meaning, correct numbers | evidence and external citations on a definition, with `unverified_semantics` flagged | `INTERFACE.md` §2.8 |
| Pollution: two capability lists merged as duplicates | `merge_types` refuses a predicate merge unless the extents are identical and non-empty | `INTERFACE.md` §5.10 |
| Lock-in | open source, three reference backends, a contract suite that defines conformance | `PACKAGE.md` §0 |
| Too complex | a fourteen-call surface with no compute, no UI and no platform | `INTERFACE.md` §5 |
| Manual uploads | **not yet addressed.** The ingestion mapping layer is specified (`INGEST.md`) and not built | Phase 3 build row |

**The honest caveat [Observed].** None of the table above has been tried by anyone outside this project. `VISION.md` §9 already says nobody has told the founder they would adopt a different ontology layer.

---

## 5. Recommended row order

1. **Row 8a, the Foundry metadata importer.** `import_foundry(full_metadata)` with a dry-run report, reading the `OntologyFullMetadata` shape (§3). It fixes the four defects in §2 on the way, because they sit on the same door. Design tests: a fixture built from Palantir's published model shapes, plus the project's three use cases, per standing constraint 7. **The fixture is [Assumed] faithful** until a real export is available (§6, question 2).
2. **The property model, if the founder rules it in (§6, question 1).** This is the biggest remaining parity gap and it touches `INTERFACE.md` §0.
3. **Phase 3 build (`resolve_instance`).** This is the row that addresses the manual-upload pain.
4. **The 6j follow-on (the skip-census gate's routed holes).** It is internal quality work that serves neither goal directly, so it drops below the three above.
5. **Edge cardinality.** Small, and it can ride with row 8a or the property row.

---

## 6. Questions only the founder can answer

1. **Do entity properties come into scope?** `INTERFACE.md` §0 says the registry *"is not a schema store"*. Replacing Foundry's ontology function needs property definitions (name, base type, primary key, title key), because in Foundry those are part of the ontology, not the data. Options: **`in`** (properties become governed entries with their own proposal loop, and §0 is amended), **`carry`** (import them verbatim into `attributes` and never validate them, which is the default this document proposes until ruled), or **`recommend`** (a design row brings the options with evidence).
2. **Can the partner organisation export its ontology metadata for a design test?** A fixture built from Palantir's published shapes is an assumption about the format. One real `fullMetadata` response, even redacted, would turn it into an observation. That is an access and permission question, and standing constraint 0 still applies to what could be committed.
3. **Is the goal replacement or an escape hatch?** `VISION.md` §11 question 5 asks it already, and the importer's scope depends on it. A one-way import supports both. A round trip back into Foundry is only needed for the escape hatch, and it would go through Ontology-as-code, which is beta.

---

## 7. Method

- Foundry facts: a research pass on 2026-09-22 over palantir.com docs and Palantir's GitHub repos. Two load-bearing claims were re-opened independently: the export page's warning about the JSON schema, and `get_full_metadata` / `load_metadata` being Public Beta and Private Beta.
- ontoloche facts: read from `main` at `8f2b50f`. The §2 probe used `ontoloche.backends.sqlite.SQLiteAdapter` on an in-memory store and called `Registry.import_types` once per row. It was a throwaway script and is not committed.
- Pages that returned 404 on 2026-09-22: https://www.palantir.com/docs/foundry/api/v2/ontologies-v2-resources/ontologies/get-ontology-full-metadata/ and https://www.palantir.com/docs/foundry/ontologies/ontologies-proposals/.
