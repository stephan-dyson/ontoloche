"""The fifth gate: a RATCHET on RESULT-CONDITIONED skips in the contract suite.

Row 6h's deliverable. The finding it exists to gate, in the brief's own words:

    A skip decided by the ENVIRONMENT is legitimate. A skip decided by the RESULT
    is never legitimate, because the result is the thing under test.

Three instances are known -- ``C3-14`` (row 4d, by mutation), ``C10-16`` (row 6f
round 1) and ``C3-26``, *written by row 6f in the very round whose finding ``F1``
was this exact shape*. All three were fixed one at a time. What no local edit
removes is the mechanism: **the suite treats a skip as coverage and cannot tell
the two kinds apart**, and the unaudited surface grows faster than the audited one
even while careful rows are watching (+8 bare skips against +2
``requires_capability`` markers in the two rows before this one).

WHY A RATCHET AND NOT A REPORTER OR A BLOCKER
---------------------------------------------
A checker that reports and exits 0 is the exact defect this row exists to kill --
it would read as coverage and assert nothing. A checker that blocks on every
pre-existing site forces exactly one outcome: someone weakens it until it passes.
So the gate carries a BASELINE of currently-flagged sites as data, and:

* it FAILS when a flagged site appears that the baseline does not hold;
* it FAILS when the baseline holds a site the checker no longer flags;
* it FAILS when the baseline's own ``count`` disagrees with its own ``sites``;
* and lowering the baseline is REFUSED when the site stopped being flagged because
  an assertion was DELETED rather than because the skip was repaired -- see
  ``_leaving_verdict``, which exists because a fresh lens found that removing
  coverage was the cheapest way to make this gate green.

Raising the baseline requires the supervisor's ruling. Lowering it does not.

THE DISCRIMINATOR
-----------------
Pre-registered in ``docs/runs/6H-RUN.md`` §0.3 as **D1**:

    A bare ``pytest.skip(...)`` is S2 (illegitimate) when the guard controlling it
    reads a name whose value is also read by an ``assert`` in the same test
    function. It is S1 when the guard reads a call result no assert ever reads.
    It is S0 when the guard reads no call result at all.

**D1 is implemented over OBSERVATION ROOTS rather than over names**, which is the
one change that makes it survive contact with real tests. A name assigned from a
call to the system under test IS an observation and is its own root. A name
derived from another WITHOUT a fresh call -- ``warnings = rows[0].warnings or ()``,
``refused = isinstance(out, Refusal)``, ``why, detail = out.reason, out.detail`` --
inherits the root of what it was derived from. Calls to builtins are derivations,
not observations. So a guard and an assertion that reach the same observation by
different names are still reading the same thing, and one hop of indirection no
longer defeats the comparison.

**The RECEIVER rule, and the false step it corrects.** ``registry =
make_registry(adapter)`` is an assignment from a call, so a naive reading makes
``registry`` an observation and flags the canonical *legitimate* guard ``if not
registry.caps.indexes_membership``. The object a test drives the system THROUGH is
configuration, not a result -- but "any name you call a method on" was too wide,
and a fresh lens proved it: one extra ``assert unscored.outcome.startswith(...)``
turned the gate's own pinned ``C3-26`` case from S2 into S0. **Adding an assertion
un-flagged the defect.** So a receiver is now specifically a name whose method call
PRODUCES AN ASSIGNED VALUE -- the driving object -- and an incidental ``.strip()``
inside an assertion no longer launders a result into configuration.

THE CATEGORIES, and the fourth one the brief's model did not have
----------------------------------------------------------------
::

    S0  ENVIRONMENT       guard reads no observation             legitimate
    S1  SETUP RESULT      reads an observation no assert reaches probably legitimate; NOT ruled here
    S2  RESULT UNDER TEST reads an observation an assert reaches never legitimate   <-- GATED
    S3  UNCONDITIONAL     no enclosing conditional at all        reported, not gated
    S4  UNDECIDABLE       this checker cannot see enough to say  reported, never gated
    S5  PROVEN            reads the result under test, then ASSERTS THE CAPABILITY
                          that explains it before skipping

**S5 is the suite's own invention, not this checker's.** It is documented inside
the tests in their own words -- *"Gated on the CAPABILITY rather than on the
outcome, so a store that CAN hold the alias and merged anyway is a finding and not
a skip"* -- and there are seven. Break the implementation on a capable backend and
the assertion fails, so the id FAILS rather than skips. That is precisely the
repair of ``C3-26``'s defect, applied by the suite before this row existed, and a
gate that flagged it would delete the correct pattern along with the wrong one.

**S4 is an honest refusal to answer, and it is never gated**, because gating a cell
the checker cannot see into is how a gate acquires false positives nobody can
audit. It holds: guards that call inline and bind no name; guards on a HELPER's
parameter, where the value arrives from a caller this checker does not follow; and
guards that are not ``if`` statements at all.

Only S2 is gated. Gating S1, S4 or S5 would rule on questions row 6h is explicitly
not authorised to rule on.

USAGE
-----
::

    py docs/tools/check_skip_census.py                   # the gate. exit 0 or 1
    py docs/tools/check_skip_census.py --census          # full breakdown, exit 0
    py docs/tools/check_skip_census.py --selftest        # classifier calibration only
    py docs/tools/check_skip_census.py --write-baseline  # LOWER (or seed) the baseline

The gate runs ``--selftest`` on every invocation and fails if the classifier
regressed, because a gate whose own classifier is untested is the exact defect this
row exists to name.
"""

from __future__ import annotations

import argparse
import ast
import collections
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACT_DIR = REPO_ROOT / "ontoloche" / "contract"
# The async tree is MOSTLY generated from the sync one by tools/unasync.py, but
# NOT entirely: `conftest.py` and `test_c0_backend_local.py` are hand-written
# there and carry skips of their own (unasync.py's HAND_WRITTEN_ASYNC names the
# second, and the first has no generated banner). A gate that scanned only the
# sync tree left those two files permanently unwatched, which a fresh lens found
# and demonstrated. So both trees are scanned and generated files are skipped by
# their own banner -- gating a derivative would only double-count the source.
AIO_CONTRACT_DIR = REPO_ROOT / "ontoloche" / "aio" / "contract"
SCAN_DIRS = (CONTRACT_DIR, AIO_CONTRACT_DIR)
GENERATED_BANNER = "GENERATED FILE -- do not edit"
BASELINE_PATH = Path(__file__).resolve().parent / "skip_census_baseline.json"

# Calls that DERIVE a value rather than OBSERVE the system. A name assigned from
# `isinstance(out, Refusal)` still holds a fact about `out`; a name assigned from
# `registry.merge_types(...)` holds a new observation of its own.
PURE_CALLS = frozenset(
    {
        "isinstance", "len", "set", "list", "tuple", "dict", "any", "all",
        "sorted", "str", "int", "float", "bool", "getattr", "hasattr", "abs",
        "max", "min", "sum", "type", "repr", "frozenset", "next", "iter",
        "enumerate", "zip", "reversed", "round", "id", "format", "divmod",
    }
)

# Attribute names that make an assertion a CAPABILITY proof rather than any old
# assertion. S5 turns on this: the suite's proven-environmental skips all assert
# `x.caps.<flag>` or `x.capabilities().<flag>`, and without this the pattern is
# launderable by asserting something trivially true before skipping.
CAPABILITY_MARKERS = frozenset({"caps", "capabilities"})

ENV = "S0-ENVIRONMENT"
SETUP = "S1-SETUP-RESULT"
UNDER_TEST = "S2-RESULT-UNDER-TEST"
UNCONDITIONAL = "S3-UNCONDITIONAL"
UNDECIDABLE = "S4-UNDECIDABLE"
PROVEN_ENV = "S5-PROVEN-ENVIRONMENTAL"

CATEGORIES = (ENV, SETUP, UNDER_TEST, UNCONDITIONAL, UNDECIDABLE, PROVEN_ENV)


class Site:
    """One skip call site, and what this gate decided about it.

    Identity is ``(file, function, ordinal)`` and deliberately NOT the line number:
    line numbers churn on every edit above them, so a line-keyed baseline would
    fail the gate on unrelated commits, and a gate that fails for unrelated reasons
    is a gate somebody weakens.
    """

    __slots__ = (
        "file", "func", "ordinal", "line", "category", "guard", "why", "asserts",
    )

    def __init__(self, file, func, ordinal, line, category, guard, why, asserts=0):
        self.file = file
        self.func = func
        self.ordinal = ordinal
        self.line = line
        self.category = category
        self.guard = guard
        self.why = why
        # How many assertions the enclosing function holds. Carried into the
        # baseline because the cheapest way to make this gate green is to DELETE
        # the assertion that made a site illegitimate. See _leaving_verdict.
        self.asserts = asserts

    @property
    def ident(self) -> str:
        return f"{self.file}::{self.func}#{self.ordinal}"

    def __repr__(self) -> str:  # pragma: no cover - diagnostics only
        return f"<Site {self.ident} {self.category}>"


# --------------------------------------------------------------------------
# finding the skips
# --------------------------------------------------------------------------

def _pytest_aliases(tree: ast.AST) -> tuple[set[str], set[str]]:
    """``(module aliases for pytest, bare names bound to pytest.skip)``.

    Both `import pytest as p` and `from pytest import skip as bail` hide a skip
    from a checker that hardcodes the spelling, and a fresh lens found both.
    """
    modules = {"pytest"}
    bare: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                if a.name == "pytest":
                    modules.add(a.asname or a.name)
        elif isinstance(node, ast.ImportFrom) and node.module == "pytest":
            for a in node.names:
                if a.name in ("skip", "xfail"):
                    bare.add(a.asname or a.name)
    for node in ast.walk(tree):
        # module-level `_bail = pytest.skip`
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Attribute):
            if node.value.attr in ("skip", "xfail"):
                base = node.value.value
                if isinstance(base, ast.Name) and base.id in modules:
                    for t in node.targets:
                        if isinstance(t, ast.Name):
                            bare.add(t.id)
    return modules, bare


def _is_skip_call(node, modules: set[str], bare: set[str]) -> bool:
    """``pytest.skip(...)``, ``p.xfail(...)``, an alias, or
    ``raise pytest.skip.Exception(...)``."""
    if not isinstance(node, ast.Call):
        return False
    f = node.func
    if isinstance(f, ast.Name):
        return f.id in bare
    if isinstance(f, ast.Attribute):
        if f.attr in ("skip", "xfail"):
            return isinstance(f.value, ast.Name) and f.value.id in modules
        # raise pytest.skip.Exception(...)
        if f.attr == "Exception" and isinstance(f.value, ast.Attribute):
            inner = f.value
            if inner.attr in ("skip", "xfail"):
                return isinstance(inner.value, ast.Name) and inner.value.id in modules
    return False


# --------------------------------------------------------------------------
# observation roots -- the heart of D1
# --------------------------------------------------------------------------

def _names_read(node) -> set[str]:
    return {
        n.id
        for n in ast.walk(node)
        if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)
    }


def _assign_targets(node) -> list[str]:
    """The NAMES this assignment binds.

    An ATTRIBUTE target is deliberately not one of them. ``adapter._migration_sql =
    lambda: broken`` binds nothing called ``adapter`` -- it pokes a field on an
    object the test was handed -- and treating it as a binding sent observation
    roots BACKWARDS onto the fixture, which then flowed onto every later name read
    off that fixture and flagged an ordinary environment guard. A subscript target
    IS included: ``seen["u"] = call()`` really does put an observation in ``seen``.
    """
    if isinstance(node, ast.Assign):
        raw = list(node.targets)
    elif isinstance(node, (ast.AnnAssign, ast.AugAssign, ast.NamedExpr)):
        raw = [node.target]
    else:
        return []

    out: list[str] = []

    def walk(t):
        if isinstance(t, ast.Name):
            out.append(t.id)
        elif isinstance(t, (ast.Tuple, ast.List)):
            for e in t.elts:
                walk(e)
        elif isinstance(t, ast.Starred):
            walk(t.value)
        elif isinstance(t, ast.Subscript):
            walk(t.value)
        # ast.Attribute: deliberately nothing.

    for t in raw:
        walk(t)
    return out


def _capability_reads(expr) -> set[str]:
    """Names this expression reads ONLY as a source of CAPABILITY facts.

    ``registry.caps.stores_events`` and ``adapter.capabilities().owns_schema`` are
    reads of the CONFIGURATION, whoever owns the object. Without this, narrowing
    the receiver rule (which had to be narrowed -- an extra assertion was
    un-flagging real defects) flagged three canonical environment guards, because
    the object carrying ``.caps`` had itself come back from a call.
    """
    out: set[str] = set()
    for n in ast.walk(expr):
        marker = None
        if isinstance(n, ast.Attribute) and n.attr in CAPABILITY_MARKERS:
            marker = n.value
        elif (
            isinstance(n, ast.Call)
            and isinstance(n.func, ast.Attribute)
            and n.func.attr in CAPABILITY_MARKERS
        ):
            marker = n.func.value
        if marker is None:
            continue
        while isinstance(marker, (ast.Attribute, ast.Subscript)):
            marker = marker.value
        if isinstance(marker, ast.Name):
            out.add(marker.id)
    return out


def _capability_derived(func: ast.AST) -> set[str]:
    """Names bound from a capability read -- ``caps = adapter.capabilities()``."""
    out: set[str] = set()
    for node in ast.walk(func):
        if isinstance(node, (ast.Assign, ast.AnnAssign, ast.NamedExpr)):
            value = getattr(node, "value", None)
            if value is not None and _capability_reads(value):
                out.update(_assign_targets(node))
    return out


def _observes(value: ast.AST) -> bool:
    """Does this expression CALL the system, as opposed to deriving from a value?"""
    for n in ast.walk(value):
        if not isinstance(n, ast.Call):
            continue
        f = n.func
        if isinstance(f, ast.Name) and f.id in PURE_CALLS:
            continue
        return True
    return False


def _roots(func: ast.AST) -> dict[str, set[str]]:
    """name -> the set of OBSERVATIONS its value stands for.

    A name assigned from a call to the system is its own root. A name derived
    without a fresh call inherits the roots of what it was derived from, so a
    guard on ``seen["reason"]`` and an assert on ``out`` meet at ``out``.
    """
    roots: dict[str, set[str]] = {}
    derived: list[tuple[list[str], set[str]]] = []

    for node in ast.walk(func):
        if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign, ast.NamedExpr)):
            value = getattr(node, "value", None)
            if value is None:
                continue
            targets = _assign_targets(node)
            if _observes(value):
                for t in targets:
                    roots.setdefault(t, set()).add(t)
            else:
                derived.append((targets, _names_read(value)))
        elif isinstance(node, ast.withitem):
            if node.optional_vars is not None and _observes(node.context_expr):
                for s in ast.walk(node.optional_vars):
                    if isinstance(s, ast.Name):
                        roots.setdefault(s.id, set()).add(s.id)

    changed = True
    while changed:
        changed = False
        for targets, reads in derived:
            inherited: set[str] = set()
            for r in reads:
                inherited |= roots.get(r, set())
            if not inherited:
                continue
            for t in targets:
                before = len(roots.get(t, set()))
                roots.setdefault(t, set()).update(inherited)
                if len(roots[t]) != before:
                    changed = True
    return roots


def _driving_receivers(func: ast.AST) -> set[str]:
    """Names whose method calls PRODUCE an assigned value: the objects a test
    drives the system through.

    Narrow on purpose. "Any name you call a method on" was the first cut, and it
    let one extra ``assert result.field.startswith(...)`` launder a result into
    configuration and un-flag a real defect.
    """
    out: set[str] = set()

    def bases_of_producing_calls(value):
        for n in ast.walk(value):
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute):
                base = n.func.value
                while isinstance(base, (ast.Attribute, ast.Subscript)):
                    base = base.value
                if isinstance(base, ast.Name):
                    out.add(base.id)

    for node in ast.walk(func):
        if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign, ast.NamedExpr)):
            if getattr(node, "value", None) is not None:
                bases_of_producing_calls(node.value)
        elif isinstance(node, ast.withitem):
            if node.optional_vars is not None:
                bases_of_producing_calls(node.context_expr)
    return out


def _locally_bound(func: ast.AST) -> set[str]:
    """Comprehension and for-loop targets -- ``w`` in ``any(w.startswith(...) ...)``."""
    out: set[str] = set()
    for node in ast.walk(func):
        target = None
        if isinstance(node, ast.comprehension):
            target = node.target
        elif isinstance(node, (ast.For, ast.AsyncFor)):
            target = node.target
        if target is not None:
            for s in ast.walk(target):
                if isinstance(s, ast.Name):
                    out.add(s.id)
    return out


def _assertion_nodes(func: ast.AST) -> list[ast.AST]:
    """Every construct that ASSERTS something.

    A bare ``assert`` is not the only one. ``with pytest.raises(...)`` is an
    assertion about a call, and a test whose only check is a raises-block was
    scoring as "no assert reads this" -- inverting D1's premise silently.
    """
    out: list[ast.AST] = []
    for node in ast.walk(func):
        if isinstance(node, ast.Assert):
            out.append(node)
        elif isinstance(node, (ast.With, ast.AsyncWith)):
            for item in node.items:
                call = item.context_expr
                if isinstance(call, ast.Call) and isinstance(call.func, ast.Attribute):
                    if call.func.attr in ("raises", "warns", "deprecated_call"):
                        out.append(node)
                        break
    return out


# --------------------------------------------------------------------------
# guards
# --------------------------------------------------------------------------

def _guard_chain(func: ast.AST, skip_node: ast.AST):
    """``([(test, taken)], innermost if-node, shape)``.

    ``taken`` is False when the skip is reached through the ``else``, so the
    condition that actually holds there is ``not test``. **Dropping that was a
    hole a fresh lens walked straight through**: with polarity discarded, an
    ``if not isinstance(gone, Refusal): ... else: <skip>`` handed the else-branch
    the exemption earned by the ``if``, on the one branch where the value IS a
    refusal and its reason DOES exist. That is F12 again, inside the fix for F12.

    ``shape`` is "if" when every enclosing conditional is an ``if``, "other" when
    the skip sits under a ``while``, an ``except``, a ``match`` arm or a boolean
    short-circuit, and "" when nothing guards it. The distinction matters: a skip
    in an ``except`` handler for the exception the test exists to catch is exactly
    this row's defect, and calling it "unconditional" hides it.
    """
    found: dict = {}

    def visit(node, active, inner, shape):
        if found:
            return
        if node is skip_node:
            found.update(chain=list(active), inner=inner, shape=shape)
            return
        if isinstance(node, ast.If):
            if any(n is skip_node for n in ast.walk(node.test)):
                found.update(chain=list(active), inner=inner, shape=shape or "other")
                return
            for stmt in node.body:
                visit(stmt, active + [(node.test, True)], node, shape or "if")
            for stmt in node.orelse:
                visit(stmt, active + [(node.test, False)], node, shape or "if")
            return
        # A LOOP'S `else` IS UNDECIDABLE; ITS BODY IS NOT. `for ... else: <skip>`
        # runs only when the loop completed without `break`, which is a condition
        # this checker cannot read -- it was landing in S3-UNCONDITIONAL with the
        # sentence "no enclosing conditional", an UNGATED cell and a false
        # sentence. But a skip inside the loop BODY is governed by its own `if`
        # and must keep that reading: the first cut of this fix put the whole
        # loop in "other" and dropped THIS ROW'S OWN REPAIR at
        # `test_c10_merge_types.py:1297` from S5 to S4, because `test_c10_23`
        # runs its fixture inside `for i, order in enumerate(...)`. Measured, not
        # noticed later.
        if isinstance(node, (ast.For, ast.AsyncFor)):
            for stmt in node.body:
                visit(stmt, active, inner, shape)
            for stmt in node.orelse:
                visit(stmt, active, inner, "other")
            return
        if isinstance(node, (ast.While, ast.Try, ast.Match, ast.BoolOp)):
            for child in ast.iter_child_nodes(node):
                visit(child, active, inner, "other")
            return
        for child in ast.iter_child_nodes(node):
            visit(child, active, inner, shape)

    for stmt in getattr(func, "body", []):
        visit(stmt, [], None, "")
        if found:
            break
    return found.get("chain", []), found.get("inner"), found.get("shape", "")


def _guard_inline_calls(chain, driving: set[str], local: set[str]) -> set[str]:
    """Calls made from inside the guard itself, binding no name."""
    out: set[str] = set()
    for t in chain:
        # A walrus binds the call's result to a name, so `if (out :=
        # registry.merge_types(...)).reason == "x":` is NOT "binding no name".
        # It was landing in S4 with that sentence printed about it -- an ungated
        # escape, and false of the guard it quoted.
        walrus_bound = {id(n.value) for n in ast.walk(t) if isinstance(n, ast.NamedExpr)}
        for n in ast.walk(t):
            if not isinstance(n, ast.Call):
                continue
            if id(n) in walrus_bound:
                continue
            f = n.func
            if isinstance(f, ast.Name):
                if f.id not in PURE_CALLS:
                    out.add(f.id + "()")
            elif isinstance(f, ast.Attribute):
                base = f.value
                while isinstance(base, (ast.Attribute, ast.Subscript)):
                    base = base.value
                if isinstance(base, ast.Name) and base.id not in local:
                    out.add(f"{base.id}.{f.attr}()")
    return out


# --------------------------------------------------------------------------
# THE S5 PROOF, AS AN AXIS -- `6I-RUN.md` §7's three independent parts.
#
#   what is asserted    is the capability asserted in the sense that FAILS on a
#                       backend that HAS it?             F4: `... is True`
#   when it is reached  does the guard narrow to a reason, or establish that
#                       there is no reason to narrow?    F12: guard never read
#   whether it can fail is the assertion's own expression defeatable?
#                                                        F15: `assert True or X`
#
# EACH IS A RULE ABOUT THE SHAPE, not a list of the cases that produced it. A set
# built from three remembered names will not catch the fourth nobody has thought
# of, and `_capability_proof` used to check exactly one of the three.
#
# Parts 1 and 3 are ONE recursive predicate, `_falsifying`, and that is not a
# shortcut: "can this expression fail whenever the capability is present" is the
# question both of them ask. `assert caps.f is True` cannot fail on a capable
# backend and neither can `assert True or caps.f`; the same walk refuses both.
#
# EVERY AMBIGUITY RESOLVES TOWARD S2. S5 is the UNGATED cell, so a checker unsure
# whether a proof is real must not grant the promotion. Failing toward the gated
# cell costs a conversation. Failing toward the ungated one is F12.
# --------------------------------------------------------------------------

NARROWING_METHODS = frozenset({"startswith", "endswith"})

# The type whose complement is ONE outcome. `not isinstance(x, Refusal)` says the
# call did not refuse, and there is no `.reason` on that branch to compare -- which
# is the whole argument for the exemption. `not isinstance(x, Success)` says the
# opposite: it names the refusal FAMILY, where the reason exists and matters. A
# lens got the exemption with `Success`, and with `str`, because the type was never
# examined at all. Declared here, next to CAPABILITY_MARKERS, because the file
# already carries its domain knowledge as reviewable constants rather than as
# guesses in a walk -- and NEVER as a named test, which would stop applying the
# moment anyone renamed one.
FAMILY_TYPES = frozenset({"Refusal"})


def _mentions_capability(node, cap_derived: set[str] = frozenset()) -> bool:
    """Does this tree mention a capability AT ALL -- spelled out, or via a bound name?

    `cap_derived` matters and its absence was a live defect: a site writing the
    suite's own `caps = adapter.capabilities()` then `assert caps.stores_events is
    False` was refused with *"no assertion in the skip's own branch reads a
    capability"*, which is FALSE of that block. The gate refused a correct proof
    AND printed a false reason for refusing it -- F15 pointed the other way, in
    the row that closed F15. `test_c15_09` in the calibration set writes exactly
    that shape.

    Deliberately loose, and used only to decide whether a site was TRYING to prove
    a capability -- which is what the `why` text needs in order to say something
    useful about a near miss. It is NOT what grants S5; `_capability_expr` is.
    """
    return any(
        (isinstance(n, ast.Attribute) and n.attr in CAPABILITY_MARKERS)
        or (isinstance(n, ast.Name) and n.id in cap_derived)
        for n in ast.walk(node)
    )


def _capability_expr(node, cap_derived: set[str], observations: set[str]) -> bool:
    """Is this expression ITSELF a capability read, rather than one that mentions one?

    The distinction is the whole of a lens's MAJOR: `_falsifying` used to ask only
    whether a capability appeared somewhere inside the compared side, so
    `(registry.caps.stores_events and False) is False` -- constantly true, F15's
    own property -- and `explains(registry.caps, gone) is False` -- opaque, with
    the result under test passed in as an argument -- both bought S5.

    Accepted: `<base>.<flag>` where `<base>` is `x.caps`, `x.capabilities()`, or a
    name bound from one (`caps = adapter.capabilities()`), and the owning name is
    NOT itself the result under test. Everything else is refused, toward S2.
    """
    if not isinstance(node, ast.Attribute):
        return False
    base = node.value
    if isinstance(base, ast.Call):
        base = base.func
    if isinstance(base, ast.Attribute) and base.attr in CAPABILITY_MARKERS:
        owner = base.value
        while isinstance(owner, (ast.Attribute, ast.Subscript)):
            owner = owner.value
        # `gone.caps.stores_events`, where `gone` is the result under test, is not a
        # fact about the environment however it is spelled.
        return not (isinstance(owner, ast.Name) and owner.id in observations)
    if isinstance(base, ast.Name):
        return base.id in cap_derived
    return False


def _falsifying(node, cap_derived: set[str], observations: set[str]) -> bool:
    """Does this expression FAIL on a backend that HAS the capability?

    Parts 1 and 3 of the axis, in one walk. `caps.f is False` and `not caps.f`
    fail on a capable backend; `caps.f is True` does not, and that is F4's
    exploit -- inverted, trivially true on every real backend. `and` needs ONE
    falsifying operand because either operand can fail the whole; `or` needs
    BOTH, because a single non-falsifying operand carries it -- which is F15's
    `assert True or registry.caps.stores_events` and every rewording of it.
    """
    if isinstance(node, ast.BoolOp):
        parts = [_falsifying(v, cap_derived, observations) for v in node.values]
        return any(parts) if isinstance(node.op, ast.And) else all(parts)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
        return _capability_expr(node.operand, cap_derived, observations)
    if isinstance(node, ast.Compare):
        if len(node.ops) != 1 or not isinstance(node.ops[0], (ast.Is, ast.Eq)):
            return False
        left, right = node.left, node.comparators[0]
        return (
            _capability_expr(left, cap_derived, observations)
            and _is_false_constant(right)
        ) or (
            _capability_expr(right, cap_derived, observations)
            and _is_false_constant(left)
        )
    return False


def _is_false_constant(node) -> bool:
    return isinstance(node, ast.Constant) and node.value is False


def _string_constant(node) -> bool:
    """A string literal, or a tuple/list/set of them -- `x.reason in ("a", "b")`."""
    if isinstance(node, ast.Constant):
        return isinstance(node.value, (str, bytes))
    if isinstance(node, (ast.Tuple, ast.List, ast.Set)):
        return bool(node.elts) and all(_string_constant(e) for e in node.elts)
    return False


def _flatten_and(test) -> list:
    if isinstance(test, ast.BoolOp) and isinstance(test.op, ast.And):
        out: list = []
        for value in test.values:
            out.extend(_flatten_and(value))
        return out
    return [test]


def _positive_naming(test, observations: set[str], positive: bool = True) -> bool:
    """Does this test NAME the outcome the capability is claimed to explain?

    A POSITIVE naming only, and the polarity is the point. `x.reason ==
    "cannot_record_override"` pins the branch to one reason. Its COMPLEMENT pins
    nothing, and a lens proved it with four shapes the first cut accepted:
    `x.reason != "alias_collision"`, `x.reason not in (...)`, `"overridable" in
    x.detail`, and `x.reason != ""`. Each admits every outcome but one -- F12's
    own sentence, *true of twelve refusals where the capability explains one*,
    with the quantifier flipped.

    NUMERIC constants never name a reason: `len(x.warnings) > 0` is a threshold,
    and admitting it sells the promotion for a `0`. An ENUM-valued reason is
    refused too. Both are the fail-closed direction -- a conversation rather than
    a silent promotion.
    """
    if isinstance(test, ast.UnaryOp) and isinstance(test.op, ast.Not):
        return _positive_naming(test.operand, observations, not positive)
    if isinstance(test, ast.BoolOp):
        parts = [_positive_naming(v, observations, positive) for v in test.values]
        # At positive polarity `A and B` is pinned by either conjunct while `A or
        # B` needs both, since one unnamed branch leaves the outcome free. Under a
        # negation De Morgan swaps which is which.
        return any(parts) if isinstance(test.op, ast.And) == positive else all(parts)
    if not positive:
        return False
    if isinstance(test, ast.Compare):
        if len(test.ops) != 1:
            return False
        op, left, right = test.ops[0], test.left, test.comparators[0]
        if isinstance(op, (ast.Eq, ast.Is)):
            return (_string_constant(right) and bool(_names_read(left) & observations)) or (
                _string_constant(left) and bool(_names_read(right) & observations)
            )
        if isinstance(op, ast.In):
            # `x.reason in ("a", "b")` names a closed set. `"key" in x.detail`
            # does not -- it names a KEY that any number of refusals may carry,
            # which is why the observation must be on the LEFT.
            return _string_constant(right) and bool(_names_read(left) & observations)
        return False
    if (
        isinstance(test, ast.Call)
        and isinstance(test.func, ast.Attribute)
        and test.func.attr in NARROWING_METHODS
        and any(_string_constant(a) for a in test.args)
    ):
        # A prefix names one marker -- but only over the OBSERVATION. Without that
        # check a lens laundered a bare `isinstance(gone, Refusal)` with `not
        # adapter.dsn.startswith("postgres://")`, which narrows nothing about
        # `gone`, while the `why` said "narrows on a literal outcome".
        return bool(_names_read(test) & observations)
    if (
        isinstance(test, ast.Call)
        and isinstance(test.func, ast.Name)
        and test.func.id in {"any", "all"}
        and len(test.args) == 1
        and isinstance(test.args[0], (ast.GeneratorExp, ast.ListComp, ast.SetComp))
    ):
        comp = test.args[0]
        if not any(bool(_names_read(g.iter) & observations) for g in comp.generators):
            return False
        # THE TARGET CARRIES THE OBSERVATION. `w` in `for w in warnings` has no
        # root of its own, so without this the element expression reads nothing
        # observed and `any(w.startswith("import_refused:") for w in warnings)`
        # named no outcome -- while the gate printed "without naming WHICH
        # outcome" about a guard that names one. The same prefix written
        # `out.reason.startswith(...)` was accepted, so the refusal was
        # inconsistent rather than conservative.
        bound = set(observations)
        for g in comp.generators:
            bound |= {t.id for t in ast.walk(g.target) if isinstance(t, ast.Name)}
        return _positive_naming(comp.elt, bound, positive)
    return False


def _establishes_not_that_type(test, observations: set[str]) -> bool:
    """`not isinstance(x, T)` over an observation -- the value is NOT a `T`.

    THE ONE EXEMPTION from the narrowing requirement, and it is a rule about the
    SHAPE rather than about a site: hard-coding a test name into the instrument
    stops applying the moment anyone renames the test.

    On this branch the value is not a `Refusal`, so `x.reason` DOES NOT EXIST. A
    rule demanding a reason comparison here demands an attribute reference that
    would raise, and **a requirement no correct site can meet is a defect in the
    checker, not a rule.** The proof is complete by another route: a backend that
    CAN do the thing and did it anyway fails the capability assertion.

    Narrowed to the TYPE test on purpose. `not x.ok` is NOT exempt -- `x.reason`
    is right there to compare against, so the requirement CAN be met, and a
    negated truthiness test admits a family exactly as a positive one does.
    Otherwise "invert your guard and the reason requirement disappears" would be
    true by accident, which is F12's shape wearing a different hat.
    """
    if not (isinstance(test, ast.UnaryOp) and isinstance(test.op, ast.Not)):
        return False
    call = test.operand
    if not (
        isinstance(call, ast.Call)
        and isinstance(call.func, ast.Name)
        and call.func.id == "isinstance"
        and len(call.args) == 2
        and bool(_names_read(call.args[0]) & observations)
    ):
        return False
    # THE TYPE IS THE ARGUMENT, and the first cut never looked at it -- a lens got
    # the exemption with `not isinstance(gone, Success)`, which IS the refusal
    # family, and again with `not isinstance(gone, str)`, which is true on every
    # branch. Only the complement of a FAMILY_TYPES type carries the argument.
    kind = call.args[1]
    return isinstance(kind, ast.Name) and kind.id in FAMILY_TYPES


def _guard_narrows(pairs, observations: set[str]) -> str:
    """How the guard narrows, or "" if it does not. Part 2 of the axis.

    F12 in one sentence: `isinstance(gone, Refusal)` is true of TWELVE different
    refusals in `retire` and the capability explains ONE, so a capability
    assertion under it fires on eleven cases it does not cover.
    """
    effective = []
    for test, taken in pairs:
        if taken:
            effective.extend(_flatten_and(test))
        else:
            # On the else-branch the condition that holds is `not test`, and
            # `not (A and B)` guarantees nothing about A or B separately, so it is
            # carried whole rather than split.
            effective.append(ast.UnaryOp(op=ast.Not(), operand=test))
    if any(_positive_naming(s, observations) for s in effective):
        return "narrows on a literal outcome"
    exempt = [s for s in effective if _establishes_not_that_type(s, observations)]
    family = [
        s
        for s in effective
        if _names_read(s) & observations
        and not _establishes_not_that_type(s, observations)
    ]
    if exempt and not family:
        return "establishes the value is NOT a refusal, so there is no reason to compare"
    return ""


def _capability_proof(pairs, inner_if, skip_node, observations: set[str],
                      all_observations: set[str], cap_derived):
    """``(proof source, how it narrows)`` when S5 holds; ``("", why not)`` when not.

    Two narrowings a fresh lens made necessary in row 6h and both still stand: the
    assertion must be in the branch the skip is actually in, not any enclosing
    one, and it must read a capability, because "any assertion at all" is
    satisfied by `assert registry is not None`. What row 6h's fix never did was
    LOOK AT THE GUARD, and that is F12.

    The refusal reason is returned rather than dropped: a site that ALMOST proved
    it is more useful to a reader than a bare S2.
    """
    if inner_if is None:
        return "", "the skip is not inside an `if`"
    branch = None
    for candidate in (inner_if.body, inner_if.orelse):
        if any(any(n is skip_node for n in ast.walk(s)) for s in candidate):
            branch = candidate
            break
    if branch is None:
        return "", "the skip is not in either branch of its own `if`"
    before = []
    for stmt in branch:
        if any(n is skip_node for n in ast.walk(stmt)):
            break
        before.append(stmt)

    narrowing = _guard_narrows(pairs, observations)
    if not narrowing:
        # THE BRANCH CAN PIN WHAT THE GUARD LEFT OPEN, and that is how
        # `test_c10_25` is ACTUALLY correct. Its guard is `out.reason !=
        # "alias_collision"`, a complement that names nothing; the assertion
        # `out.reason == "predicate_merge"` sitting above the skip is what makes
        # every other reason FAIL rather than skip. The first cut accepted that
        # site for its GUARD, which does not carry it -- so the case passed for
        # the wrong reason and a lens said so.
        pinned = [
            s for s in before
            if isinstance(s, ast.Assert) and _positive_naming(s.test, observations)
        ]
        if pinned:
            narrowing = (
                "leaves the outcome open in the guard, but the block asserts "
                f"`{ast.unparse(pinned[0].test)}` before it skips, which FAILS on "
                "every other outcome"
            )
    if not narrowing:
        # WHICH KIND OF FLAG IS THIS? The baseline conflates two different pieces
        # of news and the supervisor's ruling on raising it requires the
        # difference to be legible in the entry itself. A site with NO capability
        # assertion has no proof to check. A site that HAS one, in the falsifying
        # sense, has a proof this gate cannot verify -- which is a limit of the
        # instrument, not a defect in the suite. Reporting only the first failure
        # made those two read the same.
        held = ""
        for stmt in before:
            if isinstance(stmt, ast.Assert) and _mentions_capability(stmt.test, cap_derived):
                if _falsifying(stmt.test, cap_derived, all_observations):
                    held = ast.unparse(stmt.test)
                    break
        base = (
            "the guard tests the observation without naming WHICH outcome the "
            "capability explains, so an assertion under it fires on every other "
            "outcome too"
        )
        if held:
            return "", (
                base + f". NOTE THE KIND: the block DOES assert `{held}`, which fails "
                "on a backend holding the capability -- so the proof may well be "
                "sound and THIS GATE CANNOT VERIFY IT. A limit of the instrument, "
                "not an established defect in the suite"
            )
        return "", (
            base + ". NOTE THE KIND: no assertion in the skip's own branch reads a "
            "capability at all, so there is no proof here to check"
        )

    found = ""
    for stmt in before:
        if not isinstance(stmt, ast.Assert):
            continue
        if not _mentions_capability(stmt.test, cap_derived):
            continue
        found = ast.unparse(stmt.test)
        if _falsifying(stmt.test, cap_derived, all_observations):
            return found, narrowing
    if found:
        # NOT "cannot fail". A lens fed three expressions that DO fail on a capable
        # backend -- `caps.f == 0`, `caps.f is not True`, a chained comparison --
        # and the gate refused each with a sentence that was FALSE of the
        # expression it had just quoted. Refusing them is fail-closed and right;
        # printing a false reason is F15 pointed the other way. So the text now
        # says what this gate READS, which is a claim about the gate.
        return "", (
            f"the block asserts `{found}` before it skips, but that is not a form "
            f"this gate can verify FAILS on a backend holding the capability -- it "
            f"reads `<cap> is False`, `not <cap>`, and `and`/`or` combinations of "
            f"those, and nothing else"
        )
    return "", "no assertion in the skip's own branch reads a capability before it skips"


# --------------------------------------------------------------------------
# classification
# --------------------------------------------------------------------------

def classify_file(path: Path) -> list[Site]:
    return classify_source(
        path.read_text(encoding="utf-8"), path.relative_to(REPO_ROOT).as_posix()
    )


def classify_source(src: str, rel: str) -> list[Site]:
    tree = ast.parse(src, filename=rel)
    modules, bare = _pytest_aliases(tree)

    owner: dict[int, ast.AST] = {}
    for func in [
        n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]:
        for node in ast.walk(func):
            if _is_skip_call(node, modules, bare):
                prev = owner.get(id(node))
                if prev is None or func.lineno > prev.lineno:
                    owner[id(node)] = func

    sites: list[Site] = []
    cache: dict[int, tuple] = {}

    for node in sorted(
        [n for n in ast.walk(tree) if _is_skip_call(n, modules, bare)],
        key=lambda n: (n.lineno, n.col_offset),
    ):
        func = owner.get(id(node))
        fname = func.name if func is not None else "<module>"
        ordinal = 0  # rewritten below, grouped by guard text

        if func is None:
            sites.append(
                Site(rel, fname, ordinal, node.lineno, UNCONDITIONAL, "",
                     "skip at module level, outside any function", 0)
            )
            continue

        if id(func) not in cache:
            roots = _roots(func)
            driving = _driving_receivers(func) - _locally_bound(func)
            observations = {n for n, r in roots.items() if r} - driving
            assert_roots: set[str] = set()
            for a in _assertion_nodes(func):
                for n in _names_read(a):
                    assert_roots |= roots.get(n, set())
            params = {a.arg for a in func.args.args + func.args.kwonlyargs}
            n_asserts = len(_assertion_nodes(func))
            cache[id(func)] = (
                roots, driving, observations, assert_roots, params, n_asserts,
                _locally_bound(func), _capability_derived(func),
            )
        (roots, driving, observations, assert_roots, params, n_asserts, local,
         cap_derived) = cache[id(func)]

        pairs, inner_if, shape = _guard_chain(func, node)
        chain = [t for t, _ in pairs]

        polar = " and ".join(
            ast.unparse(t) if taken else f"not ({ast.unparse(t)})" for t, taken in pairs
        )

        if shape == "other":
            sites.append(
                Site(rel, fname, ordinal, node.lineno, UNDECIDABLE, polar,
                     "the guard is not an `if` -- a while, a `for`/`while` ELSE, an "
                     "except handler, a match arm or a boolean short-circuit -- so "
                     "this checker cannot say what it reads", n_asserts)
            )
            continue

        if not chain:
            sites.append(
                Site(rel, fname, ordinal, node.lineno, UNCONDITIONAL, "",
                     "no enclosing conditional -- this skip is unconditional", n_asserts)
            )
            continue

        # THE RECORDED TEXT CARRIES POLARITY. Without it an else-branch guard was
        # written down as its own negation: `ontoloche/contract/conftest.py:149`
        # recorded `backend == 'external' and backend == 'sqlite' and backend ==
        # 'sqlite_minimal' and backend == 'postgres'` -- four mutually exclusive
        # equalities ANDed, a literal contradiction, as the guard of a REACHABLE
        # skip. That text goes into the census, into the baseline, and into the
        # ordinal key. **[Measured before changing it]** 16 sites' text moves and
        # NONE is in a baselined function, so no ident in the ratchet changes.
        guard_src = polar
        guard_names: set[str] = set()
        cap_read: set[str] = set()
        for t in chain:
            guard_names |= _names_read(t)
            # A walrus TARGET is a Store context, so `_names_read` does not see it --
            # yet `if (out := registry.merge_types(...)).reason == "x":` plainly reads
            # `out`. Without this the guard read nothing observed and the site landed
            # in S0-ENVIRONMENT, the most ungated cell there is, for a skip decided by
            # the result under test.
            guard_names |= {
                w.id
                for n in ast.walk(t) if isinstance(n, ast.NamedExpr)
                for w in ast.walk(n.target) if isinstance(w, ast.Name)
            }
            cap_read |= _capability_reads(t)

        read_obs = (guard_names - cap_read - cap_derived) & observations
        guard_roots: set[str] = set()
        for n in read_obs:
            guard_roots |= roots.get(n, set())

        def emit(cat, why):
            sites.append(
                Site(rel, fname, ordinal, node.lineno, cat, guard_src, why, n_asserts)
            )

        if read_obs:
            shared = guard_roots & assert_roots
            if shared:
                proof, detail = _capability_proof(
                    pairs, inner_if, node, read_obs, observations, cap_derived
                )
                if proof:
                    # The `why` says WHAT WAS CHECKED and what was not. F15: the old
                    # text quoted the vacuous assertion verbatim and then stated a
                    # consequence that was false of the very expression it had just
                    # quoted -- it printed the disproof and drew the opposite
                    # conclusion, and told the reader not to look.
                    emit(PROVEN_ENV,
                         "guard reads " + ", ".join(sorted(read_obs))
                         + f" -- the result under test -- but it {detail}, and the block "
                         f"asserts `{proof}` before it skips, an expression that FAILS on "
                         "a backend holding the capability. CHECKED: the narrowing, the "
                         "falsifying sense, and that the assertion is defeatable. NOT "
                         "CHECKED, because no AST can know it: that this capability is "
                         "the one that explains this outcome")
                else:
                    emit(UNDER_TEST,
                         "guard reads " + ", ".join(sorted(read_obs))
                         + " -- an observation this test's own assertions also reach"
                         + (f" (via {', '.join(sorted(shared))})"
                            if shared != read_obs else "")
                         + f"; NOT proven-environmental because {detail}")
            else:
                emit(SETUP,
                     "guard reads " + ", ".join(sorted(read_obs))
                     + " -- an observation no assertion in this function reaches")
            continue

        guarded_params = guard_names & params
        if guarded_params and not fname.startswith("test_"):
            emit(UNDECIDABLE,
                 "guard reads " + ", ".join(sorted(guarded_params))
                 + " -- a parameter of a HELPER, so the value arrives from a caller "
                 "this checker does not follow")
            continue

        inline = _guard_inline_calls(chain, driving, local)
        if inline:
            emit(UNDECIDABLE,
                 "guard calls " + ", ".join(sorted(inline))
                 + " inline, binding no name, so nothing can be compared against the "
                 "assertions")
            continue

        emit(ENV, "guard reads no observation")

    # Ordinals are assigned per (function, GUARD TEXT), not per function, and the
    # reason is a fresh lens's finding: with a plain per-function counter, adding
    # an ordinary ENVIRONMENT skip above a flagged one renumbered the flagged one
    # and the gate failed on a commit that added no defect at all -- with
    # `--write-baseline` offered as the remedy. "A gate that fails for unrelated
    # reasons is a gate somebody weakens" is this file's own sentence.
    seen: dict[tuple[str, str], int] = {}
    for site in sites:
        key = (site.func, site.guard)
        site.ordinal = seen.get(key, 0)
        seen[key] = site.ordinal + 1
    return sites


# ---------------------------------------------------------------------------
# CALIBRATION. A gate whose own classifier is untested is the defect this row
# exists to name, so the classifier is pinned against the shapes that produced
# it and the gate runs the pin on every invocation.
#
# HONESTY NOTE ON PROVENANCE, because it matters and is easy to hide.
# `C3-26`'s pre-fix source is quoted VERBATIM from the row 6h brief, where the
# supervisor recorded it after reading it at test_c3_resolve_type.py:1173.
# `C10-16`'s pre-fix source is a RECONSTRUCTION from its current form and row
# 6f's account of the fix, not a recovery -- row 6f fixed both inside its own
# working tree, so no commit ever held them and `git log -S` finds nothing.
# `C3-14`'s pre-fix form is NOT recoverable and NOT reconstructible without
# guessing, so it is EXCLUDED from this set rather than invented.
#
# Cases 6 onward were all written by ADVERSARIAL LENSES in round 1, each of
# which broke the classifier as it then stood. They are pinned so the breakage
# cannot come back.
# ---------------------------------------------------------------------------

CALIBRATION: tuple[tuple[str, str, str], ...] = (
    (
        "C3-26 pre-fix (VERBATIM from the brief)",
        UNDER_TEST,
        '''
import pytest
def test_c3_26(adapter, make_registry):
    blind = make_registry(DegradedAdapter(adapter, indexes_membership=False))
    unscored = blind.resolve_type("commentable", ResolveContext(), tier="opus")
    if unscored.confidence is not None:
        pytest.skip(
            "this leg still scored the pair, so the unscorable branch is not reachable "
            "here and there is nothing for this id to assert"
        )
    assert unscored.confidence is None
    assert unscored.outcome == "existing"
''',
    ),
    (
        "C10-16 pre-fix (RECONSTRUCTED, not recovered)",
        UNDER_TEST,
        '''
import pytest
def test_c10_16(adapter, make_registry):
    registry = make_registry(adapter, approval_policy="auto")
    merged = registry.merge_types("commentable", "searchable", "same", merged_by="user:sd")
    if isinstance(merged, Refusal):
        pytest.skip("this backend refused the merge")
    assert not isinstance(merged, Refusal), merged
''',
    ),
    (
        "the supervisor's SETUP RESULT shape -- must NOT be flagged",
        SETUP,
        '''
import pytest
def test_setup(registry):
    gone = registry.retire("boroname", "consolidated", retired_by="user:sd")
    if isinstance(gone, Refusal):
        pytest.skip("this backend cannot retire the holder")
    out = registry.resolve_type("boroname", ResolveContext())
    assert "RETIRED" in out.reason
''',
    ),
    (
        "the supervisor's ENVIRONMENT shape -- must NOT be flagged",
        ENV,
        '''
import pytest
def test_env(registry):
    if not registry.caps.indexes_membership:
        pytest.skip("this backend cannot read extents")
    out = registry.resolve_type("boroname", ResolveContext())
    assert out.confidence == 1.0
''',
    ),
    (
        "the suite's own NOT REACHABLE shape -- proven environmental",
        PROVEN_ENV,
        '''
import pytest
def test_proven(adapter, make_registry):
    degraded = make_registry(DegradedAdapter(adapter, stores_aliases=False))
    refused = degraded.merge_types("ent_a", "ent_b", "one", merged_by="user:sd")
    if not isinstance(refused, Refusal):
        assert degraded.caps.stores_aliases is False, refused
        pytest.skip("NOT REACHABLE: stores_aliases=False drops the alias")
    assert any(w.startswith("identity_guard_skipped:") for w in refused.warnings)
''',
    ),
    (
        "LENS B1: an extra assertion calling a method on the result MUST NOT un-flag it",
        UNDER_TEST,
        '''
import pytest
def test_b1(adapter, make_registry):
    blind = make_registry(DegradedAdapter(adapter, indexes_membership=False))
    unscored = blind.resolve_type("commentable", ResolveContext(), tier="opus")
    if unscored.confidence is not None:
        pytest.skip("nothing for this id to assert")
    assert unscored.confidence is None
    assert unscored.outcome.startswith("ex")
''',
    ),
    (
        "LENS M8a: the guard reads a DICT-STASHED copy of what the assert reads",
        UNDER_TEST,
        '''
import pytest
def test_m8a(registry):
    out = registry.merge_types("a", "b", "one", merged_by="user:sd")
    seen = {"reason": out.reason}
    if seen["reason"] is None:
        pytest.skip("nothing to assert")
    assert out.reason == "alias_collision"
''',
    ),
    (
        "LENS M8b: the guard reads a BOOL derived from what the assert reads",
        UNDER_TEST,
        '''
import pytest
def test_m8b(registry):
    out = registry.merge_types("a", "b", "one", merged_by="user:sd")
    refused = isinstance(out, Refusal)
    if refused:
        pytest.skip("nothing to assert")
    assert out.warnings
''',
    ),
    (
        "LENS M7: `with pytest.raises` IS an assertion",
        UNDER_TEST,
        '''
import pytest
def test_m7(registry):
    out = registry.merge_types("a", "b", "one", merged_by="user:sd")
    if isinstance(out, Refusal):
        pytest.skip("nothing to assert")
    with pytest.raises(ValueError):
        out.explode()
''',
    ),
    (
        "LENS M9: a TRIVIAL proof must not launder an S2 into S5",
        UNDER_TEST,
        '''
import pytest
def test_m9(registry):
    out = registry.merge_types("a", "b", "one", merged_by="user:sd")
    if isinstance(out, Refusal):
        assert registry is not None
        pytest.skip("NOT REACHABLE")
    assert out.warnings
''',
    ),
    (
        "LENS M5: a skip in an EXCEPT handler is not `unconditional`",
        UNDECIDABLE,
        '''
import pytest
def test_m5(registry):
    try:
        out = registry.merge_types("a", "b", "one", merged_by="user:sd")
    except ValueError:
        pytest.skip("this backend raises here")
    assert out.warnings
''',
    ),
    (
        "LENS M6: `raise pytest.skip.Exception(...)` is a skip",
        UNDER_TEST,
        '''
import pytest
def test_m6(registry):
    out = registry.merge_types("a", "b", "one", merged_by="user:sd")
    if isinstance(out, Refusal):
        raise pytest.skip.Exception("nothing to assert")
    assert out.warnings
''',
    ),
    (
        "LENS M6b: `import pytest as p` hides nothing",
        UNDER_TEST,
        '''
import pytest as p
def test_m6b(registry):
    out = registry.merge_types("a", "b", "one", merged_by="user:sd")
    if isinstance(out, Refusal):
        p.skip("nothing to assert")
    assert out.warnings
''',
    ),
    (
        "LENS B2: a HELPER guarding on its own PARAMETER is undecidable, not environment",
        UNDECIDABLE,
        '''
import pytest
def _skip_if_cannot_record(registry, out):
    if isinstance(out, Refusal) and out.reason == "cannot_record_override":
        pytest.skip("this backend cannot record")
''',
    ),
    # The three below were FALSE POSITIVES this checker produced for real, in the
    # census run that followed the receiver rule being narrowed. Narrowing it was
    # forced (see B1); these are what the narrowing cost, and they are pinned so
    # the cost cannot come back silently. All three are canonical ENVIRONMENT.
    (
        "REGRESSION: a capability object bound from a call is still CONFIGURATION",
        ENV,
        '''
import pytest
def test_c15_09(adapter, make_registry):
    caps = adapter.capabilities()
    if caps.stores_attributes:
        pytest.skip("this backend stores arbitrary attributes")
    projected = sorted(caps.attribute_projections)[0]
    out = make_registry(adapter).attribute_census(projected)
    assert out.complete is False, caps
''',
    ),
    (
        "REGRESSION: `x.caps.flag` is a capability read whoever owns x",
        ENV,
        '''
import pytest
def test_c19_68(adapter, make_registry):
    registry = make_registry(adapter)
    if not registry.caps.stores_invocations:
        pytest.skip("this backend does not store invocations")
    assert registry.list_types("entity").types is not None
''',
    ),
    (
        "REGRESSION: poking an ATTRIBUTE on a fixture does not make the fixture a result",
        ENV,
        '''
import pytest
def test_c0_05(adapter):
    migrations = getattr(adapter, "_migration_sql", None)
    if migrations is None:
        pytest.skip("this backend does not expose numbered migrations to inspect")
    original = migrations()
    version = len(original)
    broken = list(original) + [(version + 1, "broken", "NOT SQL")]
    adapter._migration_sql = lambda: broken
    assert len(original) == version
''',
    ),
    # -----------------------------------------------------------------------
    # ROW 6j: THE AXIS. Derived from the three PARTS, not from the three names
    # -- a set built from three remembered cases will not catch the fourth
    # nobody has thought of. One case per part per DIRECTION: the shape that
    # must be refused, and the shape that must still be accepted. The accept
    # cases are drawn from live sites so the set cannot drift from the suite.
    # -----------------------------------------------------------------------
    (
        "AXIS part 2 (F12) -- the repaired shape, narrowed. MUST stay S5",
        PROVEN_ENV,
        '''
import pytest
def _tombstone_holding(registry, word="zzz_moved"):
    gone = registry.retire("alpha", "no longer used", retired_by="user:sd", force=True)
    if isinstance(gone, Refusal) and gone.reason == "cannot_record_override":
        assert registry.caps.stores_events is False, (
            "this backend records events, so the refusal is not a capability", gone.detail,
        )
        pytest.skip("NOT REACHABLE: stores_events=False refuses the forced retire")
    assert not isinstance(gone, Refusal), gone
    assert word in (gone.aliases or ()), gone.aliases
    return gone
''',
    ),
    (
        "AXIS part 2 (F12) EXPERIMENT 1 -- the SAME site with ONLY the reason clause "
        "removed. Classified S5 before this fix, which is the whole finding",
        UNDER_TEST,
        '''
import pytest
def _tombstone_holding(registry, word="zzz_moved"):
    gone = registry.retire("alpha", "no longer used", retired_by="user:sd", force=True)
    if isinstance(gone, Refusal):
        assert registry.caps.stores_events is False, (
            "this backend records events, so the refusal is not a capability", gone.detail,
        )
        pytest.skip("NOT REACHABLE: stores_events=False refuses the forced retire")
    assert not isinstance(gone, Refusal), gone
    assert word in (gone.aliases or ()), gone.aliases
    return gone
''',
    ),
    (
        "AXIS part 2 (F12) EXPERIMENT 2 -- the supervisor's AUTHORISED one-liner, "
        "verbatim. It moved this site S2 -> S5 while leaving the defect in place",
        UNDER_TEST,
        '''
import pytest
def _tombstone_holding(registry, word="zzz_moved"):
    gone = registry.retire("alpha", "no longer used", retired_by="user:sd", force=True)
    if isinstance(gone, Refusal):
        assert registry.caps.stores_events is False, gone
        pytest.skip(f"this backend refused the forced retire ({gone.reason})")
    assert word in (gone.aliases or ()), gone.aliases
    return gone
''',
    ),
    (
        "AXIS part 2 -- `reason !=` narrows as well as `reason ==`. MUST stay S5",
        PROVEN_ENV,
        '''
import pytest
def test_c10_25(adapter, make_registry):
    registry = make_registry(adapter)
    out = registry.merge_types("alpha", "beta", "one", merged_by="user:sd")
    assert isinstance(out, Refusal), out
    if out.reason != "alias_collision":
        assert registry.caps.indexes_membership is False, out.reason
        assert out.reason == "predicate_merge", out.reason
        pytest.skip("NOT REACHABLE: indexes_membership=False makes both extents unknowable")
    assert out.detail["overridable"] is False
''',
    ),
    (
        # THIS CASE ENCODED THE DEFECT IT WAS WRITTEN TO PIN, and a lens said so:
        # it would have passed identically with the negation removed and with the
        # `startswith` on an unrelated object, because the first cut's rule
        # ignored both. Its expectation is CORRECTED here rather than deleted --
        # `not any(w.startswith("import_refused:") ...)` is the COMPLEMENT of a
        # marker test, so it names no outcome, and the exemption does not reach it
        # because it is not a type test. This is a LIVE site
        # (`test_c12_foundry_import.py:1402`) and moving it is the whole of this
        # row's reclassification. Fail-closed, and the supervisor rules on the
        # baseline.
        "AXIS part 2 -- a COMPLEMENTED marker test names no outcome, and the "
        "exemption does not reach it. This case was pinned S5 by the first cut",
        UNDER_TEST,
        '''
import pytest
def test_c12_27(registry):
    out = registry.import_types([{"name": "plaza"}], namespace="dpr", kind="entity")
    assert out, out
    warnings = tuple(out[0].warnings or ())
    if not any(w.startswith("import_refused:") for w in warnings):
        assert registry.caps.stores_aliases is False, warnings
        pytest.skip("NOT REACHABLE: stores_aliases=False drops the alias")
    assert any(w.startswith("import_field_ignored:") for w in warnings), warnings
''',
    ),
    (
        "AXIS part 2 -- a NUMERIC constant must not buy a narrowing. `len(x) > 0` is a "
        "threshold, not a reason, and admitting it sells the exemption for a `0`",
        UNDER_TEST,
        '''
import pytest
def test_numeric_is_not_a_reason(registry):
    out = registry.merge_types("a", "b", "one", merged_by="user:sd")
    if isinstance(out, Refusal) and len(out.warnings) > 0:
        assert registry.caps.stores_events is False, out
        pytest.skip("NOT REACHABLE")
    assert out.warnings
''',
    ),
    # THE EXEMPTION, IN ALL THREE DIRECTIONS. An exemption is a NEW WAY THROUGH
    # THE GATE -- F12's shape wearing a different hat -- so "invert your guard and
    # the reason requirement disappears" must not become true by accident. The
    # gate's response to abusing it is written down here on purpose.
    (
        "EXEMPTION, legitimate: an inverse guard WITH a capability proof. The value is "
        "not a Refusal, so `.reason` does not exist and no narrowing can be demanded",
        PROVEN_ENV,
        '''
import pytest
def test_c10_27(adapter, make_registry):
    degraded = make_registry(DegradedAdapter(adapter, stores_aliases=False))
    refused = degraded.merge_types("ent_a", "ent_b", "one", merged_by="user:sd")
    if not isinstance(refused, Refusal):
        assert degraded.caps.stores_aliases is False, (
            "this backend stores aliases, so the collision was real", refused,
        )
        pytest.skip("NOT REACHABLE: stores_aliases=False drops the alias")
    assert any(w.startswith("identity_guard_skipped:") for w in refused.warnings)
''',
    ),
    (
        "EXEMPTION, abused: an inverse guard with NO capability proof is still FLAGGED. "
        "Inverting a guard buys nothing on its own",
        UNDER_TEST,
        '''
import pytest
def test_inverse_with_no_proof(adapter, make_registry):
    degraded = make_registry(DegradedAdapter(adapter, stores_aliases=False))
    refused = degraded.merge_types("ent_a", "ent_b", "one", merged_by="user:sd")
    if not isinstance(refused, Refusal):
        pytest.skip("this leg did not refuse, so there is nothing to assert")
    assert any(w.startswith("identity_guard_skipped:") for w in refused.warnings)
''',
    ),
    (
        "EXEMPTION, abused: an inverse guard with a VACUOUS proof. F15 applies here too "
        "and the exemption must not smuggle it past",
        UNDER_TEST,
        '''
import pytest
def test_inverse_with_a_vacuous_proof(adapter, make_registry):
    degraded = make_registry(DegradedAdapter(adapter, stores_aliases=False))
    refused = degraded.merge_types("ent_a", "ent_b", "one", merged_by="user:sd")
    if not isinstance(refused, Refusal):
        assert True or degraded.caps.stores_aliases
        pytest.skip("NOT REACHABLE: stores_aliases=False drops the alias")
    assert any(w.startswith("identity_guard_skipped:") for w in refused.warnings)
''',
    ),
    (
        "EXEMPTION, boundary: `not x.ok` is NOT exempt. `x.reason` IS available there, "
        "so the requirement CAN be met, and a negated truthiness test admits a family "
        "exactly as a positive one does",
        UNDER_TEST,
        '''
import pytest
def test_negated_truthiness_is_not_the_exemption(registry):
    out = registry.merge_types("a", "b", "one", merged_by="user:sd")
    if not out.ok:
        assert registry.caps.stores_events is False, out
        pytest.skip("NOT REACHABLE")
    assert out.warnings
''',
    ),
    (
        "AXIS part 1 (F4) -- the INVERTED sense. `is True` is trivially true on every "
        "real backend, so it cannot fail and proves nothing",
        UNDER_TEST,
        '''
import pytest
def test_f4_inverted_sense(registry):
    gone = registry.retire("alpha", "gone", retired_by="user:sd", force=True)
    if isinstance(gone, Refusal) and gone.reason == "cannot_record_override":
        assert registry.caps.stores_events is True, gone
        pytest.skip("NOT REACHABLE")
    assert not isinstance(gone, Refusal), gone
''',
    ),
    (
        "AXIS part 1 (F4) -- a BARE TRUTHY capability read is the same defect without "
        "the `is True` spelling",
        UNDER_TEST,
        '''
import pytest
def test_f4_bare_truthy(registry):
    gone = registry.retire("alpha", "gone", retired_by="user:sd", force=True)
    if isinstance(gone, Refusal) and gone.reason == "cannot_record_override":
        assert registry.caps.stores_events, gone
        pytest.skip("NOT REACHABLE")
    assert not isinstance(gone, Refusal), gone
''',
    ),
    (
        "AXIS part 3 (F15) -- `assert True or X` verbatim. The gate used to QUOTE this "
        "expression and then state a consequence that is false of it",
        UNDER_TEST,
        '''
import pytest
def test_f15_verbatim(registry):
    gone = registry.retire("alpha", "gone", retired_by="user:sd", force=True)
    if isinstance(gone, Refusal) and gone.reason == "cannot_record_override":
        assert True or registry.caps.stores_events
        pytest.skip("NOT REACHABLE")
    assert not isinstance(gone, Refusal), gone
''',
    ),
    # -----------------------------------------------------------------------
    # ROUND 2. Six shapes three fresh lenses broke the axis with, pinned so the
    # breakage cannot come back. Two lenses found the first one independently.
    # -----------------------------------------------------------------------
    (
        "R2 -- ONE ALIAS LINE must not launder the capability off the RESULT. "
        "`gone.caps` is not a fact about the environment however it is spelled",
        UNDER_TEST,
        '''
import pytest
def test_alias_launder(registry):
    gone = registry.retire("alpha", "no longer used", retired_by="user:sd", force=True)
    why, detail = gone.reason, gone.detail
    if why == "cannot_record_override":
        assert gone.caps.stores_events is False, detail
        pytest.skip("NOT REACHABLE")
    assert not isinstance(gone, Refusal), gone
''',
    ),
    (
        "R2 -- the SAME aliased guard with a real environment proof MUST stay S5, so "
        "the fix above is not a blanket refusal of aliased guards",
        PROVEN_ENV,
        '''
import pytest
def test_alias_ok(registry):
    gone = registry.retire("alpha", "no longer used", retired_by="user:sd", force=True)
    why, detail = gone.reason, gone.detail
    if why == "cannot_record_override":
        assert registry.caps.stores_events is False, detail
        pytest.skip("NOT REACHABLE")
    assert not isinstance(gone, Refusal), gone
''',
    ),
    (
        "R2 -- `caps = adapter.capabilities()` IS a capability proof. Refusing it "
        "printed `no assertion ... reads a capability`, which was false of the block",
        PROVEN_ENV,
        '''
import pytest
def test_caps_bound(adapter, registry):
    caps = adapter.capabilities()
    gone = registry.retire("alpha", "gone", retired_by="user:sd", force=True)
    if isinstance(gone, Refusal) and gone.reason == "cannot_record_override":
        assert caps.stores_events is False, gone
        pytest.skip("NOT REACHABLE: stores_events=False refuses the forced retire")
    assert not isinstance(gone, Refusal), gone
''',
    ),
    (
        "R2 -- a POSITIVE `any(w.startswith(...))` over an observed collection NAMES "
        "an outcome. The comprehension target carries the observation it iterates",
        PROVEN_ENV,
        '''
import pytest
def test_any_positive(registry):
    out = registry.import_types([{"name": "plaza"}], namespace="dpr", kind="entity")
    assert out, out
    warnings = tuple(out[0].warnings or ())
    if any(w.startswith("import_refused:") for w in warnings):
        assert registry.caps.stores_aliases is False, warnings
        pytest.skip("NOT REACHABLE: stores_aliases=False drops the alias")
    assert any(w.startswith("import_field_ignored:") for w in warnings), warnings
''',
    ),
    (
        "R2 -- a skip in a `for ... else` is UNDECIDABLE, never `unconditional`. The "
        "loop BODY keeps its own `if`, which is how this row's own repair stayed S5",
        UNDECIDABLE,
        '''
import pytest
def test_for_else(registry):
    out = registry.merge_types("a", "b", "one", merged_by="user:sd")
    for w in out.warnings:
        if w.startswith("identity_guard_skipped:"):
            break
    else:
        pytest.skip("no guard note on this backend")
    assert out.warnings
''',
    ),
    (
        "R2 -- a WALRUS binds a name, so the guard is not an unbindable inline call. "
        "It was landing in S4 with that sentence printed about it",
        UNDER_TEST,
        '''
import pytest
def test_walrus(registry):
    if (out := registry.merge_types("a", "b", "one", merged_by="user:sd")).reason == "cannot_record_override":
        pytest.skip("nothing to assert")
    assert out.warnings
''',
    ),
    (
        "AXIS part 3 (F15) -- the same vacuity NOT spelled `True or`, so the pin is on "
        "the property rather than on the wording",
        UNDER_TEST,
        '''
import pytest
def test_f15_reworded(registry):
    gone = registry.retire("alpha", "gone", retired_by="user:sd", force=True)
    if isinstance(gone, Refusal) and gone.reason == "cannot_record_override":
        assert registry.caps.stores_events is False or registry is not None, gone
        pytest.skip("NOT REACHABLE")
    assert not isinstance(gone, Refusal), gone
''',
    ),
)


def run_selftest(verbose: bool = False) -> list[str]:
    """Classify the calibration shapes. Returns the failures, empty if clean."""
    failures: list[str] = []
    for label, expected, src in CALIBRATION:
        sites = classify_source(src, f"<calibration:{label}>")
        got = [s.category for s in sites]
        if got != [expected]:
            failures.append(f"{label}: expected [{expected}], got {got}")
        elif verbose:
            print(f"    OK  {expected:24s} {label}")
    return failures


# --------------------------------------------------------------------------
# census, baseline, gate
# --------------------------------------------------------------------------

def is_generated(path: Path) -> bool:
    try:
        with path.open(encoding="utf-8") as fh:
            for _ in range(12):
                line = fh.readline()
                if not line:
                    break
                if GENERATED_BANNER in line:
                    return True
    except (OSError, UnicodeDecodeError):
        return False
    return False


def census(directories=SCAN_DIRS) -> list[Site]:
    if isinstance(directories, (str, Path)):
        directories = (Path(directories),)
    sites: list[Site] = []
    for directory in directories:
        if not directory.is_dir():
            continue
        for path in sorted(directory.rglob("*.py")):
            if "__pycache__" in path.parts or is_generated(path):
                continue
            try:
                sites.extend(classify_file(path))
            except (SyntaxError, UnicodeDecodeError, OSError) as exc:
                # Fail CLOSED and say which file. A census that silently drops an
                # unreadable file is a census that passes by not looking.
                print(f"FAIL: {path} could not be censused: {exc!r}", file=sys.stderr)
                raise SystemExit(1)
    return sites


def flagged_idents(sites) -> list[str]:
    return sorted(s.ident for s in sites if s.category == UNDER_TEST)


def load_baseline():
    if not BASELINE_PATH.exists():
        return None
    try:
        data = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
    except (ValueError, OSError) as exc:
        print(f"FAIL: the baseline at {BASELINE_PATH} is unreadable: {exc}",
              file=sys.stderr)
        raise SystemExit(1)
    if not isinstance(data, dict) or not isinstance(data.get("sites"), list):
        print(f"FAIL: the baseline at {BASELINE_PATH} is malformed -- `sites` must be "
              f"a list", file=sys.stderr)
        raise SystemExit(1)
    return data


def _entries(sites) -> list[dict]:
    # `why` rides along because THE BASELINE CONFLATES TWO DIFFERENT THINGS and a
    # reader counting entries would read every one as a defect. Most mean *this
    # site's proof is MISSING*. At least one means *this site's proof EXISTS and
    # this instrument cannot see it* -- `test_c12_27` asserts a capability that a
    # capable backend would fail, under a guard whose refusal-evidence marker no
    # AST can recognise as refusal evidence. Both are correctly flagged and they
    # are not the same news. The supervisor's ruling on raising this baseline
    # required the distinction to be legible HERE, without reading `6J-RUN.md`.
    return [
        {"site": s.ident, "asserts": s.asserts, "guard": s.guard, "why": s.why}
        for s in sorted(
            (s for s in sites if s.category == UNDER_TEST), key=lambda s: s.ident
        )
    ]


def function_assertions(directories=SCAN_DIRS) -> dict[tuple[str, str], int]:
    """``(file, function) -> assertion count``, over every function, skip or not.

    Needed because the BEST repair for a flagged site deletes the site: turning
    ``if X: pytest.skip()`` into ``assert not X`` leaves no skip to classify. Without
    this map that reads as "the function is GONE" and the sanctioned repair was
    refused -- which would have pushed people toward the laundering repairs instead.
    """
    out: dict[tuple[str, str], int] = {}
    if isinstance(directories, (str, Path)):
        directories = (Path(directories),)
    for directory in directories:
        if not directory.is_dir():
            continue
        for path in sorted(directory.rglob("*.py")):
            if "__pycache__" in path.parts or is_generated(path):
                continue
            try:
                tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            except (SyntaxError, UnicodeDecodeError, OSError):
                continue
            rel = path.relative_to(REPO_ROOT).as_posix()
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    out[(rel, node.name)] = len(_assertion_nodes(node))
    return out


def _leaving_verdict(entry, current_by_ident, func_asserts=None):
    """Why did a baselined site stop being flagged? REPAIRED, or DE-ASSERTED?

    This is the hole a fresh lens opened in round 1, and it is the sharpest thing
    said about this gate. Every flagged site becomes UNFLAGGED if you simply DELETE
    the assertion that reads the guarded value: the site drops to S1, the census
    shrinks, and ``--write-baseline`` was documented as "a normal commit anyone may
    make". **So the cheapest path to a green gate was to remove coverage** -- the
    exact outcome the ratchet exists to prevent, and worse than the defect it gates.

    Three of the flagged sites are near-identical helpers: ``_tombstone_holding``
    in ``test_c4_propose_type.py``, ``test_c12_foundry_import.py`` and
    ``test_c9_retire.py``. Only the c4 copy was flagged, and the only difference is
    that the c4 copy ASSERTS that its fixture held. **The gate was punishing the
    strongest of the three.**

    So the enclosing function's assertion count rides in the baseline, and a site
    may only leave it while that function still asserts at least as much as it did.
    A repair ADDS assertions -- ``if X: skip()`` becoming ``assert not X``, or
    becoming the suite's proven-environmental shape, both go UP. Deleting coverage
    goes DOWN, and that is refused here rather than noticed later in review.
    """
    was = entry.get("asserts")
    site = current_by_ident.get(entry["site"])
    if site is None:
        # The skip is gone. That is the BEST repair -- `if X: skip()` became
        # `assert not X` -- provided the function is still there and still asserts.
        path, _, rest = entry["site"].partition("::")
        fname = rest.split("#")[0]
        now = (func_asserts or {}).get((path, fname))
        if now is None:
            return "GONE", (
                "the skip AND its function are both gone. Deleting a test is not "
                "repairing it, and this needs a ruling rather than a baseline edit"
            )
        if was is not None and now < was:
            return "DE-ASSERTED", (
                f"the skip is gone, but `{fname}` went from {was} assert(s) to {now}. "
                f"The site left the flagged set because COVERAGE WAS REMOVED"
            )
        return "REPAIRED", (
            f"the skip is gone and `{fname}` now holds {now} assert(s) against {was} "
            f"before -- the skip became an assertion"
        )
    if was is not None and site.asserts < was:
        return "DE-ASSERTED", (
            f"the enclosing function went from {was} assert(s) to {site.asserts}. "
            f"This site left the flagged set because COVERAGE WAS REMOVED, not "
            f"because the skip was repaired. A repair adds assertions"
        )
    return "REPAIRED", (
        f"now {site.category}, with {site.asserts} assert(s) against {was} before"
    )


def write_baseline(sites, allow_deassertion: bool = False) -> int:
    entries = _entries(sites)
    current_by_ident = {s.ident: s for s in sites}
    old = load_baseline()

    if old is not None:
        func_asserts = function_assertions()
        keeping = {e["site"] for e in entries}
        refused = []
        for entry in old.get("sites", []):
            if isinstance(entry, str) or entry.get("site") in keeping:
                continue
            verdict, why = _leaving_verdict(entry, current_by_ident, func_asserts)
            if verdict in ("DE-ASSERTED", "GONE") and not allow_deassertion:
                refused.append(f"{entry['site']}\n        {verdict}: {why}")
        if refused:
            print("REFUSED to lower the baseline. These sites left the flagged set "
                  "WITHOUT being repaired:", file=sys.stderr)
            for r in refused:
                print("    " + r, file=sys.stderr)
            print("\n  Repair them, or get the supervisor's ruling and re-run with\n"
                  "  --allow-deassertion, so the choice is on the record.",
                  file=sys.stderr)
            return 1

    payload = {
        "_comment": (
            "RATCHET BASELINE for check_skip_census.py. A site may only leave this "
            "list by being REPAIRED. `asserts` is the enclosing function's assertion "
            "count, carried so that DELETING the assertion -- the cheapest way to "
            "make this gate green, and strictly worse for the suite -- is refused "
            "rather than rewarded. RAISING the list requires the ontoloche "
            "supervisor's ruling. The gate fails if `count` disagrees with `sites`. "
            "READ `why` BEFORE COUNTING DEFECTS: an entry saying the guard names no "
            "outcome, or that no assertion reads a capability, is a site whose proof "
            "is MISSING. An entry saying the guard is a complemented marker test is a "
            "site whose proof EXISTS and which this instrument cannot verify -- a "
            "limit of the checker, not a defect in the suite. A ratchet baseline "
            "records what the instrument can PROVE, not what the author believes."
        ),
        "count": len(entries),
        "sites": entries,
    }
    BASELINE_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return 0


def run_gate() -> int:
    calibration_failures = run_selftest()
    if calibration_failures:
        print("check_skip_census: FAIL -- the CLASSIFIER itself regressed",
              file=sys.stderr)
        for f in calibration_failures:
            print("    " + f, file=sys.stderr)
        return 1

    for required in SCAN_DIRS:
        if not required.is_dir():
            # BOTH trees, not just the sync one. The module docstring records that
            # scanning only the sync tree left two hand-written async files
            # permanently unwatched, and a fresh lens found it. Checking only
            # CONTRACT_DIR here left the same hole one rename away: 18 of 139
            # sites would vanish and the gate would still pass.
            print(f"FAIL: {required} is not a directory. A census of nothing is not "
                  f"a pass.", file=sys.stderr)
            return 1

    sites = census()
    if not sites:
        print("FAIL: the census found NO skip call sites at all, which means the "
              "instrument is broken rather than the suite being clean.", file=sys.stderr)
        return 1

    found = flagged_idents(sites)
    baseline = load_baseline()
    if baseline is None:
        print(f"FAIL: no baseline at {BASELINE_PATH}", file=sys.stderr)
        print("      run --write-baseline to seed it", file=sys.stderr)
        return 1

    entries = [e for e in baseline.get("sites", []) if isinstance(e, dict)]
    declared = [e["site"] for e in entries]
    declared_count = baseline.get("count")
    failures: list[str] = []

    if len(entries) != len(baseline.get("sites", [])):
        failures.append("the baseline holds entries that are not objects -- it was "
                        "written by an older or hand-edited version")
    if declared_count != len(declared):
        failures.append(
            f"the baseline's own count ({declared_count}) disagrees with its own site "
            f"list ({len(declared)} entries). The number cannot move without the sites "
            f"moving with it."
        )
    if len(set(declared)) != len(declared):
        failures.append("the baseline holds DUPLICATE sites, so its count overstates "
                        "what it actually pins")

    # COUNTED, not set-tested, and that is the INTERIM MITIGATION for J19.
    #
    # `Site.ident` is `file::func#ordinal` and ordinals are per (function, GUARD
    # TEXT), so two skips in one function with different guards BOTH carry `#0`.
    # A set test therefore absorbs the second one: add a result-conditioned skip
    # to a function that already holds a baselined one and `[i for i in found if i
    # not in set(declared)]` returns nothing. Demonstrated in `6J-RUN.md` §3.3 --
    # two flagged skips, zero reported, the ratchet not turning.
    #
    # The real fix puts the guard into the ident and rewrites every entry in the
    # baseline, which is routed to its own row. This costs nothing and closes the
    # reachable half: `found` and `declared` are LISTS, one element per flagged
    # site, so comparing them as MULTISETS catches an addition that collides.
    # It reads only the baseline's existing `sites` list and changes no
    # classification.
    #
    # ITS LIMIT, NAMED RATHER THAN LEFT: it cannot catch a SWAP -- one flagged
    # site removed and another added inside the same function, where the count
    # holds. Only a real identity closes that, which is why the routing stands.
    found_counts = collections.Counter(found)
    declared_counts = collections.Counter(declared)
    new = sorted(
        i for i in found_counts if found_counts[i] > declared_counts.get(i, 0)
    )
    if new:
        failures.append(
            "RESULT-CONDITIONED SKIPS ADDED -- the ratchet only turns one way:\n"
            + "\n".join(
                f"    + {i}"
                + (
                    f"   ({found_counts[i]} sites now carry this ident, "
                    f"{declared_counts.get(i, 0)} baselined -- see J19)"
                    if found_counts[i] > 1
                    else ""
                )
                for i in new
            )
        )

    current_by_ident = {s.ident: s for s in sites}
    stale = [e for e in entries if e["site"] not in set(found)]
    if stale:
        func_asserts = function_assertions()
    for entry in stale:
        verdict, why = _leaving_verdict(entry, current_by_ident, func_asserts)
        failures.append(
            f"{entry['site']} is no longer flagged -- {verdict}\n        {why}\n"
            f"        Lower the baseline with --write-baseline in the same commit."
        )

    if failures:
        print("check_skip_census: FAIL", file=sys.stderr)
        for f in failures:
            print("  " + f, file=sys.stderr)
        _print_detail([s for s in sites if s.ident in set(new)], file=sys.stderr)
        return 1

    print(f"check_skip_census: OK -- {len(found)} result-conditioned skip(s), "
          f"baseline {declared_count}, and the ratchet holds.")
    return 0


def _print_detail(sites, file=sys.stdout) -> None:
    for s in sites:
        print(f"    {s.file}:{s.line}  {s.func}#{s.ordinal}", file=file)
        print(f"      guard: {s.guard}", file=file)
        print(f"      why:   {s.why}", file=file)


def run_census(directories=SCAN_DIRS) -> int:
    sites = census(directories)
    by_cat: dict[str, list[Site]] = {c: [] for c in CATEGORIES}
    for s in sites:
        by_cat[s.category].append(s)

    print("census of " + ", ".join(
        d.relative_to(REPO_ROOT).as_posix() for d in
        ([Path(directories)] if isinstance(directories, (str, Path)) else directories)
    ) + "   (generated mirrors skipped)")
    print(f"  AST call sites: {len(sites)}")
    print(f"  files:          {len(sorted({s.file for s in sites}))}")
    print()
    for cat in CATEGORIES:
        print(f"  {cat:24s} {len(by_cat[cat]):4d}")
    print()
    for cat in (UNDER_TEST, PROVEN_ENV, UNDECIDABLE, UNCONDITIONAL):
        if not by_cat[cat]:
            continue
        print(f"--- {cat} ({len(by_cat[cat])}) ---")
        _print_detail(by_cat[cat])
        print()
    print(f"--- {SETUP} ({len(by_cat[SETUP])}) ---")
    for s in by_cat[SETUP]:
        print(f"    {s.file}:{s.line}  {s.func}#{s.ordinal}  guard: {s.guard}")
    print()
    print(f"--- {ENV} ({len(by_cat[ENV])}), by file ---")
    per_file: dict[str, int] = {}
    for s in by_cat[ENV]:
        per_file[s.file] = per_file.get(s.file, 0) + 1
    for f, n in sorted(per_file.items(), key=lambda kv: -kv[1]):
        print(f"    {n:4d}  {f}")
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--census", action="store_true", help="print the full breakdown")
    p.add_argument("--dir", help="census a different directory (reporting only)")
    p.add_argument("--selftest", action="store_true",
                   help="classify the calibration shapes only")
    p.add_argument("--write-baseline", action="store_true",
                   help="seed or LOWER the ratchet baseline")
    p.add_argument("--allow-deassertion", action="store_true",
                   help="permit lowering a site that lost coverage. Needs a ruling.")
    args = p.parse_args(argv)

    if args.selftest:
        failures = run_selftest(verbose=True)
        for f in failures:
            print("FAIL " + f, file=sys.stderr)
        return 1 if failures else 0
    if args.census:
        if args.dir:
            d = Path(args.dir)
            return run_census((d if d.is_absolute() else (REPO_ROOT / d)).resolve())
        return run_census(SCAN_DIRS)
    if args.write_baseline:
        sites = census()
        rc = write_baseline(sites, allow_deassertion=args.allow_deassertion)
        if rc == 0:
            print(f"baseline written: {len(flagged_idents(sites))} site(s)")
        return rc
    return run_gate()


if __name__ == "__main__":
    raise SystemExit(main())
