import json
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlmodel import Session
from db.database import get_session
from models.db_models import App
from models.schemas import SchemaParseResponse
from services.schema_parser import parse_csv

router = APIRouter()


@router.post("/parse", response_model=SchemaParseResponse)
async def parse_schema(file: UploadFile = File(...)):
    """Upload a CSV file and get back an auto-detected schema + preview rows."""
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported.")

    content = (await file.read()).decode("utf-8")
    fields, preview = parse_csv(content)

    if not fields:
        raise HTTPException(status_code=422, detail="CSV appears to be empty or malformed.")

    return SchemaParseResponse(schema_fields=fields, preview=preview)


@router.post("/parse-and-attach/{app_id}", response_model=SchemaParseResponse)
async def parse_and_attach(
    app_id: int,
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
):
    """Parse CSV and immediately save the detected schema to an existing app."""
    app = session.get(App, app_id)
    if not app:
        raise HTTPException(status_code=404, detail="App not found")

    content = (await file.read()).decode("utf-8")
    fields, preview = parse_csv(content)

    app.schema_json = json.dumps([f.dict() for f in fields])
    app.updated_at = datetime.utcnow()
    session.add(app)
    session.commit()

    return SchemaParseResponse(schema_fields=fields, preview=preview)
