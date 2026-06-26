from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PAGE_CSV = PROJECT_ROOT / "data" / "metadata" / "page_inventory.csv"
DOC_CSV = PROJECT_ROOT / "data" / "metadata" / "document_inventory.csv"
OUTPUT_CSV = PROJECT_ROOT / "data" / "annotations" / "page_labels.csv"


def main():
    if not PAGE_CSV.exists():
        raise FileNotFoundError(f"Page inventory not found: {PAGE_CSV}")
    if not DOC_CSV.exists():
        raise FileNotFoundError(f"Document inventory not found: {DOC_CSV}")

    page_df = pd.read_csv(PAGE_CSV)
    doc_df = pd.read_csv(DOC_CSV)

    keep_doc_cols = ["doc_id", "file_name", "document_family", "experiment_tier"]
    doc_df = doc_df[[c for c in keep_doc_cols if c in doc_df.columns]]

    merged = page_df.merge(doc_df, on="doc_id", how="left")

    new_cols = {
        "page_type": "",
        "has_table": "",
        "has_diagram": "",
        "has_designators": "",
        "has_dimensions": "",
        "has_dense_text": "",
        "is_candidate_page": "",
        "label_notes": ""
    }

    for col, default_val in new_cols.items():
        if col not in merged.columns:
            merged[col] = default_val

    ordered_cols = [
        "page_id", "doc_id", "page_num",
        "file_name", "document_family", "experiment_tier",
        "pdf_path", "image_path", "image_name",
        "width", "height",
        "page_type", "has_table", "has_diagram", "has_designators",
        "has_dimensions", "has_dense_text", "is_candidate_page", "label_notes"
    ]
    ordered_cols = [c for c in ordered_cols if c in merged.columns] + [c for c in merged.columns if c not in ordered_cols]

    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    merged[ordered_cols].to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")

    print(f"[INFO] Initialized page labels file: {OUTPUT_CSV}")
    print(f"[INFO] Rows: {len(merged)}")


if __name__ == "__main__":
    main()
