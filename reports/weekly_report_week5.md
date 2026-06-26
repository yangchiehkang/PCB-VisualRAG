# Weekly Report - Week 5

**Project:** PCB_VisualRAG_Project  
**Week:** Week 5  
**Date:** 2026-05-07  
**Topic:** Token Budgeting for Efficient Multi-vector Retrieval  
**Author:** 杨杰康  
**Status:** Completed  

---

## 1. 本周目标

Week 5 的目标是研究 PCB 文档页面 multi-vector 表征中的 token 冗余，并验证 token-level budget 是否可以降低检索系统的存储成本和匹配成本。

在 Week 4 中，系统已经实现 coarse-to-fine retrieval，即先使用 single-vector retrieval 召回候选页面，再使用 full multi-vector late interaction reranking。Week 5 在该框架上进一步引入 token budget M，只保留每个页面中 top-M 个高价值 page tokens。

本周核心研究问题包括：

1. 每页只保留部分 patch/token vectors 是否仍能保持检索质量；
2. 不同 M 对 Recall@10、MRR@10、nDCG@10 的影响；
3. 不同 M 对 index size 和 reranking latency 的影响；
4. 当前最佳 quality-cost trade-off 点；
5. 哪些 tokens 或页面区域更值得保留；
6. Week 6 量化压缩实验应选择哪些代表配置。

---

## 2. 实验设置

当前页面 full multi-vector embedding 的 shape 为：

```text
(49, 512)
```

因此每页原始 token 数为：

```text
L = 49
```

原计划中的 M64、M128 等设置超过当前 token 数，因此 Week 5 实际测试以下 M：

| Setting | M | Keep Ratio | Redundancy Ratio |
|---|---:|---:|---:|
| M8 | 8 | 16.33% | 83.67% |
| M16 | 16 | 32.65% | 67.35% |
| M24 | 24 | 48.98% | 51.02% |
| M32 | 32 | 65.31% | 34.69% |
| M49 | 49 | 100.00% | 0.00% |

固定 retrieval setting：

| 项目 | 设置 |
|---|---|
| Retrieval pipeline | C2F reranking |
| Candidate budget | N=10 |
| Query count | 30 |
| Candidate rows | 300 |
| Page count | 101 |
| Embedding dim | 512 |
| Token selection | Norm-based Top-M |
| Full-token reference | M49 |

---

## 3. 方法说明

本周采用的 token selection 方法是：

```text
Norm-based Top-M Token Selection
```

该方法对每个 page token embedding 计算 L2 norm，并保留 norm 最大的 M 个 tokens。该策略不依赖 query，可以离线处理所有页面，因此适合用于构建 compressed page embedding index。

流程如下：

1. 读取 full page multi-vector embedding；
2. 计算每个 token embedding 的 L2 norm；
3. 按 norm 从大到小排序；
4. 保留 top-M tokens；
5. 输出 compressed page embeddings；
6. 使用 compressed page embeddings 进行 late interaction reranking。

该方法的优势是简单、无需训练、易于复现，并能直接控制 index size。

---

## 4. 主结果表

本周主结果如下：

| Method | M | Keep Ratio | Redundancy Ratio | Recall@10 | MRR@10 | nDCG@10 | Index Size MB | Latency ms/query |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Full MV | full | 100.00% | 0.00% | 0.1333 | 0.0644 | 0.0807 | 9.6660 | N/A |
| C2F N10 M8 | 8 | 16.33% | 83.67% | 0.2667 | 0.0907 | 0.1249 | 1.5781 | 2.0249 |
| C2F N10 M16 | 16 | 32.65% | 67.35% | 0.2667 | 0.0901 | 0.1242 | 3.1563 | 1.6379 |
| C2F N10 M24 | 24 | 48.98% | 51.02% | 0.2667 | 0.0754 | 0.1145 | 4.7344 | 1.6846 |
| C2F N10 M32 | 32 | 65.31% | 34.69% | 0.2667 | 0.0465 | 0.0920 | 6.3125 | 1.8168 |
| C2F N10 M49 | 49 | 100.00% | 0.00% | 0.2667 | 0.0628 | 0.1033 | 9.6660 | 2.3857 |

说明：

- Full MV 与 C2F 系列不是完全相同的 pipeline，因此 Full MV 更适合作为系统级参考；
- token budget 内部最可靠的比较是 C2F N10 M8、M16、M24、M32 和 M49；
- M49 是 C2F token budget 实验中的 full-token reference。

---

## 5. 主要发现

从主结果表可以得到以下发现：

1. 所有 token budget 设置下 Recall@10 均为 0.2667；
2. M8 和 M16 的 MRR@10 与 nDCG@10 高于 full-token M49；
3. M16 具有最低的 measured reranking latency；
4. M8 具有最小的 index size 和最高的 ranking metrics；
5. M32 排序质量低于 M49，说明更多 tokens 不一定带来更好的 late interaction ranking；
6. M49 与 Week 4 C2F N10 结果一致，说明 token-budget pipeline 是可靠的。

---

## 6. Index Size and Latency Analysis

### 6.1 Index Size

不同 M 下的 index size 如下：

| M | Total Vectors | Avg Tokens/Page | Payload Size MB | Reduction vs M49 |
|---:|---:|---:|---:|---:|
| 8 | 808 | 8.00 | 1.5781 | 83.67% |
| 16 | 1616 | 16.00 | 3.1563 | 67.35% |
| 24 | 2424 | 24.00 | 4.7344 | 51.02% |
| 32 | 3232 | 32.00 | 6.3125 | 34.69% |
| 49 | 4949 | 49.00 | 9.6660 | 0.00% |

Index size 与 M 基本呈线性关系。  
从 M49 降到 M16 时，payload size 从 9.6660 MB 降到 3.1563 MB，减少 67.35%。

---

### 6.2 Latency

不同 M 下的 reranking latency 如下：

| M | Latency ms/query |
|---:|---:|
| 8 | 2.0249 |
| 16 | 1.6379 |
| 24 | 1.6846 |
| 32 | 1.8168 |
| 49 | 2.3857 |

M49 是当前最慢配置。  
M16 是当前最快配置。

由于当前 query 数较少，且 latency 处于毫秒级，细微差异可能受到缓存、文件读取和 Python 开销影响。因此 latency 的细节不宜过度解读，但整体上 token pruning 有助于降低 reranking cost。

---

## 7. Token Redundancy Analysis

以 M49 作为 full-token reference，redundancy analysis 结果如下：

| M | Keep Ratio | Redundancy Ratio | Recall Retention | MRR Retention | nDCG Retention |
|---:|---:|---:|---:|---:|---:|
| 8 | 16.33% | 83.67% | 100.00% | 144.46% | 120.89% |
| 16 | 32.65% | 67.35% | 100.00% | 143.57% | 120.27% |
| 24 | 48.98% | 51.02% | 100.00% | 120.19% | 110.82% |
| 32 | 65.31% | 34.69% | 100.00% | 74.04% | 89.06% |
| 49 | 100.00% | 0.00% | 100.00% | 100.00% | 100.00% |

该结果说明：

- M16 仅保留 32.65% tokens，却保持 100% Recall@10；
- M8 仅保留 16.33% tokens，也保持 Recall@10 不下降；
- 当前至少约 67.35% tokens 可被视为高冗余；
- 在强压缩设置下，约 83.67% tokens 可被移除且 Recall@10 不下降。

---

## 8. Page Type and Query Type Analysis

本周已生成 page type 和 query type annotation templates：

```text
results\budgeted\token_selection\day5_redundancy_analysis\day5_page_type_annotations.csv
results\budgeted\token_selection\day5_redundancy_analysis\day5_query_type_annotations.csv
```

当前 page types 和 query types 尚未人工标注，因此所有样本暂时归为：

```text
Unlabeled
```

当前 type sensitivity 分析验证了流程，但暂时不能对以下类别做细粒度结论：

- BOM；
- Stackup；
- Drill Table；
- Assembly Drawing；
- Notes；
- 参数查表类 query；
- 元件定位类 query；
- 规格确认类 query；
- 跨页一致性类 query。

后续补充标注后，可以重新运行相同脚本分析不同页面类型和 query 类型对 token budget 的敏感性。

---

## 9. Token Retention Region Observation

本周生成了多个页面的 token mask 可视化图。每张图展示同一页面在 M8、M16、M24、M32 和 M49 下的 selected token spatial distribution。

观察到的现象：

1. Selected tokens 并非均匀分布；
2. M8 和 M16 保留的 tokens 稀疏但具有明显结构；
3. 很多 selected tokens 出现在页面上方、边缘、表格结构、dense text region 或 local annotation area；
4. 大面积空白区域或低纹理区域更容易被剪枝；
5. M49 保留全部 49 个 tokens，作为 full-token reference。

这说明 norm-based token selection 倾向于保留高信息密度区域，而不是随机保留 tokens。

---

## 10. Best Configuration

本周最佳 overall quality-cost trade-off 配置为：

```text
C2F N10 M16
```

选择理由：

- 只保留 32.65% tokens；
- 移除 67.35% tokens；
- Payload size 从 9.6660 MB 降至 3.1563 MB；
- Recall@10 与 M49 持平；
- MRR@10 从 0.0628 提升到 0.0901；
- nDCG@10 从 0.1033 提升到 0.1242；
- latency 从 2.3857 ms/query 降至 1.6379 ms/query；
- 质量接近 M8，但 latency 更低。

M8 是 strongest compression point。  
M24 是 conservative high-quality compression point。  
M49 是 full-token reference。

---

## 11. Week 6 Representative Configurations

Week 6 将进行 quantization compression 实验。建议选择以下代表配置：

| Configuration Type | Recommended Setting | Reason |
|---|---|---|
| High-quality / conservative compression | C2F N10 M24 | Keeps 48.98% tokens, reduces index size by 51.02%, and maintains stronger ranking metrics than M49 |
| Best trade-off | C2F N10 M16 | Best balance among quality, index size, and latency |
| Extreme lightweight | C2F N10 M8 | Keeps only 16.33% tokens and tests the low-cost boundary |
| Full-token reference | C2F N10 M49 | Full-token baseline for token pruning and quantization comparison |

Week 6 should combine token pruning with vector quantization, testing different bit-widths on M8, M16, M24, and M49 to construct a complete quality-cost Pareto frontier.

---

## 12. 本周结论

Week 5 demonstrates that PCB document page-level multi-vector representations contain significant token redundancy. By retaining only top-M high-value local vectors, the system can substantially reduce index size and matching cost while maintaining retrieval quality.

The strongest practical result is M16: it removes 67.35% page tokens, reduces payload size by 67.35%, preserves Recall@10, and improves both MRR@10 and nDCG@10 compared with the full-token M49 setting. M8 further shows that even 83.67% token removal does not reduce Recall@10 under the current setup.

These results support token selection as an effective compression stage before Week 6 quantization experiments.
