from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from config.database import get_db
from models.servico_model import Servico
from schemas.servico_schema import Servico, ServicoCreate, ServicoUpdate
from services.servico_service import (
    listar_servicos,
    buscar_servico_por_id,
    criar_servico,
    atualizar_servico,
    deletar_servico,
)

router = APIRouter(prefix="/servicos", tags=["Serviços"])

@router.get("/", response_model=List[Servico])
def read_servicos(db: Session = Depends(get_db)):
    return listar_servicos(db)

@router.get("/{servico_id}", response_model=Servico)
def read_servico(servico_id: int, db: Session = Depends(get_db)):
    servico = buscar_servico_por_id(db, servico_id)
    if not servico:
        raise HTTPException(status_code=404, detail="Serviço não encontrado")
    return servico

@router.post("/", response_model=Servico, status_code=201)
def create_servico(servico: ServicoCreate, db: Session = Depends(get_db)):
    return criar_servico(db, servico.dict())

@router.put("/{servico_id}", response_model=Servico)
def update_servico(servico_id: int, servico: ServicoUpdate, db: Session = Depends(get_db)):
    atualizado = atualizar_servico(db, servico_id, servico.dict())
    if not atualizado:
        raise HTTPException(status_code=404, detail="Serviço não encontrado")
    return atualizado

@router.delete("/{servico_id}", status_code=204)
def delete_servico(servico_id: int, db: Session = Depends(get_db)):
    sucesso = deletar_servico(db, servico_id)
    if not sucesso:
        raise HTTPException(status_code=404, detail="Serviço não encontrado")
    return None

