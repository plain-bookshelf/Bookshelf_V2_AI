from sqlmodel import Session, select
from app.v1.common.error.exception import MemberNotFoundException, SessionNotFoundException
from app.v1.domain.chat.models import ChatAiSession, Member


def get_member(session: Session, username: str) -> Member:
    member = session.exec(select(Member).where(Member.username == username)).first()
    if not member:
        raise MemberNotFoundException(username)
    return member


def get_session(session: Session, session_id: int, member_id: int) -> ChatAiSession:
    stmt = select(ChatAiSession).where(
        ChatAiSession.id == session_id,
        ChatAiSession.member_id == member_id,
    )
    result = session.exec(stmt).first()
    if not result:
        raise SessionNotFoundException(session_id)
    return result