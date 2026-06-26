# 2026-04-09 Day 3 Full Multi-Vector Retrieval Log

## 今日目标
完成 full multi-vector retrieval 的 Day 3 小规模闭环，包括：
- query embedding 提取
- late interaction scoring
- run 文件输出
- evaluation 评测

---

## 今日完成内容

### 1. Query Embedding 提取完成
- 使用 CLIP text tower 提取 query token embeddings
- 之后修正为 **projected text tokens**
- query embeddings 最终维度统一为 **512**
- 成功提取 30 条 query embeddings

### 2. Page Embedding 重新生成完成
- 原始 page token 为 `(49, 768)`，与 query `(n, 512)` 不匹配
- 修正为使用 **visual_projection** 后的 projected page tokens
- page embeddings 最终统一为 **(49, 512)**
- subset 和 full 数据都已重新生成成功

### 3. Late Interaction Retrieval 跑通
- 使用 **sum-maxsim** 做 late interaction scoring
- 成功生成：
  - `results/full_multivector/full_mv_small_run.tsv`

### 4. Evaluation 脚本修正完成
- 最初 evaluation 结果全为 0
- 排查后发现问题是：
  - `qrels.tsv` 是 **page-level**
  - 原评测脚本错误地按 **doc-level** 比较
- 修正后重新评测，得到有效结果

---

## 关键排查过程

### 问题 1：subset query 选中数为 0
- 原因：subset/qrels/query 对齐逻辑未完全确认
- 处理：先对全部 query 做 embedding，retrieval 阶段再限制 subset

### 问题 2：retrieval 配置字段报错
- 原因：配置文件字段名与脚本读取字段不一致
- 处理：统一 `full_multivector.yaml` 中的 outputs 字段

### 问题 3：query/page embedding 维度不一致
- query: `(n, 512)`
- page: `(49, 768)`
- 处理：将 page 改为 projected visual tokens，统一到 **512 维**

### 问题 4：评测结果全 0
- 原因：qrels 是 page_id，而旧 evaluation 脚本按 doc_id 比较
- 处理：修正为 page-level evaluation，并增加 doc-level 辅助指标

---

## 当前结果

### Page-level
- MRR@10 = **0.0272**
- Recall@1 = **0.0000**
- Recall@5 = **0.0667**
- Recall@10 = **0.1667**
- nDCG@10 = **0.0638**

### Doc-level (aux)
- Recall@1 = **0.0333**
- Recall@5 = **0.8000**
- Recall@10 = **1.0000**

---

## 当前结论

本日实验表明：

- full multi-vector retrieval 原型已经**成功跑通**
- projected CLIP query/page tokens 可以在共享 512 维空间中完成 late interaction scoring
- 当前方法对**文档级召回效果较强**
- 对**页级精确定位能力较弱**

也就是说，目前系统更擅长：
- **找到正确文档**
而不是：
- **直接找到正确页面**

---

## 输出文件

今日已成功生成：

- `artifacts/embeddings/full_multivector/pages/*.npy`
- `artifacts/embeddings/full_multivector/queries/*.npy`
- `artifacts/embeddings/full_multivector/page_embedding_meta.jsonl`
- `artifacts/embeddings/full_multivector/query_embedding_meta.jsonl`
- `results/full_multivector/full_mv_small_run.tsv`
- `results/full_multivector/full_mv_small_metrics.json`

---

## 下一步计划
下一阶段优先考虑：

1. 做 **doc-first, page-second** 两阶段检索
2. 尝试 **global + local score fusion**
3. 引入 **OCR / text signal** 辅助页级定位
4. 继续分析 “right doc but wrong page” 的比例

---

## 一句话总结
今天完成了 **Day 3 full multi-vector retrieval 的完整工程闭环**，并确认当前 baseline 具备较强文档级召回能力，但页级定位仍需进一步优化。
