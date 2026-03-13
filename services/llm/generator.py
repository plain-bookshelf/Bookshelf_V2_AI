from core.config import settings
from services.llm.rag.ranking.rerank import get_reranked_chunk
from services.llm.rag.metadata.keywords import keyword_maker
from services.llm.rag.metadata.q_embedding import query_embedding
from services.llm.rag.metadata.set_prompt import book_prompt
from sqlmodel import Session
import google.generativeai as genai

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
    ):
        keywords = keyword_maker.get_response(user_q)
        q_embedding = query_embedding(user_q)
        chunks = get_reranked_chunk(
            session,
            user_q,
            q_embedding,
            keywords,
            limit,
            top_k,
        )
        return chunks


    def bookshelf_model(self, session: Session, con_id, user_q: str, limit: int, top_k: int):
        chunks = self._build_bookshelf_context(session, user_q, limit, top_k)
        prompt = book_prompt(session, user_q, chunks, con_id)
        model = genai.GenerativeModel(
            self.model_name,
            system_instruction=prompt,
        )
        response = model.generate_content(user_q)
        return response.text


bookshelf_llm_service = BookshelfLLMService()