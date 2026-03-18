from app.config import settings
from openai import OpenAI
from app.domain.chat.services.llm.rag.ranking.rank import ranking_class
from sqlmodel import Session
import json


class RerankService:

    def __init__(self):
        self.client = OpenAI(
            base_url=settings.BASE_URL,
            api_key=settings.SMALL_API_KEY,
        )


    @staticmethod
    def _ranking_instructions(top_k: int):
        instructions = (
            "너는 RAG 리랭커다. query와 chunks를 보고 질문에 가장 도움이 되는 청크들을 고른다.\n"
            f"출력은 반드시 JSON 배열로만 출력해라. 길이는 정확히 {top_k}.\n"
            "배열 원소는 chunk id 문자열이다.\n"
            "입력으로 주어진 id 중에서만 선택하고, 중복 없이 뽑아라.\n"
            "같은 책이 있다면 반드시 하나만 선택해라."
            "그 외 어떤 설명/텍스트도 출력하지 마라."
        )
        return instructions


    def _ranking_model_response(self, top_k: int, ask_str: str, chunk: list[str]):
        resp = self.client.responses.create(
            model=settings.MODEL_2,
            instructions=self._ranking_instructions(top_k),
            input=f"query:\n{ask_str}\n\nchunks:\n{chunk}",
        )
        return resp


    def ranking_model_answer(self, session: Session, ask_str: str, ask_em: list[float], keywords: str, limit: int, top_k: int):
        chunk = ranking_class.get_ranked_chunk(session, ask_em, keywords, limit)
        response = self._ranking_model_response(top_k, ask_str, chunk)

        resp_list = json.loads(response.output_text)
        ids_int = [int(x) for x in resp_list]
        return ids_int


rerank_service = RerankService()