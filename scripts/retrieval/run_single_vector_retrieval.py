from pathlib import Path
import argparse
import json
from datetime import datetime
from collections import defaultdict

import numpy as np
import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def log(msg):
    print(f"[{now()}] {msg}")


def ensure_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)


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


def load_qrels(qrels_path: Path):
    qrels = defaultdict(dict)
    with qrels_path.open("r", encoding="utf-8") as f:
        first = True
        for line in f:
            parts = line.strip().split("\t")
            if len(parts) < 3:
                continue

            if first and parts[0] == "query_id":
                first = False
                continue
            first = False

            qid = parts[0].strip()
            target_id = parts[1].strip()
            rel = parts[2].strip()
            try:
                rel = int(rel)
            except Exception:
                continue
            qrels[qid][target_id] = rel
    return qrels


def mean_pool(arr):
    if arr.ndim != 2:
        raise ValueError(f"Expected 2D array, got shape={arr.shape}")
    v = arr.mean(axis=0)
    norm = np.linalg.norm(v)
    if norm > 0:
        v = v / norm
    return v.astype(np.float32)


def main():
    parser = argparse.ArgumentParser(description="Run single-vector retrieval using mean pooled projected embeddings.")
    parser.add_argument("--config", type=str, default=str(PROJECT_ROOT / "configs" / "full_multivector.yaml"))
    parser.add_argument("--output-run", type=str, default=str(PROJECT_ROOT / "results" / "single_vector" / "single_vector_run.tsv"))
    parser.add_argument("--topk", type=int, default=10)
    args = parser.parse_args()

    cfg = load_yaml(Path(args.config))

    page_meta_file = PROJECT_ROOT / cfg["outputs"]["page_meta_file"]
    query_meta_file = PROJECT_ROOT / cfg["outputs"]["query_meta_file"]
    qrels_file = PROJECT_ROOT / cfg["data"]["qrels_file"]
    run_file = Path(args.output_run)

    ensure_exists(page_meta_file, "page meta file")
    ensure_exists(query_meta_file, "query meta file")
    ensure_exists(qrels_file, "qrels file")
    ensure_dir(run_file.parent)

    page_meta = [r for r in read_jsonl(page_meta_file) if r.get("status") in ["ok", "existing"]]
    query_meta = [r for r in read_jsonl(query_meta_file) if r.get("status") in ["ok", "existing"]]
    qrels = load_qrels(qrels_file)

    valid_qids = set(qrels.keys())
    query_meta = [r for r in query_meta if r["query_id"] in valid_qids]

    log(f"Single-vector mode: pages={len(page_meta)}, queries={len(query_meta)}")

    page_vecs = []
    page_ids = []
    for r in page_meta:
        emb_path = PROJECT_ROOT / r["embedding_file"]
        if not emb_path.exists():
            continue
        arr = np.load(emb_path)
        vec = mean_pool(arr)
        page_vecs.append(vec)
        page_ids.append(r["page_id"])

    if not page_vecs:
        raise RuntimeError("No page vectors loaded.")

    page_mat = np.vstack(page_vecs).astype(np.float32)

    query_vecs = []
    query_ids = []
    for r in query_meta:
        emb_path = PROJECT_ROOT / r["embedding_file"]
        if not emb_path.exists():
            continue
        arr = np.load(emb_path)
        vec = mean_pool(arr)
        query_vecs.append(vec)
        query_ids.append(r["query_id"])

    if not query_vecs:
        raise RuntimeError("No query vectors loaded.")

    query_mat = np.vstack(query_vecs).astype(np.float32)

    scores = query_mat @ page_mat.T

    with run_file.open("w", encoding="utf-8") as f:
        for i, qid in enumerate(query_ids):
            row_scores = scores[i]
            top_idx = np.argsort(-row_scores)[:args.topk]
            for rank, j in enumerate(top_idx, start=1):
                f.write(f"{qid}\tQ0\t{page_ids[j]}\t{rank}\t{float(row_scores[j]):.6f}\tsingle_vector_meanpool\n")

    log(f"Wrote single-vector run to: {run_file}")


if __name__ == "__main__":
    main()
