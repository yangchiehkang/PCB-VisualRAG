from pathlib import Path
import csv
import json
import shutil


PROJECT_ROOT = Path(r"E:\Working\PCB_VisualRAG_Project")

INPUT_CSV = PROJECT_ROOT / "results" / "week8" / "visual_rag" / "qa_inputs.csv"
OUT_DIR = PROJECT_ROOT / "results" / "week8" / "visual_rag" / "manual_vlm_pack"
OUT_CASES_DIR = OUT_DIR / "cases"
OUT_IMAGES_DIR = OUT_DIR / "images"
OUT_MANIFEST = OUT_DIR / "manual_vlm_manifest.csv"
OUT_OUTPUT_TEMPLATE = PROJECT_ROOT / "results" / "week8" / "visual_rag" / "qa_outputs_manual_template.csv"

SELECTED_SETTINGS = [
    "Gold Evidence",
    "BM25",
    "Full MV",
    "Hybrid Fusion",
    "Budgeted MV",
    "Gold Masked",
    "Random Masked",
]


PROMPT_TEMPLATE = """You are answering a question about a PCB engineering document page.
Use only the provided page image as evidence.
If the page does not contain enough information, answer "Not enough evidence".

Question:
{query}

Return:
1. Short answer
2. Evidence description
3. Confidence: high / medium / low
"""


def safe_name(s):
    return s.replace(" ", "_").replace("/", "_").replace("\\", "_")


def main():
    OUT_CASES_DIR.mkdir(parents=True, exist_ok=True)
    OUT_IMAGES_DIR.mkdir(parents=True, exist_ok=True)

    rows = list(csv.DictReader(INPUT_CSV.open("r", encoding="utf-8-sig", newline="")))

    rows = [r for r in rows if r["setting"] in SELECTED_SETTINGS]

    manifest_rows = []
    output_rows = []

    for idx, r in enumerate(rows, start=1):
        query_id = r["query_id"]
        setting = r["setting"]
        case_id = f"{query_id}__{safe_name(setting)}"

        rel_image_path = r["image_path"]
        src_image = PROJECT_ROOT / rel_image_path

        copied_image_rel = ""
        copied_image_abs = ""

        if src_image.exists():
            suffix = src_image.suffix
            dst_image = OUT_IMAGES_DIR / f"{case_id}{suffix}"
            shutil.copyfile(src_image, dst_image)
            copied_image_rel = str(dst_image.relative_to(PROJECT_ROOT))
            copied_image_abs = str(dst_image)

        prompt = PROMPT_TEMPLATE.format(query=r["query"])

        case_md = OUT_CASES_DIR / f"{case_id}.md"
        case_md.write_text(
            "\n".join([
                f"# Case: {case_id}",
                "",
                f"- query_id: {query_id}",
                f"- setting: {setting}",
                f"- gold_page_id: {r['gold_page_id']}",
                f"- page_id: {r['page_id']}",
                f"- rank: {r['rank']}",
                f"- retrieval_score: {r['retrieval_score']}",
                f"- is_gold_page: {r['is_gold_page']}",
                f"- image_path: {copied_image_rel}",
                "",
                "## Prompt",
                "",
                "```text",
                prompt,
                "```",
            ]),
            encoding="utf-8",
        )

        manifest_rows.append({
            "case_id": case_id,
            "query_id": query_id,
            "setting": setting,
            "query": r["query"],
            "gold_page_id": r["gold_page_id"],
            "page_id": r["page_id"],
            "rank": r["rank"],
            "retrieval_score": r["retrieval_score"],
            "is_gold_page": r["is_gold_page"],
            "image_path": copied_image_rel,
            "case_prompt_file": str(case_md.relative_to(PROJECT_ROOT)),
        })

        output_rows.append({
            "case_id": case_id,
            "query_id": query_id,
            "setting": setting,
            "query": r["query"],
            "gold_page_id": r["gold_page_id"],
            "page_id": r["page_id"],
            "is_gold_page": r["is_gold_page"],
            "image_path": copied_image_rel,
            "vlm_answer": "",
            "evidence_description": "",
            "confidence": "",
            "notes": "",
        })

    with OUT_MANIFEST.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(manifest_rows[0].keys()))
        writer.writeheader()
        writer.writerows(manifest_rows)

    with OUT_OUTPUT_TEMPLATE.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(output_rows[0].keys()))
        writer.writeheader()
        writer.writerows(output_rows)

    print("[Week8] Manual VLM pack generated.")
    print("Cases:", len(manifest_rows))
    print("Wrote:", OUT_MANIFEST)
    print("Wrote:", OUT_OUTPUT_TEMPLATE)
    print("Images:", OUT_IMAGES_DIR)
    print("Case prompts:", OUT_CASES_DIR)


if __name__ == "__main__":
    main()
