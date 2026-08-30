# 2A-RUN — the Phase 2A run record

> **Package renamed** `open_ontology` → `ontoloche` at commit <rename-sha> (2026-08-30); the commands and paths quoted below are as recorded at the time.

**Status:** deliverable **#3** landed 2026-08-28. The reference implementation, the 109
contract tests, and the CMS design test.
**Result:** **the whole suite is green on both reference backends, in one process, in one
run.** The CMS design test executes and reproduces every pre-registered ground-truth
count. Per **A5** this is the Phase 2B gate.
**Implements:** [`INTERFACE.md`](../specs/INTERFACE.md) v0 and [`PACKAGE.md`](../specs/PACKAGE.md) v0.
Fourteen recorded deviations, none silently resolved — §4.

---

## 1. The result

```
$ OO_POSTGRES_DSN=postgresql://…@localhost:55432/open_ontology \
  python -m pytest --pyargs open_ontology.contract -q
........................................................................ [ 31%]
........................................................................ [ 62%]
........................................................................ [ 94%]
.............                                                            [100%]
229 passed in 49.25s
```

| Leg | Result | Command |
|---|---|---|
| **SQLite** | **113 passed, 0 failed** | `pytest --pyargs open_ontology.contract -k sqlite` → `113 passed, 116 deselected in 0.91s` |
| **Postgres 16.14** | **113 passed, 0 failed** | `pytest --pyargs open_ontology.contract -k postgres` → `113 passed, 116 deselected in 47.98s` |
| Backend-independent | 3 passed | `C0-04` (source inspection), `C14-07` (no default type), the manifest check |
| **Both, one run** | **229 passed, 0 failed, 0 skipped** | the command above |

Without a Postgres to talk to, the Postgres leg **skips with a reason** rather than
vanishing — a leg that disappears from a run is a leg nobody notices is missing:

```
$ python -m pytest --pyargs open_ontology.contract -q
116 passed, 113 skipped in 0.89s
```

### Test-count arithmetic, so nobody has to reverse-engineer it

`PACKAGE.md` §6.2 enumerates **109 ids in seventeen groups**, and calls that *the
coverage floor, not a budget*. All 109 exist; `test_manifest.py` fails if one goes
missing or if a test claims an id the enumeration does not contain.

| | count |
|---|---|
| contract ids enumerated by `PACKAGE.md` §6.2 | 109 |
| …of which are backend-independent (`C0-04`, `C14-07`) | 2 |
| …parametrised over a backend | 107 |
| `C4-09` is parametrised over 7 malformed names, so it collects | 7 items, not 1 |
| **pytest items per backend leg** | **113** |
| two legs + 2 backend-independent + 1 manifest check | **229** |

### Environment

| | |
|---|---|
| Python | 3.13.14 (floor is 3.11; `requires-python = ">=3.11"`) |
| SQLite | 3.50.4 (bundled with CPython) |
| Postgres | 16.14 (`postgres:16-alpine`, Docker, port 55432) |
| psycopg | 3.3.4 |
| pytest | 9.1.1 |
| Runtime dependencies of the package itself | **zero** |

---

## 2. Reproducing it

```bash
cd C:\Users\steph\projects\open-ontology
py -3.13 -m venv .venv
.venv\Scripts\python.exe -m pip install -e ".[contract]"

# 1. the SQLite leg alone -- no dependencies, no services, no configuration
.venv\Scripts\python.exe -m pytest --pyargs open_ontology.contract -q

# 2. the Postgres leg. Any Postgres will do; this is the one the run above used.
.venv\Scripts\python.exe -m pip install "psycopg[binary]>=3.1,<4"
docker run -d --name oo-pg -e POSTGRES_PASSWORD=openontology \
  -e POSTGRES_DB=open_ontology -p 55432:5432 postgres:16-alpine

# 3. both legs, one process, one run -- this is the conformance run
set OO_POSTGRES_DSN=postgresql://postgres:openontology@localhost:55432/open_ontology
.venv\Scripts\python.exe -m pytest --pyargs open_ontology.contract -q
```

Regenerating the CMS fixture from the public file (it is checked in, so this is only
needed to verify its provenance or to cut a new month's slice):

```bash
.venv\Scripts\python.exe tools\make_sample_state.py --download
```

Running the suite against a backend this package has never heard of:

```bash
python -m open_ontology.contract --adapter beacon.ontology:WorkLinkTypeAdapter
```

---

## 3. The CMS design test — counts against the pre-registered ground truth

The source file downloaded from the CMS Provider Data Catalog on 2026-08-28 is
**165,336,194 bytes — byte-for-byte the size
[`0.5-ground-truth-PREREGISTERED.md`](../findings/0.5-ground-truth-PREREGISTERED.md) records for the
file 0.5 used.** So the fixture is the sample 0.5 actually cut, not a lookalike.

**Eight type rows, not four hundred.** The registry stores types, not instances; the 400
rows land as eight `TypeEntry` rows plus their instance counts in `usage`. Reading "the
sample loads" as "400 citations become types" is the T3/T6 failure the ground truth
predicted, committed by the harness instead of by a model — `C13-01` asserts against it.

| `kind` | `name` | rows | `usage.count` | pre-registered | match |
|---|---|---|---|---|---|
| `entity` | `facility` | 1 | **10** | 10 **[Observed]** | ✅ |
| `entity` | `survey` | 1 | **69** | 69 **[Observed]** | ✅ |
| `entity` | `citation` | 1 | **400** | 400 **[Observed]** | ✅ |
| `entity` | `deficiency_tag` | 1 | **92** | 92 (T5) **[Observed]** | ✅ |
| `value_set` | `deficiency_corrected_status` | 1 | **4** present (6 full-file) | 4 / 6 (T1) **[Observed]** | ✅ |
| `value_set` | `scope_severity_code` | 1 | **7** | **[Inferred]** — computed, not asserted | see below |
| `edge` | `issued_during` | 1 | **400** | 400, from the grain | ✅ |
| `edge` | `conducted_at` | 1 | **69**, from the survey count | 69 | ✅ |

**Totals: 8 rows in `oo_type`, 8 in `oo_usage`, 8 in `oo_proposal`, 16 in `oo_event`
(a `proposed` and an `approved` per type), 0 in `oo_consumer`** — nothing in a CSV
registers a consumer, and `consumers("facility")` correctly reports `known: 0,
complete: False`.

### The one [Inferred] count, computed rather than asserted

`PACKAGE.md` §8.2 marks the severity-code count **[Inferred]** and instructs that the
test *compute this number from the sample rather than assert it*, because the letter
list was quoted from run **D** — the run that got the ordering backwards — and was never
independently counted. Grading against a number taken from an unverified quotation is
exactly the moved-target failure the pre-registration exists to prevent.

> **Computed independently on 2026-08-28: 7 distinct codes — B, C, D, E, F, G, J.**

That confirms the quotation rather than relying on it. `C13-02` prints the number and
records it as a pytest property; it asserts equality against the *computed* value only.

### The other ground-truth facts the fixture reproduces

| Trap | Ground truth | Computed from the fixture |
|---|---|---|
| T5 — description is a lookup on the tag | 92 tags, **0** with more than one description | 92 tags, **0** ✅ |
| T3 — `Location` is a redundant projection | **400 of 400** exactly rebuilt from four sibling columns | **400 of 400** ✅ |
| T7 — `Processing Date` is an export stamp | single-valued | **1** distinct value ✅ |

`C3-08` and `C3-09` turn the last two into behaviour: `resolve_type("location", …)`
returns `not_a_type` / `redundant_projection` and `resolve_type("processing_date", …)`
returns `not_a_type` / `export_artefact`, rather than the `None` that reads to any
caller as *"go propose it"*.

### The severity case, end to end

`C5-03` runs `INTERFACE.md` §10's worked example verbatim. A `haiku`-tier `value_set`
proposal defining the scale as *"Higher letters are LESS serious"* with no evidence
comes back carrying `no_evidence` and `unverified_semantics`, is **refused** for
auto-approval with `tier_below_auto_approve_policy` (`detail={"tier": "haiku",
"min_auto_approve_tier": "sonnet"}`), and — if a human approves it anyway — keeps
`unverified_semantics` permanently and is enumerable through
`list_types(unverified_semantics=True)`.

---

## 4. Deviations

Where the docs and the implementation could not both be satisfied, **the code follows
the docs and the conflict is recorded here rather than resolved silently.** Where the
two documents disagree with each other, `PACKAGE.md`'s own header rule applies:
**`INTERFACE.md` wins.**

### 4.1 The one that wanted a founder ruling — **resolved by R4**

> **RESOLVED 2026-08-28 by ruling R4** ([`decisions/2026-08-28-package-v0-rulings.md`](../decisions/2026-08-28-package-v0-rulings.md)),
> implemented in row **3c**. Option 1 below was taken: `consumer_source_read_only` is the
> fifteenth value of `INTERFACE.md` §5.12, added in the same change that made
> `register_consumer` return `Refusal(reason="consumer_source_read_only")` — which is R3's
> own amendment rule, not an exception to it. `C11-04` asserts the reason in both the sync
> and the async suite; both stayed green. The record below is left as written so the
> reasoning that produced the ruling is still readable.

**D-1 — `register_consumer` against a read-only consumer source raises `NotSupported`;
it does not return a `Refusal`.**

`PACKAGE.md` §3.4 primitive 10 and test `C11-04` both say the registry surfaces this
*as a `Refusal`, never as a silent no-op*. But ruling **R3** closed `Refusal.reason` at
fourteen values (`INTERFACE.md` §5.12), and **none of the fourteen says this honestly** —
`proposals_not_stored` is about proposals, `cannot_record_override` is about an audit
trail, and reusing either would be the confident wrong answer Rule U forbids.

Three options, and why the third was taken:

1. Return a `Refusal` with a fifteenth reason → violates §5.12, and §5.12 says the suite
   must assert the vocabulary is closed. Adding a value is a product decision R3 just
   made in the other direction.
2. Reuse an existing reason → dishonest, and Rule U exists to prevent exactly this.
3. **Raise `NotSupported`** → a loud, typed, unmissable failure. What `C11-04` is
   actually about is that this is **never a silent no-op**, and a raised exception is the
   loudest available answer.

`C11-04` asserts the exception and that nothing was written, and carries this reasoning
in its docstring. **Ruling wanted: add a fifteenth reason (say `consumer_source_read_only`)
and amend §5.12 in the same change per R3, or confirm the exception.** Everything else
here is a note; this one changes a document.

### 4.2 Shapes that gained a field the docs require but do not list

| id | Deviation | Why it was forced |
|---|---|---|
| **D-3** | `TypeEntry.warnings` exists | `INTERFACE.md` §2.1's field table omits it, but §5.4 (`name_previously_retired`), §5.5 (*the entry keeps the warning*) and §5.9 (`retired_without_usage_evidence`) all describe returned entries carrying warnings, and `PACKAGE.md` §3.3/§4.1 store them on `TypeRecord`/`oo_type.warnings_json`. §5.5 words it as *"keeps the warning on `provenance`"*; it is implemented as a top-level field, mirroring the storage shape. Tests: `C4-08`, `C5-06`, `C9-03`. |
| **D-4** | `Provenance.history_why: str \| None` | `PACKAGE.md` §3.4 primitive 15: *`stores_events=False` ⇒ the registry returns `history == []` **with a `why`***. `INTERFACE.md` §2.4 has nowhere to put it, and an empty history with no explanation is `[]` standing in for "we did not look". |
| **D-5** | `TypeListing.excluded_unknown: int \| None` | `C6-05`: *`orphaned=True` **excludes** types whose `orphaned` is `None`; **the count of excluded-as-unknown is reported***. §5.6's four fields have nowhere to report it. |
| **D-12** | `Resolution.alternatives` items are `tuple[str, float \| None]` | §5.3 types them `tuple[str, float]`, but `C3-07` requires a prior rejection to surface in `alternatives` and nothing scored it. `0.0` would be Rule U's forbidden zero. `None` says *we did not score this*. |

### 4.3 Return types the docs widen elsewhere

| id | Deviation | Why |
|---|---|---|
| **D-10** | `propose_type` may return a `Refusal`, and `reject` may return a `Refusal` | `PACKAGE.md` §5.3 requires `propose_type`/`approve` to return `Refusal("attributes_schema_violation")` under `enforce`, and §3.6 requires `proposals_not_stored` from `approve`/`reject`. Neither is in `INTERFACE.md` §5.4/§5.5's signatures. `reject` also needs an answer for an unknown or already-decided id. Tests: `C15-04`, `C5-04`. |
| **D-11** | Under `approval_policy="auto"`, a proposal below `min_auto_approve_tier` **stays pending** and comes back as a `Proposal` carrying `auto_approval_refused:tier_below_auto_approve_policy` | Neither document says what happens when the auto path meets the tier gate. Returning a `TypeEntry` would let the severity case escape the gate by policy; returning a `Refusal` would discard a valid proposal. Falling back to review loses nothing and is the behaviour §2.7's gate exists to produce. On a `stores_proposals=False` backend there is nowhere to hold it, so that case is a `Refusal("tier_below_auto_approve_policy")`. |

### 4.4 Methods beyond the twelve

| id | Deviation | Why |
|---|---|---|
| **D-2** | The attribute-schema and census tables are reached through an **optional `AttributeStore` protocol, outside the fifteen primitives and outside conformance** | `PACKAGE.md` §5 specifies `oo_attr_schema` and `oo_attr_observed` and one façade method, but **adds no primitive to carry them** while §3.4 stays at fifteen and `C0-04` polices the boundary. Ruling **R2** already keeps `attribute_census` package-local and outside the conformance definition, so the storage for it is too. A backend that does not implement the extension is still fully conformant, and `attribute_census` then reports `complete=False` with a `why` rather than an empty census. |
| **D-8** | `Registry.import_types` | `INTERFACE.md` §2.5 states the Foundry status mapping *"here, not left to an importer"*, and `PACKAGE.md` §6.2's **C12 group tests it** — but no §5 call performs it. It had to live somewhere callable. |
| **D-7** | `merge_types(into_namespace=…)` | `INTERFACE.md` §5.10 takes a single `namespace`, which makes a cross-namespace merge **unexpressible** — and therefore makes refusal #4, `cross_namespace_merge` (`C10-04`), unreachable. One additive keyword argument, defaulting to `namespace`. |
| — | The façade exposes **thirteen** §5 methods plus three package-local ones (`import_types`, `register_attribute_schema`, `attribute_census`) | The counting note in `PACKAGE.md` §2.2 and §11.2 stands and is unchanged by this deliverable: `INTERFACE.md` says *twelve calls*, enumerating §5.1–§5.11 gives thirteen. Nothing depends on which number is right. |

### 4.5 Behaviour the docs specify in two places that disagree

**D-6 — `unverified_semantics` is detected by a conservative keyword rule.**

`INTERFACE.md` §2.8 says plainly: *"v0 does not attempt to detect automatically whether
a definition asserts a domain semantic. That is a model judgement and belongs to the
proposer."* But §10's worked example produces `p.warnings == ["no_evidence",
"unverified_semantics"]` from a `propose_type` call carrying no such flag, and
`PACKAGE.md` `C4-06` asserts the same. A flag-only design cannot satisfy §10; a
detection-only design contradicts §2.8.

Implemented as a keyword rule over the definition (ordering / severity / scale / rank /
threshold / regulatory / compliance / Immediate Jeopardy / …), plus `kind="value_set"`
with `attributes["ordered"]`. **It deliberately over-warns rather than under-warns:** a
spurious `unverified_semantics` costs one enumerable entry, and a missed one is the 0.5
severity inversion going unlabelled. If §2.8 is meant literally, the fix is an explicit
proposer-supplied flag on `propose_type`, which is an `INTERFACE.md` change.

### 4.6 Test-harness and layout notes

| id | Deviation |
|---|---|
| **D-9** | `C16`'s whole-store invariants run over a store driven through **every write path the suite uses** (propose, auto-approve, amend, reject, retire, merge, import, `record_use`), not literally over everything the suite wrote. The suite's adapters are function-scoped so a failure in one test cannot make another fail for the wrong reason, and a session-scoped shared store would trade that isolation for a phrase. |
| **D-13** | `C0-03` and `C3-02` assert the store is unchanged via a digest read through the **public primitives** rather than a byte comparison. "Byte-identical" is not portable across two backends whose on-disk formats differ by design, and reading through the protocol is the stronger test: it catches a write that landed, not merely a file that changed size. |
| **D-14** | Layout additions beyond `PACKAGE.md` §2.1: `contract/doubles.py` (the degraded backends that make capability-honest tests possible), `contract/_support.py` (the CMS harness and shared helpers), `contract/test_manifest.py` (suite bookkeeping, not one of the 109), and `tools/make_sample_state.py`. The shared SQL adapter base lives **inside** `backends/_sql.py` rather than in a new private module, to keep §2.1's file list exact. `errors.py` carries `AmbiguousKind` and `NotSupported` beyond the four §2.2 names; both are referenced by §3.4 and had nowhere else to live. |
| **D-15** | `PACKAGE.md` §8.4 estimates the fixture at ~80 KB. It is **152,927 bytes** — the `Deficiency Description` column is long. Still trivially small; noted only so the number in the doc is not quoted onward. |

### 4.7 One thing that is not a deviation, recorded because it looks like one

`C11-04`, `C7-01`, `C7-02`, `C7-03`, `C7-06`, `C2-02`, `C6-02`, `C9-02`, `C10-08`,
`C14-02` and `C14-06` all need a backend that declares a capability `False`. Both
reference backends declare every flag `True`, so those tests run against
`contract/doubles.DegradedAdapter`, which wraps a real backend and **actually behaves**
like one with that gap — `bump_usage` really is a no-op, `read_events` really raises,
membership really is unindexed. This is not a weakened test: `PACKAGE.md` §6.1's first
rule is that a test whose subject is a declared-`False` capability asserts the *honest
unknown*, and there is no other way to assert it. It is also the cheapest available
check on §7's claim that a one-table registry can be conformant without weakening
conformance.

---

## 5. What this does and does not establish

**Does.** Two unlike backends — one stdlib, zero-dependency, file-or-memory; one a real
Postgres server with `jsonb`, `timestamptz` and `SELECT … FOR UPDATE` — satisfy the same
109 tests in one process, in one run. The CMS vocabulary loads through the adapter and
its counts match a ground truth frozen before any proposal was generated. Per **A5**,
the Phase 2B gate is met.

**Does not.** The two reference backends are both SQL, and both declare every capability
`True`. The interesting half of the conformance claim — *an unlike backend with real gaps
is conformant without weakening conformance* — is exercised by `DegradedAdapter`, which
is a wrapper this repository wrote, not a third party's store. **The first real test of
that claim is `work_link_types` behind the adapter, which is 2B.**

Nothing async exists *in this deliverable*, per ruling **R1**: that is row **3b**, which
**landed 2026-08-28** — see [`3B-ASYNC.md`](3B-ASYNC.md). The async mirror is generated
from the code recorded here, so **all fourteen deviations below are inherited by it
unchanged**, D-1's wanted ruling included — **and D-1's resolution by R4 is likewise
inherited, because the async mirror regenerates from the sync source.**

---

## 6. Landing checklist against the brief

| Brief item | Where |
|---|---|
| Package skeleton per `PACKAGE.md` §2, project venv, generated data out of git | `pyproject.toml`, `open_ontology/`, `.gitignore`; the 165 MB CMS source is ignored, the 153 KB derivative is the fixture |
| The registry layer — the twelve calls, refusals per §5 and §5.12 | `open_ontology/registry.py`; `Refusal` validates against the closed vocabulary at construction (fourteen values at 2A; **fifteen since ruling R4**) |
| SQLite backend, whole suite green in one run | ✅ `113 passed` |
| The contract suite — all 109, parametrised exactly as §6 specifies | ✅ `test_manifest.py` proves all 109 ids exist |
| Postgres backend, conformance leg | ✅ **green**, not pending — Postgres 16.14 via Docker, no system-level install |
| The CMS test per §8 | ✅ executes; counts match the pre-registered ground truth |
| Run record with the exact commands | this file |
| Nothing async, no EDGES, no ingestion, no HTTP | ✅ — R1 respected; the package imports no web framework and has zero runtime dependencies |
