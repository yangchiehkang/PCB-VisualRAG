# Week 6 Day 2 实验日志：基础压缩实验与 PQ / OPQ / IVF-PQ 流程验证

**Project:** PCB_VisualRAG_Project  
**Stage:** Week 6  
**Day:** Day 2  
**Date:** 2026-05-07  
**Experiment:** Quantized Budgeted Multi-vector Retrieval Pipeline Validation  
**Representative Budget:** N=10, M=16  
**Status:** Completed  

---

## 1. 今日目标

Week 6 Day 2 的目标是完成基础向量压缩检索流水线，并在一个代表性预算配置上跑通多种压缩方式。

原计划建议使用中间预算点：

```text
N=50, M=64
```

但根据当前真实实验环境，Week 6 Day 1 已确认：

```text
当前 coarse candidates 仅支持 N=10
当前每页 full token 数为 49
Week 5 最佳 trade-off token budget 为 M=16
```

因此 Day 2 实际采用代表配置：

```text
N=10, M=16
```

本日需要验证的压缩方式包括：

- PQ
- OPQ + PQ
- IVF + PQ
- IVF + OPQ + PQ

并确认以下流程是否正常：

- 压缩索引构建；
- 压缩后 embedding 输出；
- coarse-to-fine reranking；
- run 文件生成；
- evaluation 脚本兼容；
- latency 统计；
- pipeline validation summary 生成。

---

## 2. 今日输入与实验设置

### 2.1 输入文件

本日实验使用的主要输入包括：

```text
artifacts/embeddings/token_selection/pages_M16
artifacts/embeddings/full_multivector/queries
artifacts/rerank_cache/single_vector_topN/single_vector_candidates_top10.tsv
data/metadata/qrels.tsv
```

### 2.2 数据规模

从压缩构建脚本输出可知：

| Item | Value |
|---|---:|
| Num Pages | 101 |
| Tokens per Page | 16 |
| Total Vectors | 1616 |
| Embedding Dim | 512 |
| Original FP File Size | 3.1686 MB |
| Original FP Payload Size | 3.1563 MB |

### 2.3 压缩参数

Day 2 为小规模通路验证，因此采用较稳定的 4-bit PQ 设置：

| Parameter | Value |
|---|---:|
| pq_m | 16 |
| bits | 4 |
| nlist | 8 |
| nprobe | 4 |

每个向量的估算 PQ code size 为：

```text
16 subquantizers × 4 bits = 64 bits = 8 bytes/vector
```

总压缩码本体积估算为：

```text
0.012329 MB
```

相对原始 float32 payload 的压缩倍率约为：

```text
256×
```

---

## 3. 今日完成的脚本与产物

### 3.1 压缩索引构建脚本

已完成并运行：

```text
scripts/compression/build_week6_quantized_embeddings_day2.py
```

该脚本完成了以下输出：

```text
artifacts/embeddings/joint_compression/pages_M16_pq
artifacts/embeddings/joint_compression/pages_M16_opq_pq
artifacts/embeddings/joint_compression/pages_M16_ivf_pq
artifacts/embeddings/joint_compression/pages_M16_ivf_opq_pq
```

同时生成 index stats：

```text
results/budgeted/joint_compression/index_stats/w6_N10_M16_pq_index_stats.json
results/budgeted/joint_compression/index_stats/w6_N10_M16_opq_pq_index_stats.json
results/budgeted/joint_compression/index_stats/w6_N10_M16_ivf_pq_index_stats.json
results/budgeted/joint_compression/index_stats/w6_N10_M16_ivf_opq_pq_index_stats.json
```

汇总文件：

```text
results/budgeted/joint_compression/day2_validation/day2_quantization_build_summary.csv
results/budgeted/joint_compression/day2_validation/day2_quantization_build_summary.md
```

---

### 3.2 Quantized C2F Reranking 脚本

已完成并运行：

```text
scripts/retrieval/run_week6_quantized_c2f_day2.py
```

该脚本完成了 5 个配置的 reranking：

```text
w6_N10_M16_none
w6_N10_M16_pq
w6_N10_M16_opq_pq
w6_N10_M16_ivf_pq
w6_N10_M16_ivf_opq_pq
```

生成 run 文件：

```text
results/budgeted/joint_compression/runs/w6_N10_M16_none_run.tsv
results/budgeted/joint_compression/runs/w6_N10_M16_pq_run.tsv
results/budgeted/joint_compression/runs/w6_N10_M16_opq_pq_run.tsv
results/budgeted/joint_compression/runs/w6_N10_M16_ivf_pq_run.tsv
results/budgeted/joint_compression/runs/w6_N10_M16_ivf_opq_pq_run.tsv
```

生成 latency 文件：

```text
results/budgeted/joint_compression/latency/w6_N10_M16_none_latency.json
results/budgeted/joint_compression/latency/w6_N10_M16_pq_latency.json
results/budgeted/joint_compression/latency/w6_N10_M16_opq_pq_latency.json
results/budgeted/joint_compression/latency/w6_N10_M16_ivf_pq_latency.json
results/budgeted/joint_compression/latency/w6_N10_M16_ivf_opq_pq_latency.json
```

汇总文件：

```text
results/budgeted/joint_compression/day2_validation/day2_quantized_rerank_latency.csv
results/budgeted/joint_compression/day2_validation/day2_quantized_rerank_latency.md
```

---

### 3.3 Evaluation 脚本

已完成并运行：

```text
scripts/evaluation/evaluate_week6_quantized_day2.py
```

生成评测文件：

```text
results/budgeted/joint_compression/day2_validation/day2_quantized_metrics.csv
results/budgeted/joint_compression/day2_validation/day2_quantized_metrics.md
```

同时生成每个 run 的 metrics JSON：

```text
results/budgeted/joint_compression/metrics/w6_N10_M16_none_metrics.json
results/budgeted/joint_compression/metrics/w6_N10_M16_pq_metrics.json
results/budgeted/joint_compression/metrics/w6_N10_M16_opq_pq_metrics.json
results/budgeted/joint_compression/metrics/w6_N10_M16_ivf_pq_metrics.json
results/budgeted/joint_compression/metrics/w6_N10_M16_ivf_opq_pq_metrics.json
```

---

### 3.4 Validation Summary 脚本

已完成并运行：

```text
scripts/analysis/summarize_week6_day2_validation.py
```

生成最终验收文件：

```text
results/budgeted/joint_compression/day2_validation/day2_compression_pipeline_validation.csv
results/budgeted/joint_compression/day2_validation/day2_compression_pipeline_validation.md
results/budgeted/joint_compression/day2_validation/day2_validation_summary.md
```

---

## 4. 今日主要实验结果

### 4.1 压缩构建结果

| Run Name | Compression | MSE | MAE | Estimated Code Size MB | Compression Ratio | Build Time sec |
|---|---|---:|---:|---:|---:|---:|
| w6_N10_M16_pq | PQ | 0.000472634 | 0.0169268 | 0.0123291 | 256× | 0.1200 |
| w6_N10_M16_opq_pq | OPQ+PQ | 0.000450466 | 0.0164834 | 0.0123291 | 256× | 17.0127 |
| w6_N10_M16_ivf_pq | IVF+PQ | 0.000439198 | 0.0163011 | 0.0123291 | 256× | 0.1593 |
| w6_N10_M16_ivf_opq_pq | IVF+OPQ+PQ | 0.000422250 | 0.0159488 | 0.0123291 | 256× | 16.5048 |

观察：

- 所有压缩索引均成功构建；
- 所有压缩配置的 estimated code size 均为 0.0123291 MB；
- 相对原始 float32 payload，估算压缩倍率为 256×；
- IVF+OPQ+PQ 的重建误差最低；
- OPQ 相关配置构建时间明显更高，主要来自 OPQ rotation training；
- 当前 reconstructed `.npy` 文件仅用于兼容现有 reranking pipeline，不代表真实压缩索引体积。

---

### 4.2 Reranking 与 Latency 结果

| Run Name | Compression | Valid Queries | Valid Candidates | Latency ms/query |
|---|---|---:|---:|---:|
| w6_N10_M16_none | None | 30 | 300 | 5.2517 |
| w6_N10_M16_pq | PQ | 30 | 300 | 5.4172 |
| w6_N10_M16_opq_pq | OPQ+PQ | 30 | 300 | 5.2228 |
| w6_N10_M16_ivf_pq | IVF+PQ | 30 | 300 | 5.4952 |
| w6_N10_M16_ivf_opq_pq | IVF+OPQ+PQ | 30 | 300 | 5.2117 |

观察：

- 所有配置均成功处理 30 个 query；
- 所有配置均成功 rerank 300 个 candidate；
- run 文件格式与前几周兼容；
- latency 统计逻辑正常；
- 当前实验使用 reconstructed embeddings 进行 late interaction，因此 latency 差异主要反映 pipeline 兼容性，而不是严格的真实 IVF ANN 加速收益。

---

### 4.3 Retrieval Metrics 结果

| Run Name | Compression | Recall@10 | MRR@10 | nDCG@10 | Index Size MB | Latency ms/query |
|---|---|---:|---:|---:|---:|---:|
| w6_N10_M16_none | None | 0.266667 | 0.090132 | 0.124232 | 3.156250 | 5.2517 |
| w6_N10_M16_pq | PQ | 0.266667 | 0.065000 | 0.107177 | 0.012329 | 5.4172 |
| w6_N10_M16_opq_pq | OPQ+PQ | 0.266667 | 0.042315 | 0.088381 | 0.012329 | 5.2228 |
| w6_N10_M16_ivf_pq | IVF+PQ | 0.266667 | 0.065648 | 0.106069 | 0.012329 | 5.4952 |
| w6_N10_M16_ivf_opq_pq | IVF+OPQ+PQ | 0.266667 | 0.077963 | 0.116206 | 0.012329 | 5.2117 |

观察：

- 所有压缩方法均保持 Recall@10 = 0.266667；
- PQ 和 IVF+PQ 会降低 MRR@10 与 nDCG@10，但 Recall@10 保持不变；
- OPQ+PQ 的 MSE 低于 PQ，但排序质量并未优于 PQ；
- IVF+OPQ+PQ 在压缩配置中综合排序质量最好；
- IVF+OPQ+PQ 的 nDCG@10 = 0.116206，接近未压缩 N10 M16 的 nDCG@10 = 0.124232；
- 压缩后 estimated index size 从 3.156250 MB 降至 0.012329 MB，体积下降明显。

---

## 5. Day 2 压缩流程验收表

| Compression | Index Built | Run Output | Metrics OK | Latency OK |
|---|---|---|---|---|
| PQ | Completed | Completed | Completed | Completed |
| OPQ + PQ | Completed | Completed | Completed | Completed |
| IVF + PQ | Completed | Completed | Completed | Completed |
| IVF + OPQ + PQ | Completed | Completed | Completed | Completed |

Day 2 所有核心验收项均已完成。

---

## 6. 今日遇到的问题与处理

### 6.1 IVF reconstruct 报错

最初 IVF+PQ 在调用 `index.reconstruct(i)` 时出现 direct map 未初始化问题：

```text
direct map not initialized
```

处理方式：

- 在 IVF index 上调用 `index.make_direct_map()`；
- 添加 fallback reconstruction 逻辑；
- 修复后 IVF+PQ 与 IVF+OPQ+PQ 均可正常输出 reconstructed embeddings。

---

### 6.2 Candidate 文件表头被误读为 query

初次运行 reranking 时，candidate TSV 的表头被误读为真实 query：

```text
query_id
```

导致脚本尝试查找：

```text
query_id.npy
```

处理方式：

- 修改 candidate loader；
- 自动识别并移除 header-like row；
- 清洗后 candidate 数据恢复为：

```text
30 queries
300 candidates
10 candidates/query
```

---

### 6.3 OPQ 训练 warning

OPQ 相关配置中出现多次 FAISS warning：

```text
clustering 1616 points to 256 centroids: please provide at least 9984 training points
```

原因：

- 当前训练向量数为 1616；
- OPQ 内部训练阶段仍触发较多 256-centroid clustering；
- 数据量偏小，因此 FAISS 给出训练样本不足 warning。

影响：

- pipeline 仍成功完成；
- 输出 embedding、run、metrics、latency 均正常；
- 该 warning 需要在报告中标注为小数据设置下的训练稳定性提示；
- Day 3 批量实验可以继续使用当前配置，但 OPQ 结论需要谨慎解释。

---

## 7. 今日结论

Week 6 Day 2 已成功完成基础压缩检索流水线验证。在代表性预算配置 N=10, M=16 下，PQ、OPQ+PQ、IVF+PQ 和 IVF+OPQ+PQ 四种压缩方式均已成功构建索引、生成压缩后 embedding、完成 coarse-to-fine reranking，并输出兼容的 run 文件、metrics 文件和 latency 统计。

从结果看，所有压缩方法均保持了 Recall@10 = 0.266667，同时将 estimated index size 从 3.156250 MB 降至 0.012329 MB，达到约 256× 的估算压缩倍率。其中 IVF+OPQ+PQ 在压缩配置中取得了最好的综合排序质量，MRR@10 为 0.077963，nDCG@10 为 0.116206，接近未压缩配置的 nDCG@10 = 0.124232。

Day 2 验收标准已全部满足，当前压缩检索管线可稳定运行，可以进入 Week 6 Day 3 的批量联合预算实验。

---

## 8. 已完成文件清单

### Build Summary

```text
results/budgeted/joint_compression/day2_validation/day2_quantization_build_summary.csv
results/budgeted/joint_compression/day2_validation/day2_quantization_build_summary.md
```

### Reranking Latency

```text
results/budgeted/joint_compression/day2_validation/day2_quantized_rerank_latency.csv
results/budgeted/joint_compression/day2_validation/day2_quantized_rerank_latency.md
```

### Metrics

```text
results/budgeted/joint_compression/day2_validation/day2_quantized_metrics.csv
results/budgeted/joint_compression/day2_validation/day2_quantized_metrics.md
```

### Validation

```text
results/budgeted/joint_compression/day2_validation/day2_compression_pipeline_validation.csv
results/budgeted/joint_compression/day2_validation/day2_compression_pipeline_validation.md
results/budgeted/joint_compression/day2_validation/day2_validation_summary.md
```

### Quantized Embeddings

```text
artifacts/embeddings/joint_compression/pages_M16_pq
artifacts/embeddings/joint_compression/pages_M16_opq_pq
artifacts/embeddings/joint_compression/pages_M16_ivf_pq
artifacts/embeddings/joint_compression/pages_M16_ivf_opq_pq
```

### Run Files

```text
results/budgeted/joint_compression/runs/w6_N10_M16_none_run.tsv
results/budgeted/joint_compression/runs/w6_N10_M16_pq_run.tsv
results/budgeted/joint_compression/runs/w6_N10_M16_opq_pq_run.tsv
results/budgeted/joint_compression/runs/w6_N10_M16_ivf_pq_run.tsv
results/budgeted/joint_compression/runs/w6_N10_M16_ivf_opq_pq_run.tsv
```

---

## 9. Day 2 验收状态

| Requirement | Status |
|---|---|
| 基础 PQ 压缩流程可运行 | Completed |
| OPQ + PQ 流程可运行 | Completed |
| IVF + PQ 流程可运行 | Completed |
| IVF + OPQ + PQ 流程可运行 | Completed |
| 压缩后结果可正常输出 | Completed |
| run 文件格式兼容 | Completed |
| evaluation 脚本兼容 | Completed |
| latency 统计逻辑正常 | Completed |
| 可进入批量联合实验 | Completed |
