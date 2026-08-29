"""EDGES.md v0 -- the operational machinery, EXECUTED rather than asserted.

Added by round 1 of the adversarial loop (EDGES.md 17). A reviewer's sharpest
finding was not a bug but a pattern: retraction, every capability-degradation
path, the dead-end walk and the `edge_families=None` shape were specified in
prose and run by nothing -- and the round's two BLOCKING defects were both
hiding in exactly that unrun half.

This probe drives them. It uses the CMS fixture where it needs a real leaf node
and synthetic edges where the point is a capability declaration rather than a
dataset.

    py docs/tools/edges_capability_probe.py
"""

from __future__ import annotations

import csv
import pathlib
import sys
from datetime import datetime

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

from docs.tools.edges_probe_kit import (  # noqa: E402
    DEFAULT_MAX_EDGES,
    EdgeCapabilities,
    EdgeQuery,
    assert_adapter_boundary,
    EdgeRegistry,
    EdgeStore,
    Family,
    InstanceRef,
    TypeRef,
    prov,
)

NS = "cms"
CITATION = TypeRef(NS, "entity", "citation")
TAG = TypeRef(NS, "entity", "deficiency_tag")
SURVEY = TypeRef(NS, "entity", "survey")
SAMPLE = (
    pathlib.Path(__file__).resolve().parents[2]
    / "open_ontology" / "contract" / "fixtures" / "cms_sample_400.csv"
)

CITES = Family(
    name="cites", level="instance", namespace=NS,
    definition="The citation cites this deficiency tag.",
    inverse_label="cited_by",
    endpoint_kinds={"src": ("entity",), "dst": ("entity",)},
)
NOW = datetime(2026, 8, 29, 12, 0, 0)


def check(label: str, got, want, notes: str = "") -> bool:
    ok = got == want
    print(f"  {'PASS' if ok else 'FAIL'}  {label}: got {got!r}, expected {want!r} {notes}")
    return ok


def main() -> int:  # noqa: C901
    ok = True

    # ---- 2.6 retraction, actually run -------------------------------------
    print("EDGES 2.6 -- retract_edge, on a store that CAN record events")
    store = EdgeStore()
    reg = EdgeRegistry(families=[CITES], store=store,
                       registered_types=[CITATION, TAG])
    e = reg.add_edge("cites", InstanceRef(CITATION, "1"), InstanceRef(TAG, "F684"),
                     prov("import:cms", "user"), namespace=NS)
    r = reg.retract_edge(e.edge_id, "the tag number was mis-keyed at ingest",
                         retracted_by="user:sd", at=NOW)
    ok &= check("status", r.status, "retracted")
    ok &= check("the row IS the record",
                (r.provenance.retract_reason, r.provenance.retracted_by),
                ("the tag number was mis-keyed at ingest", "user:sd"))
    ok &= check("nothing was deleted", store.get_edge(e.edge_id) is not None, True)
    ok &= check("no warning on a store that records events", r.warnings, ())
    try:
        reg.retract_edge(e.edge_id, "   ", retracted_by="user:sd", at=NOW)
        ok &= check("empty reason raises", False, True)
    except ValueError as exc:
        ok &= check("empty reason raises ValueError", True, True, f"-- {exc}")

    print("\nEDGES 2.6/4.3 -- a retracted edge is hidden by default, and complete says so")
    rep = reg.neighbors(InstanceRef(CITATION, "1"), ["cites"], 1, namespace=NS)
    ok &= check("edges", len(rep.edges), 0)
    ok &= check("complete is FALSE, because a default hid something", rep.complete, False)
    print(f"    why_incomplete: {rep.why_incomplete}")
    ok &= check("why_incomplete is populated", bool(rep.why_incomplete), True)
    rep2 = reg.neighbors(InstanceRef(CITATION, "1"), ["cites"], 1, namespace=NS,
                         include_retracted=True)
    ok &= check("include_retracted=True returns it, complete again",
                (len(rep2.edges), rep2.complete), (1, True))

    # ---- 6, every flag declined, one at a time ----------------------------
    print("\nEDGES 6 -- stores_edge_events=False: retraction SUCCEEDS and warns")
    caps_noev = EdgeCapabilities(
        stores_edge_events=False,
        why={"stores_edge_events": "work_links has no event table and beacon owns the schema"},
    )
    reg2 = EdgeRegistry(families=[CITES], store=EdgeStore(caps_noev),
                        registered_types=[CITATION, TAG])
    e2 = reg2.add_edge("cites", InstanceRef(CITATION, "2"), InstanceRef(TAG, "F686"),
                       prov("import:cms", "user"), namespace=NS)
    r2 = reg2.retract_edge(e2.edge_id, "superseded", retracted_by="user:sd", at=NOW)
    ok &= check("NOT refused -- the row is the record", getattr(r2, "refused", False), False)
    print(f"    warnings: {r2.warnings}")
    ok &= check("warns instead",
                any(w.startswith("retracted_without_event_trail:") for w in r2.warnings), True)
    ok &= check("the backend's own sentence is carried verbatim",
                caps_noev.why["stores_edge_events"] in r2.warnings[0], True)

    print("\nEDGES 3.2/6 -- PACKAGE 3.2's invariant: a False flag needs a why")
    try:
        EdgeCapabilities(stores_edge_events=False)
        ok &= check("a why-less False flag raises", False, True)
    except ValueError as exc:
        ok &= check("a why-less False flag raises ValueError", True, True, f"-- {exc}")

    print("\nEDGES 6 -- stores_edge_attributes=False plus a projection")
    caps_attr = EdgeCapabilities(
        stores_edge_attributes=False,
        edge_attribute_projections=frozenset({"description"}),
        why={"stores_edge_attributes":
             "work_links has description and confidence as columns and no JSON blob"},
    )
    reg3 = EdgeRegistry(families=[CITES], store=EdgeStore(caps_attr),
                        registered_types=[CITATION, TAG])
    e3 = reg3.add_edge("cites", InstanceRef(CITATION, "3"), InstanceRef(TAG, "F550"),
                       prov("import:cms", "user"), namespace=NS,
                       attributes={"description": "kept", "severity": "lost"})
    ok &= check("the projected key survives", e3.attributes.get("description"), "kept")
    ok &= check("the non-projected key is ABSENT, not empty-valued",
                "severity" in e3.attributes, False)
    ok &= check("and NO warning was minted for it", e3.warnings, (),
                "-- PACKAGE 3.4 primitive 4: the returned record IS the signal")

    print("\nEDGES 6.2 -- edge_transaction_scope='savepoint' stamps WRITES, never reads")
    caps_sp = EdgeCapabilities(
        edge_transaction_scope="savepoint",
        why={"edge_transaction_scope":
             "this adapter runs over a connection the host owns; the host commits"},
    )
    reg4 = EdgeRegistry(families=[CITES], store=EdgeStore(caps_sp),
                        registered_types=[CITATION, TAG])
    e4 = reg4.add_edge("cites", InstanceRef(CITATION, "4"), InstanceRef(TAG, "F812"),
                       prov("import:cms", "user"), namespace=NS)
    ok &= check("the write carries it",
                any(w.startswith("not_durable_until_host_commits:") for w in e4.warnings), True)
    rep4 = reg4.neighbors(InstanceRef(CITATION, "4"), ["cites"], 1, namespace=NS)
    ok &= check("the READ carries nothing", rep4.warnings, (),
                "-- a signal that never turns off is noise (row 3d's lesson)")

    print("\nEDGES 6 -- stores_edges=False: every call refuses, none returns an empty report")
    caps_none = EdgeCapabilities(
        stores_edges=False,
        why={"stores_edges": "this backend is a type registry only; no table holds relationships"},
    )
    reg5 = EdgeRegistry(families=[CITES], store=EdgeStore(caps_none),
                        registered_types=[CITATION, TAG])
    for label, call in (
        ("add_edge", lambda: reg5.add_edge("cites", InstanceRef(CITATION, "5"),
                                           InstanceRef(TAG, "F550"),
                                           prov("import:cms", "user"), namespace=NS)),
        ("neighbors", lambda: reg5.neighbors(InstanceRef(CITATION, "5"), ["cites"], 1,
                                             namespace=NS)),
        ("retract_edge", lambda: reg5.retract_edge("e1", "x", retracted_by="u", at=NOW)),
    ):
        out = call()
        ok &= check(f"{label} refuses", getattr(out, "reason", None), "edge_store_absent")

    # ---- 4.3 the dead end vs the truncated walk --------------------------
    print("\nEDGES 4.3 -- a REAL dead end (a CMS deficiency_tag sink) is complete=True")
    with SAMPLE.open(newline="", encoding="utf-8-sig") as fh:
        rows = list(csv.DictReader(fh))
    store6 = EdgeStore()
    reg6 = EdgeRegistry(families=[CITES], store=store6, registered_types=[CITATION, TAG])
    for i, row in enumerate(rows):
        reg6.add_edge("cites", InstanceRef(CITATION, str(i)),
                      InstanceRef(TAG, row["Deficiency Tag Number"]),
                      prov("import:cms", "user"), namespace=NS)
    a_tag = rows[0]["Deficiency Tag Number"]
    leaf = reg6.neighbors(InstanceRef(TAG, a_tag), ["cites"], 2, namespace=NS,
                          direction="out")
    print(f"    tag {a_tag} walked out-only to depth 2: known={leaf.known} "
          f"depth_reached={leaf.depth_reached} complete={leaf.complete}")
    ok &= check("nothing found", leaf.known, 0)
    ok &= check("depth_reached < depth_requested",
                leaf.depth_reached < leaf.depth_requested, True)
    ok &= check("and complete is TRUE -- ran out of graph, not cut short",
                leaf.complete, True)
    ok &= check("with no why_incomplete", leaf.why_incomplete, None)

    # ---- 4.1/4.3 edge_families=None spans EVERY namespace ----------------
    print("\nEDGES 4.1 -- edge_families=None spans every namespace (round 1's BLOCKING)")
    hub = InstanceRef(TypeRef("dpr", "entity", "street_tree"), "434008")
    fam_a = Family(name="in_lot", level="instance", namespace="dpr",
                   definition="tree on a lot", inverse_label="lot_of",
                   endpoint_kinds={"src": ("entity",), "dst": ("entity",)})
    fam_b = Family(name="reported_by", level="instance", namespace="oti_311",
                   definition="tree reported by a request", inverse_label="reported",
                   endpoint_kinds={"src": ("entity",), "dst": ("entity",)})
    store7 = EdgeStore()
    reg7 = EdgeRegistry(families=[fam_a, fam_b], store=store7, registered_types=[hub.type])
    reg7.add_edge("in_lot", hub, InstanceRef(TypeRef("dpr", "entity", "tax_lot"), "3042290028"),
                  prov("import:socrata", "user"), namespace="dpr")
    reg7.add_edge("reported_by", hub,
                  InstanceRef(TypeRef("oti_311", "entity", "service_request"), "47124985"),
                  prov("import:socrata", "user"), namespace="oti_311")
    for ns in ("dpr", "oti_311", "default"):
        rep7 = reg7.neighbors(hub, None, 1, namespace=ns)
        print(f"    namespace={ns:8s} families_searched={rep7.families_searched} known={rep7.known}")
        ok &= check(f"both families found from namespace={ns}", rep7.known, 2,
                    "-- scoping this to `namespace` was Cause C inside the read seam")

    # ---- 2.4.1 the general predicate ban, and edge-kind endpoints --------
    print("\nEDGES 2.4.1 -- `predicate` is refused as an endpoint kind at DECLARATION time")
    try:
        Family(name="same_capability", level="type",
               definition="two predicates that mean the same capability",
               symmetric=True,
               endpoint_kinds={"src": ("predicate",), "dst": ("predicate",)})
        ok &= check("a predicate-endpoint family is refused", False, True)
    except ValueError as exc:
        ok &= check("a predicate-endpoint family raises", True, True, f"-- {exc}")

    print("\nEDGES 2.4.1 -- a kind='edge' TYPE endpoint is legal; an edge INSTANCE is not")
    eq = Family(name="equivalent_to", level="type", namespace="default",
                definition="the two types denote the same thing", symmetric=True,
                endpoint_kinds={"src": ("entity", "value_set", "edge"),
                                "dst": ("entity", "value_set", "edge")})
    concerns = TypeRef("dpr", "edge", "concerns")
    relates = TypeRef("oti_311", "edge", "relates_to")
    reg8 = EdgeRegistry(families=[eq], store=EdgeStore(),
                        registered_types=[concerns, relates])
    out8 = reg8.add_edge("equivalent_to", concerns, relates,
                         prov("user:steward", "user", confidence=0.8))
    ok &= check("two edge FAMILIES may be declared equivalent",
                getattr(out8, "refused", False), False,
                "-- a row of the vocabulary, not a reification")
    # An instance-level family that DECLARES an edge endpoint is refused at
    # declaration time -- so a reifying edge cannot be written at all. The first
    # version of this check tried to write one and it went through: the kit
    # checked membership in endpoint_kinds and the family had declared `edge`,
    # so the reification ban was a rule the family author could opt out of --
    # the same defect round 1 found in the predicate clause, one clause along.
    try:
        Family(name="derived_from", level="instance", namespace="default",
               definition="one edge derived from another", inverse_label="derived",
               endpoint_kinds={"src": ("entity",), "dst": ("entity", "edge")})
        ok &= check("an instance family declaring an edge endpoint is refused",
                    False, True)
    except ValueError as exc:
        ok &= check("an instance family declaring an edge endpoint raises",
                    True, True, f"-- {exc}")

    # And the write-time check still holds for a well-declared family.
    inst_fam = Family(name="cites_tag", level="instance", namespace="default",
                      definition="a citation cites a tag", inverse_label="cited_by",
                      endpoint_kinds={"src": ("entity",), "dst": ("entity",)})
    reg9 = EdgeRegistry(families=[inst_fam], store=EdgeStore(),
                        registered_types=[CITATION, concerns])
    out9 = reg9.add_edge("cites_tag", InstanceRef(CITATION, "1"),
                         InstanceRef(concerns, "e42"), prov("user:x", "user"))
    ok &= check("an edge INSTANCE endpoint is refused at write time too",
                getattr(out9, "reason", None), "endpoint_kind_mismatch")
    if getattr(out9, "refused", False):
        print(f"    detail={out9.detail}")
        ok &= check("...on the KIND, which is the reification ban",
                    out9.detail["problem"], "kind")

    # ---- round 2: direction on a SYMMETRIC family ------------------------
    print("\nEDGES 2.2/4.1 -- `direction` does not filter a SYMMETRIC family")
    eq = Family(name="equivalent_to", level="type", namespace="default",
                definition="the two types denote the same thing", symmetric=True,
                endpoint_kinds={"src": ("value_set",), "dst": ("value_set",)})
    BA = TypeRef("dpr", "value_set", "borough")
    BB = TypeRef("dot", "value_set", "borough")
    reg_s = EdgeRegistry(families=[eq], store=EdgeStore(), registered_types=[BA, BB])
    reg_s.add_edge("equivalent_to", BA, BB, prov("user:dpr_steward", "user"))
    seen = {}
    for node, d in ((BA, "out"), (BB, "out"), (BA, "in"), (BB, "in"),
                    (BA, "both"), (BB, "both")):
        rep = reg_s.neighbors(node, ["equivalent_to"], 1, namespace="default",
                              direction=d)
        seen[(str(node), d)] = rep.known
    print(f"    known by (origin, direction): { {k: v for k, v in seen.items()} }")
    ok &= check("every origin/direction combination finds the one edge",
                sorted(set(seen.values())), [1],
                "-- `A eq B` IS `B eq A`; filtering on stored src/dst gave a "
                "confident complete=True FALSE NEGATIVE from one end")

    print("\nEDGES 4.1 -- a DIRECTED family still filters")
    blocks = Family(name="blocks", level="instance", namespace="default",
                    definition="src blocks dst", inverse_label="blocked_by",
                    endpoint_kinds={"src": ("entity",), "dst": ("entity",)})
    TK = TypeRef("t", "entity", "task")
    reg_d = EdgeRegistry(families=[blocks], store=EdgeStore(), registered_types=[TK])
    reg_d.add_edge("blocks", InstanceRef(TK, "41"), InstanceRef(TK, "77"),
                   prov("ai:classifier", "ai", confidence=0.8))
    outs = reg_d.neighbors(InstanceRef(TK, "41"), ["blocks"], 1,
                           namespace="default", direction="out").known
    ins = reg_d.neighbors(InstanceRef(TK, "41"), ["blocks"], 1,
                          namespace="default", direction="in").known
    ok &= check("out finds it, in does not", (outs, ins), (1, 0))

    # ---- round 2: the dead end under the DEFAULT direction ---------------
    print("\nEDGES 4.3 -- the dead end holds under the DEFAULT direction='both'")
    reg_de = EdgeRegistry(families=[CITES], store=EdgeStore(),
                          registered_types=[CITATION, TAG])
    reg_de.add_edge("cites", InstanceRef(CITATION, "1"), InstanceRef(TAG, "F684"),
                    prov("import:cms", "user"), namespace=NS)
    for d in ("both", "out"):
        rep = reg_de.neighbors(InstanceRef(CITATION, "1"), ["cites"], 2,
                               namespace=NS, direction=d)
        print(f"    direction={d:4s} depth_reached={rep.depth_reached}/"
              f"{rep.depth_requested} complete={rep.complete}")
        ok &= check(f"depth_reached is 1, not 2, with direction={d}",
                    rep.depth_reached, 1,
                    "-- counting 'the scan returned records' made the frontier "
                    "re-find its arriving edge and call that progress")
        ok &= check(f"and complete stays True with direction={d}", rep.complete, True)

    # ---- round 2: indexes_edges_by_family=False, actually implemented ----
    print("\nEDGES 6/7.1 -- indexes_edges_by_family=False: the store cannot filter")
    caps_noidx = EdgeCapabilities(
        indexes_edges_by_family=False,
        why={"indexes_edges_by_family":
             "work_links.relationship is free text with no index"},
    )
    store_ni = EdgeStore(caps_noidx)
    reg_ni = EdgeRegistry(families=[CITES, blocks], store=store_ni,
                          registered_types=[CITATION, TAG, TK])
    reg_ni.add_edge("cites", InstanceRef(CITATION, "9"), InstanceRef(TAG, "F684"),
                    prov("import:cms", "user"), namespace=NS)
    reg_ni.add_edge("blocks", InstanceRef(CITATION, "9"), InstanceRef(CITATION, "10"),
                    prov("user:x", "user"), namespace="default")
    raw = store_ni.find_edges(EdgeQuery(
        incident_to=((NS, "entity", "citation", "9"),), families=("cites",)))
    ok &= check("the STORE ignores the family filter and returns both",
                len(raw.records), 2)
    ok &= check("...and says its page IS complete for what it was asked",
                raw.complete, True,
                "-- the deliberate deviation from find_types' rule, EDGES 7.1")
    rep_ni = reg_ni.neighbors(InstanceRef(CITATION, "9"), ["cites"], 1, namespace=NS)
    ok &= check("the REGISTRY narrows above the store", rep_ni.known, 1)
    ok &= check("families_searched is the caller's, not the store's",
                rep_ni.families_searched, ("cites",))
    ok &= check("and the answer is still complete", rep_ni.complete, True)

    # ---- round 2: degree, not depth, is the unbounded axis ---------------
    print("\nEDGES 4.2 -- the cap bounds HOPS, not degree: a hub at depth 1")
    hub = InstanceRef(TypeRef("oti_311", "entity", "agency"), "NYPD")
    reg_hub = EdgeRegistry(families=[CITES], store=EdgeStore(),
                           registered_types=[CITATION, TAG, hub.type],
                           max_edges=500, page_size=64)
    for i in range(2000):
        reg_hub.add_edge("cites", InstanceRef(CITATION, f"r{i}"), hub,
                         prov("import:socrata", "user"), namespace=NS)
    rep_hub = reg_hub.neighbors(hub, ["cites"], 1, namespace=NS)
    print(f"    2000 edges on one node, max_edges=500, page_size=64 -> "
          f"known={rep_hub.known} complete={rep_hub.complete}")
    print(f"    why_incomplete: {rep_hub.why_incomplete}")
    ok &= check("the report is bounded", rep_hub.known <= 500, True)
    ok &= check("and says so rather than truncating silently", rep_hub.complete, False)
    ok &= check("with a why naming the bound", "assembly bound" in
                (rep_hub.why_incomplete or ""), True)

    print("\nEDGES 7.1 -- with NO bound, the registry exhausts the pages per level")
    reg_pg = EdgeRegistry(families=[CITES], store=EdgeStore(),
                          registered_types=[CITATION, TAG, hub.type],
                          page_size=64)
    for i in range(300):
        reg_pg.add_edge("cites", InstanceRef(CITATION, f"p{i}"), hub,
                        prov("import:socrata", "user"), namespace=NS)
    rep_pg = reg_pg.neighbors(hub, ["cites"], 1, namespace=NS)
    ok &= check("all 300 assembled from 64-row pages", rep_pg.known, 300,
                "-- a level built from one page of five would be silently partial")
    ok &= check("and complete", rep_pg.complete, True)

    # ---- round 3: the assembly bound counts DISTINCT edges ---------------
    print("\nEDGES 4.2 -- the assembly bound counts DISTINCT edges (round 3)")
    N = TypeRef("t", "entity", "n")
    rel = Family(name="rel", level="instance", namespace="default",
                 definition="a relation", inverse_label="rel_by",
                 endpoint_kinds={"src": ("entity",), "dst": ("entity",)})
    reg_b = EdgeRegistry(families=[rel], store=EdgeStore(), registered_types=[N],
                         max_edges=20, page_size=8)
    hub2 = InstanceRef(N, "hub")
    leaves = [InstanceRef(N, f"L{i}") for i in range(15)]
    for lf in leaves:
        reg_b.add_edge("rel", hub2, lf, prov("u", "user"))
    for i in range(4):          # leaf-leaf edges, only reachable at depth 2
        reg_b.add_edge("rel", leaves[i], leaves[i + 1], prov("u", "user"))
    rep_b = reg_b.neighbors(hub2, ["rel"], 2, namespace="default")
    print(f"    19 distinct edges, max_edges=20 -> known={rep_b.known} "
          f"complete={rep_b.complete} why={rep_b.why_incomplete}")
    ok &= check("all 19 returned", rep_b.known, 19,
                "-- comparing the bound against the RAW page dropped 4 and "
                "claimed a bound nothing crossed")
    ok &= check("and complete, because the bound was NOT hit", rep_b.complete, True)
    ok &= check("with no why", rep_b.why_incomplete, None)

    print("\nEDGES 4.2 -- and it still fires when the bound IS genuinely hit")
    reg_b2 = EdgeRegistry(families=[rel], store=EdgeStore(), registered_types=[N],
                          max_edges=10, page_size=4)
    for lf in leaves:
        reg_b2.add_edge("rel", hub2, lf, prov("u", "user"))
    rep_b2 = reg_b2.neighbors(hub2, ["rel"], 2, namespace="default")
    ok &= check("bounded", rep_b2.known <= 10, True)
    ok &= check("and says so", rep_b2.complete, False)

    print("\nEDGES 4.2 -- the bound is ON BY DEFAULT, not opt-in")
    ok &= check("a registry built with no arguments has a bound",
                EdgeRegistry(families=[rel], store=EdgeStore()).max_edges,
                DEFAULT_MAX_EDGES,
                "-- an opt-in circuit breaker leaves the DEFAULT as the "
                "unbounded fetch R13 exists to prevent")
    ok &= check("and disabling it is a deliberate act",
                EdgeRegistry(families=[rel], store=EdgeStore(),
                             max_edges=None).max_edges, None)

    # ---- round 3: retract_edge stamps its own durability warning ---------
    print("\nEDGES 6.2 -- retract_edge stamps the savepoint warning ITSELF")
    caps_sp2 = EdgeCapabilities(
        edge_transaction_scope="savepoint",
        why={"edge_transaction_scope": "this adapter runs over a host-owned connection"},
    )
    reg_r = EdgeRegistry(families=[rel], store=EdgeStore(caps_sp2),
                         registered_types=[N])
    e_r = reg_r.add_edge("rel", InstanceRef(N, "a"), InstanceRef(N, "b"),
                         prov("u", "user"))
    # Simulate an edge the host committed in an EARLIER transaction: durable,
    # so it carries no warning of its own.
    from dataclasses import replace as _replace

    from docs.tools.edges_probe_kit import _to_record

    reg_r.store.put_edge(_to_record(_replace(e_r, warnings=())))
    out_r = reg_r.retract_edge(e_r.edge_id, "superseded", retracted_by="user:sd",
                               at=NOW)
    print(f"    warnings: {out_r.warnings}")
    ok &= check("the retraction carries it on its own",
                any(w.startswith("not_durable_until_host_commits:")
                    for w in out_r.warnings), True,
                "-- it was INHERITED from the edge's prior state, so retracting "
                "an already-durable edge came back looking durable")

    print("\nEDGES 2.6 -- retract_edge on an edge that does not exist")
    miss = reg_r.retract_edge("no-such-edge", "x", retracted_by="u", at=NOW)
    ok &= check("reason", getattr(miss, "reason", None), "unknown_edge",
                "-- it reused `edge_family_unknown`, which names a different "
                "failure: INTERFACE 2.3's Cause B")

    # ---- round 3: the adapter boundary, checked the way C0-04 checks it --
    print("\nPACKAGE 3.1 -- the probe's own adapter speaks records, not the facade")
    try:
        assert_adapter_boundary()
        ok &= check("EdgeStore mentions no facade shape and speaks EdgeRecord/"
                    "EdgePage", True, True)
    except AssertionError as exc:
        ok &= check("adapter boundary", False, True, f"-- {exc}")

    # ---- round 3 MINOR: self-loops and the triangle ----------------------
    print("\nEDGES 4.1 -- a self-loop counts in `known` and adds no `nodes`")
    reg_sl = EdgeRegistry(families=[rel], store=EdgeStore(), registered_types=[N])
    reg_sl.add_edge("rel", InstanceRef(N, "A"), InstanceRef(N, "A"), prov("u", "user"))
    rep_sl = reg_sl.neighbors(InstanceRef(N, "A"), ["rel"], 1, namespace="default")
    ok &= check("known counts the edge", rep_sl.known, 1)
    ok &= check("nodes is empty -- `origin excluded` covers both ends",
                len(rep_sl.nodes), 0)

    print("\nEDGES 4.4 -- at_depth marks the EDGE's level, not the node's")
    reg_tri = EdgeRegistry(families=[rel], store=EdgeStore(), registered_types=[N])
    for a, b in (("A", "B"), ("A", "C"), ("B", "C")):
        reg_tri.add_edge("rel", InstanceRef(N, a), InstanceRef(N, b), prov("u", "user"))
    rep_tri = reg_tri.neighbors(InstanceRef(N, "A"), ["rel"], 2, namespace="default")
    depths = {f"{ne.edge.src}->{ne.edge.dst}": ne.at_depth for ne in rep_tri.edges}
    print(f"    triangle A-B, A-C, B-C from A: {depths}")
    ok &= check("all three edges returned", rep_tri.known, 3)
    ok &= check("B->C is at_depth 2 though BOTH its ends were reached at depth 1",
                depths.get("t:entity:n#B->t:entity:n#C"), 2,
                "-- at_depth is a property of the EDGE's discovery, not of a "
                "newly-reached node")

    print("\n" + ("ALL CHECKS PASSED" if ok else "SOME CHECKS FAILED"))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
