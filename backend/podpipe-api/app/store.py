from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from app.models import ScoredLead, SearchEvent, SearchRecord


@dataclass
class ManagedSearch:
    record: SearchRecord


class SearchStore:
    def __init__(self) -> None:
        self._searches: dict[str, ManagedSearch] = {}

    async def create(
        self,
        search_id: str,
        query: str,
        seed_handles: list[str] | None = None,
        podcast_description: str = ""
    ) -> SearchRecord:
        record = SearchRecord(
            id=search_id,
            query=query,
            seed_handles=seed_handles or [],
            podcast_description=podcast_description
        )
        self._searches[search_id] = ManagedSearch(record=record)
        return record

    async def get(self, search_id: str) -> Optional[ManagedSearch]:
        return self._searches.get(search_id)

    async def append_event(self, search_id: str, event: SearchEvent) -> None:
        managed = await self.get(search_id)
        if managed is None:
            return
        managed.record.events.append(event)

    async def append_lead(self, search_id: str, lead: ScoredLead) -> None:
        managed = await self.get(search_id)
        if managed is None:
            return
        managed.record.leads.append(lead)
        managed.record.events.append(SearchEvent(type="lead", data=lead))

    async def complete(self, search_id: str) -> None:
        managed = await self.get(search_id)
        if managed is None:
            return
        managed.record.status = "completed"
        managed.record.events.append(
            SearchEvent(type="done", total_leads=len(managed.record.leads))
        )

    async def fail(self, search_id: str, message: str) -> None:
        managed = await self.get(search_id)
        if managed is None:
            return
        managed.record.status = "failed"
        managed.record.error = message
        managed.record.events.append(SearchEvent(type="error", message=message))
