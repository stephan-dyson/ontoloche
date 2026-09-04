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
