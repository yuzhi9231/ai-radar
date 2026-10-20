"""Integration tests for AI Radar collector pipeline.

Tests the full data flow: collection → dedup → storage → AI processing.
"""

from __future__ import annotations

import os
import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

# Ensure collector package is importable
sys.path.insert(0, str(Path(__file__).parent))

os.environ["USE_MOCK_AI"] = "true"

import pytest

from collector.ai import process_article
from collector.collectors import COLLECTORS
from collector.db import (
    get_all_articles,
    get_article_by_id,
    get_sources,
    get_stats,
    init_db,
    upsert_article,
)
from collector.dedup import deduplicate
from collector.models import (
    Article,
    ArticleSource,
    DailyBrief,
    PipelineRun,
    ProcessedArticle,
)
from collector.run import run_pipeline

# --- Fixtures ---

@pytest.fixture(autouse=True)
def temp_db(tmp_path: Path):
    """Provide a temporary SQLite database for each test."""
    db_path = tmp_path / "test-ai-radar.db"
    os.environ["DATABASE_URL"] = f"file:{db_path}"
    # Reset global connection
    import collector.db as db_mod
    db_mod._db_conn = None
    init_db(f"file:{db_path}")
    yield db_path
    # Cleanup
    db_mod._db_conn = None


# --- Collection Tests ---

class TestCollector:
    """Test data collection from all sources."""

    def test_collectors_list(self):
        """COLLECTORS should contain exactly 3 sources."""
        assert len(COLLECTORS) == 3
        source_values = [k.value for k in COLLECTORS.keys()]
        assert "techcrunch" in source_values
        assert "theverge" in source_values
        assert "hn" in source_values

    @pytest.mark.skipif(
        os.environ.get("SKIP_NETWORK_TESTS") == "true",
        reason="Network tests disabled (SKIP_NETWORK_TESTS=true)",
    )
    def test_rss_collector_techcrunch(self):
        """TechCrunch RSS collector returns articles with correct structure."""
        from collector.collectors import collect_techcrunch

        articles = collect_techcrunch()
        for article in articles:
            assert isinstance(article, Article)
            assert article.source == ArticleSource.TECHCRUNCH
            assert article.source_url
            assert article.raw_title
            assert article.language in ("en", "zh")

    @pytest.mark.skipif(
        os.environ.get("SKIP_NETWORK_TESTS") == "true",
        reason="Network tests disabled (SKIP_NETWORK_TESTS=true)",
    )
    def test_rss_collector_theverge(self):
        """The Verge RSS collector returns articles with correct structure."""
        from collector.collectors import collect_theverge

        articles = collect_theverge()
        for article in articles:
            assert isinstance(article, Article)
            assert article.source == ArticleSource.THE_VERGE
            assert article.source_url
            assert article.raw_title

    @pytest.mark.skipif(
        os.environ.get("SKIP_NETWORK_TESTS") == "true",
        reason="Network tests disabled (SKIP_NETWORK_TESTS=true)",
    )
    def test_hn_collector(self):
        """Hacker News collector returns articles with correct structure."""
        from collector.collectors import collect_hn

        articles = collect_hn()
        for article in articles:
            assert isinstance(article, Article)
            assert article.source == ArticleSource.HN
            assert article.source_url
            assert article.raw_title


# --- Dedup Tests ---

class TestDedup:
    """Test deduplication logic."""

    def test_url_exact_dedup(self):
        """Articles with the same URL should be deduplicated."""
        url = "https://techcrunch.com/2024/01/01/test-article"
        article1 = Article(source_url=url, source_name="TechCrunch", source=ArticleSource.TECHCRUNCH, raw_title="Test 1")
        article2 = Article(source_url=url, source_name="TechCrunch", source=ArticleSource.TECHCRUNCH, raw_title="Test 1 - Duplicate")
        existing = [article1]
        new, dup_count = deduplicate([article2], existing)
        assert len(new) == 0
        assert dup_count == 1

    def test_title_similarity_dedup(self):
        """Articles with highly similar titles should be deduplicated."""
        base_title = "OpenAI Releases GPT-5 with Revolutionary Multimodal Capabilities"
        article1 = Article(source_url="https://example.com/1", source_name="TC", source=ArticleSource.TECHCRUNCH, raw_title=base_title)
        article2 = Article(source_url="https://example.com/2", source_name="TV", source=ArticleSource.THE_VERGE, raw_title=base_title + " and More")
        existing = [article1]
        new, dup_count = deduplicate([article2], existing)
        assert len(new) == 0
        assert dup_count == 1

    def test_different_articles_not_deduped(self):
        """Articles with different URLs and titles should NOT be deduplicated."""
        article1 = Article(source_url="https://example.com/1", source_name="TC", source=ArticleSource.TECHCRUNCH, raw_title="OpenAI Launches GPT-5")
        article2 = Article(source_url="https://example.com/2", source_name="TV", source=ArticleSource.THE_VERGE, raw_title="Google Announces Gemini Pro Update")
        existing = [article1]
        new, dup_count = deduplicate([article2], existing)
        assert len(new) == 1
        assert dup_count == 0

    def test_dedup_with_existing_articles(self):
        """Dedup should filter new articles against existing ones."""
        existing = [
            Article(source_url="https://example.com/existing", source_name="TC", source=ArticleSource.TECHCRUNCH, raw_title="Existing Article"),
        ]
        new_articles = [
            Article(source_url="https://example.com/existing", source_name="TC", source=ArticleSource.TECHCRUNCH, raw_title="Existing Article"),
            Article(source_url="https://example.com/new", source_name="TV", source=ArticleSource.THE_VERGE, raw_title="Brand New Article"),
        ]
        filtered, dup_count = deduplicate(new_articles, existing)
        assert len(filtered) == 1
        assert filtered[0].raw_title == "Brand New Article"
        assert dup_count == 1


# --- Database Tests ---

class TestDatabase:
    """Test SQLite operations."""

    def test_upsert_article(self, temp_db: Path):
        """Test inserting and retrieving an article."""
        article = Article(
            source_url="https://example.com/test",
            source_name="Test Source",
            source=ArticleSource.TECHCRUNCH,
            raw_title="Test Article",
        )
        result = upsert_article(article)
        assert result is True

        articles = get_all_articles()
        assert len(articles) == 1
        assert articles[0].raw_title == "Test Article"

    def test_upsert_article_duplicate(self, temp_db: Path):
        """Inserting a duplicate article should return False."""
        article1 = Article(
            source_url="https://example.com/test",
            source_name="Test Source",
            source=ArticleSource.TECHCRUNCH,
            raw_title="Test Article",
        )
        result1 = upsert_article(article1)
        result2 = upsert_article(article1)
        assert result1 is True
        assert result2 is False

    def test_get_article_by_id(self, temp_db: Path):
        """Test retrieving an article by ID."""
        article = Article(
            source_url="https://example.com/test",
            source_name="Test Source",
            source=ArticleSource.TECHCRUNCH,
            raw_title="Test Article",
        )
        upsert_article(article)

        fetched = get_article_by_id(article.id)
        assert fetched is not None
        assert fetched.id == article.id
        assert fetched.raw_title == "Test Article"

    def test_get_article_not_found(self, temp_db: Path):
        """Test retrieving a non-existent article."""
        fetched = get_article_by_id("nonexistent")
        assert fetched is None

    def test_get_stats(self, temp_db: Path):
        """Test statistics calculation."""
        # Insert some articles
        for i in range(5):
            article = Article(
                source_url=f"https://example.com/{i}",
                source_name="Test",
                source=ArticleSource.TECHCRUNCH,
                raw_title=f"Article {i}",
            )
            upsert_article(article)

        stats = get_stats()
        assert stats["total_articles"] == 5
        assert stats["enabled_sources"] == 3  # Default sources
        assert stats["today_count"] == 5

    def test_get_sources(self, temp_db: Path):
        """Test retrieving all sources."""
        sources = get_sources()
        assert len(sources) == 3
        source_ids = {s["id"] for s in sources}
        assert source_ids == {"techcrunch", "theverge", "hn"}

    def test_article_language_default(self, temp_db: Path):
        """Articles should default to English language."""
        article = Article(
            source_url="https://example.com/test",
            source_name="Test",
            source=ArticleSource.TECHCRUNCH,
            raw_title="Test",
        )
        upsert_article(article)
        fetched = get_article_by_id(article.id)
        assert fetched.language == "en"


# --- AI Processing Tests ---

class TestAIProcessing:
    """Test AI processing with mock mode."""

    def test_mock_ai_enabled(self):
        """Mock AI mode should be enabled by default in tests."""
        assert os.environ.get("USE_MOCK_AI") == "true"

    def test_process_article_mock(self):
        """Mock AI should return structured processing results."""
        article = Article(
            source_url="https://example.com/test-ai",
            source_name="TechCrunch",
            source=ArticleSource.TECHCRUNCH,
            raw_title="OpenAI Announces New GPT Model",
            raw_description="OpenAI has unveiled its latest language model with improved reasoning capabilities.",
        )
        processed = process_article(article)
        assert isinstance(processed, ProcessedArticle)
        assert processed.article_id == article.id
        assert processed.generation_status == "success"
        assert processed.headline_zh
        assert processed.summary_zh
        assert processed.category in ("general", "product", "research", "business", "engineering")

    def test_mock_ai_headline_in_chinese(self):
        """Mock AI should produce Chinese headlines."""
        article = Article(
            source_url="https://example.com/test-zh",
            source_name="TechCrunch",
            source=ArticleSource.TECHCRUNCH,
            raw_title="Google DeepMind Breakthrough in AI",
        )
        processed = process_article(article)
        assert processed.headline_zh
        # Should not be the same as the English title
        assert processed.headline_zh != article.raw_title

    def test_mock_ai_tags_generated(self):
        """Mock AI should generate tags."""
        article = Article(
            source_url="https://example.com/test-tags",
            source_name="The Verge",
            source=ArticleSource.THE_VERGE,
            raw_title="Apple Launches AI-Powered Vision Pro Update",
        )
        processed = process_article(article)
        assert isinstance(processed.tags, list)
        assert len(processed.tags) > 0

    def test_mock_ai_importance_score(self):
        """Mock AI should assign an importance score."""
        article = Article(
            source_url="https://example.com/test-score",
            source_name="Hacker News",
            source=ArticleSource.HN,
            raw_title="Meta Releases Open Source LLM",
        )
        processed = process_article(article)
        assert isinstance(processed.importance_score, int)
        assert 0 <= processed.importance_score <= 100


# --- Pipeline Integration Test ---

class TestPipeline:
    """Test the full collection pipeline."""

    def test_full_pipeline_with_mock(self, temp_db: Path):
        """Run the full pipeline and verify results."""
        with patch("collector.run.collect_all") as mock_collect:
            # Mock collected articles
            mock_collect.return_value = {
                "techcrunch": [
                    Article(
                        source_url="https://techcrunch.com/test-1",
                        source_name="TechCrunch AI",
                        source=ArticleSource.TECHCRUNCH,
                        raw_title="OpenAI Launches GPT-5",
                        raw_description="New model with multimodal capabilities",
                    ),
                    Article(
                        source_url="https://techcrunch.com/test-2",
                        source_name="TechCrunch AI",
                        source=ArticleSource.TECHCRUNCH,
                        raw_title="Google Announces Gemini Pro 2.0",
                    ),
                ],
                "theverge": [
                    Article(
                        source_url="https://theverge.com/test-1",
                        source_name="The Verge AI",
                        source=ArticleSource.THE_VERGE,
                        raw_title="Apple Vision Pro Gets Major AI Update",
                    ),
                ],
                "hn": [
                    Article(
                        source_url="https://hn.algolia.com/test-1",
                        source_name="Hacker News",
                        source=ArticleSource.HN,
                        raw_title="Show HN: I built an AI code reviewer",
                    ),
                ],
            }

            run = run_pipeline()

            assert run.status == "success"
            assert run.articles_fetched == 4
            assert run.articles_new == 4
            assert len(run.source_results) == 3

            # Verify articles in DB
            articles = get_all_articles()
            assert len(articles) == 4

            # Verify processed articles have Chinese summaries
            for article in articles:
                if article.__processed__:
                    assert article.__processed__.generation_status == "success"


# --- Daily Brief Tests ---

class TestDailyBrief:
    """Test daily brief database operations."""

    def test_upsert_and_get_brief(self, temp_db: Path):
        """Test creating and retrieving a daily brief."""
        from collector.db import get_daily_brief, upsert_daily_brief

        brief = DailyBrief(
            date="2026-10-20",
            trend_summary="AI industry continues rapid growth",
            highlights=[{"headline": "GPT-5 Released", "summary": "New model"}],
            dev_focus=[{"headline": "Open Source LLM", "summary": "Meta release"}],
        )
        upsert_daily_brief(brief)

        fetched = get_daily_brief("2026-10-20")
        assert fetched is not None
        assert fetched.trend_summary == brief.trend_summary
        assert len(fetched.highlights) == 1
        assert fetched.highlights[0]["headline"] == "GPT-5 Released"

    def test_get_nonexistent_brief(self, temp_db: Path):
        """Test retrieving a non-existent daily brief."""
        from collector.db import get_daily_brief

        fetched = get_daily_brief("2020-01-01")
        assert fetched is None


# --- Pipeline Run Tests ---

class TestPipelineRun:
    """Test pipeline run tracking."""

    def test_create_pipeline_run(self, temp_db: Path):
        """Test creating and retrieving a pipeline run."""
        from collector.db import create_pipeline_run, get_latest_pipeline_run

        run = PipelineRun(
            started_at=datetime.utcnow(),
            status="success",
            articles_fetched=10,
            articles_new=5,
        )
        run_id = create_pipeline_run(run)
        assert run_id

        latest = get_latest_pipeline_run()
        assert latest is not None
        assert latest.status == "success"
        assert latest.articles_fetched == 10


# --- CLI Tests ---

class TestCLI:
    """Test CLI entry point."""

    def test_cli_show_help(self, capsys):
        """CLI should show help when no arguments provided."""
        import collector.cli as cli
        sys.argv = ["collector"]
        try:
            cli.main()
        except SystemExit:
            pass
        captured = capsys.readouterr()
        assert "usage" in captured.err.lower() or "usage" in captured.out.lower()

    def test_cli_run_with_mock(self, capsys, tmp_path: Path):
        """CLI run command should work with mock AI."""
        import collector.cli as cli
        import collector.db as db_mod
        os.environ["DATABASE_URL"] = f"file:{tmp_path}/test-cli.db"
        db_mod._db_conn = None

        with patch("collector.run.collect_all") as mock_collect:
            mock_collect.return_value = {
                "techcrunch": [
                    Article(source_url="https://example.com/cli-test", source_name="TC", source=ArticleSource.TECHCRUNCH, raw_title="CLI Test"),
                ],
                "theverge": [],
                "hn": [],
            }
            sys.argv = ["collector", "run"]
            with pytest.raises(SystemExit):
                cli.main()
        captured = capsys.readouterr()
        assert "Fetched:" in captured.out or "New:" in captured.out


# --- Collector Mock Mode Test ---

class TestMockMode:
    """Test mock AI mode behavior."""

    def test_mock_ai_without_ollama(self):
        """Mock mode should work even without Ollama running."""
        # This test verifies that process_article doesn't require Ollama
        article = Article(
            source_url="https://example.com/no-ollama",
            source_name="Test",
            source=ArticleSource.TECHCRUNCH,
            raw_title="Test Article Without Ollama",
        )
        # Should not raise even if Ollama is unreachable
        processed = process_article(article)
        assert processed.generation_status == "success"

    def test_mock_ai_different_titles_produce_different_summaries(self):
        """Different article titles should produce different mock summaries."""
        article1 = Article(
            source_url="https://example.com/1",
            source_name="TC",
            source=ArticleSource.TECHCRUNCH,
            raw_title="OpenAI Launches GPT-5",
        )
        article2 = Article(
            source_url="https://example.com/2",
            source_name="TV",
            source=ArticleSource.THE_VERGE,
            raw_title="Google DeepMind Achieves Quantum Breakthrough",
        )
        p1 = process_article(article1)
        p2 = process_article(article2)
        assert p1.summary_zh != p2.summary_zh
