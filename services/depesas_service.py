# services/despesas_service.py

import streamlit as st
from datetime import datetime
from config.supabase_client import supabase
from utils.formatters import formatar_data_br

def carregar_despesas():
    response = supabase.table("despesas").select("*").order("data", desc=True).execute()
    if response.status_code == 200:
        return response.data
    else:
        st.error("Erro ao carregar despesas.")
        return []

def salvar_despesa(despesa):
    if "id" in despesa and despesa["id"]:
        response = supabase.table("despesas").update(despesa).eq("id", despesa["id"]).execute()
    else:
        response = supabase.table("despesas").insert(despesa).execute()
    if response.status_code not in (200, 201):
        st.error("Erro ao salvar despesa.")
        return False
    return True

def excluir_despesa(despesa_id):
    response = supabase.table("despesas").delete().eq("id", despesa_id).execute()
    if response.status_code not in (200, 204):
        st.error("Erro ao excluir despesa.")
        return False
    return True

def limpar_formulario_despesa():
    st.session_state["descricao"] = ""
    st.session_state["valor"] = 0.0
    st.session_state["data"] = datetime.today()

def form_despesas():
    st.subheader("Cadastro de Despesas")

    descricao = st.text_input("Descrição", key="descricao")
    valor = st.number_input("Valor (R$)", min_value=0.0, format="%.2f", key="valor")
    data = st.date_input("Data", value=st.session_state.get("data", datetime.today()), key="data")

    despesas = carregar_despesas()

    despesa_selecionada = st.selectbox(
        "Selecione uma despesa para editar/excluir",
        options=[""] + [f"{d['descricao']} - {formatar_data_br(d['data'])} - R$ {d['valor']:.2f}" for d in despesas]
    )

    despesa_id = None
    if despesa_selecionada:
        index = [f"{d['descricao']} - {formatar_data_br(d['data'])} - R$ {d['valor']:.2f}" for d in despesas].index(despesa_selecionada)
        despesa = despesas[index]
        despesa_id = despesa["id"]

        if "descricao" not in st.session_state or st.session_state["descricao"] == "":
            st.session_state["descricao"] = despesa["descricao"]
            st.session_state["valor"] = despesa["valor"]
            st.session_state["data"] = datetime.strptime(despesa["data"], "%Y-%m-%d")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("Salvar"):
            if not descricao:
                st.error("Descrição é obrigatória.")
            elif valor <= 0:
                st.error("Valor deve ser maior que zero.")
            else:
                despesa_obj = {
                    "descricao": descricao,
                    "valor": valor,
                    "data": data.strftime("%Y-%m-%d"),
                    "id": despesa_id
                }
                if salvar_despesa(despesa_obj):
                    st.success("Despesa salva com sucesso!")
                    limpar_formulario_despesa()
                    st.experimental_rerun()

    with col2:
        if despesa_id:
            if st.button("Excluir"):
                if excluir_despesa(despesa_id):
                    st.success("Despesa excluída com sucesso!")
                    limpar_formulario_despesa()
                    st.experimental_rerun()

    with col3:
        if st.button("Limpar formulário"):
            limpar_formulario_despesa()

