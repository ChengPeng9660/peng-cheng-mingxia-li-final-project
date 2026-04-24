# Polymarket Final Submission

This folder is the cleaned submission package for the course project:

**AI-Enhanced Business Event Forecasting Using Polymarket**

## Folder layout

- `01_Paper/`
  - `final_paper.pdf`: ready-to-read paper
  - `final_paper.tex`: LaTeX source of the paper
  - `final_report.md`: generated analytical report
- `02_Results/`
  - `dashboard.html`: interactive HTML dashboard
  - `market_analysis.csv`: cleaned market-level output
  - `raw_markets.json`: raw market records used by the run
  - `summary.json`: compact summary metrics and case-study output
- `03_Project/`
  - source code, fixture data, tests, `README.md`, and `pyproject.toml`
- `04_Preview/`
  - dashboard screenshots for quick preview

## Recommended open order

1. Open `01_Paper/final_paper.pdf`
2. Open `02_Results/dashboard.html`
3. Use `02_Results/summary.json` and `market_analysis.csv` if you need the underlying outputs
4. Use `03_Project/` if you need to rerun or inspect the implementation

## Re-run command

From inside `03_Project/`:

```bash
PYTHONPATH=src python3 -m polymarket_ai_business run --source fixture --news-source fixture --compile-paper
```

## Note

The current packaged outputs were generated from the project's fixture mode because the working environment was geoblocked from live Polymarket access during development.
