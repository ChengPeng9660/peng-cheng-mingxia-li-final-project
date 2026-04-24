from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from polymarket_ai_business.config import DEFAULT_FIXTURE_PATH, PipelineConfig
from polymarket_ai_business.pipeline import run_pipeline


class PipelineTests(unittest.TestCase):
    def test_fixture_pipeline_generates_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            config = PipelineConfig(
                source_mode="fixture",
                provider="heuristic",
                output_dir=Path(tmpdir),
                fixture_path=DEFAULT_FIXTURE_PATH,
            )
            result = run_pipeline(config)
            self.assertEqual(result.source, "fixture")
            self.assertTrue(result.artifacts["html"].exists())
            self.assertTrue(result.artifacts["csv"].exists())
            self.assertTrue(result.artifacts["report"].exists())
            self.assertTrue(result.artifacts["paper_tex"].exists())
            self.assertGreater(len(result.analyzed_markets), 0)

    def test_summary_contains_business_categories(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            config = PipelineConfig(
                source_mode="fixture",
                provider="heuristic",
                output_dir=Path(tmpdir),
                fixture_path=DEFAULT_FIXTURE_PATH,
            )
            result = run_pipeline(config)
            categories = {row["category"] for row in result.summary["category_counts"]}
            self.assertIn("Business / Finance", categories)
            self.assertIn("Macro / Regulation", categories)

    def test_news_digest_is_attached(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            config = PipelineConfig(
                source_mode="fixture",
                provider="heuristic",
                news_source="fixture",
                output_dir=Path(tmpdir),
                fixture_path=DEFAULT_FIXTURE_PATH,
            )
            result = run_pipeline(config)
            self.assertGreater(len(result.summary["news_digest"]), 0)
            self.assertIn("source", result.summary["news_digest"][0])

    def test_openai_provider_without_key_falls_back_cleanly(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            config = PipelineConfig(
                source_mode="fixture",
                provider="openai",
                openai_api_key=None,
                output_dir=Path(tmpdir),
                fixture_path=DEFAULT_FIXTURE_PATH,
            )
            result = run_pipeline(config)
            providers = {row["provider"] for row in result.summary["top_relevant_markets"] if "provider" in row}
            self.assertEqual(result.source, "fixture")
            self.assertTrue(result.artifacts["paper_tex"].exists())

    def test_resolved_metrics_are_populated(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            config = PipelineConfig(
                source_mode="fixture",
                provider="heuristic",
                output_dir=Path(tmpdir),
                fixture_path=DEFAULT_FIXTURE_PATH,
            )
            result = run_pipeline(config)
            resolved = result.summary["resolved_evaluation"]
            self.assertGreaterEqual(resolved["eligible_markets"], 4)
            self.assertIsNotNone(resolved["directional_accuracy"])
            self.assertIsNotNone(resolved["brier_score"])


if __name__ == "__main__":
    unittest.main()
