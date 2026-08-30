# ---------------------------------------------------------------------------------
# GENERATED FILE -- do not edit. Edit open_ontology/contract/test_c6_list_types.py and run:
#
#     python tools/unasync.py
#
# The sync module is the single source of truth; this is its mechanical async mirror
# (deliverable 3b). open_ontology/aio/contract/test_generated_matches_source.py fails
# if this file and its source have drifted apart.
# ---------------------------------------------------------------------------------

"""C6 -- ``list_types`` (9). Mechanism 2: nobody could find the existing types."""

from __future__ import annotations
import pytest
from datetime import timedelta
from open_ontology.aio.contract._support import seed
from open_ontology.aio.contract.doubles import AsyncDegradedAdapter


@pytest.mark.requires_capability("indexes_membership")
async def test_c6_01_any_filter_that_hid_rows_makes_the_listing_incomplete(registry):
    await seed(registry, "facility", definition="a nursing home")
    await seed(registry, "watch", definition="a thing a user watches")
    await registry.retire("watch", "superseded", retired_by="user:sd")

    default = await registry.list_types()
    # A store at version 4 ships one seeded family, `default:edge:equivalent_to`
    # (EDGES.md 3.1, ruling R7), so a census of a fresh store counts it. Listed
    # rather than filtered out of the assertion: a census that hid a row would stop
    # being a census, which is this whole group's subject.
    assert [t.name for t in default.types] == ["equivalent_to", "facility"]
    assert default.complete is False, (
        "include_retired=False is the default AND hides things"
    )
    assert "include_retired=False" in default.why_incomplete

    by_kind = await registry.list_types("entity", include_retired=True)
    assert by_kind.complete is False
    assert "kind" in by_kind.why_incomplete

async def test_c6_02_known_counts_the_returned_set_and_is_none_when_uncountable(
    adapter, make_registry
):
    setup = await make_registry(adapter)
    await seed(setup, "facility", definition="a nursing home")
    await seed(setup, "survey", definition="an inspection visit")

    listing = await setup.list_types(include_retired=True, status=None, namespace=None)
    # Two seeded here plus the one the store ships -- EDGES.md 3.1.
    assert listing.known == 3 == len(listing.types)

    blind = await make_registry(AsyncDegradedAdapter(adapter, pages_countable=False))
    uncountable = await blind.list_types(include_retired=True, status=None, namespace=None)
    assert uncountable.known is None, "None, not 0 -- 0 means 'we counted and found none'"
    assert uncountable.complete is False
    assert uncountable.why_incomplete

@pytest.mark.requires_capability("indexes_membership")
async def test_c6_03_the_predicate_filter_is_the_extent_read_the_other_way(registry):
    await seed(registry, "commentable", kind="predicate", definition="a code path will accept it")
    await seed(registry, "task", predicates=["commentable"])
    await seed(registry, "note", predicates=["commentable"])
    await seed(registry, "capture", definition="not commentable")

    listing = await registry.list_types(predicate="commentable")
    assert sorted(t.name for t in listing.types) == ["note", "task"]

    [entry] = [p for p in await registry.predicates() if p.name == "commentable"]
    assert sorted(entry.extent) == sorted(t.name for t in listing.types)

async def test_c6_04_the_true_census_is_complete(registry):
    await seed(registry, "facility", definition="a nursing home")
    await seed(registry, "watch", definition="a thing a user watches")
    await registry.retire("watch", "superseded", retired_by="user:sd")

    census = await registry.list_types(include_retired=True, status=None, namespace=None)
    assert census.complete is True
    assert census.why_incomplete is None
    # A store at version 4 ships one seeded family, `default:edge:equivalent_to`
    # (EDGES.md 3.1, ruling R7), so a census of a fresh store counts it. Listed
    # rather than filtered out of the assertion: a census that hid a row would stop
    # being a census, which is this whole group's subject.
    assert sorted(t.name for t in census.types) == [
        "equivalent_to",
        "facility",
        "watch",
    ]
    assert census.known == 3

@pytest.mark.requires_capability("counts_usage")
async def test_c6_05_orphaned_excludes_the_unknowable_and_says_how_many(adapter, make_registry, clock):
    setup = await make_registry(adapter)
    await seed(setup, "facility", definition="a nursing home")
    await seed(setup, "survey", definition="an inspection visit")
    await setup.record_use("facility")

    half_blind = await make_registry(
        AsyncDegradedAdapter(
            adapter,
            timestamps_usage=False,
            why={"timestamps_usage": "work_link_types has no last_used_at column"},
        )
    )
    # `facility` has been used, but without a timestamp its orphan state is unknowable;
    # `survey` has a count of zero, which IS knowable.
    assert (await half_blind.usage("facility")).orphaned is None
    assert (await half_blind.usage("survey")).orphaned is True

    listing = await half_blind.list_types(orphaned=True)
    # The seeded family has never been recorded either, so it is orphaned too --
    # which is the true answer about a store nobody has written an edge into yet.
    assert [t.name for t in listing.types] == ["equivalent_to", "survey"]
    assert listing.excluded_unknown == 1, (
        "an unknown orphan state is excluded from both answers and counted, not folded "
        "into whichever answer the caller asked for"
    )
    assert listing.complete is False

@pytest.mark.requires_capability("stores_proposals")
async def test_c6_06_unverified_semantics_enumerates_exactly_the_carriers(registry):
    await seed(registry, "facility", definition="a nursing home")
    proposal = await registry.propose_type(
        "scope_severity_code",
        "Ordered severity scale A-L. Higher letters are LESS serious.",
        [],
        "ai:proposer",
        kind="value_set",
        tier="opus",
    )
    await registry.approve(proposal.id, "user:sd")

    flagged = await registry.list_types(unverified_semantics=True)
    assert [t.name for t in flagged.types] == ["scope_severity_code"]

    clean = await registry.list_types(unverified_semantics=False)
    # The seeded family asserts no domain semantic and carries its own evidence
    # (ruling R7), so it belongs on the clean side -- which is the assertion that
    # would catch a seed that quietly arrived unverified.
    assert [t.name for t in clean.types] == ["equivalent_to", "facility"]
    assert flagged.complete is False and clean.complete is False

async def test_c6_07_the_census_spans_namespaces_and_a_scoped_listing_says_it_did_not(registry):
    """``list_types`` is the only call in INTERFACE.md 5 whose ``namespace`` may be
    ``None``, so it is the only way a reader sees a word that two publishers scoped
    apart. Added by row 3c after UC3; see docs/findings/3C-VALIDATION.md.

    Mechanism 2, across namespaces: if the city-wide census does not span them, nobody
    can find out that ``status`` is already taken three times over -- and a scoped
    listing that reported ``complete=True`` would say the opposite of the truth.
    """
    await seed(registry, "status", kind="value_set", namespace="dpr",
         definition="whether a street tree is alive, dead, or a stump")
    await seed(registry, "status", kind="value_set", namespace="oti_311",
         definition="where a 311 service request is in its workflow")
    await seed(registry, "status", kind="value_set", namespace="dot",
         definition="whether a parking meter is in service")

    census = await registry.list_types(include_retired=True, status=None, namespace=None)
    assert census.complete is True and census.why_incomplete is None
    assert sorted(t.namespace for t in census.types) == [
        "default",  # the seeded family -- EDGES.md 3.1
        "dot",
        "dpr",
        "oti_311",
    ]
    assert census.known == 4
    assert len({t.definition for t in census.types}) == 4, "three words, three meanings"

    scoped = await registry.list_types(include_retired=True, status=None, namespace="dot")
    assert [t.namespace for t in scoped.types] == ["dot"]
    assert scoped.complete is False, "a scoped listing hid two rows and must say so"
    assert scoped.why_incomplete and "namespace" in scoped.why_incomplete

@pytest.mark.requires_capability("stores_aliases", "stores_events", "indexes_membership")
async def test_c6_08_the_predicate_filter_resolves_the_identity_per_namespace(
    adapter, make_registry
):
    """**Ruling R54, row 4d — `list_types(predicate=)` names an identity, not a word.**

    `list_types` is the call whose absence means *"nobody could find the existing
    types"*. After a merge it stopped finding them: every type that had declared the
    absorbed word vanished from the survivor's listing, with a `known` that counted only
    what it happened to see. Both directions are asserted — asking by the **survivor**
    finds the type that declared the absorbed word, and asking by the **absorbed** word
    finds the type that declared the survivor — because they are one identity and the
    call cannot have an opinion about which of its names the caller happened to use.

    **The scoping rule is the interesting half.** An identity is per `(namespace, kind)`
    (§2.1, §2.6): the same word in two namespaces is two identities, and that is exactly
    what §2.6 makes `namespace` the answer to mechanism 4 *for*. So the closure is
    resolved **inside** a namespace and never across one, and a second namespace holding
    its own `commentable` is left alone — asserted here, because a fix that merged the
    two would be §2.6's answer to mechanism 4 deleting itself, which is the shape ruling
    R6 was careful to avoid one call along (§5.3.1 rule 4).
    """
    registry = await make_registry(adapter, approval_policy="auto")
    for name in ("commentable", "searchable"):
        await seed(registry, name, kind="predicate", definition="a capability")
    await seed(registry, "note", predicates=["commentable", "searchable"])

    # A DIFFERENT agency's `commentable`, in its own namespace, meaning its own thing.
    await seed(registry, "commentable", kind="predicate", namespace="dpr", definition="a capability")
    await seed(registry, "park_sign", namespace="dpr", predicates=["commentable"])

    merged = await registry.merge_types(
        "commentable", "searchable", "identical non-empty extents", merged_by="user:sd",
        acknowledge=["definitions_diverge", "no_consumer_evidence"],
    )
    assert hasattr(merged, "aliases_added"), merged

    await seed(registry, "memo", predicates=["commentable"])
    await seed(registry, "doc", predicates=["searchable"])

    by_survivor = await registry.list_types(predicate="searchable", namespace="default")
    assert {t.name for t in by_survivor.types} == {"note", "memo", "doc"}, (
        "`memo` declared the absorbed word; it is a member of this identity and the "
        "call that exists so people can FIND types must find it"
    )
    assert by_survivor.known == 3

    by_absorbed = await registry.list_types(predicate="commentable", namespace="default")
    assert {t.name for t in by_absorbed.types} == {"note", "memo", "doc"}, (
        "one identity, and the answer cannot depend on which of its names was used"
    )

    # **The default `namespace=None` is the ordinary call and gets the same answer** --
    # resolved per namespace, by one bounded `name_in` lookup rather than a census.
    unscoped = await registry.list_types(predicate="searchable")
    assert {t.name for t in unscoped.types} == {"note", "memo", "doc"}

    # ...and the other agency's identical word is untouched. Scoping is what stops two
    # teams' meanings being collapsed, and R54 must not undo it.
    other = await registry.list_types(predicate="commentable", namespace="dpr")
    assert {t.name for t in other.types} == {"park_sign"}

    # **§5.6.1-3: the lookup is BOUNDED, and the rule was unexercised until round 3** --
    # a mutation replacing the `name_in` probe with an unbounded census left all 245 ids
    # green, because this test asserted result sets and never the shape of the query.
    # Ruling R13 declined to page that census in v0; a fix that quietly reintroduces it
    # is a fix that changes what the call costs at UC3 scale.
    seen: list = []
    inner = registry.adapter

    class _Counting:
        def __getattr__(self, name):
            return getattr(inner, name)

        async def find_types(self, q):
            seen.append(q)
            return await inner.find_types(q)

    counted = await make_registry(_Counting(), approval_policy="auto")
    await counted.list_types(predicate="searchable")
    censuses = [
        q for q in seen
        if q.predicate is None and q.name_in is None and q.namespace is None
    ]
    assert not censuses, (
        f"the identity is resolved by a bounded `name_in` lookup, not by reading every "
        f"type in every namespace: {len(censuses)} unfiltered queries"
    )
    assert any(q.name_in for q in seen), "and the bounded lookup is the one that ran"

    # **The identity only ever ADDS (§5.6.1-4).** The written word is queried in
    # whatever scope the caller asked for, so a type declaring a predicate that names no
    # row at all -- a dangling reference, which EDGES.md §2.7 calls a fact rather than
    # an error -- is still found. A fix that replaced the written word with a closure
    # would have deleted this answer.
    await seed(registry, "leaflet", predicates=["nobody_registered_this"])
    dangling = await registry.list_types(predicate="nobody_registered_this", namespace="default")
    assert {t.name for t in dangling.types} == {"leaflet"}

@pytest.mark.requires_capability("stores_aliases", "indexes_membership")
async def test_c6_09_an_identity_written_only_as_an_alias_is_found_both_ways(
    adapter, make_registry
):
    """**`known=0` about types the registry can see.** Row 4d, round 2.

    `_identity_closure` walked the successor relation **both** ways and the alias
    relation only **one**: it extended its frontier with a row's own aliases, and never
    asked *which live row answers to THIS word as an alias*. So an identity written the
    way a foreign dump writes one — `import_types` putting `aliases: ["borough_scoped"]`
    onto `geo_scoped`, with no row ever named `borough_scoped` — was findable from the
    survivor and **invisible** from the absorbed word:

    | call | answer |
    |---|---|
    | `resolve_type("borough_scoped")` | `geo_scoped` at **1.0** |
    | `propose_type(predicates=["borough_scoped"])` | `declared_predicate_merged` |
    | `list_types(predicate="geo_scoped")` | both members |
    | `list_types(predicate="borough_scoped")` | **`[]`, `known=0`** |

    One store, three doors saying the two words are one identity and a fourth answering a
    **confident zero** — §5.2's own named failure mode, in the call ruling **R54** exists
    to fix. It also falsified §5.6.1-1 as written; `C6-08` could not catch it because it
    builds every identity with `merge_types`, and a merge writes a **row**.

    **UC3:** an export's alias column is how a legacy word survives, and `import_types`
    is the ingestion wedge's landing path.
    """
    registry = await make_registry(adapter, approval_policy="auto")
    await seed(registry, "geo_scoped", kind="predicate", definition="a capability")
    await seed(registry, "bike_rack", predicates=["geo_scoped"])
    await seed(registry, "street_segment", predicates=["geo_scoped"])
    imported = (await registry.import_types(
        [{"name": "geo_scoped", "kind": "predicate", "definition": "a capability",
          "aliases": ["borough_scoped"], "status": "active"}],
        namespace="default", kind="predicate",
    ))[0]
    assert "borough_scoped" in (imported.aliases or ()), imported.warnings

    survivor = await registry.list_types(namespace="default", predicate="geo_scoped")
    absorbed = await registry.list_types(namespace="default", predicate="borough_scoped")
    assert {t.name for t in survivor.types} == {"bike_rack", "street_segment"}
    assert {t.name for t in absorbed.types} == {"bike_rack", "street_segment"}, (
        "one identity, and the answer cannot depend on which of its names was used -- "
        "5.6.1-1, which was false for the alias-only shape"
    )
    assert absorbed.known == 2, "and `known` is not a confident zero"
