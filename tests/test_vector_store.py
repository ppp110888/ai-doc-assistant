import pytest

from app.services import vector_store


class FakeCollection:
    def __init__(self):
        self.upsert_data = None

    def upsert(self, **kwargs):
        self.upsert_data = kwargs

    def query(self, **kwargs):
        return {
            "documents": [["第一段内容"]],
            "metadatas": [[{
                "file_id": 7,
                "chunk_index": 0,
            }]],
            "distances": [[0.12]],
        }


def test_add_chunks(monkeypatch):
    collection = FakeCollection()

    monkeypatch.setattr(
        vector_store,
        "get_collection",
        lambda: collection,
    )

    vector_store.add_chunks(
        file_id=7,
        chunks=["第一段", "第二段"],
        embeddings=[
            [0.1, 0.2],
            [0.3, 0.4],
        ],
    )

    assert collection.upsert_data["ids"] == [
        "7:0",
        "7:1",
    ]
    assert collection.upsert_data["documents"] == [
        "第一段",
        "第二段",
    ]
    assert collection.upsert_data["metadatas"][0] == {
        "file_id": 7,
        "chunk_index": 0,
    }


def test_add_chunks_rejects_length_mismatch():
    with pytest.raises(ValueError):
        vector_store.add_chunks(
            file_id=7,
            chunks=["第一段"],
            embeddings=[],
        )


def test_search_chunks(monkeypatch):
    collection = FakeCollection()

    monkeypatch.setattr(
        vector_store,
        "get_collection",
        lambda: collection,
    )

    result = vector_store.search_chunks(
        query_embedding=[0.1, 0.2],
        limit=3,
    )

    assert result == [{
        "text": "第一段内容",
        "file_id": 7,
        "chunk_index": 0,
        "distance": 0.12,
    }]