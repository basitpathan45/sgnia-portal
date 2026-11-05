"""Repair CNIC lookup columns when the user relation is a view.

Revision ID: 7d4a9f13bc21
Revises: 4fe8b39c120a
Create Date: 2026-11-06
"""
from alembic import op

from app.cnic_schema import downgrade_cnic_schema, ensure_cnic_schema


revision = "7d4a9f13bc21"
down_revision = "4fe8b39c120a"
branch_labels = None
depends_on = None


def upgrade():
    ensure_cnic_schema()


def downgrade():
    downgrade_cnic_schema()
