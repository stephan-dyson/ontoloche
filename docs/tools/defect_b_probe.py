"""Row 6g's **defect B probe** -- `6G-RUN.md` §0.3's three questions, answered by running.

**Defect B is the DECLARE-NOTHING hole**, and the brief is explicit that it is *a
deliberate, argued choice -- not an oversight*:

    if not mine or not theirs:
        return None
    # A family that has not DECLARED is not a family that declared differently. Row 6b's
    # `declared_policy.declared` draws the same line, and refusing on an absence is the
    # FIRST trip's operand pointing the wrong way.

Row 6f measured its walk 2: with the absorbed family declaring nothing,
`retire(successor=)` returns RETIRED with no refusal -- **but the terminal
`record_invocation` refuses, for an unrelated schema reason, so the harm does not
complete.** The brief's sentence about that is the one this file exists to test:
**a harm blocked by an accident is not blocked.**

**This file ROUTES an answer. It does not rule one.** R102 §4 leaves *whether absence
equals divergence* undecided, and reversing it would reverse a stated argument from row
6b, which belongs to the supervisor and possibly the founder. **Nothing here changes the
declare-nothing branch.**

Three questions, each answered by an observation rather than by a code-read:

    Q1  What EXACTLY refuses `record_invocation` on walk 2, and does anything pin it?
    Q2  Is that refusal load-bearing by ACCIDENT or by DESIGN?
    Q3  Does *absence is not divergence* survive the case where the SURVIVOR declares
        human-approval-only and the absorbed family declares nothing at all?

**It changes nothing.** Reads, builds ``:memory:`` stores, prints.
Run: ``py docs/tools/defect_b_probe.py``
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))

from ontoloche import Registry  # noqa: E402
from ontoloche.actions import Effect, action_attributes  # noqa: E402
from ontoloche.backends.sqlite import SQLiteAdapter  # noqa: E402
from ontoloche.types import Evidence, Refusal, TypeEntry  # noqa: E402

EVIDENCE = [Evidence(kind="data", summary="row 6g defect B fixture")]

#: The survivor: human approval only, irreversible. §2.2's cross-field rule makes those
#: two go together, and this is the shape A3's own sentence names.
GOVERNED = dict(
    approval_mode="human",
    min_auto_tier=None,
    reversibility="irreversible",
    effects=(Effect(op="propose_type", namespace="default", kind="entity"),),
)


def record(label: str, value: str, note: str = "") -> None:
    print(f"  {label:<52} {value}" + (f"   -- {note}" if note else ""))


def seed(reg, name, *, kind="entity", attributes=None, definition=None):
    out = reg.propose_type(
        name,
        definition or f"{name}, seeded by row 6g's defect B probe",
        EVIDENCE,
        "user:sd",
        kind=kind,
        attributes=attributes,
    )
    if isinstance(out, (TypeEntry, Refusal)):
        return out
    return reg.approve(out.id, "user:sd")


def _reason(out) -> str:
    """**Warnings are printed, and that is not cosmetic.**

    The governance register's stop criterion reads *"...and no door refuses OR WARNS."*
    An `Invocation` printed without its warnings looks like a door that said nothing,
    which is the difference between a finding and a non-finding. The first cut of this
    probe omitted them and I read `outcome='applied'` as silence for a few minutes.
    """
    if isinstance(out, Refusal):
        return f"Refusal {out.reason!r}"
    warns = list(getattr(out, "warnings", ()) or ())
    return (
        f"{type(out).__name__} outcome={getattr(out, 'outcome', None)!r} "
        f"warnings={warns}"
    )


def collapsed_pair() -> Registry:
    """Walk 2's fixture: the absorbed family declares NOTHING, the survivor declares."""
    reg = Registry(SQLiteAdapter(":memory:"))
    seed(reg, "old_verb", kind="action", attributes={}, definition="one and the same verb")
    seed(
        reg, "new_verb", kind="action",
        attributes=action_attributes(**GOVERNED), definition="one and the same verb",
    )
    out = reg.retire("old_verb", "superseded", retired_by="user:sd", successor="new_verb")
    record(
        "collapse via retire(successor=), ordinary calls",
        "REFUSED " + out.reason if isinstance(out, Refusal) else "RETIRED -- no refusal",
    )
    return reg


def q1_what_refuses() -> None:
    print("\n--- Q1: what EXACTLY refuses record_invocation on walk 2 ---")
    reg = collapsed_pair()

    inv = reg.record_invocation(
        "old_verb", {}, actor="ai:haiku", outcome="applied",
        approved_by="auto:action_policy",
    )
    record("record_invocation('old_verb', 'applied') as Haiku", _reason(inv))
    if isinstance(inv, Refusal):
        record("  its detail", str(inv.detail)[:130])

    pf = reg.preflight("old_verb", {}, actor="ai:haiku")
    record(
        "preflight('old_verb') as Haiku",
        f"verdict={getattr(pf, 'verdict', None)!r} reason={getattr(pf, 'reason', None)!r}",
    )
    print(
        "\n  The refusal is `attributes_schema_violation`, and it is rule 2.2-1's:\n"
        "  a `kind=\"action\"` entry declaring NONE of the eight keys is a legal TypeEntry\n"
        "  that `preflight` and `record_invocation` refuse to run. It is about whether the\n"
        "  family DECLARED, not about whether two families' governance agrees."
    )


def q2_accident_or_design() -> None:
    print("\n--- Q2: is that refusal load-bearing by ACCIDENT or by DESIGN ---")
    print(
        "  PINNED: `C19-26` asserts rule 2.2-1, and its own docstring names the threat:\n"
        "    *\"The hole that opens (declare nothing, then invoke anything) is closed at\n"
        "     the other end, in `preflight`.\"*\n"
        "  So the refusal is BY DESIGN as a rule, and it is pinned by a contract id.\n"
        "  **But the threat it was designed against is `declare nothing, then invoke\n"
        "  anything` -- a SINGLE undeclared family. It is not a guard about a COLLAPSE.**\n"
        "  It blocks walk 2 because walk 2's dead word happens to be the undeclared one.\n"
        "  Same fact, two consequences: the absence that makes the write door permit the\n"
        "  collapse is the absence that makes the invocation refuse."
    )

    reg = collapsed_pair()
    r = reg.resolve_type("old_verb", None, tier="haiku")
    record(
        "resolve_type('old_verb') -- what a host is TOLD to call",
        f"outcome={r.outcome} type={getattr(r.type, 'name', None)!r} "
        f"confidence={r.confidence!r}",
    )
    print(
        "  So a host that follows the redirect does NOT call the dead word at all.\n"
        "  Q3 asks what happens when it calls the SURVIVOR instead."
    )


def q3_does_the_argument_survive() -> None:
    print("\n--- Q3: survivor declares human-approval-only, absorbed declares nothing ---")
    reg = collapsed_pair()

    for word in ("old_verb", "new_verb"):
        pf = reg.preflight(word, {}, actor="ai:haiku")
        record(
            f"preflight({word!r}) as a Haiku machine actor",
            f"verdict={getattr(pf, 'verdict', None)!r} reason={getattr(pf, 'reason', None)!r}",
        )

    survivor = reg.record_invocation(
        "new_verb", {}, actor="ai:haiku", outcome="applied",
        approved_by="auto:action_policy",
    )
    record("record_invocation('new_verb', 'applied') as Haiku", _reason(survivor))
    if isinstance(survivor, Refusal):
        record("  its detail", str(survivor.detail)[:130])

    human = reg.record_invocation(
        "new_verb", {}, actor="user:sd", outcome="applied", approved_by="user:sd",
    )
    record("record_invocation('new_verb', 'applied') as a HUMAN", _reason(human))

    print("")
    print("  **The CONTROL, and it is what stops this being read as a finding.** The same")
    print("  two calls are made below against a family with NO COLLAPSE ANYWHERE NEAR IT.")
    control()

    led = reg.invocations(family="new_verb", limit=100)
    rows = getattr(led, "invocations", None)
    rows = rows if rows is not None else getattr(led, "rows", ())
    record("invocations(family='new_verb') -- the survivor's ledger", f"n={len(rows)}")


def control() -> None:
    """A plain human-approval-only family. No retire, no merge, no import, no alias.

    **[Observed]** `preflight` refuses a Haiku actor and `record_invocation` records
    `applied` carrying **`approval_unrecorded`** -- under every `approved_by` value,
    including `None`. So the recording behaviour has nothing to do with a collapse, it
    is the same before and after row 6g, and **the door WARNS**, which is the clause the
    governance register's stop criterion turns on. It is not a second harm and this row
    does not mint one.
    """
    reg = Registry(SQLiteAdapter(":memory:"))
    seed(reg, "solo_verb", kind="action", attributes=action_attributes(**GOVERNED))
    pf = reg.preflight("solo_verb", {}, actor="ai:haiku")
    record("  CONTROL preflight('solo_verb') as Haiku", f"verdict={pf.verdict!r}")
    for approver in ("auto:action_policy", None, "user:sd"):
        inv = reg.record_invocation(
            "solo_verb", {}, actor="ai:haiku", outcome="applied", approved_by=approver,
        )
        record(f"  CONTROL record as Haiku, approved_by={approver!r}", _reason(inv))


def main() -> int:
    print("Row 6g defect B probe -- [Observed] against ontoloche.Registry, SQLite leg")
    print("It ROUTES an answer. It does not rule one, and it changes no branch.")
    q1_what_refuses()
    q2_accident_or_design()
    q3_does_the_argument_survive()
    print(
        "\nEvery call is printed, including the ones that refuse. The declare-nothing\n"
        "branch is UNCHANGED by row 6g: R102 section 4 leaves `whether absence equals\n"
        "divergence` undecided, and reversing row 6b's stated argument is not a worker's."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
