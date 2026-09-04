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

#### 6.2a The trip — **a truncated scan that FINDS a match answers `existing` at 1.0 on a label twelve facilities answer to**

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
