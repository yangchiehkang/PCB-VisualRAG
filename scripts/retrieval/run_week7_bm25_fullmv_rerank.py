from pathlib import Path
from collections import defaultdict
import csv
import json
import time

import numpy as np


PROJECT_ROOT = Path(r"E:\Working\PCB_VisualRAG_Project")

CANDIDATE_DIR = PROJECT_ROOT / "artifacts" / "rerank_cache" / "week7_topN"
QUERY_EMB_DIR = PROJECT_ROOT / "artifacts" / "embeddings" / "full_multivector" / "queries"
PAGE_EMB_DIR = PROJECT_ROOT / "artifacts" / "embeddings" / "full_multivector" / "pages"

RESULT_DIR = PROJECT_ROOT / "results" / "week7" / "c2f_fixed_N"

N_VALUES = [10, 20, 50, 100]
FINAL_TOP_K = 10


def ensure_dirs():
    RESULT_DIR.mkdir(parents=True, exist_ok=True)


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


def is_header(row):
    joined = "\t".join(row).lower()
    keywords = [
        "query_id",
        "candidate_page_id",
        "page_id",
        "doc_id",
        "rank",
        "score",
        "run_name",
    ]
    return any(k in joined for k in keywords)


def parse_candidate_rows(path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f, delimiter="\t"))

    if not rows:
        return []

    parsed = []

    first = rows[0]
    has_header = is_header(first)

    if has_header:
        header = first
        data_rows = rows[1:]
        col_idx = {name: i for i, name in enumerate(header)}

        lower_to_original = {name.lower(): name for name in header}

        def get_col(row, names, default=""):
            for name in names:
                original = lower_to_original.get(name.lower())
                if original is not None:
                    idx = col_idx[original]
                    if idx < len(row):
                        return row[idx].strip()
            return default

        for row in data_rows:
            qid = get_col(row, ["query_id", "qid"])
            pid = get_col(row, ["candidate_page_id", "page_id", "doc_id", "docid", "pid"])
            rank = get_col(row, ["coarse_rank", "rank"], "999999")
            score = get_col(row, ["coarse_score", "score"], "0.0")

            if qid and pid:
                parsed.append(
                    {
                        "query_id": qid,
                        "candidate_page_id": pid,
                        "coarse_rank": rank,
                        "coarse_score": score,
                    }
                )

        return parsed

    for row in rows:
        if len(row) >= 6 and row[1].strip().upper() == "Q0":
            parsed.append(
                {
                    "query_id": row[0].strip(),
                    "candidate_page_id": row[2].strip(),
                    "coarse_rank": row[3].strip(),
                    "coarse_score": row[4].strip(),
                }
            )

        elif len(row) >= 5 and row[0].strip().lower().startswith("bm25"):
            parsed.append(
                {
                    "query_id": row[1].strip(),
                    "candidate_page_id": row[2].strip(),
                    "coarse_rank": row[3].strip(),
                    "coarse_score": row[4].strip(),
                }
            )

        elif len(row) >= 4:
            parsed.append(
                {
                    "query_id": row[0].strip(),
                    "candidate_page_id": row[1].strip(),
                    "coarse_rank": row[2].strip(),
                    "coarse_score": row[3].strip(),
                }
            )

    return parsed


def read_candidate_file(path):
    if not path.exists():
        raise FileNotFoundError("Candidate file not found: {}".format(path))

    by_query = defaultdict(list)
    rows = parse_candidate_rows(path)

    for row in rows:
        qid = row["query_id"]
        pid = row["candidate_page_id"]

        if not qid or not pid:
            continue

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
    candidate_path = CANDIDATE_DIR / "candidates_bm25_N{}.tsv".format(n)

    run_path = RESULT_DIR / "bm25_fullmv_N{}_run.tsv".format(n)
    score_debug_path = RESULT_DIR / "bm25_fullmv_N{}_scores.csv".format(n)
    validation_path = RESULT_DIR / "bm25_fullmv_N{}_validation.csv".format(n)

    by_query = read_candidate_file(candidate_path)

    start_time = time.perf_counter()

    run_rows = []
    score_debug_rows = []
    validation_rows = []

    total_candidates = 0
    total_scored = 0
    total_written = 0

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
                    "scored_candidates": 0,
                    "written_candidates": 0,
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

            fine_score = late_interaction_score(query_emb, page_emb)

            scored_items.append(
                {
                    "query_id": qid,
                    "page_id": pid,
                    "coarse_rank": item["coarse_rank"],
                    "coarse_score": item["coarse_score"],
                    "fine_score": fine_score,
                }
            )

        scored_items.sort(key=lambda x: x["fine_score"], reverse=True)

        reranked_ids = [item["page_id"] for item in scored_items]
        subset_ok = set(reranked_ids).issubset(set(input_candidate_ids))

        write_items = scored_items[:FINAL_TOP_K]

        if len(scored_items) == 0:
            subset_status = "FAILED"
            reason = "zero scored candidates"
        elif not subset_ok:
            subset_status = "FAILED"
            reason = "reranked page not in candidate set"
        else:
            subset_status = "PASSED"
            reason = ""

        validation_rows.append(
            {
                "query_id": qid,
                "input_candidates": len(candidates),
                "scored_candidates": len(scored_items),
                "written_candidates": len(write_items),
                "subset_check": subset_status,
                "reason": reason,
            }
        )

        for rank, item in enumerate(write_items, start=1):
            run_rows.append(
                [
                    "bm25_fullmv_N{}".format(n),
                    item["query_id"],
                    item["page_id"],
                    rank,
                    "{:.8f}".format(item["fine_score"]),
                ]
            )

        for rank, item in enumerate(scored_items, start=1):
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
        total_written += len(write_items)

    end_time = time.perf_counter()
    elapsed_seconds = end_time - start_time

    query_count = len(by_query)
    avg_candidates_per_query = total_candidates / query_count if query_count else 0.0
    avg_scored_per_query = total_scored / query_count if query_count else 0.0
    avg_written_per_query = total_written / query_count if query_count else 0.0
    avg_latency_ms = elapsed_seconds * 1000.0 / query_count if query_count else 0.0

    with run_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerow(["run_name", "query_id", "page_id", "rank", "score"])
        writer.writerows(run_rows)

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
                "scored_candidates",
                "written_candidates",
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
        "score_debug_file": str(score_debug_path.relative_to(PROJECT_ROOT)),
        "validation_file": str(validation_path.relative_to(PROJECT_ROOT)),
        "query_count": query_count,
        "final_top_k": FINAL_TOP_K,
        "total_candidates": total_candidates,
        "total_scored": total_scored,
        "total_written": total_written,
        "avg_candidates_per_query": avg_candidates_per_query,
        "avg_scored_per_query": avg_scored_per_query,
        "avg_written_per_query": avg_written_per_query,
        "rerank_time_seconds": elapsed_seconds,
        "avg_rerank_latency_ms_per_query": avg_latency_ms,
        "missing_query_embeddings": sorted(set(missing_query_embeddings)),
        "missing_page_embeddings": sorted(set(missing_page_embeddings)),
    }

    return summary


def write_summary_csv(summaries):
    path = RESULT_DIR / "bm25_fullmv_rerank_summary.csv"

    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)

        writer.writerow(
            [
                "N",
                "query_count",
                "final_top_k",
                "total_candidates",
                "total_scored",
                "total_written",
                "avg_candidates_per_query",
                "avg_scored_per_query",
                "avg_written_per_query",
                "rerank_time_seconds",
                "avg_rerank_latency_ms_per_query",
                "candidate_file",
                "run_file",
                "validation_file",
                "missing_query_embeddings_count",
                "missing_page_embeddings_count",
            ]
        )

        for s in summaries:
            writer.writerow(
                [
                    s["N"],
                    s["query_count"],
                    s["final_top_k"],
                    s["total_candidates"],
                    s["total_scored"],
                    s["total_written"],
                    "{:.4f}".format(s["avg_candidates_per_query"]),
                    "{:.4f}".format(s["avg_scored_per_query"]),
                    "{:.4f}".format(s["avg_written_per_query"]),
                    "{:.6f}".format(s["rerank_time_seconds"]),
                    "{:.6f}".format(s["avg_rerank_latency_ms_per_query"]),
                    s["candidate_file"],
                    s["run_file"],
                    s["validation_file"],
                    len(s["missing_query_embeddings"]),
                    len(s["missing_page_embeddings"]),
                ]
            )

    return path


def write_summary_json(summaries):
    path = RESULT_DIR / "bm25_fullmv_rerank_summary.json"

    with path.open("w", encoding="utf-8") as f:
        json.dump(summaries, f, indent=2, ensure_ascii=False)

    return path


def main():
    ensure_dirs()

    print("[Week7-Day2] Starting BM25 + Full MV reranking...")

    summaries = []

    for n in N_VALUES:
        print("[Week7-Day2] Reranking BM25 candidates N={} ...".format(n))

        summary = rerank_for_n(n)
        summaries.append(summary)

        print(
            "[Week7-Day2] N={} done. queries={}, total_candidates={}, total_scored={}, total_written={}, avg_latency_ms={:.6f}".format(
                n,
                summary["query_count"],
                summary["total_candidates"],
                summary["total_scored"],
                summary["total_written"],
                summary["avg_rerank_latency_ms_per_query"],
            )
        )

        if summary["missing_query_embeddings"]:
            print("  Missing query embeddings: {}".format(summary["missing_query_embeddings"]))

        if summary["missing_page_embeddings"]:
            print("  Missing page embeddings count: {}".format(len(summary["missing_page_embeddings"])))
            print("  Missing page embeddings sample: {}".format(summary["missing_page_embeddings"][:10]))

    summary_csv = write_summary_csv(summaries)
    summary_json = write_summary_json(summaries)

    print("")
    print("========== Week7 Day2 BM25 + Full MV Completed ==========")
    print("Summary CSV: {}".format(summary_csv))
    print("Summary JSON: {}".format(summary_json))

    for s in summaries:
        print("")
        print("N={}".format(s["N"]))
        print("  Candidate: {}".format(PROJECT_ROOT / s["candidate_file"]))
        print("  Run: {}".format(PROJECT_ROOT / s["run_file"]))
        print("  Validation: {}".format(PROJECT_ROOT / s["validation_file"]))
        print("  Total candidates: {}".format(s["total_candidates"]))
        print("  Total scored: {}".format(s["total_scored"]))
        print("  Total written: {}".format(s["total_written"]))
        print("  Avg candidates/query: {:.4f}".format(s["avg_candidates_per_query"]))
        print("  Avg scored/query: {:.4f}".format(s["avg_scored_per_query"]))
        print("  Avg written/query: {:.4f}".format(s["avg_written_per_query"]))
        print("  Avg latency/query ms: {:.6f}".format(s["avg_rerank_latency_ms_per_query"]))


if __name__ == "__main__":
    main()
