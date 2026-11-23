"""Load batch into Snowflake, replacing and inserting in one transaction."""

import argparse
from datetime import datetime, UTC
import re

from pathlib import Path

from ingestion.connection import get_connection
from ingestion.source import read_pages
from ingestion.exceptions import DataQualityError
from ingestion.dq_checks import check_billing, check_crm

BATCHNAME_CHECK = r"batch_(\d+)"

def get_id(batch_path: Path) -> int:
    batch_name = batch_path.name
    if batch_name == "bad_batch":
        return -1
    m = re.fullmatch(BATCHNAME_CHECK, batch_name)
    if not m:
        raise ValueError(
            f"Batch name '{batch_name}' doesn't match expected format."
        )
    return int(m.group(1))


def read_all(batch_path: Path, file: str) -> list[dict]:
    batch = [] 
    for page in read_pages(batch_path / file, 2):
        batch.extend(page)
    return batch


def get_loaded_at(cur, batch_id: int) -> datetime:
    cur.execute("""
        SELECT _LOADED_AT FROM CRM_CUSTOMERS WHERE BATCH_ID = %s LIMIT 1
    """, (batch_id,))
    row = cur.fetchone()
    if row is None:
        return datetime.now(UTC)
    return row[0]


def delete_rows(cur, table: str, batch_id: int) -> None:
    cur.execute(
        f"DELETE FROM {table} WHERE BATCH_ID = %s",
        (batch_id,),
    )
    print(f"Deleted {cur.rowcount} rows from {table}.")


def insert_rows(
    cur, 
    table: str, 
    batch: list[dict], 
    keys: dict[str, str], 
    batch_id: int, 
    loaded_at: datetime
) -> None:
    values = []
    for row in batch:
        value = [batch_id, loaded_at]
        for raw_name in keys.values():
            value.append(row[raw_name])
        values.append(tuple(value))

    columns = ", ".join(keys)
    marks = ", ".join(["%s"] * len(keys))
    cur.executemany(
        f"INSERT INTO {table} (BATCH_ID, _LOADED_AT, {columns}) "
        f"VALUES (%s, %s, {marks})",
        values,
    )
    print(f"Inserted {cur.rowcount} rows into {table}.")


def load() -> None:
    # === Function arguments ===
    parser = argparse.ArgumentParser(description="Input batch folder location.")
    parser.add_argument(
        "batch",
        help="Batch folder location from current directory, e.g. 'data/batch_1'.",
        type=Path,
    )
    args = parser.parse_args()

    # === Obtain batch ID ===
    batch_id = get_id(args.batch)

    # === Generate pages and save batches and header keys ===
    crm_batch = read_all(args.batch, "crm_customers.csv")
    crm_keys = check_crm(crm_batch)
    billing_batch = read_all(args.batch, "billing_customers.csv")
    billing_keys = check_billing(billing_batch)

    # === Run deletions and insertions in one transaction ===
    conn = get_connection(
        warehouse="DELTA_VAULT_WH", database="DELTA_VAULT", schema="RAW"
    )
    try:
        cur = conn.cursor()
        loaded_at = get_loaded_at(cur, batch_id)
        delete_rows(cur, "CRM_CUSTOMERS", batch_id)
        delete_rows(cur, "BILLING_CUSTOMERS", batch_id)
        insert_rows(
            cur, 
            "CRM_CUSTOMERS", 
            crm_batch, 
            crm_keys, 
            batch_id, 
            loaded_at
        )
        insert_rows(
            cur, 
            "BILLING_CUSTOMERS", 
            billing_batch, 
            billing_keys, 
            batch_id, 
            loaded_at
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    load()
