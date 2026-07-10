from pathlib import Path
import csv
import json


PROJECT_ROOT = Path(r"E:\Working\PCB_VisualRAG_Project")

RESULTS_ROOT = PROJECT_ROOT / "results" / "week7"
OUTPUT_DIR = RESULTS_ROOT / "day6_core_tables"

INPUT_CANDIDATES = [
    RESULTS_ROOT / "occlusion" / "occlusion_table12_condition_results.csv",
    RESULTS_ROOT / "occlusion" / "occlusion_output_tables.csv",
    RESULTS_ROOT / "occlusion" / "occlusion_metrics_summary.csv",
]

OUTPUT_CSV = OUTPUT_DIR / "table17_occlusion_main_results.csv"
OUTPUT_MD = OUTPUT_DIR / "table17_occlusion_main_results.md"
OUTPUT_JSON = OUTPUT_DIR / "table17_occlusion_main_results.json"

CONDITION_ORDER = [
    "Original",
    "Gold Mask",
    "Random Mask",
]

METRIC_ALIASES = {
    "MRR@10": [
        "MRR@10",
        "mrr@10",
        "MRR_10",
        "mrr_10",
        "MRR",
    ],
    "nDCG@10": [
        "nDCG@10",
        "NDCG@10",
        "ndcg@10",
        "nDCG_10",
        "NDCG_10",
        "ndcg_10",
        "nDCG",
    ],
    "Avg Gold Page Score": [
        "Avg Gold Page Score",
        "avg_gold_page_score",
        "Gold Page Score",
        "gold_page_score",
        "Mean Score Original",
        "Mean Score Gold Mask",
        "Mean Score Random Mask",
    ],
}


def read_csv(path):
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            return list(csv.DictReader(f))
    except UnicodeDecodeError:
        with path.open("r", encoding="gbk", newline="") as f:
            return list(csv.DictReader(f))


def safe_float(v):
    try:
        if v is None or str(v).strip() in ["", "-"]:
            return None
        return float(str(v).strip())
    except Exception:
        return None


def fmt(v):
    if v is None:
        return "-"
    return "{:.4f}".format(v)


def fmt_score(v):
    if v is None:
        return "-"
    return "{:.8f}".format(v)


def get_value(row, aliases):
    lower_map = {str(k).lower(): k for k in row.keys()}

    for alias in aliases:
        if alias in row and str(row[alias]).strip() != "":
            return row[alias]

    for alias in aliases:
        real_key = lower_map.get(alias.lower())
        if real_key is not None and str(row[real_key]).strip() != "":
            return row[real_key]

    return None


def normalize_condition(text):
    t = str(text).strip().lower()

    if t == "original":
        return "Original"

    if t in ["gold mask", "gold_mask", "goldmask"]:
        return "Gold Mask"

    if t in ["random mask", "random_mask", "randommask"]:
        return "Random Mask"

    return None


def find_input_file():
    for path in INPUT_CANDIDATES:
        if path.exists():
            return path

    for path in RESULTS_ROOT.rglob("*.csv"):
        name = path.name.lower()
        if "occlusion" in name and "table12" in name:
            return path

    for path in RESULTS_ROOT.rglob("*.csv"):
        name = path.name.lower()
        if "occlusion" in name and "condition" in name:
            return path

    raise FileNotFoundError("No occlusion condition results CSV found.")


def parse_condition_table(input_csv):
    rows = read_csv(input_csv)

    result_map = {}

    for row in rows:
        raw_condition = (
            row.get("Condition")
            or row.get("condition")
            or row.get("Config")
            or row.get("config")
            or ""
        )

        condition = normalize_condition(raw_condition)

        if condition is None:
            continue

        result_map[condition] = {
            "Condition": condition,
            "MRR@10": safe_float(get_value(row, METRIC_ALIASES["MRR@10"])),
            "nDCG@10": safe_float(get_value(row, METRIC_ALIASES["nDCG@10"])),
            "Avg Gold Page Score": safe_float(get_value(row, METRIC_ALIASES["Avg Gold Page Score"])),
            "Source File": str(input_csv.relative_to(PROJECT_ROOT)),
        }

    return result_map


def parse_summary_table(input_csv):
    rows = read_csv(input_csv)

    if not rows:
        return {}

    row = rows[0]

    result_map = {
        "Original": {
            "Condition": "Original",
            "MRR@10": safe_float(row.get("Mean nDCG Original")),
            "nDCG@10": safe_float(row.get("Mean nDCG Original")),
            "Avg Gold Page Score": safe_float(row.get("Mean Score Original")),
            "Source File": str(input_csv.relative_to(PROJECT_ROOT)),
        },
        "Gold Mask": {
            "Condition": "Gold Mask",
            "MRR@10": safe_float(row.get("Mean nDCG Gold Mask")),
            "nDCG@10": safe_float(row.get("Mean nDCG Gold Mask")),
            "Avg Gold Page Score": safe_float(row.get("Mean Score Gold Mask")),
            "Source File": str(input_csv.relative_to(PROJECT_ROOT)),
        },
        "Random Mask": {
            "Condition": "Random Mask",
            "MRR@10": safe_float(row.get("Mean nDCG Random Mask")),
            "nDCG@10": safe_float(row.get("Mean nDCG Random Mask")),
            "Avg Gold Page Score": safe_float(row.get("Mean Score Random Mask")),
            "Source File": str(input_csv.relative_to(PROJECT_ROOT)),
        },
    }

    return result_map


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    input_csv = find_input_file()

    if input_csv.name == "occlusion_metrics_summary.csv":
        result_map = parse_summary_table(input_csv)
    else:
        result_map = parse_condition_table(input_csv)

        if not result_map:
            fallback = RESULTS_ROOT / "occlusion" / "occlusion_metrics_summary.csv"
            if fallback.exists():
                input_csv = fallback
                result_map = parse_summary_table(input_csv)

    output_rows = []

    for condition in CONDITION_ORDER:
        row = result_map.get(condition, {
            "Condition": condition,
            "MRR@10": None,
            "nDCG@10": None,
            "Avg Gold Page Score": None,
            "Source File": "NOT_FOUND",
        })

        output_rows.append(row)

    with OUTPUT_CSV.open("w", encoding="utf-8", newline="") as f:
        fieldnames = [
            "Condition",
            "MRR@10",
            "nDCG@10",
            "Avg Gold Page Score",
            "Source File",
        ]

        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for row in output_rows:
            writer.writerow({
                "Condition": row["Condition"],
                "MRR@10": fmt(row["MRR@10"]),
                "nDCG@10": fmt(row["nDCG@10"]),
                "Avg Gold Page Score": fmt_score(row["Avg Gold Page Score"]),
                "Source File": row["Source File"],
            })

    lines = []
    lines.append("# Week 7 Day 6 Table 17: Occlusion 主结果表")
    lines.append("")
    lines.append("## Table 17: Occlusion 主结果表")
    lines.append("")
    lines.append("| Condition | MRR@10 | nDCG@10 | Avg Gold Page Score |")
    lines.append("|---|---:|---:|---:|")

    for row in output_rows:
        lines.append(
            "| {} | {} | {} | {} |".format(
                row["Condition"],
                fmt(row["MRR@10"]),
                fmt(row["nDCG@10"]),
                fmt_score(row["Avg Gold Page Score"]),
            )
        )

    lines.append("")
    lines.append("## Source")
    lines.append("")
    lines.append("```text")
    lines.append(str(input_csv.relative_to(PROJECT_ROOT)))
    lines.append("```")

    OUTPUT_MD.write_text("\n".join(lines), encoding="utf-8")

    with OUTPUT_JSON.open("w", encoding="utf-8") as f:
        json.dump(
            {
                "source": str(input_csv.relative_to(PROJECT_ROOT)),
                "table17": output_rows,
            },
            f,
            indent=2,
            ensure_ascii=False,
        )

    print("[Week7-Day6] Table 17 generated.")
    print("Input:", input_csv)
    print("Wrote:", OUTPUT_CSV)
    print("Wrote:", OUTPUT_MD)
    print("Wrote:", OUTPUT_JSON)

    print("")
    print("========== Table 17 ==========")
    print("Condition,MRR@10,nDCG@10,Avg Gold Page Score,Source File")

    for row in output_rows:
        print(
            "{},{},{},{},{}".format(
                row["Condition"],
                fmt(row["MRR@10"]),
                fmt(row["nDCG@10"]),
                fmt_score(row["Avg Gold Page Score"]),
                row["Source File"],
            )
        )


if __name__ == "__main__":
    main()
