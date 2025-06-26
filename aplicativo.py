import streamlit as st
import sqlite3
from datetime import datetime, date
from streamlit_drawable_canvas import st_canvas
import pandas as pd
import matplotlib.pyplot as plt
from PIL import Image
import io

# Banco de dados
conn = sqlite3.connect("studio_depilation.db", check_same_thread=False)
cursor = conn.cursor()

def criar_tabelas():
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario TEXT UNIQUE,
        senha TEXT
    )""")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS empresa (
        id INTEGER PRIMARY KEY,
        nome TEXT,
        cnpj TEXT,
        email TEXT,
        telefone TEXT
    )""")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS clientes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        telefone TEXT,
        email TEXT,
        assinatura BLOB
    )""")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS produtos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        quantidade INTEGER,
        preco_custo REAL,
        preco_venda REAL
    )""")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS servicos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        unidade TEXT,
        quantidade INTEGER,
        valor REAL
    )""")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS agendamentos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cliente_id INTEGER,
        data TEXT,
        servico_id INTEGER,
        FOREIGN KEY(cliente_id) REFERENCES clientes(id),
        FOREIGN KEY(servico_id) REFERENCES servicos(id)
    )""")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS vendas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cliente_id INTEGER,
        data TEXT,
        total REAL,
        cancelada INTEGER DEFAULT 0,
        FOREIGN KEY(cliente_id) REFERENCES clientes(id)
    )""")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS venda_itens (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        venda_id INTEGER,
        tipo TEXT,
        item_id INTEGER,
        quantidade INTEGER,
        preco REAL,
        FOREIGN KEY(venda_id) REFERENCES vendas(id)
    )""")
    conn.commit()

criar_tabelas()

def criar_admin():
    user = cursor.execute("SELECT * FROM usuarios WHERE usuario='admin'").fetchone()
    if not user:
        cursor.execute("INSERT INTO usuarios (usuario, senha) VALUES (?, ?)", ("admin", "admin"))
        conn.commit()

criar_admin()

def autenticar(usuario, senha):
    user = cursor.execute("SELECT * FROM usuarios WHERE usuario=? AND senha=?", (usuario, senha)).fetchone()
    return user is not None

if "login" not in st.session_state:
    st.session_state["login"] = False
if "usuario" not in st.session_state:
    st.session_state["usuario"] = ""

def tela_login():
    st.title("Login - Studio de Depilação")
    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if autenticar(usuario, senha):
            st.session_state["login"] = True
            st.session_state["usuario"] = usuario
            st.experimental_rerun()
        else:
            st.error("Usuário ou senha inválidos")

def menu_lateral():
    # Tente trocar o caminho do logo para um arquivo existente, ou comente se não tiver logo
    try:
        st.image("logo.png", width=150)
    except:
        st.write("Logo aqui")
    menu = st.sidebar.radio("Menu", [
        "Iniciar",
        "Dashboard",
        "Cadastro Empresa",
        "Cadastro Cliente",
        "Cadastro Produtos",
        "Cadastro Serviços",
        "Agendamento",
        "Vendas",
        "Cancelar Vendas",
        "Relatórios",
        "Sair"
    ])
    return menu

def pagina_iniciar():
    st.header(f"Bem-vindo {st.session_state['usuario']} ao Studio de Depilação!")
    st.write("Vamos iniciar mais um dia produtivo!")
    hoje = date.today().strftime("%Y-%m-%d")
    st.write(f"Data de hoje: {hoje}")
    agendados = cursor.execute("""
        SELECT clientes.nome, servicos.nome FROM agendamentos 
        JOIN clientes ON agendamentos.cliente_id = clientes.id
        JOIN servicos ON agendamentos.servico_id = servicos.id
        WHERE agendamentos.data = ?
        """, (hoje,)).fetchall()
    if agendados:
        st.subheader("Clientes agendados para hoje:")
        for cli, serv in agendados:
            st.write(f"- {cli} | Serviço: {serv}")
    else:
        st.write("Nenhum agendamento para hoje.")

def dashboard():
    st.title("Dashboard")
    total_clientes = cursor.execute("SELECT COUNT(*) FROM clientes").fetchone()[0]
    total_vendas = cursor.execute("SELECT COUNT(*) FROM vendas WHERE cancelada=0").fetchone()[0]
    total_canceladas = cursor.execute("SELECT COUNT(*) FROM vendas WHERE cancelada=1").fetchone()[0]
    total_estoque = cursor.execute("SELECT SUM(quantidade) FROM produtos").fetchone()[0]
    total_estoque = total_estoque if total_estoque else 0
    col1, col2 = st.columns(2)
    col1.metric("Clientes Cadastrados", total_clientes)
    col1.metric("Vendas Realizadas", total_vendas)
    col2.metric("Vendas Canceladas", total_canceladas)
    col2.metric("Estoque Total Produtos", total_estoque)

def cadastro_empresa():
    st.title("Cadastro da Empresa")
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
            st.success("Dados da empresa salvos com sucesso!")

def cadastro_cliente():
    st.title("Cadastro de Cliente")
    with st.form("form_cliente"):
        nome = st.text_input("Nome Completo")
        telefone = st.text_input("Telefone")
        email = st.text_input("Email")
        st.write("Assinatura (use mouse ou touch para desenhar):")
        canvas_result = st_canvas(
            fill_color="rgba(0, 0, 0, 0)", 
            stroke_width=2,
            stroke_color="#000000",
            background_color="#eee",
            height=150,
            width=400,
            drawing_mode="freedraw",
            key="canvas"
        )
        if st.form_submit_button("Salvar"):
            if not nome:
                st.error("Nome é obrigatório")
                return
            assinatura_bytes = None
            if canvas_result.image_data is not None:
                img = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
                buffer = io.BytesIO()
                img.save(buffer, format="PNG")
                assinatura_bytes = buffer.getvalue()
            cursor.execute("INSERT INTO clientes (nome, telefone, email, assinatura) VALUES (?, ?, ?, ?)",
                           (nome, telefone, email, assinatura_bytes))
            conn.commit()
            st.success("Cliente cadastrado com sucesso!")

def cadastro_produtos():
    st.title("Cadastro de Produtos")
    produtos = cursor.execute("SELECT * FROM produtos").fetchall()
    with st.form("form_produto"):
        nome = st.text_input("Nome do Produto")
        quantidade = st.number_input("Quantidade", min_value=0, step=1)
        preco_custo = st.number_input("Preço de Custo", min_value=0.0, step=0.01, format="%.2f")
        preco_venda = st.number_input("Preço de Venda", min_value=0.0, step=0.01, format="%.2f")
        if st.form_submit_button("Adicionar Produto"):
            if not nome:
                st.error("Nome do produto é obrigatório")
                return
            cursor.execute("INSERT INTO produtos (nome, quantidade, preco_custo, preco_venda) VALUES (?, ?, ?, ?)",
                           (nome, quantidade, preco_custo, preco_venda))
            conn.commit()
            st.success("Produto adicionado!")
    if produtos:
        st.subheader("Produtos Cadastrados")
        for prod in produtos:
            st.write(f"ID: {prod[0]} | Nome: {prod[1]} | Qtd: {prod[2]} | Custo: R${prod[3]:.2f} | Venda: R${prod[4]:.2f}")
            if st.button(f"Excluir Produto {prod[0]}"):
                cursor.execute("DELETE FROM produtos WHERE id=?", (prod[0],))
                conn.commit()
                st.experimental_rerun()
    else:
        st.info("Nenhum produto cadastrado.")

def cadastro_servicos():
    st.title("Cadastro de Serviços")
    servicos = cursor.execute("SELECT * FROM servicos").fetchall()
    with st.form("form_servico"):
        nome = st.text_input("Nome do Serviço")
        unidade = st.text_input("Unidade (ex: sessão)")
        quantidade = st.number_input("Quantidade em estoque", min_value=0, step=1)
        valor = st.number_input("Valor do Serviço", min_value=0.0, step=0.01, format="%.2f")
        if st.form_submit_button("Adicionar Serviço"):
            if not nome or not unidade:
                st.error("Nome e Unidade são obrigatórios")
                return
            cursor.execute("INSERT INTO servicos (nome, unidade, quantidade, valor) VALUES (?, ?, ?, ?)",
                           (nome, unidade, quantidade, valor))
            conn.commit()
            st.success("Serviço adicionado!")
    if servicos:
        st.subheader("Serviços Cadastrados")
        for serv in servicos:
            st.write(f"ID: {serv[0]} | Nome: {serv[1]} | Unidade: {serv[2]} | Qtd: {serv[3]} | Valor: R${serv[4]:.2f}")
            if st.button(f"Excluir Serviço {serv[0]}"):
                cursor.execute("DELETE FROM servicos WHERE id=?", (serv[0],))
                conn.commit()
                st.experimental_rerun()
    else:
        st.info("Nenhum serviço cadastrado.")

def agendamento():
    st.title("Agendamento")
    clientes = cursor.execute("SELECT id, nome FROM clientes").fetchall()
    servicos = cursor.execute("SELECT id, nome FROM servicos").fetchall()
    cliente_dict = {nome: id for (id, nome) in clientes}
    servico_dict = {nome: id for (id, nome) in servicos}
    cliente_selecionado = st.selectbox("Cliente", list(cliente_dict.keys()))
    data_agendamento = st.date_input("Data do Agendamento", date.today())
    servico_selecionado = st.selectbox("Serviço", list(servico_dict.keys()))
    if st.button("Agendar"):
        cliente_id = cliente_dict[cliente_selecionado]
        servico_id = servico_dict[servico_selecionado]
        data_str = data_agendamento.strftime("%Y-%m-%d")
        cursor.execute("INSERT INTO agendamentos (cliente_id, data, servico_id) VALUES (?, ?, ?)",
                       (cliente_id, data_str, servico_id))
        conn.commit()
        st.success("Agendamento realizado!")
    st.subheader("Agendamentos futuros")
    agend = cursor.execute("""
        SELECT agendamentos.id, clientes.nome, agendamentos.data, servicos.nome
        FROM agendamentos 
        JOIN clientes ON agendamentos.cliente_id = clientes.id
        JOIN servicos ON agendamentos.servico_id = servicos.id
        WHERE agendamentos.data >= ?
        ORDER BY agendamentos.data
        """, (date.today().strftime("%Y-%m-%d"),)).fetchall()
    for ag in agend:
        st.write(f"ID: {ag[0]} | Cliente: {ag[1]} | Data: {ag[2]} | Serviço: {ag[3]}")

def vendas():
    st.title("Vendas")
    clientes = cursor.execute("SELECT id, nome FROM clientes").fetchall()
    produtos = cursor.execute("SELECT id, nome, quantidade, preco_venda FROM produtos").fetchall()
    servicos = cursor.execute("SELECT id, nome, valor FROM servicos").fetchall()
    cliente_dict = {nome: id for (id, nome) in clientes}
    produto_dict = {nome: (id, qtd, preco) for (id, nome, qtd, preco) in produtos}
    servico_dict = {nome: (id, valor) for (id, nome, valor) in servicos}
    cliente_selecionado = st.selectbox("Cliente", list(cliente_dict.keys()))
    opcoes_venda = st.radio("Tipo de Venda", ["Produtos", "Serviços", "Ambos"])
    itens_venda = []
    total = 0.0
    if opcoes_venda in ["Produtos", "Ambos"]:
        st.subheader("Produtos")
        produtos_selecionados = st.multiselect("Selecione produtos", list(produto_dict.keys()))
        for p in produtos_selecionados:
            id_p, qtd_estoque, preco_venda = produto_dict[p]
            quantidade = st.number_input(f"Quantidade para {p} (estoque: {qtd_estoque})", min_value=1, max_value=qtd_estoque, key=f"prod_{id_p}")
            itens_venda.append(("produto", id_p, quantidade, preco_venda))
            total += preco_venda * quantidade
    if opcoes_venda in ["Serviços", "Ambos"]:
        st.subheader("Serviços")
        servicos_selecionados = st.multiselect("Selecione serviços", list(servico_dict.keys()))
        for s in servicos_selecionados:
            id_s, valor = servico_dict[s]
            quantidade = st.number_input(f"Quantidade para {s}", min_value=1, max_value=100, key=f"serv_{id_s}")
            itens_venda.append(("servico", id_s, quantidade, valor))
            total += valor * quantidade
    st.write(f"**Total da venda: R$ {total:.2f}**")
    if st.button("Finalizar Venda"):
        if total == 0:
            st.error("Selecione ao menos um produto ou serviço para vender.")
            return
        cliente_id = cliente_dict[cliente_selecionado]
        data_hoje = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("INSERT INTO vendas (cliente_id, data, total) VALUES (?, ?, ?)", (cliente_id, data_hoje, total))
        venda_id = cursor.lastrowid
        for tipo, item_id, qtd, preco in itens_venda:
            cursor.execute("INSERT INTO venda_itens (venda_id, tipo, item_id, quantidade, preco) VALUES (?, ?, ?, ?, ?)",
                           (venda_id, tipo, item_id, qtd, preco))
            if tipo == "produto":
                # Atualiza estoque
                cursor.execute("UPDATE produtos SET quantidade = quantidade - ? WHERE id=?", (qtd, item_id))
        conn.commit()
        st.success(f"Venda finalizada com sucesso! Total: R$ {total:.2f}")

def cancelar_vendas():
    st.title("Cancelar Vendas")
    data_inicio = st.date_input("Data Início", value=date.today())
    data_fim = st.date_input("Data Fim", value=date.today())
    vendas_cancel = cursor.execute("""
        SELECT vendas.id, clientes.nome, vendas.data, vendas.total, vendas.cancelada
        FROM vendas JOIN clientes ON vendas.cliente_id = clientes.id
        WHERE vendas.data BETWEEN ? AND ? AND vendas.cancelada=0
    """, (data_inicio.strftime("%Y-%m-%d 00:00:00"), data_fim.strftime("%Y-%m-%d 23:59:59"))).fetchall()
    if vendas_cancel:
        df = pd.DataFrame(vendas_cancel, columns=["ID", "Cliente", "Data", "Total", "Cancelada"])
        st.dataframe(df)
        venda_id = st.number_input("Informe o ID da venda para cancelar", min_value=1, step=1)
        if st.button("Cancelar Venda"):
            venda = cursor.execute("SELECT * FROM vendas WHERE id=? AND cancelada=0", (venda_id,)).fetchone()
            if not venda:
                st.error("Venda não encontrada ou já cancelada.")
                return
            # Atualiza estoque para produtos vendidos
            itens = cursor.execute("SELECT tipo, item_id, quantidade FROM venda_itens WHERE venda_id=?", (venda_id,)).fetchall()
            for tipo, item_id, qtd in itens:
                if tipo == "produto":
                    cursor.execute("UPDATE produtos SET quantidade = quantidade + ? WHERE id=?", (qtd, item_id))
            cursor.execute("UPDATE vendas SET cancelada=1 WHERE id=?", (venda_id,))
            conn.commit()
            st.success(f"Venda {venda_id} cancelada e estoque ajustado.")
    else:
        st.info("Nenhuma venda encontrada no período selecionado.")

def relatorios():
    st.title("Relatórios")
    data_inicio = st.date_input("Data Início", value=date.today())
    data_fim = st.date_input("Data Fim", value=date.today())
    vendas_rel = cursor.execute("""
        SELECT vendas.id, clientes.nome, vendas.data, vendas.total, vendas.cancelada
        FROM vendas JOIN clientes ON vendas.cliente_id = clientes.id
        WHERE vendas.data BETWEEN ? AND ?
        """, (data_inicio.strftime("%Y-%m-%d 00:00:00"), data_fim.strftime("%Y-%m-%d 23:59:59"))).fetchall()
    if vendas_rel:
        df = pd.DataFrame(vendas_rel, columns=["ID", "Cliente", "Data", "Total", "Cancelada"])
        st.dataframe(df)
        total_vendas = df[df["Cancelada"] == 0]["Total"].sum()
        total_canceladas = df[df["Cancelada"] == 1]["Total"].sum()
        fig, ax = plt.subplots()
        ax.bar(["Vendas Realizadas", "Vendas Canceladas"], [total_vendas, total_canceladas], color=["green", "red"])
        ax.set_ylabel("Valor (R$)")
        ax.set_title("Vendas no Período")
        st.pyplot(fig)
    else:
        st.info("Nenhuma venda no período selecionado.")

def main():
    st.set_page_config(page_title="Studio Depilação", layout="wide")
    if not st.session_state["login"]:
        tela_login()
    else:
        menu = menu_lateral()
        if menu == "Iniciar":
            pagina_iniciar()
        elif menu == "Dashboard":
            dashboard()
        elif menu == "Cadastro Empresa":
            cadastro_empresa()
        elif menu == "Cadastro Cliente":
            cadastro_cliente()
        elif menu == "Cadastro Produtos":
            cadastro_produtos()
        elif menu == "Cadastro Serviços":
            cadastro_servicos()
        elif menu == "Agendamento":
            agendamento()
        elif menu == "Vendas":
            vendas()
        elif menu == "Cancelar Vendas":
            cancelar_vendas()
        elif menu == "Relatórios":
            relatorios()
        elif menu == "Sair":
            st.session_state["login"] = False
            st.session_state["usuario"] = ""
            st.experimental_rerun()

if __name__ == "__main__":
    main()
