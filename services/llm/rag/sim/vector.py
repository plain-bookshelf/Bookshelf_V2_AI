from db.session import engine
from db.schemas import BookVector, Books
from FlagEmbedding import BGEM3FlagModel
from sqlmodel import select, Session, asc, cast, Float, func

# def embedding_sim(session: Session, ask_em: list[float], limit: int):
#     distances = cast(BookVector.embedding.op("<=>")(ask_em), Float).label("distance")
#     result = (
#         select(
#             Books.titles, BookVector.Books_id, distances)
#             .join(BookVector, BookVector.Books_id == Books.id)
#             .order_by(asc(distances)).limit(limit)
#     )
#     return session.exec(result).all()

# 중복 제거 (토큰 절약 용)
def embedding_sim(session: Session, ask_em: list[float], limit: int):
    distance_expr = cast(BookVector.embedding.op("<=>")(ask_em), Float)

    result = (
        select(
            func.min(Books.titles).label("titles"),
            func.min(BookVector.Books_id).label("Books_id"),
            distance_expr.label("distance")
        )
        .join(BookVector, BookVector.Books_id == Books.id)
        .group_by(distance_expr)
        .order_by(asc("distance"))
        .limit(limit)
    )

    return session.exec(result).all()

# text = """sf소설 추천해줘"""
# m3 = BGEM3FlagModel("BAAI/bge-m3")
# out = m3.encode(text, batch_size=12, max_length=4096)
# dense = out['dense_vecs']
#
# with Session(engine) as session:
#     rows = embedding_sim(session, dense, limit=15)
#     print(rows)
#     for t, n, d in rows:
#         print(n,d,t)