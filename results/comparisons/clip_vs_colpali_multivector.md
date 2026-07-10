# CLIP vs ColPali — Full Multi-Vector (Late Interaction) Retrieval

Encoder swap for the visual multi-vector retriever: **CLIP → ColPali v1.3**, everything
downstream unchanged (same MaxSim scoring script, same run format, same qrels, same
evaluation script, same `topk=10`).

## Apples-to-apples setup

- **Same corpus scale:** all methods evaluated on the **full 101-page** corpus / **30 queries**.
- **Same evaluation:** `scripts/evaluation/eval_full_multivector_run.py`, same `data/metadata/qrels.tsv`, page-level metrics, k=10.
- **Same scoring:** `cosine_sum_maxsim` = `sum_i max_j (q_i · p_j)`.
  - CLIP: token vectors are L2-normalized → dot product = cosine MaxSim.
  - ColPali: token vectors are the model's **native (un-normalized)** output → native dot-product MaxSim
    (ColPali's designed scoring; its output is already ~unit-norm internally). No extra normalization applied.

## Results (page-level, k=10)

| Method          | #pages | #queries | Recall@1 | Recall@5 | Recall@10 | MRR@10 | nDCG@10 |
|-----------------|:------:|:--------:|:--------:|:--------:|:---------:|:------:|:-------:|
| CLIP Full MV    |  101   |    30    |  0.0333  |  0.1000  |  0.1333   | 0.0644 | 0.0807  |
| ColPali Full MV |  101   |    30    |  0.4333  |  0.8333  |  0.9333   | 0.6228 | 0.6832  |
| BM25 (reference)|  101   |    30    |   n/a    |   n/a    |  0.8833   |  n/a   | 0.5241  |

BM25 numbers are the project's known baseline (only Recall@10 and nDCG@10 available here);
n/a = not available in the provided reference, not zero.

## Reading of the numbers (page-level)

- **ColPali vs CLIP:** ColPali improves Recall@10 from 0.1333 to 0.9333 (**+0.80 absolute, ~7.0×**)
  and nDCG@10 from 0.0807 to 0.6832 (**~8.5×**); MRR@10 rises from 0.0644 to 0.6228. The gain is
  consistent across all cutoffs (Recall@1: 0.0333 → 0.4333). This is the expected direction: ColPali
  is trained with a late-interaction objective and token-level alignment, whereas raw CLIP tokens are not.
- **ColPali vs BM25:** ColPali now **surpasses** the BM25 reference on both available metrics —
  Recall@10 0.9333 vs 0.8833 (**+0.05**) and nDCG@10 0.6832 vs 0.5241 (**+0.159**). Under CLIP the
  visual multi-vector retriever was far below BM25; after the encoder swap the gap is not just closed but reversed.

Auxiliary (not the headline metric): ColPali document-level Recall@10 = 1.0 vs CLIP 0.90.

## Provenance

- CLIP run: `results/full_multivector/full_mv_run.tsv` (reused; matches README Recall@10 = 0.1333).
- ColPali run: `results/colpali_multivector/colpali_mv_run.tsv` (model `vidore/colpali-v1.3`, MPS).
- ColPali metrics: `results/colpali_multivector/colpali_mv_metrics.json`.
