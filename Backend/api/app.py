

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from Backend.api.routes.chat    import router as chat_router
from Backend.api.routes.session import router as session_router
from Backend.api.routes.hmis    import router as hmis_router 

app = FastAPI(title="Patient Triage Chatbot API")

# ── CORS — allows Streamlit (port 8501) to call FastAPI (port 8000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   
    allow_methods=["*"],
    allow_headers=["*"]
)

#  Routers 
app.include_router(chat_router,    prefix="/api")  
app.include_router(session_router, prefix="/api")   
app.include_router(hmis_router,    prefix="/api")   

@app.get("/")
async def root():
    return {"status": "Patient Triage API running"}