from app.local_test_version.core.config import settings
from openai import OpenAI

client = OpenAI(
    base_url=settings.BASE_URL,
    api_key=settings.SMALL_API_KEY
)

class KeywordModel:
    def __init__(self):
        self.client = OpenAI(
            base_url=settings.BASE_URL,
            api_key=settings.SMALL_API_KEY
        )


    @staticmethod
    def _keyword_instructions():
        instructions = (
            "너는 사용자 질문에 키워드를 뽑는 기계다.\n"
            "책의 제목이 있다면 그것도 키워드다\n"
            "출력은 반드시 단어 혹은 쉽표를 이용해 '키워드' 처럼 출력한다.\n"
            "반드시 해당 질문에 대한 키워드만 출력해라."
            "반드시 단어여야 한다.\n"
            "그 외 어떤 설명/텍스트도 출력하지 마라.\n"
            "--------------------------------\n"
            "출력 예시n\n"
            "사용자 질문: 1984 같은 책 추천해줘\n"
            "1984, 디스토피아"
        )
        return instructions


    def get_response(self, user_query: str):
        instructions = self._keyword_instructions()

        resp = self.client.responses.create(
            model=settings.MODEL_3,
            instructions=instructions,
            input=f"query:\n{user_query}",
        )
        answer = resp.output_text
        return answer


keyword_maker = KeywordModel()