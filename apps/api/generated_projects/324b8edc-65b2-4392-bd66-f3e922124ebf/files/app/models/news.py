from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func

from app.database import Base

class NewsArticle(Base):
    __tablename__ = "news_articles"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    summary = Column(Text, nullable=False)
    source = Column(String, nullable=False)
    region = Column(String, default="global")
    published_at = Column(DateTime, default=func.now())
    created_at = Column(DateTime, default=func.now())
