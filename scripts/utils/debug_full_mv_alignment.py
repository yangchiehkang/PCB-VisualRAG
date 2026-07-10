from pathlib import Path
from collections import defaultdict
import argparse
import json


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def ensure_exists(path: Path, name: str):
    if not path.exists():
        raise FileNotFoundError(f"{name} not found: {path}")


def normalize_id(x: str):
    x = str(x).strip()
    if not x:
        return x
    x = x.replace("\\", "/")
    x = x.split("/")[-1]
    return x


def to_doc_id(x: str):
    x = normalize_id(x)
    if "_p" in x:
        return x.split("_p")[0]
    return x


def load_qrels(qrels_path: Path):
    qrels = defaultdict(list)

    lines = qrels_path.read_text(encoding="utf-8").splitlines()
    lines = [ln.strip() for ln in lines if ln.strip()]

    if not lines:
        return qrels

    first_parts = lines[0].split("\t")
    has_header = False
    if len(first_parts) >= 3:
        first_lower = [p.strip().lower() for p in first_parts]
        if "query_id" in first_lower or "qid" in first_lower:
            has_header = True

    start_idx = 1 if has_header else 0

    for line in lines[start_idx:]:
        parts = line.split("\t")
        if len(parts) < 3:
            parts = line.split()

        if len(parts) < 3:
            continue

        if has_header:
            qid = normalize_id(parts[0])
            target = normalize_id(parts[1])
            rel_raw = parts[2]
        else:
            # support either 3-col qrels or TREC 4-col qrels
            if len(parts) >= 4:
                qid = normalize_id(parts[0])
                target = normalize_id(parts[2])
                rel_raw = parts[3]
            else:
                qid = normalize_id(parts[0])
                target = normalize_id(parts[1])
                rel_raw = parts[2]

        try:
            rel = int(float(rel_raw))
        except Exception:
            continue

        if rel > 0:
            qrels[qid].append(target)

    return qrels


def load_run(run_path: Path):
    run = defaultdict(list)

    for line in run_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue

        parts = line.split("\t")
        if len(parts) < 6:
            parts = line.split()

        if len(parts) < 6:
            continue

        qid = normalize_id(parts[0])
        page_id = normalize_id(parts[2])

        try:
            rank = int(parts[3])
        except Exception:
            rank = 999999

        try:
            score = float(parts[4])
        except Exception:
            score = 0.0

        run[qid].append((page_id, rank, score))

    for qid in run:
        run[qid] = sorted(run[qid], key=lambda x: x[1])

    return run


def main():
    parser = argparse.ArgumentParser(description="Debug alignment between qrels and Full MV run.")
    parser.add_argument(
        "--qrels",
        type=str,
        default=str(PROJECT_ROOT / "data" / "metadata" / "qrels.tsv")
    )
    parser.add_argument(
        "--run",
        type=str,
        default=str(PROJECT_ROOT / "results" / "full_multivector" / "full_mv_small_run.tsv")
    )
    parser.add_argument(
        "--topk",
        type=int,
        default=10
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=10
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(PROJECT_ROOT / "results" / "analysis" / "debug_full_mv_alignment_summary.json")
    )
    args = parser.parse_args()

    qrels_path = Path(args.qrels)
    run_path = Path(args.run)
    output_path = Path(args.output)

    ensure_exists(qrels_path, "qrels file")
    ensure_exists(run_path, "run file")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    qrels = load_qrels(qrels_path)
    run = load_run(run_path)

    qrels_qids = set(qrels.keys())
    run_qids = set(run.keys())
    all_qids = sorted(qrels_qids | run_qids)
    both_qids = sorted(qrels_qids & run_qids)
    only_in_qrels = sorted(qrels_qids - run_qids)
    only_in_run = sorted(run_qids - qrels_qids)

    page_hit_count = 0
    doc_hit_count = 0
    evaluated_qids = 0
    sample_debug = []

    for qid in all_qids:
        gold_targets = qrels.get(qid, [])
        pred_pages = [x[0] for x in run.get(qid, [])[:args.topk]]

        gold_docs = [to_doc_id(g) for g in gold_targets]
        pred_docs = [to_doc_id(p) for p in pred_pages]

        page_hit = len(set(gold_targets).intersection(set(pred_pages))) > 0
        doc_hit = len(set(gold_docs).intersection(set(pred_docs))) > 0

        if qid in qrels:
            evaluated_qids += 1
            if page_hit:
                page_hit_count += 1
            if doc_hit:
                doc_hit_count += 1

        if len(sample_debug) < args.sample_size:
            sample_debug.append({
                "query_id": qid,
                "gold_targets": gold_targets[:10],
                "gold_docs": gold_docs[:10],
                "pred_pages_topk": pred_pages,
                "pred_docs_topk": pred_docs,
                "page_hit_at_k": page_hit,
                "doc_hit_at_k": doc_hit
            })

    summary = {
        "qrels_path": str(qrels_path),
        "run_path": str(run_path),
        "topk": args.topk,
        "query_count_in_run": len(run_qids),
        "query_count_in_qrels": len(qrels_qids),
        "queries_in_both": len(both_qids),
        "queries_only_in_qrels": len(only_in_qrels),
        "queries_only_in_run": len(only_in_run),
        "evaluated_queries": evaluated_qids,
        "queries_with_page_exact_hit_at_k": page_hit_count,
        "queries_with_doc_hit_at_k": doc_hit_count,
        "page_hit_rate_at_k": round(page_hit_count / evaluated_qids, 6) if evaluated_qids > 0 else 0.0,
        "doc_hit_rate_at_k": round(doc_hit_count / evaluated_qids, 6) if evaluated_qids > 0 else 0.0,
        "sample_queries_only_in_qrels": only_in_qrels[:10],
        "sample_queries_only_in_run": only_in_run[:10],
        "sample_debug": sample_debug
    }

    output_path.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    print(json.dumps(summary, indent=2, ensure_ascii=False))
    print(f"\nWrote summary to: {output_path}")


if __name__ == "__main__":
    main()
