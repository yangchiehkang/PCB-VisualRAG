from pathlib import Path
from collections import defaultdict
import csv
import json

PROJECT_ROOT = Path(__file__).resolve().parents[2]

CANDIDATE_DIR = PROJECT_ROOT / "artifacts" / "rerank_cache" / "week7_topN"
OUT_DIR = PROJECT_ROOT / "results" / "week7" / "c2f_fixed_N"

# 自动尝试这些 qrels 路径
QRELS_CANDIDATES = [
    PROJECT_ROOT / "data" / "metadata" / "qrels.tsv",
    PROJECT_ROOT / "data" / "metadata" / "qrels.txt",
    PROJECT_ROOT / "data" / "metadata" / "relevance.tsv",
    PROJECT_ROOT / "data" / "metadata" / "relevance.jsonl",
    PROJECT_ROOT / "data" / "metadata" / "query_relevance.tsv",
]

FILES = [
    {
        "method": "Single-vector Visual",
        "short_name": "visual",
        "N": 10,
        "path": CANDIDATE_DIR / "candidates_visual_N10.tsv",
    },
    {
        "method": "Single-vector Visual",
        "short_name": "visual",
        "N": 20,
        "path": CANDIDATE_DIR / "candidates_visual_N20.tsv",
    },
    {
        "method": "Single-vector Visual",
        "short_name": "visual",
        "N": 50,
        "path": CANDIDATE_DIR / "candidates_visual_N50.tsv",
    },
    {
        "method": "Single-vector Visual",
        "short_name": "visual",
        "N": 100,
        "path": CANDIDATE_DIR / "candidates_visual_N100.tsv",
    },
    {
        "method": "BM25",
        "short_name": "bm25",
        "N": 10,
        "path": CANDIDATE_DIR / "candidates_bm25_N10.tsv",
    },
    {
        "method": "BM25",
        "short_name": "bm25",
        "N": 20,
        "path": CANDIDATE_DIR / "candidates_bm25_N20.tsv",
    },
    {
        "method": "BM25",
        "short_name": "bm25",
        "N": 50,
        "path": CANDIDATE_DIR / "candidates_bm25_N50.tsv",
    },
    {
        "method": "BM25",
        "short_name": "bm25",
        "N": 100,
        "path": CANDIDATE_DIR / "candidates_bm25_N100.tsv",
    },
]


def find_qrels_path():
    for path in QRELS_CANDIDATES:
        if path.exists():
            return path

    raise FileNotFoundError(
        "Cannot find qrels file. Tried:\n"
        + "\n".join(str(p) for p in QRELS_CANDIDATES)
    )


def normalize_id(x):
    return str(x).strip()


def parse_qrels_tsv_or_txt(path: Path):
    """
    支持常见 qrels 格式：

    1. TREC qrels:
       qid 0 doc_id relevance

    2. TSV with header:
       query_id page_id relevance
       query_id doc_id label
       qid docid rel

    3. 无 header 三列:
       qid doc_id relevance
    """
    qrels = defaultdict(set)

    with path.open("r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    if not lines:
        raise ValueError(f"Empty qrels file: {path}")

    first_parts = lines[0].replace(",", "\t").split()
    lower_first = [x.lower() for x in first_parts]

    has_header = any(
        key in lower_first
        for key in [
            "query_id",
            "qid",
            "doc_id",
            "docid",
            "page_id",
            "relevance",
            "rel",
            "label",
        ]
    )

    start_idx = 1 if has_header else 0

    if has_header:
        header = lower_first

        def find_col(possible_names, default=None):
            for name in possible_names:
                if name in header:
                    return header.index(name)
            return default

        qid_idx = find_col(["query_id", "qid", "query"], 0)
        doc_idx = find_col(["page_id", "doc_id", "docid", "document_id", "pid"], 1)
        rel_idx = find_col(["relevance", "rel", "label", "score"], 2)

        for line in lines[start_idx:]:
            parts = line.replace(",", "\t").split()
            if len(parts) <= max(qid_idx, doc_idx, rel_idx):
                continue

            qid = normalize_id(parts[qid_idx])
            doc_id = normalize_id(parts[doc_idx])

            try:
                rel = float(parts[rel_idx])
            except ValueError:
                rel = 1.0

            if rel > 0:
                qrels[qid].add(doc_id)

    else:
        for line in lines[start_idx:]:
            parts = line.replace(",", "\t").split()

            if len(parts) >= 4:
                # TREC: qid Q0 doc_id rel
                qid = normalize_id(parts[0])
                doc_id = normalize_id(parts[2])
                try:
                    rel = float(parts[3])
                except ValueError:
                    rel = 1.0

            elif len(parts) >= 3:
                # qid doc_id rel
                qid = normalize_id(parts[0])
                doc_id = normalize_id(parts[1])
                try:
                    rel = float(parts[2])
                except ValueError:
                    rel = 1.0

            else:
                continue

            if rel > 0:
                qrels[qid].add(doc_id)

    return qrels


def parse_qrels_jsonl(path: Path):
    """
    支持 JSONL 中常见字段：
    query_id / qid / id
    page_id / doc_id / relevant_doc_id
    relevance / rel / label
    """
    qrels = defaultdict(set)

    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            obj = json.loads(line)

            qid = None
            for key in ["query_id", "qid", "id", "query"]:
                if key in obj:
                    qid = normalize_id(obj[key])
                    break

            doc_id = None
            for key in ["page_id", "doc_id", "docid", "relevant_doc_id", "document_id"]:
                if key in obj:
                    doc_id = normalize_id(obj[key])
                    break

            rel = 1.0
            for key in ["relevance", "rel", "label", "score"]:
                if key in obj:
                    try:
                        rel = float(obj[key])
                    except ValueError:
                        rel = 1.0
                    break

            if qid is not None and doc_id is not None and rel > 0:
                qrels[qid].add(doc_id)

    return qrels


def load_qrels(path: Path):
    if path.suffix.lower() == ".jsonl":
        qrels = parse_qrels_jsonl(path)
    else:
        qrels = parse_qrels_tsv_or_txt(path)

    if not qrels:
        raise ValueError(f"No positive qrels loaded from: {path}")

    return qrels


def load_candidates(path: Path):
    """
    读取 TREC run / candidates 格式：
    qid Q0 doc_id rank score run_name
    """
    candidates = defaultdict(list)

    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            parts = line.split("\t")
            if len(parts) < 6:
                parts = line.split()

            if len(parts) < 3:
                continue

            qid = normalize_id(parts[0])
            doc_id = normalize_id(parts[2])

            if len(parts) >= 4:
                try:
                    rank = int(parts[3])
                except ValueError:
                    rank = len(candidates[qid]) + 1
            else:
                rank = len(candidates[qid]) + 1

            candidates[qid].append((rank, doc_id))

    for qid in candidates:
        candidates[qid].sort(key=lambda x: x[0])

    return candidates


def compute_coarse_recall(qrels, candidates):
    """
    Coarse Recall@N:
    query 的候选集中包含至少一个 relevant doc，则该 query hit。

    recall = hit_queries / total_qrel_queries
    """
    total_queries = len(qrels)
    hit_queries = 0
    miss_queries = 0
    hit_qids = []
    miss_qids = []

    for qid, relevant_docs in qrels.items():
        candidate_docs = {doc_id for _, doc_id in candidates.get(qid, [])}

        if relevant_docs & candidate_docs:
            hit_queries += 1
            hit_qids.append(qid)
        else:
            miss_queries += 1
            miss_qids.append(qid)

    recall = hit_queries / total_queries if total_queries > 0 else 0.0

    return {
        "total_queries": total_queries,
        "hit_queries": hit_queries,
        "miss_queries": miss_queries,
        "coarse_recall": recall,
        "hit_qids": hit_qids,
        "miss_qids": miss_qids,
    }


def write_markdown_table(rows, out_path: Path):
    with out_path.open("w", encoding="utf-8") as f:
        f.write("| Coarse Method | N | Coarse Recall@N | Hit Queries | Miss Queries |\n")
        f.write("|---|---:|---:|---:|---:|\n")

        for row in rows:
            f.write(
                f"| {row['Coarse Method']} "
                f"| {row['N']} "
                f"| {row['Coarse Recall@N']:.4f} "
                f"| {row['Hit Queries']} "
                f"| {row['Miss Queries']} |\n"
            )


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    qrels_path = find_qrels_path()
    print(f"Using qrels: {qrels_path}")

    qrels = load_qrels(qrels_path)

    print(f"Loaded qrels queries: {len(qrels)}")
    print(f"Total relevant pairs: {sum(len(v) for v in qrels.values())}")

    rows = []
    details = []

    for item in FILES:
        method = item["method"]
        n = item["N"]
        path = item["path"]

        if not path.exists():
            raise FileNotFoundError(f"Missing candidate file: {path}")

        candidates = load_candidates(path)
        stats = compute_coarse_recall(qrels, candidates)

        row = {
            "Coarse Method": method,
            "N": n,
            "Coarse Recall@N": stats["coarse_recall"],
            "Hit Queries": stats["hit_queries"],
            "Miss Queries": stats["miss_queries"],
            "Total Queries": stats["total_queries"],
            "candidate_file": str(path),
        }
        rows.append(row)

        for qid in stats["hit_qids"]:
            details.append({
                "method": method,
                "N": n,
                "qid": qid,
                "status": "hit",
            })

        for qid in stats["miss_qids"]:
            details.append({
                "method": method,
                "N": n,
                "qid": qid,
                "status": "miss",
            })

        print(
            f"{method:22s} "
            f"N={n:<3d} "
            f"Recall={stats['coarse_recall']:.4f} "
            f"Hit={stats['hit_queries']} "
            f"Miss={stats['miss_queries']}"
        )

    csv_path = OUT_DIR / "coarse_recall_atN.csv"
    md_path = OUT_DIR / "coarse_recall_atN.md"
    detail_path = OUT_DIR / "coarse_recall_atN_query_details.csv"

    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "Coarse Method",
                "N",
                "Coarse Recall@N",
                "Hit Queries",
                "Miss Queries",
                "Total Queries",
                "candidate_file",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    write_markdown_table(rows, md_path)

    with detail_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["method", "N", "qid", "status"],
        )
        writer.writeheader()
        writer.writerows(details)

    print()
    print(f"Wrote CSV: {csv_path}")
    print(f"Wrote Markdown table: {md_path}")
    print(f"Wrote query details: {detail_path}")


if __name__ == "__main__":
    main()
