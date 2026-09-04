# 7A-RUN — roadmap row 7a: `docs/specs/INGEST.md` v0, the Layer B / Phase 3 ingestion-mapping SPEC row

**Status:** in flight. **Row:** Phase 3's first row, opened by the founder 2026-09-02
([`docs/decisions/2026-09-02-phase3-repoint-R77-R78.md`](../decisions/2026-09-02-phase3-repoint-R77-R78.md)).
**Constraints cited by the brief:** **R58** (the façade pages under one rule for `known`; a guard never
reads a page), **R59** (tenant-blind protocol; tenancy is the host's predicate), **R60** (one three-valued
`Condition` language, the ingestion loop its first consumer), **R77** (instance resolution is Phase 3's and
`resolve_type` is never extended to cover it), **R78** (the host holds the instances — *deliberately
falsifiable, and design test 1 is what may falsify it*).
**This row ships no product code.** Its probes live under `docs/tools/`, exactly as
[`actions_nyc_probe.py`](../tools/actions_nyc_probe.py) did for row #6.
**Suite floor at the row's start:** 366 ids, sync 837 / async 874, three legs. This row must not disturb it.

Claims are tagged **[Observed] / [Inferred] / [Assumed]**.

---

## 0. Design test 1's expectations — **PRE-REGISTERED, written before the probe existed**

`USE-CASES.md`'s validation protocol requires expected outcomes stated *before* the walk-through. This
section is committed in its own change, ahead of [`docs/tools/ingest_seam_probe.py`](../tools/ingest_seam_probe.py),
so the pre-registration is checkable in `git log` rather than asserted in prose.

**The question, and it is R78's:** does this project become an instance store, or does it define resolution
*over instances the host already holds*? **Pass** = every outcome of `resolve_instance` is reachable with a
host-side table and a candidate-retrieval primitive, and **no instance row is copied into the registry**.
**Fail** = write why and stop; the supervisor rules before any section of `INGEST.md` is written.

### 0.1 The fixture, pinned from the real file

**[Observed] 2026-09-03**, `NH_HealthCitations_Aug2026.csv` re-downloaded from the CMS Provider Data
Catalog (`https://data.cms.gov/provider-data/dataset/r5ix-sfxw`, distribution `modified: 2026-08-01`) —
**165,336,194 bytes, 419,479 rows, 14,627 CCNs, 14,498 distinct provider names, 104 names shared by more
than one CCN.** All four numbers reproduce `USE-CASES.md`'s pre-registered figures exactly. The checked-in
400-row Montana sample carries **10** facilities and **zero** shared names, so it cannot pose this test and
the full file is used, as the brief anticipated.

| # | candidate | what the file says **[Observed]** | expected outcome |
|---|---|---|---|
| T1.1 | `"BURNS NURSING HOME, INC."` | exactly one CCN — `015009` | **`existing`**, confidence at the top of the range |
| T1.2 | `"MILLER'S MERRY MANOR"` | **twelve** CCNs, all Indiana, all distinct facilities | **`ambiguous`** — never `existing` at 1.0, and never a proposal |
| T1.3 | a provider name absent from all 419,479 rows | no CCN | **`proposal`** |
| T1.4 | `"Provider Name"` — the column header, landed as a value | not a facility at all | **`not_an_instance`** |
| T1.5 | T1.1's candidate with the host's scan **truncated before its row** | the match exists and was not read | **the open question this test decides** — see 0.2 |

`"MILLER'S MERRY MANOR"` is the sharpest available case and it is why this fixture was chosen over the
104's alphabetical first: twelve facilities in one state answering to one string is `INTERFACE.md` §10.3's
finding at its maximum, and it is the exact shape of the kill row one level down — *two instances answering
to one identity*.

### 0.2 The one thing this test is expected to decide beyond pass/fail

The brief offers `existing` / `proposal` / `ambiguous` / `not_an_instance` — four, mirroring `resolve_type`
— and invites a different closed set to be argued. **T1.5 is the case that decides it.** R58 makes the
candidate primitive page, so a scan can end without having read the row that would have matched. Under a
four-outcome set that scan has nowhere to land but `proposal`, and a proposal is how a second row for one
facility gets created. **Predicted [Inferred]: the four-outcome set is not closed under Rule U and a fifth,
`unknowable`, is required** — with the whole point being that it is an *outcome* and not a flag, because a
flag beside `outcome="proposal"` is a caller's to ignore.

**Recorded as a prediction, not as a finding.** If T1.5 lands cleanly in one of the four, the fifth is not
taken and this paragraph is the record of a wrong guess.

### 0.3 What is asserted about the seam itself

1. The registry is the **shipped** `ontoloche.Registry` on SQLite — so *"no instance rows"* is a claim about
   the real store, not about a probe kit. After the whole walk-through, the store's type table is
   enumerated and must hold **only** `kind="entity"` vocabulary rows.
2. The host table is reached **only** through the candidate primitive. The probe holds it to
   `PACKAGE.md` §3.1's adapter boundary by source inspection, the way `C0-04` and
   `edges_probe_kit.assert_adapter_boundary()` do: the host-side object may not name a façade shape.
3. Nothing in the walk-through calls `resolve_type` on an instance string. **R77 is non-negotiable** and
   the probe asserts the separation rather than assuming it.

---

## 1. Design test 1 — **the R78 seam. VERDICT: CONFIRMED.**

**Probe:** [`docs/tools/ingest_seam_probe.py`](../tools/ingest_seam_probe.py). **Run 2026-09-03,
16/16 checks pass, exit 0.** Two engines, as `actions_nyc_probe.py` uses them: the **shipped**
`ontoloche.Registry` on SQLite holds the vocabulary — so *"no instance rows"* is a claim about the real
store — and the host table plus `resolve_instance` are throwaway kit, because this row ships no product code.

### 1.1 Observed output, pasted

```
DESIGN TEST 1 -- the R78 seam, over CMS `NH_HealthCitations_Aug2026.csv`
  source: https://data.cms.gov/provider-data/dataset/r5ix-sfxw
  file: 165336194 bytes, 419479 rows
  host table: 14627 CCNs, 14498 distinct provider names, 104 names shared by more than one CCN
  [PASS] the pre-registered CMS figures reproduce
  [PASS] the host table names no facade shape (PACKAGE 3.1, C0-04's rule)

  R77 control -- resolve_type('BURNS NURSING HOME, INC.')
    -> outcome='not_a_type' reason='instance_not_type'
  [PASS] R77: the type registry refuses the instance question rather than answering it

T1.1 -- 'BURNS NURSING HOME, INC.' (one CCN in the file)
  -> outcome='existing' ref_key='cms:entity:facility#015009' confidence=1.0 scanned=14627 complete=True

T1.2 -- "MILLER'S MERRY MANOR" (twelve CCNs in the file)
  -> outcome='ambiguous' known=12 confidence=1.0
       cms:entity:facility#155049  1.0  WARSAW, IN
       cms:entity:facility#155102  1.0  PLYMOUTH, IN
       cms:entity:facility#155173  1.0  MARION, IN
       cms:entity:facility#155235  1.0  LOGANSPORT, IN
       cms:entity:facility#155299  1.0  PORTAGE, IN
       cms:entity:facility#155557  1.0  INDIANAPOLIS, IN
       cms:entity:facility#155564  1.0  MOORESVILLE, IN
       cms:entity:facility#155574  1.0  WALKERTON, IN
       cms:entity:facility#155578  1.0  NEW CARLISLE, IN
       cms:entity:facility#155579  1.0  HOPE, IN
       cms:entity:facility#155583  1.0  GARRETT, IN
       cms:entity:facility#155589  1.0  CULVER, IN
  [PASS] T1.2 ambiguous, never `existing`, and all twelve are handed back
  [PASS] T1.2 no ref_key: nothing answered for twelve facilities at once

T1.3 -- 'ONTOLOCHE MEMORIAL CARE CENTER', absent from all 419479 rows
  -> outcome='proposal' confidence=0.8 scanned=14627 complete=True

T1.4 -- 'Provider Name', the column header landed as a value
  -> outcome='not_an_instance' scanned=0

T1.5 -- 'Tuskegee Airmen Texas State Veterans Home', whose row is 14,623 of 14,627,
        with the host's scan capped at 14000
  five-outcome set -> outcome='unknowable' complete=False scanned=14000
                      why='host scan cap of 14000 rows reached; the rest of this
                           table cannot be read from this surface'
  four-outcome set -> outcome='proposal' complete=False
                      reason='nothing in the scanned rows matched'
  uncapped control -> outcome='existing' ref_key='cms:entity:facility#745057' confidence=1.0

T1.6 -- R58's three states off one primitive
     the set: known=14627 complete=True  next_after=None     why=None
      a page: known=500   complete=False next_after='045350' why=None
   truncated: known=14000 complete=False next_after=None     why='host scan cap of 14000
                                                                 rows reached; ...'

T1.7 -- what the registry holds after all of it
  registry rows: [('entity', 'facility')]

==============================================================================
16/16 checks pass
R78 VERDICT: CONFIRMED -- every outcome is reachable over a host-held table,
             through two read primitives, with no instance row in the registry.
```

### 1.2 What the verdict rests on, stated so it can be attacked

**R78 is CONFIRMED, and the confirmation is narrower than *"an instance store is unnecessary."*** What
was tested is that **every outcome of the resolution call is reachable** with (a) a table the host owns,
(b) two **read-only** adapter primitives, and (c) no instance row in the registry — **[Observed]**, T1.7:
after a walk-through that scanned 14,627 host rows five times, the shipped store holds exactly
`[('entity', 'facility')]`, and no CCN and no provider-name string appears in it. What was **not** tested
is write-side ingest at volume; that is §4's contract and the build row's problem.

**Three things the run established that were not asked for, and that change what §1–§5 may say:**

1. **R77 is already enforced by shipped code, not merely declared.** `resolve_type("BURNS NURSING HOME,
   INC.")` returns `outcome='not_a_type'` with reason **`instance_not_type`** — a `NotAType` branch that
   has been in [`ontoloche/_resolve.py`](../../ontoloche/_resolve.py) since row #1. **[Observed]** The
   type registry does not merely decline the instance question; it **names** it, which means the pointer
   `INGEST.md` adds to `INTERFACE.md` §1 has a call-level counterpart already live. *The seam's type-side
   half was built before the seam was.*
2. **The primitive count is TWO, not three, and the difference is the seam.** `EDGES.md` §7.1 and
   `ACTIONS.md` §9 each take three — `put` / `get` / `find` — because this project **stores** edges and
   invocations. Instances are the host's, so there is no `put`, and **two read primitives is the
   strongest available evidence that R78 holds**: a protocol that needed a third would be an instance
   store with a different name. §2 takes the two.
3. **The four-outcome set is NOT closed under Rule U, and T1.5 constructs the failure rather than arguing
   it.** With the fifth outcome absent, a scan cut off before the matching row returns
   `outcome='proposal'` for a facility that **exists in the same table** — `cms:entity:facility#745057`,
   confirmed `existing` at 1.0 by the uncapped control in the same run. That is the pollution machine
   with a governance loop bolted to the front of it: the proposal is well-formed, provenance-bearing,
   approvable, and wrong. §3 therefore takes **five** outcomes, and the fifth is an **outcome** rather
   than a flag beside `proposal`, because a flag is a caller's to ignore and an outcome is not.

**The prediction pre-registered in §0.2 held.** It was written at `a1b0364`, before the probe existed,
and is recorded as a prediction that came true rather than as a finding discovered by looking.

### 1.3 The kill row, checked at this row's own surface — and it is why `ambiguous` is decided FIRST

`ROADMAP.md`'s kill criterion is *two things answering to one identity*. T1.2 is that criterion one level
below where the fourteen trips live: twelve genuinely different Indiana facilities answer to the string
`"MILLER'S MERRY MANOR"`, every one of them scoring **1.0** on the name. A resolver that took the top
candidate would return `existing` at 1.0 — **the confidence `INTERFACE.md` §5.3 calls a guarantee** — and
silently file eleven facilities' citations into a twelfth's record.

**So the ordering inside the call is a rule, not an implementation detail:** ambiguity is decided
**before** existence, and a tie inside the margin can never collapse to its first member. The probe
asserts the negative (`ref_key is None`) as well as the positive, because *the outcome was right and the
ref was populated anyway* is the shape trips eleven and twelve took.

### 1.4 What would overturn this verdict

Stated now, so a later reviewer has something to aim at rather than a conclusion to admire.

| what arrives | what it overturns |
|---|---|
| a host whose table cannot be scanned at all — no `find`, only `get` by key | **R78.** Resolution needs candidates; a host that can only confirm a key it is already given cannot supply them, and the choice becomes an ontoloche-side index (still not a store of record, but a store) |
| an ingest volume where scanning the host per landed row is not affordable | not R78, but §2's primitive: it would need a blocking/keying argument, which is a **build-row** measurement and is raised as a question rather than designed here |
| the propose-at-ingest contract needing to hold an approved instance before the host writes it | **R78 at the write side**, which this test did not exercise. §4 is written to avoid it; see §4's own statement of what it refuses to store |

---

## 2. Design test 2 — **paging under load (R58). 10/10, live against `erm2-nwe9`.**

**Probe:** [`docs/tools/ingest_paging_probe.py`](../tools/ingest_paging_probe.py). The host is
**Socrata itself**, not a fixture: `$limit`/`$offset` are its own paging, so the primitive is a thin
adapter over them and the cursor is opaque exactly as R58 leaves it.

```
2.1 the node                                   measured 2026-09-03
  rows in the dataset : 22,345,358   (row #4, 2026-08-29: 22,294,072)
  agency='NYPD'       : 9,764,249    (row #4, 2026-08-29:  9,738,128)
  drift since row #4  : +51,286 rows, +26,121 on the partition

2.2 R58's three states, live
  host narrowing      : agency='NYPD' AND complaint_type='Illegal Fireworks'
                        AND incident_zip='11214'
  narrowed partition  : 725 rows -- 13,468x smaller than the node
     the set: known=725  complete=True  next_after=None  (0.58s)
      a page: known=200  complete=False next_after='200' (0.25s)
   truncated: known=1000 complete=False next_after=None
              why='scan budget of 2000 rows reached in 2 host requests; the
                   partition continues past this surface'
              (read 2000 of 9,764,249 rows in 2 host requests)

2.3 the exhaustive read the guard would need
  one 50000-row page took 1.26s and returned 50000 rows
  exhausting agency='NYPD' at the host's ceiling needs 196 requests
  [Inferred] lower bound: 4.1 minutes FOR ONE LANDED ROW

2.4 -> outcome='unknowable' for a candidate resolved against the whole partition
  the same read over the HOST-NARROWED partition drains to exhaustion:
  725 rows in 4 requests, complete=True
10/10 checks pass
```

**Two of those lines are findings and one is a correction.**

1. **Row #4's pinned figures have MOVED, and the probe asserts that they moved.** `EDGES.md` §4.2 and
   R58 both cite **22,294,072 / 9,738,128**, **[Observed] 2026-08-29**. Five days later the same two
   queries return **22,345,358 / 9,764,249**. Nothing is wrong with either measurement — `erm2-nwe9` is
   a live feed — but a spec that cites a live count as though it were a constant will be wrong on a
   schedule. **`INGEST.md` cites the date with every number it takes from this dataset**, and the probe
   makes the drift a `[PASS]` rather than a surprise.
2. **An exhaustive candidate scan of the pre-registered node is not affordable per landed row.**
   **[Observed]** one 50,000-row page (the host's own ceiling) at 1.26s warm — the first, cold, took
   **13.86s** — and 196 pages to exhaust the partition. **[Inferred]** 4.1 minutes at the warm rate, ~45
   at the cold one, and both ignore deep-`$offset` decay, so both are lower bounds. **For one landed
   row.** A loop that lands ten thousand rows cannot pay it once, let alone ten thousand times.
3. **So the primitive's affordability is a fact about the HOST's table, and the narrowing is the host's
   to declare.** The same read drains to exhaustion in **four requests** once `agency` +
   `complaint_type` + `incident_zip` narrow 9,764,249 rows to **725**. `INGEST.md` §2 therefore gives
   the candidate query a **host filter that is opaque to this project** — the host's own predicate over
   its own indexed columns — and states that this project neither invents it nor validates it.

**And this is where *a guard never reads a page* bites at this row's surface.** The ambiguity decision
is an identity read (§1.3), so it may not run on a page. Over `agency='NYPD'` unnarrowed the exhaustive
read cannot finish, so the outcome is **`unknowable`** — design test 1's fifth value, arriving at scale
from a completely different direction. Design test 1 constructed it from a fixture cap; design test 2
gets it from a real 9.7-million-row partition and a real API ceiling.

---

## 3. Design test 3 — **the two-tenant loop (R59 / R60). 12/12, over CMS CA + CO.**

**Probe:** [`docs/tools/ingest_condition_probe.py`](../tools/ingest_condition_probe.py). **The fixture
is the sharpest the CMS file offers: [Observed]** 84 provider names are shared across more than one
state, and **California and Colorado share five of them** — the largest pair. Two tenants, **one
store**, five names both tenants answer to: if tenancy leaks, it leaks here.

```
  one store: 1373 facilities -- 1164 ca-host, 209 co-host
  provider names BOTH tenants answer to: 5
     'BRIGHTON CARE CENTER'  'DEVONSHIRE CARE CENTER'  'SAN LUIS CARE CENTER'
     'VALLEY VIEW CARE CENTER'  'WESTWOOD POST ACUTE'

3.1 primitive signature: find_instance_candidates(self, q: CandidateQuery) -> CandidatePage
    [PASS] the candidate primitive takes NO tenant parameter -- R24 / R59 intact

3.2 e.g. 'BRIGHTON CARE CENTER'
     ca-host: outcome='existing' ref='cms:entity:facility#555338'
              considered=1373 excluded_by_predicate=209
     co-host: outcome='existing' ref='cms:entity:facility#065240'
              considered=1373 excluded_by_predicate=1164
    [PASS] NO cross-tenant candidate reached either answer
    [PASS] each host saw the WHOLE store and the predicate did the excluding

3.3 a predicate over 'ownership_type' -- an attribute no column carries
     -> outcome='unknowable' undecidable=1373 excluded_by_predicate=0
        why='the host predicate was undecidable on 1373 of 1373 candidates'

3.3b unknowable-as-FALSE: 1373 excluded, 0 survive -> propose a NEW facility for one
                          that exists (mechanism C, and the pollution machine)
     unknowable-as-TRUE : 2 survive across ['ca-host','co-host'] -> cross-tenant leak,
                          which is R59's own reversal condition

3.4 eq over a NULL readable attribute -> holds=None
    is_null over the same             -> holds=True

3.5 REFUSED a thirteenth term / eq against a null operand / an empty `why` /
    a combinator with no terms / `in` against a scalar

3.6 all_of(T,U)=None  all_of(F,U)=False  any_of(T,U)=True  any_of(F,U)=None
12/12 checks pass
```

**Four things this decided, and 3.3b is the one that decided the most.**

1. **R59 holds and the protocol stays tenant-blind — literally.** The primitive's signature is
   `find_instance_candidates(q: CandidateQuery) -> CandidatePage`; the word *tenant* is not in it, the
   store it offers is the whole store, and **[Observed]** each host `considered=1373` of 1373 rows. The
   separation is not that the host hid rows; it is that **the predicate did the excluding, above the
   primitive, where it is enumerable.**
2. **Both two-valued readings of `unknowable` are real failures, and the probe constructs both rather
   than arguing them.** Read as **false**, all 1,373 candidates are excluded and the loop proposes a new
   facility for one that exists — mechanism C, and the pollution machine with a governance loop in front
   of it. Read as **true**, two candidates survive across *both* tenants — a cross-tenant leak, which is
   R59's own stated reversal condition. **The third value is not a preference; it is the only reading
   that is neither of those two.**
3. **`eq` against null is `unknowable`, and `is_null` is a separate operator, because SQL says so.** A
   host implementing this predicate in SQL gets `x = NULL` → UNKNOWN; a registry that answered `False`
   would disagree with the host executing its own gate. Two operators, one fact each: `INTERFACE.md`
   §2.3's Cause B avoided at the operator level. **[Observed]** in 3.4.
4. **Twelve terms, and the count is derived from what the fixtures forced.** Ten operators over one
   record's attribute values — `eq` `ne` `in` `not_in` `lt` `lte` `gt` `gte` `is_null` `is_not_null` —
   and two combinators, `all_of` / `any_of`, composed by **Kleene** three-valued logic so a partly
   unreadable predicate still decides what it can. **No `not`**: negation is available only as `ne` /
   `not_in` over a named attribute, so a caller cannot build an unbounded negation, and `not(unknowable)`
   never has to be argued about.

---

## 4. Design test 4 — **"I already know 38 of these". 7/7, over live 311 rows.**

**Probe:** [`docs/tools/ingest_gate_probe.py`](../tools/ingest_gate_probe.py). `ROADMAP.md` homes
instance resolution in Phase 3 with the walkthrough's *"I already know 38 of these"*. The batch is 100
real rows out of the 311 partition design test 2 narrowed: **38 already held exactly, 24 held but landing
in an abbreviated spelling, 38 genuinely new.**

```
  400 rows fetched, 271 with a distinct address
  host holds 62 instances (38 exact + 24 that will land abbreviated)
  landing batch: 100 rows (38 known / 24 abbreviated / 38 new)

4.1 the gate, declared on the entry: match_at=0.97 propose_below=0.8
      known: {'match': 38}
     banded: {'match': 1, 'review': 23}
      novel: {'propose': 38}
     known:match   e.g. '7502 18 AVENUE' @ 1.0
     banded:review e.g. '2260 BENSON AVE' @ 0.9091
     novel:propose e.g. '25 BAY   13 STREET REAR ANNEX 2031' @ 0.6122

  the number: 38 of 38 already-known rows matched

4.2 outcomes that fired across the batch: ['match', 'propose', 'review']

4.3 the same batch under two callers who chose their own thresholds
  18 of 100 rows resolve DIFFERENTLY for the two callers
     '2260 BENSON AVE' @ 0.9091: caller A -> match, caller B -> review
     '1602 SHORE PKWY' @ 0.9091: caller A -> match, caller B -> review
     '130 BAY   47 ST' @ 0.8667: caller A -> match, caller B -> review

4.4 policy.verdict(None) -> 'unknowable'
7/7 checks pass
```

**The number is 38 of 38, and it is in the record because the row was told to put it there.** All three
of the gate's outcomes fire on one batch of real rows: 38 `match`, 23 `review`, 38 `propose`, with one
abbreviated row matching at 1.0 because its address (`BATH BEACH PARK`) contains no abbreviable word —
**[Observed]**, and it is the correct answer rather than a miss.

**4.3 is the section that decides §5's shape.** Two callers who each chose a threshold for the same
vocabulary disagree on **18 of 100 rows**, every one of them an abbreviated address in the band. Each
caller is internally consistent; the store ends up with duplicates whose cause is *which caller landed
the row*, which is a fact the curation loop cannot see, cannot enumerate, and cannot fix — because
nothing recorded it. **So the threshold is a declared, governed fact on the entry**, riding the
proposal→approval loop like every other governed fact, and it is **not** a call parameter. `MatchPolicy.why`
is required and non-empty for `ACTIONS.md` §2.4-3's reason: an undescribed threshold is one nobody will
ever be able to raise.

**4.4 closes the loop back to design test 1.** A candidate the scan could not score is `unknowable` at
the gate too — the gate never softens the fifth outcome into a fourth.

---

## 6. The adversarial loop

**Cap 3 rounds** (standing constraint 7). Lenses: the **beacon integrator** (would the design partner's
capture path go through this spec without a second resolution call?), the **public data** (does every shape
survive CMS and NYC, and did any shape take its form because the partner has it?), and the **kill row**
(does any resolution outcome let two instances answer to one identity through the confidence gate?). Every
reviewer was briefed with [`../USE-CASES.md`](../USE-CASES.md) and required to **construct and run** each
finding rather than argue it.

**This section is written to disk as each lens returns** — row 6c's rule, adopted because a round's findings
recorded only after the fixes are a round the record cannot audit.

### 6.1 Round 1, lens 1 — **the beacon integrator. NOT YET: 4 BLOCKING, 7 MAJOR, 2 MINOR.**

**The verdict in one sentence, and it is the sharpest thing this row has been told:** *the capture path does
not go through this spec — it stops at the first call.* For the one case the design partner is actually
missing — a project that does not exist yet — there is no invocation to make, because **the thing being
proposed cannot be named as an input**.

**All four BLOCKING findings are in §4, and they are one defect wearing four hats: §4's claim that a
propose-at-ingest act needs NOTHING new from [`../specs/ACTIONS.md`](../specs/ACTIONS.md) is FALSE on the
propose path — which is the only path §4 exists for.**

| # | severity | finding | disposition |
|---|---|---|---|
| **F1** | **BLOCKING** | **The gate cannot run before the host writes.** `InputSpec(ref="instance")` is validated at both doors (ACTIONS rule 6-6) and a thing being proposed has **no `InstanceRef` yet**. **[Observed]** omitting it → `Refusal(input_kind_mismatch, {"problem":"missing"})`; naming the type instead → `Refusal(input_kind_mismatch, {"declared":"instance","supplied":"type"})`; **inventing** an id → `Preflight allowed`, which rule `C20-01` forbids. Declaring the inputs optional is worse: `preflight` called with **nothing** returned `verdict='allowed'` — *the gate answered for a capture whose subject it never saw* | **ACCEPTED.** §4 gains a **fourth reference shape** and says so | 
| **F2** | **BLOCKING** | **Rule 4-3 has no carrier.** **[Observed]** no field on `Invocation` carries a *result*. Route A — the minted ref in the `host_state` effect's `why` (its identity, ACTIONS 2.5-9) — makes a **correct** capture warn `effect_undeclared:host_state:created beacon:entity:task#t-9001…`, which is ACTIONS' own *"a detector that fires on a correct run is not a detector"* reproduced one document along. Route B — an optional `InputSpec` used as an output slot — works, and is one container meaning two things | **ACCEPTED.** Named as an amendment INGEST **asks of** ACTIONS, not one it can make |
| **F3** | **BLOCKING** | **Rule 4-5 is not implementable with ACTIONS unchanged.** **[Observed]** `record_invocation`'s parameters contain neither `approval_mode` nor `warnings`; `declared_policy` is copied from the family, and the only shipped route to `review` is a governance act that moves **every subsequent row** there | **ACCEPTED.** Second required amendment |
| **F4** | **BLOCKING** | **The kill criterion reaches the BATCH, and §13's five routes do not list it.** **[Observed]** two captures in one act both resolve the same label *before either is written*, both correctly answer `proposal` under rule 3-7 (`complete=True`), both are written — and the next capture resolves `ambiguous known=2 confidence=1.0` over `#p-9001` and `#p-9002`, permanently. **[Observed]** the string `idempot` occurs **zero** times in `INGEST.md` and `within the batch` **zero** times; all four `batch` hits are about scheduling | **ACCEPTED, and it is the most important finding of the round** — see §6.1a |
| **F5** | MAJOR | **No relationship resolution, no dedupe, and no policy for one.** `CandidateQuery.kind` is *"always `entity` in v0"* and no call resolves an edge instance; **[Observed]** `add_edge` twice for one capture → two `edge_id`s, `neighbors known=2`. `InstanceRef.id` is non-optional, so *an edge to a thing not written yet* is inexpressible | **ACCEPTED** as a recorded contortion and a question — it is out of this row's scope and the spec must say so rather than imply it |
| **F6** | MAJOR | **`InstanceContext` repeats ACT2 for prose, and the measurement is decisive.** **[Observed]** of the 104 shared-name ties, `row_attributes` separates **104/104** and `sibling_labels` **0/104** — the field that carries the signal is the one a capture cannot fill, and the field a capture *can* fill cannot break a tie by construction (tied candidates share a label, so their siblings are identical). `sibling_labels` is also **type-mixed**: resolving a task is handed a project name and a person name | **ACCEPTED.** The field is typed and the contortion recorded |
| **F7** | MAJOR | **`instance_ambiguous_at_proposal:<n>` cannot say WHICH entity was ambiguous.** **[Observed]** a capture with a 3-way and a 2-way tie records `['instance_ambiguous_at_proposal:3','instance_ambiguous_at_proposal:2']` — two integers, no input name, no refs | **ACCEPTED.** One more segment, no new value |
| **F8** | MAJOR | **Rules 7-1 and 7-4 name the resolution as their carrier and it has no field for them.** Rule 7-4 says *"the resolution says so"*; `InstanceResolution` has no `warnings`, and `why_incomplete` is `""` on a complete scan | **ACCEPTED** |
| **F9** | MAJOR | **The evidence base does not reach the shapes §8 prints.** **[Observed]** `InstanceContext` (the call's second **positional** argument), `label_source`, `row_attributes`, `sibling_labels`, `resolves_instances`, `instance_filters`, `InstanceRecord.source_version`, `NotSupported` and `get_instance` were **never run** by any of the four design tests — and design test 1's own probe takes `min_confidence` as a **call parameter**, the exact shape rule 3-10 (`C20-24`) forbids | **ACCEPTED, and it is the round's second-most important finding**: the row's own probe contradicts the row's own rule |
| **F10** | MAJOR | **`not_an_instance` is unreachable from prose.** **[Observed]** `'the team'`, `'next quarter'`, `'action items'`, `'TBD'`, `'the migration'` all → `proposal`; only `'Provider Name'` → `not_an_instance`. §3.3's mechanism is a class-word list built from column headers, and UC1 has no cells | **ACCEPTED** as a contortion, and §12's *"the partner's shape changed nothing"* is corrected |
| **F11** | MAJOR | **§4.3 calls both consequences "mechanical" and the second is prose.** **[Observed]** `review_invocation(reviewed_by='ai:capture')` — the same actor that ingested — succeeds. ACTIONS §6.5/R73 argued only that a `reviewed_by=` **parameter on the write call** would allow self-review; it never claimed actor distinctness is enforced | **ACCEPTED.** The sentence is false as written |
| **F12** | MINOR | **§12 tags `[Observed]` a claim this repository's own record tags `[Inferred]`**, from a source not in `docs/` | **ACCEPTED** — this is the one discipline the project cannot be loose about |
| **F13** | MINOR | **Primitive 22 is called by nothing this document specifies.** `C20-05` is a rule about a primitive no caller reaches | **ACCEPTED**, and it has a real caller once named |

### 6.1a F4 — the kill row's shape at the instance surface, reached in a SPEC before any code

**Recorded to the standard the fourteen trip records set, because it is the same criterion one level down and
the brief is explicit that this row's resolution outcome must not become a fifteenth by another name.**

**The construction, [Observed], five ordinary steps and no guard bypassed:** one ingest act carries two rows
whose labels resolve to the same thing. `resolve_instance` is called for each **before either is written** —
which is the ordinary shape, because the host writes on approval. Both scans **finish** (`complete=True`), so
rule 3-7 is satisfied and both correctly answer `proposal`. Both are approved. The store now holds two rows
answering to one identity, and the *next* resolution reports it: `ambiguous known=2 confidence=1.0`.

**Every rule in §3 fired correctly and the outcome is still two things answering to one identity.** That is
the distinction the register's own trips turn on: this is not a guard that failed to look, it is **a guard
that was never asked** — the state is created *between* two correct answers, and nothing in the document
made the second call aware of the first.

**Whose defect it is, stated plainly rather than argued.** It is **this document's**, introduced by this
document, and it is **not** a fifteenth trip of the register's kill row: the register's fourteen are
constructed against shipped code at the type-identity surface, and this is constructed against a
specification with no implementation, at a surface that does not exist yet. **[Observed]** by construction:
`git log` shows no code in this row, and the probe builds the state entirely out of `INGEST.md`'s own printed
rules. The honest reading is the one the thirteenth countersignature used for its Variant A — *the loop
reaching past its own diff* — inverted: **the loop reached the defect before the diff existed**, which is the
whole reason a spec row runs an adversarial loop at all.

**Standing rule (d) is what should have caught it and did not.** *A rule minted at the caller that prompted
it is half-applied until the commit that mints it names every other caller it binds.* §3's ordering rule
(`ambiguous` before `existing`) was minted at `resolve_instance` and the enumeration stopped there. The
caller it also binds is **the ingest act**, which calls `resolve_instance` more than once and is the only
place that knows the calls are related. The register's own rule named the gap and this row did not apply it.

**Closed by:** a new rule in §4 with its own id, a sixth row in §13's table, and a probe that constructs the
state and shows the rule refusing it. Recorded in §5 of this document as what the round cost.

### 6.1b What the lens attacked and could NOT break — carried forward so round 2 is not re-tread

1. **The reserved-value arithmetic.** **[Observed]** `types.REFUSAL_REASONS` is 31 and `types.WARNING_VALUES`
   is 37, so §9's *"thirty-second refusal"* and *"thirty-eighth warning"* are exactly right and R11's
   reservation argument holds.
2. **§1's *"two primitives, no `put`"*.** The lens looked for a write the capture path forces this project to
   perform and found none. **R78's seam survives the write side of a capture** — which is the claim §1.2 said
   design test 1 had not tested, now tested from the other end by a reviewer trying to break it.
3. **`C20-01`, no minted identifiers.** The registry produced no instance id; the reviewer had to invent one
   by hand to get past `preflight`, which is the rule working.
4. **Rules 3-3 / 3-4.** They fired correctly on the batch case — `ambiguous`, `known=2`, no `ref`. The
   ordering rule is right; F4 is that it runs after the damage.
5. **§4.2's provenance claim.** `InvocationProvenance` genuinely carries actor, tier, confidence, approver and
   `source_version` for a capture. **No provenance field is missing** — §4.2 is the one part of §4 that holds
   exactly as written.
6. **`input_kind_mismatch` at both doors** holds under ingest load.
7. **Deliberately not attacked by this lens:** §2.2's paging states, §6's twelve terms and their Kleene
   composition, §6.2's null handling, and design tests 2 and 3's live measurements. Another lens takes those.

### 6.2 Round 1, lens 2 — **the kill row. NOT YET: 4 BLOCKING, 4 MAJOR, 2 MINOR, and it found a trip.**

**Provenance first, standing rule (a).** **[Observed]** `grep -rc "resolve_instance\|MatchPolicy\|find_instance_candidates" ontoloche/` returns **zero**: the instance-identity surface does not exist in shipped code, so there is no earlier commit to bisect against. Every finding below is established **by construction and measurement** against the artefacts `INGEST.md` itself cites as its evidence, plus the shipped `Registry`, `ref_key`, `parse_ref` and `flat_form_problem`.

#### 6.2a `I-1` — **a truncated scan that FINDS a match answers `existing` at 1.0 on a label twelve facilities answer to**

*Classified by [R83](../decisions/2026-09-04-7a-supervisor-ruling-R83.md): **not** a fifteenth kill-row trip — the
trip count stays at **fourteen** — and recorded as the first of the `I-n` **instance-surface records**, a series
that never merges with the trip count. The countersignature is at the end of this section.*

**[Observed]**, one ordinary `scan_cap` — R58's own third state, the same mechanism design test 1's own T1.5 uses — set one row past the first of `"MILLER'S MERRY MANOR"`'s twelve CCNs:

```
CONTROL   (uncapped)      outcome='ambiguous' ref=None conf=1.0 known=12 complete=True  scanned=14627

TRUNCATED (scan_cap=3541, 11,086 rows unread, ELEVEN of the twelve among them)
  outcome='existing' ref='cms:entity:facility#155049' conf=1.0 known=1 complete=False scanned=3541
  why_incomplete='host scan cap of 3541 rows reached; the rest of this table cannot be read
                  from this surface'
  reason='one host row answers to "MILLER\'S MERRY MANOR"'
```

**`conf=1.0` is `INTERFACE.md` §5.3's guarantee, handed out for a string twelve distinct Indiana facilities
answer to** — and the `reason` string says *"one host row answers to"* while eleven others do, unread. Eleven
facilities' citations file into a twelfth's record: **§3.2's own sentence, arrived at through the door §3.2
does not guard.**

**Why both of §13's first two routes claim to close this and neither fires.**

- Route 1 — *"two candidates tie and the top one is returned → rule 3-3"*. The tie test is evaluated over
  `scanned=3541 of 14627`, **a partial extent**. That is **the register's FIFTH trip verbatim** (`_extent`
  read one page, discarded the `why`, and two predicates whose first page matched compared equal), one
  identity surface down.
- Route 2 — *"a truncated scan finds nothing and a duplicate is proposed → rules 3-5 / 3-6 / 3-7"*. Its
  `[Observed]` evidence is `cms:entity:facility#745057`, and **[Observed]** the only `scan_cap` in the whole
  probe set is `cap = 14000` against a target at row **14,623 of 14,627** — truncation with the match
  **unread**. The quadrant *truncation × match-found* is posed by nothing.

**The root cause is a disagreement inside this document, and it is not subtle.** §3.4's prose reasons only
about the empty case — *"is `unknowable`, never **not found**"*, *"a resolution that reached **no candidate**
over a scan that did not finish"* — and states the ordering as *"the incompleteness is checked before the
**emptiness** is interpreted."* Rule **3-5**'s table row says something strictly wider: *"whatever the
candidates found."* **The prose and the rule table disagree; §13's route table inherited the narrow one; and
the row's own probe implements the narrow one.** Rule 3-6 forbids `complete=False` beside `proposal` and says
nothing about `existing`; rule 3-7 requires `complete=True` for `proposal` only.

**The worker's reading, offered for countersignature rather than assumed.** *(A trip is never the worker's to
judge alone; this record is written in the fourteen records' shape and left for the supervisor to read
against the commit.)*

1. **It is a defect of THIS document, introduced with the surface at `d9faebb`**, and not one inherited from
   any shipped guard. **[Observed]** by the zero-grep above: there is nothing older to blame.
2. **It is not a fifteenth trip of the register's kill row, and the difference is worth keeping.** The
   register's fourteen are constructed against **shipped code** at the **type**-identity surface. This is
   constructed against a **specification** at a surface that does not exist yet, by a loop the brief required
   to run before the build row. **The loop reached the defect before the diff existed** — the inverse of the
   thirteenth countersignature's *loop reaching past its own diff*, and it is the whole reason a spec row
   runs an adversarial loop at all. Whether the register counts it is the supervisor's, not mine; what I will
   not do is let it land unrecorded because the classification is arguable.
3. **Standing rule (d) is what should have caught it and did not**, and this is the second lens in one round
   to say so (see §6.1a). §3's ordering rule was minted at `resolve_instance` and the enumeration stopped
   there — see finding 7 below, where the row's **own two probes order the same rule opposite ways.**

**COUNTERSIGNED 2026-09-04 — [R83](../decisions/2026-09-04-7a-supervisor-ruling-R83.md), and the record is `I-1`.**
The supervisor read the record against the commits rather than against the paragraph above, and **adopted the
worker's reading on the classification**: this is **not** a fifteenth kill-row trip, and **the count stays at
fourteen** — verified **[Observed]** by `git diff --name-only a1b0364^..39d3718 -- ontoloche/` returning
nothing, so the row constructs no state against shipped code at a shipped door. What R83 added is where the
finding then lives, so that *not a trip* did not become *not recorded*:

- **The record is labelled `I-1`** — the first of the **instance-surface records**, an `I-n` series kept in the
  same register and **distinct from the trip count, with which it never merges**. It is written up at
  [`2026-08-29-3c-rulings-R6-R12.md`, "The instance-surface records"](../decisions/2026-08-29-3c-rulings-R6-R12.md).
- **`stop` is NOT put an eleventh time.** The ten puts attach to trips; this is not one, and a record that is
  not a trip does not get to borrow a trip's weight. **Q56 remains the class-closing question and the
  founder's**, with defaults in force unchanged.
- **The cross-reference to the fifth trip is confirmed**, against the fifth trip's own record: *partial is not
  equal*, with the read's own `why` discarded — same operand, same discarded signal, new surface.
- **The register's rules already bind this surface even though its trips do not.** K4 is standing rule (c) one
  surface down; K7 is standing rule (d) **measured**. That asymmetry is why the series exists.
- **K6's shipped half is Q56's territory, not a trip's** (R83 §6). The successor redirect answering `existing`
  at 1.0 is the specified behaviour with a founder-visible question already open on it; K6's defect is its
  **unshipped** half. Recorded so the register is not asked this twice.
- **The dedicated identity-surface row** recommended at the fourteenth countersignature §4 **gains an instance
  half**: its lenses become the fourteen trip records *and* the `I-n` records.

**Nothing in R83 reopens a disposition.** K1's fix as landed at `07af54f` / `39d3718` stands, and the loop's
cap of 3 is unchanged with round 1 counting as round 1.

#### 6.2b Every finding, with its disposition

| # | severity | finding | disposition |
|---|---|---|---|
| **K1** | **BLOCKING** | **The trip, above.** §3.4 guards emptiness, not the candidate set | **ACCEPTED.** §3.4's ordering is restated over the **set**, and a rule beside 3-6/3-7 requires `complete=True` for `existing` and `ambiguous` too. Closes K5 and K9 as well |
| **K2** | **BLOCKING** | **The match band is wider than the ambiguity margin**, so two rows are both `existing`-grade and the call names one. Rule 5-2 constrains only `propose_below <= match_at`; **nothing constrains `ambiguity_margin` against `1 - match_at`**, and with the row's own printed numbers (`match_at=0.97`, `ambiguity_margin=0.02`) the band is width **0.03 > 0.02** — an arithmetic gap in the spec's own figures. **[Observed]** seven real CMS pairs land in it, including `MAGNOLIA MANOR OF COLUMBUS NURSING CENTER - WEST` vs `- EAST` (two genuinely different Georgia facilities) and `'Mountain View Health Care'` (115688) vs `'MOUNTAIN VIEW HEALTHCARE'` (265412) at **0.9796** → `outcome='existing' conf=1.0 known=2 complete=True`, reason *"one host row answers to"*. **No truncation, no ties, ordinary data** | **ACCEPTED.** The tie test becomes a **set** test: every candidate at or above `match_at` is tied, and `existing` requires exactly one. That is stronger than the margin arithmetic and needs no second constraint |
| **K3** | **BLOCKING** | **`review` is a gate verdict with no outcome in a vocabulary rule 3-1 closes at five.** **[Observed]** the two probes the document cites answer one landed row two ways — `MatchPolicy.verdict → 'review'`, `resolve_instance → 'proposal'` — on `'WILLOWBROOKE CT SKILLED CARE CENTER AT MEASE LI'` @ 0.9691. With nothing forbidding a re-ingest and no human draining the band: pass 1 proposes and the host mints `HOST-MINTED-1`; pass 2 then answers `existing` at 1.0; the final resolution reports `known=2` over the original and the duplicate. **Two host rows for one facility, from ordinary calls** | **ACCEPTED.** §5 must say which of the five a banded score returns, and §3/§5 must be one call rather than two artefacts |
| **K4** | **BLOCKING** | **The propose path is not idempotent in the state the resolution read** — trip 12's standing rule, unapplied at the only write door this document has. Between proposal and host write the state is unchanged, so the permission can be cashed again. **[Observed]** three passes → three unreviewed invocations for one label, `warnings=[[], [], []]`, and the store then answers `ambiguous known=3`. **The concurrent variant needs no repeat call at all**: two workers read the same state, both answer `proposal`, both hosts write | **ACCEPTED.** This is **standing rule (c) one surface down**: *a pending ingest proposal is an unconsumed permission to mint an instance identity, and no door asks who already holds one for this word* |
| **K5** | MAJOR | **§3.4's second `unknowable` absorber does not reach the match path either, and the leak is cross-tenant.** A host obeying rule 2-7 to the letter returns `complete=False` with a `why`; **[Observed]** the resolution answers `existing` at **1.0** on `cms:entity:facility#155102` — **another tenant's row**, from a page the host said could not be read as the set. **R59's own stated reversal condition, reached through the field R58's measurement forced** — contortion ING4's cost arriving as an outcome rather than as an opacity | **ACCEPTED**, closed by K1's fix |
| **K6** | MAJOR | **An instance's type can be retired toward a successor underneath it.** **[Observed]** against the **shipped** `Registry`: after `retire('facility', successor='nursing_facility')`, `resolve_type('facility')` → `existing / nursing_facility / 1.0` while `resolve_instance(type_name='nursing_facility')` → `proposal / scanned=0 / complete=True` and the ledger ends holding both `#facility#015009` and `#nursing_facility#HOST-MINTED-1`. Three defects in one construction: the identity read does not follow the successor chain that `EDGES.md` rule 4.3-14 / **R38** requires of `neighbors`; `proposal` over `scanned=0` with `complete=True` is **a confident "there is nothing like this" from a scan that read no rows**; and the retired name answers `existing` at 1.0 forever, because `InstanceRecord.type_name` is the host's string | **ACCEPTED** |
| **K7** | MAJOR | **Standing rule (d), measured: the row's own two probes order ONE rule opposite ways.** **[Observed]** design test 3's absorber (an undecidable predicate) is checked **before** scoring — `unknowable`, correct; design test 1's absorber (a truncated scan) is checked **only when nothing scored** — `existing` at 1.0 on a truncated read. One document, one row, one rule (§3.4), two orderings. The lens then enumerated the five places an identity is decided and showed §4 and §5 ask the ambiguity question at neither | **ACCEPTED.** The enumeration goes into §3.4 and §13, per standing rule (d) |
| **K8** | MAJOR | **`ref_key` collides for two different instances and `INGEST.md` never points at the shipped guard.** **[Observed]** `type_name='facility'`/`id='015009#2024-03-11'` and `type_name='facility#015009'`/`id='2024-03-11'` produce the identical flat key, and it round-trips to the first. `flat_form_problem` — shipped, and `C19-82`'s own fix — catches the `type_name` and `namespace` cases and is enforced at ACTIONS' invocation door only; primitive 23 and `InstanceResolution.ref` hand a caller a ref without passing through it | **ACCEPTED.** One rule in §2 and a pointer in §8 |
| **K9** | MINOR | **`instance_ambiguous_at_proposal:<n>` is counted over whatever extent the scan read.** **[Observed]** `scan_cap=3596` → `ambiguous known=3 complete=False` where the true multiplicity is **12**; a reviewer draining the queue sees `:3` for a twelve-way collision | **ACCEPTED**, closed for free by K1 and named so it is not lost if that fix is scoped narrowly |
| **K10** | MINOR | **Contortion ING3's risk is already realised in the row's own scorer.** **[Observed]** `'状态'` and `'!!!'` → `not_an_instance` with `scanned=0`: `_norm` is `identity_key`'s ASCII-only collapse re-implemented, so a real Chinese-language facility name is refused as a class word. **`C4-14`'s defect in its other direction**, in the second notion of *the same string* that ING3 names | **ACCEPTED as evidence for Q86**, whose text now carries it rather than calling the risk theoretical. A probe defect, not a spec defect — §3.3 declines to define the classifier — and that is exactly why it belongs in the question |

#### 6.2c The countable-absence count — **eleven**, and five of them are a previous trip's count verbatim

Five consecutive trips in this register were explained by a *countable absence* in the gate rather than a
subtle one. The lens ran the same count over the three ingest probes together:

1. **Zero** fixtures pose *truncation × match-found*. `scan_cap` is set exactly **twice**, both at `14000`
   against a target at row **14,623**. That is K1's entire quadrant.
2. **Zero** `resolve_instance` call sites in `ingest_gate_probe.py` — §5's gate has **never been run through
   §3's call**, which is why the two disagree (K3).
3. **Zero** occurrences of `ambiguity_margin`, `ambiguous` or `tied` in the gate probe. **The probe that is
   the confidence gate's entire evidence cannot pose the ambiguity question** — and §13's own sharpest
   question is *does any resolution outcome let two instances answer to one identity **through the confidence
   gate**?*
4. **Zero** gate fixtures able to hold two rows for one label: the host is deduped by `seen.setdefault(...)`
   (**the trip-12 `_alias_map` shape**) and `best_score` keeps the first of a tie by `s > best[1]`.
5. **Zero** repeated calls of `resolve_instance` on one label against one store, across **12** call sites —
   *the identical count that explained trip 12.*
6. **Zero** `retire(`, **zero** `merge_types(`, **zero** `successor` — *the identical count that explained
   trip 14* (K6).
7. **Zero** `host_filter` — §2.1's load-bearing distinction and §3.4's second absorber are posed by nothing (K5).
8. **Zero** `instance_filters`, **zero** `resolves_instances` — §2.3's two minted flags and rule 1-3's refusal
   are exercised by nothing.
9. **Zero** `record_invocation`, `invocations(`, `InvocationProvenance` — **§4, the whole propose-at-ingest
   contract, has no probe at all** (K4).
10. **Zero** `instance_ambiguous_at_proposal` — §4.3's own mechanical handle is never exercised.
11. **Zero** `parse_ref` / `flat_form_problem` — §2 and §8's grammar over a host-supplied opaque id is checked
    by nothing (K8).

**The sentence this register has now written nine times, at this row:** *a probe set built to prove five
outcomes reachable cannot pose the question of whether two of them are reachable at once.*

#### 6.2d What the lens attacked and could NOT break

1. **Rule 3-4 — `ref` is `None` on `ambiguous`.** Held under every construction (uncapped, half-capped,
   filter-unapplied): `ambiguous / ref=None / known=12` every time. **The shape trips 11 and 12 took does not
   reproduce here.**
2. **Rule 3-8** — `not_an_instance` without reading the host table. Held, `scanned=0`.
3. **Rules 5-2 / 5-3 at declaration.** Both refused in `__post_init__`, not at runtime.
4. **Trip 8's empty-key collision at the instance layer.** **Not constructible**: the candidate side is
   guarded, host labels that normalise empty score `0.0`, and **[Observed] zero of 14,627 real CMS labels
   normalise to the empty key.** (Its *other* direction is real — K10 — but the two-instances-one-identity
   form is not reachable.)
5. **`parse_ref` round trip for the legal opaque id.** `'015009#2024'`, `'a:b:c'`, `'#'`, `''`, `'x#y:z#w'` —
   all round-trip. **The grammar is sound for the field rule 1-1 actually declares opaque**; only the
   unguarded `type_name` / `namespace` break it (K8).
6. **§6.3's tenant-blindness (R59 / R24, rule 6-17), and the condition probe's ordering.** `if undecided:`
   **before** scoring is correct, and rule 6-16 holds even with a 1.0 match present. **This is the one
   absorber the row got right — and it is what proves the other two were reachable.**
7. **§1's seam claim (R78).** *"I did not find a route by which an outcome requires an instance row in the
   registry. The two-primitive count survives every construction above; every duplicate I produced was
   written by the host, exactly as rule 4-2 says it would be."* **Two lenses have now tried to break R78 from
   opposite ends and neither could.**
8. **Cross-namespace instance resolution.** `namespace` is untouched at this surface as it has been at the
   type surface across all fourteen trips.

### 6.3 Round 1, lens 3 — **the public data. NOT YET: 3 BLOCKING, 9 MAJOR, 2 MINOR.**

**This lens found the trip independently, from a different direction, and proved the gate blind to it by
MUTATION** — which is the strongest form of evidence this project accepts and the one the register's own
axes are held to.

#### 6.3a The mutation proof, and it is the finding behind the finding

**[Observed]** the lens moved design test 1's entire Rule-U block from **before** the ambiguity/existence
branches to **after** them — *deleting the load-bearing sentence of §3.4* — and re-ran the unmodified probe:

```
16/16 checks pass
R78 VERDICT: CONFIRMED
```

**Byte-identical verdict.** The row's own gate cannot see its own most important rule being removed. That is
the ninth consecutive dress of *a checker only asks the questions its fixtures can pose*, and it lands on
this row's own probes rather than on an inherited one.

#### 6.3b Every finding, with its disposition

| # | severity | finding | disposition |
|---|---|---|---|
| **P1** | **BLOCKING** | **The trip, reached independently** (= K1, §6.2a): cap the scan past the first of the twelve and rule 3-3 has nothing to compare — `existing / #155049 / 1.0 / complete=False`, eleven unread rows carrying the same label at 1.0. The lens's own diagnosis is the one that matters: **rule 3-5 as written already forbids it** (*"whatever the candidates found"*) **and §3.4's prose argues only the empty case, and the only implementation this row ships implements only the empty case** — `if not top and not complete:` | **ACCEPTED.** Two lenses, two constructions, one root cause. §3.4's prose is corrected to what rule 3-5 already says, a T1.2-under-cap case joins design test 1, and §13 route 1 cites rule 3-5 rather than rule 3-3 |
| **P2** | **BLOCKING** | **Rule 2-8 (`label` may narrow) + rule 3-7 (`proposal` needs `complete=True`) is a duplicate factory, with no contortion recording it.** §2.1 specifies what an *ignoring* backend reports and says **nothing** about a *narrowing* one — no `complete=False`, no `why`, and `instance_filters` governs `host_filter` names only. **[Observed]** two conformant backends over design test 4's own batch: the ignoring host routes 23 banded rows to a human; the narrowing host answers **`proposal` with `candidates_seen=0` and `complete=True`** for all 23. `unknowable` cannot fire — nothing was truncated. **This is §5.1's own argument one layer down, where the spec did not look** | **ACCEPTED.** `label` becomes non-narrowing by rule; all narrowing goes through `host_filter` |
| **P3** | **BLOCKING** | **§3's `predicate` is a call parameter defaulting to `None` while rule 6-14 declares it on the entry — and the default is R59's reversal condition.** **[Observed]** same CA+CO fixture, one caller passing the entry's predicate and one omitting the keyword: **5 of 5 shared names resolve differently**, and every caller-B answer hands the CA caller a CO `InstanceRef` in `candidates`. **[Observed]** design test 3 only ever tested the call-parameter path. **§5.1 refuses a per-call THRESHOLD on exactly this reasoning and then admits a per-call PREDICATE two sections earlier** | **ACCEPTED, and it is the round's most embarrassing finding**: the document argues the rule and then breaks it in its own printed signature |
| **M1** | MAJOR | **Design test 2's `unknowable` check cannot go red, and §3.1's "two independent routes" claim is therefore false.** **[Observed]** the probe computes `outcome = "unknowable" if not p_trunc.complete else "resolvable"` — a restatement of the check three lines above — and **calls no resolver at all**; a rule-3-5-**violating** resolver inserted over the same truncated page answers `'proposal'` and the probe still prints `10/10 checks pass` | **ACCEPTED. The claim is withdrawn and the probe is made to call a resolver.** A second route asserted and not run is exactly what this project's drift checker exists to catch, pointing inward |
| **M2** | MAJOR | **`host_filter` buys affordability with duplicates, and §2.1 celebrates it without recording the cost.** The spec never says *which set* `complete` is about. **[Observed]** over the 725-row narrowed slice, **3,330 of 3,330** landed rows resolve `proposal` with `complete=True` — one of them at an address the same host table holds **122** rows for | **ACCEPTED.** `complete` is defined as *about the set the query named, `host_filter` included*, and a `proposal` off a narrowed set carries a warning naming the filter |
| **M3** | MAJOR | **"38 of 38" is a property of one dedup line, not of the data.** **[Observed]** `ingest_gate_probe.py` builds its host with `seen.setdefault(address, r)` — one instance per address — while the instance in `erm2-nwe9` is a service request keyed by `unique_key`; **46%** of the fetched rows share an address, and the probe discards **32%** of them. Un-deduped, the same batch gives **`{'ambiguous': 13, 'existing': 25}`** | **ACCEPTED.** §5 prints the real number and says what the fixture does. *A headline number that is an artefact of a fixture line is the thing this project's own §5.1 argument is about* |
| **M4** | MAJOR | **ING5 quantified on UC3, and the label choice does not merely hide a decision — it defeats the gate.** **[Observed]** `uvpi-gqnh`, 683,788 DPR instances: `address` → 408,701 distinct, **59.7% of instances share an address with another**, so 59.7% of landed rows are `ambiguous` and rule 4-5 forces every one into `review`; `spc_common` → 132 class words → `not_an_instance`; `tree_id` → the opaque host id, which is not *"the human-facing string a landed row would carry"* | **ACCEPTED.** The measured cost goes into ING5 |
| **M5** | MAJOR | **`Condition` cannot compare two attributes of one record, and the nearest expressible form is accepted at declaration and `False` for every record.** UC2's own pre-registered pathology — **5,338 of 416,948 rows (1.2803%)** carry a correction date before the survey date — has the gate `Correction Date >= Survey Date`. **[Observed]** `Condition(op='gte', attribute='Correction Date', value='Survey Date')` is **ACCEPTED** at declaration and answers `holds=False` for valid and inverted rows alike, because every ISO date sorts below `'S'`. **That is design test 3's own 3.3b mechanism C, reached by a predicate that passes rules 6-1…6-13 with a non-empty `why`** | **ACCEPTED** as a recorded contortion and a routed question. A thirteenth term is a §-row change and is not taken on a design test's authority |
| **M6** | MAJOR | **`kind` is pinned to `"entity"` with no reason and no contortion, which silently drops half of UC2.** `INTERFACE.md` §10's CMS design test registers six types, **two of them `value_set`** — and *"which of the six statuses is this cell?"* is an instance question over a landed row, is what UC2 was chosen to test, and this protocol cannot ask it. The constraint is **inherited** from `EDGES.md` §2.1 — *but an inherited constraint that removes a fixture's stated pathology is a contortion, not a non-issue* | **ACCEPTED** |
| **M7** | MAJOR | **Primitive 22 has no tenancy surface at all.** Rule 6-17 constrains the *candidate* primitive; `get_instance` takes no `predicate` and no `host_filter`, so rule 6-15 has nothing to evaluate over. **[Observed]** a CA caller can confirm a CO row by key. Design test 3 never calls it | **ACCEPTED**, and it answers F13/K-adjacent *"what calls primitive 22?"* at the same time |
| **M8** | MAJOR | **`instance_filters` (a set of NAMES) cannot govern `host_filter` (an opaque EXPRESSION), so rules 2-7, 2-9, 2-10 and `C20-03` have no decidable test.** **[Observed]** `grep -c` returns **0** for both flags across all four probes | **ACCEPTED.** `host_filter` becomes a named-filter mapping so `instance_filters` can actually cover it |
| **M9** | MAJOR | **`not_an_instance`'s cost is real, one-sided and measured, and T1.4 picked the one value the hand-written list contains.** **[Observed]** of CMS's 23 headers, **22 are not caught**; of `erm2-nwe9`'s values, **16,001 distinct street names carrying 861,161 rows (3.9%)** — `'BROADWAY'` 24,154, `'5 AVENUE'` 12,821 — are classes that pass as instances and become well-formed provenance-bearing proposals. False positives: **0 of 14,498** | **ACCEPTED.** Both numbers go into §3.3 |
| **p-m1** | MINOR | §12's `9,764,249` carries no date, unlike §2.1's and §2.2's — the document's own finding, unapplied to its own §12 | **ACCEPTED** |
| **p-m2** | MINOR | **§2.1's timing figures are not reproducible on the day they were taken.** **[Observed]** an unmodified re-run: `one 50000-row page took 8.39s`, `27.4 minutes`, against the cited `1.26s` / `4.1 minutes`. **The argument survives — both are far past per-row affordable — but the printed number is 6.7x off within hours** | **ACCEPTED.** Printed as a range, with the two-decimal precision dropped |

#### 6.3c What the lens attacked and could NOT break

1. **Every CMS number the spec cites**, re-derived from the real 165,336,194-byte file: `419479 / 14627 /
   14498 / 104`, `MATCH: True True True True True`. The 1.28% date inversion reproduces exactly
   (5,338 of 416,948 = **1.2803%**); `Deficiency Corrected` has exactly six values. **Nothing pre-registered
   is wrong.**
2. **R78 itself.** *"I could not find an outcome that needs an instance store. The seam holds; T1.7's
   `[('entity','facility')]` is real and the mutation did not disturb it."* **Three lenses have now tried to
   break R78 from three directions and none could.**
3. **The five-outcome set.** T1.5 is a genuine constructed failure and the fifth outcome is genuinely forced
   by it — only the *second* route (M1) was fabricated.
4. **`ambiguous` before `existing` as a rule.** Removing it **does** make design test 1 go red — the rule is
   tested. *Its premise (a complete scan) is what fails*, which is P1 and not a defect in the rule.
5. **Kleene composition and the `is_null` / `eq` split.** All reproduce; the SQL-agreement argument holds.
6. **The rule→id accounting.** 62 distinct ids, 62 rule rows, `C20-01`…`C20-62`, no gaps, no duplicates.
7. **§9's reservation of `instance_source_absent`.** Consistent with R11 and with the drift checker's scope;
   **Q85 correctly routes the disagreement rather than deciding it.**
8. **The absence of `not` and `matches`.** *"I tried to construct a real CMS or NYC host predicate needing
   either and could not — every case I built reduced to `ne`/`not_in` or to M5's attribute-to-attribute gap,
   which is a different missing thing."*

### 6.4 Round 1, totalled — **11 BLOCKING, 20 MAJOR, 6 MINOR across three lenses**

**Three lenses, three verdicts of NOT YET, and no lens returned nothing.** The findings converge rather than
scatter, which is the useful case: **two independent lenses reached the same trip from opposite directions**
(K1 / P1), **two independently invoked standing rule (d)** (F4's batch enumeration, K7's two orderings), and
**all three tried to break R78 and none could.**

**What round 1 says about the row, stated before the fixes so it cannot be tidied afterwards:**

1. **The seam is right and the rules around it were half-written.** Every BLOCKING finding is a rule that
   guarded the case that prompted it and not the case beside it — §3.4's emptiness but not its candidate set;
   §5's threshold but not its predicate; §4's existing instances but not proposed ones. That is standing rule
   (d) three times in one round, in a row whose brief cited the register that minted it.
2. **The row's own probes were the weakest artefact it shipped.** A mutation deleting §3.4's load-bearing
   sentence left `16/16` green (M1/P1); design test 2's headline outcome was computed from a flag rather than
   from a resolver (M1); design test 4's headline number was an artefact of one `setdefault` line (M3).
   **Eleven countable absences** (§6.2c). The fixes are worth less than the probe rewrite that proves them.
3. **The document contradicted itself twice in ways a reader would act on** — §3.4's prose against rule 3-5,
   and §5.1's argument against §3's own printed signature. Both are the same failure: *a claim made in prose
   and not carried into the shape beside it.*

---

### 6.5 Round 2, lens 1 — **the fix auditor. NOT YET: 5 BLOCKING, 7 MAJOR, 4 MINOR, and it found the kill-row family inside round 1's own fix.**

**Why this lens went first, and it is a rule rather than a choice.** The twelfth countersignature made it
standing: *every round after a fix round begins with a lens pointed at that fix.* Round 1 shipped a large fix
set — INGEST 62 → 74 rules, a fourth reference shape, a rewritten kill-criterion table, one kit replacing two
resolvers — so round 2's first lens was pointed at exactly `07af54f`..`39d3718` and at nothing else. The
register's own count said this is where the next defect lives (3e 4-of-10; row #4 round 3 2-of-4; 4d round 2
five inside round 1's fixes; 6b round 2 the tenth trip inside the ninth's fix). **It was right again.**

**The lens reproduced the baseline before attacking it: [Observed]** DT1 36/36, DT2 13/13, DT3 17/17,
DT4 11/11, DT5 10/10 = **87/87**. It mutated **copies** of the probes in a scratch directory with `PYTHONPATH`
pointed at the repo, so the shipped `ontoloche` package was the real one and **no repo file was ever
modified** — `git status --short` returned nothing throughout.

#### 6.5a `I-2` (proposed) — **the successor chain is followed for ONE hop, and two ordinary curation passes give two confident answers at 1.0 for one identity**

**This is inside round 1's own diff.** Rule **3-14** (`C20-68`) and route 11 of §13 were both minted at
`07af54f` to close **K6**. The rule says the identity read resolves `type_name` *"through the successor
**chain** ... as `neighbors` does under **R38**"*. **[Observed]**, verified by the worker at
[`../tools/ingest_probe_kit.py`](../tools/ingest_probe_kit.py) lines 491–499, the implementation is a `while`
whose body ends in an unconditional `break`:

```python
    # --- rule 3-14: follow the successor chain BEFORE querying -------------
    effective_type = type_name
    seen = {type_name}
    while entry is not None and entry.successor and entry.successor not in seen:
        warnings.append(f"instance_type_succeeded:{entry.successor}")
        effective_type = entry.successor
        seen.add(effective_type)
        entry = vocab.entry(namespace, effective_type) or entry
        break
```

**The construction, [Observed], two ordinary `retire(successor=)` passes and no guard bypassed:**

```
TWO-hop chain  (facility -> nursing_facility -> ltc_facility)
   outcome='existing' ref='cms:entity:nursing_facility#999999' conf=1.0 complete=True why_incomplete=''
   warnings=('instance_type_succeeded:nursing_facility', 'no_tenancy_predicate', 'consumers_unregistered')
ONE-hop chain  (facility -> ltc_facility), the chain-following CONTROL
   outcome='existing' ref='cms:entity:ltc_facility#015009' conf=1.0 complete=True

ONE WORD, ONE TYPE IDENTITY, TWO CONFIDENT ANSWERS AT 1.0:
   cms:entity:nursing_facility#999999  vs  cms:entity:ltc_facility#015009
```

**Three things make this the fix auditor's finding rather than a fresh one.**

1. **Round 1's headline fix cannot see it.** Rules 3-5 / 3-6 guard the completeness the read *reports*, and
   this read reports `complete=True` with `why_incomplete=''`. **It did not fail to finish; it finished over
   the wrong extent.** `I-1` was a scan that stopped early and said so; this is a scan that ran to the end of
   the wrong set and said nothing.
2. **This repository already closed this exact defect one document along, and rule 3-14 cites the ruling it
   fails to implement.** **[Observed]** [`../../ontoloche/registry.py`](../../ontoloche/registry.py) line 1403
   carries the comment *"**The chain, not one hop** (row 4d, round 2). This read ONE successor and required it
   to be live, so a vocabulary curated **twice** — the ordinary outcome after two passes — lost §5.10's
   promise"*, and `_identity_closure` follows the chain with a visited set, a hop cap, and `complete=False`
   with a `why` when it stops early. Rule 3-14 names **R38** as its authority and implements none of R38's
   three termination rules.
3. **Standing rule (d), inside the commit that invoked standing rule (d) as its reason for existing.** The
   rule was minted at `resolve_instance` and the enumeration stopped there; the caller it also binds is the
   shipped `_identity_closure`, whose behaviour it contradicts.

**A second defect rides in the same four lines**, [Observed] by the worker: `entry = vocab.entry(namespace,
effective_type) or entry` keeps the **old** entry when the successor's entry is absent, so the read then
queries `effective_type` while holding the predecessor's entry.

**Classification is NOT the worker's.** It is constructed against a **specification** and a **throwaway kit**,
not against shipped code at a shipped door — which is the exact distinction [**R83**](../decisions/2026-09-04-7a-supervisor-ruling-R83.md)
used to classify `I-1`. On that reading it is a second instance-surface record, **`I-2`**, and not a fifteenth
trip; it is recorded here to the standard R83 set and **routed to the supervisor**, who rules. The kill-row
trip count is **not** incremented anywhere by this record.

#### 6.5b Every finding, with its disposition

| # | severity | finding | disposition |
|---|---|---|---|
| **A1** | **BLOCKING** | **The successor chain is one hop — §6.5a above.** Rule 3-14 says *chain*, cites R38, and the kit `break`s after one. Two curation passes give two `existing`/1.0 answers for one identity, both `complete=True` | **ACCEPTED.** Rule 3-14 is restated over the closure, with R38's three termination rules (visited set, hop cap, `complete=False` **with a `why`** when the cap or a dangling successor stops it), and the kit implements the closure rather than a hop. A probe constructs the two-hop state and shows the rule refusing it |
| **A2** | **BLOCKING** | **Neither fix commit touched the run record, so §1–§4 still hold the evidence round 1 refuted.** **[Observed]**, verified by the worker: `git log --oneline 07af54f^..39d3718 -- docs/runs/7A-RUN.md` returns **nothing**. §4 still prints `{'match': 38}` / `{'review': 23}` — **the three-verdict vocabulary K3 killed and rule 5-4 (`C20-38`) now forbids in terms** — still prints *"two callers who chose their own thresholds"* and *"18 of 100"*, and still asserts *"the number is 38 of 38"* with no trace of M3. §2's header says `10/10` and §3's `12/12`; the probes now print 13/13 and 17/17. **There is no §5 at all**, while `INGEST.md` §8.1 and this document's own §6.1a both cite *"§5 of this document"*. **Design test 5 has no section in the run record** | **ACCEPTED, and it is the round's most consequential finding for the reader.** Every round-1 disposition was kept in `INGEST.md` and in the probes and in **neither** of the two documents that carry the row's evidence. §1–§4 are re-run and re-pasted from the amended kit, §5 is written, and design test 5 gets its own section |
| **A3** | **BLOCKING** | **§9 — the standing-constraint-8 accounting section — is wrong three ways after the fix, and round 1 verified it right before the fix.** **(i)** **[Observed]**, re-verified by the worker: the distinct `C20-` ids number **74**, and §9 line 924 reads ***"Seventy-six rules, seventy-six planned ids, `C20-01` … `C20-74`"*** — off by two and self-contradictory in one sentence. `git show 07af54f^:docs/specs/INGEST.md` said *"Sixty-two rules, sixty-two planned ids"*, which was correct. **(ii)** The pre-fix table gave ordinals for every reserved value; the amended one gives an ordinal for the refusal and **none for the four warnings**, and *"the reservation is written so the count stays reconcilable"* was deleted. **(iii)** **Two vocabulary values the fix itself minted are reserved nowhere.** **[Observed]**, re-verified: `len(types.WARNING_VALUES)` = 37, `'consumers_unregistered' in WARNING_VALUES` = **False**, `'no_tenancy_predicate' in WARNING_VALUES` = **False** — and the kit emits both on **every** call. §9 says *"**Five** vocabulary values are RESERVED here"*; there are **seven** | **ACCEPTED.** R11's reservation is what keeps `check_spec_drift.py` reconcilable with the closed tuples, and it is what **Q85** is about. This is standing rule (d) failing **inside the section whose only job is to enumerate**: F8's fix minted two values and the commit that minted them did not name §9. Also accepted: §9 names `warnings` as the carrier for two handles that §4.4 amendment A3 records **[Observed]** `record_invocation` cannot carry — §9 and §4.4 must agree |
| **A4** | **BLOCKING** | **Rule 2-15 (`C20-66`), minted to close M7, is not implementable as written, and its implementation is a wrapper the primitive's own caller walks past.** The rule: *"a record the predicate fails is `None` **with a `why`**"* — but primitive 22 returns `InstanceRecord \| None`, so **[Observed]** `type is NoneType -- no room for a why`. The guard lives in `get_instance_checked`, not in primitive 22, and **[Observed]** the primitive itself returns the other tenant's row unchanged: `-> 'co-host' / '065001'`. **[Observed]** `ingest_seam_probe.py:439` calls `host.get_instance(...)` **directly**, and the check that passes on it is labelled *"T1.13 primitive 22 re-confirms a resolved ref at the moment of use"*. **[Observed]** `resolve_instance` never calls primitive 22 at all | **ACCEPTED.** F13's disposition was *"it has a real caller once named"* and M7's was that primitive 22 gain a tenancy surface; §2 names the caller in **prose** and no rule requires it and no code path performs it. The rule is restated where the return type can carry its `why`, and the row's own design test stops calling the unguarded door |
| **A5** | **BLOCKING** | **§8.1's claim *"Nothing else in §2, §3, §4, §5 or §6 is unexercised after the amendments"* is FALSE, proved by mutation.** 21 single-rule deletions, each followed by all five design tests; **two survive with all 87 green**: rule **2-5** (*a backend that cannot count returns `known=None`, never 0*) and rule **3-9** (*confidence `None` means did not score, never 0.0*). **[Observed]** `can_count=False -> known=None complete=True` and `grep -c can_count` across the five design tests is **0**; **[Observed]** a proposal whose predicate excluded every scanned row gives `confidence=None scanned=1`, and mutating it to `0.0` — the value `INTERFACE.md` §5.3 forbids — moves nothing | **ACCEPTED.** `C20-08` and `C20-23` have no check at all, and §3.4's third named absorber rides `C20-08`. Round 1 counted eleven countable absences; the amended §8.1 asserts three and it is at least five. The two rules get checks that go red, and §8.1's closing sentence is withdrawn |
| **A6** | MAJOR | **§12 still prints the withdrawn `18-of-100`.** **[Observed]**, re-verified by the worker: `INGEST.md:627` and `:1065` carry **31 of 100**; `INGEST.md:1029` carries ***"The 18-of-100 disagreement forced the threshold onto the entry"***. `39d3718`'s own message says *"the disagreement is 31 of 100, not 18, and the spec carries the new number"* — and the diff touched two sites of three | **ACCEPTED.** The number is the whole argument for putting the threshold on the entry and the document now gives two values for it. **The fix closed the two occurrences that prompted it and not the one beside them — the defect §6.4 says the round was about, reproduced by the round's own fix** |
| **A7** | MAJOR | **§13's intro contradicts §13's own closing line, in the section the fix rewrote.** **[Observed]**, re-verified: lines 1056–1058 read *"round 1 constructed **four** more through it ... and the **four** rows added by the loop are marked"*, and line 1075 reads *"Twelve routes, five of which this document listed and **seven** of which a loop constructed."* | **ACCEPTED.** The paragraph is pre-fix text the rewrite left behind, in the section whose own heading says it *"was NOT sufficient the first time"* |
| **A8** | MAJOR | **p-m2's disposition does not survive one day, and the printed range excludes the measurement the landing commit says it prints.** §2.1 prints *"**1.3 s to 8.4 s** in same-day runs"*; `39d3718`'s message says a third same-day measurement was **20.74s** and *"the spec now prints all three"*. **[Observed]** `grep -n "20.74"` over the whole repo returns **nothing**. **[Observed]** the lens's unmodified re-run today: `one 50000-row page took 0.65s` — **below the printed floor** | **ACCEPTED.** The range is false in both directions on the first re-run after it landed, and the commit message asserts a spec change the spec does not contain. p-m2's real lesson — *a live per-page timing is not a fact a spec can pin* — is not what the fix implemented; §2.1 states the affordability argument without pinning a number, and the numbers move to the run record with their dates |
| **A9** | MAJOR | **Rule 2-14's enforcement path inside `resolve_instance` is reached by no check, and the check that claims to reach it is green for an unrelated reason.** **[Observed]** T1.13's last call returns `Refusal('instance_source_absent')` — the **vocabulary** refusal — with `host reads performed: 0`, and the probe asserts only `isinstance(r13, Refusal)`. With the entry declared so the read happens, the guard does fire. **[Observed]** deleting the entire guard leaves that check green: `35/36`, and the one red is a different assertion | **ACCEPTED.** K8's disposition is kept in the rule and lost in the evidence: the only thing exercising it is a unit call on the helper. **This is M1's shape — a check that restates something else — surviving into the fix round** |
| **A10** | MAJOR | **`flat_form_ok` is a divergent second copy of the shipped guard rule 2-14 cites, and it reproduces the exact falsehood `C19-90` / `C19-94` closed.** **[Observed]** kit, `namespace='org:cms'` → *"`parse_ref` would read back a **different reference**"*; shipped `flat_form_problem`, same input → *"`ref_key` would write a string `parse_ref` **RAISES** on, so the ledger row it writes cannot be read back at all"*. The shipped function's own comments record why it **asks** `parse_ref` instead of classifying: *"a case analysis over `(field, separator)` is a second home for `parse_ref`'s grammar ... and it is the thing that went stale here within one commit"* (`C19-94`, row 6c round 3 **fix-auditor lens**). Nothing imports the shipped guard | **ACCEPTED.** This is contortion **ING3** — *two notions of the same string* — arriving at the guard itself, and standing rule (d) once more: the rule was minted at primitive 23 and the commit did not name the shipped implementation it binds, in the same commit that cited `C19-82` as its evidence |
| **A11** | MAJOR | **The kit's tied set carries a `>= propose_below` floor the spec does not state, and it papers over a contradiction between §3.2 and §5's own table.** Kit: `near_top = (top.score - c.score) <= margin and (c.score >= policy.propose_below)`. Rules 3-3 (`C20-17`) / 5-8 (`C20-73`) state the tied set with **no floor**. **[Observed]** two candidates tied inside the margin and both below `propose_below` (`ACME REHAB OF SPRINGFIELD` / `SPRINGVILLE`, both 0.5714) → `outcome='proposal'`, while §5's table row 2 says `ambiguous` and row 4 says `proposal` **for the same input** | **ACCEPTED.** K2's disposition claimed the set test *"needs no second constraint"*; there **is** a second constraint, it lives in the code and not in the document, and a build-row implementer reading rules 3-3 and 5-8 writes the other behaviour. §5's table and §3.2 are made to agree, and the floor is either stated as a rule or removed |
| **A12** | MAJOR | **Rule 2-13's only two checks assert its warning on the outcomes rule 2-13 is not about, so M2's actual population is posed by nothing.** Rule 2-13 (`C20-64`) is about a **`proposal`** decided over a narrowed set — M2's *"3,330 of 3,330 landed rows resolved `proposal` with `complete=True`"*. **[Observed]** DT1's check asserts it on an `existing` and DT2's on an `ambiguous`; the kit appends the warning to **every** outcome, unconditionally on `host_filter` | **ACCEPTED.** Not one narrowed `proposal` is asserted anywhere, and the implementation is wider than the rule, so the handle that was supposed to say *"this proposal was decided over a slice"* does not distinguish proposals |
| **A13** | MINOR | **§14 still says *"the four design tests"*.** **[Observed]**, re-verified: `INGEST.md:1094`. Five ship | **ACCEPTED**, and it is A2's shadow: the exit criteria are accurate about the record and wrong about the artefacts |
| **A14** | MINOR | **Kill-criterion route 5 is prose nothing tests.** *"an ingest family proposes a `kind=\"predicate\"` type at volume → rule 4-8"*. **[Observed]** no probe constructs a family with `Effect(op="propose_type", kind="predicate")` | **ACCEPTED.** It is an **original** route, not one of the seven the loop added — the lens confirmed each of those seven goes red under deletion |
| **A15** | MINOR | **`assert_adapter_boundary` inspects only the fixture adapter.** **[Observed]** `inspect.getsource(HostTable)` is the whole check; `SocrataServiceRequests` — the implementation running against 9.7M live rows — is never inspected, so rule 2-6 (`C20-09`) is enforced against the fixture and not against the real one | **ACCEPTED** |
| **A16** | MINOR | **§5.2's two percentages no longer come from one run.** §5.2 says *"46% of the fetched rows share an address and the probe discards 32% of them"*; **[Observed]** the amended probe prints `129 sharing one (32%)` — it labels **32%** as the *sharing* rate | **ACCEPTED.** M3's disposition was that §5 print the real number **and say what the fixture does**; a reader cannot reconcile 46% with anything the probe emits |

#### 6.5c What the lens attacked and could NOT break — carried forward so round 3 is not re-tread

1. **`I-1`'s own fix, attacked by mutation from three directions.** `_mutate="rule_u_last"` goes red in DT1
   **and** DT2 **and** DT4; deleting the `if not complete` branch, the `undecided` branch and the
   `scanned == 0` branch each go red. **The ordering is real, load-bearing, and now tested in three places.**
   The only confident answer over a wrong extent the lens obtained was A1, which does not pass through this
   guard at all.
2. **"One kit replaces two resolvers" — the disagreement was DECIDED, not deduplicated.** **[Observed]**
   exactly one `resolve_instance`, one `evaluate`, one `norm`, one `similar` across all six files, all in the
   kit, and `_rule_u()` runs before the branches. **K7's correct ordering (design test 3's) won.**
3. **Rules 3-3 / 3-4's `ref=None` on `ambiguous`.** Not populatable; putting the top ref on an `ambiguous`
   result goes red immediately. **The shape trips 11 and 12 took still does not reproduce.**
4. **The set test against K2's actual population.** Reverting to a top-two margin comparison goes red in two
   probes. The `MAGNOLIA ... - WEST` / `- EAST` and `Mountain View` pairs are genuinely caught — A11 is about
   a **floor**, not about K2's band.
5. **Rules 6-4 / 6-5 / 6-12 / 6-16, the three-valued language.** Every deletion goes red. Round 1's
   could-not-break #6 still holds and is now the ordering the whole kit uses.
6. **Rules 2-7 / 2-10 / 2-8 — the P2 and M8 fixes.** Ignoring an undeclared `host_filter` key goes red;
   making `label` narrow goes red in **four probes at once**. `host_filter` really is a named mapping and
   `label` really is non-narrowing, in the kit and in **both** host adapters.
7. **Rule 2-11's cursor exhaustion is tested — but by DT2 alone.** Stopping the identity read at the first
   page leaves DT1, DT3, DT4 and DT5 **all green**; only DT2 goes red, on `ambiguous complete=True` over 1,000
   of 9,768,174 rows. Not a finding, because the suite as a whole catches it — **recorded because four of the
   five design tests cannot see the fifth trip's own shape.**
8. **`C20-01` and the R78 seam, from a fourth direction.** `resolve_instance` returns
   `InstanceResolution | Refusal`, `CandidateRef` has no `id` field at all, `HostTable` has no writer.
   **Four lenses have now failed to force an instance row into the registry.**
9. **Rules 5-2 / 5-3 / 5-9 at declaration and at the gate.** Both refused in `__post_init__`; turning the band
   into a `proposal` goes red twice. **K3 is genuinely closed** — DT4 prints
   `['ambiguous','existing','proposal']` and the `match`/`propose`/`review` vocabulary is gone from every
   probe. *(It survives only in the run record — which is A2.)*
10. **Rules 4-10 / 4-11 and design test 5.** F4 and K4 are each constructed and each proved by mutation,
    10/10. A fourth way to cash a pending proposal was caught by `invocations(unreviewed=True)`.
    **§6.2c's countable absence #9 is genuinely closed.**
11. **The `C20-xx` grammar itself.** **[Observed]** 74 distinct ids, no gaps, 74 rule rows, one id each. Only
    the **prose count** is wrong (A3), never the mapping.
12. **`check_links.py` and `check_spec_drift.py`.** Both green, as the commits claim. Neither covers
    `INGEST.md`, which is why A3 and A6 are invisible to them — stated in §8, and not a defect.

#### 6.5d What this lens says about the register's own prediction

**The register predicted the defect would be inside the fix, and it was — five BLOCKING inside a diff of two
commits.** More precisely, and this is the part worth carrying: **three of the five are the SAME failure the
round they fix was about.** A6 is *"closed the occurrence that prompted it and not the one beside it"*,
verbatim, in the commit whose own message announced the number change. A3 is standing rule (d) failing inside
**the section whose only job is to enumerate**. A10 is standing rule (d) failing in a commit that cited row
6c's fix-auditor finding as its evidence. **A round's fixes are written by the person who has just read the
findings, and that is exactly when the enumeration feels finished.**

**And A2 is the one a reader meets first.** Every disposition of round 1 was kept in two artefacts and in
neither of the two documents that carry the row's evidence. The run record still prints the vocabulary the
spec now forbids.

---

### 6.6 Round 2, lens 2 — **the beacon integrator. NOT YET: 5 BLOCKING, 4 MAJOR, 4 MINOR.**

**The verdict in one sentence:** *the capture path still does not go through — it no longer stops at the
first call, it stops at the second **reference**, and rule 4-10 is where.*

Round 1's beacon lens found the path stopped at the first call, because the thing being proposed could not be
named as an input. `CandidateRef` genuinely closed that (§6.6c item 3). What round 1's fix did not do is give
the *per-act* rules the scope the per-call rules already had. **[Observed]** baseline reproduced before
anything: DT1 36/36, DT2 13/13, DT3 17/17, DT4 11/11, DT5 10/10 = **87/87**; the lens worked in an isolated
worktree and modified no repo file, building four constructions against the real kit and the shipped package.

#### 6.6a The kill-row family again — **three of the five BLOCKING findings end in two host rows answering to one identity, with rules 4-10 and 4-11 fully enforced**

**1. `I-3` (proposed) — rule 4-10 has no type scope, and a capture act is multi-type by construction.**
Rule 4-10 (`C20-70`) verbatim, and the worker re-verified it at `INGEST.md:586`: *"**Within one ingest act a
label is resolved once**; later references to it in that act reuse the first `CandidateRef`"* — **no
`(namespace, kind, type_name)`**. Rule 4-11, **one line below at `:587`, has one.** Implemented exactly as
written, over one act carrying a `project` and a `task` that share a label:

```
land(project , 'Meridian') -> proposed  CandidateRef(type_name='project', label='Meridian')
land(task    , 'Meridian') -> reused    CandidateRef(namespace='beacon', kind='entity',
                                        type_name='project', label='Meridian',
                                        resolution='proposal', act_id='act-c6')
invocations recorded: 1  [('project', 'Meridian')]
the two CandidateRefs are the SAME object: True
the TASK ends up named by: type_name='project'
```

**Proved by mutation:** adding the type to the key gives `2` invocations and `SAME object: False`.
**[Observed]** design test 5 cannot see it — `IngestAct.__init__` fixes `type_name` for the whole act, so a
multi-type act is not constructible in it. And **§8 of this same document already knows the case**: `siblings`
was typed in round 1 precisely because *"a capture resolving a task was handed a project name and a person
name with nothing to tell them apart."* **Standing rule (d) inside the fix commit once more** — the qualifier
was written onto 4-11 and not onto 4-10 beside it, in the same commit that typed `siblings` for this reason.

**2. `I-4` (proposed) — rule 4-11 names a door that cannot answer its question.** Rule 4-11 asks
`invocations(unreviewed=True)` *"who already holds a pending proposal for **this label** under this
`(namespace, kind, type_name)`"*. **[Observed]**, re-verified by the worker against the shipped
[`Registry.invocations`](../../ontoloche/registry.py) signature —
`(*, family, namespace, actor, outcome, gate_verdict, effect_undeclared, unreviewed, since, limit=100)`:
there is **no `label` filter, no `type_name` filter and no `kind` filter**. `ACTIONS.md` §6.3 says in terms
*"It does not page"*, and **[Observed]** [`ontoloche/backends/_sql.py`](../../ontoloche/backends/_sql.py)
line 1915 is `ORDER BY created_at, invocation_id LIMIT {limit}+1` — so the page is the **oldest 100**. One
ordinary 250-row batch, the same facility at rows 150 and 250:

```
DT5's own ledger              -> complete=True   warnings=('instance_proposal_pending:inv-150',)
                                 identities minted: 1
the ledger ACTIONS SHIPS      -> complete=False  why='limit of 100 truncated the answer'
                                 the repeat's warnings: ()
                                 invocations carrying the pending warning: 0
                                 identities minted on approval: 2
```

**And rule 4-11's read is an identity read**, so §3's own rules bind it: rule 2-11 says an identity read
*"exhausts the cursor or reports truncated; it never reads one page and decides"*, and §3.4 says an unfinished
one is `unknowable` **whatever it found**. Rule 4-11 reads one page of a non-paging call and decides. This is
`I-1`'s operand — *partial is not equal* — at a **third** surface.

**3. `I-5` (proposed) — rules 4-10/4-11 dedupe by the RAW STRING while §3 and §5 decide identity by the
normaliser.** Two spellings of one real CMS facility, in one act, both rules on:

```
norm(A) == norm(B) -> True ('the sarah roberts french home')      similar(A,B) -> 1.0
A == B  (rule 4-10 / 4-11's test)                                 -> False
counterfactual: if row 1 were already written, row 2 resolves
                outcome='existing' ref='cms:entity:facility#HOST-1' confidence=1.0

one act, both rules ON:
  land outcomes    = ['proposed', 'proposed']
  ledger           = 2 invocations, warnings=[(), ()]
  host writes      = ['HOST-1 / THE SARAH ROBERTS FRENCH HOME',
                      'HOST-2 / The Sarah Roberts French Home.']
  the NEXT resolution -> outcome='ambiguous' known=2 confidence=1.0 complete=True
```

**F4's exact outcome, with F4's fix fully enforced.** This is contortion **ING3** — *two notions of the same
string* — arriving at the **act** layer, where it costs an identity rather than a refusal. A capture writes
one name two ways in one meeting note as a matter of course.

**4. `I-6` (proposed) — rule 4-10's per-act memory is written only on the `proposed` branch, and a warned
invocation is still an approvable permission.**

```
act-0 lands the label once      -> 'proposed';  unreviewed=1
act-1 lands the SAME label TWICE -> 'pending', 'pending'
  resolve_instance host reads inside act-1 = 2   (one per resolution)
  act-1's own rule-4-10 memory _minted = {}      <-- the label was resolved twice in one act
queue: inv-1 mode='auto' warnings=()   inv-2/inv-3 ('instance_proposal_pending:inv-1',)
drain it the ordinary way (§4.2: the host writes on approval, and NO rule in §4 refuses a
write for an invocation carrying `instance_proposal_pending`)
  host writes = ['HOST-1', 'HOST-2', 'HOST-3']
  the NEXT resolution -> outcome='ambiguous' known=3 confidence=1.0
```

Rule 4-11's *"mints no second identity"* is a claim about the **invocation**, not about the **write**, and
nothing binds the write door. That is contortion **ING2**'s advisory-at-the-only-enforcing-door arriving at
rule 4-11, where ING2 records it only for rule 4-7.

**Classification is not the worker's and not the lens's.** On [**R83**](../decisions/2026-09-04-7a-supervisor-ruling-R83.md)'s
reading all four are constructed against a **specification** and a **throwaway kit**, so they are proposed as
instance-surface records and **the fourteen-trip count is not incremented**. `I-4` is the one closest to the
line, because its measurement is of the **shipped** `invocations` signature and the **shipped**
`ORDER BY created_at … LIMIT`. Routed to the supervisor.

#### 6.6b Every finding, with its disposition

| # | severity | finding | disposition |
|---|---|---|---|
| **B1** | **BLOCKING** | **Rule 4-10 has no type scope — §6.6a.1.** One act, `project 'Meridian'` and `task 'Meridian'`: the task **reuses the project's `CandidateRef`** and is never proposed | **ACCEPTED.** Rule 4-10 gains `(namespace, kind, type_name)`, as rule 4-11 one line below already has, and §4.3's rule 1 with it. Design test 5 gains a **multi-type act** — `IngestAct` takes `type_name` per `land`, not per act — and the check goes red without the qualifier |
| **B2** | **BLOCKING** | **Rule 4-11 names a door that cannot answer its question — §6.6a.2.** **[Observed]**, re-verified: the shipped `invocations` has **no `label`, `type_name` or `kind` filter**, `limit=100`, and `_sql.py:1915` orders by `created_at` — the oldest page. On a 250-row batch the repeat carries **no** warning and **two** identities are minted | **ACCEPTED, and §4.4 gains a FOURTH amendment**: `invocations` needs a `label`/`type_name` filter and a completeness answer. Rule 4-11 gains its own Rule-U branch, because its read is an identity read and rule 2-11 already binds it. **§6.5c item 10's "caught by `invocations(unreviewed=True)`" is corrected on the record** — it was caught by design test 5's own `Ledger.unreviewed(...)`, which is not that call |
| **B3** | **BLOCKING** | **Rules 4-10/4-11 dedupe by the raw string; §3 and §5 decide identity by the normaliser — §6.6a.3.** One document, two notions of *the same thing*, disagreeing **inside one act** | **ACCEPTED.** The per-act rules dedupe over whatever §3 calls the same thing, or the document states they are exact-string and prices it in **ING3** |
| **B4** | **BLOCKING** | **The capture's relationship half has no path, no non-goal, no contortion and no question — and §12 tells the reader it is handled.** F5's disposition was *"the spec must say so rather than imply it"*. **[Observed]**, re-verified by the worker: `'relationship'` occurs **2** times in `INGEST.md` (the VISION quote and §12's row), `'add_edge'` **0**; §0.1's non-goals name no relationship; §10's ING1–ING10 contain none about edges; §11's Q85–Q90 contain none. The walk: two `proposal`s, then `InstanceRef(id=None)` → `TypeError`, `ref_key(CandidateRef)` → `AttributeError`, and `NodeRef = TypeRef \| InstanceRef`. §12 row 3 meanwhile answers *"**No.** Inherited, not designed — and the one part of §4 round 1 could not break"* | **ACCEPTED, and it is A2's shape inside round 1's own fix set**: a disposition kept in the run record and landed in **none** of §0.1, §10 or §11. §0.1 gains the non-goal, §10 gains the contortion with the walk pasted, §11 gains the question, and §12's row is corrected so a reader cannot conclude the relationship half is covered |
| **B5** | **BLOCKING** | **Rule 4-10's per-act memory is written only on the `proposed` branch — §6.6a.4.** Three approvals for one label, `ambiguous known=3` after | **ACCEPTED.** Either rule 4-11's warning binds the approval door, or §10 records that it does not — ING2's shape, at the rule minted to close K4 |
| **M1** | MAJOR | **`InstanceCandidate.discriminators` is documented as the opposite of what a reviewer needs, and implemented as a third thing.** **[Observed]**, re-verified at `INGEST.md:881`: `discriminators: dict # the host attributes that did NOT separate the tie`. On the real 12-way tie: `discriminators[0] = {'city':'WARSAW','state':'IN','zip':'46580','address':'1630 S COUNTY FARM RD'}`, and *"of those keys, the ones that DO separate the tie: `['address','city','zip']`"* | **ACCEPTED.** An implementer reading §8 literally filters to the non-separating set and hands the reviewer `{'state':'IN'}` — **deleting the only signal that resolves the tie**, on the queue rule 4-5 routes every ambiguous capture into. The comment is corrected and the kit's behaviour becomes the rule |
| **M2** | MAJOR | **Amendment A1 names one surface, and the ledger's actual storage is a second one it does not name.** ACTIONS §2.3 / **R72**: *"what the ledger actually holds for each argument is the flat string `ref_key` writes"*. **[Observed]**, re-verified: `ref_key(CandidateRef)` → `AttributeError`; `ontoloche.actions.REF_SHAPES` → **`('type','instance','edge')`**; and inside §4.4 the strings `ref_key`, `parse_ref`, `REF_SHAPES` and *flat form* occur **zero** times | **ACCEPTED.** The ACTIONS row could land A1 exactly as written and the capture would still be unable to record an invocation. **Standing rule (d) in the section whose only job is to enumerate what must land** — A3's shape, one section along |
| **M3** | MAJOR | **`CandidateRef.label` is a prose string in a reference shape, and no rule guards its flat form.** Rule 2-14 (`C20-65`) binds `InstanceRecord`'s three fields only. **[Observed]** on labels a meeting note actually produces — `'Q3: migration'`, `'sprint #14'`, `"Dana's 1:1"`, `'OKR #2: latency'` — the shipped `flat_form_problem` returns `None` for every one, because `ref_shape` is `None` for a shape ACTIONS does not know. **[Observed]**, re-verified: §4.1 contains `flat_form_problem` **zero** times | **ACCEPTED.** `C19-82` / **K8** — *a confident reading of the wrong thing* — arriving at the **fourth** reference shape, minted in the same fix round that closed it at the third |
| **M4** | MAJOR | **`InstanceContext` is the call's second positional argument and NO rule in the document binds it.** **[Observed]** over `resolve_instance`'s source: `label_source` read **False**, `row_attributes` **False**, `siblings` **False**, `proposed_by` **False**, `act_id` **True**. **[Observed]** INGEST rules 1-1…7-4 mentioning `InstanceContext` or any field: **none**. A 12-way tie **with `siblings` supplied** still answers `ambiguous known=12` | **ACCEPTED.** F9 said the fields were never *run*; the amendment makes DT1 construct the object and assert nothing about its effect — **A9's shape, a check green for an unrelated reason.** ING8 prices the *emptiness* of two fields; nothing prices the *inertness* of all five |
| **b-m1** | MINOR | **§4.1's printed `CandidateRef` and the kit's diverge, undetectably.** §4.1 prints `type: TypeRef`; the kit's is `CandidateRef(namespace, kind, type_name, label, resolution, act_id)`. `check_spec_drift.py` does not cover `INGEST.md` | **ACCEPTED.** The one shape this document *adds* is printed one way and implemented another |
| **b-m2** | MINOR | **§4.1's own comment is false for half the values `resolution` may take.** `CandidateRef: # NEW … A thing that does NOT exist yet`, while `resolution` is *"`proposal` or `ambiguous`"* and `ambiguous` means **more than one held instance** answers. **[Observed]** the 12-way tie yields `CandidateRef(… resolution='ambiguous')` — twelve things that **do** exist, cached by rule 4-10 for reuse at every later reference | **ACCEPTED** |
| **b-m3** | MINOR | **Design test 5 models two ACTIONS amendments and labels one.** Its `Invocation` carries `minted_ref` (labelled as amendment A2) **and** `approval_mode` and `warnings`, which are amendment **A3** and are labelled nowhere — so DT5's rule 4-5 and rule 4-6 checks are green against a ledger §4.4 says does not exist | **ACCEPTED**, and it is one more row §8.1's *"still unexercised"* table does not carry |
| **b-m4** | MINOR | **ING8 counts four `InstanceContext` fields; §8 prints five.** **[Observed]**, re-verified: `INGEST.md:966` says *"two of `InstanceContext`'s **four** fields"*; the printed shape at `:854` carries `label_source`, `row_attributes`, `siblings`, `act_id`, `proposed_by` | **ACCEPTED** — an enumeration error inside the contortion that is the strongest evidence for **Q86** |

#### 6.6c What the lens attacked and could NOT break

1. **`not_an_instance` from prose is recorded honestly, and the measurement only extends it.** Against a
   25-word real capture vocabulary: **[Observed]** `answered not_an_instance: 0 of 25` — all 25 `proposal`.
   ING8 says exactly this and it is softened nowhere. **Round 3 should not re-measure it.**
2. **ING8's `row_attributes` / `siblings` asymmetry is honestly stated.** Typing `siblings` did not and could
   not change 104/104 vs 0/104 — tied candidates share a label, so their siblings are identical — and §8's
   claim is about type-mixing, not tie-breaking. No overclaim. M4 is a different defect: **inertness, not
   emptiness.**
3. **`CandidateRef` genuinely closes F1's first-call stop.** The entity half now has an invocation to make;
   `CandidateRef` has no `id` field at all and the reviewer could not make one acquire one. **Five lenses have
   now failed to force an instance row into the registry** — `C20-01` / R78 hold from a fifth direction.
4. **§4.2's provenance claim, re-checked for the relationship case.** `InvocationProvenance` carries actor,
   tier, confidence, approver and `source_version`; nothing is missing. It stays the one part of §4 that holds
   as written — the defect is that §12 makes it answer a question about *relationships* that it does not.
5. **Rule 4-7 and rule 3-6 at the act door.** `land` over a truncated read → `unknowable`, ledger holds **0**
   invocations. No route from `unknowable` to a proposal, in-act or across acts.
6. **Rules 3-3 / 3-4 / 5-8 at the act layer.** Every duplicate above was produced *between* correct
   resolutions, never by a wrong one; every post-hoc resolution correctly reported `ambiguous` with
   `ref=None`. **The set test is not the weak point; the act scope is.**
7. **`Effect(op="add_edge")` is not the missing piece.** The gate, the family, the namespace-from-inputs rule
   and the provenance for a relationship write all ship. **What is missing is only the endpoint.** So B4 is a
   scope-and-statement defect, not an ACTIONS capability gap — round 3 should not hunt an `add_edge`
   amendment.
8. **Deliberately not attacked by this lens:** §2.2's paging states, §6's twelve terms and their Kleene
   composition, §6.2's null handling, design tests 2 and 3's live measurements, and the whole of §6.5's
   A1–A16. No finding here duplicates one of those.
