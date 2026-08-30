# Rulings 2026-08-29 — five findings routed upstream from beacon 21.1, and R5 (savepoint transactions)

> **Package renamed** `open_ontology` → `ontoloche` at commit <rename-sha> (2026-08-30); the commands and paths quoted below are as recorded at the time.

**Source:** beacon `spec-ontology-2b` landed roadmap row 21.1 (`docs/specs/2026-08-28-ontology-2b-work-link-types-backend-design.md`, beacon `6e87d61a`) and routed five findings to open-ontology as protocol/implementation defects, plus one ruling the beacon program says is ours: R5. Relayed by the general supervisor 2026-08-29 ~00:25; full text recovered from its transcript.
**Verified before ruling (2026-08-29 00:35, open-ontology `main` at `b19e131`):** each finding checked against the landed code and doc; citations inline.

---

## R5 — an adapter over a host-owned session MAY implement `transaction()` as a SAVEPOINT. Ruled YES, with a declared scope.

**The question.** `PACKAGE.md` §3 item 3 [Observed]: *"Groups writes. Commits on clean exit, rolls back on any exception. Re-entrant calls join the outermost transaction (savepoints are not required)."* It never contemplates a session the adapter does not own. Beacon's `AsyncSession` owns its transaction; a "no" would force beacon to open a second connection and lose transaction sharing — the exact thing ruling R1 and row 3b exist to provide.

**Ruling.**
1. **Yes.** Over a host-owned session, `transaction()` opens a `SAVEPOINT` at depth 0, **RELEASEs** it on clean exit, and **ROLLBACK TO SAVEPOINT** on exception. The outer commit belongs to the host and is never issued by the adapter.
2. **Declared, not silent.** `Capabilities` gains `transaction_scope: "owned" | "savepoint"` (default `"owned"`). `transactional` stays REQUIRED `True` — a savepoint adapter is still transactional: **G2 atomicity is preserved inside the host's transaction; durability at clean exit is the host's, and the registry says so** (Rule U — a `why`-style sentence surfaces in any result that would otherwise imply durability).
3. **Re-entrancy unchanged.** Nested calls join the outermost savepoint.
4. **The reference `AsyncPostgresAdapter` is currently wrong for borrowed connections** [Observed `open_ontology/aio/backends/postgres.py:70` `await conn.set_autocommit(True)`; `_sql.py:222` commits at depth 0]: given a borrowed connection it must not touch autocommit or commit — borrowed ⇒ `transaction_scope="savepoint"`. That is U1 below, a bug fix with a test.
5. **What "no" would have cost:** re-speccing beacon 21.2 around a second connection, and an adapter that shares a connection without sharing a transaction — which is worse than either honest option. Recorded so the choice is reviewable.

**Amendments this ruling requires:** `PACKAGE.md` §3 item 3 (scope semantics), §3.5 (`transaction_scope` in `Capabilities` with its `why`), §6 (a C0-03 variant: an exception inside `transaction()` on a borrowed connection leaves the host's outer transaction open and the savepoint rolled back). Row 3d carries them.

---

## The five findings — disposition

| # | Finding (beacon's words, abridged) | Verified? | Disposition |
|---|---|---|---|
| **U1** | `transaction()` on a host-owned session: `AsyncPostgresAdapter` accepts a borrowed connection then forces `set_autocommit(True)` and commits at depth 0 — sharing a connection is not sharing a transaction. Corrects note 2 of the 3b relay. | **Yes** — `postgres.py:70`, `_sql.py:199-222` | **Row 3d.** Fix per R5: borrowed ⇒ savepoint scope; capability declared; C0-03 borrowed-connection variant in both suites. |
| **U2** | The contract suite cannot verify a *natively* degraded backend — it simulates degradation via `DegradedAdapter`; `test_c9_02` asserts a successful forced retire on the plain fixture. 21.2 writes a beacon-side harness instead. | **Yes** — `contract/doubles.py:233`, `test_c9_02` | **Row 3d.** Add a third *reference* leg to §6: a real SQLite backend built natively without the optional stores (`stores_events=False`, `stores_attributes=False`, `indexes_membership=False`, `owns_schema=False`), and run the whole suite against it. Beacon's harness stays, but conformance must be provable from this repo alone — that is the A5 gate's meaning. |
| **U3** | `stores_attributes` is binary: a host-owned backend with pre-existing typed columns cannot say "I store arbitrary keys faithfully AND own two typed columns". | **Yes** — `Capabilities` block, PACKAGE §3.5 | **Row 3d.** Add `attribute_projections: frozenset[str]` (keys the backend owns as typed columns; round-trip through the column, not the JSON) alongside `stores_attributes`. C0-06 gains the projected-key case. Small; no INTERFACE change. |
| **U4** | `PACKAGE.md` §3.3's printed `TypeRecord` has diverged from the landed dataclass — `retire_reason` / `retired_by` / `retired_at` / `successor` absent from the doc a third-party author reads. | **Yes** — `adapter.py:118-121` vs PACKAGE §3.3 | **Row 3d, mechanical.** Sync the doc; extend the 3c spec-drift check (`941256f`) to cover the printed dataclasses so this class of drift is caught by the gate. |
| **U5** | `stores_events=False` with no registered consumers gets neither refusal nor audit trail on `retire(force=True)` — guard was `if report.gates_on and force and not stores_events`. | **Already fixed on `main`** — `registry.py:1223` is now `if force and not self.caps.stores_events` (3c adversarial round; see the comment above it) | **No row.** Beacon's finding was against a pre-3c tip; relay the commit. |

## Consequence for the 3b relay

Note 2 of `briefs/2026-08-28-relay-3b-landed-for-beacon-21-2.md` ("takes an already-open connection so transactions are shared") was **wrong as landed** — the connection was shared, the transaction was not. Corrected by R5 + U1; beacon 21.2 should build against 3d, not 3b, for the transaction seam.
