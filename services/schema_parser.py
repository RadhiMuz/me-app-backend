import csv
import io
import re
from typing import List, Tuple
from models.schemas import FieldSchema


def _infer_type(key: str, values: List[str]) -> dict:
    """Infer a field's type from its column name and sample values."""
    samples = [v for v in values if v.strip()][:20]
    key_lower = key.lower()

    # Primary key
    if key_lower == "id":
        return {"type": "number", "subtype": "key"}

    # Email
    if "email" in key_lower:
        return {"type": "email"}

    # Date
    date_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}")
    if "date" in key_lower or (samples and all(date_pattern.match(v) for v in samples)):
        return {"type": "date"}

    # Number
    if samples and all(_is_number(v) for v in samples):
        return {"type": "number"}

    # Enum — low-cardinality text column
    unique = list(dict.fromkeys(samples))   # preserves order, deduplicates
    if len(unique) <= 6 and len(samples) >= 3:
        return {"type": "enum", "options": unique}

    # Long text
    if samples and any(len(v) > 80 for v in samples):
        return {"type": "textarea"}

    return {"type": "text"}


def _is_number(value: str) -> bool:
    try:
        float(value)
        return True
    except ValueError:
        return False


def parse_csv(content: str) -> Tuple[List[FieldSchema], List[dict]]:
    """
    Parse CSV text into (schema_fields, preview_rows).
    Returns the inferred schema and up to 5 preview rows.
    """
    reader = csv.DictReader(io.StringIO(content))
    rows = list(reader)

    if not rows:
        return [], []

    headers = list(rows[0].keys())
    fields: List[FieldSchema] = []

    for header in headers:
        values = [row.get(header, "") for row in rows]
        inferred = _infer_type(header, values)

        label = header.replace("_", " ").title()
        required = inferred.get("subtype") == "key" or header.lower() == "name"

        fields.append(FieldSchema(
            key=header,
            label=label,
            required=required,
            **inferred,
        ))

    preview = rows[:5]
    return fields, preview


def validate_record(data: dict, fields: List[FieldSchema]) -> List[str]:
    """
    Validate a record dict against the schema.
    Returns a list of error messages (empty = valid).
    """
    errors = []
    field_map = {f.key: f for f in fields}

    for field in fields:
        if field.subtype == "key":
            continue   # auto-assigned, skip validation
        value = data.get(field.key, "")

        if field.required and not str(value).strip():
            errors.append(f"'{field.label}' is required.")
            continue

        if not value and not field.required:
            continue

        if field.type == "number":
            try:
                float(value)
            except (TypeError, ValueError):
                errors.append(f"'{field.label}' must be a number.")

        if field.type == "email":
            if not re.match(r"^[^@]+@[^@]+\.[^@]+$", str(value)):
                errors.append(f"'{field.label}' must be a valid email address.")

        if field.type == "enum" and field.options:
            if str(value) not in field.options:
                errors.append(f"'{field.label}' must be one of: {', '.join(field.options)}.")

    return errors
