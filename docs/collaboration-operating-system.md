# Noah x Codex Operating System

## Outcome

Run `noahlucas.com` as a high-velocity personal-brand studio with minimal admin overhead, while keeping Squarespace for managed hosting, app editing, and built-in analytics.

## Collaboration stack

- Build + technical execution: Codex workspace (this repo)
- Website runtime/CMS/analytics/app: Squarespace
- Strategic ideation + writing loops: ChatGPT (desktop/mobile)
- Optional deeper automation: OpenAI API + Responses API tools (later phase)

## Correct OpenAI links

- ChatGPT macOS app and app integrations: https://help.openai.com/en/articles/10119604-work-with-apps-on-macos
- Tasks in ChatGPT: https://openai.com/index/introducing-tasks-in-chatgpt/
- Building agents with OpenAI tools: https://openai.com/index/new-tools-for-building-agents/
- Responses API docs: https://platform.openai.com/docs/api-reference/responses
- OpenAI platform docs home: https://platform.openai.com/docs/overview

## Roles

- Noah (Vision Owner)
- Codex (Operator): design systems, implementation, SEO, analytics instrumentation, publishing pipeline, QA
- ChatGPT (Strategist/Writer): rapid ideation, content iteration, first-draft generation

## Operating rhythm

- Daily (optional, 15 min)
- Capture ideas, wins, lessons, and experiments into Notes backlog
- Choose one post concept to draft

- Weekly (60 min)
- Review traffic, top pages, top referrers, and conversion proxies
- Publish 1-2 Notes posts
- Ship one design/content experiment to staging
- Promote one post on LinkedIn

- Monthly (90 min)
- Brand narrative audit (positioning, proof points, voice)
- Portfolio update (new projects, artifacts, speaking)
- Analytics trend review and quarterly bets

## Branch and environment model

- `main`: production-ready artifacts
- `staging`: active experiments and design R&D
- Squarespace production domain: `noahlucas.com`
- Squarespace staging domain: `staging.noahlucas.com` (recommended via connected subdomain)
- Private work subdomain: `lab.noahlucas.com` (password/member gated)

## Guardrails

- Production edits happen only after staging approval
- Every publish has a short changelog entry
- Reusable components and styles only; no one-off page hacks unless explicitly approved
- All content ideas go through the Notes pipeline and metadata template

## What “seamless” means here

- You provide direction and approvals
- Codex handles implementation and technical/admin work
- Editing content remains simple in Squarespace UI/app
- Analytics stay in Squarespace dashboards with an optional external layer later
