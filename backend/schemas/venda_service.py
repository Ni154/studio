# backend/schemas/venda_schema.py

from typing import List, Optional
from datetime import date
from pydantic import BaseModel

class ProdutoSchema(BaseModel):
    nome: str
    preco: float

class VendaBase(BaseModel):
    cliente_id: int
    cliente_nome: str
    data: date
    produtos: List[ProdutoSchema] = []
    servicos: List[str] = []
    total: float
    cancelada: Optional[bool] = False
    agendamento_id: Optional[int] = None
    forma_pagamento: Optional[str] = None

class VendaCreate(VendaBase):
    pass

class VendaUpdate(BaseModel):
    cancelada: Optional[bool] = None

class Venda(VendaBase):
    id: int

    class Config:
        orm_mode = True

