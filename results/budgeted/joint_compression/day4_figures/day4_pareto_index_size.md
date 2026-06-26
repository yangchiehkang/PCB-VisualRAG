|   N |   M | Compression   |   Recall@10 |    MRR@10 |   nDCG@10 |   Index Size MB |   Latency ms/query | run_name              | label          | pareto_index_size   | pareto_latency   |
|----:|----:|:--------------|------------:|----------:|----------:|----------------:|-------------------:|:----------------------|:---------------|:--------------------|:-----------------|
|  10 |   8 | IVF+OPQ+PQ    |    0.266667 | 0.0553175 | 0.0990213 |      0.00616455 |            4.80393 | w6_N10_M8_ivf_opq_pq  | M8-IVF+OPQ+PQ  | True                | True             |
|  10 |  16 | IVF+OPQ+PQ    |    0.266667 | 0.077963  | 0.116206  |      0.0123291  |            5.70052 | w6_N10_M16_ivf_opq_pq | M16-IVF+OPQ+PQ | True                | False            |
|  10 |  24 | IVF+OPQ+PQ    |    0.266667 | 0.0956878 | 0.129585  |      0.0184937  |            5.40662 | w6_N10_M24_ivf_opq_pq | M24-IVF+OPQ+PQ | True                | True             |
