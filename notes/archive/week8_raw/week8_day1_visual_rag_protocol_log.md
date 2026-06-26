# Week 8 Day 1 实验日志：轻量 Visual RAG 下游验证协议与 QA 输入构造

**日期**：2026-05-08  
**项目**：PCB_VisualRAG_Project  
**环境**：`pcb_visualrag`  
**工作目录**：`E:\Working\PCB_VisualRAG_Project`  
**阶段**：Week 8 Day 1  
**主题**：Lightweight Visual RAG Protocol and QA Input Construction  
**状态**：Completed with follow-up fix needed  

---

## 1. 今日目标

Week 8 Day 1 的目标是启动轻量 Visual RAG / QA 下游验证任务，并建立论文写作材料目录。

本日主要完成：

1. 创建 Week 8 结果目录；
2. 创建论文写作目录；
3. 生成轻量 Visual RAG 下游验证协议；
4. 固定 QA 输入设置与评估指标；
5. 生成论文 claims / sections outline / figures manifest；
6. 构造 Week 8 QA 输入文件；
7. 检查 query text 与 occlusion image path 是否完整。

---

## 2. 创建目录结构

### 2.1 Week 8 结果目录

执行命令：

```bash
mkdir results\week8
mkdir results\week8\visual_rag
mkdir results\week8\visual_rag\inputs
mkdir results\week8\visual_rag\outputs
mkdir results\week8\visual_rag\tables
```

生成目录：

```text
results/week8/
results/week8/visual_rag/
results/week8/visual_rag/inputs/
results/week8/visual_rag/outputs/
results/week8/visual_rag/tables/
```

---

### 2.2 论文写作目录

执行命令：

```bash
mkdir paper
mkdir paper\sections
mkdir paper\figures
mkdir paper\tables
mkdir paper\notes
```

生成目录：

```text
paper/
paper/sections/
paper/figures/
paper/tables/
paper/notes/
```

---

## 3. Task 1：生成轻量 Visual RAG 验证协议

### 3.1 执行脚本

执行命令：

```bash
python scripts\evaluation\prepare_week8_day1_visual_rag_protocol.py
```

终端输出：

```text
[Week8-Day1] Visual RAG protocol prepared.
Wrote: E:\Working\PCB_VisualRAG_Project\results\week8\visual_rag\visual_rag_protocol.md
Wrote: E:\Working\PCB_VisualRAG_Project\results\week8\visual_rag\qa_settings.csv
Wrote: E:\Working\PCB_VisualRAG_Project\results\week8\visual_rag\qa_metrics_definition.csv
Wrote: E:\Working\PCB_VisualRAG_Project\paper\notes\claims_and_evidence.md
Wrote: E:\Working\PCB_VisualRAG_Project\paper\notes\sections_outline.md
Wrote: E:\Working\PCB_VisualRAG_Project\paper\notes\figures_manifest.md
```

---

### 3.2 输出文件

本任务生成以下文件：

```text
results/week8/visual_rag/visual_rag_protocol.md
results/week8/visual_rag/qa_settings.csv
results/week8/visual_rag/qa_metrics_definition.csv

paper/notes/claims_and_evidence.md
paper/notes/sections_outline.md
paper/notes/figures_manifest.md
```

---

## 4. Visual RAG 验证协议内容

### 4.1 下游验证闭环

本周轻量 Visual RAG / QA 验证采用如下闭环：

```text
Query
↓
Retrieval Result
↓
Evidence Page / Page Subset
↓
VLM Answer
↓
Answer Evaluation
```

当前 Windows `type` 命令显示 Markdown 时，箭头符号出现编码显示问题：

```text
鈫?
```

该问题属于终端编码显示问题，不影响文件内容本身。后续可使用 UTF-8 编辑器或执行：

```bash
chcp 65001
```

后再查看。

---

### 4.2 验证问题

本实验需要验证三件事：

```text
1. Does retrieval evidence quality affect answer quality?
2. Can Budgeted Retrieval still support Visual QA / RAG?
3. Does Evidence Occlusion affect downstream answers?
```

对应中文目标：

```text
1. 检索证据质量是否影响回答质量；
2. Budgeted Retrieval 是否仍能支撑 Visual QA / RAG；
3. Evidence Occlusion 的影响是否会传导到下游回答。
```

---

### 4.3 QA 输入设置

执行命令：

```bash
type results\week8\visual_rag\qa_settings.csv
```

输出结果：

| Setting | Source | Purpose | Required |
|---|---|---|---|
| Gold Evidence | gold evidence page | QA upper bound | yes |
| BM25 | BM25 top retrieval result | strong OCR/text baseline | yes |
| Full MV | Full multi-vector retrieval result | visual retrieval baseline | recommended |
| Hybrid Fusion | hybrid BM25 + MV retrieval result | text-visual fusion validation | yes |
| Budgeted MV | budgeted multi-vector retrieval result | budgeted retrieval downstream validation | optional |
| Gold Masked | gold evidence region masked page | test evidence occlusion effect | yes |
| Random Masked | random region masked page | occlusion control | yes |

---

### 4.4 QA 评估指标

执行命令：

```bash
type results\week8\visual_rag\qa_metrics_definition.csv
```

输出结果：

| Metric | Type | Values | Description |
|---|---|---|---|
| Answer Correctness | binary | 0/1 | Whether the answer is correct. |
| Evidence Supported | binary | 0/1 | Whether the answer is supported by visible page evidence. |
| Unknown Rate | binary | 0/1 | Whether the model answers not enough evidence / unknown. |
| Answer Consistency | categorical | same/changed | Whether the answer changes across input settings. |
| Error Type | categorical | wrong_page/masked_evidence/hallucination/insufficient_info/ocr_error/none | Manual error category. |

---

### 4.5 固定 Prompt Template

当前协议中固定的 QA prompt 为：

```text
You are answering a question about a PCB engineering document page.
Use only the provided page image as evidence.
If the page does not contain enough information, answer "Not enough evidence".

Question:
{query}

Return:
1. Short answer
2. Evidence description
3. Confidence: high / medium / low
```

---

## 5. 论文写作材料初始化

### 5.1 Claims and Evidence

执行命令：

```bash
type paper\notes\claims_and_evidence.md
```

核心 claim：

```text
This work proposes a budget-aware VisualRAG retrieval framework for PCB documents. 
While OCR-based BM25 remains a strong overall baseline, visual multi-vector retrieval 
and hybrid fusion provide complementary evidence-aware retrieval signals.
```

---

### 5.2 已支持的论文主张

| Claim | Evidence | Source |
|---|---|---|
| BM25 remains a strong overall baseline | Highest main retrieval nDCG@10 | Week 7 Table 14 |
| Hybrid Fusion matches BM25 on evidence retrieval | Evidence Hit@5 = 1.0000, Evidence Hit@10 = 1.0000 | Week 7 Table 16 |
| Hybrid Fusion improves region-level localization | Region Hit@5 = 0.4000 | Week 7 Region Hit |
| Gold evidence region is causally important | Gold Mask score drops to 0.00000000 | Week 7 Table 17 |
| Downstream QA should reflect evidence quality | To be validated | Week 8 Visual RAG |

---

### 5.3 需要避免的论文表述

当前文件中明确记录了需要避免的 claim：

```text
1. Do not claim that the visual method universally outperforms BM25.
2. Do not claim end-to-end model training.
3. Do not claim full automatic answer evaluation if manual scoring is used.
```

该部分对后续论文写作非常重要，因为 Week 7 主结果显示 BM25 仍是强整体检索基线，因此论文主张应强调：

```text
evidence-aware complementary visual retrieval
```

而不是简单声称：

```text
visual method universally outperforms BM25
```

---

### 5.4 论文章节骨架

执行命令：

```bash
type paper\notes\sections_outline.md
```

当前章节骨架：

```text
1. Introduction
2. Related Work
3. Problem Setup
4. Method
5. Experimental Setup
6. Main Results
7. Evidence Attribution and Counterfactual Validation
8. Lightweight Visual RAG Downstream Validation
9. Discussion and Limitations
10. Conclusion
```

Week 8 写作优先级：

```text
1. Problem Setup
2. Method
3. Introduction
4. Experiments outline
```

---

### 5.5 图表目录初版

执行命令：

```bash
type paper\notes\figures_manifest.md
```

当前图表目录：

| ID | Item | Status | Source |
|---|---|---|---|
| Figure 1 | Overall Pipeline | TODO | paper/figures/fig1_pipeline.pdf |
| Table 1 | Baseline Retrieval Results | Available | previous results |
| Table 2 | Budgeted Retrieval Results | Available | Week 6 / Week 7 |
| Table 3 | BM25-C2F and Hybrid Results | Available | Week 7 Table 14 |
| Table 4 | Evidence Hit / Region Hit | Available | Week 7 Table 16 + Region Hit |
| Table 5 | Occlusion Main Results | Available | Week 7 Table 17 |
| Figure 2 | Occlusion Visual Cases | Available | figures/week7/evidence_case_*.png |
| Table 6 | Lightweight Visual RAG Results | TODO | Week 8 Table 19 |
| Figure 3 | Retrieval Quality vs QA Quality | TODO | Week 8 |

---

## 6. Task 2：构造 Visual RAG QA 输入

### 6.1 执行脚本

执行命令：

```bash
python scripts\evaluation\build_week8_day1_visual_rag_inputs.py
```

终端输出：

```text
[Week8-Day1] QA inputs generated.
Rows: 70
Queries: 10
Settings per query: 7
Wrote: E:\Working\PCB_VisualRAG_Project\results\week8\visual_rag\qa_inputs.jsonl
Wrote: E:\Working\PCB_VisualRAG_Project\results\week8\visual_rag\qa_inputs.csv
Wrote: E:\Working\PCB_VisualRAG_Project\results\week8\visual_rag\qa_inputs_preview.md

Missing query text count: 0
Missing image path count: 0
```

---

### 6.2 输出文件

生成以下文件：

```text
results/week8/visual_rag/qa_inputs.jsonl
results/week8/visual_rag/qa_inputs.csv
results/week8/visual_rag/qa_inputs_preview.md
```

---

### 6.3 样本规模

当前 QA 输入构造结果：

```text
Queries: 10
Settings per query: 7
Rows: 70
```

即：

```text
10 evidence queries × 7 input settings = 70 QA cases
```

---

## 7. QA 输入条件

当前每个 query 包含 7 个 setting：

```text
Gold Evidence
BM25
Full MV
Hybrid Fusion
Budgeted MV
Gold Masked
Random Masked
```

其中：

```text
Gold Evidence / Gold Masked / Random Masked
```

均已成功关联到 Week 7 生成的 occlusion page images。

---

## 8. Query Text 检查

### 8.1 检查结果

脚本输出：

```text
Missing query text count: 0
```

说明所有 10 条 evidence query 均已成功从：

```text
data/metadata/queries.jsonl
```

补全 query text。

---

### 8.2 evidence subset 原始问题

检查文件：

```bash
type data\annotations\evidence_query_subset.jsonl
```

发现 evidence subset 中 query 字段为空：

```json
{"query_id": "q001", "query": "", "gold_page_id": "doc001_p001", ...}
```

但输入构造脚本已成功从：

```text
data/metadata/queries.jsonl
```

中按 query_id 补齐 query text，因此当前 QA 输入中 query 字段完整。

---

### 8.3 已补齐的 query 示例

例如 q001：

```text
Which page contains the fabrication requirements table with material, panel, and special requirement specifications?
```

q011：

```text
Which page contains the populated board and zoomed assembly view for the SOT323 grounded emitter variant?
```

q012：

```text
Which page contains the populated board and zoomed assembly view for the SOT323 emitter degeneration variant?
```

---

## 9. Occlusion 图像路径检查

### 9.1 检查结果

脚本输出：

```text
Missing image path count: 0
```

说明以下条件均已成功关联 image path：

```text
Gold Evidence
Gold Masked
Random Masked
```

---

### 9.2 图像路径来源

图像路径来自：

```text
results/week7/occlusion/occlusion_inputs.csv
```

示例：

```text
artifacts\occlusion_pages\q001_doc001_p001_original.png
artifacts\occlusion_pages\q001_doc001_p001_gold_mask.png
artifacts\occlusion_pages\q001_doc001_p001_random_mask.png
```

---

### 9.3 occlusion 条件状态

`occlusion_inputs.csv` 中所有样本状态均为：

```text
PASSED
```

说明 Week 7 的 occlusion 页面可直接用于 Week 8 下游 QA 验证。

---

## 10. 当前 QA 输入预览

执行命令：

```bash
type results\week8\visual_rag\qa_inputs_preview.md
```

预览显示每个 query 均包含：

```text
Gold Evidence
BM25
Full MV
Hybrid Fusion
Budgeted MV
Gold Masked
Random Masked
```

示例 q001：

| Query ID | Setting | Gold Page | Input Page | Image Path |
|---|---|---|---|---|
| q001 | Gold Evidence | doc001_p001 | doc001_p001 | artifacts\occlusion_pages\q001_doc001_p001_original.png |
| q001 | BM25 | doc001_p001 |  |  |
| q001 | Full MV | doc001_p001 |  |  |
| q001 | Hybrid Fusion | doc001_p001 |  |  |
| q001 | Budgeted MV | doc001_p001 |  |  |
| q001 | Gold Masked | doc001_p001 | doc001_p001 | artifacts\occlusion_pages\q001_doc001_p001_gold_mask.png |
| q001 | Random Masked | doc001_p001 | doc001_p001 | artifacts\occlusion_pages\q001_doc001_p001_random_mask.png |

---

## 11. 当前发现的问题

### 11.1 Retrieval setting 的 page_id / rank / score 为空

在当前 `qa_inputs.csv` 中，以下 setting 的 retrieval result 字段为空：

```text
BM25
Full MV
Hybrid Fusion
Budgeted MV
```

表现为：

```text
page_id = empty
rank = empty
retrieval_score = empty
image_path = empty
```

示例：

```text
q001, ..., BM25, doc001_p001,,,,,
q001, ..., Full MV, doc001_p001,,,,,
q001, ..., Hybrid Fusion, doc001_p001,,,,,
q001, ..., Budgeted MV, doc001_p001,,,,,
```

---

### 11.2 问题原因判断

初步判断原因是：

```text
build_week8_day1_visual_rag_inputs.py 中的 read_trec_run() 解析逻辑未匹配当前 run.tsv 文件格式。
```

当前脚本假设 run 文件为 TREC 格式：

```text
query_id Q0 doc_id rank score method
```

但实际 Week 7 run 文件可能为 CSV / TSV header 格式，例如：

```text
query_id	page_id	rank	score
```

或包含不同字段名。

---

### 11.3 影响范围

该问题不影响以下部分：

```text
1. Visual RAG protocol 已生成；
2. Query text 已补齐；
3. Gold Evidence / Gold Masked / Random Masked 图像路径完整；
4. Week 8 目录与论文写作材料已初始化。
```

但会影响后续：

```text
BM25 / Full MV / Hybrid Fusion / Budgeted MV 检索结果接入下游 QA。
```

因此 Day 2 前需要修复 retrieval run 解析，并为 retrieval setting 补齐：

```text
page_id
rank
retrieval_score
image_path
```

---

## 12. 当前结果目录检查

执行命令：

```bash
dir results\week8\visual_rag
```

输出：

```text
05/08/2026  05:59 PM    <DIR>          inputs
05/08/2026  05:59 PM    <DIR>          outputs
05/08/2026  06:02 PM            15,240 qa_inputs.csv
05/08/2026  06:02 PM            26,919 qa_inputs.jsonl
05/08/2026  06:02 PM             5,396 qa_inputs_preview.md
05/08/2026  06:01 PM               481 qa_metrics_definition.csv
05/08/2026  06:01 PM               558 qa_settings.csv
05/08/2026  05:59 PM    <DIR>          tables
05/08/2026  06:01 PM             2,383 visual_rag_protocol.md
```

当前共生成：

```text
6 个文件
5 个目录
```

---

## 13. Day 1 输出文件总览

### 13.1 Week 8 Visual RAG 文件

```text
results/week8/visual_rag/visual_rag_protocol.md
results/week8/visual_rag/qa_settings.csv
results/week8/visual_rag/qa_metrics_definition.csv
results/week8/visual_rag/qa_inputs.jsonl
results/week8/visual_rag/qa_inputs.csv
results/week8/visual_rag/qa_inputs_preview.md
```

---

### 13.2 论文写作材料文件

```text
paper/notes/claims_and_evidence.md
paper/notes/sections_outline.md
paper/notes/figures_manifest.md
```

---

## 14. Day 1 验收结论

### 14.1 已完成部分

| Task | 内容 | Status |
|---|---|---|
| Task 1 | 创建 Week 8 结果目录 | PASSED |
| Task 2 | 创建论文写作目录 | PASSED |
| Task 3 | 生成 Visual RAG protocol | PASSED |
| Task 4 | 固定 QA settings | PASSED |
| Task 5 | 固定 QA metrics | PASSED |
| Task 6 | 生成 claims and evidence | PASSED |
| Task 7 | 生成 paper sections outline | PASSED |
| Task 8 | 生成 figures manifest | PASSED |
| Task 9 | 构造 70 条 QA 输入 | PASSED |
| Task 10 | 补齐 query text | PASSED |
| Task 11 | 补齐 occlusion image paths | PASSED |

---

### 14.2 待修复部分

| Issue | 内容 | Priority |
|---|---|---:|
| Retrieval run parsing | BM25 / Full MV / Hybrid Fusion / Budgeted MV 的 page_id、rank、score 为空 | High |
| Retrieval image mapping | retrieval result page_id 需要映射到 page image path | High |
| QA inference chain | 尚未接入 VLM 进行回答生成 | Day 2 |
| QA evaluation | 尚未生成人工/半自动评分表 | Day 2-3 |

---

## 15. Day 1 总结

Week 8 Day 1 已完成轻量 Visual RAG 下游验证的协议设计、输入设置、评估指标、论文 claim 管理、章节骨架和图表目录初始化。

同时，已成功构造 10 条 evidence query × 7 种 setting 的 QA 输入框架，共 70 条样本。所有 query text 均已补齐，Gold Evidence / Gold Masked / Random Masked 的图像路径均完整。

当前唯一需要在 Day 2 前修复的问题是 retrieval run 解析逻辑：BM25 / Full MV / Hybrid Fusion / Budgeted MV 的检索页面、rank 和 score 尚未成功写入 QA 输入表。

最终状态：

```text
Week 8 Day 1 Lightweight Visual RAG Protocol: PASSED
Week 8 Day 1 QA Input Skeleton: PASSED_WITH_RETRIEVAL_MAPPING_FIX_NEEDED
```
---

# Week 8 Day 1 补充日志：下游输入条件与 Retrieval 映射诊断

**日期**：2026-05-08  
**时间**：18:14  
**项目**：PCB_VisualRAG_Project  
**环境**：`pcb_visualrag`  
**工作目录**：`E:\Working\PCB_VisualRAG_Project`  
**任务主题**：Lightweight Visual RAG Input Conditions and Retrieval Mapping Diagnosis  
**状态**：Partially Completed / Retrieval Mapping Still Needs Fix  

---

## 1. 本轮目标

本轮工作围绕第 8 周计划中的 **3.2 下游输入条件** 展开，目标是将轻量 Visual RAG / QA 的输入条件正式落到可执行数据文件中。

计划接入以下输入条件：

| 条件 | 说明 |
|---|---|
| Gold Evidence | 使用人工标注的 gold evidence page，作为回答上限参考 |
| Full MV Retrieval | 使用 Full Multi-vector Retrieval 返回的页面 |
| Budgeted Retrieval | 使用 Budgeted Multi-vector Retrieval 返回的页面 |
| Random / Weak Retrieval | 可选，用作弱对照 |
| Gold Region Masked | 使用遮挡 gold evidence region 的页面 |
| Random Region Masked | 使用遮挡随机区域的页面 |

实际实现中，为了增强对照性，当前设置为：

```text
Gold Evidence
BM25
Full MV
Hybrid Fusion
Budgeted MV
Gold Masked
Random Masked
```

---

## 2. Week 7 Run 文件检查

### 2.1 检查 run.tsv 文件

执行命令：

```bash
dir results\week7 /s /b | findstr /I "run.tsv"
```

检查到 Week 7 中存在以下主要 run 文件：

```text
results\week7\c2f_fixed_N\bm25_budgetmv_N20_M16_none_run.tsv
results\week7\c2f_fixed_N\bm25_budgetmv_N20_M8_none_run.tsv
results\week7\c2f_fixed_N\bm25_budgetmv_N50_M24_none_run.tsv
results\week7\c2f_fixed_N\bm25_fullmv_N100_run.tsv
results\week7\c2f_fixed_N\bm25_fullmv_N10_run.tsv
results\week7\c2f_fixed_N\bm25_fullmv_N20_run.tsv
results\week7\c2f_fixed_N\bm25_fullmv_N50_run.tsv
results\week7\hybrid_fusion\hybrid_budgetmv_N50_M24_alpha0p0_run.tsv
...
results\week7\hybrid_fusion\hybrid_budgetmv_N50_M24_alpha1p0_run.tsv
results\week7\hybrid_fusion\hybrid_fullmv_N50_alpha0p0_run.tsv
...
results\week7\hybrid_fusion\hybrid_fullmv_N50_alpha1p0_run.tsv
```

结论：

```text
Week 7 的 Full MV、Budgeted MV、Hybrid Fusion run 文件均存在。
```

---

### 2.2 检查 hybrid 文件

执行命令：

```bash
dir results\week7 /s /b | findstr /I "hybrid"
```

确认 `results/week7/hybrid_fusion/` 下包含：

```text
hybrid_alpha_ablation_table.csv
hybrid_alpha_ablation_table.md
hybrid_alpha_all_results.csv
hybrid_alpha_best_results.csv
hybrid_alpha_best_results.json
hybrid_budgetmv_N50_M24_alpha*_run.tsv
hybrid_fullmv_N50_alpha*_run.tsv
hybrid_fusion_summary.csv
hybrid_fusion_summary.json
```

结论：

```text
Hybrid Fusion 实验结果完整，可作为 Week 8 下游输入来源。
```

---

### 2.3 检查 c2f 文件

执行命令：

```bash
dir results\week7 /s /b | findstr /I "c2f"
```

确认 `results/week7/c2f_fixed_N/` 下包含：

```text
bm25_fullmv_N10_run.tsv
bm25_fullmv_N20_run.tsv
bm25_fullmv_N50_run.tsv
bm25_fullmv_N100_run.tsv
bm25_budgetmv_N20_M8_none_run.tsv
bm25_budgetmv_N20_M16_none_run.tsv
bm25_budgetmv_N50_M24_none_run.tsv
bm25_c2f_main_results.csv
bm25_c2f_main_results.md
coarse_recall_atN.csv
query_type_delta_analysis.csv
```

结论：

```text
BM25-guided C2F reranking 的 Full MV 与 Budgeted MV 文件均存在。
```

---

## 3. Run 文件格式诊断

### 3.1 执行诊断脚本

执行命令：

```bash
python scripts\evaluation\diagnose_week8_run_files.py
```

---

### 3.2 诊断结果

诊断显示当前 run 文件格式为：

```text
run_name        query_id        page_id rank    score
```

示例：

```text
hybrid_fullmv_N50_alpha1p0      q001    doc006_p019     1       1.00000000
hybrid_fullmv_N50_alpha1p0      q001    doc001_p001     2       0.88666938
```

另一个示例：

```text
bm25_fullmv_N10 q001    doc006_p013     1       1.03309250
bm25_fullmv_N10 q001    doc003_p004     2       1.01229644
```

结论：

```text
当前 Week 7 run 文件不是标准 TREC 格式，也不是 query_id/page_id/rank/score 四列格式；
它是五列 TSV 格式：
run_name, query_id, page_id, rank, score
```

---

## 4. 第一次运行 Fixed 脚本失败

### 4.1 执行命令

```bash
python scripts\evaluation\build_week8_visual_rag_inputs_fixed.py
```

---

### 4.2 报错信息

```text
TypeError: '<' not supported between instances of 'int' and 'str'
```

报错位置：

```text
if new_rank < old_rank:
```

---

### 4.3 原因

原因是旧版本脚本中 `rank` 字段存在字符串和整数混用问题：

```text
new_rank = int
old_rank = str
```

导致 Python 不能比较：

```text
int < str
```

---

### 4.4 修复方式

随后对脚本进行了修改，加入：

```python
safe_int()
safe_float()
```

并在 rank 比较时统一转为整数：

```python
old_rank = safe_int(result[qid].get("rank", 999999), default=999999)
new_rank = safe_int(rank, default=999999)
```

修复后 TypeError 消失。

---

## 5. 第二次运行 Fixed 脚本成功但映射失败

### 5.1 执行命令

```bash
python scripts\evaluation\build_week8_visual_rag_inputs_fixed.py
```

---

### 5.2 运行结果

终端输出：

```text
[Week8] Fixed QA inputs generated.
Rows: 70
Wrote: E:\Working\PCB_VisualRAG_Project\results\week8\visual_rag\qa_inputs_fixed.jsonl
Wrote: E:\Working\PCB_VisualRAG_Project\results\week8\visual_rag\qa_inputs_fixed.csv
Wrote: E:\Working\PCB_VisualRAG_Project\results\week8\visual_rag\qa_inputs_fixed_preview.md
Wrote: E:\Working\PCB_VisualRAG_Project\results\week8\visual_rag\qa_input_mapping_summary.csv
```

---

### 5.3 使用的 run 文件

脚本实际使用的 run 文件如下：

| Setting | Used Run File |
|---|---|
| BM25 | `results\week7\hybrid_fusion\hybrid_fullmv_N50_alpha1p0_run.tsv` |
| Full MV | `results\week7\c2f_fixed_N\bm25_fullmv_N10_run.tsv` |
| Hybrid Fusion | `results\week7\hybrid_fusion\hybrid_budgetmv_N50_M24_alpha1p0_run.tsv` |
| Budgeted MV | `results\week7\c2f_fixed_N\bm25_budgetmv_N20_M8_none_run.tsv` |

---

## 6. 映射结果检查

### 6.1 查看映射汇总

执行命令：

```bash
type results\week8\visual_rag\qa_input_mapping_summary.csv
```

输出：

| setting | total | mapped_page_id | mapped_image_path | gold_page_hits | used_run_file |
|---|---:|---:|---:|---:|---|
| Gold Evidence | 10 | 10 | 10 | 10 | |
| BM25 | 10 | 0 | 0 | 0 | results\week7\hybrid_fusion\hybrid_fullmv_N50_alpha1p0_run.tsv |
| Full MV | 10 | 0 | 0 | 0 | results\week7\c2f_fixed_N\bm25_fullmv_N10_run.tsv |
| Hybrid Fusion | 10 | 0 | 0 | 0 | results\week7\hybrid_fusion\hybrid_budgetmv_N50_M24_alpha1p0_run.tsv |
| Budgeted MV | 10 | 0 | 0 | 0 | results\week7\c2f_fixed_N\bm25_budgetmv_N20_M8_none_run.tsv |
| Gold Masked | 10 | 10 | 10 | 10 | |
| Random Masked | 10 | 10 | 10 | 10 | |

---

### 6.2 最终验证命令

执行命令：

```bash
python -c "import csv; rows=list(csv.DictReader(open('results/week8/visual_rag/qa_inputs.csv',encoding='utf-8-sig'))); print('rows=',len(rows)); print('missing_page=',sum(1 for r in rows if not r['page_id'])); print('missing_image=',sum(1 for r in rows if not r['image_path'])); print('retrieval_missing_page=',sum(1 for r in rows if r['setting'] in ['BM25','Full MV','Hybrid Fusion','Budgeted MV'] and not r['page_id'])); print('retrieval_missing_image=',sum(1 for r in rows if r['setting'] in ['BM25','Full MV','Hybrid Fusion','Budgeted MV'] and not r['image_path']))"
```

输出：

```text
rows= 70
missing_page= 40
missing_image= 40
retrieval_missing_page= 40
retrieval_missing_image= 40
```

---

## 7. 当前问题定位

### 7.1 问题现象

虽然脚本已经成功运行，但以下 4 类 retrieval setting 仍未映射成功：

```text
BM25
Full MV
Hybrid Fusion
Budgeted MV
```

共计：

```text
4 settings × 10 queries = 40 rows
```

表现为：

```text
page_id 为空
image_path 为空
rank 为空
score 为空
```

---

### 7.2 根本原因

根据 run 文件诊断结果，当前 run 文件格式是：

```text
run_name query_id page_id rank score
```

但当前解析逻辑仍然主要按以下格式理解：

```text
query_id page_id rank score
```

或：

```text
query_id Q0 page_id rank score run_name
```

因此实际解析时把字段错位了：

```text
qid 被解析成 run_name
page_id 被解析成 query_id
rank 被解析成 page_id
score 被解析成 rank
```

结果导致 `run_maps` 中的 key 不是：

```text
q001, q002, q004, ...
```

而是：

```text
hybrid_fullmv_N50_alpha1p0
bm25_fullmv_N10
...
```

所以后续按 query_id 查询时：

```python
run_maps[setting].get(qid, {})
```

无法匹配任何结果。

---

## 8. 当前可用结果

虽然 retrieval mapping 仍未完成，但当前已有 30 条 QA 输入完全可用：

```text
Gold Evidence: 10
Gold Masked: 10
Random Masked: 10
```

这三类输入已经足够先跑一个最小 occlusion downstream QA 闭环：

```text
Original / Gold Masked / Random Masked
```

可用于验证：

```text
Evidence Occlusion 是否影响下游回答质量
```

---

## 9. 当前不可用结果

以下 40 条 retrieval-based QA 输入暂不可用：

```text
BM25: 10
Full MV: 10
Hybrid Fusion: 10
Budgeted MV: 10
```

原因：

```text
run 文件解析字段顺序未正确适配 run_name query_id page_id rank score 格式。
```

---

## 10. 已替换主 QA 输入文件

虽然 retrieval 部分仍为空，本轮仍执行了主输入文件替换：

```bash
copy /Y results\week8\visual_rag\qa_inputs_fixed.csv results\week8\visual_rag\qa_inputs.csv
copy /Y results\week8\visual_rag\qa_inputs_fixed.jsonl results\week8\visual_rag\qa_inputs.jsonl
copy /Y results\week8\visual_rag\qa_inputs_fixed_preview.md results\week8\visual_rag\qa_inputs_preview.md
```

输出：

```text
已复制 1 个文件。
已复制 1 个文件。
已复制 1 个文件。
```

当前主文件仍需下一步修复后再次覆盖。

---

## 11. 下一步修复计划

下一步需要修改：

```text
scripts/evaluation/build_week8_visual_rag_inputs_fixed.py
```

重点修改函数：

```python
parse_run_line()
```

使其明确支持当前五列格式：

```text
run_name query_id page_id rank score
```

正确解析为：

```python
qid = parts[1]
page_id = parts[2]
rank = parts[3]
score = parts[4]
```

修复目标：

```text
retrieval_missing_page = 0
retrieval_missing_image = 0
```

预期修复后应得到：

```text
rows = 70
missing_page = 0
missing_image = 0
retrieval_missing_page = 0
retrieval_missing_image = 0
```

前提是所有 retrieval page_id 对应的图片文件均存在于：

```text
data/images/{doc_id}/{page_id}.png
```

或可通过 `rglob` 找到。

---

## 12. 当前状态总结

本轮完成了：

```text
1. Week 7 run 文件存在性检查；
2. Hybrid Fusion 与 C2F 结果文件定位；
3. Run 文件格式诊断；
4. TypeError rank 类型错误修复；
5. Fixed QA input 文件重新生成；
6. QA input mapping summary 输出；
7. 确认 Gold / Masked 条件已完整可用。
```

当前未完成：

```text
Retrieval-based input mapping 尚未完成。
```

当前状态：

```text
Gold / Masked QA Inputs: READY
Retrieval QA Inputs: NEED_PARSE_FIX
Week 8 Downstream Input Conditions: PARTIALLY_READY
```

---

## 13. 今日阶段性结论

Week 8 的下游输入条件已经完成基础落盘，并确认 Week 7 的 occlusion 数据能够直接接入下游 QA。  
不过，retrieval-based settings 的输入仍需修复 run 文件解析逻辑。当前 run 文件真实格式为：

```text
run_name query_id page_id rank score
```

下一步只需针对该五列格式修改解析函数，即可补齐 BM25 / Full MV / Hybrid Fusion / Budgeted MV 的检索页面、rank、score 和 image path。

```text
Next Action:
Fix parse_run_line() for five-column run format.
```
