from fastapi import APIRouter, HTTPException, Depends
from typing import List
from sqlalchemy.orm import Session
from schemas.cliente_schema import ClienteCreate, ClienteUpdate, ClienteOut
from models.cliente_model import Cliente
from config.database import get_db
from services.cliente_service import ClienteService

router = APIRouter(prefix="/clientes", tags=["Clientes"])

@router.get("/", response_model=List[ClienteOut])
def listar_clientes(db: Session = Depends(get_db)):
    clientes = ClienteService.listar_todos(db)
    return clientes

@router.post("/", response_model=ClienteOut)
def criar_cliente(cliente: ClienteCreate, db: Session = Depends(get_db)):
    novo_cliente = ClienteService.criar(db, cliente)
    return novo_cliente

@router.put("/{cliente_id}", response_model=ClienteOut)
def atualizar_cliente(cliente_id: int, cliente: ClienteUpdate, db: Session = Depends(get_db)):
    cliente_atualizado = ClienteService.atualizar(db, cliente_id, cliente)
    if not cliente_atualizado:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    return cliente_atualizado

@router.delete("/{cliente_id}", status_code=204)
def deletar_cliente(cliente_id: int, db: Session = Depends(get_db)):
    sucesso = ClienteService.deletar(db, cliente_id)
    if not sucesso:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")

