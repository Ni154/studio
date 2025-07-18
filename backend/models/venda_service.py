# backend/models/venda_model.py

from sqlalchemy import Column, Integer, String, Date, Float, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from config.database import Base

class Venda(Base):
    __tablename__ = "vendas"

    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=False)
    cliente_nome = Column(String, nullable=False)
    data = Column(Date, nullable=False)
    produtos = Column(JSON, default=[])
    servicos = Column(JSON, default=[])
    total = Column(Float, nullable=False)
    cancelada = Column(Boolean, default=False)
    agendamento_id = Column(Integer, ForeignKey("agendamentos.id"), nullable=True)
    forma_pagamento = Column(String, nullable=True)

    cliente = relationship("Cliente", back_populates="vendas")
    agendamento = relationship("Agendamento", back_populates="vendas")

