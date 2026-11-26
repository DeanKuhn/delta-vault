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
    cur.execute("""
        CREATE TABLE IF NOT EXISTS DELTA_VAULT.RAW.CRM_CUSTOMERS (
            BATCH_ID INTEGER NOT NULL,
            _LOADED_AT TIMESTAMP_TZ NOT NULL,
            CRM_ID VARCHAR NOT NULL,
            ACCOUNT_NUMBER VARCHAR,
            CUSTOMER_NAME VARCHAR,
            CITY VARCHAR
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS DELTA_VAULT.RAW.BILLING_CUSTOMERS (
            BATCH_ID INTEGER NOT NULL,
            _LOADED_AT TIMESTAMP_TZ NOT NULL,
            BILLING_ID VARCHAR NOT NULL,
            ACCOUNT_NUMBER VARCHAR,
            CUSTOMER_NAME VARCHAR,
            CITY VARCHAR,
            PLAN VARCHAR
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS DELTA_VAULT.RAW.PAYMENTS (
            BATCH_ID INTEGER NOT NULL,
            _LOADED_AT TIMESTAMP_TZ NOT NULL,
            PAYMENT_ID VARCHAR NOT NULL,
            BILLING_ID VARCHAR NOT NULL,
            AMOUNT VARCHAR NOT NULL,
            PAID_DATE VARCHAR NOT NULL
        )
    """)
    conn.close()


if __name__ == "__main__":
    schema()
