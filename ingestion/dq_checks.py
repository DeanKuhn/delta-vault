"""Checks the whole batch for duplicates and then individual rows."""

from collections.abc import Sequence

from ingestion.exceptions import DataQualityError

CRM_HEADERS = ["CRM_ID", "ACCOUNT_NUMBER", "CUSTOMER_NAME", "CITY"]
BILLING_HEADERS = ["BILLING_ID", "ACCOUNT_NUMBER", "CUSTOMER_NAME", "CITY", "PLAN"]
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
        multi = "problems"
        if len(problems) == 1:
            multi = "problem"
        raise DataQualityError(
            f"{system} batch encountered {len(problems)} {multi}:\n"
            + "\n".join(f"{i}. {p}" for i, p in enumerate(problems, start=1))
        )
    return keys


def check_billing(raw_headers: Sequence[str], rows: list[dict]) -> dict[str, str]:
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

    if problems:
        multi = "problems"
        if len(problems) == 1:
            multi = "problem"
        raise DataQualityError(
            f"{system} batch encountered {len(problems)} {multi}:\n"
            + "\n".join(f"{i}. {p}" for i, p in enumerate(problems, start=1))
        )
    return keys
