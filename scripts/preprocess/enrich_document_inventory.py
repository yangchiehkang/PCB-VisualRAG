from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DOC_CSV = PROJECT_ROOT / "data" / "metadata" / "document_inventory.csv"


def infer_document_family(file_name: str) -> str:
    name = str(file_name).lower()

    if "fabrication" in name:
        return "fabrication"
    if "assembly" in name:
        return "assembly"
    if "bom" in name:
        return "bom"
    if "layout" in name:
        return "layout_guideline"
    if "manual" in name:
        return "manual"
    if "eval" in name or "evm" in name:
        return "evaluation_board"
    return "other"


def infer_experiment_tier(file_name: str) -> str:
    name = str(file_name).lower()

    core_keywords = ["fabrication", "assembly", "bom"]
    if any(k in name for k in core_keywords):
        return "core"

    extended_keywords = ["manual", "layout", "eval", "evm"]
    if any(k in name for k in extended_keywords):
        return "extended"

    return "exclude"


def main():
    if not DOC_CSV.exists():
        raise FileNotFoundError(f"Document inventory not found: {DOC_CSV}")

    df = pd.read_csv(DOC_CSV)

    df["document_family"] = df["file_name"].apply(infer_document_family)
    df["experiment_tier"] = df["file_name"].apply(infer_experiment_tier)

    df.to_csv(DOC_CSV, index=False, encoding="utf-8-sig")

    print(f"[INFO] Enriched document inventory: {DOC_CSV}")
    print(df[["doc_id", "file_name", "document_family", "experiment_tier"]].to_string(index=False))


if __name__ == "__main__":
    main()
