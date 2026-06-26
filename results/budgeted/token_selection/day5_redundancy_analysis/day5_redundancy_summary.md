# Week 5 Day 5 Redundancy Summary

## 1. Full-token Reference

- Full-token setting: M49
- Full avg tokens/page: 49.00
- Full payload size MB: 9.666016
- Full Recall@10: 0.266667
- Full MRR@10: 0.062778
- Full nDCG@10: 0.103290

## 2. Key Findings

- Best nDCG@10 setting: M8, nDCG@10=0.124865, redundancy ratio=83.67%
- Best MRR@10 setting: M8, MRR@10=0.090688, redundancy ratio=83.67%
- Fastest setting: M16, latency=1.637923 ms/query

## 3. Answer to Redundancy Questions

- M16 keeps 32.65% tokens and removes 67.35% tokens. It preserves 100.00% Recall@10 and 120.27% nDCG@10 compared with M49.
- M8 keeps 16.33% tokens and removes 83.67% tokens. It preserves 100.00% Recall@10 and 120.89% nDCG@10 compared with M49.
- The exact 10% token setting was not tested because the current M list starts from M8. Since M8 corresponds to 16.33% retained tokens, it is the closest tested strong-compression setting.
