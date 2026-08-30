# 4B-RUN — roadmap row 4b: EDGES v0 implemented, and what it cost the specification

> **Package renamed** `open_ontology` → `ontoloche` at commit 802ddf0 (2026-08-30); the commands and paths quoted below are as recorded at the time.

**Row:** 4b. **Date:** 2026-08-29. **Repo:** [`open-ontology`](https://github.com/stephan-dyson/open-ontology), `main`.
**What it carried:** [`docs/specs/EDGES.md`](https://github.com/stephan-dyson/open-ontology/blob/main/docs/specs/EDGES.md) v0 — the reference edge store, `neighbors`, and edge conformance — plus rulings **R17**–**R26** applied to it, and **R31** (standing constraint 8) folded in after the row started.
**Why it ran next:** Tenshen slices 1–2 (the `neighbors` read seam, the `relations` slot) and beacon 21.2 need a **real** edge store to build against, not only a specification. Row #4 shipped no implementation on purpose; this is its 2A.

---

## 1. The headline, in numbers

| | before (row 3e) | after |
|---|---|---|
| adapter primitives ([`PACKAGE.md`](https://github.com/stephan-dyson/open-ontology/blob/main/docs/specs/PACKAGE.md) §3.4) | 15 | **18** |
| contract ids (§6.2) | 150 | **194** |
| sync suite, one run | `388 passed, 80 skipped` | **`480 passed, 120 skipped`** |
| async suite, one run | `421 passed, 80 skipped` | **`516 passed, 120 skipped`** |
| `Capabilities` flags | 10 + 2 declarations | **14 + 5 declarations** |
| store schema version | 3 | **4** |
| `warnings` values (`INTERFACE.md` §5.4) | 20 | **22** |
| `Refusal.reason` values (§5.12) | 21 | **21** — row #4 had already added all four |
| `check_spec_drift.py` | 15 shapes, 14 calls, 2 vocabularies | **+3 PACKAGE shapes, +6 EDGES shapes, +18 primitive signatures, +1 rule-coverage gate (R31)** |
| registry facade calls | 14 + 3 package-local | **14 + 3 package-local, and 3 edge calls** |

**Forty-four new ids: thirty-four in `C17` and ten in `C18`.** Nothing here came from a ruling that had not already been made — the whole of row #4's design was ruled in `R17`–`R26` before the row started — so the ratio that matters is a different one: **ten of `C17`'s ids exist to hold a BLOCKING finding that row #4's own adversarial loop had already found and fixed *in a throwaway probe kit the package does not import*,** and **five more came from row 4b's own loop** (§6). §3 is about the first ten.

> **These numbers were measured, and the first draft of this table did not measure two of them.** It wrote `476 / 512` by arithmetic — the previous run plus two new ids × two new tests — and the suites actually report `474 / 510`, because the new ids skip on `sqlite_minimal`. Nothing turned on the difference, which is exactly why it is worth recording: this repository has been bitten four times by a number in prose that nothing derives, and a *predicted* number is that same defect with better intentions. Caught by re-running rather than by re-reading.

---

## 2. The two suite tails, verbatim

### 2.1 Sync — `pytest --pyargs open_ontology.contract -q`

```
CONFORMANCE (PACKAGE.md 6.1)
  backends exercised: postgres, sqlite, sqlite_minimal
  resolver: the shipped DeterministicResolver (2.6's fixed point)
  nonbinding tests excluded from the verdict: none
  coverage, per leg (PACKAGE.md 6.4 / ruling R12):
    sqlite          CONFORMANT: 191 ids exercised, 1 not exercisable on this backend (listed)
                      1: PACKAGE.md 5.7 -- this backend stores arbitrary attributes, so a census restricted to its
                        projections has no subject here. C15-02 is the full case.
                         C15-09
    postgres        CONFORMANT: 191 ids exercised, 1 not exercisable on this backend (listed)
                      1: PACKAGE.md 5.7 -- this backend stores arbitrary attributes, so a census restricted to its
                        projections has no subject here. C15-02 is the full case.
                         C15-09
    sqlite_minimal  CONFORMANT: 74 ids exercised, 118 not exercisable on this backend (listed)
                      37: PACKAGE.md 3.2 -- this backend declares stores_edges=False, which 3.2 says is conformant.
                        This test needs it as scaffolding, not as its subject: this store is a type registry only: no
                        table holds relationships, so there is nothing to write an edge to and nothing for a neighbour
                        walk to read
                         C17-02, C17-03, C17-04, C17-05, C17-06, C17-07, C17-08, C17-11, C17-12, C17-13, C17-14, C17-15,
                           C17-16, C17-17, C17-18, C17-19, C17-20, C17-21, C17-22, C17-23, C17-24, C17-26, C17-30, C17-31,
                           C18-01, C18-02, C18-03, C18-04, C18-05, C18-06, C18-07, C18-08, C18-09, C18-10
                      23: PACKAGE.md 3.2 -- this backend declares indexes_membership=False, which 3.2 says is
                        conformant. [...]
                         C1-04, C1-09, C10-01, C10-02, C11-01, C12-01, C12-05, C12-06, C17-28, C2-01, C2-03, C2-04,
                           C2-05, C3-10, C4-08, C6-01, C6-03, C9-01, C9-02, C9-03, C9-04, C9-11, C9-15
                      22: PACKAGE.md 3.2 -- this backend declares stores_proposals=False, which 3.2 says is
                        conformant. [...]
                         C15-03, C15-06, C17-10, C3-06, C3-07, C4-02, C4-04, C4-05, C5-01, C5-03, C5-04, C5-05, C5-06,
                           C5-07, C5-08, C5-09, C5-10, C5-11, C6-06, C8-01, C8-02, C8-05
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
480 passed, 120 skipped in 237.77s (0:03:57)
```

*(Reasons unchanged from [`3E-RUN.md`](https://github.com/stephan-dyson/open-ontology/blob/main/docs/runs/3E-RUN.md) §2.1 are elided with `[...]`; the new ones and every id list are printed in full. The run itself prints all of them.)*

**`sqlite_minimal` goes 70 → 74 ids exercised and 78 → 118 not exercisable, and both halves are the point.** It declares `stores_edges=False` **natively** — `oo_edge` is absent from its SQL, not hidden behind a Python `if` — so 37 `C17`/`C18` ids skip there with the backend's own sentence, one more skips for a reason specific to the declaration check, and `C17-28` skips on `indexes_membership` and `C17-10` on `stores_proposals`. The four it *gains* are the ones whose subject IS a declined capability: `C17-01` (every edge call refuses rather than returning an empty report), `C17-25`, `C17-27` and `C17-29`.

### 2.2 Async — `pytest --pyargs open_ontology.aio.contract -q`

Same three legs, same per-leg numbers:

```
CONFORMANCE (PACKAGE.md 6.1)
  backends exercised: postgres, sqlite, sqlite_minimal
  resolver: the shipped DeterministicResolver (2.6's fixed point)
  nonbinding tests excluded from the verdict: none
  coverage, per leg (PACKAGE.md 6.4 / ruling R12):
    sqlite          CONFORMANT: 191 ids exercised, 1 not exercisable on this backend (listed)
    postgres        CONFORMANT: 191 ids exercised, 1 not exercisable on this backend (listed)
    sqlite_minimal  CONFORMANT: 74 ids exercised, 118 not exercisable on this backend (listed)
    (+2 backend-independent, run once: C0-04, C14-07)
  A conformance claim without its coverage line is not a claim (ruling R12).
516 passed, 120 skipped in 171.71s (0:02:51)
```

The async tree is generated by [`tools/unasync.py`](https://github.com/stephan-dyson/open-ontology/blob/main/tools/unasync.py) and `test_generated_matches_source.py` fails if it has drifted. It refused to emit twice during this row and was right both times — see §5, D-4b-7.

### 2.3 The capability matrix — `py docs/tools/check_capability_matrix.py`

```
PACKAGE.md 3.2 -- every OPTIONAL capability, declined one at a time.
required and never declinable: enforces_unique_name, transactional

  configuration                  verdict   passed  skipped  failed
  stores_proposals=False         conformant    173       28       0
  stores_events=False            conformant    168       33       0
  stores_attributes=False        conformant    146       55       0
  stores_aliases=False           conformant    191       10       0
  indexes_membership=False       conformant    154       47       0
  counts_usage=False             conformant    187       14       0
  timestamps_usage=False         conformant    192        9       0
  owns_schema=False              conformant    195        6       0
  stores_edges=False             conformant    157       44       0
  stores_edge_events=False       conformant    194        7       0
  indexes_edges_by_family=False  conformant    194        7       0
  stores_edge_attributes=False   conformant    194        7       0
  no AttributeStore              conformant    188       13       0
  stores_attributes=False +proj  conformant    146       55       0
  stores_edge_attributes=F +proj conformant    194        7       0
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
| **2.4.1-2** type level accepts any registered kind except `predicate`, `edge` included | `C17-30`, `C17-27`, `C18-05` |
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
| **4.3-14** *(new)* the origin's type is joined to another by a merge, so the walk is `complete=False` and says which other name holds edges it did not search | `C17-33` |

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

**What the gate does NOT do, stated rather than implied.** Two things, and round 1 of this row's own loop found the second one by walking into it.

1. It cannot see a rule added to a section's *prose* and never added to that section's *table*. It compares the table to the suite, which is two of the three sides.
2. **It verifies that a named id EXISTS. It cannot verify that the id asserts the rule it is mapped to** — and it never will, because that is a judgement about what a test means, not a fact about a file. Round 1 found rule `2.4.1-2` mapped to two ids, neither of which wrote a `kind="edge"` endpoint: the rule was claimed as exercised and was not. **That is the failure R31 exists to prevent, found inside the row that built R31's gate.** The mapping needs a reader. §6.2 is what the reader found.

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
| **D-4b-15** | **A merge splits an edge endpoint's identity, and `neighbors` does not follow it.** `merge_types` retires one word with the other as its `successor` and **rewrites no edge** — an edge's endpoints are references by identity triple (§2.1) and nothing in this package edits a stored reference. So edges written before a merge keep naming the absorbed word | **The report is made honest; the walk is not made clever.** It carries `endpoint_type_merged:<ref>`, `complete=False`, and a `why` naming the other name (rule `4.3-14`, `C17-33`). It does **not** follow the chain and return those edges: whether an edge written under a merged word is an edge of its survivor is a decision above this row, and making it silently would change what `neighbors` means. **Q33.** *(Before this the walk from the canonical type — the CORRECT thing to do after a merge — returned `known=0`, `complete=True` and an empty `warnings`, which contradicts §4.4's own argument for why `complete` may ever be `True`.)* |
| **D-4b-16** | **Retracting an already-retracted edge overwrites the first retraction's reason, actor and timestamp on the row**, and on `stores_edge_events=False` the first retraction is then gone entirely | **Recorded, not changed at the cap.** §2.6's argument for not refusing an unrecordable retraction is *the record is the row* — and that argument silently assumes retraction happens once. A second retraction is neither refused nor idempotent. Narrow (it needs a declined event store **and** a caller error) but the justification stops holding the moment it happens, so it is on this list rather than in a reviewer's notes. **Q34** |
| **D-4b-13** | **`edge_amended` is a vocabulary value nothing writes.** `EDGES.md` §5.2 adds three `event` values and narrates the third with a worked example — *"changing an edge's `confidence` after a re-classification is a new `edge_amended` event carrying the old and new values"* — and **v0 has no amend call for an edge at all.** Only `edge_added` and `edge_retracted` are ever appended | **Recorded, not removed.** The value is in `adapter.py`'s comment and in both migrations because the vocabulary is stored, never judged (§3.1), and a host that amends its own edge rows may write it. But §5.2 narrates it as landed behaviour with an example, and it is not. **Q32** asks whether 4c gives edges an amend path (which is where `payload_schema` and Q29 also point) or whether the example goes. Found by row 4b's second adversarial round |
| **D-4b-14** | **`Capabilities.scope_conflict()` is exercised by `C17-25` and not folded into `C0-01`'s universal declaration gate**, so a third-party backend gets `missing_why()` checked for free and this checked only if `C17-25` runs against it | Left as it is for v0 and recorded. `C17-25` does run against the real parametrised `adapter` fixture on all three legs for the no-conflict case, and uses a synthetic `Capabilities` for the conflict case because a **conformant** backend cannot produce one to check. Folding it into `C0-01` would put an edge-specific rule in the group that predates edges; the honest place is where it is |
| **D-4b-12** | **`find_edges` counts suppressed retracted edges with an extra query per page.** §4.3 rule 8 requires `complete=False` when a retracted edge was hidden, and only the adapter can know | Counted over the whole matching set rather than the page, because a caller told `complete=True` on page one and `complete=False` on page three has been told two different things about one query. The cost is one indexed count per `find_edges` call with `include_retracted=False`, and it is stated rather than discovered |

---

## 6. The adversarial review loop

*(Standing constraint 7. This section is written **after** the loop runs, never before it — row #4's own §17 recorded its exit-criteria table claiming two rounds while §17 recorded one, which was a BLOCKING finding of its round 2. See §6.1 below for the live state.)*

**Protocol** (standing constraint 7; the brief's stop rule): fresh reviewers each round, two per round with **distinct lenses** — one told to *drive the shipped registry through the CMS and NYC fixtures and try to make a broken edge backend pass*, one told to *hold the code against the three specifications and each document against the others*. Neither is told the work passed an earlier round, or who wrote it. **Stop: two consecutive clean rounds, or three rounds plus an honest convergence note.**

### 6.1 Round log

| Round | Reviewers | Verdicts | BLOCKING | MAJOR | Outcome |
|---|---|---|---|---|---|
| **1** | real-data lens · coherence lens | SHIP IT · NOT YET | **2** | **1** + 2 MINOR | Both blockers were in the DOCUMENTS, not the code — and one of them is row #4's own round-2 finding recurring inside the commit that added the gate meant to catch it. §6.2 |
| **2** | real-data lens · coherence lens | NOT YET · NOT YET | **4** | **3** + 5 MINOR | The first defect in the shipped CODE: the assembly bound fired on an exact match with nothing truncated. And three more mappings and shapes claimed and not exercised. §6.3 |
| **3** | real-data lens · **consumer lens** | NOT YET · NOT YET | **2** | **4** + 2 MINOR | A new lens, and it earned its place: five of the six came from *being the engineer who integrates next week* rather than from auditing. §6.4 |

### 6.2 Round 1 — what it found

**The split verdict is itself the finding.** The reviewer who *ran* things could not break the implementation: they reproduced every headline number independently against a real Postgres, built **seven** lying adapters — ignore `limit`/`after`, ignore `families` while declaring `indexes_edges_by_family=True`, lose the retraction tombstone, declare `stores_edges=True` and silently no-op every write, truncate while claiming `complete=True`, ignore `include_retracted=False`, ignore `incident_to` entirely — and **every one was driven to `NOT CONFORMANT`**, several by more than one test. They then drove the CMS and NYC fixtures through shapes `C17`/`C18` do not use (mixed symmetric and directed families in one call under `out` and `in`, self-loops, a triangle with both endpoints in the frontier, a retired family through `edge_families=None`, a cross-namespace walk, the assembly bound against real CMS fan-out) and found no wrong answer, no false `complete=True` and no dropped edge. **SHIP IT, one MINOR.**

The reviewer who *read* returned **NOT YET** with two BLOCKING, and both are the failure class this repository keeps paying for.

**B1 — `EDGES.md` §16 said row 4b "ran its own loop", in the same commit whose `4B-RUN.md` §6 said it had not started.** One document asserting the other's content, and the other flatly contradicting it. **This is row #4's own round-2 BLOCKING finding B6 — *"§16 said the loop had run twice when §17 recorded once"* — recurring one row later, inside the change that added ruling R31's process gate.** The gate could not see it: R31 binds §2.4.1, §4.3 and §4.4's rule tables, not §16's prose.

*Resolved* by making the cross-reference a **pointer rather than a claim**: §16 now says what §6 *records* is the state, and carries the recurrence in its own text so the next reader knows it happened twice.

**B2 — rule `2.4.1-2` was mapped to two contract ids, neither of which exercises it.** The rule is *"a `level="type"` family accepts any registered kind except `predicate`, `kind="edge"` included"*. `C17-27` asserts that `equivalent_to`'s declared `endpoint_kinds` *contains* `"edge"`; `C18-05` writes only `value_set` endpoints. **Nothing in the suite had ever written a `kind="edge"` endpoint.** And the case is not academic: it is **T3.13**, which `EDGES.md` §11.3 added specifically because §1 forbade `edge` as an endpoint kind while §3.1 declared it legal three sections later — *"a contradiction no design test exercised"*, found by both of that row's round-1 reviewers **by reading, and by neither by running, because nothing ran it**.

> **This is the failure R31 exists to prevent, found inside the row that built R31's gate — and the gate is blind to it by construction.** `check_spec_drift.py` verifies that a named id *exists*. It cannot verify that the id *asserts the rule it is mapped to*, and it never will: that is a judgement about what a test means. **The mapping needs a reader, and this is what the reader is for.** Recorded in §4 as a named limit of the gate rather than left as a property nobody stated.

*Resolved* by **`C17-30`**, which writes `equivalent_to(dpr:edge:concerns, oti_311:edge:relates_to)` through the shipped registry, reads it back, asserts the instance-level form is still refused (reification stays unconstructible), and asserts `predicate` is still refused at the same level. The rule table now names it first.

**M1 — `EDGES.md` §16 miscounted its own `Refusal.reason` additions, three ways at once.** The exit-criteria table said *"Three added… §5.12 now enumerates eighteen"*, while §17.4 of the same document records its round 3 adding a fourth (`unknown_edge`, the nineteenth), `INTERFACE.md` §5.12's own header says four, and `types.REFUSAL_REASONS`' comment says nineteen. Row 4b had edited two other cells of that same table without noticing the stale one beside them. *Corrected, with the three-way mismatch recorded in the cell.*

**The two MINOR, both taken.**

| # | Finding | Resolution |
|---|---|---|
| m1 | **Ruling R20's `model_tier` was threaded end to end and asserted nowhere on the edge path.** The only `model_tier` assertions in the suite are on the type side | Asserted in `C17-02`: written, read back through the store, and `None` rather than a manufactured default when nothing scored the edge |
| m2 | **`_edge_passes` returned `True` unconditionally on the `direction="both"` branch**, so its own docstring's *"the registry narrows, always"* was false for the direction every caller defaults to. An adapter ignoring `incident_to` was caught — by four tests whose subject is something else, which is a weaker claim than *pinned* | The branch re-checks incidence, and **`C17-31`** pins the primitive's own filter the way `C17-06` pins the family filter. **The regression was reproduced before the fix was believed**: reverting the branch fails `C17-31` and nothing else |

**Two numbers in this document were wrong when round 1 read it**, and neither reviewer caught them — they were found by re-running the suites to write §2's tails: §1 said `476 / 512`, computed by arithmetic from the previous run rather than measured, and the truth is `474 / 510`. Recorded in §1 rather than quietly corrected, because a *predicted* number is the same defect this repository has been bitten by four times, with better intentions.

### 6.3 Round 2 — what it found

**Both reviewers returned NOT YET, and the split is different from round 1's.** Round 1's real-data reviewer could not break the implementation; round 2's could, on the one axis nobody had walked.

**B3 — the assembly bound fired on an EXACT match, with nothing truncated.** A store holding exactly *N* edges on one node under `Registry(max_edges=N)` reported `known=N`, **`complete=False`**, and a `why_incomplete` naming a bound nothing had crossed — every edge that exists was returned and the adapter's own last page came back with no cursor. **[Reproduced]** on both SQLite and a real Postgres, deterministically, at *N* = 1, 5 and 500.

> **This is round 3's own B7, on the one axis its fix never walked.** That finding was *"the bound double-counted re-found edges"*; its test exercised 19-distinct-under-20 and 19-under-5 — strictly below and strictly above — **and never `==`**. Row #4's §17.6 says it in as many words: *"adding a test for the gap you were told about does not close the class… coverage of a surface is two-dimensional and each round had only walked one axis."* The class was named, the axis was named, and the boundary case was still not run.

*Resolved:* the page check is `>` rather than `>=`, and the per-edge cap stays `>=` — the two cannot disagree, because reaching the cap requires the page check to have fired first. `C17-18` now walks below, **at**, and above. Verified at *N* = 0, 1, 2, 4, 5, 6, 499, 500 and 501.

**B4 — two more R31 mappings named ids that do not exercise their rule**, which is `C17-30`'s finding recurring twice in the same table.

- **`2.4.1-6`** (*`equivalent_to` requires `src.kind == dst.kind`*) was mapped to `C17-08`, which declared a made-up family and asserted the **generic** `endpoint_kinds` mismatch. `grep family_constraint` returned the registry's own branch and **no test anywhere**.
- **`2.4.1-5`** (*a breaching declaration is refused at every door*) was mapped to `C17-09`, **whose own docstring named three doors while its body called two** — `approve()` appears nowhere in the function.

*Resolved:* `C17-08` writes a cross-kind `equivalent_to` and asserts `problem="family_constraint"`, and asserts that both kinds are individually legal for the family so the refusal is the family's semantics and not `endpoint_kinds` by accident. `C17-09` walks the second door by writing a breaching declaration past `propose_type` onto a pending proposal, which is what a proposal made before the rule looks like.

**B5 — `EDGES.md` §5.1 denied a field the code carries, contradicting the ruling, the code, and itself.** It printed an `EdgeProvenance` with no `model_tier` and argued at length that it was *"deliberately absent"*, recorded as open question Q15 — while **R20 answered Q15 yes on 2026-08-29, before this row started**, the field is on the dataclass, `add_edge` threads it, and §14's own Q15 row five hundred lines below printed *"`model_tier`: yes"*.

> **The hole is closed rather than patched.** `INTERFACE.md`'s printed shapes have been held against `types.py` since row 3c and `PACKAGE.md`'s against `adapter.py` since row 3d — each gate added after this same class of defect. **`EDGES.md` §5.1 was the last printed shape in this repository that nothing checked, and it is the one that drifted.** `check_spec_drift.py` now holds six EDGES shapes against `open_ontology/edges.py`, and the gate was watched failing: deleting the `model_tier` line reports *"the code has it and EDGES.md's printed shape does not"* and exits 1. **That is the third time drift has migrated into whichever half is not gated. There is no fourth half.**

**B6 — `EDGES.md` §16 said "39 contract ids"; the count is 41.** 29 + 10 was the figure before round 1 added `C17-30` and `C17-31`, and round 1's own fix commit corrected two other cells of that same table and left the third stale. **The third self-accounting error in that table, and the second inside row 4b.** §17.5 says a document that self-reports its own evidence needs an adversary pointed at the self-report; it was right again.

**The three MAJOR.**

| # | Finding | Resolution |
|---|---|---|
| M2 | **`edge_family_retired` was emitted on the `Edge` carrier at write time**, and §2.8's table listed only `NeighborReport`. **A closed vocabulary opening by CODE rather than by prose**, which is a worse version of §2.8's original finding rather than a better one — and it was absent from §5's deviations, which makes it a *silently resolved divergence*, the thing that list exists to prevent | The signal is right and the table was short: writing an edge under a word somebody withdrew is something a caller is entitled to know. §2.8 gains the second carrier **in the same change**, per ruling R3, and `C17-15` binds both |
| M3 | **`Registry.edge_provenance` raised an uncaught `NotSupported`** when `stores_events=False` and `stores_edge_events=True` — a combination nothing forbids and neither reference backend can produce. `read_events` is the same primitive `stores_events` gates, and this checked only the edge flag | Both flags are checked, and it degrades to `history=()` with the backend's own sentence — which `_events()`, the type-side twin, has always done. `C17-26` binds it. **A declined capability degrades; it never raises** |
| M4 | **`PACKAGE.md` §6.2's `C17-09` and `C17-26` rows overclaimed** what their tests assert — the same defect class as B4, in a second document that states it independently | Both rows are now true, because the tests were extended rather than the claims weakened |

**The MINOR, all taken except one recorded:** `EDGES.md` §6 printed a stale `Capabilities` missing `edge_store_shares_connection`, which is the *premise* of §6.2's own binding rule (added); §5.1's `created_by` still said *"`seed | ai | user`, unchanged"* after **R17** added `derived` in row 3e (corrected); `PACKAGE.md`'s inline prose cited `C17-14` for §6.2's binding rule instead of `C17-25` (corrected); **`edge_amended` is narrated by §5.2 with a worked example and written by nothing** (recorded as **D-4b-13**, with **Q32**); and `scope_conflict()` is bound by `C17-25` rather than by `C0-01`'s universal gate (recorded as **D-4b-14**).

**What round 2 says about round 1.** Round 1 found two blockers in the documents and its real-data reviewer found none in the code. Round 2's real-data reviewer, told explicitly *not* to repeat round 1's seven lying adapters and to walk the parameter space instead, found the bound defect in an afternoon. **The instruction that produced the finding was "go somewhere else"** — which is §17.6's lesson operationalised, and the strongest argument in this row for briefing each round away from the last one's ground rather than at it.

### 6.4 Round 3 — what it found, and the lens that found most of it

**Round 3 changed one reviewer's lens rather than only their briefing.** Rounds 1 and 2 ran a real-data lens beside a coherence lens; round 3 kept the first and replaced the second with a **consumer lens** — *you are the engineer who has to build against this next week, and you have never seen it before*, told to write an adapter from the documents alone and a scheduled job from the API alone. **Five of the six findings came from that reviewer**, and none of them is a thing an auditor would have looked for.

**B7 — a merge silently orphans every instance-level edge, and the walk reports `complete=True` about it.** `merge_types` is the registry's sanctioned answer to mechanism **4**, which §12 calls **co-dominant** for this row. It retires one word with the other as its `successor` and **rewrites no edge**. So a caller who does the *correct* thing afterwards — resolve to the canonical type, exactly as `resolve_type` teaches — got `known=0`, **`complete=True`**, and an empty `warnings` about edges sitting in the store under the absorbed name. **[Reproduced]** on every backend, because it lives entirely in the registry's node matching.

> This contradicts §4.4's own argument for why `complete` may ever be `True`: *"there is no edge that exists in the store and is invisible to a query over it."* **Across a merge there is.** And it is the shape §2.2's `direction` finding calls unacceptable — a confident, complete, false negative — reached this time not by an odd parameter but by ordinary housekeeping.

*Resolved by making the report honest and not by making the walk clever.* The origin's merge relations are read (its `successor`, the retired rows whose successor is it, its aliases) and the report carries `endpoint_type_merged:<ref>`, `complete=False`, and a `why` naming the other name. **It does not follow the chain**: whether an edge written under a merged word is an edge of its survivor is a decision above this row, and making it silently would change what `neighbors` means. Rule `4.3-14`, `C17-33`, deviation **D-4b-15**, **Q33**.

*And the fix's own first version was wrong within the hour, caught by the capability matrix rather than by a reviewer:* it read a `why` off `stores_aliases=False`, which made **every** walk on such a backend `complete=False` — a signal that never turns off, which is row 3d's own recorded failure for the durability warning, reproduced by the fix for a false `complete=True`. Aliases are a second reading of a fact the successor scan already reads, so their absence subtracts nothing.

**B8 — a caller's mistake did not arrive as the documented error.** §4.2 promises a `ValueError` for a caller's mistake, *"a caller error like §5.4's empty definition"*. The consumer reviewer passed `depth=1.5` — not exotic; `n / 1` is a float in Python and JSON round-trips ints as floats — and got a raw `TypeError` from three frames down, inside `range()`. A `node` that was a plain string died on `.namespace` deep in the walk. **And `edge_families="blocks"` was read one character at a time**, because a bare `str` satisfies `Sequence[str]`, and refused with `detail={"families": ["b","l","o","c","k","s"]}` — which does not merely fail, it *misleads a caller debugging why family `b` is unknown*.

> **The call this document is built around had no input validation at all.** Three of the first four things a new integrator tried went through it.

*Resolved:* the shape checks run first and name the parameter and the rule. `C17-32`.

**The four MAJOR.**

| # | Finding | Resolution |
|---|---|---|
| M5 | **§9.3's worked example — the grounding bundle's `relations` slot, the reason this row exists — is silently wrong past hop 1 when implemented the obvious way.** The reviewer compared each edge's endpoints against the ORIGIN; at depth 2 the far end of a second-hop edge was never incident on the origin, so `person#7` never appeared, `task#77` appeared twice, and there was **no error, no warning and no `complete=False`**. *Mechanism C, inside the example written to show a consumer how to avoid it* | `NeighborEdge.reached` names the node each edge newly reached (`None` for a self-loop and for a triangle's closing edge, which reaches nobody new). Filled by the walk, because the walk is the only thing that knows; and `edges`' `(at_depth, edge_id)` order is now a **guarantee** rather than an accident, because the consumer has to walk it in discovery order for `reached` to mean anything. §1's *"a set, not a ranked list"* is about relevance and stands. §9.3's example is rewritten and `C17-34` binds it |
| M6 | **`PACKAGE.md` §3.4 primitive 15's printed signature was stale, and deviation D-4b-2 said it had been amended.** A third-party author implementing `read_events` literally from the document — which §3.1 calls the whole point — got a `TypeError` on the first `edge_provenance` call. **Two adversarial rounds read past it**, because this project's drift checker diffed façade signatures and printed dataclasses and never the eighteen primitive blocks | The signature is amended, and **the gate now covers all eighteen printed primitive signatures against the Protocol** — watched failing before it was trusted. A deviation claiming an amendment nobody made is `EDGES.md` §17.4's M10 exactly, one row later, in this document's own list |
| M7 | `node` of the wrong type raised `AttributeError` from inside the walk | Folded into `C17-32` |
| M8 | `edge_families` as a bare `str` iterated character by character | Folded into `C17-32` |

**The two MINOR:** `NodeRef` — the type in `neighbors`' own signature — was not exported from `open_ontology` (added); and **retracting an already-retracted edge overwrites the first retraction's reason, actor and timestamp**, which on `stores_edge_events=False` erases it entirely (recorded as **D-4b-16** and **Q34** rather than changed at the cap: §2.6's *"the record is the row"* argument silently assumes retraction happens once).

**One thing the round investigated and cleared**, recorded so it is not re-walked: `add_edge` does not bump `usage()`, so an edge family looks orphaned however many edges are written under it. That is `record_use`'s established, opt-in, pre-existing mechanism for *all* type usage in this registry — not something `add_edge` was ever meant to drive — and not a row-4b regression.

---

### 6.5 Convergence — honestly, and the loop did **not** converge

**Three rounds, six fresh reviewers, five NOT YET and one SHIP IT.** The brief's stop rule was *two consecutive clean rounds, or three rounds plus an honest convergence note*. **The second branch applies**, which is the same close rows 3c, 3d, 3e and #4 took, and it should be read the same way: as a fact about the process, not a formality.

**What the defect class did across the three rounds** — the only real evidence of convergence, and the shape here is different from row #4's:

| Round | The defects were… |
|---|---|
| 1 | **In the documents' self-reports.** Two BLOCKING, both about what a document said about itself; the reviewer who ran the code found nothing, having built seven lying adapters that were all caught |
| 2 | **In the claims about what was tested, and one boundary nobody had run.** Three mappings and shapes claimed and not exercised — plus the first defect in the shipped code, on the exact axis the previous row's retro had already named |
| 3 | **In what a NEWCOMER hits, which nobody had been asked to be.** Five of six from the consumer lens: no input validation on the central call, a stale primitive signature a builder would build from, and the document's own worked example silently wrong |

**That is not narrowing, and saying otherwise would be the kind of claim this row spent three rounds catching.** Rounds 1 and 2 found defects in the *evidence*; round 3 found defects in the *product*, and found more of them. What changed between rounds was not the artifact's quality but **where the reviewers were pointed** — and each time they were pointed somewhere new, they came back with something real.

> **The honest reading: the ceiling here is the lens, not the artifact.** Row #4's §17.5 concluded that *"prose-plus-probe review has a floor, and this document has reached it"*, and named the next signal with real information as **a real consumer over a real store**. Round 3 was the closest available approximation of that — a reviewer told to *be* the consumer — and it produced the largest and most product-relevant haul of the three. **[Inferred]** a fourth round with a seventh lens would find a fourth class rather than none. That is an argument for shipping this to its actual consumer and routing what they find back, not for a fourth synthetic round.

**Three things this loop did that are worth keeping.**

1. **Every BLOCKING finding was reproduced by running code before it was believed**, including the two that were about documents rather than code — those were reproduced by reading both sides and quoting them.
2. **Two of the three rounds found a defect inside the mechanism built to prevent that very defect**: round 1 found a rule mapped to ids that did not exercise it *inside the row that built ruling R31's gate*, and round 3 found a stale primitive signature *invisible to the drift checker this project built for exactly that*. Both closed the class rather than the instance — the gate now reads what the ids assert only insofar as a human can, and it now reads all eighteen primitive signatures.
3. **Changing the LENS produced more than changing the briefing.** Round 2's real-data reviewer was told *"do not repeat round 1's seven lying adapters, go somewhere else"* and found one BLOCKING. Round 3's consumer lens was told *"be the engineer who integrates next week"* and found five findings nobody had been positioned to see. Rows 3c through #4 all ran two lenses; **this is the first round in this repository where a third lens was tried, and it was the productive one.**

---

## 7. Questions for the supervisor — **Q27 onward**

Numbering continues from Q26 (ruled as R31). None is taken on this row's authority.

| # | Question | Recommendation | Founder-visible? |
|---|---|---|---|
| **Q27** | **`equivalent_to`'s `src.kind == dst.kind` constraint is hard-coded to one family name.** §2.4.1 says plainly that it is *"that family's semantics and not a general mechanism"*, so the registry knows one rule about one word. Should it become a sixth declarable key (`same_kind_endpoints: bool`)? | **No, and record it.** A sixth attribute invented for one family is how a declared shape starts growing a rule language, which is exactly what R18 accepted *narrowly*. Revisit when a second family needs it | No |
| **Q28** | **`endpoint_kinds` cannot express the constraint §2.4 uses to motivate it** (D-4b-3): a citation and a facility are both `entity`, so *"a citation edge must not accept a facility at the tag end"* is unexpressible. CMS carries the fact in unvalidated `from`/`to` | **Narrow the sentence, do not widen the mechanism.** An endpoint *type* constraint is a second identity triple per end and a second thing to keep in step with the endpoints; the honest v0 move is for §2.4 to say what `endpoint_kinds` does. Phase 3's ingestion loop is the consumer that would force more | No |
| **Q29** | **`payload_schema` is inert and its blocker has gone** (D-4b-6): §2.5 declares it inert until **R10**, and R10 landed in row 3e. §13's own rule says an unlandable `payload_schema` should be *removed* rather than left as a `None` that never becomes anything — which now reads the other way round | **Take it in 4c**, with edge payload validation as its own row: modes, versions, `attr_schema_version` on the edge, and `C15`'s shape transposed. It is the one part of the edge model with a declared field and no mechanism, and E10 is the cost UC1 is already paying | No |
| **Q30** | **A retired family reached through `edge_families=None` is searched and NOT warned about** (D-4b-11), because §2.8's carrier table says *"a named family"*. At scale a `None` walk over a store with fifty retired families would emit fifty warnings | **Keep the literal reading for v0 and revisit with Phase 3's ingestion loop**, which is the first caller that will use `None` at scale. The alternative — a count rather than a list — is a new warning shape, and the vocabulary is closed | No |
| **Q33** | **Should `neighbors` FOLLOW a merged type's successor chain** (D-4b-15), rather than only reporting that it did not? `resolve_type` already follows it (`C3-11`), so a caller is taught one identity model by one call and given another by the next | **Yes, and it is 4c's to take**, with the shape `resolve_type` already uses. It is not this row's to take silently: following the chain changes what an edge's endpoint MEANS — from *the reference that was written* to *the identity that reference now belongs to* — and that is an `INTERFACE.md` §2.1 question, not an `EDGES.md` one. The honest v0 answer is the one shipped: say what was not searched, and stop claiming completeness | **Yes** — it decides whether a merge is safe to run on a store with edges in it |
| **Q34** | **A second retraction overwrites the first's reason, actor and timestamp** (D-4b-16), and §2.6's *the record is the row* argument assumes retraction happens once | **Refuse the second one** in 4c (`already_decided`'s shape, which §5.5 already has a value for), or make it idempotent. Not taken at this row's cap because either is a behaviour change and neither is forced by a use case | No |
| **Q32** | **`edge_amended` is a vocabulary value nothing writes** (D-4b-13). `EDGES.md` §5.2 narrates it with a worked example — re-classifying an edge's `confidence` — and v0 has no amend call for an edge at all | **4c decides, with `payload_schema` (Q29)**, because they point at the same missing surface: an edge whose payload is validated is an edge somebody will want to correct. Until then the example should not read as landed behaviour | No |
| **Q31** | **`neighbors` is bounded by `max_edges` at the REGISTRY, so two registries over one store can disagree about what `complete` means.** The bound is a deployment parameter (`Registry(max_edges=…)`), which is what makes it a circuit breaker rather than something a caller can raise per call | **Accept for v0 and record.** It is the same shape as `NamespacePolicy`, which is already per-registry, and R25 has routed the real question (façade paging) to Phase 3 with R13 | No |

---

## 8. What this row did NOT do

- **No `payload_schema` validation** (D-4b-6, Q29). The field is specified, stored and never read.
- **No `narrower_than`, no second family.** §3.3 declined it and none of the three fixtures asked for it here either.
- **No façade paging.** R13 stands, R25 routed the 9.7M-degree node to Phase 3, and the assembly bound tells the truth without solving it.
- **No tenancy dimension.** R24, and `C18-09` asserts that `user_id` is *not* mapped onto `namespace`.
- **Nothing in beacon was edited, imported or executed**, and nothing of beacon's is vendored. `C18-09`/`C18-10` carry column names and a shape, read once, read-only, from row #4's own §7.2 table.
