from fastapi import APIRouter
from shared.schemas.chat_schema import ChatRequest, CopilotResponse
from server.src.controllers.chat_controller import handle_chat_request

router = APIRouter(prefix="/api", tags=["Chat & Intelligence"])

@router.post("/chat", response_model=CopilotResponse)
def chat_endpoint(req: ChatRequest):
    return handle_chat_request(req)
