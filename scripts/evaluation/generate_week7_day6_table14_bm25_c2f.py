from pathlib import Path
from collections import OrderedDict
import csv
import json
import re


PROJECT_ROOT = Path(r"E:\Working\PCB_VisualRAG_Project")

RESULTS_ROOT = PROJECT_ROOT / "results" / "week7"
OUTPUT_DIR = RESULTS_ROOT / "day6_core_tables"

OUTPUT_CSV = OUTPUT_DIR / "table14_bm25_c2f_main_results.csv"
OUTPUT_MD = OUTPUT_DIR / "table14_bm25_c2f_main_results.md"
OUTPUT_JSON = OUTPUT_DIR / "table14_bm25_c2f_main_results.json"


TARGET_METHODS = OrderedDict([
    ("BM25", ["bm25"]),
    ("BM25 + Full MV", ["fullmv", "full_mv", "full mv", "bm25_fullmv"]),
    ("BM25 + Budgeted MV", ["budgetmv", "budgeted", "budget_mv", "bm25_budgetmv"]),
    ("Hybrid Fusion", ["hybrid", "fusion", "hybrid_fusion"]),
])


METRIC_ALIASES = {
    "Recall@1": [
        "Recall@1", "recall@1", "R@1", "r@1",
        "Recall_1", "recall_1", "Recall@01"
    ],
    "Recall@5": [
        "Recall@5", "recall@5", "R@5", "r@5",
        "Recall_5", "recall_5", "Recall@05"
    ],
    "Recall@10": [
        "Recall@10", "recall@10", "R@10", "r@10",
        "Recall_10", "recall_10"
    ],
    "MRR@10": [
        "MRR@10", "mrr@10", "MRR_10", "mrr_10", "MRR"
    ],
    "nDCG@10": [
        "nDCG@10", "NDCG@10", "ndcg@10",
        "nDCG_10", "NDCG_10", "ndcg_10", "nDCG"
    ],
    "Index Size": [
        "Index Size", "index_size", "IndexSize",
        "index size", "Index_Size",
        "Candidate Count", "candidate_count",
        "Doc Count", "doc_count",
        "Page Count", "page_count",
        "N", "n"
    ],
}


METHOD_COLUMNS = [
    "Method", "method", "Model", "model",
    "Run", "run", "System", "system",
    "name", "Name"
]


RUN_FILE_COLUMNS = [
    "Run File", "run_file", "RunFile",
    "path", "Path", "file", "File"
]


def read_csv_rows(path):
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            return list(csv.DictReader(f))
    except UnicodeDecodeError:
        with path.open("r", encoding="gbk", newline="") as f:
            return list(csv.DictReader(f))
    except Exception:
        return []


def safe_float(value):
    if value is None:
        return None

    text = str(value).strip()

    if text == "" or text == "-":
        return None

    text = text.replace("%", "")

    try:
        return float(text)
    except Exception:
        return None


def format_metric(value, digits=4):
    if value is None:
        return "-"

    return f"{value:.{digits}f}"


def normalize_text(text):
    return str(text).lower().replace("-", "_").replace(" ", "_")


def get_value_by_alias(row, aliases):
    for alias in aliases:
        if alias in row:
            value = row.get(alias)
            if value is not None and str(value).strip() != "":
                return value

    lower_map = {str(k).lower(): k for k in row.keys()}

    for alias in aliases:
        key = lower_map.get(alias.lower())
        if key is not None:
            value = row.get(key)
            if value is not None and str(value).strip() != "":
                return value

    return None


def detect_method(text):
    norm = normalize_text(text)

    if "hybrid" in norm or "fusion" in norm:
        return "Hybrid Fusion"

    if "fullmv" in norm or "full_mv" in norm or "full" in norm and "mv" in norm:
        return "BM25 + Full MV"

    if "budgetmv" in norm or "budget_mv" in norm or "budgeted" in norm:
        return "BM25 + Budgeted MV"

    if "bm25" in norm:
        return "BM25"

    return None


def row_text_for_method(path, row):
    parts = [str(path)]

    for col in METHOD_COLUMNS:
        if col in row and row[col]:
            parts.append(str(row[col]))

    for col in RUN_FILE_COLUMNS:
        if col in row and row[col]:
            parts.append(str(row[col]))

    return " ".join(parts)


def count_run_file_lines(path):
    if not path:
        return None

    run_path = Path(path)

    if not run_path.is_absolute():
        run_path = PROJECT_ROOT / run_path

    if not run_path.exists():
        return None

    try:
        with run_path.open("r", encoding="utf-8-sig") as f:
            lines = [line for line in f if line.strip()]
        return len(lines)
    except Exception:
        return None


def extract_run_file(row):
    for col in RUN_FILE_COLUMNS:
        if col in row and row[col]:
            return row[col]
    return None


def candidate_quality(candidate):
    score = 0

    for metric in ["Recall@1", "Recall@5", "Recall@10", "MRR@10", "nDCG@10"]:
        if candidate.get(metric) is not None:
            score += 10

    if candidate.get("Index Size") not in [None, "", "-"]:
        score += 2

    source = normalize_text(candidate.get("source_file", ""))

    if "summary" in source or "results" in source or "metrics" in source:
        score += 3

    if "per_query" in source or "top" in source:
        score -= 5

    return score


def collect_candidates():
    candidates = []

    csv_files = list(RESULTS_ROOT.rglob("*.csv"))

    for csv_path in csv_files:
        if "day6_core_tables" in str(csv_path):
            continue

        rows = read_csv_rows(csv_path)

        if not rows:
            continue

        for row in rows:
            text = row_text_for_method(csv_path, row)
            method = detect_method(text)

            if method is None:
                continue

            candidate = {
                "Method": method,
                "Recall@1": safe_float(get_value_by_alias(row, METRIC_ALIASES["Recall@1"])),
                "Recall@5": safe_float(get_value_by_alias(row, METRIC_ALIASES["Recall@5"])),
                "Recall@10": safe_float(get_value_by_alias(row, METRIC_ALIASES["Recall@10"])),
                "MRR@10": safe_float(get_value_by_alias(row, METRIC_ALIASES["MRR@10"])),
                "nDCG@10": safe_float(get_value_by_alias(row, METRIC_ALIASES["nDCG@10"])),
                "Index Size": get_value_by_alias(row, METRIC_ALIASES["Index Size"]),
                "source_file": str(csv_path.relative_to(PROJECT_ROOT)),
            }

            if candidate["Index Size"] in [None, "", "-"]:
                run_file = extract_run_file(row)
                run_line_count = count_run_file_lines(run_file)

                if run_line_count is not None:
                    candidate["Index Size"] = run_line_count

            has_metric = any(
                candidate.get(metric) is not None
                for metric in ["Recall@1", "Recall@5", "Recall@10", "MRR@10", "nDCG@10"]
            )

            if has_metric:
                candidates.append(candidate)

    return candidates


def choose_best_rows(candidates):
    best = OrderedDict()

    for method in TARGET_METHODS.keys():
        method_candidates = [
            c for c in candidates
            if c["Method"] == method
        ]

        if method_candidates:
            method_candidates = sorted(
                method_candidates,
                key=candidate_quality,
                reverse=True
            )
            best[method] = method_candidates[0]
        else:
            best[method] = {
                "Method": method,
                "Recall@1": None,
                "Recall@5": None,
                "Recall@10": None,
                "MRR@10": None,
                "nDCG@10": None,
                "Index Size": "-",
                "source_file": "NOT_FOUND",
            }

    return best


def write_outputs(best_rows, all_candidates):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "Method",
        "Recall@1",
        "Recall@5",
        "Recall@10",
        "MRR@10",
        "nDCG@10",
        "Index Size",
        "Source File",
    ]

    with OUTPUT_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for method, row in best_rows.items():
            writer.writerow({
                "Method": method,
                "Recall@1": format_metric(row["Recall@1"]),
                "Recall@5": format_metric(row["Recall@5"]),
                "Recall@10": format_metric(row["Recall@10"]),
                "MRR@10": format_metric(row["MRR@10"]),
                "nDCG@10": format_metric(row["nDCG@10"]),
                "Index Size": row["Index Size"] if row["Index Size"] not in [None, ""] else "-",
                "Source File": row["source_file"],
            })

    lines = []

    lines.append("# Week 7 Day 6 Table 14: BM25-C2F 主结果表")
    lines.append("")
    lines.append("## Table 14: BM25-C2F 主结果表")
    lines.append("")
    lines.append("| Method | Recall@1 | Recall@5 | Recall@10 | MRR@10 | nDCG@10 | Index Size |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|")

    for method, row in best_rows.items():
        lines.append(
            "| {} | {} | {} | {} | {} | {} | {} |".format(
                method,
                format_metric(row["Recall@1"]),
                format_metric(row["Recall@5"]),
                format_metric(row["Recall@10"]),
                format_metric(row["MRR@10"]),
                format_metric(row["nDCG@10"]),
                row["Index Size"] if row["Index Size"] not in [None, ""] else "-",
            )
        )

    lines.append("")
    lines.append("## Source Files")
    lines.append("")
    lines.append("| Method | Source File |")
    lines.append("|---|---|")

    for method, row in best_rows.items():
        lines.append(
            "| {} | {} |".format(
                method,
                row["source_file"],
            )
        )

    lines.append("")
    lines.append("## Candidate Scan Summary")
    lines.append("")
    lines.append("- Scanned root: `results/week7`")
    lines.append("- Candidate rows found: `{}`".format(len(all_candidates)))

    OUTPUT_MD.write_text("\n".join(lines), encoding="utf-8")

    with OUTPUT_JSON.open("w", encoding="utf-8") as f:
        json.dump(
            {
                "table14": list(best_rows.values()),
                "candidate_count": len(all_candidates),
                "all_candidates": all_candidates,
            },
            f,
            indent=2,
            ensure_ascii=False,
        )


def main():
    print("[Week7-Day6] Generating Table 14: BM25-C2F main results")
    print("Scanning:", RESULTS_ROOT)

    candidates = collect_candidates()
    best_rows = choose_best_rows(candidates)

    write_outputs(best_rows, candidates)

    print("")
    print("Candidate rows found:", len(candidates))
    print("Wrote:", OUTPUT_CSV)
    print("Wrote:", OUTPUT_MD)
    print("Wrote:", OUTPUT_JSON)

    print("")
    print("========== Table 14 ==========")
    print("Method,Recall@1,Recall@5,Recall@10,MRR@10,nDCG@10,Index Size,Source File")

    for method, row in best_rows.items():
        print(
            "{},{},{},{},{},{},{},{}".format(
                method,
                format_metric(row["Recall@1"]),
                format_metric(row["Recall@5"]),
                format_metric(row["Recall@10"]),
                format_metric(row["MRR@10"]),
                format_metric(row["nDCG@10"]),
                row["Index Size"] if row["Index Size"] not in [None, ""] else "-",
                row["source_file"],
            )
        )


if __name__ == "__main__":
    main()
