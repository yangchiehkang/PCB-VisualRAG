from pathlib import Path
from collections import defaultdict
import csv
import json
import time


PROJECT_ROOT = Path(r"E:\Working\PCB_VisualRAG_Project")

INPUT_DIR = PROJECT_ROOT / "results" / "week7" / "score_normalized"
OUTPUT_DIR = PROJECT_ROOT / "results" / "week7" / "hybrid_fusion"

FINAL_TOP_K = 10

ALPHAS = [
    0.0,
    0.1,
    0.2,
    0.3,
    0.4,
    0.5,
    0.6,
    0.7,
    0.8,
    0.9,
    1.0,
]

CONFIGS = [
    {
        "method": "fullmv",
        "setting": "fullmv_N50",
        "N": 50,
        "M": "-",
        "input_file": INPUT_DIR / "bm25_fullmv_N50_normalized_scores.csv",
    },
    {
        "method": "budgetmv",
        "setting": "budgetmv_N50_M24_none",
        "N": 50,
        "M": 24,
        "input_file": INPUT_DIR / "bm25_budgetmv_N50_M24_none_normalized_scores.csv",
    },
]


def ensure_dirs():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def alpha_tag(alpha):
    return "{:.1f}".format(alpha).replace(".", "p")


def to_float(value, default=0.0):
    try:
        return float(value)
    except Exception:
        return default


def to_int(value, default=999999):
    try:
        return int(float(value))
    except Exception:
        return default


def read_normalized_scores(path):
    if not path.exists():
        raise FileNotFoundError("Normalized score file not found: {}".format(path))

    rows = []

    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)

        for row in reader:
            qid = row.get("query_id", "").strip()
            pid = row.get("page_id", "").strip()

            if not qid or not pid:
                continue

            rows.append(
                {
                    "query_id": qid,
                    "page_id": pid,
                    "coarse_rank": to_int(row.get("coarse_rank", 999999)),
                    "fine_rank": to_int(row.get("fine_rank", 999999)),
                    "bm25_score_raw": to_float(row.get("bm25_score_raw", row.get("coarse_score", 0.0))),
                    "mv_score_raw": to_float(row.get("mv_score_raw", row.get("fine_score", 0.0))),
                    "bm25_score_norm": to_float(row.get("bm25_score_norm", 0.0)),
                    "mv_score_norm": to_float(row.get("mv_score_norm", 0.0)),
                }
            )

    return rows


def group_by_query(rows):
    by_query = defaultdict(list)

    for row in rows:
        by_query[row["query_id"]].append(row)

    return by_query


def run_fusion_for_config(config, alpha):
    method = config["method"]
    setting = config["setting"]
    n = config["N"]
    m = config["M"]
    input_file = config["input_file"]

    tag = alpha_tag(alpha)

    if method == "fullmv":
        run_name = "hybrid_fullmv_N{}_alpha{}".format(n, tag)
        run_path = OUTPUT_DIR / "{}_run.tsv".format(run_name)
        score_path = OUTPUT_DIR / "{}_scores.csv".format(run_name)
        validation_path = OUTPUT_DIR / "{}_validation.csv".format(run_name)

    else:
        run_name = "hybrid_budgetmv_N{}_M{}_alpha{}".format(n, m, tag)
        run_path = OUTPUT_DIR / "{}_run.tsv".format(run_name)
        score_path = OUTPUT_DIR / "{}_scores.csv".format(run_name)
        validation_path = OUTPUT_DIR / "{}_validation.csv".format(run_name)

    rows = read_normalized_scores(input_file)
    by_query = group_by_query(rows)

    start = time.perf_counter()

    run_rows = []
    score_rows = []
    validation_rows = []

    total_candidates = 0
    total_written = 0

    for qid in sorted(by_query.keys()):
        qrows = by_query[qid]
        total_candidates += len(qrows)

        scored = []

        for row in qrows:
            hybrid_score = alpha * row["bm25_score_norm"] + (1.0 - alpha) * row["mv_score_norm"]

            item = dict(row)
            item["hybrid_score"] = hybrid_score
            scored.append(item)

        scored.sort(
            key=lambda x: (
                x["hybrid_score"],
                x["bm25_score_norm"],
                x["mv_score_norm"],
                -x["coarse_rank"],
            ),
            reverse=True,
        )

        write_items = scored[:FINAL_TOP_K]
        total_written += len(write_items)

        subset_ok = set([x["page_id"] for x in write_items]).issubset(set([x["page_id"] for x in qrows]))

        if len(write_items) == 0:
            subset_check = "FAILED"
            reason = "zero written candidates"
        elif not subset_ok:
            subset_check = "FAILED"
            reason = "written page not in input candidates"
        else:
            subset_check = "PASSED"
            reason = ""

        validation_rows.append(
            {
                "query_id": qid,
                "input_candidates": len(qrows),
                "written_candidates": len(write_items),
                "subset_check": subset_check,
                "reason": reason,
            }
        )

        for rank, item in enumerate(write_items, start=1):
            run_rows.append(
                [
                    run_name,
                    item["query_id"],
                    item["page_id"],
                    rank,
                    "{:.8f}".format(item["hybrid_score"]),
                ]
            )

        for rank, item in enumerate(scored, start=1):
            score_rows.append(
                [
                    item["query_id"],
                    item["page_id"],
                    item["coarse_rank"],
                    item["fine_rank"],
                    "{:.8f}".format(item["bm25_score_raw"]),
                    "{:.8f}".format(item["mv_score_raw"]),
                    "{:.8f}".format(item["bm25_score_norm"]),
                    "{:.8f}".format(item["mv_score_norm"]),
                    alpha,
                    "{:.8f}".format(item["hybrid_score"]),
                    rank,
                ]
            )

    elapsed = time.perf_counter() - start

    with run_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerow(["run_name", "query_id", "page_id", "rank", "score"])
        writer.writerows(run_rows)

    with score_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "query_id",
                "page_id",
                "coarse_rank",
                "fine_rank",
                "bm25_score_raw",
                "mv_score_raw",
                "bm25_score_norm",
                "mv_score_norm",
                "alpha",
                "hybrid_score",
                "hybrid_rank",
            ]
        )
        writer.writerows(score_rows)

    with validation_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "query_id",
                "input_candidates",
                "written_candidates",
                "subset_check",
                "reason",
            ],
        )
        writer.writeheader()
        writer.writerows(validation_rows)

    query_count = len(by_query)
    avg_candidates = total_candidates / query_count if query_count else 0.0
    avg_written = total_written / query_count if query_count else 0.0
    avg_latency_ms = elapsed * 1000.0 / query_count if query_count else 0.0

    failed_count = sum(1 for x in validation_rows if x["subset_check"] != "PASSED")

    return {
        "method": method,
        "setting": setting,
        "N": n,
        "M": m,
        "alpha": alpha,
        "run_name": run_name,
        "input_file": str(input_file.relative_to(PROJECT_ROOT)),
        "run_file": str(run_path.relative_to(PROJECT_ROOT)),
        "score_file": str(score_path.relative_to(PROJECT_ROOT)),
        "validation_file": str(validation_path.relative_to(PROJECT_ROOT)),
        "query_count": query_count,
        "final_top_k": FINAL_TOP_K,
        "total_candidates": total_candidates,
        "total_written": total_written,
        "avg_candidates_per_query": avg_candidates,
        "avg_written_per_query": avg_written,
        "fusion_time_seconds": elapsed,
        "avg_fusion_latency_ms_per_query": avg_latency_ms,
        "failed_validation_count": failed_count,
        "status": "PASSED" if failed_count == 0 and total_written > 0 else "FAILED",
    }


def write_summary_csv(summaries):
    path = OUTPUT_DIR / "hybrid_fusion_summary.csv"

    fieldnames = [
        "method",
        "setting",
        "N",
        "M",
        "alpha",
        "run_name",
        "query_count",
        "final_top_k",
        "total_candidates",
        "total_written",
        "avg_candidates_per_query",
        "avg_written_per_query",
        "fusion_time_seconds",
        "avg_fusion_latency_ms_per_query",
        "failed_validation_count",
        "status",
        "input_file",
        "run_file",
        "score_file",
        "validation_file",
    ]

    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for s in summaries:
            row = dict(s)
            row["alpha"] = "{:.1f}".format(s["alpha"])
            row["avg_candidates_per_query"] = "{:.4f}".format(s["avg_candidates_per_query"])
            row["avg_written_per_query"] = "{:.4f}".format(s["avg_written_per_query"])
            row["fusion_time_seconds"] = "{:.6f}".format(s["fusion_time_seconds"])
            row["avg_fusion_latency_ms_per_query"] = "{:.6f}".format(s["avg_fusion_latency_ms_per_query"])
            writer.writerow(row)

    return path


def write_summary_json(summaries):
    path = OUTPUT_DIR / "hybrid_fusion_summary.json"

    with path.open("w", encoding="utf-8") as f:
        json.dump(summaries, f, indent=2, ensure_ascii=False)

    return path


def main():
    ensure_dirs()

    print("[Week7-Day3] Starting hybrid fusion rerank...")

    summaries = []

    for config in CONFIGS:
        for alpha in ALPHAS:
            print(
                "[Week7-Day3] Fusion setting={} alpha={:.1f} ...".format(
                    config["setting"],
                    alpha,
                )
            )

            summary = run_fusion_for_config(config, alpha)
            summaries.append(summary)

            print(
                "[Week7-Day3] {} alpha={:.1f} done. queries={}, candidates={}, written={}, latency_ms={:.6f}, status={}".format(
                    config["setting"],
                    alpha,
                    summary["query_count"],
                    summary["total_candidates"],
                    summary["total_written"],
                    summary["avg_fusion_latency_ms_per_query"],
                    summary["status"],
                )
            )

    summary_csv = write_summary_csv(summaries)
    summary_json = write_summary_json(summaries)

    print("")
    print("========== Week7 Day3 Hybrid Fusion Completed ==========")
    print("Summary CSV: {}".format(summary_csv))
    print("Summary JSON: {}".format(summary_json))

    for s in summaries:
        print("")
        print("setting={} alpha={:.1f}".format(s["setting"], s["alpha"]))
        print("  Run: {}".format(PROJECT_ROOT / s["run_file"]))
        print("  Validation: {}".format(PROJECT_ROOT / s["validation_file"]))
        print("  Total candidates: {}".format(s["total_candidates"]))
        print("  Total written: {}".format(s["total_written"]))
        print("  Avg candidates/query: {:.4f}".format(s["avg_candidates_per_query"]))
        print("  Avg written/query: {:.4f}".format(s["avg_written_per_query"]))
        print("  Status: {}".format(s["status"]))


if __name__ == "__main__":
    main()
