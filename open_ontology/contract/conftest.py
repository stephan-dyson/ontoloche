"""The adapter factory, parametrised over backends.

PACKAGE.md 6.1: *the suite is parametrised over both reference backends and must pass
on both, in one process, in one run.* So both legs are always collected. When there is
no Postgres to talk to, its leg **skips with a reason** rather than vanishing -- a leg
that disappears from the run is a leg nobody notices is missing.

Point it at a Postgres with::

    OO_POSTGRES_DSN=postgresql://user:pw@localhost:5432/postgres pytest --pyargs open_ontology.contract
"""

from __future__ import annotations

import os
import uuid

import pytest

from .._clock import FixedClock
from ..backends.sqlite import SQLiteAdapter
from ..policy import NamespacePolicy
from ..registry import Registry
from . import _support

POSTGRES_DSN = os.environ.get("OO_POSTGRES_DSN")
BACKENDS = ("sqlite", "postgres")


def pytest_configure(config):
    config.addinivalue_line("markers", "cms: the CMS design test (PACKAGE.md 8)")
    config.addinivalue_line("markers", "nonbinding: outside the conformance definition")
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
    if _support.EXTERNAL_FACTORY is None:
        return
    skip = pytest.mark.skip(
        reason=(
            "PACKAGE.md 2.6 / ruling R8 -- this test asserts an outcome only the "
            "shipped DeterministicResolver produces. It is binding for the reference "
            "backends and says nothing about a foreign adapter's storage."
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
def adapter_factory(backend):
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
def adapter(adapter_factory):
    return adapter_factory()


@pytest.fixture
def clock():
    return FixedClock()


@pytest.fixture
def make_registry(clock):
    """``make_registry(adapter, **policy_kwargs)`` -- one clock across the whole test."""

    def build(adapter, **policy_kwargs):
        policies = policy_kwargs.pop("policies", None)
        return Registry(
            adapter,
            clock=clock,
            policy=NamespacePolicy(**policy_kwargs),
            policies=policies,
        )

    return build


@pytest.fixture
def registry(adapter, make_registry):
    return make_registry(adapter)


# --------------------------------------------------------------------------- reporting
# PACKAGE.md 6.1: a backend is conformant iff *the whole suite* passes, on *both*
# reference backends, *in one run*. A bare `pytest --pyargs open_ontology.contract`
# with no OO_POSTGRES_DSN exits 0 having exercised SQLite alone, and a skip is easy to
# miss next to a wall of passes. So the run states what it actually covered. Added by
# row 3c after an adversarial review round; see docs/findings/3C-VALIDATION.md.

_EXERCISED: set[str] = set()
_EXEMPTED: set[str] = set()


def pytest_runtest_logreport(report):
    if report.when != "call" or report.outcome not in ("passed", "failed"):
        return
    for name in BACKENDS + ("external",):
        if f"[{name}]" in report.nodeid:
            _EXERCISED.add(name)


def pytest_deselected(items):
    for item in items:
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
    if _EXEMPTED:
        write(
            f"  nonbinding tests excluded from the verdict: {len(_EXEMPTED)} "
            f"({', '.join(sorted(_EXEMPTED))})"
        )
    else:
        write("  nonbinding tests excluded from the verdict: none")
