"""Extract ColPali query token multi-vector embeddings for Full MV retrieval.

Drop-in encoder replacement for run_full_multivector_query_embeddings.py (CLIP):
same queries.jsonl reading, meta schema, resume logic, and --overwrite. ONLY the
model-load + encode step differs.

IMPORTANT (query-side alignment):
  Queries are encoded with processor.process_queries(...) -- NOT a bare tokenizer.
  For ColPali v1.3 this applies the model's designed query treatment:
    <bos> + query text tokens + 10 x "<pad>" query-augmentation tokens.
  (query_prefix is intentionally "" in v1.3; the natural-language instruction lives on
  the IMAGE side: "<image><bos>Describe the image.". The 10 pad tokens are the ColPali
  "query augmentation" that late interaction relies on.) Bypassing process_queries would
  drop the augmentation buffer and yield unfairly low scores.

Contract (matches the page script):
  - no extra L2 normalization (config model.normalize_embeddings=false; store raw vectors)
  - query dim MUST equal page dim (== 128); asserted against the page meta, hard error otherwise.
"""
from pathlib import Path
import argparse
import json
import os
import time
from datetime import datetime

if os.environ.get("HF_ENDPOINT", "").endswith("hf-mirror.com"):
    os.environ["HF_ENDPOINT"] = "https://huggingface.co"
os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")

import numpy as np
import torch
import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def log(msg, logs=None):
    line = f"[{now()}] {msg}"
    print(line, flush=True)
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


def load_colpali(model_name: str, model_type: str, device: str):
    if model_type == "colqwen2":
        from colpali_engine.models import ColQwen2, ColQwen2Processor
        model = ColQwen2.from_pretrained(model_name, torch_dtype=torch.bfloat16, device_map=device).eval()
        processor = ColQwen2Processor.from_pretrained(model_name)
    else:
        from colpali_engine.models import ColPali, ColPaliProcessor
        model = ColPali.from_pretrained(model_name, torch_dtype=torch.bfloat16, device_map=device).eval()
        processor = ColPaliProcessor.from_pretrained(model_name)
    return model, processor


def encode_query_tokens(model, processor, text: str, normalize: bool):
    """Return [N_query_tokens, dim] float32 using ColPali's process_queries path."""
    batch = processor.process_queries([text]).to(model.device)
    with torch.no_grad():
        emb = model(**batch)  # [1, N_qtok, dim]
    arr = emb[0].to(torch.float32).cpu().numpy().astype(np.float32)
    if normalize:
        arr = arr / (np.linalg.norm(arr, axis=-1, keepdims=True) + 1e-12)
    return arr


def get_page_dim(page_meta_file: Path):
    """Read the page embedding dim from the page meta (for the dim-match assertion)."""
    if not page_meta_file.exists():
        return None
    for r in read_jsonl(page_meta_file):
        if r.get("status") in ("ok", "existing") and "dim" in r:
            return int(r["dim"])
    return None


def write_jsonl(path: Path, rows):
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def main():
    parser = argparse.ArgumentParser(description="Extract ColPali query embeddings for Full MV retrieval.")
    parser.add_argument("--config", type=str, default=str(PROJECT_ROOT / "configs" / "colpali_multivector.yaml"))
    parser.add_argument("--subset-only", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    logs = []
    cfg = load_yaml(Path(args.config))

    query_file = PROJECT_ROOT / cfg["data"]["query_file"]
    model_name = cfg["model"]["name"]
    model_type = str(cfg["model"].get("type", "colpali")).strip().lower()
    device = cfg["model"].get("device", "mps")
    normalize_embeddings = bool(cfg["model"].get("normalize_embeddings", False))

    query_save_dir = PROJECT_ROOT / cfg["query_embedding"]["save_dir"]
    query_meta_file = PROJECT_ROOT / cfg["outputs"]["query_meta_file"]
    page_meta_file = PROJECT_ROOT / cfg["outputs"]["page_meta_file"]

    ensure_exists(query_file, "query file")
    ensure_dir(query_save_dir)
    ensure_dir(query_meta_file.parent)

    if device == "mps" and not torch.backends.mps.is_available():
        log("MPS not available, fallback to cpu", logs)
        device = "cpu"
    if device == "cuda" and not torch.cuda.is_available():
        log("CUDA not available, fallback to cpu", logs)
        device = "cpu"

    # page dim for the hard dim-match assertion
    page_dim = get_page_dim(page_meta_file)
    if page_dim is None:
        log(f"WARNING: could not read page dim from {page_meta_file}; "
            f"run the page script first. Proceeding without cross-check.", logs)
    else:
        log(f"Page dim (from page meta) = {page_dim}", logs)

    log(f"Loading queries from: {query_file}", logs)
    queries = read_jsonl(query_file)
    log(f"Loaded queries: {len(queries)}", logs)

    if args.subset_only:
        log("Subset mode ON, but all queries will be encoded for stability "
            "(retrieval filters to the subset qrels anyway).", logs)
    else:
        log("Subset mode OFF, using all queries.", logs)

    log(f"Loading model: {model_name} (type={model_type})  normalize_embeddings={normalize_embeddings}", logs)
    model, processor = load_colpali(model_name, model_type, device)
    log(f"Model loaded on device: {device}", logs)

    meta_rows = []
    printed = 0
    start_all = time.time()

    for idx, q in enumerate(queries, start=1):
        qid = str(q.get("query_id", "")).strip()
        text = str(q.get("query_text", "")).strip()

        if not qid or not text:
            continue

        out_path = query_save_dir / f"{qid}.npy"

        if out_path.exists() and not args.overwrite:
            arr = np.load(out_path)
            meta_rows.append({
                "query_id": qid,
                "query_text": text,
                "embedding_file": str(out_path.relative_to(PROJECT_ROOT)),
                "status": "existing",
                "num_tokens": int(arr.shape[0]),
                "dim": int(arr.shape[1]),
                "normalized": bool(normalize_embeddings),
            })
            log(f"[{idx}/{len(queries)}] existing: {qid}", logs)
            continue

        try:
            arr = encode_query_tokens(model, processor, text, normalize=normalize_embeddings)
            q_dim = int(arr.shape[1])

            # HARD dim-match assertion: query dim must equal page dim (== 128).
            if page_dim is not None and q_dim != page_dim:
                raise ValueError(
                    f"DIM MISMATCH: query '{qid}' dim={q_dim} != page dim={page_dim}. "
                    f"Page and query embeddings must share the same dim for MaxSim scoring."
                )

            np.save(out_path, arr)
            meta_rows.append({
                "query_id": qid,
                "query_text": text,
                "embedding_file": str(out_path.relative_to(PROJECT_ROOT)),
                "status": "ok",
                "num_tokens": int(arr.shape[0]),
                "dim": q_dim,
                "normalized": bool(normalize_embeddings),
            })
            log(f"[{idx}/{len(queries)}] ok: {qid} shape={arr.shape}", logs)

            if printed < 3:
                word_count = len(text.split())
                log(f"    [sample {printed+1}] {qid}: words={word_count} -> tokens={arr.shape[0]} "
                    f"(<bos> + {word_count}~ content + 10 <pad> augmentation), dim={q_dim}", logs)
                printed += 1

        except Exception as e:
            meta_rows.append({
                "query_id": qid,
                "query_text": text,
                "embedding_file": str(out_path.relative_to(PROJECT_ROOT)),
                "status": "error",
                "error": str(e),
            })
            log(f"[{idx}/{len(queries)}] error: {qid} -> {e}", logs)

    write_jsonl(query_meta_file, meta_rows)
    elapsed = time.time() - start_all

    from collections import Counter
    counts = Counter(r["status"] for r in meta_rows)
    ok_rows = [r for r in meta_rows if r["status"] in ("ok", "existing")]
    if ok_rows:
        tok_counts = [r["num_tokens"] for r in ok_rows]
        dims = sorted(set(r["dim"] for r in ok_rows))
        log(f"Query token count (min/mean/max) = "
            f"{min(tok_counts)}/{sum(tok_counts)/len(tok_counts):.1f}/{max(tok_counts)}", logs)
        log(f"Query dims seen = {dims} (page dim = {page_dim})", logs)
    log(f"Status summary: {dict(counts)}", logs)
    log(f"Wrote query meta to: {query_meta_file}", logs)
    log(f"Done in {elapsed:.2f}s", logs)


if __name__ == "__main__":
    main()
