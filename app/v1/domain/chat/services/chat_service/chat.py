from sqlmodel import Session
from app.v1.domain.chat.schemas import Chat
from app.v1.domain.chat.models import ChatAiMessage, MessageRole
from app.v1.domain.chat.services.chat_service.get_infos import get_member, get_session
from app.v1.domain.chat.services.llm.generator import bookshelf_llm_service


def process_chat(session: Session, chat: Chat) -> (dict, int):
    member = get_member(session, chat.member_id)
    chat_session = get_session(session, chat.session_id, member.id)

    answer, token = bookshelf_llm_service.bookshelf_model(
        session, chat.session_id, chat.question, 15, 6
    )

    message_id = _save_messages(session, chat, answer, token)
    return answer, message_id


def _save_messages(session: Session, chat: Chat, answer: dict, token: int):
    session.add(ChatAiMessage(
        session_id=chat.session_id,
        role=MessageRole.USER,
        content=chat.question,
        token_usage=token,
    ))

    assistant_msg = ChatAiMessage(
        session_id=chat.session_id,
        role=MessageRole.ASSISTANT,
        content=answer.get("answer", "오류가 발생했습니다."),
        token_usage=token,
    )
    session.add(assistant_msg)
    session.flush()
    session.commit()

    return assistant_msg.id