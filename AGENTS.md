# AICTE-AUTOMATE Project Context

## Repository and branch rules

- Repository: `suvitkankariya2007-debug/AICTE`
- Active development branch: `test` (tracks `origin/test`).
- Make and commit project changes on `test` only.
- Before writing or pushing, verify the active branch is `test`.
- Never commit, push, merge into, or edit `main` unless the user explicitly asks.
- Push the current `test` branch to `origin/test`; do not push another branch.

## Project purpose

Build an integrated AICTE approval workflow and institutional compliance monitoring platform. Route applications through configurable APH stages; track scrutiny, re-scrutiny, EVC scheduling and reports; monitor time-bound undertakings and document validity; provide role-based dashboards; send deadline reminders and authorised escalations; and retain a complete audit trail.

The platform supports administrative work. It must not replace statutory scrutiny, inspection, verification, or decisions reserved for competent authorities.

## Product rules

- Make routes and timelines configurable, versioned, and traceable to an approved rule source and effective date.
- Different application types may have different routes. Do not assume one universal route.
- Model SAC and SHC as distinct procedures.
- Keep application processing, compliance obligations, and document validity as separate status areas.
- A submission is not accepted compliance until an authorised official verifies it.
- Preserve document versions, action reasons, deadline changes, notification outcomes, and actor/time audit records.
- Enforce access on the server by role, assignment, and jurisdiction; a UI role toggle is only a demo.
- Use fictional or approved data only. Do not claim live AICTE data access or integration without authorization.
- AI may assist with extraction or summaries, with human confirmation. It must not make approval or compliance decisions.

## Build and delivery

- Start with the smallest end-to-end workflow slice and maintain runnable setup instructions.
- Document required environment variables without committing secrets.
- Include acceptance checks for routing, permissions, deadline logic, duplicate notification prevention, evidence verification, audit history, and integration failures.
- Clearly label prototype data and unvalidated sample rules.
