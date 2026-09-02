"""
Idempotent wrappers around the Alembic operations used by this project.

The deployment path (docker/db-init.sh) runs `alembic upgrade head` over BOTH a
brand-new database and a legacy one built by the old complete_schema.sql dump.
The legacy database already contains some of what the early revisions add, so a
bare op.add_column() aborts the whole upgrade on DuplicateColumn.

Each helper checks the catalog first and skips work that is already done, so the
same chain converges from either starting point.
"""
from alembic import op
import sqlalchemy as sa


def _scalar(sql: str, **params):
    return op.get_bind().execute(sa.text(sql), params).scalar()


def table_exists(table: str) -> bool:
    return _scalar("SELECT to_regclass(:q)", q=f"public.{table}") is not None


def column_exists(table: str, column: str) -> bool:
    return bool(_scalar(
        "SELECT 1 FROM information_schema.columns "
        "WHERE table_schema='public' AND table_name=:t AND column_name=:c",
        t=table, c=column))


def index_exists(name: str) -> bool:
    return bool(_scalar(
        "SELECT 1 FROM pg_indexes WHERE schemaname='public' AND indexname=:n",
        n=name))


def constraint_exists(table: str, name: str) -> bool:
    return bool(_scalar(
        "SELECT 1 FROM information_schema.table_constraints "
        "WHERE table_schema='public' AND table_name=:t AND constraint_name=:n",
        t=table, n=name))


def add_column(table: str, column: sa.Column) -> None:
    """op.add_column, skipped when the column (or its table) is already there."""
    if not table_exists(table):
        return
    if column_exists(table, column.name):
        return
    op.add_column(table, column)


def create_table(name: str, *columns, **kwargs) -> None:
    if table_exists(name):
        return
    op.create_table(name, *columns, **kwargs)


def create_index(name: str, table: str, columns, **kwargs) -> None:
    if not table_exists(table) or index_exists(name):
        return
    op.create_index(name, table, columns, **kwargs)


def create_unique_constraint(name: str, table: str, columns, **kwargs) -> None:
    if not table_exists(table) or constraint_exists(table, name):
        return
    op.create_unique_constraint(name, table, columns, **kwargs)


def create_foreign_key(name: str, source: str, referent: str, local_cols,
                       remote_cols, **kwargs) -> None:
    if not (table_exists(source) and table_exists(referent)):
        return
    if constraint_exists(source, name):
        return
    op.create_foreign_key(name, source, referent, local_cols, remote_cols, **kwargs)
