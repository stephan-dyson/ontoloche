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
from ..errors import AlreadyExists
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


FORBIDDEN = ("Refusal", "Rejection", "Resolution", "Proposal", "TypeEntry")


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
    stored = adapter.put_type(_type(), expect_absent=True)
    assert stored.name == "facility"
    assert stored.definition.startswith("a Medicare/Medicaid-certified")
    assert stored.predicates == ("searchable",)
    assert stored.aliases == ("nursing_home",)
    assert stored.attributes == {"primary_key": ["ccn"]}
    assert stored.provenance == {"approved_by": "user:sd"}
    assert stored.warnings == ("no_evidence",)
    assert stored.created_at == NOW and stored.updated_at == NOW

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
    assert back == proposal
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
    adapter.append_event(event)
    assert adapter.read_events("default", name="facility") == [event]

    adapter.bump_usage("default", "entity", "facility", at=NOW, by="user:sd")
    usage = adapter.get_usage("default", "entity", "facility")
    assert usage.count == 1 and usage.first_seen == NOW and usage.last_seen == NOW

    # A field the backend cannot store comes back EMPTY, not wrong -- so the caller can
    # tell the write did not round-trip instead of believing it did.
    degraded = DegradedAdapter(adapter, stores_attributes=False, stores_aliases=False)
    got = degraded.get_type("default", "facility", kind="entity")
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
        assert got.attributes == rec.attributes

    # And the collision is still refused *within* a namespace.
    with pytest.raises(AlreadyExists):
        adapter.put_type(rows["dpr"], expect_absent=True)

    everywhere = adapter.find_types(TypeQuery(namespace=None, kind="value_set"))
    assert sorted(r.namespace for r in everywhere.records) == ["dot", "dpr", "oti_311"]
