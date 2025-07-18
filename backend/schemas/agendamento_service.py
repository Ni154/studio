from pydantic import BaseModel, Field
from typing import Optional
from datetime import date

class AgendamentoBase(BaseModel):
    cliente_id: int
    cliente_nome: str
    data: date
    hora: str
    servicos: str
    status: str = Field(default="Agendado")

class AgendamentoCreate(AgendamentoBase):
    pass

class AgendamentoUpdate(BaseModel):
    data: Optional[date]
    hora: Optional[str]
    servicos: Optional[str]
    status: Optional[str]

class AgendamentoInDB(AgendamentoBase):
    id: int

    class Config:
        orm_mode = True

