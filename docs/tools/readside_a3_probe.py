"""Row 6f's **A3 end-to-end probe** -- 6F-RUN.md section 0.6, against `ontoloche.Registry`.

**The deliverable this file exists for**, in the brief's own words: *a probe reproducing
A3's shape end to end and showing that after the change the machine actor no longer
receives a clean 1.0 on that verb.*

**Section 0.6 fixed the pass condition BEFORE this file existed**, so it cannot be
relaxed to fit what the probe returns:

    A CLEAN 1.0 is `outcome == "existing"` with `confidence == 1.0` and NO refusal.
    Satisfying the deliverable requires a REFUSAL or a `confidence != 1.0`.
    A WARNING ALONE DOES NOT SATISFY IT -- `identity_stale` shipped 2026-08-30 and A3
    was filed after it.

**What this file establishes first, and it changed the row's scope.** Row 6d's commit
`304967a` (2026-09-05, *"A3 CLOSED"*) added `_action_declarations_diverge` at all three
collapse doors, and it is an ancestor of HEAD. So A3's shape as the governance register
tabulates it -- two families that BOTH declare, and contradict -- is now refused
**non-overridably** at `retire(successor=)` and at `merge_types`, and the alias is
refused `alias_collision` at `import_types`.

That is not the end of A3, because the fix has a deliberate hole in it and says so:

    if not mine or not theirs:
        return None
    # A family that has not DECLARED is not a family that declared differently.

So a family that declares **nothing** is not "diverging" from one that declares
human-approval-only and irreversible, and the collapse walks. **Whether that reaches A3's
harm is the question this probe answers by running it**, rather than by reading the
comment and inferring. Both walks are run and both answers are printed, because a probe
that only runs the walk it expects to succeed is not evidence.

**It changes nothing.** Reads, builds `:memory:` stores, prints.
Run: ``py docs/tools/readside_a3_probe.py``
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))

from ontoloche import Registry  # noqa: E402
from ontoloche.actions import (  # noqa: E402
    Effect,
    InputSpec,
    Precondition,
    action_attributes,
)
from ontoloche.backends.sqlite import SQLiteAdapter  # noqa: E402
from ontoloche.types import Evidence, Refusal, TypeEntry  # noqa: E402

EVIDENCE = [Evidence(kind="data", summary="row 6f A3 fixture")]


def record(label: str, value: str, note: str = "") -> None:
    print(f"  {label:<50} {value}" + (f"   -- {note}" if note else ""))


def fresh() -> Registry:
    return Registry(SQLiteAdapter(":memory:"))


def seed(reg, name, *, kind="entity", attributes=None):
    out = reg.propose_type(
        name,
        f"{name}, seeded by row 6f's A3 probe",
        EVIDENCE,
        "user:sd",
        kind=kind,
        attributes=attributes,
    )
    if isinstance(out, (TypeEntry, Refusal)):
        return out
    return reg.approve(out.id, "user:sd")


GOVERNED = dict(
    approval_mode="human",
    min_auto_tier=None,
    reversibility="irreversible",
    effects=(Effect(op="propose_type", namespace="default", kind="entity"),),
)


PERMISSIVE = dict(
    approval_mode="auto",
    min_auto_tier="haiku",
    reversibility="reversible",
    effects=(Effect(op="propose_type", namespace="default", kind="entity"),),
)


def walk(label, *, shape: str):
    """A3 end to end: collapse `old_verb` into `new_verb`, then read the dead word.

    ``shape`` selects which of three constructions is walked:

    ``"declared"``  the register's tabulated shape -- both families declare and the four
                    governance keys contradict.
    ``"bare"``      the hole `304967a` left on purpose -- the absorbed family declares
                    nothing, so it is not "declaring differently".
    ``"uncompared"`` both families declare, and the four keys row 6d compared AGREE --
                    they differ on ``preconditions``. **The name is now HISTORICAL:**
                    founder ruling **R102** (`Q99`, "all eight", row 6g) put all eight
                    declared keys into the comparator, so this walk is no longer an
                    UNCOMPARED key and the write door now REFUSES it. Row 6d's
                    own finding A10 already observed that narrowing the tuple to two keys
                    survives the suite; this asks the complementary question -- what does
                    the tuple not reach at all?
    """
    print(f"\n--- {label} ---")
    reg = fresh()
    if shape == "declared":
        seed(reg, "old_verb", kind="action", attributes=action_attributes(**PERMISSIVE))
        seed(reg, "new_verb", kind="action", attributes=action_attributes(**GOVERNED))
    elif shape == "bare":
        # `ACTIONS.md` 2.2-1 permits an entry with no declaration, and the governance
        # probe's K7 already pins that such an entry registers.
        seed(reg, "old_verb", kind="action", attributes={})
        seed(reg, "new_verb", kind="action", attributes=action_attributes(**GOVERNED))
    elif shape == "uncompared":
        seed(reg, "old_verb", kind="action", attributes=action_attributes(**PERMISSIVE))
        seed(reg, "never_holds", kind="predicate")
        seed(reg, "guarded_thing", kind="entity")
        got = seed(
            reg,
            "new_verb",
            kind="action",
            attributes=action_attributes(
                inputs=(InputSpec(name="target", ref="instance", kinds=("entity",)),),
                preconditions=(
                    Precondition(
                        kind="predicate_holds",
                        subject="target",
                        predicate="never_holds",
                        why=(
                            "the surviving family protects this action behind a "
                            "predicate the absorbed family never required"
                        ),
                    ),
                ),
                **PERMISSIVE,
            ),
        )
        if isinstance(got, Refusal):
            record("survivor declaration", f"REFUSED {got.reason}", str(got.detail)[:110])
            return
    else:  # pragma: no cover -- the set is closed and this says so
        raise AssertionError(shape)

    out = reg.retire("old_verb", "superseded", retired_by="user:sd", successor="new_verb")
    if isinstance(out, Refusal):
        record(
            "collapse via retire(successor=)",
            f"REFUSED {out.reason}",
            f"overridable={(out.detail or {}).get('overridable')}",
        )
        return
    record("collapse via retire(successor=)", "RETIRED -- no refusal, no force, no ack")

    r = reg.resolve_type("old_verb", None, tier="haiku")
    warns = list(getattr(r.type, "warnings", ()) or ()) if r.type else []
    clean = r.outcome == "existing" and r.confidence == 1.0
    record(
        "resolve_type('old_verb')",
        f"outcome={r.outcome} type={getattr(r.type, 'name', None)!r} "
        f"confidence={r.confidence!r} warnings={warns}",
    )
    record(
        "  section 0.6: is this a CLEAN 1.0?",
        "YES -- the deliverable is NOT met" if clean else "NO -- the deliverable IS met",
        "a warning alone does not satisfy it",
    )

    for word in ("old_verb", "new_verb"):
        pf = reg.preflight(word, {}, actor="ai:haiku")
        record(
            f"preflight({word!r}) as a Haiku machine actor",
            f"verdict={getattr(pf, 'verdict', None)!r} reason={getattr(pf, 'reason', None)!r}",
        )

    inv = reg.record_invocation(
        "old_verb", {}, actor="ai:haiku", outcome="applied", approved_by="auto:action_policy"
    )
    record(
        "record_invocation('old_verb', outcome='applied')",
        f"{type(inv).__name__} outcome={getattr(inv, 'outcome', None)!r} "
        f"warnings={list(getattr(inv, 'warnings', ()) or ())}",
    )
    led = reg.invocations(family="new_verb", limit=100)
    rows = getattr(led, "invocations", None)
    rows = rows if rows is not None else getattr(led, "rows", ())
    record(
        "invocations(family='new_verb') -- the SURVIVOR's ledger",
        f"n={len(rows)}",
        "A3's own sentence: the record is filed under the DEAD word",
    )


def main() -> int:
    print("Row 6f A3 end-to-end probe -- [Observed] against ontoloche.Registry, SQLite leg")
    walk(
        "WALK 1 -- the register's tabulated shape: BOTH declare, four keys CONTRADICT",
        shape="declared",
    )
    walk(
        "WALK 2 -- the hole 304967a left on purpose: the absorbed family declares NOTHING",
        shape="bare",
    )
    walk(
        "WALK 3 -- both declare, row 6d's four AGREE, they differ on preconditions "
        "(UNCOMPARED until R102; the write door now REFUSES this collapse)",
        shape="uncompared",
    )
    print("\n(Both walks are printed. A probe that runs only the walk it expects to")
    print(" succeed is not evidence.)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
