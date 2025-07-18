import pandas as pd
from io import BytesIO
from fpdf import FPDF
from datetime import datetime
from sqlalchemy.orm import Session
from models.venda_model import Venda
from models.despesa_model import Despesa
from utils.formatters import formatar_data_br

def carregar_vendas_periodo(db: Session, data_inicio: str, data_fim: str):
    vendas = db.query(Venda)\
        .filter(Venda.data >= data_inicio)\
        .filter(Venda.data <= data_fim)\
        .filter(Venda.cancelada == False)\
        .all()
    return vendas

def carregar_despesas_periodo(db: Session, data_inicio: str, data_fim: str):
    despesas = db.query(Despesa)\
        .filter(Despesa.data >= data_inicio)\
        .filter(Despesa.data <= data_fim)\
        .all()
    return despesas

def gerar_pdf_relatorio(df: pd.DataFrame, data_inicio: str, data_fim: str):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    titulo = f"Relatório Financeiro ({formatar_data_br(data_inicio)} a {formatar_data_br(data_fim)})"
    pdf.cell(0, 10, titulo, ln=True, align='C')

    pdf.set_font("Arial", '', 12)
    pdf.ln(5)

    # Cabeçalho da tabela
    pdf.cell(40, 10, "Data", border=1)
    pdf.cell(50, 10, "Vendas (R$)", border=1)
    pdf.cell(50, 10, "Despesas (R$)", border=1)
    pdf.cell(40, 10, "Lucro (R$)", border=1)
    pdf.ln()

    for _, row in df.iterrows():
        pdf.cell(40, 10, row["Data"], border=1)
        pdf.cell(50, 10, f"{row['Total_Vendas']:.2f}", border=1)
        pdf.cell(50, 10, f"{row['Total_Despesas']:.2f}", border=1)
        pdf.cell(40, 10, f"{row['Lucro']:.2f}", border=1)
        pdf.ln()

    output = BytesIO()
    pdf.output(output)
    output.seek(0)
    return output

def gerar_relatorio_financeiro(db: Session, data_inicio: str, data_fim: str):
    vendas = carregar_vendas_periodo(db, data_inicio, data_fim)
    despesas = carregar_despesas_periodo(db, data_inicio, data_fim)

    # Transformar em DataFrames
    df_vendas = pd.DataFrame([{"data": v.data, "total": v.total} for v in vendas])
    df_despesas = pd.DataFrame([{"data": d.data, "valor": d.valor} for d in despesas])

    if df_vendas.empty:
        df_vendas = pd.DataFrame(columns=["data", "total"])
    if df_despesas.empty:
        df_despesas = pd.DataFrame(columns=["data", "valor"])

    df_vendas_group = df_vendas.groupby("data").agg({"total": "sum"}).reset_index()
    df_despesas_group = df_despesas.groupby("data").agg({"valor": "sum"}).reset_index()

    df_vendas_group.rename(columns={"data": "Data", "total": "Total_Vendas"}, inplace=True)
    df_despesas_group.rename(columns={"data": "Data", "valor": "Total_Despesas"}, inplace=True)

    df_vendas_group["Data"] = pd.to_datetime(df_vendas_group["Data"])
    df_despesas_group["Data"] = pd.to_datetime(df_despesas_group["Data"])

    df = pd.merge(df_vendas_group, df_despesas_group, on="Data", how="outer").fillna(0)
    df["Lucro"] = df["Total_Vendas"] - df["Total_Despesas"]
    df = df.sort_values("Data")
    df["Data"] = df["Data"].dt.strftime("%d/%m/%Y")

    return df

