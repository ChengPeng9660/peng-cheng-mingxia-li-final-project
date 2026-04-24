# Final Project Report: AI-Enhanced Business Event Forecasting Using Polymarket

Generated at: 2026-04-23T12:43:39.321702+00:00

> Note: this report was generated from the bundled synthetic fixture dataset because the current environment could not access live Polymarket data.

## 1. Project Objective

This project evaluates whether AI can improve the usefulness of Polymarket-style prediction market probabilities for business research. The implemented pipeline collects market records, filters for business-relevant topics, produces AI-assisted summaries, links major market moves to topical news coverage, and generates descriptive and resolved-market evaluation outputs.

## 2. Data and Implementation

- Market source used in this run: `fixture`
- Total markets analyzed: `20`
- Business-relevant markets: `15`
- Active relevant markets: `9`
- Resolved relevant markets: `6`

The system currently supports two enrichment modes:

- `heuristic`: keyword-based business classification and summary generation
- `openai`: optional LLM-based enrichment when `OPENAI_API_KEY` is available

## 3. Descriptive Findings

- Share of markets identified as business-relevant: `75.0%`
- Average absolute 1-day move for active relevant markets: `+2.1pp`
- Average absolute 1-week move for active relevant markets: `+8.4pp`
- Average relevance score: `0.7711`

### Category distribution

| Category | Count |
| --- | ---: |
| Macro / Regulation | 8 |
| Business / Finance | 6 |
| AI / Technology | 1 |

### Top relevant active markets

| Market | Category | Implied probability | 1-week move |
| --- | --- | ---: | ---: |
| Will OpenAI publicly launch GPT-5 before October 1, 2026? | AI / Technology | 71.0% | +14.0pp |
| Will the Fed cut rates by September 2026? | Macro / Regulation | 57.0% | +8.0pp |
| Will the FTC block a major Big Tech acquisition in 2026? | Macro / Regulation | 52.0% | +5.0pp |
| Will the U.S. expand AI chip export controls before the end of 2026? | Macro / Regulation | 62.0% | +9.0pp |
| Will Apple reach a $4 trillion market cap by December 31, 2026? | Business / Finance | 46.0% | +6.0pp |

## 4. Research Question Assessment

### RQ1. Do Polymarket probabilities provide meaningful forward-looking signals for business-related events?

This run evaluated `6` resolved binary business-related markets. The prototype produced directional accuracy of `100.0%` and a Brier score of `0.1156`. These results suggest that pre-resolution probabilities can contain usable forward-looking information, although the current sample remains small and exploratory.

### RQ2. Can an AI pipeline automatically identify and summarize relevant markets in a way that improves interpretability for business users?

Yes. The pipeline automatically classified relevant markets into business, AI/technology, and macro/regulation groups, then generated short summaries explaining why each market matters from a business perspective. The dashboard and CSV outputs convert raw market questions into a more structured research dataset.

### RQ3. Are large changes in Polymarket probabilities associated with major news developments before final resolution?

The pipeline identifies high-movement markets and attaches linked headline context when available. This does not establish causality, but it creates a practical workflow for event study style follow-up on sudden shifts in expectations.

## 5. News-Linked Market Context

### Will OpenAI publicly launch GPT-5 before October 1, 2026?
- Category: AI / Technology
- News source: `fixture`
- Query used: `("OpenAI" OR "GPT-5" OR "Gpt")`
- Digest: Recent coverage is centered on: Enterprise buyers accelerate spending plans ahead of next-generation foundation models Also notable: Cloud providers prepare capacity upgrades as model launch expectations rise
- Linked article: [Enterprise buyers accelerate spending plans ahead of next-generation foundation models](https://example.com/news/openai-enterprise-buyers) (Example Business Desk)
- Linked article: [Cloud providers prepare capacity upgrades as model launch expectations rise](https://example.com/news/cloud-capacity-upgrades) (Example Tech Wire)

### Will U.S. spot Bitcoin ETF net inflows exceed $50B in 2026?
- Category: Business / Finance
- News source: `fixture`
- Query used: `("Bitcoin ETF" OR "Bitcoin" OR "ETF")`
- Digest: Recent coverage is centered on: Institutional allocators revisit digital-asset exposure after ETF inflow rebound Also notable: Wealth platforms expand Bitcoin ETF access as product demand broadens
- Linked article: [Institutional allocators revisit digital-asset exposure after ETF inflow rebound](https://example.com/news/etf-inflow-rebound) (Example Digital Assets)
- Linked article: [Wealth platforms expand Bitcoin ETF access as product demand broadens](https://example.com/news/wealth-platform-bitcoin-etf) (Example Asset Management)

### Will Nvidia close above $150 on June 30, 2026?
- Category: Business / Finance
- News source: `fixture`
- Query used: `("Nvidia")`
- Digest: Recent coverage is centered on: AI infrastructure capex outlook boosts semiconductor revenue expectations Also notable: Major hyperscalers guide to higher GPU deployment in second half of 2026
- Linked article: [AI infrastructure capex outlook boosts semiconductor revenue expectations](https://example.com/news/ai-capex-semiconductors) (Example Markets)
- Linked article: [Major hyperscalers guide to higher GPU deployment in second half of 2026](https://example.com/news/hyperscaler-gpu-deployment) (Example Technology Journal)

### Will the U.S. expand AI chip export controls before the end of 2026?
- Category: Macro / Regulation
- News source: `fixture`
- Query used: `("export controls" OR "AI chips" OR "Chips")`
- Digest: Recent coverage is centered on: Washington weighs tighter AI chip export rules as supply-chain risks deepen Also notable: Semiconductor firms model revenue exposure under broader export restrictions
- Linked article: [Washington weighs tighter AI chip export rules as supply-chain risks deepen](https://example.com/news/ai-chip-export-rules) (Example Policy Monitor)
- Linked article: [Semiconductor firms model revenue exposure under broader export restrictions](https://example.com/news/chip-firms-export-exposure) (Example Industry Journal)

## 6. Case Studies

### Will OpenAI publicly launch GPT-5 before October 1, 2026?
- Category: AI / Technology
- Current probability: 71.0%
- 1-day move: +4.0pp
- 1-week move: +14.0pp
- Market interpretation: Will OpenAI publicly launch GPT-5 before October 1, 2026? is classified as AI / Technology. The market implies 71.0% for Yes, with moves of +4.0pp over 1 day and +14.0pp over 1 week. It matters for business research because it captures technology adoption, AI competition, or semiconductor demand; matched cues include ai, openai, gpt.
- Business relevance: Marked as business-relevant because it tracks AI or technology developments with likely implications for capex, competition, or platform strategy, including ai, openai, gpt, model.
- Related headline: [Enterprise buyers accelerate spending plans ahead of next-generation foundation models](https://example.com/news/openai-enterprise-buyers)
- Related headline: [Cloud providers prepare capacity upgrades as model launch expectations rise](https://example.com/news/cloud-capacity-upgrades)

### Will U.S. spot Bitcoin ETF net inflows exceed $50B in 2026?
- Category: Business / Finance
- Current probability: 49.0%
- 1-day move: +5.0pp
- 1-week move: +12.0pp
- Market interpretation: Will U.S. spot Bitcoin ETF net inflows exceed $50B in 2026? is classified as Business / Finance. The market implies 49.0% for Yes, with moves of +5.0pp over 1 day and +12.0pp over 1 week. It matters for business research because it captures firm value, investor sentiment, or operating performance; matched cues include etf, bitcoin.
- Business relevance: Marked as business-relevant because it references company, asset-price, or corporate-performance signals such as etf, bitcoin.
- Related headline: [Institutional allocators revisit digital-asset exposure after ETF inflow rebound](https://example.com/news/etf-inflow-rebound)
- Related headline: [Wealth platforms expand Bitcoin ETF access as product demand broadens](https://example.com/news/wealth-platform-bitcoin-etf)

### Will Nvidia close above $150 on June 30, 2026?
- Category: Business / Finance
- Current probability: 64.0%
- 1-day move: +3.0pp
- 1-week move: +11.0pp
- Market interpretation: Will Nvidia close above $150 on June 30, 2026? is classified as Business / Finance. The market implies 64.0% for Yes, with moves of +3.0pp over 1 day and +11.0pp over 1 week. It matters for business research because it captures firm value, investor sentiment, or operating performance; matched cues include stock, nvidia.
- Business relevance: Marked as business-relevant because it references company, asset-price, or corporate-performance signals such as stock, nvidia.
- Related headline: [AI infrastructure capex outlook boosts semiconductor revenue expectations](https://example.com/news/ai-capex-semiconductors)
- Related headline: [Major hyperscalers guide to higher GPU deployment in second half of 2026](https://example.com/news/hyperscaler-gpu-deployment)

## 7. Main Takeaways

- 15 of 20 markets (75.0%) were identified as business-relevant.
- The largest relevant bucket was Macro / Regulation with 8 markets, suggesting the pipeline can separate corporate, AI, and policy themes.
- Among 6 resolved binary markets, the prototype produced directional accuracy of 100.0% and a Brier score of 0.116.
- The biggest active mover was 'Will OpenAI publicly launch GPT-5 before October 1, 2026?', which supports RQ3 by surfacing markets where sharp price changes deserve news-based case-study follow-up.

## 8. Limitations

- Prediction market prices are not guaranteed to be calibrated objective probabilities.
- Some markets may be thinly traded or noisy.
- The current evaluation is descriptive rather than causal.
- When live Polymarket access is blocked, offline fixture data is used instead.
- News linkage is supportive context, not proof that a specific article caused a market movement.

## 9. Conclusion

The implemented system delivers a feasible proof of concept for AI-enhanced business event forecasting with Polymarket-style data. It supports market collection, business filtering, summary generation, descriptive analysis, resolved-market evaluation, news-assisted case study development, and report/dashboard production in one reproducible workflow.
