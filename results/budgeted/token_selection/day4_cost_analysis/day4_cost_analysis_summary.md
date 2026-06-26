# Week 5 Day 4 Token Budget Cost Analysis Summary

## 1. Full-token Reference

- Full-token setting: M49
- Full payload size MB: 9.666016
- Full total vectors: 4949
- Full avg tokens/page: 49.00
- Full nDCG@10: 0.103290
- Full MRR@10: 0.062778

## 2. Best Quality Settings

- Best nDCG@10: M8, nDCG@10=0.124865, payload reduction=83.67%
- Best MRR@10: M8, MRR@10=0.090688, payload reduction=83.67%

## 3. Best Cost Settings

- Smallest index: M8, payload size=1.578125 MB, payload reduction=83.67%
- Fastest reranking: M16, latency=1.637923 ms/query

## 4. Compact Table

| M | Avg Tokens/Page | Total Vectors | Payload Size MB | Payload Reduction % | Recall@10 | MRR@10 | nDCG@10 | Latency ms/query |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 8 | 8.00 | 808 | 1.578125 | 83.67 | 0.2667 | 0.0907 | 0.1249 | 2.0249 |
| 16 | 16.00 | 1616 | 3.156250 | 67.35 | 0.2667 | 0.0901 | 0.1242 | 1.6379 |
| 24 | 24.00 | 2424 | 4.734375 | 51.02 | 0.2667 | 0.0754 | 0.1145 | 1.6846 |
| 32 | 32.00 | 3232 | 6.312500 | 34.69 | 0.2667 | 0.0465 | 0.0920 | 1.8168 |
| 49 | 49.00 | 4949 | 9.666016 | 0.00 | 0.2667 | 0.0628 | 0.1033 | 2.3857 |
