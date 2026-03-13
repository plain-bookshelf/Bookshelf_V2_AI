from sqlmodel import select, Session
from db.schemas import Message

def get_messages(session: Session, con_id):
    recent_chat = ""
    stmt = select(Message).where(Message.conversation_id == con_id)
    result = session.exec(stmt).all()
    if result:
        for message in result[-12:]:
            role = message.role
            content = message.content
            recent_chat += f"{role}: {content}\n"
        return recent_chat
    else:
        return "none"