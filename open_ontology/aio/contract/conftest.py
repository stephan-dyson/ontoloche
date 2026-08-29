"""The async adapter factory, parametrised over backends.

The same rule as the sync suite (PACKAGE.md 6.1): *both reference backends, in one
process, in one run*, and when there is no Postgres to talk to its leg **skips with a
reason** rather than vanishing -- a leg that disappears from the run is a leg nobody
notices is missing.

Three things here are async-specific and none of them is in the generated tree:

the event loop policy
    ``psycopg`` refuses to run async on Windows' default ``ProactorEventLoop`` and
    raises ``InterfaceError`` saying so. On ``win32`` this module selects a selector
    loop at import, before any loop exists; on every other platform it changes
    nothing. Deviation D-A3.

auto mode
    the suite is plain ``async def test_*`` functions with no ``@pytest.mark.asyncio``
    on them, because the marker is not in the sync source and the ids must stay
    identical. ``asyncio_mode = "auto"`` is in ``pyproject.toml`` for a repository run,
    and ``run_async_contract_suite`` passes ``--asyncio-mode=auto`` for an installed
    one. Deviation D-A2.

the fixtures themselves
    are async, and ``make_registry`` hands back an async builder, because
    ``AsyncRegistry`` is constructed with ``await AsyncRegistry.open(...)``
    (deviation D-A1).

Point it at a Postgres with::

    OO_POSTGRES_DSN=postgresql://user:pw@localhost:5432/postgres pytest --pyargs open_ontology.aio.contract
"""

from __future__ import annotations

import asyncio
import os
import sys
import uuid

import pytest

if sys.platform == "win32":
    # Not a preference and not a Windows nicety: psycopg raises
    # InterfaceError("Psycopg cannot use the 'ProactorEventLoop' to run in async mode")
    # on the platform default. Set before any loop is created, so every runner the
    # asyncio plugin builds for this session inherits it.
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from open_ontology._clock import FixedClock
from open_ontology.aio.backends.sqlite import AsyncSQLiteAdapter
from open_ontology.aio.registry import AsyncRegistry
from open_ontology.policy import NamespacePolicy

from open_ontology.contract._coverage import Coverage

from . import _support

POSTGRES_DSN = os.environ.get("OO_POSTGRES_DSN")

#: PACKAGE.md 6.1, amended by row 3d: **three** reference legs, in one process, in one
#: run. ``sqlite_minimal`` is a real SQLite store with four of the nine reference tables
#: absent (``open_ontology/backends/sqlite_minimal.py``) -- five capability flags
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

    Ruling **R8**, applied by row 3c: they stay **binding for the two reference
    backends**, where they pin real behaviour of the resolver this package ships, and
    are **skipped for a foreign adapter**, where they assert nothing about the backend
    under test. Skipped with a reason, never silently -- and the reason names the
    ruling, so a third-party author can see what was not run and why.
    """
    if _support.EXTERNAL_RESOLVER is None:
        return
    skip = pytest.mark.skip(
        reason=(
            "PACKAGE.md 2.6 / ruling R8 -- this test asserts an outcome only the "
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
async def adapter_factory(backend, tmp_path_factory):
    """An async callable returning a fresh, migrated, empty store."""
    made = []

    if backend == "external":
        factory = _support.EXTERNAL_FACTORY

        async def build():
            adapter = await factory()
            await adapter.migrate()
            made.append(adapter)
            return adapter

    elif backend == "sqlite":

        async def build():
            adapter = await AsyncSQLiteAdapter.open(":memory:")
            await adapter.migrate()
            made.append(adapter)
            return adapter

    elif backend == "sqlite_minimal":
        from open_ontology.aio.backends.sqlite_minimal import AsyncMinimalSQLiteAdapter

        async def build():
            # A file, not ``:memory:``: the HOST creates the schema on its own
            # connection and only then is the store handed over. Two connections to
            # ``:memory:`` are two different databases.
            path = str(tmp_path_factory.mktemp("oo_minimal") / "store.sqlite")
            AsyncMinimalSQLiteAdapter.create_host_schema(path)
            adapter = await AsyncMinimalSQLiteAdapter.open(path)
            await adapter.migrate()  # verify-only: it checks, it does not create
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

        from open_ontology.aio.backends.postgres import AsyncPostgresAdapter

        async def build():
            schema = "oo_" + uuid.uuid4().hex[:12]
            adapter = await AsyncPostgresAdapter.open(POSTGRES_DSN, schema=schema)
            await adapter.migrate()
            made.append(adapter)
            return adapter

    else:  # pragma: no cover
        raise AssertionError(backend)

    yield build

    for adapter in made:
        try:
            if getattr(adapter, "schema", None):
                await adapter._execute(f'DROP SCHEMA IF EXISTS "{adapter.schema}" CASCADE')
            close = getattr(adapter, "close", None)
            if close:
                await close()
        except Exception:  # pragma: no cover - teardown must not mask a failure
            pass


@pytest.fixture
async def adapter(adapter_factory, request, backend):
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
    made = await adapter_factory()
    # Ruling R12 / row 3d: the report says what each leg DECLARED, so a declaration
    # nothing checked cannot be printed as part of a clean CONFORMANT verdict.
    _COVERAGE.declare(backend, await made.capabilities())
    if request.node.get_closest_marker("requires_attribute_store") is not None:
        from open_ontology.adapter import AttributeStore

        if not isinstance(made, AttributeStore):
            pytest.skip(
                "PACKAGE.md 5.5 / ruling R2 -- this backend declines the optional "
                "AttributeStore extension, which 5.5 says leaves it fully conformant. "
                "`attribute_census` reports complete=False with a why; this test needs "
                "the extension itself."
            )
    marker = request.node.get_closest_marker("requires_capability")
    if marker is not None:
        caps = await made.capabilities()
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
    """``await make_registry(adapter, **policy_kwargs)`` -- one clock across the test."""

    async def build(adapter, **policy_kwargs):
        policies = policy_kwargs.pop("policies", None)
        resolver = policy_kwargs.pop("resolver", None)
        if resolver is None and _support.EXTERNAL_RESOLVER is not None:
            resolver = _support.EXTERNAL_RESOLVER()
        # PACKAGE.md 7.3 B4 -- no proposal table forces approval_policy="auto".
        if "approval_policy" not in policy_kwargs and not (
            await adapter.capabilities()
        ).stores_proposals:
            policy_kwargs["approval_policy"] = "auto"
        return await AsyncRegistry.open(
            adapter,
            clock=clock,
            resolver=resolver,
            policy=NamespacePolicy(**policy_kwargs),
            policies=policies,
        )

    return build


@pytest.fixture
async def registry(adapter, make_registry):
    return await make_registry(adapter)


# --------------------------------------------------------------------------- reporting
# PACKAGE.md 6.1: a backend is conformant iff *the whole suite* passes, on *both*
# reference backends, *in one run*. A bare `pytest --pyargs open_ontology.contract`
# with no OO_POSTGRES_DSN exits 0 having exercised SQLite alone, and a skip is easy to
# miss next to a wall of passes. So the run states what it actually covered. Added by
# row 3c after an adversarial review round; see docs/findings/3C-VALIDATION.md.

_EXERCISED: set[str] = set()
_EXEMPTED: set[str] = set()
#: Ruling R12, row 3d: which contract ids each leg could not exercise, and why.
_COVERAGE = Coverage(BACKENDS)


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
            "the resolver_dependent tests were skipped (ruling R8)"
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
