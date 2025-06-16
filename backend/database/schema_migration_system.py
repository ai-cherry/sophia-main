"""Dynamic Schema Migration System for Sophia AI Pay Ready Platform.

This module provides the :class:`SchemaMigrationManager` which analyses
incoming data structures and evolves the PostgreSQL schema accordingly.
It tracks migrations via a dedicated ``migrations`` table and supports
rollback if a migration fails. Data quality of incoming payloads can be
scored to give quick feedback about completeness and consistency.

Note: Implementation is simplified for the demo environment.
"""
from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

import psycopg2
from psycopg2 import pool

logger = logging.getLogger(__name__)


@dataclass
class MigrationRecord:
    """Represents a tracked schema migration."""

    name: str
    hash: str
    applied_at: datetime = field(default_factory=datetime.utcnow)


class SchemaMigrationManager:
    """Manage dynamic schema migrations for PostgreSQL."""

    def __init__(
        self,
        dsn: str,
        minconn: int = 1,
        maxconn: int = 5,
    ) -> None:
        self.dsn = dsn
        self.pool = pool.SimpleConnectionPool(minconn, maxconn, dsn)
        self._ensure_migrations_table()
        logger.info("SchemaMigrationManager initialized")

    def _ensure_migrations_table(self) -> None:
        query = (
            "CREATE TABLE IF NOT EXISTS migrations (\n"
            "    id SERIAL PRIMARY KEY,\n"
            "    name TEXT UNIQUE NOT NULL,\n"
            "    hash TEXT NOT NULL,\n"
            "    applied_at TIMESTAMP NOT NULL\n"
            ")"
        )
        with self.pool.getconn() as conn:
            with conn.cursor() as cur:
                cur.execute(query)
            conn.commit()
        self.pool.putconn(conn)
        logger.debug("Migrations table ensured")

    def _calculate_hash(self, definition: Dict[str, Any]) -> str:
        raw = json.dumps(definition, sort_keys=True).encode()
        return hashlib.sha256(raw).hexdigest()

    def _migration_exists(self, name: str, hash_value: str) -> bool:
        query = "SELECT 1 FROM migrations WHERE name=%s AND hash=%s"
        with self.pool.getconn() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (name, hash_value))
                exists = cur.fetchone() is not None
            self.pool.putconn(conn)
        return exists

    def _record_migration(self, record: MigrationRecord) -> None:
        query = "INSERT INTO migrations (name, hash, applied_at) VALUES (%s, %s, %s)"
        with self.pool.getconn() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (record.name, record.hash, record.applied_at))
            conn.commit()
            self.pool.putconn(conn)
        logger.info("Migration recorded: %s", record.name)

    def _rollback(self, queries: List[str]) -> None:
        with self.pool.getconn() as conn:
            with conn.cursor() as cur:
                for q in reversed(queries):
                    try:
                        cur.execute(q)
                    except Exception as exc:  # noqa: BLE001
                        logger.error("Rollback query failed: %s", exc)
                conn.commit()
            self.pool.putconn(conn)
        logger.warning("Rollback completed")

    def infer_column_type(self, sample: Any) -> str:
        """Infer PostgreSQL column type from sample value."""
        if isinstance(sample, int):
            return "INTEGER"
        if isinstance(sample, float):
            return "DECIMAL"
        if isinstance(sample, dict):
            return "JSONB"
        if isinstance(sample, str):
            try:
                datetime.fromisoformat(sample)
                return "TIMESTAMP"
            except ValueError:
                pass
            if len(sample) > 255:
                return "TEXT"
            return "VARCHAR(255)"
        return "TEXT"

    def evolve_table(self, table: str, data: Dict[str, Any]) -> None:
        """Create or update a table based on provided data structure."""
        definition = {k: self.infer_column_type(v) for k, v in data.items()}
        hash_value = self._calculate_hash(definition)
        if self._migration_exists(table, hash_value):
            logger.info("No migration required for %s", table)
            return

        queries: List[str] = []
        with self.pool.getconn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT column_name FROM information_schema.columns WHERE table_name=%s",
                    (table,),
                )
                existing = {r[0] for r in cur.fetchall()}

                if not existing:
                    cols = ", ".join(f"{k} {t}" for k, t in definition.items())
                    create_q = f"CREATE TABLE {table} ({cols})"
                    queries.append(f"DROP TABLE IF EXISTS {table}")
                    cur.execute(create_q)
                else:
                    for col, col_type in definition.items():
                        if col not in existing:
                            alter_q = f"ALTER TABLE {table} ADD COLUMN {col} {col_type}"
                            queries.append(f"ALTER TABLE {table} DROP COLUMN IF EXISTS {col}")
                            cur.execute(alter_q)
            conn.commit()
            self.pool.putconn(conn)

        self._record_migration(MigrationRecord(table, hash_value))
        logger.info("Schema evolved for table %s", table)

    def score_quality(self, data: Dict[str, Any]) -> float:
        """Compute a simple quality score based on completeness."""
        if not data:
            return 0.0
        filled = sum(1 for v in data.values() if v not in (None, ""))
        return filled / len(data)

    def apply_migration(self, table: str, sample_row: Dict[str, Any]) -> None:
        """Public interface to evolve schema with rollback on failure."""
        try:
            self.evolve_table(table, sample_row)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Migration failed for table %s", table)
            self._rollback([])
            raise exc

    def close(self) -> None:
        self.pool.closeall()
        logger.debug("Connection pool closed")
