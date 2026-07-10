from pathlib import Path
import json
import time
import numpy as np
import pandas as pd

try:
    import faiss
except ImportError as e:
    raise ImportError("Please install faiss-cpu first: pip install faiss-cpu") from e


M = 24
N = 10
PQ_M = 16
BITS_LIST = [2, 4, 8]

PAGE_INPUT_DIR = Path(f"artifacts/embeddings/token_selection/pages_M{M}")
QUERY_DIR = Path("artifacts/embeddings/full_multivector/queries")
CANDIDATE_FILE = Path("artifacts/rerank_cache/single_vector_topN/single_vector_candidates_top10.tsv")
QRELS_FILE = Path("data/metadata/qrels.tsv")

COMP_ROOT = Path("artifacts/embeddings/joint_compression")
RUN_DIR = Path("results/budgeted/joint_compression/runs")
SCORE_DIR = Path("results/budgeted/joint_compression/scores")
LATENCY_DIR = Path("results/budgeted/joint_compression/latency")
METRIC_DIR = Path("results/budgeted/joint_compression/metrics")
INDEX_STATS_DIR = Path("results/budgeted/joint_compression/index_stats")
OUT_DIR = Path("results/budgeted/joint_compression/day5_analysis")

for d in [COMP_ROOT, RUN_DIR, SCORE_DIR, LATENCY_DIR, METRIC_DIR, INDEX_STATS_DIR, OUT_DIR]:
    d.mkdir(parents=True, exist_ok=True)


def run_name_for(bits: int) -> str:
    return f"w6_N{N}_M{M}_pq_b{bits}"


def out_dir_for(bits: int) -> Path:
    return COMP_ROOT / f"pages_M{M}_pq_b{bits}"


def safe_to_markdown(df: pd.DataFrame, path: Path):
    try:
        text = df.to_markdown(index=False)
    except Exception:
        text = df.to_string(index=False)

    with path.open("w", encoding="utf-8") as f:
        f.write(text)
        f.write("\n")


def normalize_id(x) -> str:
    if pd.isna(x):
        return ""
    return str(x).strip().strip('"').strip("'")


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


def load_page_embeddings(input_dir: Path):
    files = sorted(input_dir.glob("*.npy"))

    if not files:
        raise FileNotFoundError(f"No npy files found in {input_dir}")

    arrays = []
    meta = []
    offset = 0

    for fp in files:
        arr = np.load(fp).astype("float32")

        if arr.ndim != 2:
            raise ValueError(f"Invalid page embedding shape: {fp}, shape={arr.shape}")

        arrays.append(arr)
        meta.append({
            "file": fp.name,
            "num_tokens": int(arr.shape[0]),
            "dim": int(arr.shape[1]),
            "start": int(offset),
            "end": int(offset + arr.shape[0]),
        })
        offset += arr.shape[0]

    x = np.vstack(arrays).astype("float32")
    return files, meta, x


def save_reconstructed(meta, recon: np.ndarray, out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)

    for item in meta:
        arr = recon[item["start"]:item["end"]].astype("float32")
        np.save(out_dir / item["file"], arr)


def estimate_fp_payload_size_mb(num_vectors: int, dim: int) -> float:
    return num_vectors * dim * 4 / 1024 / 1024


def estimate_code_size_mb(num_vectors: int, pq_m: int, bits: int) -> float:
    return num_vectors * pq_m * bits / 8 / 1024 / 1024


def build_pq_reconstruction(x: np.ndarray, pq_m: int, bits: int):
    d = x.shape[1]

    if d % pq_m != 0:
        raise ValueError(f"dim={d} must be divisible by pq_m={pq_m}")

    pq = faiss.ProductQuantizer(d, pq_m, bits)

    t0 = time.time()
    pq.train(x)
    codes = pq.compute_codes(x)
    recon = pq.decode(codes).astype("float32")
    build_time = time.time() - t0

    return recon, codes, build_time


def is_header_like_row(row: pd.Series) -> bool:
    values = [normalize_id(v).lower() for v in row.tolist()]
    return (
        "query_id" in values
        or "qid" in values
        or "page_id" in values
        or "docid" in values
        or "rank" in values
    )


def load_candidates(path: Path) -> pd.DataFrame:
    raw = pd.read_csv(path, sep="\t", header=None, dtype=str)
    raw = raw[~raw.apply(is_header_like_row, axis=1)].copy()
    raw = raw.dropna(how="all").copy()

    if raw.shape[1] >= 6:
        df = raw.iloc[:, :6].copy()
        df.columns = ["query_id", "Q0", "page_id", "rank", "coarse_score", "tag"]
    elif raw.shape[1] == 5:
        df = raw.copy()
        df.columns = ["query_id", "page_id", "rank", "coarse_score", "tag"]
        df["Q0"] = "Q0"
    elif raw.shape[1] == 4:
        df = raw.copy()
        df.columns = ["query_id", "page_id", "rank", "coarse_score"]
        df["Q0"] = "Q0"
        df["tag"] = "candidate"
    elif raw.shape[1] == 3:
        df = raw.copy()
        df.columns = ["query_id", "page_id", "coarse_score"]
        df["rank"] = df.groupby("query_id").cumcount() + 1
        df["Q0"] = "Q0"
        df["tag"] = "candidate"
    else:
        raise ValueError(f"Unsupported candidate format: {path}, columns={raw.shape[1]}")

    df["query_id"] = df["query_id"].apply(normalize_id)
    df["page_id"] = df["page_id"].apply(normalize_id)

    df = df[(df["query_id"] != "") & (df["page_id"] != "")].copy()
    df = df[df["query_id"].str.lower() != "query_id"].copy()
    df = df[df["page_id"].str.lower() != "page_id"].copy()

    df["rank"] = pd.to_numeric(df["rank"], errors="coerce")
    df["coarse_score"] = pd.to_numeric(df["coarse_score"], errors="coerce").fillna(0.0)

    df["rank"] = df["rank"].fillna(df.groupby("query_id").cumcount() + 1).astype(int)
    df = df.sort_values(["query_id", "rank"]).reset_index(drop=True)

    return df


def find_query_file(query_id: str) -> Path:
    qid = normalize_id(query_id)

    candidates = [
        QUERY_DIR / f"{qid}.npy",
        QUERY_DIR / f"{qid}_query.npy",
        QUERY_DIR / f"query_{qid}.npy",
        QUERY_DIR / f"q_{qid}.npy",
    ]

    for fp in candidates:
        if fp.exists():
            return fp

    matches = sorted(QUERY_DIR.glob(f"*{qid}*.npy"))
    if matches:
        return matches[0]

    raise FileNotFoundError(f"Query embedding not found: {qid}")


def find_page_file(page_dir: Path, page_id: str) -> Path:
    pid = normalize_id(page_id)

    candidates = [
        page_dir / f"{pid}.npy",
        page_dir / f"{pid}_page.npy",
        page_dir / f"page_{pid}.npy",
        page_dir / f"p_{pid}.npy",
    ]

    for fp in candidates:
        if fp.exists():
            return fp

    matches = sorted(page_dir.glob(f"*{pid}*.npy"))
    if matches:
        return matches[0]

    raise FileNotFoundError(f"Page embedding not found: {pid} in {page_dir}")


def late_interaction_score(q: np.ndarray, p: np.ndarray) -> float:
    sim = q @ p.T
    return float(sim.max(axis=1).sum())


def rerank_one(bits: int, page_dir: Path, candidates: pd.DataFrame) -> dict:
    run_name = run_name_for(bits)

    run_rows = []
    score_rows = []
    missing_rows = []

    query_ids = sorted(candidates["query_id"].unique())

    query_cache = {}
    page_cache = {}

    valid_query_count = 0
    valid_candidate_count = 0

    t0 = time.time()

    for qid in query_ids:
        try:
            q_file = find_query_file(qid)
        except FileNotFoundError as e:
            missing_rows.append({
                "run_name": run_name,
                "query_id": qid,
                "page_id": "",
                "missing_type": "query",
                "message": str(e),
            })
            continue

        if q_file not in query_cache:
            query_cache[q_file] = np.load(q_file).astype("float32")

        q = query_cache[q_file]
        sub = candidates[candidates["query_id"] == qid].copy()

        page_scores = []

        for _, row in sub.iterrows():
            pid = row["page_id"]

            try:
                p_file = find_page_file(page_dir, pid)
            except FileNotFoundError as e:
                missing_rows.append({
                    "run_name": run_name,
                    "query_id": qid,
                    "page_id": pid,
                    "missing_type": "page",
                    "message": str(e),
                })
                continue

            if p_file not in page_cache:
                page_cache[p_file] = np.load(p_file).astype("float32")

            p = page_cache[p_file]
            score = late_interaction_score(q, p)

            page_scores.append((pid, score))
            valid_candidate_count += 1

            score_rows.append({
                "query_id": qid,
                "page_id": pid,
                "score": score,
                "run_name": run_name,
                "bits": bits,
                "query_file": str(q_file),
                "page_file": str(p_file),
            })

        page_scores = sorted(page_scores, key=lambda x: x[1], reverse=True)

        if page_scores:
            valid_query_count += 1

        for rank, (pid, score) in enumerate(page_scores, start=1):
            run_rows.append({
                "query_id": qid,
                "Q0": "Q0",
                "page_id": pid,
                "rank": rank,
                "score": score,
                "tag": run_name,
            })

    elapsed = time.time() - t0
    latency_ms = elapsed / valid_query_count * 1000.0 if valid_query_count > 0 else None

    run_df = pd.DataFrame(run_rows)
    score_df = pd.DataFrame(score_rows)
    missing_df = pd.DataFrame(missing_rows)

    run_path = RUN_DIR / f"{run_name}_run.tsv"
    score_path = SCORE_DIR / f"{run_name}_scores.csv"
    latency_path = LATENCY_DIR / f"{run_name}_latency.json"
    missing_path = OUT_DIR / f"{run_name}_missing_embeddings.csv"

    run_df.to_csv(
        run_path,
        sep="\t",
        header=False,
        index=False,
        columns=["query_id", "Q0", "page_id", "rank", "score", "tag"],
    )

    score_df.to_csv(score_path, index=False, encoding="utf-8-sig")

    if not missing_df.empty:
        missing_df.to_csv(missing_path, index=False, encoding="utf-8-sig")

    latency = {
        "run_name": run_name,
        "N": N,
        "M": M,
        "Compression": f"PQ-b{bits}",
        "bits": bits,
        "input_query_count": int(len(query_ids)),
        "valid_query_count": int(valid_query_count),
        "input_candidate_rows": int(len(candidates)),
        "valid_candidate_count": int(valid_candidate_count),
        "rerank_time_seconds": float(elapsed),
        "per_query_latency_ms": float(latency_ms) if latency_ms is not None else None,
        "run_file": str(run_path),
        "score_file": str(score_path),
        "missing_file": str(missing_path) if not missing_df.empty else None,
        "page_dir": str(page_dir),
    }

    with latency_path.open("w", encoding="utf-8") as f:
        json.dump(latency, f, indent=2, ensure_ascii=False)

    return latency


def load_qrels(path: Path) -> dict:
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
        raise ValueError(f"Unsupported qrels format: {path}")

    df["query_id"] = df["query_id"].astype(str).str.strip()
    df["page_id"] = df["page_id"].astype(str).str.strip()
    df["rel"] = pd.to_numeric(df["rel"], errors="coerce").fillna(1).astype(float)
    df = df[df["rel"] > 0].copy()

    qrels = {}
    for qid, group in df.groupby("query_id"):
        qrels[str(qid)] = set(group["page_id"].astype(str).tolist())

    return qrels


def load_run(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, sep="\t", header=None, dtype=str)

    if df.shape[1] >= 6:
        df = df.iloc[:, :6]
        df.columns = ["query_id", "Q0", "page_id", "rank", "score", "tag"]
    elif df.shape[1] == 5:
        df.columns = ["query_id", "page_id", "rank", "score", "tag"]
        df["Q0"] = "Q0"
    else:
        raise ValueError(f"Unsupported run format: {path}")

    df["query_id"] = df["query_id"].astype(str).str.strip()
    df["page_id"] = df["page_id"].astype(str).str.strip()
    df["rank"] = pd.to_numeric(df["rank"], errors="coerce").fillna(999999).astype(int)
    df["score"] = pd.to_numeric(df["score"], errors="coerce").fillna(0.0)

    return df


def recall_at_k(ranked_docs, rel_docs, k: int) -> float:
    return 1.0 if any(doc in rel_docs for doc in ranked_docs[:k]) else 0.0


def rr_at_k(ranked_docs, rel_docs, k: int) -> float:
    for idx, doc in enumerate(ranked_docs[:k], start=1):
        if doc in rel_docs:
            return 1.0 / idx
    return 0.0


def ndcg_at_k(ranked_docs, rel_docs, k: int) -> float:
    dcg = 0.0
    for idx, doc in enumerate(ranked_docs[:k], start=1):
        rel = 1.0 if doc in rel_docs else 0.0
        dcg += rel / np.log2(idx + 1)

    ideal_hits = min(len(rel_docs), k)
    idcg = sum(1.0 / np.log2(idx + 1) for idx in range(1, ideal_hits + 1))

    return float(dcg / idcg) if idcg > 0 else 0.0


def evaluate_run(run_df: pd.DataFrame, qrels: dict) -> dict:
    r1, r5, r10, mrr10, ndcg10 = [], [], [], [], []

    missing = 0

    for qid, rel_docs in qrels.items():
        sub = run_df[run_df["query_id"] == qid].sort_values("rank")

        if sub.empty:
            ranked = []
            missing += 1
        else:
            ranked = sub["page_id"].tolist()

        r1.append(recall_at_k(ranked, rel_docs, 1))
        r5.append(recall_at_k(ranked, rel_docs, 5))
        r10.append(recall_at_k(ranked, rel_docs, 10))
        mrr10.append(rr_at_k(ranked, rel_docs, 10))
        ndcg10.append(ndcg_at_k(ranked, rel_docs, 10))

    return {
        "evaluated_queries": int(len(qrels)),
        "missing_run_queries": int(missing),
        "Recall@1": float(np.mean(r1)),
        "Recall@5": float(np.mean(r5)),
        "Recall@10": float(np.mean(r10)),
        "MRR@10": float(np.mean(mrr10)),
        "nDCG@10": float(np.mean(ndcg10)),
    }


def main():
    files, meta, x = load_page_embeddings(PAGE_INPUT_DIR)
    candidates = load_candidates(CANDIDATE_FILE)
    qrels = load_qrels(QRELS_FILE)

    rows = []

    for bits in BITS_LIST:
        run_name = run_name_for(bits)
        out_dir = out_dir_for(bits)

        print("=" * 80)
        print(f"[Bits Sweep] {run_name}")

        recon, codes, build_time_sec = build_pq_reconstruction(x, PQ_M, bits)
        save_reconstructed(meta, recon, out_dir)

        num_vectors = int(x.shape[0])
        dim = int(x.shape[1])

        original_fp_file_size_mb = file_size_mb(PAGE_INPUT_DIR)
        original_fp_payload_size_mb = estimate_fp_payload_size_mb(num_vectors, dim)
        reconstructed_file_size_mb = file_size_mb(out_dir)
        estimated_code_size_mb = estimate_code_size_mb(num_vectors, PQ_M, bits)

        mse = float(np.mean((x - recon) ** 2))
        mae = float(np.mean(np.abs(x - recon)))

        stats = {
            "run_name": run_name,
            "N": N,
            "M": M,
            "Compression": f"PQ-b{bits}",
            "compression": f"PQ-b{bits}",
            "bits": bits,
            "pq_m": PQ_M,
            "num_pages": int(len(files)),
            "total_vectors": num_vectors,
            "dim": dim,
            "input_dir": str(PAGE_INPUT_DIR),
            "output_dir": str(out_dir),
            "original_fp_file_size_mb": original_fp_file_size_mb,
            "original_fp_payload_size_mb": original_fp_payload_size_mb,
            "reconstructed_file_size_mb": reconstructed_file_size_mb,
            "estimated_code_size_mb": estimated_code_size_mb,
            "index_size_mb": estimated_code_size_mb,
            "estimated_compression_ratio_vs_fp_payload": (
                original_fp_payload_size_mb / estimated_code_size_mb
                if estimated_code_size_mb > 0 else None
            ),
            "mse": mse,
            "mae": mae,
            "build_time_sec": build_time_sec,
            "index_built": True,
            "reconstruct_mode": "pq_decode",
            "code_size_bytes_per_vector": float(PQ_M * bits / 8),
        }

        stats_path = INDEX_STATS_DIR / f"{run_name}_index_stats.json"
        with stats_path.open("w", encoding="utf-8") as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)

        latency = rerank_one(bits, out_dir, candidates)

        run_path = RUN_DIR / f"{run_name}_run.tsv"
        run_df = load_run(run_path)
        metrics = evaluate_run(run_df, qrels)

        row = {
            "run_name": run_name,
            "N": N,
            "M": M,
            "Compression": f"PQ-b{bits}",
            "bits": bits,
            **metrics,
            "Index Size MB": estimated_code_size_mb,
            "Original FP Payload Size MB": original_fp_payload_size_mb,
            "Compression Ratio vs FP Payload": stats["estimated_compression_ratio_vs_fp_payload"],
            "MSE": mse,
            "MAE": mae,
            "Build Time sec": build_time_sec,
            "Latency ms/query": latency["per_query_latency_ms"],
            "Rerank Time sec": latency["rerank_time_seconds"],
            "run_file": str(run_path),
            "index_stats_file": str(stats_path),
        }

        metric_path = METRIC_DIR / f"{run_name}_metrics.json"
        with metric_path.open("w", encoding="utf-8") as f:
            json.dump(row, f, indent=2, ensure_ascii=False)

        rows.append(row)

        print(f"[Done] {run_name}")
        print(f"[bits] {bits}")
        print(f"[Recall@10] {row['Recall@10']:.4f}")
        print(f"[MRR@10] {row['MRR@10']:.4f}")
        print(f"[nDCG@10] {row['nDCG@10']:.4f}")
        print(f"[Index Size MB] {row['Index Size MB']:.8f}")
        print(f"[MSE] {mse:.8f}")

    df = pd.DataFrame(rows)

    csv_path = OUT_DIR / "day5_bits_sweep_results.csv"
    md_path = OUT_DIR / "day5_bits_sweep_results.md"

    df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    safe_to_markdown(df, md_path)

    print("=" * 80)
    print("[Done] Day 5 bits sweep completed.")
    print(f"[Output] {csv_path}")
    print(f"[Output] {md_path}")


if __name__ == "__main__":
    main()
