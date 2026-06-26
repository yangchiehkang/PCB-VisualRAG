from pathlib import Path
import argparse
import json
from collections import defaultdict
import math


def normalize_id(x):
    return str(x).strip()


def to_doc_id(x):
    x = normalize_id(x)
    if "_p" in x:
        return x.split("_p")[0]
    return x


def load_qrels(path: Path):
    qrels = defaultdict(dict)

    lines = [ln.strip() for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]
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
            qid, target_id, rel = parts[0], parts[1], parts[2]
        else:
            if len(parts) >= 4:
                qid, _, target_id, rel = parts[:4]
            elif len(parts) >= 3:
                qid, target_id, rel = parts[:3]
            else:
                continue

        try:
            rel = int(float(rel))
        except Exception:
            continue

        qrels[normalize_id(qid)][normalize_id(target_id)] = rel

    return qrels


def load_run(path: Path):
    run = defaultdict(list)

    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            parts = line.split("\t")
            if len(parts) < 6:
                parts = line.split()

            if len(parts) < 6:
                continue

            qid, _, target_id, rank, score, _ = parts[:6]

            try:
                rank = int(rank)
                score = float(score)
            except Exception:
                continue

            run[normalize_id(qid)].append((normalize_id(target_id), rank, score))

    for qid in run:
        run[qid].sort(key=lambda x: x[1])

    return run


def dcg(rels):
    out = 0.0
    for i, rel in enumerate(rels, start=1):
        out += (2 ** rel - 1) / math.log2(i + 1)
    return out


def average_valid(values):
    vals = [v for v in values if v is not None]
    return sum(vals) / len(vals) if vals else 0.0


def recall_at_k_for_qid(run, qrels, qid, k=10):
    rel_targets = {t for t, r in qrels.get(qid, {}).items() if r > 0}
    if not rel_targets:
        return None
    ranked = run.get(qid, [])
    top_targets = {target_id for target_id, _, _ in ranked[:k]}
    return 1.0 if len(rel_targets.intersection(top_targets)) > 0 else 0.0


def mrr_at_k_for_qid(run, qrels, qid, k=10):
    rel_targets = {t for t, r in qrels.get(qid, {}).items() if r > 0}
    if not rel_targets:
        return None
    ranked = run.get(qid, [])
    for i, (target_id, _, _) in enumerate(ranked[:k], start=1):
        if target_id in rel_targets:
            return 1.0 / i
    return 0.0


def ndcg_at_k_for_qid(run, qrels, qid, k=10):
    gold = qrels.get(qid, {})
    if not gold:
        return None
    ranked = run.get(qid, [])
    pred_rels = [gold.get(target_id, 0) for target_id, _, _ in ranked[:k]]
    ideal_rels = sorted(gold.values(), reverse=True)[:k]
    if not ideal_rels:
        return None
    actual = dcg(pred_rels)
    ideal = dcg(ideal_rels)
    return actual / ideal if ideal > 0 else 0.0


def doc_level_recall_at_k_for_qid(run, qrels, qid, k=10):
    rel_pages = {t for t, r in qrels.get(qid, {}).items() if r > 0}
    rel_docs = {to_doc_id(t) for t in rel_pages}
    if not rel_docs:
        return None
    ranked = run.get(qid, [])
    pred_docs = {to_doc_id(target_id) for target_id, _, _ in ranked[:k]}
    return 1.0 if len(rel_docs.intersection(pred_docs)) > 0 else 0.0


def evaluate_run(run, qrels):
    eval_qids = sorted(qrels.keys())

    metrics = {
        "query_count_in_run": len(run),
        "query_count_in_qrels": len(qrels),
        "evaluated_queries": len(eval_qids),
        "page_level": {
            "MRR@10": average_valid([mrr_at_k_for_qid(run, qrels, qid, 10) for qid in eval_qids]),
            "Recall@1": average_valid([recall_at_k_for_qid(run, qrels, qid, 1) for qid in eval_qids]),
            "Recall@5": average_valid([recall_at_k_for_qid(run, qrels, qid, 5) for qid in eval_qids]),
            "Recall@10": average_valid([recall_at_k_for_qid(run, qrels, qid, 10) for qid in eval_qids]),
            "nDCG@10": average_valid([ndcg_at_k_for_qid(run, qrels, qid, 10) for qid in eval_qids]),
        },
        "doc_level_aux": {
            "Recall@1": average_valid([doc_level_recall_at_k_for_qid(run, qrels, qid, 1) for qid in eval_qids]),
            "Recall@5": average_valid([doc_level_recall_at_k_for_qid(run, qrels, qid, 5) for qid in eval_qids]),
            "Recall@10": average_valid([doc_level_recall_at_k_for_qid(run, qrels, qid, 10) for qid in eval_qids]),
        },
    }

    return metrics


def flatten_top_level_metrics(metrics):
    page = metrics["page_level"]
    return {
        "query_count": metrics["evaluated_queries"],
        "MRR": page["MRR@10"],
        "Recall@1": page["Recall@1"],
        "Recall@5": page["Recall@5"],
        "Recall@10": page["Recall@10"],
        "nDCG@10": page["nDCG@10"],
        "page_level": metrics["page_level"],
        "doc_level_aux": metrics["doc_level_aux"],
        "query_count_in_run": metrics["query_count_in_run"],
        "query_count_in_qrels": metrics["query_count_in_qrels"],
    }


def main():
    parser = argparse.ArgumentParser(description="Evaluate a generic run file against qrels.")
    parser.add_argument("--qrels", type=str, required=True)
    parser.add_argument("--run", type=str, required=True)
    parser.add_argument("--output", type=str, required=True)
    args = parser.parse_args()

    qrels = load_qrels(Path(args.qrels))
    run = load_run(Path(args.run))

    metrics = evaluate_run(run, qrels)
    output_obj = flatten_top_level_metrics(metrics)

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(output_obj, indent=2, ensure_ascii=False), encoding="utf-8")

    print(json.dumps(output_obj, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
