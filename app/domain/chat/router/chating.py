from fastapi import APIRouter, HTTPException
from sqlmodel import select
from app.common.dependencies import SessionDep
from app.domain.chat.models import ChatAiSession, ChatAiMessage, ChatAiImage, MessageRole
from app.common.models.user import Member
from app.domain.chat.schemas import Chat
from app.domain.chat.services.llm.generator import bookshelf_llm_service

chat_router = APIRouter()


# class ChatAiMessage(SQLModel):
#     __tablename__ = "chat_ai_message"
#
#     id: Optional[int] = Field(default=None, primary_key=True)
#     session_id: int = Field(foreign_key="chat_ai_session.id", nullable=False, index=True)
#     content: str = Field(max_length=10000, nullable=False)
#     token_usage: int = Field(nullable=False)
#     role: MessageRole = Field(nullable=False)
#     create_at: datetime = Field(default_factory=datetime.now, nullable=False)
#
#     session: Optional[ChatAiSession] = Relationship(back_populates="messages")
#     images: list["ChatAiImage"] = Relationship(back_populates="message")
#
#
# class ChatAiImage(SQLModel):
#     __tablename__ = "chat_ai_image"
#
#     id: Optional[int] = Field(default=None, primary_key=True)
#     message_id: int = Field(foreign_key="chat_ai_message.id", nullable=False, index=True)
#     image_url: str = Field(max_length=1000, nullable=False)
#     created_at: datetime = Field(default_factory=datetime.now, nullable=False)
#
#     message: Optional[ChatAiMessage] = Relationship(back_populates="images")



@chat_router.post("/chat")
async def chatbot(session: SessionDep, chat: Chat):
    result = session.get(Member, chat.member_id)
    if not result:
        raise HTTPException(status_code=404, detail="no user")
    con_stmt = select(ChatAiSession).where(ChatAiSession.id == chat.member_id).where(ChatAiSession.member_id == result.id)
    con_result = session.exec(con_stmt).first()
    if not con_result:
        raise HTTPException(status_code=404, detail="no session")

    answer = bookshelf_llm_service.bookshelf_model(session, chat.member_id, chat.question, 15, 6)
    session.add(ChatAiMessage(session_id=chat.session_id, role=MessageRole.USER ,content=chat.question))
    try:
        session.add(ChatAiMessage(session_id=chat.session_id, role=MessageRole.ASSISTANT, content=answer.get("answer", "")))

    except AttributeError as e:
        print(e)
        session.add(ChatAiMessage(session_id=chat.session_id, role=MessageRole.ASSISTANT, content="뭐 오류가 일어났다 그런거"))
    session.commit()
    return answer