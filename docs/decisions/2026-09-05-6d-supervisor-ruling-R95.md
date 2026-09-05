# R95 — K2 is NOT a trip: a stranger of another kind and another spelling decides whether `import_types` refuses, and that is the `I-4` mis-keyed cell at change A's own consumer

**Ruled 2026-09-05 by the ontoloche program supervisor**, classifying the second candidate row 6d's
round 3 routed at [`6D-RUN.md` §6.19–6.21](https://github.com/stephan-dyson/ontoloche/blob/main/docs/runs/6D-RUN.md)
(`0d4ff66`: round 3 closes NOT YET, 30 distinct / 9 BLOCKING). Follows
[R94](2026-09-05-6d-supervisor-ruling-R94.md), which countersigned K1 as the twenty-third trip.

## Verification, done here rather than accepted

- **[Observed]** `ontoloche/registry.py:5196–5204`: `standing = adapter.get_type(namespace, name, kind=…)`;
  when that is `None`, the widened `_word_rows(…, match_aliases=True)` scan collects retired rows and
  `named = [r for r in retired_here if same_word(r.name, name)]` — **any kind, any spelling variant** —
  and `standing = named[0]`. This is change A's (`8d717c9`) widening, the twenty-first trip's fix.
- **[Observed]** `registry.py:5248`: the `name_previously_retired` refusal fires only when the incoming
  row is **not** itself retired (`status != "retired"`).
- **[Observed]** `registry.py:5354`: `if standing is None:` gates the `_alias_holder` NAME guard — the
  guard that refuses `alias_collision` when a live row already holds the word.
- **[Observed]** The kill-row lens's probe (its `K4`, the run record's `K2`) and its transcript: import
  `holder`(entity, alias `w_word`); import `w_word`(predicate, `status="deprecated"`) →
  **without** a bystander: `import_refused:alias_collision`; **with** an entity tombstone `w_word_`
  present first: the predicate tombstone `w_word` is **written**, and `reinstate('w_word')` then refuses
  `alias_collision` with `collides_with: holder`. The mechanism reads straight off the three lines above.

## R95, part one: K2 is not a kill-row trip

The criterion is a state reached by ordinary calls at shipped doors **where two rows answer to one
word.** After K2's write the store holds `holder` (active, alias `w_word`) and `w_word` (a **retired**
predicate). One row answers at 1.0; the other is a tombstone **the importer itself asked to write as
retired.** Nothing is displaced at `resolve_type`; no identity's answer changed hands. The
twenty-third trip (R94) and the fifteenth, sixteenth, twentieth and twenty-first all have a **live**
row answering over a tombstone's word — the tombstone's identity silently taken. K2 has no such taking.
**Not countersigned as a trip. The count stays at TWENTY-THREE.**

## R95, part two: what K2 is, and it is BLOCKING

**A stranger decides the door's answer.** The same row is refused when the store is clean and written
when an unrelated tombstone — another kind, another spelling — happens to exist. That is R93's
twenty-second-trip axis (a row identified by word where §4.1 lets kinds share one) reappearing **inside
`import_types` itself, three lines below the twenty-first trip's fix**: change A widened `named` to
cross-kind, cross-spelling tombstones so the byte-identical tombstone would be found, and did not
enumerate the **`if standing is None:` gate at 5354 as a consumer of that widening.** A standing-rule-(d)
failure by number, at the row's own commit, on the commit's own subject.

Classified as the **`I-4` mis-keyed** cell: a fact looked up on one key (word, any kind) and then used as
if it were a fact on another (this name, this kind). The fix is one of two, and the commit says which
it declined: the NAME guard runs regardless of a cross-kind `standing`, or `standing` is only ever set
from a **same-kind** tombstone with the twenty-first trip's byte-identical case preserved.

## R95, part three: a spec question surfaced, not minted

K2's control refuses a **predicate** named `w_word` because an **entity** holds `w_word` as an alias, and
`reinstate` refuses on the same cross-kind pair — while `PACKAGE.md` §4.1 permits two kinds to share a
word and the twenty-second trip was countersigned on exactly that permission. Whether `alias_collision`
at the import and reinstate doors should fire **across kinds** is a specification question the row's
fix set will meet head-on. It is recorded here so that it is met as a question and not answered by
accident; if it needs a number, the next is **Q97**.

## Unchanged

The count is twenty-three (R94). `stop` was put for the fifteenth time in R94 and this ruling adds no
put. Q56, Q94 and Q95 remain the founder's. Standing rules (a)–(e) stand. Beacon's pin is
**[Observed]** still an ancestor.

Next ruling number: **R96**. Next question number: **Q97**.
