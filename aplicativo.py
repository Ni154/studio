import streamlit as st
import sqlite3
from datetime import datetime, date
from streamlit_drawable_canvas import st_canvas
from PIL import Image
import io
import pandas as pd
import plotly.express as px
import shutil
import os
import tempfile
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm

st.set_page_config(page_title="Studio de Depilação", layout="wide", initial_sidebar_state="expanded")

DB_PATH = "studio.db"
BACKUP_DIR = "backups"
BACKUP_LOG = "backup_log.txt"

# Funções de backup (igual no seu código original)...
def realizar_backup():
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(BACKUP_DIR, f"studio_backup_{timestamp}.db")
    shutil.copy2(DB_PATH, backup_path)
    with open(BACKUP_LOG, "w") as f:
        f.write(datetime.now().strftime("%Y-%m-%d"))
    st.info(f"Backup automático realizado: {backup_path}")

def checar_backup():
    if not os.path.exists(BACKUP_LOG):
        realizar_backup()
        return
    with open(BACKUP_LOG, "r") as f:
        ultima_data_str = f.read().strip()
    try:
        ultima_data = datetime.strptime(ultima_data_str, "%Y-%m-%d").date()
    except:
        realizar_backup()
        return
    hoje = date.today()
    if (hoje - ultima_data).days >= 15:
        realizar_backup()

if not os.path.exists(DB_PATH):
    open(DB_PATH, 'a').close()

checar_backup()
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
cursor = conn.cursor()

# Criação das tabelas (incluindo empresa e preco_custo no produtos)
cursor.execute("""
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY, usuario TEXT UNIQUE, senha TEXT
)
""")
cursor.execute("INSERT OR IGNORE INTO usuarios (id, usuario, senha) VALUES (1, 'admin', 'admin')")

cursor.execute("""
CREATE TABLE IF NOT EXISTS clientes (
    id INTEGER PRIMARY KEY, nome TEXT, telefone TEXT, data_nascimento TEXT, instagram TEXT,
    cantor_favorito TEXT, bebida_favorita TEXT, assinatura BLOB
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS ficha_avaliacao (
    id INTEGER PRIMARY KEY, cliente_id INTEGER,
    epilacao_anterio TEXT, alergia TEXT, qual_alergia TEXT, problema_pele TEXT,
    tratamento_dermatologico TEXT, tipo_pele TEXT, hidrata_pele TEXT, gravida TEXT,
    medicamento TEXT, qual_medicamento TEXT, dispositivo TEXT, diabete TEXT,
    pelos_encravados TEXT, cirurgia_recente TEXT, foliculite TEXT, qual_foliculite TEXT,
    outro_problema TEXT, qual_outro TEXT, autorizacao_imagem TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS agendamentos (
    id INTEGER PRIMARY KEY, cliente_id INTEGER, servico TEXT, data TEXT, hora TEXT, status TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS servicos (
    id INTEGER PRIMARY KEY, nome TEXT, descricao TEXT, duracao INTEGER, valor REAL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS produtos (
    id INTEGER PRIMARY KEY, nome TEXT, estoque INTEGER, valor REAL, preco_custo REAL DEFAULT 0
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS vendas (
    id INTEGER PRIMARY KEY, cliente_id INTEGER, data TEXT, forma_pagamento TEXT, total REAL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS vendas_itens (
    id INTEGER PRIMARY KEY, venda_id INTEGER, tipo TEXT, nome TEXT, quantidade INTEGER, preco REAL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS despesas (
    id INTEGER PRIMARY KEY, descricao TEXT, valor REAL, data TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS empresa (
    nome TEXT,
    cnpj TEXT,
    endereco TEXT,
    telefone TEXT,
    email TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS empresa (
    id INTEGER PRIMARY KEY,
    nome TEXT,
    cnpj TEXT,
    endereco TEXT,
    telefone TEXT,
    email TEXT
)
""")
conn.commit()


# Estilo e layout (igual no seu código original)...

# Função menu lateral com botões fixos
def menu_lateral_botao(opcoes, key):
    selected = st.session_state.get(key, opcoes[0])
    for opcao in opcoes:
        classe = "menu-btn"
        if opcao == selected:
            classe += " menu-btn-selected"
        if st.button(opcao, key=f"menu_{opcao}"):
            st.session_state[key] = opcao
            st.experimental_rerun()
    return st.session_state.get(key)

menu_opcoes = [
    "Início","Dashboard", "Clientes", "Agendamentos", "Serviços",
    "Produtos", "Vendas", "Despesas", "Relatórios",
    "Cadastro Empresa", "Importação", "Sair"
]

# Login igual ao seu código original (sem alterações) ...

with st.sidebar:
    st.image("https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=400&q=80", use_column_width=True)
    st.markdown("### Priscila Santos Epilação")
    st.markdown("---")
    menu = menu_lateral_botao(menu_opcoes, "menu_selecionado")

# Continua no próximo envio com as páginas específicas integradas (Clientes, Produtos com edição, Vendas com comprovante, Cadastro da empresa, Relatórios melhorados etc.)
if menu == "Clientes":
    st.title("👩 Cadastro de Clientes + Ficha de Avaliação")

    with st.form("form_cadastro_cliente"):
        col1, col2 = st.columns(2)
        with col1:
            nome = st.text_input("Nome completo", key="nome_cliente")
            telefone = st.text_input("Telefone", key="telefone_cliente")
            data_nascimento = st.date_input("Data de nascimento", value=date(1990,1,1), max_value=date.today(), key="nascimento_cliente")
            instagram = st.text_input("Instagram", key="instagram_cliente")
        with col2:
            cantor = st.text_input("Cantor favorito", key="cantor_cliente")
            bebida = st.text_input("Bebida favorita", key="bebida_cliente")

        st.markdown("### ✍️ Assinatura Digital")
        canvas_result = st_canvas(
            fill_color="rgba(255,255,255,0)", stroke_width=2,
            stroke_color="#000", background_color="#fff", height=150,
            drawing_mode="freedraw", key="canvas_assinatura"
        )
        assinatura_bytes = None
        if canvas_result.image_data is not None:
            img = canvas_result.image_data
            buffered = io.BytesIO()
            Image.fromarray((img[:, :, :3]).astype('uint8')).save(buffered, format="PNG")
            assinatura_bytes = buffered.getvalue()

        st.markdown("### 📋 Anamnese")
        col1, col2 = st.columns(2)
        with col1:
            epilacao = st.radio("Já fez epilação na cera?", ["SIM", "NÃO"], key="epilacao")
            alergia = st.radio("Possui alergia?", ["SIM", "NÃO"], key="alergia")
            qual_alergia = st.text_input("Qual?", disabled=(alergia == "NÃO"), key="qual_alergia")
            problema_pele = st.radio("Problemas de pele?", ["SIM", "NÃO"], key="problema_pele")
            tratamento = st.radio("Em tratamento dermatológico?", ["SIM", "NÃO"], key="tratamento")
            tipo_pele = st.selectbox("Tipo de pele", ["SECA", "OLEOSA", "NORMAL"], key="tipo_pele")
            hidrata = st.radio("Hidrata a pele?", ["SIM", "NÃO"], key="hidrata")
            gravida = st.radio("Está grávida?", ["SIM", "NÃO"], key="gravida")
        with col2:
            medicamento = st.radio("Usa medicamento?", ["SIM", "NÃO"], key="medicamento")
            qual_medicamento = st.text_input("Qual?", disabled=(medicamento == "NÃO"), key="qual_medicamento")
            dispositivo = st.selectbox("Dispositivo?", ["DIU", "Marca-passo", "Nenhum"], key="dispositivo")
            diabete = st.radio("Diabetes?", ["SIM", "NÃO"], key="diabete")
            encravado = st.radio("Pelos encravados?", ["SIM", "NÃO"], key="encravado")
            cirurgia = st.radio("Cirurgia recente?", ["SIM", "NÃO"], key="cirurgia")
            foliculite = st.radio("Foliculite?", ["SIM", "NÃO"], key="foliculite")
            qual_foliculite = st.text_input("Qual?", disabled=(foliculite == "NÃO"), key="qual_foliculite")
            outro = st.radio("Outro problema?", ["SIM", "NÃO"], key="outro")
            qual_outro = st.text_input("Qual?", disabled=(outro == "NÃO"), key="qual_outro")
            imagem = st.radio("Autoriza uso de imagem?", ["SIM", "NÃO"], key="imagem")

        if st.form_submit_button("Salvar Cadastro"):
            if not nome.strip():
                st.error("O nome do cliente é obrigatório.")
            else:
                cursor.execute(
                    """INSERT INTO clientes (nome, telefone, data_nascimento, instagram, cantor_favorito, bebida_favorita, assinatura)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (nome, telefone, str(data_nascimento), instagram, cantor, bebida, assinatura_bytes)
                )
                cliente_id = cursor.lastrowid

                cursor.execute(
                    """INSERT INTO ficha_avaliacao (
                        cliente_id, epilacao_anterio, alergia, qual_alergia, problema_pele,
                        tratamento_dermatologico, tipo_pele, hidrata_pele, gravida, medicamento,
                        qual_medicamento, dispositivo, diabete, pelos_encravados, cirurgia_recente,
                        foliculite, qual_foliculite, outro_problema, qual_outro, autorizacao_imagem)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (cliente_id, epilacao, alergia, qual_alergia, problema_pele, tratamento, tipo_pele, hidrata,
                     gravida, medicamento, qual_medicamento, dispositivo, diabete, encravado, cirurgia,
                     foliculite, qual_foliculite, outro, qual_outro, imagem)
                )
                conn.commit()
                st.success("✅ Cadastro salvo com sucesso!")

    st.markdown("### Clientes Cadastrados")
    clientes = cursor.execute("SELECT id, nome, telefone FROM clientes").fetchall()
    if clientes:
        for c in clientes:
            st.write(f"**{c[1]}** — Telefone: {c[2]}")
    else:
        st.info("Nenhum cliente cadastrado ainda.")
elif menu == "Produtos":
    st.title("📦 Produtos")

    # Cadastro / edição
    with st.form("form_produtos"):
        produto_ids = [p[0] for p in cursor.execute("SELECT id FROM produtos").fetchall()]
        produtos_todos = cursor.execute("SELECT id, nome, estoque, valor, preco_custo FROM produtos").fetchall()

        col1, col2 = st.columns(2)
        with col1:
            # Select para editar ou criar novo
            produto_selecionado_id = st.selectbox(
                "Selecione produto para editar ou escolha 'Novo Produto'",
                options=[0] + produto_ids,
                format_func=lambda x: "Novo Produto" if x == 0 else [p[1] for p in produtos_todos if p[0] == x][0]
            )
        with col2:
            if produto_selecionado_id != 0:
                prod = next((p for p in produtos_todos if p[0] == produto_selecionado_id), None)
                nome = st.text_input("Nome do produto", value=prod[1])
                estoque = st.number_input("Estoque", min_value=0, step=1, value=prod[2])
                valor = st.number_input("Preço de venda (R$)", min_value=0.0, step=0.1, format="%.2f", value=prod[3])
                preco_custo = st.number_input("Preço de custo (R$)", min_value=0.0, step=0.1, format="%.2f", value=prod[4])
            else:
                nome = st.text_input("Nome do produto", value="")
                estoque = st.number_input("Estoque", min_value=0, step=1, value=0)
                valor = st.number_input("Preço de venda (R$)", min_value=0.0, step=0.1, format="%.2f", value=0.0)
                preco_custo = st.number_input("Preço de custo (R$)", min_value=0.0, step=0.1, format="%.2f", value=0.0)

        if st.form_submit_button("Salvar Produto"):
            if not nome.strip():
                st.error("O nome do produto é obrigatório.")
            else:
                if produto_selecionado_id == 0:
                    # Inserir novo produto
                    cursor.execute(
                        "INSERT INTO produtos (nome, estoque, valor, preco_custo) VALUES (?, ?, ?, ?)",
                        (nome, estoque, valor, preco_custo)
                    )
                    conn.commit()
                    st.success("✅ Produto cadastrado com sucesso.")
                else:
                    # Atualizar produto existente
                    cursor.execute(
                        "UPDATE produtos SET nome=?, estoque=?, valor=?, preco_custo=? WHERE id=?",
                        (nome, estoque, valor, preco_custo, produto_selecionado_id)
                    )
                    conn.commit()
                    st.success("✅ Produto atualizado com sucesso.")

    # Listagem simples abaixo do formulário
    st.markdown("### 📋 Lista de Produtos")
    produtos = cursor.execute("SELECT id, nome, estoque, valor, preco_custo FROM produtos").fetchall()
    if produtos:
        for p in produtos:
            st.write(f"**{p[1]}** — Estoque: {p[2]} | Preço Venda: R$ {p[3]:.2f} | Preço Custo: R$ {p[4]:.2f}")
    else:
        st.info("Nenhum produto cadastrado ainda.")
elif menu == "Vendas":
    st.title("💳 Vendas")

    # Buscar dados
    clientes = cursor.execute("SELECT id, nome FROM clientes").fetchall()
    servicos = cursor.execute("SELECT nome, valor FROM servicos").fetchall()
    produtos = cursor.execute("SELECT id, nome, valor, estoque FROM produtos").fetchall()
    empresa = cursor.execute("SELECT nome, cnpj, endereco, telefone, email FROM empresa LIMIT 1").fetchone()

    if not clientes:
        st.warning("⚠️ Cadastre clientes antes de realizar vendas.")
        st.stop()

    # Preparar listas para seleção com opção Nenhum
    lista_produtos = ["Nenhum"] + [p[1] for p in produtos]
    lista_servicos = ["Nenhum"] + [s[0] for s in servicos]

    with st.form("form_venda"):
        cliente = st.selectbox("Cliente", clientes, format_func=lambda x: x[1])
        forma_pagamento = st.selectbox("Forma de pagamento", ["Dinheiro", "Cartão", "Pix"])

        st.markdown("### Produtos")
        produto_selecionado = st.selectbox("Produto", lista_produtos)
        quantidade_prod = 0
        if produto_selecionado != "Nenhum":
            idx_prod = [p[1] for p in produtos].index(produto_selecionado)
            estoque_atual = produtos[idx_prod][3]
            quantidade_prod = st.number_input("Quantidade", min_value=1, step=1, key="qtd_produto")
        else:
            quantidade_prod = 0

        st.markdown("### Serviços")
        servico_selecionado = st.selectbox("Serviço", lista_servicos)
        quantidade_serv = 0
        if servico_selecionado != "Nenhum":
            quantidade_serv = st.number_input("Quantidade", min_value=1, step=1, key="qtd_servico")
        else:
            quantidade_serv = 0

        if st.form_submit_button("Finalizar Venda"):
            total = 0.0
            itens_venda = []

            if produto_selecionado != "Nenhum":
                valor_prod = produtos[idx_prod][2]
                if estoque_atual < quantidade_prod:
                    st.error("Estoque insuficiente para o produto selecionado.")
                    st.stop()
                total += valor_prod * quantidade_prod
                itens_venda.append(("Produto", produto_selecionado, quantidade_prod, valor_prod))

            if servico_selecionado != "Nenhum":
                idx_serv = [s[0] for s in servicos].index(servico_selecionado)
                valor_serv = servicos[idx_serv][1]
                total += valor_serv * quantidade_serv
                itens_venda.append(("Serviço", servico_selecionado, quantidade_serv, valor_serv))

            if len(itens_venda) == 0:
                st.error("Selecione pelo menos um produto ou serviço para realizar a venda.")
                st.stop()

            # Inserir venda
            cursor.execute(
                "INSERT INTO vendas (cliente_id, data, forma_pagamento, total) VALUES (?, ?, ?, ?)",
                (cliente[0], str(date.today()), forma_pagamento, total)
            )
            venda_id = cursor.lastrowid

            # Inserir itens da venda
            for tipo, nome, qtd, preco in itens_venda:
                cursor.execute(
                    "INSERT INTO vendas_itens (venda_id, tipo, nome, quantidade, preco) VALUES (?, ?, ?, ?, ?)",
                    (venda_id, tipo, nome, qtd, preco)
                )
                # Atualizar estoque se for produto
                if tipo == "Produto":
                    idx_produto = [p[1] for p in produtos].index(nome)
                    estoque_novo = produtos[idx_produto][3] - qtd
                    cursor.execute("UPDATE produtos SET estoque=? WHERE id=?", (estoque_novo, produtos[idx_produto][0]))

            conn.commit()
            st.success(f"Venda finalizada com sucesso! Total: R$ {total:.2f}")

            # Gerar comprovante PDF
            import pdfkit
            from tempfile import NamedTemporaryFile

            cabecalho = f"""
            <h2 style='text-align:center'>{empresa[0] if empresa else 'Studio de Depilação'}</h2>
            <p style='text-align:center'>
            CNPJ: {empresa[1] if empresa else ''}<br>
            Endereço: {empresa[2] if empresa else ''}<br>
            Telefone: {empresa[3] if empresa else ''}<br>
            Email: {empresa[4] if empresa else ''}
            </p>
            <hr>
            <h3>Comprovante de Venda</h3>
            <p><strong>Cliente:</strong> {cliente[1]}</p>
            <p><strong>Data:</strong> {date.today()}</p>
            <p><strong>Forma de pagamento:</strong> {forma_pagamento}</p>
            <table border="1" style="width:100%; border-collapse: collapse;">
                <thead>
                    <tr><th>Tipo</th><th>Nome</th><th>Quantidade</th><th>Preço Unit.</th><th>Subtotal</th></tr>
                </thead>
                <tbody>
            """

            linhas = ""
            for tipo, nome, qtd, preco in itens_venda:
                subtotal = qtd * preco
                linhas += f"<tr><td>{tipo}</td><td>{nome}</td><td>{qtd}</td><td>R$ {preco:.2f}</td><td>R$ {subtotal:.2f}</td></tr>"

            rodape = f"""
                </tbody>
            </table>
            <h3>Total: R$ {total:.2f}</h3>
            <hr>
            <p style='text-align:center; font-size:12px;'>Obrigado pela preferência! {empresa[0] if empresa else ''}</p>
            """

            html = cabecalho + linhas + rodape

            with NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
                pdfkit.from_string(html, tmp_pdf.name)
                with open(tmp_pdf.name, "rb") as fpdf:
                    pdf_bytes = fpdf.read()

            st.download_button("📄 Baixar Comprovante PDF", data=pdf_bytes, file_name=f"comprovante_{venda_id}.pdf", mime="application/pdf")
elif menu == "Cadastro Empresa":
    st.title("🏢 Cadastro da Empresa")

    # Buscar dados existentes
    empresa = cursor.execute("SELECT id, nome, cnpj, endereco, telefone, email FROM empresa LIMIT 1").fetchone()

    if empresa:
        empresa_id = empresa[0]
        nome = empresa[1]
        cnpj = empresa[2]
        endereco = empresa[3]
        telefone = empresa[4]
        email = empresa[5]
    else:
        empresa_id = None
        nome = ""
        cnpj = ""
        endereco = ""
        telefone = ""
        email = ""

    with st.form("form_empresa"):
        nome = st.text_input("Nome da empresa", value=nome)
        cnpj = st.text_input("CNPJ", value=cnpj)
        endereco = st.text_input("Endereço", value=endereco)
        telefone = st.text_input("Telefone", value=telefone)
        email = st.text_input("E-mail", value=email)

        if st.form_submit_button("Salvar Dados"):
            if not nome.strip():
                st.error("O nome da empresa é obrigatório.")
            else:
                if empresa_id:
                    cursor.execute(
                        "UPDATE empresa SET nome=?, cnpj=?, endereco=?, telefone=?, email=? WHERE id=?",
                        (nome, cnpj, endereco, telefone, email, empresa_id)
                    )
                else:
                    cursor.execute(
                        "INSERT INTO empresa (nome, cnpj, endereco, telefone, email) VALUES (?, ?, ?, ?, ?)",
                        (nome, cnpj, endereco, telefone, email)
                    )
                conn.commit()
                st.success("✅ Dados da empresa salvos com sucesso!")

elif menu == "Relatórios":
    st.title("📊 Relatórios")

    tipo_rel = st.selectbox("Tipo de relatório", ["Vendas", "Despesas"])
    data_ini = st.date_input("Data inicial", value=date(2023, 1, 1))
    data_fim = st.date_input("Data final", value=date.today())

    if data_ini > data_fim:
        st.error("Data inicial não pode ser maior que a data final.")
        st.stop()

    empresa = cursor.execute("SELECT nome, cnpj, endereco, telefone, email FROM empresa LIMIT 1").fetchone()

    if tipo_rel == "Vendas":
        query = """
            SELECT v.data, v.forma_pagamento, v.total, c.nome
            FROM vendas v
            LEFT JOIN clientes c ON v.cliente_id = c.id
            WHERE date(v.data) BETWEEN ? AND ?
            ORDER BY v.data ASC
        """
        df = pd.read_sql_query(query, conn, params=(str(data_ini), str(data_fim)))

        if df.empty:
            st.warning("Nenhum dado de vendas encontrado no período.")
        else:
            st.dataframe(df)

            # Gráfico total vendas por dia
            fig = px.bar(df.groupby('data').sum().reset_index(), x='data', y='total', title="Total de Vendas por Dia")
            st.plotly_chart(fig)

            # Botão para exportar relatório com cabeçalho e rodapé
            import pdfkit
            from tempfile import NamedTemporaryFile

            cabecalho = f"""
            <h2 style='text-align:center'>{empresa[0] if empresa else 'Studio de Depilação'}</h2>
            <p style='text-align:center'>
            CNPJ: {empresa[1] if empresa else ''}<br>
            Endereço: {empresa[2] if empresa else ''}<br>
            Telefone: {empresa[3] if empresa else ''}<br>
            Email: {empresa[4] if empresa else ''}
            </p>
            <hr>
            <h3>Relatório de Vendas</h3>
            <p>Período: {data_ini} até {data_fim}</p>
            <table border="1" style="width:100%; border-collapse: collapse;">
                <thead>
                    <tr><th>Data</th><th>Forma Pagamento</th><th>Total (R$)</th><th>Cliente</th></tr>
                </thead>
                <tbody>
            """

            linhas = ""
            for _, row in df.iterrows():
                linhas += f"<tr><td>{row['data']}</td><td>{row['forma_pagamento']}</td><td>R$ {row['total']:.2f}</td><td>{row['nome']}</td></tr>"

            rodape = """
                </tbody>
            </table>
            <hr>
            <p style='text-align:center; font-size:12px;'>Relatório gerado pelo sistema Studio de Depilação</p>
            """

            html = cabecalho + linhas + rodape

            with NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
                pdfkit.from_string(html, tmp_pdf.name)
                with open(tmp_pdf.name, "rb") as fpdf:
                    pdf_bytes = fpdf.read()

            st.download_button("📄 Baixar Relatório de Vendas PDF", data=pdf_bytes, file_name="relatorio_vendas.pdf", mime="application/pdf")

    else:
        # Relatório Despesas
        query = """
            SELECT descricao, valor, data
            FROM despesas
            WHERE date(data) BETWEEN ? AND ?
            ORDER BY data ASC
        """
        df = pd.read_sql_query(query, conn, params=(str(data_ini), str(data_fim)))

        if df.empty:
            st.warning("Nenhum dado de despesas encontrado no período.")
        else:
            st.dataframe(df)

            fig = px.bar(df.groupby('data').sum().reset_index(), x='data', y='valor', title="Despesas por Dia")
            st.plotly_chart(fig)

            import pdfkit
            from tempfile import NamedTemporaryFile

            cabecalho = f"""
            <h2 style='text-align:center'>{empresa[0] if empresa else 'Studio de Depilação'}</h2>
            <p style='text-align:center'>
            CNPJ: {empresa[1] if empresa else ''}<br>
            Endereço: {empresa[2] if empresa else ''}<br>
            Telefone: {empresa[3] if empresa else ''}<br>
            Email: {empresa[4] if empresa else ''}
            </p>
            <hr>
            <h3>Relatório de Despesas</h3>
            <p>Período: {data_ini} até {data_fim}</p>
            <table border="1" style="width:100%; border-collapse: collapse;">
                <thead>
                    <tr><th>Descrição</th><th>Valor (R$)</th><th>Data</th></tr>
                </thead>
                <tbody>
            """

            linhas = ""
            for _, row in df.iterrows():
                linhas += f"<tr><td>{row['descricao']}</td><td>R$ {row['valor']:.2f}</td><td>{row['data']}</td></tr>"

            rodape = """
                </tbody>
            </table>
            <hr>
            <p style='text-align:center; font-size:12px;'>Relatório gerado pelo sistema Studio de Depilação</p>
            """

            html = cabecalho + linhas + rodape

            with NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
                pdfkit.from_string(html, tmp_pdf.name)
                with open(tmp_pdf.name, "rb") as fpdf:
                    pdf_bytes = fpdf.read()

            st.download_button("📄 Baixar Relatório de Despesas PDF", data=pdf_bytes, file_name="relatorio_despesas.pdf", mime="application/pdf")
# Atualize a lista de opções do menu lateral:
menu_opcoes = [
    "Início", "Clientes", "Agendamentos", "Serviços",
    "Produtos", "Vendas", "Despesas", "Relatórios",
    "Cadastro Empresa", "Dashboard", "Importação", "Sair"
]

# Função menu lateral com botões fixos (mantida igual)
def menu_lateral_botao(opcoes, key):
    selected = st.session_state.get(key, opcoes[0])
    for opcao in opcoes:
        classe = "menu-btn"
        if opcao == selected:
            classe += " menu-btn-selected"
        if st.button(opcao, key=f"menu_{opcao}"):
            st.session_state[key] = opcao
            st.experimental_rerun()
    return st.session_state.get(key)

# No sidebar, o menu lateral fixo com os botões:
with st.sidebar:
    st.image("https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=400&q=80", use_column_width=True)
    st.markdown("### Priscila Santos Epilação")
    st.markdown("---")
    menu = menu_lateral_botao(menu_opcoes, "menu_selecionado")

# Implementação do menu "Dashboard"
if menu == "Dashboard":
    st.title("📊 Dashboard - Informações Gerais")

    # Total de clientes
    total_clientes = cursor.execute("SELECT COUNT(*) FROM clientes").fetchone()[0]

    # Total de vendas
    total_vendas = cursor.execute("SELECT COUNT(*) FROM vendas").fetchone()[0]

    # Total de vendas canceladas (se quiser registrar cancelamentos, deve ter campo de status, mas como não tem, vamos supor que não há)
    # Caso tenha, adapte aqui, ex:
    # total_vendas_canceladas = cursor.execute("SELECT COUNT(*) FROM vendas WHERE status='Cancelado'").fetchone()[0]
    # Por enquanto deixamos 0
    total_vendas_canceladas = 0

    # Total de agendamentos cancelados
    total_agendamentos_cancelados = cursor.execute("SELECT COUNT(*) FROM agendamentos WHERE status='Cancelado'").fetchone()[0]

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Clientes Cadastrados", total_clientes)
    col2.metric("Vendas Realizadas", total_vendas)
    col3.metric("Vendas Canceladas", total_vendas_canceladas)
    col4.metric("Agendamentos Cancelados", total_agendamentos_cancelados)

    st.markdown("---")
    st.markdown("Dashboard com informações resumidas do sistema.")

# Não esqueça que as demais opções (Início, Clientes, Agendamentos, Serviços, Produtos, Vendas, Despesas, Relatórios, Cadastro Empresa, Importação, Sair) permanecem conforme já implementadas.

elif menu == "Vendas":
    st.title("💳 Vendas")

    clientes = cursor.execute("SELECT id, nome FROM clientes").fetchall()
    servicos = cursor.execute("SELECT nome, valor FROM servicos").fetchall()
    produtos = cursor.execute("SELECT nome, valor, estoque FROM produtos").fetchall()

    if not clientes:
        st.warning("Cadastre clientes para realizar vendas.")
        st.stop()
    if not servicos and not produtos:
        st.warning("Cadastre produtos ou serviços para realizar vendas.")
        st.stop()

    with st.form("form_venda"):
        cliente = st.selectbox("Cliente", clientes, format_func=lambda x: x[1])
        forma_pagamento = st.selectbox("Forma de pagamento", ["Dinheiro", "Cartão", "Pix"])

        st.markdown("### Produtos")
        opcoes_produto = ["Nenhum"] + [p[0] for p in produtos]
        produto_selecionado = st.selectbox("Produto", opcoes_produto)
        quantidade_prod = 0
        if produto_selecionado != "Nenhum":
            quantidade_prod = st.number_input("Quantidade", min_value=1, step=1, key="qtd_produto")
        
        st.markdown("### Serviços")
        opcoes_servico = ["Nenhum"] + [s[0] for s in servicos]
        servico_selecionado = st.selectbox("Serviço", opcoes_servico)
        quantidade_serv = 0
        if servico_selecionado != "Nenhum":
            quantidade_serv = st.number_input("Quantidade", min_value=1, step=1, key="qtd_servico")

        if st.form_submit_button("Finalizar Venda"):
            total = 0
            if produto_selecionado != "Nenhum":
                idx_prod = [p[0] for p in produtos].index(produto_selecionado)
                estoque_atual = produtos[idx_prod][2]
                valor_prod = produtos[idx_prod][1]

                if estoque_atual < quantidade_prod:
                    st.error("Estoque insuficiente para o produto selecionado.")
                    st.stop()
                total += valor_prod * quantidade_prod
            else:
                quantidade_prod = 0

            if servico_selecionado != "Nenhum":
                idx_serv = [s[0] for s in servicos].index(servico_selecionado)
                valor_serv = servicos[idx_serv][1]
                total += valor_serv * quantidade_serv
            else:
                quantidade_serv = 0

            if quantidade_prod == 0 and quantidade_serv == 0:
                st.error("Selecione ao menos um produto ou serviço para vender.")
                st.stop()

            # Inserir venda
            cursor.execute(
                "INSERT INTO vendas (cliente_id, data, forma_pagamento, total) VALUES (?, ?, ?, ?)",
                (cliente[0], str(date.today()), forma_pagamento, total)
            )
            venda_id = cursor.lastrowid

            # Inserir itens da venda
            if quantidade_prod > 0:
                cursor.execute(
                    "INSERT INTO vendas_itens (venda_id, tipo, nome, quantidade, preco) VALUES (?, ?, ?, ?, ?)",
                    (venda_id, "Produto", produto_selecionado, quantidade_prod, valor_prod)
                )
                # Atualizar estoque
                novo_estoque = estoque_atual - quantidade_prod
                cursor.execute("UPDATE produtos SET estoque = ? WHERE nome = ?", (novo_estoque, produto_selecionado))

            if quantidade_serv > 0:
                cursor.execute(
                    "INSERT INTO vendas_itens (venda_id, tipo, nome, quantidade, preco) VALUES (?, ?, ?, ?, ?)",
                    (venda_id, "Serviço", servico_selecionado, quantidade_serv, valor_serv)
                )

            conn.commit()
            st.success(f"Venda finalizada. Total: R$ {total:.2f}")
# 1. Atualizar a tabela produtos para incluir preco_custo (se ainda não existir)
cursor.execute("PRAGMA table_info(produtos)")
colunas = [col[1] for col in cursor.fetchall()]
if "preco_custo" not in colunas:
    cursor.execute("ALTER TABLE produtos ADD COLUMN preco_custo REAL DEFAULT 0.0")
    conn.commit()

elif menu == "Produtos":
    st.title("📦 Produtos")

    # Formulário para cadastrar novo produto (com preco de custo)
    with st.form("form_produtos"):
        nome = st.text_input("Nome do produto")
        estoque = st.number_input("Estoque", min_value=0, step=1)
        preco_custo = st.number_input("Preço de custo R$", min_value=0.0, step=0.01, format="%.2f")
        valor = st.number_input("Valor de venda R$", min_value=0.0, step=0.01, format="%.2f")

        if st.form_submit_button("Cadastrar Produto"):
            if not nome.strip():
                st.error("O nome do produto é obrigatório.")
            else:
                cursor.execute(
                    "INSERT INTO produtos (nome, estoque, preco_custo, valor) VALUES (?, ?, ?, ?)",
                    (nome, estoque, preco_custo, valor)
                )
                conn.commit()
                st.success("✅ Produto cadastrado com sucesso.")

    st.markdown("---")
    st.markdown("### 📋 Estoque de Produtos - Editar Produtos")

    # Listar produtos e permitir editar
    produtos = cursor.execute("SELECT id, nome, estoque, preco_custo, valor FROM produtos").fetchall()

    if produtos:
        for p in produtos:
            with st.expander(f"Produto: {p[1]} (ID: {p[0]})"):
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    nome_edit = st.text_input("Nome", value=p[1], key=f"nome_{p[0]}")
                with col2:
                    estoque_edit = st.number_input("Estoque", min_value=0, step=1, value=p[2], key=f"estoque_{p[0]}")
                with col3:
                    preco_custo_edit = st.number_input("Preço de custo R$", min_value=0.0, step=0.01, format="%.2f", value=p[3], key=f"custo_{p[0]}")
                with col4:
                    valor_edit = st.number_input("Valor de venda R$", min_value=0.0, step=0.01, format="%.2f", value=p[4], key=f"valor_{p[0]}")

                if st.button("Salvar Alterações", key=f"salvar_{p[0]}"):
                    if not nome_edit.strip():
                        st.error("O nome do produto não pode ficar vazio.")
                    else:
                        cursor.execute(
                            "UPDATE produtos SET nome=?, estoque=?, preco_custo=?, valor=? WHERE id=?",
                            (nome_edit, estoque_edit, preco_custo_edit, valor_edit, p[0])
                        )
                        conn.commit()
                        st.success(f"Produto '{nome_edit}' atualizado com sucesso!")
                        st.experimental_rerun()
    else:
        st.info("Nenhum produto cadastrado ainda.")
# Criação da tabela empresa (uma única empresa operando o sistema)
cursor.execute("""
# Criação da tabela empresa - isso deve estar no início do arquivo
cursor.execute("""
CREATE TABLE IF NOT EXISTS empresa (
    id INTEGER PRIMARY KEY,
    nome TEXT,
    cnpj TEXT,
    telefone TEXT,
    endereco TEXT,
    email TEXT
)
""")
conn.commit()

# ... (aqui vem o restante do seu código anterior)

elif menu == "Cadastro Empresa":
    st.title("🏢 Cadastro da Empresa")

    empresa = cursor.execute("SELECT * FROM empresa WHERE id = 1").fetchone()

    with st.form("form_empresa"):
        col1, col2 = st.columns(2)
        with col1:
            nome = st.text_input("Nome da empresa", value=empresa[1] if empresa else "")
            cnpj = st.text_input("CNPJ", value=empresa[2] if empresa else "")
            telefone = st.text_input("Telefone", value=empresa[3] if empresa else "")
        with col2:
            endereco = st.text_input("Endereço", value=empresa[4] if empresa else "")
            email = st.text_input("E-mail", value=empresa[5] if empresa else "")

        if st.form_submit_button("Salvar dados"):
            if empresa:
                cursor.execute("""
                    UPDATE empresa
                    SET nome=?, cnpj=?, telefone=?, endereco=?, email=?
                    WHERE id = 1
                """, (nome, cnpj, telefone, endereco, email))
            else:
                cursor.execute("""
                    INSERT INTO empresa (id, nome, cnpj, telefone, endereco, email)
                    VALUES (1, ?, ?, ?, ?, ?)
                """, (nome, cnpj, telefone, endereco, email))
            conn.commit()
            st.success("✅ Dados da empresa salvos com sucesso!")


elif menu == "Vendas":
    st.title("💳 Vendas")

    clientes = cursor.execute("SELECT id, nome FROM clientes").fetchall()
    servicos = cursor.execute("SELECT nome, valor FROM servicos").fetchall()
    produtos = cursor.execute("SELECT nome, valor, estoque FROM produtos").fetchall()

    if not clientes:
        st.warning("⚠️ Cadastre clientes antes de realizar vendas.")
        st.stop()

    with st.form("form_venda"):
        cliente = st.selectbox("Cliente", clientes, format_func=lambda x: x[1])
        forma_pagamento = st.selectbox("Forma de pagamento", ["Dinheiro", "Cartão", "Pix"])

        # Produtos
        opcoes_produto = ["Nenhum"] + [p[0] for p in produtos]
        produto_selecionado = st.selectbox("Produto", opcoes_produto)
        quantidade_prod = 0
        if produto_selecionado != "Nenhum":
            quantidade_prod = st.number_input("Quantidade do produto", min_value=1, step=1, key="qtd_produto")

        # Serviços
        opcoes_servico = ["Nenhum"] + [s[0] for s in servicos]
        servico_selecionado = st.selectbox("Serviço", opcoes_servico)
        quantidade_serv = 0
        if servico_selecionado != "Nenhum":
            quantidade_serv = st.number_input("Quantidade do serviço", min_value=1, step=1, key="qtd_servico")

        if st.form_submit_button("Finalizar Venda"):
            total = 0.0
            venda_itens = []

            # Processar produto
            if produto_selecionado != "Nenhum":
                idx_prod = [p[0] for p in produtos].index(produto_selecionado)
                estoque_atual = produtos[idx_prod][2]
                valor_prod = produtos[idx_prod][1]

                if estoque_atual < quantidade_prod:
                    st.error("Estoque insuficiente para o produto selecionado.")
                    st.stop()

                total += valor_prod * quantidade_prod
                venda_itens.append(("Produto", produto_selecionado, quantidade_prod, valor_prod))

            # Processar serviço
            if servico_selecionado != "Nenhum":
                idx_serv = [s[0] for s in servicos].index(servico_selecionado)
                valor_serv = servicos[idx_serv][1]
                total += valor_serv * quantidade_serv
                venda_itens.append(("Serviço", servico_selecionado, quantidade_serv, valor_serv))

            if len(venda_itens) == 0:
                st.error("Selecione pelo menos um produto ou serviço para realizar a venda.")
                st.stop()

            # Inserir venda
            cursor.execute(
                "INSERT INTO vendas (cliente_id, data, forma_pagamento, total) VALUES (?, ?, ?, ?)",
                (cliente[0], str(date.today()), forma_pagamento, total)
            )
            venda_id = cursor.lastrowid

            # Inserir itens da venda
            for tipo, nome, qtd, preco in venda_itens:
                cursor.execute(
                    "INSERT INTO vendas_itens (venda_id, tipo, nome, quantidade, preco) VALUES (?, ?, ?, ?, ?)",
                    (venda_id, tipo, nome, qtd, preco)
                )
                # Atualizar estoque se for produto
                if tipo == "Produto":
                    cursor.execute(
                        "UPDATE produtos SET estoque = estoque - ? WHERE nome = ?",
                        (qtd, nome)
                    )

            conn.commit()
            st.success(f"Venda finalizada com sucesso! Total: R$ {total:.2f}")

            # Gerar comprovante e exibir
            arquivo_comprovante, texto_comprovante = gerar_comprovante_venda(venda_id)
            st.text_area("Comprovante de Venda", texto_comprovante, height=300)
            with open(arquivo_comprovante, "rb") as f:
                st.download_button(
                    label="Download do Comprovante (.txt)",
                    data=f,
                    file_name=f"comprovante_venda_{venda_id}.txt",
                    mime="text/plain"
                )
elif menu == "Dashboard":
    st.title("📊 Dashboard da Empresa")

    # Buscar dados empresa para mostrar nome e info principal
    empresa = cursor.execute("SELECT nome FROM empresa WHERE id=1").fetchone()
    if empresa:
        st.subheader(f"Empresa: {empresa[0]}")
    else:
        st.warning("Nenhuma empresa cadastrada. Cadastre no menu 'Cadastro Empresa'.")

    total_clientes = cursor.execute("SELECT COUNT(*) FROM clientes").fetchone()[0]
    total_vendas = cursor.execute("SELECT COUNT(*) FROM vendas").fetchone()[0]
    vendas_canceladas = cursor.execute("SELECT COUNT(*) FROM vendas WHERE status = 'Cancelada'").fetchone()
    vendas_canceladas = vendas_canceladas[0] if vendas_canceladas else 0
    agend_cancelados = cursor.execute("SELECT COUNT(*) FROM agendamentos WHERE status = 'Cancelado'").fetchone()[0]

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Clientes Cadastrados", total_clientes)
    col2.metric("Vendas Realizadas", total_vendas)
    col3.metric("Vendas Canceladas", vendas_canceladas)
    col4.metric("Agendamentos Cancelados", agend_cancelados)
elif menu == "Dashboard":
    st.title("📊 Dashboard da Empresa")

    # Buscar dados empresa para mostrar nome e info principal
    empresa = cursor.execute("SELECT nome FROM empresa WHERE id=1").fetchone()
    if empresa:
        st.subheader(f"Empresa: {empresa[0]}")
    else:
        st.warning("Nenhuma empresa cadastrada. Cadastre no menu 'Cadastro Empresa'.")

    total_clientes = cursor.execute("SELECT COUNT(*) FROM clientes").fetchone()[0]
    total_vendas = cursor.execute("SELECT COUNT(*) FROM vendas").fetchone()[0]
    vendas_canceladas = cursor.execute("SELECT COUNT(*) FROM vendas WHERE status = 'Cancelada'").fetchone()
    vendas_canceladas = vendas_canceladas[0] if vendas_canceladas else 0
    agend_cancelados = cursor.execute("SELECT COUNT(*) FROM agendamentos WHERE status = 'Cancelado'").fetchone()[0]

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Clientes Cadastrados", total_clientes)
    col2.metric("Vendas Realizadas", total_vendas)
    col3.metric("Vendas Canceladas", vendas_canceladas)
    col4.metric("Agendamentos Cancelados", agend_cancelados)
elif menu == "Cadastro Empresa":
    st.title("🏢 Cadastro da Empresa")

    # Tentar carregar dados existentes
    empresa = cursor.execute("SELECT id, nome, cnpj, endereco, telefone, email FROM empresa WHERE id = 1").fetchone()

    nome = ""
    cnpj = ""
    endereco = ""
    telefone = ""
    email = ""

    if empresa:
        nome, cnpj, endereco, telefone, email = empresa[1], empresa[2], empresa[3], empresa[4], empresa[5]

    with st.form("form_empresa"):
        nome_input = st.text_input("Nome da Empresa", value=nome)
        cnpj_input = st.text_input("CNPJ", value=cnpj)
        endereco_input = st.text_input("Endereço", value=endereco)
        telefone_input = st.text_input("Telefone", value=telefone)
        email_input = st.text_input("E-mail", value=email)

        if st.form_submit_button("Salvar Dados"):
            if not nome_input.strip():
                st.error("O nome da empresa é obrigatório.")
            else:
                if empresa:
                    # Atualizar
                    cursor.execute("""
                        UPDATE empresa SET nome=?, cnpj=?, endereco=?, telefone=?, email=? WHERE id=1
                    """, (nome_input, cnpj_input, endereco_input, telefone_input, email_input))
                else:
                    # Inserir
                    cursor.execute("""
                        INSERT INTO empresa (id, nome, cnpj, endereco, telefone, email) VALUES (1, ?, ?, ?, ?, ?)
                    """, (nome_input, cnpj_input, endereco_input, telefone_input, email_input))
                conn.commit()
                st.success("Dados da empresa salvos com sucesso!")
def gerar_comprovante_venda(venda_id):
    venda = cursor.execute("SELECT v.data, v.forma_pagamento, v.total, c.nome FROM vendas v LEFT JOIN clientes c ON v.cliente_id = c.id WHERE v.id = ?", (venda_id,)).fetchone()
    itens = cursor.execute("SELECT tipo, nome, quantidade, preco FROM vendas_itens WHERE venda_id = ?", (venda_id,)).fetchall()
    empresa = cursor.execute("SELECT nome, cnpj, endereco, telefone, email FROM empresa WHERE id = 1").fetchone()

    texto = []
    texto.append("========== COMPROVANTE DE VENDA ==========")
    texto.append(f"Data: {venda[0]}   -   Cliente: {venda[3]}")
    texto.append(f"Forma de Pagamento: {venda[1]}")
    texto.append("------------------------------------------")
    texto.append("Tipo     | Nome                | Qtd | Valor")
    texto.append("------------------------------------------")
    for item in itens:
        tipo, nome, qtd, preco = item
        total_item = qtd * preco
        texto.append(f"{tipo:<8} {nome:<18} {qtd:>3} x R$ {preco:.2f} = R$ {total_item:.2f}")
    texto.append("------------------------------------------")
    texto.append(f"TOTAL GERAL: R$ {venda[2]:.2f}")
    texto.append("------------------------------------------")
    if empresa:
        texto.append("")
        texto.append(f"{empresa[0]} - CNPJ: {empresa[1]}")
        texto.append(f"Endereço: {empresa[2]}")
        texto.append(f"Telefone: {empresa[3]} | Email: {empresa[4]}")
    texto.append("==========================================")

    nome_arquivo = f"comprovante_venda_{venda_id}.txt"
    caminho = os.path.join("comprovantes", nome_arquivo)
    if not os.path.exists("comprovantes"):
        os.makedirs("comprovantes")

    with open(caminho, "w", encoding="utf-8") as f:
        f.write("\n".join(texto))

    return caminho, "\n".join(texto)
    texto.append("Tipo     | Nome                | Qtd | Preço")
    texto.append("------------------------------------------")
    for item in itens:
        tipo, nome, qtd, preco = item
        texto.append(f"{tipo:<9}{nome:<20} {qtd:>3}  R$ {preco:.2f}")
    texto.append("------------------------------------------")
    texto.append(f"TOTAL: R$ {venda[2]:.2f}")
    texto.append("")

    if empresa:
        texto.append("------ Dados da Empresa ------")
        texto.append(f"{empresa[0]}")  # nome
        if empresa[1]: texto.append(f"CNPJ: {empresa[1]}")
        if empresa[2]: texto.append(f"Endereço: {empresa[2]}")
        if empresa[3]: texto.append(f"Telefone: {empresa[3]}")
        if empresa[4]: texto.append(f"E-mail: {empresa[4]}")
    texto.append("==========================================")

    nome_arquivo = f"comprovante_venda_{venda_id}.txt"
    caminho = os.path.join("comprovantes", nome_arquivo)

    if not os.path.exists("comprovantes"):
        os.makedirs("comprovantes")

    with open(caminho, "w", encoding="utf-8") as f:
        f.write("\n".join(texto))

    return caminho, "\n".join(texto)
elif menu == "Produtos":
    st.title("📦 Produtos")

    with st.form("form_produtos"):
        nome = st.text_input("Nome do produto")
        estoque = st.number_input("Estoque", min_value=0, step=1)
        preco_custo = st.number_input("Preço de Custo R$", min_value=0.0, step=0.1, format="%.2f")
        valor = st.number_input("Valor de Venda R$", min_value=0.0, step=0.1, format="%.2f")

        if st.form_submit_button("Cadastrar Produto"):
            if not nome.strip():
                st.error("O nome do produto é obrigatório.")
            else:
                cursor.execute(
                    "INSERT INTO produtos (nome, estoque, preco_custo, valor) VALUES (?, ?, ?, ?)",
                    (nome, estoque, preco_custo, valor)
                )
                conn.commit()
                st.success("✅ Produto cadastrado com sucesso.")

    st.markdown("### 📋 Estoque de Produtos")
    produtos = cursor.execute("SELECT id, nome, estoque, preco_custo, valor FROM produtos").fetchall()
    if produtos:
        for p in produtos:
            with st.expander(f"{p[1]} — Estoque: {p[2]} | R$ {p[4]:.2f}"):
                novo_nome = st.text_input("Editar Nome", value=p[1], key=f"nome_{p[0]}")
                novo_estoque = st.number_input("Editar Estoque", value=p[2], step=1, key=f"estoque_{p[0]}")
                novo_custo = st.number_input("Editar Preço de Custo", value=p[3] or 0.0, step=0.1, format="%.2f", key=f"custo_{p[0]}")
                novo_valor = st.number_input("Editar Valor de Venda", value=p[4], step=0.1, format="%.2f", key=f"valor_{p[0]}")

                if st.button("Salvar Alterações", key=f"salvar_{p[0]}"):
                    cursor.execute("""
                        UPDATE produtos
                        SET nome = ?, estoque = ?, preco_custo = ?, valor = ?
                        WHERE id = ?
                    """, (novo_nome, novo_estoque, novo_custo, novo_valor, p[0]))
                    conn.commit()
                    st.success("Alterações salvas com sucesso.")
                    st.experimental_rerun()
    else:
        st.info("Nenhum produto cadastrado ainda.")
elif menu == "Relatórios":
    st.title("📊 Relatórios")

    empresa = cursor.execute("SELECT nome, cnpj, endereco, telefone, email FROM empresa WHERE id = 1").fetchone()
    if empresa:
        st.markdown(f"### 🏢 {empresa[0]}")
        if empresa[1]: st.markdown(f"**CNPJ:** {empresa[1]}")
        if empresa[2]: st.markdown(f"**Endereço:** {empresa[2]}")
        if empresa[3]: st.markdown(f"**Telefone:** {empresa[3]}")
        if empresa[4]: st.markdown(f"**E-mail:** {empresa[4]}")
        st.markdown("---")

    tipo_rel = st.selectbox("Tipo de relatório", ["Vendas", "Despesas"])
    data_ini = st.date_input("Data inicial", value=date(2023, 1, 1))
    data_fim = st.date_input("Data final", value=date.today())

    if data_ini > data_fim:
        st.error("Data inicial não pode ser maior que a final.")
        st.stop()

    if tipo_rel == "Vendas":
        query = """
            SELECT v.data, v.forma_pagamento, v.total, c.nome
            FROM vendas v
            LEFT JOIN clientes c ON v.cliente_id = c.id
            WHERE date(v.data) BETWEEN ? AND ?
        """
        df = pd.read_sql_query(query, conn, params=(str(data_ini), str(data_fim)))

        if df.empty:
            st.warning("Nenhum dado de vendas encontrado no período.")
        else:
            st.markdown("### 📄 Relatório de Vendas")
            st.dataframe(df)
            total = df["total"].sum()
            st.success(f"Total vendido no período: R$ {total:.2f}")
            fig = px.bar(df.groupby('data').sum().reset_index(), x='data', y='total', title="Total de Vendas por Dia")
            st.plotly_chart(fig)

    else:  # Despesas
        query = """
            SELECT descricao, valor, data
            FROM despesas
            WHERE date(data) BETWEEN ? AND ?
        """
        df = pd.read_sql_query(query, conn, params=(str(data_ini), str(data_fim)))

        if df.empty:
            st.warning("Nenhum dado de despesas encontrado no período.")
        else:
            st.markdown("### 📄 Relatório de Despesas")
            st.dataframe(df)
            total = df["valor"].sum()
            st.error(f"Total de despesas no período: R$ {total:.2f}")
            fig = px.bar(df.groupby('data').sum().reset_index(), x='data', y='valor', title="Despesas por Dia")
            st.plotly_chart(fig)
