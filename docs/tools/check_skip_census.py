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
* it FAILS when the baseline holds a site that is no longer flagged (fix the
  test, lower the baseline in the same commit -- a normal commit anyone may make);
* it FAILS when the baseline's own ``count`` disagrees with its own ``sites``,
  so nobody can raise the number without the diff showing the site.

Raising the baseline requires the supervisor's ruling. Lowering it does not.

THE DISCRIMINATOR
-----------------
Pre-registered in ``docs/runs/6H-RUN.md`` §0.3 as **D1**:

    A bare ``pytest.skip(...)`` is S2 (illegitimate) when the guard controlling it
    reads a name whose value is also read by an ``assert`` in the same test
    function. It is S1 when the guard reads a call result no assert ever reads.
    It is S0 when the guard reads no call result at all.

**D1 was amended TWICE, both times before the census was counted, and both
amendments are recorded in §1.2 of the run record rather than made silently.**

*First:* as pre-registered it flagged the RECEIVER as well as the RESULT.
``registry = make_registry(adapter)`` makes ``registry`` a call result, so
``if not registry.caps.indexes_membership: skip()`` -- the canonical *legitimate*
environment skip -- would have been flagged in any test whose assertions mention
``registry``. The fix is a sharpening rather than a weakening:

    A name used as a CALL RECEIVER (``name.method(...)``) anywhere in the function
    is a receiver, not a result. Guards read results; the object that produces
    results is configuration.

*Second:* a value one step downstream of a call is still that call's result, so
``warnings = rows[0].warnings or ()`` carries ``rows``'s result-ness. The closure
stops at the next call, because a call produces a new value rather than a view of
the old one.

**AND THE MODEL ITSELF DID NOT SURVIVE THE CENSUS.** The brief's three categories
are four. This suite invented the fourth on purpose and documented it in its own
words -- *"Gated on the CAPABILITY rather than on the outcome, so a store that CAN
hold the alias and merged anyway is a finding and not a skip"* -- and there are
SEVEN of them. A skip that reads the result under test and then ASSERTS, before
skipping, that a capability explains that result has converted a result-condition
into an environment-condition and shown its work. It is not the ``C3-26`` shape:
break the implementation on a capable backend and the assertion fails, so the id
FAILS rather than skips.

    S0  ENVIRONMENT       guard reads no call result            legitimate
    S1  SETUP RESULT      guard reads a result no assert reads  probably legitimate; NOT ruled here
    S2  RESULT UNDER TEST guard reads a result an assert reads  never legitimate  <-- GATED
    S3  UNCONDITIONAL     no guard at all                       reported, not gated
    S4  UNDECIDABLE       the guard CALLS inline, binding no name, so nothing can be
                          compared against the assertions. Never gated: an unbound
                          value cannot be the value an assertion reads
    S5  PROVEN            reads the result under test, then asserts the capability
                          that explains it before skipping -- the suite's own
                          "NOT REACHABLE, never a pass" pattern

Only S2 is gated. Gating S1 or S5 would rule on categories row 6h is explicitly
not authorised to rule on.

USAGE
-----
    py docs/tools/check_skip_census.py                   # the gate. exit 0 or 1
    py docs/tools/check_skip_census.py --census          # full breakdown, exit 0
    py docs/tools/check_skip_census.py --selftest        # classifier calibration only
    py docs/tools/check_skip_census.py --write-baseline  # lower (or seed) the baseline

The gate runs ``--selftest`` on every invocation and fails if the classifier
regressed, because a gate whose own classifier is untested is the exact defect
this row exists to name.
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACT_DIR = REPO_ROOT / "ontoloche" / "contract"
BASELINE_PATH = Path(__file__).resolve().parent / "skip_census_baseline.json"

# Builtins and test-helper predicates that may appear inside a guard without
# meaning "this guard calls the system under test". `isinstance(gone, Refusal)`
# is the supervisor's own SETUP RESULT example and must not land in S4.
GUARD_SAFE_CALLS = frozenset(
    {
        "isinstance", "len", "set", "list", "tuple", "dict", "any", "all",
        "sorted", "str", "int", "float", "bool", "getattr", "hasattr", "abs",
        "max", "min", "sum", "type", "repr", "frozenset", "next", "iter",
    }
)

ENV = "S0-ENVIRONMENT"
SETUP = "S1-SETUP-RESULT"
UNDER_TEST = "S2-RESULT-UNDER-TEST"
UNCONDITIONAL = "S3-UNCONDITIONAL"
UNDECIDABLE = "S4-UNDECIDABLE"
PROVEN_ENV = "S5-PROVEN-ENVIRONMENTAL"

CATEGORIES = (ENV, SETUP, UNDER_TEST, UNCONDITIONAL, UNDECIDABLE, PROVEN_ENV)


class Site:
    """One bare ``pytest.skip(...)`` call site, and what this gate decided about it.

    Identity is ``(file, function, ordinal)`` and deliberately NOT the line number:
    line numbers churn on every edit above them, so a line-keyed baseline would
    fail the gate on unrelated commits, and a gate that fails for unrelated reasons
    is a gate somebody weakens.
    """

    __slots__ = ("file", "func", "ordinal", "line", "category", "guard", "why")

    def __init__(self, file, func, ordinal, line, category, guard, why):
        self.file = file
        self.func = func
        self.ordinal = ordinal
        self.line = line
        self.category = category
        self.guard = guard
        self.why = why

    @property
    def ident(self) -> str:
        return f"{self.file}::{self.func}#{self.ordinal}"

    def __repr__(self) -> str:  # pragma: no cover - diagnostics only
        return f"<Site {self.ident} {self.category}>"


def _names_read(node) -> set[str]:
    return {n.id for n in ast.walk(node) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)}


def _assign_targets(node) -> list[str]:
    targets = []
    if isinstance(node, ast.Assign):
        raw = node.targets
    elif isinstance(node, (ast.AnnAssign, ast.AugAssign)):
        raw = [node.target]
    elif isinstance(node, ast.NamedExpr):
        raw = [node.target]
    else:
        return targets
    for t in raw:
        for sub in ast.walk(t):
            if isinstance(sub, ast.Name):
                targets.append(sub.id)
    return targets


def _is_skip_call(node, skip_aliases: set[str]) -> bool:
    if not isinstance(node, ast.Call):
        return False
    f = node.func
    if isinstance(f, ast.Attribute) and f.attr == "skip":
        return isinstance(f.value, ast.Name) and f.value.id in {"pytest", "pt"}
    if isinstance(f, ast.Name) and f.id in skip_aliases:
        return True
    return False


def _skip_aliases(tree: ast.AST) -> set[str]:
    """Names bound to ``pytest.skip`` by an import, e.g. ``from pytest import skip``."""
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "pytest":
            for a in node.names:
                if a.name == "skip":
                    found.add(a.asname or a.name)
    return found


def _receivers(func: ast.AST) -> set[str]:
    """Names that have a method called ON them somewhere in this function.

    These are the objects the test drives the system through -- ``registry``,
    ``adapter``, ``blind`` -- not the results it examines. The amendment to D1
    turns on this set: a guard that reads a receiver is reading configuration,
    not a result.
    """
    out: set[str] = set()
    for node in ast.walk(func):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            base = node.func.value
            while isinstance(base, (ast.Attribute, ast.Subscript)):
                base = base.value
            if isinstance(base, ast.Name):
                out.add(base.id)
    return out


def _call_results(func: ast.AST) -> set[str]:
    """Names holding a call's result -- a fresh observation of the system.

    Two ways in. Direct: the assigned expression contains a call. Derived: the
    assigned expression contains NO call and reads a name that is already a
    result, so ``warnings = rows[0].warnings or ()`` carries ``rows``'s
    result-ness onto ``warnings``. The derived arm is a bounded closure -- it
    stops at the next call, because a call produces a NEW value rather than a
    view of the old one, which is what stops ``registry`` (the object every call
    is made THROUGH) from being dragged in as a result of itself.
    """
    out: set[str] = set()
    pending: list[tuple[list[str], set[str]]] = []

    for node in ast.walk(func):
        if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign, ast.NamedExpr)):
            value = node.value
            if value is None:
                continue
            targets = _assign_targets(node)
            if any(isinstance(n, ast.Call) for n in ast.walk(value)):
                out.update(targets)
            else:
                pending.append((targets, _names_read(value)))
        elif isinstance(node, ast.withitem):
            if node.optional_vars is not None and isinstance(node.context_expr, ast.Call):
                for sub in ast.walk(node.optional_vars):
                    if isinstance(sub, ast.Name):
                        out.add(sub.id)

    changed = True
    while changed:
        changed = False
        for targets, reads in pending:
            if reads & out and not set(targets) <= out:
                out.update(targets)
                changed = True
    return out


def _locally_bound(func: ast.AST) -> set[str]:
    """Comprehension and for-loop targets -- ``w`` in ``any(w.startswith(...) ...)``.

    These are iteration variables, not objects the test drives the system through,
    so a method called on one is not the guard calling the system under test.
    """
    out: set[str] = set()
    for node in ast.walk(func):
        if isinstance(node, ast.comprehension):
            for sub in ast.walk(node.target):
                if isinstance(sub, ast.Name):
                    out.add(sub.id)
        elif isinstance(node, (ast.For, ast.AsyncFor)):
            for sub in ast.walk(node.target):
                if isinstance(sub, ast.Name):
                    out.add(sub.id)
    return out


def _proves_environment(func: ast.AST, chain, skip_node, receivers, results) -> str:
    """Does the guarded block ASSERT the environmental cause before it skips?

    The suite invented this pattern on purpose and documents it in its own words:

        Gated on the CAPABILITY rather than on the outcome, so a store that CAN
        hold the alias and merged anyway is a finding and not a skip.

    A skip that reads the result under test and then asserts, before skipping,
    that a CAPABILITY explains that result has converted a result-condition into
    an environment-condition and shown its work. It is not the ``C3-26`` shape:
    if the implementation broke tomorrow on a capable backend, the assertion
    fails and the id does NOT skip.

    Returns the assertion's source if the block proves it, else "".
    """
    for node in ast.walk(func):
        if not isinstance(node, ast.If):
            continue
        if not any(t is node.test for t in chain):
            continue
        for branch in (node.body, node.orelse):
            seen_skip = False
            for stmt in branch:
                if any(n is skip_node for n in ast.walk(stmt)):
                    seen_skip = True
                    break
            if not seen_skip:
                continue
            for stmt in branch:
                if any(n is skip_node for n in ast.walk(stmt)):
                    break
                if not isinstance(stmt, ast.Assert):
                    continue
                names = _names_read(stmt.test)
                if names & receivers and not names & results:
                    return ast.unparse(stmt.test)
    return ""


def _asserted_names(func: ast.AST) -> set[str]:
    out: set[str] = set()
    for node in ast.walk(func):
        if isinstance(node, ast.Assert):
            out |= _names_read(node)
    return out


def _guard_chain(func: ast.AST, skip_node: ast.AST) -> list[ast.expr]:
    """Every ``if`` test that must hold for ``skip_node`` to run, outermost first.

    Walks DOWN from the function body carrying the active tests, so a skip nested
    two ``if``s deep reports both. A test the skip sits inside the ``test`` of --
    a walrus in the condition itself -- is not a guard on it and is not collected.
    """
    chain: list[ast.expr] = []
    found = False

    def contains(node) -> bool:
        return any(n is skip_node for n in ast.walk(node))

    def visit(node, active: list[ast.expr]) -> None:
        nonlocal found, chain
        if found:
            return
        if node is skip_node:
            chain = list(active)
            found = True
            return
        if isinstance(node, ast.If):
            if contains(node.test):
                chain = list(active)
                found = True
                return
            for stmt in node.body:
                visit(stmt, active + [node.test])
            for stmt in node.orelse:
                visit(stmt, active + [node.test])
            return
        for child in ast.iter_child_nodes(node):
            visit(child, active)

    for stmt in getattr(func, "body", []):
        visit(stmt, [])
        if found:
            break
    return chain


def _enclosing_functions(tree: ast.AST) -> list[ast.AST]:
    return [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]


def classify_file(path: Path) -> list[Site]:
    return classify_source(
        path.read_text(encoding="utf-8"), path.relative_to(REPO_ROOT).as_posix()
    )


def classify_source(src: str, rel: str) -> list[Site]:
    tree = ast.parse(src, filename=rel)
    aliases = _skip_aliases(tree)

    # innermost enclosing function for each skip call
    owner: dict[int, ast.AST] = {}
    for func in _enclosing_functions(tree):
        for node in ast.walk(func):
            if _is_skip_call(node, aliases):
                prev = owner.get(id(node))
                if prev is None or (
                    getattr(func, "lineno", 0) > getattr(prev, "lineno", 0)
                ):
                    owner[id(node)] = func

    sites: list[Site] = []
    per_func: dict[str, int] = {}
    module_level = [
        n for n in ast.walk(tree) if _is_skip_call(n, aliases) and id(n) not in owner
    ]

    for node in sorted(
        [n for n in ast.walk(tree) if _is_skip_call(n, aliases)],
        key=lambda n: (n.lineno, n.col_offset),
    ):
        func = owner.get(id(node))
        fname = func.name if func is not None else "<module>"
        ordinal = per_func.get(fname, 0)
        per_func[fname] = ordinal + 1

        if func is None:
            sites.append(
                Site(rel, fname, ordinal, node.lineno, UNCONDITIONAL,
                     "", "skip at module level, outside any test function")
            )
            continue

        chain = _guard_chain(func, node)

        if not chain:
            sites.append(
                Site(rel, fname, ordinal, node.lineno, UNCONDITIONAL,
                     "", "no enclosing `if` -- this skip is unconditional")
            )
            continue

        guard_src = " and ".join(ast.unparse(t) for t in chain)
        guard_names = set()
        for t in chain:
            guard_names |= _names_read(t)

        receivers = _receivers(func) - _locally_bound(func)
        results = _call_results(func) - receivers
        asserted = _asserted_names(func)

        read_results = guard_names & results
        sut_calls = _guard_sut_calls(chain, receivers)

        if read_results:
            if read_results & asserted:
                proof = _proves_environment(func, chain, node, receivers, results)
                if proof:
                    cat = PROVEN_ENV
                    why = (
                        "guard reads "
                        + ", ".join(sorted(read_results & asserted))
                        + f" -- the result under test -- but the block asserts `{proof}` "
                        "BEFORE it skips, so a capable backend that behaved wrongly "
                        "would FAIL here rather than skip"
                    )
                    sites.append(Site(rel, fname, ordinal, node.lineno, cat, guard_src, why))
                    continue
                why = (
                    "guard reads "
                    + ", ".join(sorted(read_results & asserted))
                    + " -- a call result this test's own assertions also read"
                )
                cat = UNDER_TEST
            else:
                why = (
                    "guard reads "
                    + ", ".join(sorted(read_results))
                    + " -- a call result no assert in this function reads"
                )
                cat = SETUP
        elif sut_calls:
            cat = UNDECIDABLE
            why = (
                "guard calls "
                + ", ".join(sorted(sut_calls))
                + " inline, so there is no bound name to compare against the assertions"
            )
        else:
            cat = ENV
            why = "guard reads no call result"

        sites.append(Site(rel, fname, ordinal, node.lineno, cat, guard_src, why))

    return sites


def _guard_sut_calls(chain, receivers: set[str]) -> set[str]:
    """Calls made ON a receiver from inside the guard itself."""
    out: set[str] = set()
    for t in chain:
        for n in ast.walk(t):
            if isinstance(n, ast.Call):
                f = n.func
                if isinstance(f, ast.Name):
                    if f.id not in GUARD_SAFE_CALLS:
                        out.add(f.id + "()")
                elif isinstance(f, ast.Attribute):
                    base = f.value
                    while isinstance(base, (ast.Attribute, ast.Subscript)):
                        base = base.value
                    if isinstance(base, ast.Name) and base.id in receivers:
                        out.add(f"{base.id}.{f.attr}()")
    return out


def _owning_stmt(func: ast.AST, node: ast.AST):
    """The statement node that contains ``node``, so guard walking has a target."""
    for stmt in ast.walk(func):
        if isinstance(stmt, ast.stmt):
            for child in ast.walk(stmt):
                if child is node:
                    # prefer the innermost statement
                    inner = None
                    for s2 in ast.walk(stmt):
                        if isinstance(s2, ast.stmt) and s2 is not stmt:
                            for c2 in ast.walk(s2):
                                if c2 is node:
                                    inner = s2
                                    break
                        if inner is not None:
                            break
                    return inner or stmt
    return None


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
# guessing, so it is EXCLUDED from this set rather than invented. Two of the
# three known instances are pinned here; the third is named as missing.
# ---------------------------------------------------------------------------

CALIBRATION: tuple[tuple[str, str, str], ...] = (
    (
        "C3-26 pre-fix (VERBATIM from the brief)",
        UNDER_TEST,
        """
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
""",
    ),
    (
        "C10-16 pre-fix (RECONSTRUCTED, not recovered)",
        UNDER_TEST,
        """
import pytest
def test_c10_16(adapter, make_registry):
    registry = make_registry(adapter, approval_policy="auto")
    merged = registry.merge_types("commentable", "searchable", "same", merged_by="user:sd")
    if isinstance(merged, Refusal):
        pytest.skip("this backend refused the merge")
    assert not isinstance(merged, Refusal), merged
""",
    ),
    (
        "the supervisor's SETUP RESULT shape -- must NOT be flagged",
        SETUP,
        """
import pytest
def test_setup(registry):
    gone = registry.retire("boroname", "consolidated", retired_by="user:sd")
    if isinstance(gone, Refusal):
        pytest.skip("this backend cannot retire the holder")
    out = registry.resolve_type("boroname", ResolveContext())
    assert "RETIRED" in out.reason
""",
    ),
    (
        "the supervisor's ENVIRONMENT shape -- must NOT be flagged",
        ENV,
        """
import pytest
def test_env(registry):
    if not registry.caps.indexes_membership:
        pytest.skip("this backend cannot read extents")
    out = registry.resolve_type("boroname", ResolveContext())
    assert out.confidence == 1.0
""",
    ),
    (
        "the suite's own NOT REACHABLE shape -- proven environmental, not flagged",
        PROVEN_ENV,
        """
import pytest
def test_proven(adapter, make_registry):
    degraded = make_registry(DegradedAdapter(adapter, stores_aliases=False))
    refused = degraded.merge_types("ent_a", "ent_b", "one", merged_by="user:sd")
    if not isinstance(refused, Refusal):
        assert degraded.caps.stores_aliases is False, refused
        pytest.skip("NOT REACHABLE: stores_aliases=False drops the alias")
    assert any(w.startswith("identity_guard_skipped:") for w in refused.warnings)
""",
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


def census(directory: Path = CONTRACT_DIR) -> list[Site]:
    sites: list[Site] = []
    for path in sorted(directory.glob("*.py")):
        if "__pycache__" in path.parts:
            continue
        sites.extend(classify_file(path))
    return sites


def flagged_idents(sites) -> list[str]:
    return sorted(s.ident for s in sites if s.category == UNDER_TEST)


def load_baseline():
    if not BASELINE_PATH.exists():
        return None
    return json.loads(BASELINE_PATH.read_text(encoding="utf-8"))


def write_baseline(sites) -> None:
    idents = flagged_idents(sites)
    payload = {
        "_comment": (
            "RATCHET BASELINE for check_skip_census.py. Lowering this list is a "
            "normal commit anyone may make: fix the site, drop its entry. RAISING "
            "it -- adding an entry -- requires the ontoloche supervisor's ruling. "
            "The gate fails if `count` disagrees with `sites`, so the number cannot "
            "move without the site moving with it."
        ),
        "count": len(idents),
        "sites": idents,
    }
    BASELINE_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def run_gate() -> int:
    calibration_failures = run_selftest()
    if calibration_failures:
        print("check_skip_census: FAIL -- the CLASSIFIER itself regressed", file=sys.stderr)
        for f in calibration_failures:
            print("    " + f, file=sys.stderr)
        return 1

    sites = census()
    found = flagged_idents(sites)
    baseline = load_baseline()

    if baseline is None:
        print(f"FAIL: no baseline at {BASELINE_PATH}", file=sys.stderr)
        print("      run --write-baseline to seed it", file=sys.stderr)
        return 1

    declared = list(baseline.get("sites", []))
    declared_count = baseline.get("count")

    failures: list[str] = []

    if declared_count != len(declared):
        failures.append(
            f"the baseline's own count ({declared_count}) disagrees with its own "
            f"site list ({len(declared)} entries). The number cannot move without "
            f"the sites moving with it."
        )

    new = [i for i in found if i not in set(declared)]
    if new:
        failures.append(
            "RESULT-CONDITIONED SKIPS ADDED -- the ratchet only turns one way:\n"
            + "\n".join(f"    + {i}" for i in new)
        )

    stale = [i for i in declared if i not in set(found)]
    if stale:
        failures.append(
            "baseline holds sites the checker no longer flags. If you fixed them, "
            "lower the baseline in the same commit (--write-baseline):\n"
            + "\n".join(f"    - {i}" for i in stale)
        )

    if failures:
        print("check_skip_census: FAIL", file=sys.stderr)
        for f in failures:
            print("  " + f, file=sys.stderr)
        _print_detail([s for s in sites if s.ident in set(new)], file=sys.stderr)
        return 1

    print(
        f"check_skip_census: OK -- {len(found)} result-conditioned skip(s), "
        f"baseline {declared_count}, and the ratchet holds."
    )
    return 0


def _print_detail(sites, file=sys.stdout) -> None:
    for s in sites:
        print(f"    {s.file}:{s.line}  {s.func}#{s.ordinal}", file=file)
        print(f"      guard: {s.guard}", file=file)
        print(f"      why:   {s.why}", file=file)


def run_census() -> int:
    sites = census()
    by_cat: dict[str, list[Site]] = {c: [] for c in CATEGORIES}
    for s in sites:
        by_cat[s.category].append(s)

    print(f"census of {CONTRACT_DIR.relative_to(REPO_ROOT).as_posix()}")
    print(f"  AST call sites: {len(sites)}")
    files = sorted({s.file for s in sites})
    print(f"  files:          {len(files)}")
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
    p.add_argument(
        "--write-baseline", action="store_true", help="seed or LOWER the ratchet baseline"
    )
    p.add_argument(
        "--selftest", action="store_true", help="classify the calibration shapes only"
    )
    args = p.parse_args(argv)

    if args.selftest:
        failures = run_selftest(verbose=True)
        for f in failures:
            print("FAIL " + f, file=sys.stderr)
        return 1 if failures else 0
    if args.census:
        return run_census()
    if args.write_baseline:
        sites = census()
        write_baseline(sites)
        print(f"baseline written: {len(flagged_idents(sites))} site(s)")
        return 0
    return run_gate()


if __name__ == "__main__":
    raise SystemExit(main())
