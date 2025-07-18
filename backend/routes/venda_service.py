from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from models.venda_model import Venda
from schemas.venda_schema import VendaCreate, VendaRead
from config.database import get_db
from services.venda_service import (
    carregar_agendamentos_para_venda,
    carregar_vendas,
    salvar_venda,
    cancelar_venda
)

router = APIRouter(prefix="/vendas", tags=["Vendas"])

@router.get("/agendamentos", response_model=List)
def listar_agendamentos(db: Session = Depends(get_db)):
    agendamentos = carregar_agendamentos_para_venda(db)
    return agendamentos

@router.get("/", response_model=List[VendaRead])
def listar_vendas(db: Session = Depends(get_db)):
    vendas = carregar_vendas(db)
    return vendas

@router.post("/", response_model=VendaRead)
def criar_venda(venda_data: VendaCreate, db: Session = Depends(get_db)):
    venda = Venda(**venda_data.dict())
    salvar_venda(db, venda)
    return venda

@router.put("/{venda_id}/cancelar")
def cancelar_venda_endpoint(venda_id: int, db: Session = Depends(get_db)):
    sucesso = cancelar_venda(db, venda_id)
    if not sucesso:
        raise HTTPException(status_code=404, detail="Venda não encontrada")
    return {"message": "Venda cancelada com sucesso"}
