"""UC2 design test for ACTIONS.md v0 -- `flag_facility_for_review` over the
400-row CMS sample, and the severity value the precondition cannot see.

Data: ``open_ontology/contract/fixtures/cms_sample_400.csv``, the checked-in
Montana cut of the public CMS health-citations file. Ground truth is
pre-registered in ``docs/findings/0.5-ground-truth-PREREGISTERED.md``.

Run: ``py docs/tools/actions_cms_probe.py``
"""

from __future__ import annotations

import collections
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from actions_probe_kit import (  # noqa: E402
    ActionCapabilities,
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
    InstanceRef,
    TypeRef,
    prov,
)

REPO = Path(__file__).resolve().parent.parent.parent
SAMPLE = REPO / "open_ontology" / "contract" / "fixtures" / "cms_sample_400.csv"
IJ = {"J", "K", "L"}
HARM = {"G", "H", "I", "J", "K", "L"}

CHECKS: list[tuple[str, bool, str]] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    CHECKS.append((label, ok, detail))
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}" + (f" -- {detail}" if detail else ""))


def main() -> int:
    print("UC2 -- CMS, the 400-row Montana sample. ACTIONS.md 12\n")

    rows = list(csv.DictReader(SAMPLE.open(encoding="utf-8-sig")))
    by_ccn: dict[str, set[str]] = collections.defaultdict(set)
    for r in rows:
        by_ccn[r["CMS Certification Number (CCN)"]].add(r["Scope Severity Code"])
    hist = collections.Counter(r["Scope Severity Code"] for r in rows)
    ij = sorted(k for k, v in by_ccn.items() if v & IJ)
    harm = sorted(k for k, v in by_ccn.items() if v & HARM)

    print("12.1 T2.8 -- the fixture's numbers:")
    check("T2.8a  400 citations", len(rows) == 400, str(len(rows)))
    check("T2.8b  10 facilities", len(by_ccn) == 10, str(len(by_ccn)))
    check("T2.8c  severity histogram B2 C5 D235 E82 F41 G31 J4",
          dict(hist) == {"B": 2, "C": 5, "D": 235, "E": 82, "F": 41, "G": 31, "J": 4},
          str(dict(sorted(hist.items()))))
    check("T2.8d  3 of 10 facilities carry an Immediate-Jeopardy citation",
          len(ij) == 3, f"{ij}")
    check("T2.8e  8 of 10 carry actual harm (G+)", len(harm) == 8, f"{len(harm)}")

    # ------------------------------------------------------------------
    # The edge world CMS already has (EDGES 10), plus the flag family.
    edges = EdgeRegistry(
        families=[
            Family(name="cites", level="instance", namespace="cms",
                   inverse_label="cited_by"),
            Family(name="flagged_for_review", level="instance", namespace="cms",
                   inverse_label="review_of"),
        ],
        store=EdgeStore(EdgeCapabilities()),
        registered_types=[
            TypeRef("cms", "entity", "facility"),
            TypeRef("cms", "entity", "citation"),
            TypeRef("cms", "entity", "deficiency_tag"),
            TypeRef("cms", "value_set", "scope_severity_code"),
        ],
    )
    for i, r in enumerate(rows):
        edges.add_edge(
            "cites",
            InstanceRef(TypeRef("cms", "entity", "citation"), str(i)),
            InstanceRef(TypeRef("cms", "entity", "deficiency_tag"),
                        r["Deficiency Tag Number"]),
            prov("import:cms"),
            namespace="cms",
        )

    reg = ActionRegistry(
        edges=edges,
        edge_families={"cites", "flagged_for_review"},
        registered_types=[
            TypeRef("cms", "entity", "facility"),
            TypeRef("cms", "value_set", "scope_severity_code"),
        ],
        tier_order=("haiku", "sonnet", "opus"),   # supplied by the DEPLOYMENT
    )

    print("\n12.1 T2.1/T2.4 -- what the family can and cannot say:")
    flag = ActionFamily(
        name="flag_facility_for_review",
        namespace="cms",
        definition="Flag a facility for state-survey review.",
        reversibility="reversible",
        approval_mode="auto",
        min_auto_tier="sonnet",
        reachability=("survey_console",),
        inputs=(InputSpec("facility", "instance", kinds=("entity",)),),
        preconditions=(
            Precondition(
                kind="type_active",
                subject="cms:value_set:scope_severity_code",
                why="the scale this flag is judged against must still be in the "
                    "vocabulary -- 0.5 found a cheap tier inverting it",
            ),
        ),
        effects=(Effect(op="add_edge", family="flagged_for_review"),),
    )
    reg.declare(flag)
    check("T2.1   the family expresses under 2.2", len(reg.families) == 1)

    # T2.2 -- the severity precondition is NOT expressible.
    # Round 2: this used to assert a construction-time ValueError. The rule now
    # binds at the DOOR, so it carries a reason and a door like every other one.
    try:
        reg.declare(ActionFamily(
            name="flag_by_severity", namespace="cms", reversibility="reversible",
            approval_mode="auto",
            inputs=(InputSpec("facility", "instance", kinds=("entity",)),),
            preconditions=(Precondition(kind="value_in_set", subject="facility",
                                        why="the facility has a citation in the IJ band"),)))
        check("T2.2   a value-level precondition is NOT expressible", False, "it was accepted")
    except DeclarationRefused as exc:
        check("T2.2   a value-level precondition is NOT expressible",
              exc.reason == "attributes_schema_violation"
              and "closed at four" in exc.detail.get("why", ""),
              f"{exc.reason} at door={exc.detail['door']}")

    # T2.3 -- the modelling escape hatch is refused by EDGES 2.4.1, twice.
    try:
        Family(name="has_severity", level="instance", namespace="cms",
               endpoint_kinds={"src": ("entity",), "dst": ("entity", "value_set")})
        declaration_refused = False
    except ValueError:
        declaration_refused = True
    ok_family = Family(name="has_severity", level="instance", namespace="cms")
    e2 = EdgeRegistry(families=[ok_family], store=EdgeStore(EdgeCapabilities()),
                      registered_types=[TypeRef("cms", "value_set", "scope_severity_code")])
    write = e2.add_edge(
        "has_severity",
        InstanceRef(TypeRef("cms", "entity", "citation"), "42"),
        TypeRef("cms", "value_set", "scope_severity_code"),
        prov("import:cms"),
        namespace="cms",
    )
    check("T2.3   severity-as-an-edge is refused at BOTH layers",
          declaration_refused and getattr(write, "refused", False)
          and write.reason == "endpoint_kind_mismatch",
          f"declaration refused={declaration_refused}; write={getattr(write, 'reason', write)}"
          f" {getattr(write, 'detail', {}).get('problem', '')}")

    check("T2.4   what IS expressible is about the VOCABULARY, not the data",
          flag.preconditions[0].kind == "type_active"
          and flag.preconditions[0].subject.endswith("scope_severity_code"))

    # T2.5 / T2.6 -- the tier gate.
    print("\n12.1 T2.5-T2.7 -- min_auto_tier:")
    facility = InstanceRef(TypeRef("cms", "entity", "facility"), ij[0])
    low = reg.preflight("flag_facility_for_review", {"facility": facility},
                        namespace="cms", actor="ai:haiku_classifier", tier="haiku")
    check("T2.5   a haiku invocation is refused tier_below_action_policy",
          low.verdict == "refused" and low.refusal.reason == "tier_below_action_policy"
          and low.refusal.detail == {"state": "false", "tier": "haiku",
                                     "min_auto_tier": "sonnet"},
          str(low.refusal.detail))
    high = reg.preflight("flag_facility_for_review", {"facility": facility},
                         namespace="cms", actor="ai:opus_classifier", tier="opus")
    check("T2.6   an opus invocation is allowed, approved_by auto:<policy>",
          high.verdict == "allowed" and high.approved_by == "auto:action_policy",
          f"{high.verdict} {high.approved_by}")

    # T2.7 -- no deployment tier order.
    reg_no_order = ActionRegistry(
        edges=edges, edge_families={"flagged_for_review"},
        registered_types=[TypeRef("cms", "value_set", "scope_severity_code")],
        tier_order=None,
    )
    reg_no_order.declare(flag)
    blind = reg_no_order.preflight("flag_facility_for_review", {"facility": facility},
                                   namespace="cms", actor="ai:x", tier="opus")
    check("T2.7   with no deployment tier order the floor is UNKNOWN and refused",
          blind.verdict == "refused"
          and blind.refusal.reason == "tier_below_action_policy"
          and blind.refusal.detail.get("state") == "unknown",
          blind.refusal.detail.get("why", ""))

    # Round 1: three more tier states, each UNKNOWN rather than a confident below.
    for label, kw, expect in (
        ("no tier supplied", {"tier": None}, "no tier was supplied"),
        ("a tier outside the order", {"tier": "gemini-flash"}, "not in this deployment"),
    ):
        r = reg.preflight("flag_facility_for_review", {"facility": facility},
                          namespace="cms", actor="ai:x", **kw)
        check(f"R1-A9  {label} is UNKNOWN, not a confident below",
              r.verdict == "refused" and r.refusal.detail.get("state") == "unknown"
              and expect in r.refusal.detail.get("why", ""),
              r.refusal.detail.get("why", ""))

    # Round 1 BLOCKING 2: the ledger must never fabricate an approval.
    unapproved = reg.record_invocation(
        "flag_facility_for_review", {"facility": facility}, namespace="cms",
        actor="ai:reaper", outcome="applied", gate_verdict="not_asked")
    check("R1-B2  an applied invocation with no approver is null + warned, NOT fabricated",
          unapproved.provenance.approved_by is None
          and "approval_unrecorded" in unapproved.warnings,
          f"approved_by={unapproved.provenance.approved_by!r} "
          f"warnings={unapproved.warnings}")

    # T2.9 -- an effect naming an unregistered edge family.
    try:
        reg.declare(ActionFamily(
            name="flag_facility_v2", namespace="cms", reversibility="reversible",
            approval_mode="auto", effects=(Effect(op="add_edge", family="not_registered"),)))
        check("T2.9   an effect on an unregistered edge family is refused", False, "accepted")
    except DeclarationRefused as exc:
        check("T2.9   an effect on an unregistered edge family is refused",
              exc.reason == "edge_family_unknown", f"{exc.reason} {exc.detail}")

    # T2.10 -- two independent gates on one failure.
    print("\n12.1 T2.10 -- 0.5's inversion, caught twice:")
    check("T2.10a the INVOCATION gate is tier_below_action_policy",
          low.refusal.reason == "tier_below_action_policy")
    check("T2.10b the PROPOSAL gate is a different value on a different object",
          "tier_below_auto_approve_policy" != low.refusal.reason,
          "INTERFACE 2.7's gate is about approving a proposed TYPE; "
          "5.2's is about invoking an approved ACTION")

    # The record path: a refused invocation is still recordable, and an
    # undeclared effect is warned rather than discarded.
    inv = reg.record_invocation(
        "flag_facility_for_review", {"facility": facility}, namespace="cms",
        actor="ai:haiku_classifier", tier="haiku", outcome="refused",
        gate_verdict="refused", refusal=low.refusal)
    check("       a refused invocation is recorded with its reason",
          inv.outcome == "refused" and inv.refusal.reason == "tier_below_action_policy")
    over = reg.record_invocation(
        "flag_facility_for_review", {"facility": facility}, namespace="cms",
        actor="user:sd", outcome="applied", gate_verdict="refused",
        approved_by="user:sd",
        observed_effects=(Effect(op="add_edge", family="flagged_for_review"),
                          Effect(op="host_state", why="wrote a note nobody declared")))
    check("       an undeclared effect is a WARNING on a kept record",
          any(w.startswith("effect_undeclared:") for w in over.warnings), str(over.warnings))
    rep = reg.invocations(gate_verdict="refused", outcome="applied")
    check("       every override is enumerable", len(rep.invocations) == 1,
          f"{len(rep.invocations)} override(s)")

    print()
    failed = [c for c in CHECKS if not c[1]]
    if failed:
        print(f"{len(failed)} CHECK(S) FAILED")
        return 1
    print(f"ALL {len(CHECKS)} CHECKS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
