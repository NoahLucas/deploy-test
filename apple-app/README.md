# Noah Apple App (iPhone, Apple Watch, Apple Vision)

This folder contains a native SwiftUI app scaffold for `https://noahlucas.com` across:

- iOS (`NoahSite-iOS`)
- watchOS (`NoahSite-Watch`)
- visionOS (`NoahSite-Vision`)

The iOS and visionOS apps load the site in-app with `WKWebView`.  
The watchOS app provides a lightweight companion with refresh + quick-open actions.

## Generate the Xcode project

1. Install Xcode 15+ (required for visionOS target support).
2. Install XcodeGen if needed:

```bash
brew install xcodegen
```

3. Generate the project:

```bash
cd /Users/noah/Documents/New\ project/apple-app
xcodegen generate
```

4. Open `NoahSite.xcodeproj` in Xcode and run the scheme for your target device/simulator.

## Customize the URL

Edit:

- `Sources/Shared/SiteConfiguration.swift`

## Notes

- Apple Watch does not host full `WKWebView` content like iPhone/visionOS. The watch target is designed as a companion launcher + status surface.
- You may need to set your Team under `Signing & Capabilities` for each target before deploying to physical devices.
