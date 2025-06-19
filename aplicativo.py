import streamlit as st
import sqlite3
from datetime import datetime, date
import base64
import io
import pandas as pd
import plotly.express as px
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# --- Banco ---
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
        descricao TEXT,
        valor REAL,
        data TEXT,
        quantidade INTEGER,
        observacao TEXT
    )''')

    conn.commit()

def criar_usuario_padrao():
    cursor.execute("SELECT * FROM usuarios WHERE usuario = 'admin'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO usuarios (usuario, senha) VALUES (?, ?)", ('admin', '1234'))
        conn.commit()

def verificar_login(usuario, senha):
    cursor.execute("SELECT senha FROM usuarios WHERE usuario = ?", (usuario,))
    res = cursor.fetchone()
    return res is not None and res[0] == senha

# Criar tabelas e usuário padrão
criar_tabelas()
criar_usuario_padrao()

# --- Funções CRUD ---
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

# --- Páginas ---

def pagina_login():
    st.title("Login - Sistema Estúdio de Beleza")
    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if verificar_login(usuario, senha):
            st.session_state["login"] = True
            st.session_state["pagina"] = "Dashboard"
            st.experimental_rerun()
        else:
            st.error("Usuário ou senha incorretos")

def pagina_dashboard():
    st.title("Dashboard")
    st.write("Resumo rápido do sistema")

    cursor.execute("SELECT COUNT(*) FROM clientes WHERE status = 'ativo'")
    total_clientes = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM agendamentos WHERE status = 'ativo'")
    total_agendamentos = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM vendas WHERE status = 'ativo'")
    total_vendas = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM despesas")
    total_despesas = cursor.fetchone()[0]

    st.metric("Clientes ativos", total_clientes)
    st.metric("Agendamentos ativos", total_agendamentos)
    st.metric("Vendas registradas", total_vendas)
    st.metric("Despesas registradas", total_despesas)

def pagina_clientes():
    st.title("Clientes")
    with st.expander("Cadastrar Novo Cliente"):
        with st.form("form_cliente", clear_on_submit=True):
            nome = st.text_input("Nome", max_chars=100)
            telefone = st.text_input("Telefone")
            email = st.text_input("Email")
            anamnese = st.text_area("Anamnese")
            bebida = st.text_input("Bebida Preferida")
            gosto = st.text_input("Gosto Musical")
            assinatura = st.text_area("Assinatura")
            foto = st.file_uploader("Foto do Cliente", type=["png", "jpg", "jpeg"])

            assinatura_b64 = base64.b64encode(assinatura.encode()).decode() if assinatura else None
            foto_bytes = foto.read() if foto else None

            submitted = st.form_submit_button("Salvar Cliente")
            if submitted:
                if not nome.strip():
                    st.error("Nome é obrigatório")
                else:
                    salvar_cliente(nome, telefone, email, anamnese, bebida, gosto, assinatura_b64, foto_bytes)
                    st.success(f"Cliente '{nome}' salvo com sucesso!")
                    st.experimental_rerun()

    st.subheader("Clientes Ativos")
    clientes = carregar_clientes(ativos=True)
    for cid, nome, telefone in clientes:
        col1, col2, col3 = st.columns([5,3,2])
        with col1:
            st.write(nome)
        with col2:
            st.write(telefone)
        with col3:
            if st.button(f"Cancelar {cid}"):
                cancelar_cliente(cid)
                st.success("Cliente cancelado")
                st.experimental_rerun()
                def salvar_servico(nome, descricao, duracao, valor):
    cursor.execute("INSERT INTO servicos (nome, descricao, duracao, valor) VALUES (?, ?, ?, ?)", (nome, descricao, duracao, valor))
    conn.commit()

def carregar_servicos():
    cursor.execute("SELECT id, nome, descricao, duracao, valor FROM servicos")
    return cursor.fetchall()

def salvar_produto(nome, descricao, preco_custo, preco_venda, quantidade):
    cursor.execute("INSERT INTO produtos (nome, descricao, preco_custo, preco_venda, quantidade) VALUES (?, ?, ?, ?, ?)", (nome, descricao, preco_custo, preco_venda, quantidade))
    conn.commit()

def carregar_produtos():
    cursor.execute("SELECT id, nome, descricao, preco_custo, preco_venda, quantidade FROM produtos")
    return cursor.fetchall()

def pagina_servicos():
    st.title("Serviços")
    with st.expander("Cadastrar Novo Serviço"):
        with st.form("form_servico", clear_on_submit=True):
            nome = st.text_input("Nome do Serviço")
            descricao = st.text_area("Descrição")
            duracao = st.number_input("Duração (minutos)", min_value=1, step=1)
            valor = st.number_input("Valor R$", min_value=0.0, format="%.2f")
            submitted = st.form_submit_button("Salvar Serviço")
            if submitted:
                if not nome.strip():
                    st.error("Nome é obrigatório")
                else:
                    salvar_servico(nome, descricao, duracao, valor)
                    st.success(f"Serviço '{nome}' salvo!")
                    st.experimental_rerun()

    st.subheader("Serviços Cadastrados")
    servicos = carregar_servicos()
    for s in servicos:
        col1, col2, col3, col4 = st.columns([3,5,2,2])
        with col1:
            st.write(s[1])
        with col2:
            st.write(s[2])
        with col3:
            st.write(f"{s[3]} min")
        with col4:
            st.write(f"R$ {s[4]:.2f}")

def pagina_produtos():
    st.title("Produtos")
    with st.expander("Cadastrar Novo Produto"):
        with st.form("form_produto", clear_on_submit=True):
            nome = st.text_input("Nome do Produto")
            descricao = st.text_area("Descrição")
            preco_custo = st.number_input("Preço de Custo R$", min_value=0.0, format="%.2f")
            preco_venda = st.number_input("Preço de Venda R$", min_value=0.0, format="%.2f")
            quantidade = st.number_input("Quantidade em Estoque", min_value=0, step=1)
            submitted = st.form_submit_button("Salvar Produto")
            if submitted:
                if not nome.strip():
                    st.error("Nome é obrigatório")
                else:
                    salvar_produto(nome, descricao, preco_custo, preco_venda, quantidade)
                    st.success(f"Produto '{nome}' salvo!")
                    st.experimental_rerun()

    st.subheader("Produtos Cadastrados")
    produtos = carregar_produtos()
    for p in produtos:
        col1, col2, col3, col4, col5, col6 = st.columns([3,5,2,2,2,1])
        with col1:
            st.write(p[1])
        with col2:
            st.write(p[2])
        with col3:
            st.write(f"R$ {p[3]:.2f}")
        with col4:
            st.write(f"R$ {p[4]:.2f}")
        with col5:
            st.write(p[5])
        with col6:
            pass  # Espaço para ações futuras, tipo editar/excluir

# ---

# No main() você deve adicionar essas páginas no menu, por exemplo:

def main():
    st.set_page_config(page_title="Sistema Estúdio de Beleza", layout="wide")

    if "login" not in st.session_state:
        st.session_state["login"] = False
    if "pagina" not in st.session_state:
        st.session_state["pagina"] = "Login"

    if not st.session_state["login"]:
        pagina_login()
    else:
        col1, col2 = st.columns([1, 7])
        with col1:
            st.sidebar.title("Menu")
            pagina = st.sidebar.radio("Navegação", [
                "Dashboard",
                "Clientes",
                "Serviços",
                "Produtos",
                # outras páginas que iremos enviar depois...
            ])
            st.session_state["pagina"] = pagina
        with col2:
            pagina_atual = st.session_state["pagina"]
            if pagina_atual == "Dashboard":
                pagina_dashboard()
            elif pagina_atual == "Clientes":
                pagina_clientes()
            elif pagina_atual == "Serviços":
                pagina_servicos()
            elif pagina_atual == "Produtos":
                pagina_produtos()
            else:
                st.write("Página não encontrada")

if __name__ == "__main__":
    main()
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
        SELECT a.id, c.nome, s.nome, a.data_hora 
        FROM agendamentos a
        JOIN clientes c ON a.cliente_id = c.id
        JOIN servicos s ON a.servico_id = s.id
        WHERE a.status = ?
        ORDER BY a.data_hora
    ''', (status,))
    return cursor.fetchall()

def cancelar_agendamento(agendamento_id):
    cursor.execute("UPDATE agendamentos SET status = 'cancelado' WHERE id = ?", (agendamento_id,))
    conn.commit()

def pagina_agendamentos():
    st.title("Agendamentos")
    with st.expander("Novo Agendamento"):
        with st.form("form_agendamento", clear_on_submit=True):
            clientes = carregar_clientes(ativos=True)
            clientes_dict = {f"{nome} (ID:{cid})": cid for cid, nome, _ in clientes}
            servicos = carregar_servicos()
            servicos_dict = {f"{nome} (ID:{sid})": sid for sid, nome, *_ in servicos}

            cliente_selecionado = st.selectbox("Cliente", list(clientes_dict.keys()))
            servico_selecionado = st.selectbox("Serviço", list(servicos_dict.keys()))
            data_hora = st.datetime_input("Data e Hora do Agendamento", value=datetime.now())

            submitted = st.form_submit_button("Salvar Agendamento")
            if submitted:
                if not cliente_selecionado or not servico_selecionado:
                    st.error("Cliente e Serviço são obrigatórios")
                else:
                    salvar_agendamento(clientes_dict[cliente_selecionado], servicos_dict[servico_selecionado], data_hora.strftime("%Y-%m-%d %H:%M:%S"))
                    st.success("Agendamento salvo!")
                    st.experimental_rerun()

    st.subheader("Agendamentos Ativos")
    agendamentos = carregar_agendamentos(ativos=True)
    for aid, nome_cliente, nome_servico, data_h in agendamentos:
        col1, col2, col3, col4 = st.columns([4,4,3,1])
        with col1:
            st.write(nome_cliente)
        with col2:
            st.write(nome_servico)
        with col3:
            st.write(data_h)
        with col4:
            if st.button(f"Cancelar {aid}"):
                cancelar_agendamento(aid)
                st.success("Agendamento cancelado")
                st.experimental_rerun()
def salvar_venda(cliente_id, servico_id, produto_id, quantidade, valor, forma_pagamento):
    data_atual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('''
        INSERT INTO vendas (cliente_id, servico_id, produto_id, quantidade, valor, forma_pagamento, data)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (cliente_id, servico_id, produto_id, quantidade, valor, forma_pagamento, data_atual))
    conn.commit()

def carregar_vendas():
    cursor.execute('''
        SELECT v.id, c.nome, s.nome, p.nome, v.quantidade, v.valor, v.forma_pagamento, v.data
        FROM vendas v
        LEFT JOIN clientes c ON v.cliente_id = c.id
        LEFT JOIN servicos s ON v.servico_id = s.id
        LEFT JOIN produtos p ON v.produto_id = p.id
        ORDER BY v.data DESC
    ''')
    return cursor.fetchall()

def pagina_vendas():
    st.title("Vendas")

    clientes = carregar_clientes(ativos=True)
    clientes_dict = {f"{nome} (ID:{cid})": cid for cid, nome, _ in clientes}

    servicos = carregar_servicos()
    servicos_dict = {f"{nome} (ID:{sid})": sid for sid, nome, *_ in servicos}

    produtos = carregar_produtos()
    produtos_dict = {f"{nome} (ID:{pid}) - R$ {preco_venda:.2f}": (pid, preco_venda) for pid, nome, _, _, preco_venda, _ in produtos}

    with st.form("form_venda", clear_on_submit=True):
        cliente_selecionado = st.selectbox("Cliente", list(clientes_dict.keys()))
        servico_selecionado = st.selectbox("Serviço", ["Nenhum"] + list(servicos_dict.keys()))
        produto_selecionado = st.selectbox("Produto", ["Nenhum"] + list(produtos_dict.keys()))
        quantidade = st.number_input("Quantidade (para produto)", min_value=1, step=1, value=1)

        formas_pagamento = ["Dinheiro", "Cartão Crédito", "Cartão Débito", "Pix"]
        forma_pagamento = st.selectbox("Forma de Pagamento", formas_pagamento)

        submitted = st.form_submit_button("Finalizar Venda")
        if submitted:
            if not cliente_selecionado:
                st.error("Selecione um cliente")
            else:
                cid = clientes_dict[cliente_selecionado]
                sid = servicos_dict.get(servico_selecionado) if servico_selecionado != "Nenhum" else None
                pid, preco_unitario = produtos_dict.get(produto_selecionado, (None, 0)) if produto_selecionado != "Nenhum" else (None, 0)
                qtd = quantidade if pid else 0
                valor_total = 0.0

                if sid:
                    # Pega valor do serviço
                    cursor.execute("SELECT valor FROM servicos WHERE id = ?", (sid,))
                    valor_servico = cursor.fetchone()
                    valor_servico = valor_servico[0] if valor_servico else 0
                    valor_total += valor_servico

                if pid:
                    valor_total += preco_unitario * qtd

                if valor_total <= 0:
                    st.error("Selecione um serviço ou produto válido para venda")
                else:
                    salvar_venda(cid, sid, pid, qtd, valor_total, forma_pagamento)
                    st.success(f"Venda registrada! Total: R$ {valor_total:.2f}")
                    st.experimental_rerun()

    st.subheader("Últimas Vendas")
    vendas = carregar_vendas()
    for vid, nome_cliente, nome_servico, nome_produto, qtd, valor, forma, data_venda in vendas[:10]:
        col1, col2, col3, col4, col5, col6 = st.columns([3,3,3,2,2,3])
        with col1:
            st.write(nome_cliente)
        with col2:
            st.write(nome_servico if nome_servico else "-")
        with col3:
            st.write(nome_produto if nome_produto else "-")
        with col4:
            st.write(qtd if qtd else "-")
        with col5:
            st.write(f"R$ {valor:.2f}")
        with col6:
            st.write(f"{forma} - {data_venda}")
def salvar_despesa(descricao, valor, data, quantidade, observacao):
    cursor.execute('''
        INSERT INTO despesas (descricao, valor, data, quantidade, observacao)
        VALUES (?, ?, ?, ?, ?)
    ''', (descricao, valor, data, quantidade, observacao))
    conn.commit()

def carregar_despesas(data_inicio=None, data_fim=None):
    query = "SELECT id, descricao, valor, data, quantidade, observacao FROM despesas"
    params = []
    if data_inicio and data_fim:
        query += " WHERE date(data) BETWEEN ? AND ?"
        params.extend([data_inicio, data_fim])
    query += " ORDER BY data DESC"
    cursor.execute(query, params)
    return cursor.fetchall()

def pagina_despesas():
    st.title("Despesas")
    with st.expander("Nova Despesa"):
        with st.form("form_despesa", clear_on_submit=True):
            descricao = st.text_input("Descrição")
            valor = st.number_input("Valor", min_value=0.0, format="%.2f")
            data = st.date_input("Data", value=date.today())
            quantidade = st.number_input("Quantidade", min_value=1, step=1)
            observacao = st.text_area("Observação")
            submitted = st.form_submit_button("Salvar")
            if submitted:
                if not descricao.strip():
                    st.error("Descrição é obrigatória")
                else:
                    salvar_despesa(descricao, valor, data.strftime("%Y-%m-%d"), quantidade, observacao)
                    st.success("Despesa registrada com sucesso!")
                    st.experimental_rerun()

    st.subheader("Despesas Recentes")
    despesas = carregar_despesas()
    for d in despesas:
        st.write(f"{d[1]} - R$ {d[2]:.2f} - Data: {d[3]} - Qtde: {d[4]} - Obs: {d[5]}")
import plotly.express as px
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io
import pandas as pd

def gerar_pdf_vendas(data_inicio=None, data_fim=None):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    largura, altura = letter

    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, altura - 50, "Relatório de Vendas")

    query = '''
        SELECT v.id, c.nome, s.nome, p.nome, v.quantidade, v.valor, v.forma_pagamento, v.data
        FROM vendas v
        LEFT JOIN clientes c ON v.cliente_id = c.id
        LEFT JOIN servicos s ON v.servico_id = s.id
        LEFT JOIN produtos p ON v.produto_id = p.id
        ORDER BY v.data DESC
    '''
    params = []
    if data_inicio and data_fim:
        query += " WHERE date(v.data) BETWEEN ? AND ?"
        params.extend([data_inicio, data_fim])
    cursor.execute(query, params)
    vendas = cursor.fetchall()

    y = altura - 80
    for v in vendas:
        texto = f"ID {v[0]} - Cliente: {v[1]} - Serviço: {v[2]} - Produto: {v[3]} - Qtde: {v[4]} - Valor: R$ {v[5]:.2f} - Pagto: {v[6]} - Data: {v[7]}"
        c.drawString(50, y, texto)
        y -= 15
        if y < 50:
            c.showPage()
            y = altura - 50
    c.save()
    buffer.seek(0)
    return buffer

def gerar_pdf_despesas(data_inicio=None, data_fim=None):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    largura, altura = letter

    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, altura - 50, "Relatório de Despesas")

    despesas = carregar_despesas(data_inicio, data_fim)

    y = altura - 80
    for d in despesas:
        texto = f"ID {d[0]} - {d[1]} - Valor: R$ {d[2]:.2f} - Data: {d[3]} - Qtde: {d[4]} - Obs: {d[5]}"
        c.drawString(50, y, texto)
        y -= 15
        if y < 50:
            c.showPage()
            y = altura - 50
    c.save()
    buffer.seek(0)
    return buffer

def pagina_relatorios():
    st.title("Relatórios")

    st.subheader("Filtros")
    data_inicio = st.date_input("Data Início", value=date.today().replace(day=1))
    data_fim = st.date_input("Data Fim", value=date.today())

    st.markdown("---")

    # Gráfico Vendas
    vendas = carregar_vendas()
    if vendas:
        df_vendas = pd.DataFrame(vendas, columns=["ID", "Cliente", "Serviço", "Produto", "Qtde", "Valor", "Pagamento", "Data"])
        df_vendas['Data'] = pd.to_datetime(df_vendas['Data']).dt.date
        vendas_filtradas = df_vendas[(df_vendas['Data'] >= data_inicio) & (df_vendas['Data'] <= data_fim)]
        vendas_agrupadas = vendas_filtradas.groupby('Data')['Valor'].sum().reset_index()

        fig_vendas = px.bar(vendas_agrupadas, x='Data', y='Valor', title="Vendas por Data", labels={"Valor": "R$"})
        st.plotly_chart(fig_vendas, use_container_width=True)
    else:
        st.info("Sem vendas para exibir")

    # Gráfico Despesas
    despesas = carregar_despesas(data_inicio.strftime("%Y-%m-%d"), data_fim.strftime("%Y-%m-%d"))
    if despesas:
        df_despesas = pd.DataFrame(despesas, columns=["ID", "Descrição", "Valor", "Data", "Quantidade", "Observação"])
        df_despesas['Data'] = pd.to_datetime(df_despesas['Data']).dt.date
        despesas_agrupadas = df_despesas.groupby('Data')['Valor'].sum().reset_index()

        fig_despesas = px.bar(despesas_agrupadas, x='Data', y='Valor', title="Despesas por Data", labels={"Valor": "R$"})
        st.plotly_chart(fig_despesas, use_container_width=True)
    else:
        st.info("Sem despesas para exibir")

    st.markdown("---")
    st.subheader("Exportar PDF")

    if st.button("Exportar Relatório de Vendas PDF"):
        pdf_vendas = gerar_pdf_vendas(data_inicio.strftime("%Y-%m-%d"), data_fim.strftime("%Y-%m-%d"))
        st.download_button("Clique para baixar", data=pdf_vendas, file_name="relatorio_vendas.pdf", mime="application/pdf")

    if st.button("Exportar Relatório de Despesas PDF"):
        pdf_despesas = gerar_pdf_despesas(data_inicio.strftime("%Y-%m-%d"), data_fim.strftime("%Y-%m-%d"))
        st.download_button("Clique para baixar", data=pdf_despesas, file_name="relatorio_despesas.pdf", mime="application/pdf")
def pagina_sair():
    st.session_state["login"] = False
    st.session_state["pagina"] = "Login"
    st.experimental_rerun()
def main():
    st.set_page_config(page_title="Sistema Estúdio de Beleza", layout="wide")

    if "login" not in st.session_state:
        st.session_state["login"] = False
    if "pagina" not in st.session_state:
        st.session_state["pagina"] = "Login"

    if not st.session_state["login"]:
        pagina_login()
    else:
        col1, col2 = st.columns([1, 7])
        with col1:
            st.sidebar.title("Menu")
            pagina = st.sidebar.radio("Navegação", [
                "Dashboard",
                "Clientes",
                "Serviços",
                "Produtos",
                "Agendamentos",
                "Vendas",
                "Despesas",
                "Relatórios",
                "Sair"
            ])
            st.session_state["pagina"] = pagina
        with col2:
            pagina_atual = st.session_state["pagina"]
            if pagina_atual == "Dashboard":
                pagina_dashboard()
            elif pagina_atual == "Clientes":
                pagina_clientes()
            elif pagina_atual == "Serviços":
                pagina_servicos()
            elif pagina_atual == "Produtos":
                pagina_produtos()
            elif pagina_atual == "Agendamentos":
                pagina_agendamentos()
            elif pagina_atual == "Vendas":
                pagina_vendas()
            elif pagina_atual == "Despesas":
                pagina_despesas()
            elif pagina_atual == "Relatórios":
                pagina_relatorios()
            elif pagina_atual == "Sair":
                pagina_sair()
            else:
                st.write("Página não encontrada")

if __name__ == "__main__":
    main()

