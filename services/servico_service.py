import streamlit as st
from config.supabase_client import supabase
from utils.form_helpers import limpar_formulario_servico

def carregar_servicos():
    response = supabase.table("servicos").select("*").execute()
    if response.status_code == 200:
        return response.data
    else:
        st.error("Erro ao carregar serviços")
        return []

def salvar_servico(dados_servico):
    if "id" in dados_servico and dados_servico["id"]:
        response = supabase.table("servicos").update(dados_servico).eq("id", dados_servico["id"]).execute()
    else:
        response = supabase.table("servicos").insert(dados_servico).execute()
    if response.status_code not in (200, 201):
        st.error("Erro ao salvar serviço")
        return False
    return True

def excluir_servico(servico_id):
    response = supabase.table("servicos").delete().eq("id", servico_id).execute()
    if response.status_code not in (200, 204):
        st.error("Erro ao excluir serviço")
        return False
    return True

def cadastro_servicos():
    st.subheader("🛠️ Cadastro de Serviços")

    if "servico_editando" not in st.session_state:
        st.session_state.servico_editando = None

    servicos = carregar_servicos()

    col1, col2 = st.columns([2, 3])

    with col1:
        with st.form("form_servico", clear_on_submit=False):
            if st.session_state.servico_editando:
                servico = st.session_state.servico_editando
                nome_inicial = servico.get("nome", "")
                descricao_inicial = servico.get("descricao", "")
                preco_inicial = servico.get("preco", 0.0)
            else:
                nome_inicial = ""
                descricao_inicial = ""
                preco_inicial = 0.0

            nome = st.text_input("Nome do Serviço", value=nome_inicial)
            descricao = st.text_area("Descrição", value=descricao_inicial)
            preco = st.number_input("Preço (R$)", min_value=0.0, format="%.2f", value=preco_inicial)

            submitted = st.form_submit_button("Salvar Serviço")

            if submitted:
                if not nome.strip():
                    st.error("O nome do serviço é obrigatório.")
                else:
                    dados = {
                        "nome": nome.strip(),
                        "descricao": descricao.strip(),
                        "preco": preco,
                    }
                    if st.session_state.servico_editando:
                        dados["id"] = st.session_state.servico_editando.get("id")

                    sucesso = salvar_servico(dados)
                    if sucesso:
                        st.success("Serviço salvo com sucesso!")
                        st.session_state.servico_editando = None
                        limpar_formulario_servico()
                        st.experimental_rerun()

    with col2:
        st.write("### Serviços Cadastrados")
        if servicos:
            for s in servicos:
                st.write(f"**{s['nome']}** - R$ {s['preco']:.2f}")
                col_edit, col_del = st.columns([1, 1])
                with col_edit:
                    if st.button(f"✏️ Editar {s['nome']}", key=f"edit_serv_{s['id']}"):
                        st.session_state.servico_editando = s
                        st.experimental_rerun()
                with col_del:
                    if st.button(f"❌ Excluir {s['nome']}", key=f"del_serv_{s['id']}"):
                        if excluir_servico(s["id"]):
                            st.success("Serviço excluído.")
                            st.experimental_rerun()
        else:
            st.info("Nenhum serviço cadastrado.")

