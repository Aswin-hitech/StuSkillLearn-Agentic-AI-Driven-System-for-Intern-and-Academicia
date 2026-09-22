# StuSkillLink Architecture

## Runtime topology

```text
Browser
  |
  | HTTPS / same-origin HttpOnly cookies
  v
React 19 + Tailwind frontend
  |
  | /api/v1 reverse proxy
  v
FastAPI application
  |
  +--> Authentication / rotating refresh sessions / RBAC
  +--> Admin control plane
  +--> Tenant-scoped Student / Company / Academician / Institution APIs
  +--> Seven-agent orchestration boundary
  +--> Multi-provider LLM gateway
  +--> Notification / integration adapters
  |
  +---------------------------+
  |                           |
  v                           v
PostgreSQL                 Redis
transactional data         rate limits / Celery broker & result backend
  |
  +--> Alembic migrations
  +--> users / tenants / opportunities / applications
  +--> rankings / allocations / snapshots / audit
  +--> credentials / agent-run results / curriculum insight history

Celery worker / beat
  +--> asynchronous notification and operational tasks

Optional external adapters
  +--> SMTP
  +--> Twilio
  +--> MongoDB audit-event mirror
  +--> NVIDIA NIM / Groq / Gemini / OpenRouter
```

Development can run directly on SQLite for a lightweight local process, but the Docker development topology and all supported production deployments use PostgreSQL. Production settings fail closed if SQLite is configured.

## Five workspace model

The four ecosystem participants remain separated by tenant and role boundaries:

- **Student** — owns personal learning/readiness/application data.
- **Company** — manages only its organization profile, opportunities, candidates authorized through applications, allocations and engagement feedback.
- **Academician** — owns faculty profile and institution-scoped engagement/curriculum data.
- **Institution** — sees only students/academicians assigned to its verified tenant.
- **Admin** — is the global control plane. Admin is intentionally not a public registration role.

The Admin portal controls organization verification, account activation, tenant assignment, opportunity moderation, reservation evidence/policy governance, credential verification, allocation oversight, global audit, agent operations and platform health.

## Seven agents

1. **Intake & Eligibility Agent** — profile readiness, prerequisites and trusted eligibility facts.
2. **Skill & Communication Intelligence Agent** — structured skill gaps and LSRW/readiness evidence.
3. **Portfolio & Preference Agent** — projects, credentials and explicit student preference signals.
4. **Matching & Allocation Agent** — deterministic match evidence, ranking and allocation state.
5. **Academician Engagement Agent** — FDP/research/consultancy and academia-industry engagement signals.
6. **Monitoring, Notification & Escalation Agent** — offer/engagement lifecycle, reallocation and operational follow-up.
7. **Curriculum Framing Agent** — converts aggregate demand, gaps and outcome feedback into curriculum insight records.

`app/agent_graph.py` executes seven deterministic domain stages and then produces advisory natural-language reasoning. Agent outputs are stored with status/provenance and visible through role-scoped activity feeds; Admin has global oversight.

### Decision boundary

```text
Untrusted / probabilistic layer
  resume interpretation enhancements
  learning explanations
  evidence-grounded agent explanations
  optional provider reasoning

                 DOES NOT AWARD SEATS
                         |
                         v
Trusted deterministic layer
  eligibility
  score components
  tier assignment
  tie-breaking
  policy constraints
  seat accounting
  allocation/reallocation
  engagement lifecycle rules
                         |
                         v
Audited relational records
```

The LLM gateway can fail completely without changing deterministic allocation semantics.

## Multi-provider LLM gateway

Provider priority is configurable. The default order is:

```text
NVIDIA NIM → Groq → Gemini → OpenRouter
```

The gateway records provider/model attempts and switches to deterministic explanation when no live provider succeeds. Model configuration is exposed operationally; the current implementation does not claim that every provider supports identical live model-discovery semantics.

## Matching and allocation

The matching engine stores structured score components and an eligibility result. Company ranking is generated from eligible applications only and deterministic tie-breaking is used.

Allocation is guarded by:

- opportunity lifecycle and deadline checks
- administrative moderation
- verified organization status
- approved policy constraints
- database uniqueness constraints
- PostgreSQL row locks for seat accounting
- immutable decision snapshot data
- algorithm and policy version identifiers

Reservation evidence is verified outside the recruiter flow and hidden from recruiter-facing candidate serialization. If a deployment policy permits reserved-seat conversion, the conversion is represented explicitly in the allocation audit rather than silently preserving a misleading category slot.

## Opportunity and engagement lifecycle

Company opportunities move through governed states such as draft/review/open/closed rather than becoming public immediately after company creation. Unverified companies cannot publish operational opportunities.

Allocation/engagement state is also explicit:

```text
OFFERED → ACCEPTED → IN_PROGRESS → COMPLETED
       \→ REJECTED → deterministic reallocation
```

Company outcome feedback is accepted only after a completed engagement.

## Credential lifecycle

```text
learning/program completion
        |
        v
PENDING_VERIFICATION credential evidence
        |
        v
Admin evidence review
   |             |
 VERIFIED      REJECTED
```

A student action does not create a trusted verified credential by itself.

## Curriculum intelligence

Curriculum refreshes are explicit mutation operations rather than side effects of GET requests. Insight history is retained per generation run rather than deleting the previous dataset. This keeps evidence reconstructable over time.

## Authentication and browser session model

- bcrypt is the production password hash; legacy PBKDF2 hashes can be verified and migrated.
- access sessions are short lived.
- refresh sessions are rotated and can be revoked.
- browser tokens are held in HttpOnly cookies, not browser storage.
- cookie-authenticated state-changing requests require a trusted browser Origin in production.
- organization and email verification gates are separate from simple authentication.
- Admin is provisioned through a server-side CLI, not self-registration.

## Data tenancy

Student and academician profiles carry an institution tenant relationship. Company-owned data carries a company relationship. Every organization-scoped read/write path must bind the authenticated principal to that tenant before returning or mutating records.

Global audit and global agent activity are Admin-only; ordinary workspace feeds are scoped to the caller's authorized data.

## Background processing

Celery and Redis are included in the production topology. They are intended for operations that should not block interactive HTTP requests, especially notifications and longer-running operational tasks. Deterministic ranking/allocation remains transactional in the API/domain layer.

## Deployment model

Production uses:

- PostgreSQL
- Redis
- Alembic migrations
- FastAPI application container
- Celery worker and beat containers
- React static frontend behind Nginx
- same-origin `/api/` reverse proxy
- non-root containers and dropped Linux capabilities where configured
- read-only backend filesystems with writable `/tmp`

`/health` is a liveness endpoint. `/ready` verifies database connectivity and, in production, Redis availability and Alembic revision presence.

## External/target capabilities from the SIH deck

The presentation proposes a broader future stack including Whisper, Kokoro, embeddings/BGE, OR-Tools CP-SAT, MCP connectors and W3C/Open Badges credential standards. The current source should be judged by `PPT_COVERAGE_MATRIX.md`: those entries are not automatically considered implemented merely because they appear in the deck.
