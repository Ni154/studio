# backend/models/despesa_model.py

from sqlalchemy import Column, Integer, String, Float, DateTime
from config.database import Base
from datetime import datetime

class Despesa(Base):
    __tablename__ = "despesas"

    id = Column(Integer, primary_key=True, index=True)
    valor = Column(Float, nullable=False)
    categoria = Column(String(100), nullable=False)
    descricao = Column(String(255), nullable=True)
    data = Column(DateTime, default=datetime.utcnow)

