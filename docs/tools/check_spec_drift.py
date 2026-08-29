"""Does INTERFACE.md still describe the code? -- run it and find out.

Six consecutive adversarial review rounds on `docs/specs/INTERFACE.md` each found at
least one defect of **the same family**: a printed data shape or signature that had
drifted from the reference implementation.

    round 1  `Resolution` and `predicates()` were missing Rule K's fields
    round 2  `register_consumer` was declared `-> Consumer`; it returns `| Refusal`
    round 3  `propose_type`'s third outcome was undocumented
    round 4  `PredicateEntry.extent_size` was typed `int`; the code says `int | None`
    round 5  `MergeResult` had no printed shape at all
    round 6  `merge_types` was missing `into_namespace`; `TypeEntry` was missing two fields

Every one was found by a human-shaped reader comparing two files by eye, and every one
had survived earlier readers doing the same thing. That is a job for a script.

**What this checks, and what it deliberately does not.** It compares the *names* of
fields in the spec's fenced ``Shape:`` blocks against the dataclass in ``types.py``, and
the *parameter names* of the spec's ``def`` blocks against the method on ``Registry``.
It does **not** compare types or defaults: the spec writes ``list[str]`` where the code
writes ``tuple[str, ...]`` on purpose, because the spec describes a contract and the
implementation chose immutability (deviation D-12's neighbourhood). Names are where the
drift that mattered actually happened -- a missing field is invisible to a reader, a
different container is not.

A shape the spec prints that the code does not have, or a field the code returns that
the spec never mentions, is a finding either way: the first misleads an implementer, the
second is a surface nobody agreed to.

Run: ``python docs/tools/check_spec_drift.py`` -- exit 0 clean, 1 with a report.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / "docs" / "specs" / "INTERFACE.md"
sys.path.insert(0, str(ROOT))

from open_ontology import registry as registry_module  # noqa: E402
from open_ontology import types as types_module  # noqa: E402

#: Shapes the spec prints as ``Name:`` inside a fenced block, and their dataclass.
#: A shape is listed here only when the spec means it to be the whole record.
SHAPES = {
    "Provenance": "Provenance",
    "Evidence": "Evidence",
    "Citation": "Citation",
    "Consumer": "Consumer",
    "ConsumerReport": "ConsumerReport",
    "PredicateEntry": "PredicateEntry",
    "PredicateListing": "PredicateListing",
    "ResolveContext": "ResolveContext",
    "Resolution": "Resolution",
    "Proposal": "Proposal",
    "Refusal": "Refusal",
    "Rejection": "Rejection",
    "MergeResult": "MergeResult",
    "TypeListing": "TypeListing",
    "UsageReport": "UsageReport",
}

#: Calls the spec prints as ``def name(...)``, and the Registry method they describe.
CALLS = (
    "consumers",
    "predicates",
    "resolve_type",
    "propose_type",
    "approve",
    "reject",
    "list_types",
    "usage",
    "provenance",
    "retire",
    "merge_types",
    "register_consumer",
    "record_use",
)

#: Fields the spec deliberately declines to print, with the reason. Empty is the goal;
#: an entry here is a decision on the record, not a way to silence the check.
SPEC_OMITS: dict[str, set[str]] = {}

_FENCE = re.compile(r"```(?:python)?\n(.*?)```", re.S)
_FIELD = re.compile(r"^\s{4}([a-z_][a-z0-9_]*)\s*:", re.M)
_TABLE_FIELD = re.compile(r"^\|\s*`([a-z_][a-z0-9_]*)`\s*\|", re.M)


def spec_blocks(text: str) -> list[str]:
    return [m.group(1) for m in _FENCE.finditer(text)]


def shape_fields(blocks: list[str], name: str) -> set[str] | None:
    """The field names the spec prints for ``name:``, or None if it prints none."""
    for block in blocks:
        for chunk in re.split(r"\n(?=\S)", block):
            if chunk.lstrip().startswith(f"{name}:"):
                return set(_FIELD.findall(chunk))
    return None


def call_params(blocks: list[str], name: str) -> set[str] | None:
    for block in blocks:
        m = re.search(rf"def {re.escape(name)}\((.*?)\)\s*->", block, re.S)
        if m:
            body = re.sub(r"#[^\n]*", "", m.group(1))
            found = set()
            for part in re.split(r",(?![^\[\]]*\])", body):
                part = part.strip()
                if not part or part == "*":
                    continue
                found.add(part.split(":")[0].split("=")[0].strip().lstrip("*"))
            return found - {""}
    return None


def main() -> int:
    text = SPEC.read_text(encoding="utf-8")
    blocks = spec_blocks(text)
    problems: list[str] = []

    # --- TypeEntry is a table, not a fenced block (2.1).
    table = set(_TABLE_FIELD.findall(text))
    actual = set(types_module.TypeEntry.__dataclass_fields__)
    missing = sorted(actual - table - SPEC_OMITS.get("TypeEntry", set()))
    if missing:
        problems.append(
            f"TypeEntry: the code returns {missing} and 2.1's field table never lists "
            f"them -- an implementer building from the table alone gets the wrong type"
        )

    for spec_name, cls_name in SHAPES.items():
        cls = getattr(types_module, cls_name, None)
        if cls is None or not hasattr(cls, "__dataclass_fields__"):
            problems.append(f"{spec_name}: types.py has no dataclass {cls_name}")
            continue
        printed = shape_fields(blocks, spec_name)
        if printed is None:
            problems.append(
                f"{spec_name}: the spec names it in a signature but never prints its "
                f"shape -- 13's exit criterion says every call has one"
            )
            continue
        actual = set(cls.__dataclass_fields__)
        allowed = SPEC_OMITS.get(spec_name, set())
        for field in sorted(actual - printed - allowed):
            problems.append(f"{spec_name}.{field}: returned by the code, absent from the spec")
        for field in sorted(printed - actual):
            problems.append(f"{spec_name}.{field}: printed by the spec, absent from the code")

    for call in CALLS:
        method = getattr(registry_module.Registry, call, None)
        if method is None:
            problems.append(f"{call}(): the spec declares it; Registry has no such method")
            continue
        import inspect

        actual = set(inspect.signature(method).parameters) - {"self"}
        printed = call_params(blocks, call)
        if printed is None:
            problems.append(f"{call}(): no signature printed in the spec")
            continue
        for name in sorted(actual - printed):
            problems.append(
                f"{call}(): the implementation takes {name!r} and the spec's signature "
                f"does not -- a reader implementing from the spec cannot reach it"
            )
        for name in sorted(printed - actual):
            problems.append(f"{call}(): the spec declares {name!r}; the code does not take it")

    if problems:
        print(f"{SPEC.relative_to(ROOT)} has drifted from the implementation:\n")
        for p in problems:
            print(f"  - {p}")
        print(
            f"\n{len(problems)} problem(s). Every one of these was, at least once, found "
            "by a human reading two files side by side. Fix the spec, or record the "
            "divergence in SPEC_OMITS with a reason."
        )
        return 1

    print(
        f"{SPEC.relative_to(ROOT)}: every printed shape and signature matches the "
        f"implementation ({len(SHAPES)} shapes, {len(CALLS)} calls)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
