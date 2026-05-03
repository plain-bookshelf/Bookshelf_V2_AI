import re
import json
from sqlmodel import Session
import google.generativeai as genai
from app.v1.config import settings
from app.v1.common.error.exception import LLMServiceException
from app.v1.domain.chat.services.llm.memory.bookdata import get_book_datas
from app.v1.domain.chat.services.llm.rag.ranking.rerank import get_reranked_chunk
from app.v1.domain.chat.services.llm.rag.metadata.query_models import query_router
from app.v1.domain.chat.services.llm.rag.metadata.q_embedding import query_embedding
from app.v1.domain.chat.services.llm.rag.metadata.set_prompt import prompts

genai.configure(api_key=settings.BIG_API_KEY)


class BookshelfLLMService:
    def __init__(self, model_name: str = "gemini-2.5-flash"):
        self.model_name = model_name


    @staticmethod
    def _build_bookshelf_context(
            session: Session,
            user_q: str,
            limit: int,
            top_k: int,
            con_id: int,
    ) -> str:

        book_data = get_book_datas(session, con_id)
        rewrite_prompt = prompts.rewrite_query(session, con_id, book_data)
        rewritten_q = query_router.get_response(user_q, rewrite_prompt, model=settings.MODEL_2)

        keyword_prompt = prompts.keyword_prompt()
        keywords = query_router.get_response(rewritten_q, keyword_prompt, model=settings.MODEL_3)
        q_embedding = query_embedding(rewritten_q)

        chunks = get_reranked_chunk(
            session,
            rewritten_q,
            q_embedding,
            keywords,
            limit,
            top_k,
            con_id
        )
        return chunks


    @staticmethod
    def _parse_llm_json(text: str) -> dict:
        text = text.strip()

        text = re.sub(r"^```json\s*", "", text)
        text = re.sub(r"^```\s*", "", text)
        text = re.sub(r"\s*```$", "", text)

        return json.loads(text)


    def bookshelf_model(self, session: Session, con_id, user_q: str, limit: int, top_k: int)-> (dict, int):
        if_rag = query_router.sim_response(user_q, prompts.sim_query_prompt(session, con_id))
        if if_rag:
            chunks = self._build_bookshelf_context(session, user_q, limit, top_k, con_id)
        else:
            chunks = '이전 정보들을 참고하세요'

        prompt = prompts.book_prompt(session, chunks, con_id)
        model = genai.GenerativeModel(
            self.model_name,
            system_instruction=prompt,
        )
        response = model.generate_content(user_q)
        total_token = response.usage_metadata.total_token_count

        try:
            result = self._parse_llm_json(response.text)
            return result, total_token
        except json.JSONDecodeError:
            raise LLMServiceException()


bookshelf_llm_service = BookshelfLLMService()