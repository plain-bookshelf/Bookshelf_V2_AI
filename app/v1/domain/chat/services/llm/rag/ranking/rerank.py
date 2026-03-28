from app.v1.common.models.book_tables import BookAffiliation, BookGenre, Book
from app.v1.domain.chat.services.llm.rag.ranking.rank_model import rerank_service
from sqlmodel import Session, select
from sqlalchemy.orm import joinedload, selectinload


def get_reranked_chunk(session: Session, ask_str: str, ask_em: list[float], keywords: str, limit: int, top_k: int):
    top_k_ids = rerank_service.ranking_model_answer(session, ask_str, ask_em, keywords, limit, top_k)

    stmt = (
        select(BookAffiliation)
        .where(BookAffiliation.id.in_(top_k_ids))
        .options(
            joinedload(BookAffiliation.book)
            .selectinload(Book.genre_links)
            .joinedload(BookGenre.genre),
            joinedload(BookAffiliation.affiliation),
            selectinload(BookAffiliation.details),
        )
    )
    results = session.exec(stmt).unique().all()

    ba_map = {r.id: r for r in results}

    books_to_give = ""
    for ba_id in top_k_ids:
        ba = ba_map.get(ba_id)

        category = ", ".join(gl.genre.genre_name for gl in ba.book.genre_links) or "없음"
        reg_numbers = ", ".join(d.registration_number for d in ba.details) or "없음"
        call_numbers = ", ".join(d.call_number for d in ba.details) or "없음"

        books_to_give += f"""
                [책 아이디] {ba.book.id}
                [제목] {ba.book.title}
                [작가] {ba.book.author}
                [출판사] {ba.book.publisher}
                [카테고리] {category}
                [책소개] {ba.book.introduction}
                [학교] {ba.affiliation.affiliation_name}
                [등록번호] {reg_numbers}
                [청구기호] {call_numbers}
                [출판일] {ba.book.publication_date}
                """

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