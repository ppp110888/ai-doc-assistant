from functools import lru_cache
from pathlib import Path

import chromadb


BASE_DIR = Path(__file__).resolve().parent.parent.parent
CHROMA_DIR = BASE_DIR / "chroma_db"
COLLECTION_NAME = "document_chunks"


@lru_cache
def get_collection():
    client = chromadb.PersistentClient(
        path=str(CHROMA_DIR),
    )

    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def add_chunks(
    file_id: int,
    chunks: list[str],
    embeddings: list[list[float]],
) -> None:
    if len(chunks) != len(embeddings):
        raise ValueError(
            "chunks and embeddings must have the same length"
        )

    if not chunks:
        return

    ids = [
        f"{file_id}:{index}"
        for index in range(len(chunks))
    ]

    metadatas = [
        {
            "file_id": file_id,
            "chunk_index": index,
        }
        for index in range(len(chunks))
    ]

    get_collection().upsert(
        ids=ids,
        documents=chunks,
        embeddings=embeddings,
        metadatas=metadatas,
    )


def search_chunks(
    query_embedding: list[float],
    limit: int = 3,
) -> list[dict]:
    if limit <= 0:
        raise ValueError("limit must be greater than 0")

    result = get_collection().query(
        query_embeddings=[query_embedding],
        n_results=limit,
        include=["documents", "metadatas", "distances"],
    )

    documents = result["documents"][0]
    metadatas = result["metadatas"][0]
    distances = result["distances"][0]

    return [
        {
            "text": document,
            "file_id": metadata["file_id"],
            "chunk_index": metadata["chunk_index"],
            "distance": distance,
        }
        for document, metadata, distance in zip(
            documents,
            metadatas,
            distances,
        )
    ]