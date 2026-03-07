# Add Fusion Engine Tab on noahlucas.com (Squarespace)

This patch keeps your existing website and adds `Fusion Engine` as a new top-level tab.

## 1) Create the page

In Squarespace:

- Go to `Pages`.
- Add a new page named `Fusion Engine`.
- Set URL slug to `fusion-engine`.
- Add a `Code` block and paste the contents of:
  - [squarespace/fusion-engine-page-content.html](/Users/noah/Documents/New%20project/squarespace/fusion-engine-page-content.html)

## 2) Add the tab to desktop + mobile nav

In Squarespace:

- Go to `Settings -> Developer Tools -> Code Injection -> Footer`.
- Paste the contents of:
  - [squarespace/fusion-engine-nav-injection.js](/Users/noah/Documents/New%20project/squarespace/fusion-engine-nav-injection.js)

This script targets your current live nav structure (`Home`, `Bio`, `Notes`, `Holocron`) and appends `Fusion Engine` in both header and mobile menu.

## 3) Apply matching styles

In Squarespace:

- Go to `Design -> Custom CSS`.
- Paste:
  - [squarespace/fusion-engine-custom-css.css](/Users/noah/Documents/New%20project/squarespace/fusion-engine-custom-css.css)

## 4) Verify

- Desktop header now includes `Fusion Engine`.
- Mobile overlay menu includes `Fusion Engine`.
- `/fusion-engine` marks the tab active.
- The page renders fallback values if `/api/v1/public/feed` is not wired yet.

## Notes

- Your current live nav markup was verified from `https://noahlucas.com` with selectors:
  - `.header-nav-list`
  - `.header-menu-nav-wrapper`
- If you later add Fusion Engine directly in Squarespace navigation, remove the injection script to avoid duplicate tabs.
