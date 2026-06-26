from pathlib import Path
from collections import defaultdict
import csv
import json
import cv2
import numpy as np


PROJECT_ROOT = Path(r"E:\Working\PCB_VisualRAG_Project")

INPUT_CSV = PROJECT_ROOT / "results" / "week7" / "occlusion" / "occlusion_inputs.csv"
OUTPUT_DIR = PROJECT_ROOT / "results" / "week7" / "occlusion"

OUTPUT_PER_QUERY_CSV = OUTPUT_DIR / "occlusion_metrics_per_query.csv"
OUTPUT_SUMMARY_CSV = OUTPUT_DIR / "occlusion_metrics_summary.csv"
OUTPUT_MD = OUTPUT_DIR / "occlusion_metrics_results.md"
OUTPUT_JSON = OUTPUT_DIR / "occlusion_metrics_summary.json"

CONDITIONS = ["Original", "Gold Mask", "Random Mask"]


def read_csv(path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def parse_bbox(text):
    if not text:
        return None

    try:
        return json.loads(text)
    except Exception:
        return None


def clamp_bbox(bbox, w, h):
    x1, y1, x2, y2 = [int(round(v)) for v in bbox]

    x1 = max(0, min(w - 1, x1))
    y1 = max(0, min(h - 1, y1))
    x2 = max(x1 + 1, min(w, x2))
    y2 = max(y1 + 1, min(h, y2))

    return [x1, y1, x2, y2]


def evidence_score(image_path, bbox):
    img = cv2.imread(str(image_path))

    if img is None:
        return None

    h, w = img.shape[:2]

    bbox = clamp_bbox(bbox, w, h)

    x1, y1, x2, y2 = bbox

    crop = img[y1:y2, x1:x2]

    if crop.size == 0:
        return None

    if crop.shape[0] > 8 and crop.shape[1] > 8:
        crop = crop[4:-4, 4:-4]

    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)

    edges = cv2.Canny(gray, 50, 150)
    edge_density = float((edges > 0).mean())

    ink_density = float((gray < 245).mean())

    score = 0.7 * edge_density + 0.3 * ink_density

    return {
        "score": score,
        "edge_density": edge_density,
        "ink_density": ink_density,
    }


def safe_float(v):
    try:
        return float(v)
    except Exception:
        return 0.0


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    rows = read_csv(INPUT_CSV)

    grouped = defaultdict(dict)

    for row in rows:
        qid = row["query_id"]
        condition = row["condition"]
        grouped[qid][condition] = row

    per_query_rows = []

    print("[Week7-Day5] Evaluating Counterfactual Occlusion metrics")
    print("Input:", INPUT_CSV)

    for qid, condition_map in grouped.items():
        missing_conditions = [c for c in CONDITIONS if c not in condition_map]

        if missing_conditions:
            per_query_rows.append({
                "query_id": qid,
                "page_id": "",
                "region_id": "",
                "score_original": "",
                "score_gold_mask": "",
                "score_random_mask": "",
                "COG_score": "",
                "nDCG_original": "",
                "nDCG_gold_mask": "",
                "nDCG_random_mask": "",
                "COG_nDCG": "",
                "delta_original_gold": "",
                "delta_original_random": "",
                "random_iou_with_gold": "",
                "status": "MISSING_CONDITION",
            })
            continue

        original = condition_map["Original"]
        gold = condition_map["Gold Mask"]
        random_mask = condition_map["Random Mask"]

        page_id = original["page_id"]
        region_id = original["region_id"]

        gold_bbox = parse_bbox(original["gold_bbox"])

        original_image = PROJECT_ROOT / original["image_path"]
        gold_image = PROJECT_ROOT / gold["image_path"]
        random_image = PROJECT_ROOT / random_mask["image_path"]

        original_score_obj = evidence_score(original_image, gold_bbox)
        gold_score_obj = evidence_score(gold_image, gold_bbox)
        random_score_obj = evidence_score(random_image, gold_bbox)

        if original_score_obj is None or gold_score_obj is None or random_score_obj is None:
            per_query_rows.append({
                "query_id": qid,
                "page_id": page_id,
                "region_id": region_id,
                "score_original": "",
                "score_gold_mask": "",
                "score_random_mask": "",
                "COG_score": "",
                "nDCG_original": "",
                "nDCG_gold_mask": "",
                "nDCG_random_mask": "",
                "COG_nDCG": "",
                "delta_original_gold": "",
                "delta_original_random": "",
                "random_iou_with_gold": random_mask.get("random_iou_with_gold", ""),
                "status": "IMAGE_OR_SCORE_FAILED",
            })
            continue

        score_original = original_score_obj["score"]
        score_gold = gold_score_obj["score"]
        score_random = random_score_obj["score"]

        denom = max(score_original, score_gold, score_random, 1e-12)

        ndcg_original = score_original / denom
        ndcg_gold = score_gold / denom
        ndcg_random = score_random / denom

        cog_score = score_random - score_gold
        cog_ndcg = ndcg_random - ndcg_gold

        delta_original_gold = score_original - score_gold
        delta_original_random = score_original - score_random

        status = "PASSED" if cog_score > 0 else "CHECK"

        per_query_rows.append({
            "query_id": qid,
            "page_id": page_id,
            "region_id": region_id,
            "score_original": "{:.8f}".format(score_original),
            "score_gold_mask": "{:.8f}".format(score_gold),
            "score_random_mask": "{:.8f}".format(score_random),
            "COG_score": "{:.8f}".format(cog_score),
            "nDCG_original": "{:.8f}".format(ndcg_original),
            "nDCG_gold_mask": "{:.8f}".format(ndcg_gold),
            "nDCG_random_mask": "{:.8f}".format(ndcg_random),
            "COG_nDCG": "{:.8f}".format(cog_ndcg),
            "delta_original_gold": "{:.8f}".format(delta_original_gold),
            "delta_original_random": "{:.8f}".format(delta_original_random),
            "random_iou_with_gold": random_mask.get("random_iou_with_gold", ""),
            "status": status,
        })

        print(
            "DONE,{},{},COG_score={:.8f},COG_nDCG={:.8f},status={}".format(
                qid,
                page_id,
                cog_score,
                cog_ndcg,
                status,
            )
        )

    valid_rows = [r for r in per_query_rows if r["status"] in ["PASSED", "CHECK"]]

    def mean_of(key):
        vals = [safe_float(r[key]) for r in valid_rows if r[key] != ""]
        return sum(vals) / len(vals) if vals else 0.0

    query_count = len(per_query_rows)
    valid_count = len(valid_rows)
    passed_count = sum(1 for r in valid_rows if r["status"] == "PASSED")
    check_count = sum(1 for r in valid_rows if r["status"] == "CHECK")

    summary = {
        "Query Count": query_count,
        "Valid Query Count": valid_count,
        "COG Positive Count": passed_count,
        "COG Check Count": check_count,
        "COG Positive Rate": passed_count / valid_count if valid_count else 0.0,
        "Mean Score Original": mean_of("score_original"),
        "Mean Score Gold Mask": mean_of("score_gold_mask"),
        "Mean Score Random Mask": mean_of("score_random_mask"),
        "Mean COG_score": mean_of("COG_score"),
        "Mean nDCG Original": mean_of("nDCG_original"),
        "Mean nDCG Gold Mask": mean_of("nDCG_gold_mask"),
        "Mean nDCG Random Mask": mean_of("nDCG_random_mask"),
        "Mean COG_nDCG": mean_of("COG_nDCG"),
        "Status": "PASSED" if passed_count > 0 and valid_count == query_count else "CHECK",
    }

    with OUTPUT_PER_QUERY_CSV.open("w", encoding="utf-8", newline="") as f:
        fieldnames = [
            "query_id",
            "page_id",
            "region_id",
            "score_original",
            "score_gold_mask",
            "score_random_mask",
            "COG_score",
            "nDCG_original",
            "nDCG_gold_mask",
            "nDCG_random_mask",
            "COG_nDCG",
            "delta_original_gold",
            "delta_original_random",
            "random_iou_with_gold",
            "status",
        ]

        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(per_query_rows)

    with OUTPUT_SUMMARY_CSV.open("w", encoding="utf-8", newline="") as f:
        fieldnames = list(summary.keys())
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        out = dict(summary)

        for key, value in out.items():
            if isinstance(value, float):
                out[key] = "{:.8f}".format(value)

        writer.writerow(out)

    lines = []
    lines.append("# Week 7 Day 5 Counterfactual Occlusion Metrics")
    lines.append("")
    lines.append("## Table 12: Occlusion 指标结果")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|---|---:|")
    lines.append("| Query Count | {} |".format(summary["Query Count"]))
    lines.append("| Valid Query Count | {} |".format(summary["Valid Query Count"]))
    lines.append("| COG Positive Count | {} |".format(summary["COG Positive Count"]))
    lines.append("| COG Positive Rate | {:.4f} |".format(summary["COG Positive Rate"]))
    lines.append("| Mean Score Original | {:.8f} |".format(summary["Mean Score Original"]))
    lines.append("| Mean Score Gold Mask | {:.8f} |".format(summary["Mean Score Gold Mask"]))
    lines.append("| Mean Score Random Mask | {:.8f} |".format(summary["Mean Score Random Mask"]))
    lines.append("| Mean COG_score | {:.8f} |".format(summary["Mean COG_score"]))
    lines.append("| Mean nDCG Original | {:.8f} |".format(summary["Mean nDCG Original"]))
    lines.append("| Mean nDCG Gold Mask | {:.8f} |".format(summary["Mean nDCG Gold Mask"]))
    lines.append("| Mean nDCG Random Mask | {:.8f} |".format(summary["Mean nDCG Random Mask"]))
    lines.append("| Mean COG_nDCG | {:.8f} |".format(summary["Mean COG_nDCG"]))
    lines.append("| Status | {} |".format(summary["Status"]))
    lines.append("")
    lines.append("## Definition")
    lines.append("")
    lines.append("```text")
    lines.append("COG_score = Score(Random Mask) - Score(Gold Mask)")
    lines.append("COG_nDCG  = nDCG(Random Mask) - nDCG(Gold Mask)")
    lines.append("```")
    lines.append("")
    lines.append("## Per-query Results")
    lines.append("")
    lines.append("| Query ID | Score Original | Score Gold Mask | Score Random Mask | COG_score | COG_nDCG | Status |")
    lines.append("|---|---:|---:|---:|---:|---:|---|")

    for row in per_query_rows:
        lines.append(
            "| {} | {} | {} | {} | {} | {} | {} |".format(
                row["query_id"],
                row["score_original"],
                row["score_gold_mask"],
                row["score_random_mask"],
                row["COG_score"],
                row["COG_nDCG"],
                row["status"],
            )
        )

    OUTPUT_MD.write_text("\n".join(lines), encoding="utf-8")

    with OUTPUT_JSON.open("w", encoding="utf-8") as f:
        json.dump(
            {
                "summary": summary,
                "per_query": per_query_rows,
            },
            f,
            indent=2,
            ensure_ascii=False,
        )

    print("")
    print("[Week7-Day5] Occlusion metrics completed.")
    print("Query count:", query_count)
    print("Valid query count:", valid_count)
    print("COG positive count:", passed_count)
    print("COG positive rate: {:.4f}".format(summary["COG Positive Rate"]))
    print("Mean COG_score: {:.8f}".format(summary["Mean COG_score"]))
    print("Mean COG_nDCG: {:.8f}".format(summary["Mean COG_nDCG"]))
    print("Status:", summary["Status"])
    print("Wrote:", OUTPUT_PER_QUERY_CSV)
    print("Wrote:", OUTPUT_SUMMARY_CSV)
    print("Wrote:", OUTPUT_MD)
    print("Wrote:", OUTPUT_JSON)


if __name__ == "__main__":
    main()
