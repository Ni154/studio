# SISTEMA COMPLETO PARA STUDIO DE DEPILAÇÃO
# Inclui login, menu, cadastro de clientes com anamnese e assinatura,
# agendamentos, serviços, produtos, vendas, despesas, relatórios e tema clínico

import streamlit as st
import sqlite3
from datetime import datetime, date
from streamlit_drawable_canvas import st_canvas
from PIL import Image
import io
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Studio de Depilação", layout="wide")

# BANCO DE DADOS
conn = sqlite3.connect("studio.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS usuarios (id INTEGER PRIMARY KEY, usuario TEXT, senha TEXT)")
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
cursor.execute("CREATE TABLE IF NOT EXISTS agendamentos (id INTEGER PRIMARY KEY, cliente_id INTEGER, servico TEXT, data TEXT, hora TEXT, status TEXT)")
cursor.execute("CREATE TABLE IF NOT EXISTS servicos (id INTEGER PRIMARY KEY, nome TEXT, descricao TEXT, duracao INTEGER, valor REAL)")
cursor.execute("CREATE TABLE IF NOT EXISTS produtos (id INTEGER PRIMARY KEY, nome TEXT, estoque INTEGER, valor REAL)")
cursor.execute("CREATE TABLE IF NOT EXISTS vendas (id INTEGER PRIMARY KEY, cliente_id INTEGER, data TEXT, forma_pagamento TEXT, total REAL)")
cursor.execute("CREATE TABLE IF NOT EXISTS vendas_itens (id INTEGER PRIMARY KEY, venda_id INTEGER, tipo TEXT, nome TEXT, quantidade INTEGER, preco REAL)")
cursor.execute("CREATE TABLE IF NOT EXISTS despesas (id INTEGER PRIMARY KEY, descricao TEXT, valor REAL, data TEXT)")
conn.commit()

# LOGIN
if "logado" not in st.session_state:
    st.session_state.logado = False
if not st.session_state.logado:
    st.title("🔐 Login")
    u = st.text_input("Usuário")
    s = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if u == "admin" and s == "admin":
            st.session_state.logado = True
            st.experimental_rerun()
        else:
            st.error("Acesso negado.")
    st.stop()

# MENU
menu = st.sidebar.radio("Menu", ["Início", "Clientes", "Agendamentos", "Serviços", "Produtos", "Vendas", "Despesas", "Relatórios", "Sair"])

if menu == "Início":
    st.title("🌿 Bem-vinda ao Studio de Depilação")
    st.markdown("Use o menu à esquerda para navegar no sistema.")

elif menu == "Clientes":
    st.title("👩 Cadastro de Clientes + Ficha de Avaliação")
    with st.form("cadastro_cliente"):
        col1, col2 = st.columns(2)
        with col1:
            nome = st.text_input("Nome completo")
            telefone = st.text_input("Telefone")
            data_nascimento = st.date_input("Data de nascimento", value=date.today())
            instagram = st.text_input("Instagram")
        with col2:
            cantor = st.text_input("Cantor favorito")
            bebida = st.text_input("Bebida favorita")
        st.markdown("### ✍️ Assinatura Digital")
        canvas_result = st_canvas(fill_color="rgba(255,255,255,0)", stroke_width=2, stroke_color="#000", background_color="#fff", height=150, drawing_mode="freedraw", key="canvas")
        assinatura_bytes = None
        if canvas_result.image_data is not None:
            img = canvas_result.image_data
            buffered = io.BytesIO()
            Image.fromarray((img[:, :, :3]).astype('uint8')).save(buffered, format="PNG")
            assinatura_bytes = buffered.getvalue()
        st.markdown("### 📋 Anamnese")
        col1, col2 = st.columns(2)
        with col1:
            epilacao = st.radio("Já fez epilação na cera?", ["SIM", "NÃO"])
            alergia = st.radio("Possui alergia?", ["SIM", "NÃO"])
            qual_alergia = st.text_input("Qual?", disabled=(alergia == "NÃO"))
            problema_pele = st.radio("Problemas de pele?", ["SIM", "NÃO"])
            tratamento = st.radio("Em tratamento dermatológico?", ["SIM", "NÃO"])
            tipo_pele = st.selectbox("Tipo de pele", ["SECA", "OLEOSA", "NORMAL"])
            hidrata = st.radio("Hidrata a pele?", ["SIM", "NÃO"])
            gravida = st.radio("Está grávida?", ["SIM", "NÃO"])
        with col2:
            medicamento = st.radio("Usa medicamento?", ["SIM", "NÃO"])
            qual_medicamento = st.text_input("Qual?", disabled=(medicamento == "NÃO"))
            dispositivo = st.selectbox("Dispositivo?", ["DIU", "Marca-passo", "Nenhum"])
            diabete = st.radio("Diabetes?", ["SIM", "NÃO"])
            encravado = st.radio("Pelos encravados?", ["SIM", "NÃO"])
            cirurgia = st.radio("Cirurgia recente?", ["SIM", "NÃO"])
            foliculite = st.radio("Foliculite?", ["SIM", "NÃO"])
            qual_foliculite = st.text_input("Qual?", disabled=(foliculite == "NÃO"))
            outro = st.radio("Outro problema?", ["SIM", "NÃO"])
            qual_outro = st.text_input("Qual?", disabled=(outro == "NÃO"))
            imagem = st.radio("Autoriza uso de imagem?", ["SIM", "NÃO"])
        if st.form_submit_button("Salvar Cadastro"):
            cursor.execute("INSERT INTO clientes (nome, telefone, data_nascimento, instagram, cantor_favorito, bebida_favorita, assinatura) VALUES (?, ?, ?, ?, ?, ?, ?)", (nome, telefone, str(data_nascimento), instagram, cantor, bebida, assinatura_bytes))
            cliente_id = cursor.lastrowid
            cursor.execute("INSERT INTO ficha_avaliacao (cliente_id, epilacao_anterio, alergia, qual_alergia, problema_pele, tratamento_dermatologico, tipo_pele, hidrata_pele, gravida, medicamento, qual_medicamento, dispositivo, diabete, pelos_encravados, cirurgia_recente, foliculite, qual_foliculite, outro_problema, qual_outro, autorizacao_imagem) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (cliente_id, epilacao, alergia, qual_alergia, problema_pele, tratamento, tipo_pele, hidrata, gravida, medicamento, qual_medicamento, dispositivo, diabete, encravado, cirurgia, foliculite, qual_foliculite, outro, qual_outro, imagem))
            conn.commit()
            st.success("Cadastro salvo com sucesso!")

elif menu == "Sair":
    st.session_state.logado = False
    st.experimental_rerun()

# As demais páginas (Agendamentos, Serviços, Produtos, Vendas, Despesas, Relatórios)
# serão adicionadas nas próximas partes, respeitando seu pedido de envio por partes se necessário.
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
        cliente = st.selectbox("Cliente", clientes, format_func=lambda x: f"{x[1]}")
        servico = st.selectbox("Serviço", [s[0] for s in servicos])
        data_agenda = st.date_input("Data", min_value=date.today())
        hora = st.time_input("Hora")
        if st.form_submit_button("Agendar"):
            cursor.execute("INSERT INTO agendamentos (cliente_id, servico, data, hora, status) VALUES (?, ?, ?, ?, ?)",
                           (cliente[0], servico, str(data_agenda), str(hora), "Ativo"))
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
            if st.button("❌ Cancelar", key=ag[0]):
                cursor.execute("UPDATE agendamentos SET status = 'Cancelado' WHERE id = ?", (ag[0],))
                conn.commit()
                st.experimental_rerun()
elif menu == "Serviços":
    st.title("📝 Cadastro de Serviços")
    with st.form("form_servico"):
        nome_serv = st.text_input("Nome do Serviço")
        desc_serv = st.text_area("Descrição")
        duracao = st.number_input("Duração (em minutos)", step=5, min_value=5)
        valor = st.number_input("Valor (R$)", step=0.5, min_value=0.0)
        if st.form_submit_button("Salvar Serviço"):
            cursor.execute("INSERT INTO servicos (nome, descricao, duracao, valor) VALUES (?, ?, ?, ?)",
                           (nome_serv, desc_serv, duracao, valor))
            conn.commit()
            st.success("Serviço salvo com sucesso!")

    st.markdown("### 📋 Lista de Serviços")
    servicos = cursor.execute("SELECT nome, descricao, duracao, valor FROM servicos").fetchall()
    for s in servicos:
        st.write(f"**{s[0]}** — {s[1]} | ⏱️ {s[2]} min | 💰 R$ {s[3]:.2f}")

elif menu == "Produtos":
    st.title("📦 Cadastro de Produtos")
    with st.form("form_produto"):
        nome_prod = st.text_input("Nome do Produto")
        estoque = st.number_input("Estoque", step=1, min_value=0)
        valor_prod = st.number_input("Valor (R$)", step=0.5, min_value=0.0)
        if st.form_submit_button("Salvar Produto"):
            cursor.execute("INSERT INTO produtos (nome, estoque, valor) VALUES (?, ?, ?)",
                           (nome_prod, estoque, valor_prod))
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

    cliente_venda = st.selectbox("Cliente", clientes, format_func=lambda x: x[1])
    st.markdown("### 🛒 Adicionar ao Carrinho")

    carrinho = st.session_state.get("carrinho", [])

    col1, col2 = st.columns(2)
    with col1:
        item_tipo = st.radio("Tipo", ["Produto", "Serviço"])
    with col2:
        if item_tipo == "Produto":
            itens = [f"{p[0]} - R$ {p[1]:.2f}" for p in produtos]
        else:
            itens = [f"{s[0]} - R$ {s[1]:.2f}" for s in servicos]
        item_selecionado = st.selectbox("Item", itens)

    qtd = st.number_input("Quantidade", min_value=1, step=1)
    if st.button("Adicionar ao Carrinho"):
        nome = item_selecionado.split(" - ")[0]
        preco = float(item_selecionado.split("R$ ")[-1])
        carrinho.append({"tipo": item_tipo, "nome": nome, "qtd": qtd, "preco": preco})
        st.session_state.carrinho = carrinho
        st.success(f"{item_tipo} adicionado!")

    if carrinho:
        st.markdown("### 🧾 Carrinho")
        total = 0
        for i, item in enumerate(carrinho):
            subtotal = item["qtd"] * item["preco"]
            total += subtotal
            st.write(f"{item['nome']} ({item['tipo']}) — {item['qtd']} x R$ {item['preco']:.2f} = R$ {subtotal:.2f}")
            if st.button("Remover", key=f"remover_{i}"):
                carrinho.pop(i)
                st.session_state.carrinho = carrinho
                st.experimental_rerun()

        st.markdown(f"### 💰 Total: R$ {total:.2f}")
        forma_pg = st.radio("Forma de Pagamento", ["Pix", "Dinheiro", "Crédito", "Débito"])
        if st.button("Finalizar Venda"):
            cursor.execute("INSERT INTO vendas (cliente_id, data, forma_pagamento, total) VALUES (?, ?, ?, ?)",
                           (cliente_venda[0], str(datetime.now()), forma_pg, total))
            venda_id = cursor.lastrowid
            for item in carrinho:
                cursor.execute("INSERT INTO vendas_itens (venda_id, tipo, nome, quantidade, preco) VALUES (?, ?, ?, ?, ?)",
                               (venda_id, item["tipo"], item["nome"], item["qtd"], item["preco"]))
                if item["tipo"] == "Produto":
                    cursor.execute("UPDATE produtos SET estoque = estoque - ? WHERE nome = ?",
                                   (item["qtd"], item["nome"]))
            conn.commit()
            st.success("Venda registrada com sucesso!")
            st.session_state.carrinho = []
    else:
        st.info("Carrinho vazio.")
elif menu == "Despesas":
    st.title("📉 Controle de Despesas")

    with st.form("form_despesa"):
        desc = st.text_input("Descrição da Despesa")
elif menu == "Relatórios":
    st.title("📊 Relatórios e Gráficos Financeiros")

    st.markdown("### 🔎 Filtro por Período")
    col1, col2 = st.columns(2)
    with col1:
        data_inicio = st.date_input("Data Inicial", value=date.today().replace(day=1))
    with col2:
        data_fim = st.date_input("Data Final", value=date.today())

    # Relatório de Vendas
    st.markdown("### 💵 Vendas no Período")
    vendas = cursor.execute("""
        SELECT data, forma_pagamento, total FROM vendas
        WHERE DATE(data) BETWEEN ? AND ?
    """, (str(data_inicio), str(data_fim))).fetchall()

    total_vendas = sum([v[2] for v in vendas])
    st.metric("Total em Vendas", f"R$ {total_vendas:.2f}")
    if vendas:
        df_vendas = pd.DataFrame(vendas, columns=["Data", "Pagamento", "Total"])
        df_vendas["Data"] = pd.to_datetime(df_vendas["Data"]).dt.date
        fig = px.bar(df_vendas, x="Data", y="Total", color="Pagamento", title="Faturamento por Dia")
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(df_vendas)
    else:
        st.info("Nenhuma venda registrada no período.")

    # Relatório de Despesas
    st.markdown("### 📉 Despesas no Período")
    despesas = cursor.execute("""
        SELECT descricao, valor, data FROM despesas
        WHERE DATE(data) BETWEEN ? AND ?
    """, (str(data_inicio), str(data_fim))).fetchall()

    total_despesas = sum([d[1] for d in despesas])
    st.metric("Total em Despesas", f"R$ {total_despesas:.2f}")
    if despesas:
        df_desp = pd.DataFrame(despesas, columns=["Descrição", "Valor", "Data"])
        df_desp["Data"] = pd.to_datetime(df_desp["Data"]).dt.date
        st.dataframe(df_desp)
    else:
        st.info("Nenhuma despesa registrada no período.")

    # Saldo
    st.markdown("### 💰 Saldo Final")
    saldo = total_vendas - total_despesas
    cor = "green" if saldo >= 0 else "red"
    st.markdown(f"<h2 style='color:{cor}'>R$ {saldo:.2f}</h2>", unsafe_allow_html=True)
# --- APLICAÇÃO DE TEMA CLÍNICO PERSONALIZADO ---
st.markdown("""
    <style>
    html, body, [class*="css"] {
        background-color: #f7f9fb;
        font-family: 'Segoe UI', sans-serif;
    }
    .css-1d391kg { padding-top: 2rem; }
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
        padding-left: 2rem;
        padding-right: 2rem;
    }
    .stSidebar {
        background-color: #e3edf4;
    }
    .stButton > button {
        background-color: #0099cc;
        color: white;
        border-radius: 5px;
        height: 2.5em;
        width: 100%;
        font-weight: bold;
    }
    .stButton > button:hover {
        background-color: #007399;
    }
    .stRadio > div {
        background-color: #ffffff;
        padding: 10px;
        border-radius: 8px;
    }
    </style>
""", unsafe_allow_html=True)
        
        valor = st.number_input("Valor (R$)", step=0.5, min_value=0.0)
        data_desp = st.date_input("Data da Despesa", value=date.today())
        if st.form_submit_button("Registrar Despesa"):
            cursor.execute("INSERT INTO despesas (descricao, valor, data) VALUES (?, ?, ?)",
                           (desc, valor, str(data_desp)))
            conn.commit()
            st.success("Despesa registrada com sucesso!")

    st.markdown("### 📋 Histórico de Despesas")
    despesas = cursor.execute("SELECT descricao, valor, data FROM despesas ORDER BY data DESC").fetchall()
    for d in despesas:
        st.write(f"🧾 {d[0]} — R$ {d[1]:.2f} em {d[2]}")
