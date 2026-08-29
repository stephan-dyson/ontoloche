"""The contract suite -- the definition of conformance.

    A backend is conformant iff the whole suite passes against it.

The suite ships *inside* the package on purpose: a third-party backend author has to be
able to run the thing that decides whether their backend is correct, without cloning
this repository.

    pytest --pyargs open_ontology.contract
    python -m open_ontology.contract --adapter beacon.ontology:WorkLinkTypeAdapter

**``nonbinding`` is enforced here, not merely declared.** PACKAGE.md 5.5 says a backend
*"may not be failed for"* ``C15-02``, because ``AttributeStore`` is optional and a
backend that omits it answers honestly with ``complete=False`` rather than wrongly.
Registering the marker did not make that true: until row 3c the runner passed every
test and a conformant backend was told it had failed. ``run_contract_suite`` now
excludes ``nonbinding`` by default and **says so in the summary**, so a green run can
never be read without seeing what it exempted.
"""

from __future__ import annotations

from typing import Any, Callable, Sequence

__all__ = ["run_contract_suite"]


def run_contract_suite(
    adapter_factory: Callable[[], Any],
    *,
    resolver_factory: Callable[[], Any] | None = None,
    args: Sequence[str] = (),
    include_nonbinding: bool = False,
) -> int:
    """Run the conformance suite against one backend. Returns pytest's exit code.

    ``adapter_factory`` must return a **fresh, empty** store each time it is called --
    the suite calls it once per test and expects no state to survive between them.
    ``migrate()`` is called for you.

    ``resolver_factory`` supplies a ``Resolver`` for the whole run -- PACKAGE.md 2.6's
    **production path**, which the suite could not exercise at all until row 3c. Supply
    it and the three ``resolver_dependent`` tests are skipped with a reason (ruling R8),
    because they assert outcomes only the shipped ``DeterministicResolver`` produces.
    Leave it ``None`` and they are binding, whichever adapter you brought.

    ``include_nonbinding=False`` (the default) deselects tests marked ``nonbinding``,
    which are the ones PACKAGE.md declares outside the conformance definition. Pass
    ``True`` to run them anyway -- useful when you want the whole picture, never when
    you are deciding whether a backend conforms.
    """
    import pytest

    from . import _support

    marker = () if include_nonbinding else ("-m", "not nonbinding")
    previous = _support.EXTERNAL_FACTORY
    previous_resolver = _support.EXTERNAL_RESOLVER
    _support.EXTERNAL_FACTORY = adapter_factory
    _support.EXTERNAL_RESOLVER = resolver_factory
    try:
        return int(pytest.main(["--pyargs", "open_ontology.contract", *marker, *args]))
    finally:
        _support.EXTERNAL_FACTORY = previous
        _support.EXTERNAL_RESOLVER = previous_resolver
