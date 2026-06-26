from pathlib import Path


PROJECT_ROOT = Path(r"E:\Working\PCB_VisualRAG_Project")

OUT_MD = PROJECT_ROOT / "results" / "week8" / "visual_rag" / "week8_visual_rag_experiment_summary.md"

TABLES = {
    "Input Mapping": PROJECT_ROOT / "results" / "week8" / "visual_rag" / "qa_input_mapping_summary.csv",
    "Main Results": PROJECT_ROOT / "results" / "week8" / "visual_rag" / "tables" / "table19_visual_rag_main_results.md",
    "Occlusion Results": PROJECT_ROOT / "results" / "week8" / "visual_rag" / "tables" / "table20_occlusion_downstream_results.md",
    "Retrieval vs QA": PROJECT_ROOT / "results" / "week8" / "visual_rag" / "tables" / "table21_retrieval_vs_qa_results.md",
    "Retrieval Quality vs QA Quality": PROJECT_ROOT / "results" / "week8" / "visual_rag" / "tables" / "table23_retrieval_quality_vs_qa_quality.md",
}


def read_text(path):
    if not path.exists():
        return f"`Missing: {path}`"
    return path.read_text(encoding="utf-8", errors="ignore")


def main():
    lines = []

    lines.append("# Week 8 Lightweight Visual RAG Experiment Summary")
    lines.append("")
    lines.append("## Status")
    lines.append("")
    lines.append("```text")
    lines.append("QA input mapping: complete")
    lines.append("Ollama VLM inference: complete")
    lines.append("Rule-based QA evaluation: complete")
    lines.append("Result tables: complete")
    lines.append("```")
    lines.append("")
    lines.append("## Key Output Files")
    lines.append("")
    lines.append("```text")
    lines.append("results/week8/visual_rag/qa_inputs.csv")
    lines.append("results/week8/visual_rag/qa_outputs_ollama.csv")
    lines.append("results/week8/visual_rag/qa_outputs_manual_filled.csv")
    lines.append("results/week8/visual_rag/qa_evaluation.csv")
    lines.append("results/week8/visual_rag/tables/table19_visual_rag_main_results.csv")
    lines.append("results/week8/visual_rag/tables/table20_occlusion_downstream_results.csv")
    lines.append("results/week8/visual_rag/tables/table21_retrieval_vs_qa_results.csv")
    lines.append("results/week8/visual_rag/tables/table22_qa_error_breakdown.csv")
    lines.append("results/week8/visual_rag/tables/table23_retrieval_quality_vs_qa_quality.csv")
    lines.append("```")
    lines.append("")

    for title, path in TABLES.items():
        lines.append(f"## {title}")
        lines.append("")
        lines.append(read_text(path))
        lines.append("")

    lines.append("## Experiment-Level Conclusion")
    lines.append("")
    lines.append("```text")
    lines.append("The first-pass lightweight Visual RAG downstream experiment is complete.")
    lines.append("The results show that answer correctness is strongly tied to whether the retrieved page matches the gold evidence page.")
    lines.append("In the current page-level QA setup, Gold Masked and Random Masked conditions do not reduce QA accuracy.")
    lines.append("The occlusion result should therefore be reported cautiously as a negative or inconclusive downstream occlusion finding under the current setup.")
    lines.append("```")
    lines.append("")

    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

    print("[Week8] Experiment summary generated.")
    print("Wrote:", OUT_MD)


if __name__ == "__main__":
    main()
