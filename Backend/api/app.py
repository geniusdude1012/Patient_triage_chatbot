from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from Backend.api.routes.chat import router

app = FastAPI(title="Patient Triage Chatbot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in production
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(router, prefix="/api")