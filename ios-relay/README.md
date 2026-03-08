# iOS Secure Signal Relay

This folder contains a Swift starter for relaying privacy-safe Apple metrics to the backend.

## Intended runtime model

1. Collect HealthKit metrics locally.
2. Aggregate to coarse daily values on device.
3. Sign payload with relay secret and attach nonce/timestamp headers.
4. Send to `POST /api/v1/apple/ingest`.
5. Attach Apple client context (`bundle_id`, `app_version`, `ios_version`) and optional attestation token.

## Hardening before production

- Add App Attest verification and reject untrusted devices.
- Use Sign in with Apple identity token checks on backend.
- Keep relay secret in secure enclave/keychain with rotation strategy.
- Gate relay on explicit user consent and a visible privacy policy.

## Signal policy recommendation

Only include broad metrics such as:

- `sleep_hours`
- `resting_hr`
- `steps`
- `mindful_minutes`
- `deep_work_minutes`
- `screen_time_hours`

Do not upload granular timestamped event data.
