# backend/schemas/despesa_schema.py

from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class DespesaBase(BaseModel):
    valor: float
    categoria: str
    descricao: Optional[str] = None
    data: Optional[datetime] = None

class DespesaCreate(DespesaBase):
    pass

class DespesaUpdate(BaseModel):
    valor: Optional[float] = None
    categoria: Optional[str] = None
    descricao: Optional[str] = None
    data: Optional[datetime] = None

class Despesa(DespesaBase):
    id: int

    class Config:
        orm_mode = True

