from pathlib import Path
import json

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OCR_ROOT = PROJECT_ROOT / "data" / "ocr_raw"
OUT_PATH = PROJECT_ROOT / "data" / "metadata" / "ocr_corpus.jsonl"


def ensure_exists(path: Path, name: str):
    if not path.exists():
        raise FileNotFoundError(f"{name} not found: {path}")


def main():
    ensure_exists(OCR_ROOT, "OCR root directory")
    txt_paths = sorted(OCR_ROOT.glob("*/*.txt"))
    print(f"Found {len(txt_paths)} OCR txt files.")

    total = 0
    kept = 0
    skipped = 0

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with OUT_PATH.open("w", encoding="utf-8") as fout:
        for txt_path in txt_paths:
            total += 1
            doc_id = txt_path.parent.name
            page_id = txt_path.stem

            text = txt_path.read_text(encoding="utf-8", errors="ignore").strip()

            if not text or text.startswith("[OCR_ERROR"):
                skipped += 1
                continue

            row = {
                "doc_id": doc_id,
                "page_id": page_id,
                "text": text,
                "source": str(txt_path.relative_to(PROJECT_ROOT)).replace("\\", "/")
            }
            fout.write(json.dumps(row, ensure_ascii=False) + "\n")
            kept += 1

    print(f"Done. total={total}, kept={kept}, skipped={skipped}")
    print(f"Wrote corpus jsonl to: {OUT_PATH}")


if __name__ == "__main__":
    main()
