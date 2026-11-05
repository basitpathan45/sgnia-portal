"""Add privacy-preserving CNIC lookup fields to staff users.

Revision ID: 4fe8b39c120a
Revises: 9c4a71d2e6b0
Create Date: 2026-11-06
"""
from alembic import op

from app.cnic_schema import downgrade_cnic_schema, ensure_cnic_schema


revision = "4fe8b39c120a"
down_revision = "9c4a71d2e6b0"
branch_labels = None
depends_on = None


def upgrade():
    ensure_cnic_schema()


def downgrade():
    downgrade_cnic_schema()
