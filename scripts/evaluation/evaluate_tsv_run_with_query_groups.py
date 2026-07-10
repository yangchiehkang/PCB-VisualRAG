import argparse
import csv
import json
import math
from collections import defaultdict
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def normalize_id(x):
    return str(x).strip()


def to_doc_id(x):
    x = normalize_id(x)
    if "_p" in x:
        return x.split("_p")[0]
    return x


def load_run_tsv(run_path: Path):
    runs_by_query = defaultdict(list)
    run_names = set()

    with run_path.open("r", encoding="utf-8") as f:
        first_line = f.readline()
        f.seek(0)

        if "query_id" in first_line.lower() and "rank" in first_line.lower():
            reader = csv.DictReader(f, delimiter="\t")
            fieldnames = reader.fieldnames or []

            qid_key = "query_id" if "query_id" in fieldnames else fieldnames[0]
            pid_key = "page_id" if "page_id" in fieldnames else ("docid" if "docid" in fieldnames else fieldnames[2])
            rank_key = "rank"
            score_key = "score"
            run_name_key = "run_name" if "run_name" in fieldnames else None

            for row in reader:
                query_id = normalize_id(row[qid_key])
                page_id = normalize_id(row[pid_key])
                rank = int(row[rank_key])
                score = float(row[score_key])

                run_name = row[run_name_key].strip() if run_name_key and row.get(run_name_key) else "unknown_run"
                run_names.add(run_name)

                runs_by_query[query_id].append({
                    "page_id": page_id,
                    "rank": rank,
                    "score": score,
                })
        else:
            for line in f:
                parts = line.strip().split("\t")
                if len(parts) < 6:
                    parts = line.strip().split()
                if len(parts) < 6:
                    continue

                query_id, _, page_id, rank, score, run_name = parts[:6]
                runs_by_query[normalize_id(query_id)].append({
                    "page_id": normalize_id(page_id),
                    "rank": int(rank),
                    "score": float(score),
                })
                run_names.add(run_name)

    for query_id in runs_by_query:
        runs_by_query[query_id] = sorted(runs_by_query[query_id], key=lambda x: x["rank"])

    run_name = list(run_names)[0] if run_names else "unknown_run"
    return run_name, runs_by_query


def load_qrels_tsv(qrels_path: Path):
    qrels = defaultdict(dict)

    lines = [ln.strip() for ln in qrels_path.read_text(encoding="utf-8").splitlines() if ln.strip()]
    if not lines:
        return qrels

    header = lines[0].split("\t")
    header_lower = [x.lower() for x in header]
    has_header = ("query_id" in header_lower or "qid" in header_lower)

    for line in lines[1:] if has_header else lines:
        parts = line.split("\t")
        if len(parts) < 3:
            parts = line.split()

        if has_header:
            if len(parts) < 3:
                continue
            query_id, page_id, relevance = parts[0], parts[1], parts[2]
        else:
            if len(parts) >= 4:
                query_id, _, page_id, relevance = parts[:4]
            elif len(parts) >= 3:
                query_id, page_id, relevance = parts[:3]
            else:
                continue

        try:
            relevance = int(float(relevance))
        except Exception:
            continue

        qrels[normalize_id(query_id)][normalize_id(page_id)] = relevance

    return qrels


def load_queries_jsonl(queries_path: Path | None):
    query_meta = {}
    if queries_path is None:
        return query_meta

    with queries_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            query_id = normalize_id(obj["query_id"])
            query_meta[query_id] = obj

    return query_meta


def hit_at_k(retrieved_ids, relevant_ids, k):
    top_k = retrieved_ids[:k]
    return 1.0 if any(pid in relevant_ids for pid in top_k) else 0.0


def reciprocal_rank(retrieved_ids, relevant_ids, k=10):
    for i, pid in enumerate(retrieved_ids[:k], start=1):
        if pid in relevant_ids:
            return 1.0 / i
    return 0.0


def dcg_at_k(retrieved_ids, relevance_dict, k):
    dcg = 0.0
    for i, pid in enumerate(retrieved_ids[:k], start=1):
        rel = relevance_dict.get(pid, 0)
        if rel > 0:
            dcg += (2 ** rel - 1) / math.log2(i + 1)
    return dcg


def ndcg_at_k(retrieved_ids, relevance_dict, k):
    ideal_rels = sorted(relevance_dict.values(), reverse=True)
    ideal_ids = [f"ideal_{i}" for i in range(len(ideal_rels))]
    ideal_rel_dict = {pid: rel for pid, rel in zip(ideal_ids, ideal_rels)}

    idcg = dcg_at_k(ideal_ids, ideal_rel_dict, k)
    if idcg == 0:
        return 0.0

    dcg = dcg_at_k(retrieved_ids, relevance_dict, k)
    return dcg / idcg


def doc_hit_at_k(retrieved_ids, relevant_ids, k):
    rel_docs = {to_doc_id(x) for x in relevant_ids}
    pred_docs = {to_doc_id(x) for x in retrieved_ids[:k]}
    return 1.0 if len(rel_docs.intersection(pred_docs)) > 0 else 0.0


def evaluate_queries(runs_by_query, qrels, ks=(1, 5, 10)):
    per_query = {}
    query_ids = sorted(qrels.keys())

    for query_id in query_ids:
        relevant_dict = qrels.get(query_id, {})
        relevant_ids = set(relevant_dict.keys())

        retrieved = runs_by_query.get(query_id, [])
        retrieved_ids = [x["page_id"] for x in retrieved]

        metrics = {}
        for k in ks:
            metrics[f"Recall@{k}"] = hit_at_k(retrieved_ids, relevant_ids, k)
            metrics[f"nDCG@{k}"] = ndcg_at_k(retrieved_ids, relevant_dict, k)
            metrics[f"DocRecall@{k}"] = doc_hit_at_k(retrieved_ids, relevant_ids, k)

        metrics["MRR@10"] = reciprocal_rank(retrieved_ids, relevant_ids, k=10)
        per_query[query_id] = metrics

    return per_query


def aggregate_metrics(per_query_metrics):
    if not per_query_metrics:
        return {}

    metric_names = list(next(iter(per_query_metrics.values())).keys())
    aggregated = {}

    for metric_name in metric_names:
        values = [m[metric_name] for m in per_query_metrics.values()]
        aggregated[metric_name] = sum(values) / len(values)

    return aggregated


def group_metrics_by_query_type(per_query_metrics, query_meta):
    grouped = defaultdict(dict)

    for query_id, metrics in per_query_metrics.items():
        query_type = query_meta.get(query_id, {}).get("query_type", "unknown")
        grouped[query_type][query_id] = metrics

    grouped_aggregated = {}
    for query_type, metrics_dict in grouped.items():
        grouped_aggregated[query_type] = aggregate_metrics(metrics_dict)

    return grouped_aggregated


def main():
    parser = argparse.ArgumentParser(description="Evaluate TSV run file with optional query-group analysis.")
    parser.add_argument("--run", type=str, required=True, help="Path to run TSV/TREC file")
    parser.add_argument("--qrels", type=str, required=True, help="Path to qrels TSV file")
    parser.add_argument("--queries", type=str, default=None, help="Path to queries JSONL file")
    parser.add_argument("--output", type=str, default=None, help="Optional output JSON file")
    args = parser.parse_args()

    run_path = Path(args.run)
    qrels_path = Path(args.qrels)
    queries_path = Path(args.queries) if args.queries else None

    run_name, runs_by_query = load_run_tsv(run_path)
    qrels = load_qrels_tsv(qrels_path)
    query_meta = load_queries_jsonl(queries_path)

    per_query_metrics = evaluate_queries(runs_by_query, qrels, ks=(1, 5, 10))
    overall_metrics = aggregate_metrics(per_query_metrics)

    output_obj = {
        "run_name": run_name,
        "query_count_in_run": len(runs_by_query),
        "query_count_in_qrels": len(qrels),
        "evaluated_queries": len(per_query_metrics),
        "overall": overall_metrics,
    }

    if query_meta:
        output_obj["by_query_type"] = group_metrics_by_query_type(per_query_metrics, query_meta)

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(output_obj, indent=2, ensure_ascii=False), encoding="utf-8")

    print(json.dumps(output_obj, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
