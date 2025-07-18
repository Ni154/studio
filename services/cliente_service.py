import streamlit as st
from supabase import Client
from datetime import datetime
from utils.pdf_generator import gerar_pdf_cliente  # Função para criar PDF (deve existir em utils/pdf_generator.py)
from utils.form_helpers import limpar_formulario    # Função para limpar formulário

def listar_clientes(supabase: Client):
    response = supabase.table("clientes").select("*").order("nome", ascending=True).execute()
    if response.status_code == 200:
        return response.data
    else:
        st.error("Erro ao carregar clientes")
        return []

def cadastrar_cliente(supabase: Client, dados: dict):
    dados['created_at'] = datetime.utcnow().isoformat()
    response = supabase.table("clientes").insert(dados).execute()
    if response.status_code == 201:
        return response.data[0]  # Retorna cliente cadastrado
    else:
        st.error("Erro ao cadastrar cliente")
        return None

def atualizar_cliente(supabase: Client, cliente_id: int, dados: dict):
    dados['updated_at'] = datetime.utcnow().isoformat()
    response = supabase.table("clientes").update(dados).eq("id", cliente_id).execute()
    if response.status_code == 200:
        return True
    else:
        st.error("Erro ao atualizar cliente")
        return False

def excluir_cliente(supabase: Client, cliente_id: int):
    response = supabase.table("clientes").delete().eq("id", cliente_id).execute()
    if response.status_code == 200:
        return True
    else:
        st.error("Erro ao excluir cliente")
        return False

def carregar_cliente(supabase: Client, cliente_id: int):
    response = supabase.table("clientes").select("*").eq("id", cliente_id).single().execute()
    if response.status_code == 200:
        return response.data
    else:
        st.error("Erro ao carregar cliente")
        return None

def formulario_cadastro_cliente():
    with st.form("form_cliente", clear_on_submit=False):
        nome = st.text_input("Nome")
        telefone = st.text_input("Telefone")
        email = st.text_input("Email")
        endereco = st.text_area("Endereço")

        st.markdown("### Ficha de Anamnese")
        alergias = st.text_area("Alergias")
        medicacoes = st.text_area("Medicações")
        doencas_cronicas = st.text_area("Doenças Crônicas")
        outras_informacoes = st.text_area("Outras Informações")

        enviado = st.form_submit_button("Salvar Cliente")
        
        dados_cliente = {
            "nome": nome,
            "telefone": telefone,
            "email": email,
            "endereco": endereco,
            "anamnese": {
                "alergias": alergias,
                "medicacoes": medicacoes,
                "doencas_cronicas": doencas_cronicas,
                "outras_informacoes": outras_informacoes
            }
        }
        
        return enviado, dados_cliente

def cadastro_cliente_interface(supabase: Client):
    st.subheader("Cadastro de Clientes")
    
    # Carregar clientes para edição ou exclusão
    clientes = listar_clientes(supabase)
    clientes_dict = {c["nome"]: c["id"] for c in clientes}
    
    cliente_selecionado = st.selectbox("Selecionar cliente para editar ou excluir", [""] + list(clientes_dict.keys()))
    
    if cliente_selecionado:
        cliente_id = clientes_dict[cliente_selecionado]
        dados_atual = carregar_cliente(supabase, cliente_id)
        if dados_atual:
            with st.form("form_editar_cliente", clear_on_submit=False):
                nome = st.text_input("Nome", value=dados_atual["nome"])
                telefone = st.text_input("Telefone", value=dados_atual.get("telefone", ""))
                email = st.text_input("Email", value=dados_atual.get("email", ""))
                endereco = st.text_area("Endereço", value=dados_atual.get("endereco", ""))
                
                anamnese = dados_atual.get("anamnese", {})
                alergias = st.text_area("Alergias", value=anamnese.get("alergias", ""))
                medicacoes = st.text_area("Medicações", value=anamnese.get("medicacoes", ""))
                doencas_cronicas = st.text_area("Doenças Crônicas", value=anamnese.get("doencas_cronicas", ""))
                outras_informacoes = st.text_area("Outras Informações", value=anamnese.get("outras_informacoes", ""))
                
                atualizar = st.form_submit_button("Atualizar Cliente")
                excluir = st.form_submit_button("Excluir Cliente")
                
                if atualizar:
                    dados_atualizar = {
                        "nome": nome,
                        "telefone": telefone,
                        "email": email,
                        "endereco": endereco,
                        "anamnese": {
                            "alergias": alergias,
                            "medicacoes": medicacoes,
                            "doencas_cronicas": doencas_cronicas,
                            "outras_informacoes": outras_informacoes
                        }
                    }
                    if atualizar_cliente(supabase, cliente_id, dados_atualizar):
                        st.success("Cliente atualizado com sucesso!")
                        st.experimental_rerun()
                
                if excluir:
                    if excluir_cliente(supabase, cliente_id):
                        st.success("Cliente excluído com sucesso!")
                        st.experimental_rerun()
    
    else:
        enviado, dados = formulario_cadastro_cliente()
        if enviado:
            cliente_novo = cadastrar_cliente(supabase, dados)
            if cliente_novo:
                st.success("Cliente cadastrado com sucesso!")
                gerar_pdf_cliente(cliente_novo)  # Gera PDF com dados e ficha
                limpar_formulario("form_cliente")  # Limpa o formulário para próximo cadastro
                st.experimental_rerun()
