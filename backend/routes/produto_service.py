from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session
from config.database import get_db
from models.produto_model import Produto
from schemas.produto_schema import ProdutoCreate, ProdutoResponse
from fastapi import Depends

router = APIRouter(prefix="/produtos", tags=["Produtos"])

@router.post("/", response_model=ProdutoResponse)
def criar_produto(produto: ProdutoCreate, db: Session = Depends(get_db)):
    novo_produto = Produto(**produto.dict())
    db.add(novo_produto)
    db.commit()
    db.refresh(novo_produto)
    return novo_produto

@router.get("/", response_model=list[ProdutoResponse])
def listar_produtos(db: Session = Depends(get_db)):
    return db.query(Produto).all()

@router.get("/{produto_id}", response_model=ProdutoResponse)
def obter_produto(produto_id: str, db: Session = Depends(get_db)):
    produto = db.query(Produto).filter(Produto.id == produto_id).first()
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    return produto

@router.put("/{produto_id}", response_model=ProdutoResponse)
def atualizar_produto(produto_id: str, produto: ProdutoCreate, db: Session = Depends(get_db)):
    db_produto = db.query(Produto).filter(Produto.id == produto_id).first()
    if not db_produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    for key, value in produto.dict().items():
        setattr(db_produto, key, value)
    db.commit()
    db.refresh(db_produto)
    return db_produto

@router.delete("/{produto_id}")
def deletar_produto(produto_id: str, db: Session = Depends(get_db)):
    db_produto = db.query(Produto).filter(Produto.id == produto_id).first()
    if not db_produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    db.delete(db_produto)
    db.commit()
    return {"ok": True, "message": "Produto deletado com sucesso"}

