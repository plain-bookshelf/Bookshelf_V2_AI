"""
알라딘 Open API 도서 정보 수집기
- 학교 도서 엑셀 파일을 읽어서 알라딘 API로 상세 정보 수집
- API 키 자동 로테이션 (횟수 초과 시 다음 키로 전환)
- 중단 시점 저장 및 재개 기능 (checkpoint)
- DB 적재 가능한 CSV 출력

출력 CSV 컬럼 → DB 테이블 매핑:
  title              → book.title
  author             → book.author
  publisher          → book.publisher
  publication_date   → book.publication_date
  introduction       → book.introduction
  book_image         → book.book_image
  genre_name         → genre.genre_name  (BookGenre 연결용)
  affiliation_name   → affiliation.affiliation_name
  registration_number→ book_detail.registration_number  (id_number)
  call_number        → book_detail.call_number           (call_num)
  api_found          → 알라딘 API 매칭 성공 여부 (True/False)
"""

import time
import json
import logging
import requests
import pandas as pd
from pathlib import Path

# ─────────────────────────────────────────────
# ⚙️  설정 영역 (여기만 수정하면 됩니다)
# ─────────────────────────────────────────────

# 알라딘 API 키 목록 (순서대로 사용, 제한 초과 시 다음 키로 전환)
API_KEYS = [
    "ttblgg40171731002",
    "ttblgg40171731003",
    "YOUR_TTB_KEY_3",
    # 필요한 만큼 추가
]

# 파일 경로
EXCEL_INPUT_PATH = "school_books.xlsx"   # 학교 도서 엑셀 파일 경로
OUTPUT_CSV_PATH  = "books_for_db.csv"    # 최종 출력 CSV
CHECKPOINT_PATH  = "crawler_checkpoint.json"  # 중단점 저장 파일
FAILED_LOG_PATH  = "failed_books.csv"    # API 매칭 실패 목록

# API 요청 설정
REQUEST_DELAY_SEC    = 0.35   # 요청 간격 (초) — 알라딘 서버 부하 방지
MAX_RETRIES          = 3      # 동일 키 재시도 횟수
RATE_LIMIT_PAUSE_SEC = 5      # 키 전환 전 대기 시간
API_VERSION          = "20131101"

# ─────────────────────────────────────────────
# 로깅 설정
# ─────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("crawler.log", encoding="utf-8"),
    ],
)
log = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# API 키 로테이터
# ─────────────────────────────────────────────
class ApiKeyRotator:
    def __init__(self, keys: list[str]):
        if not keys or keys[0].startswith("YOUR_"):
            raise ValueError("API_KEYS에 실제 TTBKey를 입력하세요!")
        self.keys = keys
        self.idx  = 0
        self.exhausted: set[int] = set()

    @property
    def current_key(self) -> str:
        return self.keys[self.idx]

    def rotate(self) -> bool:
        """다음 사용 가능한 키로 전환. 모두 소진되면 False 반환."""
        self.exhausted.add(self.idx)
        for i, _ in enumerate(self.keys):
            if i not in self.exhausted:
                self.idx = i
                log.warning(f"🔑 API 키 전환: 키 #{self.idx + 1} 사용 시작")
                return True
        log.error("❌ 모든 API 키가 소진되었습니다.")
        return False

    def reset_exhausted(self):
        """전체 재시작 시 소진 상태 초기화"""
        self.exhausted.clear()
        self.idx = 0


# ─────────────────────────────────────────────
# 알라딘 API 클라이언트
# ─────────────────────────────────────────────
class AladinClient:
    SEARCH_URL = "http://www.aladin.co.kr/ttb/api/ItemSearch.aspx"
    LOOKUP_URL = "http://www.aladin.co.kr/ttb/api/ItemLookUp.aspx"

    def __init__(self, rotator: ApiKeyRotator):
        self.rotator = rotator
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "LibraryDataCollector/1.0"})

    def _get(self, url: str, params: dict) -> dict | None:
        """GET 요청 with 재시도 + 키 로테이션."""
        params["ttbkey"] = self.rotator.current_key
        params["output"] = "JS"
        params["Version"] = API_VERSION

        for attempt in range(MAX_RETRIES):
            try:
                resp = self.session.get(url, params=params, timeout=10)
                resp.raise_for_status()

                # 알라딘은 rate limit을 HTTP 오류가 아닌 본문으로 전달하는 경우 있음
                text = resp.text
                if "일일 사용량" in text or "ttbkey" in text.lower() and "error" in text.lower():
                    log.warning("⚠️  API 제한 감지 — 키 전환 시도")
                    time.sleep(RATE_LIMIT_PAUSE_SEC)
                    if not self.rotator.rotate():
                        return None
                    params["ttbkey"] = self.rotator.current_key
                    continue

                return resp.json()

            except requests.exceptions.HTTPError as e:
                status = e.response.status_code if e.response else 0
                if status == 429 or status == 403:
                    log.warning(f"⚠️  HTTP {status} — 키 전환 시도")
                    time.sleep(RATE_LIMIT_PAUSE_SEC)
                    if not self.rotator.rotate():
                        return None
                    params["ttbkey"] = self.rotator.current_key
                else:
                    log.error(f"HTTP 오류 {status}: {e}")
                    time.sleep(2 ** attempt)

            except requests.exceptions.RequestException as e:
                log.warning(f"네트워크 오류 (시도 {attempt+1}/{MAX_RETRIES}): {e}")
                time.sleep(2 ** attempt)

        return None

    def search(self, title: str, author: str) -> dict | None:
        """제목+저자로 검색 → 첫 번째 결과 반환."""
        query = f"{title} {author}".strip()
        params = {
            "Query":        query,
            "QueryType":    "Keyword",
            "SearchTarget": "Book",
            "MaxResults":   1,
            "start":        1,
            "Cover":        "Big",
        }
        data = self._get(self.SEARCH_URL, params)
        if data and data.get("item"):
            return data["item"][0]
        # 저자 없이 제목만 재시도
        if author:
            params["Query"]     = title
            params["QueryType"] = "Title"
            data = self._get(self.SEARCH_URL, params)
            if data and data.get("item"):
                return data["item"][0]
        return None

    def lookup(self, isbn13: str) -> dict | None:
        """ISBN13으로 상세 조회 (fullDescription, 카테고리 등)."""
        params = {
            "itemIdType": "ISBN13",
            "ItemId":     isbn13,
            "Cover":      "Big",
            "OptResult": "categoryIdList,fulldescription",  # 카테고리 정보 포함
        }
        data = self._get(self.LOOKUP_URL, params)
        if data and data.get("item"):
            return data["item"][0]
        return None


# ─────────────────────────────────────────────
# 체크포인트 (중단 재개)
# ─────────────────────────────────────────────
def load_checkpoint() -> int:
    p = Path(CHECKPOINT_PATH)
    if p.exists():
        cp = json.loads(p.read_text(encoding="utf-8"))
        idx = cp.get("last_processed_index", -1)
        log.info(f"📌 체크포인트 발견: {idx + 1}번 행부터 재개")
        return idx
    return -1

def save_checkpoint(idx: int):
    Path(CHECKPOINT_PATH).write_text(
        json.dumps({"last_processed_index": idx}, ensure_ascii=False),
        encoding="utf-8",
    )


# ─────────────────────────────────────────────
# 알라딘 응답 → DB 컬럼 매핑
# ─────────────────────────────────────────────
def extract_book_info(item: dict, detail: dict | None) -> dict:
    """알라딘 API 응답에서 DB에 필요한 필드만 추출."""
    src = detail if detail else item  # lookup 성공 시 상세 정보 우선

    # 카테고리(장르) 이름 추출
    genre_name = ""
    # lookup 결과에서 categoryIdList 사용
    cat_list = (src.get("categoryIdList") or {}).get("categoryInfo", [])
    if isinstance(cat_list, dict):
        cat_list = [cat_list]
    if cat_list:
        # 가장 세분화된 카테고리 (마지막) 사용
        genre_name = cat_list[-1].get("categoryName", "")
    # fallback: 검색 결과의 categoryName
    if not genre_name:
        genre_name = item.get("categoryName", "")

    # fullDescription 우선, 없으면 description(요약)
    introduction = (
        src.get("fullDescription")
        or src.get("fullDescription2")
        or item.get("description")
        or ""
    )
    # DB 컬럼 max_length=1000 맞춤 truncate
    introduction = introduction[:1000].strip()

    return {
        "title":            (src.get("title") or item.get("title", ""))[:100],
        "author":           (src.get("author") or item.get("author", ""))[:100],
        "publisher":        (src.get("publisher") or item.get("publisher", ""))[:20],
        "publication_date": (src.get("pubDate") or item.get("pubDate", ""))[:20],
        "introduction":     introduction,
        "book_image":       (src.get("cover") or item.get("cover", ""))[:100],
        "genre_name":       genre_name[:45],
        "api_found":        True,
    }


# ─────────────────────────────────────────────
# 메인 크롤러
# ─────────────────────────────────────────────
def run_crawler():
    # 1. 엑셀 로드
    log.info(f"📂 엑셀 파일 로딩: {EXCEL_INPUT_PATH}")
    df_excel = pd.read_excel(EXCEL_INPUT_PATH, dtype=str).fillna("")
    log.info(f"   총 {len(df_excel):,}행 로드 완료")

    # 컬럼 정규화 (한글/영문 헤더 모두 허용)
    col_map = {
        "title":      ["title", "제목", "도서명"],
        "writer":     ["writer", "author", "저자", "작가"],
        "publisher":  ["publisher", "출판사"],
        "school":     ["school", "소속", "학교"],
        "id_number":  ["id_number", "등록번호", "id번호"],
        "call_num":   ["call_num", "청구기호", "call_number"],
    }
    rename = {}
    for target, candidates in col_map.items():
        for c in candidates:
            if c in df_excel.columns:
                rename[c] = target
                break
    df_excel = df_excel.rename(columns=rename)

    required = ["title", "writer", "publisher", "school", "id_number", "call_num"]
    missing = [c for c in required if c not in df_excel.columns]
    if missing:
        raise ValueError(f"엑셀에 필수 컬럼 없음: {missing}\n실제 컬럼: {list(df_excel.columns)}")

    # 2. 체크포인트 확인
    last_idx = load_checkpoint()
    start_from = last_idx + 1

    # 3. 기존 결과 CSV 이어쓰기 준비
    output_path = Path(OUTPUT_CSV_PATH)
    failed_path = Path(FAILED_LOG_PATH)
    write_header = not output_path.exists() or start_from == 0

    # 4. API 클라이언트 초기화
    rotator = ApiKeyRotator(API_KEYS)
    client  = AladinClient(rotator)

    # 5. 순회
    total = len(df_excel)
    success_count = 0
    fail_count    = 0

    log.info(f"🚀 크롤링 시작: {start_from}번 행부터 (총 {total - start_from:,}건 처리 예정)")

    for i, row in df_excel.iterrows():
        if i < start_from:
            continue

        title     = str(row["title"]).strip()
        writer    = str(row["writer"]).strip()
        publisher = str(row["publisher"]).strip()
        school    = str(row["school"]).strip()
        id_number = str(row["id_number"]).strip()
        call_num  = str(row["call_num"]).strip()

        if not title:
            log.warning(f"[{i}] 제목 없음 — 건너뜀")
            continue

        log.info(f"[{i}/{total}] 검색: '{title}' / {writer}")

        # 5-1. 검색
        item = client.search(title, writer)

        if item:
            # 5-2. ISBN13으로 상세 조회 (fullDescription, 카테고리)
            isbn13 = item.get("isbn13") or item.get("isbn", "")
            detail = None
            if isbn13:
                detail = client.lookup(isbn13)
                time.sleep(REQUEST_DELAY_SEC)

            book_info = extract_book_info(item, detail)
            success_count += 1
        else:
            # API 미매칭: 엑셀 원본 데이터만 저장
            book_info = {
                "title":            title[:100],
                "author":           writer[:100],
                "publisher":        publisher[:20],
                "publication_date": "",
                "introduction":     "",
                "book_image":       "",
                "genre_name":       "",
                "api_found":        False,
            }
            fail_count += 1
            log.warning(f"   ↳ API 미매칭: '{title}'")

        # 5-3. DB 매핑 컬럼 조합
        record = {
            # ── book 테이블
            "title":             book_info["title"] or title[:100],
            "author":            book_info["author"] or writer[:100],
            "publisher":         book_info["publisher"] or publisher[:20],
            "publication_date":  book_info["publication_date"],
            "introduction":      book_info["introduction"],
            "book_image":        book_info["book_image"],
            # ── genre 테이블 (BookGenre 연결)
            "genre_name":        book_info["genre_name"],
            # ── affiliation 테이블
            "affiliation_name":  school,
            # ── book_detail 테이블
            "registration_number": id_number,
            "call_number":         call_num,
            # ── 메타
            "api_found": book_info["api_found"],
        }

        # 5-4. CSV 저장 (행 단위 즉시 flush → 중단에도 데이터 보존)
        pd.DataFrame([record]).to_csv(
            output_path,
            mode="a",
            header=write_header,
            index=False,
            encoding="utf-8-sig",
        )
        write_header = False

        # 미매칭 별도 로그
        if not book_info["api_found"]:
            pd.DataFrame([{"index": i, "title": title, "writer": writer}]).to_csv(
                failed_path,
                mode="a",
                header=not failed_path.exists(),
                index=False,
                encoding="utf-8-sig",
            )

        # 5-5. 체크포인트 저장 (100건마다)
        if i % 100 == 0:
            save_checkpoint(i)
            log.info(f"   💾 체크포인트 저장 (index={i}) | 성공:{success_count} 실패:{fail_count}")

        time.sleep(REQUEST_DELAY_SEC)

    # 최종 체크포인트
    save_checkpoint(total - 1)
    log.info("=" * 60)
    log.info(f"✅ 완료! 총 {total:,}건 처리")
    log.info(f"   API 매칭 성공: {success_count:,}건")
    log.info(f"   API 미매칭:    {fail_count:,}건  → {FAILED_LOG_PATH}")
    log.info(f"   출력 파일:     {OUTPUT_CSV_PATH}")


# ─────────────────────────────────────────────
# 진행 상황 요약 조회 (옵션)
# ─────────────────────────────────────────────
def print_summary():
    """수집 완료된 CSV의 현황을 출력."""
    p = Path(OUTPUT_CSV_PATH)
    if not p.exists():
        print("아직 수집된 데이터가 없습니다.")
        return
    df = pd.read_csv(p, encoding="utf-8-sig")
    print(f"\n📊 현황 요약 ({OUTPUT_CSV_PATH})")
    print(f"   총 행수:        {len(df):,}")
    print(f"   API 매칭 성공: {df['api_found'].sum():,}")
    print(f"   미매칭:        {(~df['api_found']).sum():,}")
    print(f"   장르 수:       {df['genre_name'].nunique()}")
    print(f"   소속 수:       {df['affiliation_name'].nunique()}")
    print(f"\n상위 장르:\n{df['genre_name'].value_counts().head(10)}")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "summary":
        print_summary()
    else:
        run_crawler()