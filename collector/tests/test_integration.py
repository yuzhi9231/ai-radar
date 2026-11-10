"""Integration tests for AI Radar collector pipeline.

Tests the full data flow: collection → dedup → storage → AI processing.
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

# Ensure collector package is importable
sys.path.insert(0, str(Path(__file__).parent))

os.environ["USE_MOCK_AI"] = "true"

import pytest

from collector.ai import process_article
from collector.collectors import COLLECTORS
from collector.db import (
    create_pipeline_run,
    get_all_articles,
    get_article_by_id,
    get_connection,
    get_latest_pipeline_run,
    get_sources,
    get_stats,
    init_db,
    upsert_article,
    upsert_processed_article,
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

    def test_hn_api_url_queries_ai_stories_by_date(self):
        """Algolia has no 'ai' tag, so a bare tags=ai filter returns 0 hits.
        The collector must query AI story posts by date instead (Issue #7 intent)."""
        from unittest.mock import patch
        from urllib.parse import urlencode

        import httpx

        from collector.collectors import collect_hackernews

        with patch.object(httpx.Client, "get") as mock_get:
            mock_get.return_value.json.return_value = {"hits": []}
            collect_hackernews()
            call_args = mock_get.call_args
            assert call_args is not None
            url = call_args[0][0]
            params = call_args[1].get("params", {})
            full = f"{url}?{urlencode(params)}"
            assert "search_by_date" in url, f"HN API should sort by date, got: {full}"
            assert "query=AI" in full, f"HN API should query AI, got: {full}"
            assert "tags=story" in full, f"HN API should filter stories, got: {full}"

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

    def test_url_normalization_rewrites_dash_date_segment(self):
        """A dash-form date segment 404s on TechCrunch; the collector stores the
        slash form the site actually serves."""
        from collector.urls import looks_uncanonical, normalize_article_url

        dash = "https://techcrunch.com/2026-10-19/some-slug/"
        fixed = "https://techcrunch.com/2026/10/19/some-slug/"
        assert looks_uncanonical(dash)
        assert normalize_article_url(dash) == fixed
        assert not looks_uncanonical(fixed)
        # paths whose first segment is not a date are left alone
        untouched = "https://www.theverge.com/podcast/123456/x/"
        assert normalize_article_url(untouched) == untouched

    def test_collect_all_records_source_errors(self):
        """A failed source must not look like a source that had no articles."""
        from unittest.mock import patch

        from collector.collectors import COLLECTORS, collect_all

        def failing() -> list[Article]:
            raise RuntimeError("feed down")

        def empty() -> list[Article]:
            return []

        replacements = {
            ArticleSource.TECHCRUNCH: failing,
            ArticleSource.THE_VERGE: empty,
            ArticleSource.HN: empty,
        }
        with patch.dict(COLLECTORS, replacements, clear=True):
            errors: dict[str, str] = {}
            results = collect_all(errors)

        assert results == {"techcrunch": [], "theverge": [], "hn": []}
        assert errors == {"techcrunch": "feed down"}

    def test_hn_skips_hits_without_external_url(self):
        """Text and Ask posts have no external link, so they cannot be stored
        or deduped by URL and are dropped."""
        from unittest.mock import patch

        import httpx

        from collector.collectors import collect_hackernews

        hits = [
            {
                "url": "https://example.com/story",
                "title": "Story with a link",
                "created_at": "2026-11-10T09:00:00Z",
            },
            {"url": "", "title": "Text post", "created_at": "2026-11-10T09:00:00Z"},
        ]
        with patch.object(httpx.Client, "get") as mock_get:
            mock_get.return_value.json.return_value = {"hits": hits}
            articles = collect_hackernews()

        assert len(articles) == 1
        assert articles[0].source_url == "https://example.com/story"
        # Algolia timestamps are ISO-8601 strings, not epochs
        assert articles[0].published_at is not None
        assert articles[0].published_at.tzinfo is not None

    def test_hn_unparsable_timestamp_stays_none(self):
        """A malformed timestamp must not crash the collector."""
        from unittest.mock import patch

        import httpx

        from collector.collectors import collect_hackernews

        hits = [
            {"url": "https://example.com/story", "title": "Story", "created_at": "x"}
        ]
        with patch.object(httpx.Client, "get") as mock_get:
            mock_get.return_value.json.return_value = {"hits": hits}
            articles = collect_hackernews()

        assert len(articles) == 1
        assert articles[0].published_at is None


class TestDedup:
    """Test deduplication logic."""

    def test_url_exact_dedup(self):
        """Articles with the same URL should be deduplicated."""
        url = "https://techcrunch.com/2024/01/01/test-article"
        article1 = Article(
            source_url=url,
            source_name="TechCrunch",
            source=ArticleSource.TECHCRUNCH,
            raw_title="Test 1",
        )
        article2 = Article(
            source_url=url,
            source_name="TechCrunch",
            source=ArticleSource.TECHCRUNCH,
            raw_title="Test 1 - Duplicate",
        )
        existing = [article1]
        new, dup_count = deduplicate([article2], existing)
        assert len(new) == 0
        assert dup_count == 1

    def test_title_similarity_dedup(self):
        """Articles with highly similar titles should be deduplicated."""
        base_title = "OpenAI Releases GPT-5 with Revolutionary Multimodal Capabilities"
        article1 = Article(
            source_url="https://example.com/1",
            source_name="TC",
            source=ArticleSource.TECHCRUNCH,
            raw_title=base_title,
        )
        article2 = Article(
            source_url="https://example.com/2",
            source_name="TV",
            source=ArticleSource.THE_VERGE,
            raw_title=base_title + " and More",
        )
        existing = [article1]
        new, dup_count = deduplicate([article2], existing)
        assert len(new) == 0
        assert dup_count == 1

    def test_different_articles_not_deduped(self):
        """Articles with different URLs and titles should NOT be deduplicated."""
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
            raw_title="Google Announces Gemini Pro Update",
        )
        existing = [article1]
        new, dup_count = deduplicate([article2], existing)
        assert len(new) == 1
        assert dup_count == 0

    def test_dedup_with_existing_articles(self):
        """Dedup should filter new articles against existing ones."""
        existing = [
            Article(
                source_url="https://example.com/existing",
                source_name="TC",
                source=ArticleSource.TECHCRUNCH,
                raw_title="Existing Article",
            ),
        ]
        new_articles = [
            Article(
                source_url="https://example.com/existing",
                source_name="TC",
                source=ArticleSource.TECHCRUNCH,
                raw_title="Existing Article",
            ),
            Article(
                source_url="https://example.com/new",
                source_name="TV",
                source=ArticleSource.THE_VERGE,
                raw_title="Brand New Article",
            ),
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

    def test_mock_ai_is_not_the_default(self):
        """Mock must be an explicit choice, not the default path (Issue #23)."""
        import importlib

        import collector.ai as ai_mod

        saved = os.environ.copy()
        os.environ.clear()
        try:
            importlib.reload(ai_mod)
            assert ai_mod.USE_MOCK_AI is False
        finally:
            os.environ.update(saved)
            importlib.reload(ai_mod)

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
        assert processed.category in (
            "general",
            "product",
            "research",
            "business",
            "engineering",
        )

    def test_ai_failure_records_reason(self, temp_db: Path):
        """An unreachable model must be stored as a failure with the reason, not as
        a success with placeholder text."""
        article = Article(
            source_url="https://example.com/test-failure",
            source_name="TechCrunch",
            source=ArticleSource.TECHCRUNCH,
            raw_title="Model Server Down",
            raw_description="The inference service refused the connection.",
        )
        upsert_article(article)

        with (
            patch("collector.ai.USE_MOCK_AI", False),
            patch(
                "collector.ai._call_model",
                return_value=(None, "Ollama request failed: connect refused"),
            ),
        ):
            processed = process_article(article)

        assert processed.generation_status == "failed"
        assert "connect refused" in (processed.error or "")

        upsert_processed_article(processed)
        stored = get_article_by_id(article.id)
        assert stored is not None and stored.processed is not None
        assert stored.processed.generation_status == "failed"
        assert "connect refused" in (stored.processed.error or "")

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
                if article.processed:
                    assert article.processed.generation_status == "success"

    def test_pipeline_records_ai_failures(self, temp_db: Path):
        """A run that stored articles but analysed none is partial_failure, and the
        counts land on the run row instead of the run being left open."""
        article = Article(
            source_url="https://techcrunch.com/test-fail",
            source_name="TechCrunch AI",
            source=ArticleSource.TECHCRUNCH,
            raw_title="Article stored without analysis",
            raw_description="The model server was unreachable.",
        )

        with patch("collector.run.collect_all") as mock_collect:
            mock_collect.return_value = {"techcrunch": [article]}
            with (
                patch("collector.ai.USE_MOCK_AI", False),
                patch("collector.ai._call_model", return_value=(None, "unreachable")),
            ):
                run = run_pipeline()

        assert run.status == "partial_failure"
        assert run.completed_at is not None
        assert run.articles_new == 1
        assert run.articles_processed == 0
        assert run.articles_failed == 1

        stored = get_article_by_id(article.id)
        assert stored is not None and stored.processed is not None
        assert stored.processed.error == "unreachable"


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
            started_at=datetime.now(timezone.utc),
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


# --- Source Model Tests ---


class TestSource:
    """Test Source model and database operations."""

    def test_source_model_defaults(self):
        """Source model should have correct defaults."""
        from collector.models import Source

        source = Source(
            id="test_source",
            name="Test Source",
            feed_url="https://example.com/feed",
            feed_type="rss",
        )
        assert source.id == "test_source"
        assert source.name == "Test Source"
        assert source.feed_url == "https://example.com/feed"
        assert source.feed_type == "rss"
        assert source.enabled is True
        assert source.last_success is None
        assert source.last_error is None

    def test_source_model_disabled(self):
        """Source model should support disabled state."""
        from collector.models import Source

        source = Source(
            id="disabled_source",
            name="Disabled",
            feed_url="https://example.com/feed",
            feed_type="api",
            enabled=False,
        )
        assert source.enabled is False

    def test_upsert_source(self, temp_db: Path):
        """Test inserting and retrieving a source."""
        from collector.db import get_source_by_id, upsert_source
        from collector.models import Source

        source = Source(
            id="custom_source",
            name="Custom AI Source",
            feed_url="https://example.com/ai/feed",
            feed_type="rss",
        )
        upsert_source(source)

        fetched = get_source_by_id("custom_source")
        assert fetched is not None
        assert fetched.name == "Custom AI Source"
        assert fetched.feed_type == "rss"
        assert fetched.enabled is True

    def test_get_nonexistent_source(self, temp_db: Path):
        """Test retrieving a non-existent source."""
        from collector.db import get_source_by_id

        fetched = get_source_by_id("nonexistent")
        assert fetched is None


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
                    Article(
                        source_url="https://example.com/cli-test",
                        source_name="TC",
                        source=ArticleSource.TECHCRUNCH,
                        raw_title="CLI Test",
                    ),
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


# --- URL Normalization Tests ---


class TestUrls:
    """Test the URL helpers that fix dash-form date segments (Issue #20)."""

    def test_dash_date_segment_is_rewritten(self):
        """The stored form 404s; the site serves /YYYY/MM/DD/slug/."""
        from collector.urls import looks_uncanonical, normalize_article_url

        url = "https://www.theverge.com/2026-10-21/abc123/openai-launch"
        assert normalize_article_url(url) == (
            "https://www.theverge.com/2026/10/21/abc123/openai-launch"
        )
        assert looks_uncanonical(url) is True

    def test_query_and_fragment_are_preserved(self):
        from collector.urls import normalize_article_url

        url = "https://www.theverge.com/2026-10-21/abc/story?utm_source=x#comment"
        assert normalize_article_url(url) == (
            "https://www.theverge.com/2026/10/21/abc/story?utm_source=x#comment"
        )

    def test_already_canonical_url_is_unchanged(self):
        from collector.urls import looks_uncanonical, normalize_article_url

        url = "https://www.theverge.com/2026/10/21/abc123/openai-launch"
        assert normalize_article_url(url) == url
        assert looks_uncanonical(url) is False

    def test_non_date_first_segment_is_unchanged(self):
        """A path that does not start with a date must not be touched."""
        from collector.urls import looks_uncanonical, normalize_article_url

        url = "https://techcrunch.com/2026/10/21/openai-launch"
        assert normalize_article_url(url) == url
        assert looks_uncanonical(url) is False

        url = "https://example.com/reviews/openai"
        assert normalize_article_url(url) == url
        assert looks_uncanonical(url) is False


# --- Repair Tests ---


class TestRepair:
    """Test the one-off repair of rows written before the fixes (Issue #20)."""

    def _dash_article(self):
        article = Article(
            source_url="https://www.theverge.com/2026-10-21/abc123/alpha-runs-on-device",
            source_name="The Verge",
            source=ArticleSource.THE_VERGE,
            raw_title="Alpha runs on device",
        )
        upsert_article(article)
        return article

    def test_verified_url_is_rewritten(self, temp_db: Path):
        """A candidate confirmed by the live og:title is written to the DB."""
        from collector import repair
        from collector.urls import normalize_article_url

        article = self._dash_article()
        with patch.object(
            repair, "fetch_og_title", return_value="Alpha runs on device"
        ):
            report = repair.repair_urls()

        assert report["checked"] == 1
        assert report["fixed"] == 1
        stored = get_article_by_id(article.id)
        assert stored.source_url == normalize_article_url(article.source_url)

    def test_entities_in_stored_title_still_match(self, temp_db: Path):
        """Titles are compared after unescaping entities and collapsing spaces."""
        from collector import repair

        article = Article(
            source_url="https://www.theverge.com/2026-10-21/abc123/story",
            source_name="The Verge",
            source=ArticleSource.THE_VERGE,
            raw_title="OpenAI&#8217;s model,   now",
        )
        upsert_article(article)

        with patch.object(repair, "fetch_og_title", return_value="OpenAI’s model, now"):
            report = repair.repair_urls()

        assert report["fixed"] == 1

    def test_og_title_with_site_suffix_matches(self, temp_db: Path):
        """og:title carries the site suffix ("Title | TechCrunch"); raw_title does not."""
        from collector import repair
        from collector.urls import normalize_article_url

        article = self._dash_article()
        with patch.object(
            repair, "fetch_og_title", return_value="Alpha runs on device | TechCrunch"
        ):
            report = repair.repair_urls()

        assert report["fixed"] == 1
        stored = get_article_by_id(article.id)
        assert stored.source_url == normalize_article_url(article.source_url)

    def test_og_title_with_site_name_in_front_matches(self, temp_db: Path):
        """Some pages put the site first: "TechCrunch - Alpha runs on device"."""
        from collector import repair
        from collector.urls import normalize_article_url

        article = self._dash_article()
        with patch.object(
            repair, "fetch_og_title", return_value="TechCrunch - Alpha runs on device"
        ):
            report = repair.repair_urls()

        assert report["fixed"] == 1
        stored = get_article_by_id(article.id)
        assert stored.source_url == normalize_article_url(article.source_url)

    def test_unverified_row_is_left_alone(self, temp_db: Path):
        """A different og:title means the candidate is not the same article."""
        from collector import repair

        article = self._dash_article()
        with patch.object(repair, "fetch_og_title", return_value="A different article"):
            report = repair.repair_urls()

        assert report["unverified"] == 1
        assert report["fixed"] == 0
        stored = get_article_by_id(article.id)
        assert stored.source_url == article.source_url

    def test_unreachable_page_is_not_rewritten(self, temp_db: Path):
        """Verification failure must not guess a new URL."""
        from collector import repair

        article = self._dash_article()
        with patch.object(repair, "fetch_og_title", return_value=None):
            report = repair.repair_urls()

        assert report["unverified"] == 1
        stored = get_article_by_id(article.id)
        assert stored.source_url == article.source_url

    def test_dry_run_does_not_write(self, temp_db: Path):
        from collector import repair

        article = self._dash_article()
        with patch.object(
            repair, "fetch_og_title", return_value="Alpha runs on device"
        ):
            report = repair.repair_urls(dry_run=True)

        assert report["fixed"] == 1
        stored = get_article_by_id(article.id)
        assert stored.source_url == article.source_url

    def test_hn_feed_url_is_repaired(self, temp_db: Path):
        """The old tags=ai filter returns no hits, so the source row must be updated."""
        from collector import repair

        conn = get_connection()
        conn.execute(
            "UPDATE sources SET feed_url = ? WHERE id = 'hn'",
            ("https://hn.algolia.com/api/v1/search?tags=ai",),
        )
        conn.commit()

        assert repair.repair_hn_feed_url() is True
        from collector.db import get_source_by_id

        assert get_source_by_id("hn").feed_url == repair.HN_FEED_URL
        # A second run is a no-op
        assert repair.repair_hn_feed_url() is False

    def test_interrupted_runs_are_marked(self, temp_db: Path):
        """A 'running' row with no completion time is an interrupted run."""
        from collector import repair

        create_pipeline_run(PipelineRun(status="running"))
        assert repair.mark_interrupted_runs() == 1
        assert get_latest_pipeline_run().status == "interrupted"

    def test_completed_runs_are_not_touched(self, temp_db: Path):
        from collector import repair

        create_pipeline_run(
            PipelineRun(status="success", completed_at=datetime.now(timezone.utc))
        )
        assert repair.mark_interrupted_runs() == 0
        assert get_latest_pipeline_run().status == "success"


# --- Run Status Tests ---


class TestRunStatus:
    """Run status semantics (Issue #22)."""

    def test_all_duplicates_is_success(self, temp_db: Path):
        """Everything already stored is a normal outcome, not a failure."""
        article = Article(
            source_url="https://example.com/already-stored",
            source_name="Hacker News",
            source=ArticleSource.HN,
            raw_title="Already stored",
        )
        upsert_article(article)

        with patch("collector.run.collect_all", return_value={"hn": [article]}):
            run = run_pipeline()

        assert run.status == "success"
        assert run.articles_fetched == 1
        assert run.articles_new == 0

    def test_failed_only_when_every_source_errors(self, temp_db: Path):
        def fake_collect(errors: dict) -> dict:
            errors["hn"] = "feed down"
            return {"hn": []}

        with patch("collector.run.collect_all", side_effect=fake_collect):
            run = run_pipeline()

        assert run.status == "failed"
        assert run.completed_at is not None

    def test_partial_failure_when_one_source_errors(self, temp_db: Path):
        article = Article(
            source_url="https://example.com/from-hn",
            source_name="Hacker News",
            source=ArticleSource.HN,
            raw_title="Collected from HN",
        )

        def fake_collect(errors: dict) -> dict:
            errors["techcrunch"] = "feed down"
            return {"techcrunch": [], "hn": [article]}

        with patch("collector.run.collect_all", side_effect=fake_collect):
            run = run_pipeline()

        assert run.status == "partial_failure"
        assert run.source_results["techcrunch"]["status"] == "error"
        assert run.source_results["hn"]["status"] == "success"

    def test_interrupted_run_keeps_partial_counts(self, temp_db: Path):
        """A signal mid-run stores the counts collected so far as 'interrupted'."""
        import collector.run as run_mod

        articles = [
            Article(
                source_url="https://example.com/1",
                source_name="Hacker News",
                source=ArticleSource.HN,
                raw_title="First",
            ),
            Article(
                source_url="https://example.com/2",
                source_name="Hacker News",
                source=ArticleSource.HN,
                raw_title="Second",
            ),
        ]
        processed_ids = []

        def fake_process(article):
            processed_ids.append(article.id)
            # The first article is processed, then the run is interrupted
            run_mod._interrupted = True
            return ProcessedArticle(article_id=article.id, generation_status="success")

        with (
            patch("collector.run.collect_all", return_value={"hn": articles}),
            patch("collector.run.process_article", side_effect=fake_process),
        ):
            run = run_pipeline()

        assert run.status == "interrupted"
        assert run.articles_new == 2
        assert run.articles_processed == 1
        assert len(processed_ids) == 1
        assert get_latest_pipeline_run().status == "interrupted"

    def test_signal_handler_marks_the_run_interrupted(self):
        import signal

        import collector.run as run_mod

        run_mod._interrupted = False
        run_mod._handle_signal(signal.SIGINT, None)
        assert run_mod._interrupted is True
        run_mod._interrupted = False

    def test_pipeline_run_status_accepts_interrupted(self, temp_db: Path):
        """The status column stores whatever the run recorded."""
        create_pipeline_run(PipelineRun(status="interrupted"))
        assert get_latest_pipeline_run().status == "interrupted"


class TestReprocess:
    """Reprocessing must only touch articles that were never analysed (Issue #23)."""

    def test_failed_article_is_analysed_on_reprocess(self, temp_db: Path):
        from collector.run import reprocess_failed

        article = Article(
            source_url="https://example.com/failed-article",
            source_name="TechCrunch",
            source=ArticleSource.TECHCRUNCH,
            raw_title="OpenAI Releases A New Model",
        )
        upsert_article(article)
        upsert_processed_article(
            ProcessedArticle(
                article_id=article.id,
                generation_status="failed",
                error="Ollama request failed: timeout",
            )
        )

        report = reprocess_failed()
        assert report["candidates"] == 1
        assert report["processed"] == 1
        assert report["still_failed"] == 0

        stored = get_article_by_id(article.id)
        assert stored.processed.generation_status == "success"

    def test_good_results_are_not_overwritten(self, temp_db: Path):
        from collector.run import reprocess_failed

        article = Article(
            source_url="https://example.com/good-article",
            source_name="TechCrunch",
            source=ArticleSource.TECHCRUNCH,
            raw_title="Already Analysed Article",
        )
        upsert_article(article)
        upsert_processed_article(
            ProcessedArticle(
                article_id=article.id,
                headline_zh="已有标题",
                generation_status="success",
            )
        )

        report = reprocess_failed()
        assert report["candidates"] == 0

        stored = get_article_by_id(article.id)
        assert stored.processed.headline_zh == "已有标题"

    def test_article_without_a_processed_row_is_a_candidate(self, temp_db: Path):
        """An article stored without analysis is still recoverable."""
        from collector.run import reprocess_failed

        article = Article(
            source_url="https://example.com/unanalysed",
            source_name="Hacker News",
            source=ArticleSource.HN,
            raw_title="Show HN: A Code Reviewer",
        )
        upsert_article(article)

        report = reprocess_failed()
        assert report["candidates"] == 1
        assert report["processed"] == 1
        assert get_article_by_id(article.id).processed is not None
