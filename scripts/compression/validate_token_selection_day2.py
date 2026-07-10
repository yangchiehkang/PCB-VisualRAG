import argparse
from pathlib import Path

import numpy as np
import pandas as pd


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--query-dir",
        type=str,
        default="artifacts/embeddings/full_multivector/queries",
    )
    parser.add_argument(
        "--page-root",
        type=str,
        default="artifacts/embeddings/token_selection",
    )
    parser.add_argument(
        "--summary-dir",
        type=str,
        default="results/budgeted/token_selection/day2_validation",
    )
    parser.add_argument(
        "--m-list",
        type=int,
        nargs="+",
        default=[8, 16, 24, 32, 49],
    )
    return parser.parse_args()


def ensure_2d(x):
    if x.ndim == 1:
        return x.reshape(1, -1)
    return x


def late_interaction_score(query_emb, page_emb):
    query_emb = ensure_2d(query_emb)
    page_emb = ensure_2d(page_emb)

    if query_emb.shape[1] != page_emb.shape[1]:
        raise ValueError(f"Dim mismatch: query={query_emb.shape}, page={page_emb.shape}")

    sim = query_emb @ page_emb.T
    score = sim.max(axis=1).sum()
    return float(score)


def main():
    args = parse_args()

    query_dir = Path(args.query_dir)
    page_root = Path(args.page_root)
    summary_dir = Path(args.summary_dir)
    summary_dir.mkdir(parents=True, exist_ok=True)

    query_files = sorted(query_dir.glob("*.npy"))
    if not query_files:
        raise FileNotFoundError(f"No query embeddings found in {query_dir}")

    query_path = query_files[0]
    query_emb = np.load(query_path)

    rows = []

    for m in args.m_list:
        page_dir = page_root / f"pages_M{m}"
        page_files = sorted(page_dir.glob("*.npy"))

        if not page_files:
            rows.append(
                {
                    "M": m,
                    "query_file": str(query_path),
                    "page_file": "",
                    "query_shape": str(query_emb.shape),
                    "page_shape": "",
                    "score": "",
                    "status": "FAILED_NO_PAGE_FILE",
                }
            )
            continue

        page_path = page_files[0]
        page_emb = np.load(page_path)

        try:
            score = late_interaction_score(query_emb, page_emb)
            status = "PASSED"
        except Exception as e:
            score = ""
            status = f"FAILED: {e}"

        rows.append(
            {
                "M": m,
                "query_file": str(query_path),
                "page_file": str(page_path),
                "query_shape": str(query_emb.shape),
                "page_shape": str(page_emb.shape),
                "score": score,
                "status": status,
            }
        )

    df = pd.DataFrame(rows)
    out_path = summary_dir / "day2_late_interaction_compatibility_check.csv"
    df.to_csv(out_path, index=False)

    print("[Done] Compatibility validation completed.")
    print(f"[Output] {out_path}")
    print(df)


if __name__ == "__main__":
    main()
