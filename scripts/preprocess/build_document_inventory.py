from pathlib import Path
import pandas as pd
import fitz  # PyMuPDF

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_PDF_DIR = PROJECT_ROOT / "data" / "raw_pdfs"
METADATA_DIR = PROJECT_ROOT / "data" / "metadata"
OUTPUT_CSV = METADATA_DIR / "document_inventory.csv"


def infer_doc_id(filename: str) -> str:
    return filename.split("_")[0]


def count_pdf_pages(pdf_path: Path) -> int:
    try:
        with fitz.open(pdf_path) as doc:
            return len(doc)
    except Exception as e:
        print(f"[WARN] Failed to read {pdf_path.name}: {e}")
        return -1


def main():
    if not RAW_PDF_DIR.exists():
        raise FileNotFoundError(f"RAW_PDF_DIR not found: {RAW_PDF_DIR}")

    METADATA_DIR.mkdir(parents=True, exist_ok=True)

    pdf_files = sorted(RAW_PDF_DIR.glob("*.pdf"))
    records = []

    for pdf_path in pdf_files:
        doc_id = infer_doc_id(pdf_path.name)
        page_count = count_pdf_pages(pdf_path)

        records.append({
            "doc_id": doc_id,
            "file_name": pdf_path.name,
            "pdf_path": str(pdf_path.relative_to(PROJECT_ROOT)).replace("\\", "/"),
            "page_count": page_count,
        })

    df = pd.DataFrame(records)
    df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")

    print(f"[INFO] Wrote document inventory: {OUTPUT_CSV}")
    print(f"[INFO] Documents: {len(df)}")


if __name__ == "__main__":
    main()
