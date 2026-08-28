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
