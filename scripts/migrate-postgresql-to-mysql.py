"""Copy an existing TrainFlow PostgreSQL database into an empty MySQL schema.

The script is deliberately non-destructive: it never drops tables, never
deletes source rows and refuses to copy into non-empty target tables.
"""

from __future__ import annotations

import argparse
import os
from collections.abc import Mapping
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import MetaData, Table, create_engine, func, insert, select
from sqlalchemy.engine import Connection

TABLES = (
    "administrators",
    "companies",
    "trainers",
    "training_case_counters",
    "training_catalog_items",
    "company_contacts",
    "trainer_cvs",
    "training_cases",
    "activity_logs",
    "training_needs",
    "training_programs",
    "training_program_days",
    "training_program_items",
    "training_program_item_methods",
    "training_pricings",
    "training_documents",
)


def normalized(value: object) -> object:
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, datetime) and value.tzinfo is not None:
        return value.astimezone(UTC).replace(tzinfo=None)
    if isinstance(value, Mapping):
        return {key: normalized(item) for key, item in value.items()}
    if isinstance(value, list):
        return [normalized(item) for item in value]
    if isinstance(value, tuple):
        return tuple(normalized(item) for item in value)
    if isinstance(value, Decimal):
        return value
    return value


def reflected(connection: Connection, table_name: str) -> Table:
    return Table(table_name, MetaData(), autoload_with=connection)


def count(connection: Connection, table: Table) -> int:
    return int(connection.scalar(select(func.count()).select_from(table)) or 0)


def rows(connection: Connection, table: Table) -> list[dict[str, object]]:
    statement = select(table)
    if table.name == "training_program_items":
        statement = statement.order_by(table.c.parent_id.is_not(None), table.c.position)
    return [
        {key: normalized(value) for key, value in row.items()}
        for row in connection.execute(statement).mappings()
    ]


def urls() -> tuple[str, str]:
    source = os.getenv("SOURCE_POSTGRES_DATABASE_URL", "").strip()
    target = os.getenv("TARGET_MYSQL_DATABASE_URL", "").strip()
    if not source or not target:
        raise SystemExit(
            "Define SOURCE_POSTGRES_DATABASE_URL and TARGET_MYSQL_DATABASE_URL before running."
        )
    if not source.startswith("postgresql") or not target.startswith("mysql"):
        raise SystemExit("Source must be PostgreSQL and target must be MySQL.")
    return source, target


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify-only", action="store_true")
    arguments = parser.parse_args()
    source_url, target_url = urls()
    source_engine = create_engine(source_url, pool_pre_ping=True)
    target_engine = create_engine(target_url, pool_pre_ping=True)

    with source_engine.connect() as source, target_engine.begin() as target:
        for table_name in TABLES:
            source_table = reflected(source, table_name)
            target_table = reflected(target, table_name)
            source_count = count(source, source_table)
            target_count = count(target, target_table)
            if arguments.verify_only:
                state = "OK" if source_count == target_count else "MISMATCH"
                print(f"{table_name}: source={source_count} target={target_count} {state}")
                continue
            if target_count:
                raise SystemExit(
                    f"Target table {table_name} is not empty ({target_count} rows); copy aborted."
                )
            payload = rows(source, source_table)
            if payload:
                target.execute(insert(target_table), payload)
            copied = count(target, target_table)
            if copied != source_count:
                raise RuntimeError(
                    f"Count mismatch for {table_name}: source={source_count}, target={copied}."
                )
            print(f"{table_name}: copied {copied} rows")


if __name__ == "__main__":
    main()
