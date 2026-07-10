Week 4 Day 3 Coarse-to-Fine Full MV Reranking Log
Project: PCB_VisualRAG_Project

Stage: Week 4

Day: Day 3

Date: 2026-05-07

Experiment Name: Coarse-to-Fine Full Multi-vector Reranking

Author: 杨杰康

Status: Completed

1. 今日目标
今日目标是在 Day 2 生成的 top-N candidate pages 上接入 Week 3 已经跑通的 Full Multi-vector Late Interaction reranker，完成 coarse-to-fine 管线的 second-stage reranking。

本日重点是让 Full MV 不再对全库页面执行 late interaction，而是仅在 coarse retriever 给出的候选集合内进行精排。

今日需要完成以下任务：

设计 rerank 输入接口；
读取 Day 2 生成的 top-N candidate files；
复用 Week 3 的 query token embeddings；
复用 Week 3 的 page multi-vector embeddings；
对每个 N 独立执行 Full MV late interaction reranking；
输出 N=10、20、50、100 对应的 rerank run 文件；
验证 reranking 是否严格限制在候选集合内；
生成 subset validation log 和 rerank summary。
2. 实验背景
Week 4 的核心任务是构建一个可控制候选规模的 coarse-to-fine retrieval 框架。

Day 2 已经完成 coarse candidate pipeline，使用 single-vector visual retrieval 作为 coarse retriever，并输出了不同 N 下的候选集合。

Day 3 在此基础上接入 Full MV reranker。

整体流程为：

Query
Single-vector Visual Coarse Retriever
Top-N Candidate Pages
Full Multi-vector Late Interaction Reranker
Final Top-k Ranking
Evaluation + Cost Analysis
本日实验关注的是：

Full MV reranker 是否能够在候选集合内正常运行，并为每个 query 输出重新排序后的 top-k 页面。

3. 输入文件
今日使用的输入文件如下：

类型	路径
Top-10 candidates	artifacts/rerank_cache/single_vector_topN/single_vector_candidates_top10.tsv
Top-20 candidates	artifacts/rerank_cache/single_vector_topN/single_vector_candidates_top20.tsv
Top-50 candidates	artifacts/rerank_cache/single_vector_topN/single_vector_candidates_top50.tsv
Top-100 candidates	artifacts/rerank_cache/single_vector_topN/single_vector_candidates_top100.tsv
Query embeddings	artifacts/embeddings/full_multivector/queries/*.npy
Page embeddings	artifacts/embeddings/full_multivector/pages/*.npy
其中：

candidate files 来自 Day 2；
query embeddings 复用 Week 3 的 projected token-level query embeddings；
page embeddings 复用 Week 3 的 projected visual token embeddings；
query/page embeddings 均位于 CLIP shared projection space；
page embedding shape 为 (49, 512)；
query embedding 为 token-level projected text embeddings。
4. 输出文件
今日生成的主要输出文件如下：

类型	路径
N=10 run	results/budgeted/coarse_to_fine/c2f_single_vector_N10_run.tsv
N=20 run	results/budgeted/coarse_to_fine/c2f_single_vector_N20_run.tsv
N=50 run	results/budgeted/coarse_to_fine/c2f_single_vector_N50_run.tsv
N=100 run	results/budgeted/coarse_to_fine/c2f_single_vector_N100_run.tsv
N=10 alias run	results/budgeted/coarse_to_fine/c2f_N10_run.tsv
N=20 alias run	results/budgeted/coarse_to_fine/c2f_N20_run.tsv
N=50 alias run	results/budgeted/coarse_to_fine/c2f_N50_run.tsv
N=100 alias run	results/budgeted/coarse_to_fine/c2f_N100_run.tsv
N=10 scores	results/budgeted/coarse_to_fine/c2f_single_vector_N10_scores.csv
N=20 scores	results/budgeted/coarse_to_fine/c2f_single_vector_N20_scores.csv
N=50 scores	results/budgeted/coarse_to_fine/c2f_single_vector_N50_scores.csv
N=100 scores	results/budgeted/coarse_to_fine/c2f_single_vector_N100_scores.csv
N=10 validation	results/budgeted/coarse_to_fine/c2f_single_vector_N10_validation.csv
N=20 validation	results/budgeted/coarse_to_fine/c2f_single_vector_N20_validation.csv
N=50 validation	results/budgeted/coarse_to_fine/c2f_single_vector_N50_validation.csv
N=100 validation	results/budgeted/coarse_to_fine/c2f_single_vector_N100_validation.csv
Day 3 summary CSV	results/budgeted/coarse_to_fine/c2f_single_vector_day3_rerank_summary.csv
Day 3 summary JSON	results/budgeted/coarse_to_fine/c2f_single_vector_day3_rerank_summary.json
Validation log	notes/archive/week4_raw/2026-05-07_week4_day3_subset_validation_log.md
5. 使用脚本
今日使用脚本如下：

脚本	作用
scripts/retrieval/run_c2f_full_mv_rerank.py	在 top-N candidates 上执行 Full MV late interaction reranking
执行命令为：python scripts\retrieval\run_c2f_full_mv_rerank.py

脚本完成了以下操作：

读取 Day 2 生成的 candidate files；
按 query 加载 query embeddings；
按 candidate page 加载 page embeddings；
对 query tokens 和 page visual tokens 计算 late interaction score；
对每个 query 的候选页面按 fine score 重新排序；
为 N=10、20、50、100 分别输出 run 文件；
生成 validation 文件检查 reranking 是否只发生在候选集合内；
生成 rerank summary 统计运行耗时和候选数量。
6. Reranking 方法
今日 fine reranker 采用 Week 3 已经实现的 Full Multi-vector Late Interaction。

scoring 函数为：

S
c
o
r
e
(
q
,
d
)
=
∑
i
=
1
∣
Q
∣
max
⁡
j
=
1
∣
D
∣
s
i
m
(
q
i
,
d
j
)
Score(q,d)=∑ 
i=1
∣Q∣
​
 max 
j=1
∣D∣
​
 sim(q 
i
​
 ,d 
j
​
 )

其中：

q
i
q 
i
​
  表示 query 的第 
i
i 个 token embedding；
d
j
d 
j
​
  表示页面的第 
j
j 个 visual token embedding；
s
i
m
(
q
i
,
d
j
)
sim(q 
i
​
 ,d 
j
​
 ) 表示 query token 与 page visual token 的相似度。
本日 reranking 只在 coarse candidate set 内执行，不再对全库页面执行 Full MV matching。

7. 脚本运行结果
脚本运行成功，终端输出显示：

N	Queries	Total Scored	Avg Latency / Query
10	30	300	10.814273 ms
20	30	300	8.275523 ms
50	30	300	7.613857 ms
100	30	300	7.747487 ms
完整 summary 文件为：

results/budgeted/coarse_to_fine/c2f_single_vector_day3_rerank_summary.csv

其内容如下：

N	Query Count	Total Candidates	Total Scored	Avg Candidates / Query	Avg Scored / Query	Rerank Time Seconds	Avg Rerank Latency / Query
10	30	300	300	10.0000	10.0000	0.324428	10.814273 ms
20	30	300	300	10.0000	10.0000	0.248266	8.275523 ms
50	30	300	300	10.0000	10.0000	0.228416	7.613857 ms
100	30	300	300	10.0000	10.0000	0.232425	7.747487 ms
8. Validation 结果
今日对 N=10 和 N=100 的 validation 文件进行了检查。

N=10 validation 文件为：

results/budgeted/coarse_to_fine/c2f_single_vector_N10_validation.csv

检查结果显示：

30 条 query 均成功读取候选页面；
每条 query 输入候选数为 10；
每条 query reranked candidate 数为 10；
所有 query 的 subset check 均为 PASSED。
N=100 validation 文件为：

results/budgeted/coarse_to_fine/c2f_single_vector_N100_validation.csv

检查结果显示：

30 条 query 均成功读取候选页面；
每条 query 输入候选数仍为 10；
每条 query reranked candidate 数仍为 10；
所有 query 的 subset check 均为 PASSED。
这说明：

reranking 逻辑已经正确限制在候选集合内，没有发生候选集合外页面被 rerank 的情况。

9. 重要发现：不同 N 实际候选数相同
今日最重要的观察是：

N=10、20、50、100 的实际候选数量均为 300，即每条 query 平均只有 10 个候选页面。

具体表现为：

N	Total Candidates	Avg Candidates / Query
10	300	10.0000
20	300	10.0000
50	300	10.0000
100	300	10.0000
这与 Day 2 的发现一致：

single_vector_candidates_top10.tsv
single_vector_candidates_top20.tsv
single_vector_candidates_top50.tsv
single_vector_candidates_top100.tsv
这些文件大小完全相同。

因此，当前并没有真正形成不同候选预算下的 reranking 对比。

原因很可能是：

Week 2 的 single_vector_visual_run.tsv 原始 run 文件每个 query 只保存了 top-10 结果，因此 Day 2 无法从该文件中截取 top-20、top-50 或 top-100 候选。

10. Run 文件检查
今日检查了 c2f_single_vector_N10_run.tsv 的内容。

run 文件格式如下：

字段	说明
run_name	实验名称
query_id	Query ID
page_id	Reranked page ID
rank	Fine reranker 排名
score	Full MV late interaction score
示例观察：

Query	Top-1 Page	Top-1 Fine Score
q001	doc006_p008	1.07069719
q002	doc001_p002	0.50915086
q003	doc003_p013	0.06804084
q004	doc001_p002	0.84752858
q005	doc004_p012	0.16846004
这说明 Full MV fine reranker 已经成功对候选页面重新打分，并生成新的排序。

11. 与 Day 2 的关系
Day 2 已经发现 single-vector coarse retriever 的 coarse recall 较低：

Candidate Depth	Coarse Recall
Top-10	0.2667
Top-20	0.2667
Top-50	0.2667
Top-100	0.2667
Day 3 的 reranking 结果进一步确认：

当前 pipeline 能够正常运行；
但候选输入本身只有 top-10；
因此不同 N 的 rerank 不具备真实 budget 差异；
后续 Day 4 如果直接评测这些 run 文件，N=10、20、50、100 的指标大概率会相同或非常接近；
当前实验更适合作为 C2F pipeline validation，而不是最终质量–成本曲线实验。
12. 当前瓶颈分析
今日实验说明，coarse-to-fine 框架的技术链路已经跑通，但当前结果存在两个主要限制。

12.1 Candidate depth 限制
当前 single-vector coarse run 很可能只包含每个 query 的 top-10 页面。

因此，即使设置 N=20、50、100，也无法真正扩大候选集合。

这会导致：

不同 N 的 total candidates 相同；
不同 N 的 rerank cost 接近；
不同 N 的 retrieval quality 接近；
无法绘制真实质量–成本曲线。
12.2 Coarse recall 限制
Day 2 的 coarse recall 只有 0.2667。

这意味着：

有 22 条 query 的 gold page 在 coarse 阶段已经丢失；
Full MV reranker 无法恢复这些 query；
当前 C2F 的上限被 single-vector coarse 严重限制；
即使 fine reranker 排序能力更强，也无法解决 coarse 漏召回问题。
13. 今日验收结果
Day 3 验收标准完成情况如下：

验收项	状态
rerank 输入接口完成	Completed
top-N candidate files 成功读取	Completed
query embeddings 成功加载	Completed
page multi-vector embeddings 成功加载	Completed
Full MV late interaction scoring 成功运行	Completed
N=10 run 文件生成	Completed
N=20 run 文件生成	Completed
N=50 run 文件生成	Completed
N=100 run 文件生成	Completed
score debug 文件生成	Completed
validation 文件生成	Completed
subset check 验证通过	Completed
Day 3 summary 生成	Completed
14. 今日结论
Day 3 已成功完成 coarse-to-fine second-stage reranking pipeline。

今日实验确认：

Full MV reranker 可以接入 Day 2 的 candidate files；
query token embeddings 与 page multi-vector embeddings 可以正常复用；
late interaction scoring 能够在候选集合内稳定运行；
reranking 输出格式符合 run 文件要求；
validation 显示所有 reranked pages 均来自候选集合；
N=10、20、50、100 的 run 文件均已生成。
但今日也确认了一个关键限制：

当前 single-vector visual coarse run 实际只提供了每条 query 约 10 个候选页面，因此 N=20、50、100 并没有真正扩大候选预算。

因此，今日的主要结论是：

Coarse-to-fine reranking pipeline 已经跑通，但当前 single-vector coarse candidate depth 与 coarse recall 均不足，导致该实验暂时只能验证流程正确性，尚不能形成有效的不同 N 质量–成本对比。

15. 对 Day 4 的影响
Day 4 原计划是系统跑出不同 N 下的效果与时延结果。

根据 Day 3 当前结果，Day 4 需要注意：

可以继续评测 N=10、20、50、100 的 run 文件；
但必须在分析中说明当前不同 N 的实际候选数都为 10；
因此这些 N 的结果不能代表真实候选预算变化；
Day 4 应重点确认 C2F reranking 的 page-level metrics；
同时建议补充生成更深的 coarse run，或引入 BM25 coarse 作为候选召回器。
Day 4 如果要继续推进，有两个可选方向：

方向	说明
路线 A	评测当前 C2F run，完成 pipeline 闭环
路线 B	重新生成 top-100 coarse run，再做真正 N=10、20、50、100 对比
当前建议：

先完成路线 A，获得 C2F pipeline 的完整评测闭环；随后再补充路线 B，解决真实候选预算不足的问题。