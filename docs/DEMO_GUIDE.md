# SIH Demo Guide

The seeded demo is enabled only in a development/demo environment with `AUTO_SEED_DEMO=true`; set `VITE_SHOW_DEMO_ACCOUNTS=true` to expose the one-click demo login controls. Production Compose forces the demo-login UI off. All seeded accounts use password `Demo@123`.

## 0. Admin — establish governance first

Login: `admin@stuskilllink.demo`

Show this first so judges understand that StuSkillLink is a governed multi-tenant platform, not four disconnected dashboards.

1. **Command center** — platform account counts, pending organizations/opportunities, allocations and operational health.
2. **Users & tenancy** — institution assignment and protected reservation-evidence workflow.
3. **Organizations** — approve/reject/suspend companies and institutions.
4. **Opportunity moderation** — explain why a recruiter cannot directly control protected allocation policy.
5. **Policy & credentials** — show versioned allocation policy and pending credential evidence.
6. **Audit & allocations** — show request IDs, algorithm version, policy version, rank/round and slot evidence.
7. **AI & operations** — provider/integration health and seven-agent executions.

Key line: **Admin controls the platform; AI never bypasses policy or deterministic allocation rules.**

## 1. Student — prove readiness intelligence

Login: `student@stuskilllink.demo`

Show in this order:

1. Overview: readiness, LSRW, skill gaps and strongest matches.
2. Profile & Resume: upload TXT/PDF/DOCX and map skills.
3. Preferences: domains, locations/work modes, explicit role ordering and general-pool opt-in.
4. LSRW: listening, speaking, reading and writing readiness.
5. Learning: complete a recommendation or industry program.
6. Portfolio: show that new completion evidence is **pending verification** until approved by the governance layer.
7. Opportunities: open a role and explain matched skills, missing skills and score evidence.
8. Offers: rank, allocation round, slot/policy evidence and offer lifecycle.

## 2. Company — prove controlled, explainable allocation

Login: `industry@stuskilllink.demo`

Show:

1. Verified organization status.
2. Submit an internship or placement role.
3. Explain that the role enters moderation before becoming an approved open opportunity.
4. Open the company-wise rank list.
5. Explain visible score components, fit tier and deterministic tie-break order.
6. Allocate seats through the governed allocator.
7. Move an accepted engagement through `IN_PROGRESS` to `COMPLETED` before feedback is permitted.
8. Publish industry-led learning content.

Important privacy point: recruiter candidate output does not expose protected reservation-category evidence.

## 3. Student again — prove rejection and reallocation

Open Student → Offers and reject an `OFFERED` allocation. Return to Company → Allocation & Feedback and show the next eligible ranked candidate receiving a later allocation round.

Explain that seat accounting and reallocation are deterministic and audited.

## 4. Academician — prove faculty engagement

Login: `academician@stuskilllink.demo`

Show expertise matching for FDP, research and consultancy opportunities plus curriculum signals derived from hiring demand and student gaps.

## 5. Institution — prove tenant isolation and closed-loop curriculum

Login: `institution@stuskilllink.demo`

Show:

- only institution-assigned students
- cohort readiness and average LSRW
- current skill supply/gaps
- protected reservation-evidence administration for its own students
- curriculum insight history/actions
- academician opportunities

Explain that a newly registered institution sees no other institution's students until Admin establishes the tenant relationship.

## 6. Seven-agent activity — explain AI boundaries

Open Agent Activity in an authorized workspace or Admin → AI & Operations.

Explain the seven stages:

1. Intake & Eligibility
2. Skill & Communication Intelligence
3. Portfolio & Preference
4. Matching & Allocation
5. Academician Engagement
6. Monitoring, Notification & Escalation
7. Curriculum Framing

Key line: **Each agent starts from deterministic evidence. LLM reasoning is an explanation/assistance layer; seat decisions remain deterministic.**

## 7. Production-readiness talking points

If judges ask what changed beyond a prototype:

- Admin cannot self-register.
- companies/institutions require verification.
- cross-tenant reads are blocked.
- browser auth uses HttpOnly cookies and rotating refresh sessions.
- reservation evidence is protected and recruiter views hide it.
- expired opportunities reject applications.
- feedback requires completed engagement.
- credential completion is pending until verification.
- PostgreSQL row locking and uniqueness constraints protect allocation seat accounting.
- allocation records snapshot decision/policy versions.
- Alembic, Redis/Celery, readiness probes, hardened Docker/Compose and CI are included.

## Judge-friendly one-line architecture

**Governed identity → skill & communication readiness → learning evidence → preference-aware deterministic ranking → explainable allocation/reallocation → verified outcomes → placement continuity → curriculum framing.**
