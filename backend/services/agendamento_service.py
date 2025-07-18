from sqlalchemy.orm import Session
from datetime import datetime
from models.agendamento_model import Agendamento

def carregar_agendamentos(db: Session, filtro_data: datetime.date = None):
    query = db.query(Agendamento).order_by(Agendamento.data.asc(), Agendamento.hora.asc())
    if filtro_data:
        query = query.filter(Agendamento.data >= filtro_data)
    return query.all()

def salvar_agendamento(db: Session, dados_agendamento: dict):
    if "id" in dados_agendamento and dados_agendamento["id"]:
        agendamento = db.query(Agendamento).filter(Agendamento.id == dados_agendamento["id"]).first()
        if not agendamento:
            return False
        for key, value in dados_agendamento.items():
            setattr(agendamento, key, value)
    else:
        agendamento = Agendamento(**dados_agendamento)
        db.add(agendamento)
    db.commit()
    return True

def cancelar_agendamento(db: Session, agendamento_id: int):
    agendamento = db.query(Agendamento).filter(Agendamento.id == agendamento_id).first()
    if not agendamento:
        return False
    agendamento.status = "Cancelado"
    db.commit()
    return True

def reagendar_agendamento(db: Session, agendamento_id: int, nova_data: datetime.date, nova_hora: str):
    agendamento = db.query(Agendamento).filter(Agendamento.id == agendamento_id).first()
    if not agendamento:
        return False
    agendamento.data = nova_data
    agendamento.hora = nova_hora
    agendamento.status = "Reagendado"
    db.commit()
    return True

