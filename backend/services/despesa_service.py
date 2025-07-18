# backend/services/despesa_service.py

from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from models.despesa_model import Despesa
from schemas.despesa_schema import DespesaCreate, DespesaUpdate

def listar_despesas(db: Session, skip: int = 0, limit: int = 100) -> List[Despesa]:
    return db.query(Despesa).order_by(Despesa.data.desc()).offset(skip).limit(limit).all()

def criar_despesa(db: Session, despesa: DespesaCreate) -> Despesa:
    db_despesa = Despesa(
        valor=despesa.valor,
        categoria=despesa.categoria,
        descricao=despesa.descricao,
        data=despesa.data or datetime.utcnow()
    )
    db.add(db_despesa)
    db.commit()
    db.refresh(db_despesa)
    return db_despesa

def atualizar_despesa(db: Session, despesa_id: int, despesa: DespesaUpdate) -> Optional[Despesa]:
    db_despesa = db.query(Despesa).filter(Despesa.id == despesa_id).first()
    if not db_despesa:
        return None
    if despesa.valor is not None:
        db_despesa.valor = despesa.valor
    if despesa.categoria is not None:
        db_despesa.categoria = despesa.categoria
    if despesa.descricao is not None:
        db_despesa.descricao = despesa.descricao
    if despesa.data is not None:
        db_despesa.data = despesa.data
    db.commit()
    db.refresh(db_despesa)
    return db_despesa

def deletar_despesa(db: Session, despesa_id: int) -> bool:
    db_despesa = db.query(Despesa).filter(Despesa.id == despesa_id).first()
    if not db_despesa:
        return False
    db.delete(db_despesa)
    db.commit()
    return True

