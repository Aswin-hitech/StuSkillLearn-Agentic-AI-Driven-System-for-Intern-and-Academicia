# SIH26044 Deck Coverage Matrix

This matrix deliberately separates what the repository **implements now** from technologies/capabilities that appear in the updated SIH deck as a **target architecture or extension**. A presentation claim is not treated as implemented unless corresponding source/infrastructure exists.

Status meanings:

- **Implemented** — present in the current repository and exercised by application/tests where practical.
- **Partial** — meaningful boundary/prototype exists, but not the full production integration described by the deck.
- **Target** — proposed in the deck; not implemented as a live production integration in this repository.

| Deck commitment / technology | Status | Repository evidence / boundary |
|---|---|---|
| Student workspace | Implemented | Profile/resume, preferences, skill gaps, LSRW, learning, portfolio, opportunities and offers |
| Company / Industry workspace | Implemented | Organization verification gate, opportunity workflow, rank lists, allocation lifecycle, feedback, learning programs |
| Academician workspace | Implemented | Expertise profile, FDP/research/consultancy matching and curriculum signals |
| Institution workspace | Implemented | Tenant-scoped readiness, curriculum insight and academician opportunity management |
| Admin / governance control plane | Implemented | Global users/tenancy, organizations, opportunity moderation, policy, credentials, audit, allocations, agents and health |
| 7 specialized agents | Implemented | Intake & Eligibility; Skill & Communication; Portfolio & Preference; Matching & Allocation; Academician Engagement; Monitoring/Notification/Escalation; Curriculum Framing |
| LangGraph | Implemented | Required backend dependency and `app/agent_graph.py`; deterministic degraded path for offline review environments |
| Skill-gap mapping | Implemented | Student/opportunity demand comparison and priority recommendations |
| Actionable learning path | Implemented | Demand-backed recommendations and company learning programs |
| Communication assessment / LSRW | Partial | Objective listening/reading + prototype text rubrics for speaking/writing; not a validated high-stakes language exam engine |
| Preference-aware matching | Implemented | Domain/location/work-mode signals, explicit ranked opportunities and general-pool opt-in |
| Company-wise rank lists | Implemented | Deterministic rankings with visible components and fit tiers |
| Explainable allocation | Implemented | Match evidence, tie-break evidence, allocation reason, immutable decision snapshot, algorithm/policy versions and audit trail |
| Multi-seat allocation | Implemented | Capacity checks, uniqueness constraints and PostgreSQL row locking path |
| Reservation-category handling | Implemented with deployment-policy boundary | Protected evidence, institution/Admin verification, recruiter redaction and Admin-approved opportunity policy; no statutory percentage is hard-coded |
| Automatic reallocation | Implemented | Offer rejection advances to the next eligible candidate according to deterministic policy |
| Placement continuity | Implemented | Completed engagement feedback can add a visible placement-continuity signal |
| Curriculum Framing Agent | Implemented | Explicit refresh operation and versioned/history-preserving curriculum insight records |
| Curriculum co-design / joint sign-off | Partial | Curriculum signals/history and administrative governance exist; a formal two-party digital-signature workflow is not implemented |
| Digital portfolio | Implemented | Skills, projects, certifications, LSRW and credential evidence |
| Verified digital credentials | Partial | Pending/verified/rejected credential lifecycle + public verification metadata; W3C cryptographic VC issuance is not implemented |
| React 19 | Implemented | Frontend source and locked package configuration |
| Tailwind CSS | Implemented | UI design system and responsive role workspaces |
| React Query | Target | Current frontend uses a typed shared fetch/session layer and local data states; `@tanstack/react-query` is not currently installed |
| FastAPI / Pydantic | Implemented | Typed REST API, validation and role/tenant dependencies |
| PostgreSQL / Neon | Implemented production path | SQLAlchemy + psycopg + Alembic; production config rejects SQLite |
| Redis | Implemented infrastructure | Rate-limit/Celery integration and production readiness requirement |
| Celery | Implemented infrastructure | Worker/beat app and Compose services; not every HTTP operation is converted to an asynchronous task |
| NVIDIA NIM | Implemented provider adapter | OpenAI-compatible chat provider with provenance/failover |
| Groq | Implemented provider adapter | Configurable failover provider |
| Gemini | Implemented provider adapter | Configurable failover provider |
| OpenRouter | Implemented provider adapter | Configurable failover provider |
| Live `/v1/models` provider discovery | Partial | Provider/model configuration/status exists; the project does not claim identical remote live discovery for all providers |
| BGE / Sentence-BERT embeddings | Target | Not included as a live local embedding model in the current repository |
| spaCy | Target | No production spaCy pipeline in the current repository |
| Whisper Large-v3 | Target | Browser speech-to-text/prototype text assessment exists; Whisper is not integrated |
| Kokoro-82M | Target | Not integrated |
| Embedding-based LSRW grading | Target | Current production code uses deterministic/prototype rubric logic |
| OR-Tools CP-SAT | Target | Current allocator is deterministic transactional domain logic; OR-Tools is not installed |
| MCP orchestration | Target | No MCP runtime is required by this repository |
| Twilio | Partial | Real SMS adapter/configuration boundary exists; availability depends on credentials/service configuration |
| SMTP email | Implemented adapter | Verification/reset notification path with production SMTP requirement |
| NPTEL / Coursera / Udemy connectors | Partial | Learning metadata/resource boundaries exist; authenticated provider APIs/contracts are not bundled |
| Bhashini API | Target | Not integrated |
| GitHub MCP | Target | Not required or integrated in the application runtime |
| W3C Verifiable Credentials | Target | Credential metadata/status exists; no W3C cryptographic VC issuer/verifier implementation |
| Open Badges 3.0 | Target | Standards metadata can be stored; full signed Open Badges 3.0 issuance is not implemented |
| MongoDB | Partial / optional | Best-effort audit-event mirror adapter when configured; PostgreSQL remains source of truth |
| OAuth 2.0 | Target for external identity federation | Current application uses first-party email/password + JWT/cookie sessions; no third-party OAuth IdP is bundled |
| bcrypt | Implemented | Production password hashing with legacy PBKDF2 verification/migration path |
| JWT | Implemented | Short-lived access JWT + rotating server-tracked refresh sessions |
| Cloudflare | Deployment target | Compatible with reverse proxy/WAF deployment; not provisioned by repository code |
| Vercel / Render | Deployment target | Container/static deployment can be adapted; no provider account is provisioned here |
| AWS EC2/S3/RDS | Deployment target | Production architecture is compatible; infrastructure-as-code for AWS is not included |
| Kubernetes | Deployment target | Containers are suitable building blocks; Kubernetes manifests/operator setup are not included |
