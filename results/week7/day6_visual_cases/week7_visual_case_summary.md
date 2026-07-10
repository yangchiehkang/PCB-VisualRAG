# Week 7 可视化案例图

## Table 18: Week 7 可视化案例类型

| 案例类型 | 数量 | 作用 |
|---|---:|---|
| Gold mask 后明显掉分 | 2 | 支撑证据依赖 |
| Random mask 影响较小 | 1 | 支撑对照有效 |
| 遮挡不敏感失败例 | 1 | 展示客观分析 |
| BM25 + MV 改善排序例 | 1 | 支撑性能补强 |

## Visual Cases

| Case ID | Case Type | Query ID | Page ID | COG_score | Figure |
|---|---|---|---|---:|---|
| evidence_case_001 | Gold mask 后明显掉分 | q001 | doc001_p001 | 0.28208059 | figures\week7\evidence_case_001.png |
| evidence_case_002 | Gold mask 后明显掉分 | q011 | doc003_p010 | 0.28198810 | figures\week7\evidence_case_002.png |
| evidence_case_003 | Random mask 影响较小 | q002 | doc001_p002 | 0.13606575 | figures\week7\evidence_case_003.png |
| evidence_case_004 | 遮挡不敏感失败例 | q004 | doc001_p004 | 0.01350269 | figures\week7\evidence_case_004.png |
| evidence_case_005 | BM25 + MV 改善排序例 | q010 | doc003_p009 | 0.28175521 | figures\week7\evidence_case_005.png |

## evidence_case_001

- Case type: Gold mask 后明显掉分
- Query ID: q001
- Page ID: doc001_p001
- COG_score: 0.28208059
- COG_nDCG: 1.00000000
- Explanation: Gold evidence bbox 被遮挡后，evidence score 明显下降；random mask 基本保持原始区域信息，说明模型分数主要依赖被标注的 evidence region。

![evidence_case_001](figures/week7/evidence_case_001.png)

## evidence_case_002

- Case type: Gold mask 后明显掉分
- Query ID: q011
- Page ID: doc003_p010
- COG_score: 0.28198810
- COG_nDCG: 1.00000000
- Explanation: Gold evidence bbox 被遮挡后，evidence score 明显下降；random mask 基本保持原始区域信息，说明模型分数主要依赖被标注的 evidence region。

![evidence_case_002](figures/week7/evidence_case_002.png)

## evidence_case_003

- Case type: Random mask 影响较小
- Query ID: q002
- Page ID: doc001_p002
- COG_score: 0.13606575
- COG_nDCG: 1.00000000
- Explanation: Random mask 与 gold evidence 几乎无重叠，score_random 与 score_original 接近；该案例用于证明对照遮挡未破坏关键证据区域。

![evidence_case_003](figures/week7/evidence_case_003.png)

## evidence_case_004

- Case type: 遮挡不敏感失败例
- Query ID: q004
- Page ID: doc001_p004
- COG_score: 0.01350269
- COG_nDCG: 1.00000000
- Explanation: 该样本的 COG_score 相对较小，可作为遮挡敏感性较弱的客观分析案例；说明部分页面证据区域可能较稀疏或存在上下文冗余。

![evidence_case_004](figures/week7/evidence_case_004.png)

## evidence_case_005

- Case type: BM25 + MV 改善排序例
- Query ID: q010
- Page ID: doc003_p009
- COG_score: 0.28175521
- COG_nDCG: 1.00000000
- Explanation: 该案例保留原始页面、gold evidence bbox 与 occlusion 对照图，可用于展示视觉证据对排序补强的贡献。

![evidence_case_005](figures/week7/evidence_case_005.png)
