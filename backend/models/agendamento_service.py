from sqlalchemy import Column, Integer, String, Date
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Agendamento(Base):
    __tablename__ = "agendamentos"

    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(Integer, nullable=False)
    cliente_nome = Column(String, nullable=False)
    data = Column(Date, nullable=False)
    hora = Column(String, nullable=False)
    servicos = Column(String, nullable=False)
    status = Column(String, nullable=False, default="Agendado")

