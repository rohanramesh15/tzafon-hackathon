from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator


SearchStatus = Literal["running", "completed", "failed"]
EventType = Literal["status", "lead", "done", "error"]


class QuestionOption(BaseModel):
    id: str
    label: str


class FollowUpQuestion(BaseModel):
    id: str
    question: str
    type: str = "single_choice"  # "single_choice" or "text"
    options: list[QuestionOption] = Field(default_factory=list)


class QueryAnalysisResult(BaseModel):
    needs_clarification: bool
    questions: list[FollowUpQuestion] = Field(default_factory=list)
    ready_to_search: bool = False


class AnalyzeQueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)


class AnalyzeQueryResponse(BaseModel):
    needs_clarification: bool
    questions: list[FollowUpQuestion] = Field(default_factory=list)


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    seed_handles: list[str] = Field(default_factory=list)
    podcast_description: str = ""
    clarification_answers: dict[str, str] = Field(default_factory=dict)  # question_id -> answer

    @field_validator("query")
    @classmethod
    def normalize_query(cls, value: str) -> str:
        return value.strip()

    @field_validator("seed_handles")
    @classmethod
    def normalize_seed_handles(cls, value: list[str]) -> list[str]:
        cleaned = []
        for h in value:
            handle = h.strip().lstrip("@")
            if handle:
                cleaned.append(f"@{handle}")
        return cleaned[:5]  # Max 5 seed handles


class SearchResponse(BaseModel):
    search_id: str


class ParsedQuery(BaseModel):
    keywords: list[str] = Field(default_factory=list)
    role: str = "guest"
    vibe: str = "substantive"
    handles: list[str]

    @field_validator("handles")
    @classmethod
    def validate_handles(cls, value: list[str]) -> list[str]:
        cleaned: list[str] = []
        for item in value:
            handle = item.strip().split("/")[-1].strip()
            if not handle:
                continue
            handle = handle if handle.startswith("@") else f"@{handle}"
            if handle not in cleaned:
                cleaned.append(handle)
        if not cleaned:
            raise ValueError("at least one Twitter handle is required")
        return cleaned[:15]


class ProfileData(BaseModel):
    name: str
    twitter_handle: str
    twitter_url: str
    bio: str = ""
    followers: int = 0
    profile_image_url: Optional[str] = None
    recent_tweets: list[str] = Field(default_factory=list)

    @field_validator("twitter_handle")
    @classmethod
    def normalize_handle(cls, value: str) -> str:
        handle = value.strip()
        return handle if handle.startswith("@") else f"@{handle}"


class ScoredLead(ProfileData):
    id: str
    match_score: int = Field(..., ge=0, le=100)
    match_reason: str
    outreach_dm: str


class ScoreResult(BaseModel):
    match_score: int = Field(..., ge=0, le=100)
    match_reason: str


class SearchEvent(BaseModel):
    type: EventType
    message: Optional[str] = None
    step: Optional[str] = None
    data: Optional[ScoredLead] = None
    total_leads: Optional[int] = None


class SearchRecord(BaseModel):
    id: str
    query: str
    seed_handles: list[str] = Field(default_factory=list)
    podcast_description: str = ""
    status: SearchStatus = "running"
    events: list[SearchEvent] = Field(default_factory=list)
    leads: list[ScoredLead] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    error: Optional[str] = None
