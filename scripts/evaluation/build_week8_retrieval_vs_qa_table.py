from pathlib import Path
import csv


PROJECT_ROOT = Path(r"E:\Working\PCB_VisualRAG_Project")

MAPPING_CSV = PROJECT_ROOT / "results" / "week8" / "visual_rag" / "qa_input_mapping_summary.csv"
QA_MAIN_CSV = PROJECT_ROOT / "results" / "week8" / "visual_rag" / "tables" / "table19_visual_rag_main_results.csv"

OUT_CSV = PROJECT_ROOT / "results" / "week8" / "visual_rag" / "tables" / "table23_retrieval_quality_vs_qa_quality.csv"
OUT_MD = PROJECT_ROOT / "results" / "week8" / "visual_rag" / "tables" / "table23_retrieval_quality_vs_qa_quality.md"


def read_csv(path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path, rows, fields):
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})


def write_md(path, rows, fields):
    lines = []
    lines.append("# Table 23: Retrieval Quality vs QA Quality")
    lines.append("")
    lines.append("| " + " | ".join(fields) + " |")
    lines.append("|" + "|".join(["---"] * len(fields)) + "|")

    for r in rows:
        lines.append("| " + " | ".join(str(r.get(k, "")) for k in fields) + " |")

    path.write_text("\n".join(lines), encoding="utf-8")


def f4(x):
    try:
        return f"{float(x):.4f}"
    except Exception:
        return "0.0000"


def main():
    mapping = read_csv(MAPPING_CSV)
    qa = read_csv(QA_MAIN_CSV)

    mapping_by_setting = {r["setting"]: r for r in mapping}
    qa_by_setting = {r["setting"]: r for r in qa}

    settings = [
        "Gold Evidence",
        "BM25",
        "Full MV",
        "Hybrid Fusion",
        "Budgeted MV",
        "Gold Masked",
        "Random Masked",
    ]

    rows = []

    for s in settings:
        m = mapping_by_setting.get(s, {})
        q = qa_by_setting.get(s, {})

        total = float(m.get("total", q.get("num_cases", 0)) or 0)
        hits = float(m.get("gold_page_hits", 0) or 0)

        retrieval_hit_rate = hits / total if total else 0.0

        rows.append({
            "setting": s,
            "num_cases": int(total),
            "gold_page_hits": int(hits),
            "retrieval_gold_hit_rate": f"{retrieval_hit_rate:.4f}",
            "answer_accuracy": q.get("answer_accuracy", ""),
            "evidence_supported_rate": q.get("evidence_supported_rate", ""),
            "unknown_rate": q.get("unknown_rate", ""),
            "hallucination_count": q.get("hallucination_count", ""),
            "used_run_file": m.get("used_run_file", ""),
        })

    fields = [
        "setting",
        "num_cases",
        "gold_page_hits",
        "retrieval_gold_hit_rate",
        "answer_accuracy",
        "evidence_supported_rate",
        "unknown_rate",
        "hallucination_count",
        "used_run_file",
    ]

    write_csv(OUT_CSV, rows, fields)
    write_md(OUT_MD, rows, fields)

    print("[Week8] Retrieval vs QA table generated.")
    print("Wrote:", OUT_CSV)
    print("Wrote:", OUT_MD)


if __name__ == "__main__":
    main()
