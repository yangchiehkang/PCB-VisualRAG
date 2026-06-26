from pathlib import Path
import argparse
import json
import time
from datetime import datetime

import numpy as np
import torch
import yaml
from transformers import CLIPProcessor, CLIPModel


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


def get_projected_text_tokens(model, processor, text, device="cpu", normalize=True):
    with torch.no_grad():
        inputs = processor(text=[text], return_tensors="pt", padding=True, truncation=True)
        input_ids = inputs["input_ids"].to(device)
        attention_mask = inputs["attention_mask"].to(device)

        text_outputs = model.text_model(
            input_ids=input_ids,
            attention_mask=attention_mask
        )
        hidden = text_outputs.last_hidden_state

        mask = attention_mask[0].bool()
        tokens = hidden[0][mask]

        projected = model.text_projection(tokens)

        if normalize:
            projected = torch.nn.functional.normalize(projected, dim=-1)

    return projected.cpu().numpy().astype(np.float32)


def write_jsonl(path: Path, rows):
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def main():
    parser = argparse.ArgumentParser(description="Extract projected query token embeddings for Full MV retrieval.")
    parser.add_argument("--config", type=str, default=str(PROJECT_ROOT / "configs" / "full_multivector.yaml"))
    parser.add_argument("--subset-only", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    logs = []
    cfg = load_yaml(Path(args.config))

    query_file = PROJECT_ROOT / cfg["data"]["query_file"]
    model_name = cfg["model"]["name"]
    device = cfg["model"].get("device", "cuda")
    normalize_embeddings = bool(cfg["model"].get("normalize_embeddings", True))

    query_save_dir = PROJECT_ROOT / cfg["query_embedding"]["save_dir"]
    query_meta_file = PROJECT_ROOT / cfg["outputs"]["query_meta_file"]

    ensure_exists(query_file, "query file")
    ensure_dir(query_save_dir)
    ensure_dir(query_meta_file.parent)

    if device == "cuda" and not torch.cuda.is_available():
        log("CUDA not available, fallback to cpu", logs)
        device = "cpu"

    log(f"Loading queries from: {query_file}", logs)
    queries = read_jsonl(query_file)
    log(f"Loaded queries: {len(queries)}", logs)

    if args.subset_only:
        log("Subset mode ON, but all queries will be encoded for stability.", logs)
    else:
        log("Subset mode OFF, using all queries.", logs)

    log(f"Loading model: {model_name}", logs)
    processor = CLIPProcessor.from_pretrained(model_name)
    model = CLIPModel.from_pretrained(model_name)
    model.eval()
    model.to(device)
    log(f"Model loaded on device: {device}", logs)

    meta_rows = []
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
            })
            log(f"[{idx}/{len(queries)}] existing: {qid}", logs)
            continue

        try:
            arr = get_projected_text_tokens(
                model=model,
                processor=processor,
                text=text,
                device=device,
                normalize=normalize_embeddings
            )
            np.save(out_path, arr)

            meta_rows.append({
                "query_id": qid,
                "query_text": text,
                "embedding_file": str(out_path.relative_to(PROJECT_ROOT)),
                "status": "ok",
                "num_tokens": int(arr.shape[0]),
                "dim": int(arr.shape[1]),
            })
            log(f"[{idx}/{len(queries)}] ok: {qid} shape={arr.shape}", logs)

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
    log(f"Wrote query meta to: {query_meta_file}", logs)
    log(f"Done in {elapsed:.2f}s", logs)


if __name__ == "__main__":
    main()
