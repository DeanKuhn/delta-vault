"""Reads one CSV and yields a page of rows at a time. A generator."""

import csv
from collections.abc import Iterator, Sequence
from pathlib import Path


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


def read_headers(path: Path) -> Sequence[str] | None:
    with open(path, "r", newline="", encoding="utf-8") as f:
        return csv.DictReader(f).fieldnames
