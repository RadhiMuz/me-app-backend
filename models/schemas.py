from typing import Optional, List, Any
from pydantic import BaseModel
from datetime import datetime


# ── Field schema (one entry per column) ─────────────────────────────────────

class FieldSchema(BaseModel):
    key: str
    label: str
    type: str                        # text | number | email | date | enum | textarea
    subtype: Optional[str] = None    # key (primary key marker)
    options: Optional[List[str]] = None   # for enum fields
    required: bool = False


# ── App ──────────────────────────────────────────────────────────────────────

class AppCreate(BaseModel):
    name: str
    description: Optional[str] = None

class AppUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    schema_fields: Optional[List[FieldSchema]] = None

class AppResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    schema_fields: List[FieldSchema]
    created_at: datetime
    updated_at: datetime


# ── Schema parse ─────────────────────────────────────────────────────────────

class SchemaParseResponse(BaseModel):
    schema_fields: List[FieldSchema]
    preview: List[dict]              # first 5 rows as dicts


# ── Records ──────────────────────────────────────────────────────────────────

class RecordCreate(BaseModel):
    data: dict[str, Any]

class RecordUpdate(BaseModel):
    data: dict[str, Any]

class RecordResponse(BaseModel):
    id: int
    app_id: int
    data: dict[str, Any]
    created_at: datetime
    updated_at: datetime

class RecordListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[RecordResponse]
