# Walkthrough — how a non-technical person gets from a spreadsheet to an action

**Status:** Draft v0.1, 2026-08-27. Written to be argued with, not implemented.
**Companions:** [`../VISION.md`](../VISION.md) (thesis), [`../ROADMAP.md`](../ROADMAP.md) (sequence), [`FINDINGS-0.1-tenshen-archaeology.md`](FINDINGS-0.1-tenshen-archaeology.md) (why step 5 exists)

---

## Why this document exists

**[Observed]** Two people in one office spend about an hour a day each moving CSV and Excel files into Foundry by hand. **[Observed]** The organisation relies on Palantir-sourced contractors to build ingest, pipelines and transforms, because not enough people internally can. **[Inferred]** Those two facts are the same fact: getting a pipeline built means starting a procurement, so hand-uploading is *rational avoidance*, not a skills gap.

This walkthrough is the concrete test of whether the thing we are proposing would actually help that person. **If it takes a developer at any step, it has failed** — a tool that needs a contractor to set up has reproduced the problem it claims to solve.

Meet **Dana**. She is an analyst. She is expert in her domain and in Excel. She does not write code, does not have a database login, cannot install software without a ticket, and has no interest in learning what a foreign key is. She is not a beginner — she is a professional whose expertise is not software.

---

## Step 0 — What Dana has today

A file, `site_visits_2026_08.xlsx`, that lands in her Outlook every Monday from a regional office. Sixty or so rows:

| Visit date | Facility | Inspector | Region | Finding | Severity | Follow-up by |
|---|---|---|---|---|---|---|
| 2026-08-03 | Riverside Care Center | M. Okafor | 4 | Med storage unlocked | High | 2026-08-17 |
| 2026-08-04 | Bayview Nursing | J. Lindqvist | 4 | Staffing log incomplete | Medium | 2026-08-31 |

She opens it, tidies a few columns, uploads it, and someone downstream builds a report. **The hour a day is the tidying and the uploading**, repeated across several such files.

**What she actually wants** — and cannot get today: *"tell me which facilities have an overdue high-severity follow-up, and email the responsible inspector."* That is one question and one action. It is currently a person's afternoon.

---

## Step 1 — Connect (mostly not our product, and we should say so)

Dana forwards the file, or points at the folder/mailbox it arrives in.

**Be honest about this step: extraction and loading is a solved, crowded category.** Airbyte ships 600+ connectors and self-hosts at no cost; dbt owns SQL transformation; Airflow and Dagster own orchestration. **We consume them. We do not compete with them** (`VISION.md` §6). For Dana's spreadsheet, "connect" means a file drop or a mailbox watch, which is genuinely simple. For a live source system, it means an Airbyte connector someone configures once.

**What Dana sees:** she drops the file in, and within seconds gets a reading back — not a success message.

> **I think this file is about facility inspections.**
> 62 rows, 7 columns, no blank rows.
> `Visit date` looks like a date. `Severity` has 3 distinct values. `Facility` has 41 distinct values — I think these are places.
> **Does that sound right?**

She says yes. **She has not been asked to define a schema, and she never will be.**

**Why the reading matters more than the upload:** the file is the easy part. What has never been automated is *understanding what the file is about*, and that is where the contractor hours go.

---

## Step 2 — The mapping moment (this is the product)

This is the step Airbyte and dbt do not do, the step contractors are paid for, and the step everything else in this project exists to serve.

The system proposes a reading. It does not ask Dana to build one.

> **Here is what I think this file describes:**
>
> - **41 Facilities** — from `Facility`. *I already know 38 of these; 3 are new to me.*
> - **9 Inspectors** — from `Inspector`. **These look like People.** I already track 7; 2 are new.
> - **62 Inspections** — one per row. This is a new kind of thing; I have not seen it before.
> - **Relationships:** each Inspection *was performed at* a Facility, and *was performed by* an Inspector.
> - **Each Inspection has:** a date, a finding, a severity, and a follow-up deadline.
>
> **Two things I am unsure about:**
> 1. `Region` — is this a property of the Facility, or of the visit? *(I guessed: property of the Facility.)*
> 2. Is `Inspector` the same kind of person as the `Staff` I already know about, or different?

Dana corrects one thing — Region belongs to the Facility, and Inspectors *are* the same people as Staff. **That is the whole configuration step.** Two answers to two plain-language questions.

**Three properties of this interaction carry the design:**

1. **It proposes; she disposes.** She is never given an empty schema editor. **[Assumed]** that reviewing a proposal is achievable for a domain expert while authoring a model is not — this is the load-bearing usability bet and it is untested.
2. **It says what it already knows.** *"I already know 38 of these"* is the anti-pollution mechanism doing its work in the open — the system resolved her facilities against existing ones rather than creating 41 new records.
3. **It surfaces its uncertainty as a question, not a silent guess.** The two things it was unsure about are exactly the two things a contractor would have decided alone, invisibly, six months ago.

---

## Step 3 — Ask a question (the payoff, immediately)

Dana can now ask her real question. Not in SQL.

> **Which facilities have an overdue high-severity follow-up?**

> **4 facilities.** Riverside Care Center (11 days overdue), Elmwood Manor (4), Bayview Nursing (2), Harbor Point (1).
> *Riverside also has two other open findings from June. It is the only facility with more than one.*

She never joined a table. The join existed because step 2 established that inspections happen *at* facilities — **the relationship was captured once, at ingest, and every later question reuses it.** This is the difference between a graph and a pile of spreadsheets, and it is the whole reason the ontology is worth having.

The unprompted last line is the point of an ontology rather than a query tool: nothing asked about repeat offenders, but the structure made it visible.

---

## Step 4 — Turn it into an action

A question that ends in a chart is a BI tool. **The action is the part Foundry actually gets right, and the part we must match.**

> **Email each responsible inspector about their overdue high-severity findings.**

> **This would send 3 emails** (two facilities share an inspector).
> Here is the first:
>
> > To: M. Okafor
> > Subject: Overdue follow-up — Riverside Care Center
> > The high-severity finding from 3 Aug (medication storage unlocked) had a follow-up date of 17 Aug, now 11 days past. Riverside also has two open findings from June.
>
> **[Send all 3] [Edit] [Cancel]**

**Nothing is sent without a click.** The action is *composed* by the system and *authorised* by Dana. That boundary is not decoration — it is what makes an automated action safe enough for a regulated environment, and it is the same discipline Tenshen enforces as its L1–L4 action ceiling.

**Where the action definition comes from:** the ontology knows an Inspector is a Person, that a Person has an email, and that "notify" is a thing you can do to a Person. **Dana did not define an action.** She got one because the type system already knew enough.

---

## Step 5 — Next month, and the step that makes this different

September's file arrives. It has a new column: `Corrective Plan Status`. And the regional office has started logging a new kind of row — remote desk reviews, not site visits.

Most tools handle this one of two ways: silently ignore the new column, or break. **Both are the failure this project is named against.**

> **This file is slightly different from August's.**
>
> - **New column `Corrective Plan Status`** — 3 values (Submitted / Approved / None). I suggest adding it as a property of Inspection. *(Reviewing it as a property, not a new kind of thing, because it only ever appears alongside an inspection.)*
> - **11 rows say `Desk Review` where I expected a site visit.** I think this is a **new kind of Inspection**, not a new kind of thing entirely.
>
> **⚠ If I add `Desk Review`, here is what will not understand it yet:**
> - The **overdue follow-up alert** only looks at site visits → *desk reviews would be silently skipped*
> - The **regional summary** groups by facility → *works fine, no change needed*
> - The **inspector workload** report counts visits → *would undercount by 11*
>
> **[Add it and update all three] [Add it, leave the rest for now] [It's not a new kind — merge into site visits]**

**This screen is the entire product thesis in one interaction, and it comes directly from finding 0.1.**

The Tenshen incident that motivated it: a new type (`capture`) started being emitted, one piece of code had a private list that did not include it, and a feature was **silently dead** for exactly the case that had just started working. No error. No failing test. Found because a human noticed a button did nothing.

**Nothing on the market answers "if I add this type, what will silently ignore it?"** That question is why `consumers(type)` exists in the interface (`ROADMAP.md` §1). It is also the answer to the pollution problem from the other direction: **most ontology rot is not people adding types carelessly — it is people adding types without any way to see the consequences, so nobody ever cleans up because nobody can tell what is safe to touch.**

---

## What Dana never did

Worth stating plainly, because each is a place a real tool would have lost her:

- Write code, SQL, or a formula
- Define a schema, a table, or a data type
- Learn what an entity, a relationship, or an ontology is *(she was never shown the words)*
- File a ticket, or wait for a contractor
- Choose between "add a column" and "add a table"
- Discover three weeks later that a report had been quietly wrong

## What Dana did do — five decisions, all in her own domain language

1. *"Yes, that's what this file is."*
2. *"Region belongs to the facility."*
3. *"Inspectors are the same people as staff."*
4. *"Send those three emails."*
5. *"Yes, desk reviews are a new kind of inspection — update all three."*

**Every one is a judgement only she can make, and none requires software knowledge.** That is the bar. If a design step cannot be reduced to a question in this form, it belongs to the system, not the user.

---

## Where this could fail — the honest section

| Risk | Why it is serious | Cheapest early test |
|---|---|---|
| **Step 2's proposal is wrong often enough to erode trust** | A user who must correct four things in five stops reviewing and starts rubber-stamping — worse than no proposal, because errors now carry her approval | Run step 2 against 10 real messy files. **Measure the correction rate before building anything else.** **[Assumed]** it is low; entirely unvalidated |
| **Step 5's impact list is incomplete** | An impact list that misses a consumer is *more* dangerous than none — it promises safety it cannot deliver | Only claim consumers the registry can enumerate mechanically. **Never infer one.** Show "3 known, may be others" rather than "3" |
| **Dana's real files are far messier** | Merged cells, headers on row 4, three tables in one sheet, inconsistent facility names | Get five real files early. **[Assumed]** they resemble the clean example above; this is likely the weakest assumption here |
| **"Facility" and "Inspector" resolution is the hard part** | *"I already know 38 of these"* requires reliable entity resolution across spelling variants and name changes. This is a genuinely hard, well-studied problem | Do not hide it. Where confidence is low, **ask** — a fourth question is cheaper than a wrong merge |
| **Step 4's action needs a real integration** | Sending mail in a government environment means auth, audit, retention, and approval to send at all | Deliberately out of scope until Phase 3. **The compose-and-authorise shape is the claim; the transport is not** |
| **She has no permission to install anything** | Every step assumes a running system she can reach | Not a product problem, an adoption problem — but it decides whether the wedge is self-serve or must enter through an existing procurement |

## What this walkthrough does not address

- **Multi-user governance.** Dana is alone here. The pollution problem is fundamentally about *many* people editing one vocabulary over years, and this document shows none of that — deliberately, because the single-user path must work first, but do not mistake it for the hard case.
- **Scale.** 62 rows. Nothing here says anything about 62 million.
- **Who resolves a disagreement** when Dana says "Region belongs to the Facility" and another analyst says it belongs to the visit. **That is the actual ontology-governance problem**, and it is unaddressed.
- **Where the AI runs.** Steps 1, 2 and 5 imply a capable model reading the user's data. In a government context that is a data-residency question before it is a product question, and it may be disqualifying for the hosted version.

---

## The one-sentence version

**Airbyte moves the bytes; dbt reshapes the columns; neither knows what a *Facility* is — and the person who does know is the one currently locked out of the tools.** This walkthrough is a claim that the gap between "rows landed" and "typed, connected, actionable" can be crossed by proposal-and-confirmation rather than by a contractor, and step 5 is the claim that it can be crossed *repeatedly* without the result rotting.

**Both claims are [Assumed]. Neither has been tested. Step 2's correction rate is the cheapest way to find out, and it should be tested before any code is written.**
