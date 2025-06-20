import streamlit as st
import sqlite3
from datetime import datetime, date
from streamlit_drawable_canvas import st_canvas
from PIL import Image
import io
import pandas as pd
import plotly.express as px
import shutil
import os

st.set_page_config(page_title="Studio de Depilação", layout="wide", initial_sidebar_state="expanded")

DB_PATH = "studio.db"
BACKUP_DIR = "backups"
BACKUP_LOG = "backup_log.txt"

def realizar_backup():
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(BACKUP_DIR, f"studio_backup_{timestamp}.db")
    shutil.copy2(DB_PATH, backup_path)
    with open(BACKUP_LOG, "w") as f:
        f.write(datetime.now().strftime("%Y-%m-%d"))
    st.info(f"Backup automático realizado: {backup_path}")

def checar_backup():
    if not os.path.exists(BACKUP_LOG):
        realizar_backup()
        return
    with open(BACKUP_LOG, "r") as f:
        ultima_data_str = f.read().strip()
    try:
        ultima_data = datetime.strptime(ultima_data_str, "%Y-%m-%d").date()
    except:
        realizar_backup()
        return
    hoje = date.today()
    if (hoje - ultima_data).days >= 15:
        realizar_backup()

if not os.path.exists(DB_PATH):
    open(DB_PATH, 'a').close()

checar_backup()
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
cursor = conn.cursor()
# Criação das tabelas
cursor.execute("""CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY, usuario TEXT UNIQUE, senha TEXT)""")
cursor.execute("INSERT OR IGNORE INTO usuarios (id, usuario, senha) VALUES (1, 'admin', 'admin')")

cursor.execute("""CREATE TABLE IF NOT EXISTS clientes (
    id INTEGER PRIMARY KEY, nome TEXT, telefone TEXT, data_nascimento TEXT, instagram TEXT,
    cantor_favorito TEXT, bebida_favorita TEXT, assinatura BLOB)""")

cursor.execute("""CREATE TABLE IF NOT EXISTS ficha_avaliacao (
    id INTEGER PRIMARY KEY, cliente_id INTEGER,
    epilacao_anterio TEXT, alergia TEXT, qual_alergia TEXT, problema_pele TEXT,
    tratamento_dermatologico TEXT, tipo_pele TEXT, hidrata_pele TEXT, gravida TEXT,
    medicamento TEXT, qual_medicamento TEXT, dispositivo TEXT, diabete TEXT,
    pelos_encravados TEXT, cirurgia_recente TEXT, foliculite TEXT, qual_foliculite TEXT,
    outro_problema TEXT, qual_outro TEXT, autorizacao_imagem TEXT)""")

cursor.execute("""CREATE TABLE IF NOT EXISTS agendamentos (
    id INTEGER PRIMARY KEY, cliente_id INTEGER, servico TEXT, data TEXT, hora TEXT, status TEXT)""")

cursor.execute("""CREATE TABLE IF NOT EXISTS servicos (
    id INTEGER PRIMARY KEY, nome TEXT, descricao TEXT, duracao INTEGER, valor REAL)""")

cursor.execute("""CREATE TABLE IF NOT EXISTS produtos (
    id INTEGER PRIMARY KEY, nome TEXT, estoque INTEGER, valor REAL)""")

cursor.execute("""CREATE TABLE IF NOT EXISTS vendas (
    id INTEGER PRIMARY KEY, cliente_id INTEGER, data TEXT, forma_pagamento TEXT, total REAL)""")

cursor.execute("""CREATE TABLE IF NOT EXISTS vendas_itens (
    id INTEGER PRIMARY KEY, venda_id INTEGER, tipo TEXT, nome TEXT, quantidade INTEGER, preco REAL)""")

cursor.execute("""CREATE TABLE IF NOT EXISTS despesas (
    id INTEGER PRIMARY KEY, descricao TEXT, valor REAL, data TEXT)""")

conn.commit()

# Estilo e layout
st.markdown("""
<style>
body, .block-container {
    background-color: #fefbf6;
    color: #7c6f58;
    font-family: 'Georgia', serif;
}
.sidebar .sidebar-content {
    background-color: #fffaf0;
    padding-top: 20px;
}
.menu-btn {
    background-color: #f7f2e7;
    border: 2px solid #a18856;
    border-radius: 6px;
    color: #7c6f58;
    font-weight: 600;
    padding: 12px 16px;
    margin-bottom: 8px;
    width: 100%;
    cursor: pointer;
    text-align: left;
    transition: background-color 0.3s ease, color 0.3s ease;
}
.menu-btn:hover {
    background-color: #a18856;
    color: #fffaf0;
}
.menu-btn-selected {
    background-color: #7c6f58;
    color: #fefbf6;
    border-color: #7c6f58;
}
.sidebar .element-container img {
    display: block;
    margin-left: auto;
    margin-right: auto;
    width: 180px;
    padding-bottom: 15px;
    border-radius: 12px;
}
.stButton > button {
    border-radius: 6px !important;
}
.login-box {
    max-width: 400px;
    margin: 60px auto;
    padding: 30px;
    background: white;
    border-radius: 12px;
    box-shadow: 0 0 20px rgba(0,102,153,0.25);
    text-align: center;
}
.login-box img {
    border-radius: 10px;
    margin-bottom: 15px;
    max-width: 100%;
}
.login-box h2 {
    margin-bottom: 25px;
    color: #004466;
}
</style>
""", unsafe_allow_html=True)

# Função menu lateral com botões fixos
def menu_lateral_botao(opcoes, key):
    selected = st.session_state.get(key, opcoes[0])
    for opcao in opcoes:
        classe = "menu-btn"
        if opcao == selected:
            classe += " menu-btn-selected"
        if st.button(opcao, key=f"menu_{opcao}"):
            st.session_state[key] = opcao
            st.experimental_rerun()
    return st.session_state.get(key)

# Login
if "logado" not in st.session_state:
    st.session_state.logado = False

if not st.session_state.logado:
    st.markdown(f"""
    <div class="login-box">
        <img src="https://images.unsplash.com/photo-1588776814546-cded238c6846?auto=format&fit=crop&w=600&q=80" alt="Logo Studio" />
        <h2>Login - Studio de Depilação</h2>
    </div>
    """, unsafe_allow_html=True)
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
# Menu lateral com opções
menu_opcoes = [
    "Início", "Clientes", "Agendamentos", "Serviços",
    "Produtos", "Vendas", "Despesas", "Relatórios",
    "Importação", "Sair"
]

with st.sidebar:
    st.image("https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=400&q=80", use_column_width=True)
    st.markdown("### Priscila Santos Epilação")
    st.markdown("---")
    menu = menu_lateral_botao(menu_opcoes, "menu_selecionado")

# Página inicial
if menu == "Início":
    st.title("🌿 Bem-vinda ao Studio de Depilação")
    st.image("https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=800&q=80", use_column_width=True)
    st.markdown("Use o menu ao lado para navegar no sistema.")

# Cadastro de clientes + ficha de avaliação
elif menu == "Clientes":
    st.title("👩 Cadastro de Clientes + Ficha de Avaliação")
    with st.form("form_cadastro_cliente"):
        col1, col2 = st.columns(2)
        with col1:
            nome = st.text_input("Nome completo", key="nome_cliente")
            telefone = st.text_input("Telefone", key="telefone_cliente")
            data_nascimento = st.date_input("Data de nascimento", value=date(1990,1,1), max_value=date.today(), key="nascimento_cliente")
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
                    """INSERT INTO ficha_avaliacao (
                        cliente_id, epilacao_anterio, alergia, qual_alergia, problema_pele,
                        tratamento_dermatologico, tipo_pele, hidrata_pele, gravida, medicamento,
                        qual_medicamento, dispositivo, diabete, pelos_encravados, cirurgia_recente,
                        foliculite, qual_foliculite, outro_problema, qual_outro, autorizacao_imagem)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (cliente_id, epilacao, alergia, qual_alergia, problema_pele, tratamento, tipo_pele, hidrata,
                     gravida, medicamento, qual_medicamento, dispositivo, diabete, encravado, cirurgia,
                     foliculite, qual_foliculite, outro, qual_outro, imagem)
                )
                conn.commit()
                st.success("✅ Cadastro salvo com sucesso!")
elif menu == "Agendamentos":
    st.title("📆 Agendamentos")

    with st.form("form_agendamento"):
        clientes = cursor.execute("SELECT id, nome FROM clientes").fetchall()
        servicos = cursor.execute("SELECT nome FROM servicos").fetchall()

        if not clientes:
            st.warning("⚠️ Nenhum cliente cadastrado.")
            st.stop()
        if not servicos:
            st.warning("⚠️ Nenhum serviço cadastrado.")
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
            st.success("✅ Agendamento registrado com sucesso.")

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
    st.title("📝 Serviços")

    with st.form("form_servicos"):
        nome = st.text_input("Nome do serviço")
        descricao = st.text_area("Descrição")
        duracao = st.number_input("Duração (minutos)", min_value=1, step=1)
        valor = st.number_input("Valor R$", min_value=0.0, step=0.1, format="%.2f")

        if st.form_submit_button("Cadastrar Serviço"):
            if not nome.strip():
                st.error("O nome do serviço é obrigatório.")
            else:
                cursor.execute(
                    "INSERT INTO servicos (nome, descricao, duracao, valor) VALUES (?, ?, ?, ?)",
                    (nome, descricao, duracao, valor)
                )
                conn.commit()
                st.success("✅ Serviço cadastrado com sucesso.")

    st.markdown("### 📋 Lista de Serviços Cadastrados")
    servicos = cursor.execute("SELECT id, nome, descricao, duracao, valor FROM servicos").fetchall()
    if servicos:
        for s in servicos:
            st.write(f"**{s[1]}** — {s[2]} | ⏱️ {s[3]} min | 💰 R$ {s[4]:.2f}")
    else:
        st.info("Nenhum serviço cadastrado ainda.")
elif menu == "Produtos":
    st.title("📦 Produtos")

    with st.form("form_produtos"):
        nome = st.text_input("Nome do produto")
        estoque = st.number_input("Estoque", min_value=0, step=1)
        valor = st.number_input("Valor R$", min_value=0.0, step=0.1, format="%.2f")

        if st.form_submit_button("Cadastrar Produto"):
            if not nome.strip():
                st.error("O nome do produto é obrigatório.")
            else:
                cursor.execute(
                    "INSERT INTO produtos (nome, estoque, valor) VALUES (?, ?, ?)",
                    (nome, estoque, valor)
                )
                conn.commit()
                st.success("✅ Produto cadastrado com sucesso.")

    st.markdown("### 📋 Estoque de Produtos")
    produtos = cursor.execute("SELECT id, nome, estoque, valor FROM produtos").fetchall()
    if produtos:
        for p in produtos:
            st.write(f"**{p[1]}** — Estoque: {p[2]} | 💰 R$ {p[3]:.2f}")
    else:
        st.info("Nenhum produto cadastrado ainda.")
elif menu == "Vendas":
    st.title("💳 Vendas")

    clientes = cursor.execute("SELECT id, nome FROM clientes").fetchall()
    servicos = cursor.execute("SELECT nome, valor FROM servicos").fetchall()
    produtos = cursor.execute("SELECT nome, valor, estoque FROM produtos").fetchall()

    if not clientes or (not servicos and not produtos):
        st.warning("Cadastre clientes, serviços e produtos para realizar vendas.")
        st.stop()

    with st.form("form_venda"):
        cliente = st.selectbox("Cliente", clientes, format_func=lambda x: x[1])
        forma_pagamento = st.selectbox("Forma de pagamento", ["Dinheiro", "Cartão", "Pix"])

        st.markdown("### Produtos")
        produto_selecionado = st.selectbox("Produto", [p[0] for p in produtos])
        quantidade_prod = st.number_input("Quantidade", min_value=1, step=1, key="qtd_produto")

        st.markdown("### Serviços")
        servico_selecionado = st.selectbox("Serviço", [s[0] for s in servicos])
        quantidade_serv = st.number_input("Quantidade", min_value=1, step=1, key="qtd_servico")

        if st.form_submit_button("Finalizar Venda"):
            idx_prod = [p[0] for p in produtos].index(produto_selecionado)
            estoque_atual = produtos[idx_prod][2]
            valor_prod = produtos[idx_prod][1]

            if estoque_atual < quantidade_prod:
                st.error("Estoque insuficiente para o produto selecionado.")
            else:
                total = valor_prod * quantidade_prod

                idx_serv = [s[0] for s in servicos].index(servico_selecionado)
                valor_serv = servicos[idx_serv][1]
                total += valor_serv * quantidade_serv

                cursor.execute(
                    "INSERT INTO vendas (cliente_id, data, forma_pagamento, total) VALUES (?, ?, ?, ?)",
                    (cliente[0], str(date.today()), forma_pagamento, total)
                )
                venda_id = cursor.lastrowid

                cursor.execute(
                    "INSERT INTO vendas_itens (venda_id, tipo, nome, quantidade, preco) VALUES (?, ?, ?, ?, ?)",
                    (venda_id, "Produto", produto_selecionado, quantidade_prod, valor_prod)
                )
                cursor.execute(
                    "INSERT INTO vendas_itens (venda_id, tipo, nome, quantidade, preco) VALUES (?, ?, ?, ?, ?)",
                    (venda_id, "Serviço", servico_selecionado, quantidade_serv, valor_serv)
                )

                novo_estoque = estoque_atual - quantidade_prod
                cursor.execute("UPDATE produtos SET estoque = ? WHERE nome = ?", (novo_estoque, produto_selecionado))

                conn.commit()
                st.success(f"Venda finalizada. Total: R$ {total:.2f}")
elif menu == "Despesas":
    st.title("📉 Controle de Despesas")

    with st.form("form_despesas"):
        descricao = st.text_input("Descrição")
        valor = st.number_input("Valor R$", min_value=0.0, step=0.1, format="%.2f")
        data_despesa = st.date_input("Data", max_value=date.today())

        if st.form_submit_button("Registrar Despesa"):
            if not descricao.strip():
                st.error("A descrição é obrigatória.")
            else:
                cursor.execute(
                    "INSERT INTO despesas (descricao, valor, data) VALUES (?, ?, ?)",
                    (descricao, valor, str(data_despesa))
                )
                conn.commit()
                st.success("Despesa registrada com sucesso.")

    despesas = cursor.execute("SELECT descricao, valor, data FROM despesas ORDER BY data DESC").fetchall()
    df_despesas = pd.DataFrame(despesas, columns=["Descrição", "Valor", "Data"])
    st.dataframe(df_despesas)
elif menu == "Relatórios":
    st.title("📊 Relatórios")

    tipo_rel = st.selectbox("Tipo de relatório", ["Vendas", "Despesas"])
    data_ini = st.date_input("Data inicial", value=date(2023, 1, 1))
    data_fim = st.date_input("Data final", value=date.today())

    if data_ini > data_fim:
        st.error("Data inicial não pode ser maior que a data final.")
        st.stop()

    if tipo_rel == "Vendas":
        query = """
            SELECT v.data, v.forma_pagamento, v.total, c.nome
            FROM vendas v
            LEFT JOIN clientes c ON v.cliente_id = c.id
            WHERE date(v.data) BETWEEN ? AND ?
        """
        df = pd.read_sql_query(query, conn, params=(str(data_ini), str(data_fim)))

        if df.empty:
            st.warning("Nenhum dado de vendas encontrado no período.")
        else:
            st.dataframe(df)
            fig = px.bar(df.groupby('data').sum().reset_index(), x='data', y='total', title="Total de Vendas por Dia")
            st.plotly_chart(fig)

    else:  # Despesas
        query = """
            SELECT descricao, valor, data
            FROM despesas
            WHERE date(data) BETWEEN ? AND ?
        """
        df = pd.read_sql_query(query, conn, params=(str(data_ini), str(data_fim)))

        if df.empty:
            st.warning("Nenhum dado de despesas encontrado no período.")
        else:
            st.dataframe(df)
            fig = px.bar(df.groupby('data').sum().reset_index(), x='data', y='valor', title="Despesas por Dia")
            st.plotly_chart(fig)
elif menu == "Importação":
    st.title("📥 Importação de Dados")
    st.warning("⚠️ Importar um arquivo de backup substituirá o banco atual. Faça backup antes!")

    uploaded_file = st.file_uploader("Selecione o arquivo de backup (.db)", type=["db"])

    if uploaded_file is not None:
        if st.button("Importar backup"):
            with open(DB_PATH, "wb") as f:
                f.write(uploaded_file.getbuffer())
            st.success("Backup importado com sucesso! Reinicie o sistema para aplicar as mudanças.")
            st.stop()
elif menu == "Sair":
    st.session_state.logado = False
    st.experimental_rerun()

# Ajuste geral largura e padding para melhor visualização
st.markdown("""
<style>
    .main .block-container {
        max-width: 1100px;
        padding-left: 2rem;
        padding-right: 2rem;
    }
</style>
""", unsafe_allow_html=True)
