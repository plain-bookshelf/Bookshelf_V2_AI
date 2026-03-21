from sqlmodel import Session, select, case, Float, cast, func, desc, or_
from app.v1.common.models.books import Book


class Search:

    @staticmethod
    def fts_search(keywords: str):
        tsq = func.websearch_to_tsquery("simple", keywords)

        fts_rank_raw = func.ts_rank_cd(Book.similarity_token, tsq)
        fts_score = case(
            (Book.similarity_token.op("@@")(tsq), fts_rank_raw),
            else_=0.0
        ).label("fts_score")
        return fts_score


    @staticmethod
    def trgm_search(keywords: str):
        title_ns = func.replace(Book.title, " ", "")
        q_ns = func.replace(keywords, " ", "")

        trgm_raw = func.greatest(
            func.similarity(Book.title, keywords),
            func.similarity(title_ns, q_ns),
        )
        trgm_score = cast(trgm_raw, Float).label("trgm_score")
        return trgm_score


    def fts_trgm_search(self, session: Session, q: str, limit: int):
        q = (q or "").strip()
        if not q:
            return []

        tsq = func.websearch_to_tsquery("simple", q)
        fts_score = self.fts_search(q)
        trgm_score = self.trgm_search(q)
        score = fts_score + trgm_score

        stmt = (
            select(Book, score)
            .where(
                or_(
                    Book.search_tsv.op("@@")(tsq),
                    trgm_score >= 0,
                    Book.title.ilike(f"%{q}%")
                )
            )
            .order_by(desc(score))
            .limit(limit)
        )
        return session.exec(stmt).all()


search_class = Search()


# from db.session import engine
# with Session(engine) as session:
#     rows = fts_trgm_search(session, "동물", limit=50)
#     i = 0
#     for book, scores in rows:
#         i += 1
#         print(i, book.id, scores, book.titles, book.authors)
