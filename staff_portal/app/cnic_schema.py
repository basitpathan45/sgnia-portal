import sqlalchemy as sa
from alembic import op


USER_VIEW_COLUMNS = (
    "id",
    "name",
    "email",
    "password_hash",
    "role",
    "department",
    "active",
    "created_at",
    "cnic_hash",
    "cnic_last4",
)


def _add_cnic_columns(table_name, schema):
    inspector = sa.inspect(op.get_bind())
    columns = {
        column["name"]
        for column in inspector.get_columns(table_name, schema=schema)
    }
    if "cnic_hash" not in columns:
        op.add_column(
            table_name,
            sa.Column("cnic_hash", sa.String(length=64), nullable=True),
            schema=schema,
        )
    if "cnic_last4" not in columns:
        op.add_column(
            table_name,
            sa.Column("cnic_last4", sa.String(length=4), nullable=True),
            schema=schema,
        )

    indexes = inspector.get_indexes(table_name, schema=schema)
    lookup_index = next(
        (index for index in indexes if index["name"] == "ix_user_cnic_hash"),
        None,
    )
    if not lookup_index or not lookup_index["unique"]:
        if lookup_index:
            op.drop_index(
                "ix_user_cnic_hash",
                table_name=table_name,
                schema=schema,
            )
        op.create_index(
            "ix_user_cnic_hash",
            table_name,
            ["cnic_hash"],
            unique=True,
            schema=schema,
        )


def _replace_user_view(schema):
    bind = op.get_bind()
    preparer = bind.dialect.identifier_preparer
    view_name = preparer.quote("user")
    source_name = preparer.quote("users")
    if schema:
        view_name = f"{preparer.quote_schema(schema)}.{view_name}"
        source_name = f"{preparer.quote_schema(schema)}.{source_name}"
    columns = ", ".join(preparer.quote(column) for column in USER_VIEW_COLUMNS)
    create_view = f"CREATE VIEW {view_name} AS SELECT {columns} FROM {source_name}"
    if bind.dialect.name == "sqlite":
        op.execute(f"DROP VIEW IF EXISTS {view_name}")
        op.execute(create_view)
    else:
        op.execute(create_view.replace("CREATE VIEW", "CREATE OR REPLACE VIEW", 1))


def ensure_cnic_schema():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    schema = "public" if bind.dialect.name == "postgresql" else None
    view_names = inspector.get_view_names(schema=schema)

    if "user" in view_names:
        if not inspector.has_table("users", schema=schema):
            raise RuntimeError(
                "The public.user view exists, but its public.users source table was not found."
            )
        _add_cnic_columns("users", schema)
        _replace_user_view(schema)
        return

    if not inspector.has_table("user", schema=schema):
        raise RuntimeError("The user table or view was not found for the CNIC migration.")
    _add_cnic_columns("user", schema)


def downgrade_cnic_schema():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    schema = "public" if bind.dialect.name == "postgresql" else None
    if "user" in inspector.get_view_names(schema=schema):
        raise RuntimeError(
            "CNIC schema changes on the public.user view cannot be safely reversed."
        )

    table_name = "user"
    columns = {
        column["name"]
        for column in inspector.get_columns(table_name, schema=schema)
    }
    indexes = {index["name"] for index in inspector.get_indexes(table_name, schema=schema)}
    if "ix_user_cnic_hash" in indexes:
        op.drop_index("ix_user_cnic_hash", table_name=table_name, schema=schema)
    if "cnic_last4" in columns:
        op.drop_column(table_name, "cnic_last4", schema=schema)
    if "cnic_hash" in columns:
        op.drop_column(table_name, "cnic_hash", schema=schema)
