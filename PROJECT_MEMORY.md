# Project memory

Last updated: 2026-10-31

## Working agreement

- Active repository: suvitkankariya2007-debug/AICTE.
- All project changes and remote commits belong on branch `test` only.
- The assistant handles commits and remote updates; the user does not want to run local CLI commands.
- Read AGENTS.md and this file before continuing project work. Update this record when requirements, decisions, implementation status, or blockers change. Commit updates on `test`.
- This is a curated project record, not a verbatim archive of all chats. Never store credentials or authentication codes.

## Problem statement and expected outcome

Build one integrated platform for AICTE approval processing and institutional compliance monitoring. Reduce repetitive follow-up, make processing and pendency visible, improve deadline and document tracking, and preserve accountability. The platform supports, but does not replace, regulatory scrutiny, inspection, verification, or decisions reserved for competent authorities.

### Approval workflow

- Automatically route applications through APH-prescribed combinations: Only Scrutiny, Scrutiny + EVC, EVC + SAC/SHC, Only EVC, and other applicable routes.
- Move cases to the next prescribed stage only after predecessor completion and required authorised action.
- Let authorised users return/revert a case for deficiency, clarification, or further verification with recorded reasons.
- Automate permitted administrative tasks, standard communications, and electronic case summaries.
- Keep routes and timelines configurable, versioned, traceable to rule source/effective date; don't assume one universal route. SAC and SHC remain distinct procedures.

### Dashboards and pendency

- Consolidated near-real-time views across regions, stages, institutions, officers, and committees.
- Track ageing, prescribed timelines, workloads, pending cases, and bottlenecks.
- Alert on approaching/overdue timelines.
- Role-based dashboards for Regional officers, Bureau officers, committees, and other authorised roles.
- Full audit of case movement, observations, actions, decisions, notifications, and closure.

### EVC

- Put eligible cases in an EVC queue after preliminary processing.
- Track scheduling and completion, especially for new institutions; remind and escalate delays.
- The prototype may have an AICTE scheduling official coordinate scheduling, with experts indicating availability and institutions receiving the schedule/preparing. This is a product assumption to validate against current APH procedure. Committee selection and visit scheduling are distinct.

### Undertakings and compliance

- Maintain approval conditions/time-bound undertakings, evidence requirements, due dates, submission records, and verification status.
- Include undertaking forms in the institution workflow: view applicable form/condition, fill or acknowledge it, attach supporting evidence, submit, track due date, and receive clarification/verification outcome.
- Notify institutions of upcoming due dates; let them submit evidence online.
- Authorised officials verify compliance evidence. Submission alone is not verified compliance.
- Remind and escalate overdue/unfulfilled conditions.

### Lease and document validity

- Track validity/expiry for lease and other prescribed documents where applicable.
- Alert institutions before expiry; request renewal documents; track submission and official verification.
- Alert/escalate expired documents and missing renewals.

### Notifications, escalation, reports, security, integration

- Configurable notifications for pending applications, deadlines, EVC, compliance, and expiry.
- Rule-based escalations to designated officials; consolidated reports for pendency, EVC, undertakings, document validity, overdue work, and regional performance.
- Secure document storage, confidentiality, server-enforced role/jurisdiction/assignment permissions, and traceable actions.
- Integrate with authorised AICTE systems where feasible; do not claim live integration without access/approval.

### OCR requirement (prototype feature)

- Add OCR/document extraction to help process relevant uploaded evidence: identify document type and suggest fields such as institution/application reference, undertaking identifier, issue/effective date, due date, lease start/end/expiry, and extracted text snippets.
- Preserve source file, page/region provenance, extracted value, confidence, parser/version, and reviewer corrections.
- Show low-confidence/missing fields for human review. Never let OCR decide document validity, compliance, eligibility, or approval. Authorised human verification remains mandatory.
- Prototype with synthetic/de-identified sample documents; confirm actual form templates, required fields, languages, file formats, and OCR dataset availability before selecting a final OCR engine.
- Keep OCR outputs separate from authoritative application/compliance/document statuses.

## Roles and interface direction

One login with role-based workspaces. A role switcher can support a seeded-data prototype only; production permissions must be enforced server-side. Candidate workspaces: Institution representative; scrutiny/re-scrutiny official; EVC coordinator/member; Regional officer; Bureau officer; committee/competent authority; system administrator. Confirm actual role boundaries from official process before production.

Desired screens: dashboards, applications list, case detail/timeline, document review/OCR, undertaking/compliance workbench, EVC scheduling, alerts/escalations, reports, audit history, and configuration/rule management.

## Prototype approach and acceptance

Start with one end-to-end path: institution submits application and documents -> official scrutiny raises a reasoned deficiency -> institution resubmits corrected/versioned evidence -> official verifies and advances stage -> applicable undertaking form is completed with evidence and due date -> authorised official verifies it -> reminder/escalation is demonstrated for an overdue item. Add EVC and route variants as the next slice.

Prototype evaluation should demonstrate workflow accuracy, alert timeliness, dependable deadlines, visible pending work, reduced manual follow-up, and complete audit trail. Acceptance should cover route transitions, permission enforcement, deadline calculations, notification de-duplication, evidence verification, OCR confidence/review, audit history, and integration failure handling. Clearly label prototype data and unvalidated sample rules.

## User requests and preferences

- Explain complete solution architecture and workflow for PPT use.
- Separate workflow and architecture diagram images in the supplied PPT's dark style: dark background, bright outlines, rounded boxes, light connectors; remove Bug Mafias branding and irrelevant cropped content.
- Build an initial AICTE-style frontend with complete page layouts/design specs; decide roles, logins, dashboards.
- Evaluate/refine the iteration using 0.25 feasibility + 0.25 innovation + 0.20 dataset availability + 0.15 competitive advantage + 0.15 ability. Define scale and evidence before scoring.
- Reference slide link: https://canva.link/kbgxqb16k748grk . Full contents have not been verified in this repository.

## Confirmed progress

- Original repository gangrasshrikant0-ui/AICTE-AUTOMATE was readable but connector writes returned HTTP 403.
- Replacement repository: suvitkankariya2007-debug/AICTE. Branch `test` exists.
- Commit c1b8b3255b29eb0d29d4939a50f27b0d3a82b3e8 added AGENTS.md.
- Commit 3d226a7fe1adde352891c807b7d4d44123aaae68 added the earlier PROJECT_MEMORY.md; this update records the complete PS pasted by the user and the undertaking/OCR additions.
- No application implementation or diagram deliverables have been verified in this repository yet.

## Next steps

1. Read current repository files and confirm any existing frontend/prototype.
2. Map the problem statement to roles, routes, state transitions, forms, data entities, and acceptance criteria.
3. Build the smallest complete workflow slice; clearly identify APH rules requiring verification.
4. Add OCR assistive extraction and reviewer correction flow using sample documents.
5. Keep implementation, diagrams, and this record aligned; commit only to `test`.

## Continuity limits

Separate chats do not automatically share their full histories. In a new chat, identify this repository and `test` branch and ask the assistant to read AGENTS.md and PROJECT_MEMORY.md first. Treat repo records as curated project context, not a verbatim chat archive; distinguish confirmed facts from assumptions.


## Implementation checkpoint — 1 November 2026

Latest user scope: reuse properly where possible and defer additional substantial engines. Current tested slice implements shared persisted applications, three illustrative checklists, two routes, permission-scoped institution/reviewer/regional/oversight accounts, reasoned correction/resubmission, versioned documents, EVC scheduling/report gate, authorised demo decisions, undertaking/document evidence references and verification, actual renewal dates, deadline worker, deduplicated simulated notices and transactional audit.

Licensed reusable foundations: transitions (MIT), SQLAlchemy, FastAPI, React/Vite and Lucide. Same-PS repositories have no confirmed reusable licence, so their code was studied but not copied. Sources and exact prompt coverage are in docs/REUSE.md and docs/SCOPE.md. This is deliberately not completion of every original prompt.

Verified locally: 10 backend HTTP/database scenarios, 4 frontend jsdom interaction scenarios, TypeScript/build, fresh SQLite migration, uvicorn startup and worker sweep. Managed browser preview could not access the Python virtual environment; no browser E2E or pixel-level visual QA claimed. PostgreSQL/Docker execution remains unverified.

Deferred: APH registry approval/import, numeric regulation/OCR engine, remaining official role workspaces, workload assignment, expert appointment/quorum, SHC/SAC/hearings, national referrals, grievances, full compliance evidence files, live SMS/payment/NBA, AI drafts and certificate PDFs. No external API keys required for current demo. User explicitly authorised pushing tested work to test; main remains untouched.

Next: use README.md to launch; address docs/SCOPE.md deferred list only when user expands scope; preserve test-only pushes and rerun relevant checks after changes.

## Preview/testing update — 1 November 2026, release 2026-11-01-r2

User requests: preserve the SAME ChatGPT Site URL after every update, no Railway deployment for now, keep a separate GitHub acceptance checklist, and explain stage tests before adding features.

Site identity: appgprj_6ae7414286e48191815bc2ac4dfdf833. URL: https://aicte-workspace-preview-suvit.glassycalf256.chatgpt.site/ . Preserve existing audience.

Implemented next features: regional reviewer reassignment with open workload counts, reason/revision/region/closed-case checks and immediate backend scope changes; versioned actual compliance evidence uploads/downloads with hashes, submission prerequisite and explicit human verification. Replacement files clear the old submission description and reopen verification. Per-obligation form state is isolated. In-review metrics/filter now agree.

Preview 2 uses the same React screens plus an explicitly separate IndexedDB rehearsal adapter in frontend/preview. It simulates workflows and account scopes, retains files in this browser, and supports reset. It is NOT a deployed FastAPI backend, shared cross-device database, secure multi-user identity, or running scheduler. Do not certify server permissions from it. The normal frontend build excludes the adapter; preview build script adds it separately.

TEST_CHECKLIST.md contains numbered steps, expected results, actor/case details, architecture mappings, backend-only checks and unfilled user acceptance boxes. Explain changed test IDs before subsequent features; run relevant automated tests, update docs, push only test and republish this same Site. No keys required for this release.

Remaining: full APH validation, workload recommendations/expertise/conflicts, committee/hearing/SAC/SHC engines, OCR, live integration providers and full hosting of the Python backend. No Railway work is authorised for this preview.

## Module 0 update — 1 November 2026

Foundation hardening is complete on `test`: validated environment settings, request correlation and structured access logging, operational database indexes with an idempotent migration, and regression tests for the new contracts. Backend tests pass 16/16; frontend tests pass 10/10; typecheck and production build pass. Existing npm audit findings remain outside this module's scope.

Follow-up hardening resolved the frontend audit findings, bounded client-provided request IDs, and made Docker use migration-first startup with `AUTO_CREATE_SCHEMA=false`; local and test startup retain automatic schema creation.

## Module 1 update — identity and authorization foundation

Added persisted active role memberships scoped by role, region, and institution, with `/api/me/roles`. Case and reviewer access now require matching active memberships, and secure-cookie configuration uses validated settings. Migration `0003` is compatible with the existing initial `create_all` bootstrap. Backend tests pass 17/17; frontend behavior remains unchanged.

Module 2 adds persistent versioned rule sets with source/effective date/status, validated draft publishing for national oversight, and application binding to the latest effective published rules. Existing cases retain their stored route/version; unstarted future rules are not selected.

Module 3 adds persisted document MIME/size metadata, shared upload validation for application and compliance files, and constrained safe download filenames. Migration `0005` is bootstrap-compatible; document storage remains database base64 for this demo and should move behind object storage before production.

Module 4 adds structured scrutiny findings with reviewer-only creation/closure, institution responses, optimistic revisions, and audit history. Migration `0006` is added; the existing broad correction transition remains compatible while finding-level workflow is introduced.

Module 5 adds durable assignment history, active reviewer conflict declaration/clearance, membership-based reviewer eligibility, and migration backfill for existing application owners. Assignment remains manual and coordinator-confirmed; automatic expertise/capacity recommendations remain deferred.

Module 6 adds EVC participant assignment, acceptance/decline, conflict handling, and a two-member conflict-free quorum gate before EVC decision advancement. Expert appointment remains synthetic and committee/SAC/SHC procedures are still deferred.

Module 7 adds compliance clarification/rejection state, reviewer reason, verification actor/time metadata, and mandatory replacement evidence after clarification. Compliance status remains separate from application status; real obligation templates and statutory rules remain deferred.

Module 8 adds notification delivery lifecycle metadata and national-oversight retry for failed simulated deliveries. Deadline deduplication remains persistent; real provider adapters, retry backoff, and transactional outbox remain deferred.

Module 10 adds a reviewable document extraction foundation. Plain text is extracted deterministically; PDFs remain failed with an explicit OCR-not-configured error. Extracted content is never treated as authoritative until an authorized reviewer accepts it.

Module 11 adds database-backed readiness and a persistent deadline-worker heartbeat. Worker iteration failures are logged and exposed through heartbeat state; Docker/PostgreSQL runtime remains unverified locally.

Module 12 corrected the Docker Compose PostgreSQL URL to the installed psycopg driver format and validated it through configuration tests. Docker/PostgreSQL runtime remains unverified because Docker is unavailable locally.

Module 13 adds a Playwright browser smoke-test harness with mocked APIs and keyboard/accessibility checks. Vitest is scoped to `src`; browser execution remains pending until Playwright Chromium is installed.

The catalogue upgrade now exposes twenty populated application categories from the supplied workbook across four illustrative tracks. The frontend groups category selection by track, while legacy `new_course` and EoA slots remain compatible with existing seeded cases and tests.

The dashboard upgrade now gives institution, scrutiny officer, regional officer, and national oversight users distinct headings, guidance, primary actions, and metric labels. Unknown roles fall back safely; authorization remains server-enforced and unchanged.

Architecture persona foundation adds stage coordinator, stage member, and national verification demo identities. Stage-member access is limited to active EVC participant assignments; coordinator and national verification access is read-only pending dedicated workflow actions.

The stage and national verification foundation is tested at the API boundary: stage-member assignment isolation and read-only restrictions are enforced server-side, while dashboard differences are presentation-only until dedicated action models are added.
