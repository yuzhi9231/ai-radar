"""AI processing module for AI Radar.

Processes articles through Ollama (local) or uses mock mode for testing.
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Optional

import httpx

from .models import Article, ProcessedArticle

OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://ollama:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen3.6-35b-a3b-ud-q4_k_m")
OLLAMA_TIMEOUT = int(os.environ.get("OLLAMA_TIMEOUT", "120"))
USE_MOCK_AI = os.environ.get("USE_MOCK_AI", "false").lower() == "true"

CATEGORIES = [
    "大模型/API", "AI Coding/Agent", "AI 产品/工具",
    "开源项目", "论文/研究", "行业/公司/政策", "general",
]


SYSTEM_PROMPT = """你是一个专业的 AI 科技新闻分析师。请根据提供的新闻内容，生成中文分析结果。

请按以下 JSON 格式输出，不要输出其他内容：
{
  "headline_zh": "中文标题（15-30字）",
  "summary_zh": "中文摘要（80-150字）",
  "why_it_matters_zh": "为什么重要（50-100字）",
  "category": "分类（从以下选项中选择：大模型/API, AI Coding/Agent, AI 产品/工具, 开源项目, 论文/研究, 行业/公司/政策）",
  "tags": ["关键词1", "关键词2", "关键词3"],
  "importance_score": 75,
  "source_confidence": 0.9,
  "related_entities": ["实体1", "实体2"]
}

注意事项：
- 标题要简洁有力，抓住核心
- 摘要要包含关键信息，80-150字
- 评分基于对 AI 行业的影响程度（0-100）
- 所有字段必须填写，不要省略任何字段
- 如果信息不足，使用合理推断并降低 confidence"""


def _build_user_content(article: Article) -> str:
    """Build the user prompt content from an article."""
    content = f"标题：{article.raw_title}\n"
    if article.raw_description:
        content += f"描述：{article.raw_description}\n"
    content += f"来源：{article.source_name}\n"
    content += f"链接：{article.source_url}"
    return content


def _call_ollama(article: Article) -> Optional[dict]:
    """Call Ollama API to process a single article."""
    url = f"{OLLAMA_BASE_URL}/api/generate"
    user_content = _build_user_content(article)

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": SYSTEM_PROMPT,
        "system": "你只输出 JSON，不要输出任何其他内容。",
        "stream": False,
        "options": {
            "temperature": 0.3,
            "num_predict": 512,
        },
    }

    try:
        with httpx.Client(timeout=OLLAMA_TIMEOUT) as client:
            resp = client.post(url, json=payload)
            resp.raise_for_status()
            result = resp.json()
            response_text = result.get("response", "")
    except Exception:
        return None

    # Extract JSON from response (model may include markdown formatting)
    json_str = _extract_json(response_text)
    if not json_str:
        return None

    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        return None


def _extract_json(text: str) -> Optional[str]:
    """Extract JSON object from text that may contain markdown code blocks."""
    # Try to find JSON between ```json and ```
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start:end + 1]
    return None


def process_article_mock(article: Article) -> ProcessedArticle:
    """Mock AI processing - generates realistic test data without Ollama."""
    importance = min(100, max(10, len(article.raw_title) * 2 + len(article.raw_description) // 10))
    categories = ["general", "product", "research", "business", "engineering"]
    category = categories[hash(article.id) % len(categories)]

    return ProcessedArticle(
        article_id=article.id,
        headline_zh=f"[AI Radar] {article.raw_title[:40]}",
        summary_zh=f"来自 {article.source_name} 的报道：{article.raw_title}。{article.raw_description[:100]}...",
        why_it_matters_zh=f"该事件可能对 AI 领域产生重要影响，值得持续关注。",
        category=category,
        tags=[article.source.value, "AI"],
        importance_score=importance,
        source_confidence=0.85,
        related_entities=[article.source_name],
        generation_status="success",
    )


def process_article(article: Article) -> ProcessedArticle:
    """Process a single article through AI."""
    if USE_MOCK_AI:
        return process_article_mock(article)

    result = _call_ollama(article)

    if result is None:
        return ProcessedArticle(
            article_id=article.id,
            headline_zh=article.raw_title,
            summary_zh=article.raw_description or "摘要生成失败，请稍后重试。",
            generation_status="failed",
        )

    # Validate required fields
    required = ["headline_zh", "summary_zh", "category", "importance_score"]
    for field in required:
        if field not in result:
            result[field] = "" if field != "importance_score" else 0

    # Normalize importance_score
    score = result.get("importance_score", 0)
    try:
        score = max(0, min(100, int(score)))
    except (ValueError, TypeError):
        score = 50

    return ProcessedArticle(
        article_id=article.id,
        headline_zh=result.get("headline_zh", article.raw_title),
        summary_zh=result.get("summary_zh", ""),
        why_it_matters_zh=result.get("why_it_matters_zh", ""),
        category=result.get("category", "general"),
        tags=result.get("tags", []),
        importance_score=score,
        source_confidence=result.get("source_confidence", 0.5),
        related_entities=result.get("related_entities", []),
        generation_status="success" if result else "failed",
    )


def process_articles(articles: list[Article]) -> list[ProcessedArticle]:
    """Process a batch of articles. Returns list of processed articles."""
    results = []
    for article in articles:
        processed = process_article(article)
        results.append(processed)
    return results
