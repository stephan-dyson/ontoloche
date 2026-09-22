# PROPERTIES-OPTIONS — how entity properties should come into the registry

**Status:** recommendation, 2026-09-22, written under founder ruling [R105](../decisions/2026-09-22-founder-rulings-R105-R107.md) (`recommend`). Not a spec. The recommendation went back to the founder as `Q102`, and **he ruled `adopt B` on 2026-09-22, recorded as [R108](../decisions/2026-09-22-founder-ruling-R108.md).** Row 8b specifies it.

**Claim tags:** **[Observed]** seen directly in this repo or on a page opened on 2026-09-22 · **[Inferred]** a reasonable read · **[Assumed]** believed, untested.

---

## 0. The recommendation, first

**Option B: govern property definitions as vocabulary, in two tiers that mirror Foundry's own split, and never store or validate property values.**

- **Local properties** are declared on the entity entry that owns them: name, base type, description, required flag, and optionally a `value_set` reference. The entry also names its primary key and title property. They go through the entity's own proposal and approval, like everything else an entity declares.
- **Shared properties** become registry entries of a new `kind="property"`. They are governed one by one, `resolve_type` can find them, and the entities that use one declare it.
- **Values stay with the host.** R78 is unchanged, and the registry never holds an instance or checks a row against a declaration.

**Why B.** Option A (`carry`) cannot support R107's full replacement. Option C (a schema store that validates data) is the object model `VISION.md` §3 warns against building, and it collides with R78. B is the smallest change that gives a departing Foundry customer governed property definitions they can build their own tables from. It also closes a contortion this project recorded on 2026-08-28 and never resolved (§1).

**What B costs, stated plainly:** a new `kind` is a new door for every guard, and this project's history says new doors produce kill-row trips. On top of that, the registry has no call that changes an approved entity's declaration, so a local property cannot be added after approval without a new call or a supersede pattern (§3).

---

## 1. The evidence that properties need a home

1. **Contortion 10, recorded and never closed [Observed].** `INTERFACE.md` §10b.3: `resolve_type("latitude", ...)` returns `outcome="proposal"`, so *"an approver who is not paying attention gets `latitude` in the vocabulary."* None of the four `not_a_type` reasons describes a property, and `ontoloche/types.py:69` still holds exactly four. The spec's own words: *"A perfect resolver still has nowhere honest to put the answer."*
2. **UC3's collision words are properties [Observed].** The NYC design test's shared words are `status`, `borough`, `latitude` and `longitude` (`findings/3C-VALIDATION.md`). `status` was registered as a `kind="value_set"` in each agency namespace (prediction W1.4), which records the *values* and nothing about *which entity has the property*. The value set exists, but nothing says a tree has a `status` drawn from it.
3. **INGEST already names properties without governing them [Observed].** `INGEST.md` rule 2-12 makes `host_filter` a mapping of declared keys (`agency`, `complaint_type`, `incident_zip`), and the spec says *"The VALUES stay opaque to this project; the KEYS do not."* Those keys are property names, and nothing in the registry defines them.
4. **Foundry treats properties as part of the ontology [Observed].** Every object type carries a `properties` map of `PropertyV2` (`dataType`, `description`, `displayName`, `status`, `visibility`, `valueTypeApiName`), plus `primaryKey` and `titleProperty`. https://www.palantir.com/docs/foundry/api/v2/ontologies-v2-resources/object-types/get-object-type/. Shared property types are separate, governed resources that several object types map onto (`sharedPropertyTypeMapping` in `ObjectTypeFullMetadata`). https://www.palantir.com/docs/foundry/object-link-types/shared-property-metadata/
5. **R107 makes it load-bearing.** A customer leaving Foundry has to build their own tables from somewhere, and property definitions are what they would build them from.

---

## 2. The three options

| | A. `carry` | **B. govern the definitions (recommended)** | C. schema store |
|---|---|---|---|
| What it is | Foundry properties imported verbatim into `attributes`, never read | Local properties declared on the entity, shared ones as `kind="property"` entries, values never touched | Property schemas the registry enforces against data, with migrations |
| Supports R107 full replacement | **No.** Definitions arrive but are not governed and cannot be trusted to build from | Yes, for the definitions. Data movement stays with pipeline tools | Yes, and it also takes on the data platform's job |
| Closes contortion 10 | No | **Yes.** `latitude` resolves to an existing property instead of becoming a type proposal | Yes |
| Addresses pollution (goal 2) | No. Properties rot ungoverned, the same way Foundry's do | Yes. Duplicate shared properties are found by `resolve_type`, definitions are required, and evidence and model tier are recorded | Yes, at far higher cost |
| Conflicts with a standing position | None | `INTERFACE.md` §0's *"not a schema store"* sentence is amended to *"not a store of values"* | `VISION.md` §3 (*"The object model is table stakes and it is not what failed"*), R78 (the host holds the instances), `VISION.md` §6 (no data platform) |
| Cost | Nothing, and it already exists as the interim under R105 | One new `kind`, one per-kind `AttributeSchema` for entities, a way to amend an approved entity (§3), and design tests on all three use cases | A new product |

**Why not a single tier.** The rejected variant is to make *every* property a `kind="property"` entry. It fails on a collision this project has already measured: names are unique within `(namespace, kind)`, so a tree's `status` and a request's `status` inside one namespace would have to be one entry, and UC3 shows they mean different things (`3C-VALIDATION.md` W1). Foundry avoids this by making properties local by default and shared only on purpose, and B copies that split.

---

## 3. What B has to settle, left to its spec row

1. **Amending an approved entity [Observed gap].** The only amend call in `ontoloche/registry.py` is `amend_edge` (line 7036). There is no way to change an approved type's declaration, so adding a property to a live entity has no route. The options are a new governed call (an amendment that goes through the proposal loop), or supersede-and-retire. This is the largest open design question under B.
2. **The local declaration's shape.** `FieldSpec` (`ontoloche/attributes.py:59`) already carries `type`, a required non-empty `description`, `required`, `enum` and `item_type`. **[Inferred]** a local property declaration can reuse that shape nearly as it is, validated by a per-kind `AttributeSchema` for `kind="entity"`, which is the same mechanism `EDGES.md` §2.4 uses for edge families.
3. **Base types.** Foundry has about twenty (https://www.palantir.com/docs/foundry/object-link-types/properties-overview/). The spec row decides which map to `FieldSpec` types, and which are carried as an opaque `foundry_type` string with a warning.
4. **Guards at the new door.** `merge_types`, `retire`, `import_types` and `resolve_type` all have to handle `kind="property"`. The history is the warning: row 6b's new ACTIONS doors produced kill-row trips 9 to 11, and row 6d's identity doors took the count from 14 to 23. The spec row should pre-register which guards apply before any code exists.
5. **Retiring a shared property still in use.** Foundry shows a Usage list of the object types that use a shared property. The registry equivalent is refusing to retire a `kind="property"` entry while an active entity declares it, which is the same shape as `retire`'s existing `live_consumers` refusal.
6. **`not_a_type` gains no fifth reason.** Under B, `latitude` resolves as a property rather than being declined as not-a-type, so contortion 10 closes without touching the closed reason set.

---

## 4. Design tests the spec row must run (constraint 7)

Expected outcomes are pre-registered by the spec row before it runs anything. They are not fixed here.

- **UC2 CMS:** classify the file's 23 columns into local property, shared property, value set or `not_a_type`, and check that the known traps stay caught. The severity scale stays a `value_set` with evidence, and `Location` stays `redundant_projection`.
- **UC3 NYC:** `status` stays three different things across three agencies, `latitude` and `longitude` resolve as properties, and nothing merges across namespaces.
- **UC1 Tenshen:** **[Assumed]** Tenshen's entities are defined in its own code, so this test may be that B costs Tenshen nothing. The spec row confirms or refutes that.
- **Foundry:** the fixture from R106's routes 1 and 2. Every property and shared property type in Palantir's test ontologies lands somewhere under B, and the importer's dry run names anything that does not.

---

## 5. The ask

**`Q102` — adopt option B?** Options: **`adopt B`** (a spec row opens under it, amending `INTERFACE.md` §0), **`adopt A`** (stay at `carry` indefinitely, accepting that full replacement ships without governed properties), or **`discuss`**. Default in force: `carry`, per R105.
