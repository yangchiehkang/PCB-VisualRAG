from pathlib import Path
import csv


PROJECT_ROOT = Path(r"E:\Working\PCB_VisualRAG_Project")

REQUIRED_FILES = [
    "results/week8/visual_rag/qa_inputs.csv",
    "results/week8/visual_rag/qa_inputs.jsonl",
    "results/week8/visual_rag/qa_input_mapping_summary.csv",
    "results/week8/visual_rag/qa_outputs_ollama.csv",
    "results/week8/visual_rag/qa_outputs_manual_filled.csv",
    "results/week8/visual_rag/qa_evaluation_template.csv",
    "results/week8/visual_rag/qa_evaluation.csv",
    "results/week8/visual_rag/qa_evaluation_autofill_summary.csv",
    "results/week8/visual_rag/tables/table19_visual_rag_main_results.csv",
    "results/week8/visual_rag/tables/table20_occlusion_downstream_results.csv",
    "results/week8/visual_rag/tables/table21_retrieval_vs_qa_results.csv",
    "results/week8/visual_rag/tables/table22_qa_error_breakdown.csv",
    "results/week8/visual_rag/tables/table23_retrieval_quality_vs_qa_quality.csv",
]


def read_csv(path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def main():
    print("[Week8] Visual RAG Completion Check")
    print("=" * 80)

    missing = []

    for rel in REQUIRED_FILES:
        path = PROJECT_ROOT / rel
        ok = path.exists()
        print(("PASS" if ok else "MISSING"), rel)
        if not ok:
            missing.append(rel)

    print()
    print("[QA Input Check]")
    qa_inputs = PROJECT_ROOT / "results/week8/visual_rag/qa_inputs.csv"

    if qa_inputs.exists():
        rows = read_csv(qa_inputs)
        print("rows:", len(rows))
        print("missing_page:", sum(1 for r in rows if not r.get("page_id")))
        print("missing_image:", sum(1 for r in rows if not r.get("image_path")))
        print("retrieval_missing_page:", sum(1 for r in rows if r.get("setting") in ["BM25", "Full MV", "Hybrid Fusion", "Budgeted MV"] and not r.get("page_id")))
        print("retrieval_missing_image:", sum(1 for r in rows if r.get("setting") in ["BM25", "Full MV", "Hybrid Fusion", "Budgeted MV"] and not r.get("image_path")))

    print()
    print("[QA Output Check]")
    qa_outputs = PROJECT_ROOT / "results/week8/visual_rag/qa_outputs_manual_filled.csv"

    if qa_outputs.exists():
        rows = read_csv(qa_outputs)
        print("rows:", len(rows))
        print("blank_answer:", sum(1 for r in rows if not r.get("vlm_answer")))

    print()
    print("[QA Evaluation Check]")
    qa_eval = PROJECT_ROOT / "results/week8/visual_rag/qa_evaluation.csv"

    if qa_eval.exists():
        rows = read_csv(qa_eval)
        print("rows:", len(rows))
        print("missing_correctness:", sum(1 for r in rows if r.get("answer_correctness", "") == ""))
        print("missing_supported:", sum(1 for r in rows if r.get("evidence_supported", "") == ""))
        print("missing_unknown:", sum(1 for r in rows if r.get("unknown", "") == ""))
        print("missing_error_type:", sum(1 for r in rows if r.get("error_type", "") == ""))

    print()
    if missing:
        print("STATUS: INCOMPLETE")
    else:
        print("STATUS: WEEK8_VISUAL_RAG_EXPERIMENT_COMPLETE")


if __name__ == "__main__":
    main()
