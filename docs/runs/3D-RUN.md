# 3D-RUN — roadmap row 3d: the upstream fixes from beacon 21.1, and what three adversarial rounds did to them

> **Package renamed** `open_ontology` → `ontoloche` at commit 802ddf0 (2026-08-30); the commands and paths quoted below are as recorded at the time.

**Row:** 3d. **Date:** 2026-08-29. **Repo:** `open-ontology`, `main`.
**What it carried:** beacon findings **U1–U4** (routed upstream from their 21.1 spec), rulings **R5**, **R8**, **R12**, **R13**.
**Why it exists:** beacon's row 21.2 builds an adapter over its own async database session. Without U1, *sharing a connection is not sharing a transaction*. **This row is that seam.**

---

## 1. The headline, in numbers

| | before (row 3c) | after |
|---|---|---|
| contract ids (`PACKAGE.md` §6.2) | 124 | **129** |
| sync suite, one run | `261 passed` | **`340 passed, 64 skipped`** |
| async suite, one run | `295 passed` | **`374 passed, 64 skipped`** |
| reference legs per run | 2 | **3** |
| `check_capability_matrix.py` | 9 configurations | **10** |
| `check_spec_drift.py` | INTERFACE only, 15 shapes | **INTERFACE 15 + 13 calls, PACKAGE 13 shapes** |

The skips are not a regression: they are the natively-degraded third leg reporting, per contract id, what it could not exercise and why (§6.4, ruling R12). **Both full legs exercise 126 of 129 ids; nothing that ran before is skipped now.**

---

## 2. The three suite tails, verbatim

### 2.1 Sync — `pytest --pyargs open_ontology.contract -q`

```
CONFORMANCE (PACKAGE.md 6.1)
  backends exercised: postgres, sqlite, sqlite_minimal
  resolver: the shipped DeterministicResolver (2.6's fixed point)
  nonbinding tests excluded from the verdict: none
  coverage, per leg (PACKAGE.md 6.4 / ruling R12):
    sqlite          CONFORMANT: 126 ids exercised, 1 not exercisable on this backend (listed)
                      1: PACKAGE.md 5.7 -- this backend stores arbitrary attributes, so a census restricted to its
                        projections has no subject here. C15-02 is the full case.
                         C15-09
    postgres        CONFORMANT: 126 ids exercised, 1 not exercisable on this backend (listed)
                      1: PACKAGE.md 5.7 -- this backend stores arbitrary attributes, so a census restricted to its
                        projections has no subject here. C15-02 is the full case.
                         C15-09
    sqlite_minimal  CONFORMANT: 65 ids exercised, 62 not exercisable on this backend (listed)
                      21: PACKAGE.md 3.2 -- this backend declares stores_proposals=False, which 3.2 says is
                        conformant. This test needs it as scaffolding, not as its subject: this store has no proposal
                        table: a decision is recorded on the type row and a pending proposal has nowhere to live
                         C15-03, C15-06, C3-06, C3-07, C4-02, C4-04, C4-05, C5-01, C5-03, C5-04, C5-05, C5-06, C5-07,
                           C5-08, C5-09, C5-10, C5-11, C6-06, C8-01, C8-02, C8-05
                      18: PACKAGE.md 3.2 -- this backend declares indexes_membership=False, which 3.2 says is
                        conformant. This test needs it as scaffolding, not as its subject: this store has no predicate-
                        membership table, so which types satisfy a predicate is not a question it can answer
                         C1-04, C1-09, C10-01, C10-02, C11-01, C12-01, C2-01, C2-03, C2-04, C2-05, C3-10, C4-08, C6-01,
                           C6-03, C9-01, C9-02, C9-03, C9-04
                      12: PACKAGE.md 3.2 -- this backend declares stores_events=False, which 3.2 says is conformant.
                        This test needs it as scaffolding, not as its subject: this store has no event table, so there
                        is no audit trail to append to and no history to read back
                         C0-03, C10-05, C10-06, C10-07, C14-03, C16-01, C16-02, C16-03, C16-04, C3-11, C9-06, C9-07
                      9: PACKAGE.md 3.2 -- this backend declares stores_attributes=False, which 3.2 says is
                        conformant. This test needs it as scaffolding, not as its subject: this store has no attributes
                        column: the host schema owns its columns and arbitrary keys have nowhere to go
                         C12-04, C13-03, C13-04, C13-05, C14-01, C15-01, C15-02, C15-05, C15-08
                      1: PACKAGE.md 7.3 B4 -- this backend declares stores_proposals=False, so propose_type returns a
                        TypeEntry and there is no proposal for two approvals to race. The G1 half above ran and held on
                        this store.
                         C0-08
                      1: PACKAGE.md 9.3 -- this backend declares owns_schema=False, so migrate() issues no DDL and the
                        atomic-migration half of C0-05 has nothing to drive. Idempotence was asserted; C0-09 is the
                        subject for verify-only migrate().
                         C0-05
    (+2 backend-independent, run once: C0-04, C14-07)
  A conformance claim without its coverage line is not a claim (ruling R12).
340 passed, 64 skipped in 59.39s
```

### 2.2 Async — `pytest --pyargs open_ontology.aio.contract -q`

The same coverage block, same three legs, same per-leg numbers:

```
CONFORMANCE (PACKAGE.md 6.1)
  backends exercised: postgres, sqlite, sqlite_minimal
  resolver: the shipped DeterministicResolver (2.6's fixed point)
  nonbinding tests excluded from the verdict: none
  coverage, per leg (PACKAGE.md 6.4 / ruling R12):
    sqlite          CONFORMANT: 126 ids exercised, 1 not exercisable on this backend (listed)
    postgres        CONFORMANT: 126 ids exercised, 1 not exercisable on this backend (listed)
    sqlite_minimal  CONFORMANT: 65 ids exercised, 62 not exercisable on this backend (listed)
    (+2 backend-independent, run once: C0-04, C14-07)
  A conformance claim without its coverage line is not a claim (ruling R12).
374 passed, 64 skipped in 56.61s
```

**The arithmetic closes on every leg**, and that is checked mechanically rather than by eye: `126 + 1 + 2 = 129` on both full legs, `65 + 62 + 2 = 129` on the degraded one. A leg short of the run's id universe prints `INCOMPLETE COVERAGE` and reads `NOT CONFORMANT`.

### 2.3 The third leg is a real store, not a wrapper

`sqlite_minimal` ([`open_ontology/backends/sqlite_minimal.py`](https://github.com/stephan-dyson/open-ontology/blob/main/open_ontology/backends/sqlite_minimal.py)) has **five tables where the reference schema has nine**. No `oo_proposal`, no `oo_event`, no `oo_type_predicate`, and an `oo_type` with no `attributes_json` but with a typed `primary_key_json` the host owns. Five capability flags declined at once, natively. Its host schema lives in the same module so `migrate()`'s verify-only promise stays testable: nothing the adapter does can create those tables.

---

## 3. The borrowed-connection proof

[`docs/tools/borrowed_connection_proof.py`](https://github.com/stephan-dyson/open-ontology/blob/main/docs/tools/borrowed_connection_proof.py) drives the **real registry** over a connection the **host** owns, on both reference backends. `C0-12` passing is the assertion; this is the demonstration.

```
postgres -- host owns the connection AND the schema
    host schema created and committed by the host        oo_proof_bce4bd07
    Capabilities.transaction_scope                       savepoint
    Capabilities.transactional                           True
    why['transaction_scope']                             this adapter was opened over a connection it does not own: t...
    migrate() (verify-only, host owns the schema)        1
    registry.propose_type -> status                      active
    host transaction still open                          INTRANS
    after an exception: 'doomed' present?                False
    after an exception: 'facility' present?              True
    after an exception: host transaction                 INTRANS
    what ANOTHER connection sees before host commit      0
    what it sees after the HOST commits                  1

sqlite -- SAVEPOINT works here too, so 2B's harness is not Postgres-only
    host schema created and committed by the host        proof.sqlite
    Capabilities.transaction_scope                       savepoint
    Capabilities.transactional                           True
    migrate() (verify-only, host owns the schema)        1
    host transaction still open                          True
    after an exception: 'doomed' present?                False
    after an exception: 'facility' present?              True
    after an exception: host transaction open            True
    what ANOTHER connection sees before host commit      0
    what it sees after the HOST commits                  1

Neither adapter issued a COMMIT. Durability at clean exit is the host's -- R5.
```

**One line each, for the relay:**

- **Postgres** — an exception inside `transaction()` leaves the host's transaction `INTRANS` with the host's earlier row intact and the rolled-back one gone; a clean exit is invisible to every other connection until the host commits.
- **SQLite** — identical, on `sqlite3` with the host holding `BEGIN IMMEDIATE`. SQLite has `SAVEPOINT`, so 2B's harness is not Postgres-only.

---

## 4. What changed in `PACKAGE.md`, by section

**This list is the relay to beacon's row 21.2.**

| § | change |
|---|---|
| **§3.2** | `Capabilities` gains **`transaction_scope: Literal["owned","savepoint"]`** (R5/U1) and **`attribute_projections: frozenset[str]`** (U3). Both are *declarations, not flags*: neither is in `CAPABILITY_FLAGS` and neither weakens the two-non-negotiable rule. `C0-01`'s invariant now covers a savepoint scope's `why`. |
| **§3 item 3** | `transaction()` rewritten: a table of what each scope does at depth 0, and **four consequences** — (1) the connection must be inside the host's transaction, checked, `HostTransactionRequired`; (2) nothing is durable until the host commits and **every write result says so**, reads say nothing; (3) the version probe is savepoint-protected; (4) **scopes on one borrowed connection must nest**, checked, `SavepointOutOfOrder`. |
| **§3.4 primitive 4** | a `stores_attributes=False` backend returns *the projected keys*, not `{}`. |
| **§3.5** | G2 holds in both scopes; durability at clean exit is a separate question and belongs to the host. A projection is **not** a fourth guarantee. |
| **§5.7 (new)** | **projected attribute keys** — why `stores_attributes` could not describe a host-owned schema, the five rules, and the one stated collision (a key written as literal `None` is indistinguishable from absent, and why the sentinel fix was rejected: the column belongs to the host). |
| **§6.1** | **three reference legs**, not two, with `sqlite_minimal` named and justified. `--borrowed` and `--schema-harness` in the running instructions. |
| **§6.2** | 124 → **129** ids: `C0-12` (borrowed connection), `C0-13` (its precondition), `C0-14` (its nesting rule), `C11-05` (R8), `C15-09` (U3). Plus a `C15-08` row that had been missing since row 3c. |
| **§6.4 (new)** | **the coverage report** (R12) — *a conformance claim without its coverage line is not a claim* — plus the two harness shapes a third party supplies to have its declarations checked, printed and drift-checked. |
| **§3.3** | `TypeRecord`'s four retirement fields, absent from the printed shape since they landed (U4). Plus **R13**: the facade does not page in v0, and why that is a decision rather than a backlog entry. |
| **§8b.5** | corrected: the hand-written async module holds **three** backend-building tests, not two. |

And in `INTERFACE.md`: `ConsumerReport.warnings` with `gate_unregistered:<gate>` (R8, §5.1); the `warnings` vocabulary **seven → eleven values** — the new durability warning, and three `MergeResult` values that had been produced since row 3c and documented nowhere; `Consumer.warnings` and `Rejection.warnings`; and §5.10's "reserved and always empty" corrected.

---

## 5. The adversarial loop — three rounds, no clean pass

**Six fresh reviewers, two per round, briefed with `USE-CASES.md` and told to drive the real registry rather than read it.** Every round returned **NOT YET**. The loop is closed at the brief's cap of three rounds, not on a clean verdict — the same honest ending as row 3c §7.5, and for a related reason: **each round's fixes created the next round's findings.**

| round | what it found | severity |
|---|---|---|
| **1** | a foreign adapter declaring `transaction_scope="savepoint"` **while committing at depth 0** — the literal U1 regression — ran the suite to `130 passed`, `CONFORMANT`. `C0-12` hard-coded its backend list and skipped every other adapter, including the third reference leg. | BLOCKING |
| **1** | the coverage report **dropped** any id whose test errored in *setup* (pytest reports `when="setup", outcome="failed"`, matching neither branch), so a broken adapter `__init__` vanished and the leg still said `CONFORMANT`. | BLOCKING |
| **1** | R5 and §3 item 3 both promise a durability sentence on results; **`transaction_scope` appeared nowhere in `registry.py`**. | MAJOR |
| **1** | an idle autocommit connection: Postgres raised a raw driver error, **SQLite silently started a transaction and committed it on `RELEASE`** — on the zero-config default backend. | MAJOR |
| **1** | savepoint names were per-adapter, so two adapters on one connection both started at `oo_1`; a projected `None` collides with absent; `C15-08` had no row in §6.2. | MINOR ×3 |
| **2** | **two adapters on one borrowed connection, interleaved**: A's clean exit destroys B's savepoint (both engines release cascadingly), B's exit raises a raw driver error, and on Postgres the whole connection is poisoned so A's own reads fail. | BLOCKING |
| **2** | `HostTransactionRequired` — the precondition the whole scope rests on — was **never exercised anywhere**, because every harness called `host_begin()` first. An adapter omitting the check passed all 127 ids. | BLOCKING |
| **2** | an already-**aborted** host transaction read as "open"; `register_consumer` and `reject` carried no durability warning and vanished on host rollback; `owns_schema=False` had **no third-party verification path at all**. | MAJOR ×3 |
| **3** | round 2's durability warning **leaked onto reads and never expired** — stamped in the two helpers that also build `resolve_type` and `list_types` results, so a savepoint registry marked every read not-durable forever. | BLOCKING |
| **3** | `CONFORMANT, DECLARATIONS UNVERIFIED` was **dead code** for R5's own shape: it read the declaration off the plain factory, which honestly says `"owned"`. A savepoint adapter with the precondition deleted reached a clean `CONFORMANT`. | BLOCKING |
| **3** | `SavepointOutOfOrder` refused correctly and left the adapter **looking closed**, so a caller could orphan the savepoint permanently; the harness shapes were public API described in a private module; **`MergeResult.warnings` had been documented as "always empty" since row 3c while the code populated it on every merge**. | MAJOR ×3 |

### 5.1 The honest convergence note

**The loop did not converge, and saying it did would be the finding.** Three rounds, six reviewers, six `NOT YET` verdicts. Two things about that are worth writing down rather than smoothing over:

1. **Two of the five BLOCKING findings were defects introduced by the previous round's fix.** The durability warning was added in round 2 to close a MAJOR and leaked onto reads in round 3; `DECLARATIONS UNVERIFIED` was added in round 1 and was dead code until round 3 found it. A loop that keeps finding things is not obviously a loop that is failing — but it is also not evidence that a fourth round would be clean, and the brief's cap of three exists so that judgment is made by a person and not by the loop.
2. **Every finding of substance came from *running* something.** Reviewers were told this, and it held for all fourteen: the lying adapters were built and run, the interleaved savepoints were driven on both engines, the read-leak was reproduced against a live Postgres. Not one substantive finding came from reading the diff. That is now two rows' worth of evidence for the same rule.

**What this means for the state of the row:** the seam is in better shape than any single round's verdict suggests — the class of defect the loop kept finding narrowed from *"the mechanism does not exist"* (round 1) to *"the mechanism exists and one of its edges is wrong"* (round 3) — and it is **not** certified clean by a fresh reviewer. The specific residual risk, stated: **an adapter whose declarations nobody can check.** That risk is now *visible* rather than eliminated — the run says `CONFORMANT, DECLARATIONS UNVERIFIED` and names the claim — which is the same move `ConsumerReport.complete=False` makes, and it is the honest position rather than a solved one.

### 5.2 Verified to bite

Every mechanism this row added was checked against an adapter that lies about it, through the third-party path (`python -m open_ontology.contract --adapter … --borrowed …`):

| the lie | caught by |
|---|---|
| declares `savepoint`, commits at depth 0 | `C0-12` **and** `C0-13` |
| declares `savepoint`, omits the precondition check | `C0-13` |
| declares `owns_schema=False`, issues DDL anyway | `C0-09` |
| declares a projection it silently drops | `C0-06` |
| `transaction()` that is not re-entrant | `C0-12` |
| ends a scope out of order on a shared connection | `C0-14` |
| supplies no harness at all | `CONFORMANT, DECLARATIONS UNVERIFIED`, claims named |

**Before this row, every one of them ran the suite to a clean `CONFORMANT`.**

---

## 6. Gates

```
$ python tools/unasync.py --check
22 generated files are current

$ python docs/tools/check_links.py
All relative markdown links resolve.

$ python docs/tools/check_spec_drift.py
docs\specs\INTERFACE.md: every printed shape and signature matches the implementation (15 shapes, 13 calls).
docs\specs\PACKAGE.md: every printed dataclass matches the implementation (13 shapes).

$ python docs/tools/check_capability_matrix.py
Every optional capability can be declined alone and the backend still conforms.
3.2's claim holds, measured rather than asserted.        [10 configurations, 0 failures]
```

**Environment:** Python 3.13.14, Postgres 16.14 (`postgres:16-alpine`, Docker, port 55432), SQLite via stdlib `sqlite3` + `aiosqlite`, `psycopg` 3.

---

## 7. Open items this row does not close

1. **`transaction_scope` and `owns_schema` remain declarations for any adapter that supplies no harness.** The run says so; nothing forces a harness. Making one mandatory would mean refusing conformance to an adapter that is honest and simply has no borrowed mode — see §6.4.
2. **Ruling R12's two-flag rule is unchanged.** The natively-degraded leg declines five flags at once and conforms, which is evidence for §3.2's sentence rather than a proof of it; a backend declining a *different* five has still never been run.
3. **The loop's cap was reached, not its stop rule.** A fourth round would be a reasonable thing for someone to ask for; the brief said three, and three is what ran.
