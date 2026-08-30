# EDGES — typed relationships over the registry

**Version:** `v0` — **unstable.** Every name, field and return shape here may change without a deprecation path. Standing constraint 4.
**Status:** Draft, 2026-08-29. Satisfies `ROADMAP.md` row **#4**. Unblocks Tenshen slices 1–2 (the read seam, and the grounding bundle's `relations` slot).
**Assumptions:** *written against the 2026-08-28 assumptions; see docs/decisions/* — specifically [`decisions/2026-08-28-assumptions-in-lieu-of-office-answers.md`](../decisions/2026-08-28-assumptions-in-lieu-of-office-answers.md).
**Rulings this document carries:** **R7** (`equivalent_to` is an edge, and EDGES v0 must carry type-level edges) · **R13** (the façade does not page in v0) · **R5** (`transaction_scope`, inherited by the edge store) · **R3** (`Refusal.reason` is closed — three values added to [`INTERFACE.md`](INTERFACE.md) §5.12 by this change).
**Claim tags:** **[Observed]** seen directly · **[Inferred]** a reasonable read · **[Assumed]** believed, untested.

**This row was a spec. Row 4b is its implementation, and this document is now the specification of shipped code** — see [`docs/runs/4B-RUN.md`](../runs/4B-RUN.md). The design tests in §9–§11 were walk-throughs driven through real data by throwaway probes ([`docs/tools/`](../tools/)); §10 and §11 are now driven through the shipped store by the **`C18`** contract group as well, on all three reference legs, with the same pre-registered numbers. Where a probe still stands in for a store, it says so.

**What 4b changed in this document, and it is deliberately little.** Three amendments and no reversals: §2.4.1, §4.3 and §4.4 gained rule tables mapping every numbered rule to the contract id that exercises it (ruling **R31**, standing constraint 8); §4.3 gained a thirteenth row for a case the specification did not cover — an edge whose family is registered nowhere; and §16 now reports what landed. Everything the three adversarial rounds of the spec row fixed is now an assertion in the suite rather than in a probe kit the package does not import. The places where the implementation could **not** follow the document as written are enumerated as deviations in [`4B-RUN.md`](../runs/4B-RUN.md) §5, never silently resolved.

---

## 0. What this is, in three sentences

A store of **typed relationships** — `(family, src, dst)` with provenance — where every **family** is itself an entry in the type registry, so a relationship label gets the same proposal→approval loop, lifecycle, consumer analysis and provenance that a noun gets.

It carries edges at **two levels**: between *instances* (`task 41 blocks task 77`) and between *types* (`dpr:borough equivalent_to dot:borough`), and the level is declared by the family, not inferred from the endpoints.

It offers exactly **one read call** — `neighbors(node, edge_families, depth)` — bounded at depth 2, with Rule K/U fields, no traversal language and no materialisation.

---

## 1. Non-goals — one line each

- **No graph database, no query language, no path expressions.** `neighbors` returns edges and the nodes they reach; anything that needs `MATCH (a)-[:X*]->(b)` is out.
- **No materialisation.** The registry does not maintain a mirror of the host's relationships. The edge store is *asked*, never *synchronised* — beacon's own reading of the same choice (beacon spec §5.3(a), §9) is on-demand for the same reason: a copy drifts from the truth.
- **No paging, in the façade.** **R13** applies unchanged: `neighbors` takes no `limit` and no `after`, and the reason is the same one — Rule K has no answer yet for what `known` means on a page. The depth cap in §4.2 is what stands in for it, and §4.2 says so.
- **No instance store.** EDGES stores *edges*. It does not store nodes, node properties, or node existence. `src`/`dst` are **references**, and a reference to something that does not exist is a dangling edge, not an error — §2.7.
- **No reification.** An edge *instance* is never a node. There is no edge-about-an-edge in v0, and the rule that makes it structurally impossible is §2.4.1's — an `InstanceRef` may only name a `kind="entity"` type, so there is no way to construct a reference to an edge. **A `kind="edge"` TypeEntry is a different thing and IS a legal type-level endpoint** (§2.4.1): it is a *row of the vocabulary*, exactly like an `entity` or `value_set` row, and two publishers' relationship vocabularies colliding is UC3's own shape one level up. *(An earlier draft banned `edge` from `endpoint_kinds` outright, which contradicted §3.1's own `equivalent_to` declaration three sections later and was never exercised by any design test. Both round-1 reviewers found it independently — §17.)*
- **No approval loop for individual edges.** Families are approved; instances are written. §2.6 argues it.
- **No entity resolution.** Same gap `INTERFACE.md` §1 names: this document does not decide whether `"BURNS NURSING HOME, INC."` and `"Burns Nursing Home"` are one facility. It records an edge between two *references* the caller supplies.
- **No traversal ordering, ranking or aggregation.** `neighbors` returns a set, not a ranked list. `entity_touchpoint_service`'s *"open work first, because that is the decision input"* is a consumer's ordering, and it stays there.

---

## 2. The edge model

### 2.1 References — the two shapes a node takes

```
TypeRef:                            # a row of the vocabulary. INTERFACE §2.1's identity
    namespace:  str
    kind:       str                 # "entity" | "predicate" | "edge" | "value_set" | <open>
    name:       str

InstanceRef:                        # one thing of that type
    type:       TypeRef             # kind MUST be "entity" — §2.4
    id:         str                 # opaque to this document. The host's identifier

NodeRef = TypeRef | InstanceRef
```

**Why the identity triple and not a surrogate.** `PACKAGE.md` §3.3 already fixes it: *"identity is `(namespace, kind, name)`. No surrogate."* An edge endpoint that named a surrogate id would be unreadable without a join and unstable across a store rebuild.

**`InstanceRef.id` is an opaque string, and that is a decision.** Beacon's ids are integers; CMS's facility key is a CCN string; a Socrata row has a `:id` system field. Typing it `str` costs a cast on one of those three and lets the other two work; typing it `int` excludes CMS outright. **[Observed]** the host-owned table this must sit over (`work_links`) types its endpoint ids `Integer`, so the adapter over it casts — recorded as contortion **E4** in §9.

**A written reference resolves to the identity it now belongs to — not to the reference that was written** *(ruling **R38**, row 4c; founder-visible)*. A stored endpoint is never edited: `merge_types` retires one word with the other as its `successor` and rewrites no edge, and nothing in this package edits a stored reference. So the two questions come apart, and v0 answered them inconsistently:

| the question | answered by |
|---|---|
| *what does this edge say?* | `edge.src` / `edge.dst`, verbatim, forever |
| *whose edge is this now?* | the identity the reference belongs to — its successor chain, resolved |

`resolve_type` has answered the second question since row 3c, and `INTERFACE.md` §5.3 calls the confidence-1.0 redirect a **registry guarantee**. `neighbors` answered the first, so **one identity model per call** — which is a defect rather than a choice, and its cost is that a merge silently orphans every edge ever written against the merged-away name. R38 rules the second answer for both documents. §4.3 rule `4.3-14` is the behaviour; `via_successor` on `NeighborEdge` is the honesty rule that comes with it, and it exists precisely because the first question still has to be answerable.

**A reference carries its own namespace, and that is what makes cross-namespace edges cheap.** `resolve_type` had to be scoped to one namespace because it *searches* (`INTERFACE.md` §10b.1, contortion 8). `neighbors` reads a stored fact whose two endpoints are both fully named, so there is nothing to search and nothing to scope. §4.5 develops this; it is the single most useful thing this document does for UC3.

### 2.2 `Edge`

```
Edge:
    edge_id:      str               # opaque, generated ABOVE the store. PACKAGE §4.2's rule
    family:       str               # the NAME of a kind="edge" TypeEntry. §2.3
    namespace:    str               # the namespace the FAMILY is registered in — not the endpoints'
    src:          NodeRef
    dst:          NodeRef
    provenance:   EdgeProvenance    # §5
    attributes:   dict              # the family's payload, opaque unless a schema is in force. §2.5
    status:       "active" | "retracted"    # §2.6
    warnings:     list[str]         # INTERFACE §5.4's vocabulary - which this change AMENDS. §2.8
    attr_schema_version: int | None # the payload schema in force when this was written. §2.5
```

**The call that writes one, and it was printed nowhere until row 4c.**

```python
def add_edge(
    family: str,
    src: NodeRef,
    dst: NodeRef,
    created_by_actor: str,
    *,
    namespace: str = "default",
    created_by: str = "user",              # INTERFACE §2.1's vocabulary, incl. R17
    confidence: float | None = None,       # None = nothing scored it. NOT 0.0 — §5.1
    evidence: list[Evidence] = (),
    source_version: str | None = None,     # the SOURCE's own version. §5.3
    model_tier: str | None = None,         # ruling R20
    attributes: dict | None = None,        # the family's payload, validated per §2.5
) -> Edge | Refusal: ...
```

> **This block exists because a gate found it missing** *(row 4c)*. `INTERFACE.md`'s fourteen call signatures have been held against `Registry` by [`check_spec_drift.py`](../tools/check_spec_drift.py) since row 3c and `PACKAGE.md`'s eighteen primitives since row 4b's third adversarial round; **this document's calls were held against nothing at all** — in the one document whose surface is not in `INTERFACE.md` §5. Row 4c extended the gate to `add_edge`, `retract_edge`, `amend_edge` and `neighbors`, and its first run reported *"EDGES `add_edge()`: no signature printed in the spec"*: the **primary write call of the whole document** had a data shape, a behaviour section and no signature, so a reader implementing from the document had to infer the argument list from prose. Exactly the class deviation **D-4b-2** recorded one layer down, found the same way — by a checker rather than by a reader.

**`namespace` on the edge is the *family's* namespace, and the endpoints keep their own.** A `dot` consumer may write an `equivalent_to` edge (family registered in `default`) between a `dpr` type and an `oti_311` type. Three namespaces, one edge, no contradiction — because the field answers *"whose word is `equivalent_to`?"*, not *"whose data is this?"*. **Stated because the obvious alternative — deriving the edge's namespace from its endpoints — has no answer when the endpoints disagree, which in UC3 is the normal case.**

**There is no `direction` field.** `src` and `dst` are ordered; whether the order carries meaning is the family's business (`symmetric`), not the edge's.

> **And that has a consequence the first two drafts did not draw: `neighbors(direction=…)` must not filter a symmetric family.** `A equivalent_to B` **is** `B equivalent_to A` — the stored order is an accident of which publisher wrote it — so filtering on `src`/`dst` makes the answer depend on that accident. **[Observed]**, on `equivalent_to`, the only family this document ships: one edge written `src=dpr, dst=dot`, then `neighbors(dot:borough, ["equivalent_to"], direction="out")` returned `known=0, complete=True, nodes=[]`. **A confident, complete, false negative** — Rule U's forbidden empty, produced by a parameter the caller was entitled to pass. Found in round 2 (§17) by a reviewer trying a parameter combination no design test had tried. §4.1 states the rule; the alternative (refusing `direction != "both"` when any searched family is symmetric) was rejected because it breaks a mixed query over one symmetric and one directed family, which is the ordinary case.

### 2.3 The edge family **is** a `TypeEntry` with `kind="edge"`. No fifth kind, and not a predicate.

The brief asks whether `edge_family` is a new `kind` value or a predicate. **Neither. It is the `kind="edge"` that `INTERFACE.md` §2.2 already defines**, and the justification is worth spelling out because both alternatives are superficially attractive.

**Why not a fifth kind `edge_family`.** `INTERFACE.md` §2.2 defines `edge` as *"a relationship type. Registered here (name, definition, provenance, lifecycle); its shape and its instances live in #4."* That sentence describes an edge family exactly. Adding `edge_family` beside it would put two words in the registry's own `kind` vocabulary for one concept — which is `INTERFACE.md` §2.3's **Cause B**, semantic collision, committed by the spec whose job is to prevent it. It would also silently invalidate a determination already made and shipped: `PACKAGE.md` §7.1 rules that beacon's `work_link_types` rows are `kind="edge"` and has the adapter supply the constant. A fifth kind would make that constant wrong on the day EDGES landed.

**Why not a predicate.** `INTERFACE.md` §2.3 is explicit: a predicate is *a named capability set* whose **members are types** and whose extent is derived from `TypeEntry.predicates`. `blocks` has no extent of that shape — its members are *edges*, not types — and `merge_types` refuses predicate merges non-overridably, which would make two genuinely duplicate edge families unmergeable for the wrong reason. Making families predicates would also mean §2.3's *"a predicate is not a supertype"* rule has to be re-litigated for edges, and it should not be.

**What this buys, and it is the whole architectural bet of this document.** A family gets, free and unchanged:

| From INTERFACE | What it means for a family |
|---|---|
| `propose_type` → `approve`/`reject` | a new relationship label is a *request*, not a fact — mechanism **1** |
| `resolve_type` | a proposer is told `blocks` already exists before inventing `blocked_by_task` — mechanism **2** |
| `usage` / `retire` / `list_types(orphaned=True)` | a family nothing writes any more is enumerable — mechanism **3** |
| `namespace` | two teams may both have `owns` and mean different things — mechanism **4** |
| **`consumers` / `predicates`** | **the code paths that traverse this family, and the ones that would silently drop a new one — mechanism C, and §8 is the argument** |
| `Provenance`, `Evidence`, `model_tier` | *which model proposed this label, on what evidence, and did a human approve it* |

**No new call in `INTERFACE.md` §5 is required to manage families.** That is the test of whether this decision is right, and it passes: this document adds none. *(The surface went 13 → 14 in row 3e, and not because of this document: ruling **R11** added `reinstate`, which by ruling **R19** covers edge **families** — they are `TypeEntry`s — and never edge **instances**, for which a retraction is no claim (§3.2) and a re-assertion is a new edge.)*

**What would change this.** If a family ever needs a field that cannot honestly live in `attributes` *and* cannot be validated by `PACKAGE.md` §5 — i.e. a field the registry itself must read — then `kind="edge"` has stopped being a type and wants its own table, and this section is wrong. §2.5 is where that pressure would show up first.

### 2.4 The family's declared shape

Five fields, all in `TypeEntry.attributes`, all governed by one `AttributeSchema` keyed `(namespace, kind="edge")` — `PACKAGE.md` §5.2's mechanism, used for the first time on a kind where every entry has the *same* shape, which is the case that mechanism was designed for.

| key | type | meaning |
|---|---|---|
| `level` | `"type" \| "instance"` | which shape the endpoints take (§2.1). **Required.** No default: a family that does not say is a family whose edges cannot be validated |
| `symmetric` | `bool` | `A→B` asserts `B→A`. Required |
| `inverse_label` | `str \| None` | the name to read `dst→src` by (`blocks` / `blocked_by`). **Must be `None` when `symmetric` is `True`** |
| `endpoint_kinds` | `{"src": [kind…], "dst": [kind…]}` | which registry `kind`s each end may take. §2.4.1 |
| `payload_schema` | `str \| None` | the name of an `AttributeSchema` governing `Edge.attributes` for this family. §2.5 |

`created_by` is **not** in this list: it is `TypeEntry.created_by` (`seed | ai | user`), already required by `INTERFACE.md` §2.1 with the same three values, taken from UC1's `work_link_types` in the first place. Restating it in `attributes` would be a second home for one fact.

**This is `work_link_types` generalised — and UC1 is cited as a test, not a source.** `work_link_types` has `is_symmetric` and `inverse_label`; two of the five keys above match it, and the other three (`level`, `endpoint_kinds`, `payload_schema`) come from data beacon does not have: CMS forces `endpoint_kinds` (a `has_severity` edge must not accept a **`value_set`** where it declared an **`entity`** — T2.5 — §10), and UC3 forces `level` (`equivalent_to` runs between types, and beacon has no type-level edge at all — §11). The direction of the borrowing is checked in §15.

> **The sentence above was narrowed by ruling **R33**, row 4c, and the old one is quoted here rather than deleted.** It read: *"a `citation` edge must not accept a `facility` at the tag end"* — and **`endpoint_kinds` cannot express that**, because a citation and a facility are both `kind="entity"`. The field constrains an endpoint's **kind**, never its **type**, and the motivating example named a constraint the mechanism has no slot for. Row 4b implemented the field, found the gap and recorded it as deviation **D-4b-3**; **Q28** asked whether §2.4 should gain an endpoint *type* constraint or whether the sentence should be narrowed. R33 rules: **narrow the sentence, do not widen the mechanism.**
>
> **Why not widen it.** An endpoint *type* constraint is a second identity triple per end — a family would declare not just *what kind may sit here* but *which row of the vocabulary* — and that is a schema language growing inside a five-key declaration, which is the same move §2.4.1 refuses for `equivalent_to`'s same-kind rule (ruling **R32**) and `PACKAGE.md` §5.6 refuses for cross-field rules. **The consumer that would force it is Phase 3's ingestion loop**, and until that consumer exists a mechanism invented for one fixture's convenience is a mechanism with one user and no evidence.
>
> **What CMS actually gets from §2.4.1, and it is real:** the entity-vs-`value_set` exclusion. `citation:42 --has_severity--> scope_severity_code:J` is refused, which is what stops a column of 419,479 property values becoming 419,479 edges. What CMS does **not** get is *"src is a citation and dst is a survey"*; that fact lives in the vocabulary rows' own unvalidated `from`/`to` attributes, which is where it lived before this document and where it stays. Rule `2.4.1-7` carries the tag.

**The win this closes, named in `INTERFACE.md` §9 contortion 1.** That contortion says v0 *"cannot stop two types disagreeing about direction"* and *"cannot enforce that a symmetric type has no inverse label"*. With the schema above in `warn` or `enforce` mode, `propose_type(kind="edge", attributes={"symmetric": True, "inverse_label": "blocked_by"})` is a cross-field rule — and `PACKAGE.md` §5.6 says plainly that `FieldSpec` is per-field and **does not validate cross-field rules**. **So contortion 1 is half closed, not closed:** the fields now have a declared, versioned, described home (that is real), and the *"symmetric implies no inverse"* rule still has nowhere to be checked. It is checked by the registry at family-approval time as a documented rule of this section, not by the schema mechanism — and that is one rule this document asks `approve()` to know, recorded as **Q13** in §14 because it is a small crack in `PACKAGE.md` §5.6's own boundary.

#### 2.4.1 `endpoint_kinds`, and the rule that decides what a value set may be

> **A `level="instance"` family accepts only `kind="entity"` endpoints. A `level="type"` family accepts any registered kind except `predicate`. No family, at either level, may name `predicate`.**

The three clauses earn their keep on real fixtures, and the first two pull in opposite directions:

- **Instance level, entities only.** Only an entity has instances. A `predicate`'s extent is a set of *types*; a `value_set`'s members are *values*; an `edge` family's instances are edges, and §1 rules out reification. So `citation:42 --has_severity--> scope_severity_code:J` is **refused** (`endpoint_kind_mismatch`) — and that refusal is the right answer for UC2, because it stops the registry from turning a column of 419,479 property values into 419,479 edges, and stops it from having to know what a *value* is, which `INTERFACE.md` §2.1 refuses on purpose and ruling **R8** deferred to Phase 3. **Severity is a property of a citation, and this document does not store node properties (§1).**
- **Type level, any kind but one.** `dpr:value_set:borough equivalent_to dot:value_set:borough` is exactly UC3's W2 case, and the endpoints are `value_set` entries. Forbidding `value_set` here would make the one relation R7 exists to provide unexpressible on the data that forced it. **`kind="edge"` is legal here too**, and it is not reification: `dpr:edge:concerns equivalent_to oti_311:edge:relates_to` relates two *rows of the vocabulary*, which is what a type-level edge does. Reification would be an edge pointing at an edge **instance**, and the instance-level clause makes that unconstructible.
- **`predicate` is excluded at BOTH levels, and it is a general rule rather than a family's opt-in.** Two predicates being "equivalent" is a claim about **extents**, and `INTERFACE.md` §5.10's refusal #2 (`predicate_merge`) is non-overridable precisely because that claim must be made from **non-empty** byte-identical extents or not at all. *(The `non-empty` half was added by row #6's second adversarial round, which merged two live predicates through the shipped registry because `set() == set()`; this document's statement of the rule was the one `ACTIONS.md` cited as correct, and was left stale by that row's own fix until its third round found it.)* A type-level edge asserting equivalence between two predicates is **the `ROADMAP.md` kill row one indirection away** — *a capability predicate treated as a duplicate* — and §15 claims it is structurally blocked. It is only structurally blocked if the rule is general. *(It was not, in the first draft: a round-1 reviewer declared a permissive family of their own and wrote a predicate-to-predicate edge with no refusal. §17.)*

**So a `value_set` IS a legal edge endpoint — as a type, never as an instance.** Two fixtures pulling opposite ways, one rule, no exception clause. The decision the brief asks for in §10 is this sentence.

> **All three clauses bind at family-DECLARATION time, not only at write time, and that distinction is the one round 1 was spent on.** A rule checked only when an edge is written is a rule a family author can opt out of by declaring a permissive `endpoint_kinds` — and both halves of this section were exactly that in the first draft. A reviewer declared a family with `predicate` endpoints and wrote a predicate-to-predicate edge with no refusal (the kill row, §15); writing the test for that then exposed the same hole in the instance clause, where a family declaring `("entity", "edge")` at instance level would have reified an edge. **A family whose `endpoint_kinds` breach this section is refused when it is declared**, so the write-time check has nothing left to be talked around — and the write-time check still runs, because an endpoint of the wrong *level* is a caller's mistake rather than the family's. Both layers are exercised in [`edges_capability_probe.py`](../tools/edges_capability_probe.py); §17.

**`equivalent_to` additionally requires `src.kind == dst.kind`** — a family-level constraint beyond `endpoint_kinds`, stated in §3.1 rather than here, because it is that family's semantics and not a general mechanism.

> **The rules of this section, numbered and each exercised or tagged** — ruling **R31**, standing constraint 8. Held against the contract suite by [`check_spec_drift.py`](../tools/check_spec_drift.py).

| # | rule | exercised by |
|---|---|---|
| 2.4.1-1 | A `level="instance"` family accepts only `kind="entity"` endpoints — only an entity has instances, and §1 rules out reification | `C17-09`, `C18-04` |
| 2.4.1-2 | A `level="type"` family accepts any registered kind except `predicate`, `kind="edge"` included — that is a row of the vocabulary, not a reified instance | `C17-30`, `C17-27`, `C18-05` |
| 2.4.1-3 | `predicate` is excluded at **both** levels, as a general rule rather than a family's opt-in — the `ROADMAP.md` kill row is one indirection away | `C17-09` |
| 2.4.1-4 | All three clauses bind at family-**DECLARATION** time, not only at write time; the write-time check still runs, because an endpoint of the wrong *level* is a caller's mistake rather than the family's | `C17-08`, `C17-09` |
| 2.4.1-5 | A family whose declaration breaches this section is refused at every door a declaration can arrive through | `C17-09` |
| 2.4.1-6 | `equivalent_to` additionally requires `src.kind == dst.kind` (§3.1's family-level constraint) | `C17-08` |
| 2.4.1-7 | `endpoint_kinds` constrains the **kind** of an endpoint and not its **type**, so it cannot say *"src is a citation and dst is a survey"* — both are entities | `prose-only:` the mechanism has no slot for it, which is a limit of §2.4 rather than a rule to test — **ruled by R33 (row 4c): narrow the sentence, do not widen the mechanism**, because an endpoint *type* constraint is a second identity triple per end and Phase 3's ingestion loop is the consumer that would force it. §2.4's motivating sentence is narrowed accordingly; the old wording is quoted there rather than deleted. Deviation **D-4b-3** in [`4B-RUN.md`](../runs/4B-RUN.md); CMS carries the fact in unvalidated `from`/`to` attributes meanwhile |

### 2.5 `payload_schema` — validated, as of ruling **R34** (row 4c, 2026-08-29)

`Edge.attributes` carries the payload a family declares — `role` on a stakeholder edge, `description` and a join basis on an inferred one. Validation is `PACKAGE.md` §5's mechanism, and **the key was the problem**: §5.2 keyed an `AttributeSchema` by `(namespace, kind, version)`, one per **kind**. Every edge family shares `kind="edge"`, and their payloads do not share a shape — `task_stakeholders` has `role` and a NOT-NULL `source`; `person_links` has none; `meeting_attendees` has six.

That is **exactly** `PACKAGE.md` §5.6's recorded failure, on which ruling **R10** was made: *attribute schemas keyed per name as an override — YES, row 3e.* R10 landed in row 3e; this field stayed inert through row 4b anyway, which recorded it as deviation **D-4b-6** and asked **Q29**. Ruling **R34** answers it: *take it in row 4c.*

> **The mechanism is `PACKAGE.md` §5's, transposed and not reinvented.** Three modes, versions that are never retroactive, and R10's enforcement floor — every one of them is that section's rule, reached one kind along. Nothing here is a second validation mechanism for edges, and a reader who knows §5 already knows this section.

**1. The key is `(namespace, "edge_payload", <the declared name>)`, and the kind is not `"edge"`.** This is the one place where §2.5's original sentence could not be implemented as written, and it was reproduced before it was designed around. That sentence said `(namespace, "edge", <family name>)` — which is the **identical key ruling R10 gives the name-level schema governing the family's own `TypeEntry.attributes`**, its `level`, `symmetric`, `inverse_label`, `endpoint_kinds` and `payload_schema`. One key, two dicts, which is `INTERFACE.md` §2.3's Cause B.

**[Observed, row 4c]** a payload schema `{"role": FieldSpec(str)}` with `additional="forbid"` registered under `(default, "edge", "blocks")` made `propose_type(kind="edge", name="blocks", …)` return `Refusal(reason="attributes_schema_violation")` naming all five declaration keys as *"not declared in the schema"*: **governing a family's payload made the family unregisterable.** A schema kind of its own separates the two spaces with no new table, no new primitive and no reachable collision — including the case that produced the finding, where a family's payload schema is named after the family. Deviation **D-4c-1**; `C17-38` is the regression pin.

**2. Two levels, the same shadowing rule R10 already wrote.** A schema keyed `(namespace, "edge_payload")` with no name governs **every** edge payload written in that namespace; a family's declared `payload_schema` name **shadows** it for that family. Shadowing is replacement of the *fields* and never a merge (`PACKAGE.md` §5.2b rule 1), and the *strictness* is a **floor** (rule 3) — a `mode="off"` override under an `enforce` namespace schema still refuses, because an override is a schema and not an exemption. `C17-39`.

**3. Three modes, `PACKAGE.md` §5.3's, unchanged.** `off` checks nothing and is the default, so an untouched deployment behaves exactly as row 4b shipped. `warn` writes the edge and carries `attributes_invalid:<field>:<why>` on it — `INTERFACE.md` §5.4's existing value, on one more carrier. `enforce` returns `Refusal(reason="attributes_schema_violation")`, **§5.12's existing value with no new one minted**, whose `detail` names the schema that refused (`schema_name`, `schema_version`, per `PACKAGE.md` §5.2b rule 4) and the `family`, because two families in one namespace may be judged by two different schemas. `C17-35`, `C17-36`.

**4. `attr_schema_version` is recorded on the `Edge`, and `PACKAGE.md` §5.4's promise is what it buys.** *Entries written under an older schema are never rewritten and never retroactively invalidated — it makes them v1 rows.* An edge carries the version in force at its write for the reason a `TypeEntry` does: so a reader can tell which generation of a payload they are looking at without the registry pretending to interpret it. `None` still means *"written with validation off"* (`INTERFACE.md` §2.1), which is now a reachable state with a second cause — see rule 5. `C17-36`.

**5. A family that names a schema nobody registered is written, and warned about.** `payload_schema_unregistered:<name>` — the twenty-sixth `warnings` value, added to `INTERFACE.md` §5.4 in the same change per ruling **R3**. Refusing would put the ordering of two deployment acts (register the family, register the schema) inside a data path and make a family declared first permanently unusable; writing it silently is the inert `payload_schema` this ruling exists to end, because the caller could not then tell a validated payload from an unvalidated one. Rule U in one value. `C17-37`.

**6. The payload is validated against what the CALLER wrote, not against what survives storage.** That is the type side's order (`_write_approved` validates `rec.attributes`) and it is the honest one: a `required` field a backend cannot store is that backend's declared loss (§6, `stores_edge_attributes`, and `PACKAGE.md` §5.7's projections), not the writer's schema violation. **The consequence, stated rather than found later:** on a backend that stores no arbitrary edge attributes, a payload can validate on the way in and come back absent. §6's table already says no warning is minted for that — the returned record is the signal and `Capabilities.why` says why — and this section does not add a second way to report one fact.

**7. `PACKAGE.md` §5.5's census floor applies to edge payloads too.** Every key ever written is recorded under `kind="edge_payload"`, in every mode, so `attribute_census(kind="edge_payload")` enumerates what edge payloads actually carry. §5.5's argument is that the escape hatch *"will accumulate if nobody watches it"*, and `Edge.attributes` is that hatch on the surface with millions of rows rather than hundreds. The tri-state `declared` is honest here because the census discovers payload schemas **through the families that declare them** — there is no `kind="edge_payload"` type to enumerate, and without that discovery the census would answer a confident `declared=False` about a key a payload schema declares `required`, which is the exact wrong answer R10's own census fix was made to stop. `C17-40` (**nonbinding**, ruling R2).

> **The rules of this section, numbered and each exercised or tagged** — ruling **R31**, standing constraint 8. Held against the contract suite by [`check_spec_drift.py`](../tools/check_spec_drift.py).

| # | rule | exercised by |
|---|---|---|
| 2.5-1 | An edge payload schema is keyed `(namespace, "edge_payload", <declared name>)` — **not** `(namespace, "edge", <family name>)`, which is the key R10 already gives the family's own declaration, so registering one made the family unregisterable | `C17-38` |
| 2.5-2 | A `(namespace, "edge_payload")` schema with no name governs every edge payload in the namespace; a family's declared name shadows it, replacing the fields, and the strictness is a floor | `C17-39` |
| 2.5-3 | `enforce` refuses with `attributes_schema_violation` and `detail` naming which schema and which family; `warn` writes and carries `attributes_invalid:<field>:<why>`; `off` is the default and checks nothing | `C17-35`, `C17-36` |
| 2.5-4 | `attr_schema_version` records the version in force at the write, and an edge written under an older schema is never re-validated and never rewritten | `C17-36` |
| 2.5-5 | A family declaring a `payload_schema` no schema answers to is **written**, with `payload_schema_unregistered:<name>` and `attr_schema_version=None` | `C17-37` |
| 2.5-6 | The payload is validated as the caller wrote it, before the backend's projection rules drop what it cannot store — a column somebody else's schema lacks is not the writer's violation | `prose-only:` the two orders differ only on a backend declaring `stores_edge_attributes=False`, where §6's table already fixes what is reported and forbids a second warning for it. There is no third behaviour to assert |
| 2.5-7 | Every edge payload key ever written is censused under `kind="edge_payload"`, in every mode, and `declared` stays tri-state because the census finds payload schemas through the families that declare them | `C17-40` |

**What this does NOT do, stated rather than implied.** It does not validate cross-field rules on a payload — `FieldSpec` is per-field and `PACKAGE.md` §5.6 says so; the one cross-field rule this registry knows is R18's, about a family's *declaration*, and it is an exception list of length one. It does not give a payload schema a proposal→approval loop: an `AttributeSchema` is deployment configuration and not a word in the vocabulary (`PACKAGE.md` §5.2), and that cost is already recorded there. And it does not migrate an existing edge: §5.4's rule is the whole point of carrying the version.

### 2.6 Lifecycle — `active | retracted`, and no proposal loop for instances

An edge has two states. There is no `proposed`.

**Why families are governed and instances are not.** The proposal→approval loop exists because a *word* entering a vocabulary is a claim everyone downstream inherits (`INTERFACE.md` §5.4). A single edge is a fact about two things, not a claim about the vocabulary; there are millions of them; and beacon writes them from a weekly scheduled job at ≥0.7 confidence without a human in the loop **[Observed, beacon spec §2.5]**. A design that put an approval queue in front of that would either be ignored or would stop the job. **The governance lives one level up, where it is affordable and where it bites**: the *label* `colleague` was approved once; the ten thousand `colleague` edges are provenance-bearing facts.

**`retract_edge`, and why it is not `retire`.**

```python
def retract_edge(edge_id: str, reason: str, *, retracted_by: str) -> Edge | Refusal: ...
```

`reason` is REQUIRED and non-empty, for `INTERFACE.md` §5.5's reason: *the cheapest record of "we already considered this and decided against it"*. Nothing is deleted: `status` becomes `retracted`, the row stays, an event is appended.

**It is not refused when the store cannot record events, and that is a departure from `PACKAGE.md` §3.6 that must be argued rather than assumed.** §3.6's rule is *a destructive override that cannot be recorded is refused*, and it refuses `retire(force=True)` on `stores_events=False`. Retraction is different in the way that rule cares about: **the record is the row.** `status="retracted"`, `retracted_by`, `retracted_at` and `reason` are columns on the edge itself (§7.1's `EdgeRecord`), so an unrecordable retraction does not exist — the audit trail survives in the store even with no event table. What is lost without events is the *sequence* (retracted, reinstated, retracted again), and that is surfaced as a warning, not a refusal:

- `stores_edge_events=False` ⇒ the returned edge carries `warnings: ["retracted_without_event_trail:<why>"]`, `<why>` verbatim from `Capabilities.why`.

**`retract_edge` on an `edge_id` the store does not hold returns `Refusal(reason="unknown_edge")`** — the nineteenth value of `INTERFACE.md` §5.12, added by this change per **R3**, and the exact shape of `unknown_proposal` one object along. *(It reused `edge_family_unknown` until round 3, which names a different failure: §2.3's Cause B, committed inside a document that argues at length against reusing `kind_mismatch` for two things.)*

**A SECOND retraction is refused `already_decided`** *(ruling **R39**, row 4c)*. §2.6's argument for not refusing an unrecordable retraction is *"the record **is** the row"* — and **that argument silently assumes retraction happens once.** A second retraction overwrote the first's reason, actor and timestamp on the row, and on `stores_edge_events=False` the first decision was then gone entirely, so the justification stopped holding at the exact moment the case occurred. Recorded by row 4b as deviation **D-4b-16** and question **Q34**.

It is **not** made idempotent, and that is the ruling rather than an implementation choice: **idempotency would hide a real double decision.** Two people withdrawing one edge for two different reasons is a fact about a deployment, and a call that silently returns the first decision has answered a question nobody asked. A refusal names it. `already_decided` is `INTERFACE.md` §5.5's existing value — it says precisely this about a proposal one object along — so nothing is minted; `detail` carries the standing `retracted_by`, `retracted_at` and reason, so the caller learns whose decision it was without a second call. The read happens **inside the transaction**, as `approve`'s does, which is what turns a race into a refusal rather than a lost write. `C17-47`.

**There is no `delete_edge` in v0, and no reinstatement.** Deletion is out because nothing else in this project deletes. Reinstatement is out because ruling **R11** is already specifying `reinstate` for types in row 3e, and inventing a second, differently-shaped reinstatement for edges one row ahead of it is how two calls come to mean nearly the same thing. **Recorded as Q14** — 3e should decide whether `reinstate` covers edges.

**A retracted edge is invisible to `neighbors` by default** and reachable with `include_retracted=True`, mirroring `list_types(include_retired=)` — including its Rule K consequence: a default that hides things sets `complete=False` (§4.3).

### 2.7 A dangling endpoint is a fact, not an error

`src` or `dst` may reference a type that is not registered, or an instance that no longer exists. `put_edge` does **not** check that endpoints exist, and `neighbors` returns them.

**Why, and it is `PACKAGE.md` §3.4 primitive 10's argument transposed.** `put_consumer` deliberately accepts a `gate` naming a predicate that does not exist, *because a consumer gating on a word nobody registered is precisely mechanism C, and refusing the registration would hide it.* The same holds here: an edge pointing at a type nobody registered is the ingestion layer's mistake made visible; refusing the write moves the failure into a log nobody reads.

Two consequences, both stated:

- **`endpoint_kind_mismatch` can only fire when the endpoint's type IS registered.** On an unregistered endpoint the registry cannot know the kind, so it does not guess: the edge is written and carries `warnings: ["endpoint_type_unregistered:<namespace>:<kind>:<name>"]`. Rule U — a positive claim about a mismatch requires having looked. This is the same shape as `gate_unregistered:<gate>` (ruling R8) and deliberately so.
- **Orphan sweeping is not this document's job.** Beacon's `purge_orphan_links` **deletes** rows whose endpoint it does not recognise, and **[Observed, beacon spec §10.4]** its `else` branch judges every non-`task` endpoint against the project id set, so live `report` edges written by `decisions/actions.py` are purged daily. That is recorded as contortion **E5** in §9. This document's position: an orphan is `retract_edge`'s subject, never a `DELETE`.


### 2.8 The warnings vocabulary is closed too, and this change amends it

`INTERFACE.md` §5.4 enumerates the `warnings` vocabulary — *"complete — eleven values across three carriers"* — and §5.12 does the same for `Refusal.reason`, with **ruling R3**'s rule attached: *a value is added by amending the enumerating section in the same change that introduces it.*

**R3's rule is written for `Refusal.reason`. It applies with equal force here, and the first draft of this document broke it.** Three refusal values were added to §5.12 correctly and carefully; five *warning* values were minted in the prose of §§2.6–8 and §4.3 and enumerated nowhere, while `Edge.warnings` claimed to carry *"INTERFACE §5.4's vocabulary. Same values."* **A closed vocabulary that opens by prose is not closed**, and doing it in the same document that gets the sibling case right is worse than doing it by oversight. Found by a round-1 reviewer; see §17.

**So §5.4 is amended in this change, to sixteen values across four carriers.** The five, with their carrier:

| value | carrier | from |
|---|---|---|
| `endpoint_type_unregistered:<namespace>:<kind>:<name>` | **`Edge`** | §2.7 — the endpoint's type is not registered, so no kind claim is made in either direction. Rule U, and the same `<name>:<subject>` shape as `gate_unregistered` (ruling R8) |
| `retracted_without_event_trail:<why>` | **`Edge`** | §2.6 — the retraction stands (the row *is* the record) but its sequence is unrecoverable. `<why>` is the backend's own sentence |
| `edge_family_retired:<name>` | **`NeighborReport`** and **`Edge`** | §4.3 on the READ — a named family is retired; its edges were not deleted, so it is searched, and the caller is told. **And on the WRITE**: `add_edge` onto a retired family is not refused (retirement is a statement about the vocabulary; an edge is a fact about two things) and the returned `Edge` carries this, because a caller who has just written under a word somebody withdrew is entitled to know. *(The second carrier was added by row 4b, which found its own code emitting the value there while this table listed one carrier — **a closed vocabulary opening by CODE rather than by prose**, which is a worse version of this section's original finding, not a better one. `C17-15` binds both carriers.)* |
| `origin_type_unregistered:<ref>` | **`NeighborReport`** | §4.3 — the walk's origin names a type nobody registered |
| `endpoint_type_merged:<ref>` | **`NeighborReport`** | §4.3 rule 14 — this reference's identity spans more than one written name, joined by a merge or a retirement-with-successor. **The value keeps its name and its meaning CHANGED with ruling R38** *(row 4c)*: it said *"and edges under the other name were not searched"*, and it now says **they were, and each one is marked `via_successor`**. The report is no longer incomplete for this reason — a caller who needs to know which edges were followed reads the marker, not `complete`. Minted by row 4b's third adversarial round; amended here in the same change that changed the behaviour, per ruling R3, because a closed vocabulary whose values quietly change meaning is not closed either |
| `no_edge_gate_registered` | **`ConsumerReport`** | §8 — no predicate's extent contains any edge family, so `would_drop: []` means *nobody told us what traverses edges*, not *nothing will drop this* |

**One value was considered and deliberately NOT minted:** a warning for attributes that did not round-trip. `PACKAGE.md` §3.4 primitive 4's mechanism already reports it — the returned record simply lacks the key, and `Capabilities.why` says why — and the type side has no such warning. Adding one on the edge side would make one fact reportable two ways. §6.

---
---

## 3. Type-to-type edges — ruling R7

### 3.1 `equivalent_to`, the first family

Ruling **R7**: *a relation between two scoped types is a type-to-type edge, so EDGES v0 must carry type-level edges, not only instance-level ones; `equivalent_to` is its first named family (symmetric, non-merging, provenance-bearing).* Its subject is `INTERFACE.md` §10b.2, contortion 9: *nothing can say "these two mean the same thing, kept apart."*

```
TypeEntry(
    name="equivalent_to",
    kind="edge",
    namespace="default",
    definition=(
        "The two types denote the same thing in their respective vocabularies. "
        "It does NOT assert that they are interchangeable, that their value sets "
        "match, that their consumers accept each other, or that either may be "
        "retired in favour of the other. It licenses a reader to join them and "
        "requires that reader to look at both definitions first."
    ),
    created_by="seed",
    attributes={
        "level": "type",
        "symmetric": True,
        "inverse_label": None,
        "endpoint_kinds": {"src": ["entity", "value_set", "edge"],
                           "dst": ["entity", "value_set", "edge"]},
        "payload_schema": None,
    },
)
```

**Family-specific constraint: `src.kind == dst.kind`.** An `entity` is not equivalent to a `value_set`; `facility ≡ deficiency_corrected_status` is a category error, not a claim. A cross-kind attempt is refused `endpoint_kind_mismatch` with `detail={"src_kind":…, "dst_kind":…}`.

**`predicate` is absent from the list above because §2.4.1 forbids it generally, not because this family opted out.** That distinction is the whole point and it was got wrong once (§15, §17): a per-family exclusion is a rule that holds only as long as every future family author remembers it, and the thing on the other side of it is the kill row. `kind="edge"` **is** in the list, and §2.4.1 argues why that is not reification: `dpr:edge:concerns ≡ oti_311:edge:relates_to` relates two rows of the vocabulary, which is precisely what a type-level edge is for, and it is the shape UC3 predicts when two agencies name the same real-world relation differently.

**Explicitly NOT transitive, and not closed.** `A ≡ B` and `B ≡ C` do **not** yield `A ≡ C`. Three publishers wanting a three-way join write three edges. This is not a limitation to be fixed later; transitivity would make the family a silent equivalence-class builder over a registry whose whole answer to mechanism 4 is *scoping*, and one wrong edge would then merge a class. §4.4 is where this becomes a reporting requirement rather than a note.

### 3.2 What `equivalent_to` licenses, and what it does not

| It **does** | It **does not** |
|---|---|
| let a reader join two scoped types deliberately, having seen both definitions | make them one type, or make either retireable in favour of the other |
| carry provenance: who claimed this, when, on what evidence, at what confidence | assert anything about their *values* — three `borough` value sets stay three, with three encodings (§11) |
| become visible to `resolve_type` in `alternatives` — **once R6's `search_namespaces` exists (row 3e)** | make `resolve_type` cross-namespace on its own. An edge is not a lookup index; **[Observed]** contortion 8 is closed by R6, not by this document |
| answer `neighbors(dpr:borough, ["equivalent_to"])` today | answer *"what is the canonical borough type?"* — there is no canonical one, by construction |
| get retired like any type, and retracted like any edge | survive as a licence after retraction: a retracted `equivalent_to` is not a weaker claim, it is no claim |

**`merge_types` is untouched, and this is the load-bearing sentence of the section.** `Refusal(reason="cross_namespace_merge")` is non-overridable (`INTERFACE.md` §5.10 refusal #4), and an `equivalent_to` edge is **not** an `acknowledge` token, not a precondition that weakens the refusal, and not evidence for one. If it were, the answer to mechanism 4 would have quietly become *merge, once someone asserts equivalence* — which is the exact failure `§2.6` of INTERFACE calls *the destructive move*. **An edge asserting sameness and a merge performing it are different acts, and the second stays refused.**

`resolve_type`'s `alternatives` may **surface** an equivalent — that is the one interaction — and even there the rule is Rule K: an alternative reached through an `equivalent_to` edge is labelled as such, so a caller can tell a scored near-miss from an asserted equivalence.

### 3.3 `narrower_than` — considered, **not taken in v0**

The brief invites a second family *if a use case needs it*. **None of the three does.**

- **UC1**: `part_of` already exists in `work_link_types` and is an *instance*-level family (task part_of project), not a type-level one. It is expressed in §9 unchanged and needs nothing new.
- **UC2**: the three levels (citation → survey → facility) are instance-level containment, served by ordinary instance families. `deficiency_tag` is not narrower than `citation`; it is a lookup.
- **UC3**: `community_board` and `council_district` nest inside `borough` geographically — but that is a fact about **values**, not about types, and §2.4.1's rule keeps values out of the edge store. The type-level claim *"`dpr:council_district` is narrower than `dpr:borough`"* is not something any of the three fixtures needs to record, and inventing it would let a reader build a taxonomy.

**And a taxonomy is the thing to be careful about.** `INTERFACE.md` §2.3 states three times that a predicate *is not a supertype, not an interface, not a parent in a hierarchy*, because a hierarchy invites the inference *"anything commentable is searchable"* that the kill row exists to prevent. `equivalent_to` plus `narrower_than` is a subsumption lattice; a reader who has one will compute over it. **Recorded, not taken.** If Phase 3's ingestion loop needs it, it arrives with the use case that forces it, as `value_set` did for CMS.

---

## 4. The read seam — `neighbors`

### 4.1 Signature and shape

```python
def neighbors(
    node: NodeRef,
    edge_families: Sequence[str] | None = None,
    depth: int = 1,
    *,
    namespace: str,
    direction: "both" | "out" | "in" = "both",
    include_retracted: bool = False,
) -> NeighborReport | Refusal: ...
```

```
NeighborReport:
    origin:            NodeRef
    depth_requested:   int
    depth_reached:     int                  # the deepest level at which a NEW edge was
                                            #   found. "New" is load-bearing: see below.
                                            #   A dead end is depth_reached < depth_requested
                                            #   with complete=True. Truncation is a SEPARATE
                                            #   signal - complete=False plus a why. §4.3
    direction:         str
    families_searched: tuple[str, ...]      # what was ACTUALLY consulted. §4.4
    edges:             tuple[NeighborEdge, ...]
    nodes:             tuple[NodeRef, ...]  # distinct endpoints reached; origin excluded
    known:             int                  # len(edges). A plain int, NOT int | None - see below
    complete:          bool                 # §4.3 — and it CAN be True. §4.4
    why_incomplete:    str | None
    warnings:          tuple[str, ...]

NeighborEdge:
    edge:           Edge
    at_depth:       int          # 1 = incident on the origin. §4.4 — not decoration
    reached:        NodeRef | None   # the node THIS edge newly reached. Below
    via_successor:  str | None   # ruling R38 — the reference this edge was actually
                                 #   FOUND under, when that is not the one the caller
                                 #   walked from. None = written under the very name
                                 #   asked for. `edge.src`/`edge.dst` still read what
                                 #   was written. §4.3 rule 14
```

**`depth_reached` counts levels that found something NEW, and the word is load-bearing.** Under the default `direction="both"`, the frontier at level 2 contains the node reached at level 1 — and that node is incident on the very edge the walk arrived on. A `depth_reached` computed from *"did the scan return any records"* therefore reports `depth_reached == depth_requested` on a genuine dead end, because the walk re-found its own arriving edge and counted that as progress. **[Observed]** in round 2 (§17): a one-edge graph walked to depth 2 reported `depth_reached=2`, and the probe written to test dead ends missed it because it hard-coded `direction="out"`, which structurally cannot re-find an incoming edge. **The dead-end rule of §4.3 was therefore true only for the one direction nobody defaults to.** Both directions are now exercised.

> **`edges` is ordered by `(at_depth, edge_id)`, and `reached` names the node each edge newly reached** — `None` for a self-loop and for a triangle's closing edge, which reaches nobody new. *(Both added by row 4b's third adversarial round, and §9.3's worked example is why. That example fills the Tenshen grounding bundle's `relations` slot from a depth-2 report — **the worked example for the reason the edge row exists** — and a reviewer implemented it the obvious way: compare each edge's endpoints against the ORIGIN. At depth 2 that is silently wrong, because the far end of a second-hop edge was never incident on the origin: `person#7` never appears, `task#77` appears twice, and there is no error, no warning and no `complete=False`. **Mechanism C, inside the example written to show a consumer how to avoid it.** Computing it correctly needs `edges` walked in discovery order against a growing visited set — an inference the walk can make once, exactly, and a consumer can only re-derive. The order is therefore a guarantee rather than an accident: a deterministic traversal order, **not a ranking** — §1's *"a set, not a ranked list"* is about relevance and stands. `C17-34`.)*

**Two corner cases, stated because they are reachable and were not** *(round 3)*. **A self-loop** (`src == dst`) counts in `known` and contributes **nothing** to `nodes`, because both its endpoints are the origin and `nodes` excludes the origin — so `known=1, nodes=()` is a correct report of one real edge, not an inconsistency. **`at_depth` is a property of the edge's discovery, not of a newly-reached node**: in a triangle `A→B, A→C, B→C` walked from `A`, the `B→C` edge is `at_depth=2` although both of its endpoints were reached at depth 1. Both are exercised in `edges_capability_probe.py`.

**`known` is a plain `int`, and `INTERFACE.md` §3 is why.** That section already settles the case: *"`ConsumerReport.known` and `Resolution.known` are plain `int` because both are lengths of lists this document has already materialised — there is nothing there to fail to count."* `NeighborReport.edges` is materialised in the report, so `known` is its length and a backend has nothing to decline. **`int | None` here would be a Rule-U field with no reachable `None`** — decoration shaped like honesty. *(It was `int | None` in the first draft; a round-1 reviewer reported being unable to produce the `None`, which is the right way to find a field that cannot happen.)* The adapter's own `EdgePage.known` (§7.1) **is** `int | None`, because a store genuinely may not be able to count without materialising.

`namespace` is **required and keyword-only**, and it names the namespace **the `edge_families` argument is resolved in** — *not* the origin's, which the origin carries itself (§2.1), and *not* a filter on results (§4.5). Making it required rather than defaulting to `"default"` is deliberate: UC3's whole subject is that `"default"` is a wrong answer nobody notices.

> **`direction` filters DIRECTED families only.** For a family whose `symmetric` is `True` there is no in and no out (§2.2), so the filter does not apply and both orientations are returned whatever the caller passed. For a directed family it filters as expected. A mixed query gets both behaviours in one report, per family — which is why this is a per-family rule rather than a per-call refusal. **[Observed]** in `edges_capability_probe.py`: six (origin, direction) combinations over one symmetric edge, all returning it; and a directed family still answering `out`→1, `in`→0.

> **`edge_families=None` searches every family the store can answer, in EVERY namespace — so `namespace` is a no-op in that call shape, and that is stated rather than left to be discovered.** The alternative, scoping the `None` case to the named namespace, was in the first draft, and **[Observed]** a round-1 reviewer reproduced its consequence in twenty lines: two families in two namespaces, both incident on one node, and each call found only one of them. **That is Cause C — the silent per-consumer drop this whole document is designed against (§12) — inside the one read call it offers, on the exact axis UC3 exists to stress.** It is not merely a scoping choice: it is the same failure the required `namespace` parameter was added to prevent, moved one level down. §4.5's reasoning settles it — `neighbors` reads a stored fact whose endpoints are fully named, so there is nothing to scope — and `families_searched` is what tells the caller what was actually consulted.

### 4.2 The depth cap is **2**, and it is R13's consequence rather than a separate decision

> **`depth` may be `1` or `2`. `depth >= 3` raises `ValueError`.**

`ValueError`, not `Refusal` — it is a caller error like `INTERFACE.md` §5.4's empty definition, and R3's closed vocabulary should not grow a value for a typo.

**Why a cap at all.** R13 rules that the façade does not page in v0, *because Rule K has no answer yet for what `known` means on a page.* An unpaged result must therefore be bounded by something else, and depth is the only bound available that a caller can reason about. Fan-out compounds: a node of degree *d* returns up to *d* edges at depth 1 and up to *d²* at depth 2. On beacon's `person_links` at founder scale that is tens; on UC3's 22.3M-row 311 dataset a naive depth-3 walk from a common node is a result nobody can hold. **The cap and R13 are one decision, and if R13 is revisited the cap should be revisited in the same change.**

**Why 2 and not 1.** Because 2 is the smallest cap that serves a traversal a shipped consumer already wants. Beacon's flagship query is *"who is blocking anything due this week?"* — `task --blocks--> task --stakeholder--> person`, two hops **[Observed, beacon spec §5.5 query 1]** — and `deadline_cluster_service` already walks the first hop by hand and stops **[Observed, beacon spec §2.7]**: *"it reaches the blocker task and goes no further… the hop it is missing is the one that turns 'what is blocking this' into 'who is blocking this'."* A cap of 1 ships a read seam that cannot answer the query the read seam was justified by.

**Why not 3.** Nothing in the three fixtures needs it. CMS's deepest chain is `citation → survey → facility`, which is 2. UC3's cross-agency joins are 1. The moment a real consumer needs 3, the cap moves *with that consumer's evidence* and with an answer for what bounds the result — which is Phase 3's paging decision (R13), not this row's.

**The cap is not a performance claim, and this is the sharpest limit in the document.** *The cap bounds hops. It does not bound degree, and degree is unbounded.* **[Observed 2026-08-29]**, on UC3's own pinned dataset: `erm2-nwe9` holds **22,294,072** rows, of which **9,738,128 carry `agency = NYPD`** — 44% on one value. The Phase 3 ingestion shape this row exists to unblock would naturally write `service_request --reported_to_agency--> agency`, and then **`neighbors(agency:NYPD, depth=1)` is ~9.7M edges in one unpaged call.** A single hop, on the fixture's own data, is already *a result nobody can hold* — so §4.2's argument above, which reasons about a naive depth-3 walk, was describing the second-worst case. Found in round 2 (§17) by a reviewer who went and counted.

**Two things follow, and both are specified rather than left open:**

1. **The registry exhausts the adapter's pages for a level.** `EdgeQuery.limit`/`after` and `EdgePage.next_after` exist (§7.1); a level assembled from one page of five would be silently partial, which is exactly what Rule K exists to prevent. So `neighbors` loops `find_edges` until `next_after` is `None`, per depth level. **[Observed]**: 300 edges on one node, assembled from 64-row pages, `known=300, complete=True`.
2. **The assembly bound is ON by default**, and hitting it is an *incomplete report with a `why`*, never a shorter one. **It counts DISTINCT edges** — see the two boxes below, both of which were round-3 findings. **[Observed]**: 2,000 edges on one node with a bound of 500 gives `known=500`, **`complete=False`**, and `why_incomplete` naming the bound. **This is not paging** — the caller gets no cursor and cannot ask for the next 500, because R13 says the façade does not page in v0 and this document does not quietly reverse that. It is a circuit breaker that tells the truth.

> **The bound counts distinct edges, and getting that wrong is worse than not having a bound.** **[Observed]** in round 3: the bound was compared against each *raw page*, and at depth ≥ 2 a frontier legitimately re-finds edges already counted at depth 1 — so a walk of **19 distinct edges under a bound of 20** stopped at depth 1, returned **15**, and reported `complete=False` with a `why` naming a bound **nothing had crossed**. Two failures in one: four real edges silently dropped, and a false claim in the one field §4.2 promises will tell the truth. The page is deduplicated against what the walk has already seen *before* the bound is consulted.

> **The bound is not opt-in, and that was a round-3 finding too.** An earlier draft said *"a deployment MAY configure"* one. **A circuit breaker nobody has to switch on is not a circuit breaker** — with none configured, the default behaviour of `neighbors` is to loop `find_edges` until the cursor is exhausted, which is precisely the unbounded materialisation R13 exists to prevent, on the 9.7M-degree node this section just measured. **A bound is in force by default; disabling it is a deliberate act** (`max_edges=None`), and a deployment that does so has chosen the unbounded fetch rather than inherited it.

**What it does not do, stated plainly:** a caller who needs all 9.7M neighbours cannot get them from this surface. **Q21** asks whether that is acceptable for Phase 3 or whether the façade must page after all — which is R13's question, re-opened by real data rather than by preference, and it is the supervisor's to answer.

### 4.3 Behaviour when uncertain

> **The rules of this section are numbered and each is exercised or tagged** — ruling **R31**, standing constraint 8, applied for the first time by row 4b. The `exercised by` column is held against the contract suite by [`check_spec_drift.py`](../tools/check_spec_drift.py): an id named here that no test claims is a failure, and a row with an empty cell is a failure. `prose-only:` is a legal answer with a reason attached, and there is one.

| # | Situation | Result | exercised by |
|---|---|---|---|
| 4.3-1 | The registry has no edge store | **`Refusal(reason="edge_store_absent")`**. Never an empty report — an empty `NeighborReport` reads as *"this node has no neighbours"*, which is Rule U's forbidden empty list in the one call that would be believed | `C17-01` |
| 4.3-2 | A named family in `edge_families` is not a registered `kind="edge"` entry | **`Refusal(reason="edge_family_unknown", detail={"families": [...]})`**. The whole call, not a partial answer: a caller that names a family and gets a report back is entitled to believe the family was searched, and a typo'd name returning a clean empty set is mechanism **C** committed by the read seam | `C17-14` |
| 4.3-3 | A named family exists but is **retired** | Not a refusal. It is searched (its edges were not deleted), and the report carries `warnings: ["edge_family_retired:<name>"]` | `C17-15` |
| 4.3-4 | `edge_families=None` | Every family the store can answer, **across every namespace** (§4.1). `families_searched` echoes exactly which, and `complete` is about *those* — §4.4 | `C17-13` |
| 4.3-5 | The **adapter** cannot count | `EdgePage.known=None`, never `0` — `PACKAGE.md` §3.4's uniform uncertainty rule. **`NeighborReport.known` is never `None`** (§4.1): the report materialises its edges, so its `known` is a length. *(This row said `known=None` about the report itself until round 3 — leftover prose from before §4.1's own correction, contradicting it two sections apart.)* | `C17-19`, `C17-22` |
| 4.3-6 | **The walk ran out of graph** — a leaf, a sink, a node with no edges at all | `depth_reached < depth_requested` **with `complete=True`** and no `why_incomplete`. This is the *common* case in real data and it is **not** an incomplete answer: the walk saw everything there was | `C17-17` |
| 4.3-7 | **The walk was cut short** — a scan bound, a store that timed out, a page it could not exhaust | `depth_reached < depth_requested` **with `complete=False`**, and `why_incomplete` names the bound. **Never a silently shallower answer** | `C17-18`, `C17-19` |
| 4.3-8 | `include_retracted=False` (the default) and a retracted edge was suppressed | `complete=False`, because a default that hides things is `list_types`' rule (`INTERFACE.md` §5.6) | `C17-20` |
| 4.3-9 | A named family in `edge_families` is registered in a **different** namespace from the one passed | `Refusal(reason="edge_family_unknown")`. Resolving names is `namespace`'s one job (§4.1) | `C17-14` |
| 4.3-10 | `node` is an `InstanceRef` whose type is not registered | Not an error (§2.7). The walk proceeds and the report carries `warnings: ["origin_type_unregistered:<ref>"]` | `C17-11` |
| 4.3-11 | The edge store is `transaction_scope="savepoint"` and this is a **read** | **Nothing is added.** `PACKAGE.md` §3.4 primitive 3, note 2: a read says nothing about durability in either direction, because the registry cannot know whether the host has committed | `C17-21` |
| 4.3-12 | **No `UnknownNode` exception**, and the paragraph below argues why `UnknownType`'s reasoning does not transpose | The honest form is a report with `edges: ()`, `known: 0` and a warning when the origin's type is unregistered | `C17-11` |
| 4.3-13 | An edge whose family is registered **nowhere** is returned by an `edge_families=None` walk, with `edge_family_unregistered:<namespace>:<name>` | *Added by row 4b, which implemented this section. There is deliberately no foreign key from an edge to its family (§2.7's argument, and §7.2 observes beacon's `work_links` has none either), so the case is reachable — and the spec did not say what the READ does with it. Dropping it is mechanism **C** in the read seam* | `C17-13` |
| 4.3-14 | The origin's type — or a frontier node's — is joined to another by a **merge**, or by a retirement with a `successor` | **The walk FOLLOWS the chain** *(ruling **R38**, row 4c)*. An edge endpoint reference resolves to *the identity it now belongs to*, not to *the reference that was written*, in both directions: a walk from the survivor finds the edges written against the absorbed name, and a walk from the absorbed name finds the survivor's, because `INTERFACE.md` §5.3 makes that redirect a guarantee. **Rule K comes with it:** every edge reached through a successor hop carries `via_successor` on its `NeighborEdge`, naming the reference it was found under, while `edge.src`/`edge.dst` still read what was written — so a caller can always tell a written reference from a followed one. `complete` stays about what was **searched**: nothing is hidden, so it is `True`, and the report still carries `endpoint_type_merged:<ref>` to say the identity spans more than one written name. The origin under a former name is still the origin and is excluded from `nodes`. *(Row 4b made the report honest about this gap and stopped there — deviation **D-4b-15**, **Q33** — because whether an edge written under a merged word is an edge of its survivor is a decision above that row. R38 is that decision, and it is what makes `merge_types` **safe on a store with edges in it**: without it a merge silently orphans every edge ever written against the merged-away name.)* | `C17-33`, `C17-44`, `C17-46` |
| 4.3-15 | The successor chain **cannot be followed to an end** — a cycle, a chain longer than the cap, or a backend that cannot page its retired rows | The walk **stops** and says so: `complete=False` with a `why` naming what stopped it, and it never claims to have resolved an identity it did not finish resolving. `C0-10`'s question — *can a broken backend make this loop?* — asked of chain-following, and *"it hangs"* is not an answer. A cycle is constructible: nothing in `INTERFACE.md` §5.9 forbids `retire(a, successor=b)` followed by `retire(b, successor=a)` | `C17-45` |

**No `UnknownNode` exception.** `INTERFACE.md` §5.1 raises `UnknownType` rather than returning an empty `ConsumerReport`, and the reasoning was that an empty report is false reassurance. It does not transpose: the registry **has no node store** (§1), so it cannot distinguish *a node with no edges* from *a node that does not exist*, and raising would require inventing a fact. The honest form is a report with `edges: ()`, `known: 0` and a `warnings` entry when the origin's type is unregistered. **This is a place where two rules of this project point opposite ways and the tie is broken by which one requires the registry to know something it does not.**

### 4.4 `complete` **can be `True`** — unlike the two carriers that never can, and the caveat that makes it honest

`ConsumerReport.complete` is *always* `false` because consumers are **registered, not discovered** — the registry cannot know about a code path nobody told it about. `Resolution.complete` is always `false` because near-misses are scored in one namespace. **Edges are different in kind from both: an edge is a stored row.** There is no edge that exists in the store and is invisible to a query over it. So when the store answered without truncation, `complete=True` is a true statement and Rule K should let it be said.

*(An earlier draft called this **"the first Rule-K carrier in this project that can be `True`"**. That was an overclaim and round 2 caught it: `TypeListing.complete` is already `True` for an unfiltered census — `registry.py`'s `list_types` computes `complete=bool(page.complete and not applied)`, and `list_types(namespace=None, include_retired=True, status=None)` is exactly the call `INTERFACE.md` §5.6 recommends for a true census. The comparison that holds is with the two carriers that are **always** `False`, and it is stated that way now.)*

**The caveat, and it is not small.** "Complete" is over `families_searched` and over the **edge store**, never over the host's relationships. Beacon has seventeen bespoke join tables plus three shapes of edge **[Observed, beacon spec §2.2]**; an adapter that maps three families and not the other fourteen answers `complete=True` about a graph that is four-fifths invisible. That is why `families_searched` is a required field of the report rather than an echo of the argument: **`complete=True` is only readable next to the list of what was searched**, exactly as ruling R12 requires a conformance verdict to be read next to its coverage line. A `NeighborReport` printed without `families_searched` is the same category of claim as a conformance run printed without its coverage — *"a completeness claim without its scope line is not a claim"*.

**`at_depth` is the second thing that keeps this honest, and it is `equivalent_to`'s problem specifically.** §3.1 makes `equivalent_to` symmetric and **not transitive**. A depth-2 walk from `dpr:borough` over `A≡B` and `B≡C` returns `dot:borough` — reachable, and **not asserted equivalent to the origin**. Without `at_depth` a caller renders three boroughs as one equivalence class, which is the transitive closure the family refused to license, manufactured by the read seam.

> **`neighbors` returns reachability. It never returns entailment.** A consumer that treats a depth-2 result as a depth-1 claim has made the inference itself, and the report gives it every means not to.

> **The rules of this section, numbered and each exercised or tagged** — ruling **R31**, standing constraint 8. Held against the contract suite by [`check_spec_drift.py`](../tools/check_spec_drift.py).

| # | rule | exercised by |
|---|---|---|
| 4.4-1 | `complete` **can** be `True`, unlike `ConsumerReport.complete` and `Resolution.complete`, because an edge is a stored row: there is no edge that exists in the store and is invisible to a query over it | `C17-22` |
| 4.4-2 | `complete` is over `families_searched` and over the **edge store**, never over the host's relationships — so `families_searched` is a required field of the report and not an echo of the argument (ruling R12's rule, taken rather than restated) | `C17-22`, `C18-06` |
| 4.4-3 | `at_depth` distinguishes reachability from entailment: a depth-2 walk over `A≡B` and `B≡C` returns `C`, **not asserted equivalent to `A`**, and without `at_depth` a caller renders three as one equivalence class | `C17-23`, `C18-05` |
| 4.4-4 | The comparison that holds is with the two carriers that are **always** `False`; `TypeListing.complete` is already `True` for an unfiltered census, so *"the first Rule-K carrier that can be True"* was an overclaim | `prose-only:` a correction to this document's own prose about a claim `C6-04` already binds on the type side. Nothing new to exercise |

### 4.5 What `neighbors` does across namespaces — and why it does not inherit contortion 8

`INTERFACE.md` §10b.1's contortion 8: `resolve_type` takes one `namespace`, scores against that namespace alone, and so *the second publisher of a word is never told the first exists.* The obvious fear is that `neighbors` inherits it.

**It does not, and the reason is structural rather than lucky.** `resolve_type` **searches** — it must decide *which* namespaces to score in, and any answer it gives is scoped by that choice. `neighbors` **reads** — both endpoints of every edge are fully named `(namespace, kind, name)` before the call starts, so there is no set to choose. `neighbors(dpr:borough, ["equivalent_to"])` returns the `oti_311` and `dot` types because the edges say so, not because a search reached into those namespaces.

Consequently:

- A `NeighborReport`'s `nodes` routinely span namespaces, and that is normal rather than exceptional.
- `namespace` on the call scopes **only** the resolution of `edge_families` names. It never filters results.
- **This does not close contortion 8.** Somebody still had to *write* the `equivalent_to` edge, and the publisher who never learned the word was taken never writes one. **R6's `search_namespaces` (row 3e) is the call that finds; `equivalent_to` is the record that the finding happened.** Recorded plainly so that "EDGES fixes contortion 8" is not read into this section — it fixes contortion **9**, and 8 is 3e's.

---

## 5. Provenance on edges

### 5.1 `EdgeProvenance` — a narrowing of `Provenance`, and the narrowing is the argument

```
EdgeProvenance:
    created_at:        datetime
    created_by_actor:  str                  # "user:sd", "ai:classifier", "seed", "import:socrata"
    created_by:        "seed"|"ai"|"user"|"derived"  # INTERFACE §2.1's, incl. R17
    confidence:        float | None         # None = nothing scored it. NOT 0.0 — Rule U
    evidence:          list[Evidence]       # INTERFACE §2.8, unchanged, incl. external_doc + Citation
    source_version:    str | None           # the SOURCE's own version. §5.3
    model_tier:        str | None           # ruling R20 -- see the paragraph below
    retracted_by:      str | None
    retracted_at:      datetime | None
    retract_reason:    str | None
    history:           list[ProvenanceEvent]        # append-only. INTERFACE §5.8
    history_why:       str | None           # why `history` is empty, when it is. Rule U
```

**Why not `Provenance` verbatim.** `Provenance` carries `proposed_by`, `approved_by`, `approved_at` and `model_tier`, and `INTERFACE.md` §2.4 makes a rule of one of them: *"`approved_by` is never null on an `active` type… a registry that leaves the field blank invites a reader to assume a human signed off."* §2.6 above establishes that edge **instances** have no approval loop. Carrying `approved_by` on an edge therefore forces one of two bad answers on every single edge ever written: `None`, which breaks the §2.4 rule the field exists for, or a manufactured `"auto:…"` that asserts an approval nobody performed. **A field whose only honest value is a lie should not be on the shape.** Narrowing is the honest move, and it is the same move `INTERFACE.md` §5.2 makes when it gives `PredicateEntry` its own shape rather than reusing `TypeEntry`.

**`model_tier` is present, by ruling R20 — and this paragraph argued the opposite until row 4b's second adversarial round.** Q15 below asked whether `EdgeProvenance` should carry it; **R20 answered yes on 2026-08-29, before row 4b started**, and row 4b added the field, threaded it through `add_edge` and round-tripped it (`C17-02`). The shape above and this paragraph both went on denying it, while §14's own Q15 row five hundred lines below printed *"`model_tier`: yes"* — the document contradicting the code, the ruling, and itself, in three places at once. **The hole that allowed it is closed rather than patched**: `check_spec_drift.py` now holds this document's printed shapes against `open_ontology/edges.py`, the way it has held `INTERFACE.md`'s against `types.py` since row 3c and `PACKAGE.md`'s since row 3d. §5.1 was the last printed shape in this repository that nothing checked, and it is the one that drifted. The argument that stood here is kept, because it is why the field matters: `INTERFACE.md` §2.7 makes tier a product parameter because a cheap tier inverted the CMS severity scale silently. Beacon's `infer_person_relationships` classifies person pairs with **Haiku** and auto-applies at ≥0.7 **[Observed, beacon spec §2.5]** — an AI-written edge from a named cheap tier, which is 0.5's exact shape one level down. The tier was recoverable from `created_by_actor` only by convention (`"ai:haiku_classifier"`), which is not a field. **R20 takes the field and declines the gate**: a tier gate on a weekly batch job is a product decision about beacon's behaviour rather than a storage shape, and it is relayed to the beacon program as an observation, not as a requirement.

**`confidence` is `float | None` and `None` is not `0.0`.** Beacon types it `Float` nullable on both `WorkLink` and `PersonLink` **[Observed]**, and `interview_service` selects rows *"with a null `relationship_type` or confidence below 0.7"* — so null confidence is a live, meaningful state in the one host this must sit over. Coercing it to `0.0` would turn *"nothing scored this"* into *"scored zero"*, which is `INTERFACE.md` §5.3's `confidence: None ≠ 0.0` rule verbatim.

### 5.2 Append-only, and what a correction is — `amend_edge`, ruling **R37**

`INTERFACE.md` §5.8: *"`history` is append-only: a correction is a new `ProvenanceEvent`, never an edit."* Unchanged for edges, with one addition that the shape forces.

`PACKAGE.md` §3.3's `EventRecord` has `kind`, `name` and `proposal_id` and **no slot for an edge**. So edge events have nowhere to go in the existing event store. **The amendment is one nullable field:**

```python
@dataclass(frozen=True)
class EventRecord:
    ...
    edge_id: str | None = None      # the edge this concerns, if any. EDGES §5.2
```

with three new `event` values — `edge_added`, `edge_retracted`, `edge_amended` — and the same rule as everything else in that vocabulary: the adapter **stores** the string and never judges the transition (`PACKAGE.md` §3.1).

**Corrections in practice, and the call that makes them** *(ruling **R37**, row 4c)*. Changing an edge's `confidence` after a re-classification is a new `edge_amended` event carrying the old and new values; it is not an edit of the first event, and the first event's `created_by_actor` stays whatever it was. Beacon's weekly job re-running over the same pair is exactly this case, and until row 4c it had no trail at all — because **v0 had no amend call**. `edge_amended` was a vocabulary value nothing wrote, this section narrated it as landed behaviour, and row 4b recorded that as deviation **D-4b-13** and asked **Q32**: give edges an amend path, or delete the example.

```python
def amend_edge(
    edge_id: str,
    reason: str,                              # REQUIRED, non-empty
    *,
    amended_by: str,
    confidence: float | None = UNCHANGED,
    attributes: dict | None = UNCHANGED,
    model_tier: str | None = UNCHANGED,
    source_version: str | None = UNCHANGED,
    evidence: list[Evidence] = UNCHANGED,
) -> Edge | Refusal: ...
```

**`UNCHANGED` is a sentinel and not decoration.** §5.1 makes the point for the field that matters most: `confidence` is `float | None` and `None` is *"nothing scored it"*, never `0.0`. A default of `None` could not distinguish *leave it alone* from *a re-classification decided nothing scores this any more*, and the second is a correction beacon's `interview_service` selects on.

> **R37's condition was a design test — *take the amend path unless it is a second write path in disguise* — and that is not a rhetorical caution.** The `ROADMAP.md` kill row's **third** trip (`05b8e04`) is precisely that shape: `retire(successor=)` reached `merge_types`' outcome carrying none of `merge_types`' guards. The test passed on three properties, and all three are **structural** rather than promised. `C17-42` asserts them, the first of them by reading the signature.

1. **`family`, `src` and `dst` are not parameters.** An amend cannot move an endpoint, change a family, or reify anything, so §2.4.1's declaration-time and write-time checks have nothing to be talked around. Re-pointing an edge is `retract_edge` followed by `add_edge` — which §3.2 already names as the shape of re-assertion: *a retracted edge is no claim; re-asserting it is a new edge whose provenance cites the retracted one.*
2. **`attributes` goes back through §2.5's payload validation on exactly `add_edge`'s terms**, and `attr_schema_version` is re-stamped with the version in force at the amendment. An amend that skipped it would be *a guard written for one call over a fact that more than one call can change*, which is the third trip's own diagnosis, one row later.
3. **`status` is not a parameter, and a retracted edge is refused `already_decided`.** A retracted edge is no claim; amending one asserts something about a claim that was withdrawn, and un-retracting through the amend door is `retract_edge`'s guard being walked around.

**It is REFUSED when the event cannot be recorded, and that is the one place it does not follow `retract_edge`.** §2.6 argues retraction past `PACKAGE.md` §3.6 because *"the record **is** the row"* — `status`, `retracted_by`, `retracted_at` and the reason are columns on the edge itself, so an unrecordable retraction does not exist. **That argument does not transpose.** There is no column holding an edge's *prior* confidence, so on `stores_edge_events=False` an amendment erases the old value with no record anywhere that it ever held one — which is §3.6's rule verbatim, *a destructive override that cannot be recorded is refused*, and it is `reinstate`'s shape exactly (§3.6's own box: `reinstate` clears fields off the live row, which makes its event the only record).

So `amend_edge` returns `Refusal(reason="cannot_record_override")` on `stores_edge_events=False` **or** `stores_events=False` — both, per the lesson `edge_provenance` paid for, because `stores_events` gates the same `append_event` primitive and nothing ties the two declarations together. **No new `Refusal.reason` is minted:** this is the fourth caller of an argued rule rather than an exemption from it. The available path on such a store is `retract_edge` + `add_edge`, which §3.2 already blesses and which that store *can* record, because the record is the row. `C17-43` asserts both halves on one store — the amendment refused, the retraction still succeeding and still warning — because the two are only defensible together.

**Two caller errors raise rather than refuse**, on §5.5's rule for a closed vocabulary: an empty `reason`, and an amendment that names no field to change. The second is not pedantry — an `edge_amended` event recording no amendment is a trail entry asserting a correction nobody made, and a call that quietly did nothing is the shape ruling **R4** forbade for `register_consumer`.

> **The rules of this section, numbered and each exercised or tagged** — ruling **R31**, standing constraint 8. Held against the contract suite by [`check_spec_drift.py`](../tools/check_spec_drift.py).

| # | rule | exercised by |
|---|---|---|
| 5.2-1 | A correction is a new `edge_amended` event carrying the old and new values; the row carries the new, the history carries both, and the first event is not edited | `C17-41` |
| 5.2-2 | `family`, `src`, `dst` and `status` are not amendable — an amend is not a second write path, and the guarantee is the signature rather than a promise | `C17-42` |
| 5.2-3 | An amended `attributes` is validated on `add_edge`'s exact terms (§2.5), and a refused amendment appends no event | `C17-42` |
| 5.2-4 | Amending a retracted edge is refused `already_decided` | `C17-42` |
| 5.2-5 | An amendment that cannot be recorded is refused `cannot_record_override`, while a retraction on the same store still succeeds and warns — §2.6's *"the record is the row"* covers retraction and does not transpose | `C17-43` |
| 5.2-6 | An empty `reason`, or an amendment naming no field, raises `ValueError` | `C17-42` |
| 5.2-7 | `EventRecord.edge_id` is the one shape amendment this section makes, and the adapter stores the `event` string without judging the transition | `C17-26` |

### 5.3 `source_version` — taken here, and the asymmetry recorded

`INTERFACE.md` §10b.5, contortion 12: a type derived from a 2017 snapshot and one derived from a daily feed record identically, because `Provenance.created_at` is when *we* wrote the row. The one-line fix — `source_version: str | None` — was collected for v1 and not taken.

**It is taken here**, on `EdgeProvenance`, because a cross-agency edge is *entirely* a claim about two source snapshots. `dpr:tree:1234 --concerns--> oti_311:service_request:5678` asserted from a 2017-10-04 tree census and a 311 feed updated 2026-08-28 **[Observed, dataset `data_updated_at` values]** is a different claim from the same edge over two current feeds, and the difference is nine years of trees.

**The asymmetry this creates is recorded rather than smoothed:** `EdgeProvenance` has `source_version` and `Provenance` does not. Two shapes, one concept, one of them missing the field — which is drift of the kind this repo has caught six times. **Q16**: should `Provenance` gain `source_version` in row 3e, closing it? The recommendation is yes; it is additive, defaults `None`, and 3e is already amending that shape for R6/R10/R11.

---

## 6. Capability flags for the edge store

In `PACKAGE.md` §3.2's style: every `False` flag carries a sentence in `Capabilities.why`, surfaced verbatim wherever a result would otherwise imply a fact. **Four flags and three declarations**, added to the existing `Capabilities` — and the distinction is the one §3.2 draws for `transaction_scope` and `attribute_projections`: a flag is something a backend *declines*; a declaration says *how* it does something it can do.

```python
    stores_edges:              bool     # the store holds edges at all
    stores_edge_events:        bool     # append_event with an edge_id is durable
    indexes_edges_by_family:   bool     # a family-filtered neighbour query need not scan the node's edges
    stores_edge_attributes:    bool     # an arbitrary payload dict survives a round trip
    edge_transaction_scope: Literal["owned", "savepoint"] = "owned"    # R5, §6.2
    edge_attribute_projections: frozenset[str] = frozenset()           # U3's shape, §6.3
    edge_store_shares_connection: bool = True                          # §6.2's premise
```

> **The third declaration was missing from this block until row 4b's second adversarial round**, while `PACKAGE.md` §3.2 printed it correctly and the code has carried it since that row's first commit. It is the **premise** of §6.2's binding rule and not decoration: when the edge store and the type store are the same store on one connection — which both reference backends declare — the two scopes MUST be equal; when they are genuinely two connections they may differ, and **G2 across the seam is gone**. A rule whose premise is unstated is a rule an adapter author can miss by reading. `Capabilities.scope_conflict()` returns the sentence or `None`, and `C17-25` binds it.

| Flag | `False` means | `why` example | What the registry does |
|---|---|---|---|
| `stores_edges` | there is no edge store behind this adapter | *"this backend is a type registry only; no table holds relationships"* | **every** edge call returns `Refusal(reason="edge_store_absent")`. Never an empty report — §4.3 |
| `stores_edge_events` | an edge event cannot be persisted | *"`work_links` has no event table and beacon owns the schema"* | `retract_edge` **succeeds** and warns `retracted_without_event_trail:<why>` (§2.6); `provenance(edge).history == []` with the `why`; **`amend_edge` REFUSES `cannot_record_override`** (§5.2, ruling R37) — the record is the row for a retraction and there is no column for a prior confidence |
| `indexes_edges_by_family` | a family filter costs a scan of the node's edges | *"`work_links.relationship` is free text with no index"* | correctness is unchanged — the registry filters above the store. But a scan may hit a bound, and then `depth_reached < depth_requested`, `complete=False`, `why_incomplete` = this sentence |
| `stores_edge_attributes` | an arbitrary payload key does not round-trip | *"`work_links` has `description` and `confidence` as columns and no JSON blob"* | `Edge.attributes` returns **only** the keys in `edge_attribute_projections`. **No warning value is minted for this**, deliberately: `PACKAGE.md` §3.4 primitive 4's mechanism is that the *returned record* is the signal — a key that did not round-trip is absent from it, and `Capabilities.why` says why — and the type side has no warning for it either. Adding one here would make the edge path and the type path report the same fact two different ways |

**Two flags are NOT added, deliberately.** There is no `enforces_unique_edge` and no `edges_transactional`.

**No uniqueness flag, because there is nothing for one to declare.** An edge's key is `edge_id`, **generated above the store** — the same rule `PACKAGE.md` §4.2 already applies to `proposal_id` and `event_id`, neither of which has a capability flag either. A key the registry mints is unique by construction, so a flag would assert nothing. *(An earlier draft reached this conclusion by citing `PACKAGE.md` §3.5's **G1**; round 2 pointed out that G1 is defined narrowly as uniqueness of `(namespace, kind, name)` **in the type store** and does not literally bind an edge table. The conclusion stands on §4.2's precedent alone, which is where it should have stood.)* **There is deliberately no uniqueness constraint on `(family, src, dst)`** — see §6.1.

**No transactionality flag, because `transactional` is already REQUIRED `True` for a conformant adapter** (`PACKAGE.md` §3.5) and that requirement does not fragment by table. What *does* vary is who commits, and that is `edge_transaction_scope` (§6.2).

### 6.1 Why duplicate edges are permitted, and what that costs

Two `blocks` edges between the same pair, written by a human in March and by the classifier in August, are **two facts with different provenance**, not one fact written twice. A uniqueness constraint on `(family, src, dst)` would force the second write to either fail or overwrite the first — and overwriting is an edit of a provenance-bearing record, which `INTERFACE.md` §5.8 forbids.

**The cost, stated:** `neighbors` may return the same pair twice, `known` counts edges rather than distinct neighbours, and a caller that wants distinct nodes reads `NeighborReport.nodes` (which *is* deduplicated) rather than counting `edges`. **[Observed]** beacon's `work_links` has no unique constraint on its endpoint columns either, so this matches the one host that exists; that is corroboration, not the reason.

### 6.2 `edge_transaction_scope` — R5, and the rule that stops it lying

Ruling **R5** gives `transaction_scope: "owned" | "savepoint"`. The edge store may be a different store from the type store (a host-owned edge table beside a package-owned registry), so it gets its own declaration — with one binding rule:

> **When the edge store and the type store share a connection, `edge_transaction_scope` MUST equal `transaction_scope`. A `Capabilities` that declares two different scopes on one connection is non-conformant.**

Otherwise the adapter is claiming that half its writes are the host's to commit and half are its own, on one transaction, which is not a thing that can be true. When they are genuinely two connections, the two may differ, and then **the atomicity of a write that touches both is gone** — approving an `equivalent_to` family and writing the first edge are no longer one transaction. That is a real limit and it is stated rather than papered over: **a two-connection deployment does not get G2 across the seam**, and the adapter says so in `why["edge_transaction_scope"]`.

Under `"savepoint"`, an edge write result carries `not_durable_until_host_commits:<why>` — `INTERFACE.md` §5.4's existing warning value, unchanged, on one more carrier. **No new warning value is needed**, and the row-3d lesson applies verbatim: it is stamped at the *write* call sites (`add_edge`, `retract_edge`) and **not** on `neighbors`, because a signal that never turns off is noise.

> **Each write call site stamps it ITSELF, and the word *itself* is the finding.** **[Observed]** in round 3: `retract_edge` carried the warning forward from the edge's prior state instead of applying it, so **retracting an edge the host had already committed came back with no warning at all** — a write over a borrowed connection that looked exactly as durable as one over an owned connection. That is `PACKAGE.md` §3.4 primitive 3 note 2's own recorded bug class — *"`register_consumer` and `reject` construct their results directly and skipped the stamp"* — reproduced one layer up, in the call this section names by name. Every write checks `edge_transaction_scope` on its own behalf.

### 6.3 `edge_attribute_projections` — beacon finding U3's shape, reused

`stores_edge_attributes` is binary and the same argument that split `stores_attributes` (U3, `PACKAGE.md` §5.7) splits this one: `task_stakeholders.role` and `work_links.description` are **real typed columns** that round-trip perfectly on a backend that stores no arbitrary key at all. `True` would silently lose arbitrary keys; `False` would disclaim two the backend owns.

So the declaration is the same shape, with the same five rules and the same one collision — a projected key written as `None` is indistinguishable from never written, because the column is `NULL` either way, and writing a sentinel into a column the **host** owns is what `owns_schema=False` exists to prevent. Nothing new is invented here; §5.7 is cited and applies.

---

## 7. Adapter primitives, and how a host-owned table becomes an edge backend

### 7.1 Three primitives — 16, 17, 18

The brief allows up to eight. It takes three, and that is the strongest evidence that §2.3's decision (a family is a `TypeEntry`) was right: families need **no** new primitive, because `put_type` / `get_type` / `find_types` already serve them.

```python
@dataclass(frozen=True)
class EdgeRecord:
    edge_id:      str
    namespace:    str               # the FAMILY's namespace
    family:       str
    src_namespace: str; src_kind: str; src_name: str; src_instance_id: str | None
    dst_namespace: str; dst_kind: str; dst_name: str; dst_instance_id: str | None
    attributes:   dict              # opaque to the adapter. §2.5
    attr_schema_version: int | None
    provenance:   dict              # the whole EdgeProvenance, JSON-encoded. Opaque
    status:       str               # "active" | "retracted" — STORED, never judged
    warnings:     tuple[str, ...]
    created_at:   datetime
    updated_at:   datetime
    # The retraction tombstone, columns for the same reason TypeRecord's is:
    # a backend with stores_edge_events=False still has to answer "why is this retracted?"
    retract_reason: str | None
    retracted_by:   str | None
    retracted_at:   datetime | None

@dataclass(frozen=True)
class EdgeQuery:
    namespace:  str | None = None                   # the family's namespace. None = any
    families:   tuple[str, ...] | None = None
    # The frontier: one call serves a whole depth-2 level rather than N calls. §4.2
    incident_to: tuple[tuple[str, str, str, str | None], ...] | None = None
                                                    # (namespace, kind, name, instance_id)
    direction:  str = "both"                        # "both" | "out" | "in"
    include_retracted: bool = False
    edge_ids:   tuple[str, ...] | None = None
    limit:      int | None = None                   # the ADAPTER pages. R13: the façade does not
    after:      str | None = None                   # opaque cursor; ordering is (created_at, edge_id)

@dataclass(frozen=True)
class EdgePage:
    records:    tuple[EdgeRecord, ...]
    known:      int | None          # None = the backend cannot count. NOT 0. Rule U
    complete:   bool
    why_incomplete: str | None
    next_after: str | None
```

**16. `put_edge(rec: EdgeRecord, *, expect_absent: bool = False) -> EdgeRecord`**
Upsert on `edge_id`. Writes `status`, `retract_reason`, `retracted_by`, `retracted_at` **as given** and validates no transition (`PACKAGE.md` §3.1). Returns the record as stored, so a backend that could not store `attributes` returns them reduced to its projections and the registry can tell.
**Uncertainty:** `stores_edges=False` ⇒ raises `NotSupported`; the registry checks the capability first and never calls this, surfacing `Refusal(reason="edge_store_absent")`. It does not pretend to store and lose.

**17. `get_edge(edge_id: str) -> EdgeRecord | None`**
`None` means *absent*, which is a fact — the adapter always knows whether a key exists.

**18. `find_edges(q: EdgeQuery) -> EdgePage`**
The one call behind `neighbors`. **Traversal is not pushed into the adapter**: the registry issues one `find_edges` per depth level, with the whole frontier in `incident_to`. That is a deliberate §3.1 boundary — an adapter that knew about `depth` would know about `NeighborReport`, and `C0-04`'s source-inspection test would have a new identifier to police.
**The registry exhausts this call's pages for each depth level** (§4.2): it loops on `EdgePage.next_after` until the level is assembled, or until a configured assembly bound stops it — and a bound that stops it makes the *report* incomplete with a `why`, never shorter and silent. `EdgeQuery.limit`/`after` are therefore used by the registry internally, which is not a contradiction of **R13**: R13 is about the *façade* exposing paging to a caller, and `neighbors` exposes none.

**Uncertainty:** the general rule is `find_types`': a filter the backend cannot apply returns `complete=False` with a `why`, **never** a filtered-looking empty page. **One case deviates, and the deviation is deliberate rather than an inconsistency.** `PACKAGE.md` §3.4 primitive 6 handles `find_types(predicate=…)` on `indexes_membership=False` by returning an **empty** page with `known=None, complete=False`. Here, `find_edges` with `q.families` set on `indexes_edges_by_family=False` returns the node's edges **unfiltered, with `complete=True`**, and the registry filters above.

**Why the two differ.** The type case has no bound: the alternative to an index is scanning the whole type table, so the honest answer is *"I cannot answer this"*. The edge case is already bounded by `q.incident_to` — the frontier is a handful of nodes — so the backend genuinely **can** return a complete answer to a slightly wider question, and the registry narrows it. The page it returns *is* complete for what it was asked. **A backend that could not even do that returns `complete=False` with the `why`, and the general rule applies again.**

> **The boundary is exercised, not only asserted** *(round 3)*. This section calls the three-primitive count *"the strongest evidence that §2.3's decision was right"*, and `PACKAGE.md` §3.1 makes the boundary a **testable** rule — `C0-04` inspects the source and fails if `adapter.py` so much as names `Refusal`. **[Observed]** the probe kit's own `EdgeStore` was storing and returning `Edge` — the rich façade object with structured `NodeRef`s and computed warnings — so the boundary this section leans on was asserted here and contradicted by the one runnable artifact. It now stores `EdgeRecord`, takes an `EdgeQuery`, returns an `EdgePage`, and `assert_adapter_boundary()` checks it by source inspection the way `C0-04` checks the real one. *(The rewrite immediately paid: writing this document's own `EventRecord` amendment into `adapter.py` tripped `C0-04` for a **comment** mentioning the forbidden identifier. The rule is enforced, not decorative.)*

**No fourth primitive for retraction, and no fifth for counting.** Retraction is `put_edge` with a changed `status`; counting is `EdgePage.known`. Both were considered and dropped, because a primitive that only exists to express a policy transition is a policy inside the adapter.

**One amendment to an existing shape:** `EventRecord.edge_id: str | None = None` (§5.2). Additive, defaulted, and it costs the reference backends one nullable column. **[Landed in this change]** — in `PACKAGE.md` §3.3 *and* in `open_ontology/adapter.py`, together with the three new `event` values. *(Round 3 found both sentences claiming an amendment that had reached neither file. `check_spec_drift.py` could not catch it: PACKAGE.md and the code agreed with each other on the old shape, so a third document asserting a change nobody made was invisible to a two-way diff. Recorded as a named limit of that checker.)*

### 7.2 A host-owned table as an edge backend — `work_links`

**[Observed 2026-08-29, read-only** from `C:\Users\steph\projects\beacon\src\beacon\models\work_link.py`. Nothing in beacon was edited.**]**

```
work_links
    id                 int        PK
    user_id            int        NULL, no FK
    from_type          String(20) NOT NULL, no FK        # "task, project" is a COMMENT
    from_id            int        NOT NULL, no FK
    to_type            String(20) NOT NULL, no FK
    to_id              int        NOT NULL, no FK
    relationship_type  String(100) NOT NULL default "related_to"   # DB column name: `relationship`
    description        Text       NULL
    confidence         Float      NULL
    created_by         String(20) NOT NULL default "user"          # user | ai | interview
    created_at         DateTime   NOT NULL server_default now()
```

| `EdgeRecord` field | From | Verdict |
|---|---|---|
| `edge_id` | `str(id)` | ✅ |
| `namespace`, `family` | `"default"` constant; `relationship_type` | ✅ — and the family is **advisory**: no FK to `work_link_types`, so `edge_family_unknown` cannot be enforced by the store. The registry must check it. **[Observed]** beacon's own doc calls this out: *"the registry is advisory rather than enforced"* |
| `src_*`, `dst_*` | `("default", "entity", from_type, str(from_id))` | ✅ with **contortion E4** — `from_id` is `Integer`, `InstanceRef.id` is `str`; the adapter casts both ways |
| `attributes` | `{"description": …}` via `edge_attribute_projections={"description"}` | ✅ on that one key; any other key has nowhere to go, `stores_edge_attributes=False` + `why` |
| `provenance` | `created_at`, `created_by`, `confidence` project onto columns; everything else has no home | **contortion E1** |
| `status` | no column | **contortion E2** — one additive column |
| `warnings`, `attr_schema_version` | no column | `()` / `None`, honest |
| `retract_*` | no columns | **contortion E2** — with `status`, three columns |

**Verdict: `work_links` serves as an edge backend after a four-column additive migration** (`status`, `retract_reason`, `retracted_by`, `retracted_at`) **and a three-column projection** (`description`, `confidence`, `created_by`). One `ALTER TABLE`, one table, no rewrite — the same shape and the same size as `PACKAGE.md` §7.3's B3 verdict for `work_link_types`. It is not zero.

The contortions are enumerated with the rest in §9.4, including the two the brief names specifically: `user_id` nullable, and the cross-workspace question.

**The `user_id` question is recorded and NOT solved.** `work_links.user_id` is nullable with no FK, so an edge is not always owned by a user **[Observed, beacon spec §2.5]**, and `work_links` has no `workspace` column at all **[Observed, beacon spec §10.6 cost 7]**. The edge model has no tenancy field, and **the tempting move — map `user_id` or `workspace` onto `Edge.namespace` — is refused.** `namespace` scopes a *vocabulary* (whose word is this?), not a *tenant* (whose data is this?). Mapping tenancy onto it would give every user their own `blocks` family, which is mechanism 4 manufactured by this spec on data that has no collision in it. **So: an adapter over `work_links` either filters by `user_id` outside the protocol or exposes rows across users, and this document does not choose.** That is beacon's workspace rule to make; recorded as contortion **E3** and relayed as a finding, not solved here.

---

## 8. Consumers of edges — yes, and no new mechanism

**Does `consumers(type)` extend to edge families? Yes — because a family is a `TypeEntry`, and `consumers` already takes a type.** The interesting part is the mechanism-C argument for why it matters, which is not hypothetical.

**[Observed, beacon spec §2.7 and §10.4]** `deadline_cluster_service` — live for every user since 2026-07-06 — walks `hard-deadline task → work_links[blocks] → blocker task` to build decision cards. The family name `blocks` is in its code. Meanwhile `work_link_types` *"is extended by the AI classifier when it is confident none of the existing types fit"* **[Observed, beacon spec §2.2]**. So:

> A classifier proposes `waiting_on`, it is auto-approved, edges start being written with it — and the one shipped producer that consumes edges keeps walking `blocks` and never sees them. The clusters get quietly less complete. Nothing errors.

That is **finding 0.1's Cause C exactly**, with an AI classifier as the producer and a scheduled job as the consumer, on a live system. `INTERFACE.md` §5.1 exists for it and needs no change to cover it.

**The mechanism, concretely.** A consumer of edges registers the way any consumer does — its `gate` is a predicate name, and the predicate's extent is the set of families it traverses:

```python
propose_type(name="deadline_traversable", kind="predicate",
             definition="Edge families deadline_cluster_service walks when building clusters.")
# blocks: TypeEntry(kind="edge", predicates=["deadline_traversable"])

register_consumer(Consumer(id="deadline_cluster_service.build",
                           gate="deadline_traversable", on_unknown="drop",
                           locator="src/beacon/services/deadline_cluster_service.py:_walk"))

consumers("waiting_on")     # the new family
# -> would_drop=[deadline_cluster_service.build], known=1, complete=False
```

The report says the true thing: *this producer will silently drop the new family.* `PredicateEntry.extent` for `deadline_traversable` is *"the families this producer traverses"* — the same shape as an allowlist, which is `INTERFACE.md` §2.3's *"single most load-bearing idea"* holding one level over.

**What does NOT extend, recorded.** A consumer that gates on edges by **endpoint kind** rather than by family — *"I traverse any edge whose `dst` is a `person`"* — has no representation. `Consumer.gate` is a predicate name over types, and "any family whose `endpoint_kinds.dst` includes `entity:person`" is a query over family *attributes*, which the registry does not read (`INTERFACE.md` §2.1). This is the **same shape** as contortion 11 (a consumer that gates on *values*), one level along, and it gets the same treatment: recorded, not fixed, no gate vocabulary invented. **Q17.**

**And one warning is added**, by the same reasoning that made ruling R8 add `gate_unregistered`: when `consumers(type)` is called on a `kind="edge"` entry and **no predicate's extent contains any edge family at all**, the report carries `warnings: ["no_edge_gate_registered"]`. Without it, a system where nobody has registered an edge-traversing consumer returns `would_drop: []` for every new family, which reads as *"nothing will drop this"* — and the truth is *"nobody has told us what traverses edges"*. Rule U: only emitted when the underlying lookup came back `complete`, exactly as `gate_unregistered` is (`C11-05`'s rule).

---

## 9. Design test 1 — UC1 Tenshen: `WorkLink`, `PersonLink`, and one payload-carrying join table

**A design *test*, not a design *input*** (`ROADMAP.md`, rule of the ordering). Read **read-only** on 2026-08-29 from `C:\Users\steph\projects\beacon`. **Nothing in beacon was edited.** **[Observed]** unless marked.

**One citation correction, matter-of-factly:** the brief asks for `neighbors` to be walked over *"§5.3's three shipped traversals"*. Beacon spec §5.3 is four *design choices*, not traversals; the three **shipped** read seams are enumerated in **§2.7** — `entity_touchpoint_service`, `view_query_service` and `deadline_cluster_service`. §9.3 walks those three.

### 9.1 Expected outcomes — **stated before the walk-through**

Per `USE-CASES.md`'s protocol, and committed in its own commit ahead of the results.

| # | Prediction | Expected |
|---|---|---|
| **T1.1** | `work_link_types` rows become `kind="edge"` families; `work_links` rows become their edges | **PASS.** `PACKAGE.md` §7.1 already ruled the rows `kind="edge"`; §2.4's `symmetric`/`inverse_label` are `is_symmetric`/`inverse_label` renamed. `level="instance"` and `endpoint_kinds` are new and have no column |
| **T1.2** | `PersonLink` becomes a family per `relationship_type` value | **PREDICTED FAILURE.** `PersonLink.relationship_type` is **nullable** and there is no `person_link_types` registry — the labels are free text in a comment (`colleague, manager, direct_report, client_contact, vendor_contact, partner, mentor, other`). `Edge.family` is required. A null-family row has no honest mapping: skipping it is a silent drop by the adapter, and inventing a family is a fact the data does not carry |
| **T1.3** | `task_stakeholders` — the payload-carrying join table — becomes a family with a `payload_schema` | **PREDICTED PARTIAL.** The family expresses; the payload (`role`, and a NOT-NULL-no-default `source`) round-trips only through `edge_attribute_projections`, **unvalidated**, because `payload_schema` is inert until **R10** lands in row 3e |
| **T1.4** | `source`'s four values (`user \| auto_extract \| intake_auto \| legacy`) land in `attributes`, **not** in `EdgeProvenance.created_by` | **PASS expected, and the prediction is that it is tempting and wrong.** `source` looks like provenance and is payload: beacon's connect-suggestion gate *counts `'user'` only*, so it is a business signal on the edge, not a statement about who wrote the row |
| **T1.5** | `EdgeProvenance.created_by` has a value for beacon's `interview` | **PREDICTED CONTORTION.** Both `WorkLink` and `PersonLink` type `created_by` as `user \| ai \| interview`; `INTERFACE.md` §2.1's vocabulary is `seed \| ai \| user`. Expect the distinction to survive only in `created_by_actor` |
| **T1.6** | `neighbors(task:X, ["blocks"], depth=1)` reproduces `deadline_cluster_service`'s walk | **PASS** |
| **T1.7** | `neighbors(task:X, ["blocks", "task_stakeholder"], depth=2)` answers beacon's flagship query — *"who is blocking anything due this week?"* | **PASS expected**, and this is the hop §2.7 says is missing: *"the one that turns 'what is blocking this' into 'who is blocking this'"*. It is the whole justification for a cap of 2 rather than 1 |
| **T1.8** | `entity_touchpoint_service` (Org/Thing → tasks, projects, people) expresses as four families at depth 2 | **PASS on shape, CONTORTION on payload** — `task_organizations` / `project_organizations` / `task_things` / `project_things` each carry `role` |
| **T1.9** | `view_query_service`'s Shape-B mention substrate expresses as an edge family | **PREDICTED FAILURE.** A mention's far end is `(source_table, record_id)` — a **row in a table** (`task_notes`, `project_notes`, `meeting_notes`, `open_loops`), not an instance of a registered entity. `endpoint_kinds` cannot be satisfied and cannot be checked |
| **T1.10** | `endpoint_kind_mismatch` can fire on beacon today | **PREDICTED NO.** It fires only when the endpoint's type is registered, and beacon's entity-type vocabulary *disagrees with itself* across seven live definitions. Expect the spec to arrive independently at beacon's own §10.4 conclusion — **Slice 0 is a hard prerequisite** — which is corroboration, not a design input |
| **T1.11** | A `NeighborReport` fills the grounding bundle's `relations` slot | **PREDICTED LOSSY.** The slot is `list[Reference]` and `Reference` is `{type, id, note}` — no family slot, no confidence slot, no provenance slot. Expect the family and the confidence to survive only as prose in `note`, which is the one field a constrained narrator may not parse |
| **T1.12** | The four-column additive migration of §7.2 is the whole cost | **PASS expected** — `status`, `retract_reason`, `retracted_by`, `retracted_at`. One `ALTER TABLE`, one table, matching `PACKAGE.md` §7.3's B3 shape |

**What would count as a failure of this design test rather than of beacon:** any of T1.1, T1.6, T1.7 or T1.12 not holding. T1.2, T1.9 and T1.10 are predicted to fail *in beacon's data*, and a recorded contortion is a pass (`USE-CASES.md`).


### 9.2 The walk-through — expected vs observed

**Method.** Not prose. [`docs/tools/edges_beacon_probe.py`](../tools/edges_beacon_probe.py) parses beacon's model files **read-only** for their `mapped_column` declarations, maps every column onto an `EdgeRecord` field or onto *no home*, and walks the three shipped read seams over synthetic instances shaped like beacon's rows using [`edges_probe_kit.py`](../tools/edges_probe_kit.py) — a throwaway implementation of §2–§7 that lives in `docs/tools`, is not imported by the package, and imports `REFUSAL_REASONS` from `open_ontology.types` so it cannot quietly widen the closed vocabulary. **Nothing in beacon was edited, imported or executed.**

| # | Expected | **Observed** | Verdict |
|---|---|---|---|
| T1.1 | PASS | Ten of eleven `work_links` columns map. `relationship_type` → `family` — **and the DB column is named `relationship`, not `relationship_type`**, a mapping a third-party adapter author would get wrong from the docs alone. `status`, `retract_reason`, `retracted_by`, `retracted_at` are all absent, confirming the four-column migration | **PASS** |
| T1.2 | PREDICTED FAILURE | `relationship_type: Mapped[str \| None]` — **nullable**, confirmed by parse. No `person_link_types` model exists; the labels are a code comment | **FAILS as predicted → contortion E6** |
| T1.3 | PREDICTED PARTIAL | Every `task_stakeholders` column maps. `role` and `source` land in `attributes`, **unvalidated** — `payload_schema` is inert until R10 | **PARTIAL as predicted → contortion E10** |
| T1.4 | PASS | `source` mapped to `attributes`, not to `EdgeProvenance` | **PASS** |
| T1.5 | PREDICTED CONTORTION | See T1.5b below — it is worse than predicted | **CONTORTION E8** |
| T1.6 | PASS | `neighbors(task#41, ["blocks"], 1, direction="out")` → `["tenshen:entity:task#77"]` | **PASS** |
| T1.7 | PASS | `neighbors(task#41, ["blocks","task_stakeholder"], 2)` → `["tenshen:entity:person#7", "tenshen:entity:task#77"]`, `at_depth ∈ {1,2}` | **PASS — the missing hop, answered** |
| T1.8 | PASS on shape | `neighbors(organization#3, ["task_organization","blocks"], 2)` → both tasks. `role` rides in `attributes` | **PASS on shape, contortion E10 on payload** |
| T1.9 | PREDICTED FAILURE | The mixin's far end is `(source_table, record_id)` and `source_table ∈ {task_notes, project_notes, meeting_notes, open_loops}` — **table names, not entity names** | **FAILS as predicted → contortion E7** |
| T1.10 | PREDICTED NO | With **no** registered types, the `blocks` edge is **written**, not refused, carrying `warnings: ("endpoint_type_unregistered:tenshen:entity:task", ×2)` | **CONFIRMED, and it is the right behaviour** |
| T1.11 | PREDICTED LOSSY | See §9.3 | **LOSSY as predicted → contortion E9** |
| T1.12 | PASS | The four columns are absent from `work_links` today and nothing else is needed | **PASS** |

**T1.5b — the `created_by` count, and it is the finding of this design test.** The probe enumerated **six** `created_by`-shaped vocabularies across the interface and beacon:

| Site | Values |
|---|---|
| `INTERFACE.md` §2.1 `TypeEntry.created_by` | `seed` · `ai` · `user` |
| `WorkLink.created_by` | `user` · `ai` · **`interview`** |
| `PersonLink.created_by` | `user` · `ai` · **`interview`** |
| `TaskStakeholder.source` | `user` · `auto_extract` · `intake_auto` · `legacy` |
| `EntityMention.source` | `ai-inferred` · `user-linked` |
| `EntityMention.match` | **`deterministic`** · `llm` · `manual` |

**[Observed]** `EntityMention.match` carries the exact three-way distinction EDGES needs and does not have — *derived by a rule* / *inferred by a model* / *asserted by a person* — and its first value, **`deterministic`, is the same value UC3's BBL join wanted and could not name** (T3.8). **Two independent fixtures, on unrelated data, reach for one missing value.** That is `Q12`, and it is the strongest evidence in this document for amending a vocabulary rather than recording a contortion.

This is also, precisely, finding 0.1's *"seven vocabularies in one codebase"* recurring on the provenance axis rather than the entity axis. The registry's answer to that is `namespace` and `predicate`; neither helps here, because these six are not competing definitions of one word — they are six locally-correct answers to *how did this row come to exist*, which is one question with one right answer.

**T1.10, and why the observed behaviour is a pass rather than a shrug.** `endpoint_kind_mismatch` **cannot fire anywhere in beacon today**, because it fires only on a *registered* endpoint type and beacon has seven live, disagreeing entity-type vocabularies and no registered one. The probe shows the edge being written with two `endpoint_type_unregistered` warnings rather than refused — Rule U, a positive claim about a mismatch requires having looked. **This document reaches beacon's own §10.4 conclusion independently: *"Slice 0 (one entity-type vocabulary) is a hard prerequisite of this rule, not a nice-to-have."*** Recorded as corroboration, **not** as a design input — nothing here took a shape because beacon says so, and the agreement is what makes it worth reporting.

### 9.3 The `relations` slot — filled, and what is lost filling it

Beacon's `architecture/grounding-contract.md` specifies `"relations": list[Reference]` per entity and **`grep -rn '"relations"' src/beacon/ --include=*.py` returns zero hits** [Observed, beacon spec §2.4]. `Reference` is `{type, id, note}` [Observed, beacon spec §2.8].

The probe fills it from the T1.7 report:

```python
# `reached` is what makes this correct, and it was added because this very
# example was implemented the obvious way and came out silently wrong at hop 2.
[
    {"type": ne.reached.type.name, "id": ne.reached.id,
     "note": f"{ne.edge.family} (hop {ne.at_depth})"}
    for ne in report.edges if ne.reached is not None
]
{"type": "task",   "id": "77", "note": "blocks (hop 1, confidence 0.82)"}
{"type": "person", "id": "7",  "note": "task_stakeholder (hop 2)"}
```

> **Do not compute the far end by comparing an edge's endpoints against the origin.** At hop 2 the far end was never incident on the origin, so that reading returns the intermediate node twice and never mentions the one actually reached — with no error and no `complete=False`. `NeighborEdge.reached` exists because a reviewer wrote exactly that loop against the shipped registry (§4.1, row 4b's third round).

**It works, and the projection is lossy in a specific and reportable way.** Nine things a `NeighborReport` carries have no slot in a `Reference`: `family`, `at_depth`, `confidence`, `created_by`, `source_version`, `status`, `warnings`, and the report-level `complete` and `families_searched`.

**Why that matters more than it looks.** Under `constrained-narrator.md` §no-free-form-recall a producer-composed artifact may only cite relationships present in the bundle. So everything above survives **only as prose in `note`** — which is the one field a constrained narrator must not parse, because parsing it would be free-form recall. Concretely: **`at_depth` and `complete` cannot reach the narrator as structure**, so the two safeguards §4.4 installed against reading reachability as entailment are exactly the two the bundle drops.

**This is a finding for the beacon program, not a change to this document.** `Reference` would need three fields (`family`, `hop`, `confidence`) and the bundle a `relations_complete` flag; that is beacon's contract to amend, and slice 2 is where it would land. Recorded as contortion **E9** and relayed.

### 9.4 The ten contortions, recorded and **not** designed away

| # | Contortion | Where it bites |
|---|---|---|
| **E1** | `work_links` has no provenance beyond `created_by` / `created_at` / `confidence`. No actor, no evidence, no history, no `source_version` | `EdgeProvenance` returns them empty **with a `why`**; `stores_edge_events=False`. Honest, and half-blind — the same shape as `PACKAGE.md` §7.3's B5 |
| **E2** | No lifecycle columns at all | Retraction costs four additive columns. One `ALTER TABLE`, one table, no rewrite (T1.12) |
| **E3** | **Tenancy has no home, and this document refuses to invent one.** `work_links.user_id` is nullable with no FK; `work_links` has no `workspace` at all; the mention mixin has both, NOT NULL | Mapping `user_id`/`workspace` onto `Edge.namespace` is **refused**: namespace scopes a *vocabulary*, not a *tenant*, and mapping tenancy onto it would give every user a private `blocks` family — mechanism 4 manufactured by this spec on data with no collision in it. So an adapter filters outside the protocol or leaks across users. **Beacon's workspace rule to make. Q19** |
| **E4** | Endpoint ids are `Integer` in beacon, `str` in `InstanceRef` | The adapter casts both ways. Cheap, and it means an edge id round-trips as text; recorded because a `str`/`int` cast is where a silent key mismatch lives |
| **E5** | `purge_orphan_links` **DELETES** rows whose endpoint it does not recognise, and its `else` branch judges every non-`task` endpoint against the *project* id set — so live `report` edges are purged daily [Observed, beacon spec §10.4] | EDGES has no delete (§1) and retracts instead. The two policies contradict; the host's wins because the host owns the rows. **Relayed as a finding, already filed in beacon's own `TODO.md`** |
| **E6** | `PersonLink.relationship_type` is **nullable**; `Edge.family` is required | Skipping null-family rows is a silent drop by the adapter — mechanism **C** committed at the seam. Inventing a family asserts a fact the data lacks. **Neither is taken. Q18** |
| **E7** | Shape B's far end is `(source_table, record_id)` — a **row in a table**, not an entity instance | `endpoint_kinds` cannot be satisfied or checked. The three mention families are expressible only by declaring the four `source_table` values to be entity types, which they are not. **Q20** |
| **E8** | Six `created_by`-shaped vocabularies; `deterministic` has no value in ours | Survives only in `created_by_actor`, which is a string, not a vocabulary. **Q12**, and UC3 hits the same wall (T3.8) |
| **E9** | The grounding bundle's `Reference` drops nine fields, including `at_depth` and `complete` | The two safeguards §4.4 installs are the two the bundle cannot carry. Beacon's contract to amend |
| **E10** | Edge payload is unvalidated until **R10** lands in row 3e | `role`, `source` and `description` round-trip through projections with no schema. `PACKAGE.md` §5.3's default is `off` anyway, so nothing regresses — but the *justification* for `payload_schema` is unavailable in the row that specifies it |

### 9.5 UC1 verdict

> **Expressible, with ten recorded contortions, none designed away.** All three of beacon's relationship shapes map: Shape A cleanly (one homeless column, `user_id`), Shape C cleanly (every column homed), Shape B **not** (its far end is a table row). The three shipped read seams walk, and the flagship two-hop query — the one `deadline_cluster_service` stops one hop short of — is answered at `depth=2`, which is the whole argument for the cap being 2 rather than 1.
>
> **The cost is one `ALTER TABLE` on one table** (four additive columns), plus the three-column additive migration `PACKAGE.md` §7.3 already priced for `work_link_types`. Not zero, and the same order of magnitude.
>
> **Two of the ten are the interface telling beacon something true about its own data** rather than complaining about a field: E6 (a relationship whose type is optional is not a typed relationship) and E5 (the sweeper deletes what it does not recognise). Per `ROADMAP.md`'s rule of the ordering, those are the good outcomes.

---

---

## 10. Design test 2 — UC2 CMS: the implicit edges in a 400-row export

**CMS wins any conflict with Tenshen** (`ROADMAP.md`, rule of the ordering). Data: the checked-in 400-row Montana sample, `open_ontology/contract/fixtures/cms_sample_400.csv`, cut from the public CMS file by [`docs/tools/make_sample.py`](../tools/make_sample.py). Counts are pre-registered in [`0.5-ground-truth-PREREGISTERED.md`](../findings/0.5-ground-truth-PREREGISTERED.md).

### 10.1 Expected outcomes — **stated before the walk-through**

The ground truth fixes the node counts: **10** facilities (distinct CCN), **69** surveys `(CCN, Survey Date, Survey Type)`, **400** citations (one per row), **92** deficiency tags. The edge counts follow arithmetically, and stating them in advance is the point.

| # | Prediction | Expected |
|---|---|---|
| **T2.1** | Three instance-level families: `issued_during` (citation→survey), `conducted_at` (survey→facility), `cites` (citation→deficiency_tag) | **PASS.** All three are `level="instance"`, `endpoint_kinds` all `["entity"]`, none symmetric, all with an `inverse_label` |
| **T2.2** | Edge counts, from the ground truth | `issued_during` = **400** · `conducted_at` = **69** · `cites` = **400**. Distinct `dst` of `cites` = **92** |
| **T2.3** | `neighbors(facility:<ccn>, depth=1)` returns that facility's surveys; `depth=2` adds its citations | **PASS**, and the per-facility totals must sum to 69 and 400 across the ten facilities. `complete=True` over `families_searched` |
| **T2.4** | `neighbors(citation:<row>, depth=2, direction="out")` reaches the facility in two hops | **PASS** — `citation → survey → facility`, the deepest chain in the fixture, and the reason depth 2 is enough for CMS |
| **T2.5** | **The `value_set`-as-endpoint decision.** `citation:42 --has_severity--> value_set:scope_severity_code` | **REFUSED**, `endpoint_kind_mismatch`, per §2.4.1: a `level="instance"` family takes only `entity` endpoints |
| **T2.6** | **The harder half of the same question**: severity as `Edge.attributes` on the `cites` edge | **PREDICTED: it fits structurally, and must be refused on principle.** The test is mechanical — *does every property of the citation row fit on the `cites` edge?* If `Scope Severity Code` rides on the edge, so do `Deficiency Corrected`, `Correction Date` and the five Y/N flags, and `cites` becomes the citation row under another name. Expect the answer to be **yes, they all fit**, and therefore expect the edge model to refuse the whole class: **a citation's properties belong to the citation, and EDGES stores no node properties (§1)** |
| **T2.7** | The two CMS `value_set`s appear in the edge store at all | **PREDICTED NO** — neither at instance level (T2.5) nor as a payload (T2.6). Expect them to be reachable only as **type-level** endpoints, which CMS has no use for. The `value_set` kind CMS forced into `INTERFACE.md` is exercised here as an endpoint *the rule excludes* |
| **T2.8** | **T4 — 104 names shared across CCNs** — is caught | **PREDICTED NO, by design.** §1 declines entity resolution. An ingester keying facilities by `Provider Name` writes `conducted_at` edges that merge distinct facilities, and the edge model cannot tell. Expect the probe to check whether the ten sample facilities collide by name, and expect **they do not** — so the fixture does not exercise the trap, which is itself worth recording |
| **T2.9** | **T2 — 6 of 400 rows have a correction date before the survey date** — is representable | **PREDICTED: representable, not caught.** It is a fact about two *columns of one row*, i.e. a node property, so it never becomes an edge. Expect it to be recordable only as `Evidence` on the `issued_during` family's provenance, which is a statement about the vocabulary and not about the six rows |
| **T2.10** | **T3 — `Location` is 99.988% redundant** | **PREDICTED: not an edge question at all.** `resolve_type` already answers it `not_a_type / redundant_projection` (`C3-08`). Expect EDGES to add nothing and to claim nothing |

**The conflict rule is live in T2.5/T2.6.** UC1 would be *served* by letting payload ride on edges — beacon has fourteen payload-carrying families out of seventeen. UC2 says a property of a row is not a property of a relationship. **CMS wins**, and §2.4.1's rule is written CMS's way.

### 10.2 The walk-through — expected vs observed

**Method.** [`docs/tools/edges_cms_probe.py`](../tools/edges_cms_probe.py) reads the checked-in 400-row sample, builds the three families and every edge through `edges_probe_kit`, and compares every count against the **frozen** ground truth. `py docs/tools/edges_cms_probe.py` → `ALL CHECKS PASSED`. The machinery that is *not* CMS-specific — retraction, every declined capability, the dead-end walk — is driven separately by [`edges_capability_probe.py`](../tools/edges_capability_probe.py), added in round 1 (§17).

| # | Expected | **Observed** | Verdict |
|---|---|---|---|
| T2.1 | PASS | three `level="instance"` families, `endpoint_kinds` all `("entity",)`, none symmetric, each with an `inverse_label` | **PASS** |
| T2.2 | 400 / 69 / 400, 92 distinct | nodes: facilities **10**, surveys **69**, citations **400**, tags **92**. Edges: `issued_during` **400**, `conducted_at` **69**, `cites` **400**, distinct `cites` destinations **92** | **PASS — every pre-registered number** |
| T2.3 | sums to 69 and 400 | summed over all ten facilities: **69** surveys at depth 1, **400** citations added at depth 2. One report: `known=47 complete=True depth_reached=2 families_searched=('conducted_at','issued_during')`, `at_depth ∈ {1,2}` | **PASS** |
| T2.4 | facility in two hops | `neighbors(citation#0, [...], 2, direction="out")` → `["cms:entity:survey#275012|2025-12-16|Health", "cms:entity:facility#275012"]` | **PASS** |
| T2.5 | REFUSED | Refused at **two** layers. Declaring the permissive family at all raises *"a level='instance' family may only declare `entity` endpoints"*; and with a correctly declared family the write returns `Refusal(reason="endpoint_kind_mismatch", detail={"endpoint": "dst", "problem": **"level"**, "family_level": "instance", "node_level": "type", …})` | **PASS, and sharper than predicted twice over** — see below |
| T2.6 | fits, refuse anyway | **10 of 10** citation properties are single-valued per `cites` edge | **PASS — the prediction was exact** |
| T2.7 | value sets absent | neither value set appears in the edge store | **PASS** |
| T2.8 | not caught; sample does not exercise it | 10 distinct provider names over 10 CCNs; **0** names shared | **PASS — the fixture does not exercise T4** |
| T2.9 | representable, not caught | **6 of 400** rows carry a correction date before the survey date, matching the pre-registered 1.5% | **PASS** |
| T2.10 | nothing added | `resolve_type` answers it; EDGES adds nothing | **PASS** |

**T2.5 was refused on `level`, not on `kind`, and that is worth noticing.** The probe deliberately declared `has_severity` with `endpoint_kinds={"dst": ("entity","value_set")}` — a family that *permits* a value set — to check whether the rule could be talked around by a permissive declaration. It cannot, and after round 1 it cannot in two different ways: **the declaration itself is refused**, and even for a correctly declared family the `level` check runs before the kind check, so a `value_set` reached as `scope_severity_code` is a `TypeRef` where the family requires an `InstanceRef`. **In the first draft only the second of those existed, and `endpoint_kinds` was therefore a rule a family author could opt out of.** That ordering and that enforcement point are now explicit in §2.4.1 because the probe made them visible.

**T2.6, and the mechanical test coming out exactly as pre-registered.** *Does every property of the citation row fit on the `cites` edge?* For each of `Deficiency Prefix`, `Deficiency Category`, `Scope Severity Code`, `Deficiency Corrected`, `Correction Date` and the five Y/N flags, the probe grouped values by `(citation, tag)` pair: **every one is single-valued.** All ten fit.

> **Therefore the whole class is refused.** If `Scope Severity Code` may ride on the edge, so may the other nine, and `cites` becomes the citation row under another name — with the registry storing node properties it has said three times (§1, §2.4.1, `INTERFACE.md` §2.1) that it does not store. The test was pre-registered as a mechanical one so the answer could not be argued afterwards, and it came out as predicted.

**The UC2-vs-UC1 conflict, resolved in CMS's favour.** UC1 would be *served* by payload on edges: **14 of beacon's 17 join families carry payload** [Observed, beacon spec §10.5]. UC2 says a property of a row is not a property of a relationship. **CMS wins**, per the rule of the ordering, and §2.4.1 is written CMS's way. The cost to UC1 is real and is recorded as contortion **E10**: beacon's `role` and `source` ride in `attributes`, unvalidated, and `payload_schema` is the thing that would validate them.

### 10.3 UC2 verdict

> **Expressible with no contortions, every pre-registered count reproduced, and one decision taken against UC1's interest.** The three-level CMS structure is three instance families; the deepest chain is two hops, which is the cap; the two `value_set` entries are excluded from the edge store by a rule the fixture itself motivated.
>
> **What UC2 contributed that no other fixture could:** the `endpoint_kinds`/`level` split (§2.4.1), and the mechanical test that stopped the edge model from absorbing a row. **What it did not exercise:** T4 (name collisions) — the ten-facility sample has none, so entity resolution's absence is *stated* here rather than *shown*, and a later fixture should show it.

---

---

## 11. Design test 3 — UC3 NYC: cross-agency edges and `borough` as three types

**The subject [Observed 2026-08-28, re-verified 2026-08-29].** The three datasets `USE-CASES.md` and [`3C-VALIDATION.md`](../findings/3C-VALIDATION.md) §1 fix, kept so the test is reproducible: **A** `uvpi-gqnh` (DPR trees, 683,788 rows, `data_updated_at` 2017-10-04), **B** `erm2-nwe9` (311 requests, 22,283,935 rows, 2026-08-28), **C** `693u-uax6` (DOT parking meters, 15,598 rows, 2026-08-24). Namespaces `dpr`, `oti_311`, `dot`.

**UC3 conflicts are recorded as Q-numbered questions for the supervisor, never as R-numbers** (brief; `USE-CASES.md` conflict rule).

### 11.1 Expected outcomes — **stated before the walk-through**

| # | Prediction | Expected |
|---|---|---|
| **T3.1** | The three `borough` value sets register as three scoped `kind="value_set"` types and are joined by `equivalent_to` | **PASS.** W2.2's PREDICTED GAP in [`3C-VALIDATION.md`](../findings/3C-VALIDATION.md) is the gap this family exists to close, and R7 is the ruling that assigned it here |
| **T3.2** | The realistic write order is a **chain, not a triangle**: each publisher joins the one it found. So `A ≡ B` and `B ≡ C` are written, and `A ≡ C` is not | **PASS**, and it is the interesting case rather than the tidy one |
| **T3.3** | `neighbors(dpr:borough, ["equivalent_to"], depth=1)` returns `{oti_311:borough}` | **PASS**, `complete=True`, `known=1` |
| **T3.4** | `neighbors(dpr:borough, ["equivalent_to"], depth=2)` returns `{oti_311:borough, dot:borough}` | **PASS on reachability — and `dot:borough` is NOT asserted equivalent to `dpr:borough`.** §3.1 makes the family symmetric and **not** transitive. Expect `at_depth` to be the only thing standing between this report and a manufactured equivalence class, and expect the design test to *check* that it does |
| **T3.5** | `neighbors` returns nodes in namespaces the caller did not name | **PASS**, and this is the answer the brief asks for: the report spans `dpr`, `oti_311` and `dot`, `namespace=` on the call scopes only the resolution of `edge_families`, and it filters nothing |
| **T3.6** | Is that report `complete`? | **PASS with a caveat that must be stated: `complete=True` over `families_searched`, never over the catalogue.** 2,399 datasets exist; three are in this store. Expect the design test to state that a `complete=True` printed without `families_searched` is not a claim (§4.4) |
| **T3.7** | A cross-agency **instance** edge between two datasets is expressible | **PASS expected.** The joinable key is `bbl` (borough-block-lot), present in both A and B. Expect `dpr:street_tree:<id> --same_tax_lot--> oti_311:service_request:<id>`, `level="instance"`, with `confidence` and an `Evidence` recording the join basis |
| **T3.8** | `EdgeProvenance.created_by` has a value for *"derived by a deterministic rule at ingest"* | **PREDICTED CONTORTION, and the second fixture to hit it.** The vocabulary is `seed \| ai \| user` (T1.5 hits the same wall from beacon's `interview`). A deterministic `bbl` join is none of the three. Expect it to survive only in `created_by_actor` |
| **T3.9** | `dpr:street_tree:<id> --in_borough--> dpr:borough` | **REFUSED**, `endpoint_kind_mismatch` — an instance-level family may not point at a `value_set`. Expect the §2.4.1 rule to bite on the fixture that motivated the *other* half of it |
| **T3.10** | `EdgeProvenance.source_version` makes a stale cross-agency edge visibly stale | **PASS expected.** A `same_tax_lot` edge from A's 2017-10-04 census to B's 2026-08-28 feed is a nine-year-old claim about one endpoint, and §5.3 exists so that fact is on the row rather than in a reader's head |
| **T3.11** | Dataset B's own agency ambiguity (`resource.attribution` = `311`, `domain_metadata` = OTI) affects edges | **PREDICTED: inherited, not created.** The namespace choice is made before any edge exists; expect the edge model to add no new ambiguity and to fix none |
| **T3.12** | `equivalent_to` weakens `merge_types` | **PREDICTED NO, and this is the load-bearing check.** With `dpr:borough ≡ oti_311:borough` written, `merge_types(from_="borough", into="borough", namespace="dpr", into_namespace="oti_311")` must still return `Refusal(reason="cross_namespace_merge")`, non-overridably, with the edge present and with `acknowledge=["cross_namespace_merge"]` supplied. Expect **refused**, exactly as in `INTERFACE.md` §10b's table |

### 11.2 What a failure would mean

T3.12 failing would be the kill row (`ROADMAP.md`: *the answer to collision must be scoping, not merging*) reopened by this document. T3.4 failing — a report a reader cannot distinguish from an equivalence class — would mean `equivalent_to` is transitive in practice however it is documented, and the family should not ship.

---
### 11.3 The walk-through — expected vs observed

**Method.** [`docs/tools/edges_nyc_probe.py`](../tools/edges_nyc_probe.py), live against the SODA API, using **two** engines on purpose: the **shipped** `open_ontology.Registry` on SQLite for everything about types (so T3.12's claim about `merge_types` is a claim about the real implementation), and `edges_probe_kit` for everything about edges. `py docs/tools/edges_nyc_probe.py` → `ALL CHECKS PASSED`. Capability-degradation and lifecycle paths are driven by [`edges_capability_probe.py`](../tools/edges_capability_probe.py) (§17).

**The value sets, re-pulled live 2026-08-29** — W2's data, unchanged:

| | field | values |
|---|---|---|
| **A** `uvpi-gqnh` | `boroname` | `Bronx` · `Brooklyn` · `Manhattan` · `Queens` · `Staten Island` |
| **B** `erm2-nwe9` | `borough` | `BRONX` · `BROOKLYN` · `MANHATTAN` · `QUEENS` · `STATEN ISLAND` · **`Unspecified`** |
| **C** `693u-uax6` | `borough` | `Bronx` · `Brooklyn` · `Manhattan` · `Queens` · `Staten Island` |

Same five referents, three encodings, and B carries an extra spelling of *unknown*. **This is why `equivalent_to` is not a merge:** the types denote the same thing and their value sets are not interchangeable.

| # | Expected | **Observed** | Verdict |
|---|---|---|---|
| T3.1 | PASS | three `TypeEntry` rows from the **shipped** registry, `dot:borough` / `dpr:borough` / `oti_311:borough`, coexisting | **PASS** |
| T3.2 | chain | `A ≡ B` and `B ≡ C` written; `A ≡ C` not | **PASS** |
| T3.3 | `{oti_311}`, `known=1`, complete | exactly that | **PASS** |
| T3.4 | reaches `dot`, **not** asserted equivalent | `nodes = [dot:value_set:borough, oti_311:value_set:borough]`; `at_depth`: `dpr→oti_311` = **1**, `oti_311→dot` = **2**; **no edge in the report has `dpr:borough` and `dot:borough` as its two ends** | **PASS — reachability, not entailment** |
| T3.5 | spans namespaces | the caller passed `namespace="default"` and the report's nodes are in `dot` and `oti_311` — **neither of them the namespace named** | **PASS** |
| T3.6 | complete, with the caveat | `complete=True`, `families_searched=("equivalent_to",)` | **PASS, and see below** |
| T3.7 | expressible | 25 complaints over **22** distinct BBLs; **54** census trees on those lots; **102** edges written; **18 of 25** complaints matched a tree; **max 16 trees on one lot** | **PASS, and it found something** |
| T3.8 | CONTORTION | `created_by='user'`, `created_by_actor='import:socrata_bbl_join'` | **CONTORTION confirmed — Q12** |
| T3.9 | REFUSED | Refused at **two** layers, as in T2.5: the permissive family raises at declaration, and the write returns `Refusal(reason="endpoint_kind_mismatch", detail={"problem": "level", …})` | **PASS** |
| T3.10 | visible staleness | `source_version = "erm2-nwe9@2026-08-28 / uvpi-gqnh@2017-10-04"` on every edge | **PASS** |
| T3.11 | inherited, not created | namespace assignment for B is made before any edge; EDGES adds no ambiguity | **PASS** |
| T3.12 | **still refused** | `Refusal(reason="cross_namespace_merge")` with the edge present; **and again** with `acknowledge=["cross_namespace_merge","definitions_diverge"]` | **PASS — the load-bearing check** |

**T3.13 — added in round 1, and NOT pre-registered.** The expectations in §11.1 were frozen before the loop, and this case is not among them: **`equivalent_to` between two `kind="edge"` types.** It is recorded here as an addition rather than folded into §11.1, because a prediction written after the fact is not a prediction.

```
equivalent_to(dpr:edge:concerns, oti_311:edge:relates_to)   -> written, not refused
neighbors(dpr:edge:concerns, ["equivalent_to"], 1)          -> ["oti_311:edge:relates_to"]
```

**Why it matters enough to add a case:** two agencies naming the same real-world relation differently is UC3's own collision shape, one level up from `borough`, and the first draft's §1 forbade it while §3.1 declared it legal — a contradiction no design test exercised. Both round-1 reviewers found it by reading; **neither could have found it by running, because nothing ran it.** That is the argument for the case, and for the fourth probe.

Also observed, from the same run: `depth=3` raises `ValueError` (§4.2); a typo'd family (`equivalant_to`) returns `Refusal(reason="edge_family_unknown")` for the **whole call**; and a registry with no edge store returns `Refusal(reason="edge_store_absent")` rather than an empty report.

**T3.7 found something the expectation did not anticipate, and it is the UC3 finding.** The BBL join is **many-to-many**: one tax lot carries up to **16** census trees, and **7 of 25** 311 tree complaints matched no census tree at all. So a deterministic key match — the most confident kind of join an ingestion layer can make — does **not** establish the relationship a reader wants. *"This complaint is about this tree"* is not entailed by *"this complaint and this tree share a tax lot"*.

Two consequences taken in the walk-through rather than argued:

1. **The family is named for what the key proves**, `same_tax_lot`, not for what a reader wants, `concerns`. A family name that overstates its evidence is mechanism 4 arriving through the vocabulary the edge store itself introduces.
2. **`confidence` is `1/n`** where *n* is the number of trees on the lot — 1.0 for a single-tree lot, 0.0625 for the sixteen-tree one — and `Evidence` records the join basis verbatim. Both fields already existed for exactly this; the fixture is what shows they are load-bearing rather than ornamental.

**A reproducibility gap, found and closed.** The first two runs of this probe printed different numbers (73 edges / max 29, then 62 / max 16) because the SODA query had `limit` and no `order`, so the API returned an arbitrary 25 rows. **A design test whose numbers move between runs is not a design test.** The query now pins `order=unique_key` and two consecutive runs agree exactly. Recorded because it is the same class of defect as `2A-RUN.md` §8.4's, and because it was found by running twice rather than by reading.

**T3.6, said plainly.** `complete=True` here means *every `equivalent_to` edge in this store was returned*. It does **not** mean anything about the 2,399 datasets in the catalogue, of which three are present. That is why `families_searched` is a required field and not an echo: **a `complete=True` printed without it is the same category of claim as a conformance verdict printed without its coverage line** (ruling R12), and this document takes R12's rule rather than restating it.

### 11.4 Contortion E11, and the thing UC3 did **not** break

**E11 — `equivalent_to` at scale has no proposer.** The two edges in this walk-through were written by hand. Nothing in v0 *finds* the equivalence: `resolve_type` is scoped to one namespace (contortion 8), and **R6's `search_namespaces` — the call that would find it — lands in row 3e, after this one.** So the family exists and the mechanism that would populate it does not, and at 2,399 datasets a hand-written equivalence is not a mechanism. **This document closes contortion 9 and is dependent on 3e closing contortion 8 for the closure to be useful.** Stated so that *"EDGES fixed the borough problem"* is not read into §11.

**What UC3 did not break, which is the more important half.** The kill row's mechanism — *scope, do not merge* — is **stronger** after this test, not weaker. Before EDGES, a steward who knew two scoped types denoted one thing had exactly one move available and it was the destructive one, refused. Now there is a non-destructive move that records the knowledge, **and the destructive one is still refused, twice, including under explicit acknowledgement.** T3.12 is the check that this document did not quietly become a merge licence, and it was run against the shipped registry rather than reasoned about.

### 11.5 UC3 verdict

> **Expressible. Contortion 9 (`INTERFACE.md` §10b.2 — *nothing can say "these two mean the same thing, kept apart"*) is closed by `equivalent_to`, and the closure was checked against the shipped `merge_types`: the `cross_namespace_merge` refusal holds, non-overridably, with the equivalence edge present.**
>
> **One new contortion (E11)** — the family has no proposer until R6 lands in 3e — **and one finding the expectations missed:** a deterministic key join is many-to-many, so the most confident join an ingestion layer can make still does not establish the relationship a reader wants. `confidence` and `Evidence` are what carry that, and the family is named for what the key proves.
>
> **UC3 conflicts with neither UC1 nor UC2.** Every finding here is an absence or a caution, none contradicts the other two fixtures, and per `USE-CASES.md`'s conflict rule there is nothing for the supervisor to arbitrate between fixtures. The four items wanting a ruling are Q-numbered in §14.

---

## 12. Which mechanism this is designed against

**Primarily mechanism C — silent per-consumer drop — and that is a different answer from `INTERFACE.md`'s.** `INTERFACE.md` §6 is designed against **1 + 3** under assumption A1, with C *"present, unobserved"*. For edges the ranking inverts, and the evidence is in this repo rather than assumed:

| Mechanism | Status for EDGES | What answers it |
|---|---|---|
| **C** silent drop | **Dominant, and [Observed] rather than assumed.** `deadline_cluster_service` hard-codes the family `blocks`; `work_link_types` is *extended at runtime by an AI classifier*; a new family is therefore invisible to the one shipped edge consumer, silently. That is 0.1's incident shape with a classifier as producer | §8 — `consumers` extends to families with **no new call**, because a family is a `TypeEntry`. Plus the `no_edge_gate_registered` warning |
| **4** collision | **Co-dominant, and it is why this row exists at all.** R7 assigned `equivalent_to` here because `INTERFACE.md`'s answer to collision — scope, do not merge — left nothing that could say *equivalent, kept apart* | §3 — `equivalent_to`, symmetric, non-transitive, non-merging, and explicitly not a merge licence (T3.12) |
| **3** never retired | Present | Families retire like any type; edges retract (§2.6). `usage`/`orphaned` on a family answers *"is anything still writing this?"* |
| **1** no review | Present, **at the family level only** | The family goes through `propose_type` → `approve`; individual edges do not, and §2.6 argues why rather than assuming it |
| **2** could not find | **Present and NOT answered here.** E11: nothing finds the equivalence to be recorded | R6's `search_namespaces`, row 3e. Stated as a dependency, not claimed |

**No single call is the centre, and for edges that is easier to see than for types.** There is one read call and two writes. The centre is the *family*, which is not a call at all — it is the decision that a relationship label is a governed word.

---

## 13. What would change this

Mirroring `INTERFACE.md` §11.

| If… | Then | What changes here |
|---|---|---|
| **A family needs a field the registry must READ** — not validate, read | §2.3 is wrong | `kind="edge"` stops being a type and wants its own table and its own calls. §2.4's five keys are the pressure point; `level` is the one closest to needing it |
| **A real consumer needs `depth=3`** | §4.2's cap is wrong | The cap moves *with that consumer's evidence*, and R13 must be revisited in the same change — the cap and the no-paging rule are one decision |
| **R13 is revisited and the façade pages** | §4.2's justification evaporates | The depth cap becomes arbitrary and should be re-derived, or dropped in favour of a page bound |
| **R10 does not land in 3e** | §2.5 is a dead field | `payload_schema` is removed rather than left as a `None` that never becomes anything, and edge payloads are declared permanently opaque |
| **`equivalent_to` is used as a merge precondition anywhere** | §3.2 has failed in practice | The family should be withdrawn. An edge that becomes a licence is worse than no edge, because the refusal it erodes is the answer to the kill row |
| **A consumer reads a depth-2 report as an equivalence class** | §4.4's `at_depth` is insufficient | Either `neighbors` refuses `depth=2` for non-transitive families, or the family declares `transitive: bool` and the report enforces it. Both are surface changes and neither is taken now |
| **Beacon's Slice 0 does not land** | `endpoint_kinds` is unenforceable on the one host that exists | The declaration stays honest (warnings, not claims) and buys nothing operationally. It is not removed — CMS and NYC both register their types |
| **The office says two teams meaning different things by one word IS the main complaint** (A1 wrong) | `INTERFACE.md` §11's first row fires | `equivalent_to` gets *more* load-bearing, not less, and its non-transitivity becomes the thing to defend hardest |
| **`Reference` in beacon's grounding contract stays three fields** | §9.3's loss is permanent | Slice 2 delivers a `relations` slot that cannot carry `at_depth` or `complete`, so the narrator sees reachability with no way to tell it from entailment. **This is the most consequential open item for the Tenshen rebuild** |

**Weaknesses named now so they are not discovered later:**

- **The edge store's `complete=True` is the first true completeness claim this project makes**, and it is true only over `families_searched`. Every consumer that prints it without that list is making a claim this document did not authorise.
- **Duplicate edges are permitted (§6.1)**, so `known` counts edges and not distinct neighbours. A consumer that counts `edges` to mean *"how many people are blocked"* is wrong, and nothing stops it.
- **No edge is ever deleted**, so a store that ingests a daily feed accumulates retracted edges forever. Nothing here sizes that.
- **`neighbors` is the only read.** There is no *"do these two nodes have an edge?"* call, which is a one-edge `find_edges` a caller must express as a depth-1 walk and filter.

---

## 14. Questions for the supervisor — **Q12 onward**

Numbering continues from Q11 (ruled as R16). None of these is taken on this document's authority.

| # | Question | Recommendation | Founder-visible? |
|---|---|---|---|
| **Q12** | **`created_by` has three values and the data needs four.** Six `created_by`-shaped vocabularies were counted (§9.2 T1.5b), and **two independent fixtures reach for the same missing one**: beacon's `EntityMention.match` has `deterministic`, and UC3's BBL join is a deterministic rule that must currently claim `user`. Add a fourth value — `derived` — to `INTERFACE.md` §2.1's `created_by`? | **Yes**, in row 3e, which is already amending that document. It is additive, it is the *only* one of these questions with evidence from two unrelated fixtures, and the alternative is a string convention in `created_by_actor` that nothing validates | **Yes** — it changes `TypeEntry` too, not only edges |
| **Q13** | **`symmetric ⇒ inverse_label is None` is a cross-field rule, and `PACKAGE.md` §5.6 says `FieldSpec` does not do cross-field rules.** So `approve()` must know one rule about `kind="edge"` attributes. Is that acceptable, or does it breach §3.1's boundary? | **Accept it, narrowly**, and record it as the one attribute rule the registry knows. The alternative — a rule language in the schema mechanism — is much larger than v0 needs, and `INTERFACE.md` §9 contortion 1 has been open since #1 | No |
| **Q14** | **Does R11's `reinstate` (row 3e) cover edges?** §2.6 declines to invent a second reinstatement one row ahead of the first | **3e decides**, with edges in scope. Two differently-shaped reinstatements would be Cause B | No |
| **Q15** | **Should `EdgeProvenance` carry `model_tier`, and should AI-written edges have a tier gate?** Beacon's `infer_person_relationships` classifies with **Haiku** and auto-applies at ≥0.7 — 0.5's failure shape, one level down | **`model_tier`: yes** (cheap, additive, symmetric with `Provenance`). **A tier gate: no in v0** — gating a weekly batch job is a product decision about beacon's behaviour, not a storage shape | **Yes** — it is 0.5 consequence 2 reappearing |
| **Q16** | **Should `Provenance` gain `source_version` too?** `EdgeProvenance` has it (§5.3); `INTERFACE.md` §10b.5 collected it for v1. Two shapes, one concept, one missing the field | **Yes**, row 3e. Additive, defaults `None`, and 3e already opens that shape. Beacon has independently built the same thing as `EntityMention.content_hash` | No |
| **Q17** | **A consumer that gates on edges by ENDPOINT KIND has no representation** — *"I traverse any edge whose `dst` is a `person`"*. Same shape as contortion 11 (value-level gates), one level along | **Defer to Phase 3**, with contortion 11. Both would make `Consumer.gate` a query language | No |
| **Q18** | **`Edge.family` is required; `PersonLink.relationship_type` is nullable.** Should there be a reserved `unclassified` family, or must an adapter refuse to map such rows? | **Neither in v0. Record it.** A reserved family is a vocabulary this document invents for a host's missing constraint; refusing to map is a silent drop. The honest third answer is that beacon should make the column NOT NULL, which is beacon's call | No |
| **Q19** | **Tenancy has no home (E3).** `user_id` / `workspace` map to nothing, and `Edge.namespace` is refused as their home | **Do not solve it here** — the brief says so and the reason holds: namespace scopes a vocabulary, not a tenant. But the question *"does the edge protocol need a tenancy dimension at all, or is filtering the host's job?"* is Phase 2B's first real integration question and should be answered before beacon builds against this | **Yes** — it gates 2B |
| **Q21** | **The depth cap bounds hops; degree is unbounded, and UC3's own fixture has a 9.7M-degree node (§4.2).** `neighbors` materialises its answer and R13 forbids façade paging, so a caller who needs all of a supernode's neighbours cannot get them. The assembly bound tells the truth and does not solve it | **Route it to R13's own question rather than answering it here.** R13 deferred façade paging to Phase 3 *because the ingestion loop is the consumer that would force it* — and this is that consumer, arriving with a number. The recommendation is that **Phase 3 decides paging for `list_types` and `neighbors` together**, since Rule K's unanswered question (what `known` means on a page) is identical for both. Nothing here should page in isolation | **Yes** — it is the first hard scale limit this project has measured rather than assumed |
| **Q20** | **Shape B's far end is a table row, not an entity instance (E7).** Does `endpoint_kinds` need a third level, or is Slice 0 the answer? | **Slice 0 is the answer**, and this is evidence for it rather than a change here. A `record` level would let any table row be a node, which deletes the distinction §2.4.1 exists to hold | No |

---

## 15. Kill-criterion check — required, and not skipped

**`ROADMAP.md`'s kill row:** *"A capability predicate gets merged as a duplicate → Stop."* And the rule of the ordering: *nothing in #1–#4 may take a shape because Tenshen has it.*

**Neither is tripped, and here is the mechanical form of both.**

**1. Is this document a merge licence?** No, and it was tested rather than asserted. T3.12 wrote the `equivalent_to` edge and then asked the **shipped** registry to merge the two types: refused `cross_namespace_merge`, and refused again under explicit `acknowledge`. §3.2 states the rule; the probe checked it against `open_ontology.Registry`, not against the probe's own model.

**2. Can a predicate be an edge endpoint?** **No, and this answer had to be earned.** The rule is **general** — §2.4.1 forbids `kind="predicate"` in any family's `endpoint_kinds`, at either level — for the reason `INTERFACE.md` §5.10's refusal #2 is non-overridable: two predicates being "equivalent" is a claim about **extents**, and it must be made from **non-empty** byte-identical extents or not at all *(the `non-empty` half added by row #6 — see §2.4.1)*. **A type-level edge asserting equivalence between two predicates is exactly the kill row, one indirection away.**

> **In the first draft it was NOT structurally blocked, and this section said it was.** The exclusion lived only in `equivalent_to`'s own declaration, so it was a family author's opt-in. A round-1 reviewer declared a permissive family of their own (`same_capability`), wrote a predicate-to-predicate edge, and got no refusal — **the kill row, reached through a door this document had left open while claiming it was shut.** The rule is now general and enforced in the probe kit's `Family.__post_init__`, which refuses the family at declaration time rather than the edge at write time. Recorded rather than quietly fixed, because *a guard that depends on every future author remembering* is the class of protection this project refuses elsewhere (§5.10 refusal #2 is non-overridable for the same reason).

**3. Did anything take its shape from Tenshen?** The five family keys, checked one at a time:

| key | Whose need |
|---|---|
| `symmetric`, `inverse_label` | **Tenshen has both as columns.** They are also `INTERFACE.md` §9 contortion 1, open since deliverable #1 and named there as the reason #4 must follow #1 closely. Taken because a contortion the interface recorded is a debt this document owes, not because beacon has the columns |
| `level` | **UC3.** Beacon has *no* type-level edge at all; `equivalent_to` is unexpressible without `level`, and R7 assigned it |
| `endpoint_kinds` | **UC2.** The `citation`/`survey`/`facility`/`deficiency_tag` chain needs each end constrained, and T2.5/T2.6 is where the rule was decided — against UC1's interest |
| `payload_schema` | **UC2 again**, via `PACKAGE.md` §5.1's argument about the A–L severity ordering. UC1 is the fixture that *suffers* from it being inert (E10) |

**Three of five come from CMS or NYC; two are a debt to #1. Zero are shaped by beacon.** And the direction of the one real conflict is the check that matters: §2.4.1 was written CMS's way **against** UC1's interest, on a fixture where 14 of 17 beacon families carry the payload the rule excludes.

**4. Would deleting `equivalent_to` leave the rest coherent?** Yes — §2–§8 stand without §3, and UC1 and UC2 need no type-level edge at all. That is the operational test of whether a design is centred on one family, and it is not.

---

## 16. Exit criteria — `ROADMAP.md` row #4, checked

| Criterion | Where |
|---|---|
| A typed relationship store, specified | §2, §5, §6, §7 |
| `neighbors(node, edge_types, depth)` read seam | §4. Bounded at 2, Rule K/U throughout, no traversal language, no materialisation, no paging (R13) |
| Provenance on edges | §5. `EdgeProvenance`, append-only history, `EventRecord.edge_id`, `source_version` |
| Type-to-type edges (**R7**) | §3. `equivalent_to`, symmetric, non-transitive, non-merging — and the non-merging half checked against the shipped registry |
| `v0` and "unstable" in the header | Header, line 3 |
| A design-test section per use case, expected outcomes stated first | §9, §10, §11. **Thirty-four predictions, committed in a separate commit ahead of the results; eleven contortions recorded, none designed away** |
| An adversarial review loop | §17. **Three rounds, six fresh reviewers, ten BLOCKING and ten MAJOR findings**, every one reproduced by running code. **No round was clean.** Closed at the brief's three-round cap with a convergence note (§17.5), the same way rows 3c and 3d closed. *(Row 4b runs its own loop over the implementation; whatever [`4B-RUN.md`](../runs/4B-RUN.md) §6 records is the state of it. **This sentence used to say the loop "ran", in a commit whose own `4B-RUN.md` §6 said it had not started** — round-2 finding B6 of THIS document's loop, recurring one row later inside the change that added the process gate meant to catch it. A cross-reference that asserts the other document's content is a claim; one that names it is a pointer.)* |
| **Implemented** *(row 4b, and not part of row #4's own criteria)* | Adapter primitives **16–18**, the four capability flags and two declarations, store version **4** on both dialects, `add_edge` / `retract_edge` / `neighbors` / `edge_provenance` on the registry, `equivalent_to` seeded, and **41 contract ids** (`C17` 31, `C18` 10) across three reference legs in both stacks. *(This cell said **39** until row 4b's second adversarial round: 29 + 10 was the count before that row's FIRST round added `C17-30` and `C17-31`, and the commit that corrected two other cells of this same table left the third stale. **The third self-accounting error in this document's own summary table, and the second inside row 4b.** §17.5 says a document that self-reports its own evidence needs an adversary pointed at the self-report. It was right again.)* |
| Every new `warnings` value goes through `INTERFACE.md` §5.4 in the same change | §2.8. Five added; §5.4 now enumerates sixteen across four carriers |
| New `Refusal.reason` values go through `INTERFACE.md` §5.12 in the same change (**R3**) | **Four** added: `edge_family_unknown`, `endpoint_kind_mismatch`, `edge_store_absent` — and `unknown_edge`, which §17.4 records this document's own round 3 adding. §5.12 enumerated **nineteen** at this row's close. *(This cell said "Three… eighteen" until row 4b, disagreeing with §17.4 three sections below it, with `INTERFACE.md` §5.12's own header, and with `types.REFUSAL_REASONS`' comment — a **three-way** mismatch, in the summary table a reader checks before trusting the rest. Exactly §16's own recorded failure mode, on a different number.)* |

---

## 17. The adversarial review loop

**Protocol** (`USE-CASES.md`, standing constraint 7; the brief's stop rule): fresh reviewers each round, briefed with the three fixtures and told to **drive the design through each fixture's real data rather than read it** — 3c's lesson being that *"every finding of substance came from driving the real registry through a real scenario, none from reading."* Two reviewers per round, distinct lenses. **Stop: two consecutive clean rounds, or three rounds plus an honest convergence note.**

### 17.1 Round log

| Round | Reviewers | Verdicts | BLOCKING | MAJOR | Outcome |
|---|---|---|---|---|---|
| **1** | real-data lens · coherence lens | NOT YET · NOT YET | **3** (**1** found independently by both) | **4** | Every finding reproduced by running code. Fixes below; a fourth probe added. *(This cell said “2 found independently by both” until round 3 counted it against §17.2's own prose, which supports one. The audit trail miscounting itself, a third time — §17.5.)* |
| **2** | real-data lens · coherence lens | NOT YET · NOT YET | **3** | **3** + 1 MINOR | Two live defects in the read seam, one measured scale limit, and one false claim in this document's own exit-criteria table. §17.3 |
| **3** | real-data lens · coherence lens | NOT YET · NOT YET | **4** | **3** + 2 MINOR | Two of them defects in round 2's *own fixes*; one an unexercised boundary this document calls its strongest evidence; one an amendment claimed and never made. §17.4 |

### 17.2 Round 1 — what it found

**Three BLOCKING, and the two the reviewers found independently are the same defect from two directions.**

**B1 — `equivalent_to`'s own declaration violated the document's own stated ban, and no design test exercised it.** §1 said *"`endpoint_kinds` cannot name `edge`"* and §2.4.1 said *"any registered kind except `edge`"*; §3.1's `equivalent_to` declared `["entity", "value_set", "edge"]` on both ends, and the probe kit and the NYC probe both carried it verbatim to a green run. **A hard architectural guarantee, asserted twice and contradicted three sections later, in the one family this document ships.**

*Resolved by deciding which rule was right rather than by deleting the mismatch.* The ban was written too broadly: **reification is an edge pointing at an edge *instance*, and that is already impossible** because §2.4.1 restricts an `InstanceRef` to `kind="entity"`. A `kind="edge"` TypeEntry is a *row of the vocabulary*, and two agencies naming the same real relation differently is UC3's collision shape one level up — the case both reviewers named unprompted. §1 and §2.4.1 now say that precisely, and **T3.13** exercises it.

**B2 — `neighbors(node, edge_families=None, namespace=X)` silently dropped every family outside `X` — Cause C inside the read seam.** §4.5 claims `namespace` *"never filters results"*; the first draft's `None` case scoped to it anyway. A reviewer built two families in two namespaces incident on one node and ran the project's own kit: each call found one. **That is the silent per-consumer drop this document names as its primary mechanism (§12), committed by its only read call, on the axis UC3 exists to stress** — and none of the three design tests called `neighbors` with `edge_families=None` at all.

*Resolved by following §4.5's own reasoning to its conclusion:* `None` spans every namespace, and `namespace` is therefore a no-op in that call shape, **stated in §4.1 rather than left to be discovered.** Exercised from three different namespaces in the new probe.

**B3 — §15 claimed a predicate could not be an edge endpoint; it could.** The exclusion lived only in `equivalent_to`'s own declaration, so it was a family author's opt-in. A reviewer declared `same_capability` with permissive `endpoint_kinds` and wrote a predicate-to-predicate edge with **no refusal** — *the `ROADMAP.md` kill row, reached through a door this document had left open while §15 said it was shut.*

*Resolved by making the rule general* (§2.4.1) *and enforcing it at family-declaration time*, so a breaching family cannot be declared at all. **Writing the test for that then exposed the same hole in the instance clause** — a `level="instance"` family declaring `("entity", "edge")` would have reified an edge — which was fixed the same way. Two of the three clauses of §2.4.1 were enforceable-in-principle and unenforced in practice.

**The four MAJOR.**

| # | Finding | Resolution |
|---|---|---|
| M1 | **`Edge.warnings` claimed INTERFACE §5.4's vocabulary *"same values"* and then minted five new ones in prose.** The mirror image of the R3 discipline this document applies carefully to `Refusal.reason` two sections later — *a closed vocabulary that opens by prose is not closed* | New **§2.8**; `INTERFACE.md` §5.4 amended in this change to **sixteen values across four carriers**. One further value was considered and **not** minted: attribute loss is reported by the returned record, as on the type side |
| M2 | **`depth_reached` conflated *"hit a bound"* with *"nothing further to find"*.** A dead end is the common shape in real graphs, and an adapter author reading §4.1's comment literally would have set `complete=False` on nearly every walk | §4.1's field comment and §4.3's table now carry **two separate rows**: ran out of graph (`complete=True`, no `why`) versus cut short (`complete=False`, `why` names the bound). Exercised on a real CMS `deficiency_tag` sink |
| M3 | **Retraction, every capability flag, `include_retracted`, savepoint scope and `known` were specified in prose and executed by nothing** — and both BLOCKING defects were hiding in exactly that unrun half | **[`edges_capability_probe.py`](../tools/edges_capability_probe.py)** added: **34 executed checks** over `retract_edge`, the four flags declined one at a time, the savepoint stamp on writes and its absence on reads, the dead-end walk, the cross-namespace `None` case, and both enforcement layers of §2.4.1 |
| M4 | **`NeighborReport.known` was `int \| None` with no reachable `None`** — a reviewer reported being unable to produce one. Rule-U shape with nothing behind it | Corrected to a plain `int`, citing `INTERFACE.md` §3's own resolution of the same case for `ConsumerReport.known`. `EdgePage.known` (the adapter's) stays `int \| None`, because a store genuinely may be unable to count |

**Four MINOR, all taken:** §6 said *"five flags and one declaration"* for four flags and two declarations; the probe kit gave `Family.level` a default the spec forbids; §7.1 claimed `find_edges` follows `find_types`' uncertainty rule and then deviated from it without saying so (the deviation is right — the frontier is bounded, so the backend genuinely can answer a wider question completely — and is now argued); and §16 cited a §17 that did not exist.

### 17.3 Round 2 — what it found

**Neither reviewer had seen round 1's work.** Both returned NOT YET. Three BLOCKING again, and — the part worth noticing — **two of the three were in the same place round 1's own postmortem said defects hide: the parameter combinations nothing had run.**

**B4 — `direction="in"/"out"` was silently wrong for symmetric families, which is `equivalent_to`'s own shape.** One edge written `src=dpr:borough, dst=dot:borough`; `neighbors(dot:borough, ["equivalent_to"], 1, direction="out")` returned **`known=0, complete=True, nodes=[]`**. A confident, complete, **false negative**, on the only family this document ships, decided by an accident of which publisher wrote the edge first. **[Reproduced]** before it was believed. No design test had ever passed `direction` to `equivalent_to`.

*Resolved:* `direction` filters **directed families only** (§2.2, §4.1). For a symmetric family there is no in and no out, so both orientations return. The alternative — refusing `direction != "both"` when a symmetric family is in scope — was rejected because it breaks a mixed query, which is the ordinary case.

**B5 — `depth_reached` misreported a genuine dead end under the API's own default `direction="both"`, defeating round 1's M2 fix.** A one-edge graph walked to depth 2 reported `depth_reached=2`: the level-2 frontier contains the node reached at level 1, that node is incident on the edge the walk *arrived* on, and `depth_reached` was set whenever the scan returned *any* record. **Round 1's dead-end rule was therefore true only for `direction="out"` — the one direction the probe written to test it happened to hard-code, and the one direction nobody defaults to.**

*Resolved:* `depth_reached` counts levels that found something **new**. Both directions are now exercised.

**B6 — this document's own §16 said the loop had run two rounds when §17 recorded one.** The exit-criteria table — *the section a reader checks before trusting the rest* — carried a factual claim contradicted three lines below it, because it was written optimistically ahead of the round it described. **[Verified against `git log`.]** *Resolved:* §16 now reports the live state, including that the stop rule is not yet met.

**The three MAJOR and one MINOR.**

| # | Finding | Resolution |
|---|---|---|
| M5 | **The depth cap bounds hops, not degree — and degree is unbounded.** A reviewer went and counted: `erm2-nwe9` carries **9,738,128 of 22,294,072 rows on `agency = NYPD`**, so the Phase 3 ingestion edge this row exists to unblock makes `neighbors(agency:NYPD, depth=1)` ≈ 9.7M edges in one unpaged call. §4.2 had argued the danger was a *depth-3* walk; a single hop on the fixture's own data is already worse | §4.2 rewritten around the measured number. Two behaviours specified: the registry **exhausts the adapter's pages per level** (300 edges from 64-row pages, `complete=True`), and a deployment **may configure an assembly bound** whose breach is `complete=False` with a `why` (2,000 edges, bound 500 → `known=500, complete=False`). **Not paging** — no cursor reaches the caller, because R13 stands. **Q21** routes the real question to R13's own owner |
| M6 | **`indexes_edges_by_family=False` was never implemented and never tested**, while §7.1 spent more words justifying its deliberate deviation than any other flag. §17.2's claim that round 1 declined *"all four flags one at a time"* was false | Implemented in the kit and probed. **And writing that test found a second half missing:** the store-side degradation existed, the **registry-side narrowing §7.1 promises did not**, so a family-filtered query on such a store returned the unfiltered set. The claim in §17.2 is corrected below |
| M7 | **The `types.py` change carried stale prose.** Adding the three EDGES values to `REFUSAL_REASONS` left `Refusal`'s docstring and its `ValueError` both saying *"fifteen"* — and **`check_spec_drift.py` could not catch it**, because it diffs field and parameter *names* and never enum *contents* | Both corrected — the error message now derives the count from the tuple. **And the checker's blind spot is closed:** it now compares `INTERFACE.md` §5.12's enumerated list against `REFUSAL_REASONS`, contents **and** the count word in the prose. **Verified to bite**: a smuggled value and a stale count both fail it |
| M8 | **§4.4 claimed `NeighborReport` was *"the first Rule-K carrier in this project that can be `True`"*.** False: `registry.py`'s `list_types` computes `complete=bool(page.complete and not applied)`, so an unfiltered census — the exact call `INTERFACE.md` §5.6 recommends — is already `complete=True` | Overclaim removed. The comparison that holds is with the two carriers that are *always* `False`, and it reads that way now |
| m | §6 justified having no uniqueness flag by citing `PACKAGE.md` §3.5's **G1**, which is defined narrowly as uniqueness *in the type store* | Rewritten to stand on §4.2's `proposal_id`/`event_id` precedent alone, which is where the argument actually lives |

### 17.4 Round 3 — what it found

**Four BLOCKING. Two of them were defects in round 2's own fixes**, which is the single most useful thing this loop produced.

**B7 — the assembly bound double-counted re-found edges, dropping real data and lying about why.** Round 2 added the bound; round 3 walked a hub whose leaves are also connected to each other — *the ordinary topology of the 9.7M-degree node §4.2 is built around*. **[Reproduced]**: 19 distinct edges under a bound of 20 returned **15**, `complete=False`, and a `why_incomplete` naming a bound nothing had crossed. The check compared the bound against each *raw page*, and a depth-2 frontier legitimately re-finds the edges it arrived on. **A circuit breaker that fires early and then explains itself falsely is worse than no circuit breaker**, because the deployment reading it concludes the bound is too tight when the store had the whole answer.

**B8 — the bound was opt-in, so the default was the unbounded fetch R13 exists to prevent.** §4.2 had measured the hazard, specified a mitigation, and left it switched off. It is now on by default; disabling it is a deliberate act.

**B9 — `retract_edge` inherited the savepoint durability warning instead of stamping it.** §6.2 says the stamp is applied at *every* write call site and names `retract_edge`. **[Reproduced]**: retracting an edge the host had already committed returned **no warning at all** — a borrowed-connection write that looked exactly as durable as an owned one. This is `PACKAGE.md` §3.4 primitive 3 note 2's *own recorded bug class*, arriving one layer up.

**B10 — §4.3's behaviour table still said `known=None, never 0`** about `NeighborReport`, which §4.1 had corrected to a plain `int` in round 1, with an argument. Two sections, opposite instructions, and the table is the part a reader consults.

**The three MAJOR and two MINOR.**

| # | Finding | Resolution |
|---|---|---|
| M9 | **The three adapter primitives were never instantiated by any probe.** §7.1 calls the three-primitive count *"the strongest evidence that §2.3's decision was right"* and `PACKAGE.md` §3.1 makes the boundary a testable rule — yet the kit's `EdgeStore` stored and returned `Edge`, the rich façade object. **The boundary this document leans on was contradicted by its own runnable artifact** | `EdgeStore` now stores `EdgeRecord`, takes an `EdgeQuery` and returns an `EdgePage`; `assert_adapter_boundary()` checks it by source inspection the way `C0-04` does. **The rewrite paid immediately**: landing the `EventRecord` amendment tripped `C0-04` on a *comment* naming the forbidden identifier |
| M10 | **The `EventRecord.edge_id` amendment was claimed in two places and made in neither.** §5.2 specified it and §7.1 said *"one amendment to an existing shape… it costs the reference backends one nullable column"*, and it had reached neither `PACKAGE.md` §3.3 nor `adapter.py`. `check_spec_drift.py` could not see it: the doc and the code agreed with **each other** on the old shape, so a *third* document asserting a change nobody made is invisible to a two-way diff | Landed in both, with the three `event` values. The checker's limit is recorded rather than papered over — it compares two sides, and this was a claim from a third |
| M11 | **§17.1's own round-1 count said two defects were found by both reviewers; §17.2's prose supports one** | Corrected. It is the **third** self-accounting error in this section |
| m | `retract_edge` on a missing `edge_id` reused `edge_family_unknown` | `unknown_edge`, the nineteenth value of `INTERFACE.md` §5.12, added in this change per R3 |
| m | Self-loops and the triangle case for `at_depth` were reachable and unstated | Both stated in §4.1 and exercised |

### 17.5 Convergence — honestly, and the loop did **not** converge

**Three rounds, six fresh reviewers, six NOT YET verdicts.** The brief's stop rule was *two consecutive clean rounds, or three rounds plus an honest convergence note*. **The second branch applies.** This is the same close rows 3c and 3d took, and it should be read the same way: as a fact about the process, not a formality.

**What the defect class did over three rounds, which is the only real evidence of convergence:**

| Round | The defects were… |
|---|---|
| 1 | **The rules were not enforced.** §2.4.1 stated three clauses; two were guarded only by each family's own declaration. A stated rule with no enforcement point |
| 2 | **The rules were enforced, on the wrong axis.** Capabilities were probed on default parameters; the defects were in the parameters on default capabilities |
| 3 | **The fixes were wrong at the edges, and the evidence did not match the claim.** Two defects inside round 2's own fixes; one boundary asserted and contradicted by the probe; one amendment claimed and never made |

**That is narrowing** — from *"the mechanism does not exist"* to *"the mechanism is right and one edge of it is wrong"* — and it is the same trajectory row 3d recorded. It is **not** convergence, and three rounds of this loop have not once produced a clean reader.

**The residual risk, stated rather than eliminated.** Every round found something in the part the previous round had not run, *including the round that was added specifically to close that gap*. **[Inferred]** a fourth synthetic round would find a fourth such corner rather than none — and the honest reading of that is not that the loop should continue, but that **prose-plus-probe review has a floor, and this document has reached it.** The next signal with real information is the same one ruling **R15** identified for row 3d: **a real consumer over a real store.** For EDGES that is beacon's slice 1 building `neighbors` against `work_links`, and its findings should be routed back the way beacon 21.1's were.

**Two things this loop did that are worth keeping.** Every one of the ten BLOCKING findings was **reproduced by running code before it was believed**, and three of them were defects in the *previous round's fix* — which is only visible because each round got a reader with no stake in the last one. And the loop twice caught **this document lying about its own verification** (§16's round count, §17.1's reviewer count, §7.1's phantom amendment). *A document that self-reports its own evidence needs an adversary pointed at the self-report, not only at the design.*

### 17.6 What the loop says about the process





**Round 1: two BLOCKING defects and one MAJOR were in the half of the design nothing executed**, and the reviewer who said so said it as a *pattern* rather than a finding: *"the untested `edge_families=None` path is proof that 'asserted, not run' is where this document's actual defects were hiding."* That is 3c's lesson arriving one row later in a new shape — **not "reading finds less than running", but "the parts you did not run are exactly where the defects are"** — and the fourth probe exists because of it.

**Round 1's second lesson: two of its three BLOCKING findings were the same mistake.** §2.4.1 stated three clauses; two were enforced only by each family's own declaration, which is *a guard that depends on every future author remembering* — the class of protection this project refuses elsewhere by making `merge_types`' refusal #2 non-overridable. The document had written the rule and left the enforcement to good manners.

**Round 2 is the uncomfortable one, and it is the reason this section exists.** The fourth probe was added *specifically* to close round 1's unrun half — and **round 2 found two more BLOCKING defects in the parameter space that probe still did not cover.** `direction` was never passed to a symmetric family; the dead-end test hard-coded the one direction that structurally could not expose the bug. So the lesson sharpens again:

> **Adding a test for the gap you were told about does not close the class.** Round 1's probe tested *the capabilities*, one at a time, on the default parameters. Round 2's defects were in *the parameters*, on the default capabilities. Coverage of a surface is two-dimensional and each round had only walked one axis.

**And a third thing, which is about this document rather than the design.** One of round 2's BLOCKING findings was that **§16 claimed the loop had run twice when §17 recorded once** — the summary table lying about the evidence section three lines below it. It was written ahead of the fact and never corrected. *A document that self-reports its own verification is a document that can drift from its own verification*, and the only defence is that the table names the section a reader can check. Which is what happened.

---
