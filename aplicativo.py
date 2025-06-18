import streamlit as st
import sqlite3
from datetime import datetime
import base64
import io
from PIL import Image
from streamlit_drawable_canvas import st_canvas
import pandas as pd
import plotly.express as px
import hashlib

# --- Banco de dados ---
conn = sqlite3.connect('studio_beauty.db', check_same_thread=False)
cursor = conn.cursor()

def criar_tabelas():
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        senha_hash TEXT NOT NULL,
        criado_em TEXT
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
        preco REAL,
        quantidade INTEGER DEFAULT 0
    )''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS agendamentos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cliente_id INTEGER,
        servico_id INTEGER,
        data_hora TEXT,
        status TEXT DEFAULT 'agendado',
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
        status TEXT DEFAULT 'ativo',
        data TEXT,
        criado_em TEXT,
        FOREIGN KEY(cliente_id) REFERENCES clientes(id),
        FOREIGN KEY(servico_id) REFERENCES servicos(id),
        FOREIGN KEY(produto_id) REFERENCES produtos(id)
    )''')
    conn.commit()

criar_tabelas()

# --- Funções para login e hash de senha ---

def hash_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()

def criar_usuario(username, senha):
    try:
        cursor.execute("INSERT INTO usuarios (username, senha_hash, criado_em) VALUES (?, ?, ?)",
                      (username, hash_senha(senha), datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False

def validar_login(username, senha):
    cursor.execute("SELECT senha_hash FROM usuarios WHERE username = ?", (username,))
    row = cursor.fetchone()
    if row and row[0] == hash_senha(senha):
        return True
    return False

# --- Funções comuns ---

def salvar_cliente(nome, telefone, email, anamnese, bebida, gosto, assinatura_b64, foto_bytes):
    criado_em = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('''
        INSERT INTO clientes 
        (nome, telefone, email, anamnese, bebida_preferida, gosto_musical, assinatura, foto, criado_em)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (nome, telefone, email, anamnese, bebida, gosto, assinatura_b64, foto_bytes, criado_em))
    conn.commit()

def salvar_servico(nome, descricao, duracao, valor):
    cursor.execute('''
        INSERT INTO servicos (nome, descricao, duracao, valor) VALUES (?, ?, ?, ?)
    ''', (nome, descricao, duracao, valor))
    conn.commit()

def salvar_produto(nome, descricao, preco, quantidade):
    cursor.execute('''
        INSERT INTO produtos (nome, descricao, preco, quantidade) VALUES (?, ?, ?, ?)
    ''', (nome, descricao, preco, quantidade))
    conn.commit()

def salvar_agendamento(cliente_id, servico_id, data_hora):
    criado_em = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('''
        INSERT INTO agendamentos (cliente_id, servico_id, data_hora, criado_em) VALUES (?, ?, ?, ?)
    ''', (cliente_id, servico_id, data_hora, criado_em))
    conn.commit()

def salvar_venda_servico(cliente_id, servico_id, valor, forma_pagamento):
    data = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('''
        INSERT INTO vendas (cliente_id, servico_id, produto_id, quantidade, valor, forma_pagamento, status, data, criado_em) 
        VALUES (?, ?, NULL, NULL, ?, ?, 'ativo', ?, ?)
    ''', (cliente_id, servico_id, valor, forma_pagamento, data, data))
    conn.commit()

def salvar_venda_produto(cliente_id, produto_id, quantidade_vendida, forma_pagamento):
    cursor.execute("SELECT preco, quantidade FROM produtos WHERE id = ?", (produto_id,))
    res = cursor.fetchone()
    if not res:
        return False, "Produto não encontrado"
    preco, estoque_atual = res
    if estoque_atual < quantidade_vendida:
        return False, "Estoque insuficiente"
    novo_estoque = estoque_atual - quantidade_vendida
    valor_total = preco * quantidade_vendida

    cursor.execute("UPDATE produtos SET quantidade = ? WHERE id = ?", (novo_estoque, produto_id))

    data = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('''
        INSERT INTO vendas (cliente_id, servico_id, produto_id, quantidade, valor, forma_pagamento, status, data, criado_em)
        VALUES (?, NULL, ?, ?, ?, ?, 'ativo', ?, ?)
    ''', (cliente_id, produto_id, quantidade_vendida, valor_total, forma_pagamento, data, data))
    conn.commit()
    return True, "Venda de produto registrada"

def cancelar_cliente(cliente_id):
    cursor.execute("UPDATE clientes SET status = 'cancelado' WHERE id = ?", (cliente_id,))
    conn.commit()

def cancelar_agendamento(agendamento_id):
    cursor.execute("UPDATE agendamentos SET status = 'cancelado' WHERE id = ?", (agendamento_id,))
    conn.commit()

def cancelar_venda(venda_id):
    cursor.execute("UPDATE vendas SET status = 'cancelado' WHERE id = ?", (venda_id,))
    conn.commit()

def carregar_clientes(ativos=True):
    status = 'ativo' if ativos else 'cancelado'
    cursor.execute(f"SELECT id, nome FROM clientes WHERE status = ?", (status,))
    return cursor.fetchall()

def carregar_servicos():
    cursor.execute("SELECT id, nome, descricao, duracao, valor FROM servicos")
    return cursor.fetchall()

def carregar_produtos():
    cursor.execute("SELECT id, nome, descricao, preco, quantidade FROM produtos")
    return cursor.fetchall()

def carregar_agendamentos(ativos=True):
    status = 'agendado' if ativos else 'cancelado'
    cursor.execute(f'''
        SELECT a.id, c.nome, s.nome, a.data_hora, a.status
        FROM agendamentos a
        JOIN clientes c ON a.cliente_id = c.id
        JOIN servicos s ON a.servico_id = s.id
        WHERE a.status = ?
        ORDER BY a.data_hora
    ''', (status,))
    return cursor.fetchall()

def carregar_vendas(ativos=True):
    status = 'ativo' if ativos else 'cancelado'
    cursor.execute(f'''
        SELECT v.id, c.nome, s.nome, p.nome, v.quantidade, v.valor, v.forma_pagamento, v.data, v.status
        FROM vendas v
        LEFT JOIN clientes c ON v.cliente_id = c.id
        LEFT JOIN servicos s ON v.servico_id = s.id
        LEFT JOIN produtos p ON v.produto_id = p.id
        WHERE v.status = ?
        ORDER BY v.data DESC
    ''', (status,))
    return cursor.fetchall()

# --- Tela de Login ---

def tela_login():
    st.title("Login - Studio Beleza")

    username = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")

    if st.button("Entrar"):
        if validar_login(username, senha):
            st.session_state['usuario_logado'] = username
            st.success(f"Bem vindo, {username}!")
            st.experimental_rerun()
        else:
            st.error("Usuário ou senha incorretos")

    cursor.execute("SELECT COUNT(*) FROM usuarios")
    if cursor.fetchone()[0] == 0:
        st.info("Nenhum usuário cadastrado. Crie o usuário admin:")
        novo_user = st.text_input("Novo usuário")
        nova_senha = st.text_input("Nova senha", type="password")
        if st.button("Criar usuário admin"):
            if novo_user.strip() and nova_senha.strip():
                if criar_usuario(novo_user.strip(), nova_senha.strip()):
                    st.success("Usuário criado com sucesso! Faça login.")
                else:
                    st.error("Erro ao criar usuário. Talvez o nome já exista.")
            else:
                st.error("Usuário e senha não podem estar vazios.")

def logout():
    if 'usuario_logado' in st.session_state:
        del st.session_state['usuario_logado']
    st.experimental_rerun()

def set_pagina(pagina):
    st.session_state.pagina = pagina

# --- Cadastro externo via link ---

def pagina_cadastro_externo():
    st.title("Cadastro Cliente - Studio Beleza")
    st.write("Preencha seus dados abaixo:")

    nome = st.text_input("Nome completo", max_chars=100)
    telefone = st.text_input("Telefone")
    email = st.text_input("Email")
    anamnese = st.text_area("Ficha de Anamnese")
    bebida = st.radio("Bebida preferida", options=["Capuccino", "Soda Italiana"])
    gosto_musical = st.text_input("Gosto musical")

    st.markdown("Assinatura digital:")
    canvas_result = st_canvas(
        fill_color="rgba(0, 0, 255, 0.3)",
        stroke_width=2,
        stroke_color="#000000",
        background_color="#eee",
        height=150,
        width=400,
        drawing_mode="freedraw",
        key="canvas_ext",
    )
    foto = st.file_uploader("Upload de foto / selfie (jpg, png)", type=['jpg','jpeg','png'])

    if st.button("Enviar Cadastro"):
        if not nome.strip():
            st.error("Nome é obrigatório!")
        elif canvas_result.image_data is None:
            st.error("Assine no campo abaixo!")
        else:
            img = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
            buffered = io.BytesIO()
            img.save(buffered, format="PNG")
            assinatura_b64 = base64.b64encode(buffered.getvalue()).decode()

            foto_bytes = foto.read() if foto else None

            salvar_cliente(nome, telefone, email, anamnese, bebida, gosto_musical, assinatura_b64, foto_bytes)
            st.success("Cadastro enviado com sucesso! Obrigado.")

# --- Main ---

if "pagina" not in st.session_state:
    st.session_state.pagina = "dashboard"

pagina_url = st.query_params.get("page", [None])[0]

if pagina_url == "cadastro_cliente":
    pagina_cadastro_externo()
else:
    if 'usuario_logado' not in st.session_state:
        tela_login()
    else:
        st.sidebar.title(f"Olá, {st.session_state['usuario_logado']}")
        if st.sidebar.button("Logout"):
            logout()

        with st.sidebar:
            st.title("Menu")
            st.button("Dashboard", on_click=set_pagina, args=("dashboard",))
            st.button("Cadastro Cliente", on_click=set_pagina, args=("cadastro_cliente",))
            st.button("Cadastro Serviço", on_click=set_pagina, args=("cadastro_servico",))
            st.button("Cadastro Produto", on_click=set_pagina, args=("cadastro_produto",))
            st.button("Agendamento", on_click=set_pagina, args=("agendamento",))
            st.button("Painel Vendas", on_click=set_pagina, args=("vendas",))
            st.button("Clientes Cancelados", on_click=set_pagina, args=("clientes_cancelados",))
            st.button("Agendamentos Cancelados", on_click=set_pagina, args=("agendamentos_cancelados",))
            st.button("Vendas Canceladas", on_click=set_pagina, args=("vendas_canceladas",))

        pagina = st.session_state.pagina

        # Dashboard
        if pagina == "dashboard":
            st.title("Dashboard Administrativo")

            cursor.execute("SELECT COUNT(*) FROM clientes WHERE status = 'ativo'")
            qtd_clientes = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM servicos")
            qtd_servicos = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM produtos")
            qtd_produtos = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM agendamentos WHERE status = 'agendado'")
            qtd_agendamentos = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM vendas WHERE status = 'ativo'")
            qtd_vendas = cursor.fetchone()[0]

            st.metric("Clientes Ativos", qtd_clientes)
            st.metric("Serviços Cadastrados", qtd_servicos)
            st.metric("Produtos Cadastrados", qtd_produtos)
            st.metric("Agendamentos Ativos", qtd_agendamentos)
            st.metric("Vendas Ativas", qtd_vendas)

            cursor.execute('''
                SELECT s.nome, COUNT(v.id) AS qtd, SUM(v.valor) AS receita
                FROM vendas v
                JOIN servicos s ON v.servico_id = s.id
                WHERE v.status = 'ativo' AND v.servico_id IS NOT NULL
                GROUP BY s.nome
            ''')
            serv_data = cursor.fetchall()
            if serv_data:
                df_serv = pd.DataFrame(serv_data, columns=["Serviço", "Quantidade", "Receita"])
                fig_serv = px.bar(df_serv, x="Serviço", y="Quantidade", title="Vendas por Serviço")
                st.plotly_chart(fig_serv)

            cursor.execute('''
                SELECT p.nome, COUNT(v.id) AS qtd, SUM(v.valor) AS receita
                FROM vendas v
                JOIN produtos p ON v.produto_id = p.id
                WHERE v.status = 'ativo' AND v.produto_id IS NOT NULL
                GROUP BY p.nome
            ''')
            prod_data = cursor.fetchall()
            if prod_data:
                df_prod = pd.DataFrame(prod_data, columns=["Produto", "Quantidade", "Receita"])
                fig_prod = px.bar(df_prod, x="Produto", y="Quantidade", title="Vendas por Produto")
                st.plotly_chart(fig_prod)

        # Cadastro Cliente
        elif pagina == "cadastro_cliente":
            st.header("Cadastro de Clientes")
            with st.form("form_cliente", clear_on_submit=True):
                nome = st.text_input("Nome completo", max_chars=100)
                telefone = st.text_input("Telefone")
                email = st.text_input("Email")
                anamnese = st.text_area("Ficha de Anamnese")
                bebida = st.radio("Bebida preferida", options=["Capuccino", "Soda Italiana"])
                gosto_musical = st.text_input("Gosto musical")

                st.markdown("Assinatura digital:")
                canvas_result = st_canvas(
                    fill_color="rgba(0, 0, 255, 0.3)",
                    stroke_width=2,
                    stroke_color="#000000",
                    background_color="#eee",
                    height=150,
                    width=400,
                    drawing_mode="freedraw",
                    key="canvas",
                )
                foto = st.file_uploader("Upload de foto / selfie (jpg, png)", type=['jpg','jpeg','png'])

                submit_cliente = st.form_submit_button("Salvar Cliente")

                if submit_cliente:
                    if not nome.strip():
                        st.error("Nome é obrigatório!")
                    elif canvas_result.image_data is None:
                        st.error("Assine no campo abaixo!")
                    else:
                        img = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
                        buffered = io.BytesIO()
                        img.save(buffered, format="PNG")
                        assinatura_b64 = base64.b64encode(buffered.getvalue()).decode()

                        foto_bytes = foto.read() if foto else None

                        salvar_cliente(nome, telefone, email, anamnese, bebida, gosto_musical, assinatura_b64, foto_bytes)
                        st.success("Cliente salvo com sucesso!")

        # Cadastro Serviço
        elif pagina == "cadastro_servico":
            st.header("Cadastro de Serviços")
            with st.form("form_servico", clear_on_submit=True):
                nome = st.text_input("Nome do serviço")
                descricao = st.text_area("Descrição")
                duracao = st.number_input("Duração (minutos)", min_value=1, step=1)
                valor = st.number_input("Valor (R$)", min_value=0.0, step=0.01, format="%.2f")

                submit_servico = st.form_submit_button("Salvar Serviço")

                if submit_servico:
                    if not nome.strip():
                        st.error("Nome do serviço é obrigatório")
                    else:
                        salvar_servico(nome, descricao, duracao, valor)
                        st.success("Serviço salvo com sucesso!")

            # Listar serviços cadastrados
            servicos = carregar_servicos()
            st.subheader("Serviços cadastrados")
            for s in servicos:
                st.write(f"ID: {s[0]} - {s[1]} - R$ {s[4]:.2f} - {s[3]} min")

        # Cadastro Produto
        elif pagina == "cadastro_produto":
            st.header("Cadastro de Produtos")
            with st.form("form_produto", clear_on_submit=True):
                nome = st.text_input("Nome do produto")
                descricao = st.text_area("Descrição")
                preco = st.number_input("Preço (R$)", min_value=0.0, step=0.01, format="%.2f")
                quantidade = st.number_input("Quantidade em estoque", min_value=0, step=1)

                submit_produto = st.form_submit_button("Salvar Produto")

                if submit_produto:
                    if not nome.strip():
                        st.error("Nome do produto é obrigatório")
                    else:
                        salvar_produto(nome, descricao, preco, quantidade)
                        st.success("Produto salvo com sucesso!")

            produtos = carregar_produtos()
            st.subheader("Produtos cadastrados")
            for p in produtos:
                st.write(f"ID: {p[0]} - {p[1]} - R$ {p[3]:.2f} - Estoque: {p[4]}")

        # Agendamento
        elif pagina == "agendamento":
            st.header("Agendamento de Serviços")
            clientes = carregar_clientes()
            servicos = carregar_servicos()

            if not clientes or not servicos:
                st.warning("Cadastre clientes e serviços antes de agendar.")
            else:
                cliente_dict = {f"{c[1]} (ID:{c[0]})": c[0] for c in clientes}
                servico_dict = {f"{s[1]} (R$ {s[4]:.2f})": s[0] for s in servicos}

                cliente_sel = st.selectbox("Selecione o cliente", list(cliente_dict.keys()))
                servico_sel = st.selectbox("Selecione o serviço", list(servico_dict.keys()))
                data_hora = st.datetime_input("Data e hora do agendamento")

                if st.button("Agendar"):
                    salvar_agendamento(cliente_dict[cliente_sel], servico_dict[servico_sel], data_hora.strftime("%Y-%m-%d %H:%M:%S"))
                    st.success("Agendamento salvo com sucesso!")

            st.subheader("Agendamentos Ativos")
            agendamentos = carregar_agendamentos()
            for ag in agendamentos:
                ag_id, cliente_nome, servico_nome, data_hora_str, status = ag
                st.write(f"ID: {ag_id} - Cliente: {cliente_nome} - Serviço: {servico_nome} - Data/Hora: {data_hora_str}")
                if st.button(f"Cancelar Agendamento #{ag_id}", key=f"cancel_ag_{ag_id}"):
                    cancelar_agendamento(ag_id)
                    st.experimental_rerun()

        # Painel de Vendas
        elif pagina == "vendas":
            st.header("Painel de Vendas")

            clientes = carregar_clientes()
            servicos = carregar_servicos()
            produtos = carregar_produtos()

            if not clientes:
                st.warning("Cadastre clientes antes de realizar vendas.")
            else:
                cliente_dict = {f"{c[1]} (ID:{c[0]})": c[0] for c in clientes}
                servico_dict = {f"{s[1]} (R$ {s[4]:.2f})": s[0] for s in servicos}
                produto_dict = {f"{p[1]} (R$ {p[3]:.2f})": p[0] for p in produtos}

                tipo_venda = st.radio("Tipo de Venda", ["Serviço", "Produto"])
                cliente_sel = st.selectbox("Selecione o cliente", list(cliente_dict.keys()))

                if tipo_venda == "Serviço":
                    if not servicos:
                        st.warning("Cadastre serviços para realizar vendas.")
                    else:
                        servico_sel = st.selectbox("Selecione o serviço", list(servico_dict.keys()))
                        forma_pagamento = st.selectbox("Forma de pagamento", ["Dinheiro", "Cartão", "Pix"])

                        if st.button("Registrar Venda de Serviço"):
                            servico_id = servico_dict[servico_sel]
                            cursor.execute("SELECT valor FROM servicos WHERE id = ?", (servico_id,))
                            valor = cursor.fetchone()[0]
                            salvar_venda_servico(cliente_dict[cliente_sel], servico_id, valor, forma_pagamento)
                            st.success("Venda de serviço registrada!")
                else:
                    if not produtos:
                        st.warning("Cadastre produtos para realizar vendas.")
                    else:
                        produto_sel = st.selectbox("Selecione o produto", list(produto_dict.keys()))
                        quantidade = st.number_input("Quantidade", min_value=1, step=1)
                        forma_pagamento = st.selectbox("Forma de pagamento", ["Dinheiro", "Cartão", "Pix"])

                        if st.button("Registrar Venda de Produto"):
                            produto_id = produto_dict[produto_sel]
                            sucesso, msg = salvar_venda_produto(cliente_dict[cliente_sel], produto_id, quantidade, forma_pagamento)
                            if sucesso:
                                st.success(msg)
                            else:
                                st.error(msg)

            st.subheader("Vendas Ativas")
            vendas = carregar_vendas(ativos=True)
            for v in vendas:
                venda_id, cliente_nome, servico_nome, produto_nome, qtd, valor, forma_pagamento, data, status = v
                desc = servico_nome if servico_nome else produto_nome
                st.write(f"ID: {venda_id} - Cliente: {cliente_nome} - Item: {desc} - Qtde: {qtd if qtd else '-'} - Valor: R${valor:.2f} - Pagamento: {forma_pagamento} - Data: {data}")
                if st.button(f"Cancelar Venda #{venda_id}", key=f"cancel_venda_{venda_id}"):
                    cancelar_venda(venda_id)
                    st.experimental_rerun()

        # Clientes Cancelados
        elif pagina == "clientes_cancelados":
            st.header("Clientes Cancelados")
            clientes = carregar_clientes(ativos=False)
            for c in clientes:
                st.write(f"ID: {c[0]} - Nome: {c[1]}")

        # Agendamentos Cancelados
        elif pagina == "agendamentos_cancelados":
            st.header("Agendamentos Cancelados")
            agendamentos = carregar_agendamentos(ativos=False)
            for ag in agendamentos:
                ag_id, cliente_nome, servico_nome, data_hora, status = ag
                st.write(f"ID: {ag_id} - Cliente: {cliente_nome} - Serviço: {servico_nome} - Data/Hora: {data_hora} - Status: {status}")

        # Vendas Canceladas
        elif pagina == "vendas_canceladas":
            st.header("Vendas Canceladas")
            vendas = carregar_vendas(ativos=False)
            for v in vendas:
                venda_id, cliente_nome, servico_nome, produto_nome, qtd, valor, forma_pagamento, data, status = v
                desc = servico_nome if servico_nome else produto_nome
                st.write(f"ID: {venda_id} - Cliente: {cliente_nome} - Item: {desc} - Qtde: {qtd if qtd else '-'} - Valor: R${valor:.2f} - Pagamento: {forma_pagamento} - Data: {data} - Status: {status}")

        else:
            st.write("Página não encontrada.")
