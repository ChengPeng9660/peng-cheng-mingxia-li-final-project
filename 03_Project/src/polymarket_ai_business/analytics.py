from __future__ import annotations

import statistics
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

from polymarket_ai_business.models import AnalyzedMarket, MarketEnrichment, MarketRecord


def _safe_mean(values: list[float | None]) -> float | None:
    filtered = [value for value in values if value is not None]
    if not filtered:
        return None
    return statistics.mean(filtered)


def _round(value: float | None, digits: int = 4) -> float | None:
    return round(value, digits) if value is not None else None


@dataclass(slots=True)
class PipelineSummary:
    metadata: dict[str, Any]
    metrics: dict[str, Any]
    category_counts: list[dict[str, Any]]
    top_relevant_markets: list[dict[str, Any]]
    top_movers: list[dict[str, Any]]
    upcoming_events: list[dict[str, Any]]
    resolved_evaluation: dict[str, Any]
    case_studies: list[dict[str, Any]]
    research_takeaways: list[str]
    news_digest: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def analyze_markets(analyzed_markets: list[AnalyzedMarket], *, source: str, source_metadata: dict[str, Any]) -> PipelineSummary:
    relevant = [item for item in analyzed_markets if item.enrichment.relevant]
    active_relevant = [item for item in relevant if not item.market.closed]
    resolved_relevant = [item for item in relevant if item.market.closed]

    category_counter = Counter(item.enrichment.primary_category for item in relevant)
    category_counts = [
        {"category": category, "count": count}
        for category, count in sorted(category_counter.items(), key=lambda item: (-item[1], item[0]))
    ]

    top_relevant = sorted(
        active_relevant,
        key=lambda item: (
            item.enrichment.relevance_score,
            item.market.volume_24h or 0.0,
            abs(item.market.one_week_price_change or 0.0),
        ),
        reverse=True,
    )[:10]
    top_movers = sorted(
        active_relevant,
        key=lambda item: abs(item.market.one_week_price_change or item.market.one_day_price_change or 0.0),
        reverse=True,
    )[:8]
    upcoming = sorted(
        [item for item in active_relevant if item.market.time_to_resolution_days() is not None],
        key=lambda item: item.market.time_to_resolution_days() or 0.0,
    )[:8]

    resolved_eval = evaluate_resolved_markets(resolved_relevant)
    case_studies = build_case_studies(top_movers[:3])
    metrics = build_metrics(analyzed_markets, relevant, active_relevant, resolved_relevant, resolved_eval)
    takeaways = build_research_takeaways(metrics, category_counts, resolved_eval, case_studies)

    return PipelineSummary(
        metadata={
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "source": source,
            "source_metadata": source_metadata,
        },
        metrics=metrics,
        category_counts=category_counts,
        top_relevant_markets=[_market_card(item) for item in top_relevant],
        top_movers=[_market_card(item) for item in top_movers],
        upcoming_events=[_market_card(item) for item in upcoming],
        resolved_evaluation=resolved_eval,
        case_studies=case_studies,
        research_takeaways=takeaways,
    )


def build_metrics(
    all_markets: list[AnalyzedMarket],
    relevant: list[AnalyzedMarket],
    active_relevant: list[AnalyzedMarket],
    resolved_relevant: list[AnalyzedMarket],
    resolved_eval: dict[str, Any],
) -> dict[str, Any]:
    return {
        "total_markets": len(all_markets),
        "relevant_markets": len(relevant),
        "active_relevant_markets": len(active_relevant),
        "resolved_relevant_markets": len(resolved_relevant),
        "share_relevant": _round(len(relevant) / len(all_markets), 3) if all_markets else None,
        "avg_active_probability": _round(_safe_mean([item.market.focus_probability for item in active_relevant])),
        "avg_active_abs_1d_move": _round(_safe_mean([abs(item.market.one_day_price_change or 0.0) for item in active_relevant])),
        "avg_active_abs_1w_move": _round(_safe_mean([abs(item.market.one_week_price_change or 0.0) for item in active_relevant])),
        "avg_relevance_score": _round(_safe_mean([item.enrichment.relevance_score for item in relevant])),
        "resolved_directional_accuracy": resolved_eval.get("directional_accuracy"),
        "resolved_brier_score": resolved_eval.get("brier_score"),
    }


def evaluate_resolved_markets(markets: list[AnalyzedMarket]) -> dict[str, Any]:
    eligible = []
    calibration_buckets: dict[str, list[tuple[float, int]]] = {
        "0.0-0.2": [],
        "0.2-0.4": [],
        "0.4-0.6": [],
        "0.6-0.8": [],
        "0.8-1.0": [],
    }
    for item in markets:
        outcome = item.market.resolved_yes_outcome()
        price = item.market.last_trade_price if item.market.last_trade_price is not None else item.market.focus_probability
        if outcome is None or price is None or not item.market.is_binary_yes_no():
            continue
        price = max(0.0, min(1.0, price))
        eligible.append((item, price, outcome))
        bucket = _bucket_label(price)
        calibration_buckets[bucket].append((price, outcome))

    if not eligible:
        return {
            "eligible_markets": 0,
            "directional_accuracy": None,
            "brier_score": None,
            "calibration": [],
        }

    directional_accuracy = statistics.mean(1.0 if (price >= 0.5) == bool(outcome) else 0.0 for _, price, outcome in eligible)
    brier = statistics.mean((price - outcome) ** 2 for _, price, outcome in eligible)
    calibration = []
    for bucket, values in calibration_buckets.items():
        if not values:
            continue
        avg_prob = statistics.mean(price for price, _ in values)
        realized_rate = statistics.mean(outcome for _, outcome in values)
        calibration.append(
            {
                "bucket": bucket,
                "count": len(values),
                "avg_predicted_yes_prob": round(avg_prob, 4),
                "realized_yes_rate": round(realized_rate, 4),
            }
        )

    return {
        "eligible_markets": len(eligible),
        "directional_accuracy": round(directional_accuracy, 4),
        "brier_score": round(brier, 4),
        "calibration": calibration,
        "sample": [
            {
                "question": item.market.question,
                "predicted_yes_prob": round(price, 4),
                "realized_yes": outcome,
                "category": item.enrichment.primary_category,
            }
            for item, price, outcome in eligible[:8]
        ],
    }


def build_case_studies(markets: list[AnalyzedMarket]) -> list[dict[str, Any]]:
    studies = []
    for item in markets:
        studies.append(
            {
                "question": item.market.question,
                "category": item.enrichment.primary_category,
                "probability": item.market.focus_probability,
                "one_day_price_change": item.market.one_day_price_change,
                "one_week_price_change": item.market.one_week_price_change,
                "summary": item.enrichment.summary,
                "why_it_matters": item.enrichment.rationale,
            }
        )
    return studies


def build_research_takeaways(
    metrics: dict[str, Any],
    category_counts: list[dict[str, Any]],
    resolved_eval: dict[str, Any],
    case_studies: list[dict[str, Any]],
) -> list[str]:
    takeaways = []
    if metrics["share_relevant"] is not None:
        takeaways.append(
            f"{metrics['relevant_markets']} of {metrics['total_markets']} markets ({metrics['share_relevant']:.1%}) were identified as business-relevant."
        )
    if category_counts:
        lead = category_counts[0]
        takeaways.append(
            f"The largest relevant bucket was {lead['category']} with {lead['count']} markets, suggesting the pipeline can separate corporate, AI, and policy themes."
        )
    if resolved_eval.get("eligible_markets"):
        takeaways.append(
            f"Among {resolved_eval['eligible_markets']} resolved binary markets, the prototype produced directional accuracy of {resolved_eval['directional_accuracy']:.1%} and a Brier score of {resolved_eval['brier_score']:.3f}."
        )
    if case_studies:
        first = case_studies[0]
        takeaways.append(
            f"The biggest active mover was '{first['question']}', which supports RQ3 by surfacing markets where sharp price changes deserve news-based case-study follow-up."
        )
    return takeaways


def _market_card(item: AnalyzedMarket) -> dict[str, Any]:
    return {
        "question": item.market.question,
        "category": item.enrichment.primary_category,
        "relevance_score": item.enrichment.relevance_score,
        "probability": item.market.focus_probability,
        "focus_outcome": item.market.focus_outcome_label,
        "one_day_price_change": item.market.one_day_price_change,
        "one_week_price_change": item.market.one_week_price_change,
        "volume_24h": item.market.volume_24h,
        "end_date": item.market.end_date,
        "summary": item.enrichment.summary,
        "url": item.market.url,
    }


def _bucket_label(probability: float) -> str:
    if probability < 0.2:
        return "0.0-0.2"
    if probability < 0.4:
        return "0.2-0.4"
    if probability < 0.6:
        return "0.4-0.6"
    if probability < 0.8:
        return "0.6-0.8"
    return "0.8-1.0"
