import json
from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from db.database import get_session
from models.db_models import App
from models.schemas import AppCreate, AppUpdate, AppResponse, FieldSchema

router = APIRouter()


def _to_response(app: App) -> AppResponse:
    schema_fields = [FieldSchema(**f) for f in json.loads(app.schema_json)]
    return AppResponse(
        id=app.id,
        name=app.name,
        description=app.description,
        schema_fields=schema_fields,
        created_at=app.created_at,
        updated_at=app.updated_at,
    )


@router.get("/", response_model=List[AppResponse])
def list_apps(session: Session = Depends(get_session)):
    apps = session.exec(select(App)).all()
    return [_to_response(a) for a in apps]


@router.post("/", response_model=AppResponse, status_code=201)
def create_app(payload: AppCreate, session: Session = Depends(get_session)):
    app = App(name=payload.name, description=payload.description, schema_json="[]")
    session.add(app)
    session.commit()
    session.refresh(app)
    return _to_response(app)


@router.get("/{app_id}", response_model=AppResponse)
def get_app(app_id: int, session: Session = Depends(get_session)):
    app = session.get(App, app_id)
    if not app:
        raise HTTPException(status_code=404, detail="App not found")
    return _to_response(app)


@router.patch("/{app_id}", response_model=AppResponse)
def update_app(app_id: int, payload: AppUpdate, session: Session = Depends(get_session)):
    app = session.get(App, app_id)
    if not app:
        raise HTTPException(status_code=404, detail="App not found")

    if payload.name is not None:
        app.name = payload.name
    if payload.description is not None:
        app.description = payload.description
    if payload.schema_fields is not None:
        app.schema_json = json.dumps([f.dict() for f in payload.schema_fields])

    app.updated_at = datetime.utcnow()
    session.add(app)
    session.commit()
    session.refresh(app)
    return _to_response(app)


@router.delete("/{app_id}", status_code=204)
def delete_app(app_id: int, session: Session = Depends(get_session)):
    app = session.get(App, app_id)
    if not app:
        raise HTTPException(status_code=404, detail="App not found")
    session.delete(app)
    session.commit()
