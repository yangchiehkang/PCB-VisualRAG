from pathlib import Path
import csv


PROJECT_ROOT = Path(r"E:\Working\PCB_VisualRAG_Project")

IN_CSV = PROJECT_ROOT / "results" / "week8" / "visual_rag" / "qa_outputs_manual_filled.csv"
OUT_CSV = PROJECT_ROOT / "results" / "week8" / "visual_rag" / "qa_evaluation_template.csv"


def read_csv(path):
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")

    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path, rows, fieldnames):
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def get_value(row, keys, default=""):
    for key in keys:
        value = row.get(key, "")
        if value is not None and str(value).strip() != "":
            return str(value).strip()
    return default


def main():
    rows = read_csv(IN_CSV)

    if not rows:
        raise ValueError(f"No rows found in input file: {IN_CSV}")

    out_rows = []

    for r in rows:
        out_rows.append({
            "case_id": get_value(r, ["case_id"]),
            "query_id": get_value(r, ["query_id"]),
            "setting": get_value(r, ["setting"]),
            "query": get_value(r, ["query"]),
            "gold_page_id": get_value(r, ["gold_page_id"]),
            "page_id": get_value(r, ["page_id"]),
            "is_gold_page": get_value(r, ["is_gold_page"]),
            "image_path": get_value(r, ["image_path"]),
            "vlm_answer": get_value(r, ["vlm_answer"]),
            "evidence_description": get_value(r, ["evidence_description"]),
            "confidence": get_value(r, ["confidence"]),
            "answer_correctness": "",
            "evidence_supported": "",
            "unknown": "",
            "error_type": "",
            "eval_notes": "",
        })

    fieldnames = [
        "case_id",
        "query_id",
        "setting",
        "query",
        "gold_page_id",
        "page_id",
        "is_gold_page",
        "image_path",
        "vlm_answer",
        "evidence_description",
        "confidence",
        "answer_correctness",
        "evidence_supported",
        "unknown",
        "error_type",
        "eval_notes",
    ]

    write_csv(OUT_CSV, out_rows, fieldnames)

    print("[Week8] QA evaluation template generated.")
    print("Input:", IN_CSV)
    print("Rows:", len(out_rows))
    print("Wrote:", OUT_CSV)


if __name__ == "__main__":
    main()
