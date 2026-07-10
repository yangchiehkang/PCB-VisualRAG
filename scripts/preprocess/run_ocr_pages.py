from pathlib import Path
from PIL import Image
import pytesseract

PROJECT_ROOT = Path(__file__).resolve().parents[2]
IMAGE_ROOT = PROJECT_ROOT / "data" / "images"
OCR_ROOT = PROJECT_ROOT / "data" / "ocr_raw"

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


def ocr_image(img_path: Path) -> str:
    image = Image.open(img_path)
    text = pytesseract.image_to_string(image, lang="eng")
    return text


def main():
    if not IMAGE_ROOT.exists():
        raise FileNotFoundError(f"IMAGE_ROOT not found: {IMAGE_ROOT}")

    image_paths = sorted(IMAGE_ROOT.glob("*/*.png"))
    print(f"Found {len(image_paths)} image files.")

    success = 0
    fail = 0

    for img_path in image_paths:
        doc_id = img_path.parent.name
        page_id = img_path.stem

        out_dir = OCR_ROOT / doc_id
        out_dir.mkdir(parents=True, exist_ok=True)

        out_txt = out_dir / f"{page_id}.txt"

        try:
            text = ocr_image(img_path)
            out_txt.write_text(text, encoding="utf-8")
            success += 1
        except Exception as e:
            out_txt.write_text(f"[OCR_ERROR] {e}", encoding="utf-8")
            fail += 1
            print(f"[WARN] OCR failed for {img_path}: {e}")

    print(f"Done. success={success}, fail={fail}")
    print(f"OCR output root: {OCR_ROOT}")


if __name__ == "__main__":
    main()
