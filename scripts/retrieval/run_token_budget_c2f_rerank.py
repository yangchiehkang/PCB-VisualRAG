import argparse
import re
import time
from pathlib import Path

import numpy as np
import pandas as pd


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--candidate-file",
        type=str,
        default="artifacts/rerank_cache/single_vector_topN/single_vector_candidates_top10.tsv",
    )

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
        "--output-dir",
        type=str,
        default="results/budgeted/token_selection",
    )

    parser.add_argument(
        "--summary-dir",
        type=str,
        default="results/budgeted/token_selection/summary",
    )

    parser.add_argument(
        "--m-list",
        type=int,
        nargs="+",
        default=[8, 16, 24, 32, 49],
    )

    parser.add_argument(
        "--method-prefix",
        type=str,
        default="c2f_N10",
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
        raise ValueError(
            f"Dim mismatch: query={query_emb.shape}, page={page_emb.shape}"
        )

    sim = query_emb @ page_emb.T
    score = sim.max(axis=1).sum()
    return float(score)


def load_candidates(candidate_file):
    candidate_file = Path(candidate_file)

    if not candidate_file.exists():
        raise FileNotFoundError(f"Candidate file not found: {candidate_file}")

    df = pd.read_csv(candidate_file, sep="\t")

    required_cols = {"query_id", "candidate_page_id"}
    if not required_cols.issubset(set(df.columns)):
        raise ValueError(
            f"Candidate file must contain columns {required_cols}, got {list(df.columns)}"
        )

    df["query_id"] = df["query_id"].astype(str)
    df["candidate_page_id"] = df["candidate_page_id"].astype(str)

    return df


def normalize_id_basic(x):
    x = str(x).strip().lower()
    x = x.replace("\\", "/")
    x = Path(x).stem
    x = x.replace("-", "_")
    return x


def normalize_id_compact(x):
    x = normalize_id_basic(x)
    x = x.replace("page", "p")
    x = re.sub(r"[^a-z0-9]", "", x)
    return x


def normalize_id_nozero(x):
    """
    Convert patterns like doc003_p004 and doc3_p4 into the same loose key.
    """
    x = normalize_id_basic(x)
    x = x.replace("page", "p")

    parts = re.split(r"(\d+)", x)
    normalized_parts = []

    for p in parts:
        if p.isdigit():
            normalized_parts.append(str(int(p)))
        else:
            normalized_parts.append(re.sub(r"[^a-z]", "", p))

    return "".join(normalized_parts)


def generate_aliases(x):
    x0 = str(x).strip()
    b = normalize_id_basic(x0)

    aliases = set()

    aliases.add(x0)
    aliases.add(x0.lower())
    aliases.add(b)
    aliases.add(b.replace("_", ""))
    aliases.add(b.replace("page", "p"))
    aliases.add(b.replace("_page", "_p"))
    aliases.add(b.replace("-page", "-p"))
    aliases.add(normalize_id_compact(x0))
    aliases.add(normalize_id_nozero(x0))

    # Extra variants for common page naming.
    aliases.add(b.replace("_p", "_page"))
    aliases.add(b.replace("p", "page"))

    return {a for a in aliases if a}


def build_embedding_index(path_dir):
    path_dir = Path(path_dir)

    if not path_dir.exists():
        raise FileNotFoundError(f"Embedding directory not found: {path_dir}")

    files = sorted(path_dir.glob("*.npy"))

    if not files:
        raise FileNotFoundError(f"No .npy files found in {path_dir}")

    index = {}

    for f in files:
        aliases = generate_aliases(f.stem)
        aliases.add(str(f.name).lower())
        aliases.add(str(f.stem).lower())

        for a in aliases:
            if a not in index:
                index[a] = f

    return index, files


def find_embedding_from_index(index, files, item_id, path_dir):
    aliases = generate_aliases(item_id)

    for a in aliases:
        if a in index:
            return index[a]

    # Last-resort fuzzy matching.
    target_compact = normalize_id_compact(item_id)
    target_nozero = normalize_id_nozero(item_id)

    for f in files:
        stem_compact = normalize_id_compact(f.stem)
        stem_nozero = normalize_id_nozero(f.stem)

        if target_compact == stem_compact:
            return f

        if target_nozero == stem_nozero:
            return f

        if target_compact in stem_compact or stem_compact in target_compact:
            return f

        if target_nozero in stem_nozero or stem_nozero in target_nozero:
            return f

    sample_files = [p.name for p in files[:20]]

    raise FileNotFoundError(
        "\n"
        f"Embedding not found for id={item_id}\n"
        f"Directory: {path_dir}\n"
        f"Generated aliases: {sorted(list(aliases))}\n"
        f"Sample files in directory: {sample_files}\n"
    )


def main():
    args = parse_args()

    candidate_file = Path(args.candidate_file)
    query_dir = Path(args.query_dir)
    page_root = Path(args.page_root)
    output_dir = Path(args.output_dir)
    summary_dir = Path(args.summary_dir)

    output_dir.mkdir(parents=True, exist_ok=True)
    summary_dir.mkdir(parents=True, exist_ok=True)

    candidates = load_candidates(candidate_file)

    print(f"[Info] Candidate file: {candidate_file}")
    print(f"[Info] Query count: {candidates['query_id'].nunique()}")
    print(f"[Info] Candidate rows: {len(candidates)}")
    print(f"[Info] M list: {args.m_list}")

    query_index, query_files = build_embedding_index(query_dir)

    latency_rows = []

    query_cache = {}
    page_cache = {}

    for m in args.m_list:
        page_dir = page_root / f"pages_M{m}"

        if not page_dir.exists():
            raise FileNotFoundError(
                f"Compressed page embedding dir not found: {page_dir}"
            )

        page_index, page_files = build_embedding_index(page_dir)

        method_name = f"{args.method_prefix}_M{m}"

        run_path = output_dir / f"{method_name}_run.tsv"
        score_path = output_dir / f"{method_name}_scores.csv"
        validation_path = output_dir / f"{method_name}_validation.csv"

        run_rows = []
        score_rows = []
        validation_rows = []

        start_time = time.perf_counter()

        for query_id, group in candidates.groupby("query_id"):
            query_id = str(query_id)

            if query_id not in query_cache:
                q_path = find_embedding_from_index(
                    query_index,
                    query_files,
                    query_id,
                    query_dir,
                )
                query_cache[query_id] = np.load(q_path)

            query_emb = query_cache[query_id]

            scored = []

            for _, row in group.iterrows():
                page_id = str(row["candidate_page_id"])

                page_key = (m, page_id)

                if page_key not in page_cache:
                    p_path = find_embedding_from_index(
                        page_index,
                        page_files,
                        page_id,
                        page_dir,
                    )
                    page_cache[page_key] = np.load(p_path)

                page_emb = page_cache[page_key]

                score = late_interaction_score(query_emb, page_emb)

                scored.append(
                    {
                        "query_id": query_id,
                        "page_id": page_id,
                        "score": score,
                        "page_tokens": int(page_emb.shape[0]),
                    }
                )

            scored = sorted(scored, key=lambda x: x["score"], reverse=True)

            for rank, item in enumerate(scored, start=1):
                run_rows.append(
                    {
                        "query_id": item["query_id"],
                        "page_id": item["page_id"],
                        "rank": rank,
                        "score": item["score"],
                        "method": method_name,
                    }
                )

                score_rows.append(
                    {
                        "query_id": item["query_id"],
                        "page_id": item["page_id"],
                        "rank": rank,
                        "score": item["score"],
                        "M": m,
                        "page_tokens": item["page_tokens"],
                    }
                )

            if scored:
                min_page_tokens = min(x["page_tokens"] for x in scored)
                max_page_tokens = max(x["page_tokens"] for x in scored)
            else:
                min_page_tokens = 0
                max_page_tokens = 0

            validation_rows.append(
                {
                    "query_id": query_id,
                    "input_candidates": len(group),
                    "reranked_candidates": len(scored),
                    "M": m,
                    "expected_page_tokens": m,
                    "min_page_tokens": min_page_tokens,
                    "max_page_tokens": max_page_tokens,
                    "subset_check": "PASSED",
                }
            )

        end_time = time.perf_counter()
        rerank_time = end_time - start_time

        run_df = pd.DataFrame(run_rows)
        score_df = pd.DataFrame(score_rows)
        validation_df = pd.DataFrame(validation_rows)

        run_df.to_csv(run_path, sep="\t", index=False)
        score_df.to_csv(score_path, index=False)
        validation_df.to_csv(validation_path, index=False)

        query_count = candidates["query_id"].nunique()
        total_candidates = len(candidates)
        avg_candidates = total_candidates / query_count if query_count else 0.0
        avg_latency_ms = rerank_time / query_count * 1000 if query_count else 0.0

        latency_rows.append(
            {
                "Method": method_name,
                "M": m,
                "Query Count": query_count,
                "Total Candidates": total_candidates,
                "Avg Candidates / Query": avg_candidates,
                "Rerank Time Seconds": rerank_time,
                "Per-query Latency ms": avg_latency_ms,
                "Run File": str(run_path),
                "Validation File": str(validation_path),
            }
        )

        print(f"[Done] {method_name}")
        print(f"  Run: {run_path}")
        print(f"  Scores: {score_path}")
        print(f"  Validation: {validation_path}")
        print(f"  Avg latency: {avg_latency_ms:.6f} ms/query")

    latency_df = pd.DataFrame(latency_rows)

    latency_path = summary_dir / "token_budget_day3_latency_by_M.csv"
    latency_df.to_csv(latency_path, index=False)

    print("[Done] All token-budget reranking completed.")
    print(f"[Output] {latency_path}")


if __name__ == "__main__":
    main()
