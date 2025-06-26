import streamlit as st
import sqlite3
from datetime import datetime, date
from streamlit_drawable_canvas import st_canvas
import pandas as pd
import matplotlib.pyplot as plt
from PIL import Image
import io

# CONFIG
st.set_page_config(page_title="Studio Depilação", layout="wide")

# DB CONNECTION
conn = sqlite3.connect("studio_depilation.db", check_same_thread=False)
cursor = conn.cursor()

# TABELAS
cursor.execute("""
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario TEXT UNIQUE,
    senha TEXT
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS empresa (
    id INTEGER PRIMARY KEY,
    nome TEXT,
    cnpj TEXT,
    email TEXT,
    telefone TEXT
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS clientes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT,
    telefone TEXT,
    nascimento TEXT,
    instagram TEXT,
    cantor TEXT,
    bebida TEXT,
    epilacao TEXT,
    alergia TEXT,
    qual_alergia TEXT,
    problemas_pele TEXT,
    tratamento TEXT,
    tipo_pele TEXT,
    hidrata TEXT,
    gravida TEXT,
    medicamento TEXT,
    qual_medicamento TEXT,
    uso TEXT,
    diabete TEXT,
    pelos_encravados TEXT,
    cirurgia TEXT,
    foliculite TEXT,
    qual_foliculite TEXT,
    problema_extra TEXT,
    qual_problema TEXT,
    autorizacao_imagem TEXT,
    assinatura BLOB
)
""")
conn.commit()

# CRIA USUÁRIO PADRÃO
if not cursor.execute("SELECT * FROM usuarios WHERE usuario='admin'").fetchone():
    cursor.execute("INSERT INTO usuarios (usuario, senha) VALUES ('admin', 'admin')")
    conn.commit()

# LOGIN
if "login" not in st.session_state:
    st.session_state.login = False

if not st.session_state.login:
    st.title("🔐 Login")
    u = st.text_input("Usuário")
    s = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if cursor.execute("SELECT * FROM usuarios WHERE usuario=? AND senha=?", (u, s)).fetchone():
            st.session_state.login = True
            st.experimental_rerun()
        else:
            st.error("Usuário ou senha inválidos")
else:
    col_logo, col_menu = st.columns([1, 5])
    with col_logo:
        st.image("https://via.placeholder.com/120x80.png?text=LOGO", width=120)
    with col_menu:
        menu = st.selectbox("Menu", [
            "Início", "Dashboard", "Cadastro Cliente", "Cadastro Empresa", "Cadastro Produtos",
            "Cadastro Serviços", "Agendamento", "Vendas", "Cancelar Vendas", "Relatórios", "Sair"
        ], key="menu_selector")

    if menu == "Início":
        st.success("Bem-vindo! Vamos iniciar mais um dia produtivo.")

    elif menu == "Dashboard":
        st.subheader("📊 Dashboard")
        total_clientes = cursor.execute("SELECT COUNT(*) FROM clientes").fetchone()[0]
        col1, col2 = st.columns(2)
        col1.metric("Clientes cadastrados", total_clientes)
        col2.metric("Sistema ativo", "Studio de Depilação")

    elif menu == "Cadastro Empresa":
        st.subheader("🏢 Cadastro da Empresa")
        empresa = cursor.execute("SELECT * FROM empresa WHERE id=1").fetchone()
        with st.form("form_empresa"):
            nome = st.text_input("Nome", value=empresa[1] if empresa else "")
            cnpj = st.text_input("CNPJ", value=empresa[2] if empresa else "")
            email = st.text_input("Email", value=empresa[3] if empresa else "")
            telefone = st.text_input("Telefone", value=empresa[4] if empresa else "")
            if st.form_submit_button("Salvar"):
                if empresa:
                    cursor.execute("UPDATE empresa SET nome=?, cnpj=?, email=?, telefone=? WHERE id=1",
                                   (nome, cnpj, email, telefone))
                else:
                    cursor.execute("INSERT INTO empresa (id, nome, cnpj, email, telefone) VALUES (1, ?, ?, ?, ?)",
                                   (nome, cnpj, email, telefone))
                conn.commit()
                st.success("Empresa cadastrada com sucesso!")

    elif menu == "Cadastro Cliente":
        st.subheader("🧍 Cadastro de Cliente + Ficha de Avaliação")
        with st.form("form_cliente"):
            nome = st.text_input("Nome completo")
            telefone = st.text_input("Telefone")
            nascimento = st.date_input("Data de nascimento")
            instagram = st.text_input("Instagram")
            cantor = st.text_input("Cantor favorito")
            bebida = st.text_input("Bebida favorita")
            epilacao = st.radio("Já fez epilação na cera?", ["SIM", "NÃO"])
            alergia = st.radio("Possui alergia?", ["SIM", "NÃO"])
            qual_alergia = st.text_input("Qual alergia?") if alergia == "SIM" else ""
            problemas_pele = st.radio("Problemas de pele?", ["SIM", "NÃO"])
            tratamento = st.radio("Tratamento dermatológico?", ["SIM", "NÃO"])
            tipo_pele = st.radio("Tipo de pele", ["SECA", "OLEOSA", "NORMAL"])
            hidrata = st.radio("Hidrata a pele?", ["SIM", "NÃO"])
            gravida = st.radio("Está grávida?", ["SIM", "NÃO"])
            medicamento = st.radio("Uso de medicamentos?", ["SIM", "NÃO"])
            qual_medicamento = st.text_input("Qual medicamento?") if medicamento == "SIM" else ""
            uso = st.radio("DIU ou marca-passo?", ["DIU", "Marca-passo", "Nenhum"])
            diabete = st.radio("Diabetes?", ["SIM", "NÃO"])
            pelos_encravados = st.radio("Pelos encravados?", ["SIM", "NÃO"])
            cirurgia = st.radio("Cirurgia recente?", ["SIM", "NÃO"])
            foliculite = st.radio("Foliculite?", ["SIM", "NÃO"])
            qual_foliculite = st.text_input("Qual foliculite?") if foliculite == "SIM" else ""
            problema_extra = st.radio("Outro problema?", ["SIM", "NÃO"])
            qual_problema = st.text_input("Qual problema?") if problema_extra == "SIM" else ""
            autorizacao_imagem = st.radio("Autoriza uso de imagem?", ["SIM", "NÃO"])
            st.write("Assinatura Digital")
            assinatura_canvas = st_canvas(fill_color="rgba(0,0,0,0)", stroke_width=2, stroke_color="#000",
                                          background_color="#eee", height=150, width=400, drawing_mode="freedraw")
            if st.form_submit_button("Salvar Cliente"):
                assinatura_bytes = None
                if assinatura_canvas.image_data is not None:
                    img = Image.fromarray(assinatura_canvas.image_data.astype("uint8"), mode="RGBA")
                    buf = io.BytesIO()
                    img.save(buf, format="PNG")
                    assinatura_bytes = buf.getvalue()
                cursor.execute("""
                INSERT INTO clientes (
                    nome, telefone, nascimento, instagram, cantor, bebida, epilacao, alergia,
                    qual_alergia, problemas_pele, tratamento, tipo_pele, hidrata, gravida,
                    medicamento, qual_medicamento, uso, diabete, pelos_encravados, cirurgia,
                    foliculite, qual_foliculite, problema_extra, qual_problema, autorizacao_imagem,
                    assinatura
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    nome, telefone, nascimento.strftime("%Y-%m-%d"), instagram, cantor, bebida, epilacao, alergia,
                    qual_alergia, problemas_pele, tratamento, tipo_pele, hidrata, gravida, medicamento,
                    qual_medicamento, uso, diabete, pelos_encravados, cirurgia, foliculite, qual_foliculite,
                    problema_extra, qual_problema, autorizacao_imagem, assinatura_bytes
                ))
                conn.commit()
                st.success("Cliente cadastrado com sucesso!")

    elif menu == "Sair":
        st.session_state.login = False
        st.experimental_rerun()
# Parte 2 - Continuação do sistema completo

    elif menu == "Cadastro Produtos":
        st.subheader("🌿 Cadastro de Produtos")
        with st.form("form_produto"):
            nome = st.text_input("Nome do Produto")
            quantidade = st.number_input("Quantidade", min_value=0, step=1)
            preco_custo = st.number_input("Preço de Custo", min_value=0.0, step=0.01, format="%.2f")
            preco_venda = st.number_input("Preço de Venda", min_value=0.0, step=0.01, format="%.2f")
            if st.form_submit_button("Salvar Produto"):
                cursor.execute("""
                    INSERT INTO produtos (nome, quantidade, preco_custo, preco_venda)
                    VALUES (?, ?, ?, ?)""", (nome, quantidade, preco_custo, preco_venda))
                conn.commit()
                st.success("Produto cadastrado com sucesso!")

        st.write("Produtos cadastrados:")
        produtos = cursor.execute("SELECT * FROM produtos").fetchall()
        for prod in produtos:
            st.write(f"{prod[0]} - {prod[1]} | Qtd: {prod[2]} | Venda: R${prod[4]:.2f}")

    elif menu == "Cadastro Serviços":
        st.subheader("🚗 Cadastro de Serviços")
        with st.form("form_servico"):
            nome = st.text_input("Nome do Serviço")
            unidade = st.text_input("Unidade")
            quantidade = st.number_input("Quantidade", min_value=0, step=1)
            valor = st.number_input("Valor", min_value=0.0, step=0.01, format="%.2f")
            if st.form_submit_button("Salvar Serviço"):
                cursor.execute("""
                    INSERT INTO servicos (nome, unidade, quantidade, valor)
                    VALUES (?, ?, ?, ?)""", (nome, unidade, quantidade, valor))
                conn.commit()
                st.success("Serviço cadastrado com sucesso!")

        st.write("Serviços cadastrados:")
        servicos = cursor.execute("SELECT * FROM servicos").fetchall()
        for serv in servicos:
            st.write(f"{serv[0]} - {serv[1]} | Qtd: {serv[3]} | Valor: R${serv[4]:.2f}")

    elif menu == "Agendamento":
        st.subheader("🗓️ Agendamento")
        clientes = cursor.execute("SELECT id, nome FROM clientes").fetchall()
        servicos = cursor.execute("SELECT id, nome FROM servicos").fetchall()
        cliente_dict = {nome: id for id, nome in clientes}
        servico_dict = {nome: id for id, nome in servicos}
        cliente_sel = st.selectbox("Cliente", list(cliente_dict.keys()))
        data_agendamento = st.date_input("Data")
        servico_sel = st.selectbox("Serviço", list(servico_dict.keys()))
        if st.button("Agendar"):
            cursor.execute("INSERT INTO agendamentos (cliente_id, data, servico_id) VALUES (?, ?, ?)",
                           (cliente_dict[cliente_sel], data_agendamento.strftime("%Y-%m-%d"), servico_dict[servico_sel]))
            conn.commit()
            st.success("Agendamento realizado com sucesso!")

    elif menu == "Vendas":
        st.subheader("🛒 Painel de Vendas")
        st.write("**Funcionalidade de vendas em desenvolvimento final.**")

    elif menu == "Cancelar Vendas":
        st.subheader("❌ Cancelar Vendas")
        st.write("**Funcionalidade de cancelamento em desenvolvimento final.**")

    elif menu == "Relatórios":
        st.subheader("📊 Relatórios")
        st.write("**Relatórios de vendas, produtos e serviços serão exibidos aqui.**")

    elif menu == "Vendas":
        st.subheader("🛒 Vendas")
        clientes = cursor.execute("SELECT id, nome FROM clientes").fetchall()
        produtos = cursor.execute("SELECT id, nome, quantidade, preco_venda FROM produtos").fetchall()
        servicos = cursor.execute("SELECT id, nome, valor FROM servicos").fetchall()
        cliente_dict = {nome: id for id, nome in clientes}
        produto_dict = {nome: (id, qtd, preco) for id, nome, qtd, preco in produtos}
        servico_dict = {nome: (id, valor) for id, nome, valor in servicos}

        cliente_sel = st.selectbox("Cliente", list(cliente_dict.keys()))
        tipo_venda = st.radio("Tipo de Venda", ["Produtos", "Serviços", "Ambos"])

        itens_venda = []
        total = 0.0

        if tipo_venda in ["Produtos", "Ambos"]:
            st.markdown("### Produtos")
            for nome in st.multiselect("Selecionar produtos", list(produto_dict.keys())):
                id_p, estoque, preco = produto_dict[nome]
                qtd = st.number_input(f"Qtd para {nome} (Estoque: {estoque})", min_value=1, max_value=estoque, key=f"prod_{id_p}")
                itens_venda.append(("produto", id_p, qtd, preco))
                total += preco * qtd

        if tipo_venda in ["Serviços", "Ambos"]:
            st.markdown("### Serviços")
            for nome in st.multiselect("Selecionar serviços", list(servico_dict.keys())):
                id_s, valor = servico_dict[nome]
                qtd = st.number_input(f"Qtd para {nome}", min_value=1, max_value=10, key=f"serv_{id_s}")
                itens_venda.append(("servico", id_s, qtd, valor))
                total += valor * qtd

        st.info(f"**Total: R$ {total:.2f}**")

        if st.button("Finalizar Venda"):
            if not itens_venda:
                st.warning("Nenhum item selecionado.")
            else:
                cliente_id = cliente_dict[cliente_sel]
                data_venda = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                cursor.execute("INSERT INTO vendas (cliente_id, data, total) VALUES (?, ?, ?)", (cliente_id, data_venda, total))
                venda_id = cursor.lastrowid
                for tipo, item_id, qtd, preco in itens_venda:
                    cursor.execute("INSERT INTO venda_itens (venda_id, tipo, item_id, quantidade, preco) VALUES (?, ?, ?, ?, ?)",
                                   (venda_id, tipo, item_id, qtd, preco))
                    if tipo == "produto":
                        cursor.execute("UPDATE produtos SET quantidade = quantidade - ? WHERE id = ?", (qtd, item_id))
                conn.commit()
                st.success("Venda registrada com sucesso!")

    elif menu == "Cancelar Vendas":
        st.subheader("❌ Cancelar Vendas")
        vendas = cursor.execute("SELECT id, data, total FROM vendas WHERE cancelada = 0 ORDER BY data DESC").fetchall()
        for v in vendas:
            st.write(f"ID: {v[0]} | Data: {v[1]} | Total: R$ {v[2]:.2f}")
        id_cancelar = st.number_input("ID da venda para cancelar", min_value=1, step=1)
        if st.button("Cancelar"):
            venda = cursor.execute("SELECT * FROM vendas WHERE id=? AND cancelada=0", (id_cancelar,)).fetchone()
            if not venda:
                st.error("Venda inválida ou já cancelada")
            else:
                itens = cursor.execute("SELECT tipo, item_id, quantidade FROM venda_itens WHERE venda_id=?", (id_cancelar,)).fetchall()
                for tipo, item_id, qtd in itens:
                    if tipo == "produto":
                        cursor.execute("UPDATE produtos SET quantidade = quantidade + ? WHERE id=?", (qtd, item_id))
                cursor.execute("UPDATE vendas SET cancelada=1 WHERE id=?", (id_cancelar,))
                conn.commit()
                st.success(f"Venda {id_cancelar} cancelada com sucesso.")

    elif menu == "Relatórios":
        st.subheader("📄 Relatórios de Vendas")
        data_ini = st.date_input("Data Inicial", value=date.today())
        data_fim = st.date_input("Data Final", value=date.today())
        vendas = cursor.execute("""
            SELECT v.id, c.nome, v.data, v.total, v.cancelada
            FROM vendas v
            JOIN clientes c ON v.cliente_id = c.id
            WHERE date(v.data) BETWEEN ? AND ?
            ORDER BY v.data DESC
        """, (data_ini.strftime("%Y-%m-%d"), data_fim.strftime("%Y-%m-%d"))).fetchall()

        if vendas:
            df = pd.DataFrame(vendas, columns=["ID", "Cliente", "Data", "Total", "Cancelada"])
            st.dataframe(df)
            total_realizadas = df[df["Cancelada"] == 0]["Total"].sum()
            total_canceladas = df[df["Cancelada"] == 1]["Total"].sum()
            st.metric("Vendas Realizadas", f"R$ {total_realizadas:.2f}")
            st.metric("Vendas Canceladas", f"R$ {total_canceladas:.2f}")
            fig, ax = plt.subplots()
            ax.bar(["Realizadas", "Canceladas"], [total_realizadas, total_canceladas], color=["green", "red"])
            st.pyplot(fig)
        else:
            st.info("Nenhuma venda no período selecionado.")

    
