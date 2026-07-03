from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field
import json


class App(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    description: Optional[str] = None
    schema_json: str = Field(default="[]")   # JSON-serialized list of FieldSchema
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Record(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    app_id: int = Field(foreign_key="app.id", index=True)
    data_json: str = Field(default="{}")     # JSON-serialized dict of field values
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
