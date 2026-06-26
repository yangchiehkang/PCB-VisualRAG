# Week 6 Day 4 Figure Captions

## Figure 1: Quality vs. Index Size

This figure shows the relationship between retrieval quality, measured by nDCG@10, and estimated index size. Each point represents one joint budget configuration. Compressed configurations substantially reduce storage cost while preserving competitive retrieval quality.

## Figure 2: Quality vs. Retrieval Latency

This figure compares retrieval quality against per-query reranking latency. The plot highlights which compressed budget settings provide favorable speed-quality trade-offs under the current reconstructed-embedding reranking pipeline.

## Figure 3: Pareto Frontier

This figure marks configurations that are not dominated by another configuration with both lower cost and higher retrieval quality. Separate frontiers are shown for index size and latency.

## Key Configurations

| Category                | run_name              |   N |   M | Compression   |   Recall@10 |    MRR@10 |   nDCG@10 |   Index Size MB |   Latency ms/query |
|:------------------------|:----------------------|----:|----:|:--------------|------------:|----------:|----------:|----------------:|-------------------:|
| Closest to best quality | w6_N10_M24_ivf_opq_pq |  10 |  24 | IVF+OPQ+PQ    |    0.266667 | 0.0956878 | 0.129585  |      0.0184937  |            5.40662 |
| Lowest cost             | w6_N10_M8_ivf_opq_pq  |  10 |   8 | IVF+OPQ+PQ    |    0.266667 | 0.0553175 | 0.0990213 |      0.00616455 |            4.80393 |
| Best trade-off          | w6_N10_M24_pq         |  10 |  24 | PQ            |    0.266667 | 0.0889286 | 0.12546   |      0.0184937  |            5.10507 |

## Pareto Frontier: Index Size

| run_name              |   N |   M | Compression   |   Recall@10 |    MRR@10 |   nDCG@10 |   Index Size MB |   Latency ms/query |
|:----------------------|----:|----:|:--------------|------------:|----------:|----------:|----------------:|-------------------:|
| w6_N10_M8_ivf_opq_pq  |  10 |   8 | IVF+OPQ+PQ    |    0.266667 | 0.0553175 | 0.0990213 |      0.00616455 |            4.80393 |
| w6_N10_M16_ivf_opq_pq |  10 |  16 | IVF+OPQ+PQ    |    0.266667 | 0.077963  | 0.116206  |      0.0123291  |            5.70052 |
| w6_N10_M24_ivf_opq_pq |  10 |  24 | IVF+OPQ+PQ    |    0.266667 | 0.0956878 | 0.129585  |      0.0184937  |            5.40662 |

## Pareto Frontier: Latency

| run_name              |   N |   M | Compression   |   Recall@10 |    MRR@10 |   nDCG@10 |   Index Size MB |   Latency ms/query |
|:----------------------|----:|----:|:--------------|------------:|----------:|----------:|----------------:|-------------------:|
| w6_N10_M8_ivf_opq_pq  |  10 |   8 | IVF+OPQ+PQ    |    0.266667 | 0.0553175 | 0.0990213 |      0.00616455 |            4.80393 |
| w6_N10_M8_none        |  10 |   8 | nan           |    0.266667 | 0.0906878 | 0.124865  |      1.57812    |            4.87238 |
| w6_N10_M24_pq         |  10 |  24 | PQ            |    0.266667 | 0.0889286 | 0.12546   |      0.0184937  |            5.10507 |
| w6_N10_M24_ivf_opq_pq |  10 |  24 | IVF+OPQ+PQ    |    0.266667 | 0.0956878 | 0.129585  |      0.0184937  |            5.40662 |
