from typing import Optional, List
from datetime import datetime
from sqlmodel import SQLModel, Field


class SparePart(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    product_name: str
    product_id: str = Field(index=True)
    available_stock: int = Field(default=0)
    minimum_stock: int = Field(default=1)
    category: str = Field(default="")
    rack: str = Field(default="")
    image_url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class SparePartCreate(SQLModel):
    product_name: str
    product_id: str
    available_stock: int = 0
    minimum_stock: int = 1
    category: str = ""
    rack: str = ""
    image_url: Optional[str] = None


class SparePartUpdate(SQLModel):
    product_name: Optional[str] = None
    product_id: Optional[str] = None
    available_stock: Optional[int] = None
    minimum_stock: Optional[int] = None
    category: Optional[str] = None
    rack: Optional[str] = None
    image_url: Optional[str] = None


class SparePartResponse(SQLModel):
    id: int
    product_name: str
    product_id: str
    available_stock: int
    minimum_stock: int
    category: str
    rack: str
    image_url: Optional[str]
    status: str  # "ok" | "low" | "critical"
    created_at: datetime
    updated_at: datetime
