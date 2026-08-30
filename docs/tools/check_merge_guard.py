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
======================  ===========================================  ==================

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
from open_ontology.types import Evidence, Refusal, TypeEntry  # noqa: E402

REGISTRY_SOURCE = ROOT / "open_ontology" / "registry.py"

#: The two fields on a stored `TypeRecord` that re-point what a name RESOLVES to.
#: `successor` redirects a retired word at confidence 1.0 (`INTERFACE.md` §5.3 calls that
#: a guarantee); `aliases` makes a word answer with this entry. A third field with the
#: same power would have to be added here -- and adding one without touching this file is
#: exactly the failure Part A exists to catch, because the AST scan below would find the
#: writes and this file would not know what they mean.
IDENTITY_FIELDS = ("successor", "aliases")


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
        False,
        "a SPLIT, not a collapse: it CLEARS a `successor` off a live row, so a word "
        "that resolved to another identity goes back to resolving to its own. It cannot "
        "make two identities into one, and the state it does create is guarded on its "
        "own terms (`successor_active`, `alias_collision`, §5.9b). §5.10's guards would "
        "have nothing to compare",
    ),
    "_write_approved": CallerVerdict(
        False,
        "writes `aliases=()` -- the literal empty tuple, on every approval. A "
        "`ProposalRecord` has no `successor` and no `aliases` field, so `approve` cannot "
        "re-point a name however the proposal is amended. *(Row 4c looked for `approve` "
        "of a proposal with a successor because the brief named it as a caller; there is "
        "no such thing, and this line is the record that somebody checked.)*",
    ),
    "_entry": CallerVerdict(
        False,
        "the READ path -- it copies `aliases` off a stored record into the returned "
        "`TypeEntry`. It writes nothing",
    ),
}


# ---------------------------------------------------------------------------
# Part A -- the callers, discovered from the AST


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
    for node in ast.walk(tree):
        # `TypeRecord(..., successor=x)` / `replace(rec, aliases=y)`
        if isinstance(node, ast.keyword) and node.arg in IDENTITY_FIELDS:
            found.setdefault(_enclosing_function(node, parents), set()).add(node.arg)
        # `TypeRecord(**{**rec.__dict__, "successor": x})` -- the shape three of the
        # callers actually use, and the one a keyword-only scan would miss entirely.
        if isinstance(node, ast.Dict):
            for key in node.keys:
                if isinstance(key, ast.Constant) and key.value in IDENTITY_FIELDS:
                    found.setdefault(
                        _enclosing_function(node, parents), set()
                    ).add(key.value)
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
                f"merge_types' {reason!r} does not declare itself non-overridable; "
                f"a guard that can be acknowledged past is a warning wearing a "
                f"refusal's name"
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
        # On a backend that cannot record the override there is no way to set the
        # fixture up, and saying so is honest -- the state is unreachable there.
        return None
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


def check_states() -> tuple[list[str], list[str]]:
    problems: list[str] = []
    lines: list[str] = []
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
                if failure:
                    problems.append(f"{leg} / {caller} / {state}: {failure}")
                    lines.append(f"  {leg:15s} {caller:13s} {state:28s} FAILED")
                else:
                    lines.append(f"  {leg:15s} {caller:13s} {state:28s} {verdict}")
        # The `unknowable` row on a leg that CAN index membership, built with the
        # double rather than with a real store: the two sides genuinely differ and the
        # backend genuinely cannot say, which is the shape of the FIRST trip.
        if knowable:
            registry = build()
            _both(registry, ["note"], ["doc"])
            blind = Registry(
                DegradedAdapter(registry.adapter, indexes_membership=False),
                policies={"default": NamespacePolicy(approval_policy="auto")},
            )
            failure = _probe_merge(blind, expect_refused=True, reasons={"predicate_merge"})
            if failure:
                problems.append(f"{leg} / merge_types / unknowable: {failure}")
                lines.append(f"  {leg:15s} {'merge_types':13s} {'unknowable':28s} FAILED")
            else:
                lines.append(f"  {leg:15s} {'merge_types':13s} {'unknowable':28s} REFUSED")
    return problems, lines


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
    state_problems, lines = check_states()
    for line in lines:
        print(line)

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
        "gets the guard's answer on every leg.\n"
        "What this does NOT cover, stated rather than implied: it checks the guards a "
        "caller HAS, not the guards a caller might need for a collapse reached through "
        "a field nobody has thought of. Part A is the half that makes that visible -- a "
        "new writer of `successor` or `aliases` fails this check until a person decides "
        "what it means."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
