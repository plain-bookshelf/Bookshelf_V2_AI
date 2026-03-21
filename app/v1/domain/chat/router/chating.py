from fastapi import APIRouter
from app.v1.common.dependencies import SessionDep
from app.v1.domain.chat.schemas import Chat
from app.v1.domain.chat.services.chat_service.chat import process_chat

chat_router = APIRouter()

@chat_router.post("/chat")
async def chatbot(session: SessionDep, chat: Chat):
    answer, message_id = process_chat(session, chat)
    return {"agent": answer, "message_id": message_id}