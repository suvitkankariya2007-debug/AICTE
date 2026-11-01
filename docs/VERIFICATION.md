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

## Module 3 — intake and document management

- Document records now persist MIME type and byte size alongside hashes and revisions.
- Application and compliance uploads share the same size, MIME, PDF signature, text-binary, and filename validation.
- Download responses use the stored MIME type and a constrained safe filename.
- Added migration `0005_document_metadata`, compatible with both fresh migrations and the legacy schema bootstrap.
- Added regression coverage for metadata persistence and safe download headers.

## Module 4 — scrutiny findings and correction responses

- Added persisted finding records with open, responded, and closed states.
- Added reviewer finding creation restricted to the assigned reviewer.
- Added institution responses scoped to the owning institution.
- Added reviewer closure requiring an institutional response.
- Added optimistic finding revisions and case-linked audit events.
- Added migration `0006_findings`.
- Backend regression suite: **21 passed**; frontend tests, typecheck, and build remain passing.

## Module 5 — assignment and task foundation

- Added durable assignment history with active/inactive records, assigning actor, reason, and timestamps.
- Added reviewer conflict declaration and clearance, with conflict reviewers blocked from assignment.
- Reviewer eligibility now uses active scoped memberships.
- Added assignment history and conflict APIs with authorization checks.
- Existing applications are backfilled into assignment history during migration `0007_assignments`.
- Added regression coverage for reassignment history, conflict blocking, closed/stale handling, and scoped access.
- Backend regression suite: **22 passed**.

## Module 6 — EVC participant and quorum foundation

- Added persisted EVC participant assignments with acceptance, decline, conflict, active state, and optimistic versions.
- Added coordinator assignment of eligible regional stage members.
- Added participant-specific acceptance/decline and conflict APIs.
- Decision advancement from EVC now requires schedule, report, and two accepted conflict-free members.
- Seeded the existing West EVC demo with two accepted synthetic members.
- Added migration `0008_evc_participants`.
- Backend regression suite: **23 passed**; frontend tests, typecheck, and build remain passing.

## Module 7 — compliance review and document validity

- Added explicit compliance clarification state and review reason.
- Added official verification actor and timestamp metadata.
- Added replacement-evidence requirement after clarification.
- Replacement uploads reset the obligation to pending and clear prior verification metadata.
- Added migration `0009_compliance_review` and `0010_compliance_replacement`.
- Added regression coverage for clarification, required replacement, resubmission, and continued verification invariants.

## Module 8 — notification delivery and escalation foundation

- Added notification delivery status, attempt count, error text, and delivered timestamp.
- Deadline sweep records simulated delivery as an auditable delivered attempt.
- Added national-oversight-only retry for failed notifications.
- Retry clears the failure and records an audit event; deduplication remains unchanged.
- Added migration `0011_notification_delivery` and retry regression coverage.

## Module 10 — document extraction foundation

- Added document processing status, extracted text, extraction error, and reviewer metadata.
- Plain-text uploads use a deterministic built-in extraction adapter.
- PDF processing remains explicitly failed until a real OCR provider is configured.
- Added reviewer-only process and extraction-review endpoints.
- Added migration `0012_document_extraction` and regression coverage for authorization and manual review.

## Module 11 — production integration hardening

- Added database-backed readiness reporting at `/api/health/ready`.
- Added persistent deadline worker heartbeat with last start, completion, error, and processed-count fields.
- Worker failures are logged and surfaced without silently converting failed iterations into successful health state.
- Added migration `0013_worker_heartbeat` and readiness regression coverage.
- Docker app healthcheck now includes a startup grace period; PostgreSQL/Docker execution remains unverified locally.

## Module 12 — deployment contract verification

- Corrected Docker Compose to use the psycopg PostgreSQL URL supported by `backend/requirements.txt`.
- Configuration validation now accepts `postgresql+psycopg` and rejects unsupported database schemes.
- Local migration, worker, backend, frontend, and production-build checks passed.
- Docker and PostgreSQL runtime execution remains unverified because Docker is unavailable in the validation environment.

## Module 13 — browser E2E and accessibility harness

- Added Playwright configuration and a mocked-API browser smoke test covering login, dashboard reachability, primary navigation, keyboard activation, and the refresh control label.
- Unit tests are scoped to `src` so Vitest does not execute Playwright files.
- Frontend unit tests: **4 passed**; TypeScript/Vite build passed.
- Playwright test discovery passed; execution is blocked because Chromium is not installed in the environment.

## Catalogue upgrade — application categories and clearer intake

- Expanded the illustrative catalogue from three to twenty populated workbook categories.
- Added four labelled evaluation tracks and category-specific evidence checklists.
- Grouped application selection in the frontend by evaluation track with explanatory APH-verification messaging.
- Preserved legacy `new_course` and EoA evidence-slot compatibility for existing seeded workflows.
- Backend regression suite: **27 passed**; frontend tests: **4 passed**; TypeScript/Vite build passed.

## Role-specific dashboard upgrade

- Added distinct dashboard titles, guidance, primary actions, and metric labels for institution, scrutiny officer, regional officer, and national oversight workspaces.
- Unknown or future roles receive a safe generic dashboard fallback.
- Existing authorization and case-scope rules remain unchanged.
- Backend regression suite: **27 passed**; frontend tests: **4 passed**; TypeScript/Vite build passed.

## Architecture persona foundation

- Added demo identities for Stage Coordinator, Stage Member, and National Verification Officer.
- Stage members can read only cases with an active participant assignment.
- Stage coordinators can read cases in their region; national verification officers can read the national queue.
- These personas are intentionally read-only until their full workflow actions are implemented.
- Backend regression suite: **28 passed**; frontend tests: **4 passed**; TypeScript/Vite build passed.
