from pathlib import Path
import json
import cv2
import numpy as np


PROJECT_ROOT = Path(r"E:\Working\PCB_VisualRAG_Project")

REGIONS_PATH = PROJECT_ROOT / "data" / "annotations" / "evidence_regions.jsonl"
BACKUP_PATH = PROJECT_ROOT / "data" / "annotations" / "evidence_regions.before_auto_bbox.jsonl"
SCREENSHOT_DIR = PROJECT_ROOT / "artifacts" / "evidence_annotation_screenshots"

IMAGE_ROOTS = [
    PROJECT_ROOT / "data",
    PROJECT_ROOT / "artifacts",
    PROJECT_ROOT / "results",
]

IMAGE_EXTS = [".png", ".jpg", ".jpeg"]

MAX_BBOX_AREA = 2200000
MIN_BBOX_W = 180
MIN_BBOX_H = 180


def load_jsonl(path):
    rows = []

    with path.open("r", encoding="utf-8-sig") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))

    return rows


def write_jsonl(path, rows):
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


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


def region_sum(integral, x1, y1, x2, y2):
    return (
        integral[y2, x2]
        - integral[y1, x2]
        - integral[y2, x1]
        + integral[y1, x1]
    )


def auto_bbox(image_path):
    img = cv2.imread(str(image_path))

    if img is None:
        raise RuntimeError("Cannot read image: {}".format(image_path))

    h, w = img.shape[:2]

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (5, 5), 0)

    edges = cv2.Canny(gray, 50, 150)
    edges = (edges > 0).astype(np.float32)

    margin_x = int(w * 0.03)
    margin_y = int(h * 0.03)

    edges[:margin_y, :] = 0
    edges[h - margin_y:, :] = 0
    edges[:, :margin_x] = 0
    edges[:, w - margin_x:] = 0

    integral = cv2.integral(edges)

    candidate_sizes = [
        (int(w * 0.22), int(h * 0.18)),
        (int(w * 0.28), int(h * 0.22)),
        (int(w * 0.34), int(h * 0.26)),
        (int(w * 0.40), int(h * 0.30)),
    ]

    best = None
    best_score = -1.0

    for bw, bh in candidate_sizes:
        bw = max(MIN_BBOX_W, bw)
        bh = max(MIN_BBOX_H, bh)

        if bw * bh > MAX_BBOX_AREA:
            scale = (MAX_BBOX_AREA / float(bw * bh)) ** 0.5
            bw = int(bw * scale)
            bh = int(bh * scale)

        bw = min(bw, w - 2)
        bh = min(bh, h - 2)

        step_x = max(20, bw // 5)
        step_y = max(20, bh // 5)

        for y1 in range(margin_y, max(margin_y + 1, h - bh - margin_y), step_y):
            for x1 in range(margin_x, max(margin_x + 1, w - bw - margin_x), step_x):
                x2 = x1 + bw
                y2 = y1 + bh

                edge_count = region_sum(integral, x1, y1, x2, y2)
                area = bw * bh
                density = edge_count / max(area, 1)

                cx = (x1 + x2) / 2.0
                cy = (y1 + y2) / 2.0

                center_penalty = 0.15 * (
                    abs(cx - w / 2.0) / max(w / 2.0, 1)
                    + abs(cy - h / 2.0) / max(h / 2.0, 1)
                )

                score = density - center_penalty

                if score > best_score:
                    best_score = score
                    best = [int(x1), int(y1), int(x2), int(y2)]

    if best is None:
        bw = min(600, int(w * 0.35))
        bh = min(600, int(h * 0.35))
        x1 = max(0, int((w - bw) / 2))
        y1 = max(0, int((h - bh) / 2))
        best = [x1, y1, x1 + bw, y1 + bh]

    return best


def save_screenshot(image_path, qid, region_id, bbox):
    img = cv2.imread(str(image_path))

    if img is None:
        return None

    x1, y1, x2, y2 = [int(v) for v in bbox]

    out = img.copy()
    cv2.rectangle(out, (x1, y1), (x2, y2), (0, 0, 255), 3)

    label = "{}_{}".format(qid, region_id)

    cv2.putText(
        out,
        label,
        (max(0, x1), max(30, y1 - 10)),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.0,
        (0, 0, 255),
        2,
        cv2.LINE_AA,
    )

    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

    out_path = SCREENSHOT_DIR / "{}_{}_bbox_check.png".format(qid, region_id)
    cv2.imwrite(str(out_path), out)

    return out_path


def main():
    if not BACKUP_PATH.exists():
        BACKUP_PATH.write_text(REGIONS_PATH.read_text(encoding="utf-8-sig"), encoding="utf-8")

    rows = load_jsonl(REGIONS_PATH)
    updated = []

    print("[Week7] Auto evidence bbox generation")
    print("Input:", REGIONS_PATH)
    print("Backup:", BACKUP_PATH)

    for row in rows:
        qid = row.get("query_id", "")
        page_id = row.get("page_id", "")
        region_id = row.get("region_id", "r1")

        image_path = find_image(page_id)

        if image_path is None:
            print("FAILED,image_not_found,{},{}".format(qid, page_id))
            updated.append(row)
            continue

        bbox = auto_bbox(image_path)

        row["bbox"] = bbox
        row["bbox_status"] = "done"
        row["evidence_note"] = "auto-generated evidence region by edge-density saliency"

        screenshot_path = save_screenshot(image_path, qid, region_id, bbox)

        print("DONE,{},{},{},{}".format(qid, page_id, bbox, screenshot_path))

        updated.append(row)

    write_jsonl(REGIONS_PATH, updated)

    print("[Week7] Updated:", REGIONS_PATH)


if __name__ == "__main__":
    main()
