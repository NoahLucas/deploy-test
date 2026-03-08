# OpenAI + Apple Platform Quickstart

## New backend capabilities

- OpenAI-backed Notes ideation endpoint
- OpenAI-backed Notes draft endpoint
- Editorial memory store for consistent brand voice
- Apple client context validation hooks for relay ingest

## Environment variables

Add these to `.env`:

- `OPENAI_API_KEY`
- `OPENAI_MODEL` (default `gpt-5`)
- `OPENAI_REALTIME_MODEL` (default `gpt-realtime`)
- `OPENAI_REALTIME_VOICE` (default `alloy`)
- `ADMIN_TOKEN`
- `RELAY_SHARED_SECRET`
- `ENFORCE_APPLE_CONTEXT` (`true` or `false`)
- `APPLE_ALLOWED_BUNDLE_IDS` (comma-separated bundle IDs)
- `REQUIRE_APPLE_ATTESTATION_TOKEN` (`true` or `false`)
- `APPLE_IDENTITY_AUDIENCE` (Sign in with Apple client ID / audience)
- `APPLE_IDENTITY_ISSUER` (default `https://appleid.apple.com`)
- `APPLE_IDENTITY_JWKS_URL` (default `https://appleid.apple.com/auth/keys`)
- `APPLE_APP_ATTEST_MODE` (`off`, `basic`, or `strict`)
- `APP_ATTEST_CHALLENGE_TTL_SECONDS` (default `300`)

## OpenAI content endpoints

All require `X-Admin-Token`.

## Upsert editorial memory

`POST /api/v1/openai/editorial-memory`

```json
{
  "theme": "operator voice",
  "notes": "short, direct, evidence-driven, no fluff"
}
```

## Ideate notes

`POST /api/v1/openai/notes/ideate`

```json
{
  "context": "Generate ideas for VP Product + entrepreneur audience around AI-native org design.",
  "count": 8
}
```

## Draft note

`POST /api/v1/openai/notes/draft`

```json
{
  "brief": "Write a playbook on using weekly product reviews to improve leadership bandwidth and execution speed.",
  "target_words": 1000
}
```

## Save draft artifact

`POST /api/v1/openai/notes/save`

```json
{
  "draft": {
    "title": "Example",
    "slug": "example",
    "summary": "Example summary",
    "body_markdown": "# Heading",
    "meta_title": "Example meta title",
    "meta_description": "Example meta description",
    "social_quotes": ["q1", "q2", "q3"]
  },
  "subdir": "notes-drafts"
}
```

## One-call pipeline

`POST /api/v1/openai/notes/pipeline`

```json
{
  "context": "Generate ideas for VP Product brand growth around AI-native org design.",
  "count": 8,
  "draft_idea_index": 0,
  "target_words": 1000,
  "save_to_disk": true,
  "subdir": "notes-drafts"
}
```

## Apple ingest contract

`POST /api/v1/apple/ingest` accepts:

- `device_id`
- `collected_at`
- `signals`
- `bundle_id` (optional unless enforcement enabled)
- `app_version` (optional unless enforcement enabled)
- `ios_version` (optional unless enforcement enabled)
- `attestation_token` (optional, reserved for later verification phase)

Headers (required):

- `X-Relay-Timestamp`
- `X-Relay-Nonce`
- `X-Relay-Signature`

Headers (recommended):

- `X-Apple-Bundle-ID`
- `X-Apple-App-Version`
- `X-Apple-IOS-Version`
- `X-Apple-Attestation-Token`

## Apple identity verification (Sign in with Apple)

`POST /api/v1/apple/identity/verify`

```json
{
  "identity_token": "<apple_id_token>",
  "nonce": "optional-raw-nonce"
}
```

Notes:

- `APPLE_IDENTITY_AUDIENCE` must match your iOS/web client identifier.
- Verification uses Apple JWKS + issuer/audience checks.
- If `PyJWT` is not installed yet, endpoint returns a runtime config error.

## Apple App Attest endpoints

- `POST /api/v1/apple/app-attest/challenge`
- `POST /api/v1/apple/app-attest/verify`

`basic` mode validates challenge flow + payload structure.
`strict` mode intentionally fails until full cryptographic attestation verification is implemented.

## Private lab endpoints

All require `X-Admin-Token`.

- `POST /api/v1/lab/daily-brief`
- `POST /api/v1/lab/decision-journal`
- `GET /api/v1/lab/decision-journal`

## Integration control endpoints

All require `X-Admin-Token`.

- `GET /api/v1/admin/endpoints`
- `POST /api/v1/admin/endpoints/toggle`
- `POST /api/v1/admin/apple/connect`
- `POST /api/v1/admin/openai/connect`

## Integration control UI

Use local pages:

- `/lab.html` for operator workflows
- `/integrations.html` for Apple/OpenAI connect + endpoint toggles

## Current Apple security level

- HMAC signature and nonce replay prevention are active.
- Optional allowlist check for bundle IDs is available when `ENFORCE_APPLE_CONTEXT=true`.
- Optional attestation-token requirement is available when `REQUIRE_APPLE_ATTESTATION_TOKEN=true`.
- Full App Attest cryptographic verification is planned for next hardening phase.

## CLI runner

Run from workspace root while backend is live:

```bash
PYTHONPATH=backend .venv/bin/python backend/scripts/run_notes_pipeline.py \
  --base-url http://127.0.0.1:8000 \
  --admin-token \"$ADMIN_TOKEN\" \
  --context \"Generate ideas for AI-native VP Product leadership notes.\" \
  --count 8 \
  --draft-idea-index 0 \
  --target-words 1000
```

Daily brief runner:

```bash
PYTHONPATH=backend .venv/bin/python backend/scripts/run_lab_daily_brief.py \
  --base-url http://127.0.0.1:8000 \
  --admin-token \"$ADMIN_TOKEN\" \
  --priority \"Finalize homepage narrative\" \
  --priority \"Ship one high-signal note\" \
  --risk \"Context switching across too many themes\" \
  --context \"Focus on brand authority and weekly shipping velocity.\"
```
