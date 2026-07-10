from pathlib import Path
from collections import defaultdict
import json
import csv


PROJECT_ROOT = Path(r"E:\Working\PCB_VisualRAG_Project")

SUBSET_PATH = PROJECT_ROOT / "data" / "annotations" / "evidence_query_subset.jsonl"
REGIONS_PATH = PROJECT_ROOT / "data" / "annotations" / "evidence_regions.jsonl"
SCREENSHOT_DIR = PROJECT_ROOT / "artifacts" / "evidence_annotation_screenshots"
RESULT_DIR = PROJECT_ROOT / "results" / "week7" / "evidence_annotation"

OUTPUT_CSV = RESULT_DIR / "evidence_annotation_validation.csv"
OUTPUT_MD = RESULT_DIR / "evidence_annotation_validation.md"

MIN_SAMPLES = 8
MAX_SAMPLES = 12


def load_jsonl(path):
    rows = []

    with path.open("r", encoding="utf-8-sig") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()

            if not line:
                continue

            try:
                row = json.loads(line)
                row["_line_no"] = line_no
                rows.append(row)
            except Exception as e:
                rows.append({
                    "_line_no": line_no,
                    "_parse_error": str(e),
                })

    return rows


def check_bbox(bbox):
    if not isinstance(bbox, list):
        return False, "bbox_not_list"

    if len(bbox) != 4:
        return False, "bbox_len_not_4"

    try:
        x1, y1, x2, y2 = [float(v) for v in bbox]
    except Exception:
        return False, "bbox_not_numeric"

    if x1 < 0 or y1 < 0 or x2 < 0 or y2 < 0:
        return False, "bbox_negative"

    if x2 <= x1 or y2 <= y1:
        return False, "bbox_invalid_or_zero_area"

    width = x2 - x1
    height = y2 - y1
    area = width * height

    if area <= 0:
        return False, "bbox_zero_area"

    if width > 3000 or height > 3000:
        return False, "bbox_too_large_dimension"

    if area > 2500000:
        return False, "bbox_too_large_area"

    return True, "ok"


def has_screenshot(qid):
    patterns = [
        "{}_*.png".format(qid),
        "{}_*.jpg".format(qid),
        "{}_*.jpeg".format(qid),
    ]

    for pattern in patterns:
        if list(SCREENSHOT_DIR.glob(pattern)):
            return True

    return False


def main():
    RESULT_DIR.mkdir(parents=True, exist_ok=True)

    subset = load_jsonl(SUBSET_PATH)
    regions = load_jsonl(REGIONS_PATH)

    subset_qids = set()
    region_by_qid = defaultdict(list)

    validation_rows = []
    global_status = "PASSED"

    if len(subset) < MIN_SAMPLES or len(subset) > MAX_SAMPLES:
        global_status = "FAILED"
        validation_rows.append({
            "file": "evidence_query_subset.jsonl",
            "line_no": "",
            "query_id": "",
            "page_id": "",
            "region_id": "",
            "bbox": "",
            "status": "FAILED",
            "reason": "sample_count_not_in_8_to_12",
        })

    for row in subset:
        qid = row.get("query_id", "")
        gold_page_id = row.get("gold_page_id", "")

        status = "PASSED"
        reasons = []

        if "_parse_error" in row:
            status = "FAILED"
            reasons.append("json_parse_error")

        if not qid:
            status = "FAILED"
            reasons.append("missing_query_id")

        if not gold_page_id:
            status = "FAILED"
            reasons.append("missing_gold_page_id")

        if qid and not has_screenshot(qid):
            status = "FAILED"
            reasons.append("missing_screenshot")

        if status == "FAILED":
            global_status = "FAILED"

        if qid:
            subset_qids.add(qid)

        validation_rows.append({
            "file": "evidence_query_subset.jsonl",
            "line_no": row.get("_line_no", ""),
            "query_id": qid,
            "page_id": gold_page_id,
            "region_id": "",
            "bbox": "",
            "status": status,
            "reason": ";".join(reasons),
        })

    for row in regions:
        qid = row.get("query_id", "")
        page_id = row.get("page_id", "")
        region_id = row.get("region_id", "")
        bbox = row.get("bbox", None)
        bbox_status = row.get("bbox_status", "")

        status = "PASSED"
        reasons = []

        if "_parse_error" in row:
            status = "FAILED"
            reasons.append("json_parse_error")

        if not qid:
            status = "FAILED"
            reasons.append("missing_query_id")

        if qid not in subset_qids:
            status = "FAILED"
            reasons.append("query_not_in_subset")

        if not page_id:
            status = "FAILED"
            reasons.append("missing_page_id")

        if not region_id:
            status = "FAILED"
            reasons.append("missing_region_id")

        bbox_ok, bbox_reason = check_bbox(bbox)

        if not bbox_ok:
            status = "FAILED"
            reasons.append(bbox_reason)

        if bbox_status != "done":
            status = "FAILED"
            reasons.append("bbox_status_not_done")

        if status == "FAILED":
            global_status = "FAILED"

        if qid:
            region_by_qid[qid].append(row)

        validation_rows.append({
            "file": "evidence_regions.jsonl",
            "line_no": row.get("_line_no", ""),
            "query_id": qid,
            "page_id": page_id,
            "region_id": region_id,
            "bbox": json.dumps(bbox, ensure_ascii=False),
            "status": status,
            "reason": ";".join(reasons),
        })

    for qid in sorted(subset_qids):
        if len(region_by_qid[qid]) == 0:
            global_status = "FAILED"

            validation_rows.append({
                "file": "evidence_regions.jsonl",
                "line_no": "",
                "query_id": qid,
                "page_id": "",
                "region_id": "",
                "bbox": "",
                "status": "FAILED",
                "reason": "missing_region_for_query",
            })

    with OUTPUT_CSV.open("w", encoding="utf-8", newline="") as f:
        fieldnames = [
            "file",
            "line_no",
            "query_id",
            "page_id",
            "region_id",
            "bbox",
            "status",
            "reason",
        ]

        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(validation_rows)

    failed_rows = [x for x in validation_rows if x["status"] != "PASSED"]

    lines = []
    lines.append("# Week 7 Day 4 Evidence Annotation Validation")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append("- subset_count: {}".format(len(subset)))
    lines.append("- region_count: {}".format(len(regions)))
    lines.append("- failed_count: {}".format(len(failed_rows)))
    lines.append("- global_status: {}".format(global_status))
    lines.append("")
    lines.append("## Failed Items")
    lines.append("")
    lines.append("| File | Line | Query ID | Page ID | Region ID | Status | Reason |")
    lines.append("|---|---:|---|---|---|---|---|")

    if failed_rows:
        for x in failed_rows:
            lines.append(
                "| {} | {} | {} | {} | {} | {} | {} |".format(
                    x["file"],
                    x["line_no"],
                    x["query_id"],
                    x["page_id"],
                    x["region_id"],
                    x["status"],
                    x["reason"],
                )
            )
    else:
        lines.append("| - | - | - | - | - | PASSED | - |")

    OUTPUT_MD.write_text("\n".join(lines), encoding="utf-8")

    print("[Week7-Day4] Evidence annotation validation completed.")
    print("Subset count:", len(subset))
    print("Region count:", len(regions))
    print("Failed count:", len(failed_rows))
    print("Global status:", global_status)
    print("Validation CSV:", OUTPUT_CSV)
    print("Validation MD:", OUTPUT_MD)


if __name__ == "__main__":
    main()
