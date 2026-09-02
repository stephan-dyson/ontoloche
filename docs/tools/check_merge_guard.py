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
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from ontoloche import Registry  # noqa: E402
from ontoloche.backends.sqlite import SQLiteAdapter  # noqa: E402
from ontoloche.backends.sqlite_minimal import MinimalSQLiteAdapter  # noqa: E402
from ontoloche.contract.doubles import DegradedAdapter  # noqa: E402
from ontoloche._resolve import _norm, identity_key  # noqa: E402
from ontoloche.registry import NAME_RE  # noqa: E402
from ontoloche.policy import NamespacePolicy  # noqa: E402
from ontoloche.types import (  # noqa: E402
    Consumer,
    Evidence,
    Refusal,
    ResolveContext,
    TypeEntry,
)

REGISTRY_SOURCE = ROOT / "ontoloche" / "registry.py"

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
    # **`_declared_predicate_moved` was here for one commit, and Part A took it back
    # out.** Row 4d's item 4 added it naming `successor` as a constant, so the scan
    # flagged it UNKNOWN and the suite went red until a person wrote down that it is a
    # READER. Round 1 then rewrote it to follow `_identity_closure` instead of one hop,
    # it stopped naming the field at all, and Part A's OTHER half -- *a stale entry here
    # is a guard somebody thinks is being checked and is not* -- failed until the entry
    # came out again. Both halves earned their keep inside one row, so the churn is
    # recorded rather than tidied away.
    "_alias_map": CallerVerdict(
        False,
        "**READS** every ACTIVE row's `aliases` in one `(namespace, kind)` and hands "
        "back `{word -> the live row that answers to it}` -- the mirror of "
        "`_successor_map`, added by row 4d's SECOND round because `_identity_closure` "
        "walked the successor relation both ways and the alias relation only ONE way, so "
        "an identity written the way `import_types` writes one (an alias onto a live row, "
        "with no row of that name) was findable from the survivor and **invisible** from "
        "the absorbed word. It builds a map; it writes no row. Flagged by the over-broad "
        "scan the minute it was added, which is Part A working: a new function naming an "
        "identity field fails this check until a person writes down what it means.",
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
# Part A2 -- **does every collapsing caller reach the SHARED guard?** Row 6b, ruling R53.
#
# Part A asks *"is there a caller nobody has judged?"* and Part B asks *"does the guard
# give the right answer in every state?"*, and between them they missed the question this
# row's extraction makes askable for the first time: **is a caller that a person has
# judged CAN collapse actually running the guards at all?**
#
# Before the extraction that question had no mechanical form -- the three refusals were
# three copies of an expression, and "does this function contain a copy" is not something
# an AST can ask without enumerating shapes, which is the artefact row 4c's round 2
# proved is the same artefact as the guard. **After the extraction it is one name.** A
# caller marked `collapses=True` that never reaches `_identity_breach` is a caller that
# has quietly stopped being guarded, and that is exactly how the kill row was reached
# through `import_types` (trip four) and `retire(successor=)` (trip three): not by a
# guard being wrong, but by a caller having none.
#
# **Reached, not called directly** -- the graph is walked, because three of the five reach
# it through a helper (`_alias_identity_breach`, `_lifecycle_collisions`, `_alias_holder`)
# and demanding a direct call would force every caller to inline the lookup, which is the
# duplication R53 exists to remove.
#
# **The residual, stated rather than implied**, in the shape ruling R52 asks for: this
# proves a caller can REACH the guard, not that it reaches it on every path through
# itself. A caller with an early return that skips the guard passes here and fails Part B
# -- which is why both halves run, and why the fifth and sixth trips are the record that
# neither substitutes for the other.

#: The one function INTERFACE.md 5.10's three identity refusals now live in.
SHARED_GUARD = "_identity_breach"

#: ...and the name row 6b gave the guards' reading of a predicate's extent (ruling R64).
#: `_extent`'s `identity` is a REQUIRED keyword since this row, so no caller can take a
#: reading by accident; this is the name the guards' reading has.
WRITTEN_EXTENT = "_written_extent"


def _call_graph() -> dict[str, set[str]]:
    """``{function -> the method names it calls}``, over `registry.py`'s AST."""
    tree = ast.parse(REGISTRY_SOURCE.read_text(encoding="utf-8"))
    parents: dict[int, ast.AST] = {}
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            parents[id(child)] = node
    graph: dict[str, set[str]] = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = getattr(node.func, "attr", None) or getattr(node.func, "id", None)
        if name is None:
            continue
        graph.setdefault(_enclosing_function(node, parents), set()).add(name)
    return graph


def _path_to(graph: dict[str, set[str]], start: str, target: str) -> list[str] | None:
    """The shortest call path from ``start`` to ``target``, or ``None``.

    **The PATH and not a boolean, deliberately.** `reinstate` reaches the guards only
    through `_alias_identity_breach` -- the alias door -- and a reader who saw `True`
    would not know that. Printing the route makes the enumeration's real subject visible,
    which is `KNOWN_CALLERS`' own lesson: *a person's judgement, written down and wrong,
    is one a reviewer can find.*
    """
    seen, frontier = {start}, [[start]]
    while frontier:
        trail = frontier.pop(0)
        for called in sorted(graph.get(trail[-1], ())):
            if called == target:
                return trail + [called]
            if called not in seen:
                seen.add(called)
                frontier.append(trail + [called])
    return None


def _reaches(graph: dict[str, set[str]], start: str, target: str) -> bool:
    return _path_to(graph, start, target) is not None


def check_shared_guard() -> list[str]:
    """Every `collapses=True` caller reaches the shared guard; nothing else needs to."""
    problems: list[str] = []
    graph = _call_graph()

    if SHARED_GUARD not in graph:
        problems.append(
            f"SHARED GUARD: `registry.py` has no function `{SHARED_GUARD}`. Ruling R53 "
            f"put INTERFACE.md §5.10's refusals #1, #2 and #3 in ONE place; if that place "
            f"is gone the three are copies again, and the kill row has been reached "
            f"through eight of the gaps between copies"
        )
        return problems

    if not _reaches(graph, SHARED_GUARD, WRITTEN_EXTENT):
        problems.append(
            f"SHARED GUARD: `{SHARED_GUARD}` does not reach `{WRITTEN_EXTENT}`. Ruling "
            f"R64 named the guards' reading -- the WRITTEN word's members, not the "
            f"identity closure's -- because reading the closure makes the guard agree "
            f"with itself: the merge under examination is exactly what joined the two "
            f"names into one identity (D-4d-1, `C10-14`)"
        )

    for function, verdict in sorted(KNOWN_CALLERS.items()):
        if not verdict.collapses:
            continue
        if not _reaches(graph, function, SHARED_GUARD):
            problems.append(
                f"SHARED GUARD: `{function}` is recorded as a caller that CAN collapse "
                f"two identities into one, and nothing on any path out of it reaches "
                f"`{SHARED_GUARD}`. That is not a guard giving the wrong answer -- it is "
                f"a caller having none, which is how the kill row was reached through "
                f"`retire(successor=)` (trip three) and `import_types` (trip four). "
                f"Either it runs §5.10's guards, or KNOWN_CALLERS is wrong about it"
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


#: Every Postgres adapter this run created, so :func:`_drop_postgres_schemas` can drop
#: the schema each one owns. See the note in ``_legs``.
_POSTGRES_SCHEMAS: list = []


def _drop_postgres_schemas() -> None:
    """Drop every schema this run created. Called from ``main`` in a ``finally``."""
    for adapter in _POSTGRES_SCHEMAS:
        try:
            adapter._execute(f'DROP SCHEMA IF EXISTS "{adapter.schema}" CASCADE')
            close = getattr(adapter, "close", None)
            if close:
                close()
        except Exception:  # pragma: no cover - cleanup must not mask a verdict
            pass
    _POSTGRES_SCHEMAS.clear()


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
        from ontoloche.backends.postgres import PostgresAdapter

        def postgres():
            adapter = PostgresAdapter(dsn, schema="oo_" + uuid.uuid4().hex[:12])
            adapter.migrate()
            # **Recorded so it can be DROPPED, and not doing so bit this row.** Every
            # fixture in this file builds a fresh store, and on the Postgres leg that is
            # a fresh SCHEMA -- one per (caller x state x leg), five axes deep. Nothing
            # dropped them, so the database accumulated **19,220** `oo_*` schemas across
            # this row's runs, and the catalog bloat crashed the backend with three
            # SEGFAULTs during `CREATE TABLE`, each followed by ~4.5 minutes of recovery.
            # A checker that has to be run to be believed must be cheap enough to run.
            _POSTGRES_SCHEMAS.append(adapter)
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
    """`retire('searchable', successor='taggable')` on Door 1's store.

    **The row asserts the INVARIANT, not a verdict, and getting that wrong twice is why**
    (row 4d, rounds 1 and 2). What matters is that the collapse `merge_types` refuses
    non-overridably is not reachable by retiring the word in the middle:
    `resolve_type('commentable')` must not answer `taggable` at confidence 1.0. Whether
    the call refuses or allows is the registry's business, provided that holds — and it
    changed **twice** while this row was open:

    * **round 1** filed all three degraded doubles as *unknowable* and required a REFUSAL
      on each. On `partial` that was wrong: an honest page carries a cursor, `_extent`
      loops to exhaustion, and the two extents genuinely agree;
    * **round 2** made `resolve_type` follow the successor CHAIN, which re-pointed every
      alias `searchable` carries at `taggable` — so `retire` gained the transferred-alias
      guard `merge_types` has carried since `C10-13`, and the call this row had asserted
      *legal* became correctly refused.

    A fixture that asserts a verdict has to be rewritten every time a guard moves; one
    that asserts the invariant does not. **The invariant is the thing the kill row is
    about.**
    """
    result = registry.retire(
        "searchable",
        "the checker's stale fixture",
        retired_by="user:sd",
        successor="taggable",
        force=True,
    )
    identity_reasons = {
        "predicate_merge", "kind_mismatch", "different_consumer_sets",
        "successor_unregistered",
    }
    if isinstance(result, Refusal):
        if result.reason in identity_reasons and result.detail.get("overridable") is not False:
            return (
                f"retire(successor=)'s {result.reason!r} does not declare itself "
                f"non-overridable -- `force` overrides what could be SEEN, never what "
                f"would become TRUE"
            )
        if result.reason not in identity_reasons | {"cannot_record_override"}:
            return (
                f"retire(successor=) refused {result.reason!r} on the stale fixture. A "
                f"non-overridable identity guard reached through some OTHER refusal is "
                f"`C9-19`'s defect class: the outcome is safe and the story is wrong"
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


# ---------------------------------------------------------------------------
# Part B, third axis -- SPELLING. The kill row's SEVENTH trip.
#
# **Trips 1-5 were "the guard did not look properly". Trip 6 was "the guard looked
# correctly, and then the fact changed". Trip 7 is "the guard and the resolver disagree
# about what THE SAME WORD is."** (2026-08-30, row 4d's first adversarial round.)
#
# Every alias guard in this registry finds its collision by an exact byte comparison --
# `rec.name == alias`, `alias in rec.aliases`, `candidate in entry.aliases`. The shipped
# `DeterministicResolver` scores `_norm(candidate)` against `_norm(alias)`, where `_norm`
# lowercases and collapses every run of non-`[a-z0-9]` to `_`. So `'Commentable'` is a
# word the guards have never heard of and the resolver rates **1.0**:
#
#   1. `commentable` {aaa_note} and `searchable` {aaa_note, bbb_memo} -- two live
#      predicates whose extents genuinely differ. `merge_types` refuses that pair
#      NON-OVERRIDABLY under all five acknowledgements;
#   2. `commentable` is retired -- an ordinary, permitted governance act;
#   3. `import_types` writing `aliases: ["commentable"]` is **refused**,
#      `predicate_merge` -- row 4c's fourth-trip guard, working;
#   4. `import_types` writing `aliases: ["Commentable"]` is **written, no refusal, no
#      warning**;
#   5. `resolve_type("commentable")` answers **`searchable` at confidence 1.0** -- which
#      INTERFACE.md 5.3 calls a guarantee -- with the two extents still different and
#      **no `identity_stale`**, because row 4d's own staleness gate is the same byte
#      comparison.
#
# **The non-canonical spelling is the REAL one.** `import_types` is UC1's Foundry
# migration path and UC3's Socrata shape, and a real export's field labels arrive as
# `"Status"` and `"Processing Date"`, not as `snake_case`.
#
# **This axis exists because the other two could not pose the question.** Every fixture
# in this file spells every word exactly one way, so the checker exited 0 through trip 7
# as it did through trips 5 and 6 -- three consecutive trips, and the same sentence each
# time: *a checker only asks the questions its fixtures can pose*. The alphabet was the
# blind spot this time.
#
# It compares against **the resolver's own `_norm`**, imported rather than copied,
# because the defect is precisely that two definitions of *the same word* exist in one
# codebase and disagree.

#: Spellings `identity_key` maps onto `commentable`, so the shipped resolver scores each
#: of them 1.0 against it: case, a trailing space, a punctuation run that normalises away
#: -- and **`commentable_`, which is a `NAME_RE`-LEGAL NAME.**
#:
#: **That last one is the EIGHTH trip, and its absence is why four axes exited 0 through
#: it** (row 4d, round 3). Not one of the first four spellings satisfies
#: `^[a-z][a-z0-9_]{0,63}$`, so every one of them can only ever arrive in the `aliases`
#: field -- and the axis could therefore pose *"can a variant reach the alias door?"* and
#: never *"can a variant be a row's own NAME?"*. `NAME_RE` admits `commentable_`,
#: `commentable__`, `bike__lane`, `borough_`: every one a variant by `identity_key`, and
#: every one a legal name two agencies normalising their own column headers will produce.
#:
#: **`name` is an identity field too**, and Part A's `IDENTITY_FIELDS` says only
#: `successor` and `aliases`: two rows whose names share one key are two entries
#: answering one word, which is `C16-06` and mechanism 4.
_SPELLINGS = ("Commentable", "COMMENTABLE", "commentable ", "commentable-", "commentable_")

#: Words `identity_key` maps to the EMPTY string, which `difflib` then rates **1.0**
#: against every other such word. Row 4d, round 3: the identity function erases every
#: word with no ASCII alphanumerics -- and UC3's catalogue is multi-agency with non-Latin
#: labels, while UC2's CMS export has punctuation-only headers. It fails in **both**
#: directions: a false 1.0 between two unrelated labels, and a false `alias_collision`
#: refusing a second agency's legitimate word.
_ERASED_WORDS = ("\u72b6\u6001", "\u7c7b\u578b", "---", "!!!")


def _spelling_store(registry: Registry) -> str | None:
    """Two live predicates whose extents differ, with the left one retired.

    The pair `merge_types` refuses non-overridably, left in the state the FOURTH trip was
    made of: a retired predicate name that still resolves and still has an extent.
    """
    _seed(registry, "commentable", kind="predicate", definition="a capability")
    _seed(registry, "searchable", kind="predicate", definition="a capability")
    _seed(registry, "aaa_note", predicates=["commentable", "searchable"])
    _seed(registry, "bbb_memo", predicates=["searchable"])
    direct = registry.merge_types(
        "commentable", "searchable", "the checker's spelling fixture",
        merged_by="user:sd", acknowledge=ALL_ACKNOWLEDGEMENTS,
    )
    if not isinstance(direct, Refusal):
        return _NOT_REACHABLE + (
            "this backend does not refuse the pair the fixture is built on, so there is "
            "no refusal for a spelling to walk past"
        )
    retired = registry.retire("commentable", "superseded", retired_by="user:sd", force=True)
    if isinstance(retired, Refusal):
        return _NOT_REACHABLE + (
            f"this backend cannot record the forced retirement the fixture needs: "
            f"{retired.reason}"
        )
    return None


def _spelling_probe_import(registry: Registry, spelling: str) -> str | None:
    """The WRITE door: the same word, spelled the way a foreign system spells it."""
    entries = registry.import_types(
        [{
            "name": "searchable", "kind": "predicate", "definition": "a capability",
            "aliases": [spelling], "status": "active",
        }],
        namespace="default", kind="predicate",
    )
    entry = entries[0]
    if not any(w.startswith("import_refused:") for w in entry.warnings):
        resolution = registry.resolve_type("commentable", ResolveContext(), tier="unspecified")
        answered = resolution.type.name if resolution.type is not None else resolution.outcome
        return (
            f"import_types wrote {spelling!r} as an alias of `searchable` with NO refusal, "
            f"while the identical import spelled `commentable` is refused "
            f"`predicate_merge` -- the guard compares bytes and the resolver compares "
            f"normalised words, so one word gets two verdicts. "
            f"`resolve_type('commentable')` now answers {answered!r} at "
            f"{resolution.confidence!r}"
            + (f" carrying {list(resolution.type.warnings)}" if resolution.type is not None else "")
            + ", on a pair `merge_types` refuses non-overridably. The kill row, through "
            "the spelling door"
        )
    if spelling in (entry.aliases or ()):
        return f"import_types refused {spelling!r} and wrote the alias anyway"
    return None


def _spelling_probe_read(registry: Registry, spelling: str) -> str | None:
    """The READ door: a stale identity asked about under a variant spelling.

    Row 4d's staleness gate is `candidate in entry.aliases` -- an exact-string test on a
    redirect the resolver reached by NORMALISING.
    """
    resolution = registry.resolve_type(spelling, ResolveContext(), tier="unspecified")
    if resolution.type is None or resolution.type.name != "searchable":
        # The resolver did not reach the redirect under this spelling, so there is no
        # identity claim to re-verify and nothing to warn about.
        return None
    if resolution.confidence != 1.0:
        return None
    if "identity_stale" not in resolution.type.warnings:
        return (
            f"resolve_type({spelling!r}) answered 'searchable' at confidence 1.0 -- the "
            f"same identity claim `resolve_type('commentable')` warns about -- carrying "
            f"{list(resolution.type.warnings)}. The staleness gate goes quiet on exactly "
            f"the spelling a foreign system sends"
        )
    return None


def _spelling_probe_name(registry: Registry, spelling: str) -> str | None:
    """The NAME door: the same word, arriving as a row's own name rather than an alias.

    Only reachable for a `NAME_RE`-legal spelling, and that is the point -- the four
    spellings this axis started with are all illegal as names, so it could not pose this
    question and exited 0 through the EIGHTH trip.
    """
    if not NAME_RE.match(spelling):
        return _NOT_REACHABLE + (
            f"{spelling!r} is not a legal type NAME (`NAME_RE`), so it can only ever "
            f"arrive as an alias -- which the write row above is what asks"
        )
    out = registry.propose_type(
        spelling, "a capability", EVIDENCE, "user:sd", kind="predicate"
    )
    if not isinstance(out, (Refusal, TypeEntry)):
        approved = registry.approve(out.id, "user:sd")
        if isinstance(approved, Refusal):
            return None
    elif isinstance(out, Refusal):
        return None
    _seed(registry, "ddd_doc", predicates=[spelling])
    resolution = registry.resolve_type(
        "commentable", ResolveContext(), tier="unspecified"
    )
    if (
        resolution.type is not None
        and identity_key(resolution.type.name) == identity_key("commentable")
        and resolution.type.name != "commentable"
        and resolution.confidence == 1.0
    ):
        return (
            f"a row NAMED {spelling!r} went live beside the retired `commentable`, and "
            f"`resolve_type('commentable')` answers it at confidence 1.0 carrying "
            f"{list(resolution.type.warnings)} -- two rows whose names are ONE WORD by "
            f"the registry's own key, over extents `merge_types` refuses "
            f"non-overridably. `name` is an identity field, and this door compares bytes"
        )
    return None


def _spelling_probe_erased(registry: Registry, spelling: str) -> str | None:
    """A word `identity_key` maps to the EMPTY string, offered as an alias."""
    entries = registry.import_types(
        [{
            "name": "searchable", "kind": "predicate", "definition": "a capability",
            "aliases": [spelling], "status": "active",
        }],
        namespace="default", kind="predicate",
    )
    if any(w.startswith("import_refused:") for w in entries[0].warnings):
        return None
    other = next(w for w in _ERASED_WORDS if w != spelling)
    resolution = registry.resolve_type(other, ResolveContext(), tier="unspecified")
    if resolution.type is not None and resolution.confidence == 1.0:
        return (
            f"`searchable` was given the alias {spelling!r}, and "
            f"`resolve_type({other!r})` -- a DIFFERENT word -- answers it at confidence "
            f"1.0. `identity_key` maps every word with no ASCII alphanumerics to the "
            f"empty string, and `difflib` rates two empty strings a perfect match, so "
            f"the identity function MANUFACTURES mechanism 4 instead of preventing it"
        )
    return None


def check_spellings() -> tuple[list[str], list[str], list[str]]:
    """The spelling axis, on every leg that can pose it."""
    problems: list[str] = []
    lines: list[str] = []
    unreachable: list[str] = []
    for leg, build, _knowable in _legs():
        for spelling in _ERASED_WORDS:
            registry = build()
            built = _spelling_store(registry)
            label = "erased word"
            if built is not None:
                unreachable.append(f"{leg} / import_types / {label}: " + built[len(_NOT_REACHABLE):])
                lines.append(f"  {leg:15s} {'import_types':13s} {label:28s} NOT REACHABLE")
                continue
            try:
                failure = _spelling_probe_erased(registry, spelling)
            except Exception as error:  # pragma: no cover
                failure = f"the probe raised {type(error).__name__}: {error}"
            if failure:
                problems.append(f"{leg} / import_types / {label}: {failure}")
                lines.append(f"  {leg:15s} {'import_types':13s} {label:28s} FAILED")
            else:
                lines.append(f"  {leg:15s} {'import_types':13s} {label:28s} guarded")
    for leg, build, _knowable in _legs():
        for spelling in _SPELLINGS:
            for caller, label, store, probe in (
                ("import_types", f"write {spelling!r}", _spelling_store, _spelling_probe_import),
                ("resolve_type", f"read {spelling!r}", _stale, _spelling_probe_read),
                ("propose_type", f"name {spelling!r}", _spelling_store, _spelling_probe_name),
            ):
                registry = build()
                built = store(registry)
                if built is not None:
                    unreachable.append(f"{leg} / {caller} / {label}: " + built[len(_NOT_REACHABLE):])
                    lines.append(f"  {leg:15s} {caller:13s} {label:28s} NOT REACHABLE")
                    continue
                try:
                    failure = probe(registry, spelling)
                except Exception as error:  # pragma: no cover
                    failure = f"the probe raised {type(error).__name__}: {error}"
                if failure and failure.startswith(_NOT_REACHABLE):
                    unreachable.append(
                        f"{leg} / {caller} / {label}: " + failure[len(_NOT_REACHABLE):]
                    )
                    lines.append(f"  {leg:15s} {caller:13s} {label:28s} NOT REACHABLE")
                elif failure:
                    problems.append(f"{leg} / {caller} / {label}: {failure}")
                    lines.append(f"  {leg:15s} {caller:13s} {label:28s} FAILED")
                else:
                    lines.append(f"  {leg:15s} {caller:13s} {label:28s} guarded")
    return problems, lines, unreachable


# ---------------------------------------------------------------------------
# Part B, fourth axis -- ONE WORD, ONE LIVE IDENTITY.
#
# **`C16-06`'s whole-store invariant, asked of every write door rather than of one
# fixture.** INTERFACE.md 5.9b's `alias_collision` exists to stop *two active entries
# holding one word between them*, which is mechanism 4 itself. Row 4c's third round
# closed the door it found -- `propose_type` matching `name` and never `aliases` -- and
# row 4d's first adversarial round found the same question unasked at four more:
#
#   * `import_types` runs its alias block only `if incoming:`, so a row whose NAME is
#     spoken for, carrying no aliases of its own, is written with no refusal;
#   * `propose_type` asks at PROPOSE time and `_write_approved` writes the row at
#     APPROVE time, re-checking nothing -- and ruling **R40** forces every
#     `kind="predicate"` down that two-step path, so the guard is structurally
#     unavailable for the one kind the kill row is about;
#   * `reinstate` runs the extent guards over its dormant aliases and never asks whether
#     one of them is already held by a LIVE entry -- the question its sibling
#     `import_types` asks with `_alias_clash` on the same field;
#   * `_alias_holder` throws away `_active_page`'s `why`, so **a truncated page reads as
#     "the word is free"** -- Rule U's third operand (*partial is not equal*, the fifth
#     trip) missing from a guard shipped by the commit whose subject is the fourth.
#
# The invariant is checked over the WHOLE STORE after each door, under the resolver's own
# key, because that is the property `C16-06` states and the one a caller can feel:
# `resolve_type` answering one word with two different identities depending on nothing.


def _one_word_holders(registry: Registry, namespace: str = "default") -> dict[str, list[str]]:
    """``{word key -> the live entries that answer to it}``, `C16-06`'s own question.

    Keyed by the RESOLVER's own normalisation, because the property a caller can feel is
    *`resolve_type` answers one word with two different identities*, and the resolver is
    what decides which words are one word.
    """
    holders: dict[str, list[str]] = {}
    for entry in registry.list_types(namespace=namespace).types:
        for word in (entry.name,) + tuple(entry.aliases or ()):
            holders.setdefault(_norm(word), []).append(entry.name)
    return {word: sorted(set(names)) for word, names in holders.items() if len(set(names)) > 1}


def _alias_only_store(registry: Registry, spelling: str = "commentable") -> str | None:
    """A live entry that answers to a word **no row of that name has ever held**.

    `import_types` writes a foreign dump's aliases, and the word names nothing here, so
    no identity guard has anything to compare and the alias is written -- which is
    correct, and is the state every door below is asked about.

    ``spelling`` is how the FOREIGN system spelled it. **Only aliases can be
    non-canonical:** `propose_type` puts every `name` through `NAME_RE`, so `Commentable`
    can never be a row's name -- a real and reassuring result, and the reason the
    spelling hole is alias-side and read-side only. A dump's alias list is validated by
    nothing.
    """
    _seed(registry, "searchable", kind="predicate", definition="a capability")
    _seed(registry, "aaa_note", predicates=["searchable"])
    entries = registry.import_types(
        [{"name": "searchable", "kind": "predicate", "definition": "a capability",
          "aliases": [spelling], "status": "active"}],
        namespace="default", kind="predicate",
    )
    if spelling not in (entries[0].aliases or ()):
        return _NOT_REACHABLE + (
            f"this backend did not store the alias the fixture is built on "
            f"({list(entries[0].warnings)}), so no word is spoken for here"
        )
    return None


def _door_propose(registry: Registry):
    return registry.propose_type(
        "commentable", "a capability", EVIDENCE, "user:sd", kind="predicate"
    )


def _door_import_name(registry: Registry):
    return registry.import_types(
        [{"name": "commentable", "kind": "predicate", "definition": "a capability",
          "status": "active"}],
        namespace="default", kind="predicate",
    )


#: Doors that act on a store where the word is ALREADY spoken for, and the spelling the
#: foreign system used for it. `propose_type` over a canonically-spelled alias is the
#: CONTROL -- row 4c's third round closed that door and it must stay closed.
ONE_WORD_DOORS = {
    ("propose_type", "commentable"): _door_propose,
    ("propose (variant)", "Commentable"): _door_propose,
    ("import_types", "commentable"): _door_import_name,
}


def check_one_word() -> tuple[list[str], list[str], list[str]]:
    """`C16-06`'s invariant, asked of every write door and of a truncated look."""
    problems: list[str] = []
    lines: list[str] = []
    unreachable: list[str] = []

    def report(leg, door, built, registry, extra=""):
        if built is not None:
            unreachable.append(f"{leg} / {door} / one word: " + built[len(_NOT_REACHABLE):])
            lines.append(f"  {leg:15s} {door:17s} {'one word':24s} NOT REACHABLE")
            return
        shared = _one_word_holders(registry)
        if shared:
            problems.append(
                f"{leg} / {door} / one word: after this door, {shared} -- two LIVE "
                f"entries answer to one word, which is `C16-06`'s whole-store invariant "
                f"and INTERFACE.md 5.9b's `alias_collision`, and it is mechanism 4 "
                f"itself. `propose_type` refuses this exact act" + extra
            )
            lines.append(f"  {leg:15s} {door:17s} {'one word':24s} FAILED")
        else:
            lines.append(f"  {leg:15s} {door:17s} {'one word':24s} held")

    for leg, build, _knowable in _legs():
        for (door, spelling), act in ONE_WORD_DOORS.items():
            registry = build()
            built = _alias_only_store(registry, spelling)
            result = None
            if built is None:
                result = act(registry)
            # **The whole-store invariant is not enough at this door, and finding that
            # out took one run.** Ruling R40 makes `propose_type(kind="predicate")`
            # return a PENDING proposal, so on a backend that can hold one the invariant
            # sees no second live row and the door reads `held` for the wrong reason --
            # the collision arrives one call later, at `approve`. So the propose doors
            # assert the REFUSAL as well: 5.9b's `alias_collision` is what the caller is
            # owed, and it is owed at the door they knocked on.
            if built is None and door.startswith("propose") and not isinstance(result, Refusal):
                problems.append(
                    f"{leg} / {door} / one word: `propose_type` did not refuse "
                    f"`alias_collision` for a word the live entry `searchable` already "
                    f"answers to as the alias {spelling!r} -- it returned a "
                    f"{type(result).__name__}. The guard finds its collision by an exact "
                    f"byte comparison and the resolver scores {spelling!r} and "
                    f"'commentable' as ONE word at 1.0, so the two disagree about what "
                    f"the same word IS"
                )
                lines.append(f"  {leg:15s} {door:17s} {'one word':24s} FAILED")
                continue
            report(leg, door, built, registry)

        # **The APPROVE door needs its own ordering**: the word is free when the
        # proposal is made and taken by the time it is approved, and `_write_approved`
        # re-checks nothing. **Ruling R40 forces every `kind="predicate"` down this
        # two-step path**, so the guard is structurally unavailable for the one kind the
        # kill row is about -- and the human review window R40 exists to create is
        # exactly the window in which the check goes stale.
        registry = build()
        pending = registry.propose_type(
            "commentable", "a capability", EVIDENCE, "user:sd", kind="predicate"
        )
        if isinstance(pending, (Refusal, TypeEntry)):
            unreachable.append(
                f"{leg} / approve / one word: this backend cannot hold a pending "
                f"proposal, so there is no window between the proposal and the write"
            )
            lines.append(f"  {leg:15s} {'approve':17s} {'one word':24s} NOT REACHABLE")
        else:
            built = _alias_only_store(registry)
            if built is None:
                registry.approve(pending.id, "user:sd")
            report(
                leg, "approve", built, registry,
                extra=" -- and the word was FREE when the proposal was made",
            )

        # **A truncated look has not said the word is free.** Rule U's third operand
        # (*partial is not equal*, the fifth trip), asked of the guard `propose_type`
        # uses: `_alias_holder` reads `_active_page` and discards its `why`.
        registry = build()
        built = _alias_only_store(registry)
        if built is not None:
            unreachable.append(f"{leg} / propose (capped) / one word: " + built[len(_NOT_REACHABLE):])
            lines.append(f"  {leg:15s} {'propose (capped)':17s} {'one word':24s} NOT REACHABLE")
        else:
            for i in range(8):
                _seed(registry, f"filler_{i}", definition="a filler")
            capped = Registry(
                DegradedAdapter(registry.adapter, page_cap=3),
                policies={"default": NamespacePolicy(approval_policy="auto")},
            )
            out = capped.propose_type(
                "commentable", "a capability", EVIDENCE, "user:sd", kind="predicate"
            )
            # **The warning, not a refusal -- and this row asserted the wrong answer
            # until the suite said so.** The first fix refused here, and `C3-13` (whose
            # whole subject is a backend that caps an unlimited query) went red: refusing
            # does not narrow the guard, it BANS `propose_type` on every paging backend,
            # at exactly the scale UC3 describes. `C10-09`'s lesson, one call along. So
            # what is owed is Rule U REPORTED -- the caller is told the look did not
            # finish -- and this row asks for that.
            said = "alias_check_incomplete" in " ".join(getattr(out, "warnings", ()) or ())
            if not isinstance(out, Refusal) and not said:
                problems.append(
                    f"{leg} / propose (capped) / one word: `propose_type` accepted a word "
                    f"a live entry already answers to and said NOTHING, because the "
                    f"collision scan read a page the backend had ALREADY SAID was partial "
                    f"and read the absence as an answer. The full read refuses "
                    f"`alias_collision` non-overridably. Rule U's third operand -- partial "
                    f"is not equal -- missing from a guard shipped by the commit whose "
                    f"subject is the fourth"
                )
                lines.append(f"  {leg:15s} {'propose (capped)':17s} {'one word':24s} FAILED")
            else:
                lines.append(f"  {leg:15s} {'propose (capped)':17s} {'one word':24s} held")

        # **`reinstate` re-activating a row whose dormant alias a live entry has since
        # come to answer to** -- the question its sibling `import_types` asks with
        # `_alias_clash` on the same field, and the one `reinstate` never asks.
        registry = build()
        _seed(registry, "searchable", kind="predicate", definition="a capability")
        _seed(registry, "taggable", kind="predicate", definition="a capability")
        _seed(registry, "aaa_note", predicates=["searchable", "taggable"])
        parked = registry.import_types(
            [{"name": "searchable", "kind": "predicate", "definition": "a capability",
              "aliases": ["commentable"], "status": "active"}],
            namespace="default", kind="predicate",
        )
        retired = registry.retire("searchable", "parked", retired_by="user:sd", force=True)
        if "commentable" not in (parked[0].aliases or ()) or isinstance(retired, Refusal):
            unreachable.append(
                f"{leg} / reinstate / one word: this backend cannot build the dormant "
                f"alias the fixture needs"
            )
            lines.append(f"  {leg:15s} {'reinstate':17s} {'one word':24s} NOT REACHABLE")
            continue
        registry.import_types(
            [{"name": "taggable", "kind": "predicate", "definition": "a capability",
              "aliases": ["commentable"], "status": "active"}],
            namespace="default", kind="predicate",
        )
        registry.reinstate("searchable", "unparked", reinstated_by="user:sd")
        report(leg, "reinstate", None, registry, extra=" -- and its sibling `import_types` asks it")
    return problems, lines, unreachable


# ---------------------------------------------------------------------------
# Part B, fifth axis -- A SUCCESSOR THAT DOES NOT EXIST YET.
#
# **Every identity guard on `retire(successor=)` is nested inside `if successor row is
# not None`.** Naming a successor before it is registered skips all three -- guard #1
# (`different_consumer_sets`, transferred by `C9-20`), #2 (`predicate_merge`) and #3
# (`kind_mismatch`) -- and the word is then created by an ordinary `propose_type` +
# `approve`. `resolve_type` cashes the redirect at confidence 1.0.
#
# It is the sixth trip's own shape applied to the guards the sixth trip's commit shipped:
# **the guard looked, found nothing to compare, and then the fact arrived.** And the
# `kind` case is worse than the predicate case, because Q56's default cannot warn about
# it: a question about a `predicate` is answered with an `entity` at 1.0, which is
# INTERFACE.md 5.10 refusal #3, non-overridable, walked past entirely.
#
# UC3's shape exactly: *"we are replacing `status` with `service_status`; the other
# agency registers it next sprint"* is an ordinary staged migration in a
# dozens-of-publishers catalogue.


# ---------------------------------------------------------------------------
# The CONSUMER-SET axis -- refusal #1, which until row 6b's third round this checker
# **could not fail on at all**.
#
# **The structural finding, and it is countable rather than descriptive.** Before this
# axis, `check_merge_guard.py` contained **zero** occurrences of `register_consumer` and
# zero of `Consumer(`. No fixture, on any leg, at any door, ever registered one -- so both
# gate sets were empty in every probe and `different_consumer_sets` passed **vacuously
# everywhere**. The previous six trips were *"its fixtures could not pose the question"*;
# this is stronger: **the guard whose fix reached one call site of four is a guard this
# checker had no way to fail on.**
#
# It is `C9-20` that makes refusal #1 an IDENTITY guard rather than an evidence one --
# after the sixth trip collapsed, through `force=True`, a pair `merge_types` refuses under
# all seven acknowledgements -- and identity guards are exactly what Part B exists to
# drive. The ELEVENTH trip is what it missed: `retire`, `reinstate` and `merge_types` all
# called `_alias_identity_breach` without the target row's own `predicates`, so #1's
# `member_of` was empty and every consumer gating on a predicate the target declares was
# invisible to it. Three call sites out of four, unfixed at the doors trips 9 and 10 did
# not come through.

#: The predicate the fixture's consumer gates on. **Not** either of the two words being
#: collapsed: a gate naming the aliased word is re-pointed by the write itself, which
#: makes the two sets agree and the question unaskable. This is the shape the eleventh
#: trip needed.
_GATE_PREDICATE = "meta_p"


def _consumer_pair(registry: Registry, *, gated: str) -> str | None:
    """`commentable` and `searchable`, identical non-empty extents, DIFFERENT gate sets.

    Both extents are `{aaa_note, bbb_memo}`, so refusal **#2 passes honestly** and
    anything that refuses does so on **#1** -- which is the whole point of the axis. Only
    ``gated`` declares `meta_p`, and the consumer gates on `meta_p`.
    """
    _seed(registry, _GATE_PREDICATE, kind="predicate", definition="a meta capability")
    for word in ("commentable", "searchable"):
        _seed(
            registry,
            word,
            kind="predicate",
            definition="a capability",
            predicates=(
                [_GATE_PREDICATE] if gated in (word, "both") else []
            ),
        )
    for member in ("aaa_note", "bbb_memo"):
        _seed(registry, member, predicates=["commentable", "searchable"])
    out = registry.register_consumer(
        Consumer(id="svc:meta", gate=_GATE_PREDICATE, on_unknown="drop", owner="ops")
    )
    if isinstance(out, Refusal):  # pragma: no cover - a fixture that cannot be built
        return _NOT_REACHABLE + (
            f"this backend cannot register a consumer, so the two gate sets cannot be "
            f"made to differ: {out.reason}"
        )
    here = {
        c.id
        for c in registry.consumers(
            "searchable" if gated == "both" else gated
        ).gates_on
    }
    if here != {"svc:meta"}:
        return _NOT_REACHABLE + (
            f"this backend cannot report which consumers gate on a predicate "
            f"({sorted(here)}), so refusal #1 has nothing to compare"
        )
    return None


def _consumer_probe_merge(registry: Registry) -> str | None:
    fixture = _consumer_pair(registry, gated="searchable")
    if fixture is not None:
        return fixture
    result = registry.merge_types(
        "commentable", "searchable", "the consumer axis",
        merged_by="user:sd", acknowledge=ALL_ACKNOWLEDGEMENTS,
    )
    if not isinstance(result, Refusal):
        return (
            "merge_types COLLAPSED a pair whose extents agree and whose CONSUMER SETS "
            "differ -- refusal #1, which ROADMAP.md states without qualification: *it "
            "MUST refuse when the two have different consumer sets*"
        )
    if result.reason != "different_consumer_sets":
        return (
            f"merge_types refused {result.reason!r} where #1 is the guard that binds -- "
            f"the right outcome by the wrong route is `C9-19`'s defect class"
        )
    if result.detail.get("overridable") is not False:
        return "refusal #1 must be non-overridable; `C9-20` is the record that it is"
    return None


def _consumer_probe_retire(registry: Registry) -> str | None:
    fixture = _consumer_pair(registry, gated="searchable")
    if fixture is not None:
        return fixture
    for force in (False, True):
        result = registry.retire(
            "commentable", "the consumer axis", retired_by="user:sd",
            successor="searchable", force=force,
        )
        if not isinstance(result, Refusal):
            return (
                f"retire(successor=, force={force}) COLLAPSED a pair whose consumer sets "
                f"differ -- `resolve_type` now answers the old word with the new entry at "
                f"confidence 1.0, which is the merge refusal #1 forbids"
            )
        if result.reason == "cannot_record_override":
            return _NOT_REACHABLE + "this backend cannot record the retirement"
        if result.detail.get("overridable") is not False:
            return (
                f"retire(successor=)'s {result.reason!r} is overridable -- `force` "
                f"overrides what could be SEEN, never what would become TRUE"
            )
    return None


def _consumer_probe_import(registry: Registry) -> str | None:
    """The alias door, on the row `import_types` is REWRITING -- the tenth trip's shape
    with the eleventh's operand."""
    # **BOTH declare the gated predicate**, so the two sets AGREE at guard time and
    # refusal #1 passes honestly on the pre-write reading -- and the import then drops
    # the target's, so the sets the write PRODUCES differ. Gating only the target would
    # leave both sets empty afterwards, which is a legal alias and not this walk; the
    # axis' first cut did exactly that and reported a FAILURE against correct behaviour.
    fixture = _consumer_pair(registry, gated="both")
    if fixture is not None:
        return fixture
    retired = registry.retire(
        "commentable", "superseded", retired_by="user:sd", force=True
    )
    if isinstance(retired, Refusal):
        return _NOT_REACHABLE + (
            f"this backend cannot record the forced retirement the fixture needs: "
            f"{retired.reason}"
        )
    entry = registry.import_types(
        [
            {
                "name": "searchable",
                "kind": "predicate",
                "definition": "a capability",
                # The import DROPS `meta_p`, so the set this write produces is empty
                # while `commentable`'s is not. The guard must compare what the write
                # leaves behind, not what it is about to erase.
                "predicates": [],
                "aliases": ["commentable"],
                "status": "active",
            }
        ],
        namespace="default",
        kind="predicate",
    )[0]
    if not any(w.startswith("import_refused:") for w in entry.warnings):
        return (
            "import_types wrote the alias onto a row whose consumer set this same call "
            "empties -- `resolve_type('commentable')` now answers 'searchable' at "
            "confidence 1.0 on a pair `merge_types` refuses non-overridably. The TENTH "
            "trip's shape with the ELEVENTH's operand"
        )
    if "commentable" in (entry.aliases or ()):
        return "import_types refused and wrote the alias anyway"
    return None


def _consumer_probe_reinstate(registry: Registry) -> str | None:
    """**The ELEVENTH trip's own door.** The alias is written while it is legal, goes
    dormant, the world moves, and `reinstate` makes it answer at 1.0 again."""
    _seed(registry, _GATE_PREDICATE, kind="predicate", definition="a meta capability")
    for word in ("commentable", "searchable"):
        _seed(
            registry, word, kind="predicate", definition="a capability",
            predicates=[_GATE_PREDICATE] if word == "searchable" else [],
        )
    for member in ("aaa_note", "bbb_memo"):
        _seed(registry, member, predicates=["commentable", "searchable"])

    retired = registry.retire("commentable", "superseded", retired_by="user:sd", force=True)
    if isinstance(retired, Refusal):
        return _NOT_REACHABLE + f"this backend cannot record a forced retirement: {retired.reason}"
    entry = registry.import_types(
        [
            {
                "name": "searchable", "kind": "predicate", "definition": "a capability",
                "predicates": [_GATE_PREDICATE], "aliases": ["commentable"],
                "status": "active",
            }
        ],
        namespace="default", kind="predicate",
    )[0]
    if any(w.startswith("import_refused:") for w in entry.warnings):
        return _NOT_REACHABLE + (
            f"the alias is not writable on this backend even while it is LEGAL "
            f"(both gate sets empty): {entry.warnings}"
        )
    dormant = registry.retire("searchable", "dormant", retired_by="user:sd", force=True)
    if isinstance(dormant, Refusal):
        return _NOT_REACHABLE + f"this backend cannot record the second retirement: {dormant.reason}"

    # The world moves: a consumer now gates on what only `searchable` declares.
    out = registry.register_consumer(
        Consumer(id="svc:meta", gate=_GATE_PREDICATE, on_unknown="drop", owner="ops")
    )
    if isinstance(out, Refusal):
        return _NOT_REACHABLE + f"this backend cannot register a consumer: {out.reason}"
    if {c.id for c in registry.consumers("searchable").gates_on} != {"svc:meta"}:
        return _NOT_REACHABLE + "this backend cannot report which consumers gate on a predicate"

    result = registry.reinstate("searchable", "back", reinstated_by="user:sd")
    if not isinstance(result, Refusal):
        return (
            "reinstate re-activated a row carrying a dormant alias whose consumer sets "
            "now DIFFER -- `resolve_type('commentable')` answers 'searchable' at "
            "confidence 1.0 on a pair `merge_types` refuses non-overridably. The "
            "ELEVENTH trip"
        )
    return None


CONSUMER_PROBES = {
    "merge_types": _consumer_probe_merge,
    "retire": _consumer_probe_retire,
    "import_types": _consumer_probe_import,
    "reinstate": _consumer_probe_reinstate,
}


def check_consumer_sets() -> tuple[list[str], list[str], list[str]]:
    """Refusal #1, driven through every collapsing caller on every leg."""
    problems: list[str] = []
    lines: list[str] = []
    unreachable: list[str] = []
    for leg, build, knowable in _legs():
        for caller, probe in CONSUMER_PROBES.items():
            registry = build()
            try:
                failure = probe(registry)
            except Exception as exc:  # pragma: no cover - a probe that cannot run
                failure = f"the probe raised {type(exc).__name__}: {exc}"
            if failure is None:
                lines.append(f"  {leg:15s} {caller:13s} consumer sets differ  REFUSED")
            elif failure.startswith(_NOT_REACHABLE):
                lines.append(
                    f"  {leg:15s} {caller:13s} consumer sets differ  NOT REACHABLE"
                )
                unreachable.append(
                    f"{leg} / {caller} / consumer sets: {failure[len(_NOT_REACHABLE):]}"
                )
            else:
                lines.append(f"  {leg:15s} {caller:13s} consumer sets differ  FAILED")
                problems.append(f"{leg} / {caller} / consumer sets: {failure}")
    return problems, lines, unreachable


def check_forward_successor() -> tuple[list[str], list[str], list[str]]:
    problems: list[str] = []
    lines: list[str] = []
    unreachable: list[str] = []
    for leg, build, knowable in _legs():
        for label, later_kind, later_members in (
            ("successor arrives later", "predicate", ["bbb_memo"]),
            ("successor arrives, other kind", "entity", []),
        ):
            registry = build()
            _seed(registry, "commentable", kind="predicate", definition="a capability")
            _seed(registry, "aaa_note", predicates=["commentable"])
            retired = registry.retire(
                "commentable", "superseded by a word we have not registered yet",
                retired_by="user:sd", successor="searchable",
            )
            if isinstance(retired, Refusal):
                lines.append(f"  {leg:15s} {'retire':13s} {label:28s} REFUSED")
                continue
            _seed(registry, "searchable", kind=later_kind, definition="a capability")
            for member in later_members:
                _seed(registry, member, predicates=["searchable"])
            resolution = registry.resolve_type(
                "commentable", ResolveContext(), tier="unspecified"
            )
            if (
                resolution.type is not None
                and resolution.type.name == "searchable"
                and resolution.confidence == 1.0
            ):
                problems.append(
                    f"{leg} / retire / {label}: `retire('commentable', "
                    f"successor='searchable')` was ALLOWED because `searchable` did not "
                    f"exist yet, so guards #1, #2 and #3 had nothing to compare and none "
                    f"of them ran. The word was then created by an ordinary proposal, and "
                    f"`resolve_type('commentable')` now answers a "
                    f"{resolution.type.kind!r} at confidence 1.0 carrying "
                    f"{list(resolution.type.warnings)}. An identity guard that could not "
                    f"be EVALUATED has not said the collapse is safe -- Rule U, at the one "
                    f"call INTERFACE.md 5.3 calls a guarantee"
                )
                lines.append(f"  {leg:15s} {'retire':13s} {label:28s} FAILED")
            else:
                lines.append(f"  {leg:15s} {'retire':13s} {label:28s} guarded")
    return problems, lines, unreachable


# ---------------------------------------------------------------------------
# Part B, eighth axis -- THE ALIAS RE-POINT AT `retire(successor=)`. Ruling R75, row 6c.
#
# **Why an axis rather than a contract id alone.** Until row 6c `retire(successor=)`
# wrote no alias, and its guard nonetheless read `rec.aliases` as *"transferred"* -- the
# tenth trip's *one door disagreeing with itself*. R75 sent a DESIGN TEST at it instead
# of a patch, and the test found the guard's reading right and the write missing:
#
#   * an alias that ALSO has a row (what `merge_types` leaves behind) survives the
#     retirement through the SUCCESSOR CHAIN, and the `aliases` field plays no part;
#   * an alias with **no row**, or one naming a retired row that does not point back at
#     the holder, went from `existing / <holder> / 1.0` to `proposal / None / 0.36`
#     and `0.56` -- **on sqlite and on postgres, for entities and for predicates.**
#
# So `retire` now WRITES the transfer, which makes it a fourth writer of `aliases` --
# and this file's standing rule is that a writer of an identity field is judged and then
# DRIVEN. Part A judges it (it already prints `retire writes aliases,status,successor
# COLLAPSES`); this axis drives it, and asks the two questions Part A cannot:
#
#   1. does the word the retirement re-points still resolve to the successor at 1.0?
#      (the defect R75's design test found);
#   2. does the write happen ONLY where the identity guard passed? (the tenth trip's
#      own shape -- *the write a guard permits and the write a call performs must be
#      the same write*).

#: `(label, build the fixture, the word whose resolution is under test)`. Each builds a
#: `commentable` carrying one alias, in the two shapes the design test separated.
def _repoint_alias_only(registry: Registry) -> str | None:
    """An alias no row holds -- what `import_types` writes. Shape B."""
    _seed(registry, "taggable", kind="predicate", definition="a capability")
    _seed(registry, "commentable", kind="predicate", definition="a capability")
    _seed(registry, "aaa_note", predicates=["commentable", "taggable"])
    _seed(registry, "bbb_memo", predicates=["commentable", "taggable"])
    rows = registry.import_types(
        [
            {
                "name": "commentable",
                "status": "active",
                "aliases": ["zzz_widget_flag"],
                "definition": "a capability",
            }
        ],
        kind="predicate",
    )
    if not rows or "zzz_widget_flag" not in (rows[0].aliases or ()):
        return _NOT_REACHABLE + (
            "this backend did not keep the imported alias "
            f"({list(rows[0].warnings) if rows else 'no row'})"
        )
    return None


def _repoint_alias_names_a_retired_row(registry: Registry) -> str | None:
    """An alias naming a RETIRED row with no successor -- the kill row's FOURTH-trip
    shape, and the case the guard actually fires on. Shape B2."""
    _seed(registry, "taggable", kind="predicate", definition="a capability")
    _seed(registry, "commentable", kind="predicate", definition="a capability")
    _seed(registry, "searchable", kind="predicate", definition="a capability")
    _seed(registry, "aaa_note", predicates=["commentable", "taggable", "searchable"])
    _seed(registry, "bbb_memo", predicates=["commentable", "taggable", "searchable"])
    gone = registry.retire(
        "searchable", "no longer used", retired_by="user:sd", force=True
    )
    if isinstance(gone, Refusal):
        return _NOT_REACHABLE + f"this backend cannot retire a predicate ({gone.reason})"
    rows = registry.import_types(
        [
            {
                "name": "commentable",
                "status": "active",
                "aliases": ["searchable"],
                "definition": "a capability",
            }
        ],
        kind="predicate",
    )
    if not rows or "searchable" not in (rows[0].aliases or ()):
        return _NOT_REACHABLE + (
            "this backend did not keep the imported alias "
            f"({list(rows[0].warnings) if rows else 'no row'})"
        )
    return None


REPOINT_FIXTURES = {
    "alias-only": (_repoint_alias_only, "zzz_widget_flag"),
    "alias->retired row": (_repoint_alias_names_a_retired_row, "searchable"),
}


def _repoint_case(registry: Registry, word: str) -> tuple[str, str | None, str | None]:
    """Drive one retirement and judge it.

    ``(verdict, failure sentence or None, unreachable sentence or None)``.

    **Two questions, and they are separable on purpose.** (1) *Does the word the
    retirement re-points still resolve to the successor at 1.0?* -- the defect R75's
    design test found. (2) *Does the write happen ONLY where the identity guard passed?*
    -- the tenth trip's own shape, *the write a guard permits and the write a call
    performs must be the same write.*

    On a page-capped double the FIRST question cannot be posed at all, and the row says
    so rather than passing or failing: `_alias_map` reads the namespace's active rows to
    exhaustion, a capped backend truncates that scan, and the word therefore fails to
    resolve at 1.0 **before** the retirement as well as after. That is Rule U working --
    a truncated scan has not said the word is unheld -- not a regression, and calling it
    one would be this file's own recorded failure of printing `REFUSED` for a probe that
    never ran. **The second question is still asked there**, and it is the one that
    matters on a degraded read.
    """
    before = registry.resolve_type(word, ResolveContext(), tier="unspecified")
    posable = (
        before.type is not None
        and before.type.name == "commentable"
        and before.confidence == 1.0
    )
    retired = registry.retire(
        "commentable",
        "taggable says it better",
        retired_by="user:sd",
        successor="taggable",
        force=True,
    )
    survivor = registry.adapter.get_type("default", "taggable", kind="predicate")
    names = (survivor.aliases if survivor else ()) or ()
    if isinstance(retired, Refusal):
        # A refused retirement must leave NOTHING behind -- no tombstone and no alias.
        if word in names:
            return "FAILED", (
                f"the retirement was REFUSED ({retired.reason}) and the alias {word!r} "
                f"was written onto the successor anyway -- a write the guard did not "
                f"permit"
            ), None
        return "REFUSED, no write", None, None

    if word not in names:
        return "FAILED", (
            f"the retirement was ALLOWED and the alias {word!r} was not written onto "
            f"the successor, whose aliases are {list(names)} -- the guard on this call "
            f"reads `rec.aliases` as TRANSFERRED and this door performed no transfer. "
            f"**A door that guards a transfer it does not perform is the tenth trip's "
            f"one door disagreeing with itself** (ruling R75)"
        ), None

    if not posable:
        return "written; resolution NOT POSABLE", None, (
            f"`resolve_type({word!r})` answered "
            f"{getattr(before.type, 'name', None)!r} at {before.confidence} BEFORE the "
            f"retirement, so this backend cannot pose the resolution half: `_alias_map` "
            f"reads active rows to exhaustion and a capped page truncates that scan. "
            f"Rule U -- a truncated scan has not said the word is unheld. The WRITE half "
            f"is asked and passes"
        )

    after = registry.resolve_type(word, ResolveContext(), tier="unspecified")
    if not (
        after.type is not None
        and after.type.name == "taggable"
        and after.confidence == 1.0
    ):
        return "FAILED", (
            f"the alias was written and `resolve_type({word!r})` still answers "
            f"{getattr(after.type, 'name', None)!r} at {after.confidence}, where it "
            f"answered {getattr(before.type, 'name', None)!r} at {before.confidence} "
            f"the call before -- the write happened and the redirect did not"
        ), None
    return "re-pointed", None, None


def check_alias_repoint() -> tuple[list[str], list[str], list[str]]:
    """Ruling **R75**: the words a retirement re-points must still resolve, and the
    write must happen only where the guard passed.

    **The doubles run beside the real legs, and the fifth trip is why.** `partial` is an
    honest paging backend whose first page of two extents matches while the extents
    differ; `truncated` caps with no cursor, so there IS no rest to read and the only
    defence is the guards folding `_extent`'s own `why` into `knowable`. **A door that
    WRITES an alias on a truncated read is the fifth trip's shape with a write
    attached**, which is strictly worse than the fifth trip was -- so this axis asks the
    question on both doubles rather than on the real legs alone.
    """
    problems: list[str] = []
    lines: list[str] = []
    unreachable: list[str] = []
    for leg, build, knowable in _legs():
        shapes: list[tuple[str, Any]] = [("", None)]
        if knowable:
            shapes += [
                ("partial", lambda a: DegradedAdapter(a, page_cap=2, page_cursor=True)),
                ("truncated", lambda a: DegradedAdapter(a, page_cap=2)),
            ]
        for shape, wrap in shapes:
            for label, (fixture, word) in REPOINT_FIXTURES.items():
                row = f"{label} / {shape}" if shape else label
                registry = build()
                try:
                    blocked = fixture(registry)
                except Exception as exc:  # pragma: no cover - a probe that cannot run
                    blocked = _NOT_REACHABLE + (
                        f"the probe raised {type(exc).__name__}: {exc}"
                    )
                if blocked is not None:
                    lines.append(f"  {leg:15s} {'retire':13s} {row:32s} NOT REACHABLE")
                    unreachable.append(
                        f"{leg} / retire / {row}: {blocked[len(_NOT_REACHABLE):]}"
                    )
                    continue
                if wrap is not None:
                    # The fixture is built on the honest adapter and the RETIREMENT is
                    # driven through the degraded one, exactly as `check_states` does: a
                    # double that cannot build its own fixture poses no question at all.
                    registry = Registry(
                        wrap(registry.adapter),
                        policies={"default": NamespacePolicy(approval_policy="auto")},
                    )
                try:
                    verdict, failure, unposable = _repoint_case(registry, word)
                except Exception as exc:  # pragma: no cover
                    verdict, failure, unposable = "FAILED", (
                        f"the probe raised {type(exc).__name__}: {exc}"
                    ), None
                lines.append(f"  {leg:15s} {'retire':13s} {row:32s} {verdict}")
                if failure is not None:
                    problems.append(f"{leg} / retire / {row}: {failure}")
                if unposable is not None:
                    unreachable.append(f"{leg} / retire / {row}: {unposable}")
    return problems, lines, unreachable


# ---------------------------------------------------------------------------
# Part B, ninth axis -- THE SAME CALL, TWICE. The kill row's TWELFTH trip.
#
# **The trip.** `retire` read `.status` twice and both times on the SUCCESSOR, so it
# never asked whether the row it was retiring was ALREADY retired. Before ruling R75 a
# repeat retirement merely rewrote the tombstone; R75 attached an alias write to it, and
# a second retirement toward a different successor then copied the retired row's words
# onto a **second live row while the first still held them** -- two active entries
# answering to one word, which is `C16-06` and mechanism 4.
#
# **Why an axis and not only an id.** The checker exited 0 with this live, for the
# SEVENTH consecutive trip, and the reason is countable as it was for trip eleven: this
# file contained **zero** occurrences of a repeated call on one row. Every one of its
# `retire(`/`merge_types(`/`import_types(`/`reinstate(` fixtures opened its door exactly
# **once**. The eighth axis drives both alias shapes through `retire` on every leg and
# two doubles and still could not pose *"what if this door is opened twice?"*
#
# **The invariant this axis holds, and it is the one that closes the family:** *the write
# a call performs must be idempotent in the state the guard read.* A guard evaluated once
# for a call that can run twice is a permission cashed twice, and `rec.aliases` is not
# consumed by the write it authorises -- the tombstone keeps its words by design
# (INTERFACE.md 5.8) -- so nothing in the state stops the second cash.


def _one_word_holders_everywhere(registry: Registry) -> dict[str, list[str]]:
    """``{identity_key: [names of ACTIVE rows answering to it]}`` over the namespace.

    `C16-06`'s whole-store invariant, keyed the way the resolver keys a word (the
    seventh trip), and counting a row's NAME as well as its aliases (the eighth).
    """
    holders: dict[str, list[str]] = {}
    # **Every kind a collapsing caller can touch, and limiting this to two was a
    # BLOCKING of round 2.** `retire(successor=)` covers EDGE families by ruling R19 and
    # ACTION families by ACTIONS.md 2.1 -- a family *is* a `TypeEntry` -- and both carry
    # `aliases`. **[Observed, round 2, by mutation]** with the twelfth trip's guard
    # removed, `retire(alpha_edges -> beta_edges)` then `-> gamma_edges` left
    # `{'beta_edges': ('zeta',), 'gamma_edges': ('zeta',)}` -- `C16-06` verbatim -- and
    # this scan returned `{}`. The fixture worked and the DETECTOR was half-blind, which
    # is the eighth dress of *a checker only asks the questions its fixtures can pose*
    # wearing the other half: a checker only FINDS what its detector looks at.
    for kind in ("predicate", "entity", "edge", "action"):
        listing = registry.list_types(kind)
        for entry in listing.types:
            if entry.status != "active":
                continue
            for word in (entry.name, *(entry.aliases or ())):
                key = identity_key(word)
                if not key:
                    continue
                if entry.name not in holders.setdefault(key, []):
                    holders[key].append(entry.name)
    return holders


def _repeat_retire(registry: Registry) -> str | None:
    """`retire(alpha -> beta)` then `retire(alpha -> gamma)`. The twelfth trip."""
    for name in ("alpha", "beta", "gamma"):
        _seed(registry, name, kind="predicate", definition="one and the same thing")
    for member in ("aaa_note", "bbb_memo"):
        _seed(registry, member, predicates=["alpha", "beta", "gamma"])
    rows = registry.import_types(
        [{"name": "alpha", "status": "active", "aliases": ["zeta"],
          "definition": "one and the same thing"}],
        kind="predicate",
    )
    if not rows or "zeta" not in (rows[0].aliases or ()):
        return _NOT_REACHABLE + (
            "this backend did not keep the imported alias "
            f"({list(rows[0].warnings) if rows else 'no row'})"
        )
    first = registry.retire(
        "alpha", "superseded by beta", retired_by="user:sd", successor="beta", force=True
    )
    if isinstance(first, Refusal):
        return _NOT_REACHABLE + f"the first retirement is refused here ({first.reason})"
    registry.retire(
        "alpha", "actually gamma", retired_by="user:sd", successor="gamma", force=True
    )
    return None


def _repeat_merge(registry: Registry) -> str | None:
    """`merge_types(alpha -> beta)` twice. The absorbed row is retired by the first."""
    for name in ("alpha", "beta"):
        _seed(registry, name, kind="predicate", definition="one and the same thing")
    for member in ("aaa_note", "bbb_memo"):
        _seed(registry, member, predicates=["alpha", "beta"])
    first = registry.merge_types(
        "alpha", "beta", reason="one word for one meaning", merged_by="user:sd",
        acknowledge=list(ALL_ACKNOWLEDGEMENTS),
    )
    if isinstance(first, Refusal):
        return _NOT_REACHABLE + f"the first merge is refused here ({first.reason})"
    registry.merge_types(
        "alpha", "beta", reason="again", merged_by="user:sd",
        acknowledge=list(ALL_ACKNOWLEDGEMENTS),
    )
    return None


def _repeat_import(registry: Registry) -> str | None:
    """The same aliased row imported twice."""
    _seed(registry, "beta", kind="predicate", definition="one and the same thing")
    _seed(registry, "aaa_note", predicates=["beta"])
    row = {"name": "beta", "status": "active", "aliases": ["zeta"],
           "definition": "one and the same thing"}
    rows = registry.import_types([row], kind="predicate")
    if not rows or "zeta" not in (rows[0].aliases or ()):
        return _NOT_REACHABLE + (
            "this backend did not keep the imported alias "
            f"({list(rows[0].warnings) if rows else 'no row'})"
        )
    registry.import_types([row], kind="predicate")
    return None


def _repeat_reinstate(registry: Registry) -> str | None:
    """`reinstate` twice on one retired row."""
    _seed(registry, "alpha", kind="predicate", definition="one and the same thing")
    _seed(registry, "aaa_note", predicates=["alpha"])
    gone = registry.retire("alpha", "no longer used", retired_by="user:sd", force=True)
    if isinstance(gone, Refusal):
        return _NOT_REACHABLE + f"this backend cannot retire here ({gone.reason})"
    first = registry.reinstate("alpha", "we were wrong", reinstated_by="user:sd")
    if isinstance(first, Refusal):
        return _NOT_REACHABLE + f"the first reinstate is refused here ({first.reason})"
    registry.reinstate("alpha", "again", reinstated_by="user:sd")
    return None


def _repeat_retire_edge(registry: Registry) -> str | None:
    """The twelfth trip's shape on a `kind="edge"` FAMILY, not a predicate.

    **Widening the detector was not enough and this fixture is why** (round 2's
    BLOCKING, closed here). `retire(successor=)` covers edge families by ruling R19 and
    action families by ACTIONS.md 2.1 -- a family *is* a `TypeEntry` -- and both carry
    `aliases`. The detector now scans every kind; a detector that scans a kind no
    fixture ever writes is a detector that still cannot fail. *A checker only asks the
    questions its fixtures can pose* -- the eighth dress, and the answer is a fixture.

    No predicate extents here, so refusals #1 and #2 have nothing to fire on and the
    only thing standing between two ordinary retirements and two live rows on one word
    is the `rec.status` guard itself.
    """
    # A BARE `kind="edge"` entry, through the ordinary door. EDGES.md's rule is the one
    # ACTIONS.md inherits -- *a MISSING declaration is not a breach* -- so no attributes
    # are needed to make these rows, and reaching past `propose_type` to write one would
    # be the synthetic-record shape Part A refuses by name.
    for name in ("alpha_edges", "beta_edges", "gamma_edges"):
        _seed(registry, name, kind="edge", definition="one and the same relationship")
    rows = registry.import_types(
        [{"name": "alpha_edges", "status": "active", "aliases": ["zeta"],
          "definition": "one and the same relationship"}],
        kind="edge",
    )
    if not rows or "zeta" not in (rows[0].aliases or ()):
        return _NOT_REACHABLE + (
            "this backend did not keep the imported alias "
            f"({list(rows[0].warnings) if rows else 'no row'})"
        )
    first = registry.retire(
        "alpha_edges", "superseded by beta", retired_by="user:sd",
        successor="beta_edges", force=True,
    )
    if isinstance(first, Refusal):
        return _NOT_REACHABLE + f"the first retirement is refused here ({first.reason})"
    registry.retire(
        "alpha_edges", "actually gamma", retired_by="user:sd",
        successor="gamma_edges", force=True,
    )
    return None


REPEAT_PROBES = {
    "retire": _repeat_retire,
    "retire(edge)": _repeat_retire_edge,
    "merge_types": _repeat_merge,
    "import_types": _repeat_import,
    "reinstate": _repeat_reinstate,
}


def check_repeated_calls() -> tuple[list[str], list[str], list[str]]:
    """Every collapsing caller, opened TWICE, against `C16-06`'s whole-store invariant."""
    problems: list[str] = []
    lines: list[str] = []
    unreachable: list[str] = []
    for leg, build, knowable in _legs():
        # **The doubles run here too, and axis eight had them while this one did not**
        # (round 2). A door opened twice on a backend whose reads are capped is the
        # fifth trip's shape and the twelfth's at once; asking the question on the
        # honest legs alone is the gap this file keeps finding in itself.
        shapes: list[tuple[str, Any]] = [("", None)]
        if knowable:
            shapes += [
                ("partial", lambda a: DegradedAdapter(a, page_cap=2, page_cursor=True)),
                ("truncated", lambda a: DegradedAdapter(a, page_cap=2)),
            ]
        for shape, wrap in shapes:
          for caller, probe in REPEAT_PROBES.items():
            registry = build()
            row = f"{caller} / {shape}" if shape else caller
            try:
                blocked = probe(registry)
                if blocked is None and wrap is not None:
                    registry = Registry(
                        wrap(registry.adapter),
                        policies={"default": NamespacePolicy(approval_policy="auto")},
                    )
            except Exception as exc:  # pragma: no cover - a probe that cannot run
                blocked = _NOT_REACHABLE + f"the probe raised {type(exc).__name__}: {exc}"
            if blocked is not None:
                lines.append(f"  {leg:15s} {row:26s} called twice   NOT REACHABLE")
                unreachable.append(
                    f"{leg} / {row} / called twice: {blocked[len(_NOT_REACHABLE):]}"
                )
                continue
            shared = {
                word: names
                for word, names in _one_word_holders_everywhere(registry).items()
                if len(names) > 1
            }
            if shared:
                problems.append(
                    f"{leg} / {row} / called twice: opening this door a SECOND time "
                    f"left more than one ACTIVE row answering to a word -- {shared}. "
                    f"That is `C16-06`'s whole-store invariant and mechanism 4, and the "
                    f"guard on this call was evaluated ONCE for a call that ran twice. "
                    f"*The write a call performs must be idempotent in the state the "
                    f"guard read* -- the kill row's TWELFTH trip"
                )
                lines.append(f"  {leg:15s} {row:26s} called twice   FAILED")
            else:
                lines.append(f"  {leg:15s} {row:26s} called twice   one word, one row")
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

    # Part A2 -- row 6b. Printed with Part A because it is the same question one step on:
    # A asks whether a caller has been JUDGED, A2 asks whether a caller judged to collapse
    # actually reaches the guards.
    print()
    print(
        f"  and do the collapsing callers REACH `{SHARED_GUARD}`? "
        f"(ruling R53's extraction, made checkable):"
    )
    graph = _call_graph()
    for function, verdict in sorted(KNOWN_CALLERS.items()):
        if verdict.collapses:
            trail = _path_to(graph, function, SHARED_GUARD)
            mark = " -> ".join(trail[1:]) if trail else "DOES NOT REACH IT"
            print(f"    {function:22s} {mark}")
    caller_problems += check_shared_guard()

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

    for title, run in (
        (
            "  and the SPELLING axis -- the guard and the resolver must agree what a word IS:",
            check_spellings,
        ),
        (
            "  and ONE WORD, ONE LIVE IDENTITY -- C16-06's invariant, at every write door:",
            check_one_word,
        ),
        (
            "  and a SUCCESSOR THAT DOES NOT EXIST YET -- a guard with nothing to compare:",
            check_forward_successor,
        ),
        (
            "  and CONSUMER SETS -- refusal #1, which this checker could not fail on "
            "until row 6b's third round:",
            check_consumer_sets,
        ),
        (
            "  and the ALIAS RE-POINT -- ruling R75: a door that guards a transfer must "
            "perform it:",
            check_alias_repoint,
        ),
        (
            "  and THE SAME CALL, TWICE -- the kill row's twelfth trip: a guard "
            "evaluated once for a call that can run twice:",
            check_repeated_calls,
        ),
    ):
        print()
        print(title)
        axis_problems, axis_lines, axis_unreachable = run()
        for line in axis_lines:
            print(line)
        unreachable.extend(axis_unreachable)
        state_problems.extend(axis_problems)
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
    try:
        code = main()
    finally:
        # The verdict is printed either way; the schemas go either way too.
        _drop_postgres_schemas()
    raise SystemExit(code)
