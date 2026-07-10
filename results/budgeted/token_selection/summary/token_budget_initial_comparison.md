# Week 5 Day 3 Token Budget Initial Comparison

| Method            | M    |   Evaluated Queries |   Recall@1 |   Recall@5 |   Recall@10 |    MRR@10 |   nDCG@10 | Run File                                                      |   Latency ms/query |   Avg Candidates / Query |
|:------------------|:-----|--------------------:|-----------:|-----------:|------------:|----------:|----------:|:--------------------------------------------------------------|-------------------:|-------------------------:|
| Full Multi-vector | full |                  30 |  0.0333333 |  0.1       |    0.133333 | 0.0644444 | 0.0806665 | results\full_multivector\full_mv_run.tsv                      |          nan       |                      nan |
| Week4 C2F N10     | 49   |                  30 |  0.0333333 |  0.0333333 |    0.266667 | 0.0627778 | 0.10329   | results\budgeted\coarse_to_fine\c2f_single_vector_N10_run.tsv |          nan       |                      nan |
| C2F N10 M8        | 8    |                  30 |  0.0666667 |  0.0666667 |    0.266667 | 0.0906878 | 0.124865  | results\budgeted\token_selection\c2f_N10_M8_run.tsv           |            2.02491 |                       10 |
| C2F N10 M16       | 16   |                  30 |  0.0666667 |  0.0666667 |    0.266667 | 0.0901323 | 0.124232  | results\budgeted\token_selection\c2f_N10_M16_run.tsv          |            1.63792 |                       10 |
| C2F N10 M24       | 24   |                  30 |  0.0333333 |  0.1       |    0.266667 | 0.0754497 | 0.114467  | results\budgeted\token_selection\c2f_N10_M24_run.tsv          |            1.68456 |                       10 |
| C2F N10 M32       | 32   |                  30 |  0         |  0.1       |    0.266667 | 0.0464815 | 0.0919872 | results\budgeted\token_selection\c2f_N10_M32_run.tsv          |            1.81681 |                       10 |
| C2F N10 M49       | 49   |                  30 |  0.0333333 |  0.0333333 |    0.266667 | 0.0627778 | 0.10329   | results\budgeted\token_selection\c2f_N10_M49_run.tsv          |            2.38567 |                       10 |
