"""baseline_existing_schema

Revision ID: 0956ddd46c62
Revises: 
Create Date: 2026-09-22 19:33:07.362120

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0956ddd46c62'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "uploaded_files",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("filename", sa.String(), nullable=False),
        sa.Column("content_type", sa.String(), nullable=False),
        sa.Column("size", sa.Integer(), nullable=False),
        sa.Column("saved_path", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_uploaded_files_id"),
        "uploaded_files",
        ["id"],
        unique=False,
    )

    op.create_table(
        "chat_history",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("answer", sa.Text(), nullable=False),
        sa.Column("sources_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_chat_history_id"),
        "chat_history",
        ["id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_chat_history_id"),
        table_name="chat_history",
    )
    op.drop_table("chat_history")

    op.drop_index(
        op.f("ix_uploaded_files_id"),
        table_name="uploaded_files",
    )
    op.drop_table("uploaded_files")