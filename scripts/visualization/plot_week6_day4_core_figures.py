from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


INPUT_FILE = Path("results/budgeted/joint_compression/summary/joint_budget_results.csv")
REP_FILE = Path("results/budgeted/joint_compression/day3_main/day3_representative_points.csv")

FIG_DIR = Path("results/budgeted/joint_compression/figures")
DAY4_DIR = Path("results/budgeted/joint_compression/day4_figures")

FIG_DIR.mkdir(parents=True, exist_ok=True)
DAY4_DIR.mkdir(parents=True, exist_ok=True)


QUALITY_COL = "nDCG@10"
INDEX_COL = "Index Size MB"
LATENCY_COL = "Latency ms/query"


COMPRESSION_ORDER = [
    "None",
    "PQ",
    "OPQ+PQ",
    "IVF+PQ",
    "IVF+OPQ+PQ",
]

COMPRESSION_MARKERS = {
    "None": "o",
    "PQ": "s",
    "OPQ+PQ": "D",
    "IVF+PQ": "^",
    "IVF+OPQ+PQ": "P",
}

COMPRESSION_COLORS = {
    "None": "#4C78A8",
    "PQ": "#F58518",
    "OPQ+PQ": "#54A24B",
    "IVF+PQ": "#E45756",
    "IVF+OPQ+PQ": "#B279A2",
}


def load_results() -> pd.DataFrame:
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Input file not found: {INPUT_FILE}")

    df = pd.read_csv(INPUT_FILE)

    required = [
        "N",
        "M",
        "Compression",
        "Recall@10",
        "MRR@10",
        "nDCG@10",
        "Index Size MB",
        "Latency ms/query",
        "run_name",
    ]

    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    for col in ["N", "M", "Recall@10", "MRR@10", "nDCG@10", "Index Size MB", "Latency ms/query"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df["Compression"] = df["Compression"].astype(str)
    df["label"] = df.apply(
        lambda r: f"M{int(r['M'])}-{r['Compression']}",
        axis=1,
    )

    return df


def load_representative_points(df: pd.DataFrame) -> dict:
    reps = {}

    if REP_FILE.exists():
        rep_df = pd.read_csv(REP_FILE)

        if "Category" in rep_df.columns and "run_name" in rep_df.columns:
            for _, row in rep_df.iterrows():
                category = str(row["Category"])
                run_name = str(row["run_name"])
                matched = df[df["run_name"] == run_name]
                if not matched.empty:
                    reps[category] = matched.iloc[0].to_dict()

    if "Closest to best quality" not in reps:
        reps["Closest to best quality"] = df.sort_values(
            [QUALITY_COL, "MRR@10", "Recall@10"],
            ascending=[False, False, False],
        ).iloc[0].to_dict()

    if "Lowest cost" not in reps:
        reps["Lowest cost"] = df.sort_values(
            [INDEX_COL, LATENCY_COL],
            ascending=[True, True],
        ).iloc[0].to_dict()

    if "Best trade-off" not in reps:
        temp = df.copy()
        qmax = temp[QUALITY_COL].max()
        cmax = temp[INDEX_COL].max()
        lmax = temp[LATENCY_COL].max()

        temp["quality_norm"] = temp[QUALITY_COL] / qmax if qmax > 0 else 0.0
        temp["cost_norm"] = 0.5 * (temp[INDEX_COL] / cmax) + 0.5 * (temp[LATENCY_COL] / lmax)
        temp["tradeoff_score"] = temp["quality_norm"] / (temp["cost_norm"] + 1e-9)

        reps["Best trade-off"] = temp.sort_values(
            ["tradeoff_score", QUALITY_COL],
            ascending=[False, False],
        ).iloc[0].to_dict()

    none_df = df[df["Compression"] == "None"].copy()
    if not none_df.empty:
        reps["Best uncompressed baseline"] = none_df.sort_values(
            [QUALITY_COL, "MRR@10"],
            ascending=[False, False],
        ).iloc[0].to_dict()

    return reps


def is_pareto_frontier(df: pd.DataFrame, cost_col: str, quality_col: str) -> pd.Series:
    flags = []

    for i, row in df.iterrows():
        cost = row[cost_col]
        quality = row[quality_col]

        dominated = (
            (df[cost_col] <= cost)
            & (df[quality_col] >= quality)
            & ((df[cost_col] < cost) | (df[quality_col] > quality))
        ).any()

        flags.append(not dominated)

    return pd.Series(flags, index=df.index)


def save_table(df: pd.DataFrame, csv_path: Path, md_path: Path):
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")

    try:
        text = df.to_markdown(index=False)
    except Exception:
        text = df.to_string(index=False)

    with md_path.open("w", encoding="utf-8") as f:
        f.write(text)
        f.write("\n")


def setup_style():
    sns.set_theme(style="whitegrid")
    plt.rcParams.update({
        "figure.dpi": 150,
        "savefig.dpi": 300,
        "font.size": 11,
        "axes.labelsize": 12,
        "axes.titlesize": 13,
        "legend.fontsize": 9,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
    })


def scatter_by_compression(ax, df: pd.DataFrame, x_col: str, y_col: str):
    for comp in COMPRESSION_ORDER:
        sub = df[df["Compression"] == comp].copy()

        if sub.empty:
            continue

        ax.scatter(
            sub[x_col],
            sub[y_col],
            s=85,
            marker=COMPRESSION_MARKERS.get(comp, "o"),
            color=COMPRESSION_COLORS.get(comp, None),
            edgecolor="black",
            linewidth=0.7,
            alpha=0.9,
            label=comp,
        )

        for _, row in sub.iterrows():
            ax.annotate(
                f"M{int(row['M'])}",
                (row[x_col], row[y_col]),
                xytext=(5, 4),
                textcoords="offset points",
                fontsize=8,
                alpha=0.9,
            )


def annotate_reps(ax, reps: dict, x_col: str, y_col: str):
    annotation_map = {
        "Closest to best quality": "Best quality",
        "Lowest cost": "Lowest cost",
        "Best trade-off": "Best trade-off",
        "Best uncompressed baseline": "Best None",
    }

    offsets = {
        "Closest to best quality": (12, 16),
        "Lowest cost": (12, -18),
        "Best trade-off": (12, 28),
        "Best uncompressed baseline": (12, -30),
    }

    for key, label in annotation_map.items():
        if key not in reps:
            continue

        row = reps[key]
        x = row[x_col]
        y = row[y_col]

        ax.scatter(
            [x],
            [y],
            s=190,
            facecolors="none",
            edgecolors="black",
            linewidth=1.8,
            zorder=5,
        )

        dx, dy = offsets.get(key, (12, 12))

        ax.annotate(
            label,
            (x, y),
            xytext=(dx, dy),
            textcoords="offset points",
            fontsize=9,
            fontweight="bold",
            arrowprops=dict(
                arrowstyle="->",
                lw=0.9,
                color="black",
            ),
        )


def plot_quality_vs_index(df: pd.DataFrame, reps: dict):
    fig, ax = plt.subplots(figsize=(7.2, 5.2))

    scatter_by_compression(ax, df, INDEX_COL, QUALITY_COL)
    annotate_reps(ax, reps, INDEX_COL, QUALITY_COL)

    ax.set_xscale("log")
    ax.set_xlabel("Index Size (MB, log scale)")
    ax.set_ylabel("nDCG@10")
    ax.set_title("Quality vs. Index Size")
    ax.legend(title="Compression", loc="best", frameon=True)
    ax.grid(True, which="both", linestyle="--", linewidth=0.5, alpha=0.45)

    fig.tight_layout()

    fig.savefig(FIG_DIR / "quality_vs_index_size.pdf", bbox_inches="tight")
    fig.savefig(FIG_DIR / "quality_vs_index_size.png", bbox_inches="tight")
    fig.savefig(DAY4_DIR / "quality_vs_index_size.pdf", bbox_inches="tight")
    fig.savefig(DAY4_DIR / "quality_vs_index_size.png", bbox_inches="tight")

    plt.close(fig)


def plot_quality_vs_latency(df: pd.DataFrame, reps: dict):
    fig, ax = plt.subplots(figsize=(7.2, 5.2))

    scatter_by_compression(ax, df, LATENCY_COL, QUALITY_COL)
    annotate_reps(ax, reps, LATENCY_COL, QUALITY_COL)

    ax.set_xlabel("Latency (ms/query)")
    ax.set_ylabel("nDCG@10")
    ax.set_title("Quality vs. Retrieval Latency")
    ax.legend(title="Compression", loc="best", frameon=True)
    ax.grid(True, linestyle="--", linewidth=0.5, alpha=0.45)

    fig.tight_layout()

    fig.savefig(FIG_DIR / "quality_vs_latency.pdf", bbox_inches="tight")
    fig.savefig(FIG_DIR / "quality_vs_latency.png", bbox_inches="tight")
    fig.savefig(DAY4_DIR / "quality_vs_latency.pdf", bbox_inches="tight")
    fig.savefig(DAY4_DIR / "quality_vs_latency.png", bbox_inches="tight")

    plt.close(fig)


def plot_pareto_frontier(df: pd.DataFrame, reps: dict, pareto_index: pd.DataFrame, pareto_latency: pd.DataFrame):
    fig, axes = plt.subplots(1, 2, figsize=(13.5, 5.2))

    ax = axes[0]
    scatter_by_compression(ax, df, INDEX_COL, QUALITY_COL)

    pf = pareto_index.sort_values(INDEX_COL)
    ax.plot(
        pf[INDEX_COL],
        pf[QUALITY_COL],
        color="black",
        linewidth=1.6,
        linestyle="-",
        marker="o",
        markersize=4,
        label="Pareto frontier",
        zorder=4,
    )

    annotate_reps(ax, reps, INDEX_COL, QUALITY_COL)

    ax.set_xscale("log")
    ax.set_xlabel("Index Size (MB, log scale)")
    ax.set_ylabel("nDCG@10")
    ax.set_title("Pareto Frontier: Quality vs. Index Size")
    ax.grid(True, which="both", linestyle="--", linewidth=0.5, alpha=0.45)

    ax = axes[1]
    scatter_by_compression(ax, df, LATENCY_COL, QUALITY_COL)

    pf = pareto_latency.sort_values(LATENCY_COL)
    ax.plot(
        pf[LATENCY_COL],
        pf[QUALITY_COL],
        color="black",
        linewidth=1.6,
        linestyle="-",
        marker="o",
        markersize=4,
        label="Pareto frontier",
        zorder=4,
    )

    annotate_reps(ax, reps, LATENCY_COL, QUALITY_COL)

    ax.set_xlabel("Latency (ms/query)")
    ax.set_ylabel("nDCG@10")
    ax.set_title("Pareto Frontier: Quality vs. Latency")
    ax.grid(True, linestyle="--", linewidth=0.5, alpha=0.45)

    handles, labels = axes[0].get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    fig.legend(
        by_label.values(),
        by_label.keys(),
        loc="lower center",
        ncol=6,
        frameon=True,
        bbox_to_anchor=(0.5, -0.02),
    )

    fig.tight_layout(rect=[0, 0.08, 1, 1])

    fig.savefig(FIG_DIR / "pareto_frontier.pdf", bbox_inches="tight")
    fig.savefig(FIG_DIR / "pareto_frontier.png", bbox_inches="tight")
    fig.savefig(DAY4_DIR / "pareto_frontier.pdf", bbox_inches="tight")
    fig.savefig(DAY4_DIR / "pareto_frontier.png", bbox_inches="tight")

    plt.close(fig)


def write_figure_captions(pareto_index: pd.DataFrame, pareto_latency: pd.DataFrame, reps: dict):
    path = DAY4_DIR / "day4_figure_captions.md"

    best_quality = reps.get("Closest to best quality", {})
    lowest_cost = reps.get("Lowest cost", {})
    best_tradeoff = reps.get("Best trade-off", {})
    best_none = reps.get("Best uncompressed baseline", {})

    with path.open("w", encoding="utf-8") as f:
        f.write("# Week 6 Day 4 Figure Captions\n\n")

        f.write("## Figure 1: Quality vs. Index Size\n\n")
        f.write(
            "This figure shows the relationship between retrieval quality, measured by nDCG@10, "
            "and estimated index size. Each point represents one joint budget configuration. "
            "Compressed configurations substantially reduce storage cost while preserving competitive retrieval quality.\n\n"
        )

        f.write("## Figure 2: Quality vs. Retrieval Latency\n\n")
        f.write(
            "This figure compares retrieval quality against per-query reranking latency. "
            "The plot highlights which compressed budget settings provide favorable speed-quality trade-offs under the current reconstructed-embedding reranking pipeline.\n\n"
        )

        f.write("## Figure 3: Pareto Frontier\n\n")
        f.write(
            "This figure marks configurations that are not dominated by another configuration with both lower cost and higher retrieval quality. "
            "Separate frontiers are shown for index size and latency.\n\n"
        )

        f.write("## Key Configurations\n\n")
        rows = []

        for name, row in [
            ("Closest to best quality", best_quality),
            ("Lowest cost", lowest_cost),
            ("Best trade-off", best_tradeoff),
            ("Best uncompressed baseline", best_none),
        ]:
            if row:
                rows.append({
                    "Category": name,
                    "run_name": row.get("run_name"),
                    "N": row.get("N"),
                    "M": row.get("M"),
                    "Compression": row.get("Compression"),
                    "Recall@10": row.get("Recall@10"),
                    "MRR@10": row.get("MRR@10"),
                    "nDCG@10": row.get("nDCG@10"),
                    "Index Size MB": row.get("Index Size MB"),
                    "Latency ms/query": row.get("Latency ms/query"),
                })

        key_df = pd.DataFrame(rows)

        try:
            f.write(key_df.to_markdown(index=False))
        except Exception:
            f.write(key_df.to_string(index=False))

        f.write("\n\n")

        f.write("## Pareto Frontier: Index Size\n\n")
        try:
            f.write(pareto_index[[
                "run_name", "N", "M", "Compression", "Recall@10", "MRR@10", "nDCG@10", "Index Size MB", "Latency ms/query"
            ]].to_markdown(index=False))
        except Exception:
            f.write(pareto_index.to_string(index=False))

        f.write("\n\n")

        f.write("## Pareto Frontier: Latency\n\n")
        try:
            f.write(pareto_latency[[
                "run_name", "N", "M", "Compression", "Recall@10", "MRR@10", "nDCG@10", "Index Size MB", "Latency ms/query"
            ]].to_markdown(index=False))
        except Exception:
            f.write(pareto_latency.to_string(index=False))

        f.write("\n")


def main():
    setup_style()

    df = load_results()
    reps = load_representative_points(df)

    df["pareto_index_size"] = is_pareto_frontier(df, INDEX_COL, QUALITY_COL)
    df["pareto_latency"] = is_pareto_frontier(df, LATENCY_COL, QUALITY_COL)

    pareto_index = df[df["pareto_index_size"]].copy().sort_values([INDEX_COL, QUALITY_COL], ascending=[True, False])
    pareto_latency = df[df["pareto_latency"]].copy().sort_values([LATENCY_COL, QUALITY_COL], ascending=[True, False])

    save_table(
        pareto_index,
        DAY4_DIR / "day4_pareto_index_size.csv",
        DAY4_DIR / "day4_pareto_index_size.md",
    )

    save_table(
        pareto_latency,
        DAY4_DIR / "day4_pareto_latency.csv",
        DAY4_DIR / "day4_pareto_latency.md",
    )

    save_table(
        df,
        DAY4_DIR / "day4_results_with_pareto_flags.csv",
        DAY4_DIR / "day4_results_with_pareto_flags.md",
    )

    plot_quality_vs_index(df, reps)
    plot_quality_vs_latency(df, reps)
    plot_pareto_frontier(df, reps, pareto_index, pareto_latency)

    write_figure_captions(pareto_index, pareto_latency, reps)

    print("[Done] Day 4 figures generated.")
    print(f"[Output] {FIG_DIR / 'quality_vs_index_size.pdf'}")
    print(f"[Output] {FIG_DIR / 'quality_vs_latency.pdf'}")
    print(f"[Output] {FIG_DIR / 'pareto_frontier.pdf'}")
    print(f"[Output] {DAY4_DIR / 'day4_pareto_index_size.csv'}")
    print(f"[Output] {DAY4_DIR / 'day4_pareto_latency.csv'}")
    print(f"[Output] {DAY4_DIR / 'day4_figure_captions.md'}")


if __name__ == "__main__":
    main()
