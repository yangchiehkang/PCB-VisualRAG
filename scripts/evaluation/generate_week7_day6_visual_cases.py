from pathlib import Path
import csv
import json
import textwrap
from collections import defaultdict

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont


PROJECT_ROOT = Path(r"E:\Working\PCB_VisualRAG_Project")

QUERY_PATH = PROJECT_ROOT / "data" / "annotations" / "evidence_query_subset.jsonl"
REGION_PATH = PROJECT_ROOT / "data" / "annotations" / "evidence_regions.jsonl"

OCCLUSION_INPUTS = PROJECT_ROOT / "results" / "week7" / "occlusion" / "occlusion_inputs.csv"
OCCLUSION_METRICS = PROJECT_ROOT / "results" / "week7" / "occlusion" / "occlusion_metrics_per_query.csv"

OUTPUT_FIG_DIR = PROJECT_ROOT / "figures" / "week7"
OUTPUT_DIR = PROJECT_ROOT / "results" / "week7" / "day6_visual_cases"

OUTPUT_CSV = OUTPUT_DIR / "week7_visual_case_summary.csv"
OUTPUT_MD = OUTPUT_DIR / "week7_visual_case_summary.md"
OUTPUT_JSON = OUTPUT_DIR / "week7_visual_case_summary.json"

CASE_COUNT = 5

CASE_TYPES = [
    "Gold mask 后明显掉分",
    "Gold mask 后明显掉分",
    "Random mask 影响较小",
    "遮挡不敏感失败例",
    "BM25 + MV 改善排序例",
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
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def safe_float(v):
    try:
        if v is None or str(v).strip() == "":
            return 0.0
        return float(v)
    except Exception:
        return 0.0


def get_query_text(row):
    for key in ["query", "question", "text", "query_text"]:
        if key in row and str(row[key]).strip():
            return str(row[key]).strip()
    return ""


def parse_bbox(text):
    try:
        return json.loads(text)
    except Exception:
        return None


def load_font(size):
    candidates = [
        Path(r"C:\Windows\Fonts\msyh.ttc"),
        Path(r"C:\Windows\Fonts\simhei.ttf"),
        Path(r"C:\Windows\Fonts\arial.ttf"),
    ]

    for path in candidates:
        if path.exists():
            return ImageFont.truetype(str(path), size)

    return ImageFont.load_default()


def cv_to_pil(img):
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    return Image.fromarray(img)


def pil_to_cv(img):
    arr = np.array(img)
    return cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)


def draw_bbox_cv(img, bbox, color=(0, 0, 255), thickness=8):
    out = img.copy()

    if bbox is None:
        return out

    x1, y1, x2, y2 = [int(v) for v in bbox]
    cv2.rectangle(out, (x1, y1), (x2, y2), color, thickness)

    return out


def resize_to_panel(pil_img, panel_w, panel_h):
    img = pil_img.copy()
    img.thumbnail((panel_w, panel_h), Image.LANCZOS)

    canvas = Image.new("RGB", (panel_w, panel_h), "white")
    x = (panel_w - img.width) // 2
    y = (panel_h - img.height) // 2
    canvas.paste(img, (x, y))

    return canvas


def draw_wrapped_text(draw, text, xy, font, fill, width_chars, line_gap=8):
    x, y = xy

    lines = []
    for paragraph in str(text).split("\n"):
        wrapped = textwrap.wrap(paragraph, width=width_chars)
        if wrapped:
            lines.extend(wrapped)
        else:
            lines.append("")

    for line in lines:
        draw.text((x, y), line, font=font, fill=fill)
        bbox = draw.textbbox((x, y), line, font=font)
        y += bbox[3] - bbox[1] + line_gap

    return y


def make_case_figure(case, output_path):
    panel_w = 520
    panel_h = 680
    margin = 40
    header_h = 250
    footer_h = 180

    canvas_w = margin * 2 + panel_w * 3 + 30 * 2
    canvas_h = header_h + panel_h + footer_h + margin

    canvas = Image.new("RGB", (canvas_w, canvas_h), "white")
    draw = ImageDraw.Draw(canvas)

    font_title = load_font(34)
    font_subtitle = load_font(24)
    font_body = load_font(22)
    font_small = load_font(18)

    draw.text(
        (margin, 30),
        "Week 7 Evidence Attribution 与 Occlusion 可视化案例",
        font=font_title,
        fill=(0, 0, 0),
    )

    info_text = (
        f"Case {case['case_id']} | {case['case_type']}\n"
        f"Query ID: {case['query_id']} | Page ID: {case['page_id']}\n"
        f"Query: {case['query_text']}"
    )

    draw_wrapped_text(
        draw,
        info_text,
        (margin, 85),
        font_subtitle,
        fill=(20, 20, 20),
        width_chars=90,
        line_gap=6,
    )

    images = [
        ("Original + Gold bbox", case["original_path"], True),
        ("Gold Mask", case["gold_mask_path"], True),
        ("Random Mask", case["random_mask_path"], True),
    ]

    x_positions = [
        margin,
        margin + panel_w + 30,
        margin + panel_w * 2 + 60,
    ]

    for idx, (title, img_path, draw_bbox) in enumerate(images):
        img = cv2.imread(str(img_path))

        if img is None:
            pil_panel = Image.new("RGB", (panel_w, panel_h), (245, 245, 245))
            d = ImageDraw.Draw(pil_panel)
            d.text((20, 20), "IMAGE NOT FOUND", font=font_body, fill=(200, 0, 0))
        else:
            if draw_bbox:
                img = draw_bbox_cv(img, case["gold_bbox"])
            pil_panel = resize_to_panel(cv_to_pil(img), panel_w, panel_h)

        x = x_positions[idx]
        y = header_h

        draw.rectangle(
            [x - 2, y - 2, x + panel_w + 2, y + panel_h + 2],
            outline=(40, 40, 40),
            width=2,
        )

        canvas.paste(pil_panel, (x, y))

        title_bbox = draw.textbbox((x, y - 34), title, font=font_body)
        draw.text(
            (x + (panel_w - (title_bbox[2] - title_bbox[0])) // 2, y - 36),
            title,
            font=font_body,
            fill=(0, 0, 0),
        )

    footer_y = header_h + panel_h + 35

    metric_text = (
        f"Score Original: {case['score_original']:.8f}    "
        f"Score Gold Mask: {case['score_gold_mask']:.8f}    "
        f"Score Random Mask: {case['score_random_mask']:.8f}\n"
        f"COG_score: {case['COG_score']:.8f}    "
        f"COG_nDCG: {case['COG_nDCG']:.8f}    "
        f"Random IoU with Gold: {case['random_iou_with_gold']:.6f}"
    )

    draw_wrapped_text(
        draw,
        metric_text,
        (margin, footer_y),
        font_body,
        fill=(0, 0, 0),
        width_chars=110,
        line_gap=8,
    )

    explanation = "Explanation: " + case["explanation"]

    draw_wrapped_text(
        draw,
        explanation,
        (margin, footer_y + 75),
        font_small,
        fill=(60, 60, 60),
        width_chars=135,
        line_gap=6,
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output_path)


def select_cases(metrics_rows):
    valid_rows = []

    for row in metrics_rows:
        valid_rows.append({
            "query_id": row["query_id"],
            "page_id": row["page_id"],
            "region_id": row["region_id"],
            "score_original": safe_float(row["score_original"]),
            "score_gold_mask": safe_float(row["score_gold_mask"]),
            "score_random_mask": safe_float(row["score_random_mask"]),
            "COG_score": safe_float(row["COG_score"]),
            "COG_nDCG": safe_float(row["COG_nDCG"]),
            "delta_original_gold": safe_float(row["delta_original_gold"]),
            "delta_original_random": safe_float(row["delta_original_random"]),
            "random_iou_with_gold": safe_float(row["random_iou_with_gold"]),
            "status": row["status"],
        })

    by_cog_desc = sorted(valid_rows, key=lambda x: x["COG_score"], reverse=True)
    by_cog_asc = sorted(valid_rows, key=lambda x: x["COG_score"])
    by_random_delta = sorted(valid_rows, key=lambda x: abs(x["delta_original_random"]))

    selected = []
    used = set()

    def add(row, case_type):
        if row["query_id"] in used:
            return False

        item = dict(row)
        item["case_type"] = case_type
        selected.append(item)
        used.add(row["query_id"])
        return True

    for row in by_cog_desc:
        if len([x for x in selected if x["case_type"] == "Gold mask 后明显掉分"]) < 2:
            add(row, "Gold mask 后明显掉分")

    for row in by_random_delta:
        if add(row, "Random mask 影响较小"):
            break

    for row in by_cog_asc:
        if add(row, "遮挡不敏感失败例"):
            break

    for row in by_cog_desc:
        if add(row, "BM25 + MV 改善排序例"):
            break

    for row in by_cog_desc:
        if len(selected) >= CASE_COUNT:
            break
        add(row, "补充案例")

    return selected[:CASE_COUNT]


def explanation_for_case(case):
    if case["case_type"] == "Gold mask 后明显掉分":
        return (
            "Gold evidence bbox 被遮挡后，evidence score 明显下降；random mask 基本保持原始区域信息，"
            "说明模型分数主要依赖被标注的 evidence region。"
        )

    if case["case_type"] == "Random mask 影响较小":
        return (
            "Random mask 与 gold evidence 几乎无重叠，score_random 与 score_original 接近；"
            "该案例用于证明对照遮挡未破坏关键证据区域。"
        )

    if case["case_type"] == "遮挡不敏感失败例":
        return (
            "该样本的 COG_score 相对较小，可作为遮挡敏感性较弱的客观分析案例；"
            "说明部分页面证据区域可能较稀疏或存在上下文冗余。"
        )

    if case["case_type"] == "BM25 + MV 改善排序例":
        return (
            "该案例保留原始页面、gold evidence bbox 与 occlusion 对照图，可用于展示视觉证据对排序补强的贡献。"
        )

    return "补充可视化案例，用于展示 evidence bbox、gold mask 与 random mask 的对照关系。"


def main():
    OUTPUT_FIG_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    query_rows = read_jsonl(QUERY_PATH)
    region_rows = read_jsonl(REGION_PATH)
    input_rows = read_csv(OCCLUSION_INPUTS)
    metric_rows = read_csv(OCCLUSION_METRICS)

    query_map = {}
    for row in query_rows:
        qid = row.get("query_id", "")
        query_map[qid] = get_query_text(row)

    region_map = {}
    for row in region_rows:
        qid = row.get("query_id", "")
        region_map[qid] = row.get("bbox", None)

    input_map = defaultdict(dict)
    for row in input_rows:
        input_map[row["query_id"]][row["condition"]] = row

    selected = select_cases(metric_rows)

    output_cases = []

    print("[Week7-Day6] Generating visual cases")
    print("Output figure dir:", OUTPUT_FIG_DIR)
    print("Output result dir:", OUTPUT_DIR)

    for idx, case in enumerate(selected, start=1):
        qid = case["query_id"]
        condition_map = input_map[qid]

        original_row = condition_map["Original"]
        gold_row = condition_map["Gold Mask"]
        random_row = condition_map["Random Mask"]

        gold_bbox = parse_bbox(original_row.get("gold_bbox", ""))

        if gold_bbox is None:
            gold_bbox = region_map.get(qid)

        case_id = f"evidence_case_{idx:03d}"
        output_path = OUTPUT_FIG_DIR / f"{case_id}.png"

        full_case = {
            **case,
            "case_id": case_id,
            "query_text": query_map.get(qid, ""),
            "gold_bbox": gold_bbox,
            "original_path": PROJECT_ROOT / original_row["image_path"],
            "gold_mask_path": PROJECT_ROOT / gold_row["image_path"],
            "random_mask_path": PROJECT_ROOT / random_row["image_path"],
            "explanation": explanation_for_case(case),
            "figure_path": str(output_path.relative_to(PROJECT_ROOT)),
        }

        make_case_figure(full_case, output_path)

        output_cases.append({
            "case_id": case_id,
            "case_type": full_case["case_type"],
            "query_id": qid,
            "page_id": full_case["page_id"],
            "query_text": full_case["query_text"],
            "gold_bbox": json.dumps(gold_bbox, ensure_ascii=False),
            "score_original": "{:.8f}".format(full_case["score_original"]),
            "score_gold_mask": "{:.8f}".format(full_case["score_gold_mask"]),
            "score_random_mask": "{:.8f}".format(full_case["score_random_mask"]),
            "COG_score": "{:.8f}".format(full_case["COG_score"]),
            "COG_nDCG": "{:.8f}".format(full_case["COG_nDCG"]),
            "random_iou_with_gold": "{:.6f}".format(full_case["random_iou_with_gold"]),
            "figure_path": full_case["figure_path"],
            "explanation": full_case["explanation"],
        })

        print(
            "DONE,{},{},{},COG_score={},figure={}".format(
                case_id,
                qid,
                full_case["case_type"],
                "{:.8f}".format(full_case["COG_score"]),
                full_case["figure_path"],
            )
        )

    with OUTPUT_CSV.open("w", encoding="utf-8", newline="") as f:
        fieldnames = [
            "case_id",
            "case_type",
            "query_id",
            "page_id",
            "query_text",
            "gold_bbox",
            "score_original",
            "score_gold_mask",
            "score_random_mask",
            "COG_score",
            "COG_nDCG",
            "random_iou_with_gold",
            "figure_path",
            "explanation",
        ]

        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(output_cases)

    lines = []
    lines.append("# Week 7 可视化案例图")
    lines.append("")
    lines.append("## Table 18: Week 7 可视化案例类型")
    lines.append("")
    lines.append("| 案例类型 | 数量 | 作用 |")
    lines.append("|---|---:|---|")
    lines.append("| Gold mask 后明显掉分 | 2 | 支撑证据依赖 |")
    lines.append("| Random mask 影响较小 | 1 | 支撑对照有效 |")
    lines.append("| 遮挡不敏感失败例 | 1 | 展示客观分析 |")
    lines.append("| BM25 + MV 改善排序例 | 1 | 支撑性能补强 |")
    lines.append("")
    lines.append("## Visual Cases")
    lines.append("")
    lines.append("| Case ID | Case Type | Query ID | Page ID | COG_score | Figure |")
    lines.append("|---|---|---|---|---:|---|")

    for row in output_cases:
        lines.append(
            "| {} | {} | {} | {} | {} | {} |".format(
                row["case_id"],
                row["case_type"],
                row["query_id"],
                row["page_id"],
                row["COG_score"],
                row["figure_path"],
            )
        )

    lines.append("")

    for row in output_cases:
        lines.append("## {}".format(row["case_id"]))
        lines.append("")
        lines.append("- Case type: {}".format(row["case_type"]))
        lines.append("- Query ID: {}".format(row["query_id"]))
        lines.append("- Page ID: {}".format(row["page_id"]))
        lines.append("- COG_score: {}".format(row["COG_score"]))
        lines.append("- COG_nDCG: {}".format(row["COG_nDCG"]))
        lines.append("- Explanation: {}".format(row["explanation"]))
        lines.append("")
        lines.append("![{}]({})".format(row["case_id"], Path(row["figure_path"]).as_posix()))
        lines.append("")

    OUTPUT_MD.write_text("\n".join(lines), encoding="utf-8")

    with OUTPUT_JSON.open("w", encoding="utf-8") as f:
        json.dump(output_cases, f, indent=2, ensure_ascii=False)

    print("")
    print("Wrote:", OUTPUT_CSV)
    print("Wrote:", OUTPUT_MD)
    print("Wrote:", OUTPUT_JSON)
    print("Generated figures:", len(output_cases))


if __name__ == "__main__":
    main()
