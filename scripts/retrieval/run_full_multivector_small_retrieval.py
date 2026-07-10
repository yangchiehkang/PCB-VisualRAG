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


def log(msg, logs=None):
    line = f"[{now()}] {msg}"
    print(line)
    if logs is not None:
        logs.append(line)


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


def load_subset_page_ids(subset_file: Path):
    obj = json.loads(subset_file.read_text(encoding="utf-8"))
    return set(p["page_id"] for p in obj["pages"])


def load_doc_ids_from_page_ids(page_ids):
    return set(pid.split("_p")[0] for pid in page_ids if "_p" in pid)


def cosine_sum_maxsim(query_tokens, page_tokens):
    if query_tokens.shape[1] != page_tokens.shape[1]:
        raise ValueError(f"Embedding dim mismatch: query={query_tokens.shape}, page={page_tokens.shape}")
    sim = query_tokens @ page_tokens.T
    max_per_q = sim.max(axis=1)
    return float(max_per_q.sum())


def main():
    parser = argparse.ArgumentParser(description="Run small Full MV retrieval with late interaction.")
    parser.add_argument("--config", type=str, default=str(PROJECT_ROOT / "configs" / "full_multivector.yaml"))
    parser.add_argument("--subset-only", action="store_true")
    args = parser.parse_args()

    logs = []
    cfg = load_yaml(Path(args.config))

    page_meta_file = PROJECT_ROOT / cfg["outputs"]["page_meta_file"]
    query_meta_file = PROJECT_ROOT / cfg["outputs"]["query_meta_file"]
    qrels_file = PROJECT_ROOT / cfg["data"]["qrels_file"]
    subset_file = PROJECT_ROOT / cfg["data"]["subset_file"]
    run_file = PROJECT_ROOT / cfg["outputs"]["small_run_file"]

    topk = int(cfg["scoring"].get("topk", 10))
    ensure_exists(page_meta_file, "page meta file")
    ensure_exists(query_meta_file, "query meta file")
    ensure_exists(qrels_file, "qrels file")
    ensure_exists(subset_file, "subset file")
    ensure_dir(run_file.parent)

    page_meta = [r for r in read_jsonl(page_meta_file) if r.get("status") in ["ok", "existing"]]
    query_meta = [r for r in read_jsonl(query_meta_file) if r.get("status") in ["ok", "existing"]]
    qrels = load_qrels(qrels_file)

    subset_page_ids = load_subset_page_ids(subset_file)
    subset_doc_ids = load_doc_ids_from_page_ids(subset_page_ids)

    page_meta = [r for r in page_meta if r["page_id"] in subset_page_ids]

    filtered_queries = []
    for r in query_meta:
        qid = r["query_id"]
        rel_targets = qrels.get(qid, {})
        keep = False
        for target_id, rel in rel_targets.items():
            if rel <= 0:
                continue
            if target_id in subset_doc_ids or target_id in subset_page_ids:
                keep = True
                break
        if keep:
            filtered_queries.append(r)

    query_meta = filtered_queries

    log(f"Small retrieval mode: pages={len(page_meta)}, queries={len(query_meta)}", logs)

    page_cache = {}
    for r in page_meta:
        emb_path = PROJECT_ROOT / r["embedding_file"]
        if emb_path.exists():
            page_cache[r["page_id"]] = np.load(emb_path)

    query_cache = {}
    for r in query_meta:
        emb_path = PROJECT_ROOT / r["embedding_file"]
        if emb_path.exists():
            query_cache[r["query_id"]] = np.load(emb_path)

    with run_file.open("w", encoding="utf-8") as f:
        for qi, r in enumerate(query_meta, start=1):
            qid = r["query_id"]
            q_emb = query_cache[qid]

            scored = []
            for p in page_meta:
                pid = p["page_id"]
                p_emb = page_cache[pid]
                score = cosine_sum_maxsim(q_emb, p_emb)
                scored.append((pid, score))

            scored.sort(key=lambda x: x[1], reverse=True)

            for rank, (pid, score) in enumerate(scored[:topk], start=1):
                f.write(f"{qid}\tQ0\t{pid}\t{rank}\t{score:.6f}\tfull_mv_small_late_interaction\n")

            log(f"[{qi}/{len(query_meta)}] scored query: {qid}", logs)

    log(f"Wrote small run file to: {run_file}", logs)


if __name__ == "__main__":
    main()
