from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from polymarket_ai_business.analytics import PipelineSummary
from polymarket_ai_business.models import AnalyzedMarket


def write_outputs(
    *,
    analyzed_markets: list[AnalyzedMarket],
    summary: PipelineSummary,
    output_dir: Path,
) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "market_analysis.csv"
    raw_json_path = output_dir / "raw_markets.json"
    summary_path = output_dir / "summary.json"
    html_path = output_dir / "dashboard.html"

    rows = [item.to_row() for item in analyzed_markets]
    _write_csv(csv_path, rows)
    raw_json_path.write_text(
        json.dumps([item.market.raw for item in analyzed_markets], indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    summary_path.write_text(json.dumps(summary.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
    html_path.write_text(render_dashboard(summary), encoding="utf-8")
    return {
        "csv": csv_path,
        "raw_json": raw_json_path,
        "summary_json": summary_path,
        "html": html_path,
    }


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def render_dashboard(summary: PipelineSummary) -> str:
    payload = json.dumps(summary.to_dict(), ensure_ascii=False)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Polymarket Business Research Dashboard</title>
  <style>
    :root {{
      --bg: #f5f1e8;
      --panel: #fffaf2;
      --panel-strong: #f7efe2;
      --ink: #1f2933;
      --muted: #5f6b76;
      --accent: #0f766e;
      --accent-2: #a16207;
      --border: rgba(31, 41, 51, 0.12);
      --shadow: 0 18px 40px rgba(31, 41, 51, 0.08);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      color: var(--ink);
      background:
        radial-gradient(circle at top left, rgba(15, 118, 110, 0.12), transparent 30%),
        radial-gradient(circle at top right, rgba(161, 98, 7, 0.10), transparent 28%),
        linear-gradient(180deg, #f8f3eb 0%, var(--bg) 100%);
      font-family: "Avenir Next", "Segoe UI", sans-serif;
      line-height: 1.55;
    }}
    .wrap {{
      width: min(1180px, calc(100vw - 32px));
      margin: 0 auto;
      padding: 40px 0 64px;
    }}
    .hero {{
      display: grid;
      gap: 20px;
      grid-template-columns: 2fr 1fr;
      align-items: end;
      margin-bottom: 24px;
    }}
    .hero-card, .panel {{
      background: rgba(255, 250, 242, 0.85);
      backdrop-filter: blur(8px);
      border: 1px solid var(--border);
      border-radius: 24px;
      padding: 24px;
      box-shadow: var(--shadow);
    }}
    h1 {{
      margin: 0 0 8px;
      font-size: clamp(2rem, 4vw, 3.2rem);
      line-height: 1.05;
      letter-spacing: -0.03em;
    }}
    h2 {{
      margin: 0 0 14px;
      font-size: 1.1rem;
      letter-spacing: 0.02em;
      text-transform: uppercase;
      color: var(--muted);
    }}
    p, li {{ color: var(--muted); }}
    .badge {{
      display: inline-block;
      padding: 6px 12px;
      border-radius: 999px;
      background: rgba(15, 118, 110, 0.10);
      color: var(--accent);
      font-weight: 700;
      font-size: 0.85rem;
      margin-bottom: 14px;
    }}
    .kpis {{
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 16px;
      margin: 24px 0;
    }}
    .kpi {{
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 20px;
      padding: 18px;
      box-shadow: var(--shadow);
    }}
    .kpi-label {{
      font-size: 0.82rem;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      color: var(--muted);
    }}
    .kpi-value {{
      font-size: 1.9rem;
      font-weight: 800;
      letter-spacing: -0.03em;
      margin-top: 8px;
    }}
    .grid {{
      display: grid;
      grid-template-columns: 1.1fr 0.9fr;
      gap: 16px;
      margin-bottom: 16px;
    }}
    .chart-bars {{
      display: grid;
      gap: 10px;
    }}
    .bar-row {{
      display: grid;
      grid-template-columns: 180px 1fr 50px;
      gap: 12px;
      align-items: center;
    }}
    .bar-track {{
      height: 14px;
      border-radius: 999px;
      background: rgba(31, 41, 51, 0.08);
      overflow: hidden;
    }}
    .bar-fill {{
      height: 100%;
      border-radius: 999px;
      background: linear-gradient(90deg, var(--accent), #14b8a6);
    }}
    .takeaways li {{
      margin-bottom: 8px;
    }}
    .table-tools {{
      display: flex;
      gap: 12px;
      margin-bottom: 14px;
      flex-wrap: wrap;
    }}
    .table-tools input, .table-tools select {{
      border: 1px solid var(--border);
      border-radius: 999px;
      padding: 10px 14px;
      background: white;
      color: var(--ink);
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 0.95rem;
    }}
    th, td {{
      text-align: left;
      padding: 12px 10px;
      border-bottom: 1px solid rgba(31, 41, 51, 0.08);
      vertical-align: top;
    }}
    th {{
      font-size: 0.82rem;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      color: var(--muted);
    }}
    .pill {{
      display: inline-block;
      padding: 4px 10px;
      border-radius: 999px;
      background: rgba(161, 98, 7, 0.10);
      color: var(--accent-2);
      font-weight: 700;
      font-size: 0.78rem;
    }}
    .section {{
      margin-top: 18px;
    }}
    a {{
      color: var(--accent);
      text-decoration: none;
    }}
    @media (max-width: 960px) {{
      .hero, .grid, .kpis {{
        grid-template-columns: 1fr;
      }}
      .bar-row {{
        grid-template-columns: 1fr;
      }}
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="hero">
      <section class="hero-card">
        <div class="badge">AI for Business Research</div>
        <h1>Polymarket Business Event Forecasting Dashboard</h1>
        <p>This dashboard converts raw market data into business research signals: relevant market detection, AI-assisted summaries, descriptive analytics, and simple resolved-market forecast checks.</p>
      </section>
      <aside class="hero-card">
        <h2>Run Metadata</h2>
        <div id="metadata"></div>
      </aside>
    </div>

    <section class="kpis" id="kpis"></section>

    <section class="grid">
      <div class="panel">
        <h2>Research Takeaways</h2>
        <ul class="takeaways" id="takeaways"></ul>
      </div>
      <div class="panel">
        <h2>Relevant Category Mix</h2>
        <div class="chart-bars" id="category-bars"></div>
      </div>
    </section>

    <section class="grid">
      <div class="panel">
        <h2>Resolved Market Evaluation</h2>
        <div id="resolved-overview"></div>
        <table>
          <thead>
            <tr>
              <th>Bucket</th>
              <th>Count</th>
              <th>Avg Predicted Yes</th>
              <th>Realized Yes Rate</th>
            </tr>
          </thead>
          <tbody id="calibration-table"></tbody>
        </table>
      </div>
      <div class="panel">
        <h2>Case Study Candidates</h2>
        <div id="case-studies"></div>
      </div>
    </section>

    <section class="panel section">
      <h2>News Linkage</h2>
      <div id="news-digest"></div>
    </section>

    <section class="panel section">
      <h2>Top Relevant Active Markets</h2>
      <div class="table-tools">
        <input id="search-box" type="search" placeholder="Filter by keyword..." />
        <select id="category-filter">
          <option value="">All categories</option>
        </select>
      </div>
      <table>
        <thead>
          <tr>
            <th>Market</th>
            <th>Category</th>
            <th>Prob.</th>
            <th>1W Move</th>
            <th>Summary</th>
          </tr>
        </thead>
        <tbody id="top-relevant-table"></tbody>
      </table>
    </section>

    <section class="grid section">
      <div class="panel">
        <h2>Top Movers</h2>
        <table>
          <thead>
            <tr>
              <th>Market</th>
              <th>Category</th>
              <th>1D Move</th>
              <th>1W Move</th>
            </tr>
          </thead>
          <tbody id="top-movers-table"></tbody>
        </table>
      </div>
      <div class="panel">
        <h2>Upcoming Events</h2>
        <table>
          <thead>
            <tr>
              <th>Market</th>
              <th>Category</th>
              <th>End Date</th>
            </tr>
          </thead>
          <tbody id="upcoming-table"></tbody>
        </table>
      </div>
    </section>
  </div>

  <script>
    const data = {payload};

    const percent = (value) => value == null ? "n/a" : `${{(value * 100).toFixed(1)}}%`;
    const pp = (value) => value == null ? "n/a" : `${{value >= 0 ? "+" : ""}}${{(value * 100).toFixed(1)}}pp`;

    const metadata = document.getElementById("metadata");
    const kpis = document.getElementById("kpis");
    const takeaways = document.getElementById("takeaways");
    const categoryBars = document.getElementById("category-bars");
    const calibrationTable = document.getElementById("calibration-table");
    const caseStudies = document.getElementById("case-studies");
    const newsDigest = document.getElementById("news-digest");
    const relevantTable = document.getElementById("top-relevant-table");
    const topMoversTable = document.getElementById("top-movers-table");
    const upcomingTable = document.getElementById("upcoming-table");
    const resolvedOverview = document.getElementById("resolved-overview");
    const searchBox = document.getElementById("search-box");
    const categoryFilter = document.getElementById("category-filter");

    const sourceMeta = data.metadata.source_metadata || {{}};
    const metaLines = [
      `<p><strong>Generated:</strong> ${{data.metadata.generated_at_utc}}</p>`,
      `<p><strong>Source:</strong> <span class="pill">${{data.metadata.source}}</span></p>`
    ];
    if (sourceMeta.source_note) {{
      metaLines.push(`<p><strong>Note:</strong> ${{sourceMeta.source_note}}</p>`);
    }}
    if (sourceMeta.fallback_reason) {{
      metaLines.push(`<p><strong>Fallback:</strong> ${{sourceMeta.fallback_reason}}</p>`);
    }}
    if (sourceMeta.generated_at) {{
      metaLines.push(`<p><strong>Fixture timestamp:</strong> ${{sourceMeta.generated_at}}</p>`);
    }}
    metadata.innerHTML = metaLines.join("");

    const metricCards = [
      ["Total markets", data.metrics.total_markets],
      ["Relevant markets", data.metrics.relevant_markets],
      ["Avg active 1W move", pp(data.metrics.avg_active_abs_1w_move)],
      ["Resolved accuracy", data.metrics.resolved_directional_accuracy == null ? "n/a" : `${{(data.metrics.resolved_directional_accuracy * 100).toFixed(1)}}%`],
    ];
    metricCards.forEach(([label, value]) => {{
      const card = document.createElement("div");
      card.className = "kpi";
      card.innerHTML = `<div class="kpi-label">${{label}}</div><div class="kpi-value">${{value}}</div>`;
      kpis.appendChild(card);
    }});

    data.research_takeaways.forEach((item) => {{
      const li = document.createElement("li");
      li.textContent = item;
      takeaways.appendChild(li);
    }});

    const maxCategory = Math.max(...data.category_counts.map(item => item.count), 1);
    data.category_counts.forEach((item) => {{
      const row = document.createElement("div");
      row.className = "bar-row";
      row.innerHTML = `
        <div>${{item.category}}</div>
        <div class="bar-track"><div class="bar-fill" style="width:${{(item.count / maxCategory) * 100}}%"></div></div>
        <div>${{item.count}}</div>
      `;
      categoryBars.appendChild(row);
      const option = document.createElement("option");
      option.value = item.category;
      option.textContent = item.category;
      categoryFilter.appendChild(option);
    }});

    resolvedOverview.innerHTML = `
      <p><strong>Eligible resolved binary markets:</strong> ${{data.resolved_evaluation.eligible_markets}}</p>
      <p><strong>Brier score:</strong> ${{data.resolved_evaluation.brier_score ?? "n/a"}}</p>
      <p><strong>Directional accuracy:</strong> ${{data.resolved_evaluation.directional_accuracy == null ? "n/a" : `${{(data.resolved_evaluation.directional_accuracy * 100).toFixed(1)}}%`}}</p>
    `;

    (data.resolved_evaluation.calibration || []).forEach((row) => {{
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${{row.bucket}}</td>
        <td>${{row.count}}</td>
        <td>${{percent(row.avg_predicted_yes_prob)}}</td>
        <td>${{percent(row.realized_yes_rate)}}</td>
      `;
      calibrationTable.appendChild(tr);
    }});

    (data.case_studies || []).forEach((study) => {{
      const card = document.createElement("div");
      card.style.marginBottom = "14px";
      card.innerHTML = `
        <p><strong>${{study.question}}</strong></p>
        <p><span class="pill">${{study.category}}</span> Probability: ${{percent(study.probability)}} | 1W move: ${{pp(study.one_week_price_change)}}</p>
        <p>${{study.summary}}</p>
      `;
      caseStudies.appendChild(card);
    }});

    (data.news_digest || []).forEach((item) => {{
      const card = document.createElement("div");
      card.style.marginBottom = "18px";
      const articles = (item.articles || []).map((article) => {{
        if (article.url) {{
          return `<li><a href="${{article.url}}">${{article.title}}</a> <span class="pill">${{article.source || 'source'}}</span></li>`;
        }}
        return `<li>${{article.title}} <span class="pill">${{article.source || 'source'}}</span></li>`;
      }}).join("");
      card.innerHTML = `
        <p><strong>${{item.question}}</strong></p>
        <p><span class="pill">${{item.category}}</span> <span class="pill">${{item.source}}</span></p>
        <p>${{item.digest}}</p>
        ${{articles ? `<ul>${{articles}}</ul>` : `<p>No linked headlines available.</p>`}}
      `;
      newsDigest.appendChild(card);
    }});

    function renderRelevantTable() {{
      const searchTerm = searchBox.value.trim().toLowerCase();
      const selectedCategory = categoryFilter.value;
      relevantTable.innerHTML = "";
      data.top_relevant_markets
        .filter((row) => (!selectedCategory || row.category === selectedCategory))
        .filter((row) => !searchTerm || `${{row.question}} ${{row.summary}}`.toLowerCase().includes(searchTerm))
        .forEach((row) => {{
          const tr = document.createElement("tr");
          tr.innerHTML = `
            <td><a href="${{row.url || '#'}}">${{row.question}}</a></td>
            <td><span class="pill">${{row.category}}</span></td>
            <td>${{percent(row.probability)}} for ${{row.focus_outcome || "focus outcome"}}</td>
            <td>${{pp(row.one_week_price_change)}}</td>
            <td>${{row.summary}}</td>
          `;
          relevantTable.appendChild(tr);
        }});
    }}

    (data.top_movers || []).forEach((row) => {{
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${{row.question}}</td>
        <td>${{row.category}}</td>
        <td>${{pp(row.one_day_price_change)}}</td>
        <td>${{pp(row.one_week_price_change)}}</td>
      `;
      topMoversTable.appendChild(tr);
    }});

    (data.upcoming_events || []).forEach((row) => {{
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${{row.question}}</td>
        <td>${{row.category}}</td>
        <td>${{row.end_date || "n/a"}}</td>
      `;
      upcomingTable.appendChild(tr);
    }});

    searchBox.addEventListener("input", renderRelevantTable);
    categoryFilter.addEventListener("change", renderRelevantTable);
    renderRelevantTable();
  </script>
</body>
</html>
"""
