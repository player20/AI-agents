from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from pydantic import BaseModel
from app.services.news_service import NewsService
from app.models.news import NewsArticle

router = APIRouter()

class NewsArticleResponse(BaseModel):
    id: int
    title: str
    summary: str
    source: str
    published_at: str
    region: Optional[str] = None

@router.get("/articles", response_model=List[NewsArticleResponse])
async def get_articles(
    region: Optional[str] = None,
    limit: int = 20,
    news_service: NewsService = Depends(NewsService)
):
    try:
        articles = await news_service.get_articles(region=region, limit=limit)
        return articles
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/articles/{article_id}", response_model=NewsArticleResponse)
async def get_article(
    article_id: int,
    news_service: NewsService = Depends(NewsService)
):
    try:
        article = await news_service.get_article_by_id(article_id)
        if not article:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article not found")
        return article
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
