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
