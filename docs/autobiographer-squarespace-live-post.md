# Autobiographer Squarespace Live Post

## Recommendation

Use a single Squarespace blog post or page as the public shell for the autobiography, but treat this app as the source of truth for the body content.

That gives you:

- one stable Squarespace URL to share with family
- continuous revisions as new memories arrive
- yearly chapter permalinks when you want to preserve a finished version

## Canonical endpoints

- Live in-progress autobiography: `/api/v1/public/autobiography/live`
- Finished yearly chapter: `/api/v1/public/autobiography/{year}`

These endpoints return the same structured payload as note drafts:

- `title`
- `slug`
- `summary`
- `body_markdown`
- `meta_title`
- `meta_description`
- `social_quotes`
- `generated_at`

## Squarespace setup

### Best practical pattern

1. Create one Squarespace page or blog post called `Autobiography`.
2. Add a Code Block or embed that fetches `/api/v1/public/autobiography/live`.
3. Render the returned `title`, `summary`, and `body_markdown`.
4. Keep the Squarespace page as the stable public URL while the underlying story updates from this system.

### Year freeze pattern

At the end of a year:

1. Publish the finished yearly chapter via `/api/v1/lab/autobiographer/publish-year-note`.
2. Link the Squarespace shell page to `/api/v1/public/autobiography/{year}` or copy that version into a locked yearly post.

## Product note

As of March 14, 2026, this repo does not yet include a direct Squarespace write/update integration for standard blog posts.
The safe current architecture is:

- this backend writes and revises the autobiography
- Squarespace displays the latest canonical version
