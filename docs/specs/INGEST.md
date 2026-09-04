# INGEST — the mapping layer between landed rows and the ontology

**Version:** `v0` — **unstable.** Every name, field and return shape here may change without a
deprecation path (standing constraint 4).
**Status:** Draft, 2026-09-03, **amended the same day by the first adversarial round** — three lenses,
eleven BLOCKING findings, every one constructed and run. What each changed is in
[`../runs/7A-RUN.md`](../runs/7A-RUN.md) §6. Satisfies `ROADMAP.md` Phase 3's **first row**, opened by the
founder 2026-09-02. Deliverable **#7a** of the ordering. **This document ships no code.** Its design tests
are runnable probes under [`../tools/`](../tools/); their observed output is in the run record.
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
reference shape**, **one declared policy**, **one condition language**, and **no table**.

### 0.1 Non-goals — one line each

- **No connectors.** Extraction and loading are Airbyte's; this layer consumes what they land. `VISION.md` §6.
- **No orchestrator and no scheduler.** When a batch runs is the host's; `ACTIONS.md` §4's *the gate is
  advisory by construction* is inherited unchanged.
- **No executor.** This document specifies no call that performs a write against a host's data.
- **No HTTP.** No routes, no auth, no pagination-over-the-wire. `INTERFACE.md` §1's non-goal, unchanged.
- **No tenancy dimension.** R59 stands: tenancy is the host's predicate, made expressible by §6. Reversing
  it is a Phase 4 change, and §6's design test is what would force it.
- **No instance store.** **Decided by design test 1, and three adversarial lenses each tried to overturn it
  from a different direction and could not** — see §1.
- **No instance-level proposal loop of its own.** §4 makes an ingest proposal an **invocation of a
  host-declared action family**, using the ledger `ACTIONS.md` already ships. **No object is stored by this
  document.** It does ask `ACTIONS.md` for five additive amendments, named in §4.4 — round 1 found the
  original claim of *"nothing new"* false, and §4 is the section it was false in.
- **No change to `resolve_type`.** **R77**, non-negotiable. §3's call is a new call in this document.

---

## 1. The seam — **R78, CONFIRMED by design test 1, and held by three adversarial lenses**

**The question R78 put, deliberately falsifiably:** does this project become an instance store, or does it
define resolution *over instances the host already holds*?

**Answer: the host holds the instances. [Observed], design test 1** — 16/16 checks over the full CMS
health-citations file (**165,336,194 bytes, 419,479 rows, 14,627 CCNs, 104 provider names shared by more
than one CCN**, all four reproducing `USE-CASES.md`'s pre-registered figures and **all four independently
re-derived from the real file by round 1's public-data lens**). Every outcome of §3's call was reached with
(a) a table the host owns, (b) two **read-only** primitives, and (c) **no instance row in the registry**:
after a walk-through that scanned 14,627 host rows five times, the **shipped** `ontoloche.Registry` on
SQLite held exactly `[('entity', 'facility')]`. The expectations were pre-registered in
[`../runs/7A-RUN.md`](../runs/7A-RUN.md) §0, in a commit that predates the probe.

**And the confirmation survived the loop, which is the part worth more than the design test.** Round 1's
three lenses each attacked R78 from a different direction — *does a capture path force a write?*, *does any
outcome need a registry row?*, *does the seam hold when the scan pages?* — and **[Observed]** none could
break it. The integrator's sentence is the one to keep: *every duplicate I produced was written by the
host, exactly as rule 4-2 says it would be.* The loop produced several duplicates; **none of them landed in
this project's store.**

**Three consequences, and the second is the structural argument.**

1. **The vocabulary half is unchanged.** The registry holds `kind="entity"` rows — `facility`, `project`,
   `task` — through `propose_type` / `approve` exactly as today. Nothing in this document adds a kind.
2. **Two primitives, not three, and the count is the evidence.** [`EDGES.md`](EDGES.md) §7.1 takes three
   (`put_edge` / `get_edge` / `find_edges`) and [`ACTIONS.md`](ACTIONS.md) §9 takes three, because this
   project **stores** edges and invocations. Instances are the host's, so **there is no `put`** — and a
   protocol that needed one would be an instance store with a different name.
3. **The type-side half of the seam was already built.** **[Observed]** `resolve_type("BURNS NURSING HOME,
   INC.")` returns `outcome="not_a_type"` with reason **`instance_not_type`** — a branch live in
   [`../../ontoloche/_resolve.py`](../../ontoloche/_resolve.py) since row #1. The type registry does not
   merely decline the instance question; it **names** it. `INTERFACE.md` §1's non-goal and §10.3's
   resolution both stand and gain a pointer to this document rather than being deleted (R77).

> **What the confirmation does NOT claim.** It was not shown that an instance store is *unnecessary in
> general*; it was shown that **every outcome is reachable without one** and that three reviewers trying to
> force one failed. [`../runs/7A-RUN.md`](../runs/7A-RUN.md) §1.4 states what would still overturn it.

**Rules of §1**

| # | rule | id |
|---|---|---|
| 1-1 | This project stores no instance rows and mints no instance identifiers. An instance is named by an `InstanceRef` (`EDGES.md` §2.1) whose `id` the **host** allocated | `C20-01` |
| 1-2 | Instance resolution is a **new call** in this document and never an extension of `resolve_type`. R77 | `C20-02` |
| 1-3 | A registry whose adapter declares `resolves_instances=False` refuses every call in this document with `instance_source_absent` (§9) — **never** an empty candidate set, which would read as *"there is nothing like this"* | `C20-03` |

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
    kind:        str            # always "entity" in v0. Contortion ING7
    type_name:   str
    label:       str | None = None    # what the landed row calls it. A HINT ONLY -- rule 2-8
    host_filter: Mapping[str, Any] | None = None   # NAMED filters the host declared. 2.1
    limit:       int | None = None    # the ADAPTER pages. R58
    after:       str | None = None    # opaque cursor. The ENCODING is the build row's

@dataclass(frozen=True)
class CandidatePage:
    records:        tuple[InstanceRecord, ...]
    known:          int | None  # None = the backend cannot count. NOT 0. Rule U
    complete:       bool        # about the SET THE QUERY NAMED, host_filter included. 2.1
    why_incomplete: str | None
    next_after:     str | None
```

**22. `get_instance(namespace: str, kind: str, type_name: str, instance_id: str) -> InstanceRecord | None`**
Confirms one reference. `None` means **absent**, which is a fact — the host always knows whether its own key
exists, exactly as `get_edge` does (`EDGES.md` §7.1 primitive 17). **Its caller is §3's identity read
re-confirming a resolved `ref` at the moment of use** — the R54/R55 lesson (*identity re-verified at the
read*) at the instance surface — and §4's propose path confirming the ref the host minted.
**Uncertainty:** `resolves_instances=False` ⇒ raises `NotSupported`; the registry checks the capability
first and never calls this, surfacing `Refusal(reason="instance_source_absent")`.

**23. `find_instance_candidates(q: CandidateQuery) -> CandidatePage`**
The one call behind §3. **Scoring is not pushed into the adapter**: the adapter returns records, the
registry scores them. That is `PACKAGE.md` §3.1's boundary — an adapter that knew about confidence would
know about `InstanceResolution`, and `C0-04`'s source-inspection test would have a new identifier to police.
**Uncertainty:** the general rule is `find_types`': a filter the backend cannot apply returns
`complete=False` with a `why`, **never** a filtered-looking empty page.

**No third primitive for counting and none for writing.** Counting is `CandidatePage.known`; writing is the
host's. Both were considered and dropped, for `EDGES.md` §7.1's reason: a primitive that exists only to
express a policy is a policy inside the adapter.

### 2.1 `label` is a hint that may NOT narrow; `host_filter` is a named, declared filter

*(Both halves of this section were rewritten by round 1. The original said a backend **may** use `label` to
narrow and left `host_filter` an opaque string, and both were constructed as duplicate factories — findings
P2 and M8.)*

**`label` says what the landed row calls the thing, and a backend may use it to ORDER a page but never to
omit a record.** **[Observed], P2:** two backends both conformant to the original rule — one ignoring
`label`, one narrowing on it — answered design test 4's own batch differently: the ignoring host routed 23
banded rows to a human; the narrowing host answered **`proposal` with `candidates_seen=0` and
`complete=True`** for all 23, because nothing was truncated and so `unknowable` could not fire. That is
**§5.1's own argument one layer down**: 23 duplicates whose cause is which backend answered. So narrowing
is not a backend's discretion; it goes through `host_filter`, where it is named and declarable.

**`host_filter` is a MAPPING of named filters to values, not an opaque expression.** **[Observed], M8:**
`instance_filters` is a set of names and the original `host_filter` was a free-form string
(`"agency='NYPD' AND complaint_type='Illegal Fireworks' AND incident_zip='11214'"`), so rule 2-10 had no
decidable test and rules 2-7, 2-9, 2-10 and `C20-03` — the spec's only defence against contortion ING4 —
were untestable as written. As a mapping, `{"agency": "NYPD", "complaint_type": "Illegal Fireworks",
"incident_zip": "11214"}`, each key is checkable against `Capabilities.instance_filters` and a key outside
it forces `complete=False` with a `why` naming it. **The VALUES stay opaque to this project; the KEYS do
not.**

**`complete` is about the set the query named, `host_filter` included — and a `proposal` off a narrowed set
says so.** **[Observed], M2:** over a 725-row narrowed slice of a 9,764,249-row partition, **3,330 of 3,330**
landed rows resolved `proposal` with `complete=True`, one of them at an address the same host table holds
**122** rows for. `complete=True` is honest there — the query named that slice — and it is *cheap*, so a
proposal made over a narrowed set carries `instance_narrowed_proposal:<filter keys>` and the reviewer can
see what was not looked at.

**Why the narrowing exists at all, measured.** **[Observed], design test 2** (live against `erm2-nwe9`,
2026-09-03): one 50,000-row page — the host's own ceiling — took **1.3 s to 8.4 s in same-day runs**, and
exhausting `agency='NYPD'` needs **196 of them**. **[Inferred]** that is **minutes, not seconds, for one
landed row**, and every figure is a lower bound because deep-cursor decay is ignored. *(The original text
printed `1.26s` and `4.1 minutes` to two decimals; round 1 re-ran it the same day and got `8.39s` and
`27.4 minutes` — 6.7x. The argument survives and the precision did not, so the precision is gone.)* The
same read drains to exhaustion in **four requests** once the host's own predicate narrows 9,764,249 rows to
**725**.

**So candidate retrieval is affordable exactly when the host says it is**, and the narrowing is a fact about
the host's table that this project neither invents nor validates. A layer that arranged its own index over a
host's data would be holding a copy of it, which is §1 again.

### 2.2 Paging, under R58's one rule and no other

The three states a caller can be in are the three R58 names, and **[Observed], design test 2** all three
come off primitive 23 against the live 9.7-million-row partition and are distinguishable from the report
alone:

| the page says | it means | observed 2026-09-03 |
|---|---|---|
| `complete=True` | this is the **set the query named** | `known=725 complete=True next_after=None` |
| `complete=False`, `next_after` present | this is a **page**; ask again | `known=200 complete=False next_after='200'` |
| `complete=False`, `next_after` absent, `why_incomplete` set | **truncated** — the rest cannot be read from this surface | `known=1000 complete=False next_after=None why='scan budget of 2000 rows reached…'` |

**`known` counts what THIS PAGE materialised.** `complete` is about the **set**. A backend that cannot count
returns `known=None`, which is Rule U and which `0` would falsify.

**And a guard never reads a page.** §3's identity read is exactly that — *does more than one thing answer to
this?* — so it is an **internal exhaustive read**: the registry loops `next_after` to `None`, or reports the
read as **truncated** and answers `unknowable` (§3.4). It never treats a page as a set.
`INTERFACE.md` §5.6's caller-facing paging and this internal read must not share a code path that can
discard a cursor; R58's own fifth-trip evidence is why — **and round 1 reproduced that fifth trip at this
surface, which is §3.4.**

**The cursor's encoding is deliberately NOT decided here.** Opaque string, exactly as at the adapter — R58
leaves the contents to the row that builds it.

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
    #: The `host_filter` KEYS primitive 23 honours faithfully. U3's shape exactly: a
    #: key listed here is applied; a key NOT listed comes back with `complete=False`
    #: and a `why` naming it -- never applied-looking and never silently dropped.
    #: This is why 2.1 makes `host_filter` a named mapping: a set of names cannot
    #: govern an opaque expression, and round 1 measured that it did not.
```

**Nothing else.** A `counts_instance_candidates` flag was considered and refused: `known: int | None`
already carries that fact, and a second home for one fact is `EDGES.md` §2.4's rule.

### 2.4 The flat-form guard, at the surface that hands out refs

**[Observed], K8:** `type_name='facility'` with `instance_id='015009#2024-03-11'`, and
`type_name='facility#015009'` with `instance_id='2024-03-11'`, produce the **identical** `ref_key` —
`'cms:entity:facility#015009#2024-03-11'` — and it round-trips to the first. That is `C19-82`, row 6c's own
integrator finding (*a confident reading of the wrong thing*), reachable at a **new** door: the shipped
guard [`flat_form_problem`](../../ontoloche/actions.py) is enforced at `ACTIONS`' invocation write door
only, and primitive 23 and `InstanceResolution.ref` hand a caller a ref without passing through it.

**[Observed]** the grammar is sound for the field rule 1-1 actually declares opaque — `'015009#2024'`,
`'a:b:c'`, `'#'`, `''`, `'x#y:z#w'` all round-trip as `instance_id`. **It is the fields this document does
NOT declare opaque — `namespace`, `kind`, `type_name` — that break it**, and the guard already catches them.

**Rules of §2**

| # | rule | id |
|---|---|---|
| 2-1 | The protocol adds exactly two primitives, both **reads**. A write primitive for instances is a conformance failure | `C20-04` |
| 2-2 | `get_instance` returns `None` for absent, never a manufactured record | `C20-05` |
| 2-3 | `find_instance_candidates` pages under R58's one rule: `known` counts the page, `complete` is about the set the query named, `next_after` says whether there is more | `C20-06` |
| 2-4 | A truncated read is `complete=False`, `next_after=None`, `why_incomplete` set — distinguishable from a page by the report alone | `C20-07` |
| 2-5 | A backend that cannot count returns `known=None`, never `0` | `C20-08` |
| 2-6 | The adapter scores nothing. `C0-04`'s source inspection extends to these two primitives | `C20-09` |
| 2-7 | A `host_filter` **key** the backend cannot apply returns `complete=False` with a `why` naming that key; it is never silently ignored | `C20-10` |
| 2-8 | **`label` may order a page and may never omit a record.** A backend narrows only through `host_filter` | `C20-11` |
| 2-9 | `resolves_instances` defaults `False`, and every call here refuses `instance_source_absent` when it is | `C20-12` |
| 2-10 | Every `host_filter` key named in `instance_filters` is honoured faithfully; a key outside it is reported, per U3's rule | `C20-13` |
| 2-11 | An identity read exhausts the cursor or reports **truncated**; it never reads one page and decides | `C20-14` |
| 2-12 | `host_filter` is a mapping of **declared keys** to opaque values. A free-form expression is a conformance failure, because `instance_filters` cannot govern one | `C20-63` |
| 2-13 | `complete=True` over a `host_filter`-narrowed query is honest **and narrow**: any `proposal` decided on it carries `instance_narrowed_proposal:<keys>` | `C20-64` |
| 2-14 | An `InstanceRecord` whose `namespace`, `kind` or `type_name` would make `ref_key` unfaithful is refused at the primitive, citing `flat_form_problem` | `C20-65` |
| 2-17 | Within one closure read, records sharing `(namespace, kind, instance_id)` under **different member names** are **one candidate**, resolved under the name the closure resolves to. Rule 3-19 widened the extent along a dimension rule 2-16's key still carries, so mid-migration one facility answered `ambiguous known=2` to itself (round 3, K2). Rule 2-16 remains a **different** question: two DIFFERENT rows sharing one id under ONE name | `C20-89` |
| 2-16 | A candidate page's `instance_id`s are **distinct**, or the read is `unknowable` with a `why`: a page whose own ids do not distinguish its own rows makes the extent uncountable, and §3.2's set test would silently collapse two rows to one. §3.4b | `C20-75` |
| 2-15 | `get_instance` is evaluated against the entry's declared `Condition` (§6) before its record is returned; a record the predicate fails is `None` with a `why`, and one it cannot decide is a refusal, never a silent pass | `C20-66` |

---

## 3. `resolve_instance` — **five outcomes, and completeness is checked before ANY of them**

```python
def resolve_instance(
    candidate: str,
    context: InstanceContext,
    *,
    type_name: str,
    namespace: str = "default",
    tier: str,                          # INTERFACE 2.7 -- REQUIRED, not defaulted
    host_filter: Mapping[str, Any] | None = None,   # the HOST's narrowing. 2.1
) -> InstanceResolution: ...
```

**There is deliberately no `min_confidence` parameter and no `predicate` parameter.** `resolve_type` has the
first; this call has neither, and §5 and §6 are the reasons: the threshold and the tenancy predicate are
both **declared, governed facts on the entry**. **[Observed], P3:** the original signature took
`predicate: Condition | None = None`, and omitting that optional keyword made **5 of 5** cross-tenant
shared names resolve differently and handed a California caller Colorado `InstanceRef`s — **R59's own
stated reversal condition, reached by leaving out an argument.** §5.1 refused a per-call *threshold* on
exactly this reasoning; admitting a per-call *predicate* two sections earlier was the same defect the same
document argues against.

### 3.1 The outcomes, and why five rather than four

`resolve_type` has four: `existing` / `proposal` / `not_a_type` / `none`. The mirror was written as four and
**design test 1 broke it**.

| outcome | means |
|---|---|
| `existing` | **exactly one** held instance answers to this candidate, over a **finished** scan |
| `ambiguous` | more than one does — **or one does, but not confidently enough to be sure it is the same thing.** A human's call, and §4.3 routes it |
| `proposal` | a **finished** scan of a non-empty candidate space found none, so this is a new thing |
| `not_an_instance` | the candidate names a class, a column or an artefact — not one thing of that class |
| `unknowable` | the identity read **did not finish**, so no statement about identity can be made |

**The fifth is an outcome and not a flag, and the failure was constructed rather than argued.**
**[Observed], design test 1 T1.5:** with the fifth value absent, a scan cut off before the matching row
returns `outcome="proposal"` for a facility that exists **in the same table** —
`cms:entity:facility#745057`, confirmed `existing` at 1.0 by the uncapped control **in the same run**. The
proposal is well-formed, provenance-bearing, approvable, and wrong: *the pollution machine with a governance
loop bolted to the front of it.* A `complete=False` flag beside `outcome="proposal"` is a caller's to
ignore; an outcome is not.

> **A second claim stood here and is WITHDRAWN.** The original §3.1 said design test 2 *"reaches the same
> value from the opposite direction"* and called that *"two independent routes"*. **[Observed], M1:** that
> probe calls **no resolver** — it computed `outcome = "unknowable" if not p_trunc.complete else …`, a
> restatement of the check three lines above it, and a rule-3-5-**violating** resolver inserted over the
> same truncated page left it printing `10/10 checks pass`. **There was one route, not two.** Design test 2
> now calls the resolver, so the second route is real; the claim is re-made on the amended probe and the
> withdrawal is left on the record, because a claim asserted and not run is exactly what
> [`check_spec_drift.py`](../tools/check_spec_drift.py) exists to catch, pointing inward.

### 3.2 `ambiguous` is decided BEFORE `existing`, and it is a SET test

**[Observed], design test 1 T1.2:** `"MILLER'S MERRY MANOR"` is the label of **twelve** distinct Indiana
facilities in the CMS file, every one scoring **1.0** on the name. A resolver that took the top candidate
would answer `existing` at 1.0 — **the confidence `INTERFACE.md` §5.3 calls a guarantee** — and file eleven
facilities' citations into a twelfth's record.

**The tie test is over the SET, not over the top two.** *(Round 1, K2. The original compared
`top[0] - top[1] <= ambiguity_margin`, and* **[Observed]** *nothing constrained `ambiguity_margin` against
`1 - match_at`: with this document's own printed numbers — `match_at=0.97`, `ambiguity_margin=0.02` — the
match band is width 0.03 and the margin is 0.02, an arithmetic gap in the spec's own figures. Seven real CMS
pairs land in it, including* `MAGNOLIA MANOR OF COLUMBUS NURSING CENTER - WEST` *and* `- EAST`, *two
genuinely different Georgia facilities, and* `'Mountain View Health Care'` *(115688) against*
`'MOUNTAIN VIEW HEALTHCARE'` *(265412) at 0.9796 → `existing` at 1.0 with `known=2`, over a complete scan,
on ordinary data.)*

**The tied set is every candidate at or above `match_at`, together with every candidate within
`ambiguity_margin` of the top. `existing` requires that set to have exactly one member.** That is stronger
than any arithmetic between the two numbers — **but it is not the whole test, and round 3's K7 found that
this sentence used to claim it was.** A candidate below `propose_below` is not a tie: it is a candidate the
entry has declared too weak to be *anything*, and admitting it to the tied set turns *"nothing here is close
enough"* into `ambiguous`. **[Observed], K7:** removing that floor so the kit matches rules 3-3 / 5-8 as they
were worded **reddens a check on the real 14,627-row CMS file**, so the floor is load-bearing on real data and
was, until now, in the code and not in the document. Rule **5-12** states it.

`ROADMAP.md`'s kill criterion is *two things answering to one identity*. **This is that criterion one level
below where its fourteen trips live**, and `InstanceResolution.ref` is `None` on `ambiguous` — asserted as a
negative by the probes, because *the outcome was right and the ref was populated anyway* is the shape trips
eleven and twelve took. **[Observed]** round 1 attacked that rule from three directions and it held every
time; what failed was its **premise**, which is §3.4.

### 3.3 `not_an_instance` mirrors `not_a_type`, and its cost is now measured

`INTERFACE.md` §5.3 gained `not_a_type` because a 99.988%-redundant column resolving to `None` reads as *"go
propose it"* and hands the pollution machine its first type. The instance analogue is a landed cell that is
not an instance at all. **[Observed], T1.4:** `"Provider Name"` answers `not_an_instance` and the host table
is **never scanned for it** (`scanned=0`).

**v0 does not define the classifier**, exactly as `INTERFACE.md` §2.8 does not define semantic detection —
**and round 1 measured what that costs, in both directions, so the absence is priced rather than waved at.**
**[Observed], M9**, against the only classifier this row ships (an eleven-word class list):

- **false positives: 0 of 14,498** real CMS provider names. Nothing real was refused.
- **false negatives: 22 of CMS's 23 column headers are NOT caught** — `CMS Certification Number (CCN)`,
  `Provider Address`, `City/Town`, `State`, `ZIP Code`, `Survey Date` and the rest. **T1.4 picked the one
  header the hand-written list contains.**
- **and on UC3: 16,001 distinct `erm2-nwe9` values carrying 861,161 rows (3.9% of the dataset) are street
  names with no house number** — `'BROADWAY'` 24,154 rows, `'5 AVENUE'` 12,821 — *classes, not instances*,
  every one of which passes as an instance and becomes a well-formed provenance-bearing proposal.

**So §3.3's *"the cheapest correct answer is the one that asks the host nothing"* is true of 1 of 23 real
cases**, and the outcome's reachability is specified while its accuracy is a build-row problem with two
numbers now attached to it. `_resolve.py`'s `instance_not_type` is the mirror already shipped on the other
side of the seam; **Q86** asks whether this project should ship a matcher at all.

### 3.4 Rule U, at this call — **completeness is checked before the candidate set is INTERPRETED**

> **Standing rule (e).** *The extent an identity is decided over, **AND the facts that govern the
> decision**, are the same at every door that reads it, writes it, keys it, gates it or counts it — and a door
> that cannot prove **both** answers `unknowable` rather than deciding.*
>
> Proposed by ruling [**R85**](../decisions/2026-09-04-7a-supervisor-ruling-R85.md) over `I-1`…`I-6` and
> **amended by [R86](../decisions/2026-09-04-7a-supervisor-ruling-R86.md) before it was ever recorded**, because
> a seventh cell fell outside its first wording. The seven instance-surface records are not seven defects but
> **one question asked at seven doors** — *which host rows answer to this identity, did the resolution see all
> of them, and by whose rules was the answer judged?*
>
> | the decision is wrong because the set was… | cell |
> |---|---|
> | **truncated** — the scan stopped and said so, and the match path ignored the `why` | `I-1` |
> | **mis-walked** — the chain was followed one hop and reported `complete=True` | `I-2` |
> | **mis-written** — the read is bound by the chain and the write door is not | `I-3` |
> | **mis-keyed** — the act scopes on the raw label, the gate decides on `norm` | `I-4` |
> | **mis-timed** — the guard's window closes when the proposal drains, before the write lands | `I-5` |
> | **mis-counted** — a page's ids are not required to be distinct, so two rows collapse | `I-6` |
> | **mis-governed** — the set is right and the facts that govern the decision belong to another entry | `I-7` |
>
> Rule U is the rule at **this** door; §3.4a at the type-closure door; §3.4b at the counting door; §5.3 at the
> **governing** door; §4.3 at the act, key, guard and write doors.

*(This section is the one round 1 broke, and both of the lenses that broke it reached the same place from
opposite directions. The original ordered the check before **the emptiness** was interpreted; rule 3-5's
table row already said the wider thing — "whatever the candidates found" — and the prose, §13's route table
and this row's own probe all implemented the narrow one.)*

**An identity read that could not finish yields `unknowable`, whatever it found.** Not *"whatever it failed
to find"*: **whatever it found.** An unread row may tie the one that was read, and *a guard that could not
be evaluated has not said the collapse is safe* — which is `INTERFACE.md`'s own sentence at
`successor_unregistered`, arriving one identity surface down.

**The construction, [Observed], K1 / P1**, with an ordinary `scan_cap` — R58's own third state, the same
mechanism T1.5 already uses — set one row past the first of the twelve:

```
CONTROL   (uncapped)   outcome='ambiguous' ref=None conf=1.0 known=12 complete=True  scanned=14627
TRUNCATED (cap=3541)   outcome='existing'  ref='cms:entity:facility#155049' conf=1.0
                       known=1 complete=False scanned=3541
                       reason='one host row answers to "MILLER'S MERRY MANOR"'
```

**`conf=1.0` is `INTERFACE.md` §5.3's guarantee, handed out for a string twelve facilities answer to**, with
eleven of them unread — and the tie test that was supposed to stop it was evaluated over a **partial
extent**, which is **the register's fifth kill-row trip verbatim**, one identity surface down.

`unknowable` also absorbs three cases that are **not** truncation, and naming them stops each becoming its
own value — **and every one of them is now guarded before the interpretation, not after it**:

1. the host's declared tenancy `predicate` was **undecidable** on candidates the scan returned (§6, design
   test 3). **[Observed], K5:** under the old ordering this leaked `existing` at 1.0 on *another tenant's
   row*, from a page the host had said could not be read as the set;
2. the adapter could not apply a `host_filter` **key** it was handed, so the page answers a wider question
   than the caller asked and cannot be read as the set;
3. the backend returned `known=None` and `complete=False` together — it neither counted nor finished.

**And a scan that read NO rows is not evidence of absence.** **[Observed], K6:** a `CandidateQuery` naming a
type that had been retired toward a successor returned `proposal` over `scanned=0` with `complete=True` — *a
confident "there is nothing like this" from a read of zero rows*, which is Rule U's forbidden empty in the
one call a caller would believe. Two rules close it: the identity read **resolves `type_name` through the
successor chain** before it queries (which `EDGES.md` rule 4.3-14 / **R38** already requires of `neighbors`,
and which this document did not say), and a `proposal` requires the candidate space to have been non-empty.

### 3.4a The successor CLOSURE — **the chain, not one hop, and the extent is the whole chain**

**This section is written from [`ontoloche/registry.py`](../../ontoloche/registry.py)'s `_identity_closure`
rather than from R38's words, and that is a rule rather than a courtesy.** Ruling
[**R84**](../decisions/2026-09-04-7a-supervisor-ruling-R84.md) sharpened standing rule (d): *the enumeration
crosses the document boundary — a rule minted in a specification must name the shipped callers it binds, and
where a shipped caller already implements the rule, the specification cites that implementation as its
normative reference rather than restating the ruling the implementation was derived from.*

**Why the clause exists, and it is this document's own failure.** Round 1 minted rule 3-14 citing **R38** and
implemented **none** of R38's three termination rules; the shipped `_identity_closure` implements all three,
and had done since row 4d round 2, whose own comment reads *"**The chain, not one hop** … a vocabulary curated
**twice** — the ordinary outcome after two passes — lost §5.10's promise."* `I-2` is a defect the type surface
had **already closed** and this document re-opened by restating the ruling instead of citing the code.

Four things follow, and the fourth is the one `I-3` forced:

1. **The walk is a closure**, with a **visited set** (a cycle is not an error to construct), a **hop cap**, and
   an honest early stop.
2. **An early stop is `complete=False` WITH a `why`** — because rules 3-5 / 3-6 guard the completeness the read
   *reports*, and a walk that stops silently reports `complete=True` with `why_incomplete=''`, which is exactly
   how `I-2` passed round 1's headline fix.
3. **A dangling successor never falls back to the predecessor's entry.** Querying one type while holding
   another's governed facts is **the eighth trip's shape** — a guard holding one fact while deciding about
   another — and R84 named it as a rider defect that does not get to ride out of this round unnamed.
4. **The identity's extent is the WHOLE closure — in BOTH directions, aliases included.** The shipped
   function this section cites walks the chain **forward**, walks it **backward** (*"the direction
   `merge_types` actually produces and **the one a caller reaches after doing the right thing**"*), and
   **consults aliases** (*"`merge_types` writes both a successor and an alias for one absorption and a
   hand-written alias is one the successor scan would miss"*). **Round 3 found this document had taken the
   forward relation alone** — `I-8`, and the worst outcome the series has produced, because the SURVIVOR of a
   retirement is the name every new caller uses and the act wrote a second row for it in **`auto` mode with
   no human**. Rules 3-20 and 3-21 adopt the other two.

   > **R87's clause, which this failure minted: a citation of a shipped implementation as normative binds the
   > citing document to ALL of it, and must enumerate BY NAME, in the same change, what it ADOPTS and what it
   > DECLINES.** So, for `_identity_closure`: **ADOPTED** — the forward relation (rule 3-14), the backward
   > relation (rule 3-20), the alias relation (rule 3-21), the visited set, the hop cap (rule 3-16, now at
   > **16** to match `_IDENTITY_CHAIN_CAP` rather than the 8 round 2 chose without saying why), and the
   > honest early stop. **DECLINED, and each is a recorded contortion rather than prose** — see **ING12**:
   > this document answers `unknowable` where `_identity_closure` continues with `complete=True`, for a
   > **cycle** and for a **dangling successor**, because the shipped function is answering *"which names mean
   > this"* for a read that can tolerate a partial answer, and this one is answering *"may I mint an
   > identity"*, which cannot.

5. **The endpoint alone is a smaller set than the extent.** A row written under a name that has since
   been retired is still one of this identity's rows until the host migrates it. An endpoint-only read is a
   **smaller set than the extent**, so it proposes a duplicate for a facility the same store already holds —
   which is `I-3`, and which standing rule (e) forbids in one sentence.

### 3.4b The extent must be COUNTABLE — `I-6`

Rule 1-1 makes `instance_id` the host's and opaque, and until this change nothing required a candidate page's
ids to be **distinct**. §3.2's set test dedupes on the flat `ref_key`, so two different host records under one
id collapse to one candidate and the second **vanishes from `candidates` entirely** — `existing` at 1.0 with
`known=1` over a store holding two rows. **ING5 already measured that a host keyed on a non-unique natural
column is the ordinary case** (59.7% of `uvpi-gqnh`'s 683,788 instances share an address), so this is not an
exotic host. A read whose own ids do not distinguish its own rows cannot count the extent, and therefore does
not decide.

**Rules of §3**

| # | rule | id |
|---|---|---|
| 3-1 | The outcome vocabulary is closed at five. R3 applies: a sixth is a §-row change with a contract id | `C20-15` |
| 3-2 | `resolve_instance` is a distinct call and no argument of `resolve_type` reaches it. R77 | `C20-16` |
| 3-3 | `ambiguous` is decided before `existing`, over the **set**: every candidate at or above `match_at`, plus every candidate within `ambiguity_margin` of the top | `C20-17` |
| 3-4 | On `ambiguous`, `ref` is `None` and every tied candidate is returned | `C20-18` |
| 3-5 | An identity read that did not finish is `unknowable`, **whatever the candidates found** — checked before the candidate set is interpreted at all | `C20-19` |
| 3-6 | **No `complete=False` result carries any outcome but `unknowable` or `not_an_instance`.** `existing`, `ambiguous` and `proposal` each require a finished read | `C20-20` |
| 3-7 | `proposal` requires `complete=True` on every page the identity read consumed | `C20-21` |
| 3-8 | `not_an_instance` is reachable without reading the host table at all | `C20-22` |
| 3-9 | `confidence` is `float \| None`; `None` means *did not score*, never `0.0`. `INTERFACE.md` §5.3's rule | `C20-23` |
| 3-10 | The call takes no `min_confidence` and no `predicate`: both are the entry's. §5, §6 | `C20-24` |
| 3-11 | `tier` is required and is echoed back for provenance. `INTERFACE.md` §2.7 | `C20-25` |
| 3-12 | An undecidable host predicate makes the resolution `unknowable`, never a narrower candidate set | `C20-26` |
| 3-13 | `proposal` requires `scanned > 0`. A read of zero rows is `unknowable` with a `why`, never *"there is nothing like this"* | `C20-67` |
| 3-14 | The identity read resolves `type_name` through the successor **closure** before querying — **the chain, not one hop** — with a visited set and a hop cap, exactly as [`registry.py`](../../ontoloche/registry.py)'s `_identity_closure` does; each hop is reported as `instance_type_succeeded:<successor>`. **The shipped callers this rule binds are `_identity_closure` and `neighbors` (R38), named here per standing rule (d)'s second clause** | `C20-68` |
| 3-15 | A successor no entry declares stops the walk with `complete=False` **and a `why`**; the predecessor's entry is **never** kept as a fallback — querying one type while holding another's governed facts is the eighth trip's shape | `C20-76` |
| 3-16 | The walk carries a **hop cap**, and reaching it is `complete=False` with a `why`, never a silent answer | `C20-77` |
| 3-17 | A **cycle** in the successor chain is `complete=False` with a `why`. §5.9 does not forbid constructing one, so the walk survives it | `C20-78` |
| 3-18 | Where the closure moved and the successor's entry declares a **different `MatchPolicy` or a different predicate**, the resolution is `unknowable` with a `why` naming the changed fact — **`I-7`, and §5.3 is where the decision behind it is recorded.** The set is right here; what is wrong is whose rules judged it | `C20-79` |
| 3-20 | **The closure walks BACKWARD as well as forward**: every name retired *toward* this one is a member of the identity. `registry.py`'s `_identity_closure` calls this *"the direction `merge_types` actually produces and the one a caller reaches after doing the right thing"*, and `I-8` is what happened when this document cited that function and took the forward relation alone — the SURVIVOR of a retirement read a strict subset of the identity | `C20-86` |
| 3-21 | **Aliases are members of the closure**, because `merge_types` writes both a successor and an alias for one absorption and a hand-written alias is one the successor scan would miss | `C20-87` |
| 3-22 | A successor **name** carrying `':'` or `'#'` stops the walk with `complete=False` and a `why`. The name reaches the flat form by the **write** door — `effective_type` becomes `CandidateRef.type_name`, then `Invocation.type_name`, then the minted ref — **without ever being a record**, so rule 2-14's guard over records never sees it, and the shipped `parse_ref` reads the minted string back as a different reference (round 3, K8) | `C20-88` |
| 3-19 | **The identity's extent is the whole closure**: the read spans the declared name and every hop, because a row written under a since-retired name is still this identity's row until the host migrates it. Reading the endpoint alone is a smaller set than the extent — standing rule (e) | `C20-80` |

---

## 4. The propose-at-ingest contract — **an invocation, one new reference shape, and five amendments this row may NOT land**

**What an instance proposal IS: an invocation of a `kind="action"` family the host declared.** Most of it
already ships in [`ACTIONS.md`](ACTIONS.md):

| what a proposal needs | what already ships it |
|---|---|
| a governed declaration through propose→approve | the family is a `TypeEntry`, `ACTIONS.md` §2.1 / §5.1 |
| a gate before it runs | `preflight`, `approval_mode`, `min_auto_tier`, `ACTIONS.md` §5.2 |
| provenance with actor, tier, confidence, approver, source version | `InvocationProvenance`, `ACTIONS.md` §3.2 |
| a record of what happened | `record_invocation`, the ledger, `ACTIONS.md` §6.2 |
| a queue drained by a second person, later | `review_invocation` (**R73**), `ACTIONS.md` §6.5 |
| an enumerable backlog | `invocations(unreviewed=True)`, `ACTIONS.md` §6.3 |

> **The original section claimed this list was COMPLETE and it is not.** Round 1's integrator lens walked a
> real capture end to end and **[Observed]** it stops at the first call: *for the one case the design partner
> is actually missing — a project that does not exist yet — there is no invocation to make.* §4.3 and §4.4
> are what that finding cost, and the claim of *"adds no object"* is withdrawn in favour of a smaller true
> one: **this document adds one reference shape and no store.**

### 4.1 `CandidateRef` — the fourth reference shape, and it is this document's

`EDGES.md` §2.1 defines two; `ACTIONS.md` §2.3 takes a third; **this document takes a fourth**, for the same
reason ACTIONS gave for `EdgeRef`: the thing being named has no other honest name.

```
CandidateRef:                   # NEW, this document. A thing that does NOT exist yet
    type:       TypeRef         # kind MUST be "entity"
    label:      str             # what the landed row calls it
    resolution: str             # the outcome that produced it -- "proposal" or "ambiguous"
    act_id:     str             # the ingest act this candidate belongs to. 4.3
```

**Why it is forced. [Observed], F1:** `InputSpec(ref="instance")` is validated at both doors (ACTIONS rule
6-6), and a thing being proposed has no `InstanceRef`. Omitting the input →
`Refusal(input_kind_mismatch, {"problem":"missing"})`. Naming its type instead →
`Refusal(input_kind_mismatch, {"declared":"instance","supplied":"type"})`. **Inventing** an id →
`Preflight allowed`, which rule 1-1 forbids in terms. And declaring the input optional is worse:
`preflight` called with **nothing** returned `verdict='allowed'` — **the gate answered for a capture whose
subject it never saw.**

**A `CandidateRef` has no `id` and can never acquire one**: the host mints the identifier, and the moment it
does, the reference the ledger holds is an `InstanceRef`. That asymmetry is the seam (§1) expressed in a
type.

### 4.2 What approves it, who writes the row, and what provenance it carries

**The host writes the instance row; this project never does.** The family declares
`Effect(op="host_state", why=…)` — `ACTIONS.md` §2.5's fourth operation, the admission that *this action
changes something this protocol does not model* — and the host performs it.

**Provenance adds nothing.** `Provenance` (`INTERFACE.md` §2.4) already carries `created_by_actor`,
`model_tier` (§2.7), `approved_by` (never blank-implying-human) and `source_version` (§2.4a, **R21**);
`InvocationProvenance` narrows it and adds `confidence`. **[Observed], round 1:** the integrator lens
checked every provenance field a capture needs and found **none missing** — §4.2 is the part of this section
that held exactly as written.

### 4.3 One ingest ACT, and the two rules that make it one

**[Observed], F4 — and this is round 1's most important finding.** Two rows in one ingest act whose labels
resolve to the same thing. `resolve_instance` is called for each **before either is written** — the ordinary
shape, because the host writes on approval. **Both scans finish**, so rule 3-7 is satisfied and both
correctly answer `proposal`. Both are approved. The store now holds two rows answering to one identity, and
the *next* resolution reports it: `ambiguous known=2 confidence=1.0` over `#p-9001` and `#p-9002`.

**Every rule in §3 fired correctly and the outcome is still two things answering to one identity.** This is
not a guard that failed to look — **it is a guard that was never asked.** The state is created *between* two
correct answers, and nothing made the second call aware of the first. **[Observed]** the string `idempot`
occurred **zero** times in the original document and `within the batch` **zero** times.

**And the same shape reaches across acts. [Observed], K4:** between a proposal and the host's write the
state the resolution read is unchanged, so the permission can be cashed again — three passes produced three
unreviewed invocations for one label with `warnings=[[], [], []]`, and **the concurrent variant needs no
repeat call at all**: two workers read the same state, both answer `proposal`, both hosts write. That is
**standing rule (c) one surface down**: *a pending ingest proposal is an unconsumed permission to mint an
instance identity, and no door asked who already holds one for this word.*

**So an ingest ACT is a first-class scope, and two rules bind it:**

*(This prose was the **pre-fix** text until round 3's **B2/E8** — the rule table said one thing and the
section the rules live in said another, which is §3.4's own recorded meta-shape recurring inside the commit
that fixed it. An implementer reads this section, not the id table.)*

1. **Within one act, an IDENTITY is resolved once.** The first answer for an identity — `existing`,
   `proposal` or `ambiguous` alike — is remembered under the key
   `(namespace, kind, the closure of type_name, the label)`, and every later reference to **the same
   identity** in that act reuses it rather than resolving again. *Identity* is the gate's own question:
   `similar(norm(a), norm(b)) >= match_at`, **the relation, not its pre-processor** (finding **B1**). Rules
   4-10 and 4-13.
2. **Across acts, the propose door asks who already holds a proposal WHOSE ROW HAS NOT BEEN WRITTEN.** Not an
   *unreviewed* one: draining a proposal is the right thing to do and used to stand the guard down at exactly
   the moment the permission was live and unconsumed (`I-5`). The key is rule 4-10's, so the question follows
   the closure and the gate's relation. If one exists, the second proposal carries
   `instance_proposal_pending:<invocation_id>` and mints no second identity. Rule 4-11, and §4.4's amendments
   **A4** and **A2** are what `ACTIONS.md` must land before the question can be asked of the shipped ledger.

**Reconciling a proposal made while a candidate was `ambiguous`.** The invocation is recorded with
`instance_ambiguous_at_proposal:<input_name>:<n>` — **[Observed], F7:** the original grammar carried only
`<n>`, so a capture with a 3-way and a 2-way tie recorded `['…:3','…:2']`, two integers with no input name
and no refs — and it is recorded in `approval_mode="review"` whatever the family's default. Then
`invocations(unreviewed=True)` enumerates exactly the proposals made over an unresolved identity, and
`review_invocation` (**R73**) is its only drain.

> **`<n>` is counted over a FINISHED read or it is not counted.** **[Observed], K9:** under the old §3.4 a
> capped scan reported `ambiguous known=3` where the true multiplicity was **12**, so a reviewer draining the
> queue saw `:3` for a twelve-way collision. Rule 3-6 closes it — an unfinished read is `unknowable` and
> mints no proposal — and it is named here so the fix cannot be scoped narrowly and lose it.

> **What §4.3 says about self-review, corrected.** The original said *"the actor who ingested the row cannot
> clear their own ambiguity."* **[Observed], F11:** `review_invocation(reviewed_by='ai:capture')` — the same
> actor — succeeds. `ACTIONS.md` §6.5 / R73 argued only that a `reviewed_by=` *parameter on the write call*
> would permit self-review; it never claimed actor distinctness is enforced anywhere. **The true sentence is
> that the review is a separate act, separately recorded, by whoever performs it** — and whether the registry
> should refuse a self-review is **Q89**, not this document's to take.

### 4.4 The FIVE amendments this document ASKS OF `ACTIONS.md`, and may not make

*(Three at round 1. Round 2 added two, and both were found by a lens rather than by the author — **A4** by
the beacon integrator constructing rule 4-11's own question against the shipped door, **A5** by
[R86](../decisions/2026-09-04-7a-supervisor-ruling-R86.md) verifying that rule 5-7 had no carrier at either
end.)*

R3's rule is that a value is added in the change that introduces it; the same discipline applies to a shape.
**[Observed], round 1**, three of `ACTIONS.md`'s shipped surfaces cannot express what §4 requires, and this
row ships no code, so all three are **named here and landed by the build row**:

| # | what is missing | the evidence | why this row may not land it |
|---|---|---|---|
| **A1** | `InputSpec.ref` has no value for a thing that does not exist yet | F1's four refusals above | `InputSpec` is a printed, drift-checked shape backed by `ontoloche/actions.py`; amending the prose without the code fails [`check_spec_drift.py`](../tools/check_spec_drift.py), and amending the code is product code |
| **A2** | **`Invocation` has no field that carries a RESULT**, so rule 4-3's *"the `InstanceRef` the host minted is recorded on the invocation"* has no carrier. **[Observed], F2:** route A (the ref in the `host_state` effect's `why`, which is its identity per ACTIONS 2.5-9) makes a **correct** capture warn `effect_undeclared:host_state:created …` — *"a detector that fires on a correct run is not a detector"*, ACTIONS' own sentence, reproduced one document along. Route B (an optional `InputSpec` used as an output slot) works and is one container meaning two things | same | same |
| **A3** | `record_invocation` takes neither `approval_mode` nor `warnings`, so rule 4-5 cannot put **one** invocation into `review`. **[Observed], F3:** `declared_policy` is copied from the family and the only shipped route to `review` is a governance act that moves **every subsequent row** there | same | same |

| **A4** | **`invocations` cannot be asked rule 4-11's question, and it is NOT for want of a completeness answer.** *(Round 3's **B4** corrected this row on the record: `InvocationReport` **does** carry `known` / `complete` / `why_incomplete`, and [`registry.py`](../../ontoloche/registry.py) sets `complete=False` for **any** filter — so rule 4-11's filtered read is always incomplete, and the first draft of this amendment would have made every propose-at-ingest `unknowable` and recorded nothing, ever.)* What is missing is a **completable** read of the right question: `invocations` has no `label`, `type_name` or `kind` filter, so rule 4-11 cannot ask its own question. **[Observed], B2:** the shipped signature is `(*, family, namespace, actor, outcome, gate_verdict, effect_undeclared, unreviewed, since, limit=100)`; `ACTIONS.md` §6.3 says *"It does not page"*; and [`_sql.py`](../../ontoloche/backends/_sql.py) orders by `created_at` and returns the **oldest** page — so on an ordinary 250-row batch the repeat carries **no** warning and **two** identities are minted. **Three things the amendment must therefore ask for, named because round 3's E16 found the first draft named none of them:** (i) the predicate is *unwritten*, which depends on amendment **A2**'s `results` slot existing; (ii) the key is rule 4-10's — `(namespace, kind, **the closure of** type_name, the label under the gate's own relation)` — and **a filter over the raw stored columns can match neither the closure nor the relation**, so the amendment is for a *scoped, completable* read rather than a column filter; (iii) a client-side scan is not the fallback, because `ACTIONS.md` §6.3 says `invocations` does not page and returns the oldest 100 | same | same |
| **A5** | **The ledger cannot record WHICH policy governed.** Rule 5-7 says the policy in force is recorded on the invocation; **[Observed]** the shipped `Invocation.declared_policy` carries `approval_mode`, `min_auto_tier` and `reversibility` — **not** `match_at` / `propose_below` / `ambiguity_margin`. Rule 5-11 gives the **resolution** a carrier (`governed_by`); the **invocation** still has none, so a reviewer draining §4.3's queue cannot tell which entry's thresholds produced the row in front of them. This is `I-7`'s half that `INGEST.md` cannot close alone | same | same |

**Until all five land, §4 is a specification of a contract that cannot yet be executed**, and saying so is
the point: `ACTIONS.md` §14's *"a build row finds what a reading round cannot, by trying to write the test"*
arriving one row earlier, because a reading round **did** find it — by trying to write the walk-through.

**Rules of §4**

| # | rule | id |
|---|---|---|
| 4-1 | A propose-at-ingest act is an invocation of a `kind="action"` family; this document adds no object with a store and no primitive for it | `C20-27` |
| 4-2 | The host writes the instance row. The family declares `Effect(op="host_state")` with its mandatory `why`, and this project performs no write | `C20-28` |
| 4-3 | The `InstanceRef` the host minted is recorded on the invocation, in the `results` slot amendment **A2** adds — never in an effect's `why` and never in `inputs`. **The type it is written under is the EFFECTIVE one the resolution reports, never the declared one**, and rule 3-19 is what makes an older row still readable after a later retire | `C20-29` |
| 4-4 | Provenance is `InvocationProvenance` unchanged: actor, tier, confidence, approver, `source_version`. No field is added | `C20-30` |
| 4-5 | A proposal made over an `ambiguous` resolution carries `instance_ambiguous_at_proposal:<input_name>:<n>` and is recorded in `review` mode whatever the family declared | `C20-31` |
| 4-6 | Those proposals are enumerable by `invocations(unreviewed=True)` and drained only by `review_invocation` | `C20-32` |
| 4-7 | A resolution of `unknowable` **or of `not_an_instance`** yields **no** proposal. Both are outcomes that mint nothing, and the second is not a classifier that missed — it is the classifier **succeeding** and saying *this is not a thing*, so proposing over it in `auto` mode is how a column header becomes a host row | `C20-33` |
| 4-8 | An ingest family may not declare `Effect(op="propose_type", kind="predicate")` — `ACTIONS.md` §2.5's allowlist, restated because ingestion is the highest-volume caller that could reach it | `C20-34` |
| 4-9 | A thing being proposed is named by a `CandidateRef`, which has no `id` and never acquires one | `C20-69` |
| 4-10 | **Within one ingest act an IDENTITY is resolved once**, and the key is `(namespace, kind, the closure of type_name, the label under §3's own normaliser)` — **the key the gate decides on, computed by the same function**. Keying on the raw label proposes twice for a thing the gate itself calls `existing` at 1.0 (`I-4`); keying without the type hands a second type's landing the first's `CandidateRef` (finding B1) | `C20-70` |
| 4-11 | **Before recording a propose invocation the loop asks who already holds a proposal for this identity WHOSE ROW HAS NOT BEEN WRITTEN** — not who holds an *unreviewed* one. Draining a proposal is the right thing to do and it used to stand the guard down at exactly the moment the permission was live and unconsumed (`I-5`, standing rule (c)). The key is rule 4-10's. A second carries `instance_proposal_pending:<invocation_id>` and mints no second identity | `C20-71` |
| 4-12 | `<n>` in `instance_ambiguous_at_proposal` is counted over a finished read; rule 3-6 makes an unfinished one unable to reach this door at all | `C20-72` |
| 4-13 | The per-act memory of rule 4-10 is written on **every** branch that answers with a `CandidateRef` — the pending branch as well as the minting one. Writing it only where an identity is minted leaves the act unbound in exactly the case rule 4-11 just refused (finding B5) | `C20-81` |

---

## 5. The match-vs-propose confidence gate — **a governed fact on the entry, and it answers in §3's vocabulary**

```
MatchPolicy:                     # declared on the kind="entity" entry
    match_at:         float      # at or above: a candidate is match-grade
    propose_below:    float      # strictly below: not a candidate at all
    ambiguity_margin: float      # candidates within this of the top are TIED. 3.2
    why:              str        # REQUIRED, non-empty
```

**The gate answers in §3's five outcomes and mints no vocabulary of its own.** *(Round 1, K3. The original
gave it three verdicts of its own —* `match` / `propose` / `review` *— and* **[Observed]** `review` *was not
one of the five that rule 3-1 closes, had no `InstanceResolution` to ride, and no drain. The two artefacts
this document cited then answered one landed row two ways:* `MatchPolicy.verdict → 'review'` *and*
`resolve_instance → 'proposal'` *on* `'WILLOWBROOKE CT SKILLED CARE CENTER AT MEASE LI'` *@ 0.9691 — and
with nothing forbidding a re-ingest, pass 1 proposed, the host minted a row, and pass 2 answered `existing`
at 1.0 against the duplicate it had just created.)*

| the score says | the outcome |
|---|---|
| exactly one candidate at or above `match_at`, nothing else tied | **`existing`** |
| more than one candidate in the tied set (§3.2) | **`ambiguous`** |
| a top candidate at or above `propose_below` but below `match_at` | **`ambiguous`** — *not confident enough to be the same thing, and a human decides* |
| nothing at or above `propose_below` | **`proposal`** |
| nothing scored, or the read did not finish | **`unknowable`** |

**One outcome, two reasons, and the `reason` string says which** — `endpoint_kind_mismatch`'s recorded
economy (`EDGES.md` §7 / `INTERFACE.md` §5.12): *a closed vocabulary that grows a value per variant of one
failure is not closed for long.* Both reasons mean the same thing to a caller — **a human must decide, and
nothing may be minted meanwhile** — and rule 4-5 routes both to the same queue.

### 5.1 Why the threshold is declared and not passed — **the failure, constructed**

**[Observed], design test 4:** the identical batch, under two ENTRIES declaring different thresholds
— which is exactly what a per-*call* threshold would let two callers do —
resolves **differently on 31 of 100 rows**:

```
'7502 18 AVENUE'   @ 1.0: caller A -> ambiguous, caller B -> existing
'8004 20 AVENUE'   @ 1.0: caller A -> ambiguous, caller B -> existing
'1767 BATH AVENUE' @ 1.0: caller A -> ambiguous, caller B -> existing
```

Each caller is internally consistent. The store ends up holding duplicates **whose cause is which caller
landed the row** — a fact the curation loop cannot see, cannot enumerate and cannot fix, because nothing
recorded it. So the threshold rides the proposal→approval loop like every other governed fact.

**`why` is required and non-empty**, on `ACTIONS.md` §2.4-3's reasoning exactly: an undescribed threshold is
one nobody will ever be able to raise.

### 5.2 *"I already know 38 of these"* — the number, and what the fixture does to it

`ROADMAP.md` homes instance resolution in Phase 3 with the walkthrough's *"I already know 38 of these"*.
**[Observed], design test 4**, 100 live NYC 311 rows — 38 already held exactly, 24 held but landing in an
abbreviated spelling, 38 genuinely new:

```
match_at=0.97  propose_below=0.80
   known: {'existing': 38}     banded: {'ambiguous': 23, 'existing': 1}     novel: {'proposal': 38}
```

**And the fixture's own hand is on that number, which round 1 measured and this section now prints.**
**[Observed], M3:** the probe builds its host with one instance per **address**, while the instance in
`erm2-nwe9` is a service request keyed by `unique_key`; **46%** of the fetched rows share an address and the
probe discards **32%** of them. **Un-deduped — the host's actual rows — the same batch gives
`{'ambiguous': 13, 'existing': 25}`.**

**Both numbers are true of different hosts, and the second is the more honest headline.** *A host that holds
one instance per label answers 38 of 38; a host that holds its real rows answers 25 and correctly refuses to
guess on 13.* The second is `resolve_instance` working — 13 genuine multiplicities caught rather than
collapsed — and it is the number a reader should carry, because **[Observed]** 59.7% of `uvpi-gqnh`'s
683,788 instances share an address with another (see ING5). *A headline number that is an artefact of a
fixture line is exactly what §5.1's own argument is about, and it was one.*

**Rules of §5**

| # | rule | id |
|---|---|---|
| 5-1 | `MatchPolicy` is declared on the entry and rides propose→approve; `resolve_instance` takes no threshold argument | `C20-35` |
| 5-2 | `propose_below <= match_at`, refused at declaration otherwise | `C20-36` |
| 5-3 | `MatchPolicy.why` is required and non-empty | `C20-37` |
| 5-4 | The gate answers in §3's five outcomes and mints no verdict vocabulary of its own | `C20-38` |
| 5-5 | An unscored candidate, and a candidate off an unfinished read, are `unknowable` at the gate as at the call | `C20-39` |
| 5-6 | Two entries in one namespace may declare different policies; two **callers** may not | `C20-40` |
| 5-7 | The policy in force is recorded on the invocation, as `ACTIONS.md` rule 3-8 records the policy the gate judged. **[Observed]** this rule had **no carrier** until rule 5-11: the printed `InstanceResolution` contained no `policy` and the shipped `Invocation.declared_policy` holds `approval_mode` / `min_auto_tier` / `reversibility`, not the three thresholds | `C20-41` |
| 5-12 | The tied set carries a **floor**: a candidate below `propose_below` is not a tie but a candidate the entry has declared too weak to be anything, and admitting it turns *"nothing here is close enough"* into `ambiguous`. **[Observed], round 3's K7:** removing the floor reddens a check on the real 14,627-row file, so it is load-bearing on real data — and it lived in the code and not in this document until round 3 | `C20-90` |
| 5-10 | **A successor does NOT inherit its predecessor's `MatchPolicy`.** Where a closure hop crosses into an entry declaring a different one, the resolution is `unknowable` (rule 3-18) rather than answered under rules the caller never named. §5.3 records the decision and why the other reading was refused | `C20-82` |
| 5-11 | `InstanceResolution.governed_by` names the `(namespace, type_name)` whose entry supplied the `MatchPolicy` and the predicate this answer was judged by. **It is rule 5-7's carrier**, and an answer that cannot say which policy governed it makes rule 5-7 unfalsifiable | `C20-85` |
| 5-8 | **`existing` requires exactly one member in the tied set of §3.2** — every candidate at or above `match_at` plus every candidate within `ambiguity_margin` of the top | `C20-73` |
| 5-9 | A top candidate between `propose_below` and `match_at` is `ambiguous`, never `existing` and never `proposal` | `C20-74` |

---

### 5.3 A successor does NOT inherit the `MatchPolicy` — **the decision, and why the other reading was refused**

**[Observed]** this section was cited **eight times** in this file — by §3.4, by rules 3-18 and 5-10, by §6.3a
— and did not exist until round 3 found it (finding **E5**). Four normative rules pointed a build row at an
empty heading. It is written now, and what it records is a decision this row **took**, not one it routed.

**The decision: no inheritance.** Where the identity closure crosses into an entry declaring a different
`MatchPolicy`, the resolution is `unknowable` (rule 3-18) rather than answered under thresholds the caller
never named. Rules **5-10** and **6-18** state it; rule **7-5** puts the matching obligation on the host.

**Why the other reading was refused.** §7.2 makes the entity vocabulary **the host's to register**, and a
successor's entry may be declared by a different party from the predecessor's. Inheriting its governed facts
would therefore let a third party's declaration silently govern a caller's answer — and **[Observed], D3**,
that is not theoretical: after one `retire(successor='ltc_facility')` over design test 3's CA+CO fixture a
California caller sees `CO rows visible to this CALIFORNIA caller: 1` where the control saw `0` (**R59's own
stated reversal condition**, reached by a governance act rather than a missing keyword), and **73 of 1,373**
real CMS labels resolve differently for one caller. §5.1's rule 5-6 — *two entries may declare different
policies; two **callers** may not* — is otherwise defeated **inside one caller**.

**What "a different `MatchPolicy`" means, decided here because round 3 found it undecided (finding E10).**
It means the **three thresholds** — `match_at`, `propose_below`, `ambiguity_margin` — and **not** the object.
`MatchPolicy.why` is required and non-empty (rule 5-3) and §7.1a makes the successor's entry someone else's to
**word**, so comparing objects would stop a live ingest loop permanently over a **reworded rationale on
identical numbers**. That is a cost Q91's table does not price and nobody would choose. The same reading
applies to the predicate under rule 6-18: the terms, not the prose.

**And the comparison is per MEMBER of the closure, not between its endpoints** (finding **K1**). Round 2
compared the declared entry with the endpoint's, so **one extra `retire()`** to an endpoint declaring exactly
what the caller declared silenced the guard — while rule 3-19 admits the intermediate's rows into the extent,
making *the entry whose rows are being judged the one entry never consulted*.

**This is Q91, and Q91 is the founder's**, because it changes what the registry declines to serve — Q56's own
property. The default in force is stated above; §11 carries the three readings and the cost of each.

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
operator is a query language, which is the door `ACTIONS.md` §2.4 exists to keep shut. **[Observed], round
1:** a reviewer tried to construct a real CMS or NYC host predicate needing either and could not — *"every
case I built reduced to `ne`/`not_in` or to the attribute-to-attribute gap, which is a different missing
thing."* That gap is contortion **ING10**.

### 6.1 Three-valued, and both two-valued readings are constructed failures

**[Observed], design test 3**, over **1,373** CMS facilities from two states in **one store** — California
and Colorado, the pair sharing the most provider names (**five**, of 84 names that span more than one state):

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
  governed — and **[Observed], P3:** it may not also be a call parameter, because a caller who omits the
  keyword gets a different answer and a cross-tenant candidate. §3's signature no longer has one;
- the **registry** evaluates it over the candidates primitive 23 returned — **and over the record primitive
  22 returns** (rule 2-15), because **[Observed], M7:** `get_instance` originally had no tenancy surface at
  all and a California caller could confirm a Colorado row by key;
- the **host** may also narrow inside its adapter through `host_filter`, which is an optimisation and never
  the guarantee. **[Observed], design test 3:** the primitive's signature carries **no tenant parameter**,
  each host `considered=1373` of 1,373 rows, and the predicate did every exclusion. *The separation is not
  that the host hid rows; it is that the exclusion happened where it can be counted.*

### 6.3a A successor does not inherit the predicate either — **rule 6-18**

The same decision as §5.3 and for the same reason, stated separately because a predicate is a *tenancy*
fact and getting it wrong is **R59's own stated reversal condition** rather than a quality regression.
**[Observed], D3:** after one `retire(successor='ltc_facility')` over design test 3's CA+CO fixture, a
California caller sees `CO rows visible to this CALIFORNIA caller: 1` where the control saw `0`.

### 6.4 The one change R60 requires, and it lands with this document

R60 says the four surfaces are amended **in one change**. This document is that change: `INGEST.md` §6 is the
language, and the three sibling sections gain a pointer to it in the same commit —
[`INTERFACE.md`](INTERFACE.md) §10b.4 (contortion 11), [`EDGES.md`](EDGES.md) §4.3 (**R22**), and
[`ACTIONS.md`](ACTIONS.md) §2.4 (**ACT4**, rule 2.4-9). **The pointers change no printed shape or signature
in those documents**, because nothing here is built yet: each says where its missing mechanism now lives and
what still has to happen before it can be used.

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
| 6-14 | The condition is declared on the entry and rides propose→approve. **It is never a call parameter** | `C20-55` |
| 6-15 | The registry evaluates it, over every record either primitive returns; a host-side `host_filter` is an optimisation and never the guarantee | `C20-56` |
| 6-16 | A candidate the predicate could not decide makes the resolution `unknowable` (§3.4) and is never silently dropped | `C20-57` |
| 6-18 | **A successor does not inherit its predecessor's predicate.** A closure hop into an entry declaring a different one is `unknowable` (rule 3-18), because a tenancy predicate the caller never named deciding a caller's answer is R59's reversal condition reached through a governance act | `C20-83` |
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
`known=0, complete=false` — which is honest and is not the same as safe. **The resolution says so**: it
carries `consumers_unregistered` in its `warnings` (§8), because **[Observed], F8:** the original rules 7-1
and 7-4 named the resolution as their carrier and `InstanceResolution` had no field for either.

### 7.1a The host that declares a successor declares its governed facts — **rule 7-5**

§7.2 makes the entity vocabulary the host's to register, and **that is exactly why there is no
inheritance**: a successor's entry may be declared by a different party from the predecessor's, so
inheriting its `MatchPolicy` or predicate would let a third party's declaration silently govern a caller's
answer. The obligation is therefore on the host: **declare the successor's governed facts, or accept that
resolutions across that hop answer `unknowable`.**

### 7.2 The entity vocabulary is the host's to register

`propose_type` / `approve` are shipped. A host that wants `task`, `project`, `person`, `org`, `meeting`,
`briefing`, `decision` as `kind="entity"` rows registers them itself. **This is not a build row for anybody**
— it is separated out here so nobody waits on this project for it.

### 7.3 The tenancy predicate is the host's

R59, unchanged. The host declares it as a `Condition` (§6) on the entry, and it becomes enumerable and
governed by declaring it. A host that does not declare one is running the loop with no tenancy filter — which
is correct for a single-tenant deployment and is a defect in any other, and **this document cannot tell which
a deployment is**, so the resolution carries `no_tenancy_predicate` rather than implying a filter.

**Rules of §7**

| # | rule | id |
|---|---|---|
| 7-1 | Ingest curation reports its blast radius from `consumers()`, and reports it as incomplete, never as safe — carried in `InstanceResolution.warnings` as `consumers_unregistered` | `C20-59` |
| 7-2 | This document specifies no consumer-registration mechanism; it states the obligation | `C20-60` |
| 7-3 | The entity vocabulary is registered by the host through the shipped calls; this document adds no path for it | `C20-61` |
| 7-5 | A host declaring a `successor` on an entry declares the successor entry's `MatchPolicy` and predicate too, or resolutions crossing that hop answer `unknowable` (rules 3-18, 5-10, 6-18). §7.2 makes the entry someone else's to register, which is the reason the facts are not inherited | `C20-84` |
| 7-4 | A namespace with no declared tenancy predicate runs unfiltered and the resolution carries `no_tenancy_predicate` | `C20-62` |

---

## 8. Printed shapes — and what has and has NOT been executed

[`../tools/check_spec_drift.py`](../tools/check_spec_drift.py) compares a spec's printed shapes and
signatures against the dataclasses and methods that exist. **Nothing in this document exists**, so pointing
the checker here would fail on every line. This is `ACTIONS.md` §14's position exactly: **the build row adds
`INGEST.md` to the checker in the same change that lands the shapes.**

```
InstanceContext:                    # the ResolveContext analogue, and it is NOT that object
    label_source:   str | None      # "erm2-nwe9#incident_address" -- WHICH SURFACE the
                                    #   string was read from. INTERFACE 10b.6's finding B
    row_attributes: dict            # the landed row's other columns, opaque
    siblings:       tuple[tuple[str, str], ...]   # (type_name, label) of the other candidates
                                    #   in the same ingest act. TYPED -- see below
    act_id:         str             # the ingest act. 4.3's scope
    proposed_by:    str | None

InstanceResolution:
    outcome:        str             # the five of 3.1
    ref:            InstanceRef | None      # when "existing"
    candidate:      CandidateRef | None     # when "proposal" or "ambiguous". 4.1
    confidence:     float | None    # None means "did not score", NOT zero
    reason:         str
    candidates:     tuple[InstanceCandidate, ...]   # the tied set on "ambiguous"
    known:          int             # len(candidates). Rule K
    complete:       bool            # Rule K -- about the candidate SET
    why_incomplete: str             # "" when complete
    scanned:        int             # how many host records the identity read consumed
    warnings:       tuple[str, ...] # 7-1, 7-4, 2-13, 3-14
    tier:           str             # echoed back; goes into provenance
    governed_by:    str             # rule 5-11 -- "<namespace>:<type_name>" of the
                                    #   entry whose MatchPolicy and predicate judged
                                    #   this answer. `I-7`'s carrier, and rule 5-7's:
                                    #   an answer that cannot say which policy
                                    #   governed it makes rule 5-7 unfalsifiable

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
less signal than it was built for; this document declines to make that a second time.

**`siblings` is TYPED, and round 1 is why.** **[Observed], F6:** the original field was
`sibling_labels: list[str]`, and a capture resolving a task was handed a project name and a person name with
nothing to tell them apart. `ResolveContext.sibling_columns` carries signal because they are columns of *one
row*; these are not. The pair carries what the flat list could not.

**`label_source` exists because of a finding this project already recorded and could not act on.**
`INTERFACE.md` §10b.6 finding **B**, **[Observed]**: NYC's catalogue and its SODA API disagree on field names
for all three sampled datasets — `borough` versus `boroname`, `latitude` versus `lat` — so *the candidate a
proposer brings depends on which surface it read*, and §10b.6 says in terms that **Phase 3's ingestion layer
must record which surface a column name came from.** This is that field. It is a fact about *us* and so does
not belong in `Provenance.source_version`, which R21 reserves for a fact about the **source**.

### 8.1 What is specified and NOT yet exercised — **stated, because round 1 counted it**

**[Observed], F9 and §6.2c:** at the end of round 1, nine printed things had never been run by any design
test — `InstanceContext` and all its fields (the call's second **positional** argument), both capability
flags, `InstanceRecord.source_version`, `NotSupported`, and `get_instance` itself — and the probes contained
**eleven countable absences**, five of them a previous kill-row trip's count verbatim. The amended probes
close the ones that produced findings; **this subsection is where the remainder is named rather than
implied**, so the build row knows exactly what has a specification and no evidence behind it:

| still unexercised | why it is left | what would exercise it |
|---|---|---|
| `InstanceRecord.source_version` | no fixture carries two versions of one host row | a CMS re-export beside the current one |
| `NotSupported` at primitive 22 | needs an adapter that declares `resolves_instances=False`, which is a build-row object | the contract suite's `sqlite_minimal` leg |
| `instance_filters` with a key the host declines | needs a real adapter to decline one | `C20-10` in the build row |

**Nothing else in §2, §3, §4, §5 or §6 is unexercised after the amendments** — and §5 of this document's run
record carries the count.

---

## 9. Rule → planned id mapping *(standing constraint 8)*

**Ninety rules, ninety planned ids, `C20-01` … `C20-90`**, listed in each section's own table.
**[Observed]** the count is `grep -cE '^\| [0-9]+-[0-9]+ \|'` over this file — **the rule ROWS**, which is
the number the sentence is about. The obvious command over ids (`grep -o "C20-[0-9]*" | sort -u | wc -l`)
returns one **more**, because it matches the bare `C20-` inside this very paragraph; that is finding **E7**,
and it is recorded rather than papered over, because a verification command that cannot be quoted inside the
document it verifies is a trap for the next reader.

**This sentence has now been wrong twice.** Round 2's **A3** found it saying *seventy-six* over 74; round 3's
**B9/E7** found it saying *eighty-one* over 85, **in a sentence that claimed the count had been derived** —
the four `I-7` rules were added after the sentence was rewritten and it was never re-run. *In the section
whose only job is to enumerate.*
The prefix is `C20` because `C19` is `ACTIONS.md`'s and is full. **The ids are *planned*:** this row ships no
implementation, so no id is claimed, and the build row claims them in the change that makes each rule
testable — standing constraint 8's rule applied to a spec that precedes its build by design (R60).

**Seven vocabulary values are RESERVED here and deliberately NOT minted**, on ruling **R11**'s precedent — *a
value is added in the change that introduces it, and nothing introduces it yet*:

| value | carrier | note |
|---|---|---|
| `instance_source_absent` | `Refusal.reason`, the **thirty-second** | The **sixth capability refusal**, after `proposals_not_stored`, `cannot_record_override`, `consumer_source_read_only`, `edge_store_absent` and `action_store_absent`, and it exists for the reason the first of those does: an empty candidate page would read as *"there is nothing like this"* |
| `instance_ambiguous_at_proposal:<input_name>:<n>` | `warnings`, the **thirty-fifth** | §4.3's mechanical handle. The `<input_name>` segment was added by round 1's F7 |
| `instance_proposal_pending:<invocation_id>` | `warnings`, the **thirty-sixth** | §4.3 rule 4-11's handle — the pending-proposal question K4 forced |
| `instance_narrowed_proposal:<keys>` | `warnings`, the **thirty-seventh** | §2.1 rule 2-13's handle — M2's cheap `complete=True` made visible |
| `instance_type_succeeded:<successor>` | `warnings`, the **thirty-eighth** | §3.4a rule 3-14's handle — K6's retired-type case, and one is emitted per HOP of the closure |
| `consumers_unregistered` | `warnings`, the **thirty-ninth** | §7 rule 7-1's handle. **[Observed]** `'consumers_unregistered' in types.WARNING_VALUES` is `False` and the kit emits it on every call — round 2's finding A3, and it is standing rule (d) failing inside the section whose only job is to enumerate: round 1's F8 fix minted the value and the commit that minted it did not name §9 |
| `no_tenancy_predicate` | `warnings`, the **fortieth** | §7 rule 7-4's handle, minted by the same F8 fix and reserved nowhere until now (A3) |

**[Observed] 2026-09-04**, `len(types.WARNING_VALUES)` is **37**, so the four warnings reserved here are the thirty-eighth, thirty-ninth and fortieth *after* the three already reserved above take thirty-five, thirty-six and thirty-seven — **the reservation is written with its ordinals so the count stays reconcilable with the tuple that holds it**, which is the whole of R11's mechanism and the thing round 2's A3 found deleted.

**A malformed `Condition` mints nothing**: it is refused with **`attributes_schema_violation`**, which
`ACTIONS.md` rule 2.4-6 already uses for a malformed `Precondition` declaration. **Minting a value for the
identical failure one object along is Cause B in the direction nobody guards** — a closed vocabulary grows by
one value per *fact*, not per *object*.

**Why reservation and not amendment.** `check_spec_drift.py` holds `INTERFACE.md` §5.12's list and count
against `types.REFUSAL_REASONS`, and §5.4's table against `types.WARNING_VALUES`. Amending the prose without
the tuple fails the checker; amending the tuple is product code, which this row does not ship. **Q85** asks
the supervisor to rule it, because EDGES v0 and ACTIONS v0 both chose the other way.

**Five shape amendments to `ACTIONS.md` are likewise named and not made** — §4.4's A1–A5 — for the
same reason and with the same routing.

---

## 10. Contortions, recorded and **not** designed away

| # | contortion |
|---|---|
| **ING1** | **The ledger cannot tell an instance write from any other host-state change, except by prose.** §4 maps the write to `Effect(op="host_state")`, whose identity **is** its `why` (`ACTIONS.md` §2.5), so two ingest families with differently-worded admissions are two effects. Adding a `propose_instance` op was considered and refused: this project performs no such write. **Round 1 sharpened the cost: [Observed]** putting the minted ref into that `why` makes a **correct** capture warn `effect_undeclared`, which is why §4.4's amendment **A2** asks for a `results` slot instead |
| **ING2** | **Nothing enforces that a caller does not propose over an `unknowable` resolution.** Rule 4-7 is a rule of this document; the registry does not execute (`ACTIONS.md` §4) and `record_invocation` records what already occurred. So the loop's most important rule is **advisory at the only door that could enforce it.** Inherited, not introduced — and worse here, because ingestion is the highest-volume caller in the system |
| **ING3** | **`resolve_instance` cannot use `resolve_type`'s resolver, so the project now has two notions of *the same string*.** `_resolve.py`'s `identity_key` / `same_word` are one function *because the kill row's seventh trip is what happens when there are two*. **[Observed], K10:** the risk is already realised in this row's own probe — `'状态'` and `'!!!'` answer `not_an_instance` with `scanned=0`, because the probe's normaliser is `identity_key`'s ASCII-only collapse re-implemented, so a real Chinese-language facility name is refused as a class word. **That is `C4-14`'s defect in its other direction.** A probe defect and not a spec defect — §3.3 declines to define the classifier — and it is measured evidence for **Q86** rather than a theoretical risk |
| **ING4** | **A `host_filter` narrows in the host, so this project cannot tell a narrowing from a tenancy filter.** Rule 2-12 makes the **keys** declarable, which is what `instance_filters` needs to govern them, and the **values** stay opaque. A host that puts tenancy in a filter value still gets the right answer and an unenumerable gate; rule 6-15's registry-side evaluation is what makes the outcome safe, and it does not make the host's intent visible |
| **ING5** | **`InstanceRecord.label` assumes a host has one, and round 1 measured what that costs.** **[Observed]** on `uvpi-gqnh` (683,788 DPR instances): `address` → 408,701 distinct values and **59.7% of instances share an address with another**, so 59.7% of landed rows resolve `ambiguous` and rule 4-5 forces every one of those proposals into `review`; `spc_common` → 132 values, which are class words → `not_an_instance`; `tree_id` → the opaque host id, which is not *"the human-facing string a landed row would carry"*. **The label choice does not merely hide a decision; on the second-largest NYC fixture it defeats the gate**, and `label_parts` is the obvious answer this row does not take on a design test's authority |
| **ING6** | **The 104 shared names are handled and the 14,498 unshared ones are not proved.** Design test 1 exercises `existing` at multiplicity 1 and `ambiguous` at multiplicity 12; **[Observed], K2** the near-miss population is real (`- WEST` / `- EAST`) and §3.2's set test is what covers it. The false-positive rate of any real resolver is a **build-row** measurement and this document claims none |
| **ING7** | **`kind` is pinned to `"entity"`, and that silently drops half of UC2.** `INTERFACE.md` §10's CMS design test registers six types, **two of them `value_set`** — `deficiency_corrected_status` (**[Observed]** exactly six values, `'Deficient, Provider has date of correction'` 408,475 … `'No revisit needed'` 277) and `scope_severity_code`. *"Which of the six statuses is this cell?"* is an instance question over a landed row and is what UC2 was chosen to test, and this protocol cannot ask it. The constraint is **inherited** from `EDGES.md` §2.1 (*an `InstanceRef`'s type MUST be `kind="entity"`*) — **but an inherited constraint that removes a fixture's stated pathology is a contortion, not a non-issue.** Round 1, M6 |
| **ING8** | **For a prose source, two of `InstanceContext`'s four fields are empty and the empty pair is the discriminating pair.** **[Observed], F6:** of the 104 shared-name ties, `row_attributes` separates **104/104** and `siblings` **0/104** — and a capture from meeting prose can fill `siblings` and cannot fill `row_attributes` or `label_source`. **[Observed], F10:** `not_an_instance` is likewise unreachable from prose — `'the team'`, `'next quarter'`, `'action items'`, `'TBD'`, `'the migration'` all resolve `proposal` — so **every extraction error from a prose source lands as a well-formed proposal.** ACT2's shape at a second surface, recorded rather than designed away, and it is the strongest argument for **Q86**'s option (c) |
| **ING9** | **Self-review is not enforced and this document previously said it was.** **[Observed], F11:** `review_invocation(reviewed_by='ai:capture')` succeeds for the actor that ingested the row. `ACTIONS.md` §6.5 / R73 argued only that a `reviewed_by=` parameter on the write call would permit it; nothing anywhere enforces actor distinctness. **Q89** carries it |
| **ING10** | **`Condition` cannot compare two attributes of one record, and the nearest expressible form is accepted at declaration and `False` for every record.** UC2's own pre-registered pathology — **[Observed] 5,338 of 416,948 rows (1.2803%)** carry a correction date before the survey date — has the gate `Correction Date >= Survey Date`. **[Observed], M5:** `Condition(op='gte', attribute='Correction Date', value='Survey Date')` is **ACCEPTED** at declaration and answers `holds=False` for valid and inverted rows alike, because every ISO date sorts below `'S'`. **That is design test 3's own mechanism-C failure, reached by a predicate that passes rules 6-1…6-13 with a non-empty `why`.** A thirteenth term (`cmp_attr`) is a §-row change and is **not** taken on a design test's authority; **Q90** routes it |
| **ING11** | **Rule 3-19's own cost: while a host is MID-MIGRATION, one facility can appear under two names of one closure and the read correctly calls it `ambiguous`.** The extent spans the declared name and every hop (that is what closes `I-3`), so between a `retire(successor=)` and the host finishing its migration, a row present under both names is **two refs** and rule 3-3's set test sees two candidates. **This is not a defect and it is not designed away**: the extent genuinely is ambiguous mid-migration, and rule 4-5 routes it to a human, which is the correct destination for *“the store is halfway through changing its mind about what this type is called”*. The alternative — collapsing two refs that differ only by a name the host is retiring — is `I-6`'s defect chosen deliberately, and this document will not take it. **MEASURED in round 3, over 400 real CMS labels against the pinned file, and for a CLEAN migration the cost is ZERO:** `CONTROL [('ambiguous',10),('existing',390)] sum(known)=426` · `MID-MIGRATION` identical · `MIGRATED` identical · **`outcome changes: 0 of 400 (0.0%)`**, no `known` inflation, no `ref_key` collision, no tenancy leak. **The cost that IS real is one this contortion did not name:** **[Observed]** `196 of 400` labels answer `existing` in both arms **with a different ref** — every ref for a row the host moves changes string — e.g. `('VIEWCREST HEALTH CENTER', 'cms:entity:facility#245414', 'cms:entity:ltc_facility#245414')`. That matters because a ref rule 4-3 recorded on an invocation before a migration reads back **absent** after it, and **primitive 22 resolves no closure** (round 3, E2). The genuinely multi-name case — one row present under both names at once — is rule 2-17's |
| **ING12** | **What §3.4a's normative citation DECLINES, named because R87 requires it named.** `_identity_closure` continues with `complete=True` where this document answers `unknowable`: on a **cycle**, and on a **dangling successor**. **[Observed]** shipped, a cycle `a→b→a` returns `members=('a','b') complete=True`; a dangling `a→z` returns `members=('a',) complete=True`. **The divergence is deliberate and the reason is the question each is answering.** `_identity_closure` answers *"which written names mean this one"* for a read that can act on a partial answer — `neighbors` returns what it found and says the walk was incomplete. This document's caller is asking *"may I mint an identity"*, and standing rule (e) makes an extent it cannot prove `unknowable` rather than a floor. **So the citation adopts all three relations and both termination guards, and declines the two continue-anyway behaviours** — recorded here rather than left as prose, per R87. The hop cap is **adopted at the shipped value of 16**; round 2 chose 8 without saying why, which round 3's E6 caught |

---

## 11. Questions for the supervisor — **Q85 onward**

*(R1–R82 exist and Q1–Q84 are spent; neither number is reused.)*

**Q85 — Does `instance_source_absent` land in this row after all?** §9 reserves five values on R11's
precedent, which keeps `check_spec_drift.py` green and the scope fence intact. The counter-argument is R3's
plain words: *a value is added in the change that introduces it*, and this change introduces the
**specification** of it. EDGES v0 and ACTIONS v0 both chose the other way. **A ruling either way is cheap now
and expensive after the build row.** The same question governs §4.4's five ACTIONS shape amendments.

**Q86 — Is a second notion of *the same string* acceptable, or does the project need one?** Contortion ING3,
and round 1 turned it from a risk into a measurement: **[Observed]** this row's own normaliser refuses
`'状态'` as a class word, which is `C4-14`'s defect in its other direction. The options are (a) accept two,
named and separated, with the boundary written down; (b) generalise the existing one; (c) **require every
instance resolver to be supplied by the deployment, as `Resolver` already is, and specify only the
outcomes.** **[Inferred]** (c) is closest to what `PACKAGE.md` §2.6 already does, and ING8's measurement —
that the discriminating fields are empty for a prose source, and 3.9% of a real NYC column is class words —
is the strongest evidence for it. **It decides whether this project ships a matcher at all.**

**Q87 — Should `resolve_instance` be permitted at all when `consumers()` returns `known=0`?** §7.1 states the
obligation and now carries `consumers_unregistered` on the resolution. The stronger reading is that the
**propose** path should refuse on a namespace with no registered consumers, because proposing blind is the
failure `consumers()` exists to prevent. That makes an unmet host obligation a hard stop, which is a policy
decision about somebody else's deployment.

**Q88 — Does the Rule of the ordering's extension to Phase 3 stand?**
[`../decisions/2026-09-02-phase3-repoint-R77-R78.md`](../decisions/2026-09-02-phase3-repoint-R77-R78.md) §6
recommends it and marks it *pending the founder's word*. **This document was written under it**, and §12
records what the partner's shape would have changed.

**Q89 — Should the registry refuse a self-review?** Contortion ING9. `review_invocation`'s whole argument
(R73) is that *a review is a second act by a second person at a later time*, and **[Observed]** nothing
enforces the second person. It is `ACTIONS.md`'s call to make, not this document's, and the ingestion loop is
the caller that makes it matter — a batch of a thousand rows with a thousand self-reviews is a drained queue
that reviewed nothing.

**Q90 — Does `Condition` gain a thirteenth term for attribute-to-attribute comparison?** Contortion ING10.
The fixture is UC2's own pre-registered 1.2803% date inversion, the workaround (enumerating 47,318 literal
pairs) is absurd and the alternative (a host-computed boolean column) is ING4 arriving through §6. **The
danger is precise: the nearest expressible form is accepted at declaration and silently false for 100% of
records**, which is the shape §6 exists to prevent. R60 says a thirteenth is a §-row change with a contract
id; it is not taken on a design test's authority.

**Q91 — When a `retire(successor=)` hop changes the governed facts, should `resolve_instance` DECLINE to
answer?** This is `I-7` ([**R86**](../decisions/2026-09-04-7a-supervisor-ruling-R86.md)), and it is raised in
**Q56's shape** because it has Q56's property: *it changes what the registry declines to serve.*

**The row's decision, and the standing default in force: no inheritance.** Rules **3-18**, **5-10**, **6-18**
and **7-5** make a closure hop into an entry declaring a different `MatchPolicy` or a different predicate
answer **`unknowable`**, with a `why` naming the changed fact. **The reasoning is this document's own §7.2:**
the successor's entry is *someone else's to register*, so inheriting its governed facts would let a third
party's declaration silently govern a caller's answer. **[Observed], D3**, that is not theoretical — after one
`retire(successor='ltc_facility')` over design test 3's CA+CO fixture a California caller sees
`CO rows visible to this CALIFORNIA caller: 1` where the control saw `0` (**R59's own stated reversal
condition**, reached by a governance act rather than a missing keyword), and **73 of 1,373 real CMS labels
resolve differently for one caller**. §5.1's rule 5-6 — *two entries may declare different policies; two
**callers** may not* — is otherwise defeated **inside one caller**.

**What the founder is being asked, and why it is not the row's.** The default buys safety with availability:
an ordinary curation act now makes a live ingest loop answer `unknowable` for every label under the retired
type until the host declares the successor's governed facts (rule 7-5). Three readings exist and this row is
not entitled to choose between the second and third:

| | reading | what it costs |
|---|---|---|
| **(a)** | **no inheritance, `unknowable`** — the row's default, **in force** | a retire stops the loop until the host acts. Safe and loud, and possibly too loud for a host that retires types routinely |
| **(b)** | inherit silently | the failure D3 constructed, in production. **This row refuses (b)** and records the refusal rather than routing it |
| **(c)** | inherit **with a warning** and keep answering | (b)'s availability with a handle on it — and it is **Q56's own shape**, where a `1.0` that should carry a warning is exactly what is open. If Q56 resolves toward warning-rather-than-refusing, (c) is what consistency requires here |

**(a) and (c) differ only in whether the registry declines or warns, which is the question Q56 asks on the
read side — so they should be answered together and by the same person.** The default in force is **(a)**.

---

## 12. The partner's shape, exercised against the public data — **conflicts recorded, not resolved**

Written under the extended Rule of the ordering (Q88). **[Inferred]**, from the supervisor's architecture
framing of 2026-09-02 — *a document that is not in this repository, and this section carries that document's
own claim tag rather than upgrading it* — five open defects in the design partner's capture path are five
surfaces of one missing substrate. *(Round 1, F12: the original section tagged these `[Observed]` from an
out-of-repo source, upgrading a claim `2026-09-02-phase3-repoint-R77-R78.md` §5 tags `[Inferred]`. The
`consumers() → known:0` fact IS sourced in-repo, at `INTERFACE.md` §9 contortion 6, and keeps its tag.)*

| the partner's defect | what this spec does | did the partner's shape change anything? |
|---|---|---|
| capture emits `create_task` and has **no `create_project` verb** | §4: an ingest proposal is an invocation of a host-declared family, and §4.1's `CandidateRef` is what makes the *proposed* case expressible | **No — and round 1 proved the point the hard way.** The shape was derived from `ACTIONS.md`'s shipped ledger and CMS's *"a facility we have never seen"*, and the integrator lens then showed the derivation was **incomplete for both**, not partner-shaped |
| **project scatter** — tasks filed into wrong existing projects, for want of a match-vs-propose gate | §5's `MatchPolicy`, answering in §3's outcomes | **No, and the public data made it sharper.** The 18-of-100 disagreement forced the threshold onto the entry; the partner's defect argues for a gate but not for *where it is declared* |
| relationships auto-applied with **no approval step and no model-identity provenance** | §4.2: `InvocationProvenance` unchanged | **No.** Inherited, not designed — and the one part of §4 round 1 could not break |
| **`consumers()` returns `known:0`** **[Observed, in-repo]** | §7.1, plus `consumers_unregistered` on the resolution; **Q87** asks whether it should be a hard stop | **No** — and this is where the public data is **silent**, because CMS and NYC have no consumers either. Recorded as a **gap in the fixtures**, not in the spec |
| the rot sensor cannot fire for want of `last_used_at` | out of scope: `record_use` / `usage` are `INTERFACE.md` §5.7's | — |

**Two conflicts are recorded and routed.**

1. **Scale.** The partner's capture resolves *"which project does this task belong to?"* over a small,
   single-tenant, in-memory candidate set. The public data forced §2.1's `host_filter` and §3's `unknowable`
   because **9,764,249** rows **[Observed 2026-09-03]** cannot be scanned per landed row. **A protocol shaped
   only around the partner's case would have neither.**
2. **Source shape, and it cuts the other way.** **[Observed], ING8:** the fields that discriminate on CMS
   (`row_attributes`, 104/104 of the ties) are exactly the fields a prose capture cannot fill, and
   `not_an_instance` is unreachable from prose entirely. **The public-data shape does not serve the partner's
   source here, and this document does not resolve it toward either** — it records both, prices the prose
   case at ING8, and routes the underlying decision to **Q86**. *The rule says the public-data need wins and
   the conflict is recorded; it does not say the partner's need is refused silently, which would be the same
   failure pointing the other way.*

---

## 13. Kill-criterion check — required, and it was NOT sufficient the first time

`ROADMAP.md`'s kill criterion is *two things answering to one identity*. **Fourteen trips are on the record**
([`../decisions/2026-08-29-3c-rulings-R6-R12.md`](../decisions/2026-08-29-3c-rulings-R6-R12.md)), all at the
type-identity surface, none in a real merge.

**This document opens a second identity surface. Its first check listed five routes and round 1 constructed
four more through it** — see [`../runs/7A-RUN.md`](../runs/7A-RUN.md) §6.2. The table below is the amended
one, and the four rows added by the loop are marked.

| the route | what stops it |
|---|---|
| two candidates tie and the top one is returned | **Rules 3-3 / 3-4**: the tie test is a **set** test and `ref` is `None`. **[Observed]** on twelve real facilities scoring 1.0 |
| a truncated scan finds nothing and a duplicate is proposed | **Rules 3-5 / 3-6 / 3-7**: `unknowable` is an outcome and `proposal` requires a finished read. **[Observed]** at `cms:entity:facility#745057` |
| an undecidable tenancy predicate silently excludes the real match | **Rules 6-4 / 6-16**. **[Observed]** both readings constructed on 1,373 rows |
| two callers with different thresholds each create a row | **Rule 5-1**. **[Observed]** 31 of 100 rows disagree when it is not the entry's |
| an ingest family proposes a `kind="predicate"` type at volume | **Rule 4-8**: `ACTIONS.md` §2.5's allowlist |
| **a truncated scan FINDS a match and returns `existing` at 1.0** *(round 1, K1/P1 — the tie test evaluated over a partial extent, which is the register's fifth trip one surface down)* | **Rules 3-5 / 3-6**, as amended: completeness is checked before the candidate set is interpreted at all |
| **the match band is wider than the ambiguity margin, so two candidates are both match-grade and one is named** *(round 1, K2 — seven real CMS pairs, no truncation)* | **Rules 3-3 / 5-8**: the tied set is every candidate at or above `match_at`, and `existing` requires exactly one |
| **two rows in ONE ingest act resolve the same label before either is written** *(round 1, F4 — every §3 rule fires correctly and the state is created between two correct answers)* | **Rule 4-10**: within one act a label is resolved once |
| **a pending proposal is cashed twice, or by two concurrent workers** *(round 1, K4 — standing rule (c) one surface down)* | **Rule 4-11**: the propose door asks who already holds a pending proposal for this word |
| **a banded score has no outcome, so the gate and the call answer one row two ways** *(round 1, K3)* | **Rules 5-4 / 5-9**: the gate answers in §3's five and mints no vocabulary of its own |
| **an instance's type is retired underneath it and a zero-row read answers `proposal`** *(round 1, K6)* | **Rules 3-13 / 3-14**: `proposal` requires `scanned > 0`, and the identity read follows the successor chain as **R38** requires of `neighbors` |
| **two different instances collide in `ref_key`** *(round 1, K8 — `C19-82` at a new door)* | **Rule 2-14**: the primitive refuses a record `flat_form_problem` rejects |

**Twelve routes, five of which this document listed and seven of which a loop constructed.** The honest
reading is the one §6.4 of the run record gives: **every one of the seven was a rule that guarded the case
that prompted it and not the case beside it** — standing rule (d), three times in one round, in a row whose
brief cited the register that minted it.

---

## 14. Exit criteria — `ROADMAP.md` Phase 3 row 7a, checked

| the brief asked for | where it is |
|---|---|
| the seam decided by design test 1 **before** anything else was written | §1, and [`../runs/7A-RUN.md`](../runs/7A-RUN.md) §0 is the pre-registration, committed before the probe existed |
| candidate-retrieval primitives, each with a capability flag, each paged per R58 | §2 — two primitives, two flags, three states measured live |
| `resolve_instance` with the four-outcome shape **or a different closed set argued** | §3 — **five**, and T1.5 is the argument |
| the propose-at-ingest contract | §4 — an invocation, one reference shape, five amendments named and routed |
| the match-vs-propose confidence gate as a governed fact | §5 — and §5.1 constructs the alternative's failure |
| `Condition` as the loop consumes it, with the three sibling sections amended in one change | §6, §6.4 |
| host obligations stated | §7 |
| printed shapes, rule→id mapping, contortions, questions | §8, §9, §10, §11 |
| every shape exercised against the public data, conflicts recorded | §12, the four design tests, and §6 of the run record |
| an adversarial loop with every finding constructed and run | [`../runs/7A-RUN.md`](../runs/7A-RUN.md) §6 |
