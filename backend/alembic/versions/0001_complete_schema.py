"""complete_schema_baseline

Revision ID: 0001_complete_schema
Revises:
Create Date: 2026-06-06

Complete POB database schema — 232 tables.
This is the single authoritative migration.  On a fresh server:

    alembic upgrade head

Generates the entire database from scratch.  No other scripts are needed.
All CREATE statements use IF NOT EXISTS so the migration is safe to re-run.
"""
from typing import Sequence, Union
from pathlib import Path

from alembic import op
from sqlalchemy import text

revision: str = "0001_complete_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# DDL lives in schema_ddl.sql in the same directory — keeps this file readable
# and lets the SQL be reviewed / diffed independently.
_DDL_FILE = Path(__file__).parent / "schema_ddl.sql"


def _split_statements(sql: str) -> list[str]:
    """
    Yield top-level statements from a DDL script.

    Splitting on ";" alone is not safe here: the file contains dollar-quoted
    DO blocks (the enum guards), single-quoted literals and line comments, all
    of which can hold semicolons that do not end a statement.
    """
    import re

    def _is_only_comments(stmt: str) -> bool:
        """
        True when nothing but line comments remain.

        A plain ``stmt.startswith("--")`` test is wrong: statements in this file
        are routinely preceded by a comment banner, so that test discarded real
        DDL along with the comment. One CREATE TABLE (acc_antipassback), its
        sequence and an enum guard were being dropped silently, which is why a
        fresh `alembic upgrade head` failed on a table that appears in the file.
        """
        rest = stmt
        while True:
            rest = rest.lstrip()
            if not rest:
                return True
            if not rest.startswith("--"):
                return False
            nl = rest.find("\n")
            if nl == -1:
                return True
            rest = rest[nl + 1:]

    statements: list[str] = []
    buf: list[str] = []
    i, n = 0, len(sql)
    dollar_tag = None

    while i < n:
        ch = sql[i]

        if dollar_tag is not None:
            if sql.startswith(dollar_tag, i):
                buf.append(dollar_tag)
                i += len(dollar_tag)
                dollar_tag = None
                continue
            buf.append(ch)
            i += 1
            continue

        # Line comment — copy to end of line.
        if sql.startswith("--", i):
            j = sql.find("\n", i)
            j = n if j == -1 else j + 1
            buf.append(sql[i:j])
            i = j
            continue

        # Single-quoted literal, honouring '' escapes.
        if ch == "'":
            j = i + 1
            while j < n:
                if sql[j] == "'":
                    if j + 1 < n and sql[j + 1] == "'":
                        j += 2
                        continue
                    j += 1
                    break
                j += 1
            buf.append(sql[i:j])
            i = j
            continue

        # Start of a dollar-quoted body.
        m = re.match(r"\$\w*\$", sql[i:])
        if m:
            dollar_tag = m.group(0)
            buf.append(dollar_tag)
            i += len(dollar_tag)
            continue

        if ch == ";":
            stmt = "".join(buf).strip()
            if stmt and not _is_only_comments(stmt):
                statements.append(stmt)
            buf = []
            i += 1
            continue

        buf.append(ch)
        i += 1

    tail = "".join(buf).strip()
    if tail and not _is_only_comments(tail):
        statements.append(tail)
    return statements


def upgrade() -> None:
    conn = op.get_bind()
    raw_sql = _DDL_FILE.read_text()

    # Split on statement boundaries and execute each one individually so a
    # single failure is isolated and the exact failing statement is visible.
    #
    # The split must respect dollar-quoted bodies: the enum guards at the top of
    # the file are DO $$ ... $$ blocks containing their own semicolons, and a
    # naive split on ";" tears them in half.
    for stmt in _split_statements(raw_sql):
        conn.execute(text(stmt))


def downgrade() -> None:
    # Drop all user tables in one shot using CASCADE.
    # alembic_version is preserved so Alembic can track state after downgrade.
    op.execute(text("""
        DO $$ DECLARE r RECORD; BEGIN
            FOR r IN (
                SELECT tablename FROM pg_tables
                WHERE schemaname = 'public'
                  AND tablename <> 'alembic_version'
            ) LOOP
                EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE';
            END LOOP;
        END $$;
    """))
