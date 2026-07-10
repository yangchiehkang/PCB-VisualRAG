import csv
import json
import math
import re
from pathlib import Path
from collections import defaultdict


PROJECT_ROOT = Path(__file__).resolve().parents[2]

METRIC_FILES = {
    "OCR + BM25": PROJECT_ROOT / "results" / "baselines" / "bm25_metrics.json",
    "OCR + Dense": PROJECT_ROOT / "results" / "baselines" / "dense_text_metrics.json",
    "Single-vector Visual": PROJECT_ROOT / "results" / "baselines" / "single_vector_visual_metrics.json",
}

RUN_FILES = {
    "OCR + BM25": PROJECT_ROOT / "results" / "baselines" / "bm25_run.tsv",
    "OCR + Dense": PROJECT_ROOT / "results" / "baselines" / "dense_text_run.tsv",
    "Single-vector Visual": PROJECT_ROOT / "results" / "baselines" / "single_vector_visual_run.tsv",
}

QUERIES_FILE = PROJECT_ROOT / "data" / "metadata" / "queries.jsonl"
QRELS_FILE = PROJECT_ROOT / "data" / "metadata" / "qrels.tsv"

RESULTS_DIR = PROJECT_ROOT / "results" / "baselines"
ANALYSIS_DIR = PROJECT_ROOT / "results" / "analysis"
NOTES_DIR = PROJECT_ROOT / "notes"

BASELINE_SUMMARY_CSV = RESULTS_DIR / "baseline_summary.csv"
BASELINE_SUMMARY_XLSX = RESULTS_DIR / "baseline_summary.xlsx"

BY_TYPE_CSV = ANALYSIS_DIR / "results_by_query_type.csv"
BY_TYPE_XLSX = ANALYSIS_DIR / "results_by_query_type.xlsx"

QUERY_TYPE_COUNTS_CSV = ANALYSIS_DIR / "query_type_counts.csv"
TYPE_BEST_METHOD_CSV = ANALYSIS_DIR / "type_best_method.csv"

CONCLUSION_MD = NOTES_DIR / "2026-04-09_week2_day5_initial_conclusion.md"


def ensure_dirs():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
    NOTES_DIR.mkdir(parents=True, exist_ok=True)


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def parse_metrics_from_text(text: str):
    result = {}

    patterns = {
        "Recall@1": [
            r"Recall@1\s*[:=]\s*([0-9]*\.?[0-9]+)",
            r"R@1\s*[:=]\s*([0-9]*\.?[0-9]+)",
        ],
        "Recall@5": [
            r"Recall@5\s*[:=]\s*([0-9]*\.?[0-9]+)",
            r"R@5\s*[:=]\s*([0-9]*\.?[0-9]+)",
        ],
        "Recall@10": [
            r"Recall@10\s*[:=]\s*([0-9]*\.?[0-9]+)",
            r"R@10\s*[:=]\s*([0-9]*\.?[0-9]+)",
        ],
        "MRR": [
            r"\bMRR\b\s*[:=]\s*([0-9]*\.?[0-9]+)",
            r"MRR@10\s*[:=]\s*([0-9]*\.?[0-9]+)",
        ],
        "nDCG@10": [
            r"nDCG@10\s*[:=]\s*([0-9]*\.?[0-9]+)",
            r"ndcg@10\s*[:=]\s*([0-9]*\.?[0-9]+)",
        ],
    }

    for metric_name, metric_patterns in patterns.items():
        for pattern in metric_patterns:
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if match:
                result[metric_name] = float(match.group(1))
                break

    return result


def try_parse_metrics_file(path: Path):
    text = load_text(path).strip()

    try:
        data = json.loads(text)
        if isinstance(data, dict):
            return data
    except Exception:
        pass

    first_brace = text.find("{")
    last_brace = text.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        candidate = text[first_brace:last_brace + 1]
        try:
            data = json.loads(candidate)
            if isinstance(data, dict):
                return data
        except Exception:
            pass

    text_metrics = parse_metrics_from_text(text)
    if text_metrics:
        return text_metrics

    raise ValueError(f"Could not parse metrics file: {path}")


def normalize_metric_dict(d):
    direct_keys = {
        "Recall@1": ["Recall@1", "recall@1", "R@1", "r@1", "recall_1"],
        "Recall@5": ["Recall@5", "recall@5", "R@5", "r@5", "recall_5"],
        "Recall@10": ["Recall@10", "recall@10", "R@10", "r@10", "recall_10"],
        "MRR": ["MRR", "mrr", "MRR@10", "mrr@10", "mrr_10"],
        "nDCG@10": ["nDCG@10", "ndcg@10", "nDCG_10", "ndcg_10"],
    }

    result = {}
    for canonical, aliases in direct_keys.items():
        value = None
        for key in aliases:
            if key in d:
                value = d[key]
                break
        result[canonical] = value

    if any(v is not None for v in result.values()):
        return result

    flat = {}

    def walk(obj, prefix=""):
        if isinstance(obj, dict):
            for k, v in obj.items():
                new_prefix = f"{prefix}.{k}" if prefix else str(k)
                walk(v, new_prefix)
        else:
            flat[prefix.lower()] = obj

    walk(d)

    def find_value(candidates):
        for c in candidates:
            c = c.lower()
            if c in flat:
                return flat[c]
        for key, value in flat.items():
            last = key.split(".")[-1]
            for c in candidates:
                if c.lower() == last:
                    return value
        return None

    return {
        "Recall@1": find_value(["recall@1", "r@1", "recall_1"]),
        "Recall@5": find_value(["recall@5", "r@5", "recall_5"]),
        "Recall@10": find_value(["recall@10", "r@10", "recall_10"]),
        "MRR": find_value(["mrr", "mrr@10", "mrr_10"]),
        "nDCG@10": find_value(["ndcg@10", "ndcg_10"]),
    }


def load_queries(path: Path):
    queries = {}
    query_type_counts = defaultdict(int)

    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            qid = obj["query_id"]
            qtype = obj.get("query_type", "unknown")
            queries[qid] = obj
            query_type_counts[qtype] += 1

    return queries, query_type_counts


def load_qrels(path: Path):
    qrels = defaultdict(set)
    with path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            qid = row.get("query_id")
            pid = row.get("page_id") or row.get("docid") or row.get("doc_id")
            rel = int(row.get("relevance") or row.get("rel") or 0)
            if rel > 0:
                qrels[qid].add(pid)
    return qrels


def load_run(path: Path):
    run = defaultdict(list)
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) < 6:
                continue
            qid, _, pid, rank, score, _ = parts[:6]
            run[qid].append((int(rank), pid, float(score)))

    for qid in run:
        run[qid].sort(key=lambda x: x[0])
    return run


def recall_at_k(predicted_page_ids, relevant_page_ids, k=10):
    topk = predicted_page_ids[:k]
    return 1.0 if any(pid in relevant_page_ids for pid in topk) else 0.0


def reciprocal_rank(predicted_page_ids, relevant_page_ids, k=10):
    for idx, pid in enumerate(predicted_page_ids[:k], start=1):
        if pid in relevant_page_ids:
            return 1.0 / idx
    return 0.0


def ndcg_at_k(predicted_page_ids, relevant_page_ids, k=10):
    dcg = 0.0
    for i, pid in enumerate(predicted_page_ids[:k], start=1):
        rel = 1 if pid in relevant_page_ids else 0
        if rel > 0:
            dcg += rel / math.log2(i + 1)

    ideal_hits = min(len(relevant_page_ids), k)
    idcg = 0.0
    for i in range(1, ideal_hits + 1):
        idcg += 1.0 / math.log2(i + 1)

    if idcg == 0.0:
        return 0.0
    return dcg / idcg


def compute_type_level_metrics(run, queries, qrels):
    grouped = defaultdict(list)

    for qid, qobj in queries.items():
        qtype = qobj.get("query_type", "unknown")
        relevant = qrels.get(qid, set())
        ranked = [pid for _, pid, _ in run.get(qid, [])]

        r10 = recall_at_k(ranked, relevant, k=10)
        rr = reciprocal_rank(ranked, relevant, k=10)
        ndcg10 = ndcg_at_k(ranked, relevant, k=10)

        grouped[qtype].append({
            "query_id": qid,
            "Recall@10": r10,
            "MRR": rr,
            "nDCG@10": ndcg10,
        })

    rows = []
    for qtype, items in grouped.items():
        n = len(items)
        rows.append({
            "Query Type": qtype,
            "Num Queries": n,
            "Recall@10": sum(x["Recall@10"] for x in items) / n if n else 0.0,
            "MRR": sum(x["MRR"] for x in items) / n if n else 0.0,
            "nDCG@10": sum(x["nDCG@10"] for x in items) / n if n else 0.0,
        })

    rows.sort(key=lambda x: x["Query Type"])
    return rows


def write_csv(path: Path, rows, fieldnames):
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def try_write_xlsx(path: Path, rows, sheet_name="Sheet1"):
    try:
        from openpyxl import Workbook
    except ImportError:
        return False

    wb = Workbook()
    ws = wb.active
    ws.title = sheet_name

    if not rows:
        wb.save(path)
        return True

    headers = list(rows[0].keys())
    ws.append(headers)
    for row in rows:
        ws.append([row.get(h, "") for h in headers])

    for col in ws.columns:
        max_len = 0
        col_letter = col[0].column_letter
        for cell in col:
            value = "" if cell.value is None else str(cell.value)
            max_len = max(max_len, len(value))
        ws.column_dimensions[col_letter].width = min(max_len + 2, 40)

    wb.save(path)
    return True


def main():
    ensure_dirs()

    summary_rows = []
    by_type_all = []

    queries, query_type_counts = load_queries(QUERIES_FILE)
    qrels = load_qrels(QRELS_FILE)

    for method_name, metric_path in METRIC_FILES.items():
        metric_raw = try_parse_metrics_file(metric_path)
        metric_norm = normalize_metric_dict(metric_raw)

        summary_rows.append({
            "Method": method_name,
            "Recall@1": metric_norm.get("Recall@1", ""),
            "Recall@5": metric_norm.get("Recall@5", ""),
            "Recall@10": metric_norm.get("Recall@10", ""),
            "MRR": metric_norm.get("MRR", ""),
            "nDCG@10": metric_norm.get("nDCG@10", ""),
        })

        run = load_run(RUN_FILES[method_name])
        rows = compute_type_level_metrics(run, queries, qrels)
        for row in rows:
            row["Method"] = method_name
            by_type_all.append(row)

    write_csv(
        BASELINE_SUMMARY_CSV,
        summary_rows,
        ["Method", "Recall@1", "Recall@5", "Recall@10", "MRR", "nDCG@10"]
    )
    try_write_xlsx(BASELINE_SUMMARY_XLSX, summary_rows, sheet_name="baseline_summary")

    write_csv(
        BY_TYPE_CSV,
        by_type_all,
        ["Method", "Query Type", "Num Queries", "Recall@10", "MRR", "nDCG@10"]
    )
    try_write_xlsx(BY_TYPE_XLSX, by_type_all, sheet_name="by_query_type")

    count_rows = [{"Query Type": k, "Num Queries": v} for k, v in sorted(query_type_counts.items())]
    write_csv(QUERY_TYPE_COUNTS_CSV, count_rows, ["Query Type", "Num Queries"])

    best_rows = []
    grouped = defaultdict(list)
    for row in by_type_all:
        grouped[row["Query Type"]].append(row)

    for qtype, rows in grouped.items():
        best = max(rows, key=lambda x: x["Recall@10"])
        best_rows.append({
            "Query Type": qtype,
            "Best Method by Recall@10": best["Method"],
            "Best Recall@10": best["Recall@10"],
            "Best MRR": best["MRR"],
            "Best nDCG@10": best["nDCG@10"],
        })

    write_csv(
        TYPE_BEST_METHOD_CSV,
        best_rows,
        ["Query Type", "Best Method by Recall@10", "Best Recall@10", "Best MRR", "Best nDCG@10"]
    )

    if not CONCLUSION_MD.exists():
        CONCLUSION_MD.write_text(
            "# Initial Baseline Conclusion\n\n"
            "- Compare OCR + BM25, OCR + Dense, and Single-vector Visual.\n"
            "- Review baseline_summary.csv and results_by_query_type.csv.\n"
            "- Identify strongest baseline and weak query types.\n",
            encoding="utf-8"
        )

    print(f"Wrote baseline summary to: {BASELINE_SUMMARY_CSV}")
    print(f"Wrote query-type summary to: {BY_TYPE_CSV}")
    print(f"Wrote query type counts to: {QUERY_TYPE_COUNTS_CSV}")
    print(f"Wrote type-best-method summary to: {TYPE_BEST_METHOD_CSV}")
    print(f"Conclusion note: {CONCLUSION_MD}")


if __name__ == "__main__":
    main()
