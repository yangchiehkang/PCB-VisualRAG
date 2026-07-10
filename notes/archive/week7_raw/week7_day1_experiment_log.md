# Week 7 Day 1 实验日志：修复不同 N 候选集并重新计算 Coarse Recall@N

**日期**：2026-05-08  
**项目**：PCB_VisualRAG_Project  
**环境**：`pcb_visualrag`  
**工作目录**：`E:\Working\PCB_VisualRAG_Project`

---

## 1. 实验目标

本次 Day 1 的主要目标是修复 coarse retrieval 阶段候选数量固定为 10 的问题，并重新生成不同候选规模下的 coarse candidates。

需要验证的候选规模为：

$$
N \in \{10, 20, 50, 100\}
$$

本次实验主要完成以下任务：

1. 修改 BM25、Dense Text、Single-vector Visual 检索脚本，使其支持 `--top_k` 和 `--output` 参数。
2. 重新生成 top-101 full-depth run 文件。
3. 从 top-101 run 中切出不同 $$N$$ 的候选文件。
4. 检查 actual candidates/query 是否随 $$N$$ 正确变化。
5. 重新计算 BM25 和 Single-vector Visual 的 Coarse Recall@N。

---

## 2. 脚本修改说明

原始脚本中 `TOP_K = 10` 被写死，导致无论实验设置中的 $$N$$ 是多少，实际进入 reranking 的 candidates/query 都固定为 10。

本次修改后的脚本支持以下参数：

- `--top_k`
- `--output`

修改涉及以下脚本：

```text
scripts/retrieval/run_bm25.py
scripts/retrieval/run_dense_text_retrieval.py
scripts/retrieval/run_single_vector_visual_retrieval.py
```

修改后可以通过命令行显式指定输出 top-k 数量和输出路径，例如：

```bash
python scripts/retrieval/run_bm25.py --top_k 101 --output results/baselines/bm25_top101_run.tsv
```

---

## 3. 生成 top-101 full-depth run

### 3.1 BM25 top-101 run

执行命令：

```bash
python scripts/retrieval/run_bm25.py --top_k 101 --output results/baselines/bm25_top101_run.tsv
```

输出摘要：

```text
Loaded 101 documents from E:\Working\PCB_VisualRAG_Project\data\metadata\ocr_corpus.jsonl
Loaded 30 queries from E:\Working\PCB_VisualRAG_Project\data\metadata\queries.jsonl
TOP_K = 101
Output path = results\baselines\bm25_top101_run.tsv
Wrote BM25 run to: results\baselines\bm25_top101_run.tsv
```

---

### 3.2 Dense Text top-101 run

执行命令：

```bash
python scripts/retrieval/run_dense_text_retrieval.py --top_k 101 --output results/baselines/dense_text_top101_run.tsv
```

输出摘要：

```text
Loaded 101 documents
Loaded 30 queries
TOP_K = 101
Output path = results\baselines\dense_text_top101_run.tsv
Loading model: sentence-transformers/all-MiniLM-L6-v2
Encoding page texts...
Built FAISS index with 101 vectors, dim=384
Encoding queries...
Wrote dense text run to: results\baselines\dense_text_top101_run.tsv
```

说明：

```text
embeddings.position_ids | UNEXPECTED
```

该提示来自模型加载过程，属于不同任务或架构加载时可能出现的非关键提示。本次模型成功加载并完成编码，因此不影响实验结果。

---

### 3.3 Single-vector Visual top-101 run

执行命令：

```bash
python scripts/retrieval/run_single_vector_visual_retrieval.py --top_k 101 --output results/baselines/single_vector_top101_run.tsv
```

输出摘要：

```text
Project root: E:\Working\PCB_VisualRAG_Project
Query path: E:\Working\PCB_VisualRAG_Project\data\metadata\queries.jsonl
Image dir: E:\Working\PCB_VisualRAG_Project\data\images
Output path: results\baselines\single_vector_top101_run.tsv
Using device: cpu
Loading model: openai/clip-vit-base-patch32
Loaded 30 queries
Loaded 101 page images
TOP_K = 101
Encoded image batch 1 / 13
Encoded image batch 2 / 13
Encoded image batch 3 / 13
Encoded image batch 4 / 13
Encoded image batch 5 / 13
Encoded image batch 6 / 13
Encoded image batch 7 / 13
Encoded image batch 8 / 13
Encoded image batch 9 / 13
Encoded image batch 10 / 13
Encoded image batch 11 / 13
Encoded image batch 12 / 13
Encoded image batch 13 / 13
Encoded text batch 1 / 2
Encoded text batch 2 / 2
Wrote single-vector visual run to: results\baselines\single_vector_top101_run.tsv
```

---

## 4. top-101 run 文件检查

执行命令：

```bash
dir results\baselines\*top101_run.tsv
```

检查结果：

```text
05/08/2026  12:17 PM           151,536 bm25_top101_run.tsv
05/08/2026  12:18 PM           169,488 dense_text_top101_run.tsv
05/08/2026  12:18 PM           199,770 single_vector_top101_run.tsv
```

生成的 top-101 run 文件如下：

```text
results\baselines\bm25_top101_run.tsv
results\baselines\dense_text_top101_run.tsv
results\baselines\single_vector_top101_run.tsv
```

---

## 5. top-101 run 行数检查

执行命令：

```bash
find /c /v "" results\baselines\bm25_top101_run.tsv
find /c /v "" results\baselines\dense_text_top101_run.tsv
find /c /v "" results\baselines\single_vector_top101_run.tsv
```

检查结果：

| Run 文件 | 行数 |
|---|---:|
| `bm25_top101_run.tsv` | 3030 |
| `dense_text_top101_run.tsv` | 3030 |
| `single_vector_top101_run.tsv` | 3030 |

由于共有 30 个 queries，每个 query 输出 101 个候选，因此预期行数为：

$$
30 \times 101 = 3030
$$

实际检查结果与预期一致。

---

## 6. 从 top-101 run 切出不同 N 候选集

执行命令：

```bash
python scripts\retrieval\build_week7_candidates_from_top101.py
```

输出结果：

```text
Wrote: E:\Working\PCB_VisualRAG_Project\artifacts\rerank_cache\week7_topN\candidates_bm25_N10.tsv
Wrote: E:\Working\PCB_VisualRAG_Project\artifacts\rerank_cache\week7_topN\candidates_bm25_N20.tsv
Wrote: E:\Working\PCB_VisualRAG_Project\artifacts\rerank_cache\week7_topN\candidates_bm25_N50.tsv
Wrote: E:\Working\PCB_VisualRAG_Project\artifacts\rerank_cache\week7_topN\candidates_bm25_N100.tsv
Wrote: E:\Working\PCB_VisualRAG_Project\artifacts\rerank_cache\week7_topN\candidates_visual_N10.tsv
Wrote: E:\Working\PCB_VisualRAG_Project\artifacts\rerank_cache\week7_topN\candidates_visual_N20.tsv
Wrote: E:\Working\PCB_VisualRAG_Project\artifacts\rerank_cache\week7_topN\candidates_visual_N50.tsv
Wrote: E:\Working\PCB_VisualRAG_Project\artifacts\rerank_cache\week7_topN\candidates_visual_N100.tsv
Done.
```

生成的候选文件包括：

```text
artifacts\rerank_cache\week7_topN\candidates_bm25_N10.tsv
artifacts\rerank_cache\week7_topN\candidates_bm25_N20.tsv
artifacts\rerank_cache\week7_topN\candidates_bm25_N50.tsv
artifacts\rerank_cache\week7_topN\candidates_bm25_N100.tsv

artifacts\rerank_cache\week7_topN\candidates_visual_N10.tsv
artifacts\rerank_cache\week7_topN\candidates_visual_N20.tsv
artifacts\rerank_cache\week7_topN\candidates_visual_N50.tsv
artifacts\rerank_cache\week7_topN\candidates_visual_N100.tsv
```

---

## 7. 候选文件行数检查

执行命令：

```bash
find /c /v "" artifacts\rerank_cache\week7_topN\candidates_bm25_N10.tsv
find /c /v "" artifacts\rerank_cache\week7_topN\candidates_bm25_N20.tsv
find /c /v "" artifacts\rerank_cache\week7_topN\candidates_bm25_N50.tsv
find /c /v "" artifacts\rerank_cache\week7_topN\candidates_bm25_N100.tsv

find /c /v "" artifacts\rerank_cache\week7_topN\candidates_visual_N10.tsv
find /c /v "" artifacts\rerank_cache\week7_topN\candidates_visual_N20.tsv
find /c /v "" artifacts\rerank_cache\week7_topN\candidates_visual_N50.tsv
find /c /v "" artifacts\rerank_cache\week7_topN\candidates_visual_N100.tsv
```

检查结果：

| Method | N | 文件 | 行数 |
|---|---:|---|---:|
| BM25 | 10 | `candidates_bm25_N10.tsv` | 300 |
| BM25 | 20 | `candidates_bm25_N20.tsv` | 600 |
| BM25 | 50 | `candidates_bm25_N50.tsv` | 1500 |
| BM25 | 100 | `candidates_bm25_N100.tsv` | 3000 |
| Single-vector Visual | 10 | `candidates_visual_N10.tsv` | 300 |
| Single-vector Visual | 20 | `candidates_visual_N20.tsv` | 600 |
| Single-vector Visual | 50 | `candidates_visual_N50.tsv` | 1500 |
| Single-vector Visual | 100 | `candidates_visual_N100.tsv` | 3000 |

由于共有 30 个 queries，因此候选文件理论行数为：

$$
\text{rows} = 30 \times N
$$

对应关系如下：

| N | 预期行数 | 实际行数 |
|---:|---:|---:|
| 10 | 300 | 300 |
| 20 | 600 | 600 |
| 50 | 1500 | 1500 |
| 100 | 3000 | 3000 |

候选文件切分结果符合预期。

---

## 8. Actual Candidates / Query 检查

执行命令：

```bash
python scripts\evaluation\check_week7_actual_candidates.py
```

输出结果：

```text
Wrote: E:\Working\PCB_VisualRAG_Project\results\week7\c2f_fixed_N\actual_candidates_check.csv
bm25 N= 10 avg= 10.0 min= 10 max= 10
bm25 N= 20 avg= 20.0 min= 20 max= 20
bm25 N= 50 avg= 50.0 min= 50 max= 50
bm25 N= 100 avg= 100.0 min= 100 max= 100
visual N= 10 avg= 10.0 min= 10 max= 10
visual N= 20 avg= 20.0 min= 20 max= 20
visual N= 50 avg= 50.0 min= 50 max= 50
visual N= 100 avg= 100.0 min= 100 max= 100
```

生成文件：

```text
results\week7\c2f_fixed_N\actual_candidates_check.csv
```

CSV 内容：

```csv
method,N,expected_candidates_per_query,num_queries,avg_candidates_per_query,min_candidates_per_query,max_candidates_per_query
bm25,10,10,30,10.0,10,10
bm25,20,20,30,20.0,20,20
bm25,50,50,30,50.0,50,50
bm25,100,100,30,100.0,100,100
visual,10,10,30,10.0,10,10
visual,20,20,30,20.0,20,20
visual,50,50,30,50.0,50,50
visual,100,100,30,100.0,100,100
```

整理结果如下：

| Method | N | Expected Candidates / Query | Actual Avg | Min | Max |
|---|---:|---:|---:|---:|---:|
| BM25 | 10 | 10 | 10.0 | 10 | 10 |
| BM25 | 20 | 20 | 20.0 | 20 | 20 |
| BM25 | 50 | 50 | 50.0 | 50 | 50 |
| BM25 | 100 | 100 | 100.0 | 100 | 100 |
| Single-vector Visual | 10 | 10 | 10.0 | 10 | 10 |
| Single-vector Visual | 20 | 20 | 20.0 | 20 | 20 |
| Single-vector Visual | 50 | 50 | 50.0 | 50 | 50 |
| Single-vector Visual | 100 | 100 | 100.0 | 100 | 100 |

结论：不同 $$N$$ 下的 actual candidates/query 已经正确变化，说明原先 candidates/query 固定为 10 的问题已经修复。

---

## 9. 重新计算 Coarse Recall@N

执行命令：

```bash
python scripts\evaluation\compute_week7_coarse_recall_atN.py
```

输出结果：

```text
Using qrels: E:\Working\PCB_VisualRAG_Project\data\metadata\qrels.tsv
Loaded qrels queries: 30
Total relevant pairs: 33
Single-vector Visual   N=10  Recall=0.2667 Hit=8 Miss=22
Single-vector Visual   N=20  Recall=0.5000 Hit=15 Miss=15
Single-vector Visual   N=50  Recall=0.7333 Hit=22 Miss=8
Single-vector Visual   N=100 Recall=1.0000 Hit=30 Miss=0
BM25                   N=10  Recall=0.9000 Hit=27 Miss=3
BM25                   N=20  Recall=0.9333 Hit=28 Miss=2
BM25                   N=50  Recall=1.0000 Hit=30 Miss=0
BM25                   N=100 Recall=1.0000 Hit=30 Miss=0

Wrote CSV: E:\Working\PCB_VisualRAG_Project\results\week7\c2f_fixed_N\coarse_recall_atN.csv
Wrote Markdown table: E:\Working\PCB_VisualRAG_Project\results\week7\c2f_fixed_N\coarse_recall_atN.md
Wrote query details: E:\Working\PCB_VisualRAG_Project\results\week7\c2f_fixed_N\coarse_recall_atN_query_details.csv
```

---

## 10. Coarse Recall@N 结果表

结果文件：

```text
results\week7\c2f_fixed_N\coarse_recall_atN.csv
```

整理后的结果表如下：

| Coarse Method | N | Coarse Recall@N | Hit Queries | Miss Queries |
|---|---:|---:|---:|---:|
| Single-vector Visual | 10 | 0.2667 | 8 | 22 |
| Single-vector Visual | 20 | 0.5000 | 15 | 15 |
| Single-vector Visual | 50 | 0.7333 | 22 | 8 |
| Single-vector Visual | 100 | 1.0000 | 30 | 0 |
| BM25 | 10 | 0.9000 | 27 | 3 |
| BM25 | 20 | 0.9333 | 28 | 2 |
| BM25 | 50 | 1.0000 | 30 | 0 |
| BM25 | 100 | 1.0000 | 30 | 0 |

---

## 11. 结果分析

### 11.1 Single-vector Visual

Single-vector Visual 的 Coarse Recall@N 随 $$N$$ 增大明显提升：

| N | Recall@N | Hit Queries | Miss Queries |
|---:|---:|---:|---:|
| 10 | 0.2667 | 8 | 22 |
| 20 | 0.5000 | 15 | 15 |
| 50 | 0.7333 | 22 | 8 |
| 100 | 1.0000 | 30 | 0 |

从结果可以看出，视觉单向量检索在较小候选集下召回不足，但随着候选数量增加，召回率显著提升。

特别是从 $$N=10$$ 到 $$N=20$$，Recall 从 0.2667 提升到 0.5000；从 $$N=50$$ 到 $$N=100$$，最终达到 1.0000。

这说明 Single-vector Visual 方法对于 relevant page 的排序相对靠后，需要较大的候选池才能保证较高 coarse recall。

---

### 11.2 BM25

BM25 的 Coarse Recall@N 整体明显高于 Single-vector Visual：

| N | Recall@N | Hit Queries | Miss Queries |
|---:|---:|---:|---:|
| 10 | 0.9000 | 27 | 3 |
| 20 | 0.9333 | 28 | 2 |
| 50 | 1.0000 | 30 | 0 |
| 100 | 1.0000 | 30 | 0 |

BM25 在 $$N=10$$ 时已经达到 0.9000，说明 OCR 文本中的关键词信息对当前 PCB 问答任务非常有效。

当 $$N=50$$ 时，BM25 已经覆盖全部 30 个 query 的 relevant page，Coarse Recall@50 达到 1.0000。

---

### 11.3 方法对比

| N | Single-vector Visual | BM25 |
|---:|---:|---:|
| 10 | 0.2667 | 0.9000 |
| 20 | 0.5000 | 0.9333 |
| 50 | 0.7333 | 1.0000 |
| 100 | 1.0000 | 1.0000 |

可以观察到：

1. BM25 在小候选规模下明显优于 Single-vector Visual。
2. Single-vector Visual 需要更大的 $$N$$ 才能达到较高召回。
3. 两种方法在 $$N=100$$ 时均达到 1.0000。
4. BM25 在 $$N=50$$ 时已经达到 full recall，而 Single-vector Visual 到 $$N=100$$ 才达到 full recall。

---

## 12. 实验结论

本次 Day 1 实验完成了 coarse retrieval 候选数量修复和 Coarse Recall@N 重新计算。

主要结论如下：

1. 原先候选数量固定为 10 的问题已修复。
2. top-101 full-depth run 已正确生成，每个 run 文件均为 3030 行。
3. 不同 $$N$$ 的候选文件已正确切出：
   - $$N=10$$：300 行
   - $$N=20$$：600 行
   - $$N=50$$：1500 行
   - $$N=100$$：3000 行
4. Actual candidates/query 检查通过：
   - BM25 在不同 $$N$$ 下分别为 10、20、50、100。
   - Single-vector Visual 在不同 $$N$$ 下分别为 10、20、50、100。
5. Coarse Recall@N 呈现合理的单调递增趋势。
6. BM25 在当前数据集上表现更强，尤其在较小 $$N$$ 下优势明显。
7. Single-vector Visual 在较大候选池下可以达到 full recall，但小候选池召回不足。

---

## 13. 生成文件汇总

### 13.1 top-101 run 文件

```text
results\baselines\bm25_top101_run.tsv
results\baselines\dense_text_top101_run.tsv
results\baselines\single_vector_top101_run.tsv
```

### 13.2 不同 N 候选文件

```text
artifacts\rerank_cache\week7_topN\candidates_bm25_N10.tsv
artifacts\rerank_cache\week7_topN\candidates_bm25_N20.tsv
artifacts\rerank_cache\week7_topN\candidates_bm25_N50.tsv
artifacts\rerank_cache\week7_topN\candidates_bm25_N100.tsv

artifacts\rerank_cache\week7_topN\candidates_visual_N10.tsv
artifacts\rerank_cache\week7_topN\candidates_visual_N20.tsv
artifacts\rerank_cache\week7_topN\candidates_visual_N50.tsv
artifacts\rerank_cache\week7_topN\candidates_visual_N100.tsv
```

### 13.3 检查与评估结果

```text
results\week7\c2f_fixed_N\actual_candidates_check.csv
results\week7\c2f_fixed_N\coarse_recall_atN.csv
results\week7\c2f_fixed_N\coarse_recall_atN.md
results\week7\c2f_fixed_N\coarse_recall_atN_query_details.csv
```

---

## 14. Day 1 状态

**Day 1 实验状态：完成。**

本日实验已经确认：

- 不同 $$N$$ 的 candidates/query 正确生效。
- Coarse Recall@N 已重新计算。
- 实验结果可以用于后续 reranking、C2F pipeline 或不同候选规模下的性能比较。
