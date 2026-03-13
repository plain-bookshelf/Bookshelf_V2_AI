from sqlmodel import select, Session
from openai import OpenAI
from core.config import settings
from db.schemas import Message

client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=settings.SMALL_API_KEY
)

def memory_summary(session: Session, con_id: int):
    summerize = ""
    stmt = select(Message).where(Message.conversation_id == con_id)
    result = session.exec(stmt).all()
    if len(result) > 12:
        for message in result[12:]:
            role = message.role
            content = message.content
            summerize += f"{role}: {content}\n"

        instructions = "너는 대화 내용 압축기다. 주어진 대화 내용을 보고 중요 내용을 간단히 요약해라."

        resp = client.responses.create(
            model=settings.MODEL_3,
            instructions=instructions,
            input=f"query:\n{summerize}",
        )
        answer = resp.output_text
        return answer
    else:
        return "none"