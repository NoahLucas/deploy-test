# Native App Roadmap

## Objective

Build a native iOS control surface that operates the website stack in real time: endpoint controls, AI briefing workflows, and Squarespace event visibility.

## Implemented now

- iOS app `TabView` with:
  - Site tab (`WKWebView`)
  - Control Center tab (native API client)
- Native Control Center supports:
  - Admin token storage (local)
  - Endpoint toggle list + updates
  - Daily brief generation via OpenAI endpoint
  - Squarespace event feed visibility

## Next milestones

1. Apple auth inside app
- Sign in with Apple flow
- App Attest challenge + verify UI

2. Operational workflows
- Notes ideation/draft pipeline from app
- Decision journal create/list from app

3. Push + background
- Daily brief push notifications
- Background refresh for event and signal updates

4. Production hardening
- Keychain storage for tokens
- Device-bound auth and session rotation
- Error telemetry and crash reporting

## Key files

- `apple-app/Sources/AppleApp/iOS/IOSRootView.swift`
- `apple-app/Sources/AppleApp/iOS/ControlCenterView.swift`
- `apple-app/Sources/Shared/BackendClient.swift`
- `apple-app/Sources/Shared/BackendModels.swift`
- `apple-app/Sources/Shared/SiteConfiguration.swift`
