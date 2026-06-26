# Day 5 Initial Conclusion

## Overall Comparison
The strongest overall baseline is **OCR + BM25** based on MRR.

Overall method ranking:
1. **OCR + BM25** — Recall@1=0.1333, Recall@5=0.6833, Recall@10=0.8833, MRR=0.4105, nDCG@10=0.5241
2. **OCR + Dense** — Recall@1=0.1000, Recall@5=0.6000, Recall@10=0.8000, MRR=0.3358, nDCG@10=0.4420
3. **Single-vector Visual** — Recall@1=0.0000, Recall@5=0.0833, Recall@10=0.2500, MRR=0.0664, nDCG@10=0.1041

## Query Type Distribution
- **component_localization**: 2 queries
- **cross_page_consistency**: 4 queries
- **parameter_lookup**: 2 queries
- **similarity_based_interference**: 17 queries
- **structure_legend_interpretation**: 5 queries

## Query-Type-Level Findings
The strongest baseline by query type is:
- **component_localization**: OCR + Dense is strongest (MRR=0.0714, Recall@10=0.5000, nDCG@10=0.1667).
- **cross_page_consistency**: OCR + BM25 is strongest (MRR=0.3611, Recall@10=0.7500, nDCG@10=0.4171).
- **parameter_lookup**: OCR + BM25 is strongest (MRR=0.5000, Recall@10=1.0000, nDCG@10=0.6309).
- **similarity_based_interference**: OCR + BM25 is strongest (MRR=0.4080, Recall@10=1.0000, nDCG@10=0.5514).
- **structure_legend_interpretation**: OCR + BM25 is strongest (MRR=0.5867, Recall@10=1.0000, nDCG@10=0.6840).

## Interpretation
The current evidence does not support a strong claim that pure visual retrieval is more robust than OCR/text retrieval.
Instead, the current results better support a complementarity narrative:
- OCR + BM25 is the strongest first-stage baseline overall.
- OCR + Dense is competitive but remains below BM25.
- Single-vector Visual is substantially weaker as a standalone retriever.
- Visual information may still be useful as an auxiliary signal in multimodal fusion or reranking.

## Paper Narrative Direction
At this stage, the most defensible paper narrative is:
- Text retrieval is the strongest standalone baseline.
- Pure visual retrieval is weak in its current global-page embedding form.
- Text and visual signals are better framed as complementary rather than substitutive.
