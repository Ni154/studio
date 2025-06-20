import os
import shutil
import streamlit as st
import sqlite3
from datetime import datetime, date
from streamlit_drawable_canvas import st_canvas
from PIL import Image
import io
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Studio de Depilação", layout="wide", initial_sidebar_state="expanded")

DB_PATH = "studio.db"
BACKUP_DIR = "backups"
BACKUP_LOG = "backup_log.txt"

# --- Função de backup ---
def realizar_backup():
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(BACKUP_DIR, f"studio_backup_{timestamp}.db")
    shutil.copy2(DB_PATH, backup_path)
    # Salva data do último backup
    with open(BACKUP_LOG, "w") as f:
        f.write(datetime.now().strftime("%Y-%m-%d"))
    st.success(f"Backup realizado com sucesso: {backup_path}")

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
    dias_passados = (hoje - ultima_data).days
    if dias_passados >= 15:
        realizar_backup()

# --- Backup automático ao iniciar ---
if os.path.exists(DB_PATH):
    checar_backup()
else:
    st.warning("Banco de dados não encontrado. Criando um novo banco.")

# --- Banco de dados ---
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
cursor = conn.cursor()

# --- Criar tabelas se não existirem ---
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

# --- Estilos para menu lateral ---
st.markdown("""
<style>
div.stRadio > label {
    display: block;
    width: 100%;
    background-color: #cce6ff;
    color: #004466;
    font-weight: 600;
    font-size: 16px;
    border-radius: 0;
    padding: 10px 15px;
    margin-bottom: 10px;
    cursor: pointer;
    border: 1px solid #004466;
    transition: background-color 0.3s ease;
}
div.stRadio > label:hover {
    background-color: #99ccff;
    color: #003355;
}
div.stRadio > label > input:checked + span {
    background-color: #004466 !important;
    color: white !important;
}
</style>
""", unsafe_allow_html=True)

# --- Menu lateral ---
menu_opcoes = [
    "Início", "Clientes", "Agendamentos", "Serviços",
    "Produtos", "Vendas", "Despesas", "Relatórios",
    "Importação", "Sair"
]

menu_selecionado = st.sidebar.radio("📋 Menu", menu_opcoes, index=menu_opcoes.index(st.session_state.get("menu", "Início")))
st.session_state.menu = menu_selecionado

menu = st.session_state.menu

# --- Páginas ---
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
    produtos = cursor.execute("SELECT nome, valor FROM produtos").fetchall()
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
            itens = [f"{p[0]} - R$ {p[1]:.2f}" for p in produtos]
        else:
            itens = [f"{s[0]} - R$ {s[1]:.2f}" for s in servicos]
        item_selecionado = st.selectbox("Item", itens, key="item_selecionado")

    qtd = st.number_input("Quantidade", min_value=1, step=1, key="quantidade_item")
    if st.button("Adicionar ao Carrinho", key="btn_add_carrinho"):
        nome_item = item_selecionado.split(" - ")[0]
        preco_item = float(item_selecionado.split("R$ ")[-1])
        st.session_state.carrinho.append({"tipo": item_tipo, "nome": nome_item, "quantidade": qtd, "preco": preco_item})
        st.success(f"{item_tipo} adicionado ao carrinho!")

    if st.session_state.carrinho:
        st.markdown("### 🧾 Carrinho")
        total = 0
        indices_remover = []
        for i, item in enumerate(st.session_state.carrinho):
            subtotal = item["quantidade"] * item["preco"]
            total += subtotal
            col1, col2 = st.columns([8, 1])
            with col1:
                st.write(f"{item['nome']} ({item['tipo']}) — {item['quantidade']} x R$ {item['preco']:.2f} = R$ {subtotal:.2f}")
            with col2:
                if st.button("Remover", key=f"remover_{i}"):
                    indices_remover.append(i)

        for i in reversed(indices_remover):
            st.session_state.carrinho.pop(i)
        st.markdown(f"**Total: R$ {total:.2f}**")

        forma_pagamento = st.selectbox("Forma de pagamento", ["Dinheiro", "Crédito", "Débito", "Pix"], key="forma_pagamento")

        if st.button("Finalizar Venda"):
            if not st.session_state.carrinho:
                st.warning("Carrinho vazio.")
            else:
                cursor.execute(
                    "INSERT INTO vendas (cliente_id, data, forma_pagamento, total) VALUES (?, ?, ?, ?)",
                    (cliente_venda[0], datetime.now().strftime("%Y-%m-%d %H:%M:%S"), forma_pagamento, total)
                )
                venda_id = cursor.lastrowid
                for item in st.session_state.carrinho:
                    cursor.execute(
                        "INSERT INTO vendas_itens (venda_id, tipo, nome, quantidade, preco) VALUES (?, ?, ?, ?, ?)",
                        (venda_id, item["tipo"], item["nome"], item["quantidade"], item["preco"])
                    )
                conn.commit()
                st.success("Venda realizada com sucesso!")
                st.session_state.carrinho = []

elif menu == "Despesas":
    st.title("📉 Controle de Despesas")
    with st.form("form_despesa"):
        descricao = st.text_input("Descrição", key="descricao_despesa")
        valor = st.number_input("Valor (R$)", min_value=0.01, step=0.01, key="valor_despesa")
        data_despesa = st.date_input("Data", value=date.today(), key="data_despesa")
        if st.form_submit_button("Registrar Despesa"):
            cursor.execute(
                "INSERT INTO despesas (descricao, valor, data) VALUES (?, ?, ?)",
                (descricao, valor, str(data_despesa))
            )
            conn.commit()
            st.success("Despesa registrada!")

    st.markdown("### 📋 Histórico de Despesas")
    despesas = cursor.execute("SELECT descricao, valor, data FROM despesas ORDER BY data DESC").fetchall()
    df_despesas = pd.DataFrame(despesas, columns=["Descrição", "Valor", "Data"])
    st.dataframe(df_despesas)

elif menu == "Relatórios":
    st.title("📊 Relatórios")
    st.markdown("Filtrar período:")
    data_inicio = st.date_input("Data início", value=date.today().replace(day=1), key="data_inicio")
    data_fim = st.date_input("Data fim", value=date.today(), key="data_fim")

    # Vendas no período
    vendas = cursor.execute(
        "SELECT v.data, v.forma_pagamento, v.total FROM vendas v WHERE date(v.data) BETWEEN ? AND ?",
        (str(data_inicio), str(data_fim))
    ).fetchall()

    df_vendas = pd.DataFrame(vendas, columns=["Data", "Forma de Pagamento", "Total"])
    st.markdown("### Vendas")
    st.dataframe(df_vendas)

    if not df_vendas.empty:
        fig_vendas = px.bar(df_vendas, x="Data", y="Total", color="Forma de Pagamento", title="Vendas por Data e Forma de Pagamento")
        st.plotly_chart(fig_vendas, use_container_width=True)
    else:
        st.info("Nenhuma venda encontrada no período.")

    # Despesas no período
    despesas = cursor.execute(
        "SELECT data, descricao, valor FROM despesas WHERE date(data) BETWEEN ? AND ?",
        (str(data_inicio), str(data_fim))
    ).fetchall()
    df_despesas = pd.DataFrame(despesas, columns=["Data", "Descrição", "Valor"])
    st.markdown("### Despesas")
    st.dataframe(df_despesas)

    if not df_despesas.empty:
        fig_despesas = px.pie(df_despesas, values="Valor", names="Descrição", title="Despesas por Descrição")
        st.plotly_chart(fig_despesas, use_container_width=True)
    else:
        st.info("Nenhuma despesa encontrada no período.")

elif menu == "Importação":
    st.title("📥 Importação de Dados")

    st.warning("""
    ⚠️ Ao importar um arquivo de banco, o banco atual será substituído completamente.
    Faça backup antes de continuar!
    """)

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
