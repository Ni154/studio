from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import date

from config.database import get_db
from models.agendamento_model import Agendamento
from schemas.agendamento_schema import AgendamentoCreate, AgendamentoUpdate, AgendamentoOut

router = APIRouter(prefix="/agendamentos", tags=["Agendamentos"])

@router.get("/", response_model=List[AgendamentoOut])
def listar_agendamentos(data_inicio: date = None, db: Session = Depends(get_db)):
    query = db.query(Agendamento)
    if data_inicio:
        query = query.filter(Agendamento.data >= data_inicio)
    agendamentos = query.order_by(Agendamento.data.asc(), Agendamento.hora.asc()).all()
    return agendamentos

@router.post("/", response_model=AgendamentoOut)
def criar_agendamento(agendamento: AgendamentoCreate, db: Session = Depends(get_db)):
    novo = Agendamento(**agendamento.dict())
    db.add(novo)
    db.commit()
    db.refresh(novo)
    return novo

@router.put("/{agendamento_id}", response_model=AgendamentoOut)
def atualizar_agendamento(agendamento_id: int, agendamento: AgendamentoUpdate, db: Session = Depends(get_db)):
    ag = db.query(Agendamento).filter(Agendamento.id == agendamento_id).first()
    if not ag:
        raise HTTPException(status_code=404, detail="Agendamento não encontrado")
    for key, value in agendamento.dict(exclude_unset=True).items():
        setattr(ag, key, value)
    db.commit()
    db.refresh(ag)
    return ag

@router.put("/{agendamento_id}/cancelar", response_model=AgendamentoOut)
def cancelar_agendamento(agendamento_id: int, db: Session = Depends(get_db)):
    ag = db.query(Agendamento).filter(Agendamento.id == agendamento_id).first()
    if not ag:
        raise HTTPException(status_code=404, detail="Agendamento não encontrado")
    ag.status = "Cancelado"
    db.commit()
    db.refresh(ag)
    return ag

