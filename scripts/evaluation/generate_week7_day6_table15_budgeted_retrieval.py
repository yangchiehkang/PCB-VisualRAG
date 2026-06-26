from pathlib import Path
import csv
import json
import os
import time


PROJECT_ROOT = Path(r"E:\Working\PCB_VisualRAG_Project")

RESULTS_ROOT = PROJECT_ROOT / "results" / "week7"
OUTPUT_DIR = RESULTS_ROOT / "day6_core_tables"

OUTPUT_CSV = OUTPUT_DIR / "table15_budgeted_retrieval_configs.csv"
OUTPUT_MD = OUTPUT_DIR / "table15_budgeted_retrieval_configs.md"
OUTPUT_JSON = OUTPUT_DIR / "table15_budgeted_retrieval_configs.json"

CONFIGS = [
    {
        "Config": "Full MV",
        "N": "full",
        "M": 49,
        "Compression": "None",
        "Run File Keywords": ["fullmv", "full_mv", "bm25_fullmv"],
    },
    {
        "Config": "Budgeted Low-cost",
        "N": 20,
        "M": 8,
        "Compression": "PQ",
        "Run File Keywords": ["N20_M8", "n20_m8", "budgetmv_N20_M8", "budgetmv_n20_m8"],
    },
    {
        "Config": "Budgeted Mid-cost",
        "N": 20,
        "M": 16,
        "Compression": "PQ",
        "Run File Keywords": ["N20_M16", "n20_m16", "budgetmv_N20_M16", "budgetmv_n20_m16"],
    },
    {
        "Config": "Budgeted High-quality",
        "N": 50,
        "M": 24,
        "Compression": "PQ",
        "Run File Keywords": ["N50_M24", "n50_m24", "budgetmv_N50_M24", "budgetmv_n50_m24"],
    },
]


NDCG_KEYS = [
    "nDCG@10",
    "NDCG@10",
    "ndcg@10",
    "nDCG_10",
    "NDCG_10",
    "ndcg_10",
    "nDCG",
    "NDCG",
    "ndcg",
]


LATENCY_KEYS = [
    "Latency",
    "latency",
    "Latency_ms",
    "latency_ms",
    "Avg Latency",
    "avg_latency",
    "avg_latency_ms",
    "Mean Latency",
    "mean_latency",
]


SIZE_KEYS = [
    "Index Size MB",
    "index_size_mb",
    "IndexSizeMB",
    "size_mb",
    "Size MB",
    "storage_mb",
]


RUN_FILE_KEYS = [
    "Run File",
    "run_file",
    "RunFile",
    "path",
    "Path",
    "file",
    "File",
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


def safe_float(v):
    try:
        if v is None or str(v).strip() in ["", "-"]:
            return None
        return float(str(v).strip().replace("%", ""))
    except Exception:
        return None


def find_value(row, keys):
    lower_map = {str(k).lower(): k for k in row.keys()}

    for key in keys:
        if key in row and str(row[key]).strip() != "":
            return row[key]

    for key in keys:
        real_key = lower_map.get(key.lower())
        if real_key is not None and str(row[real_key]).strip() != "":
            return row[real_key]

    return None


def normalize(text):
    return str(text).replace("\\", "/").lower()


def row_text(path, row):
    parts = [str(path)]

    for k, v in row.items():
        if v is not None:
            parts.append(str(v))

    return normalize(" ".join(parts))


def match_config(config, text):
    for kw in config["Run File Keywords"]:
        if normalize(kw) in text:
            return True
    return False


def get_file_size_mb(path):
    try:
        p = Path(path)

        if not p.is_absolute():
            p = PROJECT_ROOT / p

        if p.exists() and p.is_file():
            return p.stat().st_size / (1024 * 1024)
    except Exception:
        return None

    return None


def get_dir_size_mb(path):
    try:
        p = Path(path)

        if not p.is_absolute():
            p = PROJECT_ROOT / p

        if p.exists() and p.is_dir():
            total = 0
            for root, _, files in os.walk(p):
                for file in files:
                    fp = Path(root) / file
                    total += fp.stat().st_size
            return total / (1024 * 1024)
    except Exception:
        return None

    return None


def extract_run_file(row):
    return find_value(row, RUN_FILE_KEYS)


def find_candidate_files(config):
    candidates = []

    for path in RESULTS_ROOT.rglob("*"):
        if not path.is_file():
            continue

        text = normalize(str(path.relative_to(PROJECT_ROOT)))

        if match_config(config, text):
            candidates.append(path)

    return candidates


def estimate_latency_from_run_file(run_file):
    if not run_file:
        return None

    try:
        p = Path(run_file)

        if not p.is_absolute():
            p = PROJECT_ROOT / p

        if not p.exists():
            return None

        start = time.perf_counter()

        with p.open("r", encoding="utf-8-sig", errors="ignore") as f:
            lines = [line for line in f if line.strip()]

        elapsed = time.perf_counter() - start

        if not lines:
            return None

        return elapsed * 1000.0 / len(lines)
    except Exception:
        return None


def collect_metrics_for_config(config):
    best = {
        "nDCG@10": None,
        "Index Size MB": None,
        "Latency": None,
        "Source File": "NOT_FOUND",
    }

    best_score = -1

    csv_files = list(RESULTS_ROOT.rglob("*.csv"))

    for csv_path in csv_files:
        if "day6_core_tables" in str(csv_path):
            continue

        rows = read_csv_rows(csv_path)

        for row in rows:
            text = row_text(csv_path, row)

            if not match_config(config, text):
                continue

            ndcg = safe_float(find_value(row, NDCG_KEYS))
            size_mb = safe_float(find_value(row, SIZE_KEYS))
            latency = safe_float(find_value(row, LATENCY_KEYS))

            run_file = extract_run_file(row)

            if size_mb is None and run_file:
                size_mb = get_file_size_mb(run_file)

            if latency is None and run_file:
                latency = estimate_latency_from_run_file(run_file)

            score = 0
            if ndcg is not None:
                score += 10
            if size_mb is not None:
                score += 3
            if latency is not None:
                score += 3

            source_text = normalize(csv_path.name)
            if "summary" in source_text or "results" in source_text or "metrics" in source_text:
                score += 2
            if "per_query" in source_text:
                score -= 3

            if score > best_score:
                best_score = score
                best = {
                    "nDCG@10": ndcg,
                    "Index Size MB": size_mb,
                    "Latency": latency,
                    "Source File": str(csv_path.relative_to(PROJECT_ROOT)),
                }

    if best["Index Size MB"] is None:
        candidate_files = find_candidate_files(config)
        sizes = [
            p.stat().st_size / (1024 * 1024)
            for p in candidate_files
            if p.exists() and p.is_file()
        ]

        if sizes:
            best["Index Size MB"] = sum(sizes)

    return best


def fmt4(v):
    if v is None:
        return "-"
    return "{:.4f}".format(v)


def fmt2(v):
    if v is None:
        return "-"
    return "{:.2f}".format(v)


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("[Week7-Day6] Generating Table 15: Budgeted Retrieval representative configs")
    print("Scanning:", RESULTS_ROOT)

    rows = []

    for config in CONFIGS:
        metrics = collect_metrics_for_config(config)

        out = {
            "Config": config["Config"],
            "N": config["N"],
            "M": config["M"],
            "Compression": config["Compression"],
            "nDCG@10": metrics["nDCG@10"],
            "Index Size MB": metrics["Index Size MB"],
            "Latency": metrics["Latency"],
            "Source File": metrics["Source File"],
        }

        rows.append(out)

        print(
            "DONE,{},{},{},{},nDCG@10={},IndexSizeMB={},Latency={},source={}".format(
                out["Config"],
                out["N"],
                out["M"],
                out["Compression"],
                fmt4(out["nDCG@10"]),
                fmt2(out["Index Size MB"]),
                fmt4(out["Latency"]),
                out["Source File"],
            )
        )

    with OUTPUT_CSV.open("w", encoding="utf-8", newline="") as f:
        fieldnames = [
            "Config",
            "N",
            "M",
            "Compression",
            "nDCG@10",
            "Index Size MB",
            "Latency",
            "Source File",
        ]

        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for row in rows:
            writer.writerow({
                "Config": row["Config"],
                "N": row["N"],
                "M": row["M"],
                "Compression": row["Compression"],
                "nDCG@10": fmt4(row["nDCG@10"]),
                "Index Size MB": fmt2(row["Index Size MB"]),
                "Latency": fmt4(row["Latency"]),
                "Source File": row["Source File"],
            })

    lines = []

    lines.append("# Week 7 Day 6 Table 15: Budgeted Retrieval 代表配置表")
    lines.append("")
    lines.append("## Table 15: Budgeted Retrieval 代表配置表")
    lines.append("")
    lines.append("| Config | N | M | Compression | nDCG@10 | Index Size MB | Latency |")
    lines.append("|---|---:|---:|---|---:|---:|---:|")

    for row in rows:
        lines.append(
            "| {} | {} | {} | {} | {} | {} | {} |".format(
                row["Config"],
                row["N"],
                row["M"],
                row["Compression"],
                fmt4(row["nDCG@10"]),
                fmt2(row["Index Size MB"]),
                fmt4(row["Latency"]),
            )
        )

    lines.append("")
    lines.append("## Source Files")
    lines.append("")
    lines.append("| Config | Source File |")
    lines.append("|---|---|")

    for row in rows:
        lines.append(
            "| {} | {} |".format(
                row["Config"],
                row["Source File"],
            )
        )

    OUTPUT_MD.write_text("\n".join(lines), encoding="utf-8")

    with OUTPUT_JSON.open("w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2, ensure_ascii=False)

    print("")
    print("Wrote:", OUTPUT_CSV)
    print("Wrote:", OUTPUT_MD)
    print("Wrote:", OUTPUT_JSON)

    print("")
    print("========== Table 15 ==========")
    print("Config,N,M,Compression,nDCG@10,Index Size MB,Latency,Source File")

    for row in rows:
        print(
            "{},{},{},{},{},{},{},{}".format(
                row["Config"],
                row["N"],
                row["M"],
                row["Compression"],
                fmt4(row["nDCG@10"]),
                fmt2(row["Index Size MB"]),
                fmt4(row["Latency"]),
                row["Source File"],
            )
        )


if __name__ == "__main__":
    main()
