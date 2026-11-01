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
