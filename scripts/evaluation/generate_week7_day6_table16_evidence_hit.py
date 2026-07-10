from pathlib import Path
import csv
import json


PROJECT_ROOT = Path(r"E:\Working\PCB_VisualRAG_Project")

RESULTS_ROOT = PROJECT_ROOT / "results" / "week7"
OUTPUT_DIR = RESULTS_ROOT / "day6_core_tables"

INPUT_CANDIDATES = [
    RESULTS_ROOT / "evidence_hit" / "evidence_hit_atk_results.csv",
    RESULTS_ROOT / "evidence_hit_atk_results.csv",
    RESULTS_ROOT / "evidence_hit" / "evidence_hit_results.csv",
]

OUTPUT_CSV = OUTPUT_DIR / "table16_evidence_hit_main_results.csv"
OUTPUT_MD = OUTPUT_DIR / "table16_evidence_hit_main_results.md"
OUTPUT_JSON = OUTPUT_DIR / "table16_evidence_hit_main_results.json"

METHOD_ORDER = [
    "BM25",
    "Full MV",
    "Budgeted MV",
    "BM25 + Budgeted MV",
    "Hybrid Fusion",
]

METHOD_ALIASES = {
    "BM25": ["BM25"],
    "Full MV": ["Full MV", "BM25 + Full MV", "BM25+Full MV", "FullMV"],
    "Budgeted MV": ["Budgeted MV", "BM25 + Budgeted MV N50", "BudgetedMV"],
    "BM25 + Budgeted MV": ["BM25 + Budgeted MV", "BM25+Budgeted MV"],
    "Hybrid Fusion": ["Hybrid Fusion", "Hybrid"],
}

METRIC_ALIASES = {
    "Evidence Hit@1": ["Evidence Hit@1", "Hit@1", "evidence_hit@1", "Evidence_Hit@1"],
    "Evidence Hit@5": ["Evidence Hit@5", "Hit@5", "evidence_hit@5", "Evidence_Hit@5"],
    "Evidence Hit@10": ["Evidence Hit@10", "Hit@10", "evidence_hit@10", "Evidence_Hit@10"],
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


def normalize_method(name):
    text = str(name).strip().lower()

    for canonical, aliases in METHOD_ALIASES.items():
        for alias in aliases:
            if text == alias.lower():
                return canonical

    for canonical, aliases in METHOD_ALIASES.items():
        for alias in aliases:
            if alias.lower() in text:
                return canonical

    return None


def find_input_file():
    for path in INPUT_CANDIDATES:
        if path.exists():
            return path

    for path in RESULTS_ROOT.rglob("*.csv"):
        name = path.name.lower()
        if "evidence" in name and "hit" in name and "result" in name:
            return path

    raise FileNotFoundError("No evidence hit results CSV found.")


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    input_csv = find_input_file()
    rows = read_csv(input_csv)

    result_map = {}

    for row in rows:
        raw_method = row.get("Method") or row.get("method") or row.get("Model") or row.get("model") or ""
        method = normalize_method(raw_method)

        if method is None:
            continue

        result_map[method] = {
            "Method": method,
            "Evidence Hit@1": safe_float(get_value(row, METRIC_ALIASES["Evidence Hit@1"])),
            "Evidence Hit@5": safe_float(get_value(row, METRIC_ALIASES["Evidence Hit@5"])),
            "Evidence Hit@10": safe_float(get_value(row, METRIC_ALIASES["Evidence Hit@10"])),
            "Source File": str(input_csv.relative_to(PROJECT_ROOT)),
        }

    output_rows = []

    for method in METHOD_ORDER:
        row = result_map.get(method, {
            "Method": method,
            "Evidence Hit@1": None,
            "Evidence Hit@5": None,
            "Evidence Hit@10": None,
            "Source File": "NOT_FOUND",
        })
        output_rows.append(row)

    with OUTPUT_CSV.open("w", encoding="utf-8", newline="") as f:
        fieldnames = [
            "Method",
            "Evidence Hit@1",
            "Evidence Hit@5",
            "Evidence Hit@10",
            "Source File",
        ]

        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for row in output_rows:
            writer.writerow({
                "Method": row["Method"],
                "Evidence Hit@1": fmt(row["Evidence Hit@1"]),
                "Evidence Hit@5": fmt(row["Evidence Hit@5"]),
                "Evidence Hit@10": fmt(row["Evidence Hit@10"]),
                "Source File": row["Source File"],
            })

    lines = []
    lines.append("# Week 7 Day 6 Table 16: Evidence Hit 主结果表")
    lines.append("")
    lines.append("## Table 16: Evidence Hit 主结果表")
    lines.append("")
    lines.append("| Method | Evidence Hit@1 | Evidence Hit@5 | Evidence Hit@10 |")
    lines.append("|---|---:|---:|---:|")

    for row in output_rows:
        lines.append(
            "| {} | {} | {} | {} |".format(
                row["Method"],
                fmt(row["Evidence Hit@1"]),
                fmt(row["Evidence Hit@5"]),
                fmt(row["Evidence Hit@10"]),
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
                "table16": output_rows,
            },
            f,
            indent=2,
            ensure_ascii=False,
        )

    print("[Week7-Day6] Table 16 generated.")
    print("Input:", input_csv)
    print("Wrote:", OUTPUT_CSV)
    print("Wrote:", OUTPUT_MD)
    print("Wrote:", OUTPUT_JSON)

    print("")
    print("========== Table 16 ==========")
    print("Method,Evidence Hit@1,Evidence Hit@5,Evidence Hit@10,Source File")

    for row in output_rows:
        print(
            "{},{},{},{},{}".format(
                row["Method"],
                fmt(row["Evidence Hit@1"]),
                fmt(row["Evidence Hit@5"]),
                fmt(row["Evidence Hit@10"]),
                row["Source File"],
            )
        )


if __name__ == "__main__":
    main()
