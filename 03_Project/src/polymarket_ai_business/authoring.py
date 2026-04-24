from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from polymarket_ai_business.analytics import PipelineSummary
from polymarket_ai_business.models import AnalyzedMarket


def write_final_report(
    *,
    summary: PipelineSummary,
    analyzed_markets: list[AnalyzedMarket],
    output_dir: Path,
    title: str,
) -> Path:
    report_path = output_dir / "final_report.md"
    report_path.write_text(render_final_report(summary, analyzed_markets, title), encoding="utf-8")
    return report_path


def write_final_paper(
    *,
    summary: PipelineSummary,
    analyzed_markets: list[AnalyzedMarket],
    output_dir: Path,
    title: str,
    authors: str,
    compile_pdf: bool,
) -> tuple[Path, Path | None]:
    tex_path = output_dir / "final_paper.tex"
    tex_path.write_text(render_final_paper_tex(summary, analyzed_markets, title, authors), encoding="utf-8")
    pdf_path = compile_latex(tex_path) if compile_pdf else None
    return tex_path, pdf_path


def render_final_report(summary: PipelineSummary, analyzed_markets: list[AnalyzedMarket], title: str) -> str:
    source = summary.metadata.get("source", "unknown")
    source_note = ""
    if source == "fixture":
        source_note = (
            "> Note: this report was generated from the bundled synthetic fixture dataset because the current environment "
            "could not access live Polymarket data.\n\n"
        )

    category_rows = "\n".join(
        f"| {row['category']} | {row['count']} |" for row in summary.category_counts
    ) or "| None | 0 |"
    top_market_rows = "\n".join(
        f"| {row['question']} | {row['category']} | {_pct(row['probability'])} | {_pp(row['one_week_price_change'])} |"
        for row in summary.top_relevant_markets[:5]
    ) or "| None | n/a | n/a | n/a |"

    news_section = _render_news_section(summary.news_digest)
    case_studies = _render_case_studies(summary.case_studies)

    return f"""# {title}

Generated at: {summary.metadata.get('generated_at_utc', 'unknown')}

{source_note}## 1. Project Objective

This project evaluates whether AI can improve the usefulness of Polymarket-style prediction market probabilities for business research. The implemented pipeline collects market records, filters for business-relevant topics, produces AI-assisted summaries, links major market moves to topical news coverage, and generates descriptive and resolved-market evaluation outputs.

## 2. Data and Implementation

- Market source used in this run: `{source}`
- Total markets analyzed: `{summary.metrics['total_markets']}`
- Business-relevant markets: `{summary.metrics['relevant_markets']}`
- Active relevant markets: `{summary.metrics['active_relevant_markets']}`
- Resolved relevant markets: `{summary.metrics['resolved_relevant_markets']}`

The system currently supports two enrichment modes:

- `heuristic`: keyword-based business classification and summary generation
- `openai`: optional LLM-based enrichment when `OPENAI_API_KEY` is available

## 3. Descriptive Findings

- Share of markets identified as business-relevant: `{_pct(summary.metrics['share_relevant'])}`
- Average absolute 1-day move for active relevant markets: `{_pp(summary.metrics['avg_active_abs_1d_move'])}`
- Average absolute 1-week move for active relevant markets: `{_pp(summary.metrics['avg_active_abs_1w_move'])}`
- Average relevance score: `{summary.metrics['avg_relevance_score']}`

### Category distribution

| Category | Count |
| --- | ---: |
{category_rows}

### Top relevant active markets

| Market | Category | Implied probability | 1-week move |
| --- | --- | ---: | ---: |
{top_market_rows}

## 4. Research Question Assessment

### RQ1. Do Polymarket probabilities provide meaningful forward-looking signals for business-related events?

This run evaluated `{summary.resolved_evaluation.get('eligible_markets', 0)}` resolved binary business-related markets. The prototype produced directional accuracy of `{_pct(summary.metrics['resolved_directional_accuracy'])}` and a Brier score of `{summary.metrics['resolved_brier_score']}`. These results suggest that pre-resolution probabilities can contain usable forward-looking information, although the current sample remains small and exploratory.

### RQ2. Can an AI pipeline automatically identify and summarize relevant markets in a way that improves interpretability for business users?

Yes. The pipeline automatically classified relevant markets into business, AI/technology, and macro/regulation groups, then generated short summaries explaining why each market matters from a business perspective. The dashboard and CSV outputs convert raw market questions into a more structured research dataset.

### RQ3. Are large changes in Polymarket probabilities associated with major news developments before final resolution?

The pipeline identifies high-movement markets and attaches linked headline context when available. This does not establish causality, but it creates a practical workflow for event study style follow-up on sudden shifts in expectations.

## 5. News-Linked Market Context

{news_section}

## 6. Case Studies

{case_studies}

## 7. Main Takeaways

{_bullet_list(summary.research_takeaways)}

## 8. Limitations

- Prediction market prices are not guaranteed to be calibrated objective probabilities.
- Some markets may be thinly traded or noisy.
- The current evaluation is descriptive rather than causal.
- When live Polymarket access is blocked, offline fixture data is used instead.
- News linkage is supportive context, not proof that a specific article caused a market movement.

## 9. Conclusion

The implemented system delivers a feasible proof of concept for AI-enhanced business event forecasting with Polymarket-style data. It supports market collection, business filtering, summary generation, descriptive analysis, resolved-market evaluation, news-assisted case study development, and report/dashboard production in one reproducible workflow.
"""


def render_final_paper_tex(
    summary: PipelineSummary,
    analyzed_markets: list[AnalyzedMarket],
    title: str,
    authors: str,
) -> str:
    source = summary.metadata.get("source", "unknown")
    top_markets = summary.top_relevant_markets[:5]
    case_studies = summary.case_studies[:3]
    news_digest = summary.news_digest[:4]
    category_items = "\n".join(
        f"\\item {latex_escape(row['category'])}: {row['count']} markets"
        for row in summary.category_counts
    ) or "\\item No relevant categories identified."
    top_market_items = "\n".join(
        (
            f"\\item \\textbf{{{latex_escape(row['question'])}}} "
            f"({latex_escape(row['category'])}); implied probability {latex_escape(_pct(row['probability']))}; "
            f"1-week move {latex_escape(_pp(row['one_week_price_change']))}."
        )
        for row in top_markets
    ) or "\\item No relevant active markets identified."
    news_items = "\n".join(_news_item_tex(item) for item in news_digest) or "\\item No linked news items were available."
    case_items = "\n".join(_case_item_tex(item) for item in case_studies) or "\\item No case studies were generated."
    takeaways = "\n".join(f"\\item {latex_escape(item)}" for item in summary.research_takeaways) or "\\item No takeaways generated."
    fixture_note = ""
    if source == "fixture":
        fixture_note = (
            "\\noindent\\textit{Note: this paper was generated from the bundled synthetic fixture dataset because the "
            "current environment could not access live Polymarket data.}\\\\\n"
        )
    return rf"""\documentclass[12pt]{{article}}
\usepackage[margin=1in]{{geometry}}
\usepackage{{hyperref}}

\linespread{{1.15}}
\title{{\textbf{{{latex_escape(title)}}}}}
\author{{{authors}}}
\date{{}}

\begin{{document}}
\maketitle

{fixture_note}
\section{{Introduction}}

This paper presents an AI-enhanced business research prototype that uses Polymarket-style prediction market data to identify, classify, summarize, and interpret business-relevant event expectations. The motivation is that firms, investors, and analysts often need forward-looking signals that update more quickly than conventional analyst reports, disclosures, or survey measures.

\section{{Project Objective}}

The objective is to evaluate whether AI can improve the usefulness of Polymarket probabilities for business research by automatically filtering relevant markets, producing structured summaries, linking large probability changes to contemporaneous news, and generating research-ready outputs.

\section{{Data and System Design}}

The implemented pipeline has four layers: market ingestion, AI-assisted enrichment, descriptive and resolved-market analysis, and output generation. In this run, the source mode was \texttt{{{latex_escape(source)}}}. The dataset contained {summary.metrics['total_markets']} markets, of which {summary.metrics['relevant_markets']} were classified as business-relevant.

The system supports two enrichment paths:
\begin{{itemize}}
\item a heuristic classifier that works without external model access;
\item a real OpenAI Responses API mode that can produce structured JSON labels and summaries when \texttt{{OPENAI\_API\_KEY}} is configured.
\end{{itemize}}

\section{{Descriptive Findings}}

The analysis found that {latex_escape(_pct(summary.metrics['share_relevant']))} of markets were business-relevant. Among active relevant markets, the average absolute one-day move was {latex_escape(_pp(summary.metrics['avg_active_abs_1d_move']))}, while the average absolute one-week move was {latex_escape(_pp(summary.metrics['avg_active_abs_1w_move']))}. The average relevance score was {latex_escape(str(summary.metrics['avg_relevance_score']))}.

\subsection{{Category Distribution}}

\begin{{itemize}}
{category_items}
\end{{itemize}}

\subsection{{Top Relevant Active Markets}}

\begin{{itemize}}
{top_market_items}
\end{{itemize}}

\section{{Research Question Assessment}}

\subsection{{RQ1: Forward-Looking Signal Value}}

The resolved-market evaluation included {summary.resolved_evaluation.get('eligible_markets', 0)} binary business-related markets. The prototype produced directional accuracy of {latex_escape(_pct(summary.metrics['resolved_directional_accuracy']))} and a Brier score of {latex_escape(str(summary.metrics['resolved_brier_score']))}. These results suggest that prediction-market probabilities can contain useful forward-looking information, although the current setting remains exploratory and sample-limited.

\subsection{{RQ2: AI-Assisted Interpretability}}

The project demonstrates that an AI pipeline can organize raw market questions into business, AI/technology, and macro/regulation categories while generating short explanations of business relevance. This substantially improves interpretability relative to raw market titles alone and makes the output more useful for research purposes.

\subsection{{RQ3: Probability Changes and News Developments}}

The system identifies high-movement markets and attaches linked news context when available. While this does not establish causal effects, it creates a practical screening workflow for case-study analysis and event-study style follow-up.

\section{{News-Linked Context}}

\begin{{itemize}}
{news_items}
\end{{itemize}}

\section{{Case Studies}}

\begin{{itemize}}
{case_items}
\end{{itemize}}

\section{{Main Takeaways}}

\begin{{itemize}}
{takeaways}
\end{{itemize}}

\section{{Limitations}}

\begin{{itemize}}
\item Prediction market prices reflect collective beliefs and incentives, not guaranteed objective probabilities.
\item Some markets may be illiquid or noisy.
\item The current evaluation is descriptive rather than causal.
\item When live access is blocked, the workflow falls back to synthetic fixtures for demonstration.
\item News linkage is supportive context rather than proof of a direct causal driver.
\end{{itemize}}

\section{{Conclusion}}

Overall, the project delivers a feasible and replicable proof of concept for AI-enhanced business event forecasting with Polymarket-style data. It integrates market collection, business filtering, summary generation, descriptive analytics, resolved-market evaluation, news-assisted case studies, and paper-ready output generation in one workflow.

\end{{document}}
"""


def _render_news_section(news_digest: list[dict]) -> str:
    if not news_digest:
        return "No news-linked market context was generated for this run."
    sections = []
    for item in news_digest:
        lines = [
            f"### {item['question']}",
            f"- Category: {item['category']}",
            f"- News source: `{item['source']}`",
            f"- Query used: `{item['query']}`",
            f"- Digest: {item['digest']}",
        ]
        if item.get("articles"):
            for article in item["articles"]:
                title = article.get("title", "Untitled article")
                url = article.get("url") or ""
                source = article.get("source") or "unknown"
                if url:
                    lines.append(f"- Linked article: [{title}]({url}) ({source})")
                else:
                    lines.append(f"- Linked article: {title} ({source})")
        sections.append("\n".join(lines))
    return "\n\n".join(sections)


def _render_case_studies(case_studies: list[dict]) -> str:
    if not case_studies:
        return "No case studies were generated."
    parts = []
    for study in case_studies:
        lines = [
            f"### {study['question']}",
            f"- Category: {study['category']}",
            f"- Current probability: {_pct(study.get('probability'))}",
            f"- 1-day move: {_pp(study.get('one_day_price_change'))}",
            f"- 1-week move: {_pp(study.get('one_week_price_change'))}",
            f"- Market interpretation: {study['summary']}",
            f"- Business relevance: {study['why_it_matters']}",
        ]
        linked_news = study.get("linked_news") or []
        for article in linked_news:
            title = article.get("title", "Untitled article")
            url = article.get("url") or ""
            if url:
                lines.append(f"- Related headline: [{title}]({url})")
            else:
                lines.append(f"- Related headline: {title}")
        parts.append("\n".join(lines))
    return "\n\n".join(parts)


def _pct(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value * 100:.1f}%"


def _pp(value: float | None) -> str:
    if value is None:
        return "n/a"
    sign = "+" if value >= 0 else ""
    return f"{sign}{value * 100:.1f}pp"


def _bullet_list(items: list[str]) -> str:
    if not items:
        return "- No summary takeaways were generated."
    return "\n".join(f"- {item}" for item in items)


def latex_escape(text: str) -> str:
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    escaped = []
    for char in text:
        escaped.append(replacements.get(char, char))
    return "".join(escaped)


def _news_item_tex(item: dict) -> str:
    base = (
        f"\\item \\textbf{{{latex_escape(item['question'])}}} "
        f"({latex_escape(item['category'])}). {latex_escape(item['digest'])}"
    )
    articles = item.get("articles") or []
    if not articles:
        return base
    article_text = "; ".join(
        f"{latex_escape(article.get('title', 'Untitled article'))} [{latex_escape(article.get('source', 'source'))}]"
        for article in articles[:2]
    )
    return base + f" Related coverage included {article_text}."


def _case_item_tex(item: dict) -> str:
    return (
        f"\\item \\textbf{{{latex_escape(item['question'])}}}. "
        f"Current probability: {latex_escape(_pct(item.get('probability')))}; "
        f"1-day move: {latex_escape(_pp(item.get('one_day_price_change')))}; "
        f"1-week move: {latex_escape(_pp(item.get('one_week_price_change')))}. "
        f"{latex_escape(item['summary'])}"
    )


def compile_latex(tex_path: Path) -> Path | None:
    engine = shutil.which("xelatex") or shutil.which("pdflatex")
    if not engine:
        return None
    command = [
        engine,
        "-interaction=nonstopmode",
        "-halt-on-error",
        tex_path.name,
    ]
    try:
        subprocess.run(command, cwd=tex_path.parent, check=True, capture_output=True, text=True)
        subprocess.run(command, cwd=tex_path.parent, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError:
        return None
    pdf_path = tex_path.with_suffix(".pdf")
    return pdf_path if pdf_path.exists() else None
