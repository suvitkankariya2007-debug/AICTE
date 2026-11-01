# AICTE approval & compliance workspace — functional demo

Working on `test` only. Synthetic institutions, staff, routes and deadlines. This is not an official AICTE service. Rules are labelled `NEEDS_APH_VERIFICATION`.

## Included release

- Institution, assigned scrutiny reviewer, regional coordinator/decision actor, stage coordinator/member, national verification officer, and national oversight accounts; server-enforced scope.
- Twenty category-specific illustrative checklists across four evaluation tracks and two routes: Scrutiny → Decision, Scrutiny → EVC → Decision.
- Draft creation with request-key deduplication, secure evidence download, PDF/text upload checks, document versions and hashes.
- Correction → institutional resubmission → scrutiny. Findings/reasons are required for reviewer actions.
- EVC schedule and report record, blocking advancement until both exist. Full expert appointment is deferred.
- Human demo approval/rejection, protected against stage jumps and stale revisions.
- Undertaking and document registers: versioned evidence **files and descriptions**, submission, authorised verification, actual renewal expiry date.
- Deadline worker, upcoming/overdue/escalated levels, persistent duplicate prevention and simulated delivery records.
- Navy/white interface, live API-derived counts, scoped queues, search, filters, route tracker and audit history. Polls shared records every ten seconds.

## Run locally

Python 3.12 and Node 24 are the tested versions. From repository root:

```sh
python -m venv .venv
.venv/bin/pip install -r backend/requirements.txt
npm ci --prefix frontend
npm run build --prefix frontend
.venv/bin/alembic -c backend/alembic.ini upgrade head
npm run dev
```

Open `http://localhost:8000`. Windows: activate the virtual environment, then run `python -m uvicorn app.main:app --app-dir backend --port 8000` instead of `npm run dev`.

SQLite is the local default. Set `DATABASE_URL` before starting for PostgreSQL. Environment values are read from the process environment; `.env.example` is documentation, not automatically loaded by the Python server. Docker Compose reads its declared environment.

Optional frontend development: `npm run dev --prefix frontend` (port 5173); proxy points to backend port 8000. Start the backend separately using the command above.

Frontend unit tests run with `npm test --prefix frontend`. Browser workflow tests run with `npm run test:e2e --prefix frontend`; from `frontend`, install the Playwright browser first with `npx playwright install chromium`.

Run one deadline sweep, or keep the worker running:

```sh
PYTHONPATH=backend .venv/bin/python -m app.worker --once
PYTHONPATH=backend .venv/bin/python -m app.worker
```

The worker runs every 60 seconds. National oversight's **Run deadline checks** button executes the same engine. No real email/SMS is sent. All delivery results say `simulated`.

`docker compose up --build` provides PostgreSQL, the app and the deadline worker. Docker/PostgreSQL execution is not yet locally verified; SQLite execution is verified.

## Demo accounts

All accounts use password `DemoPass!2026`; account cards appear on the demo login page.

| Username | Scope |
|---|---|
| college-west | Pune Demo Institute |
| college-east | Eastern Demo Institute; isolation check |
| officer-west | Assigned West Demo applications |
| officer-west-2 | Dr. Kavya Rao; initially unassigned West reviewer |
| officer-east | Assigned East Demo applications |
| regional-west | West Demo coordination and demo decisions |
| admin | National oversight and deadline checks; cannot decide cases |

Keep this release local. Demo mode is required; real provisioning, production login hardening and official authority mappings are deferred. Passwords are PBKDF2 hashed; sessions use random HttpOnly cookies, expire after eight hours, and are revocable on logout. Use HTTPS and `COOKIE_SECURE=true` if configuring a secured environment.

## Demonstration

1. College West → New application → Extension of approval. Upload one small `.txt` or valid PDF in each named slot; submit.
2. Logout → Officer West. Open the same ID, enter a review reason, request correction.
3. College West uploads replacement evidence; old versions stay visible. Resubmit.
4. Officer West records findings and completes scrutiny. Regional West records a demo decision.
5. For the EVC route use New course, or seeded `APP-DEMO-0402`: complete scrutiny, then Regional West records visit date/report before advancing to decision.
6. Compliance & validity: College West uploads a supporting file, submits an evidence description and, for renewal, a future expiry date. Regional West verifies it. Submission alone does not close it.
7. Admin runs deadline checks twice: first creates notices, second creates zero duplicates. A worker also runs the same checks when started separately.
8. Compare East and West account views; inspect the application audit trail.

## Tests

```sh
PYTHONPATH=backend .venv/bin/pytest backend/tests -q
npm test --prefix frontend
npm run build --prefix frontend
```

Backend tests exercise real HTTP handlers and a temporary SQL database, including separate sessions, restart persistence, concurrent transitions and failed-action rollback. Frontend interaction tests use jsdom and mocked API responses; they do not replace browser E2E testing. See `docs/VERIFICATION.md` for actual results and limitations.

## Reuse and remaining scope

See `docs/REUSE.md` for licensed foundations and external repository research. No unlicensed competitor source is copied into this release. See `docs/SCOPE.md` for precise prompt coverage and deferred features. This release is a complete small workflow slice, not completion of the entire 15-prompt specification.

## Preview and acceptance

Use the same URL after every update: https://aicte-workspace-preview-suvit.glassycalf256.chatgpt.site/

Preview 2 is an interactive **browser-local rehearsal**, not a deployed Python backend. Records and synthetic file contents stay in IndexedDB in the current browser; role checks are simulated. Switching demo accounts rehearses the handoff. Reset demo restores the samples. No Railway deployment is used. Do not use the Site to claim server security, shared cross-device data or running background tasks.

Test instructions and expected results are in [TEST_CHECKLIST.md](TEST_CHECKLIST.md). Start with reviewer assignment (stage 7) and evidence uploads (stage 5). Leave manual boxes unchecked until you have tested and confirmed them.

Build the separate rehearsal bundle: `npm run build --prefix frontend` then `node frontend/preview/build.mjs`. The normal production build does not include the preview adapter.
