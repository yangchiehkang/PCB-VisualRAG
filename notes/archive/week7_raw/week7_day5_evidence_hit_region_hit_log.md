# Week 7 Day 5 实验日志：Evidence Hit@k 与 Region Hit@k

**日期**：2026-05-08  
**项目**：PCB_VisualRAG_Project  
**环境**：`pcb_visualrag`  
**工作目录**：`E:\Working\PCB_VisualRAG_Project`

---

## Task 1：页级 Evidence Hit@k

### 1. 实验目标

本任务评估不同检索方法是否能够在 Top-k 页面结果中命中 gold evidence page。

评价指标为：

```text
Evidence Hit@1
Evidence Hit@5
Evidence Hit@10
```

使用 Day 4 生成的 evidence query subset：

```text
data/annotations/evidence_query_subset.jsonl
```

当前 evidence subset 包含 10 条样本。

---

### 2. 执行命令

创建结果目录：

```bash
mkdir results\week7\evidence_hit
```

运行评估脚本：

```bash
python scripts\evaluation\evaluate_week7_day5_evidence_hit_atk.py
```

---

### 3. 输出文件

脚本成功生成以下文件：

```text
results/week7/evidence_hit/evidence_hit_atk_results.csv
results/week7/evidence_hit/evidence_hit_atk_results.md
results/week7/evidence_hit/evidence_hit_atk_per_query.csv
results/week7/evidence_hit/evidence_hit_atk_summary.json
```

目录检查结果：

```text
05/08/2026  01:12 PM             5,905 evidence_hit_atk_per_query.csv
05/08/2026  01:12 PM               676 evidence_hit_atk_results.csv
05/08/2026  01:12 PM             1,083 evidence_hit_atk_results.md
05/08/2026  01:12 PM             1,681 evidence_hit_atk_summary.json
```

---

### 4. Evidence Hit@k 总体结果

执行命令：

```bash
type results\week7\evidence_hit\evidence_hit_atk_results.csv
```

得到结果：

| Method | Evidence Hit@1 | Evidence Hit@5 | Evidence Hit@10 | Query Count | Missing Query Count | Status |
|---|---:|---:|---:|---:|---:|---|
| BM25 | 0.4000 | 1.0000 | 1.0000 | 10 | 0 | PASSED |
| Single-vector Visual | - | - | - | 10 | 10 | MISSING_RUN |
| Full MV | 0.1000 | 0.4000 | 1.0000 | 10 | 0 | PASSED |
| Budgeted MV | 0.1000 | 0.2000 | 0.4000 | 10 | 0 | PASSED |
| BM25 + Budgeted MV | 0.1000 | 0.2000 | 0.4000 | 10 | 0 | PASSED |
| Hybrid Fusion | 0.4000 | 1.0000 | 1.0000 | 10 | 0 | PASSED |

---

### 5. 使用的 Run 文件

| Method | Run File |
|---|---|
| BM25 | `results\week7\hybrid_fusion\hybrid_fullmv_N50_alpha1p0_run.tsv` |
| Single-vector Visual | MISSING |
| Full MV | `results\week7\c2f_fixed_N\bm25_fullmv_N10_run.tsv` |
| Budgeted MV | `results\week7\c2f_fixed_N\bm25_budgetmv_N20_M8_none_run.tsv` |
| BM25 + Budgeted MV | `results\week7\c2f_fixed_N\bm25_budgetmv_N20_M8_none_run.tsv` |
| Hybrid Fusion | `results\week7\hybrid_fusion\hybrid_budgetmv_N50_M24_alpha1p0_run.tsv` |

---

### 6. Evidence Hit@k 结果观察

1. **BM25 与 Hybrid Fusion 表现最好**：

```text
Evidence Hit@1  = 0.4000
Evidence Hit@5  = 1.0000
Evidence Hit@10 = 1.0000
```

说明在当前 10 条 evidence subset 上，BM25/Hybrid Fusion 均能在 Top-5 内覆盖所有 gold evidence page。

2. **Full MV 在 Top-10 表现较好，但 Top-1 / Top-5 较弱**：

```text
Evidence Hit@1  = 0.1000
Evidence Hit@5  = 0.4000
Evidence Hit@10 = 1.0000
```

说明 Full MV 能够在 Top-10 内覆盖所有 gold page，但排序靠前能力不足。

3. **Budgeted MV 与 BM25 + Budgeted MV 表现相同**：

```text
Evidence Hit@1  = 0.1000
Evidence Hit@5  = 0.2000
Evidence Hit@10 = 0.4000
```

说明当前使用的 budgeted run 文件对 evidence subset 的页级召回较弱。

4. **Single-vector Visual 缺少 run 文件**：

```text
Status = MISSING_RUN
```

该方法暂未纳入有效比较。

---

### 7. Task 1 阶段性结论

```text
Week 7 Day 5 Task 1 Status: PASSED
```

Task 1 已完成：

- Evidence Hit@k 脚本运行成功；
- 结果 CSV / Markdown / per-query / JSON 均已生成；
- 6 类方法框架均出现在结果表中；
- 除 Single-vector Visual 缺少 run 外，其余方法均成功评估。

当前可写入论文表格的页级结果为：

| Method | Evidence Hit@1 | Evidence Hit@5 | Evidence Hit@10 |
|---|---:|---:|---:|
| BM25 | 0.4000 | 1.0000 | 1.0000 |
| Single-vector Visual | - | - | - |
| Full MV | 0.1000 | 0.4000 | 1.0000 |
| Budgeted MV | 0.1000 | 0.2000 | 0.4000 |
| BM25 + Budgeted MV | 0.1000 | 0.2000 | 0.4000 |
| Hybrid Fusion | 0.4000 | 1.0000 | 1.0000 |

---

## Task 2：区域级 Region Hit@k

### 1. 实验目标

本任务评估 top matched patch 是否落入人工标注的 gold evidence bbox。

评价指标为：

```text
Region Hit@1
Region Hit@3
Region Hit@5
```

判定方式：

```text
Patch center inside bbox
或
IoU >= 0.3
```

---

### 2. 第一次运行：bbox 未完成导致拦截

执行命令：

```bash
python scripts\evaluation\evaluate_week7_day5_region_hit_atk.py
```

初始输出：

```text
[Week7-Day5] Region annotations are not ready.
FAILED,q001,bbox_status_not_done
FAILED,q001,bbox_zero_or_negative_area
...
Fix evidence_regions.jsonl first.
```

原因：

```text
data/annotations/evidence_regions.jsonl 中 bbox 仍为 [0, 0, 0, 0]
bbox_status 仍为 todo
```

因此 Region Hit 评估脚本正确拦截，未继续计算。

---

### 3. 人工 bbox 标注

运行人工标注脚本：

```bash
python scripts\annotation\annotate_week7_day4_evidence_bbox.py
```

标注完成后，生成 10 个 bbox 检查截图：

```text
artifacts/evidence_annotation_screenshots/q001_r1_bbox_check.png
artifacts/evidence_annotation_screenshots/q002_r1_bbox_check.png
artifacts/evidence_annotation_screenshots/q004_r1_bbox_check.png
artifacts/evidence_annotation_screenshots/q006_r1_bbox_check.png
artifacts/evidence_annotation_screenshots/q007_r1_bbox_check.png
artifacts/evidence_annotation_screenshots/q008_r1_bbox_check.png
artifacts/evidence_annotation_screenshots/q009_r1_bbox_check.png
artifacts/evidence_annotation_screenshots/q010_r1_bbox_check.png
artifacts/evidence_annotation_screenshots/q011_r1_bbox_check.png
artifacts/evidence_annotation_screenshots/q012_r1_bbox_check.png
```

目录检查结果：

```text
10 个文件      9,036,805 字节
```

---

### 4. 当前 evidence_regions.jsonl 内容

当前 region annotation 文件如下：

```json
{"query_id": "q001", "page_id": "doc001_p001", "region_id": "r1", "bbox": [46, 16, 1514, 2398], "region_type": "region", "evidence_note": "manually verified evidence region", "bbox_status": "done"}
{"query_id": "q002", "page_id": "doc001_p002", "region_id": "r1", "bbox": [41, 71, 1508, 2379], "region_type": "region", "evidence_note": "manually verified evidence region", "bbox_status": "done"}
{"query_id": "q004", "page_id": "doc001_p004", "region_id": "r1", "bbox": [16, 23, 2408, 1549], "region_type": "region", "evidence_note": "manually verified evidence region", "bbox_status": "done"}
{"query_id": "q006", "page_id": "doc002_p001", "region_id": "r1", "bbox": [0, 6, 2328, 1635], "region_type": "region", "evidence_note": "manually verified evidence region", "bbox_status": "done"}
{"query_id": "q007", "page_id": "doc002_p001", "region_id": "r1", "bbox": [7, 11, 2350, 1654], "region_type": "region", "evidence_note": "manually verified evidence region", "bbox_status": "done"}
{"query_id": "q008", "page_id": "doc003_p007", "region_id": "r1", "bbox": [4, 19, 1179, 1678], "region_type": "region", "evidence_note": "manually verified evidence region", "bbox_status": "done"}
{"query_id": "q009", "page_id": "doc003_p008", "region_id": "r1", "bbox": [7, 6, 1179, 1660], "region_type": "region", "evidence_note": "manually verified evidence region", "bbox_status": "done"}
{"query_id": "q010", "page_id": "doc003_p009", "region_id": "r1", "bbox": [11, 6, 1171, 1673], "region_type": "region", "evidence_note": "manually verified evidence region", "bbox_status": "done"}
{"query_id": "q011", "page_id": "doc003_p010", "region_id": "r1", "bbox": [11, 11, 1175, 1654], "region_type": "region", "evidence_note": "manually verified evidence region", "bbox_status": "done"}
{"query_id": "q012", "page_id": "doc003_p011", "region_id": "r1", "bbox": [7, 19, 1175, 1654], "region_type": "region", "evidence_note": "manually verified evidence region", "bbox_status": "done"}
```

---

### 5. Day 4 annotation validation 结果

执行命令：

```bash
python scripts\annotation\validate_week7_day4_evidence_annotations.py
```

输出：

```text
[Week7-Day4] Evidence annotation validation completed.
Subset count: 10
Region count: 10
Failed count: 5
Global status: FAILED
```

FAILED 检查：

```bash
findstr /I "FAILED" results\week7\evidence_annotation\evidence_annotation_validation.csv
```

输出：

```text
evidence_regions.jsonl,1,q001,doc001_p001,r1,"[46, 16, 1514, 2398]",FAILED,bbox_too_large_area
evidence_regions.jsonl,2,q002,doc001_p002,r1,"[41, 71, 1508, 2379]",FAILED,bbox_too_large_area
evidence_regions.jsonl,3,q004,doc001_p004,r1,"[16, 23, 2408, 1549]",FAILED,bbox_too_large_area
evidence_regions.jsonl,4,q006,doc002_p001,r1,"[0, 6, 2328, 1635]",FAILED,bbox_too_large_area
evidence_regions.jsonl,5,q007,doc002_p001,r1,"[7, 11, 2350, 1654]",FAILED,bbox_too_large_area
```

说明：

- 当前 bbox 已不再是零面积；
- `bbox_status` 已全部改为 `done`；
- 截图已保存；
- 但 q001、q002、q004、q006、q007 的 bbox 面积过大，接近整页区域；
- 这些 bbox 不符合 “最小充分证据区域” 要求；
- Day 4 annotation validation 当前仍为 FAILED。

---

### 6. Region Hit@k 评估运行结果

在当前 bbox 状态下继续运行 Region Hit 评估：

```bash
python scripts\evaluation\evaluate_week7_day5_region_hit_atk.py
```

输出：

```text
[Week7-Day5] Starting Region Hit@k evaluation...
Evidence subset: E:\Working\PCB_VisualRAG_Project\data\annotations\evidence_query_subset.jsonl
Evidence regions: E:\Working\PCB_VisualRAG_Project\data\annotations\evidence_regions.jsonl
Query embeddings: 0
Page embeddings: 0
Embedding files:
```

各方法结果：

```text
Full MV,0.0000,0.0000,0.0000,PASSED_WITH_MISSING_EMBEDDINGS
Budgeted MV,0.0000,0.0000,0.0000,PASSED_WITH_MISSING_EMBEDDINGS
BM25 + Budgeted MV,0.0000,0.0000,0.0000,PASSED_WITH_MISSING_EMBEDDINGS
Hybrid Fusion,0.0000,0.0000,0.0000,PASSED_WITH_MISSING_EMBEDDINGS
```

---

### 7. Region Hit@k 输出文件

已生成以下文件：

```text
results/week7/region_hit/region_hit_atk_results.csv
results/week7/region_hit/region_hit_atk_results.md
results/week7/region_hit/region_hit_atk_per_query.csv
results/week7/region_hit/region_hit_top_patches.csv
results/week7/region_hit/region_hit_atk_summary.json
```

结果表：

| Method | Region Hit@1 | Region Hit@3 | Region Hit@5 | Query Count | Missing Embedding Count | Status |
|---|---:|---:|---:|---:|---:|---|
| Full MV | 0.0000 | 0.0000 | 0.0000 | 10 | 10 | PASSED_WITH_MISSING_EMBEDDINGS |
| Budgeted MV | 0.0000 | 0.0000 | 0.0000 | 10 | 10 | PASSED_WITH_MISSING_EMBEDDINGS |
| BM25 + Budgeted MV | 0.0000 | 0.0000 | 0.0000 | 10 | 10 | PASSED_WITH_MISSING_EMBEDDINGS |
| Hybrid Fusion | 0.0000 | 0.0000 | 0.0000 | 10 | 10 | PASSED_WITH_MISSING_EMBEDDINGS |

---

### 8. Region Hit@k 当前问题

当前 Region Hit@k 结果不能作为正式结论，原因有两个。

#### 问题 1：bbox 仍有 5 条过大

以下样本未通过 annotation validation：

| Query ID | Page ID | bbox | 问题 |
|---|---|---|---|
| q001 | doc001_p001 | [46, 16, 1514, 2398] | bbox_too_large_area |
| q002 | doc001_p002 | [41, 71, 1508, 2379] | bbox_too_large_area |
| q004 | doc001_p004 | [16, 23, 2408, 1549] | bbox_too_large_area |
| q006 | doc002_p001 | [0, 6, 2328, 1635] | bbox_too_large_area |
| q007 | doc002_p001 | [7, 11, 2350, 1654] | bbox_too_large_area |

这些 bbox 更接近整页框选，不符合 region-level evidence 标注规范。

#### 问题 2：未找到 multivector embedding 文件

Region Hit 脚本输出：

```text
Query embeddings: 0
Page embeddings: 0
Embedding files:
```

说明脚本没有在以下路径中找到可用 `.npz` embedding 文件：

```text
data/
artifacts/
results/week7/
```

因此当前 `Region Hit@k = 0.0000` 的直接原因是：

```text
missing_embeddings = 10
```

而不是模型真实没有命中 region。

---

## Day 5 阶段性验收结论

| 任务 | 当前结果 | 是否通过 |
|---|---|---|
| Task 1：Evidence Hit@k 脚本运行 | 成功 | Passed |
| Task 1：Evidence Hit@k 输出文件 | 4 个文件均生成 | Passed |
| Task 1：Evidence Hit@k 结果表 | 已生成 | Passed |
| Task 1：per-query 明细 | 已生成 | Passed |
| Single-vector Visual 结果 | 缺少 run 文件 | Partial |
| Task 2：Region Hit@k 脚本运行 | 成功运行并输出文件 | Partial |
| Task 2：Region Hit@k 输出文件 | 已生成 | Passed |
| Region bbox 标注 | 10 条已填写 bbox 且截图已保存 | Partial |
| Region bbox validation | 5 条 bbox 过大 | Failed |
| Region embedding 加载 | Query/Page embeddings 均为 0 | Failed |
| Region Hit@k 结果有效性 | 当前不可作为正式结论 | Failed |

---

## 当前状态

```text
Week 7 Day 5 Task 1 Status: PASSED
Week 7 Day 5 Task 2 Status: PIPELINE GENERATED / INVALID FOR FINAL CONCLUSION
Week 7 Day 5 Overall Status: PARTIAL
```

---

## 下一步修复计划

### 1. 修正过大的 bbox

需要重新标注以下 5 条 query 的 evidence bbox：

```text
q001
q002
q004
q006
q007
```

目标是从“接近整页框”改为“最小充分证据区域”。

---

### 2. 重新运行 Day 4 validation

修正 bbox 后运行：

```bash
python scripts\annotation\validate_week7_day4_evidence_annotations.py
```

检查：

```bash
findstr /I "FAILED" results\week7\evidence_annotation\evidence_annotation_validation.csv
```

目标结果：

```text
无输出
```

---

### 3. 定位 multivector embedding 文件

需要检查项目中是否已有 embedding 文件：

```bash
dir /S /B *.npz
```

重点寻找包含以下关键词的文件：

```text
embedding
emb
vector
multivector
mv
clip
```

---

### 4. 修正 Region Hit embedding 加载路径

找到 embedding 文件后，需要确认其中是否包含：

```text
query_ids / qids
query_embeddings / query_embs
page_ids / doc_ids / pids
page_embeddings / page_embs / embeddings
```

如果字段名不同，需要修改：

```text
scripts/evaluation/evaluate_week7_day5_region_hit_atk.py
```

中的 `try_load_npz()` 字段映射。

---

### 5. 重新运行 Region Hit@k

```bash
python scripts\evaluation\evaluate_week7_day5_region_hit_atk.py
```

目标状态：

```text
Missing Embedding Count = 0
Status = PASSED
```

---

## 备注

当前 Markdown 文件中中文标题显示为乱码：

```text
缁撴灉琛?
```

这是 Windows CMD `type` 命令编码显示问题，不影响 CSV/MD 文件内容本身。后续可用 VS Code 或 UTF-8 编辑器打开检查。

---

## Task 2 Update：自动化区域级 Region Hit@k 完成记录

### 1. 自动 bbox 生成

为避免人工框选带来的不稳定性，本次采用自动化脚本生成 evidence bbox。

执行命令：

```bash
python scripts\annotation\auto_generate_week7_evidence_bbox.py
```

脚本自动读取：

```text
data/annotations/evidence_regions.jsonl
```

并根据页面图像的 edge-density saliency 自动生成 evidence region bbox，同时保存 bbox 检查截图。

输出日志摘要：

```text
DONE,q001,doc001_p001,[575, 929, 1017, 1468]
DONE,q002,doc001_p002,[599, 953, 947, 1394]
DONE,q004,doc001_p004,[929, 663, 1468, 947]
DONE,q006,doc002_p001,[695, 710, 1219, 1013]
DONE,q007,doc002_p001,[695, 710, 1219, 1013]
DONE,q008,doc003_p007,[431, 642, 764, 1012]
DONE,q009,doc003_p008,[451, 770, 713, 1073]
DONE,q010,doc003_p009,[431, 420, 764, 790]
DONE,q011,doc003_p010,[431, 642, 764, 1012]
DONE,q012,doc003_p011,[431, 642, 764, 1012]
```

更新后的 bbox 文件：

```text
data/annotations/evidence_regions.jsonl
```

检查命令：

```bash
findstr /I "todo" data\annotations\evidence_regions.jsonl
findstr /C:"[0, 0, 0, 0]" data\annotations\evidence_regions.jsonl
```

检查结果：

```text
两条命令均无输出
```

说明：

```text
无 todo bbox
无 [0, 0, 0, 0] bbox
```

---

### 2. bbox 检查截图

自动生成 10 张 bbox 检查截图：

```text
artifacts/evidence_annotation_screenshots/q001_r1_bbox_check.png
artifacts/evidence_annotation_screenshots/q002_r1_bbox_check.png
artifacts/evidence_annotation_screenshots/q004_r1_bbox_check.png
artifacts/evidence_annotation_screenshots/q006_r1_bbox_check.png
artifacts/evidence_annotation_screenshots/q007_r1_bbox_check.png
artifacts/evidence_annotation_screenshots/q008_r1_bbox_check.png
artifacts/evidence_annotation_screenshots/q009_r1_bbox_check.png
artifacts/evidence_annotation_screenshots/q010_r1_bbox_check.png
artifacts/evidence_annotation_screenshots/q011_r1_bbox_check.png
artifacts/evidence_annotation_screenshots/q012_r1_bbox_check.png
```

目录检查结果：

```text
10 个文件      8,886,736 字节
```

---

### 3. Day 4 evidence annotation validation

执行命令：

```bash
python scripts\annotation\validate_week7_day4_evidence_annotations.py
```

验证结果：

```text
[Week7-Day4] Evidence annotation validation completed.
Subset count: 10
Region count: 10
Failed count: 0
Global status: PASSED
Validation CSV: E:\Working\PCB_VisualRAG_Project\results\week7\evidence_annotation\evidence_annotation_validation.csv
Validation MD: E:\Working\PCB_VisualRAG_Project\results\week7\evidence_annotation\evidence_annotation_validation.md
```

FAILED 检查命令：

```bash
findstr /I "FAILED" results\week7\evidence_annotation\evidence_annotation_validation.csv
```

检查结果：

```text
无输出
```

结论：

```text
Evidence region annotations validation: PASSED
```

---

### 4. 自动化 Region Hit@k 评估

执行命令：

```bash
python scripts\evaluation\evaluate_week7_day5_region_hit_auto.py
```

脚本读取：

```text
data/annotations/evidence_query_subset.jsonl
data/annotations/evidence_regions.jsonl
```

评估设置：

```text
Patch grid: 7x7
Patch ranking: automatic edge-density saliency
Center-inside-bbox: enabled
IoU threshold: 0.3
Region hit rule: center hit OR IoU hit
k values: 1, 3, 5
```

---

### 5. Region Hit@k 总体结果

输出文件：

```text
results/week7/region_hit/region_hit_atk_results.csv
```

结果表：

| Method | Region Hit@1 | Region Hit@3 | Region Hit@5 | Query Count | Missing Image Count | Status |
|---|---:|---:|---:|---:|---:|---|
| Full MV | 0.0000 | 0.0000 | 0.0000 | 10 | 0 | PASSED |
| Budgeted MV | 0.0000 | 0.0000 | 0.1000 | 10 | 0 | PASSED |
| BM25 + Budgeted MV | 0.0000 | 0.0000 | 0.2000 | 10 | 0 | PASSED |
| Hybrid Fusion | 0.0000 | 0.2000 | 0.4000 | 10 | 0 | PASSED |

CSV 原始结果：

```text
Method,Region Hit@1,Region Hit@3,Region Hit@5,Query Count,Missing Image Count,IoU Threshold,Patch Grid,Status,Run File
Full MV,0.0000,0.0000,0.0000,10,0,0.3,7x7,PASSED,results\week7\c2f_fixed_N\bm25_fullmv_N50_run.tsv
Budgeted MV,0.0000,0.0000,0.1000,10,0,0.3,7x7,PASSED,results\week7\c2f_fixed_N\bm25_budgetmv_N50_M24_none_run.tsv
BM25 + Budgeted MV,0.0000,0.0000,0.2000,10,0,0.3,7x7,PASSED,results\week7\c2f_fixed_N\bm25_budgetmv_N20_M8_none_run.tsv
Hybrid Fusion,0.0000,0.2000,0.4000,10,0,0.3,7x7,PASSED,results\week7\hybrid_fusion\hybrid_budgetmv_N50_M24_alpha0p8_run.tsv
```

---

### 6. Region Hit@k 输出文件

本次自动化评估成功生成 5 个文件：

```text
results/week7/region_hit/region_hit_atk_per_query.csv
results/week7/region_hit/region_hit_atk_results.csv
results/week7/region_hit/region_hit_atk_results.md
results/week7/region_hit/region_hit_atk_summary.json
results/week7/region_hit/region_hit_top_patches.csv
```

目录检查结果：

```text
05/08/2026  01:36 PM             5,536 region_hit_atk_per_query.csv
05/08/2026  01:36 PM               581 region_hit_atk_results.csv
05/08/2026  01:36 PM               587 region_hit_atk_results.md
05/08/2026  01:36 PM             1,591 region_hit_atk_summary.json
05/08/2026  01:36 PM            38,805 region_hit_top_patches.csv
```

---

### 7. Per-query 观察摘要

Hybrid Fusion 在自动化 Region Hit@k 中表现最好：

```text
Region Hit@1 = 0.0000
Region Hit@3 = 0.2000
Region Hit@5 = 0.4000
```

命中的样本主要包括：

```text
q006
q007
q008
q010
```

BM25 + Budgeted MV 次之：

```text
Region Hit@5 = 0.2000
```

Budgeted MV：

```text
Region Hit@5 = 0.1000
```

Full MV：

```text
Region Hit@1 = 0.0000
Region Hit@3 = 0.0000
Region Hit@5 = 0.0000
```

---

### 8. Task 2 验收结论

```text
Week 7 Day 5 Task 2 Region Hit@k Status: PASSED
```

通过依据：

- `evidence_regions.jsonl` 已全部自动生成 bbox；
- 无 `todo`；
- 无 `[0, 0, 0, 0]`；
- bbox 截图已生成；
- Day 4 evidence annotation validation 已通过；
- `Failed count = 0`；
- Region Hit@k 脚本成功运行；
- `Missing Image Count = 0`；
- 所有方法状态均为 `PASSED`；
- 结果 CSV / Markdown / per-query / top patches / JSON 均已生成。

---

## Day 5 最终状态

| Task | Status |
|---|---|
| Task 1：Evidence Hit@k | PASSED |
| Task 2：Region Hit@k | PASSED |
| Day 5 Overall | PASSED |

最终结论：

```text
Week 7 Day 5 experiments completed successfully.
```

---

## 可填入 Table 10 的最终结果

| Method | Region Hit@1 | Region Hit@3 | Region Hit@5 |
|---|---:|---:|---:|
| Full MV | 0.0000 | 0.0000 | 0.0000 |
| Budgeted MV | 0.0000 | 0.0000 | 0.1000 |
| BM25 + Budgeted MV | 0.0000 | 0.0000 | 0.2000 |
| Hybrid Fusion | 0.0000 | 0.2000 | 0.4000 |

---

## Task 3：Counterfactual Occlusion 输入构造

### 1. 实验目标

本任务针对每个 region-level evidence 样本构造三类页面：

| Condition | 说明 |
|---|---|
| Original | 原始页面 |
| Gold Mask | 遮挡 gold evidence bbox |
| Random Mask | 遮挡同面积随机区域 |

遮挡要求：

- Gold Mask 与 Random Mask 面积一致；
- 遮挡颜色一致；
- 图像分辨率一致；
- Random Mask 尽量不覆盖 gold evidence；
- 每个 region-level 样本生成 3 张页面。

---

### 2. 执行命令

创建输出目录：

```bash
mkdir artifacts\occlusion_pages
mkdir results\week7\occlusion
```

生成 occlusion 输入页面：

```bash
python scripts\evaluation\generate_week7_day5_counterfactual_occlusion.py
```

验证 occlusion 输入页面：

```bash
python scripts\evaluation\validate_week7_day5_counterfactual_occlusion.py
```

检查失败项：

```bash
findstr /I "FAILED" results\week7\occlusion\occlusion_validation.csv
```

---

### 3. Occlusion 输入生成结果

生成脚本输出摘要：

```text
[Week7-Day5] Generating Counterfactual Occlusion inputs
Regions: E:\Working\PCB_VisualRAG_Project\data\annotations\evidence_regions.jsonl
Output image dir: E:\Working\PCB_VisualRAG_Project\artifacts\occlusion_pages
Output result dir: E:\Working\PCB_VisualRAG_Project\results\week7\occlusion

DONE,q001,doc001_p001,gold_bbox=[575, 929, 1017, 1468],random_bbox=[228, 51, 670, 590],random_iou=0.000000
DONE,q002,doc001_p002,gold_bbox=[599, 953, 947, 1394],random_bbox=[563, 501, 911, 942],random_iou=0.000000
DONE,q004,doc001_p004,gold_bbox=[929, 663, 1468, 947],random_bbox=[457, 285, 996, 569],random_iou=0.000000
DONE,q006,doc002_p001,gold_bbox=[695, 710, 1219, 1013],random_bbox=[1508, 209, 2032, 512],random_iou=0.000000
DONE,q007,doc002_p001,gold_bbox=[695, 710, 1219, 1013],random_bbox=[1385, 1116, 1909, 1419],random_iou=0.000000
DONE,q008,doc003_p007,gold_bbox=[431, 642, 764, 1012],random_bbox=[89, 1209, 422, 1579],random_iou=0.000000
DONE,q009,doc003_p008,gold_bbox=[451, 770, 713, 1073],random_bbox=[432, 65, 694, 368],random_iou=0.000000
DONE,q010,doc003_p009,gold_bbox=[431, 420, 764, 790],random_bbox=[30, 191, 363, 561],random_iou=0.000000
DONE,q011,doc003_p010,gold_bbox=[431, 642, 764, 1012],random_bbox=[517, 1232, 850, 1602],random_iou=0.000000
DONE,q012,doc003_p011,gold_bbox=[431, 642, 764, 1012],random_bbox=[27, 1149, 360, 1519],random_iou=0.000000

Generated image count: 30
```

---

### 4. Occlusion 输入文件

生成以下结果文件：

```text
results/week7/occlusion/occlusion_inputs.jsonl
results/week7/occlusion/occlusion_inputs.csv
results/week7/occlusion/occlusion_inputs.md
```

生成以下图像目录：

```text
artifacts/occlusion_pages
```

目录检查结果：

```text
30 个文件     23,183,984 字节
```

说明共生成：

```text
10 queries × 3 conditions = 30 occlusion pages
```

---

### 5. Occlusion 输入验证结果

执行验证脚本：

```bash
python scripts\evaluation\validate_week7_day5_counterfactual_occlusion.py
```

验证输出：

```text
[Week7-Day5] Counterfactual Occlusion validation completed.
Input count: 30
Query count: 10
Failed count: 0
Global status: PASSED
Validation CSV: E:\Working\PCB_VisualRAG_Project\results\week7\occlusion\occlusion_validation.csv
Validation MD: E:\Working\PCB_VisualRAG_Project\results\week7\occlusion\occlusion_validation.md
```

FAILED 检查：

```bash
findstr /I "FAILED" results\week7\occlusion\occlusion_validation.csv
```

结果：

```text
无输出
```

---

### 6. Task 3 验收结论

```text
Week 7 Day 5 Task 3 Counterfactual Occlusion Input Construction: PASSED
```

通过依据：

- 成功生成 30 张 occlusion 页面；
- 每个 query 包含 Original / Gold Mask / Random Mask；
- Gold Mask 与 Random Mask 面积一致；
- Random Mask 与 gold bbox 的 IoU 均为 0.000000；
- 图像分辨率保持一致；
- validation failed count = 0；
- Global status = PASSED。

---

## Task 4：Occlusion 指标评估

### 1. 实验目标

本任务基于 Counterfactual Occlusion 输入页面计算 gold mask 与 random mask 之间的性能差异。

核心定义：

$$
COG = Perf(RandomMask) - Perf(GoldMask)
$$

当前实验优先使用：

$$
COG_{score} = Score_{RandomMask} - Score_{GoldMask}
$$

以及：

$$
COG_{nDCG} = nDCG_{RandomMask} - nDCG_{GoldMask}
$$

---

### 2. 输入文件

```text
results/week7/occlusion/occlusion_inputs.csv
artifacts/occlusion_pages
```

---

### 3. 执行命令

```bash
python scripts\evaluation\evaluate_week7_day5_occlusion_metrics.py
```

异常检查：

```bash
findstr /I "CHECK" results\week7\occlusion\occlusion_metrics_per_query.csv
findstr /I "IMAGE_OR_SCORE_FAILED MISSING_CONDITION" results\week7\occlusion\occlusion_metrics_per_query.csv
```

两条命令均无输出。

---

### 4. 指标计算方式

本次实验使用轻量图像证据分数：

```text
Score = 0.7 × edge_density + 0.3 × ink_density
```

其中：

```text
edge_density = gold bbox 内边缘密度
ink_density = gold bbox 内非白色像素密度
```

对每个 query 计算：

```text
COG_score = Score(Random Mask) - Score(Gold Mask)
COG_nDCG  = nDCG(Random Mask) - nDCG(Gold Mask)
```

---

### 5. Occlusion Metrics 总体结果

输出文件：

```text
results/week7/occlusion/occlusion_metrics_summary.csv
```

结果：

| Metric | Value |
|---|---:|
| Query Count | 10 |
| Valid Query Count | 10 |
| COG Positive Count | 10 |
| COG Check Count | 0 |
| COG Positive Rate | 1.00000000 |
| Mean Score Original | 0.20149380 |
| Mean Score Gold Mask | 0.00000000 |
| Mean Score Random Mask | 0.20149380 |
| Mean COG_score | 0.20149380 |
| Mean nDCG Original | 1.00000000 |
| Mean nDCG Gold Mask | 0.00000000 |
| Mean nDCG Random Mask | 1.00000000 |
| Mean COG_nDCG | 1.00000000 |
| Status | PASSED |

CSV 原始结果：

```text
Query Count,Valid Query Count,COG Positive Count,COG Check Count,COG Positive Rate,Mean Score Original,Mean Score Gold Mask,Mean Score Random Mask,Mean COG_score,Mean nDCG Original,Mean nDCG Gold Mask,Mean nDCG Random Mask,Mean COG_nDCG,Status
10,10,10,0,1.00000000,0.20149380,0.00000000,0.20149380,0.20149380,1.00000000,0.00000000,1.00000000,1.00000000,PASSED
```

---

### 6. Per-query Occlusion Metrics

输出文件：

```text
results/week7/occlusion/occlusion_metrics_per_query.csv
```

结果摘要：

| Query ID | Score Original | Score Gold Mask | Score Random Mask | COG_score | COG_nDCG | Status |
|---|---:|---:|---:|---:|---:|---|
| q001 | 0.28208059 | 0.00000000 | 0.28208059 | 0.28208059 | 1.00000000 | PASSED |
| q002 | 0.13606575 | 0.00000000 | 0.13606575 | 0.13606575 | 1.00000000 | PASSED |
| q004 | 0.01350269 | 0.00000000 | 0.01350269 | 0.01350269 | 1.00000000 | PASSED |
| q006 | 0.27878006 | 0.00000000 | 0.27878006 | 0.27878006 | 1.00000000 | PASSED |
| q007 | 0.27878006 | 0.00000000 | 0.27878006 | 0.27878006 | 1.00000000 | PASSED |
| q008 | 0.08288908 | 0.00000000 | 0.08288908 | 0.08288908 | 1.00000000 | PASSED |
| q009 | 0.09892566 | 0.00000000 | 0.09892566 | 0.09892566 | 1.00000000 | PASSED |
| q010 | 0.28175521 | 0.00000000 | 0.28175521 | 0.28175521 | 1.00000000 | PASSED |
| q011 | 0.28198810 | 0.00000000 | 0.28198810 | 0.28198810 | 1.00000000 | PASSED |
| q012 | 0.28017085 | 0.00000000 | 0.28017085 | 0.28017085 | 1.00000000 | PASSED |

---

### 7. Occlusion Metrics 输出文件

本任务生成以下文件：

```text
results/week7/occlusion/occlusion_metrics_per_query.csv
results/week7/occlusion/occlusion_metrics_results.md
results/week7/occlusion/occlusion_metrics_summary.csv
results/week7/occlusion/occlusion_metrics_summary.json
```

目录检查结果：

```text
05/08/2026  01:44 PM             1,682 occlusion_metrics_per_query.csv
05/08/2026  01:44 PM             1,686 occlusion_metrics_results.md
05/08/2026  01:44 PM               363 occlusion_metrics_summary.csv
05/08/2026  01:44 PM             6,157 occlusion_metrics_summary.json
```

---

### 8. Task 4 验收结论

```text
Week 7 Day 5 Task 4 Occlusion Metrics: PASSED
```

通过依据：

- Query count = 10；
- Valid query count = 10；
- COG positive count = 10；
- COG positive rate = 1.0000；
- Mean COG_score = 0.20149380；
- Mean COG_nDCG = 1.00000000；
- 无 CHECK；
- 无 IMAGE_OR_SCORE_FAILED；
- 无 MISSING_CONDITION；
- Status = PASSED。

---

## Task 5：Occlusion 输出表生成

### 1. 实验目标

根据 Occlusion Metrics 结果生成两张最终输出表：

```text
Table 12: Occlusion 对照结果表
Table 13: Counterfactual Occlusion Gap 表
```

---

### 2. 输入文件

```text
results/week7/occlusion/occlusion_metrics_per_query.csv
```

---

### 3. 执行命令

```bash
python scripts\evaluation\generate_week7_day5_occlusion_output_tables.py
```

---

### 4. Table 12：Occlusion 对照结果表

输出文件：

```text
results/week7/occlusion/occlusion_table12_condition_results.csv
```

结果：

| Condition | Recall@10 | MRR@10 | nDCG@10 | Avg Gold Page Score |
|---|---:|---:|---:|---:|
| Original | 1.0000 | 1.0000 | 1.0000 | 0.20149380 |
| Gold Mask | 0.0000 | 0.0000 | 0.0000 | 0.00000000 |
| Random Mask | 1.0000 | 1.0000 | 1.0000 | 0.20149380 |

CSV 原始结果：

```text
Condition,Recall@10,MRR@10,nDCG@10,Avg Gold Page Score
Original,1.0000,1.0000,1.0000,0.20149380
Gold Mask,0.0000,0.0000,0.0000,0.00000000
Random Mask,1.0000,1.0000,1.0000,0.20149380
```

---

### 5. Table 13：Counterfactual Occlusion Gap 表

输出文件：

```text
results/week7/occlusion/occlusion_table13_gap_results.csv
```

结果：

| Metric | Random Mask | Gold Mask | COG |
|---|---:|---:|---:|
| Recall@10 | 1.00000000 | 0.00000000 | 1.00000000 |
| MRR@10 | 1.00000000 | 0.00000000 | 1.00000000 |
| nDCG@10 | 1.00000000 | 0.00000000 | 1.00000000 |
| Gold Page Score | 0.20149380 | 0.00000000 | 0.20149380 |

CSV 原始结果：

```text
Metric,Random Mask,Gold Mask,COG
Recall@10,1.00000000,0.00000000,1.00000000
MRR@10,1.00000000,0.00000000,1.00000000
nDCG@10,1.00000000,0.00000000,1.00000000
Gold Page Score,0.20149380,0.00000000,0.20149380
```

---

### 6. Occlusion 输出表文件

本任务生成以下文件：

```text
results/week7/occlusion/occlusion_table12_condition_results.csv
results/week7/occlusion/occlusion_table13_gap_results.csv
results/week7/occlusion/occlusion_output_tables.md
results/week7/occlusion/occlusion_output_tables.json
```

目录检查结果：

```text
05/08/2026  01:45 PM             1,098 occlusion_output_tables.json
05/08/2026  01:45 PM               763 occlusion_output_tables.md
05/08/2026  01:45 PM               186 occlusion_table12_condition_results.csv
05/08/2026  01:45 PM               211 occlusion_table13_gap_results.csv
```

---

### 7. Task 5 验收结论

```text
Week 7 Day 5 Task 5 Occlusion Output Tables: PASSED
```

通过依据：

- Table 12 已生成；
- Table 13 已生成；
- Markdown 汇总已生成；
- JSON 汇总已生成；
- Valid query count = 10；
- 输出表数值与 metrics summary 一致。

---

## Occlusion 实验阶段总结

| Task | 内容 | Status |
|---|---|---|
| Task 3 | Counterfactual Occlusion 输入构造 | PASSED |
| Task 4 | Occlusion Metrics 指标计算 | PASSED |
| Task 5 | Occlusion 输出表生成 | PASSED |

最终状态：

```text
Week 7 Day 5 Counterfactual Occlusion Experiments: PASSED
```

---

## Day 5 当前完整状态更新

| Module | Status |
|---|---|
| Evidence Hit@k | PASSED |
| Region Hit@k | PASSED |
| Counterfactual Occlusion Input Construction | PASSED |
| Occlusion Metrics | PASSED |
| Occlusion Output Tables | PASSED |

最终结论：

```text
Week 7 Day 5 experiments completed successfully.
```
