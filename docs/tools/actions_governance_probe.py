"""The governance machinery of ACTIONS.md v0, EXECUTED rather than asserted.

The three fixture probes drive UC1, UC2 and UC3. This one drives the machinery
that is not any fixture's: the kill-row doors, the approval gate at both layers,
the declaration doors, the blast-radius comparison, and the ledger reads section 4
rests its whole argument on.

It exists because both adversarial rounds found their sharpest defects in exactly
the corners no fixture walks -- and because ``edges_capability_probe.py`` was added
to row #4's loop for the same reason and then grew in every round after it.

Run: ``py docs/tools/actions_governance_probe.py``
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from actions_probe_kit import (  # noqa: E402
    ActionCapabilities,
    ActionFamily,
    ActionRegistry,
    DeclarationRefused,
    Effect,
    EdgeRef,
    InputSpec,
    Precondition,
)
from edges_probe_kit import InstanceRef, TypeRef  # noqa: E402

CHECKS: list[tuple[str, bool, str]] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    CHECKS.append((label, ok, detail))
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}" + (f" -- {detail}" if detail else ""))


def fresh(**kw) -> ActionRegistry:
    kw.setdefault("edge_families", {"published_by", "person_links"})
    kw.setdefault("tier_order", ("haiku", "sonnet", "opus"))
    return ActionRegistry(**kw)


def declaration_reason(reg: ActionRegistry, fam: ActionFamily, door="propose_type"):
    try:
        reg.declare(fam, door=door)
        return None
    except DeclarationRefused as exc:
        return exc


def main() -> int:
    print("The governance machinery. ACTIONS.md 2.3, 2.5, 3, 4, 5.2, 10\n")

    # ------------------------------------------------------------------
    print("The kill row -- every door, and the two routes the rounds found:")
    reg = fresh()

    # Round 1: predicate INPUTS, at both layers.
    reg.declare(ActionFamily(name="merge_capabilities", reversibility="reversible",
                             approval_mode="auto",
                             inputs=(InputSpec("a", "type"), InputSpec("b", "type")),
                             effects=(Effect(op="host_state", why="collapses two sets"),)))
    preds = {"a": TypeRef("core", "predicate", "commentable"),
             "b": TypeRef("core", "predicate", "searchable")}
    pf = reg.preflight("merge_capabilities", preds, actor="user:sd")
    rec = reg.record_invocation("merge_capabilities", preds, actor="user:sd",
                                outcome="applied", approved_by="user:sd")
    check("K1  predicate inputs refused at preflight (round 1)",
          getattr(pf, "refused", False) and pf.reason == "input_kind_mismatch")
    check("K2  ...and at record_invocation, so there is no way round it",
          getattr(rec, "refused", False) and rec.reason == "input_kind_mismatch")
    check("K3  ...even wrapped in an InstanceRef",
          getattr(reg.preflight("merge_capabilities",
                                {"a": InstanceRef(TypeRef("core", "predicate", "x"), "1"),
                                 "b": preds["b"]}, actor="user:sd"),
                  "reason", None) == "input_kind_mismatch")

    # Round 2: a propose_type effect, by NAMING and by OMITTING the kind.
    for label, kind in (("naming `predicate`", "predicate"),
                        ("OMITTING the kind (round 2's route)", None),
                        ("naming `action` -- a live VERB", "action")):
        exc = declaration_reason(reg, ActionFamily(
            name=f"mint_{kind}", reversibility="reversible", approval_mode="auto",
            effects=(Effect(op="propose_type", namespace="cms", kind=kind),)))
        check(f"K4  a propose_type effect {label} is refused",
              exc is not None and exc.reason == "effect_not_permitted",
              f"{exc.reason if exc else 'ACCEPTED'} allowed={exc.detail.get('allowed') if exc else ''}")

    ok = declaration_reason(reg, ActionFamily(
        name="propose_facility", reversibility="reversible", approval_mode="auto",
        effects=(Effect(op="propose_type", namespace="cms", kind="entity"),)))
    check("K5  ...and an ALLOWLISTed kind still declares -- the rule is not a ban",
          ok is None)

    # Round 2 MAJOR 4: declaring LESS must not bypass the effect door.
    exc = declaration_reason(reg, ActionFamily(
        name="sneak", effects=(Effect(op="merge_types", namespace="cms"),)))
    check("K6  an entry declaring an effect and NOTHING else is still refused",
          exc is not None and exc.reason == "effect_not_permitted",
          f"{exc.reason if exc else 'WRITTEN'}")
    bare = reg.declare(ActionFamily(name="really_bare"))
    check("K7  ...while a GENUINELY empty entry registers (2.2-1) and preflight refuses",
          bare.reversibility is None
          and getattr(reg.preflight("really_bare", {}, actor="user:sd"),
                      "reason", None) == "attributes_schema_violation")

    for door in ("propose_type", "approve", "import_types"):
        exc = declaration_reason(reg, ActionFamily(
            name=f"merger_{door}", reversibility="irreversible", approval_mode="human",
            effects=(Effect(op="merge_types", namespace="cms"),)), door=door)
        expected = ("import_refused:effect_not_permitted" if door == "import_types"
                    else "effect_not_permitted")
        got = exc.detail.get("warning", exc.reason) if exc else "WRITTEN"
        check(f"K8  merge_types as an effect refused at the `{door}` door", got == expected, got)

    # ------------------------------------------------------------------
    print("\nThe approval gate, at both layers (round 2 MAJOR 2):")
    g = fresh()
    g.declare(ActionFamily(name="reap", reversibility="irreversible",
                           approval_mode="human", reachability=("admin",)))
    pf = g.preflight("reap", {}, actor="ai:reaper", approved_by="ai:reaper")
    inv = g.record_invocation("reap", {}, actor="ai:reaper", outcome="applied",
                              approved_by="ai:reaper")
    check("A1  preflight refuses a model as approver on a human-mode family",
          getattr(pf, "verdict", None) == "refused"
          and pf.refusal.reason == "human_approval_required")
    check("A2  record_invocation does NOT quietly write it either",
          inv.provenance.approved_by is None and "approval_unrecorded" in inv.warnings,
          f"approved_by={inv.provenance.approved_by!r} warnings={inv.warnings}")
    for spoof in ("bot:reaper", "svc:cleanup", "AI:bot", "agent:claude", "nobody"):
        r = g.preflight("reap", {}, actor="user:sd", approved_by=spoof)
        if getattr(r, "verdict", None) != "refused":
            check(f"A3  the allowlist refuses {spoof!r}", False, "ALLOWED")
            break
    else:
        check("A3  the allowlist refuses every non-`user` actor round 1 walked through",
              True, "bot: svc: AI: agent: nobody -- all refused")
    human = g.record_invocation("reap", {}, actor="user:sd", outcome="applied",
                                approved_by="user:sd")
    check("A4  ...and a real person is recorded with no warning",
          human.provenance.approved_by == "user:sd" and human.warnings == ())

    # ------------------------------------------------------------------
    print("\nThe blast radius with a data-dependent namespace (round 2, ingestion):")
    i = fresh()
    i.declare(ActionFamily(
        name="ingest_dataset", reversibility="reversible", approval_mode="auto",
        inputs=(InputSpec("dataset", "instance", kinds=("entity",)),),
        # `namespace=None` DECLARES that the namespace comes from the inputs.
        effects=(Effect(op="add_edge", family="published_by", namespace=None),)))
    right = InstanceRef(TypeRef("dpr", "entity", "dataset"), "uvpi-gqnh")
    ok_inv = i.record_invocation(
        "ingest_dataset", {"dataset": right}, actor="derived:ingest", outcome="applied",
        approved_by="auto:action_policy",
        observed_effects=(Effect(op="add_edge", family="published_by", namespace="dpr"),))
    wrong_inv = i.record_invocation(
        "ingest_dataset", {"dataset": right}, actor="derived:ingest", outcome="applied",
        approved_by="auto:action_policy",
        observed_effects=(Effect(op="add_edge", family="published_by",
                                 namespace="city_council"),))
    check("N1  a correct multi-publisher ingest does NOT warn",
          ok_inv.warnings == (), str(ok_inv.warnings))
    check("N2  ...and one writing into a namespace no input carries DOES",
          any(w.startswith("effect_undeclared:") for w in wrong_inv.warnings),
          str(wrong_inv.warnings))

    # ------------------------------------------------------------------
    print("\nSection 4's ledger reads (round 2 BLOCKING 1):")
    L = fresh()
    L.declare(ActionFamily(name="ingest", reversibility="reversible",
                           approval_mode="auto", reachability=("pipeline",)))
    for n in range(400):
        L.record_invocation("ingest", {}, actor="derived:ingest", outcome="applied",
                            approved_by="auto:action_policy",
                            gate_verdict="refused" if n == 200 else "allowed")
    over = L.invocations(gate_verdict="refused", outcome="applied", limit=100)
    check("L1  an override buried at row 200 is found under limit=100",
          len(over.invocations) == 1 and over.invocations[0].gate_verdict == "refused",
          f"{len(over.invocations)} row(s) from a 400-row ledger")
    check("L2  ...and the filtered answer is honestly incomplete",
          over.complete is False and over.known == 1, over.why_incomplete or "")
    check("L3  an UNfiltered census is complete", L.invocations(limit=1000).complete is True)

    # ------------------------------------------------------------------
    print("\nThe policy an auditor reads back (round 2, ingestion MAJOR 6):")
    a = fresh()
    a.declare(ActionFamily(name="flag", reversibility="reversible",
                           approval_mode="auto", min_auto_tier="haiku"))
    march = a.record_invocation("flag", {}, actor="ai:x", tier="haiku",
                                outcome="applied", approved_by="auto:action_policy")
    a.families[("default", "flag")] = ActionFamily(
        name="flag", reversibility="irreversible", approval_mode="human",
        min_auto_tier="opus")
    check("P1  the invocation carries the POLICY it was judged against, not today's",
          march.declared_policy["min_auto_tier"] == "haiku"
          and march.declared_policy["approval_mode"] == "auto"
          and a.families[("default", "flag")].min_auto_tier == "opus",
          f"recorded={march.declared_policy['min_auto_tier']} "
          f"family now={a.families[('default', 'flag')].min_auto_tier}")

    # ------------------------------------------------------------------
    print("\nA host with no surfaces at all (round 2, ingestion MAJOR 4):")
    n = fresh()
    n.declare(ActionFamily(name="ingest_only", reversibility="reversible",
                           approval_mode="auto", reachability=()))
    rep = n.projection("pipeline", budget=10, order=("pipeline",))
    check("S1  a host declaring no surfaces gets an ANSWER, not a typo refusal",
          not getattr(rep, "refused", False) and rep.counts == {"pipeline": 0},
          f"counts={getattr(rep, 'counts', rep)}")
    n.declare(ActionFamily(name="chatty", reversibility="reversible",
                           approval_mode="auto", reachability=("common",)))
    typo = n.projection("pipeline", budget=10, order=("commmon",))
    check("S2  ...while a host that DOES use surfaces still catches a misspelling",
          getattr(typo, "refused", False) and typo.reason == "action_family_unknown")

    # ------------------------------------------------------------------
    print("\nThe degraded store (8):")
    d = ActionRegistry(caps=ActionCapabilities(
        stores_invocations=False,
        why={"stores_invocations": "this backend is a type registry only"}))
    d.declare(ActionFamily(name="x", reversibility="reversible", approval_mode="auto"))
    check("D1  record_invocation and invocations refuse action_store_absent",
          getattr(d.record_invocation("x", {}, actor="user:sd", outcome="applied",
                                      approved_by="user:sd"), "reason", None)
          == "action_store_absent"
          and getattr(d.invocations(), "reason", None) == "action_store_absent")
    check("D2  ...and preflight, which touches no invocation, still answers",
          getattr(d.preflight("x", {}, actor="user:sd"), "verdict", None) == "allowed")
    conflict = ActionCapabilities(action_transaction_scope="savepoint",
                                  transaction_scope="owned",
                                  action_store_shares_connection=True,
                                  why={"action_transaction_scope": "host owns the commit"})
    check("D3  scope_conflict RETURNS the sentence rather than raising",
          isinstance(conflict.scope_conflict(), str)
          and "two transaction scopes" in conflict.scope_conflict())

    print()
    failed = [c for c in CHECKS if not c[1]]
    if failed:
        print(f"{len(failed)} CHECK(S) FAILED")
        return 1
    print(f"ALL {len(CHECKS)} CHECKS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
