from pathlib import Path
import csv
from collections import defaultdict, Counter


PROJECT_ROOT = Path(r"E:\Working\PCB_VisualRAG_Project")

EVAL_CSV = PROJECT_ROOT / "results" / "week8" / "visual_rag" / "qa_evaluation.csv"

OUT_DIR = PROJECT_ROOT / "results" / "week8" / "visual_rag" / "tables"

OUT_MAIN_CSV = OUT_DIR / "table19_visual_rag_main_results.csv"
OUT_MAIN_MD = OUT_DIR / "table19_visual_rag_main_results.md"

OUT_OCC_CSV = OUT_DIR / "table20_occlusion_downstream_results.csv"
OUT_OCC_MD = OUT_DIR / "table20_occlusion_downstream_results.md"

OUT_RETRIEVAL_QA_CSV = OUT_DIR / "table21_retrieval_vs_qa_results.csv"
OUT_RETRIEVAL_QA_MD = OUT_DIR / "table21_retrieval_vs_qa_results.md"

OUT_ERROR_CSV = OUT_DIR / "table22_qa_error_breakdown.csv"
OUT_ERROR_MD = OUT_DIR / "table22_qa_error_breakdown.md"


SETTING_ORDER = {
    "Gold Evidence": 1,
    "BM25": 2,
    "Full MV": 3,
    "Hybrid Fusion": 4,
    "Budgeted MV": 5,
    "Gold Masked": 6,
    "Random Masked": 7,
}


RETRIEVAL_SETTINGS = {
    "BM25",
    "Full MV",
    "Hybrid Fusion",
    "Budgeted MV",
}


OCCLUSION_SETTINGS = {
    "Gold Evidence",
    "Gold Masked",
    "Random Masked",
}


def read_csv(path):
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")

    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path, rows, fieldnames):
    path.parent.mkdir(parents=True, exist_ok=True)

    cleaned_rows = []
    for r in rows:
        cleaned_rows.append({k: r.get(k, "") for k in fieldnames})

    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(cleaned_rows)


def write_md(path, title, rows, fieldnames):
    lines = []
    lines.append(f"# {title}")
    lines.append("")
    lines.append("| " + " | ".join(fieldnames) + " |")
    lines.append("|" + "|".join(["---"] * len(fieldnames)) + "|")

    for r in rows:
        lines.append("| " + " | ".join(str(r.get(k, "")) for k in fieldnames) + " |")

    path.write_text("\n".join(lines), encoding="utf-8")


def norm(v):
    if v is None:
        return ""
    return str(v).strip()


def to_float(v, default=0.0):
    try:
        if v is None or str(v).strip() == "":
            return default
        return float(v)
    except Exception:
        return default


def to_int(v, default=0):
    try:
        if v is None or str(v).strip() == "":
            return default
        return int(float(v))
    except Exception:
        return default


def mean(vals):
    vals = list(vals)
    if not vals:
        return 0.0
    return sum(vals) / len(vals)


def fmt4(x):
    return f"{x:.4f}"


def summarize_by_setting(rows):
    grouped = defaultdict(list)

    for r in rows:
        grouped[norm(r.get("setting"))].append(r)

    out_rows = []

    for setting, items in grouped.items():
        n = len(items)

        answer_accuracy = mean(to_float(r.get("answer_correctness")) for r in items)
        evidence_supported_rate = mean(to_float(r.get("evidence_supported")) for r in items)
        unknown_rate = mean(to_float(r.get("unknown")) for r in items)
        gold_page_rate = mean(to_float(r.get("is_gold_page")) for r in items)

        concrete_answer_rate = 1.0 - unknown_rate

        no_answer_count = sum(1 for r in items if norm(r.get("vlm_answer")) == "")
        hallucination_count = sum(1 for r in items if norm(r.get("error_type")) == "hallucination")
        wrong_page_count = sum(1 for r in items if norm(r.get("error_type")) == "wrong_page")
        masked_evidence_count = sum(1 for r in items if norm(r.get("error_type")) == "masked_evidence")

        out_rows.append({
            "setting": setting,
            "num_cases": n,
            "gold_page_rate": fmt4(gold_page_rate),
            "answer_accuracy": fmt4(answer_accuracy),
            "evidence_supported_rate": fmt4(evidence_supported_rate),
            "unknown_rate": fmt4(unknown_rate),
            "concrete_answer_rate": fmt4(concrete_answer_rate),
            "no_answer_count": no_answer_count,
            "wrong_page_count": wrong_page_count,
            "hallucination_count": hallucination_count,
            "masked_evidence_count": masked_evidence_count,
        })

    out_rows.sort(key=lambda x: SETTING_ORDER.get(x["setting"], 999))

    return out_rows


def build_occlusion_rows(main_rows):
    rows = [r for r in main_rows if r["setting"] in OCCLUSION_SETTINGS]
    rows.sort(key=lambda x: SETTING_ORDER.get(x["setting"], 999))

    gold = next((r for r in rows if r["setting"] == "Gold Evidence"), None)
    gold_acc = to_float(gold.get("answer_accuracy")) if gold else 0.0
    gold_supp = to_float(gold.get("evidence_supported_rate")) if gold else 0.0

    out = []

    for r in rows:
        acc = to_float(r.get("answer_accuracy"))
        supp = to_float(r.get("evidence_supported_rate"))

        item = dict(r)
        item["accuracy_delta_vs_gold"] = fmt4(acc - gold_acc)
        item["support_delta_vs_gold"] = fmt4(supp - gold_supp)
        out.append(item)

    return out


def build_retrieval_rows(main_rows):
    rows = [r for r in main_rows if r["setting"] in RETRIEVAL_SETTINGS]
    rows.sort(key=lambda x: SETTING_ORDER.get(x["setting"], 999))

    out = []

    for r in rows:
        item = dict(r)
        item["retrieval_condition"] = r["setting"]
        out.append(item)

    return out


def build_error_breakdown(rows):
    grouped = defaultdict(list)

    for r in rows:
        grouped[norm(r.get("setting"))].append(r)

    out_rows = []

    for setting, items in grouped.items():
        n = len(items)
        counter = Counter(norm(r.get("error_type")) or "missing_error_type" for r in items)

        all_error_types = [
            "none",
            "wrong_page",
            "hallucination",
            "masked_evidence",
            "insufficient_info",
            "no_answer",
            "other",
            "missing_error_type",
        ]

        row = {
            "setting": setting,
            "num_cases": n,
        }

        for et in all_error_types:
            count = counter.get(et, 0)
            row[f"{et}_count"] = count
            row[f"{et}_rate"] = fmt4(count / n if n else 0.0)

        out_rows.append(row)

    out_rows.sort(key=lambda x: SETTING_ORDER.get(x["setting"], 999))

    return out_rows


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    rows = read_csv(EVAL_CSV)

    if not rows:
        raise ValueError(f"No rows found in input file: {EVAL_CSV}")

    main_rows = summarize_by_setting(rows)

    main_fields = [
        "setting",
        "num_cases",
        "gold_page_rate",
        "answer_accuracy",
        "evidence_supported_rate",
        "unknown_rate",
        "concrete_answer_rate",
        "no_answer_count",
        "wrong_page_count",
        "hallucination_count",
        "masked_evidence_count",
    ]

    write_csv(OUT_MAIN_CSV, main_rows, main_fields)
    write_md(
        OUT_MAIN_MD,
        "Table 19: Lightweight Visual RAG Main Results",
        main_rows,
        main_fields,
    )

    occ_rows = build_occlusion_rows(main_rows)

    occ_fields = main_fields + [
        "accuracy_delta_vs_gold",
        "support_delta_vs_gold",
    ]

    write_csv(OUT_OCC_CSV, occ_rows, occ_fields)
    write_md(
        OUT_OCC_MD,
        "Table 20: Occlusion Downstream Results",
        occ_rows,
        occ_fields,
    )

    retrieval_rows = build_retrieval_rows(main_rows)

    retrieval_fields = [
        "retrieval_condition",
        "setting",
        "num_cases",
        "gold_page_rate",
        "answer_accuracy",
        "evidence_supported_rate",
        "unknown_rate",
        "concrete_answer_rate",
        "wrong_page_count",
        "hallucination_count",
    ]

    write_csv(OUT_RETRIEVAL_QA_CSV, retrieval_rows, retrieval_fields)
    write_md(
        OUT_RETRIEVAL_QA_MD,
        "Table 21: Retrieval vs QA Results",
        retrieval_rows,
        retrieval_fields,
    )

    error_rows = build_error_breakdown(rows)

    error_fields = [
        "setting",
        "num_cases",
        "none_count",
        "none_rate",
        "wrong_page_count",
        "wrong_page_rate",
        "hallucination_count",
        "hallucination_rate",
        "masked_evidence_count",
        "masked_evidence_rate",
        "insufficient_info_count",
        "insufficient_info_rate",
        "no_answer_count",
        "no_answer_rate",
        "other_count",
        "other_rate",
        "missing_error_type_count",
        "missing_error_type_rate",
    ]

    write_csv(OUT_ERROR_CSV, error_rows, error_fields)
    write_md(
        OUT_ERROR_MD,
        "Table 22: QA Error Breakdown",
        error_rows,
        error_fields,
    )

    print("[Week8] Visual RAG result tables generated.")
    print("Input:", EVAL_CSV)
    print("Rows:", len(rows))
    print()
    print("Wrote:", OUT_MAIN_CSV)
    print("Wrote:", OUT_MAIN_MD)
    print("Wrote:", OUT_OCC_CSV)
    print("Wrote:", OUT_OCC_MD)
    print("Wrote:", OUT_RETRIEVAL_QA_CSV)
    print("Wrote:", OUT_RETRIEVAL_QA_MD)
    print("Wrote:", OUT_ERROR_CSV)
    print("Wrote:", OUT_ERROR_MD)
    print()
    print("Main summary:")
    for r in main_rows:
        print(r)


if __name__ == "__main__":
    main()
