# Week 5 Day 2 Token Selection Module Validation Log

**Project:** PCB_VisualRAG_Project  
**Stage:** Week 5  
**Day:** Day 2  
**Date:** 2026-05-07  
**Experiment Name:** Patch/Token Selection Module Validation  
**Author:** 杨杰康  
**Status:** Completed  

---

## 1. 今日目标

今日目标是实现 patch/token selection 机制，并在小规模页面集合上验证其正确性和兼容性。

本日重点包括：

1. 实现 norm-based top-M token selection；
2. 对少量页面生成不同 M 下的压缩 page embeddings；
3. 记录原始 token 数、保留 token 数、保留比例和压缩比例；
4. 验证 compressed page embeddings 是否兼容 late interaction scorer；
5. 生成 token 保留 mask 可视化样例。

Day 2 不进行正式检索评测，只验证 token selection 模块本身是否工作正常。

---

## 2. Token Selection 策略

今日使用 Day 1 确定的策略：

> Norm-based Top-M Token Selection

该策略根据每个 page token embedding 的 L2 norm 作为 token 重要性分数，然后保留分数最高的 top-M tokens。

具体逻辑如下：

1. 读取页面 full multi-vector embedding；
2. 对每个 page token 计算 L2 norm；
3. 按 token norm 从大到小排序；
4. 保留 top-M tokens；
5. 将保留 token 按原始 token index 顺序保存；
6. 输出压缩后的 page embedding；
7. 记录 kept token indices、keep ratio、reduction ratio 和 output path。

选择该策略的原因是：

- 不需要训练额外模型；
- 不依赖 query；
- 可以提前生成压缩 page embeddings；
- 每页固定保留 M 个 tokens，便于统计 index size reduction；
- 适合作为第一版 token selection baseline。

---

## 3. 今日 M 设置

根据 Day 1 的设计，当前 page embedding shape 为：

```text
(49, 512)
```

因此，原始 page token 数为：

```text
L = 49
```

今日小规模验证使用以下 M：

| Setting | M | 说明 |
|---|---:|---|
| M8 | 8 | 极强压缩 |
| M16 | 16 | 轻量配置 |
| M24 | 24 | 中等压缩 |
| M32 | 32 | 高质量压缩点 |
| M49 | 49 | Full-token setting |

其中：

- M8 表示每页只保留 8 个 tokens；
- M16 表示每页只保留 16 个 tokens；
- M24 表示每页只保留 24 个 tokens；
- M32 表示每页只保留 32 个 tokens；
- M49 表示保留全部 49 个 tokens，作为 full-token setting。

---

## 4. 输入文件

今日使用的输入文件如下：

| 类型 | 路径 |
|---|---|
| Full page embeddings | `artifacts/embeddings/full_multivector/pages/*.npy` |
| Query embeddings | `artifacts/embeddings/full_multivector/queries/*.npy` |

今日只选取前 8 个 page embeddings 做小规模验证。

---

## 5. 输出文件

今日生成的主要输出文件如下：

| 类型 | 路径 |
|---|---|
| M8 compressed embeddings | `artifacts/embeddings/token_selection/pages_M8/` |
| M16 compressed embeddings | `artifacts/embeddings/token_selection/pages_M16/` |
| M24 compressed embeddings | `artifacts/embeddings/token_selection/pages_M24/` |
| M32 compressed embeddings | `artifacts/embeddings/token_selection/pages_M32/` |
| M49 compressed embeddings | `artifacts/embeddings/token_selection/pages_M49/` |
| Selection summary | `results/budgeted/token_selection/day2_validation/day2_token_selection_summary.csv` |
| Selection metadata | `results/budgeted/token_selection/day2_validation/day2_token_selection_metadata_all.csv` |
| Compatibility check | `results/budgeted/token_selection/day2_validation/day2_late_interaction_compatibility_check.csv` |
| Token mask visualization | `results/budgeted/token_selection/figures/day2_token_selection_masks_sample.png` |

---

## 6. 使用脚本

今日使用两个脚本：

| 脚本 | 作用 |
|---|---|
| `scripts/compression/select_page_tokens_norm.py` | 对 page embeddings 执行 norm-based top-M token selection |
| `scripts/compression/validate_token_selection_day2.py` | 验证压缩后的 page embeddings 是否兼容 late interaction scoring |

执行命令如下：

```powershell
python scripts\compression\select_page_tokens_norm.py --max-pages 8 --make-fig
python scripts\compression\validate_token_selection_day2.py
```

---

## 7. Token Selection 运行结果

第一条命令成功完成：

```text
[Done] Token selection completed.
[Output] results\budgeted\token_selection\day2_validation\day2_token_selection_summary.csv
[Output] results\budgeted\token_selection\day2_validation\day2_token_selection_metadata_all.csv
```

说明：

- 不同 M 的压缩 page embeddings 已成功生成；
- summary 文件已生成；
- metadata 文件已生成；
- token mask 可视化已生成。

---

## 8. 小规模 Token Selection Summary

`day2_token_selection_summary.csv` 内容如下：

| M | num_pages | avg_original_tokens | avg_kept_tokens | avg_keep_ratio | avg_reduction_ratio | output_dir |
|---:|---:|---:|---:|---:|---:|---|
| 8 | 8 | 49.0 | 8.0 | 0.1633 | 0.8367 | `artifacts\embeddings\token_selection\pages_M8` |
| 16 | 8 | 49.0 | 16.0 | 0.3265 | 0.6735 | `artifacts\embeddings\token_selection\pages_M16` |
| 24 | 8 | 49.0 | 24.0 | 0.4898 | 0.5102 | `artifacts\embeddings\token_selection\pages_M24` |
| 32 | 8 | 49.0 | 32.0 | 0.6531 | 0.3469 | `artifacts\embeddings\token_selection\pages_M32` |
| 49 | 8 | 49.0 | 49.0 | 1.0000 | 0.0000 | `artifacts\embeddings\token_selection\pages_M49` |

该结果确认：

1. 原始 page token 数为 49；
2. M8、M16、M24、M32、M49 均成功生成；
3. 每个 M 下的 kept tokens 数量正确；
4. keep ratio 与 reduction ratio 计算正常；
5. 输出目录正常创建。

---

## 9. Token 压缩比例分析

不同 M 下的压缩比例如下：

| M | Original Tokens | Kept Tokens | Keep Ratio | Reduction Ratio |
|---:|---:|---:|---:|---:|
| 8 | 49 | 8 | 0.1633 | 0.8367 |
| 16 | 49 | 16 | 0.3265 | 0.6735 |
| 24 | 49 | 24 | 0.4898 | 0.5102 |
| 32 | 49 | 32 | 0.6531 | 0.3469 |
| 49 | 49 | 49 | 1.0000 | 0.0000 |

具体解释如下：

- M8 保留约 16.33% tokens，减少约 83.67% tokens；
- M16 保留约 32.65% tokens，减少约 67.35% tokens；
- M24 保留约 48.98% tokens，减少约 51.02% tokens；
- M32 保留约 65.31% tokens，减少约 34.69% tokens；
- M49 为 full-token setting，不进行压缩。

这说明 Day 2 的 token selection 模块已经能够按照预期生成不同 token budget 下的压缩页面表示。

---

## 10. Late Interaction 兼容性验证

第二条命令成功完成：

```text
[Done] Compatibility validation completed.
[Output] results\budgeted\token_selection\day2_validation\day2_late_interaction_compatibility_check.csv
```

终端输出结果如下：

| M | Score | Status |
|---:|---:|---|
| 8 | -0.178542 | PASSED |
| 16 | 0.115156 | PASSED |
| 24 | 0.225783 | PASSED |
| 32 | 0.225783 | PASSED |
| 49 | 0.336721 | PASSED |

该结果说明：

1. query embedding 可以正常加载；
2. compressed page embeddings 可以正常加载；
3. 不同 M 下 page token 数变化不会导致 scorer 崩溃；
4. query/page embedding 维度兼容；
5. late interaction score 可以正常计算；
6. scorer 已经兼容变长 page token 输入。

---

## 11. Compatibility Check 结果解释

今日兼容性验证的核心目的不是比较不同 M 的检索效果，而是确认 scorer 是否能处理不同长度的 page embeddings。

验证结果中，M8、M16、M24、M32、M49 全部显示为：

```text
PASSED
```

这说明 compressed page embeddings 可以被 late interaction scorer 正常读取和计算。

不同 M 下 score 数值不同是正常现象，因为保留的 tokens 不同，page representation 发生了变化。

---

## 12. Token Mask 可视化

今日生成 token mask 可视化文件：

```text
results/budgeted/token_selection/figures/day2_token_selection_masks_sample.png
```

该图用于检查不同 M 下被保留 token 的位置分布。

当前该图的作用是验证：

- token selection mask 可以正常生成；
- M 越大，被保留 token 数越多；
- 不同 M 的 token 保留模式可以被可视化；
- 后续可以用于观察 token 是否集中在表格、注释、图例或局部密集区域。

---

## 13. 今日检查结果

Day 2 验收项完成情况如下：

| 验收项 | 状态 |
|---|---|
| token selection 脚本已实现 | Completed |
| 小规模页面上的不同 M 压缩 embedding 已生成 | Completed |
| 原始 token 数已确认 | Completed |
| kept token 数量正确 | Completed |
| keep ratio 已记录 | Completed |
| reduction ratio 已记录 | Completed |
| kept token indices 已记录 | Completed |
| output path 已记录 | Completed |
| late interaction scorer 兼容性已验证 | Completed |
| token mask 可视化已生成 | Completed |

---

## 14. 今日结论

Week 5 Day 2 已完成 patch/token selection 模块的小规模验证。

今日实验确认：

1. 当前 page embedding 的原始 token 数为 49；
2. norm-based top-M token selection 可以正常运行；
3. M8、M16、M24、M32、M49 均能生成压缩 page embeddings；
4. 各 M 的 kept token 数与预期一致；
5. keep ratio 和 reduction ratio 统计正常；
6. late interaction scorer 可以兼容不同 token 数的 page embeddings；
7. token mask 可视化文件已经生成。

最终判断：

> Day 2 验收通过。当前 token selection 机制工作正常，不同 M 的页面表示可以生成，late interaction 管线不会因为 token 数减少而崩溃。
