# noahlucas.com Rebuild

A premium adaptive personal site with a privacy-first backend for Apple signal ingestion and OpenAI-generated operating intelligence.

## What is included

- `site/`: High-end responsive frontend personalized to Noah's experience.
- `backend/`: FastAPI API for secure ingest, signal aggregation, and public-safe feed generation.
- `ios-relay/`: Swift starter for on-device aggregation + signed relay.
- `docs/`: Architecture and Squarespace migration guide.

## Core capabilities

- Adaptive, intentional visual design with motion and responsive layouts.
- Signed ingest pipeline for Apple-derived aggregates.
- Strict allowlist sanitization for incoming signal keys.
- Public feed endpoint that never returns raw private telemetry.
- OpenAI Responses API integration for concise narrative insight generation.
- Realtime session bootstrap endpoint for future voice/agent interfaces.

## Local run

```bash
cd /Users/noah/Documents/New\ project
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --app-dir backend
```

Open:

- Website: `http://127.0.0.1:8000/`
- Health: `http://127.0.0.1:8000/health`
- Public feed: `http://127.0.0.1:8000/api/v1/public/feed`

## API summary

- `POST /api/v1/apple/ingest`
  - Requires `X-Relay-Timestamp`, `X-Relay-Nonce`, `X-Relay-Signature`
  - Accepts Apple client context fields (`bundle_id`, `app_version`, `ios_version`, optional `attestation_token`)
  - Body: `{ device_id, collected_at, signals, bundle_id?, app_version?, ios_version?, attestation_token? }`
- `POST /api/v1/apple/identity/verify`
  - Verifies Sign in with Apple identity token and returns normalized identity claims for lab auth workflows.
- `POST /api/v1/apple/app-attest/challenge`
  - Issues a one-time App Attest challenge bound to a device hash.
- `POST /api/v1/apple/app-attest/verify`
  - Validates challenge consumption and attestation payload structure (mode-based enforcement).
- `GET /api/v1/public/feed`
  - Returns safe headline + abstracted scores only.
- `GET /api/v1/public/notes-drafts`
  - Returns generated notes draft summaries from `content/notes-drafts`.
- `GET /api/v1/public/notes-drafts/{slug}`
  - Returns a generated note draft payload by slug.
- `POST /api/v1/intel/refresh`
  - Requires `X-Admin-Token`
  - Regenerates public feed via OpenAI (falls back safely if unavailable).
- `POST /api/v1/openai/realtime-session`
  - Requires `X-Admin-Token`
  - Creates OpenAI Realtime ephemeral session server-side.
- `GET /api/v1/openai/editorial-memory`
  - Requires `X-Admin-Token`
  - Lists stored editorial memory themes used in generation.
- `POST /api/v1/openai/editorial-memory`
  - Requires `X-Admin-Token`
  - Upserts editorial memory (`theme`, `notes`).
- `POST /api/v1/openai/notes/ideate`
  - Requires `X-Admin-Token`
  - Generates structured Notes ideas via OpenAI.
- `POST /api/v1/openai/notes/draft`
  - Requires `X-Admin-Token`
  - Generates a publish-ready markdown note package via OpenAI.
- `POST /api/v1/openai/notes/save`
  - Requires `X-Admin-Token`
  - Saves a draft payload to `content/<subdir>/` as markdown + JSON.
- `POST /api/v1/openai/notes/pipeline`
  - Requires `X-Admin-Token`
  - Runs ideation + draft generation + optional file save in one request.
- `POST /api/v1/lab/daily-brief`
  - Requires `X-Admin-Token`
  - Generates a structured AI daily brief for private operator workflows.
- `POST /api/v1/squarespace/webhooks`
  - Squarespace webhook ingestion endpoint with signature verification.
- `GET /api/v1/admin/squarespace/events`
  - Requires `X-Admin-Token`
  - Lists recent webhook events captured from Squarespace.
- `POST /api/v1/lab/decision-journal`
  - Requires `X-Admin-Token`
  - Persists a decision journal entry.
- `GET /api/v1/lab/decision-journal`
  - Requires `X-Admin-Token`
  - Returns recent decision journal entries.
- `GET /api/v1/admin/endpoints`
  - Requires `X-Admin-Token`
  - Returns managed endpoint activation states.
- `POST /api/v1/admin/endpoints/toggle`
  - Requires `X-Admin-Token`
  - Enables/disables a managed endpoint.
- `POST /api/v1/admin/apple/connect`
  - Requires `X-Admin-Token`
  - Verifies Apple identity token in admin control flow.
- `POST /api/v1/admin/openai/connect`
  - Requires `X-Admin-Token`
  - Configures and validates OpenAI runtime connectivity.
- `POST /api/v1/agents/chief/dispatch`
  - Requires `X-Admin-Token`
  - Creates a Chief-of-Staff run and task graph from a mission/context.
- `GET /api/v1/agents/runs`
  - Requires `X-Admin-Token`
  - Lists recent orchestration runs.
- `GET /api/v1/agents/runs/{run_id}`
  - Requires `X-Admin-Token`
  - Returns one run and its task list.
- `POST /api/v1/agents/tasks/{task_id}`
  - Requires `X-Admin-Token`
  - Updates task status/output and auto-closes run when all tasks complete.
- `POST /api/v1/agents/runs/{run_id}/execute`
  - Requires `X-Admin-Token`
  - Executes queued/draft tasks server-side and persists outputs.
- `GET /api/v1/lab/weekly-snapshot`
  - Requires `X-Admin-Token`
  - Returns 7-day execution + content + signal snapshot for operator review.

## Security posture

- HMAC-signed relay payloads with timestamp + nonce replay protection.
- Device identifiers are HMAC-hashed before storage.
- Unknown/unapproved signal keys are dropped.
- Only aggregated values are persisted.
- Public endpoint emits high-level scores and actions, never raw source records.
- Optional strict Apple context checks can enforce allowlisted bundle IDs and attestation token presence.
- Sign in with Apple identity token verification is available through Apple JWKS and audience/issuer checks.
- Endpoint-level activation toggles are available through admin routes and enforced by middleware.
- Agent run/task records are persisted for orchestration auditability.

## Deployment notes

1. Deploy `backend/` to a Python host (Fly.io, Render, Railway, or container infra).
2. Keep `OPENAI_API_KEY`, `ADMIN_TOKEN`, and `RELAY_SHARED_SECRET` in host secrets.
3. Point `noahlucas.com` DNS to the new host or reverse proxy through your edge.
4. Use [docs/squarespace-migration.md](docs/squarespace-migration.md) for phased cutover.
