# Day 5 Summary: Baseline Comparison and Query-Type Analysis

## Overall Outcome
Day 5 focused on consolidating the three completed retrieval baselines:
- OCR + BM25
- OCR + Dense
- Single-vector Visual

The automatic summary tables show that text-based retrieval remains substantially stronger than the pure visual baseline overall.
Among the completed methods, OCR + BM25 is the strongest standalone baseline, with OCR + Dense ranking second.
Single-vector Visual retrieval performs noticeably worse across global metrics.

## Query-Type Findings
The query-type analysis provides a more nuanced picture.

For component localization queries, BM25 fails completely, while OCR + Dense and Single-vector Visual both recover some relevant pages.
This suggests that component-oriented retrieval may benefit from semantic or visual signals beyond exact lexical matching.
However, Dense still slightly outperforms Visual in ranking quality, so the current visual baseline is not yet strong enough to serve as a better standalone method.

For cross-page consistency queries, OCR + BM25 and OCR + Dense clearly outperform the visual baseline.
This indicates that text signals remain more reliable for queries requiring semantic matching across pages.

Overall, the strongest method across query types is still usually a text-based retriever.
Visual retrieval shows limited but potentially meaningful value in some structure- or localization-related cases.

## Interpretation
The current evidence does not support the claim that pure visual retrieval is more robust than text retrieval for PCB manual page retrieval.
Instead, the results are more consistent with a complementarity hypothesis:
- text retrieval is the strongest standalone baseline;
- visual retrieval is weak in its current global-page embedding form;
- visual signals may still contribute useful auxiliary information in multimodal fusion or reranking.

## Practical Outcome of Day 5
The Day 5 automation script successfully generated:
- baseline summary tables
- per-query-type comparison tables
- query-type frequency counts
- strongest-method-by-type summary

These outputs are ready to be used in the experimental analysis section of the paper.
