from pathlib import Path
import pandas as pd


IN_FILE = Path("results/budgeted/joint_compression/day3_main/day3_joint_budget_results_detailed.csv")
OUT_DIR = Path("results/budgeted/joint_compression/day3_main")
SUMMARY_DIR = Path("results/budgeted/joint_compression/summary")

OUT_DIR.mkdir(parents=True, exist_ok=True)
SUMMARY_DIR.mkdir(parents=True, exist_ok=True)


def safe_to_markdown(df: pd.DataFrame) -> str:
    try:
        return df.to_markdown(index=False)
    except Exception:
        return df.to_string(index=False)


def main():
    if not IN_FILE.exists():
        raise FileNotFoundError(f"Input file not found: {IN_FILE}")

    df = pd.read_csv(IN_FILE)

    for col in ["Recall@10", "MRR@10", "nDCG@10", "Index Size MB", "Latency ms/query"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    max_ndcg = df["nDCG@10"].max()
    max_mrr = df["MRR@10"].max()
    max_recall = df["Recall@10"].max()

    best_quality = df.sort_values(
        ["nDCG@10", "MRR@10", "Recall@10"],
        ascending=[False, False, False],
    ).head(5)

    lowest_cost = df.sort_values(
        ["Index Size MB", "Latency ms/query"],
        ascending=[True, True],
    ).head(5)

    df["quality_norm"] = (
        0.5 * (df["nDCG@10"] / max_ndcg if max_ndcg > 0 else 0)
        + 0.3 * (df["MRR@10"] / max_mrr if max_mrr > 0 else 0)
        + 0.2 * (df["Recall@10"] / max_recall if max_recall > 0 else 0)
    )

    df["cost_norm"] = (
        0.5 * (df["Index Size MB"] / df["Index Size MB"].max())
        + 0.5 * (df["Latency ms/query"] / df["Latency ms/query"].max())
    )

    df["tradeoff_score"] = df["quality_norm"] / (df["cost_norm"] + 1e-9)

    best_tradeoff = df.sort_values(
        ["tradeoff_score", "nDCG@10"],
        ascending=[False, False],
    ).head(5)

    representative_rows = []

    representative_rows.append({
        "Category": "Closest to best quality",
        "run_name": best_quality.iloc[0]["run_name"],
        "N": best_quality.iloc[0]["N"],
        "M": best_quality.iloc[0]["M"],
        "Compression": best_quality.iloc[0]["Compression"],
        "Recall@10": best_quality.iloc[0]["Recall@10"],
        "MRR@10": best_quality.iloc[0]["MRR@10"],
        "nDCG@10": best_quality.iloc[0]["nDCG@10"],
        "Index Size MB": best_quality.iloc[0]["Index Size MB"],
        "Latency ms/query": best_quality.iloc[0]["Latency ms/query"],
    })

    representative_rows.append({
        "Category": "Lowest cost",
        "run_name": lowest_cost.iloc[0]["run_name"],
        "N": lowest_cost.iloc[0]["N"],
        "M": lowest_cost.iloc[0]["M"],
        "Compression": lowest_cost.iloc[0]["Compression"],
        "Recall@10": lowest_cost.iloc[0]["Recall@10"],
        "MRR@10": lowest_cost.iloc[0]["MRR@10"],
        "nDCG@10": lowest_cost.iloc[0]["nDCG@10"],
        "Index Size MB": lowest_cost.iloc[0]["Index Size MB"],
        "Latency ms/query": lowest_cost.iloc[0]["Latency ms/query"],
    })

    representative_rows.append({
        "Category": "Best trade-off",
        "run_name": best_tradeoff.iloc[0]["run_name"],
        "N": best_tradeoff.iloc[0]["N"],
        "M": best_tradeoff.iloc[0]["M"],
        "Compression": best_tradeoff.iloc[0]["Compression"],
        "Recall@10": best_tradeoff.iloc[0]["Recall@10"],
        "MRR@10": best_tradeoff.iloc[0]["MRR@10"],
        "nDCG@10": best_tradeoff.iloc[0]["nDCG@10"],
        "Index Size MB": best_tradeoff.iloc[0]["Index Size MB"],
        "Latency ms/query": best_tradeoff.iloc[0]["Latency ms/query"],
    })

    reps = pd.DataFrame(representative_rows)

    reps_csv = OUT_DIR / "day3_representative_points.csv"
    reps_md = OUT_DIR / "day3_representative_points.md"
    summary_md = SUMMARY_DIR / "day3_main_result_summary.md"

    reps.to_csv(reps_csv, index=False, encoding="utf-8-sig")

    with reps_md.open("w", encoding="utf-8") as f:
        f.write("# Week 6 Day 3 Representative Points\n\n")
        f.write(safe_to_markdown(reps))
        f.write("\n")

    with summary_md.open("w", encoding="utf-8") as f:
        f.write("# Week 6 Day 3 Main Result Summary\n\n")

        f.write("## 1. Representative Points\n\n")
        f.write(safe_to_markdown(reps))
        f.write("\n\n")

        f.write("## 2. Top-5 Quality Configurations\n\n")
        f.write(safe_to_markdown(best_quality[[
            "run_name", "N", "M", "Compression", "Recall@10", "MRR@10", "nDCG@10", "Index Size MB", "Latency ms/query"
        ]]))
        f.write("\n\n")

        f.write("## 3. Top-5 Lowest Cost Configurations\n\n")
        f.write(safe_to_markdown(lowest_cost[[
            "run_name", "N", "M", "Compression", "Recall@10", "MRR@10", "nDCG@10", "Index Size MB", "Latency ms/query"
        ]]))
        f.write("\n\n")

        f.write("## 4. Top-5 Trade-off Configurations\n\n")
        f.write(safe_to_markdown(best_tradeoff[[
            "run_name", "N", "M", "Compression", "Recall@10", "MRR@10", "nDCG@10", "Index Size MB", "Latency ms/query", "tradeoff_score"
        ]]))
        f.write("\n")

    print("[Done] Day 3 representative points generated.")
    print(f"[Output] {reps_csv}")
    print(f"[Output] {reps_md}")
    print(f"[Output] {summary_md}")


if __name__ == "__main__":
    main()
