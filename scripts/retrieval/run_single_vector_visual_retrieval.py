from pathlib import Path
import json
import argparse
import numpy as np
import torch
import faiss

from PIL import Image
from transformers import CLIPProcessor, CLIPModel

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DEFAULT_QUERY_PATH = PROJECT_ROOT / "data" / "metadata" / "queries.jsonl"
DEFAULT_IMAGE_DIR = PROJECT_ROOT / "data" / "images"
DEFAULT_OUT_PATH = PROJECT_ROOT / "results" / "baselines" / "single_vector_visual_run.tsv"

MODEL_NAME = "openai/clip-vit-base-patch32"
DEFAULT_TOP_K = 10
RUN_NAME = "single_vector_visual_baseline_v1"

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"


def ensure_exists(path: Path, name: str):
    if not path.exists():
        raise FileNotFoundError(f"{name} not found: {path}")


def load_jsonl(path: Path):
    items = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                items.append(json.loads(line))
    return items


def get_query_id(q):
    for key in ["query_id", "id"]:
        if key in q:
            return str(q[key])
    raise KeyError(f"Cannot find query id field: {q}")


def get_query_text(q):
    for key in ["query_text", "query", "text", "question"]:
        if key in q:
            return str(q[key])
    raise KeyError(f"Cannot find query text field: {q}")


def l2_normalize(x):
    norms = np.linalg.norm(x, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return x / norms


def load_page_images(image_dir: Path):
    image_paths = []
    for ext in ("*.png", "*.jpg", "*.jpeg"):
        image_paths.extend(image_dir.rglob(ext))
    image_paths = sorted(image_paths)

    items = []
    for p in image_paths:
        page_id = p.stem
        items.append({"page_id": page_id, "image_path": p})

    return items


def encode_images(model, processor, image_items, batch_size=8):
    all_embeddings = []
    total_batches = (len(image_items) + batch_size - 1) // batch_size

    for i in range(0, len(image_items), batch_size):
        batch = image_items[i:i + batch_size]
        images = [Image.open(x["image_path"]).convert("RGB") for x in batch]

        inputs = processor(images=images, return_tensors="pt", padding=True)
        pixel_values = inputs["pixel_values"].to(DEVICE)

        with torch.no_grad():
            vision_outputs = model.vision_model(pixel_values=pixel_values)
            pooled_output = vision_outputs.pooler_output
            feats = model.visual_projection(pooled_output)

        feats = feats.detach().cpu().numpy().astype("float32")
        all_embeddings.append(feats)

        print(f"Encoded image batch {i // batch_size + 1} / {total_batches}")

    return np.vstack(all_embeddings)


def encode_texts(model, processor, texts, batch_size=16):
    all_embeddings = []
    total_batches = (len(texts) + batch_size - 1) // batch_size

    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]

        inputs = processor(
            text=batch,
            return_tensors="pt",
            padding=True,
            truncation=True
        )

        input_ids = inputs["input_ids"].to(DEVICE)
        attention_mask = inputs["attention_mask"].to(DEVICE)

        with torch.no_grad():
            text_outputs = model.text_model(
                input_ids=input_ids,
                attention_mask=attention_mask
            )
            pooled_output = text_outputs.pooler_output
            feats = model.text_projection(pooled_output)

        feats = feats.detach().cpu().numpy().astype("float32")
        all_embeddings.append(feats)

        print(f"Encoded text batch {i // batch_size + 1} / {total_batches}")

    return np.vstack(all_embeddings)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--query_path", type=str, default=str(DEFAULT_QUERY_PATH))
    parser.add_argument("--image_dir", type=str, default=str(DEFAULT_IMAGE_DIR))
    parser.add_argument("--output", type=str, default=str(DEFAULT_OUT_PATH))
    parser.add_argument("--top_k", type=int, default=DEFAULT_TOP_K)
    return parser.parse_args()


def main():
    args = parse_args()

    query_path = Path(args.query_path)
    image_dir = Path(args.image_dir)
    out_path = Path(args.output)
    top_k = int(args.top_k)

    ensure_exists(query_path, "query file")
    ensure_exists(image_dir, "image directory")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Project root: {PROJECT_ROOT}")
    print(f"Query path: {query_path}")
    print(f"Image dir: {image_dir}")
    print(f"Output path: {out_path}")
    print(f"Using device: {DEVICE}")
    print(f"Loading model: {MODEL_NAME}")

    queries = load_jsonl(query_path)
    image_items = load_page_images(image_dir)

    top_k = min(top_k, len(image_items))

    print(f"Loaded {len(queries)} queries")
    print(f"Loaded {len(image_items)} page images")
    print(f"TOP_K = {top_k}")

    if len(image_items) == 0:
        raise ValueError(f"No images found under: {image_dir}")

    model = CLIPModel.from_pretrained(MODEL_NAME).to(DEVICE)
    processor = CLIPProcessor.from_pretrained(MODEL_NAME)
    model.eval()

    page_ids = [x["page_id"] for x in image_items]
    image_emb = encode_images(model, processor, image_items)
    image_emb = l2_normalize(image_emb)

    dim = image_emb.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(image_emb)

    query_ids = [get_query_id(q) for q in queries]
    query_texts = [get_query_text(q) for q in queries]

    query_emb = encode_texts(model, processor, query_texts)
    query_emb = l2_normalize(query_emb)

    scores, indices = index.search(query_emb, top_k)

    with out_path.open("w", encoding="utf-8") as out_f:
        for i, qid in enumerate(query_ids):
            for rank, (score, idx) in enumerate(zip(scores[i], indices[i]), start=1):
                page_id = page_ids[idx]
                out_f.write(f"{qid}\tQ0\t{page_id}\t{rank}\t{float(score):.6f}\t{RUN_NAME}\n")

    print(f"Wrote single-vector visual run to: {out_path}")


if __name__ == "__main__":
    main()
