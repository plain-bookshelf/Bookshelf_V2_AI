"""
Bookshelf CSV → PostgreSQL 적재 스크립트
=========================================
대상 테이블: affiliation, book, genre, book_genre, book_affiliation, book_detail
FTS(similarity_token): title + author + description + genre 조합으로 to_tsvector 생성

사용법:
    pip install psycopg2-binary pandas tqdm
    python load_books.py --dsn "postgresql://user:pass@host:5432/dbname" \
                         --csv Bookshelf_sample2.csv \
                         --affiliation-id 1   # 학교 affiliation id (없으면 자동 생성)
"""

import argparse
import math
import sys
from typing import Optional

import pandas as pd
import psycopg2
import psycopg2.extras
from tqdm import tqdm

# ──────────────────────────────────────────────
# 1. CSV 로드
# ──────────────────────────────────────────────

def load_csv(path: str) -> pd.DataFrame:
    # latin1 로 읽고 한글 컬럼은 재인코딩 시도
    df = pd.read_csv(path, encoding="latin1", dtype=str)
    # 공백 컬럼명 제거
    df.columns = df.columns.str.strip()
    # NaN → None
    df = df.where(pd.notna(df), None)
    return df


def safe_str(val, max_len: int = None) -> Optional[str]:
    if val is None or (isinstance(val, float) and math.isnan(val)):
        return None
    s = str(val).strip()
    if max_len:
        s = s[:max_len]
    return s or None


def safe_int(val, default: int = 0) -> int:
    try:
        return int(float(val))
    except (TypeError, ValueError):
        return default


def safe_bool(val) -> bool:
    if val is None:
        return False
    s = str(val).strip().lower()
    return s in ("true", "1", "yes")


# ──────────────────────────────────────────────
# 2. DB 헬퍼
# ──────────────────────────────────────────────

def upsert_affiliation(cur, name: str) -> int:
    """affiliation_name 으로 upsert, id 반환"""
    cur.execute(
        """
        INSERT INTO affiliation (affiliation_name)
        VALUES (%s)
        ON CONFLICT (affiliation_name) DO UPDATE SET affiliation_name = EXCLUDED.affiliation_name
        RETURNING id
        """,
        (name[:100],),
    )
    return cur.fetchone()[0]


def get_or_create_affiliation(cur, name: str, cache: dict) -> int:
    if name not in cache:
        cache[name] = upsert_affiliation(cur, name)
    return cache[name]


def upsert_genre(cur, name: str) -> int:
    cur.execute(
        """
        INSERT INTO genre (genre_name)
        VALUES (%s)
        ON CONFLICT (genre_name) DO UPDATE SET genre_name = EXCLUDED.genre_name
        RETURNING id
        """,
        (name[:45],),
    )
    return cur.fetchone()[0]


def get_or_create_genre(cur, name: str, cache: dict) -> int:
    if name not in cache:
        cache[name] = upsert_genre(cur, name)
    return cache[name]


def upsert_book(cur, title, author, pub_date, intro, image, publisher) -> int:
    """title + author + publisher 로 중복 체크 후 upsert
    publisher는 NULL 대신 '' 빈 문자열로 통일해서 unique 제약이 정상 동작하도록 함
    """
    cur.execute(
        """
        INSERT INTO book (title, author, publication_date, introduction, book_image, publisher)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (title, author, publisher) DO UPDATE
            SET publication_date = COALESCE(EXCLUDED.publication_date, book.publication_date),
                introduction     = COALESCE(EXCLUDED.introduction, book.introduction),
                book_image       = COALESCE(EXCLUDED.book_image, book.book_image)
        RETURNING id
        """,
        (title, author, pub_date, intro, image, publisher),
    )
    return cur.fetchone()[0]


def link_book_genre(cur, book_id: int, genre_id: int):
    cur.execute(
        """
        INSERT INTO book_genre (book_id, genre_id)
        VALUES (%s, %s)
        ON CONFLICT DO NOTHING
        """,
        (book_id, genre_id),
    )


def upsert_book_affiliation(
    cur, book_id, affiliation_id, rental_count, reservation_count, like_count,
    fts_text: str,
) -> int:
    """
    book_id + affiliation_id 조합으로 upsert.
    similarity_token 은 to_tsvector('simple', ...) 로 직접 생성.
    """
    cur.execute(
        """
        INSERT INTO book_affiliation
            (book_id, affiliation_id, rental_count, reservation_count, like_count, similarity_token)
        VALUES
            (%s, %s, %s, %s, %s, to_tsvector('simple', %s))
        ON CONFLICT (book_id, affiliation_id) DO UPDATE
            SET rental_count      = EXCLUDED.rental_count,
                reservation_count = EXCLUDED.reservation_count,
                like_count        = EXCLUDED.like_count,
                similarity_token  = EXCLUDED.similarity_token
        RETURNING id
        """,
        (book_id, affiliation_id, rental_count, reservation_count, like_count, fts_text),
    )
    return cur.fetchone()[0]


def insert_book_detail(
    cur,
    book_affiliation_id,
    member_id,
    rental_request_status,
    rental_status,
    return_date,
    registration_number,
    call_number,
):
    cur.execute(
        """
        INSERT INTO book_detail
            (book_affiliation_id, member_id, rental_request_status, rental_status,
             return_date, registration_number, call_number)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT DO NOTHING
        """,
        (
            book_affiliation_id,
            member_id,
            rental_request_status,
            rental_status,
            return_date,
            registration_number,
            call_number,
        ),
    )


# ──────────────────────────────────────────────
# 3. unique constraint 보장 (없을 경우 생성)
# ──────────────────────────────────────────────

SETUP_SQL = """
-- affiliation 이름 unique
ALTER TABLE affiliation ADD CONSTRAINT IF NOT EXISTS uq_affiliation_name UNIQUE (affiliation_name);

-- book title+author+publisher unique (publisher NULL → '' 로 통일)
ALTER TABLE book ADD CONSTRAINT IF NOT EXISTS uq_book_title_author_publisher UNIQUE (title, author, publisher);

-- book_affiliation (book_id, affiliation_id) unique
ALTER TABLE book_affiliation ADD CONSTRAINT IF NOT EXISTS uq_book_affiliation UNIQUE (book_id, affiliation_id);
"""


# ──────────────────────────────────────────────
# 4. 카테고리 파싱 (예: "교양>자기계발>리더십>리더십")
# ──────────────────────────────────────────────

def parse_genres(raw: Optional[str]) -> list[str]:
    if not raw:
        return []
    parts = [p.strip() for p in raw.replace("\\", "").split(">")]
    # 중복 제거 + 빈 문자열 제거
    seen, result = set(), []
    for p in parts:
        if p and p not in seen:
            seen.add(p)
            result.append(p[:45])
    return result


# ──────────────────────────────────────────────
# 5. 메인 적재 루프
# ──────────────────────────────────────────────

def load(dsn: str, csv_path: str, batch_size: int = 500):
    print(f"[1/5] CSV 로드: {csv_path}")
    df = load_csv(csv_path)
    print(f"      총 {len(df):,}행 로드 완료")

    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        dbname="BookMaru",
        user="ADMIN",
        password="heijiADMIN20090220!"
    )
    conn.autocommit = False
    cur = conn.cursor()

    # unique constraint 준비
    print("[2/5] DB constraint 확인/생성")
    try:
        for stmt in SETUP_SQL.strip().split(";"):
            stmt = stmt.strip()
            if stmt:
                cur.execute(stmt)
        conn.commit()
    except Exception as e:
        print(f"      [WARN] constraint 생성 중 오류 (이미 존재할 수 있음): {e}")
        conn.rollback()

    affiliation_cache: dict[str, int] = {}
    genre_cache: dict[str, int] = {}

    errors = []

    print(f"[3/5] 데이터 적재 시작 (batch={batch_size})")
    for idx, row in tqdm(df.iterrows(), total=len(df), unit="row"):
        try:
            # ── 필수값 ──────────────────────────
            title  = safe_str(row.get("title"), 100)
            author = safe_str(row.get("writer"), 100)
            if not title or not author:
                errors.append((idx, "title 또는 author 없음"))
                continue

            pub_date    = safe_str(row.get("pubDate"), 20)
            intro       = safe_str(row.get("description"), 1000) or ""
            image       = safe_str(row.get("img"), 100) or ""
            publisher   = safe_str(row.get("publisher"), 20) or ""  # NULL → '' 로 통일 (unique 제약)
            school_name = safe_str(row.get("school"), 100) or "Unknown"
            catgory_raw = safe_str(row.get("catgory"))

            rental_count      = safe_int(row.get("rental_count"))
            like_count        = safe_int(row.get("like_count"))
            reservation_count = safe_int(row.get("reservation_count"))

            # book_detail 관련
            member_raw   = row.get("member")
            id_number    = safe_str(row.get("id_number"), 100) or ""
            call_num     = safe_str(row.get("call_num"), 45) or ""
            return_date  = safe_str(row.get("return_date"))
            rental_req   = safe_bool(row.get("rental_requset_status"))
            rental_st    = safe_bool(row.get("rental_status"))

            # ── genre 파싱 ──────────────────────
            genres = parse_genres(catgory_raw)

            # ── FTS 텍스트 ──────────────────────
            fts_parts = [title, author, intro] + genres
            fts_text  = " ".join(p for p in fts_parts if p)

            # ── affiliation ─────────────────────
            aff_id = get_or_create_affiliation(cur, school_name, affiliation_cache)

            # ── book ────────────────────────────
            book_id = upsert_book(cur, title, author, pub_date, intro, image, publisher)

            # ── genre + book_genre ───────────────
            for g in genres:
                g_id = get_or_create_genre(cur, g, genre_cache)
                link_book_genre(cur, book_id, g_id)

            # ── book_affiliation ─────────────────
            ba_id = upsert_book_affiliation(
                cur, book_id, aff_id,
                rental_count, reservation_count, like_count,
                fts_text,
            )

            # ── book_detail (member 있을 때만) ───
            if member_raw is not None:
                member_id = safe_int(member_raw, default=None)
                if member_id is not None:
                    insert_book_detail(
                        cur,
                        ba_id,
                        member_id,
                        rental_req,
                        rental_st,
                        return_date,
                        id_number,
                        call_num,
                    )

            # batch commit
            if (idx + 1) % batch_size == 0:
                conn.commit()

        except Exception as e:
            conn.rollback()
            errors.append((idx, str(e)))

    conn.commit()
    cur.close()
    conn.close()

    print(f"\n[4/5] 완료")
    print(f"      성공: {len(df) - len(errors):,}행")
    print(f"      실패: {len(errors):,}행")
    if errors:
        print("\n[5/5] 실패 목록 (최대 20건):")
        for i, (row_idx, msg) in enumerate(errors[:20]):
            print(f"      row {row_idx}: {msg}")


# ──────────────────────────────────────────────
# 6. CLI
# ──────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Bookshelf CSV → PostgreSQL 적재")
    parser.add_argument(
        "--dsn",
        default="postgresql://ADMIN:heijiADMIN20090220%21@localhost:5432/BookMaru",
        help="DB 접속 DSN",
    )
    parser.add_argument("--csv", default="Bookshelf_sample2.csv", help="CSV 파일 경로")
    parser.add_argument("--batch", type=int, default=500, help="커밋 배치 크기 (기본 500)")
    args = parser.parse_args()

    load(dsn=args.dsn, csv_path=args.csv, batch_size=args.batch)

# DB_HOST=db
# DB_USERNAME=ADMIN
# DB_PASSWORD=heijiADMIN20090220!
# DB_NAME=BookMaru