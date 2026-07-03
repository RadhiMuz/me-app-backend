import json
from datetime import datetime
from typing import Optional, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from db.database import get_session
from models.db_models import App, Record
from models.schemas import (
    RecordCreate, RecordUpdate, RecordResponse, RecordListResponse, FieldSchema
)
from services.schema_parser import validate_record

router = APIRouter()


def _to_response(record: Record) -> RecordResponse:
    return RecordResponse(
        id=record.id,
        app_id=record.app_id,
        data=json.loads(record.data_json),
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


def _get_app_fields(app_id: int, session: Session) -> list[FieldSchema]:
    app = session.get(App, app_id)
    if not app:
        raise HTTPException(status_code=404, detail="App not found")
    return [FieldSchema(**f) for f in json.loads(app.schema_json)]


@router.get("/", response_model=RecordListResponse)
def list_records(
    app_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    filter_field: Optional[str] = None,
    filter_value: Optional[str] = None,
    session: Session = Depends(get_session),
):
    """List records with optional field filtering and pagination."""
    _get_app_fields(app_id, session)   # validates app exists

    all_records = session.exec(
        select(Record).where(Record.app_id == app_id)
    ).all()

    # Simple field-level filter
    if filter_field and filter_value is not None:
        all_records = [
            r for r in all_records
            if str(json.loads(r.data_json).get(filter_field, "")).lower()
            == filter_value.lower()
        ]

    total = len(all_records)
    start = (page - 1) * page_size
    page_records = all_records[start: start + page_size]

    return RecordListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[_to_response(r) for r in page_records],
    )


@router.post("/", response_model=RecordResponse, status_code=201)
def create_record(
    app_id: int,
    payload: RecordCreate,
    session: Session = Depends(get_session),
):
    # Verify app exists
    app = session.get(App, app_id)
    if not app:
        raise HTTPException(status_code=404, detail="App not found")

    record = Record(app_id=app_id, data_json=json.dumps(payload.data))
    session.add(record)
    session.commit()
    session.refresh(record)
    return _to_response(record)


@router.get("/{record_id}", response_model=RecordResponse)
def get_record(app_id: int, record_id: int, session: Session = Depends(get_session)):
    record = session.get(Record, record_id)
    if not record or record.app_id != app_id:
        raise HTTPException(status_code=404, detail="Record not found")
    return _to_response(record)


@router.patch("/{record_id}", response_model=RecordResponse)
def update_record(
    app_id: int,
    record_id: int,
    payload: RecordUpdate,
    session: Session = Depends(get_session),
):
    record = session.get(Record, record_id)
    if not record or record.app_id != app_id:
        raise HTTPException(status_code=404, detail="Record not found")

    fields = _get_app_fields(app_id, session)
    existing_data = json.loads(record.data_json)
    merged = {**existing_data, **payload.data}

    errors = validate_record(merged, fields)
    if errors:
        raise HTTPException(status_code=422, detail=errors)

    record.data_json = json.dumps(merged)
    record.updated_at = datetime.utcnow()
    session.add(record)
    session.commit()
    session.refresh(record)
    return _to_response(record)


@router.delete("/{record_id}", status_code=204)
def delete_record(app_id: int, record_id: int, session: Session = Depends(get_session)):
    record = session.get(Record, record_id)
    if not record or record.app_id != app_id:
        raise HTTPException(status_code=404, detail="Record not found")
    session.delete(record)
    session.commit()