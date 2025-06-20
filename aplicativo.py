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

# --- Menu lateral fixo e estilizado ---
def menu_lateral(opcao_atual):
    st.markdown("""
    <style>
    .menu-lateral {
        position: fixed;
        top: 0;
        left: 0;
        height: 100vh;
        width: 180px;
        background-color: #e3edf4;
        padding: 20px 10px;
        display: flex;
        flex-direction: column;
        gap: 12px;
        box-shadow: 2px 0 5px rgba(0,0,0,0.1);
        z-index: 100;
    }
    .botao-menu {
        padding: 10px 15px;
        border-radius: 0;
        border: none;
        font-size: 16px;
        font-weight: 600;
        background-color: #0099cc;
        color: white;
        cursor: pointer;
        width: 100%;
        text-align: left;
        display: flex;
        align-items: center;
        gap: 8px;
        transition: background-color 0.2s ease;
    }
    .botao-menu:hover {
        background-color: #007399;
    }
    .botao-menu-selecionado {
        background-color: #005f73 !important;
    }
    .conteudo {
        margin-left: 200px;
        padding: 20px;
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
        classe = "botao-menu"
        if opcao_atual == nome:
            classe += " botao-menu-selecionado"
        if st.button(f"{icone}  {nome}", key=f"menu_{nome}"):
            st.session_state.menu_selecionado = nome

if "menu_selecionado" not in st.session_state:
    st.session_state.menu_selecionado = "Início"

# Renderiza menu lateral fixo
st.markdown('<div class="menu-lateral">', unsafe_allow_html=True)
menu_lateral(st.session_state.menu_selecionado)
st.markdown('</div>', unsafe_allow_html=True)

# Conteúdo principal com margem à esquerda para não ficar atrás do menu
st.markdown('<div class="conteudo">', unsafe_allow_html=True)

menu = st.session_state.menu_selecionado

if menu == "Início":
    st.title("🌿 Bem-vinda ao Studio de Depilação")
    st.markdown("Use o menu lateral para navegar no sistema.")

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

    st.markdown("### Serviços Cadastrados")
    servicos = cursor.execute("SELECT id, nome, descricao, duracao, valor FROM servicos").fetchall()
    for s in servicos:
        st.write(f"**{s[1]}** - {s[2]} - Duração: {s[3]} min - R$ {s[4]:.2f}")

elif menu == "Produtos":
    st.title("📦 Cadastro de Produtos")
    with st.form("form_produto"):
        nome_prod = st.text_input("Nome do Produto", key="nome_produto")
        estoque = st.number_input("Estoque", min_value=0, step=1, key="estoque_produto")
        valor_prod = st.number_input("Valor (R$)", step=0.5, min_value=0.0, key="valor_produto")
        if st.form_submit_button("Salvar Produto"):
            cursor.execute(
                "INSERT INTO produtos (nome, estoque, valor) VALUES (?, ?, ?)",
                (nome_prod, estoque, valor_prod)
            )
            conn.commit()
            st.success("Produto salvo com sucesso!")

    st.markdown("### Produtos Cadastrados")
    produtos = cursor.execute("SELECT id, nome, estoque, valor FROM produtos").fetchall()
    for p in produtos:
        st.write(f"**{p[1]}** - Estoque: {p[2]} - R$ {p[3]:.2f}")

elif menu == "Vendas":
    st.title("💳 Painel de Vendas")
    clientes = cursor.execute("SELECT id, nome FROM clientes").fetchall()
    servicos = cursor.execute("SELECT nome, valor FROM servicos").fetchall()
    produtos = cursor.execute("SELECT nome, valor, estoque FROM produtos").fetchall()

    if not clientes:
        st.warning("Cadastre clientes antes de realizar vendas.")
        st.stop()

    with st.form("form_venda"):
        cliente_sel = st.selectbox("Cliente", clientes, format_func=lambda x: x[1], key="venda_cliente")
        forma_pagamento = st.selectbox("Forma de Pagamento", ["Pix", "Dinheiro", "Crédito", "Débito"], key="forma_pagamento")

        st.markdown("### Serviços")
        servicos_venda = {}
        for s in servicos:
            quantidade = st.number_input(f"{s[0]} (R$ {s[1]:.2f}) - Quantidade", min_value=0, max_value=10, step=0, key=f"servico_{s[0]}")
            if quantidade > 0:
                servicos_venda[s[0]] = {"quantidade": quantidade, "preco": s[1]}

        st.markdown("### Produtos")
        produtos_venda = {}
        for p in produtos:
            quantidade = st.number_input(f"{p[0]} (R$ {p[1]:.2f}, Estoque: {p[2]}) - Quantidade", min_value=0, max_value=p[2], step=0, key=f"produto_{p[0]}")
            if quantidade > 0:
                produtos_venda[p[0]] = {"quantidade": quantidade, "preco": p[1]}

        if st.form_submit_button("Finalizar Venda"):
            if not servicos_venda and not produtos_venda:
                st.warning("Adicione pelo menos um serviço ou produto à venda.")
            else:
                total = 0
                for s in servicos_venda.values():
                    total += s["quantidade"] * s["preco"]
                for p in produtos_venda.values():
                    total += p["quantidade"] * p["preco"]

                cursor.execute(
                    "INSERT INTO vendas (cliente_id, data, forma_pagamento, total) VALUES (?, ?, ?, ?)",
                    (cliente_sel[0], datetime.now().strftime("%Y-%m-%d %H:%M:%S"), forma_pagamento, total)
                )
                venda_id = cursor.lastrowid

                for nome_s, dados in servicos_venda.items():
                    cursor.execute(
                        "INSERT INTO vendas_itens (venda_id, tipo, nome, quantidade, preco) VALUES (?, ?, ?, ?, ?)",
                        (venda_id, "servico", nome_s, dados["quantidade"], dados["preco"])
                    )
                for nome_p, dados in produtos_venda.items():
                    cursor.execute(
                        "INSERT INTO vendas_itens (venda_id, tipo, nome, quantidade, preco) VALUES (?, ?, ?, ?, ?)",
                        (venda_id, "produto", nome_p, dados["quantidade"], dados["preco"])
                    )

                # Atualizar estoque
                for nome_p, dados in produtos_venda.items():
                    cursor.execute("UPDATE produtos SET estoque = estoque - ? WHERE nome = ?", (dados["quantidade"], nome_p))

                conn.commit()
                st.success(f"Venda finalizada! Total: R$ {total:.2f}")

elif menu == "Despesas":
    st.title("📉 Controle de Despesas")
    with st.form("form_despesas"):
        descricao = st.text_input("Descrição da despesa", key="descricao_despesa")
        valor = st.number_input("Valor (R$)", step=0.5, min_value=0.0, key="valor_despesa")
        data_despesa = st.date_input("Data", value=date.today(), key="data_despesa")
        if st.form_submit_button("Registrar Despesa"):
            cursor.execute(
                "INSERT INTO despesas (descricao, valor, data) VALUES (?, ?, ?)",
                (descricao, valor, str(data_despesa))
            )
            conn.commit()
            st.success("Despesa registrada com sucesso!")

    st.markdown("### Despesas Registradas")
    despesas = cursor.execute("SELECT descricao, valor, data FROM despesas ORDER BY data DESC").fetchall()
    for d in despesas:
        st.write(f"{d[2]} - {d[0]}: R$ {d[1]:.2f}")

elif menu == "Relatórios":
    st.title("📊 Relatórios")

    tipo_relatorio = st.selectbox("Tipo de relatório", ["Vendas", "Clientes", "Despesas"])

    data_inicio = st.date_input("Data início", value=date.today().replace(day=1))
    data_fim = st.date_input("Data fim", value=date.today())

    if st.button("Gerar relatório"):
        if tipo_relatorio == "Vendas":
            query = """
            SELECT v.data, c.nome, v.forma_pagamento, v.total
            FROM vendas v
            JOIN clientes c ON v.cliente_id = c.id
            WHERE date(v.data) BETWEEN ? AND ?
            ORDER BY v.data
            """
            df = pd.read_sql_query(query, conn, params=(str(data_inicio), str(data_fim)))
            st.dataframe(df)

            if not df.empty:
                fig = px.bar(df, x="data", y="total", title="Vendas no período")
                st.plotly_chart(fig)

        elif tipo_relatorio == "Clientes":
            query = """
            SELECT nome, telefone, data_nascimento FROM clientes
            """
            df = pd.read_sql_query(query, conn)
            st.dataframe(df)

        elif tipo_relatorio == "Despesas":
            query = """
            SELECT data, descricao, valor FROM despesas
            WHERE date(data) BETWEEN ? AND ?
            ORDER BY data
            """
            df = pd.read_sql_query(query, conn, params=(str(data_inicio), str(data_fim)))
            st.dataframe(df)

            if not df.empty:
                fig = px.bar(df, x="data", y="valor", title="Despesas no período")
                st.plotly_chart(fig)

elif menu == "Sair":
    st.session_state.logado = False
    st.experimental_rerun()

st.markdown('</div>', unsafe_allow_html=True)
