"""Pydantic models for data structures."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class ArticleSource(str, Enum):
    TECHCRUNCH = "techcrunch"
    THE_VERGE = "theverge"
    HN = "hn"


class Collection(str, Enum):
    SOURCES = "sources"
    ARTICLES = "articles"
    PROCESSED = "processed_articles"
    CLUSTERS = "clusters"
    CLUSTER_MEMBERS = "cluster_members"
    DAILY_BRIEFS = "daily_briefs"
    PIPELINE_RUNS = "pipeline_runs"


class Source(BaseModel):
    """External data source configuration."""

    id: str = Field(description="Unique source identifier (e.g., 'techcrunch')")
    name: str = Field(description="Display name of the source")
    feed_url: str = Field(description="RSS feed URL or API endpoint")
    feed_type: str = Field(description="Source type: 'rss' or 'api'")
    enabled: bool = Field(default=True)
    last_success: Optional[datetime] = Field(default=None)
    last_error: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Article(BaseModel):
    """Raw news article from a data source."""

    id: str = Field(default_factory=lambda: uuid4().hex[:12])
    source_url: str = Field(description="Original article URL")
    source_name: str = Field(description="Name of the data source")
    source: ArticleSource = Field(description="Source type")
    raw_title: str = Field(description="Original article title")
    raw_description: str = Field(
        default="", description="Original article description/summary"
    )
    published_at: Optional[datetime] = Field(
        default=None, description="Original publication time"
    )
    fetched_at: datetime = Field(default_factory=datetime.utcnow)
    language: str = Field(default="en", description="Detected language code")

    def __hash__(self) -> int:
        return hash(self.source_url)


class ProcessedArticle(BaseModel):
    """Article after AI processing."""

    id: str = Field(default_factory=lambda: uuid4().hex[:12])
    article_id: str = Field(description="FK to Article.id")
    headline_zh: str = ""
    summary_zh: str = ""
    why_it_matters_zh: str = ""
    category: str = "general"
    tags: list[str] = Field(default_factory=list)
    importance_score: int = 0
    source_confidence: float = 0.0
    related_entities: list[str] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    generation_status: str = "pending"  # pending | success | failed


class Cluster(BaseModel):
    """Event cluster grouping related articles."""

    id: str = Field(default_factory=lambda: uuid4().hex[:12])
    representative_article_id: str = Field(description="FK to Article.id")
    cluster_type: str = "title_similarity"
    member_article_ids: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class DailyBrief(BaseModel):
    """Daily structured brief."""

    id: str = Field(default_factory=lambda: uuid4().hex[:12])
    date: str = Field(description="Date in YYYY-MM-DD format")
    trend_summary: str = ""
    highlights: list[dict] = Field(default_factory=list)
    dev_focus: list[dict] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    generation_status: str = "pending"  # pending | success | failed


class PipelineRun(BaseModel):
    """A single collection run record."""

    id: str = Field(default_factory=lambda: uuid4().hex[:12])
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    status: str = "running"  # running | success | partial_failure | failed
    articles_fetched: int = 0
    articles_new: int = 0
    articles_updated: int = 0
    source_results: dict[str, dict] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
