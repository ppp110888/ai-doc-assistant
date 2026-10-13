from pathlib import Path

from app.services.documents import process_document
from app.services.embeddings import embed_texts
from app.services.vector_store import add_chunks


def index_document(
    file_id: int,
    file_path: Path,
    chunk_size: int = 500,
    overlap: int = 50,
) -> int:
    chunks = process_document(
        file_path,
        chunk_size=chunk_size,
        overlap=overlap,
    )

    if not chunks:
        raise ValueError(
            "Document contains no extractable text"
        )

    embeddings = embed_texts(chunks)

    add_chunks(
        file_id=file_id,
        chunks=chunks,
        embeddings=embeddings,
    )

    return len(chunks)