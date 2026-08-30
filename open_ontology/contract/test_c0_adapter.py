"""C0 -- adapter conformance (6). No interface call; this is the protocol itself."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from pathlib import Path

import pytest

from .. import adapter as adapter_module
from ..adapter import (
    CAPABILITY_FLAGS,
    REQUIRED_CAPABILITIES,
    ConsumerRecord,
    EventRecord,
    ProposalQuery,
    ProposalRecord,
    TypeQuery,
    TypeRecord,
)
from ..errors import AlreadyExists, AmbiguousKind, NotSupported
from ._support import snapshot
from .doubles import DegradedAdapter

NOW = datetime(2026, 8, 28, 12, 0, tzinfo=UTC)


def _type(name="facility", **kw) -> TypeRecord:
    base = dict(
        namespace="default",
        kind="entity",
        name=name,
        definition="a Medicare/Medicaid-certified nursing home, identified by its CCN",
        created_by="ai",
        status="active",
        predicates=("searchable",),
        aliases=("nursing_home",),
        attributes={"primary_key": ["ccn"]},
        attr_schema_version=None,
        provenance={"approved_by": "user:sd"},
        warnings=("no_evidence",),
        created_at=NOW,
        updated_at=NOW,
    )
    base.update(kw)
    return TypeRecord(**base)


def test_c0_01_capabilities_are_complete_and_every_false_flag_is_explained(adapter):
    caps = adapter.capabilities()
    for flag in CAPABILITY_FLAGS:
        assert isinstance(getattr(caps, flag), bool), f"{flag} must be a bool"
    assert isinstance(caps.why, dict)

    # The invariant: a False flag without a sentence would make the registry invent an
    # explanation, which is exactly what Capabilities exists to prevent.
    assert caps.missing_why() == (), f"False flags with no why: {caps.missing_why()}"

    # Two are not negotiable.
    for flag in REQUIRED_CAPABILITIES:
        assert getattr(caps, flag) is True, f"{flag}=False is non-conformant, full stop"

    degraded = DegradedAdapter(adapter, counts_usage=False, stores_events=False)
    assert degraded.capabilities().missing_why() == ()
    assert degraded.capabilities().reason("counts_usage").strip()


def test_c0_02_g1_uniqueness_comes_from_a_constraint(adapter):
    adapter.put_type(_type(), expect_absent=True)
    with pytest.raises(AlreadyExists):
        adapter.put_type(_type(definition="a different definition"), expect_absent=True)

    # Uniqueness is per (namespace, kind): the same word under two kinds may coexist.
    adapter.put_type(_type(kind="value_set"), expect_absent=True)
    assert adapter.get_type("default", "facility", kind="value_set") is not None


@pytest.mark.requires_capability("stores_events")
def test_c0_03_g2_an_exception_inside_a_transaction_leaves_the_store_unchanged(adapter):
    adapter.put_type(_type(), expect_absent=True)
    before = snapshot(adapter)

    class Boom(RuntimeError):
        pass

    with pytest.raises(Boom):
        with adapter.transaction():
            adapter.put_type(_type(name="survey"), expect_absent=True)
            adapter.append_event(
                EventRecord(
                    event_id="e-rollback",
                    namespace="default",
                    at=NOW,
                    actor="user:sd",
                    event="approved",
                )
            )
            adapter.bump_usage("default", "entity", "facility", at=NOW, by="user:sd")
            raise Boom("half-committed is the failure this guarantee prevents")

    assert snapshot(adapter) == before
    assert adapter.get_type("default", "survey") is None


#: PACKAGE.md 3.1 names seven. The first draft of this test checked five -- so the
#: test the document calls "the rule the whole protocol is built on" enforced less
#: than the rule it is named after. Corrected by row 3c after an adversarial review
#: round; there was no live violation, which is exactly why it went unnoticed.
FORBIDDEN = (
    "Refusal",
    "Rejection",
    "Resolution",
    "Proposal",
    "TypeEntry",
    "ConsumerReport",
    "UsageReport",
    # Row 4b, EDGES.md 7.1. Five more, and the document asked for them by name:
    # *"an adapter that knew about `depth` would know about `NeighborReport`, and
    # C0-04's source-inspection test would have a new identifier to police."* The
    # boundary EDGES.md calls "the strongest evidence that 2.3's decision was right"
    # was, in the spec row's own probe kit, asserted and contradicted -- the kit's
    # store handed back the rich facade object. It is policed here rather than
    # asserted. `EdgeRecord`, `EdgeQuery` and `EdgePage` are storage shapes and live
    # in `adapter.py`; `Edge` does not match them.
    "Edge",
    "EdgeProvenance",
    "EdgeFamily",
    "NeighborEdge",
    "NeighborReport",
    # Row 6b, ACTIONS.md 9. Nine more, on the same argument one kind along: 2.1's whole
    # architectural bet is that a family is a `TypeEntry` and an invocation is a stored
    # row, so the STORE holds `(family, inputs, effects, outcome)` with a blob of
    # provenance and a `gate_verdict` string it never judges. `InvocationRecord`,
    # `InvocationQuery` and `InvocationPage` are storage shapes and live in
    # `adapter.py`; `\bInvocation\b` does not match them. The rich shapes -- the ones
    # with typed references, a three-valued precondition result and a computed warnings
    # list -- live in `open_ontology/actions.py`, and an adapter that knew about
    # `Preflight` would know what a GATE VERDICT MEANS, which is the one thing PACKAGE.md
    # 3.1 forbids it to know.
    "Invocation",
    "InvocationProvenance",
    "InvocationReport",
    "Preflight",
    "PreconditionResult",
    "Precondition",
    "InputSpec",
    "Effect",
    "ActionFamily",
    "ProjectionReport",
)


def test_c0_04_the_adapter_does_not_know_what_a_decision_is():
    """The rule the whole protocol is built on, checked by source inspection."""
    files = [Path(adapter_module.__file__)]
    files.extend(sorted((Path(adapter_module.__file__).parent / "backends").rglob("*.py")))
    assert len(files) >= 4, "expected adapter.py plus the backends package"

    offences: list[str] = []
    for path in files:
        source = path.read_text(encoding="utf-8")
        for identifier in FORBIDDEN:
            for match in re.finditer(rf"\b{identifier}\b", source):
                line = source[: match.start()].count("\n") + 1
                offences.append(f"{path.name}:{line} mentions {identifier}")
    assert offences == [], "\n".join(offences)


def test_c0_05_migrate_is_idempotent_and_atomic(adapter):
    version = adapter.migrate()
    assert adapter.migrate() == version
    assert adapter.migrate() == version

    if not adapter.capabilities().owns_schema:
        # Idempotence is asserted above and holds on every backend. The ATOMICITY half
        # below drives a failing migration, and a verify-only backend issues no DDL at
        # all (PACKAGE.md 9.3) -- there is no half-applied migration for it to have.
        # C0-09 is the subject there. Skipped with a reason rather than returned from,
        # so the coverage report (ruling R12) can see it. Row 3d.
        pytest.skip(
            "PACKAGE.md 9.3 -- this backend declares owns_schema=False, so migrate() "
            "issues no DDL and the atomic-migration half of C0-05 has nothing to drive. "
            "Idempotence was asserted; C0-09 is the subject for verify-only migrate()."
        )

    migrations = getattr(adapter, "_migration_sql", None)
    if migrations is None:
        pytest.skip("this backend does not expose numbered migrations to inspect")

    original = migrations()
    broken = list(original) + [
        (
            version + 1,
            "broken",
            "CREATE TABLE oo_half_applied (x INTEGER);\nTHIS IS NOT SQL;",
        )
    ]
    adapter._migration_sql = lambda: broken
    try:
        with pytest.raises(Exception):
            adapter.migrate()
    finally:
        adapter._migration_sql = migrations

    # The version row and the DDL are one transaction, so a failed migration leaves
    # neither: the store is still at the version it honestly is.
    assert adapter._current_version() == version
    with pytest.raises(Exception):
        adapter._fetchone("SELECT count(*) FROM oo_half_applied")


def test_c0_06_every_record_round_trips_and_a_gap_comes_back_empty(adapter):
    """The title's second half is the point, and until row 3c only its first half was
    tested: this asserted every field came back *populated*, which is true only of a
    fully capable backend. A backend that declines `stores_aliases` or
    `stores_attributes` -- conformant per PACKAGE.md 3.2 -- failed it for storing
    exactly what it said it would. **A gap must come back empty, not wrong**, and that
    is what is asserted now.

    **The projected-key case -- beacon finding U3, row 3d.** `stores_attributes` was
    binary, so a host-owned backend with pre-existing typed columns could not say *"I
    store no arbitrary keys AND I own two named ones faithfully"*. It now can:
    `Capabilities.attribute_projections` names the keys the backend owns as typed
    columns. A projected key **survives** whatever `stores_attributes` says; a key that
    is neither stored nor projected comes back **absent, with a why** -- unchanged.

    **The `requires_capability("stores_proposals")` marker is gone**, and that is part
    of U3 rather than housekeeping: the body has always returned early when there is no
    proposal store, so the marker skipped the whole test -- including the type
    round-trip and the projection case -- on exactly the natively-degraded backend those
    assertions exist for (PACKAGE.md 6, third reference leg).
    """
    caps = adapter.capabilities()
    stored = adapter.put_type(_type(), expect_absent=True)
    assert stored.name == "facility"
    assert stored.definition.startswith("a Medicare/Medicaid-certified")
    assert stored.provenance == {"approved_by": "user:sd"}
    assert stored.warnings == ("no_evidence",)
    assert stored.created_at == NOW and stored.updated_at == NOW

    # Each of these is stored faithfully, or comes back EMPTY -- never wrong.
    assert stored.predicates == (("searchable",) if caps.indexes_membership else ())
    assert stored.aliases == (("nursing_home",) if caps.stores_aliases else ())

    # --- attributes: three outcomes, and the middle one is U3's.
    written = {"primary_key": ["ccn"], "sensitivity": "public"}
    probe = adapter.put_type(
        _type(name="projection_probe", attributes=dict(written)), expect_absent=True
    )
    survives = caps.surviving_attributes(written)
    assert probe.attributes == survives, (
        "an attribute either round-trips or comes back absent. Never a different value, "
        "and never a projected key silently dropped"
    )
    for key in sorted(caps.attribute_projections):
        assert caps.stores_attribute(key)
        if key in written:
            assert probe.attributes.get(key) == written[key], (
                f"{key!r} is DECLARED as a typed column this backend owns, so it must "
                "round trip through that column -- U3"
            )
    if not caps.stores_attributes:
        # ...and the keys it does not own are absent WITH a why, as before U3.
        assert set(probe.attributes) == set(caps.attribute_projections) & set(written)
        assert caps.reason("stores_attributes").strip()
    assert stored.attributes == caps.surviving_attributes({"primary_key": ["ccn"]})

    if not caps.stores_proposals:
        return  # the proposal half needs a proposal store; C5-12 is its subject

    proposal = ProposalRecord(
        proposal_id="p1",
        namespace="default",
        kind="value_set",
        name="scope_severity_code",
        definition="ordered severity scale A-L",
        predicates=("enumerable",),
        attributes={"ordered": True},
        evidence=[{"kind": "data", "summary": "seven codes in the sample"}],
        proposed_by="ai:proposer",
        proposed_at=NOW,
        tier="haiku",
        status="pending",
        warnings=("no_evidence",),
        near_matches=[["severity", 0.8]],
    )
    back = adapter.put_proposal(proposal, expect_absent=True)
    if caps.stores_attributes and caps.indexes_membership:
        assert back == proposal
    else:
        assert back.proposal_id == proposal.id if hasattr(back, "id") else True
        assert back.name == proposal.name and back.definition == proposal.definition
    assert adapter.find_proposals(ProposalQuery(name="scope_severity_code")).known == 1

    consumer = ConsumerRecord(
        namespace="default",
        consumer_id="aura_render.referent_link",
        gate="commentable",
        on_unknown="drop",
        owner="platform",
        registered_at=NOW,
        locator="aura/render.py:412",
    )
    assert adapter.put_consumer(consumer) == consumer

    event = EventRecord(
        event_id="e1",
        namespace="default",
        at=NOW,
        actor="user:sd",
        event="approved",
        kind="entity",
        name="facility",
        proposal_id="p1",
        detail={"tier": "haiku"},
    )
    if caps.stores_events:
        adapter.append_event(event)
        assert adapter.read_events("default", name="facility") == [event]
    else:
        # PACKAGE.md 3.4 primitives 14 and 15: NotSupported, loudly, never a silent
        # drop. A store with no audit trail says so rather than pretending to keep one.
        with pytest.raises(NotSupported):
            adapter.append_event(event)

    adapter.bump_usage("default", "entity", "facility", at=NOW, by="user:sd")
    usage = adapter.get_usage("default", "entity", "facility")
    if caps.counts_usage:
        assert usage is not None and usage.count == 1
    else:
        # `get_usage` may return None (nothing recorded at all) or a record with
        # count=None (this backend does not count). PACKAGE.md 3.4 primitive 13 says
        # those are DIFFERENT FACTS; either is honest here, and neither may be 0.
        assert usage is None or usage.count is None, "None, never 0"
        if usage is None:
            return
    if caps.timestamps_usage:
        assert usage.first_seen == NOW and usage.last_seen == NOW
    else:
        assert usage.first_seen is None and usage.last_seen is None, "empty, not wrong"

    # A field the backend cannot store comes back EMPTY, not wrong -- so the caller can
    # tell the write did not round-trip instead of believing it did.
    degraded = DegradedAdapter(adapter, stores_attributes=False, stores_aliases=False)
    dcaps = degraded.capabilities()
    got = degraded.get_type("default", "facility", kind="entity")
    # U3: "empty" means every key the backend does not own. A DECLARED projection is a
    # key it does own, so it survives -- and a wrapper that dropped it would be making
    # the same mistake in the other direction.
    assert got.attributes == dcaps.surviving_attributes(stored.attributes)
    if not dcaps.attribute_projections:
        assert got.attributes == {}
    assert got.aliases == ()
    assert got.definition == stored.definition  # nothing else was disturbed

    page = adapter.find_types(TypeQuery(namespace="default"))
    assert page.known == len(page.records) and page.complete is True


def test_c0_07_g1s_key_is_scoped_so_one_word_in_two_namespaces_is_two_rows(adapter):
    """G1 is uniqueness of ``(namespace, kind, name)`` -- C0-02 tests the uniqueness,
    this tests the *scope*, which is the half mechanism 4 depends on.

    INTERFACE.md 2.6 answers semantic collision with ``namespace``: when two publishers
    mean different things by one word, the answer is scoping and it must not be a merge.
    That answer is only worth anything if the store will actually hold both rows, keep
    them apart, and hand each back to the caller that asked in its namespace. Added by
    row 3c after UC3 (NYC Open Data) found the whole suite exercised two namespaces in
    exactly one place -- C10-04, the *refusal* -- and never the coexistence the refusal
    presupposes. See docs/findings/3C-VALIDATION.md.

    The fixture is UC3's: ``status`` means the life state of a tree to Parks, the
    workflow state of a request to 311, and the service state of a meter to
    Transportation. No value appears in more than one of the three sets.
    """
    adapter.migrate()
    rows = {
        "dpr": _type(name="status", namespace="dpr", kind="value_set",
                     definition="whether a street tree is alive, dead, or a stump",
                     attributes={"values": ["Alive", "Stump", "Dead"]}),
        "oti_311": _type(name="status", namespace="oti_311", kind="value_set",
                         definition="where a 311 service request is in its workflow",
                         attributes={"values": ["Open", "Closed", "Pending"]}),
        "dot": _type(name="status", namespace="dot", kind="value_set",
                     definition="whether a parking meter is in service",
                     attributes={"values": ["Active", "Inactive"]}),
    }
    for rec in rows.values():
        # expect_absent=True must NOT collide across namespaces -- if it does, the
        # second publisher cannot register at all and scoping is not an answer.
        adapter.put_type(rec, expect_absent=True)

    for namespace, rec in rows.items():
        got = adapter.get_type(namespace, "status", kind="value_set")
        assert got is not None, f"{namespace}:status went missing"
        assert got.definition == rec.definition, "one namespace overwrote another"
        if adapter.capabilities().stores_attributes:
            assert got.attributes == rec.attributes

    # And the collision is still refused *within* a namespace.
    with pytest.raises(AlreadyExists):
        adapter.put_type(rows["dpr"], expect_absent=True)

    everywhere = adapter.find_types(TypeQuery(namespace=None, kind="value_set"))
    assert sorted(r.namespace for r in everywhere.records) == ["dot", "dpr", "oti_311"]


def test_c0_10_keyset_pagination_actually_pages(adapter):
    """**The first defect found by asking the other question.** Eleven review rounds
    asked *"can a legitimate backend FAIL the suite?"* and found five. This one came
    from asking the mirror: **can a broken backend PASS it?**

    §3.3 gives `TypeQuery` a `limit` and an opaque `after` cursor and `TypePage` a
    `next_after`, ordered by `(namespace, kind, name)`, and spends real design ink
    justifying query objects over kwargs. **Nothing exercised any of it.** [Observed]: an
    adapter identical to the reference one except that it silently drops `limit` and
    `after` -- so every page is the whole set, which in a real keyset consumer is an
    infinite loop or a duplicate-forever bug -- ran the whole suite to
    `119 passed, exit 0` and printed the CONFORMANCE banner with no caveat.

    That matters at UC3's stated scale (2,399 datasets; "hundreds to low thousands of
    types") and for the Phase 3 ingestion loop, which is the shape this pagination
    exists for. Added by row 3c after an adversarial review round.

    **What this does NOT fix, recorded as question Q8:** `Registry` never *asks* for a
    bounded page -- every façade call site builds an unbounded query -- so a correct
    implementation is still never exercised in production. That is a design decision
    (what should `complete`/`known` mean on a paged listing?) and it wants a ruling.
    """
    adapter.migrate()
    names = [f"type_{i:02d}" for i in range(7)]
    for name in names:
        adapter.put_type(_type(name=name), expect_absent=True)

    everything = adapter.find_types(TypeQuery(namespace="default"))
    assert sorted(r.name for r in everything.records) == names, "the fixture itself"

    seen: list[str] = []
    cursor, pages = None, 0
    while True:
        page = adapter.find_types(TypeQuery(namespace="default", limit=3, after=cursor))
        pages += 1
        assert len(page.records) <= 3, (
            "a page must honour `limit` -- an adapter that returns everything makes "
            "`next_after` meaningless and loops a keyset consumer forever"
        )
        batch = [r.name for r in page.records]
        assert not (set(batch) & set(seen)), (
            f"page {pages} repeats rows from an earlier page: `after` was not honoured"
        )
        seen.extend(batch)
        cursor = page.next_after
        if cursor is None:
            break
        assert pages < 10, "next_after never went None -- this would not terminate"

    assert seen == names, "the pages must partition the result set, in key order"
    assert pages == 3, "7 rows at limit=3 is three pages, the last one short"


def test_c0_11_one_name_under_two_kinds_is_ambiguous_not_arbitrary(adapter):
    """§3.4 primitive 5: `get_type(kind=None)` *"returns the single match or raises
    `AmbiguousKind` when the same name exists under two kinds (legal: uniqueness is per
    `(namespace, kind)`)"*. **`AmbiguousKind` was raised by both reference backends and
    referenced by no test in the repository**, and [Observed] an adapter that returns
    `rows[0]` instead of checking ran the whole suite to a clean conformant pass.

    The scenario is the one §4.1 blesses by name -- *"`facility` as an `entity` and
    `facility` as a `value_set` may coexist"* -- so this is a silent wrong answer in the
    exact case the per-`(namespace, kind)` scoping exists to permit. Rule U: an arbitrary
    pick from two candidates is a confident answer to a question with no single answer.
    Added by row 3c after an adversarial review round built the arbitrary-pick adapter.
    """
    adapter.migrate()
    adapter.put_type(_type(name="facility", kind="entity"), expect_absent=True)
    adapter.put_type(
        _type(name="facility", kind="value_set", definition="an enumerated set"),
        expect_absent=True,
    )

    with pytest.raises(AmbiguousKind):
        adapter.get_type("default", "facility")

    # ...and naming the kind answers it, which is what makes the ambiguity legal.
    entity = adapter.get_type("default", "facility", kind="entity")
    value_set = adapter.get_type("default", "facility", kind="value_set")
    assert entity is not None and entity.kind == "entity"
    assert value_set is not None and value_set.kind == "value_set"
    assert entity.definition != value_set.definition, "two rows, two meanings"
