from pathlib import Path
import argparse
import csv
import json
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


def load_queries_jsonl(path: Path):
    data = {}
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            qid = obj.get("query_id") or obj.get("qid")
            if qid:
                data[qid] = obj
    return data


def first_relevant_rank(results, rel_docs):
    for docid, rank, score in results:
        if docid in rel_docs and rel_docs[docid] > 0:
            return rank, docid, score
    return None, None, None


def hit_at_k(results, rel_docs, k=10):
    for docid, rank, score in results[:k]:
        if docid in rel_docs and rel_docs[docid] > 0:
            return 1
    return 0


def main():
    parser = argparse.ArgumentParser(description="Build query-level case table.")
    parser.add_argument("--single-run", type=str, default=str(PROJECT_ROOT / "results" / "single_vector" / "single_vector_run.tsv"))
    parser.add_argument("--full-run", type=str, default=str(PROJECT_ROOT / "results" / "full_multivector" / "full_mv_run.tsv"))
    parser.add_argument("--qrels", type=str, default=str(PROJECT_ROOT / "data" / "metadata" / "qrels.tsv"))
    parser.add_argument("--queries", type=str, default=str(PROJECT_ROOT / "data" / "metadata" / "queries.jsonl"))
    parser.add_argument("--output", type=str, default=str(PROJECT_ROOT / "results" / "analysis" / "case_study_candidates.csv"))
    args = parser.parse_args()

    single_run_path = Path(args.single_run)
    full_run_path = Path(args.full_run)
    qrels_path = Path(args.qrels)
    queries_path = Path(args.queries)
    output_path = Path(args.output)

    ensure_exists(single_run_path, "single run")
    ensure_exists(full_run_path, "full run")
    ensure_exists(qrels_path, "qrels")
    ensure_exists(queries_path, "queries")

    single_run = load_run(single_run_path)
    full_run = load_run(full_run_path)
    qrels = load_qrels(qrels_path)
    queries = load_queries_jsonl(queries_path)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "query_id", "query_text", "query_type",
        "single_hit@10", "full_hit@10",
        "single_first_rel_rank", "full_first_rel_rank",
        "single_first_rel_docid", "full_first_rel_docid",
        "case_label"
    ]

    rows = []
    all_qids = sorted(set(qrels.keys()) | set(single_run.keys()) | set(full_run.keys()))

    for qid in all_qids:
        qobj = queries.get(qid, {})
        qtext = qobj.get("query_text", "")
        qtype = qobj.get("query_type", "")

        rel_docs = qrels.get(qid, {})
        s_results = single_run.get(qid, [])
        f_results = full_run.get(qid, [])

        s_hit = hit_at_k(s_results, rel_docs, 10)
        f_hit = hit_at_k(f_results, rel_docs, 10)

        s_rank, s_docid, _ = first_relevant_rank(s_results, rel_docs)
        f_rank, f_docid, _ = first_relevant_rank(f_results, rel_docs)

        if f_hit == 1 and s_hit == 0:
            case_label = "A_full_mv_better"
        elif f_hit == s_hit:
            case_label = "B_similar_or_small_gain"
        else:
            case_label = "C_both_fail" if f_hit == 0 and s_hit == 0 else "other"

        rows.append({
            "query_id": qid,
            "query_text": qtext,
            "query_type": qtype,
            "single_hit@10": s_hit,
            "full_hit@10": f_hit,
            "single_first_rel_rank": s_rank if s_rank is not None else "",
            "full_first_rel_rank": f_rank if f_rank is not None else "",
            "single_first_rel_docid": s_docid if s_docid is not None else "",
            "full_first_rel_docid": f_docid if f_docid is not None else "",
            "case_label": case_label,
        })

    with output_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote case study candidates to: {output_path}")


if __name__ == "__main__":
    main()
