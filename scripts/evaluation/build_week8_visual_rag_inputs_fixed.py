from pathlib import Path
import json
import csv
from collections import defaultdict


PROJECT_ROOT = Path(r"E:\Working\PCB_VisualRAG_Project")

EVIDENCE_QUERY_SUBSET = PROJECT_ROOT / "data" / "annotations" / "evidence_query_subset.jsonl"
EVIDENCE_REGIONS = PROJECT_ROOT / "data" / "annotations" / "evidence_regions.jsonl"
QUERIES_JSONL = PROJECT_ROOT / "data" / "metadata" / "queries.jsonl"
OCCLUSION_INPUTS = PROJECT_ROOT / "results" / "week7" / "occlusion" / "occlusion_inputs.csv"

OUTPUT_DIR = PROJECT_ROOT / "results" / "week8" / "visual_rag"
OUTPUT_JSONL = OUTPUT_DIR / "qa_inputs_fixed.jsonl"
OUTPUT_CSV = OUTPUT_DIR / "qa_inputs_fixed.csv"
OUTPUT_MD = OUTPUT_DIR / "qa_inputs_fixed_preview.md"
SUMMARY_CSV = OUTPUT_DIR / "qa_input_mapping_summary.csv"

RUN_CANDIDATES = {
    "BM25": [
        PROJECT_ROOT / "results" / "week7" / "hybrid_fusion" / "hybrid_fullmv_N50_alpha1p0_run.tsv",
    ],
    "Full MV": [
        PROJECT_ROOT / "results" / "week7" / "c2f_fixed_N" / "bm25_fullmv_N10_run.tsv",
    ],
    "Hybrid Fusion": [
        PROJECT_ROOT / "results" / "week7" / "hybrid_fusion" / "hybrid_budgetmv_N50_M24_alpha1p0_run.tsv",
    ],
    "Budgeted MV": [
        PROJECT_ROOT / "results" / "week7" / "c2f_fixed_N" / "bm25_budgetmv_N20_M8_none_run.tsv",
    ],
}


def read_jsonl(path):
    rows = []
    if not path.exists():
        return rows

    with path.open("r", encoding="utf-8-sig") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))

    return rows


def read_csv(path):
    if not path.exists():
        return []

    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def safe_int(value, default=999999):
    try:
        if value is None or value == "":
            return default
        return int(float(value))
    except Exception:
        return default


def safe_float(value, default=""):
    try:
        if value is None or value == "":
            return default
        return float(value)
    except Exception:
        return default


def get_query_text(row):
    for key in ["query", "question", "text", "query_text"]:
        value = row.get(key, "")
        if str(value).strip():
            return str(value).strip()
    return ""


def get_gold_page_id(row):
    for key in ["gold_page_id", "page_id", "doc_id", "target_page_id"]:
        value = row.get(key, "")
        if str(value).strip():
            return str(value).strip()

    golds = row.get("gold_page_ids", [])
    if isinstance(golds, list) and golds:
        return str(golds[0])

    return ""


def parse_bbox(v):
    if isinstance(v, list):
        return v

    try:
        return json.loads(v)
    except Exception:
        return []


def find_page_image(page_id):
    if not page_id:
        return ""

    if "_p" not in page_id:
        return ""

    doc_id = page_id.split("_p")[0]

    candidates = [
        PROJECT_ROOT / "data" / "images" / doc_id / f"{page_id}.png",
        PROJECT_ROOT / "data" / "images" / doc_id / f"{page_id}.jpg",
        PROJECT_ROOT / "data" / "images" / f"{page_id}.png",
        PROJECT_ROOT / "data" / "images" / f"{page_id}.jpg",
    ]

    for path in candidates:
        if path.exists():
            return str(path.relative_to(PROJECT_ROOT))

    image_root = PROJECT_ROOT / "data" / "images"
    if image_root.exists():
        found = list(image_root.rglob(f"{page_id}.*"))
        if found:
            return str(found[0].relative_to(PROJECT_ROOT))

    return ""


def is_header_line(line):
    low = line.lower().strip()

    if not low:
        return True

    if low.startswith("run_name"):
        return True

    if low.startswith("query"):
        return True

    if low.startswith("qid"):
        return True

    if "query_id" in low and "page_id" in low:
        return True

    return False


def parse_run_line(line):
    line = line.strip()

    if not line:
        return None

    if is_header_line(line):
        return None

    parts_tab = line.split("\t")
    parts_space = line.split()

    if len(parts_tab) >= 5:
        parts = parts_tab
    else:
        parts = parts_space

    parts = [p.strip() for p in parts if p.strip()]

    if len(parts) < 2:
        return None

    # Format 1:
    # run_name query_id page_id rank score
    if len(parts) >= 5 and parts[1].startswith("q") and "_p" in parts[2]:
        qid = parts[1]
        page_id = parts[2]
        rank = safe_int(parts[3])
        score = safe_float(parts[4])
        return qid, page_id, rank, score

    # Format 2:
    # query_id Q0 page_id rank score run_name
    if len(parts) >= 6 and parts[1].upper() == "Q0":
        qid = parts[0]
        page_id = parts[2]
        rank = safe_int(parts[3])
        score = safe_float(parts[4])
        return qid, page_id, rank, score

    # Format 3:
    # query_id page_id rank score
    if len(parts) >= 4 and parts[0].startswith("q") and "_p" in parts[1]:
        qid = parts[0]
        page_id = parts[1]
        rank = safe_int(parts[2])
        score = safe_float(parts[3])
        return qid, page_id, rank, score

    return None


def read_run(path):
    result = {}

    if not path.exists():
        return result

    with path.open("r", encoding="utf-8-sig", errors="ignore") as f:
        for line in f:
            parsed = parse_run_line(line)

            if parsed is None:
                continue

            qid, page_id, rank, score = parsed

            if not qid or not page_id:
                continue

            new_rank = safe_int(rank)

            if qid not in result:
                result[qid] = {
                    "page_id": page_id,
                    "rank": new_rank,
                    "score": score,
                    "run_file": str(path.relative_to(PROJECT_ROOT)),
                }
            else:
                old_rank = safe_int(result[qid].get("rank", 999999))
                if new_rank < old_rank:
                    result[qid] = {
                        "page_id": page_id,
                        "rank": new_rank,
                        "score": score,
                        "run_file": str(path.relative_to(PROJECT_ROOT)),
                    }

    return result


def load_best_available_runs():
    run_maps = {}
    used_files = {}

    for setting, candidates in RUN_CANDIDATES.items():
        selected_path = None
        selected_map = {}

        for path in candidates:
            if path.exists():
                m = read_run(path)
                if m:
                    selected_path = path
                    selected_map = m
                    break

        run_maps[setting] = selected_map
        used_files[setting] = str(selected_path.relative_to(PROJECT_ROOT)) if selected_path else ""

    return run_maps, used_files


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    subset_rows = read_jsonl(EVIDENCE_QUERY_SUBSET)
    region_rows = read_jsonl(EVIDENCE_REGIONS)
    query_rows = read_jsonl(QUERIES_JSONL)
    occlusion_rows = read_csv(OCCLUSION_INPUTS)

    query_text_map = {}

    for row in query_rows:
        qid = row.get("query_id", "")
        query_text_map[qid] = get_query_text(row)

    for row in subset_rows:
        qid = row.get("query_id", "")
        text = get_query_text(row)
        if text:
            query_text_map[qid] = text

    region_map = {}

    for row in region_rows:
        qid = row.get("query_id", "")
        region_map[qid] = {
            "bbox": parse_bbox(row.get("bbox", [])),
            "page_id": get_gold_page_id(row),
            "region_id": row.get("region_id", ""),
        }

    occlusion_map = defaultdict(dict)

    for row in occlusion_rows:
        qid = row.get("query_id", "")
        condition = row.get("condition", "")
        occlusion_map[qid][condition] = row

    run_maps, used_files = load_best_available_runs()

    output_rows = []

    for row in subset_rows:
        qid = row.get("query_id", "")
        query_text = query_text_map.get(qid, "")
        gold_page_id = get_gold_page_id(row)

        if not gold_page_id and qid in region_map:
            gold_page_id = region_map[qid].get("page_id", "")

        bbox = region_map.get(qid, {}).get("bbox", [])

        original_occ = occlusion_map[qid].get("Original", {})
        gold_mask_occ = occlusion_map[qid].get("Gold Mask", {})
        random_mask_occ = occlusion_map[qid].get("Random Mask", {})

        base = {
            "query_id": qid,
            "query": query_text,
            "gold_page_id": gold_page_id,
            "gold_bbox": json.dumps(bbox, ensure_ascii=False),
        }

        output_rows.append({
            **base,
            "setting": "Gold Evidence",
            "page_id": gold_page_id,
            "rank": "",
            "retrieval_score": "",
            "image_path": original_occ.get("image_path", find_page_image(gold_page_id)),
            "is_gold_page": "1",
            "source": "gold evidence page",
            "run_file": "",
        })

        for setting in ["BM25", "Full MV", "Hybrid Fusion", "Budgeted MV"]:
            item = run_maps.get(setting, {}).get(qid, {})
            page_id = item.get("page_id", "")

            output_rows.append({
                **base,
                "setting": setting,
                "page_id": page_id,
                "rank": item.get("rank", ""),
                "retrieval_score": item.get("score", ""),
                "image_path": find_page_image(page_id),
                "is_gold_page": "1" if page_id == gold_page_id else "0",
                "source": "retrieval result",
                "run_file": item.get("run_file", used_files.get(setting, "")),
            })

        output_rows.append({
            **base,
            "setting": "Gold Masked",
            "page_id": gold_mask_occ.get("page_id", gold_page_id),
            "rank": "",
            "retrieval_score": "",
            "image_path": gold_mask_occ.get("image_path", ""),
            "is_gold_page": "1",
            "source": "occlusion gold mask",
            "run_file": str(OCCLUSION_INPUTS.relative_to(PROJECT_ROOT)) if OCCLUSION_INPUTS.exists() else "",
        })

        output_rows.append({
            **base,
            "setting": "Random Masked",
            "page_id": random_mask_occ.get("page_id", gold_page_id),
            "rank": "",
            "retrieval_score": "",
            "image_path": random_mask_occ.get("image_path", ""),
            "is_gold_page": "1",
            "source": "occlusion random mask",
            "run_file": str(OCCLUSION_INPUTS.relative_to(PROJECT_ROOT)) if OCCLUSION_INPUTS.exists() else "",
        })

    fieldnames = [
        "query_id",
        "query",
        "setting",
        "gold_page_id",
        "page_id",
        "rank",
        "retrieval_score",
        "image_path",
        "is_gold_page",
        "gold_bbox",
        "source",
        "run_file",
    ]

    with OUTPUT_JSONL.open("w", encoding="utf-8") as f:
        for row in output_rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    with OUTPUT_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in output_rows:
            writer.writerow({k: row.get(k, "") for k in fieldnames})

    summary_rows = []

    for setting in [
        "Gold Evidence",
        "BM25",
        "Full MV",
        "Hybrid Fusion",
        "Budgeted MV",
        "Gold Masked",
        "Random Masked",
    ]:
        rows = [r for r in output_rows if r["setting"] == setting]
        mapped_page = sum(1 for r in rows if r.get("page_id"))
        mapped_image = sum(1 for r in rows if r.get("image_path"))
        gold_hits = sum(1 for r in rows if r.get("is_gold_page") == "1")

        summary_rows.append({
            "setting": setting,
            "total": len(rows),
            "mapped_page_id": mapped_page,
            "mapped_image_path": mapped_image,
            "gold_page_hits": gold_hits,
            "used_run_file": used_files.get(setting, ""),
        })

    with SUMMARY_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "setting",
                "total",
                "mapped_page_id",
                "mapped_image_path",
                "gold_page_hits",
                "used_run_file",
            ],
        )
        writer.writeheader()
        writer.writerows(summary_rows)

    lines = []
    lines.append("# Week 8 Visual RAG QA Inputs Fixed Preview")
    lines.append("")
    lines.append("| Query ID | Setting | Gold Page | Input Page | Rank | Score | Is Gold | Image Path |")
    lines.append("|---|---|---|---|---:|---:|---:|---|")

    for row in output_rows:
        lines.append(
            "| {} | {} | {} | {} | {} | {} | {} | {} |".format(
                row.get("query_id", ""),
                row.get("setting", ""),
                row.get("gold_page_id", ""),
                row.get("page_id", ""),
                row.get("rank", ""),
                row.get("retrieval_score", ""),
                row.get("is_gold_page", ""),
                row.get("image_path", ""),
            )
        )

    OUTPUT_MD.write_text("\n".join(lines), encoding="utf-8")

    print("[Week8] Fixed QA inputs generated.")
    print("Rows:", len(output_rows))
    print("Wrote:", OUTPUT_JSONL)
    print("Wrote:", OUTPUT_CSV)
    print("Wrote:", OUTPUT_MD)
    print("Wrote:", SUMMARY_CSV)
    print()
    print("Used run files:")
    for k, v in used_files.items():
        print(f"{k}: {v}")
    print()
    print("Mapping summary:")
    for row in summary_rows:
        print(row)
    print()
    print("Missing summary:")
    print("missing_page:", sum(1 for r in output_rows if not r.get("page_id")))
    print("missing_image:", sum(1 for r in output_rows if not r.get("image_path")))
    print("retrieval_missing_page:", sum(1 for r in output_rows if r.get("setting") in ["BM25", "Full MV", "Hybrid Fusion", "Budgeted MV"] and not r.get("page_id")))
    print("retrieval_missing_image:", sum(1 for r in output_rows if r.get("setting") in ["BM25", "Full MV", "Hybrid Fusion", "Budgeted MV"] and not r.get("image_path")))


if __name__ == "__main__":
    main()
