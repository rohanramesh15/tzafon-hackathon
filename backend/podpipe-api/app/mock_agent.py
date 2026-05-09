from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable

from app.models import ProfileData

StatusCallback = Callable[[str, str], Awaitable[None]]
LeadCallback = Callable[[ProfileData], Awaitable[None]]


MOCK_PROFILES = [
    ProfileData(
        name="Maya Chen",
        twitter_handle="@mayachen",
        twitter_url="https://twitter.com/mayachen",
        bio="Bootstrapped a dev tools SaaS to $2M ARR. Writing about PLG, onboarding, and founder-led growth.",
        followers=18400,
        profile_image_url="https://pbs.twimg.com/profile_images/mock/maya.jpg",
        recent_tweets=[
            "We crossed $2M ARR after rebuilding onboarding around one activation metric.",
            "PLG works when the product explains the value before sales ever gets involved.",
            "The best bootstrapped growth loop is still a great docs page plus a fast aha moment.",
        ],
    ),
    ProfileData(
        name="Priya Shah",
        twitter_handle="@priyashah",
        twitter_url="https://twitter.com/priyashah",
        bio="Fintech founder, ex-Stripe. Sharing fundraising notes, compliance lessons, and operator mistakes.",
        followers=27600,
        profile_image_url="https://pbs.twimg.com/profile_images/mock/priya.jpg",
        recent_tweets=[
            "Our seed round got easier when we stopped pitching TAM and showed weekly payment volume.",
            "Fintech founders underestimate compliance until it becomes the roadmap.",
            "A good investor update is short, quantitative, and honest about the ugly parts.",
        ],
    ),
    ProfileData(
        name="Leo Martinez",
        twitter_handle="@leobuilds",
        twitter_url="https://twitter.com/leobuilds",
        bio="Solo founder building in public. $52k MRR from a tiny workflow automation product.",
        followers=9300,
        profile_image_url="https://pbs.twimg.com/profile_images/mock/leo.jpg",
        recent_tweets=[
            "Hit $52k MRR today. The boring retention work mattered more than launch day.",
            "Build-in-public only works if you share decisions, numbers, and what failed.",
            "I killed two features this week because support tickets told a clearer story than my roadmap.",
        ],
    ),
    ProfileData(
        name="Taylor Reed",
        twitter_handle="@taylorshots",
        twitter_url="https://twitter.com/taylorshots",
        bio="Posting coffee photos, travel clips, and weekend playlists.",
        followers=1500,
        profile_image_url="https://pbs.twimg.com/profile_images/mock/taylor.jpg",
        recent_tweets=[
            "Perfect latte art is harder than it looks.",
            "Weekend playlist is live.",
            "Three days in Lisbon and I already want to move here.",
        ],
    ),
]


async def run_agent_adapter(
    handles: list[str],
    on_status: StatusCallback,
    on_lead: LeadCallback,
) -> None:
    seen_handles: set[str] = set()
    await on_status("Using mock Person A profile extractor...", "browsing")
    for handle in handles:
        await on_status(f"Analyzing {handle}'s profile...", "extracting")
        await asyncio.sleep(0.01)
        for profile in MOCK_PROFILES:
            if profile.twitter_handle in seen_handles:
                continue
            seen_handles.add(profile.twitter_handle)
            await asyncio.sleep(0.01)
            await on_lead(profile)
            break
