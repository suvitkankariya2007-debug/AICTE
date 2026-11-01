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
