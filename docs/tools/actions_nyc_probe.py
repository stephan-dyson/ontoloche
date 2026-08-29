"""UC3 design test for ACTIONS.md v0 -- `reconcile_borough`, whose effect is an
edge and never a merge.

Two engines on purpose, exactly as ``edges_nyc_probe.py`` uses them: the
**shipped** ``open_ontology.Registry`` on SQLite for everything about types (so
T3.5's claim about ``merge_types`` is a claim about the real implementation),
and the throwaway probe kits for edges and actions.

Offline by construction: the three dataset ids, their agencies, their
``data_updated_at`` values and the three ``borough`` value sets are the ones
row #4 pinned live on 2026-08-29 (``EDGES.md`` 11.3). A design test whose
numbers move between runs is not a design test.

Run: ``py docs/tools/actions_nyc_probe.py``
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from actions_probe_kit import (  # noqa: E402
    ActionFamily,
    ActionRegistry,
    DeclarationRefused,
    Effect,
    InputSpec,
    Precondition,
)
from edges_probe_kit import (  # noqa: E402
    EdgeCapabilities,
    EdgeRegistry,
    EdgeStore,
    Family,
    TypeRef,
    prov,
)

# EDGES 11: pinned, so the walk-through reproduces.
DATASETS = {
    "dpr": ("uvpi-gqnh", "2017-10-04"),
    "oti_311": ("erm2-nwe9", "2026-08-28"),
    "dot": ("693u-uax6", "2026-08-24"),
}

CHECKS: list[tuple[str, bool, str]] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    CHECKS.append((label, ok, detail))
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}" + (f" -- {detail}" if detail else ""))


def main() -> int:
    print("UC3 -- NYC Open Data, three agencies, one word. ACTIONS.md 13\n")

    boroughs = {ns: TypeRef(ns, "value_set", "borough") for ns in DATASETS}
    edges = EdgeRegistry(
        families=[Family(name="equivalent_to", level="type", symmetric=True,
                         endpoint_kinds={"src": ("entity", "value_set", "edge"),
                                         "dst": ("entity", "value_set", "edge")}),
                  Family(name="reconciled_with", level="type", symmetric=True,
                         endpoint_kinds={"src": ("entity", "value_set", "edge"),
                                         "dst": ("entity", "value_set", "edge")})],
        store=EdgeStore(EdgeCapabilities()),
        registered_types=list(boroughs.values()),
    )
    # EDGES T3.2: the realistic write order is a CHAIN, not a triangle.
    edges.add_edge("equivalent_to", boroughs["dpr"], boroughs["oti_311"], prov("user:dpr"))
    edges.add_edge("equivalent_to", boroughs["oti_311"], boroughs["dot"], prov("user:dot"))

    reg = ActionRegistry(
        edges=edges,
        edge_families={"equivalent_to", "reconciled_with"},
        registered_types=list(boroughs.values()),
        tier_order=("haiku", "sonnet", "opus"),
    )

    print("13.1 T3.1/T3.2 -- the family:")
    fam = ActionFamily(
        name="reconcile_borough",
        definition="Record that two agencies' `borough` value sets have been "
                   "reconciled. Writes an edge; never merges.",
        reversibility="reversible",
        approval_mode="review",
        reachability=("catalogue_console",),
        inputs=(
            InputSpec("a", "type", kinds=("value_set",)),
            InputSpec("b", "type", kinds=("value_set",)),
        ),
        preconditions=(
            Precondition(
                kind="edge_exists", subject="a", object="b", family="equivalent_to",
                why="reconciliation records work on an equivalence somebody already "
                    "asserted; it does not assert one",
            ),
        ),
        effects=(Effect(op="add_edge", family="reconciled_with"),),
    )
    reg.declare(fam)
    check("T3.1   two value_set TypeRef inputs are legal", len(reg.families) == 1)
    try:
        InputSpec("p", "type", kinds=("predicate",))
        check("T3.1b  a predicate input is refused", False, "accepted")
    except ValueError as exc:
        check("T3.1b  a predicate input is refused", "kill row" in str(exc) or
              "predicate" in str(exc), str(exc).split("--")[-1].strip())

    pf = reg.preflight("reconcile_borough",
                       {"a": boroughs["dpr"], "b": boroughs["oti_311"]},
                       actor="derived:catalogue_rule")
    check("T3.2   the precondition is answered by `neighbors` and nothing else",
          pf.preconditions[0].evaluated_by == "neighbors",
          pf.preconditions[0].evaluated_by)
    check("T3.2b  the adjacent pair is allowed", pf.verdict == "allowed", pf.verdict)

    # T3.3 -- the sharpest test.
    print("\n13.1 T3.3 -- an action cannot manufacture transitivity:")
    two_hop = reg.preflight("reconcile_borough",
                            {"a": boroughs["dpr"], "b": boroughs["dot"]},
                            actor="derived:catalogue_rule")
    check("T3.3   dpr <-> dot is REFUSED precondition_unmet",
          two_hop.verdict == "refused"
          and two_hop.refusal.reason == "precondition_unmet"
          and two_hop.refusal.detail.get("state") == "false"
          and two_hop.refusal.detail.get("kind") == "edge_exists",
          str(two_hop.refusal.detail))
    reach = edges.neighbors(boroughs["dpr"], ["equivalent_to"], 2, namespace="default")
    check("T3.3b  ...even though dot IS reachable at depth 2",
          str(boroughs["dot"]) in {str(n) for n in reach.nodes},
          f"nodes={[str(n) for n in reach.nodes]}")

    # T3.4 -- the kill row, at the declaration door.
    print("\n13.1 T3.4/T3.5 -- the kill row, twice:")
    try:
        reg.declare(ActionFamily(
            name="merge_borough", reversibility="irreversible", approval_mode="human",
            effects=(Effect(op="merge_types", namespace="dpr", kind="value_set"),)))
        check("T3.4   merge_types as an EFFECT is refused at declaration", False, "accepted")
    except DeclarationRefused as exc:
        check("T3.4   merge_types as an EFFECT is refused at declaration",
              exc.reason == "effect_not_permitted" and exc.detail["door"] == "declaration",
              f"{exc.reason} {exc.detail['why']}")

    # T3.5 -- against the SHIPPED registry, not the probe's model.
    inv = reg.record_invocation(
        "reconcile_borough", {"a": boroughs["dpr"], "b": boroughs["oti_311"]},
        actor="derived:catalogue_rule", created_by="derived", outcome="applied",
        gate_verdict="allowed", approved_by="auto:action_policy",
        observed_effects=(Effect(op="add_edge", family="reconciled_with"),),
        source_version=(f"{DATASETS['dpr'][0]}@{DATASETS['dpr'][1]} / "
                        f"{DATASETS['oti_311'][0]}@{DATASETS['oti_311'][1]}"))
    edges.add_edge("reconciled_with", boroughs["dpr"], boroughs["oti_311"],
                   prov("derived:catalogue_rule", by="derived"))

    from open_ontology import Evidence, NamespacePolicy, Registry  # noqa: E402
    from open_ontology.backends.sqlite import SQLiteAdapter    # noqa: E402

    shipped = Registry(
        SQLiteAdapter.open(":memory:"),
        policies={ns: NamespacePolicy(namespace=ns, approval_policy="auto",
                                      min_auto_approve_tier="sonnet")
                  for ns in ("dpr", "oti_311")},
    )
    for ns in ("dpr", "oti_311"):
        shipped.propose_type(
            "borough", kind="value_set", namespace=ns,
            definition=f"{ns}'s borough value set, as published by that agency: "
                       "the five county-level divisions of New York City.",
            evidence=[Evidence(kind="data",
                               summary="five distinct values, grouped over the full "
                                       "dataset via the SODA API",
                               locator=f"https://data.cityofnewyork.us/resource/"
                                       f"{DATASETS[ns][0]}.json")],
            proposed_by="ai:probe", tier="opus")
    r1 = shipped.merge_types("borough", "borough", reason="they denote the same five",
                             merged_by="user:probe",
                             namespace="dpr", into_namespace="oti_311")
    r2 = shipped.merge_types("borough", "borough", reason="acknowledged",
                             merged_by="user:probe",
                             namespace="dpr", into_namespace="oti_311",
                             acknowledge=["cross_namespace_merge", "definitions_diverge"])
    check("T3.5   the SHIPPED merge_types still refuses cross_namespace_merge",
          getattr(r1, "reason", None) == "cross_namespace_merge",
          f"{type(r1).__name__}: {getattr(r1, 'reason', r1)}")
    check("T3.5b  ...and refuses again under explicit acknowledge",
          getattr(r2, "reason", None) == "cross_namespace_merge",
          f"{type(r2).__name__}: {getattr(r2, 'reason', r2)}")

    # T3.6 / T3.7 / T3.8
    print("\n13.1 T3.6-T3.9 -- provenance and namespaces:")
    check("T3.6   created_by is `derived` (R17), no contortion",
          inv.provenance.created_by == "derived", inv.provenance.created_by)
    check("T3.7   source_version carries both dataset versions, nine years apart",
          inv.provenance.source_version ==
          "uvpi-gqnh@2017-10-04 / erm2-nwe9@2026-08-28", inv.provenance.source_version)
    check("T3.8   the invocation's namespace is the FAMILY's; inputs keep their own",
          inv.namespace == "default"
          and {r.namespace for r in inv.inputs.values()} == {"dpr", "oti_311"},
          f"invocation={inv.namespace} inputs={sorted(r.namespace for r in inv.inputs.values())}")

    # T3.9 -- projection across namespaces.
    reg.declare(ActionFamily(name="publish_dpr_report", namespace="dpr",
                             reversibility="reversible", approval_mode="auto",
                             reachability=("catalogue_console",)))
    reg.declare(ActionFamily(name="close_311_request", namespace="oti_311",
                             reversibility="compensable", approval_mode="review",
                             reachability=("catalogue_console",)))
    proj = reg.projection("catalogue", budget=10, order=("catalogue_console",))
    check("T3.9   one surface, three namespaces, and that is correct",
          proj.counts["catalogue_console"] == 3 and proj.would_evict == (),
          f"counts={proj.counts}")

    # `review` mode: approved by policy, and enumerable until reviewed.
    check("       review mode records approved_by='auto:<policy>' and stays enumerable",
          inv.provenance.approved_by == "auto:action_policy",
          inv.provenance.approved_by)

    print()
    failed = [c for c in CHECKS if not c[1]]
    if failed:
        print(f"{len(failed)} CHECK(S) FAILED")
        return 1
    print(f"ALL {len(CHECKS)} CHECKS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
