from pathlib import Path
from collections import defaultdict
import csv
import json


PROJECT_ROOT = Path(r"E:\Working\PCB_VisualRAG_Project")

SUBSET_PATH = PROJECT_ROOT / "data" / "annotations" / "evidence_query_subset.jsonl"

RESULT_DIR = PROJECT_ROOT / "results" / "week7" / "evidence_hit"
C2F_DIR = PROJECT_ROOT / "results" / "week7" / "c2f_fixed_N"
HYBRID_DIR = PROJECT_ROOT / "results" / "week7" / "hybrid_fusion"

OUTPUT_RESULTS_CSV = RESULT_DIR / "evidence_hit_atk_results.csv"
OUTPUT_RESULTS_MD = RESULT_DIR / "evidence_hit_atk_results.md"
OUTPUT_PER_QUERY_CSV = RESULT_DIR / "evidence_hit_atk_per_query.csv"
OUTPUT_SUMMARY_JSON = RESULT_DIR / "evidence_hit_atk_summary.json"

KS = [1, 5, 10]


METHOD_CONFIGS = [
    {
        "method": "BM25",
        "candidate_files": [
            C2F_DIR / "bm25_baseline_run.tsv",
            C2F_DIR / "bm25_run.tsv",
            C2F_DIR / "baseline_bm25_run.tsv",
            HYBRID_DIR / "hybrid_fullmv_N50_alpha1p0_run.tsv",
            HYBRID_DIR / "hybrid_budgetmv_N50_M24_alpha1p0_run.tsv",
        ],
        "candidate_globs": [
            "bm25*baseline*run.tsv",
            "*bm25*run.tsv",
        ],
    },
    {
        "method": "Single-vector Visual",
        "candidate_files": [
            C2F_DIR / "single_vector_visual_run.tsv",
            C2F_DIR / "single_visual_run.tsv",
            C2F_DIR / "visual_single_vector_run.tsv",
        ],
        "candidate_globs": [
            "*single*visual*_run.tsv",
            "*visual*single*_run.tsv",
            "*single_vector*_run.tsv",
        ],
    },
    {
        "method": "Full MV",
        "candidate_files": [
            C2F_DIR / "bm25_fullmv_N10_run.tsv",
            C2F_DIR / "bm25_fullmv_N20_run.tsv",
            C2F_DIR / "bm25_fullmv_N50_run.tsv",
            C2F_DIR / "bm25_fullmv_N100_run.tsv",
            HYBRID_DIR / "hybrid_fullmv_N50_alpha0p0_run.tsv",
        ],
        "candidate_globs": [
            "bm25_fullmv_N10_run.tsv",
            "bm25_fullmv*_run.tsv",
            "hybrid_fullmv_N50_alpha0p0_run.tsv",
        ],
    },
    {
        "method": "Budgeted MV",
        "candidate_files": [
            C2F_DIR / "bm25_budgetmv_N20_M8_none_run.tsv",
            C2F_DIR / "bm25_budgetmv_N20_M16_none_run.tsv",
            C2F_DIR / "bm25_budgetmv_N50_M24_none_run.tsv",
            HYBRID_DIR / "hybrid_budgetmv_N50_M24_alpha0p0_run.tsv",
        ],
        "candidate_globs": [
            "bm25_budgetmv_N20_M8_none_run.tsv",
            "bm25_budgetmv*_run.tsv",
            "hybrid_budgetmv_N50_M24_alpha0p0_run.tsv",
        ],
    },
    {
        "method": "BM25 + Budgeted MV",
        "candidate_files": [
            C2F_DIR / "bm25_budgetmv_N20_M8_none_run.tsv",
            C2F_DIR / "bm25_budgetmv_N20_M16_none_run.tsv",
            C2F_DIR / "bm25_budgetmv_N50_M24_none_run.tsv",
        ],
        "candidate_globs": [
            "bm25_budgetmv_N20_M8_none_run.tsv",
            "bm25_budgetmv*_run.tsv",
        ],
    },
    {
        "method": "Hybrid Fusion",
        "candidate_files": [
            HYBRID_DIR / "hybrid_budgetmv_N50_M24_alpha1p0_run.tsv",
            HYBRID_DIR / "hybrid_budgetmv_N50_M24_alpha0p8_run.tsv",
            HYBRID_DIR / "hybrid_fullmv_N50_alpha1p0_run.tsv",
            HYBRID_DIR / "hybrid_fullmv_N50_alpha0p8_run.tsv",
        ],
        "candidate_globs": [
            "hybrid_budgetmv_N50_M24_alpha1p0_run.tsv",
            "hybrid_budgetmv_N50_M24_alpha0p8_run.tsv",
            "hybrid*_run.tsv",
        ],
    },
]


def ensure_dirs():
    RESULT_DIR.mkdir(parents=True, exist_ok=True)


def load_jsonl(path):
    rows = []

    if not path.exists():
        raise FileNotFoundError("Evidence subset not found: {}".format(path))

    with path.open("r", encoding="utf-8-sig") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()

            if not line:
                continue

            row = json.loads(line)
            row["_line_no"] = line_no
            rows.append(row)

    return rows


def read_table(path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        sample = f.read(4096)
        f.seek(0)
        delimiter = "\t" if "\t" in sample else ","
        return list(csv.reader(f, delimiter=delimiter))


def looks_like_header(row):
    text = "\t".join(row).lower()
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
    return any(k in text for k in keys)


def load_run(path):
    rows = read_table(path)

    if not rows:
        return {}

    run = defaultdict(list)

    first = rows[0]
    has_header = looks_like_header(first)

    if has_header:
        header = [x.strip().lower() for x in first]
        data_rows = rows[1:]

        def idx(names, default=None):
            for name in names:
                if name in header:
                    return header.index(name)
            return default

        qid_idx = idx(["query_id", "qid"], None)
        page_idx = idx(["page_id", "doc_id", "docid", "candidate_page_id"], None)
        rank_idx = idx(["rank"], None)
        score_idx = idx(["score"], None)

        if qid_idx is None or page_idx is None:
            raise ValueError("Cannot find query/page columns in {}".format(path))

        for i, row in enumerate(data_rows):
            if len(row) <= max(qid_idx, page_idx):
                continue

            qid = row[qid_idx].strip()
            page_id = row[page_idx].strip()

            if not qid or not page_id:
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

            run[qid].append((rank, page_id, score))

    else:
        for i, row in enumerate(rows):
            if len(row) >= 6 and row[1].strip().upper() == "Q0":
                qid = row[0].strip()
                page_id = row[2].strip()

                try:
                    rank = int(float(row[3]))
                except Exception:
                    rank = i + 1

                try:
                    score = float(row[4])
                except Exception:
                    score = 0.0

                run[qid].append((rank, page_id, score))

            elif len(row) >= 5:
                qid = row[1].strip()
                page_id = row[2].strip()

                try:
                    rank = int(float(row[3]))
                except Exception:
                    rank = i + 1

                try:
                    score = float(row[4])
                except Exception:
                    score = 0.0

                run[qid].append((rank, page_id, score))

            elif len(row) >= 4:
                qid = row[0].strip()
                page_id = row[1].strip()

                try:
                    rank = int(float(row[2]))
                except Exception:
                    rank = i + 1

                try:
                    score = float(row[3])
                except Exception:
                    score = 0.0

                run[qid].append((rank, page_id, score))

    final_run = {}

    for qid, items in run.items():
        items = sorted(items, key=lambda x: (x[0], -x[2]))
        final_run[qid] = [page_id for rank, page_id, score in items]

    return final_run


def choose_run_file(config):
    for path in config["candidate_files"]:
        if path.exists():
            return path

    search_dirs = [
        C2F_DIR,
        HYBRID_DIR,
        PROJECT_ROOT / "results" / "week7",
    ]

    for pattern in config["candidate_globs"]:
        for d in search_dirs:
            if not d.exists():
                continue

            matches = sorted(d.glob(pattern))

            if matches:
                return matches[0]

    return None


def hit_at_k(gold_page_id, ranked_pages, k):
    return 1 if gold_page_id in ranked_pages[:k] else 0


def evaluate_method(method_name, run_path, subset):
    if run_path is None:
        result = {
            "Method": method_name,
            "Run File": "",
            "Evidence Hit@1": "",
            "Evidence Hit@5": "",
            "Evidence Hit@10": "",
            "Query Count": len(subset),
            "Missing Query Count": len(subset),
            "Status": "MISSING_RUN",
        }
        per_query = []

        for item in subset:
            per_query.append(
                {
                    "Method": method_name,
                    "query_id": item.get("query_id", ""),
                    "gold_page_id": item.get("gold_page_id", ""),
                    "run_file": "",
                    "rank_found": "",
                    "Evidence Hit@1": "",
                    "Evidence Hit@5": "",
                    "Evidence Hit@10": "",
                    "status": "MISSING_RUN",
                }
            )

        return result, per_query

    run = load_run(run_path)

    hit_sums = {k: 0 for k in KS}
    per_query = []
    missing_query_count = 0

    for item in subset:
        qid = item.get("query_id", "")
        gold_page_id = item.get("gold_page_id", "")

        ranked_pages = run.get(qid, [])

        if not ranked_pages:
            missing_query_count += 1

        rank_found = ""

        if gold_page_id in ranked_pages:
            rank_found = ranked_pages.index(gold_page_id) + 1

        row = {
            "Method": method_name,
            "query_id": qid,
            "gold_page_id": gold_page_id,
            "run_file": str(run_path.relative_to(PROJECT_ROOT)),
            "rank_found": rank_found,
            "status": "PASSED",
        }

        for k in KS:
            value = hit_at_k(gold_page_id, ranked_pages, k)
            hit_sums[k] += value
            row["Evidence Hit@{}".format(k)] = value

        per_query.append(row)

    query_count = len(subset)

    result = {
        "Method": method_name,
        "Run File": str(run_path.relative_to(PROJECT_ROOT)),
        "Evidence Hit@1": hit_sums[1] / query_count if query_count else 0.0,
        "Evidence Hit@5": hit_sums[5] / query_count if query_count else 0.0,
        "Evidence Hit@10": hit_sums[10] / query_count if query_count else 0.0,
        "Query Count": query_count,
        "Missing Query Count": missing_query_count,
        "Status": "PASSED" if missing_query_count == 0 else "PASSED_WITH_MISSING_QUERIES",
    }

    return result, per_query


def fmt(value):
    if value == "":
        return ""

    return "{:.4f}".format(float(value))


def write_results_csv(results):
    fieldnames = [
        "Method",
        "Evidence Hit@1",
        "Evidence Hit@5",
        "Evidence Hit@10",
        "Query Count",
        "Missing Query Count",
        "Status",
        "Run File",
    ]

    with OUTPUT_RESULTS_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for row in results:
            out = dict(row)

            for key in ["Evidence Hit@1", "Evidence Hit@5", "Evidence Hit@10"]:
                out[key] = fmt(out[key]) if out[key] != "" else ""

            writer.writerow(out)


def write_results_md(results):
    lines = []
    lines.append("# Week 7 Day 5 Evidence Hit@k Results")
    lines.append("")
    lines.append("## Table 9: Evidence Hit@k 结果表")
    lines.append("")
    lines.append("| Method | Evidence Hit@1 | Evidence Hit@5 | Evidence Hit@10 | Status | Run File |")
    lines.append("|---|---:|---:|---:|---|---|")

    for row in results:
        lines.append(
            "| {} | {} | {} | {} | {} | {} |".format(
                row["Method"],
                fmt(row["Evidence Hit@1"]) if row["Evidence Hit@1"] != "" else "-",
                fmt(row["Evidence Hit@5"]) if row["Evidence Hit@5"] != "" else "-",
                fmt(row["Evidence Hit@10"]) if row["Evidence Hit@10"] != "" else "-",
                row["Status"],
                row["Run File"] if row["Run File"] else "-",
            )
        )

    lines.append("")
    lines.append("## Definition")
    lines.append("")
    lines.append("For each query, page-level evidence hit checks whether the gold evidence page appears in top-k retrieved pages.")
    lines.append("")
    lines.append("```text")
    lines.append("EvidenceHit@k(q) = 1 if g(q) is in R_k(q), else 0")
    lines.append("EvidenceHitRate@k = average over selected evidence queries")
    lines.append("```")

    OUTPUT_RESULTS_MD.write_text("\n".join(lines), encoding="utf-8")


def write_per_query_csv(per_query_rows):
    fieldnames = [
        "Method",
        "query_id",
        "gold_page_id",
        "rank_found",
        "Evidence Hit@1",
        "Evidence Hit@5",
        "Evidence Hit@10",
        "status",
        "run_file",
    ]

    with OUTPUT_PER_QUERY_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for row in per_query_rows:
            writer.writerow(row)


def write_summary_json(results):
    with OUTPUT_SUMMARY_JSON.open("w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)


def print_results(results):
    print("")
    print("========== Evidence Hit@k Results ==========")
    print("Method,Evidence Hit@1,Evidence Hit@5,Evidence Hit@10,Status,Run File")

    for row in results:
        print(
            "{},{},{},{},{},{}".format(
                row["Method"],
                fmt(row["Evidence Hit@1"]) if row["Evidence Hit@1"] != "" else "-",
                fmt(row["Evidence Hit@5"]) if row["Evidence Hit@5"] != "" else "-",
                fmt(row["Evidence Hit@10"]) if row["Evidence Hit@10"] != "" else "-",
                row["Status"],
                row["Run File"] if row["Run File"] else "-",
            )
        )


def main():
    ensure_dirs()

    subset = load_jsonl(SUBSET_PATH)

    results = []
    all_per_query = []

    print("[Week7-Day5] Starting page-level Evidence Hit@k evaluation...")
    print("Evidence subset:", SUBSET_PATH)
    print("Evidence query count:", len(subset))

    for config in METHOD_CONFIGS:
        method = config["method"]
        run_path = choose_run_file(config)

        print("")
        print("[Week7-Day5] Evaluating method:", method)

        if run_path is None:
            print("  Run file: MISSING")
        else:
            print("  Run file:", run_path)

        result, per_query = evaluate_method(method, run_path, subset)
        results.append(result)
        all_per_query.extend(per_query)

        print(
            "  Evidence Hit@1={}, Hit@5={}, Hit@10={}, Status={}".format(
                fmt(result["Evidence Hit@1"]) if result["Evidence Hit@1"] != "" else "-",
                fmt(result["Evidence Hit@5"]) if result["Evidence Hit@5"] != "" else "-",
                fmt(result["Evidence Hit@10"]) if result["Evidence Hit@10"] != "" else "-",
                result["Status"],
            )
        )

    write_results_csv(results)
    write_results_md(results)
    write_per_query_csv(all_per_query)
    write_summary_json(results)

    print_results(results)

    print("")
    print("Wrote CSV:", OUTPUT_RESULTS_CSV)
    print("Wrote Markdown:", OUTPUT_RESULTS_MD)
    print("Wrote per-query CSV:", OUTPUT_PER_QUERY_CSV)
    print("Wrote JSON:", OUTPUT_SUMMARY_JSON)


if __name__ == "__main__":
    main()
