from sqlmodel import Session, select, case, Float, cast, func, desc, or_
from app.local_test_version.db.schemas import Books

class Search:

    @staticmethod
    def fts_search(keywords: str):
        tsq = func.websearch_to_tsquery("simple", keywords)

        fts_rank_raw = func.ts_rank_cd(Books.search_tsv, tsq)
        fts_score = case(
            (Books.search_tsv.op("@@")(tsq), fts_rank_raw),
            else_=0.0
        ).label("fts_score")
        return fts_score


    @staticmethod
    def trgm_search(keywords: str):
        title_ns = func.replace(Books.titles, " ", "")
        q_ns = func.replace(keywords, " ", "")

        trgm_raw = func.greatest(
            func.similarity(Books.titles, keywords),
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
            select(Books, score)
            .where(
                or_(
                    Books.search_tsv.op("@@")(tsq),
                    trgm_score >= 0,
                    Books.titles.ilike(f"%{q}%")
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
