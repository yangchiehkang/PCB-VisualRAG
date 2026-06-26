from pathlib import Path
import json
import argparse
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DEFAULT_CORPUS_PATH = PROJECT_ROOT / "data" / "metadata" / "ocr_corpus.jsonl"
DEFAULT_QUERY_PATH = PROJECT_ROOT / "data" / "metadata" / "queries.jsonl"
DEFAULT_OUT_PATH = PROJECT_ROOT / "results" / "baselines" / "dense_text_run.tsv"

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
DEFAULT_TOP_K = 10
RUN_NAME = "dense_text_baseline_v1"


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


def get_page_id(doc):
    for key in ["page_id", "doc_id", "id"]:
        if key in doc:
            return str(doc[key])
    raise KeyError(f"Cannot find page/document id field: {doc}")


def get_page_text(doc):
    for key in ["text", "ocr_text", "content"]:
        if key in doc:
            return str(doc[key])
    raise KeyError(f"Cannot find page text field: {doc}")


def l2_normalize(x):
    norms = np.linalg.norm(x, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return x / norms


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus_path", type=str, default=str(DEFAULT_CORPUS_PATH))
    parser.add_argument("--query_path", type=str, default=str(DEFAULT_QUERY_PATH))
    parser.add_argument("--output", type=str, default=str(DEFAULT_OUT_PATH))
    parser.add_argument("--top_k", type=int, default=DEFAULT_TOP_K)
    return parser.parse_args()


def main():
    args = parse_args()

    corpus_path = Path(args.corpus_path)
    query_path = Path(args.query_path)
    out_path = Path(args.output)
    top_k = int(args.top_k)

    ensure_exists(corpus_path, "corpus file")
    ensure_exists(query_path, "query file")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    docs = load_jsonl(corpus_path)
    queries = load_jsonl(query_path)

    top_k = min(top_k, len(docs))

    print(f"Loaded {len(docs)} documents")
    print(f"Loaded {len(queries)} queries")
    print(f"TOP_K = {top_k}")
    print(f"Output path = {out_path}")
    print(f"Loading model: {MODEL_NAME}")

    model = SentenceTransformer(MODEL_NAME)

    page_ids = [get_page_id(doc) for doc in docs]
    page_texts = [get_page_text(doc) for doc in docs]

    print("Encoding page texts...")
    doc_emb = model.encode(
        page_texts,
        batch_size=32,
        show_progress_bar=True,
        convert_to_numpy=True
    ).astype("float32")

    doc_emb = l2_normalize(doc_emb)

    dim = doc_emb.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(doc_emb)

    print(f"Built FAISS index with {index.ntotal} vectors, dim={dim}")

    query_ids = [get_query_id(q) for q in queries]
    query_texts = [get_query_text(q) for q in queries]

    print("Encoding queries...")
    query_emb = model.encode(
        query_texts,
        batch_size=32,
        show_progress_bar=True,
        convert_to_numpy=True
    ).astype("float32")

    query_emb = l2_normalize(query_emb)

    scores, indices = index.search(query_emb, top_k)

    with out_path.open("w", encoding="utf-8") as out_f:
        for i, qid in enumerate(query_ids):
            for rank, (score, idx) in enumerate(zip(scores[i], indices[i]), start=1):
                doc_id = page_ids[idx]
                out_f.write(f"{qid}\tQ0\t{doc_id}\t{rank}\t{float(score):.6f}\t{RUN_NAME}\n")

    print(f"Wrote dense text run to: {out_path}")


if __name__ == "__main__":
    main()
