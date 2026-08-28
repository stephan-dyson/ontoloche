"""``attributes`` -- the schema-per-kind mechanism. PACKAGE.md 5.

INTERFACE.md 2.1 says ``attributes`` is opaque to v0 and the registry never reads them.
That is true of an untouched deployment and stays true here, because **the default mode
is ``off``**: a #2 that validated by default would change #1's contract unilaterally.

What happens unconditionally, in every mode, is the census: every distinct attribute
key ever written is recorded. That does not solve the escape hatch, it makes it
enumerable -- the same move as ``ConsumerReport.complete = False``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

__all__ = [
    "FieldSpec",
    "AttributeSchema",
    "AttributeCensus",
    "CensusEntry",
    "validate_attributes",
    "MODES",
    "ADDITIONAL",
]

MODES = ("off", "warn", "enforce")
ADDITIONAL = ("allow", "warn", "forbid")

_PY_TYPES: dict[str, tuple[type, ...]] = {
    "str": (str,),
    "int": (int,),
    "float": (float, int),
    "bool": (bool,),
    "list": (list, tuple),
    "dict": (dict,),
    "datetime": (datetime,),
}


@dataclass(frozen=True)
class FieldSpec:
    """``description`` is required and non-empty, on exactly the reasoning of
    INTERFACE.md 2.1's non-empty ``definition``: an undescribed field is how the escape
    hatch re-forms one level down."""

    type: str
    description: str
    required: bool = False
    enum: tuple[Any, ...] | None = None
    item_type: str | None = None

    def __post_init__(self) -> None:
        if self.type not in _PY_TYPES:
            raise ValueError(f"FieldSpec.type must be one of {tuple(_PY_TYPES)}, got {self.type!r}")
        if not self.description or not self.description.strip():
            raise ValueError("FieldSpec.description is required and must be non-empty")
        if self.enum is not None:
            object.__setattr__(self, "enum", tuple(self.enum))


@dataclass(frozen=True)
class AttributeSchema:
    """Deployment configuration, versioned per ``(namespace, kind)``.

    Not a ``TypeEntry`` with ``kind="attribute_schema"``: an attribute schema is not a
    word in the vocabulary, and putting it in the type store means ``list_types()``
    mixes schemas with vocabulary and ``merge_types`` can be pointed at one.
    """

    namespace: str
    kind: str
    version: int
    fields: dict[str, FieldSpec]
    additional: str = "allow"
    mode: str = "off"
    registered_at: datetime | None = None
    registered_by: str = "deployment"

    def __post_init__(self) -> None:
        if self.mode not in MODES:
            raise ValueError(f"AttributeSchema.mode must be one of {MODES}")
        if self.additional not in ADDITIONAL:
            raise ValueError(f"AttributeSchema.additional must be one of {ADDITIONAL}")
        if self.version < 1:
            raise ValueError("AttributeSchema.version is monotonic from 1")


def _type_ok(value: Any, spec_type: str) -> bool:
    if spec_type == "bool":
        return isinstance(value, bool)
    if spec_type in ("int", "float") and isinstance(value, bool):
        return False  # bool is an int in Python; it is not an int here
    return isinstance(value, _PY_TYPES[spec_type])


def validate_attributes(schema: AttributeSchema, attributes: dict[str, Any]) -> list[str]:
    """Return one ``<field>:<why>`` string per violation. Empty means valid.

    Per-field only. Cross-field rules ("a symmetric edge must have no inverse label")
    are deliberately absent: a rule language here would be a schema language, which is
    a much larger thing than v0 needs (PACKAGE.md 5.6).
    """
    problems: list[str] = []
    for name, spec in schema.fields.items():
        if name not in attributes:
            if spec.required:
                problems.append(f"{name}:required field missing")
            continue
        value = attributes[name]
        if not _type_ok(value, spec.type):
            problems.append(f"{name}:expected {spec.type}, got {type(value).__name__}")
            continue
        if spec.enum is not None and value not in spec.enum:
            problems.append(f"{name}:{value!r} is not one of {list(spec.enum)}")
        if spec.type == "list" and spec.item_type:
            for i, item in enumerate(value):
                if not _type_ok(item, spec.item_type):
                    problems.append(f"{name}:item {i} expected {spec.item_type}")
                    break
    if schema.additional != "allow":
        for name in attributes:
            if name not in schema.fields:
                problems.append(f"{name}:not declared in the schema")
    return problems


@dataclass(frozen=True)
class CensusEntry:
    kind: str
    key: str
    n: int
    first_seen: datetime
    last_seen: datetime
    example: Any
    declared: bool
    schema_versions: tuple[int | None, ...]


@dataclass(frozen=True)
class AttributeCensus:
    """Ruling R2: package-local, outside the conformance definition.

    ``complete`` is False when the backend cannot store attributes at all -- there is
    then nothing to census, and saying "no keys" would be a claim.
    """

    namespace: str
    entries: tuple[CensusEntry, ...] = ()
    known: int | None = 0
    complete: bool = True
    why_incomplete: str | None = None
