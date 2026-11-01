# Reuse and provenance

## Reused implementations

Dependencies are installed from their published packages; no third-party source files are vendored. Their licences/notices remain in the installed distributions.

| Component | Reused capability | Licence / upstream |
|---|---|---|
| transitions 0.9.3 | State machine and transition rejection | MIT — https://github.com/pytransitions/transitions |
| SQLAlchemy 2.1.6 | Transactions, ORM, database constraints and conditional updates | MIT — https://github.com/sqlalchemy/sqlalchemy |
| FastAPI / Starlette / Pydantic | HTTP API, dependency injection, request validation, uploads, cookies | MIT / BSD — see published distribution metadata |
| Alembic | Database migration runner | MIT — https://github.com/sqlalchemy/alembic |
| React / React DOM | Component rendering and state updates | MIT — https://github.com/facebook/react |
| Vite / TypeScript | Build and type checking | MIT / Apache-2.0 — upstream package metadata |
| Lucide React | Interface icons | ISC — https://github.com/lucide-icons/lucide |
| Python standard library | Password derivation, random sessions, hashing and dates | PSF licence |

Project-specific adapters and interface are newly authored against the user's specification. This is not a claim that the SIH repositories' engines were extracted.

## Same-PS repositories researched

- https://github.com/Tharun-Kumaran/SIH26262 — workflow and deadline designs. Inspected missing-rule acceptance, request-provided actor roles and separately committed audit writes; did not import source.
- https://github.com/anubhavkashyap12354-maker/sih26262-aicte-approval-monitor — compliance and route APIs. Inspected caller-provided role filters, index-decrement returns, and hardcoded 365-day renewals; did not import source.
- https://github.com/Gayathiri05-Cs/AICTE-Smart-Approval-Compliance-Management-System — interface/storage reference; did not import source.
- https://github.com/Aditya948351/SOUL_NETRA_1 — documentation concepts; claimed engine paths were not found in inspected tree; did not import source.
- https://github.com/theparthgupta/aicte_doc_verification — document-processing reference; did not import source.

GitHub metadata reported no recognised licence for these five repositories on 1 November 2026. Direct copying remains deferred pending clear permission. Their APH mappings, performance statements and security claims are not accepted as authoritative.
