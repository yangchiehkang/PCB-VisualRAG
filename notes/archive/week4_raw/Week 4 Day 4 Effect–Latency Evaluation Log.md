Week 4 Day 4 Effect–Latency Evaluation Log
Project: PCB_VisualRAG_Project

Stage: Week 4

Day: Day 4

Date: 2026-05-07

Experiment Name: Coarse-to-Fine Retrieval Effect–Latency Evaluation

Author: 杨杰康

Status: Completed

1. 今日目标
今日目标是在正式实验集上运行不同候选规模 N 下的 coarse-to-fine retrieval 评测，获得 效果指标 与 时延指标 的初版对比结果。

本日重点是把 Day 2 和 Day 3 已经跑通的 C2F pipeline 闭环起来：

Day 2：生成 single-vector coarse candidates；
Day 3：在 candidates 内执行 Full MV late interaction reranking；
Day 4：对 reranked run 文件进行正式 evaluation，并输出效果–时延对比表。
今日需要完成以下任务：

对 C2F N=10、20、50、100 分别运行完整评测；
计算 Recall@1、Recall@5、Recall@10、MRR@10、nDCG@10；
汇总 rerank latency、per-query latency；
自动查找并评测 Full Multi-vector baseline；
输出 c2f_summary.csv 和 c2f_summary.xlsx；
生成初版效果–时延对比表；
分析不同 N 下的趋势与限制。
2. 实验背景
Week 4 的目标是验证 coarse-to-fine retrieval 是否能够在保持较好检索效果的同时降低 Full MV 的计算成本。

理论上，coarse-to-fine retrieval 的优势来自两阶段设计：

Coarse stage 使用较便宜的 single-vector retriever 从全库中快速召回 top-N candidates；
Fine stage 只在 top-N candidates 内执行更昂贵的 Full Multi-vector Late Interaction reranking。
理想情况下，随着 N 从 10 增大到 100：

检索效果应该逐渐提高或趋于饱和；
rerank latency 应该随 N 近似线性增长；
小 N 若能接近 Full MV，则说明 C2F 有较好的性价比；
如果小 N 明显低于 Full MV，则说明 coarse candidate recall 不足。
不过，Day 2 和 Day 3 已经发现当前实验存在一个重要限制：

当前 single-vector coarse run 实际每个 query 只提供约 10 个候选页面，因此 N=20、50、100 并没有真正扩大候选集合。

因此 Day 4 的结果需要结合这一限制进行解释。

3. 输入文件
今日使用的输入文件如下：

类型	路径
Qrels	data/metadata/qrels.tsv
Full MV run	results/full_multivector/full_mv_run.tsv
C2F N=10 run	results/budgeted/coarse_to_fine/c2f_single_vector_N10_run.tsv
C2F N=20 run	results/budgeted/coarse_to_fine/c2f_single_vector_N20_run.tsv
C2F N=50 run	results/budgeted/coarse_to_fine/c2f_single_vector_N50_run.tsv
C2F N=100 run	results/budgeted/coarse_to_fine/c2f_single_vector_N100_run.tsv
Day 3 latency summary	results/budgeted/coarse_to_fine/c2f_single_vector_day3_rerank_summary.csv
Day 2 coarse recall	results/budgeted/coarse_to_fine/single_vector_coarse_recall.csv
今日脚本成功自动检测到 Full MV baseline 文件：

results/full_multivector/full_mv_run.tsv

4. 输出文件
今日生成的主要输出文件如下：

类型	路径
Metrics by N	results/budgeted/coarse_to_fine/summary/c2f_day4_metrics_by_N.csv
Latency by N	results/budgeted/coarse_to_fine/summary/c2f_day4_latency_by_N.csv
Summary CSV	results/budgeted/coarse_to_fine/summary/c2f_summary.csv
Summary XLSX	results/budgeted/coarse_to_fine/summary/c2f_summary.xlsx
Evaluation summary JSON	results/budgeted/coarse_to_fine/summary/c2f_day4_evaluation_summary.json
Initial effect-latency table	results/budgeted/coarse_to_fine/summary/c2f_day4_initial_effect_latency_table.md
N=10 per-query metrics	results/budgeted/coarse_to_fine/summary/c2f_N10_per_query_metrics.csv
N=20 per-query metrics	results/budgeted/coarse_to_fine/summary/c2f_N20_per_query_metrics.csv
N=50 per-query metrics	results/budgeted/coarse_to_fine/summary/c2f_N50_per_query_metrics.csv
N=100 per-query metrics	results/budgeted/coarse_to_fine/summary/c2f_N100_per_query_metrics.csv
今日共生成 10 个 summary 文件，说明 Day 4 评测流程完整执行成功。

5. 使用脚本
今日使用脚本如下：

脚本	作用
scripts/evaluation/evaluate_c2f_day4.py	对 Full MV 与 C2F N=10、20、50、100 进行效果与时延评测
执行命令为：python scripts\evaluation\evaluate_c2f_day4.py

脚本完成了以下操作：

读取 qrels；
自动查找 Full MV run；
读取 C2F 各 N 的 rerank run；
计算 Recall@1、Recall@5、Recall@10、MRR@10、nDCG@10；
读取 Day 3 的 rerank latency；
读取 Day 2 的 coarse recall；
输出 CSV、XLSX、JSON 和 Markdown summary；
为每个 N 输出 per-query metrics。
6. Evaluation Metrics
今日评测指标包括：

指标	含义
Recall@1	Top-1 中是否召回 relevant page
Recall@5	Top-5 中是否召回 relevant page
Recall@10	Top-10 中是否召回 relevant page
MRR@10	Top-10 内第一个 relevant page 的 reciprocal rank
nDCG@10	考虑排名位置和相关性的归一化折损累计增益
Latency	每 query 平均 rerank latency
Actual Candidates / Query	实际参与 reranking 的候选页面数
其中，Latency 当前主要表示：

cached-candidate setting 下的 Full MV reranking latency。

因为 Day 2 使用的是已经生成好的 coarse candidates，所以本日 coarse_time_seconds_proxy 暂时记为 0。

7. Table 4：Full MV 与 Coarse-to-Fine 检索结果对比
今日核心结果如下：

Method	Recall@1	Recall@5	Recall@10	MRR@10	nDCG@10	Latency	Actual Candidates / Query
Full Multi-vector	0.0333	0.1000	0.1333	0.0644	0.0807		full corpus
C2F N=10	0.0333	0.0333	0.2500	0.0628	0.1033	10.814267 ms/query	10.0000
C2F N=20	0.0333	0.0333	0.2500	0.0628	0.1033	8.275533 ms/query	10.0000
C2F N=50	0.0333	0.0333	0.2500	0.0628	0.1033	7.613867 ms/query	10.0000
C2F N=100	0.0333	0.0333	0.2500	0.0628	0.1033	7.747500 ms/query	10.0000
完整表格文件为：

results/budgeted/coarse_to_fine/summary/c2f_summary.csv

Excel 版本为：

results/budgeted/coarse_to_fine/summary/c2f_summary.xlsx

8. Metrics by N 结果
c2f_day4_metrics_by_N.csv 的结果如下：

Method	N	Evaluated Queries	Recall@1	Recall@5	Recall@10	MRR@10	nDCG@10
Full Multi-vector	full	30	0.0333	0.1000	0.1333	0.0644	0.0807
C2F N=10	10	30	0.0333	0.0333	0.2500	0.0628	0.1033
C2F N=20	20	30	0.0333	0.0333	0.2500	0.0628	0.1033
C2F N=50	50	30	0.0333	0.0333	0.2500	0.0628	0.1033
C2F N=100	100	30	0.0333	0.0333	0.2500	0.0628	0.1033
主要观察：

Full MV 的 Recall@10 为 0.1333；
C2F 各 N 的 Recall@10 均为 0.2500；
Full MV 的 MRR@10 为 0.0644；
C2F 各 N 的 MRR@10 为 0.0628；
Full MV 的 nDCG@10 为 0.0807；
C2F 各 N 的 nDCG@10 为 0.1033；
C2F N=10、20、50、100 的结果完全一致。
9. Latency by N 结果
c2f_day4_latency_by_N.csv 的结果如下：

Method	Query Count	Total Candidates	Total Scored	Avg Candidates / Query	Rerank Time	Per-query Latency
C2F N=10	30	300	300	10.0000	0.324428 s	10.814267 ms
C2F N=20	30	300	300	10.0000	0.248266 s	8.275533 ms
C2F N=50	30	300	300	10.0000	0.228416 s	7.613867 ms
C2F N=100	30	300	300	10.0000	0.232425 s	7.747500 ms
主要观察：

所有 N 的 total candidates 都是 300；
所有 N 的 total scored 都是 300；
每个 query 实际都只 rerank 10 个 candidates；
因此不同 N 的 latency 并不反映真实候选规模变化；
N=20、50、100 的 latency 没有随 N 增大而增长，这是因为实际候选数没有变。
这说明当前 latency 更准确地应解释为：

每 query 10 candidates setting 下的 cached-candidate Full MV reranking latency。

10. 关于 Markdown 显示乱码的说明
今日查看 c2f_day4_initial_effect_latency_table.md 时，终端中出现了中文乱码，例如：

Full MV 涓?Coarse-to-Fine...
褰撳墠 Day 4...
这通常不是文件内容损坏，而是 Windows type 命令在当前 code page 下没有按 UTF-8 正确显示中文。

该问题不影响 CSV、XLSX 和 JSON 结果文件。

后续查看中文 Markdown 文件时，建议使用：

VS Code；
Notepad；
Typora；
或其他支持 UTF-8 的编辑器。
在实验记录中，该问题记为：

Day 4 Markdown 文件在 Windows terminal 中使用 type 查看时出现编码显示异常，但核心评测结果文件已正常生成。

11. 关键发现一：C2F Recall@10 高于当前 Full MV run
今日结果显示：

Method	Recall@10
Full Multi-vector	0.1333
C2F N=10	0.2500
C2F N=20	0.2500
C2F N=50	0.2500
C2F N=100	0.2500
表面上看，C2F 的 Recall@10 高于 Full MV。

这说明当前 C2F pipeline 在已给定候选集合内，能够保留更多 relevant pages 到 top-10。

不过这个结果需要谨慎解释：

C2F 的上限受到 coarse candidates 限制；
Day 2 的 coarse recall 只有 0.2667；
C2F Recall@10 为 0.2500，已经接近 coarse recall 上限；
当前 C2F 的提升不一定说明 C2F 全面优于 Full MV；
还需要检查 Full MV run 的候选范围、排序逻辑和评测口径是否与 C2F 完全一致。
本日可得出的稳健结论是：

在当前 30-query evaluation set 上，C2F reranking 的 Recall@10 达到 0.2500，且没有超过 Day 2 coarse recall 上限，结果逻辑一致。

12. 关键发现二：不同 N 结果完全一致
C2F N=10、20、50、100 的指标完全一致：

N	Recall@10	MRR@10	nDCG@10	Actual Candidates / Query
10	0.2500	0.0628	0.1033	10.0000
20	0.2500	0.0628	0.1033	10.0000
50	0.2500	0.0628	0.1033	10.0000
100	0.2500	0.0628	0.1033	10.0000
这与 Day 2、Day 3 的观察一致。

原因是：

当前 single-vector coarse run 每个 query 实际只提供 top-10 candidates，因此 N=20、50、100 没有真正扩大候选集合。

因此，今日无法观察到理论上应该出现的趋势：

N 增大后 Recall@10 是否提升；
N 增大后 MRR@10 是否变化；
N 增大后 nDCG@10 是否趋于饱和；
rerank time 是否随 N 线性增长。
当前不同 N 的结果完全一致，说明本轮实验完成了 pipeline 闭环，但还不能作为真实候选预算对比实验。

13. 关键发现三：C2F 结果接近 coarse recall 上限
Day 2 的 coarse recall 为：

Candidate Depth	Coarse Recall
Top-10	0.2667
Top-20	0.2667
Top-50	0.2667
Top-100	0.2667
Day 4 的 C2F Recall@10 为：

Method	Recall@10
C2F N=10	0.2500
C2F N=20	0.2500
C2F N=50	0.2500
C2F N=100	0.2500
这说明：

coarse stage 能召回 relevant page 的 query 比例约为 0.2667；
fine reranker 最终在 top-10 中保留 relevant page 的比例为 0.2500；
C2F Recall@10 已经非常接近当前 coarse recall 上限；
当前主要瓶颈仍然在 coarse retrieval，而不是 reranker 是否能在候选集合内工作。
换句话说：

Fine reranker 已经把候选集合内能命中的 relevant pages 基本保留下来了，但 coarse retriever 没有给它足够多的正确候选。

14. 与 Full MV 的对照分析
今日 Full MV baseline 的结果为：

Metric	Full MV
Recall@1	0.0333
Recall@5	0.1000
Recall@10	0.1333
MRR@10	0.0644
nDCG@10	0.0807
C2F 的结果为：

Metric	C2F
Recall@1	0.0333
Recall@5	0.0333
Recall@10	0.2500
MRR@10	0.0628
nDCG@10	0.1033
对比来看：

Recall@1 相同，均为 0.0333；
Full MV 的 Recall@5 更高，为 0.1000；
C2F 的 Recall@10 更高，为 0.2500；
MRR@10 基本接近；
C2F 的 nDCG@10 略高。
这说明 C2F 在当前实验中可能把相关页面放进了 top-10，但未必能稳定提前到 top-5 或 top-1。

因此本日可以得出一个细粒度结论：

当前 C2F 在 Recall@10 上优于检测到的 Full MV run，但在 early precision 指标上并没有明显优势。

15. 时延结果分析
当前 C2F per-query latency 如下：

Method	Per-query Latency
C2F N=10	10.814267 ms/query
C2F N=20	8.275533 ms/query
C2F N=50	7.613867 ms/query
C2F N=100	7.747500 ms/query
由于所有 N 的实际候选数都为 10，因此这里不应解读为：

N 越大速度越快。

更合理的解释是：

每个 N 实际执行的是同样规模的 reranking；
细微 latency 差异来自系统运行波动、文件读取缓存、numpy 调用状态等因素；
当前结果不能用于拟合 N 与 latency 的增长关系；
当前只说明：在每 query 10 candidates 的条件下，Full MV reranking 大约需要 7.6–10.8 ms/query。
因此，今日 latency 的有效结论是：

C2F 在 cached top-10 candidates 上的 reranking latency 约为 8–11 ms/query。

16. 今日验收结果
Day 4 验收标准完成情况如下：

验收项	状态
Full MV run 自动检测	Completed
C2F N=10 评测完成	Completed
C2F N=20 评测完成	Completed
C2F N=50 评测完成	Completed
C2F N=100 评测完成	Completed
Recall@1 / Recall@5 / Recall@10 计算完成	Completed
MRR@10 计算完成	Completed
nDCG@10 计算完成	Completed
latency summary 生成	Completed
per-query metrics 生成	Completed
c2f_summary.csv 生成	Completed
c2f_summary.xlsx 生成	Completed
初版效果–时延表生成	Completed
Day 4 的产出已满足当前阶段的验收要求。

17. 当前限制
今日实验虽然完成了完整闭环，但仍有几个限制需要明确记录。

17.1 当前 N 不是真实候选预算
N=20、50、100 的实际候选数仍然是 10。

因此：

不能说明 N=100 与 N=10 效果相同；
只能说明当前输入候选文件相同；
真实 N 对比需要重新生成更深的 coarse run。
17.2 coarse time 不是在线测得
今日 coarse_time_seconds_proxy 为 0。

原因是：

Day 2 使用的是已有 coarse run；
Day 4 没有在线执行 single-vector coarse retrieval；
因此总时延目前只包含 rerank time；
后续如果要报告 end-to-end latency，需要补测 coarse retrieval time。
17.3 Full MV latency 未自动填入
今日自动找到了 Full MV run，并评测了 Full MV 效果指标。

但 Full MV latency 没有自动填入，需要后续从 Week 3 的 cost log 或 full-mv timing summary 中补充。

18. 今日结论
Day 4 已成功完成 C2F 在正式 evaluation set 上的效果与时延评测。

今日核心结论如下：

C2F N=10、20、50、100 的 run 文件均成功评测；
Full MV baseline 被自动检测并完成评测；
C2F 在当前设置下 Recall@10 为 0.2500；
Full MV 当前 Recall@10 为 0.1333；
C2F 的 MRR@10 为 0.0628，与 Full MV 的 0.0644 接近；
C2F 的 nDCG@10 为 0.1033，高于 Full MV 的 0.0807；
C2F 的 per-query rerank latency 约为 7.6–10.8 ms/query；
当前 N=10、20、50、100 实际候选数都为 10，因此无法形成真实候选预算曲线；
当前 C2F Recall@10 接近 Day 2 coarse recall 上限，说明主要瓶颈仍在 coarse retriever。
本日最重要的判断是：

当前 coarse-to-fine pipeline 已经完整跑通，并首次获得效果–时延对比结果；但由于 single-vector coarse run 只有 top-10 深度，本轮 Day 4 结果主要证明 pipeline 可行，还不能证明不同 N 下的真实质量–成本趋势。

19. 对 Day 5 的影响
Day 5 应重点分析失败样例与 bottleneck。

基于 Day 4 结果，Day 5 建议重点检查：

C2F 命中的 8 条 query 中，fine reranker 是否把 relevant page 提升到更靠前位置；
C2F 未命中的 22 条 query 中，gold page 是否已经在 coarse 阶段丢失；
Full MV 与 C2F 的差异 query；
为什么 C2F Recall@10 高于 Full MV，但 Recall@5 更低；
是否存在 visual similarity 误匹配；
是否需要重新生成 top-100 coarse candidates；
是否引入 BM25 或 hybrid retriever 作为更强 coarse stage。
Day 5 的分析重点应从“是否跑通”转向：

哪些 query 是 coarse 阶段失败，哪些 query 是 fine reranker 排序失败，以及当前 C2F pipeline 的真实性能瓶颈在哪里。