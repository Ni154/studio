# app.py
import streamlit as st
import sqlite3
from datetime import datetime
import base64
import io
from PIL import Image
from streamlit_drawable_canvas import st_canvas
import pandas as pd
import plotly.express as px
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch

# --- Banco ---
conn = sqlite3.connect('studio_beauty.db', check_same_thread=False)
cursor = conn.cursor()

def criar_tabelas():
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
        anamnese TEXT,
        bebida_preferida TEXT,
        gosto_musical TEXT,
        assinatura TEXT,
        foto BLOB,
        status TEXT DEFAULT 'ativo',
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
    CREATE TABLE IF NOT EXISTS produtos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        descricao TEXT,
        preco_custo REAL,
        preco_venda REAL,
        quantidade INTEGER
    )''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS agendamentos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cliente_id INTEGER,
        servico_id INTEGER,
        data_hora TEXT,
        status TEXT DEFAULT 'ativo',
        criado_em TEXT,
        FOREIGN KEY(cliente_id) REFERENCES clientes(id),
        FOREIGN KEY(servico_id) REFERENCES servicos(id)
    )''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS vendas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cliente_id INTEGER,
        servico_id INTEGER,
        produto_id INTEGER,
        quantidade INTEGER,
        valor REAL,
        forma_pagamento TEXT,
        data TEXT,
        status TEXT DEFAULT 'ativo',
        FOREIGN KEY(cliente_id) REFERENCES clientes(id),
        FOREIGN KEY(servico_id) REFERENCES servicos(id),
        FOREIGN KEY(produto_id) REFERENCES produtos(id)
    )''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS despesas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        descricao TEXT,
        valor REAL,
        data TEXT,
        quantidade INTEGER,
        observacao TEXT
    )''')

    conn.commit()

criar_tabelas()

def verificar_login(usuario, senha):
    cursor.execute("SELECT senha FROM usuarios WHERE usuario = ?", (usuario,))
    res = cursor.fetchone()
    return res is not None and res[0] == senha

def criar_usuario_padrao():
    cursor.execute("SELECT * FROM usuarios WHERE usuario = 'admin'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO usuarios (usuario, senha) VALUES (?, ?)", ('admin', '1234'))
        conn.commit()

criar_usuario_padrao()

def salvar_cliente(nome, telefone, email, anamnese, bebida, gosto, assinatura_b64, foto_bytes):
    criado_em = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('''
        INSERT INTO clientes 
        (nome, telefone, email, anamnese, bebida_preferida, gosto_musical, assinatura, foto, criado_em)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (nome, telefone, email, anamnese, bebida, gosto, assinatura_b64, foto_bytes, criado_em))
    conn.commit()

def carregar_clientes(ativos=True):
    status = 'ativo' if ativos else 'cancelado'
    cursor.execute("SELECT id, nome, telefone FROM clientes WHERE status = ?", (status,))
    return cursor.fetchall()

def cancelar_cliente(cliente_id):
    cursor.execute("UPDATE clientes SET status = 'cancelado' WHERE id = ?", (cliente_id,))
    conn.commit()

def salvar_servico(nome, descricao, duracao, valor):
    cursor.execute("INSERT INTO servicos (nome, descricao, duracao, valor) VALUES (?, ?, ?, ?)", (nome, descricao, duracao, valor))
    conn.commit()

def carregar_servicos():
    cursor.execute("SELECT id, nome, descricao, duracao, valor FROM servicos")
    return cursor.fetchall()

def salvar_produto(nome, descricao, preco_custo, preco_venda, quantidade):
    cursor.execute("INSERT INTO produtos (nome, descricao, preco_custo, preco_venda, quantidade) VALUES (?, ?, ?, ?, ?)", (nome, descricao, preco_custo, preco_venda, quantidade))
    conn.commit()

def carregar_produtos():
    cursor.execute("SELECT id, nome, descricao, preco_custo, preco_venda, quantidade FROM produtos")
    return cursor.fetchall()

def salvar_agendamento(cliente_id, servico_id, data_hora):
    criado_em = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('''
        INSERT INTO agendamentos (cliente_id, servico_id, data_hora, criado_em)
        VALUES (?, ?, ?, ?)
    ''', (cliente_id, servico_id, data_hora, criado_em))
    conn.commit()

def carregar_agendamentos(ativos=True):
    status = 'ativo' if ativos else 'cancelado'
    cursor.execute('''
        SELECT a.id, c.nome, s.nome, a.data_hora, a.status
        FROM agendamentos a
        JOIN clientes c ON a.cliente_id = c.id
        JOIN servicos s ON a.servico_id = s.id
        WHERE a.status = ?
        ORDER BY a.data_hora DESC
    ''', (status,))
    return cursor.fetchall()

def cancelar_agendamento(agendamento_id):
    cursor.execute("UPDATE agendamentos SET status = 'cancelado' WHERE id = ?", (agendamento_id,))
    conn.commit()

def salvar_venda_servico(cliente_id, servico_id, valor, forma_pagamento):
    data = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('''
        INSERT INTO vendas (cliente_id, servico_id, valor, forma_pagamento, data)
        VALUES (?, ?, ?, ?, ?)
    ''', (cliente_id, servico_id, valor, forma_pagamento, data))
    conn.commit()

def salvar_venda_produto(cliente_id, produto_id, quantidade, forma_pagamento):
    cursor.execute("SELECT preco_venda, quantidade FROM produtos WHERE id = ?", (produto_id,))
    res = cursor.fetchone()
    if not res:
        return False, "Produto não encontrado"
    preco, estoque = res
    if estoque < quantidade:
        return False, f"Estoque insuficiente: disponível {estoque}"
    valor_total = preco * quantidade
    data = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute('''
        INSERT INTO vendas (cliente_id, produto_id, quantidade, valor, forma_pagamento, data)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (cliente_id, produto_id, quantidade, valor_total, forma_pagamento, data))

    cursor.execute("UPDATE produtos SET quantidade = quantidade - ? WHERE id = ?", (quantidade, produto_id))
    conn.commit()
    return True, "Venda registrada com sucesso"

def carregar_vendas(ativos=True):
    status = 'ativo' if ativos else 'cancelado'
    cursor.execute('''
        SELECT v.id, c.nome, s.nome, p.nome, v.quantidade, v.valor, v.forma_pagamento, v.data, v.status
        FROM vendas v
        LEFT JOIN clientes c ON v.cliente_id = c.id
        LEFT JOIN servicos s ON v.servico_id = s.id
        LEFT JOIN produtos p ON v.produto_id = p.id
        WHERE v.status = ?
        ORDER BY v.data DESC
    ''', (status,))
    return cursor.fetchall()

def cancelar_venda(venda_id):
    cursor.execute("UPDATE vendas SET status = 'cancelado' WHERE id = ?", (venda_id,))
    conn.commit()

def salvar_despesa(descricao, valor, data, quantidade, observacao):
    cursor.execute('''
        INSERT INTO despesas (descricao, valor, data, quantidade, observacao)
        VALUES (?, ?, ?, ?, ?)
    ''', (descricao, valor, data, quantidade, observacao))
    conn.commit()

def carregar_despesas():
    cursor.execute("SELECT id, descricao, valor, data, quantidade, observacao FROM despesas ORDER BY data DESC")
    return cursor.fetchall()

# Função para gerar PDF simples com vendas
def gerar_pdf_vendas():
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    largura, altura = letter
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, altura - 50, "Relatório de Vendas")
    c.setFont("Helvetica", 12)
    cursor.execute('''
        SELECT v.id, c.nome, s.nome, p.nome, v.quantidade, v.valor, v.forma_pagamento, v.data
        FROM vendas v
        LEFT JOIN clientes c ON v.cliente_id = c.id
        LEFT JOIN servicos s ON v.servico_id = s.id
        LEFT JOIN produtos p ON v.produto_id = p.id
        WHERE v.status = 'ativo'
        ORDER BY v.data DESC
        LIMIT 100
    ''')
    vendas = cursor.fetchall()

    y = altura - 80
    for v in vendas:
        texto = f"ID {v[0]} - Cliente: {v[1]} - Serviço: {v[2]} - Produto: {v[3]} - Qtde: {v[4]} - Valor: R$ {v[5]:.2f} - Forma: {v[6]} - Data: {v[7]}"
        c.drawString(50, y, texto)
        y -= 15
        if y < 50:
            c.showPage()
            y = altura - 50
    c.save()
    buffer.seek(0)
    return buffer

# Função para gerar PDF despesas
def gerar_pdf_despesas():
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    largura, altura = letter
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, altura - 50, "Relatório de Despesas")
    c.setFont("Helvetica", 12)
    despesas = carregar_despesas()

    y = altura - 80
    for d in despesas:
        texto = f"ID {d[0]} - {d[1]} - Valor: R$ {d[2]:.2f} - Data: {d[3]} - Qtde: {d[4]} - Obs: {d[5]}"
        c.drawString(50, y, texto)
        y -= 15
        if y < 50:
            c.showPage()
            y = altura - 50
    c.save()
    buffer.seek(0)
    return buffer

# Função para gerar PDF resumo financeiro (vendas - despesas)
def gerar_pdf_resumo_financeiro():
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    largura, altura = letter
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, altura - 50, "Resumo Financeiro")

    cursor.execute("SELECT data, valor FROM vendas WHERE status = 'ativo'")
    vendas_raw = cursor.fetchall()
    if vendas_raw:
        df_vendas = pd.DataFrame(vendas_raw, columns=["data", "valor"])
        df_vendas['data'] = pd.to_datetime(df_vendas['data']).dt.date
        total_vendas = df_vendas['valor'].sum()
    else:
        total_vendas = 0

    cursor.execute("SELECT valor FROM despesas")
    despesas_raw = cursor.fetchall()
    if despesas_raw:
        df_despesas = pd.DataFrame(despesas_raw, columns=["valor"])
        total_despesas = df_despesas['valor'].sum()
    else:
        total_despesas = 0

    total_lucro = total_vendas - total_despesas

    c.setFont("Helvetica", 12)
    c.drawString(50, altura - 90, f"Total Vendas: R$ {total_vendas:,.2f}")
    c.drawString(50, altura - 110, f"Total Despesas: R$ {total_despesas:,.2f}")
    c.drawString(50, altura - 130, f"Lucro Líquido: R$ {total_lucro:,.2f}")

    c.save()
    buffer.seek(0)
    return buffer

# Função para aplicar estilos (cor)
def aplicar_estilos():
    cor = st.session_state.get("cor_tema", "blue")
    st.markdown(f"""
    <style>
    .css-1aumxhk {{
        background-color: {cor};
        color: white;
    }}
    .stButton>button {{
        background-color: {cor} !important;
        color: white !important;
        border-radius: 8px;
        border: none;
        padding: 8px 16px;
    }}
    .stSidebar .css-1aumxhk {{
        background-color: {cor};
        color: white;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- Página dashboard ---
def pagina_dashboard():
    st.title("Dashboard Financeiro")
    aplicar_estilos()

    # Dados vendas ativos
    cursor.execute("SELECT data, valor FROM vendas WHERE status = 'ativo'")
    vendas_raw = cursor.fetchall()
    if vendas_raw:
        df_vendas = pd.DataFrame(vendas_raw, columns=["data", "valor"])
        df_vendas['data'] = pd.to_datetime(df_vendas['data']).dt.date
        df_vendas_group = df_vendas.groupby('data').sum().reset_index()
    else:
        df_vendas = pd.DataFrame(columns=["data", "valor"])
        df_vendas_group = pd.DataFrame(columns=["data", "valor"])

    # Dados despesas
    cursor.execute("SELECT data, valor FROM despesas")
    despesas_raw = cursor.fetchall()
    if despesas_raw:
        df_despesas = pd.DataFrame(despesas_raw, columns=["data", "valor"])
        df_despesas['data'] = pd.to_datetime(df_despesas['data']).dt.date
        df_despesas_group = df_despesas.groupby('data').sum().reset_index()
    else:
        df_despesas = pd.DataFrame(columns=["data", "valor"])
        df_despesas_group = pd.DataFrame(columns=["data", "valor"])

    # Lucro por dia (vendas - despesas)
    df_lucro = pd.merge(df_vendas_group, df_despesas_group, on='data', how='outer', suffixes=('_vendas', '_despesas')).fillna(0)
    df_lucro['lucro'] = df_lucro['valor_vendas'] - df_lucro['valor_despesas']

    # Mostra valores totais
    total_vendas = df_vendas['valor'].sum() if not df_vendas.empty else 0
    total_despesas = df_despesas['valor'].sum() if not df_despesas.empty else 0
    total_lucro = total_vendas - total_despesas

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Vendas (R$)", f"{total_vendas:,.2f}")
    col2.metric("Total Despesas (R$)", f"{total_despesas:,.2f}")
    col3.metric("Lucro Líquido (R$)", f"{total_lucro:,.2f}")

    # Gráfico vendas
    if not df_vendas_group.empty:
        fig_vendas = px.bar(df_vendas_group, x="data", y="valor", title="Vendas por Dia", labels={"data": "Data", "valor": "Valor (R$)"})
        st.plotly_chart(fig_vendas, use_container_width=True)
    else:
        st.info("Nenhuma venda registrada.")

    # Gráfico despesas
    if not df_despesas_group.empty:
        fig_despesas = px.bar(df_despesas_group, x="data", y="valor", title="Despesas por Dia", labels={"data": "Data", "valor": "Valor (R$)"})
        st.plotly_chart(fig_despesas, use_container_width=True)
    else:
        st.info("Nenhuma despesa registrada.")

    # Gráfico lucro
    if not df_lucro.empty:
        fig_lucro = px.line(df_lucro, x="data", y="lucro", title="Lucro Diário", labels={"data": "Data", "lucro": "Lucro (R$)"})
        st.plotly_chart(fig_lucro, use_container_width=True)

    # Botões para gerar PDFs
    st.markdown("---")
    colv, cold, colr = st.columns(3)
    with colv:
        if st.button("Gerar Relatório Vendas PDF"):
            pdf = gerar_pdf_vendas()
            b64 = base64.b64encode(pdf.read()).decode()
            href = f'<a href="data:application/octet-stream;base64,{b64}" download="relatorio_vendas.pdf">Download Relatório Vendas</a>'
            st.markdown(href, unsafe_allow_html=True)
    with cold:
        if st.button("Gerar Relatório Despesas PDF"):
            pdf = gerar_pdf_despesas()
            b64 = base64.b64encode(pdf.read()).decode()
            href = f'<a href="data:application/octet-stream;base64,{b64}" download="relatorio_despesas.pdf">Download Relatório Despesas</a>'
            st.markdown(href, unsafe_allow_html=True)
    with colr:
        if st.button("Gerar Resumo Financeiro PDF"):
            pdf = gerar_pdf_resumo_financeiro()
            b64 = base64.b64encode(pdf.read()).decode()
            href = f'<a href="data:application/octet-stream;base64,{b64}" download="resumo_financeiro.pdf">Download Resumo Financeiro</a>'
            st.markdown(href, unsafe_allow_html=True)

# --- Configurações de paleta ---
def pagina_configuracoes():
    st.title("Configurações de Tema")
    cores = {
        "Azul": "#1f77b4",
        "Verde": "#2ca02c",
        "Vermelho": "#d62728",
        "Amarelo": "#ffbf00",
        "Roxo": "#9467bd",
        "Preto": "#111111"
    }
    escolha = st.selectbox("Escolha a cor do tema:", list(cores.keys()), index=0)
    st.session_state["cor_tema"] = cores[escolha]
    aplicar_estilos()
    st.success(f"Tema alterado para {escolha}")

# --- Menu lateral fixo com ícones e botões ---
def menu_lateral():
    st.sidebar.title("Menu Principal")
    menu_opcoes = {
        "Dashboard": pagina_dashboard,
        "Clientes": pagina_clientes,
        "Serviços": pagina_servicos,
        "Produtos": pagina_produtos,
        "Agendamentos": pagina_agendamentos,
        "Vendas": pagina_vendas,
        "Despesas": pagina_despesas,
        "Configurações": pagina_configuracoes
    }
    for nome, func in menu_opcoes.items():
        if st.sidebar.button(nome):
            st.session_state["pagina_atual"] = nome
            func()

# --- Outras páginas (exemplo de clientes, serviços etc) ---
def pagina_clientes():
    st.title("Clientes")
    # Código para exibir, cadastrar, editar, cancelar clientes (semelhante a outros módulos)
    st.info("Página de clientes em desenvolvimento.")

def pagina_servicos():
    st.title("Serviços")
    st.info("Página de serviços em desenvolvimento.")

def pagina_produtos():
    st.title("Produtos")
    st.info("Página de produtos em desenvolvimento.")

def pagina_agendamentos():
    st.title("Agendamentos")
    st.info("Página de agendamentos em desenvolvimento.")

def pagina_vendas():
    st.title("Vendas")
    st.info("Página de vendas em desenvolvimento.")

def pagina_despesas():
    st.title("Despesas")
    st.info("Página de despesas em desenvolvimento.")

# --- Função principal ---
def main():
    st.set_page_config(page_title="Studio Beauty", layout="wide")
    criar_tabelas()
    if "pagina_atual" not in st.session_state:
        st.session_state["pagina_atual"] = "Dashboard"
    menu_lateral()
    pagina = st.session_state["pagina_atual"]
    if pagina == "Dashboard":
        pagina_dashboard()
    elif pagina == "Clientes":
        pagina_clientes()
    elif pagina == "Serviços":
        pagina_servicos()
    elif pagina == "Produtos":
        pagina_produtos()
    elif pagina == "Agendamentos":
        pagina_agendamentos()
    elif pagina == "Vendas":
        pagina_vendas()
    elif pagina == "Despesas":
        pagina_despesas()
    elif pagina == "Configurações":
        pagina_configuracoes()

if __name__ == "__main__":
    main()
