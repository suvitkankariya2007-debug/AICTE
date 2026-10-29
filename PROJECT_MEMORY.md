# Project memory

Last updated: 2026-10-29

## Working agreement

- Active repository: suvitkankariya2007-debug/AICTE.
- All project changes and remote commits belong on branch `test` only.
- The assistant handles commits and remote updates; the user does not want to run local CLI commands.
- Read AGENTS.md and this file before continuing project work. Update this record when requirements, decisions, implementation status, or blockers change. Commit those updates on `test`.
- This is a curated project record, not a verbatim archive of all chats. Do not store credentials or authentication codes.

## Project direction

Build an AICTE approval workflow and institutional compliance monitoring application. Current context covers configurable approval routes, scrutiny and re-scrutiny, EVC scheduling and reports, compliance obligations, document validity, role-based dashboards, reminders, escalation, and audit history. The original complete problem statement has not been captured in this repository and must be obtained before claiming full requirement coverage.

## User requests and preferences

- Explain the complete solution architecture and workflow for implementation and PPT use.
- Produce separate downloadable workflow and architecture images, using the dark background, bright outlines, rounded boxes, and light connectors from the supplied slide references.
- Remove the Bug Mafias branding and irrelevant cropped content from diagrams.
- Build an initial frontend with complete page layouts and design specifications appropriate for an AICTE portal.
- Determine required roles, logins, and dashboards. A role toggle may be used for the prototype; production access must be enforced by the server.
- Review scope and improve the iteration using: 0.25 feasibility + 0.25 innovation + 0.20 dataset availability + 0.15 competitive advantage + 0.15 ability. Define scoring scales and evidence before assigning scores.
- Reference slide link supplied by user: https://canva.link/kbgxqb16k748grk . Its complete contents have not been verified in this repository.

## Confirmed progress

- Original repository gangrasshrikant0-ui/AICTE-AUTOMATE could be read, but connector writes returned HTTP 403.
- User supplied the replacement repository suvitkankariya2007-debug/AICTE.
- Branch `test` already existed there.
- Remote write and commit access succeeded: commit c1b8b3255b29eb0d29d4939a50f27b0d3a82b3e8 added AGENTS.md. Its contents were read back successfully.
- No application implementation, HTML deliverables, or completed diagrams have been verified in this repository during the current work. Prior user references to such files do not establish their availability or completeness.

## Next implementation steps

1. Read the current repository files and obtain the exact problem statement and any existing HTML/PPT artifacts.
2. Map requirements to roles, pages, data entities, workflow states, integrations, and acceptance criteria.
3. Build the smallest complete workflow slice, documenting prototype assumptions and sample rules.
4. Keep architecture diagrams, implementation documentation, and this record consistent with actual code.

## Continuity limits

ChatGPT does not guarantee that all independent chats automatically receive this file or the full conversation history. In a new chat, identify this repository and `test` branch and instruct the assistant to read AGENTS.md and PROJECT_MEMORY.md. Repository records are the shared source of project decisions; summaries must distinguish confirmed facts from proposals.
