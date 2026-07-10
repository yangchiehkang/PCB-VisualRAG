# Week 7 Day 2 任务 1 实验日志：BM25 + Full MV Rerank

**日期**：2026-05-08  
**项目**：PCB_VisualRAG_Project  
**环境**：`pcb_visualrag`  
**工作目录**：`E:\Working\PCB_VisualRAG_Project`

---

## 1. 实验目标

本次 Day 2 任务 1 的目标是运行 **BM25 + Full Multi-vector Late Interaction Rerank** 流程。

整体流程如下：

```text
Query
↓
BM25 top-N candidate retrieval
↓
Full Multi-vector Late Interaction Reranking
↓
Final top-k pages
```

本任务测试的候选规模为：

$$
N \in \{10, 20, 50, 100\}
$$

目标输出文件为：

```text
results\week7\c2f_fixed_N\bm25_fullmv_N10_run.tsv
results\week7\c2f_fixed_N\bm25_fullmv_N20_run.tsv
results\week7\c2f_fixed_N\bm25_fullmv_N50_run.tsv
results\week7\c2f_fixed_N\bm25_fullmv_N100_run.tsv
```

---

## 2. 实验输入

本实验使用 Day 1 已经修复并验证过的 BM25 top-N candidates 文件作为 coarse retrieval 输入。

输入候选文件如下：

```text
artifacts\rerank_cache\week7_topN\candidates_bm25_N10.tsv
artifacts\rerank_cache\week7_topN\candidates_bm25_N20.tsv
artifacts\rerank_cache\week7_topN\candidates_bm25_N50.tsv
artifacts\rerank_cache\week7_topN\candidates_bm25_N100.tsv
```

Full MV reranking 使用的 embedding 目录如下：

```text
artifacts\embeddings\full_multivector\queries
artifacts\embeddings\full_multivector\pages
```

---

## 3. 脚本说明

本任务新建并运行以下脚本：

```text
scripts\retrieval\run_week7_bm25_fullmv_rerank.py
```

脚本功能：

1. 读取 BM25 top-N candidate 文件。
2. 按 query 加载 full multi-vector query embeddings。
3. 按 candidate page 加载 full multi-vector page embeddings。
4. 使用 late interaction score 进行 reranking。
5. 每个 query 最终输出 top-10 pages。
6. 为每个 N 分别输出 run 文件、score debug 文件、validation 文件和 summary 文件。

Late interaction scoring 使用：

$$
\text{score}(q,p)=\sum_i \max_j q_i^\top p_j
$$

其中：

- $$q_i$$ 表示 query 的第 $$i$$ 个 token embedding；
- $$p_j$$ 表示 page 的第 $$j$$ 个 token embedding；
- 对每个 query token，在 page token 中取最大相似度；
- 最后对所有 query token 的最大相似度求和。

---

## 4. 第一次运行问题与修复

第一次运行时，脚本成功读取了 candidate 文件数量，但 `total_scored=0`，run 文件只有 header。

第一次运行摘要如下：

| N | Total Candidates | Total Scored | Total Written | 状态 |
|---:|---:|---:|---:|---|
| 10 | 300 | 0 | 0 | Failed |
| 20 | 600 | 0 | 0 | Failed |
| 50 | 1500 | 0 | 0 | Failed |
| 100 | 3000 | 0 | 0 | Failed |

问题表现：

```text
total_scored=0
total_written=0
run 文件只有 1 行
```

修复方式：

- 修改 candidate 文件解析逻辑；
- 支持不同候选文件格式；
- 正确解析 `query_id`、`candidate_page_id`、`coarse_rank` 和 `coarse_score`；
- 对 zero scored candidates 增加 validation 检查。

修复后重新删除旧结果并重跑。

---

## 5. 删除旧结果

执行命令：

```bash
del results\week7\c2f_fixed_N\bm25_fullmv_N*_run.tsv
del results\week7\c2f_fixed_N\bm25_fullmv_N*_scores.csv
del results\week7\c2f_fixed_N\bm25_fullmv_N*_validation.csv
del results\week7\c2f_fixed_N\bm25_fullmv_rerank_summary.csv
del results\week7\c2f_fixed_N\bm25_fullmv_rerank_summary.json
```

---

## 6. 重新运行 BM25 + Full MV Rerank

执行命令：

```bash
python scripts\retrieval\run_week7_bm25_fullmv_rerank.py
```

终端输出：

```text
[Week7-Day2] Starting BM25 + Full MV reranking...
[Week7-Day2] Reranking BM25 candidates N=10 ...
[Week7-Day2] N=10 done. queries=30, total_candidates=300, total_scored=300, total_written=300, avg_latency_ms=9.361923
[Week7-Day2] Reranking BM25 candidates N=20 ...
[Week7-Day2] N=20 done. queries=30, total_candidates=600, total_scored=600, total_written=300, avg_latency_ms=13.855763
[Week7-Day2] Reranking BM25 candidates N=50 ...
[Week7-Day2] N=50 done. queries=30, total_candidates=1500, total_scored=1500, total_written=300, avg_latency_ms=32.776340
[Week7-Day2] Reranking BM25 candidates N=100 ...
[Week7-Day2] N=100 done. queries=30, total_candidates=3000, total_scored=3000, total_written=300, avg_latency_ms=63.873790

========== Week7 Day2 BM25 + Full MV Completed ==========
Summary CSV: E:\Working\PCB_VisualRAG_Project\results\week7\c2f_fixed_N\bm25_fullmv_rerank_summary.csv
Summary JSON: E:\Working\PCB_VisualRAG_Project\results\week7\c2f_fixed_N\bm25_fullmv_rerank_summary.json

N=10
  Candidate: E:\Working\PCB_VisualRAG_Project\artifacts\rerank_cache\week7_topN\candidates_bm25_N10.tsv
  Run: E:\Working\PCB_VisualRAG_Project\results\week7\c2f_fixed_N\bm25_fullmv_N10_run.tsv
  Validation: E:\Working\PCB_VisualRAG_Project\results\week7\c2f_fixed_N\bm25_fullmv_N10_validation.csv
  Total candidates: 300
  Total scored: 300
  Total written: 300
  Avg candidates/query: 10.0000
  Avg scored/query: 10.0000
  Avg written/query: 10.0000
  Avg latency/query ms: 9.361923

N=20
  Candidate: E:\Working\PCB_VisualRAG_Project\artifacts\rerank_cache\week7_topN\candidates_bm25_N20.tsv
  Run: E:\Working\PCB_VisualRAG_Project\results\week7\c2f_fixed_N\bm25_fullmv_N20_run.tsv
  Validation: E:\Working\PCB_VisualRAG_Project\results\week7\c2f_fixed_N\bm25_fullmv_N20_validation.csv
  Total candidates: 600
  Total scored: 600
  Total written: 300
  Avg candidates/query: 20.0000
  Avg scored/query: 20.0000
  Avg written/query: 10.0000
  Avg latency/query ms: 13.855763

N=50
  Candidate: E:\Working\PCB_VisualRAG_Project\artifacts\rerank_cache\week7_topN\candidates_bm25_N50.tsv
  Run: E:\Working\PCB_VisualRAG_Project\results\week7\c2f_fixed_N\bm25_fullmv_N50_run.tsv
  Validation: E:\Working\PCB_VisualRAG_Project\results\week7\c2f_fixed_N\bm25_fullmv_N50_validation.csv
  Total candidates: 1500
  Total scored: 1500
  Total written: 300
  Avg candidates/query: 50.0000
  Avg scored/query: 50.0000
  Avg written/query: 10.0000
  Avg latency/query ms: 32.776340

N=100
  Candidate: E:\Working\PCB_VisualRAG_Project\artifacts\rerank_cache\week7_topN\candidates_bm25_N100.tsv
  Run: E:\Working\PCB_VisualRAG_Project\results\week7\c2f_fixed_N\bm25_fullmv_N100_run.tsv
  Validation: E:\Working\PCB_VisualRAG_Project\results\week7\c2f_fixed_N\bm25_fullmv_N100_validation.csv
  Total candidates: 3000
  Total scored: 3000
  Total written: 300
  Avg candidates/query: 100.0000
  Avg scored/query: 100.0000
  Avg written/query: 10.0000
  Avg latency/query ms: 63.873790
```

---

## 7. 输出文件检查

执行命令：

```bash
dir results\week7\c2f_fixed_N\bm25_fullmv_N*_run.tsv
```

检查结果：

```text
05/08/2026  12:36 PM            14,474 bm25_fullmv_N100_run.tsv
05/08/2026  12:36 PM            14,198 bm25_fullmv_N10_run.tsv
05/08/2026  12:36 PM            14,181 bm25_fullmv_N20_run.tsv
05/08/2026  12:36 PM            14,176 bm25_fullmv_N50_run.tsv
```

生成文件如下：

```text
results\week7\c2f_fixed_N\bm25_fullmv_N10_run.tsv
results\week7\c2f_fixed_N\bm25_fullmv_N20_run.tsv
results\week7\c2f_fixed_N\bm25_fullmv_N50_run.tsv
results\week7\c2f_fixed_N\bm25_fullmv_N100_run.tsv
```

---

## 8. Run 文件行数检查

执行命令：

```bash
find /c /v "" results\week7\c2f_fixed_N\bm25_fullmv_N10_run.tsv
find /c /v "" results\week7\c2f_fixed_N\bm25_fullmv_N20_run.tsv
find /c /v "" results\week7\c2f_fixed_N\bm25_fullmv_N50_run.tsv
find /c /v "" results\week7\c2f_fixed_N\bm25_fullmv_N100_run.tsv
```

检查结果：

| Run 文件 | 行数 |
|---|---:|
| `bm25_fullmv_N10_run.tsv` | 301 |
| `bm25_fullmv_N20_run.tsv` | 301 |
| `bm25_fullmv_N50_run.tsv` | 301 |
| `bm25_fullmv_N100_run.tsv` | 301 |

由于共有 30 个 queries，每个 query 最终输出 top-10，并且文件包含 1 行 header，因此预期行数为：

$$
30 \times 10 + 1 = 301
$$

实际结果符合预期。

---

## 9. Validation 检查

执行命令：

```bash
findstr /I "FAILED" results\week7\c2f_fixed_N\bm25_fullmv_N*_validation.csv
```

检查结果：

```text

```

未发现 `FAILED`，说明：

- query embeddings 均正常加载；
- page embeddings 均正常加载；
- reranking 结果均限制在输入 candidate set 内；
- 每个 query 均成功完成 reranking。

---

## 10. Summary 结果

执行命令：

```bash
type results\week7\c2f_fixed_N\bm25_fullmv_rerank_summary.csv
```

CSV 内容：

```csv
N,query_count,final_top_k,total_candidates,total_scored,total_written,avg_candidates_per_query,avg_scored_per_query,avg_written_per_query,rerank_time_seconds,avg_rerank_latency_ms_per_query,candidate_file,run_file,validation_file,missing_query_embeddings_count,missing_page_embeddings_count
10,30,10,300,300,300,10.0000,10.0000,10.0000,0.280858,9.361923,artifacts\rerank_cache\week7_topN\candidates_bm25_N10.tsv,results\week7\c2f_fixed_N\bm25_fullmv_N10_run.tsv,results\week7\c2f_fixed_N\bm25_fullmv_N10_validation.csv,0,0
20,30,10,600,600,300,20.0000,20.0000,10.0000,0.415673,13.855763,artifacts\rerank_cache\week7_topN\candidates_bm25_N20.tsv,results\week7\c2f_fixed_N\bm25_fullmv_N20_run.tsv,results\week7\c2f_fixed_N\bm25_fullmv_N20_validation.csv,0,0
50,30,10,1500,1500,300,50.0000,50.0000,10.0000,0.983290,32.776340,artifacts\rerank_cache\week7_topN\candidates_bm25_N50.tsv,results\week7\c2f_fixed_N\bm25_fullmv_N50_run.tsv,results\week7\c2f_fixed_N\bm25_fullmv_N50_validation.csv,0,0
100,30,10,3000,3000,300,100.0000,100.0000,10.0000,1.916214,63.873790,artifacts\rerank_cache\week7_topN\candidates_bm25_N100.tsv,results\week7\c2f_fixed_N\bm25_fullmv_N100_run.tsv,results\week7\c2f_fixed_N\bm25_fullmv_N100_validation.csv,0,0
```

整理为表格：

| N | Queries | Final Top-k | Total Candidates | Total Scored | Total Written | Avg Candidates / Query | Avg Scored / Query | Avg Written / Query | Latency ms / Query | Missing Query Emb | Missing Page Emb |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 10 | 30 | 10 | 300 | 300 | 300 | 10.0000 | 10.0000 | 10.0000 | 9.361923 | 0 | 0 |
| 20 | 30 | 10 | 600 | 600 | 300 | 20.0000 | 20.0000 | 10.0000 | 13.855763 | 0 | 0 |
| 50 | 30 | 10 | 1500 | 1500 | 300 | 50.0000 | 50.0000 | 10.0000 | 32.776340 | 0 | 0 |
| 100 | 30 | 10 | 3000 | 3000 | 300 | 100.0000 | 100.0000 | 10.0000 | 63.873790 | 0 | 0 |

---

## 11. 结果分析

### 11.1 Candidate 数量验证

BM25 + Full MV rerank 成功读取并处理了不同 $$N$$ 的候选集。

| N | Expected Candidates | Actual Candidates | Actual Scored | 状态 |
|---:|---:|---:|---:|---|
| 10 | 300 | 300 | 300 | Passed |
| 20 | 600 | 600 | 600 | Passed |
| 50 | 1500 | 1500 | 1500 | Passed |
| 100 | 3000 | 3000 | 3000 | Passed |

说明 Day 2 任务 1 使用的是 Day 1 修复后的真实 candidate set，而不是固定 top-10。

---

### 11.2 Final top-k 输出验证

每个 N 的最终输出均为 300 条结果，即：

$$
30 \times 10 = 300
$$

加上 header 后文件总行数为 301。

这说明 reranker 对每个 query 输出了 final top-10 pages。

---

### 11.3 Latency 趋势

BM25 + Full MV reranking 的平均每 query 延迟如下：

| N | Avg Rerank Latency ms / Query |
|---:|---:|
| 10 | 9.361923 |
| 20 | 13.855763 |
| 50 | 32.776340 |
| 100 | 63.873790 |

可以看到，随着 $$N$$ 增大，需要被 Full MV reranker 打分的页面数增加，因此 reranking latency 也同步上升。

趋势如下：

$$
9.361923 \rightarrow 13.855763 \rightarrow 32.776340 \rightarrow 63.873790
$$

该趋势符合预期。

---

## 12. 输出文件汇总

### 12.1 Run 文件

```text
results\week7\c2f_fixed_N\bm25_fullmv_N10_run.tsv
results\week7\c2f_fixed_N\bm25_fullmv_N20_run.tsv
results\week7\c2f_fixed_N\bm25_fullmv_N50_run.tsv
results\week7\c2f_fixed_N\bm25_fullmv_N100_run.tsv
```

### 12.2 Score debug 文件

```text
results\week7\c2f_fixed_N\bm25_fullmv_N10_scores.csv
results\week7\c2f_fixed_N\bm25_fullmv_N20_scores.csv
results\week7\c2f_fixed_N\bm25_fullmv_N50_scores.csv
results\week7\c2f_fixed_N\bm25_fullmv_N100_scores.csv
```

### 12.3 Validation 文件

```text
results\week7\c2f_fixed_N\bm25_fullmv_N10_validation.csv
results\week7\c2f_fixed_N\bm25_fullmv_N20_validation.csv
results\week7\c2f_fixed_N\bm25_fullmv_N50_validation.csv
results\week7\c2f_fixed_N\bm25_fullmv_N100_validation.csv
```

### 12.4 Summary 文件

```text
results\week7\c2f_fixed_N\bm25_fullmv_rerank_summary.csv
results\week7\c2f_fixed_N\bm25_fullmv_rerank_summary.json
```

---

## 13. 任务 1 验收结论

Day 2 任务 1 的验收项如下：

| 验收项 | 结果 | 是否通过 |
|---|---|---|
| 四个 N 均完成 BM25 + Full MV rerank | N=10、20、50、100 全部完成 | Passed |
| 使用真实 BM25 top-N candidate 文件 | 输入来自 `week7_topN/candidates_bm25_N*.tsv` | Passed |
| 每个 N 的 candidate 数量正确 | 300、600、1500、3000 | Passed |
| 每个 N 的 scored 数量正确 | 300、600、1500、3000 | Passed |
| 每个 query 输出 final top-10 | 每个 run 文件 301 行，含 header | Passed |
| validation 无 FAILED | `findstr FAILED` 无输出 | Passed |
| embedding 缺失数为 0 | missing query/page embeddings 均为 0 | Passed |
| latency 随 N 增大合理上升 | 9.36 → 13.86 → 32.78 → 63.87 ms/query | Passed |

最终结论：

```text
Week 7 Day 2 Task 1 Status: PASS
```

BM25 + Full MV Rerank 已成功基于真实 BM25 candidate set 运行完成，可进入后续评估或 Day 2 Task 2。


---

# Week 7 Day 2 追加实验日志：Task 2–Task 4

**日期**：2026-05-08  
**项目**：PCB_VisualRAG_Project  
**环境**：`pcb_visualrag`  
**工作目录**：`E:\Working\PCB_VisualRAG_Project`

---

## Task 2：BM25 + Budgeted MV Rerank

### 1. 实验目标

本任务运行 **BM25 + Budgeted Multi-vector Rerank**，在 BM25 粗排候选集基础上，对 page multi-vector 表示进行 token budget 截断后再执行 late interaction reranking。

测试配置如下：

| Setting | N | M | Compression |
|---|---:|---:|---|
| low_cost | 20 | 8 | none |
| mid_cost | 20 | 16 | none |
| higher_quality | 50 | 24 | none |

其中：

- $$N$$ 表示 BM25 coarse retrieval candidate 数量；
- $$M$$ 表示每个 page 保留的 visual/text token 数量；
- 本次 compression 使用 `none`，即不使用 PQ 压缩。

---

### 2. 执行命令

删除旧结果时，系统提示旧文件不存在，属于正常情况：

```text
找不到 E:\Working\PCB_VisualRAG_Project\results\week7\c2f_fixed_N\bm25_budgetmv_*_run.tsv
找不到 E:\Working\PCB_VisualRAG_Project\results\week7\c2f_fixed_N\bm25_budgetmv_*_scores.csv
找不到 E:\Working\PCB_VisualRAG_Project\results\week7\c2f_fixed_N\bm25_budgetmv_*_validation.csv
找不到 E:\Working\PCB_VisualRAG_Project\results\week7\c2f_fixed_N\bm25_budgetmv_rerank_summary.csv
找不到 E:\Working\PCB_VisualRAG_Project\results\week7\c2f_fixed_N\bm25_budgetmv_rerank_summary.json
```

运行 Budgeted MV rerank：

```bash
python scripts\retrieval\run_week7_bm25_budgeted_mv_rerank.py
```

---

### 3. 运行结果

终端输出摘要：

```text
[Week7-Day2] Starting BM25 + Budgeted MV reranking...
[Week7-Day2] Reranking setting=low_cost, N=20, M=8, compression=none ...
[Week7-Day2] setting=low_cost N=20 M=8 done. queries=30, total_candidates=600, total_scored=600, total_written=300, avg_tokens_after=8.0000, avg_latency_ms=12.674273
[Week7-Day2] Reranking setting=mid_cost, N=20, M=16, compression=none ...
[Week7-Day2] setting=mid_cost N=20 M=16 done. queries=30, total_candidates=600, total_scored=600, total_written=300, avg_tokens_after=16.0000, avg_latency_ms=12.856343
[Week7-Day2] Reranking setting=higher_quality, N=50, M=24, compression=none ...
[Week7-Day2] setting=higher_quality N=50 M=24 done. queries=30, total_candidates=1500, total_scored=1500, total_written=300, avg_tokens_after=24.0000, avg_latency_ms=31.910323
```

---

### 4. 输出文件检查

执行命令：

```bash
dir results\week7\c2f_fixed_N\bm25_budgetmv_*_run.tsv
```

生成文件：

```text
05/08/2026  12:40 PM            17,495 bm25_budgetmv_N20_M16_none_run.tsv
05/08/2026  12:40 PM            17,218 bm25_budgetmv_N20_M8_none_run.tsv
05/08/2026  12:40 PM            17,485 bm25_budgetmv_N50_M24_none_run.tsv
```

---

### 5. Run 文件行数检查

执行命令：

```bash
find /c /v "" results\week7\c2f_fixed_N\bm25_budgetmv_N20_M8_none_run.tsv
find /c /v "" results\week7\c2f_fixed_N\bm25_budgetmv_N20_M16_none_run.tsv
find /c /v "" results\week7\c2f_fixed_N\bm25_budgetmv_N50_M24_none_run.tsv
```

检查结果：

| Run File | Lines |
|---|---:|
| `bm25_budgetmv_N20_M8_none_run.tsv` | 301 |
| `bm25_budgetmv_N20_M16_none_run.tsv` | 301 |
| `bm25_budgetmv_N50_M24_none_run.tsv` | 301 |

由于共有 30 个 queries，每个 query 输出 top-10，并包含 1 行 header，因此预期行数为：

$$
30 \times 10 + 1 = 301
$$

实际结果符合预期。

---

### 6. Validation 检查

执行命令：

```bash
findstr /I "FAILED" results\week7\c2f_fixed_N\bm25_budgetmv_*_validation.csv
```

结果无输出，说明 validation 全部通过。

---

### 7. Summary 结果

执行命令：

```bash
type results\week7\c2f_fixed_N\bm25_budgetmv_rerank_summary.csv
```

整理结果如下：

| Setting | N | M | Queries | Candidates | Scored | Written | Avg Tokens Before | Avg Tokens After | Token Keep Ratio | Latency ms/query | Missing Query Emb | Missing Page Emb |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| low_cost | 20 | 8 | 30 | 600 | 600 | 300 | 49.0000 | 8.0000 | 0.163265 | 12.674273 | 0 | 0 |
| mid_cost | 20 | 16 | 30 | 600 | 600 | 300 | 49.0000 | 16.0000 | 0.326531 | 12.856343 | 0 | 0 |
| higher_quality | 50 | 24 | 30 | 1500 | 1500 | 300 | 49.0000 | 24.0000 | 0.489796 | 31.910323 | 0 | 0 |

---

### 8. Task 2 验收结论

| 验收项 | 结果 | 是否通过 |
|---|---|---|
| 三组 Budgeted MV 配置完成运行 | low_cost、mid_cost、higher_quality 均完成 | Passed |
| candidate 数量正确 | 600、600、1500 | Passed |
| scored 数量正确 | 600、600、1500 | Passed |
| 每个 run 文件行数正确 | 均为 301 行 | Passed |
| validation 无 FAILED | 无输出 | Passed |
| embedding 缺失数为 0 | query/page 均为 0 | Passed |
| token budget 生效 | avg tokens after 分别为 8、16、24 | Passed |

最终结论：

```text
Week 7 Day 2 Task 2 Status: PASS
```

---

## Task 3：BM25-C2F 主结果表评估

### 1. 实验目标

本任务将以下方法与 BM25 baseline 进行对比：

1. BM25 baseline；
2. BM25 + Full MV Rerank；
3. BM25 + Budgeted MV Rerank。

评估指标包括：

```text
Recall@1
Recall@5
Recall@10
MRR@10
nDCG@10
Latency
```

---

### 2. 执行命令

```bash
python scripts\evaluation\evaluate_week7_bm25_c2f_main_table.py
```

---

### 3. 全部配置结果

终端输出：

```text
========== All Configs ==========
Method,Setting,N,M,Recall@1,Recall@5,Recall@10,MRR@10,nDCG@10,Latency
BM25,baseline,-,-,0.1333,0.6833,0.8833,0.4105,0.5241,-
BM25 + Full MV Rerank,fullmv_N10,10,-,0.0667,0.3000,0.8833,0.2107,0.3628,9.361923
BM25 + Full MV Rerank,fullmv_N20,20,-,0.0667,0.1667,0.3333,0.1211,0.1691,13.855763
BM25 + Full MV Rerank,fullmv_N50,50,-,0.0667,0.1000,0.1333,0.0881,0.0988,32.776340
BM25 + Full MV Rerank,fullmv_N100,100,-,0.0333,0.1000,0.1333,0.0644,0.0807,63.873790
BM25 + Budgeted MV Rerank,low_cost,20,8,0.0333,0.1333,0.3667,0.0956,0.1565,12.674273
BM25 + Budgeted MV Rerank,mid_cost,20,16,0.0000,0.1667,0.3667,0.0843,0.1490,12.856343
BM25 + Budgeted MV Rerank,higher_quality,50,24,0.0000,0.0333,0.1000,0.0170,0.0359,31.910323
```

整理表格如下：

| Method | Setting | N | M | Recall@1 | Recall@5 | Recall@10 | MRR@10 | nDCG@10 | Latency |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BM25 | baseline | - | - | 0.1333 | 0.6833 | 0.8833 | 0.4105 | 0.5241 | - |
| BM25 + Full MV Rerank | fullmv_N10 | 10 | - | 0.0667 | 0.3000 | 0.8833 | 0.2107 | 0.3628 | 9.361923 |
| BM25 + Full MV Rerank | fullmv_N20 | 20 | - | 0.0667 | 0.1667 | 0.3333 | 0.1211 | 0.1691 | 13.855763 |
| BM25 + Full MV Rerank | fullmv_N50 | 50 | - | 0.0667 | 0.1000 | 0.1333 | 0.0881 | 0.0988 | 32.776340 |
| BM25 + Full MV Rerank | fullmv_N100 | 100 | - | 0.0333 | 0.1000 | 0.1333 | 0.0644 | 0.0807 | 63.873790 |
| BM25 + Budgeted MV Rerank | low_cost | 20 | 8 | 0.0333 | 0.1333 | 0.3667 | 0.0956 | 0.1565 | 12.674273 |
| BM25 + Budgeted MV Rerank | mid_cost | 20 | 16 | 0.0000 | 0.1667 | 0.3667 | 0.0843 | 0.1490 | 12.856343 |
| BM25 + Budgeted MV Rerank | higher_quality | 50 | 24 | 0.0000 | 0.0333 | 0.1000 | 0.0170 | 0.0359 | 31.910323 |

---

### 4. 主结果表

执行命令：

```bash
type results\week7\c2f_fixed_N\bm25_c2f_main_results.csv
```

主结果表：

| Method | Setting | N | M | Compression | Recall@1 | Recall@5 | Recall@10 | MRR@10 | nDCG@10 | Latency ms/query |
|---|---|---:|---:|---|---:|---:|---:|---:|---:|---:|
| BM25 | baseline | - | - | - | 0.1333 | 0.6833 | 0.8833 | 0.4105 | 0.5241 | - |
| BM25 + Full MV Rerank | fullmv_N10 | 10 | - | none | 0.0667 | 0.3000 | 0.8833 | 0.2107 | 0.3628 | 9.361923 |
| BM25 + Budgeted MV Rerank | low_cost | 20 | 8 | none | 0.0333 | 0.1333 | 0.3667 | 0.0956 | 0.1565 | 12.674273 |

---

### 5. 输出文件检查

执行命令：

```bash
dir results\week7\c2f_fixed_N\bm25_c2f_*results*
```

生成文件：

```text
05/08/2026  12:42 PM             1,209 bm25_c2f_all_configs_results.csv
05/08/2026  12:42 PM             1,100 bm25_c2f_all_configs_results.md
05/08/2026  12:42 PM               477 bm25_c2f_main_results.csv
05/08/2026  12:42 PM               514 bm25_c2f_main_results.md
```

---

### 6. Task 3 结果分析

BM25 baseline 仍然是当前最佳方法：

```text
BM25 nDCG@10 = 0.5241
BM25 MRR@10 = 0.4105
BM25 Recall@10 = 0.8833
```

Full MV rerank 中最佳配置为：

```text
BM25 + Full MV Rerank, fullmv_N10
nDCG@10 = 0.3628
MRR@10 = 0.2107
Recall@10 = 0.8833
Latency = 9.361923 ms/query
```

Budgeted MV rerank 中最佳配置为：

```text
BM25 + Budgeted MV Rerank, low_cost, N=20, M=8
nDCG@10 = 0.1565
MRR@10 = 0.0956
Recall@10 = 0.3667
Latency = 12.674273 ms/query
```

本轮结果说明，当前 Full MV 与 Budgeted MV rerank 均未超过 BM25 baseline。

---

### 7. Task 3 验收结论

| 验收项 | 结果 | 是否通过 |
|---|---|---|
| BM25 baseline 指标输出 | 已输出 | Passed |
| Full MV 四组配置指标输出 | N=10、20、50、100 均输出 | Passed |
| Budgeted MV 三组配置指标输出 | low_cost、mid_cost、higher_quality 均输出 | Passed |
| 主结果表生成 | `bm25_c2f_main_results.csv/md` | Passed |
| 全配置表生成 | `bm25_c2f_all_configs_results.csv/md` | Passed |
| 指标包含 Recall/MRR/nDCG/Latency | 已包含 | Passed |

最终结论：

```text
Week 7 Day 2 Task 3 Status: PASS
```

---

## Task 4：Query Type Delta Analysis

### 1. 实验目标

本任务按 query type 分析 BM25 baseline 与最佳 Budgeted MV rerank 的差异，重点观察：

- 哪些 query type 有提升；
- 哪些 query type 被视觉重排伤害；
- 是否存在结构型 query 的相对优势。

本次自动选择的 Budgeted MV 配置为：

```text
results\week7\c2f_fixed_N\bm25_budgetmv_N20_M8_none_run.tsv
setting=low_cost N=20 M=8 compression=none
```

---

### 2. 执行命令

```bash
python scripts\evaluation\analyze_week7_query_type_delta.py
```

---

### 3. 终端输出

```text
Selected Budgeted MV run: E:\Working\PCB_VisualRAG_Project\results\week7\c2f_fixed_N\bm25_budgetmv_N20_M8_none_run.tsv
Setting: low_cost N=20 M=8 compression=none

========== Query Type Delta Analysis ==========
Query Type,Query Count,BM25 nDCG@10,BM25+Budgeted MV nDCG@10,Delta nDCG@10,Conclusion
parameter_lookup,2,0.6309,0.0000,-0.6309,Harmed
structure_legend_interpretation,5,0.6840,0.4152,-0.2688,Harmed
component_localization,2,0.0000,0.0000,0.0000,Unchanged
cross_page_consistency,4,0.4171,0.0000,-0.4171,Harmed
similarity_based_interference,17,0.5514,0.1540,-0.3973,Harmed
```

---

### 4. Query Type Delta 表

执行命令：

```bash
type results\week7\c2f_fixed_N\query_type_delta_analysis.csv
```

整理结果：

| Query Type | Query Count | BM25 nDCG@10 | BM25+Budgeted MV nDCG@10 | Delta nDCG@10 | BM25 Recall@10 | Budgeted Recall@10 | Delta Recall@10 | BM25 MRR@10 | Budgeted MRR@10 | Delta MRR@10 | Conclusion |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| parameter_lookup | 2 | 0.6309 | 0.0000 | -0.6309 | 1.0000 | 0.0000 | -1.0000 | 0.5000 | 0.0000 | -0.5000 | Harmed |
| structure_legend_interpretation | 5 | 0.6840 | 0.4152 | -0.2688 | 1.0000 | 0.8000 | -0.2000 | 0.5867 | 0.3033 | -0.2833 | Harmed |
| component_localization | 2 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | Unchanged |
| cross_page_consistency | 4 | 0.4171 | 0.0000 | -0.4171 | 0.6250 | 0.0000 | -0.6250 | 0.3611 | 0.0000 | -0.3611 | Harmed |
| similarity_based_interference | 17 | 0.5514 | 0.1540 | -0.3973 | 1.0000 | 0.4118 | -0.5882 | 0.4080 | 0.0796 | -0.3285 | Harmed |

---

### 5. 逐 Query 结果摘要

逐 query 文件已生成：

```text
results\week7\c2f_fixed_N\query_type_delta_per_query.csv
```

其中存在少量 query 在 Budgeted MV 下有局部提升：

| Query ID | Query Type | BM25 nDCG@10 | Budgeted MV nDCG@10 | Delta nDCG@10 |
|---|---|---:|---:|---:|
| q025 | similarity_based_interference | 0.2891 | 0.3869 | 0.0978 |
| q026 | similarity_based_interference | 0.2891 | 0.6309 | 0.3419 |

但从 query type 聚合均值看，`similarity_based_interference` 整体仍为负增益：

```text
Delta nDCG@10 = -0.3973
```

---

### 6. 输出文件检查

执行命令：

```bash
dir results\week7\c2f_fixed_N\query_type_delta*
```

生成文件：

```text
05/08/2026  12:45 PM               700 query_type_delta_analysis.csv
05/08/2026  12:45 PM             1,258 query_type_delta_analysis.md
05/08/2026  12:45 PM             3,136 query_type_delta_per_query.csv
```

---

### 7. 关键发现

#### 7.1 有提升的 query type

从 query type 聚合结果看：

```text
None
```

没有任何 query type 在 Budgeted MV rerank 下取得整体正向提升。

---

#### 7.2 被视觉重排伤害的 query type

以下 query type 出现负向 delta：

| Query Type | Delta nDCG@10 |
|---|---:|
| parameter_lookup | -0.6309 |
| cross_page_consistency | -0.4171 |
| similarity_based_interference | -0.3973 |
| structure_legend_interpretation | -0.2688 |

伤害最明显的是：

```text
parameter_lookup
```

其 Recall@10 从 1.0000 降至 0.0000，说明 Budgeted MV rerank 将 BM25 已召回的相关页排出了 top-10。

---

#### 7.3 未变化的 query type

```text
component_localization
```

该类型在 BM25 与 Budgeted MV 下均为：

```text
nDCG@10 = 0.0000
Recall@10 = 0.0000
MRR@10 = 0.0000
```

因此结果为 `Unchanged`。

---

#### 7.4 结构型 query 的相对优势

`structure_legend_interpretation` 虽然整体也被 Budgeted MV 伤害，但它是所有受伤类型中下降幅度最小的一类：

```text
Delta nDCG@10 = -0.2688
```

并且仍保持：

```text
Budgeted Recall@10 = 0.8000
Budgeted nDCG@10 = 0.4152
```

相比其他 query type，结构解释类 query 在 Budgeted MV rerank 下保留了较多有效结果，说明结构型 query 存在一定相对优势，但尚不足以超过 BM25 baseline。

---

### 8. Task 4 验收结论

| 验收项 | 结果 | 是否通过 |
|---|---|---|
| Query type 聚合分析输出 | 已输出 | Passed |
| BM25 vs Budgeted MV nDCG@10 delta 输出 | 已输出 | Passed |
| Recall@10 delta 输出 | 已输出 | Passed |
| MRR@10 delta 输出 | 已输出 | Passed |
| per-query delta 文件生成 | 已生成 | Passed |
| Markdown 报告生成 | 已生成 | Passed |
| Improved/Harmed/Unchanged 分类完成 | 已完成 | Passed |

最终结论：

```text
Week 7 Day 2 Task 4 Status: PASS
```

---

## Day 2 总体验收结论

本日完成任务如下：

| Task | 内容 | 状态 |
|---|---|---|
| Task 1 | BM25 + Full MV Rerank | PASS |
| Task 2 | BM25 + Budgeted MV Rerank | PASS |
| Task 3 | BM25-C2F Main Results Evaluation | PASS |
| Task 4 | Query Type Delta Analysis | PASS |

核心结果：

| Method | Best Setting | Recall@10 | MRR@10 | nDCG@10 | Latency ms/query |
|---|---|---:|---:|---:|---:|
| BM25 | baseline | 0.8833 | 0.4105 | 0.5241 | - |
| BM25 + Full MV Rerank | fullmv_N10 | 0.8833 | 0.2107 | 0.3628 | 9.361923 |
| BM25 + Budgeted MV Rerank | low_cost, N=20, M=8 | 0.3667 | 0.0956 | 0.1565 | 12.674273 |

Day 2 最终结论：

```text
Week 7 Day 2 Overall Status: PASS
```

实验观察：

1. BM25 baseline 是当前最强方法。
2. Full MV rerank 在 N=10 时保留了 BM25 的 Recall@10，但排序质量下降。
3. Budgeted MV rerank 在当前 token selection 策略下明显弱于 BM25。
4. Query type 分析显示没有 query type 获得整体提升。
5. `structure_legend_interpretation` 是 Budgeted MV 中相对最稳的类型，但仍低于 BM25。
6. 后续优化应优先检查 MV embedding 对齐、score normalization、token selection 策略和 rerank score 与 BM25 score 的融合。
