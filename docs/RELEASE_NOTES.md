# StuSkillLink 2.0 — Production Hardening Release Notes

This release evolves the original SIH26044 prototype into a governed multi-tenant release candidate centered on the updated seven-agent proposal and an Admin control plane.

## Major additions

- Admin Command Center with global user, tenant, organization, opportunity, allocation, credential, policy, audit, agent and platform-health oversight.
- Seven specialized agent stages, including Curriculum Framing.
- Company and institution trust states with Admin approval/suspension/rejection.
- Institution tenant membership for students and academicians.
- Protected reservation/category evidence with institution/Admin verification and recruiter redaction.
- Moderated opportunity lifecycle and server-side deadline enforcement.
- Deterministic, versioned allocation and reallocation with transactional seat accounting and decision snapshots.
- Pending/verified/rejected credential evidence instead of automatic self-verification.
- Engagement lifecycle controls and feedback only after completion.
- HttpOnly browser sessions, rotating refresh tokens, logout/session revocation, same-origin mutation protection and login throttling.
- Email verification and password-reset flows.
- PostgreSQL/Alembic production path, Redis/Celery infrastructure, health/readiness probes and exact Alembic-head readiness validation.
- Hardened non-root containers, security headers, development and production Compose topologies, CI and Dependabot.

## Security fixes from the prototype review

- Cross-institution/global student visibility removed.
- Global audit/agent feeds restricted and scoped.
- Unverified organizations blocked from operational access.
- Public Admin registration removed; Admin bootstrap is CLI-only.
- LSRW impossible score inputs rejected and scores bounded.
- Explicit student preference handling corrected.
- Expired opportunities cannot accept applications or be reopened without a valid deadline.
- Reserved-seat conversion follows the active Admin policy instead of silently converting.
- Company trust revocation pauses/cancels active recruitment activity.
- Demo sign-in controls are disabled in production frontend builds.
- Production config rejects weak/default/template JWT secrets and unsafe runtime defaults.

## Validation evidence

See `FINAL_VALIDATION_REPORT.md` for the exact local validation result and environment limitations. The repository CI is the authoritative release gate for network-dependent frontend dependency installation, LangGraph execution, Docker/Compose validation and image builds.

## Presentation-vs-implementation boundary

The updated SIH deck includes additional target technologies such as Whisper Large-v3, Kokoro-82M, BGE/Sentence-BERT, OR-Tools CP-SAT, MCP connectors, W3C Verifiable Credentials and Open Badges 3.0. They are not automatically claimed as implemented. See `PPT_COVERAGE_MATRIX.md` for the current status of every deck commitment.
