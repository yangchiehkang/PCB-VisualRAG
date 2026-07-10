import argparse
from pathlib import Path

import pandas as pd


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--qrels",
        type=str,
        default="data/metadata/qrels.tsv",
    )

    parser.add_argument(
        "--run-dir",
        type=str,
        default="results/budgeted/token_selection",
    )

    parser.add_argument(
        "--quality-cost-file",
        type=str,
        default="results/budgeted/token_selection/day4_cost_analysis/day4_quality_cost_table.csv",
    )

    parser.add_argument(
        "--page-type-file",
        type=str,
        default="results/budgeted/token_selection/day5_redundancy_analysis/day5_page_type_annotations.csv",
    )

    parser.add_argument(
        "--query-type-file",
        type=str,
        default="results/budgeted/token_selection/day5_redundancy_analysis/day5_query_type_annotations.csv",
    )

    parser.add_argument(
        "--output-dir",
        type=str,
        default="results/budgeted/token_selection/day5_redundancy_analysis",
    )

    parser.add_argument(
        "--m-list",
        type=int,
        nargs="+",
        default=[8, 16, 24, 32, 49],
    )

    return parser.parse_args()


def load_table_auto(path):
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    try:
        df = pd.read_csv(path, sep="\t")
        if len(df.columns) > 1:
            return df
    except Exception:
        pass

    try:
        df = pd.read_csv(path)
        if len(df.columns) > 1:
            return df
    except Exception:
        pass

    try:
        return pd.read_csv(path, sep="\t", header=None)
    except Exception as e:
        raise RuntimeError(f"Failed to read {path}: {e}")


def normalize_qrels(df):
    cols = list(df.columns)

    if {"query_id", "page_id"}.issubset(set(cols)):
        q_col = "query_id"
        p_col = "page_id"
    elif {"qid", "docid"}.issubset(set(cols)):
        q_col = "qid"
        p_col = "docid"
    elif len(cols) >= 2:
        q_col = cols[0]
        p_col = cols[1]
    else:
        raise ValueError(f"Cannot parse qrels columns: {cols}")

    if "relevance" in cols:
        rel_col = "relevance"
    elif "rel" in cols:
        rel_col = "rel"
    elif len(cols) >= 3:
        rel_col = cols[2]
    else:
        rel_col = None

    rows = []

    for _, r in df.iterrows():
        rel = 1 if rel_col is None else r[rel_col]

        try:
            rel = float(rel)
        except Exception:
            rel = 1

        if rel > 0:
            rows.append(
                {
                    "query_id": str(r[q_col]),
                    "page_id": str(r[p_col]),
                    "relevance": rel,
                }
            )

    return pd.DataFrame(rows)


def normalize_run(df):
    cols = list(df.columns)

    if {"query_id", "page_id", "rank", "score"}.issubset(set(cols)):
        out = df[["query_id", "page_id", "rank", "score"]].copy()
    elif len(cols) >= 4:
        out = pd.DataFrame(
            {
                "query_id": df.iloc[:, 0],
                "page_id": df.iloc[:, 1],
                "rank": df.iloc[:, 2],
                "score": df.iloc[:, 3],
            }
        )
    else:
        raise ValueError(f"Cannot parse run columns: {cols}")

    out["query_id"] = out["query_id"].astype(str)
    out["page_id"] = out["page_id"].astype(str)
    out["rank"] = pd.to_numeric(out["rank"], errors="coerce")
    out["score"] = pd.to_numeric(out["score"], errors="coerce")

    return out.sort_values(["query_id", "rank"])


def create_page_type_template(qrels_df, page_type_file):
    page_type_file = Path(page_type_file)
    page_type_file.parent.mkdir(parents=True, exist_ok=True)

    pages = sorted(qrels_df["page_id"].astype(str).unique())

    df = pd.DataFrame(
        {
            "page_id": pages,
            "page_type": "",
            "notes": "",
        }
    )

    df.to_csv(page_type_file, index=False, encoding="utf-8-sig")

    return df


def create_query_type_template(qrels_df, query_type_file):
    query_type_file = Path(query_type_file)
    query_type_file.parent.mkdir(parents=True, exist_ok=True)

    queries = sorted(qrels_df["query_id"].astype(str).unique())

    df = pd.DataFrame(
        {
            "query_id": queries,
            "query_type": "",
            "main_evidence": "",
            "notes": "",
        }
    )

    df.to_csv(query_type_file, index=False, encoding="utf-8-sig")

    return df


def load_or_create_annotations(qrels_df, page_type_file, query_type_file):
    page_type_file = Path(page_type_file)
    query_type_file = Path(query_type_file)

    if page_type_file.exists():
        page_df = pd.read_csv(page_type_file)
    else:
        page_df = create_page_type_template(qrels_df, page_type_file)

    if query_type_file.exists():
        query_df = pd.read_csv(query_type_file)
    else:
        query_df = create_query_type_template(qrels_df, query_type_file)

    page_df["page_id"] = page_df["page_id"].astype(str)
    query_df["query_id"] = query_df["query_id"].astype(str)

    if "page_type" not in page_df.columns:
        page_df["page_type"] = ""

    if "query_type" not in query_df.columns:
        query_df["query_type"] = ""

    page_df["page_type"] = page_df["page_type"].fillna("").replace("", "Unlabeled")
    query_df["query_type"] = query_df["query_type"].fillna("").replace("", "Unlabeled")

    return page_df, query_df


def evaluate_by_group(run_df, qrels_df, group_df, group_col, join_col):
    rel_map = {}

    for qid, g in qrels_df.groupby("query_id"):
        rel_map[str(qid)] = set(g["page_id"].astype(str).tolist())

    rows = []

    merged_qrels = qrels_df.merge(group_df[[join_col, group_col]], on=join_col, how="left")
    merged_qrels[group_col] = merged_qrels[group_col].fillna("Unlabeled")

    for group_name, group_qrels in merged_qrels.groupby(group_col):
        query_ids = sorted(group_qrels["query_id"].astype(str).unique())

        hit10_values = []
        mrr10_values = []

        for qid in query_ids:
            rel_docs_for_group = set(
                group_qrels[group_qrels["query_id"].astype(str) == qid]["page_id"].astype(str).tolist()
            )

            ranking = run_df[run_df["query_id"].astype(str) == qid].sort_values("rank")
            top10 = ranking["page_id"].astype(str).tolist()[:10]

            hit10 = int(any(d in rel_docs_for_group for d in top10))
            hit10_values.append(hit10)

            rr = 0.0
            for idx, docid in enumerate(top10, start=1):
                if docid in rel_docs_for_group:
                    rr = 1.0 / idx
                    break
            mrr10_values.append(rr)

        rows.append(
            {
                group_col: group_name,
                "Evaluated Queries": len(query_ids),
                "Recall@10": sum(hit10_values) / len(hit10_values) if hit10_values else 0.0,
                "MRR@10": sum(mrr10_values) / len(mrr10_values) if mrr10_values else 0.0,
            }
        )

    return pd.DataFrame(rows)


def main():
    args = parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    qrels_raw = load_table_auto(args.qrels)
    qrels_df = normalize_qrels(qrels_raw)

    page_df, query_df = load_or_create_annotations(
        qrels_df=qrels_df,
        page_type_file=args.page_type_file,
        query_type_file=args.query_type_file,
    )

    page_type_all_rows = []
    query_type_all_rows = []

    run_dir = Path(args.run_dir)

    for m in args.m_list:
        run_path = run_dir / f"c2f_N10_M{m}_run.tsv"

        if not run_path.exists():
            print(f"[Warning] Run file not found, skipped: {run_path}")
            continue

        run_raw = load_table_auto(run_path)
        run_df = normalize_run(run_raw)

        page_eval = evaluate_by_group(
            run_df=run_df,
            qrels_df=qrels_df,
            group_df=page_df,
            group_col="page_type",
            join_col="page_id",
        )

        page_eval["M"] = m
        page_type_all_rows.append(page_eval)

        qrels_with_query_type = qrels_df.merge(
            query_df[["query_id", "query_type"]],
            on="query_id",
            how="left",
        )
        qrels_with_query_type["query_type"] = qrels_with_query_type["query_type"].fillna("Unlabeled")

        query_eval_rows = []

        for query_type, g in qrels_with_query_type.groupby("query_type"):
            sub_qrels = g[["query_id", "page_id", "relevance"]].copy()

            rel_map = {}
            for qid, qg in sub_qrels.groupby("query_id"):
                rel_map[str(qid)] = set(qg["page_id"].astype(str).tolist())

            hit10_values = []
            mrr10_values = []

            for qid, rel_docs in rel_map.items():
                ranking = run_df[run_df["query_id"].astype(str) == qid].sort_values("rank")
                top10 = ranking["page_id"].astype(str).tolist()[:10]

                hit10 = int(any(d in rel_docs for d in top10))
                hit10_values.append(hit10)

                rr = 0.0
                for idx, docid in enumerate(top10, start=1):
                    if docid in rel_docs:
                        rr = 1.0 / idx
                        break
                mrr10_values.append(rr)

            query_eval_rows.append(
                {
                    "query_type": query_type,
                    "Evaluated Queries": len(rel_map),
                    "Recall@10": sum(hit10_values) / len(hit10_values) if hit10_values else 0.0,
                    "MRR@10": sum(mrr10_values) / len(mrr10_values) if mrr10_values else 0.0,
                    "M": m,
                }
            )

        query_type_all_rows.append(pd.DataFrame(query_eval_rows))

    page_type_result = pd.concat(page_type_all_rows, ignore_index=True) if page_type_all_rows else pd.DataFrame()
    query_type_result = pd.concat(query_type_all_rows, ignore_index=True) if query_type_all_rows else pd.DataFrame()

    page_csv = output_dir / "day5_page_type_sensitivity.csv"
    query_csv = output_dir / "day5_query_type_sensitivity.csv"
    page_best_csv = output_dir / "day5_page_type_best_m.csv"
    query_best_csv = output_dir / "day5_query_type_best_m.csv"
    md_path = output_dir / "day5_type_sensitivity_summary.md"

    page_type_result.to_csv(page_csv, index=False, encoding="utf-8-sig")
    query_type_result.to_csv(query_csv, index=False, encoding="utf-8-sig")

    if not page_type_result.empty:
        page_best = (
            page_type_result.sort_values(["page_type", "Recall@10", "MRR@10"], ascending=[True, False, False])
            .groupby("page_type")
            .head(1)
            .reset_index(drop=True)
        )
    else:
        page_best = pd.DataFrame()

    if not query_type_result.empty:
        query_best = (
            query_type_result.sort_values(["query_type", "Recall@10", "MRR@10"], ascending=[True, False, False])
            .groupby("query_type")
            .head(1)
            .reset_index(drop=True)
        )
    else:
        query_best = pd.DataFrame()

    page_best.to_csv(page_best_csv, index=False, encoding="utf-8-sig")
    query_best.to_csv(query_best_csv, index=False, encoding="utf-8-sig")

    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# Week 5 Day 5 Type Sensitivity Summary\n\n")

        f.write("## 1. Annotation Files\n\n")
        f.write(f"- Page type annotation: `{args.page_type_file}`\n")
        f.write(f"- Query type annotation: `{args.query_type_file}`\n\n")

        f.write("If the above annotation files were newly created, fill page_type and query_type first, then rerun this script.\n\n")

        f.write("## 2. Page Type Best M\n\n")
        if not page_best.empty:
            f.write("| Page Type | Best M | Evaluated Queries | Recall@10 | MRR@10 |\n")
            f.write("|---|---:|---:|---:|---:|\n")
            for _, r in page_best.iterrows():
                f.write(
                    f"| {r['page_type']} | {int(r['M'])} | {int(r['Evaluated Queries'])} "
                    f"| {r['Recall@10']:.4f} | {r['MRR@10']:.4f} |\n"
                )
        else:
            f.write("No page type result available.\n")

        f.write("\n## 3. Query Type Best M\n\n")
        if not query_best.empty:
            f.write("| Query Type | Best M | Evaluated Queries | Recall@10 | MRR@10 |\n")
            f.write("|---|---:|---:|---:|---:|\n")
            for _, r in query_best.iterrows():
                f.write(
                    f"| {r['query_type']} | {int(r['M'])} | {int(r['Evaluated Queries'])} "
                    f"| {r['Recall@10']:.4f} | {r['MRR@10']:.4f} |\n"
                )
        else:
            f.write("No query type result available.\n")

    print("[Done] Day 5 type sensitivity analysis completed.")
    print(f"[Output] {page_csv}")
    print(f"[Output] {query_csv}")
    print(f"[Output] {page_best_csv}")
    print(f"[Output] {query_best_csv}")
    print(f"[Output] {md_path}")
    print(f"[Annotation] {args.page_type_file}")
    print(f"[Annotation] {args.query_type_file}")


if __name__ == "__main__":
    main()
