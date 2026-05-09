from __future__ import annotations

import json
import logging
import os
import re
import sys
from typing import Any

from dotenv import load_dotenv

from app.models import ParsedQuery, ProfileData, ScoreResult

logging.basicConfig(level=logging.INFO, stream=sys.stdout, force=True)
logger = logging.getLogger(__name__)

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))
load_dotenv()
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "agent", ".env"))


PARSE_SYSTEM_PROMPT_BASE = """You are a search query parser for finding podcast guests on Twitter.
Given a natural language description of who the podcaster wants as a guest, you must:
1. Extract structured information about the request
2. Suggest 10-15 REAL Twitter handles of people who match this description

CRITICAL RULES:
1. Suggest REAL, EXISTING Twitter accounts only - do NOT make up handles
2. DO NOT suggest these overused accounts: @levelsio, @marckohlbrugge, @csallen, @shl, @arvidkahl, @paulg, @sama, @naval
3. Think of LESSER-KNOWN but still credible accounts in the relevant niche
4. Diversify across different sub-niches and follower counts
5. Consider people who actively engage on Twitter and would likely respond to podcast invites

Think creatively about who matches the description. Consider:
- People who tweet about the specific topic mentioned
- Rising voices in the space, not just the famous ones
- People with 5K-100K followers (more likely to engage)
- Those who share tactical/practical content

Output format:
{
  "keywords": ["keyword1", "keyword2"],
  "role": "founder|investor|creator|operator|researcher",
  "vibe": "tactical|storyteller|contrarian|educational",
  "handles": ["@handle1", "@handle2", "@handle3"]
}

Respond in JSON only. No markdown, no backticks."""


SCORE_SYSTEM_PROMPT = """You are evaluating whether a Twitter user would be a good podcast guest.

Given the podcaster's request and the candidate's profile, return:
- match_score: 0-100 (how well they fit the request)
- match_reason: 1-2 sentences explaining why they're a good/bad fit

Score based on:
- Topic relevance (do they tweet about the right stuff?)
- Credibility (do they have real experience, not just opinions?)
- Content quality (are their tweets substantive or just retweets/memes?)
- Podcast readiness (do they seem like someone who'd do interviews?)

Respond in JSON only. No markdown, no backticks."""

DETECT_FILTERS_PROMPT = """You are a filter extractor for a podcast guest search tool.

Given a natural language description of who the podcaster wants as a guest, extract values for these filters:
- Location: geographic location (city, country, region) or "Remote" if remote work is mentioned. null if not mentioned.
- Topic: main topic(s) the person talks or writes about. null if not clear.
- Audience size: any indication of follower count or audience scale (e.g. "100k followers", "niche", "large following"). null if not mentioned.
- Industry: domain or industry they work in (e.g. "SaaS", "AI", "Healthcare"). null if not clear.
- Recently active: return "yes" if recency of posting/activity is mentioned, otherwise null.

Return a single JSON object. All five keys must be present. Values are strings or null.

Example input: "A Kenya-based AI founder posting frequently about SaaS growth"
Example output:
{"Location":"Kenya","Topic":"AI / SaaS growth","Audience size":null,"Industry":"SaaS","Recently active":"yes"}

Respond with JSON only. No markdown, no backticks, no explanation."""


OUTREACH_SYSTEM_PROMPT = """Write a short Twitter DM (3-4 sentences) inviting this person to be a podcast guest.

Rules:
- Reference something specific from their bio or recent tweets
- Mention what the podcast is about (infer from the user's query)
- Keep it casual and direct, not salesy
- End with a low-commitment ask ("Would you be open to a 30-min chat?")
- Don't use exclamation marks excessively

Respond with the DM text only, no JSON, no quotes."""


async def _claude_message(system_prompt: str, user_payload: str) -> str:
    from anthropic import AsyncAnthropic

    client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    response = await client.messages.create(
        model=os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514"),
        max_tokens=900,
        temperature=0.2,
        system=system_prompt,
        messages=[{"role": "user", "content": user_payload}],
    )
    return "".join(
        block.text for block in response.content if getattr(block, "type", None) == "text"
    ).strip()


def _json_from_text(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
        if not match:
            raise
        return json.loads(match.group(0))


def _fallback_parse(raw_query: str) -> ParsedQuery:
    words = re.findall(r"[A-Za-z0-9$]+", raw_query)
    stop_words = {
        "a",
        "about",
        "and",
        "for",
        "i",
        "need",
        "of",
        "on",
        "the",
        "to",
        "who",
        "with",
    }
    keywords = [word for word in words if word.lower() not in stop_words][:6]
    if len(keywords) < 2:
        keywords = [raw_query.strip(), "podcast guest"]
    role = next(
        (
            word.lower()
            for word in words
            if word.lower() in {"founder", "investor", "operator", "creator", "researcher"}
        ),
        "guest",
    )
    lowered = raw_query.lower()
    # Use lesser-known but real handles as fallback
    handles = ["@thisiskp_", "@jasonleow", "@dagorenouf", "@_rchase_", "@tomjacquesson"]
    if any(term in lowered for term in ["indie", "build in public", "solo"]):
        handles.extend(["@AndreyAzimov", "@haborian", "@ianlandsman"])
    if any(term in lowered for term in ["investor", "vc", "fundraising"]):
        handles.extend(["@hunterwalk", "@laborvoices", "@chrija"])
    if any(term in lowered for term in ["ai", "ml", "machine learning"]):
        handles.extend(["@jeremyphoward", "@kabortz", "@dennybritz"])
    if any(term in lowered for term in ["dev tool", "developer", "plg"]):
        handles.extend(["@swyx", "@cassidoo", "@kelseyhightower"])
    if any(term in lowered for term in ["saas", "software", "b2b"]):
        handles.extend(["@Patticus", "@aaborsel", "@robjama"])

    return ParsedQuery(
        keywords=keywords,
        role=role,
        vibe="substantive",
        handles=handles,
    )


def _profile_text(profile_data: ProfileData) -> str:
    tweets = "\n".join(f"- {tweet}" for tweet in profile_data.recent_tweets)
    return (
        f"Name: {profile_data.name}\n"
        f"Handle: {profile_data.twitter_handle}\n"
        f"Bio: {profile_data.bio}\n"
        f"Followers: {profile_data.followers}\n"
        f"Recent tweets:\n{tweets}"
    )


def _fallback_detect_filters(query: str) -> dict[str, str | None]:
    q = query.lower()

    location_terms = [
        "remote", "kenya", "nairobi", "nigeria", "lagos", "ghana", "south africa",
        "usa", "united states", "new york", "san francisco", "uk", "london",
        "europe", "africa", "asia", "india", "canada", "australia", "berlin",
        "paris", "tokyo", "singapore", "dubai", "amsterdam",
    ]
    location = next((t.title() for t in location_terms if re.search(rf"\b{re.escape(t)}\b", q)), None)

    topic_keywords = [
        "ai", "machine learning", "crypto", "blockchain", "climate", "fintech",
        "saas", "web3", "startups", "entrepreneurship", "investing", "fundraising",
        "growth", "marketing", "product", "design",
    ]
    topic = next((t.upper() if len(t) <= 3 else t.title() for t in topic_keywords if re.search(rf"\b{re.escape(t)}\b", q)), None)
    if not topic:
        m = re.search(r"(?:about|discusses?|talks? about|covers?)\s+(\w+(?:\s+\w+)?)", q)
        topic = m.group(1).title() if m else None

    audience = next((m.group(0) for p in [
        r"\b\d+k\b", r"\b\d+,\d{3}\+?\s*followers?\b", r"\bmicro[\s-]influencer\b",
        r"\blarge audience\b", r"\bniche audience\b",
    ] if (m := re.search(p, q))), None)

    industry_terms = [
        "saas", "fintech", "healthtech", "edtech", "biotech", "crypto", "web3",
        "media", "finance", "healthcare", "education", "retail", "consulting", "gaming",
    ]
    industry = next((t.title() for t in industry_terms if re.search(rf"\b{re.escape(t)}\b", q)), None)
    if not industry and re.search(r"\btech(?:nology)?\b", q):
        industry = "Tech"

    recently_active = "yes" if re.search(
        r"\b(recently|active|posts?\s+(?:regularly|often|frequently)|last\s+(?:week|month|year)|this\s+(?:week|month|year))\b", q
    ) else None

    return {
        "Location": location,
        "Topic": topic,
        "Audience size": audience,
        "Industry": industry,
        "Recently active": recently_active,
    }


async def detect_filters(query: str) -> dict[str, str | None]:
    try:
        content = await _claude_message(DETECT_FILTERS_PROMPT, query)
        raw = _json_from_text(content)
        keys = ["Location", "Topic", "Audience size", "Industry", "Recently active"]
        return {k: raw.get(k) or None for k in keys}
    except Exception:
        return _fallback_detect_filters(query)


async def parse_query(raw_query: str) -> ParsedQuery:
    try:
        logger.info(f"[LLM] Calling Claude for query: {raw_query[:50]}...")
        content = await _claude_message(PARSE_SYSTEM_PROMPT_BASE, raw_query)
        logger.info(f"[LLM] Claude response: {content[:200]}...")
        result = ParsedQuery.model_validate(_json_from_text(content))
        logger.info(f"[LLM] Parsed handles: {result.handles}")
        return result
    except Exception as e:
        logger.error(f"[LLM] Error calling Claude: {e}, using fallback")
        return _fallback_parse(raw_query)


def _fallback_score(user_query: str, profile_data: ProfileData) -> ScoreResult:
    haystack = " ".join(
        [profile_data.name, profile_data.bio, " ".join(profile_data.recent_tweets)]
    ).lower()
    query_terms = {
        term.lower()
        for term in re.findall(r"[A-Za-z0-9]+", user_query)
        if len(term) > 2
    }
    matches = sum(1 for term in query_terms if term in haystack)
    score = min(95, 55 + matches * 10)
    if any(word in haystack for word in ["founder", "built", "arr", "mrr", "yc"]):
        score += 10
    score = max(35, min(100, score))
    reason = (
        f"{profile_data.name} appears relevant based on their bio and recent posts, "
        "with enough concrete operating experience to be worth reviewing."
    )
    return ScoreResult(match_score=score, match_reason=reason)


async def score_lead(user_query: str, profile_data: ProfileData) -> ScoreResult:
    payload = json.dumps(
        {"user_query": user_query, "profile_data": profile_data.model_dump()},
        ensure_ascii=True,
    )
    try:
        content = await _claude_message(SCORE_SYSTEM_PROMPT, payload)
        return ScoreResult.model_validate(_json_from_text(content))
    except Exception:
        return _fallback_score(user_query, profile_data)


def _fallback_outreach(user_query: str, profile_data: ProfileData) -> str:
    reference = profile_data.recent_tweets[0] if profile_data.recent_tweets else profile_data.bio
    return (
        f"Hey {profile_data.name.split()[0]}, I run a podcast about {user_query}. "
        f"I liked your perspective on {reference[:120].rstrip()}. "
        "It feels like the kind of specific, useful story our listeners would learn from. "
        "Would you be open to a 30-min chat?"
    )


async def generate_outreach(user_query: str, profile_data: ProfileData) -> str:
    payload = json.dumps(
        {"user_query": user_query, "profile_data": profile_data.model_dump()},
        ensure_ascii=True,
    )
    try:
        content = await _claude_message(OUTREACH_SYSTEM_PROMPT, payload)
        return content.strip().strip('"')
    except Exception:
        return _fallback_outreach(user_query, profile_data)
