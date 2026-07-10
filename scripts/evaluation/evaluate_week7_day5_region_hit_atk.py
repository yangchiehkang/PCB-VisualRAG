from pathlib import Path
from collections import defaultdict
import csv
import json
import math
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
OUTPUT_SUMMARY_JSON = RESULT_DIR / "region_hit_atk_summary.json"

KS = [1, 3, 5]
IOU_THRESHOLD = 0.3

METHOD_CONFIGS = [
    {
        "method": "Full MV",
        "run_file": C2F_DIR / "bm25_fullmv_N50_run.tsv",
        "fallback_files": [
            C2F_DIR / "bm25_fullmv_N10_run.tsv",
            C2F_DIR / "bm25_fullmv_N20_run.tsv",
            C2F_DIR / "bm25_fullmv_N100_run.tsv",
            HYBRID_DIR / "hybrid_fullmv_N50_alpha0p0_run.tsv",
        ],
        "token_budget": None,
    },
    {
        "method": "Budgeted MV",
        "run_file": C2F_DIR / "bm25_budgetmv_N50_M24_none_run.tsv",
        "fallback_files": [
            C2F_DIR / "bm25_budgetmv_N20_M8_none_run.tsv",
            C2F_DIR / "bm25_budgetmv_N20_M16_none_run.tsv",
            HYBRID_DIR / "hybrid_budgetmv_N50_M24_alpha0p0_run.tsv",
        ],
        "token_budget": 24,
    },
    {
        "method": "BM25 + Budgeted MV",
        "run_file": C2F_DIR / "bm25_budgetmv_N20_M8_none_run.tsv",
        "fallback_files": [
            C2F_DIR / "bm25_budgetmv_N20_M16_none_run.tsv",
            C2F_DIR / "bm25_budgetmv_N50_M24_none_run.tsv",
        ],
        "token_budget": 24,
    },
    {
        "method": "Hybrid Fusion",
        "run_file": HYBRID_DIR / "hybrid_budgetmv_N50_M24_alpha0p8_run.tsv",
        "fallback_files": [
            HYBRID_DIR / "hybrid_budgetmv_N50_M24_alpha0p9_run.tsv",
            HYBRID_DIR / "hybrid_budgetmv_N50_M24_alpha1p0_run.tsv",
            HYBRID_DIR / "hybrid_fullmv_N50_alpha0p8_run.tsv",
            HYBRID_DIR / "hybrid_fullmv_N50_alpha1p0_run.tsv",
        ],
        "token_budget": 24,
    },
]


def ensure_dirs():
    RESULT_DIR.mkdir(parents=True, exist_ok=True)


def load_jsonl(path):
    rows = []

    if not path.exists():
        raise FileNotFoundError(path)

    with path.open("r", encoding="utf-8-sig") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()

            if not line:
                continue

            row = json.loads(line)
            row["_line_no"] = line_no
            rows.append(row)

    return rows


def validate_regions(regions):
    failed = []

    for row in regions:
        qid = row.get("query_id", "")
        bbox = row.get("bbox", None)
        bbox_status = row.get("bbox_status", "")

        if bbox_status != "done":
            failed.append((qid, "bbox_status_not_done"))

        if not isinstance(bbox, list) or len(bbox) != 4:
            failed.append((qid, "bbox_invalid_format"))
            continue

        try:
            x1, y1, x2, y2 = [float(v) for v in bbox]
        except Exception:
            failed.append((qid, "bbox_not_numeric"))
            continue

        if x2 <= x1 or y2 <= y1:
            failed.append((qid, "bbox_zero_or_negative_area"))

    return failed


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


def choose_run_file(config):
    if config["run_file"].exists():
        return config["run_file"]

    for path in config["fallback_files"]:
        if path.exists():
            return path

    return None


def decode_id_array(arr):
    ids = []

    for x in arr:
        if isinstance(x, bytes):
            ids.append(x.decode("utf-8"))
        else:
            ids.append(str(x))

    return ids


def try_load_npz(path):
    data = np.load(path, allow_pickle=True)
    keys = set(data.files)

    qids = None
    pids = None
    qemb = None
    pemb = None

    for key in ["query_ids", "qids", "queries"]:
        if key in keys:
            qids = decode_id_array(data[key])

    for key in ["page_ids", "doc_ids", "pids", "ids"]:
        if key in keys:
            pids = decode_id_array(data[key])

    for key in ["query_embeddings", "query_embs", "q_embeddings", "q_emb"]:
        if key in keys:
            qemb = data[key]

    for key in ["page_embeddings", "page_embs", "doc_embeddings", "p_embeddings", "embeddings"]:
        if key in keys:
            pemb = data[key]

    return qids, qemb, pids, pemb


def find_embedding_files():
    roots = [
        PROJECT_ROOT / "data",
        PROJECT_ROOT / "artifacts",
        PROJECT_ROOT / "results" / "week7",
    ]

    npz_files = []

    for root in roots:
        if not root.exists():
            continue

        for path in root.rglob("*.npz"):
            name = path.name.lower()
            if "emb" in name or "embedding" in name or "vector" in name:
                npz_files.append(path)

    return sorted(npz_files)


def load_embeddings_auto():
    query_embeddings = {}
    page_embeddings = {}
    used_files = []

    for path in find_embedding_files():
        try:
            qids, qemb, pids, pemb = try_load_npz(path)
        except Exception:
            continue

        if qids is not None and qemb is not None:
            for qid, emb in zip(qids, qemb):
                query_embeddings[qid] = np.asarray(emb, dtype=np.float32)
            used_files.append(str(path.relative_to(PROJECT_ROOT)))

        if pids is not None and pemb is not None:
            for pid, emb in zip(pids, pemb):
                page_embeddings[pid] = np.asarray(emb, dtype=np.float32)
            used_files.append(str(path.relative_to(PROJECT_ROOT)))

    return query_embeddings, page_embeddings, sorted(set(used_files))


def normalize_rows(x):
    x = np.asarray(x, dtype=np.float32)

    if x.ndim == 1:
        x = x.reshape(1, -1)

    norm = np.linalg.norm(x, axis=1, keepdims=True)
    norm = np.maximum(norm, 1e-8)

    return x / norm


def patch_grid_shape(token_count):
    side = int(round(math.sqrt(token_count)))

    if side * side == token_count:
        return side, side

    cols = int(math.ceil(math.sqrt(token_count)))
    rows = int(math.ceil(token_count / cols))

    return rows, cols


def patch_bbox_from_index(index, token_count, image_w, image_h):
    rows, cols = patch_grid_shape(token_count)

    r = index // cols
    c = index % cols

    x1 = image_w * c / cols
    y1 = image_h * r / rows
    x2 = image_w * (c + 1) / cols
    y2 = image_h * (r + 1) / rows

    return [x1, y1, x2, y2]


def patch_center(patch_bbox):
    x1, y1, x2, y2 = patch_bbox
    return [(x1 + x2) / 2.0, (y1 + y2) / 2.0]


def center_inside_bbox(center, bbox):
    x, y = center
    x1, y1, x2, y2 = [float(v) for v in bbox]

    return x1 <= x <= x2 and y1 <= y <= y2


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


def find_image_size(page_id):
    exts = [".png", ".jpg", ".jpeg"]

    roots = [
        PROJECT_ROOT / "data",
        PROJECT_ROOT / "artifacts",
        PROJECT_ROOT / "results",
    ]

    try:
        from PIL import Image
    except Exception:
        return 224, 224, ""

    for root in roots:
        if not root.exists():
            continue

        for ext in exts:
            matches = list(root.rglob("{}{}".format(page_id, ext)))
            if matches:
                path = matches[0]
                with Image.open(path) as img:
                    w, h = img.size
                return w, h, str(path.relative_to(PROJECT_ROOT))

    return 224, 224, ""


def score_patches(query_emb, page_emb):
    q = normalize_rows(query_emb)
    p = normalize_rows(page_emb)

    sim = np.matmul(p, q.T)

    patch_scores = sim.max(axis=1)

    order = np.argsort(-patch_scores)

    return order, patch_scores


def evaluate_region_for_query(qid, page_id, gold_bbox, query_embeddings, page_embeddings, token_budget):
    if qid not in query_embeddings:
        return None, "missing_query_embedding"

    if page_id not in page_embeddings:
        return None, "missing_page_embedding"

    query_emb = query_embeddings[qid]
    page_emb = page_embeddings[page_id]

    if page_emb.ndim == 1:
        return None, "page_embedding_not_multivector"

    token_count_total = page_emb.shape[0]

    if token_budget is not None:
        token_count_used = min(token_budget, token_count_total)
        page_emb_used = page_emb[:token_count_used]
    else:
        token_count_used = token_count_total
        page_emb_used = page_emb

    order, patch_scores = score_patches(query_emb, page_emb_used)

    image_w, image_h, image_path = find_image_size(page_id)

    patches = []

    for rank, patch_idx in enumerate(order[:max(KS)], start=1):
        patch_box = patch_bbox_from_index(int(patch_idx), token_count_total, image_w, image_h)
        center = patch_center(patch_box)
        center_hit = center_inside_bbox(center, gold_bbox)
        patch_iou = iou(patch_box, gold_bbox)
        iou_hit = patch_iou >= IOU_THRESHOLD

        patches.append({
            "rank": rank,
            "patch_index": int(patch_idx),
            "patch_score": float(patch_scores[patch_idx]),
            "patch_bbox": patch_box,
            "patch_center_x": center[0],
            "patch_center_y": center[1],
            "center_hit": center_hit,
            "iou": patch_iou,
            "iou_hit": iou_hit,
            "region_hit": center_hit or iou_hit,
            "image_w": image_w,
            "image_h": image_h,
            "image_path": image_path,
            "token_count_total": token_count_total,
            "token_count_used": token_count_used,
        })

    return patches, "ok"


def region_hit_at_k(patches, k):
    if patches is None:
        return 0

    for item in patches[:k]:
        if item["region_hit"]:
            return 1

    return 0


def main():
    ensure_dirs()

    subset = load_jsonl(SUBSET_PATH)
    regions = load_jsonl(REGIONS_PATH)

    region_failed = validate_regions(regions)

    if region_failed:
        print("[Week7-Day5] Region annotations are not ready.")
        for qid, reason in region_failed:
            print("FAILED,{},{},{}".format(qid, reason, REGIONS_PATH))
        print("Fix evidence_regions.jsonl first.")
        return

    region_map = {}
    for row in regions:
        qid = row.get("query_id", "")
        region_map[qid] = row

    query_embeddings, page_embeddings, used_embedding_files = load_embeddings_auto()

    print("[Week7-Day5] Starting Region Hit@k evaluation...")
    print("Evidence subset:", SUBSET_PATH)
    print("Evidence regions:", REGIONS_PATH)
    print("Query embeddings:", len(query_embeddings))
    print("Page embeddings:", len(page_embeddings))
    print("Embedding files:")
    for f in used_embedding_files:
        print("  " + f)

    results = []
    per_query_rows = []
    patch_rows = []

    for config in METHOD_CONFIGS:
        method = config["method"]
        run_file = choose_run_file(config)
        run = read_run(run_file) if run_file is not None else {}

        hit_sums = {k: 0 for k in KS}
        valid_count = 0
        missing_count = 0

        print("")
        print("[Week7-Day5] Evaluating:", method)
        print("Run file:", run_file if run_file is not None else "MISSING")

        for item in subset:
            qid = item.get("query_id", "")
            gold_page_id = item.get("gold_page_id", "")

            region = region_map.get(qid, {})
            gold_bbox = region.get("bbox", None)

            ranked_pages = run.get(qid, [])
            page_rank_found = ""

            if gold_page_id in ranked_pages:
                page_rank_found = ranked_pages.index(gold_page_id) + 1

            page_retrieved_top10 = gold_page_id in ranked_pages[:10]

            patches, status = evaluate_region_for_query(
                qid=qid,
                page_id=gold_page_id,
                gold_bbox=gold_bbox,
                query_embeddings=query_embeddings,
                page_embeddings=page_embeddings,
                token_budget=config["token_budget"],
            )

            if status != "ok":
                missing_count += 1

            valid_count += 1

            row = {
                "Method": method,
                "query_id": qid,
                "gold_page_id": gold_page_id,
                "page_rank_found": page_rank_found,
                "page_retrieved_top10": 1 if page_retrieved_top10 else 0,
                "region_id": region.get("region_id", ""),
                "gold_bbox": json.dumps(gold_bbox, ensure_ascii=False),
                "status": status,
                "run_file": str(run_file.relative_to(PROJECT_ROOT)) if run_file is not None else "",
            }

            for k in KS:
                if not page_retrieved_top10:
                    hit_value = 0
                else:
                    hit_value = region_hit_at_k(patches, k)

                hit_sums[k] += hit_value
                row["Region Hit@{}".format(k)] = hit_value

            per_query_rows.append(row)

            if patches is not None:
                for p in patches:
                    patch_rows.append({
                        "Method": method,
                        "query_id": qid,
                        "gold_page_id": gold_page_id,
                        "region_id": region.get("region_id", ""),
                        "gold_bbox": json.dumps(gold_bbox, ensure_ascii=False),
                        "patch_rank": p["rank"],
                        "patch_index": p["patch_index"],
                        "patch_score": "{:.8f}".format(p["patch_score"]),
                        "patch_bbox": json.dumps([round(v, 4) for v in p["patch_bbox"]]),
                        "patch_center_x": "{:.4f}".format(p["patch_center_x"]),
                        "patch_center_y": "{:.4f}".format(p["patch_center_y"]),
                        "center_hit": int(p["center_hit"]),
                        "iou": "{:.6f}".format(p["iou"]),
                        "iou_hit": int(p["iou_hit"]),
                        "region_hit": int(p["region_hit"]),
                        "image_w": p["image_w"],
                        "image_h": p["image_h"],
                        "image_path": p["image_path"],
                        "token_count_total": p["token_count_total"],
                        "token_count_used": p["token_count_used"],
                    })

        result = {
            "Method": method,
            "Region Hit@1": hit_sums[1] / valid_count if valid_count else 0.0,
            "Region Hit@3": hit_sums[3] / valid_count if valid_count else 0.0,
            "Region Hit@5": hit_sums[5] / valid_count if valid_count else 0.0,
            "Query Count": valid_count,
            "Missing Embedding Count": missing_count,
            "IoU Threshold": IOU_THRESHOLD,
            "Run File": str(run_file.relative_to(PROJECT_ROOT)) if run_file is not None else "",
            "Status": "PASSED" if missing_count == 0 else "PASSED_WITH_MISSING_EMBEDDINGS",
        }

        results.append(result)

        print(
            "Region Hit@1={:.4f}, Region Hit@3={:.4f}, Region Hit@5={:.4f}, missing_embeddings={}".format(
                result["Region Hit@1"],
                result["Region Hit@3"],
                result["Region Hit@5"],
                missing_count,
            )
        )

    with OUTPUT_RESULTS_CSV.open("w", encoding="utf-8", newline="") as f:
        fieldnames = [
            "Method",
            "Region Hit@1",
            "Region Hit@3",
            "Region Hit@5",
            "Query Count",
            "Missing Embedding Count",
            "IoU Threshold",
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
            "token_count_total",
            "token_count_used",
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
    lines.append("- Center-inside-bbox: enabled")
    lines.append("- IoU threshold: {}".format(IOU_THRESHOLD))
    lines.append("- Region hit rule: center hit OR IoU hit")
    lines.append("- k values: 1, 3, 5")

    OUTPUT_RESULTS_MD.write_text("\n".join(lines), encoding="utf-8")

    with OUTPUT_SUMMARY_JSON.open("w", encoding="utf-8") as f:
        json.dump(
            {
                "results": results,
                "embedding_files": used_embedding_files,
                "iou_threshold": IOU_THRESHOLD,
                "ks": KS,
            },
            f,
            indent=2,
            ensure_ascii=False,
        )

    print("")
    print("========== Region Hit@k Results ==========")
    print("Method,Region Hit@1,Region Hit@3,Region Hit@5,Status")

    for row in results:
        print(
            "{},{:.4f},{:.4f},{:.4f},{}".format(
                row["Method"],
                row["Region Hit@1"],
                row["Region Hit@3"],
                row["Region Hit@5"],
                row["Status"],
            )
        )

    print("")
    print("Wrote CSV:", OUTPUT_RESULTS_CSV)
    print("Wrote Markdown:", OUTPUT_RESULTS_MD)
    print("Wrote per-query CSV:", OUTPUT_PER_QUERY_CSV)
    print("Wrote patch CSV:", OUTPUT_PATCH_CSV)
    print("Wrote JSON:", OUTPUT_SUMMARY_JSON)


if __name__ == "__main__":
    main()
