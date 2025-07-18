from datetime import date
from sqlalchemy.orm import Session
from models.cliente_model import Cliente
from schemas.cliente_schema import ClienteCreate, ClienteUpdate

def listar_clientes(db: Session):
    return db.query(Cliente).all()

def buscar_cliente_por_id(db: Session, cliente_id: int):
    return db.query(Cliente).filter(Cliente.id == cliente_id).first()

def criar_cliente(db: Session, cliente: ClienteCreate):
    db_cliente = Cliente(
        nome=cliente.nome,
        telefone=cliente.telefone,
        email=cliente.email,
        nascimento=cliente.nascimento,
        sintomas=cliente.sintomas,
        alergias=cliente.alergias,
        medicacao=cliente.medicacao,
        observacoes=cliente.observacoes,
    )
    db.add(db_cliente)
    db.commit()
    db.refresh(db_cliente)
    return db_cliente

def atualizar_cliente(db: Session, cliente_id: int, cliente: ClienteUpdate):
    db_cliente = buscar_cliente_por_id(db, cliente_id)
    if not db_cliente:
        return None
    for key, value in cliente.dict(exclude_unset=True).items():
        setattr(db_cliente, key, value)
    db.commit()
    db.refresh(db_cliente)
    return db_cliente

def excluir_cliente(db: Session, cliente_id: int):
    db_cliente = buscar_cliente_por_id(db, cliente_id)
    if not db_cliente:
        return False
    db.delete(db_cliente)
    db.commit()
    return True

