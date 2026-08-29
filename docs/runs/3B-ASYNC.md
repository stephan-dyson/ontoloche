# 3B-ASYNC — the async mirror, and the run record

**Status:** deliverable **#3b** landed 2026-08-28. `AsyncStorageAdapter`, `AsyncRegistry`,
two async reference backends, and the same 109 contract tests executed against them.
**Result:** **the whole suite is green on both async backends, in one process, in one
run** — and the sync suite is still green in the same process alongside it.
**Answers ruling R1** (`docs/decisions/2026-08-28-package-v0-rulings.md`): beacon is
`AsyncSession` throughout, so ROADMAP #5 cannot land on a synchronous adapter.
**Inherits** all fourteen deviations of [`2A-RUN.md`](2A-RUN.md) §4 unchanged; the
fourteen new ones are §5 here.

---

## 1. The result

```
$ OO_POSTGRES_DSN=postgresql://…@localhost:55432/open_ontology \
  python -m pytest --pyargs open_ontology.aio.contract -q
........................................................................ [ 26%]
........................................................................ [ 53%]
........................................................................ [ 80%]
...................................................                      [100%]
267 passed in 61.22s (0:01:01)
```

And the sync suite, unchanged and still green — this is the same working tree, after
every change this deliverable made:

```
$ OO_POSTGRES_DSN=postgresql://…@localhost:55432/open_ontology \
  python -m pytest --pyargs open_ontology.contract -q
........................................................................ [ 31%]
........................................................................ [ 62%]
........................................................................ [ 94%]
.............                                                            [100%]
229 passed in 46.18s
```

Both stacks, both backends, **one process, one run** — which is the only way to be sure
the two are the same thing rather than two things that each pass when run alone:

```
$ OO_POSTGRES_DSN=postgresql://…@localhost:55432/open_ontology \
  python -m pytest --pyargs open_ontology.contract open_ontology.aio.contract -q
........................................................................ [ 14%]
........................................................................ [ 29%]
........................................................................ [ 43%]
........................................................................ [ 58%]
........................................................................ [ 72%]
........................................................................ [ 87%]
................................................................ [100%]
496 passed in 103.30s (0:01:43)
```

| Leg | Result | Command |
|---|---|---|
| **async SQLite** (`aiosqlite`) | **113 passed, 0 failed** | the 109 ids, parametrised — `-k sqlite` |
| **async Postgres 16.14** (`psycopg` `AsyncConnection`) | **113 passed, 0 failed** | `-k postgres` |
| Backend-independent | 3 passed | `C0-04`, `C14-07`, + the async manifest pair |
| **Both async legs, one run** | **267 passed, 0 failed, 0 skipped** | the command above |
| **Sync suite, after these changes** | **229 passed, 0 failed, 0 skipped** | unchanged from 2A |
| **Everything, one run** | **496 passed** | both suites, both backends |

Without a Postgres to talk to, the async Postgres leg **skips with a reason** rather
than vanishing, exactly as the sync one does:

```
$ python -m pytest --pyargs open_ontology.aio.contract -q
153 passed, 114 skipped in 9.17s
```

And against a backend this package has never heard of — the async entry point, smoke-run
here against its own SQLite adapter, since an async adapter's entry point is normally a
classmethod (see D-A1):

```
$ python -m open_ontology.aio.contract \
    --adapter open_ontology.aio.backends.sqlite:AsyncSQLiteAdapter.open -q
153 passed, 1 skipped in 4.65s
```

### Test-count arithmetic, so nobody has to reverse-engineer it

The 109 ids are the same 109 ids, with the **same test-function names** — not
equivalent ones. `test_manifest.py` in the async suite asserts exactly that:
`implemented_ids() == sync_implemented_ids()`. It can, because every `test_c*.py` in
the async suite is *generated from the sync one*.

| | count |
|---|---|
| contract ids enumerated by `PACKAGE.md` §6.2 | 109 |
| …backend-independent (`C0-04`, `C14-07`) | 2 |
| …parametrised over a backend | 107 |
| `C4-09` is parametrised over 7 malformed names | 7 items, not 1 |
| **pytest items per async backend leg** | **113** |
| two legs + 2 backend-independent | 228 |
| the async manifest pair (ids exist; ids are *identical* to the sync ones) | 2 |
| the anti-drift check (`test_generated_matches_source.py`) | 1 |
| surface parity, sync facade vs async facade (`test_parity.py`) | 34 |
| the concurrent-approval race (`test_concurrency.py`, renamed `test_c0_backend_local.py` and promoted to **C0-08** by row 3c), one per backend | 2 |
| **total** | **267** |

The last four rows are **outside the 109** and marked `nonbinding`. None of them claims
a contract id; the async manifest check fails if one ever does.

### Environment

| | |
|---|---|
| Python | 3.13.14 (floor unchanged: 3.11) |
| SQLite | 3.50.4 (bundled with CPython), driven by `aiosqlite` 0.22.1 |
| Postgres | 16.14 (`postgres:16-alpine`, Docker, port 55432) |
| psycopg | 3.3.4 — **the same driver the sync backend uses**, `AsyncConnection` |
| pytest / pytest-asyncio | 9.1.1 / 1.4.0 |
| Runtime dependencies of the base install | **still zero** |
| New optional dependency | `aiosqlite`, under the `[aio]` extra — and nothing else |

---

## 2. Reproducing it

```bash
cd C:\Users\steph\projects\open-ontology
.venv\Scripts\python.exe -m pip install -e ".[contract,contract-aio,postgres]"

# 1. the async SQLite leg alone -- no services, no configuration
.venv\Scripts\python.exe -m pytest --pyargs open_ontology.aio.contract -q

# 2. the async Postgres leg. Same container the 2A run used.
docker run -d --name oo-pg -e POSTGRES_PASSWORD=openontology \
  -e POSTGRES_DB=open_ontology -p 55432:5432 postgres:16-alpine
set OO_POSTGRES_DSN=postgresql://postgres:openontology@localhost:55432/open_ontology

# 3. both async legs, one process, one run -- this is the async conformance run
.venv\Scripts\python.exe -m pytest --pyargs open_ontology.aio.contract -q

# 4. everything: both stacks, both backends
.venv\Scripts\python.exe -m pytest --pyargs open_ontology.contract open_ontology.aio.contract -q

# 5. regenerate the async mirror after editing any sync source
.venv\Scripts\python.exe tools\unasync.py
.venv\Scripts\python.exe tools\unasync.py --check     # exit 1 if stale
```

Running the async suite against a backend this package has never heard of:

```bash
python -m open_ontology.aio.contract --adapter beacon.ontology:AsyncWorkLinkTypeAdapter.open
```

---

## 3. The design, in one page

### 3.1 The thing that had to be decided first

R1 assumed *"mirroring sync→async is mechanical once the sync suite is green"* and said
that if it is not, **that is a finding, not a licence to redesign #3**. So the first
question was not "how do I write an async registry" but "**how does an async registry
exist without becoming a second copy of the sync one that drifts**" — which is the kill
criterion, verbatim.

Four ways to have one implementation and two calling conventions:

| approach | why not |
|---|---|
| **Async facade over the sync code in a thread pool** | This is the exact hazard R1 names: a sync adapter driven from a thread cannot share beacon's `AsyncSession` transaction. It would satisfy the type checker and defeat the deliverable. |
| **Greenlet switching** (SQLAlchemy's asyncio bridge) | Genuinely one implementation, and genuinely subtle: it makes every accidental blocking call a silent trap, and it costs a `greenlet` runtime dependency in a package whose base install has zero. |
| **Sans-I/O rewrite** — pull the decisions into pure functions over already-fetched records, and give them two drivers | The honest long-term shape, and a redesign of #3. R1 forbids it. |
| **Generate the async source from the sync source, check it in, and fail the suite when it is stale** | Chosen. |

The last one is what `httpcore`, `urllib3` and `elasticsearch-py` do (they generate in
the other direction — async first, sync derived); here the sync package is already
landed and is the source of truth, so the transformation runs sync → async.

### 3.2 What `tools/unasync.py` actually does

It is **AST-driven, not regex-driven**, and it refuses to emit anything it cannot prove
correct. Four mechanisms carry the whole thing:

1. **A fixpoint decides what is `async def`.** Seed the set of awaitable names with the
   fifteen storage primitives (minus `transaction`), the four optional attribute-store
   methods and the SQL layer's connection hooks. Then: any function that calls
   something awaitable is itself awaitable; any *method* whose name is already awaited
   somewhere must be a coroutine even if its own body does no I/O (that is how the
   bodyless `Protocol` stubs become `async def`). Iterate until nothing changes. There
   is no hand-maintained list of "the async methods" to fall out of date.

2. **`await` wraps whole call expressions, with parentheses exactly where Python's
   precedence needs them.** `self._prior_rejections(ns, c)[0]` becomes
   `(await self._prior_rejections(ns, c))[0]` — because `await f()[0]` parses as
   `await (f()[0])` and would await a tuple. The generator adds the parentheses when
   the call's parent node is an attribute access, a subscript, or the callee of
   another call, and not otherwise. Three sites in `registry.py` need them.

3. **`transaction()` is never awaited.** `with adapter.transaction():` becomes
   `async with adapter.transaction():`; the primitive stays a plain call returning an
   async context manager, and `@contextmanager` becomes `@asynccontextmanager`. This is
   the single most common way a mechanical sync→async translation goes wrong, and
   getting it wrong would compile, typecheck, and silently stop rolling anything back.
   `test_parity.py` asserts it in both directions.

4. **Generator expressions become list comprehensions when an `await` lands inside
   one.** `tuple(f(x) for x in xs)` where `f` becomes awaitable builds an *async
   generator*, which `tuple()` cannot consume; `tuple([await f(x) for x in xs])` is a
   plain list. Two sites (`find_types`, `_degrade_type`'s caller). An `await` that
   would land in a **lambda** is not fixable and is a hard error — the generator stops
   rather than emitting it.

Finally it re-parses its own output and validates it. **Nothing is emitted that does not
parse, and nothing is emitted with an `await` outside a coroutine.**

### 3.3 The tree

```
tools/unasync.py                       the transformation (687 lines)

open_ontology/aio/
    __init__.py                        hand-written  — exports
    adapter.py                    ***  GENERATED     — AsyncStorageAdapter, AsyncAttributeStore
    registry.py                   ***  GENERATED     — AsyncRegistry, all sixteen calls
    backends/__init__.py               hand-written  — lazy imports, extras stay optional
    backends/_sql.py              ***  GENERATED     — AsyncBaseSqlAdapter, the fifteen over SQL
    backends/sqlite.py                 hand-written  — the aiosqlite driver
    backends/postgres.py               hand-written  — the psycopg AsyncConnection driver
    contract/
        __init__.py, __main__.py       hand-written  — the runner and its CLI
        conftest.py                    hand-written  — async fixtures, loop policy
        _support.py, doubles.py   ***  GENERATED
        test_c*.py  (17 files)    ***  GENERATED     — the same 109 ids, same function names
        test_manifest.py               hand-written  — the ids are the sync ids
        test_generated_matches_source.py   hand-written — the anti-drift check
        test_parity.py                 hand-written  — surface parity, sync vs async
        test_concurrency.py            hand-written  — the race the sync suite cannot run
                                       (renamed test_c0_backend_local.py by row 3c)
```

---

## 4. Shared, borrowed, generated, forked — the verdict

**Nothing is forked.** Every line of decision logic in this repository exists exactly
once.

| | lines | what it is |
|---|---|---|
| **Generated** from the sync source | **5,417** | the registry, the protocol, the SQL layer, the whole contract suite |
| **Hand-written** in `aio/` | 903 | two drivers, four async-only test modules, the fixtures, the exports |
| The generator itself | 687 | `tools/unasync.py` |
| Sync sources it mirrors | 5,957 | unchanged by this deliverable |

There are exactly **three** relationships between a sync artefact and the async tree,
and no fourth:

1. **Borrowed** — imported, not copied, because it has no I/O in it and therefore no
   sync/async distinction: every record and query dataclass (`TypeRecord`,
   `ProposalRecord`, `TypeQuery`, `TypePage`, …), `Capabilities`, both dialects, the
   whole row↔record mapping, the migration loader **and the migration SQL itself**,
   `errors.py`, `types.py`, `policy.py`, `attributes.py`, `_clock.py`, `_resolve.py`,
   and every pure module-level helper in `registry.py`. The generator computes the
   borrow list *automatically* from what the extracted code actually references.
   `open_ontology/aio/backends/` contains **no migrations directory** — it runs the
   sync package's SQL files.
2. **Generated** — copied and transformed, with the copy checked in and verified.
3. **Hand-written** — the two drivers and the async-only tests. A driver's connection
   layer is the one thing a transformation cannot invent, and this is where the async
   tree is genuinely a second implementation: 903 lines against 5,417.

### How drift is prevented, and the proof that it is

`open_ontology/aio/contract/test_generated_matches_source.py` regenerates the whole
tree in memory on every run and compares it byte for byte. **Verified by breaking it on
purpose:** inserting one comment line into `Registry._require` produces

```
E       AssertionError: the async mirror is stale -- run `python tools/unasync.py`:
E           open_ontology/aio/registry.py
```

The same probe applied to a *borrowed* constant (`CONSUMERS_WHY_INCOMPLETE`) correctly
does **not** fail — the async module imports the same object, so there is nothing to
mirror. That is the whole taxonomy: a sync change either lands in copied code, where
the check catches it, or in borrowed code, where there is nothing to catch. A new
helper or a new import used by copied code changes the generated file's borrow list or
its import block, so it lands in the first category too.

`test_parity.py` covers what a byte comparison cannot: that the generator was asked for
the right things. It reads both classes and asserts the async facade has every sync
call and no extras beyond the documented construction pair, that every call takes the
same parameters, that all sixteen facade calls and fourteen of the fifteen primitives
are coroutines, and that `transaction()` is not one.

**So: R1's assumption is confirmed, with two named exceptions.** Mirroring sync→async
*is* mechanical for the registry, the protocol and the whole suite — 5,417 of 6,320
lines, including every refusal, every warning, every score and every assertion. It is
not mechanical for **construction** (D-A1, a Python language rule) or for the **driver
connection layer** (D-A4/D-A11, where the two libraries genuinely differ). Neither is a
finding against #3's design; both were predictable from the language and the drivers.
**The kill criterion was checked and not tripped: there is no second copy of the
registry logic.**

---

## 5. Deviations

Same rule as 2A: where the docs and the implementation could not both be satisfied, the
conflict is **recorded here rather than resolved silently.** The fourteen deviations of
[`2A-RUN.md`](2A-RUN.md) §4 are **inherited unchanged** — the async mirror reproduces
them exactly, because it is generated from the code that implements them. D-1 wanted the
same founder ruling it wanted in 2A, in two places. **Both were answered at once by ruling
R4 (row 3c, 2026-08-28): `consumer_source_read_only` is the fifteenth `Refusal.reason`,
`register_consumer` returns it, and `C11-04` asserts it in this suite as well as the sync
one — because this suite is generated from that source. D-1 is resolved in both.**

### 5.1 The one that changes a caller's code

**D-A1 — `AsyncRegistry` is constructed with `await AsyncRegistry.open(adapter, …)`,
not `AsyncRegistry(adapter, …)`.**

`Registry.__init__` calls `adapter.capabilities()` and `adapter.migrate()`. Both are
primitives; both must be awaited; **`__init__` cannot be a coroutine.** Three options:

1. Make construction lazy and fetch `caps` on first use → every call site pays for a
   check, and `migrate()`'s loud refusal of a store from the future (PACKAGE.md §9.2)
   stops happening at startup, which is the entire point of doing it at startup.
2. Have the caller await `migrate()` themselves → the sync constructor's contract, and
   a guarantee, silently becomes the caller's problem.
3. **A classmethod.** The generator renames `__init__` to `_open`, which then becomes a
   coroutine like any other method; a hand-written `open` classmethod builds the
   instance with `cls.__new__(cls)` and awaits it. `__init__` is redefined to raise
   `TypeError` with the correct instruction, so the wrong call is loud rather than
   returning a half-built object.

This is **the only difference in the shape of the async API**, and `test_parity.py`
pins it: `open`/`_open` are the only names the async facade is allowed to add.

### 5.2 Environment and harness

| id | Deviation | Why it was forced |
|---|---|---|
| **D-A2** | The async suite needs **pytest-asyncio in auto mode**. `asyncio_mode = "auto"` is in `pyproject.toml`, and `run_async_contract_suite` passes `--asyncio-mode=auto` itself so an installed wheel behaves identically. | pytest-asyncio resolves its `asyncio` marker during **collection**, before `pytest_collection_modifyitems`, so a conftest cannot add the marker late — verified, not assumed. The alternative is `pytestmark = pytest.mark.asyncio` in every generated test module, which is a line the sync source does not have and would be a hand-edit to generated files. Its `pytest_asyncio_loop_factories` hook was rejected for a different reason: it **parametrises** over loop factories, which would change every test id — and identical ids are the deliverable. |
| **D-A3** | On Windows, the async suite selects `WindowsSelectorEventLoopPolicy` at conftest import. | Not a preference. `psycopg` raises `InterfaceError: Psycopg cannot use the 'ProactorEventLoop' to run in async mode` on the platform default, and Windows' default is Proactor. **An application embedding `AsyncPostgresAdapter` on Windows must do the same thing.** The `event_loop_policy` fixture, which would be the tidier place, is deprecated in pytest-asyncio 1.4. |
| **D-A8** | The async suite lives at `open_ontology/aio/contract/`, **not** `open_ontology/contract/aio/`. | A `conftest.py` applies to every directory beneath it, so an async suite nested under the sync one inherits the sync `pytest_generate_tests` and pytest fails collection with `duplicate parametrization of 'backend'`. The alternative was to edit the landed sync conftest to know about a subdirectory; putting every async artefact under `aio/` costs nothing and keeps #3's files untouched. Extends 2A's D-14. |
| **D-A9** | The generated `_support.py` reaches the CMS fixture by a path substitution rather than a copied file. | The 153 KB fixture is checked in once, under the sync suite. The substitution is declarative and **must match exactly once** or generation fails, so a change to that line in the sync source is loud rather than silent. |
| **D-A10** | Four test modules beyond the 109: `test_manifest.py`, `test_generated_matches_source.py`, `test_parity.py`, `test_concurrency.py`. All `nonbinding`; none claims a contract id. **Superseded in part by row 3c:** `test_concurrency.py` was promoted to contract id **C0-08**, given the G1 race as well as the G2 one, and is now binding — it is the hand-written async counterpart of `contract/test_c0_backend_local.py` (both files were renamed from `test_concurrency.py` when `C0-09` joined them), which `tools/unasync.py` excludes by name because a thread race has no mechanical async form. The other three remain `nonbinding`. | Suite bookkeeping, the anti-drift check, surface parity, and the race G2 exists to prevent. Extends 2A's D-14. |

### 5.3 The driver layer

| id | Deviation | Why |
|---|---|---|
| **D-A4** | **Async SQLite is a thread offload, and there is no alternative.** `aiosqlite` is a new optional dependency under the `[aio]` extra. | SQLite has no asynchronous C API: every statement is a blocking call into the library, so *every* async SQLite story in Python is a thread offload. The choice is between the maintained single-purpose wrapper and a private reimplementation of the same design with fewer eyes on it. `aiosqlite` pins each connection to one dedicated worker thread, which preserves `sqlite3`'s connection affinity for free; a `run_in_executor` wrapper over a shared pool would not. **This is not the hazard R1 names.** R1's hazard is *a synchronous adapter driven from a thread by an async caller*, where the caller's transaction and the adapter's are in different worlds. Here the whole adapter is awaited from the caller's loop and the loop is never blocked; which thread the C library runs on is the driver's business. Async Postgres needs no new dependency at all — `psycopg` v3 ships `AsyncConnection` in the package the sync backend already uses. |
| **D-A11** | `AsyncPostgresAdapter.open` takes `connection=` (an already-open connection) where the sync `PostgresAdapter` takes `connection_factory=` (a callable). | A factory that must be awaited is a coroutine function, and "call this to get a connection" stops meaning what it meant. Handing over an already-open connection is the async-native form and is what an embedding application (beacon) will actually have. |
| **D-A12** | `close()` is `async def` on both async backends. | `aiosqlite`'s and `psycopg`'s `close()` are coroutines. The generator never touches `close` — it is hand-written driver code — so this is recorded rather than derived. |
| **D-A13** | `_execute` returns `None` on both async backends, where the sync base returns a cursor. | Nothing in the SQL layer reads that return value, and the sync Postgres backend already hands back a cursor its own `with` block has closed. Async cursors must be closed explicitly (aiosqlite's live on the worker thread), so returning one would hand back a closed object dressed as a live one. |
| **D-A14** | `python -m open_ontology.aio.contract --adapter` accepts a **dotted** attribute (`pkg.mod:Class.open`), where the sync runner accepts only `pkg.mod:Name`. | Because of D-A1, an async adapter's entry point is normally a classmethod. Without this the async runner could not be pointed at its own reference backends, let alone anyone else's. |

### 5.4 Transformation mechanics that are not pure token substitution

Recorded because they are the concrete content of "mirroring is *mostly* mechanical",
and because each is a way a hand-written mirror would have been silently wrong.

| id | Deviation |
|---|---|
| **D-A5** | A generator expression containing an `await` becomes a list comprehension. `tuple(f(x) for x in xs)` builds an *async generator* once `f` is awaitable, and `tuple()` cannot consume one. Two sites. CPython reports a bare `f(x for x in y)` genexp as spanning the *call's* parentheses, so the brackets go just inside them — a detail worth writing down, because getting it wrong produces `tuple[...]`. |
| **D-A6** | `await` is parenthesised when, and only when, the call's parent is an attribute access, a subscript, or another call's callee. `await f()[0]` parses as `await (f()[0])`. Three sites in `registry.py`, all of which would have been a plausible hand-written bug. |
| **D-A7** | `StorageAdapter.transaction`'s return annotation changes from `AbstractContextManager[None]` to `AbstractAsyncContextManager[None]`, and it is the **one** primitive whose async form is not a coroutine. `test_parity.py` asserts both halves. |

---

## 6. What this does and does not establish

**Does.** The async protocol exists, and two unlike async backends — one a thread-offloaded
stdlib SQLite, one a real Postgres server over `psycopg`'s native async — satisfy the
same 109 tests, with the same test-function names, in one process, in one run. The
registry logic behind them is **not duplicated**: 5,417 of the 6,320 lines in the async
tree are compiled from the sync source, and a stale copy fails the suite. The CMS design
test runs on the async stack and reproduces the same pre-registered counts. Per R1, the
async gate for **#5** is met.

The async run also establishes one thing the sync run structurally could not.
`registry.approve`'s docstring says the read and all four writes happen in one
transaction, *which is what turns `already_decided` from a race into an idempotent
refusal*. In one synchronous process that is an argument. `test_concurrency.py` makes it
a test: two registries, two connections, one event loop, `asyncio.gather` over two
approvals of the same proposal — **exactly one `TypeEntry`, exactly one
`Refusal("already_decided")`, one `approved` event in provenance.** SQLite reaches that
through `BEGIN IMMEDIATE` and Postgres through `SELECT … FOR UPDATE`; the two mechanisms
are different and the observable answer is the same.

**Does not.** The async tree has never been driven by an `AsyncSession` it did not
create. R1's actual requirement — *an adapter that can share beacon's transaction* — is
demonstrated here only as far as "the whole adapter is awaited from the caller's loop
and the primitives are coroutines"; the first real test of it is `work_link_types`
behind the async adapter, **which is 2B**. Both async reference backends still declare
every capability `True`, so the interesting half of the conformance claim is still
carried by `AsyncDegradedAdapter`, a wrapper this repository wrote.

And the transformation is a transformation: it is proved correct by the 267 tests it
produces passing, not by a proof. What it guarantees is that the async tree cannot
*silently* fall behind the sync one — not that a sync change is automatically a good
idea in async.

---

## 7. Landing checklist against the brief

| Brief item | Where |
|---|---|
| `AsyncStorageAdapter` — the async mirror of the 15 primitives, same semantics, same capability flags, same refusals | `open_ontology/aio/adapter.py`; `Capabilities` and the closed fourteen `Refusal.reason` values are *borrowed*, not re-declared, so they cannot diverge |
| An async registry facade mirroring the twelve calls, `async def` | `open_ontology/aio/registry.py` — thirteen §5 calls plus the three package-local ones, all coroutines, asserted by `test_parity.py` |
| Async reference backends: SQLite at minimum, Postgres if straightforward | ✅ **both green.** SQLite via `aiosqlite` (justified, D-A4); Postgres via `psycopg`'s `AsyncConnection` — no new dependency, so not PENDING |
| The async conformance run: the same 109 ids, ids identical so the manifest still binds | ✅ `267 passed`; `test_manifest.py` asserts the async ids **are** the sync ids |
| A short doc: the design, what is shared, how drift was avoided, the run record | this file — §3, §4, §1 |
| ROADMAP row 3b updated honestly | `ROADMAP.md` row 3b + the deliverable #3b result section |
| **The sync suite must still be green** | ✅ `229 passed` — §1, and 496 for both suites in one run |
| Every deviation recorded, none silently resolved | §5 — fourteen new, fourteen inherited |
| Kill criterion: stop if the only way through is a second copy of the registry that will drift | **checked, not tripped** — §4 |
| No employer data; public CMS data only | ✅ the same checked-in 400-row public fixture, read from where it already lives |
