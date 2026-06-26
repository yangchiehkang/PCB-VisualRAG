from pathlib import Path
import json
import argparse
from rank_bm25 import BM25Okapi

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DEFAULT_CORPUS_PATH = PROJECT_ROOT / "data" / "metadata" / "ocr_corpus.jsonl"
DEFAULT_QUERY_PATH = PROJECT_ROOT / "data" / "metadata" / "queries.jsonl"
DEFAULT_OUT_PATH = PROJECT_ROOT / "results" / "baselines" / "bm25_run.tsv"

DEFAULT_TOP_K = 10
RUN_NAME = "bm25_baseline_v1"


def tokenize(text: str):
    return text.lower().split()


def ensure_exists(path: Path, name: str):
    if not path.exists():
        raise FileNotFoundError(f"{name} not found: {path}")


def load_jsonl(path: Path):
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def get_query_id(q):
    for key in ["query_id", "id"]:
        if key in q:
            return q[key]
    raise KeyError(f"Cannot find query id field in query record: {q}")


def get_query_text(q):
    for key in ["query_text", "query", "text", "question"]:
        if key in q:
            return q[key]
    raise KeyError(f"Cannot find query text field in query record: {q}")


def get_doc_id(doc):
    for key in ["page_id", "doc_id", "id"]:
        if key in doc:
            return doc[key]
    raise KeyError(f"Cannot find document id field in corpus record: {doc}")


def get_doc_text(doc):
    for key in ["text", "ocr_text", "content"]:
        if key in doc:
            return doc[key]
    raise KeyError(f"Cannot find text field in corpus record: {doc}")


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

    print(f"Loaded {len(docs)} documents from {corpus_path}")
    print(f"Loaded {len(queries)} queries from {query_path}")
    print(f"TOP_K = {top_k}")
    print(f"Output path = {out_path}")

    tokenized_corpus = [tokenize(get_doc_text(doc)) for doc in docs]
    bm25 = BM25Okapi(tokenized_corpus)

    with out_path.open("w", encoding="utf-8") as out_f:
        for q in queries:
            qid = str(get_query_id(q))
            qtext = get_query_text(q)
            scores = bm25.get_scores(tokenize(qtext))

            scored = []
            for doc, score in zip(docs, scores):
                scored.append((str(get_doc_id(doc)), float(score)))

            scored.sort(key=lambda x: x[1], reverse=True)

            for rank, (doc_id, score) in enumerate(scored[:top_k], start=1):
                out_f.write(f"{qid}\tQ0\t{doc_id}\t{rank}\t{score:.6f}\t{RUN_NAME}\n")

    print(f"Wrote BM25 run to: {out_path}")


if __name__ == "__main__":
    main()
