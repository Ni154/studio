import streamlit as st
from datetime import datetime, date
from config.supabase_client import supabase
from utils.formatters import formatar_data_br

def carregar_agendamentos(filtro_data=None):
    query = supabase.table("agendamentos").select("*").order("data", ascending=True).order("hora", ascending=True)
    if filtro_data:
        query = query.gte("data", filtro_data)
    response = query.execute()
    if response.status_code == 200:
        return response.data
    else:
        st.error("Erro ao carregar agendamentos")
        return []

def salvar_agendamento(dados_agendamento):
    if "id" in dados_agendamento and dados_agendamento["id"]:
        response = supabase.table("agendamentos").update(dados_agendamento).eq("id", dados_agendamento["id"]).execute()
    else:
        response = supabase.table("agendamentos").insert(dados_agendamento).execute()
    if response.status_code not in (200, 201):
        st.error("Erro ao salvar agendamento")
        return False
    return True

def cancelar_agendamento(agendamento_id):
    response = supabase.table("agendamentos").update({"status": "Cancelado"}).eq("id", agendamento_id).execute()
    if response.status_code not in (200, 204):
        st.error("Erro ao cancelar agendamento")
        return False
    return True

def reagendar_agendamento(agendamento_id, nova_data, nova_hora):
    response = supabase.table("agendamentos").update({
        "data": nova_data,
        "hora": nova_hora,
        "status": "Reagendado"
    }).eq("id", agendamento_id).execute()
    if response.status_code not in (200, 204):
        st.error("Erro ao reagendar agendamento")
        return False
    return True

def cadastro_agendamento(clientes, servicos):
    st.subheader("📅 Agendamento")

    clientes_dict = {c['nome']: c for c in clientes}
    servicos_dict = {s['nome']: s for s in servicos}

    # Estado para reagendar e cancelar
    if "reagendar_id" not in st.session_state:
        st.session_state["reagendar_id"] = None
    if "cancelar_id" not in st.session_state:
        st.session_state["cancelar_id"] = None

    # --- Reagendamento ---
    if st.session_state["reagendar_id"]:
        agendamento_id = st.session_state["reagendar_id"]
        ag = supabase.table("agendamentos").select("*").eq("id", agendamento_id).single().execute()
        if ag.status_code != 200:
            st.error("Agendamento não encontrado.")
            st.session_state["reagendar_id"] = None
            return
        ag = ag.data

        cliente = clientes_dict.get(ag["cliente_nome"], {"nome": ag.get("cliente_nome", "")})

        st.subheader("🔄 Reagendar Agendamento")
        st.write(f"Cliente: {cliente['nome']}")
        st.write(f"Serviços: {ag.get('servicos', '')}")

        nova_data = st.date_input("Nova data", datetime.strptime(ag["data"], "%Y-%m-%d").date())
        nova_hora = st.text_input("Nova hora", ag["hora"])

        if st.button("Confirmar Reagendamento"):
            sucesso = reagendar_agendamento(agendamento_id, nova_data.strftime("%Y-%m-%d"), nova_hora)
            if sucesso:
                st.success("Agendamento reagendado com sucesso!")
                st.session_state["reagendar_id"] = None
                st.experimental_rerun()

        if st.button("Cancelar"):
            st.session_state["reagendar_id"] = None
            st.experimental_rerun()

        st.stop()

    # --- Cancelar ---
    if st.session_state["cancelar_id"]:
        cancelar_id = st.session_state["cancelar_id"]
        ag = supabase.table("agendamentos").select("*").eq("id", cancelar_id).single().execute()
        if ag.status_code != 200:
            st.error("Agendamento não encontrado.")
            st.session_state["cancelar_id"] = None
            return
        ag = ag.data

        st.subheader("❌ Cancelar Agendamento")
        st.write(f"Cliente: {ag.get('cliente_nome', '')}")
        st.write(f"Data: {formatar_data_br(ag.get('data', ''))}")
        st.write(f"Hora: {ag.get('hora', '')}")
        st.write(f"Serviços: {ag.get('servicos', '')}")

        if st.button("Confirmar Cancelamento"):
            sucesso = cancelar_agendamento(cancelar_id)
            if sucesso:
                st.success("Agendamento cancelado com sucesso!")
                st.session_state["cancelar_id"] = None
                st.experimental_rerun()

        if st.button("Voltar"):
            st.session_state["cancelar_id"] = None
            st.experimental_rerun()

        st.stop()

    # --- Novo Agendamento ---
    cliente_selecionado = st.selectbox("Selecione o Cliente", [""] + list(clientes_dict.keys()))
    data_agendamento = st.date_input("Data do Agendamento", date.today())
    hora_agendamento = st.text_input("Hora (ex: 14:30)")
    servicos_selecionados = st.multiselect("Selecione os Serviços", list(servicos_dict.keys()))

    if st.button("Salvar Agendamento"):
        if cliente_selecionado == "":
            st.error("Selecione um cliente.")
        elif not hora_agendamento:
            st.error("Informe a hora do agendamento.")
        elif not servicos_selecionados:
            st.error("Selecione ao menos um serviço.")
        else:
            cliente_obj = clientes_dict[cliente_selecionado]
            dados = {
                "cliente_id": cliente_obj["id"],
                "cliente_nome": cliente_selecionado,
                "data": data_agendamento.strftime("%Y-%m-%d"),
                "hora": hora_agendamento,
                "servicos": ", ".join(servicos_selecionados),
                "status": "Agendado"
            }
            sucesso = salvar_agendamento(dados)
            if sucesso:
                st.success("Agendamento salvo!")
                st.experimental_rerun()

    st.markdown("---")
    st.subheader("📋 Lista de Agendamentos")

    data_filtro = st.date_input("Filtrar agendamentos a partir de", date.today())
    filtro_str = data_filtro.strftime("%Y-%m-%d")

    agendamentos = carregar_agendamentos(filtro_str)

    if agendamentos:
        for ag in agendamentos:
            col1, col2, col3, col4, col5, col6 = st.columns([2,3,2,2,3,3])
            with col1:
                st.write(formatar_data_br(ag["data"]))
            with col2:
                st.write(ag.get("cliente_nome", ""))
            with col3:
                st.write(ag.get("hora", ""))
            with col4:
                st.write(ag.get("servicos", ""))
            with col5:
                st.write(ag.get("status", ""))
            with col6:
                if ag.get("status") == "Agendado":
                    if st.button(f"Reagendar {ag['id']}", key=f"reag_{ag['id']}"):
                        st.session_state["reagendar_id"] = ag["id"]
                        st.experimental_rerun()
                    if st.button(f"Cancelar {ag['id']}", key=f"cancel_{ag['id']}"):
                        st.session_state["cancelar_id"] = ag["id"]
                        st.experimental_rerun()
    else:
        st.info("Nenhum agendamento encontrado a partir da data selecionada.")

