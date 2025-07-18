from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.cliente_routes import router as cliente_router
from routes.produto_routes import router as produto_router
from routes.servico_routes import router as servico_router
from routes.agendamento_routes import router as agendamento_router
from routes.venda_routes import router as venda_router
from routes.relatorio_routes import router as relatorio_router
from routes.despesa_routes import router as despesa_router

app = FastAPI(title="Sistema Completo - Railway")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ajustar em produção
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(cliente_router)
app.include_router(produto_router)
app.include_router(servico_router)
app.include_router(agendamento_router)
app.include_router(venda_router)
app.include_router(relatorio_router)
app.include_router(despesa_router)

@app.get("/")
def root():
    return {"message": "Backend rodando no Railway"}


