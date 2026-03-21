from sqlmodel import Session
from app.v1.domain.chat.schemas import Chat
from app.v1.domain.chat.models import ChatAiSession, ChatAiImage, ChatAiMessage, MessageRole
from app.v1.domain.chat.services.chat_service.get_infos import get_member, get_session
from app.v1.domain.chat.services.llm.generator import bookshelf_llm_service


def process_chat(session: Session, chat: Chat) -> dict:
    member = get_member(session, chat.member_id)
    chat_session = get_session(session, chat.session_id, member.id)

    answer = bookshelf_llm_service.bookshelf_model(
        session, chat.member_id, chat.question, 15, 6
    )

    _save_messages(session, chat, answer)
    return answer


def _save_messages(session: Session, chat: Chat, answer: dict):
    session.add(ChatAiMessage(
        session_id=chat.session_id,
        role=MessageRole.USER,
        content=chat.question,
    ))

    assistant_msg = ChatAiMessage(
        session_id=chat.session_id,
        role=MessageRole.ASSISTANT,
        content=answer.get("answer", "오류가 발생했습니다."),
    )
    session.add(assistant_msg)
    session.commit()