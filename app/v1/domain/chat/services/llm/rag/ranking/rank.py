from sqlmodel import Session, cast, Float, select, asc, desc, func, or_
from app.v1.domain.chat.services.llm.rag.sim.vector import embedding_sim
from app.v1.domain.chat.services.llm.rag.sim.fts_trgm import search_class
from app.v1.common.models.book_tables import BookChunk, BookSimilarity, BookAffiliation


class Ranking:

    def __init__(self):
        self.search = search_class


    def _set_ids(self, session: Session, ask_em: list[float], keywords: str, limit: int):
        top_ids = set()
        vector = embedding_sim(session, ask_em, limit=limit)
        fts_trgm = self.search.fts_trgm_search(session, keywords, limit=limit)
        for (t, n, d), (book, score) in zip(vector, fts_trgm):
            top_ids.add(n)
            top_ids.add(book.id)
        return list(top_ids)


    @staticmethod
    def _vector_top_k(session: Session, ask_em: list[float], top_ids: list):
        distances = cast(BookSimilarity.vector_similarity.op("<=>")(ask_em), Float).label("distance")
        result = (
            select(
                BookSimilarity.book_affiliationid)  # distances
            .where(BookSimilarity.book_affiliationid.in_(top_ids))
            .order_by(asc(distances)).limit(len(top_ids))
        )
        vector_top = session.exec(result).all()
        return vector_top


    def _fts_trgm_top_k(self, session: Session, keywords: str, top_ids: list):
        tsq = func.websearch_to_tsquery("simple", keywords)
        fts_score = self.search.fts_search(keywords)
        trgm_score = self.search.trgm_search(keywords)
        score = fts_score + trgm_score

        stmt = (
            select(BookAffiliation.id)  # score
            .where(
                or_(
                    BookAffiliation.search_tsv.op("@@")(tsq),
                    trgm_score >= 0,
                    BookAffiliation.book.titles.ilike(f"%{keywords}%")
                )
            )
            .where(BookAffiliation.id.in_(top_ids))
            .order_by(desc(score))
            .limit(len(top_ids))
        )
        keywords_top = session.exec(stmt).all()
        return keywords_top


    def _rank_list(self, session: Session, ask_em: list[float], keywords: str, limit: int):
        top_ids = self._set_ids(session, ask_em, keywords, limit)

        vector_top = self._vector_top_k(session, ask_em, top_ids)
        keywords_top = self._fts_trgm_top_k(session, keywords, top_ids)

        return vector_top, keywords_top


    def _rank_top_k(self, session: Session, ask_em: list[float], keywords: str, limit: int, k=60, w_vec=1.0, w_fts=1.0):
        vec_ids, key_ids = self._rank_list(session, ask_em, keywords, limit)
        vec_rank = {bid: i + 1 for i, bid in enumerate(vec_ids)}
        key_rank = {bid: i + 1 for i, bid in enumerate(key_ids)}

        # 후보(합집합)
        all_ids = set(vec_rank) | set(key_rank)

        scores = {}
        for bid in all_ids:
            s = 0.0
            if bid in vec_rank:
                s += w_vec * (1.0 / (k + vec_rank[bid]))
            if bid in key_rank:
                s += w_fts * (1.0 / (k + key_rank[bid]))
            scores[bid] = s

        fused = sorted(all_ids, key=lambda x: scores[x], reverse=True)
        return fused


    def get_ranked_chunk(self, session: Session, ask_em: list[float], keywords: str, limit: int):
        a = self._rank_top_k(session, ask_em=ask_em, keywords=keywords, limit=limit)

        stmt = select(BookChunk.id, BookChunk.chunk).where(BookChunk.id.in_(a))
        result = session.exec(stmt).all()

        m = {bid: text for bid, text in result}
        ordered_texts = [f"[id] {bid}\n" + m[bid] for bid in a if bid in m]
        return ordered_texts


ranking_class = Ranking()