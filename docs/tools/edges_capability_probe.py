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
    EdgeCapabilities,
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

    print("\n" + ("ALL CHECKS PASSED" if ok else "SOME CHECKS FAILED"))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
