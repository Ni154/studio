from sqlalchemy.orm import Session
from models.servico_model import Servico
from schemas.servico_schema import ServicoCreate, ServicoUpdate

def listar_servicos(db: Session):
    return db.query(Servico).all()

def buscar_servico_por_id(db: Session, servico_id: int):
    return db.query(Servico).filter(Servico.id == servico_id).first()

def criar_servico(db: Session, servico: ServicoCreate):
    db_servico = Servico(
        nome=servico.nome,
        descricao=servico.descricao,
        preco=servico.preco
    )
    db.add(db_servico)
    db.commit()
    db.refresh(db_servico)
    return db_servico

def atualizar_servico(db: Session, servico_id: int, servico: ServicoUpdate):
    db_servico = buscar_servico_por_id(db, servico_id)
    if not db_servico:
        return None
    for key, value in servico.dict(exclude_unset=True).items():
        setattr(db_servico, key, value)
    db.commit()
    db.refresh(db_servico)
    return db_servico

def excluir_servico(db: Session, servico_id: int):
    db_servico = buscar_servico_por_id(db, servico_id)
    if not db_servico:
        return False
    db.delete(db_servico)
    db.commit()
    return True

