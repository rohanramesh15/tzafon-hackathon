# PodPipe Agent - Complete Integration Guide for Person B

## Table of Contents
1. [Important: Architecture Change](#important-architecture-change)
2. [Quick Start](#quick-start)
3. [Environment Setup](#environment-setup)
4. [Agent API Reference](#agent-api-reference)
5. [Data Structures](#data-structures)
6. [Your LLM Functions (with prompts)](#your-llm-functions)
7. [Complete FastAPI Implementation](#complete-fastapi-implementation)
8. [API Contract (matches PLAN.md)](#api-contract)
9. [Testing](#testing)
10. [Troubleshooting](#troubleshooting)
11. [Checklist](#checklist)

---

## Important: Architecture Change

**The original plan had the agent searching Twitter directly. This doesn't work because Twitter blocks automated search.**

### Original Flow (PLAN.md):
```
User query → parse_query() → search_queries → Agent searches Twitter → profiles
```

### Actual Flow (What We Built):
```
User query → parse_query() → LLM suggests handles → Agent visits profiles directly → profiles
```

### What this means for you:
- Instead of returning `search_queries` like `["bootstrapped SaaS founder"]`
- Your `parse_query()` returns actual Twitter handles like `["@levelsio", "@marckohlbrugge"]`
- **The LLM must suggest REAL, EXISTING Twitter handles** - not made up ones
- The agent visits each profile and extracts data
- Some handles may not exist or be private - the agent handles this gracefully

### Important: LLM Hallucination Risk
The LLM might suggest handles that don't exist. This is OK - the agent will skip invalid profiles and continue. Suggest 10-15 handles so that even if some fail, you get enough results.

---

## Quick Start

**Requirements:** Python 3.9+

```bash
# From the project root directory (tzafon-hackathon/)

# 1. Install and test the agent
cd agent
pip install -r requirements.txt
playwright install chromium

# Verify agent works (should print status messages)
python -c "
import sys; sys.path.insert(0, '..')
from agent import run_agent
run_agent(
    handles=['@levelsio'],
    on_status=print,
    on_lead=lambda l: print(f'Got lead: {l[\"name\"]}')
)
"

# 2. Set up your backend
cd ..
mkdir -p api
cd api
pip install fastapi uvicorn sse-starlette anthropic python-dotenv

# 3. Create api/.env with your Anthropic key
echo "ANTHROPIC_API_KEY=sk-ant-your-key-here" > .env

# 4. Copy main.py (see Complete FastAPI Implementation section below)

# 5. Run the server
uvicorn main:app --reload --port 8000
```

---

## Environment Setup

### Agent needs (already configured in `agent/.env`):
```env
TZAFON_API_KEY=sk_...      # Northstar CUA - for vision AI
KERNEL_API_KEY=sk_...       # KERNEL - for cloud browsers
```

### Your backend needs (create `api/.env`):
```env
ANTHROPIC_API_KEY=sk-ant-...   # For Claude API (your LLM calls)
```

### Important: Loading Both .env Files
Your FastAPI app must load BOTH env files:
```python
from dotenv import load_dotenv
import os

# Load API's own env
load_dotenv()

# Also load agent's env (for TZAFON and KERNEL keys)
load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'agent', '.env'))
```

---

## Agent API Reference

### Import
```python
# Add agent to Python path first
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from agent import run_agent, run_agent_async, AgentConfig
```

### Function Signatures

```python
def run_agent(
    handles: List[str],                    # Twitter handles to check (e.g., ["@levelsio", "@csallen"])
    on_status: Callable[[str], None],      # Called with status messages
    on_lead: Callable[[dict], None],       # Called when a profile is extracted
    config: Optional[AgentConfig] = None   # Optional configuration
) -> int:                                  # Returns count of leads found
    """
    Synchronous version. Blocks until complete.
    Use this if running in a thread.
    """

async def run_agent_async(
    handles: List[str],
    on_status: Callable[[str], None],
    on_lead: Callable[[dict], None],
    config: Optional[AgentConfig] = None
) -> int:
    """
    Async version. Use this in FastAPI.
    NOTE: The callbacks (on_status, on_lead) are called synchronously
    from within the async function. Keep callback code fast.
    """
```

### Configuration

```python
from agent import AgentConfig

config = AgentConfig(
    max_profiles=10,       # Stop after extracting this many profiles
    timeout_seconds=180    # Global timeout (3 minutes)
)
```

### Callback Behavior

**`on_status(message: str)`** is called with messages like:
- `"Initializing AI vision model..."`
- `"Starting KERNEL cloud browser..."`
- `"Browser ready (session: abc12345...)"`
- `"Analyzing @levelsio's profile..."`
- `"Found lead: Pieter Levels (@levelsio)"`
- `"@badhandle requires login, skipping..."` ← handle doesn't exist or is private
- `"Could not extract @unknown, skipping..."` ← extraction failed
- `"Agent completed. Found 5 leads."`

**`on_lead(lead: dict)`** is called once per successfully extracted profile.

---

## Data Structures

### What the Agent Returns (raw profile data)

```python
{
    "name": "Pieter Levels",
    "twitter_handle": "@levelsio",
    "twitter_url": "https://twitter.com/levelsio",
    "bio": "PhotoAI.com $100K/m\nRemoteOK.com $44K/m\nMaking things people want",
    "followers": 863700,
    "profile_image_url": "visible",   # May be "visible" or actual URL
    "recent_tweets": [
        "Just crossed $100K MRR on PhotoAI...",
        "Thread: How I validate ideas in 24 hours...",
        "Hot take: You don't need VC money..."
    ]
}
```

**Note:** `recent_tweets` may be empty if no tweets were visible. `bio` may be empty.

### What You Send to Frontend (after scoring)

This matches the PLAN.md API contract:

```python
{
    "id": "lead_001",                        # YOU generate this (e.g., lead_001, lead_002)
    "name": "Pieter Levels",
    "twitter_handle": "@levelsio",
    "twitter_url": "https://twitter.com/levelsio",
    "bio": "PhotoAI.com $100K/m...",
    "followers": 863700,
    "profile_image_url": "visible",
    "match_score": 92,                       # YOU add this (from score_lead)
    "match_reason": "Bootstrapped founder...", # YOU add this (from score_lead)
    "recent_tweets": ["...", "...", "..."],
    "outreach_dm": "Hey Pieter — ..."        # YOU add this (from generate_outreach)
}
```

### SSE Event Formats (matches PLAN.md)

```python
# Status event
{
    "type": "status",
    "message": "Analyzing @levelsio's profile...",
    "step": "extracting"  # One of: "parsing", "browsing", "extracting", "scoring"
}

# Lead event (only for scores >= 60)
{
    "type": "lead",
    "data": { ... full lead object with score and outreach_dm ... }
}

# Done event
{
    "type": "done",
    "total_leads": 8
}
```

---

## Your LLM Functions

You need to implement 3 functions using Claude (or another LLM).

### 1. `parse_query(raw_query: str) -> dict`

**Purpose:** Parse user's natural language AND suggest Twitter handles.

**Critical:** The LLM must suggest REAL Twitter accounts. Here are verified handles for common categories:

| Category | Real Handles |
|----------|-------------|
| Bootstrapped founders | @levelsio, @marckohlbrugge, @csallen, @paborenstein, @shl, @ajlkn |
| Indie hackers | @dannypostmaa, @arvidkahl, @jonbstrong, @yaborenstein |
| VC / Investors | @paulg, @sama, @naval, @balaborenstein, @jason |
| AI/ML | @kaborenstein, @ylecun, @hardmaru, @AndrewYNg |
| Dev tools | @guillarmand, @adamwathan, @maborenstein |

**System Prompt:**
```
You are a search query parser for finding podcast guests on Twitter.

Given a natural language description of who the podcaster wants as a guest, you must:
1. Extract structured information about the request
2. Suggest 10-15 REAL Twitter handles of people who match this description

CRITICAL: You must suggest REAL, EXISTING Twitter accounts. Think of actual well-known people in the tech/startup space. Do NOT make up handles.

Examples of real handles by category:
- Bootstrapped SaaS founders: @levelsio, @marckohlbrugge, @csallen, @shl, @ajlkn
- Indie hackers: @dannypostmaa, @arvidkahl, @jonbstrong
- VCs/Investors: @paulg, @sama, @naval, @jason
- AI/ML: @ylecun, @hardmaru, @AndrewYNg

Respond in JSON only. No markdown, no backticks, no explanation.

Output format:
{
  "keywords": ["keyword1", "keyword2"],
  "role": "founder|investor|creator|operator|researcher",
  "vibe": "tactical|storyteller|contrarian|educational",
  "handles": ["@handle1", "@handle2", "@handle3", ...]
}
```

**Implementation with error handling:**
```python
import anthropic
import json

client = anthropic.Anthropic()  # Uses ANTHROPIC_API_KEY env var

def parse_query(raw_query: str) -> dict:
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        system="""You are a search query parser for finding podcast guests on Twitter.

Given a natural language description, you must:
1. Extract structured information about the request
2. Suggest 10-15 REAL Twitter handles of people who match

CRITICAL: Suggest REAL, EXISTING Twitter accounts only. Think of well-known people in tech/startups.

Examples: @levelsio, @marckohlbrugge, @csallen, @paulg, @naval, @shl

Respond in JSON only. No markdown, no backticks.

Output format:
{
  "keywords": ["keyword1", "keyword2"],
  "role": "founder|investor|creator|operator|researcher",
  "vibe": "tactical|storyteller|contrarian|educational",
  "handles": ["@handle1", "@handle2", ...]
}""",
        messages=[{"role": "user", "content": raw_query}]
    )

    text = response.content[0].text.strip()

    # Handle potential markdown code blocks
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        # Return empty result if parsing fails
        print(f"JSON parse error: {e}")
        return {"keywords": [], "role": "", "vibe": "", "handles": []}
```

---

### 2. `score_lead(user_query: str, lead: dict) -> dict`

**Purpose:** Score how well a profile matches the user's request.

**System Prompt:**
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

Be strict. Only give 80+ to excellent matches. 60-79 for good matches. Below 60 means skip.

Respond in JSON only. No markdown, no backticks.

Output format:
{
  "match_score": 85,
  "match_reason": "One or two sentences explaining the score."
}
```

**Implementation:**
```python
def score_lead(user_query: str, lead: dict) -> dict:
    # Handle empty bio/tweets gracefully
    bio = lead.get('bio', '') or '(no bio)'
    tweets = lead.get('recent_tweets', []) or ['(no tweets visible)']

    profile_summary = f"""
Name: {lead.get('name', 'Unknown')}
Handle: {lead.get('twitter_handle', 'Unknown')}
Bio: {bio}
Followers: {lead.get('followers', 0)}
Recent tweets:
{chr(10).join(f'- {t}' for t in tweets)}
"""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=256,
        system="""You are evaluating whether a Twitter user would be a good podcast guest.

Return:
- match_score: 0-100
- match_reason: 1-2 sentences

Score based on topic relevance, credibility, content quality, podcast readiness.
Be strict. 80+ for excellent, 60-79 for good, below 60 skip.

Respond in JSON only. No markdown, no backticks.""",
        messages=[{
            "role": "user",
            "content": f"Podcaster request: {user_query}\n\nCandidate:\n{profile_summary}"
        }]
    )

    text = response.content[0].text.strip()

    try:
        # Handle markdown code blocks
        if "```" in text:
            text = text.split("```")[1].replace("json", "").strip()
        return json.loads(text)
    except json.JSONDecodeError:
        return {"match_score": 0, "match_reason": "Failed to parse score"}
```

---

### 3. `generate_outreach(user_query: str, lead: dict) -> str`

**Purpose:** Generate a personalized DM to invite them on the podcast.

**System Prompt:**
```
Write a short Twitter DM (3-4 sentences) inviting this person to be a podcast guest.

Rules:
- Reference something specific from their bio or recent tweets
- Mention what the podcast is about (infer from the user's query)
- Keep it casual and direct, not salesy
- End with a low-commitment ask ("Would you be open to a 30-min chat?")
- Don't use exclamation marks excessively
- Don't be cringe or overly enthusiastic

Respond with the DM text only. No JSON, no quotes, no preamble.
```

**Implementation:**
```python
def generate_outreach(user_query: str, lead: dict) -> str:
    bio = lead.get('bio', '') or '(no bio)'
    tweets = lead.get('recent_tweets', [])[:3] or ['(no tweets)']

    profile_summary = f"""
Name: {lead.get('name', 'Unknown')}
Handle: {lead.get('twitter_handle', '')}
Bio: {bio}
Recent tweets:
{chr(10).join(f'- {t}' for t in tweets)}
"""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=256,
        system="""Write a short Twitter DM (3-4 sentences) inviting this person to be a podcast guest.

Rules:
- Reference something specific from their bio or recent tweets
- Mention what the podcast is about (infer from the user's query)
- Keep it casual and direct, not salesy
- End with a low-commitment ask ("Would you be open to a 30-min chat?")
- Don't use exclamation marks excessively

Respond with the DM text only. No JSON, no quotes.""",
        messages=[{
            "role": "user",
            "content": f"Podcast topic: {user_query}\n\nGuest:\n{profile_summary}"
        }]
    )

    return response.content[0].text.strip()
```

---

## Complete FastAPI Implementation

### First, create `api/requirements.txt`:
```
fastapi>=0.100.0
uvicorn>=0.20.0
sse-starlette>=1.6.0
anthropic>=0.18.0
python-dotenv>=1.0.0
```

### Then, save this as `api/main.py`:

```python
import os
import json
import uuid
import asyncio
from typing import Dict, List
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse
from dotenv import load_dotenv
import anthropic

# Load environment variables - BOTH api and agent .env files
load_dotenv()  # Load api/.env
load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'agent', '.env'))  # Load agent/.env

# Add agent to path
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from agent import run_agent_async, AgentConfig

# Initialize
app = FastAPI(title="PodPipe API")
client = anthropic.Anthropic()

# CORS - allow all for hackathon
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage
searches: Dict[str, dict] = {}


# Request/Response models
class SearchRequest(BaseModel):
    query: str


class SearchResponse(BaseModel):
    search_id: str


# ============ LLM FUNCTIONS ============

def parse_query(raw_query: str) -> dict:
    """Parse user query and get suggested handles."""
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        system="""You are a search query parser for finding podcast guests on Twitter.

Given a natural language description, you must:
1. Extract structured information about the request
2. Suggest 10-15 REAL Twitter handles of people who match

CRITICAL: Suggest REAL, EXISTING Twitter accounts only.
Examples: @levelsio, @marckohlbrugge, @csallen, @paulg, @naval, @shl, @arvidkahl

Respond in JSON only. No markdown, no backticks.

Output format:
{
  "keywords": ["keyword1", "keyword2"],
  "role": "founder|investor|creator|operator",
  "vibe": "tactical|storyteller|contrarian|educational",
  "handles": ["@handle1", "@handle2", ...]
}""",
        messages=[{"role": "user", "content": raw_query}]
    )

    text = response.content[0].text.strip()
    if "```" in text:
        text = text.split("```")[1].replace("json", "").strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"handles": []}


def score_lead(user_query: str, lead: dict) -> dict:
    """Score how well a lead matches the query."""
    bio = lead.get('bio', '') or '(no bio)'
    tweets = lead.get('recent_tweets', []) or ['(no tweets)']

    profile_summary = f"""
Name: {lead.get('name', 'Unknown')}
Handle: {lead.get('twitter_handle', '')}
Bio: {bio}
Followers: {lead.get('followers', 0)}
Recent tweets:
{chr(10).join(f'- {t}' for t in tweets)}
"""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=256,
        system="""Evaluate if this Twitter user would be a good podcast guest.

Return JSON only:
{"match_score": 0-100, "match_reason": "1-2 sentences"}

Be strict. 80+ excellent, 60-79 good, below 60 skip.""",
        messages=[{
            "role": "user",
            "content": f"Request: {user_query}\n\nCandidate:\n{profile_summary}"
        }]
    )

    text = response.content[0].text.strip()
    if "```" in text:
        text = text.split("```")[1].replace("json", "").strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"match_score": 0, "match_reason": "Parse error"}


def generate_outreach(user_query: str, lead: dict) -> str:
    """Generate personalized outreach DM."""
    bio = lead.get('bio', '') or '(no bio)'
    tweets = lead.get('recent_tweets', [])[:3] or ['(no tweets)']

    profile_summary = f"""
Name: {lead.get('name', '')}
Handle: {lead.get('twitter_handle', '')}
Bio: {bio}
Recent tweets:
{chr(10).join(f'- {t}' for t in tweets)}
"""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=256,
        system="""Write a Twitter DM (3-4 sentences) inviting them as a podcast guest.
Reference their bio/tweets. Keep casual. End with "Would you be open to a 30-min chat?"
No exclamation marks. Not salesy. Return DM text only.""",
        messages=[{
            "role": "user",
            "content": f"Podcast: {user_query}\n\nGuest:\n{profile_summary}"
        }]
    )

    return response.content[0].text.strip()


# ============ BACKGROUND TASK ============

async def run_search_task(search_id: str, user_query: str, handles: List[str]):
    """Background task that runs the agent and processes results."""
    search = searches[search_id]
    lead_counter = [0]

    def add_event(event: dict):
        search["events"].append(event)

    def on_status(message: str):
        step = "browsing"
        if "Initializing" in message or "Starting" in message:
            step = "parsing"
        elif "Analyzing" in message:
            step = "extracting"

        add_event({"type": "status", "message": message, "step": step})

    def on_lead(raw_lead: dict):
        try:
            # Score
            score_result = score_lead(user_query, raw_lead)
            score = score_result.get("match_score", 0)
            reason = score_result.get("match_reason", "")

            if score < 60:
                add_event({
                    "type": "status",
                    "message": f"Skipping {raw_lead['twitter_handle']} (score: {score})",
                    "step": "scoring"
                })
                return

            # Generate outreach
            outreach = generate_outreach(user_query, raw_lead)

            # Build lead
            lead_counter[0] += 1
            lead = {
                "id": f"lead_{lead_counter[0]:03d}",
                "name": raw_lead.get("name", ""),
                "twitter_handle": raw_lead.get("twitter_handle", ""),
                "twitter_url": raw_lead.get("twitter_url", ""),
                "bio": raw_lead.get("bio", ""),
                "followers": raw_lead.get("followers", 0),
                "profile_image_url": raw_lead.get("profile_image_url", ""),
                "match_score": score,
                "match_reason": reason,
                "recent_tweets": raw_lead.get("recent_tweets", []),
                "outreach_dm": outreach
            }

            search["leads"].append(lead)
            add_event({"type": "lead", "data": lead})

        except Exception as e:
            add_event({
                "type": "status",
                "message": f"Error scoring {raw_lead.get('twitter_handle', '?')}: {str(e)[:50]}",
                "step": "scoring"
            })

    # Run agent
    try:
        add_event({"type": "status", "message": "Parsing your query...", "step": "parsing"})

        await run_agent_async(
            handles=handles,
            on_status=on_status,
            on_lead=on_lead,
            config=AgentConfig(max_profiles=10, timeout_seconds=180)
        )

    except Exception as e:
        add_event({"type": "status", "message": f"Agent error: {str(e)}", "step": "error"})

    search["status"] = "completed"
    add_event({"type": "done", "total_leads": len(search["leads"])})


# ============ API ENDPOINTS ============

@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/api/search", response_model=SearchResponse)
async def start_search(request: SearchRequest):
    """Start a new search. Returns immediately with search_id."""
    search_id = str(uuid.uuid4())

    searches[search_id] = {
        "query": request.query,
        "status": "running",
        "created_at": datetime.utcnow().isoformat(),
        "leads": [],
        "events": []
    }

    try:
        parsed = parse_query(request.query)
        handles = parsed.get("handles", [])

        if not handles:
            raise ValueError("No handles suggested")

    except Exception as e:
        searches[search_id]["events"].append({
            "type": "status", "message": f"Query parsing failed: {e}", "step": "error"
        })
        searches[search_id]["events"].append({"type": "done", "total_leads": 0})
        searches[search_id]["status"] = "failed"
        return SearchResponse(search_id=search_id)

    asyncio.create_task(run_search_task(search_id, request.query, handles))
    return SearchResponse(search_id=search_id)


@app.get("/api/search/{search_id}/stream")
async def stream_search(search_id: str):
    """SSE endpoint for streaming search results."""
    if search_id not in searches:
        raise HTTPException(status_code=404, detail="Search not found")

    async def event_generator():
        last_index = 0
        while True:
            search = searches.get(search_id)
            if not search:
                break

            events = search.get("events", [])
            while last_index < len(events):
                event = events[last_index]
                yield {"event": "message", "data": json.dumps(event)}
                last_index += 1
                if event.get("type") == "done":
                    return

            await asyncio.sleep(0.3)

    return EventSourceResponse(event_generator())


@app.get("/api/search/{search_id}/export")
async def export_search(search_id: str):
    """Export leads as CSV."""
    if search_id not in searches:
        raise HTTPException(status_code=404, detail="Search not found")

    import csv
    import io

    leads = searches[search_id].get("leads", [])
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(["name", "twitter_handle", "twitter_url", "bio",
                     "followers", "match_score", "match_reason", "outreach_dm"])

    for lead in leads:
        writer.writerow([
            lead.get("name", ""),
            lead.get("twitter_handle", ""),
            lead.get("twitter_url", ""),
            lead.get("bio", "").replace("\n", " "),
            lead.get("followers", 0),
            lead.get("match_score", 0),
            lead.get("match_reason", ""),
            lead.get("outreach_dm", "").replace("\n", " ")
        ])

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=podpipe-{search_id[:8]}.csv"}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

---

## API Contract

These match PLAN.md exactly:

### `POST /api/search`
```
Request:  { "query": "bootstrapped SaaS founder who gives tactical advice" }
Response: { "search_id": "uuid-string" }
```

### `GET /api/search/:search_id/stream` (SSE)

Events:
```json
{"type": "status", "message": "Parsing your query...", "step": "parsing"}
{"type": "status", "message": "Starting KERNEL cloud browser...", "step": "browsing"}
{"type": "status", "message": "Analyzing @levelsio's profile...", "step": "extracting"}
{"type": "lead", "data": {"id": "lead_001", "name": "...", "match_score": 92, ...}}
{"type": "done", "total_leads": 5}
```

### `GET /api/search/:search_id/export`
Returns CSV file download.

---

## Testing

### 1. Test the agent directly:
```bash
cd agent
python -c "
import sys; sys.path.insert(0, '..')
from agent import run_agent
run_agent(
    handles=['@levelsio', '@marckohlbrugge'],
    on_status=print,
    on_lead=lambda l: print(f'LEAD: {l[\"name\"]}')
)
"
```

### 2. Start the API server:
```bash
cd api
uvicorn main:app --reload --port 8000
```

### 3. Test with curl:
```bash
# Health check
curl http://localhost:8000/health

# Start a search
curl -X POST http://localhost:8000/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "bootstrapped SaaS founder"}'

# Stream results (use the search_id from above)
curl -N http://localhost:8000/api/search/YOUR_SEARCH_ID/stream

# Export CSV
curl http://localhost:8000/api/search/YOUR_SEARCH_ID/export -o leads.csv
```

### 4. Test SSE in browser console:
```javascript
const es = new EventSource('http://localhost:8000/api/search/YOUR_SEARCH_ID/stream');
es.onmessage = (e) => console.log(JSON.parse(e.data));
es.onerror = (e) => console.error('SSE error', e);
```

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'agent'"
The agent isn't in Python path. Make sure you have this in main.py:
```python
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
```

### "TZAFON_API_KEY not set" or "KERNEL_API_KEY not set"
You need to load the agent's .env file. Add this to main.py:
```python
load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'agent', '.env'))
```

### "No handles suggested by LLM"
The LLM returned empty handles. Check:
- Is `ANTHROPIC_API_KEY` set correctly?
- Is the query too vague?

### Agent takes too long
Default timeout is 3 minutes. Each profile takes ~10-15 seconds. Reduce `max_profiles` in config.

### SSE connection drops
Frontend should reconnect. Add reconnection logic:
```javascript
function connect() {
    const es = new EventSource(url);
    es.onerror = () => setTimeout(connect, 1000);
}
```

### LLM suggests fake handles
The agent will skip them automatically. No action needed - just ensure you suggest 10-15 handles so enough real ones work.

---

## Checklist

- [ ] Python 3.9+ installed
- [ ] `pip install fastapi uvicorn sse-starlette anthropic python-dotenv`
- [ ] `api/.env` has `ANTHROPIC_API_KEY`
- [ ] `api/main.py` loads BOTH env files (api + agent)
- [ ] `api/main.py` adds agent to sys.path
- [ ] Test: `curl http://localhost:8000/health` returns `{"status": "ok"}`
- [ ] Test: POST to `/api/search` returns `search_id`
- [ ] Test: SSE streaming works
- [ ] Test: CSV export works
- [ ] CORS works with frontend

---

## File Structure

```
tzafon-hackathon/
├── agent/                    # Person A's code (DONE)
│   ├── __init__.py
│   ├── agent_async.py
│   ├── cua.py
│   ├── requirements.txt
│   ├── .env                  # TZAFON + KERNEL keys
│   └── CONTEXT.md            # This file
│
├── api/                      # Person B's code (YOU)
│   ├── main.py
│   ├── requirements.txt
│   └── .env                  # ANTHROPIC key
│
└── PLAN.md
```
