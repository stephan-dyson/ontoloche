"""``attributes`` -- the schema-per-kind mechanism. PACKAGE.md 5.

INTERFACE.md 2.1 says ``attributes`` is opaque to v0 and the registry never reads them.
That is true of an untouched deployment and stays true here, because **the default mode
is ``off``**: a #2 that validated by default would change #1's contract unilaterally.

What happens unconditionally, in every mode, is the census: every distinct attribute
key ever written is recorded. That does not solve the escape hatch, it makes it
enumerable -- the same move as ``ConsumerReport.complete = False``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

#: INTERFACE.md 2.1's type-name grammar. Duplicated rather than imported because
#: PACKAGE.md 2.2 keeps this module free of registry imports.
_NAME_RE = re.compile(r"^[a-z][a-z0-9_]{0,63}$")

__all__ = [
    "FieldSpec",
    "AttributeSchema",
    "AttributeCensus",
    "CensusEntry",
    "validate_attributes",
    "strictest",
    "MODES",
    "ADDITIONAL",
]

#: Weakest first. The order is load-bearing: ruling R10's name-level schemas shadow the
#: per-kind one's FIELDS, and a shadow that also carried the mode would make an override
#: an exemption -- a one-line, unreviewed opt-out of a kind's governance, which in UC3
#: is one agency turning off a rule dozens publish under. So the fields are replaced and
#: the STRICTNESS is a floor: PACKAGE.md 5.2b rule 3.
MODES = ("off", "warn", "enforce")
ADDITIONAL = ("allow", "warn", "forbid")


def strictest(*values: str, order: tuple[str, ...]) -> str:
    """The strongest of several ``MODES`` / ``ADDITIONAL`` values."""
    return max(values, key=order.index)

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
    """Deployment configuration, versioned per ``(namespace, kind, name)``.

    Not a ``TypeEntry`` with ``kind="attribute_schema"``: an attribute schema is not a
    word in the vocabulary, and putting it in the type store means ``list_types()``
    mixes schemas with vocabulary and ``merge_types`` can be pointed at one.

    **``name`` is ruling R10, row 3e.** ``None`` -- the default -- is the per-kind
    schema this mechanism shipped with, unchanged. A schema with a ``name`` applies to
    exactly that one type and **shadows** the per-kind schema for it; nothing merges,
    because a merge of two field maps would silently produce a third schema nobody
    wrote (PACKAGE.md 5.2).

    The finding it closes is the mechanism's own flagship justification, asserted by
    ``C15-07``: PACKAGE.md 5.1 justifies this whole section on the CMS scope-and-
    severity ordering, and CMS has **two** ``kind="value_set"`` entries with different
    shapes. One schema per kind gets one of two wrong answers and there is no third --
    ``ordering`` required refuses the unordered set for lacking a field it has no
    business having, and ``ordering`` optional lets the ordered set be created
    declaring no order, which is the CMS severity scale back inside somebody's
    transform, unversioned.
    """

    namespace: str
    kind: str
    version: int
    fields: dict[str, FieldSpec]
    additional: str = "allow"
    mode: str = "off"
    registered_at: datetime | None = None
    registered_by: str = "deployment"
    #: ``None`` = the per-kind schema. A string = this type only, shadowing it. R10.
    name: str | None = None

    def __post_init__(self) -> None:
        if self.mode not in MODES:
            raise ValueError(f"AttributeSchema.mode must be one of {MODES}")
        if self.additional not in ADDITIONAL:
            raise ValueError(f"AttributeSchema.additional must be one of {ADDITIONAL}")
        if self.version < 1:
            raise ValueError("AttributeSchema.version is monotonic from 1")
        if self.name is not None:
            # An empty string is the STORE's sentinel for "no name" (PACKAGE.md 5.2b);
            # letting a caller pass one would make two different things one value. And a
            # name that cannot match any type is dead configuration stored silently --
            # in UC3, a typo in one agency's deployment config that governs nothing and
            # says nothing. Both are refused loudly here rather than found later.
            if not _NAME_RE.match(self.name):
                raise ValueError(
                    f"AttributeSchema.name is either None (the per-kind schema) or a "
                    f"type name matching {_NAME_RE.pattern} (INTERFACE.md 2.1); "
                    f"{self.name!r} can never match a type, so the schema would govern "
                    f"nothing"
                )


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
    """``declared`` is ``bool | None`` -- Rule U, after ruling R10 made the answer
    depend on which type.

    A census row is ``(kind, key)`` over every type of that kind, and since R10 a key
    can be declared by a name-level schema for one name and by nothing for the rest. A
    flat ``False`` there is a confident negative about a key that is *required*
    somewhere -- in the CMS fixture R10 exists for, on the call whose whole job is
    making the escape hatch enumerable.

    * ``True``  -- the per-kind schema declares it, so it is declared for every name.
    * ``False`` -- neither the per-kind schema nor any name-level schema declares it.
    * ``None``  -- the per-kind schema does not and at least one name-level schema
      does, so the answer depends on which type. ``declared_why`` names them.
    """

    kind: str
    key: str
    n: int
    first_seen: datetime
    last_seen: datetime
    example: Any
    declared: bool | None
    schema_versions: tuple[int | None, ...]
    declared_why: str | None = None


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
