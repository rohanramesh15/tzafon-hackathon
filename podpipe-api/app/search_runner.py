from __future__ import annotations

from uuid import uuid4

from app.agent_adapter import run_agent_adapter
from app.llm import generate_outreach, parse_query, score_lead
from app.models import ProfileData, ScoredLead, SearchEvent
from app.store import SearchStore

MIN_MATCH_SCORE = 60


async def run_search(search_id: str, store: SearchStore) -> None:
    managed = await store.get(search_id)
    if managed is None:
        return

    user_query = managed.record.query
    seed_handles = managed.record.seed_handles
    podcast_description = managed.record.podcast_description

    try:
        await store.append_event(
            search_id,
            SearchEvent(type="status", message="Parsing your query...", step="parsing"),
        )
        parsed = await parse_query(user_query)

        async def on_status(message: str, step: str) -> None:
            await store.append_event(
                search_id,
                SearchEvent(type="status", message=message, step=step),
            )

        async def on_lead(profile: ProfileData) -> None:
            await store.append_event(
                search_id,
                SearchEvent(
                    type="status",
                    message=f"Scoring {profile.twitter_handle}...",
                    step="scoring",
                ),
            )
            score = await score_lead(user_query, profile)
            if score.match_score < MIN_MATCH_SCORE:
                await store.append_event(
                    search_id,
                    SearchEvent(
                        type="status",
                        message=f"Skipping {profile.twitter_handle} (score: {score.match_score})",
                        step="scoring",
                    ),
                )
                return

            outreach = await generate_outreach(user_query, profile)
            lead = ScoredLead(
                **profile.model_dump(),
                id=f"lead_{uuid4().hex[:8]}",
                match_score=score.match_score,
                match_reason=score.match_reason,
                outreach_dm=outreach,
            )
            await store.append_lead(search_id, lead)

        await store.append_event(
            search_id,
            SearchEvent(
                type="status",
                message=f"Checking {len(parsed.handles)} suggested Twitter handles...",
                step="browsing",
            ),
        )
        await run_agent_adapter(parsed.handles, on_status, on_lead)
        await store.complete(search_id)
    except Exception as exc:
        await store.fail(search_id, str(exc))
