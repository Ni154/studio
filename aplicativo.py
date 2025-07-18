# app.py
import streamlit as st
from config.supabase_client import supabase
from services.cliente_service import tela_cadastro_cliente
from services.venda_service import tela_vendas
from services.relatorio_service import tela_relatorios
from services.backup_service import tela_backup
from utils.form_helpers import limpar_sessao_formulario

# --- Login Simples ---
def login():
    st.title("🔐 Login do Sistema")

    if "login" not in st.session_state:
        st.session_state.login = False

    if not st.session_state.login:
        usuario = st.text_input("Usuário")
        senha = st.text_input("Senha", type="password")

        if st.button("Entrar"):
            if usuario == "admin" and senha == "1234":
                st.session_state.login = True
                st.success("Login realizado com sucesso!")
                st.experimental_rerun()
            else:
                st.error("Usuário ou senha incorretos.")
    else:
        menu_principal()

# --- Menu Principal ---
def menu_principal():
    st.sidebar.title("📋 Menu")
    menu = st.sidebar.radio(
        "Navegar",
        ["Cadastro de Clientes", "Vendas", "Relatórios", "Backup", "Sair"],
        index=0
    )

    if menu == "Cadastro de Clientes":
        tela_cadastro_cliente()

    elif menu == "Vendas":
        tela_vendas()

    elif menu == "Relatórios":
        tela_relatorios()

    elif menu == "Backup":
        tela_backup()

    elif menu == "Sair":
        st.session_state.login = False
        st.experimental_rerun()

# --- App principal ---
def main():
    st.set_page_config(page_title="Sistema de Gestão", layout="wide")
    login()

if __name__ == "__main__":
    main()
