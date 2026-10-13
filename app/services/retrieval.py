from app.services.embeddings import embed_texts
from app.services.vector_store import search_chunks


def retrieve_chunks(
    question: str,
    limit: int = 3,
) -> list[dict]:
    question = question.strip()

    if not question:
        raise ValueError("Question must not be empty")

    query_embedding = embed_texts([question])[0]

    return search_chunks(
        query_embedding=query_embedding,
        limit=limit,
    )