from pathlib import Path
import pandas as pd


# ============================================================
# Week 6 Day 2 Compression Pipeline Validation Summary
# Generates:
# - day2_compression_pipeline_validation.csv
# - day2_compression_pipeline_validation.md
# - day2_validation_summary.md
# ============================================================

IN_FILE = Path("results/budgeted/joint_compression/day2_validation/day2_quantized_metrics.csv")
BUILD_FILE = Path("results/budgeted/joint_compression/day2_validation/day2_quantization_build_summary.csv")

OUT_DIR = Path("results/budgeted/joint_compression/day2_validation")
OUT_DIR.mkdir(parents=True, exist_ok=True)


def safe_to_markdown(df: pd.DataFrame) -> str:
    try:
        return df.to_markdown(index=False)
    except Exception:
        return df.to_string(index=False)


def status_completed(condition: bool) -> str:
    return "Completed" if condition else "Missing"


def main():
    if not IN_FILE.exists():
        raise FileNotFoundError(f"Metrics file not found: {IN_FILE}")

    metrics = pd.read_csv(IN_FILE)

    if BUILD_FILE.exists():
        build = pd.read_csv(BUILD_FILE)
    else:
        build = pd.DataFrame()

    rows = []

    for _, r in metrics.iterrows():
        compression = r["compression"]
        run_name = r["run_name"]

        run_file = Path(str(r["run_file"]))
        latency_ok = pd.notna(r.get("latency_ms_query"))
        metrics_ok = pd.notna(r.get("Recall@10")) and pd.notna(r.get("MRR@10")) and pd.notna(r.get("nDCG@10"))
        run_ok = run_file.exists()

        if compression == "None":
            index_built = True
        else:
            index_built = pd.notna(r.get("index_size_mb")) and pd.notna(r.get("mse"))

        rows.append({
            "Run Name": run_name,
            "Compression": compression,
            "Index Built": status_completed(bool(index_built)),
            "Run Output": status_completed(bool(run_ok)),
            "Metrics OK": status_completed(bool(metrics_ok)),
            "Latency OK": status_completed(bool(latency_ok)),
            "Recall@10": r.get("Recall@10"),
            "MRR@10": r.get("MRR@10"),
            "nDCG@10": r.get("nDCG@10"),
            "Index Size MB": r.get("index_size_mb"),
            "Reconstructed File Size MB": r.get("reconstructed_file_size_mb"),
            "Compression Ratio vs FP Payload": r.get("estimated_compression_ratio_vs_fp_payload"),
            "MSE": r.get("mse"),
            "MAE": r.get("mae"),
            "Latency ms/query": r.get("latency_ms_query"),
            "Build Time sec": r.get("build_time_sec"),
        })

    validation = pd.DataFrame(rows)

    validation_csv = OUT_DIR / "day2_compression_pipeline_validation.csv"
    validation_md = OUT_DIR / "day2_compression_pipeline_validation.md"
    summary_md = OUT_DIR / "day2_validation_summary.md"

    validation.to_csv(validation_csv, index=False, encoding="utf-8-sig")

    with validation_md.open("w", encoding="utf-8") as f:
        f.write("# Week 6 Day 2 Compression Pipeline Validation\n\n")
        f.write(safe_to_markdown(validation))
        f.write("\n")

    main_rows = validation[validation["Compression"] != "None"].copy()

    all_index_built = (main_rows["Index Built"] == "Completed").all()
    all_run_output = (validation["Run Output"] == "Completed").all()
    all_metrics_ok = (validation["Metrics OK"] == "Completed").all()
    all_latency_ok = (validation["Latency OK"] == "Completed").all()

    with summary_md.open("w", encoding="utf-8") as f:
        f.write("# Week 6 Day 2 Validation Summary\n\n")

        f.write("## 1. Validation Status\n\n")
        f.write("| Item | Status |\n")
        f.write("|---|---|\n")
        f.write(f"| Quantized index built | {'Completed' if all_index_built else 'Check Required'} |\n")
        f.write(f"| Run files generated | {'Completed' if all_run_output else 'Check Required'} |\n")
        f.write(f"| Metrics computed | {'Completed' if all_metrics_ok else 'Check Required'} |\n")
        f.write(f"| Latency recorded | {'Completed' if all_latency_ok else 'Check Required'} |\n\n")

        f.write("## 2. Compression Pipeline Table\n\n")
        f.write(safe_to_markdown(validation))
        f.write("\n\n")

        f.write("## 3. Build Summary\n\n")
        if not build.empty:
            f.write(safe_to_markdown(build))
            f.write("\n\n")
        else:
            f.write("Build summary file not found.\n\n")

        f.write("## 4. Day 2 Conclusion\n\n")
        if all_index_built and all_run_output and all_metrics_ok and all_latency_ok:
            f.write(
                "Week 6 Day 2 validation completed. PQ, OPQ+PQ, IVF+PQ, and IVF+OPQ+PQ "
                "pipelines were successfully built and evaluated on the representative setting "
                "N=10, M=16. The compressed embeddings produced valid run files, compatible metrics, "
                "and latency records. The pipeline is ready for Day 3 batch joint-budget experiments.\n"
            )
        else:
            f.write(
                "Week 6 Day 2 validation partially completed. Some items require checking before "
                "entering Day 3 batch joint-budget experiments.\n"
            )

    print("[Done] Day 2 validation summary generated.")
    print(f"[Output] {validation_csv}")
    print(f"[Output] {validation_md}")
    print(f"[Output] {summary_md}")


if __name__ == "__main__":
    main()
