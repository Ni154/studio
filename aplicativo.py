import streamlit as st
import sqlite3
from datetime import datetime, date
import base64
import io
import pandas as pd
import plotly.express as px
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# --- Banco de Dados ---
conn = sqlite3.connect('studio_beauty.db', check_same_thread=False)
cursor = conn.cursor()

def criar_tabelas():
    """Cria as tabelas no banco se não existirem"""
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario TEXT UNIQUE,
        senha TEXT
    )''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS clientes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        telefone TEXT,
        email TEXT,
        criado_em TEXT
    )''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS servicos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        descricao TEXT,
        duracao INTEGER,
        valor REAL
    )''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS vendas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cliente_id INTEGER,
        servico_id INTEGER,
        valor REAL,
        forma_pagamento TEXT,
        data TEXT,
        status TEXT DEFAULT 'ativo',
        FOREIGN KEY(cliente_id) REFERENCES clientes(id),
        FOREIGN KEY(servico_id) REFERENCES servicos(id)
    )''')

    conn.commit()

def criar_usuario_padrao():
    """Cria usuário padrão admin:1234 se não existir"""
    cursor.execute("SELECT * FROM usuarios WHERE usuario = 'admin'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO usuarios (usuario, senha) VALUES (?, ?)", ('admin', '1234'))
        conn.commit()

# --- Funções de login ---
def verificar_login(usuario, senha):
    cursor.execute("SELECT senha FROM usuarios WHERE usuario = ?", (usuario,))
    res = cursor.fetchone()
    return res is not None and res[0] == senha

# --- Funções clientes ---
def salvar_cliente(nome, telefone, email):
    criado_em = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("INSERT INTO clientes (nome, telefone, email, criado_em) VALUES (?, ?, ?, ?)", 
                   (nome, telefone, email, criado_em))
    conn.commit()

def carregar_clientes():
    cursor.execute("SELECT id, nome FROM clientes ORDER BY nome")
    return cursor.fetchall()

# --- Funções serviços ---
def salvar_servico(nome, descricao, duracao, valor):
    cursor.execute("INSERT INTO servicos (nome, descricao, duracao, valor) VALUES (?, ?, ?, ?)", 
                   (nome, descricao, duracao, valor))
    conn.commit()

def carregar_servicos():
    cursor.execute("SELECT id, nome, valor FROM servicos ORDER BY nome")
    return cursor.fetchall()

# --- Funções vendas ---
def salvar_venda(cliente_id, servico_id, valor, forma_pagamento):
    data = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('''
        INSERT INTO vendas (cliente_id, servico_id, valor, forma_pagamento, data)
        VALUES (?, ?, ?, ?, ?)
    ''', (cliente_id, servico_id, valor, forma_pagamento, data))
    conn.commit()

def carregar_vendas(data_inicio=None, data_fim=None):
    query = '''
    SELECT v.id, c.nome, s.nome, v.valor, v.forma_pagamento, v.data, v.status
    FROM vendas v
    JOIN clientes c ON v.cliente_id = c.id
    JOIN servicos s ON v.servico_id = s.id
    WHERE v.status = 'ativo'
    '''
    params = []
    if data_inicio and data_fim:
        query += " AND date(v.data) BETWEEN ? AND ?"
        params = [data_inicio, data_fim]
    query += " ORDER BY v.data DESC"
    cursor.execute(query, params)
    return cursor.fetchall()

def cancelar_venda(id_venda):
    cursor.execute("UPDATE vendas SET status = 'cancelado' WHERE id = ?", (id_venda,))
    conn.commit()

# --- PDF relatório ---
def gerar_pdf_vendas(data_inicio, data_fim):
    vendas = carregar_vendas(data_inicio, data_fim)
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    largura, altura = letter

    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, altura - 50, f"Relatório de Vendas de {data_inicio} até {data_fim}")

    y = altura - 80
    c.setFont("Helvetica", 12)
    for v in vendas:
        texto = f"ID {v[0]} | Cliente: {v[1]} | Serviço: {v[2]} | Valor: R$ {v[3]:.2f} | Pgto: {v[4]} | Data: {v[5]}"
        c.drawString(50, y, texto)
        y -= 15
        if y < 50:
            c.showPage()
            y = altura - 50
    c.save()
    buffer.seek(0)
    return buffer

# --- Estilização do login ---
def estilo_login():
    st.markdown("""
        <style>
        .title {
            font-family: 'Brush Script MT', cursive;
            font-size: 40px;
            color: #D6336C;
            font-weight: bold;
            text-align: center;
            margin-bottom: 20px;
        }
        </style>
    """, unsafe_allow_html=True)

# --- Aplicar estilo personalizado para botões e sidebar ---
def aplicar_estilos(cor="#D6336C"):
    st.markdown(f"""
    <style>
    /* Cor do fundo da sidebar */
    .css-1aumxhk {{
        background-color: {cor};
        color: white;
    }}
    /* Estilo do botão */
    .stButton>button {{
        background-color: {cor} !important;
        color: white !important;
        border-radius: 8px;
        padding: 8px 16px;
        font-weight: bold;
        margin-top: 10px;
    }}
    /* Cor do fundo da sidebar (alternativo) */
    .stSidebar .css-1aumxhk {{
        background-color: {cor};
        color: white;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- Página Login ---
def pagina_login():
    estilo_login()
    st.markdown('<div class="title">Priscila Santos Epilação</div>', unsafe_allow_html=True)
    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if verificar_login(usuario, senha):
            st.session_state["login"] = True
            st.session_state["usuario"] = usuario
            st.success(f"Bem-vindo(a) {usuario}!")
            st.experimental_rerun()
        else:
            st.error("Usuário ou senha incorretos")

# --- Página Dashboard ---
def pagina_dashboard():
    aplicar_estilos()
    st.title("Dashboard Financeiro")
    st.markdown("### Filtrar período das vendas")

    data_inicio = st.date_input("Data início", value=date.today().replace(day=1))
    data_fim = st.date_input("Data fim", value=date.today())

    if data_inicio > data_fim:
        st.error("Data início não pode ser maior que data fim.")
        return

    vendas = carregar_vendas(data_inicio.strftime("%Y-%m-%d"), data_fim.strftime("%Y-%m-%d"))
    if not vendas:
        st.info("Nenhuma venda registrada neste período.")
        return

    df = pd.DataFrame(vendas, columns=["ID", "Cliente", "Serviço", "Valor", "Pagamento", "Data", "Status"])
    df['Data'] = pd.to_datetime(df['Data'])
    st.dataframe(df)

    # Gráfico total vendido por dia
    vendas_por_dia = df.groupby(df['Data'].dt.date)['Valor'].sum().reset_index()
    fig = px.bar(vendas_por_dia, x='Data', y='Valor', title='Vendas por Dia (R$)')
    st.plotly_chart(fig, use_container_width=True)

    # Botão para gerar PDF
    if st.button("Gerar Relatório PDF"):
        pdf = gerar_pdf_vendas(data_inicio.strftime("%Y-%m-%d"), data_fim.strftime("%Y-%m-%d"))
        b64 = base64.b64encode(pdf.read()).decode()
        href = f'<a href="data:application/octet-stream;base64,{b64}" download="relatorio_vendas.pdf">Download Relatório Vendas PDF</a>'
        st.markdown(href, unsafe_allow_html=True)

# --- Página Clientes ---
def pagina_clientes():
    aplicar_estilos()
    st.title("Cadastro de Clientes")
    with st.form("form_cliente"):
        nome = st.text_input("Nome *")
        telefone = st.text_input("Telefone")
        email = st.text_input("Email")
        submitted = st.form_submit_button("Salvar Cliente")
        if submitted:
            if not nome.strip():
                st.error("O nome é obrigatório.")
            else:
                salvar_cliente(nome, telefone, email)
                st.success("Cliente salvo com sucesso!")

    st.markdown("### Clientes cadastrados")
    clientes = carregar_clientes()
    if clientes:
        for c in clientes:
            st.write(f"ID: {c[0]} - Nome: {c[1]}")
    else:
        st.info("Nenhum cliente cadastrado.")

# --- Página Serviços ---
def pagina_servicos():
    aplicar_estilos()
    st.title("Cadastro de Serviços")
    with st.form("form_servico"):
        nome = st.text_input("Nome do Serviço *")
        descricao = st.text_area("Descrição")
        duracao = st.number_input("Duração (minutos)", min_value=1)
        valor = st.number_input("Valor (R$)", min_value=0.0, format="%.2f")
        submitted = st.form_submit_button("Salvar Serviço")
        if submitted:
            if not nome.strip():
                st.error("Nome do serviço é obrigatório.")
            else:
                salvar_servico(nome, descricao, duracao, valor)
                st.success("Serviço salvo com sucesso!")

    st.markdown("### Serviços cadastrados")
    servicos = carregar_servicos()
    if servicos:
        for s in servicos:
            st.write(f"ID: {s[0]} - Nome: {s[1]} - Valor: R$ {s[2]:.2f}")
    else:
        st.info("Nenhum serviço cadastrado.")

# --- Página Vendas ---
def pagina_vendas():
    aplicar_estilos()
    st.title("Registrar Venda")
    clientes = carregar_clientes()
    servicos = carregar_servicos()

    if not clientes:
        st.warning("Cadastre clientes antes de registrar vendas.")
        return
    if not servicos:
        st.warning("Cadastre serviços antes de registrar vendas.")
        return

    with st.form("form_venda"):
        cliente = st.selectbox("Cliente", clientes, format_func=lambda x: x[1])
        servico = st.selectbox("Serviço", servicos, format_func=lambda x: x[1])
        forma_pagamento = st.selectbox("Forma de Pagamento", ["Pix", "Dinheiro", "Cartão Crédito", "Cartão Débito"])
        submitted = st.form_submit_button("Registrar Venda")
        if submitted:
            valor = servico[2]
            salvar_venda(cliente[0], servico[0], valor, forma_pagamento)
            st.success("Venda registrada com sucesso!")

    # Mostrar histórico das últimas 20 vendas
    st.markdown("### Últimas Vendas Registradas")
    vendas = carregar_vendas()
    if vendas:
        df = pd.DataFrame(vendas[:20], columns=["ID", "Cliente", "Serviço", "Valor", "Pagamento", "Data", "Status"])
        st.dataframe(df)
        for v in vendas[:20]:
            if st.button(f"Cancelar Venda {v[0]}"):
                cancelar_venda(v[0])
                st.warning("Venda cancelada")
                st.experimental_rerun()
    else:
        st.info("Nenhuma venda registrada.")

# --- Botão Sair ---
def botao_sair():
    if st.sidebar.button("Sair"):
        st.session_state["login"] = False
        st.experimental_rerun()

# --- Função principal ---
def main():
    st.set_page_config(page_title="Sistema Estúdio de Beleza", layout="wide")

    criar_tabelas()
    criar_usuario_padrao()

    if "login" not in st.session_state:
        st.session_state["login"] = False

    if not st.session_state["login"]:
        pagina_login()
        return

    # Mostrar botão sair na sidebar
    st.sidebar.title(f"Olá, {st.session_state.get('usuario', '')}")
    botao_sair()

    # Menu lateral com radio buttons
    menu = st.sidebar.radio("Menu", ["Dashboard", "Clientes", "Serviços", "Vendas"])

    # Navegação das páginas
    if menu == "Dashboard":
        pagina_dashboard()
    elif menu == "Clientes":
        pagina_clientes()
    elif menu == "Serviços":
        pagina_servicos()
    elif menu == "Vendas":
        pagina_vendas()

if __name__ == "__main__":
    main()
