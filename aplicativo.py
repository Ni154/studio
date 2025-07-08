import streamlit as st
import sqlite3
from datetime import datetime, date
import pandas as pd
import matplotlib.pyplot as plt
from PIL import Image
import io
import base64
import os

# Biblioteca para ícones no menu (usarei emojis direto no texto do botão)

# CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Studio Depilação", layout="wide")

# CONEXÃO COM BANCO DE DADOS
conn = sqlite3.connect("studio_depilation.db", check_same_thread=False)
cursor = conn.cursor()

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

# INSERIR USUÁRIO PADRÃO SE NÃO EXISTIR
if not cursor.execute("SELECT * FROM usuarios WHERE usuario='admin'").fetchone():
    cursor.execute("INSERT INTO usuarios (usuario, senha) VALUES ('admin', 'admin')")
    conn.commit()

# FUNÇÃO PARA FORMATAR DATA NO FORMATO BR DD/MM/YYYY
def formatar_data_br(data_iso):
    try:
        return datetime.strptime(data_iso, "%Y-%m-%d").strftime("%d/%m/%Y")
    except:
        return data_iso

# FUNÇÃO PARA BACKUP DO BANCO (LINK PARA DOWNLOAD)
def fazer_backup():
    with open("studio_depilation.db", "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
        href = f'<a href="data:file/db;base64,{b64}" download="backup_studio_depilation.db">📥 Baixar Backup do Banco de Dados</a>'
        st.markdown(href, unsafe_allow_html=True)

# ESTADO DE LOGIN
if "login" not in st.session_state:
    st.session_state.login = False

# TELA DE LOGIN
if not st.session_state.login:
    st.title("🔐 Login Studio Depilação")
    usuario_input = st.text_input("Usuário")
    senha_input = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if cursor.execute("SELECT * FROM usuarios WHERE usuario=? AND senha=?", (usuario_input, senha_input)).fetchone():
            st.session_state.login = True
            st.experimental_rerun()
        else:
            st.error("Usuário ou senha inválidos")

else:
    # SIDEBAR COM LOGO, UPLOAD E MENU
    with st.sidebar:
        # Exibir logo
        if os.path.exists("logo_studio.png"):
            st.image("logo_studio.png", width=150)
        else:
            st.image("https://via.placeholder.com/150x100.png?text=LOGO", width=150)

        st.write("📎 **Importar nova logo:**")
        uploaded_logo = st.file_uploader("", type=["png", "jpg", "jpeg"])
        if uploaded_logo:
            with open("logo_studio.png", "wb") as f:
                f.write(uploaded_logo.read())
            st.success("Logo atualizada! Recarregue a página.")

        st.write("---")
        # Menu lateral com botões e emojis que simbolizam o conteúdo
        menu_opcoes = [
            ("Início", "🏠"),
            ("Dashboard", "📊"),
            ("Cadastro Cliente", "🧍"),
            ("Cadastro Empresa", "🏢"),
            ("Cadastro Produtos", "📦"),
            ("Cadastro Serviços", "💆"),
            ("Agendamento", "📅"),
            ("Vendas", "💰"),
            ("Cancelar Vendas", "❌"),
            ("Relatórios", "📈"),
            ("Backup", "💾"),
            ("Sair", "🚪")
        ]

        for opcao, emoji in menu_opcoes:
            if st.button(f"{emoji} {opcao}"):
                st.session_state["menu"] = opcao

    menu = st.session_state.get("menu", "Início")
    st.title(f"{menu_opcoes[[o[0] for o in menu_opcoes].index(menu)][1]} {menu}")

    # ----------- MENU INÍCIO -----------
    if menu == "Início":
        st.subheader("📅 Agenda do Dia")
        hoje = date.today()

        # Calendário simplificado - selecione a data no formato DD/MM/YYYY
        dias_do_mes = pd.date_range(hoje.replace(day=1), periods=31, freq='D')
        dias_validos = [d for d in dias_do_mes if d.month == hoje.month]

        # Lista formatada DD/MM/YYYY
        lista_datas = [d.strftime("%d/%m/%Y") for d in dias_validos]

        data_selecionada = st.selectbox("Selecione uma data:", lista_datas, index=hoje.day-1)
        # Converter para ISO para consulta no banco
        data_iso = datetime.strptime(data_selecionada, "%d/%m/%Y").strftime("%Y-%m-%d")

        # Buscar agendamentos para a data selecionada
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

# ----------- MENU DASHBOARD -----------
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

# ----------- MENU CADASTRO CLIENTE -----------
elif menu == "Cadastro Cliente":
    st.subheader("🧍 Cadastro de Cliente + Histórico")

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
            from streamlit_drawable_canvas import st_canvas
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
                # Validar data nascimento no formato DD/MM/YYYY
                try:
                    nascimento = datetime.strptime(nascimento_str, "%d/%m/%Y").date()
                except:
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

# ----------- MENU CADASTRO EMPRESA -----------
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

# ----------- MENU CADASTRO PRODUTOS -----------
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

# ----------- MENU CADASTRO SERVIÇOS -----------
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
# ----------- MENU AGENDAMENTO -----------
elif menu == "Agendamento":
    st.subheader("📅 Agendamento")

    clientes = cursor.execute("SELECT id, nome FROM clientes ORDER BY nome").fetchall()
    clientes_dict = {c[1]: c[0] for c in clientes}
    servicos = cursor.execute("SELECT id, nome FROM servicos ORDER BY nome").fetchall()
    servicos_dict = {s[1]: s[0] for s in servicos}

    with st.form("form_agendamento", clear_on_submit=True):
        cliente_nome = st.selectbox("Cliente", list(clientes_dict.keys()))
        data_str = st.text_input("Data (DD/MM/AAAA)", value=date.today().strftime("%d/%m/%Y"))
        hora = st.text_input("Hora (ex: 14:30)")
        servicos_selecionados = st.multiselect("Serviços", list(servicos_dict.keys()))
        if st.form_submit_button("Agendar"):
            try:
                data_iso = datetime.strptime(data_str, "%d/%m/%Y").strftime("%Y-%m-%d")
            except:
                st.error("Data inválida. Use o formato DD/MM/AAAA.")
                st.stop()

            servicos_texto = ", ".join(servicos_selecionados)
            cliente_id = clientes_dict[cliente_nome]
            cursor.execute("""
                INSERT INTO agendamentos (cliente_id, data, hora, servicos, status)
                VALUES (?, ?, ?, ?, ?)
            """, (cliente_id, data_iso, hora, servicos_texto, "Agendado"))
            conn.commit()
            st.success("Agendamento realizado!")

    st.write("### Agendamentos futuros")
    agendamentos = cursor.execute("""
        SELECT a.id, c.nome, a.data, a.hora, a.servicos, a.status
        FROM agendamentos a
        JOIN clientes c ON a.cliente_id = c.id
        WHERE a.data >= date('now')
        ORDER BY a.data, a.hora
    """).fetchall()

    for ag in agendamentos:
        st.info(f"ID {ag[0]} | {formatar_data_br(ag[2])} às {ag[3]} | Cliente: {ag[1]} | Serviços: {ag[4]} | Status: {ag[5]}")
        novo_status = st.selectbox(f"Alterar status do agendamento {ag[0]}", ["Agendado", "Finalizado", "Cancelado"], index=["Agendado","Finalizado","Cancelado"].index(ag[5]), key=f"status_{ag[0]}")
        if novo_status != ag[5]:
            cursor.execute("UPDATE agendamentos SET status=? WHERE id=?", (novo_status, ag[0]))
            conn.commit()
            st.experimental_rerun()

# ----------- MENU VENDAS -----------
elif menu == "Vendas":
    st.subheader("💰 Registrar Venda")

    clientes = cursor.execute("SELECT id, nome FROM clientes ORDER BY nome").fetchall()
    clientes_dict = {c[1]: c[0] for c in clientes}
    produtos = cursor.execute("SELECT id, nome, preco_venda FROM produtos WHERE quantidade > 0").fetchall()
    servicos = cursor.execute("SELECT id, nome, valor FROM servicos").fetchall()

    with st.form("form_vendas", clear_on_submit=True):
        cliente_nome = st.selectbox("Cliente", list(clientes_dict.keys()))
        data_str = st.text_input("Data da venda (DD/MM/AAAA)", value=date.today().strftime("%d/%m/%Y"))

        st.markdown("### Produtos")
        produtos_selecionados = {}
        for p in produtos:
            qtd = st.number_input(f"{p[1]} (R$ {p[2]:.2f})", min_value=0, step=1, key=f"produto_{p[0]}")
            if qtd > 0:
                produtos_selecionados[p[0]] = qtd

        st.markdown("### Serviços")
        servicos_selecionados = {}
        for s in servicos:
            qtd = st.number_input(f"{s[1]} (R$ {s[2]:.2f})", min_value=0, step=1, key=f"servico_{s[0]}")
            if qtd > 0:
                servicos_selecionados[s[0]] = qtd

        if st.form_submit_button("Finalizar Venda"):
            try:
                data_iso = datetime.strptime(data_str, "%d/%m/%Y").strftime("%Y-%m-%d")
            except:
                st.error("Data inválida.")
                st.stop()

            if not produtos_selecionados and not servicos_selecionados:
                st.error("Selecione ao menos um produto ou serviço.")
                st.stop()

            cliente_id = clientes_dict[cliente_nome]
            total = 0

            # Calcular total
            for pid, qtd in produtos_selecionados.items():
                preco = next(p[2] for p in produtos if p[0] == pid)
                total += preco * qtd

            for sid, qtd in servicos_selecionados.items():
                valor = next(s[2] for s in servicos if s[0] == sid)
                total += valor * qtd

            cursor.execute("INSERT INTO vendas (cliente_id, data, total) VALUES (?, ?, ?)", (cliente_id, data_iso, total))
            venda_id = cursor.lastrowid

            # Inserir itens venda e diminuir estoque dos produtos
            for pid, qtd in produtos_selecionados.items():
                preco = next(p[2] for p in produtos if p[0] == pid)
                cursor.execute("INSERT INTO venda_itens (venda_id, tipo, item_id, quantidade, preco) VALUES (?, 'produto', ?, ?, ?)",
                               (venda_id, pid, qtd, preco))
                # Atualizar estoque
                cursor.execute("UPDATE produtos SET quantidade = quantidade - ? WHERE id = ?", (qtd, pid))

            for sid, qtd in servicos_selecionados.items():
                valor = next(s[2] for s in servicos if s[0] == sid)
                cursor.execute("INSERT INTO venda_itens (venda_id, tipo, item_id, quantidade, preco) VALUES (?, 'servico', ?, ?, ?)",
                               (venda_id, sid, qtd, valor))

            conn.commit()
            st.success(f"Venda finalizada! Total: R$ {total:.2f}")

    st.write("### Vendas realizadas")
    vendas = cursor.execute("""
        SELECT v.id, c.nome, v.data, v.total, v.cancelada
        FROM vendas v
        JOIN clientes c ON v.cliente_id = c.id
        ORDER BY v.data DESC
    """).fetchall()

    for v in vendas:
        status = "Cancelada" if v[4] else "Ativa"
        st.info(f"ID {v[0]} | Cliente: {v[1]} | Data: {formatar_data_br(v[2])} | Total: R$ {v[3]:.2f} | Status: {status}")

# ----------- MENU CANCELAR VENDAS -----------
elif menu == "Cancelar Vendas":
    st.subheader("❌ Cancelar Venda")
    vendas_ativas = cursor.execute("SELECT id FROM vendas WHERE cancelada=0").fetchall()
    venda_ids = [v[0] for v in vendas_ativas]

    venda_cancelar = st.selectbox("Selecione venda para cancelar", venda_ids)
    if st.button("Cancelar Venda"):
        cursor.execute("UPDATE vendas SET cancelada=1 WHERE id=?", (venda_cancelar,))
        conn.commit()
        st.success(f"Venda ID {venda_cancelar} cancelada.")
        st.experimental_rerun()

# ----------- MENU RELATÓRIOS -----------
elif menu == "Relatórios":
    st.subheader("📈 Relatórios")

    data_inicio = st.date_input("Data início", value=date.today().replace(day=1))
    data_fim = st.date_input("Data fim", value=date.today())

    if data_inicio > data_fim:
        st.error("Data início deve ser menor ou igual à data fim.")
    else:
        data_ini_str = data_inicio.strftime("%Y-%m-%d")
        data_fim_str = data_fim.strftime("%Y-%m-%d")

        vendas = cursor.execute("""
            SELECT data, SUM(total) FROM vendas
            WHERE data BETWEEN ? AND ? AND cancelada=0
            GROUP BY data
            ORDER BY data
        """, (data_ini_str, data_fim_str)).fetchall()

        if vendas:
            datas = [v[0] for v in vendas]
            totais = [v[1] for v in vendas]
            datas_fmt = [formatar_data_br(d) for d in datas]

            st.line_chart(data=pd.DataFrame({"Total Vendas": totais}, index=datas_fmt))
        else:
            st.info("Nenhuma venda no período selecionado.")

# ----------- MENU BACKUP -----------
elif menu == "Backup":
    st.subheader("💾 Backup do Banco de Dados")
    fazer_backup()

# ----------- MENU SAIR -----------
elif menu == "Sair":
    st.session_state.login = False
    st.experimental_rerun()
