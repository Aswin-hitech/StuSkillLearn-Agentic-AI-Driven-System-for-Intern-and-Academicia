# StuSkillLink — SIH26044

**An Agentic AI-Based Portal for Academia–Industry Collaboration**  
CodeRhythm · Smart India Hackathon 2026  
**Right Student. Right Skill. Right Internship. Deserving Opportunity.**

StuSkillLink is a working four-workspace prototype for Student, Industry/Company, Academician and Institution users. It implements the proposal as a continuous ecosystem rather than a one-time placement portal: skill mapping → LSRW/readiness → learning → preference-aware matching → company ranking → allocation/reallocation → company feedback → placement continuity and curriculum insight.

## Fastest demo

### Option A — Docker
```bash
cp .env.example .env
# Optional: put your NVIDIA NIM key in .env
docker compose up --build
```
Open `http://localhost:8080`. Backend docs: `http://localhost:8000/docs`.

### Option B — local setup
Windows PowerShell:
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup_windows.ps1
# Then run these in two terminals:
powershell -ExecutionPolicy Bypass -File .\scripts\run_backend.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\run_frontend.ps1
```
Linux/macOS:
```bash
./scripts/setup_unix.sh
# Then run these in two terminals:
./scripts/run_backend.sh
./scripts/run_frontend.sh
```
Open `http://localhost:5173`.

## Demo logins
All demo accounts use password `Demo@123`.

| Workspace | Email |
|---|---|
| Student | `student@stuskilllink.demo` |
| Industry | `industry@stuskilllink.demo` |
| Academician | `academician@stuskilllink.demo` |
| Institution | `institution@stuskilllink.demo` |

The login page has one-click buttons for each account.

## LLM providers and failover
NVIDIA NIM remains the default primary provider. StuSkillLink now supports an
ordered failover chain across NVIDIA NIM, Groq, Google Gemini and OpenRouter.
Set any available keys; unavailable or rate-limited providers are skipped and
all core workflows continue through deterministic fallbacks.

The default hosted NIM base URL is `https://integrate.api.nvidia.com/v1`. Set:
```env
NVIDIA_NIM_API_KEY=your_key
NVIDIA_NIM_MODEL=meta/llama-3.1-8b-instruct
```
Optional providers:
```env
LLM_PROVIDER_PRIORITY=nvidia,groq,gemini,openrouter
GROQ_API_KEY=
GROQ_MODEL=openai/gpt-oss-20b
GEMINI_API_KEY=
GEMINI_MODEL=gemini-2.5-flash-lite
OPENROUTER_API_KEY=
OPENROUTER_MODEL=openrouter/free
```
OpenRouter's default uses its zero-cost model router. Free-provider limits and
availability can change. Every agent run records the selected provider/model,
failed attempts, deterministic evidence and whether fallback reasoning was used.

## Core product flows
- **Student:** profile/resume → preferences → skill-gap → LSRW → learning/industry programs → verified portfolio → internships/placements → offers.
- **Industry:** publish roles → company-wise rank list → inspect score evidence → multi-seat allocation → feedback → industry-led learning.
- **Academician:** expertise profile → FDP/research/consultancy matching → curriculum signals.
- **Institution:** cohort readiness → skill supply/gaps → curriculum actions → publish academician opportunities.
- **Shared:** six-agent activity, NIM status, transparent audit trail.

## Ranking and allocation
The weighted match score uses structured evidence and exposes an auditable Tier 1–4 fit band: skill fit (40%), required-skill coverage (20%), LSRW (10%), project relevance (10%), academics (5%), location/work-mode fit (5%), preference signal (5%) and portfolio evidence (5%). LSRW completion, minimum CGPA and a minimum required-skill floor are allocation prerequisites. Tie-breaking is deterministic: score → student preference → application timestamp → stable application ID.

Reservation/category seats are configurable per opportunity and are recorded in the allocation trail. The software deliberately does **not** hard-code statutory percentages; deployment policy must be supplied by the authorized institution.

## Test
```bash
cd backend
pytest -q
```
Reset seeded demo data:
```bash
python scripts/reset_demo.py
```

## Project map
```text
backend/app/       API, data models, algorithms, NIM, six-agent boundary
backend/tests/     End-to-end product flow tests
frontend/src/      Four role-based React workspaces
docs/              Architecture, SIH deck coverage, research and validation
scripts/           Demo reset and local run helpers
docker-compose.yml Full-stack container startup
```

Start with `docs/DEMO_GUIDE.md`. Read `docs/PPT_COVERAGE_MATRIX.md` for the proposal-to-implementation matrix, `docs/RESEARCH_AND_UX.md` for portal/UI research, and `docs/FINAL_VALIDATION_REPORT.md` for release validation.
