import streamlit as st
import sqlite3
from datetime import datetime, date
from streamlit_drawable_canvas import st_canvas
from PIL import Image
import io
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Studio de Depilação", layout="wide", initial_sidebar_state="expanded")

# --- Banco de dados ---
conn = sqlite3.connect("studio.db", check_same_thread=False)
cursor = conn.cursor()

# Criação das tabelas (se não existirem)
cursor.execute("""
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY, usuario TEXT UNIQUE, senha TEXT
)""")
cursor.execute("INSERT OR IGNORE INTO usuarios (id, usuario, senha) VALUES (1, 'admin', 'admin')")

cursor.execute("""
CREATE TABLE IF NOT EXISTS clientes (
    id INTEGER PRIMARY KEY, nome TEXT, telefone TEXT, data_nascimento TEXT, instagram TEXT,
    cantor_favorito TEXT, bebida_favorita TEXT, assinatura BLOB
)""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS ficha_avaliacao (
    id INTEGER PRIMARY KEY, cliente_id INTEGER,
    epilacao_anterio TEXT, alergia TEXT, qual_alergia TEXT, problema_pele TEXT,
    tratamento_dermatologico TEXT, tipo_pele TEXT, hidrata_pele TEXT, gravida TEXT,
    medicamento TEXT, qual_medicamento TEXT, dispositivo TEXT, diabete TEXT,
    pelos_encravados TEXT, cirurgia_recente TEXT, foliculite TEXT, qual_foliculite TEXT,
    outro_problema TEXT, qual_outro TEXT, autorizacao_imagem TEXT
)""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS agendamentos (
    id INTEGER PRIMARY KEY, cliente_id INTEGER, servico TEXT, data TEXT, hora TEXT, status TEXT
)""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS servicos (
    id INTEGER PRIMARY KEY, nome TEXT, descricao TEXT, duracao INTEGER, valor REAL
)""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS produtos (
    id INTEGER PRIMARY KEY, nome TEXT, estoque INTEGER, valor REAL
)""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS vendas (
    id INTEGER PRIMARY KEY, cliente_id INTEGER, data TEXT, forma_pagamento TEXT, total REAL
)""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS vendas_itens (
    id INTEGER PRIMARY KEY, venda_id INTEGER, tipo TEXT, nome TEXT, quantidade INTEGER, preco REAL
)""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS despesas (
    id INTEGER PRIMARY KEY, descricao TEXT, valor REAL, data TEXT
)""")

conn.commit()

# --- Login ---
if "logado" not in st.session_state:
    st.session_state.logado = False

if not st.session_state.logado:
    st.title("🔐 Login")
    usuario = st.text_input("Usuário", key="login_usuario")
    senha = st.text_input("Senha", type="password", key="login_senha")
    if st.button("Entrar", key="btn_entrar"):
        cursor.execute("SELECT * FROM usuarios WHERE usuario=? AND senha=?", (usuario, senha))
        resultado = cursor.fetchone()
        if resultado:
            st.session_state.logado = True
            st.experimental_rerun()
        else:
            st.error("Usuário ou senha inválidos.")
    st.stop()

# --- Menu lateral fixo com botões estilizados ---
if "menu_selecionado" not in st.session_state:
    st.session_state.menu_selecionado = "Início"

def menu_lateral():
    st.markdown("""
    <style>
    /* Ajusta largura da sidebar */
    [data-testid="stSidebar"] {
        width: 220px;
        padding-top: 1rem;
    }
    /* Botões do menu */
    div[data-testid="stSidebar"] button {
        background-color: #0288d1 !important;
        color: white !important;
        border-radius: 0 !important;
        padding: 12px 20px !important;
        margin-bottom: 8px !important;
        font-weight: 600 !important;
        border: none !important;
        width: 100% !important;
        cursor: pointer !important;
        text-align: left !important;
        display: flex !important;
        align-items: center !important;
        gap: 10px !important;
        font-size: 16px !important;
        transition: background-color 0.3s ease !important;
    }
    div[data-testid="stSidebar"] button:hover {
        background-color: #0277bd !important;
        color: white !important;
    }
    .menu-btn-selected {
        background-color: #01579b !important;
    }
    </style>
    """, unsafe_allow_html=True)

    opcoes = [
        ("Início", "🏠"),
        ("Clientes", "👩"),
        ("Agendamentos", "📅"),
        ("Serviços", "📝"),
        ("Produtos", "📦"),
        ("Vendas", "💳"),
        ("Despesas", "📉"),
        ("Relatórios", "📊"),
        ("Sair", "🚪")
    ]

    for nome, icone in opcoes:
        # Se é o menu selecionado, adiciona classe CSS
        key = f"menu_{nome}"
        label = f"{icone}  {nome}"

        # Para indicar visualmente o selecionado, adicionaremos um pequeno truque:
        if st.session_state.menu_selecionado == nome:
            # Botão selecionado (usaremos st.markdown com HTML para simular botão ativo)
            clicked = st.sidebar.button(label, key=key)
            st.sidebar.markdown(f"""<style>
                div.stButton > button#{key} {{
                    background-color: #01579b !important;
                }}
            </style>""", unsafe_allow_html=True)
        else:
            clicked = st.sidebar.button(label, key=key)

        if clicked:
            st.session_state.menu_selecionado = nome
            st.experimental_rerun()

menu_lateral()

# --- Conteúdo das páginas ---
menu = st.session_state.menu_selecionado

if menu == "Início":
    st.title("🌿 Bem-vinda ao Studio de Depilação")
    st.markdown("Use o menu à esquerda para navegar no sistema.")

elif menu == "Clientes":
    st.title("👩 Cadastro de Clientes + Ficha de Avaliação")
    with st.form("form_cadastro_cliente"):
        col1, col2 = st.columns(2)
        with col1:
            nome = st.text_input("Nome completo", key="nome_cliente")
            telefone = st.text_input("Telefone", key="telefone_cliente")
            data_nascimento = st.date_input("Data de nascimento", value=date.today(), key="nascimento_cliente")
            instagram = st.text_input("Instagram", key="instagram_cliente")
        with col2:
            cantor = st.text_input("Cantor favorito", key="cantor_cliente")
            bebida = st.text_input("Bebida favorita", key="bebida_cliente")

        st.markdown("### ✍️ Assinatura Digital")
        canvas_result = st_canvas(
            fill_color="rgba(255,255,255,0)", stroke_width=2,
            stroke_color="#000", background_color="#fff", height=150,
            drawing_mode="freedraw", key="canvas_assinatura"
        )
        assinatura_bytes = None
        if canvas_result.image_data is not None:
            img = canvas_result.image_data
            buffered = io.BytesIO()
            Image.fromarray((img[:, :, :3]).astype('uint8')).save(buffered, format="PNG")
            assinatura_bytes = buffered.getvalue()

        st.markdown("### 📋 Anamnese")
        col1, col2 = st.columns(2)
        with col1:
            epilacao = st.radio("Já fez epilação na cera?", ["SIM", "NÃO"], key="epilacao")
            alergia = st.radio("Possui alergia?", ["SIM", "NÃO"], key="alergia")
            qual_alergia = st.text_input("Qual?", disabled=(alergia == "NÃO"), key="qual_alergia")
            problema_pele = st.radio("Problemas de pele?", ["SIM", "NÃO"], key="problema_pele")
            tratamento = st.radio("Em tratamento dermatológico?", ["SIM", "NÃO"], key="tratamento")
            tipo_pele = st.selectbox("Tipo de pele", ["SECA", "OLEOSA", "NORMAL"], key="tipo_pele")
            hidrata = st.radio("Hidrata a pele?", ["SIM", "NÃO"], key="hidrata")
            gravida = st.radio("Está grávida?", ["SIM", "NÃO"], key="gravida")
        with col2:
            medicamento = st.radio("Usa medicamento?", ["SIM", "NÃO"], key="medicamento")
            qual_medicamento = st.text_input("Qual?", disabled=(medicamento == "NÃO"), key="qual_medicamento")
            dispositivo = st.selectbox("Dispositivo?", ["DIU", "Marca-passo", "Nenhum"], key="dispositivo")
            diabete = st.radio("Diabetes?", ["SIM", "NÃO"], key="diabete")
            encravado = st.radio("Pelos encravados?", ["SIM", "NÃO"], key="encravado")
            cirurgia = st.radio("Cirurgia recente?", ["SIM", "NÃO"], key="cirurgia")
            foliculite = st.radio("Foliculite?", ["SIM", "NÃO"], key="foliculite")
            qual_foliculite = st.text_input("Qual?", disabled=(foliculite == "NÃO"), key="qual_foliculite")
            outro = st.radio("Outro problema?", ["SIM", "NÃO"], key="outro")
            qual_outro = st.text_input("Qual?", disabled=(outro == "NÃO"), key="qual_outro")
            imagem = st.radio("Autoriza uso de imagem?", ["SIM", "NÃO"], key="imagem")

        if st.form_submit_button("Salvar Cadastro"):
            # Validação simples
            if not nome.strip():
                st.error("O nome do cliente é obrigatório.")
            else:
                cursor.execute(
                    """INSERT INTO clientes (nome, telefone, data_nascimento, instagram, cantor_favorito, bebida_favorita, assinatura)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (nome, telefone, str(data_nascimento), instagram, cantor, bebida, assinatura_bytes)
                )
                cliente_id = cursor.lastrowid

                cursor.execute(
                    """INSERT INTO ficha_avaliacao (cliente_id, epilacao_anterio, alergia, qual_alergia, problema_pele,
                    tratamento_dermatologico, tipo_pele, hidrata_pele, gravida, medicamento, qual_medicamento, dispositivo,
                    diabete, pelos_encravados, cirurgia_recente, foliculite, qual_foliculite, outro_problema, qual_outro, autorizacao_imagem)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (cliente_id, epilacao, alergia, qual_alergia, problema_pele, tratamento, tipo_pele, hidrata,
                     gravida, medicamento, qual_medicamento, dispositivo, diabete, encravado, cirurgia,
                     foliculite, qual_foliculite, outro, qual_outro, imagem)
                )
                conn.commit()
                st.success("Cadastro salvo com sucesso!")

elif menu == "Agendamentos":
    st.title("📆 Agendamentos")
    with st.form("form_agendamento"):
        clientes = cursor.execute("SELECT id, nome FROM clientes").fetchall()
        servicos = cursor.execute("SELECT nome FROM servicos").fetchall()

        if not clientes:
            st.warning("Nenhum cliente cadastrado.")
            st.stop()
        if not servicos:
            st.warning("Nenhum serviço cadastrado.")
            st.stop()

        cliente = st.selectbox("Cliente", clientes, format_func=lambda x: f"{x[1]}", key="agendamento_cliente")
        servico = st.selectbox("Serviço", [s[0] for s in servicos], key="agendamento_servico")
        data_agenda = st.date_input("Data", min_value=date.today(), key="agendamento_data")
        hora = st.time_input("Hora", key="agendamento_hora")

        if st.form_submit_button("Agendar"):
            cursor.execute(
                "INSERT INTO agendamentos (cliente_id, servico, data, hora, status) VALUES (?, ?, ?, ?, ?)",
                (cliente[0], servico, str(data_agenda), str(hora), "Ativo")
            )
            conn.commit()
            st.success("Agendamento registrado.")

    st.markdown("### 📋 Agendamentos Ativos")
    agendamentos = cursor.execute("""
        SELECT a.id, c.nome, a.servico, a.data, a.hora
        FROM agendamentos a
        JOIN clientes c ON c.id = a.cliente_id
        WHERE a.status = 'Ativo'
        ORDER BY a.data, a.hora
    """).fetchall()

    for ag in agendamentos:
        col1, col2 = st.columns([4, 1])
        with col1:
            st.write(f"👤 **{ag[1]}** — {ag[2]} em {ag[3]} às {ag[4]}")
        with col2:
            if st.button("❌ Cancelar", key=f"cancelar_{ag[0]}"):
                cursor.execute("UPDATE agendamentos SET status = 'Cancelado' WHERE id = ?", (ag[0],))
                conn.commit()
                st.experimental_rerun()

elif menu == "Serviços":
    st.title("📝 Cadastro de Serviços")
    with st.form("form_servico"):
        nome_serv = st.text_input("Nome do Serviço", key="nome_servico")
        desc_serv = st.text_area("Descrição", key="desc_servico")
        duracao = st.number_input("Duração (em minutos)", step=5, min_value=5, key="duracao_servico")
        valor = st.number_input("Valor (R$)", step=0.5, min_value=0.0, key="valor_servico")
        if st.form_submit_button("Salvar Serviço"):
            cursor.execute(
                "INSERT INTO servicos (nome, descricao, duracao, valor) VALUES (?, ?, ?, ?)",
                (nome_serv, desc_serv, duracao, valor)
            )
            conn.commit()
            st.success("Serviço salvo com sucesso!")

    st.markdown("### 📋 Lista de Serviços")
    servicos = cursor.execute("SELECT nome, descricao, duracao, valor FROM servicos").fetchall()
    for s in servicos:
        st.write(f"**{s[0]}** — {s[1]} | ⏱️ {s[2]} min | 💰 R$ {s[3]:.2f}")

elif menu == "Produtos":
    st.title("📦 Cadastro de Produtos")
    with st.form("form_produto"):
        nome_prod = st.text_input("Nome do Produto", key="nome_produto")
        estoque = st.number_input("Estoque", step=1, min_value=0, key="estoque_produto")
        valor_prod = st.number_input("Valor (R$)", step=0.5, min_value=0.0, key="valor_produto")
        if st.form_submit_button("Salvar Produto"):
            cursor.execute(
                "INSERT INTO produtos (nome, estoque, valor) VALUES (?, ?, ?)",
                (nome_prod, estoque, valor_prod)
            )
            conn.commit()
            st.success("Produto salvo com sucesso!")

    st.markdown("### 📋 Lista de Produtos")
    produtos = cursor.execute("SELECT nome, estoque, valor FROM produtos").fetchall()
    for p in produtos:
        st.write(f"**{p[0]}** — Estoque: {p[1]} | 💰 R$ {p[2]:.2f}")

elif menu == "Vendas":
    st.title("💳 Painel de Vendas")

    clientes = cursor.execute("SELECT id, nome FROM clientes").fetchall()
    produtos = cursor.execute("SELECT nome, valor, estoque FROM produtos").fetchall()
    servicos = cursor.execute("SELECT nome, valor FROM servicos").fetchall()

    if not clientes:
        st.warning("Cadastre pelo menos um cliente para iniciar vendas.")
        st.stop()

    cliente_venda = st.selectbox("Cliente", clientes, format_func=lambda x: x[1], key="cliente_venda")

    st.markdown("### 🛒 Adicionar ao Carrinho")
    if "carrinho" not in st.session_state:
        st.session_state.carrinho = []

    col1, col2 = st.columns(2)
    with col1:
        item_tipo = st.radio("Tipo", ["Produto", "Serviço"], key="tipo_item")
    with col2:
        if item_tipo == "Produto":
            itens = [f"{p[0]} (R$ {p[1]:.2f} | estoque: {p[2]})" for p in produtos]
            selecionado = st.selectbox("Produto", itens, key="item_venda")
        else:
            itens = [f"{s[0]} (R$ {s[1]:.2f})" for s in servicos]
            selecionado = st.selectbox("Serviço", itens, key="item_venda")

    quantidade = st.number_input("Quantidade", min_value=1, step=1, key="quantidade_venda")

    if st.button("Adicionar ao Carrinho", key="btn_add_carrinho"):
        nome_item = selecionado.split(" (")[0]
        if item_tipo == "Produto":
            # Verifica estoque
            estoque_idx = [p[0] for p in produtos].index(nome_item)
            estoque_disponivel = produtos[estoque_idx][2]
            if quantidade > estoque_disponivel:
                st.error("Quantidade maior que o estoque disponível.")
            else:
                st.session_state.carrinho.append({"tipo": "Produto", "nome": nome_item, "quantidade": quantidade,
                                                  "preco": produtos[estoque_idx][1]})
                st.success(f"{quantidade}x {nome_item} adicionado(s) ao carrinho.")
        else:
            preco_serv = [s[1] for s in servicos if s[0] == nome_item][0]
            st.session_state.carrinho.append({"tipo": "Serviço", "nome": nome_item, "quantidade": quantidade,
                                              "preco": preco_serv})
            st.success(f"{quantidade}x {nome_item} adicionado(s) ao carrinho.")

    st.markdown("### 🛍️ Carrinho")
    total = 0
    if st.session_state.carrinho:
        for idx, item in enumerate(st.session_state.carrinho):
            st.write(f"{item['quantidade']}x {item['nome']} ({item['tipo']}) — R$ {item['preco']*item['quantidade']:.2f}")
            total += item['preco']*item['quantidade']

            if st.button("Remover", key=f"remover_{idx}"):
                st.session_state.carrinho.pop(idx)
                st.experimental_rerun()

        st.markdown(f"**Total: R$ {total:.2f}**")

        forma_pag = st.selectbox("Forma de pagamento", ["Dinheiro", "Cartão Crédito", "Cartão Débito", "Pix"], key="forma_pag")
        if st.button("Finalizar Venda", key="btn_finalizar_venda"):
            if not st.session_state.carrinho:
                st.error("O carrinho está vazio.")
            else:
                # Grava venda
                cursor.execute(
                    "INSERT INTO vendas (cliente_id, data, forma_pagamento, total) VALUES (?, ?, ?, ?)",
                    (cliente_venda[0], datetime.now().strftime("%Y-%m-%d %H:%M:%S"), forma_pag, total)
                )
                venda_id = cursor.lastrowid

                # Grava itens
                for item in st.session_state.carrinho:
                    cursor.execute(
                        "INSERT INTO vendas_itens (venda_id, tipo, nome, quantidade, preco) VALUES (?, ?, ?, ?, ?)",
                        (venda_id, item["tipo"], item["nome"], item["quantidade"], item["preco"])
                    )
                # Atualiza estoque dos produtos vendidos
                for item in st.session_state.carrinho:
                    if item["tipo"] == "Produto":
                        cursor.execute("UPDATE produtos SET estoque = estoque - ? WHERE nome = ?", (item["quantidade"], item["nome"]))

                conn.commit()
                st.success("Venda finalizada com sucesso!")
                st.session_state.carrinho = []

    else:
        st.info("O carrinho está vazio.")

elif menu == "Despesas":
    st.title("📉 Controle de Despesas")
    with st.form("form_despesas"):
        descricao = st.text_input("Descrição", key="descricao_despesa")
        valor = st.number_input("Valor (R$)", step=0.5, min_value=0.0, key="valor_despesa")
        data_despesa = st.date_input("Data", value=date.today(), key="data_despesa")

        if st.form_submit_button("Registrar Despesa"):
            cursor.execute("INSERT INTO despesas (descricao, valor, data) VALUES (?, ?, ?)",
                           (descricao, valor, str(data_despesa)))
            conn.commit()
            st.success("Despesa registrada com sucesso!")

    st.markdown("### Histórico de Despesas")
    despesas = cursor.execute("SELECT descricao, valor, data FROM despesas ORDER BY data DESC").fetchall()
    for d in despesas:
        st.write(f"{d[2]} — {d[0]} — R$ {d[1]:.2f}")

elif menu == "Relatórios":
    st.title("📊 Relatórios")

    st.markdown("### Filtrar por período")
    data_inicio = st.date_input("Data início", value=date.today().replace(day=1), key="data_inicio_rel")
    data_fim = st.date_input("Data fim", value=date.today(), key="data_fim_rel")

    # Vendas no período
    vendas = cursor.execute("""
        SELECT v.data, v.total, c.nome
        FROM vendas v
        JOIN clientes c ON c.id = v.cliente_id
        WHERE date(v.data) BETWEEN ? AND ?
        ORDER BY v.data
    """, (str(data_inicio), str(data_fim))).fetchall()

    df_vendas = pd.DataFrame(vendas, columns=["Data", "Total", "Cliente"])
    if not df_vendas.empty:
        st.markdown("#### Vendas")
        fig_vendas = px.bar(df_vendas, x="Data", y="Total", hover_data=["Cliente"], title="Vendas por data")
        st.plotly_chart(fig_vendas, use_container_width=True)
    else:
        st.info("Nenhuma venda registrada nesse período.")

    # Despesas no período
    despesas = cursor.execute("""
        SELECT data, valor, descricao FROM despesas
        WHERE date(data) BETWEEN ? AND ?
        ORDER BY data
    """, (str(data_inicio), str(data_fim))).fetchall()
    df_despesas = pd.DataFrame(despesas, columns=["Data", "Valor", "Descrição"])
    if not df_despesas.empty:
        st.markdown("#### Despesas")
        fig_despesas = px.pie(df_despesas, values="Valor", names="Descrição", title="Despesas por tipo")
        st.plotly_chart(fig_despesas, use_container_width=True)
    else:
        st.info("Nenhuma despesa registrada nesse período.")

elif menu == "Sair":
    st.session_state.logado = False
    st.experimental_rerun()

else:
    st.write("Página não encontrada.")

