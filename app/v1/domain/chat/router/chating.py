from fastapi import APIRouter
from app.v1.common.dependencies import SessionDep
from app.v1.domain.chat.schemas import Chat
from app.v1.domain.chat.services.chat_service.chat import process_chat
from app.v1.common.error.exception import MemberNotFoundException, SessionNotFoundException

from sqlmodel import select
import random
from app.v1.common.models.user import Member
from app.v1.domain.chat.models import ChatAiSession

chat_router = APIRouter()

@chat_router.post("/chat")
async def chatbot(session: SessionDep, chat: Chat):
    user = session.exec(select(Member).where(Member.username == chat.username)).first()
    if not user:
        raise MemberNotFoundException(username=chat.username)

    chat_session = session.exec(select(ChatAiSession).where(ChatAiSession.id == chat.session_id))
    if not chat_session:
        raise SessionNotFoundException(session_id=chat.session_id)

    answer, message_id = process_chat(session, chat)
    return {"agent": answer, "message_id": message_id}




@chat_router.post("/chat/session/{username}", response_model=ChatAiSession)
def create_chat_session(session: SessionDep, username: str):
    user = session.exec(select(Member).where(Member.username == username)).first()
    if not user:
        raise MemberNotFoundException(username=username)

    random_title = f"새로운 대화_{random.randint(1000, 9999)}"

    new_session = ChatAiSession(
        member_id=user.id,
        title=random_title
    )

    session.add(new_session)
    session.commit()
    session.refresh(new_session)

    return new_session