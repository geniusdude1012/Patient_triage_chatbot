from pydantic import BaseModel

class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"
    username:   str = ""

class ChatResponse(BaseModel):
    response: str
    priority: str        
    department: str | None = None
    session_id: str