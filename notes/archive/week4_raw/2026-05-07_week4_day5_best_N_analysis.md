# Week 4 Day 5 Quality-Cost Curve and Best N Analysis

**Project:** PCB_VisualRAG_Project  
**Stage:** Week 4  
**Day:** Day 5  
**Date:** 2026-05-07  
**Experiment Name:** Coarse-to-Fine Quality-Cost Curve Analysis  
**Status:** Completed  

---

## 1. 今日目标

今日目标是将 Day 4 的效果与时延评测结果转化为第一版质量–成本曲线图，并分析当前最具性价比的候选规模 N。

---

## 2. 输出图文件

| Figure | Path |
|---|---|
| Figure | `results\budgeted\coarse_to_fine\summary\figures\day5_quality_rerank_cost_Recall10_fixed.png` |
| Figure | `results\budgeted\coarse_to_fine\summary\figures\day5_quality_rerank_cost_Recall10_fixed.pdf` |
| Figure | `results\budgeted\coarse_to_fine\summary\figures\day5_quality_rerank_cost_nDCG10_fixed.png` |
| Figure | `results\budgeted\coarse_to_fine\summary\figures\day5_quality_rerank_cost_nDCG10_fixed.pdf` |
| Figure | `results\budgeted\coarse_to_fine\summary\figures\day5_quality_latency_Recall10_fixed.png` |
| Figure | `results\budgeted\coarse_to_fine\summary\figures\day5_quality_latency_Recall10_fixed.pdf` |
| Figure | `results\budgeted\coarse_to_fine\summary\figures\day5_quality_latency_nDCG10_fixed.png` |
| Figure | `results\budgeted\coarse_to_fine\summary\figures\day5_quality_latency_nDCG10_fixed.pdf` |
| Figure | `results\budgeted\coarse_to_fine\summary\figures\day5_quality_cost_curve_combined_fixed.png` |
| Figure | `results\budgeted\coarse_to_fine\summary\figures\day5_quality_cost_curve_combined_fixed.pdf` |

---

## 3. Quality-Cost Curve Data

| Method | N | Recall@10 | nDCG@10 | Latency ms/query | Rerank Cost |
|---|---:|---:|---:|---:|---:|
| Single-vector coarse | coarse | 0.2500 | 0.1041 |  | 0.0000 |
| Full Multi-vector | full | 0.1333 | 0.0807 |  | 101.0000 |
| C2F N=10 | 10 | 0.2500 | 0.1033 | 10.814267 | 10.0000 |
| C2F N=20 | 20 | 0.2500 | 0.1033 | 8.275533 | 10.0000 |
| C2F N=50 | 50 | 0.2500 | 0.1033 | 7.613867 | 10.0000 |
| C2F N=100 | 100 | 0.2500 | 0.1033 | 7.747500 | 10.0000 |

---

## 4. Best N 分析

| Best Type | N | Recall@10 | nDCG@10 | Latency ms/query | Rerank Cost |
|---|---:|---:|---:|---:|---:|
| Principled best trade-off | 10 | 0.2500 | 0.1033 | 10.814267 | 10.0000 |
| Lowest measured latency | 50 | 0.2500 | 0.1033 | 7.613867 | 10.0000 |

当前按照“效果不下降且 rerank cost 最小”的原则，N=10 是最合理的临时 best trade-off。

需要注意，当前 measured latency 的最低点不一定代表真实最佳 N，因为 N=10、20、50、100 的实际候选数都为 10。

---

## 5. 关键观察

### 5.1 当前曲线中 C2F 点重合

修改后的图中已经将重合点显式标注为 `C2F N=10/20/50/100`。

这说明当前不是绘图错误，而是实验数据本身具有如下特点：

- N=10、20、50、100 的 actual candidates/query 均为 10；
- 不同 N 的 Recall@10 完全一致；
- 不同 N 的 nDCG@10 完全一致；
- 原始 single-vector coarse run 很可能只保存了 top-10。

因此，本轮 Day 5 图应被解释为 pipeline validation figure，而不是最终 budget-scaling figure。

### 5.2 质量损失主要发生在 coarse stage

Day 2 的 coarse recall 为 0.2667，而 Day 4 的 C2F Recall@10 为 0.2500。

这说明 fine reranker 在候选集合内基本保留了可命中的 relevant pages，主要瓶颈仍然是 coarse retriever 的候选召回能力。

---

## 6. 图注草稿

**Figure 1: Coarse-to-Fine Retrieval Quality-Cost Curve.** The x-axis denotes reranking cost measured by the number of scored candidate pages per query, while the y-axis denotes retrieval quality measured by Recall@10 or nDCG@10. The figure marks the single-vector coarse baseline, the full multi-vector baseline, and C2F results under different candidate budgets. In the current experiment, all C2F settings use the same actual candidate depth of 10 pages per query due to the limited depth of the coarse retrieval run; therefore, the C2F points overlap and should be interpreted as pipeline validation rather than a complete budget-scaling curve.

---

## 7. 今日结论

Day 5 已完成第一版质量–成本曲线绘制和 best N 分析。

当前结论如下：

1. 当前 limited-depth setting 下，N=10 是最合理的临时 best trade-off；
2. 质量损失主要发生在 coarse stage；
3. C2F pipeline 值得继续推进；
4. 若要形成真实质量–成本曲线，需要重新生成 top-20、top-50、top-100 有效候选集合。


Week 4 Day 5 Quality–Cost Curve and Best N Analysis Log
Project: PCB_VisualRAG_Project

Stage: Week 4

Day: Day 5

Date: 2026-05-07

Experiment Name: Coarse-to-Fine Quality–Cost Curve Analysis

Author: 杨杰康

Status: Completed

1. 今日目标
今日目标是将 Day 4 得到的 coarse-to-fine 效果与时延评测结果转化为第一版论文图，绘制 质量–成本曲线，并分析当前设置下最具性价比的候选规模 N。

Day 5 不再重新执行检索或 reranking，而是基于已有结果完成可视化与分析。

今日重点关注以下问题：

能否绘制 coarse-to-fine 的质量–成本图；
横轴使用 rerank cost 或 latency 时，曲线趋势是否清晰；
纵轴使用 Recall@10 和 nDCG@10 时，C2F 与 Full MV 的关系如何；
当前是否能判断最佳 N；
质量损失主要发生在 coarse stage 还是 fine reranker stage；
当前 C2F pipeline 是否值得继续推进。
2. 实验背景
Week 4 的目标是验证 coarse-to-fine retrieval 是否能在降低 Full MV reranking 成本的同时保留大部分检索效果。

理论上，如果 coarse retriever 能召回足够多的相关页面，则 C2F 应表现出如下趋势：

N 增大时，Recall@10 和 nDCG@10 提升或趋于饱和；
N 增大时，rerank cost 和 latency 近似线性增长；
某个中等 N，例如 N=20 或 N=50，可能成为质量–效率折中的最佳点；
小 N 若已接近 Full MV，则说明 C2F 有明显效率优势。
不过，Day 2、Day 3 和 Day 4 已经发现一个关键限制：

当前 single-vector coarse run 实际每个 query 只保存了约 10 个候选页面，因此 N=20、50、100 并没有真正扩大候选集合。

因此 Day 5 的曲线需要被解释为：

C2F pipeline validation figure under limited candidate depth，而不是最终完整的 budget-scaling curve。

3. 输入文件
今日使用的输入文件如下：

类型	路径
Day 4 metrics	results/budgeted/coarse_to_fine/summary/c2f_day4_metrics_by_N.csv
Day 4 latency	results/budgeted/coarse_to_fine/summary/c2f_day4_latency_by_N.csv
Day 4 summary	results/budgeted/coarse_to_fine/summary/c2f_summary.csv
Single-vector run	results/baselines/single_vector_visual_run.tsv
Full MV run	results/full_multivector/full_mv_run.tsv
Qrels	data/metadata/qrels.tsv
这些文件来自 Week 4 Day 2–Day 4 的实验输出。

4. 输出文件
今日生成或修正后的主要输出文件如下：

类型	路径
Curve data	results/budgeted/coarse_to_fine/summary/day5_quality_cost_curve_data.csv
Summary JSON	results/budgeted/coarse_to_fine/summary/day5_quality_cost_curve_summary.json
Best N analysis note	notes/archive/week4_raw/2026-05-07_week4_day5_best_N_analysis.md
Recall@10 quality-cost figure	results/budgeted/coarse_to_fine/summary/figures/day5_quality_rerank_cost_Recall10_fixed.png
nDCG@10 quality-cost figure	results/budgeted/coarse_to_fine/summary/figures/day5_quality_rerank_cost_nDCG10_fixed.png
Recall@10 quality-latency figure	results/budgeted/coarse_to_fine/summary/figures/day5_quality_latency_Recall10_fixed.png
nDCG@10 quality-latency figure	results/budgeted/coarse_to_fine/summary/figures/day5_quality_latency_nDCG10_fixed.png
Combined quality-cost figure	results/budgeted/coarse_to_fine/summary/figures/day5_quality_cost_curve_combined_fixed.png
旧版未修正图仍保留，但正式分析优先使用带 _fixed 后缀的图片。

5. 使用脚本
今日使用脚本如下：

脚本	作用
scripts/analysis/plot_day5_quality_cost_curve.py	读取 Day 4 指标与时延结果，绘制质量–成本曲线并生成 best N 分析
脚本完成了以下工作：

读取 C2F N=10、20、50、100 的 metrics；
读取 C2F 各 N 的 latency；
重新评测 single-vector coarse baseline；
重新评测 Full MV baseline；
汇总 Recall@10、nDCG@10、latency、rerank cost；
生成 quality-cost figures；
生成 quality-latency figures；
自动识别 C2F 各 N 点重合问题；
输出 best N 分析文件。
6. Curve Data Summary
Day 5 使用的核心数据如下：

Method	N	Recall@10	nDCG@10	Latency ms/query	Rerank Cost
Single-vector coarse	coarse	0.2500	0.1041		0.0000
Full Multi-vector	full	0.1333	0.0807		100.0000
C2F	10	0.2500	0.1033	10.814267	10.0000
C2F	20	0.2500	0.1033	8.275533	10.0000
C2F	50	0.2500	0.1033	7.613867	10.0000
C2F	100	0.2500	0.1033	7.747500	10.0000
其中：

Rerank Cost 表示每个 query 需要执行 Full MV scoring 的候选页面数量；
Single-vector coarse 不执行 Full MV reranking，因此 rerank cost 记为 0；
Full MV 的 rerank cost 以全库或可用 page embedding 数量近似表示；
C2F 的 rerank cost 来自实际参与 reranking 的 candidates/query。
当前最重要的现象是：

C2F N=10、20、50、100 的 actual rerank cost 全部为 10，而不是名义上的 10、20、50、100。

7. Figure 1：Combined Quality–Cost Curve
今日最推荐用于记录和汇报的图为：

results/budgeted/coarse_to_fine/summary/figures/day5_quality_cost_curve_combined_fixed.png

该图包含两个子图：

Recall@10 vs. Rerank Cost；
nDCG@10 vs. Rerank Cost。
图中标记了三类方法：

图中标记	方法	含义
绿色方块	Single-vector coarse	不执行 Full MV rerank，成本最低
蓝色圆点	C2F	在候选集合内执行 Full MV reranking
红色星号	Full MV	对全库或更大范围执行 Full MV scoring
该图显示：

Single-vector coarse 位于低成本、高 Recall@10 区域；
C2F 位于低 rerank cost 区域，Recall@10 与 single-vector coarse 相同；
Full MV 位于高 rerank cost 区域，但当前 Recall@10 和 nDCG@10 低于 C2F；
C2F N=10、20、50、100 在图中重合，被标记为 C2F N=10/20/50/100。
图中底部说明明确指出：

all C2F settings currently use the same actual candidate depth: 10 pages/query.

这使得图的解释更加清楚，避免误解为真实 N=20、50、100 budget scaling。

8. Recall@10 Quality–Cost Figure
Recall@10 质量–成本图为：

results/budgeted/coarse_to_fine/summary/figures/day5_quality_rerank_cost_Recall10_fixed.png

该图显示：

Method	Rerank Cost	Recall@10
Single-vector coarse	0	0.2500
C2F N=10/20/50/100	10	0.2500
Full MV	100	0.1333
主要观察：

C2F 的 Recall@10 与 single-vector coarse 相同；
C2F 的 Recall@10 高于当前 Full MV baseline；
C2F 的 rerank cost 明显低于 Full MV；
C2F 不同 N 点完全重合。
这说明：

当前 C2F reranker 没有损失 coarse stage 已经召回的 relevant pages，但由于候选集合固定为 top-10，不同 N 无法形成真实曲线。

9. nDCG@10 Quality–Cost Figure
nDCG@10 质量–成本图为：

results/budgeted/coarse_to_fine/summary/figures/day5_quality_rerank_cost_nDCG10_fixed.png

该图显示：

Method	Rerank Cost	nDCG@10
Single-vector coarse	0	0.1041
C2F N=10/20/50/100	10	0.1033
Full MV	100	0.0807
主要观察：

C2F 的 nDCG@10 与 single-vector coarse 非常接近；
C2F 的 nDCG@10 高于当前 Full MV baseline；
Full MV 成本最高，但在当前 run 下 nDCG@10 并不占优；
C2F fine reranker 没有明显提升 nDCG，但也没有明显损害排序质量。
这说明：

在当前候选集合质量受限的情况下，Full MV reranking 对排序质量的增益有限，C2F 的主要性能仍由 coarse candidates 决定。

10. Recall@10 Quality–Latency Figure
Recall@10 质量–时延图为：

results/budgeted/coarse_to_fine/summary/figures/day5_quality_latency_Recall10_fixed.png

该图显示：

N	Recall@10	Latency ms/query
10	0.2500	10.814267
20	0.2500	8.275533
50	0.2500	7.613867
100	0.2500	7.747500
图中还有一条 Full MV quality reference，Recall@10 为 0.1333。

主要观察：

所有 C2F 点的 Recall@10 均为 0.2500；
C2F Recall@10 高于 Full MV reference；
latency 差异较小，约在 7.6–10.8 ms/query；
latency 没有随 N 增大而增长。
需要注意：

当前 latency 是 cached-candidate reranking latency，不包含 coarse retrieval time。

因此，不能把这张图解释为 end-to-end retrieval latency。

11. nDCG@10 Quality–Latency Figure
nDCG@10 质量–时延图为：

results/budgeted/coarse_to_fine/summary/figures/day5_quality_latency_nDCG10_fixed.png

该图显示：

N	nDCG@10	Latency ms/query
10	0.1033	10.814267
20	0.1033	8.275533
50	0.1033	7.613867
100	0.1033	7.747500
Full MV quality reference 为 nDCG@10 = 0.0807。

主要观察：

C2F 各 N 的 nDCG@10 完全一致；
C2F 的 nDCG@10 高于当前 Full MV reference；
不同 N 的 latency 只表现为运行波动，而不是候选规模带来的真实差异；
N=50 看起来 latency 最低，但这不能说明 N=50 是真实最佳。
原因是：

N=10、20、50、100 的实际候选数全部为 10，latency 差异主要来自系统运行波动、文件读取缓存和 numpy 调用状态，而不是候选规模差异。

12. Best N 分析
根据 Day 5 曲线和数据，当前 best N 可以从两个角度分析。

12.1 按原则选择 best trade-off
如果按照“效果不下降且 rerank cost 最小”的原则：

Best Type	N	Recall@10	nDCG@10	Rerank Cost
Principled best trade-off	10	0.2500	0.1033	10.0000
当前 N=10、20、50、100 的实际 rerank cost 全部为 10，效果也完全相同。

因此，从名义候选预算角度看，N=10 是最保守、最合理的临时 best trade-off。

12.2 按实测 latency 选择最低点
如果只看 measured latency：

Best Type	N	Recall@10	nDCG@10	Latency ms/query
Lowest measured latency	50	0.2500	0.1033	7.613867
但这个结论不能作为真实最佳 N。

原因是：

N=50 并没有真的 rerank 50 个 candidates；
N=50 实际仍然 rerank 10 个 candidates；
低 latency 主要来自测量波动；
不能说明 N=50 比 N=10 更高效。
因此，本日最终采用的 best N 判断是：

在当前 limited-depth coarse run 下，N=10 是最合理的临时 best trade-off。

13. 质量损失阶段分析
Day 5 进一步确认，当前质量瓶颈主要发生在 coarse stage。

依据如下：

阶段	指标	数值
Coarse stage	Coarse Recall	0.2667
C2F final	Recall@10	0.2500
两者非常接近。

这说明：

coarse retriever 能召回 relevant page 的 query，fine reranker 大多能够保留到 top-10；
C2F final Recall@10 没有明显低于 coarse recall 上限；
大多数失败 query 不是 reranker 排序失败，而是在 coarse candidate generation 阶段已经丢失 gold page；
当前应优先改进 coarse retriever，而不是继续微调 reranker。
因此可以写成：

The main quality loss occurs at the coarse retrieval stage. Once the relevant page enters the candidate set, the Full MV reranker largely preserves it within the top-10 results.

14. 对 C2F 是否值得继续推进的判断
当前 C2F pipeline 值得继续推进。

理由如下：

Pipeline 已完整跑通

已经实现 candidate generation、Full MV reranking、evaluation、latency summary 和 curve plotting。

C2F 在低 rerank cost 下保持可用质量

C2F 使用约 10 scored pages/query，达到 Recall@10 = 0.2500 和 nDCG@10 = 0.1033。

Fine reranker 没有明显破坏 coarse 结果

C2F Recall@10 接近 coarse recall 上限，说明 reranking 逻辑基本可靠。

未来有提升空间

如果重新生成 top-20、top-50、top-100 coarse candidates，或引入 BM25 / hybrid retriever，C2F 可以继续形成真实质量–成本曲线。

当前限制是：

C2F 的优势还没有在真实 N scaling 条件下被验证，因为候选集深度不足。

15. 图注草稿
以下图注可用于论文草稿或阶段性报告：

Figure 1: Coarse-to-Fine Retrieval Quality–Cost Curve.

The x-axis denotes reranking cost measured by the number of scored candidate pages per query, while the y-axis reports Recall@10 and nDCG@10. The figure compares the single-vector coarse baseline, the full multi-vector baseline, and C2F results under different nominal candidate budgets. In the current experiment, C2F N=10, 20, 50, and 100 all use the same actual candidate depth of 10 pages/query due to the limited depth of the coarse retrieval run. Therefore, the C2F points overlap in the cost–quality space. This figure should be interpreted as a pipeline validation result rather than a complete budget-scaling curve.

16. 今日验收结果
Day 5 验收标准完成情况如下：

验收项	状态
第一张质量–成本曲线图生成	Completed
Recall@10 quality-cost 图生成	Completed
nDCG@10 quality-cost 图生成	Completed
Recall@10 quality-latency 图生成	Completed
nDCG@10 quality-latency 图生成	Completed
Combined quality-cost 图生成	Completed
best N 分析完成	Completed
图注草稿完成	Completed
质量损失阶段分析完成	Completed
是否继续推进 C2F 的判断完成	Completed
Day 5 的目标已完成。

17. 今日结论
Day 5 已完成第一版 coarse-to-fine 质量–成本曲线绘制，并完成当前 best N 分析。

今日核心结论如下：

当前 C2F N=10、20、50、100 在图中重合；
重合原因不是绘图错误，而是所有 N 的实际候选深度均为 10；
C2F 在 rerank cost = 10 pages/query 下达到 Recall@10 = 0.2500；
C2F 的 nDCG@10 为 0.1033；
当前 Full MV baseline 的 Recall@10 为 0.1333，nDCG@10 为 0.0807；
C2F 的最终 Recall@10 接近 Day 2 coarse recall 上限 0.2667；
当前质量损失主要发生在 coarse retrieval stage；
当前最合理的临时 best N 是 N=10；
C2F pipeline 值得继续推进；
但最终质量–成本曲线需要基于真正 top-20、top-50、top-100 candidates 重新绘制。
最终判断：

当前 Day 5 图已经可以作为 pipeline validation figure 使用，但不能作为最终论文主图。要形成真正的 quality–cost trade-off curve，需要重新生成更深的 coarse candidates 或引入更强的 coarse retriever。