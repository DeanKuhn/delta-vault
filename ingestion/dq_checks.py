"""Checks the whole batch for duplicates and then individual rows."""

from ingestion.exceptions import DataQualityError

CRM_HEADERS = ["CRM_ID", "ACCOUNT_NUMBER", "CUSTOMER_NAME", "CITY"]
BILLING_HEADERS = ["BILLING_ID", "ACCOUNT_NUMBER", "CUSTOMER_NAME", "CITY", "PLAN"]
BILLING_PLANS = ["BASIC", "PRO"]


def check_not_empty(rows: list[dict], system: str) -> None:
    if not rows:
        raise DataQualityError(f"{system}: Rows are empty.")


def check_columns(rows: list[dict], headers: list[str], system: str) -> dict[str, str]:
    headers = headers.copy()
    keys = {}
    for key in rows[0]:
        cleaned_key = key.strip().upper()
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


def check_crm(rows: list[dict]) -> dict[str, str]:
    system = "CRM"
    check_not_empty(rows, system)

    # === Headers & key creation ===
    headers = CRM_HEADERS
    keys = check_columns(rows, headers, system)

    # === Duplicate ids ===
    problems = []
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


def check_billing(rows: list[dict]) -> dict[str, str]:
    system = "BILLING"
    check_not_empty(rows, system)

    # === Headers & key creation ===
    headers = BILLING_HEADERS
    keys = check_columns(rows, headers, system)

    # === Duplicate ids ===
    problems = []
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
