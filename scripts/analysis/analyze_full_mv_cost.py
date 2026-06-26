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


def cosine_sum_maxsim(query_tokens, page_tokens):
    sim = query_tokens @ page_tokens.T
    max_per_q = sim.max(axis=1)
    return float(max_per_q.sum())


def file_size_bytes(path: Path):
    return path.stat().st_size


def main():
    parser = argparse.ArgumentParser(description="Analyze Full MV cost.")
    parser.add_argument("--config", type=str, default=str(PROJECT_ROOT / "configs" / "full_multivector.yaml"))
    parser.add_argument("--cost-output", type=str, default=str(PROJECT_ROOT / "results" / "analysis" / "full_mv_cost_stats.csv"))
    parser.add_argument("--latency-output", type=str, default=str(PROJECT_ROOT / "results" / "analysis" / "query_latency_details_full_mv.csv"))
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

    page_arrays = {}
    page_token_counts = []
    page_dims = []
    total_file_size = 0
    total_elements = 0
    dtype_name = None
    itemsize = None

    for r in page_meta:
        emb_rel = r.get("embedding_file") or r.get("embedding_path")
        if not emb_rel:
            continue
        arr_path = PROJECT_ROOT / emb_rel
        ensure_exists(arr_path, f"page embedding for {r.get('page_id')}")
        arr = np.load(arr_path)
        page_arrays[r["page_id"]] = arr
        page_token_counts.append(arr.shape[0])
        page_dims.append(arr.shape[1])
        total_file_size += file_size_bytes(arr_path)
        total_elements += arr.size
        dtype_name = str(arr.dtype)
        itemsize = arr.dtype.itemsize

    avg_tokens_per_page = float(np.mean(page_token_counts))
    min_tokens_per_page = int(np.min(page_token_counts))
    max_tokens_per_page = int(np.max(page_token_counts))
    vector_dim = int(np.mean(page_dims))
    estimated_raw_bytes = int(total_elements * itemsize)

    latency_rows = []
    all_query_latencies = []
    all_query_score_times = []

    retrieval_start = time.time()

    for q in query_meta:
        qid = q["query_id"]
        q_emb_path = PROJECT_ROOT / (q.get("embedding_file") or q.get("embedding_path"))
        ensure_exists(q_emb_path, f"query embedding for {qid}")
        q_arr = np.load(q_emb_path)

        start = time.time()
        score_start = time.time()

        scores = []
        for page_id, page_arr in page_arrays.items():
            score = cosine_sum_maxsim(q_arr, page_arr)
            scores.append((page_id, score))

        score_elapsed = time.time() - score_start
        total_elapsed = time.time() - start

        all_query_score_times.append(score_elapsed)
        all_query_latencies.append(total_elapsed)

        latency_rows.append({
            "query_id": qid,
            "query_token_count": int(q_arr.shape[0]),
            "page_count_scored": len(page_arrays),
            "score_time_ms": round(score_elapsed * 1000.0, 4),
            "total_latency_ms": round(total_elapsed * 1000.0, 4),
        })

    retrieval_elapsed = time.time() - retrieval_start

    avg_query_latency_ms = float(np.mean(all_query_latencies) * 1000.0)
    avg_query_score_time_ms = float(np.mean(all_query_score_times) * 1000.0)

    rows = [
        ["metric", "value"],
        ["method", "full_multivector"],
        ["page_count", len(page_arrays)],
        ["query_count", len(query_meta)],
        ["vectors_per_page", round(avg_tokens_per_page, 4)],
        ["min_tokens_per_page", min_tokens_per_page],
        ["max_tokens_per_page", max_tokens_per_page],
        ["vector_dim", vector_dim],
        ["dtype", dtype_name],
        ["bytes_per_value", itemsize],
        ["embedding_file_size_mb", round(total_file_size / (1024 * 1024), 6)],
        ["estimated_raw_index_size_mb", round(estimated_raw_bytes / (1024 * 1024), 6)],
        ["avg_query_latency_ms", round(avg_query_latency_ms, 6)],
        ["avg_query_score_time_ms", round(avg_query_score_time_ms, 6)],
        ["total_retrieval_time_s", round(retrieval_elapsed, 6)],
    ]

    with cost_output.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(rows)

    with latency_output.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["query_id", "query_token_count", "page_count_scored", "score_time_ms", "total_latency_ms"]
        )
        writer.writeheader()
        writer.writerows(latency_rows)

    log(f"Wrote Full MV cost stats to: {cost_output}")
    log(f"Wrote Full MV latency details to: {latency_output}")


if __name__ == "__main__":
    main()
