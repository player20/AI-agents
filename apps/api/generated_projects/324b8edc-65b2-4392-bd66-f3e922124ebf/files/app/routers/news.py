from fastapi import APIRouter, Depends, HTTPException
from typing import List
from sqlalchemy.orm import Session

from app.models.news import NewsArticle
from app.database import get_db
from app.services.ai_summarizer import summarize_article

router = APIRouter()

@router.get("/articles", response_model=List[dict])
async def get_articles(region: str | None = None, db: Session = Depends(get_db)):
    query = db.query(NewsArticle)
    if region:
        query = query.filter(NewsArticle.region == region)
    articles = query.all()
    return [{
        "id": article.id,
        "title": article.title,
        "summary": article.summary,
        "source": article.source,
        "region": article.region,
        "published_at": article.published_at
    } for article in articles]

@router.get("/articles/{article_id}", response_model=dict)
async def get_article(article_id: int, db: Session = Depends(get_db)):
    article = db.query(NewsArticle).filter(NewsArticle.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return {
        "id": article.id,
        "title": article.title,
        "content": article.content,
        "summary": article.summary,
        "source": article.source,
        "region": article.region,
        "published_at": article.published_at
    }

@router.post("/articles/aggregate")
async def aggregate_articles(source_urls: List[str], region: str | None = None, db: Session = Depends(get_db)):
    # Placeholder for aggregating articles from multiple sources
    # In a real implementation, this would fetch articles from URLs using a scraper
    for url in source_urls:
        # Simulated article data
        article_data = {
            "title": f"Sample Article from {url}",
            "content": "This is a placeholder content fetched from the source.",
            "source": url,
            "region": region or "global"
        }
        summarized_content = summarize_article(article_data['content'])
        new_article = NewsArticle(
            title=article_data['title'],
            content=article_data['content'],
            summary=summarized_content,
            source=article_data['source'],
            region=article_data['region']
        )
        db.add(new_article)
    db.commit()
    return {"message": "Articles aggregated and summarized successfully"}
