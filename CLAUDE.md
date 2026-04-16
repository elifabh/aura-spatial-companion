# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What is Aura

Aura is a local-first AI wellness companion that analyzes living spaces for health risks and provides personalized recommendations. It runs entirely on-device using Ollama (no cloud LLM calls) and integrates camera/compass input from mobile browsers. It targets people with diverse needs (elderly, disability, ADHD, children, etc.) using 15+ user archetypes.

## Development Commands

### Prerequisites
- Python 3.11+
- [Ollama](https://ollama.com) running locally with Gemma 4 E4B: `ollama pull gemma4:e4b`

### Setup
```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

### Running the Server
```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```
Frontend is served statically at `http://localhost:8000` (PWA).

### Testing
```bash
pytest tests/ -v                   # All tests
pytest tests/test_aura.py -v       # Core intelligence only
pytest tests/test_api.py -v        # API endpoints only
pytest tests/test_aura.py::TestGraphRAG -v  # Single test class
```

## Architecture

### Request Lifecycle
1. PWA frontend (`frontend/`) → HTTP/SSE → FastAPI (`backend/main.py`)
2. Routes in `backend/api/routes/` delegate to core modules
3. Core modules (`backend/core/`) compose LLM + RAG + group rules
4. Responses enriched by SQLite (history), ChromaDB (semantic search), and NetworkX graph (relationship traversal)

### Intelligence Pipeline (`backend/core/`)

**`llm.py`** — Ollama/Gemma 4 E4B client. Generates chat responses and structured JSON recommendations. System prompts are composed dynamically from mood, group, and seasonal context. Temperature is fixed at 0.3 for consistency.

**`vision.py`** — Spatial analysis via LLaVA. Runs a 4-step chain-of-thought: scene description → resident inference → risk identification → improvement suggestions. Returns a structured dict with 5-dimension scores. Images are embedded into ChromaDB for multimodal memory.

**`group_rules.py`** — The user archetype system. Detects groups from profiles (e.g., `child_baby`, `disability_motor`, `night_shift_worker`) and injects group-specific rules into system prompts. This is the primary mechanism for personalizing responses — edit here to change how Aura handles specific populations.

**`mood_activities.py`** — Maps 5 mood states (energetic, calm, tired, stressed, creative) to activities and adjusts conversational style. Works together with group rules in prompt composition.

**`rag.py`** — ChromaDB semantic search over 6 ingested PDF knowledge documents (WELL Standard, WHO Housing, Universal Design, etc.). Queries are enriched with user profile context before retrieval. Also calls into graph RAG for relationship traversal.

**`safety.py`** — Content filter and hallucination guard. All LLM outputs pass through this before returning to the client.

**`timeseries.py`** — ROCKET (RandOm Convolutional Kernels Transform) classifier for environmental pattern recognition from multivariate sensor data. Model persisted at `data/rocket_model.pkl`.

### Data Layer (`backend/db/`)

**`sqlite.py`** — Tables: `user_profiles`, `conversations`, `environmental_logs`, `space_analyses`, `moods`. WAL mode. All persistence except vectors and graph goes here.

**`chroma.py`** — ChromaDB persistent at `data/chroma/`. Primary collection: `aura_knowledge` (PDF embeddings). Also stores vision analysis embeddings for room memory over time.

**`graph.py`** — NetworkX DiGraph with 40+ concept nodes and 50+ edges. Node types: condition, demographic, factor, risk, solution, standard. Enables traversal like: `ADHD → sensory_overload → quiet_zone → low_distraction_space`. Graph is seeded in code and serialized to `data/knowledge_graph.json` on startup.

### Startup Sequence (`backend/main.py` lifespan)
1. `init_db()` — create SQLite tables
2. `ingest_documents()` — load PDFs into ChromaDB (skips if already populated)
3. `seed_all()` — create demo profiles (Sarah, Michael, Emma) if not present
4. `save_graph()` — serialize NetworkX graph to JSON
5. `warmup_model()` — send dummy prompt to pre-load Gemma 4 into GPU memory

### API Routes (`backend/api/routes/`)
| Route | Purpose |
|-------|---------|
| `chat.py` | `/api/chat/send` (standard) and `/api/chat/stream` (SSE word-by-word) |
| `camera.py` | `/api/camera/analyse` — accepts image + optional compass/GPS |
| `profile.py` | CRUD for user profiles + mood logging |
| `video.py` | `/api/video/upload` — OpenCV multi-frame extraction |
| `recommendations.py` | Profile-aware personalized recommendations |
| `weather.py` | Met Éireann API (Irish weather, no auth needed) |
| `outdoor.py` | OSM Nominatim nearby accessible public spaces |
| `evaluate.py` | Model self-evaluation metrics |

### Frontend (`frontend/`)
Vanilla JS PWA — no framework, no bundler. `index.html` (30KB) contains 8 screens swapped via DOM manipulation in `app.js` (43KB). Screen names: Home, Scan, Chat, Profile, Tips, Weather, Outdoor, Settings.

**`js/api.js`** — all backend calls go through this fetch wrapper.  
**`js/camera.js`** — `getUserMedia()` → canvas capture → base64 JPEG → `/api/camera/analyse`.  
**`js/chat.js`** — SSE client that reads word tokens and appends them; listens for `[DONE]` sentinel.  
**`js/orientation.js`** — `DeviceOrientationEvent` compass heading fed into camera analysis requests.

### External Services (`backend/services/`)
- **`weather.py`** — Met Éireann (Ireland-specific, free, unauthenticated)
- **`sun.py`** — pvlib solar position from GPS + compass heading → Vitamin D windows, golden hour
- **`location.py`** — OSM Nominatim reverse geocoding + accessibility-filtered POI search
- **`profile.py`** — thin wrapper over SQLite profile CRUD

## Key Configuration (`backend/config.py` and `.env`)

```
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llava         # or gemma4:e4b
AURA_HOST=0.0.0.0
AURA_PORT=8000
AURA_DEBUG=true
```

All runtime data is local:
- `data/aura.db` — SQLite
- `data/chroma/` — ChromaDB vectors
- `data/knowledge_graph.json` — serialized graph
- `data/rocket_model.pkl` — trained ROCKET classifier

## Extending the System

**New user archetype:** Add detection logic and rules to `backend/core/group_rules.py`.

**New knowledge document:** Drop a PDF into `backend/knowledge/` and add its path to the ingestion call in `backend/main.py`. ChromaDB will chunk and embed it on next startup.

**New API endpoint:** Create a route file in `backend/api/routes/`, register it with `app.include_router()` in `backend/main.py`.

**Changing the LLM model:** Update `OLLAMA_MODEL` in `.env` and ensure the model is pulled via `ollama pull <model>`.
