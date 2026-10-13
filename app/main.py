import logging
import json
from pathlib import Path
from datetime import datetime


from fastapi import (
    Depends,
    FastAPI,
    File,
    HTTPException,
    Query,
    UploadFile,
)
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import Base, engine, get_db
from app.models import ChatHistory, UploadedFile
from app.services.files import save_uploaded_file
from app.services.llm import ask_deepseek
from app.services.indexing import index_document
from app.services.retrieval import retrieve_chunks
from app.services.rag import answer_question
from app.services.sources import add_source_filenames

app = FastAPI(
    title="AI Doc Assistant",
    description="A learning project for building an AI document assistant.",
    version="0.1.0",
)

Base.metadata.create_all(bind=engine)

BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)
ALLOWED_EXTENSIONS = {".txt", ".pdf", ".docx"}
MAX_FILE_SIZE = 5 * 1024 * 1024

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
class ChatRequest(BaseModel):
    question: str

class SearchRequest(BaseModel):
    question: str
    limit: int = Field(
        default=3,
        ge=1,
        le=10,
    )

@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> dict[str, str | int]:
    extension = Path(file.filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Only .txt, .pdf, and .docx files are allowed",
        )

    content = await file.read()

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="File size must not exceed 5 MB",
        )

    logger.info(
        "Uploading file: filename=%s, size=%s, content_type=%s",
        file.filename,
        len(content),
        file.content_type,
    )

    unique_filename, save_path = save_uploaded_file(
        upload_dir=UPLOAD_DIR,
        original_filename=file.filename,
        content=content,
    )

    uploaded_file = UploadedFile(
        filename=file.filename,
        content_type=file.content_type or "unknown",
        size=len(content),
        saved_path=str(save_path),
    )

    db.add(uploaded_file)
    db.commit()
    db.refresh(uploaded_file)

    return {
        "id": uploaded_file.id,
        "filename": uploaded_file.filename,
        "content_type": uploaded_file.content_type,
        "size": uploaded_file.size,
        "saved_path": uploaded_file.saved_path,
    }

@app.get("/files")
def list_files(db: Session = Depends(get_db)) -> list[dict]:
    files = (
        db.query(UploadedFile)
        .order_by(UploadedFile.created_at.desc())
        .all()
    )

    return [
        {
            "id": file.id,
            "filename": file.filename,
            "content_type": file.content_type,
            "size": file.size,
            "saved_path": file.saved_path,
            "created_at": file.created_at.isoformat(),
            "is_indexed": file.is_indexed,
            "indexed_at": (
                file.indexed_at.isoformat()
                if file.indexed_at
                else None
            ),
        }
        for file in files
    ]

@app.get("/files/{file_id}")
def get_file(file_id: int, db: Session = Depends(get_db)) -> dict:
    file = (
        db.query(UploadedFile)
        .filter(UploadedFile.id == file_id)
        .first()
    )

    if file is None:
        raise HTTPException(
            status_code=404,
            detail="File record not found",
        )

    return {
        "id": file.id,
        "filename": file.filename,
        "content_type": file.content_type,
        "size": file.size,
        "saved_path": file.saved_path,
        "created_at": file.created_at.isoformat(),
        "is_indexed": file.is_indexed,
        "indexed_at": (
            file.indexed_at.isoformat()
            if file.indexed_at
            else None
        ),
    }

@app.post("/files/{file_id}/index")
def index_file(
    file_id: int,
    db: Session = Depends(get_db),
) -> dict:
    uploaded_file = (
        db.query(UploadedFile)
        .filter(UploadedFile.id == file_id)
        .first()
    )

    if uploaded_file is None:
        raise HTTPException(
            status_code=404,
            detail="File record not found",
        )

    if uploaded_file.is_indexed:
        raise HTTPException(
            status_code=409,
            detail="File is already indexed",
        )
        
    try:
        chunk_count = index_document(
            file_id=uploaded_file.id,
            file_path=Path(uploaded_file.saved_path),
        )
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail="Stored file not found",
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.exception(
            "Document indexing failed: file_id=%s",
            file_id,
        )
        raise HTTPException(
            status_code=500,
            detail="Document indexing failed",
        ) from exc

    uploaded_file.is_indexed = True
    uploaded_file.indexed_at = datetime.utcnow()

    try:
        db.commit()
        db.refresh(uploaded_file)
    except Exception as exc:
        db.rollback()
        logger.exception(
            "Saving index status failed: file_id=%s",
            file_id,
        )
        raise HTTPException(
            status_code=500,
            detail="Saving index status failed",
        ) from exc
        
    return {
        "file_id": uploaded_file.id,
        "filename": uploaded_file.filename,
        "chunk_count": chunk_count,
        "status": "indexed",
        "is_indexed": uploaded_file.is_indexed,
        "indexed_at": uploaded_file.indexed_at.isoformat(),
    }

@app.post("/chat")
def chat(request: ChatRequest) -> dict[str, str]:
    if not request.question.strip():
        raise HTTPException(
            status_code=400,
            detail="Question must not be empty",
        )

    try:
        answer = ask_deepseek(request.question)
    except Exception as exc:
        logger.exception("DeepSeek request failed")
        raise HTTPException(
            status_code=502,
            detail="DeepSeek request failed",
        ) from exc

    return {
        "question": request.question,
        "answer": answer,
    }


@app.post("/search")
def search(
    request: SearchRequest,
    db: Session = Depends(get_db),
) -> dict:
    try:
        results = retrieve_chunks(
            question=request.question,
            limit=request.limit,
        )

        results = add_source_filenames(
            results,
            db,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.exception("Document search failed")
        raise HTTPException(
            status_code=500,
            detail="Document search failed",
        ) from exc

    return {
        "question": request.question,
        "count": len(results),
        "results": results,
    }

@app.post("/ask")
def ask(
    request: SearchRequest,
    db: Session = Depends(get_db),
) -> dict:
    try:
        result = answer_question(
            question=request.question,
            limit=request.limit,
        )

        sources = add_source_filenames(
        result["sources"],
        db,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.exception(
            "Knowledge base question failed"
        )
        raise HTTPException(
            status_code=500,
            detail="Knowledge base question failed",
        ) from exc

    history = ChatHistory(
        question=request.question,
        answer=result["answer"],
        sources_json=json.dumps(
            sources,
            ensure_ascii=False,
        ),
    )

    try:
        db.add(history)
        db.commit()
        db.refresh(history)
    except Exception as exc:
        db.rollback()
        logger.exception(
            "Saving chat history failed"
        )
        raise HTTPException(
            status_code=500,
            detail="Saving chat history failed",
        ) from exc

    return {
        "history_id": history.id,
        "question": request.question,
        "answer": result["answer"],
        "sources": sources,
    }

@app.get("/history")
def list_history(
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
    db: Session = Depends(get_db),
) -> list[dict]:
    records = (
        db.query(ChatHistory)
        .order_by(ChatHistory.created_at.desc())
        .limit(limit)
        .all()
    )

    return [
        {
            "id": record.id,
            "question": record.question,
            "answer": record.answer,
            "sources": json.loads(record.sources_json),
            "created_at": record.created_at.isoformat(),
        }
        for record in records
    ]