from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "outputs" / "latest"
DEFAULT_FIXTURE_PATH = PROJECT_ROOT / "data" / "fixtures" / "sample_markets.json"
DEFAULT_NEWS_FIXTURE_PATH = PROJECT_ROOT / "data" / "fixtures" / "sample_news.json"


@dataclass(slots=True)
class PipelineConfig:
    source_mode: str = "auto"
    provider: str = "heuristic"
    limit: int = 40
    max_pages: int = 3
    output_dir: Path = DEFAULT_OUTPUT_DIR
    fixture_path: Path = DEFAULT_FIXTURE_PATH
    news_source: str = "auto"
    news_limit_per_market: int = 3
    news_market_count: int = 4
    news_fixture_path: Path = DEFAULT_NEWS_FIXTURE_PATH
    report_title: str = "Final Project Report: AI-Enhanced Business Event Forecasting Using Polymarket"
    paper_title: str = "AI-Enhanced Business Event Forecasting Using Polymarket"
    paper_authors: str = "Cheng Peng \\and Mingxia Li"
    compile_paper: bool = False
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-5-mini")
