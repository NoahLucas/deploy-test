# noahlucas.com GPT + Google Drive Pipeline

## Choice

Choose Google Drive over iCloud for the provenance layer.

Why:

- Google Drive has a well-supported developer API and predictable folder/file semantics.
- It is much easier to automate export, sync, indexing, and inspection.
- OpenAI’s platform can work cleanly with external document stores through retrieval and MCP-style tool patterns.

For this system, iCloud is better as a personal storage surface.
Google Drive is better as an auditable developer-platform substrate.

## Architecture

1. Apple and manual sources create autobiographer memories.
2. Backend normalizes those into memory events, scenes, chapters, and revisions.
3. Provenance export writes a canonical yearly package into a Drive-sync folder.
4. `noahlucas.com` can query a GPT endpoint that answers from those records with sources.
5. Later, the Drive corpus can be indexed directly for retrieval or connected through tool-based document access.

## Current implementation

Backend endpoints:

- `POST /api/v1/openai/site-memory-chat`
- `POST /api/v1/openai/provenance/export`

Config:

- `GOOGLE_DRIVE_SYNC_DIR`

Default export root:

- `content/google-drive-sync/autobiographer/<year>/`

Contents:

- `manifest.json`
- yearly chapter markdown
- revision markdown files

## Provenance principle

Every answer on the site should be able to point back to:

- a memory event
- a chapter
- a revision
- or a provenance manifest entry

This is what keeps GPT useful without turning it into a vibes machine.

## Why this aligns with official docs

OpenAI’s current docs recommend the Responses API as the primary surface for tool-using agent flows, including retrieval-style use cases, background execution, and webhooks.

Sources:

- [Responses API docs](https://platform.openai.com/docs)
- [Webhooks](https://platform.openai.com/docs/webhooks)

OpenAI also supports retrieval and connector-oriented patterns, including hosted tools and remote MCP servers, which fit a future Drive-backed memory corpus.

Sources:

- [Tools - File search](https://platform.openai.com/docs/guides/tools-file-search)
- [Remote MCP](https://platform.openai.com/docs/guides/tools-remote-mcp)

Google Drive is a suitable storage substrate because its API supports structured file management and app-specific storage patterns.

Sources:

- [Google Drive API](https://developers.google.com/workspace/drive/api/guides/about-sdk)
- [Store application data](https://developers.google.com/workspace/drive/api/guides/appdata)

## Next steps

1. Point `GOOGLE_DRIVE_SYNC_DIR` at a local Google Drive desktop-synced folder.
2. Export yearly provenance packages automatically after chapter/revision updates.
3. Add a site UI surface that queries `site-memory-chat`.
4. Later, connect the Drive corpus to retrieval directly instead of only file export.
