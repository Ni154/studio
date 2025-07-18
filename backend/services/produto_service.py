from sqlalchemy.orm import Session
from models.produto_model import Produto
from schemas.produto_schema import ProdutoCreate, ProdutoUpdate

def listar_produtos(db: Session):
    return db.query(Produto).all()

def buscar_produto_por_id(db: Session, produto_id: int):
    return db.query(Produto).filter(Produto.id == produto_id).first()

def criar_produto(db: Session, produto: ProdutoCreate):
    db_produto = Produto(
        nome=produto.nome,
        descricao=produto.descricao,
        preco=produto.preco
    )
    db.add(db_produto)
    db.commit()
    db.refresh(db_produto)
    return db_produto

def atualizar_produto(db: Session, produto_id: int, produto: ProdutoUpdate):
    db_produto = buscar_produto_por_id(db, produto_id)
    if not db_produto:
        return None
    for key, value in produto.dict(exclude_unset=True).items():
        setattr(db_produto, key, value)
    db.commit()
    db.refresh(db_produto)
    return db_produto

def excluir_produto(db: Session, produto_id: int):
    db_produto = buscar_produto_por_id(db, produto_id)
    if not db_produto:
        return False
    db.delete(db_produto)
    db.commit()
    return True

