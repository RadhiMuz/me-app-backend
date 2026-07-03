import os
import shutil
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlmodel import Session, select
from db.database import get_session
from models.spare_parts import SparePart, SparePartCreate, SparePartUpdate, SparePartResponse

router = APIRouter()

UPLOAD_DIR = "uploads/spare-parts"
os.makedirs(UPLOAD_DIR, exist_ok=True)


def _status(part: SparePart) -> str:
    if part.available_stock == 0:
        return "critical"
    if part.available_stock <= part.minimum_stock:
        return "low"
    return "ok"


def _to_response(part: SparePart) -> SparePartResponse:
    return SparePartResponse(
        id=part.id,
        product_name=part.product_name,
        product_id=part.product_id,
        available_stock=part.available_stock,
        minimum_stock=part.minimum_stock,
        category=part.category,
        rack=part.rack,
        image_url=part.image_url,
        status=_status(part),
        created_at=part.created_at,
        updated_at=part.updated_at,
    )


@router.get("/", response_model=List[SparePartResponse])
def list_parts(
    category: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    session: Session = Depends(get_session),
):
    parts = session.exec(select(SparePart)).all()

    if category:
        parts = [p for p in parts if p.category.lower() == category.lower()]
    if search:
        parts = [p for p in parts if search.lower() in p.product_name.lower() or search.lower() in p.product_id.lower()]

    responses = [_to_response(p) for p in parts]

    if status:
        responses = [r for r in responses if r.status == status]

    return responses


@router.post("/", response_model=SparePartResponse, status_code=201)
def create_part(part: SparePartCreate, session: Session = Depends(get_session)):
    db_part = SparePart(**part.dict())
    session.add(db_part)
    session.commit()
    session.refresh(db_part)
    return _to_response(db_part)


@router.get("/categories", response_model=List[str])
def list_categories(session: Session = Depends(get_session)):
    parts = session.exec(select(SparePart)).all()
    return sorted(set(p.category for p in parts if p.category))


@router.get("/{part_id}", response_model=SparePartResponse)
def get_part(part_id: int, session: Session = Depends(get_session)):
    part = session.get(SparePart, part_id)
    if not part:
        raise HTTPException(status_code=404, detail="Part not found")
    return _to_response(part)


@router.patch("/{part_id}", response_model=SparePartResponse)
def update_part(part_id: int, payload: SparePartUpdate, session: Session = Depends(get_session)):
    part = session.get(SparePart, part_id)
    if not part:
        raise HTTPException(status_code=404, detail="Part not found")

    for field, value in payload.dict(exclude_unset=True).items():
        setattr(part, field, value)

    part.updated_at = datetime.utcnow()
    session.add(part)
    session.commit()
    session.refresh(part)
    return _to_response(part)


@router.delete("/{part_id}", status_code=204)
def delete_part(part_id: int, session: Session = Depends(get_session)):
    part = session.get(SparePart, part_id)
    if not part:
        raise HTTPException(status_code=404, detail="Part not found")
    session.delete(part)
    session.commit()


@router.post("/{part_id}/image", response_model=SparePartResponse)
async def upload_image(
    part_id: int,
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
):
    part = session.get(SparePart, part_id)
    if not part:
        raise HTTPException(status_code=404, detail="Part not found")

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in [".jpg", ".jpeg", ".png", ".webp"]:
        raise HTTPException(status_code=400, detail="Only JPG, PNG, WEBP allowed")

    filename = f"{part_id}{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    with open(filepath, "wb") as f:
        shutil.copyfileobj(file.file, f)

    part.image_url = f"/uploads/spare-parts/{filename}"
    part.updated_at = datetime.utcnow()
    session.add(part)
    session.commit()
    session.refresh(part)
    return _to_response(part)
