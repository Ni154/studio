import streamlit as st
import sqlite3
from datetime import datetime
import base64
import io
from PIL import Image
from streamlit_drawable_canvas import st_canvas
import pandas as pd
import plotly.express as px

# --- Banco de dados ---
conn = sqlite3.connect('studio_beauty.db', check_same_thread=False)
cursor = conn.cursor()

def criar_tabelas():
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
    criado_em = data
    cursor.execute('''
        INSERT INTO vendas (cliente_id, servico_id, produto_id, quantidade, valor, forma_pagamento, status, data, criado_em) 
        VALUES (?, ?, NULL, NULL, ?, ?, 'ativo', ?, ?)
    ''', (cliente_id, servico_id, valor, forma_pagamento, data, criado_em))
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

def mostrar_foto(foto_blob):
    if foto_blob:
        img = Image.open(io.BytesIO(foto_blob))
        st.image(img, width=150)

def mostrar_assinatura(assinatura_b64):
    if assinatura_b64:
        assinatura_bytes = base64.b64decode(assinatura_b64)
        img = Image.open(io.BytesIO(assinatura_bytes))
        st.image(img, width=200)

# --- Página pública para cadastro externo via link ---

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

# --- Interface Streamlit principal ---

pagina = st.experimental_get_query_params().get("page", ["main"])[0]

if pagina == "cadastro_cliente":
    pagina_cadastro_externo()

else:
    st.title("Sistema Studio Beleza")

    menu = st.sidebar.selectbox("Menu", [
        "Dashboard Administrativo",
        "Cadastro Cliente", 
        "Cadastro Serviço",
        "Cadastro Produto",
        "Agendamento",
        "Painel Vendas",
        "Clientes Cancelados",
        "Agendamentos Cancelados",
        "Vendas Canceladas"
    ])

    if menu == "Cadastro Cliente":
        st.header("Cadastro de Clientes")
        with st.form("form_cliente", clear_on_submit=True):
            nome = st.text_input("Nome completo", max_chars=100)
            telefone = st.text_input("Telefone")
            email = st.text_input("Email")
            anamnese = st.text_area("Ficha de Anamnese")
            bebida = st.radio("Bebida preferida", options=["Capuccino", "Soda Italiana"])
            gosto_musical = st.text_input("Gosto musical")

            st.markdown("Assinatura da cliente (desenhe abaixo):")
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

            foto = st.file_uploader("Upload de foto / selfie (jpg, png)", type=['jpg', 'jpeg', 'png'])

            submit = st.form_submit_button("Salvar Cliente")

            if submit:
                if not nome.strip():
                    st.error("Nome é obrigatório!")
                elif canvas_result.image_data is None:
                    st.error("Por favor, faça a assinatura digital.")
                else:
                    img = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
                    buffered = io.BytesIO()
                    img.save(buffered, format="PNG")
                    assinatura_b64 = base64.b64encode(buffered.getvalue()).decode()

                    foto_bytes = foto.read() if foto else None

                    salvar_cliente(nome, telefone, email, anamnese, bebida, gosto_musical, assinatura_b64, foto_bytes)
                    st.success("Cliente cadastrado com sucesso!")

    elif menu == "Cadastro Serviço":
        st.header("Cadastro de Serviços")
        with st.form("form_servico", clear_on_submit=True):
            nome = st.text_input("Nome do serviço")
            descricao = st.text_area("Descrição")
            duracao = st.number_input("Duração (minutos)", min_value=1, step=1)
            valor = st.number_input("Valor (R$)", min_value=0.0, step=0.1, format="%.2f")
            submit = st.form_submit_button("Salvar Serviço")
            if submit:
                if not nome.strip():
                    st.error("Nome do serviço obrigatório!")
                else:
                    salvar_servico(nome, descricao, duracao, valor)
                    st.success("Serviço cadastrado!")

    elif menu == "Cadastro Produto":
        st.header("Cadastro de Produtos")
        with st.form("form_produto", clear_on_submit=True):
            nome = st.text_input("Nome do produto")
            descricao = st.text_area("Descrição")
            preco = st.number_input("Preço (R$)", min_value=0.0, step=0.1, format="%.2f")
            quantidade = st.number_input("Quantidade em estoque", min_value=0, step=1)
            submit = st.form_submit_button("Salvar Produto")
            if submit:
                if not nome.strip():
                    st.error("Nome obrigatório!")
                else:
                    salvar_produto(nome, descricao, preco, quantidade)
                    st.success("Produto cadastrado!")

    elif menu == "Agendamento":
        st.header("Agendar Serviço")
        clientes = carregar_clientes(ativos=True)
        servicos = carregar_servicos()
        if not clientes or not servicos:
            st.warning("Cadastre clientes e serviços primeiro!")
        else:
            cliente_dict = {f"{c[1]} (ID:{c[0]})": c[0] for c in clientes}
            servico_dict = {f"{s[1]} (R$ {s[4]:.2f})": s[0] for s in servicos}

            cliente_sel = st.selectbox("Selecione o cliente", list(cliente_dict.keys()))
            servico_sel = st.selectbox("Selecione o serviço", list(servico_dict.keys()))
            data_hora = st.datetime_input("Data e hora do agendamento", value=datetime.now())

            cursor.execute('''
                SELECT COUNT(*) FROM agendamentos
                WHERE data_hora = ? AND status = 'agendado'
            ''', (data_hora.strftime("%Y-%m-%d %H:%M:%S"),))
            conflito = cursor.fetchone()[0] > 0

            if conflito:
                st.error("Já existe um agendamento para essa data e hora!")
            else:
                if st.button("Agendar"):
                    salvar_agendamento(cliente_dict[cliente_sel], servico_dict[servico_sel], data_hora.strftime("%Y-%m-%d %H:%M:%S"))
                    st.success("Agendamento realizado!")

        st.subheader("Agendamentos Ativos")
        agendamentos = carregar_agendamentos(ativos=True)
        for ag in agendamentos:
            ag_id, cliente_nome, servico_nome, data_hora, status = ag
            st.write(f"ID: {ag_id} - Cliente: {cliente_nome} - Serviço: {servico_nome} - Data/Hora: {data_hora}")
            if st.button(f"Cancelar Agendamento #{ag_id}", key=f"cancel_ag_{ag_id}"):
                cancelar_agendamento(ag_id)
                st.success(f"Agendamento #{ag_id} cancelado!")
                st.experimental_rerun()

    elif menu == "Painel Vendas":
        st.header("Registrar Venda")

        venda_tipo = st.radio("Tipo de venda", ["Serviço", "Produto"])

        clientes = carregar_clientes(ativos=True)
        cliente_dict = {f"{c[1]} (ID:{c[0]})": c[0] for c in clientes}

        if venda_tipo == "Serviço":
            servicos = carregar_servicos()
            servico_dict = {f"{s[1]} (R$ {s[4]:.2f})": (s[0], s[4]) for s in servicos}

            cliente_sel = st.selectbox("Cliente", list(cliente_dict.keys()))
            servico_sel = st.selectbox("Serviço", list(servico_dict.keys()))
            valor = servico_dict[servico_sel][1]
            forma_pagamento = st.selectbox("Forma de pagamento", ["Dinheiro", "Cartão Crédito", "Cartão Débito", "Pix"])

            if st.button("Registrar Venda"):
                salvar_venda_servico(cliente_dict[cliente_sel], servico_dict[servico_sel][0], valor, forma_pagamento)
                st.success("Venda de serviço registrada!")

        else:  # Produto
            produtos = carregar_produtos()
            if not produtos:
                st.warning("Cadastre produtos primeiro!")
            else:
                produto_dict = {f"{p[1]} (R$ {p[3]:.2f}) - Estoque: {p[4]}": (p[0], p[3], p[4]) for p in produtos}

                produto_sel = st.selectbox("Produto", list(produto_dict.keys()))
                quantidade_vendida = st.number_input("Quantidade vendida", min_value=1, max_value=produto_dict[produto_sel][2], step=1)

                forma_pagamento = st.selectbox("Forma de pagamento", ["Dinheiro", "Cartão Crédito", "Cartão Débito", "Pix"])

                if st.button("Registrar Venda de Produto"):
                    produto_id = produto_dict[produto_sel][0]
                    sucesso, msg = salvar_venda_produto(cliente_dict[cliente_sel], produto_id, quantidade_vendida, forma_pagamento)
                    if sucesso:
                        st.success(msg)
                    else:
                        st.error(msg)

        st.subheader("Vendas Ativas")
        vendas = carregar_vendas(ativos=True)
        for v in vendas:
            v_id, cliente_nome, servico_nome, produto_nome, quantidade, valor, forma_pag, data, status = v
            desc = f"ID: {v_id} - Cliente: {cliente_nome} - "
            if servico_nome:
                desc += f"Serviço: {servico_nome} - "
            if produto_nome:
                desc += f"Produto: {produto_nome} (Qtd: {quantidade}) - "
            desc += f"Valor: R${valor:.2f} - Pagamento: {forma_pag} - Data: {data}"
            st.write(desc)
            if st.button(f"Cancelar Venda #{v_id}", key=f"cancel_venda_{v_id}"):
                cancelar_venda(v_id)
                st.success(f"Venda #{v_id} cancelada!")
                st.experimental_rerun
