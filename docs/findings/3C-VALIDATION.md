# 3C — the use-case validation pass: UC3 (NYC Open Data) against INTERFACE v0 and PACKAGE v0

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
