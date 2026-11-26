"""Load batch into Snowflake, replacing and inserting in one transaction."""

import argparse
import re
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path

from ingestion.connection import transaction
from ingestion.dq_checks import check_billing, check_crm, check_payments
from ingestion.source import read_headers, read_pages
from ingestion.timed import timed

BATCHNAME_CHECK = r"batch_(\d+)"


def get_id(batch_path: Path) -> int:
    batch_name = batch_path.name
    if batch_name == "bad_batch":
        return -1
    m = re.fullmatch(BATCHNAME_CHECK, batch_name)
    if not m:
        raise ValueError(f"Batch name '{batch_name}' doesn't match expected format.")
    return int(m.group(1))


def read_all(batch_path: Path, file: str) -> tuple[Sequence[str], list[dict]]:
    headers = read_headers(batch_path / file)
    if not headers:
        raise ValueError(f"No headers returned for {file}.")
    batch = []
    for page in read_pages(batch_path / file, 2):
        batch.extend(page)
    return headers, batch


def get_loaded_at(cur, batch_id: int) -> datetime:
    cur.execute(
        """
        SELECT _LOADED_AT FROM CRM_CUSTOMERS WHERE BATCH_ID = %s LIMIT 1
    """,
        (batch_id,),
    )
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
    loaded_at: datetime,
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


@timed
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
    crm_headers, crm_batch = read_all(args.batch, "crm_customers.csv")
    crm_keys = check_crm(crm_headers, crm_batch)
    billing_headers, billing_batch = read_all(args.batch, "billing_customers.csv")
    billing_keys, reference_billing_ids = check_billing(billing_headers, billing_batch)
    payment_headers, payment_batch = read_all(args.batch, "payments.csv")
    payment_keys = check_payments(payment_headers, payment_batch, reference_billing_ids)

    # === Run deletions and insertions in one transaction ===
    with transaction(        
        warehouse="DELTA_VAULT_WH", database="DELTA_VAULT", schema="RAW"
    ) as conn:
        cur = conn.cursor()
        loaded_at = get_loaded_at(cur, batch_id)
        delete_rows(cur, "CRM_CUSTOMERS", batch_id)
        delete_rows(cur, "BILLING_CUSTOMERS", batch_id)
        delete_rows(cur, "PAYMENTS", batch_id)
        insert_rows(cur, "CRM_CUSTOMERS", crm_batch, crm_keys, batch_id, loaded_at)
        insert_rows(
            cur, "BILLING_CUSTOMERS", billing_batch, billing_keys, batch_id, loaded_at
        )
        insert_rows(cur, "PAYMENTS", payment_batch, payment_keys, batch_id, loaded_at)


if __name__ == "__main__":
    load()
