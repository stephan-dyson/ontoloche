"""PRIVATE. Row <-> record mapping shared by the two reference backends.

The two backends differ in exactly three places -- JSON storage, timestamps, and how a
read inside a write transaction is serialised -- and those differences are the adapter's
*content*, not something to abstract away. So they live in a small ``_Dialect`` object
and everything else is shared, which is the only honest way to have two backends that
are provably the same thing.

Nothing in this file knows what an approval or a refusal is.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any, Iterable

from ..adapter import (
    AttrObservedRecord,
    AttrSchemaRecord,
    ConsumerRecord,
    EventRecord,
    ProposalRecord,
    TypeRecord,
    UsageRecord,
)

__all__ = ["Dialect", "SqliteDialect", "PostgresDialect", "SqlStore"]


class Dialect:
    """What differs between the two stores, and nothing else."""

    name = "generic"
    ph = "?"
    event_order = "at, event_id"
    supports_row_values = True

    def enc_json(self, obj: Any) -> Any:
        raise NotImplementedError

    def dec_json(self, value: Any) -> Any:
        raise NotImplementedError

    def enc_ts(self, value: datetime | None) -> Any:
        raise NotImplementedError

    def dec_ts(self, value: Any) -> datetime | None:
        raise NotImplementedError


def _iso(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z"


class SqliteDialect(Dialect):
    name = "sqlite"
    ph = "?"
    event_order = "at, rowid"

    def enc_json(self, obj: Any) -> Any:
        return json.dumps(obj, sort_keys=True, default=str)

    def dec_json(self, value: Any) -> Any:
        if value is None:
            return None
        return json.loads(value)

    def enc_ts(self, value: datetime | None) -> Any:
        return None if value is None else _iso(value)

    def dec_ts(self, value: Any) -> datetime | None:
        if value is None:
            return None
        if isinstance(value, datetime):
            return value if value.tzinfo else value.replace(tzinfo=UTC)
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))


class PostgresDialect(Dialect):
    name = "postgres"
    ph = "%s"
    event_order = "at, seq"

    def __init__(self) -> None:
        from psycopg.types.json import Jsonb  # imported here so base install stays clean

        self._Jsonb = Jsonb

    def enc_json(self, obj: Any) -> Any:
        return self._Jsonb(json.loads(json.dumps(obj, sort_keys=True, default=str)))

    def dec_json(self, value: Any) -> Any:
        if value is None:
            return None
        if isinstance(value, (str, bytes)):
            return json.loads(value)
        return value

    def enc_ts(self, value: datetime | None) -> Any:
        if value is None:
            return None
        return value if value.tzinfo else value.replace(tzinfo=UTC)

    def dec_ts(self, value: Any) -> datetime | None:
        if value is None:
            return None
        if isinstance(value, datetime):
            return value if value.tzinfo else value.replace(tzinfo=UTC)
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))


TYPE_COLUMNS = (
    "namespace",
    "kind",
    "name",
    "definition",
    "created_by",
    "status",
    "aliases_json",
    "attributes_json",
    "attr_schema_version",
    "provenance_json",
    "warnings_json",
    "retire_reason",
    "retired_by",
    "retired_at",
    "successor",
    "created_at",
    "updated_at",
)

PROPOSAL_COLUMNS = (
    "proposal_id",
    "namespace",
    "kind",
    "name",
    "definition",
    "predicates_json",
    "attributes_json",
    "evidence_json",
    "near_matches_json",
    "warnings_json",
    "proposed_by",
    "proposed_at",
    "tier",
    "status",
    "decided_by",
    "decided_at",
    "decision_reason",
    "superseded_by",
)

CONSUMER_COLUMNS = (
    "namespace",
    "consumer_id",
    "gate",
    "on_unknown",
    "owner",
    "registered_at",
    "locator",
)

EVENT_COLUMNS = (
    "event_id",
    "namespace",
    "kind",
    "name",
    "proposal_id",
    "at",
    "actor",
    "event",
    "detail_json",
)


class SqlStore:
    """Mapping helpers bound to one dialect. Pure functions over rows and records.

    ``type_columns`` is a parameter rather than the module constant because a backend
    sitting on a schema it does not own (PACKAGE.md 9.3) may have **fewer** columns --
    the natively-degraded third reference leg (PACKAGE.md 6.1, beacon finding U2) has no
    ``attributes_json`` at all. ``projections`` maps such a backend's own typed columns
    to the attribute keys they carry (PACKAGE.md 5.7, beacon finding U3): the value goes
    into the column, not into a JSON blob that does not exist.
    """

    def __init__(
        self,
        dialect: Dialect,
        type_columns: tuple[str, ...] = TYPE_COLUMNS,
        projections: dict[str, str] | None = None,
    ):
        self.d = dialect
        self.type_columns = tuple(type_columns)
        #: ``{column_name: attribute_key}``
        self.projections = dict(projections or {})

    # ------------------------------------------------------------------ placeholders
    def marks(self, n: int) -> str:
        return ", ".join([self.d.ph] * n)

    # ------------------------------------------------------------------- type record
    def type_values(self, rec: TypeRecord) -> list[Any]:
        """Values in ``self.type_columns`` order -- the columns this backend has."""
        full = dict(zip(TYPE_COLUMNS, self._full_type_values(rec)))
        attributes = dict(rec.attributes or {})
        out: list[Any] = []
        for column in self.type_columns:
            if column in full:
                out.append(full[column])
            elif column in self.projections:
                out.append(self.d.enc_json(attributes.get(self.projections[column])))
            else:  # pragma: no cover - a column the mapper was never told about
                raise KeyError(f"no value for oo_type column {column!r}")
        return out

    def _full_type_values(self, rec: TypeRecord) -> list[Any]:
        d = self.d
        return [
            rec.namespace,
            rec.kind,
            rec.name,
            rec.definition,
            rec.created_by,
            rec.status,
            d.enc_json(list(rec.aliases)),
            d.enc_json(dict(rec.attributes or {})),
            rec.attr_schema_version,
            d.enc_json(dict(rec.provenance or {})),
            d.enc_json(list(rec.warnings)),
            rec.retire_reason,
            rec.retired_by,
            d.enc_ts(rec.retired_at),
            rec.successor,
            d.enc_ts(rec.created_at),
            d.enc_ts(rec.updated_at),
        ]

    def type_from_row(self, row: Iterable[Any], predicates: tuple[str, ...]) -> TypeRecord:
        d = self.d
        r = dict(zip(self.type_columns, row))
        attributes = d.dec_json(r["attributes_json"]) or {} if "attributes_json" in r else {}
        for column, key in self.projections.items():
            if column not in r:
                continue
            value = d.dec_json(r[column])
            # A projected column that is NULL means the key was never written -- absent,
            # not present-and-null. PACKAGE.md 5.7.
            if value is not None:
                attributes[key] = value
        return TypeRecord(
            namespace=r["namespace"],
            kind=r["kind"],
            name=r["name"],
            definition=r["definition"],
            created_by=r["created_by"],
            status=r["status"],
            predicates=predicates,
            aliases=tuple(d.dec_json(r.get("aliases_json")) or ()),
            attributes=attributes,
            attr_schema_version=r.get("attr_schema_version"),
            provenance=d.dec_json(r.get("provenance_json")) or {},
            warnings=tuple(d.dec_json(r.get("warnings_json")) or ()),
            retire_reason=r.get("retire_reason"),
            retired_by=r.get("retired_by"),
            retired_at=d.dec_ts(r.get("retired_at")),
            successor=r.get("successor"),
            created_at=d.dec_ts(r.get("created_at")),
            updated_at=d.dec_ts(r.get("updated_at")),
        )

    # --------------------------------------------------------------- proposal record
    def proposal_values(self, rec: ProposalRecord) -> list[Any]:
        d = self.d
        return [
            rec.proposal_id,
            rec.namespace,
            rec.kind,
            rec.name,
            rec.definition,
            d.enc_json(list(rec.predicates)),
            d.enc_json(dict(rec.attributes or {})),
            d.enc_json(list(rec.evidence or [])),
            d.enc_json(list(rec.near_matches or [])),
            d.enc_json(list(rec.warnings)),
            rec.proposed_by,
            d.enc_ts(rec.proposed_at),
            rec.tier,
            rec.status,
            rec.decided_by,
            d.enc_ts(rec.decided_at),
            rec.decision_reason,
            rec.superseded_by,
        ]

    def proposal_from_row(self, row: Iterable[Any]) -> ProposalRecord:
        d = self.d
        r = dict(zip(PROPOSAL_COLUMNS, row))
        return ProposalRecord(
            proposal_id=r["proposal_id"],
            namespace=r["namespace"],
            kind=r["kind"],
            name=r["name"],
            definition=r["definition"],
            predicates=tuple(d.dec_json(r["predicates_json"]) or ()),
            attributes=d.dec_json(r["attributes_json"]) or {},
            evidence=list(d.dec_json(r["evidence_json"]) or []),
            near_matches=list(d.dec_json(r["near_matches_json"]) or []),
            warnings=tuple(d.dec_json(r["warnings_json"]) or ()),
            proposed_by=r["proposed_by"],
            proposed_at=d.dec_ts(r["proposed_at"]),
            tier=r["tier"],
            status=r["status"],
            decided_by=r["decided_by"],
            decided_at=d.dec_ts(r["decided_at"]),
            decision_reason=r["decision_reason"],
            superseded_by=r["superseded_by"],
        )

    # --------------------------------------------------------------- consumer record
    def consumer_values(self, rec: ConsumerRecord) -> list[Any]:
        return [
            rec.namespace,
            rec.consumer_id,
            rec.gate,
            rec.on_unknown,
            rec.owner,
            self.d.enc_ts(rec.registered_at),
            rec.locator,
        ]

    def consumer_from_row(self, row: Iterable[Any]) -> ConsumerRecord:
        r = dict(zip(CONSUMER_COLUMNS, row))
        return ConsumerRecord(
            namespace=r["namespace"],
            consumer_id=r["consumer_id"],
            gate=r["gate"],
            on_unknown=r["on_unknown"],
            owner=r["owner"],
            registered_at=self.d.dec_ts(r["registered_at"]),
            locator=r["locator"],
        )

    # ------------------------------------------------------------------ event record
    def event_values(self, rec: EventRecord) -> list[Any]:
        return [
            rec.event_id,
            rec.namespace,
            rec.kind,
            rec.name,
            rec.proposal_id,
            self.d.enc_ts(rec.at),
            rec.actor,
            rec.event,
            self.d.enc_json(dict(rec.detail or {})),
        ]

    def event_from_row(self, row: Iterable[Any]) -> EventRecord:
        r = dict(zip(EVENT_COLUMNS, row))
        return EventRecord(
            event_id=r["event_id"],
            namespace=r["namespace"],
            kind=r["kind"],
            name=r["name"],
            proposal_id=r["proposal_id"],
            at=self.d.dec_ts(r["at"]),
            actor=r["actor"],
            event=r["event"],
            detail=self.d.dec_json(r["detail_json"]) or {},
        )

    # ------------------------------------------------------------------ usage record
    def usage_from_row(self, row: Iterable[Any]) -> UsageRecord:
        namespace, kind, name, count, first_seen, last_seen = row
        return UsageRecord(
            namespace=namespace,
            kind=kind,
            name=name,
            count=count,
            first_seen=self.d.dec_ts(first_seen),
            last_seen=self.d.dec_ts(last_seen),
        )

    # ------------------------------------------------------ attribute-store records
    def attr_schema_values(self, rec: AttrSchemaRecord) -> list[Any]:
        return [
            rec.namespace,
            rec.kind,
            rec.version,
            self.d.enc_json(rec.fields_json),
            rec.additional,
            rec.mode,
            self.d.enc_ts(rec.registered_at),
            rec.registered_by,
        ]

    def attr_schema_from_row(self, row: Iterable[Any]) -> AttrSchemaRecord:
        ns, kind, version, fields_json, additional, mode, registered_at, registered_by = row
        return AttrSchemaRecord(
            namespace=ns,
            kind=kind,
            version=version,
            fields_json=self.d.dec_json(fields_json) or {},
            additional=additional,
            mode=mode,
            registered_at=self.d.dec_ts(registered_at),
            registered_by=registered_by,
        )

    def attr_observed_from_row(self, row: Iterable[Any]) -> AttrObservedRecord:
        ns, kind, key, n, first_seen, last_seen, example_json, versions_json = row
        raw_versions = self.d.dec_json(versions_json) or []
        return AttrObservedRecord(
            namespace=ns,
            kind=kind,
            key=key,
            n=n,
            first_seen=self.d.dec_ts(first_seen),
            last_seen=self.d.dec_ts(last_seen),
            example=self.d.dec_json(example_json),
            schema_versions=tuple(raw_versions),
        )


# --------------------------------------------------------------------------- adapter

import re
from contextlib import contextmanager
from pathlib import Path

from ..adapter import (
    Capabilities,
    ProposalPage,
    ProposalQuery,
    TypePage,
    TypeQuery,
)
from ..errors import AlreadyExists, AmbiguousKind, SchemaMismatch, StoreVersionUnknown

MIGRATIONS_ROOT = Path(__file__).resolve().parent / "migrations"

_COMMENT = re.compile(r"^\s*--")

_CURSOR_SEP = "\x1f"


def encode_cursor(namespace: str, kind: str, name: str) -> str:
    return _CURSOR_SEP.join((namespace, kind, name))


def decode_cursor(cursor: str) -> tuple[str, str, str]:
    parts = cursor.split(_CURSOR_SEP)
    if len(parts) != 3:
        raise ValueError(f"not a cursor from this backend: {cursor!r}")
    return parts[0], parts[1], parts[2]


def split_statements(sql: str) -> list[str]:
    """Split a migration file into statements.

    Deliberately not ``executescript``: on SQLite that issues a COMMIT first and runs
    outside our transaction control, which would put the DDL and the version row in
    different transactions and leave a store whose version is a lie (C0-05).
    """
    body = "\n".join(line for line in sql.splitlines() if not _COMMENT.match(line))
    return [s.strip() for s in body.split(";") if s.strip()]


def load_migrations(backend: str) -> list[tuple[int, str, str]]:
    """``(version, slug, sql)`` in strict numeric order. Forward-only; no down path."""
    directory = MIGRATIONS_ROOT / backend
    out: list[tuple[int, str, str]] = []
    for path in sorted(directory.glob("*.sql")):
        version_text, _, slug = path.stem.partition("_")
        out.append((int(version_text), slug, path.read_text(encoding="utf-8")))
    out.sort(key=lambda item: item[0])
    return out


class BaseSqlAdapter:
    """The fifteen primitives over a DB-API connection, shared by both backends.

    Subclasses supply a connection, a dialect, and the three things that genuinely
    differ: how a transaction begins, which exception a uniqueness constraint raises,
    and whether a read inside a write transaction needs an explicit lock.
    """

    backend_name = "generic"
    _owns_schema = True
    #: The ``oo_type`` columns THIS backend has, and the attribute keys any extra column
    #: carries. A backend over a schema it does not own may have fewer -- PACKAGE.md 5.7
    #: and 9.3, beacon findings U2 and U3.
    type_columns: tuple[str, ...] = TYPE_COLUMNS
    type_projections: dict[str, str] = {}
    #: False when there is no ``oo_type_predicate`` table: membership is then unindexed
    #: and ``find_types(predicate=...)`` answers with an honest empty page, never known=0.
    has_predicate_table: bool = True
    #: Ruling R5 / PACKAGE.md 3.5. True when this adapter was handed a connection it
    #: does not own. It then never touches autocommit and never commits: ``transaction()``
    #: brackets its writes in a SAVEPOINT and the outer commit belongs to the host.
    _borrowed = False

    def __init__(self, dialect: Dialect):
        self.d = dialect
        self.m = SqlStore(dialect, self.type_columns, self.type_projections)
        self._depth = 0
        self._failed = False
        self._savepoint_n = 0
        self._savepoint: str | None = None

    # ------------------------------------------------------------------ subclass API
    def _execute(self, sql: str, params: tuple | list = ()) -> Any:
        raise NotImplementedError

    def _fetchall(self, sql: str, params: tuple | list = ()) -> list[tuple]:
        raise NotImplementedError

    def _fetchone(self, sql: str, params: tuple | list = ()) -> tuple | None:
        raise NotImplementedError

    def _begin(self) -> None:
        raise NotImplementedError

    def _commit(self) -> None:
        raise NotImplementedError

    def _rollback(self) -> None:
        raise NotImplementedError

    @property
    def _integrity_errors(self) -> tuple[type[BaseException], ...]:
        raise NotImplementedError

    def _lock_clause(self) -> str:
        """Appended to the proposal read so ``already_decided`` stops being a race."""
        return ""

    def _columns_of(self, table: str) -> tuple[str, ...]:
        raise NotImplementedError

    # ---------------------------------------------------------------- 1 capabilities
    def capabilities(self) -> Capabilities:
        return Capabilities(
            enforces_unique_name=True,
            transactional=True,
            stores_proposals=True,
            stores_events=True,
            stores_attributes=True,
            stores_aliases=True,
            indexes_membership=True,
            counts_usage=True,
            timestamps_usage=True,
            owns_schema=self._owns_schema,
            why=dict(self._why()),
            transaction_scope="savepoint" if self._borrowed else "owned",
        )

    #: Ruling R5: a savepoint scope is DECLARED, never silent. The sentence is the one
    #: the registry surfaces wherever a result would otherwise imply durability.
    BORROWED_WHY = (
        "this adapter was opened over a connection it does not own: transaction() "
        "brackets its writes in a SAVEPOINT and never commits, so a clean exit is "
        "atomic but becomes durable only when the host commits its own transaction"
    )

    #: The same rule for owns_schema=False. [Observed, row 3d] both reference backends
    #: returned an EMPTY ``why`` for it -- C0-01's invariant ("every False flag has a
    #: non-empty why") was never violated by the fixtures, which are all owns_schema=True,
    #: and C0-09 built one and asserted ``why.get("owns_schema") or True``. The first
    #: borrowed-connection adapter (C0-12) hit it immediately.
    HOST_SCHEMA_WHY = (
        "the schema belongs to the host application, not to this adapter: migrate() "
        "verifies the columns it needs and issues no DDL (PACKAGE.md 9.3)"
    )

    def _why(self) -> dict[str, str]:
        why: dict[str, str] = {}
        if self._borrowed:
            why["transaction_scope"] = self.BORROWED_WHY
        if not self._owns_schema:
            why["owns_schema"] = self.HOST_SCHEMA_WHY
        return why

    # -------------------------------------------------------------------- 2 migrate
    def _migration_sql(self) -> list[tuple[int, str, str]]:
        return load_migrations(self.backend_name)

    def _current_version(self) -> int | None:
        # Over a BORROWED connection the probe runs inside its own savepoint. Postgres
        # aborts the whole transaction on a failed statement, and the owned-connection
        # recovery below is a bare ROLLBACK -- which on a host's connection would
        # discard work that is not ours. Found while implementing ruling R5: the very
        # first call a borrowed adapter makes is this probe, and on a fresh store it
        # fails by design.
        if self._borrowed:
            probe = self._next_savepoint("oo_probe")
            self._execute(f"SAVEPOINT {probe}")
            try:
                row = self._fetchone("SELECT max(version) FROM oo_schema_version")
            except Exception:
                self._execute(f"ROLLBACK TO SAVEPOINT {probe}")
                self._execute(f"RELEASE SAVEPOINT {probe}")
                return None
            self._execute(f"RELEASE SAVEPOINT {probe}")
            return None if row is None else row[0]
        try:
            row = self._fetchone("SELECT max(version) FROM oo_schema_version")
        except Exception:
            self._recover_from_failed_probe()
            return None
        return None if row is None else row[0]

    def _recover_from_failed_probe(self) -> None:
        """Postgres aborts the whole transaction on a failed statement; SQLite does not."""
        return None

    def _required_columns(self) -> dict[str, tuple[str, ...]]:
        """What a verify-only migrate() insists on when the schema belongs elsewhere."""
        return {
            "oo_type": (
                "namespace",
                "kind",
                "name",
                "definition",
                "created_by",
                "status",
                "provenance_json",
            ),
        }

    def migrate(self) -> int:
        migrations = self._migration_sql()
        latest = max(v for v, _, _ in migrations)
        current = self._current_version()

        if not self._owns_schema:
            # Verify-only. Never issues DDL against a schema it does not own.
            missing: list[str] = []
            for table, columns in self._required_columns().items():
                have = set(self._columns_of(table))
                if not have:
                    missing.append(f"{table} (table absent)")
                    continue
                missing.extend(f"{table}.{c}" for c in columns if c not in have)
            if missing:
                raise SchemaMismatch("store is missing: " + ", ".join(sorted(missing)))
            return current if current is not None else latest

        if current is not None and current > latest:
            raise StoreVersionUnknown(
                f"store is at version {current}; this package knows up to {latest}"
            )

        for version, slug, sql in migrations:
            if current is not None and version <= current:
                continue
            with self.transaction():
                for statement in split_statements(sql):
                    self._execute(statement)
                self._execute("DELETE FROM oo_schema_version")
                self._execute(
                    f"INSERT INTO oo_schema_version (version, applied_at, note) "
                    f"VALUES ({self.d.ph}, {self.d.ph}, {self.d.ph})",
                    (version, self.d.enc_ts(datetime.now(UTC)), slug),
                )
            current = version
        return latest

    # ---------------------------------------------------------------- 3 transaction
    def _next_savepoint(self, prefix: str = "oo") -> str:
        self._savepoint_n += 1
        return f"{prefix}_{self._savepoint_n}"

    def _open_scope(self) -> None:
        """Depth 0 entry. Owned: BEGIN. Borrowed: SAVEPOINT -- ruling R5."""
        if self._borrowed:
            self._savepoint = self._next_savepoint()
            self._execute(f"SAVEPOINT {self._savepoint}")
        else:
            self._begin()

    def _close_scope(self) -> None:
        """Depth 0 clean exit. Owned: COMMIT. Borrowed: RELEASE -- the outer commit is
        the host's and this adapter never issues it."""
        if self._borrowed:
            self._execute(f"RELEASE SAVEPOINT {self._savepoint}")
            self._savepoint = None
        else:
            self._commit()

    def _abort_scope(self) -> None:
        """Depth 0 failure. Owned: ROLLBACK. Borrowed: ROLLBACK TO, then RELEASE, which
        leaves the HOST's transaction open with everything before the savepoint intact."""
        if self._borrowed:
            self._execute(f"ROLLBACK TO SAVEPOINT {self._savepoint}")
            self._execute(f"RELEASE SAVEPOINT {self._savepoint}")
            self._savepoint = None
        else:
            self._rollback()

    @contextmanager
    def transaction(self):
        """Re-entrant: an inner call joins the outermost transaction -- or, over a
        borrowed connection, the outermost savepoint (ruling R5 point 3)."""
        if self._depth == 0:
            self._open_scope()
            self._failed = False
        self._depth += 1
        try:
            yield
        except BaseException:
            self._depth -= 1
            if self._depth == 0:
                self._abort_scope()
                self._failed = False
            else:
                self._failed = True
            raise
        else:
            self._depth -= 1
            if self._depth == 0:
                if self._failed:
                    self._failed = False
                    self._abort_scope()
                else:
                    self._close_scope()

    # ------------------------------------------------------------------- 4 put_type
    def put_type(self, rec: TypeRecord, *, expect_absent: bool = False) -> TypeRecord:
        now = datetime.now(UTC)
        stamped = TypeRecord(
            **{
                **rec.__dict__,
                "created_at": rec.created_at or now,
                "updated_at": rec.updated_at or now,
            }
        )
        values = self.m.type_values(stamped)
        cols = ", ".join(self.type_columns)
        marks = self.m.marks(len(self.type_columns))
        ph = self.d.ph
        with self.transaction():
            if expect_absent:
                try:
                    self._execute(f"INSERT INTO oo_type ({cols}) VALUES ({marks})", values)
                except self._integrity_errors as exc:
                    raise AlreadyExists(
                        f"({rec.namespace}, {rec.kind}, {rec.name}) is already taken"
                    ) from exc
            else:
                updates = ", ".join(
                    f"{c} = excluded.{c}"
                    for c in self.type_columns
                    if c not in ("namespace", "kind", "name")
                )
                self._execute(
                    f"INSERT INTO oo_type ({cols}) VALUES ({marks}) "
                    f"ON CONFLICT (namespace, kind, name) DO UPDATE SET {updates}",
                    values,
                )
            if self.has_predicate_table:
                self._execute(
                    f"DELETE FROM oo_type_predicate WHERE namespace = {ph} "
                    f"AND member_kind = {ph} AND member_name = {ph}",
                    (rec.namespace, rec.kind, rec.name),
                )
                for predicate in dict.fromkeys(rec.predicates):
                    self._execute(
                        f"INSERT INTO oo_type_predicate "
                        f"(namespace, member_kind, member_name, predicate_name) "
                        f"VALUES ({ph}, {ph}, {ph}, {ph})",
                        (rec.namespace, rec.kind, rec.name, predicate),
                    )
            stored = self.get_type(rec.namespace, rec.name, kind=rec.kind)
        assert stored is not None
        return stored

    # ------------------------------------------------------------------- 5 get_type
    def _predicates_for(self, namespace: str, kind: str, name: str) -> tuple[str, ...]:
        if not self.has_predicate_table:
            # There is no membership table, so membership was never stored. Empty is the
            # honest answer for the RECORD; find_types() is where the uncertainty of the
            # QUERY is reported, with known=None and a why (PACKAGE.md 3.4 primitive 6).
            return ()
        ph = self.d.ph
        rows = self._fetchall(
            f"SELECT predicate_name FROM oo_type_predicate WHERE namespace = {ph} "
            f"AND member_kind = {ph} AND member_name = {ph} ORDER BY predicate_name",
            (namespace, kind, name),
        )
        return tuple(r[0] for r in rows)

    def get_type(
        self, namespace: str, name: str, *, kind: str | None = None
    ) -> TypeRecord | None:
        ph = self.d.ph
        cols = ", ".join(self.type_columns)
        if kind is None:
            rows = self._fetchall(
                f"SELECT {cols} FROM oo_type WHERE namespace = {ph} AND name = {ph}",
                (namespace, name),
            )
            if len(rows) > 1:
                kinds = sorted(r[1] for r in rows)
                raise AmbiguousKind(f"{name!r} exists under kinds {kinds} in {namespace!r}")
        else:
            rows = self._fetchall(
                f"SELECT {cols} FROM oo_type WHERE namespace = {ph} AND name = {ph} "
                f"AND kind = {ph}",
                (namespace, name, kind),
            )
        if not rows:
            return None
        row = rows[0]
        return self.m.type_from_row(row, self._predicates_for(namespace, row[1], row[2]))

    # ----------------------------------------------------------------- 6 find_types
    def find_types(self, q: TypeQuery) -> TypePage:
        ph = self.d.ph
        cols = ", ".join(f"t.{c}" for c in self.type_columns)
        if q.predicate is not None and not self.has_predicate_table:
            # Never known=0 -- that reads as "nothing is commentable", which is
            # INTERFACE.md 5.2's named failure. PACKAGE.md 3.4 primitive 6.
            return TypePage(
                records=(),
                known=None,
                complete=False,
                why_incomplete=self.capabilities().reason("indexes_membership"),
            )
        where: list[str] = []
        params: list[Any] = []
        joins = ""
        if q.predicate is not None:
            joins = (
                " JOIN oo_type_predicate p ON p.namespace = t.namespace "
                "AND p.member_kind = t.kind AND p.member_name = t.name"
            )
            where.append(f"p.predicate_name = {ph}")
            params.append(q.predicate)
        if q.namespace is not None:
            where.append(f"t.namespace = {ph}")
            params.append(q.namespace)
        if q.kind is not None:
            where.append(f"t.kind = {ph}")
            params.append(q.kind)
        if q.status is not None:
            where.append(f"t.status = {ph}")
            params.append(q.status)
        elif not q.include_retired:
            where.append("t.status <> 'retired'")
        if q.created_by is not None:
            where.append(f"t.created_by = {ph}")
            params.append(q.created_by)
        if q.name_in is not None:
            if not q.name_in:
                return TypePage(records=(), known=0, complete=True)
            where.append(f"t.name IN ({self.m.marks(len(q.name_in))})")
            params.extend(q.name_in)
        if q.after is not None:
            ns, kind, name = decode_cursor(q.after)
            where.append(f"(t.namespace, t.kind, t.name) > ({ph}, {ph}, {ph})")
            params.extend([ns, kind, name])
        clause = (" WHERE " + " AND ".join(where)) if where else ""
        limit = f" LIMIT {int(q.limit) + 1}" if q.limit is not None else ""
        rows = self._fetchall(
            f"SELECT {cols} FROM oo_type t{joins}{clause} "
            f"ORDER BY t.namespace, t.kind, t.name{limit}",
            params,
        )
        more = q.limit is not None and len(rows) > q.limit
        if more:
            rows = rows[: q.limit]
        records = tuple(
            self.m.type_from_row(row, self._predicates_for(row[0], row[1], row[2]))
            for row in rows
        )
        next_after = (
            encode_cursor(records[-1].namespace, records[-1].kind, records[-1].name)
            if more and records
            else None
        )
        return TypePage(
            records=records,
            known=len(records),
            complete=not more,
            why_incomplete="a page limit was applied" if more else None,
            next_after=next_after,
        )

    # --------------------------------------------------------------- 7 put_proposal
    def put_proposal(
        self, rec: ProposalRecord, *, expect_absent: bool = False
    ) -> ProposalRecord:
        cols = ", ".join(PROPOSAL_COLUMNS)
        marks = self.m.marks(len(PROPOSAL_COLUMNS))
        values = self.m.proposal_values(rec)
        with self.transaction():
            if expect_absent:
                try:
                    self._execute(f"INSERT INTO oo_proposal ({cols}) VALUES ({marks})", values)
                except self._integrity_errors as exc:
                    raise AlreadyExists(f"proposal {rec.proposal_id} already exists") from exc
            else:
                updates = ", ".join(f"{c} = excluded.{c}" for c in PROPOSAL_COLUMNS[1:])
                self._execute(
                    f"INSERT INTO oo_proposal ({cols}) VALUES ({marks}) "
                    f"ON CONFLICT (proposal_id) DO UPDATE SET {updates}",
                    values,
                )
            stored = self.get_proposal(rec.proposal_id)
        assert stored is not None
        return stored

    # --------------------------------------------------------------- 8 get_proposal
    def get_proposal(self, proposal_id: str) -> ProposalRecord | None:
        cols = ", ".join(PROPOSAL_COLUMNS)
        lock = self._lock_clause() if self._depth > 0 else ""
        row = self._fetchone(
            f"SELECT {cols} FROM oo_proposal WHERE proposal_id = {self.d.ph}{lock}",
            (proposal_id,),
        )
        return None if row is None else self.m.proposal_from_row(row)

    # ------------------------------------------------------------- 9 find_proposals
    def find_proposals(self, q: ProposalQuery) -> ProposalPage:
        ph = self.d.ph
        cols = ", ".join(PROPOSAL_COLUMNS)
        where: list[str] = []
        params: list[Any] = []
        if q.namespace is not None:
            where.append(f"namespace = {ph}")
            params.append(q.namespace)
        if q.name is not None:
            where.append(f"name = {ph}")
            params.append(q.name)
        if q.status is not None:
            where.append(f"status = {ph}")
            params.append(q.status)
        if q.after is not None:
            where.append(f"proposal_id > {ph}")
            params.append(q.after)
        clause = (" WHERE " + " AND ".join(where)) if where else ""
        limit = f" LIMIT {int(q.limit) + 1}" if q.limit is not None else ""
        rows = self._fetchall(
            f"SELECT {cols} FROM oo_proposal{clause} ORDER BY proposed_at, proposal_id{limit}",
            params,
        )
        more = q.limit is not None and len(rows) > q.limit
        if more:
            rows = rows[: q.limit]
        records = tuple(self.m.proposal_from_row(r) for r in rows)
        return ProposalPage(
            records=records,
            known=len(records),
            complete=not more,
            why_incomplete="a page limit was applied" if more else None,
            next_after=records[-1].proposal_id if more and records else None,
        )

    # -------------------------------------------------------------- 10 put_consumer
    def put_consumer(self, rec: ConsumerRecord) -> ConsumerRecord:
        cols = ", ".join(CONSUMER_COLUMNS)
        marks = self.m.marks(len(CONSUMER_COLUMNS))
        updates = ", ".join(f"{c} = excluded.{c}" for c in CONSUMER_COLUMNS[2:])
        self._execute(
            f"INSERT INTO oo_consumer ({cols}) VALUES ({marks}) "
            f"ON CONFLICT (namespace, consumer_id) DO UPDATE SET {updates}",
            self.m.consumer_values(rec),
        )
        return self.find_consumers(rec.namespace, consumer_id=rec.consumer_id)[0]

    # ------------------------------------------------------------ 11 find_consumers
    def find_consumers(
        self, namespace: str, *, gate: str | None = None, consumer_id: str | None = None
    ) -> list[ConsumerRecord]:
        ph = self.d.ph
        cols = ", ".join(CONSUMER_COLUMNS)
        where = [f"namespace = {ph}"]
        params: list[Any] = [namespace]
        if gate is not None:
            where.append(f"gate = {ph}")
            params.append(gate)
        if consumer_id is not None:
            where.append(f"consumer_id = {ph}")
            params.append(consumer_id)
        rows = self._fetchall(
            f"SELECT {cols} FROM oo_consumer WHERE {' AND '.join(where)} ORDER BY consumer_id",
            params,
        )
        return [self.m.consumer_from_row(r) for r in rows]

    # ---------------------------------------------------------------- 12 bump_usage
    def bump_usage(
        self,
        namespace: str,
        kind: str,
        name: str,
        *,
        at: datetime | None,
        by: str | None,
    ) -> None:
        ph = self.d.ph
        stamp = self.d.enc_ts(at or datetime.now(UTC))
        self._execute(
            f"INSERT INTO oo_usage (namespace, kind, name, count, first_seen, last_seen) "
            f"VALUES ({ph}, {ph}, {ph}, 1, {ph}, {ph}) "
            f"ON CONFLICT (namespace, kind, name) DO UPDATE SET "
            f"count = COALESCE(oo_usage.count, 0) + 1, "
            f"first_seen = COALESCE(oo_usage.first_seen, excluded.first_seen), "
            f"last_seen = CASE WHEN oo_usage.last_seen IS NULL "
            f"OR excluded.last_seen > oo_usage.last_seen "
            f"THEN excluded.last_seen ELSE oo_usage.last_seen END",
            (namespace, kind, name, stamp, stamp),
        )

    # ----------------------------------------------------------------- 13 get_usage
    def get_usage(self, namespace: str, kind: str, name: str) -> UsageRecord | None:
        ph = self.d.ph
        row = self._fetchone(
            f"SELECT namespace, kind, name, count, first_seen, last_seen FROM oo_usage "
            f"WHERE namespace = {ph} AND kind = {ph} AND name = {ph}",
            (namespace, kind, name),
        )
        return None if row is None else self.m.usage_from_row(row)

    # -------------------------------------------------------------- 14 append_event
    def append_event(self, rec: EventRecord) -> None:
        cols = ", ".join(EVENT_COLUMNS)
        marks = self.m.marks(len(EVENT_COLUMNS))
        self._execute(f"INSERT INTO oo_event ({cols}) VALUES ({marks})", self.m.event_values(rec))

    # --------------------------------------------------------------- 15 read_events
    def read_events(
        self,
        namespace: str,
        *,
        kind: str | None = None,
        name: str | None = None,
        proposal_id: str | None = None,
    ) -> list[EventRecord]:
        ph = self.d.ph
        cols = ", ".join(EVENT_COLUMNS)
        where = [f"namespace = {ph}"]
        params: list[Any] = [namespace]
        if kind is not None:
            where.append(f"kind = {ph}")
            params.append(kind)
        if name is not None:
            where.append(f"name = {ph}")
            params.append(name)
        if proposal_id is not None:
            where.append(f"proposal_id = {ph}")
            params.append(proposal_id)
        rows = self._fetchall(
            f"SELECT {cols} FROM oo_event WHERE {' AND '.join(where)} "
            f"ORDER BY {self.d.event_order}",
            params,
        )
        return [self.m.event_from_row(r) for r in rows]

    # ------------------------------------------------- optional attribute extension
    _ATTR_SCHEMA_COLS = (
        "namespace, kind, version, fields_json, additional, mode, registered_at, registered_by"
    )

    def put_attr_schema(self, rec: AttrSchemaRecord) -> AttrSchemaRecord:
        marks = self.m.marks(8)
        updates = (
            "fields_json = excluded.fields_json, additional = excluded.additional, "
            "mode = excluded.mode, registered_at = excluded.registered_at, "
            "registered_by = excluded.registered_by"
        )
        self._execute(
            f"INSERT INTO oo_attr_schema ({self._ATTR_SCHEMA_COLS}) VALUES ({marks}) "
            f"ON CONFLICT (namespace, kind, version) DO UPDATE SET {updates}",
            self.m.attr_schema_values(rec),
        )
        got = self.get_attr_schema(rec.namespace, rec.kind, version=rec.version)
        assert got is not None
        return got

    def get_attr_schema(
        self, namespace: str, kind: str, *, version: int | None = None
    ) -> AttrSchemaRecord | None:
        ph = self.d.ph
        if version is None:
            row = self._fetchone(
                f"SELECT {self._ATTR_SCHEMA_COLS} FROM oo_attr_schema "
                f"WHERE namespace = {ph} AND kind = {ph} ORDER BY version DESC LIMIT 1",
                (namespace, kind),
            )
        else:
            row = self._fetchone(
                f"SELECT {self._ATTR_SCHEMA_COLS} FROM oo_attr_schema "
                f"WHERE namespace = {ph} AND kind = {ph} AND version = {ph}",
                (namespace, kind, version),
            )
        return None if row is None else self.m.attr_schema_from_row(row)

    def observe_attributes(
        self,
        namespace: str,
        kind: str,
        attributes: dict[str, Any],
        *,
        at: datetime,
        schema_version: int | None,
    ) -> None:
        ph = self.d.ph
        stamp = self.d.enc_ts(at)
        for key, value in (attributes or {}).items():
            existing = self._fetchone(
                f"SELECT n, schema_versions_json FROM oo_attr_observed "
                f"WHERE namespace = {ph} AND kind = {ph} AND key = {ph}",
                (namespace, kind, key),
            )
            versions = list(self.d.dec_json(existing[1]) or []) if existing else []
            if schema_version not in versions:
                versions.append(schema_version)
            if existing is None:
                self._execute(
                    f"INSERT INTO oo_attr_observed (namespace, kind, key, n, first_seen, "
                    f"last_seen, example_json, schema_versions_json) "
                    f"VALUES ({ph}, {ph}, {ph}, 1, {ph}, {ph}, {ph}, {ph})",
                    (
                        namespace,
                        kind,
                        key,
                        stamp,
                        stamp,
                        self.d.enc_json(value),
                        self.d.enc_json(versions),
                    ),
                )
            else:
                self._execute(
                    f"UPDATE oo_attr_observed SET n = n + 1, last_seen = {ph}, "
                    f"example_json = {ph}, schema_versions_json = {ph} "
                    f"WHERE namespace = {ph} AND kind = {ph} AND key = {ph}",
                    (
                        stamp,
                        self.d.enc_json(value),
                        self.d.enc_json(versions),
                        namespace,
                        kind,
                        key,
                    ),
                )

    def read_attr_observed(
        self, namespace: str, *, kind: str | None = None
    ) -> list[AttrObservedRecord]:
        ph = self.d.ph
        cols = (
            "namespace, kind, key, n, first_seen, last_seen, example_json, schema_versions_json"
        )
        where = [f"namespace = {ph}"]
        params: list[Any] = [namespace]
        if kind is not None:
            where.append(f"kind = {ph}")
            params.append(kind)
        rows = self._fetchall(
            f"SELECT {cols} FROM oo_attr_observed WHERE {' AND '.join(where)} ORDER BY kind, key",
            params,
        )
        return [self.m.attr_observed_from_row(r) for r in rows]
