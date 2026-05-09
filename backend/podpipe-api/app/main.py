from __future__ import annotations

import asyncio
import json
import os
import uvicorn
from uuid import uuid4

from fastapi import BackgroundTasks, FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse, StreamingResponse

from .csv_export import leads_to_csv
from .llm import detect_filters
from .models import DetectFiltersRequest, DetectFiltersResponse, SearchRequest, SearchResponse
from .search_runner import run_search
from .store import SearchStore

_cors_origins = [o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",")]

app = FastAPI(title="PodPipe API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

store = SearchStore()


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/detect-filters", response_model=DetectFiltersResponse)
async def detect_filters_endpoint(request: DetectFiltersRequest) -> DetectFiltersResponse:
    filters = await detect_filters(request.query)
    return DetectFiltersResponse(filters=filters)


@app.post("/api/search", response_model=SearchResponse)
async def start_search(
    request: SearchRequest, background_tasks: BackgroundTasks
) -> SearchResponse:
    search_id = str(uuid4())
    await store.create(search_id, request.query)
    background_tasks.add_task(run_search, search_id, store)
    return SearchResponse(search_id=search_id)


@app.get("/api/search/{search_id}/stream")
async def stream_search(search_id: str) -> StreamingResponse:
    managed = await store.get(search_id)
    if managed is None:
        raise HTTPException(status_code=404, detail="search_id not found")

    async def event_generator():
        index = 0
        while True:
            while index < len(managed.record.events):
                event = managed.record.events[index]
                index += 1
                data = event.model_dump(mode="json", exclude_none=True)
                yield f"data: {json.dumps(data)}\n\n"

            if managed.record.status in {"completed", "failed"}:
                break

            await asyncio.sleep(0.05)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.get("/api/search/{search_id}/export")
async def export_search(search_id: str) -> Response:
    managed = await store.get(search_id)
    if managed is None:
        raise HTTPException(status_code=404, detail="search_id not found")

    csv_text = leads_to_csv(managed.record.leads)
    return PlainTextResponse(
        csv_text,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="podpipe-leads.csv"'},
    )


if __name__ == "__main__":

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
