import pytest

from app.services import retrieval


def test_retrieve_chunks(monkeypatch):
    monkeypatch.setattr(
        retrieval,
        "embed_texts",
        lambda texts: [[0.1, 0.2]],
    )

    monkeypatch.setattr(
        retrieval,
        "search_chunks",
        lambda query_embedding, limit: [{
            "text": "向量模型是 BGE",
            "file_id": 27,
            "chunk_index": 0,
            "distance": 0.12,
        }],
    )

    result = retrieval.retrieve_chunks(
        "系统使用什么向量模型？",
        limit=3,
    )

    assert result == [{
        "text": "向量模型是 BGE",
        "file_id": 27,
        "chunk_index": 0,
        "distance": 0.12,
    }]


def test_retrieve_chunks_rejects_empty_question(
    monkeypatch,
):
    def fail_if_called(texts):
        raise AssertionError(
            "Embedding should not be called"
        )

    monkeypatch.setattr(
        retrieval,
        "embed_texts",
        fail_if_called,
    )

    with pytest.raises(
        ValueError,
        match="Question must not be empty",
    ):
        retrieval.retrieve_chunks("   ")