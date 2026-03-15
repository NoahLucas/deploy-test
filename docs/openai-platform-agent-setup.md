# OpenAI Platform Setup For Historian + Autobiographer

## Recommendation

Use the OpenAI developer platform in this split:

- `Prompts` for versioned prompt assets
- `Agent Builder` for visual workflow iteration and debugging
- `Responses API` for production runtime
- `background=true` for nightly autobiography jobs

Do not build new platform work on `Assistants API`.

As of March 15, 2026, OpenAI documents that Assistants is deprecated and scheduled to shut down on August 26, 2026.

Sources:

- [Agent Builder](https://platform.openai.com/docs/guides/agent-builder)
- [Migrate to Responses](https://platform.openai.com/docs/guides/migrate-to-responses)
- [Background mode](https://platform.openai.com/docs/guides/background)
- [Deprecations](https://platform.openai.com/docs/deprecations)

## Repo assets

Prompt assets:

- [autobiographer.prompt.md](/Users/noah/Documents/New project/openai-platform/prompts/autobiographer.prompt.md)
- [historian.prompt.md](/Users/noah/Documents/New project/openai-platform/prompts/historian.prompt.md)

Agent Builder source-of-truth specs:

- [autobiographer-agent.json](/Users/noah/Documents/New project/openai-platform/agent-builder/autobiographer-agent.json)
- [historian-agent.json](/Users/noah/Documents/New project/openai-platform/agent-builder/historian-agent.json)

## How to mirror this into OpenAI

### 1. Prompts

Create two prompt assets in the OpenAI dashboard:

- `Autobiographer`
- `Historian`

Paste the prompt files from this repo into those prompt assets.

### 2. Agent Builder

Create two agents in Agent Builder:

- `Autobiographer`
- `Historian`

Mirror the corresponding JSON specs:

- purpose
- tool list
- recommended model
- workflow notes

### 3. Runtime

Keep runtime execution in this backend using the Responses API.

Why:

- your memory graph and provenance system live here
- your nightly note publishing lives here
- your Google Drive provenance export lives here

Agent Builder becomes the visual design surface, not the source of truth database.

## Background jobs

Nightly autobiography refreshes should use background Responses.

That is the correct OpenAI-platform primitive for:

- long yearly synthesis
- long monthly narrative rewrites
- provenance-heavy responses

## Evals and fine-tuning

Not yet.

The right sequence is:

1. collect real traces
2. collect good and bad outputs
3. build eval sets
4. improve prompts and tool schemas
5. only then consider fine-tuning if prompt + retrieval + tools plateau

That is especially true here because this system depends heavily on retrieval quality, provenance quality, and missing-memory handling. Fine-tuning too early would mostly hide problems instead of solving them.

## Current implementation status

Already true in code:

- backend uses Responses API
- autobiographer and historian have dedicated prompt modules
- nightly living-autobiography publish flow exists
- provenance export exists

Still to add:

- explicit background-mode submission and polling for nightly autobiography jobs
- more complete tool surface between backend memory graph and Agent Builder workflows
- eval datasets once enough real memory traces exist
