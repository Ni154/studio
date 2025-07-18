# services/backup_service.py

import streamlit as st
import json
from config.supabase_client import supabase

def fazer_backup():
    st.subheader("💾 Backup do Banco de Dados")

    tabelas = ["clientes", "produtos", "servicos", "agendamentos", "vendas", "despesas"]

    dados_backup = {}

    for tabela in tabelas:
        response = supabase.table(tabela).select("*").execute()
        if response.status_code == 200:
            dados_backup[tabela] = response.data
        else:
            st.error(f"Erro ao buscar dados da tabela {tabela}")
            return

    json_backup = json.dumps(dados_backup, indent=2, ensure_ascii=False)

    st.download_button(
        label="Baixar backup JSON",
        data=json_backup,
        file_name=f"backup_{tabela}.json",
        mime="application/json"
    )

