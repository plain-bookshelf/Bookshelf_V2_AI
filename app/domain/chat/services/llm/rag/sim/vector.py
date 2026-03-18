from app.common.models.books import BookSimilarity, Book
from sqlmodel import select, Session, cast, Float, func


def embedding_sim(session: Session, ask_em: list[float], limit: int):
    distance_expr = cast(BookSimilarity.vector_similarity.op("<=>")(ask_em), Float)

    book_data = (
        select(
            Book.title.label("titles"),
            Book.id.label("book_ids"),
            distance_expr.label("distances")
        )
        .join(BookSimilarity, BookSimilarity.book_id == Book.id)
        .subquery()
    )

    ranked = (
        select(
            book_data.c.titles,
            book_data.c.book_ids,
            book_data.c.distances,
            func.row_number().over(
                partition_by=book_data.c.titles,
                order_by=(book_data.c.distances, book_data.c.book_ids)
            ).label("rank")
        )
        .subquery()
    )

    result = (
        select(
            ranked.c.titles,
            ranked.c.book_ids,
            ranked.c.distances
        )
        .where(ranked.c.rank == 1)
        .order_by(ranked.c.distances)
        .limit(limit)
    )

    return session.exec(result).all()


# from db.session import engine
# from FlagEmbedding import BGEM3FlagModel
# text = """c언어"""
# m3 = BGEM3FlagModel("BAAI/bge-m3")
# out = m3.encode(text, batch_size=12, max_length=4096)
# dense = out['dense_vecs']
#
# with Session(engine) as session:
#     rows = embedding_sim(session, dense, limit=15)
#     print(rows)
#     for t, n, d in rows:
#         print(n,d,t)