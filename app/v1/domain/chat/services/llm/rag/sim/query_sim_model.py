from app.v1.config import settings
from sqlmodel import Session
from app.v1.domain.chat.services.llm.memory.store import get_messages
from openai import OpenAI

client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=settings.SMALL_API_KEY
)

def sim_model(session: Session, user_q: str, con_id: int):
    recent_chat = get_messages(session, con_id)

    instructions = (
        "너는 RAG 사용 판별 기계다.\n"
        "만약 사용자의 질문이 새로운 책 등을 추천 받거나 검색하고 싶은 등 새로 데이터를 검색해야 하는 경우 'True'를 반환하라\n"
        "그 외 전의 정보를 암시하는 등의 질문 등 필요 없는 경우 'False'를 반환하라\n"
        "반드시 'True' 혹은 'False'로 반환해라\n"
        "그 외 어떤 설명/텍스트도 출력하지 마라."
        f"이전 대화들: {recent_chat}"
    )

    resp = client.responses.create(
        model=settings.MODEL_3,
        instructions=instructions,
        input=f"query:\n{user_q}",
    )
    answer = resp.output_text
    if answer == 'True':
        return True
    else:
        return False
#
# print(sim_model("저 책들 중에 특히 더 추천할만한 책 없어? 그리고 내 이름 기억해?"))