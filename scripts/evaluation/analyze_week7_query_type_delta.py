from pathlib import Path
from collections import defaultdict
import csv
import json
import math


PROJECT_ROOT = Path(r"E:\Working\PCB_VisualRAG_Project")

QRELS_PATH = PROJECT_ROOT / "data" / "metadata" / "qrels.tsv"
QUERIES_PATH = PROJECT_ROOT / "data" / "metadata" / "queries.jsonl"

RESULT_DIR = PROJECT_ROOT / "results" / "week7" / "c2f_fixed_N"

BM25_RUN = PROJECT_ROOT / "results" / "baselines" / "bm25_top101_run.tsv"
ALL_CONFIGS_RESULTS = RESULT_DIR / "bm25_c2f_all_configs_results.csv"

OUTPUT_CSV = RESULT_DIR / "query_type_delta_analysis.csv"
OUTPUT_MD = RESULT_DIR / "query_type_delta_analysis.md"
OUTPUT_PER_QUERY_CSV = RESULT_DIR / "query_type_delta_per_query.csv"

TARGET_QUERY_TYPES = [
    "parameter_lookup",
    "structure_legend_interpretation",
    "component_localization",
    "cross_page_consistency",
    "similarity_based_interference",
]


def read_table(path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        sample = f.read(4096)
        f.seek(0)
        delimiter = "\t" if "\t" in sample else ","
        return list(csv.reader(f, delimiter=delimiter))


def load_qrels(path):
    rows = read_table(path)
    qrels = defaultdict(set)

    if not rows:
        return {}

    first = [x.strip().lower() for x in rows[0]]
    has_header = (
        "query_id" in first
        or "qid" in first
        or "page_id" in first
        or "doc_id" in first
        or "relevance" in first
    )

    if has_header:
        header = first
        data_rows = rows[1:]

        def idx(names, default=None):
            for name in names:
                if name in header:
                    return header.index(name)
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

            rel = 1.0
            if rel_idx is not None and rel_idx < len(row):
                try:
                    rel = float(row[rel_idx])
                except Exception:
                    rel = 1.0

            if rel > 0:
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
    rows = read_table(path)

    if not rows:
        return {}

    run = defaultdict(list)

    first = rows[0]
    has_header = is_header(first)

    if has_header:
        header = [x.strip().lower() for x in first]
        data_rows = rows[1:]

        def idx(names, default=None):
            for name in names:
                if name in header:
                    return header.index(name)
            return default

        qid_idx = idx(["query_id", "qid"], None)
        doc_idx = idx(["page_id", "doc_id", "docid", "candidate_page_id"], None)
        rank_idx = idx(["rank"], None)
        score_idx = idx(["score"], None)

        if qid_idx is None or doc_idx is None:
            raise ValueError("Cannot find query/doc columns in run file: {}".format(path))

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


def load_query_types(path):
    query_types = {}

    if not path.exists():
        return query_types

    with path.open("r", encoding="utf-8-sig") as f:
        for line in f:
            line = line.strip()

            if not line:
                continue

            obj = json.loads(line)

            qid = (
                obj.get("query_id")
                or obj.get("qid")
                or obj.get("id")
                or obj.get("queryId")
            )

            qtype = (
                obj.get("query_type")
                or obj.get("type")
                or obj.get("category")
                or obj.get("query_category")
                or obj.get("question_type")
                or obj.get("task_type")
            )

            if qid:
                query_types[str(qid).strip()] = str(qtype).strip() if qtype else "unknown"

    return query_types


def dcg_at_k(rels, k):
    score = 0.0

    for i, rel in enumerate(rels[:k], start=1):
        if rel:
            score += 1.0 / math.log2(i + 1)

    return score


def ndcg_at_10_for_query(ranked_docs, relevant):
    rels = [1 if docid in relevant else 0 for docid in ranked_docs[:10]]
    dcg = dcg_at_k(rels, 10)

    ideal_count = min(len(relevant), 10)
    ideal_rels = [1] * ideal_count
    idcg = dcg_at_k(ideal_rels, 10)

    return dcg / idcg if idcg > 0 else 0.0


def recall_at_k_for_query(ranked_docs, relevant, k):
    retrieved = ranked_docs[:k]
    hit = len(set(retrieved) & relevant)
    return hit / len(relevant) if relevant else 0.0


def mrr_at_10_for_query(ranked_docs, relevant):
    for rank, docid in enumerate(ranked_docs[:10], start=1):
        if docid in relevant:
            return 1.0 / rank
    return 0.0


def select_best_budgeted_run():
    if not ALL_CONFIGS_RESULTS.exists():
        fallback = RESULT_DIR / "bm25_budgetmv_N50_M24_none_run.tsv"
        return fallback, "higher_quality", "50", "24", "none"

    with ALL_CONFIGS_RESULTS.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        rows = []

        for row in reader:
            if row.get("Method", "").strip() == "BM25 + Budgeted MV Rerank":
                rows.append(row)

    if not rows:
        fallback = RESULT_DIR / "bm25_budgetmv_N50_M24_none_run.tsv"
        return fallback, "higher_quality", "50", "24", "none"

    def key(row):
        try:
            ndcg = float(row.get("nDCG@10", "0"))
        except Exception:
            ndcg = 0.0

        try:
            mrr = float(row.get("MRR@10", "0"))
        except Exception:
            mrr = 0.0

        try:
            recall = float(row.get("Recall@10", "0"))
        except Exception:
            recall = 0.0

        return (ndcg, mrr, recall)

    best = sorted(rows, key=key, reverse=True)[0]

    run_file = best.get("Run File", "").strip()
    run_path = PROJECT_ROOT / run_file if run_file else RESULT_DIR / "bm25_budgetmv_N50_M24_none_run.tsv"

    return (
        run_path,
        best.get("Setting", ""),
        best.get("N", ""),
        best.get("M", ""),
        best.get("Compression", ""),
    )


def mean(values):
    return sum(values) / len(values) if values else 0.0


def write_csv(rows, path):
    fieldnames = [
        "Query Type",
        "Query Count",
        "BM25 nDCG@10",
        "BM25+Budgeted MV nDCG@10",
        "Delta nDCG@10",
        "BM25 Recall@10",
        "BM25+Budgeted MV Recall@10",
        "Delta Recall@10",
        "BM25 MRR@10",
        "BM25+Budgeted MV MRR@10",
        "Delta MRR@10",
        "Conclusion",
    ]

    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_per_query_csv(rows, path):
    fieldnames = [
        "query_id",
        "query_type",
        "BM25_nDCG@10",
        "BudgetedMV_nDCG@10",
        "Delta_nDCG@10",
        "BM25_Recall@10",
        "BudgetedMV_Recall@10",
        "Delta_Recall@10",
        "BM25_MRR@10",
        "BudgetedMV_MRR@10",
        "Delta_MRR@10",
    ]

    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_md(rows, path, selected_run, setting, n, m, compression):
    lines = []

    lines.append("# Week 7 Query Type Delta Analysis")
    lines.append("")
    lines.append("Selected Budgeted MV run:")
    lines.append("")
    lines.append("```text")
    lines.append(str(selected_run.relative_to(PROJECT_ROOT)))
    lines.append("setting={} N={} M={} compression={}".format(setting, n, m, compression))
    lines.append("```")
    lines.append("")
    lines.append("| Query Type | Query Count | BM25 nDCG@10 | BM25+Budgeted MV nDCG@10 | Delta nDCG@10 | BM25 Recall@10 | Budgeted Recall@10 | Delta Recall@10 | Conclusion |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---|")

    for row in rows:
        lines.append(
            "| {} | {} | {} | {} | {} | {} | {} | {} | {} |".format(
                row["Query Type"],
                row["Query Count"],
                row["BM25 nDCG@10"],
                row["BM25+Budgeted MV nDCG@10"],
                row["Delta nDCG@10"],
                row["BM25 Recall@10"],
                row["BM25+Budgeted MV Recall@10"],
                row["Delta Recall@10"],
                row["Conclusion"],
            )
        )

    lines.append("")
    lines.append("## Key Findings")
    lines.append("")

    improved = [r for r in rows if float(r["Delta nDCG@10"]) > 0]
    harmed = [r for r in rows if float(r["Delta nDCG@10"]) < 0]
    unchanged = [r for r in rows if float(r["Delta nDCG@10"]) == 0]

    lines.append("### Improved query types")
    lines.append("")
    if improved:
        for r in improved:
            lines.append("- {}: Delta nDCG@10={}".format(r["Query Type"], r["Delta nDCG@10"]))
    else:
        lines.append("- None")
    lines.append("")

    lines.append("### Harmed query types")
    lines.append("")
    if harmed:
        for r in harmed:
            lines.append("- {}: Delta nDCG@10={}".format(r["Query Type"], r["Delta nDCG@10"]))
    else:
        lines.append("- None")
    lines.append("")

    lines.append("### Unchanged query types")
    lines.append("")
    if unchanged:
        for r in unchanged:
            lines.append("- {}: Delta nDCG@10={}".format(r["Query Type"], r["Delta nDCG@10"]))
    else:
        lines.append("- None")
    lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")


def main():
    RESULT_DIR.mkdir(parents=True, exist_ok=True)

    qrels = load_qrels(QRELS_PATH)
    query_types = load_query_types(QUERIES_PATH)

    bm25_run = load_run(BM25_RUN)

    budgeted_run_path, setting, n, m, compression = select_best_budgeted_run()
    budgeted_run = load_run(budgeted_run_path)

    per_query_rows = []
    grouped = defaultdict(list)

    for qid in sorted(qrels.keys()):
        qtype = query_types.get(qid, "unknown")

        relevant = qrels[qid]
        bm25_docs = bm25_run.get(qid, [])
        budget_docs = budgeted_run.get(qid, [])

        bm25_ndcg = ndcg_at_10_for_query(bm25_docs, relevant)
        budget_ndcg = ndcg_at_10_for_query(budget_docs, relevant)
        delta_ndcg = budget_ndcg - bm25_ndcg

        bm25_recall = recall_at_k_for_query(bm25_docs, relevant, 10)
        budget_recall = recall_at_k_for_query(budget_docs, relevant, 10)
        delta_recall = budget_recall - bm25_recall

        bm25_mrr = mrr_at_10_for_query(bm25_docs, relevant)
        budget_mrr = mrr_at_10_for_query(budget_docs, relevant)
        delta_mrr = budget_mrr - bm25_mrr

        item = {
            "query_id": qid,
            "query_type": qtype,
            "bm25_ndcg": bm25_ndcg,
            "budget_ndcg": budget_ndcg,
            "delta_ndcg": delta_ndcg,
            "bm25_recall": bm25_recall,
            "budget_recall": budget_recall,
            "delta_recall": delta_recall,
            "bm25_mrr": bm25_mrr,
            "budget_mrr": budget_mrr,
            "delta_mrr": delta_mrr,
        }

        grouped[qtype].append(item)

        per_query_rows.append(
            {
                "query_id": qid,
                "query_type": qtype,
                "BM25_nDCG@10": "{:.4f}".format(bm25_ndcg),
                "BudgetedMV_nDCG@10": "{:.4f}".format(budget_ndcg),
                "Delta_nDCG@10": "{:.4f}".format(delta_ndcg),
                "BM25_Recall@10": "{:.4f}".format(bm25_recall),
                "BudgetedMV_Recall@10": "{:.4f}".format(budget_recall),
                "Delta_Recall@10": "{:.4f}".format(delta_recall),
                "BM25_MRR@10": "{:.4f}".format(bm25_mrr),
                "BudgetedMV_MRR@10": "{:.4f}".format(budget_mrr),
                "Delta_MRR@10": "{:.4f}".format(delta_mrr),
            }
        )

    output_rows = []

    ordered_types = []
    for t in TARGET_QUERY_TYPES:
        if t in grouped:
            ordered_types.append(t)

    for t in sorted(grouped.keys()):
        if t not in ordered_types:
            ordered_types.append(t)

    for qtype in ordered_types:
        items = grouped[qtype]

        bm25_ndcg = mean([x["bm25_ndcg"] for x in items])
        budget_ndcg = mean([x["budget_ndcg"] for x in items])
        delta_ndcg = budget_ndcg - bm25_ndcg

        bm25_recall = mean([x["bm25_recall"] for x in items])
        budget_recall = mean([x["budget_recall"] for x in items])
        delta_recall = budget_recall - bm25_recall

        bm25_mrr = mean([x["bm25_mrr"] for x in items])
        budget_mrr = mean([x["budget_mrr"] for x in items])
        delta_mrr = budget_mrr - bm25_mrr

        if delta_ndcg > 0:
            conclusion = "Improved"
        elif delta_ndcg < 0:
            conclusion = "Harmed"
        else:
            conclusion = "Unchanged"

        output_rows.append(
            {
                "Query Type": qtype,
                "Query Count": len(items),
                "BM25 nDCG@10": "{:.4f}".format(bm25_ndcg),
                "BM25+Budgeted MV nDCG@10": "{:.4f}".format(budget_ndcg),
                "Delta nDCG@10": "{:.4f}".format(delta_ndcg),
                "BM25 Recall@10": "{:.4f}".format(bm25_recall),
                "BM25+Budgeted MV Recall@10": "{:.4f}".format(budget_recall),
                "Delta Recall@10": "{:.4f}".format(delta_recall),
                "BM25 MRR@10": "{:.4f}".format(bm25_mrr),
                "BM25+Budgeted MV MRR@10": "{:.4f}".format(budget_mrr),
                "Delta MRR@10": "{:.4f}".format(delta_mrr),
                "Conclusion": conclusion,
            }
        )

    write_csv(output_rows, OUTPUT_CSV)
    write_per_query_csv(per_query_rows, OUTPUT_PER_QUERY_CSV)
    write_md(output_rows, OUTPUT_MD, budgeted_run_path, setting, n, m, compression)

    print("Selected Budgeted MV run: {}".format(budgeted_run_path))
    print("Setting: {} N={} M={} compression={}".format(setting, n, m, compression))
    print("")
    print("========== Query Type Delta Analysis ==========")
    print("Query Type,Query Count,BM25 nDCG@10,BM25+Budgeted MV nDCG@10,Delta nDCG@10,Conclusion")

    for row in output_rows:
        print(
            "{},{},{},{},{},{}".format(
                row["Query Type"],
                row["Query Count"],
                row["BM25 nDCG@10"],
                row["BM25+Budgeted MV nDCG@10"],
                row["Delta nDCG@10"],
                row["Conclusion"],
            )
        )

    print("")
    print("Wrote CSV: {}".format(OUTPUT_CSV))
    print("Wrote Markdown: {}".format(OUTPUT_MD))
    print("Wrote per-query CSV: {}".format(OUTPUT_PER_QUERY_CSV))


if __name__ == "__main__":
    main()
