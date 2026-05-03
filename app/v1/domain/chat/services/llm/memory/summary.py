from sqlmodel import select, Session
from app.v1.config import settings
from app.v1.domain.chat.models import ChatAiMessage
from app.v1.domain.chat.services.llm.rag.metadata.query_models import query_router


def memory_summary(session: Session, session_id: int):
    summerize = ""
    stmt = (select(ChatAiMessage)
            .where(ChatAiMessage.session_id == session_id)
            .order_by(ChatAiMessage.created_at))
    result = session.exec(stmt).all()
    if len(result) > 12:
        for message in result[:-12]: # 12
            role = message.role
            content = message.content
            summerize += f"{role}: {content}\n"

        prompt = "너는 대화 내용 압축기다. 주어진 대화 내용을 보고 중요 내용을 간단히 요약해라."
        answer = query_router.get_response(summerize, prompt, settings.MODEL_3)

        return answer
    else:
        return "none"