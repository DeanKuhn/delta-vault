"""Reads one CSV and yields a page of rows at a time. A generator."""

import csv
import logging
from collections.abc import Iterator
from pathlib import Path

logger = logging.getLogger(__name__)


def read_pages(path: Path, page_length: int) -> Iterator[list[dict]]:
    with open(path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        page: list = []
        for row in reader:
            page.append(row)
            if len(page) == page_length:
                yield page
                page = []
        if page:
            yield page


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    for page in read_pages(Path("data/batch_1/billing_customers.csv"), 2):
        print(page)
