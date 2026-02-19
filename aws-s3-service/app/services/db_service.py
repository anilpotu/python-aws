"""PostgreSQL CRUD operations for user personal, financial, and health data.

Tables are created automatically on startup if they do not exist:
  - users_personal
  - users_financial
  - users_health

Each table uses user_id (TEXT) as the primary key.
"""

import asyncio
import logging
from typing import Any

import asyncpg

from app.config import settings

logger = logging.getLogger(__name__)

_pool: asyncpg.Pool | None = None

# ---------------------------------------------------------------------------
# Pool lifecycle (called from main.py lifespan)
# ---------------------------------------------------------------------------

_DDL = """
CREATE TABLE IF NOT EXISTS users_personal (
    user_id        TEXT PRIMARY KEY,
    name           TEXT NOT NULL,
    email          TEXT NOT NULL,
    phone          TEXT,
    address        TEXT,
    date_of_birth  DATE,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS users_financial (
    user_id        TEXT PRIMARY KEY,
    account_number TEXT,
    credit_score   INTEGER,
    annual_income  NUMERIC(15, 2),
    total_debt     NUMERIC(15, 2),
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS users_health (
    user_id      TEXT PRIMARY KEY,
    blood_type   TEXT,
    conditions   TEXT[] NOT NULL DEFAULT '{}',
    medications  TEXT[] NOT NULL DEFAULT '{}',
    allergies    TEXT[] NOT NULL DEFAULT '{}',
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
"""


async def init_pool() -> None:
    """Create the connection pool and ensure schema exists."""
    global _pool
    _pool = await asyncpg.create_pool(settings.database_url, min_size=2, max_size=10)
    async with _pool.acquire() as conn:
        await conn.execute(_DDL)
    logger.info("PostgreSQL connection pool created and schema initialised")


async def close_pool() -> None:
    """Gracefully close the connection pool."""
    global _pool
    if _pool:
        await _pool.close()
        _pool = None
        logger.info("PostgreSQL connection pool closed")


def _get_pool() -> asyncpg.Pool:
    if _pool is None:
        raise RuntimeError("Database pool is not initialised")
    return _pool


def _row_to_dict(row: asyncpg.Record | None) -> dict[str, Any] | None:
    """Convert an asyncpg Record to a plain dict."""
    return dict(row) if row is not None else None


# ---------------------------------------------------------------------------
# Personal information
# ---------------------------------------------------------------------------

async def insert_personal(data: dict[str, Any]) -> dict[str, Any]:
    """Insert a new personal-info row. Raises if user_id already exists."""
    pool = _get_pool()
    row = await pool.fetchrow(
        """
        INSERT INTO users_personal (user_id, name, email, phone, address, date_of_birth)
        VALUES ($1, $2, $3, $4, $5, $6)
        RETURNING *
        """,
        data["user_id"],
        data["name"],
        data["email"],
        data.get("phone"),
        data.get("address"),
        data.get("date_of_birth"),
    )
    logger.info("Inserted personal info for user %s", data["user_id"])
    return _row_to_dict(row)


async def get_personal(user_id: str) -> dict[str, Any] | None:
    """Fetch personal info by user_id. Returns None if not found."""
    pool = _get_pool()
    row = await pool.fetchrow(
        "SELECT * FROM users_personal WHERE user_id = $1", user_id
    )
    return _row_to_dict(row)


async def update_personal(user_id: str, data: dict[str, Any]) -> dict[str, Any] | None:
    """Update personal info for a user. Only provided fields are changed."""
    pool = _get_pool()
    row = await pool.fetchrow(
        """
        UPDATE users_personal
        SET
            name          = COALESCE($2, name),
            email         = COALESCE($3, email),
            phone         = COALESCE($4, phone),
            address       = COALESCE($5, address),
            date_of_birth = COALESCE($6, date_of_birth),
            updated_at    = NOW()
        WHERE user_id = $1
        RETURNING *
        """,
        user_id,
        data.get("name"),
        data.get("email"),
        data.get("phone"),
        data.get("address"),
        data.get("date_of_birth"),
    )
    if row:
        logger.info("Updated personal info for user %s", user_id)
    return _row_to_dict(row)


async def delete_personal(user_id: str) -> bool:
    """Delete personal info for a user. Returns True if a row was deleted."""
    pool = _get_pool()
    result = await pool.execute(
        "DELETE FROM users_personal WHERE user_id = $1", user_id
    )
    deleted = result.split()[-1] != "0"
    if deleted:
        logger.info("Deleted personal info for user %s", user_id)
    return deleted


# ---------------------------------------------------------------------------
# Financial information
# ---------------------------------------------------------------------------

async def insert_financial(data: dict[str, Any]) -> dict[str, Any]:
    """Insert a new financial-info row."""
    pool = _get_pool()
    row = await pool.fetchrow(
        """
        INSERT INTO users_financial (user_id, account_number, credit_score, annual_income, total_debt)
        VALUES ($1, $2, $3, $4, $5)
        RETURNING *
        """,
        data["user_id"],
        data.get("account_number"),
        data.get("credit_score"),
        data.get("annual_income"),
        data.get("total_debt"),
    )
    logger.info("Inserted financial info for user %s", data["user_id"])
    return _row_to_dict(row)


async def get_financial(user_id: str) -> dict[str, Any] | None:
    """Fetch financial info by user_id."""
    pool = _get_pool()
    row = await pool.fetchrow(
        "SELECT * FROM users_financial WHERE user_id = $1", user_id
    )
    return _row_to_dict(row)


async def update_financial(user_id: str, data: dict[str, Any]) -> dict[str, Any] | None:
    """Update financial info for a user."""
    pool = _get_pool()
    row = await pool.fetchrow(
        """
        UPDATE users_financial
        SET
            account_number = COALESCE($2, account_number),
            credit_score   = COALESCE($3, credit_score),
            annual_income  = COALESCE($4, annual_income),
            total_debt     = COALESCE($5, total_debt),
            updated_at     = NOW()
        WHERE user_id = $1
        RETURNING *
        """,
        user_id,
        data.get("account_number"),
        data.get("credit_score"),
        data.get("annual_income"),
        data.get("total_debt"),
    )
    if row:
        logger.info("Updated financial info for user %s", user_id)
    return _row_to_dict(row)


async def delete_financial(user_id: str) -> bool:
    """Delete financial info for a user."""
    pool = _get_pool()
    result = await pool.execute(
        "DELETE FROM users_financial WHERE user_id = $1", user_id
    )
    deleted = result.split()[-1] != "0"
    if deleted:
        logger.info("Deleted financial info for user %s", user_id)
    return deleted


# ---------------------------------------------------------------------------
# Health information
# ---------------------------------------------------------------------------

async def insert_health(data: dict[str, Any]) -> dict[str, Any]:
    """Insert a new health-info row."""
    pool = _get_pool()
    row = await pool.fetchrow(
        """
        INSERT INTO users_health (user_id, blood_type, conditions, medications, allergies)
        VALUES ($1, $2, $3, $4, $5)
        RETURNING *
        """,
        data["user_id"],
        data.get("blood_type"),
        data.get("conditions", []),
        data.get("medications", []),
        data.get("allergies", []),
    )
    logger.info("Inserted health info for user %s", data["user_id"])
    return _row_to_dict(row)


async def get_health(user_id: str) -> dict[str, Any] | None:
    """Fetch health info by user_id."""
    pool = _get_pool()
    row = await pool.fetchrow(
        "SELECT * FROM users_health WHERE user_id = $1", user_id
    )
    return _row_to_dict(row)


async def update_health(user_id: str, data: dict[str, Any]) -> dict[str, Any] | None:
    """Update health info for a user."""
    pool = _get_pool()
    row = await pool.fetchrow(
        """
        UPDATE users_health
        SET
            blood_type  = COALESCE($2, blood_type),
            conditions  = COALESCE($3, conditions),
            medications = COALESCE($4, medications),
            allergies   = COALESCE($5, allergies),
            updated_at  = NOW()
        WHERE user_id = $1
        RETURNING *
        """,
        user_id,
        data.get("blood_type"),
        data.get("conditions"),
        data.get("medications"),
        data.get("allergies"),
    )
    if row:
        logger.info("Updated health info for user %s", user_id)
    return _row_to_dict(row)


async def delete_health(user_id: str) -> bool:
    """Delete health info for a user."""
    pool = _get_pool()
    result = await pool.execute(
        "DELETE FROM users_health WHERE user_id = $1", user_id
    )
    deleted = result.split()[-1] != "0"
    if deleted:
        logger.info("Deleted health info for user %s", user_id)
    return deleted


# ---------------------------------------------------------------------------
# Aggregated fetch (used before sending to SQS)
# ---------------------------------------------------------------------------

async def get_user_full(user_id: str) -> dict[str, Any]:
    """Fetch personal, financial, and health records for a user in parallel."""
    personal, financial, health = await asyncio.gather(
        get_personal(user_id),
        get_financial(user_id),
        get_health(user_id),
    )
    return {
        "user_id": user_id,
        "personal": personal,
        "financial": financial,
        "health": health,
    }
