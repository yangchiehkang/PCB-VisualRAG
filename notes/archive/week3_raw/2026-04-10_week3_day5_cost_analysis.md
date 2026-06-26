# 2026-04-09 Day 5 Cost Analysis Log

## 今日目标
系统记录 Full Multi-vector 的成本，并与 Single-vector 做性能—代价对照分析。

---

## 1. 性能对比结果

### Single-vector
- MRR@10: 0.0000
- Recall@10: 0.0000
- nDCG@10: 0.0000
- Doc Recall@10: 0.7333

### Full Multi-vector
- MRR@10: 0.0644
- Recall@10: 0.1333
- nDCG@10: 0.0807
- Doc Recall@10: 0.9000

---

## 2. 成本对比结果

### Single-vector
- vectors per page: 1
- vector dim: 512
- estimated raw index size: 0.1973 MB
- avg query latency: 0.1130 ms

### Full Multi-vector
- vectors per page: 49
- vector dim: 512
- estimated raw index size: 9.6660 MB
- avg query latency: 6.5679 ms
- avg late interaction cost: 6.5452 ms

---

## 3. 成本比例分析
- vectors/page: **49.0x**
- index size: **49.0x**
- avg query latency: **58.1x**

---

## 4. 核心观察
1. Full MV 在 page-level retrieval 上明显优于 Single-vector。
2. Full MV 在 doc-level retrieval 上也优于 Single-vector。
3. Full MV 的额外成本主要来自 multi-vector late interaction scoring。
4. 性能提升是明确存在的，但成本增长也非常显著。

---

## 5. 结论链条
本日实验已经形成清晰论证：

- Full MV 的确更强；
- Full MV 也的确更贵；
- 且额外代价主要来自 token-level late interaction；
- 因此，后续研究 budgeted multi-vector optimization 是合理且必要的。

---

## 6. 输出文件
- `results/analysis/full_mv_cost_stats.csv`
- `results/analysis/single_vector_cost_stats.csv`
- `results/analysis/perf_cost_comparison.csv`
- `results/analysis/perf_cost_comparison_with_ratio.csv`
- `results/analysis/query_latency_details_full_mv.csv`
- `results/analysis/query_latency_details_single_vector.csv`

---

## 7. 一句话总结
今天完成了 Full MV 与 Single-vector 的第一版性能—代价分析，确认了 Full MV 虽然更有效，但需要付出约 49x 的表示成本和约 58x 的检索时延，因此 budgeted optimization 是后续工作的必要方向。
