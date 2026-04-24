# Peng Cheng Mingxia Li Final Project

This repository contains the final submission package for the project:

**AI-Enhanced Business Event Forecasting Using Polymarket**

## Repository Layout

- `01_Paper/`
  - `final_paper.pdf`: final paper
  - `final_paper.tex`: LaTeX source
  - `final_report.md`: generated analytical report
- `02_Results/`
  - `dashboard.html`: interactive dashboard
  - `market_analysis.csv`: market-level output
  - `raw_markets.json`: raw market records used in the run
  - `summary.json`: summary metrics and case studies
- `03_Project/`
  - runnable source code, fixture data, tests, and package metadata
- `04_Preview/`
  - dashboard preview images

## Recommended Viewing Order

1. Open `01_Paper/final_paper.pdf`
2. Open `02_Results/dashboard.html`
3. Review `02_Results/summary.json`
4. Inspect `03_Project/` for implementation details

## Reproduce the Project

From inside `03_Project/`:

```bash
PYTHONPATH=src python3 -m polymarket_ai_business run --source fixture --news-source fixture --compile-paper
```

Run tests with:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests
```

## Note

The packaged outputs were generated in fixture mode because the development environment was geoblocked from live Polymarket access during development.
