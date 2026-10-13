from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text

from app.database import Base


class UploadedFile(Base):
    __tablename__ = "uploaded_files"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    content_type = Column(String, nullable=False)
    size = Column(Integer, nullable=False)
    saved_path = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    is_indexed = Column(
        Boolean,
        nullable=False,
        default=False,
        server_default="0",
    )
    indexed_at = Column(
        DateTime,
        nullable=True,
    )
    
class ChatHistory(Base):
    __tablename__ = "chat_history"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )
    question = Column(
        Text,
        nullable=False,
    )
    answer = Column(
        Text,
        nullable=False,
    )
    sources_json = Column(
        Text,
        nullable=False,
        default="[]",
    )
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )