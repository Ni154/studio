
# backend/routes/despesa_routes.py

from fastapi import APIRouter, HTTPException, Depends
from typing import List
from sqlalchemy.orm import Session
from schemas.despesa_schema import Despesa, DespesaCreate, DespesaUpdate
from models.despesa_model import Despesa as DespesaModel
from config.database import get_db

router = APIRouter(prefix="/despesas", tags=["Despesas"])

@router.post("/", response_model=Despesa)
def criar_despesa(despesa: DespesaCreate, db: Session = Depends(get_db)):
    db_despesa = DespesaModel(**despesa.dict())
    db.add(db_despesa)
    db.commit()
    db.refresh(db_despesa)
    return db_despesa

@router.get("/", response_model=List[Despesa])
def listar_despesas(db: Session = Depends(get_db)):
    despesas = db.query(DespesaModel).all()
    return despesas

@router.get("/{despesa_id}", response_model=Despesa)
def obter_despesa(despesa_id: int, db: Session = Depends(get_db)):
    despesa = db.query(DespesaModel).filter(DespesaModel.id == despesa_id).first()
    if not despesa:
        raise HTTPException(status_code=404, detail="Despesa não encontrada")
    return despesa

@router.put("/{despesa_id}", response_model=Despesa)
def atualizar_despesa(despesa_id: int, despesa_update: DespesaUpdate, db: Session = Depends(get_db)):
    despesa = db.query(DespesaModel).filter(DespesaModel.id == despesa_id).first()
    if not despesa:
        raise HTTPException(status_code=404, detail="Despesa não encontrada")
    for var, value in vars(despesa_update).items():
        if value is not None:
            setattr(despesa, var, value)
    db.commit()
    db.refresh(despesa)
    return despesa

@router.delete("/{despesa_id}")
def deletar_despesa(despesa_id: int, db: Session = Depends(get_db)):
    despesa = db.query(DespesaModel).filter(DespesaModel.id == despesa_id).first()
    if not despesa:
        raise HTTPException(status_code=404, detail="Despesa não encontrada")
    db.delete(despesa)
    db.commit()
    return {"detail": "Despesa deletada com sucesso"}
