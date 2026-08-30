# 4D-RUN — roadmap row 4d: identity staleness, and the gate that could finally pose the question

**Row:** 4d. **Date:** 2026-08-30. **Repo:** [`open-ontology`](https://github.com/stephan-dyson/open-ontology), `main`.
**What it carries:** the **Q56 default** (`resolve_type` re-verifies a predicate identity claim at the read and warns when it has gone stale — confidence stays 1.0, because the expensive half is the founder's), ruling **R54** (`_extent` and `predicates()` resolve the IDENTITY, not the written word) and ruling **R55** (the write-door warning), from [`2026-08-30-4c-rulings-R48-R57.md`](../decisions/2026-08-30-4c-rulings-R48-R57.md).
**Why it ran next:** row 4c's loop tripped [`ROADMAP.md`](https://github.com/stephan-dyson/open-ontology/blob/main/ROADMAP.md)'s kill row a fourth, fifth and **sixth** time, and the sixth is *different in kind*. Trips 1–5 were all *the guard did not look properly*. The sixth is **the guard looked correctly, and then the fact changed** — every identity guard compares predicate extents at **write** time, `resolve_type` grants confidence 1.0 at **read** time, and the vocabulary moves in between. Row 4c closed the four doors it found; it did not close the gap. **Rule U's fourth operand: STALE is not equal.**

---

## 1. The headline, in numbers

| | before (row 4c) | after |
|---|---|---|
| contract ids ([`PACKAGE.md`](https://github.com/stephan-dyson/open-ontology/blob/main/docs/specs/PACKAGE.md) §6.2) | 226 | *(in progress)* |
| sync suite, one run, three legs | `549 passed, 148 skipped` | *(in progress)* |
| async suite, one run, three legs | `584 passed, 148 skipped` | *(in progress)* |
| `warnings` values ([`INTERFACE.md`](https://github.com/stephan-dyson/open-ontology/blob/main/docs/specs/INTERFACE.md) §5.4) | 29 | *(in progress)* |
| `Refusal.reason` values (§5.12) | 28 | *(in progress)* |
| mechanical gates in the suite | 5 | *(in progress)* |
| `ROADMAP.md` kill-row trips | 6 | *(in progress)* |

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

## 3. Deviations

*(to be completed)*

## 4. Rule → id mapping

*(to be completed)*

## 5. What the build taught

*(to be completed)*

## 6. Questions — **Q61 onward**

*(to be completed)*
