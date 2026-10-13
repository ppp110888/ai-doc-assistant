import numpy as np

from app.services import embeddings


class FakeEmbeddingModel:
    def embed(self, texts: list[str]):
        for index, _ in enumerate(texts):
            yield np.array(
                [float(index), 0.5, 1.0],
                dtype=np.float32,
            )


def test_embed_texts(monkeypatch):
    fake_model = FakeEmbeddingModel()

    monkeypatch.setattr(
        embeddings,
        "get_embedding_model",
        lambda: fake_model,
    )

    result = embeddings.embed_texts([
        "第一段文本",
        "第二段文本",
    ])

    assert result == [
        [0.0, 0.5, 1.0],
        [1.0, 0.5, 1.0],
    ]


def test_embed_empty_list_does_not_load_model(monkeypatch):
    def fail_if_called():
        raise AssertionError("Model should not be loaded")

    monkeypatch.setattr(
        embeddings,
        "get_embedding_model",
        fail_if_called,
    )

    assert embeddings.embed_texts([]) == []