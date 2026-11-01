# Verification record — 1 November 2026

Executed and passed:

- Backend pytest: 10 scenarios against temporary SQLite databases.
- Frontend Vitest/jsdom: 4 interaction scenarios with mocked API responses.
- TypeScript typecheck and Vite production build.
- Alembic initial migration against a fresh SQLite database.
- Uvicorn application startup, schema and seed initialization.
- Standalone deadline worker: first run created 5 simulated notices; repeat run created 0.

Backend coverage includes authentication, session revocation, forged role payloads, regional and document access isolation, distinct checklists, missing and invalid uploads, request-key replay, document revisions, correction/resubmission, route-specific stage rejection, decision permissions, EVC prerequisites, submission versus verification, renewal dates, alert deduplication and escalation, continuing document monitoring, failed-action rollback, independent sessions, restart persistence, concurrent updates, audit original/destination state and origin rejection.

Frontend coverage: login → dashboard → case → logout; request-specific checklist; queue search/empty result; API failure shown without claiming success.

Limits: managed preview failed because its mirrored environment could not access `.venv/bin/python`. No browser screenshots, browser E2E or visual match verification are claimed. Docker and PostgreSQL execution are unverified. FastAPI/Starlette emitted one httpx test-client deprecation warning; tests passed. This release is a local functional demo, not a deployed public service.

## Release 2026-11-01-r2

- FastAPI HTTP/SQLite tests: **14 passed**, including assignment authority and scope handoff, cross-region/closed/stale rejection, meaningful reason checks, compliance-file versions/download isolation, mandatory upload, and replacement reopening verification.
- React/jsdom interactions: **4 passed**.
- Separate browser-local rehearsal tests: **6 passed** (these are not backend security evidence).
- TypeScript and Vite production build passed. No database schema change in this release; previous migration result remains applicable.
- Browser QA of the local static rehearsal: role login, regional dashboard, conditional tracker and reviewer reassignment succeeded; workload counts, revision and audit updated visibly. QA caught an insecure-HTTP randomUUID issue; identifiers now use getRandomValues. File hashing requires HTTPS (the hosted preview uses HTTPS). Browser upload/download E2E remains unverified; actual bytes/hash/version/isolation are exercised in backend and rehearsal unit tests.

Deployment boundary: ChatGPT Site hosts an interactive browser-local rehearsal, not FastAPI. It uses IndexedDB for this browser and sessionStorage for the selected demo account. Role checks are simulations; server security, cross-device persistence and background tasks cannot be accepted from it. No Railway deployment. PostgreSQL/Docker and full browser E2E remain unverified. Manual acceptance boxes remain unchecked.

## Module 0 — foundation hardening

- Backend regression suite: **16 passed**.
- Added validated environment settings for database URL, frontend origin, demo mode and secure cookies.
- Added request correlation via `X-Request-ID`, response security headers and structured request access logs without logging credentials or file contents.
- Added operational indexes for scoped application queues, documents, obligations, audit history, sessions and notifications.
- Added an idempotent Alembic migration for the operational indexes.
- Added regression coverage for request correlation and invalid database configuration.
- Frontend Vitest/jsdom: **10 passed**; TypeScript typecheck and Vite production build passed.

Validation note: dependencies were installed from the existing `backend/requirements.txt` and `frontend/package-lock.json`. The later follow-up hardening upgraded frontend development tooling and resolved the reported audit findings.

## Follow-up hardening — 1 November 2026

- Correlation IDs now accept only bounded alphanumeric IDs with `.`, `_`, `:` and `-`; invalid values are replaced with a generated ID before logging or response headers.
- Production Docker startup now sets `AUTO_CREATE_SCHEMA=false` and uses the existing Alembic upgrade command. Local/test startup retains `AUTO_CREATE_SCHEMA=true` for the lightweight demo flow.
- Frontend build tooling was upgraded to address the reported Vite, Vitest, and Tinypool advisories; tests and build were rerun after the upgrade.

## Module 1 — identity and authorization foundation

- Added persisted, active role memberships with region and institution scope.
- Added `/api/me/roles` for verified memberships; existing login and UI user payloads remain backward compatible.
- Case access and reviewer authorization now require an active matching membership instead of trusting only the legacy user fields.
- Session cookies now use validated `COOKIE_SECURE` settings.
- Added an idempotent role-membership migration compatible with the repository's initial schema bootstrap.
- Backend regression suite: **17 passed**.
- Frontend tests, typecheck, and production build remain required regression checks for the unchanged UI.

## Module 2 — versioned rule registry

- Added persistent rule sets with version, source, effective date, status, and checklist/route definitions.
- Existing applications retain their stored route and rule version.
- New applications bind to the latest published rule set whose effective date has started.
- Added national oversight draft and publish endpoints with strict route/checklist validation.
- Added migration `0004_rule_sets`, compatible with the existing schema bootstrap.
- Added regression coverage for draft publication, future-proof effective-date selection, and application rule binding.
