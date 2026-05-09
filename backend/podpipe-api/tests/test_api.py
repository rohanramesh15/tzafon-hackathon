import csv
import json
from io import StringIO

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def _collect_sse_events(search_id: str):
    events = []
    with client.stream("GET", f"/api/search/{search_id}/stream") as response:
        assert response.status_code == 200
        for line in response.iter_lines():
            if line.startswith("data: "):
                payload = line.removeprefix("data: ")
                event = json.loads(payload)
                events.append(event)
                if event["type"] in {"done", "error"}:
                    break
    return events


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_unknown_search_id_returns_404():
    response = client.get("/api/search/missing/stream")
    assert response.status_code == 404


def test_search_stream_and_export(monkeypatch):
    monkeypatch.setenv("USE_MOCK_LLM", "true")
    response = client.post(
        "/api/search",
        json={"query": "YC founder who bootstrapped a dev tools company and tweets about PLG"},
    )
    assert response.status_code == 200
    search_id = response.json()["search_id"]

    events = _collect_sse_events(search_id)
    event_types = [event["type"] for event in events]
    assert "status" in event_types
    assert "lead" in event_types
    assert event_types[-1] == "done"

    export = client.get(f"/api/search/{search_id}/export")
    assert export.status_code == 200
    assert export.headers["content-disposition"] == 'attachment; filename="podpipe-leads.csv"'

    rows = list(csv.DictReader(StringIO(export.text)))
    assert rows
    assert {"name", "twitter_handle", "match_score", "outreach_dm"}.issubset(rows[0].keys())
    assert all(int(row["match_score"]) >= 60 for row in rows)
