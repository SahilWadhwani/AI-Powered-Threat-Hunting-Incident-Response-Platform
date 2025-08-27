from __future__ import annotations
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import os
import sys
from pathlib import Path

# Make sure 'backend' is on sys.path (when running inside backend/)
sys.path.append(str(Path(__file__).resolve().parents[1]))  # .../backend

# --- NEW: Load the project root .env so pydantic-settings sees it ---
from dotenv import load_dotenv
PROJECT_ROOT = Path(__file__).resolve().parents[2]  # .../sentinelx
load_dotenv(PROJECT_ROOT / ".env")




# Import settings and metadata
from app.core.config import settings
from app.models import get_metadata

# this is the Alembic Config object
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = get_metadata()

def run_migrations_offline():
    url = settings.database_url
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    connectable = engine_from_config(
        {
            "sqlalchemy.url": settings.database_url
        },
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