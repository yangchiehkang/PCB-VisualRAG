from pathlib import Path
import json
import csv
from collections import defaultdict


PROJECT_ROOT = Path(r"E:\Working\PCB_VisualRAG_Project")

EVIDENCE_QUERY_SUBSET = PROJECT_ROOT / "data" / "annotations" / "evidence_query_subset.jsonl"
EVIDENCE_REGIONS = PROJECT_ROOT / "data" / "annotations" / "evidence_regions.jsonl"
QUERIES_JSONL = PROJECT_ROOT / "data" / "metadata" / "queries.jsonl"

OCCLUSION_INPUTS = PROJECT_ROOT / "results" / "week7" / "occlusion" / "occlusion_inputs.csv"

RUN_FILES = {
    "BM25": PROJECT_ROOT / "results" / "week7" / "hybrid_fusion" / "hybrid_fullmv_N50_alpha1p0_run.tsv",
    "Full MV": PROJECT_ROOT / "results" / "week7" / "c2f_fixed_N" / "bm25_fullmv_N10_run.tsv",
    "Hybrid Fusion": PROJECT_ROOT / "results" / "week7" / "hybrid_fusion" / "hybrid_budgetmv_N50_M24_alpha1p0_run.tsv",
    "Budgeted MV": PROJECT_ROOT / "results" / "week7" / "c2f_fixed_N" / "bm25_budgetmv_N20_M8_none_run.tsv",
}

OUTPUT_DIR = PROJECT_ROOT / "results" / "week8" / "visual_rag"
OUTPUT_JSONL = OUTPUT_DIR / "qa_inputs.jsonl"
OUTPUT_CSV = OUTPUT_DIR / "qa_inputs.csv"
OUTPUT_MD = OUTPUT_DIR / "qa_inputs_preview.md"


SETTINGS_ORDER = [
    "Gold Evidence",
    "BM25",
    "Full MV",
    "Hybrid Fusion",
    "Budgeted MV",
    "Gold Masked",
    "Random Masked",
]


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


def get_query_text(row):
    for key in ["query", "question", "text", "query_text"]:
        if key in row and str(row[key]).strip():
            return str(row[key]).strip()
    return ""


def get_gold_page_id(row):
    for key in ["gold_page_id", "page_id", "doc_id", "target_page_id"]:
        if key in row and str(row[key]).strip():
            return str(row[key]).strip()
    return ""


def parse_bbox(v):
    if isinstance(v, list):
        return v

    try:
        return json.loads(v)
    except Exception:
        return []


def read_trec_run(path):
    result = {}

    if not path.exists():
        return result

    with path.open("r", encoding="utf-8-sig") as f:
        for line in f:
            line = line.strip()

            if not line or line.lower().startswith("query"):
                continue

            parts = line.split()

            if len(parts) >= 6:
                qid = parts[0]
                docid = parts[2]
                rank = int(float(parts[3]))
                score = float(parts[4])

                if qid not in result or rank < result[qid]["rank"]:
                    result[qid] = {
                        "page_id": docid,
                        "rank": rank,
                        "score": score,
                        "run_file": str(path.relative_to(PROJECT_ROOT)),
                    }

    return result


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

    run_maps = {name: read_trec_run(path) for name, path in RUN_FILES.items()}

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

        if original_occ:
            original_image_path = original_occ.get("image_path", "")
        else:
            original_image_path = ""

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
            "image_path": original_image_path,
            "source": "gold evidence page",
            "run_file": "",
        })

        for setting in ["BM25", "Full MV", "Hybrid Fusion", "Budgeted MV"]:
            item = run_maps.get(setting, {}).get(qid, {})
            output_rows.append({
                **base,
                "setting": setting,
                "page_id": item.get("page_id", ""),
                "rank": item.get("rank", ""),
                "retrieval_score": item.get("score", ""),
                "image_path": "",
                "source": "retrieval result",
                "run_file": item.get("run_file", ""),
            })

        output_rows.append({
            **base,
            "setting": "Gold Masked",
            "page_id": gold_mask_occ.get("page_id", gold_page_id),
            "rank": "",
            "retrieval_score": "",
            "image_path": gold_mask_occ.get("image_path", ""),
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
            "source": "occlusion random mask",
            "run_file": str(OCCLUSION_INPUTS.relative_to(PROJECT_ROOT)) if OCCLUSION_INPUTS.exists() else "",
        })

    with OUTPUT_JSONL.open("w", encoding="utf-8") as f:
        for row in output_rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    fieldnames = [
        "query_id",
        "query",
        "setting",
        "gold_page_id",
        "page_id",
        "rank",
        "retrieval_score",
        "image_path",
        "gold_bbox",
        "source",
        "run_file",
    ]

    with OUTPUT_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for row in output_rows:
            writer.writerow({k: row.get(k, "") for k in fieldnames})

    lines = []
    lines.append("# Week 8 Visual RAG QA Inputs Preview")
    lines.append("")
    lines.append("| Query ID | Setting | Gold Page | Input Page | Rank | Image Path |")
    lines.append("|---|---|---|---|---:|---|")

    for row in output_rows[:80]:
        lines.append(
            "| {} | {} | {} | {} | {} | {} |".format(
                row.get("query_id", ""),
                row.get("setting", ""),
                row.get("gold_page_id", ""),
                row.get("page_id", ""),
                row.get("rank", ""),
                row.get("image_path", ""),
            )
        )

    OUTPUT_MD.write_text("\n".join(lines), encoding="utf-8")

    print("[Week8-Day1] QA inputs generated.")
    print("Rows:", len(output_rows))
    print("Queries:", len(subset_rows))
    print("Settings per query:", len(SETTINGS_ORDER))
    print("Wrote:", OUTPUT_JSONL)
    print("Wrote:", OUTPUT_CSV)
    print("Wrote:", OUTPUT_MD)

    missing_query_text = [r["query_id"] for r in output_rows if r["setting"] == "Gold Evidence" and not r["query"]]
    missing_images = [r for r in output_rows if r["setting"] in ["Gold Evidence", "Gold Masked", "Random Masked"] and not r["image_path"]]

    print("")
    print("Missing query text count:", len(missing_query_text))
    if missing_query_text:
        print("Missing query text:", ",".join(missing_query_text))

    print("Missing image path count:", len(missing_images))


if __name__ == "__main__":
    main()
