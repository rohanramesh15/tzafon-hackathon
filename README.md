# PodPipe

> Find podcast guests who actually know what they're talking about.

**Live:** [podpipe.vercel.app](https://podpipe.vercel.app/)
**Repo:** [github.com/rohanramesh15/tzafon-hackathon](https://github.com/rohanramesh15/tzafon-hackathon)

---

## Demo

https://github.com/user-attachments/assets/demo.mov

---

## The Problem

Finding good podcast guests is tedious. Hosts spend hours scrolling Twitter, LinkedIn, and newsletters trying to find people who:
- Actually have expertise (not just opinions)
- Post substantive content (not just retweets)
- Would realistically say yes to an interview

Most end up reaching out to the same overexposed names, or worse, sending cold DMs to people who don't fit at all.

---

## What PodPipe Does

You describe who you're looking for in plain English:

> "Indie hackers building AI tools who share revenue numbers publicly"

PodPipe then:
1. Parses your query to understand intent, role, and vibe
2. Searches Twitter for matching profiles using an agentic pipeline
3. Scores each candidate on topic relevance, credibility, and podcast-readiness
4. Generates a personalized outreach DM for each match

Results stream in real-time. You export the ones you like as CSV.

---

## Design Decisions

**Auto-filter detection over follow-up questions**
We tested two UX flows: asking clarifying MCQs vs. auto-detecting filters as the user types. Chose auto-detection—it's faster, less interruptive, and feels more like the app "gets" you.

**Streaming results instead of loading states**
Guests appear one-by-one as they're found and scored. This keeps the experience alive and lets users start reviewing immediately instead of waiting for a batch.

**Personalized outreach by default**
Every match comes with a ready-to-send DM that references something specific from their bio or recent tweets. The goal: zero friction from "I like this person" to "I've messaged them."

---

## Technical Decisions

**SSE streaming over polling**
Used Server-Sent Events to push search progress and leads to the frontend in real-time. Keeps the UI responsive without hammering the server with requests.

**LLM-powered scoring pipeline**
Each candidate is scored on topic relevance, credibility, content quality, and podcast readiness. A minimum threshold (60) filters out weak matches before generating outreach—saves API calls and keeps results high-quality.

**Blacklisting overused handles**
The LLM was defaulting to the same popular accounts (@levelsio, @marckohlbrugge, etc.) for every query. Fixed by explicitly excluding them in the prompt and biasing toward lesser-known voices (5K-100K followers) who are more likely to engage.

**Agentic browser automation**
Twitter profiles are fetched via a headless browser agent that extracts bios, follower counts, and recent tweets. This avoids API rate limits and gets richer data than the official endpoints.

---

## Stack

| Layer | Tech |
|-------|------|
| Frontend | React, TypeScript, TailwindCSS, TanStack Query |
| Backend | FastAPI, Pydantic, SSE |
| LLM | Claude (Anthropic) |
| Agent | Browser automation with structured extraction |
| Infra | Vercel (frontend), Railway (backend) |

---

## Run Locally

```bash
# Backend
cd podpipe-api
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # add your ANTHROPIC_API_KEY
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

