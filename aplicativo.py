import streamlit as st
import sqlite3
from datetime import datetime, date
from streamlit_drawable_canvas import st_canvas
import pandas as pd
import matplotlib.pyplot as plt
from PIL import Image
import io
import base64
import os

# CONFIGURAÇÃO INICIAL
df_mes = pd.date_range(start=date.today().replace(day=1), periods=31, freq='D')
df_mes = [d for d in df_mes if d.month == date.today().month]

st.set_page_config(page_title="Studio Depilação", layout="wide")

# CONEXÃO COM BANCO
conn = sqlite3.connect("studio_depilation.db", check_same_thread=False)
cursor = conn.cursor()

# FUNÇÃO DE FORMATAÇÃO
def formatar_data_br(data_iso):
    try:
        return datetime.strptime(data_iso, "%Y-%m-%d").strftime("%d/%m/%Y")
    except:
        return data_iso

# BACKUP DO BANCO
def fazer_backup():
    with open("studio_depilation.db", "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
        href = f'<a href="data:file/db;base64,{b64}" download="backup_studio_depilation.db">📥 Baixar Backup</a>'
        st.markdown(href, unsafe_allow_html=True)

# CRIAÇÃO DAS TABELAS
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
    hora_agendada TEXT,
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
cursor.execute("""
CREATE TABLE IF NOT EXISTS produtos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT,
    quantidade INTEGER,
    preco_venda REAL
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS servicos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT,
    unidade TEXT,
    quantidade INTEGER,
    valor REAL
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS agendamentos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente_id INTEGER,
    data TEXT,
    hora TEXT,
    servicos TEXT,
    status TEXT
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS vendas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente_id INTEGER,
    data TEXT,
    total REAL,
    cancelada INTEGER DEFAULT 0
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS venda_itens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    venda_id INTEGER,
    tipo TEXT,
    item_id INTEGER,
    quantidade INTEGER,
    preco REAL
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS despesas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data TEXT,
    descricao TEXT,
    valor REAL
)
""")
conn.commit()

# INSERE USUÁRIO PADRÃO
if not cursor.execute("SELECT * FROM usuarios WHERE usuario='admin'").fetchone():
    cursor.execute("INSERT INTO usuarios (usuario, senha) VALUES ('admin', 'admin')")
    conn.commit()

# LOGIN
if "login" not in st.session_state:
    st.session_state.login = False

if not st.session_state.login:
    st.title("🔐 Login")
    usuario_input = st.text_input("Usuário")
    senha_input = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if cursor.execute("SELECT * FROM usuarios WHERE usuario=? AND senha=?", (usuario_input, senha_input)).fetchone():
            st.session_state.login = True
            st.rerun()
        else:
            st.error("Usuário ou senha inválidos")
else:
    with st.sidebar:
        if "logo_img" in st.session_state:
            st.image(st.session_state["logo_img"], width=150)
        elif os.path.exists("logo_studio.png"):
            with open("logo_studio.png", "rb") as f:
                st.session_state["logo_img"] = f.read()
            st.image(st.session_state["logo_img"], width=150)
        else:
            st.image("https://via.placeholder.com/150x100.png?text=LOGO", width=150)

        st.write("📎 **Importar nova logo:**")
        uploaded_logo = st.file_uploader("Importar Logo", type=["png", "jpg", "jpeg"])
        if uploaded_logo:
            bytes_logo = uploaded_logo.read()
            with open("logo_studio.png", "wb") as f:
                f.write(bytes_logo)
            st.session_state["logo_img"] = bytes_logo
            st.success("Logo atualizada!")

        menu_opcoes = [
            "Início", "Dashboard", "Cadastro Cliente", "Cadastro Empresa", "Cadastro Produtos",
            "Cadastro Serviços", "Agendamento", "Vendas", "Cancelar Vendas", "Despesas", "Relatórios", "Backup", "Sair"
        ]

        icones_menu = {
            "Início": "🏠",
            "Dashboard": "📊",
            "Cadastro Cliente": "🧍",
            "Cadastro Empresa": "🏢",
            "Cadastro Produtos": "📦",
            "Cadastro Serviços": "💆",
            "Agendamento": "📅",
            "Vendas": "💰",
            "Cancelar Vendas": "🚫",
            "Despesas": "💸",
            "Relatórios": "📈",
            "Backup": "💾",
            "Sair": "🔓"
        }

        for opcao in menu_opcoes:
            icone = icones_menu.get(opcao, "📌")
            if st.button(f"{icone} {opcao}"):
                st.session_state["menu"] = opcao

    menu = st.session_state.get("menu", "Início")
    st.title(f"🧭 {menu}")

    # --- MENU INÍCIO ---
    if menu == "Início":
        st.subheader("👋 Seja bem-vindo(a)!")
        hoje = date.today().strftime("%d/%m/%Y")
        st.markdown(f"### Agendamentos para o dia: **{hoje}**")

        data_inicio = st.date_input("Filtrar de", date.today(), format="DD/MM/YYYY")
        data_fim = st.date_input("até", date.today(), format="DD/MM/YYYY")

        if data_inicio > data_fim:
            st.error("Data inicial não pode ser maior que a data final.")
        else:
            data_inicio_iso = data_inicio.strftime("%Y-%m-%d")
            data_fim_iso = data_fim.strftime("%Y-%m-%d")
            agendamentos = cursor.execute("""
                SELECT a.id, c.nome, a.data, a.hora, a.servicos, a.status
                FROM agendamentos a
                JOIN clientes c ON a.cliente_id = c.id
                WHERE a.data BETWEEN ? AND ?
                ORDER BY a.data, a.hora
            """, (data_inicio_iso, data_fim_iso)).fetchall()

            if agendamentos:
                for ag in agendamentos:
                    st.info(f"📅 {formatar_data_br(ag[2])} 🕒 {ag[3]} | 👤 {ag[1]} | 💼 Serviços: {ag[4]} | 📌 Status: {ag[5]}")
            else:
                st.warning("Nenhum agendamento no período.")

    # --- MENU DASHBOARD ---
    elif menu == "Dashboard":
        st.subheader("📊 Visão Geral")
        total_clientes = cursor.execute("SELECT COUNT(*) FROM clientes").fetchone()[0]
        total_vendas = cursor.execute("SELECT COUNT(*) FROM vendas WHERE cancelada=0").fetchone()[0]
        total_produtos = cursor.execute("SELECT COUNT(*) FROM produtos").fetchone()[0]
        total_servicos = cursor.execute("SELECT COUNT(*) FROM servicos").fetchone()[0]
        total_despesas = cursor.execute("SELECT SUM(valor) FROM despesas").fetchone()[0] or 0
        total_faturamento = cursor.execute("SELECT SUM(total) FROM vendas WHERE cancelada=0").fetchone()[0] or 0
        lucro_liquido = total_faturamento - total_despesas

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("👥 Clientes", total_clientes)
        col2.metric("🧾 Vendas", total_vendas)
        col3.metric("📦 Produtos", total_produtos)
        col4.metric("💆 Serviços", total_servicos)

        st.metric("💰 Faturamento Total", f"R$ {total_faturamento:.2f}")
        st.metric("💸 Despesas", f"R$ {total_despesas:.2f}")
        st.metric("📈 Lucro Líquido", f"R$ {lucro_liquido:.2f}")

        vendas_data = cursor.execute("""
            SELECT cancelada, COUNT(*)
            FROM vendas
            GROUP BY cancelada
        """).fetchall()

        canceladas = sum([q for c, q in vendas_data if c == 1])
        realizadas = sum([q for c, q in vendas_data if c == 0])

        fig, ax = plt.subplots()
        ax.bar(["Realizadas", "Canceladas"], [realizadas, canceladas], color=["green", "red"])
        ax.set_ylabel("Quantidade")
        ax.set_title("Resumo de Vendas")
        st.pyplot(fig)

    # --- MENU DESPESAS ---
    elif menu == "Despesas":
        st.subheader("📉 Registro de Despesas")
        with st.form("form_despesa", clear_on_submit=True):
            data_desp = st.date_input("Data da Despesa", date.today(), format="DD/MM/YYYY")
            descricao = st.text_input("Descrição")
            valor = st.number_input("Valor (R$)", min_value=0.0, format="%.2f")
            if st.form_submit_button("Salvar Despesa"):
                cursor.execute("INSERT INTO despesas (data, descricao, valor) VALUES (?, ?, ?)",
                               (data_desp.strftime("%Y-%m-%d"), descricao, valor))
                conn.commit()
                st.success("Despesa registrada!")

        despesas = cursor.execute("SELECT data, descricao, valor FROM despesas ORDER BY data DESC").fetchall()
        if despesas:
            df_despesas = pd.DataFrame(despesas, columns=["Data", "Descrição", "Valor"])
            df_despesas["Data"] = df_despesas["Data"].apply(formatar_data_br)
            st.dataframe(df_despesas)
        else:
            st.info("Nenhuma despesa registrada.")

    # --- MENU CADASTRO CLIENTE ---
    elif menu == "Cadastro Cliente":
        st.subheader("🧍 Cadastro e Gerenciamento de Clientes")
        clientes = cursor.execute("SELECT id, nome FROM clientes ORDER BY nome").fetchall()
        clientes_dict = {c[1]: c[0] for c in clientes}

        col1, col2 = st.columns([2, 3])

        with col1:
            with st.form("form_cliente", clear_on_submit=True):
                nome = st.text_input("Nome completo")
                telefone = st.text_input("Telefone")
                nascimento_str = st.text_input("Data de nascimento (DD/MM/AAAA)", placeholder="31/12/1980")
                hora_agendada = st.text_input("Hora agendada (ex: 14:30)")
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
                assinatura_canvas = st_canvas(
                    fill_color="rgba(0,0,0,0)",
                    stroke_width=2,
                    stroke_color="#000",
                    background_color="#eee",
                    height=150,
                    width=400,
                    drawing_mode="freedraw"
                )

                if st.form_submit_button("Salvar Cliente"):
                    try:
                        nascimento = datetime.strptime(nascimento_str, "%d/%m/%Y").date()
                    except Exception:
                        st.error("Data de nascimento inválida. Use o formato DD/MM/AAAA.")
                        st.stop()

                    assinatura = None
                    if assinatura_canvas.image_data is not None:
                        img = Image.fromarray(assinatura_canvas.image_data.astype('uint8'), 'RGBA')
                        buffer = io.BytesIO()
                        img.save(buffer, format="PNG")
                        assinatura = buffer.getvalue()

                    cursor.execute("""
                        INSERT INTO clientes (
                            nome, telefone, nascimento, hora_agendada, instagram, cantor, bebida,
                            epilacao, alergia, qual_alergia, problemas_pele, tratamento,
                            tipo_pele, hidrata, gravida, medicamento, qual_medicamento, uso,
                            diabete, pelos_encravados, cirurgia, foliculite, qual_foliculite,
                            problema_extra, qual_problema, autorizacao_imagem, assinatura
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        nome, telefone, nascimento.strftime("%Y-%m-%d"), hora_agendada, instagram, cantor, bebida,
                        epilacao, alergia, qual_alergia, problemas_pele, tratamento,
                        tipo_pele, hidrata, gravida, medicamento, qual_medicamento, uso,
                        diabete, pelos_encravados, cirurgia, foliculite, qual_foliculite,
                        problema_extra, qual_problema, autorizacao_imagem, assinatura
                    ))
                    conn.commit()
                    st.success("Cliente cadastrado!")

        with col2:
            st.write("### Clientes Cadastrados")
            df_clientes = pd.DataFrame(clientes, columns=["ID", "Nome"])
            st.dataframe(df_clientes[["Nome"]], use_container_width=True)

            cliente_selecionado = st.selectbox("Selecionar cliente para visualizar ou excluir", [""] + list(clientes_dict.keys()))
            if cliente_selecionado:
                cliente_id = clientes_dict[cliente_selecionado]
                dados_cliente = cursor.execute("SELECT * FROM clientes WHERE id=?", (cliente_id,)).fetchone()
                st.write(f"Nome: {dados_cliente[1]}")
                st.write(f"Telefone: {dados_cliente[2]}")
                st.write(f"Nascimento: {formatar_data_br(dados_cliente[3])}")
                st.write(f"Hora Agendada: {dados_cliente[4]}")
                st.write(f"Instagram: {dados_cliente[5]}")
                st.write(f"Cantor favorito: {dados_cliente[6]}")
                st.write(f"Bebida favorita: {dados_cliente[7]}")
                st.write(f"Já fez epilação na cera? {dados_cliente[8]}")
                st.write(f"Possui alergia? {dados_cliente[9]}")
                if dados_cliente[9] == "SIM":
                    st.write(f"Qual alergia? {dados_cliente[10]}")
                st.write(f"Problemas de pele? {dados_cliente[11]}")
                st.write(f"Tratamento dermatológico? {dados_cliente[12]}")
                st.write(f"Tipo de pele: {dados_cliente[13]}")
                st.write(f"Hidrata a pele? {dados_cliente[14]}")
                st.write(f"Está grávida? {dados_cliente[15]}")
                st.write(f"Uso de medicamentos? {dados_cliente[16]}")
                if dados_cliente[16] == "SIM":
                    st.write(f"Qual medicamento? {dados_cliente[17]}")
                st.write(f"DIU ou marca-passo? {dados_cliente[18]}")
                st.write(f"Diabetes? {dados_cliente[19]}")
                st.write(f"Pelos encravados? {dados_cliente[20]}")
                st.write(f"Cirurgia recente? {dados_cliente[21]}")
                st.write(f"Foliculite? {dados_cliente[22]}")
                if dados_cliente[22] == "SIM":
                    st.write(f"Qual foliculite? {dados_cliente[23]}")
                st.write(f"Outro problema? {dados_cliente[24]}")
                if dados_cliente[24] == "SIM":
                    st.write(f"Qual problema? {dados_cliente[25]}")
                st.write(f"Autoriza uso de imagem? {dados_cliente[26]}")
                if dados_cliente[27]:
                    st.image(dados_cliente[27], caption="Assinatura digital", use_column_width=True)

                if st.button("Excluir Cliente"):
                    cursor.execute("DELETE FROM clientes WHERE id=?", (cliente_id,))
                    conn.commit()
                    st.success("Cliente excluído!")
                    st.rerun()

    # --- MENU CADASTRO PRODUTOS ---
    elif menu == "Cadastro Produtos":
        st.subheader("📦 Cadastro e Gerenciamento de Produtos")
        produtos = cursor.execute("SELECT id, nome, quantidade, preco_venda FROM produtos ORDER BY nome").fetchall()
        produtos_dict = {p[1]: p[0] for p in produtos}

        col1, col2 = st.columns([2,3])

        with col1:
            with st.form("form_produto", clear_on_submit=True):
                nome = st.text_input("Nome do produto")
                quantidade = st.number_input("Quantidade em estoque", min_value=0, step=1)
                preco_venda = st.number_input("Preço de venda (R$)", min_value=0.0, format="%.2f")
                if st.form_submit_button("Salvar Produto"):
                    cursor.execute("""
                        INSERT INTO produtos (nome, quantidade, preco_venda)
                        VALUES (?, ?, ?)
                    """, (nome, quantidade, preco_venda))
                    conn.commit()
                    st.success("Produto cadastrado!")

        with col2:
            st.write("### Produtos Cadastrados")
            df_produtos = pd.DataFrame(produtos, columns=["ID", "Nome", "Quantidade", "Preço"])
            st.dataframe(df_produtos[["Nome", "Quantidade", "Preço"]], use_container_width=True)

            produto_selecionado = st.selectbox("Selecionar produto para editar ou excluir", [""] + list(produtos_dict.keys()))

            if produto_selecionado:
                produto_id = produtos_dict[produto_selecionado]
                dados_produto = cursor.execute("SELECT nome, quantidade, preco_venda FROM produtos WHERE id=?", (produto_id,)).fetchone()

                novo_nome = st.text_input("Nome", value=dados_produto[0])
                nova_quantidade = st.number_input("Quantidade", min_value=0, step=1, value=dados_produto[1])
                novo_preco = st.number_input("Preço de venda (R$)", min_value=0.0, format="%.2f", value=dados_produto[2])

                if st.button("Atualizar Produto"):
                    cursor.execute("""
                        UPDATE produtos SET nome=?, quantidade=?, preco_venda=?
                        WHERE id=?
                    """, (novo_nome, nova_quantidade, novo_preco, produto_id))
                    conn.commit()
                    st.success("Produto atualizado!")
                    st.rerun()

                if st.button("Excluir Produto"):
                    cursor.execute("DELETE FROM produtos WHERE id=?", (produto_id,))
                    conn.commit()
                    st.success("Produto excluído!")
                    st.rerun()

    # --- MENU CADASTRO SERVIÇOS ---
    elif menu == "Cadastro Serviços":
        st.subheader("💆 Cadastro e Gerenciamento de Serviços")
        servicos = cursor.execute("SELECT id, nome, unidade, quantidade, valor FROM servicos ORDER BY nome").fetchall()
        servicos_dict = {s[1]: s[0] for s in servicos}

        col1, col2 = st.columns([2,3])

        with col1:
            with st.form("form_servico", clear_on_submit=True):
                nome = st.text_input("Nome do serviço")
                unidade = st.text_input("Unidade (ex: sessão)")
                quantidade = st.number_input("Quantidade disponível", min_value=0, step=1)
                valor = st.number_input("Valor do serviço (R$)", min_value=0.0, format="%.2f")
                if st.form_submit_button("Salvar Serviço"):
                    cursor.execute("""
                        INSERT INTO servicos (nome, unidade, quantidade, valor)
                        VALUES (?, ?, ?, ?)
                    """, (nome, unidade, quantidade, valor))
                    conn.commit()
                    st.success("Serviço cadastrado!")

        with col2:
            st.write("### Serviços Cadastrados")
            df_servicos = pd.DataFrame(servicos, columns=["ID", "Nome", "Unidade", "Quantidade", "Valor"])
            st.dataframe(df_servicos[["Nome", "Unidade", "Quantidade", "Valor"]], use_container_width=True)

            servico_selecionado = st.selectbox("Selecionar serviço para editar ou excluir", [""] + list(servicos_dict.keys()))

            if servico_selecionado:
                servico_id = servicos_dict[servico_selecionado]
                dados_servico = cursor.execute("SELECT nome, unidade, quantidade, valor FROM servicos WHERE id=?", (servico_id,)).fetchone()

                novo_nome = st.text_input("Nome", value=dados_servico[0])
                nova_unidade = st.text_input("Unidade", value=dados_servico[1])
                nova_quantidade = st.number_input("Quantidade", min_value=0, step=1, value=dados_servico[2])
                novo_valor = st.number_input("Valor (R$)", min_value=0.0, format="%.2f", value=dados_servico[3])

                if st.button("Atualizar Serviço"):
                    cursor.execute("""
                        UPDATE servicos SET nome=?, unidade=?, quantidade=?, valor=?
                        WHERE id=?
                    """, (novo_nome, nova_unidade, nova_quantidade, novo_valor, servico_id))
                    conn.commit()
                    st.success("Serviço atualizado!")
                    st.rerun()

                if st.button("Excluir Serviço"):
                    cursor.execute("DELETE FROM servicos WHERE id=?", (servico_id,))
                    conn.commit()
                    st.success("Serviço excluído!")
                    st.rerun()

    # --- MENU AGENDAMENTO ---
    elif menu == "Agendamento":
        st.subheader("📅 Agendamento")
        clientes = cursor.execute("SELECT id, nome FROM clientes ORDER BY nome").fetchall()
        clientes_dict = {c[1]: c[0] for c in clientes}
    
        # Inicializa estados se não existir
        if "reagendar_id" not in st.session_state:
            st.session_state["reagendar_id"] = None
        if "cancelar_id" not in st.session_state:
            st.session_state["cancelar_id"] = None
    
        # Modo reagendar
        if st.session_state["reagendar_id"]:
            agendamento_id = st.session_state["reagendar_id"]
    
            ag = cursor.execute("""
                SELECT a.id, c.nome, a.data, a.hora, a.servicos
                FROM agendamentos a
                JOIN clientes c ON a.cliente_id = c.id
                WHERE a.id=?
            """, (agendamento_id,)).fetchone()
    
            st.subheader("🔄 Reagendar Agendamento")
            st.write(f"Cliente: {ag[1]}")
            st.write(f"Serviços: {ag[4]}")
    
            # Permite escolher nova data e hora
            nova_data = st.date_input("Nova data", datetime.strptime(ag[2], "%Y-%m-%d").date())
            nova_hora = st.text_input("Nova hora", ag[3])
    
            if st.button("Confirmar Reagendamento"):
                cursor.execute("""
                    UPDATE agendamentos SET data=?, hora=?, status='Reagendado'
                    WHERE id=?
                """, (nova_data.strftime("%Y-%m-%d"), nova_hora, agendamento_id))
                conn.commit()
                st.success("Agendamento reagendado com sucesso!")
                st.session_state["reagendar_id"] = None
                st.rerun()
    
            if st.button("Cancelar"):
                st.session_state["reagendar_id"] = None
                st.rerun()
    
            st.stop()
    
        # Modo cancelar
        if st.session_state["cancelar_id"]:
            cancelar_id = st.session_state["cancelar_id"]
    
            ag = cursor.execute("""
                SELECT a.id, c.nome, a.data, a.hora, a.servicos
                FROM agendamentos a
                JOIN clientes c ON a.cliente_id = c.id
                WHERE a.id=?
            """, (cancelar_id,)).fetchone()
    
            st.subheader("❌ Cancelar Agendamento")
            st.write(f"Cliente: {ag[1]}")
            st.write(f"Data: {formatar_data_br(ag[2])}")
            st.write(f"Hora: {ag[3]}")
            st.write(f"Serviços: {ag[4]}")
    
            if st.button("Confirmar Cancelamento"):
                cursor.execute("""
                    UPDATE agendamentos SET status='Cancelado'
                    WHERE id=?
                """, (cancelar_id,))
                conn.commit()
                st.success("Agendamento cancelado com sucesso!")
                st.session_state["cancelar_id"] = None
                st.rerun()
    
            if st.button("Voltar"):
                st.session_state["cancelar_id"] = None
                st.rerun()
    
            st.stop()
    
        # Interface principal do Agendamento
        cliente_selecionado = st.selectbox("Selecione o Cliente", [""] + list(clientes_dict.keys()))
        data_agendamento = st.date_input("Data do Agendamento", date.today())
        hora_agendamento = st.text_input("Hora (ex: 14:30)")
        servicos = cursor.execute("SELECT id, nome FROM servicos").fetchall()
        servicos_dict = {s[1]: s[0] for s in servicos}
        servicos_selecionados = st.multiselect("Selecione os Serviços", list(servicos_dict.keys()))
    
        if st.button("Salvar Agendamento"):
            if cliente_selecionado == "":
                st.error("Selecione um cliente.")
            elif not hora_agendamento:
                st.error("Informe a hora do agendamento.")
            elif not servicos_selecionados:
                st.error("Selecione ao menos um serviço.")
            else:
                id_cliente = clientes_dict[cliente_selecionado]
                data_str = data_agendamento.strftime("%Y-%m-%d")
                servicos_str = ", ".join(servicos_selecionados)
                cursor.execute("""
                    INSERT INTO agendamentos (cliente_id, data, hora, servicos, status)
                    VALUES (?, ?, ?, ?, 'Agendado')
                """, (id_cliente, data_str, hora_agendamento, servicos_str))
                conn.commit()
                st.success("Agendamento salvo!")
    
        st.markdown("---")
        st.subheader("📋 Lista de Agendamentos")
        data_filtro = st.date_input("Filtrar agendamentos a partir de", date.today())
        data_filtro_str = data_filtro.strftime("%Y-%m-%d")
    
        agendamentos = cursor.execute("""
            SELECT a.id, c.nome, a.data, a.hora, a.servicos, a.status
            FROM agendamentos a
            JOIN clientes c ON a.cliente_id = c.id
            WHERE a.data >= ?
            ORDER BY a.data, a.hora
        """, (data_filtro_str,)).fetchall()
    
        if agendamentos:
            for ag in agendamentos:
                col1, col2, col3, col4, col5, col6 = st.columns([2,3,2,2,3,3])
                with col1:
                    st.write(formatar_data_br(ag[2]))
                with col2:
                    st.write(ag[1])
                with col3:
                    st.write(ag[3])
                with col4:
                    st.write(ag[4])
                with col5:
                    st.write(ag[5])
                with col6:
                    if ag[5] == "Agendado":
                        if st.button(f"Reagendar {ag[0]}"):
                            st.session_state["reagendar_id"] = ag[0]
                            st.experimental_rerun()
                        if st.button(f"Cancelar {ag[0]}"):
                            st.session_state["cancelar_id"] = ag[0]
                            st.rerun()
        else:
            st.info("Nenhum agendamento encontrado a partir da data selecionada.")

    elif menu == "Vendas":
        st.subheader("💰 Registrar Venda")

        clientes = cursor.execute("SELECT id, nome FROM clientes ORDER BY nome").fetchall()
        clientes_dict = {c[1]: c[0] for c in clientes}
    
        st.write("### Selecione agendamento do dia para venda rápida")
        data_venda = st.date_input("Data para filtrar agendamentos", date.today())
        data_venda_str = data_venda.strftime("%Y-%m-%d")
    
        agendamentos_disponiveis = cursor.execute("""
            SELECT a.id, c.nome, a.hora, a.servicos
            FROM agendamentos a
            JOIN clientes c ON a.cliente_id = c.id
            WHERE a.data = ? AND a.status = 'Agendado'
        """, (data_venda_str,)).fetchall()
    
        agendamento_dict = {f"{ag[1]} - {ag[2]} - {ag[3]}": ag[0] for ag in agendamentos_disponiveis}
        agendamento_selecionado = st.selectbox("Agendamento disponível para venda", [""] + list(agendamento_dict.keys()))
    
        cliente_selecionado = ""
        servicos_agendados = []
    
        if agendamento_selecionado != "":
            ag_id = agendamento_dict[agendamento_selecionado]
            ag_info = cursor.execute("SELECT cliente_id, servicos FROM agendamentos WHERE id=?", (ag_id,)).fetchone()
            cliente_selecionado = next((c[1] for c in clientes if c[0] == ag_info[0]), "")
            servicos_agendados = ag_info[1].split(", ") if ag_info[1] else []
    
        else:
            cliente_selecionado = st.selectbox("Cliente para venda", [""] + list(clientes_dict.keys()))
    
        produtos = cursor.execute("SELECT id, nome, preco_venda FROM produtos ORDER BY nome").fetchall()
        produtos_dict = {p[1]: (p[0], p[2]) for p in produtos}
    
        servicos = cursor.execute("SELECT id, nome, valor FROM servicos ORDER BY nome").fetchall()
        servicos_dict = {s[1]: (s[0], s[2]) for s in servicos}
    
        with st.form("form_venda"):
            st.write(f"Cliente selecionado: **{cliente_selecionado}**")
    
            # Produtos multiselect
            itens_produtos = st.multiselect("Produtos", list(produtos_dict.keys()))
    
            # Serviços multiselect com seleção padrão dos agendados
            itens_servicos = st.multiselect("Serviços", list(servicos_dict.keys()), default=servicos_agendados)
    
            # Dicionários para guardar quantidades
            quantidade_produtos = {}
            quantidade_servicos = {}
    
            # Layout para exibir os itens com quantidade, preço unitário e subtotal
            st.markdown("### Itens selecionados")
            total_geral = 0
    
            # Produtos
            for p in itens_produtos:
                qtd = st.number_input(f"Quantidade - Produto: {p}", min_value=1, value=1, key=f"qtd_p_{p}")
                quantidade_produtos[p] = qtd
                preco = produtos_dict[p][1]
                subtotal = preco * qtd
                total_geral += subtotal
                st.write(f"**{p}** — Preço unitário: R$ {preco:.2f} — Quantidade: {qtd} — Subtotal: R$ {subtotal:.2f}")
    
            # Serviços
            for s in itens_servicos:
                qtd = st.number_input(f"Quantidade - Serviço: {s}", min_value=1, value=1, key=f"qtd_s_{s}")
                quantidade_servicos[s] = qtd
                preco = servicos_dict[s][1]
                subtotal = preco * qtd
                total_geral += subtotal
                st.write(f"**{s}** — Preço unitário: R$ {preco:.2f} — Quantidade: {qtd} — Subtotal: R$ {subtotal:.2f}")
    
            st.markdown("---")
            st.write(f"## Total: R$ {total_geral:.2f}")
    
            if st.form_submit_button("Finalizar Venda"):
                if cliente_selecionado == "":
                    st.error("Selecione um cliente para a venda.")
                elif (not itens_produtos) and (not itens_servicos):
                    st.error("Selecione pelo menos um produto ou serviço.")
                else:
                    id_cliente = clientes_dict[cliente_selecionado]
    
                    cursor.execute("""
                        INSERT INTO vendas (cliente_id, data, total, cancelada) VALUES (?, ?, ?, 0)
                    """, (id_cliente, data_venda_str, 0))
                    conn.commit()
                    venda_id = cursor.lastrowid
    
                    total = 0
                    for p_nome, qtd in quantidade_produtos.items():
                        pid, preco = produtos_dict[p_nome]
                        cursor.execute("""
                            INSERT INTO venda_itens (venda_id, tipo, item_id, quantidade, preco) VALUES (?, 'produto', ?, ?, ?)
                        """, (venda_id, pid, qtd, preco))
                        total += preco * qtd
                        cursor.execute("UPDATE produtos SET quantidade = quantidade - ? WHERE id=?", (qtd, pid))
    
                    for s_nome, qtd in quantidade_servicos.items():
                        sid, preco = servicos_dict[s_nome]
                        cursor.execute("""
                            INSERT INTO venda_itens (venda_id, tipo, item_id, quantidade, preco) VALUES (?, 'servico', ?, ?, ?)
                        """, (venda_id, sid, qtd, preco))
                        total += preco * qtd
    
                    cursor.execute("UPDATE vendas SET total=? WHERE id=?", (total, venda_id))
                    conn.commit()
    
                    # Atualiza status do agendamento para finalizado se veio da seleção
                    if agendamento_selecionado != "":
                        cursor.execute("UPDATE agendamentos SET status='Finalizado' WHERE id=?", (ag_id,))
                        conn.commit()
    
                    st.success(f"Venda finalizada com total R$ {total:.2f}")
                    st.rerun()

   
    # --- MENU CANCELAR VENDAS ---
    elif menu == "Cancelar Vendas":
        st.subheader("🚫 Cancelar Venda")
        vendas_ativas = cursor.execute("SELECT id, cliente_id, data, total FROM vendas WHERE cancelada=0 ORDER BY data DESC").fetchall()
        vendas_dict = {f"ID {v[0]} - Cliente {cursor.execute('SELECT nome FROM clientes WHERE id=?', (v[1],)).fetchone()[0]} - R$ {v[3]:.2f}": v[0] for v in vendas_ativas}

        venda_selecionada = st.selectbox("Selecione a venda para cancelar", [""] + list(vendas_dict.keys()))
        if venda_selecionada != "":
            venda_id = vendas_dict[venda_selecionada]
            if st.button("Confirmar Cancelamento"):
                cursor.execute("UPDATE vendas SET cancelada=1 WHERE id=?", (venda_id,))
                conn.commit()
                st.success("Venda cancelada!")
                st.rerun()

    # --- MENU RELATÓRIOS ---
    elif menu == "Relatórios":
        import pandas as pd
    
        st.subheader("📈 Relatórios Financeiros")
    
        # Seleção do período para relatório
        data_inicio = st.date_input("Data Início", value=pd.to_datetime("today").replace(day=1))
        data_fim = st.date_input("Data Fim", value=pd.to_datetime("today"))
    
        if data_fim < data_inicio:
            st.error("A data final não pode ser anterior à data inicial.")
        else:
            data_inicio_str = data_inicio.strftime("%Y-%m-%d")
            data_fim_str = data_fim.strftime("%Y-%m-%d")
    
            # Consulta vendas por data
            vendas_rel = cursor.execute("""
                SELECT data, SUM(total) FROM vendas
                WHERE data BETWEEN ? AND ? AND cancelada=0
                GROUP BY data ORDER BY data
            """, (data_inicio_str, data_fim_str)).fetchall()
    
            # Consulta despesas por data
            despesas_rel = cursor.execute("""
                SELECT data, SUM(valor) FROM despesas
                WHERE data BETWEEN ? AND ?
                GROUP BY data ORDER BY data
            """, (data_inicio_str, data_fim_str)).fetchall()
    
            # DataFrames
            df_vendas = pd.DataFrame(vendas_rel, columns=["Data", "Total_Vendas"])
            df_despesas = pd.DataFrame(despesas_rel, columns=["Data", "Total_Despesas"])
    
            # Ajustar datas para datetime
            df_vendas["Data"] = pd.to_datetime(df_vendas["Data"])
            df_despesas["Data"] = pd.to_datetime(df_despesas["Data"])
    
            # Combinar vendas e despesas
            df = pd.merge(df_vendas, df_despesas, on="Data", how="outer").fillna(0)
    
            # Calcular lucro
            df["Lucro"] = df["Total_Vendas"] - df["Total_Despesas"]
    
            df = df.sort_values("Data")
    
            # Gráfico de linha
            st.line_chart(df.set_index("Data")[["Total_Vendas", "Total_Despesas", "Lucro"]])
    
            # Mostrar tabela formatada
            df["Data"] = df["Data"].dt.strftime("%d/%m/%Y")
            st.write("### Tabela de Resultados")
            st.dataframe(df, use_container_width=True)


    # --- MENU BACKUP ---
    elif menu == "Backup":
        st.subheader("💾 Backup do Banco de Dados")
        fazer_backup()

    # --- MENU SAIR ---
    elif menu == "Sair":
        st.session_state.login = False
        st.session_state.menu = "Início"
        st.rerun()
