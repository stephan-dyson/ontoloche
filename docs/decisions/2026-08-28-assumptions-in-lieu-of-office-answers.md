# Decision 2026-08-28 — proceed on assumptions; office answers refine, not gate

**Founder ruling (verbatim intent):** "make reasonable assumptions and move forward — I will refine over the next few weeks and we can adjust. Begin working on a roadmap, specs, etc. and be cognizant of ordering with respect to unblocking Tenshen rebuilding on top of open-ontology."

**What this changes.** Phase 0's three office conversations (0.2, 0.2b, 0.4) stop being gates. Each gets an **[Assumed]** answer below, chosen to be the *most likely* reading given 0.1 and 0.5, and each names what would revise it. Phase 1 starts now. Every spec written under this decision carries the line *"written against the 2026-08-28 assumptions; see docs/decisions/"* so a later correction knows what to re-examine.

**What this does NOT change.** Standing constraint 0 (no employer data, ever) and constraint 5 (consume the ETL layer) are untouched. The kill criteria stand; assumptions are not a licence to skip them.

---

## A1 — 0.2, the HHS pollution mechanism

**[Assumed]** HHS's dominant mechanism is **1 + 3 together: anyone could add a type with no review, and nothing was ever retired** — with a named cause, contractor rotation (`VISION.md` §2, [Inferred]). Semantic collision (mechanism 4) is **present but not dominant**, as in Tenshen (2 of 7). Silent per-consumer drop (Cause C from 0.1) is **present but unobserved by the office**, because no existing tool surfaces it.

**Why this reading:** it is the only one consistent with all three first-hand observations — "too many entities", "too many people making changes", and "contractors build the pipelines". Plain duplicate sprawl without review is the base rate for multi-writer schemas everywhere.

**What it commits the interface to:** `propose_type` with an approval queue (mechanism 1), `usage`/`orphaned`/lifecycle (mechanism 3), `consumers` (Cause C), and `resolve_type` good enough that a proposer *finds* the existing type — all four first-class, none demoted. `merge_types` stays guarded. **No single call is "the centre"**; the centre is the proposal→approval loop.

**Kill-criterion check:** not tripped by assumption — collision assumed non-dominant. **Revise if:** the office reports two teams meaning different things by one word as the *main* complaint → stop, re-centre on namespacing, per the roadmap's kill row.

## A2 — 0.2b, what the contractors produce

**[Assumed]** a contractor engagement produces all four (connectors, transforms, ontology definitions, actions), and **ontology mapping — landed rows to typed entities/links — is the largest share, roughly half.** Connectors are mostly configured, not written (Airbyte-class problem); transforms are dbt-shaped; actions are few.

**Why this reading:** `VISION.md` §4b's argument that mapping is the un-automated layer; and 0.5 showed the mapping step is where model quality *matters*, which is where paid humans currently sit.

**What it commits the roadmap to:** the venture thesis holds provisionally — the product is the mapping layer (Phase 3), consuming Airbyte/dbt beneath. **Revise if:** hours turn out to be mostly plumbing → the venture narrows to the registry alone (Phase 1–2), and Phase 3 is dropped, not built.

## A3 — 0.4, has anyone tried to automate the uploads

**[Assumed]** the answer is **"a pipeline means a contractor engagement, and that queue is long"** — the first of the three readings. Manual upload is rational avoidance of a procurement, not a skills gap.

**Why this reading:** it is the direct consequence of the observed services dependency; "source system won't allow it" would not explain *two* people across *different* sources, and "nobody has asked" is unlikely in an office that already licenses the platform.

**What it commits Phase 3 to:** self-serve mapping — a domain analyst, not a contractor, gets a CSV into typed entities (`docs/WALKTHROUGH.md`). **Revise if:** "source system won't allow it" → Phase 3 is an engineering problem on the extraction side and belongs to Airbyte, not us.

## A4 — Tenshen Q7a (beacon spec §7)

**[Assumed]** Q7a resolves to the spec's own current recommendation: **file the write-shape rule, with the lint.** Not ruled — the ruling is the founder's, in the beacon repo — but open-ontology plans as if it lands, because §12 of that spec makes the lint the sensor for the venture's core bet.

**Revise if:** ruled *do-not-file* → Phase 2B proceeds without its sensor; the rot-detection evidence for the [Assumed] bet must come from open-ontology's own `usage`/`orphaned` reporting instead.

## A5 — "rebuild Tenshen on top" and the direction of the arrow

The beacon spec §12 (commit `27a9b712`) records: Tenshen will be rebuilt on top of open-ontology; build Tenshen's cheap version now (§6 slices); and *the arrow points from Tenshen as evidence, never as a dependency, until the venture has a working Phase 1 with a real outside user.*

**Founder direction today:** order open-ontology's work so that rebuild is unblocked as early as possible.

**Reading adopted [Assumed on the interpretation, founder to confirm]:** the two are compatible. §12's condition "working Phase 1 with a real outside user" is **relaxed to "Phase 2A passes contract tests with CMS data as its primary consumer."** CMS public data is the outside consumer; a paying user is not required before Tenshen may depend on the package. The three §12 reasons still bind: the abstraction is derived from messy government data first, Tenshen second; Tenshen's §6 slices proceed independently in beacon and are not waited on; `work_link_types` staying clean is the venture's first experiment.

**What it commits the roadmap to:** component order = **what Tenshen's slices consume first.** See `ROADMAP.md` §"Ordering for the Tenshen rebuild".

---

## Assumptions register (for the office visits)

| # | Roadmap row | Assumed answer | The one question that tests it |
|---|---|---|---|
| A1 | 0.2 | no-review + never-retired dominant; collision minor; silent-drop present | "When someone adds a type, how do they find out what breaks?" |
| A2 | 0.2b | ~half of contractor hours are ontology mapping | "What does an engagement actually produce?" |
| A3 | 0.4 | long queue for a pipeline | "Has anyone tried to automate the uploads?" |
| A4 | Q7a | file with lint | founder ruling in beacon |
| A5 | §12 arrow | relaxed to "2A passes contract tests on CMS data" | founder confirms this reading |

When an office answer arrives, edit the row, tag the change **[Observed]**, and open a roadmap diff — do not silently rewrite the specs.
