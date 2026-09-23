# StuSkillLink Production Runbook

This runbook describes the minimum supported production path for the repository. It is intentionally stricter than the local demo configuration.

## 1. Provision external services

Required:

- PostgreSQL 16+ / compatible managed PostgreSQL
- Redis 7+ / compatible managed Redis
- SMTP service capable of sending verification/reset mail
- HTTPS hostname for the application

Optional:

- one or more LLM providers
- Twilio SMS
- MongoDB audit mirror

Do not use the demo Compose passwords or demo seed on a public system.

## 2. Create production environment

Copy `.env.production.example` into your secret-management system. Do not commit filled secrets.

Generate a strong JWT secret, for example using a trusted secret manager or OS CSPRNG. The app requires a unique secret of at least 32 characters.

Required variables include:

```text
PUBLIC_APP_URL=https://...
ALLOWED_HOSTS=...
DATABASE_URL=postgresql+psycopg://...
REDIS_URL=redis://... or rediss://...
JWT_SECRET_KEY=...
SMTP_URL=...
SMTP_FROM_EMAIL=...
```

The application validates these invariants at startup.

## 3. Database migration

Never use `Base.metadata.create_all()` as the production migration mechanism.

Run:

```bash
cd backend
alembic upgrade head
alembic current
alembic check
```

Back up the database before applying migrations in an existing environment.

## 4. Bootstrap the first Admin

From a trusted backend environment:

```bash
cd backend
python -m app.cli create-admin
```

Enter the administrator email and a strong password interactively. Do not expose an Admin registration route.

## 5. Container deployment

Reference deployment:

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml config
docker compose --env-file .env.production -f docker-compose.prod.yml up --build -d
```

The production Compose file assumes PostgreSQL and Redis are managed/external services; it does not publish database/cache containers as part of the public stack.

## 6. Health checks

- `GET /health` — process liveness.
- `GET /ready` — database connectivity; production also requires Redis and an Alembic revision.
- frontend `GET /healthz` — Nginx/static frontend health.

Do not route user traffic to a backend that fails `/ready`.

## 7. Verification workflow after deploy

Perform these checks with non-production test identities before enabling real users:

1. public Admin registration returns failure.
2. unverified company cannot publish/use operational company routes.
3. unverified institution cannot read tenant student data.
4. newly verified empty institution sees zero other-institution students.
5. student cannot set protected reservation status directly.
6. recruiter rank-list response does not contain reservation-category evidence.
7. expired opportunity rejects applications.
8. company feedback is rejected before `COMPLETED` engagement state.
9. learning completion creates pending, not verified, credential evidence.
10. Admin can verify credential evidence.
11. browser login creates HttpOnly access/refresh cookies.
12. logout invalidates the session.
13. cross-origin cookie mutation is rejected.
14. allocation records retain algorithm/policy version and decision snapshot.

The automated backend hardening suite covers these boundaries and should be run in CI on every release.

## 8. CI release gates

`.github/workflows/ci.yml` gates:

- dependency installation
- Python compilation
- backend tests
- LangGraph tests in a fully provisioned runner
- Alembic upgrade/check/downgrade/upgrade lifecycle
- locked `npm ci`
- TypeScript + Vite production build
- development Compose validation
- production Compose validation
- backend Docker build
- frontend Docker build

Do not promote a release with a failed CI gate.

## 9. Backup and rollback

Before schema/application changes:

- take a consistent PostgreSQL backup/snapshot,
- record the deployed application image/version,
- record the current Alembic revision,
- test restore procedures periodically.

Application rollback is safe only when the database schema remains compatible. If a migration must be downgraded, test the downgrade against a staging copy first.

## 10. Logs and monitoring

Backend access logs include request ID, method, path, status and latency. Preserve `X-Request-ID` through the external reverse proxy/load balancer.

Production operations should additionally collect:

- 5xx/error rate
- p50/p95/p99 latency
- DB connection/pool saturation
- Redis health
- Celery queue depth/failures
- LLM provider failure/fallback rates
- email/SMS delivery failures
- login throttling events
- organization/account suspension events
- allocation/reallocation errors

## 11. Scaling notes

The transactional source of truth is PostgreSQL. Web/API replicas can be scaled horizontally provided they share the same database, Redis and secrets.

Agent final results are persisted in the relational model. The current LangGraph execution checkpoint is local/ephemeral per process in the reference container; do not advertise cross-replica resumable long-running graph execution without replacing it with a shared production checkpointer. Ordinary synchronous seven-stage runs complete within the handling process and retain their final audited output in PostgreSQL.

## 12. Data governance

Before onboarding real institutions, define:

- retention/deletion periods,
- who may verify reservation/category evidence,
- who may approve allocation policy,
- credential-evidence retention,
- applicant consent language,
- audit access policy,
- incident response contacts,
- data export/deletion processes required by applicable law/policy.
