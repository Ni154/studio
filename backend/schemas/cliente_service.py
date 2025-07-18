from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import date

class ClienteBase(BaseModel):
    nome: str = Field(..., example="João da Silva")
    telefone: Optional[str] = Field(None, example="(11) 91234-5678")
    email: Optional[EmailStr] = Field(None, example="joao@email.com")
    nascimento: Optional[date] = Field(None, example="1990-01-01")
    sintomas: Optional[str] = Field(None, example="Dor de cabeça, tontura")
    alergias: Optional[str] = Field(None, example="Nenhuma")
    medicacao: Optional[str] = Field(None, example="Dipirona")
    observacoes: Optional[str] = Field(None, example="Paciente ansioso")

class ClienteCreate(ClienteBase):
    pass

class ClienteUpdate(ClienteBase):
    pass

class ClienteInDB(ClienteBase):
    id: int

    class Config:
        orm_mode = True
