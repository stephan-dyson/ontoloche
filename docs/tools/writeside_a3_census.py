"""Row 6g's **WRITE-DOOR census** -- `6G-RUN.md` sections 0.2, 0.4 and 0.4b.

**What this file is for.** `R102` rules `Q99` **`all eight`**, and its section 4 names three
things it deliberately did not decide. One of them is a **measurement this row owes the
founder**: *how many currently-legal collapses does `all eight` refuse?* Section 0.4 fixed
the method **before** the number was seen, and this file is that method.

**It is also the instrument for the falsifiers**, so it is written before the comparator is
touched and is run unchanged on both sides of the change. A census whose fixture moves
between its BEFORE and its AFTER measures the fixture.

**The six cells, from section 0.2, fixed before anything was measured:**

    W0  both declare, all eight agree                         -> must PERMIT
    W1  both declare, a key in the COMPARED FOUR contradicts  -> refuses since 304967a
    W2  both declare, a key in the UNCOMPARED FOUR contradicts-> A3's live route
    W3  identical AS SETS, differing only in element ORDER    -> must PERMIT
    W4  one family declares NOTHING                           -> defect B, not this row's
    W5  a key PRESENT on one side and ABSENT on the other     -> named before measuring

**Section 0.4a's exclusions, and they matter more than the count.** Only **W2** pairs are
"currently-legal collapses this ruling refuses". **W3 is not a data point -- a W3 pair that
refuses is `C19-100`'s defect in this row's own code**, published as the ruling's cost. W1
is row 6d's work and counting it would credit this row with it. W4 and W5 are not changed
by this row, so a flip there is unintended and BLOCKING rather than a measurement.

**Ordinary calls, per the governance register's standing rule 3:** no ``force``, and no
acknowledgement -- with **one exception that is recorded in the output rather than in a
footnote**. `merge_types` refuses `no_consumer_evidence` for every fixture pair here,
because neither side has a registered consumer (`INTERFACE.md` section 5.10, *"merging two
types about which nothing is known"*). That guard is about **consumers**, not about
governance, so the merge door is measured **twice** -- strictly ordinary, and again
acknowledging that one consumer guard and nothing else -- and both columns are printed.
Acknowledging a consumer guard is not acknowledging a governance guard, and hiding the
distinction would make the merge column unreadable.

**It changes nothing.** Reads, builds ``:memory:`` stores, prints.
Run: ``py docs/tools/writeside_a3_census.py``
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

EVIDENCE = [Evidence(kind="data", summary="row 6g A3 write-door census")]

COMPARED_FOUR = ("approval_mode", "min_auto_tier", "reversibility", "effects")
UNCOMPARED_FOUR = ("inputs", "preconditions", "reachability", "payload_schema")
UNORDERED = ("effects", "inputs", "preconditions", "reachability")


# --------------------------------------------------------------------------- fixtures


def _effects_a():
    return (
        Effect(op="propose_type", namespace="default", kind="entity"),
        Effect(op="host_state", why="writes a row in the host's own ledger"),
    )


def _inputs_a():
    return (
        InputSpec(name="target", ref="instance", kinds=("entity",)),
        InputSpec(name="other", ref="instance", kinds=("entity",)),
    )


def _preconditions_a():
    return (
        Precondition(
            kind="predicate_holds",
            subject="target",
            predicate="never_holds",
            why="the family requires this predicate before it runs",
        ),
        Precondition(
            kind="predicate_holds",
            subject="other",
            predicate="also_never_holds",
            why="and this one too",
        ),
    )


def base_kwargs() -> dict:
    """The BASE declaration. Reversible, so `approval_mode` is free to vary.

    `ACTIONS.md` section 2.2's one cross-field rule is
    ``reversibility="irreversible" => approval_mode MUST be "human"``, refused at
    declaration. A base declaring ``irreversible`` would make the `approval_mode` cell
    unmeasurable, so the base is ``reversible`` and that choice is stated here rather
    than discovered by a reader.
    """
    return dict(
        approval_mode="auto",
        min_auto_tier="haiku",
        reversibility="reversible",
        effects=_effects_a(),
        inputs=_inputs_a(),
        preconditions=_preconditions_a(),
        reachability=("mcp", "cli"),
        payload_schema=None,
    )


#: A genuine CONTRADICTION on each key: the same key, a different declared value.
CONTRADICTIONS = {
    "approval_mode": "human",
    "min_auto_tier": "opus",
    "reversibility": "compensable",
    # **Two dead ends before this one, both recorded rather than tidied away.**
    # `add_edge` refused the DECLARATION with `edge_family_unknown`; `propose_type` with
    # `kind="predicate"` refused `effect_not_permitted`, because PROPOSABLE_KINDS is an
    # ALLOWLIST that excludes predicates by name. A cell that refuses UPSTREAM of the
    # thing under test measures the fixture, not the door. Dropping one of the base's
    # two effects is a genuine set difference the declaration accepts.
    "effects": (Effect(op="host_state", why="writes a row in the host's own ledger"),),
    # Likewise: `kinds=("predicate",)` refused `input_kind_mismatch` at declaration. A
    # THIRD input is a genuine set difference that the declaration accepts.
    "inputs": _inputs_a() + (InputSpec(name="third", ref="instance", kinds=("entity",)),),
    "preconditions": (
        Precondition(
            kind="predicate_holds",
            subject="target",
            predicate="never_holds",
            why="a DIFFERENT precondition set from the base",
        ),
    ),
    "reachability": ("slack",),
    "payload_schema": "some_schema",
}


def variant(key: str, value) -> dict:
    kw = base_kwargs()
    kw[key] = value
    return action_attributes(**kw)


def order_only(key: str) -> dict:
    """The same declaration with ONE list key's elements REVERSED. `C19-100`'s shape."""
    kw = base_kwargs()
    kw[key] = tuple(reversed(tuple(kw[key])))
    return action_attributes(**kw)


def missing(key: str) -> dict:
    """W5 -- the family declares seven of the eight keys and omits one.

    Built by DELETING from the stored form rather than by not passing the argument,
    because `action_attributes` always emits all eight. That is itself a finding about
    W5's reachability and it is reported in the output.
    """
    attrs = action_attributes(**base_kwargs())
    attrs.pop(key, None)
    return attrs


# --------------------------------------------------------------------------- doors


def fresh() -> Registry:
    reg = Registry(SQLiteAdapter(":memory:"))
    for pred in ("never_holds", "also_never_holds"):
        seed(reg, pred, kind="predicate")
    for ent in ("guarded_thing", "other_thing"):
        seed(reg, ent, kind="entity")
    return reg


#: **Both action families share ONE definition string, and that is load-bearing.**
#: `registry.py`'s own comment at the merge door says row 6d's narrowing was *"true of
#: the lens's fixture, where the two definitions differed"* and that with IDENTICAL
#: definitions the same collapse MERGES. The first cut of this census gave the two
#: families different definitions and every non-W1 merge cell came back
#: `definitions_diverge/ov=True` -- **the same fixture mistake, in the instrument built
#: to measure it.** Identical definitions put the declaration operand in front of the
#: door instead of behind a resolver score.
SHARED_DEFINITION = "one governed verb, declared by row 6g's write-door census"


def seed(reg, name, *, kind="entity", attributes=None):
    out = reg.propose_type(
        name,
        SHARED_DEFINITION if kind == "action" else f"{name}, seeded by row 6g's census",
        EVIDENCE,
        "user:sd",
        kind=kind,
        attributes=attributes,
    )
    if isinstance(out, (TypeEntry, Refusal)):
        return out
    return reg.approve(out.id, "user:sd")


def _verdict(out) -> str:
    if isinstance(out, Refusal):
        ov = (out.detail or {}).get("overridable")
        return f"REFUSED {out.reason}" + ("" if ov is None else f"/ov={ov}")
    return "PERMITTED"


def door_retire(left_attrs, right_attrs) -> str:
    reg = fresh()
    a = seed(reg, "old_verb", kind="action", attributes=left_attrs)
    b = seed(reg, "new_verb", kind="action", attributes=right_attrs)
    for who, got in (("old_verb", a), ("new_verb", b)):
        if isinstance(got, Refusal):
            return f"DECL-REFUSED {who}:{got.reason}"
    out = reg.retire("old_verb", "superseded", retired_by="user:sd", successor="new_verb")
    return _verdict(out)


def door_merge(left_attrs, right_attrs, *, ack_consumers: bool) -> str:
    reg = fresh()
    a = seed(reg, "old_verb", kind="action", attributes=left_attrs)
    b = seed(reg, "new_verb", kind="action", attributes=right_attrs)
    for who, got in (("old_verb", a), ("new_verb", b)):
        if isinstance(got, Refusal):
            return f"DECL-REFUSED {who}:{got.reason}"
    out = reg.merge_types(
        "old_verb",
        "new_verb",
        "row 6g census",
        merged_by="user:sd",
        acknowledge=["no_consumer_evidence"] if ack_consumers else [],
    )
    return _verdict(out)


def door_import(left_attrs, right_attrs) -> str:
    """The alias write. Rule 2.2-4: a `Refusal` is not returnable here.

    The pass condition is **the alias is NOT written**, so this reports whether the
    incoming row carries `import_refused:` and whether `old_verb` ended up as an alias.
    """
    reg = fresh()
    got = seed(reg, "old_verb", kind="action", attributes=left_attrs)
    if isinstance(got, Refusal):
        return f"DECL-REFUSED old_verb:{got.reason}"
    rows = [
        {
            "name": "new_verb",
            "kind": "action",
            "definition": SHARED_DEFINITION,
            "status": "active",
            "aliases": ["old_verb"],
            "attributes": right_attrs,
        }
    ]
    out = reg.import_types(rows, namespace="default", kind="action")
    entry = out[0] if out else None
    warns = list(getattr(entry, "warnings", ()) or ())
    aliases = list(getattr(entry, "aliases", ()) or ())
    written = "old_verb" in aliases
    refused = [w for w in warns if w.startswith("import_refused:")]
    if written:
        return "PERMITTED (alias WRITTEN)"
    return "ALIAS NOT WRITTEN" + (f" {refused}" if refused else f" warnings={warns}")


# --------------------------------------------------------------------------- census


def row(label: str, left, right) -> None:
    r = door_retire(left, right)
    m_ord = door_merge(left, right, ack_consumers=False)
    m_ack = door_merge(left, right, ack_consumers=True)
    i = door_import(left, right)
    print(f"  {label:<34} | {r:<36} | {m_ord:<30} | {m_ack:<36} | {i}")


def header(title: str) -> None:
    print(f"\n### {title}")
    print(
        f"  {'cell':<34} | {'retire(successor=)':<36} | "
        f"{'merge (strictly ordinary)':<30} | {'merge (ack no_consumer_evidence)':<36} | "
        f"import_types (alias)"
    )
    print("  " + "-" * 170)


def main() -> int:
    print("Row 6g WRITE-DOOR census -- [Observed] against ontoloche.Registry, SQLite leg")
    print("Ordinary calls: no force, no acknowledgement except the merge column that says so.")

    base = action_attributes(**base_kwargs())

    header("W0 -- both declare, all eight AGREE. Must PERMIT, before and after.")
    row("W0 identical", base, base)

    header("W1 -- CONTRADICTION in the COMPARED FOUR. Refuses since 304967a; not this row's.")
    for key in COMPARED_FOUR:
        row(f"W1 {key}", base, variant(key, CONTRADICTIONS[key]))

    header("W2 -- CONTRADICTION in the UNCOMPARED FOUR. A3's live route; the cell R102 closes.")
    for key in UNCOMPARED_FOUR:
        row(f"W2 {key}", base, variant(key, CONTRADICTIONS[key]))

    header("W3 -- ORDER-ONLY difference on a list key. MUST PERMIT. A refusal here is C19-100.")
    for key in UNORDERED:
        row(f"W3 {key} reversed", base, order_only(key))

    header("W4 -- the absorbed family declares NOTHING. Defect B; unchanged by this row.")
    row("W4 bare", {}, base)

    header("W5 -- a key PRESENT on one side, ABSENT on the other. Named before measuring.")
    for key in COMPARED_FOUR + UNCOMPARED_FOUR:
        row(f"W5 {key} absent", missing(key), base)

    print(
        "\nEvery cell is printed, including the ones that refuse and the ones that were"
        "\nexpected to permit. A census that prints only the rows it hoped for is not"
        "\nevidence. Section 0.4a: only W2 counts toward the number this row owes the"
        "\nfounder; a W3 refusal is this row's OWN defect, not the ruling's cost."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
