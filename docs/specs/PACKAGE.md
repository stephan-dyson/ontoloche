# PACKAGE — the `ontoloche` package, its storage-adapter protocol, and the contract suite that defines conformance

**Version:** `v0` — **unstable.** Every module name, class name, primitive signature, table shape and test id here may change without a deprecation path. Standing constraint 4.
**Status:** Draft, 2026-08-28. Satisfies `ROADMAP.md` Phase 2 preparation. Deliverable **#2** of the Tenshen-rebuild ordering. **Deliverable #3 has since landed** — the package, both backends and the 113-test suite are real and green (§8.4, §8b.5, §11); the sections written before it say so where it matters. *(Header corrected by row 3c; it still read "No code yet".)*
**Assumptions:** *written against the 2026-08-28 assumptions; see docs/decisions/* — specifically [`decisions/2026-08-28-assumptions-in-lieu-of-office-answers.md`](../decisions/2026-08-28-assumptions-in-lieu-of-office-answers.md), assumptions **A1**, **A4** and ruling **A5**.
**Sits underneath:** [`INTERFACE.md`](INTERFACE.md) v0. Where this document and `INTERFACE.md` disagree, `INTERFACE.md` wins and the disagreement is recorded in §11 rather than resolved silently.
**Evidence inputs:** [`INTERFACE.md`](INTERFACE.md) (the calls, the refusals, the two design tests) · `0.5-RESULTS.md` and `0.5-ground-truth-PREREGISTERED.md` (the CMS entities and their pre-registered counts) · `beacon/src/beacon/models/work_link_type.py` and `.../services/work_link_service.py`, read-only on 2026-08-28 (the Tenshen design test) · `0.3-prior-art.md` (the Foundry import mapping the suite must test).
**Claim tags:** **[Observed]** seen directly · **[Inferred]** a reasonable read · **[Assumed]** believed, untested.

---

## 0. What this is, in four sentences

`INTERFACE.md` says what the registry *does*. This says what you `pip install`, what a storage backend must implement, and how you prove a backend is correct.

The load-bearing idea is one sentence: **the storage adapter is a typed record store that does not know what a proposal, an approval or a refusal is.** Everything in `INTERFACE.md` §5 that refuses, warns, scores or decides lives above the adapter; the adapter stores records, enforces exactly two guarantees, and — the part that makes two unlike backends possible — **declares in advance what it cannot do, so the registry can return an honest unknown instead of guessing.**

The contract suite is not a test of the package. **It is the definition of conformance:** a backend is conformant iff the whole suite passes against it. That suite is the 2B gate per **A5**.

---

## 1. Non-goals — one line each

- **No HTTP/API server.** A server is a *consumer* of `Registry`, never part of it; nothing in this package imports a web framework.
- **No relationships or edges.** `kind="edge"` rows are names, definitions, provenance and lifecycle only. Edge shape and edge instances are deliverable **#4, [`docs/specs/EDGES.md`](EDGES.md)** — **landed 2026-08-29**.
- **No ingestion or mapping.** Landed rows → typed entities is **Phase 3**; this package is handed a decided vocabulary, not a CSV.
- **No instance resolution.** *"I already know 38 of these facilities"* is entity resolution and belongs to **Phase 3 ingestion** (`INTERFACE.md` §10.3; `ROADMAP.md` Phase 3, supervisor's provisional assignment 2026-08-28, founder may move it). Mentioned once, here, and not designed.
- **No ORM is mandated** — see §2.5. The protocol is defined over dataclasses, so a third-party adapter *may* be written with one.
- **No async in v0** — and this is a real gap, not a preference. See §7 contortion **B2**; it blocks ROADMAP #5 and is escalated in §11. **Closed 2026-08-28 by ruling R1's row 3b**, which took option 3 below: `AsyncStorageAdapter` / `AsyncRegistry` alongside the sync ones, generated from them rather than forked ([`3B-ASYNC.md`](../runs/3B-ASYNC.md)).
- **No embeddings, no vector store, no model call.** `resolve_type`'s near-match scoring is a pluggable `Resolver`; v0 ships a deterministic default so the contract suite never depends on a model. See §2.6.
- **No auth, no multi-tenancy** beyond `namespace`; no UI; no CLI beyond a contract-suite runner.

---

## 2. Package shape

### 2.1 Distribution and module layout

Distribution name `ontoloche`; import name `ontoloche` — the two coincide since the 2026-08-30 rename (they were `open-ontology` / `open_ontology` before). **[Assumed]** the PyPI name is available; not checked, and not worth checking before #3.

```
ontoloche/
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
        __main__.py        # python -m ontoloche.contract --adapter pkg.mod:Class
        conftest.py        # the adapter_factory fixture, parametrised over backends
        test_*.py          # the suite (§6)
        fixtures/
            cms_sample_400.csv   # the 400-row public CMS sample (§8.4)
```

### 2.2 The public import surface

```python
from ontoloche import Registry
```

`Registry` is **one façade object** carrying the `INTERFACE.md` §5 calls as methods, with signatures identical to §5 minus the implicit `self`.

**Counting note — raised here, resolved in #1 by row 3c.** `INTERFACE.md` used to say "twelve calls". Enumerating §5.1–§5.11 yields **thirteen** functions: `consumers`, `predicates`, `resolve_type`, `propose_type`, `approve`, `reject`, `list_types`, `usage`, `provenance`, `retire`, `merge_types`, `register_consumer`, `record_use`. §5.5 defines two and §5.11 defines two. The façade exposes thirteen methods. `INTERFACE.md` §5.10, §12 and §13 now all say thirteen. **Fourteen since row 3e**, which added `reinstate` (`INTERFACE.md` §5.9b, ruling **R11**) — the first call added to that surface since v0, and the count is now checked mechanically by [`check_spec_drift.py`](../tools/check_spec_drift.py)'s `CALLS` tuple rather than restated in prose. *(Raised by this document at #2, corrected in #1 during row 3c after a fifth adversarial round — a two-line fix that had been carried as a known-wrong number through four deliverables.)*

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
| `ontoloche` (base) | — | SQLite is stdlib; the default backend must not cost a wheel |
| `ontoloche[postgres]` | `psycopg>=3.1,<4` | one driver per backend, no pool, no C extra by default |
| `ontoloche[contract]` | `pytest>=8` | the suite ships *inside* the package because it is the definition of conformance (§6) — a third-party backend must be able to run it |

**[Observed]**, PyPI metadata for `psycopg`, retrieved 2026-08-28: latest `3.3.4`, `requires_python >=3.10`, extras `c` / `binary` / `pool` / `test` / `dev` / `docs`. We depend on the plain wheel; deployments that want `psycopg[binary]` or `psycopg[c]` install it themselves. `psycopg2` is **not** supported — it is a different driver with a different parameter style, and supporting both doubles the SQL layer for no gain.

**No ORM is mandated. Stated and justified:**

1. **Size.** The adapter is fifteen primitives over seven tables (§4.1). An ORM's identity map, unit of work, lazy loading and relationship graph are all machinery for a problem this does not have.
2. **It would defeat the adapter.** The two backends differ in exactly the places an ORM abstracts badly — JSON storage (`TEXT` vs `jsonb`), timestamps (`TEXT` vs `timestamptz`), and the `already_decided` race (write lock vs `SELECT … FOR UPDATE`). Those differences are the adapter's *content*. Hiding them behind an ORM moves them somewhere nobody reads.
3. **It would make 2B worse.** beacon already maps `work_link_types` with SQLAlchemy. Mandating SQLAlchemy here means beacon's migration has to reconcile two `MetaData` objects over one table; raw SQL against the table beacon already owns is strictly less entangled. See §7.
4. **Constraint 2** (`ROADMAP.md`): do not build the general thing before the specific thing works. An ORM is generality bought before need.

**The protocol does not forbid one.** `StorageAdapter` is defined over dataclasses and Python values, never over rows or cursors. A third-party adapter — beacon's — is free to be an eighty-line SQLAlchemy shim. **That freedom is the point of having a protocol at all**, and §7 is where it gets tested.

### 2.5 What is *not* in the package, deliberately

- No logging configuration; the package logs to `logging.getLogger("ontoloche")` and configures nothing.
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
    stores_edges:              bool = False   # EDGES §6 — there is an edge store at all
    stores_edge_events:        bool = False   # append_event with an edge_id is durable
    indexes_edges_by_family:   bool = False   # a family filter need not scan the node's edges
    stores_edge_attributes:    bool = False   # an arbitrary edge payload survives a round trip
    stores_invocations:            bool = False  # ACTIONS §8 — there is an invocation store at all
    stores_invocation_events:      bool = False  # append_event with an invocation_id is durable
    indexes_invocations_by_family: bool = False  # a family-filtered read need not scan
    why: dict[str, str]            # one sentence per False flag — surfaced verbatim as Rule U's `why`
    transaction_scope: Literal["owned", "savepoint"] = "owned"   # who owns the commit. §3.5, R5
    attribute_projections: frozenset[str] = frozenset()          # keys owned as typed columns. §5.7
    edge_transaction_scope: Literal["owned", "savepoint"] = "owned"  # EDGES §6.2, R5 inherited
    edge_attribute_projections: frozenset[str] = frozenset()         # EDGES §6.3, U3's shape
    edge_store_shares_connection: bool = True                        # EDGES §6.2's binding rule
    action_transaction_scope: Literal["owned", "savepoint"] = "owned"  # ACTIONS §8.2, R5 again
    action_store_shares_connection: bool = True                        # ACTIONS §8.2's premise
```

> **The four edge flags default to `False`, and that is the load-bearing choice** *(row 4b, EDGES §6)*. An adapter written against the fifteen-primitive protocol has no edge store. Defaulting `stores_edges` to `True` would make every such adapter claim one, and the registry would then call `put_edge` on an object that does not have the method; defaulting it `False` makes every edge call on a pre-4b backend return `Refusal(reason="edge_store_absent")`, which is the true answer. They are ordinary members of `CAPABILITY_FLAGS` rather than a separate tuple, because `check_capability_matrix.py` declines one flag at a time off that tuple, `C0-01` requires a `why` off that tuple, and `DegradedAdapter` validates its kwargs against it — an edge flag living anywhere else is an edge flag none of those three reaches.
>
> **`C0-01`'s invariant has one carve-out, and it is stated rather than assumed.** When `stores_edges` is `False` the other three are **vacuous, not declined**: there is no edge store, so *"why do you not index edges by family?"* has no answer beyond the first sentence. Requiring three more would teach an adapter author to write sentences nobody reads, which is how a `why` dict stops being the mechanism this section says it is. `Capabilities.missing_why()` skips them in that one case and in no other.
>
> **`edge_transaction_scope` carries one binding rule, and it is checkable** (EDGES §6.2). When the edge store and the type store share a connection — `edge_store_shares_connection=True`, which is what both reference backends declare because `oo_edge` sits in the same schema as `oo_type` — the two scopes **MUST** be equal. An adapter declaring otherwise is claiming that half its writes are the host's to commit and half its own, on one transaction, which is not a thing that can be true. `Capabilities.scope_conflict()` returns the sentence or `None`, and `C17-25` binds it. When they are genuinely two connections the two may differ, and then **atomicity across the seam is gone** — approving an `equivalent_to` family and writing the first edge are no longer one transaction. Stated rather than papered over: a two-connection deployment does not get **G2** across the seam, and says so in `why["edge_transaction_scope"]`.

> **The three action flags default `False` for the same load-bearing reason, and the carve-out is the same one** *(row 6b, ACTIONS §8)*. An adapter written against the eighteen-primitive protocol has no invocation store; defaulting `stores_invocations` `True` would make every such adapter claim one and this package would call `put_invocation` on an object without the method. `Refusal(reason="action_store_absent")` is the true answer, and **never an empty report** — an empty invocation report reads as *"nothing has ever run"*, which is Rule U's forbidden empty in the one call a caller would believe. They are ordinary members of `CAPABILITY_FLAGS`, and when `stores_invocations` is `False` the other two are **vacuous rather than declined**, exactly as the three edge flags are — `Capabilities.missing_why()` now skips two groups and in no other case.
>
> **`action_transaction_scope` is the third store's declaration, and it makes `scope_conflict()` answer about TWO independent pairs** (ACTIONS §8.2). The binding rule is unchanged in shape: when the invocation store and the type store share a connection — `action_store_shares_connection=True`, which is what both reference backends declare because `oo_invocation` sits in the same schema as `oo_type` — the two scopes **MUST** be equal. Which pair the one returned sentence names when **both** conflict is unspecified; that is question **Q42**, ruled **R46** (record it, do not change a shipped method's signature for a case no backend has produced), and the edge pair is reported first.

**The `why` dict is the mechanism, not decoration.** When a flag is `False`, the registry does not invent an explanation; it surfaces the adapter's sentence. `usage("blocks")` on beacon's table returns `last_seen=None, orphaned=None, why="work_link_types has no last_used_at column"` — which is `INTERFACE.md` §9 contortion 2, reported by the system rather than discovered by a human.

**Two flags are not optional.** `enforces_unique_name=False` or `transactional=False` ⇒ **non-conformant**, full stop (§3.5). Every other flag may be `False` and the backend can still be conformant, because the suite asserts *honest unknowns*, not values. That single rule is what lets Tenshen's one-table registry be a third backend (§7).

> **Measured, not asserted** *(row 3c, 2026-08-29)*. That sentence was **false for six of the eight optional flags** for four deliverables: declining any one of `stores_events`, `stores_attributes`, `stores_aliases`, `indexes_membership`, `counts_usage` or `timestamps_usage` — **one at a time, nothing else degraded** — failed the suite outright, from 1 failure to 24. Two of those turned out to be defects in the *registry*, not the suite (§8b.5); the rest were tests using a capability as scaffolding for a scenario about something else, which now carry `requires_capability` and skip with a reason. [`docs/tools/check_capability_matrix.py`](../tools/check_capability_matrix.py) runs the whole suite against all nine declined configurations and prints the table; the contract suite runs it, `nonbinding`. **All nine now conform.** What it does *not* cover is several capabilities declined **at once** — that is question **Q7** and it is open.

**Invariant, tested (`C0-01`):** every `False` flag has a non-empty entry in `why` — and so does `transaction_scope="savepoint"`, which is not a bool but is the one declaration that changes what a *successful* return means (§3.5). *(Row 3d, [Observed]: both reference backends returned an **empty** `why` for `owns_schema=False`, because every fixture backend is `owns_schema=True` and the one test that built such a backend asserted `why.get("owns_schema") or True`. The first borrowed-connection adapter hit it on its first call. Fixed in the backends and the assertion given teeth — `C0-09`, `C0-12`.)*

> **`attribute_projections` is a declaration, not a flag either** *(row 3d, beacon finding **U3**)*. `stores_attributes` was **binary**, and that made one real backend undescribable: a host-owned store with pre-existing typed columns cannot say *"I store no arbitrary keys **and** I own two named ones faithfully"* — it had to claim `True` and lose the arbitrary ones silently, or claim `False` and disclaim keys it round-trips perfectly. `attribute_projections` names the keys the backend owns **as typed columns**; those round-trip through the column, not through the JSON blob. Everything else is unchanged: a key that is neither stored nor projected comes back **absent, with a `why`**. `Capabilities.stores_attribute(key)` and `.surviving_attributes(dict)` are the two derived answers a caller actually wants, so nobody has to re-derive the rule. §5.7, `C0-06`.

> **`transaction_scope` is a declaration, not a flag** *(row 3d, ruling **R5**)*. It is `Literal["owned","savepoint"]` rather than a `bool` because the two values are not "can" and "cannot": both are fully transactional, and what differs is **who issues the commit**. It is therefore not in `CAPABILITY_FLAGS` and not part of the two-non-negotiable rule; `transactional` stays REQUIRED `True` in both scopes.

### 3.3 The record shapes

Flat, frozen dataclasses. Every field is `str`, `int`, `bool`, `datetime`, `None`, or a JSON-serialisable `dict`/`list`. No nesting of interface objects.

> **These blocks are checked against the code** *(row 3d, beacon finding **U4**)*. `TypeRecord` had lost `retire_reason`, `retired_by`, `retired_at` and `successor` — four fields the landed dataclass has and this document, which is what a third-party adapter author builds from, did not. `INTERFACE.md`'s fifteen printed shapes were mechanically diffed against `types.py` from row 3c onward and this document's eleven were not, so the drift simply moved into the half nobody was checking. [`check_spec_drift.py`](../tools/check_spec_drift.py) now covers both, and the contract suite runs it.

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
    # The retirement tombstone. INTERFACE §5.9: a retired name is not reusable and the
    # reason is not optional, so these are columns, not something derived from events —
    # a backend with `stores_events=False` still has to answer "why is this retired?".
    retire_reason: str | None
    retired_by: str | None
    retired_at: datetime | None
    successor: str | None           # the word that replaced it, if there is one. §5.10

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
    source_version: str | None = None   # ruling R21, store version 3 — the SOURCE's own
                                    #   version, carried on the proposal row until
                                    #   approval writes it into provenance_json. §9.7

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
    # EDGES.md 5.2 -- the edge this event concerns, if any. Additive, defaulted,
    # and set by no v0 code path: row #4 is a spec. It is here rather than in the
    # build row because a shape a document says exists and the code does not have
    # is drift whichever side moved -- ruling R3's argument about
    # `Refusal.reason`, applied to a record.
    edge_id: str | None = None
    # ACTIONS.md 3.5 -- the invocation this event concerns, if any. Same shape,
    # same reason, one object along; set by no v0 code path, because row #6 is a
    # spec. Added by that row's FIRST adversarial round, which found ACTIONS.md
    # describing this field, a `read_events` filter for it and a `review` mode
    # that reads it, in a change that never touched `adapter.py`.
    invocation_id: str | None = None
    event: str                      # "proposed"|"approved"|"rejected"|"retired"|"merged"|
                                    #   "amended"|"override"|"imported"|"used"|
                                    #   "edge_added"|"edge_retracted"|"edge_amended"|
                                    #   "invocation_recorded"|"invocation_reviewed"|
                                    #   "invocation_compensated"
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

@dataclass(frozen=True)
class EdgeRecord:                        # EDGES §7.1, row 4b
    edge_id:       str                   # generated ABOVE the store — §4.2's rule
    namespace:     str                   # the FAMILY's namespace, never the endpoints'
    family:        str
    src_namespace: str; src_kind: str; src_name: str; src_instance_id: str | None
    dst_namespace: str; dst_kind: str; dst_name: str; dst_instance_id: str | None
    attributes:    dict = field(default_factory=dict)      # opaque to the adapter
    attr_schema_version: int | None = None
    provenance:    dict = field(default_factory=dict)      # the whole EdgeProvenance, JSON. Opaque
    status:        str = "active"        # "active" | "retracted" — STORED, never judged
    warnings:      tuple[str, ...] = ()
    created_at:    datetime | None = None
    updated_at:    datetime | None = None
    # The retraction tombstone, columns for the same reason TypeRecord's are: a backend
    # with stores_edge_events=False still has to answer "why is this retracted?"
    retract_reason: str | None = None
    retracted_by:   str | None = None
    retracted_at:   datetime | None = None

@dataclass(frozen=True)
class EdgeQuery:                         # EDGES §7.1
    namespace:   str | None = None       # the family's namespace. None = any
    families:    tuple[str, ...] | None = None
    # The frontier: one call serves a whole depth level rather than N calls
    incident_to: tuple[tuple[str, str, str, str | None], ...] | None = None
    direction:   str = "both"            # "both" | "out" | "in"
    include_retracted: bool = False
    edge_ids:    tuple[str, ...] | None = None
    limit:       int | None = None       # the ADAPTER pages. R13: the façade does not
    after:       str | None = None       # opaque cursor; ordering is (created_at, edge_id)

@dataclass(frozen=True)
class EdgePage:
    records:     tuple[EdgeRecord, ...]
    known:       int | None              # None = the backend cannot count. NOT 0. Rule U
    complete:    bool
    why_incomplete: str | None = None
    next_after:  str | None = None
```

> **The adapter pages. The registry does not, in v0, and this says so** *(ruling **R13**, row 3d)*. `TypeQuery.limit` / `TypeQuery.after` are real keyset pagination, implemented by both reference backends and tested by `C0-10` — seven rows at `limit=3` give three disjoint, ordered, exhaustive pages and a terminating `next_after`. **No call site in either facade passes either of them.** `list_types(namespace=None)` is a full fetch, and at UC3 scale (dozens of agencies publishing independently) that is a real cost, stated here rather than discovered.
>
> **Why it is not fixed in v0, which is a design answer and not a backlog entry.** Paging the *facade* is not plumbing `limit` through; it is deciding what Rule K means when a result is a page. `TypeListing.known` currently means *how many types matched* — a fact about the vocabulary. On a paged call it could mean that, or how many are in this page, and the two readings differ in exactly the situation Rule K exists for: a caller deciding whether it has seen everything. `complete` has the same ambiguity, and `INTERFACE.md` §3's Rule K has **no answer yet** for either. Shipping a paged facade before that answer exists is how `known` quietly starts meaning two things — which is `INTERFACE.md` §2.3's Cause B, committed by the spec itself.
>
> **So the seam stays where it is:** pagination is an **adapter capability** (`C0-10` binds it, and a third-party backend that silently drops `limit` and `after` fails that test), and the product path does not use it. The `TypeListing` paging design belongs to **Phase 3**, because the ingestion loop is the consumer that would force it and would also settle what `known` should say. Recorded as a named weakness in §11.3, not as an omission.

Two filters from `INTERFACE.md` §5.6 are deliberately **absent** from `TypeQuery`: `unverified_semantics` and `orphaned`. Both are *derived* — one from `provenance.evidence` and the approval warnings, the other from `status` + `usage` + the policy's orphan window. Pushing them into the adapter would put registry policy inside the backend, which is exactly what §3.1 forbids. The registry computes them from `find_types` + `get_usage` and reports `complete: false` when it had to page to do it. **Cost, stated: `list_types(orphaned=True)` is O(types), not O(matches), on every backend.** Acceptable at the scale this registry is for (hundreds to low thousands of types); recorded so nobody is surprised.

```python
@dataclass(frozen=True)
class InvocationRecord:                  # ACTIONS §9, row 6b
    invocation_id: str                   # minted ABOVE the store. §4.2 — so no uniqueness flag
    namespace: str                       # the FAMILY's. Never the inputs' — EDGES §2.2's rule
    family: str
    inputs: dict                         # JSON-serialisable. The typed refs are ACTIONS §2.3's
    declared_effects: tuple              # COPIED from what the GATE judged. ACTIONS §3.1
    observed_effects: tuple              # what the HOST reports it did. Recorded, never verified
    declared_policy: dict                # approval_mode / min_auto_tier / reversibility / kinds
    family_version: int                  # the declaration generation this was judged against
    outcome: str                         # "applied" | "refused" | "failed" | "compensated" — STORED
    refusal_reason: str | None           # INTERFACE §5.12's vocabulary, when outcome == "refused"
    gate_verdict: str                    # "allowed" | "refused" | "not_asked" — STORED, never judged
    compensates: str | None              # the FORWARD pointer only; the façade derives the other
    created_at: datetime
    created_by_actor: str                # INTERFACE §2.4's field, verbatim
    created_by: str                      # DERIVED from the actor by the registry. INTERFACE §2.1
    model_tier: str | None               # R20 — the tier of the actor that INVOKED
    confidence: float | None             # None = nothing scored it. NOT 0.0 — Rule U
    approved_by: str | None              # NEVER blank-implying-human. ACTIONS §3.2
    approved_at: datetime | None
    source_version: str | None           # R21's field, the SOURCE's own version
    attr_schema_version: int | None
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class InvocationPage:                    # ACTIONS §9 — a Page, and the reason is `known`
    records: tuple[InvocationRecord, ...]
    known: int | None                    # None = the BACKEND cannot count. NOT 0
    complete: bool
    why_incomplete: str | None
    next_after: str | None               # keyset: (created_at, invocation_id)
```

> **A `Page`, not a 2-tuple, and the reason is `known`** *(row #6, adversarial round 1)*. `ACTIONS.md` §6.3 requires the façade's `known` to be `int | None` because *a backend entitled to say "we did not count" must have somewhere to say it*. A `(page, truncated)` tuple gives the backend nowhere, so the façade could only ever report `len(rows)` — the falsification that rule forbids — or `None` by fiat regardless of what the backend knew. Every other paging primitive in this package already returns this shape; the fix is to stop being different.
>
> **`compensates` is on the record and `compensated_by` is not**, which is one fact stored one way and read the other. The store holds the forward pointer because the compensating invocation is written *after* the one it compensates and a store never rewrites a row (`INTERFACE.md` §5.8); the façade derives the backward pointer. Stated because the asymmetry is real and a reader who saw only `ACTIONS.md` §3.1's surface would look for a column this record does not have.
>
> **Neither `evidence` nor `history` is here.** Both ride `append_event`'s existing path with an `invocation_id` (§3.3's `EventRecord`, `ACTIONS.md` §3.5), which is where a provenance history already lives. Putting them on this record would give one concept two homes and would make a backend that stores invocations but not events undescribable.

### 3.4 The twenty-one primitives

*(Fifteen until row 4b, which added EDGES §7.1's three. The heading is the count the code has; a number in prose that nothing derives is the thing that goes stale, four times so far in this repository, so `C17-01` derives it.)*

Each has a signature, a data shape, and its uncertainty behaviour. **The uniform uncertainty rule: a primitive that cannot answer returns `None` (or a page with `known=None, complete=False`) plus a `why` drawn from `Capabilities.why` — never `0`, never `[]`, never `False`.**

---

**1. `capabilities() -> Capabilities`**
Pure, cheap, callable before `migrate()`. **Uncertainty:** none — a backend that does not know its own capabilities is broken, not uncertain.

**2. `migrate() -> int`**
Brings the store to the version this package expects; returns the version now in force. Idempotent. **When `Capabilities.owns_schema is False`, `migrate()` is verify-only:** it checks the columns it needs exist and either returns the version or raises `SchemaMismatch` listing what is missing. It never issues DDL against a schema it does not own. **Uncertainty:** a store whose version is *higher* than the package knows raises `StoreVersionUnknown` — never a silent downgrade (§9).

**3. `transaction() -> ContextManager[None]`**
Groups writes. Re-entrant calls join the outermost scope. **Uncertainty:** none — `transactional=False` is non-conformant, so this always means what it says. What "commits" means depends on who owns the connection, and the adapter **declares which** in `Capabilities.transaction_scope` (§3.5):

| `transaction_scope` | at depth 0, entry | clean exit | exception | who commits |
|---|---|---|---|---|
| `"owned"` (default) | `BEGIN` | `COMMIT` | `ROLLBACK` | this adapter |
| `"savepoint"` | `SAVEPOINT oo_<n>` | `RELEASE SAVEPOINT oo_<n>` | `ROLLBACK TO SAVEPOINT oo_<n>`, then `RELEASE` | **the host, never this adapter** |

*(Amended by roadmap row 3d, 2026-08-29, per ruling **R5** — beacon finding **U1**. The previous text — "*Commits on clean exit … savepoints are not required*" — never contemplated a session the adapter does not own, and the reference `AsyncPostgresAdapter` accepted a borrowed connection, forced `set_autocommit(True)` on it and committed at depth 0. **Sharing a connection is not sharing a transaction.**)*

**An adapter opened over a borrowed connection** — `PostgresAdapter.open(connection=…)`, `AsyncPostgresAdapter.open(connection=…)`, `SQLiteAdapter.open(connection=…)`, `AsyncSQLiteAdapter.open(connection=…)` — **never touches autocommit, never commits, and never closes the connection.** Four consequences, all stated rather than left to be discovered:

1. **The connection must be inside the host's transaction, and this is now checked.** The adapter opens none. *(Amended row 3d, second adversarial round, [Observed] on both backends.)* The two engines disagreed about the mistake and **one of them disagreed silently**: Postgres refuses an out-of-transaction `SAVEPOINT` with a raw `psycopg.errors.NoActiveSqlTransaction` — loud, but a driver exception this document never named — while SQLite **starts** a transaction on an outermost `SAVEPOINT` and **commits** it on `RELEASE`, so on the backend §4.3 calls the zero-config default the same mistake silently grants a durability the host never asked for. Both backends now check the precondition before the first savepoint and raise **`HostTransactionRequired`**, so they fail the same documented way. A driver that cannot tell returns `None` from the hook and the check is skipped rather than guessed — Rule U applies to the adapter's own preconditions too.

   **Two ways to fail the precondition, not one** *(third adversarial round)*. A connection can have **no transaction**, or one that has **already failed** — and on Postgres the second is *in* a transaction while being unable to run anything, `SAVEPOINT` included. Reading it as "open" produced exactly the raw `InFailedSqlTransaction` this check exists to replace, out of the adapter's own constructor before the caller could do anything about it. The hook therefore answers `"open"` / `"none"` / `"aborted"` / `None`, and the two refusals say which mistake the host made, because *"begin a transaction"* is the wrong advice for a transaction that already exists and is dead.

2. **Nothing is durable until the host commits, and every WRITE result says so.** A clean exit is atomic (G2 holds *inside* the host's transaction) and not yet durable. Under `transaction_scope="savepoint"` **every result of a write — `TypeEntry`, `Proposal`, the `Consumer` from `register_consumer`, the `Rejection` from `reject` — carries `not_durable_until_host_commits:<why>`**, where `<why>` is the backend's own sentence verbatim (`INTERFACE.md` §5.4's warnings vocabulary).

   **A read carries nothing, and that is Rule U rather than an omission.** A write's result is genuinely not durable at the moment it is returned. A read's result is a statement about what the store holds, and this registry cannot know whether the host has since committed — so it says nothing in either direction.

   *(Two corrections, two rounds. The paragraph originally ended at "Rule U requires it to surface" and [Observed] **nothing implemented it** — `transaction_scope` appeared nowhere in `registry.py`, so `approve()` over a host-owned session returned `TypeEntry(status="active")` with no trace that the host had not committed. The first fix then attached the sentence inside the two helpers that build `TypeEntry` and `Proposal` — which also build the results of `resolve_type`, the call §6.2 calls* "the call that must not write"*, and `list_types` — so a savepoint-scoped registry stamped the warning on **every read, forever**, including reads of rows the host had committed minutes earlier. A signal that never turns off is noise. It is now stamped at the write call sites and nowhere else, and `C0-12` binds it.)*
3. **A failed probe is savepoint-protected too.** `migrate()`'s version probe fails by design on a fresh store, and on Postgres a failed statement aborts the whole transaction; the owned-connection recovery is a bare `ROLLBACK`, which on a borrowed connection would discard the host's work. Over a borrowed connection the probe runs inside its own savepoint.

4. **Scopes on one borrowed connection must nest, and this is checked.** Two adapters may share a borrowed connection — the suite requires two adapters in one process elsewhere, and a host holding one session is the shape beacon has. But **the savepoint stack belongs to the connection, not to the adapter**, and both engines release cascadingly: `RELEASE SAVEPOINT a` destroys every savepoint opened after `a`, and so does `ROLLBACK TO a`. So if A opens a scope, B opens one on the same connection, and **A finishes first**, A's clean exit silently destroys B's — and B's own exit then fails with a raw driver error which, on Postgres, poisons the whole connection so that A's later reads fail too. *(Reproduced end to end, third adversarial round.)* The adapter keeps the stack per connection and raises **`SavepointOutOfOrder`** *before* issuing the doomed statement. The scope opened last must finish first; strict nesting is what the check permits and is all a host needs.

`C0-12` (the savepoint semantics), `C0-13` (the precondition) and `C0-14` (the nesting rule) assert all of it, on all three reference legs and in both stacks. A third-party adapter has them run against it by supplying a `BorrowedHarness` (§6.4).

**4. `put_type(rec: TypeRecord, *, expect_absent: bool = False) -> TypeRecord`**
Upsert on `(namespace, kind, name)`. With `expect_absent=True`, raises `AlreadyExists` if the key is present — **and that must come from a real constraint, not from a read-then-write check** (guarantee **G1**, §3.5). Returns the record as stored, so a backend that could not store `attributes` or `aliases` returns them empty and the registry can tell.
**Uncertainty:** if `stores_attributes` is `False`, the returned record has `attributes=` **only the keys named in `Capabilities.attribute_projections`** — `{}` when it declares none, which is what every backend declared before row 3d. The caller must not assume the rest round-tripped; the suite tests exactly this (`C0-06`), including the mixed case where one key of a two-key write survives and the other does not. *(Amended row 3d, beacon finding **U3** — §5.7.)*

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

**15. `read_events(namespace: str, *, kind: str | None = None, name: str | None = None, proposal_id: str | None = None, edge_id: str | None = None, invocation_id: str | None = None) -> list[EventRecord]`**
*(`edge_id` added by row 4b — `EventRecord.edge_id` (EDGES §5.2) gives an edge event somewhere to live and nothing to read it back by. Additive and defaulted: a caller that never passes it sees exactly the pre-4b behaviour, and `read_events(namespace)` with no filter still returns edge events, because they are events. **This line was stale for two adversarial rounds** — deviation D-4b-2 said the signature had been amended here and it had not, and a third-party author implementing `read_events` literally from this block hit a `TypeError` on the first `edge_provenance` call. `check_spec_drift.py` now diffs all eighteen printed primitive signatures against the Protocol, which is what should have caught it. **Row #6 added an `invocation_id` filter here and then took it back out, and the round trip is the lesson.** `ACTIONS.md` §3.5 and §9 read an invocation's history through this call, so that row's first adversarial round asked for the filter — and it was added to the **Protocol and to this line only**, leaving all six implementations behind. `runtime_checkable` matches on method *names*, so `isinstance` stayed green; [`check_spec_drift.py`](../tools/check_spec_drift.py) compares this printed signature against the **Protocol**, not against the backends, so the gate added after D-4b-2 passed; and every shipped adapter raised `TypeError` on the keyword. **That is D-4b-2 itself, one row later, inside the fix that cites it.** The second adversarial round found it. The `EventRecord.invocation_id` **field** stays — that is what a spec row adds, and it is what row #4 added — and the filter is the build row's, with the six implementations and the column. `ACTIONS.md` §9.1. **Row 6b lands it, and lands the three halves together**: this keyword, the `oo_event.invocation_id` column in store version 5, and all six implementations, in one change — which is the only order in which this printed signature has ever been telling the truth.)*
Ordered by `at`, then by insertion. **Uncertainty:** `stores_events=False` ⇒ the registry returns `Provenance.history == []` **with a `why`**, and — see §3.6 — refuses any destructive override that it cannot record.

---

*The last three are EDGES §7.1's, added by row 4b. **Three, not eight** — and the count is the evidence that EDGES §2.3's decision was right, because a family needs no primitive at all: it is a `TypeEntry`, so `put_type` / `get_type` / `find_types` already serve it.*

**16. `put_edge(rec: EdgeRecord, *, expect_absent: bool = False) -> EdgeRecord`**
Upsert on `edge_id`. Writes `status`, `retract_reason`, `retracted_by`, `retracted_at` **as given** and validates no transition (§3.1). Returns the record as stored, so a backend that could not store `attributes` returns them reduced to `edge_attribute_projections` and the registry can tell.
**Uncertainty:** `stores_edges=False` ⇒ raises `NotSupported`; the registry checks the capability first and never calls it, surfacing `Refusal(reason="edge_store_absent")`. It does not pretend to store and lose.
**There is deliberately no uniqueness constraint on `(family, src, dst)`** (EDGES §6.1): two `blocks` edges between one pair, written by a human in March and by a classifier in August, are two facts with different provenance, and forcing the second write to fail or overwrite makes it an edit of a provenance-bearing record, which `INTERFACE.md` §5.8 forbids. **And there is no uniqueness *flag*,** because `edge_id` is minted above the store exactly as `proposal_id` and `event_id` are (§4.2), neither of which has one either.

**17. `get_edge(edge_id: str) -> EdgeRecord | None`**
`None` means *absent*, which is a fact — the adapter always knows whether a key exists. `NotSupported` when `stores_edges=False`.

**18. `find_edges(q: EdgeQuery) -> EdgePage`**
The one call behind `neighbors`. **Traversal is not pushed into the adapter**: the registry issues one `find_edges` per depth level, with the whole frontier in `incident_to`, and **exhausts the pages for that level** — a level assembled from one page of five would be silently partial, which is what Rule K exists to prevent. `EdgeQuery.limit`/`after` are therefore used by the registry internally, which is not a contradiction of **R13**: R13 is about the *façade* exposing paging to a caller, and `neighbors` exposes none. Ordering is `(created_at, edge_id)`; `C17-05` binds the keyset the way `C0-10` binds `find_types`'.
**Uncertainty:** the general rule is `find_types`' — a filter the backend cannot apply returns `complete=False` with a `why`, never a filtered-looking empty page. **One case deviates deliberately.** `find_edges` with `q.families` set on `indexes_edges_by_family=False` returns the node's edges **unfiltered, with `complete=True`**, and the registry filters above. The type case has no bound — the alternative to an index is scanning the whole type table, so the honest answer is *"I cannot answer this"* — whereas the edge case is already bounded by `q.incident_to`, so the backend genuinely **can** answer a slightly wider question completely and the registry narrows it. A backend that could not even do that returns `complete=False` with the `why`, and the general rule applies again.
**Second uncertainty, and it is the one a reader misses:** with `include_retracted=False` (the default) a page that **suppressed** a retracted edge is `complete=False` with a `why`, because a default that hides things is `list_types`' rule (`INTERFACE.md` §5.6). The adapter is the only party that knows the count, so the adapter says it.

**No fourth primitive for retraction, and no fifth for counting.** Retraction is `put_edge` with a changed `status`; counting is `EdgePage.known`. Both were considered and dropped, because a primitive that exists only to express a policy transition is a policy inside the adapter.

### 3.5 The two storage guarantees, and the one that is not required

Exactly two things cannot be enforced above the adapter.

**G1 — uniqueness of `(namespace, kind, name)` in the type store.**
Required by §5.4 (*name already taken → return the existing entry*) and §5.9 (*a retired name is not reusable*). A read-then-write check is not sufficient: two concurrent approvals of `facility` both read absent and both insert, and the registry's central promise — one word, one entry — is gone. `put_type(expect_absent=True)` must raise from a **database constraint**. Note the constraint is per `(namespace, kind)`: `facility` as an `entity` and `facility` as a `value_set` may coexist (`INTERFACE.md` §2.1).

> **Both guarantees are raced, not merely asserted** *(added by roadmap row 3c, 2026-08-28, after an adversarial review round)*. Until then the only tests of G1 and G2 called the primitives **sequentially on one thread**, which a read-then-write check passes exactly as happily as a real constraint does — so a backend whose "uniqueness" was a Python-level check could have been blessed conformant and then corrupted itself the moment two ingestion workers hit one store, which is the deployment shape UC3 is the fixture for. `C0-08` now races two adapters on one store, on both reference backends and in both stacks. **Verified to bite:** a wrapper that implements `expect_absent` as check-then-insert produces **two winners** under the race and fails `C0-08`, while the constraint-backed backends produce one winner and one `AlreadyExists`.

**G2 — atomicity of the decision transactions.**
`approve` writes four things: the proposal's decision, the new `TypeEntry`, its membership rows, and a `ProvenanceEvent`. A half-commit produces either an approved proposal with no type (an approval nobody can see) or an active type with no approval record — and the second violates `INTERFACE.md` §2.4's rule that `approved_by` is never null on an `active` type, which is the rubber-stamping failure arriving through the data model. `reject`, `retire` and `merge_types` have the same shape.

> **G2 holds in both transaction scopes, and durability is a separate question** *(row 3d, ruling **R5**)*. Over a **borrowed** connection (`transaction_scope="savepoint"`) `transaction()` opens `SAVEPOINT oo_<n>` at depth 0, `RELEASE`s it on clean exit and `ROLLBACK TO`s it on exception; nested calls join the outermost savepoint. The four writes of an `approve` are still all-or-nothing — **that is G2, and it is preserved** — but the outer commit belongs to the host and this adapter never issues it. `transactional` therefore stays REQUIRED `True` for a savepoint adapter: it *is* transactional. What it is not is *durable at clean exit*, and `Capabilities.why["transaction_scope"]` is the sentence the registry surfaces wherever a result would imply otherwise. **What "no" would have cost, recorded so the choice is reviewable:** a host that shares a connection without sharing a transaction, or a second connection and no shared transaction at all — both worse than either honest option (R5 point 5). `C0-12`.

**A projection is not a fourth guarantee.** `attribute_projections` (§3.2, §5.7) says *where* a key is stored, not that storage is atomic or unique — G1 and G2 are untouched by it, and no new guarantee is required to implement it. It is named here only because a reader looking for "what must the storage layer promise" should not have to go to §5 to find that the answer is still two.

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

`retire(force=True)` "records the override in `history`" (§5.9); `merge_types(acknowledge=[…])` records the acknowledgement (§5.10); and since row 3e `reinstate` (§5.9b, ruling **R11**) **clears** four retirement fields off the live row, which makes its event the only record that the retirement ever happened. On a backend with `stores_events=False` the record cannot be written. The options are to do the destructive thing unrecorded, or to refuse. **Refuse.** An unrecorded override is exactly the class of silent, unattributable change this registry exists to prevent, and a backend that cannot keep an audit trail has not earned the right to be overridden. A backend with `stores_events=False` is still conformant — the suite tests the *refusal*, not the capability (`C9-02`, `C10-08`, `C9-11`).

> **`amend_edge` is the fourth caller, and it is the one that had to argue its way IN rather than out** *(row 4c, ruling **R37**)*. [`EDGES.md`](EDGES.md) §2.6 argues `retract_edge` **past** this rule — *"the record **is** the row"*, because `status`, `retracted_by`, `retracted_at` and the reason are columns on the edge itself, so an unrecordable retraction does not exist. **That argument does not transpose to an amendment.** There is no column holding an edge's *prior* confidence, so on `stores_edge_events=False` an amendment erases the old value with no record anywhere that it ever held one. That is this rule verbatim, and it is `reinstate`'s shape exactly. Refused, non-overridably, and **no new `Refusal.reason` was minted for it** — the honest answer to *"is this a new failure?"* was no. `C17-43` asserts both halves on one store: the amendment refused, the retraction still succeeding and still warning, because the two are only defensible together.

> **`reinstate` is the third caller, and the one where "destructive" needs saying out loud** *(row 3e)*. Every other call in `INTERFACE.md` §5 only ever **appends**: `retire` adds a tombstone, `merge_types` adds an alias and a tombstone, and nothing is deleted anywhere. `reinstate` removes `retire_reason`, `retired_by`, `retired_at` and `successor` from the live row — because a retirement that is no longer in force must not read as current (§5.8's append-only rule puts it in the history instead). **The stated cost:** a `stores_events=False` store cannot un-burn a name. That is the world exactly as it was before R11, and it is consistent rather than an exception, because such a store already cannot record a forced retirement either.


---

*The last three are ACTIONS §9's, added by row 6b. **Three, not eight** — and the count is the evidence that ACTIONS §2.1's decision was right for the same reason EDGES §7.1's three were: an action **family** needs no primitive at all, because it is a `TypeEntry`. What needs a store is the **invocation**, which is an instance, not a word.*

**19. `put_invocation(rec: InvocationRecord) -> InvocationRecord`**
A plain INSERT, not an upsert, and **`expect_absent` is deliberately absent as a parameter**: `invocation_id` is minted above the store (§4.2), so a collision is not a case a caller can reach; and an invocation ledger is append-only by construction, so there is no amend path for an upsert to serve. A duplicate id raises `AlreadyExists` rather than silently overwriting a provenance-bearing record (`INTERFACE.md` §5.8). Writes `outcome` and `gate_verdict` **as given** and validates no transition (§3.1). Returns the record as stored.
**Uncertainty:** `stores_invocations=False` ⇒ raises `NotSupported`; the registry checks the capability first and never calls it, surfacing `Refusal(reason="action_store_absent")`. It does not pretend to store and lose.

**20. `get_invocation(invocation_id: str) -> InvocationRecord | None`**
`None` means *absent*, which is a fact — the adapter always knows whether a key exists. `NotSupported` when `stores_invocations=False`.

**21. `find_invocations(*, family: str | None = None, namespace: str | None = None, actor: str | None = None, outcome: str | None = None, since: datetime | None = None, gate_verdict: str | None = None, effect_undeclared: bool | None = None, unreviewed: bool | None = None, compensates: str | None = None, after: str | None = None, limit: int = 100) -> InvocationPage`**
The one call behind the ledger. Ordering is `(created_at, invocation_id)` and the cursor is keyset, for `find_edges`' reason: an offset page over an append-only table shifts under a concurrent write. **The registry does not expose the cursor** (rulings **R25**/**R47**/**R58** route paging to Phase 3); the primitive has one so the façade can bound its own reads honestly.
**The last three filters are the reason this primitive has ten arguments and not seven**, and their absence was `ACTIONS.md` §4's whole argument failing quietly *(row #6, adversarial round 2)*. `gate_verdict`, `effect_undeclared` and `unreviewed` are the three reads a governance layer exists to serve — the override query, the blast-radius query and the review queue — and they were on the façade and on **no primitive**, so *"the registry filters above the store"* meant reading a `limit`-bounded page and filtering it afterwards. On a pinned 2,399-dataset ledger with one override at row 1,200 the query returned **zero rows** with `complete=False`. **A floor of zero is not a conservative measurement; it is the wrong one, and it is indistinguishable from a clean deployment.**
`effect_undeclared` is a predicate over the **stored** `warnings` list and not a judgement about one: the adapter matches a string it never interprets (§3.1). `unreviewed` pushes down as far as *"no `invocation_reviewed` event exists for this row"*; the half that asks whether the **family** is in `review` mode is a fact about another row's attributes and stays above the store, over a set of families the registry has already materialised — and the report says `complete=False` either way.
**Uncertainty:** the general rule is `find_types`' — a filter the backend cannot apply returns `complete=False` with a `why`, never a filtered-looking empty page. A backend with `indexes_invocations_by_family=False` may answer a family filter by scanning; correctness is unchanged and a scan may hit `limit`, and then `complete=False` carries the backend's own sentence.


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
    created_by      TEXT         NOT NULL             -- seed | ai | user | derived (R17)
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
    source_version  TEXT                                  -- the SOURCE's own version (R21, §9.7)
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
    version: int                    # monotonic per (namespace, kind, name)
    fields: dict[str, FieldSpec]
    additional: str                 # "allow" | "warn" | "forbid"  — unlisted keys
    mode: str                       # "off" | "warn" | "enforce"
    registered_at: datetime
    registered_by: str
    name: str | None = None         # ruling R10 — None is the per-kind schema; a name
                                    #   is a schema for that ONE type, shadowing it
```

Stored in an eighth table, `oo_attr_schema (namespace, kind, name, version)` — **not** as a new `TypeEntry` kind. The dogfooding option (register a schema as `kind="attribute_schema"`, getting provenance and the approval loop for free) was considered and **rejected**: an attribute schema is not a word in the vocabulary, and putting it in `oo_type` means `list_types()` mixes schemas with vocabulary and `merge_types` can be pointed at one. That is `INTERFACE.md` §2.3's Cause B — one container meaning two things — committed by the schema itself. **Cost of the rejection, stated: attribute schemas have no proposal→approval loop in v0.** Recorded as a weakness in §11.

**`FieldSpec.description` is required and non-empty**, on exactly the reasoning of `INTERFACE.md` §2.1's non-empty `definition`: an undescribed field is how the escape hatch re-forms one level down.

### 5.2b Name-level schemas shadow the per-kind one *(ruling **R10**, row 3e, 2026-08-29)*

`name` is `None` for the per-kind schema — which is every schema this mechanism shipped with — and a type name for a schema that applies to **that one type**. The name-level schema **shadows** the per-kind one; every other name of that kind is judged by the per-kind schema exactly as before.

**Why it is a ruling and not a tidy-up.** §5.6's third bullet records the limitation *in this mechanism's own flagship justification*, and `C15-07` asserts both of its horns: a schema keyed per kind cannot serve CMS's two `kind="value_set"` entries, because `scope_severity_code` must be made to declare an `ordering` (§5.1's whole argument) and `deficiency_corrected_status` has none to declare. Requiring the field refuses the unordered set for lacking something it has no business having; making it optional lets the ordered set be created declaring no order — **which is the CMS severity scale back inside somebody's transform, unversioned, which is the thing §5.1 says this mechanism exists to prevent.** There was no third option until this key change.

**Four rules, and the first is the one to read twice:**

1. **Shadowing is replacement, never merge.** A name-level schema's `fields` are the whole schema for that type; the per-kind schema's fields — including its `required` ones — do not come along. A merge of two field maps produces a third schema **nobody wrote and nobody versioned**, which is the unversioned accumulation this whole section exists to stop, one level up. The cost is stated: a deployment that wants the common fields in an override writes them there.
2. **Fallback is per lookup, not per field.** `(namespace, kind, name)` if one exists, else `(namespace, kind)`, else no schema. One of the two governs a write; never both.
3. **An override is a schema, not an exemption — the fields are replaced and the strictness is a FLOOR.** Its own `required` fields and `enum`s apply with full force (`C15-10` asserts an override refusing its own write), and its `mode` and `additional` are raised to the per-kind schema's whenever the per-kind schema is stricter. **[Observed, row 3e first adversarial round]** the first cut shadowed `mode` and `additional` along with `fields`, so a name-level schema with `fields={}`, `additional="allow"`, `mode="off"` **turned a strictly enforced kind completely off for one name** — no refusal, no warning, and nothing in the census to show it. In UC3 that is one agency's one-line, unreviewed opt-out of a rule dozens of agencies publish under; the softer form (a `warn` override under an `enforce` kind) silently downgrades a refusal to a warning. **The floor is applied when a write is validated, not when a schema is registered**, because a registration-time check is bypassed by registering the weak override first and the strict per-kind schema second — a rule whose ordering the caller picks is not a rule. `C15-12`.
4. **`Refusal(reason="attributes_schema_violation").detail` names which schema refused**, as `schema_name` (`None` = the per-kind one) beside `schema_version`. With two schemas in play *"which one refused me"* became a question a caller has to be able to answer.

**Two costs of the key change, stated rather than found later.**

- **`attribute_census` reads one schema per type, per kind.** There is no *list the schemas* primitive — the optional `AttributeStore` extension has four methods and adding a fifth would silently un-implement it for every existing third-party backend (`isinstance` against a `runtime_checkable` Protocol matches on method names) — so discovering which names carry an override means asking. The lookups are hoisted out of the per-key loop and memoised per kind, which took a measured **21,043 round-trips down to 1,003** for 500 types and 21 census keys *(row 3e, second adversarial round)*; what remains is linear in the types of a kind, on an audit call, and is stated here rather than hidden. Do not put `attribute_census()` in a request path.
- **A name-level schema cannot be removed.** `put_attr_schema` is an upsert keyed `(namespace, kind, name, version)` and the lookup takes the highest version, so an override registered once governs that type for the life of the store; the only retraction is a higher-version override that hand-copies the per-kind schema's fields — which is the *"third schema nobody wrote"* rule 1 refuses elsewhere. **Recorded as a decision, not fixed:** a delete would be the first destructive operation on deployment configuration in this package, and §9.4's licence to drop a v0 store is the available answer meanwhile. Raised by row 3e's second adversarial round; noted in §11.3.

> **One kind's "name" is not a type name, and that is `edge_payload`** *(ruling **R34**, row 4c; recorded here after that row's first adversarial round pointed out this section had not been amended for it)*. Everything above assumes a name-level schema's `name` is a **type** name — the fallback rule, the census's discovery of overrides by enumerating the types of a kind, and the sentence *"a name-level schema whose name matches no type governs nothing"*. For `kind="edge_payload"` none of that holds: the name is the string a `kind="edge"` family declares in its `payload_schema`, there are no `kind="edge_payload"` **types** at all, and the census therefore discovers those schemas **through the families that declare them** ([`EDGES.md`](EDGES.md) §2.5, deviation **D-4c-2**). The four rules above apply unchanged — shadowing is replacement, fallback is per lookup, the strictness is a floor, and the refusal names which schema — because they are about how two schemas compose, which is independent of what the third key component denotes. **What changes is only where a reader looks the name up**, and this box is here so that reader is not left inferring it.

**Storage, and the one sentinel.** `name` is a `NOT NULL` column whose empty string means *the per-kind schema*. No type name can be empty — `INTERFACE.md` §2.1 requires `^[a-z][a-z0-9_]{0,63}$` — so one column carries both cases, the primary key stays a primary key rather than a partial index over a nullable column, and the two are never confusable. `AttributeSchema(name="")` raises rather than quietly meaning "per-kind": the sentinel belongs to the store, not to the caller. **This is the opposite decision from §5.7's projected `None`**, and deliberately so: there the colliding column belongs to the *host* and writing our sentinel into it is what `owns_schema=False` forbids; here the column is ours.

**`attribute_census`'s `declared` is tri-state, and Rule U is why** *(corrected after row 3e's first adversarial round)*. A census row is `(kind, key)` over **every** type of that kind, so after this ruling a key can be declared by a name-level schema for one name and by nothing for the rest. `True` would claim it for types the override never covered — the reason the first cut asked only the per-kind schema. But `False` is the symmetric error and it is the one that fires: **[Observed]** with the natural post-R10 CMS configuration — a strict per-kind `value_set` schema plus the `deficiency_corrected_status` override — the census reported that override's **required** `values` key as *undeclared*, a confident negative on the call whose whole job is making the escape hatch enumerable, in the fixture this ruling exists for. So:

| `declared` | means |
|---|---|
| `True` | every schema that governs a type of this kind declares it |
| `False` | none of them does |
| `None` | they **disagree** — some name of this kind is governed by a schema that declares it and some by one that does not, so the answer depends on which type. `declared_why` names them |

> **The rule is symmetric, and the first cut only got one direction** *(corrected after row 3e's second adversarial round)*. It asked the per-kind schema, fell back to the overrides when that said `False`, and returned a flat `True` when the per-kind schema declared a key an override **removes** — while the registry refused a write of that key on the overridden name with *"not declared in the schema"*. Shadowing is replacement (rule 1), so an override drops fields as readily as it adds them, and both directions are the same Rule U failure in the same call on the same CMS fixture. **What `declared` is answered over, stated:** the schemas governing types **that exist**. A name-level schema whose name matches no type governs nothing, and the census is a report about what was written.

`C15-12`.

**One consequence of the key change, stated rather than discovered: `attr_schema_version` no longer identifies a schema on its own.** Two entries of one kind written under two different schemas can both record `attr_schema_version = 1`, because the version sequence is per `(namespace, kind, name)` and the per-kind sequence starts at 1 as well. **The version is meaningful together with the entry's own name**, which is how a reader resolves it: look for `(namespace, kind, name, version)` first, then `(namespace, kind, version)`. §5.4's promise — that an entry says which *generation* of `attributes` it belongs to — still holds under that reading, and `oo_attr_observed.schema_versions` likewise mixes the two sequences. **The residual case, named:** a name-level schema registered *after* an entry was written makes that lookup attribute the entry to the override it was not written under. Recorded in §11.3 rather than fixed, because the fix is a second column on `oo_type` and the ambiguity is resolvable by a reader who knows the rule above.

**Store version 2.** See §9.6.

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
- ~~**It cannot serve two `value_set`s of one dataset differently**~~ — **FIXED by ruling R10, row 3e, 2026-08-29; see §5.2b.** *(Recorded by row 3c after an adversarial review round; the two horns stay asserted by `C15-07`, which is now the record of what the key change bought rather than a live limitation.)* A schema was keyed `(namespace, kind, version)` — **one per kind, not per type name** — and CMS has two `kind="value_set"` entries with different shapes. `C15-10` drives both of them through the name-level key and `C15-11` holds the other half: a name with no override of its own is still judged by the per-kind schema, so registering one exception does not quietly relax the kind.
- It does not stop a deployment from writing `attributes={"stuff": {...}}` and putting an entire nested world in one declared `dict` field. Nothing can, short of a schema language.

### 5.7 Projected keys — when the backend owns the column *(row 3d, beacon finding U3)*

Everything above assumes `attributes` is one opaque JSON document the adapter never reads (§4.5). For the two reference backends that is exactly true. It is **not** true for a backend sitting on a schema somebody else designed, which is the deployment §9.3 and §7 are both about: beacon's `work_link_types` has `is_symmetric` and `inverse_label` as real typed columns, and an adapter over it round-trips those two keys **perfectly** while storing no arbitrary key at all.

`stores_attributes` could not describe that backend. It had two answers and both were wrong:

| answer | what it claims | what actually happens |
|---|---|---|
| `True` | every key round-trips | arbitrary keys are silently lost — Rule U's named failure |
| `False` | no key round-trips | two keys it stores faithfully are disclaimed, and the registry reports an unknown where it has a fact |

**So the declaration is split.** `stores_attributes` keeps its meaning — *an **arbitrary** dict survives a round trip* — and `attribute_projections: frozenset[str]` names the keys the backend owns as typed columns. The rules, in full:

1. A key in `attribute_projections` **round-trips through the column**, whatever `stores_attributes` says. It is not in the JSON blob; on a backend with no blob at all there is no blob for it to be in.
2. A key that is neither stored nor projected comes back **absent, with the `why` from `stores_attributes`** — unchanged from v0, and still never invented and never a value shaped like an unknown.
3. `attribute_projections` is **not** a `Capabilities` flag: there is nothing to decline. A backend that projects nothing declares `frozenset()`, which is the default and is what both reference backends declare.
4. **The census (§5.5) counts projected keys and says it is partial.** `attribute_census` used to refuse outright when `stores_attributes` was `False`; a projected key is a key that *was written*, so refusing hid a fact it had. It now returns those entries with `complete=False` and a `why_incomplete` naming the projected keys — the `ConsumerReport.complete=False` move, applied to the census.
5. **No `INTERFACE.md` change.** A caller of `list_types` sees `attributes` and its warnings exactly as before; this is a storage-layer declaration about where a key lives, not a new surface.

**One collision, stated** *(row 3d, second adversarial round)*. A projected key written with the value `None` is **indistinguishable from never written**: the column is `NULL` either way, so it comes back absent and `attribute_census` does not count it. Rule 1 above is therefore true for every value except that one. **The alternative was rejected on purpose:** distinguishing them needs a sentinel written into the column — and that column belongs to the **host**, is typed by the host, and may not accept one. Writing this package's private encoding into somebody else's schema is exactly what `owns_schema=False` exists to prevent, and a projection that only works on columns we are allowed to corrupt is not a projection. A host that needs a meaningful `None` should keep that key out of `attribute_projections` and let it be honestly absent-with-a-`why` instead.

**What it does not do.** It does not let the registry *ask* for a projection, and it does not migrate a key into a column. The set is the backend's own statement about a schema it did not choose. Tested by `C0-06` — a projected key survives and a non-projected key on the same write does not — and by [`check_capability_matrix.py`](../tools/check_capability_matrix.py)'s tenth configuration, `stores_attributes=False` **plus** a declared projection.

---

## 6. The contract suite — the definition of conformance

### 6.1 The rule

> **A backend is conformant iff the whole suite passes against it. The suite is parametrised over the three reference legs and must pass on all three, in one process, in one run.**

*(“Both reference backends” until row 3d, 2026-08-29, which added the third — beacon finding **U2**.)*

**The three legs.**

| leg | what it is | why it is a leg and not a double |
|---|---|---|
| `sqlite` | the full reference backend, nine tables, every flag `True` | the zero-config case (§4.3) |
| `postgres` | the full reference backend, the reference deployment (§4.4) | two unlike stores, one observable answer |
| `sqlite_minimal` | **a real SQLite store with four of the nine tables absent** — no `oo_proposal`, no `oo_event`, no `oo_type_predicate`, and an `oo_type` with no `attributes_json` but with a typed `primary_key_json` the host owns. Five flags declined at once (`stores_proposals`, `stores_events`, `stores_attributes`, `indexes_membership`, `owns_schema`), plus `attribute_projections={"primary_key"}` | §7.4 calls a backend of exactly this shape conformant *"as a third backend"*, and until row 3d **nothing here checked it against a real store**: degradation was simulated by wrapping a fully capable adapter in `DegradedAdapter`, which is a test double reporting on itself |

`ontoloche/backends/sqlite_minimal.py`, and its hand-written async twin. The missing tables are missing **from the SQL**, not behind a Python `if`; the host's DDL lives in the same module (`create_host_schema`) precisely so `migrate()`'s verify-only promise stays testable — nothing the adapter does can create those tables.

**A degraded leg cannot exercise every contract id, and the run says which.** That is the coverage report (§6.4, ruling **R12**), and it is the other half of this leg: a third leg that passed 66 fewer assertions in silence would be worse than no third leg.

Per **A5** (founder-confirmed 2026-08-28), this suite passing on CMS data is the gate for Phase 2B — the condition that replaces §12's "real outside user" and permits Tenshen to depend on the package.

Two rules that keep the definition honest:

1. **Capability-honest tests.** A test whose subject is a declared-`False` capability asserts the *honest unknown* — `None` plus a non-empty `why` drawn from `Capabilities.why` — not a value. A backend that cannot count usage passes `C7-01` by returning `count=None`; it fails by returning `0`. This is what makes conformance achievable for unlike backends without weakening it.
2. **Two capabilities are not negotiable.** `enforces_unique_name` and `transactional` must be `True` (§3.5). Everything else may be `False`.

**Running it.** `pytest --pyargs ontoloche.contract`, or against a foreign backend `python -m ontoloche.contract --adapter beacon.ontology:WorkLinkTypeAdapter`. **Add `--borrowed pkg.mod:make_harness` if your adapter declares `transaction_scope="savepoint"`, and `--schema-harness pkg.mod:make_schema_harness` if it declares `owns_schema=False`** — without them those declarations are taken on trust and the run says so (§6.4).

*(This paragraph amended by row 3c, 2026-08-28, after an adversarial review round found the conformance machinery did not enforce what this section claims.)*

**`nonbinding` now exempts, where before it only annotated.** §5.5 says a backend *"may not be failed for"* `C15-02`. Registering `@pytest.mark.nonbinding` never made that true: the runner passed every test, so a backend that honestly declines the optional `AttributeStore` protocol — behaviour §5.5 explicitly permits — got `complete=False`, failed `C15-02`'s assertion, and was reported as failing the suite. **Verified before it was fixed:** a wrapper that omits `AttributeStore` returns `AttributeCensus(entries=(), known=None, complete=False, why="this backend has no attribute census storage")` and fails that test. `run_contract_suite` and `python -m ontoloche.contract` now pass `-m "not nonbinding"` by default, with `--include-nonbinding` to run them anyway. **A conformance verdict is the default run; the flag is for curiosity.**

**Resolver-dependent tests are binding here and not there.** `C3-08`, `C3-09` and `C4-06` carry a `resolver_dependent` marker. Against the two reference backends they run and must pass — they pin real behaviour of the resolver this package ships. Against a foreign adapter (`--adapter`, or `run_contract_suite`) they are **skipped with a reason naming §2.6 and question **Q4****, because a third-party backend paired with its own resolver — §2.6's own production path — was otherwise failing mandatory conformance tests for a reason that is neither its storage nor its choice. Skipped, never silent: `-rs` prints exactly what was not run and why.

**Every run states what it covered.** §6.1 requires *both* reference backends *in one run*, and a bare `pytest --pyargs ontoloche.contract` with no `OO_POSTGRES_DSN` exits `0` having exercised SQLite alone — a skip is easy to miss beside a wall of passes. The suite now prints, at the end of every run:

```
CONFORMANCE (PACKAGE.md 6.1)
  backends exercised: postgres, sqlite, sqlite_minimal
  nonbinding tests excluded from the verdict: none
```

and, when a reference backend did not execute, **`NOT a conformance run -- postgres did not execute`** in its place. It is still possible to run the suite without Postgres; it is no longer possible to read the result as conformance.

### 6.2 The suite, enumerated

**335 tests in twenty groups.** *(The last two are row #6's, and both pin a trip of `ROADMAP.md`'s kill row against the shipped registry: `C10-09` from its second adversarial round — two EMPTY predicate extents compared byte-identical — and `C9-18` from its third — `retire(successor=)` performing the collapse `merge_types` refuses, with none of its guards.)* *(109 at #3; **fifteen** added by row 3c — `C0-07` … `C0-11`, `C1-09`, `C3-10`, `C3-11`, `C5-12`, `C6-07`, `C7-07`, `C9-07`, `C9-08`, `C15-07`, `C15-08`. See §8b.2 and §8b.5. **Five** added by row 3d — `C0-12` (ruling R5 / beacon finding U1), `C0-13` (its precondition) and `C0-14` (its nesting rule, both from the adversarial loop), `C15-09` (beacon finding U3) and `C11-05` (ruling R8). **Eight** added by row 3e — `C3-12` (ruling **R6**, cross-namespace lookup), `C15-10` and `C15-11` (ruling **R10**, name-level attribute schemas), `C9-09`, `C9-10` and `C9-11` (ruling **R11**, `reinstate`), `C4-10` (ruling **R17**, `created_by="derived"`) and `C8-06` (ruling **R21**, `Provenance.source_version`). **Three more** by row 3e's first adversarial round — `C3-13`, `C9-12`, `C15-12` — **five** by its second — `C9-13`, `C9-14`, `C9-15`, `C12-05`, `C16-05` — and **five** by its third: `C9-16`, `C9-17`, `C12-06`, `C12-07`, `C16-06`. **Forty-four added by row 4b** — the whole of `C17`, the first group in this suite whose subject is a surface `INTERFACE.md` does not carry (`EDGES.md` v0's two writes and one read), and the whole of `C18`, which drives row #4's three design tests through the **shipped** store instead of through the throwaway probe kit they were written against. *(8 + 3 + 5 + 5 = 21, and 129 + 21 = 150; 150 + 34 + 10 = 194 — `C17-30`/`C17-31` were added by row 4b's own first adversarial round and `C17-32`/`C17-33`/`C17-34` by its third. The group headers above are checked against `test_manifest.py` by `C0-04`'s neighbour in that module, because row 3e's third adversarial round found them summing to 142 over tables enumerating 145 — a number in prose the code does not derive, for the fourth time in this repository.)*)* **Thirty added by row 4c** — four by its THIRD adversarial round (`C9-20`, `C9-21`, `C10-13`, `C17-53`), which reproduced the kill row's **sixth** trip through four doors; six by its FIRST adversarial round and two by its SECOND (`C17-51`, `C17-52`), which found ruling **R38** unapplied to family names; (`C10-11`, `C10-12`, `C12-10`, `C17-48`, `C17-49`, `C17-50`), which reproduced the kill row's **fifth** trip; — `C12-08`/`C12-09` and `C9-19` for the kill row's FOURTH trip and the guard-ordering defect beside it, both found by [`check_merge_guard.py`](../tools/check_merge_guard.py); `C10-10` for ruling **R40**, `C17-47` for ruling **R39**, `C17-44` … `C17-46` for ruling **R38** (the walk follows the successor chain, and says which edges it followed), `C17-41` … `C17-43` for ruling **R37** (`edge_amended` given the call it was narrated with), `C17-35` … `C17-40` for ruling **R34** (`payload_schema` validated: modes, versions, the enforcement floor, the census floor and the key collision that made a governed family unregisterable), and `C15-13` for the defect that ruling reached on the Postgres leg. **Twenty-three added by row 4d** (226 → 249), and the split is the row's own story: **six** by the build itself — `C2-06`, `C3-14`, `C4-11`, `C6-08`, `C10-14`, `C12-11` for the Q56 default, R54 and R55 — and **seventeen by its three adversarial rounds**, which reached `ROADMAP.md`'s kill row a **seventh** and an **eighth** time. Round 1: `C4-12`, `C9-22`, `C9-23`, `C10-15`, `C10-16`, `C12-12`. Round 2: `C3-15`, `C4-13`, `C6-09`, `C9-24`, `C10-17`, `C10-18`, `C12-13` — five of them defects in round 1's own fixes. Round 3: `C3-16`, `C4-14`, `C9-25`, `C10-19`. Mechanism labels are `INTERFACE.md` §4's: **1** no review · **2** could not find · **3** never retired · **4** collision · **C** silent per-consumer drop.

**C0 — adapter conformance (14).** No interface call; this is the protocol itself.

| id | asserts | mech |
|---|---|---|
| C0-01 | `capabilities()` returns every field; every `False` flag has a non-empty `why` | — |
| C0-02 | **G1**: `put_type(expect_absent=True)` twice raises `AlreadyExists` from a constraint | — |
| C0-03 | **G2**: an exception inside `transaction()` leaves the store byte-identical | — |
| C0-04 | **§3.1, by source inspection**: all **seven** of §3.1's identifiers — `Refusal`, `Rejection`, `Resolution`, `ConsumerReport`, `UsageReport`, `TypeEntry`, `Proposal` — appear nowhere in `adapter.py` or `backends/`. *(Row 3c: the test checked five of the seven; `ConsumerReport` and `UsageReport` were missing from it, though neither was ever present in the code)* | — |
| C0-05 | `migrate()` is idempotent; the version row is written in the same transaction as the DDL | — |
| C0-06 | every `*Record` round-trips; a field the backend cannot store comes back empty, not wrong | — |
| C0-11 | **one name under two kinds is ambiguous, not arbitrary:** §4.1 blesses `facility` as an `entity` beside `facility` as a `value_set`, and §3.4 primitive 5 says `get_type(kind=None)` raises `AmbiguousKind` there. *(Row 3c: `AmbiguousKind` was raised by both reference backends and referenced by **no test in the repository**; an adapter returning `rows[0]` passed the whole suite — a silent wrong answer in the exact case the per-`(namespace, kind)` scoping exists to permit)* | — |
| C0-10 | **keyset pagination actually pages:** seven rows at `limit=3` give three disjoint, ordered, exhaustive pages and a terminating `next_after`. *(Row 3c, and the first defect found by asking whether a BROKEN backend can PASS: an adapter that silently drops `limit` and `after` — a duplicate-forever loop in any real keyset consumer — ran the whole suite to `119 passed, exit 0`. Both reference backends had implemented it correctly and nothing had ever checked)* | — |
| C0-09 | **`owns_schema=False` makes `migrate()` verify-only** (§9.3): against a store the host application owns, `migrate()` raises `SchemaMismatch` naming what is missing, issues no DDL to fix it, and once the owner has created the schema returns the version and is usable. *(Row 3c. B1 is the first Tenshen contortion and the enterprise-DBA posture is the reference deployment — both reference backends implemented this and nothing asserted it.)* | — |
| C0-08 | **G1 and G2, RACED:** two adapters on one store and two real concurrent writers — one absent name (exactly one insert wins, one `AlreadyExists`, one row in the store) and one proposal approved twice (exactly one `TypeEntry`, one `Refusal("already_decided")`). *(Row 3c, §8b.5. `C0-02`/`C0-07` call the primitives sequentially, which a read-then-write check passes as happily as a constraint does — §3.5 says a read-then-write check is **not** sufficient, and until this test nothing held it to that. A thread race has no mechanical async form, so the sync module is excluded from `tools/unasync.py` and the async counterpart is hand-written; both claim this id and both are binding.)* | — |
| C0-12 | **a borrowed connection uses SAVEPOINTs and never commits** (§3 item 3, §3.5, ruling **R5**): an exception inside `transaction()` leaves the **host's** transaction OPEN with only the savepoint rolled back and the host's earlier work intact; a clean exit is visible to the adapter and invisible to every other connection until the host commits; nested calls join the outermost savepoint. *(Row 3d, beacon finding **U1**. `AsyncPostgresAdapter.open(connection=…)` accepted a borrowed connection, called `set_autocommit(True)` on it and committed at depth 0 — the host shared a connection and did not share a transaction. Builds backends directly, so the async twin is hand-written like `C0-08`'s and `C0-09`'s; both claim the id and both are binding.)* | — |
| C0-13 | **a borrowed connection with no usable transaction is refused** (§3 item 3, consequence 1): a connection with **no** transaction, and one whose transaction has **already failed**, both raise `HostTransactionRequired`, and the two messages say which mistake was made. *(Row 3d, third adversarial round. The precondition existed and **nothing tested it**: every harness in the suite called `host_begin()` before handing the connection over, so an adapter omitting the check passed all 127 ids — while being able, on SQLite, to start a transaction on its outermost `SAVEPOINT` and commit it on `RELEASE`, granting a durability nobody asked for. Its own id rather than an assertion inside `C0-12`, so a backend that cannot drive it says so in the coverage report instead of passing quietly.)* | — |
| C0-14 | **scopes on one borrowed connection must nest** (§3 item 3, consequence 4): strictly nested scopes work; an out-of-order close is refused with `SavepointOutOfOrder` **before any SQL is issued**; and the refused adapter is then unusable rather than quietly reusable. *(Row 3d, third adversarial round. Reproduced: A opens a scope, B opens one on the same connection, A finishes first — A's `RELEASE` destroys B's savepoint because both engines release cascadingly, B's exit then raises a raw driver error, and on Postgres the whole connection is poisoned so A's own later reads fail. The first fix refused correctly and still left the adapter looking closed, so a caller could open a fresh scope that orphaned the old savepoint forever — refusing to corrupt the connection is not enough if the adapter's own state is left corrupt.)* | — |
| C0-07 | **G1's key is *scoped*:** one word under three namespaces is three rows, each `expect_absent=True`, each retrievable with its own definition and attributes; the collision is still raised *within* a namespace; `TypeQuery(namespace=None)` returns all three. *(Row 3c, §8b.2 — the half of G1 that `INTERFACE.md` §2.6's answer to mechanism 4 rests on, and that nothing asserted)* | **4** |

**C1 — `consumers` (9).** Mechanism **C**.

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
| C1-09 | **a consumer whose gate IS a predicate gates on that predicate** — and `retire` on it refuses `live_consumers`. *(Row 3c, on a fully capable backend: `consumers("commentable")` returned `gates_on: []` and filed the consumer of `commentable` under **`would_drop`** — backwards — and the predicate was then retired with no refusal. "Which consumers gate on this?" has two answers and v0 computed one; a predicate is never a member of itself)* |

**C2 — `predicates` (6).** Mechanisms **4** (defensively) and the `ROADMAP.md` kill row.

| id | asserts |
|---|---|
| C2-01 | the extent is **derived**: writing membership touches only the member's rows; the predicate's own record is unchanged, and no consumer-membership table exists |
| C2-02 | `indexes_membership=False` ⇒ `extent=[]` **with `extent_size=None`** and a `why` — never `extent_size=0` |
| C2-03 | `of=` returns only predicates that type satisfies |
| C2-04 | `include_retired` |
| C2-05 | a predicate is not a supertype: membership of `commentable` implies nothing about `searchable` |
| C2-06 | **`extent` and `of=` resolve the IDENTITY, not the written word** (ruling **R54**, §5.2, row 4d). After `merge(commentable → searchable)`, a type declaring the **absorbed** word is a member of the survivor's extent and `predicates(of=it)` answers `known=1`. *(It answered `known=0` — §5.2's own named failure mode, an empty answer read as a confident zero, reached by two ordinary governance acts. The GUARDS are untouched: they compare the two written words, because asking whether one identity equals itself is circular.)* |

**C3 — `resolve_type` (16).** Mechanisms **2**, and **1** as the gate.

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
| C3-11 | **a retired name with a live successor resolves to the successor** — registry-guaranteed, down both lifecycle paths and whatever resolver is supplied. *(Row 3c: §5.10's "the old word still resolves" was kept only by accident — a merge writes an alias and the shipped resolver happens to score it 1.0. `retire(successor=)` writes no alias, and §2.6's production path is a caller's own resolver, so one fact had four answers and three were wrong)* |
| C3-10 | **a retired name is named in the resolution**, with its `retire_reason` and `successor`, and listed in `alternatives` with a `None` score — never a bare *"nothing fits"*. *(Row 3c: `resolve_type` read the tombstone and discarded it, answering with a confident negative about a word it knew was burned — Rule U, in the call designed against mechanism 2)* |
| C3-12 | **a word taken in another namespace is found when the caller asks** (`INTERFACE.md` §5.3.1, ruling **R6**): the default `search_namespaces=None` reads nothing and still reports `complete=False`; naming a namespace lands the taken name in `alternatives` as `"<namespace>:<name>"` and in `reason`, **without** changing the outcome; and `complete` is `True` only once every namespace that has a type in it was named, with the omitted ones named by name when it is not. *(Row 3e. This is UC3's W1.3 verbatim — `status` registered in `dpr`, asked for in `oti_311`, answered *"nothing in the vocabulary fits"* with an empty `alternatives` while the same context in `dpr` returned `existing` at 1.0. Mechanism **2** reintroduced by §2.6's answer to mechanism **4**, in the call designed against mechanism 2.)* |
| C3-13 | **a truncated page cannot support a completeness claim** (`INTERFACE.md` §5.3.1 rule 8): against a backend that caps an unlimited query and says so, `complete` is `False` and `why_incomplete` carries the backend's own reason. *(Row 3e, first adversarial round. `TypePage.complete` exists for exactly this and `_extent` had honoured it since v0; the cross-namespace search read the records and ignored the flag — harmless while `Resolution.complete` was hard-wired `False`, not harmless once R6 made it a claim. Observed: five types in one namespace, a cap of two, the exact match at row four, answered `complete=True`.)* |
| C3-14 | **an identity claim is re-verified where it is MADE — the Q56 default** (§5.3, row 4d). A retired predicate redirected to its live successor still answers `existing` at confidence **1.0**, and when the two extents that claim stands on no longer agree the returned entry carries **`identity_stale`**; when they still agree it carries nothing. Both halves, on all three legs. *(The kill row's sixth trip: every identity guard compares extents at WRITE time and this call grants 1.0 at READ time. Rule U's fourth operand — STALE is not equal. The negative is the half a careless fix breaks: a warning that never turns off is noise, which is row 4c's own `predicate_requires_review` lesson.)* | **kill row** |
| C3-15 | **a vocabulary curated TWICE still resolves** (§5.3, row 4d round 2): after `retire(a, successor=b)` then `retire(b, successor=c)`, `resolve_type(a)` answers `c` at **1.0**. It read ONE successor, so the second curation pass lost §5.10's *"the old word still resolves"* while `list_types(predicate=)`, `predicates(of=)` and R55's warning all said the identity was live — one store, two contradictory answers. Capped and cycle-guarded. |
| C3-16 | **the successor walk never RAISES, and says when it stopped** (§5.3, row 4d round 3): the lookups omitted `kind=`, and `get_type` with no kind raises on a word registered under two kinds — which PACKAGE §4.1 blesses and `C0-11` pins — so three ordinary calls threw `AmbiguousKind` out of the call designed against mechanism 2. And past `_IDENTITY_CHAIN_CAP` the answer said *nothing ACTIVE fits this* while blaming namespaces; the cap is now named in `reason` and `why_incomplete`, as `_identity_closure` and `list_types` already did. |

**C4 — `propose_type` (14).** Mechanism **1**.

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
| C4-10 | **`created_by="derived"` is reachable and distinct** (`INTERFACE.md` §2.1, ruling **R17**): an actor of `derived:<rule>` lands `created_by="derived"`, while `ai:`, `seed`/`import:` and a plain actor still land `ai`, `seed` and `user`. *(Row 3e. Two unrelated fixtures reached for the same missing value — beacon's `EntityMention.match = "deterministic"` and UC3's BBL join, which had to claim `user` for a join no user performed. `import:` stays `seed` on purpose: an import arrives already decided, a rule decides now.)* |
| C4-11 | **a declared predicate whose identity has MOVED is warned, never refused** (ruling **R55**, §5.4, row 4d): `predicates=["commentable"]` after `commentable` was merged into `searchable` returns `warnings: ["declared_predicate_merged:commentable:searchable"]` and the declaration **stands**. A live unmerged predicate, and a predicate naming no row at all, carry nothing. *(Neither write door validated its `predicates` list against anything; R54 makes the declaration visible in the survivor's extent, this makes it announced at the door.)* |
| C4-12 | **the word is re-checked at the WRITE, and a partial look says so** (§5.4, row 4d round 1). (a) A proposal made while a word was free and approved after a merge or an import took it is refused `alias_collision` at `approve` — **ruling R40 forces every predicate down that two-step path**, so the guard was structurally unavailable for the one kind the kill row is about. (b) A collision scan over a page the backend declared PARTIAL carries `alias_check_incomplete:<why>` and **still creates the proposal**: refusing would ban the call on every paging backend, which is what `C3-13` caught. |
| C4-13 | **two legal NAMES that are one word cannot both go live** (§5.4, row 4d round 2): `commentable` / `commentable_` and `bike_lane` / `bike__lane` are all `NAME_RE`-legal and all one `identity_key`, so the resolver scores each pair 1.0. Refused `alias_collision` at `propose_type` and at `import_types`, non-overridably — mechanism 4 with **no alias, no merge and no retirement**. The narrowing is asserted: PACKAGE §4.1's one word under two KINDS stays legal. |
| C4-14 | **a word the key cannot read is not the same word** (§5.4, row 4d round 3): `identity_key` maps every word with no ASCII alphanumerics to the empty string and `difflib` rates two empty strings 1.0 — so an alias 状态 made `resolve_type(类型)`, a DIFFERENT word, answer at 1.0, **and** the second agency's legitimate 类型 was then refused `alias_collision`. The identity function was manufacturing mechanism 4 instead of preventing it. An empty key is never equal to anything. |

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

**C6 — `list_types` (9).** Mechanism **2**.

| id | asserts |
|---|---|
| C6-01 | `complete=False` whenever any filter suppressed rows — including the default `include_retired=False` |
| C6-02 | `known` counts the returned set, and is `None` (not `0`) when the backend cannot count |
| C6-03 | `predicate=` returns the extent, and matches `predicates(of=…)` in the other direction |
| C6-04 | the true census — `include_retired=True, status=None, namespace=None` — reports `complete=True` |
| C6-05 | `orphaned=True` **excludes** types whose `orphaned` is `None`; the count of excluded-as-unknown is reported |
| C6-06 | `unverified_semantics=True` enumerates exactly the entries carrying the warning |
| C6-07 | **the census spans namespaces and a scoped listing says it did not:** `namespace=None` returns one word's three scoped entries with three definitions and `complete=True`; `namespace="dot"` returns one with **`complete=False`** and a `why_incomplete` naming the namespace *(row 3c, §8b.2)* |
| C6-08 | **`predicate=` names an identity, and it is resolved PER NAMESPACE** (ruling **R54**, §5.6, row 4d). Asking by the survivor finds the type that declared the absorbed word; asking by the absorbed word finds the type that declared the survivor; the default `namespace=None` gets the same answer through one bounded `name_in` lookup rather than a census; **and a second namespace's identical word is untouched**, because an identity is per `(namespace, kind)` and collapsing across one would be §2.6's answer to mechanism 4 deleting itself. |
| C6-09 | **an identity written only as an ALIAS is found both ways** (ruling **R54**, §5.6, row 4d round 2): `import_types` writing `aliases:["borough_scoped"]` onto `geo_scoped`, with no row of that name, makes `list_types(predicate="borough_scoped")` return the survivor's members. It returned `[]`, `known=0` — a confident zero, while three other doors said the two words are one identity. `C6-08` could not catch it because it builds every identity with `merge_types`, and a merge writes a ROW. |

**C7 — `usage` (7).** Mechanism **3**.

| id | asserts |
|---|---|
| C7-01 | `counts_usage=False` ⇒ `count=None` with a `why` — **never `0`** |
| C7-02 | `timestamps_usage=False` ⇒ `last_seen=None` — **never "never"** |
| C7-03 | **`last_seen` unknown ⇒ `orphaned=None`, never `False`** — contortion 2's test |
| C7-04 | `status="active"` + `last_seen < now - window` ⇒ `orphaned=True`, and `window` is reported |
| C7-05 | `get_usage` returning `None` (nothing recorded) and returning `count=None` (not counted) produce **different** `UsageReport`s |
| C7-06 | `record_use` on a non-counting backend is a no-op and `usage()` says so |
| C7-07 | **`last_seen` never moves backwards**: a late or replayed `record_use` stamped with an older time leaves `last_seen` where it was. *(Row 3c: §3.4 primitive 12 states `max(last_seen, at)` unconditionally and nothing tested it; an adapter that overwrites instead passed the whole suite. **Not** the G3 carve-out — G3 waives serialisation under a race, not the `max()` semantic — and a regressed `last_seen` reports a live type as orphaned, which §5.7 calls the sensor for the venture's core bet)* |

**C8 — `provenance` (6).** Mechanisms **1** and **3**.

| id | asserts |
|---|---|
| C8-01 | missing evidence is `[]` — never a reconstructed narrative |
| C8-02 | `history` is append-only: after a correction, no prior event's bytes changed |
| C8-03 | `approved_by` on an auto-approved entry has the form `auto:<policy>` |
| C8-04 | an imported row carries `unknown:imported`, never null |
| C8-05 | `model_tier` is never overwritten by a later approval or amendment |
| C8-06 | **`source_version` is the SOURCE's version and round-trips from proposal to provenance** (`INTERFACE.md` §2.4a, ruling **R21**): supplied to `propose_type`, readable on the `Proposal` before approval, present on `Provenance` after it, and `None` — never invented, never our own timestamp — when no caller supplied one. *(Row 3e, §10b.5 contortion 12. `EdgeProvenance` had the field and `Provenance` did not: two shapes for one concept, which is the drift the drift-check exists to catch, pointing inward.)* |

**C9 — `retire` and `reinstate` (25).** Mechanism **3**.

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
| C9-09 | **the round trip, and the classifier shape**: propose → approve → retire → `reinstate`, and `resolve_type` on the name is back to `existing` at confidence `1.0`. The retirement is **cleared from the live row and kept in the history** — the `reinstated` event carries `retire_reason`, `retired_by`, `retired_at` and `successor`. *(Row 3e, `INTERFACE.md` §5.9b, ruling **R11**. Row 3c's round 8 found `resolve_type` answering *"nothing in the vocabulary fits"* about a word it had just read the tombstone of; a name that still read as burned after being brought back is the same wrong answer pointing the other way.)* |
| C9-10 | **`successor_active`, the twentieth `Refusal.reason`**: reinstating a word whose retirement named a successor that is **itself active** is refused, non-overridably, with the path back named in `detail`; retiring the successor first then lets the reinstatement through. *(Row 3e. Two live words on one meaning is mechanism **4** arriving through the lifecycle.)* |
| C9-11 | **`reinstate` is refused where it cannot be recorded, and never no-ops silently**: on `stores_events=False` it returns `Refusal("cannot_record_override")` with the fields it would have cleared in `detail`, and nothing is written; on a type that is **not** retired it returns the entry carrying `reinstate_no_op:not_retired`. *(Row 3e. This is the only call in §5 that REMOVES a lifecycle fact from the live row, so §3.6's rule applies to it — and the second half is ruling R4's rule that a call which quietly did nothing is mechanism C committed by the registry. Needs `indexes_membership` as scaffolding: on a store that cannot compute an extent there is no way to reach a retired row at all, `C9-07` + `C9-08`.)* |
| C9-12 | **`reinstate` refuses to manufacture two live words for one meaning** — `Refusal("alias_collision")`, the twenty-first reason (`INTERFACE.md` §5.9b). *(Row 3e, first adversarial round, reproduced on the UC3 fixture: merge `bike_lane` into `cycle_track`, retire `cycle_track`, reinstate `bike_lane`, reinstate `cycle_track` — four ordinary calls ending with both active and `cycle_track` still holding `bike_lane` as an alias, with no refusal and no warning. `merge_types` refuses by default and `propose_type` on a live type's alias returns the tombstone; `reinstate` was the one door left open to mechanism 4, in the registry whose thesis is detecting it. Both directions of the collision are checked, because either side of a merge can be the one coming back.)* |
| C9-13 | **the successor relation is checked through the CHAIN, not one hop** (`INTERFACE.md` §5.9b): following the path back `successor_active`'s own `detail["path_back"]` names — retire the successor, then reinstate — is refused at the last step with `alias_collision` / `relation="predecessor"`. *(Row 3e, second adversarial round. `retire(successor=)` writes no alias, and `reinstate` CLEARS `successor` off the live row, so a one-hop check on that column checks a fact the call itself deletes. `C9-10` stopped one call short of this.)* |
| C9-14 | **the chain is transitive and the scan is namespace-scoped**: `retire a→b; retire b→c; reinstate a` is refused with `collides_with=c`; and the identical word live in ANOTHER namespace is **not** a collision, because §2.6 makes that the state scoping exists to preserve. *(Row 3e. A mutation dropping the namespace filter ran the full suite green.)* |
| C9-15 | **`reinstate` says when it could not look, and when it is not yet durable**: `stores_aliases=False` and a backend that pages both yield `reinstate_alias_check_unavailable:<why>` on the returned entry; a `transaction_scope="savepoint"` adapter yields `not_durable_until_host_commits:<why>`. *(Row 3e, second adversarial round — three separate mutations of `reinstate` ran the whole suite green, including one that dropped ruling R5's durability sentence from the fourteenth call.)* |
| C9-16 | **a merge the guard can only see in EVENTS still blocks**: an ordinary `import_types` of the survivor wipes the alias a merge wrote, and the collision is still refused. *(Row 3e, third adversarial round. The alias column was the guard's only evidence for a merge, and one ordinary call erases it -- so the succession graph now reads `merged` events as well as `retired` ones, which is the record neither call can overwrite.)* |
| C9-18 | **`retire(successor=)` takes `merge_types`' IDENTITY guards**, refusals #2 and #3, non-overridably and `force=True` included. `resolve_type` on a retired name returns its successor at confidence 1.0 (`INTERFACE.md` §5.3), so retirement-with-a-successor performs the collapse a merge performs — and row #6's **third** adversarial round reproduced `ROADMAP.md`'s kill row through it: the pair `merge_types` had just refused non-overridably under all five acknowledgements collapsed here with **no refusal, no acknowledgement and no warning**, across kinds too. The guard is narrow and this id pins both halves: a plain retirement still works, and so does one whose successor shares a **non-empty identical** extent |
| C9-19 | **a non-overridable guard is never reached through an overridable one** (row 4c, found by [`check_merge_guard.py`](../tools/check_merge_guard.py)). Row 3c moved `merge_types`' `cannot_record_override` check to *after* its four non-overridable refusals for exactly this reason; `retire` had the same defect the other way round, so on `indexes_membership=False` a predicate retirement-with-successor was refused **`no_consumer_evidence`** — which advertises `force=True` — while the true answer was `predicate_merge`, which never moves. The outcome was safe and the STORY was wrong, and the story is what a caller acts on. Third instance of one class; the kill row's first trip was its dangerous form | **kill row** |
| C9-20 | **§5.10's refusal #1 transfers to a successor, and `force` does not move it** (row 4c, round 3). `C9-18` gave this call refusals #2 and #3 on the argument that *"the two guards that transfer are the two about IDENTITY rather than evidence"* — which filed `different_consumer_sets` under evidence, though §5.10's own rationale for it (*"merging asserts that every consumer of one accepts the other"*) is an identity claim and its table says *"No. Not by `force`, not by `acknowledge`"*. **[Observed]** a pair refused under all seven acknowledgements, collapsed by `retire(successor=, force=True)` | **kill row** |
| C9-21 | **a consumer's `gate` and a type's `usage` follow the identity** — ruling **R38** was ruled *for both documents* and shipped for one call (row 4c, round 3). A live gating consumer of an absorbed predicate was filed under `would_drop` **with no warning** and `retire(survivor)` then succeeded with **no `live_consumers`** — the row-3c defect `_consumer_report` calls *"the exact opposite of the truth"*, one axis along; and 500 uses under the absorbed word left the survivor reading `count=0, orphaned=True`, in the call §5.7 names *"the sensor for the venture's core bet"*. `record_use` still writes the word the caller used; the **report** sums the identity | **C** |
| C9-17 | **the collision scan pages to exhaustion**: against a backend that pages honestly -- partial **plus** a cursor -- a collision on page two is still found. *(Row 3e, third adversarial round. §5.9b claims the scan reads to exhaustion and nothing checked it: `C9-15`'s double returns no cursor by design, so a mutation replacing `next_after` with `None` ran the whole suite green while silently turning a refusal into a warning.)* |
| C9-22 | **the kill row's SEVENTH trip — a successor that does not exist YET** (§5.9, row 4d round 1): `retire(successor=)` refuses **`successor_unregistered`**, non-overridably and with `force=True`, because every one of §5.10's identity guards is evaluated against the successor's ROW and a word that does not exist gave all three nothing to compare — after which the word was created by an ordinary proposal and `resolve_type` cashed the redirect at 1.0. Narrowing asserted: register the successor first and the guard answers on the merits. | **kill row** |
| C9-23 | **`reinstate` asks the collision question its sibling asks** (§5.9b, row 4d round 1): a row retired carrying an alias that a LIVE entry has since come to answer to is refused `alias_collision` non-overridably. Row 4c gave this call §5.10's EXTENT guards over its dormant aliases and never §5.9b's COLLISION question, which `import_types` asks on the same field. Four ordinary calls. | **kill row** |
| C9-24 | **`reinstate`'s MIRROR case, and a word is not its own successor** (§5.9/§5.9b, row 4d round 2): the row coming back may carry no aliases while ANOTHER live row holds ITS NAME as one — the shape `import_types` writes — which round 1's `if dormant:` fence never reached. And `retire(X, successor=X)` is refused: a tombstone that redirects to itself is a claim nobody made. |
| C9-25 | **a retired successor leaves the old word resolving to NOTHING** (§5.9, row 4d round 3): refused `retired_operand`, **overridable by `force`** exactly as §5.10's is, because the outcome is a loss rather than a false claim and a steward may mean it (`C17-45` does). `merge_types` has always refused the identical act; this door did not ask. |

**C10 — `merge_types`, and the doors its operands come through (19).** Mechanism **4**.

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
| C10-09 | **two EMPTY extents are not a byte-identical extent.** `C10-02` pins the case where two predicate extents *differ* and row 3c closed the case where they cannot be *computed*; nothing pinned the case where they are both empty, and `set() == set()` — so two predicates nothing satisfies compared identical, guard 2 did not fire, and the merge fell through to the overridable guards. Reproduced end to end by row #6's second adversarial round: two `ai:`-proposed predicates auto-approved at Haiku, then merged under two acknowledgements. **`ROADMAP.md`'s kill row, tripped in test for the second time in this project's life and closed the same day.** An empty extent is *no evidence of membership*, not *evidence of identical membership*. A non-empty identical extent still merges |
| C10-10 | **a predicate proposal never takes the auto path** (ruling **R40**, row 4c) — `propose_type(kind="predicate")` returns a pending `Proposal` whatever the namespace's `approval_policy` says, warning `predicate_requires_review`, and an `entity` in the same namespace under the same policy still auto-approves. **Belt-and-braces over `C10-09` and `C9-18`:** those guard the merge, this guards the door its operands came through, and two of the three kill-row trips began with a predicate that went live without a human. On `stores_proposals=False` there is nowhere to hold one, so the entry is written and carries the warning — the one place the ruling cannot be honoured, made enumerable rather than silent | **kill row** |
| C10-11 | **`ROADMAP.md`'s kill row, FIFTH trip** — a **PARTIAL** extent is not an identical extent (row 4c, first adversarial round). Rule U's third operand: row 3c fixed *unknowable is not equal*, row #6 r2 fixed *empty is not equal*, and `_extent` read **one page** while every guard discarded the `why` that said so. **[Observed]** on this repo's own honest-paging double, two predicates whose FIRST PAGE matched compared equal and `merge_types`, `retire(successor=)` and `import_types` all performed the collapse. Two backends, two defences: an honest **page** is answered by paging to exhaustion, a **truncated** answer by folding `_extent`'s `why` into `knowable` — and the guard is still narrowed, not banned | **kill row** |
| C10-12 | **`predicate_requires_review` marks the unreviewed and only them** (ruling R40, row 4c r1). The value's job is to make *"a predicate went live without review"* enumerable, which is Q50's whole subject — and it rode onto every **approved** predicate and stayed, so a reviewed entry and an unreviewed one read identically. Four states asserted; `import_types` also puts a live predicate in and now says so | **kill row** |
| C10-13 | **`ROADMAP.md`'s kill row, SIXTH trip — four doors, one root cause** (row 4c, round 3). Trips 1–5 were *the guard did not look properly*; this is *the guard looked correctly and then the fact changed*. Guard #2 compares two extents and says nothing about `left.aliases`, which the same write re-points at `right` — so two individually legal merges plus ordinary vocabulary growth made `resolve_type(A)` answer `C` at 1.0, a pair refused non-overridably when asked directly. Rule U's fourth operand: **STALE is not equal** | **kill row** |
| C10-14 | **Door 1's store, read — the Q56 default at the ALIAS door** (§5.3, row 4d). After `merge(commentable → searchable)` over identical extents and one new type declaring `searchable`, `resolve_type('commentable')` still answers `searchable` at **1.0** and now carries **`identity_stale`**; the same store before the divergence carries nothing, and an alias hit on two non-predicates carries nothing and reads no extent. *(`C10-13` closes Door 1's WRITE; this closes the read the write left behind.)* | **kill row** |
| C10-15 | **the kill row's SEVENTH trip — one word is not one string** (row 4d round 1). The guards found their collision by an exact BYTE comparison while the resolver scored `identity_key(candidate)` against `identity_key(alias)` and rated an exact match **1.0** — so `aliases: ["Commentable"]` was written unrefused where `["commentable"]` is refused `predicate_merge`, and `resolve_type('commentable')` answered at 1.0 over differing extents. Every spelling now gets one verdict; a genuinely different word still does not. | **kill row** |
| C10-16 | **the same trip's READ half**: `identity_stale` survives every spelling, and `min_confidence`, `kind=` and `search_namespaces` are none of them an escape. The gate was `candidate in entry.aliases`, an exact-string test on a redirect the resolver reached by NORMALISING — and a raw column header is the production shape of this call. | **kill row** |
| C10-17 | **`retire(successor=)` validates the aliases its successor INHERITS** (row 4d round 2, found by `check_merge_guard.py` within a minute of the chain fix). Door 1 with a different second act: `retire` writes no alias, so it was out of reach while `resolve_type` took one hop — and following the chain re-pointed every alias the retired row carries, uncompared. `merge_types` has carried this guard since `C10-13`. | **kill row** |
| C10-18 | **the fifth identity guard answers above the capability gate** (§5.10, row 4d round 2): on `stores_events=False` an acknowledging caller is told `predicate_merge`, non-overridably — not that the audit log is missing. Round 1 moved this check above the three overridable guards and stopped one short of `cannot_record_override`, which is `C9-19`'s defect class inside the fix for `C9-19`'s defect class. |
| C10-19 | **the kill row's EIGHTH trip — a retired name reused under another spelling** (row 4d round 3). §5.4's *a retired name is not reusable* was a BYTE comparison, and round 2's keyed guard scans ACTIVE rows only — so `commentable_` retired, then `commentable` proposed and approved, then `resolve_type('commentable_')` at **1.0** over extents `merge_types` refuses non-overridably. Both write doors hand back the tombstone; a genuinely different word is still free. | **kill row** |

**C11 — `register_consumer` / `record_use` (5).** Mechanism **C**.

| id | asserts |
|---|---|
| C11-01 | a consumer round-trips with `on_unknown`, `owner`, `locator` intact |
| C11-02 | a consumer may gate on a predicate that does not exist; it registers, and the type shows up in `would_drop` |
| C11-03 | `record_use` advances `last_seen` when `timestamps_usage=True` |
| C11-04 | a read-only consumer source (a config file) ⇒ `register_consumer` returns a refusal, never a silent no-op |
| C11-05 | **a gate naming no registered predicate raises `gate_unregistered:<gate>`** in `ConsumerReport.warnings`, and `would_drop` still lists the consumer. *(Row 3d, ruling **R8**. `C11-02` says such a registration must be accepted — it IS mechanism C — but the report then read as a fact about a live gate: `would_drop` implies *the extent excludes this type*, when the truth is that there is no extent and **every** type would drop. A registered-but-retired predicate raises nothing: the tombstone is an entry. `INTERFACE.md` §5.1)* |

**C12 — Foundry import mapping, and the fourth door into the kill row (18).** From 0.3 consequence 2 / `INTERFACE.md` §2.5.

| id | asserts |
|---|---|
| C12-01 | `experimental` ⇒ **`active` plus predicate `experimental`** — never `proposed` |
| C12-02 | `deprecated` ⇒ `retired` with `retire_reason="imported: foundry deprecated"` |
| C12-03 | `apiName` and `rid` land in `provenance.imported_from`, not in fields of our own |
| C12-04 | `visibility` and `groups` land in `attributes` |
| C12-05 | **an import does not un-retire a local name**: `import_types` over a name this deployment retired returns the retired entry with `name_previously_retired` and writes nothing. *(Row 3e, second adversarial round: it used to overwrite the tombstone — status, `retire_reason`, `retired_by`, `retired_at`, `successor`, `created_by`, definition and provenance — in one call, with none of §5.9b's three guards and no `reinstated` event. A fourth door into mechanism 4, and it falsified §5.9b's own claim that there were none.)* |
| C12-06 | **an import does not retire a type something still gates on**: the mirror of `C12-05`, refused with `import_refused:live_consumers` and nothing written. *(Row 3e, third adversarial round. `retire()` refuses `live_consumers`; the identical act through a Foundry `deprecated` row succeeded with no refusal, no warning and no `retired` event, bypassing §3.6 on every backend.)* |
| C12-07 | **`source_version` survives the import** (`INTERFACE.md` §2.4a, ruling **R21**) — the ingestion path is UC3's actual wedge, and §10b.5's finding is precisely that a dump's own version had nowhere to go. *(Row 3e, third adversarial round: dropping it from `import_types` ran the whole suite green.)* |
| C12-08 | **`ROADMAP.md`'s kill row, FOURTH trip** — an imported `aliases` row cannot collapse two predicate identities. Found by [`check_merge_guard.py`](../tools/check_merge_guard.py)'s caller enumeration on its first run, which is the artefact row 4c was told to build *instead of a fourth patch*. **[Observed]**: two live predicates with different non-empty extents, `merge_types` refusing them non-overridably, one retired by an ordinary act, and `import_types` then writing it as an alias of the other with **no refusal and no warning** — `resolve_type` going from `proposal / None / 0.4762` to `existing / searchable / 1.0`. `alias_collision` could not see it: it refuses a **live** entry's name, and a retired predicate name still resolves and still has an extent | **4**, **kill row** |
| C12-09 | **and an imported alias between two identical non-empty extents is still written** — the half a careless fix deletes. §5.10 refusal #2 permits that collapse (`C10-09` narrowed the guard rather than closing the operation), so a fix that refused every predicate alias would pass a suite asserting only refusals while removing a legal write | — |
| C12-10 | **the identity guard survives a word registered under two kinds** (row 4c r1). §4.1 blesses one word under two kinds and `C0-11` pins that `get_type` with no `kind` **raises** there — row 4c's new guard called it that way, so a dump whose alias named a two-kind word blew `AmbiguousKind` out of `import_types`, a call whose contract is *"it returns entries, not refusals"*, aborting the batch with earlier rows committed. Also: a refused import carries the **row's** `kind`, not a hard-coded `entity` | — |
| C12-11 | **the same warning at the second write door** (ruling **R55**, §2.5, row 4d): an imported row declaring a merged-away predicate is **written**, and carries `declared_predicate_merged:<declared>:<identity>`; one declaring a live predicate does not. An import is a vocabulary arriving already decided, so warning is all this call may do about a declaration. |
| C12-12 | **the row's own NAME is a word too** (§2.5, row 4d round 1): an imported row whose name a live entry already answers to is refused `import_refused:alias_collision`, carrying no aliases of its own. The alias block ran only `if incoming:`, so this door never asked — while `propose_type` refuses the identical act. `C16-06`'s whole-store invariant, in one ordinary import row. |
| C12-13 | **a legal import is not banned by a backend that PAGES** (§2.5, row 4d round 2): a row carrying a brand-new, unheld alias is **written** on `page_cap=3`, with the truncation reported exactly once. Round 1 replaced a one-row `name_in` probe with an unfiltered namespace scan and fed its partial `why` into a NON-OVERRIDABLE refusal — so the ingestion wedge came back `import_refused:kind_mismatch`, a legal row refused with a reason naming two kinds. The guard is narrowed, not banned, for the third time in one row. |
| C12-14 | **the kill row's NINTH trip**, found by the review ruling **R53** and the seventh-trip countersignature say those guards never got. `_alias_identity_breach` read the row being aliased ONTO to compare consumer sets -- and `import_types` creates that row in the same call, so with none to read the guard compared the *other* row against **itself** and §5.10's refusal #1 was equal by construction. Two predicates with non-empty IDENTICAL extents (so #2 passes honestly) and different gate sets collapsed at confidence 1.0, on a pair `merge_types` refuses non-overridably under all five acknowledgements. **The fix is a COMPUTED set, not a refusal**: the incoming row declares its own `predicates`, so its consumer set is a fact rather than an unknown | **kill row** |
| C12-15 | `C12-14`'s narrowing: an import creating a row whose computed consumer set MATCHES the word it aliases is **still written**. Every guard fix in this repository ships with this assertion beside it, because *refusing everything passes a checker that only tests refusals and deletes a legal operation* | — |
| C12-16 | **the kill row's TENTH trip**, found by round 2's fix-auditor lens pointed at round 1's own fixes. `C12-14` computed the incoming row's consumer set **on one branch only**; where the aliased-onto row already existed the guard read `_consumer_report` off the STORED row — *the row `import_types` is about to overwrite* — so it evaluated a state the call destroys and gave **two different answers for one final state** depending on whether the name happened to exist. It is the SIXTH trip's diagnosis (*a guard written for one call over a fact more than one call can change*) applied to a **fix** rather than to a guard, which is also the EIGHTH's shape. Refusal #1 now compares the sets the write will produce, on both branches | **kill row** |
| C12-17 | **the kill row's ELEVENTH trip.** Refusal #1's operand was passed at **one of `_alias_identity_breach`'s four call sites** — `retire(successor=)`, `reinstate` and `merge_types` all called it bare — so `_gates_on`'s `member_of` was empty and every consumer gating on a predicate the target itself declares was invisible. Through `reinstate`, in seven ordinary calls with refusal #2 passing honestly throughout: the alias is imported **legally** while both gate sets are empty, goes dormant, the world moves, and the reinstatement makes it answer at **confidence 1.0** on a pair `merge_types` refuses non-overridably. **The sixth trip's diagnosis applied to a FIX for the third consecutive round** — trip 9 the missing operand, trip 10 one branch of two, trip 11 one call site of four | **kill row** |
| C12-18 | `C12-17`'s narrowing, in ruling **R64**'s shape: `declared_predicates` is a **required keyword**, so a fifth caller cannot arrive bare. Asserted by signature rather than behaviour, because the thing pinned is that **there is no default to fall back to** — a behavioural test would pass just as happily with one | — |

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

**C15 — the `attributes` mechanism (13).** §5 of this document.

| id | asserts |
|---|---|
| C15-01 | with no schema registered, behaviour is byte-identical to `INTERFACE.md` §2.1 — opaque, unread, unvalidated |
| C15-02 | the census records every key written, in `off` mode, and reports the `attr_schema_version` spread *(see §5.5 — not yet part of the conformance definition)* |
| C15-03 | `warn` adds `attributes_invalid:<field>` and does **not** refuse |
| C15-04 | `enforce` returns `Refusal("attributes_schema_violation")` with the offending field in `detail` |
| C15-05 | a v2 schema with a new required field does **not** invalidate v1 rows; they read back verbatim with `attr_schema_version=1` |
| C15-06 | under `enforce`, a `value_set` without a declared `ordering` when `ordered=True` is refused — the CMS severity case |
| C15-09 | **a projected key is censused, and the census says it is partial** (§5.7): on a backend with `stores_attributes=False` and a declared projection, `attribute_census` lists the projected key with `complete=False` and a `why_incomplete` naming what it counted. *(Row 3d, beacon finding **U3**. The census used to refuse outright on `stores_attributes=False` and return `entries=()` — a confident wrong answer on a backend that had written the key, in the one call whose job is making the escape hatch enumerable.)* |
| C15-08 | **declining the optional `AttributeStore` extension leaves a backend conformant** (§5.5, ruling R2): `attribute_census` returns `entries=()`, `known=None` — never `0` — `complete=False` and a `why`, and attributes still round-trip. *(Row 3c. §5.5 and `2A-RUN.md` D-2 both said so and it was false: four C15 tests called `register_attribute_schema` unguarded, and `DegradedAdapter` re-declared the four extension methods unconditionally, so the tool built to construct degraded backends could not construct the one optional capability that is a **protocol** rather than a flag. Row 3d note: this row was missing from this table although the test existed and `test_manifest.py` counted it — found by an adversarial reviewer building from the document alone.)* |
| C15-07 | **one schema per kind cannot serve both CMS `value_set`s:** with `ordering` required, `deficiency_corrected_status` is refused for lacking an order it has no business having; with `ordering` optional, `scope_severity_code` may be created claiming an order and declaring none — the pollution §5.1 says the mechanism exists to prevent. Both horns asserted. *(Row 3c, §5.6 — a limitation of the mechanism, not of any backend)* |
| C15-10 | **a name-level schema shadows the per-kind one** (§5.2b, ruling **R10**): with the strict per-kind schema in force, `scope_severity_code` still obeys it and `deficiency_corrected_status` is still refused **by it** (`detail["schema_name"] is None`); registering a `(namespace, kind, name)` schema for that one name lets it through **judged by its own fields**, and the per-kind schema's `required` `ordering` does **not** come along — shadowing is replacement, never merge. *(Row 3e. `C15-07`'s two horns, closed on CMS's own two value sets.)* |
| C15-11 | **the per-kind schema still governs every name without an override** (§5.2b rule 2): a third `value_set` with no override is refused by the per-kind schema, and the refusal names which schema refused it. *(Row 3e. The failure mode a name-level key invites is that one exception quietly relaxes the kind; this is the test that would catch it.)* |
| C15-12 | **an override may not weaken the kind, and the census says when `declared` depends on the name** (§5.2b rules 3 and the tri-state table): a name-level schema with `mode="off"` and no fields under an `enforce` kind still refuses; and a key only a name-level schema declares comes back `declared=None` with a `declared_why` naming it. *(Row 3e, first adversarial round. The first cut shadowed `mode` and `additional` with the fields, so an override was a one-line opt-out of a kind's governance; and `declared=False` was a confident negative about a key that is required somewhere — Rule U, on the CMS fixture R10 exists for.)* |
| C15-13 | **a plain string attribute survives the census on every leg** — a string, an int, a list and a dict written as `attributes` and read back through `attribute_census`. *(Row 4c. **[Observed] on `main`**: one type with `attributes={"note": "a plain string"}` made `attribute_census()` raise `JSONDecodeError` on the **Postgres** leg and only there — every `*_json` column there is `jsonb`, so psycopg decodes before the dialect sees it, and the dialect re-parsed anything arriving as a `str`, which is exactly a jsonb column holding a JSON string. Nothing caught it for three rows: no test wrote a string-valued attribute and then censused it, the census is **nonbinding** under ruling R2 so it sat outside the conformance verdict, and both sqlite legs parse text correctly so the two-leg agreement had one leg that never disagreed. Found by wiring R34's edge-payload census onto the same call.)* |

**C16 — whole-store invariants (6).** *(Amended by row 3c: this said "run once at suite end, over everything the suite wrote". The shipped group is **function-scoped** — a fixture drives one store through representative write paths and each test then inspects it. Recorded at 2A as deviation D-9 and never brought inline here. It matters because "everything the suite wrote" would be a stronger claim than the tests make.)*

| id | asserts |
|---|---|
| C16-01 | every `active` entry has a non-null `approved_by` |
| C16-02 | no retired name was reused |
| C16-03 | no event's bytes changed after it was written |
| C16-04 | every list-shaped result produced during the run carried both `complete` and `known` |
| C16-05 | **every returned `created_by` is one of `INTERFACE.md` §2.1's four values, and every `status` one of §2.5's three**. *(Row 3e, second adversarial round. `Refusal.reason`, `Evidence.kind`, `Consumer.on_unknown` and `NotAType.reason` all raise on an unknown value and `created_by` did not — a third-party backend's garbage flowed straight out through `list_types`. `kind` is deliberately not checked: §2.2 makes it an OPEN vocabulary.)* |
| C16-06 | **no two ACTIVE entries in one namespace hold one word between them** — counting names and aliases together. Mechanism **4**, asserted directly. *(Row 3e, third adversarial round. `merge_types`, `propose_type` and `reinstate` each refuse to produce this state, and the loop found THREE different walks into it anyway, each closed at whichever call the reviewer came in through. This is the invariant those guards approximate, and it does not depend on guessing the next entrance.)* |

**C17 — edges: the store and the read seam (53).** `EDGES.md` v0, row 4b; **C17-35 … C17-40** by row 4c (ruling **R34**), **C17-41 … C17-43** by the same row (ruling **R37**), **C17-44 … C17-46** by the same row (ruling **R38**, which also rewrote `C17-33`), **C17-47** (ruling **R39**), **C17-48 … C17-50** by that row's FIRST adversarial round, **C17-51 … C17-52** by its SECOND, and **C17-53** by its THIRD. Mechanisms **C** (dominant, and [Observed] rather than assumed) and **4**.

*Three things shape this group.* **Ruling R31 / standing constraint 8** requires every numbered rule of `EDGES.md` §2.4.1, §4.3 and §4.4 to ship with an id that exercises it or a `prose-only` tag with a reason; the mapping is enforced by [`check_spec_drift.py`](../tools/check_spec_drift.py)'s `EDGE_RULE_MAP` and reported in [`4B-RUN.md`](../runs/4B-RUN.md) §4. **Every BLOCKING finding of row #4's own adversarial loop is an assertion here** — that loop found ten, each reproduced by running code, three of them defects in the previous round's fix, and all ten were fixed in a throwaway probe kit under `docs/tools/` that the package does not import and the suite did not know about. And **`C0-10`'s question is asked of this surface**: can a BROKEN edge backend pass?

| id | asserts | mech |
|---|---|---|
| C17-01 | **the protocol is EIGHTEEN primitives**, and `stores_edges=False` makes every edge call return `Refusal(reason="edge_store_absent")` with the backend's own sentence — **never an empty report**, because an empty `NeighborReport` reads as *"this node has no neighbours"*, which is Rule U's forbidden empty in the one call that would be believed. Its subject is the declined capability, so it does not skip on the leg that declines it | — |
| C17-02 | `EdgeRecord` round-trips; a payload key the backend cannot store comes back **absent**, not wrong, and **no warning value is minted for it** — the returned record is the signal (§3.4 primitive 4), and the type side has no warning either. Beacon finding U3, one row down | — |
| C17-03 | `put_edge` writes `status` and the retraction tombstone **as given** and validates no transition (§3.1) | — |
| C17-04 | **duplicate edges are permitted** (`EDGES.md` §6.1): two `blocks` edges between one pair, written by a human and by a classifier, are two facts with different provenance — a uniqueness constraint would force the second to fail or to overwrite, and overwriting is an edit of a provenance-bearing record. The cost is asserted too: `known` counts edges, `nodes` is deduplicated | — |
| C17-05 | **keyset pagination actually pages** — `C0-10`'s shape for `find_edges`: seven edges at `limit=3` give disjoint, ordered, exhaustive pages, a terminating cursor, and the same order as the unpaged query | — |
| C17-06 | the family filter degrades **the way `EDGES.md` §7.1 says and not the way `find_types` does**: on `indexes_edges_by_family=False` the store returns the frontier's edges unfiltered **with `complete=True`** (the query is bounded by `incident_to`, so it genuinely can answer a wider question completely) and **the registry narrows above** — the half that was specified and, in row #4's own kit, not implemented | **C** |
| C17-07 | a type-level endpoint's `NULL` instance id is a **value to match, not a wildcard**: a type node and an instance of it are two different endpoints, and `NULL = NULL` is not true in SQL | — |
| C17-08 | the **level** check runs before the **kind** check and `detail["problem"]` says which — UC2's T2.5, so a caller is not told to fix an `endpoint_kinds` declaration that is already correct. **And `equivalent_to`'s own `src.kind == dst.kind` constraint** (`EDGES.md` §3.1, rule `2.4.1-6`), which the rule table mapped to this id while the id asserted only the generic mismatch — the `problem="family_constraint"` branch was returned by the registry and asserted by nothing until row 4b's second adversarial round | — |
| C17-09 | **§2.4.1's clauses bind at DECLARATION time, at all three doors** — `propose_type`, `approve` and `import_types`. *(A round-1 reviewer of row #4 declared `same_capability` with `predicate` endpoints and wrote a predicate-to-predicate edge with no refusal — the `ROADMAP.md` kill row, through a door the document had left open while claiming it was shut. Writing the test for that exposed the same hole in the instance clause.)* *(And this row said "all three doors" while the test called two: `approve()` was named in the docstring and never invoked, found by row 4b's second adversarial round reading the test behind the claim. The third door is now walked, by writing a breaching declaration past `propose_type` onto a pending proposal — which is what a proposal made before the rule looks like.)* | **kill row** |
| C17-10 | **ruling R18**: `symmetric ⇒ inverse_label is None`, refused at `propose_type` and at `approve()`, which is the site R18 names. `INTERFACE.md` §9 contortion 1, open since deliverable #1, half closed | — |
| C17-11 | a **dangling endpoint is a fact, not an error** (§2.7) — written with `endpoint_type_unregistered` per end, never refused, because `endpoint_kind_mismatch` can only fire when the endpoint's type IS registered. An unregistered ORIGIN warns on the report and the walk proceeds: there is no `UnknownNode`, because the registry has no node store and raising would require inventing a fact | **C** |
| C17-12 | the depth cap is **2**; `0`, `3` and `4` raise `ValueError`, not a `Refusal` — a caller error, and R3's closed vocabulary does not grow a value for a typo. The cap and R13's no-paging rule are one decision | — |
| C17-13 | `edge_families=None` **spans every namespace** — *(a round-1 reviewer built two families in two namespaces on one node and each call found one: Cause C inside the only read call, on the axis UC3 exists to stress)* — and an edge whose family **nobody registered** is RETURNED with `edge_family_unregistered`, because there is deliberately no foreign key from an edge to its family and beacon's `work_links` has none either | **C** |
| C17-14 | a typo'd family, and a family registered in **another namespace**, both refuse `edge_family_unknown` for the **whole call**: a caller that names a family and gets a report back is entitled to believe it was searched | **C** |
| C17-15 | a **retired** family is searched, not refused, and the report warns `edge_family_retired:<name>` — its edges were never deleted, and a read that hid them would be deleting data by lifecycle. **Both carriers**: `add_edge` onto an already-retired family is also not refused and the returned `Edge` carries the same value, which the code emitted while `EDGES.md` §2.8's table listed one carrier — *a closed vocabulary opening by CODE rather than by prose*, found by row 4b's second adversarial round | **3** |
| C17-16 | **`direction` filters DIRECTED families only.** Six (origin, direction) combinations over one symmetric edge all return it; a directed family answers `out`→1, `in`→0; a mixed query gets both behaviours in one report. *(Round 2's BLOCKING: `neighbors(dot:borough, ["equivalent_to"], direction="out")` returned `known=0, complete=True, nodes=[]` — a confident, complete, false negative decided by which publisher wrote the edge first.)* | **4** |
| C17-17 | **a dead end is `complete=True`** with `depth_reached < depth_requested` and no `why`; truncation is the other signal. Exercised in **all three directions**, because round 1's fix was true only for `direction="out"` — the one direction the probe testing it hard-coded, and the one nobody defaults to | — |
| C17-18 | **the assembly bound counts DISTINCT edges, fires only when something was actually truncated, and is ON by default.** 19 distinct edges under a bound of 20 come back whole; **19 under a bound of exactly 19 also come back whole** — *(row 4b, adversarial round 2, BLOCKING: the check was `>=`, so an exact match reported `complete=False` with a `why` naming a bound nothing had crossed, on both backends, deterministically. That is round 3's own B7 on the one axis its fix never walked: the test exercised strictly-below and strictly-above and never `==`)* — and a tighter bound gives `known=<bound>`, `complete=False` and a `why` that says it is **not paging**. *(Round 3's B7 and B8: the bound was compared against each raw page, so a walk under budget dropped four real edges and named a bound nothing had crossed; and it was opt-in, leaving the default as the unbounded materialisation R13 exists to prevent.)* | — |
| C17-19 | the registry **exhausts the adapter's pages per level** (300 edges from 64-row pages, `complete=True`), and a backend whose cursor never advances **stops and says why** rather than looping forever. The second half is not in `EDGES.md`; it was found by implementing it | — |
| C17-20 | **retraction is an event, never a delete** — and it is **not refused** on `stores_edge_events=False`, which is a departure from §3.6 that `EDGES.md` §2.6 argues: the record IS the row, so an unrecordable retraction does not exist; what is lost is the sequence, and that is `retracted_without_event_trail:<why>`. `unknown_edge` on a missing id (**not** `edge_family_unknown`, which names a different failure); an empty reason raises; the default hides it and says `complete=False` | **3** |
| C17-21 | **every edge WRITE stamps `not_durable_until_host_commits` on its own behalf**, including `retract_edge` on an edge the host had already committed — *(round 3's B9: it inherited the warning from the edge's prior state, so that retraction came back with no warning at all, a borrowed-connection write that looked exactly as durable as an owned one)* — and **a read stamps nothing**, because a signal that never turns off is noise | — |
| C17-22 | **`complete` can be `True`, and is readable only next to `families_searched`** (ruling R12's rule, taken rather than restated): "complete" is over the families searched and over the edge store, never over the host's relationships. The shape itself refuses a `complete=True` carrying a `why` and a `complete=False` without one | — |
| C17-23 | the two corner cases §4.1 states because they were reachable and unstated: a **self-loop** counts in `known` and contributes nothing to `nodes`; **`at_depth` is a property of the edge's discovery**, so in a triangle walked from `A` the `B→C` edge is `at_depth=2` although both its endpoints were reached at depth 1 | — |
| C17-24 | **can a BROKEN edge backend pass?** Three shapes: one that silently drops `limit` (the registry must still assemble the level), one that returns a **stale `next_after`** (the loop must terminate and say the level is incomplete), and one paging small enough that the depth-2 frontier re-finds what depth 1 counted (the bound must still count distinct) | — |
| C17-25 | **two transaction scopes on one connection is non-conformant** (§6.2): `Capabilities.scope_conflict()` names it, and returns `None` when the two are genuinely two connections — which is legal and costs **G2 across the seam**, stated rather than papered over | — |
| C17-26 | an edge's history is append-only and **says when it could not be read**: `EventRecord.edge_id` carries it, `edge_provenance` assembles it, and `neighbors`/`add_edge` return `history=()` with a `why` naming the call to make — never `()` reading as *"nothing happened"*. On `stores_edge_events=False` the `why` is the backend's own sentence, verbatim. **And on `stores_events=False` with `stores_edge_events=True`** — a combination nothing forbids and neither reference backend can produce — it degrades rather than raising: `read_events` is the same primitive `stores_events` gates, and `edge_provenance` checked only the edge flag until row 4b's second adversarial round drove an uncaught `NotSupported` out of it | — |
| C17-27 | **`equivalent_to` is seeded at store creation with §3.1's exact shape**, field by field, and carries evidence and an `approved_by` — a seeded family with neither would be the registry warning about its own seed. On a `stores_attributes=False` backend the five keys do not round-trip and the test asserts *that*, rather than skipping past it | **4** |
| C17-28 | **`consumers` extends to edge families with no new call** — the test of §2.3's decision — and `no_edge_gate_registered` fires when no predicate's extent contains any edge family, so `would_drop: []` is not read as *"nothing will drop this"* when the truth is *"nobody has told us what traverses edges"*. Ruling R8's reasoning, one level along | **C** |
| C17-29 | a family that **declared nothing** is a legal `TypeEntry` and an unusable family: `INTERFACE.md` §2.1 requires no attributes and beacon's `work_link_types` rows carry none of the five, so refusing the *registration* would reject types the interface says are legal — and the write refuses `attributes_schema_violation` naming the missing `level`, which is where the door shuts | — |
| C17-30 | **`equivalent_to` between two `kind="edge"` types is WRITTEN, not refused** — `EDGES.md` §3.1's endpoint list and §2.4.1's second clause, at write time. *(Row 4b's own first adversarial round: rule `2.4.1-2` was mapped to two ids that only read the declaration, so nothing in the suite had ever written a `kind="edge"` endpoint. That is the "an id exists but does not exercise the rule it is mapped to" failure **R31** was made to prevent, inside the row that built R31's gate — and the gate is blind to it by construction, because it checks that an id exists and not what it asserts. The case is `T3.13`, which `EDGES.md` §11.3 added because §1 and §3.1 contradicted each other and no design test ran it.)* It is not reification — the instance-level clause makes an edge-about-an-edge unconstructible, asserted here — and `predicate` is still refused | **4**, **kill row** |
| C17-32 | **a caller's mistake arrives as the documented error.** `depth=1.5` sailed past the range guard and died inside `range()`; a `node` that was a plain string died on `.namespace` deep in the walk; and `edge_families="blocks"` — **a bare `str` satisfies `Sequence[str]`** — was read one character at a time and refused with `families: ["b","l","o","c","k","s"]`, which does not merely fail but misleads. §4.2 promises a `ValueError` for a caller's mistake, and a raw `TypeError` three frames down is not that promise kept | — |
| C17-33 | **a merge does not orphan an edge, and the walk says which ones it followed** (`EDGES.md` rule `4.3-14`, **rewritten by ruling R38**). `merge_types` is the sanctioned answer to mechanism **4** and rewrites no edge, so before row 4b a caller who resolved to the canonical type before walking — the CORRECT thing — got `known=0`, `complete=True` and an empty `warnings`; row 4b made that honest and left the gap open (D-4b-15, **Q33**). The walk now resolves an endpoint reference to *the identity it now belongs to*, in both directions, and every edge reached that way carries `via_successor` while `edge.src`/`edge.dst` still read what was written | **4** |
| C17-34 | **the report says which node each edge reached**, and `edges` is ordered by `(at_depth, edge_id)` as a guarantee. `EDGES.md` §9.3's worked example — the grounding bundle's `relations` slot, the reason the edge row exists — is silently wrong at hop 2 when computed the obvious way, because the far end of a second-hop edge was never incident on the origin. **Mechanism C inside the example written to prevent it** | **C** |
| C17-31 | **`find_edges` returns only records incident to the frontier**, pinned as its own subject the way `C17-06` pins the family filter — *(an adapter that ignores `incident_to` entirely was caught by four tests whose subject is something else, and "caught incidentally" is a weaker claim than "pinned")* — and the registry narrows above a store that does not, **on the default `direction="both"` as well as on `out` and `in`**, which is the branch that returned `True` unconditionally until this round | — |
| C17-35 | **an enforced payload schema refuses the edge and names which schema** (`EDGES.md` §2.5, ruling **R34**). No new `Refusal.reason` is minted — this is `attributes_schema_violation`, `PACKAGE.md` §5.3's `enforce` row reached one kind along — and `detail` carries `schema_name`, `schema_version` and the **family**, because two families in one namespace may be judged by two different schemas | — |
| C17-36 | **`warn` writes and enumerates, and the version in force is recorded on the edge.** §5.4's promise transposed: an edge written under v1 is not re-validated by v2 and does not grow v2's warnings — *it is a v1 row* | — |
| C17-37 | **a family naming a payload schema nobody registered writes the edge and says so** — `payload_schema_unregistered:<name>`, the twenty-sixth `warnings` value, with `attr_schema_version=None`. Refusing would put the ordering of two deployment acts inside a data path; writing it silently is the inert field R34 exists to end | **C** |
| C17-38 | **a payload schema does not make its own family unregisterable** — deviation **D-4c-1**, pinned. `EDGES.md` §2.5's original key was `(namespace, "edge", <family name>)`, which is the key ruling R10 already gives the family's own declaration. **[Observed, row 4c]** a payload schema with `additional="forbid"` under that key made `propose_type(kind="edge", …)` refuse with all five declaration keys *"not declared in the schema"*. One container meaning two things — §2.3's Cause B | — |
| C17-39 | **the enforcement floor and the per-namespace schema both apply** (§5.2b rules 2 and 3): a family declaring no `payload_schema` is judged by the `(namespace, "edge_payload")` schema, and a `mode="off"` override under an `enforce` one still refuses — an override is a schema, not an exemption | — |
| C17-40 | **the census enumerates edge payload keys and stays tri-state** (§5.5's floor, on `Edge.attributes`). **Nonbinding**, ruling R2. Payload schemas are discovered through the FAMILIES that declare them, because there is no `kind="edge_payload"` type to enumerate — without that, the census would answer a confident `declared=False` about a key a payload schema declares `required` | — |
| C17-41 | **an amendment is a new event carrying the old and new values** (`EDGES.md` §5.2, ruling **R37**). That section narrated `edge_amended` with a worked example and **nothing wrote it** — deviation D-4b-13, question Q32. The row carries the new value, the history carries both, and `edge_added`'s actor is not rewritten by the correction | — |
| C17-42 | **an amendment is not a second write path**, and R37's condition was that design test. `family`, `src`, `dst` and `status` are not parameters — asserted by reading the signature, because the guarantee has to be structural; the payload goes back through §2.5's validation on `add_edge`'s exact terms; a refused amendment appends no event; a retracted edge is refused `already_decided`. *(The kill row's third trip is this exact shape: a guard written for one call over a fact more than one call can change.)* | **kill row** |
| C17-43 | **an amendment that cannot be recorded is refused, and a retraction on the same store is not.** §3.6's rule, fourth caller. `EDGES.md` §2.6 argues retraction past it because *the record is the row*; there is no column for a prior confidence, so that argument does not transpose. Both halves asserted together, because they are only defensible together | — |
| C17-44 | **the chain is followed at every hop, not only at the origin.** The far endpoint of a SECOND-hop edge is orphaned by a merge in exactly the way the origin is, and no depth-1 test can reach it. The graph is `EDGES.md` §4.2's own justification for the cap of 2 — beacon's `task --blocks--> task --stakeholder--> person` — with the person merged after the edge was written, which is beacon slice 1's shape | **4** |
| C17-45 | **a broken or looping chain stops at depth and says so** — `C0-10`'s question asked of chain-following, where *"it hangs"* is not an answer. Three reachable shapes: a **cycle** (`retire(a, successor=b)` then `retire(b, successor=a)`, which nothing in §5.9 forbids), a chain past the cap (`complete=False` with a `why`, never a silently shallower answer), and a backend that cannot page its retired rows (Rule U — it has not said there is no merge, only that it could not say) | — |
| C17-46 | **`retire(successor=)` is followed exactly as a merge is**, and a plain retirement joins nothing. §5.3 makes the redirect a guarantee and `C9-18` gave that call §5.10's identity guards because it **is** the collapse; following one act and not the other would be the kill row's third trip in mirror image — one act, two behaviours, the cheaper door unguarded | **4**, **kill row** |
| C17-47 | **a second retraction is refused and the first decision survives** (ruling **R39**; D-4b-16, **Q34**). `EDGES.md` §2.6 argues past §3.6 on *"the record **is** the row"* — and that assumes retraction happens once; a second one overwrote the first's reason, actor and timestamp, and with no edge event table the first decision was gone. Refused rather than made idempotent, because idempotency hides a real double decision. `already_decided` is §5.5's existing value on a second object | — |
| C17-48 | **a written reference is never reported as a followed one** — Rule K, precisely (row 4c r1, three defects in one walk). `via_successor` was set on an edge whose `src` was literally the reference passed, because `expanded.get(src) or expanded.get(dst)` cannot tell *absent* from *present-and-written*; `nodes` was not de-duplicated across a merged identity though the ORIGIN was, with an explicit argument; and a merged node produced no `endpoint_type_merged` unless it happened to be the origin | **C** |
| C17-49 | **an unregistered family's edge still has to be INCIDENT** — *"the registry narrows, ALWAYS"* on the one branch no test reached. `C17-31` claims the narrowing holds on the default direction and passes `edge_families=[…]`, which makes this branch unreachable from it: *"caught incidentally is a weaker claim than pinned"*, one branch along, in the id that makes the complaint. Keeping the edge (rule 4.3-13) and dropping the incidence check are two decisions and only the first was argued | **C** |
| C17-50 | **an unrelated amendment does not erase the payload's warnings** (rule `2.5-3`, *"`warn` writes and **enumerates**"*). `amend_edge` stripped `attributes_invalid:` unconditionally, so amending only the `confidence` deleted the enumeration from a row whose payload was still invalid and still stored — §5.5's whole subject, reached through the call R37 added. Also: a missing edge is `unknown_edge`, never a capability complaint | — |
| C17-51 | **merging an edge FAMILY does not orphan its edges** — ruling **R38** on the axis it was not applied to (row 4c, second adversarial round, found by the lens that builds beacon's slice 1). R38 resolves an *endpoint* reference to the identity it now belongs to and said nothing about *family names*, while §2.3's architectural bet is that a family **is** a `TypeEntry` inheriting `merge_types` for free. **[Observed]** a steward merging two duplicate families and a consumer asking for the SURVIVING name got `known=2, complete=True, warnings=()` with a real stakeholder missing — verbatim the sentence R38 exists to close, one axis over, inside the row that closed it. Every R38 test merged `entity` types | **4** |
| C17-52 | **a retired origin type says so, and an integer `InstanceRef.id` is refused.** §4.3-3 warns for a retired *family* and §4.3-10 for an *unregistered* origin; a deliberately retired origin — **mechanism 3**, a steward's explicit *"stop using this word"* — had no carrier at all. And §2.1 records the `str`/`int` cast as contortion **E4**, *"where a silent key mismatch lives"*: it was living there, with `neighbors` returning `known=0, complete=True` on SQLite and raising a raw psycopg error on Postgres for one input | **3**, **C** |
| C17-53 | **an absorbed family name is not a hole in the schema floor** — the WRITE side of `C17-51` (row 4c, round 3). Round 2 taught `neighbors` to follow the family chain and left `add_edge` comparing the written string, so an absorbed name was a permanent, warning-free bypass of the surviving family's `enforce` payload schema while §2.5 makes the strictness a **floor**. The edge is still written under the name given and validated by the family it now denotes | — |


**C18 — the three use cases through the shipped edge store (10).** Row 4b. Mechanisms **4** and the `ROADMAP.md` kill row.

Row #4's design tests were walked by a throwaway kit in `docs/tools/` that this package does not import, and §17.5 of that document says plainly what that is worth: *"prose-plus-probe review has a floor, and this document has reached it. The next signal with real information is a real consumer over a real store."* This group is the smallest available version of that — the same three fixtures and the same **pre-registered** numbers, driven through `ontoloche.Registry` on all three legs.

**Both fixtures are checked in, and that is a rule rather than a convenience.** A contract test may not depend on a network — `--pyargs ontoloche.contract` promises a third-party author a suite that runs — and §8.4 and `EDGES.md` §11.3 record the same defect twice: a query with a `limit` and no `order` returns an arbitrary window, and two runs of the NYC probe printed different numbers. UC3's sample is pinned by [`pin_nyc_edge_sample.py`](../tools/pin_nyc_edge_sample.py) and carries each dataset's own `data_updated_at`, so `EdgeProvenance.source_version` has something true to say.

| id | asserts | mech |
|---|---|---|
| C18-01 | **[CMS]** the three implicit relationships are three `level="instance"` families, and every pre-registered edge count holds: `issued_during` **400**, `conducted_at` **69**, `cites` **400** over **92** distinct destinations and **10** distinct facilities. `created_by="derived"` — ruling **R17** on its second fixture | — |
| C18-02 | **[CMS]** summed over all ten facilities, `neighbors(facility, depth=2)` returns exactly **69** surveys at depth 1 and **400** citations at depth 2 — the ground truth reached the other way round, through the read seam | — |
| C18-03 | **[CMS]** `citation → survey → facility` is the deepest chain in the fixture and it is **two hops**, which is why the cap is 2. `EDGES.md` §4.2 argues the cap from beacon's flagship query; CMS arrives at the same number independently | — |
| C18-04 | **[CMS]** T2.5 and T2.6, the decision UC2 forced **against UC1's interest**: a `value_set` endpoint is refused at both layers (the declaration, and then the write on `level`), and the pre-registered mechanical test comes out as predicted — **all ten** citation properties are single-valued per `(citation, tag)` pair, so if severity may ride on the edge so may the other nine and `cites` becomes the citation row under another name. 14 of beacon's 17 join families carry payload; **CMS wins** | — |
| C18-05 | **[NYC]** three `borough` value sets, five referents, three encodings and a sixth spelling of *unknown*; the realistic write order is a **chain, not a triangle**, so a depth-2 walk **reaches** C and does not assert `A ≡ C`. `at_depth` is the only thing standing between that report and a manufactured equivalence class, and this checks that it does. `source_version` carries the 2017-10-04 / 2026-08 skew | **4** |
| C18-06 | **[NYC]** the report's nodes are in namespaces the caller never named — `namespace` scopes only the resolution of `edge_families` and filters nothing — and `complete=True` is stated next to `families_searched`, because it is a claim about three datasets out of 2,399 | — |
| C18-07 | **[NYC] the kill row.** With the `equivalent_to` edge present, `merge_types` across namespaces is still refused, and refused **again** under explicit `acknowledge`. An edge asserting sameness and a merge performing it are different acts; if this ever passes, `EDGES.md` §13 says the family should be withdrawn | **kill row** |
| C18-08 | **[NYC]** the finding the expectations did not anticipate: a deterministic key join is **many-to-many** — 102 edges, **18 of 25** complaints matched, **max 16** trees on one lot — so the most confident join an ingestion layer can make does not establish the relationship a reader wants. The family is named for what the key proves (`same_tax_lot`, not `concerns`) and `confidence` is `1/n` | **4** |
| C18-09 | **[Tenshen, read-only]** a `work_links`-shaped row maps onto `EdgeRecord` and the two-hop walk `deadline_cluster_service` stops short of is answered at depth 2. Contortions **E1**–**E4** are exercised rather than described: the `Integer`→`str` cast, one projected payload key, the four missing lifecycle columns, and **tenancy refused a home** (`user_id` is not mapped onto `namespace` — ruling **R24**) | — |
| C18-10 | **[Tenshen, read-only] ruling R23**: a NULL `relationship_type` is **refused explicitly**, never skipped. Skipping is a silent drop by the adapter — mechanism **C** at the seam — and inventing a family asserts a fact the data does not carry; a reserved `unclassified` family is a vocabulary this package would be inventing for a host's missing constraint. The honest third answer is on beacon's side | **C** |



**C19 — governed actions: the family, the gate and the ledger (81).** `ACTIONS.md` v0, row 6b. **58** of these are the ids that document's eight rule tables PLANNED, one per numbered rule, and `check_spec_drift.py` reads those tables for the first time in this change — which is what §14 asked for, *"in the same change that lands the tests, which is the only order in which the gate is ever telling the truth."* **Two more (`C19-59`, `C19-60`) come from the build**: UC1's tool-slot arithmetic and the Phase 3 ingestion loop's override census, driven through the shipped registry rather than through the throwaway kit they were written against. Mechanisms **1** (dominant — *a noun that nobody reviewed describes something wrongly; a verb that nobody reviewed CHANGES something wrongly*), **C** (co-dominant and measured: the busiest page sits at **127 of 127**) and the `ROADMAP.md` kill row, which this document's own loop reached **five** times.

Every BLOCKING finding of that loop is an assertion here. They were fixed in a throwaway kit under `docs/tools/` that this package does not import — so until this group they were fixed nowhere a backend author could be held to, which is row 4b's own recorded lesson and §14 asks for exactly this transposition.

| id | asserts | mech |
|---|---|---|
| C19-01 | **§2.4-1** the precondition vocabulary is closed at four kinds; a family declaring a fifth is refused at all three declaration doors. UC2's own action wants the fifth and does not get one — contortion **ACT4**, routed to Phase 3 by **R22**/**R41**/**R60** | — |
| C19-02 | **§2.4-2** each kind is answered by a call that ALREADY EXISTS — `list_types` / `predicates` / `neighbors` — and `evaluated_by` names which, so §2.4's no-query-language claim is mechanical rather than asserted. `resolve_type` is deliberately not an evaluator (**ACT2**/**ACT6**) | — |
| C19-03 | **§2.4-3** `Precondition.why` is required and non-empty, on `FieldSpec.description`'s reasoning: *a precondition nobody can read is one nobody will delete when it stops being true* | — |
| C19-04 | **§2.4-4** a condition that does not hold returns `precondition_unmet` naming the failing condition's `kind` and `subject`, never a bare `False`. One value, two states, and `detail["state"]` says which — `endpoint_kind_mismatch`'s own precedent | — |
| C19-05 | **§2.4-5** an UNKNOWN condition is `None` plus a `why` and `preflight` refuses rather than treating unknown as satisfied. **Its subject is the declined capability**, so it runs on every leg | — |
| C19-06 | **§2.5-1** the effect vocabulary is closed at four operations; a fifth is `effect_not_permitted` at all three doors | — |
| C19-07 | **§2.5-2 the kill row through a door no previous row had.** `approve` · `reject` · `retire` · `reinstate` · `merge_types` · `register_consumer` may NEVER be an effect, as a general rule rather than a family's opt-in — *an action that can `merge_types` is the kill row wearing a verb* | **kill row** |
| C19-08 | **§2.5-3** `propose_type` MAY be an effect, so the line has a legal side: *an action may PROPOSE; only a human, or an auto-policy a deployment set deliberately, may APPROVE* | **1** |
| C19-09 | **§2.5-4** `op="host_state"` requires a non-empty `why`. **[Observed]** 11 of `delete_person`'s 15 foreign keys are expressible only this way, and UC1 would be SERVED by dropping the sentence — CMS's rule beats UC1's convenience | — |
| C19-10 | **§2.5-5** the exclusion binds at DECLARATION, not only at invocation: EDGES §2.4.1 spent a round learning that a rule checked at write time is one a family author opts out of by declaring something permissive | **kill row** |
| C19-11 | **§2.5-6** an observed effect outside the declared set is a **warning** on a KEPT record, never a refusal that discards it — the brief offered `effect_undeclared` as a `Refusal.reason` and the UC1 design test moved it, because refusing destroys the only evidence the undeclared effect happened | **C** |
| C19-12 | **§2.5-7** an effect naming an unregistered `kind="edge"` family is refused `edge_family_unknown` — EDGES §4.3's EXISTING value, not a new one — and the guard is narrowed rather than banned | — |
| C19-13 | **§5.2-1** `approval_mode` is closed at three; a fourth is a policy language arriving one value at a time | **1** |
| C19-14 | **§5.2-2 an ALLOWLIST off the actor, and it took two rounds.** `bot:reaper`, `svc:cleanup`, `AI:bot`, `agent:claude` and `nobody` walked through round 1's three-prefix blocklist AND through round 2's derived-`created_by` test. INTERFACE §5.4 line 58's named failure; **Rule U: unknown is not a person** | **1** |
| C19-15 | **§5.2-3** a tier below the family's floor refuses `tier_below_action_policy` with `state="false"`, the floor and the tier. `tier_below_auto_approve_policy` is NOT reused: that is about a *type proposal*, this about an *invocation* — §2.3's Cause B | **1** |
| C19-16 | **§5.2-4** `min_auto_tier=None` under `auto` is a LEGAL configuration reported as `tier_floor=None` plus a `why` — never a warning, because minting one would put a vocabulary entry on a correct configuration | — |
| C19-17 | **§5.2-5** the comparison is `bool | None` and **all three** unknown causes refuse with `state="unknown"` and their own sentence. **None raises and none says `false`** — round 1 found a confident refusal for a tier nobody supplied and an uncaught `ValueError` for a tier outside the order | — |
| C19-18 | **§5.2-6** an invocation's `model_tier` is the tier of the actor that INVOKED, distinct from the family's own — *a family proposed by Haiku and invoked by Opus is not the same risk as the reverse* | — |
| C19-19 | **§10-1** `reachability` values are opaque strings in the host's vocabulary and the registry never interprets one; an EMPTY list is a positive declaration, not a forgotten field | **C** |
| C19-20 | **§10-2** with `order=None` the report carries `counts` only and **`order_source is None` is the marker** — §10.2's rule made structural. *The one question this layer most obviously could have answered is the one it is built to be unable to answer* | **C** |
| C19-21 | **§10-3** `counts` is RULE-INDEPENDENT and identical under every permutation of `order`; a family in two groups is counted in both and charged to one. Round 1 found `counts` changing with the order, and no design test caught it because beacon's `category` is a single string | **C** |
| C19-22 | **§10-4** `greedy_whole_group` admits groups whole, in the caller's order, until `budget − reserved` is exhausted — **[Observed]** the only host that exists drops whole categories | **C** |
| C19-23 | **§10-5** `consumers_at_risk` inherits `ConsumerReport.complete == False` and can never be a complete casualty list — and an EMPTY one is that same `false` wearing a different name | **C** |
| C19-24 | **§10-6** an `order` naming only groups no family carries is refused `action_family_unknown`; a MIX answers with zeroes and `complete=False`, because a host legitimately assembles a context from groups that are empty today | **C** |
| C19-25 | **§10-7** the 128 is a PROVIDER's: `budget` is a caller's argument with **no default**, and no number from that measurement is in this package's code at all | — |
| C19-26 | **§2.2-1** a `kind="action"` entry declaring none of the eight keys is a legal `TypeEntry` and is NOT refused — `edges.family_declaration_problem`'s own recorded decision for the identical case, which round 1 found this document silently reversing | — |
| C19-27 | **§2.2-2** a partial declaration must declare `reversibility` and `approval_mode` from their closed sets, and **"partial" means ANY of the eight** — round 2 reached the kill row through a version that returned early on the two required keys, so an entry declaring `merge_types` and nothing else was written at all three doors | **kill row** |
| C19-28 | **§2.2-3** `reversibility="irreversible"` ⇒ `approval_mode` MUST be `"human"`, refused with **`attributes_schema_violation`** — ruling **R18**'s own value. The first draft minted `human_approval_required`, which would have made two instances of one ruling return two different reasons | **1** |
| C19-29 | **§3-1** `declared_effects` is COPIED from the family at invocation time, so amending the family does not re-describe an existing invocation's blast radius | — |
| C19-30 | **§3-2** `gate_verdict` has three values and `not_asked` is one of them; `False` would assert a refusal that never happened | — |
| C19-31 | **§3-3** `approved_by` is never fabricated and never null where the gate decided. Round 1 found the first draft writing `"auto:<policy>"` onto an `irreversible`/`human` family invoked by `ai:reaper` with no human and no warning — the field EDGES §5.1 dropped because *a field whose only honest value is a lie should not be on the shape* | **1** |
| C19-32 | **§3-4** `outcome="refused"` REQUIRES a refusal from INTERFACE §5.12's closed vocabulary; the vocabulary is closed at four and there is no `pending` | — |
| C19-33 | **§3-5** a surplus effect warns and the record is kept; a SUBSET warns nothing, because a permission is not a promise and warning on an unused one trains hosts to declare narrowly and amend often | — |
| C19-34 | **§6-1** `preflight` records NOTHING and is idempotent: N calls leave the invocation store unchanged | — |
| C19-35 | **§6-2** every `PreconditionResult` names the existing call that answered it, from the closed set — the field a later reader will use to notice that a query language grew | — |
| C19-36 | **§6-3** `holds=None` is refused and the refusal says **unknown** rather than **false**; unknown is never treated as satisfied. Its own id rather than an assertion inside `C19-05`, because producing an honest unknown and refusing on one are different rules | — |
| C19-37 | **§6-4** `record_invocation` does not re-evaluate preconditions — the TOCTOU gap NAMED rather than closed — and an invocation whose gate refused is recorded rather than discarded, which is §4's whole argument | — |
| C19-38 | **§6-5** `known` is `int | None` and `complete` is `False` whenever a filter suppressed rows or `limit` truncated the answer. *(The first draft stamped it `True` through a dead sub-expression `(not filtered or True)`, in the one query §4 asks an operator to act on.)* | — |
| C19-39 | **§8-1** `stores_invocations=False` makes every call that reads or writes the store refuse `action_store_absent`, **never an empty report** — the fifth capability refusal of that shape. `preflight` and `projection` touch no invocation and are unaffected | — |
| C19-40 | **§8-2** every `False` action flag carries a non-empty `why`, and with no store the other two are **vacuous rather than declined** — `C0-01`'s carve-out shape, applied to a third group | — |
| C19-41 | **§8-3** two transaction scopes on one connection is non-conformant, and `scope_conflict()` RETURNS the sentence rather than raising. With a third store there are two independent pairs and one sentence: **Q42**, ruled **R46** | — |
| C19-42 | **§8-4** under `action_transaction_scope="savepoint"`, `record_invocation` stamps `not_durable_until_host_commits` ITSELF and `invocations` does not — *a signal that never turns off is noise*, and EDGES §6.2 records `retract_edge` getting the *itself* half wrong | — |
| C19-43 | **§8-5** the action flags default `False`, so an adapter written against the eighteen-primitive protocol claims no invocation store — the same load-bearing default EDGES §6 chose for its four | — |
| C19-44 | **§2.2-4 the third door, and round 1 walked through it.** Every declaration rule binds at `propose_type`, `approve` AND `import_types`: a reviewer imported an **active** family declaring `merge_types` *and* breaching the cross-field rule with **no warning at all**, while the same call refused a breaching EDGE family correctly | **kill row** |
| C19-45 | **§2.4-6** a condition naming no `InputSpec` and no literal ref — and a `predicate_holds` with no predicate, and an edge condition with no family — is refused **at declaration**: *the precondition door is shut where the effect door is* | — |
| C19-46 | **§2.4-7** `Precondition.namespace` is the FAMILY's and reaches `neighbors`, which has no default for it. The printed shape omitted it until round 1 while the probe kit had silently added it, and the two readings gave OPPOSITE verdicts on UC3's own fixture | **4** |
| C19-47 | **§2.4-8** the edge kinds search `direction="both"`, so a DIRECTED family's `edge_absent` is conservative rather than exact — EDGES §2.2 records the confident false negative a direction filter produces | — |
| C19-48 | **§2.5-8 the kill row's second trip in this document's loop.** A `propose_type` effect must NAME a kind from an **allowlist**; round 2 walked past round 1's blocklist by OMITTING the key, and again with `kind="action"` — a live **verb** minted unattended | **kill row** |
| C19-49 | **§2.5-9** effect identity is `(op, namespace, family, kind)` with `why` excluded — except `host_state`, which has no target and whose `why` IS its identity. Contortion **ACT9**, ruled **R46**: the cost is stated rather than paid for with a sixth key | — |
| C19-50 | **§5.2-7** `review` mode records `approved_by="auto:<policy>"` and the invocation is enumerable by `invocations(unreviewed=True)` until an `invocation_reviewed` event sets `reviewed_at`. The writer of that event is deviation **D-6b-3**: §5.2 names the read and §6's four calls append nothing | — |
| C19-51 | **§6-6 the kill row, constructed end to end.** Both invocation calls validate every supplied input and refuse a `kind="predicate"` ref WHATEVER the family declared — round 1 declared `kinds=None`, handed `preflight` two predicates, got `allowed` and recorded it `applied` | **kill row** |
| C19-52 | **§6-7** a shipped call that RAISES for an unregistered subject is caught and becomes `holds=None` plus a `why`; nothing escapes the return type. Round 1 found the escape, and this build found the same question one implementation along | — |
| C19-53 | **§10-8** `known` is the number of families this report SELECTED, not the size of the registry | — |
| C19-54 | **§10-9** a host whose families all declare `reachability=()` gets zeroes rather than a typo refusal, and a `namespace` that holds no such family is a legitimate scope — **[Observed, round 2]** the rule misfiring on the venture's own customer. *Narrowed to the `namespace`-scoped pool by ruling **R70**, row 6c; `C19-74` holds the other direction* | **C** |
| C19-55 | **§2.5-10** `namespace=None` on an edge op DECLARES an input-determined namespace, satisfied only by an observed effect whose namespace one of the invocation's own inputs carries. Round 2 measured the alternative at **2,394 of 2,399 correct invocations** carrying `effect_undeclared` — *a detector that fires on 99.8% of a correct run is not a detector* | **C** |
| C19-56 | **§3-7** the copy is taken from what the GATE judged: `family_version` is stamped on both shapes, `record_invocation(judged=…)` records that declaration, and a mismatch is `declaration_amended:<from>:<to>`. Round 2 widened a family between the two calls and watched an undeclared `retract_edge` enter the ledger with no warning | — |
| C19-57 | **§3-8** `declared_policy` carries `approval_mode`, `min_auto_tier`, `reversibility` and the precondition kinds — for the reason rule 3-1 carries the effects, and with all four taken from the same moment. Round 3 found `reversibility` alone reading the current family: *one dict, two moments, no marker* | — |
| C19-58 | **§10-10** a group repeated in `order` is charged ONCE, so `fits` and `would_evict` can never intersect — round 2 found a duplicate in both, over a pair rule 10-4 defines as disjoint | — |
| C19-59 | **[UC1] beacon's own arithmetic, reproduced through `projection` against the shipped registry.** `budget=127`, `order=(common, task, project, person)` → `counts` **45 / 48 / 21 / 13**, all four fit, `over_by=0`; a **49th** `task` family → `would_evict=("person",)`, `over_by=1`. beacon's source comment, reproduced arithmetically rather than quoted | **C** |
| C19-60 | **[Phase 3 ingestion] §4's one measurement, at a size that would have returned zero before the push-down.** `invocations(gate_verdict="refused", outcome="applied")` finds the single override past the default `limit`, and says `complete=False`. Round 2 got **zero rows from a 2,399-row ledger that had one** — *a floor of zero is indistinguishable from a clean deployment* | **1** |
| C19-61 | **BLOCKING, round 1.** `invocations(family=X)` returned invocations of OTHER families on a backend declaring `indexes_invocations_by_family=False`. §8's *"correctness is unchanged -- the registry filters above the store"* was not implemented: the shipped double DROPS that filter, modelling `find_edges`' deviation, which is only sound because an edge query is already bounded by `incident_to`. **A ledger read has no such bound.** Every filter is re-applied above the store now, which answers `C0-10`'s question at this surface for all of them | **C** |
| C19-62 | **BLOCKING, round 1.** `compensated_by` -- and the `outcome` derived from it -- lied past the bound: the derivation discarded the page's `complete=False` and returned a bare `None`, so a compensated invocation read back `outcome="applied"`. It is `None` **plus a sentence** now. The bound stays (**R58** puts façade paging in Phase 3); what changes is that the caller is told | — |
| C19-63 | **BLOCKING, round 1**, and it is **D-4c-1** reproduced by the row that inherited the mechanism. §2.7's literal key made a `payload_schema` schema govern the family's own eight DECLARATION keys, so *the family became undeclarable by the act of governing its own inputs*. Contortion **ACT1** predicted it -- *"it works because the two objects never share a store"* -- and they share `oo_attr_schema`. `action_payload` is `edges.EDGE_PAYLOAD_KIND` one kind along | — |
| C19-64 | **MAJOR, round 1.** Omitting `record_invocation(judged=…)` silently dropped rule **3-7**'s guarantee: the same invocation filed `declaration_amended` plus an `effect_undeclared` with it, and a **clean row** without. `declaration_unjudged` is the thirty-third warning value (**R3**). A host that never asked the gate is not warned -- there was nothing to hand back | — |
| C19-65 | **MAJOR, round 1.** `tier_floor_why` said *"every tier auto-approves"* on the `irreversible`/`human` family §2.2's cross-field rule exists to make un-auto-approvable. §5.2 mints that sentence for `auto` mode; it was emitted unconditionally | — |
| C19-66 | **MAJOR, round 1.** `invocations(unreviewed=True)` implies *awaiting review*, and on `stores_invocation_events=False` nothing can ever leave the queue -- rule **8-2** requires the flag's sentence *"wherever a result would otherwise imply a fact"*, and the generic *"a filter suppressed rows"* was swallowing it | — |
| C19-67 | **MAJOR, round 1.** A family naming a `payload_schema` nobody registered was byte-identical on the record to one naming none -- ruling **R34**'s inert `payload_schema` arriving back through the ABSENCE of a warning. `payload_schema_unregistered` is EDGES.md §2.5's existing value, reused rather than re-minted | — |
| C19-68 | **MAJOR, round 2.** `invocations(unreviewed=False)` answered `known=0` on the fully capable leg with a row that belonged in the answer. The filter is HALF pushed down, and the store's `NOT EXISTS` half is a narrowing of the façade's predicate only for `True` — for `False` it drops the larger half (every auto-mode row), which the registry can narrow but never widen. Fix 2's guarantee holds exactly where the push-down narrows; where it does not, the filter is not pushed | — |
| C19-69 | **MAJOR, round 2**, and a regression fix 2 introduced: re-applying filters above the store put a Python-side `created_at >= since` where none existed, and **primitive 21 accepts a naive `since` and answers** while the façade raised `TypeError`. A façade that crashes on a value its own primitive takes is not a narrower answer | — |
| C19-70 | **MAJOR, round 2.** `attribute_census(kind="action_payload")` answered `keys=[]` with **`complete=True`** after an invocation carried an input — the kind's own justification cites that census, and nothing called `observe_attributes` for invocation inputs. PACKAGE.md §5.5's floor, and Rule U's forbidden empty in the one call whose job is enumerating what got written | — |
| C19-71 | **BLOCKING, round 3** — the ACTIONS door's own kill-row walk, alive through a mislabelled string. `C19-51` closed *"a `kind="predicate"` ref is refused whatever the family declared"* against `ref_kind`, which returns **the kind the CALLER wrote** and never checks it against the stored row — so `TypeRef("default", "entity", "commentable")` naming a real capability predicate reached `verdict="allowed"` and was **recorded `applied`**. The SEVENTH trip's *guard comparing a byte where the registry holds a stored fact*, one surface along. A ref naming no registered row is deliberately still allowed: there is no stored fact to contradict | **kill row** |
| C19-72 | **MAJOR, round 3.** `preflight` never evaluated the family's `payload_schema`, so the gate said *may this run* → **yes** for inputs `record_invocation` then refused non-overridably. `_input_refusal`'s own docstring states the rule it broke — *a rule with one enforcement point is a rule with one door left open* — and **a gate a recorder overrules is worse than no gate** | — |
| C19-73 | **MAJOR, round 3**, and the surface `6B-RUN.md` §6.2 predicted this round would reach. `preflight`'s `predicate_holds` found its predicate by an exact **byte** match on a registry whose published notion of one word is `same_word` — so it said *"no registered predicate named X"* about a word `resolve_type` answers at confidence **1.0**. The direction was safe (Rule U); the sentence was a confident falsehood | — |
| C19-74 | **§10-9, ruling R70, row 6c.** The typo judgement is made against **this scope's** pool, not the store-wide one. **[Observed, row 6c's design test over UC3's many-publishers catalogue]** four `ingest_dataset_*` families in `dpr` with `reachability=()`, alone on the store, answered `counts={'catalogue_ingest': 0}` — and **refused `action_family_unknown` on the identical call** the moment a co-tenant registered one surfaced family in `oti_311`. One host's answer depended on an unrelated host's data, in a catalogue whose whole shape is dozens of publishers. Both prior readings cost a round each; this id holds the co-tenant direction and the misspelling that must still be caught | **C** |
| C19-75 | **§2.5-11, ruling R71, row 6c** — the GATE half. A declared `kind="edge"` blast-radius family retired **after** the declaration: `preflight` warns `edge_family_retired:<name>`, keeps `verdict="allowed"`, and one retired family declared by two edge ops is **one** warning. §2.5-7's *"the door is the declaration"* had no answer for the family being retired afterwards | **3** |
| C19-76 | **§2.5-11, ruling R71** — the LEDGER half, and there are two ids rather than one because shipping this at `record_invocation` alone would be *a fix applied at one call site of two*: the single sentence of the kill row's ninth, tenth and eleventh trips. Judged over the **declaration of record**, so the warning is about the moment the gate judged | **3** |
| C19-77 | **§2.3, ruling R72, row 6c** — `parse_ref`, the public inverse of `ref_key`, pinned as a PROPERTY over every reference shape in both directions: `parse_ref(ref_key(r)) == r` and `ref_key(parse_ref(k)) == k`. Opaque ids carrying `:` and `#` are exercised, because that is what breaks a naive split, and the stored ledger string is driven through the shipped registry so the parser reads the format the store actually holds | **C** |
| C19-78 | **§2.3, ruling R72** — and this is the id that matters. `parse_ref` **raises** for anything outside §2.3's grammar: no `None` fallback, no *"probably a type ref"* branch. *A permissive default for a value you did not recognise* is the single shape row 6b shipped twice — `ref_shape` walking a capability-predicate merge to `allowed`, and `_alias_identity_breach` comparing a row against itself (the kill row's NINTH trip). The narrowing half is asserted too, because refusing everything passes a test that only tests refusals | **C** |
| C19-79 | **§6-9, ruling R73, row 6c** — `review_invocation` is a FIFTH call and never a parameter on `record_invocation`, adopting D-6b-3's argument in full: *a review is a second act by a second person at a later time*, and a `reviewed_by=` on the write call would let the actor who ran the action mark their own invocation reviewed. Asserted mechanically off the signatures, and `reviewed_by` is a REQUIRED keyword on the fifth call | **1** |
| C19-80 | **§6-10, ruling R73** — `unknown_invocation`, the **thirty-first** `Refusal.reason`. §7 argued the value and declined it on an explicitly conditional premise — *"no call in this document names an existing invocation by id"* — and §6.5's call names one. Not `action_family_unknown`, which the build row reused and recorded as a mismatch: one word for a missing FAMILY and a missing INVOCATION is INTERFACE.md §2.3's Cause B | **2** |
| C19-81 | **§6-11, ruling R73** — the `review` queue drains END TO END: mode, gate, three filed invocations, three reviews, an empty queue, `reviewed_at` set, and the `invocation_reviewed` event naming its reviewer. §5.2 specified the read and §3.5 minted the event while v0's four calls appended none, and three adversarial rounds read both sections without finding it — **what found it was writing the ids** | **1** |


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
| `cannot_record_override` (reinstate) | **C9-11** |
| **`successor_active`** (reinstate, non-overridable) | **C9-10** |
| `reinstate_no_op:not_retired` | **C9-11** |
| a reinstated name resolves again | **C9-09** |
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

**[Inferred]** the built suite will be larger than 124 — parametrisation over kinds and over `on_unknown` values will multiply several of these. The enumeration is the coverage floor, not a budget.

---

### 6.4 The coverage report — *a conformance claim without its coverage line is not a claim*

**Ruling R12, row 3d.** §6.1's verdict used to be *"the whole suite passed"*. On a backend that declines capabilities that sentence is true and misleading at once: a declined flag makes some contract ids **unexercisable**, the suite skips them with a reason, and a run that reports `330 passed` has told the truth about the assertions and nothing about the coverage. So the verdict is now two clauses:

> **the whole suite passed; N ids exercised, M not exercisable on this backend, listed.**

Same move as `ConsumerReport.complete=False` (`INTERFACE.md` §5.1), and for the same reason: a report that omits what it could not see promises a completeness it does not have. Every run prints, after the `CONFORMANCE` block:

```
  coverage, per leg (PACKAGE.md 6.4 / ruling R12):
    sqlite          CONFORMANT: 123 ids exercised, 1 not exercisable on this backend (listed)
                      1: PACKAGE.md 5.7 -- this backend stores arbitrary attributes, so a census
                        restricted to its projections has no subject here. C15-02 is the full case.
                         C15-09
    postgres        CONFORMANT: 123 ids exercised, 1 not exercisable on this backend (listed)
                      …
    sqlite_minimal  CONFORMANT: 61 ids exercised, 63 not exercisable on this backend (listed)
                      21: PACKAGE.md 3.2 -- this backend declares stores_proposals=False, which 3.2
                        says is conformant. This test needs it as scaffolding, not as its subject:
                        this store has no proposal table: a decision is recorded on the type row and
                        a pending proposal has nowhere to live
                         C15-03, C15-06, C3-06, C3-07, C4-02, C4-04, C4-05, C5-01, …
                      …
    (+2 backend-independent, run once: C0-04, C14-07)
  A conformance claim without its coverage line is not a claim (ruling R12).
```

Four things about it are deliberate:

1. **The reasons are the tests', not the report's.** `ontoloche/contract/_coverage.py` aggregates skip reasons and invents none. The `requires_capability` fixture already named the flag and quoted the backend's own `why`; this prints it.
2. **It is grouped by reason, wrapped, and never truncated.** The informative half of a `requires_capability` reason is the backend's `why`, which is at the *end* of the sentence — the first version clipped the line and cut off exactly that.
3. **The arithmetic must close.** Exercised + not-exercisable + backend-independent = §6.2's enumeration, on every leg. It did not on the first run: `C4-09` is parametrised over malformed names *as well as* over backends, so its node ids read `[sqlite-name0]`, matched no leg by substring, and **three contract ids went missing from every leg's count**. Found by the report's own arithmetic failing to add up — which is the argument for the report in one sentence.
4. **A failing leg says `NOT CONFORMANT` and names the ids.** The report is not a way to be conformant with failures in it. Three cases count as failing, and the last two were added by the second adversarial round after being reproduced against the real class:
   - a test **failed** in its call phase;
   - a test **errored in setup or teardown** — pytest reports that as `when="setup", outcome="failed"`, which matched neither branch of the first version, so the id **vanished** from the leg entirely: not exercised, not skipped, not failed, and the leg still printed `CONFORMANT`. That is a defect *in the backend under test* — a broken `__init__`, a fixture that raises — disappearing from the very report built to catch it;
   - a leg is **short of the universe**: an id that ran on another leg and is neither exercised, skipped nor errored here is printed as `INCOMPLETE COVERAGE` and named. This is the closure check made mechanical rather than left to a reader's arithmetic.

5. **A declaration nothing checked is never printed as part of a clean verdict.** `transaction_scope="savepoint"` and `owns_schema=False` are *claims*, and until row 3d nothing could check either for any adapter but the two shipped drivers — `C0-12` and `C0-09` hard-coded their backend list. [Observed] an adapter declaring `"savepoint"` **while committing at depth 0** — the literal U1 regression this row exists to fix — ran the suite to `130 passed`, verdict `CONFORMANT`. Two things changed:
   - **`C0-12` is generic.** A third-party author supplies a `BorrowedHarness` — their adapter over a connection *they* own, plus handles onto their host transaction — via `run_contract_suite(borrowed_factory=…)` or `--borrowed pkg.mod:callable`, and the test runs against their adapter. The natively-degraded third leg, whose driver takes a borrowed connection perfectly well, is no longer skipped either.
   - **`C0-09` got the same treatment one round later.** `owns_schema=False` is the *other* declaration §7 (B1) calls load-bearing and is beacon's own shape, and [Observed] an adapter declaring it while running the full DDL path ran the whole suite green. A `SchemaHarness` — a store whose schema does not exist yet, plus the host's own migration — is supplied via `run_contract_suite(schema_harness_factory=…)` or `--schema-harness`, and `C0-09` then proves the verify-only claim against a third-party adapter. The asymmetry was itself a finding: generalising one of the two and describing the pair as fixed is how a document stops being true.
   - **The precondition is checked too, and has its own id.** Verifying `transaction_scope="savepoint"` means `C0-12` *and* `C0-13`; a `BorrowedHarness` that supplies no `idle_adapter` leaves the second unexercised, and the coverage block says which.
   - **When nobody supplies a harness, the verdict says so:** the leg reads `CONFORMANT, DECLARATIONS UNVERIFIED` and the block names the declaration and the id that would have checked it. Conformance may be claimed on trust; it may not be claimed *silently* on trust.

   - **The `DECLARATIONS UNVERIFIED` verdict was dead code for a whole class of adapter, and that was itself a finding** *(third adversarial round)*. It read the declaration off the plain `adapter_factory` — and ruling R5's shape is an adapter that is `"owned"` when it opens its own connection and `"savepoint"` only when one is lent to it, which is exactly what beacon will build. Such a factory honestly declares `"owned"`, the predicate never matched, and **a savepoint adapter with the precondition check deleted reached a clean `CONFORMANT`.** The verdict now reads the declaration of the adapter the harness actually hands over, and treats *"no harness supplied"* as its own unverified declaration: silence about a mode is not evidence the mode is absent.

   **The two harnesses, importable from `ontoloche.contract.harness`:**

```python
@dataclass(frozen=True)
class BorrowedHarness:
    adapter: Any                    # your adapter, over a connection YOU own
    outsider: Callable              # outsider(name) -> row count, from another connection
    host_begin: Callable            # put your transaction on the connection
    host_open: Callable             # -> bool: is it still open?
    host_commit: Callable           # commit it
    teardown: Callable              # dispose of everything this factory made
    idle_adapter: Callable | None = None      # ...over a connection with NO transaction. C0-13
    aborted_adapter: Callable | None = None   # ...over one whose transaction FAILED. C0-13
    second_adapter: Callable | None = None    # a SECOND adapter on the same connection. C0-14

@dataclass(frozen=True)
class SchemaHarness:
    guest: Callable                 # your adapter over a store whose schema does not exist yet
    create_host_schema: Callable    # your host's own migration
    teardown: Callable
```

   The async suite takes the same shapes with coroutine callables. Nothing checks the type — an object with these attributes does as well — and the optional fields are optional: omitting one costs you the id it would have exercised, listed in the coverage block, not a refusal.

   **Verified to bite** *(third adversarial round, through the third-party path)*: a savepoint-declaring adapter that commits at depth 0 fails `C0-12` **and** `C0-13`; one that is honest about savepoints but omits the precondition check fails `C0-13` alone; one that declares `owns_schema=False` and issues DDL anyway fails `C0-09`; and one that supplies no harness at all — or a harness missing the optional adapters — reads `CONFORMANT, DECLARATIONS UNVERIFIED` with the unchecked claims named. Before these rounds every one of them ran the suite to a clean `CONFORMANT`.

**What it changed the moment it existed** *(row 3d, [Observed])*: `C0-09`, whose entire subject is `owns_schema=False`, was being **skipped on the one leg that declares `owns_schema=False`**, with the reason *"owns_schema is a property of the reference backends"*. `C0-08` was skipped there with the reason *"no adapter factory"*. Both were written before the third leg existed and neither was visible in `330 passed`. Both are now exercised on that leg — `C0-08` for its G1 half, and it says in its skip reason that the G2 half has no proposal to race.

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

Sample: `sample_state.csv`, the first 400 Montana rows of `NH_HealthCitations_Aug2026.csv` (CMS Provider Data Catalog, downloaded 2026-08-28). Ground truth frozen in `0.5-ground-truth-PREREGISTERED.md` as `093f102`, before any proposal was generated.

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

**Caution on the one [Inferred] count.** The seven severity codes present in the sample (B, C, D, E, F, G, J) come from `0.5-RESULTS.md`'s quotation of run **D**, which is the run that got the *ordering* backwards. The letter list itself was not among the two claims verified as errors, but it was also not independently counted. **The contract test must compute this number from the sample rather than assert it**, and record it — grading against a number taken from an unverified quotation is exactly the moved-target failure the pre-registration exists to prevent. The four `[Observed]` counts are asserted; this one is computed and reported.

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

**Task for deliverable #3:** check the 400-row public sample in at `ontoloche/contract/fixtures/cms_sample_400.csv` (~80 KB), and add a `make_sample_state.py` that regenerates it from the public file so the provenance is checkable. Until it exists, the C13 group is `skipif`-gated on the fixture and **the CMS design test is therefore not yet runnable — it is specified, not passing.** Said plainly so nobody reads §8.2 as a result.

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

> **One generation exception, and it is deliberate.** A thread race has no mechanical async form — the async equivalent of two threads is `asyncio.gather` over two coroutines, a *different mechanism* rather than a token substitution. `tools/unasync.py` therefore excludes **`contract/test_c0_backend_local.py`** by name (`HAND_WRITTEN_ASYNC`), and **`aio/contract/test_c0_backend_local.py`** is maintained by hand, the way the driver-level `close()` methods are (`3B-ASYNC.md` D-A12). It holds the **three** contract tests that **build backends directly** rather than taking the `adapter` fixture — `C0-08`'s thread race, `C0-09`'s `owns_schema=False` construction (whose async form is `await AsyncSQLiteAdapter.open(...)`, D-A1), and, since row 3d, `C0-12`'s borrowed connection, which needs a *host* connection the fixture cannot supply. *(Said "two" until row 3d; corrected there, and it is the paragraph that explains why these three are the tests most likely to be under-generalised — see §6.4 on unverified declarations.)* **It is the only contract module in the suite that is not generated**, and the exclusion is a named constant so it cannot grow quietly. *(Filenames corrected by row 3c: the module was renamed from `test_c0_concurrency.py` when `C0-09` was folded in, and this paragraph did not follow.)*

**The capability sweep, and the two registry defects it found.** §3.2 says every optional flag may be `False`. **[Observed] six of eight could not**, one at a time. Most were scaffolding, but two were real:

- **`indexes_membership=False` defeated the kill row.** `merge_types`' refusal #2 compares the two extents; on such a backend every extent is empty, so two predicates with genuinely different members compared **equal**, the *non-overridable* `predicate_merge` refusal never fired, and the merge fell through to the *overridable* `no_consumer_evidence` guard. **`ROADMAP.md`'s kill criterion — "a capability predicate gets merged as a duplicate" — tripped, on the declared capability shape of Tenshen's own table (§7.3 B3).** Rule U: an extent that could not be computed is not a byte-identical extent. Fixed; refuses non-overridably, naming the unknowability.
- **`cannot_record_override` was checked before the four non-overridable guards**, so a caller trying to acknowledge past the kill row was told the audit log was missing rather than that the merge was forbidden — the wrong reason for the right outcome. Moved after them.

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

**What "the columns the adapter needs" means, and why it is derived rather than listed** *(row 3e, first adversarial round)*. Until that round the check listed seven `oo_type` columns and nothing else — so the first migration to touch any other table (store version 3, `oo_proposal.source_version`) was **unverifiable on exactly this path**: **[Observed]** a host store laid down from an older revision of this package's DDL passed `migrate()` with no complaint and then died on a raw driver error at the first `propose_type`. The check now derives the other two tables from this backend's own column tuples — `oo_proposal` when it declares `stores_proposals`, `oo_attr_schema` when it declares `stores_attributes` — so a column a future store version adds is covered the moment it is added and nobody has to remember. `oo_type` stays hand-listed, because a backend over a schema it does not own may legitimately have fewer of those and project the rest (§5.7).

> **The version NUMBER is deliberately not the check.** Comparing `oo_schema_version` against this package's latest migration looks like the one-line version of the same fix and is wrong here: when `owns_schema=False` that row is the **host's** statement about a schema the host maintains, and it need not track this package's migration numbering at all — `sqlite_minimal` is a live example, a correct five-table host schema that says version 1. Refusing on the number would fail an honest host whose columns are all present, which is the shape ruling **R14** named when it declined to punish an adapter for having no borrowed mode. **The columns are the fact; the number is a claim.** `C0-09`.

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

### 9.6 Store version 2 — `oo_attr_schema` gains `name` *(ruling **R10**, row 3e, 2026-08-29)*

The first store-schema revision this package has shipped, and it is the case §9.4 was written for.

| | |
|---|---|
| **migration** | `backends/migrations/{sqlite,postgres}/0002_name_level_attr_schemas.sql` |
| **shape** | `DROP TABLE oo_attr_schema`, then recreate with `name TEXT NOT NULL DEFAULT ''` and `PRIMARY KEY (namespace, kind, name, version)` |
| **what it discards** | **every attribute schema registered against a v0 store.** Nothing else. |
| **what it does not touch** | `oo_type`, `oo_proposal`, `oo_event`, `oo_consumer`, `oo_usage`, `oo_type_predicate`, `oo_attr_observed` — the vocabulary, its provenance, its consumers and the census all survive |

**Drop-and-recreate is exercised, not merely permitted.** §9.4 says a `v0` store may be dropped and rebuilt rather than migrated and that this package promises no migration path between v0 schema revisions; the practical form of that promise is that anything in a v0 store that matters must be reproducible from its source. An `AttributeSchema` is **deployment configuration** (§5.2) — it is written by the deployment, from the deployment's own source, and re-registering it is one call. That is why this revision spends the permission here rather than writing an `ALTER`: the data it discards is the one kind in the store that is reproducible by definition.

**What survives is chosen, not incidental.** `oo_type.attr_schema_version` is untouched, so an entry written under a schema this migration drops **still says which generation of `attributes` it belongs to** (§5.4: entries are never rewritten and never retroactively invalidated), and `oo_attr_observed` keeps the spread of versions per key, so `attribute_census` still reports what was written and under what. A migration that dropped those too would have made §5.4's promise unkeepable, which is a different and much worse thing than dropping a config table.

**A store still at version 1 is not read under version-2 assumptions.** `migrate()` applies `0002` in one transaction with its version row (§9.1); a store at version 2 opened by an older package is refused outright (§9.2). **An `owns_schema=False` store gets no migration and is therefore checked instead, by column** — see §9.3, which is the half of this that row 3e's first adversarial round found missing.

### 9.7 Store version 3 — `oo_proposal` gains `source_version` *(ruling **R21**, row 3e, 2026-08-29)*

`Provenance` gains `source_version` (`INTERFACE.md` §2.4a): the **source's** own version, never ours. On an approved entry it lives inside `oo_type.provenance_json`, where every other provenance field lives, so **`oo_type` needs no column**. A *proposal* is written before its `Provenance` exists, so the value has to survive on the proposal row until approval — otherwise `propose_type(source_version=…)` accepts a value and loses it, which is worse than not accepting one.

| | |
|---|---|
| **migration** | `backends/migrations/{sqlite,postgres}/0003_proposal_source_version.sql` |
| **shape** | `ALTER TABLE oo_proposal ADD COLUMN source_version TEXT` |
| **what it discards** | nothing |

**`ALTER`, not drop-and-recreate — and the contrast with §9.6 is the point.** This column is additive and nullable, so there is nothing to lose and no permission to spend. §9.4's licence to drop a v0 store is a real permission and it is spent only where it **buys** something: §9.6 spends it to change a primary key, on the one table whose contents are reproducible by definition. Reaching for it here, where an `ALTER` does the job, would be treating a stated allowance as a default.

A backend with `stores_proposals=False` has no `oo_proposal` table and is unaffected — such a store returns a `TypeEntry` from `propose_type` (§7.3 B4), so the value goes straight into `provenance_json` with no row to survive on. An `owns_schema=False` store that *does* declare `stores_proposals` is checked by column at `migrate()` (§9.3).

---

## 10. Exit criteria — the brief's, checked

| Criterion (verbatim from the brief) | Where |
|---|---|
| *every adapter primitive has a signature, data shape and uncertainty behaviour* | §3.4 — fifteen primitives, each with all three; the uniform uncertainty rule stated once at the head |
| *both backends have table shapes* | §4.1 (shared logical shape, seven tables; two more in §5), §4.3 (SQLite dialect), §4.4 (Postgres dialect) |
| *the `attributes` mechanism is decided or explicitly declared a v0 gap* | §5 — **decided**: per-kind versioned schemas, three modes, default `off` to keep #1's contract, plus an unconditional census; §5.4 states the behaviour for entries written under an older schema |
| *the contract-test list covers every §5 call and every §5 refusal* | §6.2 (124 tests, seventeen groups — 109 at #3, fifteen added by row 3c) and §6.3 (the refusal-by-refusal coverage table — none untested) |
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

- ~~**The call count.**~~ **Corrected by row 3c**: `INTERFACE.md` §5.10, §12 and §13 said **thirteen**, which is what enumerating §5.1–§5.11 gave (§2.2). **Fourteen since row 3e** (`reinstate`, §5.9b, ruling R11).
- **`INTERFACE.md` §2.1 says the registry never reads `attributes`.** §5 of this document makes reading them possible but off by default, so an untouched deployment matches §2.1 exactly. If #1 adopts the mechanism, that sentence needs a clause.
- **`INTERFACE.md` §9 does not name the `kind` of a `work_link_types` row.** This document determines `kind="edge"` (§7.1) from §2.2's definition.

### 11.2b Recorded by roadmap row 3c (the UC3 validation pass), 2026-08-28

§8b runs the NYC Open Data fixture against this document. The protocol needed **no change** — scoping was already in G1's key and attribute schemas were already keyed on `(namespace, kind)` — and the suite gained the two tests §8b.2 describes (109 → 111). Two contortions are open:

- **B7 — `find_consumers` and `attribute_census` are single-namespace** (§8b.3). Only `TypeQuery.namespace` is nullable, so the ingestion-shaped reader that UC3 describes must register itself once per agency and read one census per agency. The fix is one nullable parameter on each and it is not free — a cross-namespace `find_consumers` makes `ConsumerReport` ambiguous about which scope it answered for.
- **B8 — `C3-08` and `C3-09` assert resolver behaviour, which §2.6 says no contract test may do** (§8b.3). The same `location`-rebuilt-from-its-parts pathology returns `not_a_type/redundant_projection` on CMS's postal-address sibling set and `proposal` on NYC's `latitude`/`longitude` one, because `_PROJECTION_FAMILIES` is a lookup table fitted to the first dataset. A deployment shipping its own resolver — which §2.6 calls the production path — therefore fails the suite that defines conformance for a non-storage reason. **Ruling wanted:** mark the two non-binding the way `C15-02` is, or move them out of the conformance definition. See [`findings/3C-VALIDATION.md`](../findings/3C-VALIDATION.md) §6.

### 11.3 Weaknesses of this design, named now so they are not discovered later

- **A name-level attribute schema cannot be removed** *(row 3e, ruling R10)*. See §5.2b: an override registered once governs that type for the life of the store. In UC3 that is one agency's one-line exception outliving the person who wrote it.
- **`attr_schema_version` is only meaningful next to the entry's own name** *(row 3e, ruling R10)*. Two entries of one kind can carry `attr_schema_version = 1` under two different schemas, because the version sequence is per `(namespace, kind, name)`. §5.2b states the lookup rule that resolves it and the one residual case it does not — a name-level schema registered after an entry was written. The fix is a second column on `oo_type`; it is not taken, and this is the record of that.

- **Attribute schemas have no proposal→approval loop.** They are deployment configuration, not vocabulary (§5.2). A deployment can therefore change how `value_set` attributes validate with no review — which is mechanism **1**, one level down, in the mechanism built to answer §11's worry about mechanism 1. The dogfooding fix (register a schema as a `TypeEntry`) was rejected for a good reason and the cost is real.
- **`list_types(orphaned=)` and `list_types(unverified_semantics=)` are O(types)** on every backend (§3.3), because pushing them into the adapter would put policy in the backend.
- **The deterministic default resolver is not good enough for production** and is not meant to be (§2.6). Every `resolve_type` quality question is a resolver question, and no contract test can catch a bad one.
- **The façade never asks for a bounded page.** `TypeQuery.limit`/`.after` and `TypePage.next_after` (§3.3) are implemented correctly by both reference backends and, since row 3c, tested by `C0-10` — but **one call site in `Registry` passes `after`** — `_active_page`, added by row 3e for §5.9b's collision scan, which pages to exhaustion because a partial page there would be a confident *no collision* (see §5.9b). Nothing else passes either, so `list_types(namespace=None)` is an unconditional full fetch. §3.3 already accepts O(types) *"at the scale this registry is for"*, so this may be right; what makes it a decision rather than a bug is that paging internally would need `TypeListing.known` to say whether it counts the page or the set, and Rule K has no answer. **Ruled — R13 (row 3d): the facade stays unbounded in v0 and §3.3 now says so in full; the `TypeListing` paging design is Phase 3's, because the ingestion loop is the consumer that would force it and would also settle what `known` should say.**
- **`record_use` has no batch form.** CMS's real file is 419,479 rows and the design test only ever runs the 400-row sample (§8.4), so one `get_type` + one `bump_usage` per row has never been measured at that scale. Every backend pays it equally, so it is not a conformance question — recorded so it is not discovered for the first time during an actual CMS-scale run.
- **`ConsumerReport.complete` is `False` forever**, so `merge_types`' consumer-set guard operates on known sets only — `INTERFACE.md` §5.10 already takes the weaker rule, and this package cannot strengthen it.

### 11.4 What would change this document

| If… | Then |
|---|---|
| the founder rules **async is a separate deliverable** | the ordering table gains a row between #3 and #5, and 2B's date moves |
| **A5 is reopened** (2A's contract tests stop being the 2B gate) | §6.1's conformance rule loses its authority; the suite becomes internal QA rather than a gate |
| **A4 lands *do-not-file*** (Q7a) | `usage()` becomes the venture's only rot sensor — and §7 B5 says beacon's backend **cannot supply it**, so `last_used_at` moves from *nice* to *load-bearing*, and the Tenshen backend stops being able to carry the core-bet experiment at all |
| **A1 is wrong** and semantic collision is dominant | `oo_type`'s primary key already carries `namespace`, so the schema survives; `merge_types` and its eight tests are deleted rather than guarded |
| the partner agency reports **plain duplicate sprawl, no predicate structure** | `oo_type_predicate` becomes overhead rather than the load-bearing join, and C1/C2 (13 tests) shrink to a handful |
| a **second real backend** appears that cannot meet **G1** (an eventually-consistent store) | the conformance definition itself must change — G1 is currently non-negotiable, and that is a bet that the registry's scale never needs a store that cannot do it |
