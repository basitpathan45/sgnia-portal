"""Add privacy-preserving CNIC lookup fields to staff users.

Revision ID: 4fe8b39c120a
Revises: 9c4a71d2e6b0
Create Date: 2026-11-06
"""
from alembic import op
import sqlalchemy as sa


revision = "4fe8b39c120a"
down_revision = "9c4a71d2e6b0"
branch_labels = None
depends_on = None


def upgrade():
    inspector = sa.inspect(op.get_bind())
    columns = {column["name"] for column in inspector.get_columns("user")}
    if "cnic_hash" not in columns:
        op.add_column("user", sa.Column("cnic_hash", sa.String(length=64), nullable=True))
    if "cnic_last4" not in columns:
        op.add_column("user", sa.Column("cnic_last4", sa.String(length=4), nullable=True))

    indexes = {index["name"]: index for index in inspector.get_indexes("user")}
    lookup_index = indexes.get("ix_user_cnic_hash")
    if not lookup_index or not lookup_index["unique"]:
        if lookup_index:
            op.drop_index("ix_user_cnic_hash", table_name="user")
        op.create_index("ix_user_cnic_hash", "user", ["cnic_hash"], unique=True)


def downgrade():
    op.drop_index("ix_user_cnic_hash", table_name="user")
    op.drop_column("user", "cnic_last4")
    op.drop_column("user", "cnic_hash")
