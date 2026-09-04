# INGEST — the mapping layer between landed rows and the ontology

**Version:** `v0` — **unstable.** Every name, field and return shape here may change without a
deprecation path (standing constraint 4).
**Status:** Draft, 2026-09-03. Satisfies `ROADMAP.md` Phase 3's **first row**, opened by the founder
2026-09-02. Deliverable **#7a** of the ordering. **This document ships no code.** Its four design tests are
runnable probes under [`../tools/`](../tools/); their observed output is in
[`../runs/7A-RUN.md`](../runs/7A-RUN.md).
**Constraints it is written against:** **R58** (the façade pages under one rule for `known`; *a guard never
reads a page*), **R59** (the protocol stays tenant-blind; tenancy is the host's predicate), **R60** (one
three-valued `Condition` language, the ingestion loop its first consumer) — all three in
[`../decisions/2026-08-30-phase3-decisions-R58-R60.md`](../decisions/2026-08-30-phase3-decisions-R58-R60.md);
**R77** (instance resolution is Phase 3's, and `resolve_type` is never extended to cover it) and **R78**
(the host holds the instances) — both in
[`../decisions/2026-09-02-phase3-repoint-R77-R78.md`](../decisions/2026-09-02-phase3-repoint-R77-R78.md).
**Claim tags:** **[Observed]** seen directly · **[Inferred]** a reasonable read · **[Assumed]** believed,
untested.

---

## 0. What this is, in three sentences

[`../../VISION.md`](../../VISION.md) §4b, verbatim: *"the product is neither ETL nor an ontology store. It
is **the mapping layer between them**: landed rows to typed entities and relationships, with curation and
provenance applied **at the point of ingest**."* This document specifies that mapping layer's identity
half — **given a landed row, which existing thing is this, and if none, what is proposed instead** — as a
protocol over instances **the host already holds**.

It is not a store, not a pipeline, and not a queue. It adds **two read primitives**, **one call**, **one
declared policy**, **one condition language**, and **no table**.

### 0.1 Non-goals — one line each

- **No connectors.** Extraction and loading are Airbyte's; this layer consumes what they land. `VISION.md` §6.
- **No orchestrator and no scheduler.** When a batch runs is the host's; `ACTIONS.md` §4's *the gate is
  advisory by construction* is inherited unchanged.
- **No executor.** This document specifies no call that performs a write against a host's data.
- **No HTTP.** No routes, no auth, no pagination-over-the-wire. `INTERFACE.md` §1's non-goal, unchanged.
- **No tenancy dimension.** R59 stands: tenancy is the host's predicate, made expressible by §6. Reversing
  it is a Phase 4 change, and §6's design test is what would force it.
- **No instance store.** **Decided by design test 1, not assumed** — see §1. This project stores no
  instance rows, mints no instance identifiers, and holds no copy of a host's table.
- **No instance-level proposal loop of its own.** §4 makes an ingest proposal an **invocation of a
  host-declared action family**, using the ledger `ACTIONS.md` already ships. Nothing new is stored.
- **No change to `resolve_type`.** **R77**, non-negotiable. §3's call is a new call in this document.

---

## 1. The seam — **R78, CONFIRMED by design test 1 before anything else here was written**

**The question R78 put, deliberately falsifiably:** does this project become an instance store, or does it
define resolution *over instances the host already holds*?

**Answer: the host holds the instances. [Observed], design test 1** — [`ingest_seam_probe.py`](../tools/ingest_seam_probe.py),
16/16 checks, over the full CMS health-citations file (**165,336,194 bytes, 419,479 rows, 14,627 CCNs, 104
provider names shared by more than one CCN**, all four reproducing `USE-CASES.md`'s pre-registered figures).
Every outcome of §3's call was reached with (a) a table the host owns, (b) two **read-only** primitives, and
(c) **no instance row in the registry**: after a walk-through that scanned 14,627 host rows five times, the
**shipped** `ontoloche.Registry` on SQLite held exactly `[('entity', 'facility')]`, and no CCN and no
provider-name string appeared in it. The expectations were pre-registered in
[`../runs/7A-RUN.md`](../runs/7A-RUN.md) §0, in a commit that predates the probe.

**Three consequences, and the second is the structural argument.**

1. **The vocabulary half is unchanged.** The registry holds `kind="entity"` rows — `facility`, `project`,
   `task` — through `propose_type` / `approve` exactly as today. Nothing in this document adds a kind.
2. **Two primitives, not three, and the count is the evidence.** [`EDGES.md`](EDGES.md) §7.1 takes three
   (`put_edge` / `get_edge` / `find_edges`) and [`ACTIONS.md`](ACTIONS.md) §9 takes three, because this
   project **stores** edges and invocations. Instances are the host's, so **there is no `put`** — and a
   protocol that needed one would be an instance store with a different name. §2 takes two, both reads.
3. **The type-side half of the seam was already built.** **[Observed]** `resolve_type("BURNS NURSING HOME,
   INC.")` returns `outcome="not_a_type"` with reason **`instance_not_type`** — a branch live in
   [`../../ontoloche/_resolve.py`](../../ontoloche/_resolve.py) since row #1. The type registry does not
   merely decline the instance question; it **names** it. `INTERFACE.md` §1's non-goal and §10.3's
   resolution both stand and gain a pointer to this document rather than being deleted (R77).

> **What the confirmation does NOT claim.** It was not shown that an instance store is *unnecessary in
> general*; it was shown that **every outcome is reachable without one**, on the read path, at 14,627 rows.
> Write-side ingest at volume is §4's contract and the build row's measurement.
> [`../runs/7A-RUN.md`](../runs/7A-RUN.md) §1.4 states what would overturn this verdict, so a later reviewer
> has something to aim at.

**Rules of §1**

| # | rule | id |
|---|---|---|
| 1-1 | This project stores no instance rows and mints no instance identifiers. An instance is named by an `InstanceRef` (`EDGES.md` §2.1) whose `id` the **host** allocated | `C20-01` |
| 1-2 | Instance resolution is a **new call** in this document and never an extension of `resolve_type`. R77 | `C20-02` |
| 1-3 | A registry whose adapter declares `resolves_instances=False` refuses every call in this document with `instance_source_absent` (§8.4) — **never** an empty candidate set, which would read as *"there is nothing like this"* | `C20-03` |

---

## 2. Candidate retrieval — **two primitives, numbered 22 and 23**

`PACKAGE.md` §3.4 has twenty-one. This document adds **two**, and — as in `EDGES.md` §7.1 — the number is
the argument: **families need no new primitive** (`put_type` / `get_type` / `find_types` serve them), and
**instances need no write primitive** (§1, consequence 2).

```python
@dataclass(frozen=True)
class InstanceRecord:
    namespace:     str          # the TYPE's namespace
    kind:          str          # "entity" -- EDGES 2.1's rule for an InstanceRef's type
    type_name:     str
    instance_id:   str          # the HOST's identifier. Opaque to this project
    label:         str          # the human-facing string a landed row would carry
    attributes:    dict         # opaque. The host's own columns, carried so a resolver
                                #   can discriminate; never interpreted by the adapter
    source_version: str | None  # the SOURCE's own version. INTERFACE 2.4a, R21

@dataclass(frozen=True)
class CandidateQuery:
    namespace:   str
    kind:        str            # always "entity" in v0
    type_name:   str
    label:       str | None = None    # what the landed row calls it. A HINT, not a filter
    host_filter: str | None = None    # the HOST's own predicate, opaque to this project
    limit:       int | None = None    # the ADAPTER pages. R58
    after:       str | None = None    # opaque cursor. The ENCODING is the build row's

@dataclass(frozen=True)
class CandidatePage:
    records:        tuple[InstanceRecord, ...]
    known:          int | None  # None = the backend cannot count. NOT 0. Rule U
    complete:       bool        # about the SET. R58
    why_incomplete: str | None
    next_after:     str | None
```

**22. `get_instance(namespace: str, kind: str, type_name: str, instance_id: str) -> InstanceRecord | None`**
Confirms one reference. `None` means **absent**, which is a fact — the host always knows whether its own key
exists, exactly as `get_edge` does (`EDGES.md` §7.1 primitive 17).
**Uncertainty:** `resolves_instances=False` ⇒ raises `NotSupported`; the registry checks the capability
first and never calls this, surfacing `Refusal(reason="instance_source_absent")`.

**23. `find_instance_candidates(q: CandidateQuery) -> CandidatePage`**
The one call behind §3. **Scoring is not pushed into the adapter**: the adapter returns records, the
registry scores them. That is `PACKAGE.md` §3.1's boundary — an adapter that knew about confidence would
know about `InstanceResolution`, and `C0-04`'s source-inspection test would have a new identifier to police.
Design test 1 holds the probe's own host table to that rule by source inspection.
**Uncertainty:** the general rule is `find_types`': a filter the backend cannot apply returns
`complete=False` with a `why`, **never** a filtered-looking empty page.

**No third primitive for counting and none for writing.** Counting is `CandidatePage.known`; writing is the
host's. Both were considered and dropped, for `EDGES.md` §7.1's reason: a primitive that exists only to
express a policy is a policy inside the adapter.

### 2.1 `label` is a hint and `host_filter` is a filter, and confusing them is the failure

`label` says what the landed row calls the thing. A backend **may** use it to narrow; a backend that ignores
it returns a wider page and the registry scores it, and **that is not incompleteness** — the page it returned
*is* complete for what it was asked. `host_filter` is different in kind: it is the **host's own predicate
over its own indexed columns**, opaque to this project, and a host that cannot apply the one it was handed
must say so (`complete=False` plus a `why`) rather than ignore it.

**Why the distinction is load-bearing, measured.** **[Observed], design test 2**
([`ingest_paging_probe.py`](../tools/ingest_paging_probe.py), live against `erm2-nwe9` on 2026-09-03): one
50,000-row page — the host's own ceiling — costs **1.26s warm and 13.86s cold**, and exhausting
`agency='NYPD'` needs **196 of them**. **[Inferred]** 4.1 minutes at the warm rate, ~45 at the cold one,
both ignoring deep-cursor decay, both lower bounds — **for one landed row.** The same read drains to
exhaustion in **four requests** once the host's own predicate narrows **9,764,249** rows to **725**.

**So candidate retrieval is affordable exactly when the host says it is**, and the narrowing is a fact about
the host's table that this project neither invents nor validates. A layer that arranged its own index over a
host's data would be holding a copy of it, which is §1 again.

### 2.2 Paging, under R58's one rule and no other

The three states a caller can be in are the three R58 names, and **[Observed], design test 2** all three
come off primitive 23 against the live 9.7-million-row partition and are distinguishable from the report
alone:

| the page says | it means | observed 2026-09-03 |
|---|---|---|
| `complete=True` | this is the **set** | `known=725 complete=True next_after=None` |
| `complete=False`, `next_after` present | this is a **page**; ask again | `known=200 complete=False next_after='200'` |
| `complete=False`, `next_after` absent, `why_incomplete` set | **truncated** — the rest cannot be read from this surface | `known=1000 complete=False next_after=None why='scan budget of 2000 rows reached…'` |

**`known` counts what THIS PAGE materialised.** `complete` is about the **set**. A backend that cannot count
returns `known=None`, which is Rule U and which `0` would falsify.

**And a guard never reads a page.** §3's ambiguity decision is an **identity** read — *do two things answer
to this?* — so it is an **internal exhaustive read**: the registry loops `next_after` to `None`, or reports
the read as **truncated** and answers `unknowable` (§3.4). It never treats a page as a set.
`INTERFACE.md` §5.6's caller-facing paging and this internal read must not share a code path that can
discard a cursor; R58's own fifth-trip evidence is why.

**The cursor's encoding is deliberately NOT decided here.** Opaque string, exactly as at the adapter — R58
leaves the contents to the row that builds it, and this row does not take it.

### 2.3 The two capability flags this document mints

`Capabilities` gains flags the way beacon finding **U3** added `attribute_projections`: one bool for *does
this backend do this at all*, one projection set for *which named things does it honour faithfully*.

```
resolves_instances:  bool = False
    #: Does this adapter answer instance-candidate queries? Defaults FALSE, for the
    #: load-bearing reason `stores_edges` and `stores_invocations` default False: an
    #: adapter written against the twenty-one-primitive protocol answers none, and a
    #: True default would make every such adapter claim it. The honest answer for a
    #: backend that predates this row is `instance_source_absent`.

instance_filters:  frozenset[str] = frozenset()
    #: The named host filters primitive 23 honours faithfully. U3's shape exactly: a
    #: filter listed here is applied; a filter NOT listed comes back with
    #: `complete=False` and a `why` naming it -- never applied-looking and never
    #: silently dropped.
```

**Nothing else.** A `counts_instance_candidates` flag was considered and refused: `known: int | None`
already carries that fact, and a second home for one fact is `EDGES.md` §2.4's rule.

**Rules of §2**

| # | rule | id |
|---|---|---|
| 2-1 | The protocol adds exactly two primitives, both **reads**. A write primitive for instances is a conformance failure | `C20-04` |
| 2-2 | `get_instance` returns `None` for absent, never a manufactured record | `C20-05` |
| 2-3 | `find_instance_candidates` pages under R58's one rule: `known` counts the page, `complete` is about the set, `next_after` says whether there is more | `C20-06` |
| 2-4 | A truncated read is `complete=False`, `next_after=None`, `why_incomplete` set — distinguishable from a page by the report alone | `C20-07` |
| 2-5 | A backend that cannot count returns `known=None`, never `0` | `C20-08` |
| 2-6 | The adapter scores nothing. `C0-04`'s source inspection extends to these two primitives | `C20-09` |
| 2-7 | A `host_filter` the backend cannot apply returns `complete=False` with a `why` naming it; it is never silently ignored | `C20-10` |
| 2-8 | `label` is a hint: a backend that ignores it returns a wider page with `complete=True`, and the registry narrows above | `C20-11` |
| 2-9 | `resolves_instances` defaults `False`, and every call here refuses `instance_source_absent` when it is | `C20-12` |
| 2-10 | A filter named in `instance_filters` is honoured faithfully; one outside it is reported, per U3's rule | `C20-13` |
| 2-11 | An identity read exhausts the cursor or reports **truncated**; it never reads one page and decides | `C20-14` |

---

## 3. `resolve_instance` — **five outcomes, and the fifth was forced by a constructed failure**

```python
def resolve_instance(
    candidate: str,
    context: InstanceContext,
    *,
    type_name: str,
    namespace: str = "default",
    tier: str,                          # INTERFACE 2.7 -- REQUIRED, not defaulted
    host_filter: str | None = None,     # the HOST's narrowing. 2.1
    predicate: Condition | None = None, # the HOST's tenancy predicate. 6, R59
) -> InstanceResolution: ...
```

**There is deliberately no `min_confidence` parameter.** `resolve_type` has one; this call does not, and §5
is the reason: the threshold is a **declared, governed fact on the entry**, and a per-call threshold is a
duplicate factory (design test 4, §5.1). That is the sharpest difference between the two calls and it is not
an oversight.

### 3.1 The outcomes, and why five rather than four

`resolve_type` has four: `existing` / `proposal` / `not_a_type` / `none`. The mirror was written as four and
**design test 1 broke it**.

| outcome | means |
|---|---|
| `existing` | exactly one held instance answers to this candidate, above the entry's `match_at` |
| `ambiguous` | **more than one** does, inside the entry's ambiguity margin, and nothing here separates them |
| `proposal` | a **finished** scan found none, so this is a new thing |
| `not_an_instance` | the candidate names a class, a column or an artefact — not one thing of that class |
| `unknowable` | the candidate scan **did not finish**, so no statement about existence can be made |

**The fifth is an outcome and not a flag, and the failure was constructed rather than argued.**
**[Observed], design test 1 T1.5:** with the fifth value absent, a scan cut off before the matching row
returns `outcome="proposal"` for a facility that exists **in the same table** —
`cms:entity:facility#745057`, confirmed `existing` at 1.0 by the uncapped control **in the same run**. The
proposal is well-formed, provenance-bearing, approvable, and wrong: *the pollution machine with a governance
loop bolted to the front of it.* A `complete=False` flag beside `outcome="proposal"` is a caller's to
ignore; an outcome is not.

**[Observed], design test 2** reaches the same value from the opposite direction and with no fixture at all:
resolved against `agency='NYPD'` unnarrowed, the answer is `unknowable`, because 196 host requests is not a
scan any per-row loop performs. **Two independent routes to one value is the evidence this document rests
the fifth outcome on.**

### 3.2 `ambiguous` is decided BEFORE `existing`, and that ordering is a rule

**[Observed], design test 1 T1.2:** `"MILLER'S MERRY MANOR"` is the label of **twelve** distinct Indiana
facilities in the CMS file, every one of them scoring **1.0** on the name. A resolver that took the top
candidate would answer `existing` at 1.0 — **the confidence `INTERFACE.md` §5.3 calls a guarantee** — and
file eleven facilities' citations into a twelfth's record.

`ROADMAP.md`'s kill criterion is *two things answering to one identity*. **This is that criterion one level
below where its fourteen trips live**, and the ordering is the guard: a tie inside the margin can never
collapse to its first member, and `InstanceResolution.ref` is `None` on `ambiguous` — asserted as a negative
by the probe, because *the outcome was right and the ref was populated anyway* is the shape trips eleven and
twelve took.

### 3.3 `not_an_instance` mirrors `not_a_type`, and it is the same argument

`INTERFACE.md` §5.3 gained `not_a_type` because a 99.988%-redundant column resolving to `None` reads as *"go
propose it"* and hands the pollution machine its first type. The instance analogue is a landed cell that is
not an instance at all — a column header that arrived as a value, a class word, a blank. **[Observed], T1.4:**
`"Provider Name"` answers `not_an_instance` and the host table is **never scanned for it** (`scanned=0`),
which is the point: the cheapest correct answer is the one that asks the host nothing.

**v0 does not define the classifier**, exactly as `INTERFACE.md` §2.8 does not define semantic detection. It
defines the **outcome** and requires it to be reachable. `_resolve.py`'s `instance_not_type` is the mirror
already shipped on the other side of the seam and is the natural place for the pair to be kept honest.

### 3.4 Rule U, at this call

**A candidate scan that could not finish is `unknowable`, never *not found*.** Stated as an ordering inside
the call, because the ordering is what makes it true: **the incompleteness is checked before the emptiness
is interpreted.** A resolution that reached no candidate over a scan that did not finish has not learned that
there is no such instance; it has learned nothing.

`unknowable` also absorbs three cases that are **not** truncation, and naming them stops each becoming its
own value:

1. the host's tenancy `predicate` was **undecidable** on candidates the scan returned (§6, design test 3);
2. the adapter could not apply a `host_filter` it was handed, so the page it returned answers a wider
   question than the caller asked and cannot be read as the set;
3. the backend returned `known=None` and `complete=False` together — it neither counted nor finished.

**Rules of §3**

| # | rule | id |
|---|---|---|
| 3-1 | The outcome vocabulary is closed at five. R3 applies: a sixth is a §-row change with a contract id | `C20-15` |
| 3-2 | `resolve_instance` is a distinct call and no argument of `resolve_type` reaches it. R77 | `C20-16` |
| 3-3 | `ambiguous` is decided before `existing`; a tie inside the entry's margin never collapses to its first member | `C20-17` |
| 3-4 | On `ambiguous`, `ref` is `None` and every tied candidate is returned | `C20-18` |
| 3-5 | A scan that did not finish is `unknowable`, whatever the candidates found — checked **before** emptiness is interpreted | `C20-19` |
| 3-6 | `unknowable` is an outcome, not a flag: no `complete=False` result carries `outcome="proposal"` | `C20-20` |
| 3-7 | `proposal` requires `complete=True` on every page the identity read consumed | `C20-21` |
| 3-8 | `not_an_instance` is reachable without reading the host table at all | `C20-22` |
| 3-9 | `confidence` is `float \| None`; `None` means *did not score*, never `0.0`. `INTERFACE.md` §5.3's rule | `C20-23` |
| 3-10 | The call takes no `min_confidence`: the threshold is the entry's. §5 | `C20-24` |
| 3-11 | `tier` is required and is echoed back for provenance. `INTERFACE.md` §2.7 | `C20-25` |
| 3-12 | An undecidable host predicate makes the resolution `unknowable`, never a narrower candidate set | `C20-26` |

---

## 4. The propose-at-ingest contract — **an invocation, not a fourth object**

**What an instance proposal IS: an invocation of a `kind="action"` family the host declared.** Nothing is
added. [`ACTIONS.md`](ACTIONS.md) already ships every part of it:

| what a proposal needs | what already ships it |
|---|---|
| a governed declaration that goes through propose→approve | the family is a `TypeEntry`, `ACTIONS.md` §2.1 / §5.1 |
| a way to name the landed row's identity | `InstanceRef` + `ref_key` / `parse_ref` (R72), `ACTIONS.md` §2.3 |
| a gate before it runs | `preflight`, `approval_mode`, `min_auto_tier`, `ACTIONS.md` §5.2 |
| provenance with actor, tier, confidence, approver, source version | `InvocationProvenance`, `ACTIONS.md` §3.2 |
| a record of what happened | `record_invocation`, the ledger, `ACTIONS.md` §6.2 |
| a queue that can be drained by a second person, later | `review_invocation` (**R73**), `ACTIONS.md` §6.5 |
| an enumerable backlog | `invocations(unreviewed=True)`, `ACTIONS.md` §6.3 |

**So this section specifies a shape and a rule, and no storage.** That is why §1's *two read primitives*
survives contact with the write side: the propose-at-ingest act is recorded where every other governed act
of this project is recorded.

### 4.1 What approves it, and who writes the row

**The host writes the instance row; this project never does.** The family declares
`Effect(op="host_state", why=…)` — `ACTIONS.md` §2.5's fourth operation, the admission that *this action
changes something this protocol does not model* — and the host performs it. The `InstanceRef` the host
minted comes back on the invocation, so the ledger holds *which* thing was created, by whom, at what tier,
at what confidence, approved by whom.

**`approval_mode` carries the whole gate.** A family whose ingest proposals may auto-apply declares
`auto`; one whose proposals a human must see declares `review` or `human`; §5's band is what routes an
individual row to the second of those.

### 4.2 What provenance it carries — **nothing new**

`Provenance` (`INTERFACE.md` §2.4) already carries `created_by_actor`, `model_tier` (§2.7), `approved_by`
(never blank-implying-human), and `source_version` (§2.4a, **R21**). `InvocationProvenance` narrows it and
adds `confidence`. **Nothing is added here**, and the brief's instruction — *add nothing until a design test
forces it* — was not overridden by any of the four.

**One thing that is inherited and is worth stating because it closes a live defect.** **[Observed]**, the
design partner's capture applies relationships with *no approval step and no model-identity provenance*;
recorded in the supervisor's own architecture framing of 2026-09-02 as one of five surfaces of one missing
substrate. Under this contract that act is an invocation carrying an actor, a tier and an approver, and it is
enumerable afterwards. **The fix is not a feature of this document; it is what using it costs nothing extra.**

### 4.3 Reconciling a proposal made while a candidate was `ambiguous`

This is the case the brief names and it needs a mechanical handle, not prose.

**The rule: a propose-at-ingest invocation made while `resolve_instance` answered `ambiguous` is recorded
with the warning `instance_ambiguous_at_proposal:<n>`, where `<n>` is the number of tied candidates, and it
is recorded in `approval_mode="review"` whatever the family's default.** Two consequences, both mechanical:

1. `invocations(unreviewed=True)` enumerates exactly the proposals that were made over an unresolved
   identity. The backlog is a query, not a memory.
2. `review_invocation` (**R73**) is its only drain, and R73's own argument applies unchanged: **a review is
   a second act by a second person at a later time.** The actor who ingested the row cannot clear their own
   ambiguity.

**A proposal made while the resolution was `unknowable` is a different case and this document refuses to
soften it:** it is not recorded as a proposal at all, because *we could not look* is not *we looked and found
nothing*. §10 records what this cannot enforce.

**Rules of §4**

| # | rule | id |
|---|---|---|
| 4-1 | A propose-at-ingest act is an invocation of a `kind="action"` family; this document adds no object and no primitive for it | `C20-27` |
| 4-2 | The host writes the instance row. The family declares `Effect(op="host_state")` with its mandatory `why`, and this project performs no write | `C20-28` |
| 4-3 | The `InstanceRef` the host minted is recorded on the invocation, so the ledger names what was created | `C20-29` |
| 4-4 | Provenance is `InvocationProvenance` unchanged: actor, tier, confidence, approver, `source_version`. No field is added | `C20-30` |
| 4-5 | A proposal made over an `ambiguous` resolution carries `instance_ambiguous_at_proposal:<n>` and is recorded in `review` mode whatever the family declared | `C20-31` |
| 4-6 | Those proposals are enumerable by `invocations(unreviewed=True)` and drained only by `review_invocation` | `C20-32` |
| 4-7 | A resolution of `unknowable` yields **no** proposal | `C20-33` |
| 4-8 | An ingest family may not declare `Effect(op="propose_type", kind="predicate")` — `ACTIONS.md` §2.5's allowlist, inherited and restated because an ingestion loop is the highest-volume caller that could reach it | `C20-34` |

---

## 5. The match-vs-propose confidence gate — **a governed fact on the entry, never a call parameter**

```
MatchPolicy:                    # declared on the kind="entity" entry
    match_at:        float      # at or above: `existing`
    propose_below:   float      # strictly below: `proposal`
    ambiguity_margin: float     # candidates within this of the top are TIED. 3.2
    why:             str        # REQUIRED, non-empty
```

**Three outcomes, three-valued per R60**, and the band between the two thresholds is the third: a human's,
not a default's. **[Observed], design test 4** ([`ingest_gate_probe.py`](../tools/ingest_gate_probe.py),
100 live NYC 311 rows, 38 already held exactly, 24 held but landing in an abbreviated spelling, 38 genuinely
new):

```
match_at=0.97  propose_below=0.80
   known: {'match': 38}          novel: {'propose': 38}
  banded: {'review': 23, 'match': 1}
```

**38 of 38** — `ROADMAP.md`'s *"I already know 38 of these"*, made literal on public data. All three outcomes
fire on one batch. The one abbreviated row that matched at 1.0 is `BATH BEACH PARK`, which contains no
abbreviable word: the correct answer, not a miss.

### 5.1 Why the threshold is declared and not passed — **the failure, constructed**

**[Observed], design test 4 §4.3:** the identical batch, under two callers who each chose their own
threshold, resolves **differently on 18 of 100 rows** — every one of them an address in the band:

```
'2260 BENSON AVE' @ 0.9091: caller A -> match, caller B -> review
'1602 SHORE PKWY' @ 0.9091: caller A -> match, caller B -> review
'130 BAY   47 ST' @ 0.8667: caller A -> match, caller B -> review
```

Each caller is internally consistent. The store ends up holding duplicates **whose cause is which caller
landed the row** — a fact the curation loop cannot see, cannot enumerate and cannot fix, because nothing
recorded it. So the threshold rides the proposal→approval loop like every other governed fact, is
enumerable, and changes by a governance act rather than by an argument.

**`why` is required and non-empty**, on `ACTIONS.md` §2.4-3's reasoning exactly: an undescribed threshold is
one nobody will ever be able to raise.

**And the gate never softens `unknowable`.** **[Observed]** `policy.verdict(None) == "unknowable"`: a
candidate the scan could not score is not a candidate the gate may call `propose`.

**Rules of §5**

| # | rule | id |
|---|---|---|
| 5-1 | `MatchPolicy` is declared on the entry and rides propose→approve; `resolve_instance` takes no threshold argument | `C20-35` |
| 5-2 | `propose_below <= match_at`, refused at declaration otherwise | `C20-36` |
| 5-3 | `MatchPolicy.why` is required and non-empty | `C20-37` |
| 5-4 | At or above `match_at` is `existing`; strictly below `propose_below` is `proposal`; the band between is the human's, and it is a third outcome rather than a rounded one | `C20-38` |
| 5-5 | An unscored candidate is `unknowable` at the gate as at the call | `C20-39` |
| 5-6 | Two entries in one namespace may declare different policies; two **callers** may not | `C20-40` |
| 5-7 | The policy in force is recorded on the invocation, as `ACTIONS.md` rule 3-8 records the policy the gate judged | `C20-41` |

---

## 6. `Condition` — **one language, twelve terms, three-valued** *(R60)*

R60 ruled that four surfaces reaching for one missing mechanism get **one** language: `Consumer.gate`'s
value-level case (`INTERFACE.md` §10b.4, contortion 11), edge gates (**R22**), `Precondition`'s value case
(`ACTIONS.md` §2.4-9, contortion ACT4) and the ledger query (**Q44**). The ingestion loop is its first
consumer and this row is the spec row R60 said must come first.

```
Condition:
    op:         one of the twelve below
    attribute:  str | None      # required for the ten; None for the two combinators
    value:      Any | None      # required for the six comparisons; a sequence for in/not_in;
                                #   forbidden for is_null/is_not_null and the combinators
    terms:      tuple[Condition, ...]   # required for all_of/any_of; empty for the ten
    why:        str             # REQUIRED, non-empty. ACTIONS 2.4-3's rule inherited

ConditionResult:
    holds:      bool | None     # None = unknowable. Rule U
    why:        str             # REQUIRED when `holds` is None
    unreadable: tuple[str, ...] # the attributes that could not be read
```

**The twelve terms.** Ten operators over **one record's attribute values** — never over another call's
result, because a condition that calls `consumers` is a gate that hides a walk (R60) — plus two combinators:

`eq` · `ne` · `in` · `not_in` · `lt` · `lte` · `gt` · `gte` · `is_null` · `is_not_null` · **`all_of`** · **`any_of`**

**Each is forced by a fixture, and the ones that are not are absent.**

- `eq` / `in` — R59's tenancy predicate, single-tenant and multi-tenant. **[Observed]**, design test 3.
- `in` — contortion 11's own case: an operations dashboard accepting only `{Closed, In Progress}`.
- `ne` / `not_in` — the negations a caller needs without a general `not`.
- `lt` / `lte` / `gt` / `gte` — `find_invocations(since=…)` is a **shipped** primitive (21) taking a
  datetime bound; Q44's ledger query needs both ends. All four are taken as one decision, because a closed
  set that makes a caller encode a bound as its complement is how the off-by-one this vocabulary exists to
  prevent gets written.
- `is_null` / `is_not_null` — the SQL NULL trap, and they are **separate operators on purpose**: see §6.2.
- `all_of` / `any_of` — beacon's own `work_links.user_id: int | None` makes *"mine or unowned"* a real
  host predicate, which needs disjunction.

**There is no `not`, and no `matches`.** Negation exists only as `ne` / `not_in` over a named attribute, so a
caller cannot build an unbounded negation and `not(unknowable)` never has to be argued about; a regex
operator is a query language, which is the door §2.4 of `ACTIONS.md` exists to keep shut.

### 6.1 Three-valued, and both two-valued readings are constructed failures

**[Observed], design test 3** ([`ingest_condition_probe.py`](../tools/ingest_condition_probe.py)), over
**1,373** CMS facilities from two states in **one store** — California and Colorado, the pair sharing the
most provider names (**five**, of 84 names that span more than one state):

- a predicate over `ownership_type`, **an attribute no column of this export carries**, evaluates
  `unknowable` on all 1,373 candidates and the resolution is `unknowable`;
- read as **false**, all 1,373 are excluded and the loop proposes a **new** facility for one that exists —
  mechanism **C**, and the pollution machine;
- read as **true**, two candidates survive across **both** tenants — a cross-tenant leak, which is **R59's
  own stated reversal condition.**

**The third value is not a preference. It is the only reading that is neither of those two.**

**Composition is Kleene**, so a partly unreadable predicate still decides what it can:
**[Observed]** `all_of(T,U)=None`, `all_of(F,U)=False`, `any_of(T,U)=True`, `any_of(F,U)=None`.

### 6.2 `eq` against null is `unknowable`, and `is_null` is a different question

A readable attribute that is **null** makes every comparison `unknowable` — SQL's own rule — and `is_null`
answers it as a **fact**. Two operators, one fact each: `INTERFACE.md` §2.3's Cause B avoided at the operator
level, and the reason is concrete rather than aesthetic: **a host implementing its own gate in SQL must not
be able to disagree with the registry evaluating the same condition.** `eq` with a null operand is therefore
refused **at declaration**, not met at runtime.

### 6.3 Who evaluates it, and what the host still does

R60: **declared on the entry, evaluated by the registry**, so two hosts cannot disagree about what a gate
meant. R59: **the tenancy predicate is the host's.** Both hold, and they are not in tension:

- the predicate is **declared** as a `Condition` on the entry, which is what makes it enumerable and
  governed;
- the **registry** evaluates it over the candidates primitive 23 returned — that evaluation is the
  guarantee;
- the **host** may also apply it inside its adapter as `host_filter`, which is an optimisation and never the
  guarantee. **[Observed], design test 3:** the primitive's signature carries **no tenant parameter**, each
  host `considered=1373` of 1,373 rows, and the predicate did every exclusion. *The separation is not that
  the host hid rows; it is that the exclusion happened where it can be counted.*

### 6.4 The one change R60 requires, and it lands with this document

R60 says the four surfaces are amended **in one change**. This document is that change: `INGEST.md` §6 is the
language, and the three sibling sections gain a pointer to it in the same commit —
[`INTERFACE.md`](INTERFACE.md) §10b.4 (contortion 11), [`EDGES.md`](EDGES.md) §4.3 (**R22**), and
[`ACTIONS.md`](ACTIONS.md) §2.4 (**ACT4**, rule 2.4-9). **The pointers do not change any printed shape or
signature in those documents**, because nothing here is built yet: each says where its missing mechanism now
lives and what still has to happen before it can be used.

**Rules of §6**

| # | rule | id |
|---|---|---|
| 6-1 | The vocabulary is closed at twelve terms; a thirteenth is refused **at declaration** | `C20-42` |
| 6-2 | A `Condition` reads one record's attribute values and never another call's result | `C20-43` |
| 6-3 | Evaluation is three-valued: holds / fails / **unknowable**, with `why` required on the third | `C20-44` |
| 6-4 | An attribute outside the backend's readable set is `unknowable`, never absent-and-therefore-false | `C20-45` |
| 6-5 | A readable-but-null attribute makes every comparison `unknowable`; `is_null` answers it as a fact | `C20-46` |
| 6-6 | `eq` / `ne` / the four comparisons refuse a null operand at declaration | `C20-47` |
| 6-7 | `in` / `not_in` take a sequence; a scalar is refused at declaration | `C20-48` |
| 6-8 | A combinator with no terms is refused at declaration | `C20-49` |
| 6-9 | A combinator carrying an `attribute` or a `value` is refused at declaration | `C20-50` |
| 6-10 | An operator carrying `terms` is refused at declaration | `C20-51` |
| 6-11 | `Condition.why` is required and non-empty | `C20-52` |
| 6-12 | `all_of` is `False` if any term is; otherwise `unknowable` if any is; otherwise `True`. `any_of` is its dual | `C20-53` |
| 6-13 | There is no `not` and no `matches` | `C20-54` |
| 6-14 | The condition is declared on the entry and rides propose→approve | `C20-55` |
| 6-15 | The registry evaluates it; a host-side `host_filter` is an optimisation and never the guarantee | `C20-56` |
| 6-16 | A candidate the predicate could not decide makes the resolution `unknowable` (§3.4) and is never silently dropped | `C20-57` |
| 6-17 | The candidate primitive takes no tenant parameter. R24 / R59 | `C20-58` |

---

## 7. Host obligations, stated

Three things this project **cannot** do for a host, written here because a spec that leaves them implicit
lets everyone wait for someone else.

### 7.1 Consumer registration — `INTERFACE.md` §5.11, and it gates safety rather than convenience

§5.11 says in terms: *"v0 does not specify how a consumer gets registered (decorator, config, lint,
manual)."* **[Observed]** the design partner's `consumers()` returns `known:0`. **Ingest curation cannot be
safe while `consumers()` returns nothing**: proposing an instance into a store with no registered consumers
is proposing blind, and `ConsumerReport.complete` is `false` by construction (`INTERFACE.md` §5.1), so the
registry cannot even say how blind.

**Nothing in this project can fix it. Registering consumers is a host act.** This document states the
obligation; meeting it belongs to the host, and until it is met every ingest proposal's blast radius is
`known=0, complete=false` — which is honest and is not the same as safe.

### 7.2 The entity vocabulary is the host's to register

`propose_type` / `approve` are shipped. A host that wants `task`, `project`, `person`, `org`, `meeting`,
`briefing`, `decision` as `kind="entity"` rows registers them itself. **This is not a build row for anybody**
— it is separated out here so nobody waits on this project for it. (`../decisions/2026-09-02-phase3-repoint-R77-R78.md`
§5, row 0d: **NOT STARTED — and it needs NO work from this project.**)

### 7.3 The tenancy predicate is the host's

R59, unchanged. The host declares it as a `Condition` (§6) on the entry, and it becomes enumerable and
governed by declaring it. A host that does not declare one is running the loop with no tenancy filter — which
is correct for a single-tenant deployment and is a defect in any other, and **this document cannot tell which
a deployment is.**

**Rules of §7**

| # | rule | id |
|---|---|---|
| 7-1 | Ingest curation reports its blast radius from `consumers()`, and reports it as incomplete, never as safe | `C20-59` |
| 7-2 | This document specifies no consumer-registration mechanism; it states the obligation | `C20-60` |
| 7-3 | The entity vocabulary is registered by the host through the shipped calls; this document adds no path for it | `C20-61` |
| 7-4 | A namespace with no declared tenancy predicate runs unfiltered, and the resolution says so rather than implying a filter | `C20-62` |

---

## 8. Printed shapes — and why `check_spec_drift.py` is **not** pointed here yet

[`../tools/check_spec_drift.py`](../tools/check_spec_drift.py) compares a spec's printed shapes and
signatures against the dataclasses and methods that exist. **Nothing in this document exists**, so pointing
the checker here would fail on every line of it. This is `ACTIONS.md` §14's position exactly, and the
sequence is the same: **the build row adds `INGEST.md` to the checker in the same change that lands the
shapes**, and until then the shapes below are a specification and are checked by reading.

The shapes are printed in full in §2 (`InstanceRecord`, `CandidateQuery`, `CandidatePage`), §3 (the call),
§5 (`MatchPolicy`) and §6 (`Condition`, `ConditionResult`). The one shape not yet printed:

```
InstanceContext:                    # the ResolveContext analogue, and it is NOT that object
    label_source:   str | None      # "erm2-nwe9#incident_address" -- WHICH SURFACE the
                                    #   string was read from. INTERFACE 10b.6's finding B
    row_attributes: dict            # the landed row's other columns, opaque
    sibling_labels: list[str]       # other candidate labels in the same batch
    proposed_by:    str | None

InstanceResolution:
    outcome:        str             # the five of 3.1
    ref:            InstanceRef | None      # when "existing"
    confidence:     float | None    # None means "did not score", NOT zero
    reason:         str
    candidates:     tuple[InstanceCandidate, ...]   # ties on "ambiguous"; near misses otherwise
    known:          int             # len(candidates). Rule K
    complete:       bool            # Rule K -- about the candidate SET
    why_incomplete: str             # "" when complete
    scanned:        int             # how many host records the identity read consumed
    tier:           str             # echoed back; goes into provenance

InstanceCandidate:
    ref:            InstanceRef
    label:          str
    score:          float
    discriminators: dict            # the host attributes that did NOT separate the tie
```

**`InstanceContext` is a second context object and that is deliberate.** `ResolveContext` is
**column-shaped** — `sample_values` is *"up to N observed instances"* and `sibling_columns` *"carries most of
the signal"* — which is the right shape for resolving the word `facility` and the wrong one for resolving
`"BURNS NURSING HOME, INC."`. `ACTIONS.md` §5.1 recorded contortion **ACT2** for using `ResolveContext` with
less signal than it was built for; this document declines to make that a second time and says why.

**`label_source` exists because of a finding this project already recorded and could not act on.**
`INTERFACE.md` §10b.6 finding **B**, **[Observed]**: NYC's catalogue and its SODA API disagree on field names
for all three sampled datasets — `borough` versus `boroname`, `latitude` versus `lat` — so *the candidate a
proposer brings depends on which surface it read*, and §10b.6 says in terms that **Phase 3's ingestion layer
must record which surface a column name came from.** This is that field. It is a fact about *us* and so does
not belong in `Provenance.source_version`, which R21 reserves for a fact about the **source**.

---

## 9. Rule → planned id mapping *(standing constraint 8)*

**Sixty-two rules, sixty-two planned ids, `C20-01` … `C20-62`**, listed in each section's own table above.
The prefix is `C20` because `C19` is `ACTIONS.md`'s and is full. **The ids are *planned*:** this row ships no
implementation, so no id is claimed, and the build row claims them in the change that makes each rule
testable — which is standing constraint 8's own rule about spec and ids landing together, applied to a spec
that precedes its build by design (R60: *nothing is built before the spec row*).

**Three vocabulary values are RESERVED here and deliberately NOT minted**, on ruling **R11**'s precedent
— *a value is added in the change that introduces it, and nothing introduces it yet*:

| value | carrier | why it is reserved rather than added |
|---|---|---|
| `instance_source_absent` | `Refusal.reason`, the **thirty-second** | No v0 code path can return it: this row ships none. The build row mints it in `INTERFACE.md` §5.12 **and** `types.REFUSAL_REASONS` in the change that makes it reachable. It is the **sixth capability refusal**, after `proposals_not_stored`, `cannot_record_override`, `consumer_source_read_only`, `edge_store_absent` and `action_store_absent`, and it exists for the reason the first of those does: an empty candidate page would read as *"there is nothing like this"*, which is Rule U's forbidden empty in the one call a caller would believe |
| `instance_ambiguous_at_proposal:<n>` | `warnings`, the **thirty-eighth** | §4.3's mechanical handle. Reserved for the same reason |
| — no third refusal — | | A malformed `Condition` is refused with **`attributes_schema_violation`**, which `ACTIONS.md` rule 2.4-6 already uses for a malformed `Precondition` declaration. **Minting a value for the identical failure one object along is Cause B in the direction nobody guards** — a closed vocabulary grows by one value per *fact*, not per *object* |

**Why the reservation and not the amendment.** `check_spec_drift.py` holds `INTERFACE.md` §5.12's list and
count against `types.REFUSAL_REASONS`, and §5.4's table against `types.WARNING_VALUES`. Amending the prose
without the tuple fails the checker; amending the tuple is product code, which this row does not ship. The
reservation is written so the count stays reconcilable — exactly the reason R11's reservation was written.

---

## 10. Contortions, recorded and **not** designed away

| # | contortion |
|---|---|
| **ING1** | **The ledger cannot tell an instance write from any other host-state change, except by prose.** §4 maps the write to `Effect(op="host_state")`, whose identity **is** its `why` (`ACTIONS.md` §2.5), so two ingest families with differently-worded admissions are two effects. Adding a `propose_instance` op was considered and refused: this project performs no such write, and an op naming an operation it never performs is a permission that misdescribes itself. **The cost is stated, not paid down.** |
| **ING2** | **Nothing enforces that a caller does not propose over an `unknowable` resolution.** Rule 4-7 is a rule of this document; the registry does not execute (`ACTIONS.md` §4) and `record_invocation` records what already occurred, because *refusing to record what already happened is the worst available answer* (`ACTIONS.md` rule 2.5-6). So the loop's most important rule is **advisory at the only door that could enforce it.** Inherited, not introduced — and worse here than in ACTIONS, because ingestion is the highest-volume caller in the system. |
| **ING3** | **`resolve_instance` cannot use `resolve_type`'s resolver, and the two can drift about what one word is.** `_resolve.py`'s `identity_key` / `same_word` are the registry's notion of *the same word* and exist as one function because the kill row's seventh trip is what happens when there are two. This document scores **instance labels**, which are not vocabulary words — `"MILLER'S MERRY MANOR"` is not a candidate for `NAME_RE` — so it cannot reuse that function and must not, and there is now a **second** notion of similarity in the project. **[Observed]** it is a real risk rather than a theoretical one: the seventh trip is exactly this shape one layer up. §11 carries it as a question rather than a design. |
| **ING4** | **A `host_filter` is opaque, so this project cannot tell a narrowing from a tenancy filter.** §2.1 requires the host's filter to be opaque; §6.3 requires the tenancy predicate to be a declared `Condition`. A host that puts its tenancy inside `host_filter` gets the right answer and an **unenumerable** gate — the thing R60 exists to prevent, arriving through the field R58's measurement forced. Rule 6-15 says the registry's evaluation is the guarantee, which makes the outcome safe; it does not make the host's filter visible. |
| **ING5** | **`InstanceRecord.label` assumes a host has one.** CMS has `Provider Name`, 311 has `incident_address`, and a host whose instances are identified by a composite of four columns has none. v0 requires the **host** to choose the label its adapter returns and records that this is a choice the adapter makes silently, with nothing in the protocol able to see it. |
| **ING6** | **The 104 shared names are handled and the 14,498 unshared ones are not proved.** Design test 1 exercises `existing` at multiplicity 1 and `ambiguous` at multiplicity 12. **[Observed]** the file's remaining structure — near-misses that are *genuinely different facilities with similar names* — is exercised only by design test 4's abbreviation band, on a different dataset. The false-positive rate of any real resolver is a **build-row** measurement and this document does not claim one. |

---

## 11. Questions for the supervisor — **Q85 onward**

*(R1–R82 exist and Q1–Q84 are spent; neither number is reused.)*

**Q85 — Does `instance_source_absent` land in this row after all?** §9 reserves it on R11's precedent, which
keeps `check_spec_drift.py` green and the scope fence intact. The counter-argument is R3's plain words: *a
value is added in the change that introduces it*, and this change introduces the **specification** of it.
EDGES v0 and ACTIONS v0 both chose the other way — they amended `types.REFUSAL_REASONS` from a spec row. **A
ruling either way is cheap now and expensive after the build row.**

**Q86 — Is a second notion of *the same string* acceptable, or does the project need one?** Contortion ING3.
`identity_key` / `same_word` are one function *because the kill row's seventh trip is what happens when there
are two*, and this document has now created a second scorer for a different class of string. The honest
options are (a) accept two, named and separated, with the boundary written down; (b) generalise the existing
one; (c) require every instance resolver to be supplied by the deployment, as `Resolver` already is, and
specify only the outcomes. **[Inferred]** (c) is closest to what `PACKAGE.md` §2.6 already does, and it is
the founder's call because it decides whether this project ships a matcher at all.

**Q87 — Should `resolve_instance` be permitted at all when `consumers()` returns `known=0`?** §7.1 states the
obligation and stops. The stronger reading is that ingest **curation** — the propose path — should refuse on
a namespace with no registered consumers, because proposing blind is the failure `consumers()` exists to
prevent. That would make an unmet host obligation a hard stop rather than a warning, which is a policy
decision about somebody else's deployment and is not a spec row's to take.

**Q88 — Does the Rule of the ordering's extension to Phase 3 stand?**
[`../decisions/2026-09-02-phase3-repoint-R77-R78.md`](../decisions/2026-09-02-phase3-repoint-R77-R78.md) §6
recommends it and marks it *pending the founder's word*. **This document was written under it** — every shape
was exercised against CMS and NYC first, and §12 records what the partner's shape would have changed. If the
extension is declined, §12 becomes a list of things to reconsider rather than a list of conflicts recorded.

---

## 12. The partner's shape, exercised against the public data — **conflicts recorded, not resolved**

Written under the extended Rule of the ordering (Q88). **[Observed]** from the supervisor's architecture
framing of 2026-09-02, five open defects in the design partner's capture path are five surfaces of one
missing substrate. Each is checked here against what the public data forced.

| the partner's defect | what this spec does | did the partner's shape change anything? |
|---|---|---|
| capture emits `create_task` and has **no `create_project` verb** — the propose step missing on the entity that matters | §4: an ingest proposal is an invocation of a host-declared family; the missing verb is a family the host declares and approves | **No.** §4 was derived from `ACTIONS.md`'s shipped ledger, and CMS's *"a facility we have never seen"* is the same shape |
| **project scatter** — tasks filed into wrong existing projects, for want of a match-vs-propose gate | §5's `MatchPolicy`, three-valued | **No, and the public data made it sharper.** The 18-of-100 disagreement (design test 4 §4.3) is what forced the threshold onto the entry; the partner's defect argues for a gate but not for *where the gate is declared* |
| relationships auto-applied with **no approval step and no model-identity provenance** | §4.2: `InvocationProvenance` unchanged — actor, tier, approver | **No.** Inherited, not designed |
| **`consumers()` returns `known:0`** | §7.1: stated as a host obligation, and Q87 asks whether it should be a hard stop | **No** — and this is the one where the public data is silent, because CMS and NYC have no consumers either. Recorded as a **gap in the fixtures**, not in the spec |
| the rot sensor cannot fire for want of `last_used_at` | out of scope: `record_use` / `usage` are `INTERFACE.md` §5.7's | — |

**One conflict is recorded and routed.** The partner's capture path resolves *"which project does this task
belong to?"* — an instance question over a small, single-tenant, in-memory candidate set. The public data
forced §2.1's `host_filter` and §3's `unknowable` because **9,764,249** rows cannot be scanned per landed row.
**A protocol shaped only around the partner's case would have neither**, and would be correct for that case
and wrong for the venture claim R78 §4 rests on. **The public-data need wins and the conflict is recorded
here**, per the rule.

---

## 13. Kill-criterion check — required, and not skipped

`ROADMAP.md`'s kill criterion is *two things answering to one identity*. **Fourteen trips are on the record**
([`../decisions/2026-08-29-3c-rulings-R6-R12.md`](../decisions/2026-08-29-3c-rulings-R6-R12.md)), all at the
type-identity surface, none in a real merge.

**This document opens a second identity surface and the check is therefore obligatory.** The question: *does
any resolution outcome let two instances answer to one identity through the confidence gate?*

| the route | what stops it |
|---|---|
| two candidates tie and the top one is returned | **Rule 3-3**: `ambiguous` is decided before `existing`, and rule 3-4 makes `ref` `None`. **[Observed]** on twelve real facilities scoring 1.0 |
| a truncated scan finds nothing and a duplicate is proposed | **Rules 3-5 / 3-6 / 3-7**: `unknowable` is an outcome and `proposal` requires a finished scan. **[Observed]** constructed at `cms:entity:facility#745057` |
| an undecidable tenancy predicate silently excludes the real match | **Rules 6-4 / 6-16**: `unknowable` is neither false nor true. **[Observed]** both readings constructed on 1,373 rows |
| two callers with different thresholds each create a row | **Rule 5-1**: the threshold is the entry's. **[Observed]** 18 of 100 rows disagree when it is not |
| an ingest family proposes a `kind="predicate"` type at volume | **Rule 4-8**: `ACTIONS.md` §2.5's allowlist, restated here because ingestion is the highest-volume caller that could reach it |

**The check does not trip, and the reason is worth stating plainly: every one of the five routes was closed
by a rule whose evidence is a constructed failure rather than an argument.** What this document cannot claim
is that the *list* is complete — that is what the adversarial loop is for, and §14 of
[`../runs/7A-RUN.md`](../runs/7A-RUN.md) carries what it found.

---

## 14. Exit criteria — `ROADMAP.md` Phase 3 row 7a, checked

| the brief asked for | where it is |
|---|---|
| the seam decided by design test 1 **before** anything else was written | §1, and [`../runs/7A-RUN.md`](../runs/7A-RUN.md) §0 is the pre-registration, committed before the probe existed |
| candidate-retrieval primitives, each with a capability flag, each paged per R58 | §2 — two primitives, two flags, three states measured live |
| `resolve_instance` with the four-outcome shape **or a different closed set argued** | §3 — **five**, and T1.5 is the argument |
| the propose-at-ingest contract | §4 — an invocation, no new object |
| the match-vs-propose confidence gate as a governed fact | §5 — and §5.1 constructs the alternative's failure |
| `Condition` as the loop consumes it, with the three sibling sections amended in one change | §6, §6.4 |
| host obligations stated | §7 |
| printed shapes, rule→id mapping, contortions, questions | §8, §9, §10, §11 |
| every shape exercised against the public data, conflicts recorded | §12, and the four design tests in [`../runs/7A-RUN.md`](../runs/7A-RUN.md) |
