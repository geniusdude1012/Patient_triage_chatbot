from pydantic import BaseModel

class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"

class ChatResponse(BaseModel):
    response: str
    priority: str        # critical / urgent / routine / low
    department: str | None = None
    session_id: str