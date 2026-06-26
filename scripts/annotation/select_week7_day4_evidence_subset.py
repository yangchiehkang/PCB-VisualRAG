from pathlib import Path
from collections import defaultdict
import csv
import json
import re


PROJECT_ROOT = Path(r"E:\Working\PCB_VisualRAG_Project")

METADATA_DIR = PROJECT_ROOT / "data" / "metadata"
ANNOTATION_DIR = PROJECT_ROOT / "data" / "annotations"
RESULT_DIR = PROJECT_ROOT / "results" / "week7" / "evidence_annotation"

OUTPUT_SUBSET = ANNOTATION_DIR / "evidence_query_subset.jsonl"
OUTPUT_REGIONS = ANNOTATION_DIR / "evidence_regions.jsonl"
OUTPUT_CANDIDATES = RESULT_DIR / "evidence_subset_candidates.csv"
OUTPUT_REPORT = RESULT_DIR / "evidence_subset_selection_report.md"

TARGET_N = 10

TYPE_PRIORITY = {
    "parameter_lookup": 1,
    "structure_legend_interpretation": 2,
    "component_localization": 3,
    "similarity_based_interference": 4,
    "cross_page_consistency": 5,
}

TYPE_QUOTA = {
    "parameter_lookup": 2,
    "structure_legend_interpretation": 3,
    "component_localization": 2,
    "similarity_based_interference": 2,
    "cross_page_consistency": 1,
}

EVIDENCE_TYPE_MAP = {
    "parameter_lookup": "table_cell",
    "structure_legend_interpretation": "legend_or_structure_region",
    "component_localization": "component_region",
    "similarity_based_interference": "visual_similarity_region",
    "cross_page_consistency": "cross_page_reference_region",
}

PAGE_TYPE_MAP = {
    "parameter_lookup": "table_or_spec_page",
    "structure_legend_interpretation": "layout_or_legend_page",
    "component_localization": "pcb_layout_page",
    "similarity_based_interference": "visual_comparison_page",
    "cross_page_consistency": "multi_page_reference",
}


def ensure_dirs():
    ANNOTATION_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_DIR.mkdir(parents=True, exist_ok=True)


def read_csv_or_tsv(path):
    if not path.exists():
        return []

    with path.open("r", encoding="utf-8-sig", newline="") as f:
        sample = f.read(4096)
        f.seek(0)
        delimiter = "\t" if "\t" in sample else ","
        return list(csv.DictReader(f, delimiter=delimiter))


def load_queries():
    query_map = {}

    files = []
    files.extend(METADATA_DIR.glob("*query*.csv"))
    files.extend(METADATA_DIR.glob("*query*.tsv"))
    files.extend(METADATA_DIR.glob("*queries*.csv"))
    files.extend(METADATA_DIR.glob("*queries*.tsv"))

    for path in files:
        rows = read_csv_or_tsv(path)

        for row in rows:
            row_l = {k.strip().lower(): v for k, v in row.items()}

            qid = (
                row_l.get("query_id")
                or row_l.get("qid")
                or row_l.get("id")
                or ""
            ).strip()

            if not qid:
                continue

            query = (
                row_l.get("query")
                or row_l.get("question")
                or row_l.get("text")
                or ""
            ).strip()

            query_type = (
                row_l.get("query_type")
                or row_l.get("type")
                or "unknown"
            ).strip()

            query_map[qid] = {
                "query_id": qid,
                "query": query,
                "query_type": query_type,
            }

    return query_map


def load_qrels():
    qrels_path = METADATA_DIR / "qrels.tsv"

    if not qrels_path.exists():
        qrels_path = METADATA_DIR / "qrels.csv"

    if not qrels_path.exists():
        raise FileNotFoundError("qrels file not found in data/metadata")

    with qrels_path.open("r", encoding="utf-8-sig", newline="") as f:
        sample = f.read(4096)
        f.seek(0)
        delimiter = "\t" if "\t" in sample else ","
        rows = list(csv.reader(f, delimiter=delimiter))

    qrels = defaultdict(list)

    first = [x.strip().lower() for x in rows[0]]
    has_header = "query_id" in first or "qid" in first or "page_id" in first or "doc_id" in first

    if has_header:
        header = first
        data_rows = rows[1:]

        def find_col(names, default=None):
            for name in names:
                if name in header:
                    return header.index(name)
            return default

        qid_idx = find_col(["query_id", "qid"], 0)
        page_idx = find_col(["page_id", "doc_id", "docid"], 1)
        rel_idx = find_col(["relevance", "rel", "label"], None)

        for row in data_rows:
            if len(row) <= max(qid_idx, page_idx):
                continue

            qid = row[qid_idx].strip()
            page_id = row[page_idx].strip()

            rel = 1.0
            if rel_idx is not None and rel_idx < len(row):
                try:
                    rel = float(row[rel_idx])
                except Exception:
                    rel = 1.0

            if qid and page_id and rel > 0:
                qrels[qid].append(page_id)

    else:
        for row in rows:
            if len(row) >= 4:
                qid = row[0].strip()
                page_id = row[2].strip()

                try:
                    rel = float(row[3])
                except Exception:
                    rel = 1.0

                if qid and page_id and rel > 0:
                    qrels[qid].append(page_id)

            elif len(row) >= 2:
                qid = row[0].strip()
                page_id = row[1].strip()

                if qid and page_id:
                    qrels[qid].append(page_id)

    return dict(qrels)


def load_run_file(path):
    run = defaultdict(list)

    with path.open("r", encoding="utf-8-sig", newline="") as f:
        sample = f.read(4096)
        f.seek(0)
        delimiter = "\t" if "\t" in sample else ","
        reader = csv.DictReader(f, delimiter=delimiter)

        for row in reader:
            row_l = {k.strip().lower(): v for k, v in row.items()}

            qid = (
                row_l.get("query_id")
                or row_l.get("qid")
                or ""
            ).strip()

            page_id = (
                row_l.get("page_id")
                or row_l.get("doc_id")
                or row_l.get("docid")
                or ""
            ).strip()

            if not qid or not page_id:
                continue

            try:
                rank = int(float(row_l.get("rank", 999999)))
            except Exception:
                rank = 999999

            run[qid].append((rank, page_id))

    final = {}

    for qid, items in run.items():
        final[qid] = [page_id for rank, page_id in sorted(items, key=lambda x: x[0])]

    return final


def find_retrievable_info(qrels):
    run_files = []

    search_dirs = [
        PROJECT_ROOT / "results" / "week7" / "c2f_fixed_N",
        PROJECT_ROOT / "results" / "week7" / "hybrid_fusion",
    ]

    for d in search_dirs:
        if d.exists():
            run_files.extend(d.glob("*_run.tsv"))

    info = defaultdict(lambda: {
        "retrievable": "no",
        "best_rank": "",
        "matched_run": "",
    })

    for run_path in run_files:
        run = load_run_file(run_path)

        for qid, gold_pages in qrels.items():
            ranked = run.get(qid, [])

            for gold_page in gold_pages:
                if gold_page in ranked:
                    rank = ranked.index(gold_page) + 1

                    old_rank = info[qid]["best_rank"]

                    if old_rank == "" or rank < int(old_rank):
                        info[qid] = {
                            "retrievable": "yes",
                            "best_rank": str(rank),
                            "matched_run": str(run_path.relative_to(PROJECT_ROOT)),
                        }

    return info


def qid_key(qid):
    nums = re.findall(r"\d+", qid)

    if nums:
        return int(nums[-1])

    return 999999


def build_candidates():
    queries = load_queries()
    qrels = load_qrels()
    retrievable_info = find_retrievable_info(qrels)

    candidates = []

    for qid, gold_pages in qrels.items():
        meta = queries.get(qid, {})
        query_type = meta.get("query_type", "unknown")

        priority = TYPE_PRIORITY.get(query_type, 99)
        retrievable = retrievable_info[qid]["retrievable"]

        score = 0
        score += 100 - priority * 10
        score += 30 if retrievable == "yes" else 0

        candidates.append({
            "query_id": qid,
            "query": meta.get("query", ""),
            "gold_page_id": gold_pages[0],
            "query_type": query_type,
            "page_type": PAGE_TYPE_MAP.get(query_type, "unknown"),
            "evidence_type": EVIDENCE_TYPE_MAP.get(query_type, "region"),
            "retrievable": retrievable,
            "best_rank": retrievable_info[qid]["best_rank"],
            "matched_run": retrievable_info[qid]["matched_run"],
            "selection_score": score,
            "priority": priority,
        })

    candidates.sort(
        key=lambda x: (
            -x["selection_score"],
            x["priority"],
            qid_key(x["query_id"]),
        )
    )

    return candidates


def select_subset(candidates):
    selected = []
    selected_qids = set()
    type_count = defaultdict(int)

    for qtype, quota in TYPE_QUOTA.items():
        pool = [x for x in candidates if x["query_type"] == qtype]

        for item in pool:
            if len(selected) >= TARGET_N:
                break

            if type_count[qtype] >= quota:
                break

            if item["query_id"] in selected_qids:
                continue

            selected.append(item)
            selected_qids.add(item["query_id"])
            type_count[qtype] += 1

    if len(selected) < TARGET_N:
        for item in candidates:
            if len(selected) >= TARGET_N:
                break

            if item["query_id"] in selected_qids:
                continue

            selected.append(item)
            selected_qids.add(item["query_id"])

    selected.sort(key=lambda x: qid_key(x["query_id"]))

    return selected


def write_jsonl(path, rows):
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_candidates_csv(candidates):
    fieldnames = [
        "query_id",
        "query",
        "gold_page_id",
        "query_type",
        "page_type",
        "evidence_type",
        "retrievable",
        "best_rank",
        "matched_run",
        "selection_score",
        "priority",
    ]

    with OUTPUT_CANDIDATES.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(candidates)


def write_report(selected):
    lines = []
    lines.append("# Week 7 Day 4 Evidence Query Subset Selection Report")
    lines.append("")
    lines.append("| Query ID | Query Type | Gold Page | Evidence Type | Retrievable | Best Rank |")
    lines.append("|---|---|---|---|---|---:|")

    for x in selected:
        lines.append(
            "| {} | {} | {} | {} | {} | {} |".format(
                x["query_id"],
                x["query_type"],
                x["gold_page_id"],
                x["evidence_type"],
                x["retrievable"],
                x["best_rank"] or "-",
            )
        )

    OUTPUT_REPORT.write_text("\n".join(lines), encoding="utf-8")


def main():
    ensure_dirs()

    candidates = build_candidates()
    selected = select_subset(candidates)

    subset_rows = []
    region_rows = []

    for x in selected:
        subset_rows.append({
            "query_id": x["query_id"],
            "query": x["query"],
            "gold_page_id": x["gold_page_id"],
            "query_type": x["query_type"],
            "page_type": x["page_type"],
            "evidence_type": x["evidence_type"],
        })

        region_rows.append({
            "query_id": x["query_id"],
            "page_id": x["gold_page_id"],
            "region_id": "r1",
            "bbox": [0, 0, 0, 0],
            "region_type": x["evidence_type"],
            "evidence_note": "TODO",
            "bbox_status": "todo",
        })

    write_candidates_csv(candidates)
    write_jsonl(OUTPUT_SUBSET, subset_rows)
    write_jsonl(OUTPUT_REGIONS, region_rows)
    write_report(selected)

    print("[Week7-Day4] Evidence subset selected.")
    print("Selected count:", len(selected))
    print("Subset:", OUTPUT_SUBSET)
    print("Regions:", OUTPUT_REGIONS)
    print("Candidates:", OUTPUT_CANDIDATES)
    print("Report:", OUTPUT_REPORT)
    print("")
    print("query_id,query_type,gold_page_id,evidence_type,retrievable,best_rank")

    for x in selected:
        print(
            "{},{},{},{},{},{}".format(
                x["query_id"],
                x["query_type"],
                x["gold_page_id"],
                x["evidence_type"],
                x["retrievable"],
                x["best_rank"] or "-",
            )
        )


if __name__ == "__main__":
    main()
