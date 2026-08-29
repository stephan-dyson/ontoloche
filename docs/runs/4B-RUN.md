# 4B-RUN — roadmap row 4b: EDGES v0 implemented, and what it cost the specification

**Row:** 4b. **Date:** 2026-08-29. **Repo:** [`open-ontology`](https://github.com/stephan-dyson/open-ontology), `main`.
**What it carried:** [`docs/specs/EDGES.md`](https://github.com/stephan-dyson/open-ontology/blob/main/docs/specs/EDGES.md) v0 — the reference edge store, `neighbors`, and edge conformance — plus rulings **R17**–**R26** applied to it, and **R31** (standing constraint 8) folded in after the row started.
**Why it ran next:** Tenshen slices 1–2 (the `neighbors` read seam, the `relations` slot) and beacon 21.2 need a **real** edge store to build against, not only a specification. Row #4 shipped no implementation on purpose; this is its 2A.

---

## 1. The headline, in numbers

| | before (row 3e) | after |
|---|---|---|
| adapter primitives ([`PACKAGE.md`](https://github.com/stephan-dyson/open-ontology/blob/main/docs/specs/PACKAGE.md) §3.4) | 15 | **18** |
| contract ids (§6.2) | 150 | **189** |
| sync suite, one run | `388 passed, 80 skipped` | **`470 passed, 115 skipped`** |
| async suite, one run | `421 passed, 80 skipped` | **`506 passed, 115 skipped`** |
| `Capabilities` flags | 10 + 2 declarations | **14 + 5 declarations** |
| store schema version | 3 | **4** |
| `warnings` values (`INTERFACE.md` §5.4) | 20 | **21** |
| `Refusal.reason` values (§5.12) | 21 | **21** — row #4 had already added all four |
| `check_spec_drift.py` | 15 shapes, 14 calls, 2 vocabularies | **+3 PACKAGE shapes, +1 rule-coverage gate (R31)** |
| registry facade calls | 14 + 3 package-local | **14 + 3 package-local, and 3 edge calls** |

**Thirty-nine new ids: twenty-nine in `C17` and ten in `C18`.** Nothing here came from a ruling that had not already been made — the whole of row #4's design was ruled in `R17`–`R26` before the row started — so the ratio that matters is a different one: **ten of the twenty-nine `C17` ids exist to hold a BLOCKING finding that row #4's own adversarial loop had already found and fixed *in a throwaway probe kit the package does not import*.** §3 is about that.

---

## 2. The two suite tails, verbatim

### 2.1 Sync — `pytest --pyargs open_ontology.contract -q`

```
CONFORMANCE (PACKAGE.md 6.1)
  backends exercised: postgres, sqlite, sqlite_minimal
  resolver: the shipped DeterministicResolver (2.6's fixed point)
  nonbinding tests excluded from the verdict: none
  coverage, per leg (PACKAGE.md 6.4 / ruling R12):
    sqlite          CONFORMANT: 186 ids exercised, 1 not exercisable on this backend (listed)
                      1: PACKAGE.md 5.7 -- this backend stores arbitrary attributes, so a census restricted to its
                        projections has no subject here. C15-02 is the full case.
                         C15-09
    postgres        CONFORMANT: 186 ids exercised, 1 not exercisable on this backend (listed)
                      1: PACKAGE.md 5.7 -- this backend stores arbitrary attributes, so a census restricted to its
                        projections has no subject here. C15-02 is the full case.
                         C15-09
    sqlite_minimal  CONFORMANT: 74 ids exercised, 113 not exercisable on this backend (listed)
                      32: PACKAGE.md 3.2 -- this backend declares stores_edges=False, which 3.2 says is conformant.
                        This test needs it as scaffolding, not as its subject: this store is a type registry only: no
                        table holds relationships, so there is nothing to write an edge to and nothing for a neighbour
                        walk to read
                      22: PACKAGE.md 3.2 -- this backend declares indexes_membership=False, which 3.2 says is
                        conformant. [...]
                      22: PACKAGE.md 3.2 -- this backend declares stores_proposals=False, which 3.2 says is
                        conformant. [...]
                      21: PACKAGE.md 3.2 -- this backend declares stores_events=False, which 3.2 says is conformant.
                        [...]
                      12: PACKAGE.md 3.2 -- this backend declares stores_attributes=False, which 3.2 says is
                        conformant. [...]
                      1: PACKAGE.md 3.2 -- this backend declares stores_edges=False, so add_edge refuses
                        `edge_store_absent` before it can reach the declaration check. The registration half above ran
                        and held on this store.
                         C17-29
                      1: PACKAGE.md 7.3 B4 -- [...] C0-08
                      1: PACKAGE.md 9.3 -- [...] C0-05
    (+2 backend-independent, run once: C0-04, C14-07)
  A conformance claim without its coverage line is not a claim (ruling R12).
470 passed, 115 skipped in 170.66s (0:02:50)
```

*(The five long `requires_capability` reasons are elided with `[...]` only where they are unchanged from [`3E-RUN.md`](https://github.com/stephan-dyson/open-ontology/blob/main/docs/runs/3E-RUN.md) §2.1; the new ones are printed in full. The run prints all of them.)*

**`sqlite_minimal` goes 70 → 74 ids exercised and 78 → 113 not exercisable, and both halves of that are the point.** It declares `stores_edges=False` **natively** — `oo_edge` is absent from its SQL, not hidden behind a Python `if` — so 32 `C17`/`C18` ids skip there with the backend's own sentence. The four it *gains* are the ones whose subject IS the declined capability: `C17-01` (every edge call refuses rather than returning an empty report), `C17-25`, `C17-27` and `C17-29`.

### 2.2 Async — `pytest --pyargs open_ontology.aio.contract -q`

Same three legs, same per-leg numbers:

```
CONFORMANCE (PACKAGE.md 6.1)
  backends exercised: postgres, sqlite, sqlite_minimal
  resolver: the shipped DeterministicResolver (2.6's fixed point)
  nonbinding tests excluded from the verdict: none
  coverage, per leg (PACKAGE.md 6.4 / ruling R12):
    sqlite          CONFORMANT: 186 ids exercised, 1 not exercisable on this backend (listed)
    postgres        CONFORMANT: 186 ids exercised, 1 not exercisable on this backend (listed)
    sqlite_minimal  CONFORMANT: 74 ids exercised, 113 not exercisable on this backend (listed)
    (+2 backend-independent, run once: C0-04, C14-07)
  A conformance claim without its coverage line is not a claim (ruling R12).
506 passed, 115 skipped in 178.93s (0:02:58)
```

The async tree is generated by [`tools/unasync.py`](https://github.com/stephan-dyson/open-ontology/blob/main/tools/unasync.py) and `test_generated_matches_source.py` fails if it has drifted. It refused to emit twice during this row and was right both times — see §5, D-4b-7.

### 2.3 The capability matrix — `py docs/tools/check_capability_matrix.py`

```
PACKAGE.md 3.2 -- every OPTIONAL capability, declined one at a time.
required and never declinable: enforces_unique_name, transactional

  configuration                  verdict   passed  skipped  failed
  stores_proposals=False         conformant    168       28       0
  stores_events=False            conformant    164       32       0
  stores_attributes=False        conformant    146       50       0
  stores_aliases=False           conformant    186       10       0
  indexes_membership=False       conformant    150       46       0
  counts_usage=False             conformant    182       14       0
  timestamps_usage=False         conformant    187        9       0
  owns_schema=False              conformant    190        6       0
  stores_edges=False             conformant    157       39       0
  stores_edge_events=False       conformant    189        7       0
  indexes_edges_by_family=False  conformant    189        7       0
  stores_edge_attributes=False   conformant    189        7       0
  no AttributeStore              conformant    183       13       0
  stores_attributes=False +proj  conformant    146       50       0
  stores_edge_attributes=F +proj conformant    189        7       0
```

**Twelve configurations became fifteen**, and the four edge flags are ordinary members of `CAPABILITY_FLAGS` rather than a separate tuple precisely so this script reaches them without being told about them. The fifteenth is beacon finding **U3**'s shape one row down: a host-owned edge table with `description` and `confidence` as real typed columns and no JSON blob.

---

## 3. What the ids are for, and the ratio worth reading

Row #4's adversarial loop found **ten BLOCKING and ten MAJOR** defects across three rounds, every one reproduced by running code, three of them defects in the previous round's own fix. All ten BLOCKING were fixed — **in [`docs/tools/edges_probe_kit.py`](https://github.com/stephan-dyson/open-ontology/blob/main/docs/tools/edges_probe_kit.py), a throwaway module the package does not import and the contract suite does not know exists.**

So on the morning this row started, every one of those ten was fixed **nowhere a backend author could be held to**. That is the single largest thing this row did, and it is why `C17` is twenty-nine ids rather than twelve:

| row #4's finding | now held by |
|---|---|
| **B1** `equivalent_to` declared an endpoint kind §1 banned | `C17-27` |
| **B2** `edge_families=None` silently dropped every family outside the named namespace — Cause C in the read seam | `C17-13` |
| **B3** a permissive family could declare `predicate` endpoints and write the kill row | `C17-09` |
| **B4** `direction` was silently wrong for symmetric families — a confident, complete, false negative | `C17-16` |
| **B5** `depth_reached` misreported a dead end under the API's own default direction | `C17-17` |
| **B7** the assembly bound double-counted re-found edges, dropping four real ones and naming a bound nothing crossed | `C17-18` |
| **B8** the bound was opt-in, so the default was the unbounded fetch R13 exists to prevent | `C17-18` |
| **B9** `retract_edge` inherited the durability warning instead of stamping it | `C17-21` |
| **B10** §4.3's table still contradicted §4.1 about `known` | `C17-22`, and the row itself is now `4.3-5` with an id |
| **M9** the three adapter primitives were never instantiated | `C17-01`…`C17-07` |
| **M10** the `EventRecord.edge_id` amendment was claimed twice and made nowhere | `C17-26`, and store version 4 |
| **B6, M11** the document miscounted its own review rounds, twice | *nothing here can hold that; §6 is the answer* |

**And `C18` does the same for the design tests.** Row #4 walked UC1, UC2 and UC3 through the probe kit; `C18` walks the same fixtures through `open_ontology.Registry` on three reference legs, against the same **pre-registered** numbers. Every one reproduces: CMS `400 / 69 / 400` over `92` distinct tags and `10` facilities; NYC `25` complaints over `22` BBLs, `54` census trees, `102` edges, `18 of 25` matched, `max 16` trees on one lot.

---

## 4. Ruling R31 — the rule→id mapping, as the supervisor asked

**R31 (standing constraint 8), ruled after this row started:** *every numbered rule in a spec section ships with either a contract id that exercises it or an explicit `prose-only` tag with a reason, and `check_spec_drift.py` fails on a rule with neither.* Row 4b maps `EDGES.md` §2.4.1, §4.3 and §4.4 first, since it is the row implementing them.

**The mapping lives in the specification, not beside it.** Each of the three sections now carries a rule table whose last column names the ids; [`check_spec_drift.py`](https://github.com/stephan-dyson/open-ontology/blob/main/docs/tools/check_spec_drift.py) reads those tables and holds them against the suite. A dict in the checker would have been a *third* artefact to keep in step with two others — which is the exact shape of drift the constraint exists to catch — and a reader of §4.3 would have had to open a Python file to learn which id holds a row.

### 4.1 `EDGES.md` §2.4.1 — the endpoint rules

| rule | exercised by |
|---|---|
| **2.4.1-1** instance level accepts only `entity` endpoints | `C17-09`, `C18-04` |
| **2.4.1-2** type level accepts any registered kind except `predicate`, `edge` included | `C17-27`, `C18-05` |
| **2.4.1-3** `predicate` excluded at both levels, as a general rule | `C17-09` |
| **2.4.1-4** all three clauses bind at DECLARATION time; the write-time check still runs | `C17-08`, `C17-09` |
| **2.4.1-5** a breaching declaration is refused at every door | `C17-09` |
| **2.4.1-6** `equivalent_to` requires `src.kind == dst.kind` | `C17-08` |
| **2.4.1-7** `endpoint_kinds` constrains the KIND, not the TYPE | **`prose-only`** — deviation **D-4b-3** |

### 4.2 `EDGES.md` §4.3 — the uncertainty table

Thirteen rows, twelve from the specification and one added by implementing it.

| rule | exercised by |
|---|---|
| **4.3-1** no edge store ⇒ `edge_store_absent`, never an empty report | `C17-01` |
| **4.3-2** an unknown named family refuses the whole call | `C17-14` |
| **4.3-3** a retired family is searched and warned about | `C17-15` |
| **4.3-4** `edge_families=None` spans every namespace | `C17-13` |
| **4.3-5** `EdgePage.known` may be `None`; `NeighborReport.known` never is | `C17-19`, `C17-22` |
| **4.3-6** ran out of graph ⇒ `complete=True` | `C17-17` |
| **4.3-7** cut short ⇒ `complete=False` with a `why` | `C17-18`, `C17-19` |
| **4.3-8** a suppressed retracted edge ⇒ `complete=False` | `C17-20` |
| **4.3-9** a family in another namespace ⇒ `edge_family_unknown` | `C17-14` |
| **4.3-10** an unregistered origin type warns; the walk proceeds | `C17-11` |
| **4.3-11** a READ over a savepoint scope adds nothing | `C17-21` |
| **4.3-12** no `UnknownNode` exception | `C17-11` |
| **4.3-13** *(new)* an edge whose family is registered nowhere is RETURNED, warned | `C17-13` |

### 4.3 `EDGES.md` §4.4 — completeness and entailment

| rule | exercised by |
|---|---|
| **4.4-1** `complete` can be `True`, because an edge is a stored row | `C17-22` |
| **4.4-2** `complete` is over `families_searched`, which is therefore required | `C17-22`, `C18-06` |
| **4.4-3** `at_depth` separates reachability from entailment | `C17-23`, `C18-05` |
| **4.4-4** the comparison is with the two carriers that are ALWAYS `False` | **`prose-only`** — a correction to this document's own prose; `C6-04` binds the type-side claim |

### 4.4 The gate was watched failing, four ways

A checker nobody has watched fail is a checker nobody knows works — row 3e proved that when the §5.12 count check silently stopped parsing the moment the vocabulary reached a hyphenated number word. Four mutations, each restored afterwards:

```
  CAUGHT  an empty `exercised by` cell
          - EDGES 4.3-1: neither a contract id nor a `prose-only:` tag (ruling R31 ...)
  CAUGHT  a contract id no test claims
          - EDGES 4.3-2: names C17-99, and no test in the suite claims that id
  CAUGHT  a `prose-only:` tag with no reason
          - EDGES 4.4-4: tagged `prose-only:` with no reason -- R31 requires the reason ...
  CAUGHT  a rule deleted from the table and left in the prose
          - EDGES 4.3: the rule numbers are [... 12, 14], not [... 12, 13] -- a gap is a rule
            somebody deleted from the table and left in the prose
```

**What the gate does NOT do, stated rather than implied:** it cannot see a rule added to a section's *prose* and never added to that section's *table*. It compares the table to the suite, which is two of the three sides. The third side is what the adversarial loop is for, and `EDGES.md` §17.5 is honest about what that is worth.

---

## 5. Deviations — every place the implementation could not follow the document as written

**None is silently resolved.** Where the document and the code disagree, the document was amended (and §4 says which sections), or the disagreement is recorded here.

| # | Deviation | Why, and what was done |
|---|---|---|
| **D-4b-1** | **`Registry.edge_provenance(edge_id)` is a call `EDGES.md` never specifies.** §6's capability table promises that `stores_edge_events=False` gives *"`provenance(edge).history == []` with the `why`"*, and no section anywhere defines such a read | Supplied as a **package-local** helper, the standing `attribute_census`, `import_types` and `register_attribute_schema` already have — not as a fifteenth `INTERFACE.md` §5 call, because EDGES v0's stated surface is two writes and one read. `neighbors` and `add_edge` return `history=()` with a `history_why` naming this call, rather than letting `()` read as *"nothing happened"*: fetching events per edge is one `read_events` per row of the report, which on the 9.7M-degree node §4.2 measures is the whole reason the read seam is bounded. `C17-26` |
| **D-4b-2** | **`read_events` gains an `edge_id` filter — primitive 15's signature changed.** §5.2's `EventRecord.edge_id` amendment gives an edge event somewhere to live and nothing to read it back by | Additive and defaulted, so a caller that never passes it sees exactly the pre-4b behaviour and `read_events(namespace)` with no filter still returns edge events, because they are events. `PACKAGE.md` §3.4 primitive 15 amended in the same change |
| **D-4b-3** | **`endpoint_kinds` constrains the KIND of an endpoint and not its TYPE.** §2.4 motivates the field with *"a citation edge must not accept a facility at the tag end"* — and it cannot express that, because a citation and a facility are both `entity`. What CMS actually gets from §2.4.1 is the entity-vs-`value_set` exclusion | **Recorded, not designed away.** The CMS vocabulary rows keep `from`/`to` alongside the five keys, as unvalidated payload, because that is where the fact currently lives. Tagged `prose-only` under R31 with this deviation named. **Q28** asks whether §2.4 should gain an endpoint *type* constraint or whether the motivating sentence should be narrowed |
| **D-4b-4** | **A family's declared shape lives in `TypeEntry.attributes`, so a backend with `stores_attributes=False` cannot DECLARE a family at all** — its `level` does not round-trip and `add_edge` then refuses `attributes_schema_violation` however capable its edge store is | The escape hatch is the one `PACKAGE.md` §5.7 already built: such a backend names the five keys in `attribute_projections` and they round-trip through its own typed columns — which is the shape beacon's `work_link_types` already has for two of them (`is_symmetric`, `inverse_label`). Measured by the capability matrix, skipped with a reason in `C17`, and `C17-27` asserts what it costs on `sqlite_minimal` rather than skipping past it |
| **D-4b-5** | **A `kind="edge"` entry that declares none of the five keys is registered, not refused.** §2.4 says `level` is REQUIRED with no default | `INTERFACE.md` §2.1 requires no attributes at all, and **beacon's `work_link_types` rows carry none of the five** — `C14-01` seeds exactly such a row. Refusing the registration would make this row reject types the interface says are legal, on the data of the one real host. The refusal is at WRITE time, which is where the door shuts: no edge can be written on a family that declared nothing. `C17-29` |
| **D-4b-6** | **`payload_schema` is still inert, and the reason it was inert has gone.** §2.5 declares it inert *"until R10 lands"* — and **R10 landed in row 3e** | Wiring it would mean validating `Edge.attributes` against a name-level `AttributeSchema`, with modes, versions and an `attr_schema_version` on every edge: a mechanism, not a field. Not in this row's brief and not built. **Q29** asks whether 4c takes it or whether `payload_schema` is removed per §13's own rule — *"if R10 does not land, `payload_schema` is removed rather than left as a `None` that never becomes anything"* — which now reads the other way round |
| **D-4b-7** | **`neighbors` pushes `direction` to the adapter only when nothing in scope is symmetric.** §7.1's printed `EdgeQuery` has a `direction` and no way to say which families are symmetric, so an adapter cannot honour §4.1's per-family rule | Resolved **without amending `EdgeQuery`**: with any symmetric family in scope the adapter is asked for both orientations and the registry narrows per family above it — the same division `indexes_edges_by_family=False` already uses, and it keeps §7.1's shape exactly as printed. The registry narrows **always**, so one code path decides what is in a report rather than two that must agree; the store-side filter is then an efficiency claim and `C17-06` binds it at the primitive |
| **D-4b-8** | **`neighbors` guards against a pagination cursor that never advances.** Not in `EDGES.md` | `C0-10` asked whether a BROKEN backend can pass; the answer for a per-level exhaustion loop must not be *"it hangs"*. The walk stops and reports `complete=False` with a `why` naming the backend. `C17-19`, `C17-24` |
| **D-4b-9** | **`edge_family_unregistered:<namespace>:<name>` is a warning value the specification did not have.** §4.3 had no row for an edge whose family is registered nowhere, and §2.7 plus §7.2 make that reachable on purpose | Minted and added to `INTERFACE.md` §5.4 **in the same change**, per ruling R3, and added to §4.3 as rule `4.3-13`. The edge is returned, never dropped — dropping it is the silent per-consumer drop §12 names as this document's dominant mechanism, in its only read call, on exactly the host §7.2 maps |
| **D-4b-10** | **Adding primitives 16–18 to `StorageAdapter` breaks `isinstance` for every adapter written against the fifteen.** `StorageAdapter` is `runtime_checkable`, and ruling R30 records the same hazard for `AttributeStore` | Taken deliberately, because `EDGES.md` §6 puts the four flags on `Capabilities` and §7.1 gives the primitives the `stores_proposals=False` treatment — methods that exist and raise. **Nothing in this package calls `isinstance(x, StorageAdapter)`**, so the breakage is nominal; it is recorded because a third-party author who does call it will see it. `stores_edges` defaults to `False` so a pre-4b adapter's edge calls refuse honestly rather than crashing |
| **D-4b-11** | **The `edge_family_retired` warning fires only for a family the caller NAMED**, not for a retired family reached through `edge_families=None` | `EDGES.md` §2.8's carrier table says *"a named family is retired"*, and this follows it literally rather than widening a closed vocabulary's meaning by implementation. **Q30** asks whether a `None` walk should warn per retired family it consulted, or whether that is noise at scale |
| **D-4b-12** | **`find_edges` counts suppressed retracted edges with an extra query per page.** §4.3 rule 8 requires `complete=False` when a retracted edge was hidden, and only the adapter can know | Counted over the whole matching set rather than the page, because a caller told `complete=True` on page one and `complete=False` on page three has been told two different things about one query. The cost is one indexed count per `find_edges` call with `include_retracted=False`, and it is stated rather than discovered |

---

## 6. The adversarial review loop

*(Standing constraint 7. This section is written **after** the loop runs, never before it — row #4's own §17 recorded its exit-criteria table claiming two rounds while §17 recorded one, which was a BLOCKING finding of its round 2. See §6.1 below for the live state.)*

### 6.1 Round log

*Pending — the loop has not run at the time of writing. This sentence is the honest state and is replaced by the log, not deleted.*

---

## 7. Questions for the supervisor — **Q27 onward**

Numbering continues from Q26 (ruled as R31). None is taken on this row's authority.

| # | Question | Recommendation | Founder-visible? |
|---|---|---|---|
| **Q27** | **`equivalent_to`'s `src.kind == dst.kind` constraint is hard-coded to one family name.** §2.4.1 says plainly that it is *"that family's semantics and not a general mechanism"*, so the registry knows one rule about one word. Should it become a sixth declarable key (`same_kind_endpoints: bool`)? | **No, and record it.** A sixth attribute invented for one family is how a declared shape starts growing a rule language, which is exactly what R18 accepted *narrowly*. Revisit when a second family needs it | No |
| **Q28** | **`endpoint_kinds` cannot express the constraint §2.4 uses to motivate it** (D-4b-3): a citation and a facility are both `entity`, so *"a citation edge must not accept a facility at the tag end"* is unexpressible. CMS carries the fact in unvalidated `from`/`to` | **Narrow the sentence, do not widen the mechanism.** An endpoint *type* constraint is a second identity triple per end and a second thing to keep in step with the endpoints; the honest v0 move is for §2.4 to say what `endpoint_kinds` does. Phase 3's ingestion loop is the consumer that would force more | No |
| **Q29** | **`payload_schema` is inert and its blocker has gone** (D-4b-6): §2.5 declares it inert until **R10**, and R10 landed in row 3e. §13's own rule says an unlandable `payload_schema` should be *removed* rather than left as a `None` that never becomes anything — which now reads the other way round | **Take it in 4c**, with edge payload validation as its own row: modes, versions, `attr_schema_version` on the edge, and `C15`'s shape transposed. It is the one part of the edge model with a declared field and no mechanism, and E10 is the cost UC1 is already paying | No |
| **Q30** | **A retired family reached through `edge_families=None` is searched and NOT warned about** (D-4b-11), because §2.8's carrier table says *"a named family"*. At scale a `None` walk over a store with fifty retired families would emit fifty warnings | **Keep the literal reading for v0 and revisit with Phase 3's ingestion loop**, which is the first caller that will use `None` at scale. The alternative — a count rather than a list — is a new warning shape, and the vocabulary is closed | No |
| **Q31** | **`neighbors` is bounded by `max_edges` at the REGISTRY, so two registries over one store can disagree about what `complete` means.** The bound is a deployment parameter (`Registry(max_edges=…)`), which is what makes it a circuit breaker rather than something a caller can raise per call | **Accept for v0 and record.** It is the same shape as `NamespacePolicy`, which is already per-registry, and R25 has routed the real question (façade paging) to Phase 3 with R13 | No |

---

## 8. What this row did NOT do

- **No `payload_schema` validation** (D-4b-6, Q29). The field is specified, stored and never read.
- **No `narrower_than`, no second family.** §3.3 declined it and none of the three fixtures asked for it here either.
- **No façade paging.** R13 stands, R25 routed the 9.7M-degree node to Phase 3, and the assembly bound tells the truth without solving it.
- **No tenancy dimension.** R24, and `C18-09` asserts that `user_id` is *not* mapped onto `namespace`.
- **Nothing in beacon was edited, imported or executed**, and nothing of beacon's is vendored. `C18-09`/`C18-10` carry column names and a shape, read once, read-only, from row #4's own §7.2 table.
