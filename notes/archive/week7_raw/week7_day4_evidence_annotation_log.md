# Week 7 Day 4 实验日志：Evidence Query Subset 与区域级 bbox 标注

**日期**：2026-05-08  
**项目**：PCB_VisualRAG_Project  
**环境**：`pcb_visualrag`  
**工作目录**：`E:\Working\PCB_VisualRAG_Project`

---

## Task 1：Evidence Query Subset 构建

### 1. 实验目标

Day 4 开始进入 evidence attribution 阶段，目标是构建一个小规模、高质量的 evidence query subset，用于后续 Evidence Hit 与 Occlusion 实验。

本日计划产出：

```text
data/annotations/evidence_query_subset.jsonl
data/annotations/evidence_regions.jsonl
data/annotations/evidence_annotation_guideline.md
artifacts/evidence_annotation_screenshots
results/week7/evidence_annotation/evidence_subset_candidates.csv
results/week7/evidence_annotation/evidence_subset_selection_report.md
```

---

### 2. 执行命令

运行 Evidence 子集选择脚本：

```bash
python scripts\annotation\select_week7_day4_evidence_subset.py
```

---

### 3. 运行结果

终端输出：

```text
[Week7-Day4] Evidence subset selected.
Selected count: 10
Subset: E:\Working\PCB_VisualRAG_Project\data\annotations\evidence_query_subset.jsonl
Regions: E:\Working\PCB_VisualRAG_Project\data\annotations\evidence_regions.jsonl
Candidates: E:\Working\PCB_VisualRAG_Project\results\week7\evidence_annotation\evidence_subset_candidates.csv
Report: E:\Working\PCB_VisualRAG_Project\results\week7\evidence_annotation\evidence_subset_selection_report.md

query_id,query_type,gold_page_id,evidence_type,retrievable,best_rank
q001,unknown,doc001_p001,region,yes,2
q002,unknown,doc001_p002,region,yes,1
q004,unknown,doc001_p004,region,yes,1
q006,unknown,doc002_p001,region,yes,1
q007,unknown,doc002_p001,region,yes,2
q008,unknown,doc003_p007,region,yes,1
q009,unknown,doc003_p008,region,yes,1
q010,unknown,doc003_p009,region,yes,2
q011,unknown,doc003_p010,region,yes,2
q012,unknown,doc003_p011,region,yes,2
```

---

### 4. 子集样本结果

本次自动选择了 10 条 evidence query 样本。

| Query ID | Query Type | Gold Page | Evidence Type | Retrievable | Best Rank |
|---|---|---|---|---|---:|
| q001 | unknown | doc001_p001 | region | yes | 2 |
| q002 | unknown | doc001_p002 | region | yes | 1 |
| q004 | unknown | doc001_p004 | region | yes | 1 |
| q006 | unknown | doc002_p001 | region | yes | 1 |
| q007 | unknown | doc002_p001 | region | yes | 2 |
| q008 | unknown | doc003_p007 | region | yes | 1 |
| q009 | unknown | doc003_p008 | region | yes | 1 |
| q010 | unknown | doc003_p009 | region | yes | 2 |
| q011 | unknown | doc003_p010 | region | yes | 2 |
| q012 | unknown | doc003_p011 | region | yes | 2 |

---

### 5. Query Type 加载问题

检查 `evidence_query_subset.jsonl` 后发现：

```text
query 字段为空
query_type 全部为 unknown
page_type 全部为 unknown
evidence_type 全部为 region
```

实际文件内容摘要：

```json
{"query_id": "q001", "query": "", "gold_page_id": "doc001_p001", "query_type": "unknown", "page_type": "unknown", "evidence_type": "region"}
{"query_id": "q002", "query": "", "gold_page_id": "doc001_p002", "query_type": "unknown", "page_type": "unknown", "evidence_type": "region"}
{"query_id": "q004", "query": "", "gold_page_id": "doc001_p004", "query_type": "unknown", "page_type": "unknown", "evidence_type": "region"}
```

原因判断：

- 脚本成功读取了 `qrels`；
- 脚本成功根据 run 文件判断了 gold page 是否可召回；
- 但未成功读取 query 文本与 query type metadata；
- 因此当前选择逻辑退化为基于 qrels 与 retrievable rank 的选择；
- 当前子集满足数量要求，但暂未满足“覆盖不同 query type”的要求。

---

### 6. 候选集文件检查

执行命令：

```bash
type results\week7\evidence_annotation\evidence_subset_candidates.csv
```

候选集包含 30 条 query，其中多数 query 可被 BM25 / Hybrid run 召回。

候选摘要：

| Query ID | Gold Page | Query Type | Retrievable | Best Rank | Matched Run |
|---|---|---|---|---:|---|
| q001 | doc001_p001 | unknown | yes | 2 | hybrid_budgetmv_N50_M24_alpha0p9_run.tsv |
| q002 | doc001_p002 | unknown | yes | 1 | bm25_fullmv_N10_run.tsv |
| q004 | doc001_p004 | unknown | yes | 1 | hybrid_budgetmv_N50_M24_alpha0p4_run.tsv |
| q006 | doc002_p001 | unknown | yes | 1 | hybrid_budgetmv_N50_M24_alpha0p8_run.tsv |
| q007 | doc002_p001 | unknown | yes | 2 | hybrid_budgetmv_N50_M24_alpha0p8_run.tsv |
| q008 | doc003_p007 | unknown | yes | 1 | bm25_budgetmv_N20_M8_none_run.tsv |
| q009 | doc003_p008 | unknown | yes | 1 | hybrid_budgetmv_N50_M24_alpha0p5_run.tsv |
| q010 | doc003_p009 | unknown | yes | 2 | hybrid_budgetmv_N50_M24_alpha0p4_run.tsv |
| q011 | doc003_p010 | unknown | yes | 2 | hybrid_budgetmv_N50_M24_alpha0p8_run.tsv |
| q012 | doc003_p011 | unknown | yes | 2 | hybrid_budgetmv_N50_M24_alpha0p6_run.tsv |

---

### 7. 输出文件检查

已生成文件：

```text
data/annotations/evidence_query_subset.jsonl
data/annotations/evidence_regions.jsonl
results/week7/evidence_annotation/evidence_subset_candidates.csv
results/week7/evidence_annotation/evidence_subset_selection_report.md
```

尚未生成文件：

```text
data/annotations/evidence_annotation_guideline.md
```

检查命令结果：

```bash
type data\annotations\evidence_annotation_guideline.md
```

输出：

```text
系统找不到指定的文件。
```

---

## Task 2：Evidence Regions 初始文件生成

### 1. 生成文件

执行命令：

```bash
type data\annotations\evidence_regions.jsonl
```

当前文件内容：

```json
{"query_id": "q001", "page_id": "doc001_p001", "region_id": "r1", "bbox": [0, 0, 0, 0], "region_type": "region", "evidence_note": "TODO", "bbox_status": "todo"}
{"query_id": "q002", "page_id": "doc001_p002", "region_id": "r1", "bbox": [0, 0, 0, 0], "region_type": "region", "evidence_note": "TODO", "bbox_status": "todo"}
{"query_id": "q004", "page_id": "doc001_p004", "region_id": "r1", "bbox": [0, 0, 0, 0], "region_type": "region", "evidence_note": "TODO", "bbox_status": "todo"}
{"query_id": "q006", "page_id": "doc002_p001", "region_id": "r1", "bbox": [0, 0, 0, 0], "region_type": "region", "evidence_note": "TODO", "bbox_status": "todo"}
{"query_id": "q007", "page_id": "doc002_p001", "region_id": "r1", "bbox": [0, 0, 0, 0], "region_type": "region", "evidence_note": "TODO", "bbox_status": "todo"}
{"query_id": "q008", "page_id": "doc003_p007", "region_id": "r1", "bbox": [0, 0, 0, 0], "region_type": "region", "evidence_note": "TODO", "bbox_status": "todo"}
{"query_id": "q009", "page_id": "doc003_p008", "region_id": "r1", "bbox": [0, 0, 0, 0], "region_type": "region", "evidence_note": "TODO", "bbox_status": "todo"}
{"query_id": "q010", "page_id": "doc003_p009", "region_id": "r1", "bbox": [0, 0, 0, 0], "region_type": "region", "evidence_note": "TODO", "bbox_status": "todo"}
{"query_id": "q011", "page_id": "doc003_p010", "region_id": "r1", "bbox": [0, 0, 0, 0], "region_type": "region", "evidence_note": "TODO", "bbox_status": "todo"}
{"query_id": "q012", "page_id": "doc003_p011", "region_id": "r1", "bbox": [0, 0, 0, 0], "region_type": "region", "evidence_note": "TODO", "bbox_status": "todo"}
```

---

### 2. 当前标注状态

当前 `evidence_regions.jsonl` 是自动生成的待标注模板，所有 bbox 均为占位值：

```text
[0, 0, 0, 0]
```

所有标注状态均为：

```text
bbox_status = todo
```

因此当前文件还不能作为最终 evidence region 标注结果。

---

## Task 3：标注验证

### 1. 执行命令

```bash
python scripts\annotation\validate_week7_day4_evidence_annotations.py
```

---

### 2. 验证结果

终端输出：

```text
[Week7-Day4] Evidence annotation validation completed.
Subset count: 10
Region count: 10
Failed count: 20
Global status: FAILED
Validation CSV: E:\Working\PCB_VisualRAG_Project\results\week7\evidence_annotation\evidence_annotation_validation.csv
Validation MD: E:\Working\PCB_VisualRAG_Project\results\week7\evidence_annotation\evidence_annotation_validation.md
```

---

### 3. FAILED 检查

执行命令：

```bash
findstr /I "FAILED" results\week7\evidence_annotation\evidence_annotation_validation.csv
```

输出：

```text
evidence_query_subset.jsonl,1,q001,doc001_p001,,,FAILED,missing_screenshot
evidence_query_subset.jsonl,2,q002,doc001_p002,,,FAILED,missing_screenshot
evidence_query_subset.jsonl,3,q004,doc001_p004,,,FAILED,missing_screenshot
evidence_query_subset.jsonl,4,q006,doc002_p001,,,FAILED,missing_screenshot
evidence_query_subset.jsonl,5,q007,doc002_p001,,,FAILED,missing_screenshot
evidence_query_subset.jsonl,6,q008,doc003_p007,,,FAILED,missing_screenshot
evidence_query_subset.jsonl,7,q009,doc003_p008,,,FAILED,missing_screenshot
evidence_query_subset.jsonl,8,q010,doc003_p009,,,FAILED,missing_screenshot
evidence_query_subset.jsonl,9,q011,doc003_p010,,,FAILED,missing_screenshot
evidence_query_subset.jsonl,10,q012,doc003_p011,,,FAILED,missing_screenshot
evidence_regions.jsonl,1,q001,doc001_p001,r1,"[0, 0, 0, 0]",FAILED,bbox_invalid_or_zero_area;bbox_status_not_done
evidence_regions.jsonl,2,q002,doc001_p002,r1,"[0, 0, 0, 0]",FAILED,bbox_invalid_or_zero_area;bbox_status_not_done
evidence_regions.jsonl,3,q004,doc001_p004,r1,"[0, 0, 0, 0]",FAILED,bbox_invalid_or_zero_area;bbox_status_not_done
evidence_regions.jsonl,4,q006,doc002_p001,r1,"[0, 0, 0, 0]",FAILED,bbox_invalid_or_zero_area;bbox_status_not_done
evidence_regions.jsonl,5,q007,doc002_p001,r1,"[0, 0, 0, 0]",FAILED,bbox_invalid_or_zero_area;bbox_status_not_done
evidence_regions.jsonl,6,q008,doc003_p007,r1,"[0, 0, 0, 0]",FAILED,bbox_invalid_or_zero_area;bbox_status_not_done
evidence_regions.jsonl,7,q009,doc003_p008,r1,"[0, 0, 0, 0]",FAILED,bbox_invalid_or_zero_area;bbox_status_not_done
evidence_regions.jsonl,8,q010,doc003_p009,r1,"[0, 0, 0, 0]",FAILED,bbox_invalid_or_zero_area;bbox_status_not_done
evidence_regions.jsonl,9,q011,doc003_p010,r1,"[0, 0, 0, 0]",FAILED,bbox_invalid_or_zero_area;bbox_status_not_done
evidence_regions.jsonl,10,q012,doc003_p011,r1,"[0, 0, 0, 0]",FAILED,bbox_invalid_or_zero_area;bbox_status_not_done
```

---

### 4. FAILED 原因归纳

当前共 20 条 failed validation。

| Failed Type | Count | 原因 |
|---|---:|---|
| missing_screenshot | 10 | 每条 query 尚未保存 bbox 检查截图 |
| bbox_invalid_or_zero_area | 10 | bbox 仍为 `[0, 0, 0, 0]` |
| bbox_status_not_done | 10 | bbox_status 仍为 `todo` |

其中 region 文件每条样本同时包含两个失败原因：

```text
bbox_invalid_or_zero_area
bbox_status_not_done
```

---

## Task 4：标注截图目录检查

执行命令：

```bash
dir artifacts\evidence_annotation_screenshots
```

输出：

```text
E:\Working\PCB_VisualRAG_Project\artifacts\evidence_annotation_screenshots 的目录

05/08/2026  01:02 PM    <DIR>          .
05/08/2026  01:02 PM    <DIR>          ..
               0 个文件              0 字节
```

当前截图目录为空，说明尚未保存 bbox 检查截图。

---

## 当前问题与处理计划

### 1. Query metadata 未成功读取

当前 evidence 子集中：

```text
query = ""
query_type = unknown
page_type = unknown
evidence_type = region
```

后续需要补充或修正 query metadata 来源，使 query type 能够覆盖：

```text
parameter_lookup
structure_legend_interpretation
component_localization
similarity_based_interference
cross_page_consistency
```

---

### 2. bbox 尚未标注

当前所有 bbox 仍为：

```text
[0, 0, 0, 0]
```

后续需要打开 gold page 原图，手动标注真实 evidence region bbox，并将：

```text
bbox_status = todo
```

改为：

```text
bbox_status = done
```

---

### 3. guideline 文件尚未创建

当前执行：

```bash
type data\annotations\evidence_annotation_guideline.md
```

结果为：

```text
系统找不到指定的文件。
```

后续需要创建：

```text
data/annotations/evidence_annotation_guideline.md
```

---

### 4. 标注截图尚未保存

当前截图目录：

```text
artifacts/evidence_annotation_screenshots
```

为空。

后续每条 evidence query 需要保存一张 bbox 检查截图，例如：

```text
q001_r1_bbox_check.png
q002_r1_bbox_check.png
q004_r1_bbox_check.png
q006_r1_bbox_check.png
q007_r1_bbox_check.png
q008_r1_bbox_check.png
q009_r1_bbox_check.png
q010_r1_bbox_check.png
q011_r1_bbox_check.png
q012_r1_bbox_check.png
```

---

## Day 4 阶段性验收结论

| 验收项 | 当前结果 | 是否通过 |
|---|---|---|
| 8–12 条 region-level 样本 | 已生成 10 条 | Passed |
| 每条样本都有 gold page | 10 条均有 gold page | Passed |
| 每条样本可被检索系统召回 | 10 条均 retrievable=yes | Passed |
| evidence_query_subset.jsonl 生成 | 已生成 | Passed |
| evidence_regions.jsonl 生成 | 已生成 | Passed |
| evidence_subset_candidates.csv 生成 | 已生成 | Passed |
| evidence_subset_selection_report.md 生成 | 已生成 | Passed |
| query 文本成功加载 | query 为空 | Failed |
| query type 成功加载 | 全部为 unknown | Failed |
| evidence_annotation_guideline.md 生成 | 文件不存在 | Failed |
| 每条样本都有明确 bbox | 当前均为 `[0,0,0,0]` | Failed |
| bbox_status 均为 done | 当前均为 `todo` | Failed |
| 标注检查截图保存 | 截图目录为空 | Failed |
| validation 无 FAILED | failed_count=20 | Failed |

---

## Day 4 当前状态

```text
Week 7 Day 4 Status: IN PROGRESS
```

当前已完成：

1. Evidence subset 自动选择流程已跑通；
2. 成功生成 10 条 evidence query subset；
3. 成功生成待标注 evidence region 模板；
4. 成功生成候选集与选择报告；
5. 成功运行 validation 检查脚本。

当前未完成：

1. query metadata 未正确加载；
2. query type 未覆盖不同类别；
3. evidence_annotation_guideline.md 未创建；
4. bbox 尚未手动标注；
5. bbox 检查截图尚未保存；
6. validation 当前为 FAILED。

下一步需要优先处理：

```text
1. 创建 evidence_annotation_guideline.md
2. 补充或修复 query / query_type metadata
3. 手动标注 evidence_regions.jsonl 中 10 条 bbox
4. 保存 10 张 bbox 检查截图
5. 重新运行 validate_week7_day4_evidence_annotations.py
6. 确认 findstr FAILED 无输出
```
