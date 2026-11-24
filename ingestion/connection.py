"""Snowflake connection in one place."""

import os
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import snowflake.connector
from dotenv import load_dotenv

load_dotenv()

PRIVATE_KEY_PATH = Path.home() / ".snowflake/rsa_key.p8"


def get_connection(
    warehouse=None, database=None, schema=None
) -> snowflake.connector.SnowflakeConnection:
    conn = snowflake.connector.connect(
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        user=os.getenv("SNOWFLAKE_USER"),
        authenticator="SNOWFLAKE_JWT",
        private_key_file=PRIVATE_KEY_PATH,
        warehouse=warehouse,
        database=database,
        schema=schema,
        role="SYSADMIN",
        autocommit=False,
        enable_server_session_keep_alive_auto_detection=False,
    )
    return conn


@contextmanager
def transaction(
    warehouse=None, database=None, schema=None
) -> Iterator[snowflake.connector.SnowflakeConnection]:
    conn = get_connection(warehouse, database, schema)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
