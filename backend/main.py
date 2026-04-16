"""
Aura — AI-Powered Spatial Companion
FastAPI entry point.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.api.routes import chat, camera, profile, recommendations, weather, evaluate, video, outdoor, gamification
from backend.config import DEBUG
from backend.db.sqlite import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle."""
    # ── Startup ───────────────────────────────────
    init_db()

    # Document ingestion (skip if already done)
    try:
        from backend.core.ingest import ingest_documents
        ingest_documents()
    except Exception as e:
        print(f"[Aura] Document ingestion skipped: {e}")

    # Seed demo data (skip if profiles already exist)
    try:
        from backend.services.profile import get_user_profile
        if not get_user_profile("sarah"):
            from backend.seed_demo import seed_all
            seed_all()
        else:
            print("[Aura] Demo profiles already exist. Skipping full seed.")
            # Migration: seed zone demo data if not yet present
            try:
                from backend.db.sqlite import get_zone_analyses
                if not get_zone_analyses("sarah", limit=1):
                    from backend.seed_demo import seed_demo_zones
                    seed_demo_zones()
            except Exception as e:
                print(f"[Aura] Zone migration skipped: {e}")
    except Exception as e:
        print(f"[Aura] Demo seeding skipped: {e}")

    # Save knowledge graph
    try:
        from backend.db.graph import save_graph
        save_graph()
    except Exception as e:
        print(f"[Aura] Graph save skipped: {e}")

    # Warm up the LLM model (pre-load into GPU for faster first response)
    try:
        from backend.core.warmup import warmup_model
        await warmup_model()
    except Exception as e:
        print(f"[Aura] Model warmup skipped: {e}")

    print("[Aura] Awake.")
    yield
    # ── Shutdown ──────────────────────────────────
    print("[Aura] Resting.")


app = FastAPI(
    title="Aura",
    description="AI-powered spatial companion — live better with what you have.",
    version="0.1.0",
    lifespan=lifespan,
)

# ── CORS (allow local PWA frontend) ──────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── API Routes ───────────────────────────────────────
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
app.include_router(camera.router, prefix="/api/camera", tags=["Camera"])
app.include_router(profile.router, prefix="/api/profile", tags=["Profile"])
app.include_router(recommendations.router, prefix="/api/recommendations", tags=["Recommendations"])
app.include_router(weather.router, prefix="/api/weather", tags=["Weather"])
app.include_router(evaluate.router, prefix="/api/evaluate", tags=["Evaluation"])
app.include_router(video.router, prefix="/api/video", tags=["Video"])
app.include_router(outdoor.router, prefix="/api/outdoor", tags=["Outdoor"])
app.include_router(gamification.router, prefix="/api/gamification", tags=["Gamification"])

# ── Health check (must be registered before the catch-all static mount) ──────
@app.get("/api/health")
async def health_check():
    return {"status": "ok", "service": "aura"}


# ── Serve PWA Frontend (catch-all — keep last) ───────────────────────────────
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
