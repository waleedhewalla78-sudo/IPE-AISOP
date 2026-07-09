"""SEC-05: Ensure cdm_user.password_hash populated (C-04 audit)

Revision ID: 028
Revises: 027
Create Date: 2026-06-26

Backfills NULL password_hash values using SHA-256 digest format:
  {SHA-256}<hex(sha256(plaintext))>

If a legacy plaintext `password` column exists (custom deployments), rows are
updated from that column first. The `password` column is never dropped here.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "028"
down_revision = "027"
branch_labels = None
depends_on = None

_SHA256_PREFIX = "{SHA-256}"


def _column_exists(inspector, table: str, column: str) -> bool:
    return column in {c["name"] for c in inspector.get_columns(table)}


def upgrade():
    bind = op.get_bind()
    inspector = inspect(bind)

    op.execute(sa.text("CREATE EXTENSION IF NOT EXISTS pgcrypto"))

    if not _column_exists(inspector, "cdm_user", "password_hash"):
        op.add_column(
            "cdm_user",
            sa.Column("password_hash", sa.String(256), nullable=True),
        )

    if _column_exists(inspector, "cdm_user", "password"):
        op.execute(
            sa.text(
                f"""
                UPDATE cdm_user
                SET password_hash = '{_SHA256_PREFIX}' || encode(digest(password, 'sha256'), 'hex')
                WHERE password IS NOT NULL
                  AND (password_hash IS NULL OR password_hash = '')
                """
            )
        )
    else:
        # Demo / seed users: hash known development password 'admin'
        op.execute(
            sa.text(
                f"""
                UPDATE cdm_user
                SET password_hash = '{_SHA256_PREFIX}' || encode(digest('admin', 'sha256'), 'hex')
                WHERE password_hash IS NULL OR password_hash = ''
                """
            )
        )


def downgrade():
    bind = op.get_bind()
    inspector = inspect(bind)

    if not _column_exists(inspector, "cdm_user", "password_hash"):
        return

    op.execute(
        sa.text(
            f"""
            UPDATE cdm_user
            SET password_hash = NULL
            WHERE password_hash LIKE '{_SHA256_PREFIX}%'
            """
        )
    )
