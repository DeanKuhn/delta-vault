"""Checks the whole batch for duplicates and then individual rows."""

from collections.abc import Sequence
from datetime import date

from ingestion.exceptions import DataQualityError

CRM_HEADERS = ["CRM_ID", "ACCOUNT_NUMBER", "CUSTOMER_NAME", "CITY"]
BILLING_HEADERS = ["BILLING_ID", "ACCOUNT_NUMBER", "CUSTOMER_NAME", "CITY", "PLAN"]
PAYMENT_HEADERS = ["PAYMENT_ID", "BILLING_ID", "AMOUNT", "PAID_DATE"]
BILLING_PLANS = ["BASIC", "PRO"]


def check_not_empty(rows: list[dict], system: str) -> None:
    if not rows:
        raise DataQualityError(f"{system}: Rows are empty.")


def check_row_lengths(rows: list[dict], system: str) -> None:
    problems = []
    for i, row in enumerate(rows, start=1):
        if None in row:
            problems.append(f"{system}: Too many fields, row {i}.")
        if None in row.values():
            problems.append(f"{system}: Too few fields, row {i}.")
    if problems:
        raise DataQualityError("\n".join(problems))


def check_columns(
    raw_headers: Sequence[str],
    headers: list[str],
    system: str,
    problems: list,
) -> dict[str, str]:
    headers = headers.copy()
    keys = {}
    for key in raw_headers:
        cleaned_key = key.strip().upper()
        if cleaned_key in keys:
            problems.append(
                f"{system}: Duplicate cleaned column detected: {cleaned_key}."
            )
        if cleaned_key in headers:
            headers.remove(cleaned_key)
            keys[cleaned_key] = key
    if headers:
        raise DataQualityError(f"{system}: Missing columns: {headers}.")
    return keys


def check_no_duplicates(
    rows: list[dict], system: str, keys: dict[str, str], problems: list, name: str
) -> None:
    seen = set()
    for i, row in enumerate(rows, start=1):
        value = row[keys[name]].strip().upper()
        if value in seen:
            problems.append(f"{system}: Duplicate {name}: {value}, row {i}.")
        if value != "":
            seen.add(value)


def check_no_empty(
    rows: list[dict], system: str, keys: dict[str, str], problems: list, name: str
) -> None:
    for i, row in enumerate(rows, start=1):
        value = row[keys[name]].strip().upper()
        if value == "":
            problems.append(f"{system}: Empty {name}, row {i}.")


def raise_problems(problems: list[str], system: str) -> None:
    multi = "problems"
    if len(problems) == 1:
        multi = "problem"
    raise DataQualityError(
        f"{system} batch encountered {len(problems)} {multi}:\n"
        + "\n".join(f"{i}. {p}" for i, p in enumerate(problems, start=1))
    )


def check_crm(raw_headers: Sequence[str], rows: list[dict]) -> dict[str, str]:
    system = "CRM"
    problems = []

    # === Check empty & row lengths ===
    check_not_empty(rows, system)
    check_row_lengths(rows, system)

    # === Headers & key creation ===
    headers = CRM_HEADERS
    keys = check_columns(raw_headers, headers, system, problems)

    # === Duplicate ids ===
    check_no_duplicates(rows, system, keys, problems, "CRM_ID")
    check_no_duplicates(rows, system, keys, problems, "ACCOUNT_NUMBER")

    # === Empty values ==
    check_no_empty(rows, system, keys, problems, "CRM_ID")

    if problems:
        raise_problems(problems, system)
    return keys


def check_billing(
    raw_headers: Sequence[str], rows: list[dict]
) -> tuple[dict[str, str], set[str]]:
    system = "BILLING"
    problems = []

    # === Check empty & row lengths ===
    check_not_empty(rows, system)
    check_row_lengths(rows, system)

    # === Headers & key creation ===
    headers = BILLING_HEADERS
    keys = check_columns(raw_headers, headers, system, problems)

    # === Duplicate ids ===
    check_no_duplicates(rows, system, keys, problems, "BILLING_ID")
    check_no_duplicates(rows, system, keys, problems, "ACCOUNT_NUMBER")

    # === Empty values ==
    check_no_empty(rows, system, keys, problems, "BILLING_ID")

    # === Validate plans (billing only) ===
    for i, row in enumerate(rows, start=1):
        value = row[keys["PLAN"]].strip().upper()
        if value not in BILLING_PLANS:
            problems.append(
                f"{system}: Plan value {value}, row {i}, doesn't match known options."
            )

    # === Get list of cleaned billing_id rows for payments ===
    reference_billing_ids = set()
    for row in rows:
        value = row[keys["BILLING_ID"]].strip().upper()
        reference_billing_ids.add(value)

    if problems:
        raise_problems(problems, system)
    return keys, reference_billing_ids


def check_payments(
    raw_headers: Sequence[str], rows: list[dict], reference_billing_ids: set[str]
) -> dict[str, str]:
    system = "PAYMENTS"
    problems = []

    # === Check empty & row lengths ===
    check_not_empty(rows, system)
    check_row_lengths(rows, system)

    # === Headers & key creation ===
    headers = PAYMENT_HEADERS
    keys = check_columns(raw_headers, headers, system, problems)

    # === Duplicate ids ===
    check_no_duplicates(rows, system, keys, problems, "PAYMENT_ID")

    # === Empty values ==
    check_no_empty(rows, system, keys, problems, "PAYMENT_ID")
    check_no_empty(rows, system, keys, problems, "BILLING_ID")
    check_no_empty(rows, system, keys, problems, "AMOUNT")
    check_no_empty(rows, system, keys, problems, "PAID_DATE")

    # === Custom payments checks ===
    for i, row in enumerate(rows, start=1):
        amount_value = row[keys["AMOUNT"]].strip()
        date_value = row[keys["PAID_DATE"]].strip()
        billing_id = row[keys["BILLING_ID"]].strip().upper()

        if amount_value != "":
            try:
                amount_float = float(amount_value)
                if amount_float <= 0:
                    problems.append(
                        f"{system}: Amount value {amount_value} is <= 0, row {i}."
                    )
            except ValueError:
                problems.append(
                    f"{system}: Amount value {amount_value} failed to parse into float, "
                    f"row {i}."
                )

        if date_value != "":
            try:
                date.fromisoformat(date_value)
            except ValueError:
                problems.append(
                    f"{system}: Date value {date_value} failed to parse into date format, "
                    f"row {i}."
                )

        if billing_id != "" and billing_id not in reference_billing_ids:
            problems.append(
                f"{system}: Billing_id value {billing_id} not found in billing "
                f"reference ids, row {i}."
            )

    if problems:
        raise_problems(problems, system)
    return keys
