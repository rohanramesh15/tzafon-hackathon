# PodPipe — Hackathon Plan

## What is it?
Juicebox for podcast guest discovery. A podcaster types a natural language description of who they want on their show, an AI agent browses Twitter/X to find matching people, and returns a ranked list of potential guests with personalized outreach DMs.

## One-liner pitch
"Describe your dream podcast guest → our agent browses Twitter and finds them for you."

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
- [ ] Sign up at `lightcone.ai/signup?campaign=HACKMAY9` (get $2,500 credits)
- [ ] `pip install tzafon` and confirm API key works with a basic test
- [ ] Sign up at `dashboard.onkernel.com/hackathon?code=KERNELHACKATHON2026`
- [ ] Install KERNEL: `npm install -g @onkernel/cli` or use Python SDK
- [ ] Run a hello-world: spin up KERNEL browser → take screenshot → send to Northstar → confirm you get an action back

**Core functions to build:**

`start_browser()`:
- [ ] Spins up a KERNEL cloud browser
- [ ] Returns browser instance + CDP connection
- [ ] Set viewport to 1280x720 (what Northstar expects)
- [ ] If using a logged-in Twitter session, load the KERNEL persistent profile

`search_twitter(browser, query)`:
- [ ] Navigate to `twitter.com/search?q={query}&src=typed_query&f=user` (the People tab)
- [ ] Wait for results to load (screenshot and check with Northstar, or wait for DOM)
- [ ] Screenshot the results page
- [ ] Return the screenshot for profile extraction

`extract_profiles_from_search(browser, screenshot)`:
- [ ] Send screenshot to Northstar: "List all the Twitter usernames/handles visible on this page"
- [ ] Parse Northstar's response into a list of handles/profile URLs
- [ ] Return list of profile URLs to visit (aim for 5-10)

`extract_profile_data(browser, profile_url)`:
- [ ] Navigate to the profile URL
- [ ] Wait for page load
- [ ] Screenshot the profile header area
- [ ] Use Northstar to extract: display name, @handle, bio text, follower count, profile image URL
- [ ] Scroll down to tweets section, screenshot
- [ ] Use Northstar to extract 3-5 recent tweet texts
- [ ] Return structured profile object:
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

`run_agent(search_queries, on_status, on_lead)`:
- [ ] Calls `start_browser()`
- [ ] For each query in search_queries:
  - [ ] Calls `on_status("Searching Twitter for '{query}'...")`
  - [ ] Calls `search_twitter(browser, query)`
  - [ ] Calls `extract_profiles_from_search()` to get profile list
  - [ ] For each profile:
    - [ ] Calls `on_status("Analyzing @handle's profile...")`
    - [ ] Calls `extract_profile_data()` 
    - [ ] Calls `on_lead(profile_data)` — this is how Person B receives data
  - [ ] Deduplicates profiles across queries (by handle)
- [ ] Closes browser when done

**Error handling:**
- [ ] Twitter login wall → try KERNEL persistent session, or navigate to mobile.twitter.com as fallback
- [ ] Profile is private → skip, log, continue
- [ ] Page didn't load → retry once, then skip
- [ ] Northstar returns garbage → retry screenshot, then skip profile
- [ ] Set a global timeout (e.g., 3 minutes max per search)

**PR checklist:**
- [ ] `start_browser()` — browser spins up and takes a screenshot
- [ ] `search_twitter()` — navigates to Twitter search, results page loads
- [ ] `extract_profiles_from_search()` — returns 5+ handles from a search page
- [ ] `extract_profile_data()` — returns complete profile object for a single profile
- [ ] `run_agent()` — full loop works, calls callbacks correctly
- [ ] Error handling for login wall, private profiles, timeouts
- [ ] Tested with 2+ different search queries

---

### 🟢 Person B — Backend API + LLM Logic (Scoring, Parsing, Outreach)

You own the server, the query parser, the scoring engine, and the outreach generator.

**Setup:**
- [ ] Init project: `mkdir podpipe-api && cd podpipe-api`
- [ ] If Python: `pip install fastapi uvicorn sse-starlette` (or use `fastapi.responses.StreamingResponse`)
- [ ] If Node: `npm init && npm install express` (use `res.write()` for SSE)
- [ ] Set up LLM access (Claude API, or use Northstar for this too)
- [ ] Test: start server, hit SSE endpoint from browser, confirm events arrive

**Query parsing — `parse_query(raw_query)`:**
- [ ] Takes the user's raw natural language input
- [ ] Sends to LLM with system prompt:
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
- [ ] Parse LLM response as JSON
- [ ] Validate: search_queries should be 2-3 strings, each 2-5 words
- [ ] Test with 5+ different input queries

**Scoring — `score_lead(user_query, profile_data)`:**
- [ ] Takes the original user query + extracted profile data
- [ ] Sends to LLM with system prompt:
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
- [ ] Parse response, validate match_score is 0-100
- [ ] Filter: only pass through leads with match_score >= 60

**Outreach generation — `generate_outreach(user_query, profile_data)`:**
- [ ] Takes profile data + user query
- [ ] Sends to LLM with system prompt:
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
- [ ] Return the DM text as a string

**API endpoints:**

`POST /api/search`:
- [ ] Accept `{ query: string }` in request body
- [ ] Generate a `search_id` (uuid)
- [ ] Store in memory: `searches[search_id] = { status: "running", leads: [], events: [] }`
- [ ] Kick off agent in background (asyncio task / thread)
  - [ ] Call `parse_query(query)` → get search_queries
  - [ ] Call Person A's `run_agent(search_queries, on_status, on_lead)`
  - [ ] `on_status(msg)` → append to events list
  - [ ] `on_lead(profile)` → call `score_lead()` → if score >= 60: call `generate_outreach()` → append to leads list + events list
  - [ ] When agent finishes → set status to "completed", append done event
- [ ] Return `{ search_id }` immediately

`GET /api/search/:search_id/stream`:
- [ ] SSE endpoint
- [ ] Stream all events for this search_id
- [ ] Keep connection open, yield new events as they arrive
- [ ] Close when done event is sent
- [ ] Set CORS headers so frontend can connect

`GET /api/search/:search_id/export`:
- [ ] Build CSV from `searches[search_id].leads`
- [ ] Return as file download with `Content-Disposition: attachment; filename="podpipe-leads.csv"`
- [ ] Columns: name, twitter_handle, twitter_url, bio, followers, match_score, match_reason, outreach_dm

**CORS:**
- [ ] Enable CORS for all origins (hackathon, don't worry about security)

**PR checklist:**
- [ ] Server starts, health check endpoint works
- [ ] `parse_query()` returns valid search_queries for 3+ test inputs
- [ ] `score_lead()` returns match_score + match_reason for a test profile
- [ ] `generate_outreach()` returns a personalized DM for a test profile
- [ ] `POST /api/search` kicks off background task, returns search_id
- [ ] `GET /api/search/:id/stream` streams events correctly (test with curl)
- [ ] `GET /api/search/:id/export` returns valid CSV
- [ ] CORS enabled
- [ ] Integrated with Person A's agent (or working with mock agent)

---

### 🔵 Person C — Frontend (Magic Patterns) + Integration + Demo

You own the UI, wiring everything together, and the final demo.

**Magic Patterns setup:**
- [ ] Send the PodPipe prompt to Magic Patterns via MCP or web UI
- [ ] Review the generated output — confirm it has:
  - [ ] Single text input with placeholder text
  - [ ] "Find Guests" submit button
  - [ ] Status bar / activity indicator area
  - [ ] Card list area for results
  - [ ] Individual card component with: photo, name, handle, bio, followers, score badge, match reason
  - [ ] Expanded card view with: recent tweets, outreach DM, copy button, Twitter link
  - [ ] Export CSV button
- [ ] If anything is missing or off, send follow-up prompts to Magic Patterns to fix
- [ ] Export / download the generated code into the repo

**Wiring to backend:**

Search trigger:
- [ ] "Find Guests" button calls `POST /api/search` with the input text
- [ ] Store the returned `search_id`
- [ ] Disable the input + button, show loading state
- [ ] Immediately connect to `GET /api/search/:search_id/stream` via `EventSource`

SSE handling:
- [ ] On `status` event → update the status bar text, show loading animation
- [ ] On `lead` event → parse lead data, add a new card to the results list
  - [ ] Card should animate in (fade + slide up)
  - [ ] Update the lead count ("3 guests found")
- [ ] On `done` event → stop loading animation, re-enable input, show export button
- [ ] On EventSource error → show "Connection lost, retrying..." message, attempt reconnect

Card interactions:
- [ ] Click card → expand to show full details (recent tweets, outreach DM)
- [ ] Click again → collapse
- [ ] "Copy DM" button → `navigator.clipboard.writeText(outreach_dm)` → show "Copied!" toast
- [ ] "View on Twitter" → `window.open(twitter_url, '_blank')`

Export:
- [ ] "Export CSV" button → `window.open(/api/search/:id/export)` to trigger download

Match score styling:
- [ ] Score >= 80 → green badge
- [ ] Score >= 60 → yellow badge
- [ ] Score < 60 → shouldn't appear (filtered by backend) but gray if it does

**States to handle:**
- [ ] Empty state (initial) — just the search input, maybe a few example queries as clickable suggestions
- [ ] Searching state — input disabled, status bar active, cards streaming in
- [ ] Done state — all cards visible, export button shown, input re-enabled for new search
- [ ] Error state — error message below input, "Try again" button
- [ ] No results state — "No matching guests found. Try a broader description."

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
- [ ] Magic Patterns UI imported and rendering locally
- [ ] "Find Guests" triggers POST /api/search
- [ ] SSE connected — status bar updates in real time
- [ ] Lead cards render as they stream in with animation
- [ ] Expanded card shows tweets + DM + copy + Twitter link
- [ ] "Copy DM" works
- [ ] "Export CSV" triggers download
- [ ] Error state handled (SSE drop, search failure)
- [ ] Empty results state handled
- [ ] Demo runs end-to-end successfully 3 times
