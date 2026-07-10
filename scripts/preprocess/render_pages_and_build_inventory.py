from pathlib import Path
import pandas as pd
import fitz  # PyMuPDF
from tqdm import tqdm

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_PDF_DIR = PROJECT_ROOT / "data" / "raw_pdfs"
IMAGES_DIR = PROJECT_ROOT / "data" / "images"
METADATA_DIR = PROJECT_ROOT / "data" / "metadata"

DOC_CSV = METADATA_DIR / "document_inventory.csv"
PAGE_CSV = METADATA_DIR / "page_inventory.csv"

ZOOM_X = 2.0
ZOOM_Y = 2.0


def make_page_id(doc_id: str, page_num: int) -> str:
    return f"{doc_id}_p{page_num:03d}"


def render_pdf_pages(pdf_path: Path, doc_id: str):
    output_dir = IMAGES_DIR / doc_id
    output_dir.mkdir(parents=True, exist_ok=True)

    page_records = []

    with fitz.open(pdf_path) as doc:
        for i in tqdm(range(len(doc)), desc=f"Rendering {doc_id}", leave=False):
            page = doc[i]
            page_num = i + 1
            page_id = make_page_id(doc_id, page_num)

            matrix = fitz.Matrix(ZOOM_X, ZOOM_Y)
            pix = page.get_pixmap(matrix=matrix, alpha=False)

            image_name = f"{page_id}.png"
            image_path = output_dir / image_name
            pix.save(str(image_path))

            page_records.append({
                "page_id": page_id,
                "doc_id": doc_id,
                "page_num": page_num,
                "pdf_path": str(pdf_path.relative_to(PROJECT_ROOT)).replace("\\", "/"),
                "image_path": str(image_path.relative_to(PROJECT_ROOT)).replace("\\", "/"),
                "image_name": image_name,
                "width": pix.width,
                "height": pix.height,
                "split": "train",
                "include_flag": "yes",
                "notes": ""
            })

    return page_records


def main():
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    METADATA_DIR.mkdir(parents=True, exist_ok=True)

    if DOC_CSV.exists():
        doc_df = pd.read_csv(DOC_CSV)
        pdf_list = [(row["doc_id"], PROJECT_ROOT / row["pdf_path"]) for _, row in doc_df.iterrows()]
    else:
        pdf_files = sorted(RAW_PDF_DIR.glob("*.pdf"))
        pdf_list = [(pdf.name.split("_")[0], pdf) for pdf in pdf_files]

    all_page_records = []

    for doc_id, pdf_path in pdf_list:
        if not pdf_path.exists():
            print(f"[WARN] Missing pdf for {doc_id}: {pdf_path}")
            continue
        records = render_pdf_pages(pdf_path, doc_id)
        all_page_records.extend(records)

    page_df = pd.DataFrame(all_page_records)
    page_df.to_csv(PAGE_CSV, index=False, encoding="utf-8-sig")

    print(f"[INFO] Wrote page inventory: {PAGE_CSV}")
    print(f"[INFO] Total pages rendered: {len(page_df)}")


if __name__ == "__main__":
    main()
