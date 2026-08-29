"""Do INTERFACE.md and PACKAGE.md still describe the code? -- run them and find out.

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

**PACKAGE.md is checked the same way, added by row 3d (beacon finding U4).** That
finding was one more of the same family: 3.3's printed ``TypeRecord`` had lost
``retire_reason``, ``retired_by``, ``retired_at`` and ``successor`` -- four fields the
landed dataclass has and the document a third-party adapter author reads does not. The
fifteen INTERFACE shapes were mechanically checked and the ten PACKAGE ones were not,
so the drift moved into the half of the specification nobody was checking. The
difference from INTERFACE.md is only in shape: PACKAGE prints real ``@dataclass``
blocks rather than ``Name:`` sketches, so the parser reads a ``class X:`` header. Names
only, again -- the spec writes what a field *is called*, and a container type that
differs on purpose is not drift.

Run: ``python docs/tools/check_spec_drift.py`` -- exit 0 clean, 1 with a report.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / "docs" / "specs" / "INTERFACE.md"
PACKAGE = ROOT / "docs" / "specs" / "PACKAGE.md"
sys.path.insert(0, str(ROOT))

from open_ontology import adapter as adapter_module  # noqa: E402
from open_ontology import attributes as attributes_module  # noqa: E402
from open_ontology.contract import harness as harness_module  # noqa: E402
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
    "reinstate",
    "merge_types",
    "register_consumer",
    "record_use",
)

#: Fields the spec deliberately declines to print, with the reason. Empty is the goal;
#: an entry here is a decision on the record, not a way to silence the check.
SPEC_OMITS: dict[str, set[str]] = {}

#: PACKAGE.md prints these as real ``@dataclass`` blocks, and they are meant to BE the
#: whole record -- a third-party adapter author builds from them. ``{printed name:
#: (module, attribute)}``. Row 3d, beacon finding U4.
PACKAGE_SHAPES = {
    "Capabilities": (adapter_module, "Capabilities"),
    "TypeRecord": (adapter_module, "TypeRecord"),
    "ProposalRecord": (adapter_module, "ProposalRecord"),
    "ConsumerRecord": (adapter_module, "ConsumerRecord"),
    "UsageRecord": (adapter_module, "UsageRecord"),
    "EventRecord": (adapter_module, "EventRecord"),
    "TypeQuery": (adapter_module, "TypeQuery"),
    "TypePage": (adapter_module, "TypePage"),
    "ProposalQuery": (adapter_module, "ProposalQuery"),
    "FieldSpec": (attributes_module, "FieldSpec"),
    "AttributeSchema": (attributes_module, "AttributeSchema"),
    # 6.4 prints the two harness shapes a third-party author builds. They were
    # described only in a module 2.2 calls private until row 3d's third adversarial
    # round; printing them here means they cannot drift from the dataclasses either.
    "BorrowedHarness": (harness_module, "BorrowedHarness"),
    "SchemaHarness": (harness_module, "SchemaHarness"),
}

#: Same rule as SPEC_OMITS, for PACKAGE.md. An entry is a decision on the record.
PACKAGE_OMITS: dict[str, set[str]] = {}

_FENCE = re.compile(r"```(?:python)?\n(.*?)```", re.S)
_CLASS = re.compile(r"^class ([A-Z]\w*)[:(]", re.M)
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


def package_shape_fields(blocks: list[str], name: str) -> set[str] | None:
    """The field names PACKAGE.md prints for ``class <name>:``, or None if it prints none.

    PACKAGE prints executable-looking ``@dataclass`` blocks, so the header is
    ``class Name:`` and the body is four-space-indented ``field: type`` lines, often with
    a trailing comment. A method definition ends the record -- ``Capabilities`` prints
    none, but a future shape might.
    """
    for block in blocks:
        for m in _CLASS.finditer(block):
            if m.group(1) != name:
                continue
            body = block[m.end() :]
            end = re.search(r"^(?:@|class |\S)", body, re.M)
            if end:
                body = body[: end.start()]
            body = re.split(r"^    def ", body, maxsplit=1, flags=re.M)[0]
            # PACKAGE.md packs some records: `namespace: str; kind: str; name: str`.
            # Reading only the first field of such a line invents five findings that are
            # not drift, which is how a checker teaches people to ignore it.
            return {
                name
                for line in body.splitlines()
                for name in _FIELD.findall(
                    "\n".join("    " + part.strip() for part in line.split(";"))
                )
            }
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


# ---------------------------------------------------------------------------
# Closed vocabularies -- added by row #4's adversarial round 2.
#
# This checker diffed field NAMES and parameter NAMES and never enum CONTENTS,
# so INTERFACE.md 5.12's enumerated list and ``types.REFUSAL_REASONS`` could
# disagree and the gate would stay green. They did: row #4 added three values to
# both and left ``Refusal``'s own docstring and error message saying "fifteen".
# A reviewer found that by reading two files side by side, which is precisely
# what this file exists to make unnecessary.


#: Number words this checker can read out of prose. Both closed vocabularies state
#: their size in words, and a number the code does not derive is exactly the half that
#: goes stale -- three times so far in this repository.
_WORDS = {
    "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15,
    "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19, "twenty": 20,
    "twenty-one": 21, "twenty-two": 22, "twenty-three": 23, "twenty-four": 24,
    "twenty-five": 25, "twenty-six": 26, "twenty-seven": 27, "twenty-eight": 28,
    "twenty-nine": 29, "thirty": 30,
}


def _check_closed_vocabularies(spec_text: str) -> list[str]:
    """INTERFACE.md 5.12's enumerated values must equal ``types.REFUSAL_REASONS``."""
    problems: list[str] = []
    m = re.search(
        r"takes exactly these \*\*([\w-]+)\*\* values.*?:\n\n(.+?)\n",
        spec_text,
        re.S,
    )
    if m is None:
        return ["INTERFACE 5.12: could not find the enumerated Refusal.reason list"]
    printed = set(re.findall(r"`([a-z_]+)`", m.group(2)))
    actual = set(types_module.REFUSAL_REASONS)
    for name in sorted(printed - actual):
        problems.append(
            f"INTERFACE 5.12: {name!r} is enumerated in the document and absent "
            f"from types.REFUSAL_REASONS"
        )
    for name in sorted(actual - printed):
        problems.append(
            f"INTERFACE 5.12: {name!r} is in types.REFUSAL_REASONS and is not "
            f"enumerated in the document -- ruling R3 requires both in one change"
        )
    # The count word in the prose has to match too: a number a reader trusts and
    # the code does not derive is exactly the half that went stale.
    words = _WORDS
    _unused = {
        # Hyphenated from here on. Row 3e: the vocabulary reached twenty-one and this
        # check silently stopped working -- ``\w+`` does not cross a hyphen, so the
        # whole 5.12 block failed to parse and the checker reported "could not find the
        # enumerated list" instead of a wrong number. A checker that degrades into a
        # different error the moment the thing it checks grows has a shelf life, so the
        # words run to thirty and the pattern crosses a hyphen.
        "twenty-one": 21, "twenty-two": 22, "twenty-three": 23, "twenty-four": 24,
        "twenty-five": 25, "twenty-six": 26, "twenty-seven": 27, "twenty-eight": 28,
        "twenty-nine": 29, "thirty": 30,
    }
    said = words.get(m.group(1).lower())
    if said is not None and said != len(actual):
        problems.append(
            f"INTERFACE 5.12 says {m.group(1)!r} values; types.REFUSAL_REASONS "
            f"has {len(actual)}"
        )
    return problems


def _check_warning_vocabulary(spec_text: str) -> list[str]:
    """INTERFACE.md 5.4's table must equal ``types.WARNING_VALUES``.

    Added by row 3e's third adversarial round. 5.4 said "eighteen values" over a table
    that omitted ``gate_unregistered`` -- a value ruling R8 added in row 3d, that v0
    code emits, that ``C11-05`` tests, and that **the table's own last row named**.
    Nothing checked it, because this file held only 5.12's vocabulary. The two closed
    vocabularies are now held the same way, contents and count.

    Values carrying a ``:<detail>`` suffix are compared by their prefix, which is the
    part the vocabulary closes over.
    """
    problems = []
    m = re.search(r"`warnings` vocabulary, complete \u2014 ([\w-]+) values", spec_text)
    if m is None:
        return ["INTERFACE 5.4: could not find the warnings vocabulary heading"]
    block = spec_text[m.end():]
    cut = re.search(r"\n\s*---", block)
    if cut is not None:
        block = block[: cut.start()]
    printed = set(re.findall(r"^\| `([a-z_]+)[:`]", block, re.M))
    actual = set(types_module.WARNING_VALUES)
    for name in sorted(printed - actual):
        problems.append(
            f"INTERFACE 5.4: {name!r} is in the table and absent from "
            f"types.WARNING_VALUES"
        )
    for name in sorted(actual - printed):
        problems.append(
            f"INTERFACE 5.4: {name!r} is in types.WARNING_VALUES and absent from the "
            f"table -- a closed vocabulary nothing derives is one that quietly opens"
        )
    said = _WORDS.get(m.group(1).lower())
    if said is not None and said != len(actual):
        problems.append(
            f"INTERFACE 5.4 says {m.group(1)!r} values; types.WARNING_VALUES has "
            f"{len(actual)}"
        )
    return problems


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

    # --- PACKAGE.md's printed dataclasses. Row 3d, beacon finding U4.
    package_blocks = spec_blocks(PACKAGE.read_text(encoding="utf-8"))
    for printed, (module, attribute) in PACKAGE_SHAPES.items():
        cls = getattr(module, attribute, None)
        if cls is None or not hasattr(cls, "__dataclass_fields__"):
            problems.append(f"PACKAGE {printed}: {module.__name__} has no dataclass {attribute}")
            continue
        fields = package_shape_fields(package_blocks, printed)
        if fields is None:
            problems.append(
                f"PACKAGE {printed}: listed as a printed shape and PACKAGE.md prints no "
                f"`class {printed}:` block -- an adapter author has nothing to build from"
            )
            continue
        actual = set(cls.__dataclass_fields__)
        allowed = PACKAGE_OMITS.get(printed, set())
        for name in sorted(actual - fields - allowed):
            problems.append(
                f"PACKAGE {printed}.{name}: the code has it, PACKAGE.md's printed shape "
                f"does not -- a third-party adapter built from the document is wrong"
            )
        for name in sorted(fields - actual):
            problems.append(
                f"PACKAGE {printed}.{name}: printed by PACKAGE.md, absent from the code"
            )

    problems.extend(_check_closed_vocabularies(SPEC.read_text(encoding="utf-8")))
    problems.extend(_check_warning_vocabulary(SPEC.read_text(encoding="utf-8")))

    if problems:
        print("the specifications have drifted from the implementation:\n")
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
        f"implementation ({len(SHAPES)} shapes, {len(CALLS)} calls).\n"
        f"{PACKAGE.relative_to(ROOT)}: every printed dataclass matches the "
        f"implementation ({len(PACKAGE_SHAPES)} shapes).\n"
        f"INTERFACE.md 5.12: the closed Refusal.reason vocabulary matches "
        f"types.REFUSAL_REASONS ({len(types_module.REFUSAL_REASONS)} values), "
        f"contents and count.\n"
        f"INTERFACE.md 5.4: the closed warnings vocabulary matches "
        f"types.WARNING_VALUES ({len(types_module.WARNING_VALUES)} values)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
