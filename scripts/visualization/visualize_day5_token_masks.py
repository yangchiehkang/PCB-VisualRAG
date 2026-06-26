import argparse
import ast
import math
import re
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--metadata-file",
        type=str,
        default="results/budgeted/token_selection/day2_validation/day2_token_selection_metadata_all.csv",
    )

    parser.add_argument(
        "--output-dir",
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
        "--max-pages",
        type=int,
        default=8,
    )

    parser.add_argument(
        "--grid-size",
        type=int,
        default=7,
    )

    return parser.parse_args()


def find_col(df, candidates):
    cols_lower = {c.lower(): c for c in df.columns}

    for cand in candidates:
        if cand.lower() in cols_lower:
            return cols_lower[cand.lower()]

    for c in df.columns:
        c_lower = c.lower()
        for cand in candidates:
            if cand.lower() in c_lower:
                return c

    return None


def parse_indices(x):
    if pd.isna(x):
        return []

    s = str(x).strip()

    if not s:
        return []

    try:
        value = ast.literal_eval(s)
        if isinstance(value, (list, tuple)):
            return [int(v) for v in value]
    except Exception:
        pass

    nums = re.findall(r"\d+", s)
    return [int(n) for n in nums]


def main():
    args = parse_args()

    metadata_path = Path(args.metadata_file)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not metadata_path.exists():
        raise FileNotFoundError(f"Metadata file not found: {metadata_path}")

    df = pd.read_csv(metadata_path)

    page_col = find_col(df, ["page_id", "doc_id", "id", "file_stem"])
    m_col = find_col(df, ["M", "m", "token_budget"])
    idx_col = find_col(df, ["kept_indices", "kept_token_indices", "selected_indices", "token_indices"])

    if page_col is None:
        raise ValueError(f"Cannot find page id column. Columns: {list(df.columns)}")

    if m_col is None:
        raise ValueError(f"Cannot find M column. Columns: {list(df.columns)}")

    if idx_col is None:
        raise ValueError(
            "Cannot find kept token indices column. "
            f"Columns: {list(df.columns)}"
        )

    df[page_col] = df[page_col].astype(str)
    df[m_col] = pd.to_numeric(df[m_col], errors="coerce").astype("Int64")
    df = df.dropna(subset=[m_col]).copy()
    df[m_col] = df[m_col].astype(int)

    pages = sorted(df[page_col].unique())[: args.max_pages]
    grid = args.grid_size
    total_tokens = grid * grid

    for page_id in pages:
        sub = df[df[page_col] == page_id].copy()

        fig, axes = plt.subplots(1, len(args.m_list), figsize=(3.0 * len(args.m_list), 3.2))

        if len(args.m_list) == 1:
            axes = [axes]

        for ax, m in zip(axes, args.m_list):
            row = sub[sub[m_col] == m]

            mask = np.zeros(total_tokens, dtype=int)

            if not row.empty:
                indices = parse_indices(row.iloc[0][idx_col])

                for idx in indices:
                    if 0 <= idx < total_tokens:
                        mask[idx] = 1

            mask_2d = mask.reshape(grid, grid)

            ax.imshow(mask_2d, cmap="Blues", vmin=0, vmax=1)
            ax.set_title(f"{page_id}\nM={m}", fontsize=9)
            ax.set_xticks([])
            ax.set_yticks([])

        plt.tight_layout()

        safe_page_id = re.sub(r"[^a-zA-Z0-9_\\-]", "_", page_id)

        png_path = output_dir / f"day5_token_mask_{safe_page_id}.png"
        pdf_path = output_dir / f"day5_token_mask_{safe_page_id}.pdf"

        plt.savefig(png_path, dpi=300)
        plt.savefig(pdf_path)
        plt.close()

        print(f"[Figure] {png_path}")
        print(f"[Figure] {pdf_path}")

    print("[Done] Day 5 token mask visualization completed.")


if __name__ == "__main__":
    main()
