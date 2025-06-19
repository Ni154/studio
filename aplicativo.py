import streamlit as st
import sqlite3
from datetime import datetime, date
import base64
import io
import pandas as pd
import plotly.express as px
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

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

def criar_usuario_padrao():
    cursor.execute("SELECT * FROM usuarios WHERE usuario = 'admin'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO usuarios (usuario, senha) VALUES (?, ?)", ('admin', '1234'))
        conn.commit()

def verificar_login(usuario, senha):
    cursor.execute("SELECT senha FROM usuarios WHERE usuario = ?", (usuario,))
    res = cursor.fetchone()
    return res is not None and res[0] == senha

# Criar tabelas e usuário padrão
criar_tabelas()
criar_usuario_padrao()

# --- Funções CRUD ---
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

def carregar_vendas(ativos=True, data_inicio=None, data_fim=None):
    status = 'ativo' if ativos else 'cancelado'
    query = '''
        SELECT v.id, c.nome, s.nome, p.nome, v.quantidade, v.valor, v.forma_pagamento, v.data, v.status
        FROM vendas v
        LEFT JOIN clientes c ON v.cliente_id = c.id
        LEFT JOIN servicos s ON v.servico_id = s.id
        LEFT JOIN produtos p ON v.produto_id = p.id
        WHERE v.status = ?
    '''
    params = [status]
    if data_inicio and data_fim:
        query += " AND date(v.data) BETWEEN ? AND ?"
        params.extend([data_inicio, data_fim])
    query += " ORDER BY v.data DESC"
    cursor.execute(query, params)
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

def carregar_despesas(data_inicio=None, data_fim=None):
    query = "SELECT id, descricao, valor, data, quantidade, observacao FROM despesas"
    params = []
    if data_inicio and data_fim:
        query += " WHERE date(data) BETWEEN ? AND ?"
        params.extend([data_inicio, data_fim])
    query += " ORDER BY data DESC"
    cursor.execute(query, params)
    return cursor.fetchall()

# --- PDFs: vendas, despesas e resumo financeiro ---
def gerar_pdf_vendas(data_inicio=None, data_fim=None):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    largura, altura = letter
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, altura - 50, "Relatório de Vendas")
    c.setFont("Helvetica", 12)
    query = '''
        SELECT v.id, c.nome, s.nome, p.nome, v.quantidade, v.valor, v.forma_pagamento, v.data
        FROM vendas v
        LEFT JOIN clientes c ON v.cliente_id = c.id
        LEFT JOIN servicos s ON v.servico_id = s.id
        LEFT JOIN produtos p ON v.produto_id = p.id
        WHERE v.status = 'ativo'
    '''
    params = []
    if data_inicio and data_fim:
        query += " AND date(v.data) BETWEEN ? AND ?"
        params.extend([data_inicio, data_fim])
    query += " ORDER BY v.data DESC LIMIT 100"
    cursor.execute(query, params)
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

def gerar_pdf_despesas(data_inicio=None, data_fim=None):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    largura, altura = letter
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, altura - 50, "Relatório de Despesas")
    c.setFont("Helvetica", 12)
    despesas = carregar_despesas(data_inicio, data_fim)

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

def gerar_pdf_resumo_financeiro(data_inicio=None, data_fim=None):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    largura, altura = letter
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, altura - 50, "Resumo Financeiro")

    params = []
    query_vendas = "SELECT data, valor FROM vendas WHERE status = 'ativo'"
    if data_inicio and data_fim:
        query_vendas += " AND date(data) BETWEEN ? AND ?"
        params = [data_inicio, data_fim]

    cursor.execute(query_vendas, params)
    vendas_raw = cursor.fetchall()
    if vendas_raw:
        df_vendas = pd.DataFrame(vendas_raw, columns=["data", "valor"])
        df_vendas['data'] = pd.to_datetime(df_vendas['data']).dt.date
        total_vendas = df_vendas['valor'].sum()
    else:
        total_vendas = 0

    query_despesas = "SELECT valor FROM despesas"
    params = []
    if data_inicio and data_fim:
        query_despesas += " WHERE date(data) BETWEEN ? AND ?"
        params = [data_inicio, data_fim]

    cursor.execute(query_despesas, params)
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

# --- Páginas ---

def pagina_login():
    st.title("Login - Sistema Estúdio de Beleza")
    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if verificar_login(usuario, senha):
            st.session_state["login"] = True
            st.experimental_rerun()
        else:
            st.error("Usuário ou senha incorretos")

def pagina_dashboard():
    st.title("Dashboard")
    st.write("Resumo rápido do sistema")

    # Exemplo: totais básicos
    cursor.execute("SELECT COUNT(*) FROM clientes WHERE status = 'ativo'")
    total_clientes = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM agendamentos WHERE status = 'ativo'")
    total_agendamentos = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM vendas WHERE status = 'ativo'")
    total_vendas = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM despesas")
    total_despesas = cursor.fetchone()[0]

    st.metric("Clientes ativos", total_clientes)
    st.metric("Agendamentos ativos", total_agendamentos)
    st.metric("Vendas registradas", total_vendas)
    st.metric("Despesas registradas", total_despesas)

def pagina_clientes():
    st.title("Clientes")
    with st.expander("Cadastrar Novo Cliente"):
        with st.form("form_cliente", clear_on_submit=True):
            nome = st.text_input("Nome", max_chars=100)
            telefone = st.text_input("Telefone")
            email = st.text_input("Email")
            anamnese = st.text_area("Anamnese")
            bebida = st.text_input("Bebida Preferida")
            gosto = st.text_input("Gosto Musical")
            assinatura = st.text_area("Assinatura")
            foto = st.file_uploader("Foto do Cliente", type=["png", "jpg", "jpeg"])

            assinatura_b64 = base64.b64encode(assinatura.encode()).decode() if assinatura else None
            foto_bytes = foto.read() if foto else None

            submitted = st.form_submit_button("Salvar Cliente")
            if submitted:
                if not nome.strip():
                    st.error("Nome é obrigatório")
                else:
                    salvar_cliente(nome, telefone, email, anamnese, bebida, gosto, assinatura_b64, foto_bytes)
                    st.success(f"Cliente '{nome}' salvo com sucesso!")
                    st.experimental_rerun()

    st.subheader("Clientes Ativos")
    clientes = carregar_clientes(ativos=True)
    for cid, nome, telefone in clientes:
        col1, col2, col3 = st.columns([5,3,2])
        with col1:
            st.write(nome)
        with col2:
            st.write(telefone)
        with col3:
            if st.button(f"Cancelar {cid}"):
                cancelar_cliente(cid)
                st.success("Cliente cancelado")
                st.experimental_rerun()

def pagina_servicos():
    st.title("Serviços")
    with st.expander("Cadastrar Novo Serviço"):
        with st.form("form_servico", clear_on_submit=True):
            nome = st.text_input("Nome do Serviço")
            descricao = st.text_area("Descrição")
            duracao = st.number_input("Duração (minutos)", min_value=1, step=1)
            valor = st.number_input("Valor R$", min_value=0.0, format="%.2f")
            submitted = st.form_submit_button("Salvar Serviço")
            if submitted:
                if not nome.strip():
                    st.error("Nome é obrigatório")
               
