from pathlib import Path
import json
import csv


PROJECT_ROOT = Path(r"E:\Working\PCB_VisualRAG_Project")

OUT_DIR = PROJECT_ROOT / "results" / "week8" / "visual_rag"
PAPER_NOTES_DIR = PROJECT_ROOT / "paper" / "notes"
PAPER_SECTIONS_DIR = PROJECT_ROOT / "paper" / "sections"

PROTOCOL_MD = OUT_DIR / "visual_rag_protocol.md"
CLAIMS_MD = PAPER_NOTES_DIR / "claims_and_evidence.md"
OUTLINE_MD = PAPER_NOTS_DIR = PAPER_NOTES_DIR / "sections_outline.md"
FIGURES_MD = PAPER_NOTES_DIR / "figures_manifest.md"

QA_SETTINGS_CSV = OUT_DIR / "qa_settings.csv"
QA_METRICS_CSV = OUT_DIR / "qa_metrics_definition.csv"


SETTINGS = [
    {
        "setting": "Gold Evidence",
        "source": "gold evidence page",
        "purpose": "QA upper bound",
        "required": "yes",
    },
    {
        "setting": "BM25",
        "source": "BM25 top retrieval result",
        "purpose": "strong OCR/text baseline",
        "required": "yes",
    },
    {
        "setting": "Full MV",
        "source": "Full multi-vector retrieval result",
        "purpose": "visual retrieval baseline",
        "required": "recommended",
    },
    {
        "setting": "Hybrid Fusion",
        "source": "hybrid BM25 + MV retrieval result",
        "purpose": "text-visual fusion validation",
        "required": "yes",
    },
    {
        "setting": "Budgeted MV",
        "source": "budgeted multi-vector retrieval result",
        "purpose": "budgeted retrieval downstream validation",
        "required": "optional",
    },
    {
        "setting": "Gold Masked",
        "source": "gold evidence region masked page",
        "purpose": "test evidence occlusion effect",
        "required": "yes",
    },
    {
        "setting": "Random Masked",
        "source": "random region masked page",
        "purpose": "occlusion control",
        "required": "yes",
    },
]


METRICS = [
    {
        "metric": "Answer Correctness",
        "type": "binary",
        "values": "0/1",
        "description": "Whether the answer is correct.",
    },
    {
        "metric": "Evidence Supported",
        "type": "binary",
        "values": "0/1",
        "description": "Whether the answer is supported by visible page evidence.",
    },
    {
        "metric": "Unknown Rate",
        "type": "binary",
        "values": "0/1",
        "description": "Whether the model answers not enough evidence / unknown.",
    },
    {
        "metric": "Answer Consistency",
        "type": "categorical",
        "values": "same/changed",
        "description": "Whether the answer changes across input settings.",
    },
    {
        "metric": "Error Type",
        "type": "categorical",
        "values": "wrong_page/masked_evidence/hallucination/insufficient_info/ocr_error/none",
        "description": "Manual error category.",
    },
]


def write_csv(path, rows, fieldnames):
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    PAPER_NOTES_DIR.mkdir(parents=True, exist_ok=True)
    PAPER_SECTIONS_DIR.mkdir(parents=True, exist_ok=True)

    write_csv(
        QA_SETTINGS_CSV,
        SETTINGS,
        ["setting", "source", "purpose", "required"],
    )

    write_csv(
        QA_METRICS_CSV,
        METRICS,
        ["metric", "type", "values", "description"],
    )

    protocol_lines = []
    protocol_lines.append("# Week 8 Day 1: Lightweight Visual RAG Protocol")
    protocol_lines.append("")
    protocol_lines.append("## Goal")
    protocol_lines.append("")
    protocol_lines.append("Build a lightweight downstream Visual RAG / QA validation pipeline.")
    protocol_lines.append("")
    protocol_lines.append("```text")
    protocol_lines.append("Query")
    protocol_lines.append("↓")
    protocol_lines.append("Retrieval Result")
    protocol_lines.append("↓")
    protocol_lines.append("Evidence Page / Page Subset")
    protocol_lines.append("↓")
    protocol_lines.append("VLM Answer")
    protocol_lines.append("↓")
    protocol_lines.append("Answer Evaluation")
    protocol_lines.append("```")
    protocol_lines.append("")
    protocol_lines.append("## Validation Questions")
    protocol_lines.append("")
    protocol_lines.append("- Does retrieval evidence quality affect answer quality?")
    protocol_lines.append("- Can Budgeted Retrieval still support Visual QA / RAG?")
    protocol_lines.append("- Does Evidence Occlusion affect downstream answers?")
    protocol_lines.append("")
    protocol_lines.append("## QA Input Settings")
    protocol_lines.append("")
    protocol_lines.append("| Setting | Source | Purpose | Required |")
    protocol_lines.append("|---|---|---|---|")

    for row in SETTINGS:
        protocol_lines.append(
            f"| {row['setting']} | {row['source']} | {row['purpose']} | {row['required']} |"
        )

    protocol_lines.append("")
    protocol_lines.append("## Evaluation Metrics")
    protocol_lines.append("")
    protocol_lines.append("| Metric | Type | Values | Description |")
    protocol_lines.append("|---|---|---|---|")

    for row in METRICS:
        protocol_lines.append(
            f"| {row['metric']} | {row['type']} | {row['values']} | {row['description']} |"
        )

    protocol_lines.append("")
    protocol_lines.append("## Fixed Prompt Template")
    protocol_lines.append("")
    protocol_lines.append("```text")
    protocol_lines.append("You are answering a question about a PCB engineering document page.")
    protocol_lines.append("Use only the provided page image as evidence.")
    protocol_lines.append('If the page does not contain enough information, answer "Not enough evidence".')
    protocol_lines.append("")
    protocol_lines.append("Question:")
    protocol_lines.append("{query}")
    protocol_lines.append("")
    protocol_lines.append("Return:")
    protocol_lines.append("1. Short answer")
    protocol_lines.append("2. Evidence description")
    protocol_lines.append("3. Confidence: high / medium / low")
    protocol_lines.append("```")
    protocol_lines.append("")
    protocol_lines.append("## Planned Outputs")
    protocol_lines.append("")
    protocol_lines.append("```text")
    protocol_lines.append("results/week8/visual_rag/qa_inputs.jsonl")
    protocol_lines.append("results/week8/visual_rag/qa_outputs_all.jsonl")
    protocol_lines.append("results/week8/visual_rag/qa_evaluation.csv")
    protocol_lines.append("results/week8/visual_rag/tables/table19_visual_rag_main_results.csv")
    protocol_lines.append("results/week8/visual_rag/tables/table20_occlusion_downstream_results.csv")
    protocol_lines.append("```")

    PROTOCOL_MD.write_text("\n".join(protocol_lines), encoding="utf-8")

    claims_lines = []
    claims_lines.append("# Claims and Evidence")
    claims_lines.append("")
    claims_lines.append("## Main Claim")
    claims_lines.append("")
    claims_lines.append(
        "This work proposes a budget-aware VisualRAG retrieval framework for PCB documents. "
        "While OCR-based BM25 remains a strong overall baseline, visual multi-vector retrieval "
        "and hybrid fusion provide complementary evidence-aware retrieval signals."
    )
    claims_lines.append("")
    claims_lines.append("## Supported Claims")
    claims_lines.append("")
    claims_lines.append("| Claim | Evidence | Source |")
    claims_lines.append("|---|---|---|")
    claims_lines.append("| BM25 remains a strong overall baseline | Highest main retrieval nDCG@10 | Week 7 Table 14 |")
    claims_lines.append("| Hybrid Fusion matches BM25 on evidence retrieval | Evidence Hit@5 = 1.0000, Evidence Hit@10 = 1.0000 | Week 7 Table 16 |")
    claims_lines.append("| Hybrid Fusion improves region-level localization | Region Hit@5 = 0.4000 | Week 7 Region Hit |")
    claims_lines.append("| Gold evidence region is causally important | Gold Mask score drops to 0.00000000 | Week 7 Table 17 |")
    claims_lines.append("| Downstream QA should reflect evidence quality | To be validated | Week 8 Visual RAG |")
    claims_lines.append("")
    claims_lines.append("## Claims to Avoid")
    claims_lines.append("")
    claims_lines.append("- Do not claim that the visual method universally outperforms BM25.")
    claims_lines.append("- Do not claim end-to-end model training.")
    claims_lines.append("- Do not claim full automatic answer evaluation if manual scoring is used.")

    CLAIMS_MD.write_text("\n".join(claims_lines), encoding="utf-8")

    outline_lines = []
    outline_lines.append("# Paper Sections Outline")
    outline_lines.append("")
    outline_lines.append("1. Introduction")
    outline_lines.append("2. Related Work")
    outline_lines.append("3. Problem Setup")
    outline_lines.append("4. Method")
    outline_lines.append("5. Experimental Setup")
    outline_lines.append("6. Main Results")
    outline_lines.append("7. Evidence Attribution and Counterfactual Validation")
    outline_lines.append("8. Lightweight Visual RAG Downstream Validation")
    outline_lines.append("9. Discussion and Limitations")
    outline_lines.append("10. Conclusion")
    outline_lines.append("")
    outline_lines.append("## Week 8 Writing Priority")
    outline_lines.append("")
    outline_lines.append("1. Problem Setup")
    outline_lines.append("2. Method")
    outline_lines.append("3. Introduction")
    outline_lines.append("4. Experiments outline")

    OUTLINE_MD.write_text("\n".join(outline_lines), encoding="utf-8")

    figures_lines = []
    figures_lines.append("# Figures and Tables Manifest")
    figures_lines.append("")
    figures_lines.append("| ID | Item | Status | Source |")
    figures_lines.append("|---|---|---|---|")
    figures_lines.append("| Figure 1 | Overall Pipeline | TODO | paper/figures/fig1_pipeline.pdf |")
    figures_lines.append("| Table 1 | Baseline Retrieval Results | Available | previous results |")
    figures_lines.append("| Table 2 | Budgeted Retrieval Results | Available | Week 6 / Week 7 |")
    figures_lines.append("| Table 3 | BM25-C2F and Hybrid Results | Available | Week 7 Table 14 |")
    figures_lines.append("| Table 4 | Evidence Hit / Region Hit | Available | Week 7 Table 16 + Region Hit |")
    figures_lines.append("| Table 5 | Occlusion Main Results | Available | Week 7 Table 17 |")
    figures_lines.append("| Figure 2 | Occlusion Visual Cases | Available | figures/week7/evidence_case_*.png |")
    figures_lines.append("| Table 6 | Lightweight Visual RAG Results | TODO | Week 8 Table 19 |")
    figures_lines.append("| Figure 3 | Retrieval Quality vs QA Quality | TODO | Week 8 |")

    FIGURES_MD.write_text("\n".join(figures_lines), encoding="utf-8")

    print("[Week8-Day1] Visual RAG protocol prepared.")
    print("Wrote:", PROTOCOL_MD)
    print("Wrote:", QA_SETTINGS_CSV)
    print("Wrote:", QA_METRICS_CSV)
    print("Wrote:", CLAIMS_MD)
    print("Wrote:", OUTLINE_MD)
    print("Wrote:", FIGURES_MD)


if __name__ == "__main__":
    main()
