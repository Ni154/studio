from pydantic import BaseModel
from uuid import UUID
from typing import Optional

class ServicoBase(BaseModel):
    nome: str
    descricao: Optional[str] = None
    preco: float

class ServicoCreate(ServicoBase):
    pass

class ServicoResponse(ServicoBase):
    id: UUID

    class Config:
        orm_mode = True

