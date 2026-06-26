import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input-dir",
        type=str,
        default="artifacts/embeddings/full_multivector/pages",
    )
    parser.add_argument(
        "--output-root",
        type=str,
        default="artifacts/embeddings/token_selection",
    )
    parser.add_argument(
        "--summary-dir",
        type=str,
        default="results/budgeted/token_selection/day2_validation",
    )
    parser.add_argument(
        "--fig-dir",
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
        "--make-fig",
        action="store_true",
    )
    return parser.parse_args()


def select_top_m_by_norm(page_emb, m):
    original_tokens = page_emb.shape[0]
    m_eff = min(m, original_tokens)

    norms = np.linalg.norm(page_emb, axis=1)
    top_idx_by_score = np.argsort(-norms)[:m_eff]
    kept_indices = np.sort(top_idx_by_score)

    selected_emb = page_emb[kept_indices]

    return selected_emb, kept_indices, norms


def make_mask_figure(mask_records, fig_path):
    import matplotlib.pyplot as plt

    if not mask_records:
        return

    n_rows = len(mask_records)
    fig, axes = plt.subplots(n_rows, 1, figsize=(6, 2.2 * n_rows))

    if n_rows == 1:
        axes = [axes]

    for ax, record in zip(axes, mask_records):
        page_id = record["page_id"]
        m = record["M"]
        mask = record["mask"]
        original_tokens = len(mask)

        side = int(np.sqrt(original_tokens))

        if side * side == original_tokens:
            grid = mask.reshape(side, side)
            ax.imshow(grid, cmap="Blues", vmin=0, vmax=1)
            ax.set_xticks([])
            ax.set_yticks([])
            ax.set_title(f"{page_id} | M={m} | selected tokens")
        else:
            ax.bar(np.arange(original_tokens), mask)
            ax.set_title(f"{page_id} | M={m} | selected tokens")
            ax.set_xlabel("Token index")
            ax.set_ylabel("Selected")

    plt.tight_layout()
    fig.savefig(fig_path, dpi=200)
    plt.close(fig)


def main():
    args = parse_args()

    input_dir = Path(args.input_dir)
    output_root = Path(args.output_root)
    summary_dir = Path(args.summary_dir)
    fig_dir = Path(args.fig_dir)

    output_root.mkdir(parents=True, exist_ok=True)
    summary_dir.mkdir(parents=True, exist_ok=True)
    fig_dir.mkdir(parents=True, exist_ok=True)

    page_files = sorted(input_dir.glob("*.npy"))

    if args.max_pages is not None and args.max_pages > 0:
        page_files = page_files[: args.max_pages]

    if not page_files:
        raise FileNotFoundError(f"No .npy page embeddings found in {input_dir}")

    all_rows = []
    summary_rows = []
    mask_records = []

    for m in args.m_list:
        out_dir = output_root / f"pages_M{m}"
        out_dir.mkdir(parents=True, exist_ok=True)

        m_rows = []

        for page_path in page_files:
            page_id = page_path.stem
            page_emb = np.load(page_path)

            if page_emb.ndim != 2:
                raise ValueError(f"Invalid page embedding shape for {page_path}: {page_emb.shape}")

            original_tokens, dim = page_emb.shape

            selected_emb, kept_indices, norms = select_top_m_by_norm(page_emb, m)

            out_path = out_dir / page_path.name
            np.save(out_path, selected_emb)

            keep_ratio = selected_emb.shape[0] / original_tokens
            reduction_ratio = 1.0 - keep_ratio

            row = {
                "page_id": page_id,
                "M": m,
                "original_tokens": original_tokens,
                "kept_tokens": selected_emb.shape[0],
                "dim": dim,
                "keep_ratio": keep_ratio,
                "reduction_ratio": reduction_ratio,
                "kept_indices": " ".join(map(str, kept_indices.tolist())),
                "input_path": str(page_path),
                "output_path": str(out_path),
                "status": "PASSED",
            }

            all_rows.append(row)
            m_rows.append(row)

            if args.make_fig and len(mask_records) < 12:
                mask = np.zeros(original_tokens, dtype=np.float32)
                mask[kept_indices] = 1.0
                mask_records.append(
                    {
                        "page_id": page_id,
                        "M": m,
                        "mask": mask,
                    }
                )

        m_df = pd.DataFrame(m_rows)
        m_df.to_csv(summary_dir / f"day2_token_selection_metadata_M{m}.csv", index=False)

        summary_rows.append(
            {
                "M": m,
                "num_pages": len(m_rows),
                "avg_original_tokens": float(np.mean([r["original_tokens"] for r in m_rows])),
                "avg_kept_tokens": float(np.mean([r["kept_tokens"] for r in m_rows])),
                "avg_keep_ratio": float(np.mean([r["keep_ratio"] for r in m_rows])),
                "avg_reduction_ratio": float(np.mean([r["reduction_ratio"] for r in m_rows])),
                "output_dir": str(out_dir),
            }
        )

    all_df = pd.DataFrame(all_rows)
    all_df.to_csv(summary_dir / "day2_token_selection_metadata_all.csv", index=False)

    summary_df = pd.DataFrame(summary_rows)
    summary_df.to_csv(summary_dir / "day2_token_selection_summary.csv", index=False)

    summary_json = {
        "input_dir": str(input_dir),
        "output_root": str(output_root),
        "m_list": args.m_list,
        "num_test_pages": len(page_files),
        "summary": summary_rows,
    }

    with open(summary_dir / "day2_token_selection_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary_json, f, ensure_ascii=False, indent=2)

    if args.make_fig:
        fig_path = fig_dir / "day2_token_selection_masks_sample.png"
        make_mask_figure(mask_records, fig_path)

    print("[Done] Token selection completed.")
    print(f"[Output] {summary_dir / 'day2_token_selection_summary.csv'}")
    print(f"[Output] {summary_dir / 'day2_token_selection_metadata_all.csv'}")


if __name__ == "__main__":
    main()
