from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session
from fastapi import Depends

from config.database import get_db
from models.servico_model import Servico
from schemas.servico_schema import ServicoCreate, ServicoOut

router = APIRouter(prefix="/servicos", tags=["Serviços"])

@router.post("/", response_model=ServicoOut)
def criar_servico(servico: ServicoCreate, db: Session = Depends(get_db)):
    db_servico = Servico(**servico.dict())
    db.add(db_servico)
    db.commit()
    db.refresh(db_servico)
    return db_servico

@router.get("/", response_model=list[ServicoOut])
def listar_servicos(db: Session = Depends(get_db)):
    return db.query(Servico).all()

@router.get("/{servico_id}", response_model=ServicoOut)
def obter_servico(servico_id: str, db: Session = Depends(get_db)):
    servico = db.query(Servico).get(servico_id)
    if not servico:
        raise HTTPException(status_code=404, detail="Serviço não encontrado")
    return servico

@router.put("/{servico_id}", response_model=ServicoOut)
def atualizar_servico(servico_id: str, dados: ServicoCreate, db: Session = Depends(get_db)):
    servico = db.query(Servico).get(servico_id)
    if not servico:
        raise HTTPException(status_code=404, detail="Serviço não encontrado")
    
    for key, value in dados.dict().items():
        setattr(servico, key, value)
    
    db.commit()
    db.refresh(servico)
    return servico

@router.delete("/{servico_id}")
def deletar_servico(servico_id: str, db: Session = Depends(get_db)):
    servico = db.query(Servico).get(servico_id)
    if not servico:
        raise HTTPException(status_code=404, detail="Serviço não encontrado")
    
    db.delete(servico)
    db.commit()
    return {"detail": "Serviço removido com sucesso"}

