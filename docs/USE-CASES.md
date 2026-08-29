# USE-CASES — the three fixtures every spec and design is validated against

**Status:** v1, 2026-08-28. Founder direction: *"we need 2-3 use cases to test what we're building against, more diverse the better. Tenshen can be one. we run our specs / designs against those use cases for validation (along with the adversarial review loops)."*
**Rule (ROADMAP standing constraint 7):** no spec or design is marked done until it carries a design-test section for **each** of the three use cases below and has survived an adversarial review loop. A recorded contortion is a pass; a silently accommodated one is a failure.

---

## Why these three — the diversity matrix

The three are chosen so that **no two share a failure mode**. Each column is something the product must survive; each use case is the fixture that exercises it.

| | **UC1 Tenshen** | **UC2 CMS citations** | **UC3 NYC Open Data** |
|---|---|---|---|
| Writers | one (single-owner codebase) | one agency, one export | **dozens of agencies**, independently |
| Shape | code registry of relationship types; consumers are code paths | one flat table, 23 columns, 419,479 rows | **2,399 datasets**, each with its own column vocabulary |
| Pollution mechanism exercised | **C silent drop** (0.1) + capability predicates | data-quality traps: fake booleans, value sets, redundant projections, `not_a_type` | **4 semantic collision across teams** — the kill-criterion row — plus 1 and 3 |
| What "type" means | edge label between app objects | entity extracted from rows (facility, citation, tag, value set) | **the same word meaning different things per publisher** ("status", "district", "borough", "type") |
| Namespace pressure | none (one implicit namespace) | none | **the whole point** — `namespace` stops being an unused field |
| Consumer of the package | Phase 2B: a third backend behind the adapter | Phase 2A: the reference implementation's test data | **Phase 3: the ingestion / mapping wedge** — the venture's actual customer shape |
| Data access | read-only from the beacon repo; never edited | public CMS file, reproducible by any reader | public Socrata catalog + per-dataset API, reproducible by any reader |
| Employer-data risk | none | none | none |

**What UC3 adds that the other two cannot:** multi-writer semantic collision, cross-dataset namespacing, and an ingestion-shaped consumer. Until now the kill-criterion mechanism (collision across teams) has been *assumed non-dominant* (A1) and never exercised. UC3 exercises it on public data that structurally resembles the HHS target (many government units publishing into one catalogue) without touching the office.

---

## UC1 — Tenshen: the single-writer app registry

**What it is [Observed].** `work_link_types` in `C:\Users\steph\projects\beacon` — a registry of relationship labels for `WorkLink` rows, seeded with five, grown at runtime by an AI classifier that proposes a new type only when confident none fit; `created_by: seed | ai | user`; usage counted. Seven entity-type vocabularies coexist in the codebase, five of them capability predicates (`FINDINGS-0.1`).

**What it tests.** Cause C (a consumer silently drops a type it does not know); predicates as distinct from types; the "one service, one table, not a rewrite" migration (PACKAGE §7); async transaction sharing (row 3b). It is the venture's **first rot experiment** (beacon spec §12): if this curated vocabulary stays clean as families grow, that is evidence for the core [Assumed] bet.

**Rules of use.** Read-only. It is a design *test*, never a design *input* — nothing takes a shape because Tenshen has it. Recorded so far: seven contortions in INTERFACE §9, one `ALTER TABLE` in PACKAGE §7.

**Data:** `beacon/src/beacon/models/work_link_type.py`, `.../services/work_link_service.py`; spec `beacon/docs/specs/2026-08-27-ontology-layer-exploration-design.md`.

## UC2 — CMS nursing-home health citations: one flat government export

**What it is [Observed].** `NH_HealthCitations_Aug2026.csv` from data.cms.gov — 165,336,194 bytes, 23 columns, 419,479 rows, 14,627 facilities. Pre-registered pathologies (`0.5-ground-truth-PREREGISTERED.md`): a boolean-sounding column holding six status strings; 1.28% of rows with a correction date preceding the survey date; a `Location` column 99.988% redundant with four others; 104 facility names shared across CCNs; a severity scale that a low-tier model inverted silently (`0.5-RESULTS.md`).

**What it tests.** Entity extraction from rows (facility, citation, tag, value sets); `resolve_type`'s `not_a_type` outcome; `value_set` as a kind; model tier as a product parameter; evidence against external documentation; the contract suite's CMS leg (`2A-RUN.md` reproduces every pre-registered count).

**Rules of use.** CMS wins any conflict with Tenshen (ROADMAP "Rule of the ordering"). The 400-row Montana sample is checked in; the full file is regenerated with `docs/tools/make_sample.py`.

**Data:** https://data.cms.gov/provider-data/dataset/r5ix-sfxw

## UC3 — NYC Open Data: many agencies, one catalogue, colliding words

**What it is [Observed 2026-08-28].** The City of New York's open-data portal, `data.cityofnewyork.us`: **2,399 datasets** in the Socrata catalog (`https://api.us.socrata.com/api/catalog/v1?domains=data.cityofnewyork.us&only=datasets`), each attributed to a publishing agency (e.g. "Taxi and Limousine Commission (TLC)", category "Transportation"), each with its own column names and value vocabularies, all queryable through one API pattern.

**Why it is the right third fixture [Inferred].** It is the public analogue of the HHS situation VISION §2 describes — many organisational units, rotating authors, no shared curation — with the multi-team collision mechanism visibly present: the same column word (`status`, `type`, `district`, `borough`, `agency`) carries different value sets and different meanings across publishers. It is also **ingestion-shaped**: the natural task is "land N datasets and get typed entities and relationships, not N piles of columns", which is Phase 3's wedge and the buyer's actual problem.

**What it tests.**
- **Mechanism 4, semantic collision across teams** — the ROADMAP kill row. The interface must handle two agencies' `status` as *scoped* types, not merge them. `namespace` (INTERFACE §2, currently "v0 requires nobody to use it") becomes load-bearing; `merge_types`'s `cross_namespace_merge` refusal gets its first real exercise.
- **Mechanism 1 and 3** at scale — no review, never retired: the catalogue's own age and duplication is the evidence.
- **`resolve_type` at scale** — does a proposer *find* the existing scoped type among thousands, or re-propose it (mechanism 2 wearing 1's clothes)?
- **Provenance** — every type traces to a dataset, an agency, an update date.
- **The Phase 3 loop** — the WALKTHROUGH's five steps against a source with many tables, not one.

**Protocol for a UC3 design test.** Pick **three datasets from three different agencies that share at least two column words** (e.g. `status`, `borough`); state the expected outcome for each shared word (same type / scoped types / not a type) *before* running the spec against it; record the outcome and every contortion. Keep the chosen dataset ids in the test so it is reproducible.

**Data:** catalog API above; per-dataset SODA endpoints `https://data.cityofnewyork.us/resource/<id>.json`. Public; keep pulled data out of git except small pinned samples.

---

## A governance precedent, not a fourth use case — Wikidata property proposals

**[Observed 2026-08-28]** at `https://www.wikidata.org/wiki/Wikidata:Property_proposal`: "Before a new property is created, it has to be discussed here. When after some time there are some supporters, but no or very few opponents, the property is created by a property creator or an administrator." Proposers must first "search the Wikidata:List of properties to see if it already exists"; a "Properties for deletion" process and archives record rejections and retirements.

**Why it matters.** It is a real, public, multi-writer, decade-old instance of the exact loop this product automates — propose → resolve-existing-first → discuss → approve/reject → retire — with its history visible. It is not a use case (nothing here will consume Wikidata) but it is the best available **evidence base** for "does the proposal→approval loop actually resist rot, and where does it fail?" Any spec that claims a governance property should be checkable against how Wikidata's process behaves.

---

## The validation protocol (applies to every spec and design from row 3c onward)

1. **Three design-test sections, one per use case**, each stating expected outcomes *before* the walk-through, then the walk-through, then every contortion recorded. UC2 wins conflicts with UC1; UC3 conflicts with either are recorded and decided by the supervisor or founder, because UC3 is closest to the customer.
2. **An adversarial review loop** (`/adversarial-review-loop`, two consecutive clean fresh reviewers) on the spec before it is marked done. The reviewer brief names the three use cases and asks the reviewer to break the spec against each.
3. **The retro pass (row 3c):** INTERFACE v0 and PACKAGE v0 were validated against UC1 and UC2 only. Row 3c runs UC3 and the adversarial loop against both, and records what changes — or that nothing does, which would itself be a finding about UC3's diversity.
