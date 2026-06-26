# Week 6 Day 5 Budget Triplet Analysis Note

## 1. Budget Dimension Impact

| Budget Dimension   | Current Evidence                                                  | Observed Risk                                                                             | Analysis Focus                                            | Current Conclusion                                                                      |
|:-------------------|:------------------------------------------------------------------|:------------------------------------------------------------------------------------------|:----------------------------------------------------------|:----------------------------------------------------------------------------------------|
| N                  | N fixed at 10 in Day 3 because available candidate file is top10. | Coarse-stage recall ceiling is controlled by whether gold pages enter the candidate pool. | Use candidate-level gold coverage as N sensitivity proxy. | N is the first-order budget because missed gold pages cannot be recovered by reranking. |
| M                  | M values tested: [8, 16, 24]                                      | Small M may remove fine-grained local evidence.                                           | Compare per-query nDCG changes across M8, M16, M24.       | Best uncompressed M point is M=8, nDCG@10=0.124865.                                     |
| bits               | bits tested: 2, 4, 8                                              | Low bits may distort similarity ranking.                                                  | Compare PQ-b2, PQ-b4, PQ-b8 at fixed N=10 and M=24.       | Best bits setting is b=4, nDCG@10=0.125460.                                             |

## 2. M Group Summary

|   M | Best Quality Run      | Best Quality Compression   |   Best nDCG@10 |   Best MRR@10 |   Best Index Size MB |   Best Latency ms/query | Lowest Cost Run      | Lowest Cost Compression   |   Lowest Cost Index Size MB |   None nDCG@10 |
|----:|:----------------------|:---------------------------|---------------:|--------------:|---------------------:|------------------------:|:---------------------|:--------------------------|----------------------------:|---------------:|
|   8 | w6_N10_M8_none        | None                       |       0.124865 |     0.0906878 |            1.57812   |                 4.87238 | w6_N10_M8_ivf_opq_pq | IVF+OPQ+PQ                |                  0.00616455 |       0.124865 |
|  16 | w6_N10_M16_none       | None                       |       0.124232 |     0.0901323 |            3.15625   |                 5.01538 | w6_N10_M16_pq        | PQ                        |                  0.0123291  |       0.124232 |
|  24 | w6_N10_M24_ivf_opq_pq | IVF+OPQ+PQ                 |       0.129585 |     0.0956878 |            0.0184937 |                 5.40662 | w6_N10_M24_opq_pq    | OPQ+PQ                    |                  0.0184937  |       0.114467 |

## 3. Compression Delta vs None

|   M | Compression   | run_name              |   Delta Recall@10 vs None |   Delta MRR@10 vs None |   Delta nDCG@10 vs None |   Index Size Ratio vs None |   Latency Delta ms/query vs None |
|----:|:--------------|:----------------------|--------------------------:|-----------------------:|------------------------:|---------------------------:|---------------------------------:|
|   8 | PQ            | w6_N10_M8_pq          |                         0 |            -0.0403175  |             -0.0299739  |                 0.00390625 |                        0.0235955 |
|   8 | OPQ+PQ        | w6_N10_M8_opq_pq      |                         0 |            -0.0480556  |             -0.0360534  |                 0.00390625 |                        0.0187794 |
|   8 | IVF+PQ        | w6_N10_M8_ivf_pq      |                         0 |            -0.0377778  |             -0.0279475  |                 0.00390625 |                       -0.0641346 |
|   8 | IVF+OPQ+PQ    | w6_N10_M8_ivf_opq_pq  |                         0 |            -0.0353704  |             -0.0258433  |                 0.00390625 |                       -0.06845   |
|  16 | PQ            | w6_N10_M16_pq         |                         0 |            -0.0251323  |             -0.0170556  |                 0.00390625 |                       -0.0628551 |
|  16 | OPQ+PQ        | w6_N10_M16_opq_pq     |                         0 |            -0.0478175  |             -0.0358516  |                 0.00390625 |                       -0.0352383 |
|  16 | IVF+PQ        | w6_N10_M16_ivf_pq     |                         0 |            -0.0244841  |             -0.0181634  |                 0.00390625 |                        0.698209  |
|  16 | IVF+OPQ+PQ    | w6_N10_M16_ivf_opq_pq |                         0 |            -0.0121693  |             -0.00802636 |                 0.00390625 |                        0.685143  |
|  24 | PQ            | w6_N10_M24_pq         |                         0 |             0.0134788  |              0.0109938  |                 0.00390625 |                       -0.212638  |
|  24 | OPQ+PQ        | w6_N10_M24_opq_pq     |                         0 |             0.00681217 |              0.00560795 |                 0.00390625 |                       -0.311406  |
|  24 | IVF+PQ        | w6_N10_M24_ivf_pq     |                         0 |            -0.00291005 |             -0.00242523 |                 0.00390625 |                       -0.217859  |
|  24 | IVF+OPQ+PQ    | w6_N10_M24_ivf_opq_pq |                         0 |             0.0202381  |              0.0151183  |                 0.00390625 |                        0.0889142 |

## 4. Bits Sensitivity

| run_name         |   N |   M | Compression   |   bits |   evaluated_queries |   missing_run_queries |   Recall@1 |   Recall@5 |   Recall@10 |    MRR@10 |   nDCG@10 |   Index Size MB |   Original FP Payload Size MB |   Compression Ratio vs FP Payload |         MSE |       MAE |   Build Time sec |   Latency ms/query |   Rerank Time sec | run_file                                                         | index_stats_file                                                                 |   Delta nDCG@10 vs b4 |   Delta MRR@10 vs b4 |   Index Size Ratio vs b4 |   MSE Ratio vs b4 |
|:-----------------|----:|----:|:--------------|-------:|--------------------:|----------------------:|-----------:|-----------:|------------:|----------:|----------:|----------------:|------------------------------:|----------------------------------:|------------:|----------:|-----------------:|-------------------:|------------------:|:-----------------------------------------------------------------|:---------------------------------------------------------------------------------|----------------------:|---------------------:|-------------------------:|------------------:|
| w6_N10_M24_pq_b2 |  10 |  24 | PQ-b2         |      2 |                  30 |                     0 |  0         |   0.1      |    0.266667 | 0.0631481 |  0.105743 |      0.00924683 |                       4.73438 |                               512 | 0.000551798 | 0.0182663 |        0.0719864 |            5.06581 |          0.151974 | results\budgeted\joint_compression\runs\w6_N10_M24_pq_b2_run.tsv | results\budgeted\joint_compression\index_stats\w6_N10_M24_pq_b2_index_stats.json |            -0.0197177 |           -0.0257804 |                      0.5 |          1.20453  |
| w6_N10_M24_pq_b4 |  10 |  24 | PQ-b4         |      4 |                  30 |                     0 |  0.0333333 |   0.133333 |    0.266667 | 0.0889286 |  0.12546  |      0.0184937  |                       4.73438 |                               256 | 0.000458101 | 0.0166069 |        0.169007  |            4.90586 |          0.147176 | results\budgeted\joint_compression\runs\w6_N10_M24_pq_b4_run.tsv | results\budgeted\joint_compression\index_stats\w6_N10_M24_pq_b4_index_stats.json |             0         |            0         |                      1   |          1        |
| w6_N10_M24_pq_b8 |  10 |  24 | PQ-b8         |      8 |                  30 |                     0 |  0.0333333 |   0.1      |    0.266667 | 0.0739286 |  0.1134   |      0.0369873  |                       4.73438 |                               128 | 0.000279376 | 0.0127791 |        0.595178  |            5.27718 |          0.158315 | results\budgeted\joint_compression\runs\w6_N10_M24_pq_b8_run.tsv | results\budgeted\joint_compression\index_stats\w6_N10_M24_pq_b8_index_stats.json |            -0.012061  |           -0.015     |                      2   |          0.609858 |

## 5. Coarse Recall Ceiling

Coarse candidate recall ceiling at top10: 0.26666666666666666

## 6. Failure Case Summary

| failure_type                    |   count |
|:--------------------------------|--------:|
| large_budget_still_failure      |      20 |
| quantization_ranking_distortion |      20 |
| small_M_failure                 |       1 |
| small_N_or_coarse_miss          |      22 |

## 7. Main Takeaways

- N controls whether the gold page enters the candidate pool and therefore controls the recall ceiling.
- M controls how much fine-grained visual-token evidence is preserved for late interaction reranking.
- bits controls quantization fidelity and can change similarity ordering when too aggressive.
- In the current fixed-N setting, M24 with compression provides the strongest quality-cost trade-off.
- Coarse recall should be protected first, token evidence second, and compression strength tuned last.
