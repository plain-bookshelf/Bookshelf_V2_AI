from app.common.models.books import Book
from app.common.models.books import BookDetail
from app.domain.chat.services.llm.rag.ranking.rank_model import rerank_service
from sqlmodel import Session, select


def get_reranked_chunk(session: Session, ask_str: str, ask_em: list[float], keywords: str, limit: int, top_k: int):
    top_k_ids = rerank_service.ranking_model_answer(session, ask_str, ask_em, keywords, limit, top_k)

    books_to_give = ""
    for i in top_k_ids:
        stmt = select(Book).where(Book.id == i)
        result = session.exec(stmt).first()

        temp = f"""
            [책 아이디] {result.id}
            [책 아이디] {result.id}
            [제목] {result.title}
            [작가] {result.authors}
            [출판사] {result.publisher}
            # [카테고리] {result.genres}
            [책소개] {result.introduction}
            # [학교] {result.school}
            # [등록번호] {result.id_number}
            # [청구기호] {result.call_num}
            [출판일] {result.publication_date}
            """
        books_to_give += temp

    return books_to_give

# from db.session import engine
# with Session(engine) as session:
#     text = "c언어 관련 책 추천해줘"
#     metadata = "c언어"
#     # text = "1984랑 비슷한 책 추천해줘"
#     # metadata = "디스토피아"
#     from FlagEmbedding import BGEM3FlagModel
#     m3 = BGEM3FlagModel("BAAI/bge-m3")
#     out = m3.encode(text, batch_size=12, max_length=4096)
#     dense = out['dense_vecs']
#
#     a = get_reranked_chunk(session, text, dense, metadata, 15, 6)
#     print(a)