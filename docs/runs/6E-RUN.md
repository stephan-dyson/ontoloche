# 6E-RUN — THE REGISTER AUDIT

Opened by founder ruling [R96](../decisions/2026-09-07-founder-ruling-R96.md), his word: *"audit."*
Worker: row 6e (Opus). Supervisor: ontoloche program supervisor, tmux `fleet-supervisor-ontoloche` pane `%2`.

**The question, fixed by R96 clause 4 and not restatable by me:**

> Are the twenty-three kill-row trips twenty-three implementation defects, or ONE design defect found
> twenty-three times?

---

## §0 — PRE-REGISTRATION

**This section is committed BEFORE any analytic reading of the twenty-three trips.** `git log` is the only
artefact that can prove that ordering, because a pre-registration and a post-hoc rationalisation are
textually identical. If this section's commit is not an ancestor of every classification commit in this
document's history, the audit is a confirmation and should be read as worthless whatever it concludes.

### §0.1 — Prior exposure, disclosed

A pre-registration that hides what its author had already read is not one. Before writing this section I had
read, in this order and no more:

1. My brief (`C:\Users\steph\.claude\fleet-supervisor\briefs\2026-09-07-oo-6e-register-audit.md`).
2. [`R96`](../decisions/2026-09-07-founder-ruling-R96.md), [`R97`](../decisions/2026-09-07-founder-ruling-R97.md),
   [`R98`](../decisions/2026-09-07-founder-ruling-R98.md), and
   [the governance register](../decisions/2026-09-07-governance-register.md) — all four in full.
3. `ROADMAP.md` § *Kill criteria*: the criterion's verbatim wording, and the opening of the kill-table cell's
   running narrative — **including its own re-framing at the second trip, which says in the ROADMAP's own
   words that calling it "implementation defect, not design" twice would file "two unrelated bugs where
   there is one design defect found twice."** I read that before forming my hypothesis and it moved my
   hypothesis. Recording that here rather than presenting the hypothesis as naive.
4. The **section headings only** of the kill-row register
   ([`2026-08-29-3c-rulings-R6-R12.md`](../decisions/2026-08-29-3c-rulings-R6-R12.md), 849 lines) — enough
   to know there are twenty-three trips over rows 3c, 4c, 4d, 6b, 6c and 6d, plus a separate uncounted
   `I-1`…`I-8` instance-surface series.
5. **Trips 1, 2 and 3 in full** (lines 37–64), read to learn what fields the record actually carries so that
   §0.3's criteria could be written against real fields rather than invented ones. This is prior exposure to
   three of the twenty-three and it is disclosed as such; those three are also the three that most obviously
   support my hypothesis, which is a reason to distrust it, not to trust it.

I have **not** read trips 4–23, `6D-RUN.md`, `7A-RUN.md` or `INGEST.md` at the time of this commit.

### §0.2 — Hypothesis, stated plainly

**I expect the answer to be: NOT twenty-three implementation defects.**

More precisely, I expect the twenty-three to collapse onto a **small number of recurring generative
statements** — my central expectation is **two to four**, with one of them covering the largest share — and
I expect at least one of those statements to be a property of the **merge-centred identity design** rather
than of any single guard's code.

The reasoning behind the expectation, so it can be attacked: the register's own contemporaneous language
already links trips across rows before anyone tried to ("the second hole in the same guard expression in
24 hours"; trip 3 "widens the second trip's, rather than repeating it"; trip 13 titled "the TWELFTH's class
at the sibling caller"; trip 23 titled "the fourth door, and the one the rule was never wired to"). Twenty-
three genuinely independent defects would not have produced that vocabulary twenty-three times.

**The bias this creates, named so §0.4 can be aimed at it:** I am the row whose stated purpose is to be able
to return an answer that costs the project, opened by a founder who chose `audit` over `continue`. The
socially rewarded finding is a design defect. An audit that finds what it was convened to find is worth
nothing, so the falsifier below is written to be *easy to trip*, not hard.

### §0.3 — Classification criteria, fixed here and not revisable after analysis begins

**Every one of the twenty-three gets an entry. None is skipped as obvious**, including the ones whose
classification I predict in §0.5. If a criterion below turns out to be unworkable mid-analysis, I do not
silently replace it: I record the failure, the trip that broke it, and the amendment, in a commit of its
own, so the change is visible in `git log` as an amendment rather than as the original.

**Per-trip record — seven fields, the same seven for all twenty-three:**

| # | Field | What it holds |
|---|---|---|
| 1 | **Door(s)** | Which call(s) the defect was reachable at (`merge_types`, `retire(successor=)`, `import_types`, `reinstate`, `resolve_type`, `preflight`, …) |
| 2 | **Guard expression** | The specific predicate/comparison/scan that failed, quoted or named |
| 3 | **Fix shape** | Exactly one of the fixed taxonomy below (F1–F6) |
| 4 | **Contract ids pinned** | The `Cnn-nn` ids the fix added, or none |
| 5 | **Contemporaneous link** | Did the register, *at the time*, call this the same class as an earlier trip? Verbatim quote, or "none" |
| 6 | **Pre-emption test** | Is there an earlier trip `E` whose fix, had it been applied at the altitude `E`'s own commit claimed to be fixing at, would have pre-empted this trip? **YES/NO + the evidence.** This is the load-bearing discriminator |
| 7 | **Generative statement** | One sentence naming the underlying wrongness, written to a fixed template (below) so that two trips' statements can be compared as strings rather than as impressions |

**Fix-shape taxonomy (F1–F6), fixed:** F1 narrow a comparison; F2 add an existing guard to another caller;
F3 widen a matcher or a scan; F4 add a contract id / test only; F5 change an API shape; F6 spec or doc
amendment only.

**Generative-statement template, fixed:** *"A `<mechanism>` treats `<X>` as `<Y>`, at `<scope>`."* Two trips
share a generative statement only when all three slots match. Partial matches are recorded as partial and
are **not** counted as recurrences.

**Each trip is classified into exactly one of three classes:**

- **`I` — independent implementation defect.** Field 6 is NO, and its generative statement is not an
  instance of any earlier trip's.
- **`R` — recurrence.** An earlier trip's generative statement covers it; the earlier fix was applied at a
  narrower scope than the defect actually existed at.
- **`D` — design defect.** Its generative statement is a property of the **shape** — the merge-centred
  identity model, in which more than one call may change what a name resolves to — rather than of any one
  guard's code, such that no local fix at any altitude removes it.

**The `D` bar is deliberately high, and this is the anti-bias clause.** A generative statement that names a
comparison, a caller list, or a matcher's width is an **implementation** property and classifies as `I` or
`R` **even when it recurs twenty times**. "One implementation defect found twenty-three times" is a real and
different verdict from "one design defect found twenty-three times", it is weaker, and under `ROADMAP.md`'s
criterion it does **not** license `stop`. I pre-commit to reporting the weaker verdict if that is what the
statements say.

### §0.4 — Falsifiers

**Primary falsifier (kills my hypothesis).** If, across the twenty-three, **eight or fewer** classify as `R`
or `D` — that is, if sixteen or more trips answer NO at field 6 and carry generative statements that no
earlier trip's statement covers — then the answer is **twenty-three implementation defects**, the register's
twenty-three individual judgments were right in series as well as one at a time, and I report that. This
number is fixed now and is not adjustable afterwards.

**Secondary falsifier (kills the `stop`-licensing half specifically).** If recurrence is high but **every**
recurring generative statement fills the `<mechanism>` slot with a guard-implementation property, then `D`
is empty, the verdict is "one implementation defect found N times", and **`stop` does not fire on my
finding**. Recurrence alone is not design.

**Decision rule for the middle outcome, fixed in advance so it cannot be rounded either way later:** if the
trips resolve into 2–4 generative statements each covering three or more trips, that is **not** "twenty-
three implementation defects" and I will not report it as such; it is reported as *N recurring defects*,
with each one's class (`I`/`R`/`D`) stated separately, and the `stop` consequence attaching only to those
that reach `D`.

**What I do NOT get to change.** The count stays **TWENTY-THREE** whatever the classification says — this
row audits what the twenty-three mean, not how many there are (R96 § *Counts and numbering*). I record no
sixteenth `stop` decline; the fifteenth put stands open. Any harm my analysis reaches is **routed to the
supervisor, never self-classified**.

### §0.5 — Prediction: which trips will be hardest to classify

Recorded now so that a trip I later find easy cannot be quietly reclassified as one I always expected to be
easy, and so that agreeing with the register on the hard ones is visibly a choice.

1. **Trips 6 and 7** — the register itself titles them *"different in kind"* and *"a third kind"*. These are
   hardest because **agreeing with that claim is free and disagreeing is expensive**, which is exactly the
   asymmetry an audit exists to correct. Field 7's fixed template is aimed at these two.
2. **Trips 20, 21, 22** — all three recorded **PRE-EXISTING**, found by a new lens, with the register noting
   *"the counted policy inverts"*. A pre-existing defect newly made visible is genuinely ambiguous between a
   new finding and an old one, and the count's meaning turns on which it is.
3. **Trips 15 and 16** — **predicted before the lens ran.** A defect predictable in advance is prima facie
   evidence of a generative statement already known, but predicting it may also be ordinary competence; the
   two readings need separating on evidence rather than on which is more flattering.
4. **Trip 23** — `reinstate` as *"the fourth door, and the one the rule was never wired to"*. My prediction
   is that this classifies `R` against trip 3, and the difficulty is resisting how neatly it fits.
5. **Trips 17, 18, 19** — three trips from one lens in one round. Whether that is three defects or one lens
   finding one thing three times is the whole audit's question in miniature, at a scale small enough to get
   wrong quickly.

I predict trips 1–5 and 8–11 will be the easiest, and I predict I will be tempted to spend least effort on
them. Every one still gets a full seven-field entry.

### §0.6 — The two carried questions, and their scope

Both are answered in this document, after the classification, in their own sections.

**(a) The criterion's silent widening (from [R97](../decisions/2026-09-07-founder-ruling-R97.md)).**
`ROADMAP.md` writes the criterion as *"a capability predicate gets merged as a duplicate."* The register has
been reading it as *"two things answering to one identity"* (`7A-RUN.md:202`, `INGEST.md:364`). **That
widening was never ruled — it happened in practice.** To answer: **when** the reading widened, **by what
commit**, and whether the count still means one thing. Pre-registered method: the widening is dated by
`git log -S` on the widened phrasing, not by reading for it — the date is a derived number and §0.7 governs
it.

**(b) The construction routed to me by [R98](../decisions/2026-09-07-founder-ruling-R98.md) — verify or
KILL.** The supervisor's own, unadopted: *warn on the write when a tombstone answers to the word*. **Its
falsifier is R98's, verbatim, and I do not get to restate it in easier terms:** *if a warning cannot be
emitted at that write without also refusing a `C12-09`-blessed write, the idea is dead and the residual
stays silent.* I return a verdict, not a patch. **Killing it is a fully acceptable result.** I write no
product code to reach that verdict; a read-only analysis script under `docs/tools/` is permitted if a number
needs deriving, and a script that mutates a store is out of scope.

### §0.7 — Numbers

**Every published number in this document is re-derived by its defining command LAST**, after the prose is
written, and the command is printed in the document beside the number. This project has four recorded
instances of a number in prose that the code did not derive. Numbers appearing in §0 above — 23 trips, 849
lines, 8-or-fewer for the primary falsifier — are either fixed by ruling or are thresholds I am setting, not
derived measurements, and are marked as such by being here.

### §0.8 — State at pre-registration

| Fact | Value |
|---|---|
| `main` locally | `ac163d6` |
| `origin/main` | `655f515` |
| Push | **BLOCKED (403)** — wrong active `gh` account; commits are local-only and **nothing in this row is landed** |
| Kill-row count | **TWENTY-THREE** (unchanged by this row) |
| Governance register | **ONE** (A3, BLOCKING, open) |
| `stop` | **HELD OPEN** at the fifteenth put — not declined, and this row records no sixteenth decline |
| Next ruling | **R99** |

---

## §1 — Method as executed, and the one place §0 needed interpreting

All twenty-three trips were read from
[`2026-08-29-3c-rulings-R6-R12.md`](../decisions/2026-08-29-3c-rulings-R6-R12.md), in order, after
`9dc994d`. Each got the seven fields §0.3 fixed. Nothing in §0 was amended.

**The one interpretation, recorded rather than made silently.** §0.3 says two trips share a generative
statement *"only when all three slots match"*, and separately defines class `R` as *"an earlier trip's
generative statement **covers** it."* Those are two different tests and the analysis needs both, so the
reading is stated: **slot-identity** means the same defect twice; **coverage** means the earlier trip's
statement, *at the altitude that trip's own commit claimed*, entails the later trip. The `<scope>` slot is
precisely where the narrowing happens in this register, so requiring slot-identity for `R` would classify
every incomplete application as independent — which is the answer the register already gave twenty-three
times, and adopting it by definition would decide the audit rather than perform it. Coverage governs `R`;
slot-identity is reported alongside it. No trip's class turns on the difference without being flagged.

### The six generative statements

Each is written to §0.3's template. They are numbered in the order the register minted them.

| | statement | minted at |
|---|---|---|
| **A** | A **comparison** treats **a non-answer** as **an answer**, at **the guard that compares** | trip 1 |
| **B** | A **guard** treats **one call site** as **every call that can change the guarded fact**, at **the caller set** | trip 3 |
| **C** | A **guard** treats **a permission the state does not consume** as **spent**, at **a row's words** | trip 12 |
| **D** | A **guard** treats **a byte comparison** as **the resolver's normalised key**, at **the identity of the name** | trip 7 |
| **E** | The **registry** treats **a fact checked at WRITE time** as **true at READ time**, at **`resolve_type`'s §5.3 guarantee of 1.0** | trip 6 |
| **F** | A **non-overridable answer** treats **page order** as **immaterial**, at **the holder scan** | trip 17 |

---

## §2 — The twenty-three entries

Format per trip: **door(s) · guard expression · fix shape · ids · contemporaneous link · pre-emption test
(field 6) · statement · class.** Fix shapes are §0.3's taxonomy F1–F6.

**1 — 3c round 9, `0e89037`.** `merge_types` · refusal #2's extent comparison on
`indexes_membership=False` · **F1** · `C9-08` · link: none, it is the first · **field 6: N/A** ·
**statement A** (unknowable → equal) · **class `I`** — mints A.

**2 — #6 round 2, `fcb05b3`.** `merge_types` · guard 2's byte-identical test; two EMPTY extents are
byte-identical · **F1** · `C10-09` · link: *"the second hole in the same guard expression in 24 hours"*,
and `ROADMAP.md`'s own cell says calling it implementation twice files *"two unrelated bugs where there is
one design defect found twice"* · **field 6: YES** — trip 1's commit claimed Rule U (*"an extent that could
not be computed is not a byte-identical extent"*); *no evidence of membership is not evidence of identical
membership* is the same rule at the other end of one expression · **statement A** · **class `R`**.

**3 — #6 round 3, `05b8e04`.** `retire(successor=)` · §5.10's identity guards absent from a second caller
that re-points what a name resolves to · **F2** · `C9-18` · link: *"widens the second trip's, rather than
repeating it"* · **field 6: NO** — trips 1 and 2 fixed one expression inside `merge_types` and claimed no
altitude above that call · **statement B** (mints) · **class `I`**.

**4 — row 4c, `8e641e6`.** `import_types` (the `aliases` field) · `alias_collision` asks about *live*
holders, so a retired name that still resolves is invisible · **F2** · `C12-08`, `C12-09`, `C9-19` ·
link: *"the diagnosis widens a third time… a guard written for ONE CALL, over a fact that MORE THAN ONE
CALL can change, reached through MORE THAN ONE FIELD"* · **field 6: YES** — trip 3's commit claimed exactly
that altitude and named *"any other call that changes what a name resolves to"* as the checker's
obligation · **statement B** · **class `R`**.

**5 — row 4c round 1, `3a1d38b`/`9935823`.** `merge_types`, `retire`, `import_types` · all three callers
took `set(self._extent(...)[0])` and discarded the `why` saying the read was partial · **F1** · `C10-11` ·
link: *"This is Rule U's third operand on one expression"* · **field 6: YES** against trips 1–2 · statement
**A** (partial → equal) · **class `R`**.

**6 — row 4c round 3, `a3f9e6e`.** four doors · every identity guard compares at **write** time;
`resolve_type` grants 1.0 at **read** time, and four things move in between · **F1+F2** · `C10-13`, `C9-20` ·
link: the register's own *"different in kind"* — *"the guard looked correctly, and then the fact changed"* ·
**field 6: NO** · **statement E** (mints) · **class `D` — see §3.2.** The register agrees the class is not
closed by the fix and names the closing question **Q56**: *should an identity claim be verified where it is
MADE (at `resolve_type`'s 1.0) rather than only where it is WRITTEN?* — *"a change to a shipped guarantee,
and it belongs to the founder."*

**7 — row 4d round 1, `0f1d647`/`87aac1e`/`843af71`.** `import_types` alias door vs `DeterministicResolver`
· guards compare `rec.name == alias` by byte; the resolver scores `_norm(candidate)` — `'Commentable'` is a
word the guards never heard of and the resolver rates 1.0 · **F3** · `C10-15`, `C9-22`, `C4-12`, `C9-23`,
`C12-12` · link: the register's own *"a third kind"* · **field 6: NO** · **statement D** (mints) ·
**class `I`**.

**8 — row 4d round 3, `f06144c`/`fd919de`/`3f0c2f3`.** the **name** door (`propose_type`, `import_types`)
· `identity_key` was published at trip 7 and reached five callers of six; the retired half of the name door
was never keyed · **F2** · `C10-19`, `C4-14` · link: the register's own *"the seventh trip alive at HEAD
rather than a new class"*, and *"a fix that publishes a shared key is only as good as its application"* ·
**field 6: YES** — trip 7's commit claimed *one* notion of the same word for the whole registry ·
**statement D**, applied incompletely (**B**) · **class `R`**.

**9 — row 6b round 1, `07ac4e7`/`ef87025`.** `import_types` · refusal #1 read the aliased-onto row to get
its consumer set, and `import_types` creates that row in the same call, so `get_type(...) or other` fell
back to `other` and compared the left against itself · **F1** · `C12-14`, `C12-15` · link: the register
extends Rule U's operand table — *"a row that does not exist has none to READ, and that is not the same as
having none"* · **field 6: YES** against trip 1 — a non-answer treated as an answer, at a new operand ·
**statement A** · **class `R`**.

**10 — row 6b round 2, `6fd065d`.** `import_types`, existing-row branch · trip 9's fix computed the
incoming set on **one branch of two**; the other read `_consumer_report` off the row the same call is about
to overwrite · **F1** · `C12-16` · link: *"one door disagreeing with itself"*, and the register calls it
the enumeration diagnosis *"applied to a FIX rather than to a guard"* · **field 6: YES** against trip 3 ·
**statement B** · **class `R`**.

**11 — row 6b round 3, `d985621`.** `retire(successor=)`, `reinstate`, `merge_types`, `import_types` ·
`declared_predicates` was passed at **one of four** call sites of `_alias_identity_breach` · **F2** ·
`C12-17`, `C19-71` · link: the register's own *"trips nine, ten and eleven are one defect found three
rounds apart — the operand absent, the operand on one branch of two, the operand at one call site of
four"* · **field 6: YES** against trip 3 · **statement B** · **class `R`**.

**12 — row 6c round 1, `3844f92`.** `retire(successor=)` · the call was guarded once for a permission the
state never consumes — §5.8 keeps a tombstone's words **by design**, so a repeat retirement cashes the same
permission again · **F1** · `C9-29`, `C9-30`, `C9-31` · link: the register distinguishes it explicitly from
9/10/11 · **field 6: NO** — no earlier statement reaches *across calls*; every earlier one holds per call ·
**statement C** (mints) · **class `I`**. First trip whose provenance was proved by **bisect**.

**13 — row 6c round 2, `e5540ff`.** `merge_types` · the identical unconsumed-permission write at the
sibling caller; §5.10's guards compare the two **operands** and never ask who holds the **words being
moved** · **F2** · `C10-20` · link: the section's own title, *"it is the TWELFTH's class at the sibling
caller"* · **field 6: YES** — trip 12's rule (*the write a call performs must be idempotent in the state
the guard read*) covers it; the fix was made per-caller for a per-row obligation · **statement C** ·
**class `R`**.

**14 — row 6c round 3, `2da0433`/`0c0c7f6`.** `propose_type`, `approve`, `import_types` (the **mint**
doors) · standing rule (c) was applied to the callers that **transfer** a tombstone's words and not to
those that **mint** one; no door asked *which rows answer to this word, by name or alias, whatever their
status* · **F3** · `C4-15`, `C5-13`, `C12-21` · link: *"the register gains no new rule, and that is the
finding: standing rule (c) already said this"* → **standing rule (d)** · **field 6: YES** against trips
12/13 · **statement C**, applied incompletely (**B**) · **class `R`**.

**15 — row 6d round 1, `aa6d2e5`.** all three mint doors, one kind along · `_word_rows` was called
`kind=`-scoped, so a retired `action` family's alias was minted as a `predicate` **name** · **F3** ·
(R91's 2×2×2) · link: *"two cells of ONE table… of which the fourteenth trip's fix drove exactly one cell"*
· **field 6: YES** against trip 14 · **statement B** · **class `R`**. **Predicted before the lens ran**
(T14, by cell).

**16 — row 6d round 1, `3126023`.** `import_types` alias write, `retire(successor=)` transfer,
`merge_types` word move · `_alias_identity_breach` calls `_word_rows(...)` with `match_aliases` **defaulted
`False`** — *the exact operand whose absence IS trip 14* — and discards the `why` · **F2** · (same 2×2×2) ·
link: as above · **field 6: YES** against trip 14, and the register says so in the same breath ·
**statement B** · **class `R`**. **Predicted before the lens ran** (T11, by address).

**17 — row 6d round 1, `85c9eb6`.** `merge_types` · `alias_collision` escapes on
`not same_word(holder, left.name)` while `_alias_clash` returns **one** holder in page order; **60 of 120
orders swallow it** · **F1** · (R92) · link: *"this is R80/Q82 — the register's only carried-forward
suspicion — CONSTRUCTED"* · **field 6: NO** — no earlier statement is about order · **statement F**
(mints) · **class `I`**.

**18 — row 6d round 1, `85c9eb6`.** `merge_types` · `clash_why` bound and never used; behind `page_cap=3` a
truncated look reads as *the words are free* · **F1** · (R92) · link: the register's own *"the FIFTH trip's
operand un-applied to a guard the THIRTEENTH's fix added… rule (d) by number"* · **field 6: YES** against
trip 5 · **statement A** · **class `R`**.

**19 — row 6d round 1, `85c9eb6`.** `_alias_identity_breach` on a declared-degraded backend · refusal #1 is
appended only `if self.caps.indexes_membership`, so declaring it `False` skips the guard and says nothing ·
**F1** · (R92; residual Q69) · link: *"Trips 1 and 9 asked whether unknowable equals equal or different;
this asks whether it equals nothing to say"* · **field 6: YES** against trip 1 · **statement A** ·
**class `R`**.

**20 — row 6d round 2, `6042547`.** `_write_approved` — *the door R40 forces every predicate down* ·
trip 8's `name_previously_retired` was applied at two mint doors and never here · **F2** · (R93) · link:
R93's *"a widened matcher is a minted rule, and its consumers are its doors"* · **field 6: YES** against
trip 8 · **statement B** · **class `R`**. **PRE-EXISTING** by bisect; the round's own fix commits *"stood
next to it and did not see it."*

**21 — row 6d round 2, `6042547`.** `import_types`' name door · the byte-identical **cross-kind** tombstone
is discarded, and `reinstate` takes no `kind`, so the tombstone is unreachable · **F2** · (R93) · link:
*"the 2×2×2 crossed with the eighth trip's own dimension"* · **field 6: YES** against trips 8/15 ·
**statement D**, incompletely applied (**B**) · **class `R`**. **PRE-EXISTING.**

**22 — row 6d round 2, `6042547`.** `merge_types`' escape · it identifies a row by its **word** where §4.1
permits two kinds to share one, so the escape excuses a **stranger** · **F1** · (R93; `C10-26` for the
sorted holders) · link: *"the seventeenth trip's guard crossed with the fifteenth's axis"* · **field 6:
YES** against trip 7 — one word is not one row, which is D's statement at the row rather than the string ·
**statement D** · **class `R`**. **PRE-EXISTING.**

**23 — row 6d round 3, `cabff4b`.** `reinstate` · `word_held_by_tombstone` was minted by this row's own
change 1 (`9a4e140`) and walked to **three of the four** doors that make a word answer at 1.0 · **F2** ·
(R94) · link: R94's own *"a rule-(d) failure by number"* · **field 6: YES** — against trip 14, whose rule
(d) is *a rule minted at the caller that prompted it is half-applied until the commit that mints it names
every other caller it binds* · **statement B** · **class `R`**.

---

## §3 — The answer

### §3.1 — The classification, against §0.4's fixed thresholds

| class | trips | n |
|---|---|---|
| **`I`** — independent implementation defect, mints a statement | 1, 3, 7, 12, 17 | **5** |
| **`R`** — recurrence of an earlier statement at a narrower scope | 2, 4, 5, 8, 9, 10, 11, 13, 14, 15, 16, 18, 19, 20, 21, 22, 23 | **17** |
| **`D`** — design defect | 6 | **1** |

**`R` + `D` = 18 of 23.** §0.4's primary falsifier fires at **eight or fewer**. It does not fire: my
hypothesis survives a test I fixed before reading, and it survives by ten.

Statement coverage, one primary statement per trip:

| statement | trips | n |
|---|---|---|
| **B** — one call site treated as every caller | 3, 4, 10, 11, 15, 16, 20, 23 | **8** |
| **A** — a non-answer treated as an answer | 1, 2, 5, 9, 18, 19 | **6** |
| **D** — a byte treated as the resolver's key | 7, 8, 21, 22 | **4** |
| **C** — an unconsumed permission treated as spent | 12, 13, 14 | **3** |
| **E** — a write-time fact treated as true at read time | 6 | **1** |
| **F** — page order treated as immaterial | 17 | **1** |

**Four statements cover three or more trips each.** That is exactly §0.4's pre-registered **middle
outcome**, and its rule binds: *this is not "twenty-three implementation defects" and I do not report it as
such.*

### §3.2 — The secondary falsifier, and the one statement that survives the `D` bar

§0.3 set the `D` bar high on purpose: a statement naming *a comparison*, *a caller list* or *a matcher's
width* is an implementation property and stays `I`/`R` **however often it recurs**. Applied without mercy:

- **A** names a comparison → implementation. **B** names a caller list → implementation. **D** names a
  matcher's width → implementation. **F** names a scan's order → implementation.
- **C** is the near miss and is worth its sentence: §5.8 keeps a tombstone's words **by design**, so the
  permission is a design property — but standing rule (c) *did* remove it with a local fix once the
  enumeration was complete. By my own bar that is implementation. **`C` classifies `R`/`I`, not `D`.**
- **E does not fall.** Its statement names neither a comparison, a caller list, a matcher nor an order: it
  names **when a guarantee is granted relative to when its fact is checked.** No local fix removes it. The
  register agrees, in its own words and repeatedly — the class-closing question is **Q56**, *"a change to a
  shipped guarantee,"* explicitly *"the founder's."* The **cheap half** shipped (warn at `resolve_type`
  when the extents disagree) and trips 12 and 13 proved it structurally blind to transferred words
  (**Q79**). The **expensive half** — refusing to answer — was never taken, because it changes the design.

So §0.4's secondary falsifier does **not** fire either: `D` is not empty.

### §3.3 — The finding, stated so it costs what it costs

**Neither of R96's two answers is the true one, and the pre-registered middle outcome is why I can say so
without having chosen it afterwards.** The twenty-three are:

> **four recurring implementation-defect families (A, B, C, D — eighteen of the twenty-three), one
> order-dependence singleton (F), and ONE design defect (E) which is the mechanism that delivers the harm
> in twenty-one of the twenty-three.**

The last clause is the audit's actual finding, and it is the one no single trip could show. Every family
A–D and F is a story about a **guard**. But a failed guard is only a kill-row trip when something then
**answers to the collapsed word at confidence 1.0**, which `INTERFACE.md` §5.3 calls a **guarantee**. That
delivery is E. **Sixteen of the register's eighteen trip sections record a 1.0 answer — trips 3 through 23,
twenty-one of the twenty-three; the only two that do not are trips 1 and 2, which predate `resolve_type`
entering the record at all** (derivation D2, §6).

The register counted the guards. It never counted the delivery, because every countersignature tested
*design* with one fixed question — *is `namespace` untouched, does `cross_namespace_merge` still refuse?* —
which appears **ten times** (D4) and which **R90 has already found to be two claims, one of them never
tested in six rulings**. A test that narrow cannot see E: `namespace` can be untouched in every trip while
the read-side guarantee is what makes each of them reach the harm.

**What follows from `D` being non-empty is not mine to decide.** Under `ROADMAP.md`'s criterion the honest
consequence of one design defect is that `stop` fires and the merge-centred shape goes back on the table.
**That is a construction reaching a harm, and this row does not self-classify it — it is routed to the
supervisor in §7.** What I assert is narrower and is evidenced above: **the answer to R96's question is not
"twenty-three implementation defects."**

**The counterweight, stated because an audit that only argues one way is not one.** Every trip was caught in
test, none in a real merge; two of the last five were **predicted in writing before the lens ran**; and E's
closing question has been open, named and visible since **trip 6** — this is a known unruled decision, not
a discovery. A founder may reasonably read E as *a design question already on the table* rather than *a
design defect*, and the difference between those two readings is a ruling, not a measurement.

### §3.4 — The §0.5 prediction scorecard, including the miss

| predicted hardest | what happened |
|---|---|
| trips **6 and 7** (agreeing with *"different in kind"* is free) | Correct that these were the hard ones, and the analysis **did not** simply agree: trip 7 is `I` as the register says, but trip 6 is **`D`**, a harder call than the register's own. |
| trips **20, 21, 22** (PRE-EXISTING) | All three `R`. The ambiguity resolved cleanly: pre-existing changes *whose* defect it is, not *what* it is. |
| trips **15, 16** (predicted before the lens ran) | Both `R`. Predictability was evidence of a known statement, exactly as suspected — both are trip 14's cells. |
| trip **23** (predicted `R` against trip 3) | `R`, **but against trip 14**, not trip 3 — rule (d), not the raw enumeration rule. **Recorded as a miss**: the class was right, the parent was wrong. |
| trips **17, 18, 19** (three from one lens) | **One `I` and two `R`** — 17 mints F; 18 and 19 are A. The miniature answered the way the whole did. |

---

## §4 — Question (a): the criterion's silent widening

**It widened twice, and only the second widening was ever written down.**

**Widening 1 — in practice, at trip 3, commit `05b8e04`, 2026-08-29, and never phrased.** `ROADMAP.md`'s
criterion is *"a capability predicate gets merged as a duplicate."* Trips 1 and 2 are literally that:
`merge_types`, a duplicate, a merge. **Trip 3 is a `retire(successor=)`** — no merge — counted as the same
trip because the effect is the same collapse. That is the criterion's trigger moving from *one call* to
*any call that changes what a name resolves to*, and it is the same commit that mints statement **B**. The
register never restated the criterion to match: **the phrase "answering to one identity" occurs ZERO times
in the kill-row register** (derivation D4). The reading widened by counting, not by writing.

**Widening 2 — phrased, at commit `b6cf860`, 2026-09-03, in `docs/runs/7A-RUN.md` (row 7a).** The sentence
*"`ROADMAP.md`'s kill criterion is two things answering to one identity"* first appears there and nowhere
earlier (derivation D6). It then propagated into `docs/specs/INGEST.md`. **It is attributed to
`ROADMAP.md`, and `ROADMAP.md` does not say it** — that document's cell says *"a capability predicate gets
merged as a duplicate"*, once (D4).

**Does the count still mean one thing? No — it means at least two, and the register has already acted on
that.** Trips 1–2 are the ROADMAP sentence. Trips 3–23 are the widened reading. `7A-RUN.md` and
`INGEST.md` use it a level lower still — *"that criterion one level below where the trips live"*, at
instance resolution — and **the project has already ruled that level out of the count**: R83 made the
`I-1`…`I-8` cells a separate series, and R97 has now made governance identity a third register. Both
rulings are the same corrective applied after the fact.

**The judgment R97 asked for.** This is the defect the project has recorded twenty-three times, committed
by its register: R93's *"a widened matcher is a minted rule, and its consumers are its doors"* — the
criterion is a matcher, it was widened at `05b8e04`, its consumers are every countersignature that quotes
the count, and **no commit enumerated them.** Rule (d) by number, at the register rather than at the code.
The mitigating fact, and it is real: **the widening made the criterion *better*, not looser in a
self-serving direction** — it caught twenty-one trips a merge-only reading would have missed. The harm is
not that the count grew wrongly; it is that **a number the founder is asked to read as one signal has been
produced under two definitions, and the switch is undated anywhere except in this section.**

**Recorded as a construction and routed, not classified: whether the count needs restating as `2 + 21`
under two definitions is a register decision, and §7 routes it.**

---

## §5 — Question (b): verdict on the construction R98 routed here

**VERDICT: VERIFIED CONSTRUCTIBLE. R98's falsifier is NOT met.** No product code was written; every claim
below is a read of shipped code at `ac163d6`, cited by line.

**The construction.** *Warn on the write when a tombstone answers to the word* — disclose the
un-reinstatable state created by the `C12-09`-blessed path at the moment it is created.

**R98's falsifier, verbatim and not restated in easier terms:** *if a warning cannot be emitted at that
write without also refusing a `C12-09`-blessed write, the idea is dead and the residual stays silent.*

**Why it is not met — four findings, each checkable.**

1. **The condition needs no scan, so it cannot collide with the scan that refuses.**
   `_retired_holder` (`ontoloche/registry.py:8233`) deliberately matches **aliases only** — its own comment
   says the name half is excluded because *"a tombstone's own NAME being written as an alias onto another
   row is the ordinary post-retirement succession `C12-09` blesses… refusing it here would reverse a
   narrowing this register pinned on purpose."* The residual's condition is **not** a scan result: it is a
   property of the write's own operands — *this call moves `left.name` onto a live row and leaves `left` a
   tombstone.* Nothing needs to be added to `_retired_holder`, so its aliases-only cut is untouched and no
   `C12-09`-blessed write changes its refusal status.

2. **`merge_types` already computes the exact set to warn about, and puts it in a detail field.** The
   escape at `registry.py:4874` is
   `blocking = tuple((n, k) for n, k in holders if not (n == left.name and k == left.kind))`, and the
   refusal detail carries **`"excused": [n for n, k in holders if n == left.name and k == left.kind]`**.
   The warning's subject is that `excused` set — *already computed, already named, and the complement of
   what the door refuses.* Warning on the carve-out cannot refuse the carve-out.

3. **Both doors already return a warnings channel and already populate it on the success path.**
   `MergeResult.warnings` exists (`ontoloche/types.py`) and the success return at `registry.py:5111` fills
   it with derived values (`definitions_similarity:…`, `definitions_uncertified`). `retire` returns a
   `TypeEntry`, which carries `warnings` and `with_warnings`, and already emits on success —
   `registry.py:3141` returns `retire_no_op:already_retired`. **No new mechanism is required**, which is
   what R98 predicted when it noted `Refusal.warnings` landed at `4f8db52`.

4. **The disclosure would be accurate, and the register has already proved the harm it names.** Trip 23's
   own construction ends *"`reinstate('beta')` refuses `alias_collision` non-overridably — the tombstone is
   **permanently un-reinstatable**, the harm §5.12 names."* That is the state the warning discloses.

**What I am NOT saying, and it is the honest limit of a read-only verdict.** I have not executed anything:
no probe, no suite, no mutation. `oo-pg` is `Exited(255)` and no three-leg suite has been run. **This
verdict is constructibility by code-read, not by observation** — the standard the register itself applies
to a *routed construction*, and one grade below the `[Observed]` a trip requires. A build row implementing
it must reproduce before it believes.

**Two costs the verdict carries rather than hides.** (i) The warning fires on the **ordinary** succession
path, which is the common case — a value that fires often is a value callers learn to ignore, and the
minting row should weigh whether it belongs on the write or on `reinstate`'s eventual refusal. (ii) Minting
it is an `INTERFACE.md` §5.4 vocabulary addition under **R3** (a fortieth value with its row), so the cost
is one spec change plus one contract id per door, not zero.

**Recommendation, offered and not taken:** the construction survives its own falsifier and should be
**routed onward as implementable**, with the two costs on the record. **Killing it remains available on the
noise objection**, which is a judgment about the vocabulary and not about constructibility — and that
judgment is not mine to make.

---

## §6 — Every number, re-derived by its defining command

Run from the repo root, after the prose above was written, per §0.7.

**The deriving script is [`docs/tools/audit_6e_register.py`](../tools/audit_6e_register.py)** — read-only:
it opens one markdown file, writes nothing, and touches no store.

```
py docs/tools/audit_6e_register.py
```

| # | number | value | defining command / derivation |
|---|---|---|---|
| D1 | trip **sections** in the register | **18** | `py docs/tools/audit_6e_register.py` → D1 (eighteen headings covering twenty-three counted trips; four headings carry 2–3 trips each) |
| D2 | sections recording a **1.0** answer | **16 of 18** | same script → D2. The two without are trips 1 and 2. Sections naming `resolve_type` within 240 chars of `1.0`: **15 of 18** |
| D2′ | trips whose harm is a 1.0 answer | **21 of 23** (trips 3–23) | D2's sixteen sections expanded to their trip numbers |
| D3 | first appearance of the one-call diagnosis | **line 61** (trip 3) | same script → D3 |
| D3′ | times it is credited to *"the sixth trip"* | **5** (lines 210, 256, 266, 290, 298) | same script → D3 |
| D4 | *"the design is still not what tripped"* | **10** | same script → D4 |
| D4′ | *"capability predicate gets merged as a duplicate"* in the register | **1** | same script → D4 |
| D4″ | *"two things answering to one identity"* in the register | **0** | same script → D4 |
| D5 | Q56 mentions / named as class-closing | **18 / 9** | same script → D5 |
| D6 | commit that first wrote the widened criterion | **`b6cf860`, 2026-09-03, `docs/runs/7A-RUN.md`** | `git log --reverse --format='%h %ad %s' --date=short -S "two things answering to one identity" --` (oldest hit), confirmed by `git show b6cf860^:docs/runs/7A-RUN.md \| grep -c` → **0** |
| D7 | classification totals | **`I` 5 · `R` 17 · `D` 1 = 23** | §2's twenty-three entries, tallied in §3.1; §0.4's falsifier threshold is `R+D ≤ 8` and `R+D` = **18** |
| D8 | local-only commits after this one lands | **4** | `git rev-list --count origin/main..HEAD` — 3 before this commit, 4 after |

**One correction made by this process, recorded because §0.7 exists to catch exactly this.** D2's first
implementation tested `resolve_type` and `1.0` **on the same line** and returned **14**. The row-6d
sections of the register are hard-wrapped at ~100 columns, so the call and its confidence routinely land on
different lines. The test now searches the section body across newlines and returns **15** (and **16** for
a 1.0 answer however worded). **The prose above was written against the corrected number**; the wrong one
never reached a sentence. The script carries the note at the test.

---

## §7 — Routed to the supervisor. NOT self-classified.

Three items. Each is a construction my analysis reached; none is classified here.

1. **`stop`, and what §3.2 does to it.** Statement **E** survives §0.3's high `D` bar: one design defect,
   pre-registered as a real outcome, delivering the harm in twenty-one of twenty-three trips, with its
   class-closing question **Q56** named *"the founder's"* **nine times** and never ruled. Under
   `ROADMAP.md`'s criterion the consequence is that `stop` fires and the merge-centred shape returns to the
   table. **I do not fire it and I record no decline.** The fifteenth put stands open per R96; this row
   returns the evidence it was opened to get.

2. **The count's two definitions (§4).** The criterion's trigger widened at `05b8e04` (2026-08-29) in
   practice and at `b6cf860` (2026-09-03) in words, and no commit enumerated the consumers of the widened
   matcher. Whether **TWENTY-THREE** should be restated as **2 + 21 under two definitions** — the way R83
   and R97 have already split off two other levels — is a register decision. **The count is unchanged by
   this row: TWENTY-THREE.**

3. **The misattribution (D3′).** The enumeration diagnosis is minted at trip 3 (line 61) and credited to
   *"the sixth trip"* five times from row 4d onward. It is small and it is not a code defect — but it made
   family **B** look five trips younger than it is at exactly the moment the register was deciding whether
   the trips were independent. Routed as a register-hygiene item, not as a finding.

**Row state.** Committed locally, **unpushed** — `git push` is 403-blocked (wrong active `gh` account) and
this row brings the local-only total to **four**. **Nothing in this row is landed.** No product code was
written; the only non-document file added is the read-only derivation script under `docs/tools/`.
`oo-pg` is `Exited(255)`; **no suite was run and none is claimed.**
