# services/relatorio_service.py

import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO
from fpdf import FPDF
from config.supabase_client import supabase
from utils.formatters import formatar_data_br

def carregar_vendas_periodo(data_inicio, data_fim):
    response = supabase.table("vendas")\
        .select("data,total,cancelada")\
        .gte("data", data_inicio)\
        .lte("data", data_fim)\
        .execute()
    if response.status_code == 200:
        # filtrar vendas não canceladas
        return [v for v in response.data if not v.get("cancelada", False)]
    else:
        st.error("Erro ao carregar vendas.")
        return []

def carregar_despesas_periodo(data_inicio, data_fim):
    response = supabase.table("despesas")\
        .select("data,valor")\
        .gte("data", data_inicio)\
        .lte("data", data_fim)\
        .execute()
    if response.status_code == 200:
        return response.data
    else:
        st.error("Erro ao carregar despesas.")
        return []

def gerar_pdf_relatorio(df, data_inicio, data_fim):
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

def relatorios_financeiros():
    st.subheader("📈 Relatórios Financeiros")

    data_inicio = st.date_input("Data Início", value=pd.to_datetime("today").replace(day=1))
    data_fim = st.date_input("Data Fim", value=pd.to_datetime("today"))

    if data_fim < data_inicio:
        st.error("A data final não pode ser anterior à data inicial.")
        return

    data_inicio_str = data_inicio.strftime("%Y-%m-%d")
    data_fim_str = data_fim.strftime("%Y-%m-%d")

    vendas = carregar_vendas_periodo(data_inicio_str, data_fim_str)
    despesas = carregar_despesas_periodo(data_inicio_str, data_fim_str)

    df_vendas = pd.DataFrame(vendas)
    df_despesas = pd.DataFrame(despesas)

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

    st.line_chart(df.set_index("Data")[["Total_Vendas", "Total_Despesas", "Lucro"]])

    st.write("### Tabela de Resultados")
    st.dataframe(df, use_container_width=True)

    if st.button("Exportar relatório PDF"):
        pdf_file = gerar_pdf_relatorio(df, data_inicio, data_fim)
        st.download_button(
            label="Baixar PDF",
            data=pdf_file,
            file_name=f"relatorio_{data_inicio_str}_a_{data_fim_str}.pdf",
            mime="application/pdf"
        )

