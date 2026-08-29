# PACKAGE — the `open_ontology` package, its storage-adapter protocol, and the contract suite that defines conformance

**Version:** `v0` — **unstable.** Every module name, class name, primitive signature, table shape and test id here may change without a deprecation path. Standing constraint 4.
**Status:** Draft, 2026-08-28. Satisfies `ROADMAP.md` Phase 2 preparation. Deliverable **#2** of the Tenshen-rebuild ordering. **Deliverable #3 has since landed** — the package, both backends and the 113-test suite are real and green (§8.4, §8b.5, §11); the sections written before it say so where it matters. *(Header corrected by row 3c; it still read "No code yet".)*
**Assumptions:** *written against the 2026-08-28 assumptions; see docs/decisions/* — specifically [`decisions/2026-08-28-assumptions-in-lieu-of-office-answers.md`](../decisions/2026-08-28-assumptions-in-lieu-of-office-answers.md), assumptions **A1**, **A4** and ruling **A5**.
**Sits underneath:** [`INTERFACE.md`](INTERFACE.md) v0. Where this document and `INTERFACE.md` disagree, `INTERFACE.md` wins and the disagreement is recorded in §11 rather than resolved silently.
**Evidence inputs:** [`INTERFACE.md`](INTERFACE.md) (the calls, the refusals, the two design tests) · [`0.5-RESULTS.md`](../findings/0.5-RESULTS.md) and [`0.5-ground-truth-PREREGISTERED.md`](../findings/0.5-ground-truth-PREREGISTERED.md) (the CMS entities and their pre-registered counts) · `beacon/src/beacon/models/work_link_type.py` and `.../services/work_link_service.py`, read-only on 2026-08-28 (the Tenshen design test) · [`0.3-prior-art.md`](../findings/0.3-prior-art.md) (the Foundry import mapping the suite must test).
**Claim tags:** **[Observed]** seen directly · **[Inferred]** a reasonable read · **[Assumed]** believed, untested.

---

## 0. What this is, in four sentences

`INTERFACE.md` says what the registry *does*. This says what you `pip install`, what a storage backend must implement, and how you prove a backend is correct.

The load-bearing idea is one sentence: **the storage adapter is a typed record store that does not know what a proposal, an approval or a refusal is.** Everything in `INTERFACE.md` §5 that refuses, warns, scores or decides lives above the adapter; the adapter stores records, enforces exactly two guarantees, and — the part that makes two unlike backends possible — **declares in advance what it cannot do, so the registry can return an honest unknown instead of guessing.**

The contract suite is not a test of the package. **It is the definition of conformance:** a backend is conformant iff the whole suite passes against it. That suite is the 2B gate per **A5**.

---

## 1. Non-goals — one line each

- **No HTTP/API server.** A server is a *consumer* of `Registry`, never part of it; nothing in this package imports a web framework.
- **No relationships or edges.** `kind="edge"` rows are names, definitions, provenance and lifecycle only. Edge shape and edge instances are deliverable **#4, `docs/EDGES.md`**.
- **No ingestion or mapping.** Landed rows → typed entities is **Phase 3**; this package is handed a decided vocabulary, not a CSV.
- **No instance resolution.** *"I already know 38 of these facilities"* is entity resolution and belongs to **Phase 3 ingestion** (`INTERFACE.md` §10.3; `ROADMAP.md` Phase 3, supervisor's provisional assignment 2026-08-28, founder may move it). Mentioned once, here, and not designed.
- **No ORM is mandated** — see §2.5. The protocol is defined over dataclasses, so a third-party adapter *may* be written with one.
- **No async in v0** — and this is a real gap, not a preference. See §7 contortion **B2**; it blocks ROADMAP #5 and is escalated in §11. **Closed 2026-08-28 by ruling R1's row 3b**, which took option 3 below: `AsyncStorageAdapter` / `AsyncRegistry` alongside the sync ones, generated from them rather than forked ([`3B-ASYNC.md`](../runs/3B-ASYNC.md)).
- **No embeddings, no vector store, no model call.** `resolve_type`'s near-match scoring is a pluggable `Resolver`; v0 ships a deterministic default so the contract suite never depends on a model. See §2.6.
- **No auth, no multi-tenancy** beyond `namespace`; no UI; no CLI beyond a contract-suite runner.

---

## 2. Package shape

### 2.1 Distribution and module layout

Distribution name `open-ontology`; import name `open_ontology`. **[Assumed]** the PyPI name is available; not checked, and not worth checking before #3.

```
open_ontology/
    __init__.py            # the public surface, re-exported. Nothing else is public.
    registry.py            # Registry — the façade. The INTERFACE §5 calls, as methods.
    types.py               # TypeEntry, Provenance, Evidence, Citation, Consumer, Proposal,
                           #   Resolution, ConsumerReport, PredicateEntry, TypeListing,
                           #   UsageReport, Refusal, Rejection, MergeResult, ResolveContext
    errors.py              # UnknownType, AlreadyExists, SchemaMismatch, StoreVersionUnknown
    policy.py              # NamespacePolicy, TierOrder
    adapter.py             # StorageAdapter Protocol + the *Record dataclasses + Capabilities
    attributes.py          # AttributeSchema, FieldSpec, AttributeCensus  (§5)
    _resolve.py            # PRIVATE. default deterministic Resolver, near-match scoring
    _clock.py              # PRIVATE. injectable clock, so the suite is not time-flaky
    backends/
        __init__.py
        sqlite.py          # SQLiteAdapter
        postgres.py        # PostgresAdapter
        _sql.py            # PRIVATE. row <-> Record mapping, JSON encode/decode
        migrations/
            sqlite/0001_init.sql
            postgres/0001_init.sql
    contract/
        __init__.py        # run_contract_suite(adapter_factory) + the pytest plugin
        __main__.py        # python -m open_ontology.contract --adapter pkg.mod:Class
        conftest.py        # the adapter_factory fixture, parametrised over backends
        test_*.py          # the suite (§6)
        fixtures/
            cms_sample_400.csv   # the 400-row public CMS sample (§8.4)
```

### 2.2 The public import surface

```python
from open_ontology import Registry
```

`Registry` is **one façade object** carrying the `INTERFACE.md` §5 calls as methods, with signatures identical to §5 minus the implicit `self`.

**Counting note — raised here, resolved in #1 by row 3c.** `INTERFACE.md` used to say "twelve calls". Enumerating §5.1–§5.11 yields **thirteen** functions: `consumers`, `predicates`, `resolve_type`, `propose_type`, `approve`, `reject`, `list_types`, `usage`, `provenance`, `retire`, `merge_types`, `register_consumer`, `record_use`. §5.5 defines two and §5.11 defines two. The façade exposes thirteen methods. `INTERFACE.md` §5.10, §12 and §13 now all say thirteen. *(Raised by this document at #2, corrected in #1 during row 3c after a fifth adversarial round — a two-line fix that had been carried as a known-wrong number through four deliverables.)*

Public, in the sense of *"you may build against it, knowing v0 will break it"*:

| Exported | Why public |
|---|---|
| `Registry` | the only entry point |
| every data shape in `types.py` | callers construct `Evidence`, `Consumer`, `ResolveContext` and read every report shape |
| every exception in `errors.py` | `UnknownType` is a specified behaviour (§5.1), so it is API |
| `StorageAdapter`, `Capabilities`, and the `*Record` dataclasses | a third-party backend must implement them — this is the point of #2 |
| `NamespacePolicy`, `TierOrder` | `min_auto_approve_tier` is deployment-supplied per §2.7 |
| `AttributeSchema`, `FieldSpec` | §5 |
| `backends.sqlite.SQLiteAdapter`, `backends.postgres.PostgresAdapter` | the two reference backends |
| `contract.run_contract_suite` | conformance must be runnable by people who did not write this package |

Private, meaning it may change between two commits with no note and **the contract suite may not import it**: `_resolve`, `backends._sql`, every module-level name beginning `_`, and the SQL files (they are an implementation of the adapter, not a schema anyone may depend on).

**One carve-out, and §2.1 always implied it:** the suite **may** import `_clock`. §2.1's own layout comment says `_clock.py` exists *"so the suite is not time-flaky"* — that is the suite's use, and `conftest.py` has imported `FixedClock` since #3. The blanket sentence above contradicted §2.1 from the first draft and the code sided with §2.1. *(Corrected by row 3c after an adversarial review round.)* `_resolve` stays forbidden and that one matters: a suite that reached into the resolver could pin resolver behaviour, which §2.6 forbids.

**Why a façade object and not module-level functions**, given §5 writes them as free functions: every call needs an adapter, a namespace policy, a clock and a resolver. Module-level functions would need a process-global registry — and the contract suite must hold a SQLite adapter and a Postgres adapter **in one process at once** to parametrise over both. A global makes that impossible. **[Inferred]** — the constraint is the suite's, and it is decisive.

### 2.3 Python version floor: **3.11**

**[Observed]**, python.org developer guide, retrieved 2026-08-28: 3.10 reaches end of life **2026-10** — six weeks from this document — and 3.11 is in security-fix status until **2027-10**. Setting the floor at 3.10 buys a version that is dead before #3 ships.

3.11 also gives, without conditional imports: PEP 604 `str | None` (3.10), `datetime.UTC` (3.11), `typing.Self` (3.11), `tomllib` (3.11), exception groups (3.11). `typing.Protocol` is 3.8, so the adapter protocol costs nothing.

`requires-python = ">=3.11"`. The reference deployment target is 3.12 or 3.13; the floor is what the suite is *run* at in CI, because a floor nobody tests is not a floor.

### 2.4 Dependency policy

**Runtime, base install: zero dependencies.** stdlib only — `sqlite3`, `json`, `datetime`, `dataclasses`, `uuid`, `re`, `difflib`, `contextlib`, `typing`.

| Extra | Adds | Why exactly one |
|---|---|---|
| `open-ontology` (base) | — | SQLite is stdlib; the default backend must not cost a wheel |
| `open-ontology[postgres]` | `psycopg>=3.1,<4` | one driver per backend, no pool, no C extra by default |
| `open-ontology[contract]` | `pytest>=8` | the suite ships *inside* the package because it is the definition of conformance (§6) — a third-party backend must be able to run it |

**[Observed]**, PyPI metadata for `psycopg`, retrieved 2026-08-28: latest `3.3.4`, `requires_python >=3.10`, extras `c` / `binary` / `pool` / `test` / `dev` / `docs`. We depend on the plain wheel; deployments that want `psycopg[binary]` or `psycopg[c]` install it themselves. `psycopg2` is **not** supported — it is a different driver with a different parameter style, and supporting both doubles the SQL layer for no gain.

**No ORM is mandated. Stated and justified:**

1. **Size.** The adapter is fifteen primitives over seven tables (§4.1). An ORM's identity map, unit of work, lazy loading and relationship graph are all machinery for a problem this does not have.
2. **It would defeat the adapter.** The two backends differ in exactly the places an ORM abstracts badly — JSON storage (`TEXT` vs `jsonb`), timestamps (`TEXT` vs `timestamptz`), and the `already_decided` race (write lock vs `SELECT … FOR UPDATE`). Those differences are the adapter's *content*. Hiding them behind an ORM moves them somewhere nobody reads.
3. **It would make 2B worse.** beacon already maps `work_link_types` with SQLAlchemy. Mandating SQLAlchemy here means beacon's migration has to reconcile two `MetaData` objects over one table; raw SQL against the table beacon already owns is strictly less entangled. See §7.
4. **Constraint 2** (`ROADMAP.md`): do not build the general thing before the specific thing works. An ORM is generality bought before need.

**The protocol does not forbid one.** `StorageAdapter` is defined over dataclasses and Python values, never over rows or cursors. A third-party adapter — beacon's — is free to be an eighty-line SQLAlchemy shim. **That freedom is the point of having a protocol at all**, and §7 is where it gets tested.

### 2.5 What is *not* in the package, deliberately

- No logging configuration; the package logs to `logging.getLogger("open_ontology")` and configures nothing.
- No retry, no backoff, no connection pool. The adapter is handed a connection or a factory; connection lifecycle belongs to the deployment.
- No `Registry.close()` that closes the caller's connection. The adapter owns only what it opened.

### 2.6 The `Resolver` seam — and why the suite must never call a model

`resolve_type` (§5.3) needs near-match scoring, and `propose_type` (§5.4) needs `near_matches`. Both are model-shaped in production and **must not be model-shaped in the contract suite**, or conformance becomes non-deterministic and a backend can fail for reasons that have nothing to do with storage.

```python
class Resolver(Protocol):
    def score(self, candidate: str, context: ResolveContext,
              known: Sequence[TypeEntry], *, tier: str) -> list[tuple[str, float]]: ...
    def classify(self, candidate: str, context: ResolveContext,
                 *, tier: str) -> NotAType | None: ...
```

v0 ships `_resolve.DeterministicResolver`: `difflib.SequenceMatcher` over `name` and `definition`, plus a rule-based `classify` that detects the two `not_a_type` cases the CMS data forced (§8.3). It **records** `tier` into provenance and **does not use it** — the tier gate lives in `approve`, per `INTERFACE.md` §2.7 point 3, not in scoring.

**The consequence, stated plainly:** the deterministic resolver is not good enough for production and is not meant to be. It exists so the suite has a fixed point. `Registry(adapter, resolver=MyModelResolver())` is the production path, and **no contract test may pass or fail because of resolver quality** — the suite asserts *outcomes and shapes* (`confidence is None`, `outcome == "none"`, `alternatives` populated), never scores.

> **Three tests broke that rule, and row 3c enforces it rather than restating it.** `C3-08`/`C3-09` assert a `not_a_type` **outcome** that only the shipped `DeterministicResolver`'s lookup table produces, and `C4-06`'s keyword rule is not behind this seam at all (§8b.3, B8). They now carry a `resolver_dependent` marker: **binding for the two reference backends**, where they pin real behaviour of the resolver this package ships, and **skipped, with a reason naming this section, for a foreign adapter**, where they assert nothing about the backend under test. Ruling **Q4**'s recommendation, applied — see [`../findings/3C-VALIDATION.md`](../findings/3C-VALIDATION.md) §6, which the supervisor may reverse.

---

## 3. The storage-adapter protocol

### 3.1 The rule the protocol is built on

> **The adapter stores records. It does not know what a proposal, an approval or a refusal is.**

Mechanically, and testable (`C0-04` in §6):

- The identifiers `Refusal`, `Rejection`, `Resolution`, `ConsumerReport`, `UsageReport`, `TypeEntry`, `Proposal` **do not appear** in `adapter.py` or in any module under `backends/`.
- The adapter speaks flat, JSON-serialisable `*Record` dataclasses (§3.3) — projections of the interface shapes with no computed fields.
- `ProposalRecord` has a `status: str` column. The adapter **stores** that string and **never decides** which transitions are legal. `ProposalRecord.warnings: list[str]` is stored and **never derived**.
- No adapter method returns a refusal, raises on a policy violation, or reads a definition.

### 3.2 `Capabilities` — the primitive that makes Rule U implementable

`INTERFACE.md` Rule U: *uncertainty is a value, never a default. Unknown is `None` plus a `why: str`.* Across two unlike backends that is unimplementable unless the backend says, in advance, what it cannot answer — otherwise the registry must either guess or probe.

```python
@dataclass(frozen=True)
class Capabilities:
    enforces_unique_name: bool     # G1 — REQUIRED True to be conformant
    transactional:        bool     # G2 — REQUIRED True to be conformant
    stores_proposals:     bool     # proposals survive a restart
    stores_events:        bool     # append_event is durable
    stores_attributes:    bool     # an arbitrary dict survives a round trip
    stores_aliases:       bool     # TypeEntry.aliases survives a round trip
    indexes_membership:   bool     # find_types(predicate=…) is answerable
    counts_usage:         bool     # get_usage returns a count
    timestamps_usage:     bool     # get_usage returns first_seen / last_seen
    owns_schema:          bool     # False when the schema belongs to the host app (§9.3)
    why: dict[str, str]            # one sentence per False flag — surfaced verbatim as Rule U's `why`
```

**The `why` dict is the mechanism, not decoration.** When a flag is `False`, the registry does not invent an explanation; it surfaces the adapter's sentence. `usage("blocks")` on beacon's table returns `last_seen=None, orphaned=None, why="work_link_types has no last_used_at column"` — which is `INTERFACE.md` §9 contortion 2, reported by the system rather than discovered by a human.

**Two flags are not optional.** `enforces_unique_name=False` or `transactional=False` ⇒ **non-conformant**, full stop (§3.5). Every other flag may be `False` and the backend can still be conformant, because the suite asserts *honest unknowns*, not values. That single rule is what lets Tenshen's one-table registry be a third backend (§7).

**Invariant, tested (`C0-01`):** every `False` flag has a non-empty entry in `why`.

### 3.3 The record shapes

Flat, frozen dataclasses. Every field is `str`, `int`, `bool`, `datetime`, `None`, or a JSON-serialisable `dict`/`list`. No nesting of interface objects.

```python
@dataclass(frozen=True)
class TypeRecord:
    namespace: str
    kind: str
    name: str                       # identity is (namespace, kind, name). No surrogate. §4.2
    definition: str
    created_by: str                 # "seed" | "ai" | "user"
    status: str                     # "proposed" | "active" | "retired"
    predicates: tuple[str, ...]     # membership lives HERE, on the member. INTERFACE §2.3
    aliases: tuple[str, ...]
    attributes: dict                # opaque to the adapter. §5
    attr_schema_version: int | None # the schema in force when this was written. §5.4
    provenance: dict                # the whole Provenance, JSON-encoded. Opaque to the adapter.
    warnings: tuple[str, ...]
    created_at: datetime
    updated_at: datetime

@dataclass(frozen=True)
class ProposalRecord:
    proposal_id: str                # opaque, generated ABOVE the adapter. §4.2
    namespace: str; kind: str; name: str
    definition: str
    predicates: tuple[str, ...]
    attributes: dict
    evidence: list                  # JSON-encoded list[Evidence]. Opaque to the adapter.
    proposed_by: str
    proposed_at: datetime
    tier: str | None
    status: str                     # "pending"|"approved"|"rejected"|"superseded" — STORED, not judged
    warnings: tuple[str, ...]
    near_matches: list              # [[name, score], …]
    decided_by: str | None
    decided_at: datetime | None
    decision_reason: str | None
    superseded_by: str | None

@dataclass(frozen=True)
class ConsumerRecord:
    namespace: str
    consumer_id: str                # "aura_render.referent_link"
    gate: str                       # a predicate NAME. May name a predicate that does not exist. §3.4.11
    on_unknown: str                 # "drop" | "error" | "passthrough"
    owner: str | None
    registered_at: datetime
    locator: str | None

@dataclass(frozen=True)
class UsageRecord:
    namespace: str; kind: str; name: str
    count: int | None
    first_seen: datetime | None
    last_seen: datetime | None

@dataclass(frozen=True)
class EventRecord:
    event_id: str                   # generated above the adapter
    namespace: str
    kind: str | None; name: str | None      # the type this concerns, if any
    proposal_id: str | None
    at: datetime
    actor: str
    event: str                      # "proposed"|"approved"|"rejected"|"retired"|"merged"|
                                    #   "amended"|"override"|"imported"|"used"
    detail: dict
```

Queries are objects, not kwargs, so the protocol has fifteen methods rather than fifteen plus a signature that grows every time `list_types` gains a filter:

```python
@dataclass(frozen=True)
class TypeQuery:
    namespace: str | None = None         # None = all namespaces
    kind: str | None = None
    status: str | None = None
    name_in: tuple[str, ...] | None = None
    predicate: str | None = None         # the extent query. INTERFACE §5.6
    created_by: str | None = None
    include_retired: bool = False
    limit: int | None = None
    after: str | None = None             # opaque cursor; ordering is (namespace, kind, name)

@dataclass(frozen=True)
class TypePage:
    records: tuple[TypeRecord, ...]
    known: int | None                    # None = the backend cannot count. NOT 0. Rule U
    complete: bool
    why_incomplete: str | None
    next_after: str | None

@dataclass(frozen=True)
class ProposalQuery:
    namespace: str | None = None
    name: str | None = None
    status: str | None = None
    limit: int | None = None
    after: str | None = None
```

Two filters from `INTERFACE.md` §5.6 are deliberately **absent** from `TypeQuery`: `unverified_semantics` and `orphaned`. Both are *derived* — one from `provenance.evidence` and the approval warnings, the other from `status` + `usage` + the policy's orphan window. Pushing them into the adapter would put registry policy inside the backend, which is exactly what §3.1 forbids. The registry computes them from `find_types` + `get_usage` and reports `complete: false` when it had to page to do it. **Cost, stated: `list_types(orphaned=True)` is O(types), not O(matches), on every backend.** Acceptable at the scale this registry is for (hundreds to low thousands of types); recorded so nobody is surprised.

### 3.4 The fifteen primitives

Each has a signature, a data shape, and its uncertainty behaviour. **The uniform uncertainty rule: a primitive that cannot answer returns `None` (or a page with `known=None, complete=False`) plus a `why` drawn from `Capabilities.why` — never `0`, never `[]`, never `False`.**

---

**1. `capabilities() -> Capabilities`**
Pure, cheap, callable before `migrate()`. **Uncertainty:** none — a backend that does not know its own capabilities is broken, not uncertain.

**2. `migrate() -> int`**
Brings the store to the version this package expects; returns the version now in force. Idempotent. **When `Capabilities.owns_schema is False`, `migrate()` is verify-only:** it checks the columns it needs exist and either returns the version or raises `SchemaMismatch` listing what is missing. It never issues DDL against a schema it does not own. **Uncertainty:** a store whose version is *higher* than the package knows raises `StoreVersionUnknown` — never a silent downgrade (§9).

**3. `transaction() -> ContextManager[None]`**
Groups writes. Commits on clean exit, rolls back on any exception. Re-entrant calls join the outermost transaction (savepoints are not required). **Uncertainty:** none — `transactional=False` is non-conformant, so this always means what it says.

**4. `put_type(rec: TypeRecord, *, expect_absent: bool = False) -> TypeRecord`**
Upsert on `(namespace, kind, name)`. With `expect_absent=True`, raises `AlreadyExists` if the key is present — **and that must come from a real constraint, not from a read-then-write check** (guarantee **G1**, §3.5). Returns the record as stored, so a backend that could not store `attributes` or `aliases` returns them empty and the registry can tell.
**Uncertainty:** if `stores_attributes` is `False`, the returned record has `attributes={}` — the caller must not assume the write round-tripped; the suite tests exactly this (`C0-06`).

**5. `get_type(namespace: str, name: str, *, kind: str | None = None) -> TypeRecord | None`**
`None` means *absent*, which here is a fact, not an unknown — the adapter always knows whether a key exists. With `kind=None`, returns the single match or raises `AmbiguousKind` when the same name exists under two kinds (legal: uniqueness is per `(namespace, kind)`).

**6. `find_types(q: TypeQuery) -> TypePage`**
**Uncertainty, the important one:** when `q.predicate` is set and `indexes_membership` is `False`, return `TypePage(records=(), known=None, complete=False, why_incomplete=<Capabilities.why["indexes_membership"]>)`. **Never `known=0`** — that reads as *"nothing is commentable"*, which is `INTERFACE.md` §5.2's named failure. Same rule for any filter the backend cannot apply: return `complete=False` with a `why`, never a filtered-looking empty page.

**7. `put_proposal(rec: ProposalRecord, *, expect_absent: bool = False) -> ProposalRecord`**
Upsert on `proposal_id`. The adapter writes `status`, `decided_by`, `decided_at` **as given** and validates no transition.
**Uncertainty:** if `stores_proposals` is `False`, raises `NotSupported`. It does not pretend to store and lose. The registry checks the capability first and never calls this (§7 contortion B4).

**8. `get_proposal(proposal_id: str) -> ProposalRecord | None`**
`None` = absent. **Must be callable inside `transaction()` with a write intent** so `approve` can read-then-decide atomically: on Postgres that is `SELECT … FOR UPDATE`; on SQLite the `BEGIN IMMEDIATE` write lock already serialises it. This is how `already_decided` (§5.5) stops being a race. `NotSupported` when `stores_proposals` is `False`.

**9. `find_proposals(q: ProposalQuery) -> ProposalPage`**
Used by `resolve_type` to surface a prior rejection in `alternatives` (§5.5) and by `propose_type` to find a pending proposal for the same name. **Uncertainty:** same page rule as `find_types`. `NotSupported` when `stores_proposals` is `False` — and the registry then omits prior rejections from `alternatives` **and says so** in `Resolution.reason`, rather than presenting a short list as complete.

**10. `put_consumer(rec: ConsumerRecord) -> ConsumerRecord`**
Upsert on `(namespace, consumer_id)`. The `gate` may name a predicate that does not exist yet; the adapter does not check. **[Inferred]** this is correct: a consumer that gates on a word nobody registered is precisely mechanism **C**, and refusing the registration would hide it.
**Uncertainty:** none. A consumer source that is read-only (a config file — see §7) raises `NotSupported` and the registry surfaces that as `Refusal(reason="consumer_source_read_only")` from `register_consumer`, not as a silent no-op. *(Amended by ruling **R4**, row 3c 2026-08-28: the reason is the fifteenth value of `INTERFACE.md` §5.12, added in the same change per R3. Before R4 the registry raised, because no honest reason existed — deviation D-1, now resolved.)*

**11. `find_consumers(namespace: str, *, gate: str | None = None, consumer_id: str | None = None) -> list[ConsumerRecord]`**
The one call behind `consumers()` and `PredicateEntry.consumers`.
**Uncertainty — and this is the sharpest point in the protocol:** the returned list is **always** treated as incomplete by the registry. `ConsumerReport.complete` is `False` unconditionally in v0 (`INTERFACE.md` §5.1) *whatever this returns*, because consumers are registered, not discovered. The adapter is not asked to say whether it is complete; it cannot know, and asking would invite a `True`.

**12. `bump_usage(namespace: str, kind: str, name: str, *, at: datetime | None, by: str | None) -> None`**
Increments the count and advances `last_seen` to `max(last_seen, at)`; sets `first_seen` if unset. **Explicitly allowed to be a no-op** (`INTERFACE.md` §5.11) — a backend with `counts_usage=False` does nothing and says so via `get_usage`.
**Uncertainty / concurrency:** last-writer-wins on `last_seen` is acceptable. **No storage guarantee is required here** (§3.5, G3) — stated so nobody implements a lock they do not need. `usage` is advisory and Rule U covers the rest.

**13. `get_usage(namespace: str, kind: str, name: str) -> UsageRecord | None`**
`None` = the type has never been recorded at all. A record with `count=None` = *this backend does not count*. **These are different facts and must not be collapsed** — the first says nothing has happened, the second says we did not look. `INTERFACE.md` §5.7 turns the second into `count: None`, `orphaned: None`.
**Uncertainty:** `timestamps_usage=False` ⇒ `first_seen`/`last_seen` are `None` and the registry sets `orphaned=None` with the adapter's `why`. **Never `orphaned=False`.**

**14. `append_event(rec: EventRecord) -> None`**
Append-only. **The adapter must have no update or delete path for events** — `INTERFACE.md` §5.8: *a correction is a new event, never an edit*. `NotSupported` when `stores_events=False`.

**15. `read_events(namespace: str, *, kind: str | None = None, name: str | None = None, proposal_id: str | None = None) -> list[EventRecord]`**
Ordered by `at`, then by insertion. **Uncertainty:** `stores_events=False` ⇒ the registry returns `Provenance.history == []` **with a `why`**, and — see §3.6 — refuses any destructive override that it cannot record.

### 3.5 The two storage guarantees, and the one that is not required

Exactly two things cannot be enforced above the adapter.

**G1 — uniqueness of `(namespace, kind, name)` in the type store.**
Required by §5.4 (*name already taken → return the existing entry*) and §5.9 (*a retired name is not reusable*). A read-then-write check is not sufficient: two concurrent approvals of `facility` both read absent and both insert, and the registry's central promise — one word, one entry — is gone. `put_type(expect_absent=True)` must raise from a **database constraint**. Note the constraint is per `(namespace, kind)`: `facility` as an `entity` and `facility` as a `value_set` may coexist (`INTERFACE.md` §2.1).

> **Both guarantees are raced, not merely asserted** *(added by roadmap row 3c, 2026-08-28, after an adversarial review round)*. Until then the only tests of G1 and G2 called the primitives **sequentially on one thread**, which a read-then-write check passes exactly as happily as a real constraint does — so a backend whose "uniqueness" was a Python-level check could have been blessed conformant and then corrupted itself the moment two ingestion workers hit one store, which is the deployment shape UC3 is the fixture for. `C0-08` now races two adapters on one store, on both reference backends and in both stacks. **Verified to bite:** a wrapper that implements `expect_absent` as check-then-insert produces **two winners** under the race and fails `C0-08`, while the constraint-backed backends produce one winner and one `AlreadyExists`.

**G2 — atomicity of the decision transactions.**
`approve` writes four things: the proposal's decision, the new `TypeEntry`, its membership rows, and a `ProvenanceEvent`. A half-commit produces either an approved proposal with no type (an approval nobody can see) or an active type with no approval record — and the second violates `INTERFACE.md` §2.4's rule that `approved_by` is never null on an `active` type, which is the rubber-stamping failure arriving through the data model. `reject`, `retire` and `merge_types` have the same shape.

**G3 — monotonic `last_seen` under concurrent `record_use`: NOT required.**
Named here so it is a decision rather than an omission. `usage` is advisory; a lost update costs one count and at most a slightly-stale `last_seen`, and the orphan judgement already degrades to `None` under uncertainty. Requiring serialisation here would make `record_use` — the highest-frequency call in the surface — take a write lock for no safety gain.

### 3.6 Which refusals are enforced where

**Zero of `INTERFACE.md` §5's refusals are enforced by a backend.** Two are only *enforceable* because of a storage guarantee.

| `INTERFACE.md` refusal / behaviour | Enforced | Needs a storage guarantee? |
|---|---|---|
| §5.1 `UnknownType` rather than an empty report | registry | no (`get_type` → `None`) |
| §5.1 `complete` always `False` | registry, unconditionally | no — and the adapter is never *asked* |
| §5.2 `extent_size: None` when membership unindexed | registry, from `Capabilities` | no |
| §5.3 below `min_confidence` → `none` + alternatives | registry + resolver | no |
| §5.3 `not_a_type` (`redundant_projection`, `export_artefact`, …) | resolver | no |
| §5.3 `confidence: None` ≠ `0.0` | registry | no |
| §5.4 empty `definition` → `ValueError` | registry | no |
| §5.4 `ai:` proposer without `tier` → `ValueError` | registry | no |
| §5.4 name taken → return the existing entry | registry | **yes — G1** |
| §5.4 `near_duplicate` warns, never refuses | registry | no |
| §5.4 `no_evidence`, `unverified_semantics` warnings | registry | no |
| §5.4 retired name → `name_previously_retired` | registry | **yes — G1** (the retired row must still be there) |
| §5.5 `tier_below_auto_approve_policy` | registry + `NamespacePolicy` | no |
| §5.5 `already_decided` (idempotent) | registry, **read inside the transaction** | **yes — G2** |
| §5.5 `unknown_proposal` | registry | no |
| §5.5 `reject` requires a non-empty reason | registry | no |
| §5.5 approval with `unverified_semantics` succeeds, keeps the warning | registry | no |
| §5.9 `live_consumers` | registry, from `find_consumers` + membership | no |
| §5.9 `retired_without_usage_evidence` warning | registry | no |
| §5.10 all six merge refusals + `no_consumer_evidence` | registry, entirely | no |

**Three new refusal reasons this document introduces**, all of them consequences of a backend that cannot do something rather than of a policy — flagged in §11 for #1 to adopt or reject *(all three adopted by ruling R3; a fourth of the same shape followed under R4 — see below)*:

- **`proposals_not_stored`** — `approve`/`reject` on a backend with `stores_proposals=False` (§7, B4). Reusing `unknown_proposal` here would be a confident wrong answer, which Rule U forbids. **Tested by `C5-12`** *(added by row 3c; it had no test at all, and §6.3's coverage line said otherwise — see §8b.5)*.
- **`cannot_record_override`** — see below.
- **`attributes_schema_violation`** — §5, `enforce` mode only.

> **A fourth capability refusal, added by ruling R4 (row 3c, 2026-08-28): `consumer_source_read_only`.** `register_consumer` against a read-only consumer source (§7.3) returns it, and `register_consumer`'s return type is therefore `Consumer | Refusal`. It belongs in this list by shape — a backend that cannot do something, not a policy decision — and it is enumerated in `INTERFACE.md` §5.12, which is now fifteen values. `C11-04` asserts it in both suites.

**The rule behind `cannot_record_override`, which is a design consequence rather than a mechanism:**

> **A destructive override that cannot be recorded is refused.**

`retire(force=True)` "records the override in `history`" (§5.9); `merge_types(acknowledge=[…])` records the acknowledgement (§5.10). On a backend with `stores_events=False` the record cannot be written. The options are to do the destructive thing unrecorded, or to refuse. **Refuse.** An unrecorded override is exactly the class of silent, unattributable change this registry exists to prevent, and a backend that cannot keep an audit trail has not earned the right to be overridden. A backend with `stores_events=False` is still conformant — the suite tests the *refusal*, not the capability (`C9-02`, `C10-08`).

---

## 4. The two backends

### 4.1 Table shapes

Seven tables. Note that seven tables serve five logical collections (types, proposals, consumers, usage, events) — `oo_schema_version` is store metadata (§9) and `oo_type_predicate` is the normalised form of `TypeRecord.predicates`, not a collection of its own.

**On `oo_type_predicate` and `INTERFACE.md` §2.3.** §2.3 requires that membership lives on the member and that a predicate's extent is *derived, never stored twice*. The join table satisfies this: it **is** the storage of `TypeRecord.predicates`, written only when a member's record is written, and **nothing is ever written to the predicate's own row**. The extent is a query against it, in the other direction.

And the structural result §2.3 calls the most load-bearing idea in `INTERFACE.md` shows up here as a fact about the schema: **`consumers()` and `predicates()` are answered by the same join.** `oo_consumer.gate` holds a predicate name; `consumers(type)` is *"for each consumer, is `type` in the extent of `consumer.gate`?"*, which is one lookup in `oo_type_predicate` plus a scan of `oo_consumer`. There is no consumer-membership table, and there must not be — **if an implementation grows one, it has stored the extent twice and §2.3 has been missed.** Testable: `C2-01`.

```
oo_schema_version
    version         INTEGER      PRIMARY KEY          -- one row
    applied_at      <ts>         NOT NULL
    note            TEXT

oo_type
    namespace       TEXT         NOT NULL
    kind            TEXT         NOT NULL
    name            TEXT         NOT NULL
    definition      TEXT         NOT NULL             -- CHECK length(definition) > 0
    created_by      TEXT         NOT NULL             -- seed | ai | user
    status          TEXT         NOT NULL             -- proposed | active | retired
    aliases_json    TEXT/jsonb   NOT NULL DEFAULT '[]'
    attributes_json TEXT/jsonb   NOT NULL DEFAULT '{}'
    attr_schema_version INTEGER                       -- NULL = written with validation off (§5)
    provenance_json TEXT/jsonb   NOT NULL             -- the whole Provenance
    warnings_json   TEXT/jsonb   NOT NULL DEFAULT '[]'
    retire_reason   TEXT
    retired_by      TEXT
    retired_at      <ts>
    successor       TEXT
    created_at      <ts>         NOT NULL
    updated_at      <ts>         NOT NULL
    PRIMARY KEY (namespace, kind, name)               -- guarantee G1
    INDEX (namespace, status), INDEX (namespace, kind), INDEX (created_by)

oo_type_predicate                                     -- the normalised form of TypeRecord.predicates
    namespace       TEXT         NOT NULL
    member_kind     TEXT         NOT NULL
    member_name     TEXT         NOT NULL
    predicate_name  TEXT         NOT NULL
    PRIMARY KEY (namespace, member_kind, member_name, predicate_name)
    INDEX (namespace, predicate_name)                 -- the extent query
    FOREIGN KEY (namespace, member_kind, member_name) -> oo_type ON DELETE CASCADE
    -- deliberately NO foreign key on predicate_name: a member may claim a predicate
    -- that is only proposed. Refusing that would be propose_type refusing a near-duplicate.

oo_proposal
    proposal_id     TEXT         PRIMARY KEY          -- uuid4 hex, generated above the adapter
    namespace, kind, name, definition                 -- as oo_type
    predicates_json, attributes_json, evidence_json, near_matches_json, warnings_json
    proposed_by     TEXT         NOT NULL
    proposed_at     <ts>         NOT NULL
    tier            TEXT
    status          TEXT         NOT NULL             -- pending | approved | rejected | superseded
    decided_by      TEXT
    decided_at      <ts>
    decision_reason TEXT
    superseded_by   TEXT
    INDEX (namespace, name, status)                   -- prior-rejection lookup, §5.5
    -- NO unique constraint on (namespace, kind, name): several proposals for one word
    -- over time is normal, and one of them being a retained rejection is the point.

oo_consumer
    namespace       TEXT         NOT NULL
    consumer_id     TEXT         NOT NULL
    gate            TEXT         NOT NULL             -- a predicate name; may not exist
    on_unknown      TEXT         NOT NULL             -- drop | error | passthrough
    owner           TEXT
    registered_at   <ts>         NOT NULL
    locator         TEXT
    PRIMARY KEY (namespace, consumer_id)
    INDEX (namespace, gate)

oo_usage
    namespace, kind, name        NOT NULL
    count           INTEGER                           -- NULL = this backend does not count
    first_seen      <ts>
    last_seen       <ts>
    PRIMARY KEY (namespace, kind, name)

oo_event                                              -- append-only. No UPDATE, no DELETE.
    event_id        TEXT         PRIMARY KEY
    namespace       TEXT         NOT NULL
    kind            TEXT
    name            TEXT
    proposal_id     TEXT
    at              <ts>         NOT NULL
    actor           TEXT         NOT NULL
    event           TEXT         NOT NULL
    detail_json     TEXT/jsonb   NOT NULL DEFAULT '{}'
    INDEX (namespace, kind, name, at), INDEX (proposal_id)
```

### 4.2 The surrogate-key decision

`INTERFACE.md` §9 row 1 defers this: *"`id: int` primary key — not represented; `name` is the identity in v0. Surrogate keys are storage (#2)."* Decided here.

> **The storage key is the natural key `(namespace, kind, name)`. No surrogate integer id is exposed by the adapter protocol or by any interface call. A backend may carry one internally; it must never surface.**

Three reasons:

1. **The interface's identity already is the name.** Every call in §5 takes `type: str`. Exposing a surrogate creates a second identity, and the first thing that happens with a second identity is that something joins on it and the name becomes mutable — which §5.9 forbids outright (*a retired name is not reusable*). One identity, enforced by the schema.
2. **It keeps an id-allocation primitive out of the protocol.** With a natural key there is no `next_id()`, no sequence, no "which backend allocates". Fifteen primitives instead of sixteen.
3. **It is what lets beacon's table join the party.** `work_link_types.id` stays exactly where it is; the adapter maps `("default", "edge", name)` onto the row and the surrogate lives below the boundary, invisible. See §7.

**The cost, stated: a rename is impossible.** Renaming a type in v0 is: propose the new name, add the old name to `aliases`, retire the old entry with `successor=<new>`. That is three operations where a surrogate key would allow one `UPDATE`. **It is not an accident.** A rename under a surrogate key silently changes what every consumer's allowlist means, with no event, no approval and no way to ask *"what will drop this?"* — the whole of mechanism **C**, delivered by a convenience.

**Proposal ids are the one exception, and they are opaque strings, generated above the adapter** (`uuid4().hex`). Reason: `approve(proposal_id)` needs a handle, and a proposal has no natural key — several proposals for one word over time is normal (§4.1). Generating them above the adapter means two backends can never disagree about an id and the protocol needs no allocation primitive. Same for `event_id`.

### 4.3 SQLite — zero-config, the default for tests and single-user

`sqlite3` from the stdlib. No dependency. `SQLiteAdapter(path)` or `SQLiteAdapter(":memory:")`.

Connection setup, and why each line is there:

| Setting | Value | Why |
|---|---|---|
| `isolation_level` | `None` | Python's `sqlite3` opens implicit **DEFERRED** transactions by default (`isolation_level=""`). **[Observed]**, docs.python.org/3/library/sqlite3. We manage transactions ourselves. |
| transaction start | explicit `BEGIN IMMEDIATE` | **[Observed]**, sqlite.org/lang_transaction: a deferred transaction that starts with a read *"will upgrade the transaction to a write transaction if possible, or return `SQLITE_BUSY`."* Every registry transaction reads then writes (`approve` reads the proposal, then writes four rows), so DEFERRED turns a routine approval into a spurious `SQLITE_BUSY` the moment there is a second writer. `BEGIN IMMEDIATE` takes the write lock up front. This is **G2**, and it is also how `already_decided` stops being a race. |
| `Connection.autocommit` | **not used** | **[Observed]**, docs.python.org: added in **Python 3.12**. The floor is 3.11 (§2.3), so the portable path is `isolation_level=None` + explicit `BEGIN IMMEDIATE`, which behaves identically on 3.11 through 3.14. |
| `journal_mode` | `WAL` | readers do not block the writer |
| `foreign_keys` | `ON` | off by default in SQLite; the `oo_type_predicate` cascade depends on it |
| `busy_timeout` | 5000 ms | a queued writer waits rather than failing |

- **JSON columns are `TEXT`**, encoded and decoded with `json` in Python. SQLite's JSON functions are built in by default only **as of 3.38.0 (2022-02-22)** and JSONB only as of **3.45.0 (2024-01-15)** — **[Observed]**, sqlite.org/json1.html — and the SQLite version bundled with CPython varies by platform build. The package therefore **never uses a SQLite JSON function**. Consequence, stated: `attributes` cannot be queried in SQL on this backend, which is fine — no interface call queries inside `attributes` (§5 keeps the census in its own table).
- **Timestamps are `TEXT`**, ISO-8601, UTC, `Z`-suffixed, microsecond precision. SQLite has no date type; this format sorts correctly as text, which is what the `oo_event` ordering and the orphan-window comparison need.
- **Name validation:** SQLite has no regex in core. The column carries `CHECK (length(name) BETWEEN 1 AND 64 AND name GLOB '[a-z]*')` — a first-character and length guard only. **The full `^[a-z][a-z0-9_]{0,63}$` rule is enforced above the adapter, on both backends**, so the two behave identically; the CHECK is belt-and-braces against a direct `INSERT`.
- **Concurrency posture:** one writer. This is the default for the contract suite and for single-user use, and it is not the reference deployment.

### 4.4 Postgres — the reference deployment

`psycopg` v3 (§2.4). `PostgresAdapter(conninfo)` or `PostgresAdapter(connection_factory=…)`.

| Concern | Postgres |
|---|---|
| JSON columns | `jsonb`, with a GIN index on `oo_type.attributes_json` — the census (§5.5) reads it, and a deployment may want to grep the escape hatch |
| Timestamps | `timestamptz`, stored UTC |
| Name validation | `CHECK (name ~ '^[a-z][a-z0-9_]{0,63}$')` — the full rule, natively, in addition to the check above the adapter |
| G1 | the same composite `PRIMARY KEY` |
| G2 | `BEGIN` at `READ COMMITTED`; `approve` reads the proposal with `SELECT … FOR UPDATE`, which is what turns `already_decided` into an idempotent refusal rather than a double-approve |
| Extent query | the same join, plus `INDEX (namespace, predicate_name)` |
| Events | `INSERT` only. **[Inferred]** a deployment that wants this enforced rather than promised should `REVOKE UPDATE, DELETE ON oo_event`; the package does not issue grants |
| DDL rights | see §9.3 — an enterprise deployment where the DBA owns DDL sets `owns_schema=False` and `migrate()` becomes verify-only |

**Deliberately not used**, so the two backends stay honest about the same things: `SERIAL`/`IDENTITY` (§4.2), `ON CONFLICT … DO UPDATE` as a substitute for reading inside the transaction (it would hide `already_decided`), array columns (SQLite has none, and the join table is the shared shape), and `LISTEN`/`NOTIFY`.

### 4.5 How `attributes` is stored

One JSON document per row in `oo_type.attributes_json`, plus one integer, `oo_type.attr_schema_version`, recording the attribute schema in force **at write time**. `NULL` means it was written with validation off.

Those two columns are the whole of §5 at the storage layer. The adapter treats the document as opaque: it never reads a key, never validates, never merges. Validation, when a deployment turns it on, happens above the adapter — because a backend that validated would be a backend making a policy decision, which §3.1 forbids.

---

## 5. `attributes` — the schema-per-kind mechanism

`INTERFACE.md` §11 hands this to #2: *"`attributes` is unversioned. Everything v0 cannot type goes there. Without a schema-per-kind mechanism in #2, it will accumulate."*

**Decision: designed, not declared a gap — with the default set so that #2 does not silently change #1's contract.**

### 5.1 Why it is worth designing, in CMS's terms rather than Tenshen's

`INTERFACE.md` §10.1 calls the A–L scope-and-severity ordering *"the single most consequential domain semantic in the dataset"*, and §10 puts it in `attributes` because a `value_set`'s ordering has nowhere else to live. So today the ordering that decides which nursing homes are Immediate Jeopardy is **an unversioned, unvalidated, undescribed list inside an opaque dict** — the exact thing 0.5 found the cheapest model tier inverted.

That is a CMS-driven argument. Tenshen's `is_symmetric`/`inverse_label` (§9 contortion 1) also live in `attributes`, but the mechanism is **not** shaped for them and does not fix them: edge shape is #4. Recorded per `ROADMAP.md`'s rule of the ordering — the mechanism exists because the CMS data needs it.

### 5.2 The mechanism

An `AttributeSchema` is **configuration owned by the deployment**, versioned, and stored in its own table:

```python
@dataclass(frozen=True)
class FieldSpec:
    type: str                       # str | int | float | bool | list | dict | datetime
    required: bool = False
    enum: tuple | None = None
    item_type: str | None = None    # for list
    description: str = ""           # REQUIRED non-empty — see below

@dataclass(frozen=True)
class AttributeSchema:
    namespace: str
    kind: str                       # entity | predicate | edge | value_set | <open>
    version: int                    # monotonic per (namespace, kind)
    fields: dict[str, FieldSpec]
    additional: str                 # "allow" | "warn" | "forbid"  — unlisted keys
    mode: str                       # "off" | "warn" | "enforce"
    registered_at: datetime
    registered_by: str
```

Stored in an eighth table, `oo_attr_schema (namespace, kind, version)` — **not** as a new `TypeEntry` kind. The dogfooding option (register a schema as `kind="attribute_schema"`, getting provenance and the approval loop for free) was considered and **rejected**: an attribute schema is not a word in the vocabulary, and putting it in `oo_type` means `list_types()` mixes schemas with vocabulary and `merge_types` can be pointed at one. That is `INTERFACE.md` §2.3's Cause B — one container meaning two things — committed by the schema itself. **Cost of the rejection, stated: attribute schemas have no proposal→approval loop in v0.** Recorded as a weakness in §11.

**`FieldSpec.description` is required and non-empty**, on exactly the reasoning of `INTERFACE.md` §2.1's non-empty `definition`: an undescribed field is how the escape hatch re-forms one level down.

### 5.3 Three modes, and the default is `off`

| Mode | Behaviour on a violation |
|---|---|
| `off` | nothing is checked. **The v0 default.** |
| `warn` | the write succeeds; `warnings` gains `attributes_invalid:<field>:<why>`; the entry is thereafter enumerable |
| `enforce` | `propose_type` / `approve` return `Refusal(reason="attributes_schema_violation", detail={…})` |

**Why `off` is the default.** `INTERFACE.md` §2.1 states that `attributes` is *"opaque to v0"* and that *"the registry never reads them"*. A #2 that validated by default would change #1's contract unilaterally, which the ordering rule does not permit and which would make every existing statement in §2.1 wrong. With `off` as the default, an untouched deployment behaves exactly as `INTERFACE.md` describes, and a deployment that wants the guarantee opts in. The disagreement is recorded in §11 for #1 to absorb.

### 5.4 What happens to entries written under an older schema

> **They are never rewritten and never retroactively invalidated.**

`oo_type.attr_schema_version` records the version in force at write. Reading returns the attributes verbatim alongside that version. Adding a `required=True` field in v2 does not make v1 rows invalid — **it makes them v1 rows.**

The reasoning is `INTERFACE.md` §2.4 and §5.8: provenance is append-only and *a correction is a new event, never an edit*. Silently re-validating an old row against a new schema — or worse, migrating its attributes — is a rewrite of a record that carries an approval. The package ships **no** attribute migrations. A deployment that wants one writes it, and it lands as ordinary `put_type` calls with new `ProvenanceEvent`s, visible in `history` like any other change.

Consequence, stated: a store can contain three generations of `value_set` attributes at once, and `enforce` mode does not fix that retroactively. **That is the honest state and the census is how you see it.**

### 5.5 The floor that applies even in `off` mode — the attribute census

Setting the default to `off` would leave §11's actual worry — *it will accumulate if nobody watches it* — untouched. So one thing happens unconditionally, in every mode, on every backend that can store attributes:

**every distinct attribute key ever written is recorded.**

```
oo_attr_observed
    namespace, kind, key         NOT NULL
    n              INTEGER       NOT NULL     -- writes seen carrying this key
    first_seen, last_seen        NOT NULL
    example_json   TEXT/jsonb                 -- one example value, most recent
    PRIMARY KEY (namespace, kind, key)
```

Exposed as one method on the façade:

```python
Registry.attribute_census(namespace: str = "default", kind: str | None = None) -> AttributeCensus
```

returning, per `(kind, key)`: `n`, `first_seen`, `last_seen`, an example, whether the key is declared in the current schema, and the spread of `attr_schema_version` across rows carrying it.

This is the same move as `ConsumerReport.complete = False`: it does not solve the problem, it makes the problem **visible and enumerable** rather than silent. It also gives the only sane migration path — you read the census, *then* write a schema that matches reality, *then* turn on `warn`, *then* `enforce`.

> **Recorded by deliverable #3, 2026-08-28 — this section specifies two tables and a facade method but adds no primitive to carry them,** while §3.4 stays at fifteen and `C0-04` polices the boundary. Phase 2A reaches them through an **optional `AttributeStore` protocol, outside the fifteen and outside conformance**, which is consistent with ruling R2. A backend that does not implement it is still fully conformant, and `attribute_census` then reports `complete=False` with a `why` rather than an empty census. See [`2A-RUN.md`](../runs/2A-RUN.md) §4.4, deviation D-2.

**Flagged: `attribute_census` is a method beyond the calls enumerated in `INTERFACE.md` §5.** It is the only one this document adds. §11 asks for a ruling: absorb it into #1, or keep it package-local and out of the conformance definition. **Ruled R2: package-local, outside the conformance definition.** The suite tests it (`C15-02`) and a backend may not be failed for it — the test is marked **`nonbinding`**, and since row 3c that marker actually deselects it from a conformance verdict rather than merely annotating it (§6.1). *(This sentence previously named a marker, `xfail_if_not_declared`, that exists nowhere in the codebase — corrected by row 3c after an adversarial review round.)*

### 5.6 What it does not fix

- It does not give `is_symmetric`/`inverse_label` a home. It lets them be *declared*; edge shape is still #4 (`INTERFACE.md` §9 contortion 1).
- It does not validate cross-field rules (*"a symmetric edge must have no inverse label"*). `FieldSpec` is per-field on purpose; a rule language here would be a schema language, which is a much larger thing than v0 needs.
- **It cannot serve two `value_set`s of one dataset differently, and that includes the two this section is justified on** *(recorded by row 3c, 2026-08-28, after an adversarial review round)*. A schema is keyed `(namespace, kind, version)` — **one per kind, not per type name** — and CMS has two `kind="value_set"` entries with different shapes: `scope_severity_code` must be made to declare an `ordering` (§5.1's whole argument) and `deficiency_corrected_status` has no order to declare. A deployment gets one of two wrong answers and there is no third: `ordering` required refuses the unordered set for lacking a field it has no business having, and `ordering` optional lets the ordered set be created with no ordering — **which is the CMS severity scale back inside somebody's transform, unversioned, which is the exact thing §5.1 says this mechanism exists to prevent.** Both horns are asserted by `C15-07`. The fix — key schemas `(namespace, kind, name)`, or allow a name-level override — is a change to §5.2's storage shape and **wants a ruling**; see [`../findings/3C-VALIDATION.md`](../findings/3C-VALIDATION.md) §6.
- It does not stop a deployment from writing `attributes={"stuff": {...}}` and putting an entire nested world in one declared `dict` field. Nothing can, short of a schema language.

---

## 6. The contract suite — the definition of conformance

### 6.1 The rule

> **A backend is conformant iff the whole suite passes against it. The suite is parametrised over both reference backends and must pass on both, in one process, in one run.**

Per **A5** (founder-confirmed 2026-08-28), this suite passing on CMS data is the gate for Phase 2B — the condition that replaces §12's "real outside user" and permits Tenshen to depend on the package.

Two rules that keep the definition honest:

1. **Capability-honest tests.** A test whose subject is a declared-`False` capability asserts the *honest unknown* — `None` plus a non-empty `why` drawn from `Capabilities.why` — not a value. A backend that cannot count usage passes `C7-01` by returning `count=None`; it fails by returning `0`. This is what makes conformance achievable for unlike backends without weakening it.
2. **Two capabilities are not negotiable.** `enforces_unique_name` and `transactional` must be `True` (§3.5). Everything else may be `False`.

**Running it.** `pytest --pyargs open_ontology.contract`, or against a foreign backend `python -m open_ontology.contract --adapter beacon.ontology:WorkLinkTypeAdapter`.

*(This paragraph amended by row 3c, 2026-08-28, after an adversarial review round found the conformance machinery did not enforce what this section claims.)*

**`nonbinding` now exempts, where before it only annotated.** §5.5 says a backend *"may not be failed for"* `C15-02`. Registering `@pytest.mark.nonbinding` never made that true: the runner passed every test, so a backend that honestly declines the optional `AttributeStore` protocol — behaviour §5.5 explicitly permits — got `complete=False`, failed `C15-02`'s assertion, and was reported as failing the suite. **Verified before it was fixed:** a wrapper that omits `AttributeStore` returns `AttributeCensus(entries=(), known=None, complete=False, why="this backend has no attribute census storage")` and fails that test. `run_contract_suite` and `python -m open_ontology.contract` now pass `-m "not nonbinding"` by default, with `--include-nonbinding` to run them anyway. **A conformance verdict is the default run; the flag is for curiosity.**

**Resolver-dependent tests are binding here and not there.** `C3-08`, `C3-09` and `C4-06` carry a `resolver_dependent` marker. Against the two reference backends they run and must pass — they pin real behaviour of the resolver this package ships. Against a foreign adapter (`--adapter`, or `run_contract_suite`) they are **skipped with a reason naming §2.6 and question **Q4****, because a third-party backend paired with its own resolver — §2.6's own production path — was otherwise failing mandatory conformance tests for a reason that is neither its storage nor its choice. Skipped, never silent: `-rs` prints exactly what was not run and why.

**Every run states what it covered.** §6.1 requires *both* reference backends *in one run*, and a bare `pytest --pyargs open_ontology.contract` with no `OO_POSTGRES_DSN` exits `0` having exercised SQLite alone — a skip is easy to miss beside a wall of passes. The suite now prints, at the end of every run:

```
CONFORMANCE (PACKAGE.md 6.1)
  backends exercised: postgres, sqlite
  nonbinding tests excluded from the verdict: none
```

and, when a reference backend did not execute, **`NOT a conformance run -- postgres did not execute`** in its place. It is still possible to run the suite without Postgres; it is no longer possible to read the result as conformance.

### 6.2 The suite, enumerated

**119 tests in seventeen groups.** *(109 at #3; **ten** added by row 3c — `C0-07`, `C0-08`, `C0-09`, `C3-10`, `C5-12`, `C6-07`, `C9-07`, `C9-08`, `C15-07`, `C15-08`. See §8b.2 and §8b.5.)* Mechanism labels are `INTERFACE.md` §4's: **1** no review · **2** could not find · **3** never retired · **4** collision · **C** silent per-consumer drop.

**C0 — adapter conformance (9).** No interface call; this is the protocol itself.

| id | asserts | mech |
|---|---|---|
| C0-01 | `capabilities()` returns every field; every `False` flag has a non-empty `why` | — |
| C0-02 | **G1**: `put_type(expect_absent=True)` twice raises `AlreadyExists` from a constraint | — |
| C0-03 | **G2**: an exception inside `transaction()` leaves the store byte-identical | — |
| C0-04 | **§3.1, by source inspection**: all **seven** of §3.1's identifiers — `Refusal`, `Rejection`, `Resolution`, `ConsumerReport`, `UsageReport`, `TypeEntry`, `Proposal` — appear nowhere in `adapter.py` or `backends/`. *(Row 3c: the test checked five of the seven; `ConsumerReport` and `UsageReport` were missing from it, though neither was ever present in the code)* | — |
| C0-05 | `migrate()` is idempotent; the version row is written in the same transaction as the DDL | — |
| C0-06 | every `*Record` round-trips; a field the backend cannot store comes back empty, not wrong | — |
| C0-09 | **`owns_schema=False` makes `migrate()` verify-only** (§9.3): against a store the host application owns, `migrate()` raises `SchemaMismatch` naming what is missing, issues no DDL to fix it, and once the owner has created the schema returns the version and is usable. *(Row 3c. B1 is the first Tenshen contortion and the enterprise-DBA posture is the reference deployment — both reference backends implemented this and nothing asserted it.)* | — |
| C0-08 | **G1 and G2, RACED:** two adapters on one store and two real concurrent writers — one absent name (exactly one insert wins, one `AlreadyExists`, one row in the store) and one proposal approved twice (exactly one `TypeEntry`, one `Refusal("already_decided")`). *(Row 3c, §8b.5. `C0-02`/`C0-07` call the primitives sequentially, which a read-then-write check passes as happily as a constraint does — §3.5 says a read-then-write check is **not** sufficient, and until this test nothing held it to that. A thread race has no mechanical async form, so the sync module is excluded from `tools/unasync.py` and the async counterpart is hand-written; both claim this id and both are binding.)* | — |
| C0-07 | **G1's key is *scoped*:** one word under three namespaces is three rows, each `expect_absent=True`, each retrievable with its own definition and attributes; the collision is still raised *within* a namespace; `TypeQuery(namespace=None)` returns all three. *(Row 3c, §8b.2 — the half of G1 that `INTERFACE.md` §2.6's answer to mechanism 4 rests on, and that nothing asserted)* | **4** |

**C1 — `consumers` (8).** Mechanism **C**.

| id | asserts |
|---|---|
| C1-01 | `complete` is `False` even when every consumer in the store is registered |
| C1-02 | `why_incomplete` is non-empty and names *registered, not discovered* |
| C1-03 | an unknown type raises `UnknownType` — **never** an empty report |
| C1-04 | `gates_on` = consumers whose gate predicate includes the type |
| C1-05 | `would_drop` = gate excludes **and** `on_unknown == "drop"` |
| C1-06 | `would_error` = gate excludes **and** `on_unknown == "error"`; `passthrough` appears in neither |
| C1-07 | `known == len(gates_on) + len(would_drop) + len(would_error)` |
| C1-08 | **the `capture` incident replay** (finding 0.1): register a consumer gating on a predicate whose extent excludes a newly-approved type; `would_drop` is non-empty and names it |

**C2 — `predicates` (5).** Mechanisms **4** (defensively) and the `ROADMAP.md` kill row.

| id | asserts |
|---|---|
| C2-01 | the extent is **derived**: writing membership touches only the member's rows; the predicate's own record is unchanged, and no consumer-membership table exists |
| C2-02 | `indexes_membership=False` ⇒ `extent=[]` **with `extent_size=None`** and a `why` — never `extent_size=0` |
| C2-03 | `of=` returns only predicates that type satisfies |
| C2-04 | `include_retired` |
| C2-05 | a predicate is not a supertype: membership of `commentable` implies nothing about `searchable` |

**C3 — `resolve_type` (10).** Mechanisms **2**, and **1** as the gate.

| id | asserts | note |
|---|---|---|
| C3-01 | `existing` sets `confidence` to a float | |
| C3-02 | **`proposal` persists nothing** — the store is byte-identical after the call | the call that must not write |
| C3-03 | below `min_confidence` ⇒ `outcome="none"` with `alternatives` populated | never the best of a bad set |
| C3-04 | `confidence is None` when no scorer ran; `None != 0.0` | Rule U |
| C3-05 | `tier` is required — omitting it is a `TypeError`, not a default | §2.7 |
| C3-06 | `tier` is echoed on the `Resolution` and lands in provenance unchanged | |
| C3-07 | a prior rejection for the candidate surfaces in `alternatives` | §5.5 |
| C3-08 | **[CMS]** `resolve_type("location", context(sibling_columns=["Provider Address","City/Town","State","ZIP Code"]))` ⇒ `not_a_type` / `redundant_projection`. **`resolver_dependent`** — binding for the reference backends, skipped for a foreign adapter (§2.6, Q4) | §10.2 |
| C3-09 | **[CMS]** `resolve_type("processing_date", …)` on a single-valued column ⇒ `not_a_type` / `export_artefact`. **`resolver_dependent`** (§2.6, Q4) | §10.2, T7 |
| C3-10 | **a retired name is named in the resolution**, with its `retire_reason` and `successor`, and listed in `alternatives` with a `None` score — never a bare *"nothing fits"*. *(Row 3c: `resolve_type` read the tombstone and discarded it, answering with a confident negative about a word it knew was burned — Rule U, in the call designed against mechanism 2)* |

**C4 — `propose_type` (9).** Mechanism **1**.

| id | asserts |
|---|---|
| C4-01 | empty `definition` raises `ValueError` |
| C4-02 | `proposed_by="ai:…"` with `tier=None` raises `ValueError` |
| C4-03 | a name already taken in `(namespace, kind)` returns the **existing `TypeEntry`** — not an error |
| C4-04 | a near-duplicate returns a `Proposal` with `warnings=["near_duplicate:<name>"]` and **does not refuse** — the kill-row protection |
| C4-05 | `evidence=[]` ⇒ `warnings` contains `no_evidence`; the proposal is still created |
| C4-06 | a definition asserting a domain semantic with no `external_doc` evidence ⇒ `unverified_semantics`. **`resolver_dependent`** — the keyword rule behind it is not even behind the `Resolver` seam (§2.6, §8b.3 B8, Q4) |
| C4-07 | under `approval_policy="auto"` the return is a `TypeEntry` with `provenance.approved_by == "auto:<policy>"` — **never blank** |
| C4-08 | a retired name ⇒ the retired entry plus `warnings=["name_previously_retired"]`, and no new entry |
| C4-09 | `^[a-z][a-z0-9_]{0,63}$` enforced identically on both backends |

**C5 — `approve` / `reject` (12).** Mechanism **1**.

| id | asserts |
|---|---|
| C5-01 | `approve` sets `approved_by`, `approved_at`, `status="active"` |
| C5-02 | **the §2.4 invariant**: no `active` entry anywhere in the store has a null `approved_by` |
| C5-03 | **the severity case, verbatim from §10:** `propose_type(name="scope_severity_code", kind="value_set", definition="…Higher letters are LESS serious.", evidence=[], proposed_by="ai:proposer", tier="haiku")` then `approve(mode="auto")` ⇒ `Refusal(reason="tier_below_auto_approve_policy", detail={"tier":"haiku","min_auto_approve_tier":"sonnet"})` |
| C5-04 | approving an already-decided proposal ⇒ `Refusal("already_decided")` — idempotent, not an exception |
| C5-05 | an unknown proposal id ⇒ `Refusal("unknown_proposal")` |
| C5-06 | approving with `unverified_semantics` **succeeds**, and the entry keeps the warning permanently |
| C5-07 | an approver's amendment to `definition`/`predicates` keeps the original in `history` |
| C5-08 | `reject` with an empty reason raises |
| C5-09 | a rejection is **retained** and findable — the record that stops re-proposal in six months |
| C5-10 | `reject(superseded_by=…)` records the successor |
| C5-11 | **atomicity**: an injected failure between the type write and the event write leaves no type and no decided proposal |
| C5-12 | **`proposals_not_stored`**, on a backend with `stores_proposals=False`: `propose_type` **is** the decision and returns an auto-approved `TypeEntry` with a non-blank `approved_by`; `approve` and `reject` return `Refusal("proposals_not_stored")` — not `unknown_proposal`, which would be a confident wrong answer about a proposal that was never storable. *(Row 3c. §3.6 introduced this reason and §6.3 claimed it was covered; it had no test anywhere in either suite, and it is UC1's own path — §7.3 B4)* |

**C6 — `list_types` (7).** Mechanism **2**.

| id | asserts |
|---|---|
| C6-01 | `complete=False` whenever any filter suppressed rows — including the default `include_retired=False` |
| C6-02 | `known` counts the returned set, and is `None` (not `0`) when the backend cannot count |
| C6-03 | `predicate=` returns the extent, and matches `predicates(of=…)` in the other direction |
| C6-04 | the true census — `include_retired=True, status=None, namespace=None` — reports `complete=True` |
| C6-05 | `orphaned=True` **excludes** types whose `orphaned` is `None`; the count of excluded-as-unknown is reported |
| C6-06 | `unverified_semantics=True` enumerates exactly the entries carrying the warning |
| C6-07 | **the census spans namespaces and a scoped listing says it did not:** `namespace=None` returns one word's three scoped entries with three definitions and `complete=True`; `namespace="dot"` returns one with **`complete=False`** and a `why_incomplete` naming the namespace *(row 3c, §8b.2)* |

**C7 — `usage` (6).** Mechanism **3**.

| id | asserts |
|---|---|
| C7-01 | `counts_usage=False` ⇒ `count=None` with a `why` — **never `0`** |
| C7-02 | `timestamps_usage=False` ⇒ `last_seen=None` — **never "never"** |
| C7-03 | **`last_seen` unknown ⇒ `orphaned=None`, never `False`** — contortion 2's test |
| C7-04 | `status="active"` + `last_seen < now - window` ⇒ `orphaned=True`, and `window` is reported |
| C7-05 | `get_usage` returning `None` (nothing recorded) and returning `count=None` (not counted) produce **different** `UsageReport`s |
| C7-06 | `record_use` on a non-counting backend is a no-op and `usage()` says so |

**C8 — `provenance` (5).** Mechanisms **1** and **3**.

| id | asserts |
|---|---|
| C8-01 | missing evidence is `[]` — never a reconstructed narrative |
| C8-02 | `history` is append-only: after a correction, no prior event's bytes changed |
| C8-03 | `approved_by` on an auto-approved entry has the form `auto:<policy>` |
| C8-04 | an imported row carries `unknown:imported`, never null |
| C8-05 | `model_tier` is never overwritten by a later approval or amendment |

**C9 — `retire` (8).** Mechanism **3**.

| id | asserts |
|---|---|
| C9-01 | non-empty `gates_on` ⇒ `Refusal("live_consumers", detail={"gates_on":[…]})` |
| C9-02 | `force=True` overrides **and records** — and on `stores_events=False` returns `Refusal("cannot_record_override")` instead (§3.6) |
| C9-03 | `orphaned is None` ⇒ retirement proceeds with `warnings=["retired_without_usage_evidence"]` |
| C9-04 | the retired name is not reusable (pairs with C4-08) |
| C9-05 | an empty `reason` raises |
| C9-06 | `successor` is recorded and surfaces in `provenance` |
| C9-07 | **an unknowable consumer set blocks the retirement:** on `indexes_membership=False` every extent is empty, so an empty `gates_on` means *we could not look* — `Refusal("no_consumer_evidence")`, overridable by `force=True`. *(Row 3c. `retire` read an empty `gates_on` as "nothing gates on this" and **silently retired a type with a live registered consumer** — mechanism C committed by the call built to catch it)* |
| C9-08 | **`force=True` is refused when it cannot be recorded, whichever guard it overrides** — `indexes_membership=False` **and** `stores_events=False` together, which is `work_link_types`' own declared shape (B3 + B6). *(Row 3c. The recordability check lived inside the `live_consumers` branch, and with no extent to compute `gates_on` is always empty, so the branch never ran: a type with a live registered gate retired with no refusal, no warning and no history — while §7.3 B6 says in terms that this case returns `cannot_record_override`. `merge_types` had the unconditional form since v0)* |

**C10 — `merge_types` (8).** Mechanism **4**.

| id | asserts |
|---|---|
| C10-01 | different **known** consumer sets ⇒ `Refusal("different_consumer_sets")`, and neither `force` nor `acknowledge` overrides it |
| C10-02 | **the `ROADMAP.md` kill row:** either side `kind="predicate"` with non-identical extents ⇒ `Refusal("predicate_merge")`, non-overridable |
| C10-03 | different `kind` ⇒ `Refusal("kind_mismatch")`, non-overridable |
| C10-04 | different `namespace` ⇒ `Refusal("cross_namespace_merge")`, non-overridable |
| C10-05 | a retired operand ⇒ refusal, overridable by `acknowledge=["retired_operand"]` |
| C10-06 | diverging definitions ⇒ refusal, overridable by `acknowledge=["definitions_diverge"]` |
| C10-07 | **both consumer sets empty ⇒ `Refusal("no_consumer_evidence")`** — the one place "we do not know" blocks rather than warns |
| C10-08 | every `acknowledge` is recorded in `history`; on `stores_events=False` the merge is refused with `cannot_record_override` |

**C11 — `register_consumer` / `record_use` (4).** Mechanism **C**.

| id | asserts |
|---|---|
| C11-01 | a consumer round-trips with `on_unknown`, `owner`, `locator` intact |
| C11-02 | a consumer may gate on a predicate that does not exist; it registers, and the type shows up in `would_drop` |
| C11-03 | `record_use` advances `last_seen` when `timestamps_usage=True` |
| C11-04 | a read-only consumer source (a config file) ⇒ `register_consumer` returns a refusal, never a silent no-op |

**C12 — Foundry import mapping (4).** From 0.3 consequence 2 / `INTERFACE.md` §2.5.

| id | asserts |
|---|---|
| C12-01 | `experimental` ⇒ **`active` plus predicate `experimental`** — never `proposed` |
| C12-02 | `deprecated` ⇒ `retired` with `retire_reason="imported: foundry deprecated"` |
| C12-03 | `apiName` and `rid` land in `provenance.imported_from`, not in fields of our own |
| C12-04 | `visibility` and `groups` land in `attributes` |

**C13 — the CMS design test (5).** Uses the 0.5 sample; see §8.

| id | asserts |
|---|---|
| C13-01 | the sample's vocabulary loads: 4 `entity`, 2 `value_set`, 2 `edge` = **8 rows in `oo_type`** |
| C13-02 | `oo_usage.count` per type matches the pre-registered ground truth (§8.2) |
| C13-03 | `deficiency_corrected_status` carries **six** values full-file and none of them is a yes/no — T1 |
| C13-04 | `scope_severity_code` is `kind="value_set"`, `ordered`, and carries an `external_doc` `Citation` with a `url`, `title` and `retrieved_at` |
| C13-05 | `kind="value_set"` is accepted by `propose_type` and survives a round trip on both backends |

**C14 — the Tenshen contortions, documented (7).** One per contortion in `INTERFACE.md` §9. **Every one of these passes when the interface behaves as specified — not when Tenshen is accommodated.**

| id | contortion | asserts |
|---|---|---|
| C14-01 | 1 | `is_symmetric`/`inverse_label` in `attributes` are **not validated** by v0; a symmetric type with an inverse label is accepted and nothing complains |
| C14-02 | 2 | a bare counter ⇒ `count` set, `last_seen=None`, **`orphaned=None`** |
| C14-03 | 3 | a source with no status migrates every row `active`, and no retirement history is invented |
| C14-04 | 4 | no approval step ⇒ `approval_policy="auto"` and `approved_by="auto:classifier"` — **the auto-approval is legible and enumerable**, which is the point |
| C14-05 | 5 | an AI-created type with a discarded fit score has `evidence == []` and carries `no_evidence` — honest and unflattering |
| C14-06 | 6 | zero registered consumers ⇒ `known=0, complete=False` — a null result reported as a null result |
| C14-07 | 7 | **the package ships no default type**: no name `default_type`, no fallback constant, anywhere in the public surface. The `related_to` fallback is caller policy and stays there |

**C15 — the `attributes` mechanism (8).** §5 of this document.

| id | asserts |
|---|---|
| C15-01 | with no schema registered, behaviour is byte-identical to `INTERFACE.md` §2.1 — opaque, unread, unvalidated |
| C15-02 | the census records every key written, in `off` mode, and reports the `attr_schema_version` spread *(see §5.5 — not yet part of the conformance definition)* |
| C15-03 | `warn` adds `attributes_invalid:<field>` and does **not** refuse |
| C15-04 | `enforce` returns `Refusal("attributes_schema_violation")` with the offending field in `detail` |
| C15-05 | a v2 schema with a new required field does **not** invalidate v1 rows; they read back verbatim with `attr_schema_version=1` |
| C15-06 | under `enforce`, a `value_set` without a declared `ordering` when `ordered=True` is refused — the CMS severity case |
| C15-07 | **one schema per kind cannot serve both CMS `value_set`s:** with `ordering` required, `deficiency_corrected_status` is refused for lacking an order it has no business having; with `ordering` optional, `scope_severity_code` may be created claiming an order and declaring none — the pollution §5.1 says the mechanism exists to prevent. Both horns asserted. *(Row 3c, §5.6 — a limitation of the mechanism, not of any backend)* |

**C16 — whole-store invariants (4).** *(Amended by row 3c: this said "run once at suite end, over everything the suite wrote". The shipped group is **function-scoped** — a fixture drives one store through representative write paths and each test then inspects it. Recorded at 2A as deviation D-9 and never brought inline here. It matters because "everything the suite wrote" would be a stronger claim than the tests make.)*

| id | asserts |
|---|---|
| C16-01 | every `active` entry has a non-null `approved_by` |
| C16-02 | no retired name was reused |
| C16-03 | no event's bytes changed after it was written |
| C16-04 | every list-shaped result produced during the run carried both `complete` and `known` |

### 6.3 Coverage check against `INTERFACE.md` §5

Every refusal and every specified uncertainty behaviour in §5, with its test:

| §5 refusal / behaviour | test |
|---|---|
| `UnknownType` not an empty report | C1-03 |
| `complete` always `False` | C1-01, C1-02 |
| `extent_size: None` | C2-02 |
| below `min_confidence` ⇒ `none` | C3-03 |
| `not_a_type` (both CMS reasons) | C3-08, C3-09 |
| `confidence: None ≠ 0.0` | C3-04 |
| empty definition | C4-01 |
| `ai:` without tier | C4-02 |
| name taken ⇒ existing | C4-03 |
| near-duplicate warns, never refuses | C4-04 |
| `no_evidence` | C4-05 |
| `unverified_semantics` | C4-06, C5-06 |
| `name_previously_retired` | C4-08 |
| `tier_below_auto_approve_policy` | **C5-03** |
| `already_decided` | C5-04 |
| `unknown_proposal` | C5-05 |
| `reject` requires a reason | C5-08 |
| `live_consumers` | C9-01 |
| `no_consumer_evidence` (retire) | **C9-07** |
| `cannot_record_override` (retire, compound) | **C9-08** |
| `retired_without_usage_evidence` | C9-03 |
| retired name not reusable | C9-04, C16-02 |
| `different_consumer_sets` (non-overridable) | C10-01 |
| `predicate_merge` (non-overridable) | C10-02 |
| `kind_mismatch` | C10-03 |
| `cross_namespace_merge` | C10-04 |
| `retired_operand` (overridable) | C10-05 |
| `definitions_diverge` (overridable) | C10-06 |
| `no_consumer_evidence` | C10-07 |
| `record_use` may be a no-op | C7-06, C11-03 |

**No §5 refusal is untested, and since row 3c that is true rather than merely stated.** The four refusals this document adds (§3.6) are tested at:

| refusal | test |
|---|---|
| `cannot_record_override` | `C9-02` (retire), `C10-08` (merge) |
| `attributes_schema_violation` | `C15-04`, `C15-06`, `C15-07` |
| `consumer_source_read_only` | `C11-04` (ruling R4) |
| **`proposals_not_stored`** | **`C5-12`** |

> *Corrected by row 3c after an adversarial review round.* This line read *"the three refusals this document adds are tested at C9-02, C10-08, C15-04"* — which names three ids covering **two** of the reasons, and left **`proposals_not_stored` with no test anywhere in either suite**. That is UC1's own path (§7.3 B4: a backend with no proposal table is conformant and `approve`/`reject` must refuse), so the capability the Tenshen design test most depends on was the one the suite never checked. `C5-12` closes it.

**[Inferred]** the built suite will be larger than 119 — parametrisation over kinds and over `on_unknown` values will multiply several of these. The enumeration is the coverage floor, not a budget.

---

## 7. The Tenshen design test for #2 — can `work_link_types` sit behind the adapter?

**A design *test*, not a design *input*** (`ROADMAP.md`, rule of the ordering). Read read-only on 2026-08-28 from `beacon/src/beacon/models/work_link_type.py` and `beacon/src/beacon/services/work_link_service.py`. **Nothing in beacon was edited.** **[Observed]** unless marked.

**The question, from `ROADMAP.md` 2B:** *one service, one table — not a rewrite.* Can that one table be a third backend?

### 7.1 The subject, as it stands

```
work_link_types
    id             int      PK
    name           String(64)  NOT NULL  UNIQUE          -- globally unique, no namespace/kind
    definition     Text        NOT NULL
    is_symmetric   Boolean     NOT NULL  DEFAULT False
    inverse_label  String(64)  NULL
    created_by     String(20)  NOT NULL  DEFAULT "seed"   -- seed | ai | user
    usage_count    Integer     NOT NULL  DEFAULT 0
    created_at     DateTime    NOT NULL  server_default now()
```

**Absent:** `status`, `namespace`, `kind`, `attributes`, `aliases`, predicates, evidence, any provenance beyond `created_by`/`created_at`, `last_used_at`, and any proposal, consumer, rejection or event table.

**One determination this document makes that `INTERFACE.md` §9 left open: these rows are `kind="edge"`.** They are relationship types for `WorkLink` rows, and `INTERFACE.md` §2.2 defines `edge` as *"a relationship type. Registered here (name, definition, provenance, lifecycle); its shape and its instances live in #4."* That is exactly what `work_link_types` is. The adapter therefore supplies `namespace="default"` and `kind="edge"` as constants — both free, both invisible to beacon.

### 7.2 The fifteen primitives, walked

| # | Primitive | Against `work_link_types` | Verdict |
|---|---|---|---|
| 1 | `capabilities()` | returns `enforces_unique_name=True`, `transactional=True`, everything else `False` with a `why` | ✅ **and this is the primitive that makes the whole thing possible** |
| 2 | `migrate()` | beacon owns this schema (Alembic). Must be verify-only | **B1** |
| 3 | `transaction()` | beacon's `AsyncSession` — **the protocol is sync** | **B2 — blocking** |
| 4 | `put_type(expect_absent=True)` | `name UNIQUE` is *stronger* than G1 needs (global vs per `(ns,kind)`) — fine, since there is one implicit namespace and one kind. But seven `TypeRecord` fields have no column | ✅ on G1; **B3** on fields |
| 5 | `get_type` | `SELECT … WHERE name = ?`, constants filled in | ✅ |
| 6 | `find_types` | `status`/`kind`/`namespace` are constants; `created_by` maps; `predicate=` ⇒ empty page with `known=None` and a `why` | ✅ with honest incompleteness |
| 7 | `put_proposal` | no proposal table | **B4** |
| 8 | `get_proposal` | no proposal table | **B4** |
| 9 | `find_proposals` | no proposal table | **B4** |
| 10 | `put_consumer` | no consumer table — **and none is needed**, see below | ✅ |
| 11 | `find_consumers` | a config-backed consumer source, no table at all | ✅ **highest-value primitive available to beacon** |
| 12 | `bump_usage` | `usage_count = usage_count + 1` | ✅ |
| 13 | `get_usage` | `count` set; `first_seen`/`last_seen` `None` + `why` | **B5** (= §9 contortion 2, confirmed at the storage layer) |
| 14 | `append_event` | no event table | **B6** |
| 15 | `read_events` | no event table ⇒ `history=[]` + `why` | **B6** |

**Nine of fifteen serve as-is.** Six carry a contortion.

### 7.3 The six contortions, recorded and not designed away

**B1 — the adapter cannot own a schema the host application owns.**
beacon's Alembic owns `work_link_types`. `migrate()` issuing DDL against it would be this package reaching into another program's migration history.
**Resolution: `Capabilities.owns_schema=False` makes `migrate()` verify-only** — it checks the columns it needs exist and raises `SchemaMismatch` naming what is missing, and never issues DDL.
**This is a change to my own adapter protocol, and it needs justifying against the rule of the ordering.** It is **not** taken because Tenshen has it: the identical case is the reference deployment. An enterprise Postgres deployment where the DBA owns DDL and the application role has no `CREATE` right is the normal posture at an organisation like the one A1 describes, and it needs verify-only `migrate()` for the same reason. **Adopted on the CMS/reference-deployment case; the Tenshen test is what surfaced it.**

**B2 — beacon is async; the protocol is sync. This blocks ROADMAP #5, and it is #2's problem, not beacon's.**
beacon's data layer is `sqlalchemy.ext.asyncio.AsyncSession` throughout. Three options were considered:

1. *Make the protocol async.* Poisons the SQLite backend and the contract suite, and forces every caller — including a synchronous CMS ingest script — into an event loop.
2. *Keep it sync; beacon calls it through `asyncio.to_thread`.* **Does not work.** The adapter would then need its own connection, so `create_work_link` could not write the link and bump the type's usage in one transaction. It would also drive an `AsyncSession` from another thread, which is not safe.
3. *Ship both: `StorageAdapter` and `AsyncStorageAdapter`, `Registry` and `AsyncRegistry`, with the contract suite parametrised over both.*

**Decision: (3) is right, and v0 ships (1)-shaped sync only.** Doubling the surface before there is a single implementation is generality-before-need (`ROADMAP.md` constraint 2), and 2A — the reference implementation and the CMS data path — is synchronous.

**But the consequence must not be buried: Phase 2B cannot land on a sync-only package.** `AsyncStorageAdapter` is a **named prerequisite of ROADMAP #5** and it belongs to this deliverable's line, not to the beacon program. Escalated in §11.

> **Resolved 2026-08-28 — option 3, and B2's *sync-only* half is closed.** Ruling **R1** made it row **3b**, which landed with `AsyncStorageAdapter`, `AsyncRegistry`, async SQLite and async Postgres, and the same 109 contract ids green on both (`267 passed`). Option 3's stated cost — two implementations to keep in step — was avoided rather than paid: the async tree is **generated from the sync source** by `tools/unasync.py` and a suite check fails when it is stale, so there is no second copy of the registry logic. Option 1's objection stands and is why the sync package is untouched: a synchronous CMS ingest script still needs no event loop. See [`3B-ASYNC.md`](../runs/3B-ASYNC.md).
>
> **What is NOT yet verified, recorded by row 3c after an adversarial review round.** B2's concrete blocker was that a sync adapter *cannot share beacon's transaction*, beacon's data layer being `sqlalchemy.ext.asyncio.AsyncSession`. What landed accepts an already-open `psycopg.AsyncConnection` (D-A11). **Nothing in this package references SQLAlchemy, and nothing demonstrates that a raw `psycopg` connection taken from inside a live `AsyncSession` transaction can be handed to `AsyncPostgresAdapter` and actually share that transaction.** That is the literal scenario option 2 was rejected over, and it is 2B's first integration step, not this package's — but "B2 is closed" should not be read as "transaction sharing with beacon is proven". It is not. **[Assumed]**, and the spike belongs to 2B before beacon depends on it.

**B3 — seven `TypeRecord` fields have no column; three of them must exist, and the cost is a three-column additive migration.**

| Field | Resolution | Cost |
|---|---|---|
| `namespace`, `kind` | adapter constants `"default"` / `"edge"` | none |
| `aliases` | `stores_aliases=False`, always `()` + a `why` | none — honest unknown |
| `predicates` | `indexes_membership=False`, always `()` — and this is *correct*: `INTERFACE.md` §9 records `work_link_types` as the one Tenshen vocabulary of eight that is genuinely a type list and not a predicate | none |
| `status` | **required.** `retire` is one of the calls; a backend that cannot express `retired` cannot serve it | **`status TEXT NOT NULL DEFAULT 'active'`** |
| `attributes` | `is_symmetric` and `inverse_label` project onto their existing columns both ways, so beacon's own reads keep working. Any *other* key has nowhere to go | **`attributes_json TEXT NOT NULL DEFAULT '{}'`** |
| `provenance` | `created_by` + `created_at` give two fields of it; `approved_by` — which §2.4 says is never null on an active type — has no home | **`provenance_json TEXT`** |

> **Verdict on B3: `work_link_types` serves as a third backend after a three-column additive migration and a two-column projection. That is one `ALTER TABLE`, one table, no rewrite** — which is what `ROADMAP.md` 2B asks for. It is not zero.

The projection is worth naming precisely: on read, `attributes = json.loads(attributes_json) | {"is_symmetric": row.is_symmetric, "inverse_label": row.inverse_label}`; on write, those two keys go back to their columns and the rest to the JSON. beacon's existing code reads `is_symmetric` from the column it always did.

**B4 — there is no proposal table, and one table is the price of review.**
`_create_type_from_ai` validates shape (snake_case name via `_TYPE_NAME_RE`, non-empty definition, no collision) and then persists. **[Observed]** There is no queue, no reviewer, no `proposed` state. `INTERFACE.md` §9 contortion 4 records this as structural; here it arrives as a missing table.

**Resolution: `stores_proposals=False` is conformant, and it forces `approval_policy="auto"` for that namespace.** `propose_type` returns a `TypeEntry` immediately with `approved_by="auto:classifier"` (exactly §5.4's auto path); `approve` and `reject` return `Refusal(reason="proposals_not_stored")`. Reusing `unknown_proposal` was considered and rejected — it would be a confident wrong answer where Rule U requires an honest one, so a new reason is introduced and flagged in §11.

**The finding, which is the valuable part:** a backend with no proposal storage **cannot have a review step**, and now the price of one is legible — *one table*. Whether to pay it is beacon's decision, and `INTERFACE.md` §9 already names the collision it runs into: `_create_type_from_ai`'s own comment names **Haiku** as the model whose output it normalises **[Observed]**, so under a strict `min_auto_approve_tier` Tenshen's current classifier would fail auto-approval. The interface is not bent for it, and neither is this package.

**B5 — no `last_used_at`, so `usage()` is half-blind. Confirms `INTERFACE.md` §9 contortion 2 at the storage layer.**
`bump_usage` maps to `usage_count = usage_count + 1` and nothing else. `get_usage` returns `count` set, `first_seen`/`last_seen` `None`, `timestamps_usage=False`, `why="work_link_types has no last_used_at column"`. Therefore `orphaned` is `None`, and the venture's rot sensor (`ROADMAP.md` kill row, *"Tenshen's own curated vocabulary rots anyway"*) cannot fire on this backend.
**Per the brief: noted as a known gap; not depended on.** The `last_used_at` column is a beacon change relayed separately to the beacon program by the supervisor. **Nothing in this package assumes it.** Test C14-02 asserts the honest `None`, and will keep passing unchanged if beacon ever adds the column — it is a test of the interface, not of beacon.

**B6 — no event table, so an override cannot be recorded — and is therefore refused.**
`stores_events=False` ⇒ `provenance().history == []` with a `why`. That collides directly with §5.9 (`force=True` *records the override in history*) and §5.10 (`acknowledge` is recorded).
**Resolution — the rule stated in §3.6: a destructive override that cannot be recorded is refused.** `retire(force=True)` and `merge_types(acknowledge=[…])` return `Refusal(reason="cannot_record_override")`. The backend stays conformant; the suite tests the refusal (C9-02, C10-08), not the capability.
**[Inferred]** this is the right trade: an unrecorded, unattributable destructive change is precisely what this registry exists to prevent, and a store that cannot keep an audit trail has not earned the right to be overridden.

**And one non-contortion worth more than several of the contortions.** `find_consumers` needs **no table at all**. `INTERFACE.md` §5.11 explicitly declines to specify how a consumer gets registered; a `ConfigConsumerSource` reading a checked-in file — `consumer_id`, `gate`, `on_unknown`, `owner`, `locator` — is a legitimate adapter implementation, and it is how beacon gains `consumers()` for the cost of one config file and the work of writing down its seven allowlists. `INTERFACE.md` §9 contortion 6 says it plainly: *the registration is the work; the call is trivial.* **This is the highest-value thing in the whole Tenshen path and it needs zero schema change.** (`register_consumer` against a read-only source returns `Refusal(reason="consumer_source_read_only")` rather than a silent no-op — C11-04, ruling R4.)

### 7.4 Tenshen verdict

> **Yes — as a third backend, with a three-column additive migration on one table, a config-backed consumer source needing no table, and an async protocol this package does not yet have.**
>
> **Nine of fifteen primitives serve as-is. Six contortions, recorded, none designed away. One of them (B2, async) is a blocker for `ROADMAP.md` #5 and belongs to this deliverable, not to beacon.**

Two of the six are the interface telling beacon something true about its own instrumentation rather than complaining about a field — B5 (no timestamps, so the rot sensor cannot fire) and B4 (no proposal table, so review costs exactly one table). Per `ROADMAP.md`'s rule of the ordering, those are the good outcomes.

### 7.5 Kill-criterion check — required, and not skipped

**The brief's stop condition:** *if the adapter protocol can only be satisfied by reproducing Tenshen's schema — i.e. the CMS backend would be Tenshen's tables with the names filed off — stop and report. That is the N=1 failure `VISION.md` §9 names.*

**Not tripped.** The test is mechanical, so here it is mechanically:

1. **Table count.** The reference schema is **nine tables** (the seven in §4.1, plus `oo_attr_schema` and `oo_attr_observed` from §5). Tenshen's is **one**. If the protocol were Tenshen's schema renamed, those numbers would match.
2. **Primitive fit.** Tenshen's table serves **9 of 15** primitives; six need additive columns or a declared-`False` capability. A protocol shaped around that table would score 15 of 15.
3. **Which columns are load-bearing.** The columns the **CMS** data forces and Tenshen does not have — `kind` (because `value_set` had to exist, `INTERFACE.md` §10.1), `attributes` *with a schema* (because the A–L ordering has nowhere else to live, §5.1), `evidence`/`Citation` inside `provenance_json` (0.5 consequence 3), and the whole `oo_proposal` table (because the proposal is not the decision) — account for **more than half the reference schema by column count**. Every one of them is dead weight from Tenshen's point of view.
4. **The direction of the two protocol amendments made during the design tests.** `owns_schema` (B1) was adopted on the enterprise-DBA case and only *surfaced* by Tenshen; `stores_aliases` (B3) was added as an honesty flag, not as an accommodation. Neither changed a shape to fit `work_link_types`.

**The protocol is CMS-shaped, and Tenshen is a partial fit that has to pay to join.** That is the opposite of the kill criterion.

---

## 8. The CMS design test for #2 — the 0.5 sample through the adapter into SQLite

### 8.1 What "loads" means, precisely

**The registry stores types, not instances.** The 400 sample rows do **not** become 400 rows in `oo_type`. What lands is:

- the **vocabulary** derived from the sample — eight `TypeEntry` rows;
- the **instance counts**, in `oo_usage`, via `record_use` — which is what `UsageReport.count` is for, and what `INTERFACE.md` §8's worked entry shows (`usage=UsageReport(count=14627, …)`).

Stating this is not pedantry: reading "the sample loads through the adapter" as "400 citations become types" is the T3/T6 failure the ground truth predicted, committed by the test harness instead of by a model.

### 8.2 Expected row counts, from the pre-registered ground truth

Sample: `sample_state.csv`, the first 400 Montana rows of `NH_HealthCitations_Aug2026.csv` (CMS Provider Data Catalog, downloaded 2026-08-28). Ground truth frozen in [`0.5-ground-truth-PREREGISTERED.md`](../findings/0.5-ground-truth-PREREGISTERED.md) as `093f102`, before any proposal was generated.

| `kind` | `name` | rows in `oo_type` | `oo_usage.count` | source of the count |
|---|---|---|---|---|
| `entity` | `facility` | 1 | **10** | pre-registered, test file **[Observed]** |
| `entity` | `survey` | 1 | **69** | pre-registered, test file **[Observed]** |
| `entity` | `citation` | 1 | **400** | pre-registered, test file **[Observed]** |
| `entity` | `deficiency_tag` | 1 | **92** | T5, test file — *92 tags, 0 with more than one description* **[Observed]** |
| `value_set` | `deficiency_corrected_status` | 1 | **4** distinct values present (**6** full-file) | T1 **[Observed]** |
| `value_set` | `scope_severity_code` | 1 | **7** distinct codes present (A–L declared) | **[Inferred]** — see the caution below |
| `edge` | `issued_during` | 1 | **400** (citation → survey) | **[Inferred]** from the 400-row grain |
| `edge` | `conducted_at` | 1 | **69** (survey → facility) | **[Inferred]** from the survey count |

**Totals: 8 rows in `oo_type`, 8 in `oo_usage`, 8 in `oo_proposal`, ≥16 in `oo_event`** (a `proposed` and an `approved` per type), and 0 in `oo_consumer` — nothing in a CSV registers a consumer, and `consumers()` correctly reports `known: 0, complete: False`.

**Caution on the one [Inferred] count.** The seven severity codes present in the sample (B, C, D, E, F, G, J) come from [`0.5-RESULTS.md`](../findings/0.5-RESULTS.md)'s quotation of run **D**, which is the run that got the *ordering* backwards. The letter list itself was not among the two claims verified as errors, but it was also not independently counted. **The contract test must compute this number from the sample rather than assert it**, and record it — grading against a number taken from an unverified quotation is exactly the moved-target failure the pre-registration exists to prevent. The four `[Observed]` counts are asserted; this one is computed and reported.

### 8.3 What the CMS path exercises beyond counts

| Behaviour | Why it is here |
|---|---|
| `resolve_type("location", …)` ⇒ `not_a_type` / `redundant_projection` | **[Observed]** T3: `Location` is exactly rebuilt from four columns in 419,428 of 419,479 rows and **400 of 400** in the sample. Under a three-outcome surface this returns `None`, which reads as *go propose it* — the registry handing the pollution machine its first type. C3-08. |
| `resolve_type("processing_date", …)` ⇒ `not_a_type` / `export_artefact` | **[Observed]** T7: single-valued (`2026-08-01`) across the file. C3-09. |
| the severity proposal at `tier="haiku"` with `evidence=[]` ⇒ `Refusal("tier_below_auto_approve_policy")` | 0.5's worst result, made operational. C5-03. |
| `scope_severity_code` carries an `external_doc` `Citation` | 0.5 consequence 3 — the inversion was caught by reading CMS documentation, not by inspecting data. C13-04. |
| `deficiency_corrected_status` has six values, none a yes/no | T1. C13-03. |
| `deficiency_tag` is its own entity, description as **its** property | T5, and the fourth entity the Opus run added that 0.5 recorded as **better than the ground truth**. |
| under `enforce`, `scope_severity_code` without a declared `ordering` is refused | §5.6/C15-06 — the reason the attribute-schema mechanism exists at all |

### 8.4 A reproducibility gap, recorded

**[Observed]** the 400-row `sample_state.csv` is **not in this repository**, and `docs/tools/make_sample.py` does not produce it: that script takes a **seeded 300-row reservoir sample** of the full national file and writes `sample_300.csv`. The 400-row contiguous Montana file that 0.5 actually used is described in the ground truth but not checked in, and `nh_full.csv` (165 MB) is not either.

Standing constraint 0 argues *for* fixing this, not against: the data is public CMS data, and *"a test that cannot be run on public data is a test this project does not run."*

**Task for deliverable #3:** check the 400-row public sample in at `open_ontology/contract/fixtures/cms_sample_400.csv` (~80 KB), and add a `make_sample_state.py` that regenerates it from the public file so the provenance is checkable. Until it exists, the C13 group is `skipif`-gated on the fixture and **the CMS design test is therefore not yet runnable — it is specified, not passing.** Said plainly so nobody reads §8.2 as a result.

> **DONE, deliverable #3, 2026-08-28.** The fixture is checked in (**152,927 bytes**, not ~80 KB — the `Deficiency Description` column is long) and `tools/make_sample_state.py` regenerates it. The source file re-downloaded that day is **165,336,194 bytes, byte-for-byte the size the ground truth records**, so the fixture is the sample 0.5 actually cut. The C13 group runs and §8.2 is now a result: every [Observed] count matches, and the one [Inferred] count was **computed** — 7 distinct severity codes, B C D E F G J — rather than asserted against run D's quotation. See [`2A-RUN.md`](../runs/2A-RUN.md) §3.

### 8.5 CMS verdict

> **The vocabulary loads: 8 type rows, 8 usage rows, 0 consumers, on SQLite with zero configuration and no dependencies. The two `value_set` entries are the reason the attribute-schema mechanism in §5 exists, and `not_a_type` is what stops `location` becoming type #9.**
>
> **Not yet executed — the 400-row fixture is not in the repo (§8.4). Specified, gated, and honest about which of it is [Observed] and which is [Inferred].**

---

## 8b. The NYC Open Data design test for #2 — three agencies through the adapter

*Added by roadmap row 3c, 2026-08-28 — the third use-case fixture (`docs/USE-CASES.md` UC3), run against v0 retroactively per standing constraint 7. The interface half is [`INTERFACE.md`](INTERFACE.md) §10b; this half asks only what §3–§6 have to answer.*

**The subject.** Three NYC Open Data datasets, three agencies, one shared word meaning three unrelated things: `uvpi-gqnh` (DPR, 683,788 rows, `status` = a tree is `Alive`/`Stump`/`Dead`), `erm2-nwe9` (OTI/311, 22,283,935 rows, `status` = a request's workflow state, eight values), `693u-uax6` (DOT, 15,598 rows, `status` = a meter is `Active`/`Inactive`/null/`active`). Evidence and counts: [`findings/3C-VALIDATION.md`](../findings/3C-VALIDATION.md).

**The question §3 has to answer:** does a protocol designed around one flat CMS export and one single-namespace Tenshen table carry *many* namespaces without contortion?

### 8b.1 The protocol carries it, and this is the least surprising section in the document

**[Observed]** against both reference backends:

| Concern | Where it lands | Verdict |
|---|---|---|
| Three `status` rows, one word | `oo_type` PRIMARY KEY `(namespace, kind, name)` — **G1 is already scoped** (§3.5, §4.1) | ✅ no change |
| Registering the second and third without collision | `put_type(expect_absent=True)` raises only within a namespace | ✅ **now tested — C0-07** |
| A city-wide census | `TypeQuery.namespace: str \| None = None`, the one nullable scope in the protocol | ✅ **now tested — C6-07** |
| Per-agency value sets | `TypeRecord.attributes` + `attr_schema_version`, one row each | ✅ no change |
| Per-agency *validation* of those value sets | `AttributeSchema(namespace, kind, version)` — §5.2 keys the schema on the namespace | ✅ **and this is the strongest UC3 result in the package** |

**The attribute mechanism was designed for CMS and it is what UC3 needs.** §5.1 justifies §5 on the A–L severity ordering — a CMS argument. UC3 exercises the same mechanism on a different axis: **[Observed]** a schema registered for `("oti_311", "value_set")` requiring both `values` and `unknown_encodings` refuses `Refusal(reason="attributes_schema_violation", detail={"violations": ["unknown_encodings:required field missing"], …})`, while `("dpr", "value_set")` requiring only `values` accepts DPR's row unchanged — in the same store, in the same process.

That matters because B's `status` and `borough` each carry **two** spellings of unknown (`Unspecified` and an absent field) and A's carry none. A deployment can therefore *require the publisher who has unknowns to declare them* without imposing it on the publisher who does not. **Per-namespace schema versioning was not designed for this; it falls out of keying on `(namespace, kind)`, and UC3 is the first thing to use it.**

### 8b.2 The gap UC3 found in the suite, and it is closed here

**[Observed]** before this row, across all 109 contract tests, **two namespaces appeared in exactly one test** — `C10-04`, which asserts the `cross_namespace_merge` **refusal**. Nothing asserted the coexistence that refusal presupposes: that the store will hold two same-named rows, keep them apart, and hand each back. A backend could have passed the whole suite while silently letting the second publisher's `put_type` collide with the first's, and only `C10-04` — which never writes a second row it then reads back — would have been in the area.

**Two tests, added under §6.2's enumeration rules with `test_manifest.py` updated (109 → 111):**

- **`C0-07`** — *G1's key is scoped.* Three `status` rows in three namespaces, all `expect_absent=True`, all retrievable with their own definitions and attributes intact; a fourth write of the first row still raises `AlreadyExists`; `find_types(TypeQuery(namespace=None))` returns all three. **This is the storage guarantee `INTERFACE.md` §2.6's answer to mechanism 4 actually rests on**, and it was the one half of G1 nothing checked.
- **`C6-07`** — *the census spans namespaces and a scoped listing says it did not.* `list_types(namespace=None)` returns three `status` rows with three different definitions and `complete=True`; `list_types(namespace="dot")` returns one and **`complete=False` with a `why_incomplete` naming the namespace**. A scoped listing that reported `complete=True` would tell a reader the word is used once when it is used three times.

Both are capability-honest in §6.1's sense — they assert shapes and honest incompleteness, never a value a backend might legitimately not have — and both pass on SQLite and Postgres in one run.

### 8b.3 The two contortions

**B7 — `find_consumers` and `attribute_census` are single-namespace, so the ingestion-shaped reader must ask N times.**
**[Observed]** `find_consumers(namespace: str, …)` (§3.4 primitive 11) and `Registry.attribute_census(namespace: str = "default", …)` (§5.5) both take a required scalar namespace; only `TypeQuery.namespace` is nullable. UC3's actual consumer — a Phase 3 ingestion job landing three agencies — is one code path reading three namespaces, and it must register itself three times and read three censuses to see itself.

**Not fixed.** The change is one nullable parameter on each, and it is not free: `find_consumers` returning rows from every namespace makes `ConsumerReport` ambiguous about which scope it answered for, and §5.1's `complete: False` already carries all the honesty the report has. **Recorded so the cost is legible when #4 or Phase 3 asks for it.** The accumulation worry §5.5 exists to answer is *per-namespace* accumulation, which the census does answer; what it cannot answer is *"is `values` declared inconsistently across the city?"*

**B8 — the deterministic resolver's `not_a_type` rules are a CMS lookup table, and `C3-08` pins them.**
This is the sharp one. §2.6 states the rule that **"no contract test may pass or fail because of resolver quality"** — the suite asserts outcomes and shapes, never scores. `C3-08` and `C3-09` do not keep that promise: they assert a specific `not_a_type` **outcome** for two specific candidates, which only the shipped `DeterministicResolver` produces.

**[Observed]**, and it is the same pathology in both cases — a `location` column exactly rebuilt from the columns beside it:

```python
resolve_type("location", ctx(sibling_columns=("Provider Address","City/Town","State","ZIP Code")))
# -> not_a_type / redundant_projection          <- CMS. C3-08 passes.

resolve_type("location", ctx(sibling_columns=("latitude","longitude")))
# -> proposal, "nothing in the vocabulary fits 'location'"    <- NYC. Nothing catches it.
```

**[Observed]** in B and C, `location` is a GeoJSON `Point` whose coordinates equal `(longitude, latitude)` in **50 of 50 sampled rows each, in two agencies independently** — the CMS `Location` finding (T3, 419,428 of 419,479 rows) reproduced in a different government body's data. `_resolve._PROJECTION_FAMILIES["location"]` enumerates postal-address parts and contains no coordinate name, so the geographic flavour walks straight past. `borocode` — 1:1 onto `boroname` over the sample — is likewise returned as a `proposal`.

**Two things are true and both are recorded.** (1) Per §2.6 this is resolver quality, the deterministic resolver is explicitly *not good enough for production*, and adding `latitude`/`longitude`/`lat`/`long` to a lookup table would be fitting the table to the second dataset the way it was already fitted to the first. (2) `C3-08` and `C3-09` are nevertheless **conformance tests that a backend cannot fail and a resolver can** — so a deployment that ships its own resolver, which §2.6 says is the production path, fails the suite that defines conformance for reasons that have nothing to do with storage.

**And there is a second instance, worse than the first** *(added by row 3c after an adversarial review round)*. `C4-06`'s `unverified_semantics` behaviour is driven by a hardcoded keyword list — `_DOMAIN_SEMANTIC_WORDS` in `registry.py`, holding literals like `"immediate jeopardy"`, `"severity"`, `"higher letters"` — read by a module function that `propose_type` calls **directly**. It is not behind the `Resolver` seam at all. So where `C3-08`/`C3-09` at least fail through a component §2.6 says you may replace, **`C4-06` cannot be satisfied by supplying `Registry(adapter, resolver=MyModelResolver())` — the production path §2.6 itself names — because the heuristic is baked into the façade.** A third-party backend with its own resolver still fails a mandatory conformance test for a reason that is neither storage nor its resolver. This is deviation D-6's keyword rule (`INTERFACE.md` §2.8) meeting §2.6's rule, and the collision was not previously recorded anywhere.

> **`C4-06`'s share of this fix is cosmetic, and saying so is the honest part** *(recorded row 3c, after a fourth review round on this document)*. The `resolver_dependent` marker skips a test when the caller supplies their own `Resolver`. For `C3-08`/`C3-09` that is a real remedy: the outcome comes from `self.resolver.classify()`, so a deployment's resolver genuinely determines it. **`C4-06`'s does not touch the resolver at all** — `_asserts_domain_semantic` is a module function `propose_type` calls directly — so supplying a resolver changes nothing about whether it would pass, and the defect B8 names for it is *relabelled, not addressed*. The exemption is still right (a third-party backend should not fail a test it cannot influence), but **the only real fix is moving the domain-semantic judgement behind the `Resolver` seam**, which is the v1 item below. Recorded here rather than bundled silently with the other two.

**Recommendation, and it was applied** *(row 3c, after the finding recurred in two consecutive review rounds — see [`../findings/3C-VALIDATION.md`](../findings/3C-VALIDATION.md) §6, question **Q4**, whose recommendation was applied and which the supervisor may reverse)*. The three carry a `resolver_dependent` marker: **binding for the two reference backends, skipped with a reason for a foreign adapter** (§2.6, §6.1). That is the narrower of the two options, and it was chosen because it changes nothing about this repository's own gate — §6.1 already requires both reference backends — while removing a promise the suite could not keep to anyone else.

**What was deliberately NOT done:** widening `_PROJECTION_FAMILIES` to include `latitude`/`longitude`. That fits the table to the second dataset the way it was already fitted to the first, and it would make the *next* use case's version of this finding harder to see rather than easier. Moving the domain-semantic judgement behind `Resolver` is the tidier long-run answer and stays a v1 item.

### 8b.4 NYC verdict

> **The protocol carries three agencies with no change to the fifteen primitives, no change to the table shapes, and no change to `Capabilities`.** Scoping was already in the primary key; per-namespace attribute schemas already worked and are the mechanism UC3 most needs. **Two contortions (B7, B8), neither designed away.**
>
> **The suite gained two tests it should have had since #2** — `C0-07` and `C6-07`, and four more from the review rounds, 109 → 115 — because UC3 found that the coexistence half of G1 and the cross-namespace half of `list_types` were both unasserted. Per `ROADMAP.md`'s rule of the ordering, a use case that finds a missing test rather than a missing feature is the good outcome.
>
> **Kill-criterion check (§7.5), re-run against a third fixture: still not tripped.** Nothing about NYC's shape is in the schema. The columns UC3 leans on hardest — `namespace` in the primary key, `attr_schema_version`, `oo_attr_schema` keyed on `(namespace, kind)` — were all put there by CMS and Tenshen, before this dataset existed.

### 8b.5 What the adversarial review rounds added — six more tests, 109 → 115

The review loop that follows a design test (standing constraint 7) found two more places where a test asserted less than the document claimed. Both are recorded here rather than in a run record, because both changed the conformance definition.

**`C0-08` — G1 and G2, raced.** §3.5 says G1 *"must raise from a **database constraint**"* and that a read-then-write check *"is not sufficient"*, and that G2 is what turns `already_decided` from a race into an idempotent refusal. Every test of both — `C0-02`, `C0-07`, `C5-11` — called the primitives **sequentially on one thread**, which a check-then-insert implementation passes exactly as happily as a real constraint does. The only genuine race in the repository lived in the async tree and was marked `nonbinding`, outside conformance, so **the sync suite that is the actual 2B gate contained no test of its own two non-negotiable capabilities under the only conditions that distinguish them.**

`C0-08` races two adapter instances over one store: one absent name written twice, and one proposal approved twice. **It was verified to bite before it was believed:** a wrapper implementing `expect_absent` as check-then-insert produces **two winners** and fails, while both constraint-backed backends produce one winner and one `AlreadyExists`. The async counterpart was promoted from `nonbinding` to this id and given the G1 half as well, so both stacks assert it.

> **One generation exception, and it is deliberate.** A thread race has no mechanical async form — the async equivalent of two threads is `asyncio.gather` over two coroutines, a *different mechanism* rather than a token substitution. `tools/unasync.py` therefore excludes **`contract/test_c0_backend_local.py`** by name (`HAND_WRITTEN_ASYNC`), and **`aio/contract/test_c0_backend_local.py`** is maintained by hand, the way the driver-level `close()` methods are (`3B-ASYNC.md` D-A12). It holds the two contract tests that **build backends directly** rather than taking the `adapter` fixture — `C0-08`'s thread race and `C0-09`'s `owns_schema=False` construction, whose async form is `await AsyncSQLiteAdapter.open(...)` (D-A1). **It is the only contract module in the suite that is not generated**, and the exclusion is a named constant so it cannot grow quietly. *(Filenames corrected by row 3c: the module was renamed from `test_c0_concurrency.py` when `C0-09` was folded in, and this paragraph did not follow.)*

**`C15-07` — one schema per kind cannot serve both CMS `value_set`s.** §5.6 now records the limitation; `C15-07` asserts both horns of it. It is not a bug report against a backend — every backend behaves this way, because the key is in the schema, not in the storage — and it is pinned so that a later ruling to key schemas per `(namespace, kind, name)` has a test that changes when the answer does.

**`C0-09` — `owns_schema=False` is verify-only.** §9.3 says that when the schema belongs to the host application — beacon's Alembic, or an enterprise Postgres where the DBA owns DDL — `migrate()` checks the columns it needs, raises `SchemaMismatch` naming what is missing, and **never issues DDL against a schema it does not own**. Both reference backends implemented it; nothing asserted it. It is **B1, the first contortion of the Tenshen design test**, and §7.3 justifies it on the enterprise-DBA posture being the reference deployment — so the suite was silent about a path both of its own worked examples take.

**`C5-12` — `proposals_not_stored`, and the claim that a proposal-less backend conforms.** This one started as a coverage gap and turned into the largest single finding of the loop.

§3.2 says **"Every other flag may be `False` and the backend can still be conformant"**, and §7.4's verdict says a `stores_proposals=False` backend — Tenshen's — conforms *"as a third backend"*. **[Observed] both were false: 26 of the 113 tests failed against such a backend**, and four of them crashed outright with `AttributeError: 'TypeEntry' object has no attribute 'id'`. Two distinct causes, neither previously recorded:

1. **The suite ran every backend under `approval_policy="review"`**, which §7.3 B4 says a proposal-less backend cannot serve — so `propose_type` returned a `Refusal` where the harness expected a `Proposal`. The suite now defaults such a backend to `approval_policy="auto"`, because B4 says the flag *forces* it.
2. **Test harnesses assumed `propose_type` returns a `Proposal`.** Where the capability is the test's *subject*, the test asserts the honest answer (that is §6.1 rule 1, unchanged, and `C5-12` is now that test). Where it is only *scaffolding* — every test that must have a proposal before it can approve one — the test is skipped by a new `requires_capability` marker, with a reason naming the flag and quoting the backend's own `why`.

**[Observed] result:** a `stores_proposals=False` backend now runs the suite to **`96 passed, 25 skipped, 1 deselected`, exit 0**, and the two reference backends still execute all 115 with nothing skipped. §3.2's sentence and §7.4's verdict are true for the first time.

> **What this did NOT close, recorded rather than half-fixed.** A backend declining **several** optional capabilities at once still fails, and the residue is real: with `stores_events=False` an acknowledged merge is correctly refused (`cannot_record_override`, §3.6) so `C16`'s fixture cannot build the store it inspects, and with `indexes_membership=False` the `C10` group's consumer-set guards all degrade to `no_consumer_evidence` rather than the specific refusals they assert. **[Observed]**, on a double declining all seven optional flags. Closing it may require deciding what conformance *means* for a backend that can never merge and can never index — which is a ruling, not a test fix. **Q7** in [`../findings/3C-VALIDATION.md`](../findings/3C-VALIDATION.md) §6.

---

## 9. Versioning of the store

### 9.1 The mechanism

`oo_schema_version` holds one row: an integer `version`, when it was applied, and a note. Migrations are numbered SQL files, `backends/migrations/<backend>/NNNN_<slug>.sql`, applied strictly in order. **Each migration and the version-row update happen in one transaction** (C0-05) — a half-applied migration would leave a store whose version is a lie.

**Forward-only. v0 ships no down-migrations and will not.** A rollback is restore-from-backup, which is a real operation people already have, rather than a reverse-DDL script nobody tests.

`migrate()` is idempotent: at the expected version it is a no-op returning that version.

### 9.2 A store from the future is refused, never downgraded

If `oo_schema_version.version` is **higher** than the package knows, `migrate()` raises `StoreVersionUnknown` and `Registry` will not open the store. It does not "work anyway" against columns it does not understand — a newer schema may have moved a meaning, and reading it under old assumptions is how a registry starts asserting things that are not true.

### 9.3 A store whose schema someone else owns

`Capabilities.owns_schema=False` (§7, B1) makes `migrate()` **verify-only**: it checks the columns the adapter needs and raises `SchemaMismatch` naming what is missing, and issues no DDL. This covers beacon's Alembic-owned table and the enterprise Postgres deployment where the DBA owns DDL and the application role has no `CREATE`.

### 9.4 v0 stores may be dropped rather than migrated — stated explicitly

**Standing constraint 4:** *an interface labelled unstable is cheap to replace; one two codebases quietly assume is permanent is not.* The same applies to the store.

> **A `v0` store may be dropped and rebuilt rather than migrated. This package promises no migration path between v0 schema revisions.** It will ship one when it is cheap and it will not apologise when it does not. Anything in a v0 store that matters must be reproducible from its source.

The practical form of that promise: **`Registry` refuses to open a store it does not understand** (§9.2), so the failure mode is a loud refusal at startup, never a quiet misread.

### 9.5 Two version axes, not one

Do not conflate them:

| Axis | Where | Meaning |
|---|---|---|
| **store schema version** | `oo_schema_version.version` | the shape of the tables — this section |
| **attribute schema version** | `oo_type.attr_schema_version`, `oo_attr_schema.version` | the shape of a `kind`'s `attributes` **content** — §5 |

The first is forward-only and may be dropped. The second is never applied backwards to existing rows at all (§5.4). They move independently.

---

## 10. Exit criteria — the brief's, checked

| Criterion (verbatim from the brief) | Where |
|---|---|
| *every adapter primitive has a signature, data shape and uncertainty behaviour* | §3.4 — fifteen primitives, each with all three; the uniform uncertainty rule stated once at the head |
| *both backends have table shapes* | §4.1 (shared logical shape, seven tables; two more in §5), §4.3 (SQLite dialect), §4.4 (Postgres dialect) |
| *the `attributes` mechanism is decided or explicitly declared a v0 gap* | §5 — **decided**: per-kind versioned schemas, three modes, default `off` to keep #1's contract, plus an unconditional census; §5.4 states the behaviour for entries written under an older schema |
| *the contract-test list covers every §5 call and every §5 refusal* | §6.2 (119 tests, seventeen groups — 109 at #3, ten added by row 3c) and §6.3 (the refusal-by-refusal coverage table — none untested) |
| *both design tests are recorded with their contortions* | §7 (Tenshen: six contortions, verdict, kill-criterion check) and §8 (CMS: counts, verdict, and the reproducibility gap) |
| *header carries `v0` / `unstable` / the assumptions line* | header, lines 3–5 |
| **Kill criterion** — *the adapter can only be satisfied by reproducing Tenshen's schema* | §7.5 — **not tripped**, on four mechanical grounds |

---

## 11. Open items, and what would change this

> **Deliverable #3 landed 2026-08-28.** The whole suite is green on both reference backends in one run (`229 passed`) and the CMS design test executes. Fourteen deviations are recorded in [`2A-RUN.md`](../runs/2A-RUN.md) §4; the one that wanted a founder ruling was **D-1** — §3.4 primitive 10 and `C11-04` require a `Refusal` for a read-only consumer source, and ruling R3's closed fourteen had no honest value for it. **Resolved 2026-08-28 by ruling R4**, which added `consumer_source_read_only` as the fifteenth value of `INTERFACE.md` §5.12 in the same change that made the registry return it. Item 1 below (async) was answered by ruling **R1** as new row 3b, **which landed 2026-08-28** ([`3B-ASYNC.md`](../runs/3B-ASYNC.md), `267 passed`); items 2 and 3 by **R2** and **R3**.

### 11.1 Raised for the founder — all three **ruled**

*(Rewritten by row 3c, 2026-08-28, after an adversarial review round. All three were answered on 2026-08-28 and the note above said so, while the items themselves still read "Ruling wanted" — **a ruling ledger that had drifted out of sync with its own rulings**, in the document of a project whose thesis is that unmaintained statements are the rot mechanism. The questions are kept, because what was asked is worth reading; the answers are now attached to them.)*

1. **The async protocol is missing, and Phase 2B cannot land without it** (§7, B2). beacon's data layer is `AsyncSession` throughout; a sync adapter cannot share its transaction, and driving one from a thread is not safe. *Asked: is `AsyncStorageAdapter` / `AsyncRegistry` inside deliverable #3's scope, or a separate deliverable between #3 and #5?*
   → **Ruled R1: a separate row, 3b, after #3 and before #5. Landed 2026-08-28** ([`3B-ASYNC.md`](../runs/3B-ASYNC.md)) — generated from the sync source, not forked. The one part that remains **[Assumed]** is SQLAlchemy transaction sharing; see the note in §7 B2.
2. **`attribute_census` is a method beyond the calls `INTERFACE.md` §5 enumerates** (§5.5) — the only one this document adds. *Asked: absorb it into #1's surface, or keep it package-local?*
   → **Ruled R2: package-local, outside the conformance definition.** `C15-02` is therefore `nonbinding` permanently, not provisionally — and since row 3c the marker **actually exempts it** from a conformance verdict, which registering the marker never did (§6.1).
3. **Three new `Refusal.reason` values** are introduced here — `proposals_not_stored`, `cannot_record_override`, `attributes_schema_violation` (§3.6). *Asked: amend #1's list, or state that `reason` is an open vocabulary?*
   → **Ruled R3: amend #1. `Refusal.reason` is a CLOSED vocabulary**, enumerated in `INTERFACE.md` §5.12, and adding a value requires amending that section in the same change. **Ruling R4** later added a fifteenth, `consumer_source_read_only`, by exactly that route.

**Open items that remain open are not here.** They are the six in [`../findings/3C-VALIDATION.md`](../findings/3C-VALIDATION.md) §6 (Q1–Q6), of which two are this document's: per-kind attribute schemas (**Q5**, open) and `C3-08`/`C3-09`/`C4-06` versus §2.6 (**Q4** — whose recommendation was *applied* by row 3c after recurring in two consecutive review rounds, so the ruling wanted there is confirm-or-revert rather than decide).

### 11.2 Recorded for #1's next revision, no ruling needed

- ~~**The call count.**~~ **Corrected by row 3c**: `INTERFACE.md` §5.10, §12 and §13 now say **thirteen**, which is what enumerating §5.1–§5.11 gives (§2.2).
- **`INTERFACE.md` §2.1 says the registry never reads `attributes`.** §5 of this document makes reading them possible but off by default, so an untouched deployment matches §2.1 exactly. If #1 adopts the mechanism, that sentence needs a clause.
- **`INTERFACE.md` §9 does not name the `kind` of a `work_link_types` row.** This document determines `kind="edge"` (§7.1) from §2.2's definition.

### 11.2b Recorded by roadmap row 3c (the UC3 validation pass), 2026-08-28

§8b runs the NYC Open Data fixture against this document. The protocol needed **no change** — scoping was already in G1's key and attribute schemas were already keyed on `(namespace, kind)` — and the suite gained the two tests §8b.2 describes (109 → 111). Two contortions are open:

- **B7 — `find_consumers` and `attribute_census` are single-namespace** (§8b.3). Only `TypeQuery.namespace` is nullable, so the ingestion-shaped reader that UC3 describes must register itself once per agency and read one census per agency. The fix is one nullable parameter on each and it is not free — a cross-namespace `find_consumers` makes `ConsumerReport` ambiguous about which scope it answered for.
- **B8 — `C3-08` and `C3-09` assert resolver behaviour, which §2.6 says no contract test may do** (§8b.3). The same `location`-rebuilt-from-its-parts pathology returns `not_a_type/redundant_projection` on CMS's postal-address sibling set and `proposal` on NYC's `latitude`/`longitude` one, because `_PROJECTION_FAMILIES` is a lookup table fitted to the first dataset. A deployment shipping its own resolver — which §2.6 calls the production path — therefore fails the suite that defines conformance for a non-storage reason. **Ruling wanted:** mark the two non-binding the way `C15-02` is, or move them out of the conformance definition. See [`findings/3C-VALIDATION.md`](../findings/3C-VALIDATION.md) §6.

### 11.3 Weaknesses of this design, named now so they are not discovered later

- **Attribute schemas have no proposal→approval loop.** They are deployment configuration, not vocabulary (§5.2). A deployment can therefore change how `value_set` attributes validate with no review — which is mechanism **1**, one level down, in the mechanism built to answer §11's worry about mechanism 1. The dogfooding fix (register a schema as a `TypeEntry`) was rejected for a good reason and the cost is real.
- **`list_types(orphaned=)` and `list_types(unverified_semantics=)` are O(types)** on every backend (§3.3), because pushing them into the adapter would put policy in the backend.
- **The deterministic default resolver is not good enough for production** and is not meant to be (§2.6). Every `resolve_type` quality question is a resolver question, and no contract test can catch a bad one.
- **`ConsumerReport.complete` is `False` forever**, so `merge_types`' consumer-set guard operates on known sets only — `INTERFACE.md` §5.10 already takes the weaker rule, and this package cannot strengthen it.

### 11.4 What would change this document

| If… | Then |
|---|---|
| the founder rules **async is a separate deliverable** | the ordering table gains a row between #3 and #5, and 2B's date moves |
| **A5 is reopened** (2A's contract tests stop being the 2B gate) | §6.1's conformance rule loses its authority; the suite becomes internal QA rather than a gate |
| **A4 lands *do-not-file*** (Q7a) | `usage()` becomes the venture's only rot sensor — and §7 B5 says beacon's backend **cannot supply it**, so `last_used_at` moves from *nice* to *load-bearing*, and the Tenshen backend stops being able to carry the core-bet experiment at all |
| **A1 is wrong** and semantic collision is dominant | `oo_type`'s primary key already carries `namespace`, so the schema survives; `merge_types` and its eight tests are deleted rather than guarded |
| the office reports **plain duplicate sprawl, no predicate structure** | `oo_type_predicate` becomes overhead rather than the load-bearing join, and C1/C2 (13 tests) shrink to a handful |
| a **second real backend** appears that cannot meet **G1** (an eventually-consistent store) | the conformance definition itself must change — G1 is currently non-negotiable, and that is a bet that the registry's scale never needs a store that cannot do it |
