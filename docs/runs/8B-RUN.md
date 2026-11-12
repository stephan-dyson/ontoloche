# 8B-RUN — roadmap row 8b: entity properties in `INTERFACE.md`, the SPEC row under R108

**Status:** in flight. **Row:** opened by founder ruling [R108](../decisions/2026-09-22-founder-ruling-R108.md) (`adopt B`), run per the [brief](../handoffs/2026-09-22-row-8b-properties-spec-brief.md). **This row ships no product code.** Anything it runs lives under `docs/tools/`, the way row 7a's probes did.

**Claim tags:** **[Observed]** seen directly in this repo, in a command's output, or on a page opened this row · **[Inferred]** a reasonable read · **[Assumed]** believed, untested.

---

## §0 — PRE-REGISTRATION, committed before any section of `INTERFACE.md` changes and before any design test runs

This section is the first commit that touches this record. Every prediction below is made from the brief, R108, [`PROPERTIES-OPTIONS.md`](../findings/PROPERTIES-OPTIONS.md), the shipped code and the three use-case documents. **No design test has been walked and the Foundry fixture has not been read** when this is written. A wrong prediction stays here and is scored as a miss in §1.

### §0.1 — The spec choices the predictions are made under

The predictions only mean something against a stated design, so the design is stated first. Each choice is the spec's to make unless it decides what the registry refuses (§0.5).

1. **Carrier.** Local property declarations live in `TypeEntry.attributes` of a `kind="entity"` entry, under three reserved keys: `properties`, `primary_key` and `title_property`. A shared property's declaration lives in the `attributes` of its own `kind="property"` entry. This is the precedent edge families (`EDGES.md` §2.4) and action families (`ACTIONS.md` §2.2) already use: a declaration in `attributes`, read as a view, validated by the registry. **No new `TypeEntry` field.**
2. **`primary_key` keeps the shape it already has.** **[Observed]** the contract suite's CMS fixture already writes `attributes={"primary_key": ["ccn"]}`, and `["ccn", "survey_date", "survey_type"]` for `survey` (`ontoloche/contract/_support.py:390`, `:411`), and `sqlite_minimal` owns that one key as a typed column (`ontoloche/backends/sqlite_minimal.py:108`). So `primary_key` is an ordered list of slot names, not a single name. Foundry's single key is a one-element list.
3. **A slot either is local or uses a shared property, never both.** A local slot declares `name`, `base_type`, `description` (required, non-empty), `required`, and optionally `value_set` and `item_type`. A shared slot declares `name`, `shared` and `required`, and reads its type, description and value set from the `kind="property"` entry it names. One fact, one home.
4. **No inline `enum`.** An enumerated property points at a `kind="value_set"` entry. `INTERFACE.md` §10's CMS conflict 1 is the reason: an inline list has no provenance and no evidence slot.
5. **`shared` and `value_set` name entries in the entity's own namespace only.** A cross-namespace reference is not expressible. *The same meaning, kept apart* across namespaces stays `equivalent_to`'s job (ruling R7, `EDGES.md`).
6. **Base types.** `base_type` is a closed set: FieldSpec's seven (`str`, `int`, `float`, `bool`, `datetime`, `list`, `dict`) plus `date`, `decimal` and `opaque`. A property imported from a foreign system keeps the foreign type verbatim in `source_type`. A foreign type with no faithful mapping lands as `opaque`.
7. **Dangling and moved references warn, they never refuse.** A `shared` or `value_set` reference that names nothing, names a retired word, or names a word whose identity moved is written and warned. This is ruling R55's treatment of a declared predicate, and `EDGES.md` §2.7's rule that a dangling reference is a fact.
8. **`not_a_type`'s four reasons are untouched.** Contortion 10 closes because `property` is now a kind, so `resolve_type` has an honest answer to give, not because a fifth reason is added.

### §0.2 — Predictions for each design test (brief §3)

#### UC2 CMS — the 23 columns

| # | column | predicted home |
|---|---|---|
| 1 | CMS Certification Number (CCN) | `facility` local, `str` (leading zeros), `primary_key` |
| 2 | Provider Name | `facility` local, `str`, `title_property` |
| 3 | Provider Address | `facility` local, `str` |
| 4 | City/Town | `facility` local, `str` |
| 5 | State | `facility` local, `str` |
| 6 | ZIP Code | `facility` local, `str` (leading zeros) |
| 7 | Survey Date | `survey` local, `date`, part of `primary_key` |
| 8 | Survey Type | `survey` local, `str`, part of `primary_key` |
| 9 | Deficiency Prefix | `deficiency_tag` local, `str` |
| 10 | Deficiency Category | `deficiency_tag` local, `str` |
| 11 | Deficiency Tag Number | `deficiency_tag` local, `str` (leading zero), `primary_key` |
| 12 | Deficiency Description | `deficiency_tag` local, `str`, `title_property` (T5: the description belongs to the tag) |
| 13 | Scope Severity Code | `citation` local, `value_set` → `scope_severity_code`, **external evidence kept** |
| 14 | Deficiency Corrected | `citation` local, `value_set` → `deficiency_corrected_status` (T1) |
| 15 | Correction Date | `citation` local, `date`, not required |
| 16 | Inspection Cycle | `citation` local, `int` |
| 17–21 | Standard / Complaint / Infection Control Inspection Deficiency, Citation under IDR / IIDR | `citation` local, `bool` each |
| 22 | Location | **`not_a_type` / `redundant_projection`**, unchanged |
| 23 | Processing Date | **`not_a_type` / `export_artefact`**, unchanged (T7) |

**Counts predicted:** 21 local slots across four entities, **0 shared**, 2 slots pointing at a `value_set`, 2 `not_a_type`. **Shared properties: zero**, because one publisher writes one flat file and no column is used by two entities. That is a finding about which fixture exercises the shared tier (UC3 and Foundry), not a failure.

**Contortions predicted in UC2:** (a) `survey.ccn` and `citation`'s survey columns are **foreign keys**, and B has no way to say a slot's values are another entity's key. That is `EDGES.md`'s job, so it is recorded, not designed away. (b) `citation` has no natural key. `primary_key` is absent, which is a fact rather than an error. (c) The 1.28% of rows whose correction date precedes the survey date are **not caught**, because values are never checked (R78). That is by design, not a contortion.

#### UC3 NYC — `status`, `latitude`, `longitude`

1. **`status` stays three separate things.** Each agency's entity declares a local `status` slot whose `value_set` names its own namespace's value set. Nothing joins them: `shared` cannot cross a namespace (§0.1 item 5) and `merge_types` across namespaces is still refused non-overridably.
2. **`latitude` and `longitude` resolve as properties** in two shapes. Where an agency has registered `latitude` as a `kind="property"` entry, `resolve_type("latitude", kind="property")` answers `existing` at 1.0. Where it is only a local slot, the same call answers `proposal` with `kind="property"`, which is an honest home and closes contortion 10 as written.
3. **The residual, predicted and not designed away:** with `kind=None`, the shipped resolver still proposes an **entity**. **[Observed]** `ontoloche/registry.py:2082` builds the proposal with `kind=kind or "entity"`. Contortion 10's own text says *"it is not the resolver being weak"*, so this residual is the resolver's, and the spec does not claim to close it.
4. **No cross-namespace merge succeeds**, and none of the new doors offers a route to one.

#### UC1 Tenshen

**Predicted: B costs Tenshen nothing on the path it uses, and the brief's [Assumed] "costs nothing" is REFUTED in one place.** Tenshen's entities live in its own code and its registry vocabulary is relationship types, so an entry declaring no properties must behave exactly as today. **But** Tenshen's declared backend shape is `sqlite_minimal`, which keeps only `primary_key` out of `attributes` ([Observed] the module docstring and `Capabilities.surviving_attributes`, `ontoloche/adapter.py:320`). So `properties` and `title_property` cannot be stored there. If Tenshen ever declares a property, the declaration is lost on write unless the host adds a column. **Predicted cost: zero today, one `ALTER TABLE` the day it declares a property**, the same shape as `PACKAGE.md` §7's one `ALTER TABLE`.

#### Foundry — the fixture from R106's routes

Predicted without reading the fixture:

1. Every Foundry **shared property type** becomes one `kind="property"` entry, and every object type property that maps onto one becomes a shared slot.
2. Every other object type property becomes a local slot.
3. `string`, `integer`, `double`, `boolean`, `timestamp` and `date` map. `long`, `short`, `byte`, `float` and `decimal` map with `source_type` kept. `array` maps to `list` with `item_type`. **Geo, attachment, media, time series, vector, cipher text and marking types land `opaque`**, with `source_type` kept and a warning.
4. **Recorded contortions predicted:** (a) an **interface's property contract** has no home, because `kind="predicate"` is a capability set, not a property contract. (b) A `struct`'s sub-fields have no typed home. (c) Value types other than an enum constraint (range, regex, uuid) have no home beyond `source_type`. (d) A Foundry shared property mapped onto an object type under a **different property apiName** needs the slot name and the shared name to differ, and §0.1 item 3 allows that.

### §0.3 — The falsifiers

The brief asks for *"a falsifier for the amendment-mechanism choice"*, and "amendment" means two things in the governing documents: the carrier this spec amendment uses (brief §1), and how an approved entity is amended (R108 §2 item 1). Both get one.

- **F1, the carrier.** §0.1 item 1 is falsified if any design test needs a property fact that a declaration in `attributes` cannot hold without a second home for the same fact, or if an entry written before this amendment changes meaning because of the reserved keys. **Predicted: not falsified,** with the `sqlite_minimal` cost above recorded as a cost of the carrier rather than a falsification.
- **F2, amending an approved entity.** The candidates are a governed amendment through the proposal loop, or supersede-and-retire. **Supersede-and-retire is falsified** if adding one optional slot to an approved `facility` needs a name other than `facility`. **Predicted: falsified.** Names are unique per `(namespace, kind)`, a taken name returns the existing entry (§5.4), and a retired name is burned (§5.9), so every property addition would rename the word. **The governed amendment is falsified** if an ordinary property change in any design test can only be written by editing a provenance-bearing row in place with no event. **Predicted: not falsified.** What the amendment call may *refuse* is the founder's (§0.5), so the spec records the mechanism and does not decide its refusals.

### §0.4 — The kill-row doors `kind="property"` opens

Rows 6b and 6d produced trips through new doors. Kill row at the start of this row: **twenty-three** trips (`STATUS.md`). The doors, listed before the spec is written:

| # | door | predicted state |
|---|---|---|
| D1 | minting a `kind="property"` name at `propose_type`, `approve`, `import_types` | **inherited**: uniqueness, `name_previously_retired`, `word_previously_retired` and `C16-06`'s one-word invariant are kind-blind |
| D2 | collapsing two `kind="property"` entries at `merge_types`, `retire(successor=)`, `import_types`' alias write | **OPEN.** No guard compares base types, so two properties of different types collapse after acknowledging `no_consumer_evidence` and `definitions_diverge`. Every entity using the absorbed word then reads the survivor's type. *One word, two definitions*: the governance register's shape, not the kill row's |
| D3 | collapsing a property into an entity, or across namespaces | **inherited**: `kind_mismatch` and `cross_namespace_merge`, non-overridable |
| D4 | `resolve_type` redirecting through a property's alias or successor | **inherited residual**: `kind="property"` joins 5.3.2-13(b), a kind with no staleness operand that answers 1.0 |
| D5 | an entity's `shared` or `value_set` reference to a word that is unregistered, retired or merged | **new door, warned** under §0.1 item 7. Resolves to the identity by R38 |
| D6 | retiring a `kind="property"` entry an active entity still uses | **OPEN.** `retire` is guarded by `consumers()`, and nothing gates on a property, so it succeeds silently and leaves every user dangling |
| D7 | amending an approved entity's declaration | **OPEN.** No call exists. **[Inferred]** `import_types` re-importing an active entity rewrites its `attributes`, which makes import an ungoverned amendment door today. Checked in §1 |
| D8 | the reserved keys colliding with `attributes` written before the amendment | **inherited**: `PACKAGE.md` §5.4 never re-validates an entry written under an older schema. `primary_key` already has the reserved shape |
| D9 | a backend that cannot store `attributes` | **new door**: declarations dropped on write. Warned, never refused, as the least-refusing option |
| D10 | a property entering a predicate's extent, or being a consumer's gate | **not opened.** A property is not a predicate and `kind_mismatch` blocks every collapse into one |

**Predicted: zero new kill-row trips** (the kill row is a capability predicate merged as a duplicate, and D3 and D10 keep properties away from predicates). **Three open doors (D2, D6, D7), and each one decides what the registry refuses**, so each goes to the founder (§0.5) instead of into the spec as a default.

### §0.5 — What goes to the founder

From R108 §2's four open questions:

1. **How an approved entity is amended (D7)** decides what may change after approval, so it is the founder's. **Q103.**
2. **Base-type mapping** decides no refusal. The spec answers it (§0.1 item 6).
3. **Which guards the door inherits** is answered by the spec for every inherited guard. The one new refusal it needs, comparing two properties' declarations before a collapse (D2), is the founder's. **Q105.**
4. **Retiring a shared property still in use (D6)** is a refusal by construction. **Q104.**

The spec lands with all three marked open, and their rules are reserved rather than pinned.

### §0.6 — The stopping rule, adapted to a spec row and stated before round 1

Row 6j's adopted criterion (`6J-RUN.md` §3.9, §5 item 10), verbatim: *"The loop ends when a full round finds no in-scope code MAJOR reachable by a shape a contributor would plausibly write — measured as: does the shape, or anything structurally like it, appear anywhere in the live suite?"*

This row has no code, so the adaptation is stated here and not chosen later. **The loop ends when a full round finds no in-scope BLOCKING or MAJOR in the amended spec that a build row or a caller would plausibly hit, measured as: is it reachable using only calls and shapes the amended `INTERFACE.md` prints, over UC1, UC2, UC3 or the Foundry fixture?** Also bound, from `6I-RUN.md` §6.6 and `6J-RUN.md` §4.4: a round that produces a MAJOR or BLOCKING fix is followed by a full round that sees it, the last round sees the final text, and nothing in the reviewed artefact is edited while any lens of a round is running. **Cap: five rounds.** If round 5 still finds a reachable in-scope MAJOR, the row stops and brings it rather than fixing it, which is `answers-10` §3's rule.

Each round runs three fresh lenses: the build-row implementer, the kill-row door adversary, and the use-case and Foundry fidelity reviewer. The reviewer brief names the three use cases and the Foundry fixture.

### §0.7 — The commands this row will run, named before they are run

```
py docs/tools/check_links.py          # exit 0 at the row's start (observed) and at its end
py docs/tools/check_spec_drift.py     # exit 0 at the row's start (observed) and at its end
```

`check_spec_drift.py` has to learn every printed shape this amendment adds (brief §4). There is no code for those shapes to be checked against, so the row teaches the checker to hold them as **planned**: printed, listed, and absent from the code. The check fails the day a build row lands the class without moving it to the implemented list. That is `ACTIONS.md`'s *"extend the checker in the same change that lands the code"*, kept true for the half of the check that can run before the code exists.


---

## §1 — The design tests, walked after §0 was committed, and scored against it

### §1.0 — The baseline, measured rather than read

`py docs/tools/properties_baseline_probe.py`, on the shipped registry at `2558863` **[Observed]**:

```
C10 resolve_type(latitude, kind=None)            outcome=proposal proposal.kind=entity
C10 resolve_type(latitude, kind='property')      outcome=proposal proposal.kind=property
D7 active entity attributes after re-import      {'properties': []}
D9 sqlite_minimal attributes after write         {'primary_key': ['ccn']}
D9 sqlite_minimal warnings                       ()
D2 merge, no acknowledgement                     definitions_diverge
D2 merge, acknowledged                           MergeResult
D6 retire a used shared property                 retired
D6 warnings                                      ()
```

Round 1 added four lines to the probe, run on the same code **[Observed]**:

```
D2 retire(successor=), no acknowledgement        retired
D11 retire(survey, successor=citation)           retired
D11 warnings                                     ()
D7b property attributes after re-import          {'base_type': 'int'}
D7b warnings                                     ()
D10 retire a property a consumer gates on        live_consumers
```

**Scored against §0.4: D2, D6, D7 and D9 all HIT.** D7 is worse than predicted: re-importing an active entity did not merely rewrite `properties`, it dropped the declared `primary_key` as well, because the whole `attributes` dict is replaced. D9 is half wrong: §0.4 predicted a warning, and today there is **none**, so the warning in rule 2.10-15 is new behaviour for the build row rather than a description of the shipped code.

### §1.1 — UC2 CMS, the 23 columns

Walked under rules 2.10-1 to 2.10-12 against the shipped CMS fixture's keys (`ontoloche/contract/_support.py:390`, `:411`, `:448`: `facility` keyed on `["ccn"]`, `survey` on `["ccn", "survey_date", "survey_type"]`, `deficiency_tag` on `["tag_number"]`).

| entity | slots | key | title |
|---|---|---|---|
| `facility` | `ccn` (shared), `provider_name`, `provider_address`, `city_town`, `state`, `zip_code` (`str`) | `["ccn"]` | `provider_name` |
| `survey` | `ccn` (shared), `survey_date` (`date`), `survey_type` (`str`) | `["ccn", "survey_date", "survey_type"]` | absent |
| `deficiency_tag` | `tag_number` (shared), `deficiency_prefix`, `deficiency_category`, `deficiency_description` (`str`) | `["tag_number"]` | `deficiency_description` |
| `citation` | `scope_severity_code` (`str`, value set), `deficiency_corrected` (`str`, value set), `correction_date` (`date`), `inspection_cycle` (`int`), five `bool` flags, and `ccn`, `survey_date`, `survey_type`, `tag_number` to say which survey and tag | absent | absent |
| not declared | `Location` is `not_a_type` / `redundant_projection`, `Processing Date` is `not_a_type` / `export_artefact` | | |

**Scored against §0.2:**

- **MISS: shared properties are not zero, they are two.** §0.2 predicted 0 shared and wrote *"no column is used by two entities"*. That is false. The shipped fixture's own `survey` key includes `ccn`, and rule 2.10-5 requires every key slot to be declared on the entity, so `ccn` is a slot on `facility`, `survey` and `citation`, and `tag_number` on `deficiency_tag` and `citation`. One property used by several entities in one namespace is exactly what `kind="property"` is for. The miss came from counting CSV columns instead of slots.
- **HIT:** 2 value sets. `scope_severity_code` keeps its `external_doc` evidence because it is a `kind="value_set"` entry with provenance, so §10's severity case is unchanged. `Location` stays `redundant_projection`.
- **HIT, contortion (a):** a shared `ccn` says *the same property*, not *a reference to a facility*. Nothing in §2.10 can say that `survey.ccn`'s values are `facility`'s key. That is `EDGES.md`'s job and stays recorded, not designed away.
- **HIT, contortion (b):** `citation` has no natural key, and `primary_key` is absent.
- **HIT, by design:** the 1.28% of rows whose correction date precedes the survey date are not caught (rule 2.10-12).
- **Not predicted, recorded:** the CMS headers are not slot names (`City/Town`, `Deficiency Tag Number`). Each slot carries the header verbatim in `display_name`, which is why that field is on `PropertySpec`.

### §1.2 — UC3 NYC, `status`, `latitude`, `longitude`

1. **HIT.** Each agency's entity declares a local `status` slot with a `value_set` in its own namespace (`dpr`, `oti`, `dot`). Rule 2.10-8 gives no syntax to name another namespace's value set or property, and `merge_types` across namespaces is still refused non-overridably (rule 2.10-14). They stay three separate things.
2. **HIT.** `resolve_type("latitude", ctx, kind="property")` answers a `kind="property"` proposal **[Observed]**, §1.0 line C10. Where an agency has registered `latitude` as a `kind="property"` entry, the same call scores against it and answers `existing`. **[Inferred]** from the shipped resolver scoring within the requested kind, and not run against a seeded property in this row. Each UC3 agency publishes one dataset, so in UC3 `latitude` is a local slot and no agency needs the entry, which is a fact about the fixture rather than a gap in the design.
3. **HIT, the residual.** With `kind=None` the resolver still proposes an entity **[Observed]**, §1.0. Rule 2.10-13 records it.
4. **HIT.** No door offers a cross-namespace merge.

### §1.3 — UC1 Tenshen

**HIT, and the brief's [Assumed] "costs nothing" is REFUTED in one place, as predicted.** Rule 2.10-1 leaves an entry that declares nothing unchanged in every respect, so Tenshen, whose entities live in its own code, pays nothing today. **But** its declared backend shape is `sqlite_minimal` (beacon finding U3, `PACKAGE.md` §5.7), and **[Observed]** §1.0 line D9: that backend keeps `primary_key` and drops `properties` and `title_property`. If Tenshen ever declares a property, the declaration is lost unless the host adds a column. **The cost is zero today and one host-side column the day it declares a property.** Rule 2.10-15 makes the write say so.

### §1.4 — Foundry, the fixture from R106's routes

**The pin [Observed].** `palantir/osdk-ts` at `7fed36772967fa8287d0e8b4497177c2b204af67` (<https://github.com/palantir/osdk-ts/tree/7fed36772967fa8287d0e8b4497177c2b204af67>), the `@osdk/faux` test ontologies in `packages/shared.test/src/stubs/` and two inline in `packages/faux/src/FauxFoundry/`. Generated to `OntologyFullMetadata` JSON and parsed with `foundry-platform-sdk` **1.111.0**. The raw documents fail a strict parse only on placeholder RIDs (`"rid"`, `"ri.Employee"`), and pass with no data-type, field or discriminator error once those are rewritten, so the property shapes are valid against Palantir's own SDK. The generation reproduced `FauxOntology`'s three register methods rather than importing the class, which needs a workspace install. The generated documents are not committed: they are Palantir's test data regenerated from a pinned commit, and the pin is what makes this reproducible.

**What the fixture holds [Observed].** Four registration sites, 13 object-type rows, **84 distinct properties**, **1 shared property type** (`fooSpt`, mapped by `Employee.fullName`), **3 interfaces**, **0 value types**. 21 distinct top-level property types, which is 21 of the SDK's 22 `ObjectPropertyType` variants (`marking` never appears). Every object type is `ACTIVE`.

**Scored against §0.2:**

1. **HIT.** `fooSpt` becomes one `kind="property"` entry (`foo_spt`, with the apiName kept as an alias per §2.1), and `Employee.fullName` a shared slot.
2. **HIT.** Every other property is a local slot.
3. **HIT on the mapping: every one of the 21 types has a home** under §2.10's table. 13 of the 84 properties land `opaque` (`attachment` 2, `geopoint` 2, `geoshape` 2, `timeseries` 2, `vector` 2, `cipherText`, `geotimeSeriesReference`, `mediaReference`), with `source_type` kept.
4. **HIT (a):** an interface's property contract has no home. **HIT (b):** a `struct`'s sub-field types are kept only in `source_type`. **UNTESTED (c):** the fixture has no value types, so the prediction that a range or regex constraint has no home was neither confirmed nor refuted here. **HIT (d):** `fooSpt` is mapped onto `fullName`, a different name, which rule 2.10-4 allows.

**Not predicted, and the largest finding of the walk:**

- **MISS, and it changed the spec before the loop. 61 of the 84 properties have no description**, and that puts an undescribed property on **all ten** `LegacyFauxFoundry` object types. Rule 2.10-3 as first written required a description at `import_types`, so the import would have declined every object type in Palantir's main test ontology. That is the founder's stated goal for this project, an easy import (R105 to R107), failing on the first fixture. Rule 2.10-3 now writes an imported slot with no description, warns `property_description_missing:<slot>`, and still refuses it at `approve`. This **deviates from the brief's literal "description (required, non-empty)" at one door**, and the deviation is chosen because it is the less-refusing option: it refuses nothing new, it fabricates nothing, and `approve` keeps the brief's rule for anything that becomes approved vocabulary. Reviewers are asked to test this choice directly.
- **Recorded contortion: per-property metadata beyond `displayName` and `description` has no home.** Every fixture property carries `typeClasses`. `PropertyV2` also models `status`, `visibility`, `valueFormatting` and `dataConstraints`, which the fixture never sets. None of them has a slot, and only `status` is a governance fact. The importer's handling is row 8a's.
- **Recorded: Palantir's fixture contains a dangling reference.** In the `addEmployeeOntology` ontology, `Employee` maps `fooSpt` and no `fooSpt` is registered. Under rule 2.10-9 that is written and warned `property_reference_unregistered`, never refused. A refusal there would reject Palantir's own test data, which is the strongest evidence this row has that warn-not-refuse is the right treatment of a dangling reference.
- **Primary keys and titles [Observed]:** every object type has a single `primaryKey` and a `titleProperty`, and each lands as a one-element `primary_key` list and a `title_property`. `ObjectWithTimestampPrimaryKey` keys on a `timestamp`, so a `datetime` key slot is legal under rule 2.10-5.

### §1.5 — The falsifiers, scored

- **F1, the carrier: NOT falsified.** No design test needed a property fact that `attributes` could not hold without a second home. The `sqlite_minimal` cost (§1.3) is a cost of the carrier and is stated in rule 2.10-15.
- **F2, amending an approved entity: supersede-and-retire FALSIFIED, as predicted.** Adding a slot to an approved `facility` would need a name other than `facility`, because a taken name returns the existing entry and a retired name is burned. **The governed amendment is not falsified**, and what it refuses is Q103's.

### §1.6 — Score *(as first committed; superseded by §1.8 after round 1)*

| test | predictions | hits | misses | untested |
|---|---|---|---|---|
| UC2 | 6 | 5 | 1 (shared count) | 0 |
| UC3 | 4 | 4 | 0 | 0 |
| UC1 | 1 | 1 | 0 | 0 |
| Foundry | 7 | 6 | 0 | 1 (value types) |
| doors D2, D6, D7, D9 | 4 | 4 | 0 (D9's warning half wrong, §1.0) | 0 |
| falsifiers | 2 | 2 | 0 | 0 |

Two findings no prediction covered: the undescribed Foundry properties, which changed rule 2.10-3, and the CMS headers needing `display_name`.

### §1.7 — Corrections to §1, from round 1 of the loop

§1.0 to §1.5 are left as committed at `ae634c4`, so the record shows what the walk claimed before review. Each correction below is round 1's, re-checked from disk or by a run before it was written here, and §1.6's table is replaced by the corrected one in §1.8.

1. **UC1 was scored against the wrong backend. Partial MISS.** **[Observed]** Tenshen's shipped adapter is `WorkLinkTypeAdapter` (`C:\Users\steph\projects\beacon\src\beacon\services\ontology\work_link_type_adapter.py`, beacon `ec2e7000`), not `sqlite_minimal`. It declares `stores_attributes=True` with an `attributes_json` column, and it raises on any record other than `("tenshen", "edge")`. So *"zero today"* holds, more strongly than stated, because no entity or property entry can be written there at all. The predicted cost, *"one `ALTER TABLE`"* because declarations would be dropped, is wrong: nothing would be dropped. The real cost of Tenshen declaring properties is widening that adapter's fixed kind and namespace. Rule 2.10-16's mechanism stands for `sqlite_minimal` itself.
2. **The UC2 fixture's own shape broke rule 2.10-5 as first written. BLOCKING, fixed.** The shipped loader writes `primary_key` with no `properties` (`_support.py:390`, `:411`, `:448`), and 2.10-5 required every key name to be a declared slot, so the build row would have refused the suite's own UC2 entities. §1.1's walk had quietly assumed a fixture with `properties` added. Rule 2.10-1 now keeps that pre-amendment shape legal and unchecked against slots. **D8 is rescored MISS as first written, HIT after the fix**, and **F1 was falsified by the first draft** on §0.3's own clause (*"an entry written before this amendment changes meaning"*); the fix is what keeps the carrier, and §1.5's NOT falsified is true only of the corrected text.
3. **UC2's shared count is a choice, not a fact.** Sharing is the declarer's choice. `ccn` and `tag_number` are the two that a key forces onto several entities. `survey_date` and `survey_type` could be shared too if `citation` declares them, which makes four candidates. §0's *"21 local slots"* is scored MISS: the count of slots is not the count of columns.
4. **UC3 HIT 2 is half UNTESTED.** `existing` against a registered `kind="property"` entry was [Inferred], not run. And NYC's `location` is **not** caught as `redundant_projection`, because the resolver's `location` projection family names address columns rather than coordinates (`ontoloche/_resolve.py`). It was never walked in §1.2. It is pre-existing and now recorded as a residual in rule 2.10-14.
5. **The Foundry `opaque` prediction was half wrong.** §0.2 Foundry item 3 said `opaque` lands *"with `source_type` kept **and a warning**"*. §2.10 attaches no warning, and says so.
6. **The import exception for descriptions moved again.** Round 1 showed rule 2.10-3's *"`approve` still refuses"* never fires for a Foundry import, because §2.5 imports `active` as `active` and `approve` never sees the row. That made the exception a decision about what the registry refuses at import, so it is no longer the spec's: rule 2.10-21 is `reserved: Q106`. Row 8a's founder ruling on undescribed *types* (hold the row, take the text from the caller) is offered there as an option.
7. **The dangling `fooSpt` case loses a type.** A shared slot carries no `base_type`, so when the property it names is unregistered, `Employee.fullName`'s Foundry `string` has nowhere to go. It is still written and warned, and the loss is recorded in rule 2.10-10. An undescribed Foundry shared property type is rule 2.10-21's case too.

### §1.8 — Score, corrected

| test | predictions | hits | misses | untested |
|---|---|---|---|---|
| UC2 | 7 | 5 | 2 (shared count, local-slot count) | 0 |
| UC3 | 4 | 3 | 0 | 1 (`existing` against a registered property) |
| UC1 | 1 | 0 | 1 partial (the cost) | 0 |
| Foundry | 7 | 5 | 1 half (`opaque` warning) | 1 (value types) |
| doors D1 to D10 | 10 | 7 | 3 (D8 as first written; D9's warning; D10, see §2.1) | 0 |
| kill row: *"zero new trips"* | 1 | 1 | 0 | 0 |
| falsifiers | 2 | 1 | 1 (F1 falsified by the first draft) | 0 |

**Doors §0.4 never listed:** D11, collapsing two entities whose declarations contradict (round 1, rule 2.10-18), and D7b, re-importing a `kind="property"` entry (round 1, rule 2.10-20).

---

## §2 — The adversarial loop

### §2.1 — Round 1

Three fresh lenses, run in parallel against `ae634c4` with nothing edited while they ran: the build-row implementer, the door adversary, and the use-case and Foundry fidelity reviewer. **1 BLOCKING, 11 MAJOR, 13 MINOR** across the three, with two lenses finding the BLOCKING independently. Every MAJOR below was reached using only calls and shapes the amended `INTERFACE.md` prints, over a design test, and each one marked [Observed] was re-run by `properties_baseline_probe.py` before the fix was written.

| # | sev | finding | lens | fix |
|---|---|---|---|---|
| 1 | BLOCKING | 2.10-5 refuses the shipped UC2 fixture's `primary_key`-only shape | implementer, fidelity | 2.10-1 keeps that shape legal |
| 2 | MAJOR | D11: two entities with contradicting declarations collapse silently at `retire(successor=)` **[Observed]** | doors | 2.10-18, `reserved: Q105`, Q105 widened |
| 3 | MAJOR | Q105 and 2.10-16 misstated the default: `retire(successor=)` collapses two properties with **no** acknowledgement **[Observed]** | doors | stated door by door in 2.10-17 and Q105 |
| 4 | MAJOR | re-importing an active `kind="property"` entry changes its type silently **[Observed]** | doors | 2.10-20 and Q103 widened to property entries |
| 5 | MAJOR | the view cannot say *absent, not stored*, and no accessor was named | implementer | `why_absent` and two planned view functions |
| 6 | MAJOR | a `kind="property"` entry's validity was undefined | implementer | new rule 2.10-9 |
| 7 | MAJOR | a property may carry a predicate, so a consumer *can* gate on it and `retire` refuses `live_consumers` **[Observed]**; 2.10-17, 2.10-19, D10 and Q104 were false | implementer | 2.10-19, 2.10-22 and Q104 reworded |
| 8 | MAJOR | 2.10-2 misstated its precedent (*"one rule per kind"*) and did not say whether the checks run through `AttributeSchema` | implementer | 2.10-2: bespoke and unconditional, `detail` keys printed |
| 9 | MAJOR | 2.10-3's *"`approve` still refuses"* never fires for an `active` import | fidelity | the import case reserved as 2.10-21, Q106 |
| 10 | MAJOR | UC1 scored HIT against the wrong backend | fidelity | §1.7 item 1 |
| 11 | MAJOR | the `opaque` warning half-miss was not disclosed | fidelity | §1.7 item 5 |
| 12 | MAJOR | (counted with 1 by the fidelity lens) the UC2 rescore of D8 and F1 | fidelity | §1.7 item 2 |
| 13 to 25 | MINOR | wrong guard named at `merge_types` (`predicate_merge` runs before `kind_mismatch`); `AmbiguousKind` and the cross-kind tombstone; the absence case in Q105; an `AttributeSchema` with `additional="forbid"`; `_PLANNED_HOMES` too narrow, ids not checked unique, reserved questions not checked to exist; the namespace rule for a property entry's own `value_set`; `display_name` on both sides; `required` on a property entry; `types.KINDS` and `PROPOSABLE_KINDS`; the UC2 shared count; UC3 `location`; unscored doors; the dangling `fooSpt` type loss; an undescribed shared property type | all three | each folded into the rule named in §2.10 or §1.7; the checker now scans every `ontoloche` module, requires each `C21` id once, and requires each `reserved:` question to exist in `DECISIONS-OPEN.md` |

**Not reproduced, recorded:** the door lens could not reproduce `import_types`' alias write collapsing two properties, and called its result inconclusive. Rule 2.10-17 says so rather than claiming the door.

**A finding about this row, not the spec.** Row 8a is running in parallel in `.claude/worktrees/row-8a`, and its in-progress ruling file links to an `8A-RUN.md` it has not written yet, so `py docs/tools/check_links.py` from this tree reported one broken link **in that worktree's file** while round 1's fixes were being written, and passed again once that row wrote its record. `check_links.py` walks every `*.md` under the repo root, worktrees included, so another row's half-written file can fail this row's exit check. This row does not edit another row's files, so that is recorded rather than fixed.

**Round 1 produced a BLOCKING and MAJOR fixes, so round 2 is a full round that sees them** (§0.6).
