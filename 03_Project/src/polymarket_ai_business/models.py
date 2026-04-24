from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def parse_float(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return float(value)
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return None
        try:
            return float(stripped)
        except ValueError:
            return None
    return None


def first_non_none(*values: Any) -> Any:
    for value in values:
        if value is not None:
            return value
    return None


def parse_string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return []
        if stripped.startswith("["):
            try:
                parsed = json.loads(stripped)
                if isinstance(parsed, list):
                    return [str(item) for item in parsed]
            except json.JSONDecodeError:
                return [stripped]
        return [stripped]
    return [str(value)]


def parse_float_list(value: Any) -> list[float]:
    return [item for item in (parse_float(raw) for raw in parse_string_list(value)) if item is not None]


def coerce_iso_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        if value.endswith("Z"):
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(slots=True)
class MarketRecord:
    market_id: str
    question: str
    description: str
    slug: str
    url: str
    outcomes: list[str]
    outcome_prices: list[float]
    focus_outcome_label: str | None
    focus_probability: float | None
    last_trade_price: float | None
    one_day_price_change: float | None
    one_week_price_change: float | None
    volume_24h: float | None
    volume_total: float | None
    liquidity: float | None
    category_hint: str
    tags: list[str]
    event_title: str
    event_description: str
    active: bool
    closed: bool
    archived: bool
    end_date: str | None
    fetched_at: str
    raw: dict[str, Any] = field(repr=False)

    @classmethod
    def from_api(cls, raw: dict[str, Any], fetched_at: str) -> "MarketRecord":
        outcomes = parse_string_list(raw.get("outcomes"))
        outcome_prices = parse_float_list(raw.get("outcomePrices"))
        focus_outcome_label, focus_probability = cls._focus_outcome(outcomes, outcome_prices)
        tags = []
        for tag in raw.get("tags") or []:
            if isinstance(tag, dict):
                label = tag.get("label") or tag.get("slug") or tag.get("name")
                if label:
                    tags.append(str(label))
            elif tag:
                tags.append(str(tag))
        events = raw.get("events") or []
        first_event = events[0] if events and isinstance(events[0], dict) else {}
        slug = str(raw.get("slug") or raw.get("market_slug") or raw.get("id") or "")
        url = str(raw.get("url") or "")
        if not url and slug:
            url = f"https://polymarket.com/event/{slug}"
        return cls(
            market_id=str(raw.get("id") or slug or ""),
            question=str(raw.get("question") or raw.get("title") or ""),
            description=str(raw.get("description") or ""),
            slug=slug,
            url=url,
            outcomes=outcomes,
            outcome_prices=outcome_prices,
            focus_outcome_label=focus_outcome_label,
            focus_probability=focus_probability,
            last_trade_price=first_non_none(
                parse_float(raw.get("lastTradePrice")),
                parse_float(raw.get("last_trade_price")),
            ),
            one_day_price_change=first_non_none(
                parse_float(raw.get("oneDayPriceChange")),
                parse_float(raw.get("one_day_price_change")),
            ),
            one_week_price_change=first_non_none(
                parse_float(raw.get("oneWeekPriceChange")),
                parse_float(raw.get("one_week_price_change")),
            ),
            volume_24h=first_non_none(
                parse_float(raw.get("volume24hr")),
                parse_float(raw.get("volume_24h")),
            ),
            volume_total=first_non_none(
                parse_float(raw.get("volume")),
                parse_float(raw.get("volumeNum")),
                parse_float(raw.get("volume_total")),
            ),
            liquidity=first_non_none(
                parse_float(raw.get("liquidity")),
                parse_float(raw.get("liquidityNum")),
            ),
            category_hint=str(raw.get("category") or first_event.get("category") or ""),
            tags=tags,
            event_title=str(first_event.get("title") or ""),
            event_description=str(first_event.get("description") or ""),
            active=bool(raw.get("active")),
            closed=bool(raw.get("closed")),
            archived=bool(raw.get("archived")),
            end_date=str(raw.get("endDate") or raw.get("end_date") or "") or None,
            fetched_at=fetched_at,
            raw=raw,
        )

    @staticmethod
    def _focus_outcome(outcomes: list[str], prices: list[float]) -> tuple[str | None, float | None]:
        if not outcomes or not prices:
            return None, None
        lower = [outcome.lower() for outcome in outcomes]
        if "yes" in lower:
            index = lower.index("yes")
            if index < len(prices):
                return outcomes[index], prices[index]
        return outcomes[0], prices[0] if prices else None

    def is_binary_yes_no(self) -> bool:
        lower = [outcome.lower() for outcome in self.outcomes]
        return len(lower) == 2 and "yes" in lower and "no" in lower

    def resolved_yes_outcome(self) -> int | None:
        if not self.closed or not self.is_binary_yes_no() or len(self.outcome_prices) != 2:
            return None
        yes_index = [outcome.lower() for outcome in self.outcomes].index("yes")
        yes_price = self.outcome_prices[yes_index]
        no_price = self.outcome_prices[1 - yes_index]
        if yes_price is None or no_price is None:
            return None
        if yes_price >= 0.97:
            return 1
        if no_price >= 0.97:
            return 0
        return None

    def time_to_resolution_days(self, reference: datetime | None = None) -> float | None:
        if not self.end_date:
            return None
        target = coerce_iso_datetime(self.end_date)
        if not target:
            return None
        current = reference or now_utc()
        delta = target - current
        return delta.total_seconds() / 86400.0


@dataclass(slots=True)
class MarketEnrichment:
    primary_category: str
    secondary_categories: list[str]
    relevant: bool
    relevance_score: float
    matched_keywords: list[str]
    rationale: str
    summary: str
    provider: str


@dataclass(slots=True)
class AnalyzedMarket:
    market: MarketRecord
    enrichment: MarketEnrichment

    def to_row(self) -> dict[str, Any]:
        resolved_yes = self.market.resolved_yes_outcome()
        return {
            "market_id": self.market.market_id,
            "question": self.market.question,
            "event_title": self.market.event_title,
            "primary_category": self.enrichment.primary_category,
            "secondary_categories": ", ".join(self.enrichment.secondary_categories),
            "relevant": self.enrichment.relevant,
            "relevance_score": round(self.enrichment.relevance_score, 3),
            "focus_outcome": self.market.focus_outcome_label or "",
            "focus_probability": self.market.focus_probability,
            "last_trade_price": self.market.last_trade_price,
            "one_day_price_change": self.market.one_day_price_change,
            "one_week_price_change": self.market.one_week_price_change,
            "volume_24h": self.market.volume_24h,
            "volume_total": self.market.volume_total,
            "liquidity": self.market.liquidity,
            "active": self.market.active,
            "closed": self.market.closed,
            "end_date": self.market.end_date,
            "resolved_yes_outcome": resolved_yes,
            "tags": ", ".join(self.market.tags),
            "summary": self.enrichment.summary,
            "rationale": self.enrichment.rationale,
            "provider": self.enrichment.provider,
            "url": self.market.url,
        }
