# Week 2 Baseline Experiments Log

**Project:** PCB_VisualRAG_Project  
**Stage:** Week 2  
**Date Range:** 2026-04-01 to 2026-04-09  
**Topic:** OCR/Text Baselines and Single-vector Visual Baseline  
**Status:** Completed  

---

## 1. 本阶段目标

Week 2 的核心目标是将 Week 1 已经搭建好的页面级检索任务，推进为一套可比较的 baseline 实验流程。

本阶段重点完成以下工作：

- 构建页面级 OCR 文本语料；
- 实现 OCR + BM25 baseline；
- 实现 OCR + Dense Text Retrieval baseline；
- 实现 Single-vector Visual Retrieval baseline；
- 统一输出 run 文件和 metrics 文件；
- 完成 overall comparison 与 query-type analysis；
- 初步判断文本信号与视觉信号在 PCB 页面检索中的作用。

本阶段的核心问题是：

> 在 PCB 工程文档页面检索任务中，OCR-based text retrieval 和 pure visual retrieval 哪一种更适合作为基础检索方法？

---

## 2. 实验数据与评测设置

### 2.1 数据规模

当前使用的数据规模如下：

| 项目 | 数量 |
|---|---:|
| PDF 文档数 | 10 |
| 页面图像数 | 101 |
| Query 数量 | 30 |
| 检索粒度 | Page-level |
| 标注方式 | Page-level qrels |

核心输入文件包括：

| 文件 | 路径 |
|---|---|
| 页面语料 | `data/metadata/corpus.jsonl` |
| OCR 语料 | `data/metadata/ocr_corpus.jsonl` |
| Queries | `data/metadata/queries.jsonl` |
| Qrels | `data/metadata/qrels.tsv` |
| Query taxonomy | `data/metadata/query_taxonomy.md` |

---

### 2.2 Query 类型

当前 query 类型包括：

| Query Type | 说明 |
|---|---|
| `parameter_lookup` | 参数查找类查询 |
| `structure_legend_interpretation` | 结构、图例或符号解释类查询 |
| `component_localization` | 元件定位类查询 |
| `cross_page_consistency` | 跨页一致性检查类查询 |
| `similarity_based_interference` | 相似页面干扰类查询 |

Query type 分布如下：

| Query Type | Query 数量 |
|---|---:|
| `component_localization` | 2 |
| `cross_page_consistency` | 4 |
| `parameter_lookup` | 2 |
| `similarity_based_interference` | 17 |
| `structure_legend_interpretation` | 5 |

---

### 2.3 评测指标

本阶段统一使用以下检索指标：

| 指标 | 说明 |
|---|---|
| `Recall@1` | Top-1 是否命中相关页面 |
| `Recall@3` | Top-3 是否命中相关页面 |
| `Recall@5` | Top-5 是否命中相关页面 |
| `Recall@10` | Top-10 是否命中相关页面 |
| `MRR` | Mean Reciprocal Rank |
| `nDCG@10` | Top-10 排序质量指标 |

主评测口径为 **page-level retrieval**。

---

## 3. Day 1：OCR 页面文本抽取与质量检查

### 3.1 目标

Day 1 的目标是对页面图像执行 OCR，并构建可供文本检索使用的页面级 OCR 语料。

---

### 3.2 输入与输出

| 类型 | 路径 |
|---|---|
| 输入页面图像 | `data/images/` |
| OCR 原始输出 | `data/ocr_raw/` |
| OCR 语料文件 | `data/metadata/ocr_corpus.jsonl` |
| OCR 日志 | `notes/2026-04-01_week2_day1_ocr_log.txt` |
| OCR 质量检查 | `notes/2026-04-01_week2_day1_ocr_quality_check.txt` |

---

### 3.3 完成内容

本日完成以下工作：

- 对所有页面图像批量执行 OCR；
- 将 OCR 文本整理为页面级语料；
- 检查 OCR 输出与 `page_id` 的对应关系；
- 对部分页面进行人工质量抽查；
- 确认 OCR 文本可作为 BM25 和 Dense Retrieval 的输入。

---

### 3.4 初步观察

OCR 输出整体可用，但存在以下问题：

- 小字号文本容易识别错误；
- 表格结构被破坏；
- 符号、单位和特殊字符存在缺失；
- 部分页面中的图例和电路标注识别不稳定。

尽管 OCR 并不完美，但页面中的标题、器件名、参数名、接口名和部分表格字段仍然被保留，因此可以支撑文本检索 baseline。

---

## 4. Day 2：OCR + BM25 Baseline

### 4.1 目标

Day 2 的目标是实现第一个正式 baseline：OCR + BM25。

该方法使用 OCR 文本作为页面表示，通过词项匹配计算 query 与页面之间的相关性。

---

### 4.2 输出文件

| 类型 | 路径 |
|---|---|
| Run 文件 | `results/baselines/bm25_run.tsv` |
| Metrics 文件 | `results/baselines/bm25_metrics.json` |
| 实验总结 | `notes/2026-04-02_week2_day2_bm25_summary.md` |

---

### 4.3 Overall Metrics

| Metric | OCR + BM25 |
|---|---:|
| Recall@1 | 0.1333 |
| Recall@3 | 0.6833 |
| Recall@5 | 0.6833 |
| Recall@10 | 0.8833 |
| MRR | 0.4105 |
| nDCG@10 | 0.5241 |

---

### 4.4 阶段结论

BM25 成为了当前最强的 standalone baseline。

这说明在 PCB 工程文档页面检索中，显式文本信息非常重要。即使 OCR 存在噪声，只要关键术语、器件编号、参数名和标题被识别出来，传统 lexical retrieval 仍然非常有效。

---

## 5. Day 3：OCR + Dense Text Retrieval

### 5.1 目标

Day 3 的目标是实现 OCR + Dense Text Retrieval，并与 BM25 进行对比。

Dense Text Retrieval 的作用是验证语义匹配是否能够弥补 BM25 对词面匹配的依赖。

---

### 5.2 输出文件

| 类型 | 路径 |
|---|---|
| Run 文件 | `results/baselines/dense_text_run.tsv` |
| Metrics 文件 | `results/baselines/dense_text_metrics.json` |
| 实验总结 | `notes/2026-04-03_week2_day3_dense_text_summary.md` |

---

### 5.3 Overall Metrics

| Metric | OCR + BM25 | OCR + Dense |
|---|---:|---:|
| Recall@1 | 0.1333 | 0.1000 |
| Recall@3 | 0.6833 | 0.4500 |
| Recall@5 | 0.6833 | 0.6000 |
| Recall@10 | 0.8833 | 0.8000 |
| MRR | 0.4105 | 0.3358 |
| nDCG@10 | 0.5241 | 0.4420 |

---

### 5.4 阶段结论

Dense Text Retrieval 整体表现弱于 BM25，但仍明显强于纯视觉 single-vector baseline。

该结果说明：

- 当前 query 很多依赖精确术语和参数名；
- BM25 对 PCB 文档中的器件编号、参数字段和标题更敏感；
- Dense Retrieval 可能在词面不一致时有补充价值；
- 但在当前数据规模和 query 设置下，Dense 尚未超过 BM25。

---

## 6. Day 4：Single-vector Visual Retrieval

### 6.1 目标

Day 4 的目标是实现纯视觉 single-vector baseline，验证单页全局视觉向量是否足以支撑 PCB 工程文档页面级检索。

---

### 6.2 方法设置

| 模块 | 设置 |
|---|---|
| Visual encoder | `openai/clip-vit-base-patch32` |
| Page representation | 每页一个全局图像向量 |
| Query representation | CLIP text embedding |
| Retrieval backend | FAISS IndexFlatIP |
| Similarity | L2-normalized inner product |
| 检索粒度 | Page-level |

---

### 6.3 输出文件

| 类型 | 路径 |
|---|---|
| Run 文件 | `results/baselines/single_vector_visual_run.tsv` |
| Metrics 文件 | `results/baselines/single_vector_visual_metrics.json` |
| 实验总结 | `notes/2026-04-04_week2_day4_single_vector_visual_summary.md` |

---

### 6.4 Overall Metrics

| Metric | OCR + BM25 | OCR + Dense | Single-vector Visual |
|---|---:|---:|---:|
| Recall@1 | 0.1333 | 0.1000 | 0.0000 |
| Recall@3 | 0.6833 | 0.4500 | 0.0833 |
| Recall@5 | 0.6833 | 0.6000 | 0.0833 |
| Recall@10 | 0.8833 | 0.8000 | 0.2500 |
| MRR | 0.4105 | 0.3358 | 0.0664 |
| nDCG@10 | 0.5241 | 0.4420 | 0.1041 |

---

### 6.5 阶段结论

Single-vector Visual Retrieval 明显弱于两种 OCR-based text retrieval 方法。

主要原因包括：

- 单个全局视觉向量会过度压缩页面信息；
- PCB 页面包含大量细粒度文本、表格、符号和局部布局；
- query 往往指向局部区域，而不是整页视觉风格；
- CLIP 全局图文匹配难以区分相似工程页面；
- 页面级全局向量不适合表达局部结构和证据区域。

该结果说明，纯视觉检索如果采用 single-vector 表示，不足以替代 OCR/Text retrieval。

---

## 7. Day 5：Baseline 汇总与 Query-type 分析

### 7.1 目标

Day 5 的目标是整合前三个 baseline 的结果，形成统一对比表，并进行 query-type analysis。

---

### 7.2 输出文件

| 类型 | 路径 |
|---|---|
| Baseline 汇总 | `results/baselines/baseline_summary.csv` |
| Baseline 汇总 Excel | `results/baselines/baseline_summary.xlsx` |
| Query-type 结果 | `results/analysis/results_by_query_type.csv` |
| Query-type 结果 Excel | `results/analysis/results_by_query_type.xlsx` |
| Query-type 数量统计 | `results/analysis/query_type_counts.csv` |
| 每类最佳方法 | `results/analysis/type_best_method.csv` |
| 初步结论 | `notes/2026-04-09_week2_day5_initial_conclusion.md` |
| Day 5 总结 | `notes/2026-04-09_misc_day5_summary.md` |

---

### 7.3 Overall Comparison

| Method | Recall@1 | Recall@5 | Recall@10 | MRR | nDCG@10 |
|---|---:|---:|---:|---:|---:|
| OCR + BM25 | 0.1333 | 0.6833 | 0.8833 | 0.4105 | 0.5241 |
| OCR + Dense | 0.1000 | 0.6000 | 0.8000 | 0.3358 | 0.4420 |
| Single-vector Visual | 0.0000 | 0.0833 | 0.2500 | 0.0664 | 0.1041 |

Overall method ranking based on MRR:

1. OCR + BM25
2. OCR + Dense
3. Single-vector Visual

---

### 7.4 Query-type Findings

Query-type analysis 显示不同类型 query 对检索信号的依赖不同。

#### Parameter lookup

`parameter_lookup` 类型 query 通常包含明确参数名、数值、器件名或字段名称，因此 BM25 表现较稳定。

#### Cross-page consistency

`cross_page_consistency` 类型 query 更依赖跨页文本线索、实体名称和接口名，因此 OCR-based 方法更有优势。

#### Component localization

`component_localization` 类型 query 更依赖局部结构和位置关系。BM25 在某些情况下可能失效，Dense Text 和 Visual 方法可能提供一定补充，但当前 Single-vector Visual 仍不够强。

#### Similarity-based interference

`similarity_based_interference` 是当前数量最多的 query 类型。该类 query 容易被相似页面干扰，对排序能力要求更高。

#### Structure / legend interpretation

`structure_legend_interpretation` 类型 query 涉及图例、结构说明和局部视觉元素。该类型可能是后续 multi-vector visual retrieval 发挥作用的重要场景。

---

## 8. 本阶段主要结论

Week 2 的实验得到以下关键结论：

1. OCR + BM25 是当前最强 standalone baseline。
2. OCR + Dense Retrieval 具备一定语义补充价值，但整体弱于 BM25。
3. Single-vector Visual Retrieval 表现较弱，说明全局视觉向量不足以表达 PCB 工程页面的局部结构。
4. 当前结果不支持“视觉方法直接替代 OCR/Text”的叙事。
5. 更合理的研究方向是探索 text + visual complementarity。
6. 后续应重点尝试 multi-vector late interaction、visual reranking 和 fusion。

---

## 9. 对后续实验的启示

根据 Week 2 结果，后续实验应围绕以下方向展开：

- 使用 multi-vector 表示替代 single-vector visual 表示；
- 利用局部视觉 token 建模页面结构和图例；
- 使用 OCR/BM25 作为强 coarse retriever；
- 使用视觉 multi-vector 方法作为 reranker；
- 分析不同 query type 下文本与视觉信号的互补性；
- 不再将研究叙事建立在“视觉全面替代 OCR”之上。

---

## 10. 可写入论文的阶段性表述

Week 2 experiments establish several retrieval baselines for the proposed PCB page-level retrieval task. The results show that OCR-based lexical retrieval remains a strong standalone baseline, with OCR + BM25 achieving the best overall performance. Dense text retrieval provides a semantic alternative but does not outperform BM25 under the current dataset and query setting. In contrast, single-vector visual retrieval performs substantially worse, indicating that global page-level visual embeddings are insufficient for capturing the fine-grained tables, component labels, structural diagrams, and layout cues in PCB engineering documents. These findings motivate the following exploration of multi-vector late interaction and visual reranking as complementary mechanisms rather than replacements for OCR-based retrieval.
