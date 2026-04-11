from sqlmodel import select, Session
from app.v1.domain.chat.models import ChatAiMessage


def get_messages(session: Session, session_id):
    recent_chat = ""
    stmt = (select(ChatAiMessage)
            .where(ChatAiMessage.session_id == session_id)
            .order_by(ChatAiMessage.create_at))
    result = session.exec(stmt).all()
    if result:
        for message in result[-12:]:
            role = message.role
            content = message.content
            recent_chat += f"{role}: {content}\n"
        return recent_chat
    else:
        return "none"