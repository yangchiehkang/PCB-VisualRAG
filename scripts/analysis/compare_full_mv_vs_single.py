from pathlib import Path
import argparse
import json
import csv
from collections import defaultdict
import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def load_yaml(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_qrels(path: Path):
    qrels = defaultdict(dict)
    with path.open("r", encoding="utf-8") as f:
        first = True
        for line in f:
            parts = line.strip().split("\t")
            if len(parts) < 3:
                continue
            if first and parts[0] == "query_id":
                first = False
                continue
            first = False
            qid, target_id, rel = parts[0], parts[1], parts[2]
            try:
                rel = int(rel)
            except Exception:
                continue
            qrels[qid][target_id] = rel
    return qrels


def load_run(path: Path):
    run = defaultdict(list)
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) < 6:
                continue
            qid, _, target_id, rank, score, tag = parts[:6]
            run[qid].append((target_id, int(rank), float(score)))
    for qid in run:
        run[qid].sort(key=lambda x: x[1])
    return run


def page_hit_at_k(run, qrels, qid, k):
    rel_targets = {t for t, r in qrels.get(qid, {}).items() if r > 0}
    preds = [target_id for target_id, _, _ in run.get(qid, [])[:k]]
    return int(len(rel_targets.intersection(set(preds))) > 0)


def reciprocal_rank_at_k(run, qrels, qid, k):
    rel_targets = {t for t, r in qrels.get(qid, {}).items() if r > 0}
    preds = run.get(qid, [])[:k]
    for i, (target_id, _, _) in enumerate(preds, start=1):
        if target_id in rel_targets:
            return 1.0 / i
    return 0.0


def main():
    parser = argparse.ArgumentParser(description="Compare Full MV vs Single-vector.")
    parser.add_argument("--config", type=str, default=str(PROJECT_ROOT / "configs" / "full_multivector.yaml"))
    parser.add_argument("--single-metrics", type=str, default=str(PROJECT_ROOT / "results" / "single_vector" / "single_vector_metrics.json"))
    parser.add_argument("--single-run", type=str, default=str(PROJECT_ROOT / "results" / "single_vector" / "single_vector_run.tsv"))
    args = parser.parse_args()

    cfg = load_yaml(Path(args.config))

    qrels_file = PROJECT_ROOT / cfg["data"]["qrels_file"]
    full_metrics_file = PROJECT_ROOT / cfg["outputs"]["full_metrics_file"]
    full_run_file = PROJECT_ROOT / cfg["outputs"]["full_run_file"]
    comparison_csv_file = PROJECT_ROOT / cfg["outputs"]["comparison_csv_file"]
    comparison_query_csv_file = PROJECT_ROOT / cfg["outputs"]["comparison_query_csv_file"]

    comparison_csv_file.parent.mkdir(parents=True, exist_ok=True)
    comparison_query_csv_file.parent.mkdir(parents=True, exist_ok=True)

    qrels = load_qrels(qrels_file)
    full_metrics = load_json(full_metrics_file)
    single_metrics = load_json(Path(args.single_metrics))

    full_run = load_run(full_run_file)
    single_run = load_run(Path(args.single_run))

    summary_rows = [
        ["metric_group", "metric", "full_multivector", "single_vector", "delta_full_minus_single"],
        ["effectiveness", "Recall@10", full_metrics.get("Recall@10", ""), single_metrics.get("Recall@10", ""),
         round(float(full_metrics.get("Recall@10", 0)) - float(single_metrics.get("Recall@10", 0)), 6)],
        ["effectiveness", "MRR", full_metrics.get("MRR", ""), single_metrics.get("MRR", ""),
         round(float(full_metrics.get("MRR", 0)) - float(single_metrics.get("MRR", 0)), 6)],
        ["effectiveness", "nDCG@10", full_metrics.get("nDCG@10", ""), single_metrics.get("nDCG@10", ""),
         round(float(full_metrics.get("nDCG@10", 0)) - float(single_metrics.get("nDCG@10", 0)), 6)],
    ]

    with comparison_csv_file.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(summary_rows)

    query_rows = [["query_id", "full_hit@10", "single_hit@10", "full_rr@10", "single_rr@10", "delta_rr"]]
    all_qids = sorted(set(qrels.keys()) | set(full_run.keys()) | set(single_run.keys()))

    for qid in all_qids:
        full_hit = page_hit_at_k(full_run, qrels, qid, 10)
        single_hit = page_hit_at_k(single_run, qrels, qid, 10)
        full_rr = reciprocal_rank_at_k(full_run, qrels, qid, 10)
        single_rr = reciprocal_rank_at_k(single_run, qrels, qid, 10)
        query_rows.append([
            qid,
            full_hit,
            single_hit,
            round(full_rr, 6),
            round(single_rr, 6),
            round(full_rr - single_rr, 6),
        ])

    with comparison_query_csv_file.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(query_rows)

    print(f"Wrote comparison summary to: {comparison_csv_file}")
    print(f"Wrote query-level comparison to: {comparison_query_csv_file}")


if __name__ == "__main__":
    main()
