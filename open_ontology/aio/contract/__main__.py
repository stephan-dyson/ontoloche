"""``python -m open_ontology.aio.contract --adapter pkg.mod:Class [args...]``

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
    module_name, _, attribute = spec.partition(":")
    if not attribute:
        raise SystemExit(f"--adapter wants pkg.mod:Class, got {spec!r}")
    module = importlib.import_module(module_name)
    try:
        return getattr(module, attribute)
    except AttributeError as exc:
        raise SystemExit(f"{module_name} has no {attribute!r}") from exc


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m open_ontology.aio.contract")
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
    known, passthrough = parser.parse_known_args(argv)

    target = _load(known.adapter)

    async def factory():
        return await target(*known.arg)

    return run_async_contract_suite(factory, args=passthrough)


if __name__ == "__main__":
    sys.exit(main())
