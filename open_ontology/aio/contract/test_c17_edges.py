# ---------------------------------------------------------------------------------
# GENERATED FILE -- do not edit. Edit open_ontology/contract/test_c17_edges.py and run:
#
#     python tools/unasync.py
#
# The sync module is the single source of truth; this is its mechanical async mirror
# (deliverable 3b). open_ontology/aio/contract/test_generated_matches_source.py fails
# if this file and its source have drifted apart.
# ---------------------------------------------------------------------------------

"""C17 -- the edge store and the read seam (34). `EDGES.md` v0, roadmap row 4b.

Three things shape this group, and each is a lesson this repository already paid for.

**The rules of `EDGES.md` §2.4.1, §4.3 and §4.4 are mapped to ids here, one by one**
(ruling **R31**, standing constraint 8). Thirteen of row 3e's twenty-one new ids
existed only to pin claims the specification already made, and round 3 of that row's
loop found four false prose sentences no gate could see. So a numbered rule in those
sections now ships with either an id that exercises it or a `prose-only` tag with a
reason, and `check_spec_drift.py` fails on a rule with neither. The mapping is in
`docs/runs/4B-RUN.md` §4 and in `docs/tools/check_spec_drift.py`'s `EDGE_RULE_MAP`.

**Every BLOCKING finding of the spec row's own adversarial loop is an assertion here.**
That loop found ten, every one reproduced by running code, and three of them were
defects in the previous round's fix. They were fixed in a throwaway probe kit in
`docs/tools/`, which the package does not import and the suite does not know about --
so until this file they were fixed nowhere that a backend author could be held to.

**`C0-10`'s question, asked of this surface: can a BROKEN edge backend PASS?** That
question found the first defect of its kind -- an adapter silently dropping `limit` and
`after`, a duplicate-forever loop in any keyset consumer, running the whole suite to
`119 passed, exit 0`. `C17-24` asks it of three broken edge backends.

**Why so many of these need `stores_attributes` as well as `stores_edges`, which is a
finding rather than a fixture detail.** EDGES.md 2.4 puts a family's five declared keys
in `TypeEntry.attributes`, so **a backend that stores no arbitrary attributes cannot
DECLARE a family at all** -- its `level` does not round-trip, and `add_edge` then
refuses `attributes_schema_violation` (`C17-29`) however capable its edge store is. The
escape hatch is the one PACKAGE.md 5.7 already built: such a backend names the five in
`attribute_projections` and they round-trip through its own typed columns, which is
exactly the shape beacon's `work_link_types` has for two of them (`is_symmetric`,
`inverse_label`). Measured by `check_capability_matrix.py`, recorded in
`docs/runs/4B-RUN.md`'s deviations, and skipped with a reason here rather than hidden.
"""

from __future__ import annotations
from dataclasses import replace
import pytest
from open_ontology.aio.adapter import EdgeQuery, EdgeRecord
from open_ontology.edges import (
    EQUIVALENT_TO,
    EQUIVALENT_TO_ATTRIBUTES,
    EQUIVALENT_TO_DEFINITION,
    InstanceRef,
    TypeRef,
)
from open_ontology.errors import NotSupported
from open_ontology.types import Evidence, Refusal, TypeEntry
from open_ontology.aio.contract._support import edge_family, seed
from open_ontology.aio.contract.doubles import AsyncDegradedAdapter


TASK = TypeRef("tenshen", "entity", "task")

PERSON = TypeRef("tenshen", "entity", "person")

NO_EDGES = {
    "stores_edges": "this backend is a type registry only; no table holds relationships"
}

def task(i) -> InstanceRef:
    return InstanceRef(TASK, str(i))

async def blocks(registry, **kw):
    return await edge_family(registry, "blocks", inverse_label="blocked_by", **kw)

async def test_c17_01_eighteen_primitives_and_no_edge_store_refuses_rather_than_raising(
    adapter, make_registry
):
    """EDGES.md §4.3 row 1 and §6's first flag. **Never an empty report.**

    An empty ``NeighborReport`` reads as *"this node has no neighbours"*, which is Rule
    U's forbidden empty list in the one call that would be believed -- so a registry
    with no edge store refuses, with the backend's own sentence attached.

    This test's SUBJECT is the declined capability, so it does not skip on a backend
    that declines it: PACKAGE.md 6.1 rule 1, unchanged. It runs on all three legs, and
    on `sqlite_minimal` it runs against a store whose `oo_edge` is absent from the SQL
    rather than hidden behind a Python `if`.
    """
    from open_ontology.aio.adapter import AsyncStorageAdapter

    primitives = {n for n in vars(AsyncStorageAdapter) if not n.startswith("_")}
    assert len(primitives) == 18, "fifteen until row 4b; EDGES.md 7.1 added three"
    assert {"put_edge", "get_edge", "find_edges"} <= primitives

    caps = await adapter.capabilities()
    if caps.stores_edges:
        blind = await make_registry(AsyncDegradedAdapter(adapter, stores_edges=False, why=NO_EDGES))
    else:
        blind = await make_registry(adapter)

    # Written out rather than looped over a list of lambdas: `tools/unasync.py` refuses
    # to place an `await` inside a lambda it cannot prove it is transforming correctly,
    # and it is right to -- so the async mirror of this file is generated from four
    # ordinary statements.
    outcomes = [
        await blind.neighbors(task(1), None, 1, namespace="default"),
        await blind.add_edge("blocks", task(1), task(2), "user:sd"),
        await blind.retract_edge("e1", "no", retracted_by="user:sd"),
        await blind.edge_provenance("e1"),
    ]
    for out in outcomes:
        assert isinstance(out, Refusal), out
        assert out.reason == "edge_store_absent"
        assert out.detail["why"].strip(), "the backend's own sentence, surfaced verbatim"

    # And the primitive underneath raises rather than pretending to store and lose.
    if not caps.stores_edges:
        with pytest.raises(NotSupported):
            await adapter.find_edges(EdgeQuery())

@pytest.mark.requires_capability(
    "stores_edges", "stores_attributes", "stores_edge_attributes"
)
async def test_c17_02_an_edge_record_round_trips_and_a_lost_payload_key_is_absent_not_wrong(
    adapter, make_registry, clock
):
    """PACKAGE.md 3.4 primitive 16 and EDGES.md 6.3 -- beacon finding U3, one row down.

    `work_links` has `description` and `confidence` as real typed columns and no JSON
    blob, so `stores_edge_attributes=True` would silently lose arbitrary keys and
    `False` alone would disclaim two the backend round-trips perfectly. A key that did
    not survive comes back **absent** -- and no warning value is minted for it, because
    PACKAGE.md 3.4 primitive 4's mechanism is that the returned record IS the signal.
    """
    registry = await make_registry(adapter)
    await blocks(registry)
    edge = await registry.add_edge(
        "blocks", task(1), task(2), "user:sd",
        confidence=0.82, attributes={"description": "the flagship query", "note": "x"},
    )
    assert not isinstance(edge, Refusal), edge
    assert edge.attributes == {"description": "the flagship query", "note": "x"}
    assert edge.provenance.confidence == 0.82
    assert edge.provenance.created_by == "user"
    # Ruling **R20** -- `model_tier` on `EdgeProvenance`. Additive and symmetric
    # with `Provenance`, and the reason it exists is beacon's
    # `infer_person_relationships` classifying person pairs with a named cheap tier
    # and auto-applying at 0.7 -- finding 0.5's failure shape one level down. R20
    # takes the FIELD and declines the gate. It was threaded end to end and
    # asserted nowhere until row 4b's first adversarial round.
    tiered = await registry.add_edge(
        "blocks", task(5), task(6), "ai:classifier",
        created_by="ai", confidence=0.71, model_tier="haiku",
    )
    assert tiered.provenance.model_tier == "haiku"
    assert tiered.provenance.created_by == "ai"
    read_back = await registry.neighbors(task(5), ["blocks"], 1, namespace="default")
    assert read_back.edges[0].edge.provenance.model_tier == "haiku", (
        "and it survives the round trip through the store, not only the return value"
    )
    assert edge.provenance.model_tier is None, (
        "None, not a manufactured default -- nothing scored this one"
    )

    stored = await adapter.get_edge(edge.edge_id)
    assert isinstance(stored, EdgeRecord)
    assert (stored.src_namespace, stored.src_kind, stored.src_name, stored.src_instance_id) == (
        "tenshen", "entity", "task", "1",
    )
    assert stored.status == "active"

    projected = await make_registry(
        AsyncDegradedAdapter(
            adapter,
            stores_edge_attributes=False,
            edge_attribute_projections=("description",),
            why={"stores_edge_attributes": "work_links has description as a column and no blob"},
        )
    )
    blocks_two = await projected.add_edge(
        "blocks", task(3), task(4), "user:sd",
        attributes={"description": "kept", "note": "lost"},
    )
    assert blocks_two.attributes == {"description": "kept"}, (
        "the projected key survives through its own column; the other is ABSENT"
    )
    assert not any("note" in w for w in blocks_two.warnings), (
        "no warning value is minted for attribute loss -- the record is the signal, and "
        "the type side has no warning for it either (EDGES.md 6)"
    )

@pytest.mark.requires_capability("stores_edges", "stores_attributes")
async def test_c17_03_put_edge_stores_the_status_and_the_tombstone_and_judges_no_transition(
    adapter, clock
):
    """PACKAGE.md 3.1 and 3.4 primitive 16. The adapter stores; it decides nothing.

    A `status` of `"retracted"` written straight through the primitive, with no
    tombstone and no prior `"active"` row, comes back exactly as given. An adapter that
    validated the transition would be an adapter with a policy in it.
    """
    rec = EdgeRecord(
        edge_id="hand-written",
        namespace="default",
        family="blocks",
        src_namespace="tenshen", src_kind="entity", src_name="task", src_instance_id="1",
        dst_namespace="tenshen", dst_kind="entity", dst_name="task", dst_instance_id="2",
        status="retracted",
        retract_reason=None,
        retracted_by=None,
        warnings=("endpoint_type_unregistered:tenshen:entity:task",),
    )
    stored = await adapter.put_edge(rec)
    assert stored.status == "retracted"
    assert stored.retract_reason is None and stored.retracted_by is None
    assert stored.warnings == ("endpoint_type_unregistered:tenshen:entity:task",)
    assert stored.created_at is not None and stored.updated_at is not None

@pytest.mark.requires_capability("stores_edges", "stores_attributes")
async def test_c17_04_duplicate_edges_are_permitted_and_that_is_a_decision(adapter, make_registry):
    """EDGES.md 6.1. Two `blocks` edges between one pair are TWO FACTS.

    One written by a human in March and one by a classifier in August have different
    provenance; a uniqueness constraint would force the second write to fail or to
    overwrite the first, and overwriting is an edit of a provenance-bearing record,
    which INTERFACE.md 5.8 forbids.

    **The cost is asserted too**: `known` counts edges and not distinct neighbours, and
    a caller who wants distinct nodes reads `nodes`, which IS deduplicated.
    """
    registry = await make_registry(adapter)
    await blocks(registry)
    first = await registry.add_edge("blocks", task(1), task(2), "user:sd", created_by="user")
    second = await registry.add_edge(
        "blocks", task(1), task(2), "ai:classifier", created_by="ai", confidence=0.71
    )
    assert first.edge_id != second.edge_id

    report = await registry.neighbors(task(1), ["blocks"], 1, namespace="default")
    assert report.known == 2, "two edges, because they are two facts"
    assert len(report.nodes) == 1, "one distinct neighbour -- `nodes` is deduplicated"

@pytest.mark.requires_capability("stores_edges", "stores_attributes")
async def test_c17_05_keyset_pagination_actually_pages(adapter, make_registry):
    """`C0-10`'s shape, for `find_edges`. PACKAGE.md 3.4 primitive 18.

    C0-10 was the first defect found by asking whether a BROKEN backend can PASS: an
    adapter silently dropping `limit` and `after` -- a duplicate-forever loop in any
    keyset consumer -- ran the whole suite to `119 passed, exit 0`, on two reference
    backends that had both implemented it correctly and nothing had ever checked.
    """
    registry = await make_registry(adapter)
    await blocks(registry)
    for i in range(2, 9):
        await registry.add_edge("blocks", task(1), task(i), "user:sd")

    key = ("tenshen", "entity", "task", "1")
    seen: list[str] = []
    pages, cursor = 0, None
    while True:
        page = await adapter.find_edges(EdgeQuery(incident_to=(key,), limit=3, after=cursor))
        pages += 1
        assert len(page.records) <= 3
        seen.extend(r.edge_id for r in page.records)
        cursor = page.next_after
        if cursor is None:
            break
        assert pages < 10, "a cursor that never terminates"
    assert pages == 3
    assert len(seen) == 7 == len(set(seen)), "disjoint and exhaustive"
    unpaged = await adapter.find_edges(EdgeQuery(incident_to=(key,)))
    assert seen == [r.edge_id for r in unpaged.records], "and in the same order"

@pytest.mark.requires_capability(
    "stores_edges", "stores_attributes", "indexes_edges_by_family"
)
async def test_c17_06_the_family_filter_degrades_the_way_edges_says_and_not_the_way_types_does(
    adapter, make_registry
):
    """EDGES.md 7.1's DELIBERATE deviation from `find_types`' uncertainty rule.

    `find_types(predicate=…)` on `indexes_membership=False` returns an EMPTY page with
    `known=None, complete=False`, because the alternative to an index there is scanning
    the whole type table and the honest answer is *"I cannot answer this"*. `find_edges`
    is already bounded by `incident_to` -- the frontier is a bounded set -- so the
    backend genuinely CAN return a complete answer to a slightly wider question, and it
    returns the frontier's edges **unfiltered with `complete=True`** while the registry
    narrows above.

    Both halves are asserted, because the spec row's round 2 found the store-side
    degradation implemented and **the registry-side narrowing missing**, so a
    family-filtered query on such a store returned the unfiltered set.

    `indexes_edges_by_family` is scaffolding for the FIRST half: a backend that already
    declines the index cannot demonstrate the indexed behaviour, and wrapping a declined
    flag in a second `AsyncDegradedAdapter` that declines it again proves nothing.
    """
    registry = await make_registry(adapter)
    await blocks(registry)
    await edge_family(registry, "mentions")
    await registry.add_edge("blocks", task(1), task(2), "user:sd")
    await registry.add_edge("mentions", task(1), task(3), "user:sd")

    key = ("tenshen", "entity", "task", "1")
    indexed = await adapter.find_edges(EdgeQuery(incident_to=(key,), families=("blocks",)))
    assert [r.family for r in indexed.records] == ["blocks"]
    assert indexed.complete is True

    unindexed = AsyncDegradedAdapter(
        adapter,
        indexes_edges_by_family=False,
        why={"indexes_edges_by_family": "work_links.relationship is free text with no index"},
    )
    page = await unindexed.find_edges(EdgeQuery(incident_to=(key,), families=("blocks",)))
    assert sorted(r.family for r in page.records) == ["blocks", "mentions"], (
        "the store answers the wider question it CAN answer"
    )
    assert page.complete is True, (
        "and completely -- this is not find_types' empty page, and EDGES.md 7.1 says why"
    )

    above = await make_registry(unindexed)
    narrowed = await above.neighbors(task(1), ["blocks"], 1, namespace="default")
    assert [ne.edge.family for ne in narrowed.edges] == ["blocks"], (
        "and the REGISTRY narrows -- the half that was specified and not implemented"
    )
    assert narrowed.complete is True

@pytest.mark.requires_capability("stores_edges", "stores_attributes")
async def test_c17_07_a_type_level_endpoint_is_a_value_to_match_not_a_wildcard(adapter, make_registry):
    """A ``NULL`` instance id is a VALUE. `NULL = NULL` is not true in SQL, so an
    adapter writing the frontier clause with `=` silently matches nothing; one writing
    it with no clause at all silently matches an instance's edges too.

    A type node and an instance of that type are two different endpoints, and EDGES.md
    2.1 is built on the distinction -- `equivalent_to` runs between types and `blocks`
    between instances, in the same store.
    """
    registry = await make_registry(adapter)
    await edge_family(registry, "relates_to", level="type", src_kinds=("entity",), dst_kinds=("entity",))
    await blocks(registry)
    await registry.add_edge("relates_to", TASK, PERSON, "user:sd")
    await registry.add_edge("blocks", task(1), task(2), "user:sd")

    type_page = await adapter.find_edges(
        EdgeQuery(incident_to=(("tenshen", "entity", "task", None),))
    )
    assert [r.family for r in type_page.records] == ["relates_to"]

    instance_page = await adapter.find_edges(
        EdgeQuery(incident_to=(("tenshen", "entity", "task", "1"),))
    )
    assert [r.family for r in instance_page.records] == ["blocks"]

@pytest.mark.requires_capability("stores_edges", "stores_attributes")
async def test_c17_08_the_level_check_runs_before_the_kind_check_and_the_detail_says_which(
    registry,
):
    """EDGES.md 2.4.1, and UC2's T2.5 is where the ordering became visible.

    A level mismatch makes the kind question meaningless: a `value_set` reached as a
    `TypeRef` where the family requires an `InstanceRef` is refused on **level**, and
    `detail["problem"]` says so, so a caller is not told to fix an `endpoint_kinds`
    declaration that is already correct.
    """
    await blocks(registry)
    refusal = await registry.add_edge("blocks", TASK, task(2), "user:sd")
    assert isinstance(refusal, Refusal) and refusal.reason == "endpoint_kind_mismatch"
    assert refusal.detail["problem"] == "level"
    assert refusal.detail["endpoint"] == "src"
    assert refusal.detail["family_level"] == "instance"
    assert refusal.detail["node_level"] == "type"

    await edge_family(registry, "concerns", level="type", src_kinds=("entity",), dst_kinds=("entity",))
    kind_refusal = await registry.add_edge(
        "concerns", TASK, TypeRef("dpr", "value_set", "borough"), "user:sd"
    )
    assert kind_refusal.reason == "endpoint_kind_mismatch"
    assert kind_refusal.detail["problem"] == "kind"
    assert kind_refusal.detail["declared"] == ["entity"]
    assert kind_refusal.detail["node_kind"] == "value_set"

    # **Rule 2.4.1-6, and it had no test at all until row 4b's second adversarial
    # round.** `equivalent_to` carries a family-level constraint beyond
    # `endpoint_kinds` -- `src.kind == dst.kind` -- because an `entity` is not
    # equivalent to a `value_set`: `facility == deficiency_corrected_status` is a
    # category error, not a claim. The rule table mapped it to this id, and this id
    # asserted only the GENERIC `endpoint_kinds` mismatch above; the
    # `problem="family_constraint"` branch that implements the rule was returned by
    # the registry and asserted by nothing. Second instance of the same defect class
    # `C17-30` closed, found by reading the tests behind the mapping.
    await seed(registry, "borough", kind="value_set", namespace="dpr", definition="the five")
    await seed(registry, "borough", kind="entity", namespace="dot", definition="a borough")
    cross_kind = await registry.add_edge(
        EQUIVALENT_TO,
        TypeRef("dpr", "value_set", "borough"),
        TypeRef("dot", "entity", "borough"),
        "user:dot",
    )
    assert isinstance(cross_kind, Refusal)
    assert cross_kind.reason == "endpoint_kind_mismatch"
    assert cross_kind.detail["problem"] == "family_constraint"
    assert cross_kind.detail["src_kind"] == "value_set"
    assert cross_kind.detail["dst_kind"] == "entity"
    # And BOTH kinds are individually legal for this family, so the refusal is the
    # family's own semantics and not `endpoint_kinds` doing it by accident.
    kinds = (await registry.adapter.get_type("default", EQUIVALENT_TO, kind="edge")).attributes[
        "endpoint_kinds"
    ]
    assert "value_set" in kinds["src"] and "entity" in kinds["dst"]

async def test_c17_09_the_endpoint_rules_bind_at_declaration_time_at_every_door(registry):
    """EDGES.md 2.4.1's fourth clause, and it is the one round 1 was spent on.

    > A rule checked only when an edge is written is a rule a family author can opt out
    > of by declaring a permissive `endpoint_kinds`.

    A round-1 reviewer declared `same_capability` with `predicate` endpoints and wrote a
    predicate-to-predicate edge with **no refusal** -- the `ROADMAP.md` kill row, reached
    through a door the document had left open while claiming it was shut. Writing the
    test for that then exposed the same hole in the instance clause.

    Three doors, because a rule with one enforcement point is a rule with one door left
    open: `propose_type`, `approve` (ruling **R18** names it), and `import_types`.
    """
    forbidden = {
        "level": "type",
        "symmetric": True,
        "inverse_label": None,
        "endpoint_kinds": {"src": ["predicate"], "dst": ["predicate"]},
    }
    reification = {
        "level": "instance",
        "symmetric": False,
        "inverse_label": None,
        "endpoint_kinds": {"src": ["entity"], "dst": ["entity", "edge"]},
    }

    for attributes, why in ((forbidden, "the kill row"), (reification, "reification")):
        refused = await registry.propose_type(
            "same_capability", "two predicates that mean the same thing", [], "user:sd",
            kind="edge", attributes=attributes,
        )
        assert isinstance(refused, Refusal), why
        assert refused.reason == "endpoint_kind_mismatch"
        assert refused.detail["rule"] == "EDGES 2.4.1"
        assert await registry.adapter.get_type("default", "same_capability", kind="edge") is None

    # **Door two: `approve()`.** This test's own docstring named three doors and its
    # body called two, until row 4b's second adversarial round read it -- the same
    # "claimed and not exercised" defect as `C17-30`'s, inside the test that exists to
    # prove a rule is not talked around. `propose_type` refuses a breaching declaration
    # up front, so the only way to reach `approve` with one is to write the proposal
    # past it, which is what a proposal made before the rule existed looks like.
    if registry.caps.stores_proposals:
        legal = await registry.propose_type(
            "same_capability", "two predicates that mean the same thing", [], "user:sd",
            kind="edge",
            attributes={"level": "type", "symmetric": True, "inverse_label": None,
                        "endpoint_kinds": {"src": ["entity"], "dst": ["entity"]}},
        )
        assert not isinstance(legal, Refusal), legal
        pending = await registry.adapter.get_proposal(legal.id)
        await registry.adapter.put_proposal(
            type(pending)(**{**pending.__dict__, "attributes": forbidden})
        )
        at_approval = await registry.approve(legal.id, "user:sd")
        assert isinstance(at_approval, Refusal), "the second door"
        assert at_approval.reason == "endpoint_kind_mismatch"
        assert at_approval.detail["rule"] == "EDGES 2.4.1"
        assert await registry.adapter.get_type("default", "same_capability", kind="edge") is None

    # Door three: an import cannot return a Refusal, so it returns the row unwritten
    # with `import_refused` and the reason -- the shape C12-06 already uses.
    imported = await registry.import_types(
        [{"name": "same_capability", "kind": "edge", "attributes": forbidden}]
    )
    assert len(imported) == 1
    assert any(w.startswith("import_refused:endpoint_kind_mismatch") for w in imported[0].warnings)
    assert await registry.adapter.get_type("default", "same_capability", kind="edge") is None

@pytest.mark.requires_capability("stores_proposals")
async def test_c17_10_a_symmetric_family_has_no_inverse_label_and_approve_is_where_it_is_checked(
    registry,
):
    """Ruling **R18** -- the ONE cross-field rule the registry knows about `kind="edge"`
    attributes, and INTERFACE.md 9 contortion 1, open since deliverable #1.

    PACKAGE.md 5.6 says plainly that `FieldSpec` is per-field and does not validate
    cross-field rules, so this rule has nowhere else to live. R18 accepts it narrowly and
    records it as an exception list of length one. `approve()` is the site R18 names,
    and it is checked there as well as at `propose_type`, because a pending proposal may
    predate the rule.
    """
    refusal = await registry.propose_type(
        "equivalent_ish", "symmetric and yet named in one direction", [], "user:sd",
        kind="edge",
        attributes={"level": "type", "symmetric": True, "inverse_label": "same_as"},
    )
    assert isinstance(refusal, Refusal)
    assert refusal.reason == "attributes_schema_violation"
    assert refusal.detail["rule"] == "EDGES 2.4 / R18"

    # And at approve(): a proposal written before the rule, amended into existence by
    # going round propose_type's check.
    good = await registry.propose_type(
        "pairs_with", "a symmetric family", [], "user:sd",
        kind="edge", attributes={"level": "type", "symmetric": True, "inverse_label": None},
    )
    assert not isinstance(good, Refusal), good
    rec = await registry.adapter.get_proposal(good.id)
    await registry.adapter.put_proposal(
        type(rec)(**{**rec.__dict__, "attributes": {**rec.attributes, "inverse_label": "x"}})
    )
    assert (await registry.approve(good.id, "user:sd")).reason == "attributes_schema_violation"

@pytest.mark.requires_capability("stores_edges", "stores_attributes")
async def test_c17_11_a_dangling_endpoint_is_a_fact_not_an_error(registry):
    """EDGES.md 2.7, and it is PACKAGE.md 3.4 primitive 10's argument transposed.

    `put_consumer` deliberately accepts a `gate` naming a predicate that does not exist,
    *because a consumer gating on a word nobody registered is precisely mechanism C, and
    refusing the registration would hide it.* The same holds here: an edge pointing at a
    type nobody registered is the ingestion layer's mistake made visible, and refusing
    the write moves the failure into a log nobody reads.

    **`endpoint_kind_mismatch` can only fire when the endpoint's type IS registered** --
    on an unregistered one the registry cannot know the kind, so it does not guess.
    """
    await blocks(registry)
    edge = await registry.add_edge("blocks", task(1), task(2), "user:sd")
    assert not isinstance(edge, Refusal)
    assert edge.warnings.count("endpoint_type_unregistered:tenshen:entity:task") == 2, (
        "two endpoints, two facts -- collapsing them would turn 'both ends' into 'one'"
    )

    report = await registry.neighbors(task(1), ["blocks"], 1, namespace="default")
    assert "origin_type_unregistered:tenshen:entity:task" in report.warnings
    assert report.known == 1, "the walk proceeds; there is no UnknownNode exception"

    await seed(registry, "task", namespace="tenshen", definition="a unit of work")
    clean = await registry.add_edge("blocks", task(5), task(6), "user:sd")
    assert not any(w.startswith("endpoint_type_unregistered") for w in clean.warnings)

@pytest.mark.requires_capability("stores_edges", "stores_attributes")
async def test_c17_12_the_depth_cap_is_two_and_three_raises(registry):
    """EDGES.md 4.2, and it is R13's consequence rather than a separate decision.

    `ValueError`, not a `Refusal`: a caller error like INTERFACE.md 5.4's empty
    definition, and R3's closed vocabulary should not grow a value for a typo. **The cap
    and the no-paging rule are ONE decision** -- if R13 is revisited the cap is revisited
    in the same change, and this test is where that would be noticed.
    """
    await blocks(registry)
    one = await registry.neighbors(task(1), ["blocks"], 1, namespace="default")
    two = await registry.neighbors(task(1), ["blocks"], 2, namespace="default")
    assert (one.depth_requested, two.depth_requested) == (1, 2)
    for bad in (0, 3, 4):
        with pytest.raises(ValueError, match="depth must be"):
            await registry.neighbors(task(1), ["blocks"], bad, namespace="default")

@pytest.mark.requires_capability("stores_edges", "stores_attributes")
async def test_c17_13_edge_families_none_spans_every_namespace_and_an_unregistered_family_is_kept(
    adapter, registry
):
    """EDGES.md 4.1's `None` case, and the value row 4b had to mint.

    **The `None` case.** A round-1 reviewer built two families in two namespaces
    incident on one node and ran the project's own kit: each call found one. That is
    Cause C -- the silent per-consumer drop EDGES.md is designed against -- inside its
    only read call, on the exact axis UC3 exists to stress. `None` spans every
    namespace, and `namespace` is therefore a no-op in that call shape.

    **The value.** There is deliberately no foreign key from an edge to its family
    (EDGES.md 2.7's argument; beacon's `work_links` has none to `work_link_types`
    either), so an edge whose family nobody registered is reachable. Dropping it here
    would be that same Cause C, in the same call. It is returned, with
    `edge_family_unregistered` -- the twenty-first value of INTERFACE.md 5.4.
    """
    await blocks(registry)
    await edge_family(registry, "owns", namespace="dpr")
    await registry.add_edge("blocks", task(1), task(2), "user:sd")
    await registry.add_edge("owns", task(1), task(3), "user:sd", namespace="dpr")

    scoped = await registry.neighbors(task(1), None, 1, namespace="default")
    assert scoped.known == 2, "`None` spans every namespace; `namespace` filters nothing"
    assert sorted(scoped.families_searched) == ["blocks", "equivalent_to", "owns"]

    await adapter.put_edge(
        EdgeRecord(
            edge_id="host-written",
            namespace="default",
            family="waiting_on",  # a family the host wrote and nobody registered
            src_namespace="tenshen", src_kind="entity", src_name="task", src_instance_id="1",
            dst_namespace="tenshen", dst_kind="entity", dst_name="task", dst_instance_id="9",
        )
    )
    report = await registry.neighbors(task(1), None, 1, namespace="default")
    assert report.known == 3, "the edge is RETURNED, not silently dropped"
    assert "edge_family_unregistered:default:waiting_on" in report.warnings

@pytest.mark.requires_capability("stores_edges", "stores_attributes")
async def test_c17_14_a_typo_and_a_wrong_namespace_both_refuse_the_whole_call(registry):
    """EDGES.md 4.3 rows 2 and 9.

    A caller that names a family and gets a report back is entitled to believe the
    family was searched, so a typo'd name returning a clean empty set is mechanism C
    committed by the read seam. Resolving names is `namespace`'s one job, so a family
    registered in a different namespace is a different family.
    """
    await blocks(registry)
    await edge_family(registry, "owns", namespace="dpr")

    typo = await registry.neighbors(task(1), ["blocs"], 1, namespace="default")
    assert isinstance(typo, Refusal) and typo.reason == "edge_family_unknown"
    assert typo.detail["families"] == ["blocs"]

    elsewhere = await registry.neighbors(task(1), ["owns"], 1, namespace="default")
    assert isinstance(elsewhere, Refusal) and elsewhere.reason == "edge_family_unknown"

    mixed = await registry.neighbors(task(1), ["blocks", "blocs"], 1, namespace="default")
    assert isinstance(mixed, Refusal), "the WHOLE call, not a partial answer"

@pytest.mark.requires_capability(
    "stores_edges", "stores_attributes", "stores_events", "indexes_membership"
)
async def test_c17_15_a_retired_family_is_searched_and_the_caller_is_told(registry):
    """EDGES.md 4.3 row 3. Not a refusal: its edges were not deleted.

    Retiring a family is a statement about the vocabulary; the edges written under it
    remain facts. A read that hid them would be deleting data by lifecycle, which
    nothing in this project does.

    `indexes_membership` is scaffolding here rather than the subject: `retire` refuses
    when the consumer set is unknowable (`C9-07`), so a backend that cannot answer
    membership cannot produce a retired family for this test to read. Skipped with a
    reason, which is how the matrix found it.
    """
    await blocks(registry)
    await registry.add_edge("blocks", task(1), task(2), "user:sd")
    retired = await registry.retire("blocks", "the classifier replaced it", retired_by="user:sd")
    assert not isinstance(retired, Refusal), retired
    assert retired.status == "retired"

    report = await registry.neighbors(task(1), ["blocks"], 1, namespace="default")
    assert not isinstance(report, Refusal), "retired is not unknown"
    assert report.known == 1
    assert "edge_family_retired:blocks" in report.warnings

    # **The second carrier**, which EDGES.md 2.8's table did not list until row 4b's
    # second adversarial round found the code emitting it. Writing an edge onto a
    # retired family is not refused -- retirement is a statement about the vocabulary
    # and an edge is a fact about two things -- but a caller who has just written under
    # a word somebody withdrew is entitled to know, and `Edge.warnings` is where a write
    # tells them. A carrier minted by implementation is the closed vocabulary opening by
    # code rather than by prose, which is worse than opening by prose, so 2.8 now lists
    # it and this asserts it.
    late = await registry.add_edge("blocks", task(3), task(4), "user:sd")
    assert not isinstance(late, Refusal), "not refused -- the family's edges are facts"
    assert "edge_family_retired:blocks" in late.warnings

@pytest.mark.requires_capability("stores_edges", "stores_attributes")
async def test_c17_16_direction_filters_directed_families_only(registry):
    """EDGES.md 2.2 and 4.1 -- a BLOCKING finding of the spec row's round 2.

    One edge written `src=dpr, dst=dot`; `neighbors(dot, ["equivalent_to"], 1,
    direction="out")` returned **`known=0, complete=True, nodes=[]`**. A confident,
    complete, **false negative**, on the only family the document ships, decided by an
    accident of which publisher wrote the edge first. No design test had ever passed
    `direction` to a symmetric family.

    For a symmetric family there is no in and no out, so both orientations return. For a
    directed family the filter applies. A mixed query gets both behaviours in one
    report, which is why this is a per-family rule rather than a per-call refusal -- the
    alternative breaks a query over one symmetric and one directed family, the ordinary
    case.
    """
    dpr, dot = TypeRef("dpr", "value_set", "borough"), TypeRef("dot", "value_set", "borough")
    await seed(registry, "borough", kind="value_set", namespace="dpr", definition="the five")
    await seed(registry, "borough", kind="value_set", namespace="dot", definition="the five")
    await registry.add_edge(EQUIVALENT_TO, dpr, dot, "user:sd")

    for origin in (dpr, dot):
        for direction in ("both", "out", "in"):
            report = await registry.neighbors(
                origin, [EQUIVALENT_TO], 1, namespace="default", direction=direction
            )
            assert report.known == 1, (
                f"symmetric family, origin {origin}, direction {direction}: the stored "
                "order is an accident of which publisher wrote it"
            )

    await blocks(registry)
    await registry.add_edge("blocks", task(1), task(2), "user:sd")
    out = await registry.neighbors(task(1), ["blocks"], 1, namespace="default", direction="out")
    into = await registry.neighbors(task(1), ["blocks"], 1, namespace="default", direction="in")
    assert out.known == 1 and into.known == 0

    mixed = await registry.neighbors(
        dpr, [EQUIVALENT_TO, "blocks"], 1, namespace="default", direction="out"
    )
    assert mixed.known == 1, "one report, two behaviours, per family"

@pytest.mark.requires_capability("stores_edges", "stores_attributes")
async def test_c17_17_a_dead_end_is_complete_and_truncation_is_a_separate_signal(registry):
    """EDGES.md 4.3 rows 6 and 7, and 4.1's `depth_reached`. Round 2's second BLOCKING.

    A one-edge graph walked to depth 2 reported `depth_reached=2`: the level-2 frontier
    contains the node reached at level 1, that node is incident on the edge the walk
    *arrived* on, and `depth_reached` was set whenever the scan returned any record. So
    round 1's dead-end rule was true only for `direction="out"` -- the one direction the
    probe written to test it happened to hard-code, and the one direction nobody
    defaults to. **Both directions are exercised here.**
    """
    await blocks(registry)
    await registry.add_edge("blocks", task(1), task(2), "user:sd")

    for direction in ("both", "out", "in"):
        report = await registry.neighbors(
            task(1), ["blocks"], 2, namespace="default", direction=direction
        )
        assert report.depth_reached < report.depth_requested
        assert report.complete is True, f"a dead end is COMPLETE ({direction})"
        assert report.why_incomplete is None

    barren = await registry.neighbors(task(404), ["blocks"], 2, namespace="default")
    assert barren.known == 0 and barren.depth_reached == 0 and barren.complete is True

@pytest.mark.requires_capability("stores_edges", "stores_attributes")
async def test_c17_18_the_assembly_bound_counts_distinct_edges_and_is_on_by_default(
    adapter, make_registry
):
    """EDGES.md 4.2 -- two BLOCKING findings of the spec row's round 3, in one test.

    **B7, the double count.** The bound was compared against each *raw page*, and at
    depth >= 2 a frontier legitimately re-finds edges already counted at depth 1 -- so a
    walk of **19 distinct edges under a bound of 20** stopped at depth 1, returned
    **15**, and reported `complete=False` with a `why` naming a bound nothing had
    crossed. Two failures in one: four real edges silently dropped, and a false claim in
    the one field 4.2 promises will tell the truth. The topology is the ordinary one --
    a hub whose leaves are also connected to each other.

    **B8, the opt-in.** 4.2 had measured the hazard, specified a mitigation and left it
    switched off. A circuit breaker nobody has to switch on is not a circuit breaker.
    """
    registry = await make_registry(adapter, max_edges=20)
    await blocks(registry)
    hub = task("hub")
    leaves = [task(i) for i in range(10)]
    for leaf in leaves:
        await registry.add_edge("blocks", hub, leaf, "user:sd")
    for a, b in zip(leaves, leaves[1:]):
        await registry.add_edge("blocks", a, b, "user:sd")

    report = await registry.neighbors(hub, ["blocks"], 2, namespace="default")
    assert report.known == 19, "nineteen DISTINCT edges, and the bound is twenty"
    assert report.complete is True, "nothing crossed the bound, so nothing claims it did"
    assert report.why_incomplete is None

    bounded = await make_registry(adapter, max_edges=5)
    tight = await bounded.neighbors(hub, ["blocks"], 2, namespace="default")
    assert tight.known == 5
    assert tight.complete is False
    assert "assembly bound of 5" in tight.why_incomplete
    assert "not paging" in tight.why_incomplete, (
        "the caller gets no cursor and cannot ask for the next five -- R13 stands"
    )

    # **The exact boundary, and it was the one axis this test never walked** (row 4b,
    # adversarial round 2, BLOCKING). A walk of exactly `max_edges` distinct edges has
    # had NOTHING truncated -- every edge that exists was returned and the adapter's
    # last page came back with no cursor -- and it reported `complete=False` with a
    # `why` naming a bound nothing had crossed. That is round 3's own B7, on the case
    # its fix never tried: this test exercised strictly-below and strictly-above and
    # never `==`, which is exactly where this project's own retro says defects hide.
    exact = await make_registry(adapter, max_edges=19)
    at_bound = await exact.neighbors(hub, ["blocks"], 2, namespace="default")
    assert at_bound.known == 19
    assert at_bound.complete is True, (
        "exactly at the bound with nothing truncated is COMPLETE -- a false claim in "
        "the one field EDGES.md 4.2 promises will tell the truth is worse than no bound"
    )
    assert at_bound.why_incomplete is None

    one_less = await make_registry(adapter, max_edges=18)
    over = await one_less.neighbors(hub, ["blocks"], 2, namespace="default")
    assert over.known == 18 and over.complete is False, "one below it, and it fires"

    default_on = await make_registry(adapter)
    assert default_on.max_edges is not None, "ON by default; disabling it is deliberate"
    unbounded = await make_registry(adapter, max_edges=None)
    assert unbounded.max_edges is None

@pytest.mark.requires_capability("stores_edges", "stores_attributes")
async def test_c17_19_the_registry_exhausts_the_adapters_pages_and_a_stale_cursor_does_not_hang(
    adapter, make_registry
):
    """EDGES.md 4.2's first consequence, plus a guard the specification does not ask for.

    A level assembled from one page of five would be silently partial, which is exactly
    what Rule K exists to prevent -- so `neighbors` loops `find_edges` until `next_after`
    is `None`, per depth level.

    **And a backend whose cursor never advances must not hang the walk.** `C0-10` asked
    whether a broken backend can pass; the answer here must not be *"it loops forever"*.
    Not in EDGES.md, added by implementing it.
    """
    registry = await make_registry(adapter)
    await blocks(registry)
    for i in range(300):
        await registry.add_edge("blocks", task("hub"), task(i), "user:sd")

    paged = await make_registry(AsyncDegradedAdapter(adapter, edge_page_cap=64))
    report = await paged.neighbors(task("hub"), ["blocks"], 1, namespace="default")
    assert report.known == 300, "assembled from 64-row pages"
    assert report.complete is True

    stale = await make_registry(
        AsyncDegradedAdapter(adapter, edge_page_cap=64, stale_edge_cursor=True)
    )
    stuck = await stale.neighbors(task("hub"), ["blocks"], 1, namespace="default")
    assert stuck.complete is False
    assert "already returned" in stuck.why_incomplete

@pytest.mark.requires_capability("stores_edges", "stores_attributes")
async def test_c17_20_retraction_is_an_event_never_a_delete(adapter, registry, make_registry):
    """EDGES.md 2.6, and the departure from PACKAGE.md 3.6 that it argues for.

    3.6's rule is that a destructive override which cannot be recorded is refused, and it
    refuses `retire(force=True)` on `stores_events=False`. Retraction is different in the
    way that rule cares about: **the record IS the row.** `status`, `retracted_by`,
    `retracted_at` and the reason are columns on the edge itself, so an unrecordable
    retraction does not exist. What is lost without events is the *sequence*, and that is
    a warning rather than a refusal.
    """
    await blocks(registry)
    edge = await registry.add_edge("blocks", task(1), task(2), "user:sd")

    with pytest.raises(ValueError, match="non-empty reason"):
        await registry.retract_edge(edge.edge_id, "   ", retracted_by="user:sd")

    missing = await registry.retract_edge("no-such-edge", "gone", retracted_by="user:sd")
    assert isinstance(missing, Refusal) and missing.reason == "unknown_edge", (
        "not `edge_family_unknown` -- that names a different failure (EDGES.md 2.3's "
        "own Cause B, inside the document that argues against reusing one word for two)"
    )

    out = await registry.retract_edge(edge.edge_id, "the wrong task", retracted_by="user:sd")
    assert out.status == "retracted"
    assert out.provenance.retract_reason == "the wrong task"
    assert out.provenance.retracted_by == "user:sd"
    assert await adapter.get_edge(edge.edge_id) is not None, "nothing is deleted"

    hidden = await registry.neighbors(task(1), ["blocks"], 1, namespace="default")
    assert hidden.known == 0
    assert hidden.complete is False, "a default that hides things is list_types' rule"
    shown = await registry.neighbors(
        task(1), ["blocks"], 1, namespace="default", include_retracted=True
    )
    assert shown.known == 1 and shown.complete is True

    trailless = await make_registry(
        AsyncDegradedAdapter(
            adapter,
            stores_edge_events=False,
            why={"stores_edge_events": "work_links has no event table and beacon owns the schema"},
        )
    )
    second = await trailless.add_edge("blocks", task(7), task(8), "user:sd")
    warned = await trailless.retract_edge(second.edge_id, "still wrong", retracted_by="user:sd")
    assert warned.status == "retracted", "succeeds -- the row IS the record"
    assert any(w.startswith("retracted_without_event_trail:") for w in warned.warnings)

@pytest.mark.requires_capability("stores_edges", "stores_attributes")
async def test_c17_21_every_edge_write_stamps_durability_itself_and_reads_stamp_nothing(
    adapter, make_registry
):
    """EDGES.md 6.2, and **the word *itself* is the finding** -- round 3's B9.

    `retract_edge` carried the warning forward from the edge's prior state instead of
    applying it, so **retracting an edge the host had already committed came back with
    no warning at all** -- a write over a borrowed connection that looked exactly as
    durable as one over an owned connection. That is PACKAGE.md 3.4 primitive 3 note 2's
    own recorded bug class, reproduced one layer up, in the call 6.2 names by name.

    A read carries nothing, and that is Rule U rather than an omission: this registry
    cannot know whether the host has since committed, so it says nothing in either
    direction. A signal that never turns off is noise.
    """
    borrowed = AsyncDegradedAdapter(
        adapter,
        edge_transaction_scope="savepoint",
        why={"edge_transaction_scope": "the connection belongs to the host"},
    )
    registry = await make_registry(borrowed)
    await blocks(registry)

    added = await registry.add_edge("blocks", task(1), task(2), "user:sd")
    assert any(w.startswith("not_durable_until_host_commits:") for w in added.warnings)

    # An edge written over an OWNED connection, then retracted over a borrowed one: the
    # prior state carries no warning, so inheriting is indistinguishable from omitting.
    owned = await make_registry(adapter)
    durable = await owned.add_edge("blocks", task(3), task(4), "user:sd")
    assert not any(w.startswith("not_durable_until_host_commits:") for w in durable.warnings)

    retracted = await registry.retract_edge(durable.edge_id, "changed", retracted_by="user:sd")
    assert any(w.startswith("not_durable_until_host_commits:") for w in retracted.warnings), (
        "stamped by THIS call, not inherited from the edge's prior state"
    )

    report = await registry.neighbors(task(1), ["blocks"], 1, namespace="default")
    assert not any(w.startswith("not_durable_until_host_commits") for w in report.warnings), (
        "a read says nothing about durability in either direction"
    )

@pytest.mark.requires_capability("stores_edges", "stores_attributes")
async def test_c17_22_complete_is_readable_only_next_to_families_searched(registry):
    """EDGES.md 4.4, and it takes ruling **R12**'s rule rather than restating it.

    `complete` CAN be `True` here, unlike `ConsumerReport.complete` and
    `Resolution.complete`, because an edge is a stored row: there is no edge that exists
    in the store and is invisible to a query over it.

    **The caveat is not small.** "Complete" is over `families_searched` and over the edge
    store, never over the host's relationships. Beacon has seventeen bespoke join tables;
    an adapter that maps three families and not the other fourteen answers `complete=True`
    about a graph that is four-fifths invisible. That is why `families_searched` is a
    required field of the report rather than an echo of the argument -- *a completeness
    claim without its scope line is not a claim*.
    """
    await blocks(registry)
    await edge_family(registry, "mentions")
    await registry.add_edge("blocks", task(1), task(2), "user:sd")
    await registry.add_edge("mentions", task(1), task(3), "user:sd")

    narrow = await registry.neighbors(task(1), ["blocks"], 1, namespace="default")
    assert narrow.complete is True
    assert narrow.families_searched == ("blocks",)
    assert narrow.known == 1, "complete -- over ONE family, with the other one right there"

    wide = await registry.neighbors(task(1), ["blocks", "mentions"], 1, namespace="default")
    assert wide.complete is True and wide.known == 2
    assert wide.families_searched == ("blocks", "mentions")

    # The shape itself refuses to carry a completeness claim with a `why`, and refuses
    # an incompleteness claim without one.
    from open_ontology.edges import NeighborReport

    with pytest.raises(ValueError, match="complete=True carries no why"):
        NeighborReport(
            origin=task(1), depth_requested=1, depth_reached=1, direction="both",
            families_searched=("blocks",), edges=(), nodes=(), known=0,
            complete=True, why_incomplete="something",
        )
    with pytest.raises(ValueError, match="requires why_incomplete"):
        NeighborReport(
            origin=task(1), depth_requested=1, depth_reached=1, direction="both",
            families_searched=("blocks",), edges=(), nodes=(), known=0,
            complete=False, why_incomplete=None,
        )

@pytest.mark.requires_capability("stores_edges", "stores_attributes")
async def test_c17_23_self_loops_and_the_triangle_are_reachable_and_specified(registry):
    """EDGES.md 4.1's two corner cases, stated in round 3 because they were reachable
    and unstated.

    **A self-loop** counts in `known` and contributes nothing to `nodes`, because both
    of its endpoints are the origin and `nodes` excludes the origin -- so `known=1,
    nodes=()` is a correct report of one real edge, not an inconsistency.

    **`at_depth` is a property of the edge's DISCOVERY, not of a newly-reached node**:
    in a triangle `A->B, A->C, B->C` walked from `A`, the `B->C` edge is `at_depth=2`
    although both of its endpoints were reached at depth 1.
    """
    await blocks(registry)
    await registry.add_edge("blocks", task("self"), task("self"), "user:sd")
    loop = await registry.neighbors(task("self"), ["blocks"], 1, namespace="default")
    assert loop.known == 1 and loop.nodes == ()

    a, b, c = task("a"), task("b"), task("c")
    await registry.add_edge("blocks", a, b, "user:sd")
    await registry.add_edge("blocks", a, c, "user:sd")
    await registry.add_edge("blocks", b, c, "user:sd")
    triangle = await registry.neighbors(a, ["blocks"], 2, namespace="default")
    assert triangle.known == 3
    assert sorted(ne.at_depth for ne in triangle.edges) == [1, 1, 2]
    assert sorted(str(n) for n in triangle.nodes) == [str(b), str(c)]

@pytest.mark.requires_capability("stores_edges", "stores_attributes")
async def test_c17_24_can_a_broken_edge_backend_pass(adapter, make_registry):
    """`C0-10`'s question, asked of this surface. Three broken backends, three answers.

    C0-10 exists because an adapter that silently dropped `limit` and `after` ran the
    whole suite to `119 passed, exit 0` while being a duplicate-forever loop in any
    keyset consumer. The three shapes here are the edge equivalents:

    1. **drops `limit`** -- the registry must still assemble the level correctly rather
       than trusting the window it asked for;
    2. **returns a stale `next_after`** -- the per-level loop must terminate and SAY the
       level is incomplete, not hang and not claim completeness;
    3. **counts non-distinct edges against the bound** -- the shape round 3 found, here
       reproduced through a backend that pages small enough to make the frontier
       re-find its own edges.
    """
    registry = await make_registry(adapter)
    await blocks(registry)
    for i in range(40):
        await registry.add_edge("blocks", task("hub"), task(i), "user:sd")

    dropper = await make_registry(AsyncDegradedAdapter(adapter, drops_edge_limit=True))
    report = await dropper.neighbors(task("hub"), ["blocks"], 1, namespace="default")
    assert report.known == 40, "a backend that ignores `limit` must not lose edges"
    assert report.complete is True

    stale = await make_registry(AsyncDegradedAdapter(adapter, edge_page_cap=8, stale_edge_cursor=True))
    stuck = await stale.neighbors(task("hub"), ["blocks"], 1, namespace="default")
    assert stuck.complete is False and "already returned" in stuck.why_incomplete

    # And the bound, on a backend paging small enough that the depth-2 frontier re-finds
    # what depth 1 already counted. The bound counts DISTINCT edges, so a walk under
    # budget stays complete however many raw rows crossed the seam.
    small = await make_registry(AsyncDegradedAdapter(adapter, edge_page_cap=3), max_edges=45)
    whole = await small.neighbors(task("hub"), ["blocks"], 2, namespace="default")
    assert whole.known == 40 and whole.complete is True

async def test_c17_25_two_transaction_scopes_on_one_connection_is_non_conformant(adapter):
    """EDGES.md 6.2's binding rule, as a value rather than as prose.

    > When the edge store and the type store share a connection,
    > `edge_transaction_scope` MUST equal `transaction_scope`.

    Otherwise the adapter is claiming that half its writes are the host's to commit and
    half its own, on one transaction, which is not a thing that can be true. When they
    are genuinely two connections the two may differ -- and then **atomicity across the
    seam is gone**, which the adapter says in its own `why`.
    """
    caps = await adapter.capabilities()
    assert caps.scope_conflict() is None, "the reference backends derive one from the other"
    assert caps.missing_why() == ()

    from dataclasses import replace

    lying = replace(
        caps,
        transaction_scope="owned",
        edge_transaction_scope="savepoint",
        edge_store_shares_connection=True,
        why={**caps.why, "edge_transaction_scope": "the host owns it"},
    )
    assert lying.scope_conflict() is not None
    assert "ONE connection" in lying.scope_conflict()

    two_connections = replace(lying, edge_store_shares_connection=False)
    assert two_connections.scope_conflict() is None, (
        "two connections MAY differ -- and lose G2 across the seam, which is why the "
        "declaration exists rather than being derived"
    )

@pytest.mark.requires_capability(
    "stores_edges", "stores_attributes", "stores_events", "stores_edge_events"
)
async def test_c17_26_an_edges_history_is_append_only_and_says_when_it_could_not_be_read(
    adapter, registry, make_registry
):
    """EDGES.md 5.2 and 6. `EventRecord.edge_id` is the amendment that makes it possible.

    That amendment was claimed in two places in EDGES.md and made in neither -- round 3
    found it -- and `check_spec_drift.py` could not see it, because PACKAGE.md and the
    code agreed with **each other** on the old shape and a third document asserting a
    change nobody made is invisible to a two-way diff.

    Rule U on the history itself: `neighbors` and `add_edge` do not fetch events per
    edge, so the `history` on an edge THEY returned is empty with a `why` saying which
    call to make -- rather than `()` reading as *"nothing happened"*.
    """
    await blocks(registry)
    edge = await registry.add_edge("blocks", task(1), task(2), "user:sd")
    assert edge.provenance.history == ()
    assert "edge_provenance" in edge.provenance.history_why

    await registry.retract_edge(edge.edge_id, "changed", retracted_by="user:sd")
    provenance = await registry.edge_provenance(edge.edge_id)
    assert [e.event for e in provenance.history] == ["edge_added", "edge_retracted"]
    assert provenance.history_why is None
    assert provenance.retract_reason == "changed"

    trailless = await make_registry(
        AsyncDegradedAdapter(
            adapter,
            stores_edge_events=False,
            why={"stores_edge_events": "work_links has no event table"},
        )
    )
    blind = await trailless.edge_provenance(edge.edge_id)
    assert blind.history == ()
    assert blind.history_why == "work_links has no event table", (
        "the backend's own sentence, verbatim -- never a reason the registry invented"
    )

    # The `neighbors` carrier, which PACKAGE.md 6.2's row for this id claimed and this
    # test did not assert until row 4b's second adversarial round read the two side by
    # side. Rule U on a field the read seam deliberately does not fill.
    walked = await registry.neighbors(task(1), ["blocks"], 1, namespace="default",
                                include_retracted=True)
    assert walked.edges[0].edge.provenance.history == ()
    assert "edge_provenance" in walked.edges[0].edge.provenance.history_why

    # **`stores_events=False` with `stores_edge_events=True` is a combination nothing
    # forbids and neither reference backend can produce** -- and it raised an uncaught
    # `NotSupported` out of `edge_provenance`, because `read_events` is the same
    # primitive `stores_events` gates. A declined capability degrades to an honest empty
    # plus a `why`; it never raises. Row 4b, adversarial round 2.
    split = await make_registry(
        AsyncDegradedAdapter(
            adapter,
            stores_events=False,
            why={"stores_events": "this store has no event table"},
        )
    )
    honest = await split.edge_provenance(edge.edge_id)
    assert honest.history == ()
    assert honest.history_why == "this store has no event table"

async def test_c17_27_equivalent_to_is_seeded_with_the_exact_shape_the_spec_prints(registry):
    """EDGES.md 3.1 and ruling **R7**, checked field by field.

    Seeded at store creation rather than left to a caller, because `equivalent_to` is
    the answer to INTERFACE.md 10b.2 contortion 9 -- *nothing can say "these two mean the
    same thing, kept apart"* -- and a registry where the answer exists only if somebody
    remembered to declare it has not answered it.

    **`kind="edge"` IS a legal endpoint here and `predicate` is not**, and that
    asymmetry is the whole point: `predicate` is absent because 2.4.1 forbids it
    GENERALLY, not because this family opted out. A per-family exclusion holds only as
    long as every future family author remembers it, and the thing on the other side of
    it is the kill row.
    """
    entry = await registry.adapter.get_type("default", EQUIVALENT_TO, kind="edge")
    assert entry is not None and entry.status == "active"
    assert entry.created_by == "seed"
    assert entry.definition == EQUIVALENT_TO_DEFINITION

    if not registry.caps.stores_attributes:
        # And here is what that costs, stated rather than skipped past. On a backend
        # with no attributes column the five declared keys do not round-trip, so the
        # family is REGISTERED and UNUSABLE: `add_edge` on it refuses
        # `attributes_schema_violation` for a missing `level` (C17-29), and on this leg
        # it would refuse `edge_store_absent` first anyway. The word exists, honestly,
        # and the deployment is told what it cannot do rather than being handed a family
        # whose shape silently vanished.
        assert entry.attributes == {}
        assert registry.caps.reason("stores_attributes").strip()
        return

    assert entry.attributes == EQUIVALENT_TO_ATTRIBUTES

    kinds = entry.attributes["endpoint_kinds"]
    assert kinds["src"] == kinds["dst"] == ["entity", "value_set", "edge"]
    assert "predicate" not in kinds["src"] and "predicate" not in kinds["dst"]
    assert entry.attributes["symmetric"] is True
    assert entry.attributes["inverse_label"] is None
    assert entry.attributes["level"] == "type"

    surfaced = await registry.provenance(EQUIVALENT_TO)
    assert surfaced.approved_by, "never null on an active type (INTERFACE.md 2.4)"
    assert surfaced.evidence, "a seeded family with no evidence would warn about itself"

@pytest.mark.requires_capability("indexes_membership")
async def test_c17_28_consumers_extends_to_edge_families_with_no_new_mechanism(registry):
    """EDGES.md 8, and the mechanism-C argument for why it matters is not hypothetical.

    `deadline_cluster_service` -- live for every user since 2026-07-06 -- walks
    `work_links[blocks]` and the family name `blocks` is in its code, while
    `work_link_types` *"is extended by the AI classifier when it is confident none of the
    existing types fit"*. So a classifier proposes `waiting_on`, it is auto-approved,
    edges start being written with it, and the one shipped producer that consumes edges
    keeps walking `blocks` and never sees them. **Nothing errors.**

    `consumers` extends to a family with **no new call**, because a family is a
    `TypeEntry`. And one warning is added by the same reasoning that made ruling R8 add
    `gate_unregistered`: when nobody has registered an edge-traversing consumer at all,
    `would_drop: []` reads as *"nothing will drop this"* when the truth is *"nobody has
    told us what traverses edges"*.
    """
    from open_ontology.types import Consumer

    await edge_family(registry, "waiting_on")
    bare = await registry.consumers("waiting_on")
    assert bare.would_drop == ()
    assert "no_edge_gate_registered" in bare.warnings, (
        "nobody has told us what traverses edges -- which is not the same as nothing "
        "will drop this"
    )

    await seed(registry, "deadline_traversable", kind="predicate",
         definition="Edge families deadline_cluster_service walks when building clusters.")
    await edge_family(registry, "blocks", inverse_label="blocked_by")
    # The family claims the predicate: membership lives on the MEMBER, and the
    # extent is a query in the other direction (INTERFACE.md 2.3). Written through
    # the adapter because `approve(predicates=...)` has already run for this family.
    family = await registry.adapter.get_type("default", "blocks", kind="edge")
    claimed = type(family)(
        **{**family.__dict__, "predicates": ("deadline_traversable",)}
    )
    await registry.adapter.put_type(claimed)
    await registry.register_consumer(
        Consumer(
            id="deadline_cluster_service.build",
            gate="deadline_traversable",
            on_unknown="drop",
            locator="src/beacon/services/deadline_cluster_service.py:_walk",
        )
    )

    report = await registry.consumers("waiting_on")
    assert [c.id for c in report.would_drop] == ["deadline_cluster_service.build"], (
        "the report says the true thing: this producer will silently drop the new family"
    )
    assert "no_edge_gate_registered" not in report.warnings, (
        "somebody HAS told us what traverses edges now"
    )
    assert report.complete is False, "consumers are registered, not discovered"
    on_blocks = await registry.consumers("blocks")
    assert [c.id for c in on_blocks.gates_on] == ["deadline_cluster_service.build"]

async def test_c17_29_a_family_that_declared_nothing_is_a_legal_type_and_an_unusable_family(
    registry,
):
    """EDGES.md 2.4: `level` is REQUIRED with no default -- *"a family that does not say
    is a family whose edges cannot be validated"*.

    But a `kind="edge"` entry with no attributes is a perfectly legal `TypeEntry`:
    INTERFACE.md 2.1 requires no attributes at all, and **beacon's `work_link_types` rows
    carry none of the five keys** -- `C14-01` seeds exactly such a row. Refusing the
    REGISTRATION would make this row reject types INTERFACE.md says are legal, on the
    data of the one real host that exists.

    So the refusal is at write time, and that is where the door closes: a family that
    declared nothing cannot be talked around, because no edge can be written on it.
    """
    entry = await seed(registry, "related_to", kind="edge", definition="an unspecified relationship")
    assert isinstance(entry, TypeEntry) and entry.status == "active", (
        "registered -- beacon's work_link_types rows look exactly like this"
    )

    if not registry.caps.stores_edges:
        pytest.skip(
            "PACKAGE.md 3.2 -- this backend declares stores_edges=False, so add_edge "
            "refuses `edge_store_absent` before it can reach the declaration check. "
            "The registration half above ran and held on this store."
        )
    refusal = await registry.add_edge("related_to", task(1), task(2), "user:sd")
    assert isinstance(refusal, Refusal)
    assert refusal.reason == "attributes_schema_violation"
    assert refusal.detail["missing"] == ["level"]
    assert refusal.detail["rule"] == "EDGES 2.4"

@pytest.mark.requires_capability("stores_edges", "stores_attributes")
async def test_c17_30_equivalent_to_between_two_edge_families_is_written_not_refused(registry):
    """EDGES.md 2.4.1's second clause and 3.1's endpoint list, at WRITE time.

    **The rule table mapped this rule to two ids that only read the declaration.** Row
    4b's first adversarial round found it: `C17-27` asserts that `endpoint_kinds`
    *contains* `"edge"` and `C18-05` writes only `value_set` endpoints, so nothing in
    the suite had ever written a `kind="edge"` endpoint. That is the "an id exists but
    does not exercise the rule it is mapped to" failure ruling **R31** was made to
    prevent, inside the row that built R31's gate -- and the gate is structurally blind
    to it, because it verifies that an id exists and not what the id asserts.

    **And the case is not academic**: it is T3.13, which `EDGES.md` 11.3 added
    specifically because §1 forbade `edge` as an endpoint kind while §3.1 declared it
    legal three sections later -- *"a contradiction no design test exercised"*, found by
    both round-1 reviewers by reading, and by neither by running, **because nothing ran
    it**. Two agencies naming the same real-world relation differently is UC3's own
    collision shape, one level up from `borough`.

    It is **not** reification. Reification is an edge pointing at an edge *instance*,
    and 2.4.1's instance clause makes that unconstructible: an `InstanceRef` may only
    name a `kind="entity"` type. A `kind="edge"` `TypeEntry` is a row of the vocabulary,
    exactly like an `entity` or a `value_set` row.
    """
    concerns = await edge_family(
        registry, "concerns", namespace="dpr",
        definition="a DPR record concerns a thing",
    )
    relates_to = await edge_family(
        registry, "relates_to", namespace="oti_311",
        definition="a 311 request relates to a thing",
    )
    assert concerns.kind == relates_to.kind == "edge"

    src = TypeRef("dpr", "edge", "concerns")
    dst = TypeRef("oti_311", "edge", "relates_to")
    written = await registry.add_edge(EQUIVALENT_TO, src, dst, "user:dot")
    assert not isinstance(written, Refusal), written
    assert written.family == EQUIVALENT_TO

    report = await registry.neighbors(src, [EQUIVALENT_TO], 1, namespace="default")
    assert [str(n) for n in report.nodes] == ["oti_311:edge:relates_to"]
    assert report.complete is True

    # And the clause that makes it not reification: an InstanceRef may only name a
    # `kind="entity"` type, so there is no way to construct a reference to an edge
    # INSTANCE and therefore no edge-about-an-edge.
    instance_level = await registry.add_edge(
        EQUIVALENT_TO, InstanceRef(src, "1"), InstanceRef(dst, "2"), "user:dot"
    )
    assert isinstance(instance_level, Refusal)
    assert instance_level.reason == "endpoint_kind_mismatch"
    assert instance_level.detail["problem"] == "level"

    # `predicate` is still refused at this level, and that is the asymmetry the whole
    # clause turns on: `edge` is legal because 3.1's list includes it, `predicate` is
    # illegal because 2.4.1 forbids it GENERALLY -- not because this family opted out.
    await seed(registry, "commentable", kind="predicate", definition="a code path accepts it")
    kill_row = await registry.add_edge(
        EQUIVALENT_TO,
        TypeRef("default", "predicate", "commentable"),
        TypeRef("default", "predicate", "commentable"),
        "user:dot",
    )
    assert isinstance(kill_row, Refusal)
    assert kill_row.reason == "endpoint_kind_mismatch"

@pytest.mark.requires_capability("stores_edges", "stores_attributes")
async def test_c17_31_find_edges_returns_only_records_incident_to_the_frontier(
    adapter, make_registry
):
    """PACKAGE.md 3.4 primitive 18's own filter, pinned as its own subject.

    `C17-06` does this for the family filter; **nothing did it for `incident_to`**, and
    row 4b's first adversarial round built an adapter that ignores the frontier entirely
    and returns every edge of the matching family. It was caught -- by `C17-07`,
    `C17-17`, `C17-23` and `C18-05`, four tests whose subject is something else. *Caught
    incidentally* is a weaker claim than *pinned*, and a backend author reading the
    coverage report cannot tell which of the two they have.

    The same round found the registry's own half of it missing: `_edge_passes` returned
    `True` unconditionally on the `direction="both"` branch, so its docstring's *"the
    registry narrows, always"* was false for the direction every caller defaults to.
    Both halves are asserted here -- the primitive filters, and the registry narrows
    above a store that does not.
    """
    registry = await make_registry(adapter)
    await blocks(registry)
    await registry.add_edge("blocks", task(1), task(2), "user:sd")
    await registry.add_edge("blocks", task(90), task(91), "user:sd")  # nowhere near the frontier

    frontier = (("tenshen", "entity", "task", "1"),)
    page = await adapter.find_edges(EdgeQuery(incident_to=frontier))
    assert len(page.records) == 1
    for rec in page.records:
        src = (rec.src_namespace, rec.src_kind, rec.src_name, rec.src_instance_id)
        dst = (rec.dst_namespace, rec.dst_kind, rec.dst_name, rec.dst_instance_id)
        assert src in frontier or dst in frontier, (
            "every returned record has an endpoint in the frontier it was asked about"
        )

    # A frontier of several nodes, including one with no edges at all: still only what
    # is incident, and the node with none contributes none rather than widening the set.
    wider = await adapter.find_edges(
        EdgeQuery(
            incident_to=(
                ("tenshen", "entity", "task", "1"),
                ("tenshen", "entity", "task", "404"),
                ("tenshen", "entity", "task", "90"),
            )
        )
    )
    assert len(wider.records) == 2

    # And the registry's half: a store that ignores the frontier is narrowed above it,
    # on the default direction as well as on `out` and `in`.
    class _IgnoresFrontier:
        def __init__(self, inner):
            self.inner = inner

        def __getattr__(self, name):
            return getattr(self.inner, name)

        async def find_edges(self, q):
            return await self.inner.find_edges(replace(q, incident_to=None))

    blind = await make_registry(_IgnoresFrontier(adapter))
    for direction in ("both", "out", "in"):
        report = await blind.neighbors(
            task(1), ["blocks"], 1, namespace="default", direction=direction
        )
        for ne in report.edges:
            assert "#1" in (str(ne.edge.src) + str(ne.edge.dst)), (
                f"direction={direction}: the registry narrows an unfiltered store, "
                "and `both` is the direction every caller defaults to"
            )

@pytest.mark.requires_capability("stores_edges", "stores_attributes")
async def test_c17_32_a_callers_mistake_arrives_as_the_documented_error(registry):
    """EDGES.md 4.2 promises a `ValueError` for a caller's mistake. It has to keep it.

    `neighbors` is the one call this document is built around, and it had **no input
    validation at all** until row 4b's third adversarial round, whose reviewer was told
    to be the engineer integrating against it next week. Three of the four things they
    tried in the first hour blew up three frames down:

    * `depth=1.5` sailed past the range guard and died inside `range()` with a
      `TypeError` naming neither the parameter nor the rule. Not exotic: `n / 1` is a
      float in Python, and JSON round-trips ints as floats.
    * a `node` that is a plain string died on `.namespace` deep in the walk.
    * `edge_families="blocks"` -- **a bare `str` satisfies `Sequence[str]`**, which is
      the most natural mistake in Python -- was iterated character by character and
      refused with `detail={"families": ["b","l","o","c","k","s"]}`, which does not
      merely fail, it actively misleads the caller about what they got wrong.

    A raw `TypeError` from three frames down is not the promise 4.2 makes.
    """
    await blocks(registry)
    origin = task(1)

    for bad_depth in (1.5, "2", True, None):
        with pytest.raises(ValueError, match="depth"):
            await registry.neighbors(origin, ["blocks"], bad_depth, namespace="default")

    with pytest.raises(TypeError, match="TypeRef or an InstanceRef"):
        await registry.neighbors("tenshen:entity:task#1", ["blocks"], 1, namespace="default")

    with pytest.raises(TypeError, match="sequence of family names"):
        await registry.neighbors(origin, "blocks", 1, namespace="default")

    with pytest.raises(ValueError, match="direction"):
        await registry.neighbors(origin, ["blocks"], 1, namespace="default", direction="outbound")

    # And the legal shapes still work, so the guards are guards and not a wall.
    assert (await registry.neighbors(origin, ["blocks"], 1, namespace="default")).known == 0
    assert (await registry.neighbors(origin, None, 2, namespace="default")).known == 0
    assert (await registry.neighbors(origin, (), 1, namespace="default")).families_searched == ()

@pytest.mark.requires_capability(
    "stores_edges", "stores_attributes", "stores_events", "indexes_membership"
)
async def test_c17_33_a_merge_makes_the_walk_incomplete_and_the_report_says_so(registry):
    """EDGES.md 4.3, rule `4.3-14` -- and it was a **confident, complete, false
    negative** until row 4b's third adversarial round.

    `merge_types` is the registry's sanctioned answer to mechanism **4**, which
    `EDGES.md` 12 calls **co-dominant** for this row: it retires one word with the other
    as its `successor` and adds the retired name to the survivor's aliases. **It rewrites
    no edge** -- `src`/`dst` are references by identity triple (2.1) and nothing in this
    package edits a stored reference.

    So a caller who does the CORRECT thing after a merge -- resolve to the canonical
    type, exactly as `resolve_type` teaches, and then walk -- got `known=0`,
    **`complete=True`** and an empty `warnings`, about edges sitting in the store under
    the other name. That is the shape 2.2's `direction` finding calls unacceptable, and
    it contradicts 4.4's own argument for why `complete` may ever be `True`: *"there is
    no edge that exists in the store and is invisible to a query over it."* Across a
    merge there is.

    **The walk still does not follow the chain**, and that is deliberate: whether an edge
    written under a merged word is an edge of its survivor is a decision above this row.
    Deviation **D-4b-15**, question **Q33**. What it does is stop claiming otherwise.
    """
    await blocks(registry)
    await seed(registry, "facility_old", definition="a nursing home, as we first called it")
    await seed(registry, "facility_new", definition="a nursing home, as we first called it")
    await seed(registry, "citation", definition="a deficiency cited at a survey")
    old = TypeRef("default", "entity", "facility_old")
    new = TypeRef("default", "entity", "facility_new")
    cit = TypeRef("default", "entity", "citation")

    written = await registry.add_edge(
        "blocks", InstanceRef(cit, "C1"), InstanceRef(old, "F1"), "user:sd"
    )
    assert not isinstance(written, Refusal), written

    clean = await registry.neighbors(InstanceRef(old, "F1"), ["blocks"], 1, namespace="default")
    assert clean.known == 1 and clean.complete is True, "before the merge, nothing is hidden"

    merged = await registry.merge_types(
        "facility_old", "facility_new", "one word for one facility", merged_by="user:sd",
        acknowledge=["definitions_diverge", "no_consumer_evidence"],
    )
    assert not isinstance(merged, Refusal), merged

    # The survivor: the edge is in the store, under the other name, and invisible here.
    survivor = await registry.neighbors(InstanceRef(new, "F1"), ["blocks"], 1, namespace="default")
    assert survivor.known == 0
    assert survivor.complete is False, (
        "an empty answer about a node whose edges are in the store under a word this "
        "one absorbed is not a complete answer"
    )
    assert f"endpoint_type_merged:{new}" in survivor.warnings
    assert "facility_old" in survivor.why_incomplete

    # And the predecessor, walked directly: the edges are there, and the report still
    # says the identity is split, because a caller reading it needs to know either way.
    predecessor = await registry.neighbors(
        InstanceRef(old, "F1"), ["blocks"], 1, namespace="default"
    )
    assert predecessor.known == 1
    assert predecessor.complete is False
    assert f"endpoint_type_merged:{old}" in predecessor.warnings

    # A type nobody merged says nothing of the kind.
    ordinary = await registry.neighbors(InstanceRef(cit, "C1"), ["blocks"], 1, namespace="default")
    assert ordinary.complete is True
    assert not any(w.startswith("endpoint_type_merged") for w in ordinary.warnings)

@pytest.mark.requires_capability("stores_edges", "stores_attributes")
async def test_c17_34_the_report_says_which_node_each_edge_reached(registry):
    """EDGES.md 4.1's `reached`, and 9.3's worked example is why it exists.

    9.3 fills the Tenshen grounding bundle's `relations` slot from a depth-2 report --
    **the worked example for the reason this row exists** -- and row 4b's third
    adversarial round implemented it the obvious way, comparing each edge's endpoints
    against the ORIGIN. At depth 2 that is silently wrong: the far end of a second-hop
    edge was never incident on the origin, so `person#7` never appears and `task#77`
    appears twice, with no error, no warning and no `complete=False`. **Mechanism C,
    inside the example written to show a consumer how to avoid it.**

    Computing it correctly needs `edges` walked in discovery order against a growing
    visited set -- an inference the report can make once, exactly, and a consumer can
    only re-derive. So the walk fills it, and the order it is filled in is **guaranteed**
    rather than incidental: `(at_depth, edge_id)`. That is a deterministic traversal
    order and not a ranking; 1's *"a set, not a ranked list"* is about relevance.
    """
    await blocks(registry)
    await edge_family(registry, "stakeholder", inverse_label="stakes")
    person = TypeRef("tenshen", "entity", "person")
    t41, t77, p7 = task(41), task(77), InstanceRef(person, "7")
    await registry.add_edge("blocks", t41, t77, "user:sd", confidence=0.82)
    await registry.add_edge("stakeholder", t77, p7, "user:sd")

    report = await registry.neighbors(
        t41, ["blocks", "stakeholder"], 2, namespace="default", direction="out"
    )
    assert [ne.at_depth for ne in report.edges] == [1, 2], "ordered by (at_depth, edge_id)"

    # 9.3's projection, written the way a consumer would now write it.
    relations = [
        {
            "type": ne.reached.type.name,
            "id": ne.reached.id,
            "note": f"{ne.edge.family} (hop {ne.at_depth})",
        }
        for ne in report.edges
        if ne.reached is not None
    ]
    assert relations == [
        {"type": "task", "id": "77", "note": "blocks (hop 1)"},
        {"type": "person", "id": "7", "note": "stakeholder (hop 2)"},
    ], "the hop that turns 'what is blocking this' into 'who is blocking this'"

    # `None` where nothing new was reached, which is Rule U rather than picking an end.
    loop_registry_edge = await registry.add_edge("blocks", task(9), task(9), "user:sd")
    assert not isinstance(loop_registry_edge, Refusal)
    loop = await registry.neighbors(task(9), ["blocks"], 1, namespace="default")
    assert [ne.reached for ne in loop.edges] == [None], "a self-loop reaches nobody new"

    a, b, c = task("a"), task("b"), task("c")
    await registry.add_edge("blocks", a, b, "user:sd")
    await registry.add_edge("blocks", a, c, "user:sd")
    await registry.add_edge("blocks", b, c, "user:sd")
    triangle = await registry.neighbors(a, ["blocks"], 2, namespace="default")
    closing = [ne for ne in triangle.edges if ne.at_depth == 2]
    assert len(closing) == 1 and closing[0].reached is None, (
        "a triangle's closing edge reaches nobody new, and saying so is Rule U rather "
        "than naming one of its two already-reached ends"
    )
    assert {str(ne.reached) for ne in triangle.edges if ne.reached} == {str(b), str(c)}
