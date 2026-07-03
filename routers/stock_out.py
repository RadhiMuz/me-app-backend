from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select, SQLModel, Field
from db.database import get_session
from models.spare_parts import SparePart

router = APIRouter()


class StockOut(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    part_id: int = Field(foreign_key="sparepart.id", index=True)
    product_name: str
    product_id: str
    quantity: int
    usage: str
    user: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class StockOutCreate(SQLModel):
    part_id: int
    quantity: int
    usage: str
    user: str


class StockOutResponse(SQLModel):
    id: int
    part_id: int
    product_name: str
    product_id: str
    quantity: int
    usage: str
    user: str
    timestamp: datetime


@router.get("/", response_model=List[StockOutResponse])
def list_stock_outs(
    part_id: Optional[int] = None,
    user: Optional[str] = None,
    session: Session = Depends(get_session),
):
    items = session.exec(select(StockOut)).all()
    if part_id:
        items = [i for i in items if i.part_id == part_id]
    if user:
        items = [i for i in items if i.user.lower() == user.lower()]
    return sorted(items, key=lambda x: x.timestamp, reverse=True)


@router.post("/", response_model=StockOutResponse, status_code=201)
def create_stock_out(payload: StockOutCreate, session: Session = Depends(get_session)):
    part = session.get(SparePart, payload.part_id)
    if not part:
        raise HTTPException(status_code=404, detail="Part not found")
    if part.available_stock < payload.quantity:
        raise HTTPException(status_code=400, detail=f"Insufficient stock. Available: {part.available_stock}")

    # Deduct stock
    part.available_stock -= payload.quantity
    part.updated_at = datetime.utcnow()
    session.add(part)

    # Record the transaction
    record = StockOut(
        part_id=part.id,
        product_name=part.product_name,
        product_id=part.product_id,
        quantity=payload.quantity,
        usage=payload.usage,
        user=payload.user,
    )
    session.add(record)
    session.commit()
    session.refresh(record)
    return record


@router.delete("/{record_id}", status_code=204)
def delete_stock_out(record_id: int, session: Session = Depends(get_session)):
    record = session.get(StockOut, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    session.delete(record)
    session.commit()