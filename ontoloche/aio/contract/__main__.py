"""``python -m ontoloche.aio.contract --adapter pkg.mod:Class [args...]``

Runs the async conformance suite against a backend this package has never heard of --
which is the point of having an async protocol at all. The callable must be awaitable
and must return a fresh, empty store.
"""

from __future__ import annotations

import argparse
import importlib
import sys

from . import run_async_contract_suite


def _load(spec: str):
    """``pkg.mod:Name`` or ``pkg.mod:Class.classmethod``.

    The dotted form is not decoration. An async adapter's entry point is usually a
    classmethod, because ``__init__`` cannot await a connection (deviation D-A1), so
    ``AsyncSQLiteAdapter.open`` is the *normal* shape here rather than an exception.
    """
    module_name, _, attribute = spec.partition(":")
    if not attribute:
        raise SystemExit(f"--adapter wants pkg.mod:Name or pkg.mod:Class.method, got {spec!r}")
    target = importlib.import_module(module_name)
    for part in attribute.split("."):
        try:
            target = getattr(target, part)
        except AttributeError as exc:
            raise SystemExit(f"{module_name}:{attribute} -- no {part!r}") from exc
    return target


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m ontoloche.aio.contract")
    parser.add_argument(
        "--adapter",
        required=True,
        help="pkg.mod:Class -- an async zero-argument callable returning a fresh, empty store",
    )
    parser.add_argument(
        "--arg",
        action="append",
        default=[],
        help="an argument to pass to the adapter callable (repeatable)",
    )
    parser.add_argument(
        "--include-nonbinding",
        action="store_true",
        help=(
            "also run tests marked nonbinding -- the ones PACKAGE.md places outside "
            "the conformance definition. Never pass this when deciding conformance."
        ),
    )
    known, passthrough = parser.parse_known_args(argv)

    target = _load(known.adapter)

    async def factory():
        return await target(*known.arg)

    return run_async_contract_suite(
        factory, args=passthrough, include_nonbinding=known.include_nonbinding
    )


if __name__ == "__main__":
    sys.exit(main())
