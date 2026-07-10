from pathlib import Path
from collections import defaultdict
import csv
import math
import json


PROJECT_ROOT = Path(r"E:\Working\PCB_VisualRAG_Project")

QRELS_PATH = PROJECT_ROOT / "data" / "metadata" / "qrels.tsv"

RESULT_DIR = PROJECT_ROOT / "results" / "week7" / "c2f_fixed_N"

BM25_BASELINE_RUN = PROJECT_ROOT / "results" / "baselines" / "bm25_top101_run.tsv"

FULLMV_SUMMARY = RESULT_DIR / "bm25_fullmv_rerank_summary.csv"
BUDGETMV_SUMMARY = RESULT_DIR / "bm25_budgetmv_rerank_summary.csv"

ALL_CONFIGS_OUTPUT_CSV = RESULT_DIR / "bm25_c2f_all_configs_results.csv"
ALL_CONFIGS_OUTPUT_MD = RESULT_DIR / "bm25_c2f_all_configs_results.md"

MAIN_TABLE_OUTPUT_CSV = RESULT_DIR / "bm25_c2f_main_results.csv"
MAIN_TABLE_OUTPUT_MD = RESULT_DIR / "bm25_c2f_main_results.md"


def read_tsv_or_csv(path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        sample = f.read(4096)
        f.seek(0)

        if "\t" in sample:
            delimiter = "\t"
        else:
            delimiter = ","

        return list(csv.reader(f, delimiter=delimiter))


def load_qrels(path):
    rows = read_tsv_or_csv(path)

    if not rows:
        raise ValueError("Empty qrels file: {}".format(path))

    qrels = defaultdict(set)

    first = rows[0]
    lower = [x.strip().lower() for x in first]

    has_header = (
        "query_id" in lower
        or "qid" in lower
        or "page_id" in lower
        or "doc_id" in lower
        or "relevance" in lower
    )

    if has_header:
        header = lower
        data_rows = rows[1:]

        def idx(candidates, default=None):
            for c in candidates:
                if c in header:
                    return header.index(c)
            return default

        qid_idx = idx(["query_id", "qid"], 0)
        doc_idx = idx(["page_id", "doc_id", "docid", "candidate_page_id"], 1)
        rel_idx = idx(["relevance", "rel", "label"], None)

        for row in data_rows:
            if len(row) <= max(qid_idx, doc_idx):
                continue

            qid = row[qid_idx].strip()
            docid = row[doc_idx].strip()

            if not qid or not docid:
                continue

            if rel_idx is not None and rel_idx < len(row):
                try:
                    rel = float(row[rel_idx])
                except Exception:
                    rel = 1.0
                if rel <= 0:
                    continue

            qrels[qid].add(docid)

    else:
        for row in rows:
            if len(row) >= 4:
                qid = row[0].strip()
                docid = row[2].strip()
                try:
                    rel = float(row[3])
                except Exception:
                    rel = 1.0

                if qid and docid and rel > 0:
                    qrels[qid].add(docid)

            elif len(row) >= 2:
                qid = row[0].strip()
                docid = row[1].strip()

                if qid and docid:
                    qrels[qid].add(docid)

    return dict(qrels)


def is_header(row):
    joined = "\t".join(row).lower()
    keys = [
        "query_id",
        "qid",
        "page_id",
        "doc_id",
        "docid",
        "rank",
        "score",
        "run_name",
    ]
    return any(k in joined for k in keys)


def load_run(path):
    rows = read_tsv_or_csv(path)

    if not rows:
        raise ValueError("Empty run file: {}".format(path))

    run = defaultdict(list)

    first = rows[0]
    has_header = is_header(first)

    if has_header:
        header = [x.strip().lower() for x in first]
        data_rows = rows[1:]

        def idx(candidates, default=None):
            for c in candidates:
                if c in header:
                    return header.index(c)
            return default

        qid_idx = idx(["query_id", "qid"], None)
        doc_idx = idx(["page_id", "doc_id", "docid", "candidate_page_id"], None)
        rank_idx = idx(["rank"], None)
        score_idx = idx(["score"], None)

        if qid_idx is None or doc_idx is None:
            raise ValueError("Cannot find qid/docid columns in {}".format(path))

        for i, row in enumerate(data_rows):
            if len(row) <= max(qid_idx, doc_idx):
                continue

            qid = row[qid_idx].strip()
            docid = row[doc_idx].strip()

            if not qid or not docid:
                continue

            if rank_idx is not None and rank_idx < len(row):
                try:
                    rank = int(float(row[rank_idx]))
                except Exception:
                    rank = i + 1
            else:
                rank = i + 1

            if score_idx is not None and score_idx < len(row):
                try:
                    score = float(row[score_idx])
                except Exception:
                    score = 0.0
            else:
                score = 0.0

            run[qid].append((rank, docid, score))

    else:
        for i, row in enumerate(rows):
            if len(row) >= 6 and row[1].strip().upper() == "Q0":
                qid = row[0].strip()
                docid = row[2].strip()

                try:
                    rank = int(float(row[3]))
                except Exception:
                    rank = i + 1

                try:
                    score = float(row[4])
                except Exception:
                    score = 0.0

                run[qid].append((rank, docid, score))

            elif len(row) >= 5 and row[0].strip().lower().startswith(("bm25", "c2f")):
                qid = row[1].strip()
                docid = row[2].strip()

                try:
                    rank = int(float(row[3]))
                except Exception:
                    rank = i + 1

                try:
                    score = float(row[4])
                except Exception:
                    score = 0.0

                run[qid].append((rank, docid, score))

            elif len(row) >= 4:
                qid = row[0].strip()
                docid = row[1].strip()

                try:
                    rank = int(float(row[2]))
                except Exception:
                    rank = i + 1

                try:
                    score = float(row[3])
                except Exception:
                    score = 0.0

                run[qid].append((rank, docid, score))

    final_run = {}

    for qid, items in run.items():
        items = sorted(items, key=lambda x: (x[0], -x[2]))
        final_run[qid] = [docid for rank, docid, score in items]

    return final_run


def dcg_at_k(rels, k):
    total = 0.0

    for i, rel in enumerate(rels[:k], start=1):
        if rel:
            total += 1.0 / math.log2(i + 1)

    return total


def evaluate_run(run, qrels):
    query_ids = sorted(qrels.keys())

    recall_1_values = []
    recall_5_values = []
    recall_10_values = []
    mrr_10_values = []
    ndcg_10_values = []

    for qid in query_ids:
        relevant = qrels[qid]
        ranked_docs = run.get(qid, [])

        def recall_at_k(k):
            retrieved = ranked_docs[:k]
            hit = len(set(retrieved) & relevant)
            return hit / len(relevant) if relevant else 0.0

        recall_1_values.append(recall_at_k(1))
        recall_5_values.append(recall_at_k(5))
        recall_10_values.append(recall_at_k(10))

        rr = 0.0
        for rank, docid in enumerate(ranked_docs[:10], start=1):
            if docid in relevant:
                rr = 1.0 / rank
                break
        mrr_10_values.append(rr)

        rels = [1 if docid in relevant else 0 for docid in ranked_docs[:10]]
        dcg = dcg_at_k(rels, 10)

        ideal_rel_count = min(len(relevant), 10)
        ideal_rels = [1] * ideal_rel_count
        idcg = dcg_at_k(ideal_rels, 10)

        ndcg = dcg / idcg if idcg > 0 else 0.0
        ndcg_10_values.append(ndcg)

    def mean(values):
        return sum(values) / len(values) if values else 0.0

    return {
        "Recall@1": mean(recall_1_values),
        "Recall@5": mean(recall_5_values),
        "Recall@10": mean(recall_10_values),
        "MRR@10": mean(mrr_10_values),
        "nDCG@10": mean(ndcg_10_values),
        "Queries": len(query_ids),
    }


def load_latency_map(summary_path, key_type):
    latency_map = {}

    if not summary_path.exists():
        return latency_map

    with summary_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)

        for row in reader:
            if key_type == "fullmv":
                n = row.get("N", "").strip()
                key = "fullmv_N{}".format(n)

            elif key_type == "budgetmv":
                n = row.get("N", "").strip()
                m = row.get("M", "").strip()
                compression = row.get("compression", "").strip()
                key = "budgetmv_N{}_M{}_{}".format(n, m, compression)

            else:
                continue

            latency = row.get("avg_rerank_latency_ms_per_query", "")

            latency_map[key] = latency

    return latency_map


def format_float(x):
    if isinstance(x, str):
        return x
    return "{:.4f}".format(float(x))


def build_all_configs_rows(qrels):
    rows = []

    bm25_run = load_run(BM25_BASELINE_RUN)
    bm25_metrics = evaluate_run(bm25_run, qrels)

    rows.append(
        {
            "Method": "BM25",
            "Setting": "baseline",
            "N": "-",
            "M": "-",
            "Compression": "-",
            "Recall@1": bm25_metrics["Recall@1"],
            "Recall@5": bm25_metrics["Recall@5"],
            "Recall@10": bm25_metrics["Recall@10"],
            "MRR@10": bm25_metrics["MRR@10"],
            "nDCG@10": bm25_metrics["nDCG@10"],
            "Latency": "-",
            "Run File": str(BM25_BASELINE_RUN.relative_to(PROJECT_ROOT)),
        }
    )

    full_latency = load_latency_map(FULLMV_SUMMARY, "fullmv")
    budget_latency = load_latency_map(BUDGETMV_SUMMARY, "budgetmv")

    for n in [10, 20, 50, 100]:
        run_path = RESULT_DIR / "bm25_fullmv_N{}_run.tsv".format(n)

        if not run_path.exists():
            continue

        run = load_run(run_path)
        metrics = evaluate_run(run, qrels)

        rows.append(
            {
                "Method": "BM25 + Full MV Rerank",
                "Setting": "fullmv_N{}".format(n),
                "N": n,
                "M": "-",
                "Compression": "none",
                "Recall@1": metrics["Recall@1"],
                "Recall@5": metrics["Recall@5"],
                "Recall@10": metrics["Recall@10"],
                "MRR@10": metrics["MRR@10"],
                "nDCG@10": metrics["nDCG@10"],
                "Latency": full_latency.get("fullmv_N{}".format(n), "-"),
                "Run File": str(run_path.relative_to(PROJECT_ROOT)),
            }
        )

    budget_configs = [
        ("low_cost", 20, 8, "none"),
        ("mid_cost", 20, 16, "none"),
        ("higher_quality", 50, 24, "none"),
    ]

    for setting, n, m, compression in budget_configs:
        run_path = RESULT_DIR / "bm25_budgetmv_N{}_M{}_{}_run.tsv".format(n, m, compression)

        if not run_path.exists():
            continue

        run = load_run(run_path)
        metrics = evaluate_run(run, qrels)

        key = "budgetmv_N{}_M{}_{}".format(n, m, compression)

        rows.append(
            {
                "Method": "BM25 + Budgeted MV Rerank",
                "Setting": setting,
                "N": n,
                "M": m,
                "Compression": compression,
                "Recall@1": metrics["Recall@1"],
                "Recall@5": metrics["Recall@5"],
                "Recall@10": metrics["Recall@10"],
                "MRR@10": metrics["MRR@10"],
                "nDCG@10": metrics["nDCG@10"],
                "Latency": budget_latency.get(key, "-"),
                "Run File": str(run_path.relative_to(PROJECT_ROOT)),
            }
        )

    return rows


def pick_best_rows(all_rows):
    main_rows = []

    bm25_rows = [r for r in all_rows if r["Method"] == "BM25"]
    full_rows = [r for r in all_rows if r["Method"] == "BM25 + Full MV Rerank"]
    budget_rows = [r for r in all_rows if r["Method"] == "BM25 + Budgeted MV Rerank"]

    if bm25_rows:
        main_rows.append(bm25_rows[0])

    if full_rows:
        best_full = sorted(
            full_rows,
            key=lambda r: (float(r["nDCG@10"]), float(r["MRR@10"]), float(r["Recall@10"])),
            reverse=True,
        )[0]
        main_rows.append(best_full)

    if budget_rows:
        best_budget = sorted(
            budget_rows,
            key=lambda r: (float(r["nDCG@10"]), float(r["MRR@10"]), float(r["Recall@10"])),
            reverse=True,
        )[0]
        main_rows.append(best_budget)

    return main_rows


def write_csv(rows, path):
    fieldnames = [
        "Method",
        "Setting",
        "N",
        "M",
        "Compression",
        "Recall@1",
        "Recall@5",
        "Recall@10",
        "MRR@10",
        "nDCG@10",
        "Latency",
        "Run File",
    ]

    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for row in rows:
            out = dict(row)

            for k in ["Recall@1", "Recall@5", "Recall@10", "MRR@10", "nDCG@10"]:
                out[k] = format_float(out[k])

            if out["Latency"] != "-":
                out["Latency"] = "{:.6f}".format(float(out["Latency"]))

            writer.writerow(out)


def write_md(rows, path, title):
    lines = []
    lines.append("# {}".format(title))
    lines.append("")
    lines.append("| Method | Setting | N | M | Compression | Recall@1 | Recall@5 | Recall@10 | MRR@10 | nDCG@10 | Latency ms/query |")
    lines.append("|---|---|---:|---:|---|---:|---:|---:|---:|---:|---:|")

    for row in rows:
        latency = row["Latency"]
        if latency != "-":
            latency = "{:.6f}".format(float(latency))

        lines.append(
            "| {} | {} | {} | {} | {} | {} | {} | {} | {} | {} | {} |".format(
                row["Method"],
                row["Setting"],
                row["N"],
                row["M"],
                row["Compression"],
                format_float(row["Recall@1"]),
                format_float(row["Recall@5"]),
                format_float(row["Recall@10"]),
                format_float(row["MRR@10"]),
                format_float(row["nDCG@10"]),
                latency,
            )
        )

    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def print_table(rows, title):
    print("")
    print("========== {} ==========".format(title))

    header = [
        "Method",
        "Setting",
        "N",
        "M",
        "Recall@1",
        "Recall@5",
        "Recall@10",
        "MRR@10",
        "nDCG@10",
        "Latency",
    ]

    print(",".join(header))

    for row in rows:
        latency = row["Latency"]
        if latency != "-":
            latency = "{:.6f}".format(float(latency))

        print(
            "{},{},{},{},{},{},{},{},{},{}".format(
                row["Method"],
                row["Setting"],
                row["N"],
                row["M"],
                format_float(row["Recall@1"]),
                format_float(row["Recall@5"]),
                format_float(row["Recall@10"]),
                format_float(row["MRR@10"]),
                format_float(row["nDCG@10"]),
                latency,
            )
        )


def main():
    RESULT_DIR.mkdir(parents=True, exist_ok=True)

    qrels = load_qrels(QRELS_PATH)

    all_rows = build_all_configs_rows(qrels)
    main_rows = pick_best_rows(all_rows)

    write_csv(all_rows, ALL_CONFIGS_OUTPUT_CSV)
    write_md(all_rows, ALL_CONFIGS_OUTPUT_MD, "Week 7 BM25-C2F All Configs Results")

    write_csv(main_rows, MAIN_TABLE_OUTPUT_CSV)
    write_md(main_rows, MAIN_TABLE_OUTPUT_MD, "Week 7 BM25-C2F Main Results")

    print_table(all_rows, "All Configs")
    print_table(main_rows, "Main Table")

    print("")
    print("Wrote CSV: {}".format(ALL_CONFIGS_OUTPUT_CSV))
    print("Wrote Markdown: {}".format(ALL_CONFIGS_OUTPUT_MD))
    print("Wrote CSV: {}".format(MAIN_TABLE_OUTPUT_CSV))
    print("Wrote Markdown: {}".format(MAIN_TABLE_OUTPUT_MD))


if __name__ == "__main__":
    main()
