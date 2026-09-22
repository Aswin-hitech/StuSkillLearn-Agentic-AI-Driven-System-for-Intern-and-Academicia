# StuSkillLink Security Model

## Security goals

StuSkillLink handles student education/readiness data, company hiring workflows and institution-level analytics. The primary security requirements are therefore:

1. prevent cross-tenant disclosure,
2. prevent self-authorized organization/admin privileges,
3. protect authentication sessions,
4. protect sensitive reservation/category evidence from unnecessary recruiter exposure,
5. preserve allocation integrity and auditability,
6. fail closed under unsafe production configuration.

## Identity and role model

Public registration supports only:

- `STUDENT`
- `COMPANY`
- `ACADEMICIAN`
- `INSTITUTION`

`ADMIN` is not publicly registerable. Production administrators are created server-side with `python -m app.cli create-admin`.

Authentication alone does not grant every portal capability:

- company workflows require verified company status,
- institution workflows require verified institution status,
- production portal access can require verified email,
- tenant-scoped resources require an explicit tenant relationship.

## Session model

- passwords: bcrypt in production; legacy PBKDF2 hashes are accepted only for migration compatibility.
- access token: short-lived signed JWT.
- refresh token: opaque random secret whose hash is stored server-side.
- refresh rotation: a successful refresh revokes/replaces the previous refresh session.
- browser persistence: HttpOnly cookies; the React client does not store JWTs in Web Storage.
- logout: revokes the presented refresh session and clears cookies.
- password reset: revokes all existing refresh sessions for the account.

## CSRF and browser boundary

Cookie-authenticated state-changing requests (`POST`, `PUT`, `PATCH`, `DELETE`) are protected by trusted-origin checks. In production, a cookie-authenticated mutation without an Origin header is rejected. Explicit bearer-authenticated API clients remain supported independently of browser cookies.

Cookies are configured `Secure` in production. Deployment must terminate HTTPS before browser traffic reaches the application.

## Tenant isolation

Institution-owned data is always scoped through `institution_profile_id`. Company-owned data is scoped through `company_profile_id`. Global feeds are not exposed to ordinary tenants.

Expected access model:

```text
Student       -> own profile/readiness/applications/offers
Company       -> own organization/opportunities/authorized applicants/allocations
Academician   -> own profile + assigned institution scope
Institution   -> only assigned students/academicians and its own published records
Admin         -> global governance and audit
```

Adding a new route that returns organization data requires an explicit tenant/role review.

## Protected reservation/category evidence

Students cannot directly edit trusted reservation/category status. Institution/Admin workflows verify evidence and record source/status. Recruiter-facing student serialization intentionally omits protected category/status data. Allocation policy consumes trusted evidence without requiring recruiters to inspect it.

Deployment authorities are responsible for configuring legally applicable policy; the software does not infer or hard-code statutory quotas.

## Organization trust

New company and institution registrations are `PENDING` by default. Operational organization endpoints require verified status. Admin can approve, reject or suspend organizations. This prevents a freshly self-registered company from publishing roles or accessing candidate operations immediately.

## Opportunity integrity

- creation by a verified company does not bypass moderation,
- deadline is represented as a datetime and enforced server-side,
- expired opportunities cannot be reopened as active without a valid future deadline,
- allocation policy is administratively governed,
- recruiter-controlled inputs cannot directly modify protected platform policy.

## Allocation integrity

Allocation uses deterministic ranking evidence and database safeguards. Production PostgreSQL paths use row locking during allocation, and database constraints prevent duplicate candidate/opportunity allocations. Allocation records retain decision snapshots plus algorithm and policy versions.

Feedback is accepted only after a completed engagement, preventing an unaccepted offer from creating placement-continuity evidence.

## Credential trust

Learning completion is evidence, not verification. New credentials enter `PENDING_VERIFICATION`; Admin changes status to `VERIFIED` or `REJECTED` after evidence review. The public verification endpoint exposes current status and metadata.

## Audit

Security-relevant and domain events are written to the relational audit trail with actor, entity and request ID where available. Organization users receive only scoped audit/activity data; Admin can inspect the global registry.

MongoDB can optionally mirror events for analytics/integration, but it is not authoritative.

## Production fail-closed rules

Production startup rejects:

- SQLite database URLs,
- known/default/template-placeholder or short JWT secrets,
- debug mode,
- auto schema creation,
- demo seeding,
- implicit/default Redis configuration,
- wildcard/empty CORS origins,
- wildcard/empty allowed hosts,
- non-HTTPS public URL/CORS origin,
- insecure cookies,
- missing SMTP when email verification is required.

## Container boundary

Reference production services run as non-root users where defined, drop Linux capabilities and use read-only filesystems for backend services with a small writable `/tmp`. Frontend Nginx adds CSP, frame protection, MIME sniffing protection, referrer and permissions policies.

## Remaining deployment responsibilities

Repository controls cannot replace platform operations. A real deployment should also provide:

- managed secret storage/rotation,
- encrypted database backups and restore drills,
- TLS/WAF/DDoS controls,
- centralized logs/metrics/traces,
- vulnerability/dependency scanning,
- incident response and data-retention policy,
- legal/privacy review for student and reservation data,
- penetration testing before high-stakes/public use.
