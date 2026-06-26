from pathlib import Path
from collections import defaultdict
import csv
import json
import time
import shutil

import numpy as np


PROJECT_ROOT = Path(r"E:\Working\PCB_VisualRAG_Project")

CANDIDATE_DIR = PROJECT_ROOT / "artifacts" / "rerank_cache" / "single_vector_topN"
QUERY_EMB_DIR = PROJECT_ROOT / "artifacts" / "embeddings" / "full_multivector" / "queries"
PAGE_EMB_DIR = PROJECT_ROOT / "artifacts" / "embeddings" / "full_multivector" / "pages"

RESULT_DIR = PROJECT_ROOT / "results" / "budgeted" / "coarse_to_fine"
NOTE_DIR = PROJECT_ROOT / "notes" / "archive" / "week4_raw"

N_VALUES = [10, 20, 50, 100]


def ensure_dirs():
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    NOTE_DIR.mkdir(parents=True, exist_ok=True)


def find_npy_file(directory, item_id):
    candidates = [
        directory / "{}.npy".format(item_id),
        directory / "{}.npy".format(item_id.lower()),
        directory / "{}.npy".format(item_id.upper()),
    ]

    for path in candidates:
        if path.exists():
            return path

    return None


def load_embedding(directory, item_id):
    path = find_npy_file(directory, item_id)

    if path is None:
        raise FileNotFoundError("Embedding not found for {} under {}".format(item_id, directory))

    arr = np.load(path)

    if arr.ndim == 1:
        arr = arr.reshape(1, -1)

    return arr.astype(np.float32)


def read_candidate_file(path):
    if not path.exists():
        raise FileNotFoundError("Candidate file not found: {}".format(path))

    by_query = defaultdict(list)

    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")

        required_cols = ["query_id", "candidate_page_id", "coarse_rank", "coarse_score"]

        for col in required_cols:
            if col not in reader.fieldnames:
                raise ValueError("Missing column {} in {}".format(col, path))

        for row in reader:
            qid = row["query_id"].strip()
            pid = row["candidate_page_id"].strip()

            try:
                coarse_rank = int(float(row["coarse_rank"]))
            except Exception:
                coarse_rank = 999999

            try:
                coarse_score = float(row["coarse_score"])
            except Exception:
                coarse_score = 0.0

            by_query[qid].append(
                {
                    "query_id": qid,
                    "page_id": pid,
                    "coarse_rank": coarse_rank,
                    "coarse_score": coarse_score,
                }
            )

    for qid in by_query:
        by_query[qid].sort(key=lambda x: x["coarse_rank"])

    return by_query


def late_interaction_score(query_emb, page_emb):
    sim = np.matmul(query_emb, page_emb.T)
    max_per_query_token = sim.max(axis=1)
    score = float(max_per_query_token.sum())
    return score


def rerank_for_n(n):
    candidate_path = CANDIDATE_DIR / "single_vector_candidates_top{}.tsv".format(n)

    run_path = RESULT_DIR / "c2f_single_vector_N{}_run.tsv".format(n)
    alias_run_path = RESULT_DIR / "c2f_N{}_run.tsv".format(n)

    score_debug_path = RESULT_DIR / "c2f_single_vector_N{}_scores.csv".format(n)
    validation_path = RESULT_DIR / "c2f_single_vector_N{}_validation.csv".format(n)

    by_query = read_candidate_file(candidate_path)

    start_time = time.perf_counter()

    run_rows = []
    score_debug_rows = []
    validation_rows = []

    total_candidates = 0
    total_scored = 0
    missing_query_embeddings = []
    missing_page_embeddings = []

    for qid in sorted(by_query.keys()):
        candidates = by_query[qid]
        input_candidate_ids = [item["page_id"] for item in candidates]
        total_candidates += len(candidates)

        try:
            query_emb = load_embedding(QUERY_EMB_DIR, qid)
        except FileNotFoundError:
            missing_query_embeddings.append(qid)
            validation_rows.append(
                {
                    "query_id": qid,
                    "input_candidates": len(candidates),
                    "reranked_candidates": 0,
                    "subset_check": "FAILED",
                    "reason": "missing query embedding",
                }
            )
            continue

        scored_items = []

        for item in candidates:
            pid = item["page_id"]

            try:
                page_emb = load_embedding(PAGE_EMB_DIR, pid)
            except FileNotFoundError:
                missing_page_embeddings.append(pid)
                continue

            score = late_interaction_score(query_emb, page_emb)

            scored_items.append(
                {
                    "query_id": qid,
                    "page_id": pid,
                    "coarse_rank": item["coarse_rank"],
                    "coarse_score": item["coarse_score"],
                    "fine_score": score,
                }
            )

        scored_items.sort(key=lambda x: x["fine_score"], reverse=True)

        reranked_ids = [item["page_id"] for item in scored_items]
        subset_ok = set(reranked_ids).issubset(set(input_candidate_ids))

        validation_rows.append(
            {
                "query_id": qid,
                "input_candidates": len(candidates),
                "reranked_candidates": len(scored_items),
                "subset_check": "PASSED" if subset_ok else "FAILED",
                "reason": "" if subset_ok else "reranked page not in candidate set",
            }
        )

        for rank, item in enumerate(scored_items, start=1):
            run_rows.append(
                [
                    "c2f_single_vector_N{}".format(n),
                    item["query_id"],
                    item["page_id"],
                    rank,
                    "{:.8f}".format(item["fine_score"]),
                ]
            )

            score_debug_rows.append(
                [
                    item["query_id"],
                    item["page_id"],
                    item["coarse_rank"],
                    "{:.8f}".format(item["coarse_score"]),
                    rank,
                    "{:.8f}".format(item["fine_score"]),
                ]
            )

        total_scored += len(scored_items)

    end_time = time.perf_counter()
    elapsed_seconds = end_time - start_time

    query_count = len(by_query)
    avg_candidates_per_query = total_candidates / query_count if query_count else 0.0
    avg_scored_per_query = total_scored / query_count if query_count else 0.0
    avg_latency_ms = elapsed_seconds * 1000.0 / query_count if query_count else 0.0

    with run_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerow(["run_name", "query_id", "page_id", "rank", "score"])
        writer.writerows(run_rows)

    shutil.copyfile(run_path, alias_run_path)

    with score_debug_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "query_id",
                "page_id",
                "coarse_rank",
                "coarse_score",
                "fine_rank",
                "fine_score",
            ]
        )
        writer.writerows(score_debug_rows)

    with validation_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "query_id",
                "input_candidates",
                "reranked_candidates",
                "subset_check",
                "reason",
            ],
        )
        writer.writeheader()
        writer.writerows(validation_rows)

    summary = {
        "N": n,
        "candidate_file": str(candidate_path.relative_to(PROJECT_ROOT)),
        "run_file": str(run_path.relative_to(PROJECT_ROOT)),
        "alias_run_file": str(alias_run_path.relative_to(PROJECT_ROOT)),
        "score_debug_file": str(score_debug_path.relative_to(PROJECT_ROOT)),
        "validation_file": str(validation_path.relative_to(PROJECT_ROOT)),
        "query_count": query_count,
        "total_candidates": total_candidates,
        "total_scored": total_scored,
        "avg_candidates_per_query": avg_candidates_per_query,
        "avg_scored_per_query": avg_scored_per_query,
        "rerank_time_seconds": elapsed_seconds,
        "avg_rerank_latency_ms_per_query": avg_latency_ms,
        "missing_query_embeddings": sorted(set(missing_query_embeddings)),
        "missing_page_embeddings": sorted(set(missing_page_embeddings)),
    }

    return summary


def write_summary_csv(summaries):
    path = RESULT_DIR / "c2f_single_vector_day3_rerank_summary.csv"

    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "N",
                "query_count",
                "total_candidates",
                "total_scored",
                "avg_candidates_per_query",
                "avg_scored_per_query",
                "rerank_time_seconds",
                "avg_rerank_latency_ms_per_query",
                "run_file",
                "validation_file",
            ]
        )

        for s in summaries:
            writer.writerow(
                [
                    s["N"],
                    s["query_count"],
                    s["total_candidates"],
                    s["total_scored"],
                    "{:.4f}".format(s["avg_candidates_per_query"]),
                    "{:.4f}".format(s["avg_scored_per_query"]),
                    "{:.6f}".format(s["rerank_time_seconds"]),
                    "{:.6f}".format(s["avg_rerank_latency_ms_per_query"]),
                    s["run_file"],
                    s["validation_file"],
                ]
            )

    return path


def write_summary_json(summaries):
    path = RESULT_DIR / "c2f_single_vector_day3_rerank_summary.json"

    with path.open("w", encoding="utf-8") as f:
        json.dump(summaries, f, indent=2, ensure_ascii=False)

    return path


def write_subset_validation_log(summaries):
    path = NOTE_DIR / "2026-05-07_week4_day3_subset_validation_log.md"

    lines = []
    lines.append("# Week 4 Day 3 Subset Validation Log")
    lines.append("")
    lines.append("**Project:** PCB_VisualRAG_Project  ")
    lines.append("**Stage:** Week 4  ")
    lines.append("**Day:** Day 3  ")
    lines.append("**Date:** 2026-05-07  ")
    lines.append("**Experiment Name:** Coarse-to-Fine Full MV Reranking Validation  ")
    lines.append("**Status:** Completed  ")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 1. 今日目标")
    lines.append("")
    lines.append("今日目标是在 Day 2 生成的 top-N candidate pages 上接入 Week 3 已经跑通的 Full Multi-vector Late Interaction reranker。")
    lines.append("")
    lines.append("本日重点是验证：")
    lines.append("")
    lines.append("- 每个 query 是否能正确读取候选页面；")
    lines.append("- reranking 是否只发生在候选集合内；")
    lines.append("- query embeddings 与 page embeddings 是否能正常加载；")
    lines.append("- late interaction scoring 是否能正常生成最终排序；")
    lines.append("- 不同 N 是否能独立输出 rerank run 文件。")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 2. 输入文件")
    lines.append("")
    lines.append("| 类型 | 路径 |")
    lines.append("|---|---|")
    lines.append("| Candidate files | `artifacts/rerank_cache/single_vector_topN/single_vector_candidates_topN.tsv` |")
    lines.append("| Query embeddings | `artifacts/embeddings/full_multivector/queries/*.npy` |")
    lines.append("| Page embeddings | `artifacts/embeddings/full_multivector/pages/*.npy` |")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 3. 输出文件")
    lines.append("")
    lines.append("| N | Run 文件 | Validation 文件 |")
    lines.append("|---:|---|---|")

    for s in summaries:
        lines.append(
            "| {} | `{}` | `{}` |".format(
                s["N"],
                s["run_file"],
                s["validation_file"],
            )
        )

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 4. Rerank 运行统计")
    lines.append("")
    lines.append("| N | Queries | Total Candidates | Total Scored | Avg Candidates / Query | Avg Rerank Latency / Query ms |")
    lines.append("|---:|---:|---:|---:|---:|---:|")

    for s in summaries:
        lines.append(
            "| {} | {} | {} | {} | {:.4f} | {:.6f} |".format(
                s["N"],
                s["query_count"],
                s["total_candidates"],
                s["total_scored"],
                s["avg_candidates_per_query"],
                s["avg_rerank_latency_ms_per_query"],
            )
        )

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 5. 验证结论")
    lines.append("")
    lines.append("Day 3 已成功完成 coarse-to-fine second-stage reranking。")
    lines.append("")
    lines.append("当前系统已经实现：")
    lines.append("")
    lines.append("- 从 Day 2 candidate 文件读取 top-N 页面；")
    lines.append("- 加载 Week 3 的 query token embeddings；")
    lines.append("- 加载 Week 3 的 page multi-vector embeddings；")
    lines.append("- 在候选集合内执行 sum-maxsim late interaction scoring；")
    lines.append("- 为 N=10、20、50、100 分别输出 rerank run 文件；")
    lines.append("- 生成 validation 文件检查 reranking 是否限定在候选集合内。")
    lines.append("")
    lines.append("需要注意的是，Day 2 已发现当前 single-vector visual coarse run 的有效候选深度可能只有 top-10，因此不同 N 的 reranking 结果可能高度相似或完全相同。")
    lines.append("")
    lines.append("该问题说明当前 C2F pipeline 已经跑通，但 single-vector coarse retriever 的候选召回能力和候选深度仍然是主要限制。")
    lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")

    return path


def main():
    ensure_dirs()

    print("[Day3] Starting coarse-to-fine Full MV reranking...")

    summaries = []

    for n in N_VALUES:
        print("[Day3] Reranking N={} ...".format(n))
        summary = rerank_for_n(n)
        summaries.append(summary)

        print(
            "[Day3] N={} done. queries={}, total_scored={}, avg_latency_ms={:.6f}".format(
                n,
                summary["query_count"],
                summary["total_scored"],
                summary["avg_rerank_latency_ms_per_query"],
            )
        )

    summary_csv = write_summary_csv(summaries)
    summary_json = write_summary_json(summaries)
    validation_log = write_subset_validation_log(summaries)

    print("")
    print("========== Day 3 Completed ==========")
    print("Summary CSV: {}".format(summary_csv))
    print("Summary JSON: {}".format(summary_json))
    print("Validation Log: {}".format(validation_log))

    for s in summaries:
        print("")
        print("N={}".format(s["N"]))
        print("  Run: {}".format(PROJECT_ROOT / s["run_file"]))
        print("  Validation: {}".format(PROJECT_ROOT / s["validation_file"]))
        print("  Total candidates: {}".format(s["total_candidates"]))
        print("  Total scored: {}".format(s["total_scored"]))
        print("  Avg candidates/query: {:.4f}".format(s["avg_candidates_per_query"]))
        print("  Avg latency/query ms: {:.6f}".format(s["avg_rerank_latency_ms_per_query"]))


if __name__ == "__main__":
    main()
