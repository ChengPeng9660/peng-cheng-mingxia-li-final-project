from __future__ import annotations

import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from polymarket_ai_business.models import MarketEnrichment, MarketRecord


CATEGORY_RULES: dict[str, dict[str, float]] = {
    "Business / Finance": {
        "stock": 1.5,
        "share": 1.0,
        "shares": 1.0,
        "market cap": 2.5,
        "earnings": 2.0,
        "revenue": 2.0,
        "guidance": 1.5,
        "ipo": 2.0,
        "merger": 2.0,
        "acquisition": 2.0,
        "buyback": 1.5,
        "deliveries": 1.5,
        "etf": 1.0,
        "bankruptcy": 2.0,
        "credit": 1.5,
        "bond": 1.0,
        "bitcoin": 1.0,
        "ethereum": 1.0,
        "nvidia": 1.5,
        "apple": 1.5,
        "microsoft": 1.5,
        "tesla": 1.5,
        "google": 1.0,
    },
    "AI / Technology": {
        "ai": 1.5,
        "openai": 2.5,
        "gpt": 2.5,
        "model": 1.0,
        "semiconductor": 2.0,
        "chip": 1.5,
        "chips": 1.5,
        "gpu": 1.5,
        "datacenter": 1.5,
        "cloud": 1.0,
        "nvidia": 2.0,
        "microsoft": 1.0,
        "google": 1.0,
        "anthropic": 2.0,
        "robotaxi": 1.0,
        "tesla": 1.0,
        "software": 1.0,
    },
    "Macro / Regulation": {
        "fed": 2.5,
        "rate cut": 2.5,
        "rates": 1.0,
        "inflation": 2.0,
        "cpi": 2.0,
        "recession": 2.0,
        "tariff": 2.0,
        "doj": 2.0,
        "ftc": 2.0,
        "sec": 1.5,
        "regulation": 2.0,
        "regulatory": 1.5,
        "export control": 2.5,
        "export controls": 2.5,
        "ban": 1.0,
        "fine": 1.0,
        "antitrust": 2.5,
        "divestiture": 2.0,
        "eu": 1.0,
    },
}

NEGATIVE_RULES = {
    "election": 2.5,
    "president": 2.0,
    "world series": 3.0,
    "nba": 2.5,
    "soccer": 2.5,
    "oscar": 3.0,
    "grammy": 3.0,
    "weather": 2.0,
    "hurricane": 2.0,
    "celebrity": 2.0,
}


def keyword_in_text(keyword: str, text: str) -> bool:
    pattern = r"\b" + re.escape(keyword.lower()) + r"\b"
    return re.search(pattern, text) is not None


def format_percent(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value * 100:.1f}%"


def format_percentage_point_move(value: float | None) -> str:
    if value is None:
        return "n/a"
    sign = "+" if value >= 0 else ""
    return f"{sign}{value * 100:.1f}pp"


class HeuristicEnricher:
    provider_name = "heuristic"

    def enrich(self, market: MarketRecord) -> MarketEnrichment:
        text = " ".join(
            part
            for part in [
                market.question,
                market.description,
                market.event_title,
                market.event_description,
                market.category_hint,
                " ".join(market.tags),
            ]
            if part
        ).lower()

        scores: dict[str, float] = defaultdict(float)
        matches: dict[str, list[str]] = defaultdict(list)
        for category, keywords in CATEGORY_RULES.items():
            for keyword, weight in keywords.items():
                if keyword_in_text(keyword, text):
                    scores[category] += weight
                    matches[category].append(keyword)

        negative_score = 0.0
        for keyword, weight in NEGATIVE_RULES.items():
            if keyword_in_text(keyword, text):
                negative_score += weight

        lower_hint = market.category_hint.lower()
        if any(token in lower_hint for token in ("business", "finance")):
            scores["Business / Finance"] += 1.5
        if any(token in lower_hint for token in ("tech", "ai")):
            scores["AI / Technology"] += 1.5
        if any(token in lower_hint for token in ("macro", "regulation", "politics", "economy")):
            scores["Macro / Regulation"] += 1.5

        ordered = sorted(scores.items(), key=lambda item: item[1], reverse=True)
        best_category, best_score = ordered[0] if ordered else ("Not Relevant", 0.0)
        relevant = bool(ordered and best_score >= 2.0 and best_score >= negative_score)
        if not relevant:
            best_category = "Not Relevant"

        secondaries = [category for category, score in ordered[1:] if score >= 2.0][:2]
        matched_keywords = matches.get(best_category, [])[:6]
        relevance_score = min(0.99, best_score / 8.0) if relevant else max(0.05, 0.25 - negative_score / 20.0)
        rationale = self._build_rationale(market, best_category, matched_keywords, relevant)
        summary = self._build_summary(market, best_category, matched_keywords, relevant)
        return MarketEnrichment(
            primary_category=best_category,
            secondary_categories=secondaries,
            relevant=relevant,
            relevance_score=round(relevance_score, 3),
            matched_keywords=matched_keywords,
            rationale=rationale,
            summary=summary,
            provider=self.provider_name,
        )

    def _build_rationale(
        self,
        market: MarketRecord,
        category: str,
        matched_keywords: list[str],
        relevant: bool,
    ) -> str:
        if not relevant:
            return "The market does not show enough finance, technology, or macro-policy signals to count as business-relevant."
        keyword_text = ", ".join(matched_keywords) if matched_keywords else "domain cues"
        if category == "Business / Finance":
            return f"Marked as business-relevant because it references company, asset-price, or corporate-performance signals such as {keyword_text}."
        if category == "AI / Technology":
            return f"Marked as business-relevant because it tracks AI or technology developments with likely implications for capex, competition, or platform strategy, including {keyword_text}."
        return f"Marked as business-relevant because it involves macroeconomic or regulatory catalysts such as {keyword_text}, which can change firm-level expectations."

    def _build_summary(
        self,
        market: MarketRecord,
        category: str,
        matched_keywords: list[str],
        relevant: bool,
    ) -> str:
        probability = format_percent(market.focus_probability)
        focus_outcome = market.focus_outcome_label or "the first listed outcome"
        one_day = format_percentage_point_move(market.one_day_price_change)
        one_week = format_percentage_point_move(market.one_week_price_change)
        if not relevant:
            return (
                f"{market.question} is currently treated as not directly useful for the business-research dashboard. "
                f"It implies {probability} for {focus_outcome}, but the market is outside the target business taxonomy."
            )

        reason = {
            "Business / Finance": "firm value, investor sentiment, or operating performance",
            "AI / Technology": "technology adoption, AI competition, or semiconductor demand",
            "Macro / Regulation": "policy, inflation, or regulatory risk for firms and investors",
        }.get(category, "business expectations")
        clue_text = ", ".join(matched_keywords[:3]) if matched_keywords else "business-related signals"
        return (
            f"{market.question} is classified as {category}. The market implies {probability} for {focus_outcome}, "
            f"with moves of {one_day} over 1 day and {one_week} over 1 week. "
            f"It matters for business research because it captures {reason}; matched cues include {clue_text}."
        )


class OpenAIEnricher:
    provider_name = "openai"
    endpoint = "https://api.openai.com/v1/responses"
    schema = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "primary_category": {
                "type": "string",
                "enum": ["Business / Finance", "AI / Technology", "Macro / Regulation", "Not Relevant"],
            },
            "secondary_categories": {
                "type": "array",
                "items": {
                    "type": "string",
                    "enum": ["Business / Finance", "AI / Technology", "Macro / Regulation"],
                },
            },
            "relevant": {"type": "boolean"},
            "relevance_score": {"type": "number"},
            "matched_keywords": {"type": "array", "items": {"type": "string"}},
            "rationale": {"type": "string"},
            "summary": {"type": "string"},
        },
        "required": [
            "primary_category",
            "secondary_categories",
            "relevant",
            "relevance_score",
            "matched_keywords",
            "rationale",
            "summary",
        ],
    }

    def __init__(
        self,
        api_key: str,
        model: str,
        fallback: HeuristicEnricher | None = None,
        timeout: int = 45,
        cache_path: Path | None = None,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.fallback = fallback or HeuristicEnricher()
        self.cache_path = cache_path
        self.cache = self._load_cache()

    def enrich(self, market: MarketRecord) -> MarketEnrichment:
        heuristic = self.fallback.enrich(market)
        cache_key = self._cache_key(market)
        cached = self.cache.get(cache_key)
        if isinstance(cached, dict):
            parsed = self._coerce_payload(cached)
            if parsed:
                parsed.provider = f"{self.provider_name}-cache"
                return parsed
        if not self.api_key:
            return heuristic

        payload = self._request_enrichment(market, heuristic)
        parsed = self._coerce_payload(payload)
        if not parsed:
            return heuristic
        self.cache[cache_key] = {
            "primary_category": parsed.primary_category,
            "secondary_categories": parsed.secondary_categories,
            "relevant": parsed.relevant,
            "relevance_score": parsed.relevance_score,
            "matched_keywords": parsed.matched_keywords,
            "rationale": parsed.rationale,
            "summary": parsed.summary,
        }
        self._write_cache()
        return parsed

    def _request_enrichment(self, market: MarketRecord, heuristic: MarketEnrichment) -> dict[str, Any] | None:
        prompt = self._build_prompt(market, heuristic)
        request = Request(
            self.endpoint,
            data=json.dumps(
                {
                    "model": self.model,
                    "input": [
                        {
                            "role": "system",
                            "content": (
                                "You are labeling Polymarket prediction markets for business research. "
                                "Return only the requested JSON schema."
                            ),
                        },
                        {"role": "user", "content": prompt},
                    ],
                    "text": {
                        "format": {
                            "type": "json_schema",
                            "name": "market_enrichment",
                            "schema": self.schema,
                            "strict": True,
                        }
                    },
                }
            ).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError):
            return None

        text = self._extract_response_text(payload)
        if text:
            parsed = self._extract_json(text)
            if parsed:
                return parsed

        if isinstance(payload.get("output_parsed"), dict):
            return payload["output_parsed"]
        return None

    def _build_prompt(self, market: MarketRecord, heuristic: MarketEnrichment) -> str:
        return (
            "You are helping with a business research project about Polymarket.\n"
            "Allowed categories: Business / Finance, AI / Technology, Macro / Regulation, Not Relevant.\n"
            "Use the market as a forward-looking business research signal, not as a trading recommendation.\n"
            "Keep the rationale to one sentence and the summary to no more than two sentences.\n\n"
            f"Question: {market.question}\n"
            f"Description: {market.description}\n"
            f"Event title: {market.event_title}\n"
            f"Category hint: {market.category_hint}\n"
            f"Tags: {', '.join(market.tags)}\n"
            f"Focus outcome: {market.focus_outcome_label}\n"
            f"Focus probability: {market.focus_probability}\n"
            f"1-day change: {market.one_day_price_change}\n"
            f"1-week change: {market.one_week_price_change}\n"
            f"Heuristic baseline: {json.dumps(heuristic.__dict__, ensure_ascii=True)}\n"
        )

    def _extract_response_text(self, payload: dict[str, Any]) -> str:
        if isinstance(payload.get("output_text"), str) and payload["output_text"].strip():
            return payload["output_text"]
        pieces: list[str] = []
        for item in payload.get("output") or []:
            if not isinstance(item, dict):
                continue
            for content in item.get("content") or []:
                if not isinstance(content, dict):
                    continue
                if content.get("type") in {"output_text", "text"} and content.get("text"):
                    pieces.append(str(content["text"]))
        return "\n".join(pieces).strip()

    def _extract_json(self, text: str) -> dict[str, Any] | None:
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return None
        try:
            parsed = json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            return None
        return parsed if isinstance(parsed, dict) else None

    def _coerce_payload(self, parsed: dict[str, Any] | None) -> MarketEnrichment | None:
        if not isinstance(parsed, dict):
            return None
        try:
            return MarketEnrichment(
                primary_category=str(parsed.get("primary_category") or "Not Relevant"),
                secondary_categories=[str(item) for item in parsed.get("secondary_categories") or []][:2],
                relevant=bool(parsed.get("relevant")),
                relevance_score=max(0.0, min(1.0, float(parsed.get("relevance_score", 0.0)))),
                matched_keywords=[str(item) for item in parsed.get("matched_keywords") or []][:6],
                rationale=str(parsed.get("rationale") or "").strip(),
                summary=str(parsed.get("summary") or "").strip(),
                provider=self.provider_name,
            )
        except (TypeError, ValueError):
            return None

    def _cache_key(self, market: MarketRecord) -> str:
        payload = json.dumps(
            {
                "question": market.question,
                "description": market.description,
                "event_title": market.event_title,
                "event_description": market.event_description,
                "category_hint": market.category_hint,
                "tags": market.tags,
            },
            sort_keys=True,
            ensure_ascii=True,
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def _load_cache(self) -> dict[str, Any]:
        if not self.cache_path or not self.cache_path.exists():
            return {}
        try:
            payload = json.loads(self.cache_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}
        return payload if isinstance(payload, dict) else {}

    def _write_cache(self) -> None:
        if not self.cache_path:
            return
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        self.cache_path.write_text(json.dumps(self.cache, indent=2, ensure_ascii=False), encoding="utf-8")


def build_enricher(
    provider: str,
    api_key: str | None = None,
    model: str = "gpt-5-mini",
    cache_path: Path | None = None,
) -> HeuristicEnricher | OpenAIEnricher:
    if provider == "openai":
        return OpenAIEnricher(api_key=api_key or "", model=model, cache_path=cache_path)
    return HeuristicEnricher()
