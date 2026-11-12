"""Does every Foundry fixture row 8a commits have Palantir's published shape? -- check it.

R106 route 2. The brief said a fixture passes when ``foundry-platform-sdk`` parses it.
**[Observed] Palantir's own fake Foundry does not meet that bar**: the documents its
``FauxOntology`` emits fail the SDK's ``OntologyFullMetadata`` model, 35 errors for the
employee ontology and 124 for the legacy default ontology, almost all of them placeholder
RIDs (``"rid"``, ``"rid.link-type.327"``) that do not match the SDK's RID pattern
(``8A-RUN.md`` §0.1 item 2).

So the check is an ALLOW-LIST rather than a parse, pre-registered in ``8A-RUN.md`` §0.5:

* a ``string_pattern_mismatch`` on a field named ``rid`` or ``linkTypeRid`` is allowed in
  the two GENERATED fixtures, because it is Palantir's placeholder, not a shape error;
* every other error must sit at one of the exact locations pinned below, per fixture;
* anything else fails, and so does a pinned location that no longer errors -- a stale
  allow-list entry is a hole somebody thinks is still being watched.

The hand-built fixtures get no RID allowance at all. They are written by this row, so
they are held to the stricter standard.

**This is not in the contract suite**, because the contract suite is what a third-party
backend installs, and the SDK is a test-only dependency under the ``foundry-fixtures``
extra (``pip install -e .[foundry-fixtures]``).

Run: ``python docs/tools/check_foundry_fixtures.py`` -- exit 0 clean, 1 with a report, 2
when the SDK is not installed.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "ontoloche" / "contract" / "fixtures"

#: Fields whose placeholder values the GENERATED fixtures may carry.
RID_FIELDS = frozenset({"rid", "linkTypeRid"})

#: ``{fixture: (allow placeholder RIDs?, {(error type, dotted location), ...})}``.
PINNED: dict[str, tuple[bool, set[tuple[str, str]]]] = {
    "foundry_faux_employee.json": (True, set()),
    "foundry_faux_legacy.json": (
        True,
        {
            # Palantir's deliberately unsupported data type, in `ActionTypeWithUnsupportedTypes`.
            ("union_tag_invalid", "actionTypes.unsupportedAction.parameters.unsupportedProperty.dataType"),
            # `editTodo`'s parameters omit `displayName`, which the SDK requires.
            ("missing", "actionTypes.editTodo.parameters.id.displayName"),
            ("missing", "actionTypes.editTodo.parameters.text.displayName"),
            ("missing", "actionTypes.editTodo.parameters.completed.displayName"),
        },
    ),
    "foundry_edge_cases.json": (
        False,
        {
            # The published ReleaseStatus has no EXAMPLE (8A-RUN.md §0.1 item 3). The
            # fixture carries it on purpose, to exercise the hold.
            ("literal_error", "objectTypes.ExampleThing.objectType.status"),
        },
    ),
    "foundry_uc2_cms.json": (False, set()),
    "foundry_uc3_nyc.json": (False, set()),
}


def check() -> list[str]:
    try:
        from foundry_sdk.v2.ontologies.models import OntologyFullMetadata
        from pydantic import ValidationError
    except ImportError as exc:  # pragma: no cover - environment
        print(f"foundry-platform-sdk is not installed ({exc}); pip install -e .[foundry-fixtures]")
        sys.exit(2)

    problems: list[str] = []
    on_disk = {p.name for p in FIXTURES.glob("foundry_*.json")}
    for name in sorted(on_disk - set(PINNED)):
        problems.append(f"{name}: a Foundry fixture this checker has no entry for")
    for name, (allow_rids, pinned) in sorted(PINNED.items()):
        path = FIXTURES / name
        if not path.exists():
            problems.append(f"{name}: pinned here and missing on disk")
            continue
        doc = json.loads(path.read_text(encoding="utf-8"))
        try:
            OntologyFullMetadata.model_validate(doc)
            errors = []
        except ValidationError as exc:
            errors = exc.errors()
        seen: set[tuple[str, str]] = set()
        rid_placeholders = 0
        for err in errors:
            loc = ".".join(str(part) for part in err["loc"])
            key = (err["type"], loc)
            if (
                allow_rids
                and err["type"] == "string_pattern_mismatch"
                and str(err["loc"][-1]) in RID_FIELDS
            ):
                rid_placeholders += 1
                continue
            if key in pinned:
                seen.add(key)
                continue
            problems.append(f"{name}: unexpected {err['type']} at {loc}: {err.get('msg')}")
        for key in sorted(pinned - seen):
            problems.append(f"{name}: pinned {key[0]} at {key[1]} no longer errors")
        print(
            f"{name}: {len(errors)} SDK error(s), {rid_placeholders} placeholder RID(s), "
            f"{len(seen)} pinned"
        )
    return problems


def main() -> int:
    problems = check()
    if problems:
        print("\n".join(problems))
        return 1
    print("check_foundry_fixtures: OK -- every fixture has the published shape, up to the pinned list.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
