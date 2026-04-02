"""
Aura — AI-Powered Spatial Companion
FastAPI entry point.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.api.routes import chat, camera, profile, recommendations, weather
from backend.config import DEBUG
from backend.db.sqlite import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle."""
    # ── Startup ───────────────────────────────────
    init_db()
    print("✦  Aura is awake.")
    yield
    # ── Shutdown ──────────────────────────────────
    print("✦  Aura is resting.")


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

# ── Serve PWA Frontend ───────────────────────────────
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "service": "aura"}
