import streamlit as st
from config.supabase_client import supabase
from utils.form_helpers import limpar_formulario_produto

def carregar_produtos():
    response = supabase.table("produtos").select("*").execute()
    if response.status_code == 200:
        return response.data
    else:
        st.error("Erro ao carregar produtos")
        return []

def salvar_produto(dados_produto):
    if "id" in dados_produto and dados_produto["id"]:
        response = supabase.table("produtos").update(dados_produto).eq("id", dados_produto["id"]).execute()
    else:
        response = supabase.table("produtos").insert(dados_produto).execute()
    if response.status_code not in (200, 201):
        st.error("Erro ao salvar produto")
        return False
    return True

def excluir_produto(produto_id):
    response = supabase.table("produtos").delete().eq("id", produto_id).execute()
    if response.status_code not in (200, 204):
        st.error("Erro ao excluir produto")
        return False
    return True

def cadastro_produtos():
    st.subheader("📦 Cadastro de Produtos")

    if "produto_editando" not in st.session_state:
        st.session_state.produto_editando = None

    produtos = carregar_produtos()
    produtos_dict = {p["nome"]: p for p in produtos}

    col1, col2 = st.columns([2, 3])

    with col1:
        with st.form("form_produto", clear_on_submit=False):
            if st.session_state.produto_editando:
                produto = st.session_state.produto_editando
                nome_inicial = produto.get("nome", "")
                descricao_inicial = produto.get("descricao", "")
                preco_inicial = produto.get("preco", 0.0)
                estoque_inicial = produto.get("estoque", 0)
            else:
                nome_inicial = ""
                descricao_inicial = ""
                preco_inicial = 0.0
                estoque_inicial = 0

            nome = st.text_input("Nome do Produto", value=nome_inicial)
            descricao = st.text_area("Descrição", value=descricao_inicial)
            preco = st.number_input("Preço (R$)", min_value=0.0, format="%.2f", value=preco_inicial)
            estoque = st.number_input("Estoque", min_value=0, step=1, value=estoque_inicial)

            submitted = st.form_submit_button("Salvar Produto")

            if submitted:
                if not nome.strip():
                    st.error("O nome do produto é obrigatório.")
                else:
                    dados = {
                        "nome": nome.strip(),
                        "descricao": descricao.strip(),
                        "preco": preco,
                        "estoque": estoque
                    }
                    if st.session_state.produto_editando:
                        dados["id"] = st.session_state.produto_editando.get("id")

                    sucesso = salvar_produto(dados)
                    if sucesso:
                        st.success("Produto salvo com sucesso!")
                        st.session_state.produto_editando = None
                        limpar_formulario_produto()
                        st.experimental_rerun()

    with col2:
        st.write("### Produtos Cadastrados")
        if produtos:
            for p in produtos:
                st.write(f"**{p['nome']}** - R$ {p['preco']:.2f}")
                col_edit, col_del = st.columns([1, 1])
                with col_edit:
                    if st.button(f"✏️ Editar {p['nome']}", key=f"edit_prod_{p['id']}"):
                        st.session_state.produto_editando = p
                        st.experimental_rerun()
                with col_del:
                    if st.button(f"❌ Excluir {p['nome']}", key=f"del_prod_{p['id']}"):
                        if excluir_produto(p["id"]):
                            st.success("Produto excluído.")
                            st.experimental_rerun()
        else:
            st.info("Nenhum produto cadastrado.")

