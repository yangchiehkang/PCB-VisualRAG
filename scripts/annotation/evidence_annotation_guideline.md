# Evidence Region Annotation Guideline

## 输出文件

- `data/annotations/evidence_query_subset.jsonl`
- `data/annotations/evidence_regions.jsonl`

## bbox 格式

```text
[x1, y1, x2, y2]
标注规则
每条 query 至少标注 1 个 evidence region。
bbox 必须框住最小充分证据区域。
不允许大面积框整页。
表格类 query 优先框具体单元格或单元格邻域。
图例/结构类 query 优先框局部 legend、symbol、走线、结构块。
元件定位类 query 优先框具体元件、焊盘、标号或局部 PCB 区域。
similarity_based_interference 可作为失败案例，但 bbox 仍需指向最可能相关的局部区域。
cross_page_consistency 证据分散，除非区域非常明确，否则不优先使用。
坐标必须来自 gold page 图像原始像素坐标。
标注完成后，将 bbox_status 从 todo 改为 done。
evidence_regions.jsonl 格式
复制
{
  "query_id": "q001",
  "page_id": "doc001_p001",
  "region_id": "r1",
  "bbox": [120, 340, 420, 510],
  "region_type": "table_cell",
  "evidence_note": "minimum drill size value",
  "bbox_status": "done"
}
验收标准
样本数为 8–12 条。
每条样本都有 gold page。
每条样本都有明确 bbox。
bbox 不能是 [0, 0, 0, 0]。
bbox 不能大面积框整页。
每条样本保存一张检查截图。
复制

---

## 5. 手工标注 bbox

打开待标注文件：

```bash
notepad data\annotations\evidence_regions.jsonl
把每一行里的：

复制
"bbox": [0, 0, 0, 0]
改成真实 bbox，例如：

复制
"bbox": [120, 340, 420, 510]
把：

复制
"evidence_note": "TODO"
改成简短证据说明，例如：

复制
"evidence_note": "minimum drill size value"
把：

复制
"bbox_status": "todo"
改成：

复制
"bbox_status": "done"
6. 保存 bbox 检查截图
截图保存目录：

复制
artifacts\evidence_annotation_screenshots
建议命名：

复制
q001_r1_bbox_check.png
q002_r1_bbox_check.png
q003_r1_bbox_check.png
q004_r1_bbox_check.png
q005_r1_bbox_check.png
q006_r1_bbox_check.png
q007_r1_bbox_check.png
q008_r1_bbox_check.png
q009_r1_bbox_check.png
q010_r1_bbox_check.png