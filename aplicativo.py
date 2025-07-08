# SISTEMA COMPLETO STUDIO DEPILAÇÃO COM MELHORIAS INTEGRADAS
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

# CONFIGURAÇÃO
st.set_page_config(page_title="Studio Depilação", layout="wide")

# CONEXÃO COM O BANCO DE DADOS
conn = sqlite3.connect("studio_depilation.db", check_same_thread=False)
cursor = conn.cursor()

# FUNÇÃO PARA FORMATAR DATA PADRÃO BR
def formatar_data_br(data_iso):
    try:
        return datetime.strptime(data_iso, "%Y-%m-%d").strftime("%d/%m/%Y")
    except:
        return data_iso

# FUNÇÃO PARA BACKUP
def fazer_backup():
    with open("studio_depilation.db", "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
        href = f'<a href="data:file/db;base64,{b64}" download="backup_studio_depilation.db">📥 Baixar Backup</a>'
        st.markdown(href, unsafe_allow_html=True)

# CRIAÇÃO DAS TABELAS (SE NÃO EXISTIREM)
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
    preco_custo REAL,
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
conn.commit()

# INSERIR USUÁRIO PADRÃO
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
            st.experimental_rerun()
        else:
            st.error("Usuário ou senha inválidos")
else:
    with st.sidebar:
        # Logo com opção de upload
        if os.path.exists("logo_studio.png"):
            st.image("logo_studio.png", width=150)
        else:
            st.image("https://via.placeholder.com/150x100.png?text=LOGO", width=150)
        st.write("📎 **Importar nova logo:**")
        uploaded_logo = st.file_uploader("Importar Logo", type=["png", "jpg", "jpeg"])
        if uploaded_logo:
            with open("logo_studio.png", "wb") as f:
                f.write(uploaded_logo.read())
            st.success("Logo atualizada!")

        # Menu lateral com botões
        menu_opcoes = [
            "Início", "Dashboard", "Cadastro Cliente", "Cadastro Empresa", "Cadastro Produtos",
            "Cadastro Serviços", "Agendamento", "Vendas", "Cancelar Vendas", "Relatórios", "Backup", "Sair"
        ]
        for opcao in menu_opcoes:
            if st.button(f"📌 {opcao}"):
                st.session_state["menu"] = opcao

    menu = st.session_state.get("menu", "Início")
    st.title(f"🧭 {menu}")

    # ----------- MENU: INÍCIO -----------
    if menu == "Início":
        st.subheader("📅 Agenda do Mês")
        hoje = date.today()
        dias_do_mes = pd.date_range(hoje.replace(day=1), periods=31, freq='D')
        dias_validos = [d for d in dias_do_mes if d.month == hoje.month]
        data_selecionada = st.selectbox("Selecione um dia do mês:", [d.strftime("%d/%m/%Y") for d in dias_validos])
        data_iso = datetime.strptime(data_selecionada, "%d/%m/%Y").strftime("%Y-%m-%d")

        agendamentos = cursor.execute("""
            SELECT a.id, c.nome, a.data, a.hora, a.servicos, a.status
            FROM agendamentos a
            JOIN clientes c ON a.cliente_id = c.id
            WHERE a.data = ?
            ORDER BY a.hora
        """, (data_iso,)).fetchall()

        if agendamentos:
            st.markdown(f"### Agendamentos para {data_selecionada}")
            for ag in agendamentos:
                st.info(f"🕒 {ag[3]} | 👤 {ag[1]} | 💼 Serviços: {ag[4]} | 📌 Status: {ag[5]}")
        else:
            st.warning("Nenhum agendamento para este dia.")

    # ----------- MENU: DASHBOARD -----------
    elif menu == "Dashboard":
        st.subheader("📊 Dashboard")
        total_clientes = cursor.execute("SELECT COUNT(*) FROM clientes").fetchone()[0]
        total_vendas = cursor.execute("SELECT COUNT(*) FROM vendas WHERE cancelada=0").fetchone()[0]
        total_produtos = cursor.execute("SELECT COUNT(*) FROM produtos").fetchone()[0]
        total_servicos = cursor.execute("SELECT COUNT(*) FROM servicos").fetchone()[0]

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Clientes Cadastrados", total_clientes)
        col2.metric("Vendas Realizadas", total_vendas)
        col3.metric("Produtos Cadastrados", total_produtos)
        col4.metric("Serviços Cadastrados", total_servicos)

        vendas_data = cursor.execute("""
            SELECT cancelada, COUNT(*)
            FROM vendas
            GROUP BY cancelada
        """).fetchall()

        canceladas = 0
        realizadas = 0
        for c, q in vendas_data:
            if c == 0:
                realizadas = q
            else:
                canceladas = q

        fig, ax = plt.subplots()
        ax.bar(["Realizadas", "Canceladas"], [realizadas, canceladas], color=["green", "red"])
        ax.set_ylabel("Quantidade")
        st.pyplot(fig)

    # ----------- MENU: CADASTRO CLIENTE -----------
    elif menu == "Cadastro Cliente":
        st.subheader("🧍 Cadastro de Cliente + Histórico de Atendimentos")
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
                    # Validação data nascimento
                    try:
                        nascimento = datetime.strptime(nascimento_str, "%d/%m/%Y").date()
                    except Exception:
                        st.error("Data de nascimento inválida. Use o formato DD/MM/AAAA.")
                        st.stop()

                    assinatura_bytes = None
                    if assinatura_canvas.image_data is not None:
                        img = Image.fromarray(assinatura_canvas.image_data.astype('uint8'), 'RGBA')
                        buffered = io.BytesIO()
                        img.save(buffered, format="PNG")
                        assinatura_bytes = buffered.getvalue()

                    cursor.execute("""
                        INSERT INTO clientes (
                            nome, telefone, nascimento, hora_agendada, instagram, cantor, bebida, epilacao, alergia, qual_alergia,
                            problemas_pele, tratamento, tipo_pele, hidrata, gravida, medicamento, qual_medicamento, uso,
                            diabete, pelos_encravados, cirurgia, foliculite, qual_foliculite, problema_extra, qual_problema,
                            autorizacao_imagem, assinatura
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        nome, telefone, nascimento.strftime("%Y-%m-%d"), hora_agendada, instagram, cantor, bebida, epilacao,
                        alergia, qual_alergia, problemas_pele, tratamento, tipo_pele, hidrata, gravida, medicamento,
                        qual_medicamento, uso, diabete, pelos_encravados, cirurgia, foliculite, qual_foliculite,
                        problema_extra, qual_problema, autorizacao_imagem, assinatura_bytes
                    ))
                    conn.commit()
                    st.success("Cliente cadastrado com sucesso!")

        with col2:
            st.write("### Clientes Cadastrados")
            cliente_selecionado = st.selectbox("Selecione um cliente para ver histórico", [""] + list(clientes_dict.keys()))
            if cliente_selecionado:
                cliente_id = clientes_dict[cliente_selecionado]

                st.write("#### Dados do Cliente")
                dados = cursor.execute("SELECT * FROM clientes WHERE id=?", (cliente_id,)).fetchone()
                if dados:
                    st.write(f"Nome: {dados[1]}")
                    st.write(f"Telefone: {dados[2]}")
                    st.write(f"Nascimento: {formatar_data_br(dados[3])}")
                    st.write(f"Hora agendada: {dados[4]}")
                    st.write(f"Instagram: {dados[5]}")
                    st.write(f"Cantor favorito: {dados[6]}")
                    st.write(f"Bebida favorita: {dados[7]}")

                st.write("#### Histórico de Agendamentos")
                ags = cursor.execute("SELECT data, hora, servicos, status FROM agendamentos WHERE cliente_id=? ORDER BY data DESC", (cliente_id,)).fetchall()
                if ags:
                    for a in ags:
                        st.write(f"- {formatar_data_br(a[0])} às {a[1]}: {a[2]} (Status: {a[3]})")
                else:
                    st.info("Nenhum agendamento para este cliente.")

                st.write("#### Histórico de Vendas")
                vendas = cursor.execute("SELECT data, total, cancelada FROM vendas WHERE cliente_id=? ORDER BY data DESC", (cliente_id,)).fetchall()
                if vendas:
                    for v in vendas:
                        status_venda = "Cancelada" if v[2] else "Ativa"
                        st.write(f"- {formatar_data_br(v[0])}: R$ {v[1]:.2f} ({status_venda})")
                else:
                    st.info("Nenhuma venda para este cliente.")

    # ----------- MENU: CADASTRO EMPRESA -----------
    elif menu == "Cadastro Empresa":
        st.subheader("🏢 Cadastro da Empresa")
        empresa = cursor.execute("SELECT * FROM empresa WHERE id=1").fetchone()
        with st.form("form_empresa", clear_on_submit=False):
            nome = st.text_input("Nome da Empresa", value=empresa[1] if empresa else "")
            cnpj = st.text_input("CNPJ", value=empresa[2] if empresa else "")
            email = st.text_input("Email", value=empresa[3] if empresa else "")
            telefone = st.text_input("Telefone", value=empresa[4] if empresa else "")
            if st.form_submit_button("Salvar Dados"):
                if empresa:
                    cursor.execute("UPDATE empresa SET nome=?, cnpj=?, email=?, telefone=? WHERE id=1",
                                   (nome, cnpj, email, telefone))
                else:
                    cursor.execute("INSERT INTO empresa (id, nome, cnpj, email, telefone) VALUES (1, ?, ?, ?, ?)",
                                   (nome, cnpj, email, telefone))
                conn.commit()
                st.success("Dados da empresa atualizados!")

    # ----------- MENU: CADASTRO PRODUTOS -----------
    elif menu == "Cadastro Produtos":
        st.subheader("📦 Cadastro de Produtos")
        with st.form("form_produtos", clear_on_submit=True):
            nome = st.text_input("Nome do Produto")
            quantidade = st.number_input("Quantidade em estoque", min_value=0, step=1)
            preco_custo = st.number_input("Preço de custo (R$)", min_value=0.0, format="%.2f")
            preco_venda = st.number_input("Preço de venda (R$)", min_value=0.0, format="%.2f")
            if st.form_submit_button("Adicionar Produto"):
                cursor.execute("""
                    INSERT INTO produtos (nome, quantidade, preco_custo, preco_venda)
                    VALUES (?, ?, ?, ?)
                """, (nome, quantidade, preco_custo, preco_venda))
                conn.commit()
                st.success("Produto adicionado!")

        st.write("### Produtos Cadastrados")
        produtos = cursor.execute("SELECT id, nome, quantidade, preco_custo, preco_venda FROM produtos").fetchall()
        df_produtos = pd.DataFrame(produtos, columns=["ID", "Nome", "Quantidade", "Preço Custo", "Preço Venda"])
        st.dataframe(df_produtos)

    # ----------- MENU: CADASTRO SERVIÇOS -----------
    elif menu == "Cadastro Serviços":
        st.subheader("💆 Cadastro de Serviços")
        with st.form("form_servicos", clear_on_submit=True):
            nome = st.text_input("Nome do Serviço")
            unidade = st.text_input("Unidade (ex: sessão, hora)")
            quantidade = st.number_input("Quantidade disponível", min_value=0, step=1)
            valor = st.number_input("Valor (R$)", min_value=0.0, format="%.2f")
            if st.form_submit_button("Adicionar Serviço"):
                cursor.execute("""
                    INSERT INTO servicos (nome, unidade, quantidade, valor)
                    VALUES (?, ?, ?, ?)
                """, (nome, unidade, quantidade, valor))
                conn.commit()
                st.success("Serviço adicionado!")

        st.write("### Serviços Cadastrados")
        servicos = cursor.execute("SELECT id, nome, unidade, quantidade, valor FROM servicos").fetchall()
        df_servicos = pd.DataFrame(servicos, columns=["ID", "Nome", "Unidade", "Quantidade", "Valor"])
        st.dataframe(df_servicos)

    # ----------- MENU: AGENDAMENTO -----------
    elif menu == "Agendamento":
        st.subheader("📅 Agendamento")
        clientes = cursor.execute("SELECT id, nome FROM clientes ORDER BY nome").fetchall()
        clientes_dict = {c[1]: c[0] for c in clientes}
        cliente_selecionado = st.selectbox("Selecione o Cliente", [""] + list(clientes_dict.keys()))
        data_agendamento = st.date_input("Data do Agendamento", date.today())
        hora_agendamento = st.text_input("Hora (ex: 14:30)")
        servicos = cursor.execute("SELECT id, nome FROM servicos").fetchall()
        servicos_dict = {s[1]: s[0] for s in servicos}
        servicos_selecionados = st.multiselect("Selecione os Serviços", list(servicos_dict.keys()))
        status = st.selectbox("Status", ["Agendado", "Finalizado", "Cancelado"])

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
                    VALUES (?, ?, ?, ?, ?)
                """, (id_cliente, data_str, hora_agendamento, servicos_str, status))
                conn.commit()
                st.success("Agendamento salvo!")

    # ----------- MENU: VENDAS -----------
    elif menu == "Vendas":
        st.subheader("💰 Registrar Venda")
        clientes = cursor.execute("SELECT id, nome FROM clientes ORDER BY nome").fetchall()
        clientes_dict = {c[1]: c[0] for c in clientes}
        cliente_selecionado = st.selectbox("Cliente", [""] + list(clientes_dict.keys()))
        produtos = cursor.execute("SELECT id, nome, preco_venda FROM produtos").fetchall()
        produtos_dict = {p[1]: (p[0], p[2]) for p in produtos}
        servicos = cursor.execute("SELECT id, nome, valor FROM servicos").fetchall()
        servicos_dict = {s[1]: (s[0], s[2]) for s in servicos}

        with st.form("form_venda"):
            itens_produtos = st.multiselect("Produtos", list(produtos_dict.keys()))
            itens_servicos = st.multiselect("Serviços", list(servicos_dict.keys()))
            quantidade_produtos = {}
            quantidade_servicos = {}

            for p in itens_produtos:
                q = st.number_input(f"Quantidade - Produto: {p}", min_value=1, step=1, key=f"qtd_prod_{p}")
                quantidade_produtos[p] = q

            for s in itens_servicos:
                q = st.number_input(f"Quantidade - Serviço: {s}", min_value=1, step=1, key=f"qtd_serv_{s}")
                quantidade_servicos[s] = q

            if st.form_submit_button("Finalizar Venda"):
                if cliente_selecionado == "":
                    st.error("Selecione um cliente.")
                else:
                    id_cliente = clientes_dict[cliente_selecionado]
                    total = 0
                    cursor.execute("INSERT INTO vendas (cliente_id, data, total, cancelada) VALUES (?, ?, ?, 0)",
                                   (id_cliente, datetime.now().strftime("%Y-%m-%d"), 0))
                    venda_id = cursor.lastrowid

                    for p_nome, qtd in quantidade_produtos.items():
                        p_id, p_preco = produtos_dict[p_nome]
                        total += p_preco * qtd
                        cursor.execute("""
                            INSERT INTO venda_itens (venda_id, tipo, item_id, quantidade, preco)
                            VALUES (?, 'produto', ?, ?, ?)
                        """, (venda_id, p_id, qtd, p_preco))

                    for s_nome, qtd in quantidade_servicos.items():
                        s_id, s_valor = servicos_dict[s_nome]
                        total += s_valor * qtd
                        cursor.execute("""
                            INSERT INTO venda_itens (venda_id, tipo, item_id, quantidade, preco)
                            VALUES (?, 'servico', ?, ?, ?)
                        """, (venda_id, s_id, qtd, s_valor))

                    cursor.execute("UPDATE vendas SET total=? WHERE id=?", (total, venda_id))
                    conn.commit()
                    st.success(f"Venda registrada! Total: R$ {total:.2f}")

    # ----------- MENU: CANCELAR VENDAS -----------
    elif menu == "Cancelar Vendas":
        st.subheader("❌ Cancelar Venda")
        vendas_ativas = cursor.execute("SELECT id, data, total FROM vendas WHERE cancelada=0").fetchall()
        vendas_dict = {f"ID: {v[0]} | Data: {formatar_data_br(v[1])} | Total: R$ {v[2]:.2f}": v[0] for v in vendas_ativas}
        venda_selecionada = st.selectbox("Selecione a venda para cancelar", [""] + list(vendas_dict.keys()))
        if st.button("Cancelar Venda"):
            if venda_selecionada == "":
                st.error("Selecione uma venda para cancelar.")
            else:
                id_venda = vendas_dict[venda_selecionada]
                cursor.execute("UPDATE vendas SET cancelada=1 WHERE id=?", (id_venda,))
                conn.commit()
                st.success("Venda cancelada com sucesso!")

    # ----------- MENU: RELATÓRIOS -----------
    elif menu == "Relatórios":
        st.subheader("📈 Relatórios")
        data_inicio = st.date_input("Data início", date.today())
        data_fim = st.date_input("Data fim", date.today())
        if data_inicio > data_fim:
            st.error("Data início não pode ser maior que data fim.")
        else:
            vendas_rel = cursor.execute("""
                SELECT v.data, SUM(v.total)
                FROM vendas v
                WHERE v.cancelada=0 AND v.data BETWEEN ? AND ?
                GROUP BY v.data
                ORDER BY v.data
            """, (data_inicio.strftime("%Y-%m-%d"), data_fim.strftime("%Y-%m-%d"))).fetchall()

            if vendas_rel:
                df = pd.DataFrame(vendas_rel, columns=["Data", "Total"])
                df["Data"] = df["Data"].apply(formatar_data_br)
                st.dataframe(df)
                fig, ax = plt.subplots()
                ax.plot(df["Data"], df["Total"], marker='o')
                ax.set_xlabel("Data")
                ax.set_ylabel("Total Vendas (R$)")
                ax.set_title("Vendas por Período")
                plt.xticks(rotation=45)
                st.pyplot(fig)
            else:
                st.info("Nenhuma venda no período selecionado.")

    # ----------- MENU: BACKUP -----------
    elif menu == "Backup":
        st.subheader("💾 Backup do Banco de Dados")
        fazer_backup()

    # ----------- MENU: SAIR -----------
    elif menu == "Sair":
        st.session_state.login = False
        st.experimental_rerun()
