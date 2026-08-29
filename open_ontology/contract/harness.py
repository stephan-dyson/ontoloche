"""The two harnesses a third-party backend supplies to have its *declarations* checked.

**Public, and public because a reviewer was right that it was not** *(row 3d, third
adversarial round)*. `run_contract_suite(borrowed_factory=…)` and
`--borrowed pkg.mod:make_harness` require an object of a particular shape, and that
shape was described only in `contract/_support.py` — a module `PACKAGE.md` §2.2
classifies as private and tells third parties not to import. An author building strictly
from the document, which §3.1 says is the whole point of having a protocol, had no
public way to learn what fields the object needs.

    from open_ontology.contract.harness import BorrowedHarness, SchemaHarness

Both are plain frozen dataclasses of callables and nothing checks their type: an object
with the same attributes does just as well. They are exported so the shape is
*writable down*, not to make it mandatory.

**Why they exist at all.** `Capabilities` carries two declarations the suite cannot
check from the outside:

``transaction_scope="savepoint"``
    *"I never commit; the host owns the transaction."* Verified by `C0-12` (the
    savepoint semantics), `C0-13` (the host-transaction precondition) and `C0-14`
    (scopes on one connection must nest) — all of which need a connection **you** own,
    which the suite cannot conjure. Supply a :class:`BorrowedHarness`.

``owns_schema=False``
    *"``migrate()`` verifies and issues no DDL."* Verified by `C0-09`, which needs a
    store whose schema does not exist yet plus your host's own migration. Supply a
    :class:`SchemaHarness`.

Supplying neither is allowed and leaves a backend conformant — but the run then reports
`CONFORMANT, DECLARATIONS UNVERIFIED` and names what nobody checked (`PACKAGE.md` §6.4).
Every one of these tests was, before row 3d, unrunnable against a third-party adapter,
and every corresponding lie ran the whole suite to a clean pass.

**The async suite takes the same shapes with coroutine callables.** `await`-ing each
field is the only difference; import them from ``open_ontology.aio.contract._support``
there, or hand over any object with the same attributes.
"""

from __future__ import annotations

from ._support import BorrowedHarness, SchemaHarness

__all__ = ["BorrowedHarness", "SchemaHarness"]
