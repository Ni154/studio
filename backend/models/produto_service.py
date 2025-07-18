
from sqlalchemy import Column, String, Float, Integer
from sqlalchemy.dialects.postgresql import UUID
import uuid
from config.database import Base

class Produto(Base):
    __tablename__ = "produtos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    nome = Column(String, nullable=False)
    descricao = Column(String)
    preco = Column(Float, nullable=False)
    categoria = Column(String)
    estoque = Column(Integer, default=0)
