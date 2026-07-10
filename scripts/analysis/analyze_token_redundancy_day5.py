import argparse
from pathlib import Path

import pandas as pd


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--quality-cost-file",
        type=str,
        default="results/budgeted/token_selection/day4_cost_analysis/day4_quality_cost_table.csv",
    )

    parser.add_argument(
        "--output-dir",
        type=str,
        default="results/budgeted/token_selection/day5_redundancy_analysis",
    )

    parser.add_argument(
        "--full-m",
        type=int,
        default=49,
    )

    return parser.parse_args()


def pct(x):
    return x * 100.0


def main():
    args = parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    qc_path = Path(args.quality_cost_file)

    if not qc_path.exists():
        raise FileNotFoundError(f"Quality-cost file not found: {qc_path}")

    df = pd.read_csv(qc_path)

    required_cols = [
        "M",
        "Avg Tokens/Page",
        "Total Vectors",
        "Payload Size MB",
        "Recall@10",
        "MRR@10",
        "nDCG@10",
        "Per-query Latency ms",
    ]

    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns in quality-cost table: {missing}")

    df["M"] = pd.to_numeric(df["M"], errors="coerce").astype(int)
    df = df.sort_values("M").reset_index(drop=True)

    full_row = df[df["M"] == args.full_m]

    if full_row.empty:
        raise ValueError(f"Full-token setting M={args.full_m} not found.")

    full_row = full_row.iloc[0]

    full_tokens = float(full_row["Avg Tokens/Page"])
    full_vectors = float(full_row["Total Vectors"])
    full_payload = float(full_row["Payload Size MB"])
    full_latency = float(full_row["Per-query Latency ms"])
    full_recall10 = float(full_row["Recall@10"])
    full_mrr10 = float(full_row["MRR@10"])
    full_ndcg10 = float(full_row["nDCG@10"])

    rows = []

    for _, row in df.iterrows():
        m = int(row["M"])

        keep_ratio = float(row["Avg Tokens/Page"]) / full_tokens
        redundancy_ratio = 1.0 - keep_ratio

        vector_ratio = float(row["Total Vectors"]) / full_vectors
        vector_reduction = 1.0 - vector_ratio

        payload_ratio = float(row["Payload Size MB"]) / full_payload
        payload_reduction = 1.0 - payload_ratio

        latency_ratio = float(row["Per-query Latency ms"]) / full_latency
        latency_reduction = 1.0 - latency_ratio

        recall10 = float(row["Recall@10"])
        mrr10 = float(row["MRR@10"])
        ndcg10 = float(row["nDCG@10"])

        recall10_retention = recall10 / full_recall10 if full_recall10 > 0 else 0.0
        mrr10_retention = mrr10 / full_mrr10 if full_mrr10 > 0 else 0.0
        ndcg10_retention = ndcg10 / full_ndcg10 if full_ndcg10 > 0 else 0.0

        rows.append(
            {
                "M": m,
                "Keep Ratio": keep_ratio,
                "Redundancy Ratio": redundancy_ratio,
                "Avg Tokens/Page": row["Avg Tokens/Page"],
                "Total Vectors": row["Total Vectors"],
                "Vector Reduction vs Full": vector_reduction,
                "Payload Size MB": row["Payload Size MB"],
                "Payload Reduction vs Full": payload_reduction,
                "Latency ms/query": row["Per-query Latency ms"],
                "Latency Reduction vs Full": latency_reduction,
                "Recall@10": recall10,
                "Recall@10 Retention vs Full": recall10_retention,
                "MRR@10": mrr10,
                "MRR@10 Retention vs Full": mrr10_retention,
                "nDCG@10": ndcg10,
                "nDCG@10 Retention vs Full": ndcg10_retention,
            }
        )

    out_df = pd.DataFrame(rows)

    csv_path = output_dir / "day5_redundancy_ratio_analysis.csv"
    md_path = output_dir / "day5_redundancy_ratio_analysis.md"
    summary_path = output_dir / "day5_redundancy_summary.md"

    out_df.to_csv(csv_path, index=False)

    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# Day 5 Token Redundancy Ratio Analysis\n\n")
        f.write("| M | Keep Ratio | Redundancy Ratio | Payload Reduction | Recall@10 | Recall Retention | MRR@10 | MRR Retention | nDCG@10 | nDCG Retention | Latency ms/query |\n")
        f.write("|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|\n")

        for _, r in out_df.iterrows():
            f.write(
                f"| {int(r['M'])} "
                f"| {pct(r['Keep Ratio']):.2f}% "
                f"| {pct(r['Redundancy Ratio']):.2f}% "
                f"| {pct(r['Payload Reduction vs Full']):.2f}% "
                f"| {r['Recall@10']:.4f} "
                f"| {pct(r['Recall@10 Retention vs Full']):.2f}% "
                f"| {r['MRR@10']:.4f} "
                f"| {pct(r['MRR@10 Retention vs Full']):.2f}% "
                f"| {r['nDCG@10']:.4f} "
                f"| {pct(r['nDCG@10 Retention vs Full']):.2f}% "
                f"| {r['Latency ms/query']:.4f} |\n"
            )

    best_ndcg = out_df.sort_values("nDCG@10", ascending=False).iloc[0]
    best_mrr = out_df.sort_values("MRR@10", ascending=False).iloc[0]
    fastest = out_df.sort_values("Latency ms/query", ascending=True).iloc[0]

    m16 = out_df[out_df["M"] == 16]
    m8 = out_df[out_df["M"] == 8]

    with open(summary_path, "w", encoding="utf-8") as f:
        f.write("# Week 5 Day 5 Redundancy Summary\n\n")

        f.write("## 1. Full-token Reference\n\n")
        f.write(f"- Full-token setting: M{args.full_m}\n")
        f.write(f"- Full avg tokens/page: {full_tokens:.2f}\n")
        f.write(f"- Full payload size MB: {full_payload:.6f}\n")
        f.write(f"- Full Recall@10: {full_recall10:.6f}\n")
        f.write(f"- Full MRR@10: {full_mrr10:.6f}\n")
        f.write(f"- Full nDCG@10: {full_ndcg10:.6f}\n\n")

        f.write("## 2. Key Findings\n\n")
        f.write(
            f"- Best nDCG@10 setting: M{int(best_ndcg['M'])}, "
            f"nDCG@10={best_ndcg['nDCG@10']:.6f}, "
            f"redundancy ratio={pct(best_ndcg['Redundancy Ratio']):.2f}%\n"
        )
        f.write(
            f"- Best MRR@10 setting: M{int(best_mrr['M'])}, "
            f"MRR@10={best_mrr['MRR@10']:.6f}, "
            f"redundancy ratio={pct(best_mrr['Redundancy Ratio']):.2f}%\n"
        )
        f.write(
            f"- Fastest setting: M{int(fastest['M'])}, "
            f"latency={fastest['Latency ms/query']:.6f} ms/query\n\n"
        )

        f.write("## 3. Answer to Redundancy Questions\n\n")

        if not m16.empty:
            r = m16.iloc[0]
            f.write(
                f"- M16 keeps {pct(r['Keep Ratio']):.2f}% tokens and removes "
                f"{pct(r['Redundancy Ratio']):.2f}% tokens. "
                f"It preserves {pct(r['Recall@10 Retention vs Full']):.2f}% Recall@10 "
                f"and {pct(r['nDCG@10 Retention vs Full']):.2f}% nDCG@10 compared with M49.\n"
            )

        if not m8.empty:
            r = m8.iloc[0]
            f.write(
                f"- M8 keeps {pct(r['Keep Ratio']):.2f}% tokens and removes "
                f"{pct(r['Redundancy Ratio']):.2f}% tokens. "
                f"It preserves {pct(r['Recall@10 Retention vs Full']):.2f}% Recall@10 "
                f"and {pct(r['nDCG@10 Retention vs Full']):.2f}% nDCG@10 compared with M49.\n"
            )

        f.write(
            "- The exact 10% token setting was not tested because the current M list starts from M8. "
            "Since M8 corresponds to 16.33% retained tokens, it is the closest tested strong-compression setting.\n"
        )

    print("[Done] Day 5 redundancy analysis completed.")
    print(f"[Output] {csv_path}")
    print(f"[Output] {md_path}")
    print(f"[Output] {summary_path}")
    print(out_df)


if __name__ == "__main__":
    main()
