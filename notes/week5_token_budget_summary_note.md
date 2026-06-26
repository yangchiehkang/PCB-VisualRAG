# Week 5 Token Budget Experiment Summary Note

**Project:** PCB_VisualRAG_Project  
**Stage:** Week 5  
**Date:** 2026-05-07  
**Topic:** Patch/Token Selection for Budgeted Multi-vector Retrieval  
**Author:** 杨杰康  
**Status:** Completed  

---

## 1. 本周核心目标

Week 5 的目标是在 Week 4 已完成的 coarse-to-fine retrieval pipeline 基础上，进一步研究 page-level multi-vector 表征内部的 token 冗余问题。

Week 4 主要控制的是 page-level budget，即每个 query 进入 reranking 的候选页面数量 N。  
Week 5 进一步控制 token-level budget，即每个 candidate page 中参与 late interaction scoring 的 page token 数量 M。

本周核心问题是：

> PCB 文档页面的 multi-vector 表征中是否存在大量冗余 tokens？如果只保留 top-M 个高价值 tokens，是否能显著降低索引体积和匹配成本，同时维持检索性能？

当前页面 full multi-vector embedding 的 shape 为：

```text
(49, 512)
```

因此每页原始 token 数为：

```text
L = 49
```

本周实际测试的 token budget 为：

| Setting | M | Keep Ratio | Redundancy Ratio |
|---|---:|---:|---:|
| M8 | 8 | 16.33% | 83.67% |
| M16 | 16 | 32.65% | 67.35% |
| M24 | 24 | 48.98% | 51.02% |
| M32 | 32 | 65.31% | 34.69% |
| M49 | 49 | 100.00% | 0.00% |

其中，M49 是 full-token reference。

---

## 2. Token Selection 策略

本周采用的 token selection 方法为：

```text
Norm-based Top-M Token Selection
```

具体流程如下：

1. 读取页面 full multi-vector embedding；
2. 对每个 page token embedding 计算 L2 norm；
3. 按 token norm 从大到小排序；
4. 保留 top-M tokens；
5. 将保留 tokens 按原始 token index 顺序保存；
6. 输出不同 M 下的 compressed page embeddings；
7. 在 C2F reranking 阶段加载 compressed page embeddings；
8. 使用 compressed tokens 执行 late interaction scoring。

选择该策略的原因：

- 不需要训练额外模型；
- 不依赖 query；
- 可以离线预计算；
- 每页固定保留 M 个 tokens，便于控制 index size；
- 适合作为 token selection 的第一版 baseline。

---

## 3. Week 5 每日进展

### 3.1 Day 1：Token Selection Design

Day 1 完成 token selection 方案设计。

主要完成内容：

- 确认当前 page embedding shape 为 `(49, 512)`；
- 确认每页原始 token 数为 49；
- 固定 page budget 为 N=10；
- 选择 M8、M16、M24、M32、M49 作为 token budget；
- 确定 M49 作为 full-token reference；
- 确定 norm-based top-M token selection 作为主策略。

---

### 3.2 Day 2：Token Selection Module Validation

Day 2 完成 token selection 模块验证。

验证内容包括：

- 小规模页面 token selection；
- 不同 M 下 compressed embeddings 生成；
- token selection metadata 记录；
- late interaction scorer 兼容性验证；
- token mask 可视化样例生成。

Day 2 验证结果：

| M | Original Tokens | Kept Tokens | Keep Ratio | Status |
|---:|---:|---:|---:|---|
| 8 | 49 | 8 | 16.33% | PASSED |
| 16 | 49 | 16 | 32.65% | PASSED |
| 24 | 49 | 24 | 48.98% | PASSED |
| 32 | 49 | 32 | 65.31% | PASSED |
| 49 | 49 | 49 | 100.00% | PASSED |

结论：

- token selection 模块运行正常；
- 不同 M 下的 compressed page embeddings 可正常生成；
- late interaction scorer 能兼容变长 page tokens；
- M49 与 full-token setting 一致。

---

### 3.3 Day 3：Formal Retrieval Evaluation

Day 3 完成不同 token budget 下的正式 C2F reranking 实验。

实验设置：

| 项目 | 设置 |
|---|---|
| Retrieval pipeline | C2F reranking |
| Candidate budget | N=10 |
| Query count | 30 |
| Candidate rows | 300 |
| Page count | 101 |
| M list | 8, 16, 24, 32, 49 |

Day 3 检索结果：

| Method | M | Recall@1 | Recall@5 | Recall@10 | MRR@10 | nDCG@10 | Latency ms/query |
|---|---:|---:|---:|---:|---:|---:|---:|
| C2F N10 M8 | 8 | 0.0667 | 0.0667 | 0.2667 | 0.0907 | 0.1249 | 2.0249 |
| C2F N10 M16 | 16 | 0.0667 | 0.0667 | 0.2667 | 0.0901 | 0.1242 | 1.6379 |
| C2F N10 M24 | 24 | 0.0333 | 0.1000 | 0.2667 | 0.0754 | 0.1145 | 1.6846 |
| C2F N10 M32 | 32 | 0.0000 | 0.1000 | 0.2667 | 0.0465 | 0.0920 | 1.8168 |
| C2F N10 M49 | 49 | 0.0333 | 0.0333 | 0.2667 | 0.0628 | 0.1033 | 2.3857 |

主要发现：

- 所有 M 下 Recall@10 均为 0.2667；
- M8 和 M16 的 MRR@10 与 nDCG@10 高于 M49；
- M49 与 Week 4 C2F N10 结果一致，验证了 pipeline 正确性；
- M32 排序质量低于预期，说明更多 tokens 不一定带来更好的 ranking。

---

### 3.4 Day 4：Index Size and Cost Analysis

Day 4 完成 index size、latency 和 quality-cost curve 分析。

Index size 统计结果：

| Setting | M | Num Pages | Total Vectors | Avg Tokens/Page | Payload Size MB | Payload Reduction vs Full |
|---|---:|---:|---:|---:|---:|---:|
| M8 | 8 | 101 | 808 | 8.00 | 1.5781 | 83.67% |
| M16 | 16 | 101 | 1616 | 16.00 | 3.1563 | 67.35% |
| M24 | 24 | 101 | 2424 | 24.00 | 4.7344 | 51.02% |
| M32 | 32 | 101 | 3232 | 32.00 | 6.3125 | 34.69% |
| M49 | 49 | 101 | 4949 | 49.00 | 9.6660 | 0.00% |

Quality-cost 综合结果：

| M | Payload Size MB | Payload Reduction | Recall@10 | MRR@10 | nDCG@10 | Latency ms/query |
|---:|---:|---:|---:|---:|---:|---:|
| 8 | 1.5781 | 83.67% | 0.2667 | 0.0907 | 0.1249 | 2.0249 |
| 16 | 3.1563 | 67.35% | 0.2667 | 0.0901 | 0.1242 | 1.6379 |
| 24 | 4.7344 | 51.02% | 0.2667 | 0.0754 | 0.1145 | 1.6846 |
| 32 | 6.3125 | 34.69% | 0.2667 | 0.0465 | 0.0920 | 1.8168 |
| 49 | 9.6660 | 0.00% | 0.2667 | 0.0628 | 0.1033 | 2.3857 |

Day 4 结论：

- Index size 与 M 基本呈线性关系；
- M16 相比 M49 降低 67.35% payload size；
- M16 保持 Recall@10 不变；
- M16 的 MRR@10 和 nDCG@10 高于 M49；
- M16 是当前最佳 quality-cost trade-off。

---

### 3.5 Day 5：Redundancy and Region Analysis

Day 5 完成 token redundancy、type sensitivity 和 token mask 可视化分析。

Redundancy ratio 结果：

| M | Keep Ratio | Redundancy Ratio | Recall Retention | MRR Retention | nDCG Retention |
|---:|---:|---:|---:|---:|---:|
| 8 | 16.33% | 83.67% | 100.00% | 144.46% | 120.89% |
| 16 | 32.65% | 67.35% | 100.00% | 143.57% | 120.27% |
| 24 | 48.98% | 51.02% | 100.00% | 120.19% | 110.82% |
| 32 | 65.31% | 34.69% | 100.00% | 74.04% | 89.06% |
| 49 | 100.00% | 0.00% | 100.00% | 100.00% | 100.00% |

关键发现：

- M8 只保留 16.33% tokens，仍保持 100% Recall@10；
- M16 只保留 32.65% tokens，仍保持 100% Recall@10；
- M8 和 M16 的 nDCG@10 均高于 M49；
- 当前至少约 67.35% tokens 可视为高冗余；
- 在强压缩设置下，约 83.67% tokens 可被移除且 Recall@10 不下降。

页面类型和 query 类型分析：

- 已生成 page type annotation template；
- 已生成 query type annotation template；
- 当前尚未人工标注，因此所有样本暂归为 Unlabeled；
- 当前 type sensitivity 结果主要用于验证分析流程。

Token mask 可视化观察：

- M8/M16 下保留 token 分布稀疏；
- selected tokens 并非均匀分布；
- selected tokens 倾向集中于页面上方、边缘、高信息密度区域；
- 这些区域可能对应标题、表格、注释、图形标注或局部结构密集区域；
- 大量空白或低纹理区域被剪枝。

---

## 4. Token Budget 主结果表

| Method | M | Keep Ratio | Redundancy Ratio | Recall@10 | MRR@10 | nDCG@10 | Index Size MB | Latency ms/query |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Full MV | full | 100.00% | 0.00% | 0.1333 | 0.0644 | 0.0807 | 9.6660 | N/A |
| C2F N10 M8 | 8 | 16.33% | 83.67% | 0.2667 | 0.0907 | 0.1249 | 1.5781 | 2.0249 |
| C2F N10 M16 | 16 | 32.65% | 67.35% | 0.2667 | 0.0901 | 0.1242 | 3.1563 | 1.6379 |
| C2F N10 M24 | 24 | 48.98% | 51.02% | 0.2667 | 0.0754 | 0.1145 | 4.7344 | 1.6846 |
| C2F N10 M32 | 32 | 65.31% | 34.69% | 0.2667 | 0.0465 | 0.0920 | 6.3125 | 1.8168 |
| C2F N10 M49 | 49 | 100.00% | 0.00% | 0.2667 | 0.0628 | 0.1033 | 9.6660 | 2.3857 |

说明：

- Full MV 与 C2F 系列并非完全相同 pipeline，因此更适合作为系统级参考；
- token budget 内部最可靠的对比是 M8、M16、M24、M32、M49；
- M49 是当前 token budget 实验的 full-token reference。

---

## 5. 最优配置结论

当前最佳 quality-cost trade-off 配置为：

```text
C2F N10 M16
```

选择理由：

1. 只保留 32.65% tokens；
2. 移除 67.35% tokens；
3. Payload size 从 9.6660 MB 降到 3.1563 MB；
4. Recall@10 与 M49 持平；
5. MRR@10 从 0.0628 提升到 0.0901；
6. nDCG@10 从 0.1033 提升到 0.1242；
7. latency 从 2.3857 ms/query 降到 1.6379 ms/query；
8. 质量接近 M8，但速度更快。

M8 是最大压缩点，适合证明极限压缩潜力。  
M24 是保守压缩点，适合高质量压缩场景。  
M49 是 full-token reference。

---

## 6. Week 6 代表配置建议

Week 6 将进入 quantization compression 实验。建议选择以下代表配置：

| 配置类型 | 建议配置 | 选择理由 |
|---|---|---|
| 高质量 / 保守压缩点 | C2F N10 M24 | 保留接近一半 tokens，payload 降低 51.02%，质量高于 M49 |
| 最佳 trade-off 点 | C2F N10 M16 | 当前质量、索引体积和 latency 最均衡 |
| 极致轻量点 | C2F N10 M8 | 只保留 16.33% tokens，用于测试极限压缩性能下界 |
| Full-token reference | C2F N10 M49 | 作为 token pruning 与 quantization 的 full-token baseline |

Week 6 可以在 M8、M16、M24 和 M49 上叠加不同 bit-width 的 embedding quantization，用于构造 token pruning + quantization 的 Pareto frontier。

---

## 7. 本周结论

Week 5 的实验表明，PCB 文档页面中的 patch/token 表征存在显著冗余。通过仅保留 norm 较高的 top-M 个局部向量，可以在大幅降低索引体积与 late interaction 匹配成本的同时，维持甚至提升当前设置下的检索排序质量。

在当前 101 页、30 个 queries、N=10 的 C2F reranking 设置下，M16 仅保留 32.65% tokens，却保持与 full-token M49 相同的 Recall@10，并将 index payload size 降低 67.35%。同时，M16 的 MRR@10 和 nDCG@10 均高于 M49，说明 norm-based token selection 可能具有一定去噪效果。

从最大压缩角度看，M8 仅保留 16.33% tokens，仍保持 Recall@10 不下降，并取得当前最高的 MRR@10 和 nDCG@10。这进一步说明当前页面 multi-vector 表征中存在大量对最终检索贡献有限的 tokens。

最终，Week 5 推荐将 M16 作为最佳 quality-cost trade-off 配置，将 M8、M16、M24 和 M49 作为 Week 6 量化压缩实验的代表配置。
