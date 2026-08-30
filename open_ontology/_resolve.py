"""PRIVATE. The default deterministic resolver -- PACKAGE.md 2.6.

``resolve_type`` needs near-match scoring and ``propose_type`` needs ``near_matches``.
Both are model-shaped in production and must not be model-shaped in the contract suite,
or conformance becomes non-deterministic and a backend can fail for reasons that have
nothing to do with storage.

**Stated plainly: this resolver is not good enough for production and is not meant to
be.** It exists so the suite has a fixed point. ``Registry(adapter,
resolver=MyModelResolver())`` is the production path, and no contract test may pass or
fail because of resolver quality -- the suite asserts outcomes and shapes, never scores.

``tier`` is recorded into provenance and **not used** in scoring. The tier gate lives in
``approve`` (INTERFACE.md 2.7 point 3), not here.
"""

from __future__ import annotations

import difflib
import re
from typing import Any, Protocol, Sequence

from .types import NotAType, ResolveContext

__all__ = ["Resolver", "DeterministicResolver"]


class Resolver(Protocol):
    def score(
        self,
        candidate: str,
        context: ResolveContext,
        known: Sequence[Any],
        *,
        tier: str,
    ) -> list[tuple[str, float]]: ...

    def classify(
        self, candidate: str, context: ResolveContext, *, tier: str
    ) -> NotAType | None: ...


def identity_key(text: str) -> str:
    """The registry's notion of *the same word*. **The kill row's SEVENTH trip.**

    Two words are the same word here iff this function maps them to one string:
    lowercased, with every run of non-``[a-z0-9]`` collapsed to ``_`` and stripped.

    **It is public, and one function, because the seventh trip is what happens when
    there are two.** Every alias guard in `registry.py` found its collision by an exact
    byte comparison -- ``rec.name == alias``, ``alias in rec.aliases``, ``candidate in
    entry.aliases`` -- while this module scored ``identity_key(candidate)`` against
    ``identity_key(alias)`` and rated an exact match **1.0**. So ``'Commentable'`` was a
    word the guards had never heard of and the resolver answered at the confidence
    `INTERFACE.md` 5.3 calls a **guarantee**:

    * `merge_types` refuses `commentable` / `searchable` NON-OVERRIDABLY when their
      extents differ, under every acknowledgement;
    * `import_types` writing ``aliases: ["commentable"]`` is refused `predicate_merge`;
    * `import_types` writing ``aliases: ["Commentable"]`` was **written, unrefused**;
    * `resolve_type("commentable")` then answered `searchable` at **1.0**, extents still
      different, carrying no warning at all.

    **[Observed]** on both fully-capable legs and the async mirror, row 4d's first
    adversarial round, with all five gates green.

    Trips 1-5 were *the guard did not look properly*. Trip 6 was *the guard looked
    correctly, and then the fact changed*. Trip 7 is **the guard and the resolver
    disagreeing about what the same word is** -- and every operand of Rule U so far has
    been about the EXTENT comparison, while nothing in this project had written down the
    identity of the **name**.

    **Why the key lives beside the resolver rather than in `registry.py`.** The registry
    must not be able to disagree with the scorer that delivers its 1.0; putting the key
    here, and importing it there, is the arrangement in which they cannot. It is a
    property of *words in this vocabulary*, not of any one resolver's scoring: a
    deployment supplying its own `Resolver` (`PACKAGE.md` 2.6's production path) changes
    what SCORES alike, never what counts as one word, and the guards are keyed to this
    rather than to whatever that resolver happens to do -- which is `C3-11`'s own
    argument, one layer down.

    Non-canonical words only ever reach the store through an **alias**: `propose_type`
    puts every `name` through `NAME_RE`, so a row can never be called ``'Commentable'``.
    A dump's alias list is validated by nothing, and `import_types` is UC1's Foundry
    migration path.
    """
    return re.sub(r"[^a-z0-9]+", "_", (text or "").lower()).strip("_")


#: The old private name, kept so nothing in this module has to change shape. Row 4d.
_norm = identity_key


def _similar(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, a, b).ratio()


# The composite-projection families. A candidate that names the whole is a redundant
# projection when its parts arrived alongside it as separate columns -- INTERFACE.md
# 10.2 / T3: CMS `Location` is exactly rebuilt from four sibling columns in 419,428 of
# 419,479 rows and 400 of 400 in the sample.
_PROJECTION_FAMILIES: dict[str, frozenset[str]] = {
    "location": frozenset(
        {
            "address",
            "provider_address",
            "street",
            "street_address",
            "city",
            "city_town",
            "town",
            "state",
            "province",
            "zip",
            "zip_code",
            "postal_code",
            "postcode",
            "country",
        }
    ),
    "address": frozenset(
        {
            "street",
            "street_address",
            "address_line_1",
            "address_line_2",
            "city",
            "city_town",
            "town",
            "state",
            "zip",
            "zip_code",
            "postal_code",
            "country",
        }
    ),
    "full_name": frozenset({"first_name", "last_name", "middle_name", "given_name", "surname"}),
    "full_address": frozenset(
        {"address", "provider_address", "city", "city_town", "state", "zip", "zip_code"}
    ),
}

_MIN_PROJECTION_PARTS = 3

# Names that stamp an export rather than describe the subject -- T7: CMS
# `Processing Date` holds one value (2026-08-01) for every row in the file.
_ARTEFACT_NAME = re.compile(
    r"^(processing|process|export|extract|extraction|run|load|refresh|ingest|as_of|asof|snapshot|"
    r"file|batch|report)_(date|time|timestamp|ts|dt|datetime|stamp|id|version)$"
)

_DERIVED_NAME = re.compile(r"^(days_to_|days_since_|num_|n_|pct_|percent_|ratio_)|(_count|_total|_avg|_pct|_rate)$")

_INSTANCE_LOOKING = re.compile(r"[A-Z]{2,}|,\s*(inc|llc|ltd|corp)\b", re.IGNORECASE)


class DeterministicResolver:
    """``difflib`` over names and definitions, plus a rule-based ``classify``."""

    def score(
        self,
        candidate: str,
        context: ResolveContext,
        known: Sequence[Any],
        *,
        tier: str,
    ) -> list[tuple[str, float]]:
        cand = _norm(candidate)
        hint = (context.definition_hint or "").strip().lower()
        scored: list[tuple[str, float]] = []
        for entry in known:
            name = getattr(entry, "name", None)
            if not name:
                continue
            by_name = _similar(cand, _norm(name))
            aliases = getattr(entry, "aliases", ()) or ()
            for alias in aliases:
                by_name = max(by_name, _similar(cand, _norm(alias)))
            by_def = 0.0
            if hint:
                definition = (getattr(entry, "definition", "") or "").strip().lower()
                if definition:
                    by_def = _similar(hint, definition)
            # Name dominates. A definition that happens to read alike is weak evidence
            # next to the word itself, and weighting it higher makes every entry with a
            # long definition look like a match for everything.
            scored.append((name, round(max(by_name, 0.65 * by_name + 0.35 * by_def), 4)))
        scored.sort(key=lambda pair: (-pair[1], pair[0]))
        return scored

    def classify(
        self, candidate: str, context: ResolveContext, *, tier: str
    ) -> NotAType | None:
        cand = _norm(candidate)
        siblings = {_norm(c) for c in context.sibling_columns}

        # 1. redundant projection -- the whole arrived alongside enough of its parts.
        for head, parts in _PROJECTION_FAMILIES.items():
            if cand != head:
                continue
            overlap = sorted(siblings & parts)
            if len(overlap) >= _MIN_PROJECTION_PARTS:
                return NotAType(
                    "redundant_projection",
                    {
                        "rebuilt_from": overlap,
                        "why": (
                            f"{candidate!r} is a projection of columns that arrived with it "
                            f"({', '.join(overlap)}); it is not a second thing"
                        ),
                    },
                )

        values = list(context.sample_values)
        distinct = {repr(v) for v in values}

        # 2. export artefact -- a stamp on the file, not a fact about the subject. Both
        # signals are required: single-valuedness alone would kill `survey_type`, which
        # is single-valued in this slice only (ground truth T7 says so explicitly).
        if _ARTEFACT_NAME.match(cand):
            if len(values) >= 2 and len(distinct) == 1:
                return NotAType(
                    "export_artefact",
                    {
                        "distinct_values": 1,
                        "sampled": len(values),
                        "value": values[0],
                        "why": (
                            f"{candidate!r} holds one value across {len(values)} sampled rows; "
                            "it stamps the export, it does not describe the subject"
                        ),
                    },
                )
            if not values:
                return NotAType(
                    "export_artefact",
                    {"why": f"{candidate!r} names an export stamp rather than a subject"},
                )

        # 3. derived value -- computed from other columns rather than observed.
        if _DERIVED_NAME.search(cand) and all(isinstance(v, (int, float)) for v in values):
            return NotAType(
                "derived_value",
                {"why": f"{candidate!r} names a computed quantity, not a thing that exists"},
            )

        # 4. an instance wearing a type's clothes.
        if _INSTANCE_LOOKING.search(candidate) and " " in candidate.strip():
            return NotAType(
                "instance_not_type",
                {"why": f"{candidate!r} reads as one instance, not as a class of them"},
            )

        return None
