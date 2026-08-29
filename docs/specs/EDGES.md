# EDGES — typed relationships over the registry

**Version:** `v0` — **unstable.** Every name, field and return shape here may change without a deprecation path. Standing constraint 4.
**Status:** Draft, 2026-08-29. Satisfies `ROADMAP.md` row **#4**. Unblocks Tenshen slices 1–2 (the read seam, and the grounding bundle's `relations` slot).
**Assumptions:** *written against the 2026-08-28 assumptions; see docs/decisions/* — specifically [`decisions/2026-08-28-assumptions-in-lieu-of-office-answers.md`](../decisions/2026-08-28-assumptions-in-lieu-of-office-answers.md).
**Rulings this document carries:** **R7** (`equivalent_to` is an edge, and EDGES v0 must carry type-level edges) · **R13** (the façade does not page in v0) · **R5** (`transaction_scope`, inherited by the edge store) · **R3** (`Refusal.reason` is closed — three values added to [`INTERFACE.md`](INTERFACE.md) §5.12 by this change).
**Claim tags:** **[Observed]** seen directly · **[Inferred]** a reasonable read · **[Assumed]** believed, untested.

**This row is a spec. No implementation lands with it.** The design tests in §9–§11 are walk-throughs driven through real data by throwaway probes ([`docs/tools/`](../tools/)), not by a shipped edge store. Where a probe stands in for a store, it says so.

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
- **No reification.** An edge is not a node. There is no edge-about-an-edge in v0, and `endpoint_kinds` cannot name `edge`.
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
    warnings:     list[str]         # INTERFACE §5.4's vocabulary. Same values, same carriers rule
    attr_schema_version: int | None # the payload schema in force when this was written. §2.5
```

**`namespace` on the edge is the *family's* namespace, and the endpoints keep their own.** A `dot` consumer may write an `equivalent_to` edge (family registered in `default`) between a `dpr` type and an `oti_311` type. Three namespaces, one edge, no contradiction — because the field answers *"whose word is `equivalent_to`?"*, not *"whose data is this?"*. **Stated because the obvious alternative — deriving the edge's namespace from its endpoints — has no answer when the endpoints disagree, which in UC3 is the normal case.**

**There is no `direction` field.** `src` and `dst` are ordered; whether the order carries meaning is the family's business (`symmetric`), not the edge's.

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

**No new call in `INTERFACE.md` §5 is required to manage families.** That is the test of whether this decision is right, and it passes: the thirteen calls stay thirteen.

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

**This is `work_link_types` generalised — and UC1 is cited as a test, not a source.** `work_link_types` has `is_symmetric` and `inverse_label`; two of the five keys above match it, and the other three (`level`, `endpoint_kinds`, `payload_schema`) come from data beacon does not have: CMS forces `endpoint_kinds` (a `citation` edge must not accept a `facility` at the tag end — §10), and UC3 forces `level` (`equivalent_to` runs between types, and beacon has no type-level edge at all — §11). The direction of the borrowing is checked in §15.

**The win this closes, named in `INTERFACE.md` §9 contortion 1.** That contortion says v0 *"cannot stop two types disagreeing about direction"* and *"cannot enforce that a symmetric type has no inverse label"*. With the schema above in `warn` or `enforce` mode, `propose_type(kind="edge", attributes={"symmetric": True, "inverse_label": "blocked_by"})` is a cross-field rule — and `PACKAGE.md` §5.6 says plainly that `FieldSpec` is per-field and **does not validate cross-field rules**. **So contortion 1 is half closed, not closed:** the fields now have a declared, versioned, described home (that is real), and the *"symmetric implies no inverse"* rule still has nowhere to be checked. It is checked by the registry at family-approval time as a documented rule of this section, not by the schema mechanism — and that is one rule this document asks `approve()` to know, recorded as **Q13** in §14 because it is a small crack in `PACKAGE.md` §5.6's own boundary.

#### 2.4.1 `endpoint_kinds`, and the rule that decides what a value set may be

> **A `level="instance"` family accepts only `kind="entity"` endpoints. A `level="type"` family accepts any registered kind except `edge`.**

Both halves earn their keep on real fixtures, in opposite directions:

- **Instance level, entities only.** Only an entity has instances. A `predicate`'s extent is a set of *types*; a `value_set`'s members are *values*; an `edge` family's instances are edges, and §1 rules out reification. So `citation:42 --has_severity--> scope_severity_code:J` is **refused** (`endpoint_kind_mismatch`) — and that refusal is the right answer for UC2, because it stops the registry from turning a column of 419,479 property values into 419,479 edges, and stops it from having to know what a *value* is, which `INTERFACE.md` §2.1 refuses on purpose and ruling **R8** deferred to Phase 3. **Severity is a property of a citation, and this document does not store node properties (§1).**
- **Type level, any kind.** `dpr:value_set:borough equivalent_to dot:value_set:borough` is exactly UC3's W2 case, and the endpoints are `value_set` entries. Forbidding `value_set` here would make the one relation R7 exists to provide unexpressible on the data that forced it.

**So a `value_set` IS a legal edge endpoint — as a type, never as an instance.** Two fixtures pulling opposite ways, one rule, no exception clause. The decision the brief asks for in §10 is this sentence.

**`equivalent_to` additionally requires `src.kind == dst.kind`** — a family-level constraint beyond `endpoint_kinds`, stated in §3.1 rather than here, because it is that family's semantics and not a general mechanism.

### 2.5 `payload_schema`, and the dependency on R10 that this document cannot discharge

`Edge.attributes` carries the payload a family declares — `role` on a stakeholder edge, `description` and a join basis on an inferred one. Validation is `PACKAGE.md` §5's mechanism, and **the key is the problem**: §5.2 keys an `AttributeSchema` by `(namespace, kind, version)`, one per **kind**. Every edge family shares `kind="edge"`, and their payloads do not share a shape — `task_stakeholders` has `role` and a NOT-NULL `source`; `person_links` has none; `meeting_attendees` has six.

That is **exactly** `PACKAGE.md` §5.6's recorded failure, on which ruling **R10** was made: *attribute schemas keyed per name as an override — YES, row 3e.* R10 is ruled and queued **after** this row.

**So EDGES v0 specifies `payload_schema` and declares it inert.** In v0:

1. `payload_schema` names an `AttributeSchema` keyed `(namespace, "edge", <family name>)` — **R10's shape, written down here so 3e has a caller**.
2. Until R10 lands, no such schema can be stored, `payload_schema` is `None` on every family, and `Edge.attributes` is opaque — which is `PACKAGE.md` §5.3's default (`mode="off"`) anyway, so nothing regresses.
3. `attr_schema_version` on the `Edge` is `None` for every v0 edge, and `None` already means *"written with validation off"* (`INTERFACE.md` §2.1). No new meaning.

**Recorded as a real ordering cost, not hidden:** the one part of the edge model that needs a ruling already made cannot use it, because the ruling was sequenced behind this row. Nothing here asks for the order to change — Tenshen's slices are what row #4 is early for — but a reader should know that **edge payload validation begins in 3e, not here.**

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

**There is no `delete_edge` in v0, and no reinstatement.** Deletion is out because nothing else in this project deletes. Reinstatement is out because ruling **R11** is already specifying `reinstate` for types in row 3e, and inventing a second, differently-shaped reinstatement for edges one row ahead of it is how two calls come to mean nearly the same thing. **Recorded as Q14** — 3e should decide whether `reinstate` covers edges.

**A retracted edge is invisible to `neighbors` by default** and reachable with `include_retracted=True`, mirroring `list_types(include_retired=)` — including its Rule K consequence: a default that hides things sets `complete=False` (§4.3).

### 2.7 A dangling endpoint is a fact, not an error

`src` or `dst` may reference a type that is not registered, or an instance that no longer exists. `put_edge` does **not** check that endpoints exist, and `neighbors` returns them.

**Why, and it is `PACKAGE.md` §3.4 primitive 10's argument transposed.** `put_consumer` deliberately accepts a `gate` naming a predicate that does not exist, *because a consumer gating on a word nobody registered is precisely mechanism C, and refusing the registration would hide it.* The same holds here: an edge pointing at a type nobody registered is the ingestion layer's mistake made visible; refusing the write moves the failure into a log nobody reads.

Two consequences, both stated:

- **`endpoint_kind_mismatch` can only fire when the endpoint's type IS registered.** On an unregistered endpoint the registry cannot know the kind, so it does not guess: the edge is written and carries `warnings: ["endpoint_type_unregistered:<namespace>:<kind>:<name>"]`. Rule U — a positive claim about a mismatch requires having looked. This is the same shape as `gate_unregistered:<gate>` (ruling R8) and deliberately so.
- **Orphan sweeping is not this document's job.** Beacon's `purge_orphan_links` **deletes** rows whose endpoint it does not recognise, and **[Observed, beacon spec §10.4]** its `else` branch judges every non-`task` endpoint against the project id set, so live `report` edges written by `decisions/actions.py` are purged daily. That is recorded as contortion **E5** in §9. This document's position: an orphan is `retract_edge`'s subject, never a `DELETE`.

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

**Family-specific constraint: `src.kind == dst.kind`.** An `entity` is not equivalent to a `value_set`; `facility ≡ deficiency_corrected_status` is a category error, not a claim. A cross-kind attempt is refused `endpoint_kind_mismatch` with `detail={"src_kind":…, "dst_kind":…}`. `predicate` is excluded from `endpoint_kinds` entirely: two predicates being "equivalent" is a claim about extents, and `merge_types`' non-overridable refusal #2 exists precisely because that claim must be made from byte-identical extents or not at all.

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
    depth_reached:     int                  # < depth_requested when the walk stopped short
    direction:         str
    families_searched: tuple[str, ...]      # what was ACTUALLY consulted. §4.4
    edges:             tuple[NeighborEdge, ...]
    nodes:             tuple[NodeRef, ...]  # distinct endpoints reached; origin excluded
    known:             int | None           # None = the store cannot count. NOT 0. Rule U
    complete:          bool                 # §4.3 — and it CAN be True. §4.4
    why_incomplete:    str | None
    warnings:          tuple[str, ...]

NeighborEdge:
    edge:      Edge
    at_depth:  int          # 1 = incident on the origin. §4.4 — this field is not decoration
```

`namespace` is **required and keyword-only**, and it names the namespace `edge_families` are resolved in — *not* the origin's, which the origin carries itself (§2.1). Making it required rather than defaulting to `"default"` is deliberate: UC3's whole subject is that `"default"` is a wrong answer nobody notices.

### 4.2 The depth cap is **2**, and it is R13's consequence rather than a separate decision

> **`depth` may be `1` or `2`. `depth >= 3` raises `ValueError`.**

`ValueError`, not `Refusal` — it is a caller error like `INTERFACE.md` §5.4's empty definition, and R3's closed vocabulary should not grow a value for a typo.

**Why a cap at all.** R13 rules that the façade does not page in v0, *because Rule K has no answer yet for what `known` means on a page.* An unpaged result must therefore be bounded by something else, and depth is the only bound available that a caller can reason about. Fan-out compounds: a node of degree *d* returns up to *d* edges at depth 1 and up to *d²* at depth 2. On beacon's `person_links` at founder scale that is tens; on UC3's 22.3M-row 311 dataset a naive depth-3 walk from a common node is a result nobody can hold. **The cap and R13 are one decision, and if R13 is revisited the cap should be revisited in the same change.**

**Why 2 and not 1.** Because 2 is the smallest cap that serves a traversal a shipped consumer already wants. Beacon's flagship query is *"who is blocking anything due this week?"* — `task --blocks--> task --stakeholder--> person`, two hops **[Observed, beacon spec §5.5 query 1]** — and `deadline_cluster_service` already walks the first hop by hand and stops **[Observed, beacon spec §2.7]**: *"it reaches the blocker task and goes no further… the hop it is missing is the one that turns 'what is blocking this' into 'who is blocking this'."* A cap of 1 ships a read seam that cannot answer the query the read seam was justified by.

**Why not 3.** Nothing in the three fixtures needs it. CMS's deepest chain is `citation → survey → facility`, which is 2. UC3's cross-agency joins are 1. The moment a real consumer needs 3, the cap moves *with that consumer's evidence* and with an answer for what bounds the result — which is Phase 3's paging decision (R13), not this row's.

**The cap is not a performance claim.** A depth-2 walk over a high-degree node can still be large, and §4.3's truncation is how that is reported honestly.

### 4.3 Behaviour when uncertain

| Situation | Result |
|---|---|
| The registry has no edge store | **`Refusal(reason="edge_store_absent")`**. Never an empty report — an empty `NeighborReport` reads as *"this node has no neighbours"*, which is Rule U's forbidden empty list in the one call that would be believed |
| A named family in `edge_families` is not a registered `kind="edge"` entry | **`Refusal(reason="edge_family_unknown", detail={"families": [...]})`**. The whole call, not a partial answer: a caller that names a family and gets a report back is entitled to believe the family was searched, and a typo'd name returning a clean empty set is mechanism **C** committed by the read seam |
| A named family exists but is **retired** | Not a refusal. It is searched (its edges were not deleted), and the report carries `warnings: ["edge_family_retired:<name>"]` |
| `edge_families=None` | Every family the store can answer. `families_searched` echoes exactly which, and `complete` is about *those* — §4.4 |
| The store cannot count | `known=None`, never `0`. `PACKAGE.md` §3.4's uniform uncertainty rule |
| The walk stopped short of `depth` (a bound, a scan limit, a store that timed out) | `depth_reached < depth_requested`, `complete=False`, and `why_incomplete` names it. **Never a silently shallower answer** |
| `include_retracted=False` (the default) and a retracted edge was suppressed | `complete=False`, because a default that hides things is `list_types`' rule (`INTERFACE.md` §5.6) |
| `node` is an `InstanceRef` whose type is not registered | Not an error (§2.7). The walk proceeds and the report carries `warnings: ["origin_type_unregistered:<ref>"]` |
| The edge store is `transaction_scope="savepoint"` and this is a **read** | **Nothing is added.** `PACKAGE.md` §3.4 primitive 3, note 2: a read says nothing about durability in either direction, because the registry cannot know whether the host has committed |

**No `UnknownNode` exception.** `INTERFACE.md` §5.1 raises `UnknownType` rather than returning an empty `ConsumerReport`, and the reasoning was that an empty report is false reassurance. It does not transpose: the registry **has no node store** (§1), so it cannot distinguish *a node with no edges* from *a node that does not exist*, and raising would require inventing a fact. The honest form is a report with `edges: ()`, `known: 0` and a `warnings` entry when the origin's type is unregistered. **This is a place where two rules of this project point opposite ways and the tie is broken by which one requires the registry to know something it does not.**

### 4.4 `complete` **can be `True`** — the first Rule-K carrier in this project that can be, and the caveat that makes it honest

`ConsumerReport.complete` is *always* `false` because consumers are **registered, not discovered** — the registry cannot know about a code path nobody told it about. `Resolution.complete` is always `false` because near-misses are scored in one namespace. **Edges are different in kind: an edge is a stored row.** There is no edge that exists in the store and is invisible to a query over it. So when the store answered without truncation, `complete=True` is a true statement and Rule K should let it be said.

**The caveat, and it is not small.** "Complete" is over `families_searched` and over the **edge store**, never over the host's relationships. Beacon has seventeen bespoke join tables plus three shapes of edge **[Observed, beacon spec §2.2]**; an adapter that maps three families and not the other fourteen answers `complete=True` about a graph that is four-fifths invisible. That is why `families_searched` is a required field of the report rather than an echo of the argument: **`complete=True` is only readable next to the list of what was searched**, exactly as ruling R12 requires a conformance verdict to be read next to its coverage line. A `NeighborReport` printed without `families_searched` is the same category of claim as a conformance run printed without its coverage — *"a completeness claim without its scope line is not a claim"*.

**`at_depth` is the second thing that keeps this honest, and it is `equivalent_to`'s problem specifically.** §3.1 makes `equivalent_to` symmetric and **not transitive**. A depth-2 walk from `dpr:borough` over `A≡B` and `B≡C` returns `dot:borough` — reachable, and **not asserted equivalent to the origin**. Without `at_depth` a caller renders three boroughs as one equivalence class, which is the transitive closure the family refused to license, manufactured by the read seam.

> **`neighbors` returns reachability. It never returns entailment.** A consumer that treats a depth-2 result as a depth-1 claim has made the inference itself, and the report gives it every means not to.

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
    created_by:        "seed" | "ai" | "user"      # INTERFACE §2.1's vocabulary, unchanged
    confidence:        float | None         # None = nothing scored it. NOT 0.0 — Rule U
    evidence:          list[Evidence]       # INTERFACE §2.8, unchanged, incl. external_doc + Citation
    source_version:    str | None           # the SOURCE's own version. §5.3
    retracted_by:      str | None
    retracted_at:      datetime | None
    retract_reason:    str | None
    history:           list[ProvenanceEvent]        # append-only. INTERFACE §5.8
    history_why:       str | None           # why `history` is empty, when it is. Rule U
```

**Why not `Provenance` verbatim.** `Provenance` carries `proposed_by`, `approved_by`, `approved_at` and `model_tier`, and `INTERFACE.md` §2.4 makes a rule of one of them: *"`approved_by` is never null on an `active` type… a registry that leaves the field blank invites a reader to assume a human signed off."* §2.6 above establishes that edge **instances** have no approval loop. Carrying `approved_by` on an edge therefore forces one of two bad answers on every single edge ever written: `None`, which breaks the §2.4 rule the field exists for, or a manufactured `"auto:…"` that asserts an approval nobody performed. **A field whose only honest value is a lie should not be on the shape.** Narrowing is the honest move, and it is the same move `INTERFACE.md` §5.2 makes when it gives `PredicateEntry` its own shape rather than reusing `TypeEntry`.

**`model_tier` is deliberately absent too, and that is a live weakness.** `INTERFACE.md` §2.7 makes tier a product parameter because a cheap tier inverted the CMS severity scale silently. Beacon's `infer_person_relationships` classifies person pairs with **Haiku** and auto-applies at ≥0.7 **[Observed, beacon spec §2.5]** — an AI-written edge from a named cheap tier, which is 0.5's exact shape one level down. The tier is recoverable from `created_by_actor` only by convention (`"ai:haiku_classifier"`), which is not a field. **Recorded as Q15**: should `EdgeProvenance` carry `model_tier`, and should there be a tier gate on AI-written edges the way §2.7 gates auto-approval? This document does not take it, because a tier gate on a weekly batch job is a product decision about beacon's behaviour, not a storage shape.

**`confidence` is `float | None` and `None` is not `0.0`.** Beacon types it `Float` nullable on both `WorkLink` and `PersonLink` **[Observed]**, and `interview_service` selects rows *"with a null `relationship_type` or confidence below 0.7"* — so null confidence is a live, meaningful state in the one host this must sit over. Coercing it to `0.0` would turn *"nothing scored this"* into *"scored zero"*, which is `INTERFACE.md` §5.3's `confidence: None ≠ 0.0` rule verbatim.

### 5.2 Append-only, and what a correction is

`INTERFACE.md` §5.8: *"`history` is append-only: a correction is a new `ProvenanceEvent`, never an edit."* Unchanged for edges, with one addition that the shape forces.

`PACKAGE.md` §3.3's `EventRecord` has `kind`, `name` and `proposal_id` and **no slot for an edge**. So edge events have nowhere to go in the existing event store. **The amendment is one nullable field:**

```python
@dataclass(frozen=True)
class EventRecord:
    ...
    edge_id: str | None = None      # the edge this concerns, if any. EDGES §5.2
```

with three new `event` values — `edge_added`, `edge_retracted`, `edge_amended` — and the same rule as everything else in that vocabulary: the adapter **stores** the string and never judges the transition (`PACKAGE.md` §3.1).

**Corrections in practice.** Changing an edge's `confidence` after a re-classification is a new `edge_amended` event carrying the old and new values; it is not an edit of the first event, and the first event's `created_by_actor` stays whatever it was. Beacon's weekly job re-running over the same pair is exactly this case, and today it has no trail at all.

### 5.3 `source_version` — taken here, and the asymmetry recorded

`INTERFACE.md` §10b.5, contortion 12: a type derived from a 2017 snapshot and one derived from a daily feed record identically, because `Provenance.created_at` is when *we* wrote the row. The one-line fix — `source_version: str | None` — was collected for v1 and not taken.

**It is taken here**, on `EdgeProvenance`, because a cross-agency edge is *entirely* a claim about two source snapshots. `dpr:tree:1234 --concerns--> oti_311:service_request:5678` asserted from a 2017-10-04 tree census and a 311 feed updated 2026-08-28 **[Observed, dataset `data_updated_at` values]** is a different claim from the same edge over two current feeds, and the difference is nine years of trees.

**The asymmetry this creates is recorded rather than smoothed:** `EdgeProvenance` has `source_version` and `Provenance` does not. Two shapes, one concept, one of them missing the field — which is drift of the kind this repo has caught six times. **Q16**: should `Provenance` gain `source_version` in row 3e, closing it? The recommendation is yes; it is additive, defaults `None`, and 3e is already amending that shape for R6/R10/R11.

---

## 6. Capability flags for the edge store

In `PACKAGE.md` §3.2's style: every `False` flag carries a sentence in `Capabilities.why`, surfaced verbatim wherever a result would otherwise imply a fact. Five flags and one declaration, added to the existing `Capabilities`.

```python
    stores_edges:              bool     # the store holds edges at all
    stores_edge_events:        bool     # append_event with an edge_id is durable
    indexes_edges_by_family:   bool     # a family-filtered neighbour query need not scan the node's edges
    stores_edge_attributes:    bool     # an arbitrary payload dict survives a round trip
    edge_transaction_scope: Literal["owned", "savepoint"] = "owned"    # R5, §6.2
    edge_attribute_projections: frozenset[str] = frozenset()           # U3's shape, §6.3
```

| Flag | `False` means | `why` example | What the registry does |
|---|---|---|---|
| `stores_edges` | there is no edge store behind this adapter | *"this backend is a type registry only; no table holds relationships"* | **every** edge call returns `Refusal(reason="edge_store_absent")`. Never an empty report — §4.3 |
| `stores_edge_events` | an edge event cannot be persisted | *"`work_links` has no event table and beacon owns the schema"* | `retract_edge` **succeeds** and warns `retracted_without_event_trail:<why>` (§2.6); `provenance(edge).history == []` with the `why` |
| `indexes_edges_by_family` | a family filter costs a scan of the node's edges | *"`work_links.relationship` is free text with no index"* | correctness is unchanged — the registry filters above the store. But a scan may hit a bound, and then `depth_reached < depth_requested`, `complete=False`, `why_incomplete` = this sentence |
| `stores_edge_attributes` | an arbitrary payload key does not round-trip | *"`work_links` has `description` and `confidence` as columns and no JSON blob"* | `Edge.attributes` returns **only** the keys in `edge_attribute_projections`, with the `why` for the rest. Never a silently lossy write — `PACKAGE.md` §3.4 primitive 4's rule |

**Two flags are NOT added, deliberately.** There is no `enforces_unique_edge` and no `edges_transactional`. `PACKAGE.md` §3.5's two non-negotiables (**G1** uniqueness, **G2** atomicity) already bind the whole adapter, and an edge store that is not transactional is not a conformant adapter — the guarantee does not fragment by table. What *is* different is **what G1 is over**: the type store's key is `(namespace, kind, name)`; an edge's key is `edge_id`, generated above the store (`PACKAGE.md` §4.2's rule), so uniqueness is trivially satisfied and asserts nothing interesting. **There is deliberately no uniqueness constraint on `(family, src, dst)`** — see §6.1.

### 6.1 Why duplicate edges are permitted, and what that costs

Two `blocks` edges between the same pair, written by a human in March and by the classifier in August, are **two facts with different provenance**, not one fact written twice. A uniqueness constraint on `(family, src, dst)` would force the second write to either fail or overwrite the first — and overwriting is an edit of a provenance-bearing record, which `INTERFACE.md` §5.8 forbids.

**The cost, stated:** `neighbors` may return the same pair twice, `known` counts edges rather than distinct neighbours, and a caller that wants distinct nodes reads `NeighborReport.nodes` (which *is* deduplicated) rather than counting `edges`. **[Observed]** beacon's `work_links` has no unique constraint on its endpoint columns either, so this matches the one host that exists; that is corroboration, not the reason.

### 6.2 `edge_transaction_scope` — R5, and the rule that stops it lying

Ruling **R5** gives `transaction_scope: "owned" | "savepoint"`. The edge store may be a different store from the type store (a host-owned edge table beside a package-owned registry), so it gets its own declaration — with one binding rule:

> **When the edge store and the type store share a connection, `edge_transaction_scope` MUST equal `transaction_scope`. A `Capabilities` that declares two different scopes on one connection is non-conformant.**

Otherwise the adapter is claiming that half its writes are the host's to commit and half are its own, on one transaction, which is not a thing that can be true. When they are genuinely two connections, the two may differ, and then **the atomicity of a write that touches both is gone** — approving an `equivalent_to` family and writing the first edge are no longer one transaction. That is a real limit and it is stated rather than papered over: **a two-connection deployment does not get G2 across the seam**, and the adapter says so in `why["edge_transaction_scope"]`.

Under `"savepoint"`, an edge write result carries `not_durable_until_host_commits:<why>` — `INTERFACE.md` §5.4's existing warning value, unchanged, on one more carrier. **No new warning value is needed**, and the row-3d lesson applies verbatim: it is stamped at the *write* call sites (`add_edge`, `retract_edge`) and **not** on `neighbors`, because a signal that never turns off is noise.

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
**Uncertainty:** the same page rule as `find_types`. A filter the backend cannot apply returns `complete=False` with a `why`, **never** a filtered-looking empty page. When `indexes_edges_by_family=False` and `q.families` is set, the backend may return the node's edges unfiltered with `complete=True` and let the registry filter — that is honest, because the page it returned *is* complete for what it was able to ask.

**No fourth primitive for retraction, and no fifth for counting.** Retraction is `put_edge` with a changed `status`; counting is `EdgePage.known`. Both were considered and dropped, because a primitive that only exists to express a policy transition is a policy inside the adapter.

**One amendment to an existing shape:** `EventRecord.edge_id: str | None = None` (§5.2). Additive, defaulted, and it costs the reference backends one nullable column.

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
