from sqlalchemy import Column, String, Text, Float
from uuid import uuid4
from sqlalchemy.dialects.postgresql import UUID
from config.database import Base

class Servico(Base):
    __tablename__ = "servicos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    nome = Column(String(100), nullable=False)
    descricao = Column(Text, nullable=True)
    preco = Column(Float, nullable=False)

