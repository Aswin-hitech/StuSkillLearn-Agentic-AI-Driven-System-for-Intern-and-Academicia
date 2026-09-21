# 🚀 StuSkillLink

### **An Agentic AI-Based Portal for Academia-Industry Collaboration**

> **Right Student. Right Skill. Right Internship. Deserving Opportunity.**

**StuSkillLink** is an Agentic AI-powered portal that connects **students, industries, academicians, and institutions** on a single platform. Instead of stopping at internship recommendation or candidate shortlisting, StuSkillLink continuously manages **skill mapping → ranking → allotment → acceptance → screening → reallocation → curriculum feedback**, and extends the same allocation logic to match academicians with their own industry opportunities.

The goal is simple:

> **The right skill, visible to the right person, matched to the right opportunity — continuously, not once.**

---

## 🏛️ Smart India Hackathon

| Field                 | Details                                                                             |
| --------------------- | ------------------------------------------------------------------------------------ |
| **Problem Statement** | SIH26044                                                                              |
| **Title**             | Portal for Academia-Industry Collaboration for Skill Mapping, Internships and Placement |
| **Theme**             | Smart Automation                                                                      |
| **PS Category**       | Software                                                                              |
| **Project**           | StuSkillLink                                                                          |
| **Team ID**           | KITSIH26-S120                                                                         |
| **Team Name**         | CodeRhythm                                                                            |

---

# 🎯 The Problem

A significant gap exists between the skills students acquire in academic institutions and the competencies industries actually expect.

* Students don't know what skills their target roles require until they're rejected.
* Industries receive thousands of applications but can't efficiently find the right-fit candidates.
* Academicians have almost no visibility into industry hiring trends, or into industry opportunities — FDPs, consultancy, research collaboration — that could keep their own practice current.
* Institutions have no aggregated view of how their students and faculty are actually doing against any of this.

Consider a simple scenario:

A company opens **6 Applied AI internship seats**.

Hundreds of students apply, most without knowing whether their skills even match the role.

The system identifies suitable, skill-matched candidates.

One candidate receives an offer but declines.

Another accepts but fails screening.

Seats become vacant again — and without an adaptive mechanism, this requires repeated manual intervention while other qualified, skill-matched candidates remain in the pool.

At national scale — roughly **1.5 million engineering graduates produced annually** in India, with the **India Skills Report 2026** putting overall graduate employability at just **56.35%** — this isn't a shortage of opportunity. It's a visibility problem, repeated at scale.

---

# 💡 Our Solution

**StuSkillLink** introduces an Agentic AI layer that continuously manages skill mapping, allocation, and cross-stakeholder collaboration — not as a one-time event, but as a running ecosystem.

Instead of:

```text
Student → Apply Blind → Wait → Rejection (no feedback)
```

StuSkillLink follows:

```text
Profile + Transcript
        ↓
Eligibility & NOC Verification
        ↓
Skill-Gap Analysis  ──────→  Curriculum Framing Agent  ──────→  Curriculum Insight (Academician)
        ↓
LSRW Communication Assessment
        ↓
Digital Portfolio Update
        ↓
Intelligent Tiered Ranking
        ↓
Seat Allocation (Preferred Partners → General Pool)
        ↓
Candidate Response
        ↓
Screening Outcome
        ↓
Observe
        ↓
Reallocate if Required
        ↓
Seat Filled → Placement Continuity Check
        ↓
Feedback Loop → back into Skill-Gap & Curriculum Framing Agent
```

In parallel, the same ranking-and-allocation logic runs for a second market: **academicians matched to FDPs, consultancy projects, research collaborations, guest lectures, mentorships, workshops, and innovation challenges** published by industry and institutions.

The system continues this process until available seats and opportunities are filled or the allocation cycle reaches its defined boundary.

---

# 🤖 Why Agentic AI?

A conventional AI model may simply answer:

> "Which internship is suitable for this student?"

StuSkillLink goes further. The system can:

* **Assess** a student's real skill gap against live industry demand — before they apply
* **Score** communication ability (Listening, Speaking, Reading, Writing) as a role-weighted ranking input
* **Rank** eligible candidates and academicians into explainable tiers
* **Allocate** seats and opportunities, progressively, across multi-seat roles
* **Observe** acceptance, decline, and screening outcomes
* **Reallocate** vacant seats automatically
* **Frame** batch-wide skill gaps into concrete syllabus recommendations
* **Escalate** unresolved cases to human administrators
* **Feed back** every outcome into curriculum insight and institution analytics

### Agentic Loop

```text
   ┌───────────┐
   │ SKILL-GAP │
   └─────┬─────┘
         ↓
   ┌───────────┐
   │   RANK    │
   └─────┬─────┘
         ↓
   ┌───────────┐
   │ ALLOCATE  │
   └─────┬─────┘
         ↓
   ┌───────────┐
   │  OBSERVE  │
   └─────┬─────┘
         ↓
   ┌───────────┐
   │  DECIDE   │
   └─────┬─────┘
         ↓
   ┌───────────┐
   │REALLOCATE │
   └─────┬─────┘
         │
         └───────────→ Repeat, feeding outcomes back into Skill-Gap & Curriculum Framing Agent
```

This creates a **closed-loop, continuously self-correcting ecosystem** rather than a one-time recommendation or allocation event.

---

# 🧠 Core Features

## 1. Skill Assessment & Skill Mapping

Every student completes a skill and aptitude assessment. The system compares three things: what a student has actually studied (transcript/curriculum), what they've self-reported (profile), and what industry roles in their target domain actually require. This produces a personal **Skill-Gap Report** with actionable learning-path suggestions — before a single application is wasted on a poor-fit role.

## 2. LSRW Communication Assessment

A one-time, auto-graded test covering **Listening, Speaking, Reading, and Writing**:

* Listening/Reading — comprehension quizzes, auto-graded
* Speaking — recorded response, transcribed via speech-to-text, scored for fluency and coherence
* Writing — LLM rubric scoring against grammar, structure, vocabulary, coherence

The composite score is generated once and reused across every application. It is a **role-weighted ranking input**, not a pass/fail gate — a back-end analytics role and a client-facing consulting role can weight it very differently.

## 3. Eligibility Gate

Eligibility is verified before a candidate enters the ranking pipeline. For final-year students, the system verifies a valid **No Objection Certificate (NOC)**, checked against the Institution Module, before the candidate proceeds.

```text
Student Profile
      ↓
Eligibility + NOC Check
      ↓
 ┌───────────────┐
 │  Eligible?    │
 └───────┬───────┘
     YES ↓       ↓ NO
    Ranking    Rejected /
                Pending
```

## 4. Tiered Candidate Ranking

Candidates are organized into priority tiers based on fit and flexibility, not a single flat score.

* **Tier 1 — Best Fit + Flexible:** strong skill/project match, flexible across eligible locations.
* **Tier 2 — Best Fit + Limited Flexibility:** strong candidate, restricted to selected locations.
* **Tier 3 — Remote / Virtual Only:** qualified, restricted to virtual roles.

Within each tier, candidates are sub-ranked by skill-gap-adjusted match score, LSRW score (weighted by the role's stated Communication Weight), project relevance, experience, and reservation-category rules where applicable — with application timestamp as the final, deterministic tie-breaker. Every step is logged and explainable. The same tiered-ranking engine is reused, unmodified in principle, to rank academicians against FDP, consultancy, and research opportunities.

## 5. Multi-Seat Progressive Allocation

```text
Applied AI Intern
Seats Available: 6

Candidate 01 → Offer → Accepted ✅
Candidate 02 → Offer → Declined ❌
                         ↓
Candidate 03 → Offer → Accepted ✅
Candidate 04 → Offer → Screening Failed ❌
                         ↓
Candidate 05 → Offer → Accepted ✅
...
6 / 6 Seats Filled → Vacancy Closed
```

## 6. Automatic Reallocation

```text
Seat Vacant
     ↓
Find Next Ranked Candidate
     ↓
Offer
     ↓
Observe Response
     ↓
Accept ───────→ Continue Screening
     │
     └─ Decline → Next Candidate
```

A declined offer or failed screening never stalls the process.

## 7. Internship-to-Placement Continuity

On successful internship completion with positive performance feedback, the system automatically evaluates the candidate for a full-time placement at the same or a comparable industry partner — turning an internship into a pipeline, not a dead end.

## 8. Verified Digital Portfolio

Every confirmed outcome — certifications, project records, internship completions, performance feedback, LSRW scores — is compiled automatically into a student's digital portfolio, pulled directly from platform records rather than self-declared, and issued as verified credentials linked to completed industry-led learning programs.

## 9. Academician Opportunity Matching

The same tiered-ranking engine that allocates student seats is reused to match academicians against opportunities industry and institutions publish: faculty internships, industrial training, FDPs, consultancy projects, research collaborations, guest lectures, mentorship, workshops, and innovation challenges. One agent curates what's available; a second matches academicians to it — proving the ranking engine generalizes rather than being single-purpose.

## 10. Curriculum Framing

A dedicated agent clusters batch-wide skill weaknesses (not individual gaps) and turns them into concrete, NOS-mapped syllabus recommendations for academicians and institutions — closing the loop from live industry demand back into what's actually taught.

## 11. Institution Analytics

Institutions get an aggregated dashboard — placement progress, academician opportunity engagement, NOC compliance, and skill-demand trends — scoped to the whole institution rather than one course or department.

## 12. AI-Powered Communication

The LLM is used as a communication and explainability layer. It generates offer letters, interview process information, HR contact details, candidate allocation explanations, curriculum insight summaries, and human-readable ranking explanations. The LLM does not make allocation decisions — **deterministic eligibility and ranking logic handles every critical decision**; AI supports understanding, semantic matching, and communication.

## 13. Explainable Allocation

A candidate should not simply receive "You were ranked #17." StuSkillLink can provide:

```text
Ranking Explanation

Skill Match:        92%
LSRW Score:         81% (Medium weight for this role)
Project Relevance:  88%
Experience:         80%
Location Fit:       Tier 1

Overall: Highly suitable candidate for the role.
```

## 14. Human-in-the-Loop

```text
             AI Allocation
                   ↓
          ┌────────┴────────┐
          ↓                 ↓
      Normal Case      Exception
          ↓                 ↓
     Auto Process      Human Review
```

Administrators can intervene on unresolved responses, eligibility disputes, allocation overrides, escalations, and reservation-category or policy questions.

---

# 🏗️ System Architecture

```text
┌────────────────────────────────────────────────────────────────────┐
│                          StuSkillLink                              │
│         Agentic AI Portal for Academia-Industry Collaboration      │
└────────────────────────────────────────────────────────────────────┘

  ┌───────────┐  ┌──────────────┐  ┌───────────┐  ┌───────────────┐
  │ Students  │  │ Academicians │  │ Industry  │  │  Institutions │
  └─────┬─────┘  └──────┬───────┘  └─────┬─────┘  └───────┬───────┘
        └───────────────┴────────┬───────┴────────────────┘
                                  ↓
                    ┌───────────────────────────┐
                    │      Data Ingestion        │
                    └─────────────┬─────────────┘
                                  ↓
              ┌────────────────────────────────────────┐
              │   Intake & Eligibility Agent            │
              │   (NOC check + profile normalization)   │
              └─────────────────┬────────────────────────┘
                                  ↓
              ┌────────────────────────────────────────┐
              │ Skill & Communication Intelligence Agent│
              │ (Skill-Gap Report + LSRW scoring)       │
              └─────────────────┬────────────────────────┘
                          skill-gap data
                                  ↓
              ┌────────────────────────────────────────┐
              │      Curriculum Framing Agent           │
              │ (clusters batch-wide skill weaknesses   │
              │  → NOS-mapped syllabus recommendations) │
              └─────────────────┬────────────────────────┘
                                  ↓ recommendations
                    Curriculum Output (Academician / Institution)
                                  ↓
              ┌────────────────────────────────────────┐
              │  Portfolio & Preference Agent            │
              │  (verified portfolio + preferences)      │
              └─────────────────┬────────────────────────┘
                                  ↓
              ┌────────────────────────────────────────┐
              │   Matching & Allocation Agent             │
              │   (tiered ranking + multi-seat allocation)│
              └─────────┬───────────────────┬────────────┘
                        ↓                   ↓
          ┌───────────────────────┐  ┌───────────────────────────┐
          │  Candidate / HR       │  │ Academician Engagement    │
          │  Interaction          │  │ Agent (curate + match     │
          │                       │  │ FDP/consultancy/research) │
          └───────────┬───────────┘  └─────────────┬─────────────┘
                        ↓                             ↓
              ┌────────────────────────────────────────┐
              │ Monitoring, Notification &              │
              │ Escalation Agent                        │
              └─────────────────┬────────────────────────┘
                                  │
                       ┌──────────┴──────────┐
                       ↓                     ↓
                   Filled Seat /       Escalation → Admin
                   Matched Opportunity        │
                       │                      │
                       └──────────┬───────────┘
                                  ↓
                    Feedback → Skill & Communication
                    Intelligence Agent + Curriculum Framing
                    Agent + Institution Analytics Dashboard
```

---

# 🧩 Agent Architecture

StuSkillLink is built as **seven specialized agents** — each owning a complete responsibility rather than a narrow sub-step, reducing integration overhead while preserving full functional coverage across all four stakeholders.

| # | Agent                                             | Responsibility                                                                                                                      |
| - | -------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| 1 | **Intake & Eligibility Agent**                     | Validates age/education/NOC eligibility for all stakeholders; parses resumes, transcripts, and CVs; normalizes and structures profile data |
| 2 | **Skill & Communication Intelligence Agent**       | Produces the personal Skill-Gap Report; administers and grades the LSRW test                        |
| 3 | **Portfolio & Preference Agent**                   | Builds each student's verified digital portfolio from confirmed platform records; captures ranked industry preferences and Open-to-Any-Partner declarations |
| 4 | **Matching & Allocation Agent**                    | Builds the tiered, skill-gap- and LSRW-weighted rank list (with reservation-category handling and timestamp tie-break); runs two-stage, multi-seat allocation; checks internship-to-placement continuity |
| 5 | **Academician Engagement Agent**                   | Curates opportunities industry/institutions publish for academicians (FDPs, consultancy, research, guest lectures, mentorship, workshops, innovation challenges) and matches academicians to them using the same ranking logic |
| 6 | **Monitoring, Notification & Escalation Agent**    | Tracks outcomes across every flow; triggers re-offers on decline/failure; generates offer letters and notifications; escalates unresolved cases; feeds outcomes back into the Skill & Communication Intelligence Agent and Curriculum Framing Agent |
| 7 | **Curriculum Framing Agent**                       | Clusters batch-wide skill weaknesses (not individual gaps) from skill-gap data and industry input; produces NOS-mapped syllabus recommendations and adopted curriculum outputs for academicians and institutions |

The agents work together as a closed-loop system spanning students, academicians, industry, and institutions.

---

# 🧮 Allocation Logic

A candidate's position is determined using multiple factors rather than a single academic score.

Conceptually:

```text
Candidate Priority
        =
Eligibility
      +
Skill-Gap-Adjusted Match
      +
LSRW Score (role-weighted)
      +
Project Relevance
      +
Experience
      +
Location / Flexibility Tier
      +
Reservation-Category Rules (explicit, auditable step)
```

Timestamp is the final, deterministic tie-breaker. The exact weights are configurable per scheme and policy requirement.

For large-scale optimization, the system can use:

* Weighted tiered scoring
* Constraint-based matching
* OR-Tools (CP-SAT)
* Hungarian algorithm

---

# 🗃️ Data Model

## Student
```text
Student
├── Student ID / Profile
├── Transcript / Completed Courses
├── Skills, Certifications, Projects, Experience, Resume
├── Domain / Location / Work-Mode Preference
├── Industry Preference List + Open-to-Any Declaration
├── LSRW Score + Per-Dimension Breakdown
├── NOC Status
└── Application Timestamp
```

## Academician
```text
Academician
├── Name, Department, Institution
├── Courses Taught, Curriculum/Syllabus Topics
├── Research Interests, Availability
└── Batch/Section Mentored
```

## Industry Partner
```text
Industry
├── Role Type (Internship / Placement)
├── Job Description, Seats Available
├── Required Skills / Projects / Certifications / Languages / Location
├── Communication Weight (Low / Medium / High)
├── HR Contact
├── Feedback on Past Interns/Hires
└── Published Learning Programs & Collaboration Opportunities
```

## Institution
```text
Institution
├── Policies, NOC Templates & Records
├── Departments
├── Academic Rules, Holiday Calendar
└── Resources
```

## Portfolio
```text
Portfolio
├── Student ID
├── Verified Skills & Certifications (with source)
├── Project Records
├── Internship Completions & Performance Feedback
└── Achievement Badges (W3C Verifiable Credentials / Open Badges 3.0)
```

## Opportunity Record
```text
Opportunity
├── Type (FDP / Consultancy / Research / Guest Lecture / Mentorship / Workshop / Innovation Challenge)
├── Source (Industry / Institution)
├── Eligibility Criteria
├── Matched Academician
└── Status
```

## Curriculum Record
```text
Curriculum Recommendation
├── Batch / Department
├── Clustered Skill Weaknesses
├── NOS-Mapped Syllabus Recommendation
├── Academician + Industry Sign-off Status
└── Adoption Status
```

## Match Record
```text
Match
├── Student/Academician ID
├── Role/Opportunity ID
├── Tier, Rank Score
├── Match Stage (Preferred Partner / General Pool)
├── Allocation Status, Offer Status, Screening Status
├── HR Contact, Interview Details
└── Placement-Continuity Flag
```

---

# 🔐 Fairness & Transparency

Because this platform affects real students' careers and real academicians' professional opportunities, fairness is a core design requirement. StuSkillLink maintains:

* Explicit eligibility rules
* Explainable, tiered ranking
* Auditable allocation and reservation-category decisions
* Configurable scoring
* Human override capability
* Policy-aware constraints
* Allocation logs

Two specific fairness risks are called out deliberately rather than glossed over:

* **LSRW scoring bias** — automated Speaking/Writing grading can unintentionally penalize regional accents or non-native phrasing. This requires a documented, auditable rubric and periodic human calibration review, not a one-time setup.
* **Reservation-category logic** — handled as an explicit, logged ranking step so any allocation outcome involving quota rules can be explained on request, never silently folded into a black-box score.

The system does **not** allow an opaque LLM response to directly determine eligibility or final allocation without controlled rules and validation.

---

# 📊 Example

### Student — Priya

Skills:
```text
SQL, Python, Data Analysis
```

Skill-Gap Report:
```text
Missing: Cloud Fundamentals (present in 70% of target roles)
Action: Enrolled in a platform-linked cloud-fundamentals course
```

LSRW Score:
```text
Reading:  Strong
Writing:  Strong
Speaking: Moderate
Composite: 81%
```

Preferences:
```text
Bright Analytics (preferred)
Open-to-Any-Partner: Yes
```

Eligibility:
```text
NOC Verified ✅ (final-year)
```

### Company

```text
Role: Data Analyst Intern
Location: Any (Medium Communication Weight)
Seats: 5
```

### Result

Priya receives:
```text
Tier: 1
Skill Match: High (post cloud course)
LSRW Contribution: Moderate-positive (Medium weight role)
Location Flexibility: High
```

She is allotted a seat, accepts, and clears screening.

Three months later, the Allocation Agent's placement-continuity check flags her as eligible for a full-time opening at Bright Analytics — offered without reapplying.

### Meanwhile — Dr. Meera (Academician)

The Curriculum Framing Agent clusters the same cloud-fundamentals gap across Dr. Meera's batch and recommends a syllabus update, pending her and industry's joint sign-off. Separately, the Academician Engagement Agent matches her to a data-engineering consultancy project Bright Analytics has published — allotted through the same ranking logic used for Priya.

Both outcomes appear on their institution's Analytics Dashboard by year end.

---

# 🆚 Recommendation vs. Allocation vs. StuSkillLink

| Capability                          | Recommendation System | Allocation-Only Engine | StuSkillLink |
| ------------------------------------ | ---------------------: | -----------------------: | ------------: |
| Recommend roles                      |                      ✅ |                        ✅ |            ✅ |
| Match skills                         |                      ✅ |                        ✅ |            ✅ |
| Skill-gap analysis before applying   |                      ❌ |                        ❌ |            ✅ |
| Communication assessment (LSRW)      |                      ❌ |                        ❌ |            ✅ |
| Rank candidates (tiered)             |                     🟡 |                        ✅ |            ✅ |
| Allocate seats                       |                      ❌ |                        ✅ |            ✅ |
| Multi-seat progressive fill          |                      ❌ |                        ✅ |            ✅ |
| Automatic backfill                   |                      ❌ |                        ✅ |            ✅ |
| Placement continuity                 |                      ❌ |                        ❌ |            ✅ |
| Verified digital portfolio           |                      ❌ |                        ❌ |            ✅ |
| Academician opportunity matching     |                      ❌ |                        ❌ |            ✅ |
| Curriculum co-design (Acad + Industry) |                    ❌ |                        ❌ |            ✅ |
| Institution-level analytics          |                      ❌ |                        ❌ |            ✅ |
| Explainable decisions                |                     🟡 |                       🟡 |            ✅ |
| Human escalation                     |                     🟡 |                       🟡 |            ✅ |
| Continuous, self-correcting loop     |                      ❌ |                       🟡 |           🔥 |

### Core distinction

> **Recommendation tells someone where they could apply.**
> **Allocation determines who gets the seat.**
> **StuSkillLink does both — for students *and* academicians — and feeds every outcome back into curriculum and institutional policy.**

---

# 🌍 Sustainable Development Goals

### 🥇 SDG 8 — Decent Work and Economic Growth
Better skill-matched placement, plus new skilled roles the platform itself creates (skill-gap rubric analysts, LSRW content designers, fairness reviewers, academic-industry liaison coordinators).

### 🥈 SDG 4 — Quality Education
Closes the loop between classroom curriculum and actual industry demand, for the first time at scale.

---

# 💻 Technology Stack

| Layer                     | Technology                                                                 |
| -------------------------- | --------------------------------------------------------------------------- |
| Frontend                   | React 19, Tailwind CSS, Vite, React Query                                  |
| Backend                    | Python, FastAPI, Pydantic, Celery + Redis                                  |
| **AI/ML & Agentic AI**      | gpt-oss-120B (Groq/vLLM), BGE/Sentence-BERT, spaCy, LangChain, LangGraph, MCP, 7 Specialized Agents |
| Speech & Language          | Whisper Large-v3, Kokoro-82M, Embedding-based Grading                     |
| Database & Optimisation    | Neon PostgreSQL, Supabase, Google OR-Tools (CP-SAT)                       |
| Deployment                 | Vercel & Render                                                            |
| Scalability                | AWS (EC2, S3, RDS), Kubernetes                                            |
| Security                   | OAuth 2.0, JWT, bcrypt, Cloudflare                                        |
| MCP Server Connections     | Twilio, NPTEL, Coursera, Udemy and other online platforms, Bhashini API, GitHub MCP |
| Credentialing               | W3C Verifiable Credentials, Open Badges 3.0                               |

---

# 📁 Proposed Project Structure

```text
StuSkillLink/
│
├── backend/
│   ├── agents/
│   │   ├── intake_eligibility_agent.py
│   │   ├── skill_communication_agent.py
│   │   ├── portfolio_preference_agent.py
│   │   ├── matching_allocation_agent.py
│   │   ├── academician_engagement_agent.py
│   │   ├── monitoring_escalation_agent.py
│   │   └── curriculum_framing_agent.py
│   │
│   ├── services/
│   │   ├── matching.py
│   │   ├── optimization.py
│   │   ├── eligibility.py
│   │   ├── lsrw_scoring.py
│   │   ├── portfolio_builder.py
│   │   ├── curriculum_clustering.py
│   │   └── notifications.py
│   │
│   ├── models/
│   ├── routes/
│   ├── database/
│   └── main.py
│
├── frontend/
│   ├── components/
│   ├── pages/
│   │   ├── student/
│   │   ├── academician/
│   │   ├── industry/
│   │   └── institution/
│   ├── services/
│   └── app/
│
├── data/
│   ├── students/
│   ├── academicians/
│   ├── companies/
│   ├── institutions/
│   └── roles/
│
├── tests/
├── docs/
├── requirements.txt
├── .env.example
└── README.md
```

---

# 🚀 Workflow

### Step 1 — Registration (Four Flows in Parallel)
Students create profiles with transcripts and preferences; academicians register courses and research interests; industries publish roles, learning programs, and opportunities; institutions register policies, NOC templates, and departments.

### Step 2 — Eligibility Verification
The Intake & Eligibility Agent validates scheme-level eligibility and NOC status against the Institution Module.

### Step 3 — Skill-Gap & Communication Assessment
The Skill & Communication Intelligence Agent produces the Skill-Gap Report and LSRW score.

### Step 4 — Curriculum Framing
The Curriculum Framing Agent clusters batch-wide skill weaknesses from that skill-gap data (plus industry input) into NOS-mapped syllabus recommendations, routed through a joint academician + industry sign-off before adoption.

### Step 5 — Portfolio & Preference Capture
The Portfolio & Preference Agent builds the verified digital portfolio and captures ranked industry preferences.

### Step 6 — Ranking
The Matching & Allocation Agent creates a tiered candidate list for every role, including reservation-category handling.

### Step 7 — Allocation
Seats are offered to the highest-priority eligible candidates, preferred partners first, general pool only on opt-in.

### Step 8 — Academician Opportunity Matching (Parallel Track)
The Academician Engagement Agent curates and matches academicians to FDPs, consultancy, research, and collaboration opportunities using the same ranking logic.

### Step 9 — Observe
The system observes: Accepted, Declined, Pending, Screening Passed, Screening Failed.

### Step 10 — Reallocation
Vacant seats or opportunities move automatically to the next eligible candidate.

### Step 11 — Completion & Continuity
Filled seats trigger placement-continuity checks; all outcomes feed back into the Skill & Communication Intelligence Agent, the Curriculum Framing Agent, and the Institution Analytics Dashboard.

---

# 📈 Expected Impact

StuSkillLink aims to:

* Give students visibility into their own skill gaps before they apply
* Give academicians both curriculum insight and their own industry opportunities
* Give institutions an aggregated, real-time analytics view
* Reduce manual allocation workload for industry
* Automatically backfill vacant seats and opportunities
* Improve transparency of ranking and reservation-category decisions
* Build a verified, trustworthy student portfolio over time
* Support large-scale, multi-institution rollout

---

# ⚠️ Limitations

The prototype may initially rely on:

* Synthetic student, academician, and institution datasets
* Synthetic company/role and opportunity datasets
* Simulated allocation cycles
* Configurable policy assumptions

Real-world deployment would require:

* Institutional data-sharing agreements (curriculum, NOC records)
* Government/AICTE-approved policies
* Security and privacy controls
* Verified candidate and academician data
* Policy-compliant quota/reservation logic
* Large-scale infrastructure
* Extensive fairness testing, particularly for LSRW scoring

---

# 🔮 Future Scope

### Phase 1 — Core Profiles & Eligibility
Student, academician, industry, and institution profiles with NOC verification.

### Phase 2 — Skill Intelligence
Skill-gap analysis and LSRW communication assessment.

### Phase 3 — Curriculum Framing
Batch-wide skill-gap clustering into NOS-mapped syllabus recommendations, with academician + industry sign-off workflow.

### Phase 4 — Portfolio & Preference Layer
Verified digital portfolio and preference-aware matching.

### Phase 5 — Tiered Ranking & Optimization
Reservation-category-aware, multi-factor ranking engine.

### Phase 6 — Agentic Allocation
Multi-seat allocation, automatic reallocation, and placement continuity.

### Phase 7 — Academician & Institution Layer
Academician opportunity matching and institution-wide analytics.

### Phase 8 — Scalable, Multi-Institution Integration
Extension beyond a single institution to scholarships, skilling programs, and government opportunities more broadly.

---

# 🏆 What Makes StuSkillLink Different?

### 01 — Automated Internship Platform
End-to-end posting, matching, and allotment — no manual shortlisting.

### 02 — Curriculum Agent
Converts skill gaps into academia–industry syllabus updates, not just a dashboard metric.

### 03 — Auditable Ranking
Transparent student and academician ranking, with reservation handling and deterministic tie-breaking, extended to FDP/research/consultancy opportunities.

### 04 — Skill-First Allocation
Assesses skills, aptitude, and LSRW before allocation — not resume keywords after the fact.

### 05 — Preference Allocation
Prioritizes preferred companies first, general pool only on student opt-in.

### 06 — Verified Credentials
Credentials earned through industry-led learning are issued and verified, not self-declared.

---

# 📌 Project Vision

> **To build an intelligent, transparent, and continuously self-correcting ecosystem where every student's skill gap is visible before they apply, every academician's expertise stays connected to industry, and every institution can see — in real time — how its people are actually doing.**

---

# 👨‍💻 Team

**StuSkillLink**

Built for **Smart India Hackathon 2026 — SIH26044**
**Theme:** Smart Automation
**Team Name:** CodeRhythm (KITSIH26-S120)

## Authors

- **Aswin N**
- **Sanjay D**
- **Aishwarya S**
- **Mohammed Sohail**
- **Nihal Hussain**
- **Harshitha M B**

Rights belong to the authors.

---

# ⭐ Core Statement

> ### **We don't just recommend internships.**
> ### **We map the skill gap, close it, allocate the seat, and keep academia and industry in sync — continuously.**

**StuSkillLink — Right Student. Right Skill. Right Internship. Deserving Opportunity.**
