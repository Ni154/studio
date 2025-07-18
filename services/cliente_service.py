import streamlit as st
from datetime import date
from utils.pdf_generator import gerar_pdf_cliente
from utils.form_helpers import limpar_formulario_cliente
from config.supabase_client import supabase

def carregar_clientes():
    response = supabase.table("clientes").select("*").execute()
    if response.status_code == 200:
        return response.data
    else:
        st.error("Erro ao carregar clientes")
        return []

def salvar_cliente(dados_cliente):
    # Salva ou atualiza cliente no supabase
    if "id" in dados_cliente and dados_cliente["id"]:
        # Atualizar cliente existente
        response = supabase.table("clientes").update(dados_cliente).eq("id", dados_cliente["id"]).execute()
    else:
        # Inserir cliente novo
        response = supabase.table("clientes").insert(dados_cliente).execute()
    if response.status_code not in (200, 201):
        st.error("Erro ao salvar cliente")
        return False
    return True

def excluir_cliente(cliente_id):
    response = supabase.table("clientes").delete().eq("id", cliente_id).execute()
    if response.status_code not in (200, 204):
        st.error("Erro ao excluir cliente")
        return False
    return True

def cadastro_clientes():
    st.subheader("👤 Cadastro de Clientes")

    # Estado para edição
    if "cliente_editando" not in st.session_state:
        st.session_state.cliente_editando = None

    clientes = carregar_clientes()
    clientes_dict = {c["nome"]: c for c in clientes}

    col1, col2 = st.columns([2,3])

    with col1:
        with st.form("form_cliente", clear_on_submit=False):
            if st.session_state.cliente_editando:
                cliente = st.session_state.cliente_editando
                nome_inicial = cliente.get("nome", "")
                telefone_inicial = cliente.get("telefone", "")
                email_inicial = cliente.get("email", "")
                nascimento_inicial = cliente.get("nascimento", "")
                # Anamnese
                sintomas_inicial = cliente.get("sintomas", "")
                alergias_inicial = cliente.get("alergias", "")
                medicacao_inicial = cliente.get("medicacao", "")
                observacoes_inicial = cliente.get("observacoes", "")
            else:
                nome_inicial = ""
                telefone_inicial = ""
                email_inicial = ""
                nascimento_inicial = ""
                sintomas_inicial = ""
                alergias_inicial = ""
                medicacao_inicial = ""
                observacoes_inicial = ""

            nome = st.text_input("Nome completo", value=nome_inicial)
            telefone = st.text_input("Telefone", value=telefone_inicial)
            email = st.text_input("Email", value=email_inicial)
            nascimento = st.date_input("Data de Nascimento", value=date.fromisoformat(nascimento_inicial) if nascimento_inicial else date.today())

            st.markdown("### 📝 Ficha de Anamnese")
            sintomas = st.text_area("Sintomas", value=sintomas_inicial)
            alergias = st.text_area("Alergias", value=alergias_inicial)
            medicacao = st.text_area("Medicação em uso", value=medicacao_inicial)
            observacoes = st.text_area("Observações adicionais", value=observacoes_inicial)

            submitted = st.form_submit_button("Salvar Cliente")

            if submitted:
                if not nome.strip():
                    st.error("O nome é obrigatório.")
                else:
                    dados = {
                        "nome": nome.strip(),
                        "telefone": telefone.strip(),
                        "email": email.strip(),
                        "nascimento": nascimento.isoformat(),
                        "sintomas": sintomas.strip(),
                        "alergias": alergias.strip(),
                        "medicacao": medicacao.strip(),
                        "observacoes": observacoes.strip()
                    }

                    if st.session_state.cliente_editando:
                        dados["id"] = st.session_state.cliente_editando.get("id")

                    sucesso = salvar_cliente(dados)
                    if sucesso:
                        st.success("Cliente salvo com sucesso!")
                        gerar_pdf_cliente(dados)  # Gera o PDF ao salvar
                        st.session_state.cliente_editando = None
                        limpar_formulario_cliente()  # Limpa o formulário após salvar
                        st.experimental_rerun()

    with col2:
        st.write("### Clientes Cadastrados")
        if clientes:
            for c in clientes:
                st.write(f"**{c['nome']}** - {c.get('telefone', '')}")
                col_edit, col_del = st.columns([1,1])
                with col_edit:
                    if st.button(f"✏️ Editar {c['nome']}", key=f"edit_{c['id']}"):
                        st.session_state.cliente_editando = c
                        st.experimental_rerun()
                with col_del:
                    if st.button(f"❌ Excluir {c['nome']}", key=f"del_{c['id']}"):
                        if excluir_cliente(c["id"]):
                            st.success("Cliente excluído.")
                            st.experimental_rerun()
        else:
            st.info("Nenhum cliente cadastrado.")

