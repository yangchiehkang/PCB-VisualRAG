# Week 4 Day 2 Coarse Candidate Pipeline Log

**Project:** PCB_VisualRAG_Project  
**Stage:** Week 4  
**Day:** Day 2  
**Date:** 2026-05-07  
**Experiment Name:** Single-vector Coarse Retrieval Candidate Pipeline  
**Author:** 杨杰康  
**Status:** Completed  

---

## 1. 今日目标

今日目标是实现 Week 4 coarse-to-fine retrieval 的第一阶段：coarse retrieval candidate pipeline。

本日重点不是执行最终 reranking，而是从已有的 single-vector visual run 文件中读取全库排序结果，并为每个 query 输出不同候选深度下的 top-N 候选页面集合。

今日需要重点确认：

- coarse retriever 是否能稳定召回相关页面；
- 哪个 N 起能够避免明显 recall 损失；
- 哪些 query 在 coarse 阶段已经丢失答案；
- 后续 Full MV reranker 的候选输入是否已经准备完成。

---

## 2. 输入文件

| 类型 | 路径 |
|---|---|
| Coarse run | `results/baselines/single_vector_visual_run.tsv` |
| Qrels | `data/metadata/qrels.tsv` |

---

## 3. 输出文件

| 类型 | 路径 |
|---|---|
| All candidates | `artifacts\rerank_cache\single_vector_topN\single_vector_candidates_all.tsv` |
| Top-10 candidates | `artifacts/rerank_cache/single_vector_topN/single_vector_candidates_top10.tsv` |
| Top-20 candidates | `artifacts/rerank_cache/single_vector_topN/single_vector_candidates_top20.tsv` |
| Top-50 candidates | `artifacts/rerank_cache/single_vector_topN/single_vector_candidates_top50.tsv` |
| Top-100 candidates | `artifacts/rerank_cache/single_vector_topN/single_vector_candidates_top100.tsv` |
| Coarse recall summary | `results\budgeted\coarse_to_fine\single_vector_coarse_recall.csv` |
| Coarse failure cases | `results\budgeted\coarse_to_fine\single_vector_coarse_failure_cases.csv` |

---

## 4. Candidate 文件格式

候选文件统一使用 TSV 格式，字段如下：

| 字段 | 说明 |
|---|---|
| `query_id` | 查询编号 |
| `candidate_page_id` | 候选页面编号 |
| `coarse_rank` | coarse 阶段排名 |
| `coarse_score` | coarse 阶段得分 |

---

## 5. Coarse Recall 统计结果

本日统计 single-vector coarse retriever 在不同候选深度下是否召回 gold page。

| Candidate Depth | Evaluated Queries | Hit Queries | Miss Queries | Coarse Recall |
|---|---:|---:|---:|---:|
| Top-10 | 30 | 8 | 22 | 0.2667 |
| Top-20 | 30 | 8 | 22 | 0.2667 |
| Top-50 | 30 | 8 | 22 | 0.2667 |
| Top-100 | 30 | 8 | 22 | 0.2667 |

---

## 6. 今日观察

本日完成了 coarse retrieval candidate pipeline，并生成了 top-10、top-20、top-50、top-100 四组候选文件。

关键观察如下：

- coarse recall 是 coarse-to-fine 系统的上限；
- 如果 gold page 未进入 coarse top-N，后续 Full MV reranking 无法恢复该 query；
- N 越大，coarse 阶段漏召回风险越低，但后续 reranking 成本也会增加；
- 当前结果将直接决定 Day 3 的 Full MV reranking 是否有足够候选基础。

当前关于候选规模的初步判断：

> 当前 single-vector coarse 在所有测试 N 下仍存在漏召回，需要在后续实验中重点关注 coarse recall 上限。

---

## 7. 粗召回失败样例记录

粗召回失败样例已保存至：

| 文件 | 说明 |
|---|---|
| `results\budgeted\coarse_to_fine\single_vector_coarse_failure_cases.csv` | 记录不同 N 下 gold page 未进入候选集的 query |

该文件包含：

- query_id；
- candidate size N；
- relevant pages；
- top candidates；
- gold page 在 full ranking 中的最好排名；
- failure reason。

---

## 8. 今日结论

Day 2 已完成 coarse retrieval 与 candidate pipeline。

今日产出已经满足 Day 3 Full MV reranking 的输入要求：

- 每个 query 已有 top-N candidate pages；
- 候选文件格式已统一；
- coarse recall 已完成统计；
- coarse 阶段失败样例已记录。

下一步将进入 Day 3：

> 在 top-N 候选集合内接入 Full Multi-vector Late Interaction reranker，并分别生成 N=10、20、50、100 的 rerank run 文件。

Week 4 Day 2 Coarse Candidate Pipeline Log
Project: PCB_VisualRAG_Project

Stage: Week 4

Day: Day 2

Date: 2026-05-07

Experiment Name: Single-vector Coarse Retrieval Candidate Pipeline

Author: 杨杰康

Status: Completed

1. 今日目标
今日目标是实现 Week 4 coarse-to-fine retrieval 的第一阶段：coarse retrieval candidate pipeline。

本日重点不是执行最终 reranking，而是从已有的 single-vector visual retrieval run 文件中读取全库排序结果，并为每个 query 输出不同候选深度下的 top-N 候选页面集合。

今日需要完成以下任务：

调用 single-vector coarse retriever 的已有 run 文件；
为每个 query 输出 top-10、top-20、top-50、top-100 候选页面；
保存统一 candidate 文件；
统计 coarse Recall@10、Recall@20、Recall@50、Recall@100；
记录 coarse 阶段已经漏召回的 query；
为 Day 3 的 Full MV reranking 准备候选输入。
2. 实验背景
Week 4 的核心目标是构建 coarse-to-fine 两阶段检索框架。

整体流程为：

Query
Single-vector Visual Coarse Retriever
Top-N Candidate Pages
Full Multi-vector Late Interaction Reranker
Final Top-k Ranking
Evaluation + Cost Analysis
Day 2 位于该流程的第一阶段，主要关注 coarse retriever 是否能把 relevant page 召回到候选集合中。

由于后续 fine reranker 只能在候选集合内重新排序，如果 gold page 没有进入 coarse top-N，那么后续 Full MV reranking 无法恢复该 query。

因此，coarse recall 是 coarse-to-fine 系统的理论上限约束。

3. 输入文件
今日使用的输入文件如下：

类型	路径
Coarse run	results/baselines/single_vector_visual_run.tsv
Qrels	data/metadata/qrels.tsv
其中：

single_vector_visual_run.tsv 来自 Week 2 的 single-vector visual baseline；
qrels.tsv 是 page-level relevance annotation；
本日 evaluation 仍以 page-level 为主。
4. 输出文件
今日生成的主要输出文件如下：

类型	路径
All candidates	artifacts/rerank_cache/single_vector_topN/single_vector_candidates_all.tsv
Top-10 candidates	artifacts/rerank_cache/single_vector_topN/single_vector_candidates_top10.tsv
Top-20 candidates	artifacts/rerank_cache/single_vector_topN/single_vector_candidates_top20.tsv
Top-50 candidates	artifacts/rerank_cache/single_vector_topN/single_vector_candidates_top50.tsv
Top-100 candidates	artifacts/rerank_cache/single_vector_topN/single_vector_candidates_top100.tsv
Coarse recall CSV	results/budgeted/coarse_to_fine/single_vector_coarse_recall.csv
Coarse recall JSON	results/budgeted/coarse_to_fine/single_vector_coarse_recall.json
Failure cases	results/budgeted/coarse_to_fine/single_vector_coarse_failure_cases.csv
Day 2 note	notes/archive/week4_raw/2026-05-07_week4_day2_coarse_candidate_pipeline.md
5. 使用脚本
今日使用脚本如下：

脚本	作用
scripts/retrieval/build_single_vector_coarse_candidates.py	从 single-vector visual run 中构建 top-N candidates，并统计 coarse recall
执行命令为：python scripts\retrieval\build_single_vector_coarse_candidates.py

脚本成功读取了：

30 条 query 的 coarse run；
30 条 query 的 qrels；
并完成 candidate 文件、coarse recall 文件和 failure case 文件输出。
6. Candidate 文件格式
候选文件统一使用 TSV 格式，字段如下：

字段	说明
query_id	查询编号
candidate_page_id	候选页面编号
coarse_rank	coarse 阶段排名
coarse_score	coarse 阶段得分
生成的 candidate 文件包括：

文件	说明
single_vector_candidates_all.tsv	所有可用 coarse candidates
single_vector_candidates_top10.tsv	Top-10 candidates
single_vector_candidates_top20.tsv	Top-20 candidates
single_vector_candidates_top50.tsv	Top-50 candidates
single_vector_candidates_top100.tsv	Top-100 candidates
7. 文件生成检查
运行后检查 artifacts/rerank_cache/single_vector_topN/ 目录，结果如下：

文件	大小
single_vector_candidates_all.tsv	9,383 bytes
single_vector_candidates_top10.tsv	9,383 bytes
single_vector_candidates_top20.tsv	9,383 bytes
single_vector_candidates_top50.tsv	9,383 bytes
single_vector_candidates_top100.tsv	9,383 bytes
当前观察到一个重要现象：

top-10、top-20、top-50、top-100 和 all candidates 文件大小完全相同。

这说明当前 single_vector_visual_run.tsv 中每个 query 可能只保存了有限数量的候选，实际候选深度没有覆盖到 20、50、100。

因此，本日 coarse recall 结果中 top-10、top-20、top-50、top-100 完全一致。

这个现象需要在后续 Day 3 或 Day 4 中注意，因为如果 coarse run 本身只输出了 top-10，那么即使设置 N=100，也无法真正获得 top-100 候选。

8. Coarse Recall 统计结果
今日统计 single-vector coarse retriever 在不同候选深度下是否召回 gold page。

Candidate Depth	Evaluated Queries	Hit Queries	Miss Queries	Coarse Recall
Top-10	30	8	22	0.2667
Top-20	30	8	22	0.2667
Top-50	30	8	22	0.2667
Top-100	30	8	22	0.2667
结果文件为：results/budgeted/coarse_to_fine/single_vector_coarse_recall.csv

文件内容为：

N	Evaluated Queries	Hit Queries	Miss Queries	Coarse Recall
10	30	8	22	0.2667
20	30	8	22	0.2667
50	30	8	22	0.2667
100	30	8	22	0.2667
9. Coarse Recall 结果解读
当前 single-vector visual coarse retriever 的 coarse recall 较低。

主要观察如下：

在 30 条 query 中，只有 8 条 query 的 gold page 进入候选集合；
有 22 条 query 在 coarse 阶段已经漏召回；
coarse Recall@10、@20、@50、@100 全部为 0.2667；
不同 N 下结果完全相同，说明当前 coarse run 的有效候选深度可能没有超过 10；
如果继续使用该候选文件进行 Day 3 reranking，Full MV fine reranker 的理论上限也只有 0.2667。
这说明：

当前 single-vector visual retriever 作为 coarse retriever 的召回能力较弱，可能不足以支撑高质量 coarse-to-fine retrieval。

10. 粗召回失败样例
粗召回失败样例已保存至：results/budgeted/coarse_to_fine/single_vector_coarse_failure_cases.csv

该文件记录了不同 N 下 gold page 未进入候选集的 query。

主要字段如下：

字段	说明
query_id	查询编号
N	候选深度
relevant_pages	gold page
top_candidates	coarse 阶段 top candidates
best_relevant_rank_if_available	gold page 在 coarse ranking 中的最好排名
failure_reason	失败原因
本日发现的失败 query 包括：

Query ID	Relevant Page
q005	doc001_p005
q006	doc002_p001
q007	doc002_p001
q008	doc003_p007
q009	doc003_p008
q010	doc003_p009
q011	doc003_p010
q012	doc003_p011
q013	doc003_p012
q014	doc003_p013
q015	doc003_p014
q016	doc003_p015
q017	doc003_p016
q018	doc003_p017
q019	doc003_p018
q020	doc003_p019
q021	doc003_p020
q023	doc003_p023
q026	doc003_p026
q027	doc003_p027
q029	doc003_p007; doc003_p010
q030	doc003_p008; doc003_p011
这些 query 在当前 single-vector visual coarse ranking 中没有进入 top-N 候选，因此后续 fine reranking 无法恢复。

11. 今日关键发现
11.1 Single-vector visual coarse recall 很低
当前 single-vector visual retriever 的 coarse recall 只有 0.2667。

这意味着如果使用该方法作为唯一 coarse retriever，后续 C2F 系统即使 fine reranker 很强，也只能在较低上限内工作。

换句话说，当前两阶段系统的瓶颈首先不是 fine reranker，而是 coarse retriever 的候选召回能力。

11.2 当前 coarse run 可能只包含 top-10
不同 N 的候选文件大小完全相同，并且 coarse Recall@10、@20、@50、@100 完全一致。

这说明当前输入 run 文件很可能只保存了每个 query 的 top-10 ranking。

因此，今天的 top-20、top-50、top-100 并不是真正意义上的更大候选预算，而只是从有限候选池中重复截断。

这个问题需要在后续实验中处理：

如果继续使用 single-vector visual coarse，需要重新生成 top-100 run；
或者改用已有完整排序的 coarse run；
或者引入 BM25 coarse 作为更强候选召回器。
12. 对 Day 3 的影响
Day 3 原计划是在 top-N 候选上接入 Full MV reranking。

根据今日结果，需要注意：

如果直接使用当前 single-vector candidates，Day 3 reranking 的 recall 上限只有 0.2667；
N=10、20、50、100 的候选集合实际可能相同；
因此 Day 3 的不同 N 对比可能无法体现真实候选预算差异；
Day 3 可以先完成 pipeline 跑通，但需要在记录中明确指出 coarse candidate depth 的限制；
后续可能需要补充一个更强 coarse retriever，例如 BM25 top-N + Full MV reranking。
13. 今日验收结果
Day 2 验收标准完成情况如下：

验收项	状态
coarse retriever run 文件成功读取	Completed
top-10 candidate 文件生成	Completed
top-20 candidate 文件生成	Completed
top-50 candidate 文件生成	Completed
top-100 candidate 文件生成	Completed
coarse recall 统计完成	Completed
coarse failure cases 记录完成	Completed
Day 2 实验日志完成	Completed
14. 今日结论
Day 2 已完成 coarse retrieval 与 candidate pipeline。

今日实验结果表明：

single-vector visual coarse retriever 可以生成候选集合；
candidate 文件格式已经统一；
coarse recall 统计流程已经跑通；
failure case 记录已经生成；
但当前 single-vector visual coarse recall 较低；
当前 coarse run 可能只包含 top-10，因此 top-20、top-50、top-100 的候选深度没有真正展开。
本日核心结论是：

当前 single-vector visual retriever 作为 coarse retriever 的召回能力不足，coarse Recall@10 至 Recall@100 均为 0.2667。这说明如果直接使用该方法进行 coarse-to-fine retrieval，最终系统性能将受到严重的 candidate recall 上限约束。

Day 3 可以继续接入 Full MV reranking 以验证 pipeline，但需要在后续分析中明确：

当前 C2F 的主要风险来自 coarse 阶段漏召回，而不是 fine reranker 本身。