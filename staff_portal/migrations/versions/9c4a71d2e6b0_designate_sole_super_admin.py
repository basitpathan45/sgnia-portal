"""Designate Owais Pathan as the sole Super Admin.

Revision ID: 9c4a71d2e6b0
Revises: 08a5be3079bc
Create Date: 2026-11-05
"""
from alembic import op
import sqlalchemy as sa
from flask import current_app


revision = "9c4a71d2e6b0"
down_revision = "08a5be3079bc"
branch_labels = None
depends_on = None


def upgrade():
    super_admin_email = current_app.config["SUPER_ADMIN_EMAIL"].strip().lower()
    users = sa.table(
        "user",
        sa.column("email", sa.String()),
        sa.column("role", sa.String()),
        sa.column("active", sa.Boolean()),
    )
    bind = op.get_bind()
    designated_accounts = bind.execute(
        sa.select(sa.func.count())
        .select_from(users)
        .where(sa.func.lower(sa.func.trim(users.c.email)) == super_admin_email)
    ).scalar_one()
    existing_accounts = bind.execute(
        sa.select(sa.func.count()).select_from(users)
    ).scalar_one()
    if existing_accounts == 0:
        return
    if designated_accounts != 1:
        raise RuntimeError(
            "The designated SUPER_ADMIN_EMAIL must match exactly one existing staff account "
            "before the administrator-role migration can run."
        )

    bind.execute(
        sa.update(users)
        .where(
            users.c.role == "super_admin",
            sa.func.lower(sa.func.trim(users.c.email)) != super_admin_email,
        )
        .values(role="admin")
    )
    bind.execute(
        sa.update(users)
        .where(sa.func.lower(sa.func.trim(users.c.email)) == super_admin_email)
        .values(role="super_admin", active=True)
    )


def downgrade():
    raise RuntimeError(
        "This migration changes role ownership and cannot be safely reversed automatically."
    )
