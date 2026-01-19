from typing import List, Optional
import asyncpg
from app.models.news import NewsArticle

class NewsRepository:
    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool

    async def get_articles(self, region: Optional[str] = None, limit: int = 20) -> List[NewsArticle]:
        query = """
            SELECT id, title, summary, source, published_at, region
            FROM news_articles
            WHERE ($1::text IS NULL OR region = $1)
            ORDER BY published_at DESC
            LIMIT $2
        """
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(query, region, limit)
            return [NewsArticle(**row) for row in rows]

    async def get_article_by_id(self, article_id: int) -> Optional[NewsArticle]:
        query = """
            SELECT id, title, summary, source, published_at, region
            FROM news_articles
            WHERE id = $1
        """
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(query, article_id)
            return NewsArticle(**row) if row else None
