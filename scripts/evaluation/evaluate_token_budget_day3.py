import argparse
from pathlib import Path

import numpy as np
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
        "--summary-dir",
        type=str,
        default="results/budgeted/token_selection/summary",
    )
    parser.add_argument(
        "--latency-file",
        type=str,
        default="results/budgeted/token_selection/summary/token_budget_day3_latency_by_M.csv",
    )
    parser.add_argument(
        "--full-mv-run",
        type=str,
        default="results/full_multivector/full_mv_run.tsv",
    )
    parser.add_argument(
        "--week4-c2f-run",
        type=str,
        default="results/budgeted/coarse_to_fine/c2f_single_vector_N10_run.tsv",
    )
    parser.add_argument(
        "--m-list",
        type=int,
        nargs="+",
        default=[8, 16, 24, 32, 49],
    )
    return parser.parse_args()


def normalize_qrels_columns(df):
    cols = list(df.columns)

    if {"query_id", "page_id"}.issubset(set(cols)):
        q_col = "query_id"
        d_col = "page_id"
    elif {"qid", "docid"}.issubset(set(cols)):
        q_col = "qid"
        d_col = "docid"
    elif len(cols) >= 2:
        q_col = cols[0]
        d_col = cols[1]
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
                    "page_id": str(r[d_col]),
                    "relevance": rel,
                }
            )

    return pd.DataFrame(rows)


def normalize_run_columns(df):
    cols = list(df.columns)

    if {"query_id", "page_id", "rank", "score"}.issubset(set(cols)):
        out = df[["query_id", "page_id", "rank", "score"]].copy()
    elif len(cols) >= 6:
        out = pd.DataFrame(
            {
                "query_id": df.iloc[:, 0],
                "page_id": df.iloc[:, 2],
                "rank": df.iloc[:, 3],
                "score": df.iloc[:, 4],
            }
        )
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
    out = out.sort_values(["query_id", "rank", "score"], ascending=[True, True, False])
    return out


def load_table_auto(path):
    path = Path(path)

    try:
        df = pd.read_csv(path, sep="\t")
        if len(df.columns) > 1:
            return df
    except Exception:
        pass

    try:
        df = pd.read_csv(path, sep="\t", header=None)
        if len(df.columns) > 1:
            return df
    except Exception:
        pass

    try:
        df = pd.read_csv(path)
        return df
    except Exception as e:
        raise RuntimeError(f"Failed to read {path}: {e}")


def evaluate_run(run_df, qrels_df, k=10):
    rel_map = {}
    for qid, group in qrels_df.groupby("query_id"):
        rel_map[qid] = set(group["page_id"].astype(str).tolist())

    query_ids = sorted(rel_map.keys())

    recall1 = []
    recall5 = []
    recall10 = []
    mrr10 = []
    ndcg10 = []

    for qid in query_ids:
        rel_docs = rel_map[qid]
        ranking = run_df[run_df["query_id"] == qid].sort_values("rank")
        docs = ranking["page_id"].astype(str).tolist()

        top1 = docs[:1]
        top5 = docs[:5]
        top10 = docs[:10]

        hit1 = int(any(d in rel_docs for d in top1))
        hit5 = int(any(d in rel_docs for d in top5))
        hit10 = int(any(d in rel_docs for d in top10))

        recall1.append(hit1)
        recall5.append(hit5)
        recall10.append(hit10)

        rr = 0.0
        for i, d in enumerate(top10, start=1):
            if d in rel_docs:
                rr = 1.0 / i
                break
        mrr10.append(rr)

        dcg = 0.0
        for i, d in enumerate(top10, start=1):
            if d in rel_docs:
                dcg += 1.0 / np.log2(i + 1)

        ideal_hits = min(len(rel_docs), 10)
        idcg = sum(1.0 / np.log2(i + 1) for i in range(1, ideal_hits + 1))
        ndcg = dcg / idcg if idcg > 0 else 0.0
        ndcg10.append(ndcg)

    return {
        "Evaluated Queries": len(query_ids),
        "Recall@1": float(np.mean(recall1)) if recall1 else 0.0,
        "Recall@5": float(np.mean(recall5)) if recall5 else 0.0,
        "Recall@10": float(np.mean(recall10)) if recall10 else 0.0,
        "MRR@10": float(np.mean(mrr10)) if mrr10 else 0.0,
        "nDCG@10": float(np.mean(ndcg10)) if ndcg10 else 0.0,
    }


def try_eval_named_run(name, path, qrels_df, m_value=None):
    path = Path(path)
    if not path.exists():
        return None

    df = load_table_auto(path)
    run_df = normalize_run_columns(df)
    metrics = evaluate_run(run_df, qrels_df)

    row = {
        "Method": name,
        "M": m_value if m_value is not None else "",
        **metrics,
        "Run File": str(path),
    }
    return row


def main():
    args = parse_args()

    qrels_path = Path(args.qrels)
    run_dir = Path(args.run_dir)
    summary_dir = Path(args.summary_dir)
    summary_dir.mkdir(parents=True, exist_ok=True)

    qrels_raw = load_table_auto(qrels_path)
    qrels_df = normalize_qrels_columns(qrels_raw)

    rows = []

    full_row = try_eval_named_run(
        "Full Multi-vector",
        args.full_mv_run,
        qrels_df,
        m_value="full",
    )
    if full_row is not None:
        rows.append(full_row)

    week4_row = try_eval_named_run(
        "Week4 C2F N10",
        args.week4_c2f_run,
        qrels_df,
        m_value="49",
    )
    if week4_row is not None:
        rows.append(week4_row)

    for m in args.m_list:
        run_path = run_dir / f"c2f_N10_M{m}_run.tsv"
        row = try_eval_named_run(
            f"C2F N10 M{m}",
            run_path,
            qrels_df,
            m_value=m,
        )
        if row is not None:
            rows.append(row)

    metrics_df = pd.DataFrame(rows)

    latency_path = Path(args.latency_file)
    if latency_path.exists():
        latency_df = pd.read_csv(latency_path)
        latency_df = latency_df.rename(columns={"Per-query Latency ms": "Latency ms/query"})

        metrics_df = metrics_df.merge(
            latency_df[["M", "Latency ms/query", "Avg Candidates / Query"]],
            on="M",
            how="left",
        )

    metrics_csv = summary_dir / "token_budget_metrics.csv"
    metrics_xlsx = summary_dir / "token_budget_metrics.xlsx"
    comparison_md = summary_dir / "token_budget_initial_comparison.md"

    metrics_df.to_csv(metrics_csv, index=False)
    metrics_df.to_excel(metrics_xlsx, index=False)

    with open(comparison_md, "w", encoding="utf-8") as f:
        f.write("# Week 5 Day 3 Token Budget Initial Comparison\n\n")
        f.write(metrics_df.to_markdown(index=False))
        f.write("\n")

    print("[Done] Token budget evaluation completed.")
    print(f"[Output] {metrics_csv}")
    print(f"[Output] {metrics_xlsx}")
    print(f"[Output] {comparison_md}")
    print(metrics_df)


if __name__ == "__main__":
    main()
