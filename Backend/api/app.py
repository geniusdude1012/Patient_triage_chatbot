"""
Backend/api/app.py
────────────────────
FastAPI application setup.
Registers all routers and middleware.
Start with: uvicorn Backend.api.app:app --reload
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from Backend.api.routes.chat    import router as chat_router
from Backend.api.routes.session import router as session_router

app = FastAPI(title="Patient Triage Chatbot API")

# ── CORS — allows Streamlit (port 8501) to call FastAPI (port 8000) ───────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # tighten to ["http://localhost:8501"] in production
    allow_methods=["*"],
    allow_headers=["*"]
)

# ── Routers ────────────────────────────────────────────────────────────────────
app.include_router(chat_router,    prefix="/api")   # /api/chat, /api/clear
app.include_router(session_router, prefix="/api")   # /api/session/start, /api/session/end


@app.get("/")
async def root():
    return {"status": "Patient Triage API running"}