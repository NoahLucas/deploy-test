# Private Lab Spec (`lab.noahlucas.com`)

## Objective

Provide a private, AI-native operating workspace for work use cases without exposing internal experimentation publicly.

## Access model

- v1: password-protected page(s)
- v2 (optional): member area with allowlisted accounts

## Core modules (v1)

- Daily Brief
  - Top priorities
  - Risks/blockers
  - Suggested actions

- Decision Journal
  - Decision
  - Context
  - Tradeoffs
  - Follow-up check date

- Prompt Library
  - Reusable prompts by workflow
  - Product strategy, roadmap, writing, leadership comms

- Experiment Tracker
  - Hypothesis
  - Experiment design
  - Outcome
  - Decision (keep/iterate/drop)

## Data handling

- No sensitive company details in public domain
- Manual curation only for v1
- If AI API integrations are added later, use strict redaction rules and least-privilege tokens

## UX requirements

- Fast load
- Keyboard-friendly interaction
- Simple mobile readability
- Clearly separate "private" from public brand pages

## Launch gates

- Access restriction verified
- No index directive for private pages
- Robots exclusions confirmed
- Internal links audited (no accidental public leakage)
