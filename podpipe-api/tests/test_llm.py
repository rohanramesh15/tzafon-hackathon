import pytest

from app.llm import generate_outreach, parse_query, score_lead
from app.models import ProfileData


@pytest.fixture
def profile():
    return ProfileData(
        name="Maya Chen",
        twitter_handle="@mayachen",
        twitter_url="https://twitter.com/mayachen",
        bio="Bootstrapped a dev tools SaaS to $2M ARR. Writes about PLG.",
        followers=18400,
        recent_tweets=["We crossed $2M ARR after rebuilding onboarding around activation."],
    )


@pytest.mark.asyncio
async def test_parse_query_returns_handles(monkeypatch):
    monkeypatch.setenv("USE_MOCK_LLM", "true")
    parsed = await parse_query("YC founder who bootstrapped dev tools and tweets about PLG")
    assert len(parsed.handles) >= 5
    assert all(handle.startswith("@") for handle in parsed.handles)
    assert parsed.role in {"founder", "guest"}


@pytest.mark.asyncio
async def test_score_lead_returns_valid_score(monkeypatch, profile):
    monkeypatch.setenv("USE_MOCK_LLM", "true")
    score = await score_lead("bootstrapped SaaS founder PLG", profile)
    assert 0 <= score.match_score <= 100
    assert score.match_reason


@pytest.mark.asyncio
async def test_generate_outreach_returns_dm(monkeypatch, profile):
    monkeypatch.setenv("USE_MOCK_LLM", "true")
    dm = await generate_outreach("bootstrapped SaaS founder PLG", profile)
    assert "Maya" in dm
    assert "30-min chat" in dm
