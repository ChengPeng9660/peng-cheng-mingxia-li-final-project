from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

from polymarket_ai_business.client import JsonHttpClient
from polymarket_ai_business.models import AnalyzedMarket


STOP_TAGS = {
    "ai",
    "macro",
    "business",
    "technology",
    "regulation",
    "stocks",
    "stock",
    "trade",
    "crypto",
    "autos",
}

KNOWN_TERMS = [
    ("openai", "OpenAI"),
    ("gpt-5", "GPT-5"),
    ("gpt 5", "GPT-5"),
    ("nvidia", "Nvidia"),
    ("apple", "Apple"),
    ("tesla", "Tesla"),
    ("microsoft", "Microsoft"),
    ("google", "Google"),
    ("bitcoin etf", "Bitcoin ETF"),
    ("bitcoin", "Bitcoin"),
    ("fed", "Federal Reserve"),
    ("rate cut", "rate cut"),
    ("cpi", "CPI inflation"),
    ("inflation", "inflation"),
    ("ftc", "FTC"),
    ("doj", "DOJ"),
    ("eu", "European Union"),
    ("export control", "export controls"),
    ("chip", "AI chips"),
    ("deliveries", "vehicle deliveries"),
    ("market cap", "market capitalization"),
]


@dataclass(slots=True)
class NewsBundle:
    source: str
    query: str
    digest: str
    articles: list[dict[str, Any]]
    metadata: dict[str, Any]


class GDELTNewsClient:
    base_url = "https://api.gdeltproject.org/api/v2/doc/doc"

    def __init__(self, timeout: int = 12) -> None:
        self.http = JsonHttpClient(timeout=timeout)

    def search(self, query: str, max_records: int = 3, timespan: str = "7days") -> NewsBundle:
        params = {
            "query": query,
            "mode": "ArtList",
            "format": "json",
            "maxrecords": str(max_records),
            "sort": "DateDesc",
            "timespan": timespan,
        }
        url = f"{self.base_url}?{urlencode(params)}"
        payload = self.http.get_json(url)
        articles = payload.get("articles") or payload.get("artlist") or payload.get("results") or []
        normalized = []
        for article in articles[:max_records]:
            if not isinstance(article, dict):
                continue
            normalized.append(
                {
                    "title": article.get("title") or "Untitled article",
                    "url": article.get("url") or article.get("urlmobile") or "",
                    "source": article.get("domain") or article.get("sourcecountry") or "unknown",
                    "published_at": article.get("seendate") or article.get("date") or "",
                    "language": article.get("language") or "",
                }
            )
        digest = build_digest_from_articles(normalized)
        return NewsBundle(
            source="gdelt",
            query=query,
            digest=digest,
            articles=normalized,
            metadata={"article_count": len(normalized), "timespan": timespan},
        )


class FixtureNewsClient:
    def load(self, path: Path) -> dict[str, list[dict[str, Any]]]:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return payload.get("market_news") or {}


def build_market_query(analyzed_market: AnalyzedMarket) -> str:
    market = analyzed_market.market
    text = f"{market.question} {' '.join(market.tags)}".lower()
    terms: list[str] = []

    def add_term(candidate: str) -> None:
        lowered = candidate.lower()
        if lowered not in {existing.lower() for existing in terms}:
            terms.append(candidate)

    for raw, canonical in KNOWN_TERMS:
        if raw in text and canonical not in terms:
            add_term(canonical)
    for tag in market.tags:
        cleaned = tag.replace("-", " ").strip()
        if not cleaned or cleaned.lower() in STOP_TAGS:
            continue
        if cleaned.upper() in {"FTC", "DOJ", "CPI", "EU"}:
            candidate = cleaned.upper()
        elif cleaned.lower() == "etf":
            candidate = "ETF"
        else:
            candidate = cleaned.title()
        add_term(candidate)
    if not terms:
        candidates = re.findall(r"\b[A-Z][A-Za-z0-9.-]{2,}\b", market.question)
        for candidate in candidates:
            add_term(candidate)
    if not terms:
        short_question = re.sub(r"^Will |^Did |^Was ", "", market.question).rstrip("?")
        add_term(short_question[:60])
    query_terms = terms[:3]
    return "(" + " OR ".join(f'"{term}"' for term in query_terms) + ")"


def build_digest_from_articles(articles: list[dict[str, Any]]) -> str:
    if not articles:
        return "No linked headlines were found for this market in the current run."
    headlines = [article["title"] for article in articles[:2] if article.get("title")]
    if len(headlines) == 1:
        return f"Recent coverage is centered on: {headlines[0]}"
    return f"Recent coverage is centered on: {headlines[0]} Also notable: {headlines[1]}"


def attach_news_digest(
    analyzed_markets: list[AnalyzedMarket],
    *,
    news_source: str,
    news_limit_per_market: int,
    news_market_count: int,
    news_fixture_path: Path,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if news_source == "none":
        return [], {"source": "none", "selected_markets": 0}

    fixture_mapping = FixtureNewsClient().load(news_fixture_path)
    gdelt = GDELTNewsClient()
    selected_markets = _select_news_targets(analyzed_markets, news_market_count)
    digest_entries: list[dict[str, Any]] = []
    live_successes = 0
    fixture_hits = 0

    for item in selected_markets:
        query = build_market_query(item)
        bundle: NewsBundle | None = None

        if news_source in {"auto", "live"}:
            try:
                bundle = gdelt.search(query, max_records=news_limit_per_market)
                if bundle.articles:
                    live_successes += 1
            except Exception as exc:
                if news_source == "live":
                    bundle = NewsBundle(
                        source="live-unavailable",
                        query=query,
                        digest=f"Live news lookup failed: {exc}",
                        articles=[],
                        metadata={"error": str(exc)},
                    )

        if (bundle is None or not bundle.articles) and news_source in {"auto", "fixture", "live"}:
            fixture_articles = fixture_mapping.get(item.market.market_id, [])[:news_limit_per_market]
            if fixture_articles:
                fixture_hits += 1
                bundle = NewsBundle(
                    source="fixture",
                    query=query,
                    digest=build_digest_from_articles(fixture_articles),
                    articles=fixture_articles,
                    metadata={"article_count": len(fixture_articles), "synthetic": True},
                )

        if bundle is None:
            bundle = NewsBundle(
                source="unavailable",
                query=query,
                digest="No linked headlines were available for this market.",
                articles=[],
                metadata={"article_count": 0},
            )

        entry = {
            "market_id": item.market.market_id,
            "question": item.market.question,
            "category": item.enrichment.primary_category,
            "query": bundle.query,
            "source": bundle.source,
            "digest": bundle.digest,
            "articles": bundle.articles,
        }
        digest_entries.append(entry)

    metadata = {
        "source_mode": news_source,
        "selected_markets": len(selected_markets),
        "live_successes": live_successes,
        "fixture_hits": fixture_hits,
    }
    return digest_entries, metadata


def _select_news_targets(analyzed_markets: list[AnalyzedMarket], count: int) -> list[AnalyzedMarket]:
    relevant_active = [item for item in analyzed_markets if item.enrichment.relevant and not item.market.closed]
    ranked = sorted(
        relevant_active,
        key=lambda item: (
            abs(item.market.one_week_price_change or 0.0),
            abs(item.market.one_day_price_change or 0.0),
            item.enrichment.relevance_score,
        ),
        reverse=True,
    )
    return ranked[:count]
