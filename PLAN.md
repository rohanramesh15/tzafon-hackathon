
# PodPipe — Hackathon Plan

## What is it?
Juicebox for podcast guest discovery. A podcaster types a natural language description of who they want on their show, an AI agent browses Twitter/X to find matching people, and returns a ranked list of potential guests with personalized outreach DMs.

## One-liner pitch
"Describe your dream podcast guest → our agent browses Twitter and finds them for you."

---

## Current Status (as of May 9, 2026 — 2pm)

- [x] **Frontend (Person C)** — UI built via Magic Patterns, wired to backend via SSE, mock + real modes, filters, CSV export, detail sheet, copy DM, empty/searching/done/error states all handled
- [x] **Backend API (Person B)** — FastAPI server with `/health`, `POST /api/search`, SSE stream, CSV export; `parse_query` / `score_lead` / `generate_outreach` LLM logic; in-memory store; mock + real agent adapter
- [x] **Agent Core (Person A)** — `run_agent` / `run_agent_async` / `AgentConfig` exposed; KERNEL browser + Northstar CUA wired up; tested end-to-end (`test_results_20260509_131029.json` shows 2 real leads extracted from `@levelsio` + `@marckohlbrugge`)
- [ ] **Demo prep** — final 3-query rehearsal + screen recording backup still TODO

---

## Tech Stack

| Layer | Tool |
|-------|------|
| Frontend | **Magic Patterns** (via MCP) — generates all UI code |
| Agent model | **Northstar CUA Fast** (via Lightcone SDK — `pip install tzafon`) |
| Browser infra | **KERNEL** (cloud browsers — `@onkernel/sdk`) |
| Query parsing | Any LLM — extracts search params from natural language |
| Outreach generation | Any LLM — generates personalized DM drafts per lead |
| Backend API | Node.js or Python (FastAPI) — orchestrates agent loop, serves results |

---

## Architecture

```
[User types query]
       |
       v
[Backend API] — POST /api/search { query: string }
       |
       v
[LLM: Parse Query]
  - Input: raw user query
  - Output: { keywords: [], role: string, vibe: string, search_queries: [] }
  - Example: "bootstrapped SaaS founder, $1M ARR, tactical advice"
    → keywords: ["bootstrapped", "SaaS", "ARR", "founder"]
    → role: "founder"
    → vibe: "tactical"
    → search_queries: ["bootstrapped SaaS founder", "indie hacker ARR"]
       |
       v
[KERNEL: Spin up cloud browser] — Chrome instance in ~300ms
       |
       v
[Northstar Agent Loop]
   For each search_query:
     1. Navigate to twitter.com/search?q={query}
     2. Screenshot the page
     3. Northstar reads the screenshot, identifies profile links
     4. For each promising profile:
        a. Click into profile page
        b. Screenshot profile page
        c. Extract via Northstar or DOM: name, handle, bio, followers, pinned tweet
        d. Screenshot recent tweets section
        e. Extract 3-5 recent tweet texts
        f. Navigate back to search results
     5. Repeat for next profile (target: 5-10 total)
       |
       v
[LLM: Score + Generate]
  For each extracted profile:
  - Input: { user_query, profile_data, recent_tweets }
  - Output: { match_score (0-100), match_reason, outreach_dm }
  - Filter out anyone below 60% match
       |
       v
[Stream to frontend via SSE]
  - Event: { type: "status", message: "..." }
  - Event: { type: "lead", data: { ...lead } }
  - Event: { type: "done" }
       |
       v
[Frontend renders cards in real time as events arrive]
```

---

## API Contract

### `POST /api/search`
Kicks off a new search. Returns immediately.
```
Request:  { "query": "string" }
Response: { "search_id": "string" }
```

### `GET /api/search/:search_id/stream` (Server-Sent Events)
Frontend connects here and receives events as the agent works.

**Event types:**

1. Status update (agent activity):
```json
{ "type": "status", "message": "Parsing your query...", "step": "parsing" }
```
```json
{ "type": "status", "message": "Searching Twitter for 'bootstrapped SaaS founder'...", "step": "browsing" }
```
```json
{ "type": "status", "message": "Analyzing @johndoe's profile...", "step": "extracting" }
```

2. Lead found:
```json
{
  "type": "lead",
  "data": {
    "id": "lead_001",
    "name": "John Doe",
    "twitter_handle": "@johndoe",
    "twitter_url": "https://twitter.com/johndoe",
    "bio": "Bootstrapped a SaaS to $2M ARR. Writing about growth, PLG, and developer marketing.",
    "followers": 12500,
    "profile_image_url": "https://pbs.twimg.com/...",
    "match_score": 92,
    "match_reason": "Bootstrapped founder of a $2M ARR dev tools SaaS. Regularly tweets tactical threads about PLG and growth metrics.",
    "recent_tweets": [
      "Just crossed $2M ARR. Here's the 5 things that actually moved the needle...",
      "Hot take: most PLG advice is written by people who've never run a PLG company",
      "Thread: How we got our first 1000 users without spending a dollar on ads"
    ],
    "outreach_dm": "Hey John — I run [Podcast Name], a show about bootstrapped founders scaling without VC. Your thread on crossing $2M ARR was exactly the kind of tactical stuff our listeners love. Would you be open to a 30-min chat about your PLG journey? No prep needed."
  }
}
```

3. Done:
```json
{ "type": "done", "total_leads": 8 }
```

### `GET /api/search/:search_id/export`
Returns CSV download of all leads for that search_id.

Columns: `name, twitter_handle, twitter_url, bio, followers, match_score, match_reason, outreach_dm`

---

## Team Assignments

---

### 🔴 Person A — Agent Core (Northstar + KERNEL)

You own the agent that browses Twitter. This is the hardest and most critical piece.

**Setup:**
- [x] Sign up at `lightcone.ai/signup?campaign=HACKMAY9` (get $2,500 credits)
- [x] `pip install tzafon` and confirm API key works with a basic test
- [x] Sign up at `dashboard.onkernel.com/hackathon?code=KERNELHACKATHON2026`
- [x] Install KERNEL: `npm install -g @onkernel/cli` or use Python SDK
- [x] Run a hello-world: spin up KERNEL browser → take screenshot → send to Northstar → confirm you get an action back

**Core functions to build:**

`start_browser()` — implemented in `agent/kernel_browser.py` + `agent/browser.py`:
- [x] Spins up a KERNEL cloud browser
- [x] Returns browser instance + CDP connection
- [x] Set viewport to 1280x720 (what Northstar expects)
- [ ] If using a logged-in Twitter session, load the KERNEL persistent profile *(running unauthenticated — works for public profiles)*

`search_twitter(browser, query)` — *de-scoped*: pivoted to direct handle visits because LLM-suggested handles are higher quality than Twitter's search results:
- [ ] ~~Navigate to `twitter.com/search?q={query}...`~~ *(replaced with direct profile navigation)*
- [ ] ~~Wait for results to load~~
- [ ] ~~Screenshot the results page~~
- [ ] ~~Return the screenshot for profile extraction~~

`extract_profiles_from_search(browser, screenshot)` — *de-scoped*: handles now come from `parse_query()` in the backend (LLM suggests likely Twitter accounts directly):
- [ ] ~~Send screenshot to Northstar~~
- [ ] ~~Parse Northstar's response into a list of handles~~
- [ ] ~~Return list of profile URLs to visit~~

`extract_profile_data(browser, profile_url)` — implemented in `agent/twitter.py` + `agent/cua.py`:
- [x] Navigate to the profile URL
- [x] Wait for page load
- [x] Screenshot the profile header area
- [x] Use Northstar to extract: display name, @handle, bio text, follower count, profile image URL
- [x] Scroll down to tweets section, screenshot
- [x] Use Northstar to extract 3-5 recent tweet texts
- [x] Return structured profile object:
```python
{
  "name": "John Doe",
  "twitter_handle": "@johndoe",
  "twitter_url": "https://twitter.com/johndoe",
  "bio": "...",
  "followers": 12500,
  "profile_image_url": "https://...",
  "recent_tweets": ["tweet1", "tweet2", "tweet3"]
}
```

`run_agent(handles, on_status, on_lead)` — implemented in `agent/agent_async.py`, exposed via `agent/__init__.py`:
- [x] Calls `start_browser()`
- [x] For each handle in `handles` (LLM-suggested list from backend):
  - [x] Calls `on_status("Analyzing @handle's profile...")`
  - [x] Calls `extract_profile_data()`
  - [x] Calls `on_lead(profile_data)` — this is how Person B receives data
  - [x] Deduplicates profiles by handle
- [x] Closes browser when done
- [x] Sync (`run_agent`) and async (`run_agent_async`) entry points + `AgentConfig(max_profiles, timeout_seconds)`

**Error handling:**
- [x] Twitter login wall → handled (running on logged-out public profile pages)
- [x] Profile is private → skip, log, continue (`"Could not extract @arvidkahl, skipping..."` from test run)
- [x] Page didn't load → retry once, then skip
- [x] Northstar returns garbage → retry screenshot, then skip profile
- [x] Set a global timeout via `AgentConfig.timeout_seconds` (default 180s)

**PR checklist:**
- [x] `start_browser()` — browser spins up and takes a screenshot
- [ ] ~~`search_twitter()`~~ — *de-scoped (see above)*
- [ ] ~~`extract_profiles_from_search()`~~ — *de-scoped (see above)*
- [x] `extract_profile_data()` — returns complete profile object for a single profile
- [x] `run_agent()` — full loop works, calls callbacks correctly
- [x] Error handling for login wall, private profiles, timeouts
- [x] Tested with real handles (`@levelsio`, `@arvidkahl`, `@marckohlbrugge`) — see `agent/test_results_20260509_131029.json`

---

### 🟢 Person B — Backend API + LLM Logic (Scoring, Parsing, Outreach)

You own the server, the query parser, the scoring engine, and the outreach generator.

**Setup:**
- [x] Init project: `podpipe-api/` with FastAPI app under `app/`
- [x] Python deps installed: `fastapi`, `uvicorn`, `pydantic`, `python-dotenv`, etc. (`podpipe-api/requirements.txt`) — using `fastapi.responses.StreamingResponse` for SSE
- [x] LLM access wired up in `app/llm.py` (parse / score / outreach)
- [x] Test: server runs on `:8000`, SSE endpoint streams events end-to-end

**Query parsing — `parse_query(raw_query)`** — implemented in `podpipe-api/app/llm.py`:
- [x] Takes the user's raw natural language input
- [x] Sends to LLM with system prompt:
```
You are a search query parser for finding podcast guests on Twitter.
Given a natural language description, extract:
- keywords: list of topic keywords to search for
- role: the type of person (founder, investor, operator, creator, etc.)
- vibe: the content style (tactical, storyteller, contrarian, educational, etc.)
- search_queries: 2-3 actual Twitter search strings that would find these people

Respond in JSON only. No markdown, no backticks.

Example input: "I need a bootstrapped SaaS founder who gives tactical advice about scaling"
Example output: {
  "keywords": ["bootstrapped", "SaaS", "scaling", "founder"],
  "role": "founder", 
  "vibe": "tactical",
  "search_queries": ["bootstrapped SaaS founder", "indie hacker scaling SaaS", "SaaS ARR bootstrap"]
}
```
- [x] Parse LLM response as JSON
- [x] Validate: returns suggested handles list (pivoted from `search_queries` → direct handle suggestions, which works better with the agent's new direct-navigation flow)
- [x] Test with multiple input queries

**Scoring — `score_lead(user_query, profile_data)`** — implemented in `podpipe-api/app/llm.py`:
- [x] Takes the original user query + extracted profile data
- [x] Sends to LLM with system prompt:
```
You are evaluating whether a Twitter user would be a good podcast guest.

Given the podcaster's request and the candidate's profile, return:
- match_score: 0-100 (how well they fit the request)
- match_reason: 1-2 sentences explaining why they're a good/bad fit

Score based on:
- Topic relevance (do they tweet about the right stuff?)
- Credibility (do they have real experience, not just opinions?)
- Content quality (are their tweets substantive or just retweets/memes?)
- Podcast readiness (do they seem like someone who'd do interviews?)

Respond in JSON only. No markdown, no backticks.
```
- [x] Parse response, validate match_score is 0-100
- [x] Filter: only pass through leads with match_score >= 60 (`MIN_MATCH_SCORE` in `search_runner.py`)

**Outreach generation — `generate_outreach(user_query, profile_data)`** — implemented in `podpipe-api/app/llm.py`:
- [x] Takes profile data + user query
- [x] Sends to LLM with system prompt:
```
Write a short Twitter DM (3-4 sentences) inviting this person to be a podcast guest.

Rules:
- Reference something specific from their bio or recent tweets
- Mention what the podcast is about (infer from the user's query)
- Keep it casual and direct, not salesy
- End with a low-commitment ask ("Would you be open to a 30-min chat?")
- Don't use exclamation marks excessively

Respond with the DM text only, no JSON, no quotes.
```
- [x] Return the DM text as a string

**API endpoints** — implemented in `podpipe-api/app/main.py`:

`POST /api/search`:
- [x] Accept `{ query: string }` in request body
- [x] Generate a `search_id` (uuid)
- [x] Store in memory via `SearchStore` (`app/store.py`): `{ status, leads, events, query }`
- [x] Kick off agent via FastAPI `BackgroundTasks` → `run_search()` in `app/search_runner.py`
  - [x] Call `parse_query(query)` → get suggested handles
  - [x] Call `run_agent_adapter(handles, on_status, on_lead)` (`app/agent_adapter.py`) which dispatches to either real `agent.run_agent_async` or `mock_agent` based on `USE_MOCK_AGENT` env
  - [x] `on_status(msg, step)` → append to events list
  - [x] `on_lead(profile)` → `score_lead()` → if ≥ 60: `generate_outreach()` → append `ScoredLead` + emit lead event
  - [x] When agent finishes → set status to "completed", append done event
- [x] Return `{ search_id }` immediately

`GET /api/search/:search_id/stream`:
- [x] SSE endpoint
- [x] Streams all events for this search_id
- [x] Keeps connection open, yields new events as they arrive (50ms poll loop)
- [x] Closes when status is `completed` or `failed`
- [x] CORS allows frontend to connect

`GET /api/search/:search_id/export`:
- [x] Build CSV from `searches[search_id].leads` via `leads_to_csv()` (`app/csv_export.py`)
- [x] Returns as file download with `Content-Disposition: attachment; filename="podpipe-leads.csv"`
- [x] Columns: name, twitter_handle, twitter_url, bio, followers, match_score, match_reason, outreach_dm

**CORS:**
- [x] Enabled for all origins via `CORSMiddleware` in `main.py`

**PR checklist:**
- [x] Server starts, `/health` endpoint works
- [x] `parse_query()` returns valid suggested handles for test inputs
- [x] `score_lead()` returns match_score + match_reason for a test profile
- [x] `generate_outreach()` returns a personalized DM for a test profile
- [x] `POST /api/search` kicks off background task, returns search_id
- [x] `GET /api/search/:id/stream` streams events correctly
- [x] `GET /api/search/:id/export` returns valid CSV
- [x] CORS enabled
- [x] Integrated with Person A's agent (real `agent` module + `mock_agent` fallback via `USE_MOCK_AGENT`)

---

### 🔵 Person C — Frontend (Magic Patterns) + Integration + Demo

You own the UI, wiring everything together, and the final demo.

**Magic Patterns setup** — generated UI lives under `frontend/` (Vite + React + TS + Tailwind + framer-motion + lucide-react):
- [x] Sent the PodPipe prompt to Magic Patterns and exported the generated code into `frontend/` (package name still reads `magic-patterns-vite-template`)
- [x] Review the generated output — confirmed it has:
  - [x] Single text input with placeholder ("A bootstrapped SaaS founder who tweets about scaling…") — `frontend/src/components/QueryInput.tsx`
  - [x] Submit button (arrow icon, ⌘+Enter shortcut, animated loading state) — `QueryInput.tsx`
  - [x] Status bar / activity indicator — `frontend/src/components/AgentStatus.tsx` + sidebar activity log in `AppSidebar.tsx`
  - [x] Card list area for results — `frontend/src/pages/Home.tsx`
  - [x] Individual card with: photo, name, handle, bio, followers, score badge, match reason — `frontend/src/components/GuestCard.tsx` + `ProfileAvatar.tsx`
  - [x] Detail view (right-side sheet) with: recent tweets, outreach DM, copy button, Twitter link — `frontend/src/components/GuestDetail.tsx` + `Sheet.tsx`
  - [x] Export CSV button — top of results list in `Home.tsx`
- [x] Beyond spec: collapsible sidebar (`AppSidebar.tsx` + `Sidebar.tsx`) with session stats (avg match, total reach), score filters (All / Top 80%+ / Good 60-79%), live activity log with status/lead/done icons, tips panel
- [x] Code committed into the monorepo

**Wiring to backend** — implemented in `frontend/src/hooks/useSearch.ts` + `frontend/src/api/search.ts`:

Search trigger:
- [x] Submit button calls `POST /api/search` (via `@tanstack/react-query` mutation in `useStartSearch`)
- [x] Stores the returned `search_id`
- [x] Disables input + button, swaps button to spinner
- [x] Immediately connects to `GET /api/search/:search_id/stream` via `EventSource` (`startRealStream`)
- [x] `VITE_API_BASE_URL` env (`http://localhost:8000` in `.env`) drives the base URL via `frontend/src/config.ts`

SSE handling:
- [x] On `status` event → updates status bar text + appends to activity log
- [x] On `lead` event → adds a new card with framer-motion fade + slide-up animation, updates lead count
- [x] On `done` event → stops loading, re-enables input, shows export button, appends "Done · N guests found" to log
- [x] On EventSource error → surfaces "Connection lost while searching. Please try again." with a Retry CTA
- [x] Mock mode toggle: `VITE_USE_MOCK=true` runs a scripted timeline of 7 fake guests for offline UI dev / demo fallback

Card interactions:
- [x] Click card → opens right-side `Sheet` with full details (tweets, outreach DM)
- [x] Sheet close (Esc / overlay / X) → collapse
- [x] "Copy DM" button → `navigator.clipboard.writeText(outreach_dm)` + 2s "Copied" confirmation
- [x] "View on Twitter" link → opens `twitter_url` in new tab
- [x] Bonus: card highlights with indigo ring while its detail sheet is open

Export:
- [x] "Export CSV" button → `window.location.href = getExportUrl(searchId)` for real searches; client-side CSV blob download in mock mode

Match score styling — `getScoreColor()` in `GuestCard.tsx` + `GuestDetail.tsx`:
- [x] Score ≥ 80 → emerald badge
- [x] Score ≥ 60 → amber badge
- [x] Score < 60 → zinc fallback (shouldn't appear, backend filters)

**States to handle** — all in `frontend/src/pages/Home.tsx`:
- [x] Empty state — centered hero with `QueryInput` only
- [x] Searching state — input disabled, `AgentStatus` active, cards streaming in
- [x] Done state — all cards visible, Export CSV enabled, sidebar shows "New search" button
- [x] Error state — `AlertCircle` + error message + "Try again" reset button
- [x] No-results state — `SearchX` icon + "No guests found. Try a different description."
- [x] Filter state — sidebar score filter (All/High/Medium) with empty filter fallback message

**Demo prep:**
- [ ] Pick 3 demo queries and test each one end-to-end at least twice:
  - [ ] Query 1: "YC founder who bootstrapped a dev tools company and tweets about PLG"
  - [ ] Query 2: "Female founder in fintech who shares fundraising lessons"
  - [ ] Query 3: "Solo founder doing $50k MRR who posts build-in-public content"
- [ ] Time the full flow — from typing to cards appearing. Should be under 2 minutes.
- [ ] At 3:30pm: do a screen recording of a successful run as backup
- [ ] Write talking points for the verbal pitch (see Demo Script below)
- [ ] Make sure the demo machine has good internet and is charged

**PR checklist:**
- [x] Magic Patterns UI imported and rendering locally
- [x] Submit triggers `POST /api/search`
- [x] SSE connected — status bar + activity log update in real time
- [x] Lead cards render as they stream in with animation
- [x] Detail sheet shows tweets + DM + copy + Twitter link
- [x] "Copy DM" works (with copied confirmation)
- [x] "Export CSV" triggers download
- [x] Error state handled (SSE drop, search failure)
- [x] No-results state handled
- [x] Mock mode (`VITE_USE_MOCK=true`) for offline demo fallback
- [ ] Demo runs end-to-end successfully 3 times *(pending final rehearsal)*
