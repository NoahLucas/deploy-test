# Apple Integration Matrix

## Objective

Use Apple platform capabilities to provide trusted, privacy-forward personal signals and premium UX for the AI-native stack.

## Integration table

| Capability | Primary Use | Surface | Priority | Notes |
|---|---|---|---|---|
| HealthKit | Local collection of wellness/activity metrics | iOS relay -> backend | P1 | Only aggregated values leave device |
| BackgroundTasks | Scheduled local aggregation + relay | iOS relay | P1 | Supports passive signal updates |
| Sign in with Apple | Identity and access controls | Lab | P2 | Better than shared password model |
| App Attest / DeviceCheck | Device trust for relay integrity | iOS relay/backend | P1 | Reduces spoofing risk |
| Keychain/Secure Enclave | Secure token and key handling | iOS relay | P0 | Core security requirement |
| Push Notifications | Private lab brief triggers/reminders | iOS app | P2 | Optional but high utility |
| Widgets/Live Activities | Ambient visibility of operator signals | iOS | P3 | Later enhancement |
| CloudKit (optional) | Private data sync for app state | iOS app | P3 | Only if needed beyond backend |

## Data policy

- Raw sensitive events stay on device
- Relay only transmits approved, coarse aggregates
- Device identity hashed before storage
- Public endpoints expose abstracted, non-sensitive outputs only

## Security controls

- Signed payloads (`timestamp.nonce.body`) and replay prevention
- Strict allowlist of accepted signal keys
- Request age and nonce validation
- Environment-specific shared secrets

## Rollout sequence

1. Harden iOS relay contract and signature flow
2. Replace stubs with real HealthKit aggregation
3. Add device attestation checks
4. Introduce authenticated private lab access path

## Risk areas

- Over-collection of data without clear product value
- Signal drift causing low-quality recommendations
- Missing redaction boundaries between private and public outputs
