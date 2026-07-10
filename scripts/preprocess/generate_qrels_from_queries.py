from pathlib import Path
import json
import csv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
INPUT_PATH = PROJECT_ROOT / "data" / "metadata" / "queries.jsonl"
OUTPUT_PATH = PROJECT_ROOT / "data" / "metadata" / "qrels.tsv"


def load_jsonl(path: Path):
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def main():
    if not INPUT_PATH.exists():
        raise FileNotFoundError(f"queries file not found: {INPUT_PATH}")

    queries = load_jsonl(INPUT_PATH)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    written = 0
    with OUTPUT_PATH.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerow(["query_id", "page_id", "relevance"])

        for q in queries:
            qid = q.get("query_id")
            gold_page_ids = q.get("gold_page_ids", [])

            if not qid or not isinstance(gold_page_ids, list):
                continue

            for pid in gold_page_ids:
                writer.writerow([qid, pid, 1])
                written += 1

    print(f"[INFO] Loaded queries: {len(queries)}")
    print(f"[INFO] Wrote qrels pairs: {written}")
    print(f"[INFO] Output: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
