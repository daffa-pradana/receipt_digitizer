from contextlib import closing

import psycopg2
from psycopg2.extras import execute_values

from app import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS transactions (
    id          SERIAL PRIMARY KEY,
    source_file TEXT,
    merchant    TEXT,
    category    TEXT NOT NULL DEFAULT 'Uncategorised',
    amount      NUMERIC(14,2) NOT NULL,
    raw_text    TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
"""


def get_connection():
    return psycopg2.connect(
        host=config.POSTGRES_HOST,
        port=config.POSTGRES_PORT,
        dbname=config.POSTGRES_DB,
        user=config.POSTGRES_USER,
        password=config.POSTGRES_PASSWORD,
    )


def init_schema() -> None:
    with closing(get_connection()) as conn, conn, conn.cursor() as cur:
        cur.execute(SCHEMA)


def insert_transactions(rows: list[dict]) -> None:
    if not rows:
        return

    values = [
        (
            row.get("source_file"),
            row.get("merchant"),
            row.get("category") or "Uncategorised",
            row["amount"],
            row.get("raw_text"),
        )
        for row in rows
    ]

    with closing(get_connection()) as conn, conn, conn.cursor() as cur:
        execute_values(
            cur,
            """
            INSERT INTO transactions (source_file, merchant, category, amount, raw_text)
            VALUES %s
            """,
            values,
        )


def spending_by_category() -> list[tuple[str, float]]:
    with closing(get_connection()) as conn, conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT category, SUM(amount)
            FROM transactions
            GROUP BY category
            ORDER BY SUM(amount) DESC
            """
        )
        return cur.fetchall()
