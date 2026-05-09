# PodPipe API

FastAPI backend for Person B: handle suggestion, lead scoring, outreach generation, SSE streaming, and CSV export.

## Setup

```bash
cd podpipe-api
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

For the hackathon mock flow, leave `USE_MOCK_LLM=true` and `USE_MOCK_AGENT=auto`.
To call Claude and use Person A's real agent when `../agent` exists, set:

```bash
ANTHROPIC_API_KEY=...
USE_MOCK_LLM=false
USE_MOCK_AGENT=auto
```

`USE_MOCK_AGENT=auto` uses Person A's `agent.run_agent_async` when available, otherwise it falls back to local mock profiles. Set `USE_MOCK_AGENT=true` to force mock mode or `USE_MOCK_AGENT=false` to require the real agent.

## Run

```bash
uvicorn app.main:app --reload
```

Health check:

```bash
curl http://127.0.0.1:8000/health
```

Start a search:

```bash
curl -X POST http://127.0.0.1:8000/api/search \
  -H 'Content-Type: application/json' \
  -d '{"query":"YC founder who bootstrapped a dev tools company and tweets about PLG"}'
```

Stream events:

```bash
curl -N http://127.0.0.1:8000/api/search/{search_id}/stream
```

Export CSV:

```bash
curl -OJ http://127.0.0.1:8000/api/search/{search_id}/export
```

## Tests

```bash
pytest
```
