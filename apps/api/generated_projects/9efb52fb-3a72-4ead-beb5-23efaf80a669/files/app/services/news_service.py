from typing import List, Optional
from app.models.news import NewsArticle
from app.repositories.news_repository import NewsRepository

class NewsService:
    def __init__(self, repository: NewsRepository):
        self.repository = repository

    async def get_articles(self, region: Optional[str] = None, limit: int = 20) -> List[NewsArticle]:
        return await self.repository.get_articles(region=region, limit=limit)

    async def get_article_by_id(self, article_id: int) -> Optional[NewsArticle]:
        return await self.repository.get_article_by_id(article_id)

    async def aggregate_news(self, sources: List[str]):
        # Placeholder for AI-driven aggregation logic
        pass
