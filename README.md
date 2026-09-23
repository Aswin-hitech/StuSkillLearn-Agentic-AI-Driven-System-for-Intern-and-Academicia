# StuSkillLink — SIH26044

**An Agentic AI-Based Portal for Academia–Industry Collaboration**  
CodeRhythm · Smart India Hackathon 2026  
**Right Student. Right Skill. Right Internship. Deserving Opportunity.**

StuSkillLink connects students, companies, academicians and institutions through one governed platform. A fifth workspace — **Admin Command Center** — operates as the platform control plane for organization approval, tenancy, policy, moderation, credentials, audit and operational oversight.

The implemented loop is:

**profile/resume → skill & communication readiness → skill gaps → learning → credential evidence → preference-aware matching → deterministic ranking → governed allocation/reallocation → engagement feedback → placement continuity → curriculum insight**

LLMs enrich explanations and learning guidance. They do **not** award seats or alter deterministic eligibility, ranking, tie-breaking or allocation decisions.

## Workspaces

| Workspace | Primary responsibility |
|---|---|
| Student | Profile, resume, preferences, LSRW, skill gaps, learning, portfolio, applications and offers |
| Company | Opportunity submission, rank lists, allocations, engagement lifecycle, feedback and industry learning |
| Academician | Expertise profile, FDP/research/consultancy matching and curriculum signals |
| Institution | Tenant-scoped student readiness, reservation evidence, curriculum insights and academician opportunities |
| Admin | Global governance: users, tenants, organization verification, opportunity moderation, policy, credentials, allocations, agents, audit and platform health |

## Seven-agent orchestration

1. Intake & Eligibility Agent
2. Skill & Communication Intelligence Agent
3. Portfolio & Preference Agent
4. Matching & Allocation Agent
5. Academician Engagement Agent
6. Monitoring, Notification & Escalation Agent
7. Curriculum Framing Agent

`backend/app/agent_graph.py` provides the LangGraph orchestration boundary. Each stage first executes trusted deterministic domain logic; LLM reasoning is advisory and provenance is recorded. If providers are unavailable, the workflow degrades transparently to deterministic reasoning rather than changing allocation behavior.

## Fast local demo

### Docker Compose — recommended

```bash
cp .env.example .env
docker compose up --build
```

Open `http://localhost:8080`.

The development Compose stack includes PostgreSQL, Redis, Alembic migration, FastAPI, Celery worker/beat and the React/Nginx frontend. Demo seeding is intentionally enabled only in the development Compose configuration.

### Local setup without Docker

Windows PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup_windows.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\run_backend.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\run_frontend.ps1
```

Linux/macOS:

```bash
./scripts/setup_unix.sh
./scripts/run_backend.sh
./scripts/run_frontend.sh
```

Open `http://localhost:5173`.

## Demo accounts

Demo accounts exist **only when `AUTO_SEED_DEMO=true`**. The frontend demo-login controls are separately gated by `VITE_SHOW_DEMO_ACCOUNTS=true`; production Compose forces this off. All seeded demo accounts use password `Demo@123`.

| Workspace | Email |
|---|---|
| Student | `student@stuskilllink.demo` |
| Company | `industry@stuskilllink.demo` |
| Academician | `academician@stuskilllink.demo` |
| Institution | `institution@stuskilllink.demo` |
| Admin | `admin@stuskilllink.demo` |

Admin cannot be publicly registered. In production, bootstrap an administrator with:

```bash
cd backend
python -m app.cli create-admin
```

The CLI is idempotent and refuses to promote an existing non-admin account.

## Authentication and security

Browser authentication uses **HttpOnly cookies**; the React app does not persist JWTs in `localStorage` or `sessionStorage`. The backend implements short-lived access tokens, rotating refresh sessions, logout/session revocation, same-origin protection for cookie-authenticated mutations, login throttling, role guards, organization verification gates, tenant scoping, security headers and production fail-closed configuration validation.

Production also requires email verification and SMTP configuration. Password reset invalidates existing refresh sessions.

See `docs/SECURITY_MODEL.md`.

## Ranking and allocation boundary

The current structured fit score uses:

- skill fit — 40%
- required-skill coverage — 20%
- LSRW — 10%
- project relevance — 10%
- academics — 5%
- location/work-mode fit — 5%
- preference signal — 5%
- portfolio evidence — 5%

Allocation prerequisites include LSRW completion, minimum CGPA, profile readiness and required-skill coverage. Tie-breaking is deterministic: **score → explicit student preference → application timestamp → stable application ID**.

Reservation/category evidence is not student-editable and is hidden from recruiter candidate views. Institution/Admin verification controls the evidence state. Opportunity reservation constraints require administrative approval and are snapshotted with algorithm/policy versions into allocation records. The software does not hard-code statutory percentages; the authorized deployment authority must configure the applicable policy.

## Credential model

Learning completion creates **credential evidence in `PENDING_VERIFICATION` state**, not an automatically verified badge. Admin verification is required before the credential is represented as verified. Public verification endpoints expose the credential status and metadata.

## LLM providers

The ordered provider gateway supports:

```text
NVIDIA NIM → Groq → Gemini → OpenRouter → deterministic fallback
```

Example:

```env
LLM_PROVIDER_PRIORITY=nvidia,groq,gemini,openrouter
NVIDIA_NIM_API_KEY=
GROQ_API_KEY=
GEMINI_API_KEY=
OPENROUTER_API_KEY=
```

Agent records retain provider/model attempts and whether live or fallback reasoning was used. The allocation engine remains deterministic when every LLM provider is unavailable.

## Production deployment

Production uses `docker-compose.prod.yml` as a reference deployment topology. It expects externally managed PostgreSQL, Redis and SMTP endpoints and deliberately rejects unsafe defaults.

```bash
cp .env.production.example .env.production
# Fill secret-managed values, then:
docker compose --env-file .env.production -f docker-compose.prod.yml up --build -d
```

Required production properties include:

- PostgreSQL database URL
- Redis endpoint
- unique 32+ character JWT secret
- HTTPS public app URL
- explicit HTTPS CORS origins
- explicit allowed hosts
- secure cookies
- email verification + SMTP
- Alembic-managed schema
- demo seed disabled

See `docs/PRODUCTION_RUNBOOK.md` before exposing the system publicly.

## Validation

Backend:

```bash
cd backend
python -m pip install -r requirements-dev.txt
python -m compileall -q app tests migrations
pytest -q
```

Migration lifecycle:

```bash
alembic upgrade head
alembic current
alembic check
```

Frontend on an internet-connected environment:

```bash
cd frontend
npm ci
npm run build
```

CI performs backend tests with the declared LangGraph dependencies, migration validation, the locked frontend production build, Compose validation and both Docker image builds.

## Important implementation-vs-target distinction

The SIH deck also names technologies such as React Query, Whisper Large-v3, Kokoro-82M, OR-Tools CP-SAT, MCP integrations, W3C Verifiable Credentials/Open Badges 3.0, BGE/Sentence-BERT and multiple external learning-platform connectors. These are **target/extension technologies unless explicitly marked implemented in `docs/PPT_COVERAGE_MATRIX.md`**. This repository does not claim a live integration merely because the technology appears in the presentation.

## Project map

```text
backend/app/                 API, auth, admin control plane, domain services, agents, integrations
backend/migrations/          Alembic production schema migrations
backend/tests/               End-to-end, product-coverage and production-hardening tests
frontend/src/                Five role-aware React workspaces and shared auth/API layer
.github/workflows/ci.yml     Backend/frontend/migration/container release gates
docs/ARCHITECTURE.md         Runtime architecture and decision boundaries
docs/SECURITY_MODEL.md       Identity, tenancy and authorization model
docs/PRODUCTION_RUNBOOK.md   Deployment and operational checklist
docs/PPT_COVERAGE_MATRIX.md  Implemented vs partial vs target SIH deck claims
docs/FINAL_VALIDATION_REPORT.md Local validation evidence and known environment limits
docs/RELEASE_NOTES.md       Production-hardening changes from the original prototype
docker-compose.yml           Development PostgreSQL + Redis full stack
docker-compose.prod.yml      Hardened reference production topology
```

For a presentation walkthrough, start with `docs/DEMO_GUIDE.md`.
