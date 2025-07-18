from datetime import datetime
from sqlalchemy.orm import Session
from models.venda_model import Venda
from models.agendamento_model import Agendamento

def carregar_agendamentos_para_venda(db: Session):
    return db.query(Agendamento).filter(Agendamento.status == "Agendado").order_by(Agendamento.data.asc(), Agendamento.hora.asc()).all()

def carregar_vendas(db: Session):
    return db.query(Venda).order_by(Venda.data.desc()).all()

def salvar_venda(db: Session, venda: Venda):
    if venda.id:
        db.merge(venda)
    else:
        db.add(venda)
    db.commit()
    return True

def cancelar_venda(db: Session, venda_id: int):
    venda = db.query(Venda).filter(Venda.id == venda_id).first()
    if not venda:
        return False
    venda.cancelada = True
    db.commit()
    return True

