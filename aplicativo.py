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
            st.session_state["pagina"] = "Dashboard"
            st.experimental_rerun()
        else:
            st.error("Usuário ou senha incorretos")

def pagina_dashboard():
    st.title("Dashboard")
    st.write("Resumo rápido do sistema")

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
                else:
                    salvar_servico(nome, descricao, duracao, valor)
                    st.success(f"Serviço '{nome}' salvo!")
                    st.experimental_rerun()

    st.subheader("Serviços Cadastrados")
    servicos = carregar_servicos()
    for s in servicos:
        col1, col2, col3, col4 = st.columns([3,5,2,2])
        with col1:
            st.write(s[1])
        with col2:
            st.write(s[2])
        with col3:
            st.write(f"{s[3]} min")
        with col4:
            st.write(f"R$ {s[4]:.2f}")

def pagina_produtos():
    st.title("Produtos")
    with st.expander("Cadastrar Novo Produto"):
        with st.form("form_produto", clear_on_submit=True):
            nome = st.text_input("Nome do Produto")
            descricao = st.text_area("Descrição")
            preco_custo = st.number_input("Preço de Custo R$", min_value=0.0, format="%.2f")
            preco_venda = st.number_input("Preço de Venda R$", min_value=0.0, format="%.2f")
            quantidade = st.number_input("Quantidade em Estoque", min_value=0, step=1)
            submitted = st.form_submit_button("Salvar Produto")
            if submitted:
                if not nome.strip():
                    st.error("Nome é obrigatório")
                else:
                    salvar_produto(nome, descricao, preco_custo, preco_venda, quantidade)
                    st.success(f"Produto '{nome}' salvo!")
                    st.experimental_rerun()

    st.subheader("Produtos Cadastrados")
    produtos = carregar_produtos()
    for p in produtos:
        col1, col2, col3, col4, col5, col6 = st.columns([3,5,2,2,2,1])
        with col1:
            st.write(p[1])
        with col2:
            st.write(p[2])
        with col3:
            st.write(f"R$ {p[3]:.2f}")
        with col4:
            st.write(f"R$ {p[4]:.2f}")
        with col5:
            st.write(p[5])
        with col6:
            pass  # Aqui pode adicionar botões editar ou excluir se quiser

def pagina_agendamentos():
    st.title("Agendamentos")
    clientes = carregar_clientes()
    servicos = carregar_servicos()

    with st.expander("Agendar Serviço"):
        with st.form("form_agendamento", clear_on_submit=True):
            cliente = st.selectbox("Cliente", clientes, format_func=lambda x: x[1]) if clientes else None
            servico = st.selectbox("Serviço", servicos, format_func=lambda x: x[1]) if servicos else None
            from datetime import datetime
            data = st.date_input("Data")
            hora = st.time_input("Hora")
            data_hora = datetime.combine(data, hora)                 
            submitted = st.form_submit_button("Agendar")
            if submitted:
                if cliente and servico:
                    salvar_agendamento(cliente[0], servico[0], data_hora.strftime("%Y-%m-%d %H:%M:%S"))
                    st.success("Agendamento salvo!")
                    st.experimental_rerun()
                else:
                    st.warning("Cadastre clientes e serviços primeiro.")

    st.subheader("Agendamentos Ativos")
    agendamentos = carregar_agendamentos()
    for a in agendamentos:
        col1, col2, col3, col4, col5 = st.columns([2,3,3,3,2])
        with col1:
            st.write(a[0])
        with col2:
            st.write(a[1])
        with col3:
            st.write(a[2])
        with col4:
            st.write(a[3])
        with col5:
            if st.button(f"Cancelar {a[0]}"):
                cancelar_agendamento(a[0])
                st.success("Agendamento cancelado")
                st.experimental_rerun()

def pagina_vendas():
    st.title("Vendas")

    # Inicializar carrinho unificado na sessão
    if "carrinho" not in st.session_state:
        st.session_state.carrinho = []

    clientes = carregar_clientes()
    servicos = carregar_servicos()
    produtos = carregar_produtos()

    # Formulário para adicionar serviços
    with st.expander("Adicionar Serviço ao Carrinho"):
        with st.form("form_add_servico_unificado"):
            if clientes and servicos:
                cliente_s = st.selectbox("Cliente", clientes, format_func=lambda x: x[1], key="cliente_servico")
                servico_s = st.selectbox("Serviço", servicos, format_func=lambda x: x[1])
                forma_s = st.selectbox("Forma de Pagamento", ["Pix", "Dinheiro", "Cartão Crédito", "Cartão Débito"], key="forma_pagamento_servico")
                submit_servico = st.form_submit_button("Adicionar Serviço")
                if submit_servico:
                    st.session_state.carrinho.append({
                        "tipo": "servico",
                        "cliente_id": cliente_s[0],
                        "cliente_nome": cliente_s[1],
                        "id": servico_s[0],
                        "nome": servico_s[1],
                        "quantidade": 1,
                        "valor_unitario": servico_s[4],
                        "valor_total": servico_s[4],
                        "forma_pagamento": forma_s
                    })
                    st.success(f"Serviço '{servico_s[1]}' adicionado ao carrinho.")

    # Formulário para adicionar produtos
    with st.expander("Adicionar Produto ao Carrinho"):
        with st.form("form_add_produto_unificado"):
            if clientes and produtos:
                cliente_p = st.selectbox("Cliente", clientes, format_func=lambda x: x[1], key="cliente_produto")
                produto_p = st.selectbox("Produto", produtos, format_func=lambda x: x[1])
                quantidade_p = st.number_input("Quantidade", min_value=1, step=1)
                forma_p = st.selectbox("Forma de Pagamento", ["Pix", "Dinheiro", "Cartão Crédito", "Cartão Débito"], key="forma_pagamento_produto")
                submit_produto = st.form_submit_button("Adicionar Produto")
                if submit_produto:
                    if produto_p[5] < quantidade_p:
                        st.warning(f"Estoque insuficiente para '{produto_p[1]}'. Disponível: {produto_p[5]}")
                    else:
                        st.session_state.carrinho.append({
                            "tipo": "produto",
                            "cliente_id": cliente_p[0],
                            "cliente_nome": cliente_p[1],
                            "id": produto_p[0],
                            "nome": produto_p[1],
                            "quantidade": quantidade_p,
                            "valor_unitario": produto_p[4],
                            "valor_total": produto_p[4] * quantidade_p,
                            "forma_pagamento": forma_p
                        })
                        st.success(f"Produto '{produto_p[1]}' (x{quantidade_p}) adicionado ao carrinho.")

    # Mostrar o carrinho
    st.subheader("Carrinho de Compras")
    if st.session_state.carrinho:
        total_geral = 0
        remover_indices = []
        for i, item in enumerate(st.session_state.carrinho):
            st.write(f"{i+1}. [{item['tipo'].capitalize()}] {item['nome']} - Qtde: {item['quantidade']} - R$ {item['valor_total']:.2f} - Cliente: {item['cliente_nome']} - Pagamento: {item['forma_pagamento']}")
            total_geral += item['valor_total']
            if st.button(f"Remover item {i+1}", key=f"remover_{i}"):
                remover_indices.append(i)
        # Remover itens selecionados
        if remover_indices:
            for index in sorted(remover_indices, reverse=True):
                st.session_state.carrinho.pop(index)
            st.experimental_rerun()

        st.write(f"**Total Geral: R$ {total_geral:.2f}**")

        # Finalizar venda para todos os itens do carrinho
        if st.button("Finalizar Venda - Todos os Itens"):
            erros = False
            for item in st.session_state.carrinho:
                if item["tipo"] == "servico":
                    salvar_venda_servico(item["cliente_id"], item["id"], item["valor_total"], item["forma_pagamento"])
                else:  # produto
                    ok, msg = salvar_venda_produto(item["cliente_id"], item["id"], item["quantidade"], item["forma_pagamento"])
                    if not ok:
                        st.error(f"Erro ao vender '{item['nome']}': {msg}")
                        erros = True
            if not erros:
                st.success("Todas as vendas foram registradas com sucesso!")
                st.session_state.carrinho.clear()
                st.experimental_rerun()
    else:
        st.info("Carrinho vazio. Adicione produtos ou serviços.")

def pagina_despesas():
    st.title("Despesas")
    with st.expander("Registrar Nova Despesa"):
        with st.form("form_despesa", clear_on_submit=True):
            descricao = st.text_input("Descrição")
            valor = st.number_input("Valor", min_value=0.0, format="%.2f")
            data = st.date_input("Data", value=date.today())
            quantidade = st.number_input("Quantidade", min_value=1, step=1)
            observacao = st.text_area("Observação")
            submitted = st.form_submit_button("Salvar Despesa")
            if submitted:
                if not descricao.strip():
                    st.error("Descrição é obrigatória")
                else:
                    salvar_despesa(descricao, valor, data.strftime("%Y-%m-%d"), quantidade, observacao)
                    st.success("Despesa registrada!")
                    st.experimental_rerun()

    st.subheader("Despesas Registradas")
    despesas = carregar_despesas()
    for d in despesas:
        st.write(f"{d[1]} - R$ {d[2]:.2f} - Data: {d[3]} - Qtde: {d[4]} - Obs: {d[5]}")

def pagina_relatorios():
    st.title("Relatórios")

    st.subheader("Filtro por período")
    data_inicio = st.date_input("Data Início", value=date.today().replace(day=1))
    data_fim = st.date_input("Data Fim", value=date.today())

    st.markdown("---")

    # Gráficos
    st.subheader("Gráfico de Vendas por Data")
    vendas = carregar_vendas(data_inicio=data_inicio.strftime("%Y-%m-%d"), data_fim=data_fim.strftime("%Y-%m-%d"))
    if vendas:
        df_vendas = pd.DataFrame(vendas, columns=["ID", "Cliente", "Serviço", "Produto", "Qtde", "Valor", "Pagamento", "Data", "Status"])
        df_vendas['Data'] = pd.to_datetime(df_vendas['Data']).dt.date
        vendas_agrupadas = df_vendas.groupby('Data')['Valor'].sum().reset_index()
        fig_vendas = px.bar(vendas_agrupadas, x='Data', y='Valor', title="Vendas por Data", labels={"Valor": "R$"})
        st.plotly_chart(fig_vendas, use_container_width=True)
    else:
        st.info("Sem vendas nesse período.")

    st.subheader("Gráfico de Despesas por Data")
    despesas = carregar_despesas(data_inicio=data_inicio.strftime("%Y-%m-%d"), data_fim=data_fim.strftime("%Y-%m-%d"))
    if despesas:
        df_despesas = pd.DataFrame(despesas, columns=["ID", "Descrição", "Valor", "Data", "Quantidade", "Observação"])
        df_despesas['Data'] = pd.to_datetime(df_despesas['Data']).dt.date
        despesas_agrupadas = df_despesas.groupby('Data')['Valor'].sum().reset_index()
        fig_despesas = px.bar(despesas_agrupadas, x='Data', y='Valor', title="Despesas por Data", labels={"Valor": "R$"})
        st.plotly_chart(fig_despesas, use_container_width=True)
    else:
        st.info("Sem despesas nesse período.")

    # Botões para baixar PDF
    st.markdown("---")
    st.subheader("Exportar Relatórios em PDF")
    if st.button("Baixar Relatório de Vendas PDF"):
        pdf_vendas = gerar_pdf_vendas(data_inicio.strftime("%Y-%m-%d"), data_fim.strftime("%Y-%m-%d"))
        st.download_button("Clique para baixar", data=pdf_vendas, file_name="relatorio_vendas.pdf", mime="application/pdf")

    if st.button("Baixar Relatório de Despesas PDF"):
        pdf_despesas = gerar_pdf_despesas(data_inicio.strftime("%Y-%m-%d"), data_fim.strftime("%Y-%m-%d"))
        st.download_button("Clique para baixar", data=pdf_despesas, file_name="relatorio_despesas.pdf", mime="application/pdf")

    if st.button("Baixar Resumo Financeiro PDF"):
        pdf_resumo = gerar_pdf_resumo_financeiro(data_inicio.strftime("%Y-%m-%d"), data_fim.strftime("%Y-%m-%d"))
        st.download_button("Clique para baixar", data=pdf_resumo, file_name="resumo_financeiro.pdf", mime="application/pdf")

def pagina_sair():
    st.session_state["login"] = False
    st.session_state["pagina"] = "Login"
    st.rerun()

# --- Layout principal ---
def main():
    st.set_page_config(page_title="Sistema Estúdio de Beleza", layout="wide")

    if "login" not in st.session_state:
        st.session_state["login"] = False
    if "pagina" not in st.session_state:
        st.session_state["pagina"] = "Login"

    if not st.session_state["login"]:
        pagina_login()
    else:
        col1, col2 = st.columns([1, 7])
        with col1:
            st.sidebar.title("Menu")
            pagina = st.sidebar.radio("Navegação", [
                "Dashboard",
                "Clientes",
                "Serviços",
                "Produtos",
                "Agendamentos",
                "Vendas",
                "Despesas",
                "Relatórios",
                "Sair"
            ])
            st.session_state["pagina"] = pagina
        with col2:
            pagina_atual = st.session_state["pagina"]
            if pagina_atual == "Dashboard":
                pagina_dashboard()
            elif pagina_atual == "Clientes":
                pagina_clientes()
            elif pagina_atual == "Serviços":
                pagina_servicos()
            elif pagina_atual == "Produtos":
                pagina_produtos()
            elif pagina_atual == "Agendamentos":
                pagina_agendamentos()
            elif pagina_atual == "Vendas":
                pagina_vendas()
            elif pagina_atual == "Despesas":
                pagina_despesas()
            elif pagina_atual == "Relatórios":
                pagina_relatorios()
            elif pagina_atual == "Sair":
                pagina_sair()
            else:
                st.write("Página não encontrada")

if __name__ == "__main__":
    main()
