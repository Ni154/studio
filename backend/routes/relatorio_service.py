# backend/routes/relatorio_routes.py

from fastapi import APIRouter, HTTPException, Query
from typing import List
from datetime import date
from services import relatorio_service
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/relatorios", tags=["Relatórios"])

@router.get("/financeiro")
async def relatorio_financeiro(
    data_inicio: date = Query(..., description="Data inicial do relatório"),
    data_fim: date = Query(..., description="Data final do relatório"),
):
    """
    Gera relatório financeiro (vendas, despesas e lucro) no período informado.
    Retorna dados consolidados e PDF para download.
    """
    if data_fim < data_inicio:
        raise HTTPException(status_code=400, detail="Data final não pode ser anterior à inicial.")

    # Obter dados consolidados
    df = relatorio_service.gerar_dados_relatorio(data_inicio, data_fim)

    # Gerar PDF
    pdf_file = relatorio_service.gerar_pdf_relatorio(df, data_inicio, data_fim)

    # Retorna PDF como streaming response para download
    return StreamingResponse(
        pdf_file,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=relatorio_{data_inicio}_a_{data_fim}.pdf"
        }
    )

