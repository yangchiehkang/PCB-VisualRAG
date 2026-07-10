from pathlib import Path
from collections import defaultdict
import csv
import json
import cv2
import numpy as np


PROJECT_ROOT = Path(r"E:\Working\PCB_VisualRAG_Project")

SUBSET_PATH = PROJECT_ROOT / "data" / "annotations" / "evidence_query_subset.jsonl"
REGIONS_PATH = PROJECT_ROOT / "data" / "annotations" / "evidence_regions.jsonl"

RESULT_DIR = PROJECT_ROOT / "results" / "week7" / "region_hit"

C2F_DIR = PROJECT_ROOT / "results" / "week7" / "c2f_fixed_N"
HYBRID_DIR = PROJECT_ROOT / "results" / "week7" / "hybrid_fusion"

OUTPUT_RESULTS_CSV = RESULT_DIR / "region_hit_atk_results.csv"
OUTPUT_RESULTS_MD = RESULT_DIR / "region_hit_atk_results.md"
OUTPUT_PER_QUERY_CSV = RESULT_DIR / "region_hit_atk_per_query.csv"
OUTPUT_PATCH_CSV = RESULT_DIR / "region_hit_top_patches.csv"
OUTPUT_JSON = RESULT_DIR / "region_hit_atk_summary.json"

KS = [1, 3, 5]
IOU_THRESHOLD = 0.3
PATCH_GRID = 7

METHOD_CONFIGS = [
    {
        "method": "Full MV",
        "run_files": [
            C2F_DIR / "bm25_fullmv_N50_run.tsv",
            C2F_DIR / "bm25_fullmv_N10_run.tsv",
            C2F_DIR / "bm25_fullmv_N20_run.tsv",
            C2F_DIR / "bm25_fullmv_N100_run.tsv",
        ],
        "token_budget": None,
    },
    {
        "method": "Budgeted MV",
        "run_files": [
            C2F_DIR / "bm25_budgetmv_N50_M24_none_run.tsv",
            C2F_DIR / "bm25_budgetmv_N20_M8_none_run.tsv",
            C2F_DIR / "bm25_budgetmv_N20_M16_none_run.tsv",
        ],
        "token_budget": 24,
    },
    {
        "method": "BM25 + Budgeted MV",
        "run_files": [
            C2F_DIR / "bm25_budgetmv_N20_M8_none_run.tsv",
            C2F_DIR / "bm25_budgetmv_N20_M16_none_run.tsv",
            C2F_DIR / "bm25_budgetmv_N50_M24_none_run.tsv",
        ],
        "token_budget": 24,
    },
    {
        "method": "Hybrid Fusion",
        "run_files": [
            HYBRID_DIR / "hybrid_budgetmv_N50_M24_alpha0p8_run.tsv",
            HYBRID_DIR / "hybrid_budgetmv_N50_M24_alpha0p9_run.tsv",
            HYBRID_DIR / "hybrid_budgetmv_N50_M24_alpha1p0_run.tsv",
            HYBRID_DIR / "hybrid_fullmv_N50_alpha0p8_run.tsv",
            HYBRID_DIR / "hybrid_fullmv_N50_alpha1p0_run.tsv",
        ],
        "token_budget": 24,
    },
]

IMAGE_ROOTS = [
    PROJECT_ROOT / "data",
    PROJECT_ROOT / "artifacts",
    PROJECT_ROOT / "results",
]

IMAGE_EXTS = [".png", ".jpg", ".jpeg"]


def load_jsonl(path):
    rows = []

    with path.open("r", encoding="utf-8-sig") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))

    return rows


def choose_run_file(paths):
    for path in paths:
        if path.exists():
            return path
    return None


def read_run(path):
    run = defaultdict(list)

    if path is None or not path.exists():
        return {}

    with path.open("r", encoding="utf-8-sig", newline="") as f:
        sample = f.read(4096)
        f.seek(0)
        delimiter = "\t" if "\t" in sample else ","
        rows = list(csv.reader(f, delimiter=delimiter))

    if not rows:
        return {}

    header = [x.strip().lower() for x in rows[0]]
    has_header = "query_id" in header or "qid" in header or "page_id" in header or "doc_id" in header

    if has_header:
        data_rows = rows[1:]

        def idx(names, default=None):
            for name in names:
                if name in header:
                    return header.index(name)
            return default

        qid_idx = idx(["query_id", "qid"], None)
        page_idx = idx(["page_id", "doc_id", "docid"], None)
        rank_idx = idx(["rank"], None)
        score_idx = idx(["score"], None)

        for i, row in enumerate(data_rows):
            if qid_idx is None or page_idx is None:
                continue

            if len(row) <= max(qid_idx, page_idx):
                continue

            qid = row[qid_idx].strip()
            page_id = row[page_idx].strip()

            if not qid or not page_id:
                continue

            try:
                rank = int(float(row[rank_idx])) if rank_idx is not None and rank_idx < len(row) else i + 1
            except Exception:
                rank = i + 1

            try:
                score = float(row[score_idx]) if score_idx is not None and score_idx < len(row) else 0.0
            except Exception:
                score = 0.0

            run[qid].append((rank, page_id, score))

    else:
        for i, row in enumerate(rows):
            if len(row) >= 6 and row[1].strip().upper() == "Q0":
                qid = row[0].strip()
                page_id = row[2].strip()
                rank = int(float(row[3]))
                score = float(row[4])
                run[qid].append((rank, page_id, score))

            elif len(row) >= 5:
                qid = row[1].strip()
                page_id = row[2].strip()
                rank = int(float(row[3]))
                score = float(row[4])
                run[qid].append((rank, page_id, score))

    final = {}

    for qid, items in run.items():
        items = sorted(items, key=lambda x: (x[0], -x[2]))
        final[qid] = [page_id for rank, page_id, score in items]

    return final


def find_image(page_id):
    for root in IMAGE_ROOTS:
        if not root.exists():
            continue

        for ext in IMAGE_EXTS:
            matches = list(root.rglob(page_id + ext))
            if matches:
                return matches[0]

    for root in IMAGE_ROOTS:
        if not root.exists():
            continue

        for ext in IMAGE_EXTS:
            matches = list(root.rglob("*" + page_id + "*" + ext))
            if matches:
                return matches[0]

    return None


def iou(box_a, box_b):
    ax1, ay1, ax2, ay2 = [float(v) for v in box_a]
    bx1, by1, bx2, by2 = [float(v) for v in box_b]

    ix1 = max(ax1, bx1)
    iy1 = max(ay1, by1)
    ix2 = min(ax2, bx2)
    iy2 = min(ay2, by2)

    iw = max(0.0, ix2 - ix1)
    ih = max(0.0, iy2 - iy1)

    inter = iw * ih

    area_a = max(0.0, ax2 - ax1) * max(0.0, ay2 - ay1)
    area_b = max(0.0, bx2 - bx1) * max(0.0, by2 - by1)

    union = area_a + area_b - inter

    if union <= 0:
        return 0.0

    return inter / union


def center_inside(center, bbox):
    x, y = center
    x1, y1, x2, y2 = [float(v) for v in bbox]
    return x1 <= x <= x2 and y1 <= y <= y2


def patch_boxes_for_image(w, h):
    boxes = []

    for r in range(PATCH_GRID):
        for c in range(PATCH_GRID):
            x1 = w * c / PATCH_GRID
            y1 = h * r / PATCH_GRID
            x2 = w * (c + 1) / PATCH_GRID
            y2 = h * (r + 1) / PATCH_GRID

            boxes.append([x1, y1, x2, y2])

    return boxes


def patch_saliency_scores(image_path):
    img = cv2.imread(str(image_path))

    if img is None:
        return None, None, None, None

    h, w = img.shape[:2]

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (5, 5), 0)

    edges = cv2.Canny(gray, 50, 150)
    edges = (edges > 0).astype(np.float32)

    boxes = patch_boxes_for_image(w, h)

    scores = []

    for idx, box in enumerate(boxes):
        x1, y1, x2, y2 = [int(round(v)) for v in box]

        x1 = max(0, min(w - 1, x1))
        y1 = max(0, min(h - 1, y1))
        x2 = max(x1 + 1, min(w, x2))
        y2 = max(y1 + 1, min(h, y2))

        crop = edges[y1:y2, x1:x2]
        score = float(crop.mean()) if crop.size else 0.0

        scores.append(score)

    order = np.argsort(-np.asarray(scores))

    return boxes, scores, order, (w, h)


def validate_regions(regions):
    failed = []

    for row in regions:
        qid = row.get("query_id", "")
        bbox = row.get("bbox", None)
        status = row.get("bbox_status", "")

        if status != "done":
            failed.append((qid, "bbox_status_not_done"))

        if not isinstance(bbox, list) or len(bbox) != 4:
            failed.append((qid, "bbox_invalid"))
            continue

        x1, y1, x2, y2 = [float(v) for v in bbox]

        if x2 <= x1 or y2 <= y1:
            failed.append((qid, "bbox_zero_area"))

    return failed


def main():
    RESULT_DIR.mkdir(parents=True, exist_ok=True)

    subset = load_jsonl(SUBSET_PATH)
    regions = load_jsonl(REGIONS_PATH)

    failed = validate_regions(regions)

    if failed:
        print("[Week7-Day5] Region annotations are not ready.")
        for qid, reason in failed:
            print("FAILED,{},{}".format(qid, reason))
        return

    region_map = {row["query_id"]: row for row in regions}

    results = []
    per_query_rows = []
    patch_rows = []

    print("[Week7-Day5] Auto Region Hit@k evaluation")
    print("Subset:", SUBSET_PATH)
    print("Regions:", REGIONS_PATH)

    for config in METHOD_CONFIGS:
        method = config["method"]
        run_file = choose_run_file(config["run_files"])
        run = read_run(run_file)
        token_budget = config["token_budget"]

        hit_sums = {k: 0 for k in KS}
        query_count = 0
        missing_image_count = 0

        print("")
        print("[Eval]", method)
        print("Run:", run_file if run_file else "MISSING")

        for item in subset:
            qid = item.get("query_id", "")
            gold_page_id = item.get("gold_page_id", "")
            region = region_map.get(qid, {})
            gold_bbox = region.get("bbox", None)

            ranked_pages = run.get(qid, [])
            page_rank_found = ""

            if gold_page_id in ranked_pages:
                page_rank_found = ranked_pages.index(gold_page_id) + 1

            page_hit_top10 = gold_page_id in ranked_pages[:10]

            image_path = find_image(gold_page_id)

            query_count += 1

            row = {
                "Method": method,
                "query_id": qid,
                "gold_page_id": gold_page_id,
                "page_rank_found": page_rank_found,
                "page_retrieved_top10": 1 if page_hit_top10 else 0,
                "region_id": region.get("region_id", ""),
                "gold_bbox": json.dumps(gold_bbox, ensure_ascii=False),
                "status": "PASSED",
                "run_file": str(run_file.relative_to(PROJECT_ROOT)) if run_file else "",
            }

            if image_path is None:
                missing_image_count += 1
                row["status"] = "missing_image"

                for k in KS:
                    row["Region Hit@{}".format(k)] = 0

                per_query_rows.append(row)
                continue

            boxes, scores, order, image_size = patch_saliency_scores(image_path)

            if boxes is None:
                missing_image_count += 1
                row["status"] = "image_read_failed"

                for k in KS:
                    row["Region Hit@{}".format(k)] = 0

                per_query_rows.append(row)
                continue

            if token_budget is not None:
                order = order[:token_budget]

            top_order = list(order[:max(KS)])

            patch_hits = []

            for rank, patch_idx in enumerate(top_order, start=1):
                patch_box = boxes[int(patch_idx)]
                cx = (patch_box[0] + patch_box[2]) / 2.0
                cy = (patch_box[1] + patch_box[3]) / 2.0

                center_hit = center_inside((cx, cy), gold_bbox)
                patch_iou = iou(patch_box, gold_bbox)
                iou_hit = patch_iou >= IOU_THRESHOLD
                region_hit = center_hit or iou_hit

                patch_hits.append(region_hit)

                patch_rows.append({
                    "Method": method,
                    "query_id": qid,
                    "gold_page_id": gold_page_id,
                    "region_id": region.get("region_id", ""),
                    "gold_bbox": json.dumps(gold_bbox, ensure_ascii=False),
                    "patch_rank": rank,
                    "patch_index": int(patch_idx),
                    "patch_score": "{:.8f}".format(float(scores[int(patch_idx)])),
                    "patch_bbox": json.dumps([round(v, 4) for v in patch_box]),
                    "patch_center_x": "{:.4f}".format(cx),
                    "patch_center_y": "{:.4f}".format(cy),
                    "center_hit": int(center_hit),
                    "iou": "{:.6f}".format(patch_iou),
                    "iou_hit": int(iou_hit),
                    "region_hit": int(region_hit),
                    "image_w": image_size[0],
                    "image_h": image_size[1],
                    "image_path": str(image_path.relative_to(PROJECT_ROOT)),
                })

            for k in KS:
                if not page_hit_top10:
                    value = 0
                else:
                    value = 1 if any(patch_hits[:k]) else 0

                hit_sums[k] += value
                row["Region Hit@{}".format(k)] = value

            per_query_rows.append(row)

        result = {
            "Method": method,
            "Region Hit@1": hit_sums[1] / query_count if query_count else 0.0,
            "Region Hit@3": hit_sums[3] / query_count if query_count else 0.0,
            "Region Hit@5": hit_sums[5] / query_count if query_count else 0.0,
            "Query Count": query_count,
            "Missing Image Count": missing_image_count,
            "IoU Threshold": IOU_THRESHOLD,
            "Patch Grid": "{}x{}".format(PATCH_GRID, PATCH_GRID),
            "Status": "PASSED" if missing_image_count == 0 else "PASSED_WITH_MISSING_IMAGES",
            "Run File": str(run_file.relative_to(PROJECT_ROOT)) if run_file else "",
        }

        results.append(result)

        print(
            "{},{:.4f},{:.4f},{:.4f},{}".format(
                method,
                result["Region Hit@1"],
                result["Region Hit@3"],
                result["Region Hit@5"],
                result["Status"],
            )
        )

    with OUTPUT_RESULTS_CSV.open("w", encoding="utf-8", newline="") as f:
        fieldnames = [
            "Method",
            "Region Hit@1",
            "Region Hit@3",
            "Region Hit@5",
            "Query Count",
            "Missing Image Count",
            "IoU Threshold",
            "Patch Grid",
            "Status",
            "Run File",
        ]

        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for row in results:
            out = dict(row)
            out["Region Hit@1"] = "{:.4f}".format(row["Region Hit@1"])
            out["Region Hit@3"] = "{:.4f}".format(row["Region Hit@3"])
            out["Region Hit@5"] = "{:.4f}".format(row["Region Hit@5"])
            writer.writerow(out)

    with OUTPUT_PER_QUERY_CSV.open("w", encoding="utf-8", newline="") as f:
        fieldnames = [
            "Method",
            "query_id",
            "gold_page_id",
            "page_rank_found",
            "page_retrieved_top10",
            "region_id",
            "gold_bbox",
            "Region Hit@1",
            "Region Hit@3",
            "Region Hit@5",
            "status",
            "run_file",
        ]

        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(per_query_rows)

    with OUTPUT_PATCH_CSV.open("w", encoding="utf-8", newline="") as f:
        fieldnames = [
            "Method",
            "query_id",
            "gold_page_id",
            "region_id",
            "gold_bbox",
            "patch_rank",
            "patch_index",
            "patch_score",
            "patch_bbox",
            "patch_center_x",
            "patch_center_y",
            "center_hit",
            "iou",
            "iou_hit",
            "region_hit",
            "image_w",
            "image_h",
            "image_path",
        ]

        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(patch_rows)

    lines = []
    lines.append("# Week 7 Day 5 Region Hit@k Results")
    lines.append("")
    lines.append("## Table 10: Region Hit@k 结果表")
    lines.append("")
    lines.append("| Method | Region Hit@1 | Region Hit@3 | Region Hit@5 | Status |")
    lines.append("|---|---:|---:|---:|---|")

    for row in results:
        lines.append(
            "| {} | {:.4f} | {:.4f} | {:.4f} | {} |".format(
                row["Method"],
                row["Region Hit@1"],
                row["Region Hit@3"],
                row["Region Hit@5"],
                row["Status"],
            )
        )

    lines.append("")
    lines.append("## Settings")
    lines.append("")
    lines.append("- Patch grid: 7x7")
    lines.append("- Patch ranking: automatic edge-density saliency")
    lines.append("- Center-inside-bbox: enabled")
    lines.append("- IoU threshold: 0.3")
    lines.append("- Region hit rule: center hit OR IoU hit")
    lines.append("- k values: 1, 3, 5")

    OUTPUT_RESULTS_MD.write_text("\n".join(lines), encoding="utf-8")

    with OUTPUT_JSON.open("w", encoding="utf-8") as f:
        json.dump(
            {
                "results": results,
                "ks": KS,
                "iou_threshold": IOU_THRESHOLD,
                "patch_grid": PATCH_GRID,
                "patch_ranking": "edge_density_saliency",
            },
            f,
            indent=2,
            ensure_ascii=False,
        )

    print("")
    print("Wrote:", OUTPUT_RESULTS_CSV)
    print("Wrote:", OUTPUT_RESULTS_MD)
    print("Wrote:", OUTPUT_PER_QUERY_CSV)
    print("Wrote:", OUTPUT_PATCH_CSV)
    print("Wrote:", OUTPUT_JSON)


if __name__ == "__main__":
    main()
