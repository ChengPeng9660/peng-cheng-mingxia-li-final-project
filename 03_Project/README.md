# Polymarket AI Business Research Prototype

This folder implements the project proposed in your write-up:

> AI-Enhanced Business Event Forecasting Using Polymarket

The prototype turns Polymarket-style market data into a research workflow with four layers:

1. market ingestion
2. AI-assisted market filtering and summarization
3. descriptive and resolved-market analysis
4. dashboard/report generation

## What is implemented

- A `live` Polymarket client using the official Gamma `keyset` market endpoint
- A `fixture` mode that runs fully offline using bundled sample data
- Business-market classification into:
  - `Business / Finance`
  - `AI / Technology`
  - `Macro / Regulation`
  - `Not Relevant`
- A default heuristic enricher that works without any API key
- An optional OpenAI-based enricher that can replace the heuristic summaries/classification
- Analysis outputs for:
  - relevant market counts
  - category distributions
  - top movers
  - upcoming events
  - resolved yes/no market accuracy and Brier score
- Optional news linkage for high-movement markets using GDELT with fixture fallback
- A generated HTML dashboard and CSV/JSON outputs
- A generated `final_report.md` that can be used as the basis for the course write-up
- A generated `final_paper.tex` and optional PDF compile path for a course-style paper deliverable

## Why fixture mode exists

Polymarket geoblocks some regions, and this environment is currently flagged as blocked by `https://polymarket.com/api/geoblock`. Because of that, the project supports:

- `--source live`: use the real Polymarket endpoint when your network can access it
- `--source fixture`: run the full pipeline offline with bundled sample data
- `--source auto`: try live first, then fall back to fixture if access is blocked

The bundled fixture is synthetic and exists only so the full prototype can run end to end even when live access is unavailable.

## Quick start

Run the project directly without installing dependencies:

```bash
cd /Users/pcc/Desktop/replication/polymarket_ai_business
PYTHONPATH=src python3 -m polymarket_ai_business run --source fixture
```

This writes outputs to:

- `outputs/latest/dashboard.html`
- `outputs/latest/market_analysis.csv`
- `outputs/latest/summary.json`
- `outputs/latest/raw_markets.json`
- `outputs/latest/final_report.md`
- `outputs/latest/final_paper.tex`
- `outputs/latest/final_paper.pdf` when `--compile-paper` succeeds

If you want to install it as a local package first:

```bash
cd /Users/pcc/Desktop/replication/polymarket_ai_business
python3 -m pip install -e .
polymarket-business run --source fixture
```

## Optional LLM enrichment

If you want true LLM-generated labels and summaries, set:

```bash
export OPENAI_API_KEY=your_key_here
export OPENAI_MODEL=gpt-5-mini
```

Then run:

```bash
PYTHONPATH=src python3 -m polymarket_ai_business run --source fixture --provider openai
```

If the OpenAI call fails, the pipeline automatically falls back to the heuristic enricher for that market.
Successful OpenAI enrichments are cached in `outputs/latest/llm_enrichment_cache.json` so repeated runs are cheaper and easier to reproduce.

## Commands

Run the pipeline:

```bash
PYTHONPATH=src python3 -m polymarket_ai_business run --source auto --news-source auto --compile-paper
```

Check whether the current network is geoblocked:

```bash
PYTHONPATH=src python3 -m polymarket_ai_business geoblock
```

Run tests:

```bash
cd /Users/pcc/Desktop/replication/polymarket_ai_business
python3 -m unittest discover -s tests
```

## Project structure

- `src/polymarket_ai_business/client.py`: live Polymarket access plus fixture loader
- `src/polymarket_ai_business/enrichment.py`: heuristic and optional OpenAI enrichment
- `src/polymarket_ai_business/news.py`: optional GDELT-based news linkage plus fixture fallback
- `src/polymarket_ai_business/analytics.py`: descriptive statistics and resolved-market evaluation
- `src/polymarket_ai_business/reporting.py`: CSV/JSON/HTML output generation
- `src/polymarket_ai_business/authoring.py`: auto-generated final report writing
- `outputs/latest/llm_enrichment_cache.json`: cached real-LLM enrichments when `--provider openai` is used
- `src/polymarket_ai_business/pipeline.py`: CLI entry point and orchestration
- `data/fixtures/sample_markets.json`: synthetic demo dataset
- `data/fixtures/sample_news.json`: synthetic linked-news demo dataset

## Notes for your final paper

This code maps closely to the proposal:

- `RQ1`: evaluated through resolved binary markets and simple forecast metrics
- `RQ2`: addressed by automatic relevance filtering and AI-enhanced summaries
- `RQ3`: supported by large-move detection and case-study candidate extraction

If you later run the project on live data from an accessible network, you can directly replace the synthetic fixture outputs with real Polymarket outputs and keep the rest of the analysis pipeline unchanged.
