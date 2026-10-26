"""Bounded CSV parsing and canonical mapping for the first governed bulk workflow."""

import csv
import io
import re

from backend.domain.rules import BusinessError

MAX_UPLOAD_BYTES = 5 * 1024 * 1024
MAX_ROWS = 5_000
MAX_COLUMNS = 20
MAX_CELL_CHARS = 2_000
BRANCH_FIELDS = (
    "external_ref",
    "brand_id",
    "city_id",
    "branch_name",
    "latitude",
    "longitude",
)
BRANCH_HEADERS = set(BRANCH_FIELDS) | {
    "external_reference",
    "external_id",
    "store_id",
    "brand",
    "city",
    "name",
    "lat",
    "lon",
    "lng",
}


def normalize_header(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")


def parse_csv(content: bytes) -> tuple[list[str], list[dict[str, str]]]:
    if not content or len(content) > MAX_UPLOAD_BYTES:
        raise BusinessError("bulk_file_size", "CSV must be between 1 byte and 5 MiB", 413)
    if b"\x00" in content:
        raise BusinessError("bulk_csv_encoding", "CSV contains invalid NUL bytes", 422)
    try:
        text = content.decode("utf-8-sig", errors="strict")
    except UnicodeDecodeError as exc:
        raise BusinessError("bulk_csv_encoding", "CSV must use UTF-8 encoding", 422) from exc
    try:
        reader = csv.DictReader(io.StringIO(text, newline=""), strict=True)
        if not reader.fieldnames:
            raise BusinessError("bulk_csv_headers", "CSV header row is required", 422)
        headers = [normalize_header(value or "") for value in reader.fieldnames]
        if (
            len(headers) > MAX_COLUMNS
            or any(not header for header in headers)
            or len(set(headers)) != len(headers)
        ):
            raise BusinessError("bulk_csv_headers", "CSV headers must be unique and limited", 422)
        if not set(headers) <= BRANCH_HEADERS:
            raise BusinessError(
                "bulk_csv_columns",
                "Branch CSV contains unsupported columns; remove unneeded and personal data",
                422,
            )
        rows = []
        for row_number, row in enumerate(reader, start=2):
            if row_number - 1 > MAX_ROWS:
                raise BusinessError("bulk_row_limit", f"CSV is limited to {MAX_ROWS} rows", 413)
            if None in row:
                raise BusinessError("bulk_csv_shape", f"Row {row_number} has extra columns", 422)
            values = {headers[i]: (value or "").strip() for i, value in enumerate(row.values())}
            if any(len(value) > MAX_CELL_CHARS for value in values.values()):
                raise BusinessError(
                    "bulk_cell_limit", f"Row {row_number} has an oversized cell", 422
                )
            if any("\x00" in value for value in values.values()):
                raise BusinessError(
                    "bulk_csv_shape", f"Row {row_number} contains invalid data", 422
                )
            if any(values.values()):
                rows.append(values)
        return headers, rows
    except csv.Error as exc:
        raise BusinessError("bulk_csv_parse", "CSV structure is invalid", 422) from exc


def apply_mapping(source: dict[str, str], mapping: dict[str, str]) -> dict[str, str]:
    return {target: source.get(mapping.get(target, target), "") for target in BRANCH_FIELDS}


def validate_mapping(mapping: dict[str, str], headers: list[str]) -> dict[str, str]:
    if set(mapping) != set(BRANCH_FIELDS):
        raise BusinessError(
            "bulk_mapping_fields", "Map each required branch field exactly once", 422
        )
    normalized = {target: normalize_header(source) for target, source in mapping.items()}
    if len(set(normalized.values())) != len(normalized) or not set(normalized.values()) <= set(
        headers
    ):
        raise BusinessError(
            "bulk_mapping_source", "Mapping sources must be unique CSV columns", 422
        )
    return normalized
