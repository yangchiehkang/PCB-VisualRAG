from pathlib import Path
from collections import defaultdict
import csv
import json


PROJECT_ROOT = Path(r"E:\Working\PCB_VisualRAG_Project")

INPUT_DIR = PROJECT_ROOT / "results" / "week7" / "c2f_fixed_N"
OUTPUT_DIR = PROJECT_ROOT / "results" / "week7" / "score_normalized"

EPS = 1e-8


INPUT_FILES = [
    {
        "method": "fullmv",
        "setting": "fullmv_N10",
        "input_file": INPUT_DIR / "bm25_fullmv_N10_scores.csv",
        "output_file": OUTPUT_DIR / "bm25_fullmv_N10_normalized_scores.csv",
    },
    {
        "method": "fullmv",
        "setting": "fullmv_N20",
        "input_file": INPUT_DIR / "bm25_fullmv_N20_scores.csv",
        "output_file": OUTPUT_DIR / "bm25_fullmv_N20_normalized_scores.csv",
    },
    {
        "method": "fullmv",
        "setting": "fullmv_N50",
        "input_file": INPUT_DIR / "bm25_fullmv_N50_scores.csv",
        "output_file": OUTPUT_DIR / "bm25_fullmv_N50_normalized_scores.csv",
    },
    {
        "method": "fullmv",
        "setting": "fullmv_N100",
        "input_file": INPUT_DIR / "bm25_fullmv_N100_scores.csv",
        "output_file": OUTPUT_DIR / "bm25_fullmv_N100_normalized_scores.csv",
    },
    {
        "method": "budgetmv",
        "setting": "budgetmv_N20_M8_none",
        "input_file": INPUT_DIR / "bm25_budgetmv_N20_M8_none_scores.csv",
        "output_file": OUTPUT_DIR / "bm25_budgetmv_N20_M8_none_normalized_scores.csv",
    },
    {
        "method": "budgetmv",
        "setting": "budgetmv_N20_M16_none",
        "input_file": INPUT_DIR / "bm25_budgetmv_N20_M16_none_scores.csv",
        "output_file": OUTPUT_DIR / "bm25_budgetmv_N20_M16_none_normalized_scores.csv",
    },
    {
        "method": "budgetmv",
        "setting": "budgetmv_N50_M24_none",
        "input_file": INPUT_DIR / "bm25_budgetmv_N50_M24_none_scores.csv",
        "output_file": OUTPUT_DIR / "bm25_budgetmv_N50_M24_none_normalized_scores.csv",
    },
]


def ensure_dirs():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def read_score_file(path):
    if not path.exists():
        raise FileNotFoundError("Input score file not found: {}".format(path))

    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        rows = []

        for row in reader:
            rows.append(row)

    return rows


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


def minmax_normalize(values):
    if not values:
        return []

    min_v = min(values)
    max_v = max(values)
    denom = max_v - min_v + EPS

    return [(v - min_v) / denom for v in values]


def normalize_rows(rows):
    by_query = defaultdict(list)

    for row in rows:
        qid = row.get("query_id", "").strip()
        if qid:
            by_query[qid].append(row)

    normalized_rows = []

    query_summaries = []

    for qid in sorted(by_query.keys()):
        qrows = by_query[qid]

        bm25_scores = [to_float(r.get("coarse_score", 0.0)) for r in qrows]
        mv_scores = [to_float(r.get("fine_score", 0.0)) for r in qrows]

        bm25_norm = minmax_normalize(bm25_scores)
        mv_norm = minmax_normalize(mv_scores)

        bm25_min = min(bm25_scores) if bm25_scores else 0.0
        bm25_max = max(bm25_scores) if bm25_scores else 0.0
        mv_min = min(mv_scores) if mv_scores else 0.0
        mv_max = max(mv_scores) if mv_scores else 0.0

        for i, row in enumerate(qrows):
            out = dict(row)

            out["bm25_score_raw"] = "{:.8f}".format(bm25_scores[i])
            out["mv_score_raw"] = "{:.8f}".format(mv_scores[i])
            out["bm25_score_norm"] = "{:.8f}".format(bm25_norm[i])
            out["mv_score_norm"] = "{:.8f}".format(mv_norm[i])

            out["query_bm25_min"] = "{:.8f}".format(bm25_min)
            out["query_bm25_max"] = "{:.8f}".format(bm25_max)
            out["query_mv_min"] = "{:.8f}".format(mv_min)
            out["query_mv_max"] = "{:.8f}".format(mv_max)

            normalized_rows.append(out)

        query_summaries.append(
            {
                "query_id": qid,
                "candidate_count": len(qrows),
                "bm25_min": bm25_min,
                "bm25_max": bm25_max,
                "mv_min": mv_min,
                "mv_max": mv_max,
                "bm25_norm_min": min(bm25_norm) if bm25_norm else 0.0,
                "bm25_norm_max": max(bm25_norm) if bm25_norm else 0.0,
                "mv_norm_min": min(mv_norm) if mv_norm else 0.0,
                "mv_norm_max": max(mv_norm) if mv_norm else 0.0,
            }
        )

    return normalized_rows, query_summaries


def get_fieldnames(rows):
    base = [
        "query_id",
        "page_id",
        "coarse_rank",
        "coarse_score",
        "fine_rank",
        "fine_score",
        "bm25_score_raw",
        "mv_score_raw",
        "bm25_score_norm",
        "mv_score_norm",
        "query_bm25_min",
        "query_bm25_max",
        "query_mv_min",
        "query_mv_max",
    ]

    extra = []

    for row in rows:
        for key in row.keys():
            if key not in base and key not in extra:
                extra.append(key)

    ordered = []

    for key in base:
        if any(key in row for row in rows):
            ordered.append(key)

    for key in extra:
        if key not in ordered:
            ordered.append(key)

    return ordered


def write_normalized_file(rows, path):
    fieldnames = get_fieldnames(rows)

    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for row in rows:
            writer.writerow(row)


def write_summary_csv(summaries):
    path = OUTPUT_DIR / "score_normalization_summary.csv"

    fieldnames = [
        "method",
        "setting",
        "input_file",
        "output_file",
        "query_count",
        "total_rows",
        "avg_candidates_per_query",
        "bm25_norm_global_min",
        "bm25_norm_global_max",
        "mv_norm_global_min",
        "mv_norm_global_max",
        "status",
    ]

    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for s in summaries:
            writer.writerow(s)

    return path


def write_summary_json(summaries):
    path = OUTPUT_DIR / "score_normalization_summary.json"

    with path.open("w", encoding="utf-8") as f:
        json.dump(summaries, f, indent=2, ensure_ascii=False)

    return path


def main():
    ensure_dirs()

    print("[Week7-Day3] Starting score normalization...")

    summaries = []

    for item in INPUT_FILES:
        method = item["method"]
        setting = item["setting"]
        input_file = item["input_file"]
        output_file = item["output_file"]

        print("[Week7-Day3] Normalizing {} ...".format(setting))

        rows = read_score_file(input_file)
        normalized_rows, query_summaries = normalize_rows(rows)

        write_normalized_file(normalized_rows, output_file)

        bm25_norm_values = [to_float(r.get("bm25_score_norm", 0.0)) for r in normalized_rows]
        mv_norm_values = [to_float(r.get("mv_score_norm", 0.0)) for r in normalized_rows]

        query_count = len(query_summaries)
        total_rows = len(normalized_rows)
        avg_candidates = total_rows / query_count if query_count else 0.0

        bm25_norm_global_min = min(bm25_norm_values) if bm25_norm_values else 0.0
        bm25_norm_global_max = max(bm25_norm_values) if bm25_norm_values else 0.0
        mv_norm_global_min = min(mv_norm_values) if mv_norm_values else 0.0
        mv_norm_global_max = max(mv_norm_values) if mv_norm_values else 0.0

        status = "PASSED"

        if total_rows == 0:
            status = "FAILED_ZERO_ROWS"

        if bm25_norm_global_min < -1e-6 or bm25_norm_global_max > 1.000001:
            status = "FAILED_BM25_RANGE"

        if mv_norm_global_min < -1e-6 or mv_norm_global_max > 1.000001:
            status = "FAILED_MV_RANGE"

        summary = {
            "method": method,
            "setting": setting,
            "input_file": str(input_file.relative_to(PROJECT_ROOT)),
            "output_file": str(output_file.relative_to(PROJECT_ROOT)),
            "query_count": query_count,
            "total_rows": total_rows,
            "avg_candidates_per_query": "{:.4f}".format(avg_candidates),
            "bm25_norm_global_min": "{:.8f}".format(bm25_norm_global_min),
            "bm25_norm_global_max": "{:.8f}".format(bm25_norm_global_max),
            "mv_norm_global_min": "{:.8f}".format(mv_norm_global_min),
            "mv_norm_global_max": "{:.8f}".format(mv_norm_global_max),
            "status": status,
        }

        summaries.append(summary)

        print(
            "[Week7-Day3] {} done. queries={}, rows={}, avg_candidates={:.4f}, bm25_norm=[{:.4f},{:.4f}], mv_norm=[{:.4f},{:.4f}], status={}".format(
                setting,
                query_count,
                total_rows,
                avg_candidates,
                bm25_norm_global_min,
                bm25_norm_global_max,
                mv_norm_global_min,
                mv_norm_global_max,
                status,
            )
        )

    summary_csv = write_summary_csv(summaries)
    summary_json = write_summary_json(summaries)

    print("")
    print("========== Week7 Day3 Score Normalization Completed ==========")
    print("Summary CSV: {}".format(summary_csv))
    print("Summary JSON: {}".format(summary_json))

    for s in summaries:
        print("")
        print("setting={}".format(s["setting"]))
        print("  Input: {}".format(PROJECT_ROOT / s["input_file"]))
        print("  Output: {}".format(PROJECT_ROOT / s["output_file"]))
        print("  Query count: {}".format(s["query_count"]))
        print("  Total rows: {}".format(s["total_rows"]))
        print("  Avg candidates/query: {}".format(s["avg_candidates_per_query"]))
        print("  BM25 norm min/max: {} / {}".format(s["bm25_norm_global_min"], s["bm25_norm_global_max"]))
        print("  MV norm min/max: {} / {}".format(s["mv_norm_global_min"], s["mv_norm_global_max"]))
        print("  Status: {}".format(s["status"]))


if __name__ == "__main__":
    main()
