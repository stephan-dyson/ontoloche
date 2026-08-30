# 4C-RUN — roadmap row 4c: edge semantics, and the kill row's fourth trip found by a machine

**Row:** 4c. **Date:** 2026-08-29. **Repo:** [`open-ontology`](https://github.com/stephan-dyson/open-ontology), `main`.
**What it carried:** rulings **R33**, **R34**, **R37**, **R38**, **R39** ([`2026-08-29-4b-rulings-R32-R39.md`](../decisions/2026-08-29-4b-rulings-R32-R39.md)) and **R40** ([`2026-08-29-6-rulings-R40-R47.md`](../decisions/2026-08-29-6-rulings-R40-R47.md)), plus [`check_merge_guard.py`](https://github.com/stephan-dyson/open-ontology/blob/main/docs/tools/check_merge_guard.py) — the artefact row #6's third round ruled was owed *instead of* a fourth patch to the merge guard.
**Why it ran next:** **R38 changes what an edge endpoint MEANS**, and beacon builds Tenshen slice 1 against the edge store immediately after this lands. A merge that silently orphans every edge written against the merged-away name is not a thing to discover from a consumer.

---

## 1. The headline, in numbers

| | before (row #6) | after |
|---|---|---|
| contract ids ([`PACKAGE.md`](https://github.com/stephan-dyson/open-ontology/blob/main/docs/specs/PACKAGE.md) §6.2) | 196 | **222** |
| sync suite, one run, three legs | `484 passed, 122 skipped` (606 collected) | **`541 passed, 144 skipped`** |
| async suite, one run, three legs | `520 passed, 122 skipped` (642 collected) | **`576 passed, 144 skipped`** |
| `warnings` values ([`INTERFACE.md`](https://github.com/stephan-dyson/open-ontology/blob/main/docs/specs/INTERFACE.md) §5.4) | 25 | **29** |
| `Refusal.reason` values (§5.12) | 28 | **28** — and that is a result, not an omission. §3 |
| mechanical gates in the suite | 4 | **5** — [`check_merge_guard.py`](https://github.com/stephan-dyson/open-ontology/blob/main/docs/tools/check_merge_guard.py) |
| `EDGES.md` sections under R31's rule gate | 3 (§2.4.1, §4.3, §4.4) | **5** (+ §2.5, §5.2) |
| `EDGES.md` printed call signatures held against the code | **0** | **4** |
| `ROADMAP.md` kill-row trips | 3, all found by human reviewers | **5** — the fourth by this row's checker, the **fifth by this row's adversarial loop, while that checker exited 0**. §6.4 |

**The floor held.** Row #6's floor was 196 ids and a sync suite that must never go below it; every commit in this row ran both suites on all three legs before it landed, and the count moved 196 → 203 → 206 → 209 → 210 → 211 → 214 → 220 → 222.

---

## 1b. The loop's first round, and the number that matters

**Two fresh reviewers, distinct lenses, both required to construct and RUN probes. Between them: 8 BLOCKING, 7 MAJOR, 7 MINOR — every code finding reproduced here before it was believed, and every one reproduced.**

That is a lot for work that had five mechanical gates green, and the shape of it is worth stating before the detail: **three of the eight BLOCKING were in code this row had just written or just changed**, one was in the checker this row built to prevent exactly this class, and one was the kill row itself.

| | found by | closed by |
|---|---|---|
| **the kill row's FIFTH trip** — a *partial* extent compares equal | the loop | `C10-11` |
| `predicate_requires_review` on every approved predicate, destroying its own signal | the loop | `C10-12` |
| `amend_edge` erasing an invalid payload's enumeration | the loop | `C17-50` |
| an unregistered family's edge returned without an incidence check | the loop | `C17-49` |
| `via_successor` on a written reference; `nodes` not deduped; the marker fired only for the origin | the loop | `C17-48` |
| `AmbiguousKind` escaping the new import guard | the loop | `C12-10` |
| `check_merge_guard.py`'s only overridability assertion being a `NameError` | the loop | fixed, plus five more watched mutations |
| five checker rows printing `REFUSED` for a probe that never ran | the loop | `NOT REACHABLE`, named |

§6.4 is the honest reading of the first row.

### The loop's second round — **4 BLOCKING, 5 MAJOR, 3 MINOR**

One lens was the brief's mandated *"who integrates next week"*: an engineer building beacon's Tenshen slice 1 against this seam, who reported plainly that **they would not ship against it**. The other was pointed at round 1's own fixes, on this project's documented pattern that a fix is the likeliest place for the next defect. Both were right.

| | what it was |
|---|---|
| **R38 was never applied to family NAMES** | `EDGES.md` §2.3's architectural bet is that a family **is** a `TypeEntry`, so it inherits `merge_types` for free. What that inheritance did was **orphan every edge written under an absorbed family name** — `known=2, complete=True, warnings=()`, a real stakeholder missing from the flagship two-hop query, after a steward did the ordinary governance act and a consumer asked for the *surviving* name. **Verbatim the sentence R38 exists to close, one axis over, inside the row that closed it.** Every R38 test merged `entity` types. `C17-51` |
| **an integer `InstanceRef.id`** | §2.1 records the `str`/`int` cast as contortion **E4**, *"where a silent key mismatch lives"* — and it was living there. `str(ref)` identical for `41` and `"41"`, the refs comparing **unequal**, `add_edge` accepting it, and `neighbors` returning `known=0, complete=True, warnings=()` on SQLite while raising a raw psycopg error on Postgres. **One input, two reference backends, two different wrong answers.** `C17-52` |
| **round 1's fix reintroduced round 1's defect class** | the alias identity guard — written as the *fifth trip's fix* — read one page of `find_types(name_in=…)` and checked `if not others and not page.complete`, which fires when the page is **empty** and never when it is **short**. A partial read compared as if it were whole, two functions and one hour away from the fix for exactly that |
| **the checker saw 4 of 9 write shapes** | Part A exited 0 with a collapsing caller live. Enumerating syntactic shapes is *the same artefact as the guard it checks* — something a person must remember to extend — so the rule is now any mention of an identity field's **name**, anywhere in a function. All nine caught; the three readers it now flags are documented in `KNOWN_CALLERS`, which is the over-broad rule's intended cost |

Four more closed with them: `via_successor` still naming an edge's own `src` when **both** merged names were in the frontier (round 1 fixed the read site and left the write site); `amend_edge` neither recomputing nor clearing `edge_family_retired`, so an amendment after `reinstate` asserted a live family was retired; `endpoint_type_merged` firing once per **name** rather than once per identity and never naming the survivor; and a retired origin type having no carrier at all — **mechanism 3**, a steward's explicit *"stop using this word"*, invisible in the call consumers run.

> **The pattern across both rounds, stated because it is the row's most useful output.** Round 1 found a defect in the guard the row had just written. Round 2 found a defect in round 1's fix, *and* found the row's flagship ruling applied to one axis and not another. **Neither round found a defect in anything this row did not touch.** The work is not fragile everywhere; it is fragile exactly where it is new, which is what constraint 7's loop is for and what no gate in this repository measures.


---

## 2. What each ruling cost, one line each

| ruling | what landed | ids |
|---|---|---|
| **R34** `payload_schema` | `PACKAGE.md` §5's modes, versions, enforcement floor and census floor, transposed to `add_edge`. **Its key had to change** — §2.5's own key collided with the schema governing the family's declaration | `C17-35`…`C17-40`, `C15-13` |
| **R37** `edge_amended` | `amend_edge`, taken after the design test R37 made a condition of taking it | `C17-41`…`C17-43` |
| **R38** `neighbors` follows the chain | an edge endpoint reference resolves to the identity it now belongs to; `via_successor` is Rule K | `C17-33` (rewritten), `C17-44`…`C17-46` |
| **R39** second retraction | refused `already_decided`, not made idempotent | `C17-47` |
| **R33** `endpoint_kinds` | §2.4's motivating sentence narrowed; the mechanism untouched | — (doc; rule `2.4.1-7` stays `prose-only`) |
| **R40** predicate proposals | never auto-approve, whatever the policy says | `C10-10` |
| **item 6** the checker | `check_merge_guard.py`, and what it found | `C12-08`, `C12-09`, `C9-19` |

---

## 3. Two vocabulary results worth stating, because both are absences

**`Refusal.reason` did not grow, and four separate opportunities to grow it were declined.** R3's rule makes adding a value cheap and *correct*; it does not make it free, and a closed vocabulary that grows a value per variant of one failure is not closed for long ([`EDGES.md`](https://github.com/stephan-dyson/open-ontology/blob/main/docs/specs/EDGES.md) §2.4.1's own words). Four times this row asked *"does none of the twenty-eight say this?"* and four times the answer was no:

1. an edge payload failing an `enforce` schema is **`attributes_schema_violation`** — the same mechanism, one kind along;
2. an amendment that cannot be recorded is **`cannot_record_override`** — §3.6's rule has a fourth caller, not an exemption;
3. a second retraction is **`already_decided`** — §5.5's word about a proposal, on a second object, with the same meaning;
4. an imported alias that would collapse two identities is **`predicate_merge`** / **`kind_mismatch`** — §5.10's own two guards, reached through a third door.

**`warnings` grew by two, and both are Rule U.** `payload_schema_unregistered:<name>` says *the payload was not validated and here is the name nobody registered*; `predicate_requires_review` says *this kind always needs a human* — and, on a backend that has nowhere to hold a proposal, *a predicate went live without the review R40 requires*. Both were added to §5.4 in the change that introduced them.

**And one value kept its name while its MEANING changed**, which R3 does not cover and which this row treats as covered anyway. `endpoint_type_merged:<ref>` used to mean *"edges under the other name were **not** searched"*, with `complete=False`; after R38 the walk searches them and the value means *"this reference's identity spans more than one written name"*. Both §5.4 and `EDGES.md` §2.8 were amended in the same commit as the behaviour, because **a closed vocabulary whose values quietly change meaning is not closed either.**

---

## 4. Deviations — every place the implementation could not follow the document as written

| # | Deviation | Why, and what was done |
|---|---|---|
| **D-4c-1** | **`EDGES.md` §2.5's key for a payload schema was unimplementable.** It said `payload_schema` names an `AttributeSchema` keyed `(namespace, "edge", <family name>)` — which is the **identical key ruling R10 gives the name-level schema governing that family's own `TypeEntry.attributes`** (its `level`, `symmetric`, `inverse_label`, `endpoint_kinds`, `payload_schema`). One key, two dicts | **Reproduced before it was designed around.** **[Observed]** a payload schema `{"role": str}` with `additional="forbid"` registered under `(default, "edge", "blocks")` made `propose_type(kind="edge", name="blocks", …)` refuse `attributes_schema_violation` with all five declaration keys *"not declared in the schema"* — **governing a family's payload made the family unregisterable.** `INTERFACE.md` §2.3's Cause B. The kind is `edge_payload`: two spaces, no new table, no new primitive, no reachable collision. §2.5 rewritten; `C17-38` is the regression pin |
| **D-4c-2** | **The census had to discover edge payload schemas through the FAMILIES.** Every other kind's name-level schemas are keyed by a *type* name, so `attribute_census` finds them by enumerating the types of that kind — and there is no `kind="edge_payload"` type to enumerate | Without the branch, the census answers a confident `declared=False` about a key a payload schema declares **`required`** — the exact wrong answer ruling R10's own census fix was made to stop, one kind along, in the row that introduced the kind. `C17-40` (nonbinding, R2) |
| **D-4c-3** | **An edge payload is validated against what the CALLER wrote, not against what survives storage.** On `stores_edge_attributes=False` a payload can validate on the way in and come back absent | The type side's order (`_write_approved` validates `rec.attributes`) and the honest one: a `required` field a backend cannot store is that backend's **declared loss** (§6, `PACKAGE.md` §5.7), not the writer's schema violation. §6's table already fixes how that is reported and forbids a second warning for it, so nothing new is minted. Rule `2.5-6`, tagged `prose-only` with this reason |
| **D-4c-4** | **`amend_edge` is refused where `retract_edge` is not.** §2.6 argues retraction past `PACKAGE.md` §3.6 on *"the record **is** the row"* | **That argument does not transpose**, and saying so is the deviation: `status`, `retracted_by`, `retracted_at` and the reason are columns; **there is no column for a prior confidence.** So an amendment on `stores_edge_events=False` erases the old value with no record anywhere, which is §3.6 verbatim and `reinstate`'s shape exactly. `C17-43` asserts both halves on one store |
| **D-4c-5** | **`retire`'s guards were in the wrong ORDER**, so a non-overridable refusal was reached through an overridable one | Found by `check_merge_guard.py`. On `indexes_membership=False` a predicate retirement-with-successor was refused `no_consumer_evidence` — which advertises `force=True` — when the true answer was `predicate_merge`, which never moves. Row 3c fixed the identical defect in `merge_types` and the lesson had not been carried across. Reordered; `C9-19` |
| **D-4c-6** | **R40 cannot be honoured on `stores_proposals=False`.** There is no table to hold a predicate for review | The alternatives were to write it with a warning or to refuse `kind="predicate"` on such a backend entirely — and refusing means a conformant one (`PACKAGE.md` §7.4 calls that shape conformant *"as a third backend"*, and it is beacon's own) cannot hold a capability predicate at all. **That is a product decision about what this registry declines to serve, so it is raised (Q50) rather than taken**, and the fact is made enumerable meanwhile: the entry carries `predicate_requires_review`. `C10-10` asserts both branches rather than skipping the degraded one |
| **D-4c-7** | **`tools/unasync.py` emitted a silent mistranslation**, in the tool whose first stated property is that it *"refuses to emit code it cannot prove is right"* | A helper nested inside `neighbors` became `async def` with **every call left un-awaited** — its name is neither a method attribute nor a module-level name, so neither branch of the fixpoint registered it. 66 async tests failed with `TypeError: cannot unpack non-iterable coroutine object`; **a nested helper whose result nothing unpacks would have been a coroutine quietly discarded.** It now **refuses** that shape rather than translating it, because awaiting a nested name correctly needs shadowing and closure scope. The fix at the call site is one line: hoist it to a method |
| **D-4c-8** | **`attribute_census()` raised on the Postgres leg for any string-valued attribute**, and had for three rows | `JSONDecodeError: Expecting value`. Every `*_json` column there is `jsonb`, so psycopg decodes before the dialect sees it, and the dialect re-parsed anything arriving as a `str` — which is exactly a jsonb column holding a JSON string. **Nothing caught it**: no test wrote a string attribute and then censused it; the census is **nonbinding** under R2, so it sits outside the conformance verdict; and both sqlite legs parse text correctly, so the two-leg agreement everything else relies on had one leg that never disagreed. Found by wiring R34's census onto the same call. `C15-13` |
| **D-4c-9** | **`EDGES.md` never printed `add_edge`'s signature**, and nothing noticed for two rows | Found by this row's own extension of `check_spec_drift.py` to EDGES' calls — the same class as deviation **D-4b-2** one layer up. The primary write call of the whole document had a data shape, a behaviour section and no signature, so a reader implementing from the document inferred the argument list from prose. Printed in §2.2, and now held against `Registry` |
| **D-4c-10** | **`DegradedAdapter` accepted a non-bool flag value and silently kept the capability ON** | `DegradedAdapter(a, stores_edge_events="this host owns the table")` — putting the *reason* where the flag goes, because `why=` is the second thing you reach for. A non-empty string is truthy, so `C17-43` ran against a fully capable backend and passed for the wrong reason. A test **double** that ignores a mistyped argument is the *"checker nobody has watched fail"* class, one layer down. It refuses now |
| **D-4c-11** | **`_merged_with` was deleted rather than left in place.** Row 4b's helper answered *"which other names hold edges this walk did not search"* | R38 makes the walk search them, so the helper's docstring described behaviour that no longer holds — and 81 lines of reasoned prose about a decision that has been reversed is worse than none. The identity closure replaces it, and it costs **one paged read of the retired rows per `(namespace, kind)`, memoised for the whole call**, where `_merged_with` did that scan **per node it was asked about**: one per frontier member at depth 2, on the 9.7M-degree node §4.2 measures |

---

## 5. Ruling R31 — the rule→id mapping

Row 4b brought `EDGES.md` §2.4.1, §4.3 and §4.4 under the gate. Row 4c brings **§2.5** and **§5.2**, because both stopped being prose in this row, and extends §4.3 by one rule.

### 5.1 `EDGES.md` §2.5 — the payload schema *(new)*

| rule | exercised by |
|---|---|
| **2.5-1** the key is `(namespace, "edge_payload", <declared name>)`, not `(namespace, "edge", <family>)` | `C17-38` |
| **2.5-2** a per-namespace schema governs every payload; a family's name shadows it, fields replaced, strictness a floor | `C17-39` |
| **2.5-3** `enforce` refuses naming which schema and which family; `warn` writes and enumerates; `off` is the default | `C17-35`, `C17-36` |
| **2.5-4** `attr_schema_version` records the version in force; an older edge is never re-validated | `C17-36` |
| **2.5-5** a family naming a schema nobody registered is **written**, with `payload_schema_unregistered:<name>` | `C17-37` |
| **2.5-6** validated as the caller wrote it, before the backend's projection rules drop what it cannot store | **`prose-only`** — D-4c-3 |
| **2.5-7** every payload key is censused under `kind="edge_payload"`, and `declared` stays tri-state | `C17-40` |

### 5.2 `EDGES.md` §5.2 — the amend path *(new)*

| rule | exercised by |
|---|---|
| **5.2-1** a correction is a new `edge_amended` event carrying old and new; the first event is not edited | `C17-41` |
| **5.2-2** `family`, `src`, `dst`, `status` are not amendable — the guarantee is the signature | `C17-42` |
| **5.2-3** an amended payload is validated on `add_edge`'s exact terms; a refused amendment appends no event | `C17-42` |
| **5.2-4** amending a retracted edge is refused `already_decided` | `C17-42` |
| **5.2-5** an unrecordable amendment is refused while a retraction on the same store is not | `C17-43` |
| **5.2-6** an empty `reason`, or an amendment naming no field, raises `ValueError` | `C17-42` |
| **5.2-7** `EventRecord.edge_id` is the one shape amendment; the adapter never judges the transition | `C17-26` |

### 5.3 `EDGES.md` §4.3 — two rows changed

**`4.3-14` was rewritten** from *"the walk does not follow the chain and says so"* to *"the walk follows it, and every edge reached that way is marked"*. `C17-33` holds the new rule as it held the old, plus `C17-44` and `C17-46`. **`4.3-15` is new** — the chain that cannot be followed to an end (a cycle, the length cap, a backend that cannot page its retired rows) — `C17-45`.

### 5.4 The gate was watched failing, seven ways

Two gates were extended and both were mutated before they were trusted, because *a checker nobody has watched fail is a checker nobody knows works* (row 3e's lesson, row 4b's §4.4).

**`check_spec_drift.py`, EDGES call signatures — three mutations, each restored:**

```
  CAUGHT  a parameter the code takes and the spec does not
          - EDGES add_edge(): the implementation takes 'model_tier' and the spec's
            signature does not -- a reader implementing from the spec cannot reach it
  CAUGHT  a parameter the spec declares and the code does not take
          - EDGES add_edge(): the spec declares 'provenance_note'; the code does not take it
  CAUGHT  a printed call Registry does not have
          - EDGES delete_edge(): the spec declares it; Registry has no such method
```

**`check_merge_guard.py` — four mutations, each restored:**

```
  CAUGHT  import_types' identity guard removed  (4 states, naming the alias door)
          - sqlite / import_types / known-different: import_types wrote `commentable` as
            an alias of `searchable` with no refusal -- resolve_type('commentable') now
            answers `searchable` at confidence 1.0 ... the kill row, through the alias door
  CAUGHT  a NEW unguarded caller writing a successor
          - CALLER: `fold_into` writes ['successor'] onto a stored record and this checker
            has never heard of it ... decide whether it can collapse two identities
  CAUGHT  the guard BANS rather than narrows
          - sqlite / merge_types / known-equal: merge_types REFUSED 'predicate_merge' a
            pair whose extents are non-empty and identical. The guard is narrowed, not
            banned -- refusing everything passes a checker that only tests refusals
  CAUGHT  retire's predicate identity guard removed
          - sqlite / retire / known-different: retire(successor=) COLLAPSED the pair with
            force=False -- resolve_type now answers the old word with the new entry at
            confidence 1.0, which is the merge merge_types refuses
```

---

## 6. `check_merge_guard.py` — the caller list, and what it found

Row #6's third round ruled: *"the fix owed is a checker, not a fourth patch"*, and the checker must enumerate the **callers** as well as the four extent states. It does both, and **Part A found an unguarded caller on its first run.**

### 6.1 The caller list, recorded as the brief asks

Discovered from `registry.py`'s **AST** rather than from a list somebody has to remember — because a list you have to remember to update *is* the defect rather than a fix for it. Every function that writes a `successor` or an `aliases` onto a stored record: those are the two fields that change what a name **resolves** to.

| caller | writes | verdict | why |
|---|---|---|---|
| **`merge_types`** | `successor`, `aliases` | **collapses** | the canonical case, and the call §5.10's guards were written for |
| **`retire`** | `successor` | **collapses** | `retire(successor=)` redirects `resolve_type` at confidence 1.0, which §5.3 calls a guarantee — the kill row's third trip |
| **`import_types`** | `aliases` | **collapses** | writes a foreign dump's aliases onto a live entry. **The kill row's FOURTH trip, found here** |
| `reinstate` | `successor` | no collapse | a **split**: it clears a successor off a live row, so a word that resolved to another identity goes back to resolving to its own. §5.10's guards would have nothing to compare, and the state it creates is guarded on its own terms (`successor_active`, `alias_collision`) |
| `_write_approved` | `aliases` | no collapse | writes `aliases=()` — the literal empty tuple, on every approval. **A `ProposalRecord` has no `successor` and no `aliases` field, so `approve` cannot re-point a name however the proposal is amended.** *(The brief named "approve of a proposal with a successor" as a caller to enumerate. There is no such thing; this row is the record that somebody looked.)* |
| `_entry` | `aliases` | no collapse | the READ path — it copies aliases off a stored record into the returned `TypeEntry`. It writes nothing |

**A caller this file has never heard of fails the check**, guarded or not, because whether a caller can collapse two identities is a person's judgement rather than a grep. It fails on a **stale** entry too — a guard somebody thinks is being checked and is not.

### 6.2 The states, on all three legs

Every extent state × every collapsing caller × every leg: **known-different** REFUSED, **known-equal** *allowed*, **empty** REFUSED, **unknowable** REFUSED, **kind-mismatch** REFUSED — the last twice, once with a predicate on one side (where both guard #2 and guard #3 bind) and once with none, **because one row can mask the other**. Every refusal is additionally checked non-overridable under every acknowledgement the call accepts and under `force=True` where the call has one.

**The `known-equal` row is the one a careless fix breaks.** The guard is *narrowed*, not *banned* — `C10-09`'s whole content — so a registry that refused every predicate collapse would pass a checker that only tested refusals, having deleted a legal operation to make a test go green.

### 6.3 The fourth trip

**[Observed], reproduced end to end against the shipped `Registry`:**

1. `commentable` and `searchable` — two live predicates, extents `{note}` and `{doc}`: non-empty and genuinely different;
2. `merge_types` refuses that pair **non-overridably**, under every acknowledgement;
3. `commentable` is retired — an ordinary, permitted governance act, **no successor**;
4. `import_types` writes `aliases: ["commentable"]` onto `searchable` with **no refusal, no warning and no acknowledgement**;
5. `resolve_type("commentable")` goes from `proposal / None / 0.4762` to **`existing / searchable / 1.0`** — a confidence §5.3 calls a registry **guarantee** — while the two extents stay different.

**Why `alias_collision` did not see it.** That guard refuses an alias that is a **live** entry's name, because §5.9b minted it to stop *two active entries holding one word between them*. A retired name is not a live entry — but **a retired predicate name still resolves, and a retired predicate still has an extent.** The guard was written for a *collision*; the failure is a *collapse*. Same write, different question.

**The diagnosis, in its full form after four trips:** *a guard written for **one call**, over a fact that **more than one call** can change, reached through **more than one field**.* Recorded in the [`ROADMAP.md`](https://github.com/stephan-dyson/open-ontology/blob/main/ROADMAP.md) kill row and in [`2026-08-29-3c-rulings-R6-R12.md`](../decisions/2026-08-29-3c-rulings-R6-R12.md).

**What is different about this one, and it is the whole argument for the checker:** the three before it were found by human adversarial reviewers, one round at a time, each after the previous fix had shipped. This one was found before any reviewer read the row, by a gate that now runs **inside the contract suite on every commit** — so the *next* caller cannot arrive unnoticed.

### 6.4 The FIFTH trip, and the honest qualification of §6.3's argument

§6.3 argues that the checker is the answer, because it found the fourth trip mechanically. **The fifth trip qualifies that, and the qualification is the most useful thing in this document.**

**What happened [Observed, round 1].** `_extent` read **one page** of a predicate's members and returned it. Every guard that compares two extents — `merge_types`' refusal #2, `retire(successor=)`'s (added by the third trip) and `_alias_identity_breach`'s (added by the fourth) — took `set(self._extent(...)[0])` and **threw away the third element, which is the `why` saying the read was partial**. Two predicates whose *first page* of members matched compared equal, and all three callers performed the collapse. Reproduced on this repository's own honest-paging double, added by row 3e because *"`PACKAGE.md` §3.3 permits it and UC3's scale produces it"*: true extents of three members and two, `merge_types` returning a `MergeResult`, `resolve_type("commentable")` answering `searchable` at confidence 1.0.

**It is Rule U's third operand on one expression.** Row 3c closed *unknowable is not equal*. Row #6's second round closed *empty is not equal*. Nobody had closed **partial is not equal** — and the read path had been publishing exactly that fact, as `PredicateEntry.why_extent_incomplete`, since row 3c. Fixed on two axes, because there are two backends and one fix does not cover the other: an honest **page** (a cursor to the rest) is answered by `_extent` looping to exhaustion; a **truncated** answer (capped, no cursor) has no rest to read and is answered by folding the `why` into `knowable`. `C10-11` pins both, on all three callers, plus the narrowing case.

> **`check_merge_guard.py` exited 0 the whole time, and that is the finding about the finding.** Its three real legs — sqlite, `sqlite_minimal`, Postgres — all answer a predicate-extent query in one page, so *no fixture it had could pose the question*. It now carries a `partial` and a `truncated` state for every collapsing caller, and `unknowable` for all three rather than for `merge_types` alone. But the general lesson is not "add more states": it is that **a checker only asks the questions its fixtures can pose, and this one's fixtures were built by the same person, in the same hour, with the same blind spot as the guard.** The loop is what asked a question the checker's author had not thought to ask.
>
> **So the fourth trip is not evidence that reviewers are now optional.** Both are load-bearing and neither replaces the other: the checker runs on every commit and catches the *next caller*; the loop runs once a row and catches the *next question*. Anyone reading §6.3 as an argument for dropping constraint 7's loop should read this box instead.

**Three more defects in the checker itself, all found by the loop:** its only overridability assertion was a `NameError` (`reason` where the local is `reasons`), so the one thing its docstring promises could never have fired; five rows printed **REFUSED** for a probe whose fixture could not be built on that leg — ruling **R12**'s own rule, *a verdict without its coverage line is not a verdict*, broken inside the checker built to enforce it; and Part A's AST scan saw one of four realistic write shapes, so a caller written with `d["successor"] = x` rather than a dict literal was invisible. All three fixed, with five further mutations watched failing.

---

## 7. What the build taught

**1. A ruling can name a key that cannot exist, and only writing the code finds it.** R34 said *take `payload_schema` in 4c*, and §2.5 had specified its key a whole row earlier, in a document that had been through three adversarial rounds. The key was the one R10 had already given to something else. **Nobody reading either document would have caught it**, because each is locally correct; the collision only exists when both mechanisms are running. Twenty minutes of probe found it; the fix is a different `kind` string.

**2. The most valuable thing this row built was not a feature.** R38 is the founder-visible ruling and it is real work — but `check_merge_guard.py` found a live kill-row defect on its first run, in a caller nobody had thought to look at, and it will keep looking. Three defect classes in this repository were closed by a mechanical checker; the class the kill row runs through now has one too, and its first act was to justify itself.

**3. "Enumerate the callers" is only useful if the enumeration is mechanical.** The first draft of the checker had a hard-coded caller list. That is *the same artefact as the guard it is checking* — something a person has to remember to update — and it would have passed happily while a fifth caller sat unguarded. Reading the AST for writes of `successor` and `aliases` costs thirty lines and turns "remember to think about this" into "the suite fails until you do".

**4. A guard can be right and still lie.** `retire`'s ordering defect never let a collapse through: the outcome was correct at every step. What was wrong was the *reason* — a caller was told to `force=True` past something that never moves. Row 3c had already fixed exactly this in `merge_types` and written down why, and the lesson did not travel. **The checker travelled it**, because it asks every caller the same question.

**5. Two suites is not redundancy.** `tools/unasync.py` silently emitted un-awaited calls to a nested coroutine. The sync suite was green. The async suite failed 66 tests. A generator that promises to refuse what it cannot prove had a branch that proved nothing and emitted anyway — and the fix is to refuse, not to be cleverer.

**6. A nonbinding test is a test nothing was ever measured against.** `attribute_census` crashed on the reference *deployment* backend for the most ordinary attribute value there is — a string — and had for three rows. It sits outside the conformance verdict by ruling R2, so no leg-to-leg disagreement was ever asserted about it; both sqlite legs happen to be correct, so the two-leg agreement everything else leans on had one leg that never disagreed. **Nonbinding should mean "a backend may not be failed for it", not "nobody checks it."**

**7. The cheapest honest answer to a product question is to raise it.** R40 cannot be honoured on a backend with no proposal table, and the choice — write it with a warning, or refuse predicates on that backend entirely — decides what this registry declines to *serve*. That is not an implementation call. It is Q50, the entry carries the warning meanwhile, and `C10-10` asserts both branches so neither can rot.

---

## 8. Questions for the supervisor — **Q49 onward**

**Q49 — Should `endpoint_type_merged` keep its name now that its meaning has changed?** R38 turned it from *"edges under the other name were not searched"* into *"this reference's identity spans more than one written name, and they were"*. Both §5.4 and §2.8 were amended in the same commit, so R3's rule is satisfied in substance — but a caller who stored the string against the old meaning has no signal that it moved. *Recommendation: keep it.* The value names a **fact about the vocabulary** rather than a fact about the walk, and that fact is unchanged; renaming would break a closed vocabulary's stability for a change in what the registry does with the fact. Recorded because "a value quietly changed meaning" is a shape this project has punished elsewhere.

**Q50 — May a backend with `stores_proposals=False` hold a `kind="predicate"` entry at all?** *(Founder-visible; it decides what the registry declines to serve.)* R40 says a predicate proposal never auto-approves, and such a backend has nowhere to hold one. Row 4c writes the entry with `predicate_requires_review`, which makes *"a predicate went live without review"* enumerable. The alternative is `Refusal(reason="proposals_not_stored")` — which means beacon's own shape (`PACKAGE.md` §7.4, *"conformant as a third backend"*) cannot carry a capability predicate. *Recommendation: keep the warning for v0 and revisit with beacon 2B's evidence*, because the kill row's danger is a predicate going live **and then being merged**, and `C10-09`/`C9-18`/`C12-08` all guard the merge on every backend regardless of this answer.

**Q51 — Is `_IDENTITY_CHAIN_CAP = 16` the right number, and should it be a `NamespacePolicy` field?** R38's chain-following stops at 16 hops and reports `complete=False`. Sixteen is a guess: no fixture has a chain longer than 2, and the cap exists so a **broken** vocabulary (or a cycle, which §5.9 does not forbid constructing) cannot make the one read call hang. *Recommendation: leave it a constant for v0.* A deployment-tunable bound on a pathological case is configuration nobody will set correctly, and R36 already ruled the assembly bound per-registry rather than per-namespace.

**Q52 — Should the identity closure apply to `resolve_type`'s `alternatives` too?** R38 ruled the endpoint-reference question *for both documents* and `INTERFACE.md` §2.1 now carries it. `resolve_type` follows the chain for an **exact** hit and scores `alternatives` against the active page, so a near-miss on a merged-away word is scored against a word that no longer denotes on its own. *Recommendation: no for v0, record it.* It is a scoring question rather than an identity question, and R6's `search_namespaces` is the surface that would have to answer it.

**Q53 — Does `edge_payload` want to be in `INTERFACE.md` §2.2's kind vocabulary?** It is an `AttributeSchema.kind`, not a `TypeEntry.kind`, and §2.2's vocabulary is explicitly **open** — but `attribute_census(kind="edge_payload")` now returns rows under a string that appears in no enumeration anywhere. *Recommendation: no, and say so in `PACKAGE.md` §5.2.* An `AttributeSchema.kind` is a schema namespace and a `TypeEntry.kind` is a word in the vocabulary; conflating them is `INTERFACE.md` §2.3's Cause B, which is the exact defect D-4c-1 was.

**Q54 — Should `check_merge_guard.py`'s `IDENTITY_FIELDS` be derived rather than declared?** Part A scans for writes of `successor` and `aliases` — a two-element tuple a person maintains, which is the shape the checker exists to replace, one level up. A third identity field added without touching that tuple would be invisible. *Recommendation: accept for v0 and record the residual.* Deriving it means knowing which `TypeRecord` fields `resolve_type` reads, which is a dataflow question a checker of this size should not answer; the honest mitigation is that this is stated in the file rather than implied.

**Q55 — `import_types` is now the fourth call with identity guards. Is the guard set worth extracting?** `merge_types`, `retire` and `import_types` each carry their own copy of §5.10's #2 and #3, in three shapes (a `Refusal`, a `Refusal`, an `import_refused:` warning). Three copies of one rule is how the first three trips happened. *Recommendation: yes, but not here.* Extraction is a refactor with no new behaviour, and this row's evidence is that the checker — not the shared function — is what catches the next caller. Recorded for the ACTIONS build row, which adds a fifth surface.

---

## 9. What this row did NOT do

- **It did not extract the identity guards** into one function (Q55). Three callers carry three copies.
- **It did not page anything.** R13's ruling stands; `neighbors` still returns an unpaged bounded report and the identity closure adds no cursor.
- **It did not touch `resolve_type`'s scoring** (Q52), the ledger, or anything in `ACTIONS.md`.
- **It did not run the design tests against new fixtures.** UC1/UC2/UC3 are exercised by `C18` unchanged; the probes this row wrote were built to find defects and were deleted, and every finding they produced is now a contract id.
- **It did not change what `merge_types` does.** Every fix in this row is a guard on a *different* caller reaching the same outcome, which is the whole content of the third trip's diagnosis.
