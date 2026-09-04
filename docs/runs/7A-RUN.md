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

## 1. Design test 1 — **the R78 seam. VERDICT: CONFIRMED. 36/36.**

> **RE-RUN AND RE-PASTED 2026-09-04, and this notice is round 2's finding A2 being closed.** Round 1's and
> round 2's fixes landed in `INGEST.md` and in the probes and **in neither of the two documents that carry
> this row's evidence** — **[Observed]** `git log --oneline 07af54f^..39d3718 -- docs/runs/7A-RUN.md` returned
> nothing. So §1–§4 went on printing the check counts, the headline numbers and, at §4, the three-verdict
> vocabulary (`match` / `propose` / `review`) that finding **K3** killed and rule 5-4 now forbids in terms.
> **Every block below is re-pasted from a run at `83f6a75`**, and where a number moved, the old one and the
> reason are kept rather than overwritten — the point of the section is the evidence, not the tidiness.
>
> **The check counts, then and now:** 16 → **36**, 10 → **13**, 12 → **17**, 7 → **11**, and design test 5 is
> new at **27**. **87 → 104 across the row.**

**Probe:** [`docs/tools/ingest_seam_probe.py`](../tools/ingest_seam_probe.py). **Run 2026-09-04 at `83f6a75`,
36/36 checks pass, exit 0.** Two engines, as `actions_nyc_probe.py` uses them: the **shipped**
`ontoloche.Registry` on SQLite holds the vocabulary — so *"no instance rows"* is a claim about the real
store — and the host table plus `resolve_instance` are throwaway kit, because this row ships no product code.

### 1.1 Observed output, pasted — **the run at `83f6a75`**

```
DESIGN TEST 1 -- the R78 seam, over CMS `NH_HealthCitations_Aug2026.csv`
  source: https://data.cms.gov/provider-data/dataset/r5ix-sfxw
  file: 165336194 bytes, 419479 rows
  host table: 14627 CCNs, 14498 distinct provider names, 104 names shared by more than one CCN

  R77 control -- resolve_type('BURNS NURSING HOME, INC.')
    -> outcome='not_a_type' reason='instance_not_type'

T1.1 -- 'BURNS NURSING HOME, INC.' (one CCN in the file)
  -> outcome='existing' ref='cms:entity:facility#015009' confidence=1.0 scanned=14627 complete=True
     warnings=('no_tenancy_predicate', 'consumers_unregistered')

T1.2 -- "MILLER'S MERRY MANOR" (twelve CCNs in the file)
  -> outcome='ambiguous' known=12 confidence=1.0   ... 12 in the tied set

T1.3 -- 'THE SARAH ROBERTS FRENCH HOME' (CCN 745040), HELD OUT of the host table
        a real facility arriving new, which is the honest shape of a proposal
  -> outcome='proposal' confidence=0.6415 scanned=14626 complete=True

T1.4 -- 'Provider Name', the column header landed as a value
  -> outcome='not_an_instance' scanned=0

T1.5 -- 'Tuskegee Airmen Texas State Veterans Home', row 14,623 of 14,627, scan capped at 14000
  capped   -> outcome='unknowable' complete=False scanned=14000
  uncapped -> outcome='existing' ref='cms:entity:facility#745057'
  MUTATED (Rule U last) -> outcome='unknowable'

T1.6 -- R58's three states off one primitive
     the set: known=14627 complete=True next_after=None
      a page: known=500 complete=False next_after='045350'
   truncated: known=14000 complete=False next_after=None

T1.7 -- what the registry holds after all of it
  registry rows: [('entity', 'facility')]

T1.8 -- ROUND 1's TRIP (`I-1`): truncation with the match FOUND
  cap=3541 (1 of the twelve read, 11 unread)
  FIXED   -> outcome='unknowable' ref=None complete=False scanned=3541
  MUTATED -> outcome='existing' ref='cms:entity:facility#155049' confidence=1.0

T1.9 -- two candidates both at or above match_at, over a COMPLETE scan
  'Mountain View Health Care' (115688) vs 'MOUNTAIN VIEW HEALTHCARE' (265412)
  -> outcome='ambiguous' ref=None known=2 complete=True

T1.10 -- a score inside the band answers in the FIVE, not a sixth verdict
  'BURNS NURSING HM INC' -> outcome='ambiguous' confidence=0.9524

T1.11 -- the type is retired underneath the instances
  resolve(type_name='facility') after retire(successor='nursing_facility')
  -> outcome='existing' ref='cms:entity:nursing_facility#015009' scanned=14627
     warnings=('instance_type_succeeded:nursing_facility', ...)
  a read of ZERO rows -> outcome='unknowable' scanned=0

T1.12 -- the two capability flags 2.3 mints
  resolves_instances=False -> Refusal('instance_source_absent')
  a host_filter key outside instance_filters -> complete=False
       why='host_filter keys this backend does not declare: ownership_type'

==============================================================================
36/36 checks pass
R78 VERDICT: CONFIRMED -- every outcome is reachable over a host-held table,
             through two read primitives, with no instance row in the registry.
```

**Three things in that block were not in round 1's, and each is a fix made visible.** **T1.3** no longer
resolves an invented name — it holds out a **real** CCN, which is the honest shape of a proposal and closes
round 1's complaint that the fixture proved nothing. **T1.8** is `I-1` itself, constructed and mutation-proved
at the door it was found at. **T1.11** is the retired-type case round 2's `I-2`, `I-3` and `I-7` all live in.

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

## 2. Design test 2 — **paging under load (R58). 13/13, live against `erm2-nwe9`.**

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

## 3. Design test 3 — **the two-tenant loop (R59 / R60). 17/17, over CMS CA + CO.**

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

## 4. Design test 4 — **"I already know 38 of these". 11/11, over live 311 rows.**

**Probe:** [`docs/tools/ingest_gate_probe.py`](../tools/ingest_gate_probe.py). `ROADMAP.md` homes instance
resolution in Phase 3 with the walkthrough's *"I already know 38 of these"*. **Re-run 2026-09-04 at
`83f6a75`, 11/11**, and the block below replaces one this document printed until round 2's **A2**: the old
one carried `{'match': 38}` / `{'review': 23}`, **a three-verdict vocabulary finding K3 killed and rule 5-4
now forbids in terms**, and a headline number round 1's **M3** had already shown to be an artefact of one
`setdefault` line.

```
DESIGN TEST 4 -- "I already know 38 of these", the confidence gate
  live from https://data.cityofnewyork.us/resource/erm2-nwe9.json, 2026-09-04
  host narrowing: {'agency':'NYPD','complaint_type':'Illegal Fireworks','incident_zip':'11214'}
  400 rows fetched, 271 with a distinct address, 129 sharing one (32%)
  landing batch: 100 rows (38 known / 24 abbreviated / 38 new)

4.1 the gate on a host holding ONE instance per address (match_at=0.97 propose_below=0.8)
    known: {'existing': 38}
   banded: {'ambiguous': 23, 'existing': 1}
    novel: {'proposal': 38}
     banded:ambiguous  e.g. '2260 BENSON AVE' @ 0.9091
     banded:existing   e.g. 'BATH BEACH PARK' @ 1.0
     novel:proposal    e.g. '25 BAY   13 STREET REAR ANNEX 2031' @ 0.6122

  the number: 38 of 38 already-known rows matched

4.2 outcomes that fired across the batch: ['ambiguous', 'existing', 'proposal']

4.3 the SAME batch against the host's ACTUAL rows -- round 1 finding M3
    (`erm2-nwe9`'s instance is a service request keyed by unique_key, not an address)
    known: {'ambiguous': 13, 'existing': 25}
   banded: {'ambiguous': 23, 'existing': 1}
    novel: {'proposal': 38}

  the honest number: 25 of 38 matched, 13 correctly refused to guess

4.4 the same batch under two ENTRIES declaring different thresholds
    (which is what a per-CALL threshold would let two callers do)
  31 of 100 rows resolve DIFFERENTLY

4.5 a candidate the read could not finish
  over a truncated read -> outcome='unknowable' complete=False
  MUTATED               -> outcome='existing'

11/11 checks pass
```

**§4.3 is the number this row actually stands behind, and it is not the headline one.** *"38 of 38"* is true
of a host holding **one instance per address**, and **[Observed]** `erm2-nwe9`'s instance is a service request
keyed by `unique_key` — so against the host's real rows the answer is **25 of 38 matched and 13 correctly
refused to guess**. Round 1's M3 found the headline was an artefact of a `seen.setdefault(address, r)` line;
**the fix was to print both numbers and say which fixture each describes**, because the fixture's number is
still the one that answers the walkthrough's question and the honest number is the one a build row must plan
for. **§4.4's disagreement is 31 of 100, not the 18 this document printed until round 2** — and the two callers
are now two **entries**, because a per-call threshold is exactly what §5.1 refuses.

**§4.5 closes the loop back to design test 1**: a candidate the scan could not score is `unknowable` at the
gate too, and the mutation proves the check goes red.

---

## 4a. Design test 5 — **the ingest ACT (`INGEST.md` §4.3). 27/27, over CMS facilities.**

*(Numbered `4a` rather than `5` on purpose: `INGEST.md` §8.1 and this document's §6.1a both cite "§5 of this
document", so §5 keeps its number and the fifth design test takes the letter. Renumbering to tidy an
appearance would break two citations, which is the trade this row does not make.)*

**Probe:** [`docs/tools/ingest_act_probe.py`](../tools/ingest_act_probe.py), on the one kit. **This design
test did not exist before round 1's fixes**, and round 1's own §6.2c counted its absence as countable absence
#9: *"zero `record_invocation`, zero `invocations(`, zero `InvocationProvenance` — §4, the whole
propose-at-ingest contract, has no probe at all."* It is now the largest of the five.

```
DESIGN TEST 5 -- the ingest ACT (INGEST 4.3), over CMS facilities
  host: 14627 CCNs; the landed rows name a facility it does NOT hold

5.1 -- two landed rows in ONE act name the same facility          [F4]
  RULE 4-10 ON : ['proposed','reused']  writes=[#HOST-1]  -> existing known=1
  MUTATED      : ['proposed','proposed'] writes=[#HOST-1,#HOST-2] -> ambiguous known=2

5.2 -- the same label landed in three SEPARATE acts, none reviewed  [K4]
  RULE 4-11 ON : 3 invocations, 1 host write
     pending-warnings=['instance_proposal_pending:inv-1', ...]  -> existing known=1
  MUTATED      : 3 invocations, 3 host writes, no warnings       -> ambiguous known=3

5.3 -- two workers read the SAME state and neither repeats a call
  outcomes=['proposed','proposed']  writes=2  -> ambiguous known=2

5.4 -- a proposal made while the resolution was `ambiguous`
  land("MILLER'S MERRY MANOR") -> proposed, approval_mode='review'
     warnings=('instance_ambiguous_at_proposal:facility:12',)
  invocations(unreviewed=True) -> 1

5.5 -- rule 4-7: nothing is proposed over an `unknowable` resolution
  land over a truncated read -> 'unknowable'; ledger holds 0 invocations

5.6 -- the instance-surface table, each cell proved by MUTATION
  I-2 CHAIN : hops=[...nursing_facility, ...ltc_facility]
  I-2 MUTATED (one hop): hops=[...nursing_facility]
  I-2 rider HONEST STOP: unknowable complete=False
  I-2 rider MUTATED (keeps predecessor): proposal complete=True
  I-7 GOVERNED : unknowable          I-7 MUTATED (ignored): proposal
  I-6 DISTINCT : unknowable known=2  I-6 MUTATED (ignored): existing known=1
  I-4 NORM KEY : ['proposed','reused'] ledger=1
  I-4 MUTATED (raw label): ['proposed','proposed'] ledger=2
  B1 per-land type: 'proposed' then 'proposed'
  I-5 UNWRITTEN: 'proposed' -> drained -> 'pending'
  I-5 MUTATED (unreviewed only): 'proposed' -> drained -> 'proposed'
  I-3 WHOLE CLOSURE: the minted row stayed under 'facility'; second act -> 'existing'
  I-3 MUTATED (endpoint only): second act -> 'proposed'
  Z6 FENCED: land('Provider Name') -> 'not_an_instance'; ledger=0
  Z6 MUTATED (unfenced): -> 'proposed'; ledger=1

27/27 checks pass
```

**§5.3 is the one that is honest about what this layer cannot do.** Two workers reading the same state and
neither repeating a call still produce two host writes, and **no rule in §4 stops them** — the guard is
advisory at the only door that enforces (contortion **ING2**). Round 2's **Z3** found §13's route table
claiming the concurrent case *closed* while this very check constructs it **open**, with the disclaimer
living only in a probe's `check()` string and pointing at `PACKAGE.md`'s **G1**, which is uniqueness in the
**type** store and therefore permanently out of this document's reach under rules 1-1 and 2-1.

**§5.6 is the seven-cell table, and it is the section round 3's fix auditor is pointed at.** Every cell has a
paired arm: the fix asserts the correct answer, the mutation asserts the defect reproduces. §6.10e carries the
sweep that removes each fix at source and confirms **nine of nine red**.

## 5. What each round cost — **the section two documents cite and that did not exist**

**[Observed]** until `83f6a75` this document had no §5, while `INGEST.md` §8.1 cited *"§5 of this document's
run record carries the count"* and §6.1a cited *"recorded in §5 of this document as what the round cost"*.
That is round 2's **A2** in its purest form: a disposition kept in one artefact and in none of the others.

### 5.1 The row, in numbers

| | before the loop | after round 1 | after round 2 |
|---|---|---|---|
| `INGEST.md` rules / planned ids | 62 | 74 | **85** |
| design tests | 4 | 5 | 5 |
| checks across them | 45 | 87 | **104** |
| kill-criterion routes (§13) | 5 | 12 | 12 |
| reference shapes | 3 | 4 (`CandidateRef`) | 4 |
| contortions recorded | 8 | 10 | **11** |
| amendments asked of `ACTIONS.md` | 0 | 3 | **5** |
| questions open | — | Q85–Q90 | **Q85–Q91** |
| instance-surface records | 0 | 1 (`I-1`) | **7** (`I-1`…`I-7`) |
| kill-row trips | 14 | **14** | **14** |

### 5.2 What each round cost, in one paragraph each

**Round 1 cost the row its probes.** Three lenses, 37 findings, 11 BLOCKING. The fixes to `INGEST.md` were the
cheap half; the expensive half was that **a mutation deleting §3.4's load-bearing sentence left the suite
printing `16/16`**, design test 2's headline outcome was computed from a flag rather than from a resolver, and
design test 4's headline number was an artefact of one `setdefault`. Two resolvers became one kit with a
mutation harness. **Eleven countable absences** were the measure of what the old probe set could not ask.

**Round 2 cost the row its idea of what a defect is.** Four lenses, 47 findings, 19 BLOCKING — **the findings
did not shrink, they grew** — and the fix auditor found five BLOCKING inside round 1's own two commits. Seven
failures of standing rule (d), every one inside the fixes of the round that cited rule (d) as its reason for
existing. But the finding that changed the row is that the nine constructions were **not nine defects**: they
are **one question asked at seven doors**, and the register ruled them a table (`I-1`…`I-7`) rather than a
list. The fix set is therefore one change, and **standing rule (e)** is what it states.

**And the cheapest thing the row bought was the harness's own defect.** §6.10e-i: the first mutation sweep
reported a real defect as *surviving*, because it disabled a fix by flipping a default the design tests
override explicitly. **That is the row's own M1/A9 shape in its own tooling, one round after it recorded
both** — and it cost one re-run to find, because the sweep was built to be checked.

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

#### 6.5a `I-2` — **the successor chain is followed for ONE hop, and two ordinary curation passes give two confident answers at 1.0 for one identity**

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

**COUNTERSIGNED 2026-09-04 — [R84](../decisions/2026-09-04-7a-supervisor-ruling-R84.md). `I-2` is
confirmed, the count stays at fourteen, and the ground is FIRMER than this record claimed.**

The worker routed the classification rather than assuming it, and R84 verified the record against the two
files it cites rather than against its paragraph — **[Observed]** the one-hop `break` at
[`ingest_probe_kit.py`](../tools/ingest_probe_kit.py) lines 491–499, and the shipped comments at
[`registry.py`](../../ontoloche/registry.py) line 1403 (*"The chain, not one hop (row 4d, round 2)"*) and
line 1421 (*"Capped and cycle-guarded the way `_identity_closure` is"*). Three things R84 adds:

1. **The argument this record made was the weaker one available.** It argued the negative — *constructed
   against a specification and a throwaway kit*. The stronger statement, and R84's: **the shipped surface is
   the CONTROL in this construction and it PASSES.** `_identity_closure` already walks the chain with a
   visited set, a hop cap and an honest early stop. So this is not a defect the register could not reach at
   the type surface — **it is one the type surface already closed, in row 4d round 2, which this document
   re-opened by restating the ruling instead of citing the implementation.** A construction whose shipped
   control passes is not a kill-row trip by any reading.
2. **Standing rule (d) gains a second clause, and it is minted by this record.** *A rule minted at the caller
   that prompted it is half-applied until the commit that mints it names every other caller it binds —* **and
   the enumeration crosses the document boundary. A rule minted in a specification must name the shipped
   callers it binds; and where a shipped caller already implements the rule, the specification cites that
   implementation as its normative reference rather than restating the ruling the implementation was derived
   from.** Rule 3-14 cites **R38** and implements none of R38's three termination rules; `_identity_closure`
   implements all three. **The spec should have pointed at the code.**
3. **The fix is constrained, so `I-2` is not closed narrowly** — see §6.10, where it lands as one row of the
   table rather than as its own fix: rule 3-14 requires what `_identity_closure` requires (visited set, hop
   cap, `complete=False` **with a `why`** on an early stop); **the rider defect in the same four lines is
   closed in the same change** — `entry = vocab.entry(namespace, effective_type) or entry` keeps the
   **predecessor's** entry when the successor's is absent, which is **the eighth trip's shape**, a guard
   holding one fact while deciding about another; and rule 3-14's text **names the shipped caller it binds.**

**`stop` is not put** — it attaches to trips. **The kill-row trip count is not incremented anywhere.**

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

---

### 6.7 Round 2, lens 3 — **the kill row. NOT YET: 4 BLOCKING, 3 MAJOR, 1 MINOR, and four more constructions in the family.**

*(Lenses 2, 3 and 4 were dispatched together in isolated worktrees; sections are numbered in the order the
lenses returned, because the rule is that each is written to disk as it returns.)*

**Provenance first, standing rule (a).** **[Observed]** `git diff --name-only a1b0364^..HEAD -- ontoloche/`
returns nothing and `grep -rc "resolve_instance\|MatchPolicy\|find_instance_candidates\|InstanceResolution"
ontoloche/` returns zero on every file. **Row 7a still ships no door**, so there is no earlier commit to
bisect: Z1, Z2, Z3, Z4, Z5, Z6 and Z7 are constructed against the **specification**, the **one kit**, and
**design test 5's own ledger**. The constructions that reach the **shipped** `ref_key` / `parse_ref` /
`flat_form_problem` / `InstanceRef` are in §6.7c, and **they held**.

**[Observed]** baseline reproduced before anything: 36/36, 13/13 (live `erm2-nwe9`), 17/17, 11/11, 10/10 =
**87/87**, and every finding below was reached with those 87 still green. Mutations were on copies with
`PYTHONPATH` pointed at the worktree; **no repo file was modified.**

#### 6.7a `I-3` … `I-6` — the four records, written to the standard the fourteen trip records set

**COUNTERSIGNED 2026-09-04 — [R85](../decisions/2026-09-04-7a-supervisor-ruling-R85.md). Records A, B, C and
D are `I-3`, `I-4`, `I-5` and `I-6`; the kill-row trip count stays at FOURTEEN and `stop` is not put.**

R85 spot-checked this record's three countable-absence claims rather than accepting them — **[Observed]**
`grep -c successor ingest_act_probe.py` → **0**, the same over `ingest_seam_probe.py` → **6**, and
`grep -c 'reviewed_by *=' ingest_act_probe.py` → **1**. All three reproduce exactly.

| record | in one line | id |
|---|---|---|
| **A / Z1** | rule 3-14 binds the identity READ and no door that WRITES | **`I-3`** |
| **B / Z2** | the act's scope key is the raw label and the gate's is `norm` | **`I-4`** |
| **C / Z4** | a drained-but-unwritten proposal is invisible to rule 4-11 | **`I-5`** |
| **D / Z7** | the tied set dedupes on `ref_key`, so two host records under one `instance_id` collapse | **`I-6`** |

**And R85's substance is that these are not four fixes.** See §6.10: the six instance-surface records are
**one table — one question asked at six doors** — and they are closed in **one change**, not one quadrant per
round in the order the lenses found them. This record's own sequencing note (*"Z1 … it is the fix to make
first"*) is right that Z1 is load-bearing and **wrong about the shape**, and R85 says why: trips 8, 12, 13 and
14 were four quadrants of one table closed one at a time over **three build rows**, because each round closed
the quadrant it found and stopped.

**Record A (Z1) — the successor chain binds the READ door and no door that WRITES.** **[Observed]**, full
165,336,194-byte CMS file, the repo's unmodified probes and kit:

```
ACT 1 (no successor yet): land('THE SARAH ROBERTS FRENCH HOME') -> 'proposed'
  reviewed by user:curator;  invocations(unreviewed=True) = 0
  host minted cms:entity:facility#HOST-1
  CONTROL, before any governance act:
    outcome='existing' ref='cms:entity:facility#HOST-1' conf=1.0 complete=True

GOVERNANCE ACT: retire('facility', successor='nursing_facility')
  the host migrates 14626 rows and leaves HOST-1 under 'facility'

ACT 2: land('THE SARAH ROBERTS FRENCH HOME') -> 'proposed'
  outcome='proposal' ref=None conf=0.6415 scanned=14626 complete=True why_incomplete=''
  warnings=('instance_type_succeeded:nursing_facility', 'no_tenancy_predicate',
            'consumers_unregistered')
  host minted cms:entity:facility#HOST-2

TWO HOST ROWS, ONE FACILITY -> once the migration finishes: ambiguous known=2 conf=1.0
```

**Rule 3-14 fired correctly, reported itself in a warning, and the duplicate was minted anyway.** §4.2 and
rule 4-3 never say **which** type the host writes under, and rule 4-11's key `(namespace, kind, type_name)`
never says which `type_name`. **Both readings break**: write under the declared name and the chain-following
read can never see it again; write under the effective name and the ledger key misses across the retire.
**[Observed]** `grep -c "successor" ingest_act_probe.py` = **0** — six in the seam probe, zero in the other
four; the successor lives in one probe and the ledger in another and **no construction puts them in one
room**, which is *trip 14's own count shape verbatim*. **MUTATION PROOF:** applying the fix to a copy leaves
design test 5 at **10/10** — the gate is blind to the rule's presence *and* its absence.
**Cross-reference: trip 14**, and it is `I-2`'s sibling rather than its duplicate — `I-2` is the chain
stopping after one hop; this is the chain **followed correctly** with only the read door bound by it.

**Record B (Z2) — the act's scope key is the raw string and the gate's is `norm`. This is lens 2's B3,
reached independently from the other direction, and it is the round's convergence.**

```
A='THE SARAH ROBERTS FRENCH HOME'   B='The Sarah Roberts French Home,'
norm(A) == norm(B) -> True          similar(A,B) -> 1.0
THE GATE, asked directly: resolve(B) against a host holding A
  -> outcome='existing' ref='cms:entity:facility#HOST-A' conf=1.0
ONE ACT, rules 4-10 and 4-11 both ON:
  outcomes=['proposed','proposed']  writes=[#HOST-1, #HOST-2]  warnings=[(),()]
  the NEXT resolution -> ambiguous known=2 conf=1.0
```

**The population is real, public, and the worker re-derived every figure from the file rather than taking the
lens's paragraph. [Observed] 2026-09-04**, over the same 165,336,194-byte file, using the kit's own `norm`:

```
rows: 419479   CCNs: 14627
distinct RAW names:  14498   shared by >1 CCN: 104
distinct NORMALISED: 14427   shared by >1 CCN: 155
normalised keys carrying MORE THAN ONE raw spelling: 71
examples: ['PARK PLACE','Park Place'] ['HERITAGE HEALTH CARE CENTER','Heritage Health Care Center']
          ['CHRISTIAN CARE NURSING CENTER','Christian Care Nursing Center']
```

**MUTATION PROOF:** rekeying rule 4-10 on `norm(label)` leaves design test 5 at **10/10** — the gate cannot
tell which key the rule uses. **[Observed]** all five `land()` sites pass one of exactly **two** string
constants and all five `IngestAct` constructions pass `namespace="cms", type_name="facility"`.
**Cross-reference: K3's shape at a new pair of artefacts**, and contortion **ING3** arriving inside §4.3.

**Record C (Z4) — a DRAINED proposal is an unconsumed permission.**

```
act-1 land(label) -> 'proposed'                 invocations(unreviewed=True) = 1
review_invocation(reviewed_by='user:curator')   invocations(unreviewed=True) = 0
the host has NOT written yet  (rule 4-2: the write is the host's)
act-2 land(label) -> 'proposed'   warnings=()
both approvals then land -> [#HOST-1, #HOST-2] -> ambiguous known=2
```

Rule 4-6 makes `review_invocation` the **only** drain and rule 4-11 makes `unreviewed=True` the **only**
question, so **draining removes the pending proposal from the guard's view while the identity it authorises
still does not exist.** The window is not exotic; it is the specified sequence, because §4.2 puts the write on
the host and `ACTIONS.md` §4's gate is advisory (**ING2**). **[Observed]** `ingest_act_probe.py` contains
exactly **one** `reviewed_by =` assignment and **no** `land()` after it.
**Cross-reference: standing rule (c) verbatim, one surface down and one drain along** — K4 was the permission
cashed while pending; this is the permission **re-issued because it was cashed**, and it is this round's
closest thing to trip 12's *a guard evaluated once for a call that can run twice*.

**Record D (Z7) — the tied set dedupes on `ref_key`, so two different host records sharing one `instance_id`
collapse to one.**

```
two host rows, one instance_id -> outcome='existing' ref='cms:entity:facility#015009'
                                  known=1 scanned=2 conf=1.0
candidates=[('cms:entity:facility#015009','BURNS NURSING HOME, INC.',1.0)]
   -- the second row ('BURNS NURSING HOME INC', state='TX') is GONE
```

Rule 1-1 makes `instance_id` the host's and opaque; **no rule requires a `CandidatePage`'s ids to be
distinct**, and §3.2's set test silently treats a repeated id as one candidate. `flat_form_problem` correctly
returns `None` — the id is the field the grammar may carry anything in. **ING5 already measured that a host
keyed on a non-unique natural column is the ordinary case** (59.7% of `uvpi-gqnh`'s 683,788 instances share an
address). **Cross-reference: trip 8's empty-key collision at the instance layer**, which round 1's §6.2d
recorded as *not constructible* — **it is constructible; it just needs the host's id rather than the label to
be the colliding field, and round 1 checked the label side and stopped.**

#### 6.7b Every finding, with its disposition

| # | severity | finding | disposition |
|---|---|---|---|
| **Z1** | **BLOCKING** | **Rule 3-14 binds the identity read and nothing binds the write — §6.7a Record A.** One ordinary `retire(successor=)` between two acts mints a second identity with every §3 rule firing correctly | **ACCEPTED, and it is the fix to make first.** §4.2 / §4.3 must say **which** `type_name` the host writes under and **which** the rule 4-11 ledger key uses; everything else in Record A follows from that one absent sentence. Rule 3-14's enumeration is extended to the write door per standing rule (d), and design test 5 gains a `retire(successor=)` |
| **Z2** | **BLOCKING** | **Rules 4-10/4-11 scope on the RAW label; the gate decides identity on `norm` — §6.7a Record B.** **[Observed]**, re-derived by the worker: **71** normalised keys carry more than one raw spelling, and the shared-name count is **104 raw / 155 normalised** | **ACCEPTED, and this is lens 2's B3 independently reached** — the round's convergence, exactly as K1/P1 were round 1's. One fix closes both: the per-act rules key on whatever §3 calls the same thing, or the document states they are exact-string and prices it in ING3 |
| **Z3** | **BLOCKING** | **§13 asserts a route CLOSED that the row's own design test constructs as OPEN, and routes it to a guarantee that cannot cover it.** Route 9 says *"a pending proposal is cashed twice, **or by two concurrent workers** … Rule 4-11"*. **[Observed]** design test 5's own check 5.3 constructs two workers reading one state, `writes=2`, `ambiguous known=2`, and passes with the message *"this document says so"* — and **[Observed]**, re-verified by the worker, the document does **not** say so: `concurrent` occurs in `INGEST.md` only in §4.3's quotation of K4's evidence and in §13's route row. **[Observed]** `PACKAGE.md` §3.5's **G1 is uniqueness in the TYPE store** | **ACCEPTED.** The route table is the artefact whose job is to say what stops the kill row, and one of its twelve rows is false; the disclaimer lives only in a probe's `check()` string and points at a guarantee that rule 1-1 and rule 2-1 put permanently out of this document's reach. Either route 9 drops the concurrent clause and §10 gains the contortion, or §4.3 gains a rule — **it cannot be both** |
| **Z4** | **BLOCKING** | **A drained-but-unwritten proposal is invisible to rule 4-11 — §6.7a Record C.** The guard asks who holds an *unreviewed* proposal rather than who holds a proposal at all | **ACCEPTED.** The guard is at the wrong end: it blocks the second proposal while the first is undrained, and stands down at exactly the moment the first is approved and still unwritten |
| **Z5** | MAJOR | **The gate's BAND branch caps `known` and `candidates` at 5 over a FINISHED read, and rule 4-5's `<n>` inherits the cap.** **[Observed]** `resolve('BURNS NURSING HM INC')` → `ambiguous conf=0.9524 complete=True scanned=14627 known=5 len(candidates)=5`, of which exactly **one** is banded and four score 0.76–0.79; the reviewer's warning is `instance_ambiguous_at_proposal:facility:5`. The tied branch by contrast gives `known=12`. **[Observed]** the only `known` assertions in all five design tests are `== 12` and `== 2` — **zero** on the band branch | **ACCEPTED.** Rule 3-4 (`C20-18`) says *"every tied candidate is returned"* and §8 prints `known: int` with no cap; rule 4-12's *"counted over a finished read"* is satisfied and the number is still meaningless. §4.3's own note said K9's fix *"cannot be scoped narrowly and lose it"* — **it was scoped to the unfinished-read case** |
| **Z6** | MAJOR | **Rule 4-7 fences `unknowable` and nothing fences `not_an_instance`.** **[Observed]**, re-verified: rule 4-7 (`C20-33`) reads *"A resolution of `unknowable` yields **no** proposal"* and names no second outcome. So: `resolve('Provider Name') -> not_an_instance scanned=0`, then `land('Provider Name') -> 'proposed'`, ledger `[('inv-1','Provider Name','not_an_instance','auto')]`, host writes `#HOST-CLASSWORD (label='Provider Name')`, and re-landing it in the same act returns `'reused', object=None` where a `CandidateRef` is contracted. **MUTATION PROOF:** extending rule 4-7 to `not_an_instance` leaves design test 5 at **10/10**; `grep -c "not_an_instance" ingest_act_probe.py` = **0** | **ACCEPTED, and it is not ING8.** ING8 is a classifier that misses; this is the classifier **succeeding** — §3.3's *"the cheapest correct answer is the one that asks the host nothing"* — and §4 proposing over it anyway, in `auto` mode, unrouted to review. Rule 4-7 names one of the **two** outcomes that must mint nothing |
| **Z7** | MAJOR | **The tied set dedupes on `ref_key` — §6.7a Record D.** Two different host records under one `instance_id` collapse to one and answer `existing` at 1.0 with `known=1` | **ACCEPTED.** Either §2 gains a rule that a page's `instance_id`s are distinct-or-`unknowable`, or §3.2 says what a repeated id means |
| **Z8** | MINOR | **§1's pre-registered *"104 provider names shared by more than one CCN"* is the RAW count; the gate collides on the normalised key, where the figure is 155.** **[Observed]**, re-derived by the worker: `RAW 14498 / shared 104` vs `NORMALISED 14427 / shared 155` | **ACCEPTED.** Nothing pre-registered is *wrong* — §1 says the four figures were independently re-derived and they were, twice — but they describe a surface `resolve_instance` **does not use**. The number that describes the gate's own collision surface is **155**, and the 51-name gap is exactly Z2's population. Both numbers are printed, with what each one measures |

#### 6.7c What the lens attacked and could NOT break

1. **The shipped flat-form grammar, from four instance-surface directions A9/A10 did not walk.**
   **[Observed]** empty `namespace` → `':entity:facility#015009'` round-trips; empty type name →
   `'cms:entity:#015009'` round-trips; empty id → `'cms:entity:facility#'` round-trips and is **distinct** from
   the `TypeRef` key `'cms:entity:facility'`; a non-`str` id is refused at `InstanceRef.__post_init__` with
   EDGES 2.1's own message. **No two distinct instance references collide in `ref_key` once
   `namespace`/`kind`/`name` are separator-free.** The one misreading route — an `InstanceRef` over a
   `kind="edge"` type — is **already recorded in `parse_ref`'s own docstring**, forbidden by EDGES 2.1, and
   INGEST pins `kind="entity"`. A9 and A10 remain the live findings there; **no third was found.**
2. **Rule 3-4's `ref=None` on `ambiguous`.** Held under every construction, including the band branch, the
   retired-type branch and the duplicate-id branch. **The shape trips 11 and 12 took still does not
   reproduce.**
3. **Rule 4-11 across a retire while the first proposal is still PENDING.** **[Observed]** act 2 answers
   `'pending'` with `instance_proposal_pending:inv-1` and **no** second mint. *The ledger key staying on the
   declared name is what saves it* — which is why Z1's two horns cannot be fixed independently.
4. **Rule U's ordering, from a fifth direction.** No construction produced a confident answer over an
   unfinished read; every path through the band, the retired type and the duplicate id reported `complete=True`
   honestly. §6.5c item 1 stands.
5. **The R78 seam, from a fifth lens.** Nothing needed an instance row in the registry; every duplicate above
   was written by the host. **Five lenses have now failed to force one.**
6. **`namespace` at the instance surface.** `find_instance_candidates` filters on it, `vocab.entry` is keyed
   on it, and a dangling successor yields `scanned=0` → `unknowable`. **`namespace` is untouched at the
   instance surface as it has been across all fourteen trips.**
7. **`MatchPolicy` at declaration.** Rules 5-2 / 5-3 refuse in `__post_init__`; no policy reaches the gate
   malformed. **A11's floor is about the tied set, not about the declaration.**
8. **Kleene composition and the three-valued language.** No predicate made §6 decide something it could not
   read. Design test 3's ordering remains the one the whole kit uses.

#### 6.7d The countable-absence count, re-run over the AMENDED kit — **nine, and three are a previous trip's count shape**

Round 1's §6.2c counted eleven over the old probes. Over the amended artefacts:

1. **Zero** `IngestAct` / `Ledger` references outside `ingest_act_probe.py` — §4's entire contract is posed by
   **one** of the five design tests.
2. **Zero** `successor` in `ingest_act_probe.py` — Z1's quadrant. ***Trip 14's count shape verbatim.***
3. **Zero** `not_an_instance` in `ingest_act_probe.py` — Z6's quadrant.
4. **Zero** `norm(` in `ingest_act_probe.py` — Z2's quadrant; the act's key is never compared with the gate's.
5. **Exactly two** distinct label constants across all five `land()` sites, and **one** `(namespace,
   type_name)` pair across all five `IngestAct` constructions.
6. **One** `reviewed_by =` in the whole file, with **no** `land()` after it — Z4's quadrant.
7. **Zero** assertions of `known` on the **band** branch — Z5's quadrant.
8. **Zero** fixtures in which two host records share an `instance_id` — Z7's quadrant.
9. **Zero** `can_count` across all five — carried from A5, because §3.4's third named absorber rides `C20-08`.

**The sentence this register has now written ten times, at this row** — and at round 2 it has a sharper form:
*§4's only probe holds **one** label, **one** type and **one** namespace, so every quadrant of §4.3 except the
one that prompted it is unposed.*

#### 6.7e Standing rule (d) — a fifth through eighth failure, all inside round 1's own fix set

Lens 1 found three (A3, A6, A10). These are four more:

1. **Rule 3-14** minted at the identity read; binds the propose door and the host write (Z1).
2. **Rules 4-10 / 4-11** minted with the word *label*; bind `norm`, the gate's own identity function (Z2, B3).
3. **Rule 4-7** minted for `unknowable`; binds `not_an_instance`, the other outcome that must mint nothing (Z6).
4. **Rules 3-4 / 4-12** minted at the tied branch; bind the band branch, where `known` is capped at 5 (Z5).

**Seven failures of standing rule (d) in one round, every one inside the fixes of the round that invoked
standing rule (d) as its own lesson.** That is the sharpest thing round 2 has to say, and §6.9 says it again
with the totals.

---

### 6.8 Round 2, lens 4 — **the public data. NOT YET: 5 BLOCKING, 4 MAJOR, 1 MINOR, and TEN of twenty mutations survive.**

**[Observed]** baseline reproduced first: 36/36, 13/13, 17/17, 11/11, 10/10 = **87/87**. Every mutation was
applied to **copies**; no repo file was modified.

**This lens's verdict has a shape the other three do not: the row's own gate cannot see its own FIRST TWO
RULES being deleted.** Round 1's public-data lens proved the gate blind to §3.4's load-bearing sentence by
mutation. Round 2's proves it blind to `C20-01` and `C20-04` — *this project stores no instance rows and mints
no instance identifiers*, and *a write primitive for instances is a conformance failure* — **the two rules the
R78 seam rests on.**

#### 6.8a D4 — **ten of twenty mutations leave all 87 checks green, and the two worst are §1's own rules**

**[Observed]**, each mutation applied to a copy of the one kit with all five design tests re-run:

```
M15  rule 1-1  C20-01  -- this project mints no instance identifiers
     resolve_instance hands back a registry-invented ref on the live path where the
     entry's predicate excluded every scanned row, over 209 real Colorado facilities:
       outcome='existing' ref='cms:entity:facility#minted-by-registry' conf=1.0
       scanned=209 complete=True
     -> 36/36  13/13  17/17  11/11  10/10      SURVIVES

M01  rule 2-1  C20-04  -- two primitives, both READS
     added `put_instance` to HostTable                              SURVIVES 87/87
M02  rule 2-2  C20-05  -- get_instance manufactures a record for an absent key   SURVIVES
M03  rule 3-4  C20-18  -- returns 1 of 12 tied candidates, still reports known=12  SURVIVES
M04  rule 3-11 C20-25  -- `tier` returned as ""; `.tier` asserted in no probe      SURVIVES
M10  rule 6-17 C20-58  -- a `tenant` parameter added to CandidateQuery            SURVIVES
M11  rule 2-12         -- the warning names host_filter VALUES instead of keys    SURVIVES
M16  ING3 / C4-14      -- norm's ASCII-only collapse                             SURVIVES
M17  rule 3-1  C20-15  -- a sixth value added to OUTCOMES                        SURVIVES (weak)
M20  rule 3-9  C20-23  -- confidence=None, never 0.0                             SURVIVES (= A5)
```

**Ten of twenty survive; eight are survivors A5 did not name**, so §8.1's *"Nothing else in §2, §3, §4, §5 or
§6 is unexercised after the amendments"* is false by **at least ten** rules rather than two.

**And this qualifies a claim this run record has now made twice.** §6.5c item 8 and §6.7c item 5 both say
*five lenses have failed to force an instance row into the registry*. **That remains true and it was
established by READING** — `HostTable` genuinely has no writer as shipped, and this lens confirms it
independently (§6.8c item 8). What M01 and M15 show is different and worse: **the row's own gate cannot detect
either rule's deletion.** The seam holds; the *check* that it holds does not exist. That distinction is now
written into §1 and §8.1 rather than left for a sixth lens to find.

The ten that went red are listed in §6.8c so round 3 does not re-run them.

#### 6.8b Every finding, with its disposition

| # | severity | finding | disposition |
|---|---|---|---|
| **D1** | **BLOCKING** | **The kill-row family on the fixture the spec itself measured: rules 4-10/4-11 are a false-merge factory over real NYC data, because they key on `label` and §5.2/ING5 already prove the label is not an identity.** **[Observed]**, live `erm2-nwe9`, `agency=NYPD` / `complaint_type='Illegal Fireworks'` / `incident_zip=10032`, 3,342 real service requests: **`2746 of 3342 (82.2%) share their address with another REQUEST in the same slice`**, and `'1001 SAINT NICHOLAS AVENUE'` carries **twenty** distinct `unique_key`s. One act → `['proposed','reused',…]`, `ledger rows: 1` — **one `CandidateRef` for twenty genuinely distinct requests**. Across acts → `act-tuesday` gets `'pending'`, `identities minted: 1`. At batch scale, 842 real held requests and 800 real rows landed in one act: **`{'proposed': 316, 'existing': 112, 'reused': 372}` — 46.5% of a real ingest batch is never resolved, never scored, never recorded and never reviewed** | **ACCEPTED, and it is the third independent route to round 2's convergence** (with lens 2's B3 and lens 3's Z2). §5.2 states in terms that *the instance in `erm2-nwe9` is a service request keyed by `unique_key`*, and ING5 measures 59.7% address-sharing on `uvpi-gqnh` — **the document contradicts itself and the public data decides against 4-10/4-11 as written.** Design test 5 cannot see it because its fixture is a CMS provider name, where one label really is one thing, and `land()` is never called with a `host_filter` at all |
| **D2** | **BLOCKING** | **A shape that does not survive UC3's own stated wedge: the store cannot be bootstrapped.** Rule 3-13 (`C20-67`, minted by round 1 to close K6) makes `scanned == 0` `unknowable`, and rule 4-7 forbids a proposal over an `unknowable`. **[Observed]** 800 real `erm2-nwe9` rows landed into an **empty** host: `{'unknowable': 800}`, `ledger rows written: 0`. Same over a *declared* `host_filter` key narrowing to zero rows: `outcome='unknowable' scanned=0 warnings=(…, 'instance_narrowed_proposal:incident_zip')` | **ACCEPTED.** `USE-CASES.md` UC3's natural task is *"land N datasets and get typed entities and relationships"* — **the first landed row of every dataset resolves `unknowable` for ever and no first instance can be proposed.** K6's case was a *retired type*; rule 3-13 as written binds **every** empty read, including the empty-store and empty-slice cases §2.1's own affordability argument creates. Rule 3-13 must distinguish *the type resolved to something with no rows* from *this namespace holds nothing yet* |
| **D3** | **BLOCKING** | **Rule 3-14 silently swaps the SUCCESSOR's governed facts in under the caller — §6's tenancy predicate and §5's `MatchPolicy` both — and one ordinary `retire(successor=)` reaches R59's stated reversal condition.** **[Observed]**, design test 3's own CA+CO fixture with a California-only `Condition` on the entry the caller named: control → `existing #555338 CA`, `CO rows visible to this CALIFORNIA caller: 0`; **after one `retire(successor='ltc_facility')`** → `ambiguous known=2 warnings=('instance_type_succeeded:ltc_facility', …)`, `CO rows visible to this CALIFORNIA caller: 1 ['cms:entity:ltc_facility#065240']` — **5 of 5**, exactly P3's population and outcome, reached by retiring a type instead of omitting a keyword. Policy half, same data: **`73 of 1373 real CMS labels resolve DIFFERENTLY once 'facility' is retired`** | **ACCEPTED, and it is distinct from A1** (which is a two-hop chain giving two confident identity answers). Nothing in §5, §6 or §7 says a successor inherits its predecessor's `MatchPolicy` or `Condition`, and §7.2 makes the successor's entry **someone else's to declare**. §5.1's rule 5-6 — *two entries may declare different policies; two callers may not* — is defeated: **one caller gets both policies.** Aggravating and accepted with it: **rule 5-7 (`C20-41`) has no carrier** — `InstanceResolution` has no policy field and shipped `Invocation.declared_policy` carries `approval_mode`/`min_auto_tier`/`reversibility`, not the three thresholds. §4.4 names three amendments and does not name this one |
| **D4** | **BLOCKING** | **Ten of twenty mutations leave all 87 green, and the two worst are rule 1-1 and rule 2-1 — §6.8a** | **ACCEPTED.** §8.1's closing sentence is withdrawn (already accepted at A5, now with the true magnitude), and **§1 gains an honest statement that the seam's two rules are asserted and unchecked.** Checks that go red are added for `C20-01`, `C20-04`, `C20-05`, `C20-18`, `C20-25`, `C20-58` and rule 2-12 |
| **D5** | **BLOCKING** | **§3.2's *"Seven real CMS pairs land in it"* is wrong by at least 4.4x.** **[Observed]**, **re-derived independently by the worker** over all 14,627 distinct CCNs with the kit's own `similar(norm(a),norm(b))`, blocked on the first three normalised characters with a length window: **`pairs 0.97 <= s < 0.98 : 31`** and **`pairs 0.98 <= s < 0.99 : 31`**. The two the spec names are both in it, and among the rest: `'Springcreek Rehabilitation and Nursing Center'` vs `'SPRING CREEK …'` at 0.9890, `'Greenville Health and Rehabilitation Center'` vs `'GREENSVILLE …'` at 0.9885, `'VALLEY HEALTH CARE CENTER'` vs `'VALLEY HEALTHCARE CENTER'` at 0.9796, and `PARKVIEW`/`PARK VIEW CARE CENTER` in six states. **Blocking makes 31 a lower bound** | **ACCEPTED.** The number is the measured size of the near-miss population rules 3-3 / 5-8 exist to catch, it is cited in §3.2 **and** in §13 route 7, and it understates the row's own fixture pathology by more than four times. Both bands are printed with the method that derived them, and **ING6's *"the near-miss population is real"* is more real than the document says** |
| **D6** | MAJOR | **M2's fix does not do what §2.1 claims: *"the reviewer can see what was not looked at"* is false over real NYC data.** **[Observed]** the label `'DYCKMAN STREET'` against three live `erm2-nwe9` slices — `incident_zip=10032` → `proposal scanned=3342`, `10040` → `ambiguous scanned=2921`, `10034` → `ambiguous` — **all three carrying the byte-identical warning `instance_narrowed_proposal:incident_zip`.** The 10032 proposal mints a new identity for a string the same host table answers to in two other slices | **ACCEPTED, and distinct from A12** (which is that the warning is appended to every outcome). Rule 2-12 keeps the values opaque **on purpose**, so the honest fix is to **withdraw §2.1's claim** and carry a *magnitude* the reviewer can act on — `scanned`, or the narrowed/unnarrowed ratio — rather than a key list |
| **D7** | MAJOR | **§3.3's second illustrative number is not a member of the population it illustrates.** **[Observed]** the no-house-number population is `861,798 rows (3.85%)` over `16,005` distinct values today, `'BROADWAY' 24,166` — the headline figures reproduce — and the classifier that produced them **excludes anything starting with a digit**. `'5 AVENUE'` carries 12,827 rows and **starts with a digit**, so it is not one of the 16,005 | **ACCEPTED.** The measurement is right and the example is misfiled — and it matters, because `'5 AVENUE'` is precisely the case showing a house-number heuristic **cannot** work, presented as one the heuristic caught. The same sentence appears in this run record at §6.3b and is corrected there too |
| **D8** | MAJOR | **ING5 converts *"share an address"* into *"resolve `ambiguous`"* 1:1, and `ambiguity_margin` makes the real rate higher and the tied sets 2.3x larger.** **[Observed]**, ING5's own `uvpi-gqnh`, one real zipcode (4,341 real DPR instances — the narrowed case §2.1 blesses), 150 real landed rows: `rows sharing an address: 1727 (39.8%)` → `{'ambiguous': 69, 'existing': 81}`, **`ambiguous rate 46.0% where ING5 predicts 39.8%`**, `tied-set sizes min=2 median=2 max=51`, `mean tied set 6.2 vs mean exact-duplicate group 2.7`. ING5's whole-table figures reproduce exactly (683,788 / 408,701 / 59.70% / 132) | **ACCEPTED.** **59.7% is a floor on the `ambiguous` rate, not the value**, and ING5 prints it as the value. The gap is `ambiguity_margin` pulling in near-miss addresses on the same street — the same mechanism D5 measures on CMS — so both the cost rule 4-5 imposes and the multiplicity `<n>` a reviewer sees are larger than the contortion says |
| **D9** | MAJOR | **`discriminators` is printed as *"the host attributes that did NOT separate the tie"* and contains attributes that fully separate it — on 104 of 104 CMS ties by ING8's own measurement.** **[Observed]** the 12-way tie: `'city'` 12 distinct → SEPARATES ALL, `'zip'` 12 distinct → SEPARATES ALL, `'address'` 12 distinct → SEPARATES ALL; only `'state'` does not. ING8's 104/104 re-derived independently with exactly those four attributes | **ACCEPTED**, and it is lens 2's M1 reached from the data side — **two lenses independently.** The one field a human draining §4.3's queue is given to act on tells them the opposite of the truth on every CMS tie. Mutating it to `{}` goes red, so *something* is asserted; **nothing asserts what it means** |
| **d-m1** | MINOR | **§3.2's K2 argument turns on a figure the document does not print.** §3.2 says *"with this document's own printed numbers — `match_at=0.97`, `ambiguity_margin=0.02`"*. **[Observed]**, re-verified by the worker: `0.02` occurs in `INGEST.md` **only inside that sentence** (line 346), and every probe declares `ambiguity_margin=0.03`. With 0.03 the band and the margin are equal and **there is no arithmetic gap** | **ACCEPTED.** The rule K2 produced (3-3 / 5-8, the set test) is correct and independently justified, and D5 shows the population it guards is real and larger than claimed — **only the motivating arithmetic is stated against a number the row does not carry**, and §13 route 7 repeats it |

#### 6.8c What the lens attacked and could NOT break

1. **Every pre-registered CMS figure, re-derived independently from the 165,336,194-byte file.**
   `419479 / 14627 / 14498 / 104`, `headers: 23`, `Deficiency Corrected` distinct values **6**, and
   `rows with BOTH dates: 416948, inverted: 5338, pct: 1.2803%`. **All exact.**
2. **Design test 3's fixture claims.** `CA 1164 / CO 209 / sum 1373`; names spanning more than one state **84**;
   and CA+CO really is the top pair — `CA CO 5, IN OH 3, IL TX 3, AL CO 2`. `MILLER'S MERRY MANOR` is 12 CCNs,
   all `IN`.
3. **Every spot figure §3.1 / §3.4 / §2.4 print.** `#745057` is the Texas veterans home; `#155049` is the
   **first of the twelve in `instance_id` order**, which is what `cap=3541` names. K8's collision reproduces
   exactly — both `ref_key`s are `cms:entity:facility#015009#2024-03-11`, `IDENTICAL: True`.
4. **M9's CMS half, exactly.** `headers caught: 1 ['Provider Name']`, `not caught: 22`, **false positives 0 of
   14,498**.
5. **M9's UC3 half and Q90's arithmetic.** `16,005` distinct no-house-number values carrying `861,798` rows
   today (round 1's 16,001 / 861,161 plus one day of 311 growth); `Q90: distinct (Survey Date, Correction
   Date) pairs: 47,318` — the "absurd" workaround is exactly 47,318 pairs.
6. **ING5's whole-table figures on `uvpi-gqnh`**, re-fetched: 683,788 / 408,701 / 59.70% / 132. Only the
   *conversion* to an ambiguous rate is wrong (D8).
7. **The three R58 page states over the live 9.7M-row partition, and design test 2's amended resolver.**
   `unknowable complete=False scanned=2000` **from a real resolver**, with `MUTATED (Rule U last) -> ambiguous`.
   **`I-1`'s fix is real and no confident answer could be got through it.**
8. **The R78 seam itself, from a fifth direction.** No outcome *requires* an instance store;
   `resolve_instance` returns `InstanceResolution | Refusal` and `HostTable` genuinely has no writer as
   shipped. **What broke is not the seam but the row's ability to DETECT its violation** — D4.
9. **The three-valued `Condition`, Kleene composition, and the `is_null` / `eq` split.** Every deletion goes
   red, including `matches` added to `VALUE_OPS`, both warnings deleted, and `CandidateRef` given an id.
10. **ING10 / M5 reproduces verbatim:** `Condition(op='gte', attribute='Correction Date', value='Survey Date')`
    is accepted and returns `[False, False, False]` for inverted and valid rows alike.
11. **§2.1's timing range, falsified a second time and in the other direction.** Today's unmodified design
    test 2 printed `one 50000-row page took 12.45s` — **above** the printed ceiling of 8.4 s, on the same day
    lens 1 measured 0.65 s **below** the printed floor. Not a new finding (A8 has it); recorded because two
    independent falsifications in opposite directions inside one day is the argument for A8's disposition.

**The ten mutations that went RED, so round 3 does not re-run them:** `discriminators` non-empty (§8);
`CandidateRef` given an id (4-9 / `C20-69`); `no_tenancy_predicate` (7-4 / `C20-62`); `consumers_unregistered`
(7-1 / `C20-59`); `matches` added (6-13 / `C20-54`); `scanned` counting pages (§8); `known` counting the set
rather than the page (§2.2); truncated ⇒ `next_after=None` (2-4 / `C20-07`); `<n>` as the true multiplicity
(4-12); the adapter scoring (2-6 / `C20-09` / `C0-04`).

---

### 6.9 Round 2, totalled — **19 BLOCKING, 18 MAJOR, 10 MINOR across four lenses. The findings did NOT shrink.**

| lens | verdict | BLOCKING | MAJOR | MINOR | ids |
|---|---|---|---|---|---|
| 1 — the **fix auditor**, pointed at `07af54f`..`39d3718` | **NOT YET** | 5 | 7 | 4 | A1–A16 |
| 2 — the **beacon integrator** | **NOT YET** | 5 | 4 | 4 | B1–B5, M1–M4, b-m1–b-m4 |
| 3 — the **kill row** | **NOT YET** | 4 | 3 | 1 | Z1–Z8 |
| 4 — the **public data** | **NOT YET** | 5 | 4 | 1 | D1–D9, d-m1 |
| **round 2** | **NOT YET** | **19** | **18** | **10** | **47 findings** |

**Round 1 was 11 BLOCKING / 20 MAJOR / 6 MINOR = 37. Round 2 is 47, and BLOCKING nearly doubled (11 → 19).**
Four lenses, four verdicts of NOT YET, and no lens returned nothing. **This is row 6c's shape at a spec row**
— *what changed each round was where the reviewers were pointed*, and the honest reading is stated here
before the fixes so it cannot be tidied afterwards.

#### 6.9a The four things round 2 says about the row

**1. The register's prediction held, and it is now the sharpest statistic this row has.** The fix-auditor lens
was pointed at exactly two commits and returned **five BLOCKING inside them**. Add lens 3's four and lens 4's
findings against round-1-minted rules and the count is **seven failures of standing rule (d), every one inside
the fixes of the round that invoked standing rule (d) as its own lesson**:

| # | rule | minted at | the caller it also binds, unnamed by the commit | found by |
|---|---|---|---|---|
| 1 | the reserved-value accounting, §9 | F8's warnings fix | §9 itself — two minted values reserved nowhere | A3 |
| 2 | the `31 of 100` number | §5.1 and §13 | §12, the third occurrence | A6 |
| 3 | rule 2-14 / `flat_form_ok` | primitive 23 | the **shipped** `flat_form_problem` it cites | A10 |
| 4 | rule 4-10 | the label that prompted it | `(namespace, kind, type_name)` — rule 4-11 one line below has it | B1 |
| 5 | rules 4-10 / 4-11 | the word *label* | `norm`, the gate's own identity function | B3 / Z2 / D1 |
| 6 | rule 3-14 | the identity **read** | the propose door and the host **write** | Z1 |
| 7 | rule 4-7 | `unknowable` | `not_an_instance`, the other outcome that must mint nothing | Z6 |

**A round's fixes are written by the person who has just read the findings, and that is exactly when the
enumeration feels finished.**

**2. Round 2 converged, and the convergence is the label.** Three lenses reached one defect from three
directions — lens 2 from a capture writing one name two ways (**B3**), lens 3 from the CMS file's 71
normalised keys carrying more than one raw spelling (**Z2**), lens 4 from `erm2-nwe9`'s 82.2% address-sharing
and a batch in which **46.5% of rows are never resolved at all** (**D1**). Two more reached
`discriminators` independently (**M1**, **D9**). Round 1's convergence was K1/P1 on a truncated scan; round
2's is this: **rules 4-10 and 4-11 assume *same label ⇒ same thing*, and every fixture this row cites says
otherwise.**

**3. The row's probes are still the weakest artefact it ships, and now the measurement is exact.**
**[Observed]** ten of twenty mutations leave all 87 checks green (**D4**), including `C20-01` and `C20-04` —
*this project mints no instance identifiers* and *a write primitive for instances is a conformance failure*,
**the two rules the R78 seam rests on**. The seam holds: five lenses have failed to force an instance row into
the registry, and `HostTable` genuinely has no writer. **What does not exist is the check that it holds.**
The countable-absence count over the *amended* kit is **nine** (§6.7d), three of them a previous trip's count
shape, and §4's entire contract is posed by **one** of the five design tests — with one label, one type and
one namespace.

**4. Four numbers the document prints are wrong, and three of them are numbers the document argues from.**
`Seventy-six` planned ids over **74** (A3); `18 of 100` where the spec elsewhere says 31 (A6); *seven* real
CMS pairs where the worker independently re-derived **31** in `[0.97, 0.98)` and **31 more** in
`[0.98, 0.99)` (D5); and `ambiguity_margin=0.02` where every probe declares **0.03**, which dissolves the
arithmetic the K2 argument is built on (d-m1). **The rules those arguments produced are right; the arithmetic
under them is not.**

#### 6.9b The instance-surface family — **SEVEN cells over NINE constructions, countersigned**

**[Observed]**, standing rule (a): `git diff --name-only a1b0364^..HEAD -- ontoloche/` returns nothing and
`resolve_instance` occurs zero times in `ontoloche/` — **re-verified by the supervisor this cycle**. Every
construction is against the **specification** and the **throwaway kit**, at a surface with no shipped door.
[**R83**](../decisions/2026-09-04-7a-supervisor-ruling-R83.md) minted the series,
[**R84**](../decisions/2026-09-04-7a-supervisor-ruling-R84.md) countersigned `I-2`,
[**R85**](../decisions/2026-09-04-7a-supervisor-ruling-R85.md) countersigned `I-3`…`I-6` and named the table,
and [**R86**](../decisions/2026-09-04-7a-supervisor-ruling-R86.md) settled the numbering this section routed.
**The kill-row trip count is FOURTEEN across all nine constructions and this row has incremented it nowhere.
`stop` is not put by any of them.**

**R86's first ruling is the one that matters most: a record is a CELL, not a construction.** The four
constructions R85 did not number do **not** become `I-7`…`I-10`. Numbering each construction separately is
precisely the error the fourteenth countersignature diagnosed — trips 8, 12, 13 and 14 were counted as four
separate things for three build rows before anyone saw they were four quadrants of one table, and that
mis-seeing is what cost the programme three rounds. **Having just named the table, this register does not go
back to counting doors.**

**The seven cells.** One question asked at seven doors: *which host rows answer to this identity, did the
resolution see all of them, and by whose rules was the answer judged?*

| the decision is wrong because the set was… | cell | the door | first seen |
|---|---|---|---|
| **truncated** — the scan stopped and said so, and the match path ignored the `why` | **`I-1`** | `resolve_instance`'s match path | round 1, K1 / P1 |
| **mis-walked** — the chain was followed one hop and reported `complete=True` | **`I-2`** | rule 3-14, the identity read | round 2, A1 |
| **mis-written** — the read is bound by the chain and the write door is not | **`I-3`** | §4.2 / §4.3, the host write | round 2, Z1 |
| **mis-keyed** — the act scopes on the raw label, the gate decides on `norm` | **`I-4`** | rules 4-10 / 4-11 | round 2, B3 / Z2 / D1 |
| **mis-timed** — the guard's window closes when the proposal drains, before the write lands | **`I-5`** | rule 4-11's `unreviewed=True` | round 2, Z4 |
| **mis-counted** — a page's own ids are not required to be distinct, so two rows collapse to one | **`I-6`** | §2 / §3.2's set test | round 2, Z7 |
| **mis-governed** — **the set is right and the facts that govern the decision belong to another entry** | **`I-7`** | §5's policy and §6.3's predicate, across a closure hop | round 2, D3 |

**Three constructions fall INSIDE existing cells, and R86 adopted this row's own mapping for all three** —
which is itself a result: the table was already wide enough to hold them.

| construction | the cell it is a construction of |
|---|---|
| **B1** — rule 4-10 has no type scope, so a `task` reuses a `project`'s `CandidateRef` | **`I-4`**, on the *type* half of the key rather than the label half |
| **B2** — rule 4-11 asks a door with no `label` filter that returns the oldest 100 | **`I-5`** and **`I-1`** at once — an identity read that reads one page and decides |
| **B5** — rule 4-10's memory is written only on the `proposed` branch | **`I-3`** |

#### 6.9b-i `I-7`, and this row's mapping of it was WRONG

**This section previously assigned D3 to `I-2`, *"mis-walked at the governed-fact half"*. R86 rejected that
and the rejection is correct** — verified against D3's own construction rather than argued: **the chain walk
succeeds and the extent is right.** Nothing about *which rows are in the set* goes wrong. What changes is
**which rules the set is judged by** — the successor's `MatchPolicy` and `Condition` swapped in under a caller
who named the predecessor. That is a different axis, and it produces a failure the other six cannot:

- **[Observed]** after one `retire(successor='ltc_facility')` over design test 3's CA+CO fixture, a
  California caller sees `CO rows visible to this CALIFORNIA caller: 1` where the control saw **`0`** —
  **R59's own stated reversal condition, reached by retiring a type rather than by omitting a keyword.**
- **[Observed]** **73 of 1,373** real CMS labels resolve differently for **one** caller.
- **§5.1's rule 5-6 is defeated in its own terms** — *two entries may declare different policies; two
  **callers** may not* — because here **one caller gets both policies.**

**Aggravating, and verified by R86 rather than accepted: rule 5-7 (`C20-41`) had no carrier.** **[Observed]**
`InstanceResolution`'s printed shape contained **zero** occurrences of `policy`, and the shipped carrier
`Invocation.declared_policy` declares `approval_mode`, `min_auto_tier` and `reversibility` — **not** the three
match thresholds. *A rule about which policy governed an answer cannot be checked while the answer cannot say
which policy governed it.* §6.10 closes the resolution half (rule **5-11**, `governed_by`) and names the
ledger half as **amendment A5**, which `INGEST.md` cannot land alone.

#### 6.9b-ii Standing rule (e), in the AMENDED seven-cell form

R85 proposed rule (e) over six cells and worded it about the *set* alone. The seventh cell is outside that
wording, so **R86 amended the rule before it was ever recorded** rather than shipping it and patching it:

> **The extent an identity is decided over, AND the facts that govern the decision, are the same at every
> door that reads it, writes it, keys it, gates it or counts it — and a door that cannot prove BOTH answers
> `unknowable` rather than deciding.**

It is stated normatively at [`INGEST.md` §3.4](../specs/INGEST.md), with the seven-cell table beside it. **The
fourteenth countersignature's lesson is the argument for closing them together:** trips 8, 12, 13 and 14 were
four quadrants of one table closed one at a time over **three build rows**, because each round closed the
quadrant it found and stopped. **This row has the whole table in front of it, in one round, before any code
exists** — which is a stronger piece of evidence for running constraint 7's loop *before* a build row than
`I-1` was.

#### 6.9b-iii Standing rule (d) is now an obligation on the COMMIT, not on the author

R84 sharpened rule (d) to cross the document boundary. R85 observed that the clause does not explain round 2's
seven failures — **four of them (Z1, Z2, Z5, Z6) are doors inside the same document**, which the original
wording already covered. The honest reading is not that the rule needs a third clause: **it is that a rule
addressed to an author's diligence failed seven times in one round while being cited by name.** So:

> **Every commit that mints a numbered rule carries, in the run record, the enumeration of the doors that rule
> binds — named, not implied. A later round that finds an unenumerated door records it as a rule-(d) failure
> BY NUMBER, and the count is reported in the round's totals.**

**Round 2's count is seven** (§6.9a's table). It is reported because it was counted, and it was counted
because a lens went looking. **§6.10c is this row's own enumeration under the new obligation, and round 3's
fix-auditor lens is pointed at exactly that enumeration.**

#### 6.9c Round 2 is NOT clean, and round 3 is the cap

**Stop condition** (standing constraint 7): two consecutive clean rounds, or three rounds plus an honest
convergence note. Round 1 was NOT YET; round 2 is NOT YET. **Round 3 is the cap**, and it must be pointed as
the register requires:

1. **A fix-auditor lens first**, at round 2's fix diff — the same standing requirement that produced five
   BLOCKING this round, in a round where the fix set is **larger** than round 1's.
2. **Standing rule (d), enumerated rather than invoked.** Round 2 found seven failures of it. Round 3's
   auditor checks that **each round-2 fix names every other caller it binds, in the commit that mints it** —
   and this time the enumeration is written into the commit message rather than assumed.
3. **A mutation sweep is now a required deliverable of the fix, not of the review.** D4 ran twenty mutations
   and ten survived. Round 2's fixes must ship checks that go red for `C20-01`, `C20-04`, `C20-05`, `C20-18`,
   `C20-25`, `C20-58`, rule 2-12 and rule 2-5, and the fix commit must state the survivor count it measured.

**The honest thing to say before the fixes, so it cannot be tidied afterwards:** the findings did not shrink
from round 1 to round 2, and the row should not expect round 3 to be clean either. What round 3 is for is to
say **where** the remaining defects live, not to reach zero.

---

## 6.10 Round 2's fix set — **ONE change over the table, per R85 and R86**

**This section is the enumeration standing rule (d) now obliges, and it is written here rather than only in
the commit message so a later round can check it by number.**

### 6.10a What was NOT done, and why it matters

The state line at the end of round 2 said *"land Z1 first — it is the fix to make first."* **That was right
about Z1 being load-bearing and wrong about the shape**, and [R85](../decisions/2026-09-04-7a-supervisor-ruling-R85.md)
is explicit about the cost of the other reading: trips 8, 12, 13 and 14 were **four quadrants of one table,
closed one at a time over three build rows**, because each round closed the quadrant it found and stopped.
This row has the whole table in front of it in one round, before any code exists, so the fix is one change
over the table with **standing rule (e)** stated normatively — [`INGEST.md` §3.4](../specs/INGEST.md).

### 6.10b The change, row by row

| row | record | what landed | rules |
|---|---|---|---|
| **truncated** | `I-1` | unchanged — round 1's fix holds and three lenses failed to get a confident answer through it | 3-5, 3-6 |
| **mis-walked** | `I-2` | §3.4a: the successor **closure** — visited set, hop cap, cycle, and an early stop that is `complete=False` **with a `why`**. A dangling successor **never** falls back to the predecessor's entry (R84's rider, the eighth trip's shape). Written from `_identity_closure`, cited as the normative reference | **3-14** amended, **3-15**, **3-16**, **3-17** new |
| **mis-governed** | **`I-7`** | §5.3 / §6.3a / §7.1a: **a successor does NOT inherit its predecessor's `MatchPolicy` or predicate.** A closure hop into an entry declaring either differently answers `unknowable` naming the changed fact. **The decision is the row's and is recorded rather than assumed** — §7.2 makes the successor's entry *someone else's to register*, so inheritance would let a third party's declaration silently govern a caller's answer. Raised as **Q91** with (a) as the default in force, because it changes what the registry declines to serve | **3-18**, **5-10**, **6-18**, **7-5** new |
| **mis-governed**, the carrier | `I-7` | **rule 5-7 had no carrier at either end** (R86, verified). `InstanceResolution.governed_by` names the `(namespace, type_name)` whose entry judged the answer; the **ledger** half cannot be closed here and is named as **amendment A5** | **5-11** new |
| **mis-written** | `I-3` | §3.4a.4: **the identity's extent is the WHOLE closure, not its endpoint.** A row written under a since-retired name is still this identity's row until the host migrates it; an endpoint-only read is a *smaller set than the extent*. The host writes under the **effective** type | **3-19** new, **4-3** amended |
| **mis-keyed** | `I-4` | §4.3: the act's key is `(namespace, kind, the closure of type_name, the label under §3's own normaliser)` — **computed by the same function the gate uses**, because two implementations of one identity question is exactly what `I-4` is | **4-10** amended |
| **mis-keyed**, type half | B1 | the same key change carries the type, so a second type answering to one label is proposed rather than handed the first's `CandidateRef` | **4-10** |
| **mis-timed** | `I-5` | §4.3: the guard asks who holds a proposal **whose row has not been written**, not who holds an *unreviewed* one | **4-11** amended |
| **mis-timed**, rider | B5 | the per-act memory is written on **every** branch answering with a `CandidateRef`, the pending branch included | **4-13** new |
| **mis-counted** | `I-6` | §3.4b: a page's `instance_id`s are **distinct-or-`unknowable`** | **2-16** new |
| — | Z6 | rule 4-7 fences **`not_an_instance`** as well as `unknowable` — the classifier *succeeding* is not a licence to propose | **4-7** amended |

**And the artefact change that makes it one rule rather than one sentence:** the ingest **act and ledger moved
into [`ingest_probe_kit.py`](../tools/ingest_probe_kit.py)**, joining the resolver. Round 2 found three doors
of one question answered three ways because the act was a *second implementation* — which is precisely the
lesson round 1 learned about the resolver and did not carry to the act beside it. `type_closure()` and
`act_key()` are now single functions that the read, the write, the key and the guard all call. **That closes
§6.7d's countable absence #1** (*§4's entire contract posed by one of the five design tests*) as a side effect
of the design rather than as a separate fix.

### 6.10c Standing rule (d)'s enumeration — **the doors each new rule binds, named**

R85: *every commit that mints a numbered rule carries the enumeration of the doors that rule binds — named,
not implied.* For the seven rules minted here:

| rule | the doors it binds |
|---|---|
| **5-10** (`C20-82`) | `resolve_instance`'s policy read; §5's gate; `type_closure`'s hop; §7.2's registering host; **Q91**, which routes the decision to the founder |
| **5-11** (`C20-85`) | `InstanceResolution` (the printed shape and the kit's); §5's rule 5-7; §4.4's amendment **A5**, which is the same fact at the ledger |
| **6-18** (`C20-83`) | `evaluate`; the entry's predicate; `type_closure`'s hop; §6.3's registry-side evaluation; R59's tenancy reversal condition |
| **7-5** (`C20-84`) | the host that declares a `successor`; §7.2's vocabulary registration; rules 3-18 / 5-10 / 6-18, which are what happens when the obligation is unmet |
| **2-16** (`C20-75`) | `resolve_instance`'s read; §3.2's set test; §4.3's `<n>` count; the two host adapters (`HostTable`, `SocrataServiceRequests`) as the producers of a page |
| **3-15** (`C20-76`) | `type_closure`; `resolve_instance`; `act_key`; rule 4-11's ledger question — **and the shipped `_identity_closure`, which already implements it** |
| **3-16** (`C20-77`) | the same four, plus `registry.py`'s `_IDENTITY_CHAIN_CAP` as the shipped precedent |
| **3-17** (`C20-78`) | the same four; `INTERFACE.md` §5.9, which does not forbid constructing a cycle |
| **3-18** (`C20-79`) | `resolve_instance`; §5's `MatchPolicy` door; §6.3's predicate door; §7.2, which makes the successor's entry someone else's to register |
| **3-19** (`C20-80`) | `resolve_instance`'s read; §4.2's host write; rule 4-11's ledger question; `act_key`; the `<n>` count |
| **4-13** (`C20-81`) | `IngestAct.land`'s pending branch and its minting branch; rule 4-10's memory; rule 4-11's guard |

**Amended rules and the doors the amendment reaches:** 5-7 (`InstanceResolution.governed_by`, the ledger's `declared_policy`, amendment A5); 3-14 (`type_closure`, `resolve_instance`, `act_key`,
`_identity_closure`, `neighbors`/R38); 4-3 (the host write, the ledger row, rule 4-11's key); 4-7
(`IngestAct.land`'s `unknowable` **and** `not_an_instance` branches); 4-10 (`act_key`, the per-act memory,
rule 4-11's question, §3's normaliser); 4-11 (`Ledger.open_proposals`, `host_writes_for`'s `minted_ref`, and
**the shipped `Registry.invocations`, which cannot answer it** — finding B2, now §4.4's fourth amendment).

### 6.10d The accounting, and it is checked rather than asserted

**[Observed] 2026-09-04**, over [`INGEST.md`](../specs/INGEST.md):

```
grep -o "C20-[0-9]*" | sort -u | wc -l   ->  85
rule rows  (^| n-n |)                    ->  85
min 01   max 85   gaps: none
```

**74 → 85 rules and ids** — 81 for the six extent cells, and four more (`5-10`, `5-11`, `6-18`, `7-5`) for
`I-7` once R86 ruled it a seventh cell rather than a half of `I-2`. §9's sentence now says *eighty-one* and says how the number is derived, because
round 2's A3 was that it said *seventy-six* over 74 — in the section whose only job is to enumerate. The
reserved-value table regains its **ordinals** and gains the **two values round 1's own fix minted and reserved
nowhere** (`consumers_unregistered`, `no_tenancy_predicate`), with **[Observed]** `len(types.WARNING_VALUES)`
= 37 printed beside them so the count is reconcilable with the tuple that holds it — which is the whole of
R11's mechanism and the thing A3 found deleted.

### 6.10e The mutation sweep — **every cell goes RED, and the harness had to be fixed first**

R85 and R86: *turn each of the mutations red, and say so with the numbers.* **[Observed] 2026-09-04**, each
fix removed one at a time from a **copy** of the kit under a scratch directory with `PYTHONPATH` pointed at
the repo, then all five design tests re-run. **Baseline 36 + 13 + 17 + 11 + 27 = 104 checks.**

```
  [RED] I-1 truncated    (rule U before the branches)
        seam 34/36 · paging 12/13 · gate 10/11 · act 22/27
  [RED] I-2 mis-walked   (the chain, not one hop)
        seam 35/36 · paging 12/13 · gate 10/11 · act 21/27
  [RED] I-2 rider        (a dangling successor keeps the predecessor's entry)
        seam 35/36 · paging 12/13 · gate 10/11 · act 22/27
  [RED] I-3 mis-written  (the extent is the whole closure)
        seam 35/36 · paging 12/13 · gate 10/11 · act 22/27
  [RED] I-4 mis-keyed    (the act's key is the gate's key)
        act 26/27
  [RED] I-5 mis-timed    (unwritten, not unreviewed)
        act 26/27
  [RED] I-6 mis-counted  (a page's ids are distinct)
        seam 35/36 · paging 12/13 · gate 10/11 · act 22/27
  [RED] I-7 mis-governed (the successor's facts are not the caller's)
        seam 35/36 · paging 12/13 · gate 10/11 · act 22/27
  [RED] Z6 not_an_instance mints nothing
        act 26/27
```

**Nine of nine red.** Round 2's own D4 found **ten of twenty** mutations leaving all 87 green, including
`C20-01` and `C20-04`; every fix this round lands with a check that goes red without it, which is the standard
D4 said the row was not meeting.

#### 6.10e-i The harness was wrong first, and that is the part worth recording

**The first sweep reported `I-2` as SURVIVING — all 104 green — and it was the harness lying, not the fix.**
The sweep disabled a fix by flipping the kit's `_mutate` **default**, and the design tests pass `_mutate=`
**explicitly** on their fixed arm, so the default never reached the code under test. The corrected harness
forces the mutation **in source**, and `I-1` immediately went red in **four** probes where the first harness
had shown three.

**This is `M1`'s shape and `A9`'s, in the row's own tooling, one round after the row recorded both** — *a
check that is green for a reason other than the one it claims*. It is recorded here rather than quietly fixed
because the register's own count is that this shape recurs, and because a mutation harness that cannot fail is
the exact object §8.1 exists to be honest about. **A harness is an artefact and is subject to the same rule as
the probes it runs**: round 3's fix-auditor lens should point at it as well as at the diff.

**One consequence for the record.** §6.5c item 1 and §6.8c item 7 both state that `I-1`'s fix is real and
mutation-proved. **That claim stands and is now better evidenced** — under the corrected harness the same
mutation reddens four probes rather than three. No finding in §6.5–§6.8 is withdrawn by the harness defect;
what changes is that the *sweep's* numbers, and only those, were re-derived after it was fixed.

---

### 6.11 Round 3's predictions — **PRE-REGISTERED, written before any lens returned**

**This section is committed before round 3's four lenses report**, so the predictions are checkable in
`git log` rather than asserted afterwards — the discipline §0 used for design test 1, applied to the loop
itself. Round 3 is the **cap**: it closes with an honest convergence note whatever it finds.

**Four lenses dispatched at `83f6a75`:** the **fix auditor** (pointed at the fix diff, at §6.10c's rule-(d)
enumeration, **and at the mutation harness itself**), the **kill row**, the **public data**, the **beacon
integrator**.

| # | prediction | why | how it will be judged |
|---|---|---|---|
| **P1** | **Round 3 will NOT be clean.** At least one BLOCKING. | Six rows of this register have run this loop and **not one closed clean**; rounds 1 and 2 here went 11 → 19 BLOCKING. A round that came back clean immediately after a fix set this large would be evidence about the lenses, not about the row. | any lens returning NOT YET |
| **P2** | **The fix auditor will find the most, and its findings will be inside `83f6a75`.** | The register's own count: 3e 4-of-10, row #4 round 3 2-of-4, 4d round 2 five inside round 1's fixes, 6b round 2 the tenth trip inside the ninth's fix, and **round 2 here five BLOCKING inside round 1's two commits**. | which lens has the highest BLOCKING count, and whether its findings cite the fix diff |
| **P3** | **Rule 3-19 — the extent spanning the whole closure — is where the new defect lives.** | It is the newest rule, the only one that made a set **bigger**, and its cost is recorded as **ING11 and explicitly unmeasured**. Every previous round found the defect in the rule minted last. | a finding against 3-19, ING11, or the read's cost/multiplicity |
| **P4** | **Standing rule (d) will fail again, and the enumeration at §6.10c will be incomplete.** | It failed **seven** times in round 2 while being cited by name, which is why R85 moved it onto the commit. §6.10c is the first enumeration written under the new obligation and it was written by the same person who wrote the rules. | any door named by a lens that §6.10c does not list |
| **P5** | **The harness audit will find something, and it will be a check that is green for a reason other than the one it claims.** | That is M1's shape, A9's shape, and §6.10e-i's shape — **three times in two rounds**, the last one in the row's own tooling. | a finding against `_mutate`, `enforce`/`ACT_RULES`, or a paired check |
| **P6** | **No lens will force an instance row into the registry.** R78 holds. | Five lenses have tried from five directions and failed; the seam's two-primitive count survived every construction. **[Assumed]** the sixth and seventh fail too. | any finding that an outcome requires an instance store |
| **P7** | **The findings will NOT shrink to zero, and the row will be closed on the cap rather than because it converged.** | Rounds 1 and 2 grew, 37 → 47. Row 6c's three rounds went 13, 12, 12 and it was **stopped rather than finished**. | §6.13's convergence note, written against the totals |

**What would falsify the row's own reading rather than confirm it.** If round 3 comes back **clean across all
four lenses**, that is not a victory to be claimed — it is evidence that round 3's lenses were pointed where
round 2's fixes already looked, and the convergence note must say so. **[Inferred]** from row #4's round 3,
where the findings halved and the round after still found a kill-row route: *a shrinking count is the weakest
signal this register has.*

---

### 6.12 Round 3, lens 1 to return — **the beacon integrator. NOT YET: 4 BLOCKING, 5 MAJOR, 1 MINOR.**

*(Written to disk before any fix. Four lenses were dispatched together; sections are numbered in return order.)*

**The verdict in one sentence:** *the capture path no longer stops at the second reference — it stops at the
key round 2 minted to FIX the second reference, and §4.3's own prose still specifies the defect the rule table
says was closed.*

**[Observed]** baseline reproduced first: 36 + 13 + 17 + 11 + 27 = **104**. The worktree was untouched
(`git status --porcelain` empty) and every construction lives in the lens's own scratch directory.

**Prediction P1 is confirmed and P4 with it** (§6.11, committed at `4f3b2eb` before any lens reported):
round 3 is **not** clean, and standing rule (d) failed again inside the enumeration written under its own new
obligation.

#### 6.12a `I-4` again, in BOTH directions — the mis-keyed cell's own fix is what defeats it

**Rule 4-10's central claim is *"the key the gate decides on, computed by the same function"*. It is FALSE.**
The gate's identity relation is `similar(norm(a), norm(b)) >= match_at`; the act's key is **exact equality of
`norm`**. Round 2's fix took the gate's **pre-processor**, not the gate.

```
SPLIT   'Meridian Migration' / 'Meridian Migraton'   (an ordinary typo in a meeting note)
  the GATE : similar=0.9714 >= match_at 0.97 -> True
  rule 4-10's KEY identical: False
  counterfactual: resolve_instance('Meridian Migraton') over a store holding row 1
                  -> existing  ref=beacon:entity:project#HOST-1  confidence=0.9714
  ONE act, every act rule ON:
     land -> proposed ; land -> proposed ; invocations: 2 warnings=[(), ()]
     host writes: [#HOST-1, #HOST-2]
     the NEXT resolution -> ambiguous known=2 confidence=1.0 complete=True

MERGE   norm('東京 Project') == norm('大阪 Project') == 'project'
        norm('Müller') == norm('Møller') == 'm ller'
        norm('Проект Alpha') == norm('Договор Alpha') == 'alpha'
  ONE act: land('東京 Project') -> proposed ; land('大阪 Project') -> reused
     invocations recorded: 1   the OSAKA row is named by CandidateRef(label='東京 Project')
  the resolver ALONE: resolve_instance('大阪 Project') over a store holding only Tokyo
     -> existing  ref=…#p-tokyo  confidence=1.0  complete=True  scanned=1
```

**And §3 defines no normaliser at all.** **[Observed]** `grep -i 'normalis\|normaliz'` over §3 returns
**nothing**; the three hits in the file are rule 4-10, **ING3** and **Q86** — and ING3 calls the only
implementation *"`identity_key`'s ASCII-only collapse re-implemented"* and dismisses it as **"a probe defect
and not a spec defect"**. **Round 2's fix promoted that probe defect into a normative rule.**

**This is the kill-row family in both directions**, with every rule of §3, §4 and §5 firing correctly: two
host rows answering to one identity (split), and one identity answering for two things (merge). Constructed
against the **specification** and the **kit**, so on R83's reading they are proposed as constructions **inside
`I-4`** — the mis-keyed cell whose fix they defeat. **The trip count is FOURTEEN and is not incremented.**
Classification is the supervisor's.

#### 6.12b Every finding, with its disposition

| # | severity | finding | disposition |
|---|---|---|---|
| **B1** | **BLOCKING** | **Rule 4-10 keys on `norm` equality; the gate decides on `similar(...) >= match_at` — §6.12a.** Split and merge both constructed; §3 defines no normaliser | **ACCEPTED.** Rule 4-10 must key on whatever §3 calls *the same thing* — **the relation, not the pre-processor** — or §3 must define a normaliser and the document must price what it does to prose. **ING3's *"a probe defect, not a spec defect"* is no longer true** and is corrected: rule 4-10 cites the function normatively |
| **B2** | **BLOCKING** | **§4.3's two numbered rules are the PRE-FIX text**, in the section titled *"One ingest ACT, and the two rules that make it one"*. **[Observed]**, re-verified by the worker at `INGEST.md:597-605`: *"Within one act, a **label** is resolved once. The first **proposal** for a label mints a `CandidateRef`…"* (no type scope = B1's round-2 defect, no normaliser = `I-4`, *"the first proposal"* = B5's defect) and *"…the loop queries `invocations(unreviewed=True)` for an **undrained** proposal…"* (= `I-5` verbatim). **These are the kit's own two mutation switches**, both of which turn design test 5 red. §13's route row is likewise unamended | **ACCEPTED, and it is the one to fix first.** The rule table and the section those rules live in say **different things about the same key** — which is §3.4's own recorded meta-shape (*"the prose, §13's route table and this row's own probe all implemented the narrow one"*) **recurring inside the commit that fixed it.** An implementer reads §4.3, not the id table |
| **B3** | **BLOCKING** | **Nine of round 2's fourteen beacon findings were dispositioned ACCEPTED and landed in nothing — B4, the relationship half, for the SECOND ROUND RUNNING.** **[Observed]**, re-verified: `'relationship'` = **2** (the same two round 2 counted), `'add_edge'` = **0**, §0.1 relationship non-goals = **0**, §10 = 11 contortions none about relationships, §11 = 7 questions none about relationships, §12's row byte-identical. Same for **M1** (`discriminators` comment unchanged at `:978`), **M2**, **M3**, **b-m1**, **b-m4**. §6.10b's fix table has rows for B1 and B5 only, and §6.10a names none of the nine | **ACCEPTED, and it is the round's most damning finding about this row's own record.** B4's own disposition read *"it is A2's shape … a disposition kept in the run record and landed in none of §0.1, §10 or §11."* **Round 2's fix set did exactly that to B4 itself** — third occurrence of one shape. Either the nine land, or §6.10a names them as deferred with a reason; **a run record whose ACCEPTED dispositions do not bind the commit is not a record** |
| **B4** | **BLOCKING** | **Amendment A4 is factually WRONG about the shipped shape, and its own stated consequence closes the capture path.** A4 says `invocations` has *"no completeness answer"*. **[Observed]**, re-verified by the worker against the shipped code: [`actions.py:792`](../../ontoloche/actions.py) `InvocationReport` carries `known` / `complete` / `why_incomplete`, and its own docstring says *"`complete` is `False` whenever a filter suppressed rows or `limit` truncated the answer — so EVERY filtered answer … is a floor rather than a total"*; [`registry.py:9590`](../../ontoloche/registry.py) is `elif filtered: why = "a filter suppressed rows; this is a floor, not a total"`. **Rule 4-11's read is filtered by construction**, so it is *always* `complete=False` — and A4's own sentence (*standing rule (e) makes an unprovable extent `unknowable` at this door as at every other*) therefore makes **every** propose-at-ingest `unknowable`, which rule 4-7 turns into **nothing recorded, ever** | **ACCEPTED, and this is the worker's error, not a lens's over-reading.** A4 must ask for a **completable** read — a scoped exhaustive one, or a `complete=True` on a filter the store can push down — not for filters plus a completeness answer it already has. **M2's shape one amendment along, in the section whose only job is to enumerate what must land.** And a `label` filter cannot express rule 4-11's key anyway: **[Observed]** the key runs through `norm` **and the closure**, and a filter over the raw stored columns sees neither — `label` filter finds 0, `type_name` filter finds 0, `act_key` finds 1 |
| **B5** | MAJOR | **Rule 3-18's `unknowable` is a SILENT DROP at the capture path, and §11 calls it *"loud"*.** One `retire(successor=)` where the successor declares a different `MatchPolicy`; a 5-row capture batch: `'unknowable'` ×5, **`invocations recorded: 0`**, `unreviewed(): 0`, `open_proposals: 0`, per-act memory `{}`, `host writes: []`. The **resolution** carries a `why`; `land` throws it away. **[Observed]** `unknowable` inside §4 appears only in rule 4-7, in A4 and in a K9 aside — **no rule says what the loop does with one** | **ACCEPTED.** §11's Q91 prices default (a) as *"safe and **loud**"*; at the act it is **silent**, which is UC1's own **mechanism C** — a consumer silently dropping what it does not know — in the highest-volume path in the system. **Q91's cost table is corrected**, and §4 gains a rule making an `unknowable` **enumerable** as rule 4-5 does for `ambiguous` |
| **B6** | MAJOR | **B5's write door is still unbound and §10 records nothing about it.** Three acts, one label, every rule on → `ledger` holds the two `instance_proposal_pending` warnings → drained the ordinary way → `host writes: [#HOST-1, #HOST-2, #HOST-3]` → `ambiguous known=3 confidence=1.0`. **[Observed]** zero §10 rows mention rule 4-11 | **ACCEPTED.** Round 2's B5 disposition was *"**either** rule 4-11's warning binds the approval door, **or** §10 records that it does not."* **Rule 4-13 was minted instead — which closes only the within-act half — and neither branch of the disposition was taken.** ING2's advisory-at-the-only-enforcing-door, at the rule minted to close K4 |
| **B7** | MAJOR | **Rule 4-13's missing branch is `existing`.** Rule 4-10 says *"within one act an **IDENTITY** is resolved once"*; rule 4-13 binds *"every branch that answers with a `CandidateRef`"* — and `existing` answers with an `InstanceRef`. **[Observed]**, re-verified by the worker at [`ingest_probe_kit.py`](../tools/ingest_probe_kit.py) line 939, the `existing` branch returns without writing `self._minted[key]`. One note naming one **held** person eight times: `['existing']×8`, **`host reads: 16`**, per-act memory `{}`. The same note where the person is not held: `['proposed','reused'×7]`, `host reads: 2` | **ACCEPTED.** *The branch that resolves an identity most cheaply-provably is the one branch rule 4-10's scope never reaches* — and on the partner's shape (a note naming one project or person repeatedly) that is the **common** case. Rule 4-13 is worded around the `CandidateRef`; rule 4-10 around the **identity**; the two do not meet |
| **B8** | MAJOR | **`InstanceContext` is still wholly inert — round 2's M4 was neither fixed nor recorded.** **[Observed]** the real 12-way tie with `row_attributes` **uniquely naming one of the twelve** answers `ambiguous known=12`, identical to the empty-context call; `resolve_instance` reads only `context.act_id`; no rule 1-1…7-5 names `InstanceContext` or any field; §8.1 gained no row for it | **ACCEPTED.** §8's justification for minting a **second** context object is unbacked by anything the document specifies. ING8 prices the **emptiness** of two fields for a prose source; **nothing prices the inertness of all five**, and F6's whole fix (typing `siblings`) is typed signal no door reads |
| **B9** | MAJOR | **§9's count is wrong by four, and the sentence asserting it was DERIVED is false — A3's exact defect, third occurrence, inside the commit that claims to have closed it.** **[Observed]**, re-verified by the worker: §9 line 1021 says *"**Eighty-one** rules, eighty-one planned ids, `C20-01` … `C20-81`"*, and `grep -o "C20-[0-9]*" \| sort -u \| wc -l` returns **85**; the run record's own §6.10d prints *"85 / 85 / min 01 max 85"* | **ACCEPTED, and it is the worker's error in the sharpest possible place.** The four `I-7` rules (5-10, 5-11, 6-18, 7-5) were added **after** §9's sentence was rewritten, and the sentence **claims the count was derived by grep** — so the row asserted a derivation it did not re-run. **The spec and its own run record disagree by four in the one section whose only job is to enumerate** |
| **b-m1** | MINOR | **A5 asks for a carrier without saying which fact it carries.** A5 cites the missing thresholds; rule 5-11's carrier records `(namespace, type_name)` — the **entry**, not the thresholds | **ACCEPTED.** The two halves of `I-7`'s carrier are specified as different shapes; one sentence in A5 naming rule 5-11's shape joins them |

#### 6.12c What the lens attacked and could NOT break

1. **`I-1`, `I-2` and its rider, `I-3`, `I-6`, `I-7` and Z6 are real and mutation-proved.** The fixed arm
   re-ran at 104/104, and `type_closure` was read line by line looking for a fourth termination case — cycle,
   cap, dangling and the honest early stop are all present with a `why`. **No walk could be made to decide
   over a chain it could not finish.**
2. **The successor closure is genuinely shared.** `resolve_instance`, `act_key` and `Ledger.open_proposals`
   all call the one `type_closure`; the read and the key could not be made to disagree about the **type** half.
   **Every divergence found was in the LABEL half — B1 — which is a different function.**
3. **Rules 3-13 and 3-6 at the act door.** No route from `unknowable` to a proposal exists; the defect is what
   happens **after** the refusal (B5), not the refusal.
4. **`C20-01` / R78, from a SIXTH direction.** No write this project must perform was found on the capture
   path; `CandidateRef` still has no `id` and cannot acquire one. **Six lenses have now failed to force an
   instance row into the registry.**
5. **Rules 3-3 / 3-4 / 5-8 at the act layer.** Every duplicate was produced *between* correct resolutions, and
   every post-hoc resolution reported `ambiguous` with `ref=None` and the right `known`. **The set test is not
   the weak point; the act's key is.**
6. **§4.2's provenance claim** holds for a fourth reading.

#### 6.12d What this lens says about the row

**Three of its four BLOCKING are the row's own recorded shapes recurring inside the fix that closed them.**
B2 is §3.4's prose-against-rule-table meta-shape; B3 is A2's *disposition kept in one artefact* — **applied to
the very finding that named A2's shape**; B9 is A3's counting defect, third occurrence, in a sentence that
asserts the count was derived. **That is not four independent defects. It is one: a fix round closes what it
was pointed at and does not re-read the neighbours.** The register has now written that sentence at every row
from 3e onward, and this row has written it three times in three rounds.

---

### 6.13 Round 3, lens 2 to return — **the kill row. NOT YET: 5 BLOCKING, 2 MAJOR, 2 MINOR, and it nominates an EIGHTH CELL.**

*(Written to disk before any fix.)* **[Observed]** baseline reproduced first: **104**, and every finding is
live over a green 104. No repo file was modified.

**Standing rule (a), provenance.** `grep -rc "resolve_instance" ontoloche/` → **0 files**; `HostTable` has no
writer. Every construction is against the specification and the kit — **with one exception: K8's misreading is
demonstrated in SHIPPED code.** The door that *mints* the bad string is spec+kit; the reader that *misreads*
it ships today.

#### 6.13a `I-8` nominated — **mis-directed: the closure is walked FORWARD ONLY, and the function this row cites as normative walks BOTH ways**

**This is R84's second clause failing in the very section written to satisfy it.** §3.4a declares itself
*"written from `registry.py`'s `_identity_closure` … a rule rather than a courtesy"* and implements that
function's **three termination rules** while implementing **one of its three relations.**

**[Observed]**, re-verified by the worker at [`registry.py`](../../ontoloche/registry.py) line 5380 — the
docstring of the function §3.4a cites:

> *The closure is walked in **both** directions and they are different questions: **forward** — `assignee` was
> retired with `owner` as its successor …; **backward** — a walk from `owner` must find the edges written
> against `assignee`, which is the direction `merge_types` actually produces and **the one a caller reaches
> after doing the right thing**. **Aliases are consulted too**, because `merge_types` writes both a successor
> and an alias for one absorption and a hand-written alias is one the successor scan would miss.*

**[Observed]** in `INGEST.md` the only `predecessor` hits are rule 3-15's **negative** use; `alias` and
`backward` are **zero** — and `alias` is **zero** in the kit.

**The construction, one partially-migrated store, one facility, two names of ONE identity:**

```
caller names the RETIRED name  -> existing  ref=cms:entity:facility#155049  conf=1.0 scanned=10   CORRECT
caller names the SURVIVOR      -> proposal  conf=0.4571 known=5 scanned=9
   closure('ltc_facility') -> effective='ltc_facility'  hops=()      <-- the extent is a SUBSET
ACT under the survivor: land(...) -> 'proposed', mode='auto'
   the host writes 'cms:entity:ltc_facility#L9'
   -> a SECOND row for cms:entity:facility#155049, in `auto` mode, with no human
```

**The survivor is the name every new caller uses after a retirement**, so this is the **ordinary**
post-retirement path, not an exotic one. Rule 3-19 widened the extent **along the axis that was already
covered** and left the axis the shipped code exists to cover.

**Why the lens calls it an eighth cell rather than a construction inside one, and the worker agrees.** All
seven existing cells describe doors **disagreeing** with one another, or a door **unable to prove**. Here the
read, the key and the write **all agree**, and they agree on a set that is a strict **subset** of the
identity — one implementation, consistent at every door, consistently deciding over the wrong set. It most
resembles `I-2` (mis-walked), but `I-2` is about **depth** (one hop, reported complete) and this is about
**direction**. **Nominated as `I-8` — mis-directed. The classification is the supervisor's, the trip count is
FOURTEEN and is not incremented.**

#### 6.13b Every finding, with its disposition

| # | severity | finding | disposition |
|---|---|---|---|
| **K4** | **BLOCKING** | **The closure is walked forward only — §6.13a.** | **ACCEPTED, and it is the fix to make first**, because its correct answer is already written down. `type_closure` walks **successors ∪ predecessors ∪ aliases**, both directions, as `_identity_closure` does; §3.4a and rule 3-19 say **identity closure** and cite the function's three **relations** by name, not only its three termination rules |
| **K1** | **BLOCKING** | **`I-7`'s guard compares only the two ENDPOINTS, so one extra `retire()` silences it.** **[Observed]** control at 1 hop → `unknowable` naming the changed predicate; **add one hop to an endpoint declaring exactly what the caller declared** → `existing conf=1.0 governed_by='cms:ltc_v2'`, `hops=('ltc_facility','ltc_v2')` — and the ref handed out lives under `ltc_facility`, whose **own** predicate says the caller may not see it. Same with a differing MatchPolicy mid-chain | **ACCEPTED.** The three rules minted in one change to close `I-7` **contradict each other**: 5-10 and 6-18 say *"a closure **hop** into an entry declaring a different one"* (per-hop, correct); **3-18 says *"the successor's entry"* (endpoint), and the kit implements 3-18.** Rule 3-19 admits the intermediate's rows into the extent, so **the entry whose rows are being judged is the one entry never consulted.** A governance act that ADDS a retirement must not turn `unknowable` into `existing`. A construction inside **`I-7`** |
| **K8** | **BLOCKING** | **The successor NAME reaches the flat form by the WRITE door, and rule 2-14 fences only the READ door.** **[Observed]** `retire(facility, successor='ltc#v2')` → no host *record* carries it, so rule 2-14's guard sees `[None, None, None, None]` → `effective_type` becomes `CandidateRef.type_name` → `Invocation.type_name` → `minted_ref='cms:entity:ltc#v2#155050'`. Then the **shipped** reader: `parse_ref(...)` → `InstanceRef(type=TypeRef(name='ltc'), id='v2#155050')`, and `ref_key` of *that* returns the identical string with `flat_form_problem` → `None`. The guard itself knows: `flat_form_problem(TypeRef(name='ltc#v2'))` names the defect exactly | **ACCEPTED. §13's route-table row 12 re-opened by this round's own §3.4a fix**, and it is round 1's K8 / `C19-82` at a door rule 2-14 does not fence — `effective_type` reaches the flat form **without ever being a record**. §7.2 makes the successor's entry a third party's to register and nothing constrains the successor **string**. Rule 7-5 gains the obligation, refused at declaration |
| **K2** | **BLOCKING** | **Rule 2-16's distinctness key omits the one dimension rule 3-19 added, and both landed in `83f6a75`.** The migration window rule 3-19's own justification names: **[Observed]** `MID-MIGRATION (3-19 on) -> ambiguous conf=1.0 known=2 complete=True` over `cms:entity:facility#155049` and `cms:entity:ltc_facility#155049` — **one facility**; the pre-3-19 endpoint-only read answered `existing known=1` and was **correct**. Rule 2-16 is blind: the two keys differ in `type_name`, so `duplicates found: []`. The act then proposes and the host writes a **third** row | **ACCEPTED.** `I-6`'s rule closes **under**-counting (two rows, one id) and leaves **over**-counting (one thing, two closure names) wide open. `known` counts host **rows**, not host **things**, and after 3-19 those differ. **This is ING11's cost, arriving as a defect rather than as the recorded contortion** — and ING11 said it was unmeasured. A construction inside **`I-6`** |
| **K7** | **BLOCKING** | **A11 was ACCEPTED in round 2 and NOT landed.** **[Observed]**, re-verified: §3.2 line 356 still reads *"stronger than any arithmetic between the two numbers and **needs no second constraint to hold**"*, while [`ingest_probe_kit.py`](../tools/ingest_probe_kit.py) line 762 carries `c.score >= policy.propose_below`. Two candidates at an **exact** tie below `propose_below` answer `proposal` where rules 3-3 / 5-8 as written say `ambiguous`. **New, by mutation:** removing the floor so the kit matches the rules **reddens a check on the real 14,627-row CMS file** | **ACCEPTED.** *A conformant implementer reading `INGEST.md` writes the other behaviour and fails the row's own design test.* **The floor is load-bearing on real data and exists nowhere in the document** — the kill row's own set test defeated by an undocumented constraint |
| **K6** | MAJOR | **Z5 was ACCEPTED in round 2 and NOT landed.** The band branch still caps `known` and `candidates` at 5 over a **finished** read, and the reviewer's `<n>` inherits it. **[Observed] by mutation:** removing the cap leaves **104/104 green** — the cap is untested in both directions | **ACCEPTED.** Rule 3-4 binds this branch (its outcome **is** `ambiguous`) and says *"every tied candidate is returned"*; §8 prints `known: int` with no cap |
| **K10** | MAJOR | **Rule 5-11, minted THIS round as `I-7`'s carrier, has ZERO checks — proved by two mutations.** **[Observed]**, re-verified by the worker: `governed_by` occurs **0** times across all five design tests. `governed_by = ""` → **104/104 green**; `governed_by` naming the **declared** entry rather than the one that judged → **104/104 green** | **ACCEPTED, and by the row's own standard — *"a check that cannot go red is a decoration"* — rule 5-11 is a decoration.** It was minted to make rule 5-7 **falsifiable** and is itself **unfalsifiable**. **A standing-rule-(d) failure inside §6.10c, the enumeration written to satisfy standing rule (d)** — §6.10c lists four doors 5-11 binds and not one asserts it |
| **K9** | MINOR | A namespace-shaped successor makes the ledger row unreadable: `minted_ref='cms:entity:nyc:facility#155051'` → `parse_ref` **RAISES**. Same door as K8, louder failure | **ACCEPTED**, closed by K8's fix |
| **K11** | MINOR | **The countable-absence count over the fix set is EIGHT** (eleven → nine → eight): zero `governed_by`; zero `alias`; zero `can_count` (still, from round 2's A5); zero resolutions from a caller naming the **survivor** (K4's quadrant); zero fixtures holding rows under two names of one closure (K2's quadrant); **exactly one** two-hop chain, whose three entries are all `replace(base, …)` — **identical policy and predicate at every hop** (K1's quadrant); zero band-branch `known` assertions; zero constructions where a key or closure crosses a namespace | **ACCEPTED.** **Three of the eight are the quadrants of the three BLOCKING findings above** — the row's own sentence for the eleventh time: *the fixture that would pose the question does not exist* |

#### 6.13c What the lens attacked and could NOT break

1. **Cycles and the cap.** Rules 3-17 and 3-16 both hold, with honest `why`s.
2. **Namespace at the closure surface — the fifteenth attempt, and it held again.** `type_closure` consults
   `vocab.entry(namespace, …)` and nothing else; **no hop crosses a namespace.** Consistent with all fourteen
   trips.
3. **`I-5`'s window, three ways** — propose-then-abandon and propose-then-**drain**-without-writing both
   answer `'pending'`. **Only `minted_ref` stands the guard down.** Standing rule (c) holds at this door.
4. **`Z6`'s fence** holds in `auto` mode.
5. **The R78 seam.** **Six lenses have now failed to force an instance row into the registry.**
6. **Rule U's ordering** — no confident outcome could be got through a `complete=False` by any route; the six
   absorbers fire before the tied set is built.
7. **`I-4`'s key on the TYPE half.** `act_key` is one function and the act, guard, read and write all call it;
   **the two doors could not be made to disagree about the type.** *(The label half is round 3's B1, a
   different function.)*

#### 6.13d What this lens says about the fix set

**Two of its five BLOCKING (K7, K6) are round-2 findings this row marked ACCEPTED and did not land**, and
**[Observed]** §6.10b's fix table lists `I-1`…`I-7`, B1, B5 and Z6 — **A11 and Z5 appear in neither the fix
table nor any deferral list.** With the beacon lens's B3 (nine more of the same), that is **eleven accepted
dispositions across two lenses that bound no commit.** §6.10a is titled *"What was NOT done, and why it
matters"* and names none of them.

**And three of the five (K4, K1, K2) are defects the fix set CREATED or left half-made in one change** — K4
by implementing one of three relations, K1 by minting three rules that contradict each other, K2 by widening
the extent past the distinctness key that landed beside it. **Prediction P3 is confirmed**: rule 3-19, the
newest rule and the only one that made a set *bigger*, is where the new defects live — and ING11, which said
its cost was unmeasured, is where K2 was found.

