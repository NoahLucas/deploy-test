# Squarespace Migration Playbook

## Goal

Move `noahlucas.com` from a Squarespace-rendered site to this custom stack with near-zero downtime.

## Recommended cutover approach

1. **Build and verify off-domain**
   - Deploy backend to a staging URL (`staging.noahlucas.com` or provider subdomain).
   - Validate `/health`, `/api/v1/public/feed`, and site rendering.

2. **Keep email untouched**
   - Preserve current MX records in Squarespace DNS during DNS edits.

3. **Switch root traffic**
   - Update `A/AAAA/CNAME` for `noahlucas.com` and `www` to your new host.
   - Use low TTL (300s) 24 hours before cutover.

4. **Monitor and rollback window**
   - Keep old Squarespace site active for 24-48 hours.
   - If needed, restore prior DNS records for immediate rollback.

5. **Decommission old rendering**
   - After stable traffic and analytics confirmation, remove Squarespace page publishing.

## Production checklist

- [ ] `OPENAI_API_KEY` present on host.
- [ ] `RELAY_SHARED_SECRET` rotated and unique per environment.
- [ ] `ADMIN_TOKEN` generated from strong random source.
- [ ] CORS includes only trusted origins.
- [ ] HTTPS and HSTS enabled.
- [ ] Rate limits configured for ingest and admin endpoints.
- [ ] Error telemetry enabled (Sentry or equivalent).
