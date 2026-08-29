"""The async contract suite -- the same definition of conformance, awaited.

    An async backend is conformant iff the whole suite passes against it.

The 115 contract ids of ``PACKAGE.md`` 6.2 are the same 115 ids here, with the same
test-function names, because every ``test_c*.py`` in this package is *generated from
the sync one* by ``tools/unasync.py``. There is no second set of assertions to keep in
step with the first; there is one set, compiled twice.

    pytest --pyargs open_ontology.aio.contract
    python -m open_ontology.aio.contract --adapter beacon.ontology:WorkLinkTypeAdapter
"""

from __future__ import annotations

from typing import Any, Callable, Sequence

__all__ = ["run_async_contract_suite"]


def run_async_contract_suite(
    adapter_factory: Callable[[], Any],
    *,
    args: Sequence[str] = (),
    include_nonbinding: bool = False,
) -> int:
    """Run the async conformance suite against one backend. Returns pytest's exit code.

    ``adapter_factory`` must be an **async** callable returning a fresh, empty store
    each time it is awaited -- the suite calls it once per test and expects no state to
    survive between them. ``migrate()`` is awaited for you.

    ``include_nonbinding=False`` (the default) deselects tests marked ``nonbinding``,
    the ones PACKAGE.md places outside the conformance definition. Same rule and same
    reason as the sync runner: registering the marker never made it bite, so a backend
    that honestly declines an optional protocol was being told it had failed.
    """
    import pytest

    from . import _support

    marker = () if include_nonbinding else ("-m", "not nonbinding")
    previous = _support.EXTERNAL_FACTORY
    _support.EXTERNAL_FACTORY = adapter_factory
    try:
        # --asyncio-mode=auto rather than an ini setting, so an installed wheel runs
        # the same way the repository does (deviation D-A2).
        return int(
            pytest.main(
                [
                    "--pyargs",
                    "open_ontology.aio.contract",
                    "--asyncio-mode=auto",
                    *marker,
                    *args,
                ]
            )
        )
    finally:
        _support.EXTERNAL_FACTORY = previous
