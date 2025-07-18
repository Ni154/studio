import streamlit as st
from config.supabase_client import supabase
from services.cliente_service import form_clientes
from services.venda_service import venda_por_agendamento, nova_venda, historico_vendas
from services.agendamento_service import form_agendamento
from services.despesas_service import form_despesas
from services.relatorio_service import relatorios_financeiros
from services.backup_service import fazer_backup
from utils.formatters import formatar_data_br
from datetime import datetime

# Usuários fixos para login simples (exemplo)
USUARIOS = {
    "admin": "123456",
}

def login():
    st.title("Login")
    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if usuario in USUARIOS and USUARIOS[usuario] == senha:
            st.session_state["logado"] = True
            st.session_state["usuario"] = usuario
            st.experimental_rerun()
        else:
            st.error("Usuário ou senha incorretos.")

def logout():
    st.session_state.clear()
    st.experimental_rerun()

def main_menu():
    st.sidebar.title(f"Bem-vindo, {st.session_state['usuario']}")
    menu = st.sidebar.radio("Menu", [
        "Clientes",
        "Agendamentos",
        "Vendas",
        "Despesas",
        "Relatórios",
        "Backup",
        "Sair"
    ])

    if menu == "Clientes":
        form_clientes()
    elif menu == "Agendamentos":
        form_agendamento()
    elif menu == "Vendas":
        st.subheader("Vendas")
        # Carrega clientes para venda
        clientes_resp = supabase.table("clientes").select("*").execute()
        if clientes_resp.status_code == 200:
            clientes = clientes_resp.data
        else:
            clientes = []
            st.error("Erro ao carregar clientes.")

        opcoes = st.radio("Tipo de venda", ["Por Agendamento", "Nova Venda", "Histórico de Vendas"])
        if opcoes == "Por Agendamento":
            agendamentos_resp = supabase.table("agendamentos").select("*").eq("status", "Agendado").order("data", ascending=True).order("hora", ascending=True).execute()
            if agendamentos_resp.status_code == 200:
                agendamentos = agendamentos_resp.data
                for ag in agendamentos:
                    st.write(f"{formatar_data_br(ag['data'])} - {ag['cliente_nome']} - {ag.get('servicos', '')}")
                agendamento_id = st.selectbox("Selecione agendamento para venda", [""] + [str(ag['id']) for ag in agendamentos])
                if agendamento_id:
                    ag_selecionado = next((a for a in agendamentos if str(a['id']) == agendamento_id), None)
                    if ag_selecionado:
                        venda_por_agendamento(ag_selecionado)
            else:
                st.error("Erro ao carregar agendamentos.")
        elif opcoes == "Nova Venda":
            nova_venda(clientes)
        elif opcoes == "Histórico de Vendas":
            historico_vendas()

    elif menu == "Despesas":
        form_despesas()
    elif menu == "Relatórios":
        relatorios_financeiros()
    elif menu == "Backup":
        st.subheader("Backup do Banco de Dados")
        if st.button("Gerar e Baixar Backup"):
            fazer_backup()
    elif menu == "Sair":
        logout()

def main():
    if "logado" not in st.session_state or not st.session_state["logado"]:
        login()
    else:
        main_menu()

if __name__ == "__main__":
    main()
