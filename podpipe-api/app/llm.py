from __future__ import annotations

import json
import os
import re
from typing import Any

from dotenv import load_dotenv

from app.models import ParsedQuery, ProfileData, ScoreResult

load_dotenv()
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "agent", ".env"))


PARSE_SYSTEM_PROMPT = """You are a search query parser for finding podcast guests on Twitter.
Given a natural language description of who the podcaster wants as a guest, you must:
1. Extract structured information about the request
2. Suggest 10-15 REAL Twitter handles of people who match this description

CRITICAL: You must suggest REAL, EXISTING Twitter accounts. Think of actual well-known people in the tech/startup space. Do NOT make up handles.

Examples of real handles by category:
- Bootstrapped SaaS founders: @levelsio, @marckohlbrugge, @csallen, @shl, @ajlkn
- Indie hackers: @dannypostmaa, @arvidkahl, @jonbstrong
- VCs/Investors: @paulg, @sama, @naval, @jason
- AI/ML: @ylecun, @hardmaru, @AndrewYNg

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

OUTREACH_SYSTEM_PROMPT = """Write a short Twitter DM (3-4 sentences) inviting this person to be a podcast guest.

Rules:
- Reference something specific from their bio or recent tweets
- Mention what the podcast is about (infer from the user's query)
- Keep it casual and direct, not salesy
- End with a low-commitment ask ("Would you be open to a 30-min chat?")
- Don't use exclamation marks excessively

Respond with the DM text only, no JSON, no quotes."""


def use_mock_llm() -> bool:
    return os.getenv("USE_MOCK_LLM", "true").lower() in {"1", "true", "yes", "on"}


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
    handles = ["@levelsio", "@marckohlbrugge", "@csallen", "@shl", "@ajlkn"]
    if any(term in lowered for term in ["indie", "build in public", "solo"]):
        handles.extend(["@dannypostmaa", "@arvidkahl", "@jonbstrong"])
    if any(term in lowered for term in ["investor", "vc", "fundraising"]):
        handles.extend(["@paulg", "@sama", "@naval", "@jason"])
    if any(term in lowered for term in ["ai", "ml", "machine learning"]):
        handles.extend(["@ylecun", "@hardmaru", "@AndrewYNg"])
    if any(term in lowered for term in ["dev tool", "developer", "plg"]):
        handles.extend(["@guillarmand", "@adamwathan"])

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


async def parse_query(raw_query: str) -> ParsedQuery:
    if use_mock_llm() or not os.getenv("ANTHROPIC_API_KEY"):
        return _fallback_parse(raw_query)

    try:
        content = await _claude_message(PARSE_SYSTEM_PROMPT, raw_query)
        return ParsedQuery.model_validate(_json_from_text(content))
    except Exception:
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
    if use_mock_llm() or not os.getenv("ANTHROPIC_API_KEY"):
        return _fallback_score(user_query, profile_data)

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
    if use_mock_llm() or not os.getenv("ANTHROPIC_API_KEY"):
        return _fallback_outreach(user_query, profile_data)

    payload = json.dumps(
        {"user_query": user_query, "profile_data": profile_data.model_dump()},
        ensure_ascii=True,
    )
    try:
        content = await _claude_message(OUTREACH_SYSTEM_PROMPT, payload)
        return content.strip().strip('"')
    except Exception:
        return _fallback_outreach(user_query, profile_data)
