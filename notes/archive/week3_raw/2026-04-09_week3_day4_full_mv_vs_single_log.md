# 2026-04-09 Day 4 Full MV vs Single-vector Log

## 今日目标
在正式实验规模上运行 Full Multi-vector Retrieval，并与 Single-vector baseline 做第一次系统对比。

---

## 今日完成内容

### 1. Full Multi-vector 正式实验运行完成
- 使用全 query 集和正式 page 库运行 Full MV retrieval
- 成功生成：
  - `results/full_multivector/full_mv_run.tsv`
  - `results/full_multivector/full_mv_metrics.json`

### 2. Full MV 正式实验结果
#### Page-level
- MRR@10 = 0.0644
- Recall@1 = 0.0333
- Recall@5 = 0.1000
- Recall@10 = 0.1333
- nDCG@10 = 0.0807

#### Doc-level (aux)
- Recall@1 = 0.7333
- Recall@5 = 0.9000
- Recall@10 = 0.9000

### 3. Single-vector baseline 构建完成
- 基于同一套 projected embeddings 构建 single-vector baseline
- 方法为：
  - query token mean pooling
  - page token mean pooling
  - cosine / dot-product 排序
- 成功生成：
  - `results/single_vector/single_vector_run.tsv`
  - `results/single_vector/single_vector_metrics.json`

### 4. Single-vector 结果
#### Page-level
- MRR@10 = 0.0000
- Recall@1 = 0.0000
- Recall@5 = 0.0000
- Recall@10 = 0.0000
- nDCG@10 = 0.0000

#### Doc-level (aux)
- Recall@1 = 0.0333
- Recall@5 = 0.7000
- Recall@10 = 0.7333

### 5. Full MV vs Single-vector 对比完成
- 成功生成：
  - `results/comparisons/full_vs_single_preliminary.csv`
  - `results/comparisons/full_vs_single_query_level.csv`

对比结果显示：

| Metric | Full MV | Single-vector | Delta |
|---|---:|---:|---:|
| MRR@10 | 0.0644 | 0.0000 | +0.0644 |
| Recall@1 | 0.0333 | 0.0000 | +0.0333 |
| Recall@5 | 0.1000 | 0.0000 | +0.1000 |
| Recall@10 | 0.1333 | 0.0000 | +0.1333 |
| nDCG@10 | 0.0807 | 0.0000 | +0.0807 |
| Doc Recall@1 | 0.7333 | 0.0333 | +0.7000 |
| Doc Recall@5 | 0.9000 | 0.7000 | +0.2000 |
| Doc Recall@10 | 0.9000 | 0.7333 | +0.1667 |

---

## 当前结论
在当前正式实验设置下，**Full Multi-vector 明显优于 Single-vector baseline**。

这表明：
- token-level late interaction 比 mean-pooled global vector 更能保留有效检索信号；
- Full MV 不仅在页级结果上更好，在文档级召回上也明显更强；
- Full MV 值得继续作为主方法推进，并进一步探索 budget 化版本。

---

## 输出文件
- `results/full_multivector/full_mv_run.tsv`
- `results/full_multivector/full_mv_metrics.json`
- `results/single_vector/single_vector_run.tsv`
- `results/single_vector/single_vector_metrics.json`
- `results/comparisons/full_vs_single_preliminary.csv`
- `results/comparisons/full_vs_single_query_level.csv`

---

## 下一步计划
1. 分析哪些 query 类型从 Full MV 中受益最大
2. 抽查 Full MV 命中而 Single-vector 失败的代表性 case
3. 开始设计 budgeted multi-vector 版本
4. 继续考虑 global + local fusion 或 doc-first/page-second 方案

---

## 一句话总结
今天完成了 Full Multi-vector 与 Single-vector 的第一次正式对比，并得到关键初步结论：**Full Multi-vector 明显更强，值得继续深入。**
