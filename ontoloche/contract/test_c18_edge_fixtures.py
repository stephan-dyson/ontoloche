"""C18 -- the three use cases through the SHIPPED edge store (10). Row 4b.

Row #4 was a spec, and its three design tests were walked by a throwaway probe kit under
`docs/tools/` that the package does not import. Its own §17.5 says what that is worth:

> **[Inferred]** a fourth synthetic round would find a fourth such corner rather than
> none -- and the honest reading of that is not that the loop should continue, but that
> **prose-plus-probe review has a floor, and this document has reached it.** The next
> signal with real information is a real consumer over a real store.

This group is the smallest available version of that: the same three fixtures, the same
pre-registered numbers, driven through `ontoloche.Registry` and a real backend on
all three legs rather than through a kit written alongside the document it was checking.

**The numbers are pre-registered and unchanged.** UC2's come from
`0.5-ground-truth-PREREGISTERED.md` -- 10 facilities, 69 surveys, 400 citations, 92
deficiency tags -- and the edge counts follow arithmetically. UC3's come from a pinned
fixture written by `docs/tools/pin_nyc_edge_sample.py`, and they reproduce `EDGES.md`
§11.3's live run exactly: 25 complaints over 22 BBLs, 54 census trees, 102 edges, 18 of
25 matched, max 16 trees on one lot.

**UC1 is read-only and there is no beacon code here.** `EDGES.md` §7.2 maps
`work_links` onto `EdgeRecord` from a read of beacon's model file; `C18-09` and `C18-10`
put a `work_links`-shaped table behind the protocol and check the mapping and ruling
**R23**'s nullable `relationship_type` -- refused explicitly, never silently dropped.
"""

from __future__ import annotations

import pytest

from ..adapter import EdgeQuery, EdgeRecord
from ..edges import EQUIVALENT_TO, InstanceRef, TypeRef
from ..types import Evidence, Refusal
from ._support import cms_edges, edge_family, load_cms_sample, nyc_edge_sample, seed
from .doubles import DegradedAdapter

pytestmark = pytest.mark.requires_capability("stores_edges", "stores_attributes")

CMS = "default"
FACILITY = TypeRef(CMS, "entity", "facility")
SURVEY = TypeRef(CMS, "entity", "survey")
CITATION = TypeRef(CMS, "entity", "citation")
TAG = TypeRef(CMS, "entity", "deficiency_tag")


def _write_cms_edges(registry) -> dict:
    """The three families' edges, written through `add_edge` on the shipped registry."""
    pairs = cms_edges()
    edge_family(
        registry, "cites", inverse_label="cited_by",
        definition="A citation names a deficiency tag.",
    )
    written = {"issued_during": 0, "conducted_at": 0, "cites": 0}
    ends = {
        "issued_during": (CITATION, SURVEY),
        "conducted_at": (SURVEY, FACILITY),
        "cites": (CITATION, TAG),
    }
    for family, rows in pairs.items():
        src_type, dst_type = ends[family]
        for src, dst in rows:
            out = registry.add_edge(
                family,
                InstanceRef(src_type, src),
                InstanceRef(dst_type, dst),
                "import:cms_sample",
                created_by="derived",
            )
            assert not isinstance(out, Refusal), out
            written[family] += 1
    return written


# --------------------------------------------------------------------------- UC2, CMS


@pytest.mark.cms
def test_c18_01_the_three_cms_families_and_every_pre_registered_edge_count(registry):
    """`EDGES.md` §10, T2.1 and T2.2. The counts were stated before the walk-through.

    The ground truth fixes the NODE counts -- 10 facilities, 69 surveys, 400 citations,
    92 deficiency tags -- and the EDGE counts follow arithmetically. Stating them in
    advance is the point: `USE-CASES.md`'s protocol exists so an answer cannot be
    argued for after the fact.

    `created_by="derived"` is ruling **R17** doing its job on its second fixture: these
    edges are produced by a deterministic rule at ingest, with no human and no model in
    the loop, and before R17 they would have had to claim `user` for a join no user
    performed.
    """
    load_cms_sample(registry)
    written = _write_cms_edges(registry)

    assert written == {"issued_during": 400, "conducted_at": 69, "cites": 400}

    pairs = cms_edges()
    assert len({dst for _, dst in pairs["cites"]}) == 92, "distinct deficiency tags"
    assert len({dst for _, dst in pairs["conducted_at"]}) == 10, "distinct facilities"
    assert len({src for src, _ in pairs["conducted_at"]}) == 69, "distinct surveys"

    for family in ("issued_during", "conducted_at", "cites"):
        entry = registry.adapter.get_type(CMS, family, kind="edge")
        assert entry is not None and entry.kind == "edge"
        assert entry.attributes["level"] == "instance"
        assert entry.attributes["symmetric"] is False
        assert entry.attributes["inverse_label"], "each is directed and reads both ways"
        assert entry.attributes["endpoint_kinds"] == {"src": ["entity"], "dst": ["entity"]}


@pytest.mark.cms
def test_c18_02_a_facilitys_surveys_and_citations_sum_to_the_ground_truth(registry):
    """T2.3, and the summing is what makes it a check rather than a spot-read.

    `neighbors(facility, depth=1)` returns that facility's surveys; `depth=2` adds its
    citations. Summed over all ten facilities the totals must be exactly 69 and 400 --
    the same numbers, reached the other way round through the read seam.
    """
    load_cms_sample(registry)
    _write_cms_edges(registry)
    pairs = cms_edges()
    facilities = sorted({dst for _, dst in pairs["conducted_at"]})
    assert len(facilities) == 10

    surveys = citations = 0
    for ccn in facilities:
        report = registry.neighbors(
            InstanceRef(FACILITY, ccn),
            ["conducted_at", "issued_during"],
            2,
            namespace=CMS,
            direction="in",
        )
        assert not isinstance(report, Refusal), report
        assert report.complete is True
        assert report.families_searched == ("conducted_at", "issued_during")
        surveys += sum(1 for ne in report.edges if ne.at_depth == 1)
        citations += sum(1 for ne in report.edges if ne.at_depth == 2)

    assert surveys == 69, "every survey, once, summed over the ten facilities"
    assert citations == 400, "and every citation, at depth 2"


@pytest.mark.cms
def test_c18_03_the_deepest_chain_in_the_fixture_is_two_hops(registry):
    """T2.4 -- `citation -> survey -> facility`, which is why the cap is 2 for CMS.

    `EDGES.md` §4.2 argues the cap from beacon's flagship two-hop query; CMS is the
    second fixture to need exactly two and no more, and the two arrive at the number
    independently.
    """
    load_cms_sample(registry)
    _write_cms_edges(registry)

    report = registry.neighbors(
        InstanceRef(CITATION, "0"),
        ["issued_during", "conducted_at"],
        2,
        namespace=CMS,
        direction="out",
    )
    reached = sorted(str(n) for n in report.nodes)
    assert len(reached) == 2, reached
    assert any(str(n).startswith(f"{CMS}:entity:survey#") for n in report.nodes)
    assert any(str(n).startswith(f"{CMS}:entity:facility#") for n in report.nodes)
    assert sorted(ne.at_depth for ne in report.edges) == [1, 2]
    assert report.depth_reached == 2 and report.complete is True


@pytest.mark.cms
def test_c18_04_a_value_set_is_not_an_instance_endpoint_and_the_class_stays_out(registry):
    """T2.5 and T2.6 -- the decision UC2 forced, taken against UC1's interest.

    **T2.5**: `citation:42 --has_severity--> value_set:scope_severity_code` is refused,
    at two layers. A family declaring `value_set` at instance level cannot be declared
    at all, and a correctly declared family refuses the write on **level**.

    **T2.6, and it is the harder half**: the mechanical test was pre-registered so the
    answer could not be argued afterwards. *Does every property of the citation row fit
    on the `cites` edge?* If `Scope Severity Code` may ride there, so may the other
    nine, and `cites` becomes the citation row under another name -- with the registry
    storing node properties it has said three times it does not store. The answer is
    **yes, they all fit**, and therefore the whole class is refused.

    14 of beacon's 17 join families carry payload, so this costs UC1 something real
    (`EDGES.md` contortion E10). **CMS wins**, per the rule of the ordering.
    """
    load_cms_sample(registry)

    permissive = registry.propose_type(
        "has_severity", "a citation's scope-and-severity code", [], "user:sd",
        kind="edge",
        attributes={
            "level": "instance",
            "symmetric": False,
            "inverse_label": None,
            "endpoint_kinds": {"src": ["entity"], "dst": ["entity", "value_set"]},
        },
    )
    assert isinstance(permissive, Refusal), "the DECLARATION is refused"
    assert permissive.reason == "endpoint_kind_mismatch"
    assert permissive.detail["rule"] == "EDGES 2.4.1"

    edge_family(registry, "has_severity", definition="a citation's severity")
    write = registry.add_edge(
        "has_severity",
        InstanceRef(CITATION, "42"),
        TypeRef(CMS, "value_set", "scope_severity_code"),
        "user:sd",
    )
    assert isinstance(write, Refusal)
    assert write.reason == "endpoint_kind_mismatch"
    assert write.detail["problem"] == "level", (
        "the level check runs first -- a value_set reached as a TypeRef is not an "
        "InstanceRef, whatever endpoint_kinds says"
    )

    # T2.6: every citation property is single-valued per (citation, tag) pair, so all
    # ten WOULD fit on the edge -- which is exactly why the class is refused.
    from ._support import read_sample

    header, rows = read_sample()
    at = {name: i for i, name in enumerate(header)}
    properties = [
        "Deficiency Prefix", "Deficiency Category", "Scope Severity Code",
        "Deficiency Corrected", "Correction Date", "Standard Deficiency",
        "Complaint Deficiency", "Infection Control Inspection Deficiency",
        "Citation under IDR", "Citation under IIDR",
    ]
    fits = 0
    for prop in properties:
        if prop not in at:
            continue
        seen: dict[tuple[str, str], set[str]] = {}
        for index, row in enumerate(rows):
            key = (str(index), row[at["Deficiency Tag Number"]])
            seen.setdefault(key, set()).add(row[at[prop]])
        if all(len(v) == 1 for v in seen.values()):
            fits += 1
    assert fits == len([p for p in properties if p in at]), (
        "every one of them fits -- so if severity may ride on the edge, so may the "
        "other nine, and `cites` becomes the citation row under another name"
    )

    census = registry.list_types(include_retired=True, status=None, namespace=None)
    edge_families = {t.name for t in census.types if t.kind == "edge"}
    assert "scope_severity_code" not in {t.name for t in census.types if t.kind == "edge"}
    assert {t.name for t in census.types if t.kind == "value_set"} == {
        "deficiency_corrected_status",
        "scope_severity_code",
    }, "the two value sets stay value sets and appear in no edge"
    assert "has_severity" in edge_families, "the family exists; it has no legal edge"


# --------------------------------------------------------------------------- UC3, NYC


def _seed_boroughs(registry) -> dict:
    sample = nyc_edge_sample()
    for dataset, meta in sample["datasets"].items():
        seed(
            registry,
            "borough",
            kind="value_set",
            namespace=meta["namespace"],
            definition=(
                f"the five boroughs as {meta['namespace']} encodes them: "
                + ", ".join(sample["boroughs"][dataset])
            ),
            evidence=[Evidence(kind="data", summary=f"{dataset}, {len(sample['boroughs'][dataset])} values")],
        )
    return sample


def test_c18_05_three_borough_value_sets_a_chain_not_a_triangle_and_no_entailment(registry):
    """T3.1, T3.2 and T3.4 -- and T3.4 is the one that decides whether this family ships.

    Three publishers encode the same five referents three ways and one of them carries a
    sixth spelling of *unknown*. **This is why `equivalent_to` is not a merge:** the
    types denote the same thing and their value sets are not interchangeable.

    The realistic write order is a **chain, not a triangle** -- each publisher joins the
    one it found -- so `A ≡ B` and `B ≡ C` are written and `A ≡ C` is not. A depth-2
    walk from A therefore *reaches* C and does **not** assert that A and C are
    equivalent. `at_depth` is the only thing standing between that report and a
    manufactured equivalence class, and this checks that it does.

    > `neighbors` returns reachability. It never returns entailment.
    """
    sample = _seed_boroughs(registry)
    dpr = TypeRef("dpr", "value_set", "borough")
    oti = TypeRef("oti_311", "value_set", "borough")
    dot = TypeRef("dot", "value_set", "borough")

    assert sample["boroughs"]["uvpi-gqnh"] != sample["boroughs"]["erm2-nwe9"], (
        "same five referents, three encodings"
    )
    assert "Unspecified" in sample["boroughs"]["erm2-nwe9"], (
        "and B carries an extra spelling of unknown"
    )

    version = "; ".join(
        f"{d}@{m['data_updated_at']}" for d, m in sorted(sample["datasets"].items())
    )
    for src, dst in ((dpr, oti), (oti, dot)):
        out = registry.add_edge(
            EQUIVALENT_TO, src, dst, "user:dot",
            created_by="user", source_version=version,
        )
        assert not isinstance(out, Refusal), out

    one = registry.neighbors(dpr, [EQUIVALENT_TO], 1, namespace="default")
    assert one.known == 1 and one.complete is True
    assert [str(n) for n in one.nodes] == [str(oti)]

    two = registry.neighbors(dpr, [EQUIVALENT_TO], 2, namespace="default")
    assert sorted(str(n) for n in two.nodes) == sorted([str(oti), str(dot)])
    depths = {
        (str(ne.edge.src), str(ne.edge.dst)): ne.at_depth for ne in two.edges
    }
    assert depths[(str(dpr), str(oti))] == 1
    assert depths[(str(oti), str(dot))] == 2
    assert (str(dpr), str(dot)) not in depths and (str(dot), str(dpr)) not in depths, (
        "REACHED, and not asserted equivalent -- the family is explicitly not transitive"
    )

    # T3.10 -- staleness is on the row, not in a reader's head. A nine-year-old census
    # joined to a feed updated this week is a different claim from two current feeds.
    assert two.edges[0].edge.provenance.source_version == version
    assert "uvpi-gqnh@2017-10-04" in version and "erm2-nwe9@2026-08" in version


def test_c18_06_the_report_spans_namespaces_the_caller_never_named(registry):
    """T3.5 and T3.6, and §4.5's reasoning is why this is structural rather than lucky.

    `resolve_type` **searches**, so any answer it gives is scoped by which namespaces it
    chose -- that is contortion 8. `neighbors` **reads**: both endpoints of every edge
    are fully named before the call starts, so there is no set to choose. `namespace`
    scopes only the resolution of `edge_families`, and it filters nothing.

    **And `complete=True` here means one thing only**: every `equivalent_to` edge in
    this store was returned. It says nothing about the 2,399 datasets in the NYC
    catalogue, of which three are present -- which is why `families_searched` is a
    required field and not an echo.
    """
    _seed_boroughs(registry)
    dpr = TypeRef("dpr", "value_set", "borough")
    oti = TypeRef("oti_311", "value_set", "borough")
    dot = TypeRef("dot", "value_set", "borough")
    registry.add_edge(EQUIVALENT_TO, dpr, oti, "user:dot")
    registry.add_edge(EQUIVALENT_TO, oti, dot, "user:dot")

    report = registry.neighbors(dpr, [EQUIVALENT_TO], 2, namespace="default")
    assert {n.namespace for n in report.nodes} == {"oti_311", "dot"}, (
        "the caller named 'default' and the answer is in neither of these"
    )
    assert report.complete is True
    assert report.families_searched == (EQUIVALENT_TO,)


def test_c18_07_an_equivalence_edge_does_not_weaken_the_merge_refusal(registry):
    """T3.12 -- **the load-bearing check, and it is the kill row.**

    `ROADMAP.md`: *a capability predicate gets merged as a duplicate -> Stop*, and its
    generalisation, *the answer to collision must be scoping, not merging*. Before
    `equivalent_to` a steward who knew two scoped types denoted one thing had exactly
    one move available and it was the destructive one, refused. Now there is a
    non-destructive move that records the knowledge -- and the destructive one must
    still be refused, **twice, including under explicit acknowledgement**.

    An edge asserting sameness and a merge performing it are different acts. If this
    ever passes, `EDGES.md` §13 says the family should be withdrawn: an edge that becomes
    a licence is worse than no edge, because the refusal it erodes is the answer to the
    kill row.
    """
    _seed_boroughs(registry)
    dpr = TypeRef("dpr", "value_set", "borough")
    oti = TypeRef("oti_311", "value_set", "borough")
    written = registry.add_edge(EQUIVALENT_TO, dpr, oti, "user:dot")
    assert not isinstance(written, Refusal)

    refusal = registry.merge_types(
        "borough", "borough", "the same five boroughs", merged_by="user:dot",
        namespace="dpr", into_namespace="oti_311",
    )
    assert isinstance(refusal, Refusal)
    assert refusal.reason == "cross_namespace_merge"

    acknowledged = registry.merge_types(
        "borough", "borough", "the same five boroughs", merged_by="user:dot",
        namespace="dpr", into_namespace="oti_311",
        acknowledge=["cross_namespace_merge", "definitions_diverge"],
    )
    assert isinstance(acknowledged, Refusal), "non-overridable, with the edge present"
    assert acknowledged.reason == "cross_namespace_merge"

    still_there = registry.neighbors(dpr, [EQUIVALENT_TO], 1, namespace="default")
    assert still_there.known == 1, "and the edge is untouched by the refusal"


def test_c18_08_a_deterministic_key_join_is_many_to_many_and_confidence_carries_it(
    registry,
):
    """T3.7 -- the finding the pre-registered expectations did **not** anticipate.

    The BBL join is the most confident kind of join an ingestion layer can make: a
    deterministic key match on a tax lot present in both datasets. And it is
    **many-to-many** -- one lot carries up to 16 census trees, and 7 of 25 tree
    complaints matched no census tree at all. *"This complaint is about this tree"* is
    not entailed by *"this complaint and this tree share a tax lot"*.

    Two consequences, taken rather than argued. **The family is named for what the key
    proves**, `same_tax_lot`, not for what a reader wants, `concerns` -- a family name
    that overstates its evidence is mechanism 4 arriving through the vocabulary the edge
    store itself introduces. And **`confidence` is `1/n`**, so the sixteen-tree lot
    carries 0.0625 and a single-tree lot carries 1.0.
    """
    sample = nyc_edge_sample()
    seed(registry, "street_tree", namespace="dpr", definition="a NYC census street tree")
    seed(registry, "service_request", namespace="oti_311", definition="a 311 request")
    edge_family(
        registry, "same_tax_lot",
        definition="Both endpoints sit on the same borough-block-lot. It asserts the "
                   "shared lot and nothing more.",
        inverse_label="shares_tax_lot_with",
    )
    tree_t = TypeRef("dpr", "entity", "street_tree")
    request_t = TypeRef("oti_311", "entity", "service_request")

    by_bbl: dict[str, list[dict]] = {}
    for tree in sample["trees"]:
        by_bbl.setdefault(tree["bbl"], []).append(tree)
    assert len(sample["complaints"]) == 25
    assert len(by_bbl) <= 22 and len(sample["trees"]) == 54
    assert max(len(v) for v in by_bbl.values()) == 16, "one lot, sixteen trees"

    version = "; ".join(
        f"{d}@{m['data_updated_at']}" for d, m in sorted(sample["datasets"].items())
    )
    written = matched = 0
    for complaint in sample["complaints"]:
        trees = by_bbl.get(complaint["bbl"], [])
        if trees:
            matched += 1
        for tree in trees:
            out = registry.add_edge(
                "same_tax_lot",
                InstanceRef(request_t, complaint["unique_key"]),
                InstanceRef(tree_t, tree["tree_id"]),
                "import:socrata_bbl_join",
                # Ruling **R17**. Before it this had to claim `user` for a join no user
                # performed -- UC3 is one of the two unrelated fixtures that forced the
                # value, and this is where it lands.
                created_by="derived",
                confidence=round(1 / len(trees), 6),
                source_version=version,
                evidence=[
                    Evidence(
                        kind="data",
                        summary=f"BBL {complaint['bbl']} matches exactly; "
                                f"{len(trees)} census trees on that lot",
                        locator="uvpi-gqnh.bbl == erm2-nwe9.bbl",
                    )
                ],
                attributes={"bbl": complaint["bbl"], "trees_on_lot": len(trees)},
            )
            assert not isinstance(out, Refusal), out
            written += 1

    assert written == 102, "the pre-pinned edge count"
    assert matched == 18, "and 7 of 25 complaints matched no census tree at all"

    biggest = max(by_bbl.items(), key=lambda kv: len(kv[1]))[0]
    complaint = next(c for c in sample["complaints"] if c["bbl"] == biggest)
    report = registry.neighbors(
        InstanceRef(request_t, complaint["unique_key"]),
        ["same_tax_lot"], 1, namespace="default", direction="out",
    )
    assert report.known == 16
    assert {ne.edge.provenance.confidence for ne in report.edges} == {round(1 / 16, 6)}, (
        "1/n, so the most confident join an ingestion layer can make still does not "
        "establish the relationship a reader wants"
    )
    assert all(ne.edge.provenance.created_by == "derived" for ne in report.edges)
    assert all(ne.edge.provenance.evidence for ne in report.edges)


# ------------------------------------------------------- UC1, a work_links-shaped table


#: `EDGES.md` §7.2's table, as data. **[Observed 2026-08-29, read-only** from
#: `beacon/src/beacon/models/work_link.py`; nothing in beacon was edited, imported or
#: executed, and nothing of beacon's is vendored here.**]** These are column names and
#: the four values a comment documents -- the shape, not the data.
WORK_LINKS_ROWS = (
    # id, user_id, from_type, from_id, to_type, to_id, relationship, description, confidence, created_by
    (1, 7, "task", 41, "task", 77, "blocks", "the flagship query's first hop", 0.82, "user"),
    (2, 7, "task", 77, "project", 3, "part_of", None, None, "ai"),
    # R23's row: `relationship_type` is NULLABLE on `PersonLink` and there is no
    # `person_link_types` registry -- the labels are free text in a code comment.
    (3, None, "person", 11, "person", 12, None, "met at the offsite", 0.61, "interview"),
)


def _map_work_link(row) -> EdgeRecord | Refusal:
    """`EDGES.md` §7.2's mapping, as the adapter would perform it.

    Ten of eleven columns map. The contortions are the ones §9.4 enumerates and none is
    designed away here: **E4** the `Integer`-to-`str` cast on both endpoint ids, **E1**
    no provenance beyond three columns, **E2** no lifecycle columns (`status` and the
    three `retract_*` are the four-column additive migration §7.2 prices), **E3**
    tenancy has no home and `user_id` is deliberately not mapped onto `namespace`.
    """
    (link_id, _user_id, from_type, from_id, to_type, to_id,
     relationship, description, confidence, created_by) = row

    if relationship is None:
        # **Ruling R23.** `Edge.family` is required and `PersonLink.relationship_type`
        # is nullable. Skipping the row is a silent drop by the adapter -- mechanism C
        # committed at the seam -- and inventing a family asserts a fact the data does
        # not carry. Neither is taken: the adapter REFUSES to map it, explicitly, and
        # the honest third answer is on beacon's side (make the column NOT NULL).
        return Refusal(
            "edge_family_unknown",
            {
                "work_link_id": link_id,
                "why": (
                    "relationship_type is NULL and Edge.family is required: mapping "
                    "this row would either drop it silently or invent a family the "
                    "data does not carry (EDGES.md E6, ruling R23)"
                ),
            },
        )
    return EdgeRecord(
        edge_id=str(link_id),  # E4: Integer -> str, both ways
        namespace="default",  # a constant. The family is ADVISORY: no FK to work_link_types
        family=relationship,
        src_namespace="default", src_kind="entity", src_name=from_type,
        src_instance_id=str(from_id),
        dst_namespace="default", dst_kind="entity", dst_name=to_type,
        dst_instance_id=str(to_id),
        # E1: three provenance columns and no home for the rest.
        provenance={"created_by": created_by, "confidence": confidence,
                    "created_by_actor": f"beacon:{created_by}"},
        # E3: `description` is the ONE projected key. Everything else has nowhere to go.
        attributes={"description": description} if description is not None else {},
        # E2: no lifecycle columns today -- the four-column additive migration.
        status="active",
    )


def test_c18_09_a_work_links_shaped_row_maps_onto_the_protocol(adapter, make_registry):
    """`EDGES.md` §7.2 and §9.4's ten contortions, checked against the real protocol.

    The spec row read beacon's model file and asserted that ten of eleven columns map.
    Here the mapping is executed: the records go through `put_edge`, come back through
    `find_edges`, and the walk `deadline_cluster_service` stops one hop short of --
    *"the hop that turns 'what is blocking this' into 'who is blocking this'"* -- is
    answered at depth 2.

    **No beacon code, and nothing of beacon's is vendored.** The rows above are column
    names and a shape, read once, read-only.
    """
    # `EDGES.md` 7.2's declaration, built rather than described: `work_links` has
    # `description` and `confidence` as REAL TYPED COLUMNS and no JSON blob, so it
    # declares `stores_edge_attributes=False` with `description` projected. `True` would
    # silently lose arbitrary keys and `False` alone would disclaim a key the table
    # round-trips perfectly -- beacon finding U3, which is the whole reason 6.3 exists.
    host = DegradedAdapter(
        adapter,
        stores_edge_attributes=False,
        edge_attribute_projections=("description",),
        why={
            "stores_edge_attributes": (
                "work_links has description and confidence as columns and no JSON blob"
            )
        },
    )
    registry = make_registry(host)
    edge_family(registry, "blocks", inverse_label="blocked_by")
    edge_family(registry, "part_of", inverse_label="has_part")

    stored = []
    for row in WORK_LINKS_ROWS:
        mapped = _map_work_link(row)
        if isinstance(mapped, Refusal):
            continue
        stored.append(host.put_edge(mapped))

    assert len(stored) == 2, "the third row is refused, not dropped -- C18-10"
    assert [r.edge_id for r in stored] == ["1", "2"], "E4: the Integer id round-trips as text"
    assert stored[0].provenance["confidence"] == 0.82
    assert stored[0].provenance["created_by"] == "user"
    assert stored[1].attributes == {}, "a NULL description is absent, not empty-string"

    # E3 / beacon finding U3 -- the DECLARATION, which holds on every backend: this host
    # stores no arbitrary key and owns exactly one.
    caps = host.capabilities()
    assert caps.stores_edge_attributes is False
    assert caps.stores_edge_attribute("description") is True
    assert caps.stores_edge_attribute("anything_else") is False
    assert caps.surviving_edge_attributes({"description": "kept", "note": "lost"}) == {
        "description": "kept"
    }
    assert caps.reason("stores_edge_attributes").strip()

    # And the ROUND TRIP, which needs a store underneath with somewhere to put it. On a
    # backend that already stores no arbitrary attributes the projected key has nowhere
    # to land either, and asserting otherwise would be asserting that a double can
    # conjure a column -- so the declaration above is what binds everywhere and this
    # binds where there is a store to bind it against.
    if adapter.capabilities().stores_edge_attributes:
        assert stored[0].attributes == {
            "description": "the flagship query's first hop"
        }, "the ONE projected key, through its own column"

    # T1.7 -- beacon's flagship query, two hops, which is the whole argument for a cap
    # of 2 rather than 1.
    task = TypeRef("default", "entity", "task")
    report = registry.neighbors(
        InstanceRef(task, "41"), ["blocks", "part_of"], 2,
        namespace="default", direction="out",
    )
    assert sorted(str(n) for n in report.nodes) == [
        "default:entity:project#3",
        "default:entity:task#77",
    ]
    assert sorted(ne.at_depth for ne in report.edges) == [1, 2]
    assert report.complete is True

    # E2, priced: today's table has none of the four lifecycle columns, so retraction
    # costs one ALTER TABLE. The protocol's own record has all four.
    fields = set(EdgeRecord.__dataclass_fields__)
    assert {"status", "retract_reason", "retracted_by", "retracted_at"} <= fields

    # E3, refused rather than solved: tenancy has no home, and `user_id` is NOT mapped
    # onto `namespace`. Ruling **R24** -- namespace scopes a VOCABULARY, not a tenant,
    # and mapping tenancy onto it would give every user a private `blocks` family.
    assert {r.namespace for r in stored} == {"default"}, (
        "one namespace, whatever user_id says -- the filtering is the host's job (R24)"
    )


def test_c18_10_a_null_relationship_type_is_refused_explicitly_never_dropped(registry):
    """Ruling **R23**, and it is the reason this test exists as its own id.

    `PersonLink.relationship_type` is **nullable** and there is no `person_link_types`
    registry -- the eight labels are free text in a code comment. `Edge.family` is
    required. Two answers are available and both are wrong: skipping the row is a
    **silent drop by the adapter**, which is mechanism C committed at the seam, and
    inventing a family asserts a fact the data does not carry.

    R23 takes neither. The adapter refuses to map the row, in a shape a caller can read,
    and the honest third answer is on beacon's side. Recorded as `EDGES.md` contortion
    **E6** and relayed.
    """
    null_row = WORK_LINKS_ROWS[2]
    assert null_row[6] is None, "relationship_type is NULL on this row"

    mapped = _map_work_link(null_row)
    assert isinstance(mapped, Refusal), "not skipped -- a silent drop is the failure"
    assert mapped.reason == "edge_family_unknown"
    assert mapped.detail["work_link_id"] == 3
    assert "invent a family" in mapped.detail["why"]

    # And the registry says the same thing about the same data, through `add_edge`:
    # there is no family, so there is nothing to write it under.
    person = TypeRef("default", "entity", "person")
    refusal = registry.add_edge(
        "unclassified", InstanceRef(person, "11"), InstanceRef(person, "12"), "beacon:interview"
    )
    assert isinstance(refusal, Refusal) and refusal.reason == "edge_family_unknown", (
        "and a reserved `unclassified` family is a vocabulary this row would be "
        "INVENTING for a host's missing constraint -- R23 declines it"
    )
