from pathlib import Path
import argparse
import json
import csv
import time
from datetime import datetime

import numpy as np
import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def log(msg):
    print(f"[{now()}] {msg}")


def ensure_exists(path: Path, name: str):
    if not path.exists():
        raise FileNotFoundError(f"{name} not found: {path}")


def load_yaml(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def read_jsonl(path: Path):
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def file_size_bytes(path: Path):
    return path.stat().st_size


def mean_pool(arr):
    v = arr.mean(axis=0)
    norm = np.linalg.norm(v)
    if norm > 0:
        v = v / norm
    return v.astype(np.float32)


def main():
    parser = argparse.ArgumentParser(description="Analyze Single-vector cost.")
    parser.add_argument("--config", type=str, default=str(PROJECT_ROOT / "configs" / "full_multivector.yaml"))
    parser.add_argument("--cost-output", type=str, default=str(PROJECT_ROOT / "results" / "analysis" / "single_vector_cost_stats.csv"))
    parser.add_argument("--latency-output", type=str, default=str(PROJECT_ROOT / "results" / "analysis" / "query_latency_details_single_vector.csv"))
    args = parser.parse_args()

    cfg = load_yaml(Path(args.config))

    page_meta_file = PROJECT_ROOT / cfg["outputs"]["page_meta_file"]
    query_meta_file = PROJECT_ROOT / cfg["outputs"]["query_meta_file"]

    ensure_exists(page_meta_file, "page meta file")
    ensure_exists(query_meta_file, "query meta file")

    cost_output = Path(args.cost_output)
    latency_output = Path(args.latency_output)
    cost_output.parent.mkdir(parents=True, exist_ok=True)
    latency_output.parent.mkdir(parents=True, exist_ok=True)

    page_meta = [r for r in read_jsonl(page_meta_file) if r.get("status") in ["ok", "existing"]]
    query_meta = [r for r in read_jsonl(query_meta_file) if r.get("status") in ["ok", "existing"]]

    if not page_meta:
        raise RuntimeError("No valid page embeddings found.")
    if not query_meta:
        raise RuntimeError("No valid query embeddings found.")

    pooled_pages = {}
    original_total_file_size = 0

    for r in page_meta:
        emb_rel = r.get("embedding_file") or r.get("embedding_path")
        if not emb_rel:
            continue
        arr_path = PROJECT_ROOT / emb_rel
        ensure_exists(arr_path, f"page embedding for {r.get('page_id')}")
        arr = np.load(arr_path)
        pooled_pages[r["page_id"]] = mean_pool(arr)
        original_total_file_size += file_size_bytes(arr_path)

    example_vec = next(iter(pooled_pages.values()))
    vector_dim = int(example_vec.shape[0])
    dtype_name = str(example_vec.dtype)
    itemsize = example_vec.dtype.itemsize

    page_count = len(pooled_pages)
    estimated_raw_bytes = page_count * vector_dim * itemsize

    latency_rows = []
    all_query_latencies = []

    page_ids = list(pooled_pages.keys())
    page_matrix = np.vstack([pooled_pages[pid] for pid in page_ids]).astype(np.float32)

    retrieval_start = time.time()

    for q in query_meta:
        qid = q["query_id"]
        q_emb_path = PROJECT_ROOT / (q.get("embedding_file") or q.get("embedding_path"))
        ensure_exists(q_emb_path, f"query embedding for {qid}")
        q_arr = np.load(q_emb_path)
        q_vec = mean_pool(q_arr)

        start = time.time()
        scores = page_matrix @ q_vec
        _ = np.argsort(-scores)[:10]
        total_elapsed = time.time() - start

        all_query_latencies.append(total_elapsed)
        latency_rows.append({
            "query_id": qid,
            "query_token_count": int(q_arr.shape[0]),
            "page_count_scored": page_count,
            "total_latency_ms": round(total_elapsed * 1000.0, 4),
        })

    retrieval_elapsed = time.time() - retrieval_start
    avg_query_latency_ms = float(np.mean(all_query_latencies) * 1000.0)

    rows = [
        ["metric", "value"],
        ["method", "single_vector"],
        ["page_count", page_count],
        ["query_count", len(query_meta)],
        ["vectors_per_page", 1],
        ["vector_dim", vector_dim],
        ["dtype", dtype_name],
        ["bytes_per_value", itemsize],
        ["original_embedding_file_size_mb", round(original_total_file_size / (1024 * 1024), 6)],
        ["estimated_raw_index_size_mb", round(estimated_raw_bytes / (1024 * 1024), 6)],
        ["avg_query_latency_ms", round(avg_query_latency_ms, 6)],
        ["total_retrieval_time_s", round(retrieval_elapsed, 6)],
    ]

    with cost_output.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(rows)

    with latency_output.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["query_id", "query_token_count", "page_count_scored", "total_latency_ms"]
        )
        writer.writeheader()
        writer.writerows(latency_rows)

    log(f"Wrote Single-vector cost stats to: {cost_output}")
    log(f"Wrote Single-vector latency details to: {latency_output}")


if __name__ == "__main__":
    main()
