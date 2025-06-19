import streamlit as st
import sqlite3
from datetime import datetime
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

# PDFs: vendas, despesas e resumo financeiro (como no seu código)
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
def aplicar_estilos():
    cor = st.session_state.get("cor_tema", "#1f77b4")
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

def pagina_dashboard():
    st.title("Dashboard Financeiro")
    aplicar_estilos()

    cursor.execute("SELECT data, valor FROM vendas WHERE status = 'ativo'")
    vendas_raw = cursor.fetchall()
    if vendas_raw:
        df_vendas = pd.DataFrame(vendas_raw, columns=["data", "valor"])
        df_vendas['data'] = pd.to_datetime(df_vendas['data']).dt.date
        df_vendas_group = df_vendas.groupby('data').sum().reset_index()
    else:
        df_vendas_group = pd.DataFrame(columns=["data", "valor"])

    cursor.execute("SELECT data, valor FROM despesas")
    despesas_raw = cursor.fetchall()
    if despesas_raw:
        df_despesas = pd.DataFrame(despesas_raw, columns=["data", "valor"])
        df_despesas['data'] = pd.to_datetime(df_despesas['data']).dt.date
        df_despesas_group = df_despesas.groupby('data').sum().reset_index()
    else:
        df_despesas_group = pd.DataFrame(columns=["data", "valor"])

    df_lucro = pd.merge(df_vendas_group, df_despesas_group, on='data', how='outer', suffixes=('_vendas', '_despesas')).fillna(0)
    df_lucro['lucro'] = df_lucro['valor_vendas'] - df_lucro['valor_despesas']

    total_vendas = df_vendas['valor'].sum() if not df_vendas.empty else 0
    total_despesas = df_despesas['valor'].sum() if not df_despesas.empty else 0
    total_lucro = total_vendas - total_despesas

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Vendas (R$)", f"{total_vendas:,.2f}")
    col2.metric("Total Despesas (R$)", f"{total_despesas:,.2f}")
    col3.metric("Lucro Líquido (R$)", f"{total_lucro:,.2f}")

    if not df_vendas_group.empty:
        fig_vendas = px.bar(df_vendas_group, x="data", y="valor", title="Vendas por Dia", labels={"data": "Data", "valor": "Valor (R$)"})
        st.plotly_chart(fig_vendas, use_container_width=True)
    else:
        st.info("Nenhuma venda registrada.")

    if not df_despesas_group.empty:
        fig_despesas = px.bar(df_despesas_group, x="data", y="valor", title="Despesas por Dia", labels={"data": "Data", "valor": "Valor (R$)"})
        st.plotly_chart(fig_despesas, use_container_width=True)
    else:
        st.info("Nenhuma despesa registrada.")

    if not df_lucro.empty:
        fig_lucro = px.line(df_lucro, x="data", y="lucro", title="Lucro Diário", labels={"data": "Data", "lucro": "Lucro (R$)"})
        st.plotly_chart(fig_lucro, use_container_width=True)

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
    st.success(f"Tema alterado para {escolha}")
    aplicar_estilos()
def pagina_login():
    st.title("Login")
    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if verificar_login(usuario, senha):
            st.session_state["login"] = True
            st.session_state["usuario"] = usuario
            st.success(f"Bem-vindo, {usuario}!")
        else:
            st.error("Usuário ou senha incorretos")

def pagina_clientes():
    st.title("Cadastro de Clientes")
    with st.form("form_cliente"):
        nome = st.text_input("Nome *")
        telefone = st.text_input("Telefone")
        email = st.text_input("Email")
        anamnese = st.text_area("Anamnese")
        bebida = st.text_input("Bebida Preferida")
        gosto = st.text_input("Gosto Musical")
        assinatura = st.text_area("Assinatura do Cliente")
        foto = st.file_uploader("Foto do Cliente", type=["png", "jpg", "jpeg"])
        submitted = st.form_submit_button("Salvar")
        if submitted:
            foto_bytes = foto.read() if foto else None
            assinatura_b64 = base64.b64encode(assinatura.encode()).decode() if assinatura else None
            if nome.strip() == "":
                st.error("Nome é obrigatório")
            else:
                salvar_cliente(nome, telefone, email, anamnese, bebida, gosto, assinatura_b64, foto_bytes)
                st.success("Cliente salvo com sucesso!")

    st.markdown("### Clientes cadastrados:")
    clientes = carregar_clientes()
    for c in clientes:
        st.write(f"ID: {c[0]} - Nome: {c[1]} - Telefone: {c[2]}")
        if st.button(f"Cancelar Cliente {c[0]}"):
            cancelar_cliente(c[0])
            st.experimental_rerun()

def pagina_servicos():
    st.title("Cadastro de Serviços")
    with st.form("form_servico"):
        nome = st.text_input("Nome do Serviço *")
        descricao = st.text_area("Descrição")
        duracao = st.number_input("Duração (minutos)", min_value=1, max_value=600)
        valor = st.number_input("Valor R$", min_value=0.0, format="%.2f")
        submitted = st.form_submit_button("Salvar")
        if submitted:
            if nome.strip() == "":
                st.error("Nome do serviço é obrigatório")
            else:
                salvar_servico(nome, descricao, duracao, valor)
                st.success("Serviço salvo com sucesso!")

    st.markdown("### Serviços cadastrados:")
    servicos = carregar_servicos()
    for s in servicos:
        st.write(f"ID: {s[0]} - Nome: {s[1]} - Valor: R$ {s[4]:.2f}")

def pagina_produtos():
    st.title("Cadastro de Produtos")
    with st.form("form_produto"):
        nome = st.text_input("Nome do Produto *")
        descricao = st.text_area("Descrição")
        preco_custo = st.number_input("Preço de Custo R$", min_value=0.0, format="%.2f")
        preco_venda = st.number_input("Preço de Venda R$", min_value=0.0, format="%.2f")
        quantidade = st.number_input("Quantidade em Estoque", min_value=0)
        submitted = st.form_submit_button("Salvar")
        if submitted:
            if nome.strip() == "":
                st.error("Nome do produto é obrigatório")
            else:
                salvar_produto(nome, descricao, preco_custo, preco_venda, quantidade)
                st.success("Produto salvo com sucesso!")

    st.markdown("### Produtos cadastrados:")
    produtos = carregar_produtos()
    for p in produtos:
        st.write(f"ID: {p[0]} - Nome: {p[1]} - Estoque: {p[5]} - Preço Venda: R$ {p[4]:.2f}")
def main():
    st.set_page_config(page_title="Sistema Estúdio de Beleza", layout="wide")

    if "login" not in st.session_state:
        st.session_state["login"] = False

    if not st.session_state["login"]:
        pagina_login()
        return

    st.sidebar.title("Menu")
    menu = st.sidebar.radio("Navegação", ["Dashboard", "Clientes", "Serviços", "Produtos", "Agendamentos", "Vendas", "Despesas", "Configurações", "Sair"])

    if menu == "Dashboard":
        pagina_dashboard()
    elif menu == "Clientes":
        pagina_clientes()
    elif menu == "Serviços":
        pagina_servicos()
    elif menu == "Produtos":
        pagina_produtos()
    elif menu == "Agendamentos":
        st.title("Agendamentos (a implementar)")
        # Aqui você pode implementar a página de agendamentos, similar ao cadastro
    elif menu == "Vendas":
        st.title("Vendas (a implementar)")
        # Aqui você pode implementar a página de vendas, com seleção de cliente, produtos, serviços, forma de pagamento
    elif menu == "Despesas":
        st.title("Despesas (a implementar)")
        # Página para cadastro e listagem de despesas
    elif menu == "Configurações":
        pagina_configuracoes()
    elif menu == "Sair":
        st.session_state["login"] = False
        st.experimental_rerun()

if __name__ == "__main__":
    main()
# Parte 6 - Continuação do app.py (páginas: Serviços, Produtos, Agendamentos, Vendas, Despesas)

def pagina_servicos():
    st.title("Serviços")
    aplicar_estilos()
    with st.form("form_servico"):
        nome = st.text_input("Nome do serviço")
        descricao = st.text_area("Descrição")
        duracao = st.number_input("Duração (min)", min_value=0)
        valor = st.number_input("Valor (R$)", min_value=0.0, format="%.2f")
        if st.form_submit_button("Salvar"):
            salvar_servico(nome, descricao, duracao, valor)
            st.success("Serviço salvo com sucesso!")

    st.subheader("Serviços cadastrados")
    servicos = carregar_servicos()
    for s in servicos:
        st.markdown(f"**{s[1]}** - {s[2]} - {s[3]}min - R$ {s[4]:.2f}")


def pagina_produtos():
    st.title("Produtos")
    aplicar_estilos()
    with st.form("form_produto"):
        nome = st.text_input("Nome do produto")
        descricao = st.text_area("Descrição")
        preco_custo = st.number_input("Preço de Custo", min_value=0.0, format="%.2f")
        preco_venda = st.number_input("Preço de Venda", min_value=0.0, format="%.2f")
        quantidade = st.number_input("Quantidade", min_value=0)
        if st.form_submit_button("Salvar"):
            salvar_produto(nome, descricao, preco_custo, preco_venda, int(quantidade))
            st.success("Produto salvo com sucesso!")

    st.subheader("Produtos cadastrados")
    produtos = carregar_produtos()
    for p in produtos:
        st.markdown(f"**{p[1]}** - {p[2]} - Estoque: {p[5]} - R$ {p[4]:.2f}")


def pagina_agendamentos():
    st.title("Agendamentos")
    aplicar_estilos()
    clientes = carregar_clientes()
    servicos = carregar_servicos()

    with st.form("form_agendamento"):
        cliente = st.selectbox("Cliente", clientes, format_func=lambda x: x[1])
        servico = st.selectbox("Serviço", servicos, format_func=lambda x: x[1])
        data_hora = st.datetime_input("Data e hora")
        if st.form_submit_button("Agendar"):
            salvar_agendamento(cliente[0], servico[0], data_hora.strftime("%Y-%m-%d %H:%M:%S"))
            st.success("Agendamento realizado com sucesso!")

    st.subheader("Agendamentos Ativos")
    agendamentos = carregar_agendamentos()
    for ag in agendamentos:
        st.markdown(f"**{ag[1]}** - {ag[2]} - {ag[3]}")
        if st.button(f"Cancelar {ag[0]}"):
            cancelar_agendamento(ag[0])
            st.warning("Agendamento cancelado")


def pagina_vendas():
    st.title("Vendas")
    aplicar_estilos()
    clientes = carregar_clientes()
    produtos = carregar_produtos()
    servicos = carregar_servicos()

    with st.expander("Venda de Serviço"):
        with st.form("form_venda_servico"):
            cliente = st.selectbox("Cliente", clientes, format_func=lambda x: x[1], key="vs_cli")
            servico = st.selectbox("Serviço", servicos, format_func=lambda x: x[1], key="vs_serv")
            forma = st.selectbox("Forma de Pagamento", ["Dinheiro", "Cartão", "Pix"], key="vs_fp")
            if st.form_submit_button("Vender Serviço"):
                salvar_venda_servico(cliente[0], servico[0], servico[4], forma)
                st.success("Venda de serviço registrada!")

    with st.expander("Venda de Produto"):
        with st.form("form_venda_produto"):
            cliente = st.selectbox("Cliente", clientes, format_func=lambda x: x[1], key="vp_cli")
            produto = st.selectbox("Produto", produtos, format_func=lambda x: x[1], key="vp_prod")
            qtd = st.number_input("Quantidade", min_value=1, step=1)
            forma = st.selectbox("Forma de Pagamento", ["Dinheiro", "Cartão", "Pix"], key="vp_fp")
            if st.form_submit_button("Vender Produto"):
                sucesso, msg = salvar_venda_produto(cliente[0], produto[0], int(qtd), forma)
                if sucesso:
                    st.success(msg)
                else:
                    st.error(msg)

    st.subheader("Histórico de Vendas")
    vendas = carregar_vendas()
    for v in vendas:
        st.markdown(f"**ID {v[0]}** - Cliente: {v[1]} - Serviço: {v[2]} - Produto: {v[3]} - Qtde: {v[4]} - R$ {v[5]:.2f} - {v[6]} - {v[7]}")
        if v[8] == "ativo" and st.button(f"Cancelar Venda {v[0]}"):
            cancelar_venda(v[0])
            st.warning("Venda cancelada")


def pagina_despesas():
    st.title("Despesas")
    aplicar_estilos()
    with st.form("form_despesa"):
        descricao = st.text_input("Descrição")
        valor = st.number_input("Valor (R$)", min_value=0.0, format="%.2f")
        data = st.date_input("Data")
        qtd = st.number_input("Quantidade", min_value=1)
        obs = st.text_area("Observações")
        if st.form_submit_button("Salvar Despesa"):
            salvar_despesa(descricao, valor, data.strftime("%Y-%m-%d"), int(qtd), obs)
            st.success("Despesa registrada!")

    st.subheader("Despesas Registradas")
    despesas = carregar_despesas()
    for d in despesas:
        st.markdown(f"**{d[1]}** - R$ {d[2]:.2f} - {d[3]} - Qtde: {d[4]} - Obs: {d[5]}")
def pagina_servicos():
    st.title("Serviços")
    aplicar_estilos()
    with st.form("form_servico"):
        nome = st.text_input("Nome do Serviço")
        descricao = st.text_area("Descrição")
        duracao = st.number_input("Duração (minutos)", min_value=0, step=5)
        valor = st.number_input("Valor (R$)", min_value=0.0, step=1.0, format="%.2f")
        submitted = st.form_submit_button("Salvar Serviço")
        if submitted and nome:
            salvar_servico(nome, descricao, duracao, valor)
            st.success("Serviço salvo com sucesso!")

    st.subheader("Lista de Serviços Cadastrados")
    servicos = carregar_servicos()
    if servicos:
        df = pd.DataFrame(servicos, columns=["ID", "Nome", "Descrição", "Duração", "Valor"])
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Nenhum serviço cadastrado ainda.")

def pagina_produtos():
    st.title("Produtos")
    aplicar_estilos()
    with st.form("form_produto"):
        nome = st.text_input("Nome do Produto")
        descricao = st.text_area("Descrição")
        preco_custo = st.number_input("Preço de Custo (R$)", min_value=0.0, step=1.0, format="%.2f")
        preco_venda = st.number_input("Preço de Venda (R$)", min_value=0.0, step=1.0, format="%.2f")
        quantidade = st.number_input("Quantidade em Estoque", min_value=0, step=1)
        submitted = st.form_submit_button("Salvar Produto")
        if submitted and nome:
            salvar_produto(nome, descricao, preco_custo, preco_venda, quantidade)
            st.success("Produto salvo com sucesso!")

    st.subheader("Lista de Produtos")
    produtos = carregar_produtos()
    if produtos:
        df = pd.DataFrame(produtos, columns=["ID", "Nome", "Descrição", "Custo", "Venda", "Estoque"])
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Nenhum produto cadastrado ainda.")
def pagina_agendamentos():
    st.title("Agendamentos")
    aplicar_estilos()

    clientes = carregar_clientes()
    servicos = carregar_servicos()

    if clientes and servicos:
        with st.form("form_agendamento"):
            cliente_escolhido = st.selectbox("Cliente", clientes, format_func=lambda x: x[1])
            servico_escolhido = st.selectbox("Serviço", servicos, format_func=lambda x: x[1])
            data_hora = st.datetime_input("Data e Hora")
            submitted = st.form_submit_button("Agendar")
            if submitted:
                salvar_agendamento(cliente_escolhido[0], servico_escolhido[0], data_hora.strftime("%Y-%m-%d %H:%M:%S"))
                st.success("Agendamento realizado com sucesso!")

    st.subheader("Agendamentos Ativos")
    agendamentos = carregar_agendamentos()
    if agendamentos:
        df = pd.DataFrame(agendamentos, columns=["ID", "Cliente", "Serviço", "Data", "Status"])
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Nenhum agendamento ativo.")
def pagina_vendas():
    st.title("Vendas")
    aplicar_estilos()

    clientes = carregar_clientes()
    produtos = carregar_produtos()
    servicos = carregar_servicos()

    aba = st.radio("Tipo de Venda", ["Serviço", "Produto"], horizontal=True)

    if aba == "Serviço" and clientes and servicos:
        with st.form("form_venda_servico"):
            cliente = st.selectbox("Cliente", clientes, format_func=lambda x: x[1])
            servico = st.selectbox("Serviço", servicos, format_func=lambda x: x[1])
            forma = st.selectbox("Forma de Pagamento", ["Pix", "Dinheiro", "Cartão Crédito", "Cartão Débito"])
            enviado = st.form_submit_button("Finalizar Venda")
            if enviado:
                valor = servico[4]
                salvar_venda_servico(cliente[0], servico[0], valor, forma)
                st.success("Venda de serviço registrada!")

    if aba == "Produto" and clientes and produtos:
        with st.form("form_venda_produto"):
            cliente = st.selectbox("Cliente", clientes, format_func=lambda x: x[1], key="cliente_prod")
            produto = st.selectbox("Produto", produtos, format_func=lambda x: x[1])
            quantidade = st.number_input("Quantidade", min_value=1, step=1)
            forma = st.selectbox("Forma de Pagamento", ["Pix", "Dinheiro", "Cartão Crédito", "Cartão Débito"], key="forma_prod")
            enviado = st.form_submit_button("Finalizar Venda")
            if enviado:
                ok, msg = salvar_venda_produto(cliente[0], produto[0], quantidade, forma)
                if ok:
                    st.success(msg)
                else:
                    st.warning(msg)

    st.subheader("Histórico de Vendas")
    vendas = carregar_vendas()
    if vendas:
        df = pd.DataFrame(vendas, columns=["ID", "Cliente", "Serviço", "Produto", "Qtde", "Valor", "Pagamento", "Data", "Status"])
        st.dataframe(df, use_container_width=True)

def pagina_despesas():
    st.title("Despesas")
    aplicar_estilos()

    with st.form("form_despesa"):
        descricao = st.text_input("Descrição da Despesa")
        valor = st.number_input("Valor (R$)", min_value=0.0, step=1.0, format="%.2f")
        data = st.date_input("Data")
        quantidade = st.number_input("Quantidade", min_value=1, step=1)
        obs = st.text_area("Observação")
        submitted = st.form_submit_button("Registrar Despesa")
        if submitted and descricao:
            salvar_despesa(descricao, valor, data.strftime("%Y-%m-%d"), quantidade, obs)
            st.success("Despesa registrada!")

    st.subheader("Histórico de Despesas")
    despesas = carregar_despesas()
    if despesas:
        df = pd.DataFrame(despesas, columns=["ID", "Descrição", "Valor", "Data", "Qtde", "Obs"])
        st.dataframe(df, use_container_width=True)
