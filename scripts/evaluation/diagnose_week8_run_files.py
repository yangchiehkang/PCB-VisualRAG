from pathlib import Path


PROJECT_ROOT = Path(r"E:\Working\PCB_VisualRAG_Project")

CANDIDATE_FILES = [
    PROJECT_ROOT / "results" / "week7" / "hybrid_fusion" / "hybrid_fullmv_N50_alpha1p0_run.tsv",
    PROJECT_ROOT / "results" / "week7" / "hybrid_fusion" / "hybrid_budgetmv_N50_M24_alpha1p0_run.tsv",
    PROJECT_ROOT / "results" / "week7" / "c2f_fixed_N" / "bm25_fullmv_N10_run.tsv",
    PROJECT_ROOT / "results" / "week7" / "c2f_fixed_N" / "bm25_budgetmv_N20_M8_none_run.tsv",
    PROJECT_ROOT / "results" / "week7" / "bm25_c2f" / "bm25_run.tsv",
]


def main():
    print("[Diagnose] Week 8 run files")
    print("=" * 80)

    for path in CANDIDATE_FILES:
        print()
        print("FILE:", path)

        if not path.exists():
            print("STATUS: MISSING")
            continue

        print("STATUS: EXISTS")
        print("SIZE:", path.stat().st_size)

        with path.open("r", encoding="utf-8-sig", errors="ignore") as f:
            for i, line in enumerate(f):
                if i >= 8:
                    break

                raw = line.rstrip("\n")
                print(f"LINE {i+1}: {raw}")
                print("TAB SPLIT:", raw.split("\t"))
                print("SPACE SPLIT:", raw.split())


if __name__ == "__main__":
    main()
