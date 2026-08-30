# 4D-RUN — roadmap row 4d: identity staleness, and the gate that could finally pose the question

**Row:** 4d. **Date:** 2026-08-30. **Repo:** [`open-ontology`](https://github.com/stephan-dyson/open-ontology), `main`.
**What it carries:** the **Q56 default** (`resolve_type` re-verifies a predicate identity claim at the read and warns when it has gone stale — confidence stays 1.0, because the expensive half is the founder's), ruling **R54** (`_extent` and `predicates()` resolve the IDENTITY, not the written word) and ruling **R55** (the write-door warning), from [`2026-08-30-4c-rulings-R48-R57.md`](../decisions/2026-08-30-4c-rulings-R48-R57.md).
**Why it ran next:** row 4c's loop tripped [`ROADMAP.md`](https://github.com/stephan-dyson/open-ontology/blob/main/ROADMAP.md)'s kill row a fourth, fifth and **sixth** time, and the sixth is *different in kind*. Trips 1–5 were all *the guard did not look properly*. The sixth is **the guard looked correctly, and then the fact changed** — every identity guard compares predicate extents at **write** time, `resolve_type` grants confidence 1.0 at **read** time, and the vocabulary moves in between. Row 4c closed the four doors it found; it did not close the gap. **Rule U's fourth operand: STALE is not equal.**

---

## 1. The headline, in numbers

| | before (row 4c) | after |
|---|---|---|
| contract ids ([`PACKAGE.md`](https://github.com/stephan-dyson/open-ontology/blob/main/docs/specs/PACKAGE.md) §6.2) | 226 | **249** |
| sync suite, one run, three legs | `549 passed, 148 skipped` | **`596 passed, 170 skipped`** |
| async suite, one run, three legs | `584 passed, 148 skipped` | **`631 passed, 170 skipped`** |
| `warnings` values ([`INTERFACE.md`](https://github.com/stephan-dyson/open-ontology/blob/main/docs/specs/INTERFACE.md) §5.4) | 29 | **32** — `identity_stale`, `declared_predicate_merged`, `alias_check_incomplete` |
| `Refusal.reason` values (§5.12) | 28 | **30** — `successor_unregistered`, `successor_is_self`. *Q56's cheap half still only REPORTS; both new refusals are about a guard that could not be **evaluated**, which is a different question from the one the founder holds* |
| mechanical gates in the suite | 5 | **5** — and one of them gained **five** new axes |
| `check_merge_guard.py` axes | 1 (extent states) | **6** — + staleness, spelling, one-word-one-identity, forward-declared successor, and the NAME door |
| spec sections under R31's rule gate | 5, all in `EDGES.md` | **9** — `INTERFACE.md` §5.2.1, §5.3.2, §5.4.1, §5.6.1 (**21** rules, 20 pinned, 1 tagged) |
| `ROADMAP.md` kill-row trips | 6 | **8** — the seventh and eighth both found by this row's loop, both one defect |

**The floor held on every commit.** The brief's floor was 226 ids, sync `549 passed`, async `584 passed`; both suites ran on all three legs before each of the six commits landed, and the count moved 226 → 228 → 230 → 232 → 238 → 245 → **249**.

**The one deliberate exception, and it is on the record.** The commit that landed item 1 left the suite **RED** — `check_merge_guard.py` runs inside the contract suite, and its new axis reported 8 problems against code that had not been changed yet. That is the brief's order (*the gate lands before the change it must see*) and the commit message says so in its second paragraph. Item 2 turned it green.

---

## 2. Item 1 — the staleness axis, watched FAILING before the change it must see

The brief's order is that **the gate lands before the change it must see**, and the fifth trip's lesson is why: *a checker built in the same hour as the fix, by the same hand, shares its blind spot.* So [`check_merge_guard.py`](https://github.com/stephan-dyson/open-ontology/blob/main/docs/tools/check_merge_guard.py) gained its staleness axis **first**, with the fixture written from the sixth trip's own record ([`2026-08-29-3c-rulings-R6-R12.md`](../decisions/2026-08-29-3c-rulings-R6-R12.md), Door 1) rather than from the fix that follows it.

### 2.1 What the axis is, and why it is a second axis rather than a sixth state

Every state Part B held before this row — `known-different`, `known-equal`, `empty`, `unknowable`, `kind-mismatch`, `partial`, `truncated` — is a state **two extents are in at the moment one guard looks**. Staleness is a state **the store** is in: an identity written when two extents agreed, over a vocabulary that then grew. It cannot be posed by seeding two predicates and calling one function. It needs Door 1's recipe, which is *two individually legal merges and one ordinary new type*:

1. `commentable`, `searchable` and `taggable` all have extent `{aaa_note, bbb_memo, ccc_card}`;
2. `merge(commentable → searchable)` — **legal, and it must stay legal** (`C10-09`: the guard is narrowed, not banned). `searchable` absorbs `commentable` as an alias; `commentable` retires with `searchable` as its successor;
3. a new type `zzz_doc` declares `searchable` and `taggable`. **No governance act at all — somebody added a type.** Now `searchable` and `taggable` are `{aaa, bbb, ccc, zzz}` and `commentable` is still `{aaa, bbb, ccc}`;
4. the identity written at step 2 is still answered at confidence 1.0, over two extents that no longer agree.

Three members before the merge and a fourth after it is deliberate: `DegradedAdapter`'s `page_cap` only caps a query it would otherwise return *more* rows than, so a two-member extent never pages and the `partial`/`truncated` doubles would have run over a fixture that cannot express what they are for.

**It asks `resolve_type` as well as the four collapsing callers**, because the read is where a stale claim is cashed — and `reinstate`, which `KNOWN_CALLERS` records as a collapsing caller (a verdict a reviewer had to correct from `False` during the sixth trip), had no probe at all before this row.

### 2.2 The run, against the code as it stood at that commit — **8 problems, and every one of them is the read**

*(A historical record of the gate landing red. `check_merge_guard.py` today has six axes and exits 0; §6 is what happened in between.)*

`py docs/tools/check_merge_guard.py` with `OO_POSTGRES_DSN` set, three legs:

```
  sqlite          resolve_type  stale                        FAILED
  sqlite          merge_types   stale                        guarded
  sqlite          retire        stale                        guarded
  sqlite          import_types  stale                        guarded
  sqlite          reinstate     stale                        guarded
  sqlite          resolve_type  stale (unknowable)           FAILED
  sqlite          merge_types   stale (unknowable)           guarded
  sqlite          retire        stale (unknowable)           guarded
  sqlite          import_types  stale (unknowable)           guarded
  sqlite          reinstate     stale (unknowable)           guarded
  sqlite          resolve_type  stale (partial)              FAILED
  sqlite          merge_types   stale (partial)              guarded
  sqlite          retire        stale (partial)              guarded
  sqlite          import_types  stale (partial)              guarded
  sqlite          reinstate     stale (partial)              guarded
  sqlite          resolve_type  stale (truncated)            FAILED
  sqlite          merge_types   stale (truncated)            guarded
  sqlite          retire        stale (truncated)            guarded
  sqlite          import_types  stale (truncated)            guarded
  sqlite          reinstate     stale (truncated)            guarded
  sqlite_minimal  resolve_type  stale                        NOT REACHABLE
  sqlite_minimal  merge_types   stale                        NOT REACHABLE
  sqlite_minimal  retire        stale                        NOT REACHABLE
  sqlite_minimal  import_types  stale                        NOT REACHABLE
  sqlite_minimal  reinstate     stale                        NOT REACHABLE
  postgres        resolve_type  stale                        FAILED
  postgres        merge_types   stale                        guarded
  postgres        retire        stale                        guarded
  postgres        import_types  stale                        guarded
  postgres        reinstate     stale                        guarded
  postgres        resolve_type  stale (unknowable)           FAILED
  …
  postgres        resolve_type  stale (partial)              FAILED
  postgres        resolve_type  stale (truncated)            FAILED

  states that could not be REACHED on a leg (not passes):
    sqlite_minimal / … / stale: this backend refuses the LEGAL merge the fixture is
    built on (predicate_merge), so no identity can be written here over two agreeing
    extents and the stale state is unreachable

  - sqlite / resolve_type / stale: resolve_type('commentable') answered 'searchable' at
    confidence 1.0 carrying [] -- and the two predicate extents that claim stands on no
    longer agree. The claim was TRUE WHEN IT WAS MADE and the vocabulary moved: Rule U's
    fourth operand, unwarned, in the call 5.3 calls a guarantee

8 problem(s).
```

**Read the shape of that table, not only its failures.** The four *write* doors are `guarded` on every leg and every double — those are row 4c's four fixes for the sixth trip, holding under a fixture built to attack them. The one row that fails is **the read**, on both knowable legs and all three degraded doubles, and it is exactly the gap Q56 names: *row 4c closed the doors; it did not close the gap.*

**`sqlite_minimal` prints NOT REACHABLE rather than passing.** A backend that cannot compute an extent refuses step 2's merge — correctly, under Rule U — so it cannot hold a stale identity at all. Ruling **R12**'s rule applied to this checker: a verdict without its coverage line is not a verdict.

### 2.3 The axis's own first defect, found by running it rather than reading it

The first cut filed all three degraded doubles as *unknowable*, and asserted that `retire('searchable', successor='taggable')` must therefore be REFUSED on each. The run said otherwise on `stale (partial)`: an honest **page** carries a cursor to the rest, `_extent` loops to exhaustion (the fifth trip's own fix), so both extents are read in full, they genuinely agree, and the collapse is as legal there as on the bare leg. **The row was asserting the wrong answer** — the fifth trip's lesson one level up, and visible only because the checker was run rather than reviewed. Corrected in place, with the reason written into the fixture.

---

## 2b. Which existing ids had to change, and this is the notice the brief requires

**The brief's rule:** *"Every existing kill-row id must still pass unchanged; if one must change, say why in `4D-RUN.md` before changing it."* No kill-row id changed. **Three ordinary ids did** — `C3-10`, `C4-08`, `C8-02` — all for one reason, and this section was written before any of them was touched. *(It said **five** until row 4d's third round checked: `C9-15` and `C16-02` were never edited. `C9-15` failed on the `C3-13` cause below, and `C16-02` changed only through the shared module-level fixture it borrows. The commit message at `843af71` repeats the same error — it says five and lists four — and is corrected here rather than rewritten there.)*

`retire(successor=)` now refuses **`successor_unregistered`** when the successor names no entry (round 1, lens A's BLOCKING 1 — every identity guard on that call is nested inside *"if the successor row exists"*, so naming a successor before it is registered skipped all three, and `resolve_type` then cashed the redirect at 1.0 as soon as the word arrived). Five fixtures name a successor they never create:

| id | the fixture | what changed, and why it is a fixture defect rather than a rule defect |
|---|---|---|
| `C3-10` | `retire("watch", successor="capture")`, `capture` never seeded | **Its subject is preserved exactly and gets sharper.** The test asserts a retired name is *named in the resolution rather than silently omitted*, with its `retire_reason` and its successor in `reason` — and it happened to reach *"the successor is not live"* by never creating it. It now seeds `capture`, retires `watch` toward it, and then retires `capture` too. Same five assertions, same subject, and the state is now one a governed vocabulary can actually be in |
| `C4-08` | the same | seeds `capture`. The subject — *a retired name is not silently reusable* — is untouched: `propose_type` still returns the tombstone |
| `C8-02` | the same | seeds `capture`. The subject is *history is append-only*; the successor is scaffolding |
| `C16-02` | the same, *through the shared `exercised` fixture* | **the test body is UNCHANGED.** The fixture it borrows seeds `recording` — not `capture`, because `C16-03` seeds `capture` itself and asserts that doing so writes new events |
| `C9-15` | — | **UNCHANGED.** It already seeded `capture`, and it failed on the **`C3-13` cause** below rather than this one |

**And `C3-13` failed for a different reason, which changed the fix rather than the test.** Its whole subject is a backend that caps an unlimited query, and the first cut of lens A's BLOCKING 5 made `propose_type` **refuse** when the collision scan could not finish. That does not narrow the guard, it **bans the call on every paging backend** — at exactly the scale (UC3: one namespace, dozens of agencies, thousands of active types) where paging happens. `C10-09`'s own lesson, one call along. So the partial look **warns** (`alias_check_incomplete:<why>`) rather than refusing, at all four doors, which is §5.4's own rule — this call refuses two things and warns about everything else — and the shape `reinstate_alias_check_unavailable` already had for the same question one call away. **`C3-13` is unchanged.**

**Three more moved in rounds 2 and 3, each with its reason in the test:** `C17-45` gained `force=True` on the second leg of the cycle it deliberately builds, because `retire(successor=)` now refuses a **retired** successor (`C9-25`) — and `stores_events`, because a forced retirement needs somewhere to record the override; and `C3-14`'s near-miss assertion was found by mutation to sit inside a conditional that never runs, so §5.3.2-5 is now honestly `prose-only:` rather than falsely pinned.

---

## 3. Deviations — every place the implementation could not follow the ruling as written

R54 says *"the fix is one line in `_extent`"*. It is not, and the reason it is not is the most useful thing this row learned. Every deviation below is recorded rather than designed away, which is standing constraint 7's rule.

| id | what the ruling said | what shipped, and why |
|---|---|---|
| **D-4d-1** | *"`_extent` … resolve the IDENTITY"* — one line | `_extent` gained a **keyword-only `identity=False`**, and every one of the five collapsing guards keeps the positional call. **A single unconditional line would have reopened the kill row through the fix meant to close a different hole**: the guards compare two extents to decide whether a collapse asserts something false, and the merge under examination is exactly what joins the two names into one identity — so the two closures would be equal *by construction*, the guard would agree with itself, and `check_merge_guard.py`'s stale axis would have gone quiet on the store it was built to fail. §5.2.1-4 states the rule; `C10-14` is what breaks if a later row flips the default |
| **D-4d-2** | the same one line | `list_types(predicate=)` needed a **second adapter query** as well. Its default is `namespace=None` — the ordinary call, and the one R54's own example uses — and an identity is per `(namespace, kind)`, so there is no one identity to resolve. It is answered by one bounded `name_in` lookup naming the namespaces that hold a `kind="predicate"` row of that word, then one query per closure word **inside** each. Bounded (at most one row per namespace), never the unbounded census ruling **R13** declined to page. **The first cut of this change fell back to the written word when `namespace is None`, which quietly made R54 a no-op in the ordinary call**; caught by running the probe, not by reading it |
| **D-4d-3** | Q56: *"when an exact hit is answered through an alias or a successor"* — one place | **Two branches, because `get_type` matches `name` and never `aliases`.** A successor redirect is the exact-match branch; an aliased word never reaches it at all — it is *scored*, and the shipped resolver rates an exact alias 1.0, which is the accident `C3-11` turned into a registry guarantee. Both are re-verified, and `C3-14`/`C10-14` pin one each |
| **D-4d-4** | *"`check_spec_drift.py` extended for the new/changed INTERFACE sections"* | The four R31 tables are **subsections** (§5.2.1, §5.3.2, §5.4.1, §5.6.1), not tables under §5.2/§5.3/§5.4/§5.6. R31 requires a section's rule numbers to run 1..N with no gap, so a table under `### 5.3` would claim to enumerate every rule in `resolve_type` — a document this row did not write and has no standing to renumber. **The residual is stated in the checker**: the rest of those four sections stays outside the gate |
| **D-4d-5** | *"a new extent-pair state"* in Part B | It is a **second axis** with its own fixture and its own probes, not a sixth row of `STATES`. Every state Part B held is a state two extents are in *when one guard looks*; staleness is a state **the store** is in, and posing it takes two individually legal merges and one new type. It also probes `resolve_type` — the only one of the five that writes nothing — and `reinstate`, which `KNOWN_CALLERS` has recorded as a collapsing caller since the sixth trip corrected that verdict and which had **no probe at all** |
| **D-4d-6** | — | The stale axis's own first cut filed all three degraded doubles as *unknowable* and asserted `retire(successor=)` must be REFUSED on each. **On `partial` that is the wrong answer**: an honest page carries a cursor, `_extent` loops to exhaustion (the fifth trip's fix), the extents are read in full and genuinely agree. Corrected, with the reason written into the fixture |
| **D-4d-7** | — | `predicates(of=…)` now walks an identity closure **per predicate row**, and only when `of=` was given. The closure is one paged read of a namespace's retired rows of that kind, memoised per call; `predicates()` already reads events per row, so this is not a new order of cost. Raised as **Q62** rather than optimised |
| **D-4d-9** | — | **The Postgres leg leaked a schema per fixture and dropped none.** `check_merge_guard.py` builds a fresh store for every (caller × state × leg), and on Postgres that is a fresh **schema**; six axes deep it is ~50 a run. The database reached **19,220** `oo_*` schemas, and the catalogue bloat **segfaulted the backend three times** during round 1, each followed by ~4.5 minutes of crash recovery — which is also why two suite runs in this row failed with *"the database system is in recovery mode"*. **Fixed at the source rather than by raising `max_locks_per_transaction`:** the checker drops every schema it created in a `finally`, and `C0-08`'s race fixture — which built its own schema and dropped nothing, on every run of the suite since row 3c — registers a finalizer so it goes **even when the test fails**. `DROP DATABASE` / `CREATE DATABASE` cleared the backlog; a full three-leg run now leaves **zero**, asserted after every run in this row since. *(The supervisor's own count at 03:55 was 18,694; mine two hours later was 19,220. Both are true readings of a number that was still growing.)* |
| **D-4d-8** | R55 | The warning's alias half is a scan of the namespace's **active** rows, so a page the backend could not finish leaves the warning **absent**. Tagged `prose-only:` at §5.4.1-5 with the reason: an absent warning asserts nothing, so there is nothing observable to pin — and the rule is on the record so a later row cannot read the absence as a guarantee |

---

## 4. The rule → id mapping (standing constraint 8)

**`check_spec_drift.py` now reads `INTERFACE.md` as well as `EDGES.md`**, and row 4d is the first row to change rules in that document since ruling R31 landed. **Twenty-one** numbered rules, **twenty pinned by a contract id and one tagged**:

| section | rules | ids |
|---|---|---|
| §5.2.1 — the identity reading (**R54**) | 4 | `C2-06`; and `C10-13`/`C10-14` for 5.2.1-4 — **not `C10-09`**, which round 3 proved by mutation still passes when the default is flipped |
| §5.3.2 — staleness at the read (**Q56 default**) | 8 | `C3-14`, `C10-14`, `C10-16`; 5.3.2-5 `prose-only:` |
| §5.4.1 — the declared-predicate warning (**R55**) | 5 | `C4-11`, `C12-11`; 5.4.1-5 `prose-only:` |
| §5.6.1 — the identity filter (**R54**) | 4 | `C6-08` |

**Writing the tables is what showed three rules had no assertion at all**, and all three got one rather than a tag:

- **5.2.1-3** — an unresolvable closure returns `extent_size: None` with the closure's own `why`. Rule U one level above the extent page it already applied to. *(The fixture failed on its first run: the successor scan is per `(namespace, kind)`, and the first cut retired **entities**. A fixture that cannot pose its own question is the fifth trip's lesson, learned here for the price of a test rather than of a guard.)*
- **5.3.2-5** — a near miss is not an identity claim and is not re-verified. Nobody wrote that two words denote one thing; the scorer merely rated them alike.
- **5.6.1-4** — the written word is always queried, so a type declaring a predicate that names no row at all is still found. **The identity only ever adds**, and a fix that swapped the word for a closure would have deleted this answer.

### 4.1 The six kill-row ids, unchanged

R54 changes what a read means in the expression **all six kill-row trips run through**, so the row's own test of itself is that nothing pinning a trip had to move. **None was edited:** `C9-08` (unknowable), `C10-09` (empty), `C10-11` (partial / truncated), `C10-13` (the sixth trip's four doors), `C9-18`…`C9-21`, `C12-08`/`C12-09`. `check_merge_guard.py` is the mechanical form of the same claim and exits 0 on three legs, three doubles and **all six axes**.

---

## 6. The adversarial loop — three rounds, six lenses, **thirty-one findings**, and it did NOT converge

**Stop rule (standing constraint 7, and the brief's):** two consecutive clean rounds, or three rounds plus an honest convergence note. **Three rounds ran; none was clean; this is the note.**

| round | lenses | BLOCKING | MAJOR | MINOR | ids after |
|---|---|---|---|---|---|
| 1 | attack 4c round 3's five guard changes · reach the kill row through this row's changes | **7** | 5 | 2 | 238 |
| 2 | attack round 1's own fixes · integrate the row as a consumer, and measure | **4** | 4 | 4 | 245 |
| 3 | reach the kill row · does the writing tell the truth about the code | **5** | 6 | 11 | 249 |

**The kill row tripped twice more — a SEVENTH and an EIGHTH time — and both are one defect.**

- **Seventh** (round 1): every alias guard found its collision by an exact **byte** comparison while the shipped resolver compared **normalised** words and rated an exact match 1.0. `aliases: ["Commentable"]` was written where `["commentable"]` is refused non-overridably, and `resolve_type("commentable")` then answered at 1.0 over differing extents. Fixed by publishing **one** notion of *the same word* beside the resolver, so the registry cannot disagree with the scorer that delivers its 1.0.
- **Eighth** (round 3): the *same disagreement*, in the one door the seventh trip's fix did not reach — §5.4's *"a retired name is not reusable"*, which was still `get_type`'s byte match, and round 2's keyed guard scans **active** rows only. Four ordinary calls, no alias, no import, no merge.

> **That pairing is the most useful thing this loop produced, and it is not flattering.** A fix that publishes a shared key is only as good as its application, and this row shipped the key and missed a caller — **the sixth trip's own diagnosis (*a guard written for one call, over a fact more than one call can change*) applied to a fix rather than to a guard.** Full records, for countersignature: [`2026-08-29-3c-rulings-R6-R12.md`](../decisions/2026-08-29-3c-rulings-R6-R12.md).

### 6.1 What the loop established that no gate in this repository measures

1. **Every round found defects in the previous round's fixes, and round 2's were the worst.** Round 2 found **five** defects inside round 1's fixes — including one where a one-row probe was replaced by an unfiltered namespace scan whose partial page fed a **non-overridable refusal**, which *banned `import_types` on every paging backend*. That is verbatim the lesson round 1 had learned one call earlier and written into its own commit message. Round 3 then found the same class a third time, in round 3's own first cut, inside one suite run.
2. **`check_merge_guard.py` has now exited 0 through trips five, six, seven and eight** — paging, staleness, the alphabet in `aliases`, the alphabet in `name`. Each time the reason was identical: *a checker only asks the questions its fixtures can pose*. It gained an axis after each, and it is at **six** now. This is the fourth consecutive row-level restatement that constraint 7's loop and constraint 8's gate are both load-bearing and neither substitutes for the other.
3. **For the first time, the loop found defects OUTSIDE what the row touched.** `4C-RUN.md` §6.6 recorded that across three rounds *"not one finding was in code this row did not touch"*. Five of round 1's twelve findings are in **row 4c's** guards. Read one way that is reassuring; read another it says guards laid down at a loop's cap need the review they did not get — which is what the supervisor ruled row 6b to be.
4. **A rule table can lie, and only mutation testing finds out.** Round 3's second lens broke the implementation of twenty-one rules one at a time and checked whether the id each table row names actually went red. **Two did not**: §5.3.2-8's warning could be deleted with all 245 ids still green, and §5.6.1-3's bounded lookup could be replaced by an unbounded census with all 245 still green. A third — §5.3.2-5 — had an assertion inside a conditional that never ran, which reads as coverage and is not. All three are corrected; §5.3.2-5 is now honestly `prose-only:`.
5. **The findings did NOT shrink.** Sixteen BLOCKING across three rounds, on work that had five green mechanical gates before the loop started and six after. What did shrink is their *distance from the row*: round 1 found a shipped collapse, round 3 found mostly documentation that had stopped being true. That is the shape of convergence without its arrival.

### 6.2 What a fourth round would find, [Assumed]

Every round of this row attacked the previous round's fixes and every one succeeded. Round 3's fixes have had no such round. **Stopping here is the cap, not a verdict that the work is clean**, and this document is the record that it was stopped rather than finished. The most likely next finding, on this row's own evidence: another door that compares a word by bytes, or another rule table row whose id passes for a different reason than the rule states.

---

## 7. What the build taught

**1. A ruling can say "one line" and be right about the intent and wrong about the shape.** R54's one line, written literally, makes every identity guard compare a merge to itself. What found it was the order the ruling imposed — the gate landed before the change it must see — so *"what does this do to every guard?"* had a mechanical answer before the change was written rather than an argument after it.

**2. Publishing a shared definition is half a fix; applying it is the other half.** The seventh trip minted `identity_key`; the eighth is the one door it did not reach. A key that lives in one place cannot drift — and a key that is *applied* in five places out of six is still a registry that disagrees with itself.

**3. "The guard is narrowed, not banned" had to be learned three times in one row.** Round 1 refused on a partial look and banned `propose_type` on every paging backend (`C3-13` caught it). Round 2 fed a namespace scan's partial page into a non-overridable refusal and banned `import_types` there (`C12-13` caught it). Round 3's first cut did the same thing again in the same function. **The rule is not "be careful"; it is *never turn "we could not finish looking" into a refusal*,** and it is now written at the three call sites.

**4. A fixture that asserts a VERDICT has to be rewritten every time a guard moves; one that asserts the INVARIANT does not.** `check_merge_guard.py`'s `retire` row was corrected twice in one row — once for the paging double, once when the chain fix made the call correctly refuse. It now asserts the thing the kill row is actually about: `resolve_type('commentable')` must not answer `taggable` at 1.0, however the call answers.

**5. Mutation testing is the only way to know a rule table is true.** Nineteen of twenty-one mutations reddened the id their rule names. The two that did not were rules nothing exercised, in tables written by this row to satisfy constraint 8 — the gate was green and two of its claims were decorative.

**6. The identity of the NAME is a Rule U question, and nobody had asked it.** Four operands of Rule U are about the extent comparison — unknowable, empty, partial, stale. Trips seven and eight are about the *name*: **one word is not one string**, and *we cannot say what word this is* (an empty key) is not *it is the same word*.

**7. A checker that has to be run to be believed must be cheap enough to run.** The Postgres leg created a schema per fixture and dropped none — ~50 a run, six axes deep. The database reached **19,220** `oo_*` schemas and the catalogue bloat **segfaulted the backend three times**, each followed by ~4.5 minutes of recovery. Fixed at the source, not by raising `max_locks_per_transaction`. See D-4d-9.

---

## 8. Questions for the supervisor — **Q61 onward**

**Q61 — Should `identity_stale` distinguish *the extents differ* from *the extents cannot be known*?** The value fires for both, which is Rule U's own reading. But on `indexes_membership=False` — **UC1 Tenshen's declared shape**, and `sqlite_minimal`, a reference leg — **every** predicate redirect carries it, permanently. This project has twice fixed exactly that shape with the sentence *a signal that never turns off is noise*. *Recommendation: keep one value for v0 and record this*, because the consequence for a caller is identical — do not trust this 1.0 without looking — and splitting doubles a closed vocabulary for a distinction `detail` carries elsewhere.

**Q62 — ~~Is `predicates(of=…)`'s per-row closure walk affordable?~~ MEASURED, and fixed in round 2.** The question asked for a measurement before a two-line change; round 2's integrator lens made it. Query counts were linear and **wall clock quadrupled per doubling** of the predicate count: 13.9× on a plain `predicates(namespace=…)` and 26.5× with `of=`, at 3,481 rows. One closure cache threaded through the call took 80 merged pairs from **109.6 ms to 22.3 ms**. *No ruling needed; recorded because the question is answered and a supervisor should not be asked to rule on it.*

**Q63 — Does `consumers` want R54's reading?** *(Corrected in round 3: the original wording named the wrong surface.)* `Consumer.gate` already resolves the identity under **R38**, and `_gate_warnings` queries `include_retired=True` deliberately, so **a gate naming a merged-away word is not warned** — the claim this question originally made is false, and running it is what showed that. The surface that *is* wrong is the one round 2 found for `list_types`: an identity written **only as an alias**, with no row of that name, was invisible from the absorbed word (`C6-09`). That is fixed. What remains open is whether `gate_unregistered` should say something about an alias-only identity. *Recommendation: fold it into row 6b, which the supervisor has ruled is the review row 4c's guards did not get.*

**Q64 — Should the guards' written-word reading be NAMED rather than defaulted?** Every collapsing guard gets the narrow reading *because it is the default*. A later row that flips it reopens the kill row silently. *Recommendation: no code change in v0; take it in 6b with R53's extraction* — R53's own reason applies verbatim, and round 3 proved by mutation that `C10-13`, `C10-14`, `C10-16`, `C10-17`, `C10-18` and `C3-14` all break if the default is flipped, which is the mitigation that shipped instead.

**Q65 — Is `resolve_type` the right place for the second half of Q56, or is the answer a new call?** The founder's open half is *refuse, or lower the confidence*. There is a third shape: leave §5.3's guarantee alone and add a **read** that answers *"is this identity still sound?"* — the question a steward asks before a merge and a consumer asks before trusting a redirect. *Recommendation: raise it, do not take it*; the founder's ruling on Q56 should see three options rather than two.

**Q66 — `identity_stale` is PERMANENT by construction. Is that the right shape for a consumer?** *(Round 2.)* The absorbed word is retired, so its own written extent can never grow again; the survivor's can. The **first** ordinary type declared against a survivor after a merge therefore makes the two written extents unequal *for good*, and no call amends a live type's `predicates` to undo it. Weakening the comparison to **containment** would make the warning miss **Door 1** — the sixth trip's own walk — so the comparison stays. §5.3.2 now says the value means *this identity has grown apart from the equality that justified it*, not *act on this now*. *Recommendation: rule on the wording, not the comparison.*

**Q67 — Does `_extent(identity=True)` owe a staleness signal of its own?** *(Round 3.)* After R54 the identity's extent includes members declared under either word — which is the ruling working — but a consumer reading `predicates(of=X)` gets no hint that the identity's own justification has gone stale, while `resolve_type` warns. `PredicateEntry` has no `warnings` field, so this is a shape change rather than a value. *Recommendation: not in v0. Record it against Q66*: if the founder rules that permanence makes the warning noise, this is the surface that would carry the better signal instead.

**Q68 — Should `identity_key` erase non-Latin words, or should the registry refuse to hold what it cannot read?** *(Round 3, and it is founder-adjacent.)* The empty-key hole is closed — an unreadable word is never *the same word* as anything — but the underlying fact remains: this registry can hold an alias it cannot compare, and every guard therefore passes it silently. UC3's catalogue is multi-agency; not every label is Latin. The alternatives are a proper Unicode fold (NFKD, combining marks, per-script rules — a real dependency and a real decision about which scripts fold together) or refusing a non-comparable alias at the write door. *Recommendation: record it, ship the empty-key guard, and put the fold to the founder before beacon 2B, because it decides what vocabularies this registry will accept.*
