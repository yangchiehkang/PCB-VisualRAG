📝 Markdown 完整内容
复制
# Week 3 实验总结：Full Multi-Vector 页面侧向量库构建

本周的核心工作是为 PCB VisualRAG 项目搭建 **Full Multi-Vector Retrieval** 的页面侧基础资产。具体来说，目标是将每个文档页面图像编码为一组局部视觉 token embeddings，并以统一格式保存，配套生成 metadata、统计信息和运行日志。到本周结束时，页面侧 multi-vector embedding 库已经成功完成全量构建，可直接作为后续 late interaction 检索实验的输入。

---

## 1. 本周实验目标

本周实验的目标可以概括为以下几点：

- 明确 Full Multi-Vector Retrieval 的实验配置
- 基于页面图像提取 patch/token-level embeddings
- 为每个页面保存统一的 `.npy` 向量文件
- 生成页面 embedding 与 page metadata 的映射文件
- 统计 token 数量、embedding 维度与存储成本
- 为后续 Day 3 的 query token embedding 与 late interaction scoring 做准备

---

## 2. 使用配置

本周实验使用的配置文件为：

```yaml
experiment_name: full_multivector_day1_plan

data:
  corpus_file: data/metadata/corpus.jsonl
  query_file: data/metadata/queries.jsonl
  qrels_file: data/metadata/qrels.tsv
  page_inventory_file: data/metadata/page_inventory.csv
  image_root: data/images
  subset_file: data/metadata/full_mv_small_subset.json

model:
  name: openai/clip-vit-base-patch32
  device: cuda
  normalize_embeddings: true

page_embedding:
  representation: local_visual_tokens
  source: patch_or_token_embeddings
  keep_cls: false
  token_limit: null
  save_dir: artifacts/embeddings/full_multivector/pages

query_embedding:
  representation: token_level
  max_length: 32
  save_dir: artifacts/embeddings/full_multivector/queries

scoring:
  similarity: cosine
  aggregation: sum_maxsim
  topk: 10

outputs:
  page_meta_file: artifacts/embeddings/full_multivector/page_embedding_meta.jsonl
  query_meta_file: artifacts/embeddings/full_multivector/query_embedding_meta.jsonl
  small_run_file: results/full_multivector/full_mv_small_run.tsv
  small_metrics_file: results/full_multivector/full_mv_small_metrics.json
  cost_summary_file: results/full_multivector/full_mv_cost_summary.csv
说明：

最初模型名使用了 clip-vit-base-patch32
运行时报错，原因是该名称不是 Hugging Face 的合法 repo id
后续修正为 openai/clip-vit-base-patch32 后，模型成功加载
3. 实验过程回顾
3.1 配置检查
首先确认了以下关键路径和参数：

page_inventory_file = data/metadata/page_inventory.csv
image_root = data/images
subset_file = data/metadata/full_mv_small_subset.json
page_embedding.save_dir = artifacts/embeddings/full_multivector/pages
model.name = openai/clip-vit-base-patch32
配置检查通过后，开始进行页面 embedding 提取实验。

3.2 Small Subset 测试
为了避免直接全量运行带来的调试风险，先在 small subset 上进行了测试。subset 共包含 50 个页面。

运行命令：

复制
python scripts\run_full_multivector_page_embeddings.py --config configs\full_multivector.yaml --subset-only --overwrite
运行结果：

页面总数：50
成功处理：50
失败处理：0
所有页面 embedding shape 一致：(49, 768)
运行耗时：约 5.84 秒
subset 测试结果表明：

脚本逻辑正确
模型加载正常
图片路径解析正常
embedding 文件成功落盘
metadata 与 token 统计文件生成成功
3.3 Full Run 全量运行
在 subset 成功后，进一步对全量页面进行 embedding 提取。page inventory 中共包含 101 个页面。

运行命令：

复制
python scripts\run_full_multivector_page_embeddings.py --config configs\full_multivector.yaml --overwrite
全量运行结果：

页面总数：101
成功处理：101
失败处理：0
所有页面 embedding shape 一致：(49, 768)
全量运行耗时：约 11.30 秒
这表明页面侧 multi-vector embedding pipeline 已经稳定可靠。

4. 结果统计
4.1 总体统计
根据 artifacts/embeddings/full_multivector/token_stats.json，全量结果如下：

指标	结果
页面总数	101
平均 token 数 / 页	49.0
最小 token 数	49
最大 token 数	49
embedding 维度	768
总存储大小	15,216,256 bytes
平均文件大小	150,656 bytes
总耗时	11.295 s
模型	openai/clip-vit-base-patch32
设备	cpu
CLS token	不保留
embedding normalization	是
4.2 分 page_type 统计
根据 token_stats_by_page_type.csv，不同页面类型的统计如下：

page_type	page_count	avg_token_count	embedding_dim	total_file_size_bytes
assembly	17	49.0	768	2,561,152
bom	7	49.0	768	1,054,592
fabrication	4	49.0	768	602,624
layout	10	49.0	768	1,506,560
other	48	49.0	768	7,231,488
schematic	15	49.0	768	2,259,840
从统计结果可以看出：

所有页面类型的 token 数均一致
所有页面 embedding 维度统一为 768
页面类型字段读取和统计逻辑正常
other 类型页面数量最多，后续如有需要可进一步细分
5. 输出文件
本周实验已成功生成以下核心文件：

页面 embedding 文件
artifacts/embeddings/full_multivector/pages/*.npy
元数据文件
artifacts/embeddings/full_multivector/page_embedding_meta.jsonl
统计文件
artifacts/embeddings/full_multivector/token_stats.json
artifacts/embeddings/full_multivector/token_stats.csv
artifacts/embeddings/full_multivector/token_stats_by_page_type.csv
日志文件
artifacts/embeddings/full_multivector/page_embedding_run.log
这些输出文件共同构成了后续 Full Multi-Vector Retrieval 实验的页面侧基础资产。

6. 关键观察与分析
6.1 页面 embedding 输出稳定
所有页面输出 shape 均为：

复制
(49, 768)
这说明：

图像预处理流程一致
CLIP 视觉编码输出结构稳定
patch token 数固定
后续 late interaction scoring 实现会更简单
6.2 存储成本合理
每个 .npy 文件大小为：

复制
150,656 bytes
从理论上看：

token 数：49
向量维度：768
数据类型：float32
理论裸数据大小约为：

复制
49 × 768 × 4 = 150,528 bytes
实际 .npy 文件大小略大于理论值，差值主要来自 .npy 文件头部开销，因此整体存储成本合理，没有异常。

6.3 CPU 运行也足够快
虽然配置中设备设置为 cuda，但运行时检测到 CUDA 不可用，因此自动回退到 CPU。即便如此：

subset 50 页仅耗时约 5.84 秒
full 101 页仅耗时约 11.30 秒
这说明当前数据规模下，页面 embedding 提取成本较低，便于后续快速迭代实验。

7. 本周遇到的问题与解决方法
问题 1：模型加载报错
初次运行时报错：

RepositoryNotFoundError
原因：clip-vit-base-patch32 不是 Hugging Face 有效 repo id
解决方法
将配置中的模型名从：

复制
name: clip-vit-base-patch32
修改为：

复制
name: openai/clip-vit-base-patch32
修正后模型成功加载，问题解决。

问题 2：CUDA 不可用
运行时日志显示：

复制
CUDA not available, fallback to cpu
处理结果
脚本自动切换到 CPU，实验仍然可以顺利完成。由于当前数据规模较小，CPU 运行时间仍然可接受，因此不影响本周实验进度。

8. 本周实验结论
本周已经成功完成 Full Multi-Vector Retrieval 的页面侧基础构建工作，具体体现在：

所有页面图像均成功编码为局部视觉 token embeddings
页面侧 multi-vector 文件全部成功保存
页面 embedding metadata 文件成功生成
token 数、embedding 维度、存储成本统计均已完成
页面类型维度的成本分析已经具备
页面侧 multi-vector embedding 库已可用于后续检索实验
换句话说，本周结束时，项目已经完成了从“实验设想”到“可运行页面多向量库”的关键过渡。