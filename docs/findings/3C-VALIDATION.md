# 3C — the use-case validation pass: UC3 (NYC Open Data) against INTERFACE v0 and PACKAGE v0

> **Package renamed** `open_ontology` → `ontoloche` at commit <rename-sha> (2026-08-30); the commands and paths quoted below are as recorded at the time.

**Roadmap row:** 3c. **Date:** 2026-08-28. **Model:** Opus.
**Why this row exists.** Founder direction 2026-08-28, [`ROADMAP.md`](../../ROADMAP.md) standing constraint 7: every spec is validated against the three fixtures in [`USE-CASES.md`](../USE-CASES.md) *and* survives an adversarial review loop before it is marked done. INTERFACE v0 and PACKAGE v0 were validated against **UC1 (Tenshen)** and **UC2 (CMS)** only. This row runs **UC3 (NYC Open Data)** against both, plus the adversarial loop, and records what changed.
**A recorded contortion is a pass. A silently accommodated one is a failure.**
**Claim tags:** **[Observed]** seen directly · **[Inferred]** a reasonable read · **[Assumed]** believed, untested.

**Standing constraint 0:** no employer data. Everything here is the public NYC Open Data portal, reproducible by any reader from the URLs below.

---

## 1. The three datasets

Chosen per the [`USE-CASES.md`](../USE-CASES.md) "Protocol for a UC3 design test": **three datasets, three different publishing agencies, sharing at least two column words.** Catalog queried 2026-08-28 via `https://api.us.socrata.com/api/catalog/v1?domains=data.cityofnewyork.us&only=datasets` — **2,399 datasets** [Observed], the count `USE-CASES.md` records.

| | **A — DPR trees** | **B — 311 requests** | **C — DOT meters** |
|---|---|---|---|
| Dataset id | **`uvpi-gqnh`** | **`erm2-nwe9`** | **`693u-uax6`** |
| Title | 2015 Street Tree Census - Tree Data | 311 Service Requests from 2020 to Present | Parking Meters Locations and Status |
| `resource.attribution` | Department of Parks and Recreation (DPR) | **`311`** | Department of Transportation (DOT) |
| `domain_metadata` agency | Department of Parks and Recreation (DPR) | **Office of Technology and Innovation (OTI)** | Department of Transportation (DOT) |
| Columns (catalog) | 45 | 48 | 22 |
| Rows | **683,788** | **22,283,935** | **15,598** |
| `data_updated_at` | 2017-10-04 | 2026-08-28 | 2026-08-24 |
| Created | 2016-06-03 | 2011-10-10 | 2023-02-15 |
| Update frequency | Historical data | Daily | Weekly |

All counts [Observed] 2026-08-28 from the per-dataset SODA endpoint `https://data.cityofnewyork.us/resource/<id>.json` with a `$select=count(*)` query.

**Note before anything else, because it is a finding on its own:** dataset B is attributed to **`311`** by `resource.attribution` and to **`Office of Technology and Innovation (OTI)`** by `classification.domain_metadata`. **The publisher of the dataset that would be used to define what "agency" means does not have one agreed name in its own catalogue.** [Observed] Namespace assignment for B is therefore already a judgement call before a single type is proposed.

### 1.1 The shared column words

Normalising catalog `columns_name` to lowercase with non-alphanumerics collapsed to `_`, the intersection of all three is **four words**:

`status` · `borough` · `latitude` · `longitude`

Shared by two of the three: `location` (B, C) · `community_board`, `council_district`, `bbl` (A, B) · `borough_boundaries`, `city_council_districts`, `community_districts`, `police_precincts` (B, C).

**A second finding before the walk-through: the catalogue's column names are not the API's field names.** [Observed]

| Dataset | In `columns_name`, not a SODA field | The SODA field instead |
|---|---|---|
| A | `borough`, `community_board`, `postcode` | `boroname`, `cb_num`, `zipcode` |
| B | 15 names incl. `problem_formerly_complaint_type`, `facility_type`, `due_date` | `complaint_type`, `descriptor`, `descriptor_2` (3 fields the catalogue does not list) |
| C | `latitude`, `longitude`, and 5 Socrata boundary columns | `lat`, `long` |

**Consequence:** a proposer that reads the catalogue and a proposer that reads the API propose **different words for the same column**. That is mechanism **2** (nobody could find the existing type) arriving one level above the registry, in the metadata the registry is fed. Recorded here; picked up in §4.

---

## 2. Expected outcomes — **stated before the walk-through**

Per the protocol. Committed in its own commit, ahead of the commit that records what actually happened, so the expectations cannot drift onto the results.

Notation: `A:status` = the `status` column of dataset A. Namespaces assumed one-per-agency: `dpr`, `oti_311`, `dot`.

### W1 — `status`

**[Observed] the three value sets, full-file, by grouped count:**

| | values | n |
|---|---|---|
| **A** `uvpi-gqnh.status` | `Alive` (652,173) · `Stump` (17,654) · `Dead` (13,961) | 3 |
| **B** `erm2-nwe9.status` | `Closed` (21,815,487) · `In Progress` (274,017) · `Open` (98,714) · `Pending` (63,130) · `Assigned` (24,644) · `Started` (5,140) · `Unspecified` (2,802) · `Cancel` (1) | 8 |
| **C** `693u-uax6.status` | `Active` (12,796) · `Inactive` (2,763) · **null (37)** · **`active` (2)** | 4 |

Three different meanings of one word: the **physical condition of an organism** (A), the **workflow state of a request** (B), the **operational state of a fixed asset** (C). No value appears in more than one of the three sets.

**Expected outcome: three scoped types, one per namespace, no merge.**

| Prediction | Call that decides it | Expected result |
|---|---|---|
| W1.1 Each `status` registers as its own type, scoped by `namespace` | `propose_type(name="status", kind="value_set", namespace="dpr" / "oti_311" / "dot")` | three `TypeEntry` rows; unique per `(namespace, kind)` so all three coexist — **pass expected** |
| W1.2 A merge across two of them is refused, non-overridably | `merge_types(from_="status", into="status", namespace="dpr", into_namespace="oti_311")` | `Refusal(reason="cross_namespace_merge")`, not overridable by `acknowledge` — **pass expected** |
| W1.3 The **second** agency's proposer is told the word is taken elsewhere | `resolve_type("status", ctx, namespace="oti_311")` after A is registered | **PREDICTED FAILURE.** `resolve_type` takes a single `namespace: str` and scores against that namespace's known types. Expect `outcome="proposal"` with **empty `alternatives`** — the proposer is never told `dpr:status` exists. That is mechanism 2 across namespaces, and v0 has no call that closes it |
| W1.4 `kind` is `value_set`, not `entity` | `propose_type(kind="value_set")` | accepted (CMS precedent `deficiency_corrected_status`) — **pass expected** |
| W1.5 C's own `Active` / `active` / null split is visible | nothing in §5 | **PREDICTED GAP.** The registry never reads `attributes` (§2.1), so a value-level collision *inside* one publisher's `value_set` is invisible. `attribute_census` sees the key, never the values |

### W2 — `borough`

**[Observed] the three value sets, full-file:**

| | values | n |
|---|---|---|
| **A** `uvpi-gqnh.boroname` | `Queens` 250,551 · `Brooklyn` 177,293 · `Staten Island` 105,318 · `Bronx` 85,203 · `Manhattan` 65,423 | 5 |
| **B** `erm2-nwe9.borough` | `BROOKLYN` 6,677,782 · `QUEENS` 5,358,920 · `BRONX` 4,746,676 · `MANHATTAN` 4,484,489 · `STATEN ISLAND` 937,163 · **`Unspecified` 40,472** · **absent 38,433** | 7 |
| **C** `693u-uax6.borough` | `Manhattan` 5,082 · `Brooklyn` 4,254 · `Queens` 4,242 · `Bronx` 1,681 · `Staten Island` 339 | 5 |

Same five referents everywhere. Three encodings: Title case, UPPER case, Title case. B carries **two distinct spellings of "we do not know"** — the literal string `Unspecified` and a missing field.

**Expected outcome: one shared type, three scoped value sets. This is the case v0 is predicted to fail.**

| Prediction | Call that decides it | Expected result |
|---|---|---|
| W2.1 `borough` is the **same** type in all three | `resolve_type("borough", ctx, namespace="oti_311")` after `dpr:borough` exists | **PREDICTED FAILURE.** Cross-namespace, so `existing` cannot be returned — the call cannot see another namespace. Expect `outcome="proposal"` and a second, then third, identical entry |
| W2.2 There is a way to record "these two scoped types denote the same thing" | none | **PREDICTED GAP.** v0 has `namespace` (preserve), `merge_types` (destructive, refused across namespaces), `aliases` (prior names, same entry) — and **nothing that says *equivalent, kept separate*.** `merge_types` is the only cross-type relation and it is exactly the wrong one |
| W2.3 The differing encodings are per-namespace `value_set` types | `propose_type(name="borough_name", kind="value_set", namespace=…)` ×3 | three entries — **pass expected**, and correct |
| W2.4 B's two unknown encodings are recordable as unknown | `attributes` on the `value_set` | **expected pass but unread** — the registry never validates it; the fact that `Unspecified` and absent mean the same thing is prose in a `definition` |
| W2.5 A's three projections (`borocode`, `boroname`, `boro_ct`) | `resolve_type("borocode", ctx(sibling_columns=["boroname", …]))` | `not_a_type` / `redundant_projection` for at least `borocode` — **[Observed]** `borocode`→`boroname` is 1:1 over the sample, `1`..`5` mapping to the five names |

### W3 — `latitude` and `longitude`

Present as columns in all three. They are neither entities, nor predicates, nor edges, nor enumerated value sets.

| Prediction | Call that decides it | Expected result |
|---|---|---|
| W3.1 A bare property column is **not a type** | `resolve_type("latitude", ctx)` | **PREDICTED GAP.** `not_a_type` has four reasons — `redundant_projection`, `derived_value`, `export_artefact`, `instance_not_type` — and **none of them says "this is a property, not a type"**. Expect either a wrong-reason `not_a_type` or an `outcome="proposal"` that would let a property become a type |

### W4 — `location` (B and C only)

**[Observed]** in both B and C, `location` is a GeoJSON `Point` whose coordinates equal `(longitude, latitude)` — **50 of 50 sample rows in each, independently, in two agencies.** This is the CMS `Location` pathology (T3, 419,428 of 419,479 rows) recurring in a different government body's data.

| Prediction | Call that decides it | Expected result |
|---|---|---|
| W4.1 | `resolve_type("location", ctx(sibling_columns=["latitude","longitude"]))` | `not_a_type` / `redundant_projection` — **pass expected**, this is `C3-08` generalising off CMS |

### W5 — provenance, consumers, and the ingestion shape

| Prediction | Call that decides it | Expected result |
|---|---|---|
| W5.1 A type traces to dataset id, agency and the dataset's own update date | `provenance(type)` | **partial pass predicted.** `Evidence.locator` takes the resource URL and `Citation` the dataset page; the dataset's `data_updated_at` has **no field of its own** — `Provenance.created_at` is when *we* wrote the row. Expect it in `imported_from`, whose stated purpose is foreign *system* identifiers, not dataset versions |
| W5.2 A downstream that gates on **one agency's `status` values** is registrable | `register_consumer(Consumer(gate=…))` | **PREDICTED FAILURE.** `Consumer.gate` is *a predicate name*, and a predicate's extent is a set of **types**. A dashboard that accepts only `Closed` and `In Progress` gates on **values inside a `value_set`**, which has no representation. Expect the consumer to be expressible only by degrading it to "gates on the type `oti_311:status`", which answers a different question |
| W5.3 `consumers()` reports incompletely and says so | `consumers("status", namespace="oti_311")` | `complete: False` with the registered-not-discovered `why` — **pass expected** |
| W5.4 `resolve_type` at 2,399-dataset scale finds an existing scoped type rather than re-proposing | `resolve_type` | **untestable at v0 in this pass** — the deterministic resolver (`PACKAGE.md` §2.6) is not the production one and no contract test may turn on resolver quality. Recorded as out of scope, not as a pass |

### 2.1 Summary of what is predicted to break

Four predicted failures and three predicted gaps, before running anything:

1. **W1.3** — `resolve_type` cannot see across namespaces, so the second publisher is never told the word is taken.
2. **W2.1 / W2.2** — no way to say two scoped types denote the same thing; the only cross-type relation v0 has is the destructive one.
3. **W3.1** — `not_a_type` has no reason for "this is a property".
4. **W5.2** — a consumer gating on *values* has no representation; `Consumer.gate` is a predicate name.
5. **W1.5** — value-level pollution inside one publisher's `value_set` is invisible.
6. **W5.1** — the source dataset's own update date has no home in `Provenance`.
7. **§1.1** — catalogue names and API field names disagree, so the candidate word depends on which surface was read.

**If the walk-through changes none of this, that is a finding about UC3's diversity and it is recorded as one, not papered over.**

---

## 3. The walk-through — expected vs observed

**Method.** Not prose. The three vocabularies were driven through the **reference implementation** (`open_ontology.Registry` on the SQLite backend, one namespace per agency, `approval_policy="auto"`, `min_auto_approve_tier="sonnet"`), so every row below is **[Observed]** output rather than a reading of the spec. The three `status` value sets and the three `borough` value sets are the ones in §2.

| # | Predicted | Observed | Verdict |
|---|---|---|---|
| **W1.1** | three scoped `status` types coexist | `[('dot','status','value_set'), ('dpr','status','value_set'), ('oti_311','status','value_set')]`; each `active`, `approved_by="auto:uc3_walk"` | ✅ **as predicted** |
| **W1.2** | `cross_namespace_merge`, non-overridable | `Refusal(reason="cross_namespace_merge")`; **still refused** with `acknowledge=["cross_namespace_merge","definitions_diverge"]` | ✅ **as predicted** |
| **W1.3** | the second publisher is not told the word is taken | `resolve_type("status", ns="oti_311")` → `outcome="proposal"`, `confidence=None`, **`alternatives=()`**. The *same context* asked in `ns="dpr"` → `outcome="existing"`, `confidence=1.0` | ❌ **failure, as predicted — and sharper.** The answer is decided by which namespace the caller picked *before* asking |
| **W1.4** | `kind="value_set"` accepted | accepted, round-trips on both backends | ✅ |
| **W1.5** | C's `Active`/`active`/null split invisible | `attributes` stored verbatim as `{"values": ["Active","Inactive",null,"active"], …}`, `warnings=()` | ⚠️ **gap, as predicted** |
| **W2.1** | `borough` re-proposed in each namespace | with two **byte-identical** `borough` definitions already active elsewhere: `outcome="proposal"`, `alternatives=(("status", 0.1538),)` — one same-namespace word at a noise score, the two exact matches unmentioned | ❌ **failure, as predicted** |
| **W2.2** | no way to say *equivalent, kept apart* | 17 public façade methods, 14 `TypeEntry` fields; the four cross-type relations (`merge_types`, `aliases`, `predicates`, `retire(successor=)`) each assert something **stronger** than equivalence | ❌ **gap, as predicted** |
| **W2.3** | three scoped `value_set`s for the encodings | accepted | ✅ |
| **W2.5** | `borocode` → `not_a_type`/`redundant_projection` | `outcome="proposal"` — the deterministic resolver does not catch it | ❌ **prediction wrong**; see W4.1, same cause |
| **W3.1** | a property column has no honest `not_a_type` reason | `resolve_type("latitude")` → `outcome="proposal"`, `confidence=0.4286` | ❌ **gap, as predicted** — a bare property becomes a proposal |
| **W4.1** | `location` → `not_a_type`/`redundant_projection` | **`outcome="proposal"`** in both B and C. The *same call* with CMS's sibling set (`Provider Address`, `City/Town`, `State`, `ZIP Code`) → `not_a_type`/`redundant_projection` | ❌ **prediction wrong, and this is the most consequential single result in the pass** — see §3.1 |
| **W5.1** | source `data_updated_at` has no home | ten `Provenance` fields, none of them it; `imported_from=None` | ⚠️ **gap, as predicted** |
| **W5.2** | a value-gating consumer is inexpressible | registered fine, then `consumers("status","oti_311")` → `gates_on=[]`, **`would_drop=["ops_dashboard.open_requests"]`** — the registry reports the consumer would drop the type it gates on | ❌ **failure, worse than predicted** |
| **W5.3** | `complete: False` with the right `why` | `known=1`, `complete=False`, `why_incomplete="consumers are registered, not discovered; unregistered code paths are invisible"` | ✅ |
| **W5.4** | out of scope | out of scope | — |

**Five of seven predictions confirmed. Two were wrong, both in the same direction and from the same cause** (W2.5, W4.1): the deterministic resolver's `not_a_type` rules did not fire on NYC data. That is §3.1.

### 3.1 The result that was not predicted: `not_a_type` is fitted to CMS

The single sharpest [Observed] pair in this pass:

```python
resolve_type("location", ctx(sibling_columns=("Provider Address","City/Town","State","ZIP Code")))
# -> not_a_type / redundant_projection        <- CMS. Contract test C3-08 asserts exactly this.

resolve_type("location", ctx(sibling_columns=("latitude","longitude")))
# -> proposal, "nothing in the vocabulary fits 'location'"      <- NYC. Nothing catches it.
```

**The pathology is identical.** [Observed] in B and C, `location` is a GeoJSON `Point` whose coordinates equal `(longitude, latitude)` in **50 of 50 sampled rows each, in two agencies independently** — the same finding as CMS's `Location` (T3: exactly rebuilt from four columns in 419,428 of 419,479 rows). `_resolve._PROJECTION_FAMILIES["location"]` enumerates postal-address parts (`address`, `city`, `state`, `zip`, …) and contains no coordinate name, so the geographic flavour of the same pathology walks straight past. `borocode` — 1:1 onto `boroname` — likewise comes back a `proposal`.

**Two true things, and the second is the finding.**

1. `PACKAGE.md` §2.6 says the deterministic resolver is *"not good enough for production and is not meant to be"*. On that reading this is not a defect, and widening the lookup table to fit NYC would be fitting it to the second dataset the way it was already fitted to the first.
2. **But `PACKAGE.md` §2.6 also says, in the same section, that *"no contract test may pass or fail because of resolver quality"* — and `C3-08` and `C3-09` do exactly that.** They assert a specific `not_a_type` outcome that only the shipped `DeterministicResolver` produces. So a deployment that swaps in its own resolver — §2.6's *production path* — fails the suite that defines conformance, for a reason that has nothing to do with storage.

That contradiction was invisible with one data source. It took a second government body publishing the same pathology in a different shape to surface it. **Ruling wanted — §6, item 4.**

---

## 4. What changed in each spec

### 4.1 `INTERFACE.md`

**New section §10b — the NYC Open Data design test.** Five contortions recorded, numbered 8–12 to continue §9's Tenshen series, none designed away:

| # | Contortion |
|---|---|
| **8** | `resolve_type` cannot see across namespaces, so the second publisher is never told the word is taken — mechanism **2** reintroduced by §2.6's answer to mechanism **4** |
| **9** | Nothing says *equivalent, kept apart*; every cross-type relation v0 has asserts something stronger |
| **10** | `not_a_type` has four reasons and a property column matches none of them |
| **11** | `Consumer.gate` is a predicate name, so a value-level consumer is inexpressible — and the nearest expressible thing reports backwards |
| **12** | `Provenance` has no home for the source dataset's own version |

**§11 gained a row-3c block** listing the four of those five that v0's next revision must answer, with the smallest honest fix named for each. **§5.12 went from fourteen values to fifteen** (that is R4, §5 below, not UC3).

**No call signature, data shape or refusal changed.** Every UC3 finding is an *absence*, and the ordering rule does not let a design test amend the design.

### 4.2 `PACKAGE.md`

**New section §8b — the NYC Open Data design test for #2.** Two contortions (B7, B8, continuing §7's Tenshen series) and **two new contract tests**.

**The protocol needed no change.** Scoping was already in G1's key `(namespace, kind, name)`; `AttributeSchema` was already keyed on `(namespace, kind)`. The strongest UC3 result in the package is that the attribute mechanism §5 justifies on the CMS severity ordering does the UC3 job unmodified: [Observed] a schema for `("oti_311","value_set")` requiring `unknown_encodings` refuses B's row with `Refusal("attributes_schema_violation")` while a schema for `("dpr","value_set")` requiring only `values` accepts A's — same store, same process. B has two spellings of unknown and A has none, and the deployment can require a declaration from the publisher who needs one without imposing it on the one who does not.

**The suite gained the two tests UC3 showed were missing — 109 → 111:**

| id | asserts | why it was missing |
|---|---|---|
| **`C0-07`** | one word under three namespaces is three rows, each written `expect_absent=True`, each retrievable with its own definition and attributes; the collision still raises **within** a namespace; `TypeQuery(namespace=None)` returns all three | Across all 109 tests, **two namespaces appeared in exactly one place — `C10-04`, the *refusal*.** Nothing asserted the coexistence that refusal presupposes. A backend could have passed everything while letting the second publisher's `put_type` collide with the first's |
| **`C6-07`** | `list_types(namespace=None)` returns the three scoped entries with three definitions and `complete=True`; `list_types(namespace="dot")` returns one with **`complete=False`** and a `why_incomplete` naming the namespace | `list_types` is the only call in `INTERFACE.md` §5 whose namespace may be `None`, so it is the only cross-namespace visibility the interface has — and a scoped listing reporting `complete=True` would say a word is used once when it is used three times |

`test_manifest.py`, §6.2's group counts (C0: 6→7, C6: 6→7), the §10 exit-criteria row and `docs/README.md` all updated in the same change.

**Both suites green after the change: `233 passed` sync, `271 passed` async** (Postgres 16.14 on 55432 in both legs; +4 each = two new tests × two backends).

---

## 5. Ruling R4 — the fifteenth `Refusal.reason`

Landed as its own commit before the walk-through, per the brief. Deviation **D-1** (2A, inherited by 3b) recorded that `register_consumer` against a read-only consumer source raised `NotSupported` because none of R3's fourteen reasons said it honestly. R4 applies R3's own amendment rule rather than making an exception to it:

- `INTERFACE.md` §5.12 now enumerates **fifteen**, with `consumer_source_read_only` named as a **capability** refusal — the third of that shape after `proposals_not_stored` and `cannot_record_override`;
- `Registry.register_consumer` returns `Consumer | Refusal`, and the adapter's `NotSupported` becomes a `Refusal` carrying **the adapter's own sentence** in `detail["why"]`, never an invented one;
- `C11-04` asserts the reason, that the vocabulary stayed closed, and that nothing was written — in both suites, the async one by generation rather than by a second copy;
- D-1 is marked resolved in [`../runs/2A-RUN.md`](../runs/2A-RUN.md) §4.1 and [`../runs/3B-ASYNC.md`](../runs/3B-ASYNC.md) §5, with the reasoning that produced the ruling left intact.

---

## 6. Wanted from the supervisor or the founder — **Q1–Q7 ruled 2026-08-29; Q8 open**

> **Ruled while this row was still in flight.** The supervisor answered all seven of the questions below as **R6–R12** in [`../decisions/2026-08-29-3c-rulings-R6-R12.md`](../decisions/2026-08-29-3c-rulings-R6-R12.md), and recorded a judgment on the kill-row trip. **Q8 was raised after that file was written and is still open.** The questions are kept as written, because what was asked and why is the reviewable part; the dispositions are attached.
>
> | | question | ruling | lands in |
> |---|---|---|---|
> | **Q1** | cross-namespace lookup in `resolve_type` | **R6 — yes, additive** (`search_namespaces=`) | row **3e** |
> | **Q2** | an `equivalent_to` relation | **R7 — yes, it is an EDGE**; EDGES v0 must carry *type-level* edges | **#4 EDGES** |
> | **Q3** | value-level consumer gates | **R8 — neither option in v0; the cheap warning IS taken**. *Founder-visible* | row **3d** |
> | **Q4** | resolver-dependent contract tests | **R9 — confirmed as applied**; widening the projection table stays forbidden | done |
> | **Q5** | attribute schemas keyed per name | **R10 — yes, as an override** over the per-kind schema | row **3e** |
> | **Q6** | `reinstate` | **R11 — yes, specify and implement**; `successor_active` becomes the sixteenth `Refusal.reason` | row **3e** |
> | **Q7** | conformance for a multi-flag-degraded backend | **R12 — the two-flag rule stands; a coverage report is required.** *Founder-visible* | row **3d** |
> | **Q8** | should the façade ever ask for a bounded page | **open** — raised after the ruling file | — |
>
> **The kill-row trip was judged an implementation defect, not a stop, and the row stays armed** — with the supervisor recording explicitly that the founder may read it the other way, since a guard that silently failed on the very backend it was written for is arguably a design-level failure. That call is the founder's.



> **Numbering, and why it changed.** These were first written as **R5–R11**, which **collided with the project's own ruling register** — `docs/decisions/` runs R1, R2, R3, R4 and, from 2026-08-29, **R5 (savepoint transactions over a host-owned session)**, ruled by the supervisor while this row was in flight. Two different things called R5 in one repository is mechanism **4** — semantic collision across writers — committed by the governance of the project built to prevent it, and it is recorded here rather than quietly renamed. **The `R` series belongs to the decisions register; a *question wanting a ruling* is a `Q`.** Renumbered accordingly by row 3c; nothing else changed.

**Seven items, Q1–Q7.** Q1–Q5 come from the UC3 walk-through; **Q6 and Q7 came from the adversarial review loop** and are recorded here rather than in §7 because they amend a v0 surface or the conformance definition, and belong with the others a ruling has to cover. **Q4 is the only one whose recommendation was applied** — it recurred in two consecutive rounds, which is the loop's own signal to decide rather than defer.

**Nothing here is a conflict between the three use cases.** Per `USE-CASES.md`'s rule, a UC3 finding that contradicted UC1 or UC2 would be recorded for the supervisor to resolve; none does. Every UC3 finding is an *absence*, and the CMS and Tenshen design tests stand unchanged. What follows is the other kind of item: **five decisions that would amend a v0 surface, which a design test and a review loop are not allowed to take on their own authority.**

Each names the recommendation, so a ruling is a yes/no rather than a research task.

### Q1 (wanted) — cross-namespace lookup in `resolve_type`

**The finding.** §3, W1.3 / contortion 8. `resolve_type` takes `namespace: str` and scores only inside it, so the second publisher of a word is never told the first exists. `resolve_type("status", ns="oti_311")` returns `proposal` with empty `alternatives` while the *same context* asked in `ns="dpr"` returns `existing` at confidence 1.0.

**Why it cannot wait for v1.** §2.6 makes `namespace` the answer to mechanism 4. Scoping without a cross-namespace *lookup* means every publisher re-proposes every word and the registry cannot say so — mechanism **2** reintroduced by the answer to mechanism **4**. UC3 is the fixture for exactly this, and it is the venture's kill-criterion row.

**Recommendation: amend `INTERFACE.md` §5.3 additively in INTERFACE v1, not v0.** One keyword, `search_namespaces: Sequence[str] | None = None`; hits land in `alternatives` as `("<namespace>:<name>", score)`; `Resolution.complete` becomes `true` only when the caller named every namespace. Additive, so no v0 caller changes. **Not taken in v0** because it is a signature change and the ordering rule does not let a design test amend the design.

**Mitigated meanwhile, and this part IS taken:** `Resolution` now carries Rule K's `known`/`complete`/`why_incomplete` and a `scoped_to`, so the empty `alternatives` is an *honest* incomplete answer rather than a silent one. See §7, round 1.

### Q2 (wanted) — an `equivalent_to` relation between scoped types

**The finding.** §3, W2.1–W2.2 / contortion 9. `borough` denotes the same five referents in all three agencies, in three encodings. Every cross-type relation v0 has — `merge_types`, `aliases`, `predicates`, `retire(successor=)` — asserts something **stronger** than equivalence, so nothing can record "the same thing, kept apart".

**Recommendation: assign it to deliverable #4, `EDGES.md`, and say so in #4's brief.** An `equivalent_to` between two scoped types is a *relationship between types*, which is #4's subject. **UC3 is therefore evidence that #4 must carry type-to-type edges and not only instance-level ones** — a finding for #4's scope, produced by a design test on #1. The alternative (a field on `TypeEntry`) is rejected here: a pointer to another namespace's entry stored on the entry itself is an edge with the edge machinery missing.

### Q3 (wanted) — `Consumer.gate`, and whether a value-level consumer exists

**The finding.** §3, W5.2 / contortion 11. `Consumer.gate` is a predicate name and a predicate's extent is a set of **types**, so the UC3-shaped consumer — a dashboard that accepts only `Closed` and `In Progress` from one agency's `status` — has no representation. Worse, the obvious workaround registers cleanly and then makes `consumers()` report that the consumer **would drop the very type it gates on**, which is internally correct and exactly backwards to a reader.

**Two honest options, and they are mutually exclusive:**

1. **Add a value-level gate** to §2.9 (`gate_values: list[str] | None` alongside `gate`). Cost: the registry starts having to know what a value *is*, which §2.1 spent a whole section refusing.
2. **Require `gate` to name a registered `kind="predicate"` entry.** Cost: it breaks `C11-02`, which blesses gating on a predicate that does not exist *because that is mechanism C made visible* — a real capability, deliberately kept.

**Recommendation: (2) is wrong and (1) is premature. Take neither in v0; take (1) at v1 if Phase 3 needs it.** The registry's job at v0 is to say what it does not know, and the concrete harm here is the *misleading report*, not the missing feature. **The cheap thing that should be done either way** is for `consumers()` to warn when `gate` names no registered predicate, so "would_drop" is not read as a fact about a live gate. That is a warning, not a signature change, and it is offered as the fallback ruling.

### Q4 (wanted) — `C3-08`, `C3-09` and `C4-06` versus `PACKAGE.md` §2.6's own rule

**The finding.** §3.1 and `PACKAGE.md` §8b.3 (B8). §2.6 states that *"no contract test may pass or fail because of resolver quality"*. Three tests do:

- `C3-08`/`C3-09` assert a `not_a_type` outcome that only the shipped `DeterministicResolver` produces — and UC3 showed the rule behind it is a **CMS-fitted lookup table**: the same `location`-rebuilt-from-its-parts pathology returns `redundant_projection` on CMS's address siblings and `proposal` on NYC's `latitude`/`longitude` ones, 50/50 rows in two agencies.
- `C4-06` is worse: its `unverified_semantics` judgement comes from a hardcoded keyword list inside the façade, **not behind the `Resolver` seam at all**, so a deployment cannot fix it by supplying its own resolver — which §2.6 calls the production path.

**Why it matters:** a conformance definition that a legitimate backend can fail for a non-storage reason is not a conformance definition. This is the thing the suite is load-bearing for (ruling A5 makes it the 2B gate).

**Recommendation: mark all three non-binding for third-party adapters the way `C15-02` already is (§5.5), and keep them binding for the two reference backends.** Widening `_PROJECTION_FAMILIES` to include coordinate names is explicitly **not** recommended — that is fitting the table to the second dataset the way it was already fitted to the first, and it would make the next use case's version of this finding harder to see, not easier. Moving the domain-semantic judgement behind `Resolver` is the tidier long-run answer and is a v1 item.

> **APPLIED, not merely recommended** — the one item of Q1–Q7 that was. It recurred as a MAJOR finding in **two consecutive** adversarial rounds (on `PACKAGE.md` and then on `INTERFACE.md`), which is this loop's own signal to decide rather than defer again. The three tests carry a `resolver_dependent` marker: binding for the two reference backends, skipped with a reason naming §2.6 and this ruling for a foreign adapter. **It changes nothing about this repository's gate** — `PACKAGE.md` §6.1 already requires both reference backends to pass in one run — and removes a promise the suite could not keep to anybody else. **Verified:** a foreign-adapter run skips exactly those three and deselects `C15-02`, printing the reason for each; a reference run still executes all of them (`237 passed` / `273 passed`).
>
> **Corrected once more, in the round after it was applied.** The first implementation gated the skip on whether the *storage adapter* was foreign — the wrong axis for a resolver question. It forgave a foreign backend that had kept the shipped resolver (where the three tests are perfectly valid) and still left §2.6's own **production path** — a reference backend plus a real model resolver — impossible to run, because nothing anywhere let a caller supply a `Resolver` at all. `run_contract_suite(resolver_factory=…)` and `--resolver pkg.mod:Name` now exist, and the skip keys on **the resolver being replaced**. **[Observed]:** with a caller-supplied resolver, exactly those three skip and the run reports `resolver: SUPPLIED BY THE CALLER`; with a foreign adapter and the shipped resolver, all three run.
>
> **The supervisor may reverse this.** What a ruling now decides is *confirm or revert*, not *choose from scratch*. The reason it was taken rather than left open: `PACKAGE.md` §0 says a backend is conformant iff the whole suite passes, ruling A5 makes that the Phase 2B gate, and until this change the suite failed legitimate backends for reasons §2.6 says must never gate conformance — a live defect in the gate, not a hypothetical one.

### Q5 (wanted) — attribute schemas keyed per kind, not per type name

**The finding.** `PACKAGE.md` §5.6, asserted by `C15-07`. A schema is keyed `(namespace, kind, version)`, and CMS has two `kind="value_set"` entries with different shapes. Requiring `ordering` refuses `deficiency_corrected_status` for lacking an order it has no business having; making it optional lets `scope_severity_code` be created claiming an order and declaring none — **the exact pollution §5.1 justifies the whole mechanism on.** There is no third option.

**Recommendation: allow a name-level override — `(namespace, kind, name)` schemas that shadow the per-kind one — in PACKAGE v1.** Not v0: it changes `oo_attr_schema`'s key, which is a store-schema change, and §9.4 already says a v0 store may be dropped rather than migrated, so the cost is low but the decision is not this row's. **Recorded and pinned meanwhile**, which is the part a use-case pass is allowed to do.

### Q6 (wanted) — `reinstate`, or an honest end to the retirement story

**The finding.** Raised by the second adversarial review round on `INTERFACE.md`, not by UC3 — recorded here because §6 is where this row collects items that amend a v0 surface.

§5.9 justified proceeding with a retirement under an unknown orphan state on the grounds that *"retiring is reversible-ish"*, and said that reusing a retired name *"requires an explicit `reinstate` decision by the approver"*. **`reinstate` does not exist.** It appeared exactly once in the whole repository — in that subordinate clause. There is no call, no test, no implementation, and no deviation record. `propose_type` on a retired name returns the retired entry and creates nothing (`C4-08`), so there is nothing for an approver to decide and **a retired name is burned permanently.**

**Taken now:** the false justification is corrected in §5.9 and replaced with the true one — retirement may proceed under uncertainty because it is guarded by `consumers`, recorded permanently, and **destroys no instances and no history**; the cost of a wrong retirement is that the vocabulary needs a new word.

**Recommendation: specify `reinstate` in INTERFACE v1**, as a real §5 call with a signature, a data shape and a behaviour-when-uncertain like every other — most plausibly `reinstate(type, reason, *, reinstated_by, namespace) -> TypeEntry | Refusal`, refusing when the retirement's `successor` is itself active, because reinstating a word whose replacement is in use is mechanism 4 arriving through the lifecycle. **Not taken in v0**: a new call is a surface addition, and this row is a validation pass.

**Why it matters beyond tidiness:** UC1 has a classifier that proposes types at runtime, and UC3 has dozens of agencies publishing into one registry. In both, a wrong retirement by one actor permanently removes a word from everyone, with no recorded path back. That is a governance property this document otherwise takes seriously.

### Q7 (wanted) — what "conformant" means for a backend that declines several capabilities

**The finding.** Raised by the third adversarial round on `PACKAGE.md`, then enlarged by running it. §3.2 says *"Every other flag may be `False` and the backend can still be conformant"*, and §7.4 calls a `stores_proposals=False` backend — **Tenshen's** — conformant *"as a third backend"*.

**[Observed] neither was true. 26 of 113 tests failed against such a backend**, four of them crashing outright. Causes and fixes are in `PACKAGE.md` §8b.5; the flagship case is now closed and verified (`96 passed, 25 skipped, exit 0`, with the two reference backends still running all 115).

**Then measured properly, and the answer was worse.** A later round swept **every** optional capability, one at a time, nothing else degraded. **[Observed] six of the eight failed**, from 1 failure to 24 — so §3.2's claim was false for most of the flags it covers, not just the one the reviewer found. Two of the six were defects in the **registry**, not the suite, and one of them is the venture's own kill criterion:

| declined alone | before | after |
|---|---|---|
| `stores_proposals` | 26 failed | conformant — 101 passed, 25 skipped |
| `stores_events` | 14 failed, 4 errors | conformant — 109 passed, 17 skipped |
| `stores_attributes` | 10 failed | conformant — 114 passed, 12 skipped |
| `stores_aliases` | 2 failed | conformant — 122 passed, 4 skipped |
| `indexes_membership` | 24 failed | conformant — 100 passed, 26 skipped |
| `counts_usage` | 8 failed | conformant — 116 passed, 10 skipped |
| `timestamps_usage` | 3 failed | conformant — 121 passed, 5 skipped |
| `owns_schema` | passed | conformant |
| no `AttributeStore` | 5 failed | conformant — 119 passed, 7 skipped |

**[`docs/tools/check_capability_matrix.py`](../tools/check_capability_matrix.py) now runs that table on demand and the suite runs it**, so §3.2's claim is measured rather than asserted — the same move as `check_spec_drift.py`, and for the same reason: the claim was wrong for four deliverables and nobody's eye caught it.

**What remains open, and it is a design question rather than a test bug.** A backend declining **several** optional capabilities at once still fails:

- with `stores_events=False`, an acknowledged merge is correctly refused (`cannot_record_override`, §3.6), so `C16`'s fixture cannot build the store whose invariants `C16` checks;
- with `indexes_membership=False`, the whole `C10` group's consumer-set guards degrade to `no_consumer_evidence` instead of the specific refusals each test asserts.

Both are the *specified* behaviour. The question is what conformance should mean for a backend that can never complete a merge and can never compute an extent — is it conformant with a much smaller covered surface, or is the honest answer that `indexes_membership` and `stores_events` join `enforces_unique_name` and `transactional` as non-negotiable?

**Recommendation: keep §3.2's two-flag rule, and add a *coverage report* rather than more non-negotiable flags.** A conformance run against a heavily-degraded backend should state which contract ids it could not exercise and why — the same move as `ConsumerReport.complete = False`: make the shortfall visible and enumerable instead of pretending the verdict covers everything. The per-run `CONFORMANCE` summary added by row 3c is where that belongs. **Not taken here**: it changes what a conformance verdict asserts, which is exactly the class of decision this row is not entitled to make alone.

**Why it matters:** UC1's migration story rests on §7.4's verdict. Until the multi-flag case is settled, *"Tenshen conforms as a third backend"* is verified for one declined capability and assumed for the rest.

### Q8 (wanted) — should the façade ever ask for a bounded page?

**The finding.** The last review round asked the question eleven earlier rounds had not: **can a broken backend PASS the suite?** It can. §3.3 gives `TypeQuery` a `limit` and an opaque `after` cursor and `TypePage` a `next_after`, ordered by `(namespace, kind, name)`, and justifies query objects over kwargs on exactly that machinery. **Nothing exercised any of it.** [Observed]: an adapter identical to the reference one except that it silently drops `limit` and `after` — every page the whole set, which in a real keyset consumer is a duplicate-forever loop — ran the whole suite to `119 passed, exit 0` and printed the CONFORMANCE banner with no caveat.

**Half of it is fixed:** `C0-10` now seeds seven rows, pages them at `limit=3`, and asserts the pages are disjoint, ordered, exhaustive and terminating. The broken adapter fails it. Both reference backends already implemented keyset pagination correctly — a proper `(namespace, kind, name) > (?, ?, ?)` — and nothing had ever checked.

**The half that wants a ruling.** `Registry` never *asks* for a bounded page: [Observed] **no call site in either the sync or the async façade passes `limit` or `after` at all.** So a correct implementation is still never exercised through the product path, and `list_types(namespace=None)` at UC3's stated scale — 2,399 datasets, *"hundreds to low thousands of types"* — is an unconditional full-table fetch. §3.3 already accepts that `list_types(orphaned=)` is O(types) *"at the scale this registry is for"*, so this may be a deliberate and correct choice.

**Still open — this one post-dates the ruling file. Recommendation: leave the façade unbounded in v0 and say so in §3.3, rather than leaving it unsaid.** The reason it is not obvious is `complete`/`known`: if `list_types` starts paging internally, a caller receiving one page must be told whether `known` counts the page or the set, and Rule K currently has no answer. **That is a design decision on `TypeListing`, not a bug**, and Phase 3's ingestion loop is the consumer that would force it. Until then the honest position is that pagination is an *adapter* capability the registry does not yet use — now tested, and stated.

### What is NOT wanted

Four items are recorded and need no ruling — they are collected in `INTERFACE.md` §11 for v1 and cost nothing to defer: `property_not_type` as a fifth `not_a_type` reason (contortion 10), `Provenance.source_version` (contortion 12), cross-namespace `find_consumers`/`attribute_census` (B7), and the catalogue-vs-API name divergence (§1.1), which no registry call can fix and which belongs to Phase 3's ingestion layer.

---

## 7. The adversarial review loop

**Protocol** (`USE-CASES.md`, ROADMAP standing constraint 7): a fresh, hostile reviewer each round, briefed with the three fixtures and asked to break the spec against each; loop until **two consecutive fresh reviewers return no BLOCKING or MAJOR findings**. Reviewers were run on Sonnet, the orchestration on Opus. No reviewer saw a previous round's verdict, and each was given the standing decisions and open rulings so it could not re-raise a settled question as new.

Every round below returned **NOT YET**. Not one finding was dismissed; each was either fixed or recorded with a written reason.

### 7.1 Round log

| # | Spec | Findings | What it caught, and what changed |
|---|---|---|---|
| 1 | INTERFACE | 2 MAJOR | **Rule K was stated globally and applied selectively.** `Resolution.alternatives` and `predicates()` were bare lists, so the second publisher of a colliding word got `alternatives: []` — an empty list standing in for *"we did not look"*, the one thing Rule U forbids by name, with no field to ask whether the search had been scoped. Both now carry Rule K. Also: §2.8 cited `C4-06` for something it does not assert; one `[Observed]` was a judgement. |
| 1 | PACKAGE | 1 BLOCKING, 2 MAJOR | **G1 and G2 were never raced.** §3.5 says G1 must come from a constraint and that a read-then-write check *"is not sufficient"* — every test called the primitives sequentially on one thread, which check-then-insert passes just as happily. `C0-08` added and **verified to bite**: a check-then-insert wrapper yields two winners and fails it. `C15-07` added for the per-kind schema limit. B8 recorded. |
| 2 | INTERFACE | 3 MAJOR | **`reinstate` was a call the document invented in a subordinate clause** — one occurrence in the whole repository, no implementation, while §5.9 leaned on it to call retirement *"reversible-ish"*. Justification corrected, not deleted (see §6, Q6). `register_consumer`'s signature still said `-> Consumer` in the one place it is declared. Rule K said `known: int`; two of its four shapes are `int \| None`. |
| 2 | PACKAGE | 1 BLOCKING, 2 MAJOR | **The conformance gate was not the gate.** §5.5 says a backend *"may not be failed for"* `C15-02`; `@pytest.mark.nonbinding` only silenced a warning and the runner ran everything, so a backend that honestly declined the optional `AttributeStore` **was reported as failing the suite that ruling A5 makes the Phase 2B gate**. Both runners now default to `-m "not nonbinding"`, and every run prints what it covered. **Q4 applied** after recurring in two rounds. §11.1's ruling ledger had drifted out of sync with its own rulings. |
| 3 | INTERFACE | 1 BLOCKING, 1 MAJOR | `propose_type` under `approval_policy="auto"` meeting the tier gate returned a still-pending `Proposal` carrying a warning in no vocabulary — neither §5.4's `TypeEntry` nor §2.7's `Refusal`. Recorded in `2A-RUN.md` as D-11; §11 had failed to carry it forward, leaving §13's *"a stated behaviour when uncertain"* false for that call. **It is UC1's own scenario.** |
| 3 | PACKAGE | 1 BLOCKING, 2 MAJOR | **The suite could not be passed by the backend the document calls conformant.** §3.2 says every optional flag may be `False`; §7.4 says a `stores_proposals=False` backend — Tenshen's — conforms *"as a third backend"*. **26 of 113 tests failed against one**, four crashing outright. Fixed (see §8b.5); now `96 passed, 25 skipped, exit 0`. `C0-09` and `C5-12` added; the multi-flag residue recorded as **Q7**. |
| 4 | INTERFACE | 2 MAJOR | `PredicateEntry.extent_size` was typed `int` in §5.2's table and required to be `None` three lines below — **Rule U's marquee example contradicting its own data shape.** Q4's applied fix gated on a foreign *adapter*, the wrong axis for a resolver question, and nothing let a caller supply a `Resolver` at all, so §2.6's *production path* was unrunnable. `resolver_factory` and `--resolver` added; the gate re-keyed. |
| 5 | INTERFACE | 1 BLOCKING, 2 MINOR | **`merge_types` was the one call in §5 with no printed data shape** — four rounds and the whole UC3 pass had walked past it. The shipped `MergeResult` carries nine fields, two of which (`entry`, `aliases_added`) hold the part of the design that matters: a merge *retires and aliases*, it does not delete. The call count, wrong since #1 and quoted onward into `README.md`, corrected from twelve to thirteen. |
| 6 | INTERFACE | 1 BLOCKING, 1 MAJOR, 1 MINOR | §5.10's signature omitted `into_namespace`, so **`cross_namespace_merge` — the non-overridable refusal this whole row exists to exercise — was unreachable from the printed contract**, while §10b and this finding both call it. `TypeEntry.attr_schema_version` is returned on every entry and was in neither the field table nor the deviation ledger. **And the durable fix:** six rounds had each found one defect of this same family, so [`docs/tools/check_spec_drift.py`](../tools/check_spec_drift.py) now compares all fifteen printed shapes and thirteen signatures against the code — **it found two more the moment it was written**, and the contract suite runs it. |
| 7 | INTERFACE | 1 BLOCKING, 1 MAJOR | The reviewer brief was re-aimed at design rather than drift, and it worked: **the `definitions_diverge` guard was anti-correlated with its own purpose.** §7.2. |
| 4 | PACKAGE | 1 BLOCKING, 2 MAJOR, 2 MINOR | **`retire()`'s live-consumer guard was silently defeated by one declined capability.** §7.3. Also: a backend declining the optional `AttributeStore` crashed five C15 tests despite §5.5 calling it conformant — and `DegradedAdapter` could not construct one, because it re-declared the four extension methods unconditionally. `C15-08` added. |

### 7.1b Round 8, and the third instance of the same error

| # | Spec | Findings | What it caught |
|---|---|---|---|
| 8 | INTERFACE | 1 MAJOR | **`resolve_type` was blind to retired names.** [Observed]: propose → approve → retire `watch`, then `resolve_type("watch", …)` returns `outcome="proposal"`, `reason="nothing in the vocabulary fits 'watch'"`, empty `alternatives` — a clean green light for a word the registry had just read the tombstone of and discarded. A classifier that trusts it calls `propose_type` and gets the **old retired entry** back, distinguishable from a fresh success only by inspecting `.status`. That is **UC1's own shape** — an auto-approving classifier, one step earlier in the pipeline than Q6 addresses — in the call §5.3 says is *designed against mechanism 2*. Fixed with no new field: the retirement is named in `reason` with its `retire_reason` and `successor`, and listed in `alternatives` with a `None` score, exactly as §5.5 already does for a prior rejection. `C3-10`. |

| 9 | INTERFACE | 1 BLOCKING | **`retire(force=True)` lost its audit guard on Tenshen's exact declared shape.** §7.3 B6 says in terms that on a backend with `stores_events=False` a forced retirement returns `Refusal("cannot_record_override")`. The check lived *inside* the `live_consumers` branch — and with `indexes_membership=False` (B3, and B3 says that is *correct*) `gates_on` is always empty, so the branch never ran. [Observed]: a type with a real registered gating consumer retired with **no refusal, no warning and no history**. `merge_types` has had the unconditional form since v0. `C9-08`. |
| 5 | PACKAGE | 1 BLOCKING, 1 MAJOR | **The kill row itself.** §7.2b. And §3.2's central claim measured for the first time: §7.2c. |

| 10 | INTERFACE | 1 MAJOR | **One fact, four answers.** §5.10 promises *"the old word still resolves"* after a merge; §5.3 says a retired match is never `existing`. Both held — and what reconciled them was an accident: a merge writes the old name into the survivor's `aliases` and the shipped resolver happens to score an exact alias 1.0. `retire(successor=)` writes no alias, and `PACKAGE.md` §2.6 calls a caller's own resolver **the production path**, so the promise held in one of four cells. Now the registry's answer, not the resolver's, down both lifecycle paths. `C3-11`. |
| 6 | PACKAGE | 1 MAJOR, 1 MINOR | **The first defect found by asking the other question.** §7.4. |

**Four findings, one error.** Round 1's empty `alternatives` for a cross-namespace word, §7.3's `retire` reading an unknowable `gates_on` as *"nothing gates on this"*, round 8's silent tombstone, and §7.2b's unknowable extent comparing *equal* are the same mistake four times: **a confident answer standing in for a fact the system either had in hand or could not have.** Rule U is the rule this project states most loudly and breaks most often in its own implementation. Neither a reviewer's eye nor a contract test caught the family — each instance was found only when someone drove the real registry through a real scenario, which is the practice worth carrying forward.

### 7.2 The finding that changed the design: `definitions_diverge` was backwards

`merge_types` refusal #6 asks whether two definitions are near-synonymous before letting a merge proceed. v0 answered it with `difflib.SequenceMatcher` character similarity against a fixed 0.55 threshold. Round 7 measured what that actually buys. **[Observed], on the reference implementation:**

| pair | similarity | old behaviour |
|---|---|---|
| UC1 — `blocks` vs `duplicates`, two Tenshen relationship types | **0.9275** | merge proceeds |
| UC2 — the two CMS `value_set`s (`deficiency_corrected_status` vs `scope_severity_code`) | **0.8021** | merge proceeds |
| UC3 — DOT meter vs DPR tree condition, templated | **0.7465** | merge proceeds |
| **the genuinely synonymous pair** — "A Medicare-certified nursing home, identified by its CCN" vs "A nursing home certified by Medicare, identified by its CMS Certification Number" | **0.5507** | barely passes |
| UC3 — DPR tree vs 311 request `status` | 0.4972 | refused, but for the wrong reason: different words, not different meaning |

**The check was anti-correlated with its purpose.** It waved through unrelated types that shared boilerplate and came within 0.0007 of refusing a real synonym that used different words, because character similarity of prose measures **writing style, not meaning** — and an AI proposer writing to a template is the normal case, not the edge case. The consequence was a silent, permanent merge (there is no `reinstate` — Q6) in which the losing name is burned and thereafter resolves to a `TypeEntry` for the wrong concept with the wrong value list.

**Fixed, by applying Rule U to the registry's own judgement.** `NamespacePolicy.definitions_diverge_threshold` now defaults to **`None`**, meaning *"no resolver here can certify that two definitions are near-synonymous"* — so `merge_types` refuses until a human acknowledges, exactly as §5.10 already does for `no_consumer_evidence` (*"the one place we do not know blocks rather than warns"*). A deployment whose resolver **can** make that judgement sets a float and takes responsibility, the same pattern §2.7 uses for tier ordering. Two consequences:

- **Identical definitions still certify without a resolver** — that is a fact, not a judgement, and it keeps the change from being noise.
- **`MergeResult.warnings` stopped being permanently reserved.** Every merge now records `definitions_similarity:<score>` and either `definitions_threshold:<t>` or `definitions_uncertified`, so an auditor asking *"how close was this to the line?"* has an answer, and a merge that went through on an uncertified guard is visibly one nobody's resolver vouched for.

**This is the second time the loop found the same shape of error** — a number standing in for a judgement the system cannot make. The first was `resolve_type`'s empty `alternatives` (round 1). Rule U is the rule this project keeps breaking in its own implementation, which is worth knowing.

### 7.2b The kill row, tripped

`ROADMAP.md`'s kill criterion is one sentence: **"A capability predicate gets merged as a duplicate."** `INTERFACE.md` §12 says it is *"structurally blocked, not merely discouraged"*, because §5.10's refusal #2 is non-overridable. §5.10 compares the two predicates' **extents**.

**[Observed] on a backend declaring `indexes_membership=False`:**

| | `commentable` | `searchable` | `merge_types(commentable → searchable)` |
|---|---|---|---|
| fully capable | `[task]` | `[capture, task]` | `Refusal(predicate_merge)` |
| `indexes_membership=False` | `[]` | `[]` | **MERGED** |

Every extent comes back empty there, so two predicates with genuinely different members compared **equal**, the non-overridable refusal never fired, and the merge fell through to the *overridable* `no_consumer_evidence` guard — which a caller can acknowledge. **That is `PACKAGE.md` §7.3 B3's declared shape for `work_link_types`**, and B3 says the empty membership is *correct*. So the venture's kill criterion tripped on the exact backend UC1 is the fixture for, and finding 0.1's five locally-correct capability lists — the evidence that produced the whole predicate concept — would have been mergeable.

**Fixed by Rule U, again: an extent that could not be computed is not a byte-identical extent.** The refusal now fires whenever membership is unindexed, non-overridably, and says the extents were unknowable. A second, smaller defect surfaced in the same sweep: `cannot_record_override` was checked *before* the four non-overridable guards, so a caller trying to acknowledge past the kill row was told the audit log was missing rather than that the merge was forbidden — the wrong reason for the right outcome. Moved after them.

### 7.2c §3.2's claim, measured

See §6, Q7's table. The one-line version: **the sentence that lets Tenshen be a third backend was false for six of the eight capabilities it covers**, had been for four deliverables, and is now checked by [`../tools/check_capability_matrix.py`](../tools/check_capability_matrix.py) on every suite run.

### 7.3 The finding that was a live safety bug: `retire()` read blindness as absence

`retire` is guarded by `consumers`, not by usage (§5.9). It refused when `gates_on` was non-empty and proceeded when it was empty. **[Observed]:** with a real, registered, gating consumer in place, a fully capable backend refuses with `live_consumers` — and the identical registry on a backend declaring `indexes_membership=False` **retired the type, with no refusal and no warning.** Every extent is empty there, so `gates_on` is empty because nothing could be looked up.

That is **mechanism C — the silent per-consumer drop — committed by the call built to prevent it**, and it is worse than round 7's merge finding because a wrong merge is at least recorded in history and a wrong retirement was not. `merge_types` had taken the honest line for the identical uncertainty since v0; `retire` had not. It now returns `Refusal("no_consumer_evidence")`, overridable by `force=True` and recorded like any other override. Pinned by `C9-07`.

### 7.3b What the loop says about the process

**Eighteen rounds, eighteen NOT YET verdicts, and the loop did not converge** — see §7.5. Four observations worth carrying to the next spec:

1. **Six of the first eight findings were the same family** — a printed shape or signature drifted from the code. No reviewer caught them all, because each was checking by eye. A twelve-line script catches the family, found two more immediately, and now runs in the suite. **Write that check on the first spec, not the sixth round.**
2. **The reviewer brief shapes the finding.** Rounds 1–6 produced mostly drift; round 7's brief said *"six rounds found almost nothing about whether the DESIGN survives the three fixtures — push there"*, and it returned the `definitions_diverge` result. A brief that does not say what has already been mined gets what has already been mined.
3. **Two findings recurred across rounds** (Q4, and the capability-honesty family). The loop's own rule — a finding that recurs is a decision to take, not to defer — was the right call both times.
4. **The suite was wrong more often than the specs were.** Of the **fifteen** contract tests added by this row, eleven exist because the suite claimed coverage it did not have. A conformance suite that is *the definition of conformance* deserves the same adversarial pressure as the document it enforces.

### 7.4 The question nobody asked for eleven rounds

Every brief carried two halves: *can a legitimate backend **fail** the suite?* and *can a broken backend **pass** it?* **Eleven rounds attacked the first and found five defects. Nobody attacked the second until round 6 on `PACKAGE.md`, and it found one immediately.**

§3.3 gives `TypeQuery` a `limit` and an opaque `after` cursor and `TypePage` a `next_after`, ordered by `(namespace, kind, name)`, and spends real design ink justifying query objects over kwargs on exactly that machinery. **Nothing exercised any of it.** [Observed]: an adapter identical to the reference one except that it silently drops `limit` and `after` — so every page is the whole set, which in a real keyset consumer is a duplicate-forever loop — ran the whole suite to `119 passed, exit 0`, and printed the CONFORMANCE banner with no caveat. Both reference backends had implemented keyset pagination correctly since #3; nothing had ever checked.

`C0-10` now pages seven rows at `limit=3` and asserts the pages are disjoint, ordered, exhaustive and terminating. The broken adapter fails it.

**Why this is the more important half, and the one to lead with next time.** A suite that is too strict fails loudly and someone comes and asks why. **A suite that is too lax certifies something broken and nobody finds out until it is in production** — and ruling A5 makes this suite the gate that lets Tenshen depend on the package. Eleven rounds of "too strict" produced five real defects and were worth every one; the first round of "too lax" produced one in an afternoon. **The next spec's review brief should open with it.**

### 7.4b Rounds 11 and 7 — the last two, and both found real defects

| # | Spec | Findings | What it caught |
|---|---|---|---|
| 11 | INTERFACE | 1 BLOCKING | **`retire()` could not see a consumer gating on the predicate being retired.** On a *fully capable* backend, nothing unknowable: `consumers("commentable")` returned `gates_on: []` and filed the consumer of `commentable` under **`would_drop`** — backwards — and `retire("commentable")` then succeeded with no refusal. *"Which consumers gate on this?"* has two answers and v0 computed one: for an `entity` the gate predicate must **include** it; for a **predicate** the gate **is** it, and a predicate is never a member of itself. `predicates()` had the right query all along. **Mechanism C inside §2.3's "single most load-bearing idea in this document"**, and `test_c9_retire.py`'s own fixture builds the exact shape — every C9 test retired the *member*, never the predicate. `C1-09`. |
| 7 | PACKAGE | 2 MAJOR | **Two more broken backends that passed.** (a) §3.4 primitive 12 states `max(last_seen, at)` unconditionally; nothing tested it, and an adapter that overwrites instead ran clean — a replayed or out-of-order `record_use` drags `last_seen` into the past and reports a live type as **orphaned**, which §5.7 calls the sensor for the venture's core bet. Not the G3 carve-out: G3 waives serialisation under a race, not the semantic. `C7-07`. (b) `AmbiguousKind` was raised by both reference backends and referenced by **no test in the repository**; an adapter returning `rows[0]` passed — a silent wrong answer in the exact `facility`-as-entity-beside-`facility`-as-value_set case §4.1 blesses by name. `C0-11`. |

**The capability matrix caught one of my own fixes within a minute of writing it.** `C7-07` asserts a count as well as a timestamp, so it failed on a `counts_usage=False` backend — the guard built two rounds earlier flagged the new test before it was committed. That is what these checks are for.

### 7.5 Convergence, honestly — the loop did **not** converge

**The protocol asks for two consecutive fresh reviewers with no BLOCKING or MAJOR findings. That never happened.** Eighteen rounds ran — eleven on `INTERFACE.md`, seven on `PACKAGE.md` — and **every single one returned NOT YET.** The last round on each document found a defect that no earlier round had, and both were real: a guard blind to the case the document is organised around, and two more backends that passed the suite while broken.

**This row is therefore closed on an escalation, not on a clean pass.** Saying otherwise would be the exact failure the whole document is built to prevent.

**What the loop actually produced.** Twenty-six BLOCKING or MAJOR findings, every one either fixed or recorded with a written reason; **not one dismissed**. The suite grew **109 → 124**, and every addition was verified against a deliberately broken backend *before* being believed. Nine defects were in the shipped **code**, not the prose:

| | defect | where it bit |
|---|---|---|
| 1 | `Resolution`/`predicates()` returned bare lists — an empty `alternatives` standing in for *"we did not look"* | UC3, cross-namespace |
| 2 | `nonbinding` annotated but did not exempt — a conformant backend was reported as failing | the Phase 2B gate itself |
| 3 | the suite could not be passed by `stores_proposals=False` | UC1, the backend §7.4 calls conformant |
| 4 | `merge_types`' divergence guard was **anti-correlated** with its purpose | UC1 and UC2 both |
| 5 | `retire()` read an unknowable `gates_on` as *"nothing gates on this"* | UC1's declared shape |
| 6 | an unknowable extent compared **equal**, and **the kill row tripped** | UC1's declared shape |
| 7 | a forced retirement nobody could audit went unrecorded | UC1's declared shape |
| 8 | one fact — a merged-away name — had four answers depending on lifecycle path and resolver | UC1, UC2 |
| 9 | `consumers()` reported a predicate's own consumer under `would_drop`, and `retire` let it go | §2.3's "most load-bearing idea" |

**Three whole families are now machine-checked**, and each was found only after several rounds had picked at instances of it one at a time:

- [`check_spec_drift.py`](../tools/check_spec_drift.py) — fifteen printed shapes and thirteen signatures against the code. Six rounds each found one instance; the script found two more the moment it existed.
- [`check_capability_matrix.py`](../tools/check_capability_matrix.py) — every optional capability declined alone. §3.2's claim was false for **six of eight** flags and had been for four deliverables. *(It then caught one of this row's own new tests within a minute of it being written.)*
- `C0-10` and `C0-11` — the first two tests written to answer *"can a broken backend **pass**?"* rather than *"can a good one fail?"*

**Why stopping here is the honest call and not the tired one.** The tail is demonstrably not empty — a nineteenth round would probably find something. But the three families above cannot recur silently any more, and **the remaining open items needed a *ruling*, not a fix** — and while this row was still running, **they got one**: the supervisor ruled Q1–Q7 as **R6–R12** ([`../decisions/2026-08-29-3c-rulings-R6-R12.md`](../decisions/2026-08-29-3c-rulings-R6-R12.md)). Four of those rulings change the surface a reviewer reads — `search_namespaces` on `resolve_type` (R6), a `consumers()` warning (R8), name-level attribute schemas (R10), and `reinstate` with a sixteenth `Refusal.reason` (R11) — so reviewing the *current* surface has a falling return by construction.

**Recommendation: land rows 3d and 3e, then run this loop again from round one against what they produce.** Continuing now would review a surface four rulings are about to change — which is the churn the loop's own stop condition names.

**And the one instruction to carry forward:** every finding of substance in eighteen rounds came from **driving the real registry through a real scenario**. None came from reading. §7.4's asymmetry is the sharpest version of that — eleven rounds asked whether a good backend could fail, one round asked whether a bad one could pass, and the second question paid out immediately. **Open the next spec's review brief with it.**

---

---

## 8. Verdict

**UC3 was worth running, and the kill-criterion mechanism held.**

**What UC3 itself changed.** `INTERFACE.md` gained **§10b** and five contortions (8–12); `PACKAGE.md` gained **§8b** and two (B7–B8). **No call signature, data shape or refusal changed because of UC3** — every finding is an *absence*, and the ordering rule does not let a design test amend the design. The three answers the design gives to mechanism 4 all held on real data: three agencies' `status` coexist as scoped types, `cross_namespace_merge` refuses non-overridably even with `acknowledge`, and `AttributeSchema` keyed on `(namespace, kind)` lets a deployment require `unknown_encodings` of 311 and not of Parks, in one store. **`namespace` stopped being an unused field and did its job.**

**What UC3 could not do, and said so.** Contortions 8 and 9 are the two that matter: a proposer in one agency's namespace is never told the word is taken in another, and nothing can record that two scoped types denote the same thing. Both are recorded, both have a recommendation, and neither is fixed here.

**What the adversarial loop changed, which was more.** Eighteen rounds, **eighteen NOT YET verdicts, no clean pass** (§7.5). Twenty-six BLOCKING/MAJOR findings, none dismissed. **Nine were defects in the shipped code**, including the venture's own kill criterion tripping on Tenshen's declared capability shape. The contract suite went **109 → 124**, and three whole families of defect are now machine-checked rather than looked for by eye.

**The honest state of the two specs.** Both are materially more correct than when this row opened and **neither has earned a clean review pass.** Seven of the eight questions were **ruled while this row was in flight** (§6 — R6–R12), and four of those rulings will change the surface: `search_namespaces` (R6), a `consumers()` warning (R8), name-level attribute schemas (R10), `reinstate` and a sixteenth `Refusal.reason` (R11). **Q8 (pagination in the façade) post-dates the ruling file and is open.** The next loop belongs after rows 3d and 3e, not before them.

**The kill row.** It tripped, on Tenshen's own declared capability shape, and was fixed before any real merge. The supervisor judged that an implementation defect in the guard rather than the design flattening a true distinction, and **the row stays armed** — while recording that the founder may read it the other way, since a guard that silently failed on the very backend it was written for is arguably a design-level failure. **That call is the founder's, and this document does not make it.**

**For the record, the thing most worth repeating:** every finding of substance in eighteen rounds came from **driving the real registry through a real scenario**. Not one came from reading either document.
