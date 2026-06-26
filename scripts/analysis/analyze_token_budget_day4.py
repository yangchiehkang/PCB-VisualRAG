import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--embedding-root",
        type=str,
        default="artifacts/embeddings/token_selection",
    )

    parser.add_argument(
        "--metrics-file",
        type=str,
        default="results/budgeted/token_selection/summary/token_budget_metrics.csv",
    )

    parser.add_argument(
        "--latency-file",
        type=str,
        default="results/budgeted/token_selection/summary/token_budget_day3_latency_by_M.csv",
    )

    parser.add_argument(
        "--output-dir",
        type=str,
        default="results/budgeted/token_selection/day4_cost_analysis",
    )

    parser.add_argument(
        "--figure-dir",
        type=str,
        default="results/budgeted/token_selection/figures",
    )

    parser.add_argument(
        "--m-list",
        type=int,
        nargs="+",
        default=[8, 16, 24, 32, 49],
    )

    parser.add_argument(
        "--full-m",
        type=int,
        default=49,
    )

    return parser.parse_args()


def bytes_to_mb(x):
    return x / (1024.0 * 1024.0)


def bytes_to_kb(x):
    return x / 1024.0


def collect_embedding_stats(embedding_root, m_list, full_m):
    embedding_root = Path(embedding_root)

    rows = []

    for m in m_list:
        page_dir = embedding_root / f"pages_M{m}"

        if not page_dir.exists():
            raise FileNotFoundError(f"Embedding directory not found: {page_dir}")

        files = sorted(page_dir.glob("*.npy"))

        if not files:
            raise FileNotFoundError(f"No .npy files found in {page_dir}")

        total_vectors = 0
        total_dims = []
        total_payload_bytes = 0
        total_file_bytes = 0
        page_token_counts = []

        for f in files:
            arr = np.load(f)

            if arr.ndim == 1:
                token_count = 1
                dim = arr.shape[0]
            elif arr.ndim == 2:
                token_count = arr.shape[0]
                dim = arr.shape[1]
            else:
                raise ValueError(f"Unexpected embedding shape in {f}: {arr.shape}")

            total_vectors += int(token_count)
            total_dims.append(int(dim))
            page_token_counts.append(int(token_count))

            total_payload_bytes += int(arr.nbytes)
            total_file_bytes += int(f.stat().st_size)

        unique_dims = sorted(set(total_dims))

        if len(unique_dims) != 1:
            dim_text = ",".join(str(x) for x in unique_dims)
        else:
            dim_text = str(unique_dims[0])

        num_pages = len(files)
        avg_tokens_per_page = total_vectors / num_pages if num_pages else 0.0
        min_tokens_per_page = min(page_token_counts) if page_token_counts else 0
        max_tokens_per_page = max(page_token_counts) if page_token_counts else 0

        rows.append(
            {
                "Setting": f"M{m}",
                "M": m,
                "Num Pages": num_pages,
                "Total Vectors": total_vectors,
                "Avg Tokens/Page": avg_tokens_per_page,
                "Min Tokens/Page": min_tokens_per_page,
                "Max Tokens/Page": max_tokens_per_page,
                "Embedding Dim": dim_text,
                "Payload Size Bytes": total_payload_bytes,
                "Payload Size KB": bytes_to_kb(total_payload_bytes),
                "Payload Size MB": bytes_to_mb(total_payload_bytes),
                "File Size Bytes": total_file_bytes,
                "File Size KB": bytes_to_kb(total_file_bytes),
                "File Size MB": bytes_to_mb(total_file_bytes),
            }
        )

    df = pd.DataFrame(rows)

    full_row = df[df["M"] == full_m]

    if full_row.empty:
        raise ValueError(f"Full setting M={full_m} not found in m_list={m_list}")

    full_payload = float(full_row.iloc[0]["Payload Size Bytes"])
    full_file = float(full_row.iloc[0]["File Size Bytes"])
    full_vectors = float(full_row.iloc[0]["Total Vectors"])
    full_avg_tokens = float(full_row.iloc[0]["Avg Tokens/Page"])

    df["Payload Ratio vs Full"] = df["Payload Size Bytes"] / full_payload
    df["Payload Reduction vs Full"] = 1.0 - df["Payload Ratio vs Full"]

    df["File Size Ratio vs Full"] = df["File Size Bytes"] / full_file
    df["File Size Reduction vs Full"] = 1.0 - df["File Size Ratio vs Full"]

    df["Vector Ratio vs Full"] = df["Total Vectors"] / full_vectors
    df["Vector Reduction vs Full"] = 1.0 - df["Vector Ratio vs Full"]

    df["Avg Token Ratio vs Full"] = df["Avg Tokens/Page"] / full_avg_tokens
    df["Avg Token Reduction vs Full"] = 1.0 - df["Avg Token Ratio vs Full"]

    df = df.sort_values("M").reset_index(drop=True)

    return df


def load_metrics(metrics_file):
    metrics_file = Path(metrics_file)

    if not metrics_file.exists():
        raise FileNotFoundError(f"Metrics file not found: {metrics_file}")

    df = pd.read_csv(metrics_file)

    # Keep only token-budget rows.
    token_df = df[df["Method"].astype(str).str.contains("C2F N10 M", regex=False)].copy()

    token_df["M"] = pd.to_numeric(token_df["M"], errors="coerce").astype("Int64")
    token_df = token_df.dropna(subset=["M"]).copy()
    token_df["M"] = token_df["M"].astype(int)

    return token_df


def load_latency(latency_file):
    latency_file = Path(latency_file)

    if not latency_file.exists():
        raise FileNotFoundError(f"Latency file not found: {latency_file}")

    df = pd.read_csv(latency_file)
    df["M"] = pd.to_numeric(df["M"], errors="coerce").astype("Int64")
    df = df.dropna(subset=["M"]).copy()
    df["M"] = df["M"].astype(int)

    return df


def build_quality_cost_table(index_df, metrics_df, latency_df):
    merged = index_df.merge(
        metrics_df[
            [
                "Method",
                "M",
                "Evaluated Queries",
                "Recall@1",
                "Recall@5",
                "Recall@10",
                "MRR@10",
                "nDCG@10",
                "Run File",
            ]
        ],
        on="M",
        how="left",
    )

    latency_cols = [
        "M",
        "Query Count",
        "Total Candidates",
        "Avg Candidates / Query",
        "Rerank Time Seconds",
        "Per-query Latency ms",
    ]

    existing_latency_cols = [c for c in latency_cols if c in latency_df.columns]

    merged = merged.merge(
        latency_df[existing_latency_cols],
        on="M",
        how="left",
    )

    return merged.sort_values("M").reset_index(drop=True)


def save_markdown_table(df, path, title):
    path = Path(path)

    display_df = df.copy()

    numeric_cols = display_df.select_dtypes(include=["float", "float64"]).columns
    for c in numeric_cols:
        display_df[c] = display_df[c].map(lambda x: f"{x:.6f}" if pd.notna(x) else "")

    with open(path, "w", encoding="utf-8") as f:
        f.write(f"# {title}\n\n")
        f.write("| " + " | ".join(display_df.columns) + " |\n")
        f.write("| " + " | ".join(["---"] * len(display_df.columns)) + " |\n")

        for _, row in display_df.iterrows():
            values = [str(row[c]) for c in display_df.columns]
            f.write("| " + " | ".join(values) + " |\n")


def plot_index_size_curves(index_df, figure_dir):
    figure_dir = Path(figure_dir)

    x = index_df["M"]
    payload_mb = index_df["Payload Size MB"]
    file_mb = index_df["File Size MB"]
    reduction = index_df["Payload Reduction vs Full"] * 100.0
    avg_tokens = index_df["Avg Tokens/Page"]

    plt.figure(figsize=(8, 5))
    plt.plot(x, payload_mb, marker="o", label="Payload Size MB")
    plt.plot(x, file_mb, marker="s", label="File Size MB")
    plt.xlabel("Token Budget M")
    plt.ylabel("Index Size MB")
    plt.title("Index Size under Different Token Budgets")
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.legend()
    plt.tight_layout()

    png_path = figure_dir / "day4_index_size_curve.png"
    pdf_path = figure_dir / "day4_index_size_curve.pdf"
    plt.savefig(png_path, dpi=300)
    plt.savefig(pdf_path)
    plt.close()

    plt.figure(figsize=(8, 5))
    plt.plot(x, reduction, marker="o", color="tab:green")
    plt.xlabel("Token Budget M")
    plt.ylabel("Payload Reduction vs Full (%)")
    plt.title("Index Size Reduction under Different Token Budgets")
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()

    png_path2 = figure_dir / "day4_index_reduction_curve.png"
    pdf_path2 = figure_dir / "day4_index_reduction_curve.pdf"
    plt.savefig(png_path2, dpi=300)
    plt.savefig(pdf_path2)
    plt.close()

    plt.figure(figsize=(8, 5))
    plt.plot(x, avg_tokens, marker="o", color="tab:purple")
    plt.xlabel("Token Budget M")
    plt.ylabel("Avg Tokens/Page")
    plt.title("Average Tokens per Page under Different Token Budgets")
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()

    png_path3 = figure_dir / "day4_avg_tokens_curve.png"
    pdf_path3 = figure_dir / "day4_avg_tokens_curve.pdf"
    plt.savefig(png_path3, dpi=300)
    plt.savefig(pdf_path3)
    plt.close()

    return [png_path, pdf_path, png_path2, pdf_path2, png_path3, pdf_path3]


def plot_quality_cost_curves(qc_df, figure_dir):
    figure_dir = Path(figure_dir)

    df = qc_df.sort_values("M").copy()

    plt.figure(figsize=(8, 5))
    plt.plot(df["Payload Size MB"], df["Recall@10"], marker="o", label="Recall@10")
    plt.plot(df["Payload Size MB"], df["nDCG@10"], marker="s", label="nDCG@10")
    plt.plot(df["Payload Size MB"], df["MRR@10"], marker="^", label="MRR@10")

    for _, row in df.iterrows():
        plt.annotate(f"M{int(row['M'])}", (row["Payload Size MB"], row["nDCG@10"]))

    plt.xlabel("Index Payload Size MB")
    plt.ylabel("Retrieval Quality")
    plt.title("Quality vs Index Size")
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.legend()
    plt.tight_layout()

    png_path = figure_dir / "day4_quality_vs_index_size.png"
    pdf_path = figure_dir / "day4_quality_vs_index_size.pdf"
    plt.savefig(png_path, dpi=300)
    plt.savefig(pdf_path)
    plt.close()

    if "Per-query Latency ms" in df.columns:
        plt.figure(figsize=(8, 5))
        plt.plot(df["Per-query Latency ms"], df["Recall@10"], marker="o", label="Recall@10")
        plt.plot(df["Per-query Latency ms"], df["nDCG@10"], marker="s", label="nDCG@10")
        plt.plot(df["Per-query Latency ms"], df["MRR@10"], marker="^", label="MRR@10")

        for _, row in df.iterrows():
            plt.annotate(f"M{int(row['M'])}", (row["Per-query Latency ms"], row["nDCG@10"]))

        plt.xlabel("Per-query Latency ms")
        plt.ylabel("Retrieval Quality")
        plt.title("Quality vs Reranking Latency")
        plt.grid(True, linestyle="--", alpha=0.5)
        plt.legend()
        plt.tight_layout()

        png_path2 = figure_dir / "day4_quality_vs_latency.png"
        pdf_path2 = figure_dir / "day4_quality_vs_latency.pdf"
        plt.savefig(png_path2, dpi=300)
        plt.savefig(pdf_path2)
        plt.close()

        return [png_path, pdf_path, png_path2, pdf_path2]

    return [png_path, pdf_path]


def make_day4_summary(qc_df, output_path, full_m=49):
    output_path = Path(output_path)

    df = qc_df.sort_values("M").copy()

    full_row = df[df["M"] == full_m].iloc[0]

    best_ndcg_row = df.sort_values("nDCG@10", ascending=False).iloc[0]
    best_mrr_row = df.sort_values("MRR@10", ascending=False).iloc[0]
    fastest_row = df.sort_values("Per-query Latency ms", ascending=True).iloc[0]
    smallest_row = df.sort_values("Payload Size MB", ascending=True).iloc[0]

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("# Week 5 Day 4 Token Budget Cost Analysis Summary\n\n")

        f.write("## 1. Full-token Reference\n\n")
        f.write(f"- Full-token setting: M{full_m}\n")
        f.write(f"- Full payload size MB: {full_row['Payload Size MB']:.6f}\n")
        f.write(f"- Full total vectors: {int(full_row['Total Vectors'])}\n")
        f.write(f"- Full avg tokens/page: {full_row['Avg Tokens/Page']:.2f}\n")
        f.write(f"- Full nDCG@10: {full_row['nDCG@10']:.6f}\n")
        f.write(f"- Full MRR@10: {full_row['MRR@10']:.6f}\n\n")

        f.write("## 2. Best Quality Settings\n\n")
        f.write(
            f"- Best nDCG@10: M{int(best_ndcg_row['M'])}, "
            f"nDCG@10={best_ndcg_row['nDCG@10']:.6f}, "
            f"payload reduction={best_ndcg_row['Payload Reduction vs Full'] * 100:.2f}%\n"
        )
        f.write(
            f"- Best MRR@10: M{int(best_mrr_row['M'])}, "
            f"MRR@10={best_mrr_row['MRR@10']:.6f}, "
            f"payload reduction={best_mrr_row['Payload Reduction vs Full'] * 100:.2f}%\n\n"
        )

        f.write("## 3. Best Cost Settings\n\n")
        f.write(
            f"- Smallest index: M{int(smallest_row['M'])}, "
            f"payload size={smallest_row['Payload Size MB']:.6f} MB, "
            f"payload reduction={smallest_row['Payload Reduction vs Full'] * 100:.2f}%\n"
        )
        f.write(
            f"- Fastest reranking: M{int(fastest_row['M'])}, "
            f"latency={fastest_row['Per-query Latency ms']:.6f} ms/query\n\n"
        )

        f.write("## 4. Compact Table\n\n")

        compact_cols = [
            "M",
            "Avg Tokens/Page",
            "Total Vectors",
            "Payload Size MB",
            "Payload Reduction vs Full",
            "Recall@10",
            "MRR@10",
            "nDCG@10",
            "Per-query Latency ms",
        ]

        compact = df[compact_cols].copy()
        compact["Payload Reduction vs Full"] = compact["Payload Reduction vs Full"] * 100.0

        f.write("| M | Avg Tokens/Page | Total Vectors | Payload Size MB | Payload Reduction % | Recall@10 | MRR@10 | nDCG@10 | Latency ms/query |\n")
        f.write("|---:|---:|---:|---:|---:|---:|---:|---:|---:|\n")

        for _, row in compact.iterrows():
            f.write(
                f"| {int(row['M'])} "
                f"| {row['Avg Tokens/Page']:.2f} "
                f"| {int(row['Total Vectors'])} "
                f"| {row['Payload Size MB']:.6f} "
                f"| {row['Payload Reduction vs Full']:.2f} "
                f"| {row['Recall@10']:.4f} "
                f"| {row['MRR@10']:.4f} "
                f"| {row['nDCG@10']:.4f} "
                f"| {row['Per-query Latency ms']:.4f} |\n"
            )


def main():
    args = parse_args()

    output_dir = Path(args.output_dir)
    figure_dir = Path(args.figure_dir)

    output_dir.mkdir(parents=True, exist_ok=True)
    figure_dir.mkdir(parents=True, exist_ok=True)

    index_df = collect_embedding_stats(
        embedding_root=args.embedding_root,
        m_list=args.m_list,
        full_m=args.full_m,
    )

    metrics_df = load_metrics(args.metrics_file)
    latency_df = load_latency(args.latency_file)

    qc_df = build_quality_cost_table(index_df, metrics_df, latency_df)

    index_csv = output_dir / "day4_index_size_stats.csv"
    latency_csv = output_dir / "day4_latency_stats.csv"
    qc_csv = output_dir / "day4_quality_cost_table.csv"
    xlsx_path = output_dir / "day4_token_budget_cost_analysis.xlsx"

    index_md = output_dir / "day4_index_size_stats.md"
    latency_md = output_dir / "day4_latency_stats.md"
    qc_md = output_dir / "day4_quality_cost_table.md"
    summary_md = output_dir / "day4_cost_analysis_summary.md"

    index_df.to_csv(index_csv, index=False)
    latency_df.to_csv(latency_csv, index=False)
    qc_df.to_csv(qc_csv, index=False)

    with pd.ExcelWriter(xlsx_path) as writer:
        index_df.to_excel(writer, sheet_name="Index Size", index=False)
        latency_df.to_excel(writer, sheet_name="Latency", index=False)
        qc_df.to_excel(writer, sheet_name="Quality Cost", index=False)

    save_markdown_table(index_df, index_md, "Day 4 Index Size Statistics")
    save_markdown_table(latency_df, latency_md, "Day 4 Latency Statistics")
    save_markdown_table(qc_df, qc_md, "Day 4 Quality-Cost Table")

    figs1 = plot_index_size_curves(index_df, figure_dir)
    figs2 = plot_quality_cost_curves(qc_df, figure_dir)

    make_day4_summary(qc_df, summary_md, full_m=args.full_m)

    print("[Done] Day 4 token budget cost analysis completed.")
    print(f"[Output] {index_csv}")
    print(f"[Output] {latency_csv}")
    print(f"[Output] {qc_csv}")
    print(f"[Output] {xlsx_path}")
    print(f"[Output] {index_md}")
    print(f"[Output] {latency_md}")
    print(f"[Output] {qc_md}")
    print(f"[Output] {summary_md}")

    for p in figs1 + figs2:
        print(f"[Figure] {p}")

    print("\n[Preview] Quality-Cost Table:")
    preview_cols = [
        "M",
        "Avg Tokens/Page",
        "Total Vectors",
        "Payload Size MB",
        "Payload Reduction vs Full",
        "Recall@10",
        "MRR@10",
        "nDCG@10",
        "Per-query Latency ms",
    ]
    print(qc_df[preview_cols])


if __name__ == "__main__":
    main()
