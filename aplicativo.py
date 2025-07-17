import streamlit as st
import pandas as pd
from datetime import datetime, date
from supabase import create_client, Client
from fpdf import FPDF
from urllib.parse import quote

# Configuração Supabase
SUPABASE_URL = "https://zgpfvrwsjsbsvevflypk.supabase.co"
SUPABASE_KEY = "sb_secret_VpH-6yfypCG-7cUS6ZnQgQ_hQgPxLdJ"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Funções auxiliares
def limpar_formulario(form_keys):
    for key in form_keys:
        if key in st.session_state:
            del st.session_state[key]

def gerar_pdf_cliente(dados_cliente, anamnese):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, f"Ficha do Cliente: {dados_cliente['nome']}", ln=True)
    pdf.set_font("Arial", size=12)
    pdf.ln(10)
    for campo, valor in dados_cliente.items():
        pdf.cell(0, 8, f"{campo.capitalize()}: {valor}", ln=True)
    pdf.ln(5)
    pdf.cell(0, 10, "Anamnese:", ln=True)
    pdf.set_font("Arial", size=11)
    for campo, valor in anamnese.items():
        pdf.cell(0, 8, f"{campo.capitalize()}: {valor}", ln=True)

    filename = f"ficha_cliente_{dados_cliente['nome'].replace(' ', '_')}.pdf"
    pdf.output(filename)
    return filename

# Função para carregar clientes do Supabase
def carregar_clientes():
    response = supabase.table("clientes").select("*").order("nome").execute()
    if response.status_code == 200:
        return response.data
    return []

# Função para excluir cliente e anamnese no Supabase
def excluir_cliente(cliente_id):
    supabase.table("anamnese").delete().eq("cliente_id", cliente_id).execute()
    supabase.table("clientes").delete().eq("id", cliente_id).execute()

# Função para salvar cliente + anamnese no Supabase
def salvar_cliente(dados_cliente, anamnese):
    # Inserir cliente
    res = supabase.table("clientes").insert(dados_cliente).execute()
    if res.status_code == 201:
        cliente_id = res.data[0]["id"]
        anamnese["cliente_id"] = cliente_id
        supabase.table("anamnese").insert(anamnese).execute()
        return True
    return False

# Função para atualizar cliente + anamnese no Supabase
def atualizar_cliente(cliente_id, dados_cliente, anamnese):
    supabase.table("clientes").update(dados_cliente).eq("id", cliente_id).execute()
    supabase.table("anamnese").update(anamnese).eq("cliente_id", cliente_id).execute()

# Menu principal
def menu_principal():
    st.sidebar.title("Menu")
    menu = st.sidebar.radio("Selecione uma opção:", [
        "Cadastro Clientes",
        "Cadastro Produtos",
        "Cadastro Serviços",
        "Agendamento",
        "Vendas",
        "Relatórios",
        "Cancelar Vendas",
        "Backup",
        "Sair"
    ])
    return menu

# Tela Cadastro Clientes
def cadastro_clientes():
    st.subheader("👤 Cadastro e Gerenciamento de Clientes")

    clientes = carregar_clientes()
    clientes_dict = {c["nome"]: c for c in clientes}

    col1, col2 = st.columns([2,3])

    with col1:
        with st.form("form_cliente", clear_on_submit=True):
            nome = st.text_input("Nome", key="nome")
            telefone = st.text_input("Telefone", key="telefone")
            email = st.text_input("Email", key="email")
            data_nascimento = st.date_input("Data de Nascimento", key="data_nascimento")
            endereco = st.text_input("Endereço", key="endereco")

            st.markdown("### Ficha de Anamnese")
            peso = st.number_input("Peso (kg)", min_value=0.0, step=0.1, key="peso")
            altura = st.number_input("Altura (m)", min_value=0.0, step=0.01, key="altura")
            pressao_arterial = st.text_input("Pressão Arterial", key="pressao_arterial")
            alergias = st.text_area("Alergias", key="alergias")
            outras_informacoes = st.text_area("Outras Informações", key="outras_informacoes")

            if st.form_submit_button("Salvar Cliente"):
                if not nome:
                    st.error("O nome é obrigatório.")
                else:
                    dados_cliente = {
                        "nome": nome,
                        "telefone": telefone,
                        "email": email,
                        "data_nascimento": data_nascimento.strftime("%Y-%m-%d"),
                        "endereco": endereco
                    }
                    anamnese = {
                        "peso": peso,
                        "altura": altura,
                        "pressao_arterial": pressao_arterial,
                        "alergias": alergias,
                        "outras_informacoes": outras_informacoes
                    }
                    sucesso = salvar_cliente(dados_cliente, anamnese)
                    if sucesso:
                        st.success("Cliente cadastrado com sucesso!")
                        # Gerar PDF ao salvar
                        pdf_file = gerar_pdf_cliente(dados_cliente, anamnese)
                        with open(pdf_file, "rb") as f:
                            st.download_button(
                                label="📄 Baixar Ficha PDF",
                                data=f,
                                file_name=pdf_file,
                                mime="application/pdf"
                            )
                        limpar_formulario(["nome", "telefone", "email", "data_nascimento", "endereco", 
                                          "peso", "altura", "pressao_arterial", "alergias", "outras_informacoes"])
                    else:
                        st.error("Erro ao salvar cliente.")

    with col2:
        st.write("### Clientes Cadastrados")
        if clientes:
            df_clientes = pd.DataFrame(clientes)
            df_clientes["data_nascimento"] = pd.to_datetime(df_clientes["data_nascimento"]).dt.strftime("%d/%m/%Y")
            st.dataframe(df_clientes[["nome", "telefone", "email", "data_nascimento", "endereco"]], use_container_width=True)

            cliente_selecionado = st.selectbox("Selecionar cliente para editar ou excluir", [""] + list(clientes_dict.keys()))

            if cliente_selecionado:
                cliente = clientes_dict[cliente_selecionado]
                cliente_id = cliente["id"]
                anamnese_res = supabase.table("anamnese").select("*").eq("cliente_id", cliente_id).execute()
                anamnese = anamnese_res.data[0] if anamnese_res.status_code == 200 and anamnese_res.data else {}

                novo_nome = st.text_input("Nome", value=cliente["nome"], key="edit_nome")
                novo_telefone = st.text_input("Telefone", value=cliente.get("telefone", ""), key="edit_telefone")
                novo_email = st.text_input("Email", value=cliente.get("email", ""), key="edit_email")
                nova_data_nasc = st.date_input("Data de Nascimento", value=datetime.strptime(cliente["data_nascimento"], "%Y-%m-%d").date(), key="edit_data_nasc")
                novo_endereco = st.text_input("Endereço", value=cliente.get("endereco", ""), key="edit_endereco")

                st.markdown("### Ficha de Anamnese")
                novo_peso = st.number_input("Peso (kg)", min_value=0.0, step=0.1, value=anamnese.get("peso", 0.0), key="edit_peso")
                nova_altura = st.number_input("Altura (m)", min_value=0.0, step=0.01, value=anamnese.get("altura", 0.0), key="edit_altura")
                nova_pressao = st.text_input("Pressão Arterial", value=anamnese.get("pressao_arterial", ""), key="edit_pressao")
                novas_alergias = st.text_area("Alergias", value=anamnese.get("alergias", ""), key="edit_alergias")
                novas_info = st.text_area("Outras Informações", value=anamnese.get("outras_informacoes", ""), key="edit_outras_info")

                col_botao1, col_botao2 = st.columns(2)
                with col_botao1:
                    if st.button("✏️ Atualizar Cliente"):
                        dados_atualizados = {
                            "nome": novo_nome,
                            "telefone": novo_telefone,
                            "email": novo_email,
                            "data_nascimento": nova_data_nasc.strftime("%Y-%m-%d"),
                            "endereco": novo_endereco
                        }
                        anamnese_atualizada = {
                            "peso": novo_peso,
                            "altura": nova_altura,
                            "pressao_arterial": nova_pressao,
                            "alergias": novas_alergias,
                            "outras_informacoes": novas_info
                        }
                        atualizar_cliente(cliente_id, dados_atualizados, anamnese_atualizada)
                        st.success("Cliente atualizado com sucesso!")
                        st.experimental_rerun()
                with col_botao2:
                    if st.button("❌ Excluir Cliente"):
                        excluir_cliente(cliente_id)
                        st.success("Cliente excluído com sucesso!")
                        st.experimental_rerun()


# Código principal
def main():
    st.title("Sistema de Gestão")
    menu = menu_principal()

    if menu == "Cadastro Clientes":
        cadastro_clientes()
    # Aqui as outras funções dos menus (Cadastro Produtos, Serviços, etc) seguem em próximas partes...

if __name__ == "__main__":
    main()
# --- Cadastro Produtos ---
def cadastro_produtos():
    st.subheader("📦 Cadastro e Gerenciamento de Produtos")

    response = supabase.table("produtos").select("*").order("nome").execute()
    produtos = response.data if response.status_code == 200 else []
    produtos_dict = {p["nome"]: p for p in produtos}

    col1, col2 = st.columns([2, 3])

    with col1:
        with st.form("form_produto", clear_on_submit=True):
            nome = st.text_input("Nome do produto", key="nome_produto")
            quantidade = st.number_input("Quantidade em estoque", min_value=0, step=1, key="quantidade_produto")
            preco_venda = st.number_input("Preço de venda (R$)", min_value=0.0, format="%.2f", key="preco_venda_produto")

            if st.form_submit_button("Salvar Produto"):
                if not nome:
                    st.error("O nome do produto é obrigatório.")
                else:
                    novo_produto = {
                        "nome": nome,
                        "quantidade": quantidade,
                        "preco_venda": preco_venda
                    }
                    res = supabase.table("produtos").insert(novo_produto).execute()
                    if res.status_code == 201:
                        st.success("Produto cadastrado com sucesso!")
                        limpar_formulario(["nome_produto", "quantidade_produto", "preco_venda_produto"])
                        st.experimental_rerun()
                    else:
                        st.error("Erro ao cadastrar produto.")

    with col2:
        st.write("### Produtos Cadastrados")
        if produtos:
            df_produtos = pd.DataFrame(produtos)
            st.dataframe(df_produtos[["nome", "quantidade", "preco_venda"]], use_container_width=True)

            produto_selecionado = st.selectbox("Selecionar produto para editar ou excluir", [""] + list(produtos_dict.keys()))

            if produto_selecionado:
                produto = produtos_dict[produto_selecionado]
                produto_id = produto["id"]

                novo_nome = st.text_input("Nome", value=produto["nome"], key="edit_nome_produto")
                nova_quantidade = st.number_input("Quantidade", min_value=0, step=1, value=produto["quantidade"], key="edit_quantidade_produto")
                novo_preco = st.number_input("Preço de venda (R$)", min_value=0.0, format="%.2f", value=produto["preco_venda"], key="edit_preco_produto")

                col_botao1, col_botao2 = st.columns(2)
                with col_botao1:
                    if st.button("✏️ Atualizar Produto"):
                        dados_atualizados = {
                            "nome": novo_nome,
                            "quantidade": nova_quantidade,
                            "preco_venda": novo_preco
                        }
                        supabase.table("produtos").update(dados_atualizados).eq("id", produto_id).execute()
                        st.success("Produto atualizado com sucesso!")
                        st.experimental_rerun()
                with col_botao2:
                    if st.button("❌ Excluir Produto"):
                        supabase.table("produtos").delete().eq("id", produto_id).execute()
                        st.success("Produto excluído com sucesso!")
                        st.experimental_rerun()


# --- Cadastro Serviços ---
def cadastro_servicos():
    st.subheader("💆 Cadastro e Gerenciamento de Serviços")

    response = supabase.table("servicos").select("*").order("nome").execute()
    servicos = response.data if response.status_code == 200 else []
    servicos_dict = {s["nome"]: s for s in servicos}

    col1, col2 = st.columns([2, 3])

    with col1:
        with st.form("form_servico", clear_on_submit=True):
            nome = st.text_input("Nome do serviço", key="nome_servico")
            unidade = st.text_input("Unidade (ex: sessão)", key="unidade_servico")
            quantidade = st.number_input("Quantidade disponível", min_value=0, step=1, key="quantidade_servico")
            valor = st.number_input("Valor do serviço (R$)", min_value=0.0, format="%.2f", key="valor_servico")

            if st.form_submit_button("Salvar Serviço"):
                if not nome:
                    st.error("O nome do serviço é obrigatório.")
                else:
                    novo_servico = {
                        "nome": nome,
                        "unidade": unidade,
                        "quantidade": quantidade,
                        "valor": valor
                    }
                    res = supabase.table("servicos").insert(novo_servico).execute()
                    if res.status_code == 201:
                        st.success("Serviço cadastrado com sucesso!")
                        limpar_formulario(["nome_servico", "unidade_servico", "quantidade_servico", "valor_servico"])
                        st.experimental_rerun()
                    else:
                        st.error("Erro ao cadastrar serviço.")

    with col2:
        st.write("### Serviços Cadastrados")
        if servicos:
            df_servicos = pd.DataFrame(servicos)
            st.dataframe(df_servicos[["nome", "unidade", "quantidade", "valor"]], use_container_width=True)

            servico_selecionado = st.selectbox("Selecionar serviço para editar ou excluir", [""] + list(servicos_dict.keys()))

            if servico_selecionado:
                servico = servicos_dict[servico_selecionado]
                servico_id = servico["id"]

                novo_nome = st.text_input("Nome", value=servico["nome"], key="edit_nome_servico")
                nova_unidade = st.text_input("Unidade", value=servico.get("unidade", ""), key="edit_unidade_servico")
                nova_quantidade = st.number_input("Quantidade", min_value=0, step=1, value=servico["quantidade"], key="edit_quantidade_servico")
                novo_valor = st.number_input("Valor (R$)", min_value=0.0, format="%.2f", value=servico["valor"], key="edit_valor_servico")

                col_botao1, col_botao2 = st.columns(2)
                with col_botao1:
                    if st.button("✏️ Atualizar Serviço"):
                        dados_atualizados = {
                            "nome": novo_nome,
                            "unidade": nova_unidade,
                            "quantidade": nova_quantidade,
                            "valor": novo_valor
                        }
                        supabase.table("servicos").update(dados_atualizados).eq("id", servico_id).execute()
                        st.success("Serviço atualizado com sucesso!")
                        st.experimental_rerun()
                with col_botao2:
                    if st.button("❌ Excluir Serviço"):
                        supabase.table("servicos").delete().eq("id", servico_id).execute()
                        st.success("Serviço excluído com sucesso!")
                        st.experimental_rerun()
# --- Agendamento ---
def agendamento():
    st.subheader("📅 Agendamento")

    response_clientes = supabase.table("clientes").select("*").order("nome").execute()
    clientes = response_clientes.data if response_clientes.status_code == 200 else []
    clientes_dict = {c["nome"]: c for c in clientes}

    # Estado para reagendar e cancelar
    if "reagendar_id" not in st.session_state:
        st.session_state["reagendar_id"] = None
    if "cancelar_id" not in st.session_state:
        st.session_state["cancelar_id"] = None

    # Reagendamento
    if st.session_state["reagendar_id"]:
        agendamento_id = st.session_state["reagendar_id"]
        res = supabase.table("agendamentos").select("id, cliente_id, data, hora, servicos").eq("id", agendamento_id).single().execute()
        ag = res.data if res.status_code == 200 else None

        if ag:
            cliente_nome = next((c["nome"] for c in clientes if c["id"] == ag["cliente_id"]), "Desconhecido")
            st.subheader("🔄 Reagendar Agendamento")
            st.write(f"Cliente: {cliente_nome}")
            st.write(f"Serviços: {ag['servicos']}")

            nova_data = st.date_input("Nova data", pd.to_datetime(ag["data"]).date())
            nova_hora = st.text_input("Nova hora", ag["hora"])

            if st.button("Confirmar Reagendamento"):
                supabase.table("agendamentos").update({
                    "data": nova_data.strftime("%Y-%m-%d"),
                    "hora": nova_hora,
                    "status": "Reagendado"
                }).eq("id", agendamento_id).execute()
                st.success("Agendamento reagendado com sucesso!")
                st.session_state["reagendar_id"] = None
                st.experimental_rerun()

            if st.button("Cancelar"):
                st.session_state["reagendar_id"] = None
                st.experimental_rerun()
        else:
            st.error("Agendamento não encontrado.")
        st.stop()

    # Cancelar agendamento
    if st.session_state["cancelar_id"]:
        cancelar_id = st.session_state["cancelar_id"]
        res = supabase.table("agendamentos").select("id, cliente_id, data, hora, servicos").eq("id", cancelar_id).single().execute()
        ag = res.data if res.status_code == 200 else None

        if ag:
            cliente_nome = next((c["nome"] for c in clientes if c["id"] == ag["cliente_id"]), "Desconhecido")
            st.subheader("❌ Cancelar Agendamento")
            st.write(f"Cliente: {cliente_nome}")
            st.write(f"Data: {pd.to_datetime(ag['data']).strftime('%d/%m/%Y')}")
            st.write(f"Hora: {ag['hora']}")
            st.write(f"Serviços: {ag['servicos']}")

            if st.button("Confirmar Cancelamento"):
                supabase.table("agendamentos").update({"status": "Cancelado"}).eq("id", cancelar_id).execute()
                st.success("Agendamento cancelado com sucesso!")
                st.session_state["cancelar_id"] = None
                st.experimental_rerun()

            if st.button("Voltar"):
                st.session_state["cancelar_id"] = None
                st.experimental_rerun()
        else:
            st.error("Agendamento não encontrado.")
        st.stop()

    # Novo agendamento
    cliente_selecionado = st.selectbox("Selecione o Cliente", [""] + list(clientes_dict.keys()))
    data_agendamento = st.date_input("Data do Agendamento", pd.Timestamp.today())
    hora_agendamento = st.text_input("Hora (ex: 14:30)")

    response_servicos = supabase.table("servicos").select("*").execute()
    servicos = response_servicos.data if response_servicos.status_code == 200 else []
    servicos_dict = {s["nome"]: s for s in servicos}

    servicos_selecionados = st.multiselect("Selecione os Serviços", list(servicos_dict.keys()))

    if st.button("Salvar Agendamento"):
        if cliente_selecionado == "":
            st.error("Selecione um cliente.")
        elif not hora_agendamento.strip():
            st.error("Informe a hora do agendamento.")
        elif not servicos_selecionados:
            st.error("Selecione ao menos um serviço.")
        else:
            cliente_id = clientes_dict[cliente_selecionado]["id"]
            data_str = data_agendamento.strftime("%Y-%m-%d")
            servicos_str = ", ".join(servicos_selecionados)

            supabase.table("agendamentos").insert({
                "cliente_id": cliente_id,
                "data": data_str,
                "hora": hora_agendamento,
                "servicos": servicos_str,
                "status": "Agendado"
            }).execute()

            st.success("Agendamento salvo!")
            st.experimental_rerun()

    st.markdown("---")
    st.subheader("📋 Lista de Agendamentos")

    data_filtro = st.date_input("Filtrar agendamentos a partir de", pd.Timestamp.today())
    data_filtro_str = data_filtro.strftime("%Y-%m-%d")

    res_agend = supabase.table("agendamentos").select("id, cliente_id, data, hora, servicos, status").gte("data", data_filtro_str).order("data", ascending=True).execute()
    agendamentos = res_agend.data if res_agend.status_code == 200 else []

    if agendamentos:
        for ag in agendamentos:
            cliente_nome = next((c["nome"] for c in clientes if c["id"] == ag["cliente_id"]), "Desconhecido")
            col1, col2, col3, col4, col5, col6 = st.columns([2,3,2,2,3,3])
            with col1:
                st.write(pd.to_datetime(ag["data"]).strftime("%d/%m/%Y"))
            with col2:
                st.write(cliente_nome)
            with col3:
                st.write(ag["hora"])
            with col4:
                st.write(ag["servicos"])
            with col5:
                st.write(ag["status"])
            with col6:
                if ag["status"] == "Agendado":
                    if st.button(f"Reagendar {ag['id']}"):
                        st.session_state["reagendar_id"] = ag["id"]
                        st.experimental_rerun()
                    if st.button(f"Cancelar {ag['id']}"):
                        st.session_state["cancelar_id"] = ag["id"]
                        st.experimental_rerun()

                    # WhatsApp
                    telefone = clientes_dict.get(cliente_nome, {}).get("telefone", "")
                    if telefone:
                        from urllib.parse import quote
                        data_fmt = pd.to_datetime(ag["data"]).strftime("%d/%m/%Y")
                        mensagem = (
                            f"Olá maravilhosa, passando para te lembrar que seu horário está marcado para {ag['hora']} "
                            f"do dia {data_fmt}. Estou te aguardando! 💛"
                        )
                        link = f"https://wa.me/55{telefone}?text={quote(mensagem)}"
                        st.markdown(f"[📲 Enviar WhatsApp]({link})", unsafe_allow_html=True)
    else:
        st.info("Nenhum agendamento encontrado a partir da data selecionada.")


# --- Vendas ---
def vendas():
    st.markdown("""
        <style>
            .stRadio > div { flex-direction: row !important; }
            .stButton button { width: 100%; font-weight: bold; }
        </style>
    """, unsafe_allow_html=True)

    st.title("💰 Painel de Vendas")
    st.markdown("---")

    opcao_venda = st.radio("Escolha o tipo de venda:", ["Venda por Agendamento", "Nova Venda"])

    response_clientes = supabase.table("clientes").select("*").order("nome").execute()
    clientes = response_clientes.data if response_clientes.status_code == 200 else []
    clientes_dict = {c["nome"]: c for c in clientes}

    response_produtos = supabase.table("produtos").select("*").gte("quantidade", 1).order("nome").execute()
    produtos = response_produtos.data if response_produtos.status_code == 200 else []
    produtos_dict = {p["nome"]: p for p in produtos}

    response_servicos = supabase.table("servicos").select("*").gte("quantidade", 1).order("nome").execute()
    servicos = response_servicos.data if response_servicos.status_code == 200 else []
    servicos_dict = {s["nome"]: s for s in servicos}

    if opcao_venda == "Venda por Agendamento":
        res_agend = supabase.table("agendamentos").select("id, cliente_id, data, hora, servicos").eq("status", "Agendado").order("data", ascending=True).execute()
        agendamentos = res_agend.data if res_agend.status_code == 200 else []

        agend_dict = {f"{pd.to_datetime(a['data']).strftime('%d/%m/%Y')} {a['hora']} - {next((c['nome'] for c in clientes if c['id']==a['cliente_id']), '')}": a for a in agendamentos}

        agendamento_selecionado = st.selectbox("Selecione o agendamento", [""] + list(agend_dict.keys()), key="agendamento")

        if agendamento_selecionado:
            ag = agend_dict[agendamento_selecionado]
            cliente_id = ag["cliente_id"]

            st.markdown(f"""
            **Cliente:** {next((c['nome'] for c in clientes if c['id']==cliente_id), '')}  
            **Data:** {pd.to_datetime(ag['data']).strftime('%d/%m/%Y')}  
            **Hora:** {ag['hora']}  
            **Serviços Agendados:** {ag['servicos']}
            """)

            servicos_agendados = [s.strip() for s in ag["servicos"].split(",") if s.strip()]
            itens_venda = []

            for serv_nome in servicos_agendados:
                servico = servicos_dict.get(serv_nome)
                if servico:
                    itens_venda.append({
                        "tipo": "servico",
                        "id": servico["id"],
                        "nome": serv_nome,
                        "quantidade": 1,
                        "preco": servico["valor"]
                    })

            st.markdown("---")
            st.markdown("### ➕ Adicionar Itens Extras")

            col1, col2 = st.columns(2)
            with col1:
                produtos_selecionados = st.multiselect("Produtos", list(produtos_dict.keys()), key="produtos_ag")
                for p in produtos_selecionados:
                    produto = produtos_dict[p]
                    itens_venda.append({
                        "tipo": "produto",
                        "id": produto["id"],
                        "nome": p,
                        "quantidade": 1,
                        "preco": produto["preco_venda"]
                    })
            with col2:
                servicos_selecionados = st.multiselect("Serviços", [s for s in servicos_dict.keys() if s not in servicos_agendados], key="servicos_ag")
                for s in servicos_selecionados:
                    servico = servicos_dict[s]
                    itens_venda.append({
                        "tipo": "servico",
                        "id": servico["id"],
                        "nome": s,
                        "quantidade": 1,
                        "preco": servico["valor"]
                    })

            st.markdown("---")
            st.markdown("### 🧾 Itens da Venda")
            total = 0
            for i, item in enumerate(itens_venda):
                qtd = st.number_input(f"{item['nome']} ({item['tipo']})", min_value=1, value=item["quantidade"], step=1, key=f"qtd_ag_{i}")
                itens_venda[i]["quantidade"] = qtd
                total += qtd * item["preco"]

            forma_pagamento = st.selectbox("Forma de pagamento", ["Dinheiro", "Cartão", "Pix"], key="fp_ag")

            st.success(f"Total: R$ {total:.2f}")

            if st.button("✅ Finalizar Venda", key="finalizar_ag"):
                if total > 0:
                    data_venda = pd.Timestamp.today().strftime("%Y-%m-%d")
                    res_venda = supabase.table("vendas").insert({
                        "cliente_id": cliente_id,
                        "data": data_venda,
                        "total": total,
                        "forma_pagamento": forma_pagamento,
                        "cancelada": False
                    }).execute()
                    venda_id = res_venda.data[0]["id"] if res_venda.status_code == 201 else None

                    if venda_id:
                        for item in itens_venda:
                            supabase.table("venda_itens").insert({
                                "venda_id": venda_id,
                                "tipo": item["tipo"],
                                "item_id": item["id"],
                                "quantidade": item["quantidade"],
                                "preco": item["preco"]
                            }).execute()

                            if item["tipo"] == "produto":
                                supabase.table("produtos").update({
                                    "quantidade": supabase.rpc("decrement_quantity", {
                                        "produto_id": item["id"],
                                        "quantidade": item["quantidade"]
                                    })
                                }).eq("id", item["id"]).execute()

                        supabase.table("agendamentos").update({"status": "Finalizado"}).eq("id", ag["id"]).execute()
                        st.success("🎉 Venda por agendamento realizada com sucesso!")
                        st.experimental_rerun()
                else:
                    st.error("Total da venda deve ser maior que zero.")

    else:
        st.markdown("### Nova Venda")

        cliente_selecionado = st.selectbox("Selecione o cliente", [""] + list(clientes_dict.keys()), key="cliente_nv")
        if cliente_selecionado:
            cliente_id = clientes_dict[cliente_selecionado]["id"]
            produtos_selecionados = st.multiselect("Produtos", list(produtos_dict.keys()), key="produtos_nv")
            servicos_selecionados = st.multiselect("Serviços", list(servicos_dict.keys()), key="servicos_nv")

            itens_venda = []
            for p in produtos_selecionados:
                produto = produtos_dict[p]
                itens_venda.append({
                    "tipo": "produto",
                    "id": produto["id"],
                    "nome": p,
                    "quantidade": 1,
                    "preco": produto["preco_venda"]
                })
            for s in servicos_selecionados:
                servico = servicos_dict[s]
                itens_venda.append({
                    "tipo": "servico",
                    "id": servico["id"],
                    "nome": s,
                    "quantidade": 1,
                    "preco": servico["valor"]
                })

            st.markdown("---")
            st.markdown("### 🧾 Itens da Venda")
            total = 0
            for i, item in enumerate(itens_venda):
                qtd = st.number_input(f"{item['nome']} ({item['tipo']})", min_value=1, value=item["quantidade"], step=1, key=f"qtd_nv_{i}")
                itens_venda[i]["quantidade"] = qtd
                total += qtd * item["preco"]

            forma_pagamento = st.selectbox("Forma de pagamento", ["Dinheiro", "Cartão", "Pix"], key="fp_nv")

            st.success(f"Total: R$ {total:.2f}")

            if st.button("✅ Finalizar Venda", key="finalizar_nv"):
                if total > 0:
                    data_venda = pd.Timestamp.today().strftime("%Y-%m-%d")
                    res_venda = supabase.table("vendas").insert({
                        "cliente_id": cliente_id,
                        "data": data_venda,
                        "total": total,
                        "forma_pagamento": forma_pagamento,
                        "cancelada": False
                    }).execute()
                    venda_id = res_venda.data[0]["id"] if res_venda.status_code == 201 else None

                    if venda_id:
                        for item in itens_venda:
                            supabase.table("venda_itens").insert({
                                "venda_id": venda_id,
                                "tipo": item["tipo"],
                                "item_id": item["id"],
                                "quantidade": item["quantidade"],
                                "preco": item["preco"]
                            }).execute()

                            if item["tipo"] == "produto":
                                supabase.table("produtos").update({
                                    "quantidade": supabase.rpc("decrement_quantity", {
                                        "produto_id": item["id"],
                                        "quantidade": item["quantidade"]
                                    })
                                }).eq("id", item["id"]).execute()

                        st.success("🎉 Venda realizada com sucesso!")
                        st.experimental_rerun()
                else:
                    st.error("Total da venda deve ser maior que zero.")
        else:
            st.warning("Selecione um cliente para continuar.")
# --- Relatórios ---
def relatorios():
    import pandas as pd

    st.subheader("📈 Relatórios Financeiros")

    data_inicio = st.date_input("Data Início", value=pd.to_datetime("today").replace(day=1))
    data_fim = st.date_input("Data Fim", value=pd.to_datetime("today"))

    if data_fim < data_inicio:
        st.error("A data final não pode ser anterior à data inicial.")
        return

    data_inicio_str = data_inicio.strftime("%Y-%m-%d")
    data_fim_str = data_fim.strftime("%Y-%m-%d")

    # Vendas por data
    vendas_rel = supabase.table("vendas")\
        .select("data, total")\
        .gte("data", data_inicio_str)\
        .lte("data", data_fim_str)\
        .eq("cancelada", False)\
        .execute()

    # Despesas por data
    despesas_rel = supabase.table("despesas")\
        .select("data, valor")\
        .gte("data", data_inicio_str)\
        .lte("data", data_fim_str)\
        .execute()

    df_vendas = pd.DataFrame(vendas_rel.data if vendas_rel.status_code == 200 else [])
    df_despesas = pd.DataFrame(despesas_rel.data if despesas_rel.status_code == 200 else [])

    if not df_vendas.empty:
        df_vendas["data"] = pd.to_datetime(df_vendas["data"])
        df_vendas = df_vendas.groupby("data").sum().reset_index()
    else:
        df_vendas = pd.DataFrame(columns=["data", "total"])

    if not df_despesas.empty:
        df_despesas["data"] = pd.to_datetime(df_despesas["data"])
        df_despesas = df_despesas.groupby("data").sum().reset_index()
    else:
        df_despesas = pd.DataFrame(columns=["data", "valor"])

    df = pd.merge(df_vendas, df_despesas, on="data", how="outer").fillna(0)
    df.rename(columns={"total": "Total_Vendas", "valor": "Total_Despesas", "data": "Data"}, inplace=True)
    df["Lucro"] = df["Total_Vendas"] - df["Total_Despesas"]
    df = df.sort_values("Data")

    st.line_chart(df.set_index("Data")[["Total_Vendas", "Total_Despesas", "Lucro"]])

    df["Data"] = df["Data"].dt.strftime("%d/%m/%Y")
    st.write("### Tabela de Resultados")
    st.dataframe(df, use_container_width=True)


# --- Cancelar Vendas ---
def cancelar_vendas():
    st.subheader("❌ Cancelar Vendas")

    vendas_ativas_res = supabase.table("vendas")\
        .select("id, cliente_id, data, total")\
        .eq("cancelada", False)\
        .order("data", desc=True)\
        .execute()
    vendas_ativas = vendas_ativas_res.data if vendas_ativas_res.status_code == 200 else []

    response_clientes = supabase.table("clientes").select("id, nome").execute()
    clientes = response_clientes.data if response_clientes.status_code == 200 else []
    clientes_dict = {c["id"]: c["nome"] for c in clientes}

    if not vendas_ativas:
        st.info("Nenhuma venda ativa para cancelar.")
        return

    opcoes_vendas = {
        f"ID: {v['id']} | Cliente: {clientes_dict.get(v['cliente_id'], '')} | Data: {v['data']} | Total: R$ {v['total']:.2f}": v["id"]
        for v in vendas_ativas
    }

    venda_selecionada = st.selectbox("Selecione a venda para cancelar", [""] + list(opcoes_vendas.keys()))

    if venda_selecionada:
        venda_id = opcoes_vendas[venda_selecionada]
        if st.button("Cancelar Venda"):
            cancelar_venda(venda_id)
            st.success("Venda cancelada com sucesso.")
            st.experimental_rerun()


def cancelar_venda(venda_id):
    supabase.table("vendas").update({"cancelada": True}).eq("id", venda_id).execute()


# --- Backup ---
def fazer_backup():
    import shutil
    import time
    import os

    st.info("Gerando backup...")

    # Como estamos usando Supabase, o backup ideal é exportar dados via API, mas aqui
    # simularemos exportação para um arquivo local

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    backup_filename = f"backup_{timestamp}.json"

    # Exportar tabelas principais
    tabelas = ["clientes", "agendamentos", "produtos", "servicos", "vendas", "venda_itens", "despesas"]

    backup_data = {}

    for tabela in tabelas:
        res = supabase.table(tabela).select("*").execute()
        if res.status_code == 200:
            backup_data[tabela] = res.data
        else:
            backup_data[tabela] = []

    import json
    with open(backup_filename, "w", encoding="utf-8") as f:
        json.dump(backup_data, f, ensure_ascii=False, indent=2)

    with open(backup_filename, "rb") as f:
        st.download_button(label="Clique para baixar o backup", data=f, file_name=backup_filename)

    # Limpar arquivo local após download (opcional)
    # os.remove(backup_filename)


# --- Excluir Cliente ---
def excluir_cliente(cliente_id):
    # Excluir agendamentos, vendas e histórico relacionados ao cliente
    supabase.table("agendamentos").delete().eq("cliente_id", cliente_id).execute()
    venda_res = supabase.table("vendas").select("id").eq("cliente_id", cliente_id).execute()
    vendas = venda_res.data if venda_res.status_code == 200 else []
    for v in vendas:
        supabase.table("venda_itens").delete().eq("venda_id", v["id"]).execute()
    supabase.table("vendas").delete().eq("cliente_id", cliente_id).execute()
    # Excluir cliente
    supabase.table("clientes").delete().eq("id", cliente_id).execute()


# --- Menu principal ---
def menu_principal():
    st.title("Sistema de Gestão - Menu Principal")
    menu = st.sidebar.selectbox("Menu", [
        "Início",
        "Cadastro Cliente",
        "Agendamento",
        "Vendas",
        "Relatórios",
        "Cancelar Vendas",
        "Backup",
        "Sair"
    ])

    if menu == "Início":
        st.write("Bem-vindo ao sistema!")

    elif menu == "Cadastro Cliente":
        cadastro_cliente()

    elif menu == "Agendamento":
        agendamento()

    elif menu == "Vendas":
        vendas()

    elif menu == "Relatórios":
        relatorios()

    elif menu == "Cancelar Vendas":
        cancelar_vendas()

    elif menu == "Backup":
        fazer_backup()

    elif menu == "Sair":
        st.session_state.login = False
        st.session_state.menu = "Início"
        st.experimental_rerun()


# --- Ponto de entrada ---
if __name__ == "__main__":
    if "login" not in st.session_state:
        st.session_state.login = False
    if not st.session_state.login:
        login()  # Função login (presumo que já exista)
    else:
        menu_principal()
