"""``python -m open_ontology.contract --adapter pkg.mod:Class [args...]``

Runs the conformance suite against a backend this package has never heard of. That is
the point of having a protocol: conformance must be checkable by people who did not
write this package.
"""

from __future__ import annotations

import argparse
import importlib
import sys

from . import run_contract_suite


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
    parser = argparse.ArgumentParser(prog="python -m open_ontology.contract")
    parser.add_argument(
        "--adapter",
        required=True,
        help="pkg.mod:Class -- a zero-argument callable returning a fresh, empty store",
    )
    parser.add_argument(
        "--arg",
        action="append",
        default=[],
        help="an argument to pass to the adapter callable (repeatable)",
    )
    known, passthrough = parser.parse_known_args(argv)

    target = _load(known.adapter)

    def factory():
        return target(*known.arg)

    return run_contract_suite(factory, args=passthrough)


if __name__ == "__main__":
    sys.exit(main())
