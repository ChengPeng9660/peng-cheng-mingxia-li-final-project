from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from polymarket_ai_business.analytics import analyze_markets
from polymarket_ai_business.authoring import write_final_paper, write_final_report
from polymarket_ai_business.client import FixtureClient, GeoblockedError, PolymarketClient, SourcePayload
from polymarket_ai_business.config import (
    DEFAULT_FIXTURE_PATH,
    DEFAULT_NEWS_FIXTURE_PATH,
    DEFAULT_OUTPUT_DIR,
    PipelineConfig,
)
from polymarket_ai_business.enrichment import build_enricher
from polymarket_ai_business.models import AnalyzedMarket, MarketRecord
from polymarket_ai_business.news import attach_news_digest
from polymarket_ai_business.reporting import write_outputs


@dataclass(slots=True)
class PipelineResult:
    source: str
    source_metadata: dict
    analyzed_markets: list[AnalyzedMarket]
    artifacts: dict[str, Path]
    summary: dict


def run_pipeline(config: PipelineConfig) -> PipelineResult:
    source_payload = load_source(config)
    fetched_at = source_payload.metadata.get("generated_at") or source_payload.metadata.get("fetched_at") or "unknown"
    records = [MarketRecord.from_api(raw, fetched_at=fetched_at) for raw in source_payload.markets]
    enricher = build_enricher(
        config.provider,
        api_key=config.openai_api_key,
        model=config.openai_model,
        cache_path=config.output_dir / "llm_enrichment_cache.json",
    )
    analyzed = [AnalyzedMarket(market=record, enrichment=enricher.enrich(record)) for record in records]
    summary = analyze_markets(analyzed, source=source_payload.source, source_metadata=source_payload.metadata)
    effective_news_source = _resolve_news_source(config.news_source, source_payload.source)
    news_digest, news_metadata = attach_news_digest(
        analyzed,
        news_source=effective_news_source,
        news_limit_per_market=config.news_limit_per_market,
        news_market_count=config.news_market_count,
        news_fixture_path=config.news_fixture_path,
    )
    summary.news_digest = news_digest
    summary.metadata["news"] = news_metadata
    _attach_news_to_case_studies(summary, news_digest)
    artifacts = write_outputs(analyzed_markets=analyzed, summary=summary, output_dir=config.output_dir)
    artifacts["report"] = write_final_report(
        summary=summary,
        analyzed_markets=analyzed,
        output_dir=config.output_dir,
        title=config.report_title,
    )
    paper_tex_path, paper_pdf_path = write_final_paper(
        summary=summary,
        analyzed_markets=analyzed,
        output_dir=config.output_dir,
        title=config.paper_title,
        authors=config.paper_authors,
        compile_pdf=config.compile_paper,
    )
    artifacts["paper_tex"] = paper_tex_path
    if paper_pdf_path is not None:
        artifacts["paper_pdf"] = paper_pdf_path
    return PipelineResult(
        source=source_payload.source,
        source_metadata=source_payload.metadata,
        analyzed_markets=analyzed,
        artifacts=artifacts,
        summary=summary.to_dict(),
    )


def load_source(config: PipelineConfig) -> SourcePayload:
    fixture_client = FixtureClient()
    live_client = PolymarketClient()

    if config.source_mode == "fixture":
        return fixture_client.load(config.fixture_path)

    if config.source_mode == "live":
        return _load_live_payload(config, live_client)

    try:
        return _load_live_payload(config, live_client)
    except GeoblockedError as exc:
        payload = fixture_client.load(config.fixture_path)
        payload.metadata = {
            **payload.metadata,
            "fallback_reason": str(exc),
            "requested_source_mode": config.source_mode,
        }
        return payload


def _load_live_payload(config: PipelineConfig, client: PolymarketClient) -> SourcePayload:
    open_payload = client.fetch_markets(closed=False, limit=config.limit, max_pages=config.max_pages)
    resolved_payload = client.fetch_markets(closed=True, limit=max(10, min(config.limit, 20)), max_pages=1)
    combined_markets = open_payload.markets + resolved_payload.markets
    deduped = []
    seen = set()
    for market in combined_markets:
        market_id = market.get("id")
        if market_id in seen:
            continue
        seen.add(market_id)
        deduped.append(market)
    return SourcePayload(
        source="live",
        markets=deduped,
        metadata={
            "open_payload": open_payload.metadata,
            "resolved_payload": resolved_payload.metadata,
            "fetched_at": open_payload.metadata.get("fetched_at", "live"),
        },
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Polymarket AI business research prototype")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Run the full data + analysis + dashboard pipeline")
    run_parser.add_argument("--source", choices=("auto", "live", "fixture"), default="auto")
    run_parser.add_argument("--provider", choices=("heuristic", "openai"), default="heuristic")
    run_parser.add_argument("--limit", type=int, default=40)
    run_parser.add_argument("--max-pages", type=int, default=3)
    run_parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    run_parser.add_argument("--fixture-path", type=Path, default=DEFAULT_FIXTURE_PATH)
    run_parser.add_argument("--news-source", choices=("auto", "live", "fixture", "none"), default="auto")
    run_parser.add_argument("--news-limit", type=int, default=3)
    run_parser.add_argument("--news-market-count", type=int, default=4)
    run_parser.add_argument("--news-fixture-path", type=Path, default=DEFAULT_NEWS_FIXTURE_PATH)
    run_parser.add_argument(
        "--report-title",
        type=str,
        default="Final Project Report: AI-Enhanced Business Event Forecasting Using Polymarket",
    )
    run_parser.add_argument(
        "--paper-title",
        type=str,
        default="AI-Enhanced Business Event Forecasting Using Polymarket",
    )
    run_parser.add_argument(
        "--paper-authors",
        type=str,
        default="Cheng Peng \\\\and Mingxia Li",
    )
    run_parser.add_argument("--compile-paper", action="store_true")

    subparsers.add_parser("geoblock", help="Check whether Polymarket geoblocks the current network")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "geoblock":
        status = PolymarketClient().geoblock_status()
        print(json.dumps(status, indent=2, ensure_ascii=False))
        return 0

    config = PipelineConfig(
        source_mode=args.source,
        provider=args.provider,
        limit=args.limit,
        max_pages=args.max_pages,
        output_dir=args.output_dir,
        fixture_path=args.fixture_path,
        news_source=args.news_source,
        news_limit_per_market=args.news_limit,
        news_market_count=args.news_market_count,
        news_fixture_path=args.news_fixture_path,
        report_title=args.report_title,
        paper_title=args.paper_title,
        paper_authors=args.paper_authors,
        compile_paper=args.compile_paper,
    )
    result = run_pipeline(config)
    print(f"Source used: {result.source}")
    print(f"Markets analyzed: {len(result.analyzed_markets)}")
    print(f"Dashboard: {result.artifacts['html']}")
    print(f"CSV: {result.artifacts['csv']}")
    print(f"Report: {result.artifacts['report']}")
    print(f"Paper TeX: {result.artifacts['paper_tex']}")
    if "paper_pdf" in result.artifacts:
        print(f"Paper PDF: {result.artifacts['paper_pdf']}")
    return 0


def _attach_news_to_case_studies(summary, news_digest: list[dict]) -> None:
    news_by_question = {item["question"]: item for item in news_digest}
    for case in summary.case_studies:
        linked = news_by_question.get(case["question"])
        case["linked_news"] = linked.get("articles", [])[:2] if linked else []


def _resolve_news_source(configured_source: str, market_source: str) -> str:
    if configured_source != "auto":
        return configured_source
    if market_source == "fixture":
        return "fixture"
    return "auto"


if __name__ == "__main__":
    raise SystemExit(main())
