# AICTE prototype — staged acceptance checklist

Preview URL (keep this URL for every update):
https://aicte-workspace-preview-suvit.glassycalf256.chatgpt.site/

Branch: `test`. Rules, regions, accounts and deadlines are illustrative. This is a proposed workflow implementation; it is not validated against every APH clause.

## How completion is recorded

- Automated verification and user acceptance are different. A checked automated result does not mean the user accepted the feature.
- Keep each manual checkbox empty until the user performs the steps and confirms the expected result.
- If a test fails, record the stage/test ID, role, application ID, exact steps, expected result, actual result and screenshot. Do not paste credentials or real institutional documents.
- After every code update: run relevant automated checks, push to `test`, update this file and PROJECT_MEMORY.md, update the SAME preview Site, and tell the user which tests changed.
- The hosted Site is a browser-local interactive rehearsal. Keep **UI rehearsal**, **backend automated pass**, and **user acceptance** as distinct results. Server permissions/shared database are not proven by the rehearsal.

## Stage 0 — Choose the correct test environment

Release: `2026-11-01-r2` / Preview 2. Hosting: existing ChatGPT Site only. No Railway deployment is required or planned for this preview.

The Site is now an **interactive browser-local rehearsal**. It simulates the API operations using IndexedDB, retains synthetic uploads in this browser and lets you switch demo accounts. It is NOT connected to the Python backend. Do not use it to certify server security, cross-device synchronization, scheduled jobs or production readiness.

- [ ] P0.1 Open the same URL. Confirm the amber **Preview 2 · Interactive rehearsal** banner and Release `2026-11-01-r2` after login.
- [ ] P0.2 College West creates a draft. Logout and choose Officer West in the SAME browser; confirm the ID appears.
- [ ] P0.3 Refresh the page and confirm changes persist in this browser. Different devices/browsers have independent demo data.
- [ ] P0.4 Use **Reset demo** to restore fictional sample data. This deletes only browser-local rehearsal records/files.
- [ ] P0.5 Open **Testing guide** in the sidebar. The guide and this checklist must match the release.

Stages 1–7 below can be rehearsed in the Site except where marked BACKEND ONLY. Role restrictions in the rehearsal are simulated, not security controls. Direct API tests, true independent sessions/concurrency, backend restart and background-worker execution require the FastAPI application and are covered separately by automated tests. Never enter real institutional evidence in the rehearsal.

## Stage 1 — Identity, shared dashboards and region isolation

Accounts: College West, College East, Officer West, Officer East, Regional West, National oversight. Demo password: `DemoPass!2026`.

- [ ] A1.1 College West sees only Pune Demo Institute cases. College East sees only Eastern Demo Institute cases.
- [ ] A1.2 Officer West sees assigned West cases; Officer East sees assigned East cases.
- [ ] A1.3 National oversight sees both regions but has no decision action. Regional West can act only on West cases.
- [ ] A1.4 Open a West case/document URL while signed in as East: access is rejected, including direct API access; no evidence contents are returned. **Direct API proof: BACKEND ONLY.**
- [ ] A1.5 Logout and reopen a protected endpoint: authentication is required.
- [ ] A1.6 Dashboard totals agree with filtered application lists after refresh.

Architecture mapping: one canonical database, server-enforced role/assignment/jurisdiction scope. National overview does not confer approval authority. Broader multi-role memberships remain deferred.

## Stage 2 — Three checklists, drafts and route selection

- [ ] A2.1 New institution shows declaration, land evidence and building evidence.
- [ ] A2.2 New course shows declaration, programme proposal and faculty statement.
- [ ] A2.3 EOA shows declaration, prior approval and compliance declaration.
- [ ] A2.4 Submit with a required slot empty: precise missing-evidence error; case stays draft.
- [ ] A2.5 Upload a plain text/PDF into each slot and submit: same ID reaches scrutiny; reviewer sees it; institutional tracker updates.
- [ ] A2.6 EOA route excludes EVC. New course/new institution include EVC. Skipped stages must not appear completed.
- [ ] A2.7 Invalid file type, empty file, fake PDF header or >2 MB file: rejected without changing the record.

Architecture mapping: checklist and route depend on the selected category and version. These are only three illustrative configurations; the full APH registry, questionnaire and regulatory numerical checks are deferred.

## Stage 3 — Findings, correction, versioned uploads and resubmission

- [ ] A3.1 Officer requests correction with an empty reason: rejected.
- [ ] A3.2 Officer records a clear reason and requests correction: college sees Action required and the reason.
- [ ] A3.3 College replaces one document: old/new revisions remain downloadable; checksums and audit entries persist.
- [ ] A3.4 College resubmits: case returns explicitly to scrutiny and the reviewer sees the updated evidence.
- [ ] A3.5 **BACKEND ONLY:** Two sessions act on the same revision: one succeeds, the stale action receives a conflict; no duplicate audit transition is added.
- [ ] A3.6 Attempt a non-permitted stage jump: rejected; state and audit counts stay unchanged.

Architecture mapping: correction loop, transactional audit and optimistic concurrency. Per-finding simultaneous clarification records remain deferred.

## Stage 4 — EVC schedule/report gate and demo decision

- [ ] A4.1 Complete scrutiny for a new-course case: case enters EVC; EOA does not.
- [ ] A4.2 Try completing EVC without visit date/report: rejected.
- [ ] A4.3 Regional West saves visit date and report: case history records them and an institutional notice is generated.
- [ ] A4.4 Complete EVC with findings: case reaches decision.
- [ ] A4.5 Scrutiny Officer and National oversight cannot grant/reject. Regional West records the reasoned demo decision.
- [ ] A4.6 College sees final status and history. A closed case cannot jump back into scrutiny.

Architecture mapping: conditional EVC, evidence gates and authorised human demo decision. Expert appointment, quorum, SHC/SAC/appeal and hearings remain deferred; this is not the complete committee architecture.

## Stage 5 — Undertakings, actual evidence files, renewal and verification

New functionality in this update: versioned compliance files replace reference-only evidence as the submission prerequisite.

- [ ] A5.1 College opens Compliance & validity, uploads a small PDF/text proof and sees filename/revision.
- [ ] A5.2 Uploading a file leaves the obligation pending. Enter evidence description and submit: status becomes submitted, not verified.
- [ ] A5.3 Try submitting without a file: rejected. Institution cannot verify its own evidence.
- [ ] A5.4 Officer verifies submitted undertaking evidence: it becomes verified; actor/time appear in case history.
- [ ] A5.5 For a document, propose a future expiry different from one year. Before verification the old expiry remains. After verification the exact proposed date becomes authoritative.
- [ ] A5.6 Upload replacement compliance evidence: retain old revisions and reopen pending verification; East account cannot download West evidence.
- [ ] A5.7 Verified undertaking stops overdue reminders; renewed documents continue to be monitored for their next expiry.

Architecture mapping: approval conditions, submission versus verification, evidence provenance and document validity. Creation/configuration of arbitrary new obligations remains deferred.

## Stage 6 — Deadline checks, escalation, audit and persistence

- [ ] A6.1 National oversight runs deadline checks: seeded upcoming, overdue and escalated items generate the configured recipient notices.
- [ ] A6.2 Immediately repeat the check: zero duplicate notices.
- [ ] A6.3 College sees institutional notices, not internal official notices.
- [ ] A6.4 Each transition, file revision, submission, verification and alert has a case-linked actor/time/reason audit entry.
- [ ] A6.5 **BACKEND ONLY:** Backend restart preserves case status, evidence versions, obligation state and deduplication records.
- [ ] A6.6 **BACKEND ONLY:** Background worker is running and executes checks without pressing a UI button. A separate worker process is required.

Architecture mapping: configurable demonstration deadlines, recipient escalation, continuing monitoring and traceable actions. Delivery is simulated; real SMS/email and retry/outbox integration are deferred. Calendars are elapsed days, not validated statutory working-day calculations.

## Stage 7 — Reviewer assignment (NEW)

Actors: Regional West, Officer West, Dr. Kavya Rao (Officer West 2).

- [ ] A7.1 Regional West opens a non-closed case. Eligible reviewers list shows only West scrutiny officers with current open-case counts.
- [ ] A7.2 Choose Dr. Kavya Rao and record a reason. Assignment saves; case origin region and stage do not change.
- [ ] A7.3 Former officer loses case access; the newly assigned officer sees it in My Work/applications.
- [ ] A7.4 East reviewer is unavailable; a forged cross-region assignment is rejected by the API.
- [ ] A7.5 Institution, ordinary officer and national oversight cannot reassign. Closed cases and stale revisions are rejected.
- [ ] A7.6 Audit shows old/new reviewer and reason; shared queues/counts update.

Architecture mapping: authorised assignment and scoped queues. This is manual, coordinator-confirmed assignment with workload counts; automatic expertise/capacity recommendations, conflicts and full task dependencies remain deferred.

## Automated evidence and release record

Previous release `eb89b89`: 10 backend scenarios, 4 frontend DOM tests, typecheck/build, SQLite migration and worker dedup passed. These do not establish user acceptance or full APH compliance.

Current results are recorded in docs/VERIFICATION.md; manual boxes remain unchecked until you confirm them. Browser visual review previously passed for the read-only dashboard; live browser E2E and PostgreSQL/Docker execution remain unverified.

## User acceptance record

| Release | Test IDs performed | Result | Defect/remarks | Confirmed by user |
|---|---|---|---|---|
| Initial release | None yet | Awaiting user acceptance | Read-only initial snapshot | No |
| Assignment/compliance-file update | None yet | Awaiting user acceptance | Preview 2: rehearse stages 5 and 7 | No |

## Recommended first pass — what to test before the next feature

1. **A7.1–A7.6:** Regional West (Priya Shah), `APP-DEMO-0402`, assign Dr. Kavya Rao. Former officer Dr. Meera Joshi loses it; Dr. Kavya Rao gains it. Region/stage stay unchanged.
2. **A5.1–A5.6:** College West (Ananya Deshmukh), upload `proof.txt` for the undertaking. Upload stays pending, submit becomes submitted, Regional West verification closes it. Repeat with lease and a future date; expiry changes only on verification.
3. **A3.1–A3.4:** A newly created EOA application: correction reason, replacement version, resubmission to scrutiny.
4. **A4.1–A4.5:** New-course application requires EVC date/report; EOA omits EVC.
5. **A6.1–A6.4:** National oversight runs deadline checks twice; inspect notices and audit. Second run creates zero duplicates.

Fault format: `A7.3 | Dr. Meera Joshi | APP-DEMO-0402 | expected hidden after assignment | actual still visible | screenshot`.

A UI rehearsal pass is not automatically a backend acceptance pass. Report either explicitly.
