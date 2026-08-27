# Vision — an open ontology and pipeline layer

**Status:** Draft v0.1 — first pass, written 2026-08-27, to be refined over the coming weeks
**Author:** Stephan Dyson
**Working name:** none yet (directory name is a placeholder)

> **How to read this.** Claims are marked by how much they are worth. **[Observed]** — seen directly, first-hand. **[Inferred]** — a reasonable read of observed things, not yet confirmed. **[Assumed]** — believed, not tested, and the thing most likely to be wrong. Keeping these separate is the single discipline that matters in a document this early, because conviction is easy and evidence is not.

---

## 1. The thesis, in one paragraph

Palantir Foundry already ships a governed ontology layer. **In the field, it rots.** Too many entities, too many editors, no curation discipline — and the layer becomes something people route around rather than through. Every open-source alternative currently visible is cloning Foundry's *structure*, which is the part that already exists and already failed. **The product is not an ontology layer. It is an ontology layer that resists rot** — one where the AI proposes and curates the vocabulary and humans approve, instead of humans hand-editing a schema into mud.

---

## 2. What was actually observed

All of this comes from one day inside an HHS office that licenses Foundry. **[Observed]** unless marked otherwise.

**They are not fully adopting Foundry, for three stated reasons:**

1. **Too complex.**
2. **Vendor lock-in.**
3. **The ontology is already polluted** — too many entities, too many people making changes to it.

**What they use instead:** PowerBI, PowerAutomate, Smartsheets, Excel. Chosen because *they know how to use them and the job gets done* — a friction and familiarity win, not a capability one.

**And the part that inverts the picture:** at least two people spend **at least an hour a day** doing manual uploads of Excel files and CSV dumps — **into Foundry**. So the spreadsheets are not only a destination that routes around the platform; they are also the **on-ramp into it**. Humans are the pipeline.

That is roughly **500 person-hours a year**, discovered from a sample of two conversations on day one. **[Inferred]** that the true figure across the organisation is materially larger; two people is not a base rate and this number must not be extrapolated without asking more people.

**Second data point:** the same ontology-pollution pattern was visible in consulting engagements at Deloitte. **[Observed]**, but by the same observer — so it is two readings by one person, not two independent sources. It is still the strongest available evidence that the pattern generalises beyond one office.

---

## 3. Why the obvious version of this idea fails

**Reason 3 is the one that made Foundry unusable — and open-sourcing an ontology layer does nothing about it.**

Ship a free, Foundry-shaped ontology layer and it rots the same way, just cheaper. Reasons 1 and 2 (complexity, lock-in) are addressed by an open alternative. Reason 3 is not, and reason 3 is the one that pushed real work into spreadsheets.

This is the thing to hold onto when the project inevitably drifts toward "let's build the object model." **The object model is table stakes and it is not what failed.**

---

## 4. The differentiator: an ontology that curates itself

The failure mode is *entropy under multi-writer pressure*. The answer is not more governance ceremony — it is to move curation off the humans.

**The shape:**

- **The AI proposes types**, and only when it is confident that no existing type fits. New vocabulary is a suggestion, not a free-for-all.
- **Every entry carries provenance** — was this type seeded, inferred, or human-authored? Who, when, on what evidence?
- **Duplicates get detected and merged**, rather than accumulating as near-synonyms.
- **Drift is surfaced**, not silently absorbed — usage counts, orphaned types, types that stopped being used.
- **Humans approve; humans do not hand-edit a schema.** The moment a schema becomes a form that anyone can fill in, it starts rotting.

**There is a working precedent for this** in an existing codebase (Tenshen's `work_link_types`): a relationship-type registry with `name`, `definition`, `is_symmetric`, `inverse_label`, `created_by: seed | ai | user`, and `usage_count`, where an AI classifier proposes a new type only when confident none of the existing ones fit. It governs one edge family today. **[Inferred]** that the pattern generalises; that is the core technical bet of this project.

---

## 5. The wedge: ingestion, aimed at the rot problem

**Do not start with the framework. Start with the hour a day.**

The first build should take those daily CSVs and land them **with provenance and typed relationships intact** — so what accumulates is a curated graph rather than another pile of entities.

This does three things at once:

1. **Immediate, measurable ROI** in a room where the pain is already quantified.
2. **It forces the hard problem.** You cannot do automated ingestion into an ontology without answering *"what type is this, and does it already exist?"* — which **is** the anti-rot problem. The curation engine is not a later phase; it is what makes ingestion work.
3. **It supplies real design inputs.** The abstraction gets derived from live, messy, government-shaped data instead of from one app's schema.

**Open question that decides the first build** — must be answered before writing code:

> *Has anyone tried to automate these uploads, and what happened?*

- **"It's a six-month queue to get a pipeline built"** → the product is a self-serve connector, and reasons 1 and 2 are the operational cause. This is a business.
- **"The source system won't allow it"** → an engineering problem with a narrow technical answer.
- **"Nobody has asked"** → an organisation that has not noticed 500 hours. Different sale entirely.

A second question, equally cheap: *once the CSV lands, does anyone connect it to anything else — or does it just sit there?* That distinguishes "they need better ingestion" from "they need relationships," and those are different products.

---

## 6. What this is NOT

Scope discipline, written down early because this idea has already demonstrated strong scope gravity.

- **Not a Foundry clone.** No compute, no pipeline orchestration engine, no dashboarding suite, no data platform.
- **Not an ontology editor for non-engineers.** That is precisely the thing that produced reason 3.
- **Not a general knowledge-graph database.** RDF/OWL/SPARQL exist and are decades mature; interoperate, do not compete.
- **Not a BI tool.** PowerBI is not the enemy and not the target.

---

## 7. Business model

**Open source, with a compliance-and-operations arm — not a "support" arm.**

The distinction matters. Support-as-bugfixes is a weak model: it is demand-driven, requires adoption first, and creates a perverse incentive to ship operationally complex software.

**The real service is carrying the compliance burden.** The US federal government adopts open source widely, and an Authorization to Operate authorises *a system's* security risk — it is not a vendor-presence test. But the ATO work has to be done by someone: control implementation, assessment evidence, continuous-monitoring artifacts, and an accountable party when an auditor asks. With a FedRAMP'd SaaS vendor, the vendor carries most of that. **With self-hosted open source, the agency carries it themselves** — which is why agencies drift toward vendors even when the licence is free.

So the paid product is: control documentation, ATO evidence packages, continuous monitoring, and someone accountable. **[Inferred]** that this is priced against a cost agencies already pay in staff time, which makes it an easier sale than net-new spend.

**This inverts the usual open-source sequencing risk.** The normal failure is: build free thing → hope adoption comes → hope support demand follows. Here the compliance entity is not a harvest, it is **a precondition for adoption**. Different bet.

---

## 8. Competitive landscape

**[Observed]** as of 2026-08-27, via search:

- **[foundry-ontology-open](https://github.com/cloudbadal007/foundry-ontology-open)** — implements exactly the target shape: ObjectTypes, LinkTypes, ActionTypes, and an MCP server exposing `execute_action` / `list_actions`. **79 stars, 21 forks, 2 watchers — and 2 commits total.**
- **[Przyval/openfoundry](https://github.com/Przyval/openfoundry)** — a Foundry SDK-compatible emulator.
- **[Shamdon/openfoundry](https://github.com/Shamdon/openfoundry)** — self-hosted Foundry alternative.
- **[Timbr](https://timbr.ai/)**, **[Dashjoin](https://dashjoin.medium.com/demystifying-palantir-features-and-open-source-alternatives-ed3ed39432f9)** — commercial-open semantic-layer plays.

**The read: the category is attempted, not won.** 79 stars on a two-commit repository is demand signal against vapor supply — people want this to exist and nobody has built it. For a conviction-driven project that is close to the best available market position.

**The caveat that must stay in view:** starring is free. It measures *"this should exist,"* not *"I will run this in production."* And the population that most needs a governed ontology layer — enterprises — is also the population with budget to simply buy Foundry. **[Assumed]** that a materially large segment prefers open and self-hosted for lock-in, cost, or data-residency reasons. This is the load-bearing commercial assumption and it is untested.

**None of the existing scaffolds is building against rot.** They are cloning structure. That is the opening.

---

## 9. What is NOT yet validated

Written plainly, because the surrounding conviction makes it easy to skip.

| Claim | Status |
|---|---|
| Foundry's ontology rots under multi-writer pressure | **[Observed]** in one office; **[Observed]** in a second context by the same observer |
| Manual CSV ingestion is a real, costly pain | **[Observed]**, two people, one day, unextrapolated |
| Anyone would *adopt* a different ontology layer | **Not validated.** Nobody has said this |
| A self-curating ontology solves rot | **[Assumed]** — the core technical bet |
| Agencies would pay a compliance arm | **[Assumed]** — the core commercial bet |
| The pattern generalises beyond public-sector health | **[Inferred]** from N=2, same observer |
| Open-source distribution beats commercial for this buyer | **[Assumed]** |

**Nobody has told Stephan they would adopt a different ontology layer.** What they have said is that data entry is tedious and Foundry is complex, locked-in, and polluted. Those are related but not identical to the product thesis.

---

## 10. Sequencing, and what it protects

**Do not quit to build this.** The current job is simultaneously the research lab, the customer-discovery channel, and the funding source — and that configuration is rare and temporary. What burns savings is building for eighteen months before contact with a user; what preserves them is shipping something small into a real workflow fast. The decision to spend capital should arrive with evidence attached, not conviction.

**Phase 0 — this week, no code.** Answer §5's two questions. Find out *why* the ontology got polluted; the reasons are the design constraints.

**Phase 1 — the ingestion wedge.** Automated CSV/Excel landing with provenance and typed relationships. Narrow, specific, one organisation.

**Phase 2 — the curation engine.** Type proposal, duplicate merge, drift surfacing. Emerges from Phase 1 because Phase 1 cannot work without it.

**Phase 3 — generalise.** Only once Phase 1 works for a real user, and ideally once a second organisation in a different sector confirms the shape. **[Inferred]** from N=2 that generalisation exists; that is not a licence to design for it yet.

**The named failure mode:** building the general thing before the specific thing works. Every scaffold in §8 — 79 stars, two commits — is somebody who started with the framework instead of the problem. The advantage here is a specific problem, a specific organisation, and specific humans losing an hour a day. Stay inside that until it works.

---

## 11. Open questions for the coming weeks

1. Has anyone tried to automate the uploads, and what happened? *(decides the first build)*
2. Once data lands, is it connected to anything — or does it sit? *(ingestion vs relationships)*
3. **Why** did the ontology get polluted? Who could edit it, and what was missing? *(the actual design spec for the curation engine)*
4. What specifically does "lock-in" mean to them — data extraction, ontology definitions, pipeline logic, or actions? *(four different products)*
5. Would portable ontology + actions over a retained Foundry compute layer solve it? *(replacement vs escape hatch — the escape hatch is a far smaller build)*
6. What would have to be true to run something self-hosted? *(the real shape of the compliance arm)*
7. Who else has this problem? *(warm intros inside government are worth more than GitHub traffic)*

**A boundary to settle before asking any of these of colleagues:** employment terms, conflict-of-interest rules, and procurement ethics if that office could ever be a customer. Worth being clear on before the conversations, not after.

---

## 12. Why this is worth doing

Foundry is a walled garden around a pattern that ought to be public: **typed entities, typed relationships, and governed actions that AI agents can safely call.** That pattern is becoming the substrate for how organisations put AI to work, and it is currently owned by a vendor whose customers describe it as too complex, locked-in, and — in the field — polluted beyond use.

An open, self-curating alternative would let an organisation own its own semantics. That is worth building even if the commercial case takes years to prove, and the author has stated he would consider it a satisfying legacy regardless of outcome.

**That is a legitimate objective function. It is simply a different one from "this will make money," and the roadmap, the time budget, and the definition of failure all differ depending on which is actually being optimised.** Worth re-reading that sentence at each major decision.
