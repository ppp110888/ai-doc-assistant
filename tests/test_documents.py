from pathlib import Path

import pytest
from docx import Document
from pypdf import PdfWriter

from app.services.documents import extract_text, process_document


def test_extract_txt(tmp_path: Path):
    file_path = tmp_path / "sample.txt"
    file_path.write_text(
        "这是 TXT 测试内容。",
        encoding="utf-8",
    )

    result = extract_text(file_path)

    assert result == "这是 TXT 测试内容。"


def test_extract_docx(tmp_path: Path):
    file_path = tmp_path / "sample.docx"

    document = Document()
    document.add_paragraph("这是 DOCX 测试内容。")
    document.save(file_path)

    result = extract_text(file_path)

    assert result == "这是 DOCX 测试内容。"


def test_extract_pdf(tmp_path: Path):
    file_path = tmp_path / "sample.pdf"

    writer = PdfWriter()
    writer.add_blank_page(width=300, height=400)

    with file_path.open("wb") as file:
        writer.write(file)

    result = extract_text(file_path)

    assert isinstance(result, str)


def test_file_not_found(tmp_path: Path):
    file_path = tmp_path / "missing.txt"

    with pytest.raises(FileNotFoundError):
        extract_text(file_path)


def test_unsupported_file_type(tmp_path: Path):
    file_path = tmp_path / "sample.jpg"
    file_path.write_bytes(b"fake image")

    with pytest.raises(Exception) as error:
        extract_text(file_path)

    assert error.value.status_code == 400

def test_process_document(tmp_path: Path):
    file_path = tmp_path / "sample.txt"
    file_path.write_text(
        "abcdefghij",
        encoding="utf-8",
    )

    result = process_document(
        file_path,
        chunk_size=4,
        overlap=1,
    )

    assert result == [
        "abcd",
        "defg",
        "ghij",
    ]