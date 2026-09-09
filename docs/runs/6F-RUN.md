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

## §5 — P2 scored, and the one measurement that decides sub-question 1

### §5.1 — P2: **TRUE**, and S3 is REACHABLE

S3 cannot be reached by *joining* on a declared-degraded backend — refusal #2 folds *unknowable* into
`not demonstrably_same`, so the join is refused `predicate_merge` non-overridably. It **is** reached by
**joining on a capable backend and reading through a degraded one**, which is not exotic: it is one
deployment reading another's store, and `PACKAGE.md` §2.6's production path is exactly that arrangement.

**[Observed]**, `DegradedAdapter(SQLiteAdapter(":memory:"), indexes_membership=False)` over a store joined
capably:

```
S3 UNKNOWABLE (joined capable, READ through degraded)
    existing / pred_b / confidence=1.0 / warnings=['near_duplicate:pred_a', 'identity_stale']
    T2 mirror on the degraded leg:  refuses/predicate_merge/NON-overridable
```

So P2's prediction holds — S3 is the hardest cell — and §3's second arm is **not hypothetical**. Under the
withdrawn T2 map this state refuses, on a backend whose only fault is that it cannot compute an extent.

### §5.2 — The measurement that decides sub-question 1: **both redirect paths ignore `min_confidence`**

**[Observed]** on the S1 fixture, and confirmed by code-read — the `min_confidence` test is at
`registry.py:1707`, **after** the exact-hit return at `1705`, so the redirect never reaches it:

| path | `min_confidence` | outcome | confidence |
|---|---|---|---|
| successor | 0.0 / 0.9 / 1.1 / 2.0 | `existing` **every time** | 1.0 |
| alias | 0.0 / 1.1 / 2.0 | `existing` **every time** | 1.0 |

A caller asking for `min_confidence=2.0` — an impossible bar — still gets `existing`. **§5.3's own
doctrine is not being applied on this path:**

> "Behaviour when uncertain — the rule this call exists for. Below `min_confidence`, return `none` with
> `alternatives` populated. **Never** return the best of a bad set as `existing`."

This was **latent and harmless while the redirect always answered 1.0** — no sane bar sits above 1.0 — and
it goes **live the moment the expensive half lowers that number**. A lowered confidence that no bar can
act on is advisory decoration.

### §5.3 — The unifying observation this row can make and no earlier row could

Three properties of the cheap half were harmless *because the answer was always 1.0*, and all three become
load-bearing the moment the read is allowed to act:

1. **The `min_confidence` bypass** (§5.2) — a lowered score nothing can gate on.
2. **The raw-name comparison** — `set(left_names) == set(right_names)` on unnormalised member names while
   the resolver scores `_norm(candidate)`. Statement **D**'s shape inside the staleness check. Its error
   direction is **over**-reporting, which costs nothing as a warning and costs a correct answer as a
   downgrade. **Code-read grade, NOT [Observed]** — recorded here at that grade deliberately, and not
   carried as a finding until it is run.
3. **The S1 / S2 / S3 collapse** — three different facts reported through one boolean.

> **Making a warning able to act does not merely add a consequence. It promotes every latent property of
> the thing that produces the warning into a live one.** That is the general cost of R99's expensive half,
> and it is the sentence this row owes the next one.

## §6 — The four sub-questions R99 §4 left open, ANSWERED WITH EVIDENCE

### §6.1 — Sub-question 1: refuse, or answer below 1.0, or both by case?

**ANSWER: answer below 1.0 — the registry never refuses on its own account — AND the redirect paths are
made to honour `min_confidence`, so the caller's own bar produces the decline.**

The reasoning, and it is not the one §0 expected:

1. **The registry can always name the correct answer**, in every reachable state. §5.10 promises the old
   word still resolves and the survivor genuinely is the identity it now belongs to. Under §0.3's
   governing rule — refuse only when the registry *cannot name a correct answer* — refusing is unavailable
   for S1, S2 and S3.
2. **T2, which was the thing that would have said otherwise, is dead** (§3), and it died refusing the
   ordinary case and refusing on paging.
3. **Refusal-on-demand is already this document's mechanism, and this path skips it** (§5.2). Honouring
   `min_confidence` on the redirect is not a new policy — it is applying §5.3's stated rule to the one
   path that returns before reaching it. A caller that declines to act on a weakened identity sets its own
   bar and gets `outcome="none"` with `alternatives` populated; a caller that does not care is unaffected.

**This means R99's authorisation to REFUSE goes deliberately UNUSED by this row, and §0.4's primary
falsifier is honoured rather than argued around.** §0.4 pre-committed: *"That is a real and available
outcome, it is the boring one, and I pre-commit to reporting it as the finding rather than reaching for
the refusal the ruling made available."* The falsifier's stated trigger (only overridable mirrors) did not
occur; its **conclusion** is nonetheless where the evidence lands, by a route §0 did not anticipate. **The
pre-commitment binds on the conclusion, not on the route**, and it is honoured here.

What the registry gains over the status quo is real and worth naming plainly: the decision moves from *the
registry decides what everyone may act on* to *the registry says how much of the claim still holds, and
each caller sets its own bar.* That is a smaller change than a refusal and a larger one than a warning.

### §6.2 — Sub-question 2: what confidence does a stale-but-answerable redirect carry?

**ANSWER: `min(resolver_score, J)` where `J` is the Jaccard agreement of the two written extents —
`|L ∩ R| / |L ∪ R|` — and `confidence: None` when the extents cannot be known.**

> ⚠ **TWO CLAIMS BELOW ARE WRONG AND ARE CORRECTED IN [§7.1](#71--07-doing-the-job-it-exists-for-two-numbers-in-62-the-code-did-not-derive).** The S2 row's `1/3` is an arithmetic error (it is **0.5**), and the *“ordering S2 < S1 < S0”* claim is false because Jaccard is symmetric. Both were caught by §0.7's re-derivation discipline **after** this section was published. The section is left as written, with this marker, because §6.2 is what I published and the governance register's standing rule 4 asks for a correction to be visible rather than for the record to look as though the error never happened.

Checked against §0.3's three conditions, all of which were fixed before the resolver was opened:

1. **Derived, not chosen.** `L` and `R` are *already read* by `_identity_stale`. No new read is added; the
   sets it already computes are measured instead of merely compared. Worked, on this row's own fixtures:

   | state | L | R | J |
   |---|---|---|---|
   | S0 AGREE | `{shared}` | `{shared}` | **1.0** — so S0 is unchanged, and that falls out rather than being special-cased |
   | S1 GROWTH | `{shared}` | `{grower, shared}` | 1/2 = **0.5** |
   | S2 DIVERGENCE | `{late_declarer, shared}` | `{shared}` | 1/3 ≈ **0.333** |
   | S3 UNKNOWABLE | not knowable | not knowable | **`None`** |

2. **Pinned.** Replacing the derivation with a constant must fail an id. The new ids assert the *ordering*
   S2 < S1 < S0 and the exact values above, so a constant fails whichever value it picks.
3. **Not round for roundness.** 0.5 and 0.333 are what these fixtures produce; a different store produces
   different numbers. Nothing here was chosen for looking reasonable.

**Why Jaccard and not containment.** Containment (`|L ∩ R| / |L|`) scores S1 at **1.0**, hiding growth
entirely — and §5.3.2's own note already rules containment out for the warning, because *"weakening it to
containment would make the warning miss Door 1"*. The same argument disqualifies it for the score.

**The cost, stated rather than hidden.** `confidence` means *how sure the registry is that this is the
right type*, and `J` measures *how much of the identity claim still holds*. They are related and they are
not the same quantity. `min()` is what keeps the composition honest — the answer is no more trustworthy
than the weaker of *does the word match* and *does the identity still hold* — but the field is carrying a
slightly different fact than it did, and a reader of §5.3 must be told so. It is told, in the amendment.

**`confidence: None` is ADOPTED AND SHIPPED, and whether it STANDS is routed.** R99 authorises answering
*"below 1.0"* and *"refusing"*. **`None` is literally neither.** It is Rule U's own answer — §5.3 says
*"`None` means 'did not score', NOT zero"* — and R99 §4 asks this row for a confidence *"not invented to a
round number without a reason on the record"*, which invites exactly this. The alternatives are worse: a
computed `0.0` is what Rule U forbids everywhere else in this document, and refusing is what §3 showed
bans the door on a legal declared-degraded backend.

> ⚠ **CORRECTION, and it is the sharpest thing round 1 found.** This paragraph first read *"that is not
> mine to settle… **I recommend `None` and I do not adopt it unilaterally**"* — and that was **not true of
> what the row had already shipped.** `_identity_agreement` returns `None` on the unknowable path, `_clears`
> short-circuits on the default `min_confidence=0.0`, and rule 5.3.2-11 forecloses refusing **in the
> committed spec**. So an ordinary caller on `PACKAGE.md` §2.6's declared-degraded production path receives
> `existing` with `confidence: None` **today**, ungated. A row cannot ship a value and describe adopting it
> as a thing it declined to do; that is having it both ways, and in a project whose discipline is that the
> record must be true it is the worse half of the two.
>
> **What is actually true:** `None` is **this row's adopted default**, shipped, pinned, and reachable now.
> **What is genuinely routed** is narrower and is stated as such — *whether `None` stands*, given it sits
> outside R99's literal two words. **The cost of a ruling against it is stated rather than hidden:** it is
> a code change plus an amended contract id, not a configuration flip, because the behaviour is pinned.
> Found by round 1's truthfulness lens; the original sentence is quoted above rather than deleted.

### §6.3 — Sub-question 3: does this reach past predicates?

**ANSWER: yes, it must — and not by widening the extent comparison, which would be meaningless.**

§4.1 established the structure. An action family has **no extent** — refusal #2 is skipped for actions by
design, and `6D-RUN.md`'s twin table records trips 1, 2 and 5 at `kind="action"` as NOT CONSTRUCTIBLE for
that reason. What an action family's identity claim stands on is its **governance declaration**.

So the change is **one principle, two operands**:

> The read verifies, per kind, **the same fact the write door verifies for that kind** — extents for
> `kind="predicate"` (`_written_extent`, row 4d), governance declarations for `kind="action"`
> (`_action_declarations_diverge`, row 6d).

**And the row inherits the cheap half's blindness on a third axis, which it says plainly rather than
describing as narrowed.** R99 §4 names trips 12 and 13 — **transferred words** — as a gap the cheap half
is *"structurally blind"* to. The read-side check is gated on an exact **alias or successor** hit
(5.3.2-1, 5.3.2-5), and a transferred word reaches the survivor by neither. **The change inherits that
blindness.** It is not closed here, it is not narrowed here, and no sentence in the amendment may read as
though it were. Recorded as a **residual** carried forward, in those words.

### §6.4 — Sub-question 4: what happens to Beacon slice 1?

Stated in the relay's own terms, and it is the second branch.

Beacon slice 1 was told on 2026-08-30 that it *"can trust a 1.0 redirect, or is told not to."* **It is now
told not to, and the consumer-facing consequence is concrete:**

1. **A `1.0` on an `existing` outcome is no longer unconditional.** It still means what it always meant —
   *the registry vouches for this* — but a redirect through an alias or a successor whose identity has
   drifted now answers **below** it. A consumer that branches on `confidence == 1.0` will start taking its
   other branch on stores where a merged predicate has since gained a member. That is not an error
   condition; it is ordinary curation becoming visible.
2. **A consumer that must not act on a weakened identity now has a supported way to say so**, which it did
   not have before: pass `min_confidence`. Below the bar the answer is `outcome="none"` with
   `alternatives` populated, which is §5.3's shipped shape for *cannot tell*. **This is new on the
   redirect path** (§5.2) and it is the half of the change slice 1 should actually build against.
3. **`identity_stale` keeps its meaning and is not sufficient on its own.** It says *this identity has
   grown apart from the equality that justified it*, not *act now*. The number is the actionable half.
4. **On a declared-degraded backend the answer may carry `confidence: None`** (subject to §6.2's routed
   question). A consumer doing arithmetic on `confidence` without a `None` check will fault. **That is a
   breaking change for such a consumer and it is stated as one rather than softened.**

**The supervisor relays this. This row does not decide what slice 1 does about it**, and has not softened
it first.

---

## §7 — The resolver change, and two errors of my own that the code caught

### §7.1 — §0.7 doing the job it exists for: TWO numbers in §6.2 the code did not derive

§0.7 requires every published number to be **re-derived by its defining command LAST**. It caught two, and
both are mine. They are corrected here rather than edited into §6.2, because §6.2 is what I published.

**Error 1 — arithmetic.** §6.2's table said S2 DIVERGENCE scores `1/3 ≈ 0.333`. **It scores `0.5`.**
`L = {late_declarer, shared}`, `R = {shared}`, so `|L ∩ R| = 1` and `|L ∪ R| = 2` — I counted the union as
three by adding the sets' sizes instead of taking their union. **[Observed]** the shipped call answers
`0.5`.

**Error 2 — a claim, and it is the worse of the two.** §6.2 said *"the new ids assert the **ordering**
S2 < S1 < S0."* **They do not, and they cannot.** Jaccard is **symmetric**: it measures *how far apart*
two sets are, not *which side moved*. On these fixtures S1 and S2 both differ by one member out of two and
both score exactly `0.5`. So the score does **not** distinguish ordinary growth from genuine divergence.

**I am not fixing that by adding a directional penalty**, because §0.3 forbids inventing a number and a
penalty would be exactly that. The honest position is that **the number measures magnitude, not
direction**, and that is stated in the record instead of engineered around. `identity_stale` and the
`reason` string carry which words moved; the score carries how far. Whether direction *should* be scored
is a question this row raises and does not answer — it needs a rule about what divergence costs, which
nobody has made. **Minted by the supervisor as `Q100`** so the raise has a handle: *should a stale
redirect's confidence reflect the DIRECTION of divergence and not only its magnitude, and what does
divergence cost?* It is **parked, not put to the founder** — the same treatment `Q50` has, visible so it
cannot be lost, and not pushed while it lacks the evidence to be ruled on.

### §7.2 — ATTACK 1 is VERIFIED, against my own implementation, by the probe

The supervisor's attack 1 said a mirror-derived read *"does not protect against both sides being wrong
together."* I recorded it as *"sound in principle and mostly moot"* once T2 died as a policy map. **It was
not moot. It landed on my first implementation within the hour.**

The first cut of the action operand **reused `_action_declarations_diverge`** — the write door's own
comparison — on the reasoning that reusing a ruled axis beats inventing one. **[Observed]** WALK 3 then
still returned a **clean 1.0**, because that function compares four of `ACTIONS.md` §2.2's eight keys and
WALK 3's families differ on `preconditions`, which is not one of the four. **The read inherited the write
door's blind spot exactly as the attack predicted**, and the probe caught it rather than a reviewer.

**The fix, and why it does not pre-empt Q99.** The read now compares **all eight declared keys**. That
makes it *stricter than the write door on purpose*, and the justification is §3.1's distinction applied a
second time:

> `merge_types` and `retire(successor=)` decide **what to FORBID** — a policy question, and precisely
> **Q99**, minted by the supervisor on 2026-09-09 out of this row's evidence and unruled. `resolve_type`
> decides **what to VOUCH FOR** — and *"these two words denote one thing"* is falsified by **any** declared
> difference, whether or not that difference is grave enough to forbid the collapse.

Comparing eight here does not pre-empt Q99's **ruling**, because this call refuses nothing (rule
5.3.2-11) and therefore never answers Q99's question about what to forbid.

> **But it is a COUPLING, and calling the two unrelated would be too strong.** Recorded as a residual
> rather than dismissed, at the supervisor's correction. **The state:** the founder rules Q99 *narrow* —
> say the current four keys — and this read still compares eight. **What the caller then sees:** two
> families differing only on `preconditions` are, by his ruling, legitimately one identity, and this call
> still hands back a confidence **below 1.0** for that difference. The read would be scoring on a notion
> of identity his policy had rejected.
>
> It is defensible on this row's own distinction — *may these be joined* and *do these still denote one
> thing* are different questions, and reporting a declared difference is a **fact**, not a veto — and the
> caller can still act, because nothing is refused. **But Q99's ruling gets to revisit this**, and the
> founder is told before he rules that the read side already scores on all eight. That relay is the
> supervisor's and is not this row's to make.

**An UNDECLARED family scores `None`, not agreement.** Row 6d's write-door line — *a family that has not
DECLARED is not a family that declared differently* — is right about **refusing** and says nothing about
vouching. Treating an absent declaration as agreement is the FIRST trip's operand exactly: **unknowable is
not equal.**

**And one defect deliberately not re-created — recorded so a later reader sees it was avoided on purpose
rather than by luck.** Row 6d's round 3 found that its own A3 fix compared
`effects` with `!=` and **closed a legal operation** for two rounds, refusing families whose governance was
identical and whose effects were merely in a different order. The read reuses `_effect_identities` for
`effects` and compares `inputs`, `preconditions` and `reachability` as **sets** (`ACTIONS.md` §1: *"no
ordering"*), so the same defect is not reintroduced one call along.

### §7.3 — What changed in the resolver

`ontoloche/registry.py`, mirrored to `ontoloche/aio/registry.py` by `tools/unasync.py` (1 of 25 files
rewritten).

| what | where |
|---|---|
| `_identity_agreement` — returns `(stale, agreement)`; the two operands, per kind | new, beside `_identity_stale`, which is kept as a thin wrapper so nothing else had to move |
| `_declaration_agreement` — all eight declared keys, order-insensitive where §1 says unordered | new |
| `_compose` — rule 5.3.2-9's `min`, with `None` **absorbing** rather than being dropped | new |
| `_clears` — rule 5.3.2-12's bar; `min_confidence <= 0.0` short-circuits so **v0 callers pay nothing** | new |
| `_identity_below_bar` — the `none` answer, survivor kept in `alternatives` | new |
| successor path | `confidence=1.0` → `confidence=agreement`, gated by `_clears` |
| alias path | `confidence=best_score` → `confidence=scored` (`min` of the two), gated by `_clears` |

**No new `Refusal.reason` and no new `warnings` value are minted by this row.** The count stays **33** and
**39**. `identity_stale` gains a carrier rather than growing a twin, which is ruling **R71**'s precedent
and the thing a closed vocabulary is for.

### §7.4 — Three shipped contract ids assert the OLD guarantee, and all three are amended

The suite named them precisely — `C3-14`, `C10-14`, `C10-16`, on both legs, and nothing else. That is the
whole blast radius of a shipped guarantee changing, and it is small because the guarantee was pinned in
exactly the places it was made.

| id | what it asserted | what it asserts now |
|---|---|---|
| `C3-14` | `stale.confidence == 1.0`, reasoned *"the redirect is a GUARANTEE (5.3). Lowering it is the founder's half of Q56"* | `< 1.0` **and** `outcome == "existing"` — the founder took that half, and it is still not a refusal |
| `C10-14` | `stale.confidence == 1.0`, reasoned *"row 4d ships the CHEAP half"* | `< 1.0` — Door 1's own store is now the fixture showing the delivery step gone |
| `C10-16` | `confidence == 1.0` for every spelling, including under `min_confidence=1.0` | `< 1.0`, and the `min_confidence=1.0` case is asserted to answer `none` |

**`C10-16` is the one worth reading twice.** Its loop had `if resolution.type is None: continue`. Under
rule 5.3.2-12 the `min_confidence=1.0` case now legitimately answers `none` with `type=None` — so it would
have **fallen through that `continue` and been silently skipped**, leaving the id green while asserting
nothing about the new behaviour. That is *"a conditional assertion whose body never ran, which is worse
than a tag because it reads as coverage"* — row 4d's third round found it by mutation, **in this same
id**. It is written out explicitly and raises rather than skipping.

**Each amended assertion keeps the superseded text in a comment** rather than deleting it, for the reason
rule 5.3.2-3 is struck rather than removed: it is what the registry promised for the ten days between
2026-08-30 and 2026-09-09, and a caller may have been built against it.

### §7.5 — Four new ids, and one of them exists to make a constant fail

| id | rule | what it pins |
|---|---|---|
| `C3-20` | 5.3.2-9 | the score equals the Jaccard the test computes from the extents **it reads back itself**, on **two stores whose Jaccard differs** — so no single constant passes both, and a containment ratio fails the first |
| `C3-21` | 5.3.2-10 | A3's shape: two action families whose declarations disagree answer **below 1.0** with `identity_stale`; **and the control** — identical declarations answer 1.0 with no warning |
| `C3-22` | 5.3.2-11 | a stale redirect is **never** a refusal, so a later row cannot quietly turn the score into one without a ruling |
| `C3-23` | 5.3.2-12 | no bar → unchanged; at the bar → `existing`; above it → `none` with the survivor still in `alternatives` |

`C3-20`'s two-store construction is §0.3's second condition made real: *"replacing the derivation with a
constant must make at least one contract id fail."*

### §7.6 — §0.6's pass condition, MET

[`readside_a3_probe.py`](../tools/readside_a3_probe.py), re-run after the change. §0.6 defined a clean 1.0
as `existing` + `1.0` + no refusal, and fixed that **a warning alone does not satisfy the deliverable**:

| walk | before | after |
|---|---|---|
| **WALK 1** (both declare, four keys contradict) | refused at the write door | unchanged — the collapse never happens |
| **WALK 2** (absorbed family declares nothing) | `existing / new_verb / **1.0**` — clean | `existing / new_verb / **None**` + `identity_stale` — **not clean** |
| **WALK 3** (four keys agree, `preconditions` differ) | `existing / new_verb / **1.0**` — clean | `existing / new_verb / **0.75**` + `identity_stale` — **not clean** |

**A3's delivery step `E` no longer hands the machine actor a clean 1.0 on that verb.** WALK 3's `0.75` is
six of eight declared keys agreeing — `inputs` and `preconditions` are the two that do not.

**A3 IS NOT CLOSED.** Its write doors still let that collapse through with no refusal and no warning: WALK
3's `retire(successor=)` still returns `RETIRED` on ordinary calls, and `record_invocation` still writes
`applied` while the survivor's ledger stays empty. **This row removed the delivery, not the defect**, which
is exactly what R99 §5 said it would and no more.

---

## §8 — This row's own findings, graded

Numbered so they can be cited, and graded rather than mentioned in passing. **None of these is
self-classified as a kill-row trip; the count stays TWENTY-THREE and anything reaching that shape is
routed.**

### §8.1 — **F1, MAJOR.** `C10-16`'s loop would have SILENTLY SWALLOWED the behaviour this row added — in the id row 4d caught by mutation for that same defect

**The construction.** `C10-16` walks every spelling of a stale word through `resolve_type` under three
kwarg sets, one of which is `{"min_confidence": 1.0}`. Its loop body opened:

```python
if resolution.type is None or resolution.type.name != "searchable":
    continue
```

Under this row's new rule **5.3.2-12** that `min_confidence: 1.0` case now answers `outcome="none"` with
`type=None` — **so it would have fallen straight through that `continue`.** The id would have stayed
green while asserting **nothing at all** about the new behaviour, on the one code path where the new
behaviour is most consequential.

**Why it is graded MAJOR and not a note.** This is the register's own recurring shape, reappearing inside
the assertion that exists to catch it:

- `INTERFACE.md` rule **5.3.2-5** already carries a `prose-only:` tag whose stated reason is that
  *"`C3-14` carried a conditional assertion whose body never ran, which is worse than a tag because it
  reads as coverage; row 4d's third round found it by mutation."*
- Row 4d found that defect **in this same family of ids**, and the fix was to write the tag rather than
  fake the coverage.
- Here the identical shape returned, in `C10-16`, and it was **created by this row's own change** — the
  `continue` was correct until 5.3.2-12 existed.

**What makes it dangerous rather than merely untidy:** a suite that goes green on a change it never
exercised is indistinguishable, from the outside, from a suite that verified it. That is the whole failure
mode standing constraint 8 exists against.

**Disposition: FIXED.** The `min_confidence` case is now handled explicitly and **raises** rather than
skipping — if a stale redirect ever answers `existing` above a caller's bar again, the id fails instead of
passing quietly. The superseded loop text is kept in a comment beside it.

**Residual, stated:** this row fixed the one instance it created. It did **not** sweep the suite for other
`continue`-guarded loop bodies that a later behaviour change could hollow out the same way. That sweep is
a real piece of work and it is named here rather than implied.

### §8.2 — **F2, MAJOR (mine, found by probe).** The read inherited the write door's blind spot

Recorded in full at [§7.2](#72--attack-1-is-verified-against-my-own-implementation-by-the-probe). Graded
here so it is counted: the first implementation of the action operand reused
`_action_declarations_diverge` and **WALK 3 still returned a clean 1.0**, because that function compares
four of `ACTIONS.md` §2.2's eight keys. The supervisor had raised exactly this as an attack before the
probe existed and I had recorded it as *"sound in principle and mostly moot."* **It was not moot.**

**Disposition: FIXED** (all eight declared keys, order-insensitive where §1 says unordered), with the Q99
coupling recorded as a residual rather than dismissed.

### §8.3 — **F3, MINOR.** Two published numbers the code did not derive

Recorded in full at [§7.1](#71--07-doing-the-job-it-exists-for-two-numbers-in-62-the-code-did-not-derive):
§6.2's S2 Jaccard was published as `1/3` and is `0.5`, and its claim that the ids *"assert the ordering
S2 < S1 < S0"* is false because Jaccard is symmetric.

**Disposition: CORRECTED, visibly**, with a marker left at §6.2 so the wrong numbers cannot be read
without the correction. The ordering question is parked as **`Q100`**. Graded MINOR because neither number
reached the spec, the code or a contract id — §0.7 caught both before they could.

### §8.4 — **F4, MINOR (process, mine).** Two reviewers were dispatched to mutate one shared working tree

I dispatched an adversarial panel in which **two** lenses were briefed to make temporary edits to
`ontoloche/registry.py` and revert them — in a tree **shared with the supervisor** and with a full suite
running against it. Their reverts would have interleaved and neither would have been provably clean, and
any suite result from that window would have been meaningless.

**Caught before either had mutated anything**, by me, not by a reviewer. Recovery: one lens was redirected
to verify by reading and told to say so rather than claim it had run a mutation; the suite run was
**stopped rather than allowed to report against a mutated tree**; and the four files were snapshotted so
the revert could be proved rather than trusted.

**The standing rule the supervisor has now stated out of this, recorded here so the next row inherits it:**
**only one agent mutates the shared tree at a time**, a mutation battery gets **exclusive** use of its
window, everything else in that window verifies by reading, and the supervisor is told before such a
battery is dispatched so it can keep off the tree.

**And a second-order finding the recovery itself produced, which is worth more than the original slip.**
The reviewer I redirected **treated my mid-flight correction as a probable prompt injection** and said so
in its report: the instruction arrived through a channel that was not its original brief, and it
*contradicted the task it had been given*. It declined to act on the instruction's authority, verified the
item by reading instead, and **explicitly reported that its verification was one grade weaker than asked
for** rather than letting the downgrade pass silently.

That is the correct behaviour and it is the reason the redirect was safe: **an out-of-band instruction that
narrows a reviewer's mandate is indistinguishable, from inside the reviewer, from an attempt to stop it
finding something.** The lesson is not that the reviewer was wrong. It is that **a mid-flight narrowing of
an adversarial brief is itself an adversarial-integrity hazard**, and the way to avoid it is to get the
dispatch right the first time — one mutator per window, decided before anything is dispatched — rather than
to correct it afterwards and hope the reviewer complies. Recorded because the next row will be tempted to
do exactly what I did.

---

## §9 — The adversarial loop

Panel mode, four fresh lenses per round, no reviewer reused, each dispatched cold with the artefact and
the bar and told nothing about who wrote it or whether it had passed anything.

### §9.1 — Round 1: **1 BLOCKING + 8 MAJOR** across four lenses

| lens | verdict | BLOCKING | MAJOR |
|---|---|---|---|
| the kill row | NOT YET | 1 | 1 |
| the truth of the row's own claims | NOT YET | 0 | 1 |
| consumer breakage | NOT YET | 1 (same one) | 3 |
| mutation and real coverage | NOT YET | 0 | 4 |

**Deduped: one BLOCKING and eight MAJOR.** Two lenses reached the BLOCKING independently from different
briefs, which is worth more than either report — the same thing row 6c recorded when two lenses collided
on `projection`'s pool.

**What the panel confirmed rather than found**, and it is worth stating because a review that only lists
faults is not a review: no caller inside the registry invokes `resolve_type`, so a lowered confidence
cannot leak into a write-side guard — **the primary kill-row question came back clean**. The vocabulary
counts held at **33** and **39**. `§0`'s git ancestry checked out. The A3 probe's `0.75` reproduced as six
of eight declared keys. And the three-id blast radius was verified by an independent broad grep.

### §9.2 — The BLOCKING, and the pattern the supervisor asked to have named

**`_identity_below_bar` listed the survivor TWICE.** The alias/near-miss branch builds `alternatives` from
the scored list, whose first entry is the winner itself; appending the survivor unconditionally produced
one word at two different confidences and made `known` count it twice. The exact-hit branch never
collided, because what *it* passes is the **dead** word — which is exactly why one call site broke and the
other did not, and why fixing only one would have been the register's own *one call site of N* shape.

**That is `C3-19`'s class, and `C3-19` is row 6d's finding X7** — *"every `alternatives` label must name a
ROW… a taken word is listed once, or `known` double-counts it."* Countersigned by the supervisor as **not
kill-row shaped**: nothing here merges a capability predicate or collapses two words to one identity, so
it is graded as this row's implementation defect and **not routed as a trip**. The count stays
**TWENTY-THREE**.

> **The pattern, which is the part worth a sentence.** Row 6d's convergence note records that **its own
> fixes became the largest single source of its findings** — in its round 3, ~20 of 30 findings were
> defects that row had introduced. Row 6f's single BLOCKING is its own change **reopening a class row 6d
> had already closed**. Two rows running, the sharpest defect in the row came from the row's own work
> rather than from the code it was sent to change. That is not a coincidence twice; it is what a build row
> does to a register that has already been swept — **the untouched code has been reviewed twenty-three
> times and the new code has been reviewed once**, and the loop is the only thing that levels that.

**None of my new ids caught it.** `C3-23` drove only the successor path; `C10-16` reached the alias path
and asserted `type is None` without ever inspecting `alternatives`. The id now asserts Rule K on **both**
call sites.

### §9.3 — The mutation lens, which was the round's most valuable and found FOUR survivors

Round 1's fourth lens ran nine mutations against this row's own rules. **Five were caught; four survived
the entire suite**, three of them on numbered rules 5.3.2-9, -10 and -12. A rule whose behaviour survives
its own mutation is a decorative rule, and row 4d proved that by deleting two rule rows with everything
green.

| mutation | round 1 | now killed by |
|---|---|---|
| `_unordered` → an order-**sensitive** list | SURVIVOR | `C3-24` |
| undeclared action family falls through the guard → **fully vouched** | SURVIVOR | `C3-25` |
| `_clears` treats an unscorable identity as clearing the bar | SURVIVOR | `C3-26` |
| `_compose` → `agreement` alone, dropping the resolver score | SURVIVOR | **see §9.4 — it is unpinnable** |

Each kill was verified by re-running the mutation and confirming a **named** id fails, then restoring from
a pristine copy and diffing to prove the restore. The `_unordered` survivor is the one that stings:
this row's own comment claims to be deliberately avoiding row 6d's round-3 defect — the one that **closed
a legal operation** for two rounds — and the protection was **unpinned**, so the claim was true of the code
and unenforced by anything.

### §9.4 — Chasing the fifth survivor produced a FINDING, not a test

`_compose`'s `min(score, agreement)` could be replaced with `agreement` alone and nothing failed. The
obvious response is a better fixture. **The obvious response is wrong here**, and finding out why is the
more useful result.

**[Observed]** by instrumenting the composition across every spelling that reaches a stale redirect:

| resolver | `_compose` called with |
|---|---|
| shipped `DeterministicResolver` | `(1.0, 0.5)`, `(1.0, 0.5)`, `(1.0, 0.5)` — the score is **always 1.0** |
| a custom resolver rating the alias `0.6` | **never called** — the branch is not reached at all |

The cause is the registry's own guarantee. `C3-11` made the redirect a **registry** promise precisely so
it would stop resting on *"the shipped scorer happening to rate an exact alias 1.0"* — and that guarantee
pins the score at 1.0 on exactly the hits that can go stale. So `min(1.0, J)` **is** `J`, and **no test can
distinguish the two implementations.** The branch is unreachable by construction rather than merely
untested, which is `5.3.2-5`'s own situation and gets `5.3.2-5`'s own disposal: a **`prose-only:`** tag
with the evidence in it.

**`C3-27` then pins the PRECONDITION rather than the tag's subject** — if a stale redirect ever arrives
scoring below 1.0, the `min` becomes observable, the tag's stated reason stops being true, and that id
fails and says so. That is the only useful thing an id can do about a branch that cannot be reached.

### §9.5 — The gate list was incomplete, and the SUITE is what caught it

This row reported *"all gates green"* against the three gates its brief named — `check_links`,
`check_spec_drift`, `check_merge_guard` — and that report was true. The full suite then returned **two
failures** in `test_manifest.py`, because **`check_capability_matrix.py` is a fourth standing gate** the
brief did not list, and because eight new contract ids existed as tests without being **enumerated** in
`PACKAGE.md` §6.2. The enumeration miss is this row's; the gate-list omission is the supervisor's and has
been corrected in the brief file.

> **The general rule, recorded so the next row inherits it: *"all gates green" is only as strong as the
> gate LIST, and a gate list is a claim that can be incomplete.*** Run the suite before believing a green
> board. An id that exists as a test but is not enumerated is an id nobody can hold a backend author to,
> which is the whole point of `PACKAGE.md` §6.2 — and nothing in the three-gate board could see it.

---

### §9.6 — Round 2: **3 BLOCKING + 4 MAJOR = SEVEN**, against round 1's NINE

Four fresh lenses, none reused, all **read-only** (round 1's collision, F4, is why). Round 1 had four
lenses and **none on the degraded leg**; round 2 added one, and it returned.

| # | grade | finding | lens | fixed |
|---|---|---|---|---|
| **R2-1** | **BLOCKING** | **Rule 5.3.2-9's `prose-only:` reason was FALSE.** A legal custom resolver makes the `min` observable | spec-vs-code | ✅ |
| **R2-2** | MAJOR | **Rule 5.3.2-4's unconditional *"answers at 1.0"* is false** on the alias door under a custom resolver | spec-vs-code | ✅ |
| **R2-3** | **BLOCKING** | **`_declaration_agreement` scored a key declared EMPTY equal to a key never declared** → a **clean 1.0** over two divergent action families | generalist | ✅ |
| **R2-4** | MAJOR | **A page-capped backend changes the ANSWER, not just the warning** — `existing` uncapped vs `none` capped at the same bar | three-leg | ✅ |
| **R2-5** | **BLOCKING** | **`C3-24` did not kill the mutation it was credited with** — it varies only `effects`, which uses a different helper | record-truth | ✅ |
| **R2-6** | MAJOR | **No final re-derived suite count** after §§7–9's changes | record-truth | ✅ §10 |
| **R2-7** | MAJOR | **`C3-25`'s stated mutant value was FABRICATED** — the real fall-through is `(True, 0.625)`, not `(False, 1.0)` | record-truth | ✅ |

MINORs, all taken: `scored` shadowing the near-miss list (renamed `composed`); the probe's stale
`left can never grow` comment; 5.3.2-13(a) not naming `stores_aliases=False`; the `stores_attributes=False`
total-degradation note.

**And one this row found against itself, outside the lenses — [§9.7](#97--the-matrix-regression-the-row-found-against-itself).**

### §9.7 — The matrix regression the row found against itself

`check_capability_matrix.py` is the **fourth** standing gate, which this row's brief did not list. Run
against a **baseline worktree at `f388cd1`** — a separate checkout, so the shared tree was never
disturbed:

| configuration | at `f388cd1` | in this row's tree |
|---|---|---|
| `stores_events=False` | **conformant**, 0 failed | **FAILS**, 2 failed |
| `indexes_membership=False` | **conformant**, 0 failed | **FAILS**, 3 failed |

**This row broke two declared-degraded legs**, and neither the three-gate board nor four round-1 lenses
saw it. The failures were **this row's own new ids**, not shipped behaviour: `retire(successor=)` refuses
`no_consumer_evidence` where the backend cannot report `gates_on`, and `merge_types(acknowledge=…)` refuses
`cannot_record_override` where there is no event store — so five fixtures' premises never held.

**Fixed with the sanctioned, AUDITED mechanism** rather than a skip in the body: `requires_capability`
markers naming what each fixture actually needs. That is the environment/result distinction §9.8 draws,
applied the moment it was available.

### §9.8 — The shape this row kept finding, at three levels

> **A thing that exists to catch a failure, and is itself the failure.**

- **`C10-16`** (F1): a `continue` that would have swallowed the new behaviour, in the id row 4d caught by
  mutation for that same defect.
- **`C3-26`**: `pytest.skip` on the very value it existed to assert. **Third occurrence** — row 4d in
  `C3-14`, round 1 in `C10-16`, and this row wrote it into a NEW id *in the round it graded the finding*.
- **This row's own MUTATION VERIFIER** (§9.9), which reported a kill that never happened.

**The distinction that makes it mechanically checkable, and it is the supervisor's:** *a skip decided by
the **environment** is legitimate; a skip decided by the **result** is never legitimate, because the result
is the thing under test.* The project already has the sanctioned path — `requires_capability`, which
`check_capability_matrix.py` audits — and **113 bare `pytest.skip(` call sites across 13 files that
nothing audits**, against **221 audited markers across 23 files**. The watched path is the dominant one;
all three known instances took the unwatched one. *(Counts the supervisor's, re-derived after it corrected
its own first figure of 114.)* **Routed as a follow-on row, explicitly NOT this row's** — a census checker
over 113 call sites is new tooling on a surface this row was not sent to touch.

> ### ⚠ The two-way distinction above is INCOMPLETE. There is a THIRD category.
>
> **Corrected after landing, by the supervisor running its own checker against `daa86e7` rather than
> re-reading the rule.** Its script reported *"result-conditioned skips left: 6"* in
> `test_c3_resolve_type.py`; it then classified them **by hand instead of publishing the number**, and the
> number was wrong — it had counted every `pytest.skip`, not the result-conditioned ones. **[Observed]**,
> re-derived here, the six are:
>
> | line | guard | category |
> |---|---|---|
> | 472 | `if not registry.caps.indexes_membership` | **ENVIRONMENT** — legitimate |
> | 1201 | *(a comment describing the skip this row FIXED)* | not a skip |
> | 689 | `if not written or "boro_nm" not in aliases` | **SETUP RESULT** |
> | 694 | `if isinstance(gone, Refusal)` — did `retire` refuse | **SETUP RESULT** |
> | 1430 | `if isinstance(out, Refusal)` — does the write door refuse | **SETUP RESULT** |
> | 1294 | `if answer.type is None or answer.type.name != "searchable"` | **BORDERLINE — and it is in `C3-27`, this row's own new id** |
>
> **A skip that reads the result of a SETUP step is the missing middle**, and it is not obviously
> illegitimate: a fixture that cannot be built on this backend genuinely has nothing to assert. So
> *"reads a result"* is **too blunt to be a checker's rule** — a gate built on the two-way version would
> have flagged five and been wrong about three.
>
> **The line needs drawing between the value UNDER TEST and the preconditions of the fixture**, and the
> borderline at 1294 shows the boundary is not crisp: it reads `answer.type` from the call under test, but
> what it is asking is *did this leg pose the question at all*. This row does not settle it — the three-way
> distinction goes into the census row's brief, which is where a rule that has to survive 113 call sites
> belongs.
>
> **And it is this row's own §9.11 method failure, committed by the supervisor and named as such by it:**
> a rule generalised from three clean instances that did not survive contact with the fifth, **caught by
> running it rather than by re-reading it.** Two parties, one day, the same error — which is the argument
> for the rule being written down rather than for either party being more careful.

### §9.9 — A finding against this row's own tooling

Round 1's mutation script reported **`CAUGHT M5 … by test_c3_24`**. That kill never happened.

The script did `s.replace("        return frozenset(out)", …)` with no count limit, and that line exists in
**both** `_unordered` and `_effect_identities`. It mutated **both helpers at once** and credited the kill
to the wrong one — `C3-24`'s fixture varied only `effects`, which is compared by `_effect_identities`.
`_unordered` was never exercised, so rule 5.3.2-10's order-insensitivity for `inputs`, `preconditions` and
`reachability` **remained decorative while this row reported it pinned.** Confirmed by mutating line 1480
alone: `C3-24` passed.

**A mutation-kill verifier that does not verify is §9.8's shape one level up**, and it is worse than the
defects it was auditing, because every verdict it produced inherits its error. Round 2's replacement is
**line-anchored and count-asserted** — it declares how many lines a needle should match and fails loudly
otherwise, which is how the ambiguity was caught the second time.

**Recorded as a finding, not fixed in passing.** The row published a kill table it had not established.

### §9.10 — R2-3's classification. **Routed, and ruled by the supervisor. NOT self-graded.**

**It is NOT a kill-row trip and NOT a governance-register entry. The count stays TWENTY-THREE and the
register stays ONE.** The reasoning is the supervisor's and is recorded because a classification without
one is a preference:

- **Not kill-row.** **A3 is precisely this shape** — action families, declarations conflated, the collapse
  succeeds, a clean 1.0 follows — and **R91** and **R97** already ruled that shape *out* of the kill row
  and into the governance register, for the stated reason that a count growing on a widening definition
  stops being a signal. Grading R2-3 a trip would overturn R97 by the back door.
- **Not a register entry either.** The register counts **harms, not mechanisms**, and this is A3's harm by
  a third route. And decisively: **R2-3 never shipped.** It was introduced and caught inside one row,
  before landing. A register that logs defects caught in development stops being a signal about shipped
  governance and becomes a defect log — R97's own failure in a different dimension.

It stays a **graded BLOCKING finding of this row against itself**.

**And the naming, corrected by the supervisor, because precision is 6e's whole lesson.** This record first
called R2-3 *"a live statement `E`."* **It is not.** `E` is specifically *the registry treats a fact
checked at WRITE time as true at READ time*. R2-3 is a **comparison** defect — *declared empty* scored
equal to *never declared* — with no write-time/read-time confusion in it. What it genuinely is, and this is
worse rather than better: **a member of `E`'s own family**, which `INTERFACE.md` §5.3 has already named in
its own words — *"a confident answer standing in for a fact the system had or could not have"* — and where
§5.3 counts it as *"the third time this loop found the same error."* Calling every family member by the
family's most famous member is how a name widens until it distinguishes nothing: **the naming form of the
counting failure R97 ruled against.**

**What still damns it, put properly: the operand this row added to remove `E`'s DELIVERY contained a defect
from `E`'s own family.** That is [§9.8](#98--the-shape-this-row-kept-finding-at-three-levels)'s shape at a
**fourth** level — and the first three were tests and tooling, while this one is **product code**.

### §9.11 — CONVERGENCE NOTE: the loop did **NOT** converge, and the row lands **NOT CLEAN**

> ## The single most important thing this row found is a METHOD failure, and it is this row's own
>
> **TWICE this row generalised a conclusion from a SINGLE measurement and PUBLISHED it — and the
> second time happened AFTER the first had already been recorded as a finding.**
>
> - [§9.9](#99--a-finding-against-this-rows-own-tooling): one unanchored `str.replace` matched two
>   helpers; the row read a single kill report and published a mutation table it had not established.
> - [§9.6](#96--round-2-3-blocking--4-major--seven-against-round-1s-nine) R2-1: one resolver score was
>   instrumented, `_compose` was not called, and the row concluded the branch was *unreachable by
>   construction* — then used that conclusion to REMOVE a contract id. It is reached for every score
>   from 0.9 to 1.0.
>
> **It is put first because it is the only finding here that would have kept producing NEW defects if
> it had gone unnamed.** Every other item on the list is a defect, or a consequence of this one, or of
> the environment. A defect is fixed once; a method that manufactures defects keeps paying out.
>
> **No gate caught either instance. Both were caught by somebody RE-RUNNING rather than re-reading**
> — a fresh lens with a custom resolver, and a lens that traced a fixture to the helper it actually
> exercises. That is the argument for the loop in one sentence, and it is also the argument against
> trusting this row's remaining unverified claims more than the evidence behind them.


| round | lenses | BLOCKING | MAJOR | total |
|---|---|---|---|---|
| 1 | kill-row · truthfulness · consumer · mutation | 1 | 8 | **9** |
| 2 | spec-vs-code · record-truth · three-leg · generalist | 3 | 4 | **7** |

**Nine then seven is not convergence, and the honest reading is weaker still than that — in the direction
that makes stopping MORE clearly right.**

> **Round 1's nine is not a trustworthy number.** [§9.9](#99--a-finding-against-this-rows-own-tooling)
> establishes that round 1's mutation verifier did an unanchored replace, mutated two helpers at once and
> credited the kill to the wrong one. So round 1's *"five caught, four survived"* was produced by an
> instrument this row has since **proved broken**. Presenting `9 → 7` as a shrinking trend would be
> comparing a **bad number to a good one**.

What can be said without an instrument problem is worse than the trend: **round 2 — measured with a
verifier that works — found THREE BLOCKINGs in code four round-1 lenses had already passed**, and one of
them was inside a fix round 1 produced. **Two of the three falsified this row's own published reasoning**,
by the same error twice: generalising a conclusion from a single measurement (§9.9's unanchored replace,
and §9.6's one-resolver-score instrumentation). The lenses are still returning first-order defects in the
newest work. That says the work is **young**, not that the loop is exhausted.

**So the row STOPS rather than finishes, per the brief's own instruction** — *"findings that do not shrink
means stop rather than finish, and say so."* This is the saying-so.

**Stop-not-clean means LAND, not abandon**, which is row 6d's precedent: it landed NOT CLEAN at the cap
with its convergence note carrying the cost. The work is worth landing — **A3's delivery is removed, the
guarantee is amended, and every finding from both rounds is fixed with eight of eight mutations killed.**
What is *not* available is the claim that this is clean, and it is not claimed.

**What a third round would most likely find**, stated so the next reader can check whether this row
guessed right rather than being told it converged:

1. **More of the degraded legs.** One lens covered three legs, once. §9.7 shows what the first look there
   cost, and no lens has yet driven the ACTION operand across every declined capability.
2. **The `_declaration_agreement` neighbourhood again.** Two rounds found two defects in it, and it is the
   newest and least-reviewed code in the change.
3. **Whichever of this row's own claims has not yet been re-derived by a command.** The record has been
   wrong four times by that test alone (§7.1's two, §9.3's credit, §9.6's R2-7), and every one was found by
   somebody re-running rather than re-reading.

### §9.12 — The best process result of the day, and it was not a lens

**The matrix regression (§9.7) was found by BASELINING, not by review**, and the method is recorded because
the next row should copy it rather than the conclusion.

Two declared-degraded legs were failing. The question *"is this mine or pre-existing?"* cannot be answered
by reading, and the working tree is shared with the supervisor so it cannot be stashed. **A `git worktree`
at the last landed commit is the answer**: a separate checkout at `f388cd1`, the same gate run there, and
the comparison is then a measurement rather than an argument. It returned **conformant / 0 failed** on both
legs, which converted *"probably pre-existing"* into *"this row broke them"* in one run.

**Neither the gate board nor four lenses had seen it**, because the brief listed three gates and the fourth
was the one that could. The rule that came out of it is the supervisor's and is in §9.5: *"all gates green"
is only as strong as the gate LIST, and a gate list is a claim that can be incomplete.*

**And the fix used the audited mechanism rather than the convenient one** — `requires_capability` markers
naming what each fixture needs, which `check_capability_matrix.py` tallies — instead of a skip inside the
test body that nothing counts. That is §9.8's environment-versus-result distinction applied **the same day
it was written down**, which is the only real test of whether a lesson took.

---

## §10 — Every number, re-derived by its defining command LAST

§0.7 requires it and round 2's **R2-6** found the record had stopped short of it: §9.5 ended on an admitted
two-failure state with no rerun, leaving §1's *"this row never drops below the floor"* unconfirmed at the
point the document ended. This section is that rerun.

### §10.1 — The four gates

| gate | result |
|---|---|
| `py docs/tools/check_links.py` | **exit 0** — every relative markdown link resolves |
| `py docs/tools/check_spec_drift.py` | **exit 0** — and every numbered rule in `INTERFACE.md` §5.3.2 carries a contract id or a tagged reason (constraint 8 / R31) |
| `py docs/tools/check_merge_guard.py` | **exit 0** — the STALE axis amended by R99, which used to *require* the 1.0 this ruling removed |
| `py docs/tools/check_capability_matrix.py` | **exit 0** — *"Every optional capability can be declined alone and the backend still conforms."* **This is the gate the brief did not list**, the one that caught §9.7's regression, and it is green again |

### §10.2 — The three legs

```
OO_POSTGRES_DSN=postgresql://postgres:openontology@localhost:55432/open_ontology py -m pytest -q --pyargs ontoloche.contract
OO_POSTGRES_DSN=postgresql://postgres:openontology@localhost:55432/open_ontology py -m pytest -q --pyargs ontoloche.aio.contract
```

| leg | floor at `396bf02` (§1) | **at this row's landing** |
|---|---|---|
| sync | 912 passed, 301 skipped | **932 passed, 311 skipped in 648.30s (0:10:48)** |
| async | 949 passed, 301 skipped | **969 passed, 311 skipped in 390.97s (0:06:30)** |
| degraded | *(the matrix gate above, every optional capability declined one at a time)* | **conformant on all of them** |

**The floor holds.** §1 pre-committed that this row never drops below it and it did not.

**Read the two deltas, because they are the row's own story in two numbers.** The **+20 passed** is the ten
new ids across two backends. The **+10 skipped** is the `requires_capability` markers round 2 added to fix
[§9.7](#97--the-matrix-regression-the-row-found-against-itself)'s degraded-leg regression — and **a skip
that DECLARES itself is not the defect §9.8 is about.** These ten are counted by
`check_capability_matrix.py`, which is what makes them coverage bookkeeping rather than coverage loss; the
113 bare `pytest.skip(` call sites nothing audits are the other thing entirely.

**One cost this run added, measured rather than quoted.** `oo-pg` held **625** `oo_*` schemas this morning
and **741** after this row's postgres legs — **this row added 116**. That is the founder's open decision
(item 10) and this row does not re-raise it; the number is here because §0.7 says a number in this record
is the one that was observed, and because the cost is growing under measurement rather than sitting still:
193 in row 6c, 476 on 2026-09-05, 625 this morning, **741 now**.

### §10.3 — The contract-id census

| | before | after |
|---|---|---|
| `C3` group | 19 | **29** |
| suite total | 399 | **409** |
| `Refusal.reason` | 33 | **33 — unchanged** |
| `warnings` | 39 | **39 — unchanged** |

**Ten new ids** — `C3-20`…`C3-29` — of which **four came from the build and six from the two adversarial
rounds**, and that split is the row's own story. **No new vocabulary value was minted in either closed
vocabulary**: `identity_stale` gained a carrier rather than growing a twin, which is ruling **R71**'s
precedent and the thing a closed vocabulary exists for.

Every one of the ten is enumerated in [`PACKAGE.md`](../specs/PACKAGE.md) §6.2 — which round 2 found it was
not, because `test_the_suite_implements_every_enumerated_contract_id` said so and the three-gate board
could not.

### §10.4 — Mutation coverage, re-run with a verifier that works

§9.9 established that round 1's verifier mutated two helpers at once and credited a kill to the wrong one.
Re-run **line-anchored and count-asserted**, one mutation at a time, each restored from a pristine copy and
diffed to prove the restore:

| mutation | verdict |
|---|---|
| `_unordered` → order-sensitive (that line **only**) | **CAUGHT** — `C3-24` |
| `_effect_identities` → order-sensitive (that line **only**) | **CAUGHT** — `C3-24` |
| absent-vs-present counted as agreeing | **CAUGHT** — `C3-29` |
| key set derived from the rows again, not the fixed eight | **CAUGHT** — `C3-29` |
| `_compose` → `agreement` alone *(round 1's survivor)* | **CAUGHT** — `C3-27` |
| `_compose` → `score` alone | **CAUGHT** — `C10-16` |
| `_clears` → an unscorable identity clears the bar | **CAUGHT** — `C3-26` |
| unknowable answers `0.0` instead of `None` | **CAUGHT** — `C3-26`, `C3-28` |

**Eight of eight. Zero survivors.** Round 1 reported five of nine with an instrument that was wrong about
at least one of them; this is the number that stands.
