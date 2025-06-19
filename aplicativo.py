import streamlit as st
import sqlite3
from datetime import datetime
import base64
import io
from PIL import Image
from streamlit_drawable_canvas import st_canvas
import pandas as pd
import plotly.express as px

# --- Banco e tabelas ---
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
        descricao TEXT NOT NULL,
        valor REAL NOT NULL,
        data TEXT NOT NULL,
        quantidade INTEGER DEFAULT 1,
        observacao TEXT
    )''')

    conn.commit()

def criar_usuario_padrao():
    cursor.execute("SELECT * FROM usuarios WHERE usuario = 'admin'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO usuarios (usuario, senha) VALUES (?, ?)", ('admin', '1234'))
        conn.commit()

criar_tabelas()
criar_usuario_padrao()

# --- Funções banco ---

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
    cursor.execute("""
        INSERT INTO produtos (nome, descricao, preco_custo, preco_venda, quantidade)
        VALUES (?, ?, ?, ?, ?)
    """, (nome, descricao, preco_custo, preco_venda, quantidade))
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
    preco_venda, estoque = res
    if estoque < quantidade:
        return False, f"Estoque insuficiente: disponível {estoque}"
    valor_total = preco_venda * quantidade
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
    cursor.execute("""
        INSERT INTO despesas (descricao, valor, data, quantidade, observacao)
        VALUES (?, ?, ?, ?, ?)
    """, (descricao, valor, data, quantidade, observacao))
    conn.commit()

def carregar_despesas():
    cursor.execute("SELECT id, descricao, valor, data, quantidade, observacao FROM despesas ORDER BY data DESC")
    return cursor.fetchall()

# --- Configuração de tema e cores ---
PALETAS = {
    "Padrão": {"botao_bg": "#007bff", "botao_fg": "#ffffff", "fundo": "#f0f2f6"},
    "Azul": {"botao_bg": "#0d6efd", "botao_fg": "#ffffff", "fundo": "#e7f1ff"},
    "Verde": {"botao_bg": "#198754", "botao_fg": "#ffffff", "fundo": "#e6f4ea"},
    "Amarelo": {"botao_bg": "#ffc107", "botao_fg": "#000000", "fundo": "#fff9e6"},
}

def aplicar_estilos():
    paleta = st.session_state.get("paleta_cor", "Padrão")
    cores = PALETAS[paleta]
    st.markdown(f"""
        <style>
        .stButton > button {{
            background-color: {cores['botao_bg']} !important;
            color: {cores['botao_fg']} !important;
            border-radius: 6px;
            height: 3em;
            width: 100%;
            margin: 5px 0;
            font-weight: bold;
            border: none;
        }}
        .css-1d391kg {{
            background-color: {cores['fundo']} !important;
        }}
        .sidebar .css-1d391kg {{
            background-color: {cores['fundo']} !important;
        }}
        </style>
    """, unsafe_allow_html=True)

# --- Menu lateral com botões fixos e botão configuração ---
def menu_lateral():
    st.sidebar.title("Menu")

    aplicar_estilos()

    if 'pagina' not in st.session_state:
        st.session_state['pagina'] = "Dashboard"

    if st.sidebar.button("Dashboard"):
        st.session_state['pagina'] = "Dashboard"
    if st.sidebar.button("Cadastro Cliente"):
        st.session_state['pagina'] = "Cadastro Cliente"
    if st.sidebar.button("Cadastro Serviço"):
        st.session_state['pagina'] = "Cadastro Serviço"
    if st.sidebar.button("Cadastro Produto"):
        st.session_state['pagina'] = "Cadastro Produto"
    if st.sidebar.button("Agendamento"):
        st.session_state['pagina'] = "Agendamento"
    if st.sidebar.button("Vendas"):
        st.session_state['pagina'] = "Vendas"
    if st.sidebar.button("Despesas"):
        st.session_state['pagina'] = "Despesas"
    if st.sidebar.button("Relatórios"):
        st.session_state['pagina'] = "Relatórios"
    if st.sidebar.button("Clientes Cancelados"):
        st.session_state['pagina'] = "Clientes Cancelados"
    if st.sidebar.button("⚙️ Configurações"):
        st.session_state['pagina'] = "Configurações"
    if st.sidebar.button("Sair"):
        st.session_state['login'] = False
        st.experimental_rerun()

    return st.session_state['pagina']

# --- Páginas ---

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
        df_vendas_group = pd.DataFrame(columns=["data", "valor"])

    # Dados despesas
    cursor.execute("SELECT data, valor FROM despesas")
    despesas_raw = cursor.fetchall()
    if despesas_raw:
        df_despesas = pd.DataFrame(despesas_raw, columns=["data", "valor"])
        df_despesas['data'] = pd.to_datetime(df_despesas['data']).dt.date
        df_despesas_group = df_despesas.groupby('data').sum().reset_index()
    else:
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

def pagina_cadastro_cliente_admin():
    st.header("Cadastro Cliente (Admin)")
    with st.form("form_cliente_admin", clear_on_submit=True):
        nome = st.text_input("Nome completo")
        telefone = st.text_input("Telefone")
        email = st.text_input("Email")
        anamnese = st.text_area("Anamnese")
        bebida = st.text_input("Bebida Preferida")
        gosto = st.text_input("Gosto Musical")
        # Para assinatura e foto deixarei simples: receber base64 texto e bytes
        assinatura = st.text_area("Assinatura Digital (base64, opcional)")
        foto = st.file_uploader("Foto (JPEG/PNG)", type=["jpg","jpeg","png"])

        foto_bytes = None
        if foto is not None:
            foto_bytes = foto.read()

        submit = st.form_submit_button("Salvar Cliente")
        if submit:
            if not nome.strip():
                st.error("Nome obrigatório")
            else:
                salvar_cliente(nome, telefone, email, anamnese, bebida, gosto, assinatura, foto_bytes)
                st.success("Cliente salvo com sucesso!")

    clientes = carregar_clientes(ativos=True)
    st.subheader("Clientes Ativos")
    for c in clientes:
        st.write(f"ID {c[0]} | {c[1]} | Telefone: {c[2]}")

def pagina_cadastro_servico():
    st.header("Cadastro Serviço")
    with st.form("form_servico", clear_on_submit=True):
        nome = st.text_input("Nome do serviço")
        descricao = st.text_area("Descrição")
        duracao = st.number_input("Duração (minutos)", min_value=1, step=1)
        valor = st.number_input("Valor (R$)", min_value=0.0, step=0.01, format="%.2f")

        submit = st.form_submit_button("Salvar Serviço")
        if submit:
            if not nome.strip():
                st.error("Nome obrigatório")
            else:
                salvar_servico(nome, descricao, duracao, valor)
                st.success("Serviço salvo")

    servicos = carregar_servicos()
    st.subheader("Serviços cadastrados")
    for s in servicos:
        st.write(f"ID {s[0]} | {s[1]} | Valor: R$ {s[4]:.2f} | Duração: {s[3]} min")

def pagina_cadastro_produto():
    st.header("Cadastro Produto")
    with st.form("form_produto", clear_on_submit=True):
        nome = st.text_input("Nome do produto")
        descricao = st.text_area("Descrição")
        preco_custo = st.number_input("Preço de Custo (R$)", min_value=0.0, step=0.01, format="%.2f")
        preco_venda = st.number_input("Preço de Venda (R$)", min_value=0.0, step=0.01, format="%.2f")
        quantidade = st.number_input("Quantidade em estoque", min_value=0, step=1)

        submit = st.form_submit_button("Salvar Produto")
        if submit:
            if not nome.strip():
                st.error("Nome obrigatório")
            else:
                salvar_produto(nome, descricao, preco_custo, preco_venda, quantidade)
                st.success("Produto salvo")

    produtos = carregar_produtos()
    st.subheader("Produtos cadastrados")
    for p in produtos:
        st.write(f"ID {p[0]} | {p[1]} | Custo: R$ {p[3]:.2f} | Venda: R$ {p[4]:.2f} | Estoque: {p[5]}")

def pagina_agendamento():
    st.header("Agendamento")
    clientes = carregar_clientes()
    servicos = carregar_servicos()

    clientes_dict = {f"{c[1]} (ID {c[0]})": c[0] for c in clientes}
    servicos_dict = {f"{s[1]} (ID {s[0]})": s[0] for s in servicos}

    with st.form("form_agendamento"):
        cliente_sel = st.selectbox("Cliente", list(clientes_dict.keys()))
        servico_sel = st.selectbox("Serviço", list(servicos_dict.keys()))
        data_hora = st.datetime_input("Data e Hora do agendamento", datetime.now())
        submit = st.form_submit_button("Salvar Agendamento")
        if submit:
            salvar_agendamento(clientes_dict[cliente_sel], servicos_dict[servico_sel], data_hora.strftime("%Y-%m-%d %H:%M:%S"))
            st.success("Agendamento salvo!")

    agendamentos = carregar_agendamentos()
    st.subheader("Agendamentos Ativos")
    for a in agendamentos:
        st.write(f"ID {a[0]} | Cliente: {a[1]} | Serviço: {a[2]} | Data/Hora: {a[3]}")

def pagina_vendas():
    st.header("Painel de Vendas")

    clientes = carregar_clientes()
    servicos = carregar_servicos()
    produtos = carregar_produtos()

    clientes_dict = {f"{c[1]} (ID {c[0]})": c[0] for c in clientes}
    servicos_dict = {f"{s[1]} (ID {s[0]})": s[0] for s in servicos}
    produtos_dict = {f"{p[1]} (ID {p[0]})": p[0] for p in produtos}

    with st.form("form_venda"):
        tipo_venda = st.radio("Tipo de venda", ("Serviço", "Produto"))
        cliente_sel = st.selectbox("Cliente", list(clientes_dict.keys()))

        forma_pagamento = st.selectbox("Forma de pagamento", ["Dinheiro", "Cartão Crédito", "Cartão Débito", "Pix"])

        if tipo_venda == "Serviço":
            servico_sel = st.selectbox("Serviço", list(servicos_dict.keys()))
            valor = st.number_input("Valor (R$)", min_value=0.0, step=0.01, format="%.2f")
            submit = st.form_submit_button("Registrar Venda")
            if submit:
                salvar_venda_servico(clientes_dict[cliente_sel], servicos_dict[servico_sel], valor, forma_pagamento)
                st.success("Venda de serviço registrada!")
        else:
            produto_sel = st.selectbox("Produto", list(produtos_dict.keys()))
            quantidade = st.number_input("Quantidade", min_value=1, step=1)
            submit = st.form_submit_button("Registrar Venda")
            if submit:
                sucesso, msg = salvar_venda_produto(clientes_dict[cliente_sel], produtos_dict[produto_sel], quantidade, forma_pagamento)
                if sucesso:
                    st.success(msg)
                else:
                    st.error(msg)

    vendas = carregar_vendas()
    st.subheader("Vendas Ativas")
    for v in vendas:
        st.write(f"ID {v[0]} | Cliente: {v[1]} | Serviço: {v[2] or '-'} | Produto: {v[3] or '-'} | Qtde: {v[4] or '-'} | Valor: R$ {v[5]:.2f} | Pagamento: {v[6]} | Data: {v[7]}")

def pagina_despesas():
    st.header("Despesas")

    with st.form("form_despesa", clear_on_submit=True):
        descricao = st.text_input("Descrição")
        valor = st.number_input("Valor (R$)", min_value=0.0, step=0.01, format="%.2f")
        data = st.date_input("Data", datetime.today())
        quantidade = st.number_input("Quantidade", min_value=1, step=1, value=1)
        observacao = st.text_area("Observação (opcional)")

        submit = st.form_submit_button("Registrar Despesa")
        if submit:
            if not descricao.strip():
                st.error("Descrição obrigatória")
            else:
                salvar_despesa(descricao, valor, data.strftime("%Y-%m-%d"), quantidade, observacao)
                st.success("Despesa registrada")

    despesas = carregar_despesas()
    st.subheader("Despesas registradas")
    for d in despesas:
        st.write(f"ID {d[0]} | {d[1]} | Valor: R$ {d[2]:.2f} | Data: {d[3]} | Quantidade: {d[4]} | Obs: {d[5]}")

def pagina_relatorios():
    st.title("Relatórios")

    # Relatório Vendas
    st.header("Relatório de Vendas")
    vendas = carregar_vendas()
    df_vendas = pd.DataFrame(vendas, columns=["ID", "Cliente", "Serviço", "Produto", "Quantidade", "Valor", "Pagamento", "Data", "Status"])
    if not df_vendas.empty:
        df_vendas['Data'] = pd.to_datetime(df_vendas['Data'])
        filtro_data = st.date_input("Filtrar vendas por data", [])
        # Filtro opcional por data (de/até)
        if filtro_data:
            if len(filtro_data) == 2:
                df_vendas = df_vendas[(df_vendas['Data'] >= pd.to_datetime(filtro_data[0])) & (df_vendas['Data'] <= pd.to_datetime(filtro_data[1]))]
        st.dataframe(df_vendas)
        # Exportar CSV
        csv = df_vendas.to_csv(index=False).encode('utf-8')
        st.download_button("Download CSV Vendas", csv, "relatorio_vendas.csv", "text/csv")
    else:
        st.info("Nenhuma venda registrada.")

    # Relatório Despesas
    st.header("Relatório de Despesas")
    despesas = carregar_despesas()
    df_despesas = pd.DataFrame(despesas, columns=["ID", "Descrição", "Valor", "Data", "Quantidade", "Observação"])
    if not df_despesas.empty:
        df_despesas['Data'] = pd.to_datetime(df_despesas['Data'])
        filtro_data = st.date_input("Filtrar despesas por data", [])
        if filtro_data:
            if len(filtro_data) == 2:
                df_despesas = df_despesas[(df_despesas['Data'] >= pd.to_datetime(filtro_data[0])) & (df_despesas['Data'] <= pd.to_datetime(filtro_data[1]))]
        st.dataframe(df_despesas)
        csv = df_despesas.to_csv(index=False).encode('utf-8')
        st.download_button("Download CSV Despesas", csv, "relatorio_despesas.csv", "text/csv")
    else:
        st.info("Nenhuma despesa registrada.")

def pagina_clientes_cancelados():
    st.header("Clientes Cancelados")
    clientes = carregar_clientes(ativos=False)
    for c in clientes:
        st.write(f"ID {c[0]} | {c[1]} | Telefone: {c[2]}")

def pagina_configuracoes():
    st.header("Configurações")

    paleta_atual = st.session_state.get("paleta_cor", "Padrão")
    nova_paleta = st.selectbox("Escolha a paleta de cores", list(PALETAS.keys()), index=list(PALETAS.keys()).index(paleta_atual))
    if st.button("Salvar"):
        st.session_state["paleta_cor"] = nova_paleta
        st.success(f"Paleta alterada para: {nova_paleta}")

def pagina_login():
    st.title("Login Studio Beleza")
    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        cursor.execute("SELECT senha FROM usuarios WHERE usuario = ?", (usuario,))
        res = cursor.fetchone()
        if res and res[0] == senha:
            st.session_state['login'] = True
            st.session_state['usuario'] = usuario
            st.experimental_rerun()
        else:
            st.error("Usuário ou senha inválidos")

# --- Main ---
def main():
    if 'login' not in st.session_state:
        st.session_state['login'] = False
    if 'paleta_cor' not in st.session_state:
        st.session_state['paleta_cor'] = "Padrão"

    if not st.session_state['login']:
        pagina_login()
        return

    pagina = menu_lateral()

    if pagina == "Dashboard":
        pagina_dashboard()
    elif pagina == "Cadastro Cliente":
        pagina_cadastro_cliente_admin()
    elif pagina == "Cadastro Serviço":
        pagina_cadastro_servico()
    elif pagina == "Cadastro Produto":
        pagina_cadastro_produto()
    elif pagina == "Agendamento":
        pagina_agendamento()
    elif pagina == "Vendas":
        pagina_vendas()
    elif pagina == "Despesas":
        pagina_despesas()
    elif pagina == "Relatórios":
        pagina_relatorios()
    elif pagina == "Clientes Cancelados":
        pagina_clientes_cancelados()
    elif pagina == "Configurações":
        pagina_configuracoes()
    else:
        st.write(f"Página '{pagina}' não implementada.")

if __name__ == "__main__":
    main()
