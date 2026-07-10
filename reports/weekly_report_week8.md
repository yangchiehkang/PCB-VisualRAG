# Week 8 周报：轻量 Visual RAG 下游验证与论文写作启动

**周期**：2026-05-04 至 2026-05-10  
**项目**：PCB_VisualRAG_Project  
**汇报阶段**：Week 8  
**主题**：Lightweight Visual RAG Downstream Validation and Paper Writing Preparation  
**当前状态**：实验闭环完成，结果表已固化，可进入论文写作  

---

## 1. 本周工作概述

本周的主要目标是将前 7 周完成的 PCB 文档检索实验进一步连接到下游 Visual RAG / QA 任务，并开始整理论文写作材料。

此前项目已经完成 OCR/Text baseline、Single-vector Visual、Full Multi-vector、Budgeted Multi-vector、Token Budget、Quantization、BM25-C2F、Hybrid Fusion 以及 Evidence Attribution / Occlusion 等实验。

本周重点完成一个轻量但完整的下游验证闭环：

```text
Query
↓
Retrieved / Gold / Masked Page
↓
Local VLM Answer
↓
Rule-based QA Evaluation
↓
Result Tables
```

最终，本周成功完成 70 条 QA case 的本地 VLM 推理、失败样本重跑、自动评估和结果汇总，并将最终表格复制到论文目录。

---

## 2. 本周目标完成情况

| 目标 | 完成情况 | 说明 |
|---|---|---|
| 构建轻量 Visual RAG 验证协议 | 已完成 | 已生成 `visual_rag_protocol.md` |
| 固定 QA 输入条件 | 已完成 | 7 个 setting，70 条 case |
| 修复 retrieval 输入映射 | 已完成 | retrieval_missing_page = 0 |
| 接入本地 VLM | 已完成 | 使用 Ollama `llama3.2-vision` |
| 完成 QA 推理 | 已完成 | 70 条均有有效 answer |
| 完成 QA evaluation | 已完成 | rule-based weak evaluator |
| 生成结果表 | 已完成 | Table 19–23 |
| 复制结果到论文目录 | 已完成 | 已复制到 `paper/tables/` |
| 论文写作材料初始化 | 已完成 | claims、outline、figures manifest 已生成 |
| 正文章节初稿 | 部分完成 / 待继续 | 已完成结构与材料整理，正文需继续写 |

---

## 3. 本周实验设计

### 3.1 下游 QA 输入条件

本周为每个 evidence query 构造 7 种输入条件：

| Setting | 类型 | 目的 |
|---|---|---|
| Gold Evidence | Oracle input | 回答上限参考 |
| BM25 | Retrieval input | 文本检索基线 |
| Full MV | Retrieval input | Full multi-vector 视觉检索对照 |
| Hybrid Fusion | Retrieval input | 文本-视觉融合检索验证 |
| Budgeted MV | Retrieval input | 预算化多向量检索下游验证 |
| Gold Masked | Occlusion input | 遮挡 gold evidence region |
| Random Masked | Occlusion control | 遮挡随机区域 |

实验规模：

```text
10 queries × 7 settings = 70 QA cases
```

---

### 3.2 使用模型

本周使用本地 Ollama VLM：

```text
llama3.2-vision
```

选择本地 VLM 的原因：

```text
1. 不依赖外部 API；
2. 可复现性较好；
3. 足够完成 lightweight downstream validation；
4. 符合本周不重新训练模型、只做下游验证的目标。
```

---

### 3.3 评估指标

本周采用以下 QA 指标：

| Metric | 含义 |
|---|---|
| answer_accuracy | 回答是否正确 |
| evidence_supported_rate | 回答是否由可见页面证据支持 |
| unknown_rate | 模型是否回答 Not enough evidence |
| concrete_answer_rate | 模型是否给出具体答案 |
| wrong_page_count | 输入为错误页面造成的错误 |
| hallucination_count | 错误页面上给出 unsupported concrete answer |
| no_answer_count | timeout 或空回答 |
| masked_evidence_count | 遮挡导致无法回答的情况 |

评估方式为：

```text
rule-based weak evaluator
```

因此结果主要用于 first-pass validation，而不是人工精标结论。

---

## 4. 本周关键工程修复

### 4.1 Retrieval run 解析修复

初始 QA 输入中，retrieval-based settings 的 page_id 和 image_path 为空。

问题原因：

```text
Week 7 run 文件格式为：
run_name query_id page_id rank score

旧解析逻辑没有正确适配该五列格式。
```

修复后：

```text
rows = 70
missing_page = 0
missing_image = 0
retrieval_missing_page = 0
retrieval_missing_image = 0
```

该修复使 BM25、Full MV、Hybrid Fusion、Budgeted MV 四类 retrieval input 全部可用于下游 QA。

---

### 4.2 Ollama 输出字段修复

初始 3 条测试时出现：

```text
ValueError: dict contains fields not in fieldnames: 'prompt'
```

原因是输出字典中包含 `prompt` 字段，但 CSV fieldnames 未包含该字段。

修复后，Ollama QA 脚本可以正常输出：

```text
qa_outputs_ollama.jsonl
qa_outputs_ollama.csv
qa_outputs_manual_filled.csv
```

---

### 4.3 Timeout 样本重跑

完整 70 条推理中出现 4 个 timeout 样本：

```text
q002__BM25
q002__Hybrid_Fusion
q007__Budgeted_MV
q012__Full_MV
```

通过重跑脚本完成补齐：

```text
Rerun cases = 4
Merged outputs = 70
remaining bad cases = 0
blank_answer = 0
```

最终所有 70 条 QA case 均有有效回答。

---

## 5. 本周主要结果

### 5.1 QA 输入映射结果

| setting | total | mapped_page_id | mapped_image_path | gold_page_hits |
|---|---:|---:|---:|---:|
| Gold Evidence | 10 | 10 | 10 | 10 |
| BM25 | 10 | 10 | 10 | 4 |
| Full MV | 10 | 10 | 10 | 1 |
| Hybrid Fusion | 10 | 10 | 10 | 4 |
| Budgeted MV | 10 | 10 | 10 | 1 |
| Gold Masked | 10 | 10 | 10 | 10 |
| Random Masked | 10 | 10 | 10 | 10 |

---

### 5.2 Lightweight Visual RAG 主结果

| setting | num_cases | gold_page_rate | answer_accuracy | evidence_supported_rate | unknown_rate | hallucination_count |
|---|---:|---:|---:|---:|---:|---:|
| Gold Evidence | 10 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 0 |
| BM25 | 10 | 0.4000 | 0.4000 | 0.9000 | 0.5000 | 1 |
| Full MV | 10 | 0.1000 | 0.1000 | 0.6000 | 0.5000 | 4 |
| Hybrid Fusion | 10 | 0.4000 | 0.4000 | 0.9000 | 0.5000 | 1 |
| Budgeted MV | 10 | 0.1000 | 0.1000 | 0.4000 | 0.3000 | 6 |
| Gold Masked | 10 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 0 |
| Random Masked | 10 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 0 |

---

### 5.3 Retrieval Quality vs QA Quality

| setting | gold_page_hits | retrieval_gold_hit_rate | answer_accuracy |
|---|---:|---:|---:|
| Gold Evidence | 10 | 1.0000 | 1.0000 |
| BM25 | 4 | 0.4000 | 0.4000 |
| Full MV | 1 | 0.1000 | 0.1000 |
| Hybrid Fusion | 4 | 0.4000 | 0.4000 |
| Budgeted MV | 1 | 0.1000 | 0.1000 |
| Gold Masked | 10 | 1.0000 | 1.0000 |
| Random Masked | 10 | 1.0000 | 1.0000 |

核心现象：

```text
retrieval_gold_hit_rate 与 answer_accuracy 在当前 top-1 page QA 设置下完全一致。
```

这说明：

```text
检索页面是否命中 gold evidence page 是下游 QA 正确性的关键因素。
```

---

## 6. 本周实验结论

### 6.1 检索质量会影响下游 QA 质量

本周最重要的实验结论是：

```text
下游 QA answer_accuracy 与 retrieval gold page hit rate 高度一致。
```

具体而言：

```text
BM25: 0.4000 retrieval hit → 0.4000 QA accuracy
Hybrid Fusion: 0.4000 retrieval hit → 0.4000 QA accuracy
Full MV: 0.1000 retrieval hit → 0.1000 QA accuracy
Budgeted MV: 0.1000 retrieval hit → 0.1000 QA accuracy
```

这说明检索质量确实会传导到下游问答质量。

---

### 6.2 Hybrid Fusion 在当前 QA 子集上与 BM25 表现一致

当前 10-query 下游子集上：

```text
BM25 answer_accuracy = 0.4000
Hybrid Fusion answer_accuracy = 0.4000
```

说明 Hybrid Fusion 在当前 top-1 QA 设置下能够达到 BM25 水平。

---

### 6.3 当前 Budgeted MV QA 表现不应被过度包装

当前结果中：

```text
Budgeted MV answer_accuracy = 0.1000
```

因此 Week 8 下游 QA 不适合作为“Budgeted MV 在 QA 上优于 BM25”的证据。

更稳妥的论文表述是：

```text
Budgeted Retrieval 的主要贡献应来自前期检索实验中的效率-效果 trade-off；
Week 8 下游实验主要证明 retrieval quality 会影响 QA quality。
```

---

### 6.4 Occlusion downstream 结果为 negative / inconclusive

Gold Masked 与 Random Masked 均未造成 accuracy 下降：

```text
Gold Evidence accuracy = 1.0000
Gold Masked accuracy = 1.0000
Random Masked accuracy = 1.0000
```

因此当前实验不能强声称：

```text
Evidence occlusion significantly degrades downstream QA.
```

更准确的结论是：

```text
在当前 page-level QA 设置与 rule-based weak evaluation 下，Gold Masked 没有降低 QA accuracy。
```

可能原因包括：

```text
1. query 偏向页面识别；
2. VLM 可以使用页码、标题或全局布局线索；
3. 遮挡区域未完全覆盖所有可回答线索；
4. 自动评估规则较宽松。
```

---

## 7. 本周完成的文件与结果表

### 7.1 实验文件

```text
results/week8/visual_rag/visual_rag_protocol.md
results/week8/visual_rag/qa_settings.csv
results/week8/visual_rag/qa_metrics_definition.csv
results/week8/visual_rag/qa_inputs.csv
results/week8/visual_rag/qa_inputs.jsonl
results/week8/visual_rag/qa_input_mapping_summary.csv
results/week8/visual_rag/qa_outputs_ollama.csv
results/week8/visual_rag/qa_outputs_ollama_merged.csv
results/week8/visual_rag/qa_outputs_manual_filled.csv
results/week8/visual_rag/qa_evaluation.csv
results/week8/visual_rag/qa_evaluation_autofill_summary.csv
results/week8/visual_rag/week8_visual_rag_experiment_summary.md
```

---

### 7.2 结果表

```text
results/week8/visual_rag/tables/table19_visual_rag_main_results.csv
results/week8/visual_rag/tables/table20_occlusion_downstream_results.csv
results/week8/visual_rag/tables/table21_retrieval_vs_qa_results.csv
results/week8/visual_rag/tables/table22_qa_error_breakdown.csv
results/week8/visual_rag/tables/table23_retrieval_quality_vs_qa_quality.csv
```

---

### 7.3 论文表格副本

```text
paper/tables/table4_visual_rag_main_results.csv
paper/tables/table5_occlusion_downstream_results.csv
paper/tables/table6_retrieval_vs_qa_results.csv
paper/tables/table7_qa_error_breakdown.csv
paper/tables/table8_retrieval_quality_vs_qa_quality.csv
```

---

## 8. 本周论文写作材料进展

本周已初始化论文写作材料目录：

```text
paper/
paper/sections/
paper/figures/
paper/tables/
paper/notes/
```

已生成：

```text
paper/notes/claims_and_evidence.md
paper/notes/sections_outline.md
paper/notes/figures_manifest.md
```

当前论文结构已固定为：

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

本周写作材料已经进入可用状态，但 Introduction / Method / Problem Setup 等正式正文仍需继续补全。

---

## 9. 当前项目完成度判断

从老师提出的“完成模型算法以及实验验证，最好能有算法性能提升”的要求来看，当前项目已经基本达到要求。

### 9.1 已完成模型 / 算法部分

当前算法主线包括：

```text
1. Full Multi-vector Retrieval
2. Budgeted Multi-vector Retrieval
3. BM25-guided Coarse-to-Fine Retrieval
4. Token / Patch Budgeting
5. Quantized Retrieval
6. Hybrid Fusion
7. Evidence Attribution
8. Counterfactual Occlusion
9. Lightweight Visual RAG Downstream Validation
```

其中 Budgeted Retrieval 可形式化为预算三元组：

$$Budget = (N, M, bits)$$

其中：

```text
N    = candidate page budget
M    = per-page visual token budget
bits = compression / quantization budget
```

---

### 9.2 已完成实验验证部分

当前实验覆盖：

```text
OCR/Text baseline
Single-vector Visual baseline
Full Multi-vector baseline
Budgeted Multi-vector Retrieval
Token Budget analysis
Quantization analysis
BM25-C2F reranking
Hybrid Fusion
Evidence Attribution
Occlusion
Lightweight Visual RAG QA
```

因此实验验证链路已经比较完整。

---

### 9.3 性能提升应如何表述

本项目的性能提升不应只理解为“QA accuracy 全面更高”。

更准确的性能提升是：

```text
Budgeted Retrieval improves the efficiency-effectiveness trade-off.
```

也就是：

```text
在控制候选数、视觉 token 数和压缩预算的情况下，尽量保持检索效果，同时降低计算和存储成本。
```

Week 8 的下游实验则补充说明：

```text
检索质量会影响下游 QA 质量，因此提高检索质量和证据命中率具有实际应用意义。
```

---

## 10. 本周存在的局限

本周实验仍有以下局限：

```text
1. VLM 使用本地 llama3.2-vision，模型能力有限；
2. QA evaluation 是 rule-based weak evaluator，不是人工精标；
3. 当前 QA 问题偏向 page identification，而不是细粒度内容问答；
4. 只测试 top-1 page input，没有测试 top-k multi-page RAG；
5. Gold Masked 没有降低 QA accuracy，因此 occlusion downstream 结果不能作为强正向证据；
6. Full MV / Budgeted MV 当前 QA 子集表现较弱，需在论文中谨慎解释。
```

---

## 11. 下周计划

下周重点应从继续扩展实验转向论文写作和结果整合。

建议任务：

```text
1. 完成 Introduction 初稿；
2. 完成 Problem Setup 初稿；
3. 完成 Method 初稿；
4. 写 Experimental Setup 中的 dataset、retrieval settings、budget settings；
5. 写 Main Results 中的 baseline、budgeted retrieval、hybrid fusion 分析；
6. 写 Evidence Attribution 与 Occlusion 章节；
7. 写 Lightweight Visual RAG Downstream Validation 小节；
8. 整理所有表格编号与图表引用；
9. 准备一张总表说明效率-效果 trade-off；
10. 人工抽查 qa_evaluation.csv 中部分样本，增强可信度。
```

---

## 12. 可直接用于论文的 Week 8 表述

建议在论文中这样写 Week 8 下游验证：

```text
We further conduct a lightweight downstream Visual QA validation using a local VLM and a rule-based weak evaluator. The experiment includes 70 QA cases across gold evidence, retrieval-based, and occlusion-based input conditions. After rerunning timeout cases, all outputs are complete and evaluable.

The results show that downstream answer accuracy is tightly coupled with whether the retrieved page matches the gold evidence page. In the current top-1 page setting, retrieval gold hit rate and answer accuracy are aligned across retrieval conditions, suggesting that evidence-bearing page retrieval is critical for downstream Visual QA.

However, the occlusion-based downstream setting does not reduce QA accuracy under the current page-level question design. This indicates that the current questions can often be answered using page-level cues such as page number, title, or global layout, and the occlusion result should therefore be interpreted cautiously.
```

---

## 13. 本周总结

本周完成了轻量 Visual RAG 下游验证实验，从 QA 输入构造、retrieval mapping 修复、本地 VLM 推理、失败样本重跑、自动评估到结果表生成，形成了完整闭环。

最终实验状态：

```text
QA Input Mapping: COMPLETE
Ollama VLM Inference: COMPLETE
Failed Case Rerun: COMPLETE
QA Evaluation: COMPLETE
Result Tables: COMPLETE
Paper Table Export: COMPLETE
Experiment Summary: COMPLETE
Completion Check: PASSED
```

最终验收输出：

```text
STATUS: WEEK8_VISUAL_RAG_EXPERIMENT_COMPLETE
```

本周最重要的结论是：

```text
检索证据质量会直接影响下游 QA answer accuracy。
```

同时需要谨慎说明：

```text
当前 Week 8 QA 结果不能证明 Budgeted MV 在下游 QA 中优于 BM25；
Budgeted Retrieval 的主要性能贡献应来自前期检索实验中的 efficiency-effectiveness trade-off。
```

至此，项目已经完成从检索算法设计、系统性实验验证到轻量下游应用验证的完整链路，可以进入论文正文集中写作阶段。
