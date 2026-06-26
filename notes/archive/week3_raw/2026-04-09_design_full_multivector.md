# Full Multi-vector Design (Day 1)

## 1. 页面多向量表示方案
本实验采用 **页面图像的局部视觉 token / patch embeddings** 作为页面多向量表示。

### 当前默认设计
- 输入：`data/images/` 下的页面图像
- 输出：每页一个二维张量，形状约为 `num_tokens x embedding_dim`
- 默认不保留 CLS，仅保留局部视觉 token
- 每页 token 数在初版实现中保持模型原始输出，不先做裁剪
- 后续若成本过高，再考虑 token pruning / budgeted selection

### 需要记录的关键信息
- `page_id`
- `token_count`
- `embedding_dim`
- `embedding_path`

---

## 2. Query 表示方案
本实验默认采用 **query token-level embeddings**，保证与页面 token embeddings 可比较。

### 当前默认设计
- query 编码为 token-level 表示，而不是单个全局向量
- query 与 page embeddings 需处于兼容向量空间
- 初版允许 query token 数较少，但必须可追踪
- 若模型暂不方便输出 query token embeddings，可先用兼容的文本 token 表示替代

---

## 3. Late Interaction Scoring 方案
初版 scoring 采用最透明、最容易验证的 **MaxSim + Sum** 机制。

### 公式
对于 query token 集合 $$Q = \{q_1, q_2, \dots, q_m\}$$  
和 page token 集合 $$P = \{p_1, p_2, \dots, p_n\}$$

评分函数定义为：

$$
score(Q, P) = \sum_{i=1}^{m} \max_{j=1}^{n} sim(q_i, p_j)
$$

### 当前默认设置
- 相似度函数：cosine similarity
- 聚合方式：per-query-token max over page tokens, then sum
- 输出：标准 top-k ranking

---

## 4. 小规模验证子集设计
初版不直接跑全量，而先构建一个可控的小规模子集。

### 子集目标
- 验证 late interaction scoring 是否正确
- 检查 query / page 输入输出格式是否统一
- 提前观察 token 数、存储和时间成本

### 当前建议规模
- query 数：8-12
- page 数：30-50
- 覆盖不同 query type 和页面类型

---

## 5. Day 1 结束时必须明确的 4 个问题
- Full MV 每页到底保留什么向量？
- query 怎么编码？
- late interaction 怎么计算？
- 先在哪个子集上验证？
