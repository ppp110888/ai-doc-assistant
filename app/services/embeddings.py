from functools import lru_cache

from fastembed import TextEmbedding


MODEL_NAME = "BAAI/bge-small-zh-v1.5"


@lru_cache
def get_embedding_model() -> TextEmbedding:
    return TextEmbedding(model_name=MODEL_NAME)


def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []

    model = get_embedding_model()
    embeddings = model.embed(texts)

    return [
        embedding.tolist()
        for embedding in embeddings
    ]