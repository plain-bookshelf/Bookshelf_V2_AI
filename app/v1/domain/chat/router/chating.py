from fastapi import APIRouter
from app.v1.common.dependencies import SessionDep
from app.v1.domain.chat.schemas import Chat, ChatAnswer, ChatSession
from app.v1.domain.chat.services.chat_service.chat import process_chat, make_chat_session
from app.v1.domain.chat.services.chat_service.get_infos import get_session, get_member

chat_router = APIRouter()

@chat_router.post("/chat")
async def chatbot(session: SessionDep, chat: Chat):
    user = get_member(session, chat.username)
    chat_session = get_session(session, chat.session_id, user.id)

    answer, message_id = process_chat(session, chat)
    return ChatAnswer(agent=answer, message_id=message_id)



@chat_router.post("/chat/session/{username}", response_model=ChatSession)
def create_chat_session(session: SessionDep, username: str):
    new_session = make_chat_session(session, username)
    return new_session