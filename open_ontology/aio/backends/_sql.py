# ---------------------------------------------------------------------------------
# GENERATED FILE -- do not edit. Edit open_ontology/backends/_sql.py and run:
#
#     python tools/unasync.py
#
# The sync module is the single source of truth; this is its mechanical async mirror
# (deliverable 3b). open_ontology/aio/contract/test_generated_matches_source.py fails
# if this file and its source have drifted apart.
# ---------------------------------------------------------------------------------

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
from uuid import uuid4
from typing import Any, Iterable
from open_ontology.aio.adapter import (
    AttrObservedRecord,
    AttrSchemaRecord,
    ConsumerRecord,
    EdgeRecord,
    EventRecord,
    InvocationRecord,
    ProposalRecord,
    TypeRecord,
    UsageRecord,
)
import re
from contextlib import asynccontextmanager
from pathlib import Path
from open_ontology.aio.adapter import (
    Capabilities,
    EdgePage,
    EdgeQuery,
    InvocationPage,
    ProposalPage,
    ProposalQuery,
    TypePage,
    TypeQuery,
)
from open_ontology.errors import (
    AlreadyExists,
    AmbiguousKind,
    HostTransactionRequired,
    SavepointOutOfOrder,
    SchemaMismatch,
    StoreVersionUnknown,
)

# The row <-> record mapping, the dialects and the migration loader are pure functions
# of a dialect object; the async mirror borrows them rather than copying them.
__all__ = ["AsyncBaseSqlAdapter"]

# Pure module-level helpers with no I/O in them, borrowed not copied.
from open_ontology.backends._sql import (
    CONSUMER_COLUMNS,
    Dialect,
    EDGE_COLUMNS,
    EVENT_COLUMNS,
    INVOCATION_COLUMNS,
    PROPOSAL_COLUMNS,
    SqlStore,
    TYPE_COLUMNS,
    _INCIDENT_CHUNK,
    _SAVEPOINT_STACKS,
    decode_cursor,
    decode_edge_cursor,
    encode_cursor,
    encode_edge_cursor,
    load_migrations,
    split_statements,
)


class AsyncBaseSqlAdapter:
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
        # Savepoint names are namespaced PER ADAPTER, not per connection. Two adapter
        # instances over one borrowed connection both used to start at `oo_1`, and
        # nothing in this file reasoned about the engine's savepoint-name stack -- the
        # nested case happened to work because both engines treat same-named savepoints
        # as LIFO, which is a property this code was relying on without knowing it. Row
        # 3d, second adversarial round: a collision is now impossible by construction.
        self._savepoint_token = uuid4().hex[:8]
        #: Set when a scope could not be ended safely. The adapter is then UNUSABLE, and
        #: says so on the next transaction() rather than carrying on over bookkeeping it
        #: knows is wrong -- row 3d, third adversarial round: raising out of _close_scope
        #: left _depth back at 0 and the stale name still on the shared stack, so the
        #: caller could open a fresh scope that silently abandoned the old savepoint and
        #: orphaned it forever. Refusing to corrupt the CONNECTION is not enough if the
        #: adapter's own state is left corrupt.
        self._scope_broken: str | None = None

    # ------------------------------------------------------------------ subclass API
    async def _execute(self, sql: str, params: tuple | list = ()) -> Any:
        raise NotImplementedError

    async def _fetchall(self, sql: str, params: tuple | list = ()) -> list[tuple]:
        raise NotImplementedError

    async def _fetchone(self, sql: str, params: tuple | list = ()) -> tuple | None:
        raise NotImplementedError

    async def _begin(self) -> None:
        raise NotImplementedError

    async def _commit(self) -> None:
        raise NotImplementedError

    async def _rollback(self) -> None:
        raise NotImplementedError

    @property
    def _integrity_errors(self) -> tuple[type[BaseException], ...]:
        raise NotImplementedError

    def _lock_clause(self) -> str:
        """Appended to the proposal read so ``already_decided`` stops being a race."""
        return ""

    async def _columns_of(self, table: str) -> tuple[str, ...]:
        raise NotImplementedError

    # ---------------------------------------------------------------- 1 capabilities
    async def capabilities(self) -> Capabilities:
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
            # EDGES.md 6, store version 4. All four True on this class: `oo_edge` is a
            # real table with a family index and a JSON payload column, and `oo_event`
            # has an `edge_id`. `edge_transaction_scope` is not decided separately --
            # `oo_edge` lives in the same schema on the same connection as `oo_type`,
            # so 6.2's binding rule says the two scopes MUST be equal, and deriving it
            # here rather than declaring it is how the rule cannot be broken by
            # forgetting. `edge_store_shares_connection` is the premise of that rule and
            # is stated so a host-owned edge table beside this registry can say False.
            stores_edges=True,
            stores_edge_events=True,
            indexes_edges_by_family=True,
            stores_edge_attributes=True,
            # ACTIONS.md 8, store version 5. All three True on this class: `oo_invocation`
            # is a real table with a family index, and `oo_event` has an `invocation_id`.
            # `action_transaction_scope` is DERIVED rather than declared, for the reason
            # the edge scope above is: `oo_invocation` lives in the same schema on the
            # same connection as `oo_type`, so 8.2's binding rule says the two MUST be
            # equal, and deriving it is how the rule cannot be broken by forgetting.
            stores_invocations=True,
            stores_invocation_events=True,
            indexes_invocations_by_family=True,
            why=dict(self._why()),
            transaction_scope="savepoint" if self._borrowed else "owned",
            edge_transaction_scope="savepoint" if self._borrowed else "owned",
            edge_store_shares_connection=True,
            action_transaction_scope="savepoint" if self._borrowed else "owned",
            action_store_shares_connection=True,
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

    #: EDGES.md 6.2. The edge store here is the same store, on the same connection, so
    #: its scope is the type store's -- but it is a SEPARATE declaration and it gets a
    #: separate sentence, because the sentence is what surfaces on an edge write. A
    #: caller reading `not_durable_until_host_commits:<why>` off an `add_edge` result
    #: wants to be told about the edge write it just made, not about a type write it
    #: did not. C0-12 found this empty on the first pass, which is the same shape as
    #: row 3d finding `owns_schema` with no sentence.
    BORROWED_EDGE_WHY = (
        "the edge store is this adapter's own store on the connection it was lent: "
        "an edge write is bracketed in a SAVEPOINT and never committed here, so a "
        "clean return is atomic and becomes durable only when the host commits"
    )

    #: ACTIONS.md 8.2, the third store's sentence. Its own text rather than the edge
    #: one's, because *"who commits an invocation write"* is a different question the
    #: moment the two stores are two connections -- and a `why` that names the wrong
    #: object is the shape of `why` a caller stops reading.
    BORROWED_ACTION_WHY = (
        "the invocation store is this adapter's own store on the connection it was "
        "lent: recording an invocation is bracketed in a SAVEPOINT and never committed "
        "here, so a clean return is atomic and becomes durable only when the host "
        "commits"
    )

    def _why(self) -> dict[str, str]:
        why: dict[str, str] = {}
        if self._borrowed:
            why["transaction_scope"] = self.BORROWED_WHY
            why["edge_transaction_scope"] = self.BORROWED_EDGE_WHY
            why["action_transaction_scope"] = self.BORROWED_ACTION_WHY
        if not self._owns_schema:
            why["owns_schema"] = self.HOST_SCHEMA_WHY
        return why

    # -------------------------------------------------------------------- 2 migrate
    def _migration_sql(self) -> list[tuple[int, str, str]]:
        return load_migrations(self.backend_name)

    async def _current_version(self) -> int | None:
        # Over a BORROWED connection the probe runs inside its own savepoint. Postgres
        # aborts the whole transaction on a failed statement, and the owned-connection
        # recovery below is a bare ROLLBACK -- which on a host's connection would
        # discard work that is not ours. Found while implementing ruling R5: the very
        # first call a borrowed adapter makes is this probe, and on a fresh store it
        # fails by design.
        if self._borrowed:
            self._require_host_transaction()
            probe = self._next_savepoint("oo_probe")
            await self._execute(f"SAVEPOINT {probe}")
            try:
                row = await self._fetchone("SELECT max(version) FROM oo_schema_version")
            except Exception:
                await self._execute(f"ROLLBACK TO SAVEPOINT {probe}")
                await self._execute(f"RELEASE SAVEPOINT {probe}")
                return None
            await self._execute(f"RELEASE SAVEPOINT {probe}")
            return None if row is None else row[0]
        try:
            row = await self._fetchone("SELECT max(version) FROM oo_schema_version")
        except Exception:
            await self._recover_from_failed_probe()
            return None
        return None if row is None else row[0]

    async def _recover_from_failed_probe(self) -> None:
        """Postgres aborts the whole transaction on a failed statement; SQLite does not."""
        return None

    def _required_columns(self) -> dict[str, tuple[str, ...]]:
        """What a verify-only migrate() insists on when the schema belongs elsewhere.

        The version comparison in ``migrate()`` is the general guard; this list is the
        specific one, and it exists because a host schema may carry **no version row at
        all** -- a store built by hand from this package's DDL has nothing to compare.
        Row 3e's first adversarial round found the gap by building exactly that: a host
        store laid down from the v1 DDL, on which ``migrate()`` returned a version, said
        nothing, and the first ``register_attribute_schema`` died on a raw driver error.

        **The version NUMBER is deliberately not the check.** Comparing
        ``oo_schema_version`` against this package's latest migration looks like the
        one-line fix and is wrong here: when ``owns_schema=False`` the version row is the
        HOST's statement about a schema the host maintains, and it need not track this
        package's migration numbering at all -- ``sqlite_minimal`` is a live example, a
        five-table host schema that says version 1 and is entirely correct. Refusing on
        the number would punish an honest host whose columns are all present, which is
        the failure ruling R14 named. The columns are the fact; the number is a claim.
        """
        required = {
            # Hand-listed, because a backend over a schema it does not own may
            # legitimately have FEWER `oo_type` columns and project the rest (5.7).
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
        # **Derived from this backend's own column tuples, not hand-listed**, so a
        # column added by a future store version is covered here the moment it is added
        # and nobody has to remember. Unconditional in THIS class because this class's
        # own ``capabilities()`` declares ``stores_proposals`` and ``stores_attributes``
        # True for every adapter built on it; a backend that declines either has no such
        # table and must not be failed for the absence (PACKAGE.md 3.2), which it says
        # by overriding this method -- ``sqlite_minimal`` does exactly that. (Reading the
        # flags off ``capabilities()`` here would be tidier and is wrong: it is one of
        # the fifteen primitives, so the async mirror makes it awaitable, and a subclass
        # override that does not await it breaks the base's ``migrate()``.)
        required["oo_proposal"] = PROPOSAL_COLUMNS
        # Store version 4. Same unconditional reasoning as `oo_proposal` above: THIS
        # class's `capabilities()` declares `stores_edges=True` for every adapter built
        # on it, so a host schema it sits over must have the table. A backend that
        # declines the edge store has no such table and must not be failed for the
        # absence -- which it says by overriding this method, exactly as
        # `sqlite_minimal` already does.
        required["oo_edge"] = EDGE_COLUMNS
        # Store version 5, ACTIONS.md 9.2. Same unconditional reasoning as `oo_edge`
        # above: THIS class's `capabilities()` declares `stores_invocations=True` for
        # every adapter built on it, so a host schema it sits over must have the table. A
        # backend that declines the invocation store has no such table and must not be
        # failed for the absence (PACKAGE.md 3.2) -- which it says by overriding this
        # method, exactly as `sqlite_minimal` already does.
        required["oo_invocation"] = INVOCATION_COLUMNS
        required["oo_attr_schema"] = tuple(
            c.strip() for c in self._ATTR_SCHEMA_COLS.split(",")
        )
        return required

    async def migrate(self) -> int:
        migrations = self._migration_sql()
        latest = max(v for v, _, _ in migrations)
        current = await self._current_version()

        if not self._owns_schema:
            # Verify-only. Never issues DDL against a schema it does not own.
            missing: list[str] = []
            for table, columns in self._required_columns().items():
                have = set(await self._columns_of(table))
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
            async with self.transaction():
                for statement in split_statements(sql):
                    await self._execute(statement)
                await self._execute("DELETE FROM oo_schema_version")
                await self._execute(
                    f"INSERT INTO oo_schema_version (version, applied_at, note) "
                    f"VALUES ({self.d.ph}, {self.d.ph}, {self.d.ph})",
                    (version, self.d.enc_ts(datetime.now(UTC)), slug),
                )
            current = version
        return latest

    # ---------------------------------------------------------------- 3 transaction
    def _next_savepoint(self, prefix: str = "oo") -> str:
        self._savepoint_n += 1
        return f"{prefix}_{self._savepoint_token}_{self._savepoint_n}"

    def _host_transaction_state(self) -> str | None:
        """``"open"``, ``"none"``, ``"aborted"``, or ``None`` when the driver cannot tell.

        ``"aborted"`` is a separate state and not a detail: a connection whose
        transaction has already failed is *in* a transaction and cannot take a
        SAVEPOINT, so treating it as open produced exactly the raw driver exception
        ``HostTransactionRequired`` exists to replace -- and, worse, out of the adapter's
        own constructor, before the caller could do anything about it. Reproduced in row
        3d's third adversarial round. Rule U's shape: three answers plus "I cannot tell".
        """
        return None

    def _require_host_transaction(self) -> None:
        if not self._borrowed:
            return
        state = self._host_transaction_state()
        if state == "aborted":
            raise HostTransactionRequired(
                "this adapter was opened over a connection it does not own, and that "
                "connection's transaction has ALREADY FAILED -- every statement on it "
                "is being ignored until the host ends the transaction. There is nothing "
                "this adapter can do inside an aborted transaction, including take a "
                "SAVEPOINT. Roll back (or roll back to your own savepoint) before "
                "handing the connection over (PACKAGE.md 3 item 3, consequence 1)."
            )
        if state == "none":
            raise HostTransactionRequired(
                "this adapter was opened over a connection it does not own, and that "
                "connection has no transaction on it. transaction() is a SAVEPOINT and "
                "a savepoint needs a transaction to sit inside: on Postgres it is an "
                "error, and on SQLite the outermost SAVEPOINT would START a transaction "
                "whose RELEASE COMMITS it -- granting a durability the host never asked "
                "for. Begin your transaction before lending the connection "
                "(PACKAGE.md 3 item 3, consequence 1)."
            )

    def _scope_stack(self) -> list[str]:
        return _SAVEPOINT_STACKS.setdefault(id(self.conn), [])

    def _break(self, message: str, error) -> None:
        """This adapter can no longer be trusted with a scope. Say so, from now on.

        The scope is left on the shared stack deliberately: it is still open on the
        connection, and quietly forgetting it would be the leak this replaces.
        """
        self._scope_broken = message
        raise error

    def _leave_scope_stack(self) -> None:
        """Pop this adapter's savepoint, refusing if it is not the top of the stack.

        Checked BEFORE the statement is issued, because the statement is the damage:
        both engines release cascadingly, so ending an outer scope while an inner one is
        open destroys the inner one and (on Postgres) poisons the connection.
        """
        if self._borrowed and self._host_transaction_state() == "none":
            # The host committed or rolled back while this scope was open, so the
            # savepoint is already gone. Issuing RELEASE now raises a raw driver error
            # ("no such savepoint") through a seam every other case wraps in a named
            # exception. Row 3d, third adversarial round.
            _SAVEPOINT_STACKS.pop(id(self.conn), None)
            self._break(
                "the host ended this scope's transaction",
                HostTransactionRequired(
                    "the host committed or rolled back the transaction this scope was "
                    "running inside, while the scope was still open -- so the savepoint "
                    "no longer exists and neither does anything written in it. A host "
                    "must not end its transaction while a borrowed adapter has a scope "
                    "open (PACKAGE.md 3 item 3, consequence 4). This adapter is now "
                    "unusable; construct a new one over the host's next transaction."
                ),
            )
        stack = _SAVEPOINT_STACKS.get(id(self.conn))
        if stack is None or self._savepoint not in stack:
            return
        if stack[-1] != self._savepoint:
            above = stack[stack.index(self._savepoint) + 1 :]
            self._break(
                "a scope was ended out of order",
                SavepointOutOfOrder(
                    f"this scope ({self._savepoint}) is not the innermost one open on "
                    f"this borrowed connection -- {len(above)} opened after it are still "
                    f"open ({', '.join(above)}). Ending it now would destroy them, "
                    "because both engines RELEASE and ROLLBACK TO cascadingly. Two "
                    "adapters may share one borrowed connection, but their scopes must "
                    "nest: the one opened last must finish first (PACKAGE.md 3 item 3, "
                    "consequence 4). This adapter is now unusable -- its savepoint is "
                    "still open and it will not open another."
                ),
            )
        stack.pop()
        if not stack:
            _SAVEPOINT_STACKS.pop(id(self.conn), None)

    async def _open_scope(self) -> None:
        """Depth 0 entry. Owned: BEGIN. Borrowed: SAVEPOINT -- ruling R5."""
        if self._scope_broken:
            raise SavepointOutOfOrder(
                f"this adapter is unusable: {self._scope_broken}, and its previous scope "
                "is still open on the connection. Opening another would abandon it and "
                "leave it orphaned. Construct a new adapter (PACKAGE.md 3 item 3, "
                "consequence 4)."
            )
        if self._borrowed:
            self._require_host_transaction()
            self._savepoint = self._next_savepoint()
            self._scope_stack().append(self._savepoint)
            await self._execute(f"SAVEPOINT {self._savepoint}")
        else:
            await self._begin()

    async def _close_scope(self) -> None:
        """Depth 0 clean exit. Owned: COMMIT. Borrowed: RELEASE -- the outer commit is
        the host's and this adapter never issues it."""
        if self._borrowed:
            self._leave_scope_stack()
            await self._execute(f"RELEASE SAVEPOINT {self._savepoint}")
            self._savepoint = None
        else:
            await self._commit()

    async def _abort_scope(self) -> None:
        """Depth 0 failure. Owned: ROLLBACK. Borrowed: ROLLBACK TO, then RELEASE, which
        leaves the HOST's transaction open with everything before the savepoint intact."""
        if self._borrowed:
            self._leave_scope_stack()
            await self._execute(f"ROLLBACK TO SAVEPOINT {self._savepoint}")
            await self._execute(f"RELEASE SAVEPOINT {self._savepoint}")
            self._savepoint = None
        else:
            await self._rollback()

    @asynccontextmanager
    async def transaction(self):
        """Re-entrant: an inner call joins the outermost transaction -- or, over a
        borrowed connection, the outermost savepoint (ruling R5 point 3)."""
        if self._depth == 0:
            await self._open_scope()
            self._failed = False
        self._depth += 1
        try:
            yield
        except BaseException:
            self._depth -= 1
            if self._depth == 0:
                await self._abort_scope()
                self._failed = False
            else:
                self._failed = True
            raise
        else:
            self._depth -= 1
            if self._depth == 0:
                if self._failed:
                    self._failed = False
                    await self._abort_scope()
                else:
                    await self._close_scope()

    # ------------------------------------------------------------------- 4 put_type
    async def put_type(self, rec: TypeRecord, *, expect_absent: bool = False) -> TypeRecord:
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
        async with self.transaction():
            if expect_absent:
                try:
                    await self._execute(f"INSERT INTO oo_type ({cols}) VALUES ({marks})", values)
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
                await self._execute(
                    f"INSERT INTO oo_type ({cols}) VALUES ({marks}) "
                    f"ON CONFLICT (namespace, kind, name) DO UPDATE SET {updates}",
                    values,
                )
            if self.has_predicate_table:
                await self._execute(
                    f"DELETE FROM oo_type_predicate WHERE namespace = {ph} "
                    f"AND member_kind = {ph} AND member_name = {ph}",
                    (rec.namespace, rec.kind, rec.name),
                )
                for predicate in dict.fromkeys(rec.predicates):
                    await self._execute(
                        f"INSERT INTO oo_type_predicate "
                        f"(namespace, member_kind, member_name, predicate_name) "
                        f"VALUES ({ph}, {ph}, {ph}, {ph})",
                        (rec.namespace, rec.kind, rec.name, predicate),
                    )
            stored = await self.get_type(rec.namespace, rec.name, kind=rec.kind)
        assert stored is not None
        return stored

    # ------------------------------------------------------------------- 5 get_type
    async def _predicates_for(self, namespace: str, kind: str, name: str) -> tuple[str, ...]:
        if not self.has_predicate_table:
            # There is no membership table, so membership was never stored. Empty is the
            # honest answer for the RECORD; find_types() is where the uncertainty of the
            # QUERY is reported, with known=None and a why (PACKAGE.md 3.4 primitive 6).
            return ()
        ph = self.d.ph
        rows = await self._fetchall(
            f"SELECT predicate_name FROM oo_type_predicate WHERE namespace = {ph} "
            f"AND member_kind = {ph} AND member_name = {ph} ORDER BY predicate_name",
            (namespace, kind, name),
        )
        return tuple(r[0] for r in rows)

    async def get_type(
        self, namespace: str, name: str, *, kind: str | None = None
    ) -> TypeRecord | None:
        ph = self.d.ph
        cols = ", ".join(self.type_columns)
        if kind is None:
            rows = await self._fetchall(
                f"SELECT {cols} FROM oo_type WHERE namespace = {ph} AND name = {ph}",
                (namespace, name),
            )
            if len(rows) > 1:
                kinds = sorted(r[1] for r in rows)
                raise AmbiguousKind(f"{name!r} exists under kinds {kinds} in {namespace!r}")
        else:
            rows = await self._fetchall(
                f"SELECT {cols} FROM oo_type WHERE namespace = {ph} AND name = {ph} "
                f"AND kind = {ph}",
                (namespace, name, kind),
            )
        if not rows:
            return None
        row = rows[0]
        return self.m.type_from_row(row, await self._predicates_for(namespace, row[1], row[2]))

    # ----------------------------------------------------------------- 6 find_types
    async def find_types(self, q: TypeQuery) -> TypePage:
        ph = self.d.ph
        cols = ", ".join(f"t.{c}" for c in self.type_columns)
        if q.predicate is not None and not self.has_predicate_table:
            # Never known=0 -- that reads as "nothing is commentable", which is
            # INTERFACE.md 5.2's named failure. PACKAGE.md 3.4 primitive 6.
            return TypePage(
                records=(),
                known=None,
                complete=False,
                why_incomplete=(await self.capabilities()).reason("indexes_membership"),
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
        rows = await self._fetchall(
            f"SELECT {cols} FROM oo_type t{joins}{clause} "
            f"ORDER BY t.namespace, t.kind, t.name{limit}",
            params,
        )
        more = q.limit is not None and len(rows) > q.limit
        if more:
            rows = rows[: q.limit]
        records = tuple([
            self.m.type_from_row(row, await self._predicates_for(row[0], row[1], row[2]))
            for row in rows
        ])
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
    async def put_proposal(
        self, rec: ProposalRecord, *, expect_absent: bool = False
    ) -> ProposalRecord:
        cols = ", ".join(PROPOSAL_COLUMNS)
        marks = self.m.marks(len(PROPOSAL_COLUMNS))
        values = self.m.proposal_values(rec)
        async with self.transaction():
            if expect_absent:
                try:
                    await self._execute(f"INSERT INTO oo_proposal ({cols}) VALUES ({marks})", values)
                except self._integrity_errors as exc:
                    raise AlreadyExists(f"proposal {rec.proposal_id} already exists") from exc
            else:
                updates = ", ".join(f"{c} = excluded.{c}" for c in PROPOSAL_COLUMNS[1:])
                await self._execute(
                    f"INSERT INTO oo_proposal ({cols}) VALUES ({marks}) "
                    f"ON CONFLICT (proposal_id) DO UPDATE SET {updates}",
                    values,
                )
            stored = await self.get_proposal(rec.proposal_id)
        assert stored is not None
        return stored

    # --------------------------------------------------------------- 8 get_proposal
    async def get_proposal(self, proposal_id: str) -> ProposalRecord | None:
        cols = ", ".join(PROPOSAL_COLUMNS)
        lock = self._lock_clause() if self._depth > 0 else ""
        row = await self._fetchone(
            f"SELECT {cols} FROM oo_proposal WHERE proposal_id = {self.d.ph}{lock}",
            (proposal_id,),
        )
        return None if row is None else self.m.proposal_from_row(row)

    # ------------------------------------------------------------- 9 find_proposals
    async def find_proposals(self, q: ProposalQuery) -> ProposalPage:
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
        rows = await self._fetchall(
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
    async def put_consumer(self, rec: ConsumerRecord) -> ConsumerRecord:
        cols = ", ".join(CONSUMER_COLUMNS)
        marks = self.m.marks(len(CONSUMER_COLUMNS))
        updates = ", ".join(f"{c} = excluded.{c}" for c in CONSUMER_COLUMNS[2:])
        await self._execute(
            f"INSERT INTO oo_consumer ({cols}) VALUES ({marks}) "
            f"ON CONFLICT (namespace, consumer_id) DO UPDATE SET {updates}",
            self.m.consumer_values(rec),
        )
        return (await self.find_consumers(rec.namespace, consumer_id=rec.consumer_id))[0]

    # ------------------------------------------------------------ 11 find_consumers
    async def find_consumers(
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
        rows = await self._fetchall(
            f"SELECT {cols} FROM oo_consumer WHERE {' AND '.join(where)} ORDER BY consumer_id",
            params,
        )
        return [self.m.consumer_from_row(r) for r in rows]

    # ---------------------------------------------------------------- 12 bump_usage
    async def bump_usage(
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
        await self._execute(
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
    async def get_usage(self, namespace: str, kind: str, name: str) -> UsageRecord | None:
        ph = self.d.ph
        row = await self._fetchone(
            f"SELECT namespace, kind, name, count, first_seen, last_seen FROM oo_usage "
            f"WHERE namespace = {ph} AND kind = {ph} AND name = {ph}",
            (namespace, kind, name),
        )
        return None if row is None else self.m.usage_from_row(row)

    # -------------------------------------------------------------- 14 append_event
    async def append_event(self, rec: EventRecord) -> None:
        cols = ", ".join(EVENT_COLUMNS)
        marks = self.m.marks(len(EVENT_COLUMNS))
        await self._execute(f"INSERT INTO oo_event ({cols}) VALUES ({marks})", self.m.event_values(rec))

    # --------------------------------------------------------------- 15 read_events
    async def read_events(
        self,
        namespace: str,
        *,
        kind: str | None = None,
        name: str | None = None,
        proposal_id: str | None = None,
        edge_id: str | None = None,
        invocation_id: str | None = None,
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
        # Store version 4, EDGES.md 5.2. Additive and defaulted: a caller that never
        # passes it sees exactly the pre-4b behaviour, and `read_events(namespace)`
        # with no filter still returns edge events, because they are events.
        if edge_id is not None:
            where.append(f"edge_id = {ph}")
            params.append(edge_id)
        # Store version 5, ACTIONS.md 3.5 / 9.1. Additive and defaulted for the reason
        # `edge_id` is: a caller that never passes it sees exactly the pre-6b behaviour,
        # and `read_events(namespace)` with no filter still returns invocation events,
        # because they are events.
        if invocation_id is not None:
            where.append(f"invocation_id = {ph}")
            params.append(invocation_id)
        rows = await self._fetchall(
            f"SELECT {cols} FROM oo_event WHERE {' AND '.join(where)} "
            f"ORDER BY {self.d.event_order}",
            params,
        )
        return [self.m.event_from_row(r) for r in rows]

    # ------------------------------------------------------------- 16 to 18, edges
    #
    # EDGES.md 7.1. The whole edge surface of this class is these three methods plus
    # the frontier clause below. What is NOT here is the point: no depth, no report, no
    # refusal, no notion of a family being retired -- an adapter that knew any of those
    # would be the boundary PACKAGE.md 3.1 forbids and C0-04 polices.

    def _edge_incident_clause(
        self, keys: tuple[tuple[str, str, str, str | None], ...], direction: str
    ) -> tuple[str, list[Any]]:
        """``(sql, params)`` matching any of ``keys`` on the end ``direction`` selects.

        ``instance_id IS NULL`` is written out rather than compared with ``=``, because
        a type-level endpoint stores NULL there and ``NULL = NULL`` is not true in SQL.
        A type node and an instance of it are two different endpoints, so this is a
        value to match, not a wildcard -- getting that wrong would have made
        ``neighbors(<a type>)`` silently return that type's instances' edges too.
        """
        ph = self.d.ph
        ends = {"out": ("src",), "in": ("dst",)}.get(direction, ("src", "dst"))
        alts: list[str] = []
        params: list[Any] = []
        for namespace, kind, name, instance_id in keys:
            for end in ends:
                if instance_id is None:
                    alts.append(
                        f"({end}_namespace = {ph} AND {end}_kind = {ph} "
                        f"AND {end}_name = {ph} AND {end}_instance_id IS NULL)"
                    )
                    params.extend([namespace, kind, name])
                else:
                    alts.append(
                        f"({end}_namespace = {ph} AND {end}_kind = {ph} "
                        f"AND {end}_name = {ph} AND {end}_instance_id = {ph})"
                    )
                    params.extend([namespace, kind, name, instance_id])
        return "(" + " OR ".join(alts) + ")", params

    def _edge_base_where(self, q: EdgeQuery) -> tuple[list[str], list[Any]]:
        ph = self.d.ph
        where: list[str] = []
        params: list[Any] = []
        if q.namespace is not None:
            where.append(f"namespace = {ph}")
            params.append(q.namespace)
        if q.families is not None:
            if not q.families:
                # An explicitly empty family list is a query for nothing, and that is a
                # fact rather than an uncertainty -- the same shape `find_types` gives
                # `name_in=()`.
                where.append("1 = 0")
            else:
                where.append(f"family IN ({self.m.marks(len(q.families))})")
                params.extend(q.families)
        if q.edge_ids is not None:
            if not q.edge_ids:
                where.append("1 = 0")
            else:
                where.append(f"edge_id IN ({self.m.marks(len(q.edge_ids))})")
                params.extend(q.edge_ids)
        if not q.include_retracted:
            where.append("status <> 'retracted'")
        return where, params

    # 16
    async def put_edge(self, rec: EdgeRecord, *, expect_absent: bool = False) -> EdgeRecord:
        now = datetime.now(UTC)
        stamped = EdgeRecord(
            **{
                **rec.__dict__,
                "created_at": rec.created_at or now,
                # Not ``rec.updated_at or now``: an amendment must move this, and a
                # caller handing back the record it just read would otherwise freeze
                # ``updated_at`` at the original write forever.
                "updated_at": now,
            }
        )
        cols = ", ".join(EDGE_COLUMNS)
        marks = self.m.marks(len(EDGE_COLUMNS))
        async with self.transaction():
            if expect_absent:
                try:
                    await self._execute(
                        f"INSERT INTO oo_edge ({cols}) VALUES ({marks})",
                        self.m.edge_values(stamped),
                    )
                except self._integrity_errors as exc:
                    raise AlreadyExists(f"edge {rec.edge_id!r} is already stored") from exc
            else:
                updates = ", ".join(
                    f"{c} = excluded.{c}" for c in EDGE_COLUMNS if c != "edge_id"
                )
                await self._execute(
                    f"INSERT INTO oo_edge ({cols}) VALUES ({marks}) "
                    f"ON CONFLICT (edge_id) DO UPDATE SET {updates}",
                    self.m.edge_values(stamped),
                )
            stored = await self.get_edge(rec.edge_id)
        assert stored is not None
        return stored

    # 17
    async def get_edge(self, edge_id: str) -> EdgeRecord | None:
        ph = self.d.ph
        cols = ", ".join(EDGE_COLUMNS)
        row = await self._fetchone(f"SELECT {cols} FROM oo_edge WHERE edge_id = {ph}", (edge_id,))
        return None if row is None else self.m.edge_from_row(row)

    # 18
    async def find_edges(self, q: EdgeQuery) -> EdgePage:
        ph = self.d.ph
        cols = ", ".join(EDGE_COLUMNS)
        base, base_params = self._edge_base_where(q)

        cursor_clause = ""
        cursor_params: list[Any] = []
        if q.after is not None:
            at, edge_id = decode_edge_cursor(q.after)
            cursor_clause = f"(created_at, edge_id) > ({ph}, {ph})"
            cursor_params = [self.d.enc_ts(at), edge_id]

        if q.incident_to is None:
            chunks: list[tuple[str, list[Any]]] = [("", [])]
        elif not q.incident_to:
            # An empty frontier is a query about nothing, and that is a fact.
            return EdgePage(records=(), known=0, complete=True)
        else:
            keys = tuple(dict.fromkeys(q.incident_to))
            chunks = [
                self._edge_incident_clause(keys[i : i + _INCIDENT_CHUNK], q.direction)
                for i in range(0, len(keys), _INCIDENT_CHUNK)
            ]

        limit_sql = f" LIMIT {int(q.limit) + 1}" if q.limit is not None else ""
        collected: dict[str, EdgeRecord] = {}
        for clause, clause_params in chunks:
            where = list(base)
            params = list(base_params)
            if clause:
                where.append(clause)
                params.extend(clause_params)
            if cursor_clause:
                where.append(cursor_clause)
                params.extend(cursor_params)
            sql = (
                f"SELECT {cols} FROM oo_edge"
                + ((" WHERE " + " AND ".join(where)) if where else "")
                + f" ORDER BY created_at, edge_id{limit_sql}"
            )
            for row in await self._fetchall(sql, params):
                rec = self.m.edge_from_row(row)
                collected.setdefault(rec.edge_id, rec)

        # The k-way merge. Each chunk returned its own sorted prefix, so the union is
        # re-sorted before the window is taken; that is what makes the cursor correct
        # across a split frontier rather than only within one chunk. Deduped first --
        # one edge can match two frontier keys at once (both of its ends in the
        # frontier, or a self-loop), and counting it twice would make the report's
        # `known` a lie about the number of edges.
        ordered = sorted(collected.values(), key=lambda r: (r.created_at, r.edge_id))
        more = q.limit is not None and len(ordered) > q.limit
        if more:
            ordered = ordered[: q.limit]

        # EDGES.md 4.3: a default that hides things sets complete=False, which is
        # `list_types(include_retired=)`'s own rule (INTERFACE.md 5.6). The adapter is
        # the only party that can know whether anything WAS hidden, so the adapter says
        # so -- a statement about this page, not a decision about policy.
        suppressed = 0 if q.include_retracted else await self._count_suppressed_edges(q, chunks)

        why: str | None = None
        if more:
            why = "a page limit was applied"
        elif suppressed:
            why = (
                f"{suppressed} retracted edge(s) were suppressed by "
                f"include_retracted=False (EDGES.md 4.3)"
            )
        return EdgePage(
            records=tuple(ordered),
            known=len(ordered),
            complete=not more and not suppressed,
            why_incomplete=why,
            next_after=(
                encode_edge_cursor(ordered[-1].created_at, ordered[-1].edge_id)
                if more and ordered
                else None
            ),
        )

    async def _count_suppressed_edges(self, q: EdgeQuery, chunks) -> int:
        """How many retracted edges this query would have returned. EDGES.md 4.3.

        Counted over the WHOLE matching set rather than over the current page, because
        the claim is about the answer and not about the window: a caller told
        ``complete=True`` on page one and ``complete=False`` on page three has been told
        two different things about one query.
        """
        ph = self.d.ph
        where_base, params_base = self._edge_base_where(
            EdgeQuery(
                namespace=q.namespace,
                families=q.families,
                edge_ids=q.edge_ids,
                include_retracted=True,
            )
        )
        seen: set[str] = set()
        for clause, clause_params in chunks:
            where = list(where_base) + [f"status = {ph}"]
            params = list(params_base) + ["retracted"]
            if clause:
                where.append(clause)
                params.extend(clause_params)
            rows = await self._fetchall(
                "SELECT edge_id FROM oo_edge WHERE " + " AND ".join(where), params
            )
            seen.update(r[0] for r in rows)
        return len(seen)

    # -------------------------------------------------- 19 to 21, invocations
    #
    # ACTIONS.md 9. The whole invocation surface of this class is these three methods.
    # What is NOT here is the point: no gate, no verdict logic, no notion of an effect
    # being undeclared -- the `effect_undeclared` filter below is a predicate over a
    # STORED warnings list, not a judgement about one. An adapter that knew what a gate
    # verdict MEANS would be the boundary PACKAGE.md 3.1 forbids and C0-04 polices.

    # 19
    async def put_invocation(self, rec: InvocationRecord) -> InvocationRecord:
        now = datetime.now(UTC)
        stamped = InvocationRecord(
            **{**rec.__dict__, "created_at": rec.created_at or now}
        )
        cols = ", ".join(INVOCATION_COLUMNS)
        marks = self.m.marks(len(INVOCATION_COLUMNS))
        async with self.transaction():
            # **`expect_absent` is not a parameter here, and the absence is a decision.**
            # `invocation_id` is minted ABOVE the store (PACKAGE.md 4.2), so a collision
            # is not a case a caller can reach; and an invocation ledger is append-only
            # by construction, so there is no amend path for an upsert to serve. A plain
            # INSERT is the honest statement: this row is new, and a duplicate id is a
            # constraint violation rather than a silent overwrite of a
            # provenance-bearing record (INTERFACE.md 5.8).
            try:
                await self._execute(
                    f"INSERT INTO oo_invocation ({cols}) VALUES ({marks})",
                    self.m.invocation_values(stamped),
                )
            except self._integrity_errors as exc:
                raise AlreadyExists(
                    f"invocation {rec.invocation_id!r} is already stored"
                ) from exc
            stored = await self.get_invocation(rec.invocation_id)
        assert stored is not None
        return stored

    # 20
    async def get_invocation(self, invocation_id: str) -> InvocationRecord | None:
        ph = self.d.ph
        cols = ", ".join(INVOCATION_COLUMNS)
        row = await self._fetchone(
            f"SELECT {cols} FROM oo_invocation WHERE invocation_id = {ph}",
            (invocation_id,),
        )
        return None if row is None else self.m.invocation_from_row(row)

    # 21
    async def find_invocations(
        self,
        *,
        family: str | None = None,
        namespace: str | None = None,
        actor: str | None = None,
        outcome: str | None = None,
        since: datetime | None = None,
        gate_verdict: str | None = None,
        effect_undeclared: bool | None = None,
        unreviewed: bool | None = None,
        compensates: str | None = None,
        after: str | None = None,
        limit: int = 100,
    ) -> InvocationPage:
        ph = self.d.ph
        cols = ", ".join(INVOCATION_COLUMNS)
        where: list[str] = []
        params: list[Any] = []
        for column, value in (
            ("family", family),
            ("namespace", namespace),
            ("created_by_actor", actor),
            ("outcome", outcome),
            ("gate_verdict", gate_verdict),
            # ACTIONS.md 9's forward pointer, asked backwards. One indexed equality --
            # the facade derives `compensated_by` from it rather than walking the ledger.
            ("compensates", compensates),
        ):
            if value is not None:
                where.append(f"{column} = {ph}")
                params.append(value)
        if since is not None:
            where.append(f"created_at >= {ph}")
            params.append(self.d.enc_ts(since))
        if effect_undeclared is not None:
            # **Pushed down, and the push-down is why ACTIONS.md 4's claim is a claim.**
            # This filter and the two beside it were on the facade and on no primitive,
            # so *"the registry filters above the store"* meant reading a `limit`-bounded
            # page and filtering it afterwards -- which returned ZERO overrides from a
            # 2,399-row ledger that had one. A floor of zero is indistinguishable from a
            # clean deployment. It is a LIKE over the stored warnings text rather than a
            # judgement: the adapter matches a string it never interprets (3.1).
            clause = self.d.warning_prefix_clause("warnings_json")
            params.append("effect_undeclared:%")
            where.append(clause if effect_undeclared else f"NOT ({clause})")
        if unreviewed is not None:
            # **Half of this one pushes down and half cannot, and saying which is the
            # honest form.** *Has this invocation been reviewed?* is a fact about this
            # row -- the `invocation_reviewed` event -- and pushes down as far as
            # "no such event exists". *Is the family in `review` mode?* is a fact about
            # ANOTHER row's attributes, and the registry answers it above the store over
            # a set of families it has already materialised. The report says
            # `complete=False` either way.
            exists = (
                f"EXISTS (SELECT 1 FROM oo_event e WHERE "
                f"e.invocation_id = oo_invocation.invocation_id AND "
                f"e.event = {ph})"
            )
            params.append("invocation_reviewed")
            where.append(f"NOT {exists}" if unreviewed else exists)
        if after is not None:
            at, invocation_id = decode_edge_cursor(after)
            where.append(f"(created_at, invocation_id) > ({ph}, {ph})")
            params.extend([self.d.enc_ts(at), invocation_id])
        sql = (
            f"SELECT {cols} FROM oo_invocation"
            + ((" WHERE " + " AND ".join(where)) if where else "")
            + f" ORDER BY created_at, invocation_id LIMIT {int(limit) + 1}"
        )
        rows = [self.m.invocation_from_row(r) for r in await self._fetchall(sql, params)]
        more = len(rows) > limit
        if more:
            rows = rows[:limit]
        return InvocationPage(
            records=tuple(rows),
            known=len(rows),
            complete=not more,
            why_incomplete="a page limit was applied" if more else None,
            next_after=(
                encode_edge_cursor(rows[-1].created_at, rows[-1].invocation_id)
                if more and rows
                else None
            ),
        )

    # ------------------------------------------------- optional attribute extension
    #: ``name`` is store version 2 (ruling R10). The empty string is the per-kind
    #: schema: no type name can be empty (INTERFACE.md 2.1), so one NOT NULL column
    #: carries both cases and the primary key stays a primary key.
    _ATTR_SCHEMA_COLS = (
        "namespace, kind, name, version, fields_json, additional, mode, "
        "registered_at, registered_by"
    )

    async def put_attr_schema(self, rec: AttrSchemaRecord) -> AttrSchemaRecord:
        marks = self.m.marks(9)
        updates = (
            "fields_json = excluded.fields_json, additional = excluded.additional, "
            "mode = excluded.mode, registered_at = excluded.registered_at, "
            "registered_by = excluded.registered_by"
        )
        await self._execute(
            f"INSERT INTO oo_attr_schema ({self._ATTR_SCHEMA_COLS}) VALUES ({marks}) "
            f"ON CONFLICT (namespace, kind, name, version) DO UPDATE SET {updates}",
            self.m.attr_schema_values(rec),
        )
        got = await self.get_attr_schema(
            rec.namespace, rec.kind, name=rec.name, version=rec.version
        )
        assert got is not None
        return got

    async def get_attr_schema(
        self,
        namespace: str,
        kind: str,
        *,
        name: str | None = None,
        version: int | None = None,
    ) -> AttrSchemaRecord | None:
        ph = self.d.ph
        # Exact lookup only -- ``name=None`` fetches the PER-KIND schema and never a
        # name-level one. The fallback from a name to its kind is the registry's
        # decision (PACKAGE.md 5.2b), and hiding it in the storage layer would make a
        # primitive answer a question about policy.
        if version is None:
            row = await self._fetchone(
                f"SELECT {self._ATTR_SCHEMA_COLS} FROM oo_attr_schema "
                f"WHERE namespace = {ph} AND kind = {ph} AND name = {ph} "
                f"ORDER BY version DESC LIMIT 1",
                (namespace, kind, name or ""),
            )
        else:
            row = await self._fetchone(
                f"SELECT {self._ATTR_SCHEMA_COLS} FROM oo_attr_schema "
                f"WHERE namespace = {ph} AND kind = {ph} AND name = {ph} "
                f"AND version = {ph}",
                (namespace, kind, name or "", version),
            )
        return None if row is None else self.m.attr_schema_from_row(row)

    async def observe_attributes(
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
            existing = await self._fetchone(
                f"SELECT n, schema_versions_json FROM oo_attr_observed "
                f"WHERE namespace = {ph} AND kind = {ph} AND key = {ph}",
                (namespace, kind, key),
            )
            versions = list(self.d.dec_json(existing[1]) or []) if existing else []
            if schema_version not in versions:
                versions.append(schema_version)
            if existing is None:
                await self._execute(
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
                await self._execute(
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

    async def read_attr_observed(
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
        rows = await self._fetchall(
            f"SELECT {cols} FROM oo_attr_observed WHERE {' AND '.join(where)} ORDER BY kind, key",
            params,
        )
        return [self.m.attr_observed_from_row(r) for r in rows]
