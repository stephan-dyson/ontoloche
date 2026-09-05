# R94 — the TWENTY-THIRD trip: `reinstate` is the fourth door and the one the rule was never wired to; a round-1 grade is withdrawn; two of the actions-twin's BLOCKINGs are the row's own; and `stop` is put for the fifteenth time

**Ruled 2026-09-05 by the ontoloche program supervisor**, countersigning the one construction
row 6d's round 3 routed at [`6D-RUN.md` §6.19](https://github.com/stephan-dyson/ontoloche/blob/main/docs/runs/6D-RUN.md)
(`cabff4b`, lenses 2 and 3 to disk before any fix). Follows
[R93](2026-09-05-6d-supervisor-ruling-R93.md) and its erratum (`20c1cf6`).

## Verification, done here rather than accepted

- **[Observed]** `_retired_holder` is called at `ontoloche/registry.py:3589` (`retire`), `:4849`
  (`merge_types`) and `:5510` (`import_types`) and **nowhere inside `reinstate`** (`3854`–`4136`: no
  `_retired_holder`, no `word_held_by_tombstone`, no `same_word`).
- **[Observed]** `word_held_by_tombstone` is emitted at `registry.py:3597`, `:4855`, `:5528` — three
  doors. In `docs/tools/check_merge_guard.py` it occurs **once, at line 2991, inside a comment.**
- **[Observed]** The supervisor **rebuilt the construction independently** (sqlite `:memory:`, `Registry`
  with a default `NamespacePolicy`, ordinary §5 calls, no `force`, no adapter write):

  ```
  1 import alpha[zeta]       -> TypeEntry alpha active   aliases=('zeta',)
  2 import beta              -> TypeEntry beta  active
  3 retire alpha succ=beta   -> TypeEntry alpha retired  aliases=('zeta',) warnings=('aliases_transferred:beta',)
  4 retire beta              -> TypeEntry beta  retired  aliases=('zeta',)
  CONTROL import gamma[zeta] -> TypeEntry gamma proposed warnings=('import_refused:word_held_by_tombstone',)
  5 reinstate alpha          -> TypeEntry alpha ACTIVE   aliases=('zeta',) warnings=()
  6 resolve zeta             -> outcome='existing' type=alpha confidence=1.0
  7 reinstate beta           -> Refusal 'alias_collision'
  ```

  Identical to §6.19's record in every value that matters.
- **[Observed]** `git log -S'mine.get(key) != theirs.get(key)' -- ontoloche/registry.py` → `304967a`
  alone: the `effects`-order comparison was **added by this row's A3 fix**.
- **[Observed]** `registry.py:5401`: `named, _named_why = self._word_rows(namespace, word)` — the why is
  bound and never read. Three of six `_word_rows` call sites drop it (`5212`, `5401`, `7608`); change A's
  consumer table (`8d717c9`) does not list `5401`.
- **[Observed]** `cabff4b` is docs-only (`6D-RUN.md` +172, zero product or tool files) and the tree was
  clean at the time of this ruling — verdicts to disk before any fix, as the brief requires.

## R94, part one: K1 is the TWENTY-THIRD trip

Two rows answer to one word at a shipped door through ordinary calls: after step 5 the live row `alpha`
answers to `zeta` at **1.0** while the tombstone `beta` still holds `zeta`, and the three doors that were
wired refuse the identical act `word_held_by_tombstone` in the same store. Step 7 is the harm
`INTERFACE.md` §5.12 names in its own words — the tombstone becomes **permanently un-reinstatable**,
which is the governance act ruling R11 created `reinstate` to provide. **Countersigned. The count is
TWENTY-THREE.**

Its lineage is the tombstone family: the eighth trip minted `name_previously_retired`; the fifteenth
and sixteenth minted `word_held_by_tombstone` (row 6d's change 1, `9a4e140`); the twentieth and
twenty-first found that value's consumers unwalked. This one is the same reading one door further:
**`reinstate` is the fourth door that makes a word answer at 1.0, and the one `9a4e140` did not walk
to.** The behaviour is **pre-existing** at `d4b86a8` — every door was silent then — and the
**contradiction** (three doors refuse, one does not) is the row's own, made by the row's own fix.
That is R93's adopted reading — *a widened matcher is a minted rule and its consumers are its doors* —
confirmed again at a rule this row minted itself, and it is a standing-rule-(d) failure by number:
`9a4e140` enumerated three doors where the surface has four.

## R94, part two: a round-1 grade is withdrawn, and R93 loses one of its three falsifications

Round 1 graded T3's predicted harm at D6 **FALSIFIED** — *"in every construction `reinstate` is the
victim, never the door"* — and §6.13 counted that among three clean falsifications offered as evidence
the loop is trustworthy. **The grade was taken before the rule was minted:** round 1 asked whether
`reinstate` creates a second *live* holder (it does not; `C9-23` pins that correctly), and the
*tombstone*-holder question did not exist as a value until `9a4e140`, which shipped after the grade.
The worker withdraws the grade rather than leaving it standing; **the supervisor accepts the
withdrawal and records the consequence against its own R93:** part four of R93 leaned on three
falsifications; it now has two. A record that withdraws its own good news is the record this row was
opened to produce.

## R94, part three: the actions-twin's BLOCKINGs are NOT trips, and two of three are the row's own

- **The `effects`-order false refusal (A7/A8/G5/K4)** is not a pre-existing hole the row stood beside:
  **[Observed]** `304967a` made it. `ACTIONS.md` settles the semantics against the row three times
  (§2.5, §3.3, §1) and the package already implements the correct comparison at
  `actions.py:585 effect_identity`. This is **governance identity** — one word, one identity, two
  policies — and stays in **Q94's** register (A9), not the kill row. It is a defect the row's own fix
  introduced, and it is the most urgent of what remains because it **closes a legal operation**.
- **`registry.py:5401` drops `_word_rows`' why.** A legal truncating backend turns *"we could not look"*
  into *"no divergence"*, the guard is skipped and the alias is written — A3's own harm with A3's fix
  live. This is the **`I-1` truncated cell** at a site change A's consumer table did not enumerate:
  a rule-(d) miss on the *other* axis (the widening made the scan larger and an incomplete page more
  likely at the one site that reads incompleteness as agreement). **Not a trip**; counted as the
  instance-surface cell it is.
- **G2 is worse than "zero fixtures"**: `grep -c 'kind="action"'` → 1 and the hit is a comment asserting
  zero; the three A3 ids drive `effects=[]` on both sides, so cutting `_GOVERNANCE_KEYS` to two keys
  leaves the suite identical to baseline. Harness, not product; R3-P5's reading.

The actions lens **declined the escalation its own brief offered** — the `effects` order is
caller-controlled, all 24 page orders identical — and said so against the brief. The record shows the
pressure was applied and refused; that is what a lens is for.

## R94, part four: round 3's predictions so far

R3-P2, R3-P3, R3-P5, R3-P6, R3-P8 **CONFIRMED**; R3-P9 **PARTIAL** (its "shown unnecessary" branch
falsified). R3-P4 — the worker's prediction against its own last commit — rides on the accumulator lens,
still running at this ruling. R3-P6 confirmed means a published number was wrong for the **third round
running**; the worker's own diagnosis stands: *not re-deriving LAST*, not failing to re-derive.

## What the round-3 fix set must be

The cap round's fix set, in this order, one change per family, the commit enumerating every door and
listing what it declined (R85, R88), **every published number re-derived by its defining command as the
LAST act before the commit is written**:

1. **`reinstate` gains the `_retired_holder` check** (the twenty-third) — and the commit enumerates all
   **four** doors that make a word answer at 1.0, with the gate gaining a fixture that drives it.
2. **G1's cross-namespace axis and G2's `kind="action"` fixtures** land in `check_merge_guard.py`, so
   MX10 and the `_GOVERNANCE_KEYS` cut both go RED.
3. **The `effects` comparison unified on `effect_identity`** — the row removes the defect it made.
4. **`5401` carries its why** (Rule U at the axis), and change A's consumer table is amended to list it.

Then the convergence note (every prediction of every round scored; the register at twenty-three; the
withdrawn grade recorded), then the landing.

## R94, part five: `stop` is put for the FIFTEENTH time

A trip obliges it. **Recommendation: continue to the row's own end and no further.** Round 3 is the
cap the brief set; what remains is its fix set, the convergence note and the landing. Twenty-three
trips, none in a real merge; this one at a door the row's own fix should have walked to, found by the
row's own kill-row lens one round later. The founder rules; this put folds into the pending founder
item with the twelfth, thirteenth and fourteenth.

## Unchanged

Q56, Q94 and Q95 remain the founder's. Standing rules (a)–(e) stand. The `INGEST` build row is not open.
Beacon's pin `802ddf02…` is **[Observed]** still an ancestor; the one storage-contract touch since R93 is
`4f8db52`'s additive `Refusal.warnings` (relayed).

Next ruling number: **R95**. Next question number: **Q97**.
