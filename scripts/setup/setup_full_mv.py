from pathlib import Path
import json
import csv
import re
from datetime import datetime
import argparse

DESIGN_MD = """# Full Multi-vector Design

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
对于 query token 集合 $$Q = \\{q_1, q_2, \\dots, q_m\\}$$  
和 page token 集合 $$P = \\{p_1, p_2, \\dots, p_n\\}$$

评分函数定义为：

$$
score(Q, P) = \\sum_{i=1}^{m} \\max_{j=1}^{n} sim(q_i, p_j)
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

## 5. 初始化阶段需要明确的关键问题
- Full MV 每页到底保留什么向量？
- query 怎么编码？
- late interaction 怎么计算？
- 先在哪个子集上验证？
"""

LOG_TEMPLATE_MD = """# Experiment Log Template

## 基本信息
- 日期：
- 实验名称：
- 数据集版本：
- 子集 / 全量：
- 模型版本：
- 配置文件：

## 输入规模
- query 数：
- page 数：
- 平均每页 token 数：
- query token 数范围：
- embedding 维度：

## Scoring 设置
- query 表示：
- page 表示：
- similarity：
- aggregation：
- top-k：

## 运行环境
- OS：
- Python：
- GPU：
- CPU：
- 内存：

## 耗时记录
- page embedding 提取耗时：
- query embedding 提取耗时：
- retrieval 耗时：
- evaluation 耗时：

## 输出文件
- run 文件：
- metrics 文件：
- 日志文件：

## 备注
- 观察到的问题：
- 可疑 bug：
- 下一步动作：
"""

YAML_TEMPLATE = """experiment_name: full_multivector_week3

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
  representation: local_visual_tokens_projected
  source: vision_hidden_states_plus_projection
  keep_cls: false
  token_limit: null
  save_dir: artifacts/embeddings/full_multivector/pages

query_embedding:
  representation: token_level_projected
  source: text_hidden_states_plus_projection
  max_length: 32
  save_dir: artifacts/embeddings/full_multivector/queries

scoring:
  similarity: cosine
  aggregation: sum_maxsim
  topk: 10

outputs:
  page_meta_file: artifacts/embeddings/full_multivector/page_embedding_meta.jsonl
  query_meta_file: artifacts/embeddings/full_multivector/query_embedding_meta.jsonl

  full_run_file: results/full_multivector/full_mv_run.tsv
  full_metrics_file: results/full_multivector/full_mv_metrics.json

  small_run_file: results/full_multivector/full_mv_small_run.tsv
  small_metrics_file: results/full_multivector/full_mv_small_metrics.json

  comparison_csv_file: results/comparisons/full_vs_single_overview.csv
  comparison_query_csv_file: results/comparisons/full_vs_single_query_level.csv
"""


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def log(msg, logs):
    line = f"[{now()}] {msg}"
    print(line)
    logs.append(line)


def ensure_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)


def normalize_id(x):
    if x is None:
        return None
    x = str(x).strip()
    if not x:
        return None
    x = x.replace("\\", "/")
    x = x.split("/")[-1]
    x = re.sub(r"\.(png|jpg|jpeg|txt|pdf)$", "", x, flags=re.IGNORECASE)
    return x


def first_existing_key(d, keys):
    for k in keys:
        if k in d and d[k] not in [None, ""]:
            return d[k]
    return None


def read_queries_jsonl(path: Path, logs):
    queries = []
    sample_keys = None

    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)

            if sample_keys is None:
                sample_keys = list(obj.keys())

            qid = first_existing_key(obj, ["query_id", "qid", "id", "question_id", "queryid"])
            qtext = first_existing_key(obj, ["query_text", "text", "query", "question", "title"])

            queries.append({
                "raw": obj,
                "query_id": normalize_id(qid),
                "query_text": str(qtext).strip() if qtext is not None else ""
            })

    log(f"Loaded queries: {len(queries)} from {path}", logs)
    if sample_keys is not None:
        log(f"Sample query keys: {sample_keys}", logs)

    valid_qid = sum(1 for q in queries if q["query_id"])
    valid_qtext = sum(1 for q in queries if q["query_text"])
    log(f"Queries with query_id: {valid_qid}", logs)
    log(f"Queries with query_text: {valid_qtext}", logs)

    return queries


def read_qrels_pages(qrels_path: Path, logs):
    qid_to_pages = {}
    sample_lines = []

    lines = qrels_path.read_text(encoding="utf-8").splitlines()
    lines = [ln.strip() for ln in lines if ln.strip()]

    if not lines:
        log(f"Qrels file is empty: {qrels_path}", logs)
        return qid_to_pages

    for ln in lines[:5]:
        sample_lines.append(ln)

    header = re.split(r"\t+", lines[0])
    header_lower = [h.strip().lower() for h in header]

    has_named_header = (
        ("query_id" in header_lower or "qid" in header_lower)
        and ("page_id" in header_lower or "docid" in header_lower or "doc_id" in header_lower)
    )

    if has_named_header:
        with qrels_path.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f, delimiter="\t")
            fieldnames = reader.fieldnames or []
            log(f"Qrels detected as header TSV with columns: {fieldnames}", logs)

            for row in reader:
                qid = first_existing_key(row, ["query_id", "qid"])
                pid = first_existing_key(row, ["page_id", "docid", "doc_id"])
                rel = first_existing_key(row, ["relevance", "rel", "label"])

                qid = normalize_id(qid)
                pid = normalize_id(pid)

                if not qid or not pid or rel in [None, ""]:
                    continue

                try:
                    rel_num = int(float(str(rel).strip()))
                except ValueError:
                    continue

                if rel_num > 0:
                    qid_to_pages.setdefault(qid, []).append(pid)

    else:
        log("Qrels detected as no-header / TREC-style format", logs)

        for line in lines:
            parts = line.split("\t")
            if len(parts) < 4:
                parts = re.split(r"\s+", line)

            if len(parts) < 4:
                continue

            qid = normalize_id(parts[0])
            pid = normalize_id(parts[2])
            rel = parts[3].strip()

            if not qid or not pid:
                continue

            try:
                rel_num = int(float(rel))
            except ValueError:
                continue

            if rel_num > 0:
                qid_to_pages.setdefault(qid, []).append(pid)

    log(f"Loaded qrels query ids: {len(qid_to_pages)} from {qrels_path}", logs)
    log(f"Sample qrels lines: {sample_lines}", logs)

    total_pairs = sum(len(v) for v in qid_to_pages.values())
    log(f"Total positive qrel pairs: {total_pairs}", logs)

    return qid_to_pages


def read_page_inventory(page_inventory_path: Path, logs):
    rows = []
    with page_inventory_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
        for row in reader:
            rows.append(row)

    log(f"Loaded page inventory rows: {len(rows)} from {page_inventory_path}", logs)
    log(f"Page inventory columns: {fieldnames}", logs)
    return rows


def infer_page_id(row):
    value = first_existing_key(row, [
        "page_id", "docid", "doc_id", "page", "page_name", "image_id", "image_name"
    ])
    return normalize_id(value)


def infer_page_type(row):
    value = first_existing_key(row, ["page_type", "type", "category"])
    return str(value).strip() if value else "unknown"


def build_small_subset(queries, qid_to_pages, page_inventory_rows, max_queries=10, max_pages=50, logs=None):
    selected_queries = []
    selected_pages = set()

    inventory_page_ids = []
    page_type_map = {}

    for row in page_inventory_rows:
        pid = infer_page_id(row)
        if pid:
            inventory_page_ids.append(pid)
            page_type_map[pid] = infer_page_type(row)

    inventory_page_set = set(inventory_page_ids)

    if logs is not None:
        log(f"Inventory page ids: {len(inventory_page_ids)}", logs)

    matched_query_count = 0
    for q in queries:
        qid = q["query_id"]
        qtext = q["query_text"]
        if not qid or not qtext:
            continue
        if qid in qid_to_pages:
            matched_query_count += 1
            selected_queries.append(q)
        if len(selected_queries) >= max_queries:
            break

    if logs is not None:
        log(f"Matched queries with positive qrels: {matched_query_count}", logs)

    matched_positive_pages = 0
    for q in selected_queries:
        qid = q["query_id"]
        for pid in qid_to_pages.get(qid, []):
            pid_norm = normalize_id(pid)
            if pid_norm in inventory_page_set:
                selected_pages.add(pid_norm)
                matched_positive_pages += 1
            if len(selected_pages) >= max_pages:
                break
        if len(selected_pages) >= max_pages:
            break

    if logs is not None:
        log(f"Matched positive pages present in inventory: {matched_positive_pages}", logs)

    for pid in inventory_page_ids:
        if len(selected_pages) >= max_pages:
            break
        selected_pages.add(pid)

    subset = {
        "subset_name": "full_mv_small_subset",
        "created_at": now(),
        "query_count": len(selected_queries),
        "page_count": len(selected_pages),
        "queries": [
            {
                "query_id": q["query_id"],
                "query_text": q["query_text"]
            }
            for q in selected_queries
        ],
        "pages": [
            {
                "page_id": pid,
                "page_type": page_type_map.get(pid, "unknown")
            }
            for pid in sorted(selected_pages)
        ]
    }
    return subset


def write_text_if_missing(path: Path, content: str, logs):
    if path.exists():
        log(f"SKIP existing file: {path}", logs)
        return
    path.write_text(content, encoding="utf-8")
    log(f"WRITE file: {path}", logs)


def write_subset_json(path: Path, subset: dict, logs):
    path.write_text(json.dumps(subset, ensure_ascii=False, indent=2), encoding="utf-8")
    log(f"WRITE subset json: {path}", logs)


def write_subset_md(path: Path, subset: dict, logs):
    lines = []
    lines.append("# Full MV Small Subset\n")
    lines.append(f"- 创建时间：{subset['created_at']}")
    lines.append(f"- query 数：{subset['query_count']}")
    lines.append(f"- page 数：{subset['page_count']}\n")

    lines.append("## Queries")
    if subset["queries"]:
        for q in subset["queries"]:
            lines.append(f"- `{q['query_id']}`: {q['query_text']}")
    else:
        lines.append("- 暂未匹配到 query，请检查 queries.jsonl / qrels.tsv 字段格式")

    lines.append("\n## Pages")
    for p in subset["pages"]:
        lines.append(f"- `{p['page_id']}` ({p['page_type']})")

    path.write_text("\n".join(lines), encoding="utf-8")
    log(f"WRITE subset md: {path}", logs)


def maybe_write_config_if_missing(path: Path, logs):
    if not path.exists():
        path.write_text(YAML_TEMPLATE, encoding="utf-8")
        log(f"WRITE file: {path}", logs)
    else:
        log(f"SKIP existing config file: {path}", logs)


def main():
    parser = argparse.ArgumentParser(description="Setup files and small subset for Full Multi-vector experiments.")
    parser.add_argument("--root", type=str, default=".", help="Project root")
    parser.add_argument("--max-queries", type=int, default=10, help="Max queries for small subset")
    parser.add_argument("--max-pages", type=int, default=50, help="Max pages for small subset")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    logs = []

    log(f"START Full MV setup at: {root}", logs)

    notes_dir = root / "notes"
    configs_dir = root / "configs"
    metadata_dir = root / "data" / "metadata"
    logs_dir = root / "logs"

    ensure_dir(notes_dir)
    ensure_dir(configs_dir)
    ensure_dir(metadata_dir)
    ensure_dir(logs_dir)

    queries_path = metadata_dir / "queries.jsonl"
    qrels_path = metadata_dir / "qrels.tsv"
    page_inventory_path = metadata_dir / "page_inventory.csv"

    if not queries_path.exists():
        raise FileNotFoundError(f"Missing queries file: {queries_path}")
    if not qrels_path.exists():
        raise FileNotFoundError(f"Missing qrels file: {qrels_path}")
    if not page_inventory_path.exists():
        raise FileNotFoundError(f"Missing page inventory file: {page_inventory_path}")

    queries = read_queries_jsonl(queries_path, logs)
    qid_to_pages = read_qrels_pages(qrels_path, logs)
    page_inventory_rows = read_page_inventory(page_inventory_path, logs)

    subset = build_small_subset(
        queries=queries,
        qid_to_pages=qid_to_pages,
        page_inventory_rows=page_inventory_rows,
        max_queries=args.max_queries,
        max_pages=args.max_pages,
        logs=logs
    )

    design_md_path = notes_dir / "2026-04-09_design_full_multivector.md"
    subset_md_path = notes_dir / "2026-04-09_experiment_full_mv_small_subset.md"
    log_template_path = notes_dir / "template_experiment_log.md"
    yaml_path = configs_dir / "full_multivector.yaml"
    subset_json_path = metadata_dir / "full_mv_small_subset.json"

    write_text_if_missing(design_md_path, DESIGN_MD, logs)
    write_text_if_missing(log_template_path, LOG_TEMPLATE_MD, logs)
    maybe_write_config_if_missing(yaml_path, logs)

    write_subset_json(subset_json_path, subset, logs)
    write_subset_md(subset_md_path, subset, logs)

    if subset["query_count"] == 0:
        log("WARNING: subset query_count is 0. Check query/qrels field alignment.", logs)

    log_file = logs_dir / "day1_full_mv_plan_log.txt"
    log_file.write_text("\n".join(logs), encoding="utf-8")
    print(f"\nLog written to: {log_file}")


if __name__ == "__main__":
    main()
