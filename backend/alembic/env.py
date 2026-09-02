from logging.config import fileConfig
import os
import sys

from sqlalchemy import engine_from_config, pool
from alembic import context

# Put this directory on sys.path so version scripts can `import migration_helpers`.
# Alembic loads each revision by file path, so a sibling module is not otherwise
# importable from them.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Override sqlalchemy.url from environment — same DATABASE_URL the app uses.
_db_url = os.getenv("DATABASE_URL", "postgresql://pob_user:pob_password@postgres:5432/pob_system")
config.set_main_option("sqlalchemy.url", _db_url)

# Import every model module so their tables are registered in Base.metadata.
# These imports are ONLY for autogenerate (target_metadata); running migrations
# (`upgrade`) does not need them — the migrations carry their own DDL. So import
# resiliently: a stale/removed model module must never break `alembic upgrade head`
# on deploy.
import importlib
import logging as _logging

from app.core.database import Base  # noqa: F401

_alembic_log = _logging.getLogger("alembic.env")
_MODEL_MODULES = [
    "benefits_management", "biotime_enhancements", "biotime_models",
    "certification", "custom_attributes", "department",
    "disciplinary_management", "employment_contract", "event", "integrations",
    "leave_management", "onboarding", "overtime_management", "payroll",
    "performance_management", "personnel", "position", "promotion_transfer",
    "report", "resignation", "roles", "shift_management", "system",
    "training_management", "user", "vendor_contractor", "zone",
]
for _m in _MODEL_MODULES:
    try:
        importlib.import_module(f"app.models.{_m}")
    except Exception as _e:  # missing/renamed module — skip, don't block migrations
        _alembic_log.warning("alembic: skipping model app.models.%s (%s)", _m, _e)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
