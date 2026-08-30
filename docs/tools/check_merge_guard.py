"""Is `ROADMAP.md`'s kill row actually guarded? -- enumerate it and find out.

    *"A capability predicate gets merged as a duplicate -> Stop. This is the failure
    that destroys meaning."*

**This checker exists because that row tripped three times in one day, and a fourth
patch to the same expression was not going to be the fix.**

============  ==========================  =================================================
commit        where                       what
============  ==========================  =================================================
``0e89037``   row 3c, `merge_types`       on ``indexes_membership=False`` every extent came
                                          back empty, so two predicates with genuinely
                                          different members compared **equal** and the
                                          non-overridable refusal never fired
``fcb05b3``   row #6 r2, `merge_types`    ``set() == set()``: two **EMPTY** extents are
                                          byte-identical, so two predicates nothing
                                          satisfies compared equal and merged under two
                                          acknowledgements
``05b8e04``   row #6 r3, `retire`         not `merge_types` at all -- ``retire(successor=)``
                                          redirects ``resolve_type`` at confidence 1.0,
                                          which IS the collapse, and it carried none of the
                                          merge's guards
``4c``        row 4c, `import_types`      **found by this checker's own caller
                                          enumeration** -- an imported ``aliases`` row
                                          naming a RETIRED predicate makes that word
                                          resolve to a live one at confidence 1.0, with no
                                          refusal and no warning
``a3f9e6e``   row 4c r3, FOUR doors       the SIXTH trip, and the first that is
                                          *different in kind*: the guard looked correctly
                                          and then the fact CHANGED. Two individually
                                          legal merges and one new type make
                                          ``resolve_type`` answer at 1.0 over a pair this
                                          registry refuses non-overridably when asked
                                          directly. **Rule U's fourth operand: STALE is
                                          not equal**
============  ==========================  =================================================

The supervisor's diagnosis after the third, which this file is built to hold:

    **a two-valued comparison over a three-valued fact, in a guard written for ONE CALL
    over a fact that MORE THAN ONE CALL can change.**

Row 4c's own trip widens it once more: the fourth caller reaches the collapse through a
different **field** (``aliases`` rather than ``successor``) as well as through a
different call. So this checker has two halves, and neither is sufficient alone:

**Part A -- the CALLERS, discovered from the source rather than remembered.** A
hard-coded list of callers is a list somebody has to remember to update, which is the
shape of the defect rather than a fix for it. This walks ``registry.py``'s AST for every
function that writes a ``successor`` or an ``aliases`` value onto a stored record -- the
two fields that re-point what a name resolves to -- and holds what it finds against the
table below. **A caller this file has never heard of fails the check**, whether it is
guarded or not, because the judgement of whether it collapses two identities is a
person's to make and to write down.

**Part B -- the STATES, exercised against the shipped registry on all three legs.** Every
state a predicate extent pair can be in, for every collapsing caller:

======================  ===========================================  ==================
state                   how it arises                                required answer
======================  ===========================================  ==================
**known-different**     two non-empty extents that differ            REFUSED
**known-equal**         two non-empty extents that are identical     **allowed**
**empty**               both extents empty, membership indexed       REFUSED
**unknowable**          ``indexes_membership=False``                 REFUSED
**kind mismatch**       the two sides are different ``kind``s        REFUSED
**partial**             an honest page whose FIRST page matches      REFUSED
**truncated**           a capped answer with no cursor to the rest   REFUSED
**stale**               they AGREED when the identity was written,   REFUSED, and the
                        and the vocabulary then grew                 READ says so
======================  ===========================================  ==================

**Part B has a second axis, and the sixth trip is why.** Every state above is a state
two extents are in *at the moment one guard looks*. The **stale** axis is a state the
STORE is in: an identity written when two extents agreed, over a vocabulary that then
grew. It cannot be posed by seeding two predicates and calling one function -- it needs
two individually legal merges and one ordinary new type -- so it has its own fixture and
its own probes, and it asks ``resolve_type`` as well as the three collapsing callers,
because **the read is where a stale claim is cashed**. See ``check_staleness`` below.

The **known-equal** row is not filler and it is the one a careless fix breaks: the guard
is *narrowed*, not *banned*. A registry that refused every predicate collapse would pass
a checker that only tested refusals, and would have deleted a legal operation to make a
test go green.

Every refusal is additionally checked to be **non-overridable** -- under every
acknowledgement the call accepts, and under ``force=True`` where the call has one.
``force`` overrides what could be SEEN, never what would become TRUE.

Usage: ``py docs/tools/check_merge_guard.py`` from anywhere. Exits non-zero and prints
every failure. Set ``OO_POSTGRES_DSN`` to include the Postgres leg; it is reported as
NOT RUN rather than silently skipped, because a leg that disappears from a run is a leg
nobody notices is missing.
"""

from __future__ import annotations

import ast
import os
import sys
import tempfile
import uuid
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from open_ontology import Registry  # noqa: E402
from open_ontology.backends.sqlite import SQLiteAdapter  # noqa: E402
from open_ontology.backends.sqlite_minimal import MinimalSQLiteAdapter  # noqa: E402
from open_ontology.contract.doubles import DegradedAdapter  # noqa: E402
from open_ontology.policy import NamespacePolicy  # noqa: E402
from open_ontology.types import (  # noqa: E402
    Evidence,
    Refusal,
    ResolveContext,
    TypeEntry,
)

REGISTRY_SOURCE = ROOT / "open_ontology" / "registry.py"

#: The three fields on a stored `TypeRecord` that re-point what a name RESOLVES to.
#:
#: **`status` was added by row 4c's THIRD adversarial round, and its absence was a
#: BLOCKING finding.** `resolve_type` scores only `status="active"` rows, so flipping a
#: row to active makes every alias it carries a confidence-1.0 answer -- which is
#: literally what `reinstate` and `import_types` do, and the mechanism of two of the
#: sixth trip's four doors. A reviewer wrote a caller that touched no `successor` and no
#: `aliases`, only `status`, and Part A did not flag it.
#: `successor` redirects a retired word at confidence 1.0 (`INTERFACE.md` §5.3 calls that
#: a guarantee); `aliases` makes a word answer with this entry. A third field with the
#: same power would have to be added here -- and adding one without touching this file is
#: exactly the failure Part A exists to catch, because the AST scan below would find the
#: writes and this file would not know what they mean.
IDENTITY_FIELDS = ("successor", "aliases")

#: **`status` is an identity field too, and it gets a NARROWER scan for one reason:
#: the word is everywhere.** `resolve_type` scores only `status="active"` rows, so
#: flipping a row to active makes every alias it carries a confidence-1.0 answer --
#: which is literally what `reinstate` and `import_types` do, and the mechanism of two
#: of the sixth trip's four doors. A reviewer wrote a caller that touched no `successor`
#: and no `aliases`, only `status`, and Part A did not flag it.
#:
#: The over-broad *"any mention of the name"* rule that `IDENTITY_FIELDS` gets is right
#: for two rare words and useless for a ubiquitous one: applied to `status` it flagged
#: eleven functions that only ever COMPARE it. So this one is matched where a record is
#: actually WRITTEN -- a keyword argument or a dict-literal key -- which still catches
#: every shape the reviewer's probe used, including
#: `TypeRecord(**{**rec.__dict__, "status": "active"})`.
#:
#: **A narrower rule is a rule with a gap, and the gap is stated rather than implied:**
#: a `status` written through a computed key escapes this scan. That is the trade a
#: ubiquitous field forces, and it is why `status` is here rather than folded into
#: `IDENTITY_FIELDS`.
STATUS_FIELD = "status"


@dataclass(frozen=True)
class CallerVerdict:
    """What a person decided about one caller, and why."""

    collapses: bool
    why: str


#: Every function in `registry.py` that writes an identity field, with the judgement a
#: person made about it. **Part A fails on any writer that is not in here** -- the point
#: is that a new one cannot arrive unnoticed, not that this list is complete today.
KNOWN_CALLERS: dict[str, CallerVerdict] = {
    "merge_types": CallerVerdict(
        True,
        "retires `from_` with `into` as its successor AND adds `from_`'s name to "
        "`into`'s aliases -- the canonical collapse, and the call §5.10's guards were "
        "written for",
    ),
    "retire": CallerVerdict(
        True,
        "`retire(successor=)` redirects `resolve_type` to the successor at confidence "
        "1.0, which INTERFACE.md §5.3 calls a guarantee -- so it IS the collapse, "
        "reached by a call that carried none of the guards until 05b8e04 (the kill "
        "row's third trip)",
    ),
    "import_types": CallerVerdict(
        True,
        "writes a foreign dump's `aliases` onto a live entry. `alias_collision` refuses "
        "an alias that is a LIVE entry's name -- and a RETIRED predicate name still "
        "resolves and still has an extent, so the collapse walked straight past a guard "
        "written for a collision (the kill row's fourth trip, row 4c, found by Part A)",
    ),
    "reinstate": CallerVerdict(
        True,
        "**this entry said `collapses=False` until row 4c's third adversarial round, "
        "and it was wrong.** It read: *a SPLIT, not a collapse -- it CLEARS a successor "
        "off a live row ... it cannot make two identities into one.* Clearing the "
        "successor is a split; **re-activating the row is not**. Every alias the row "
        "carries becomes a confidence-1.0 answer again, over a world that has moved "
        "since they were written, and `_lifecycle_collisions` scans ACTIVE rows only -- "
        "so an alias naming a retired predicate was invisible to it, which is the FOURTH "
        "trip's blind spot untouched in the sibling guard. It now runs the identity "
        "guards over its dormant aliases. *(A person's judgement, written down and "
        "wrong, is the enumeration working as designed: a wrong judgement on the record "
        "is one a reviewer can find.)*",
    ),
    "_write_approved": CallerVerdict(
        False,
        "writes `aliases=()` -- the literal empty tuple, on every approval. A "
        "`ProposalRecord` has no `successor` and no `aliases` field, so `approve` cannot "
        "re-point a name however the proposal is amended. *(Row 4c looked for `approve` "
        "of a proposal with a successor because the brief named it as a caller; there is "
        "no such thing, and this line is the record that somebody checked.)*",
    ),
    "_seed_equivalent_to": CallerVerdict(
        False,
        "writes ONE row at store creation -- `EDGES.md` §3.1's `equivalent_to` family, "
        "with `status=\"active\"` and no aliases and no successor. It creates an "
        "identity; it cannot fold two into one",
    ),
    "retract_edge": CallerVerdict(
        False,
        "writes `status=\"retracted\"` onto an **EDGE**, not onto a type. An edge has "
        "no `aliases` and no `successor` and `resolve_type` never scores one, so no name "
        "resolves differently because of it. *(Flagged by the `status` scan because that "
        "field is shared between two record shapes -- and left here rather than excluded "
        "by type, because a scan that guesses which record a field belongs to is a scan "
        "with a judgement in it.)*",
    ),
    "resolve_type": CallerVerdict(
        False,
        "**READS** a retired row's `successor` to redirect at confidence 1.0 -- it is "
        "the call whose behaviour makes every other entry in this table matter, and it "
        "writes nothing. Flagged by the over-broad scan (row 4c round 2) because it "
        "names the field; kept here because a person deciding *\"reader, not writer\"* "
        "is exactly the judgement Part A exists to force",
    ),
    "_declared_predicate_moved": CallerVerdict(
        False,
        "**READS** a retired predicate's `successor`, and scans the namespace's active "
        "rows for one holding a word as an ALIAS, to answer ruling **R55**'s question at "
        "the write door: *which identity did this declaration land in?* It returns a "
        "name that becomes a warning string, and it writes no row. **Flagged by the "
        "over-broad scan the minute row 4d added it, which is Part A doing exactly its "
        "job** -- a new function that so much as names an identity field fails this "
        "check until a person writes down what it means, whether it is a writer or not. "
        "*(The false positive costs this paragraph; a false negative costs the kill "
        "row.)*",
    ),
    "_search_namespaces": CallerVerdict(
        False,
        "**READS** `rec.successor` to build the sentence R6's cross-namespace lookup "
        "returns when a word is burned elsewhere. A message about a successor is not a "
        "successor",
    ),
    "_lifecycle_collisions": CallerVerdict(
        False,
        "**READS** `detail[\"successor\"]` and `detail[\"into\"]` out of the EVENT log "
        "to walk the chain both ways for `reinstate`'s guards. It reads history; it "
        "writes no row",
    ),
    "_entry": CallerVerdict(
        False,
        "the READ path -- it copies `aliases` off a stored record into the returned "
        "`TypeEntry`. It writes nothing",
    ),
}


# ---------------------------------------------------------------------------
# Part A -- the callers, discovered from the AST


#: Calls that WRITE a stored record, as opposed to querying one. A `status` keyword
#: inside one of these re-points what a name resolves to; the same keyword on a
#: `TypeQuery` is a filter and re-points nothing.
RECORD_WRITES = ("TypeRecord", "replace", "put_type")


def _inside_record_write(node: ast.AST, parents: dict[int, ast.AST]) -> bool:
    current = parents.get(id(node))
    while current is not None:
        if isinstance(current, ast.Call):
            name = getattr(current.func, "id", None) or getattr(
                current.func, "attr", None
            )
            if name in RECORD_WRITES:
                return True
        if isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return False
        current = parents.get(id(current))
    return False


def _enclosing_function(node: ast.AST, parents: dict[int, ast.AST]) -> str:
    while node is not None:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return node.name
        node = parents.get(id(node))
    return "<module>"


def identity_writers() -> dict[str, set[str]]:
    """``{function name -> the identity fields it writes}``, from the source."""
    tree = ast.parse(REGISTRY_SOURCE.read_text(encoding="utf-8"))
    parents: dict[int, ast.AST] = {}
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            parents[id(child)] = node

    found: dict[str, set[str]] = {}

    # **Deliberately OVER-BROAD, and that is a decision** (row 4c, second adversarial
    # round). The first version enumerated four syntactic shapes -- a keyword argument, a
    # dict literal key, a subscript assignment, a `setattr` -- and a reviewer wrote nine
    # realistic ways to write an identity field and got **five past it**, including
    # `d["aliases"] += (alias,)`, which is one refactor away from the dict-literal shape
    # three real callers already use. The checker then exited 0 with the kill row live,
    # which falsifies its own central promise.
    #
    # Enumerating shapes is the same artefact as the guard it checks: something a person
    # must remember to extend. So the rule is now **any mention of an identity field's
    # NAME as a constant or a keyword, anywhere in a function** -- a false positive costs
    # one documented line in `KNOWN_CALLERS`, and a false negative costs the kill row.
    # `_enclosing_function` attributes it, and `KNOWN_CALLERS` is where a person says
    # what it means.
    for node in ast.walk(tree):
        if isinstance(node, ast.keyword) and node.arg in IDENTITY_FIELDS:
            found.setdefault(_enclosing_function(node, parents), set()).add(node.arg)
        # `status`, narrowly: a keyword argument or a dict-literal key **inside a record
        # CONSTRUCTION**. See STATUS_FIELD for why this one is not over-broad -- and note
        # the second narrowing, which the first attempt needed: `status="active"` is also
        # a `TypeQuery` FILTER, so matching every keyword flagged fourteen functions that
        # only ever read.
        if isinstance(node, ast.keyword) and node.arg == STATUS_FIELD:
            if _inside_record_write(node, parents):
                found.setdefault(
                    _enclosing_function(node, parents), set()
                ).add(STATUS_FIELD)
        if isinstance(node, ast.Dict):
            for key in node.keys:
                if (
                    isinstance(key, ast.Constant)
                    and key.value == STATUS_FIELD
                    and _inside_record_write(node, parents)
                ):
                    found.setdefault(
                        _enclosing_function(node, parents), set()
                    ).add(STATUS_FIELD)
        if (
            isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and node.value in IDENTITY_FIELDS
        ):
            found.setdefault(_enclosing_function(node, parents), set()).add(node.value)
        # `rec.aliases = ...` / `object.__setattr__(rec, "aliases", ...)` reach the branch
        # above through the constant; a plain attribute assignment does not.
        if isinstance(node, (ast.Assign, ast.AugAssign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            stack = list(targets)
            while stack:
                target = stack.pop()
                if isinstance(target, (ast.Tuple, ast.List)):
                    stack.extend(target.elts)
                elif isinstance(target, ast.Starred):
                    stack.append(target.value)
                elif (
                    isinstance(target, ast.Attribute)
                    and target.attr in IDENTITY_FIELDS
                ):
                    found.setdefault(
                        _enclosing_function(node, parents), set()
                    ).add(target.attr)
    return found


def check_callers() -> list[str]:
    problems: list[str] = []
    writers = identity_writers()
    for function, fields in sorted(writers.items()):
        if function not in KNOWN_CALLERS:
            problems.append(
                f"CALLER: `{function}` writes {sorted(fields)} onto a stored record and "
                f"this checker has never heard of it. Every write of {list(IDENTITY_FIELDS)} "
                f"changes what a name RESOLVES to, and the kill row has now been reached "
                f"through three different calls and two different fields. Decide whether "
                f"it can collapse two identities into one, and record the decision in "
                f"KNOWN_CALLERS -- if it can, it needs INTERFACE.md §5.10's identity "
                f"guards #2 and #3, and a row in Part B's matrix"
            )
    for function in sorted(KNOWN_CALLERS):
        if function not in writers:
            problems.append(
                f"CALLER: KNOWN_CALLERS names `{function}` and no function of that name "
                f"writes an identity field any more. A stale entry here is a guard "
                f"somebody thinks is being checked and is not -- remove it, or say where "
                f"the write went"
            )
    return problems


# ---------------------------------------------------------------------------
# Part B -- the states, against the shipped registry

#: A probe that could not build its fixture on this backend returns a string starting
#: with this. It is NOT a pass: the row prints `NOT REACHABLE` and says why. Row 4c's
#: first adversarial round found five rows printing `REFUSED` for a probe that never ran.
_NOT_REACHABLE = "NOT REACHABLE: "

EVIDENCE = [Evidence(kind="data", summary="check_merge_guard fixture")]

#: Every acknowledgement `merge_types` accepts. The refusals below must survive **all**
#: of them at once: guards #2 and #3 are non-overridable, and a guard that can be
#: acknowledged past is a warning wearing a refusal's name.
ALL_ACKNOWLEDGEMENTS = [
    "definitions_diverge",
    "no_consumer_evidence",
    "retired_operand",
    "predicate_merge",
    "kind_mismatch",
]


def _seed(registry: Registry, name: str, *, kind="entity", predicates=(), definition=None):
    out = registry.propose_type(
        name,
        definition or f"a {name}, for the purposes of this check",
        EVIDENCE,
        "user:sd",
        kind=kind,
        predicates=list(predicates),
    )
    if isinstance(out, TypeEntry):
        return out
    if isinstance(out, Refusal):  # pragma: no cover - a fixture that cannot be built
        raise AssertionError(f"could not seed {name}: {out}")
    approved = registry.approve(out.id, "user:sd")
    assert isinstance(approved, TypeEntry), approved
    return approved


def _predicates(registry: Registry, left_members, right_members):
    """`commentable` and `searchable`, with the extents asked for."""
    _seed(registry, "commentable", kind="predicate", definition="a capability")
    _seed(registry, "searchable", kind="predicate", definition="a capability")
    for i, member in enumerate(left_members):
        _seed(registry, member, predicates=["commentable"])
    for member in right_members:
        if member in left_members:
            continue
        _seed(registry, member, predicates=["searchable"])
    # A member in BOTH extents has to be seeded once with both predicates.
    for member in set(left_members) & set(right_members):
        pass


def _both(registry: Registry, left_members, right_members):
    _seed(registry, "commentable", kind="predicate", definition="a capability")
    _seed(registry, "searchable", kind="predicate", definition="a capability")
    seeded: dict[str, list[str]] = {}
    for member in left_members:
        seeded.setdefault(member, []).append("commentable")
    for member in right_members:
        seeded.setdefault(member, []).append("searchable")
    for member, predicates in seeded.items():
        _seed(registry, member, predicates=predicates)


# --- one probe per (caller, state). Each returns None, or a sentence naming the failure.


def _probe_merge(registry: Registry, *, expect_refused: bool, reasons: set[str], kind="predicate") -> str | None:
    result = registry.merge_types(
        "commentable",
        "searchable",
        "the checker's fixture",
        merged_by="user:sd",
        acknowledge=ALL_ACKNOWLEDGEMENTS,
    )
    if expect_refused:
        if not isinstance(result, Refusal):
            return (
                f"merge_types COLLAPSED the pair under every acknowledgement "
                f"({ALL_ACKNOWLEDGEMENTS}) -- the kill row, reached again"
            )
        if result.reason not in reasons:
            return f"merge_types refused {result.reason!r}, expected one of {sorted(reasons)}"
        if result.detail.get("overridable") is not False:
            return (
                f"merge_types' {result.reason!r} does not declare itself "
                f"non-overridable; a guard that can be acknowledged past is a warning "
                f"wearing a refusal's name"
            )
        return None
    if isinstance(result, Refusal):
        return (
            f"merge_types REFUSED {result.reason!r} a pair whose extents are non-empty "
            f"and identical. The guard is narrowed, not banned -- refusing everything "
            f"passes a checker that only tests refusals and deletes a legal operation"
        )
    return None


def _probe_retire(registry: Registry, *, expect_refused: bool, reasons: set[str], kind="predicate") -> str | None:
    for force in (False, True):
        result = registry.retire(
            "commentable",
            "the checker's fixture",
            retired_by="user:sd",
            successor="searchable",
            force=force,
        )
        if expect_refused:
            if not isinstance(result, Refusal):
                return (
                    f"retire(successor=) COLLAPSED the pair with force={force} -- "
                    f"`resolve_type` now answers the old word with the new entry at "
                    f"confidence 1.0, which is the merge `merge_types` refuses"
                )
            if isinstance(result, Refusal) and result.detail.get("overridable") is not False:
                return (
                    f"retire(successor=)'s {result.reason!r} does not declare itself "
                    f"non-overridable -- `force` overrides what could be SEEN, never "
                    f"what would become TRUE"
                )
            if result.reason not in (reasons | {"cannot_record_override"}):
                return (
                    f"retire(successor=, force={force}) refused {result.reason!r}, "
                    f"expected one of {sorted(reasons)}. **A non-overridable identity "
                    f"guard reached through an OVERRIDABLE one is the same class of "
                    f"defect as the kill row's trips** -- the caller is told to force "
                    f"past something, about a collapse that will never be permitted"
                )
        else:
            if isinstance(result, Refusal) and result.reason in reasons:
                return (
                    f"retire(successor=) refused {result.reason!r} a pair whose extents "
                    f"are non-empty and identical -- the guard is narrowed, not banned"
                )
            return None
    return None


def _probe_import(registry: Registry, *, expect_refused: bool, reasons: set[str], kind="predicate") -> str | None:
    # The alias door: `commentable` is retired first, which is an ordinary and permitted
    # governance act, and THEN imported as an alias of `searchable`. That is the walk
    # row 4c reproduced; `alias_collision` cannot see it, because a retired name is not
    # a live entry.
    retired = registry.retire("commentable", "superseded", retired_by="user:sd", force=True)
    if isinstance(retired, Refusal):
        # **`NOT REACHABLE`, not `None`.** Returning `None` here rendered identically to
        # a real pass, so five `sqlite_minimal / import_types / ...` rows printed
        # **REFUSED** for a probe that never ran -- and the footer went on claiming
        # *"every extent state gets the guard's answer on every leg"*. That is ruling
        # R12's own rule (a verdict without its coverage line is not a verdict) broken
        # inside the checker built to enforce that discipline. Row 4c, round 1.
        return _NOT_REACHABLE + (
            f"this backend cannot record the forced retirement the fixture needs: "
            f"{retired.reason}"
        )
    entries = registry.import_types(
        [
            {
                "name": "searchable",
                "kind": kind,
                "definition": "a capability",
                "aliases": ["commentable"],
                "status": "active",
            }
        ],
        namespace="default",
        kind=kind,
    )
    entry = entries[0]
    refused = any(w.startswith("import_refused:") for w in entry.warnings)
    if expect_refused:
        if not refused:
            return (
                "import_types wrote `commentable` as an alias of `searchable` with no "
                "refusal -- `resolve_type('commentable')` now answers `searchable` at "
                "confidence 1.0, which is the merge `merge_types` refuses "
                "non-overridably. The kill row, through the alias door"
            )
        if not any(f"import_refused:{r}" in entry.warnings for r in reasons):
            return (
                f"import_types refused {entry.warnings!r}, expected one of "
                f"{sorted('import_refused:' + r for r in reasons)}"
            )
        if "commentable" in (entry.aliases or ()):
            return "import_types refused and wrote the alias anyway"
        return None
    if refused:
        return (
            "import_types refused an alias between two predicates whose extents are "
            "non-empty and identical -- the guard is narrowed, not banned"
        )
    return None


PROBES = {
    "merge_types": _probe_merge,
    "retire": _probe_retire,
    "import_types": _probe_import,
}

#: ``(label, how to build the fixture, is the collapse refused?, the reason)``
#: ``(label, build the fixture, is the collapse refused?, acceptable reasons, the KIND
#: the pair shares -- which is what `import_types` has to be told, because a foreign row
#: names its own kind)``.
STATES = (
    (
        "known-different",
        lambda r: _both(r, ["note"], ["doc"]),
        True,
        {"predicate_merge"},
        "predicate",
    ),
    (
        "known-equal",
        lambda r: _both(r, ["note"], ["note"]),
        False,
        {"predicate_merge"},
        "predicate",
    ),
    (
        "empty",
        lambda r: _both(r, [], []),
        True,
        {"predicate_merge"},
        "predicate",
    ),
    (
        # **Guard #3 with a predicate on one side, which is the dangerous shape** -- and
        # BOTH #2 and #3 bind, so either refusal is correct. §5.10 lists #2 first and
        # `merge_types` fires it first; what matters is that the collapse is refused
        # non-overridably, not which of two non-overridable guards got there.
        "kind-mismatch (predicate side)",
        lambda r: (
            _seed(r, "commentable", kind="predicate", definition="a capability"),
            _seed(r, "searchable", kind="entity", definition="a capability"),
        ),
        True,
        {"kind_mismatch", "predicate_merge"},
        "entity",
    ),
    (
        # **Guard #3 ISOLATED**, with no predicate anywhere: if #2 stopped firing
        # tomorrow this row would still hold #3, and the row above would go quiet
        # without anybody noticing. Two rows, because one of them can mask the other.
        "kind-mismatch (no predicate)",
        lambda r: (
            _seed(r, "commentable", kind="entity", definition="a word"),
            _seed(r, "searchable", kind="value_set", definition="a word"),
        ),
        True,
        {"kind_mismatch"},
        "value_set",
    ),
)


def _legs():
    """``(name, build a fresh Registry, is membership indexable here?)``, three of them."""

    def sqlite():
        adapter = SQLiteAdapter(":memory:")
        adapter.migrate()
        return Registry(adapter)

    def minimal():
        # A file, not `:memory:`: the HOST creates the schema on its own connection and
        # only then is the store handed over, which is the whole point of
        # `owns_schema=False`. Two connections to `:memory:` are two databases.
        path = str(Path(tempfile.mkdtemp(prefix="oo_merge_guard_")) / "store.sqlite")
        MinimalSQLiteAdapter.create_host_schema(path)
        adapter = MinimalSQLiteAdapter(path)
        adapter.migrate()  # verify-only: it checks, it does not create
        # PACKAGE.md 7.3 B4: no proposal table *forces* `approval_policy="auto"` --
        # there is nowhere to hold a pending proposal.
        return Registry(adapter, policies={"default": NamespacePolicy(approval_policy="auto")})

    legs = [("sqlite", sqlite, True), ("sqlite_minimal", minimal, False)]
    dsn = os.environ.get("OO_POSTGRES_DSN")
    if dsn:
        from open_ontology.backends.postgres import PostgresAdapter

        def postgres():
            adapter = PostgresAdapter(dsn, schema="oo_" + uuid.uuid4().hex[:12])
            adapter.migrate()
            return Registry(adapter)

        legs.append(("postgres", postgres, True))
    return legs


def check_states() -> tuple[list[str], list[str], list[str]]:
    problems: list[str] = []
    lines: list[str] = []
    unreachable: list[str] = []
    for leg, build, knowable in _legs():
        for caller, probe in PROBES.items():
            for label, fixture, refused, reasons, kind in STATES:
                # `sqlite_minimal` cannot index membership, so EVERY extent comes back
                # unknowable there -- which is the state row 3c's trip was made of, and
                # it makes that leg the `unknowable` row of the matrix rather than a leg
                # that runs the other three. Rule U: unknown is not equal, so the
                # collapse is refused even where the fixture says the extents match.
                expect_refused = refused or not knowable
                registry = build()
                try:
                    fixture(registry)
                    failure = probe(
                        registry,
                        expect_refused=expect_refused,
                        reasons=reasons,
                        kind=kind,
                    )
                except Exception as error:  # pragma: no cover - a fixture that broke
                    failure = f"the probe raised {type(error).__name__}: {error}"
                state = label if knowable else f"{label} (unknowable here)"
                verdict = "REFUSED" if expect_refused else "allowed"
                if failure and failure.startswith(_NOT_REACHABLE):
                    unreachable.append(
                        f"{leg} / {caller} / {state}: "
                        + failure[len(_NOT_REACHABLE):]
                    )
                    lines.append(f"  {leg:15s} {caller:13s} {state:28s} NOT REACHABLE")
                elif failure:
                    problems.append(f"{leg} / {caller} / {state}: {failure}")
                    lines.append(f"  {leg:15s} {caller:13s} {state:28s} FAILED")
                else:
                    lines.append(f"  {leg:15s} {caller:13s} {state:28s} {verdict}")
        # **The two states no real leg can produce, built with the double.** Both are
        # shapes of trips this project has already taken, and `unknowable` was exercised
        # for `merge_types` alone until row 4c's first adversarial round pointed out that
        # `import_types x unknowable` was exercised on no leg at all -- the state the
        # FIRST trip was made of, on the caller the FOURTH was.
        #
        # `partial` is the FIFTH trip's own shape: an honest paging backend
        # (`page_cap`/`page_cursor`, which PACKAGE.md 3.3 permits and UC3's scale
        # produces) whose first page of two extents matches while the extents differ.
        # `_extent` read one page and every guard discarded the `why` that said so, so
        # two predicates compared equal and all three callers performed the collapse.
        # No real leg pages at two rows, which is exactly why this row is synthetic.
        if knowable:
            for shape, wrap in (
                ("unknowable", lambda a: DegradedAdapter(a, indexes_membership=False)),
                ("partial", lambda a: DegradedAdapter(a, page_cap=2, page_cursor=True)),
                # **`truncated` is a DIFFERENT state from `partial`, and the difference
                # is which defence catches it.** `partial` is an honest PAGE (a cursor to
                # the rest) and the fix for it is `_extent` looping to exhaustion.
                # `truncated` is a backend that caps and offers no cursor -- PACKAGE.md
                # 3.3's other honest page -- where there IS no rest to read, so the only
                # defence is the guards folding `_extent`'s own `why` into `knowable`.
                # **Added because the `partial` row did NOT catch a mutation that removed
                # that fold** (row 4c, round 1): with paging fixed the extents genuinely
                # differ, so the guard refuses for the right reason anyway and the
                # belt-and-braces went unexercised. Two states, two defences, and one
                # row cannot stand in for the other.
                ("truncated", lambda a: DegradedAdapter(a, page_cap=2)),
            ):
                for caller, probe in PROBES.items():
                    registry = build()
                    if shape in ("partial", "truncated"):
                        # Extents that genuinely differ, and whose FIRST PAGE matches.
                        _both(
                            registry,
                            ["aaa_doc", "bbb_note", "zzy_scratch"],
                            ["aaa_doc", "bbb_note"],
                        )
                    else:
                        _both(registry, ["note"], ["doc"])
                    blind = Registry(
                        wrap(registry.adapter),
                        policies={"default": NamespacePolicy(approval_policy="auto")},
                    )
                    try:
                        failure = probe(
                            blind,
                            expect_refused=True,
                            reasons={"predicate_merge"},
                            kind="predicate",
                        )
                    except Exception as error:  # pragma: no cover
                        failure = f"the probe raised {type(error).__name__}: {error}"
                    if failure and failure.startswith(_NOT_REACHABLE):
                        unreachable.append(
                            f"{leg} / {caller} / {shape}: " + failure[len(_NOT_REACHABLE):]
                        )
                        lines.append(f"  {leg:15s} {caller:13s} {shape:28s} NOT REACHABLE")
                    elif failure:
                        problems.append(f"{leg} / {caller} / {shape}: {failure}")
                        lines.append(f"  {leg:15s} {caller:13s} {shape:28s} FAILED")
                    else:
                        lines.append(f"  {leg:15s} {caller:13s} {shape:28s} REFUSED")
    return problems, lines, unreachable


# ---------------------------------------------------------------------------
# Part B, second axis -- STALENESS. The state no fixture above can pose.
#
# **The sixth trip is the first that is different in kind** (2026-08-30, row 4c's third
# adversarial round, commit ``a3f9e6e``). Trips 1-5 were all one sentence: *the guard did
# not look properly* -- at an unknowable extent, at an empty one, at all, through a
# different field, at a partial page. This one is: **the guard looked correctly, and then
# the fact changed.** Every identity guard compares extents at WRITE time; `resolve_type`
# grants confidence 1.0 at READ time; and the vocabulary moves in between.
#
# **Door 1 is the recipe, and it needs nothing unusual at all** -- two individually legal
# merges and one new type:
#
#   1. `commentable`, `searchable` and `taggable` all have the same non-empty extent;
#   2. `merge(commentable -> searchable)` -- legal, extents identical. `searchable`
#      absorbs `commentable` as an alias and `commentable` retires with `searchable` as
#      its successor;
#   3. a new type declares `searchable` and `taggable` -- **ordinary vocabulary growth,
#      no governance act at all**. Now `searchable` has a member `commentable` does not;
#   4. the identity written at step 2 is still answered at confidence 1.0, and the two
#      extents it was written over no longer agree.
#
# **The fixture is written from the trip record, not from the fix.** That is the FIFTH
# trip's lesson, stated in `4C-RUN.md` 6.4: *a checker only asks the questions its
# fixtures can pose, and this one's fixtures were built by the same person, in the same
# hour, with the same blind spot as the guard*. So the steps above are Door 1 verbatim,
# and what each caller answers is asserted rather than assumed -- including the answers
# that are **allowed**, because a row that only ever expects REFUSED is a row a registry
# passes by refusing everything.
#
# **Three members and one late arrival, so the paging doubles bite.** `DegradedAdapter`'s
# `page_cap` only caps a query it would return MORE rows than -- so a two-member extent
# never pages, and the `partial`/`truncated` doubles would have run over a fixture that
# cannot express what they are for. Three members before the merge and a fourth after it
# puts both extents over a `page_cap=2`, so the two backends of the FIFTH trip get a real
# question on this axis too.

#: The member types seeded before the first merge -- every one of them declares all three
#: predicates, so the merge at step 2 is over genuinely identical, genuinely non-empty
#: extents and is exactly as legal as `C10-09` requires it to stay.
_STALE_MEMBERS = ("aaa_note", "bbb_memo", "ccc_card")

#: The type declared AFTER the merge, against the survivor and the third predicate. This
#: is the whole of *"and then the fact changed"*: no acknowledgement, no override, no
#: governance act at all -- somebody added a type.
_STALE_LATE_MEMBER = "zzz_doc"


def _stale(registry: Registry) -> str | None:
    """Door 1's store: an identity written over agreeing extents that then diverged.

    ``None``, or a ``_NOT_REACHABLE`` sentence. A backend that cannot compute an extent
    refuses step 2 -- correctly, under Rule U -- so it cannot hold a stale identity at
    all, and that is printed as NOT REACHABLE rather than folded into the passes.
    """
    for name in ("commentable", "searchable", "taggable"):
        _seed(registry, name, kind="predicate", definition="a capability")
    for member in _STALE_MEMBERS:
        _seed(registry, member, predicates=["commentable", "searchable", "taggable"])
    merged = registry.merge_types(
        "commentable",
        "searchable",
        "identical non-empty extents",
        merged_by="user:sd",
        acknowledge=ALL_ACKNOWLEDGEMENTS,
    )
    if isinstance(merged, Refusal):
        return _NOT_REACHABLE + (
            f"this backend refuses the LEGAL merge the fixture is built on "
            f"({merged.reason}), so no identity can be written here over two agreeing "
            f"extents and the stale state is unreachable"
        )
    _seed(registry, _STALE_LATE_MEMBER, predicates=["searchable", "taggable"])
    return None


def _stale_probe_resolve(registry: Registry, *, knowable: bool) -> str | None:
    """**The read is where a stale claim is cashed, and this is the row that matters.**

    `resolve_type("commentable")` answers `searchable` at confidence 1.0 -- which
    `INTERFACE.md` 5.3 calls a registry **guarantee** -- over two extents that agreed
    when the identity was written and do not now. The redirect itself is correct and
    stays: 5.10 promises the old word still resolves. What was missing is any signal that
    the claim has gone stale.
    """
    resolution = registry.resolve_type(
        "commentable", ResolveContext(), tier="unspecified"
    )
    if resolution.outcome != "existing" or resolution.type is None:
        return (
            f"resolve_type('commentable') answered {resolution.outcome!r} -- 5.10 "
            f"promises the old word still resolves after a merge, so this fixture's "
            f"premise has broken rather than its subject"
        )
    if resolution.type.name != "searchable":
        return (
            f"resolve_type('commentable') answered {resolution.type.name!r}, not the "
            f"survivor 'searchable' -- the fixture is not in the state it claims"
        )
    if resolution.confidence != 1.0:
        return (
            f"resolve_type('commentable') answered at confidence "
            f"{resolution.confidence!r}; 5.3 calls the successor redirect a guarantee at "
            f"1.0, and lowering it is the FOUNDER's half of Q56 rather than this row's"
        )
    if "identity_stale" not in resolution.type.warnings:
        return (
            f"resolve_type('commentable') answered 'searchable' at confidence 1.0 "
            f"carrying {list(resolution.type.warnings)} -- and the two predicate extents "
            f"that claim stands on no longer agree"
            + ("" if knowable else " (and cannot be known to agree on this backend)")
            + ". The claim was TRUE WHEN IT WAS MADE and the vocabulary moved: Rule U's "
            "fourth operand, unwarned, in the call 5.3 calls a guarantee"
        )
    return None


def _stale_probe_merge(registry: Registry, *, knowable: bool) -> str | None:
    """Door 1's second merge: `searchable` and `taggable` DO agree -- the alias does not."""
    result = registry.merge_types(
        "searchable",
        "taggable",
        "the checker's stale fixture",
        merged_by="user:sd",
        acknowledge=ALL_ACKNOWLEDGEMENTS,
    )
    if not isinstance(result, Refusal):
        return (
            "merge_types('searchable' -> 'taggable') COLLAPSED under every "
            "acknowledgement. Those two extents agree -- but `searchable` carries "
            "`commentable`'s alias and `commentable` does not, so the write re-points a "
            "word at an identity nothing ever compared it to, and "
            "`resolve_type('commentable')` answers `taggable` at 1.0 on a pair this "
            "registry refuses NON-OVERRIDABLY when asked directly. The kill row, through "
            "Door 1"
        )
    if result.detail.get("overridable") is not False:
        return (
            f"merge_types' {result.reason!r} on the stale fixture does not declare itself "
            f"non-overridable; a guard that can be acknowledged past is a warning wearing "
            f"a refusal's name"
        )
    if result.reason not in {"predicate_merge", "kind_mismatch"}:
        return (
            f"merge_types refused {result.reason!r} -- an identity guard reached through "
            f"some other refusal is the same class of defect as `retire`'s ordering bug "
            f"(`C9-19`): the outcome is safe and the story is wrong"
        )
    return None


def _stale_probe_retire(registry: Registry, *, knowable: bool) -> str | None:
    """`retire('searchable', successor='taggable')` -- and the answer is NOT symmetrical.

    On a leg that can read both extents to the end this collapse is **legal**: those two
    predicates genuinely agree now, and `retire` writes no alias, so `commentable` is left
    resolving to a retired word and falls back to `proposal`. The row asserts both halves
    -- that the guard stays narrowed rather than banned, **and** that the collapse it
    declined to refuse does not reach `commentable` anyway. Where the extents cannot be
    read to the end (the three doubles) Rule U binds and the same call must be REFUSED.
    """
    result = registry.retire(
        "searchable",
        "the checker's stale fixture",
        retired_by="user:sd",
        successor="taggable",
        force=True,
    )
    identity_reasons = {"predicate_merge", "kind_mismatch", "different_consumer_sets"}
    if not knowable:
        if not isinstance(result, Refusal):
            return (
                "retire(successor=) COLLAPSED `searchable` into `taggable` with "
                "force=True on a backend that cannot read either extent to the end -- "
                "Rule U: an extent that could not be computed is not an identical extent, "
                "and `force` overrides what could be SEEN, never what would become TRUE"
            )
        if result.detail.get("overridable") is not False:
            return (
                f"retire(successor=)'s {result.reason!r} does not declare itself "
                f"non-overridable"
            )
        return None
    if isinstance(result, Refusal) and result.reason in identity_reasons:
        return (
            f"retire(successor=) refused {result.reason!r} a pair whose extents are "
            f"non-empty and identical RIGHT NOW -- the guard is narrowed, not banned "
            f"(`C10-09`'s whole content), and a registry that refuses every predicate "
            f"collapse passes a checker that only tests refusals"
        )
    after = registry.resolve_type("commentable", ResolveContext(), tier="unspecified")
    if after.type is not None and after.type.name == "taggable" and after.confidence == 1.0:
        return (
            "retire('searchable', successor='taggable') left "
            "`resolve_type('commentable')` answering `taggable` at confidence 1.0 -- the "
            "pair `merge_types` refuses non-overridably, reached by retiring the word in "
            "the middle. Door 1 with a different second act"
        )
    return None


def _stale_probe_import(registry: Registry, *, knowable: bool) -> str | None:
    """The alias `merge_types` wrote onto the survivor, re-offered to a third predicate."""
    entries = registry.import_types(
        [
            {
                "name": "taggable",
                "kind": "predicate",
                "definition": "a capability",
                "aliases": ["commentable"],
                "status": "active",
            }
        ],
        namespace="default",
        kind="predicate",
    )
    entry = entries[0]
    if not any(w.startswith("import_refused:") for w in entry.warnings):
        return (
            "import_types wrote `commentable` as an alias of `taggable` with no refusal. "
            "That alias was LEGAL on `searchable` when it was written and is not legal "
            "here -- `commentable`'s extent has not grown and `taggable`'s has -- so "
            "`resolve_type('commentable')` now answers `taggable` at 1.0 on a pair "
            "`merge_types` refuses non-overridably"
        )
    if "commentable" in (entry.aliases or ()):
        return "import_types refused and wrote the alias anyway"
    return None


def _stale_probe_reinstate(registry: Registry, *, knowable: bool) -> str | None:
    """The fourth collapsing caller, asked the stale question the other way round.

    `reinstate('commentable')` would put a live entry back under a word the survivor
    already answers to -- two active entries holding one word between them, which is
    `C16-06`'s whole-store invariant and mechanism **4** itself. It is in
    ``KNOWN_CALLERS`` as a collapsing caller (a verdict a reviewer had to correct from
    ``False`` during the sixth trip) and it had no probe at all until this axis.
    """
    result = registry.reinstate(
        "commentable", "the checker's stale fixture", reinstated_by="user:sd"
    )
    if not isinstance(result, Refusal):
        return (
            "reinstate('commentable') re-activated a word `searchable` already answers to "
            "as an alias, so two ACTIVE entries now hold one word between them -- "
            "`C16-06`'s whole-store invariant, reached by the caller whose "
            "`KNOWN_CALLERS` verdict once said it could not"
        )
    if result.detail.get("overridable") is not False:
        return f"reinstate's {result.reason!r} does not declare itself non-overridable"
    return None


#: Four collapsing callers and the READ. `resolve_type` is here and nowhere else in this
#: file's probes, because it is the only one of the five that writes nothing -- and the
#: sixth trip is the record that a claim nobody re-checks is cashed at the read.
STALE_PROBES = {
    "resolve_type": _stale_probe_resolve,
    "merge_types": _stale_probe_merge,
    "retire": _stale_probe_retire,
    "import_types": _stale_probe_import,
    "reinstate": _stale_probe_reinstate,
}


def check_staleness() -> tuple[list[str], list[str], list[str]]:
    """The stale axis, on every leg and on all three doubles."""
    problems: list[str] = []
    lines: list[str] = []
    unreachable: list[str] = []
    for leg, build, knowable in _legs():
        shapes: list[tuple[str, object, bool]] = [("stale", None, knowable)]
        if knowable:
            shapes.extend(
                [
                    (
                        "stale (unknowable)",
                        lambda a: DegradedAdapter(a, indexes_membership=False),
                        False,
                    ),
                    (
                        # **`partial` is KNOWABLE here, and getting that wrong was this
                        # axis's own first defect.** The first cut filed all three
                        # doubles as unknowable and the run said otherwise: an honest
                        # PAGE has a cursor to the rest, `_extent` loops to exhaustion
                        # (the FIFTH trip's fix), so both extents are read in full and
                        # `retire`'s collapse is as legal here as on the bare leg. The
                        # row asserting REFUSED was asserting the wrong answer -- the
                        # fifth trip's own lesson, one level up, and caught only by
                        # running the checker rather than by reading it.
                        "stale (partial)",
                        lambda a: DegradedAdapter(a, page_cap=2, page_cursor=True),
                        True,
                    ),
                    ("stale (truncated)", lambda a: DegradedAdapter(a, page_cap=2), False),
                ]
            )
        for shape, wrap, shape_knowable in shapes:
            for caller, probe in STALE_PROBES.items():
                registry = build()
                built = _stale(registry)
                if built is not None:
                    unreachable.append(
                        f"{leg} / {caller} / {shape}: " + built[len(_NOT_REACHABLE):]
                    )
                    lines.append(f"  {leg:15s} {caller:13s} {shape:28s} NOT REACHABLE")
                    continue
                if wrap is not None:
                    registry = Registry(
                        wrap(registry.adapter),
                        policies={"default": NamespacePolicy(approval_policy="auto")},
                    )
                try:
                    failure = probe(registry, knowable=shape_knowable)
                except Exception as error:  # pragma: no cover - a fixture that broke
                    failure = f"the probe raised {type(error).__name__}: {error}"
                if failure:
                    problems.append(f"{leg} / {caller} / {shape}: {failure}")
                    lines.append(f"  {leg:15s} {caller:13s} {shape:28s} FAILED")
                else:
                    lines.append(
                        f"  {leg:15s} {caller:13s} {shape:28s} "
                        + ("answered" if caller == "resolve_type" else "guarded")
                    )
    return problems, lines, unreachable


def main() -> int:
    print("ROADMAP.md's kill row -- is it guarded? Every CALLER, every extent STATE.\n")

    print("Part A -- callers that change what a name resolves to, from the AST:")
    writers = identity_writers()
    for function in sorted(writers):
        verdict = KNOWN_CALLERS.get(function)
        mark = "COLLAPSES" if verdict and verdict.collapses else "no collapse"
        if verdict is None:
            mark = "UNKNOWN"
        print(f"  {function:18s} writes {','.join(sorted(writers[function])):18s} {mark}")
    caller_problems = check_callers()

    print("\nPart B -- the guard's answer for every state, on every leg:")
    if not os.environ.get("OO_POSTGRES_DSN"):
        print("  postgres        NOT RUN -- set OO_POSTGRES_DSN to include the third leg")
    state_problems, lines, unreachable = check_states()
    for line in lines:
        print(line)

    # **The second axis, and the sixth trip is why it is a section of its own.** Every
    # state above is a state two extents are in when a guard looks; this is a state the
    # STORE is in, built by two individually legal merges and one ordinary new type. It
    # asks `resolve_type` as well as the four collapsing callers, because the read is
    # where a stale claim is cashed.
    print()
    print("  and the STALE axis -- an identity written over extents that then diverged:")
    stale_problems, stale_lines, stale_unreachable = check_staleness()
    for line in stale_lines:
        print(line)
    unreachable.extend(stale_unreachable)
    state_problems.extend(stale_problems)
    if unreachable:
        # Ruling R12, applied to this checker: **a verdict without its coverage line is
        # not a verdict.** A row whose fixture could not be built on a leg is printed and
        # named, never folded into the passes.
        print("\n  states that could not be REACHED on a leg (not passes):")
        for line in unreachable:
            print(f"    {line}")

    problems = caller_problems + state_problems
    print()
    if problems:
        for problem in problems:
            print(f"  - {problem}")
        print(
            f"\n{len(problems)} problem(s). ROADMAP.md's kill row is *the failure that "
            f"destroys meaning*, and it has been reached three times through two "
            f"different fields and three different calls. A fourth patch to one "
            f"expression is not a fix; this is."
        )
        return 1
    print(
        "Every caller that re-points a name is accounted for, and every extent state "
        "that is REACHABLE on a leg gets the guard's answer there"
        + (" (the rows above say which were not)." if unreachable else ".")
        + "\n"
        "What this does NOT cover, stated rather than implied: it checks the guards a "
        "caller HAS, not the guards a caller might need for a collapse reached through "
        "a field nobody has thought of. Part A is the half that makes that visible -- a "
        "new writer of `successor` or `aliases` fails this check until a person decides "
        "what it means."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
