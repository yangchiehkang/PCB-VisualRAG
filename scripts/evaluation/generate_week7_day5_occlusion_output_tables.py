from pathlib import Path
import csv
import json


PROJECT_ROOT = Path(r"E:\Working\PCB_VisualRAG_Project")

OCCLUSION_DIR = PROJECT_ROOT / "results" / "week7" / "occlusion"

INPUT_PER_QUERY = OCCLUSION_DIR / "occlusion_metrics_per_query.csv"

OUTPUT_TABLE12_CSV = OCCLUSION_DIR / "occlusion_table12_condition_results.csv"
OUTPUT_TABLE13_CSV = OCCLUSION_DIR / "occlusion_table13_gap_results.csv"
OUTPUT_MD = OCCLUSION_DIR / "occlusion_output_tables.md"
OUTPUT_JSON = OCCLUSION_DIR / "occlusion_output_tables.json"


def read_csv(path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def safe_float(v):
    try:
        if v is None or v == "":
            return 0.0
        return float(v)
    except Exception:
        return 0.0


def mean(values):
    values = list(values)
    return sum(values) / len(values) if values else 0.0


def hit_value(score):
    return 1.0 if score > 1e-12 else 0.0


def main():
    OCCLUSION_DIR.mkdir(parents=True, exist_ok=True)

    if not INPUT_PER_QUERY.exists():
        raise FileNotFoundError(INPUT_PER_QUERY)

    rows = read_csv(INPUT_PER_QUERY)

    valid_rows = [
        row for row in rows
        if row.get("status", "") in ["PASSED", "CHECK"]
    ]

    if not valid_rows:
        raise RuntimeError("No valid occlusion metric rows found.")

    original_scores = [safe_float(r["score_original"]) for r in valid_rows]
    gold_scores = [safe_float(r["score_gold_mask"]) for r in valid_rows]
    random_scores = [safe_float(r["score_random_mask"]) for r in valid_rows]

    original_ndcg = [safe_float(r["nDCG_original"]) for r in valid_rows]
    gold_ndcg = [safe_float(r["nDCG_gold_mask"]) for r in valid_rows]
    random_ndcg = [safe_float(r["nDCG_random_mask"]) for r in valid_rows]

    table12 = [
        {
            "Condition": "Original",
            "Recall@10": mean(hit_value(v) for v in original_scores),
            "MRR@10": mean(original_ndcg),
            "nDCG@10": mean(original_ndcg),
            "Avg Gold Page Score": mean(original_scores),
        },
        {
            "Condition": "Gold Mask",
            "Recall@10": mean(hit_value(v) for v in gold_scores),
            "MRR@10": mean(gold_ndcg),
            "nDCG@10": mean(gold_ndcg),
            "Avg Gold Page Score": mean(gold_scores),
        },
        {
            "Condition": "Random Mask",
            "Recall@10": mean(hit_value(v) for v in random_scores),
            "MRR@10": mean(random_ndcg),
            "nDCG@10": mean(random_ndcg),
            "Avg Gold Page Score": mean(random_scores),
        },
    ]

    condition_map = {row["Condition"]: row for row in table12}

    random_row = condition_map["Random Mask"]
    gold_row = condition_map["Gold Mask"]

    table13 = []

    for metric in ["Recall@10", "MRR@10", "nDCG@10", "Avg Gold Page Score"]:
        table13.append({
            "Metric": "Gold Page Score" if metric == "Avg Gold Page Score" else metric,
            "Random Mask": random_row[metric],
            "Gold Mask": gold_row[metric],
            "COG": random_row[metric] - gold_row[metric],
        })

    with OUTPUT_TABLE12_CSV.open("w", encoding="utf-8", newline="") as f:
        fieldnames = [
            "Condition",
            "Recall@10",
            "MRR@10",
            "nDCG@10",
            "Avg Gold Page Score",
        ]

        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for row in table12:
            writer.writerow({
                "Condition": row["Condition"],
                "Recall@10": "{:.4f}".format(row["Recall@10"]),
                "MRR@10": "{:.4f}".format(row["MRR@10"]),
                "nDCG@10": "{:.4f}".format(row["nDCG@10"]),
                "Avg Gold Page Score": "{:.8f}".format(row["Avg Gold Page Score"]),
            })

    with OUTPUT_TABLE13_CSV.open("w", encoding="utf-8", newline="") as f:
        fieldnames = [
            "Metric",
            "Random Mask",
            "Gold Mask",
            "COG",
        ]

        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for row in table13:
            writer.writerow({
                "Metric": row["Metric"],
                "Random Mask": "{:.8f}".format(row["Random Mask"]),
                "Gold Mask": "{:.8f}".format(row["Gold Mask"]),
                "COG": "{:.8f}".format(row["COG"]),
            })

    lines = []

    lines.append("# Week 7 Day 5 Occlusion Output Tables")
    lines.append("")
    lines.append("## Table 12: Occlusion 对照结果表")
    lines.append("")
    lines.append("| Condition | Recall@10 | MRR@10 | nDCG@10 | Avg Gold Page Score |")
    lines.append("|---|---:|---:|---:|---:|")

    for row in table12:
        lines.append(
            "| {} | {:.4f} | {:.4f} | {:.4f} | {:.8f} |".format(
                row["Condition"],
                row["Recall@10"],
                row["MRR@10"],
                row["nDCG@10"],
                row["Avg Gold Page Score"],
            )
        )

    lines.append("")
    lines.append("## Table 13: Counterfactual Occlusion Gap 表")
    lines.append("")
    lines.append("| Metric | Random Mask | Gold Mask | COG |")
    lines.append("|---|---:|---:|---:|")

    for row in table13:
        lines.append(
            "| {} | {:.8f} | {:.8f} | {:.8f} |".format(
                row["Metric"],
                row["Random Mask"],
                row["Gold Mask"],
                row["COG"],
            )
        )

    lines.append("")
    lines.append("## Source")
    lines.append("")
    lines.append("```text")
    lines.append(str(INPUT_PER_QUERY.relative_to(PROJECT_ROOT)))
    lines.append("```")

    OUTPUT_MD.write_text("\n".join(lines), encoding="utf-8")

    with OUTPUT_JSON.open("w", encoding="utf-8") as f:
        json.dump(
            {
                "table12": table12,
                "table13": table13,
                "valid_query_count": len(valid_rows),
                "source": str(INPUT_PER_QUERY.relative_to(PROJECT_ROOT)),
            },
            f,
            indent=2,
            ensure_ascii=False,
        )

    print("[Week7-Day5] Occlusion output tables generated.")
    print("Valid query count:", len(valid_rows))
    print("Wrote:", OUTPUT_TABLE12_CSV)
    print("Wrote:", OUTPUT_TABLE13_CSV)
    print("Wrote:", OUTPUT_MD)
    print("Wrote:", OUTPUT_JSON)

    print("")
    print("========== Table 12 ==========")
    print("Condition,Recall@10,MRR@10,nDCG@10,Avg Gold Page Score")
    for row in table12:
        print(
            "{},{:.4f},{:.4f},{:.4f},{:.8f}".format(
                row["Condition"],
                row["Recall@10"],
                row["MRR@10"],
                row["nDCG@10"],
                row["Avg Gold Page Score"],
            )
        )

    print("")
    print("========== Table 13 ==========")
    print("Metric,Random Mask,Gold Mask,COG")
    for row in table13:
        print(
            "{},{:.8f},{:.8f},{:.8f}".format(
                row["Metric"],
                row["Random Mask"],
                row["Gold Mask"],
                row["COG"],
            )
        )


if __name__ == "__main__":
    main()
