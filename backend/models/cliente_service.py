from sqlalchemy import Column, Integer, String, Date
from config.database import Base

class Cliente(Base):
    __tablename__ = "clientes"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    telefone = Column(String, nullable=True)
    email = Column(String, nullable=True)
    nascimento = Column(Date, nullable=True)

    # Ficha de anamnese
    sintomas = Column(String, nullable=True)
    alergias = Column(String, nullable=True)
    medicacao = Column(String, nullable=True)
    observacoes = Column(String, nullable=True)

