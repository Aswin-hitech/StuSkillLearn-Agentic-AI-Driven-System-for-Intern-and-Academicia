# 🚀 PM–StuNTERN

### **Agentic AI-Based Internship Allotment Engine**

> **The Right Student. The Right Internship. The Right Opportunity.**

**PM–StuNTERN** is an Agentic AI-powered internship allotment and allocation engine designed for the **PM Internship Scheme (PMIS)**. Instead of stopping at internship recommendation or candidate shortlisting, StuNTERN continuously manages the **ranking → allotment → acceptance → screening → reallocation** lifecycle.

The goal is simple:

> **Deserving Allotment for Deserving Students.**

---

## 🏛️ Smart India Hackathon

| Field                 | Details                       |
| --------------------- | ----------------------------- |
| **Problem Statement** | SIH25033                      |
| **Ministry**          | Ministry of Corporate Affairs |
| **Theme**             | Smart Automation              |
| **Project**           | PM–StuNTERN                   |
| **Category**          | Agentic AI / Smart Automation |

---

# 🎯 The Problem

India has a massive pool of students looking for meaningful industry exposure, while companies participating in government internship programmes have internship seats that need to be filled with suitable candidates.

The challenge isn't simply **finding an internship**.

The real challenge is **efficiently and continuously allocating the right candidate to the right available seat**.

Consider a simple scenario:

A company has **6 Applied AI internship seats**.

Hundreds of eligible students apply.

The system identifies suitable candidates.

One candidate receives an offer but declines.

Another candidate accepts but fails screening.

Now seats become vacant again.

Without an adaptive allocation mechanism, these vacancies can require additional manual intervention while other eligible candidates remain available in the candidate pool.

At national scale, repeatedly handling these decisions becomes a complex allocation problem.

---

# 💡 Our Solution

**PM–StuNTERN** introduces an Agentic AI-based allocation layer that continuously manages the internship allocation process.

Instead of:

```text
Student → Apply → Wait → Selection
```

StuNTERN follows:

```text
Profile
   ↓
Eligibility Verification
   ↓
Candidate Profiling
   ↓
Intelligent Ranking
   ↓
Seat Allocation
   ↓
Candidate Response
   ↓
Screening Outcome
   ↓
Observe
   ↓
Reallocate if Required
   ↓
Seat Filled
```

The system continues this process until available seats are filled or the allocation cycle reaches its defined boundary.

---

# 🤖 Why Agentic AI?

A conventional AI model may simply answer:

> "Which internship is suitable for this student?"

StuNTERN goes further.

The system can:

* **Observe** candidate and seat states
* **Rank** eligible candidates
* **Allocate** available seats
* **Monitor** acceptance/decline outcomes
* **React** to screening results
* **Reallocate** vacant seats
* **Escalate** unresolved cases to human administrators

### Agentic Loop

```text
       ┌──────────────┐
       │    RANK      │
       └──────┬───────┘
              ↓
       ┌──────────────┐
       │   ALLOCATE   │
       └──────┬───────┘
              ↓
       ┌──────────────┐
       │    OBSERVE   │
       └──────┬───────┘
              ↓
       ┌──────────────┐
       │   DECIDE     │
       └──────┬───────┘
              ↓
       ┌──────────────┐
       │  REALLOCATE  │
       └──────┬───────┘
              │
              └──────────────→ Repeat
```

This creates a **closed-loop allocation system** rather than a one-time recommendation engine.

---

# 🧠 Core Features

## 1. Student Profiling Agent

Processes student information such as:

* Skills
* Certifications
* Projects
* Experience
* Domain preferences
* Location preferences
* Paid / unpaid preferences
* Resume
* Eligibility information

The agent converts unstructured information into a structured candidate profile.

---

## 2. Eligibility Gate

Eligibility is verified before a candidate enters the ranking pipeline.

For final-year students, the system can verify the presence of a valid **No Objection Certificate (NOC)** before the candidate proceeds to ranking.

```text
Student Profile
      ↓
Eligibility Check
      ↓
 ┌───────────────┐
 │ Eligible?     │
 └───────┬───────┘
     YES ↓       ↓ NO
    Ranking    Rejected /
                Pending
```

---

# 🏆 3. Tiered Candidate Ranking

StuNTERN does not rely on a single flat score.

Candidates are organized into priority tiers based on their fit and flexibility.

### Tier 1 — Best Fit + Flexible

Strong skill/project match with flexibility across eligible locations.

### Tier 2 — Best Fit + Limited Flexibility

Strong candidate but restricted to selected locations.

### Tier 3 — Remote / Virtual Only

Qualified candidates restricted to virtual opportunities.

Within each tier, candidates are further ranked using factors such as:

* Skill match
* Project relevance
* Certifications
* Experience
* Role requirements

This allows **flexibility and merit to work together rather than treating location as only a simple filter.**

---

# 🎯 4. Multi-Seat Progressive Allocation

StuNTERN is designed for roles with multiple internship seats.

### Example

```text
Applied AI Intern
Seats Available: 6
```

The Allocation Agent works through the ranked candidate pool.

```text
Candidate 01 → Offer → Accepted ✅
Candidate 02 → Offer → Declined ❌
                         ↓
Candidate 03 → Offer → Accepted ✅
Candidate 04 → Offer → Screening Failed ❌
                         ↓
Candidate 05 → Offer → Accepted ✅
...
```

The system continues until:

```text
6 / 6 Seats Filled
```

Once all seats are filled, the vacancy is automatically closed.

---

# 🔄 5. Automatic Reallocation

A declined offer or failed screening does **not** terminate the allocation process.

Instead:

```text
Seat Vacant
     ↓
Find Next Eligible Candidate
     ↓
Ranked Candidate
     ↓
Offer
     ↓
Observe Response
     ↓
Accept ───────→ Continue Screening
     │
     └─ Decline → Next Candidate
```

This is one of the core differentiators of PM–StuNTERN.

---

# ✉️ 6. AI-Powered Communication

The LLM is used as a communication and explainability layer.

It can generate:

* Internship offer letters
* Interview process information
* HR contact information
* Candidate allocation explanations
* Human-readable ranking explanations

The LLM is therefore not responsible for making every allocation decision.

Instead, **deterministic eligibility and allocation logic handles critical decisions**, while AI supports understanding, semantic matching and communication.

---

# 🔍 7. Explainable Allocation

A candidate should not simply receive:

> "You were ranked #17."

StuNTERN can provide an explanation such as:

```text
Ranking Explanation

Skill Match:       92%
Project Relevance: 88%
Experience:        80%
Location Fit:      Tier 1

Overall:
Highly suitable candidate for the role.
```

This improves transparency and can support grievance handling.

---

# 👥 8. Human-in-the-Loop

Automation does not mean removing humans completely.

Administrators can intervene in situations such as:

* Unresolved candidate responses
* Exceptional cases
* Eligibility disputes
* Allocation overrides
* Escalations
* Policy-related decisions

```text
             AI Allocation
                   ↓
          ┌────────┴────────┐
          ↓                 ↓
      Normal Case      Exception
          ↓                 ↓
     Auto Process      Human Review
```

---

# 🏗️ System Architecture

```text
┌──────────────────────────────────────────────────────────┐
│                     PM–StuNTERN                          │
│              Agentic AI Allocation Engine               │
└──────────────────────────────────────────────────────────┘

          ┌──────────────┐     ┌──────────────┐
          │   Students   │     │   Companies  │
          └──────┬───────┘     └──────┬───────┘
                 │                    │
                 └─────────┬──────────┘
                           ↓
                 ┌───────────────────┐
                 │ Data Ingestion    │
                 └─────────┬─────────┘
                           ↓
                 ┌───────────────────┐
                 │ Profiling Agent   │
                 └─────────┬─────────┘
                           ↓
                 ┌───────────────────┐
                 │ Eligibility Gate  │
                 └─────────┬─────────┘
                           ↓
                 ┌───────────────────┐
                 │ Ranking Agent     │
                 └─────────┬─────────┘
                           ↓
                 ┌───────────────────┐
                 │ Allocation Agent  │
                 └─────────┬─────────┘
                           ↓
                 ┌───────────────────┐
                 │ Candidate / HR    │
                 │ Interaction      │
                 └─────────┬─────────┘
                           ↓
                 ┌───────────────────┐
                 │ Outcome Observer  │
                 └─────────┬─────────┘
                           ↓
                 ┌───────────────────┐
                 │ Reallocation      │
                 │ Engine            │
                 └─────────┬─────────┘
                           │
                    ┌──────┴──────┐
                    ↓             ↓
                 Filled        Escalation
                  Seat         → Admin
```

---

# 🧩 Agent Architecture

PM–StuNTERN uses multiple specialized agents.

| Agent                  | Responsibility                                             |
| ---------------------- | ---------------------------------------------------------- |
| **Profiling Agent**    | Resume parsing, skill extraction and profile normalization |
| **Ranking Agent**      | Candidate-role ranking and tier generation                 |
| **Allocation Agent**   | Seat allocation, acceptance and reallocation               |
| **Notification Agent** | Offer letters, interview information and notifications     |
| **Escalation Layer**   | Sends unresolved cases to human administrators             |

The agents work together as a closed-loop system.

---

# 🧮 Allocation Logic

A candidate's position is determined using multiple factors rather than a single academic score.

Conceptually:

```text
Candidate Priority
        =
Eligibility
      +
Skill Match
      +
Project Relevance
      +
Experience
      +
Location / Flexibility
      +
Role Compatibility
```

The exact weights can be configured according to scheme and policy requirements.

For large-scale optimization, the system can use optimization techniques such as:

* Weighted scoring
* Constraint-based matching
* OR-Tools
* Hungarian algorithm

---

# 🗃️ Data Model

## Student

```text
Student
├── Student ID
├── Personal Information
├── Age / DOB
├── Education
├── Skills
├── Certifications
├── Projects
├── Experience
├── Resume
├── Domain Preference
├── Location Preference
├── Work Mode Preference
└── Eligibility / NOC
```

## Company / Role

```text
Company
├── Company ID
├── Role
├── Job Description
├── Required Skills
├── Required Projects
├── Required Certifications
├── Location
├── Work Mode
├── Duration
└── Seats Available
```

## Match Record

```text
Match
├── Student ID
├── Role ID
├── Tier
├── Rank Score
├── Allocation Status
├── Offer Status
├── Screening Status
├── HR Contact
└── Interview Details
```

---

# 🔐 Fairness & Transparency

Because internship allocation affects real students, fairness is a core design requirement.

StuNTERN should maintain:

* Explicit eligibility rules
* Explainable ranking
* Auditable allocation decisions
* Configurable scoring
* Human override capability
* Policy-aware constraints
* Allocation logs

The system should **not allow an opaque LLM response to directly determine a student's eligibility or final allocation without controlled rules and validation.**

---

# 📊 Example

### Student

**Ram**

Skills:

```text
Python
Machine Learning
NLP
Generative AI
```

Projects:

```text
3 AI/ML Projects
```

Preferences:

```text
Chennai
Bangalore
Hyderabad
Kochi
```

Eligibility:

```text
NOC Verified ✅
```

### Company

```text
Role: Applied AI Intern
Location: Hyderabad
Seats: 6
```

### Result

Ram receives:

```text
Tier: 1
Skill Match: High
Project Relevance: High
Location Flexibility: High
```

He is allotted a seat.

If he accepts:

```text
Offer → Screening
```

If he passes:

```text
Seat → FILLED
```

If he declines or fails:

```text
Seat → REOPENED
       ↓
Next Ranked Candidate
```

The system continues automatically.

---

# 🆚 Recommendation vs Allocation

| Capability                  | Recommendation System | PM–StuNTERN |
| --------------------------- | --------------------: | ----------: |
| Recommend roles             |                     ✅ |           ✅ |
| Match skills                |                     ✅ |           ✅ |
| Rank candidates             |                    🟡 |           ✅ |
| Allocate seats              |                     ❌ |           ✅ |
| Monitor acceptance          |                     ❌ |           ✅ |
| Handle rejection            |                     ❌ |           ✅ |
| Automatic backfill          |                     ❌ |           ✅ |
| Multi-seat progressive fill |                     ❌ |           ✅ |
| Explain allocation          |                    🟡 |           ✅ |
| Human escalation            |                    🟡 |           ✅ |
| Continuous allocation loop  |                     ❌ |          🔥 |

### Core distinction

> **Recommendation tells a student where they could apply.**
>
> **Allocation determines who gets the available seat and continuously manages what happens next.**

---

# 🌍 Sustainable Development Goals

### 🥇 SDG 8 — Decent Work and Economic Growth

PM–StuNTERN supports youth access to employment-oriented opportunities and industry experience.

### 🥈 SDG 4 — Quality Education

The platform helps bridge the gap between academic learning and industry-relevant skills.

### 🥉 SDG 10 — Reduced Inequalities

Explainable and rule-based allocation can help make access to opportunities more transparent and less dependent on informal networks.

---

# 💻 Technology Stack

| Layer             | Technology                     |
| ----------------- | ------------------------------ |
| Backend           | Python / FastAPI / Flask       |
| Frontend          | React                          |
| Database          | PostgreSQL                     |
| AI / LLM          | LLM API                        |
| Semantic Matching | Embeddings                     |
| Optimization      | OR-Tools / Hungarian Algorithm |
| Resume Processing | Document / Resume Parser       |
| Notifications     | Email / SMS APIs               |
| Deployment        | Cloud Infrastructure           |

---

# 📁 Proposed Project Structure

```text
PM-StuNTERN/
│
├── backend/
│   ├── agents/
│   │   ├── profiling_agent.py
│   │   ├── ranking_agent.py
│   │   ├── allocation_agent.py
│   │   └── notification_agent.py
│   │
│   ├── services/
│   │   ├── matching.py
│   │   ├── optimization.py
│   │   ├── eligibility.py
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
│   ├── services/
│   └── app/
│
├── data/
│   ├── students/
│   ├── companies/
│   └── roles/
│
├── tests/
│
├── docs/
│
├── requirements.txt
├── .env.example
└── README.md
```

---

# 🚀 Workflow

### Step 1 — Student Registration

Student creates a profile and submits relevant information.

### Step 2 — Company Registration

Company submits internship roles and seat requirements.

### Step 3 — Eligibility Verification

The system validates scheme-level eligibility and required documents.

### Step 4 — Candidate Profiling

The Profiling Agent extracts and structures skills, projects and experience.

### Step 5 — Ranking

The Ranking Agent creates a tiered candidate list for every role.

### Step 6 — Allocation

The Allocation Agent offers seats to the highest-priority eligible candidates.

### Step 7 — Observe

The system observes:

```text
Accepted
Declined
Pending
Screening Passed
Screening Failed
```

### Step 8 — Reallocation

If a seat becomes vacant, the system automatically moves to the next eligible candidate.

### Step 9 — Completion

Once all seats are filled:

```text
Role Status = FILLED
```

---

# 📈 Expected Impact

PM–StuNTERN aims to:

* Reduce manual allocation workload
* Improve candidate-role matching
* Reduce delays caused by declined offers
* Automatically backfill vacant seats
* Improve transparency of candidate ranking
* Provide explainable allocation decisions
* Improve utilization of available internship seats
* Support large-scale internship allocation

---

# ⚠️ Limitations

The prototype may initially rely on:

* Synthetic student datasets
* Synthetic company/role datasets
* Simulated allocation cycles
* Configurable policy assumptions

Real-world deployment would require:

* Official PMIS integration
* Government-approved policies
* Security and privacy controls
* Verified candidate data
* Policy-compliant quota/eligibility logic
* Large-scale infrastructure
* Extensive fairness testing

---

# 🔮 Future Scope

### Phase 1

Core student/company profiles and eligibility.

### Phase 2

AI-based profiling and semantic skill matching.

### Phase 3

Tiered ranking and optimization engine.

### Phase 4

Agentic allocation and automatic reallocation.

### Phase 5

Explainability, analytics and human escalation.

### Phase 6

Scalable government-system integration.

The architecture can also be extended beyond internships to other large-scale allocation problems such as scholarships, skilling programmes and government opportunities.

---

# 🏆 What Makes PM–StuNTERN Different?

### 01 — Allocation, Not Just Recommendation

The system doesn't stop after suggesting an internship.

### 02 — Agentic Decision Loop

**Rank → Allocate → Observe → Reallocate**

### 03 — Multi-Seat Allocation

A six-seat role is progressively filled rather than treated as a single allocation event.

### 04 — Automatic Vacancy Backfill

A declined or failed candidate does not leave the process stalled.

### 05 — Explainable AI

Candidates and administrators can understand why a candidate was ranked in a particular position.

### 06 — Human-in-the-Loop

Exceptional cases can always be escalated to administrators.

---

# 📌 Project Vision

> **To build an intelligent, transparent and adaptive internship allocation ecosystem where every available opportunity can reach the most suitable eligible student — without leaving seats unnecessarily vacant.**

---

# 👨‍💻 Team

**PM–StuNTERN**

Built for **Smart India Hackathon — SIH25033**

**Theme:** Smart Automation

---

# ⭐ Core Statement

> ### **We don't just recommend internships.**
>
> ### **We continuously allocate them.**

**PM–StuNTERN — The Right Student. The Right Internship. The Right Opportunity.**

## Authors

## Authors

- **Aswin N**
- **Sanjay D**
- **Aishwarya S**
- **Mohammed Sohail**
- **Mohammed Nihal**
- **Harshitha M B**

Rights Belong to us.
