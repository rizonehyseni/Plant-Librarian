"""Step 1: turn each study in data/raw into page-numbered text."""
from pathlib import Path

from .config import INTERIM, RAW


def pdf_pages(path: Path) -> list[str]:
    import fitz  # PyMuPDF

    with fitz.open(path) as doc:
        return [page.get_text() for page in doc]


def load_pages(path: Path) -> list[str]:
    if path.suffix.lower() == ".pdf":
        return pdf_pages(path)
    # Plain-text files: pages separated by form feeds, or one page.
    return path.read_text(encoding="utf-8").split("\f")


def run() -> dict[str, list[str]]:
    out = INTERIM / "text"
    out.mkdir(parents=True, exist_ok=True)
    docs = {}
    for path in sorted(RAW.iterdir()):
        if path.suffix.lower() not in {".pdf", ".txt"}:
            continue
        pages = load_pages(path)
        docs[path.stem] = pages
        (out / f"{path.stem}.txt").write_text(
            "".join(f"\n[page {i}]\n{p}" for i, p in enumerate(pages, 1)), encoding="utf-8"
        )
    print(f"ingest: {len(docs)} documents")
    return docs
