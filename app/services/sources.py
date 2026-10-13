from sqlalchemy.orm import Session

from app.models import UploadedFile


def add_source_filenames(
    sources: list[dict],
    db: Session,
) -> list[dict]:
    if not sources:
        return []

    file_ids = {
        source["file_id"]
        for source in sources
    }

    files = (
        db.query(UploadedFile)
        .filter(UploadedFile.id.in_(file_ids))
        .all()
    )

    filenames = {
        file.id: file.filename
        for file in files
    }

    return [
        {
            **source,
            "filename": filenames.get(
                source["file_id"],
                "Unknown file",
            ),
        }
        for source in sources
    ]