from pathlib import Path

import pytest

from app.services import indexing


def test_index_document(monkeypatch, tmp_path: Path):
    file_path = tmp_path / "sample.txt"
    file_path.write_text("测试内容", encoding="utf-8")

    stored_data = {}

    monkeypatch.setattr(
        indexing,
        "process_document",
        lambda *args, **kwargs: [
            "第一段",
            "第二段",
        ],
    )

    monkeypatch.setattr(
        indexing,
        "embed_texts",
        lambda chunks: [
            [0.1, 0.2],
            [0.3, 0.4],
        ],
    )

    def fake_add_chunks(file_id, chunks, embeddings):
        stored_data["file_id"] = file_id
        stored_data["chunks"] = chunks
        stored_data["embeddings"] = embeddings

    monkeypatch.setattr(
        indexing,
        "add_chunks",
        fake_add_chunks,
    )

    result = indexing.index_document(
        file_id=7,
        file_path=file_path,
    )

    assert result == 2
    assert stored_data == {
        "file_id": 7,
        "chunks": ["第一段", "第二段"],
        "embeddings": [
            [0.1, 0.2],
            [0.3, 0.4],
        ],
    }


def test_index_document_rejects_empty_document(
    monkeypatch,
    tmp_path: Path,
):
    file_path = tmp_path / "empty.txt"
    file_path.write_text("", encoding="utf-8")

    monkeypatch.setattr(
        indexing,
        "process_document",
        lambda *args, **kwargs: [],
    )

    with pytest.raises(
        ValueError,
        match="Document contains no extractable text",
    ):
        indexing.index_document(
            file_id=8,
            file_path=file_path,
        )