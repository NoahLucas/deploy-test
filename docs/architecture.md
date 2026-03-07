# Architecture

## Data flow

1. Apple device gathers HealthKit and behavioral context locally.
2. iOS relay app sanitizes/aggregates data and signs payload.
3. Backend validates signature freshness and nonce uniqueness.
4. Backend drops unknown fields and stores only allowed aggregates.
5. OpenAI Responses API turns sanitized aggregates into a concise public narrative.
6. Frontend fetches a public-safe feed and renders adaptive signal cards.

## Privacy controls

- On-device aggregation before network transport.
- HMAC request signing (`timestamp.nonce.body`) to prevent spoofing.
- Replay prevention through nonce cache + max age window.
- Signal allowlist with numeric clamp/rounding.
- Device identifier hashing at ingest.
- No raw event stream exposure in public routes.

## OpenAI usage policy

- Server-side key management only.
- `store=false` on Responses API requests for transient narrative generation.
- Prompt rules prohibit outputting raw health values.
- Admin-gated refresh endpoint to prevent abuse.

## Apple platform integration model

- HealthKit for wellness/activity signals.
- App Attest + Sign in with Apple for identity and device trust.
- Optional HealthKit sharing controls to tune exactly which metrics are included.
- Optional local differential privacy/noise before upload for extra deniability.

## Surface contract

Public feed shape:

```json
{
  "headline": "Current operating signal: recovery 84/100, focus 91/100, balance 76/100.",
  "metrics": {
    "recovery": "84/100",
    "focus": "91/100",
    "balance": "76/100",
    "action": "Hold two 90-minute no-message blocks before noon."
  },
  "updated_at": "2026-02-25T21:00:00+00:00"
}
```
