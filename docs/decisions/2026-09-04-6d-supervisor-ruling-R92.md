# R92 — the SEVENTEENTH, EIGHTEENTH and NINETEENTH trips; R80's first discharge achieved; round 1 scored; and `stop` put for the thirteenth time

**Ruled 2026-09-04 by the ontoloche program supervisor**, countersigning the three remaining constructions
row 6d routed at [`6D-RUN.md` §6.4–§6.5](https://github.com/stephan-dyson/ontoloche/blob/main/docs/runs/6D-RUN.md)
(`85c9eb6`, `02261c4`) — K1, K3 and K4. Follows [R91](2026-09-04-6d-supervisor-ruling-R91.md), which
countersigned the fifteenth and sixteenth from the same round.

## Verification, done here rather than accepted

- **[Observed]** `registry.py:4430` — `if holder is not None and not same_word(holder, left.name):` — the
  `alias_collision` escape K1 names.
- **[Observed]** `registry.py:7137` — `if self.caps.indexes_membership:` — the capability guard on refusal
  #1 that K4 names.
- **[Observed]** `grep -c "reversed(\|shuffle\|itertools.permutations" docs/tools/check_merge_guard.py`
  → **0**. The gate has no page-order control.
- **[Observed]** `self._identity_breach(` is called at `registry.py` **3092, 3219, 3247, 4312, 7175** —
  exactly the five sites T9 counted.
- **Two claims the supervisor could NOT confirm by code-read, stated as such.** (i) The record says
  `_alias_clash` returns the **first** holder at `registry.py:7441`; a grep for `return` in 7436–7446
  found nothing on those lines, so the return is elsewhere or worded differently — **the 120-permutation
  sweep (60 swallowed / 60 refused, re-run by the worker) is the evidence and it stands.** (ii) The record
  says `DegradedAdapter(indexes_membership=False)` appears **0** times *as a leg*; the supervisor's count
  of the string `indexes_membership=False` in the gate is **4**. The narrower "never as a leg" claim is
  neither confirmed nor refuted by that count. **K4's behavioural evidence — refused non-overridably on
  sqlite, written with `warnings=()` on the degraded adapter, `resolve_type` at 1.0 — does not depend on
  it.** The worker should reconcile the 4 in §6.4's gate reason.

## R92, part one: three more trips, and each is a NEW SENTENCE rather than a new door

The kill-row criterion is identity: ordinary calls at shipped doors leaving two rows answering to one
word. All three reach it, and each says something the fourteen records had not.

**K1 — the SEVENTEENTH trip: a non-overridable identity guard's answer is a function of SORT ORDER.**
`merge_types`' `alias_collision` escapes on `not same_word(holder, left.name)` while `_alias_clash`
returns one holder in page order, so a live row that is another legal spelling of `left.name` fires the
escape and the genuine third holder behind it is never seen. **60 of 120 page orders swallow the guard**;
two ACTIVE rows then answer to one word; `resolve_type` answers at 1.0; the same pair asked directly is
refused `predicate_merge` non-overridably. Reproduced on the async mirror and both paging doubles. **This
is R80's first discharge achieved** — ruling R80 said *construct the state, or prove the doors refuse it* —
and Q82, the register's only carried-forward suspicion, is now a state. On the acknowledgement caveat the
record honestly carries: the merge door requires acknowledgements on the *specified* path (they are not
`force`), and **the escape under test needs none**; the caveat is recorded and does not change the
classification. Gate reason: zero page-order controls — R58's own class, *a guard never reads a page*,
arriving at the file built to enumerate these guards.

**K3 — the EIGHTEENTH trip: the FIFTH trip's operand, un-applied to a guard added by the THIRTEENTH's
fix.** `merge_types` binds `clash_why` and never uses it (**[Observed, worker-verified]** one occurrence,
the binding; `alias_check_incomplete` zero), so behind `page_cap=3` a truncated look reads as *the words
are free*, silently, and the merge proceeds to **two live holders and 1.0**. The fix auditor stopped this
at MAJOR (*byte-identical warnings*); the kill row chained it to the collapse and the escalation to
BLOCKING is accepted — F3 showed the caller cannot tell, K3 shows what it costs. Trip 5 closed *partial is
not equal* at `_extent`'s three callers; `_alias_clash` did not exist then (added at `e5540ff`), and its
`why` was never wired. **Rule (d) by number, and R84's clause in its purest form** — a guard added later
inherited the rule's exemption, not the rule.

**K4 — the NINETEENTH trip: *unknowable* treated as *nothing to say*, on UC1's own declared shape.**
`_alias_identity_breach` appends refusal #1 only `if self.caps.indexes_membership`; on a backend declaring
it `False` the guard is skipped and **the caller is told nothing** — the shipped comment at 7158 names the
residual as Q69 *in the docstring*. Five ordinary calls on two backends: sqlite refuses
`different_consumer_sets` non-overridably; the degraded adapter writes the alias with `warnings=()`, and
`resolve_type('ent_a')` answers `ent_b` at 1.0 while `ent_a` is a live row with consumers. Trips 1 and 9
asked whether *unknowable* equals *equal* or *different*; **this asks whether *unknowable* equals *nothing
to say*, and the shipped answer is yes.** It is the FIRST trip's backend shape, which is why it matters.

**All three are countersigned as trips. The count is NINETEEN.**

## R92, part two: what the count means now, said plainly

Row 6d's round 1 produced **five** trips — fifteenth through nineteenth. That is more than any round in
the register's history, and the founder is owed it without softening. Three facts sit beside it:

1. **Every one was reached on shipped code that no build row had changed** — **[Observed]**
   `git diff --stat d4b86a8 HEAD -- ontoloche/` is empty. These are not regressions of this row; they are
   what the identity surface already held.
2. **Four of five were predicted before the lens ran** — T14 (fifteenth), T11 (sixteenth), S2
   (seventeenth), T1 (nineteenth) — and the fifth, K3, is T5's cell reached one guard further than T5
   named. §0.7 scores **21 CONFIRMED · 3 PARTIAL · 1 FALSIFIED · 5 NOT PROBED** of thirty.
3. **They cost one round of a row with no diff of its own.** The alternative was the next four build rows
   each paying for the cells they happened to touch, one at a time, as trips 8/12/13/14 were paid for.

## R92, part three: the scoring and the adjudications are countersigned

§6.5's table is adopted. Three adjudications the worker made **against** the row are the reason the
table can be trusted, and they are singled out: **T7 falsified** (the `_word_spellings` residual is closed
by the very call site above it — and the docstring still states it, which is recorded as a Cause-B hazard
rather than fixed); **T3's harm at D6 falsified** (`reinstate` is the victim in every construction, never
the door — the enumeration gap stands, the predicted harm does not); **T12 half-falsified** (`approve`
already has `already_decided`). And one adjudication the worker made **for** the row over a lens's
objection: **S4 stands CONFIRMED**, because the kill row's `kind="action"` sweep drove word-identity
constructions and §6.2's A3 is a *declaration* collapse the predicate control refuses non-overridably —
the lens did not run A3's construction because its own brief excluded the ACTIONS layer, so its negative
could not reach the finding that decides the prediction. Overruling a lens on evidence and keeping the
overruled negative on the record is the standard, and it was met.

**K7 is the round's one UNPREDICTED finding and it was found twice** — `merge_types`, `retire` and
`reinstate` raise `AmbiguousKind` on a store `PACKAGE.md` §4.1 blesses, because `_require` is called with
no `kind=`; trip 8's fourth defect at three doors the fix did not reach. Not a trip (a raise, not a
second row), MAJOR, rule (d) by number, and §0.7 said in advance that an unpredicted finding is the most
valuable thing a lens can return. Noted so it is not lost under the trips.

## What the fix set must be — three changes, not one and not nineteen

1. **The 2×2×2** (fifteenth, sixteenth, and K6's cross-kind cell) — **one change**, one mutation per
   cell, per R91.
2. **The page-order and truncation family** (seventeenth, eighteenth) — **one change**: `_alias_clash`
   returns the SET or answers `unknowable`, and its `why` is consumed at every caller; the gate gains a
   page-order axis (every fixture driven in at least two orders) — the countable form of "done" is the
   `reversed(|shuffle|permutations` grep going from 0 to a number.
3. **The capability-degraded skip** (nineteenth) — **one change**: a skipped guard emits a stated
   warning naming the skip, per T1's own falsifier; and the gate gains `DegradedAdapter` as a leg, with
   §6.4's "0 as a leg" reconciled against the 4 occurrences the supervisor counted.
4. **A3 separate** (R91). **`_search_namespaces` separate** (R90). **K7 and F5 with whichever change
   touches their door**, each named.
5. Every fix commit **enumerates the doors its rule binds and lists what it declined** (R85, R88).

## R92, part four: `stop` is put for the THIRTEENTH time

Five trips in one round oblige it. **Recommendation: continue — and this time the argument needs no
rhetoric.** Nineteen trips, none in a real merge, every one of this round's five on code no build row had
touched, four of five named in writing before the lens ran, all five closable in three changes over a
surface with no diff of its own to distract the lenses. The register has never had a round it understood
this well. **The founder rules.** This put folds into the pending founder item with R91's; one decision,
not two.

## Unchanged

Q56 remains the class-closing question for the read side and the founder's. Q94 (governance identity)
stands as minted in R91. Standing rules (a)–(e) stand. The `INGEST` build row is not open. Beacon's pin is
unaffected until the fix set lands; the supervisor re-checks it then.

Next ruling number: **R93**. Next question number: **Q95**.
