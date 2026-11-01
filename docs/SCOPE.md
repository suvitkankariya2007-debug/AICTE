# Scope and requirements map

Latest user instruction: reuse properly where possible; defer substantial additional engines. Eight personas and the full prompt pack remain the target, not the implementation status.

| Prompt | Current release | Explicitly deferred |
|---|---|---|
| 0–1 Shared architecture/design | FastAPI + SQLAlchemy + React/Vite/TS; shared database, navy/white workspaces | Tailwind conversion, React Router URLs, complete feature folder refactor |
| 2 Identity/access | Institution, assigned scrutiny reviewer, regional actor, oversight, stage coordinator/member, national verification officer; server isolation | Official jurisdiction registry, production identity |
| 3 Canonical events | Shared case IDs, transactional audit writes, optimistic revisions, creation-key dedup | Full domain event bus, notification outbox/retry providers, full normalized 30-entity schema |
| 4 APH registry | Twenty illustrative versioned checklist/route configurations across four tracks, marked unverified | Clause import, rule approval UI, corrigenda, year matrix |
| 5 Submission | Track-grouped category selection, specific slots, draft, upload/download, completeness, resubmission | Full conditional questionnaire, bundling, official APH validation |
| 6 Pre-scrutiny | Required presence, PDF signature/text MIME/size checks, hashes | Malware scan, OCR, identity/ratio/area/regulatory numerical checks, AI draft |
| 7 Assignment/tasks | Regional reviewer assignment with workload counts, reason, revision check and scoped access | Automatic workload recommendation, expertise/conflicts, independent work-task lifecycle |
| 8 Dashboards | Eight architecture personas represented with role-specific dashboard copy; scoped application access for stage members, stage coordinators, and national verification | Complaints/referrals, pagination, analytics charts |
| 9 Clarification | Reasoned correction loop, versioned files, audit | Per-finding approval/closure and multiple simultaneous clarification records |
| 10 EVC/committees | Conditional EVC schedule/report gate | Expert appointment, availability/conflict/quorum, SHC/SAC/hearings |
| 11 National verification | Separate versioned verification record with national-only actions and audit trail | Mandatory national-stage routing, official registry integration |
| 12 Tracker | Route-driven status/colours/history, responsive scroll | Stage popovers, business calendar |
| 13 Complaints | Deferred entirely | Separate grievance engine |
| 14 Automations | Versioned undertaking/document evidence-file uploads and description submission and verification; expiry; deadline worker; simulated notices | Real SMS/payment/NBA, PDF certificates, AI report, validated regulations |
| 15 QA | HTTP/database tests, typecheck/build, frontend DOM interaction checks | Full real-browser E2E and visual QA, PostgreSQL/Docker execution, full security/accessibility audit |

## Key invariants

- National oversight does not automatically confer approval power.
- An assigned reviewer cannot grant/reject a demo decision. Regional demo actor can, only from decision stage.
- Route engine rejects absent edges, unknown targets, stale and concurrent updates.
- Correction returns explicitly to scrutiny after institution submission; no decrementing stage index.
- Evidence upload retains old documents. Compliance reference submission remains separate from verification.
- A document renewal does not alter expiry until reviewer verification. The proposed date is used; no automatic +365 days.
- Closed undertakings stop alerting. Verified documents continue expiry monitoring.
- Alert deduplication includes record revision, deadline and escalation level. Alerts/logs and workflow changes commit together.
- Illustrative day thresholds and region names are never represented as verified APH requirements.

## Known demo limitations

File screening is preliminary; there is no malware scanner or sophisticated PDF content validation. Uploads use base64 database storage with a 2 MB limit, not production object storage. Audit records have no mutation API but are not cryptographically tamper-proof against database administrators. Login cards and shared public demo credentials deliberately make this unsuitable for public production use. No provider failure/retry behaviour is claimed because all deliveries are local simulations. Worker is a separate process; start it explicitly. Schema bootstrap uses create_all for easy demo runs; Alembic initial migration is provided and tested.

Preview 2 uses the same React screens with a separate browser-local rehearsal adapter. The FastAPI backend remains the authoritative implementation. No Railway deployment. See TEST_CHECKLIST.md for test boundaries.
