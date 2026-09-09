# 6G-RUN — A3's WRITE DOORS. THE HALF THAT CLOSES THE GOVERNANCE STOP CRITERION.

Opened by founder ruling [R102](../decisions/2026-09-09-founder-ruling-R102.md), his word: *"all eight"* on
**Q99** — minted 2026-09-09 out of row 6f's measurement, ruled the same day.
Worker: row 6g (Opus). Supervisor: ontoloche fleet supervisor, tmux `fleet-supervisor-ontoloche`.

**What the ruling authorises, stated at its own width.** Every one of `ACTIONS.md` §2.2's **eight** declared
keys is part of the identity two action families must share before the registry lets them collapse onto one
word. `_GOVERNANCE_KEYS` compares **four**. This row makes the write doors compare eight.

**What this row is NOT.** It is not the read side — row 6f owns that, it landed, and R99's half is done. It
is not a re-fix of commit `304967a`, which already added the declaration operand at all three doors and
which the governance register's own table was two days stale about. It is not permission to touch anything
else on the ACTIONS surface: R100's stop criterion is **FIRED** and in force, and this row is the exception
because it is the fix.

**A3 closes when both halves land, and not before.** Row 6f removed A3's *delivery* — `resolve_type` no
longer hands a machine actor a clean 1.0 on a collapsed pair. The collapse still happens. **Nothing in this
document may read as closing A3 until §0.6's pass condition is met on evidence from the write half**, and
§0.10 fixes that as a thing I do not get to change.

---

## §0 — PRE-REGISTRATION

**This section is committed BEFORE `ontoloche/registry.py` is opened and before any analysis of the two
defects the brief names.** `git log` is the only artefact that can prove that ordering, because a
pre-registration and a post-hoc rationalisation are textually identical. Rows 6e and 6f both bound
themselves this way and it is why their findings hold. **If the commit landing this section is not an
ancestor of every commit that follows in this file's history, everything below is decoration and this row's
policy choices should be read as unconstrained.**

The supervisor's instruction on this point, taken verbatim rather than paraphrased, because it names the
exact failure this section exists to prevent:

> *A count of "currently-legal collapses this refuses" chosen after seeing the number is worthless; a method
> fixed before is evidence. Also fix in §0 what you will do if the number is LARGE, because that is the
> moment the temptation to narrow the set arrives.*

§0.4 fixes the method. §0.4c fixes what happens if the number is large.

### §0.1 — Prior exposure, disclosed

A pre-registration that hides what its author had already read is not one. Before writing this section I had
read, in this order and no more:

1. My brief (`C:\Users\steph\.claude\fleet-supervisor\briefs\2026-09-09-oo-a3-write-doors.md`), in full.
2. [`R102`](../decisions/2026-09-09-founder-ruling-R102.md) in full, per the brief's gate note.
3. [The governance register](../decisions/2026-09-07-governance-register.md) in full, **including entry A3's
   2026-09-09 in-place correction and all four standing rules**.
4. [`R100`](../decisions/2026-09-09-founder-ruling-R100.md) in full, **including §2b's same-day correction**.
5. [`6F-RUN.md`](6F-RUN.md) — §0 entire (its pre-registration, which this section is modelled on), §4.4,
   §4.5, §5.1, §5.2, §5.3, and §7.3 through §7.6. **I have not read its §6, §8, §9 or §10.**
6. **A bounded read of the spec surfaces this row amends, disclosed here as prior exposure because it is:**
   [`ACTIONS.md`](../specs/ACTIONS.md) §1 (non-goals, for the *"no ordering"* sentence R102 cites) and §2.2
   entire (the eight keys, their types, and rules 2.2-1 through 2.2-5);
   [`INTERFACE.md`](../specs/INTERFACE.md) §5.10 entire (the six-refusal table and the row 4d note),
   §5.12's opening line and its thirty-three-value list, the paragraph at §5.12 defining
   **`action_declarations_diverge`**, and rule **5.3.2-10** at §5.3.2. I read these so that §0.2's cells and
   §0.3's criteria are written against real fields, real refusal values and real rule ids rather than
   invented ones. This is the same disclosed-bounded-read 6e §0.1 and 6f §0.1 each made.
7. Two `grep` hits in [`PACKAGE.md`](../specs/PACKAGE.md) — the `C12-29` and `C19-100` rows — surfaced by a
   repository-wide search for `action_declarations_diverge`. `C19-100` is row 6d's own record of the defect
   R102 §3 warns me against, in its own words.

**I have NOT read, at the time of this commit:** `ontoloche/registry.py` at all — not `_GOVERNANCE_KEYS`,
not `_action_declarations_diverge`, not `_UNORDERED_DECLARED_KEYS`, not `_declaration_agreement`, not the
three doors' call sites; `ontoloche/aio/registry.py`; `docs/tools/readside_a3_probe.py`; the `C19-97`,
`C19-98`, `C19-99` or `C19-100` contract tests; [`6D-RUN.md`](6D-RUN.md); any of the four gate scripts.
**The policy cells below are fixed before the code that would let me rationalise a preferred answer is
open.**

**One consequence of that ordering, stated rather than hidden.** §0.2's cells are derived from the *spec*
and from what R102 and the brief report about the code. If the code turns out to have a cell this partition
does not name, **that is a finding against this section** and it is recorded as one in §0.2's own terms, not
absorbed silently.

### §0.2 — The state space, fixed here, because a policy without one is a preference

Every question this row answers is a question about **which answer goes in which cell**, so the cells are
enumerated before the policy. Two `kind="action"` families arriving at a collapse door land in exactly one
of these six states with respect to `ACTIONS.md` §2.2's eight declared keys. **This partition is fixed now
and is not revisable after analysis begins.**

| state | what the two families' declarations do | behaviour at `4960831`, as reported by R102 and the register's correction |
|---|---|---|
| **W0 — AGREE** | both declare, all eight keys agree | permitted at all three doors. Correct, and must stay correct |
| **W1 — CONTRADICTION IN THE COMPARED FOUR** | both declare; at least one of `approval_mode`, `min_auto_tier`, `reversibility`, `effects` contradicts | **`REFUSED action_declarations_diverge`, `overridable=False`** at `retire(successor=)` and `merge_types`; alias not written at `import_types`. Fixed by `304967a`. **Not this row's to re-fix** |
| **W2 — CONTRADICTION ONLY IN THE UNCOMPARED FOUR** | both declare; the four above agree; at least one of `inputs`, `preconditions`, `reachability`, `payload_schema` contradicts | **permitted, no refusal, no `force`, no acknowledgement.** This is A3's live route and walk 3 of the probe. **This is the cell R102 exists to close** |
| **W3 — ORDER-ONLY DIFFERENCE ON A LIST KEY** | both declare; every key agrees **as a set**; at least one list-valued key differs only in element ORDER | permitted today for the three keys nobody compares. For `effects` it was **refused non-overridably** until row 6d's round 3 fixed it — the defect `C19-100` records. **Must stay permitted, and widening to eight triples this surface** |
| **W4 — ONE SIDE DECLARES NOTHING** | one family declares none of the eight | permitted; `_action_declarations_diverge` returns `None` by an argued choice (*"a family that has not DECLARED is not a family that declared differently"*). **Defect B. R102 §4 explicitly does not decide it** |
| **W5 — PER-KEY ABSENCE** | both families declare *something*, but a given key is present on one side and absent on the other | **unmeasured at the time of this commit, and named here so it cannot be filled by accident.** The read side's rule 5.3.2-10 treats it as *not agreeing*. R102's own table repeats that for the read. **R102 says nothing about it for the write** |

**W5 is the cell this row is most likely to get wrong**, and it is written down before anything is measured
for exactly that reason. It is not W4: W4 is a family that has declared nothing at all, and its argument —
row 6b's `declared_policy.declared` line — is about a family that never spoke. W5 is a family that spoke and
left one key out. **`reachability` makes this concrete and not hypothetical**: `ACTIONS.md` §2.2 says an
**empty list is a positive declaration** — *this host exposes me on no named surface* — so for that key,
`[]` and *absent* are different facts, and a comparator that folds them together is asserting one of them.

### §0.3 — The decision criteria, fixed here and not revisable after analysis begins

**The governing rule, one sentence, and every cell below is derived from it rather than chosen:**

> **A write door refuses a collapse when the two families' declared identities CONTRADICT. It does not
> refuse on an ABSENCE, and it does not refuse on a difference that is only an ORDERING.**

The first clause is R102. The second is R102 §4's explicit non-decision, held at the least-refusing option
until someone with the authority rules otherwise. The third is `C19-100`, which is the defect this row is
told twice not to repeat.

That rule is not self-applying, so the evidence that applies it is fixed too.

**Test T1 — reachability, with `force` and every acknowledgement REMOVED.** Each of W0–W5 is constructed
against `ontoloche.Registry` using **ordinary calls only**, at **all three doors**, borrowing the governance
register's standing rule 3 verbatim. **A state I cannot reach with ordinary calls does not get a policy
invented for it.** It is recorded as unreachable, its cell stays empty and named, and the residual is
stated. `import_types` is measured on its own terms because rule 2.2-4 says a `Refusal` is not returnable
there: **its pass is "the alias is NOT written", not "a `Refusal` object came back."**

**Test T2 — the READ-side mirror, run in the opposite direction from row 6f's.** R102 §2 says both sides now
stand on the same definition of an action family's identity, so the read is the ruled axis and the write is
derived from it rather than from a severity scale I invent. For every state reachable under T1, the same
operand pair is put to `_declaration_agreement` / `resolve_type` **at that moment**, and the mapping is
fixed here:

| what the read says about this pair, asked now | what the write door does | why this mapping and not another |
|---|---|---|
| all eight agree — agreement scores **1.0**, no `identity_stale` | **PERMIT** | the read vouches for the pair as one thing; the write has no ground to refuse a join the read certifies |
| a key **contradicts** — both sides declared it, the values differ, and they differ as **sets** for the four unordered keys | **REFUSE `action_declarations_diverge`** | R102's whole content. *"May these be joined?"* and *"do these still denote one thing?"* take the same evidence |
| a key differs **only in element order** | **PERMIT**, and the read must not be scoring it apart either | `C19-100`. `ACTIONS.md` §2.5 defines effect identity, §3.3's mechanism is set containment, §1's non-goals say *no ordering* |
| a key is **absent on one side** (W5), or a whole family declares nothing (W4) | **the cell §0 leaves EMPTY and NAMES.** Pre-commit: I take the **least-refusing** option consistent with the shipped, argued `if not mine or not theirs: return None`, I do **not** mint a new refusal condition, and I **ROUTE** the question | R102 §4 says `all eight` decides *which keys are compared when both sides declare*, not what to do when one does not. Filling this cell is deciding what the registry refuses, which is the class of `Q56`, `Q50` and `Q99` — not mine |

**Why T2 rather than a fresh axis.** The alternative is a per-key severity scale — *is a `payload_schema`
contradiction as bad as an `approval_mode` one* — which is **exactly one of the three things R102 §4 refused
to decide**. Inventing it here would be answering a founder question with an implementation choice. T2
derives the write's policy from a definition the founder has just ruled, which is worth more than a
well-argued new one.

**Criterion for the overridability question, fixed so it cannot drift.** `action_declarations_diverge` is
non-overridable today. **This row does not change that**, in either direction, for any key. If the evidence
argues that a `payload_schema` contradiction deserves a weaker severity than an `approval_mode` one, that is
**a finding I ROUTE, with the evidence attached**, and it goes to the supervisor and possibly the founder.
**A change to severity that arrives in this row's diff is a violation of this section, not a result of it.**

**Criterion for defect B (W4), fixed the same way.** The brief asks three questions and says *route the
answer; do not rule it*. What I produce is: (1) exactly what refuses `record_invocation` on walk 2, named by
symbol and by refusal value; (2) whether any contract id or spec rule **pins** that behaviour, established
by search rather than by reading and concluding; (3) the survivor-declares-human-approval-only / absorbed-
declares-nothing case, **constructed and run**, with whatever happens reported in its own words. **No
change to the `if not mine or not theirs: return None` branch lands in this row.** If the evidence says
absence should refuse, that reverses a stated argument from row 6b and belongs to the supervisor and
possibly the founder.

### §0.4 — The measurement I owe, its method fixed BEFORE it is taken

R102 §4 names this a measurement, not an assumption: **how many currently-legal collapses does `all eight`
refuse?** The method is fixed here in two parts, because a bare count without a shape is not readable.

**First, what a "currently-legal collapse" IS, defined precisely, because the supervisor is right that the
trap wears a measurement's clothes here.** A collapse counted by this measurement is a pair of
`kind="action"` families that, at `4960831`, **completes at a write door under ordinary calls with `force`
and every acknowledgement removed**, and that is counted as **newly refused** only when the refusal is
caused by a **genuine contradiction** on one of the four newly-compared keys — that is, cell **W2**.

**Three exclusions, fixed here and not after the count:**

1. **W3 is NOT a newly-refused collapse. It is a BUG.** A pair differing on a list key only by element
   ORDER is legal today and must stay legal. **If my method counts such a pair as newly refused, I have
   measured `C19-100`'s defect in my own code and published it as the ruling's cost.** Any W3 pair that
   refuses is removed from the count and re-filed as a **BLOCKING finding against this row**, in the same
   sentence that reports it.
2. **W4 and W5 are NOT counted either way.** §0.3 fixes that this row does not change the absence
   behaviour, so a pair whose only difference is an absence is not a collapse this ruling refuses. If one
   turns out to refuse, that is an unintended change and it is BLOCKING, not a data point.
3. **W1 is not counted.** Those pairs have refused since `304967a` and counting them would credit this row
   with row 6d's work — the same carry-forward error the governance register made for two days.

**So the number this row owes the founder is the count of W2 pairs, and nothing else.** Every excluded
category is published beside it with its own count, so the reader can see what was taken out rather than
having to trust that nothing was.

**Part A — SUITE-OBSERVED, and it is the one that counts.** The population is every contract id in
`ontoloche.contract` and `ontoloche.aio.contract`. The measurement is: **the set of ids that PASS at the
suite floor and FAIL after the change**, both legs, by the defining commands in §0.9.

> **The clause that makes Part A binding, pre-committed here.** Every id in that set is examined
> **individually and by name**. Any id that fails because a collapse it exercises was **legal and is now
> refused** is a **BLOCKING finding against my own change** — not a test to update, not a fixture to edit.
> `C19-100` is the recorded instance of exactly this, and its own words are *"it closed a legal
> operation."* **An id updated to accept a new refusal, without that refusal first being argued in this
> document as correct, is the defect this row was warned about, shipped.**

**Part B — CONSTRUCTED CENSUS, which gives the shape Part A's number cannot.** A lattice of **twelve cells**
— the four newly-compared keys (`inputs`, `preconditions`, `reachability`, `payload_schema`) × the three
doors (`retire(successor=)`, `merge_types`, `import_types`) — each measured **before and after**, under T1's
ordinary calls. Each cell reports permit / refuse, and the count of cells that flip is published beside the
count that do not. **Part B is run against a fixture built for it, so a cell that flips is a cell I
constructed and can print, not an inference.**

**Both parts are re-derived by their defining commands LAST**, per §0.7, and both numbers are printed with
the command that produced them.

### §0.4b — Falsifiers, written to be easy to trip

**Primary falsifier — it kills the premise that the write doors need widening at all.** If, under T1 with
ordinary calls, a contradiction on **each** of `inputs`, `preconditions`, `reachability` and `payload_schema`
turns out to be **already refused** at all three doors by some other guard — `definitions_diverge`, the
attribute schema, refusal #2's alias transfer, anything — then `all eight` adds nothing at the doors, the
honest report is *"the ruling is already satisfied by code that was already there"*, and **this row writes no
comparator change.** I predict this FALSE, because walk 3 has now reproduced under two independent runs
(row 6f's and the supervisor's own). **It is cheap to trip and I would rather find it than assume past it.**

**Secondary falsifier — it kills the row's claim to symmetry with the read side.** R102 §3 and the brief both
say *"the write side must match it"*, meaning `_UNORDERED_DECLARED_KEYS`. If that constant or
`_declaration_agreement` turns out **not to be usable at the write door** — a different data shape, a
different normalisation, values read from a different place — then this row is **re-implementing** the set
comparison, not reusing it, and *"one fact, one home"* (`C19-100`'s own closing line) is **not** achieved.
**I pre-commit to saying that in those words rather than describing a parallel implementation as matching.**

**Tertiary falsifier — it kills W5 as a distinct cell.** If per-key absence turns out to be **unreachable**
at the write doors with ordinary calls — because the attribute schema requires all eight whenever any is
declared, or because rule 2.2-2's *"must declare `reversibility` and `approval_mode`"* generalises further
than it reads — then W5 collapses into W0/W4, the partition is five cells not six, and **I invented the
sixth.** I pre-commit to collapsing it and saying so.

### §0.4c — What I do if the number is LARGE

Fixed here because, as the supervisor put it, **that is the moment the temptation to narrow the set
arrives** — and R102 §4 already ruled on the temptation in advance: *"If the number is large, that is
evidence worth bringing back, not a reason to narrow the set quietly."*

**Large is defined now, so it is not defined by the number.** Part A is **large** if the set of newly-failing
ids exceeds **five** on either leg. Part B is **large** if more than **six** of its twelve cells flip.

**What happens then, in order, and none of the steps is "narrow the key set":**

1. The full list of affected ids and cells is published in this document **by name**, with what each one was
   asserting.
2. Each is classified as **(a) a collapse that was always wrong and is now correctly refused**, or **(b) a
   collapse that was LEGAL and is now closed**. The second class is `C19-100`'s defect and any member of it
   is BLOCKING regardless of the count.
3. The number and both classes are **ROUTED to the supervisor with the evidence**, as R102 §4 directs, and
   the row does not proceed to land on its own judgement that the cost is acceptable.
4. **`_GOVERNANCE_KEYS` still holds all eight.** Narrowing the set is a founder decision, it is not
   available to this row at any count, and if I find myself writing an argument for it I stop and route
   instead.

**And the consumer-risk argument is closed off before it can be made.** The general supervisor states, via
mine, that **beacon has no action-family collapse path today and is pinned at `802ddf02`**, so the refusal
count is informational for it rather than gating. **[Attributed, NOT verified by me]** — beacon is not this
row's partition and I did not audit its code, so it is recorded at that grade. It cuts **one** way only: it
removes *"a shipped consumer will break"* as a reason to hurry or to narrow. **It is not evidence that the
cost is acceptable**, and *"no consumer is at risk today"* is not an argument this row gets to convert into
a smaller key set. The count is still measured properly, because its job is to tell the founder the size of
what he chose.

### §0.5 — Predictions, recorded before the code is open so that finding them cannot later be described as obvious

> **P1 — the ordering trap is REACHABLE at the write doors, and a naive `!=` on the three new list keys
> reproduces `C19-100`'s defect non-overridably.** The reasoning, stated so it can be attacked: `inputs`,
> `preconditions` and `reachability` are all `list[...]` per §2.2, `effects` needed a set comparison for
> exactly this reason, and nothing about the other three makes them ordered where `effects` was not.
> **Falsifier:** a naive `!=` on order-only-different declarations does not refuse at any door — in which
> case the trap is not reachable on these keys and I say so. **How it is demonstrated rather than asserted:**
> the contract id asserting order-insensitivity is written FIRST and observed to FAIL against a naive
> comparison, before the set comparison is written. A trap I only describe is a trap I have not shown.

> **P2 — the `record_invocation` refusal that blocks walk 2 is load-bearing BY ACCIDENT.** Nothing pins it,
> no spec rule names it as a governance defence, and it is a schema check that happens to sit downstream.
> **Falsifier:** a contract id asserts it, or a spec rule names it. **Why it matters:** the brief's own
> sentence — *a harm blocked by an accident is not blocked* — is only true if the accident is real, and P2
> is that claim made checkable.

> **P3 — W5 (per-key absence) is reachable with ordinary calls and is NOT refused today.** **Falsifier:** the
> tertiary falsifier above. **Why it is predicted separately:** if P3 is TRUE, this row ships a comparator
> that must make an explicit choice about W5, and §0.3 has already fixed that the choice is the
> least-refusing one and is routed.

### §0.6 — The write half's pass condition, fixed BEFORE the probe is extended

The brief requires the A3 probe extended *"to prove the write half."* **What proving it means is defined
here, now, so the definition cannot be relaxed to fit what the probe returns:**

> The write half is met when, on **walk 3's fixture** (the four old keys agree, `preconditions` differs),
> **each of `retire(successor=)`, `merge_types` and `import_types` refuses or warns** under **ordinary calls
> with `force` and every acknowledgement removed** — where `import_types`' pass is that **the alias is NOT
> written**, per rule 2.2-4, and a warning that leaves the alias written does not count.

**Three clauses against the self-deceptions available in this row, each one naming the specific mistake:**

1. **The read answering below 1.0 does NOT satisfy it.** Row 6f already made walk 3 answer `0.75` and walk 2
   answer `None`. A probe that prints those and calls the write half proven is **reporting another row's
   deliverable as this one's**. The write half is about whether the **collapse** happens.
2. **Walk 1 refusing does NOT satisfy it.** Walk 1 has refused since `304967a` on 2026-09-05. Citing it as
   evidence for this row is the same error the governance register made for two days and carried into a
   founder ruling.
3. **The terminal `record_invocation` refusing does NOT satisfy it.** That is walk 2's accident, and the
   brief's own sentence is that a harm blocked by an accident is not blocked.

**And the counter-clause, so the pass condition cannot be met by over-refusing:** the probe also runs a
**W3 control** — two families whose eight keys are identical **modulo list element order** — and the write
half is **NOT** met unless all three doors **PERMIT** that pair on ordinary calls. A comparator that refuses
everything passes clause 1 and has re-created `C19-100`.

### §0.7 — Numbers

**Every published number in this document is re-derived by its defining command LAST**, after the prose is
written, and the command is printed beside the number. Rows 6e and 6f each caught one of their own numbers
by this discipline, and 6f's §7.1 caught two the code did not derive. Numbers in §0 are thresholds I am
setting or state I have measured, and are marked as such by being here.

### §0.8 — State at pre-registration

| fact | value |
|---|---|
| `main` locally, and `origin/main` | **`4960831`** — in sync, working tree clean, **0 local-only commits** |
| Kill-row count | **TWENTY-THREE** — unchanged by this row |
| Kill row's `stop` | **RESOLVED by R99**; **no sixteenth decline is recorded here** |
| Governance register | **ONE** (A3, BLOCKING, **open and unfixed**), stop criterion **ARMED and FIRED** (R100) |
| ACTIONS-surface launches | **HALTED** by that firing. **This row is the named exception, because it is the fix** |
| A3's read half | **LANDED** (row 6f, verified independently by the supervisor, six commits on `origin/main`) |
| A3's write half | **this row.** A3 does not close until it lands |
| `Refusal.reason` | **33** values (§5.12), and this row is not expected to mint a thirty-fourth |
| `_GOVERNANCE_KEYS` | **4** at this commit; **8** is what R102 rules |
| `oo-pg` | port **55432**, DSN per the brief; all three legs runnable |
| Heavy-leg clearance | **the floor run is CLEARED** by the supervisor, which checked `beacon-land.lock` (absent), `git ls-remote origin` (no `land-lock` ref) and free memory (22 GB) rather than assuming. **S9 is still to come and I announce before the next leg** |
| Next ruling number | **R103** |

### §0.9 — The suite floor, and the commands that fill it

Fixed by running the commands below at `4960831` **before any change**, so that *"never drops below it"*
names a number this row observed rather than one it inherited from a previous row's prose.

```
OO_POSTGRES_DSN=postgresql://postgres:openontology@localhost:55432/open_ontology py -m pytest -q --pyargs ontoloche.contract
OO_POSTGRES_DSN=postgresql://postgres:openontology@localhost:55432/open_ontology py -m pytest -q --pyargs ontoloche.aio.contract
```

**Run ONE AT A TIME, never in parallel** — the supervisor's instruction, and row 6f caused an
out-of-memory kill running both at once and lost two full legs to it. The SQLite-only leg runs first as a
cheap *is-anything-broken* check before a full multi-backend run is spent.

The four gates, and the list is **four** rather than three because that was found incomplete on 2026-09-09:

```
py docs/tools/check_links.py
py docs/tools/check_spec_drift.py
py docs/tools/check_merge_guard.py
py docs/tools/check_capability_matrix.py
```

| leg | result at `4960831` |
|---|---|
| sync | *filled by the run this commit authorises; the number is the command's, not this document's* |
| async | *same* |

**Recorded honestly:** the floor cells are empty at this commit because holding the pre-registration back to
wait for a run would have meant committing §0 after the code was open, and the ordering that makes this
section binding is worth more than a filled cell. The commands above are printed and are not revisable.

### §0.10 — What I do NOT get to change

- **The kill-row count stays TWENTY-THREE.** A ruling is not a trip and neither is a build row. **I never
  self-classify a kill-row trip** — a construction reaching the criterion's shape is ROUTED.
- **The governance register stays at ONE.** It counts **HARMS, not mechanisms**, and one harm reached by a
  second route is still one harm. **I never self-classify a register entry either.**
- **The kill row's `stop` is RESOLVED by R99, not declined**, and **no sixteenth decline is recorded here.**
  If I find myself writing one I stop and ask the supervisor.
- **`_GOVERNANCE_KEYS` holds all eight**, at any measured cost. Narrowing is a founder decision (§0.4c).
- **`action_declarations_diverge`'s overridability is unchanged** by this row, in either direction (§0.3).
- **The `if not mine or not theirs: return None` branch is unchanged** by this row (§0.3).
- **A3 does not close here** unless §0.6's pass condition is met on write-half evidence, and no sentence in
  this document may read as closing it before then.
- **A skip decided by the RESULT under test is never legitimate.** A skip decided by the ENVIRONMENT is, and
  belongs on the audited `requires_capability` marker. **The middle case — a skip reading the result of a
  SETUP step — is where the line actually sits**, and three ids have already been caught on the wrong side
  of it.
- **`git add -A` is FORBIDDEN.** Explicit paths, with `git status --porcelain` immediately before staging.
  The supervisor shares this working tree.
- **"LANDED" means ON ORIGIN.** Nothing is called landed before it is pushed.
