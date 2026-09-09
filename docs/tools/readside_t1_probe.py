"""Row 6f's **T1 reachability probe** -- 6F-RUN.md section 0.3, run against `ontoloche.Registry`.

**What this establishes, and nothing else.** Section 0.2 fixed a partition of what
`resolve_type`'s read-side verification finds at an alias or successor hit -- AGREE,
GROWTH, DIVERGENCE, UNKNOWABLE. Section 0.3's test **T1** says each state is constructed
with **ordinary calls only**, `force` and acknowledgements REMOVED, borrowing the
governance register's standing rule 3 verbatim, and that *a state I cannot reach with
ordinary calls does not get a policy invented for it*.

Section 0.3's test **T2** then asks `merge_types` about the same operand pair **at that
moment** and records whether the door permits, refuses overridably, or refuses
non-overridably -- because row 6f's read-side policy is DERIVED from that answer rather
than from a read-side severity scale nobody ruled.

This probe runs both, plus the three checks the pre-registration named as decisive:

  * **P1** -- does the shipped detection fire on **A3's shape** (two `kind="action"`
    families with contradictory governance declarations)? Section 0.5 predicted NO.
  * **P3** -- do the four consequential doors (`_extent`, `predicates()`,
    `list_types(predicate=)`, `preflight`) report the staleness `resolve_type` detects?
    Section 0.5 predicted NO.
  * **The both-empty cell** -- section 0.2's S0 row claims *"both extents read to
    exhaustion, equal"* yields *"no warning, 1.0"*. `_identity_agreement`'s `bool(left)` term
    says otherwise when both extents are empty. Settled here by measurement, because a
    pre-registered partition that is wrong about shipped behaviour has to be caught and
    recorded as an error rather than quietly widened.

**It changes nothing.** No product code is touched by this file; it reads, it builds
stores in `:memory:`, and it prints. Run: ``py docs/tools/readside_t1_probe.py``
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))

from ontoloche import Registry  # noqa: E402
from ontoloche.actions import Effect, action_attributes  # noqa: E402
from ontoloche.backends.sqlite import SQLiteAdapter  # noqa: E402
from ontoloche.contract.doubles import DegradedAdapter  # noqa: E402
from ontoloche.types import Evidence, Refusal, TypeEntry  # noqa: E402

EVIDENCE = [Evidence(kind="data", summary="row 6f T1 reachability fixture")]

ROWS: list[tuple[str, str, str]] = []


def record(label: str, value: str, note: str = "") -> None:
    ROWS.append((label, value, note))
    print(f"  {label:<54} {value}" + (f"   -- {note}" if note else ""))


def fresh() -> Registry:
    return Registry(SQLiteAdapter(":memory:"))


def seed(reg, name, *, kind="entity", predicates=(), attributes=None, ns="default"):
    out = reg.propose_type(
        name,
        f"{name}, seeded by row 6f's T1 probe",
        EVIDENCE,
        "user:sd",
        kind=kind,
        namespace=ns,
        predicates=list(predicates),
        attributes=attributes,
    )
    if isinstance(out, (TypeEntry, Refusal)):
        return out
    return reg.approve(out.id, "user:sd")


def family(reg, name, **keys):
    return seed(reg, name, kind="action", attributes=action_attributes(**keys))


def door_answer(reg, frm, into) -> str:
    """T2's mirror: what does `merge_types` answer about this pair, asked NOW?

    Ordinary call -- no `force`, no acknowledgements. The string is the classification
    section 0.3's table keys on: `permits`, `refuses/<reason>/overridable`, or
    `refuses/<reason>/NON-overridable`.
    """
    out = reg.merge_types(frm, into, "row 6f T2 mirror", merged_by="user:sd")
    if isinstance(out, Refusal):
        ov = bool((out.detail or {}).get("overridable"))
        return f"refuses/{out.reason}/{'overridable' if ov else 'NON-overridable'}"
    return "permits"


def resolution(reg, word, *, kind=None):
    r = reg.resolve_type(word, None, kind=kind, tier="haiku")
    warns = tuple(getattr(r.type, "warnings", ()) or ()) if r.type else ()
    return r, warns


def fmt(r, warns) -> str:
    return (
        f"outcome={r.outcome} type={getattr(r.type, 'name', None)!r} "
        f"confidence={r.confidence!r} warnings={list(warns)}"
    )


# ---------------------------------------------------------------- the states
#
# **The correction this probe made to its own first cut, recorded rather than edited
# over.** The first fixtures seeded members on ONE side and then retired `pred_a` toward
# `pred_b`. Every one came back `RETIRE REFUSED predicate_merge overridable=False`,
# because refusal #2 requires the two extents to be NON-EMPTY and IDENTICAL *at the
# moment of the join* -- so those fixtures never built a redirect at all and could not
# have shown anything about the read.
#
# That is exactly section 5.3.2's permanence note: the join is legal only while the
# extents AGREE, and the states this row is about are what happens to that legal join
# AFTERWARDS. Every state below joins on an agreeing pair first, then moves the world
# with ordinary calls.


def legal_join(reg):
    """A LEGAL `retire(successor=)`: both extents non-empty and identical at join time.

    `shared` declares both predicates, so refusal #2's `demonstrably_same` holds and the
    door permits. Returns a refusal string if the join did not happen, else ``None``.
    """
    seed(reg, "pred_a", kind="predicate")
    seed(reg, "pred_b", kind="predicate")
    seed(reg, "shared", predicates=["pred_a", "pred_b"])
    out = reg.retire("pred_a", "superseded", retired_by="user:sd", successor="pred_b")
    if isinstance(out, Refusal):
        return f"JOIN REFUSED {out.reason} overridable={(out.detail or {}).get('overridable')}"
    return None


def report(reg, label, note=""):
    r, warns = resolution(reg, "pred_a")
    la, _, _ = reg._written_extent("default", "pred_a", include_retired=True)
    rb, _, _ = reg._written_extent("default", "pred_b", include_retired=True)
    record(label, fmt(r, warns), note)
    record("    written extents (left | right)", f"{sorted(la)} | {sorted(rb)}")
    record("    T2 mirror: merge_types(pred_a -> pred_b)", door_answer(reg, "pred_a", "pred_b"))


def main() -> int:
    print("Row 6f T1/T2 reachability probe -- [Observed] against ontoloche.Registry, SQLite leg")
    print("\nT1 -- the states of section 0.2, ORDINARY CALLS, no force, no acknowledgement\n")

    # S0 AGREE -- the legal join, read straight back. Nothing has moved.
    reg = fresh()
    bad = legal_join(reg)
    if bad:
        record("S0 AGREE", "UNREACHABLE", bad)
    else:
        report(reg, "S0 AGREE (join legal, nothing moved since)")

    # S0' BOTH EXTENTS EMPTY -- can a join even happen between two bare predicates?
    reg = fresh()
    seed(reg, "pred_a", kind="predicate")
    seed(reg, "pred_b", kind="predicate")
    out = reg.retire("pred_a", "superseded", retired_by="user:sd", successor="pred_b")
    if isinstance(out, Refusal):
        record(
            "S0' BOTH EXTENTS EMPTY",
            f"JOIN REFUSED {out.reason}",
            f"overridable={(out.detail or {}).get('overridable')} -- trip 2's rule, at the WRITE door",
        )
    else:
        report(reg, "S0' BOTH EXTENTS EMPTY")

    # S1 GROWTH -- legal join, then an ordinary new type declares the SURVIVOR. This is
    # section 5.3.2's permanence note happening: the SURVIVOR gains a member.
    # **The note's old wording said 'left can never grow' and this probe's own S2 case
    # two blocks below DISPROVES it** -- a type may declare a retired predicate, so the
    # absorbed word's extent can grow too. 5.3.2 is corrected; this comment repeated the
    # false clause in the very file INTERFACE.md cites as reproducing the correction.
    reg = fresh()
    bad = legal_join(reg)
    if bad:
        record("S1 GROWTH", "UNREACHABLE", bad)
    else:
        seed(reg, "grower", predicates=["pred_b"])
        report(reg, "S1 GROWTH (survivor gains a member after a legal join)")

    # S2 DIVERGENCE -- the absorbed word must hold a member the survivor LACKS. After a
    # legal join the left extent is frozen (the word is retired) and the right can only
    # grow, so section 0.4's SECONDARY FALSIFIER turns on whether any ordinary call
    # reaches this. The candidate move is attempted and its answer recorded.
    reg = fresh()
    bad = legal_join(reg)
    if bad:
        record("S2 DIVERGENCE", "UNREACHABLE", bad)
    else:
        out = reg.propose_type(
            "late_declarer",
            "a type declaring the ABSORBED word after the join",
            EVIDENCE,
            "user:sd",
            kind="entity",
            predicates=["pred_a"],
        )
        if isinstance(out, Refusal):
            got = f"REFUSED {out.reason} overridable={(out.detail or {}).get('overridable')}"
        elif isinstance(out, TypeEntry):
            got = "accepted and ACTIVE (auto-approved)"
        else:
            appr = reg.approve(out.id, "user:sd")
            got = (
                f"proposal APPROVE REFUSED {appr.reason}"
                if isinstance(appr, Refusal)
                else "proposal accepted AND APPROVED -- the left extent should now hold it"
            )
        record("S2 move A: declare the ABSORBED word after the join", got)
        report(reg, "S2 DIVERGENCE (after attempting to grow the left)")

    # S3 UNKNOWABLE -- a backend that DECLARES it cannot compute an extent. This is UC1
    # Tenshen's own declared shape and the FIRST trip's backend, and it is the state
    # section 0.5's P2 predicted would be hardest to justify a policy for.
    print()
    reg = fresh()
    record(
        "S3 -- caps.indexes_membership on the ordinary SQLite leg",
        repr(reg.caps.indexes_membership),
        "so S3 is not reachable here; it needs the declared-degraded leg below",
    )

    degraded = Registry(DegradedAdapter(SQLiteAdapter(":memory:"), indexes_membership=False))
    record("S3 -- caps.indexes_membership on the DEGRADED leg", repr(degraded.caps.indexes_membership))
    bad = legal_join(degraded)
    if bad:
        record(
            "S3 UNKNOWABLE -- can the join even happen here?",
            bad,
            "refusal #2 folds `unknowable` into `not demonstrably_same`, so it refuses",
        )
        # The join is refused, so S3 cannot be reached by JOINING on this backend. But a
        # store can be joined on a capable backend and then READ through a degraded one --
        # which is not exotic: it is one deployment reading another's store, and it is the
        # only way this state arises. Constructed by joining first, then degrading.
        base = SQLiteAdapter(":memory:")
        capable = Registry(base)
        bad2 = legal_join(capable)
        if bad2:
            record("S3 via join-then-degrade", "UNREACHABLE", bad2)
        else:
            seed(capable, "grower", predicates=["pred_b"])
            later = Registry(DegradedAdapter(base, indexes_membership=False))
            r, warns = resolution(later, "pred_a")
            record("S3 UNKNOWABLE (joined capable, READ through degraded)", fmt(r, warns))
            record(
                "    T2 mirror on the degraded leg",
                door_answer(later, "pred_a", "pred_b"),
                "P2's question: this arm is what would refuse on PAGING, not on identity",
            )

    # ------------------------------------------------------------------ P1: A3's shape
    print("\nP1 -- A3's shape: two kind='action' families whose governance contradicts\n")

    def a3_pair(reg):
        family(
            reg,
            "old_verb",
            approval_mode="auto",
            min_auto_tier="haiku",
            reversibility="reversible",
            effects=(Effect(op="propose_type", namespace="default", kind="entity"),),
        )
        family(
            reg,
            "new_verb",
            approval_mode="human",
            min_auto_tier=None,
            reversibility="irreversible",
            effects=(Effect(op="propose_type", namespace="default", kind="entity"),),
        )

    for door in ("retire", "merge", "import"):
        reg = fresh()
        a3_pair(reg)
        if door == "retire":
            out = reg.retire(
                "old_verb", "superseded", retired_by="user:sd", successor="new_verb"
            )
            got = (
                f"REFUSED {out.reason} overridable={(out.detail or {}).get('overridable')}"
                if isinstance(out, Refusal)
                else "RETIRED -- no refusal"
            )
        elif door == "merge":
            out = reg.merge_types("old_verb", "new_verb", "collapse", merged_by="user:sd")
            got = (
                f"REFUSED {out.reason} overridable={(out.detail or {}).get('overridable')}"
                if isinstance(out, Refusal)
                else f"MERGED warnings={list(getattr(out, 'warnings', ()) or ())}"
            )
        else:
            out = reg.import_types(
                [
                    {
                        "name": "new_verb",
                        "definition": "the survivor",
                        "kind": "action",
                        "aliases": ["old_verb"],
                    }
                ],
                imported_by="user:sd",
                kind="action",
            )
            got = "; ".join(
                f"{e.name} aliases={list(e.aliases or ())} warnings={list(e.warnings or ())}"
                for e in out
            )
        record(f"A3 collapse via {door}", got)

    # Whatever the doors did, ask the read what it now answers about the dead word.
    reg = fresh()
    a3_pair(reg)
    reg.retire("old_verb", "superseded", retired_by="user:sd", successor="new_verb")
    r, warns = resolution(reg, "old_verb")
    record("A3: resolve_type('old_verb') after the retire attempt", fmt(r, warns))
    record(
        "A3: _identity_agreement(old_verb, new_verb)",
        repr(
            reg._identity_agreement(
                "default",
                reg._require("default", "old_verb"),
                reg._require("default", "new_verb"),
            )
        ),
        "P1 predicted (False, 1.0) BEFORE the change -- the 4d gate needed BOTH sides "
        "kind='predicate'; row 6f's action operand is what moved it",
    )

    # ---------------------------------------------------- P3: the consequential doors
    print("\nP3 -- do the four consequential doors report the staleness resolve_type detects?\n")
    reg = fresh()
    bad = legal_join(reg)
    if bad:
        record("P3 fixture", "UNREACHABLE", bad)
        return 0
    seed(reg, "grower", predicates=["pred_b"])
    r, warns = resolution(reg, "pred_a")
    record("resolve_type('pred_a')", fmt(r, warns))

    names, size, why = reg._extent("default", "pred_b", False, identity=True)
    record("_extent('pred_b', identity=True)", f"members={sorted(names)} size={size} why={why!r}")

    pr = reg.predicates(of="shared")
    record(
        "predicates(of='shared')",
        f"known={getattr(pr, 'known', None)} warnings={list(getattr(pr, 'warnings', ()) or ())}",
    )

    page = reg.list_types(predicate="pred_b")
    record(
        "list_types(predicate='pred_b')",
        f"n={len(page.types)} complete={page.complete} why_incomplete={page.why_incomplete!r}",
    )

    print("\n(Every row above is [Observed] from the shipped registry on the SQLite leg.)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
