# Week 6 Day 5 实验日志：预算三元组分析、分组结果与失败案例整理

**Project:** PCB_VisualRAG_Project  
**Stage:** Week 6  
**Day:** Day 5  
**Date:** 2026-05-07  
**Experiment:** Budget Triplet Analysis and Failure Case Diagnosis  
**Budget Dimensions:** N / M / bits  
**Input Results:** Week 6 Day 3 + Day 5 bits sweep  
**Status:** Completed  

---

## 1. 今日目标

Week 6 Day 5 的目标是从 Day 3 和 Day 4 的联合 budget 实验中提炼预算三元组规律，并补充必要的分组分析与失败案例整理。

今日重点回答三个问题：

```text
1. N 控制什么？
2. M 控制什么？
3. bits 控制什么？
```

并进一步分析：

```text
- 哪些 query 对 M 更敏感；
- 哪些 query 对 quantization 更敏感；
- 哪些失败来自 coarse retrieval；
- 哪些失败来自 token budget；
- 哪些失败来自 quantization ranking distortion；
- 哪些失败即使大预算也无法解决。
```

---

## 2. 今日执行的脚本

### 2.1 Bits Sweep

已运行：

```text
python scripts/analysis/run_week6_day5_bits_sweep.py
```

该脚本在固定配置下测试不同 PQ bits：

```text
N = 10
M = 24
PQ_M = 16
bits ∈ {2, 4, 8}
```

输出文件：

```text
results/budgeted/joint_compression/day5_analysis/day5_bits_sweep_results.csv
results/budgeted/joint_compression/day5_analysis/day5_bits_sweep_results.md
```

---

### 2.2 Budget Triplet Analysis

已运行：

```text
python scripts/analysis/analyze_week6_day5_budget_triplet.py
```

该脚本完成：

```text
1. 清洗 Day 3 joint results
2. 计算 coarse recall ceiling
3. 生成 per-query metrics
4. 汇总 M group results
5. 计算 compression delta vs None
6. 分析 query sensitivity by M
7. 分析 query sensitivity by quantization
8. 汇总 bits sensitivity
9. 生成 failure cases
10. 输出 Day 5 分析笔记
```

核心输出文件：

```text
results/budgeted/joint_compression/day5_analysis/day5_budget_triplet_analysis_note.md
```

---

## 3. 今日生成文件清单

### 3.1 Bits Sweep

```text
results/budgeted/joint_compression/day5_analysis/day5_bits_sweep_results.csv
results/budgeted/joint_compression/day5_analysis/day5_bits_sweep_results.md
results/budgeted/joint_compression/day5_analysis/day5_bits_sensitivity.csv
results/budgeted/joint_compression/day5_analysis/day5_bits_sensitivity.md
```

### 3.2 Budget Dimension Analysis

```text
results/budgeted/joint_compression/day5_analysis/day5_budget_dimension_impact.csv
results/budgeted/joint_compression/day5_analysis/day5_budget_dimension_impact.md
results/budgeted/joint_compression/day5_analysis/day5_budget_triplet_analysis_note.md
```

### 3.3 Clean Joint Results

```text
results/budgeted/joint_compression/day5_analysis/day5_clean_joint_results.csv
results/budgeted/joint_compression/day5_analysis/day5_clean_joint_results.md
```

### 3.4 Coarse Recall Ceiling

```text
results/budgeted/joint_compression/day5_analysis/day5_coarse_recall_ceiling.csv
results/budgeted/joint_compression/day5_analysis/day5_coarse_recall_ceiling.md
```

### 3.5 M Group and Compression Delta

```text
results/budgeted/joint_compression/day5_analysis/day5_m_group_summary.csv
results/budgeted/joint_compression/day5_analysis/day5_m_group_summary.md
results/budgeted/joint_compression/day5_analysis/day5_compression_delta_vs_none.csv
results/budgeted/joint_compression/day5_analysis/day5_compression_delta_vs_none.md
```

### 3.6 Per-query Sensitivity

```text
results/budgeted/joint_compression/day5_analysis/day5_per_query_metrics.csv
results/budgeted/joint_compression/day5_analysis/day5_per_query_metrics.md
results/budgeted/joint_compression/day5_analysis/day5_query_sensitivity_by_M.csv
results/budgeted/joint_compression/day5_analysis/day5_query_sensitivity_by_M.md
results/budgeted/joint_compression/day5_analysis/day5_query_sensitivity_by_quantization.csv
results/budgeted/joint_compression/day5_analysis/day5_query_sensitivity_by_quantization.md
```

### 3.7 Failure Cases

```text
results/budgeted/joint_compression/day5_analysis/day5_failure_cases.csv
results/budgeted/joint_compression/day5_analysis/day5_failure_cases.md
```

---

## 4. 今日实验设置

### 4.1 主实验预算

Day 5 沿用 Day 3 主实验设置：

```text
N = 10
M ∈ {8, 16, 24}
Compression ∈ {None, PQ, OPQ+PQ, IVF+PQ, IVF+OPQ+PQ}
```

### 4.2 Bits Sweep 设置

Day 5 新增 bits sensitivity 分析：

```text
N = 10
M = 24
Compression = PQ
bits ∈ {2, 4, 8}
```

其中 b4 对应 Day 3 主实验中的 M24 + PQ 设置，可作为中间参考点。

---

## 5. Coarse Recall Ceiling 分析

### 5.1 Top-10 Candidate Pool 覆盖率

Day 5 首先检查 single-vector coarse retrieval 的 top-10 candidate pool 是否包含 gold page。

输入 candidate 文件：

```text
artifacts/rerank_cache/single_vector_topN/single_vector_candidates_top10.tsv
```

结果显示，在 30 个 qrels query 中，gold page 进入 top-10 candidate pool 的 query 数为：

```text
8 / 30
```

因此当前 top-10 coarse candidate pool 的 recall ceiling 为：

```text
Coarse Recall Ceiling@10 = 0.266667
```

这与 Day 3 所有配置的 Recall@10 完全一致：

```text
Recall@10 = 0.266667
```

说明在当前实验中，Recall@10 的上限已经由 coarse retrieval 阶段决定，后续 reranking、token budget 和 quantization 无法突破该上限。

---

### 5.2 Gold Page 在 Candidate Pool 中的 Query

根据 `day5_coarse_recall_ceiling.csv` 和 per-query results，当前进入 top-10 candidate pool 的 query 包括：

```text
q001
q002
q003
q004
q022
q024
q025
q028
```

这些 query 构成了 reranking 能够真正发挥作用的有效集合。

---

### 5.3 Coarse Miss Query

当前 gold page 未进入 top-10 candidate pool 的 query 包括：

```text
q005
q006
q007
q008
q009
q010
q011
q012
q013
q014
q015
q016
q017
q018
q019
q020
q021
q023
q026
q027
q029
q030
```

这些 query 即使在更大的 M、更高 bits 或更复杂 compression 下，也无法在当前 N=10 candidate pool 内被 reranking 找回。

因此 Day 5 的第一条核心结论是：

```text
N controls the recall ceiling.
```

---

## 6. M 维度分析

### 6.1 M 控制的内容

M 表示每个 page 保留的 visual tokens 数量。它主要控制 late interaction 阶段可用的局部证据量。

在当前实验中：

```text
M = 8  表示极低 token budget
M = 16 表示中等 token budget
M = 24 表示较高 token budget
```

M 不改变 coarse candidate pool，因此不会改变 Recall@10 上限，但会影响：

```text
- gold page 在 reranked list 中的位置；
- RR@10；
- nDCG@10；
- 局部视觉证据是否被保留。
```

---

### 6.2 M Group Summary

根据 Day 5 的 M group summary：

| M | Best Quality Run | Best Quality Compression | Role |
|---:|---|---|---|
| 8 | w6_N10_M8_ivf_opq_pq | IVF+OPQ+PQ | lowest-cost frontier |
| 16 | w6_N10_M16_ivf_opq_pq | IVF+OPQ+PQ | middle budget frontier |
| 24 | w6_N10_M24_ivf_opq_pq | IVF+OPQ+PQ | best quality frontier |

M8、M16、M24 对应的 best-quality 点都来自：

```text
IVF+OPQ+PQ
```

这与 Day 4 的 index-size Pareto frontier 一致。

---

### 6.3 对 M 敏感的 Query

Day 5 通过 `day5_query_sensitivity_by_M.csv` 比较了 None 配置下 M8、M16、M24 的 per-query nDCG@10。

最明显受益于 larger M 的 query 是：

```text
q004
```

其结果为：

```text
nDCG@10_M8  = 0.289065
nDCG@10_M16 = 0.289065
nDCG@10_M24 = 0.500000
Delta nDCG@10 M24 - M8 = +0.210935
```

对应 first relevant rank 从较低 M 下的靠后位置提升到更前位置。

这说明 q004 需要更多 page tokens 才能保留有效局部证据。小 M 时，相关证据虽然没有完全消失，但排序位置较差。

---

### 6.4 对 M 稳定的 Query

以下 query 在 M8、M16、M24 下基本稳定：

```text
q001
q003
q005
q006
q007
q008
q009
q011
...
```

其中稳定可以分为两类：

```text
1. 始终命中且排名变化很小；
2. 始终不命中，因为 gold page 不在 candidate pool。
```

第二类 query 不应被解释为 M 不重要，而是因为 N 已经成为瓶颈。

---

## 7. Bits 维度分析

### 7.1 Bits Sweep 设置

Day 5 使用固定配置测试 bits sensitivity：

```text
N = 10
M = 24
Compression = PQ
bits ∈ {2, 4, 8}
```

其中：

```text
b2 = 更强压缩
b4 = Day 3 默认压缩强度
b8 = 更弱压缩 / 更高保真度
```

---

### 7.2 已观测的 b2 结果

从 `day5_bits_sensitivity.csv` 可见，PQ-b2 的结果为：

| Setting | Value |
|---|---:|
| N | 10 |
| M | 24 |
| bits | 2 |
| Recall@10 | 0.266667 |
| MRR@10 | 0.063148 |
| nDCG@10 | 0.105743 |
| Index Size MB | 0.009247 |
| Compression Ratio vs FP Payload | 512× |

与 Day 3 的 PQ-b4 / M24 结果相比：

| Setting | nDCG@10 | MRR@10 | Index Size MB |
|---|---:|---:|---:|
| PQ-b2 | 0.105743 | 0.063148 | 0.009247 |
| PQ-b4 | 0.125460 | 0.088929 | 0.018494 |

可以看出：

```text
bits 从 4 降到 2 后，index size 约减半，但 nDCG@10 和 MRR@10 明显下降。
```

这说明过强量化会导致 fine-grained similarity ranking distortion。

---

### 7.3 Bits 控制的内容

bits 控制每个 PQ sub-vector 的编码精度。它主要影响：

```text
- reconstructed embedding fidelity；
- similarity score 的稳定性；
- reranking order 是否被改变；
- index size 与质量之间的压缩强度折中。
```

Day 5 的 bits sweep 支持以下结论：

```text
bits controls ranking fidelity.
```

较低 bits 并不一定改变 Recall@10，因为 Recall@10 受 coarse candidate ceiling 限制；但它会明显影响 MRR@10 和 nDCG@10。

---

## 8. Quantization Sensitivity 分析

### 8.1 Hurt by Quantization

Day 5 根据 `day5_query_sensitivity_by_quantization.csv` 将 query 按 quantization 后的变化分为：

```text
hurt_by_quantization
stable
improved_by_quantization
```

最明显的 hurt cases 包括：

```text
q002
q025
q004
```

---

### 8.2 q002：最强 quantization sensitivity

q002 是当前对 quantization 最敏感的 query。

在 baseline None 下，q002 的相关页排名非常靠前，但压缩后 RR@10 和 nDCG@10 出现明显下降。

典型变化包括：

```text
M8 + IVF+OPQ+PQ: RR@10 下降约 -0.8889
M8 + PQ / OPQ+PQ: RR@10 下降约 -0.8750
M16 + IVF+PQ: RR@10 下降约 -0.8333
M16 + PQ / OPQ+PQ: RR@10 下降约 -0.6667
M16 + IVF+OPQ+PQ: RR@10 下降约 -0.5000
M24 + IVF+PQ: RR@10 下降约 -0.2083
M24 + IVF+OPQ+PQ: RR@10 下降约 -0.1667
M24 + PQ: RR@10 下降约 -0.1333
```

这一现象说明 q002 的 gold page 与其他候选 page 的 score margin 可能较小，quantization noise 足以改变 top-k ordering。

---

### 8.3 q025：高质量 baseline 但压缩后排名下降

q025 在 None baseline 中表现很好：

```text
Hit@10 = 1.0
RR@10 = 1.0
nDCG@10 = 1.0
```

但在多个压缩配置下 RR@10 出现明显下降，例如：

```text
M16 + OPQ+PQ: RR@10 下降约 -0.8333
M8 + PQ / OPQ+PQ: RR@10 下降约 -0.7500
多个 M 和 compression 组合: RR@10 下降约 -0.5000
```

这说明 q025 对 fine-grained similarity score 的微小变化很敏感。

---

### 8.4 q004：同时体现 M sensitivity 和 quantization sensitivity

q004 具有双重特点：

```text
1. larger M 明显提升其 nDCG@10；
2. 部分 quantization 配置会降低其 ranking quality。
```

在 None 配置下：

```text
M8 / M16: nDCG@10 = 0.289065
M24:      nDCG@10 = 0.500000
```

说明 q004 需要更多 token evidence。

同时在 M24 下：

```text
OPQ+PQ: RR@10 下降约 -0.1667
IVF+PQ: RR@10 下降约 -0.0833
```

说明 q004 也会受到 quantization ranking distortion 的影响。

---

### 8.5 Stable Query

稳定 query 包括：

```text
q028
q003
```

其中 q028 在多个配置下保持 Hit@10 = 1.0，RR@10 变化很小；q003 也整体表现稳定。

稳定 query 通常说明：

```text
- gold page 在候选池中；
- ranking margin 相对稳定；
- token selection 和 quantization 不容易改变其 top-10 命中状态。
```

---

## 9. Compression Delta vs None

Day 5 计算了每个 M 下压缩配置相对 None baseline 的变化。

### 9.1 M8 下的压缩影响

在 M8 下，压缩不会改变 Recall@10：

```text
Delta Recall@10 vs None = 0
```

但会影响 MRR@10 和 nDCG@10。

典型变化：

```text
PQ:         Delta nDCG@10 ≈ -0.029974
OPQ+PQ:     Delta nDCG@10 ≈ -0.036053
IVF+PQ:     Delta nDCG@10 ≈ -0.027947
IVF+OPQ+PQ: Delta nDCG@10 ≈ -0.025843
```

M8 下，压缩带来明显存储收益，但排序质量有所下降。

---

### 9.2 M24 下压缩可能优于 None

Day 3 和 Day 5 的清洗结果显示，在 M24 下，部分压缩配置反而优于 None baseline。

例如：

```text
M24 + PQ:
nDCG@10 = 0.125460
```

而：

```text
M24 + None:
nDCG@10 = 0.114467
```

这说明压缩并不总是单调降低质量。原因可能包括：

```text
- quantization reconstruction 对 embedding 有一定 smoothing effect；
- ranking score 的扰动偶然提升了部分 relevant page 的位置；
- 当前样本规模较小，query-level 波动会影响 aggregate metric。
```

因此论文中应谨慎表述为：

```text
Compression can preserve competitive ranking quality and sometimes improves observed ranking under this small-scale setting.
```

而不是简单断言压缩一定提升质量。

---

## 10. Failure Case 整理

Day 5 生成失败案例文件：

```text
results/budgeted/joint_compression/day5_analysis/day5_failure_cases.csv
```

失败案例主要分为四类。

---

### 10.1 Small N / Coarse Miss Failure

失败类型：

```text
small_N_or_coarse_miss
```

原因：

```text
gold page not found in top10 candidate pool
```

对应 query 包括：

```text
q005
q006
q007
q008
q009
q010
q011
q012
q013
q014
q015
q016
q017
q018
q019
q020
q021
q023
q026
q027
q029
q030
```

分析价值：

```text
说明 N 控制 recall ceiling。
当 gold page 不进入 coarse candidate pool 时，reranking 阶段无法恢复。
```

---

### 10.2 Small M Failure

失败类型：

```text
small_M_failure
```

代表 query：

```text
q004
```

证据：

```text
Delta nDCG@10 M24 - M8 = +0.210935
```

可能原因：

```text
small token budget removes or weakens local matching evidence.
```

分析价值：

```text
说明 M 控制 fine-grained evidence retention。
对于依赖局部结构、标注、表格或细粒度视觉区域的 query，M 太小会导致排序质量下降。
```

---

### 10.3 Quantization Ranking Distortion

失败类型：

```text
quantization_ranking_distortion
```

代表 query：

```text
q002
q025
q004
```

可能原因：

```text
quantization noise changes fine-grained similarity ordering.
```

分析价值：

```text
说明 bits / compression strength 控制 ranking fidelity。
即使 Hit@10 保持不变，RR@10 和 nDCG@10 仍可能明显下降。
```

---

### 10.4 Large Budget Still Failure

失败类型：

```text
large_budget_still_failure
```

这类失败出现在 best-quality 配置下仍然没有命中的 query 中。

可能原因：

```text
- gold page 未进入 candidate pool；
- query representation 不足；
- page visual evidence 不充分；
- 当前 single-vector coarse retrieval 和 qrels 之间存在 mismatch；
- 问题不完全由 budget 决定。
```

分析价值：

```text
说明并非所有失败都能通过增加 M 或 bits 解决。
有些失败需要改进 coarse retriever、query encoder 或数据标注质量。
```

---

## 11. 预算三元组影响总结

### 11.1 预算维度影响表

| Budget Dimension | Main Control | Main Risk | Current Evidence | Conclusion |
|---|---|---|---|---|
| N | candidate pool size / recall ceiling | gold page not recalled by coarse retrieval | top-10 candidate ceiling = 0.266667 | N 是第一优先级预算 |
| M | number of retained visual tokens | local evidence removed | q004 benefits from M24 over M8 | M 控制 fine-grained evidence |
| bits | quantization fidelity | ranking distortion | PQ-b2 has lower nDCG/MRR than PQ-b4 | bits 控制 similarity ranking fidelity |

---

### 11.2 当前预算优先级

根据 Day 5 分析，当前 PCB retrieval 任务中的预算优先级应为：

```text
1. First: protect N / coarse recall
2. Second: allocate enough M / visual tokens
3. Third: tune bits / compression strength
```

原因是：

```text
- 如果 gold page 没有进入 candidate pool，后续 reranking 无法补救；
- 如果 M 太小，局部细粒度证据可能丢失；
- 如果 bits 太低，相关 page 仍可能在 top-10 内，但排序位置会变差。
```

---

## 12. 对论文主结论的支持

Day 5 支持以下论文主结论：

### 12.1 N 是 recall ceiling 的决定因素

当前所有 Day 3 配置均为：

```text
Recall@10 = 0.266667
```

而 coarse candidate pool 中 gold page 覆盖率也是：

```text
8 / 30 = 0.266667
```

因此可以明确说明：

```text
The coarse retrieval budget N determines the upper bound of recall in the current pipeline.
```

---

### 12.2 M 影响排序质量而非 recall ceiling

在固定 N=10 下，改变 M 不改变 Recall@10，但会影响：

```text
MRR@10
nDCG@10
first relevant rank
```

代表案例 q004 显示，M24 相比 M8 显著提升 nDCG@10。

---

### 12.3 Bits 影响 ranking fidelity

PQ-b2 的压缩率更高：

```text
512× vs FP payload
```

但质量明显低于 PQ-b4：

```text
PQ-b2 nDCG@10 = 0.105743
PQ-b4 nDCG@10 = 0.125460
```

说明过低 bits 会带来相似度排序失真。

---

### 12.4 Compression 在中等预算下仍可保持竞争力

M24 + PQ 和 M24 + IVF+OPQ+PQ 均显示，在较小 index size 下可以达到甚至超过 uncompressed baseline 的 nDCG@10。

这支持 Week 6 的核心方向：

```text
Budgeted multi-vector retrieval can substantially reduce storage while preserving competitive ranking quality.
```

---

## 13. 今日注意事项

### 13.1 当前 N 仍固定为 10

由于当前只有：

```text
single_vector_candidates_top10.tsv
```

Day 5 不能直接做真实 N sweep，只能通过 top-10 candidate gold coverage 分析 N 的 recall ceiling。

后续如果生成：

```text
top20
top50
top100
```

即可直接评估 N 的边际收益。

---

### 13.2 Query type / page type 分组仍需 metadata 支持

Day 5 当前完成的是 query-level sensitivity 分析，但尚未结合 query type 或 page type metadata。

如果后续存在 query/page metadata，可进一步补充：

```text
- by query intent
- by page structure
- by visual region type
- by table / legend / annotation / component layout
```

---

### 13.3 部分 uploaded CSV 内容被摘要化显示

当前部分上传文件在界面中显示为 dataset summary 或截断内容，但本地生成的 `.csv` 文件已经完整保存在：

```text
results/budgeted/joint_compression/day5_analysis
```

后续论文写作应优先使用本地原始 CSV / MD 文件，而不是界面预览文本。

---

## 14. Day 5 验收状态

| Requirement | Status |
|---|---|
| 预算三元组分析笔记已生成 | Completed |
| bits sensitivity 已完成 | Completed |
| coarse recall ceiling 已计算 | Completed |
| M group summary 已生成 | Completed |
| compression delta vs None 已生成 | Completed |
| per-query metrics 已生成 | Completed |
| query sensitivity by M 已生成 | Completed |
| query sensitivity by quantization 已生成 | Completed |
| failure cases 已整理 | Completed |
| N / M / bits 各自作用已明确 | Completed |

---

## 15. 今日结论

Week 6 Day 5 已完成预算三元组分析和失败案例整理。实验结果表明，在当前固定 N=10 的 pipeline 中，Recall@10 的上限完全由 coarse retrieval candidate pool 决定。top-10 candidate 中 gold page 覆盖率为 8/30，即 0.266667，这与所有 joint budget 配置的 Recall@10 一致。因此，N 是最关键的预算维度，决定系统的 recall ceiling。

M 主要影响 late interaction 阶段的局部证据保留和排序质量。代表 query q004 在 M24 下相较 M8 获得明显 nDCG@10 提升，说明部分 query 需要更多视觉 token 来保留关键局部信息。bits 则控制量化保真度和 similarity ranking fidelity。PQ-b2 虽然将 index size 进一步降低到 0.009247 MB，并达到约 512× 压缩率，但其 nDCG@10 和 MRR@10 明显低于 PQ-b4，说明过强量化会造成排序失真。

综合 Day 5 分析，当前 PCB VisualRAG 检索任务中的预算优先级应为：首先保证 coarse recall，即提高或保护 N；其次保证足够的 visual token budget M；最后在可接受质量损失范围内调整 bits 和 compression strength。Day 5 已为最终论文讨论提供了预算三元组规律、query-level sensitivity 和 failure case evidence。
