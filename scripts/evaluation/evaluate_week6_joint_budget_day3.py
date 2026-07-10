from pathlib import Path
import json
import numpy as np
import pandas as pd


QRELS_FILE = Path("data/metadata/qrels.tsv")

TOKEN_ROOT = Path("artifacts/embeddings/token_selection")

RUN_DIR = Path("results/budgeted/joint_compression/runs")
LATENCY_DIR = Path("results/budgeted/joint_compression/latency")
INDEX_STATS_DIR = Path("results/budgeted/joint_compression/index_stats")
METRIC_DIR = Path("results/budgeted/joint_compression/metrics")

DAY3_DIR = Path("results/budgeted/joint_compression/day3_main")
SUMMARY_DIR = Path("results/budgeted/joint_compression/summary")

METRIC_DIR.mkdir(parents=True, exist_ok=True)
DAY3_DIR.mkdir(parents=True, exist_ok=True)
SUMMARY_DIR.mkdir(parents=True, exist_ok=True)


BUDGET_MS = [8, 16, 24]
COMPRESSIONS = ["None", "PQ", "OPQ+PQ", "IVF+PQ", "IVF+OPQ+PQ"]


def comp_slug(compression: str) -> str:
    if compression == "None":
        return "none"
    return compression.lower().replace("+", "_").replace(" ", "").replace("__", "_")


def run_name_for(m: int, compression: str) -> str:
    return f"w6_N10_M{m}_{comp_slug(compression)}"


def safe_to_markdown(df: pd.DataFrame, path: Path):
    try:
        text = df.to_markdown(index=False)
    except Exception:
        text = df.to_string(index=False)

    with path.open("w", encoding="utf-8") as f:
        f.write(text)
        f.write("\n")


def file_size_mb(path: Path) -> float:
    if not path.exists():
        return 0.0

    if path.is_file():
        return path.stat().st_size / 1024 / 1024

    total = 0
    for fp in path.rglob("*"):
        if fp.is_file():
            total += fp.stat().st_size

    return total / 1024 / 1024


def estimate_fp_payload_size_mb(page_dir: Path) -> float:
    total_bytes = 0

    if not page_dir.exists():
        return 0.0

    for fp in page_dir.glob("*.npy"):
        arr = np.load(fp, mmap_mode="r")
        total_bytes += int(np.prod(arr.shape)) * 4

    return total_bytes / 1024 / 1024


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}

    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_qrels(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Qrels file not found: {path}")

    df = pd.read_csv(path, sep="\t", header=None, dtype=str)

    first_col = df.iloc[:, 0].astype(str).str.lower()
    df = df[(first_col != "query_id") & (first_col != "qid")].copy()

    if df.shape[1] >= 4:
        df = df.iloc[:, :4]
        df.columns = ["query_id", "unused", "page_id", "rel"]
    elif df.shape[1] == 3:
        df.columns = ["query_id", "page_id", "rel"]
    elif df.shape[1] == 2:
        df.columns = ["query_id", "page_id"]
        df["rel"] = 1
    else:
        raise ValueError(f"Unsupported qrels format: {path}, columns={df.shape[1]}")

    df["query_id"] = df["query_id"].astype(str).str.strip()
    df["page_id"] = df["page_id"].astype(str).str.strip()
    df["rel"] = pd.to_numeric(df["rel"], errors="coerce").fillna(1).astype(float)

    df = df[df["rel"] > 0].copy()

    qrels = {}
    for qid, group in df.groupby("query_id"):
        qrels[str(qid)] = set(group["page_id"].astype(str).tolist())

    return qrels


def load_run(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Run file not found: {path}")

    df = pd.read_csv(path, sep="\t", header=None, dtype=str)

    if df.empty:
        raise ValueError(f"Run file is empty: {path}")

    if df.shape[1] >= 6:
        df = df.iloc[:, :6]
        df.columns = ["query_id", "Q0", "page_id", "rank", "score", "tag"]
    elif df.shape[1] == 5:
        df.columns = ["query_id", "page_id", "rank", "score", "tag"]
        df["Q0"] = "Q0"
    else:
        raise ValueError(f"Unsupported run format: {path}, columns={df.shape[1]}")

    df["query_id"] = df["query_id"].astype(str).str.strip()
    df["page_id"] = df["page_id"].astype(str).str.strip()
    df["rank"] = pd.to_numeric(df["rank"], errors="coerce").fillna(999999).astype(int)
    df["score"] = pd.to_numeric(df["score"], errors="coerce").fillna(0.0).astype(float)

    return df


def recall_at_k(ranked_docs, rel_docs, k: int) -> float:
    topk = ranked_docs[:k]
    return 1.0 if any(doc in rel_docs for doc in topk) else 0.0


def reciprocal_rank_at_k(ranked_docs, rel_docs, k: int) -> float:
    topk = ranked_docs[:k]

    for idx, doc in enumerate(topk, start=1):
        if doc in rel_docs:
            return 1.0 / idx

    return 0.0


def ndcg_at_k(ranked_docs, rel_docs, k: int) -> float:
    topk = ranked_docs[:k]

    dcg = 0.0
    for idx, doc in enumerate(topk, start=1):
        rel = 1.0 if doc in rel_docs else 0.0
        dcg += rel / np.log2(idx + 1)

    ideal_hits = min(len(rel_docs), k)
    idcg = sum(1.0 / np.log2(idx + 1) for idx in range(1, ideal_hits + 1))

    if idcg <= 0:
        return 0.0

    return float(dcg / idcg)


def evaluate_run(run_df: pd.DataFrame, qrels: dict) -> dict:
    r1_list = []
    r5_list = []
    r10_list = []
    mrr10_list = []
    ndcg10_list = []

    evaluated_queries = 0
    missing_run_queries = 0

    for qid, rel_docs in qrels.items():
        sub = run_df[run_df["query_id"] == qid].sort_values("rank")

        if sub.empty:
            ranked_docs = []
            missing_run_queries += 1
        else:
            ranked_docs = sub["page_id"].tolist()

        r1_list.append(recall_at_k(ranked_docs, rel_docs, 1))
        r5_list.append(recall_at_k(ranked_docs, rel_docs, 5))
        r10_list.append(recall_at_k(ranked_docs, rel_docs, 10))
        mrr10_list.append(reciprocal_rank_at_k(ranked_docs, rel_docs, 10))
        ndcg10_list.append(ndcg_at_k(ranked_docs, rel_docs, 10))

        evaluated_queries += 1

    return {
        "evaluated_queries": int(evaluated_queries),
        "missing_run_queries": int(missing_run_queries),
        "Recall@1": float(np.mean(r1_list)) if r1_list else 0.0,
        "Recall@5": float(np.mean(r5_list)) if r5_list else 0.0,
        "Recall@10": float(np.mean(r10_list)) if r10_list else 0.0,
        "MRR@10": float(np.mean(mrr10_list)) if mrr10_list else 0.0,
        "nDCG@10": float(np.mean(ndcg10_list)) if ndcg10_list else 0.0,
    }


def get_index_stats(m: int, compression: str, run_name: str) -> dict:
    if compression == "None":
        page_dir = TOKEN_ROOT / f"pages_M{m}"

        fp_file_size_mb = file_size_mb(page_dir)
        fp_payload_size_mb = estimate_fp_payload_size_mb(page_dir)

        return {
            "index_stats_file": None,
            "original_fp_file_size_mb": fp_file_size_mb,
            "original_fp_payload_size_mb": fp_payload_size_mb,
            "reconstructed_file_size_mb": fp_file_size_mb,
            "estimated_code_size_mb": fp_payload_size_mb,
            "index_size_mb": fp_payload_size_mb,
            "estimated_compression_ratio_vs_fp_payload": 1.0,
            "file_ratio_vs_fp_files": 1.0,
            "mse": 0.0,
            "mae": 0.0,
            "build_time_sec": 0.0,
            "pq_m": None,
            "bits": None,
            "nlist": None,
            "nprobe": None,
            "reconstruct_mode": "none",
            "index_built": True,
        }

    stats_path = INDEX_STATS_DIR / f"{run_name}_index_stats.json"
    stats = load_json(stats_path)

    return {
        "index_stats_file": str(stats_path) if stats_path.exists() else None,
        "original_fp_file_size_mb": stats.get("original_fp_file_size_mb"),
        "original_fp_payload_size_mb": stats.get("original_fp_payload_size_mb"),
        "reconstructed_file_size_mb": stats.get("reconstructed_file_size_mb"),
        "estimated_code_size_mb": stats.get("estimated_code_size_mb"),
        "index_size_mb": stats.get("estimated_code_size_mb"),
        "estimated_compression_ratio_vs_fp_payload": stats.get("estimated_compression_ratio_vs_fp_payload"),
        "file_ratio_vs_fp_files": stats.get("file_ratio_vs_fp_files"),
        "mse": stats.get("mse"),
        "mae": stats.get("mae"),
        "build_time_sec": stats.get("build_time_sec"),
        "pq_m": stats.get("pq_m"),
        "bits": stats.get("bits"),
        "nlist": stats.get("nlist"),
        "nprobe": stats.get("nprobe"),
        "reconstruct_mode": stats.get("reconstruct_mode"),
        "index_built": stats.get("index_built", False),
    }


def main():
    print("[Info] Loading qrels...")
    qrels = load_qrels(QRELS_FILE)
    print(f"[Info] Evaluated qrels queries: {len(qrels)}")

    rows = []

    for m in BUDGET_MS:
        for compression in COMPRESSIONS:
            run_name = run_name_for(m, compression)
            run_path = RUN_DIR / f"{run_name}_run.tsv"
            latency_path = LATENCY_DIR / f"{run_name}_latency.json"

            print("=" * 80)
            print(f"[Eval] {run_name}")

            run_df = load_run(run_path)
            metric_values = evaluate_run(run_df, qrels)

            latency = load_json(latency_path)
            index_stats = get_index_stats(m, compression, run_name)

            row = {
                "run_name": run_name,
                "N": 10,
                "M": m,
                "Compression": compression,
                **metric_values,
                "Index Size MB": index_stats.get("index_size_mb"),
                "Estimated Code Size MB": index_stats.get("estimated_code_size_mb"),
                "Reconstructed File Size MB": index_stats.get("reconstructed_file_size_mb"),
                "Original FP Payload Size MB": index_stats.get("original_fp_payload_size_mb"),
                "Original FP File Size MB": index_stats.get("original_fp_file_size_mb"),
                "Compression Ratio vs FP Payload": index_stats.get("estimated_compression_ratio_vs_fp_payload"),
                "MSE": index_stats.get("mse"),
                "MAE": index_stats.get("mae"),
                "pq_m": index_stats.get("pq_m"),
                "bits": index_stats.get("bits"),
                "nlist": index_stats.get("nlist"),
                "nprobe": index_stats.get("nprobe"),
                "reconstruct_mode": index_stats.get("reconstruct_mode"),
                "Build Time sec": index_stats.get("build_time_sec"),
                "Latency ms/query": latency.get("per_query_latency_ms"),
                "Rerank Time sec": latency.get("rerank_time_seconds"),
                "Valid Query Count": latency.get("valid_query_count", latency.get("query_count")),
                "Valid Candidate Count": latency.get("valid_candidate_count", latency.get("total_candidates")),
                "run_file": str(run_path),
                "latency_file": str(latency_path),
                "index_stats_file": index_stats.get("index_stats_file"),
            }

            metric_path = METRIC_DIR / f"{run_name}_metrics.json"
            with metric_path.open("w", encoding="utf-8") as f:
                json.dump(row, f, indent=2, ensure_ascii=False)

            rows.append(row)

            print(f"[Recall@10] {row['Recall@10']:.4f}")
            print(f"[MRR@10] {row['MRR@10']:.4f}")
            print(f"[nDCG@10] {row['nDCG@10']:.4f}")
            print(f"[Index Size MB] {row['Index Size MB']}")
            print(f"[Latency ms/query] {row['Latency ms/query']}")

    df = pd.DataFrame(rows)

    main_cols = [
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

    main_df = df[main_cols].copy()

    detailed_csv = DAY3_DIR / "day3_joint_budget_results_detailed.csv"
    detailed_md = DAY3_DIR / "day3_joint_budget_results_detailed.md"

    main_csv = SUMMARY_DIR / "joint_budget_results.csv"
    main_md = SUMMARY_DIR / "joint_budget_results.md"
    xlsx_path = SUMMARY_DIR / "joint_budget_results.xlsx"

    df.to_csv(detailed_csv, index=False, encoding="utf-8-sig")
    safe_to_markdown(df, detailed_md)

    main_df.to_csv(main_csv, index=False, encoding="utf-8-sig")
    safe_to_markdown(main_df, main_md)

    try:
        with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
            main_df.to_excel(writer, index=False, sheet_name="main_results")
            df.to_excel(writer, index=False, sheet_name="detailed_results")
    except Exception:
        with pd.ExcelWriter(xlsx_path) as writer:
            main_df.to_excel(writer, index=False, sheet_name="main_results")
            df.to_excel(writer, index=False, sheet_name="detailed_results")

    print("=" * 80)
    print("[Done] Day 3 joint budget evaluation completed.")
    print(f"[Output] {main_csv}")
    print(f"[Output] {main_md}")
    print(f"[Output] {xlsx_path}")
    print(f"[Output] {detailed_csv}")
    print(f"[Output] {detailed_md}")


if __name__ == "__main__":
    main()
