# SIH26044 Proposal Coverage Matrix

This build treats the submitted SIH26044 deck as the product source of truth. The product has four user workspaces only: Student, Industry/Company, Academician, Institution.

| Proposal commitment | Implemented prototype evidence |
|---|---|
| Skill-gap mapping | Student profile/resume normalization, opportunity-demand comparison, priority-gap report |
| Actionable learning paths | Demand-backed recommendations, NPTEL/SWAYAM/Coursera integration boundaries, completion badges |
| LSRW before allocation | Listening/reading objective scoring + speaking/writing rubric; LSRW is an allocation prerequisite |
| Preference-aware matching | Domain/location/work-mode preferences, ranked opportunities, general-pool opt-in |
| Company-wise rank lists | Deterministic per-opportunity rankings with visible score breakdown and TIER_1–TIER_4 fit bands |
| Explainable decisions | Match evidence, missing/matched skills, tie-break order, allocation reason and audit events |
| Multi-seat allocation | Configurable seat capacity with deterministic allocation |
| Reservation-category handling | Per-opportunity configurable category seat constraints; no statutory percentages are hard-coded |
| Automatic reallocation | Rejected offers automatically move to the next eligible ranked candidate |
| Continuous placement | Successful internship feedback recommending placement adds a small, visible placement-continuity signal |
| Digital portfolio | Skills, projects, certifications, LSRW and verified badges in one student portfolio |
| Industry-led learning | Company learning programs; completion issues portfolio badge evidence |
| Company feedback loop | Internship/allocation feedback feeds curriculum insight and placement continuity |
| Academician opportunities | FDP, research, consultancy, industrial training, mentorship and workshop model |
| Curriculum insight | Institution/academician dashboards aggregate role demand, student gaps and company feedback |
| Six specialized agents | Eligibility/Profile, Skill/Communication, Portfolio/Preference, Matching/Allocation, Academic Engagement, Monitoring/Reallocation |
| LangGraph orchestration | Optional `requirements-ai.txt` + `app/agent_graph.py`; deterministic fallback keeps product runnable offline |
| NVIDIA NIM | OpenAI-compatible NIM chat client, `/v1/models` discovery, optional embeddings adapter and deterministic fallback |
| React + Tailwind | Role-based responsive React UI and custom Tailwind design system |
| FastAPI / REST | Typed FastAPI API for all four workspaces |
| PostgreSQL / Neon readiness | SQLAlchemy `DATABASE_URL` portability; local SQLite default for zero-setup demo |
| MongoDB | Optional live audit-event mirror when `MONGODB_URI` is configured; relational DB remains transactional source of truth |
| Security | JWT sessions, PBKDF2 password hashing, role guards, CORS configuration |
| Docker / cloud | Backend/frontend Dockerfiles and Docker Compose; suitable for container deployment/AWS adaptation |
| Learning/certification integrations | Provider boundaries plus verified internal badges; live third-party APIs require provider credentials/contracts |
