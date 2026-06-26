# Week 8 Note Report：Lightweight Visual RAG 下游验证与论文写作材料整理

**日期**：2026-05-04 至 2026-05-10  
**实际主要实验日期**：2026-05-08  
**项目**：PCB_VisualRAG_Project  
**环境**：`pcb_visualrag`  
**工作目录**：`E:\Working\PCB_VisualRAG_Project`  
**阶段主题**：Lightweight Visual RAG Downstream Validation and Paper Material Organization  
**当前状态**：Week 8 Visual RAG Experiment Completed / Ready for Paper Writing  

---

## 1. 本周定位

第 8 周是项目从“检索算法与实验扩展”转向“下游验证与论文成文”的关键阶段。

前 7 周已经完成了 OCR/Text baseline、Single-vector Visual、Full Multi-vector、Budgeted Multi-vector、Token Budget、Quantization、BM25-C2F、Hybrid Fusion、Evidence Attribution 与 Occlusion 等核心实验。

因此 Week 8 的重点不是继续无限增加实验，而是完成一个轻量但可信的下游 Visual RAG / QA 验证闭环，用于回答：

```text
1. 检索证据质量是否影响最终回答质量？
2. Budgeted Retrieval / Visual Retrieval 结果是否能够支撑下游 QA？
3. Evidence Occlusion 的影响是否会传导到下游回答？
4. 当前实验结论能否转化为论文中的应用验证部分？
```

本周最终完成了轻量 Visual RAG 下游实验闭环，并将结果表复制到论文写作目录。

---

## 2. 本周完成内容概览

### 2.1 已完成任务

| 模块 | 内容 | 状态 |
|---|---|---|
| Visual RAG protocol | 生成 Week 8 下游验证协议 | Completed |
| QA settings | 固定 Gold / Retrieval / Masked 输入条件 | Completed |
| QA metrics | 固定 correctness / support / unknown / error type | Completed |
| QA input construction | 构造 70 条 QA 输入 | Completed |
| Retrieval mapping fix | 修复 retrieval run 文件解析与 image path 映射 | Completed |
| Manual VLM pack | 生成手动 VLM 检查包 | Completed |
| Ollama VLM inference | 使用 `llama3.2-vision` 完成本地 VLM 推理 | Completed |
| Failed case rerun | 重跑 4 个 timeout 样本 | Completed |
| QA evaluation | 自动生成 rule-based QA evaluation | Completed |
| Result tables | 生成 Table 19–23 | Completed |
| Paper table export | 将最终结果复制到 `paper/tables/` | Completed |
| Experiment summary | 生成 Week 8 实验摘要 | Completed |

---

## 3. 下游 Visual RAG 验证设计

### 3.1 实验闭环

Week 8 采用如下轻量 Visual RAG / QA 闭环：

```text
Query
↓
Retrieval / Gold / Masked Input Page
↓
Local VLM Inference
↓
VLM Answer
↓
Rule-based QA Evaluation
↓
Result Tables
```

本实验不重新训练模型，而是使用本地现成 VLM 进行 inference，从而验证检索结果是否能支撑下游问答。

---

### 3.2 QA 输入设置

每个 query 构造 7 种输入条件：

| Setting | 说明 | 目的 |
|---|---|---|
| Gold Evidence | 使用人工标注 gold evidence page | 回答上限参考 |
| BM25 | 使用 BM25 / text-based retrieval top page | 文本检索基线 |
| Full MV | 使用 Full Multi-vector retrieval top page | 视觉多向量基线 |
| Hybrid Fusion | 使用 BM25 + Visual fusion top page | 文本-视觉融合验证 |
| Budgeted MV | 使用 Budgeted Multi-vector retrieval top page | 预算化检索下游验证 |
| Gold Masked | 遮挡 gold evidence region 的页面 | evidence occlusion 测试 |
| Random Masked | 遮挡随机区域的页面 | occlusion control |

最终规模：

```text
10 queries × 7 settings = 70 QA cases
```

---

## 4. QA 输入构造与 Retrieval Mapping

### 4.1 初始问题

Day 1 构造 QA 输入时，Gold Evidence / Gold Masked / Random Masked 三类输入已成功映射，但 retrieval-based settings 出现缺失：

```text
BM25
Full MV
Hybrid Fusion
Budgeted MV
```

初始问题表现为：

```text
retrieval_missing_page = 40
retrieval_missing_image = 40
```

原因是 Week 7 run 文件格式为五列：

```text
run_name query_id page_id rank score
```

而旧解析逻辑按其他格式理解，导致 query_id 与 page_id 字段错位。

---

### 4.2 修复结果

修复 `build_week8_visual_rag_inputs_fixed.py` 后，重新生成 QA 输入。

最终映射结果：

| setting | total | mapped_page_id | mapped_image_path | gold_page_hits |
|---|---:|---:|---:|---:|
| Gold Evidence | 10 | 10 | 10 | 10 |
| BM25 | 10 | 10 | 10 | 4 |
| Full MV | 10 | 10 | 10 | 1 |
| Hybrid Fusion | 10 | 10 | 10 | 4 |
| Budgeted MV | 10 | 10 | 10 | 1 |
| Gold Masked | 10 | 10 | 10 | 10 |
| Random Masked | 10 | 10 | 10 | 10 |

完整性检查：

```text
rows = 70
missing_page = 0
missing_image = 0
retrieval_missing_page = 0
retrieval_missing_image = 0
```

结论：

```text
全部 70 条 QA 输入均已成功映射到 page_id 与 image_path。
```

---

## 5. 本地 VLM 推理设置

### 5.1 使用模型

本周使用 Ollama 本地视觉模型：

```text
llama3.2-vision
```

模型下载：

```bash
ollama pull llama3.2-vision
```

Ollama 服务状态：

```text
Ollama service already running at localhost:11434
```

---

### 5.2 Prompt Template

统一 QA prompt：

```text
You are answering a question about a PCB engineering document page.

Use only the provided page image as evidence.
If the page does not contain enough information, answer exactly:
Not enough evidence.

Question:
{query}

Return your answer in this exact format:
Short answer: <one concise answer>
Evidence description: <what visible evidence supports the answer>
Confidence: high / medium / low
```

---

### 5.3 推理过程

先执行 3 条样本测试，修复 CSV 输出字段缺失问题：

```text
ValueError: dict contains fields not in fieldnames: 'prompt'
```

修复后，完整运行 70 条 QA case。

完整推理过程中出现 4 个 timeout case：

```text
q002__BM25
q002__Hybrid_Fusion
q007__Budgeted_MV
q012__Full_MV
```

随后使用 `rerun_week8_ollama_failed_cases.py` 单独重跑失败样本。

最终检查：

```text
remaining bad cases = 0
blank_answer = 0
```

结论：

```text
70 条 QA 输出全部有效。
```

---

## 6. QA Evaluation 方法

### 6.1 评估方式

本周采用 rule-based weak evaluator，而不是人工精标。

核心规则：

```text
1. is_gold_page = 1 且模型给出非 unknown 答案：
   answer_correctness = 1

2. is_gold_page = 0 且模型回答 Not enough evidence：
   evidence_supported = 1
   answer_correctness = 0

3. is_gold_page = 0 但模型给出具体答案：
   evidence_supported = 0
   error_type = hallucination

4. 空回答或 timeout：
   error_type = no_answer

5. Gold Masked 上若模型回答 Not enough evidence：
   error_type = masked_evidence
```

### 6.2 注意事项

该评估方式适合做 first-pass automatic validation，但不应表述为人工精细语义评测。

论文中应使用：

```text
rule-based weak evaluator
```

而不是：

```text
fully reliable automatic semantic evaluation
```

---

## 7. 最终主结果：Lightweight Visual RAG

### 7.1 Table 19 主结果

| setting | num_cases | gold_page_rate | answer_accuracy | evidence_supported_rate | unknown_rate | concrete_answer_rate | no_answer_count | wrong_page_count | hallucination_count |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Gold Evidence | 10 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 1.0000 | 0 | 0 | 0 |
| BM25 | 10 | 0.4000 | 0.4000 | 0.9000 | 0.5000 | 0.5000 | 0 | 5 | 1 |
| Full MV | 10 | 0.1000 | 0.1000 | 0.6000 | 0.5000 | 0.5000 | 0 | 5 | 4 |
| Hybrid Fusion | 10 | 0.4000 | 0.4000 | 0.9000 | 0.5000 | 0.5000 | 0 | 5 | 1 |
| Budgeted MV | 10 | 0.1000 | 0.1000 | 0.4000 | 0.3000 | 0.7000 | 0 | 3 | 6 |
| Gold Masked | 10 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 1.0000 | 0 | 0 | 0 |
| Random Masked | 10 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 1.0000 | 0 | 0 | 0 |

---

### 7.2 Table 23：Retrieval Quality vs QA Quality

| setting | num_cases | gold_page_hits | retrieval_gold_hit_rate | answer_accuracy | evidence_supported_rate | unknown_rate | hallucination_count |
|---|---:|---:|---:|---:|---:|---:|---:|
| Gold Evidence | 10 | 10 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 0 |
| BM25 | 10 | 4 | 0.4000 | 0.4000 | 0.9000 | 0.5000 | 1 |
| Full MV | 10 | 1 | 0.1000 | 0.1000 | 0.6000 | 0.5000 | 4 |
| Hybrid Fusion | 10 | 4 | 0.4000 | 0.4000 | 0.9000 | 0.5000 | 1 |
| Budgeted MV | 10 | 1 | 0.1000 | 0.1000 | 0.4000 | 0.3000 | 6 |
| Gold Masked | 10 | 10 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 0 |
| Random Masked | 10 | 10 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 0 |

---

## 8. 主要观察

### 8.1 Retrieval quality 与 QA quality 高度一致

当前 top-1 page 输入设置下，retrieval gold hit rate 与 answer accuracy 完全对齐：

```text
BM25: 0.4000 retrieval hit → 0.4000 QA accuracy
Full MV: 0.1000 retrieval hit → 0.1000 QA accuracy
Hybrid Fusion: 0.4000 retrieval hit → 0.4000 QA accuracy
Budgeted MV: 0.1000 retrieval hit → 0.1000 QA accuracy
```

这说明：

```text
下游 QA correctness 高度依赖检索页面是否命中 gold evidence page。
```

---

### 8.2 BM25 与 Hybrid Fusion 在当前下游子集表现一致

当前 10-query 子集上：

```text
BM25 answer_accuracy = 0.4000
Hybrid Fusion answer_accuracy = 0.4000
```

说明 Hybrid Fusion 在当前下游 top-1 setting 中达到与 BM25 相同的 QA accuracy。

---

### 8.3 Full MV 与 Budgeted MV 当前 top-1 QA 表现较弱

当前结果：

```text
Full MV answer_accuracy = 0.1000
Budgeted MV answer_accuracy = 0.1000
```

该结果说明当前所选 run 配置在 Week 8 的 10-query 下游子集上 top-1 命中率较低。

需要注意：

```text
这不代表 Full MV 或 Budgeted MV 在完整 ranking metrics 上无效；
它只反映当前 top-1 page QA setup 下的结果。
```

---

### 8.4 Budgeted MV 出现较多 hallucination

Budgeted MV：

```text
hallucination_count = 6
unknown_rate = 0.3000
concrete_answer_rate = 0.7000
```

说明错误检索页面可能诱导 VLM 给出 unsupported concrete answer。

该观察可用于 Discussion：

```text
Incorrectly retrieved pages may not only reduce answer correctness but also increase the risk of unsupported concrete answers.
```

---

### 8.5 Occlusion downstream 未造成 accuracy 下降

Gold Evidence / Gold Masked / Random Masked：

```text
answer_accuracy = 1.0000
```

说明当前 page-level QA 设置下，gold region masking 未显著降低下游 QA accuracy。

可能原因：

```text
1. 问题偏向 page identification，而不是细粒度内容抽取；
2. VLM 可利用页码、标题、版式等全局线索回答；
3. gold mask 未完全覆盖所有可回答线索；
4. rule-based evaluator 对 gold page 上的非 unknown 答案较宽松。
```

因此论文中应谨慎表述：

```text
The downstream occlusion result is negative or inconclusive under the current page-level QA setup.
```

---

## 9. 本周支持的论文主张

### 9.1 可以支持的主张

| Claim | Evidence |
|---|---|
| Retrieval quality affects downstream QA quality | retrieval_gold_hit_rate 与 answer_accuracy 完全对齐 |
| Gold evidence input provides an upper-bound condition | Gold Evidence accuracy = 1.0000 |
| Hybrid Fusion remains competitive with BM25 on the QA subset | BM25 与 Hybrid Fusion answer_accuracy 均为 0.4000 |
| Wrong retrieved pages can induce unsupported answers | Budgeted MV hallucination_count = 6 |
| Lightweight Visual RAG validation pipeline is feasible | 70 QA cases completed with local VLM |

---

### 9.2 不应过度声称的主张

以下表述需要避免：

```text
1. 不应声称 Budgeted MV 在 Week 8 QA 中优于 BM25。
2. 不应声称 occlusion 明显破坏了下游 QA。
3. 不应声称当前 QA evaluation 是人工精标。
4. 不应声称本项目训练了新的 end-to-end VLM。
5. 不应声称 visual retrieval universally outperforms BM25。
```

---

## 10. 与整体论文主线的关系

Week 8 不是主性能提升实验，而是下游应用验证实验。

论文中应这样定位：

```text
前 7 周实验支撑算法和检索性能主张；
Week 8 实验支撑检索质量会影响下游 Visual QA 的应用层主张。
```

因此：

```text
Budgeted Retrieval 的性能提升主要应来自 efficiency-effectiveness trade-off；
Week 8 Visual RAG 主要用于说明 retrieval quality 对 answer quality 的传导关系。
```

可以使用如下论文逻辑：

```text
1. Budgeted Retrieval reduces retrieval cost while preserving useful retrieval performance.
2. Evidence-aware retrieval is important because downstream QA quality depends strongly on whether the retrieved page contains the gold evidence.
3. A lightweight Visual RAG validation confirms this dependency under a local VLM setting.
```

---

## 11. 本周产出文件

### 11.1 Week 8 实验文件

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
results/week8/visual_rag/week8_visual_rag_experiment_summary.md
```

---

### 11.2 Week 8 结果表

```text
results/week8/visual_rag/tables/table19_visual_rag_main_results.csv
results/week8/visual_rag/tables/table20_occlusion_downstream_results.csv
results/week8/visual_rag/tables/table21_retrieval_vs_qa_results.csv
results/week8/visual_rag/tables/table22_qa_error_breakdown.csv
results/week8/visual_rag/tables/table23_retrieval_quality_vs_qa_quality.csv
```

---

### 11.3 论文目录副本

```text
paper/tables/table4_visual_rag_main_results.csv
paper/tables/table5_occlusion_downstream_results.csv
paper/tables/table6_retrieval_vs_qa_results.csv
paper/tables/table7_qa_error_breakdown.csv
paper/tables/table8_retrieval_quality_vs_qa_quality.csv
```

---

### 11.4 写作材料

```text
paper/notes/claims_and_evidence.md
paper/notes/sections_outline.md
paper/notes/figures_manifest.md
paper/notes/week8_note_report.md
```

---

## 12. 当前完成度判断

Week 8 已完成：

```text
Visual RAG protocol: DONE
QA input construction: DONE
Retrieval mapping: DONE
VLM inference: DONE
Failed case rerun: DONE
QA evaluation: DONE
Result table generation: DONE
Paper table export: DONE
Experiment summary: DONE
```

最终验收状态：

```text
STATUS: WEEK8_VISUAL_RAG_EXPERIMENT_COMPLETE
```

---

## 13. 后续写作建议

下一步应重点推进论文写作，而不是继续大规模扩展实验。

优先级：

```text
1. 写 Experimental Setup 中的 Week 8 Downstream QA 设置；
2. 写 Main Results 中的 retrieval quality vs QA quality 分析；
3. 写 Discussion 中的 occlusion negative finding；
4. 写 Limitations 中的 weak evaluator、top-1 input、local VLM limitation；
5. 整理主实验中 Budgeted Retrieval 的 efficiency-effectiveness trade-off 表。
```

推荐论文表述：

```text
We conduct a lightweight downstream Visual QA validation using a local VLM and a rule-based weak evaluator. The results show that downstream answer correctness is strongly tied to whether the retrieved page matches the gold evidence page. However, the occlusion-based downstream setting does not reduce QA accuracy under the current page-level question design, suggesting that the current QA setup can often be solved using page-level cues.
```

---

## 14. Week 8 Note 总结

Week 8 完成了轻量 Visual RAG 下游验证闭环。实验显示，在当前 top-1 page QA 设置下，retrieval gold hit rate 与 answer accuracy 完全一致，说明检索证据质量直接影响下游问答正确性。

同时，当前 occlusion downstream 设置未观察到 QA accuracy 下降，因此 occlusion 下游结果应被解释为 negative / inconclusive finding，而不是强证据遮挡效应。

总体而言，Week 8 结果可以作为论文中 “Lightweight Visual RAG Downstream Validation” 的补充实验，用于连接前期检索实验与实际问答应用。
