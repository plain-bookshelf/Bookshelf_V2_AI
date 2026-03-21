from sqlmodel import text
from app.local_test_version.db.session import engine

with engine.begin() as conn:
    conn.execute(text("""
        ALTER TABLE books
        ADD COLUMN IF NOT EXISTS search_tsv tsvector;
    """))

    conn.execute(text("""
        UPDATE books
        SET search_tsv =
          to_tsvector('simple',
            coalesce(titles,'') || ' ' ||
            coalesce(authors,'') || ' ' ||
            coalesce(publisher,'') || ' ' ||
            coalesce(genres,'') || ' ' ||
            coalesce(intro,'')
          )
        WHERE search_tsv IS NULL;
    """))

    conn.execute(text("""
        CREATE INDEX IF NOT EXISTS books_search_tsv_gin
        ON books USING gin (search_tsv);
    """))

    conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm;"))

    conn.execute(text("""
                      CREATE INDEX IF NOT EXISTS books_titles_trgm
                          ON books USING gin (titles gin_trgm_ops);
                      """))

    conn.execute(text("""
                      CREATE INDEX IF NOT EXISTS books_authors_trgm
                          ON books USING gin (authors gin_trgm_ops);
                      """))