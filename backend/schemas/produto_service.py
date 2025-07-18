from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID

class ProdutoBase(BaseModel):
    nome: str = Field(..., example="Máscara Facial Detox")
    descricao: Optional[str] = Field(None, example="Máscara com carvão ativado")
    preco: float = Field(..., example=79.90)
    categoria: Optional[str] = Field(None, example="Estética Facial")
    estoque: Optional[int] = Field(0, example=10)

class ProdutoCreate(ProdutoBase):
    pass

class ProdutoUpdate(ProdutoBase):
    nome: Optional[str]
    preco: Optional[float]

class ProdutoOut(ProdutoBase):
    id: UUID

    class Config:
        orm_mode = True

