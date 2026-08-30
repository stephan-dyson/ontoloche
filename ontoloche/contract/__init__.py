"""The contract suite -- the definition of conformance.

    A backend is conformant iff the whole suite passes against it.

The suite ships *inside* the package on purpose: a third-party backend author has to be
able to run the thing that decides whether their backend is correct, without cloning
this repository.

    pytest --pyargs ontoloche.contract
    python -m ontoloche.contract --adapter beacon.ontology:WorkLinkTypeAdapter

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
    borrowed_factory: Callable[[], Any] | None = None,
    schema_harness_factory: Callable[[], Any] | None = None,
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

    ``borrowed_factory`` supplies a :class:`~ontoloche.contract._support.
    BorrowedHarness` -- an adapter of yours opened over a connection **you** own, plus
    the handles ``C0-12`` needs to watch your host transaction. Supply it if your adapter
    declares ``transaction_scope="savepoint"``; without it that declaration is taken on
    trust and the run says so in its coverage block (PACKAGE.md 6.4). Row 3d added this
    after an adversarial reviewer got a deliberately-lying savepoint adapter to a clean
    CONFORMANT verdict.

    ``schema_harness_factory`` is its sibling for ``owns_schema=False`` -- a store
    whose schema does not exist yet, plus the host's own migration -- so ``C0-09``
    can prove that your ``migrate()`` really is verify-only. Same rule: without it the
    declaration is taken on trust and the run says so.

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
    previous_borrowed = _support.EXTERNAL_BORROWED
    previous_schema = _support.EXTERNAL_SCHEMA_HARNESS
    _support.EXTERNAL_FACTORY = adapter_factory
    _support.EXTERNAL_RESOLVER = resolver_factory
    _support.EXTERNAL_BORROWED = borrowed_factory
    _support.EXTERNAL_SCHEMA_HARNESS = schema_harness_factory
    try:
        return int(pytest.main(["--pyargs", "ontoloche.contract", *marker, *args]))
    finally:
        _support.EXTERNAL_FACTORY = previous
        _support.EXTERNAL_RESOLVER = previous_resolver
        _support.EXTERNAL_BORROWED = previous_borrowed
        _support.EXTERNAL_SCHEMA_HARNESS = previous_schema
