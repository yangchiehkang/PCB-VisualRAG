# Week 1 Weekly Report

**Project:** PCB_VisualRAG_Project  
**Week:** Week 1  
**Date:** 2026-03-19  
**Author:** 杨杰康  

---

## 1. 本周总体情况

本周的核心目标是完成 PCB 工程文档 Visual Retrieval / Visual RAG 项目的基础搭建，包括项目目录整理、页面级语料构建、query 与 qrels 初版设计、统一结果格式定义、评测脚本实现，以及一次小规模端到端通路测试。

整体来看，本周已经成功将项目从“概念性研究想法”推进到“可运行任务框架”阶段。当前项目已经具备页面级语料、结构化 query、page-level qrels、统一 run 文件格式和基础评测脚本，能够在小样本上完成从输入 query 到输出评测指标的完整流程。

本周的关键词是：

> 规范定义、结构清晰、可闭环运行。

---

## 2. 本周完成内容

### 2.1 完成项目目录结构搭建

本周首先完成了项目基础目录结构的搭建与整理，将原始数据、页面图像、标注文件、元数据、脚本、结果、日志和实验记录等内容进行了统一管理。

当前项目主要目录包括：

| 目录 | 说明 |
|---|---|
| `data/raw_pdfs/` | 原始 PCB PDF 文档 |
| `data/images/` | PDF 页面渲染后的页面图像 |
| `data/annotations/` | 标注文件，包括页面标注和后续区域证据标注 |
| `data/metadata/` | corpus、queries、qrels、inventory 等元数据 |
| `scripts/` | 数据处理、检索、评测与分析脚本 |
| `results/` | 实验 run 文件、metrics 文件和分析结果 |
| `logs/` | 程序运行日志 |
| `notes/` | 实验笔记、设计说明和阶段性记录 |
| `reports/` | 周报与阶段报告 |

该目录结构为后续 baseline 接入、实验管理和结果复现提供了统一基础。

---

### 2.2 完成页面级语料与元数据构建

围绕页面级检索任务，本周完成了 PCB PDF 文档的页面级整理，并建立了多类基础元数据文件。

当前核心元数据文件包括：

| 文件 | 作用 |
|---|---|
| `data/metadata/document_inventory.csv` | 文档级清单 |
| `data/metadata/page_inventory.csv` | 页面级清单 |
| `data/metadata/corpus.jsonl` | 页面级语料文件 |
| `data/metadata/queries.jsonl` | 查询集合 |
| `data/metadata/qrels.tsv` | query-page 相关性标注 |
| `data/metadata/query_taxonomy.md` | query 类型定义 |
| `data/metadata/run_format.md` | 检索结果格式说明 |

当前任务统一采用 **page image as retrieval unit**，即以页面作为最小检索单元。每个页面通过 `page_id` 唯一标识，并与 `doc_id`、`page_no`、`image_path` 等信息关联。

截至本周结束，当前页面级语料库已经包括：

| 项目 | 数量 |
|---|---:|
| PDF 文档数 | 10 |
| 页面图像数 | 101 |
| Query 数量 | 30 |
| 检索粒度 | Page-level |

---

### 2.3 完成 Query 与 qrels 初版构建

本周完成了 query 草案生成、query 类型整理以及 qrels 初版构建。当前 query 并不是简单的关键词查询，而是围绕 PCB 工程文档检索和 Visual RAG 场景设计的任务型查询。

当前 query 类型包括：

| Query Type | 说明 |
|---|---|
| `parameter_lookup` | 参数查找类查询 |
| `structure_legend_interpretation` | 结构、图例或符号解释类查询 |
| `component_localization` | 元件定位类查询 |
| `cross_page_consistency` | 跨页一致性检查类查询 |
| `similarity_based_interference` | 相似页面干扰类查询 |

对应的 qrels 文件采用 **page-level relevance** 标注，即每条 query 对应一个或多个相关页面。

qrels 文件路径为：

- `data/metadata/qrels.tsv`

该文件为后续 Recall@k、MRR 和 nDCG 等指标计算提供了真值依据。

---

### 2.4 定义统一 results TSV 格式

为了保证后续不同 baseline 和实验方法能够被统一评测，本周定义了统一的检索结果文件格式。

统一 run 文件字段如下：

| 字段名 | 含义 |
|---|---|
| `run_name` | 实验名称 |
| `query_id` | 查询 ID |
| `page_id` | 返回页面 ID |
| `rank` | 检索排名 |
| `score` | 检索分数 |

该格式已经在 smoke test 中使用，并被评测脚本成功读取。

统一结果格式的建立降低了后续接入 OCR + BM25、OCR + Dense、Single-vector Visual、Full Multi-vector 等方法的成本。

---

### 2.5 实现基础评测脚本

本周完成了基础评测脚本的实现，支持读取：

- run 文件；
- `qrels.tsv`；
- `queries.jsonl`。

当前评测脚本支持输出 overall metrics 和按 `query_type` 分组的指标。

已支持的指标包括：

| 指标 | 说明 |
|---|---|
| `Recall@1` | Top-1 召回率 |
| `Recall@3` | Top-3 召回率 |
| `Recall@5` | Top-5 召回率 |
| `Recall@10` | Top-10 召回率 |
| `MRR` | Mean Reciprocal Rank |
| `nDCG@1` | Top-1 归一化折损累计增益 |
| `nDCG@3` | Top-3 nDCG |
| `nDCG@5` | Top-5 nDCG |
| `nDCG@10` | Top-10 nDCG |

这一评测脚本的完成，使项目从“有数据和标注”进一步推进到“能够量化比较方法表现”的阶段。

---

### 2.6 完成小规模端到端通路测试

在本周收口阶段，完成了一次小规模 smoke test，用于验证各模块之间是否能够正确连通。

测试流程如下：

1. 读取 query 子集；
2. 构造小规模 run 文件；
3. 读取 qrels；
4. 调用评测脚本；
5. 输出 overall metrics；
6. 输出按 query type 分组的评测结果；
7. 检查 `query_id`、`page_id` 和 qrels 是否匹配。

测试结果表明：

- query 文件可被正常读取；
- qrels 可正确匹配；
- run 文件格式可解析；
- 评测脚本能够输出指标；
- 整个实验链路已经打通。

这说明当前研究工作已经不是停留在概念层面的设想，而是一套可以实际运行的页面级检索任务框架。

---

## 3. 本周关键产出

本周形成的主要产出如下：

| 类型 | 文件或目录 |
|---|---|
| 页面图像库 | `data/images/` |
| 原始 PDF | `data/raw_pdfs/` |
| 文档清单 | `data/metadata/document_inventory.csv` |
| 页面清单 | `data/metadata/page_inventory.csv` |
| 页面语料 | `data/metadata/corpus.jsonl` |
| Query 文件 | `data/metadata/queries.jsonl` |
| qrels 文件 | `data/metadata/qrels.tsv` |
| Query 类型说明 | `data/metadata/query_taxonomy.md` |
| Run 格式说明 | `data/metadata/run_format.md` |
| 评测脚本 | `scripts/eval/` |
| Smoke test 结果 | `results/` |

---

## 4. 本周已解决的问题

本周主要解决了以下问题：

1. **统一了项目目录结构**  
   避免了数据、脚本、结果和日志分散管理的问题。

2. **建立了 page-level 检索任务定义**  
   明确以页面作为最小检索单元，为后续 Visual Retrieval 和 Visual RAG 提供基础。

3. **建立了统一 ID 体系**  
   通过 `doc_id`、`page_id` 和 `query_id` 保证数据、标注和结果可以相互匹配。

4. **完成了 query 与 qrels 初版**  
   当前任务已经具备基本的真值标注，可以进行正式评测。

5. **实现了基础评测闭环**  
   已经能够从 run 文件计算 Recall@k、MRR 和 nDCG 等指标。

6. **支持按 query type 分析**  
   为后续分析不同类型查询上的方法差异提供了基础。

---

## 5. 当前仍存在的问题

虽然本周已经完成了基础框架搭建，但当前仍存在以下不足。

### 5.1 当前 run 文件仍以测试为主

本周的 run 文件主要用于 smoke test，还不是由真实 baseline 自动生成。因此，本周结果主要用于验证流程可运行，而不是评估方法性能。

### 5.2 Query 数量仍然较少

当前 query 数量为 30 条，适合 pilot 实验和初步方法验证，但后续如果要形成更有说服力的论文实验结果，需要进一步扩展 query 数量。

### 5.3 qrels 标注仍需持续审查

当前 qrels 已经能够支持评测，但后续需要继续检查：

- 是否存在多个相关页面但只标注了一个；
- 是否存在 query 表述过于模糊；
- 是否存在 page-level 标注过严或过松；
- 是否需要区分主证据页和辅助证据页。

### 5.4 评测脚本需要增强鲁棒性

后续需要补充输入合法性检查，例如：

- 重复 rank；
- 重复 query-page pair；
- 缺失字段；
- 非法 score；
- run 文件只覆盖部分 query 时的评测范围控制。

---

## 6. 本周阶段性结论

本周最重要的成果不是某个模型指标，而是完成了页面级检索任务的规范化定义和可运行闭环。

当前项目已经具备：

- 页面级语料；
- 结构化 query；
- page-level qrels；
- 统一 run 格式；
- 可执行评测脚本；
- 小规模端到端测试结果。

因此，项目已经从“研究想法”进入到“可实验、可评测、可扩展”的阶段。

---

## 7. 下周计划

下周工作重点将从“搭建任务框架”转向“跑通正式 baseline”。

### 7.1 完成 OCR 页面文本抽取

对所有页面图像执行 OCR，构建页面级 OCR 文本语料，为文本检索 baseline 提供输入。

### 7.2 实现 OCR + BM25 baseline

使用 OCR 文本作为页面表示，构建 BM25 检索基线，并输出标准 run 文件和评测结果。

### 7.3 实现 OCR + Dense Retrieval baseline

使用文本向量模型对 OCR 文本和 query 进行编码，完成稠密文本检索 baseline。

### 7.4 实现 Single-vector Visual Retrieval baseline

使用视觉或视觉语言模型为每页生成一个全局向量，验证单向量视觉检索在当前任务中的表现。

### 7.5 汇总 baseline 结果并按 query type 分析

统一三类 baseline 的指标输出，形成 overall comparison 和 query-type analysis。

---

## 8. 本周总结

Week 1 的工作重点是建立 PCB 工程文档页面级检索任务的基础设施。通过本周工作，项目已经完成了数据组织、query/qrels 初版、统一结果格式、评测脚本和小规模端到端测试。

当前项目已经具备稳定起点。下一步将进入 OCR/Text baseline 与 Single-vector Visual baseline 阶段，通过真实检索结果验证任务设定，并为后续 Full Multi-vector Late Interaction 实验提供对照基础。
