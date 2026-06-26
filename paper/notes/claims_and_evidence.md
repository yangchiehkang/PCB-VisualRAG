# Claims and Evidence

## Main Claim

This work proposes a budget-aware VisualRAG retrieval framework for PCB documents. While OCR-based BM25 remains a strong overall baseline, visual multi-vector retrieval and hybrid fusion provide complementary evidence-aware retrieval signals.

## Supported Claims

| Claim | Evidence | Source |
|---|---|---|
| BM25 remains a strong overall baseline | Highest main retrieval nDCG@10 | Week 7 Table 14 |
| Hybrid Fusion matches BM25 on evidence retrieval | Evidence Hit@5 = 1.0000, Evidence Hit@10 = 1.0000 | Week 7 Table 16 |
| Hybrid Fusion improves region-level localization | Region Hit@5 = 0.4000 | Week 7 Region Hit |
| Gold evidence region is causally important | Gold Mask score drops to 0.00000000 | Week 7 Table 17 |
| Downstream QA should reflect evidence quality | To be validated | Week 8 Visual RAG |

## Claims to Avoid

- Do not claim that the visual method universally outperforms BM25.
- Do not claim end-to-end model training.
- Do not claim full automatic answer evaluation if manual scoring is used.