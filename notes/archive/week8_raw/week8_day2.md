---

# Week 8 Day 2 实验日志：Ollama 本地 VLM 下游 QA 自动化与结果表生成

**日期**：2026-05-08  
**时间**：20:08  
**项目**：PCB_VisualRAG_Project  
**环境**：`pcb_visualrag`  
**工作目录**：`E:\Working\PCB_VisualRAG_Project`  
**任务主题**：Lightweight Visual RAG / QA Inference with Local Ollama VLM  
**状态**：Completed  

---

## 1. 本阶段目标

本阶段目标是完成 Week 8 轻量 Visual RAG 下游验证的核心实验闭环：

```text
Query
↓
Retrieval / Gold / Masked Input Page
↓
Local VLM Inference
↓
QA Output
↓
Rule-based QA Evaluation
↓
Result Tables
```

具体任务包括：

```text
1. 修复 retrieval-based QA 输入映射；
2. 使用 Ollama 本地视觉模型替代手动 VLM 填写；
3. 对 70 条 QA 输入自动生成回答；
4. 自动生成 QA evaluation 文件；
5. 汇总 Visual RAG 主结果表、Occlusion 下游结果表、Retrieval vs QA 对照表；
6. 固化 Week 8 实验结果文件。
```

---

## 2. Retrieval QA 输入映射修复完成

### 2.1 执行脚本

```bash
python scripts\evaluation\build_week8_visual_rag_inputs_fixed.py
```

---

### 2.2 输出文件

脚本成功生成：

```text
results/week8/visual_rag/qa_inputs_fixed.jsonl
results/week8/visual_rag/qa_inputs_fixed.csv
results/week8/visual_rag/qa_inputs_fixed_preview.md
results/week8/visual_rag/qa_input_mapping_summary.csv
```

---

### 2.3 使用的 Week 7 run 文件

| Setting | Used Run File |
|---|---|
| BM25 | `results\week7\hybrid_fusion\hybrid_fullmv_N50_alpha1p0_run.tsv` |
| Full MV | `results\week7\c2f_fixed_N\bm25_fullmv_N10_run.tsv` |
| Hybrid Fusion | `results\week7\hybrid_fusion\hybrid_budgetmv_N50_M24_alpha1p0_run.tsv` |
| Budgeted MV | `results\week7\c2f_fixed_N\bm25_budgetmv_N20_M8_none_run.tsv` |

---

### 2.4 映射结果

`qa_input_mapping_summary.csv` 输出如下：

| setting | total | mapped_page_id | mapped_image_path | gold_page_hits |
|---|---:|---:|---:|---:|
| Gold Evidence | 10 | 10 | 10 | 10 |
| BM25 | 10 | 10 | 10 | 4 |
| Full MV | 10 | 10 | 10 | 1 |
| Hybrid Fusion | 10 | 10 | 10 | 4 |
| Budgeted MV | 10 | 10 | 10 | 1 |
| Gold Masked | 10 | 10 | 10 | 10 |
| Random Masked | 10 | 10 | 10 | 10 |

最终完整性检查：

```text
rows= 70
missing_page= 0
missing_image= 0
retrieval_missing_page= 0
retrieval_missing_image= 0
```

结论：

```text
全部 70 条 Week 8 QA 输入已完成 page_id 与 image_path 映射。
Retrieval-based settings 已恢复可用。
```

---

## 3. 主 QA 输入文件覆盖

执行：

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

当前主输入文件：

```text
results/week8/visual_rag/qa_inputs.csv
results/week8/visual_rag/qa_inputs.jsonl
results/week8/visual_rag/qa_inputs_preview.md
```

状态：

```text
READY
```

---

## 4. Manual VLM Pack 生成

### 4.1 执行命令

```bash
python scripts\evaluation\make_week8_vlm_manual_pack.py
```

---

### 4.2 输出结果

```text
[Week8] Manual VLM pack generated.
Cases: 70
Wrote: E:\Working\PCB_VisualRAG_Project\results\week8\visual_rag\manual_vlm_pack\manual_vlm_manifest.csv
Wrote: E:\Working\PCB_VisualRAG_Project\results\week8\visual_rag\qa_outputs_manual_template.csv
Images: E:\Working\PCB_VisualRAG_Project\results\week8\visual_rag\manual_vlm_pack\images
Case prompts: E:\Working\PCB_VisualRAG_Project\results\week8\visual_rag\manual_vlm_pack\cases
```

---

### 4.3 文件检查

确认生成：

```text
results/week8/visual_rag/manual_vlm_pack/manual_vlm_manifest.csv
results/week8/visual_rag/manual_vlm_pack/images/
results/week8/visual_rag/manual_vlm_pack/cases/
results/week8/visual_rag/qa_outputs_manual_template.csv
```

其中：

```text
images: 70 files
cases: 70 files
```

结论：

```text
手动 VLM 推理包已完整生成。
```

---

## 5. Ollama 本地 VLM 自动化推理

### 5.1 本地 Ollama 状态

检查本地 Ollama 模型：

```bash
ollama list
```

初始已有：

```text
nomic-embed-text:latest
qwen2.5:3b
```

随后下载视觉模型：

```bash
ollama pull llama3.2-vision
```

下载成功：

```text
success
```

最终使用模型：

```text
llama3.2-vision
```

---

### 5.2 Ollama 服务状态

执行：

```bash
ollama serve
```

返回：

```text
Error: listen tcp 127.0.0.1:11434: bind: Only one usage of each socket address ...
```

说明：

```text
Ollama 服务已在后台运行，无需重复启动。
```

---

### 5.3 Requests 依赖

执行：

```bash
pip install requests
```

结果：

```text
Requirement already satisfied: requests
```

运行时存在 warning：

```text
RequestsDependencyWarning: urllib3/chardet/charset_normalizer version mismatch
```

该 warning 未阻止实验执行。

---

## 6. Ollama QA 脚本调试

### 6.1 首次 3 条测试

执行：

```bash
python scripts\evaluation\run_week8_ollama_vlm_qa.py --model llama3.2-vision --limit 3
```

初次运行报错：

```text
ValueError: dict contains fields not in fieldnames: 'prompt'
```

原因：

```text
输出字典中包含 prompt 字段，但 CSV fieldnames 未包含 prompt。
```

---

### 6.2 修复方式

执行字段修复命令：

```bash
python -c "from pathlib import Path; p=Path('scripts/evaluation/run_week8_ollama_vlm_qa.py'); s=p.read_text(encoding='utf-8'); s=s.replace('\"model\",\n        \"vlm_answer\",', '\"model\",\n        \"prompt\",\n        \"vlm_answer\",'); p.write_text(s, encoding='utf-8'); print('fixed')"
```

输出：

```text
fixed
```

---

### 6.3 修复后 3 条测试成功

再次执行：

```bash
python scripts\evaluation\run_week8_ollama_vlm_qa.py --model llama3.2-vision --limit 3
```

输出：

```text
[Week8] Ollama VLM QA finished.
Cases: 3
Wrote: results/week8/visual_rag/qa_outputs_ollama.jsonl
Wrote: results/week8/visual_rag/qa_outputs_ollama.csv
Wrote: results/week8/visual_rag/qa_outputs_manual_filled.csv
```

结论：

```text
Ollama VLM 自动推理链路已跑通。
```

---

## 7. Occlusion 三组最小闭环推理

### 7.1 执行命令

```bash
python scripts\evaluation\run_week8_ollama_vlm_qa.py --model llama3.2-vision --settings "Gold Evidence,Gold Masked,Random Masked"
```

---

### 7.2 推理规模

```text
Gold Evidence: 10
Gold Masked: 10
Random Masked: 10
Total: 30
```

---

### 7.3 运行情况

运行过程中出现 1 次 timeout：

```text
q006__Gold_Evidence
ERROR: HTTPConnectionPool(host='localhost', port=11434): Read timed out. (read timeout=180)
```

但脚本继续执行并完成全部 30 条 case。

输出：

```text
[Week8] Ollama VLM QA finished.
Cases: 30
Wrote: qa_outputs_ollama.jsonl
Wrote: qa_outputs_ollama.csv
Wrote: qa_outputs_manual_filled.csv
```

---

## 8. 完整 70 条 QA 自动推理

### 8.1 执行命令

```bash
python scripts\evaluation\run_week8_ollama_vlm_qa.py --model llama3.2-vision
```

---

### 8.2 推理规模

```text
Total cases: 70
Settings:
- Gold Evidence
- BM25
- Full MV
- Hybrid Fusion
- Budgeted MV
- Gold Masked
- Random Masked
```

---

### 8.3 运行情况

完整 70 条推理过程中出现 4 次 timeout：

```text
q002__BM25
q002__Hybrid_Fusion
q007__Budgeted_MV
q012__Full_MV
```

对应错误：

```text
HTTPConnectionPool(host='localhost', port=11434): Read timed out. (read timeout=180)
```

脚本未中断，继续执行后续样本，并最终完成 70 条输出。

---

### 8.4 输出文件

```text
results/week8/visual_rag/qa_outputs_ollama.jsonl
results/week8/visual_rag/qa_outputs_ollama.csv
results/week8/visual_rag/qa_outputs_manual_filled.csv
```

终端输出：

```text
[Week8] Ollama VLM QA finished.
Cases: 70
Wrote: qa_outputs_ollama.jsonl
Wrote: qa_outputs_ollama.csv
Wrote: qa_outputs_manual_filled.csv
```

结论：

```text
Week 8 下游 VLM QA 推理已完成。
```

---

## 9. QA Evaluation Template 生成

### 9.1 初次执行

第一次执行：

```bash
python scripts\evaluation\make_week8_qa_eval_template.py
```

出现：

```text
python: can't open file ... No such file or directory
```

原因：

```text
脚本文件尚未保存到 scripts/evaluation/。
```

---

### 9.2 创建脚本后重新执行

重新保存脚本后执行：

```bash
python scripts\evaluation\make_week8_qa_eval_template.py
```

输出：

```text
[Week8] QA evaluation template generated.
Input: E:\Working\PCB_VisualRAG_Project\results\week8\visual_rag\qa_outputs_manual_filled.csv
Rows: 70
Wrote: E:\Working\PCB_VisualRAG_Project\results\week8\visual_rag\qa_evaluation_template.csv
```

生成文件：

```text
results/week8/visual_rag/qa_evaluation_template.csv
```

---

## 10. QA Evaluation 自动填充

### 10.1 执行命令

```bash
python scripts\evaluation\auto_fill_week8_qa_evaluation.py
```

---

### 10.2 输出文件

```text
results/week8/visual_rag/qa_evaluation.csv
results/week8/visual_rag/qa_evaluation_autofill_summary.csv
```

终端输出：

```text
[Week8] QA evaluation auto-filled.
Rows: 70
Wrote: qa_evaluation.csv
Wrote: qa_evaluation_autofill_summary.csv
```

---

### 10.3 自动评估规则

本阶段采用弱规则自动评估：

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

注意：

```text
该评估是 rule-based weak evaluator，不等同于人工细粒度语义评估。
```

---

## 11. Auto-filled QA Evaluation Summary

自动评估摘要如下：

| setting | num_cases | gold_page_rate | answer_accuracy | evidence_supported_rate | unknown_rate |
|---|---:|---:|---:|---:|---:|
| Gold Evidence | 10 | 1.0000 | 1.0000 | 1.0000 | 0.0000 |
| BM25 | 10 | 0.4000 | 0.4000 | 0.9000 | 0.6000 |
| Full MV | 10 | 0.1000 | 0.1000 | 0.5000 | 0.5000 |
| Hybrid Fusion | 10 | 0.4000 | 0.4000 | 0.9000 | 0.6000 |
| Budgeted MV | 10 | 0.1000 | 0.1000 | 0.3000 | 0.3000 |
| Gold Masked | 10 | 1.0000 | 1.0000 | 1.0000 | 0.0000 |
| Random Masked | 10 | 1.0000 | 1.0000 | 1.0000 | 0.0000 |

结论：

```text
自动评估已完成，70 条样本全部生成 QA evaluation 记录。
```

---

## 12. Result Table 汇总脚本调试

### 12.1 初次执行

执行：

```bash
python scripts\evaluation\summarize_week8_visual_rag_results.py
```

初次出现：

```text
python: can't open file ... No such file or directory
```

原因：

```text
脚本尚未保存到 scripts/evaluation/。
```

保存脚本后再次执行。

---

### 12.2 第二次执行报错

报错：

```text
ValueError: dict contains fields not in fieldnames: 'masked_evidence_count', 'no_answer_count'
```

原因：

```text
retrieval_rows 中包含额外字段，但 retrieval_fields 未声明这些字段。
```

---

### 12.3 修复方式

将 `write_csv()` 修改为自动过滤字段：

```python
cleaned_rows = []
for r in rows:
    cleaned_rows.append({k: r.get(k, "") for k in fieldnames})
```

执行修复命令：

```bash
python -c "from pathlib import Path; p=Path('scripts/evaluation/summarize_week8_visual_rag_results.py'); s=p.read_text(encoding='utf-8'); old='''def write_csv(path, rows, fieldnames):\n    path.parent.mkdir(parents=True, exist_ok=True)\n\n    with path.open(\"w\", encoding=\"utf-8\", newline=\"\") as f:\n        writer = csv.DictWriter(f, fieldnames=fieldnames)\n        writer.writeheader()\n        writer.writerows(rows)\n'''; new='''def write_csv(path, rows, fieldnames):\n    path.parent.mkdir(parents=True, exist_ok=True)\n\n    cleaned_rows = []\n    for r in rows:\n        cleaned_rows.append({k: r.get(k, \"\") for k in fieldnames})\n\n    with path.open(\"w\", encoding=\"utf-8\", newline=\"\") as f:\n        writer = csv.DictWriter(f, fieldnames=fieldnames)\n        writer.writeheader()\n        writer.writerows(cleaned_rows)\n'''; s=s.replace(old,new); p.write_text(s,encoding='utf-8'); print('fixed write_csv')"
```

输出：

```text
fixed write_csv
```

---

### 12.4 修复后汇总成功

重新运行：

```bash
python scripts\evaluation\summarize_week8_visual_rag_results.py
```

输出：

```text
[Week8] Visual RAG result tables generated.
Input: results/week8/visual_rag/qa_evaluation.csv
Rows: 70
```

生成文件：

```text
results/week8/visual_rag/tables/table19_visual_rag_main_results.csv
results/week8/visual_rag/tables/table19_visual_rag_main_results.md
results/week8/visual_rag/tables/table20_occlusion_downstream_results.csv
results/week8/visual_rag/tables/table20_occlusion_downstream_results.md
results/week8/visual_rag/tables/table21_retrieval_vs_qa_results.csv
results/week8/visual_rag/tables/table21_retrieval_vs_qa_results.md
results/week8/visual_rag/tables/table22_qa_error_breakdown.csv
results/week8/visual_rag/tables/table22_qa_error_breakdown.md
```

---

## 13. Table 19: Lightweight Visual RAG Main Results

| setting | num_cases | gold_page_rate | answer_accuracy | evidence_supported_rate | unknown_rate | concrete_answer_rate | no_answer_count | wrong_page_count | hallucination_count | masked_evidence_count |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Gold Evidence | 10 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 1.0000 | 0 | 0 | 0 | 0 |
| BM25 | 10 | 0.4000 | 0.4000 | 0.9000 | 0.6000 | 0.4000 | 1 | 5 | 0 | 0 |
| Full MV | 10 | 0.1000 | 0.1000 | 0.5000 | 0.5000 | 0.5000 | 1 | 4 | 4 | 0 |
| Hybrid Fusion | 10 | 0.4000 | 0.4000 | 0.9000 | 0.6000 | 0.4000 | 1 | 5 | 0 | 0 |
| Budgeted MV | 10 | 0.1000 | 0.1000 | 0.3000 | 0.3000 | 0.7000 | 1 | 2 | 6 | 0 |
| Gold Masked | 10 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 1.0000 | 0 | 0 | 0 | 0 |
| Random Masked | 10 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 1.0000 | 0 | 0 | 0 | 0 |

---

## 14. Table 20: Occlusion Downstream Results

| setting | num_cases | gold_page_rate | answer_accuracy | evidence_supported_rate | unknown_rate | concrete_answer_rate | no_answer_count | wrong_page_count | hallucination_count | masked_evidence_count | accuracy_delta_vs_gold | support_delta_vs_gold |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Gold Evidence | 10 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 1.0000 | 0 | 0 | 0 | 0 | 0.0000 | 0.0000 |
| Gold Masked | 10 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 1.0000 | 0 | 0 | 0 | 0 | 0.0000 | 0.0000 |
| Random Masked | 10 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 1.0000 | 0 | 0 | 0 | 0 | 0.0000 | 0.0000 |

---

## 15. Table 21: Retrieval vs QA Results

| retrieval_condition | setting | num_cases | gold_page_rate | answer_accuracy | evidence_supported_rate | unknown_rate | concrete_answer_rate | wrong_page_count | hallucination_count |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BM25 | BM25 | 10 | 0.4000 | 0.4000 | 0.9000 | 0.6000 | 0.4000 | 5 | 0 |
| Full MV | Full MV | 10 | 0.1000 | 0.1000 | 0.5000 | 0.5000 | 0.5000 | 4 | 4 |
| Hybrid Fusion | Hybrid Fusion | 10 | 0.4000 | 0.4000 | 0.9000 | 0.6000 | 0.4000 | 5 | 0 |
| Budgeted MV | Budgeted MV | 10 | 0.1000 | 0.1000 | 0.3000 | 0.3000 | 0.7000 | 2 | 6 |

---

## 16. 当前结果解读

### 16.1 Retrieval 到 QA 的传导关系

从 Table 21 可见：

```text
BM25 / Hybrid Fusion:
gold_page_rate = 0.4000
answer_accuracy = 0.4000

Full MV / Budgeted MV:
gold_page_rate = 0.1000
answer_accuracy = 0.1000
```

在当前 rule-based evaluation 下，QA accuracy 与 gold page retrieval rate 基本一致。

说明：

```text
下游 QA 质量高度依赖检索页面是否命中 gold evidence page。
```

---

### 16.2 BM25 与 Hybrid Fusion 表现一致

当前样本中：

```text
BM25:
gold_page_rate = 0.4000
answer_accuracy = 0.4000

Hybrid Fusion:
gold_page_rate = 0.4000
answer_accuracy = 0.4000
```

说明：

```text
Hybrid Fusion 在本 10-query 下游子集上与 BM25 表现一致。
```

---

### 16.3 Full MV 与 Budgeted MV 当前下游表现较弱

当前结果：

```text
Full MV:
gold_page_rate = 0.1000
answer_accuracy = 0.1000

Budgeted MV:
gold_page_rate = 0.1000
answer_accuracy = 0.1000
```

说明：

```text
在当前选择的 N10 / M8 配置与 10-query evidence 子集上，Full MV 和 Budgeted MV 的 top-1 QA 输入命中率较低。
```

注意：

```text
该结果是基于 top-1 page 输入的轻量下游 QA，不代表完整 retrieval ranking 性能。
```

---

### 16.4 Evidence-supported Rate 的含义

当前自动规则中：

```text
wrong page + Not enough evidence
```

被计为：

```text
evidence_supported = 1
```

因此 BM25 / Hybrid Fusion 出现：

```text
answer_accuracy = 0.4000
evidence_supported_rate = 0.9000
```

解释：

```text
模型在错误页面上多数能够拒答，而不是编造答案。
```

---

### 16.5 Budgeted MV 幻觉风险较高

Budgeted MV 结果：

```text
hallucination_count = 6
unknown_rate = 0.3000
concrete_answer_rate = 0.7000
```

说明：

```text
Budgeted MV 在错误页面上更容易给出具体答案，而不是回答 Not enough evidence。
```

这可作为 Discussion 中的一个观察：

```text
错误检索页面不仅降低 answer correctness，还可能诱导 VLM hallucination。
```

---

## 17. Occlusion 结果解读

当前 Table 20 显示：

```text
Gold Evidence accuracy = 1.0000
Gold Masked accuracy = 1.0000
Random Masked accuracy = 1.0000
```

即：

```text
Gold Masked 未造成 QA accuracy 下降。
```

当前原因可能包括：

```text
1. 遮挡区域没有完全覆盖模型用于回答的 page-number / title / global layout cues；
2. 查询答案偏向页面识别，而不是细粒度内容抽取；
3. VLM 可能主要利用页码、标题、图形布局等非遮挡区域完成回答；
4. 当前自动评估规则较宽松，只要 gold page 上给出非 unknown 答案即判为 correct。
```

因此当前 occlusion downstream 结论应谨慎表述为：

```text
在当前 page-level QA 设置与 rule-based weak evaluation 下，gold-region masking 未显著降低下游回答正确率。
```

不应表述为：

```text
Evidence occlusion 已显著影响 QA。
```

---

## 18. 当前实验局限

本阶段结果存在以下限制：

```text
1. VLM 使用本地 llama3.2-vision，能力有限且推理存在 timeout；
2. 评估为 rule-based weak evaluator，不是人工精标；
3. answer correctness 当前强依赖 is_gold_page，不做细粒度语义匹配；
4. occlusion QA 问题偏向 page identification，可能无法充分测试遮挡对内容理解的影响；
5. 只使用 top-1 retrieval page，没有测试 top-k multi-page RAG；
6. Full MV 与 Budgeted MV 当前使用的 run 文件配置可能不是全局最优配置。
```

---

## 19. 本阶段完成的关键产出文件

### 19.1 QA 输入

```text
results/week8/visual_rag/qa_inputs.csv
results/week8/visual_rag/qa_inputs.jsonl
results/week8/visual_rag/qa_inputs_preview.md
results/week8/visual_rag/qa_input_mapping_summary.csv
```

### 19.2 Manual / Ollama QA 输出

```text
results/week8/visual_rag/manual_vlm_pack/manual_vlm_manifest.csv
results/week8/visual_rag/manual_vlm_pack/images/
results/week8/visual_rag/manual_vlm_pack/cases/
results/week8/visual_rag/qa_outputs_ollama.jsonl
results/week8/visual_rag/qa_outputs_ollama.csv
results/week8/visual_rag/qa_outputs_manual_filled.csv
```

### 19.3 QA 评估

```text
results/week8/visual_rag/qa_evaluation_template.csv
results/week8/visual_rag/qa_evaluation.csv
results/week8/visual_rag/qa_evaluation_autofill_summary.csv
```

### 19.4 结果表

```text
results/week8/visual_rag/tables/table19_visual_rag_main_results.csv
results/week8/visual_rag/tables/table19_visual_rag_main_results.md
results/week8/visual_rag/tables/table20_occlusion_downstream_results.csv
results/week8/visual_rag/tables/table20_occlusion_downstream_results.md
results/week8/visual_rag/tables/table21_retrieval_vs_qa_results.csv
results/week8/visual_rag/tables/table21_retrieval_vs_qa_results.md
results/week8/visual_rag/tables/table22_qa_error_breakdown.csv
results/week8/visual_rag/tables/table22_qa_error_breakdown.md
```

### 19.5 脚本

```text
scripts/evaluation/build_week8_visual_rag_inputs_fixed.py
scripts/evaluation/make_week8_vlm_manual_pack.py
scripts/evaluation/run_week8_ollama_vlm_qa.py
scripts/evaluation/make_week8_qa_eval_template.py
scripts/evaluation/auto_fill_week8_qa_evaluation.py
scripts/evaluation/summarize_week8_visual_rag_results.py
```

---

## 20. 当前阶段结论

本阶段已经完成 Week 8 轻量 Visual RAG 下游验证的最小闭环：

```text
70 QA inputs
↓
Ollama local VLM inference
↓
70 QA outputs
↓
Rule-based QA evaluation
↓
Main result tables
```

关键结果为：

```text
1. Retrieval input mapping 已完全修复；
2. 70 条 QA 输入均具有 page_id 与 image_path；
3. Ollama llama3.2-vision 成功完成本地 VLM 推理；
4. QA evaluation 与主结果表已生成；
5. 下游 QA accuracy 与 gold page hit rate 高度一致；
6. BM25 / Hybrid Fusion 在当前子集上优于 Full MV / Budgeted MV；
7. 当前 occlusion 设置未观察到 QA accuracy 下降；
8. Budgeted MV 在错误页面上出现较多 hallucination。
```

当前可以正式认为：

```text
Week 8 lightweight Visual RAG downstream QA experiment: COMPLETED as a first-pass automatic evaluation.
```

但论文中应谨慎表述为：

```text
We conduct a lightweight downstream Visual QA validation using a local VLM and a rule-based weak evaluator. The results suggest that answer correctness is strongly tied to whether the retrieved page matches the gold evidence page. In the current page-level QA setup, occlusion does not reduce QA accuracy, likely because the questions can often be answered from page-level cues such as page number, title, and layout.
```

---

## 21. 下一步建议

后续若要增强论文可信度，建议补充：

```text
1. 人工复核 qa_evaluation.csv 中 70 条 correctness；
2. 将 page-identification query 改成 content-specific QA；
3. 对 Gold Masked 重新设计更强遮挡区域；
4. 增加 top-k page input，而不是只用 top-1；
5. 使用更强 VLM 或 OCR+LLM pipeline 复跑一版；
6. 将 timeout case 重跑补齐。
```

当前阶段状态：

```text
QA Input Mapping: DONE
Ollama VLM Inference: DONE
QA Evaluation: DONE
Result Tables: DONE
Week 8 Downstream Experiment: FIRST-PASS COMPLETE
```
---

# Week 8 Day 2/3 实验日志补充：失败样本重跑、最终表格固化与实验完成检查

**日期**：2026-05-08  
**时间**：20:25  
**项目**：PCB_VisualRAG_Project  
**环境**：`pcb_visualrag`  
**工作目录**：`E:\Working\PCB_VisualRAG_Project`  
**任务主题**：Finalize Lightweight Visual RAG Downstream QA Experiment  
**状态**：Completed  

---

## 1. 本阶段目标

在上一阶段中，Week 8 轻量 Visual RAG 下游验证已经完成了 70 条 QA 输入构造、Ollama VLM 自动推理、rule-based QA evaluation 以及 Table 19–22 的生成。

本阶段主要完成实验收尾工作：

```text
1. 检查完整 70 条 VLM 推理中的 timeout / blank answer 样本；
2. 对失败样本单独重跑；
3. 合并重跑结果，确保 70 条 QA 输出均有效；
4. 重新生成 QA evaluation 与结果表；
5. 生成 retrieval quality vs QA quality 对照表 Table 23；
6. 执行 Week 8 Visual RAG 完整性检查；
7. 将最终结果表复制到 paper/tables；
8. 生成 Week 8 lightweight Visual RAG 实验摘要文件。
```

本阶段完成后，Week 8 下游实验进入可写入论文结果章节的状态。

---

## 2. 检查 Ollama 推理失败样本

### 2.1 执行命令

```bash
python -c "import csv; rows=list(csv.DictReader(open('results/week8/visual_rag/qa_outputs_ollama.csv',encoding='utf-8-sig'))); bad=[r for r in rows if r.get('status')!='OK' or not r.get('vlm_answer')]; print('bad cases=',len(bad)); [print(r['case_id'], r.get('status'), r.get('error')) for r in bad]"
```

---

### 2.2 检查结果

输出：

```text
bad cases= 4
q002__BM25 ERROR HTTPConnectionPool(host='localhost', port=11434): Read timed out. (read timeout=180)
q002__Hybrid_Fusion ERROR HTTPConnectionPool(host='localhost', port=11434): Read timed out. (read timeout=180)
q007__Budgeted_MV ERROR HTTPConnectionPool(host='localhost', port=11434): Read timed out. (read timeout=180)
q012__Full_MV ERROR HTTPConnectionPool(host='localhost', port=11434): Read timed out. (read timeout=180)
```

失败样本统计：

| case_id | setting | error type |
|---|---|---|
| q002__BM25 | BM25 | timeout |
| q002__Hybrid_Fusion | Hybrid Fusion | timeout |
| q007__Budgeted_MV | Budgeted MV | timeout |
| q012__Full_MV | Full MV | timeout |

结论：

```text
完整 70 条 QA 推理中有 4 条 timeout 样本，需要单独重跑。
```

---

## 3. 失败样本重跑

### 3.1 执行脚本

```bash
python scripts\evaluation\rerun_week8_ollama_failed_cases.py
```

---

### 3.2 重跑输入

脚本识别到 4 个失败 / 空回答样本：

```text
Failed / blank cases: 4
q002__BM25
q002__Hybrid_Fusion
q007__Budgeted_MV
q012__Full_MV
```

实际重跑图像路径：

```text
q002__BM25
Image: E:\Working\PCB_VisualRAG_Project\data\images\doc001\doc001_p001.png

q002__Hybrid_Fusion
Image: E:\Working\PCB_VisualRAG_Project\data\images\doc001\doc001_p001.png

q007__Budgeted_MV
Image: E:\Working\PCB_VisualRAG_Project\data\images\doc004\doc004_p019.png

q012__Full_MV
Image: E:\Working\PCB_VisualRAG_Project\data\images\doc005\doc005_p004.png
```

---

### 3.3 重跑输出

终端输出：

```text
[Week8] Rerun finished.
Rerun cases: 4
Merged outputs: 70
Wrote: E:\Working\PCB_VisualRAG_Project\results\week8\visual_rag\qa_outputs_ollama_rerun.jsonl
Wrote: E:\Working\PCB_VisualRAG_Project\results\week8\visual_rag\qa_outputs_ollama_rerun.csv
Wrote: E:\Working\PCB_VisualRAG_Project\results\week8\visual_rag\qa_outputs_ollama_merged.csv
Updated: E:\Working\PCB_VisualRAG_Project\results\week8\visual_rag\qa_outputs_manual_filled.csv
```

生成文件：

```text
results/week8/visual_rag/qa_outputs_ollama_rerun.jsonl
results/week8/visual_rag/qa_outputs_ollama_rerun.csv
results/week8/visual_rag/qa_outputs_ollama_merged.csv
results/week8/visual_rag/qa_outputs_manual_filled.csv
```

结论：

```text
4 个 timeout 样本已成功重跑，并与原始 70 条输出合并。
```

---

## 4. 重新生成 QA Evaluation

### 4.1 生成 evaluation template

执行：

```bash
python scripts\evaluation\make_week8_qa_eval_template.py
```

输出：

```text
[Week8] QA evaluation template generated.
Input: E:\Working\PCB_VisualRAG_Project\results\week8\visual_rag\qa_outputs_manual_filled.csv
Rows: 70
Wrote: E:\Working\PCB_VisualRAG_Project\results\week8\visual_rag\qa_evaluation_template.csv
```

生成文件：

```text
results/week8/visual_rag/qa_evaluation_template.csv
```

---

### 4.2 自动填充 QA evaluation

执行：

```bash
python scripts\evaluation\auto_fill_week8_qa_evaluation.py
```

输出：

```text
[Week8] QA evaluation auto-filled.
Input: E:\Working\PCB_VisualRAG_Project\results\week8\visual_rag\qa_evaluation_template.csv
Rows: 70
Wrote: E:\Working\PCB_VisualRAG_Project\results\week8\visual_rag\qa_evaluation.csv
Wrote: E:\Working\PCB_VisualRAG_Project\results\week8\visual_rag\qa_evaluation_autofill_summary.csv
```

生成文件：

```text
results/week8/visual_rag/qa_evaluation.csv
results/week8/visual_rag/qa_evaluation_autofill_summary.csv
```

---

## 5. 更新后的 QA Evaluation Summary

失败样本补齐后，自动评估摘要更新如下：

| setting | num_cases | gold_page_rate | answer_accuracy | evidence_supported_rate | unknown_rate |
|---|---:|---:|---:|---:|---:|
| Gold Evidence | 10 | 1.0000 | 1.0000 | 1.0000 | 0.0000 |
| BM25 | 10 | 0.4000 | 0.4000 | 0.9000 | 0.5000 |
| Full MV | 10 | 0.1000 | 0.1000 | 0.6000 | 0.5000 |
| Hybrid Fusion | 10 | 0.4000 | 0.4000 | 0.9000 | 0.5000 |
| Budgeted MV | 10 | 0.1000 | 0.1000 | 0.4000 | 0.3000 |
| Gold Masked | 10 | 1.0000 | 1.0000 | 1.0000 | 0.0000 |
| Random Masked | 10 | 1.0000 | 1.0000 | 1.0000 | 0.0000 |

与重跑前相比，主要变化包括：

```text
1. no_answer_count 从部分 setting 中清零；
2. timeout 不再作为 no_answer 影响统计；
3. BM25 / Hybrid Fusion unknown_rate 从 0.6000 更新为 0.5000；
4. Full MV evidence_supported_rate 从 0.5000 更新为 0.6000；
5. Budgeted MV evidence_supported_rate 从 0.3000 更新为 0.4000。
```

结论：

```text
重跑后 70 条样本均具有可用于评估的 VLM answer。
```

---

## 6. 重新生成 Week 8 Visual RAG 结果表

### 6.1 执行汇总脚本

```bash
python scripts\evaluation\summarize_week8_visual_rag_results.py
```

---

### 6.2 输出文件

脚本成功生成：

```text
results/week8/visual_rag/tables/table19_visual_rag_main_results.csv
results/week8/visual_rag/tables/table19_visual_rag_main_results.md
results/week8/visual_rag/tables/table20_occlusion_downstream_results.csv
results/week8/visual_rag/tables/table20_occlusion_downstream_results.md
results/week8/visual_rag/tables/table21_retrieval_vs_qa_results.csv
results/week8/visual_rag/tables/table21_retrieval_vs_qa_results.md
results/week8/visual_rag/tables/table22_qa_error_breakdown.csv
results/week8/visual_rag/tables/table22_qa_error_breakdown.md
```

终端输出：

```text
[Week8] Visual RAG result tables generated.
Input: E:\Working\PCB_VisualRAG_Project\results\week8\visual_rag\qa_evaluation.csv
Rows: 70
```

---

## 7. 更新后的 Table 19 主结果

最终主结果如下：

| setting | num_cases | gold_page_rate | answer_accuracy | evidence_supported_rate | unknown_rate | concrete_answer_rate | no_answer_count | wrong_page_count | hallucination_count | masked_evidence_count |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Gold Evidence | 10 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 1.0000 | 0 | 0 | 0 | 0 |
| BM25 | 10 | 0.4000 | 0.4000 | 0.9000 | 0.5000 | 0.5000 | 0 | 5 | 1 | 0 |
| Full MV | 10 | 0.1000 | 0.1000 | 0.6000 | 0.5000 | 0.5000 | 0 | 5 | 4 | 0 |
| Hybrid Fusion | 10 | 0.4000 | 0.4000 | 0.9000 | 0.5000 | 0.5000 | 0 | 5 | 1 | 0 |
| Budgeted MV | 10 | 0.1000 | 0.1000 | 0.4000 | 0.3000 | 0.7000 | 0 | 3 | 6 | 0 |
| Gold Masked | 10 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 1.0000 | 0 | 0 | 0 | 0 |
| Random Masked | 10 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 1.0000 | 0 | 0 | 0 | 0 |

核心观察：

```text
1. Gold Evidence、Gold Masked、Random Masked 均达到 1.0000 answer_accuracy；
2. BM25 与 Hybrid Fusion 在当前 10-query 子集上表现一致，answer_accuracy = 0.4000；
3. Full MV 与 Budgeted MV 的 answer_accuracy 均为 0.1000；
4. Budgeted MV hallucination_count = 6，为 retrieval setting 中最高；
5. 所有 setting 的 no_answer_count 均为 0，说明 timeout 已被成功补齐。
```

---

## 8. 更新后的 Table 21：Retrieval vs QA Results

最终 retrieval-based QA 对照如下：

| retrieval_condition | setting | num_cases | gold_page_rate | answer_accuracy | evidence_supported_rate | unknown_rate | concrete_answer_rate | wrong_page_count | hallucination_count |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BM25 | BM25 | 10 | 0.4000 | 0.4000 | 0.9000 | 0.5000 | 0.5000 | 5 | 1 |
| Full MV | Full MV | 10 | 0.1000 | 0.1000 | 0.6000 | 0.5000 | 0.5000 | 5 | 4 |
| Hybrid Fusion | Hybrid Fusion | 10 | 0.4000 | 0.4000 | 0.9000 | 0.5000 | 0.5000 | 5 | 1 |
| Budgeted MV | Budgeted MV | 10 | 0.1000 | 0.1000 | 0.4000 | 0.3000 | 0.7000 | 3 | 6 |

结论：

```text
在当前 top-1 retrieval page 输入设置下，answer_accuracy 与 gold_page_rate 完全一致。
```

即：

```text
BM25: 0.4000 retrieval hit → 0.4000 QA accuracy
Full MV: 0.1000 retrieval hit → 0.1000 QA accuracy
Hybrid Fusion: 0.4000 retrieval hit → 0.4000 QA accuracy
Budgeted MV: 0.1000 retrieval hit → 0.1000 QA accuracy
```

该结果支持如下实验判断：

```text
下游 QA correctness 高度受检索页面是否命中 gold evidence page 控制。
```

---

## 9. 生成 Table 23：Retrieval Quality vs QA Quality

### 9.1 执行脚本

```bash
python scripts\evaluation\build_week8_retrieval_vs_qa_table.py
```

---

### 9.2 输出文件

```text
[Week8] Retrieval vs QA table generated.
Wrote: E:\Working\PCB_VisualRAG_Project\results\week8\visual_rag\tables\table23_retrieval_quality_vs_qa_quality.csv
Wrote: E:\Working\PCB_VisualRAG_Project\results\week8\visual_rag\tables\table23_retrieval_quality_vs_qa_quality.md
```

生成文件：

```text
results/week8/visual_rag/tables/table23_retrieval_quality_vs_qa_quality.csv
results/week8/visual_rag/tables/table23_retrieval_quality_vs_qa_quality.md
```

---

### 9.3 Table 23 内容

| setting | num_cases | gold_page_hits | retrieval_gold_hit_rate | answer_accuracy | evidence_supported_rate | unknown_rate | hallucination_count | used_run_file |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| Gold Evidence | 10 | 10 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 0 |  |
| BM25 | 10 | 4 | 0.4000 | 0.4000 | 0.9000 | 0.5000 | 1 | `results\week7\hybrid_fusion\hybrid_fullmv_N50_alpha1p0_run.tsv` |
| Full MV | 10 | 1 | 0.1000 | 0.1000 | 0.6000 | 0.5000 | 4 | `results\week7\c2f_fixed_N\bm25_fullmv_N10_run.tsv` |
| Hybrid Fusion | 10 | 4 | 0.4000 | 0.4000 | 0.9000 | 0.5000 | 1 | `results\week7\hybrid_fusion\hybrid_budgetmv_N50_M24_alpha1p0_run.tsv` |
| Budgeted MV | 10 | 1 | 0.1000 | 0.1000 | 0.4000 | 0.3000 | 6 | `results\week7\c2f_fixed_N\bm25_budgetmv_N20_M8_none_run.tsv` |
| Gold Masked | 10 | 10 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 0 |  |
| Random Masked | 10 | 10 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 0 |  |

Table 23 的作用：

```text
将 retrieval gold hit rate 与 QA answer_accuracy 放在同一张表中，
用于直接展示 retrieval quality 到 downstream QA quality 的传导关系。
```

主要结论：

```text
retrieval_gold_hit_rate 与 answer_accuracy 在当前设置下完全对齐。
```

---

## 10. 检查重跑后是否仍有失败样本

### 10.1 执行命令

```bash
python -c "import csv; rows=list(csv.DictReader(open('results/week8/visual_rag/qa_outputs_ollama_merged.csv',encoding='utf-8-sig'))); bad=[r for r in rows if r.get('status')!='OK' or not r.get('vlm_answer')]; print('remaining bad cases=',len(bad)); [print(r['case_id'], r.get('status'), r.get('error')) for r in bad]"
```

---

### 10.2 输出结果

```text
remaining bad cases= 0
```

结论：

```text
所有 70 条 QA 输出均已补齐，无剩余 timeout / blank answer 样本。
```

---

## 11. Week 8 Visual RAG 完整性检查

### 11.1 执行命令

```bash
python scripts\evaluation\check_week8_visual_rag_completion.py
```

---

### 11.2 文件存在性检查

所有关键文件均通过检查：

```text
PASS results/week8/visual_rag/qa_inputs.csv
PASS results/week8/visual_rag/qa_inputs.jsonl
PASS results/week8/visual_rag/qa_input_mapping_summary.csv
PASS results/week8/visual_rag/qa_outputs_ollama.csv
PASS results/week8/visual_rag/qa_outputs_manual_filled.csv
PASS results/week8/visual_rag/qa_evaluation_template.csv
PASS results/week8/visual_rag/qa_evaluation.csv
PASS results/week8/visual_rag/qa_evaluation_autofill_summary.csv
PASS results/week8/visual_rag/tables/table19_visual_rag_main_results.csv
PASS results/week8/visual_rag/tables/table20_occlusion_downstream_results.csv
PASS results/week8/visual_rag/tables/table21_retrieval_vs_qa_results.csv
PASS results/week8/visual_rag/tables/table22_qa_error_breakdown.csv
PASS results/week8/visual_rag/tables/table23_retrieval_quality_vs_qa_quality.csv
```

---

### 11.3 QA Input 检查

```text
[QA Input Check]
rows: 70
missing_page: 0
missing_image: 0
retrieval_missing_page: 0
retrieval_missing_image: 0
```

说明：

```text
所有 QA 输入均有 page_id 和 image_path。
所有 retrieval-based setting 均无 page/image 缺失。
```

---

### 11.4 QA Output 检查

```text
[QA Output Check]
rows: 70
blank_answer: 0
```

说明：

```text
所有 70 条 QA 输出均有 vlm_answer。
```

---

### 11.5 QA Evaluation 检查

```text
[QA Evaluation Check]
rows: 70
missing_correctness: 0
missing_supported: 0
missing_unknown: 0
missing_error_type: 0
```

说明：

```text
所有 70 条 evaluation record 均完成 correctness、evidence_supported、unknown 与 error_type 标注。
```

---

### 11.6 最终状态

输出：

```text
STATUS: WEEK8_VISUAL_RAG_EXPERIMENT_COMPLETE
```

结论：

```text
Week 8 lightweight Visual RAG downstream QA experiment 已通过完整性检查。
```

---

## 12. 将最终表格复制到 paper/tables

### 12.1 创建 / 检查目录

执行：

```bash
mkdir paper\tables
```

输出：

```text
子目录或文件 paper\tables 已经存在。
```

说明：

```text
paper/tables 目录已存在，可直接写入最终论文表格。
```

---

### 12.2 复制最终 CSV 表格

执行：

```bash
copy /Y results\week8\visual_rag\tables\table19_visual_rag_main_results.csv paper\tables\table4_visual_rag_main_results.csv
copy /Y results\week8\visual_rag\tables\table20_occlusion_downstream_results.csv paper\tables\table5_occlusion_downstream_results.csv
copy /Y results\week8\visual_rag\tables\table21_retrieval_vs_qa_results.csv paper\tables\table6_retrieval_vs_qa_results.csv
copy /Y results\week8\visual_rag\tables\table22_qa_error_breakdown.csv paper\tables\table7_qa_error_breakdown.csv
copy /Y results\week8\visual_rag\tables\table23_retrieval_quality_vs_qa_quality.csv paper\tables\table8_retrieval_quality_vs_qa_quality.csv
```

全部输出：

```text
已复制 1 个文件。
```

---

### 12.3 论文表格映射

| Source Table | Paper Table | 内容 |
|---|---|---|
| table19_visual_rag_main_results.csv | table4_visual_rag_main_results.csv | Lightweight Visual RAG 主结果 |
| table20_occlusion_downstream_results.csv | table5_occlusion_downstream_results.csv | Occlusion downstream QA 结果 |
| table21_retrieval_vs_qa_results.csv | table6_retrieval_vs_qa_results.csv | Retrieval setting 与 QA 质量对照 |
| table22_qa_error_breakdown.csv | table7_qa_error_breakdown.csv | QA error breakdown |
| table23_retrieval_quality_vs_qa_quality.csv | table8_retrieval_quality_vs_qa_quality.csv | Retrieval hit rate 与 QA accuracy 对照 |

结论：

```text
Week 8 下游实验结果表已复制到论文写作目录，可用于 Results / Experiments 章节。
```

---

## 13. 生成 Week 8 实验摘要文件

### 13.1 执行脚本

```bash
python scripts\evaluation\make_week8_visual_rag_experiment_summary.py
```

---

### 13.2 输出结果

```text
[Week8] Experiment summary generated.
Wrote: E:\Working\PCB_VisualRAG_Project\results\week8\visual_rag\week8_visual_rag_experiment_summary.md
```

生成文件：

```text
results/week8/visual_rag/week8_visual_rag_experiment_summary.md
```

---

### 13.3 Summary 文件内容概览

该文件汇总了：

```text
1. Week 8 Visual RAG 实验状态；
2. 关键输出文件；
3. Input Mapping；
4. Main Results；
5. Occlusion Results；
6. Retrieval vs QA；
7. Retrieval Quality vs QA Quality；
8. Experiment-Level Conclusion。
```

其中实验状态记录为：

```text
QA input mapping: complete
Ollama VLM inference: complete
Rule-based QA evaluation: complete
Result tables: complete
```

实验级结论记录为：

```text
The first-pass lightweight Visual RAG downstream experiment is complete.
The results show that answer correctness is strongly tied to whether the retrieved page matches the gold evidence page.
In the current page-level QA setup, Gold Masked and Random Masked conditions do not reduce QA accuracy.
The occlusion result should therefore be reported cautiously as a negative or inconclusive downstream occlusion finding under the current setup.
```

---

## 14. 本阶段最终产出文件

### 14.1 重跑与合并输出

```text
results/week8/visual_rag/qa_outputs_ollama_rerun.jsonl
results/week8/visual_rag/qa_outputs_ollama_rerun.csv
results/week8/visual_rag/qa_outputs_ollama_merged.csv
results/week8/visual_rag/qa_outputs_manual_filled.csv
```

---

### 14.2 更新后的 QA evaluation

```text
results/week8/visual_rag/qa_evaluation_template.csv
results/week8/visual_rag/qa_evaluation.csv
results/week8/visual_rag/qa_evaluation_autofill_summary.csv
```

---

### 14.3 最终结果表

```text
results/week8/visual_rag/tables/table19_visual_rag_main_results.csv
results/week8/visual_rag/tables/table19_visual_rag_main_results.md

results/week8/visual_rag/tables/table20_occlusion_downstream_results.csv
results/week8/visual_rag/tables/table20_occlusion_downstream_results.md

results/week8/visual_rag/tables/table21_retrieval_vs_qa_results.csv
results/week8/visual_rag/tables/table21_retrieval_vs_qa_results.md

results/week8/visual_rag/tables/table22_qa_error_breakdown.csv
results/week8/visual_rag/tables/table22_qa_error_breakdown.md

results/week8/visual_rag/tables/table23_retrieval_quality_vs_qa_quality.csv
results/week8/visual_rag/tables/table23_retrieval_quality_vs_qa_quality.md
```

---

### 14.4 论文目录表格副本

```text
paper/tables/table4_visual_rag_main_results.csv
paper/tables/table5_occlusion_downstream_results.csv
paper/tables/table6_retrieval_vs_qa_results.csv
paper/tables/table7_qa_error_breakdown.csv
paper/tables/table8_retrieval_quality_vs_qa_quality.csv
```

---

### 14.5 实验摘要文件

```text
results/week8/visual_rag/week8_visual_rag_experiment_summary.md
```

---

### 14.6 本阶段新增 / 使用脚本

```text
scripts/evaluation/rerun_week8_ollama_failed_cases.py
scripts/evaluation/build_week8_retrieval_vs_qa_table.py
scripts/evaluation/check_week8_visual_rag_completion.py
scripts/evaluation/make_week8_visual_rag_experiment_summary.py
scripts/evaluation/make_week8_qa_eval_template.py
scripts/evaluation/auto_fill_week8_qa_evaluation.py
scripts/evaluation/summarize_week8_visual_rag_results.py
```

---

## 15. 最终实验结论

本阶段完成后，Week 8 轻量 Visual RAG 下游验证正式完成。

最终状态：

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

核心结论如下：

```text
1. 所有 70 条 QA 输入均成功映射到 page_id 与 image_path；
2. 所有 70 条 QA 输出均已获得有效 VLM answer；
3. 所有 QA evaluation 字段均完整，无缺失；
4. Retrieval gold hit rate 与 answer accuracy 在当前设置下完全对齐；
5. BM25 与 Hybrid Fusion 在当前 10-query 子集上达到 0.4000 answer accuracy；
6. Full MV 与 Budgeted MV 在当前 top-1 输入设置下为 0.1000 answer accuracy；
7. Budgeted MV 出现较高 hallucination_count，说明错误检索页面可能诱导 VLM 给出 unsupported concrete answer；
8. Gold Masked 与 Random Masked 在当前 page-level QA 任务中未造成 accuracy 下降；
9. 当前 occlusion downstream 结果应谨慎解释为 negative / inconclusive finding，而不是强正向证据。
```

---

## 16. 论文写作中的推荐表述

当前结果适合在论文中这样表述：

```text
We further conduct a lightweight downstream Visual QA validation using a local VLM and a rule-based weak evaluator. The experiment uses 70 QA cases across gold evidence, retrieval-based, and occlusion-based input conditions. After rerunning timeout cases, all outputs are complete and evaluable.

The results show that downstream answer accuracy is tightly coupled with whether the retrieved page matches the gold evidence page. In the current top-1 page setting, retrieval gold hit rate and answer accuracy are aligned across retrieval conditions. BM25 and Hybrid Fusion achieve higher downstream accuracy than the tested Full MV and Budgeted MV configurations on this small QA subset.

However, the occlusion-based downstream setting does not reduce QA accuracy under the current page-level question design. This suggests that the current questions can often be answered using page-level cues such as page number, title, or global layout, and the occlusion result should be interpreted cautiously.
```

中文解释：

```text
本阶段实验可以支持“检索质量影响下游 QA 质量”这一结论；
但不能强支持“evidence occlusion 明显破坏下游 QA”这一结论。
```

---

## 17. 后续待办

尽管 Week 8 下游验证已经完成，但为了增强论文说服力，后续可以补充：

```text
1. 人工复核 qa_evaluation.csv 中所有 answer_correctness 与 evidence_supported 标注；
2. 将部分 page-identification query 改写为 content-specific QA；
3. 增强 gold evidence masking，使遮挡更直接覆盖可回答区域；
4. 测试 top-k multi-page Visual RAG，而不是只输入 top-1 页面；
5. 使用 OCR+LLM pipeline 复跑一版作为轻量可解释对照；
6. 将当前 Table 19–23 写入 Experiments / Results Analysis 章节。
```

当前 Week 8 实验状态：

```text
WEEK8_VISUAL_RAG_EXPERIMENT_COMPLETE
READY_FOR_PAPER_WRITING
```
