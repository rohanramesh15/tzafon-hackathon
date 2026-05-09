from __future__ import annotations

import json
import logging
import os
import re
import sys
from typing import Any

from dotenv import load_dotenv

from app.models import ParsedQuery, ProfileData, ScoreResult, QueryAnalysisResult, FollowUpQuestion, QuestionOption

logging.basicConfig(level=logging.INFO, stream=sys.stdout, force=True)
logger = logging.getLogger(__name__)

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


def _build_parse_prompt(seed_handles: list[str], podcast_description: str) -> str:
    """Build the parse prompt with optional context from seeds and podcast description."""

    # If we have seeds, use a more targeted prompt
    if seed_handles:
        handles_str = ", ".join(seed_handles)
        prompt = f"""You are finding podcast guests on Twitter similar to specific examples.

The podcaster likes these accounts: {handles_str}

{f"Podcast context: {podcast_description.strip()}" if podcast_description.strip() else ""}

Based on these examples, suggest 10-15 SIMILAR Twitter accounts.

Think about:
- What topics do these example accounts tweet about?
- What's their follower range (similar size)?
- What makes them good podcast material?
- Who else is in their network/niche?

CRITICAL RULES:
1. Do NOT suggest the example accounts themselves ({handles_str})
2. Suggest REAL, EXISTING Twitter accounts only
3. Think of lesser-known accounts in the same space, not just the famous ones
4. Diversify - don't just suggest the most obvious names

Output JSON only:
{{"keywords": ["topic1", "topic2"], "role": "founder|investor|creator", "vibe": "tactical|storyteller", "handles": ["@handle1", "@handle2", ...]}}

No markdown, no backticks, no explanation."""
        return prompt

    # No seeds - use the base prompt
    prompt = PARSE_SYSTEM_PROMPT_BASE
    if podcast_description.strip():
        prompt = f"Podcast context: {podcast_description.strip()}\n\n" + prompt

    return prompt

ANALYZE_QUERY_PROMPT = """You are analyzing a podcast guest search query to determine if it needs clarification.

A query is SPECIFIC ENOUGH if it includes at least 2 of these:
1. Industry/domain (e.g., "SaaS", "AI", "fintech", "e-commerce")
2. Role (e.g., "founder", "investor", "developer", "marketer")
3. Specific characteristic (e.g., "bootstrapped", "raised Series A", "solo", "$1M ARR")
4. Content style (e.g., "tactical advice", "storytelling", "contrarian takes")

If the query is vague (e.g., "someone interesting", "a founder", "tech person"), generate 2-3 follow-up questions to clarify.

Each question should have 3-4 concrete options that help narrow down the search.

Respond in JSON:
{
  "needs_clarification": true/false,
  "questions": [
    {
      "id": "industry",
      "question": "What industry should they be in?",
      "options": [
        {"id": "saas", "label": "SaaS / Software"},
        {"id": "ai", "label": "AI / Machine Learning"},
        {"id": "fintech", "label": "Fintech"},
        {"id": "ecommerce", "label": "E-commerce / DTC"}
      ]
    }
  ]
}

If the query is specific enough, return:
{"needs_clarification": false, "questions": []}

No markdown, no backticks."""


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


async def parse_query(
    raw_query: str,
    seed_handles: list[str] | None = None,
    podcast_description: str = ""
) -> ParsedQuery:
    seed_handles = seed_handles or []

    if use_mock_llm():
        logger.info("[LLM] Using mock mode (USE_MOCK_LLM=true)")
        return _fallback_parse(raw_query)

    if not os.getenv("ANTHROPIC_API_KEY"):
        logger.info("[LLM] No ANTHROPIC_API_KEY, using fallback")
        return _fallback_parse(raw_query)

    try:
        system_prompt = _build_parse_prompt(seed_handles, podcast_description)
        logger.info(f"[LLM] Calling Claude with seeds={seed_handles}, desc={podcast_description[:50] if podcast_description else 'none'}")
        content = await _claude_message(system_prompt, raw_query)
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


def _fallback_analyze_query(raw_query: str) -> QueryAnalysisResult:
    """Fallback analysis when LLM is unavailable - always requires clarification for short queries."""
    words = raw_query.lower().split()
    # Very simple heuristic: if query has fewer than 5 words, ask for clarification
    if len(words) < 5:
        return QueryAnalysisResult(
            needs_clarification=True,
            questions=[
                FollowUpQuestion(
                    id="industry",
                    question="What industry should they be in?",
                    type="single_choice",
                    options=[
                        QuestionOption(id="saas", label="SaaS / Software"),
                        QuestionOption(id="ai", label="AI / Machine Learning"),
                        QuestionOption(id="fintech", label="Fintech"),
                        QuestionOption(id="ecommerce", label="E-commerce / DTC"),
                    ]
                ),
                FollowUpQuestion(
                    id="stage",
                    question="What stage should they be at?",
                    type="single_choice",
                    options=[
                        QuestionOption(id="bootstrapped", label="Bootstrapped / Indie"),
                        QuestionOption(id="seed", label="Seed / Early Stage"),
                        QuestionOption(id="growth", label="Series A+ / Growth"),
                        QuestionOption(id="any", label="Any stage"),
                    ]
                ),
            ]
        )
    return QueryAnalysisResult(needs_clarification=False, questions=[])


async def analyze_query(raw_query: str) -> QueryAnalysisResult:
    """Analyze if a query needs clarification and generate follow-up questions."""
    logger.info(f"[LLM] Analyzing query: {raw_query}")

    if use_mock_llm():
        logger.info("[LLM] Using mock mode for query analysis")
        return _fallback_analyze_query(raw_query)

    if not os.getenv("ANTHROPIC_API_KEY"):
        logger.info("[LLM] No ANTHROPIC_API_KEY, using fallback analysis")
        return _fallback_analyze_query(raw_query)

    try:
        content = await _claude_message(ANALYZE_QUERY_PROMPT, raw_query)
        logger.info(f"[LLM] Query analysis response: {content[:300]}...")
        data = _json_from_text(content)

        # Parse questions with proper models
        questions = []
        for q in data.get("questions", []):
            options = [QuestionOption(id=opt["id"], label=opt["label"]) for opt in q.get("options", [])]
            questions.append(FollowUpQuestion(
                id=q["id"],
                question=q["question"],
                type=q.get("type", "single_choice"),
                options=options
            ))

        result = QueryAnalysisResult(
            needs_clarification=data.get("needs_clarification", False),
            questions=questions
        )
        logger.info(f"[LLM] Query analysis result: needs_clarification={result.needs_clarification}, num_questions={len(result.questions)}")
        return result
    except Exception as e:
        logger.error(f"[LLM] Error analyzing query: {e}, using fallback")
        return _fallback_analyze_query(raw_query)
