from pydantic import BaseModel
from typing import Optional

class NewsArticle(BaseModel):
    id: int
    title: str
    summary: str
    source: str
    published_at: str
    region: Optional[str] = None

    class Config:
        orm_mode = True
