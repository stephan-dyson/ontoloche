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
{"type": "task",   "id": "77", "note": "blocks (hop 1, confidence 0.82)"}
{"type": "person", "id": "7",  "note": "task_stakeholder (hop 2)"}
```

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

**Method.** [`docs/tools/edges_cms_probe.py`](../tools/edges_cms_probe.py) reads the checked-in 400-row sample, builds the three families and every edge through `edges_probe_kit`, and compares every count against the **frozen** ground truth. `py docs/tools/edges_cms_probe.py` → `ALL CHECKS PASSED`.

| # | Expected | **Observed** | Verdict |
|---|---|---|---|
| T2.1 | PASS | three `level="instance"` families, `endpoint_kinds` all `("entity",)`, none symmetric, each with an `inverse_label` | **PASS** |
| T2.2 | 400 / 69 / 400, 92 distinct | nodes: facilities **10**, surveys **69**, citations **400**, tags **92**. Edges: `issued_during` **400**, `conducted_at` **69**, `cites` **400**, distinct `cites` destinations **92** | **PASS — every pre-registered number** |
| T2.3 | sums to 69 and 400 | summed over all ten facilities: **69** surveys at depth 1, **400** citations added at depth 2. One report: `known=47 complete=True depth_reached=2 families_searched=('conducted_at','issued_during')`, `at_depth ∈ {1,2}` | **PASS** |
| T2.4 | facility in two hops | `neighbors(citation#0, [...], 2, direction="out")` → `["cms:entity:survey#275012|2025-12-16|Health", "cms:entity:facility#275012"]` | **PASS** |
| T2.5 | REFUSED | `Refusal(reason="endpoint_kind_mismatch", detail={"endpoint": "dst", "problem": **"level"**, "family_level": "instance", "node_level": "type", …})` | **PASS, and sharper than predicted** — see below |
| T2.6 | fits, refuse anyway | **10 of 10** citation properties are single-valued per `cites` edge | **PASS — the prediction was exact** |
| T2.7 | value sets absent | neither value set appears in the edge store | **PASS** |
| T2.8 | not caught; sample does not exercise it | 10 distinct provider names over 10 CCNs; **0** names shared | **PASS — the fixture does not exercise T4** |
| T2.9 | representable, not caught | **6 of 400** rows carry a correction date before the survey date, matching the pre-registered 1.5% | **PASS** |
| T2.10 | nothing added | `resolve_type` answers it; EDGES adds nothing | **PASS** |

**T2.5 was refused on `level`, not on `kind`, and that is worth noticing.** The probe deliberately declared `has_severity` with `endpoint_kinds={"dst": ("entity","value_set")}` — i.e. a family that *permits* a value set — to check whether the rule could be talked around by a permissive declaration. It cannot: the `level` check runs first and a `value_set` reached as `scope_severity_code` is a `TypeRef`, while a `level="instance"` family requires an `InstanceRef` on both ends. **`endpoint_kinds` alone would have been a rule a family author could opt out of; `level` is not.** That ordering is now explicit in §2.4.1 because the probe made it visible.

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

**Method.** [`docs/tools/edges_nyc_probe.py`](../tools/edges_nyc_probe.py), live against the SODA API, using **two** engines on purpose: the **shipped** `open_ontology.Registry` on SQLite for everything about types (so T3.12's claim about `merge_types` is a claim about the real implementation), and `edges_probe_kit` for everything about edges. `py docs/tools/edges_nyc_probe.py` → `ALL CHECKS PASSED`.

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
| T3.9 | REFUSED | `Refusal(reason="endpoint_kind_mismatch", detail={"problem": "level", …})` | **PASS** |
| T3.10 | visible staleness | `source_version = "erm2-nwe9@2026-08-28 / uvpi-gqnh@2017-10-04"` on every edge | **PASS** |
| T3.11 | inherited, not created | namespace assignment for B is made before any edge; EDGES adds no ambiguity | **PASS** |
| T3.12 | **still refused** | `Refusal(reason="cross_namespace_merge")` with the edge present; **and again** with `acknowledge=["cross_namespace_merge","definitions_diverge"]` | **PASS — the load-bearing check** |

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
| **Q20** | **Shape B's far end is a table row, not an entity instance (E7).** Does `endpoint_kinds` need a third level, or is Slice 0 the answer? | **Slice 0 is the answer**, and this is evidence for it rather than a change here. A `record` level would let any table row be a node, which deletes the distinction §2.4.1 exists to hold | No |

---

## 15. Kill-criterion check — required, and not skipped

**`ROADMAP.md`'s kill row:** *"A capability predicate gets merged as a duplicate → Stop."* And the rule of the ordering: *nothing in #1–#4 may take a shape because Tenshen has it.*

**Neither is tripped, and here is the mechanical form of both.**

**1. Is this document a merge licence?** No, and it was tested rather than asserted. T3.12 wrote the `equivalent_to` edge and then asked the **shipped** registry to merge the two types: refused `cross_namespace_merge`, and refused again under explicit `acknowledge`. §3.2 states the rule; the probe checked it against `open_ontology.Registry`, not against the probe's own model.

**2. Can a predicate be an edge endpoint?** **No.** `equivalent_to`'s `endpoint_kinds` exclude `kind="predicate"` (§3.1), for the reason §5.10 refusal #2 is non-overridable: two predicates being "equivalent" is a claim about extents, and it must be made from byte-identical extents or not at all. **An `equivalent_to` edge between two predicates would be exactly the kill row, one indirection away**, and it is structurally blocked rather than discouraged.

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
| An adversarial review loop | §17 |
| New `Refusal.reason` values go through `INTERFACE.md` §5.12 in the same change (**R3**) | Three added: `edge_family_unknown`, `endpoint_kind_mismatch`, `edge_store_absent`. §5.12 now enumerates eighteen |

---
