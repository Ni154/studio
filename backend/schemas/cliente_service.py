from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import date

class ClienteBase(BaseModel):
    nome: str
    telefone: Optional[str] = None
    email: Optional[EmailStr] = None
    nascimento: Optional[date] = None

    # Ficha de anamnese
    sintomas: Optional[str] = None
    alergias: Optional[str] = None
    medicacao: Optional[str] = None
    observacoes: Optional[str] = None

class ClienteCreate(ClienteBase):
    pass

class ClienteUpdate(ClienteBase):
    id: int

class ClienteOut(ClienteBase):
    id: int

    class Config:
        orm_mode = True
