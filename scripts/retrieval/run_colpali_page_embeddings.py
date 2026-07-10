"""Extract ColPali patch-level multi-vector page embeddings for Full MV retrieval.

Drop-in encoder replacement for run_full_multivector_page_embeddings.py (CLIP):
same page_inventory reading, subset selection, image-path resolution, meta schema,
and resume logic. ONLY the model-load + encode step differs.

ColPali contract note (differs from the CLIP script on purpose):
  ColPali's native late interaction uses the model's RAW output token vectors -- each
  token norm encodes learned importance. We therefore do NOT apply extra L2 normalization
  (config: model.normalize_embeddings=false). The scoring stays q @ p.T sum-maxsim, which
  is ColPali-native dot-product MaxSim. (Empirically colpali-engine already unit-normalizes
  its output internally, so the stored vectors are ~unit-norm regardless.)
"""
from pathlib import Path
import argparse
import json
import csv
import os
import time
from datetime import datetime

# The environment ships a broken HF mirror (hf-mirror.com -> SSL EOF); huggingface.co works
# through the configured proxy. Fix it defensively so the script is reproducible.
if os.environ.get("HF_ENDPOINT", "").endswith("hf-mirror.com"):
    os.environ["HF_ENDPOINT"] = "https://huggingface.co"
os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")

import numpy as np
import torch
from PIL import Image
import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def log(msg):
    print(f"[{now()}] {msg}", flush=True)


def ensure_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)


def ensure_exists(path: Path, name: str):
    if not path.exists():
        raise FileNotFoundError(f"{name} not found: {path}")


def load_yaml(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def read_page_inventory(csv_path: Path):
    rows = []
    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def load_subset_page_ids(subset_file: Path):
    obj = json.loads(subset_file.read_text(encoding="utf-8"))
    return set(p["page_id"] for p in obj["pages"])


def select_rows(page_rows, subset_page_ids=None):
    selected = []
    for row in page_rows:
        page_id = str(row.get("page_id", "")).strip()
        if not page_id:
            continue

        include_flag = str(row.get("include_flag", "1")).strip().lower()
        if include_flag in ["0", "false", "no"]:
            continue

        if subset_page_ids is not None and page_id not in subset_page_ids:
            continue

        selected.append(row)
    return selected


def resolve_image_path(project_root: Path, image_root: Path, row: dict):
    """Resolve the on-disk image path.

    Extends the CLIP script's resolver with the nested layout used on this machine:
    data/images/{doc_id}/{image_name}. (The inventory's image_path column holds stale
    Windows E:\\ absolute paths, and the flat image_root/image_name does not exist here.)
    """
    image_path_str = str(row.get("image_path", "")).strip()
    image_name = str(row.get("image_name", "")).strip()
    file_name = str(row.get("file_name", "")).strip()
    doc_id = str(row.get("doc_id", "")).strip()

    candidates = []

    if image_path_str:
        candidates.append(project_root / image_path_str)
    # nested layout: data/images/<doc_id>/<image_name>
    if doc_id and image_name:
        candidates.append(image_root / doc_id / image_name)
    # flat layout: data/images/<image_name>
    if image_name:
        candidates.append(image_root / image_name)
    if file_name:
        candidates.append(image_root / file_name)

    for p in candidates:
        if p.exists():
            return p

    return candidates[0] if candidates else None


def load_colpali(model_name: str, model_type: str, device: str):
    """Load a colpali-engine model + processor by config type."""
    if model_type == "colqwen2":
        from colpali_engine.models import ColQwen2, ColQwen2Processor
        model = ColQwen2.from_pretrained(model_name, torch_dtype=torch.bfloat16, device_map=device).eval()
        processor = ColQwen2Processor.from_pretrained(model_name)
    else:  # default: colpali
        from colpali_engine.models import ColPali, ColPaliProcessor
        model = ColPali.from_pretrained(model_name, torch_dtype=torch.bfloat16, device_map=device).eval()
        processor = ColPaliProcessor.from_pretrained(model_name)
    return model, processor


def encode_page_tokens(model, processor, image: Image.Image, normalize: bool):
    """Return [N_patch_tokens, dim] float32 patch multi-vector for one page image."""
    batch = processor.process_images([image]).to(model.device)
    with torch.no_grad():
        emb = model(**batch)  # [1, N_patch, dim]
    arr = emb[0].to(torch.float32).cpu().numpy().astype(np.float32)
    if normalize:
        arr = arr / (np.linalg.norm(arr, axis=-1, keepdims=True) + 1e-12)
    return arr


def write_jsonl(path: Path, rows):
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def main():
    parser = argparse.ArgumentParser(description="Extract ColPali page embeddings for Full MV retrieval.")
    parser.add_argument("--config", type=str, default=str(PROJECT_ROOT / "configs" / "colpali_multivector.yaml"))
    parser.add_argument("--subset-only", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    cfg = load_yaml(Path(args.config))

    page_inventory_file = PROJECT_ROOT / cfg["data"]["page_inventory_file"]
    image_root = PROJECT_ROOT / cfg["data"]["image_root"]
    subset_file = PROJECT_ROOT / cfg["data"]["subset_file"]

    model_name = cfg["model"]["name"]
    model_type = str(cfg["model"].get("type", "colpali")).strip().lower()
    device = cfg["model"].get("device", "mps")
    normalize_embeddings = bool(cfg["model"].get("normalize_embeddings", False))

    save_dir = PROJECT_ROOT / cfg["page_embedding"]["save_dir"]
    page_meta_file = PROJECT_ROOT / cfg["outputs"]["page_meta_file"]

    ensure_exists(page_inventory_file, "page inventory file")
    ensure_exists(image_root, "image root")
    if args.subset_only:
        ensure_exists(subset_file, "subset file")

    ensure_dir(save_dir)
    ensure_dir(page_meta_file.parent)

    log("START ColPali page embedding extraction")
    log(f"Config: {args.config}")
    log(f"Model: {model_name} (type={model_type})  normalize_embeddings={normalize_embeddings}")

    page_rows = read_page_inventory(page_inventory_file)
    log(f"Loaded page inventory rows: {len(page_rows)}")

    subset_page_ids = None
    if args.subset_only:
        subset_page_ids = load_subset_page_ids(subset_file)
        log(f"Subset mode ON, subset pages: {len(subset_page_ids)}")
    else:
        log("Subset mode OFF")

    selected_rows = select_rows(page_rows, subset_page_ids=subset_page_ids)
    log(f"Selected rows to process: {len(selected_rows)}")

    # device resolution (mps preferred on Apple Silicon; graceful fallback to cpu)
    if device == "mps" and not torch.backends.mps.is_available():
        log("MPS not available, fallback to cpu")
        device = "cpu"
    if device == "cuda" and not torch.cuda.is_available():
        log("CUDA not available, fallback to cpu")
        device = "cpu"

    log(f"Loading model on device: {device}")
    model, processor = load_colpali(model_name, model_type, device)
    log("Model loaded")

    meta_rows = []
    printed = 0
    start_all = time.time()

    for idx, row in enumerate(selected_rows, start=1):
        page_id = str(row.get("page_id", "")).strip()
        doc_id = str(row.get("doc_id", "")).strip()
        page_num = str(row.get("page_num", "")).strip()
        page_type = str(row.get("page_type", "unknown")).strip() or "unknown"

        image_path = resolve_image_path(PROJECT_ROOT, image_root, row)
        out_path = save_dir / f"{page_id}.npy"

        if image_path is None or not image_path.exists():
            meta_rows.append({
                "page_id": page_id,
                "doc_id": doc_id,
                "page_num": page_num,
                "page_type": page_type,
                "image_path": str(image_path) if image_path else "",
                "embedding_file": str(out_path.relative_to(PROJECT_ROOT)),
                "status": "missing_image",
            })
            log(f"[{idx}/{len(selected_rows)}] missing image: {page_id}")
            continue

        if out_path.exists() and not args.overwrite:
            arr = np.load(out_path)
            meta_rows.append({
                "page_id": page_id,
                "doc_id": doc_id,
                "page_num": page_num,
                "page_type": page_type,
                "image_path": str(image_path.relative_to(PROJECT_ROOT)),
                "embedding_file": str(out_path.relative_to(PROJECT_ROOT)),
                "status": "existing",
                "num_tokens": int(arr.shape[0]),
                "dim": int(arr.shape[1]),
                "normalized": bool(normalize_embeddings),
            })
            log(f"[{idx}/{len(selected_rows)}] existing: {page_id}")
            continue

        try:
            image = Image.open(image_path).convert("RGB")
            arr = encode_page_tokens(model, processor, image, normalize=normalize_embeddings)
            np.save(out_path, arr)

            meta_rows.append({
                "page_id": page_id,
                "doc_id": doc_id,
                "page_num": page_num,
                "page_type": page_type,
                "image_path": str(image_path.relative_to(PROJECT_ROOT)),
                "embedding_file": str(out_path.relative_to(PROJECT_ROOT)),
                "status": "ok",
                "num_tokens": int(arr.shape[0]),
                "dim": int(arr.shape[1]),
                "normalized": bool(normalize_embeddings),
            })
            log(f"[{idx}/{len(selected_rows)}] ok: {page_id} shape={arr.shape}")
            if printed < 3:
                tn = np.linalg.norm(arr, axis=1)
                log(f"    [sample {printed+1}] {page_id}: shape={arr.shape} "
                    f"token_norm(mean/min/max)={tn.mean():.3f}/{tn.min():.3f}/{tn.max():.3f}")
                printed += 1

        except Exception as e:
            meta_rows.append({
                "page_id": page_id,
                "doc_id": doc_id,
                "page_num": page_num,
                "page_type": page_type,
                "image_path": str(image_path.relative_to(PROJECT_ROOT)) if image_path.exists() else str(image_path),
                "embedding_file": str(out_path.relative_to(PROJECT_ROOT)),
                "status": "error",
                "error": str(e),
            })
            log(f"[{idx}/{len(selected_rows)}] error: {page_id} -> {e}")

    write_jsonl(page_meta_file, meta_rows)
    elapsed = time.time() - start_all

    # status summary
    from collections import Counter
    counts = Counter(r["status"] for r in meta_rows)
    log(f"Wrote page meta to: {page_meta_file}")
    log(f"Status summary: {dict(counts)}")
    ok_dims = set((r["num_tokens"], r["dim"]) for r in meta_rows if r["status"] in ("ok", "existing"))
    log(f"(num_tokens, dim) seen among ok/existing: {sorted(ok_dims)[:5]}{' ...' if len(ok_dims) > 5 else ''}")
    log(f"Done in {elapsed:.2f}s")


if __name__ == "__main__":
    main()
