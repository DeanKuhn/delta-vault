"""Exceptions raised by the ingestion layer."""


class DataQualityError(Exception):
    """A batch failed one or more data quality checks."""
