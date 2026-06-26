# Week 6 Day 3 Representative Points

| Category                | run_name              |   N |   M | Compression   |   Recall@10 |    MRR@10 |   nDCG@10 |   Index Size MB |   Latency ms/query |
|:------------------------|:----------------------|----:|----:|:--------------|------------:|----------:|----------:|----------------:|-------------------:|
| Closest to best quality | w6_N10_M24_ivf_opq_pq |  10 |  24 | IVF+OPQ+PQ    |    0.266667 | 0.0956878 | 0.129585  |      0.0184937  |            5.40662 |
| Lowest cost             | w6_N10_M8_ivf_opq_pq  |  10 |   8 | IVF+OPQ+PQ    |    0.266667 | 0.0553175 | 0.0990213 |      0.00616455 |            4.80393 |
| Best trade-off          | w6_N10_M24_pq         |  10 |  24 | PQ            |    0.266667 | 0.0889286 | 0.12546   |      0.0184937  |            5.10507 |
