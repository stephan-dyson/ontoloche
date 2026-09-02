"""The adapter factory, parametrised over backends.

PACKAGE.md 6.1: *the suite is parametrised over both reference backends and must pass
on both, in one process, in one run.* So both legs are always collected. When there is
no Postgres to talk to, its leg **skips with a reason** rather than vanishing -- a leg
that disappears from the run is a leg nobody notices is missing.

Point it at a Postgres with::

    OO_POSTGRES_DSN=postgresql://user:pw@localhost:5432/postgres pytest --pyargs ontoloche.contract
"""

from __future__ import annotations

import os
import uuid

import pytest

from .._clock import FixedClock
from ..edges import DEFAULT_MAX_EDGES
from ..backends.sqlite import SQLiteAdapter
from ..policy import NamespacePolicy
from ..registry import Registry
from . import _support
from ._coverage import Coverage

POSTGRES_DSN = os.environ.get("OO_POSTGRES_DSN")

#: PACKAGE.md 6.1, amended by row 3d: **three** reference legs, in one process, in one
#: run. ``sqlite_minimal`` is a real SQLite store with four of the nine reference tables
#: absent (``ontoloche/backends/sqlite_minimal.py``) -- five capability flags
#: declined at once, natively rather than through ``DegradedAdapter``. beacon finding U2:
#: a test double reporting on itself is not evidence that a degraded backend conforms.
BACKENDS = ("sqlite", "postgres", "sqlite_minimal")


def pytest_configure(config):
    config.addinivalue_line("markers", "cms: the CMS design test (PACKAGE.md 8)")
    config.addinivalue_line("markers", "nonbinding: outside the conformance definition")
    config.addinivalue_line(
        "markers",
        "requires_capability(*flags): needs a Capabilities flag the backend may decline; "
        "skipped with a reason when it is False, per PACKAGE.md 3.2",
    )
    config.addinivalue_line(
        "markers",
        "requires_attribute_store: needs the optional AttributeStore extension, which "
        "PACKAGE.md 5.5 and ruling R2 say a conformant backend may decline",
    )
    config.addinivalue_line(
        "markers",
        "resolver_dependent: asserts an outcome only the shipped DeterministicResolver "
        "produces -- binding for the reference backends, skipped for a foreign adapter",
    )


def pytest_collection_modifyitems(config, items):
    """PACKAGE.md 2.6: *no contract test may pass or fail because of resolver quality.*

    Three tests did. ``C3-08``/``C3-09`` assert a ``not_a_type`` outcome that only the
    shipped ``DeterministicResolver``'s lookup table produces, and ``C4-06``'s keyword
    rule is not even behind the ``Resolver`` seam -- so a third-party backend paired
    with its own resolver, which 2.6 calls *the production path*, failed mandatory
    conformance tests for a reason that is neither storage nor its own choice.

    Ruling **Q4**, applied by row 3c: they are **binding whenever the suite runs on
    the shipped ``DeterministicResolver``** -- which is every reference-backend run and
    every third-party run that does not replace it -- and are **skipped when a caller
    supplies their own resolver** via ``run_contract_suite(resolver_factory=...)`` or
    ``--resolver``, because then they assert nothing about the backend under test.

    **The gate is the resolver, not the adapter.** A first attempt keyed the skip on
    whether the *adapter* was foreign, which is the wrong axis for a resolver question:
    it forgave a foreign backend that had kept the shipped resolver (where these tests
    are perfectly valid) and still left PACKAGE.md 2.6's *production path* -- a
    reference backend plus a real model resolver -- unrunnable. Corrected by row 3c
    after a fourth adversarial round. Skipped with a reason, never silently.
    """
    if _support.EXTERNAL_RESOLVER is None:
        return
    skip = pytest.mark.skip(
        reason=(
            "PACKAGE.md 2.6 / ruling Q4 -- this test asserts an outcome only the "
            "shipped DeterministicResolver produces, and this run supplied its own "
            "resolver. No contract test may pass or fail on resolver quality."
        )
    )
    for item in items:
        if item.get_closest_marker("resolver_dependent"):
            item.add_marker(skip)


def pytest_generate_tests(metafunc):
    if "backend" not in metafunc.fixturenames:
        return
    if _support.EXTERNAL_FACTORY is not None:
        metafunc.parametrize("backend", ["external"])
        return
    metafunc.parametrize("backend", list(BACKENDS))


@pytest.fixture
def adapter_factory(backend, tmp_path_factory):
    """A callable returning a fresh, migrated, empty store."""
    made = []

    if backend == "external":
        factory = _support.EXTERNAL_FACTORY

        def build():
            adapter = factory()
            adapter.migrate()
            made.append(adapter)
            return adapter

    elif backend == "sqlite":

        def build():
            adapter = SQLiteAdapter(":memory:")
            adapter.migrate()
            made.append(adapter)
            return adapter

    elif backend == "sqlite_minimal":
        from ..backends.sqlite_minimal import MinimalSQLiteAdapter

        def build():
            # A file, not ``:memory:``: the HOST creates the schema on its own
            # connection and only then is the store handed over, which is the whole
            # point of ``owns_schema=False``. Two connections to ``:memory:`` are two
            # different databases.
            path = str(tmp_path_factory.mktemp("oo_minimal") / "store.sqlite")
            MinimalSQLiteAdapter.create_host_schema(path)
            adapter = MinimalSQLiteAdapter(path)
            adapter.migrate()  # verify-only: it checks, it does not create
            made.append(adapter)
            return adapter

    elif backend == "postgres":
        if not POSTGRES_DSN:
            pytest.skip(
                "PENDING -- no local Postgres. Set OO_POSTGRES_DSN to run this leg; "
                "the 2B gate is not claimable until it is green."
            )
        try:
            import psycopg  # noqa: F401
        except ImportError:  # pragma: no cover - environment-dependent
            pytest.skip("PENDING -- psycopg is not installed (pip install -e '.[postgres]')")

        from ..backends.postgres import PostgresAdapter

        def build():
            schema = "oo_" + uuid.uuid4().hex[:12]
            adapter = PostgresAdapter(POSTGRES_DSN, schema=schema)
            adapter.migrate()
            made.append(adapter)
            return adapter

    else:  # pragma: no cover
        raise AssertionError(backend)

    yield build

    for adapter in made:
        try:
            if getattr(adapter, "schema", None):
                adapter._execute(f'DROP SCHEMA IF EXISTS "{adapter.schema}" CASCADE')
            close = getattr(adapter, "close", None)
            if close:
                close()
        except Exception:  # pragma: no cover - teardown must not mask a failure
            pass


@pytest.fixture
def adapter(adapter_factory, request, backend):
    """PACKAGE.md 3.2: *"Every other flag may be `False` and the backend can still be
    conformant"*, and 7.4 calls a ``stores_proposals=False`` backend conformant *"as a
    third backend"*. The suite falsified both -- **26 tests failed against such a
    backend**, because their harness assumes ``propose_type`` returns a ``Proposal``
    when 7.3 B4 says it returns a ``TypeEntry``.

    A test whose *subject* is a declined capability still asserts the honest unknown --
    6.1 rule 1, unchanged. A test that merely *needs* the capability as scaffolding, like
    every test that must have a proposal before it can approve one, is skipped here with
    a reason naming the flag and quoting the backend's own ``why``. Added by row 3c after
    an adversarial review round found the C13 instance; see 3C-VALIDATION.md.
    """
    made = adapter_factory()
    # Ruling R12 / row 3d: the report says what each leg DECLARED, so a declaration
    # nothing checked cannot be printed as part of a clean CONFORMANT verdict.
    _COVERAGE.declare(backend, made.capabilities())
    if request.node.get_closest_marker("requires_attribute_store") is not None:
        from ..adapter import AttributeStore

        if not isinstance(made, AttributeStore):
            pytest.skip(
                "PACKAGE.md 5.5 / ruling R2 -- this backend declines the optional "
                "AttributeStore extension, which 5.5 says leaves it fully conformant. "
                "`attribute_census` reports complete=False with a why; this test needs "
                "the extension itself."
            )
    # **`iter_markers`, not `get_closest_marker`, and the difference was a RED on main**
    # (row 6c). `get_closest_marker` returns exactly ONE mark, so **stacking two
    # `@requires_capability` decorators silently discarded all but the innermost** --
    # a test declaring `@NEEDS_ATTRIBUTES` *and* `@requires_capability("stores_edges")`
    # was skipped for edges and RUN with `stores_attributes=False`, where its fixture
    # cannot exist. Three ids did that, `check_capability_matrix.py` went from
    # conformant to five failing configurations, and nothing between the decorator and
    # the run said a declaration had been dropped.
    #
    # **A declaration this harness silently ignores is the same shape the register
    # refuses everywhere else** -- one word for two facts, a permission cashed twice, a
    # guard reading an operand nobody passed. `iter_markers` honours every declaration,
    # so a test that names four flags is skipped for four flags, and stacking is a
    # legitimate way to say *this needs the edge store AND the attribute store* rather
    # than a trap. It is also the shape that makes the composite constants
    # (`NEEDS_ATTRIBUTES`, `NEEDS_INVOCATIONS`) composable at all.
    caps = None
    for marker in request.node.iter_markers("requires_capability"):
        if caps is None:
            caps = made.capabilities()
        for flag in marker.args:
            if not getattr(caps, flag):
                pytest.skip(
                    f"PACKAGE.md 3.2 -- this backend declares {flag}=False, which 3.2 "
                    f"says is conformant. This test needs it as scaffolding, not as its "
                    f"subject: {caps.why.get(flag, 'no reason given')}"
                )
    return made


@pytest.fixture
def clock():
    return FixedClock()


@pytest.fixture
def make_registry(clock):
    """``make_registry(adapter, **policy_kwargs)`` -- one clock across the whole test."""

    def build(adapter, **policy_kwargs):
        policies = policy_kwargs.pop("policies", None)
        resolver = policy_kwargs.pop("resolver", None)
        max_edges = policy_kwargs.pop("max_edges", DEFAULT_MAX_EDGES)
        # EDGES.md 3.1's family is seeded at store creation by default, exactly as a
        # deployment gets it. A test opts out only when its subject is an EMPTY
        # vocabulary (C3-04), and says so where it does.
        seed_equivalent_to = policy_kwargs.pop("seed_equivalent_to", True)
        # PACKAGE.md 7.3 B4: no proposal table *forces* approval_policy="auto" -- there
        # is nowhere to hold a pending proposal. The suite used to run every backend
        # under the default "review", so a conformant proposal-less backend met a policy
        # the document says it cannot serve and got a Refusal where a TypeEntry belongs.
        if "approval_policy" not in policy_kwargs and not adapter.capabilities().stores_proposals:
            policy_kwargs["approval_policy"] = "auto"
        if resolver is None and _support.EXTERNAL_RESOLVER is not None:
            resolver = _support.EXTERNAL_RESOLVER()
        return Registry(
            adapter,
            clock=clock,
            resolver=resolver,
            policy=NamespacePolicy(**policy_kwargs),
            policies=policies,
            max_edges=max_edges,
            seed_equivalent_to=seed_equivalent_to,
        )

    return build


@pytest.fixture
def registry(adapter, make_registry):
    return make_registry(adapter)


# --------------------------------------------------------------------------- reporting
# PACKAGE.md 6.1: a backend is conformant iff *the whole suite* passes, on *both*
# reference backends, *in one run*. A bare `pytest --pyargs ontoloche.contract`
# with no OO_POSTGRES_DSN exits 0 having exercised SQLite alone, and a skip is easy to
# miss next to a wall of passes. So the run states what it actually covered. Added by
# row 3c after an adversarial review round; see docs/findings/3C-VALIDATION.md.

_EXERCISED: set[str] = set()
_EXEMPTED: set[str] = set()
#: Ruling R12, row 3d: which contract ids each leg could not exercise, and why.
_COVERAGE = Coverage(BACKENDS)


def pytest_sessionstart(session):
    # The suite is run in-process more than once -- run_contract_suite and
    # check_capability_matrix.py both do it -- and pytest reuses this already-imported
    # module, so without this one Coverage object reports the union of every run.
    _COVERAGE.reset()
    _EXERCISED.clear()
    _EXEMPTED.clear()


def pytest_runtest_logreport(report):
    _COVERAGE.record(report)
    if report.when != "call" or report.outcome not in ("passed", "failed"):
        return
    for name in BACKENDS + ("external",):
        if f"[{name}]" in report.nodeid:
            _EXERCISED.add(name)


def pytest_deselected(items):
    # Only marker-driven exemptions. A `-k` filter deselects too, and counting those
    # would make the summary say a normal filtered run had exempted half the suite.
    for item in items:
        if item.get_closest_marker("nonbinding"):
            _EXEMPTED.add(item.nodeid.rsplit("::", 1)[-1])


def pytest_terminal_summary(terminalreporter):
    write = terminalreporter.write_line
    write("")
    write("CONFORMANCE (PACKAGE.md 6.1)")
    if "external" in _EXERCISED:
        write("  backends exercised: the supplied adapter factory")
    else:
        missing = [b for b in BACKENDS if b not in _EXERCISED]
        write(f"  backends exercised: {', '.join(sorted(_EXERCISED)) or 'none'}")
        if missing:
            write(
                f"  NOT a conformance run -- {', '.join(missing)} did not execute. "
                "6.1 requires both reference backends in one run; set OO_POSTGRES_DSN."
            )
    if _support.EXTERNAL_RESOLVER is not None:
        write(
            "  resolver: SUPPLIED BY THE CALLER -- PACKAGE.md 2.6's production path; "
            "the resolver_dependent tests were skipped (ruling Q4)"
        )
    else:
        write("  resolver: the shipped DeterministicResolver (2.6's fixed point)")
    if _EXEMPTED:
        write(
            f"  nonbinding tests excluded from the verdict: {len(_EXEMPTED)} "
            f"({', '.join(sorted(_EXEMPTED))})"
        )
    else:
        write("  nonbinding tests excluded from the verdict: none")
    # Ruling R12. "329 passed" is the truth about the assertions and not about the
    # coverage: a backend that declines capabilities cannot exercise every id, and a
    # run that does not say which is claiming more than it checked.
    for line in _COVERAGE.lines():
        write(line)
