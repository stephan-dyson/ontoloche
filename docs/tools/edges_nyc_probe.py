"""UC3 design test for EDGES.md v0 -- cross-agency edges over three NYC datasets.

Drives the three datasets pinned by ``USE-CASES.md`` UC3 and ``3C-VALIDATION.md``
§1 -- ``uvpi-gqnh`` (DPR trees), ``erm2-nwe9`` (311/OTI service requests),
``693u-uax6`` (DOT parking meters) -- through EDGES v0.

Two engines, deliberately:

* the **real** ``open_ontology.Registry`` on SQLite for anything about types --
  in particular T3.12, that an ``equivalent_to`` edge does NOT weaken
  ``merge_types``' non-overridable ``cross_namespace_merge`` refusal. That claim
  is about the shipped registry, so it is checked against the shipped registry.
* the throwaway ``edges_probe_kit`` for anything about edges, because row #4
  ships no edge store.

Live network. Public data. Run:

    py docs/tools/edges_nyc_probe.py

Standing constraint 0: public NYC Open Data only, nothing pulled is committed.
"""

from __future__ import annotations

import json
import pathlib
import sys
import urllib.parse
import urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

from docs.tools.edges_probe_kit import (  # noqa: E402
    EdgeRegistry,
    EdgeStore,
    Family,
    InstanceRef,
    TypeRef,
    prov,
)
from open_ontology import Evidence, NamespacePolicy, Registry  # noqa: E402
from open_ontology.backends.sqlite import SQLiteAdapter  # noqa: E402

# Pinned so the test is reproducible. 3C-VALIDATION.md §1.
A, B, C = "uvpi-gqnh", "erm2-nwe9", "693u-uax6"
DATA_UPDATED = {A: "2017-10-04", B: "2026-08-28", C: "2026-08-24"}
NS_A, NS_B, NS_C = "dpr", "oti_311", "dot"

BOROUGH_A = TypeRef(NS_A, "value_set", "borough")
BOROUGH_B = TypeRef(NS_B, "value_set", "borough")
BOROUGH_C = TypeRef(NS_C, "value_set", "borough")
TREE = TypeRef(NS_A, "entity", "street_tree")
REQUEST = TypeRef(NS_B, "entity", "service_request")


def soda(dataset: str, **params: str) -> list[dict]:
    url = f"https://data.cityofnewyork.us/resource/{dataset}.json?" + urllib.parse.urlencode(
        {f"${k}": v for k, v in params.items()}
    )
    with urllib.request.urlopen(url, timeout=90) as fh:
        return json.load(fh)


def check(label: str, got, want, notes: str = "") -> bool:
    ok = got == want
    print(f"  {'PASS' if ok else 'FAIL'}  {label}: got {got!r}, expected {want!r} {notes}")
    return ok


def main() -> int:
    ok = True

    # ---- the three borough value sets, live -------------------------------
    print("The three `borough` value sets, pulled live (W2's data, re-verified)")
    vals = {}
    for ns, ds, fieldname in ((NS_A, A, "boroname"), (NS_B, B, "borough"), (NS_C, C, "borough")):
        rows = soda(ds, select=f"{fieldname}", group=fieldname, limit="50")
        v = sorted({r.get(fieldname) for r in rows if r.get(fieldname)})
        vals[ns] = v
        print(f"    {ns:8s} {ds}  {len(v)} values: {v}")
    ok &= check("all three carry five borough names (B adds Unspecified)",
                all(len([x for x in v if x.lower() != "unspecified"]) == 5
                    for v in vals.values()), True)
    ok &= check("the encodings differ, so they are NOT one value set",
                len({tuple(sorted(x.lower() for x in v)) for v in vals.values()}) > 1, True,
                "-- B carries `Unspecified`; A/B/C differ in case")

    # ---- T3.1 register three scoped types in the REAL registry ------------
    print("\nT3.1 -- three scoped `borough` value_set types in the shipped registry")
    reg = Registry(
        SQLiteAdapter.open(":memory:"),
        policies={
            ns: NamespacePolicy(namespace=ns, approval_policy="auto",
                                min_auto_approve_tier="sonnet")
            for ns in (NS_A, NS_B, NS_C)
        },
    )
    entries = {}
    for ns in (NS_A, NS_B, NS_C):
        entries[ns] = reg.propose_type(
            "borough",
            definition=("The five county-level divisions of New York City, as encoded "
                        f"by this publisher: {vals[ns]}"),
            evidence=[Evidence(kind="data",
                               summary=f"{len(vals[ns])} distinct values, grouped over the "
                                       f"full dataset via the SODA API",
                               locator=f"https://data.cityofnewyork.us/resource/"
                                       f"{ {NS_A: A, NS_B: B, NS_C: C}[ns] }.json")],
            proposed_by="ai:probe", kind="value_set", namespace=ns, tier="opus",
        )
    ok &= check("three coexisting entries", [type(e).__name__ for e in entries.values()],
                ["TypeEntry"] * 3)
    ok &= check("each keeps its own word",
                sorted(f"{ns}:{entries[ns].name}" for ns in entries),
                ["dot:borough", "dpr:borough", "oti_311:borough"])

    # ---- the equivalent_to family and the CHAIN (T3.2) ---------------------
    print("\nT3.2 -- the realistic write order is a CHAIN: A=B and B=C, not a triangle")
    equivalent_to = Family(
        name="equivalent_to", namespace="default",
        definition=("The two types denote the same thing in their respective "
                    "vocabularies. Non-merging, non-transitive."),
        level="type", symmetric=True, inverse_label=None,
        endpoint_kinds={"src": ("entity", "value_set", "edge"),
                        "dst": ("entity", "value_set", "edge")},
    )
    store = EdgeStore()
    ereg = EdgeRegistry(
        families=[equivalent_to], store=store,
        registered_types=[BOROUGH_A, BOROUGH_B, BOROUGH_C, TREE, REQUEST],
    )
    e_ab = ereg.add_edge(
        "equivalent_to", BOROUGH_A, BOROUGH_B,
        prov("user:dpr_steward", "user", confidence=1.0,
             source_version=f"{A}@{DATA_UPDATED[A]} / {B}@{DATA_UPDATED[B]}",
             evidence=({"kind": "data",
                        "summary": "identical five referents; encodings differ "
                                   "(Title vs UPPER)"},)),
    )
    e_bc = ereg.add_edge(
        "equivalent_to", BOROUGH_B, BOROUGH_C,
        prov("user:dot_steward", "user", confidence=1.0,
             source_version=f"{B}@{DATA_UPDATED[B]} / {C}@{DATA_UPDATED[C]}"),
    )
    ok &= check("two edges written", [getattr(e, "family", None) for e in (e_ab, e_bc)],
                ["equivalent_to", "equivalent_to"])

    # ---- T3.3 / T3.4 / T3.5 / T3.6 the read seam ---------------------------
    print("\nT3.3 -- neighbors(dpr:borough, [equivalent_to], depth=1)")
    r1 = ereg.neighbors(BOROUGH_A, ["equivalent_to"], 1, namespace="default")
    ok &= check("nodes", [str(n) for n in r1.nodes], ["oti_311:value_set:borough"])
    ok &= check("known", r1.known, 1)
    ok &= check("complete", r1.complete, True)

    print("\nT3.4 -- depth=2 reaches dot:borough, which is NOT asserted equivalent")
    r2 = ereg.neighbors(BOROUGH_A, ["equivalent_to"], 2, namespace="default")
    ok &= check("nodes", sorted(str(n) for n in r2.nodes),
                ["dot:value_set:borough", "oti_311:value_set:borough"])
    # Key by the EDGE, not by an endpoint: the second edge's src is oti_311,
    # not the origin, so keying by "the far end" collapses the two.
    depths = {f"{ne.edge.src} -> {ne.edge.dst}": ne.at_depth for ne in r2.edges}
    print(f"    at_depth per edge: {depths}")
    ok &= check("the A=B edge is at_depth 1",
                depths.get("dpr:value_set:borough -> oti_311:value_set:borough"), 1)
    ok &= check("the B=C edge is at_depth 2",
                depths.get("oti_311:value_set:borough -> dot:value_set:borough"), 2,
                "-- reachability, NOT entailment (EDGES 4.4)")
    # And the point of at_depth: nothing in the report says dpr = dot.
    ok &= check("no edge in the report has dpr:borough and dot:borough as its two ends",
                any({str(ne.edge.src), str(ne.edge.dst)}
                    == {str(BOROUGH_A), str(BOROUGH_C)} for ne in r2.edges), False)

    print("\nT3.5/T3.6 -- namespaces spanned, and what `complete` is over")
    spanned = sorted({n.namespace for n in r2.nodes})
    ok &= check("namespaces in the report", spanned, ["dot", "oti_311"],
                "-- the caller named `default` and got neither")
    ok &= check("complete", r2.complete, True)
    ok &= check("families_searched is on the report", r2.families_searched,
                ("equivalent_to",),
                "-- complete=True is unreadable without it (EDGES 4.4)")

    # ---- T3.12 the load-bearing check: merge_types is untouched -----------
    print("\nT3.12 -- with the equivalent_to edge WRITTEN, merge_types must still refuse")
    m = reg.merge_types("borough", "borough", reason="they denote the same five boroughs",
                        merged_by="user:probe", namespace=NS_A, into_namespace=NS_B)
    ok &= check("refused", getattr(m, "refused", False), True)
    ok &= check("reason", getattr(m, "reason", None), "cross_namespace_merge")
    m2 = reg.merge_types("borough", "borough", reason="acknowledged", merged_by="user:probe",
                         namespace=NS_A, into_namespace=NS_B,
                         acknowledge=["cross_namespace_merge", "definitions_diverge"])
    ok &= check("still refused with acknowledge", getattr(m2, "refused", False), True)
    ok &= check("reason unchanged", getattr(m2, "reason", None), "cross_namespace_merge",
                "-- non-overridable means non-overridable")

    # ---- T3.9 an instance-level family may not point at a value_set -------
    print("\nT3.9 -- dpr:street_tree#X --in_borough--> dpr:value_set:borough")
    in_borough = Family(
        name="in_borough", namespace=NS_A, level="instance",
        definition="The tree stands in this borough.", inverse_label="contains_tree",
        endpoint_kinds={"src": ("entity",), "dst": ("entity", "value_set")},
    )
    ereg2 = EdgeRegistry(
        families=[equivalent_to, in_borough], store=EdgeStore(),
        registered_types=[BOROUGH_A, BOROUGH_B, BOROUGH_C, TREE, REQUEST],
    )
    out = ereg2.add_edge("in_borough", InstanceRef(TREE, "434008"), BOROUGH_A,
                         prov("import:socrata", "user"), namespace=NS_A)
    ok &= check("refused", getattr(out, "refused", False), True)
    ok &= check("reason", getattr(out, "reason", None), "endpoint_kind_mismatch")
    if getattr(out, "refused", False):
        print(f"    detail={out.detail}")

    # ---- T3.7 a real cross-agency instance edge, joined on bbl ------------
    print("\nT3.7 -- a REAL cross-agency instance edge: 311 tree complaints -> DPR trees")
    # `order` is pinned: without it SODA returns an arbitrary 25 and the counts
    # below moved between two runs (73 edges / max 29, then 62 / max 16). A
    # design test whose numbers change per run is not reproducible.
    complaints = soda(
        B, select="unique_key,complaint_type,bbl,borough,created_date",
        where="complaint_type like '%Tree%' AND bbl IS NOT NULL",
        order="unique_key", limit="25",
    )
    bbls = sorted({c["bbl"] for c in complaints if c.get("bbl")})
    quoted = ",".join(f"'{b}'" for b in bbls)
    trees = soda(A, select="tree_id,bbl,boroname,spc_common,status",
                 where=f"bbl in ({quoted})", limit="400")
    print(f"    {len(complaints)} complaints over {len(bbls)} distinct BBLs; "
          f"{len(trees)} census trees on those BBLs")
    trees_by_bbl: dict[str, list[dict]] = {}
    for t in trees:
        trees_by_bbl.setdefault(t["bbl"], []).append(t)

    same_lot = Family(
        name="same_tax_lot", namespace="nyc", level="instance",
        definition=("The two records share a borough-block-lot (BBL). It does NOT "
                    "assert that the request is about that tree."),
        symmetric=True, inverse_label=None,
        endpoint_kinds={"src": ("entity",), "dst": ("entity",)},
    )
    ereg3 = EdgeRegistry(
        families=[same_lot], store=EdgeStore(),
        registered_types=[BOROUGH_A, BOROUGH_B, BOROUGH_C, TREE, REQUEST],
    )
    written = 0
    fanouts = []
    for c in complaints:
        ts = trees_by_bbl.get(c.get("bbl", ""), [])
        fanouts.append(len(ts))
        for t in ts:
            r = ereg3.add_edge(
                "same_tax_lot",
                InstanceRef(REQUEST, c["unique_key"]),
                InstanceRef(TREE, t["tree_id"]),
                prov("import:socrata_bbl_join", "user",
                     confidence=1.0 / len(ts),
                     source_version=f"{B}@{DATA_UPDATED[B]} / {A}@{DATA_UPDATED[A]}",
                     evidence=({"kind": "data",
                                "summary": f"BBL {c['bbl']} matches exactly; "
                                           f"{len(ts)} census trees share this lot",
                                "locator": f"{A}.bbl == {B}.bbl"},)),
                namespace="nyc",
            )
            written += r is not None and not getattr(r, "refused", False)
    ok &= check("cross-agency instance edges written", written > 0, True,
                f"({written} edges)")
    matched = sum(1 for f in fanouts if f)
    print(f"    {matched} of {len(complaints)} complaints matched a census tree; "
          f"max trees per lot = {max(fanouts)}")
    ok &= check("the key join is MANY-to-many, so it is not `concerns`",
                max(fanouts) > 1, True,
                "-- confidence is 1/n, and the family is named for what the key proves")

    # ---- T3.8 created_by has no value for a deterministic ingest join -----
    print("\nT3.8 -- what `created_by` says about a deterministic BBL join")
    sample = next(iter(ereg3.store._edges.values()))
    print(f"    created_by={sample.provenance.created_by!r}  "
          f"created_by_actor={sample.provenance.created_by_actor!r}")
    ok &= check("created_by is one of the three INTERFACE values",
                sample.provenance.created_by in ("seed", "ai", "user"), True)
    ok &= check("...and none of them means `derived by rule at ingest`",
                sample.provenance.created_by, "user",
                "-- CONTORTION: the distinction survives only in created_by_actor")

    # ---- T3.10 source_version makes the stale endpoint visible ------------
    print("\nT3.10 -- source_version on a nine-year-stale cross-agency claim")
    print(f"    {sample.provenance.source_version}")
    ok &= check("both endpoints' source versions are on the row",
                DATA_UPDATED[A] in (sample.provenance.source_version or "")
                and DATA_UPDATED[B] in (sample.provenance.source_version or ""), True)

    # ---- the depth cap ----------------------------------------------------
    print("\nEDGES 4.2 -- the depth cap")
    try:
        ereg.neighbors(BOROUGH_A, ["equivalent_to"], 3, namespace="default")
        ok &= check("depth=3 raises", False, True)
    except ValueError as exc:
        ok &= check("depth=3 raises ValueError", True, True, f"-- {exc}")

    print("\nEDGES 4.3 -- a typo'd family refuses the whole call")
    ref = ereg.neighbors(BOROUGH_A, ["equivalant_to"], 1, namespace="default")
    ok &= check("reason", getattr(ref, "reason", None), "edge_family_unknown")

    print("\nEDGES 4.3 / 6 -- no edge store at all")
    ereg4 = EdgeRegistry(families=[equivalent_to], store=None)
    ref2 = ereg4.neighbors(BOROUGH_A, ["equivalent_to"], 1, namespace="default")
    ok &= check("reason", getattr(ref2, "reason", None), "edge_store_absent",
                "-- never an empty report")

    print("\n" + ("ALL CHECKS PASSED" if ok else "SOME CHECKS FAILED"))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
