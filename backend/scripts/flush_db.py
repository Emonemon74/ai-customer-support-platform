#!/usr/bin/env python
"""Delete all application data from the configured local database."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from sqlalchemy import text

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db.base import Base
from app.db.session import engine

# Import models so Base.metadata contains every application table.
from app.models.conversation import Conversation  # noqa: F401
from app.models.document import Document  # noqa: F401
from app.models.message import Message  # noqa: F401
from app.models.refresh_token import RefreshToken  # noqa: F401
from app.models.user import User  # noqa: F401


def flush_database(allow_non_sqlite: bool) -> None:
    dialect = engine.dialect.name
    table_names = [table.name for table in reversed(Base.metadata.sorted_tables)]

    if dialect != "sqlite" and not allow_non_sqlite:
        raise SystemExit(
            "Refusing to flush a non-SQLite database. "
            "Pass --allow-non-sqlite if this is intentional."
        )

    with engine.connect() as connection:
        if dialect == "sqlite":
            connection.execute(text("PRAGMA foreign_keys=OFF"))
            connection.commit()

        with connection.begin():
            for table in reversed(Base.metadata.sorted_tables):
                connection.execute(table.delete())

            if dialect == "sqlite":
                sequence_table_exists = connection.execute(
                    text(
                        "SELECT 1 FROM sqlite_master "
                        "WHERE type = 'table' AND name = 'sqlite_sequence'"
                    )
                ).scalar()
                if sequence_table_exists:
                    connection.execute(text("DELETE FROM sqlite_sequence"))

        if dialect == "sqlite":
            connection.execute(text("PRAGMA foreign_keys=ON"))
            connection.commit()

    print(f"Flushed {len(table_names)} tables: {', '.join(table_names)}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Delete all rows from every application database table."
    )
    parser.add_argument(
        "--allow-non-sqlite",
        action="store_true",
        help="Allow flushing a non-SQLite database configured by DATABASE_URL.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    flush_database(allow_non_sqlite=args.allow_non_sqlite)


if __name__ == "__main__":
    main()
