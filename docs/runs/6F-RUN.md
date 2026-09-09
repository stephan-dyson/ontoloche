# 6F-RUN — THE READ-SIDE IDENTITY GUARANTEE

Opened by founder ruling [R99](../decisions/2026-09-09-founder-ruling-R99.md), his word: *"read"* on **Q56**,
the oldest open question in the project — flagged at the **sixth** kill-row trip, named the class-closing
question **nine** times, unruled through **twenty-three** trips and ten days.
Worker: row 6f (Opus). Supervisor: ontoloche fleet supervisor, tmux `fleet-supervisor-ontoloche`.

**What the ruling authorises, and it is narrower than it sounds:** `resolve_type` may answer **below 1.0**
and may **refuse** when the identity claim it is about to make does not re-establish at the read. The
*detection* already shipped in row 4d under the Q56 default — this call has re-read both predicate extents
on an alias or successor hit since 2026-08-30 and carried `identity_stale` when they disagree. **It could
see staleness and could not act on it.** This row is not adding the detection. It is adding the response.

---

## §0 — PRE-REGISTRATION

**This section is committed BEFORE the resolver is read and before any analysis of the four sub-questions
R99 §4 left open.** `git log` is the only artefact that can prove that ordering, because a pre-registration
and a post-hoc rationalisation are textually identical. Row 6e's falsifier was binding only because its §0
was provably the first and only commit touching its record; the same standard applies here. **If the commit
landing this section is not an ancestor of every commit that follows in this file's history, the criteria
below are decoration and this row's policy choices should be read as unconstrained.**

### §0.1 — Prior exposure, disclosed

A pre-registration that hides what its author had already read is not one. Before writing this section I had
read, in this order and no more:

1. My brief (`C:\Users\steph\.claude\fleet-supervisor\briefs\2026-09-09-oo-6f-read-side-guarantee.md`).
2. [`R99`](../decisions/2026-09-09-founder-ruling-R99.md) in full, twice, per the brief.
3. [`6E-RUN.md`](6E-RUN.md) in full — including §3.2's derivation of statement `E` and §7's routing.
4. Q56's register entry in [`2026-08-30-4c-rulings-R48-R57.md`](../decisions/2026-08-30-4c-rulings-R48-R57.md)
   in full, and [the governance register](../decisions/2026-09-07-governance-register.md) in full, including
   entry **A3** and its ordinary-calls reachability table.
5. **A bounded read of the contract surfaces this row amends, disclosed here as prior exposure because it
   is:** [`INTERFACE.md`](../specs/INTERFACE.md) §5.2.1, §5.3, §5.3.1, §5.3.2 (all eight rules and the
   permanence note), and the *shape* of the two closed vocabularies — that `Refusal.reason` holds
   **thirty-three** values (§5.12) and `warnings` holds **thirty-nine** across eleven carriers (§5.4), both
   held against `ontoloche/types.py` by [`check_spec_drift.py`](../tools/check_spec_drift.py). I read these
   so that §0.3's criteria are written against real fields and real vocabularies rather than invented ones.
   This is the same disclosed-bounded-read 6e §0.1 made for the trip record's field shapes.

**I have NOT read, at the time of this commit:** `ontoloche/registry.py`'s `resolve_type`, `_extent`,
`predicates`, `list_types` or `preflight` implementations; `ontoloche/_resolve.py`; the `C3-14`, `C10-14` or
`C10-16` contract tests; [`check_merge_guard.py`](../tools/check_merge_guard.py)'s staleness axis;
[`6D-RUN.md`](6D-RUN.md); [`ACTIONS.md`](../specs/ACTIONS.md). **The four sub-questions below are answered by
criteria fixed before the code that would let me rationalise a preferred answer was open.**

### §0.2 — The state space, fixed here, because a policy without one is a preference

Every policy question this row answers is a question about **which answer goes in which cell**, so the cells
are enumerated before the policy. At an exact hit answered through an alias or a successor, the read's
verification lands in exactly one of four states. **This partition is fixed now and is not revisable after
analysis begins.**

| state | what the read found | shipped behaviour at `396bf02` |
|---|---|---|
| **S0 — AGREE** | both extents read to exhaustion, equal | no warning, `existing`, **1.0** |
| **S1 — GROWTH** | both read to exhaustion, unequal, and the absorbed word's extent is a **subset** of the survivor's | `identity_stale`, `existing`, **1.0** |
| **S2 — DIVERGENCE** | both read to exhaustion, unequal, and the absorbed word's extent holds at least one member the survivor's does **not** — the two words demonstrably denote different sets | `identity_stale`, `existing`, **1.0** |
| **S3 — UNKNOWABLE** | at least one side could not be read to exhaustion (a partial page, a capability-degraded backend, a closure not followed) | `identity_stale` / `alias_check_incomplete:<why>`, `existing`, **1.0** |

**S1, S2 and S3 are three different facts that the shipped call reports with one answer.** That collapse is
recorded here as an observation about the cheap half, not yet as a finding — whether it matters is what
§0.3's criteria decide.

### §0.3 — The decision criteria, fixed here and not revisable after analysis begins

**The governing rule, one sentence, and every cell below is derived from it rather than chosen:**

> **A state REFUSES when the registry cannot name a correct answer to the question asked. It answers BELOW
> 1.0 when it can name one and cannot vouch for it. It answers at 1.0 only when it can vouch for it.**

That rule is not self-applying, so the evidence that applies it is fixed too.

**Test T1 — reachability, with `force` and acknowledgements REMOVED.** Each of S1/S2/S3 is constructed
against `ontoloche.Registry` using **ordinary calls only**, borrowing the governance register's standing
rule 3 verbatim. **A state I cannot reach with ordinary calls does not get a policy invented for it.** It is
recorded as unreachable, its cell stays empty and named, and the residual is stated. This is 5.3.2-5's own
lesson — a rule whose branch is unreachable by construction is a `prose-only:` tag, not coverage.

**Test T2 — the write-door mirror. This is the load-bearing discriminator and it is fixed now.** For each
reachable state, the same operand pair is put to `merge_types` **directly, at that moment**, and the door's
answer is observed. The mapping from that answer onto the read's policy is fixed here:

| what `merge_types` answers about this pair, asked now | what the read does | why this mapping and not another |
|---|---|---|
| **permits** the merge | **1.0** | the write door vouches for the pair; the read has nothing to add |
| refuses, **overridable** (`overridable=True`) | **answer, below 1.0** | an overridable refusal is this project's own way of saying *a human may decide this*. A lowered confidence is that same sentence at the read: the answer is handed over, the vouching is withdrawn |
| refuses, **NON-overridably** | **REFUSE** | this is the sixth trip's own shape, in §5.3's own words — *"this call answers at 1.0 over a pair §5.10 refuses non-overridably when asked directly."* A read that answers confidently over a pair no human may acknowledge past is statement `E` still running |

**Why T2 rather than a fresh axis.** The alternative is to invent a read-side severity scale, which is a new
policy nobody ruled. T2 derives the read's policy from the write's, which the project **has** ruled, twenty-
three trips deep — and it makes the two sides of one identity claim answer consistently, which is the defect
A3 is filed for. **A pre-registered rule that reuses a ruled axis is worth more than a well-argued new one.**

**Criterion for sub-question 2 (the confidence a stale-but-answerable redirect carries).** Three conditions,
all required:

1. **Derived, not chosen.** The number is computed from a quantity **this call already reads**. No new read
   is added to produce it. The derivation is printed beside the number in this document.
2. **Pinned.** Replacing the derivation with a constant must make at least one contract id **fail**. A number
   nothing pins is decoration — this row's own mutation bar, and 4d round 3 found two decorative rows by it.
3. **Not round for roundness.** I pre-commit to rejecting any candidate whose only argument is that it is a
   familiar float. If a derivation happens to land on a round number, the derivation is the reason and the
   roundness is a coincidence stated as one.

**And the pre-registered fallback, taken over an invented number:** if no quantity this call already reads
can produce a defensible figure, the answer is **`confidence: None`** — §5.3's own *"`None` means did not
score, NOT zero"*, Rule U at the confidence field — and **not** a float chosen to look reasonable. **I
pre-commit to taking `None` over a made-up number**, and to recording the caller cost of doing so.

**Criterion for sub-question 3 (does this reach past predicates).** Not argued — **tested.** The trip-12/13
shape is constructed: a **transferred word**, the case R99 §4 names the cheap half *"structurally blind"* to.
The read is then run against it and the response is observed. Whatever fires or does not fire is reported in
those words. **If the response does not fire, the change INHERITS the blindness and this record says exactly
that**; it does not describe the gap as narrowed, addressed, or out of scope.

**Criterion for sub-question 4 (Beacon slice 1).** Not empirical and not deferrable. The consequence is
stated in the relay's own terms — it was told on 2026-08-30 that it *"can trust a 1.0 redirect, or is told
not to"* — in one paragraph, whichever way 1–3 land, **including if the answer is that a shipped consumer
must change**. The supervisor relays it; this row does not soften it first.

### §0.4 — Falsifiers, written to be easy to trip

**Primary falsifier — it kills T2's three-way answer.** If, across every state reachable under T1, the
`merge_types` mirror returns **only overridable refusals**, then **`refuse` is never the answer**, the reply
to sub-question 1 is *"answer below 1.0, never refuse"*, and **R99's authorisation to refuse goes unused by
this row.** That is a real and available outcome, it is the boring one, and I pre-commit to reporting it as
the finding rather than reaching for the refusal the ruling made available.

**Secondary falsifier — it kills the row's premise that S1/S2/S3 need separating.** If S2 is **unreachable**
under T1 with ordinary calls — that is, if every state in which the absorbed word's extent holds a member
the survivor's lacks is already refused non-overridably at the write and can never be observed at the read —
then the partition collapses, the answer is a **two-way** split (agree / everything else), and the elaborate
state space above was my invention rather than the system's. **I pre-commit to collapsing it and saying so.**

**Tertiary falsifier — it kills the row's confidence half entirely.** If no quantity the call already reads
yields a derivable number, §0.3's fallback binds and the answer is `confidence: None`. A float that arrives
in this document without a printed derivation is a violation of this section, not a result of it.

**What I do NOT get to change.** The kill-row count stays **TWENTY-THREE**; a ruling is not a trip and
neither is a build row. **I never self-classify a kill-row trip** — a construction reaching the criterion's
shape is routed to the supervisor. **The kill row's `stop` is RESOLVED by R99, not declined, and I record no
sixteenth decline**; if I find myself writing one I stop and ask the supervisor. **A3 does not close here**
and nothing in this document may read as closing it — its two write doors still neither refuse nor warn on
ordinary calls, and they are the next row's.

### §0.5 — Prediction P1, and why it is the one that matters

**Recorded before the resolver is open, so that finding it cannot later be described as having always been
obvious.**

> **P1 — the required A3 probe cannot pass while the change stays predicates-only, so sub-question 3 is not
> an open academic question but a BLOCKING dependency of this row's own deliverable.**

The reasoning, stated so it can be attacked: the 4d gate requires **both** the word asked about and the entry
handed back to be `kind="predicate"` (5.3.2-1, 5.3.2-4 — *"a hit where either side is not a predicate reads
no extent at all"*). A3's shape is two **action families** with contradictory governance declarations. If
A3's collapse is written at `kind="action"` rows, the shipped gate reads no extent, no staleness is detected,
and **the response this row adds never fires on the very shape the brief requires it to remove.**

**P1's falsifier, fixed:** if the A3 shape is reachable through rows the 4d gate does see — because the
governance declarations hang off entries the collapse touches as predicates, or because the gate's kind test
is looser than 5.3.2-4 reads — then P1 is **FALSE**, the probe passes without extending the reach, and I
score it false in this document's own scorecard. **I predict P1 TRUE and I would rather be wrong**, because
a false P1 is a smaller row.

Two further predictions, scored the same way:

> **P2 — S3 (UNKNOWABLE) is the state whose policy is hardest to justify**, because refusing on a
> capability-degraded backend changes what a legal, declared-degraded deployment can do, and the nineteenth
> trip is exactly a guard that skipped on such a backend and said nothing. **Falsifier:** S3 turns out
> unreachable under T1, or its T2 mirror is unambiguous.

> **P3 — the four consequential doors (`_extent`, `predicates()`, `list_types(predicate=)`, `preflight`) do
> NOT today carry the staleness the resolver detects**, so specifying them is a real addition and not a
> restatement. **Falsifier:** any one of them already reports it, in which case the asymmetry the brief names
> is narrower than stated and I say so.

### §0.6 — The A3 probe's pass condition, fixed BEFORE the probe is written

The brief requires *"a probe reproducing A3's shape end to end against `ontoloche.Registry` and showing that
after your change the machine actor no longer receives a clean 1.0 on that verb."* **Clean 1.0 is defined
here, now, so the definition cannot be relaxed to fit what the probe returns:**

> A **clean 1.0** is `outcome == "existing"` with `confidence == 1.0` and **no refusal**.

**Satisfying the deliverable therefore requires one of: a refusal, or `confidence != 1.0`.**

**A warning alone does NOT satisfy it.** `identity_stale` shipped on 2026-08-30 and **A3 was filed after it**
— a probe that returns a warning and calls the deliverable met would be reporting the cheap half as the
expensive one. This clause exists because that is the easiest available self-deception in this row.

The probe reproduces A3's own sentence end to end: two action families with contradictory governance
declarations, collapsed by **ordinary calls with `force` and acknowledgements removed**, then `resolve_type`
on the dead word and `preflight` on the same word, with the Haiku-tier actor's `applied` record as the
terminal observation. **It is pinned**, and it states what it does not show.

### §0.7 — Numbers

**Every published number in this document is re-derived by its defining command LAST**, after the prose is
written, and the command is printed beside the number. This project has recorded instances of a number in
prose that the code did not derive, and 6e's own §6 caught one of its own by this discipline. Numbers in §0
are thresholds I am setting or state I have measured, and are marked as such by being here.

### §0.8 — State at pre-registration

| fact | value |
|---|---|
| `main` locally, and `origin/main` | **`396bf02`** — in sync, working tree clean, **0 local-only commits** |
| Kill-row count | **TWENTY-THREE** — unchanged by this row |
| Kill row's `stop` | **RESOLVED by R99**, explicitly not declined; **no sixteenth decline is recorded here** |
| Governance register | **ONE** (A3, BLOCKING, **open and unfixed**), its stop criterion **ARMED and FIRED** (R100) |
| ACTIONS-surface launches | **HALTED** by that firing; this row is a **read-side** row and R100 names it as not halted |
| `Refusal.reason` | **33** values (§5.12) |
| `warnings` | **39** values across eleven carriers (§5.4) |
| `oo-pg` | **Up**, port **55432** — all three legs are runnable, which 6e's row could not claim |
| Suite floor | *measured by the commands in §0.9; this row never drops below it* |
| Next ruling number | **R102** |

### §0.9 — The suite floor, measured

Fixed by running the commands below at `396bf02` **before any change**, so that "never drops below it" names
a number this row observed rather than one it inherited from a previous row's prose.

```
OO_POSTGRES_DSN=postgresql://postgres:openontology@localhost:55432/open_ontology py -m pytest -q --pyargs ontoloche.contract
OO_POSTGRES_DSN=postgresql://postgres:openontology@localhost:55432/open_ontology py -m pytest -q --pyargs ontoloche.aio.contract
```

| leg | result at `396bf02` |
|---|---|
| sync | *filled by the run in progress at this commit; the number is the command's, not this document's* |
| async | *same* |

**Recorded honestly:** the floor cells are empty at this commit because the run had not returned when §0 was
committed, and **holding the pre-registration back to wait for it would have meant committing §0 after the
resolver was open.** The ordering that makes this section binding is worth more than a filled cell; the
commands that fill it are printed above and are not revisable.

---

## §1 — The suite floor, filled

Run at `396bf02` before any change, by §0.9's own commands, `oo-pg` up on **55432**.

| leg | result at `396bf02` | wall clock |
|---|---|---|
| sync (`ontoloche.contract`) | **912 passed, 301 skipped**, exit 0 | 894.19s (14m54s) |
| async (`ontoloche.aio.contract`) | **949 passed, 301 skipped**, exit 0 | 458.83s (7m38s) |

This row never drops below it.

## §2 — T1 and T2, as measured

Probe: [`readside_t1_probe.py`](../tools/readside_t1_probe.py). Every row below is **[Observed]** against
`ontoloche.Registry` on the SQLite leg, with **ordinary calls only** — no `force`, no acknowledgements,
per §0.3's borrowing of the governance register's standing rule 3.

### §2.1 — The correction this probe made to its own first cut

Recorded rather than edited over, because a probe that silently fixes its own fixture is a probe whose
earlier output nobody can audit.

The first fixtures seeded members on **one** side and then retired `pred_a` toward `pred_b`. Every one
came back `RETIRE REFUSED predicate_merge overridable=False`. **Those fixtures never built a redirect at
all**, so they could not have shown anything about the read. Refusal #2 requires the two extents to be
non-empty and identical **at the moment of the join** — so the states this row is about are what happens
to a *legal* join **afterwards**. Every fixture now joins on an agreeing pair first (`shared` declares
both predicates) and then moves the world with ordinary calls.

### §2.2 — The table

| state | reachable? | what the shipped read answers | T2 mirror: `merge_types(pred_a → pred_b)` asked now |
|---|---|---|---|
| **S0 AGREE** | yes | `existing` / `pred_b` / **1.0**, no `identity_stale` | `retired_operand` — **OVERRIDABLE** |
| **S0' BOTH EMPTY** | **NO** — the join itself is refused `predicate_merge` **non-overridably** | — | — |
| **S1 GROWTH** | yes | `existing` / `pred_b` / **1.0** + `identity_stale` | `predicate_merge` — **NON-overridable** |
| **S2 DIVERGENCE** | **yes** | `existing` / `pred_b` / **1.0** + `identity_stale` | `predicate_merge` — **NON-overridable** |
| **S3 UNKNOWABLE** | needs a backend declaring `indexes_membership=False`; the SQLite leg reports `True` | — | — |

**§0.2's S0' cell is answered, and my pre-registration was wrong about which side answers it.** I wrote
the `bool(left)` term into §0.2 expecting the *read* to report two empty extents as stale. It never gets
the chance: the **write** door refuses to create that join at all, non-overridably, which is trip 2's own
rule (`C10-09`) doing its job one call earlier. The term in `_identity_stale` is defensive and, by
ordinary calls on this leg, unreachable. Recorded as a correction to §0.2, not as a finding against the
code.

### §2.3 — §0.4's SECONDARY falsifier does NOT fire, and finding out cost the spec a sentence

S2 is **reachable**. I expected it not to be, on `INTERFACE.md` §5.3.2's own reasoning:

> "The absorbed word is retired, so its own written extent can never grow again; the survivor's can."

**That sentence is false, and this row found it by measurement.** After a legal join,
`propose_type("late_declarer", …, predicates=["pred_a"])` — naming the **retired** predicate — is accepted
and approved by ordinary calls, and the left extent moves from `['shared']` to
`['late_declarer', 'shared']` while the right stays `['shared']`. So the absorbed word's extent **can**
grow, and S2 — the two words demonstrably denoting different sets, in the direction the merge's
justification forbids — is an ordinary-calls state.

The permanence note's whole argument rests on that sentence. Amending §5.3.2 is inside this row's scope
and is done in the spec commit.

## §3 — T2 is FALSIFIED as a policy map, by the test §0.3 fixed before the resolver was opened

**This is the row's central result and it costs me my own load-bearing discriminator.**

§0.3 fixed T2: derive the read's policy from what `merge_types` answers about the same pair, asked now.
Applied honestly to the measured table, T2 says **REFUSE** for S1 and S2, because both mirror a
**non-overridable** `predicate_merge`. It fails in **both** directions:

1. **It refuses the ordinary case.** S1 GROWTH is a legal merge followed by the first new type declaring
   the survivor. §5.3.2's permanence note says that state is **permanent by construction** and arrives on
   the first ordinary curation pass after *any* merge. T2 would therefore make `resolve_type` refuse the
   dead word **forever, for every merged word in the registry** — deleting §5.10's *"the old word still
   resolves"* promise wholesale. That is not a guarantee change the founder authorised; it is the
   guarantee's removal.

2. **It refuses on paging rather than on broken identity.** `registry.py:4610` returns
   `"overridable": False` for **every** non-`demonstrably_same` case, the **unknowable** one included. So
   T2 wires S3 straight to REFUSE, and on a **declared-degraded** backend — UC1 Tenshen's own shape, and
   the FIRST trip's backend — every alias or successor redirect between two predicates would refuse.
   Refusal #1's own comment three lines above says refusing there *"would ban these doors on that
   backend"*, citing `C10-09`, `C3-13` and `C12-13`.
   *(Attack raised by the supervisor before the probe existed and routed to me to verify or kill.
   **VERIFIED**, and the S1 arm above is a second instance the attack did not name.)*

### §3.1 — Why T2 was wrong, stated so the replacement is not the same mistake

The two calls ask **different questions**, and T2 assumed one answer served both.

> `merge_types` asks **"may this identity be CREATED?"** and answers strictly, because creating a false
> identity is irreversible. `resolve_type` asks **"is this identity, already legally created, still
> trustworthy?"** — and *a pair that would not be joined today is not the same fact as a join that should
> not be honoured.*

### §3.2 — The amendment, made visibly and not silently

§0.2 and §0.3 said the partition and the criteria are *"not revisable after analysis begins"*. That rule
binds, so T2 is **not edited in §0** — it stands there as written and is **superseded here**, in its own
committed section, exactly as row 6e's §0.3 required of a criterion found unworkable mid-analysis.

**What dies:** T2 as a *policy map*. The refuse / score / 1.0 mapping in §0.3's table is withdrawn.

**What survives, and it is not a convenience salvage:** T2 as a **detector**. The mirror discriminates
cleanly and reproducibly — a sound identity answers `retired_operand`/overridable, a drifted one answers
`predicate_merge`/NON-overridable. That is a real signal and it is kept.

**What governs instead:** §0.3's **primary** rule, which was always the governing sentence and is
untouched by this amendment —

> A state REFUSES when the registry cannot name a correct answer to the question asked. It answers BELOW
> 1.0 when it can name one and cannot vouch for it. It answers at 1.0 only when it can vouch for it.

Applied to the measured table: S0 → **1.0**. S1, S2, S3 → the registry **can** name the correct answer
(the survivor, which §5.10 promises still resolves) and **cannot** vouch for the equality that justified
the redirect → **below 1.0**. S0' → unreachable, and §0.3's own rule forbids inventing a policy for it.

**§0.4's PRIMARY falsifier does not fire either, but not for the reason it was written.** It asked whether
every reachable state mirrors only an *overridable* refusal, which would leave R99's authorisation to
refuse unused. The mirrors are non-overridable — and the mapping that would have turned that into a
refusal is the thing this section just killed. **Whether `refuse` is ever the right answer is therefore
still open at this point in the row**, and is answered against A3's shape in §4 rather than against the
predicate states here.

## §4 — P1, P2, P3 scored, and what is routed to the supervisor

### §4.1 — P1: **TRUE.** Confirmed, and it is a blocking dependency as predicted

`_identity_stale("default", old_verb, new_verb)` on two `kind="action"` families returns **`False`**. The
gate is `registry.py:1351` — `if written.kind != "predicate" or answered.kind != "predicate": return
False`. The shipped detection is structurally blind to A3's shape, so a response built on top of it never
fires on the shape this row's brief requires it to remove.

**And the widening is not the obvious one.** From [`6D-RUN.md`](6D-RUN.md)'s twin table, trips 1, 2 and 5
at `kind="action"` are all recorded **NOT CONSTRUCTIBLE**, because refusal #2 is skipped for actions **by
design** ([`ACTIONS.md`](../specs/ACTIONS.md) §2.1) — an action family has no extent to read. What an
action family's identity claim stands on is its **governance declaration**, and the registry already
computes exactly that at the write doors: `_action_declarations_diverge` (`registry.py:8106`) over
`_GOVERNANCE_KEYS = ("approval_mode", "min_auto_tier", "reversibility", "effects")`.

So the structural finding, which is bigger than the prediction that led to it:

> **Row 4d built the READ-side check for the predicate operand. Row 6d built the WRITE-side check for the
> action operand. Nobody built the read-side check for the action operand — and that gap IS statement `E`
> at `kind="action"`.**

The change this row makes is therefore one principle with two operands: **the read verifies, per kind, the
same fact the write door verifies for that kind.** It invents no third axis.

### §4.2 — P3: **TRUE.** The four consequential doors report nothing

`grep -n "_identity_stale" ontoloche/registry.py` returns **two** call sites, both inside `resolve_type`
(1503, 1667). `_extent`, `predicates()`, `list_types(predicate=)` and `preflight` never call it.
**[Observed]** on the S1 fixture, where `resolve_type` carries `identity_stale`:

| door | what it answers on a store whose identity has gone stale |
|---|---|
| `_extent('pred_b', identity=True)` | `members=['grower','shared'] size=2 why=None` — a clean, complete answer |
| `predicates(of='shared')` | `known=1 warnings=[]` |
| `list_types(predicate='pred_b')` | `n=2 complete=False why_incomplete='filters suppressed rows: predicate, include_retired=False'` — incomplete for an unrelated reason, saying nothing about the identity |

The asymmetry the brief names is real, and it is this row's to specify.

### §4.3 — P2: **not yet scored.** S3 needs the declared-degraded leg

P2 predicted S3 would be the hardest policy to justify. §3's second arm already shows why, but S3 has
**not** been constructed — the SQLite leg reports `indexes_membership=True`. Scoring P2 requires the
`sqlite_minimal` leg and is outstanding. Recorded as outstanding rather than inferred.

### §4.4 — A3 reproduces at HEAD, and the register's own table does not

Probe: [`readside_a3_probe.py`](../tools/readside_a3_probe.py). Three walks, **all three printed**,
including the one that refuses — a probe that runs only the walk it expects to succeed is not evidence.

Row 6d's commit **`304967a`**, titled *"A3 CLOSED"*, dated **2026-09-05**, **is an ancestor of HEAD**.

**WALK 1 — A3's shape as [the governance register](../decisions/2026-09-07-governance-register.md)
tabulates it** (both families declare; the four governance keys contradict):

| door | ordinary-calls result **at HEAD** | what the register states, in the present tense |
|---|---|---|
| `retire(successor=)` | **REFUSED `action_declarations_diverge`, non-overridable** | `('RETIRED','retired',[])` |
| `merge_types` | **REFUSED `action_declarations_diverge`, non-overridable** | `REFUSED definitions_diverge`, overridable |
| `import_types` | alias **not written**; `warnings=['near_duplicate:old_verb','import_refused:alias_collision']` | **warnings EMPTY** |

**WALK 3 — and A3 IS still reachable, on an axis nobody is comparing.** `_GOVERNANCE_KEYS` holds **four**
of `ACTIONS.md` §2.2's **eight** keys. **`preconditions` is not one of them.** Two families whose four
governance keys **agree** but whose preconditions differ collapse with no refusal, and the full harm
reproduces **[Observed]**:

```
collapse via retire(successor=)                   RETIRED -- no refusal, no force, no acknowledgement
resolve_type('old_verb')                          existing / new_verb / confidence=1.0    <- a CLEAN 1.0
record_invocation('old_verb', outcome='applied')  Invocation outcome='applied'
invocations(family='new_verb')                    n=0    <- the survivor's ledger is EMPTY
```

That is A3's own sentence, at HEAD, end to end. A second reachable hole: `304967a` returns `None` when
either side declares nothing (*"a family that has not DECLARED is not a family that declared
differently"*), and that walk also yields a clean 1.0, though its terminal `record_invocation` refuses for
an unrelated schema reason.

**§0.6's pass condition is therefore testable and currently NOT met** — WALK 3 is the fixture this row's
change has to break.

### §4.5 — Routed to the supervisor. NOT self-classified, and A3 is NOT closed

1. **The register's A3 table does not reproduce at HEAD on two of three doors.** Correcting a register
   entry is not this worker's. Routed.
2. **[R100](../decisions/2026-09-09-founder-ruling-R100.md) fired the governance stop criterion on A3
   today.** This row's evidence does **not** say that firing was wrong — **A3's harm does reproduce**. It
   says the *stated reachability* is wrong in one direction and incomplete in another. That reads
   founder-adjacent; routed rather than judged.
3. **The uncompared-key gap is a WRITE-door defect** and this row is fenced off the write doors. Not
   touched, not fixed, routed to the next row.

**A3 does not close here and nothing above may be read as closing it.** Its write doors still let a
governance collapse through on an axis they do not compare.

**Kill-row count: TWENTY-THREE.** Nothing in this section is self-classified as a trip. The kill row's
`stop` is **RESOLVED by R99**; **no sixteenth decline is recorded.**

---
