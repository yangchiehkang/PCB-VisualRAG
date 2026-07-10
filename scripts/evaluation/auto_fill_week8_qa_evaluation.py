from pathlib import Path
import csv
from collections import defaultdict


PROJECT_ROOT = Path(r"E:\Working\PCB_VisualRAG_Project")

IN_CSV = PROJECT_ROOT / "results" / "week8" / "visual_rag" / "qa_evaluation_template.csv"
OUT_CSV = PROJECT_ROOT / "results" / "week8" / "visual_rag" / "qa_evaluation.csv"
SUMMARY_CSV = PROJECT_ROOT / "results" / "week8" / "visual_rag" / "qa_evaluation_autofill_summary.csv"


UNKNOWN_PATTERNS = [
    "not enough evidence",
    "insufficient evidence",
    "cannot determine",
    "can't determine",
    "cannot be determined",
    "not provided",
    "not visible",
    "no evidence",
    "unable to determine",
]


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


def norm(v):
    if v is None:
        return ""
    return str(v).strip()


def is_blank(v):
    return norm(v) == ""


def is_true(v):
    return norm(v) in {"1", "true", "True", "yes", "YES", "y", "Y"}


def is_unknown_answer(answer):
    a = norm(answer).lower()

    if not a:
        return True

    for p in UNKNOWN_PATTERNS:
        if p in a:
            return True

    return False


def infer_error_type(setting, is_gold_page, unknown, has_answer, answer_correctness, evidence_supported):
    setting = norm(setting)

    if not has_answer:
        return "no_answer"

    if answer_correctness == "1" and evidence_supported == "1":
        return "none"

    if is_gold_page == "0" and unknown == "1":
        return "wrong_page"

    if is_gold_page == "0" and unknown == "0":
        return "hallucination"

    if is_gold_page == "1" and unknown == "1":
        if setting == "Gold Masked":
            return "masked_evidence"
        return "insufficient_info"

    return "other"


def infer_eval_notes(setting, is_gold_page, unknown, has_answer, answer_correctness, evidence_supported, error_type):
    if error_type == "none":
        return "Auto-filled: gold page retrieved and model produced a non-unknown answer."

    if error_type == "no_answer":
        return "Auto-filled: VLM answer is empty."

    if error_type == "wrong_page":
        return "Auto-filled: retrieved page is not the gold page; model reported insufficient evidence."

    if error_type == "hallucination":
        return "Auto-filled: retrieved page is not the gold page but model produced a concrete answer."

    if error_type == "masked_evidence":
        return "Auto-filled: gold page was provided but masked condition led to insufficient evidence."

    if error_type == "insufficient_info":
        return "Auto-filled: gold page was provided but model answered insufficient evidence."

    return "Auto-filled by rule-based weak QA evaluator."


def autofill_row(r):
    setting = norm(r.get("setting", ""))
    is_gold_page = "1" if is_true(r.get("is_gold_page", "")) else "0"
    answer = norm(r.get("vlm_answer", ""))

    has_answer = not is_blank(answer)
    unknown_flag = "1" if is_unknown_answer(answer) else "0"

    # Weak page-level correctness:
    # correct only when the input page is the gold page and the model gives a concrete answer.
    if is_gold_page == "1" and unknown_flag == "0":
        answer_correctness = "1"
    else:
        answer_correctness = "0"

    # Evidence-supported:
    # - gold page + concrete answer: supported
    # - wrong page + "not enough evidence": supported refusal
    # - wrong page + concrete answer: unsupported / hallucination
    # - gold page + unknown: unsupported failure
    if not has_answer:
        evidence_supported = "0"
    elif is_gold_page == "1" and unknown_flag == "0":
        evidence_supported = "1"
    elif is_gold_page == "0" and unknown_flag == "1":
        evidence_supported = "1"
    else:
        evidence_supported = "0"

    error_type = infer_error_type(
        setting=setting,
        is_gold_page=is_gold_page,
        unknown=unknown_flag,
        has_answer=has_answer,
        answer_correctness=answer_correctness,
        evidence_supported=evidence_supported,
    )

    eval_notes = infer_eval_notes(
        setting=setting,
        is_gold_page=is_gold_page,
        unknown=unknown_flag,
        has_answer=has_answer,
        answer_correctness=answer_correctness,
        evidence_supported=evidence_supported,
        error_type=error_type,
    )

    r["answer_correctness"] = answer_correctness
    r["evidence_supported"] = evidence_supported
    r["unknown"] = unknown_flag
    r["error_type"] = error_type
    r["eval_notes"] = eval_notes

    return r


def build_summary(rows):
    grouped = defaultdict(list)

    for r in rows:
        grouped[r["setting"]].append(r)

    summary_rows = []

    order = {
        "Gold Evidence": 1,
        "BM25": 2,
        "Full MV": 3,
        "Hybrid Fusion": 4,
        "Budgeted MV": 5,
        "Gold Masked": 6,
        "Random Masked": 7,
    }

    for setting, items in grouped.items():
        n = len(items)

        acc = sum(int(r["answer_correctness"]) for r in items) / n if n else 0
        supp = sum(int(r["evidence_supported"]) for r in items) / n if n else 0
        unk = sum(int(r["unknown"]) for r in items) / n if n else 0
        gold_rate = sum(int(r["is_gold_page"]) for r in items) / n if n else 0

        summary_rows.append({
            "setting": setting,
            "num_cases": n,
            "gold_page_rate": f"{gold_rate:.4f}",
            "answer_accuracy": f"{acc:.4f}",
            "evidence_supported_rate": f"{supp:.4f}",
            "unknown_rate": f"{unk:.4f}",
        })

    summary_rows.sort(key=lambda x: order.get(x["setting"], 999))

    return summary_rows


def main():
    rows = read_csv(IN_CSV)

    if not rows:
        raise ValueError(f"No rows found in input file: {IN_CSV}")

    out_rows = []

    for r in rows:
        out_rows.append(autofill_row(r))

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

    summary_rows = build_summary(out_rows)

    summary_fieldnames = [
        "setting",
        "num_cases",
        "gold_page_rate",
        "answer_accuracy",
        "evidence_supported_rate",
        "unknown_rate",
    ]

    write_csv(SUMMARY_CSV, summary_rows, summary_fieldnames)

    print("[Week8] QA evaluation auto-filled.")
    print("Input:", IN_CSV)
    print("Rows:", len(out_rows))
    print("Wrote:", OUT_CSV)
    print("Wrote:", SUMMARY_CSV)

    print()
    print("Summary:")
    for r in summary_rows:
        print(r)


if __name__ == "__main__":
    main()
