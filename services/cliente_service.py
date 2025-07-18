# services/cliente_service.py
import streamlit as st
from datetime import datetime
from fpdf import FPDF
from config.supabase_client import supabase
from utils.form_helpers import limpar_sessao_formulario

def tela_cadastro_cliente():
    st.subheader("👤 Cadastro de Clientes")

    with st.form("form_cliente"):
        nome = st.text_input("Nome completo")
        idade = st.number_input("Idade", min_value=0, max_value=120)
        telefone = st.text_input("Telefone")
        email = st.text_input("Email")

        st.markdown("#### 🩺 Ficha de Anamnese")
        queixa_principal = st.text_area("Queixa principal")
        historico_clinico = st.text_area("Histórico clínico")
        medicacoes = st.text_area("Medicações em uso")
        alergias = st.text_area("Alergias")
        outras_info = st.text_area("Outras informações relevantes")

        col1, col2 = st.columns(2)
        with col1:
            salvar = st.form_submit_button("Salvar Cadastro")
        with col2:
            limpar = st.form_submit_button("Limpar Formulário")

    if salvar:
        if not nome:
            st.error("O campo nome é obrigatório.")
        else:
            dados = {
                "nome": nome,
                "idade": idade,
                "telefone": telefone,
                "email": email,
                "queixa_principal": queixa_principal,
                "historico_clinico": historico_clinico,
                "medicacoes": medicacoes,
                "alergias": alergias,
                "outras_info": outras_info,
                "data_cadastro": datetime.now().isoformat()
            }

            supabase.table("clientes").insert(dados).execute()
            gerar_pdf_cliente(dados)
            st.success("Cliente cadastrado com sucesso!")
            limpar_sessao_formulario()

    if limpar:
        limpar_sessao_formulario()

    st.markdown("---")
    listar_clientes()

def gerar_pdf_cliente(dados):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.cell(200, 10, txt="Ficha de Cadastro - Loyalt Profissional", ln=True, align="C")
    pdf.ln(10)

    for chave, valor in dados.items():
        pdf.cell(200, 10, txt=f"{chave.replace('_', ' ').capitalize()}: {valor}", ln=True)

    nome_pdf = f"ficha_{dados['nome'].replace(' ', '_')}.pdf"
    pdf.output(nome_pdf)
    with open(nome_pdf, "rb") as f:
        st.download_button("📄 Baixar PDF do Cliente", f, file_name=nome_pdf)

def listar_clientes():
    st.subheader("📋 Clientes Cadastrados")
    clientes = supabase.table("clientes").select("*").execute()
    lista = clientes.data if clientes.data else []

    for cliente in lista:
        with st.expander(f"{cliente['nome']} - {cliente['telefone']}"):
            st.write("📧", cliente["email"])
            st.write("🩺 Queixa:", cliente["queixa_principal"])
            st.write("📆 Cadastrado em:", cliente["data_cadastro"])

            col1, col2 = st.columns(2)
            with col1:
                if st.button("✏️ Editar", key=f"edit_{cliente['id']}"):
                    editar_cliente(cliente)
            with col2:
                if st.button("🗑️ Excluir", key=f"del_{cliente['id']}"):
                    supabase.table("clientes").delete().eq("id", cliente["id"]).execute()
                    st.success("Cliente excluído.")
                    st.experimental_rerun()

def editar_cliente(cliente):
    st.info("Modo de edição ainda será implementado.")

