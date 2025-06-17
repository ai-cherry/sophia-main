"""Production database configuration for Sophia AI Pay Ready Platform."""
from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Generator
import os

import psycopg2
from psycopg2 import pool
import redis

logger = logging.getLogger(__name__)

POSTGRES_DSN = os.getenv("POSTGRES_URL", "postgresql://localhost:5432/sophia_payready")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")


class DatabaseConfig:
    """Manage PostgreSQL and Redis connections with pooling."""

    def __init__(self) -> None:
        self.pg_pool = pool.SimpleConnectionPool(5, 20, POSTGRES_DSN)
        self.redis = redis.Redis.from_url(REDIS_URL)
        logger.info("DatabaseConfig initialized")

    @contextmanager
    def get_conn(self) -> Generator[psycopg2.extensions.connection, None, None]:
        conn = self.pg_pool.getconn()
        try:
            yield conn
        finally:
            self.pg_pool.putconn(conn)

    def health(self) -> dict[str, bool]:
        return {
            "postgres": self.pg_pool is not None,
            "redis": self.redis.ping(),
        }

    def close(self) -> None:
        self.pg_pool.closeall()
        self.redis.close()
        logger.debug("Database connections closed")
