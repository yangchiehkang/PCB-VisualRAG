# Week 2 Weekly Report

**Project:** PCB_VisualRAG_Project  
**Week:** Week 2  
**Date:** 2026-03-26  
**Author:** 杨杰康  

---

## 1. 本周总体情况

本周的核心目标是将 Week 1 已经搭建完成的页面级检索任务框架，推进为一套可比较、可评测、可分析的 baseline 实验流程。

围绕这一目标，本周完成了页面级 OCR 文本抽取、OCR 语料构建、OCR + BM25 baseline、OCR + Dense Retrieval baseline、Single-vector Visual Retrieval baseline，以及统一的结果汇总和 query-type 分析自动化。

整体来看，项目已经从“任务定义与评测框架可运行”进入到“基线系统可比较、实验结果可解释”的阶段。

本周关键词是：

> 跑通基线、统一评测、形成对照、支撑立论。

---

## 2. 本周完成内容

### 2.1 完成 OCR 页面文本抽取与质量检查

本周首先完成了页面级 OCR 流程，对 Week 1 中已经整理好的页面图像进行了批量文本抽取，并形成了统一的 OCR 页面语料。

相关输出包括：

| 类型 | 路径 |
|---|---|
| 原始 OCR 文本 | `data/ocr_raw/` |
| OCR 页面语料 | `data/metadata/ocr_corpus.jsonl` |
| OCR 日志 | `notes/day1_week2_ocr_log.txt` |
| OCR 质量检查记录 | `notes/ocr_quality_check_day1.txt` |

本阶段主要完成了以下工作：

- 对页面图像批量执行 OCR；
- 将页面级 OCR 文本组织到统一语料格式中；
- 检查 OCR 输出与 `page_id` 的对应关系；
- 对不同类型页面进行人工抽查；
- 确认 OCR 文本可以作为文本检索 baseline 的输入。

人工抽查结果表明，OCR 输出并非完全理想，部分页面存在小字号识别错误、符号缺失、表格结构混乱等问题。但整体上，OCR 仍然保留了页面中的大量关键术语、参数项、器件编号和标题信息，可以支持基础文本检索实验。

---

### 2.2 实现 OCR + BM25 baseline

在 OCR 语料可用后，本周实现并运行了第一个正式 baseline：OCR + BM25。

相关输出包括：

| 类型 | 路径 |
|---|---|
| Run 文件 | `results/baselines/bm25_run.tsv` |
| Metrics 文件 | `results/baselines/bm25_metrics.json` |
| 实验总结 | `notes/day2_bm25_summary.md` |

该 baseline 的基本流程为：

1. 使用 OCR 文本作为页面表示；
2. 使用 query 文本作为检索输入；
3. 通过 BM25 计算 query 与页面文本之间的词项匹配分数；
4. 为每个 query 输出 top-k 页面排序结果；
5. 调用统一评测脚本计算指标。

OCR + BM25 的 overall 结果如下：

| 指标 | 结果 |
|---|---:|
| Recall@1 | 0.1333 |
| Recall@5 | 0.6833 |
| Recall@10 | 0.8833 |
| MRR | 0.4105 |
| nDCG@10 | 0.5241 |

从结果看，BM25 成为了当前最强的 standalone baseline。这说明在当前 PCB 工程文档页面检索任务中，页面中的显式文本信息仍然具有很强的检索价值。

---

### 2.3 实现 OCR + Dense Text Retrieval baseline

在 BM25 baseline 完成后，本周进一步实现了 OCR + Dense Text Retrieval baseline。

相关输出包括：

| 类型 | 路径 |
|---|---|
| Run 文件 | `results/baselines/dense_text_run.tsv` |
| Metrics 文件 | `results/baselines/dense_text_metrics.json` |
| 实验总结 | `notes/day3_dense_text_summary.md` |

该 baseline 使用 OCR 文本作为页面输入，通过文本向量模型将页面文本和 query 编码到同一语义空间中，再基于向量相似度进行页面检索。

OCR + Dense Retrieval 的 overall 结果如下：

| 指标 | 结果 |
|---|---:|
| Recall@1 | 0.1000 |
| Recall@5 | 0.6000 |
| Recall@10 | 0.8000 |
| MRR | 0.3358 |
| nDCG@10 | 0.4420 |

从当前结果看，Dense Text Retrieval 整体表现优于纯视觉 baseline，但仍低于 BM25。

这说明在当前数据规模和 query 设定下，精确术语、参数项、器件名和局部文本线索仍然是页面检索性能的重要来源。Dense Retrieval 在 query 与页面原文词面不完全一致时可能具有补充价值，但尚未超过 BM25。

---

### 2.4 实现 Single-vector Visual Retrieval baseline

为了验证纯视觉页面检索在当前任务中的可行性，本周实现了 Single-vector Visual Retrieval baseline。

相关输出包括：

| 类型 | 路径 |
|---|---|
| Run 文件 | `results/baselines/single_vector_visual_run.tsv` |
| Metrics 文件 | `results/baselines/single_vector_visual_metrics.json` |
| 实验总结 | `notes/day4_single_vector_visual_summary.md` |

该 baseline 的基本设定为：

| 模块 | 说明 |
|---|---|
| 页面表示 | 每页一个全局图像向量 |
| Query 表示 | 文本 query 映射到同一向量空间 |
| 编码模型 | CLIP 系列视觉-文本模型 |
| 检索后端 | FAISS 向量检索 |
| 检索粒度 | Page-level |

Single-vector Visual Retrieval 的 overall 结果如下：

| 指标 | 结果 |
|---|---:|
| Recall@1 | 0.0000 |
| Recall@5 | 0.0833 |
| Recall@10 | 0.2500 |
| MRR | 0.0664 |
| nDCG@10 | 0.1041 |

该结果表明，单页单向量的全局视觉表示对 PCB 工程文档检索支持有限。原因可能包括：

- 全局视觉向量过度压缩页面信息；
- 技术文档中大量关键信息位于局部区域；
- 表格、参数、器件编号和图例需要细粒度匹配；
- 单个全局向量难以表达页面内部的结构关系。

因此，当前形式下的纯视觉 single-vector 方法还不足以替代 OCR/Text retrieval。

---

### 2.5 完成 Day 5 结果自动汇总与 query-type 分析

在三类 baseline 完成后，本周最后阶段重点进行了结果整理自动化，编写并运行了 Day 5 汇总脚本，生成统一结果表和分析文件。

相关输出包括：

| 类型 | 路径 |
|---|---|
| Baseline 汇总 CSV | `results/baselines/baseline_summary.csv` |
| Baseline 汇总 Excel | `results/baselines/baseline_summary.xlsx` |
| Query-type 结果 CSV | `results/analysis/results_by_query_type.csv` |
| Query-type 结果 Excel | `results/analysis/results_by_query_type.xlsx` |
| Query-type 数量统计 | `results/analysis/query_type_counts.csv` |
| 每类最佳方法 | `results/analysis/type_best_method.csv` |
| 初步结论 | `notes/day5_initial_conclusion.md` |
| Day 5 总结 | `notes/day5_summary.md` |

该自动化流程完成了以下工作：

- 从三个 baseline 的 metrics 文件中抽取 overall 指标；
- 从 run 文件、queries 和 qrels 中重新计算 query-type 指标；
- 统计每种 query type 的样本数量；
- 自动识别每种 query type 下表现最好的 baseline；
- 生成初步结论 markdown，支持后续周报和论文写作。

这一步说明项目已经不仅能运行实验，还能够将实验结果系统化整理为可分析、可复现、可写入论文的证据材料。

---

## 3. 本周关键实验结果

### 3.1 Overall baseline comparison

本周三类 baseline 的 overall comparison 如下：

| Method | Recall@1 | Recall@5 | Recall@10 | MRR | nDCG@10 |
|---|---:|---:|---:|---:|---:|
| OCR + BM25 | 0.1333 | 0.6833 | 0.8833 | 0.4105 | 0.5241 |
| OCR + Dense | 0.1000 | 0.6000 | 0.8000 | 0.3358 | 0.4420 |
| Single-vector Visual | 0.0000 | 0.0833 | 0.2500 | 0.0664 | 0.1041 |

从总体结果可以看到：

1. **OCR + BM25 是当前最强 baseline。**
2. **OCR + Dense 整体次之，表现稳定但仍弱于 BM25。**
3. **Single-vector Visual 显著落后于两种文本方法。**

这一结果说明，在当前 PCB 工程文档页面检索任务中，OCR-based text retrieval 仍然是最可靠的一阶段检索策略。

---

### 3.2 Query-type analysis

除了 overall 指标外，本周还对不同 query type 的表现进行了自动统计。该分析更贴近研究问题，因为它可以帮助识别不同类型查询更适合哪类检索方法。

当前已经观察到以下模式。

#### 3.2.1 参数查找类 query

对于 `parameter_lookup` 类型 query，文本方法表现更稳定。该类查询通常包含明确参数名、数值、器件名或表格字段，因此 BM25 可以利用精确词项匹配获得较好召回。

#### 3.2.2 跨页一致性类 query

对于 `cross_page_consistency` 类型 query，OCR + BM25 和 OCR + Dense 整体更有优势。这类查询往往依赖术语、接口名、器件编号或跨页文字线索，因此文本检索更适合。

#### 3.2.3 元件定位类 query

对于 `component_localization` 类型 query，BM25 可能出现失效，而 Dense Text 与 Visual 方法能够提供一定补充召回。这说明元件定位类查询并不完全依赖词面匹配，可能需要语义线索或视觉结构线索。

不过，Single-vector Visual 在该类型上仍未形成明显优势，说明当前全局视觉表示仍然不足以支撑高质量的结构定位。

---

## 4. 本周实验解读

### 4.1 文本检索仍是强基线

OCR + BM25 在当前三类 baseline 中表现最好，说明页面中的术语、参数表项、器件名、接口名和标题信息仍然是页面检索中的关键线索。

这也说明，在技术文档检索场景中，即使 OCR 存在一定噪声，只要关键文本信息大体可用，传统 lexical retrieval 仍然非常有竞争力。

---

### 4.2 Dense Retrieval 有补充价值，但尚未超过 BM25

OCR + Dense Retrieval 相比 BM25 更强调语义匹配，对 query 与页面文本词面不完全一致的情况可能有帮助。

但从整体指标看，它尚未超过 BM25。这表明当前任务仍然强依赖精确术语匹配，尤其是 PCB 工程文档中的参数名、器件编号和页面标题。

---

### 4.3 纯视觉检索当前不具备替代性

Single-vector Visual Retrieval 的结果较弱，说明使用单页全局视觉嵌入处理 PCB 工程文档页面检索存在明显局限。

主要原因包括：

- 页面包含大量细粒度文本与局部布局信息；
- query 往往指向局部结构、参数区域、表格条目或符号说明；
- 单个全局向量容易丢失局部技术细节；
- 当前视觉表示无法充分建模表格、结构和空间邻接关系。

因此，当前结果不支持“纯视觉检索比文本检索更鲁棒”的强主张。

---

### 4.4 更合理的研究叙事是文本与视觉互补

综合三类 baseline 的结果，本周更支持如下叙事：

- 文本检索是当前最强 standalone baseline；
- 纯视觉检索在 single-vector 形式下效果较弱；
- 视觉信号的价值更可能体现在与文本信号的融合或重排中；
- 后续需要探索 multi-vector late interaction，以增强视觉侧的局部结构匹配能力。

因此，当前论文叙事需要从“视觉替代文本”调整为：

> 文本检索在 PCB 工程文档中仍然是强基线，而视觉检索更适合作为补充信号，用于增强局部结构、视觉布局和证据区域的建模能力。

---

## 5. 本周新增脚本与结果文件

### 5.1 新增或重点使用脚本

本周新增或重点使用的脚本包括：

| 脚本 | 作用 |
|---|---|
| `scripts/preprocess/run_ocr_pages.py` | 页面级 OCR 文本抽取 |
| `scripts/retrieval/run_bm25.py` | OCR + BM25 baseline |
| `scripts/retrieval/run_dense_text_retrieval.py` | OCR + Dense Retrieval baseline |
| `scripts/retrieval/run_single_vector_visual_retrieval.py` | Single-vector Visual baseline |
| `scripts/analysis/day5_summarize_baselines.py` | Baseline 结果自动汇总与分析 |

---

### 5.2 关键结果文件

本周产生的关键结果文件包括：

| 文件 | 说明 |
|---|---|
| `data/metadata/ocr_corpus.jsonl` | 页面级 OCR 语料 |
| `results/baselines/bm25_run.tsv` | BM25 检索结果 |
| `results/baselines/bm25_metrics.json` | BM25 指标 |
| `results/baselines/dense_text_run.tsv` | Dense Text 检索结果 |
| `results/baselines/dense_text_metrics.json` | Dense Text 指标 |
| `results/baselines/single_vector_visual_run.tsv` | Single-vector Visual 检索结果 |
| `results/baselines/single_vector_visual_metrics.json` | Single-vector Visual 指标 |
| `results/baselines/baseline_summary.csv` | Baseline 总体汇总 |
| `results/analysis/results_by_query_type.csv` | 按 query type 的结果分析 |
| `results/analysis/type_best_method.csv` | 每类 query 的最佳方法 |

这些结果文件已经构成后续论文实验部分的基础材料。

---

## 6. 当前项目状态

截至 Week 2 结束，项目已经完成以下关键阶段：

- 页面级检索任务定义完成；
- query 与 qrels 体系建立完成；
- OCR 流程与 OCR 语料构建完成；
- OCR + BM25 baseline 完成；
- OCR + Dense Retrieval baseline 完成；
- Single-vector Visual Retrieval baseline 完成；
- 统一评测流程完成；
- 自动结果汇总与 query-type 分析流程完成。

因此，项目当前已经从“任务搭建阶段”进入到“实验分析与方法改进阶段”。

---

## 7. 当前仍存在的问题

### 7.1 数据规模仍然较小

当前数据集包含 10 份 PDF、101 页页面图像和 30 条 query，适合 pilot 实验和方法验证，但如果要形成更稳健的论文结论，后续仍需要扩展 query 数量和页面覆盖范围。

### 7.2 Single-vector Visual 表现较弱

当前 single-vector visual baseline 明显弱于 OCR-based baseline，说明全局视觉表示不足以支撑结构密集型工程文档检索。后续需要进一步探索：

- multi-vector late interaction；
- region-level visual representation；
- text-visual fusion；
- visual reranking。

### 7.3 OCR-based baseline 过强，论文叙事需要调整

当前实验结果并不支持“视觉方法全面优于 OCR/Text”的强结论。因此，后续论文叙事应更强调：

- OCR/Text 是强基线；
- Visual 单独使用较弱；
- Visual 更适合作为补充信号；
- 需要通过 multi-vector 或 reranking 提升视觉侧细粒度匹配能力。

### 7.4 需要开展 query-level error analysis

目前已有 overall 和 query-type 统计，但还需要进一步分析每条 query 的成功和失败情况，找出方法差异的具体原因。

---

## 8. 下周计划

下周的工作重点将不再是继续堆叠简单 baseline，而是围绕误差分析与改进方向展开。

### 8.1 开展 query-level error analysis

结合三种 run 文件，对典型 query 进行逐条分析，重点观察：

- BM25 为什么成功或失败；
- Dense Text 在哪些 query 上优于 BM25；
- Visual 在哪些 query 上完全失效；
- 三种方法是否存在互补；
- 哪些 query 是所有方法都难以解决的。

---

### 8.2 深入分析 query type 与失败模式

围绕不同 query type，进一步分析其主要难点：

| Query Type | 可能难点 |
|---|---|
| `parameter_lookup` | 依赖精确术语、参数名和表格字段 |
| `component_localization` | 需要局部区域级视觉建模 |
| `cross_page_consistency` | 需要跨页文本语义与实体对应 |
| `structure_legend_interpretation` | 依赖结构、符号和局部图例 |
| `similarity_based_interference` | 容易被相似页面干扰 |

---

### 8.3 设计下一阶段改进方法

根据本周结果，后续更值得尝试的方向包括：

- text + visual fusion；
- OCR-based coarse retrieval + visual reranking；
- region-level visual representation；
- multi-vector late interaction；
- OCR text + layout-aware modeling。

---

### 8.4 准备论文实验部分草稿

基于当前自动生成的表格和分析结果，开始整理实验章节草稿，包括：

- task setting；
- dataset construction；
- baselines；
- evaluation metrics；
- overall results；
- query-type analysis；
- discussion。

---

## 9. 本周总结

Week 2 的工作重点是把 Week 1 已经定义好的 PCB 页面检索任务，真正落地为一套可运行、可评测、可比较的 baseline 实验体系。

通过 OCR、BM25、Dense Text 和 Single-vector Visual 三类 baseline 的实现与比较，本周已经得到清晰的早期实验结论：

> 在当前任务设定下，OCR-based text retrieval 仍然是最强的 standalone baseline；纯视觉检索在全局单向量表示下效果较弱，更适合作为潜在补充信号，而不是文本检索的直接替代方案。

这一结论为后续进入 Full Multi-vector Late Interaction 实验提供了明确动机。
