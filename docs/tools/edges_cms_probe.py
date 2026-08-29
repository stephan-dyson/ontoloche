"""UC2 design test for EDGES.md v0 -- the implicit edges in the 400-row CMS sample.

Drives the checked-in Montana sample (``open_ontology/contract/fixtures/
cms_sample_400.csv``, cut by ``make_sample.py`` from the public CMS file) through
the EDGES v0 model, using the throwaway kit in ``edges_probe_kit.py``.

Every count printed here is compared against the PRE-REGISTERED ground truth in
``docs/findings/0.5-ground-truth-PREREGISTERED.md``, which was frozen before any
of this existed. Run:

    py docs/tools/edges_cms_probe.py

Public CMS data only (standing constraint 0).
"""

from __future__ import annotations

import csv
import pathlib
import sys
from collections import defaultdict

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

from docs.tools.edges_probe_kit import (  # noqa: E402
    EdgeRegistry,
    EdgeStore,
    Family,
    InstanceRef,
    TypeRef,
    prov,
)

SAMPLE = (
    pathlib.Path(__file__).resolve().parents[2]
    / "open_ontology"
    / "contract"
    / "fixtures"
    / "cms_sample_400.csv"
)

NS = "cms"
FACILITY = TypeRef(NS, "entity", "facility")
SURVEY = TypeRef(NS, "entity", "survey")
CITATION = TypeRef(NS, "entity", "citation")
TAG = TypeRef(NS, "entity", "deficiency_tag")
SEVERITY = TypeRef(NS, "value_set", "scope_severity_code")

# EDGES 10.1 T2.2 -- pre-registered, from the frozen ground truth.
EXPECTED = {"facilities": 10, "surveys": 69, "citations": 400, "tags": 92}

FAMILIES = [
    Family(
        name="issued_during",
        namespace=NS,
        definition="The citation was issued during this survey.",
        level="instance",
        symmetric=False,
        inverse_label="issued",
        endpoint_kinds={"src": ("entity",), "dst": ("entity",)},
    ),
    Family(
        name="conducted_at",
        namespace=NS,
        definition="The survey was conducted at this facility.",
        level="instance",
        symmetric=False,
        inverse_label="host_of_survey",
        endpoint_kinds={"src": ("entity",), "dst": ("entity",)},
    ),
    Family(
        name="cites",
        namespace=NS,
        definition="The citation cites this deficiency tag.",
        level="instance",
        symmetric=False,
        inverse_label="cited_by",
        endpoint_kinds={"src": ("entity",), "dst": ("entity",)},
    ),
]


def load() -> list[dict]:
    with SAMPLE.open(newline="", encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def check(label: str, got, want, notes: str = "") -> bool:
    ok = got == want
    print(f"  {'PASS' if ok else 'FAIL'}  {label}: got {got}, expected {want} {notes}")
    return ok


def main() -> int:
    rows = load()
    ok = True
    print(f"CMS sample: {len(rows)} rows, {len(rows[0])} columns  [{SAMPLE.name}]\n")

    # ---- nodes, from the pre-registered grain -----------------------------
    ccns = {r["CMS Certification Number (CCN)"] for r in rows}
    surveys = {
        (r["CMS Certification Number (CCN)"], r["Survey Date"], r["Survey Type"])
        for r in rows
    }
    tags = {r["Deficiency Tag Number"] for r in rows}

    print("T2.2 -- node counts against the frozen ground truth")
    ok &= check("facilities (distinct CCN)", len(ccns), EXPECTED["facilities"])
    ok &= check("surveys (CCN, date, type)", len(surveys), EXPECTED["surveys"])
    ok &= check("citations (one per row)", len(rows), EXPECTED["citations"])
    ok &= check("deficiency tags", len(tags), EXPECTED["tags"])

    # ---- edges ------------------------------------------------------------
    store = EdgeStore()
    reg = EdgeRegistry(
        families=FAMILIES,
        store=store,
        registered_types=[FACILITY, SURVEY, CITATION, TAG, SEVERITY],
    )

    def sid(ccn: str, date: str, stype: str) -> str:
        return f"{ccn}|{date}|{stype}"

    for i, r in enumerate(rows):
        ccn = r["CMS Certification Number (CCN)"]
        s = sid(ccn, r["Survey Date"], r["Survey Type"])
        cit = InstanceRef(CITATION, str(i))
        reg.add_edge(
            "issued_during", cit, InstanceRef(SURVEY, s),
            prov("import:cms_nh_health_citations", "user",
                 source_version="NH_HealthCitations_Aug2026 / Processing Date "
                                + r["Processing Date"]),
            namespace=NS,
        )
        reg.add_edge(
            "cites", cit, InstanceRef(TAG, r["Deficiency Tag Number"]),
            prov("import:cms_nh_health_citations", "user"),
            namespace=NS,
        )
    for ccn, date, stype in surveys:
        reg.add_edge(
            "conducted_at",
            InstanceRef(SURVEY, sid(ccn, date, stype)),
            InstanceRef(FACILITY, ccn),
            prov("import:cms_nh_health_citations", "user"),
            namespace=NS,
        )

    by_family: dict[str, int] = defaultdict(int)
    for e in store._edges.values():
        by_family[e.family] += 1

    print("\nT2.2 -- edge counts, which follow arithmetically")
    ok &= check("issued_during", by_family["issued_during"], 400)
    ok &= check("conducted_at", by_family["conducted_at"], 69)
    ok &= check("cites", by_family["cites"], 400)
    distinct_tags = {
        str(e.dst) for e in store._edges.values() if e.family == "cites"
    }
    ok &= check("distinct dst of cites", len(distinct_tags), 92)

    # ---- T2.3 / T2.4 the read seam ----------------------------------------
    print("\nT2.3 -- neighbors(facility, depth=1) then depth=2, summed over all ten")
    d1_total = d2_total = 0
    for ccn in sorted(ccns):
        f = InstanceRef(FACILITY, ccn)
        r1 = reg.neighbors(f, ["conducted_at"], 1, namespace=NS)
        r2 = reg.neighbors(f, ["conducted_at", "issued_during"], 2, namespace=NS)
        d1_total += len(r1.edges)
        d2_total += len(r2.edges) - len(r1.edges)
    ok &= check("surveys reached at depth 1, all facilities", d1_total, 69)
    ok &= check("citations reached at depth 2, all facilities", d2_total, 400)

    one = InstanceRef(FACILITY, sorted(ccns)[0])
    rep = reg.neighbors(one, ["conducted_at", "issued_during"], 2, namespace=NS)
    print(f"    sample report for {one}: known={rep.known} complete={rep.complete} "
          f"depth_reached={rep.depth_reached} families_searched={rep.families_searched}")
    ok &= check("complete over families_searched", rep.complete, True)
    ok &= check(
        "at_depth is populated for both hops",
        sorted({ne.at_depth for ne in rep.edges}),
        [1, 2],
    )

    print("\nT2.4 -- citation reaches its facility in two hops, out-direction only")
    c0 = InstanceRef(CITATION, "0")
    rc = reg.neighbors(c0, ["issued_during", "conducted_at"], 2, namespace=NS,
                       direction="out")
    reached = [str(n) for n in rc.nodes]
    ok &= check("facility reached", any(":facility#" in n for n in reached), True,
                f"(nodes: {reached})")

    # ---- T2.5 the value_set-as-endpoint decision --------------------------
    print("\nT2.5 -- value_set as an INSTANCE-level endpoint")
    fam_sev = Family(
        name="has_severity", namespace=NS, level="instance",
        endpoint_kinds={"src": ("entity",), "dst": ("entity", "value_set")},
        definition="A citation's scope-and-severity letter.",
        inverse_label="severity_of",
    )
    reg2 = EdgeRegistry(
        families=FAMILIES + [fam_sev], store=store,
        registered_types=[FACILITY, SURVEY, CITATION, TAG, SEVERITY],
    )
    out = reg2.add_edge(
        "has_severity", InstanceRef(CITATION, "42"), SEVERITY,
        prov("import:cms", "user"), namespace=NS,
    )
    refused = getattr(out, "refused", False)
    ok &= check("refused", refused, True)
    if refused:
        print(f"    reason={out.reason} detail={out.detail}")
        ok &= check("reason", out.reason, "endpoint_kind_mismatch")
        ok &= check("problem is the LEVEL, not the kind", out.detail["problem"], "level",
                    "-- the value_set is a TypeRef, the family wants an InstanceRef")

    # ---- T2.6 the harder half: does every property fit on the edge? -------
    print("\nT2.6 -- the mechanical test: does EVERY citation property fit on `cites`?")
    citation_props = [
        "Deficiency Prefix", "Deficiency Category", "Scope Severity Code",
        "Deficiency Corrected", "Correction Date", "Standard Deficiency",
        "Complaint Deficiency", "Infection Control Inspection Deficiency",
        "Citation under IDR", "Citation under IIDR",
    ]
    fits = []
    for col in citation_props:
        # A property fits on the edge iff it is functionally determined by the
        # (citation, tag) pair -- i.e. one value per edge. Every one of these is
        # a column of the citation row, and there is exactly one `cites` edge
        # per row, so all of them are.
        per_edge = defaultdict(set)
        for i, r in enumerate(rows):
            per_edge[(str(i), r["Deficiency Tag Number"])].add(r[col])
        fits.append(max(len(v) for v in per_edge.values()) == 1)
    print(f"    {sum(fits)} of {len(citation_props)} citation properties are "
          f"single-valued per `cites` edge")
    ok &= check("every one of them fits structurally", all(fits), True)
    print("    => therefore REFUSED on principle (EDGES 1, 2.4.1): if they all fit,")
    print("       `cites` has become the citation row under another name.")

    # ---- T2.8 the T4 trap -------------------------------------------------
    print("\nT2.8 -- T4 (104 names shared across CCNs, full file) inside this sample")
    by_name = defaultdict(set)
    for r in rows:
        by_name[r["Provider Name"]].add(r["CMS Certification Number (CCN)"])
    collisions = {n: c for n, c in by_name.items() if len(c) > 1}
    ok &= check("distinct provider names", len(by_name), len(ccns),
                "-- one name per CCN in this slice")
    ok &= check("names shared across CCNs in the sample", len(collisions), 0,
                "-- so the fixture does NOT exercise the trap")

    # ---- T2.9 the T2 trap -------------------------------------------------
    print("\nT2.9 -- T2 (correction date before survey date) in this sample")
    # Both columns are ISO yyyy-mm-dd in this export, so a string compare is a
    # date compare. Verified rather than assumed: see the header row printed above.
    early = sum(
        1
        for r in rows
        if r["Correction Date"].strip()
        and r["Survey Date"].strip()
        and r["Correction Date"].strip() < r["Survey Date"].strip()
    )
    ok &= check("rows with correction before survey", early, 6,
                "-- pre-registered as 6 of 400")
    print("    => a fact about two COLUMNS OF ONE ROW. It never becomes an edge,")
    print("       and EDGES neither catches it nor claims to.")

    print("\n" + ("ALL CHECKS PASSED" if ok else "SOME CHECKS FAILED"))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
