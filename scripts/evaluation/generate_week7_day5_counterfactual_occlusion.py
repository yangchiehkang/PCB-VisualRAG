from pathlib import Path
import json
import csv
import cv2
import random
import shutil


PROJECT_ROOT = Path(r"E:\Working\PCB_VisualRAG_Project")

REGIONS_PATH = PROJECT_ROOT / "data" / "annotations" / "evidence_regions.jsonl"

OUTPUT_IMAGE_DIR = PROJECT_ROOT / "artifacts" / "occlusion_pages"
OUTPUT_RESULT_DIR = PROJECT_ROOT / "results" / "week7" / "occlusion"

OUTPUT_JSONL = OUTPUT_RESULT_DIR / "occlusion_inputs.jsonl"
OUTPUT_CSV = OUTPUT_RESULT_DIR / "occlusion_inputs.csv"
OUTPUT_MD = OUTPUT_RESULT_DIR / "occlusion_inputs.md"

IMAGE_ROOTS = [
    PROJECT_ROOT / "data",
    PROJECT_ROOT / "artifacts",
    PROJECT_ROOT / "results",
]

IMAGE_EXTS = [".png", ".jpg", ".jpeg"]

MASK_COLOR = (255, 255, 255)
MAX_RANDOM_IOU = 0.01
RANDOM_SEED = 42


def load_jsonl(path):
    rows = []

    with path.open("r", encoding="utf-8-sig") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))

    return rows


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


def clamp_bbox(bbox, w, h):
    x1, y1, x2, y2 = [int(round(v)) for v in bbox]

    x1 = max(0, min(w - 1, x1))
    y1 = max(0, min(h - 1, y1))
    x2 = max(x1 + 1, min(w, x2))
    y2 = max(y1 + 1, min(h, y2))

    return [x1, y1, x2, y2]


def area(b):
    return max(0, b[2] - b[0]) * max(0, b[3] - b[1])


def iou(a, b):
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b

    ix1 = max(ax1, bx1)
    iy1 = max(ay1, by1)
    ix2 = min(ax2, bx2)
    iy2 = min(ay2, by2)

    iw = max(0, ix2 - ix1)
    ih = max(0, iy2 - iy1)

    inter = iw * ih
    union = area(a) + area(b) - inter

    if union <= 0:
        return 0.0

    return inter / union


def make_random_bbox_same_area(gold_bbox, w, h):
    gx1, gy1, gx2, gy2 = gold_bbox
    bw = gx2 - gx1
    bh = gy2 - gy1

    max_x = max(0, w - bw)
    max_y = max(0, h - bh)

    best_bbox = None
    best_iou = 1.0

    for _ in range(5000):
        x1 = random.randint(0, max_x)
        y1 = random.randint(0, max_y)
        candidate = [x1, y1, x1 + bw, y1 + bh]

        candidate_iou = iou(candidate, gold_bbox)

        if candidate_iou < best_iou:
            best_iou = candidate_iou
            best_bbox = candidate

        if candidate_iou <= MAX_RANDOM_IOU:
            return candidate, candidate_iou

    return best_bbox, best_iou


def apply_mask(img, bbox):
    out = img.copy()
    x1, y1, x2, y2 = bbox
    out[y1:y2, x1:x2] = MASK_COLOR
    return out


def save_image(path, img):
    path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(path), img)


def main():
    random.seed(RANDOM_SEED)

    OUTPUT_IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_RESULT_DIR.mkdir(parents=True, exist_ok=True)

    regions = load_jsonl(REGIONS_PATH)

    output_rows = []

    print("[Week7-Day5] Generating Counterfactual Occlusion inputs")
    print("Regions:", REGIONS_PATH)
    print("Output image dir:", OUTPUT_IMAGE_DIR)
    print("Output result dir:", OUTPUT_RESULT_DIR)

    for row in regions:
        qid = row.get("query_id", "")
        page_id = row.get("page_id", "")
        region_id = row.get("region_id", "r1")
        bbox = row.get("bbox", None)

        image_path = find_image(page_id)

        if image_path is None:
            print("FAILED,image_not_found,{},{}".format(qid, page_id))
            continue

        img = cv2.imread(str(image_path))

        if img is None:
            print("FAILED,image_read_failed,{},{}".format(qid, page_id))
            continue

        h, w = img.shape[:2]

        gold_bbox = clamp_bbox(bbox, w, h)
        random_bbox, random_iou = make_random_bbox_same_area(gold_bbox, w, h)

        original_out = OUTPUT_IMAGE_DIR / "{}_{}_original.png".format(qid, page_id)
        gold_out = OUTPUT_IMAGE_DIR / "{}_{}_gold_mask.png".format(qid, page_id)
        random_out = OUTPUT_IMAGE_DIR / "{}_{}_random_mask.png".format(qid, page_id)

        shutil.copyfile(image_path, original_out)

        gold_img = apply_mask(img, gold_bbox)
        random_img = apply_mask(img, random_bbox)

        save_image(gold_out, gold_img)
        save_image(random_out, random_img)

        rows = [
            {
                "query_id": qid,
                "page_id": page_id,
                "region_id": region_id,
                "condition": "Original",
                "image_path": str(original_out.relative_to(PROJECT_ROOT)),
                "source_image_path": str(image_path.relative_to(PROJECT_ROOT)),
                "gold_bbox": json.dumps(gold_bbox),
                "mask_bbox": "",
                "mask_area": 0,
                "random_iou_with_gold": "",
                "image_w": w,
                "image_h": h,
                "mask_color": str(MASK_COLOR),
                "status": "PASSED",
            },
            {
                "query_id": qid,
                "page_id": page_id,
                "region_id": region_id,
                "condition": "Gold Mask",
                "image_path": str(gold_out.relative_to(PROJECT_ROOT)),
                "source_image_path": str(image_path.relative_to(PROJECT_ROOT)),
                "gold_bbox": json.dumps(gold_bbox),
                "mask_bbox": json.dumps(gold_bbox),
                "mask_area": area(gold_bbox),
                "random_iou_with_gold": "",
                "image_w": w,
                "image_h": h,
                "mask_color": str(MASK_COLOR),
                "status": "PASSED",
            },
            {
                "query_id": qid,
                "page_id": page_id,
                "region_id": region_id,
                "condition": "Random Mask",
                "image_path": str(random_out.relative_to(PROJECT_ROOT)),
                "source_image_path": str(image_path.relative_to(PROJECT_ROOT)),
                "gold_bbox": json.dumps(gold_bbox),
                "mask_bbox": json.dumps(random_bbox),
                "mask_area": area(random_bbox),
                "random_iou_with_gold": "{:.6f}".format(random_iou),
                "image_w": w,
                "image_h": h,
                "mask_color": str(MASK_COLOR),
                "status": "PASSED",
            },
        ]

        output_rows.extend(rows)

        print(
            "DONE,{},{},gold_bbox={},random_bbox={},random_iou={:.6f}".format(
                qid,
                page_id,
                gold_bbox,
                random_bbox,
                random_iou,
            )
        )

    with OUTPUT_JSONL.open("w", encoding="utf-8") as f:
        for row in output_rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    fieldnames = [
        "query_id",
        "page_id",
        "region_id",
        "condition",
        "image_path",
        "source_image_path",
        "gold_bbox",
        "mask_bbox",
        "mask_area",
        "random_iou_with_gold",
        "image_w",
        "image_h",
        "mask_color",
        "status",
    ]

    with OUTPUT_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(output_rows)

    lines = []
    lines.append("# Week 7 Day 5 Counterfactual Occlusion Inputs")
    lines.append("")
    lines.append("## Table 11: Occlusion 输入条件")
    lines.append("")
    lines.append("| Condition | 说明 |")
    lines.append("|---|---|")
    lines.append("| Original | 原始页面 |")
    lines.append("| Gold Mask | 遮挡 gold evidence bbox |")
    lines.append("| Random Mask | 遮挡同面积随机区域 |")
    lines.append("")
    lines.append("## Generated Inputs")
    lines.append("")
    lines.append("| Query ID | Page ID | Condition | Image Path | Status |")
    lines.append("|---|---|---|---|---|")

    for row in output_rows:
        lines.append(
            "| {} | {} | {} | {} | {} |".format(
                row["query_id"],
                row["page_id"],
                row["condition"],
                row["image_path"],
                row["status"],
            )
        )

    OUTPUT_MD.write_text("\n".join(lines), encoding="utf-8")

    print("")
    print("Wrote:", OUTPUT_JSONL)
    print("Wrote:", OUTPUT_CSV)
    print("Wrote:", OUTPUT_MD)
    print("Generated image count:", len(output_rows))


if __name__ == "__main__":
    main()
