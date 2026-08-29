# 3E-RUN — roadmap row 3e: the v0.1 amendments, and what three adversarial rounds did to them

**Row:** 3e. **Date:** 2026-08-29. **Repo:** `open-ontology`, `main`.
**What it carried:** rulings **R6**, **R10**, **R11** (from the 3c pass), plus **R17**, **R19** and **R21** folded in by the supervisor after the row started.
**Why it exists:** `v0` is labelled unstable *precisely so that additive amendments are cheap*. These six rulings are additive and default-off; none of them blocks anything Tenshen needs, which is why the row runs after the transaction seam (3d) and EDGES (#4).

---

## 1. The headline, in numbers

| | before (row 3d) | after |
|---|---|---|
| contract ids (`PACKAGE.md` §6.2) | 129 | **150** |
| sync suite, one run | `340 passed, 64 skipped` | **`388 passed, 80 skipped`** |
| async suite, one run | `374 passed, 64 skipped` | **`421 passed, 80 skipped`** |
| `INTERFACE.md` §5 calls | 13 | **14** (`reinstate`) |
| `Refusal.reason` values (§5.12) | 19 | **21** |
| `warnings` values (§5.4) | 16 | **20**, and **checked mechanically for the first time** |
| store schema version | 1 | **3** |
| `check_spec_drift.py` | 15 shapes, 13 calls, 1 vocabulary | **15 shapes, 14 calls, 2 vocabularies** |

Twenty-one new ids: **eight** from the rulings themselves and **thirteen** from the adversarial loop. That ratio is the row's most honest single number, and §5 is about it.

---

## 2. The two suite tails, verbatim

### 2.1 Sync — `pytest --pyargs open_ontology.contract -q`

```
CONFORMANCE (PACKAGE.md 6.1)
  backends exercised: postgres, sqlite, sqlite_minimal
  resolver: the shipped DeterministicResolver (2.6's fixed point)
  nonbinding tests excluded from the verdict: none
  coverage, per leg (PACKAGE.md 6.4 / ruling R12):
    sqlite          CONFORMANT: 147 ids exercised, 1 not exercisable on this backend (listed)
                      1: PACKAGE.md 5.7 -- this backend stores arbitrary attributes, so a census restricted to its
                        projections has no subject here. C15-02 is the full case.
                         C15-09
    postgres        CONFORMANT: 147 ids exercised, 1 not exercisable on this backend (listed)
                      1: PACKAGE.md 5.7 -- this backend stores arbitrary attributes, so a census restricted to its
                        projections has no subject here. C15-02 is the full case.
                         C15-09
    sqlite_minimal  CONFORMANT: 70 ids exercised, 78 not exercisable on this backend (listed)
                      22: PACKAGE.md 3.2 -- this backend declares indexes_membership=False, which 3.2 says is
                        conformant. This test needs it as scaffolding, not as its subject: this store has no predicate-
                        membership table, so which types satisfy a predicate is not a question it can answer
                         C1-04, C1-09, C10-01, C10-02, C11-01, C12-01, C12-05, C12-06, C2-01, C2-03, C2-04, C2-05, C3-10,
                           C4-08, C6-01, C6-03, C9-01, C9-02, C9-03, C9-04, C9-11, C9-15
                      21: PACKAGE.md 3.2 -- this backend declares stores_events=False, which 3.2 says is conformant.
                        This test needs it as scaffolding, not as its subject: this store has no event table, so there
                        is no audit trail to append to and no history to read back
                         C0-03, C10-05, C10-06, C10-07, C14-03, C16-01, C16-02, C16-03, C16-04, C16-05, C16-06, C3-11,
                           C9-06, C9-07, C9-09, C9-10, C9-12, C9-13, C9-14, C9-16, C9-17
                      21: PACKAGE.md 3.2 -- this backend declares stores_proposals=False, which 3.2 says is
                        conformant. This test needs it as scaffolding, not as its subject: this store has no proposal
                        table: a decision is recorded on the type row and a pending proposal has nowhere to live
                         C15-03, C15-06, C3-06, C3-07, C4-02, C4-04, C4-05, C5-01, C5-03, C5-04, C5-05, C5-06, C5-07,
                           C5-08, C5-09, C5-10, C5-11, C6-06, C8-01, C8-02, C8-05
                      12: PACKAGE.md 3.2 -- this backend declares stores_attributes=False, which 3.2 says is
                        conformant. This test needs it as scaffolding, not as its subject: this store has no attributes
                        column: the host schema owns its columns and arbitrary keys have nowhere to go
                         C12-04, C13-03, C13-04, C13-05, C14-01, C15-01, C15-02, C15-05, C15-08, C15-10, C15-11, C15-12
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
388 passed, 80 skipped in 72.16s (0:01:12)
```

### 2.2 Async — `pytest --pyargs open_ontology.aio.contract -q`

Same three legs, same per-leg numbers:

```
CONFORMANCE (PACKAGE.md 6.1)
  backends exercised: postgres, sqlite, sqlite_minimal
  resolver: the shipped DeterministicResolver (2.6's fixed point)
  nonbinding tests excluded from the verdict: none
  coverage, per leg (PACKAGE.md 6.4 / ruling R12):
    sqlite          CONFORMANT: 147 ids exercised, 1 not exercisable on this backend (listed)
    postgres        CONFORMANT: 147 ids exercised, 1 not exercisable on this backend (listed)
    sqlite_minimal  CONFORMANT: 70 ids exercised, 78 not exercisable on this backend (listed)
    (+2 backend-independent, run once: C0-04, C14-07)
  A conformance claim without its coverage line is not a claim (ruling R12).
421 passed, 80 skipped in 67.83s (0:01:07)
```

**The arithmetic closes on every leg, mechanically rather than by eye:** `147 + 1 + 2 = 150` on both full legs, `70 + 78 + 2 = 150` on the degraded one. The skip count rose 64 → 80 because `sqlite_minimal` declines the capabilities eleven of the new ids need as scaffolding, and says so per id.

---

## 3. The six features, one paragraph each

### R6 — cross-namespace lookup in `resolve_type` (`INTERFACE.md` §5.3.1)

`resolve_type(search_namespaces=…)`. `None` is the v0 behaviour exactly and reads nothing extra. Hits from other namespaces land in `alternatives` as `("<namespace>:<name>", score)`; **the outcome is still decided inside one namespace**, because resolving across them would be §2.6's answer to mechanism 4 deleting itself. An exact match elsewhere, a tombstone elsewhere and a prior rejection elsewhere are all **registry guarantees**, listed with a `None` score when nothing scored them. `complete` is `true` only when every namespace that could contribute was named, the type store answered in full, the proposal store answered in full, and the near-miss cap did not bite — nine rules and two sub-rules, and `why_incomplete` carries **every** applicable reason rather than the first. This closes §10b.1's contortion 8, which was the sharpest finding the UC3 validation pass produced. `C3-12`, `C3-13`.

### R10 — name-level attribute schemas (`PACKAGE.md` §5.2b), store version 1 → 2

`(namespace, kind, name)` schemas **shadow** the per-kind one. Shadowing replaces the *fields* and takes the **stricter** of the two `mode`/`additional` values, applied when a write is validated rather than when a schema is registered — a floor whose ordering the caller can pick is not a floor. `attribute_census`'s `declared` becomes tri-state, `None` whenever any name-level schema disagrees with the per-kind schema about a key **in either direction**. This closes `C15-07`, the limitation recorded in this mechanism's own flagship justification. `C15-10`, `C15-11`, `C15-12`.

### R11 / R19 — `reinstate`, the fourteenth call (`INTERFACE.md` §5.9b)

`reinstate(type, reason, *, reinstated_by, namespace) -> TypeEntry | Refusal`. §5.9 had justified retiring under uncertainty by pointing at a call that **did not exist** — it appeared once in the whole repository, in a subordinate clause. Three refusals, in evaluation order: `successor_active` (the twentieth `Refusal.reason`), `cannot_record_override`, and `alias_collision` (the twenty-first). Per **R19** it covers edge **families** — they are `TypeEntry`s — and never edge **instances**. `C9-09` … `C9-17`.

### R17 — `created_by` gains `derived` (`INTERFACE.md` §2.1)

The first change to a vocabulary taken verbatim from Tenshen's `work_link_types`. Two unrelated fixtures reached for the same missing value: beacon's `EntityMention.match`, whose first value is literally `deterministic`, and UC3's BBL join, which had to claim `user` for a join no user performed. `import:` still maps to `seed` — an import arrives already decided; a rule decides now. `C4-10`, `C16-05`.

### R21 — `Provenance.source_version` (`INTERFACE.md` §2.4a), store version 2 → 3

Every other `Provenance` field is a fact about **us**; this is the one that is a fact about the thing the entry was derived from. §10b.5 is the finding; what forced it now is that `EdgeProvenance` had the field and `Provenance` did not — two shapes for one concept, which is the drift the drift-check exists to catch, pointing inward. `C8-06`, `C12-07`.

### The two store migrations

| version | migration | shape | discards |
|---|---|---|---|
| **2** | `0002_name_level_attr_schemas.sql` | `DROP TABLE oo_attr_schema`, recreate with `name` in the primary key | every registered attribute schema, and **nothing else** |
| **3** | `0003_proposal_source_version.sql` | `ALTER TABLE oo_proposal ADD COLUMN source_version` | nothing |

**§9.4's licence to drop a v0 store is spent once, deliberately.** It buys a primary-key change on the one table in the store whose contents are reproducible *by definition* — an `AttributeSchema` is deployment configuration written from the deployment's own source. `oo_type.attr_schema_version` and `oo_attr_observed` are untouched, so §5.4's promise that an entry says which generation of `attributes` it belongs to survives the migration. Version 3 is an `ALTER`, because reaching for the drop where an `ALTER` does the job would treat a stated allowance as a default. A reviewer interrupted `0002` between its `DROP` and its `CREATE` on a real v1 store, on both engines: both rolled back with the version row still at 1 and the old rows intact, and migrated cleanly on retry.

---

## 4. What changed, by section

**`INTERFACE.md`** — §2.1 `created_by` gains `derived`, and the vocabulary is enforced for the first time (`C16-05`); **§2.4a new**, `source_version`; §3's Rule K table stops saying `Resolution.complete` is always false; §5.3's `Resolution` gains `searched_namespaces`; **§5.3.1 new**, R6's nine rules plus 8b and 8c; §5.4's warnings vocabulary 16 → **20** and now **held against `types.WARNING_VALUES`**; **§5.9b new**, `reinstate`; §5.12 19 → **21**; §10b.1's contortion 8 marked fixed; the call count 13 → **14** everywhere, found with `grep` and the drift checker rather than by eye.

**`PACKAGE.md`** — **§5.2b new**, name-level schemas: four rules, the tri-state `declared` table, two stated costs and one sentinel; §5.6's third bullet struck through; §9.3's verify-only check derives its columns from the backend's own tuples and says why the *version number* is deliberately not the check; **§9.6 and §9.7 new**, the two store versions; §11.3 gains two recorded weaknesses; §6.2 129 → **150** ids, with both halves of the section — group headers *and* enumerated rows — now held against `test_manifest.py`.

**Elsewhere** — `EDGES.md` §3.1, `docs/README.md`, `README.md` and `registry.py`'s own docstring carried stale counts (`README.md` still said *109 contract tests* and *twelve calls*); all corrected.

---

## 5. The adversarial loop — three rounds, six reviewers, six `NOT YET`

**Every reviewer was briefed with `USE-CASES.md` and told to drive the real registry rather than read it.** The loop closed at the brief's cap of three rounds, not on a clean verdict.

| round | severity | what it found |
|---|---|---|
| **1** | BLOCKING ×3 | `resolve_type(kind=…)` **hid** the cross-namespace collision it exists to report, sealed `complete=True` — UC3's collision shape answered with contortion 8's own sentence, *worse than what R6 replaced*. `TypePage.complete` ignored. **`reinstate` could manufacture mechanism 4** in four ordinary calls. |
| **1** | MAJOR ×4 | A name-level schema was an *exemption* (`mode` shadowed). Census `declared` a confident `False` about a required key. `migrate()` on `owns_schema=False` missed the new columns and died later on a raw driver error. R6's census cost 6,062 round-trips. |
| **2** | BLOCKING ×3 | `Resolution.complete` ignored the **proposal** store — on `sqlite_minimal`, a reference leg *and* UC1's shape, one object said `complete=True` while its adjacent `reason` said entries had been omitted, **and `C3-12` asserted it**. `successor_active` was a one-hop check on a field `reinstate` itself deletes, so **the path back the refusal's own `detail` names ended in the state it forbids**. The collision scan read one page and ignored `TypePage.complete`. |
| **2** | MAJOR ×5 | A word retired in a searched namespace was invisible. Census `declared` a confident `True` in the other direction. Census cost O(keys × types) — 21,043 round-trips at 500 types. `import_types` un-retired names. Five wrong `reinstate` implementations passed the suite, one assertion **vacuous** because its fixture never set up the condition. |
| **3** | BLOCKING ×4 | **Three mutations ran the suite green, two of them round 2's own R6 fixes.** `import_types` wrote `aliases` unguarded — mechanism 4 in **one** call — and erased the merge alias the collision guard depended on. `reinstate` was kind-blind while R19 puts edge families in its path: `AmbiguousKind` out of a `-> TypeEntry \| Refusal` signature, and **false** non-overridable refusals. The five-item `alternatives` cap was a silent truncation under `complete=True`. |
| **3** | MAJOR ×7 | The census read one unpaged query, so an override past page one turned the tri-state back into a confident `True`. R6 was blind to a namespace holding a rejection and no type. `import_types` **retired** a live consumer-gated type with no refusal, warning or event. §5.4's *"eighteen values"* omitted `gate_unregistered` — a value the code emits, `C11-05` tests, and **the table's own last row names**. Three more round-2 claims asserted by nothing. §6.2's headers summed to 142 over tables of 145; `README.md` said 109 tests and twelve calls. |

### 5.1 The convergence note, honestly

**The loop did not converge, and saying it did would be the finding.** Three rounds, six reviewers, six `NOT YET`, ten BLOCKING and sixteen MAJOR. Four things are worth writing down rather than smoothing over.

1. **Four of the ten BLOCKING findings were defects introduced by a previous round's fix, or gaps left inside one.** Round 1's `alias_collision` generalised to aliases and missed successions, which round 2 found. Round 2's rule 8 was applied to `find_types` and not `find_proposals`, which round 2's *other* reviewer found. Round 2's own retired-elsewhere and cross-namespace-rejection fixes were unasserted, and round 3 deleted each and ran the suite green. **A loop that keeps finding things is not obviously failing — but it is also not evidence that a fourth round would be clean**, and the brief's cap exists so that judgment is made by a person and not by the loop.
2. **Every finding of substance came from *running* something.** Across three rows and thirty-odd findings, not one came from reading a diff. Round 3 planted 24 mutations and the suite killed 21; the three survivors are three of that round's findings. Round 2's sharpest defect came from a reviewer *following the path the code's own error message told a caller to take*. That is now three rows' worth of evidence for the same rule.
3. **Rule U broke five more times, in five new places.** `complete=True` over a truncated page, over a proposal store that could not answer, and over a silently capped list; `declared` confidently `True` and confidently `False`; a collision scan reporting absence over rows it never read. The record's line that Rule U is *"the rule this project keeps breaking in its own implementation"* survives another row intact, and the pattern is specific: **every instance is a positive claim built on a look the system had already been told was partial.**
4. **The class of defect narrowed, and one answer stopped being a guard.** Round 1 found *"the mechanism does not exist"*; round 3 found *"the mechanism exists and here is a fourth entrance to it"*. Three rounds closed three different walks into two-live-words-for-one-meaning, each at whichever call the reviewer came in through — so round 3's fix is **`C16-06`, the whole-store invariant** those guards approximate: *no two active entries in one namespace hold one word between them*. That does not depend on guessing the next entrance, and it is the shape the next row should reach for first.

**The specific residual risk, stated:** the row shipped **eight** ids for its six rulings and **thirteen** more to pin claims the specifications already made. A claim in prose that nothing executes is this repository's most reliable defect, and two mechanical gates were added because of it — §5.4's vocabulary and §6.2's group headers now join §5.12 and the printed shapes in being derived rather than asserted. **What is still not checked mechanically is every other sentence**, and round 3 found four false ones. That risk is now *visible* rather than eliminated.

### 5.2 Verified to bite

Each mechanism this row added was checked against an implementation that gets it wrong:

| the wrong implementation | caught by |
|---|---|
| cross-namespace probe narrowed by `kind` | `C3-12` |
| `complete=True` over a truncated type page | `C3-13` |
| `complete=True` over a proposal store that cannot answer | `C3-12`, `C3-13` |
| a retired or rejected word elsewhere dropped from `alternatives` | `C3-12` |
| a name-level schema that merges instead of shadowing | `C15-10` |
| an override that weakens the kind's `mode` | `C15-12` |
| `declared` confidently `True` or `False` where schemas disagree | `C15-12` |
| a `reinstate` that keeps the retirement facts on the live row | `C9-09` |
| a `reinstate` whose successor check is one hop | `C9-13`, `C9-14` |
| a collision scan that stops at page one | `C9-17` |
| a merge visible only in an alias another call overwrites | `C9-16` |
| an import that un-retires, retires a gated type, or writes a colliding alias | `C12-05`, `C12-06`, `C16-06` |
| `source_version` dropped on the ingestion path | `C8-06`, `C12-07` |
| a host schema behind this package's columns | `C0-09` |

**Before this row, every one of them ran the suite to a clean `CONFORMANT`.**

---

## 6. Gates

```
$ python tools/unasync.py --check
22 generated files are current

$ python docs/tools/check_links.py
All relative markdown links resolve.

$ python docs/tools/check_spec_drift.py
docs\specs\INTERFACE.md: every printed shape and signature matches the implementation (15 shapes, 14 calls).
docs\specs\PACKAGE.md: every printed dataclass matches the implementation (13 shapes).
INTERFACE.md 5.12: the closed Refusal.reason vocabulary matches types.REFUSAL_REASONS (21 values), contents and count.
INTERFACE.md 5.4: the closed warnings vocabulary matches types.WARNING_VALUES (20 values).

$ python docs/tools/check_capability_matrix.py
Every optional capability can be declined alone and the backend still conforms.
3.2's claim holds, measured rather than asserted.
```

---

## 7. Questions this row leaves

R-numbers belong to `docs/decisions/`; these are the Q-numbers a ruling would answer.

| # | question | recommendation |
|---|---|---|
| **Q22** | **`Resolution.complete=true` is now nearly unreachable in a real namespace**, because §5.3.1 rule 8c makes the five-item near-miss cap gate the claim and any namespace with more than five active types trips it. Is that the right trade — an honest flag that rarely fires — or should `alternatives` gain a separate `truncated` field so `complete` can speak only about *namespaces searched*? | **Keep it as shipped for v0.** The flag is honest and R6's value is the hits and the named reason, not the flag. Splitting the concept is a shape change and wants Phase 3's paging decision (R13/R25) alongside it, since both are about what a bounded list may claim. |
| **Q23** | **A name-level attribute schema cannot be removed** (§5.2b). An override registered once governs that type for the life of the store; the only retraction hand-copies the per-kind fields, which rule 1 refuses elsewhere. | Add a delete to the optional `AttributeStore` extension at v1. It would be the first destructive operation on deployment configuration in this package, and §9.4's licence to drop a v0 store is the available answer meanwhile. |
| **Q24** | **`attr_schema_version` is meaningful only next to the entry's own name** (§5.2b, §11.3), and a name-level schema registered *after* an entry was written makes the lookup attribute that entry to an override it was not written under. | Record it, as done. The fix is a second `oo_type` column and a fourth store version; not worth it until a deployment has three schema generations in flight. |
| **Q25** | **`attribute_census` is linear in the types of a kind**, two queries per type, because the optional extension has no *list schemas* method and adding one would silently un-implement it for every existing third-party backend (`isinstance` against a `runtime_checkable` Protocol matches on method names). | Accept for v0 and keep the stated warning not to put it in a request path. A v1 that revs the extension's version can add the method properly. |
| **Q26** | **Only two of this specification's vocabularies are checked mechanically**, and round 3 found four false *sentences* that no gate can see. Should a row's spec claims be executable — a doctest-shaped harness over the numbered rules — rather than prose a reviewer has to drive? | **Worth a real decision before the next spec row.** Thirteen of this row's twenty-one new ids exist to pin claims the documents already made, which is the measurement that makes the question concrete. |
