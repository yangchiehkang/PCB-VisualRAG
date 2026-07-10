from pathlib import Path
from collections import defaultdict
import csv

PROJECT_ROOT = Path(__file__).resolve().parents[2]

CANDIDATE_DIR = PROJECT_ROOT / "artifacts" / "rerank_cache" / "week7_topN"
OUT_DIR = PROJECT_ROOT / "results" / "week7" / "c2f_fixed_N"

FILES = [
    ("bm25", 10, CANDIDATE_DIR / "candidates_bm25_N10.tsv"),
    ("bm25", 20, CANDIDATE_DIR / "candidates_bm25_N20.tsv"),
    ("bm25", 50, CANDIDATE_DIR / "candidates_bm25_N50.tsv"),
    ("bm25", 100, CANDIDATE_DIR / "candidates_bm25_N100.tsv"),
    ("visual", 10, CANDIDATE_DIR / "candidates_visual_N10.tsv"),
    ("visual", 20, CANDIDATE_DIR / "candidates_visual_N20.tsv"),
    ("visual", 50, CANDIDATE_DIR / "candidates_visual_N50.tsv"),
    ("visual", 100, CANDIDATE_DIR / "candidates_visual_N100.tsv"),
]


def count_candidates(path: Path):
    counts = defaultdict(set)

    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            parts = line.split("\t")
            if len(parts) < 6:
                parts = line.split()

            qid = parts[0]
            doc_id = parts[2]
            counts[qid].add(doc_id)

    values = [len(v) for v in counts.values()]
    return {
        "num_queries": len(values),
        "avg_candidates_per_query": sum(values) / len(values),
        "min_candidates_per_query": min(values),
        "max_candidates_per_query": max(values),
    }


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    rows = []

    for method, n, path in FILES:
        if not path.exists():
            raise FileNotFoundError(f"Missing file: {path}")

        stats = count_candidates(path)

        rows.append({
            "method": method,
            "N": n,
            "expected_candidates_per_query": n,
            "num_queries": stats["num_queries"],
            "avg_candidates_per_query": stats["avg_candidates_per_query"],
            "min_candidates_per_query": stats["min_candidates_per_query"],
            "max_candidates_per_query": stats["max_candidates_per_query"],
        })

    out_path = OUT_DIR / "actual_candidates_check.csv"

    with out_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "method",
                "N",
                "expected_candidates_per_query",
                "num_queries",
                "avg_candidates_per_query",
                "min_candidates_per_query",
                "max_candidates_per_query",
            ]
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote: {out_path}")

    for row in rows:
        print(
            row["method"],
            "N=",
            row["N"],
            "avg=",
            row["avg_candidates_per_query"],
            "min=",
            row["min_candidates_per_query"],
            "max=",
            row["max_candidates_per_query"],
        )


if __name__ == "__main__":
    main()
