from pathlib import Path
import csv
import json
from collections import defaultdict


PROJECT_ROOT = Path(r"E:\Working\PCB_VisualRAG_Project")

RUN_PATH = PROJECT_ROOT / "results" / "baselines" / "single_vector_visual_run.tsv"
QRELS_PATH = PROJECT_ROOT / "data" / "metadata" / "qrels.tsv"

OUT_DIR = PROJECT_ROOT / "artifacts" / "rerank_cache" / "single_vector_topN"
RESULT_DIR = PROJECT_ROOT / "results" / "budgeted" / "coarse_to_fine"
NOTE_DIR = PROJECT_ROOT / "notes" / "archive" / "week4_raw"

N_VALUES = [10, 20, 50, 100]


def ensure_dirs():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    NOTE_DIR.mkdir(parents=True, exist_ok=True)


def read_tsv_rows(path):
    if not path.exists():
        raise FileNotFoundError("Missing file: {}".format(path))

    rows = []

    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f, delimiter="\t")
        for row in reader:
            if row and any(cell.strip() for cell in row):
                rows.append(row)

    return rows


def parse_run_file(path):
    rows = read_tsv_rows(path)

    first = [x.strip() for x in rows[0]]
    lower = [x.lower() for x in first]

    has_header = (
        ("query_id" in lower or "qid" in lower)
        and (
            "page_id" in lower
            or "doc_id" in lower
            or "candidate_page_id" in lower
        )
    )

    parsed = []

    if has_header:
        header = lower
        data_rows = rows[1:]

        def find_col(candidates):
            for c in candidates:
                if c in header:
                    return header.index(c)
            return None

        q_idx = find_col(["query_id", "qid"])
        p_idx = find_col(["page_id", "doc_id", "candidate_page_id"])
        r_idx = find_col(["rank"])
        s_idx = find_col(["score"])

        if q_idx is None or p_idx is None:
            raise ValueError("Cannot identify query/page columns in run file header: {}".format(first))

        for row in data_rows:
            if len(row) <= max(q_idx, p_idx):
                continue

            qid = row[q_idx].strip()
            pid = row[p_idx].strip()

            rank = None
            if r_idx is not None and len(row) > r_idx:
                try:
                    rank = int(float(row[r_idx]))
                except Exception:
                    rank = None

            score = 0.0
            if s_idx is not None and len(row) > s_idx:
                try:
                    score = float(row[s_idx])
                except Exception:
                    score = 0.0

            parsed.append(
                {
                    "query_id": qid,
                    "page_id": pid,
                    "rank": rank,
                    "score": score,
                }
            )

    else:
        for row in rows:
            row = [x.strip() for x in row]

            if len(row) >= 6 and row[1].upper() == "Q0":
                qid = row[0]
                pid = row[2]
                rank = int(float(row[3]))
                score = float(row[4])
            elif len(row) >= 5:
                qid = row[1]
                pid = row[2]
                rank = int(float(row[3]))
                score = float(row[4])
            elif len(row) >= 4:
                qid = row[0]
                pid = row[1]
                rank = int(float(row[2]))
                score = float(row[3])
            else:
                continue

            parsed.append(
                {
                    "query_id": qid,
                    "page_id": pid,
                    "rank": rank,
                    "score": score,
                }
            )

    by_query = defaultdict(list)

    for item in parsed:
        by_query[item["query_id"]].append(item)

    for qid in by_query:
        by_query[qid].sort(
            key=lambda x: (
                x["rank"] if x["rank"] is not None else 10**9,
                -x["score"],
            )
        )

        for idx, item in enumerate(by_query[qid], start=1):
            item["rank"] = idx

    return by_query


def parse_qrels(path):
    rows = read_tsv_rows(path)

    first = [x.strip() for x in rows[0]]
    lower = [x.lower() for x in first]

    has_header = (
        ("query_id" in lower or "qid" in lower)
        and ("page_id" in lower or "doc_id" in lower)
    )

    qrels = defaultdict(set)

    if has_header:
        header = lower
        data_rows = rows[1:]

        def find_col(candidates):
            for c in candidates:
                if c in header:
                    return header.index(c)
            return None

        q_idx = find_col(["query_id", "qid"])
        p_idx = find_col(["page_id", "doc_id"])
        rel_idx = find_col(["relevance", "rel", "label"])

        if q_idx is None or p_idx is None:
            raise ValueError("Cannot identify query/page columns in qrels header: {}".format(first))

        for row in data_rows:
            if len(row) <= max(q_idx, p_idx):
                continue

            qid = row[q_idx].strip()
            pid = row[p_idx].strip()

            rel = 1.0
            if rel_idx is not None and len(row) > rel_idx:
                try:
                    rel = float(row[rel_idx])
                except Exception:
                    rel = 1.0

            if rel > 0:
                qrels[qid].add(pid)

    else:
        for row in rows:
            row = [x.strip() for x in row]

            if len(row) >= 4 and row[1] in ["0", "Q0"]:
                qid = row[0]
                pid = row[2]
                rel_raw = row[3]
            elif len(row) >= 3:
                qid = row[0]
                pid = row[1]
                rel_raw = row[2]
            elif len(row) >= 2:
                qid = row[0]
                pid = row[1]
                rel_raw = "1"
            else:
                continue

            try:
                rel = float(rel_raw)
            except Exception:
                rel = 1.0

            if rel > 0:
                qrels[qid].add(pid)

    return qrels


def write_candidates(by_query):
    all_path = OUT_DIR / "single_vector_candidates_all.tsv"

    with all_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerow(["query_id", "candidate_page_id", "coarse_rank", "coarse_score"])

        for qid in sorted(by_query.keys()):
            for item in by_query[qid]:
                writer.writerow(
                    [
                        qid,
                        item["page_id"],
                        item["rank"],
                        "{:.8f}".format(item["score"]),
                    ]
                )

    for n in N_VALUES:
        out_path = OUT_DIR / "single_vector_candidates_top{}.tsv".format(n)

        with out_path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f, delimiter="\t")
            writer.writerow(["query_id", "candidate_page_id", "coarse_rank", "coarse_score"])

            for qid in sorted(by_query.keys()):
                for item in by_query[qid][:n]:
                    writer.writerow(
                        [
                            qid,
                            item["page_id"],
                            item["rank"],
                            "{:.8f}".format(item["score"]),
                        ]
                    )

    return all_path


def compute_coarse_recall(by_query, qrels):
    query_ids = sorted(qrels.keys())
    summary = []

    for n in N_VALUES:
        hit_count = 0
        miss_count = 0
        evaluated_count = 0

        for qid in query_ids:
            relevant = qrels[qid]
            candidates = set()

            for item in by_query.get(qid, [])[:n]:
                candidates.add(item["page_id"])

            if not relevant:
                continue

            evaluated_count += 1

            if relevant & candidates:
                hit_count += 1
            else:
                miss_count += 1

        recall = hit_count / evaluated_count if evaluated_count else 0.0

        summary.append(
            {
                "N": n,
                "evaluated_queries": evaluated_count,
                "hit_queries": hit_count,
                "miss_queries": miss_count,
                "coarse_recall": recall,
            }
        )

    return summary


def write_recall_summary(summary):
    csv_path = RESULT_DIR / "single_vector_coarse_recall.csv"

    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "N",
                "evaluated_queries",
                "hit_queries",
                "miss_queries",
                "coarse_recall",
            ]
        )

        for row in summary:
            writer.writerow(
                [
                    row["N"],
                    row["evaluated_queries"],
                    row["hit_queries"],
                    row["miss_queries"],
                    "{:.4f}".format(row["coarse_recall"]),
                ]
            )

    json_path = RESULT_DIR / "single_vector_coarse_recall.json"

    with json_path.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    return csv_path, json_path


def write_failure_cases(by_query, qrels):
    path = RESULT_DIR / "single_vector_coarse_failure_cases.csv"

    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)

        writer.writerow(
            [
                "query_id",
                "N",
                "relevant_pages",
                "top_candidates",
                "best_relevant_rank_if_available",
                "failure_reason",
            ]
        )

        for qid in sorted(qrels.keys()):
            relevant = qrels[qid]
            ranking = by_query.get(qid, [])

            rank_lookup = {}
            for item in ranking:
                rank_lookup[item["page_id"]] = item["rank"]

            relevant_ranks = []
            for page_id in relevant:
                if page_id in rank_lookup:
                    relevant_ranks.append(rank_lookup[page_id])

            best_rank = min(relevant_ranks) if relevant_ranks else ""

            for n in N_VALUES:
                candidates = []
                for item in ranking[:n]:
                    candidates.append(item["page_id"])

                hit = bool(set(candidates) & relevant)

                if not hit:
                    top_preview = candidates[:10]
                    writer.writerow(
                        [
                            qid,
                            n,
                            ";".join(sorted(relevant)),
                            ";".join(top_preview),
                            best_rank,
                            "gold page not included in coarse top-{}".format(n),
                        ]
                    )

    return path


def write_day2_note(summary, candidate_all_path, recall_csv_path, failure_path):
    note_path = NOTE_DIR / "2026-05-07_week4_day2_coarse_candidate_pipeline.md"

    summary_lines = []
    for row in summary:
        line = "| Top-{} | {} | {} | {} | {:.4f} |".format(
            row["N"],
            row["evaluated_queries"],
            row["hit_queries"],
            row["miss_queries"],
            row["coarse_recall"],
        )
        summary_lines.append(line)

    best_safe = None
    for row in summary:
        if row["miss_queries"] == 0:
            best_safe = row["N"]
            break

    if best_safe is None:
        best_safe_text = "当前 single-vector coarse 在所有测试 N 下仍存在漏召回，需要在后续实验中重点关注 coarse recall 上限。"
    else:
        best_safe_text = "从 N={} 开始，当前 coarse retriever 在测试 query 上没有明显漏召回。".format(best_safe)

    content = """# Week 4 Day 2 Coarse Candidate Pipeline Log

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
| All candidates | `{}` |
| Top-10 candidates | `artifacts/rerank_cache/single_vector_topN/single_vector_candidates_top10.tsv` |
| Top-20 candidates | `artifacts/rerank_cache/single_vector_topN/single_vector_candidates_top20.tsv` |
| Top-50 candidates | `artifacts/rerank_cache/single_vector_topN/single_vector_candidates_top50.tsv` |
| Top-100 candidates | `artifacts/rerank_cache/single_vector_topN/single_vector_candidates_top100.tsv` |
| Coarse recall summary | `{}` |
| Coarse failure cases | `{}` |

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
{}

---

## 6. 今日观察

本日完成了 coarse retrieval candidate pipeline，并生成了 top-10、top-20、top-50、top-100 四组候选文件。

关键观察如下：

- coarse recall 是 coarse-to-fine 系统的上限；
- 如果 gold page 未进入 coarse top-N，后续 Full MV reranking 无法恢复该 query；
- N 越大，coarse 阶段漏召回风险越低，但后续 reranking 成本也会增加；
- 当前结果将直接决定 Day 3 的 Full MV reranking 是否有足够候选基础。

当前关于候选规模的初步判断：

> {}

---

## 7. 粗召回失败样例记录

粗召回失败样例已保存至：

| 文件 | 说明 |
|---|---|
| `{}` | 记录不同 N 下 gold page 未进入候选集的 query |

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
""".format(
        candidate_all_path.relative_to(PROJECT_ROOT),
        recall_csv_path.relative_to(PROJECT_ROOT),
        failure_path.relative_to(PROJECT_ROOT),
        "\n".join(summary_lines),
        best_safe_text,
        failure_path.relative_to(PROJECT_ROOT),
    )

    note_path.write_text(content, encoding="utf-8")

    return note_path


def main():
    ensure_dirs()

    print("[Day2] Loading single-vector coarse run...")
    by_query = parse_run_file(RUN_PATH)
    print("[Day2] Loaded queries from run: {}".format(len(by_query)))

    print("[Day2] Loading qrels...")
    qrels = parse_qrels(QRELS_PATH)
    print("[Day2] Loaded qrels queries: {}".format(len(qrels)))

    print("[Day2] Writing candidate files...")
    candidate_all_path = write_candidates(by_query)

    print("[Day2] Computing coarse recall...")
    summary = compute_coarse_recall(by_query, qrels)

    print("[Day2] Writing recall summary...")
    recall_csv_path, recall_json_path = write_recall_summary(summary)

    print("[Day2] Writing failure cases...")
    failure_path = write_failure_cases(by_query, qrels)

    print("[Day2] Writing Day 2 note...")
    note_path = write_day2_note(summary, candidate_all_path, recall_csv_path, failure_path)

    print("")
    print("========== Day 2 Completed ==========")
    print("Candidate all: {}".format(candidate_all_path))
    print("Recall CSV:    {}".format(recall_csv_path))
    print("Recall JSON:   {}".format(recall_json_path))
    print("Failures:      {}".format(failure_path))
    print("Note:          {}".format(note_path))
    print("")
    print("Coarse Recall Summary:")

    for row in summary:
        print(
            "  Top-{}: recall={:.4f}, hit={}, miss={}, total={}".format(
                row["N"],
                row["coarse_recall"],
                row["hit_queries"],
                row["miss_queries"],
                row["evaluated_queries"],
            )
        )


if __name__ == "__main__":
    main()
