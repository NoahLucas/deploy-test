# Squarespace-First Pipeline

## Why this pipeline

Keep the convenience of Squarespace (app + analytics + managed hosting) while running a serious product/design workflow with staging and controlled releases.

## Environments

- `Production`: `noahlucas.com`
- `Staging`: `staging.noahlucas.com`
- `Private lab`: `lab.noahlucas.com` (restricted)

## Release process

1. Strategy brief
- Define audience, message, and success metric.

2. Build on staging
- Implement layout/components/theme changes in staging.
- QA desktop/mobile + key browsers.

3. Content pass
- Final copy, metadata, OG image, link checks, CTA check.

4. Analytics check
- Confirm page tracking and conversion proxy visibility.

5. Promote to production
- Replicate approved changes to production.
- Add rollback notes.

6. Post-release
- Review first 24-72h traffic and engagement.

## Fast rollback

- Keep prior section/page duplicated before major edits.
- If regression occurs, restore previous duplicated version.

## Admin minimization

- One backlog for design/content experiments.
- One weekly ship window.
- One monthly architecture/performance maintenance pass.

## Ownership split

- Noah: priority and approval decisions.
- Codex: all implementation details, QA, and release operations.
