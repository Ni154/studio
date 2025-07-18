from pydantic import BaseModel
from typing import Optional

class ServicoBase(BaseModel):
    nome: str
    descricao: Optional[str] = None
    preco: float

class ServicoCreate(ServicoBase):
    pass

class ServicoUpdate(ServicoBase):
    pass

class Servico(ServicoBase):
    id: int

    class Config:
        orm_mode = True

