from pathlib import Path
import time
import json
import numpy as np
import pandas as pd


CANDIDATE_FILE = Path("artifacts/rerank_cache/single_vector_topN/single_vector_candidates_top10.tsv")
QUERY_DIR = Path("artifacts/embeddings/full_multivector/queries")

TOKEN_ROOT = Path("artifacts/embeddings/token_selection")
COMP_ROOT = Path("artifacts/embeddings/joint_compression")

RUN_DIR = Path("results/budgeted/joint_compression/runs")
SCORE_DIR = Path("results/budgeted/joint_compression/scores")
LATENCY_DIR = Path("results/budgeted/joint_compression/latency")
DAY3_DIR = Path("results/budgeted/joint_compression/day3_main")

for d in [RUN_DIR, SCORE_DIR, LATENCY_DIR, DAY3_DIR]:
    d.mkdir(parents=True, exist_ok=True)


BUDGET_MS = [8, 16, 24]
COMPRESSIONS = ["None", "PQ", "OPQ+PQ", "IVF+PQ", "IVF+OPQ+PQ"]


def comp_slug(compression: str) -> str:
    if compression == "None":
        return "none"
    return compression.lower().replace("+", "_").replace(" ", "").replace("__", "_")


def run_name_for(m: int, compression: str) -> str:
    return f"w6_N10_M{m}_{comp_slug(compression)}"


def page_dir_for(m: int, compression: str) -> Path:
    if compression == "None":
        return TOKEN_ROOT / f"pages_M{m}"
    return COMP_ROOT / f"pages_M{m}_{comp_slug(compression)}"


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

    s = str(x).strip()
    s = s.strip('"').strip("'")
    return s


def is_header_like_row(row: pd.Series) -> bool:
    values = [normalize_id(v).lower() for v in row.tolist()]
    joined = "\t".join(values)

    header_tokens = [
        "query_id",
        "qid",
        "page_id",
        "docid",
        "rank",
        "score",
        "tag",
    ]

    return any(tok in values for tok in header_tokens) or joined.startswith("query_id")


def load_candidates(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Candidate file not found: {path}")

    raw = pd.read_csv(path, sep="\t", header=None, dtype=str)

    if raw.empty:
        raise ValueError(f"Candidate file is empty: {path}")

    raw = raw[~raw.apply(is_header_like_row, axis=1)].copy()
    raw = raw.dropna(how="all").copy()

    if raw.empty:
        raise ValueError(f"No valid candidate rows after cleaning: {path}")

    num_cols = raw.shape[1]

    if num_cols >= 6:
        df = raw.iloc[:, :6].copy()
        df.columns = ["query_id", "Q0", "page_id", "rank", "coarse_score", "tag"]
    elif num_cols == 5:
        df = raw.copy()
        df.columns = ["query_id", "page_id", "rank", "coarse_score", "tag"]
        df["Q0"] = "Q0"
    elif num_cols == 4:
        df = raw.copy()
        df.columns = ["query_id", "page_id", "rank", "coarse_score"]
        df["Q0"] = "Q0"
        df["tag"] = "candidate"
    elif num_cols == 3:
        df = raw.copy()
        df.columns = ["query_id", "page_id", "coarse_score"]
        df["rank"] = df.groupby("query_id").cumcount() + 1
        df["Q0"] = "Q0"
        df["tag"] = "candidate"
    else:
        raise ValueError(f"Unsupported candidate file format: {path}, columns={num_cols}")

    df["query_id"] = df["query_id"].apply(normalize_id)
    df["page_id"] = df["page_id"].apply(normalize_id)

    df = df[(df["query_id"] != "") & (df["page_id"] != "")].copy()
    df = df[df["query_id"].str.lower() != "query_id"].copy()
    df = df[df["page_id"].str.lower() != "page_id"].copy()

    df["rank"] = pd.to_numeric(df["rank"], errors="coerce")
    df["coarse_score"] = pd.to_numeric(df["coarse_score"], errors="coerce")

    df["rank"] = df["rank"].fillna(df.groupby("query_id").cumcount() + 1).astype(int)
    df["coarse_score"] = df["coarse_score"].fillna(0.0).astype(float)

    df = df.sort_values(["query_id", "rank"]).reset_index(drop=True)

    return df


def find_query_file(query_id: str) -> Path:
    qid = normalize_id(query_id)

    candidates = [
        QUERY_DIR / f"{qid}.npy",
        QUERY_DIR / f"{qid}_query.npy",
        QUERY_DIR / f"query_{qid}.npy",
        QUERY_DIR / f"q_{qid}.npy",
    ]

    for fp in candidates:
        if fp.exists():
            return fp

    matches = sorted(QUERY_DIR.glob(f"*{qid}*.npy"))
    if matches:
        return matches[0]

    raise FileNotFoundError(f"Query embedding not found for query_id={qid} in {QUERY_DIR}")


def find_page_file(page_dir: Path, page_id: str) -> Path:
    pid = normalize_id(page_id)

    candidates = [
        page_dir / f"{pid}.npy",
        page_dir / f"{pid}_page.npy",
        page_dir / f"page_{pid}.npy",
        page_dir / f"p_{pid}.npy",
    ]

    for fp in candidates:
        if fp.exists():
            return fp

    matches = sorted(page_dir.glob(f"*{pid}*.npy"))
    if matches:
        return matches[0]

    raise FileNotFoundError(f"Page embedding not found for page_id={pid} in {page_dir}")


def late_interaction_score(q: np.ndarray, p: np.ndarray) -> float:
    if q.ndim != 2:
        raise ValueError(f"Query embedding must be 2D, got shape={q.shape}")

    if p.ndim != 2:
        raise ValueError(f"Page embedding must be 2D, got shape={p.shape}")

    if q.shape[1] != p.shape[1]:
        raise ValueError(f"Dim mismatch: q={q.shape}, p={p.shape}")

    sim = q @ p.T
    return float(sim.max(axis=1).sum())


def run_one(m: int, compression: str, candidates: pd.DataFrame) -> dict:
    run_name = run_name_for(m, compression)
    page_dir = page_dir_for(m, compression)

    if not page_dir.exists():
        raise FileNotFoundError(f"Page embedding dir not found: {page_dir}")

    print("=" * 80)
    print(f"[Run] {run_name}")
    print(f"[Compression] {compression}")
    print(f"[Page dir] {page_dir}")

    score_rows = []
    run_rows = []
    missing_rows = []

    query_ids = sorted(candidates["query_id"].unique())
    total_candidates = len(candidates)

    t0 = time.time()

    query_cache = {}
    page_cache = {}

    valid_query_count = 0
    valid_candidate_count = 0

    for qid in query_ids:
        try:
            q_file = find_query_file(qid)
        except FileNotFoundError as e:
            print(f"[Warn] {e}")
            missing_rows.append({
                "run_name": run_name,
                "query_id": qid,
                "page_id": "",
                "missing_type": "query",
                "message": str(e),
            })
            continue

        if q_file not in query_cache:
            query_cache[q_file] = np.load(q_file).astype("float32")

        q = query_cache[q_file]

        sub = candidates[candidates["query_id"] == qid].copy()
        page_scores = []

        for _, row in sub.iterrows():
            pid = str(row["page_id"])

            try:
                p_file = find_page_file(page_dir, pid)
            except FileNotFoundError as e:
                print(f"[Warn] {e}")
                missing_rows.append({
                    "run_name": run_name,
                    "query_id": qid,
                    "page_id": pid,
                    "missing_type": "page",
                    "message": str(e),
                })
                continue

            if p_file not in page_cache:
                page_cache[p_file] = np.load(p_file).astype("float32")

            p = page_cache[p_file]

            score = late_interaction_score(q, p)
            page_scores.append((pid, score))
            valid_candidate_count += 1

            score_rows.append({
                "query_id": qid,
                "page_id": pid,
                "score": score,
                "run_name": run_name,
                "compression": compression,
                "query_file": str(q_file),
                "page_file": str(p_file),
            })

        page_scores = sorted(page_scores, key=lambda x: x[1], reverse=True)

        if page_scores:
            valid_query_count += 1

        for rank, (pid, score) in enumerate(page_scores, start=1):
            run_rows.append({
                "query_id": qid,
                "Q0": "Q0",
                "page_id": pid,
                "rank": rank,
                "score": score,
                "tag": run_name,
            })

    elapsed = time.time() - t0
    latency_ms = elapsed / valid_query_count * 1000.0 if valid_query_count > 0 else None

    run_df = pd.DataFrame(run_rows)
    score_df = pd.DataFrame(score_rows)
    missing_df = pd.DataFrame(missing_rows)

    if run_df.empty:
        raise RuntimeError(f"No valid reranking results generated for {run_name}")

    run_path = RUN_DIR / f"{run_name}_run.tsv"
    score_path = SCORE_DIR / f"{run_name}_scores.csv"
    latency_path = LATENCY_DIR / f"{run_name}_latency.json"
    missing_path = DAY3_DIR / f"{run_name}_missing_embeddings.csv"

    run_df.to_csv(
        run_path,
        sep="\t",
        header=False,
        index=False,
        columns=["query_id", "Q0", "page_id", "rank", "score", "tag"],
    )

    score_df.to_csv(score_path, index=False, encoding="utf-8-sig")

    if not missing_df.empty:
        missing_df.to_csv(missing_path, index=False, encoding="utf-8-sig")

    latency = {
        "run_name": run_name,
        "compression": compression,
        "N": 10,
        "M": m,
        "input_query_count": int(len(query_ids)),
        "valid_query_count": int(valid_query_count),
        "input_candidate_rows": int(total_candidates),
        "valid_candidate_count": int(valid_candidate_count),
        "avg_input_candidates_per_query": float(total_candidates / len(query_ids)) if query_ids else 0.0,
        "avg_valid_candidates_per_valid_query": float(valid_candidate_count / valid_query_count) if valid_query_count > 0 else 0.0,
        "rerank_time_seconds": float(elapsed),
        "per_query_latency_ms": float(latency_ms) if latency_ms is not None else None,
        "run_file": str(run_path),
        "score_file": str(score_path),
        "missing_file": str(missing_path) if not missing_df.empty else None,
        "page_dir": str(page_dir),
    }

    with latency_path.open("w", encoding="utf-8") as f:
        json.dump(latency, f, indent=2, ensure_ascii=False)

    print(f"[Done] {run_name}")
    print(f"[Valid queries] {valid_query_count}/{len(query_ids)}")
    print(f"[Valid candidates] {valid_candidate_count}/{total_candidates}")
    print(f"[Latency ms/query] {latency_ms}")

    return latency


def main():
    print("[Info] Loading candidates...")
    candidates = load_candidates(CANDIDATE_FILE)

    query_count = candidates["query_id"].nunique()
    candidate_rows = len(candidates)

    print(f"[Info] Query count after cleaning: {query_count}")
    print(f"[Info] Candidate rows after cleaning: {candidate_rows}")
    print(f"[Info] Avg candidates/query: {candidate_rows / query_count:.2f}")

    latency_rows = []

    for m in BUDGET_MS:
        for compression in COMPRESSIONS:
            latency = run_one(m, compression, candidates)
            latency_rows.append(latency)

    latency_df = pd.DataFrame(latency_rows)

    csv_path = DAY3_DIR / "day3_joint_rerank_latency.csv"
    md_path = DAY3_DIR / "day3_joint_rerank_latency.md"

    latency_df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    safe_to_markdown(latency_df, md_path)

    print("=" * 80)
    print("[Done] Day 3 joint reranking completed.")
    print(f"[Output] {csv_path}")
    print(f"[Output] {md_path}")


if __name__ == "__main__":
    main()
