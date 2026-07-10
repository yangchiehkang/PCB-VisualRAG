from pathlib import Path
import argparse
import csv
from collections import defaultdict


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def ensure_exists(path: Path, name: str):
    if not path.exists():
        raise FileNotFoundError(f"{name} not found: {path}")


def load_run(path: Path):
    run = defaultdict(list)
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) < 6:
                continue
            qid, _, docid, rank, score, tag = parts[:6]
            run[qid].append((docid, int(rank), float(score)))
    for qid in run:
        run[qid] = sorted(run[qid], key=lambda x: x[1])
    return run


def load_qrels(path: Path):
    qrels = defaultdict(dict)
    with path.open("r", encoding="utf-8") as f:
        lines = [ln.strip() for ln in f if ln.strip()]

    if not lines:
        return qrels

    first = lines[0].split("\t")
    has_header = "query_id" in [x.lower() for x in first]

    for line in lines[1:] if has_header else lines:
        parts = line.split("\t")
        if len(parts) < 3:
            parts = line.split()

        if len(parts) >= 4 and not has_header:
            qid, _, docid, rel = parts[:4]
        elif len(parts) >= 3:
            qid, docid, rel = parts[:3]
        else:
            continue

        try:
            qrels[qid][docid] = int(float(rel))
        except Exception:
            continue

    return qrels


def main():
    parser = argparse.ArgumentParser(description="Export top-k details for case analysis.")
    parser.add_argument("--single-run", type=str, default=str(PROJECT_ROOT / "results" / "single_vector" / "single_vector_run.tsv"))
    parser.add_argument("--full-run", type=str, default=str(PROJECT_ROOT / "results" / "full_multivector" / "full_mv_run.tsv"))
    parser.add_argument("--qrels", type=str, default=str(PROJECT_ROOT / "data" / "metadata" / "qrels.tsv"))
    parser.add_argument("--output", type=str, default=str(PROJECT_ROOT / "results" / "analysis" / "case_topk_details.csv"))
    parser.add_argument("--topk", type=int, default=10)
    args = parser.parse_args()

    single_run_path = Path(args.single_run)
    full_run_path = Path(args.full_run)
    qrels_path = Path(args.qrels)

    ensure_exists(single_run_path, "single-run file")
    ensure_exists(full_run_path, "full-run file")
    ensure_exists(qrels_path, "qrels file")

    single_run = load_run(single_run_path)
    full_run = load_run(full_run_path)
    qrels = load_qrels(qrels_path)

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)

    rows = [[
        "query_id", "method", "rank", "docid", "score", "is_relevant"
    ]]

    all_qids = sorted(set(qrels.keys()) | set(single_run.keys()) | set(full_run.keys()))
    for qid in all_qids:
        rel_docs = qrels.get(qid, {})

        for method_name, run in [("single_vector", single_run), ("full_multi_vector", full_run)]:
            for docid, rank, score in run.get(qid, [])[:args.topk]:
                is_rel = 1 if docid in rel_docs and rel_docs[docid] > 0 else 0
                rows.append([qid, method_name, rank, docid, score, is_rel])

    with output.open("w", encoding="utf-8", newline="") as out_f:
        writer = csv.writer(out_f)
        writer.writerows(rows)

    print(f"Wrote case top-k details: {output}")


if __name__ == "__main__":
    main()
