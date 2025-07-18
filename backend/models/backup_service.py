from sqlalchemy import Column, Integer, String, Float
from config.database import Base

class Servico(Base):
    __tablename__ = "servicos"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, unique=True, index=True, nullable=False)
    descricao = Column(String, nullable=True)
    preco = Column(Float, nullable=False)

