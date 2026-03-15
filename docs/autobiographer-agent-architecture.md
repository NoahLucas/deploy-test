# Autobiographer Agent Architecture

## Goal

Build an autobiographer agent that continuously turns digital and sensor exhaust into a living family narrative.

The unit of authorship is:

- one chapter per year
- one continuously revised live autobiography surface
- many small memory events, scenes, and artifacts underneath

The product goal is not surveillance. It is remembrance:

- preserve what mattered
- surface the good stuff worth cherishing
- help future inference about meaning, growth, family life, and seasons of change

## Product shape

The autobiographer has three layers:

1. Capture
- Collect high-signal evidence from Apple platform data and other digital exhaust.

2. Memory graph
- Normalize events, cluster them into scenes, dedupe repeated exhaust, and maintain a longitudinal life record.

3. Narrative engine
- Use OpenAI to extract meaning, write revisions, preserve yearly chapters, and keep a live family-facing autobiography current.

## Platform architecture

### Apple-side capture

Primary Apple-native sources:

- HealthKit
- Core Location
- EventKit
- Photos metadata and selected media references
- Journaling Suggestions
- Motion/activity context
- WeatherKit
- App Intents / Shortcuts for explicit memory capture
- Sign in with Apple for identity
- App Attest for device trust

Recommended capture model:

1. On device, read the raw Apple data only with explicit user consent.
2. Convert raw records into compact autobiographical memory candidates.
3. Redact or aggregate sensitive fields before upload whenever possible.
4. Sign uploads and bind them to a trusted app/device identity.

Examples:

- HealthKit becomes "long walk with Sara in Ojai" or "great recovery week after hard travel," not a raw heart-rate dump.
- EventKit becomes "Willa birthday weekend blocked off with family dinner," not a blind calendar mirror.
- Core Location becomes meaningful place episodes and revisits, not a continuous breadcrumb trail.
- Photos become event anchors with timestamps and selected captions, not full library exfiltration by default.

### OpenAI-side inference

OpenAI should do the meaning-making, not the indiscriminate collection.

Recommended OpenAI stack:

- Responses API for the primary autobiographer brain
- built-in `file_search` for retrieval over life artifacts and prior chapters
- function calling for your internal memory services
- background mode for long-running yearly synthesis and timeline reconciliation
- webhooks for asynchronous completion of long-running narrative jobs
- Realtime API for future spoken memory capture, reflective interviews, and family storytelling sessions

## Memory model

The autobiographer should store more than flat notes.

### Core entities

- `memory_event`
- `memory_artifact`
- `scene_cluster`
- `person`
- `place`
- `year_chapter`
- `live_autobiography_revision`
- `source_connection`

### `memory_event`

Fields:

- `id`
- `occurred_at`
- `ingested_at`
- `source`
- `title`
- `detail`
- `people`
- `place`
- `tags`
- `confidence`
- `privacy_level`
- `sentiment_hint`
- `importance_score`
- `joy_score`
- `family_relevance_score`
- `evidence_refs`

### `memory_artifact`

Fields:

- `id`
- `source`
- `artifact_type`
- `uri`
- `captured_at`
- `checksum`
- `metadata_json`
- `embedding_ref`

### `scene_cluster`

A scene cluster is a higher-order unit such as:

- "moving to Ojai"
- "Willa's early childhood season"
- "joining Sift"
- "summer travel with family"

Fields:

- `id`
- `title`
- `start_at`
- `end_at`
- `memory_event_ids`
- `artifact_ids`
- `people`
- `place`
- `themes`
- `summary`

## Ingestion strategy

### Tier 1: Explicit memory capture

Highest quality, lowest ambiguity:

- quick-add note in iPhone app
- voice memo or typed reflection
- share sheet from Photos, Safari, Notes, Music, or Messages
- App Intent like `Remember this`

These should become first-class autobiographer memories immediately.

### Tier 2: Structured Apple exhaust

High signal with moderate inference:

- calendar events from EventKit
- reminders milestones
- HealthKit workout / sleep / mindfulness summaries
- significant locations and visits
- weather context for a place/time window
- selected photo moments

These should produce draft memory candidates, not final memories, until confidence is high.

### Tier 3: Ambient digital exhaust

Useful but noisy:

- notes and documents
- work artifacts
- email confirmations and travel receipts
- music listening patterns
- website publishing history
- app usage summaries

These should enrich retrieval and scene reconstruction more than direct narrative generation.

## Privacy boundary

The autobiographer should be privacy-maximal by default.

### Keep on device when possible

- full photo/video assets
- precise GPS history
- raw HealthKit samples
- contact graphs
- sensitive message bodies

### Sync server-side only as derived memory

- daily summaries
- scene candidates
- selected artifacts
- embeddings
- autobiographer-ready memory events

### Trust controls

- Sign in with Apple for identity continuity
- App Attest for trusted app/device lineage
- least-privilege Apple permission prompts
- per-source opt-in and per-source deletion
- privacy labels on every memory event

Apple’s current docs support this direction:

- HealthKit requires fine-grained authorization and encourages requesting only the data types you actually need. Source: [Authorizing access to health data](https://developer.apple.com/documentation/healthkit/authorizing-access-to-health-data)
- Health and fitness guidance emphasizes privacy, on-device processing, and using only essential frameworks/data. Source: [Health and fitness apps](https://developer.apple.com/health-fitness/)
- App Attest remains the right trust primitive for proving app legitimacy. Source: [Preparing to use the app attest service](https://developer.apple.com/documentation/devicecheck/preparing-to-use-the-app-attest-service)

## Narrative pipeline

### 1. Capture

Raw inputs enter a staging area with provenance:

- source
- device
- user consent scope
- confidence
- raw artifact reference

### 2. Normalize

Convert exhaust into autobiographer-ready memory events:

- normalize timestamps
- dedupe duplicates
- resolve person/place entities
- infer scene candidates
- score importance and family relevance

### 3. Retrieve

At generation time, retrieve:

- nearby events
- same people/place/theme events
- prior revisions
- yearly chapter drafts
- related artifacts

OpenAI’s official docs support using hosted retrieval via `file_search` in the Responses API for this layer. Source: [File search](https://platform.openai.com/docs/guides/tools-file-search)

### 4. Synthesize

Use OpenAI to produce:

- monthly chapter updates
- yearly chapter rewrites
- "good stuff to remember" capsules
- memory gaps and clarification questions
- family milestone summaries

For long-running yearly synthesis and reconciliation jobs, use background Responses. Source: [Background mode](https://platform.openai.com/docs/guides/background)

### 5. Publish

Publish into two surfaces:

- a live autobiography that keeps revising
- locked yearly chapters as historical snapshots

### 6. Reflect

The agent should also produce:

- weekly "moments worth keeping" summaries
- prompts to confirm or correct inferred memories
- suggested photo/caption pairings
- oral-history interview prompts for you and Sara

## Agent behaviors

The autobiographer should have five explicit modes:

### Archivist

- organizes sources
- resolves duplicates
- protects provenance

### Memory Curator

- ranks what matters
- highlights joy, tenderness, courage, growth, and family meaning

### Biographer

- writes in a grounded narrative mode
- preserves ambiguity when facts are incomplete
- refuses to invent

### Interviewer

- asks for missing context when confidence is low
- turns inferred signals into confirmed memory

### Historian

- locks prior yearly chapters
- maintains revision history of the live autobiography

## OpenAI implementation notes

As of March 15, 2026, the OpenAI platform pieces that best fit this agent are:

- Responses API as the core orchestration surface
- hosted tools like `file_search`
- custom function tools for local memory services
- background mode for long-running jobs
- webhooks for completion events

OpenAI’s docs also note that the older Assistants API is deprecated after feature parity with Responses and is scheduled to shut down on August 26, 2026. This architecture should therefore center on Responses rather than Assistants. Source: [Assistants API tools](https://platform.openai.com/docs/assistants/tools)

Webhooks are the right async completion mechanism for background Responses. Source: [Webhooks](https://platform.openai.com/docs/webhooks)

## Proposed v1 build sequence

1. Apple memory capture app
- Add explicit quick-capture memory events.
- Add EventKit and HealthKit summary import.
- Add App Attest hardening.

2. Memory graph backend
- Add normalized memory tables for people, places, artifacts, and scene clusters.
- Add embedding and retrieval infrastructure.

3. Narrative jobs
- Add background yearly synthesis jobs.
- Add revision history for the live autobiography.
- Add "good stuff worth cherishing" extraction.

4. Family surface
- Publish one live autobiography page.
- Add yearly chapter archive.
- Add private family view later if needed.

## Concrete near-term repo changes

The next implementation wave should add:

- `autobiographer_memory_artifacts` table
- `autobiographer_scene_clusters` table
- `autobiographer_people` table
- `autobiographer_places` table
- `autobiographer_revisions` table
- background job runner for yearly synthesis
- Apple-source ingestion routes for EventKit and HealthKit summaries
- a memory review queue in `/lab.html`

## North star

In the best version of this product, your daughter can one day read a chapter for any year and feel:

- what life looked like
- what her family loved
- what you were building
- where you were becoming more yourself

That is the bar.
