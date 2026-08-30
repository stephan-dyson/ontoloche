# 4D-RUN — roadmap row 4d: identity staleness, and the gate that could finally pose the question

**Row:** 4d. **Date:** 2026-08-30. **Repo:** [`open-ontology`](https://github.com/stephan-dyson/open-ontology), `main`.
**What it carries:** the **Q56 default** (`resolve_type` re-verifies a predicate identity claim at the read and warns when it has gone stale — confidence stays 1.0, because the expensive half is the founder's), ruling **R54** (`_extent` and `predicates()` resolve the IDENTITY, not the written word) and ruling **R55** (the write-door warning), from [`2026-08-30-4c-rulings-R48-R57.md`](../decisions/2026-08-30-4c-rulings-R48-R57.md).
**Why it ran next:** row 4c's loop tripped [`ROADMAP.md`](https://github.com/stephan-dyson/open-ontology/blob/main/ROADMAP.md)'s kill row a fourth, fifth and **sixth** time, and the sixth is *different in kind*. Trips 1–5 were all *the guard did not look properly*. The sixth is **the guard looked correctly, and then the fact changed** — every identity guard compares predicate extents at **write** time, `resolve_type` grants confidence 1.0 at **read** time, and the vocabulary moves in between. Row 4c closed the four doors it found; it did not close the gap. **Rule U's fourth operand: STALE is not equal.**

---

## 1. The headline, in numbers

| | before (row 4c) | after |
|---|---|---|
| contract ids ([`PACKAGE.md`](https://github.com/stephan-dyson/open-ontology/blob/main/docs/specs/PACKAGE.md) §6.2) | 226 | **232** |
| sync suite, one run, three legs | `549 passed, 148 skipped` | **`561 passed, 154 skipped`** |
| async suite, one run, three legs | `584 passed, 148 skipped` | **`596 passed, 154 skipped`** |
| `warnings` values ([`INTERFACE.md`](https://github.com/stephan-dyson/open-ontology/blob/main/docs/specs/INTERFACE.md) §5.4) | 29 | **31** — `identity_stale`, `declared_predicate_merged` |
| `Refusal.reason` values (§5.12) | 28 | **28** — and that is the row's central result. Q56's cheap half REPORTS; refusing is the founder's |
| mechanical gates in the suite | 5 | **5** — and one of them gained a whole second axis |
| `check_merge_guard.py` axes | 1 (extent states) | **2** (+ **staleness**, five callers × three legs × three doubles) |
| spec sections under R31's rule gate | 5, all in `EDGES.md` | **9** — `INTERFACE.md` §5.2.1, §5.3.2, §5.4.1, §5.6.1 |
| `ROADMAP.md` kill-row trips | 6 | *(the loop has not run yet)* |

**The floor held on every commit.** The brief's floor was 226 ids, sync `549 passed`, async `584 passed`; both suites ran on all three legs before each of the six commits landed, and the count moved 226 → 228 → 230 → 232.

**The one deliberate exception, and it is on the record.** The commit that landed item 1 left the suite **RED** — `check_merge_guard.py` runs inside the contract suite, and its new axis reported 8 problems against code that had not been changed yet. That is the brief's order (*the gate lands before the change it must see*) and the commit message says so in its second paragraph. Item 2 turned it green.

---

## 2. Item 1 — the staleness axis, watched FAILING against today's code

The brief's order is that **the gate lands before the change it must see**, and the fifth trip's lesson is why: *a checker built in the same hour as the fix, by the same hand, shares its blind spot.* So [`check_merge_guard.py`](https://github.com/stephan-dyson/open-ontology/blob/main/docs/tools/check_merge_guard.py) gained its staleness axis **first**, with the fixture written from the sixth trip's own record ([`2026-08-29-3c-rulings-R6-R12.md`](../decisions/2026-08-29-3c-rulings-R6-R12.md), Door 1) rather than from the fix that follows it.

### 2.1 What the axis is, and why it is a second axis rather than a sixth state

Every state Part B held before this row — `known-different`, `known-equal`, `empty`, `unknowable`, `kind-mismatch`, `partial`, `truncated` — is a state **two extents are in at the moment one guard looks**. Staleness is a state **the store** is in: an identity written when two extents agreed, over a vocabulary that then grew. It cannot be posed by seeding two predicates and calling one function. It needs Door 1's recipe, which is *two individually legal merges and one ordinary new type*:

1. `commentable`, `searchable` and `taggable` all have extent `{aaa_note, bbb_memo, ccc_card}`;
2. `merge(commentable → searchable)` — **legal, and it must stay legal** (`C10-09`: the guard is narrowed, not banned). `searchable` absorbs `commentable` as an alias; `commentable` retires with `searchable` as its successor;
3. a new type `zzz_doc` declares `searchable` and `taggable`. **No governance act at all — somebody added a type.** Now `searchable` and `taggable` are `{aaa, bbb, ccc, zzz}` and `commentable` is still `{aaa, bbb, ccc}`;
4. the identity written at step 2 is still answered at confidence 1.0, over two extents that no longer agree.

Three members before the merge and a fourth after it is deliberate: `DegradedAdapter`'s `page_cap` only caps a query it would otherwise return *more* rows than, so a two-member extent never pages and the `partial`/`truncated` doubles would have run over a fixture that cannot express what they are for.

**It asks `resolve_type` as well as the four collapsing callers**, because the read is where a stale claim is cashed — and `reinstate`, which `KNOWN_CALLERS` records as a collapsing caller (a verdict a reviewer had to correct from `False` during the sixth trip), had no probe at all before this row.

### 2.2 The run, on today's code — **8 problems, and every one of them is the read**

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

## 2b. Five existing ids had to change, and this is the notice the brief requires

**The brief's rule:** *"Every existing kill-row id must still pass unchanged; if one must change, say why in `4D-RUN.md` before changing it."* No kill-row id changed. **Five ordinary ids did**, all for one reason, and this section was written before any of them was touched.

`retire(successor=)` now refuses **`successor_unregistered`** when the successor names no entry (round 1, lens A's BLOCKING 1 — every identity guard on that call is nested inside *"if the successor row exists"*, so naming a successor before it is registered skipped all three, and `resolve_type` then cashed the redirect at 1.0 as soon as the word arrived). Five fixtures name a successor they never create:

| id | the fixture | what changed, and why it is a fixture defect rather than a rule defect |
|---|---|---|
| `C3-10` | `retire("watch", successor="capture")`, `capture` never seeded | **Its subject is preserved exactly and gets sharper.** The test asserts a retired name is *named in the resolution rather than silently omitted*, with its `retire_reason` and its successor in `reason` — and it happened to reach *"the successor is not live"* by never creating it. It now seeds `capture`, retires `watch` toward it, and then retires `capture` too. Same five assertions, same subject, and the state is now one a governed vocabulary can actually be in |
| `C4-08` | the same | seeds `capture`. The subject — *a retired name is not silently reusable* — is untouched: `propose_type` still returns the tombstone |
| `C8-02` | the same | seeds `capture`. The subject is *history is append-only*; the successor is scaffolding |
| `C16-02` | the same | seeds `capture`. The subject is the whole-store invariants after a merge |
| `C9-15` | reached it through the `_support.seed` helper | already seeded `capture`; it failed on the **`C3-13` cause** below, not this one |

**And `C3-13` failed for a different reason, which changed the fix rather than the test.** Its whole subject is a backend that caps an unlimited query, and the first cut of lens A's BLOCKING 5 made `propose_type` **refuse** when the collision scan could not finish. That does not narrow the guard, it **bans the call on every paging backend** — at exactly the scale (UC3: one namespace, dozens of agencies, thousands of active types) where paging happens. `C10-09`'s own lesson, one call along. So the partial look **warns** (`alias_check_incomplete:<why>`) rather than refusing, at all four doors, which is §5.4's own rule — this call refuses two things and warns about everything else — and the shape `reinstate_alias_check_unavailable` already had for the same question one call away. **`C3-13` is unchanged.**

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
| **D-4d-8** | R55 | The warning's alias half is a scan of the namespace's **active** rows, so a page the backend could not finish leaves the warning **absent**. Tagged `prose-only:` at §5.4.1-5 with the reason: an absent warning asserts nothing, so there is nothing observable to pin — and the rule is on the record so a later row cannot read the absence as a guarantee |

---

## 4. The rule → id mapping (standing constraint 8)

**`check_spec_drift.py` now reads `INTERFACE.md` as well as `EDGES.md`**, and row 4d is the first row to change rules in that document since ruling R31 landed. Eighteen numbered rules, **seventeen pinned by a contract id and one tagged**:

| section | rules | ids |
|---|---|---|
| §5.2.1 — the identity reading (**R54**) | 4 | `C2-06`; and `C10-09`/`C10-13`/`C10-14` for 5.2.1-4, the rule that the guards keep the written word |
| §5.3.2 — staleness at the read (**Q56 default**) | 6 | `C3-14`, `C10-14` |
| §5.4.1 — the declared-predicate warning (**R55**) | 5 | `C4-11`, `C12-11`; 5.4.1-5 `prose-only:` |
| §5.6.1 — the identity filter (**R54**) | 4 | `C6-08` |

**Writing the tables is what showed three rules had no assertion at all**, and all three got one rather than a tag:

- **5.2.1-3** — an unresolvable closure returns `extent_size: None` with the closure's own `why`. Rule U one level above the extent page it already applied to. *(The fixture failed on its first run: the successor scan is per `(namespace, kind)`, and the first cut retired **entities**. A fixture that cannot pose its own question is the fifth trip's lesson, learned here for the price of a test rather than of a guard.)*
- **5.3.2-5** — a near miss is not an identity claim and is not re-verified. Nobody wrote that two words denote one thing; the scorer merely rated them alike.
- **5.6.1-4** — the written word is always queried, so a type declaring a predicate that names no row at all is still found. **The identity only ever adds**, and a fix that swapped the word for a closure would have deleted this answer.

### 4.1 The six kill-row ids, unchanged

R54 changes what a read means in the expression **all six kill-row trips run through**, so the row's own test of itself is that nothing pinning a trip had to move. **None was edited:** `C9-08` (unknowable), `C10-09` (empty), `C10-11` (partial / truncated), `C10-13` (the sixth trip's four doors), `C9-18`…`C9-21`, `C12-08`/`C12-09`. `check_merge_guard.py` is the mechanical form of the same claim and exits 0 on three legs, three doubles and both axes.

---

## 5. What the build taught

**1. A ruling can say "one line" and be right about the intent and wrong about the shape — and the difference is a reopened kill row.** R54's one line, written literally, makes every identity guard compare a merge to itself. Nobody reading the ruling would have caught it; the ruling is correct about what the *reads* should do. What found it was the order the ruling itself imposed: **the gate landed before the change it must see**, so the question *"what does this do to every guard?"* had a mechanical answer before the change was written rather than an argument after it.

**2. The staleness axis found its own defect on its first run, and that is the fifth trip's lesson working.** The first cut asserted the wrong answer for one of three doubles. It was found by *running* the checker, not by reviewing it — which is exactly what §6.4 of `4C-RUN.md` says about checkers built in the same hour, by the same hand, as the thing they check. The correction is written into the fixture rather than quietly applied.

**3. Part A caught the row's own new function within a minute of it being written.** `_declared_predicate_moved` READS a `successor` and scans `aliases`; it writes nothing. The checker does not care — its rule is deliberately over-broad, *any mention of an identity field's name anywhere in a function* — so the suite went red until a person wrote down what the function means. **The false positive cost one paragraph in `KNOWN_CALLERS`; a false negative costs the kill row**, and the sixth trip is the record that a wrong judgement written down is one a reviewer can disprove.

**4. Two of this row's three ruling-driven changes were the same fact at two ends of one seam.** R54 makes a declaration under an absorbed word **visible** (the survivor's extent holds it); R55 makes it **announced** (the declarer is told which identity it landed in). Neither is sufficient: a fact you can only discover by querying afterwards is not a fact reported to the person who could still act on it, and a warning at the door does nothing for the consumer reading an extent a year later. They were ruled together and they belong together.

**5. The default in `list_types` is the call, and a fix that skips the default fixes nothing.** `namespace=None` is the ordinary shape, and the first cut of R54 handled `namespace="default"` correctly and fell back to the written word for the default — a change that passed its own new test, because the test named a namespace. Caught by a throwaway probe that used the call the way a caller would.

**6. A closed vocabulary makes you say what a value is FOR, and that is where the design argument happens.** `identity_stale` had to be written into §5.4's table with its carrier, its cause and its ids before any code could emit it — and writing *"a warning, with the confidence untouched at 1.0, because refusing changes what this registry declines to serve and that is the founder's"* is the whole of Q56's split, in one table row, where the next reader will find it.

---

## 6. Questions for the supervisor — **Q61 onward**

**Q61 — Should `identity_stale` distinguish *the extents differ* from *the extents cannot be known*?** *(Founder-visible in consequence, though not in kind.)* The value fires for both, which is Rule U's own reading — *cannot be known to agree* is not *agrees*. But on a backend with `indexes_membership=False` — **UC1 Tenshen's own declared shape**, and `sqlite_minimal`, a reference leg — **every** predicate redirect carries it, permanently and unconditionally. This project has punished exactly that shape twice: `predicate_requires_review` riding onto every approved predicate (row 4c, round 1) and row 3d's durability warning, both fixed with the sentence *a signal that never turns off is noise*. *Recommendation: keep one value for v0 and record this, because the two facts have the same consequence for a caller — do not trust this 1.0 without looking — and splitting them doubles a closed vocabulary for a distinction `Refusal.detail` already carries elsewhere.* Revisit if a deployment on an unknowable backend reports the warning as noise; the cheap mitigation, if it is wanted, is a `<why>` suffix rather than a second value.

**Q62 — Is `predicates(of=…)`'s per-row closure walk affordable at UC3 scale?** The `of=` filter now asks `_identity_names(rec)` for every predicate row in the namespace, and each is one paged read of that namespace's retired predicate rows, memoised per closure call but **not across rows**. At UC3's scale (3,000 types, 30 namespaces) the retired-predicate set is small and the read is cheap; at a scale nobody has measured it is a scan per row. *Recommendation: leave it, record it, and measure it in the Phase 3 ingestion row that first runs `predicates()` in a loop.* `_successor_map` is already memoised per `(namespace, kind)` in the caller's cache dict; passing one cache across the row loop is a two-line change nobody should make without a measurement.

**Q63 — Does `consumers` want R54's reading too?** Ruling **R38** gave `Consumer.gate` the identity closure in row 4c, so `consumers(type)` and `retire`'s `live_consumers` guard already resolve the identity. `predicates`, `list_types` and `_extent` now do. **The one surface left comparing a written predicate word is `Consumer.gate`'s `gate_unregistered` warning**, which asks whether a gate names a registered `kind="predicate"` entry — a gate naming an absorbed word is registered, under another name, and is currently warned about. *Recommendation: fold it into row 6b's guard-extraction work rather than here*, because it is a fourth surface for one rule and R53 already scheduled the place where one function replaces five copies. Recorded so 6b reads this first.

**Q64 — Should the guards' written-word reading be named rather than defaulted?** Every collapsing guard calls `self._extent(ns, name, True)` positionally and gets the narrow reading **because that is the default**. A later row that flips the default — or a reader who assumes the identity reading is the obvious one — reopens the kill row silently, and the only thing standing between that and a shipped collapse is `C10-14` and `check_merge_guard.py`'s stale axis. *Recommendation: no code change in v0, and take it in row 6b.* Naming it (`_written_extent`, or a required keyword) is a shape change to the five guards in the same breath as R53's extraction, and R53's own reason applies verbatim: changing the guards' shape in a row that changes what they compare is how trips 2, 5 and 6 happened. **The mitigation that shipped instead is that the rule is written into §5.2.1-4 with the ids that break.**

**Q65 — Is `resolve_type` now the right place for the *second* half of Q56, or is the answer a new call?** The founder's open half is *refuse, or lower the confidence*. There is a third shape neither the ruling nor this row considered: leave §5.3's guarantee alone and add a **read** that answers *"is this identity still sound?"* — the question a steward asks before a merge and a consumer asks before trusting a redirect, which today can only be assembled from two `predicates()` calls. *Recommendation: raise it, do not take it.* It is a new surface in a document whose §1 non-goals list is load-bearing, and it competes with the cheaper answer (the warning that shipped). Recorded because the founder's ruling on Q56 should see all three options rather than two.
