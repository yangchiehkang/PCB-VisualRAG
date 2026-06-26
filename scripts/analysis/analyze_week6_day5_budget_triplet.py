from pathlib import Path
import json
import numpy as np
import pandas as pd


JOINT_RESULTS = Path("results/budgeted/joint_compression/summary/joint_budget_results.csv")
BITS_RESULTS = Path("results/budgeted/joint_compression/day5_analysis/day5_bits_sweep_results.csv")

QRELS_FILE = Path("data/metadata/qrels.tsv")
CANDIDATE_FILE = Path("artifacts/rerank_cache/single_vector_topN/single_vector_candidates_top10.tsv")
RUN_DIR = Path("results/budgeted/joint_compression/runs")

OUT_DIR = Path("results/budgeted/joint_compression/day5_analysis")
OUT_DIR.mkdir(parents=True, exist_ok=True)


def safe_to_markdown(df: pd.DataFrame, path: Path):
    try:
        text = df.to_markdown(index=False)
    except Exception:
        text = df.to_string(index=False)

    with path.open("w", encoding="utf-8") as f:
        f.write(text)
        f.write("\n")


def normalize_id(x) -> str:
    if pd.isna(x):
        return ""
    return str(x).strip().strip('"').strip("'")


def normalize_compression(x) -> str:
    s = normalize_id(x)

    if s == "" or s.lower() in ["nan", "none"]:
        return "None"

    return s


def load_qrels(path: Path) -> dict:
    df = pd.read_csv(path, sep="\t", header=None, dtype=str)

    first_col = df.iloc[:, 0].astype(str).str.lower()
    df = df[(first_col != "query_id") & (first_col != "qid")].copy()

    if df.shape[1] >= 4:
        df = df.iloc[:, :4]
        df.columns = ["query_id", "unused", "page_id", "rel"]
    elif df.shape[1] == 3:
        df.columns = ["query_id", "page_id", "rel"]
    elif df.shape[1] == 2:
        df.columns = ["query_id", "page_id"]
        df["rel"] = 1
    else:
        raise ValueError(f"Unsupported qrels format: {path}")

    df["query_id"] = df["query_id"].astype(str).str.strip()
    df["page_id"] = df["page_id"].astype(str).str.strip()
    df["rel"] = pd.to_numeric(df["rel"], errors="coerce").fillna(1).astype(float)
    df = df[df["rel"] > 0].copy()

    qrels = {}
    for qid, group in df.groupby("query_id"):
        qrels[str(qid)] = set(group["page_id"].astype(str).tolist())

    return qrels


def is_header_like_row(row: pd.Series) -> bool:
    values = [normalize_id(v).lower() for v in row.tolist()]
    return (
        "query_id" in values
        or "qid" in values
        or "page_id" in values
        or "docid" in values
        or "rank" in values
    )


def load_candidates(path: Path) -> pd.DataFrame:
    raw = pd.read_csv(path, sep="\t", header=None, dtype=str)
    raw = raw[~raw.apply(is_header_like_row, axis=1)].copy()
    raw = raw.dropna(how="all").copy()

    if raw.shape[1] >= 6:
        df = raw.iloc[:, :6].copy()
        df.columns = ["query_id", "Q0", "page_id", "rank", "coarse_score", "tag"]
    elif raw.shape[1] == 5:
        df = raw.copy()
        df.columns = ["query_id", "page_id", "rank", "coarse_score", "tag"]
        df["Q0"] = "Q0"
    elif raw.shape[1] == 4:
        df = raw.copy()
        df.columns = ["query_id", "page_id", "rank", "coarse_score"]
        df["Q0"] = "Q0"
        df["tag"] = "candidate"
    elif raw.shape[1] == 3:
        df = raw.copy()
        df.columns = ["query_id", "page_id", "coarse_score"]
        df["rank"] = df.groupby("query_id").cumcount() + 1
        df["Q0"] = "Q0"
        df["tag"] = "candidate"
    else:
        raise ValueError(f"Unsupported candidate file: {path}")

    df["query_id"] = df["query_id"].apply(normalize_id)
    df["page_id"] = df["page_id"].apply(normalize_id)
    df["rank"] = pd.to_numeric(df["rank"], errors="coerce").fillna(999999).astype(int)
    df["coarse_score"] = pd.to_numeric(df["coarse_score"], errors="coerce").fillna(0.0)

    df = df[(df["query_id"] != "") & (df["page_id"] != "")].copy()
    df = df[df["query_id"].str.lower() != "query_id"].copy()
    df = df[df["page_id"].str.lower() != "page_id"].copy()

    return df.sort_values(["query_id", "rank"]).reset_index(drop=True)


def load_run(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame(columns=["query_id", "Q0", "page_id", "rank", "score", "tag"])

    df = pd.read_csv(path, sep="\t", header=None, dtype=str)

    if df.empty:
        return pd.DataFrame(columns=["query_id", "Q0", "page_id", "rank", "score", "tag"])

    if df.shape[1] >= 6:
        df = df.iloc[:, :6]
        df.columns = ["query_id", "Q0", "page_id", "rank", "score", "tag"]
    elif df.shape[1] == 5:
        df.columns = ["query_id", "page_id", "rank", "score", "tag"]
        df["Q0"] = "Q0"
    else:
        raise ValueError(f"Unsupported run file format: {path}")

    df["query_id"] = df["query_id"].astype(str).str.strip()
    df["page_id"] = df["page_id"].astype(str).str.strip()
    df["rank"] = pd.to_numeric(df["rank"], errors="coerce").fillna(999999).astype(int)
    df["score"] = pd.to_numeric(df["score"], errors="coerce").fillna(0.0)

    return df


def recall_at_k(ranked_docs, rel_docs, k: int) -> float:
    return 1.0 if any(doc in rel_docs for doc in ranked_docs[:k]) else 0.0


def rr_at_k(ranked_docs, rel_docs, k: int) -> float:
    for idx, doc in enumerate(ranked_docs[:k], start=1):
        if doc in rel_docs:
            return 1.0 / idx
    return 0.0


def ndcg_at_k(ranked_docs, rel_docs, k: int) -> float:
    dcg = 0.0

    for idx, doc in enumerate(ranked_docs[:k], start=1):
        rel = 1.0 if doc in rel_docs else 0.0
        dcg += rel / np.log2(idx + 1)

    ideal_hits = min(len(rel_docs), k)
    idcg = sum(1.0 / np.log2(idx + 1) for idx in range(1, ideal_hits + 1))

    return float(dcg / idcg) if idcg > 0 else 0.0


def first_rel_rank(ranked_docs, rel_docs, k: int = 10):
    for idx, doc in enumerate(ranked_docs[:k], start=1):
        if doc in rel_docs:
            return idx
    return None


def per_query_metrics_for_run(run_name: str, qrels: dict) -> pd.DataFrame:
    run_path = RUN_DIR / f"{run_name}_run.tsv"
    run_df = load_run(run_path)

    rows = []

    for qid, rel_docs in qrels.items():
        sub = run_df[run_df["query_id"] == qid].sort_values("rank")
        ranked = sub["page_id"].tolist() if not sub.empty else []

        rows.append({
            "run_name": run_name,
            "query_id": qid,
            "hit@10": recall_at_k(ranked, rel_docs, 10),
            "rr@10": rr_at_k(ranked, rel_docs, 10),
            "ndcg@10": ndcg_at_k(ranked, rel_docs, 10),
            "first_rel_rank": first_rel_rank(ranked, rel_docs, 10),
            "num_returned": len(ranked),
        })

    return pd.DataFrame(rows)


def build_per_query_table(results: pd.DataFrame, qrels: dict) -> pd.DataFrame:
    all_rows = []

    for _, row in results.iterrows():
        run_name = row["run_name"]

        pq = per_query_metrics_for_run(run_name, qrels)
        pq["N"] = row["N"]
        pq["M"] = row["M"]
        pq["Compression"] = row["Compression"]
        pq["Index Size MB"] = row["Index Size MB"]
        pq["Latency ms/query"] = row["Latency ms/query"]

        all_rows.append(pq)

    if not all_rows:
        return pd.DataFrame()

    return pd.concat(all_rows, ignore_index=True)


def compute_coarse_ceiling(candidates: pd.DataFrame, qrels: dict) -> pd.DataFrame:
    rows = []

    for qid, rel_docs in qrels.items():
        sub = candidates[candidates["query_id"] == qid].sort_values("rank")
        candidate_docs = sub["page_id"].tolist()

        gold_in_candidates = any(doc in rel_docs for doc in candidate_docs)
        gold_rank = first_rel_rank(candidate_docs, rel_docs, 10)

        rows.append({
            "query_id": qid,
            "candidate_count": len(candidate_docs),
            "gold_in_top10_candidates": bool(gold_in_candidates),
            "gold_candidate_rank": gold_rank,
            "coarse_recall_ceiling@10": 1.0 if gold_in_candidates else 0.0,
        })

    return pd.DataFrame(rows)


def make_dimension_impact_table(results: pd.DataFrame, bits_results: pd.DataFrame | None) -> pd.DataFrame:
    rows = []

    rows.append({
        "Budget Dimension": "N",
        "Current Evidence": "N fixed at 10 in Day 3 because available candidate file is top10.",
        "Observed Risk": "Coarse-stage recall ceiling is controlled by whether gold pages enter the candidate pool.",
        "Analysis Focus": "Use candidate-level gold coverage as N sensitivity proxy.",
        "Current Conclusion": "N is the first-order budget because missed gold pages cannot be recovered by reranking.",
    })

    none_df = results[results["Compression"] == "None"].copy()

    if not none_df.empty:
        best_m = none_df.sort_values("nDCG@10", ascending=False).iloc[0]
        m_range = f"M values tested: {sorted(none_df['M'].unique().tolist())}"
        m_conclusion = f"Best uncompressed M point is M={int(best_m['M'])}, nDCG@10={best_m['nDCG@10']:.6f}."
    else:
        m_range = "No uncompressed M results found."
        m_conclusion = "Unavailable."

    rows.append({
        "Budget Dimension": "M",
        "Current Evidence": m_range,
        "Observed Risk": "Small M may remove fine-grained local evidence.",
        "Analysis Focus": "Compare per-query nDCG changes across M8, M16, M24.",
        "Current Conclusion": m_conclusion,
    })

    if bits_results is not None and not bits_results.empty:
        b = bits_results.sort_values("bits")
        best_bits = b.sort_values("nDCG@10", ascending=False).iloc[0]
        bits_text = "bits tested: " + ", ".join(str(int(x)) for x in b["bits"].tolist())
        bits_conclusion = (
            f"Best bits setting is b={int(best_bits['bits'])}, "
            f"nDCG@10={best_bits['nDCG@10']:.6f}."
        )
    else:
        bits_text = "No Day 5 bits sweep found."
        bits_conclusion = "Run day5 bits sweep before finalizing bits conclusion."

    rows.append({
        "Budget Dimension": "bits",
        "Current Evidence": bits_text,
        "Observed Risk": "Low bits may distort similarity ranking.",
        "Analysis Focus": "Compare PQ-b2, PQ-b4, PQ-b8 at fixed N=10 and M=24.",
        "Current Conclusion": bits_conclusion,
    })

    return pd.DataFrame(rows)


def make_m_group_summary(results: pd.DataFrame) -> pd.DataFrame:
    rows = []

    for m, group in results.groupby("M"):
        best = group.sort_values(["nDCG@10", "MRR@10"], ascending=[False, False]).iloc[0]
        lowest_cost = group.sort_values(["Index Size MB", "Latency ms/query"], ascending=[True, True]).iloc[0]

        none = group[group["Compression"] == "None"]
        none_ndcg = float(none["nDCG@10"].iloc[0]) if not none.empty else None

        rows.append({
            "M": int(m),
            "Best Quality Run": best["run_name"],
            "Best Quality Compression": best["Compression"],
            "Best nDCG@10": best["nDCG@10"],
            "Best MRR@10": best["MRR@10"],
            "Best Index Size MB": best["Index Size MB"],
            "Best Latency ms/query": best["Latency ms/query"],
            "Lowest Cost Run": lowest_cost["run_name"],
            "Lowest Cost Compression": lowest_cost["Compression"],
            "Lowest Cost Index Size MB": lowest_cost["Index Size MB"],
            "None nDCG@10": none_ndcg,
        })

    return pd.DataFrame(rows)


def make_compression_delta_summary(results: pd.DataFrame) -> pd.DataFrame:
    rows = []

    for m, group in results.groupby("M"):
        none = group[group["Compression"] == "None"]

        if none.empty:
            continue

        base = none.iloc[0]

        for _, row in group.iterrows():
            if row["Compression"] == "None":
                continue

            rows.append({
                "M": int(m),
                "Compression": row["Compression"],
                "run_name": row["run_name"],
                "Delta Recall@10 vs None": row["Recall@10"] - base["Recall@10"],
                "Delta MRR@10 vs None": row["MRR@10"] - base["MRR@10"],
                "Delta nDCG@10 vs None": row["nDCG@10"] - base["nDCG@10"],
                "Index Size Ratio vs None": row["Index Size MB"] / base["Index Size MB"] if base["Index Size MB"] > 0 else None,
                "Latency Delta ms/query vs None": row["Latency ms/query"] - base["Latency ms/query"],
            })

    return pd.DataFrame(rows)


def make_m_query_sensitivity(per_query: pd.DataFrame) -> pd.DataFrame:
    none = per_query[per_query["Compression"] == "None"].copy()

    if none.empty:
        return pd.DataFrame()

    pivot = none.pivot_table(
        index="query_id",
        columns="M",
        values=["hit@10", "rr@10", "ndcg@10"],
        aggfunc="first",
    )

    pivot.columns = [f"{metric}_M{int(m)}" for metric, m in pivot.columns]
    pivot = pivot.reset_index()

    for col in ["ndcg@10_M8", "ndcg@10_M16", "ndcg@10_M24"]:
        if col not in pivot.columns:
            pivot[col] = np.nan

    pivot["delta_ndcg_M24_minus_M8"] = pivot["ndcg@10_M24"] - pivot["ndcg@10_M8"]
    pivot["delta_ndcg_M24_minus_M16"] = pivot["ndcg@10_M24"] - pivot["ndcg@10_M16"]

    pivot["M_sensitivity_type"] = "stable"
    pivot.loc[pivot["delta_ndcg_M24_minus_M8"] > 0.05, "M_sensitivity_type"] = "benefits_from_larger_M"
    pivot.loc[pivot["delta_ndcg_M24_minus_M8"] < -0.05, "M_sensitivity_type"] = "worse_with_larger_M"

    return pivot.sort_values("delta_ndcg_M24_minus_M8", ascending=False)


def make_quantization_query_sensitivity(per_query: pd.DataFrame) -> pd.DataFrame:
    rows = []

    for m in sorted(per_query["M"].dropna().unique()):
        sub = per_query[per_query["M"] == m].copy()
        base = sub[sub["Compression"] == "None"].copy()

        if base.empty:
            continue

        base = base[["query_id", "hit@10", "rr@10", "ndcg@10"]].rename(columns={
            "hit@10": "none_hit@10",
            "rr@10": "none_rr@10",
            "ndcg@10": "none_ndcg@10",
        })

        for comp in sorted(sub["Compression"].unique()):
            if comp == "None":
                continue

            comp_df = sub[sub["Compression"] == comp][["query_id", "hit@10", "rr@10", "ndcg@10", "run_name"]].copy()
            comp_df = comp_df.rename(columns={
                "hit@10": "compressed_hit@10",
                "rr@10": "compressed_rr@10",
                "ndcg@10": "compressed_ndcg@10",
            })

            merged = base.merge(comp_df, on="query_id", how="left")
            merged["M"] = int(m)
            merged["Compression"] = comp
            merged["delta_hit@10"] = merged["compressed_hit@10"] - merged["none_hit@10"]
            merged["delta_rr@10"] = merged["compressed_rr@10"] - merged["none_rr@10"]
            merged["delta_ndcg@10"] = merged["compressed_ndcg@10"] - merged["none_ndcg@10"]
            merged["quantization_sensitivity_type"] = "stable"
            merged.loc[merged["delta_ndcg@10"] <= -0.05, "quantization_sensitivity_type"] = "hurt_by_quantization"
            merged.loc[merged["delta_ndcg@10"] >= 0.05, "quantization_sensitivity_type"] = "improved_by_quantization"

            rows.append(merged)

    if not rows:
        return pd.DataFrame()

    return pd.concat(rows, ignore_index=True).sort_values("delta_ndcg@10")


def make_bits_sensitivity(bits_results: pd.DataFrame | None) -> pd.DataFrame:
    if bits_results is None or bits_results.empty:
        return pd.DataFrame()

    df = bits_results.copy()
    df["Compression"] = df["Compression"].apply(normalize_compression)

    for col in ["bits", "Recall@10", "MRR@10", "nDCG@10", "Index Size MB", "MSE", "MAE", "Latency ms/query"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    b4 = df[df["bits"] == 4]

    if not b4.empty:
        base = b4.iloc[0]
        df["Delta nDCG@10 vs b4"] = df["nDCG@10"] - base["nDCG@10"]
        df["Delta MRR@10 vs b4"] = df["MRR@10"] - base["MRR@10"]
        df["Index Size Ratio vs b4"] = df["Index Size MB"] / base["Index Size MB"]
        df["MSE Ratio vs b4"] = df["MSE"] / base["MSE"] if base["MSE"] > 0 else np.nan
    else:
        df["Delta nDCG@10 vs b4"] = np.nan
        df["Delta MRR@10 vs b4"] = np.nan
        df["Index Size Ratio vs b4"] = np.nan
        df["MSE Ratio vs b4"] = np.nan

    return df.sort_values("bits")


def make_failure_cases(
    results: pd.DataFrame,
    per_query: pd.DataFrame,
    coarse_ceiling: pd.DataFrame,
    m_sensitivity: pd.DataFrame,
    quant_sensitivity: pd.DataFrame,
) -> pd.DataFrame:
    rows = []

    coarse_miss = coarse_ceiling[coarse_ceiling["gold_in_top10_candidates"] == False].copy()

    for _, row in coarse_miss.iterrows():
        rows.append({
            "failure_type": "small_N_or_coarse_miss",
            "query_id": row["query_id"],
            "evidence_run": "single_vector_candidates_top10",
            "evidence": "gold page not found in top10 candidate pool",
            "possible_cause": "coarse retrieval did not recall gold page",
            "analysis_value": "shows N controls recall ceiling",
        })

    if not m_sensitivity.empty:
        small_m_fail = m_sensitivity[m_sensitivity["delta_ndcg_M24_minus_M8"] > 0.05].copy()

        for _, row in small_m_fail.head(20).iterrows():
            rows.append({
                "failure_type": "small_M_failure",
                "query_id": row["query_id"],
                "evidence_run": "None M8 vs None M24",
                "evidence": f"delta_ndcg_M24_minus_M8={row['delta_ndcg_M24_minus_M8']:.6f}",
                "possible_cause": "small token budget may remove local matching evidence",
                "analysis_value": "shows M controls fine-grained evidence retention",
            })

    if not quant_sensitivity.empty:
        quant_fail = quant_sensitivity[quant_sensitivity["delta_ndcg@10"] <= -0.05].copy()

        for _, row in quant_fail.head(30).iterrows():
            rows.append({
                "failure_type": "quantization_ranking_distortion",
                "query_id": row["query_id"],
                "evidence_run": row.get("run_name", ""),
                "evidence": f"M={row['M']}, Compression={row['Compression']}, delta_ndcg={row['delta_ndcg@10']:.6f}",
                "possible_cause": "quantization changed fine-grained similarity ranking",
                "analysis_value": "shows bits/compression controls ranking fidelity",
            })

    best = results.sort_values(["nDCG@10", "MRR@10"], ascending=[False, False]).iloc[0]
    best_pq = per_query[per_query["run_name"] == best["run_name"]].copy()
    large_fail = best_pq[best_pq["hit@10"] == 0].copy()

    for _, row in large_fail.head(20).iterrows():
        rows.append({
            "failure_type": "large_budget_still_failure",
            "query_id": row["query_id"],
            "evidence_run": best["run_name"],
            "evidence": "best-quality configuration still misses relevant page at top10",
            "possible_cause": "query/page representation limitation or insufficient visual evidence",
            "analysis_value": "shows failure may not be solvable by budget alone",
        })

    return pd.DataFrame(rows)


def write_analysis_note(
    dimension_impact: pd.DataFrame,
    m_summary: pd.DataFrame,
    compression_delta: pd.DataFrame,
    bits_sensitivity: pd.DataFrame,
    coarse_ceiling: pd.DataFrame,
    failure_cases: pd.DataFrame,
    path: Path,
):
    coarse_recall_ceiling = coarse_ceiling["coarse_recall_ceiling@10"].mean() if not coarse_ceiling.empty else None

    with path.open("w", encoding="utf-8") as f:
        f.write("# Week 6 Day 5 Budget Triplet Analysis Note\n\n")

        f.write("## 1. Budget Dimension Impact\n\n")
        try:
            f.write(dimension_impact.to_markdown(index=False))
        except Exception:
            f.write(dimension_impact.to_string(index=False))
        f.write("\n\n")

        f.write("## 2. M Group Summary\n\n")
        try:
            f.write(m_summary.to_markdown(index=False))
        except Exception:
            f.write(m_summary.to_string(index=False))
        f.write("\n\n")

        f.write("## 3. Compression Delta vs None\n\n")
        try:
            f.write(compression_delta.to_markdown(index=False))
        except Exception:
            f.write(compression_delta.to_string(index=False))
        f.write("\n\n")

        f.write("## 4. Bits Sensitivity\n\n")
        if bits_sensitivity.empty:
            f.write("No bits sweep result found.\n\n")
        else:
            try:
                f.write(bits_sensitivity.to_markdown(index=False))
            except Exception:
                f.write(bits_sensitivity.to_string(index=False))
            f.write("\n\n")

        f.write("## 5. Coarse Recall Ceiling\n\n")
        f.write(f"Coarse candidate recall ceiling at top10: {coarse_recall_ceiling}\n\n")

        f.write("## 6. Failure Case Summary\n\n")
        if failure_cases.empty:
            f.write("No failure cases detected by current rules.\n\n")
        else:
            summary = failure_cases.groupby("failure_type").size().reset_index(name="count")
            try:
                f.write(summary.to_markdown(index=False))
            except Exception:
                f.write(summary.to_string(index=False))
            f.write("\n\n")

        f.write("## 7. Main Takeaways\n\n")
        f.write("- N controls whether the gold page enters the candidate pool and therefore controls the recall ceiling.\n")
        f.write("- M controls how much fine-grained visual-token evidence is preserved for late interaction reranking.\n")
        f.write("- bits controls quantization fidelity and can change similarity ordering when too aggressive.\n")
        f.write("- In the current fixed-N setting, M24 with compression provides the strongest quality-cost trade-off.\n")
        f.write("- Coarse recall should be protected first, token evidence second, and compression strength tuned last.\n")


def main():
    if not JOINT_RESULTS.exists():
        raise FileNotFoundError(f"Missing joint results: {JOINT_RESULTS}")

    results = pd.read_csv(JOINT_RESULTS, keep_default_na=False)
    results["Compression"] = results["Compression"].apply(normalize_compression)

    for col in ["N", "M", "Recall@10", "MRR@10", "nDCG@10", "Index Size MB", "Latency ms/query"]:
        results[col] = pd.to_numeric(results[col], errors="coerce")

    bits_results = None
    if BITS_RESULTS.exists():
        bits_results = pd.read_csv(BITS_RESULTS, keep_default_na=False)
        bits_results["Compression"] = bits_results["Compression"].apply(normalize_compression)

    qrels = load_qrels(QRELS_FILE)
    candidates = load_candidates(CANDIDATE_FILE)

    coarse_ceiling = compute_coarse_ceiling(candidates, qrels)
    per_query = build_per_query_table(results, qrels)

    dimension_impact = make_dimension_impact_table(results, bits_results)
    m_summary = make_m_group_summary(results)
    compression_delta = make_compression_delta_summary(results)
    m_sensitivity = make_m_query_sensitivity(per_query)
    quant_sensitivity = make_quantization_query_sensitivity(per_query)
    bits_sensitivity = make_bits_sensitivity(bits_results)
    failure_cases = make_failure_cases(
        results=results,
        per_query=per_query,
        coarse_ceiling=coarse_ceiling,
        m_sensitivity=m_sensitivity,
        quant_sensitivity=quant_sensitivity,
    )

    outputs = [
        (results, "day5_clean_joint_results"),
        (coarse_ceiling, "day5_coarse_recall_ceiling"),
        (per_query, "day5_per_query_metrics"),
        (dimension_impact, "day5_budget_dimension_impact"),
        (m_summary, "day5_m_group_summary"),
        (compression_delta, "day5_compression_delta_vs_none"),
        (m_sensitivity, "day5_query_sensitivity_by_M"),
        (quant_sensitivity, "day5_query_sensitivity_by_quantization"),
        (bits_sensitivity, "day5_bits_sensitivity"),
        (failure_cases, "day5_failure_cases"),
    ]

    for df, name in outputs:
        csv_path = OUT_DIR / f"{name}.csv"
        md_path = OUT_DIR / f"{name}.md"
        df.to_csv(csv_path, index=False, encoding="utf-8-sig")
        safe_to_markdown(df, md_path)

    write_analysis_note(
        dimension_impact=dimension_impact,
        m_summary=m_summary,
        compression_delta=compression_delta,
        bits_sensitivity=bits_sensitivity,
        coarse_ceiling=coarse_ceiling,
        failure_cases=failure_cases,
        path=OUT_DIR / "day5_budget_triplet_analysis_note.md",
    )

    print("[Done] Day 5 budget triplet analysis completed.")
    print(f"[Output] {OUT_DIR / 'day5_budget_triplet_analysis_note.md'}")
    print(f"[Output] {OUT_DIR / 'day5_budget_dimension_impact.csv'}")
    print(f"[Output] {OUT_DIR / 'day5_m_group_summary.csv'}")
    print(f"[Output] {OUT_DIR / 'day5_query_sensitivity_by_M.csv'}")
    print(f"[Output] {OUT_DIR / 'day5_query_sensitivity_by_quantization.csv'}")
    print(f"[Output] {OUT_DIR / 'day5_bits_sensitivity.csv'}")
    print(f"[Output] {OUT_DIR / 'day5_failure_cases.csv'}")


if __name__ == "__main__":
    main()
