"""Set up warehouse, database, and schema layout for Snowflake."""

from ingestion.connection import get_connection


def schema():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE WAREHOUSE IF NOT EXISTS DELTA_VAULT_WH
            WAREHOUSE_SIZE = 'XSMALL'
            AUTO_SUSPEND = 60
            AUTO_RESUME = TRUE
            INITIALLY_SUSPENDED = TRUE
        """)
    cur.execute("CREATE DATABASE IF NOT EXISTS DELTA_VAULT")
    cur.execute("CREATE SCHEMA IF NOT EXISTS DELTA_VAULT.RAW")
    cur.execute("CREATE SCHEMA IF NOT EXISTS DELTA_VAULT.STAGING")
    cur.execute("CREATE SCHEMA IF NOT EXISTS DELTA_VAULT.RAW_VAULT")
    cur.execute("CREATE SCHEMA IF NOT EXISTS DELTA_VAULT.BUSINESS_VAULT")
    cur.execute("CREATE SCHEMA IF NOT EXISTS DELTA_VAULT.MARTS")
    conn.close()


if __name__ == "__main__":
    schema()
