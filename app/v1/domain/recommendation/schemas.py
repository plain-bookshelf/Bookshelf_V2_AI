from pydantic import BaseModel
from typing import Optional, List


class BookInfo(BaseModel):
    id: int
    title: str
    img: Optional[str] = None
    dis: float


class BookResponse(BaseModel):
    books: List[BookInfo]