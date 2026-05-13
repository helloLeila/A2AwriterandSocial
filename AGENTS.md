# AGENTS.md

This file provides guidance to Codex (Codex.ai/code) when working with code in this repository.

## Project Overview

A2Aforzhihu is an Agent-to-Agent (A2A) social interaction assistant for Zhihu (知乎) content creation. The system simulates multi-round dialogue between a "User Agent" (representing the asker) and an "Answerer Agent" (representing the content creator) to align needs and generate a writer framework — without producing the final answer text.

## Tech Stack

- **Frontend**: Vite 5 + React 18 + TypeScript. Port 5173.
- **Backend**: FastAPI + Uvicorn + native WebSocket (`/ws/{session_id}`). Port 8000.
- **LLM**: Anthropic Codex API (`Codex-sonnet-4-6` via `anthropic` SDK).
- **Data source**: Zhihu API (`https://www.zhihu.com/ring/moltbook/api`).

## Development Commands

### Backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# Copy and fill in .env
cp .env.example .env
# Run dev server
python main.py
# Or: uvicorn backend.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev       # Vite dev server on :5173, proxies /api and /ws to :8000
npm run build     # tsc + vite build
```

### Environment Variables
Create `backend/.env` from `backend/.env.example`. The only required variable for local development is:
- `ANTHROPIC_API_KEY` — used by all agents via `AgentConfig` in `backend/agents/base.py`.

## Architecture

### 4-Step Orchestrated Pipeline (`SessionOrchestrator`)

The entire flow is driven through a single WebSocket connection per session. `main.py` handles the WS lifecycle and delegates to `SessionOrchestrator`.

| Step | Agent(s) | What happens | WS message types |
|------|----------|--------------|------------------|
| 1 | `CollectorAgent` + `FilterAgent` | Fetch Zhihu question, top answers, hot list; filter out AI-watermarked, ad, and overly-hardcore content | `phase_start`, `collector_status`, `filter_status` |
| 2 | `UserAgent` ↔ `AnswererAgent` | 3+ rounds of social dialogue; User Agent expresses real needs/ concerns, Answerer Agent proposes and adjusts writing direction | `phase_start`, `round_start`, `chat_message` (×2 per round), `round_end` |
| 3 | `UserAgent` (LLM call) | Extract consensus from dialogue history into `ConsensusBoard` | `phase_start`, `consensus_ready` |
| 4 | `UserAgent` (LLM call) | Generate `WriterFramework` (title suggestions, angles, structure outline, pitfall checklist, tone guidance) — **never full answer text** | `phase_start`, `framework_ready`, `completed` |

### Key Backend Files

- `backend/main.py` — FastAPI app, REST endpoints (`/api/session/*`), WebSocket endpoint (`/ws/{session_id}`), `ConnectionManager`.
- `backend/agents/orchestrator.py` — `SessionOrchestrator` owns all agents and the 4-step flow. Session state is stored in-memory (`self.sessions: dict[str, SessionState]`).
- `backend/agents/base.py` — `BaseAgent` with `call_llm()` wrapping `AsyncAnthropic.messages.create()`. `AgentConfig` reads `.env` via `pydantic-settings`.
- `backend/agents/collector.py` — `CollectorAgent` fetches Zhihu data via `httpx`. `api_base` defaults to the ring/moltbook API.
- `backend/agents/filter.py` — `FilterAgent` uses regex patterns to detect AI watermarks, ads, and hardcore academic content. Also scores quality by vote/comment counts.
- `backend/agents/user_agent.py` — `UserAgent` role-plays a real Zhihu asker:口语化, emotional, pushes back,补充需求 gradually across rounds.
- `backend/agents/answerer_agent.py` — `AnswererAgent` role-plays a seasoned Zhihu creator: asks clarifying questions, offers choices, never outputs full answers.
- `backend/models/schemas.py` — All Pydantic v2 models: `SessionState`, `CollectedData`, `FilteredData`, `ChatMessage`, `DialogueRound`, `ConsensusBoard`, `WriterFramework`.

### Frontend

- `frontend/vite.config.ts` proxies `/api` → `http://localhost:8000` and `/ws` → `ws://localhost:8000`.
- **Note**: The frontend currently only has `main.tsx` and `vite-env.d.ts`. `App.tsx` (imported by `main.tsx`) does not exist yet — this is a known gap.

### Important Design Rules

1. **Never generate full answer text** — Step 4 (`step4_generate_framework`) explicitly forbids producing complete publishable paragraphs. Only framework, structure, and guidance.
2. **Session state is in-memory only** — no database. Sessions are lost on server restart.
3. **WebSocket is the primary interaction channel** — the frontend connects to `/ws/{session_id}` after creating a session via `POST /api/session/start`. The first WS message from the client must include `question_title`.
4. **LLM JSON parsing** — `orchestrator.py` strips markdown code fences and parses JSON from LLM responses for `ConsensusBoard` and `WriterFramework`. Both have fallback defaults on parse failure.
5. **Agent prompts are the product** — the system prompts in `user_agent.py` and `answerer_agent.py` define the persona and conversational strategy. Changing them changes the entire user experience.

## Common Tasks

### Add a new agent
1. Subclass `BaseAgent` in `backend/agents/<name>.py`.
2. Implement `execute(self, context) -> dict`.
3. Register in `SessionOrchestrator.__init__` if it needs to be wired into the pipeline.

### Change the Codex model
Edit `model_name` in `backend/agents/base.py:AgentConfig` (default: `Codex-sonnet-4-6`).

### Add a REST endpoint
Add to `backend/main.py`. The orchestrator and session state are already instantiated at module level.

### Run the backend without the frontend
```bash
cd backend
source .venv/bin/activate
python -c "import uvicorn; uvicorn.run('backend.main:app', host='0.0.0.0', port=8000, reload=True)"
```
Or use any WebSocket client to connect to `ws://localhost:8000/ws/{session_id}` after creating a session via `POST /api/session/start`.
