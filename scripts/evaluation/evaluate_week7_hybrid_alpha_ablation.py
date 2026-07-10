from pathlib import Path
from collections import defaultdict
import csv
import math
import json


PROJECT_ROOT = Path(r"E:\Working\PCB_VisualRAG_Project")

QRELS_PATH = PROJECT_ROOT / "data" / "metadata" / "qrels.tsv"

HYBRID_DIR = PROJECT_ROOT / "results" / "week7" / "hybrid_fusion"
OUTPUT_DIR = PROJECT_ROOT / "results" / "week7" / "hybrid_fusion"

ALPHAS_FOR_TABLE = [0.2, 0.4, 0.6, 0.8]
ALL_ALPHAS = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]

METHOD_CONFIGS = [
    {
        "method": "fullmv",
        "setting": "hybrid_fullmv_N50",
        "display_name": "Hybrid Full MV N=50",
        "run_template": "hybrid_fullmv_N50_alpha{}_run.tsv",
    },
    {
        "method": "budgetmv",
        "setting": "hybrid_budgetmv_N50_M24",
        "display_name": "Hybrid Budgeted MV N=50 M=24",
        "run_template": "hybrid_budgetmv_N50_M24_alpha{}_run.tsv",
    },
]

OUTPUT_ALL_CSV = OUTPUT_DIR / "hybrid_alpha_all_results.csv"
OUTPUT_TABLE_CSV = OUTPUT_DIR / "hybrid_alpha_ablation_table.csv"
OUTPUT_TABLE_MD = OUTPUT_DIR / "hybrid_alpha_ablation_table.md"
OUTPUT_BEST_CSV = OUTPUT_DIR / "hybrid_alpha_best_results.csv"
OUTPUT_BEST_JSON = OUTPUT_DIR / "hybrid_alpha_best_results.json"


def alpha_tag(alpha):
    return "{:.1f}".format(alpha).replace(".", "p")


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

            elif len(row) >= 5 and row[0].strip().lower().startswith(("bm25", "hybrid")):
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

        ideal_count = min(len(relevant), 10)
        ideal_rels = [1] * ideal_count
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


def format_float(x):
    return "{:.4f}".format(float(x))


def evaluate_all():
    qrels = load_qrels(QRELS_PATH)

    rows = []

    for config in METHOD_CONFIGS:
        for alpha in ALL_ALPHAS:
            tag = alpha_tag(alpha)
            run_path = HYBRID_DIR / config["run_template"].format(tag)

            if not run_path.exists():
                continue

            run = load_run(run_path)
            metrics = evaluate_run(run, qrels)

            rows.append(
                {
                    "Method": config["display_name"],
                    "Setting": config["setting"],
                    "Alpha": alpha,
                    "Recall@1": metrics["Recall@1"],
                    "Recall@5": metrics["Recall@5"],
                    "Recall@10": metrics["Recall@10"],
                    "MRR@10": metrics["MRR@10"],
                    "nDCG@10": metrics["nDCG@10"],
                    "Queries": metrics["Queries"],
                    "Run File": str(run_path.relative_to(PROJECT_ROOT)),
                }
            )

    return rows


def write_all_csv(rows):
    fieldnames = [
        "Method",
        "Setting",
        "Alpha",
        "Recall@1",
        "Recall@5",
        "Recall@10",
        "MRR@10",
        "nDCG@10",
        "Queries",
        "Run File",
    ]

    with OUTPUT_ALL_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for row in rows:
            out = dict(row)
            out["Alpha"] = "{:.1f}".format(row["Alpha"])

            for key in ["Recall@1", "Recall@5", "Recall@10", "MRR@10", "nDCG@10"]:
                out[key] = format_float(row[key])

            writer.writerow(out)


def write_ablation_table(rows):
    fieldnames = [
        "Method",
        "Alpha",
        "Recall@1",
        "Recall@5",
        "Recall@10",
        "nDCG@10",
    ]

    selected = []
    for row in rows:
        if row["Alpha"] in ALPHAS_FOR_TABLE:
            selected.append(row)

    with OUTPUT_TABLE_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for row in selected:
            writer.writerow(
                {
                    "Method": row["Method"],
                    "Alpha": "{:.1f}".format(row["Alpha"]),
                    "Recall@1": format_float(row["Recall@1"]),
                    "Recall@5": format_float(row["Recall@5"]),
                    "Recall@10": format_float(row["Recall@10"]),
                    "nDCG@10": format_float(row["nDCG@10"]),
                }
            )

    lines = []
    lines.append("# Week 7 Hybrid Fusion Alpha Ablation")
    lines.append("")

    for config in METHOD_CONFIGS:
        method_rows = [r for r in selected if r["Method"] == config["display_name"]]

        if not method_rows:
            continue

        lines.append("## {}".format(config["display_name"]))
        lines.append("")
        lines.append("| Alpha | Recall@1 | Recall@5 | Recall@10 | nDCG@10 |")
        lines.append("|---:|---:|---:|---:|---:|")

        for row in method_rows:
            lines.append(
                "| {} | {} | {} | {} | {} |".format(
                    "{:.1f}".format(row["Alpha"]),
                    format_float(row["Recall@1"]),
                    format_float(row["Recall@5"]),
                    format_float(row["Recall@10"]),
                    format_float(row["nDCG@10"]),
                )
            )

        lines.append("")

    OUTPUT_TABLE_MD.write_text("\n".join(lines), encoding="utf-8")


def write_best_results(rows):
    best_rows = []

    grouped = defaultdict(list)

    for row in rows:
        grouped[row["Method"]].append(row)

    for method, method_rows in grouped.items():
        best = sorted(
            method_rows,
            key=lambda r: (
                float(r["nDCG@10"]),
                float(r["MRR@10"]),
                float(r["Recall@10"]),
                float(r["Recall@5"]),
                float(r["Recall@1"]),
            ),
            reverse=True,
        )[0]

        best_rows.append(best)

    fieldnames = [
        "Method",
        "Setting",
        "Best Alpha",
        "Recall@1",
        "Recall@5",
        "Recall@10",
        "MRR@10",
        "nDCG@10",
        "Queries",
        "Run File",
    ]

    with OUTPUT_BEST_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for row in best_rows:
            writer.writerow(
                {
                    "Method": row["Method"],
                    "Setting": row["Setting"],
                    "Best Alpha": "{:.1f}".format(row["Alpha"]),
                    "Recall@1": format_float(row["Recall@1"]),
                    "Recall@5": format_float(row["Recall@5"]),
                    "Recall@10": format_float(row["Recall@10"]),
                    "MRR@10": format_float(row["MRR@10"]),
                    "nDCG@10": format_float(row["nDCG@10"]),
                    "Queries": row["Queries"],
                    "Run File": row["Run File"],
                }
            )

    json_rows = []
    for row in best_rows:
        json_rows.append(
            {
                "Method": row["Method"],
                "Setting": row["Setting"],
                "Best Alpha": row["Alpha"],
                "Recall@1": row["Recall@1"],
                "Recall@5": row["Recall@5"],
                "Recall@10": row["Recall@10"],
                "MRR@10": row["MRR@10"],
                "nDCG@10": row["nDCG@10"],
                "Queries": row["Queries"],
                "Run File": row["Run File"],
            }
        )

    with OUTPUT_BEST_JSON.open("w", encoding="utf-8") as f:
        json.dump(json_rows, f, indent=2, ensure_ascii=False)

    return best_rows


def print_results(rows, best_rows):
    print("")
    print("========== Hybrid Alpha All Results ==========")
    print("Method,Alpha,Recall@1,Recall@5,Recall@10,MRR@10,nDCG@10")

    for row in rows:
        print(
            "{},{},{},{},{},{},{}".format(
                row["Method"],
                "{:.1f}".format(row["Alpha"]),
                format_float(row["Recall@1"]),
                format_float(row["Recall@5"]),
                format_float(row["Recall@10"]),
                format_float(row["MRR@10"]),
                format_float(row["nDCG@10"]),
            )
        )

    print("")
    print("========== Hybrid Alpha Best Results ==========")
    print("Method,Best Alpha,Recall@1,Recall@5,Recall@10,MRR@10,nDCG@10")

    for row in best_rows:
        print(
            "{},{},{},{},{},{},{}".format(
                row["Method"],
                "{:.1f}".format(row["Alpha"]),
                format_float(row["Recall@1"]),
                format_float(row["Recall@5"]),
                format_float(row["Recall@10"]),
                format_float(row["MRR@10"]),
                format_float(row["nDCG@10"]),
            )
        )


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    rows = evaluate_all()

    write_all_csv(rows)
    write_ablation_table(rows)
    best_rows = write_best_results(rows)

    print_results(rows, best_rows)

    print("")
    print("Wrote CSV: {}".format(OUTPUT_ALL_CSV))
    print("Wrote CSV: {}".format(OUTPUT_TABLE_CSV))
    print("Wrote Markdown: {}".format(OUTPUT_TABLE_MD))
    print("Wrote CSV: {}".format(OUTPUT_BEST_CSV))
    print("Wrote JSON: {}".format(OUTPUT_BEST_JSON))


if __name__ == "__main__":
    main()
