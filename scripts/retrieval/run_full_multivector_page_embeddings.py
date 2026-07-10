from pathlib import Path
import argparse
import json
import csv
import time
from datetime import datetime

import numpy as np
import torch
from PIL import Image
import yaml
from transformers import CLIPProcessor, CLIPModel


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
    image_path_str = str(row.get("image_path", "")).strip()
    image_name = str(row.get("image_name", "")).strip()
    file_name = str(row.get("file_name", "")).strip()

    candidates = []

    if image_path_str:
        candidates.append(project_root / image_path_str)
    if image_name:
        candidates.append(image_root / image_name)
    if file_name:
        candidates.append(image_root / file_name)

    for p in candidates:
        if p.exists():
            return p

    return candidates[0] if candidates else None


def get_projected_page_tokens(model, pixel_values, keep_cls=False, normalize=True):
    with torch.no_grad():
        vision_outputs = model.vision_model(pixel_values=pixel_values)
        hidden = vision_outputs.last_hidden_state

        if not keep_cls:
            hidden = hidden[:, 1:, :]

        projected = model.visual_projection(hidden)

        if normalize:
            projected = torch.nn.functional.normalize(projected, dim=-1)

    return projected[0].cpu().numpy().astype(np.float32)


def write_jsonl(path: Path, rows):
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def main():
    parser = argparse.ArgumentParser(description="Extract projected page embeddings for Full MV retrieval.")
    parser.add_argument("--config", type=str, default=str(PROJECT_ROOT / "configs" / "full_multivector.yaml"))
    parser.add_argument("--subset-only", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    cfg = load_yaml(Path(args.config))

    page_inventory_file = PROJECT_ROOT / cfg["data"]["page_inventory_file"]
    image_root = PROJECT_ROOT / cfg["data"]["image_root"]
    subset_file = PROJECT_ROOT / cfg["data"]["subset_file"]

    model_name = cfg["model"]["name"]
    device = cfg["model"].get("device", "cuda")
    normalize_embeddings = bool(cfg["model"].get("normalize_embeddings", True))

    keep_cls = bool(cfg["page_embedding"].get("keep_cls", False))
    save_dir = PROJECT_ROOT / cfg["page_embedding"]["save_dir"]
    page_meta_file = PROJECT_ROOT / cfg["outputs"]["page_meta_file"]

    ensure_exists(page_inventory_file, "page inventory file")
    ensure_exists(image_root, "image root")
    if args.subset_only:
        ensure_exists(subset_file, "subset file")

    ensure_dir(save_dir)
    ensure_dir(page_meta_file.parent)

    log("START projected page embedding extraction")
    log(f"Config: {args.config}")

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

    if device == "cuda" and not torch.cuda.is_available():
        log("CUDA not available, fallback to cpu")
        device = "cpu"

    log(f"Loading model: {model_name}")
    processor = CLIPProcessor.from_pretrained(model_name)
    model = CLIPModel.from_pretrained(model_name)
    model.eval()
    model.to(device)
    log(f"Model loaded on device: {device}")

    meta_rows = []
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
            })
            log(f"[{idx}/{len(selected_rows)}] existing: {page_id}")
            continue

        try:
            image = Image.open(image_path).convert("RGB")
            inputs = processor(images=image, return_tensors="pt")
            pixel_values = inputs["pixel_values"].to(device)

            arr = get_projected_page_tokens(
                model=model,
                pixel_values=pixel_values,
                keep_cls=keep_cls,
                normalize=normalize_embeddings
            )
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
            })
            log(f"[{idx}/{len(selected_rows)}] ok: {page_id} shape={arr.shape}")

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
    log(f"Wrote page meta to: {page_meta_file}")
    log(f"Done in {elapsed:.2f}s")


if __name__ == "__main__":
    main()
