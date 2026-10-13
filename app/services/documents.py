from pathlib import Path

from docx import Document
from fastapi import HTTPException
from pypdf import PdfReader
from app.services.text_processing import split_text


def extract_text(file_path: Path) -> str:
    extension = file_path.suffix.lower()

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if extension == ".txt":
        return file_path.read_text(
            encoding="utf-8",
            errors="ignore",
        )

    if extension == ".pdf":
        reader = PdfReader(str(file_path))
        return "\n".join(
            page.extract_text() or ""
            for page in reader.pages
        )

    if extension == ".docx":
        document = Document(str(file_path))
        return "\n".join(
            paragraph.text
            for paragraph in document.paragraphs
            if paragraph.text.strip()
        )

    raise HTTPException(
        status_code=400,
        detail="Unsupported document type",
    )

def process_document(
    file_path: Path,
    chunk_size: int = 500,
    overlap: int = 50,
) -> list[str]:
    text = extract_text(file_path)

    return split_text(
        text,
        chunk_size=chunk_size,
        overlap=overlap,
    )