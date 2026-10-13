from pathlib import Path
from uuid import uuid4


def save_uploaded_file(
    upload_dir: Path,
    original_filename: str,
    content: bytes,
) -> tuple[str, Path]:
    unique_filename = f"{uuid4().hex}_{original_filename}"
    save_path = upload_dir / unique_filename
    save_path.write_bytes(content)

    return unique_filename, save_path