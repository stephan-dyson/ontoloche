"""The contract suite -- the definition of conformance.

    A backend is conformant iff the whole suite passes against it.

The suite ships *inside* the package on purpose: a third-party backend author has to be
able to run the thing that decides whether their backend is correct, without cloning
this repository.

    pytest --pyargs open_ontology.contract
    python -m open_ontology.contract --adapter beacon.ontology:WorkLinkTypeAdapter
"""

from __future__ import annotations

from typing import Any, Callable, Sequence

__all__ = ["run_contract_suite"]


def run_contract_suite(
    adapter_factory: Callable[[], Any], *, args: Sequence[str] = ()
) -> int:
    """Run the whole suite against one backend. Returns pytest's exit code.

    ``adapter_factory`` must return a **fresh, empty** store each time it is called --
    the suite calls it once per test and expects no state to survive between them.
    ``migrate()`` is called for you.
    """
    import pytest

    from . import _support

    previous = _support.EXTERNAL_FACTORY
    _support.EXTERNAL_FACTORY = adapter_factory
    try:
        return int(pytest.main(["--pyargs", "open_ontology.contract", *args]))
    finally:
        _support.EXTERNAL_FACTORY = previous
