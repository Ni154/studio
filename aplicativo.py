# SISTEMA COMPLETO STUDIO DEPILAÇÃO COM MELHORIAS INTEGRADAS
import streamlit as st
import sqlite3
from datetime import datetime, date, time
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

# FUNÇÃO PARA BACKUP
def fazer_backup():
    with open("studio_depilation.db", "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
        href = f'<a href="data:file/db;base64,{b64}" download="backup_studio_depilation.db">📥 Baixar Backup</a>'
        st.markdown(href, unsafe_allow_html=True)

# TABELAS NECESSÁRIAS
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

# USUÁRIO PADRÃO
if not cursor.execute("SELECT * FROM usuarios WHERE usuario='admin'").fetchone():
    cursor.execute("INSERT INTO usuarios (usuario, senha) VALUES ('admin', 'admin')")
    conn.commit()

# CONTINUA NAS PRÓXIMAS PARTES...
# Parte 2 - Login, menu lateral fixo com logo, importação da logo e botão backup

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
        # Exibe logo atual ou placeholder
        if os.path.exists("logo_studio.png"):
            st.image("logo_studio.png", width=150)
        else:
            st.image("https://via.placeholder.com/150x100.png?text=LOGO", width=150)

        # Upload para trocar logo
        st.write("📎 **Importar nova logo:**")
        uploaded_logo = st.file_uploader("Importar Logo", type=["png", "jpg", "jpeg"])
        if uploaded_logo:
            with open("logo_studio.png", "wb") as f:
                f.write(uploaded_logo.read())
            st.success("Logo atualizada!")

        # Menu lateral fixo com botões
        menu = st.radio("Menu", [
            "Início", "Dashboard", "Cadastro Cliente", "Cadastro Empresa", "Cadastro Produtos",
            "Cadastro Serviços", "Agendamento", "Vendas", "Cancelar Vendas", "Relatórios", "Backup", "Sair"
        ], key="menu_radio")

    # Aqui o menu já está definido, então pode usar
    st.title(f"🧭 {menu}")

    # ✅ Corrigido: agora essa verificação só roda quando o menu existe
    if menu == "Início":
        st.subheader("📅 Agendamentos do Dia")
        hoje = date.today().strftime("%d-%m-%Y")
        agendamentos = cursor.execute("""
        SELECT a.id, c.nome, a.data, a.hora, a.servicos, a.status
        FROM agendamentos a
        JOIN clientes c ON a.cliente_id = c.id
        WHERE a.data = ?
        ORDER BY a.hora
        """, (hoje,)).fetchall()

        if agendamentos:
            for ag in agendamentos:
                st.info(f"🕒 {ag[3]} | 👤 {ag[1]} | 💼 Serviços: {ag[4]} | 📌 Status: {ag[5]}")
        else:
            st.warning("Nenhum agendamento para hoje.")

    elif menu == "Backup":
        st.subheader("Backup dos Dados")
        st.write("Clique no botão abaixo para baixar uma cópia do banco de dados SQLite.")
        fazer_backup()

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
    
        # Gráfico de vendas realizadas e canceladas
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
        st.pyplot(fig)
# Parte 4 - Cadastro de Cliente com hora agendada, ficha, assinatura e limpeza de campos

    elif menu == "Cadastro Cliente":
        st.subheader("🧍 Cadastro de Cliente + Ficha de Avaliação")
        with st.form("form_cliente", clear_on_submit=True):
            nome = st.text_input("Nome completo")
            telefone = st.text_input("Telefone")
            # Campo nascimento sem limite, permitindo digitar (usar text_input para datas flexíveis)
            nascimento_str = st.text_input("Data de nascimento (DD-MM-YYYY)", placeholder="ex: 31-12-1980")
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
                # Validação data nascimento
                try:
                    nascimento = datetime.strptime(nascimento_str, "%d-%m-%Y").date()
                except Exception:
                    st.error("Data de nascimento inválida. Use o formato DD-MM-YYYY.")
                    st.stop()
    
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
# Parte 5 - Cadastro de Produtos com limpeza de campos e exclusão

    elif menu == "Cadastro Produtos":
        st.subheader("📦 Cadastro de Produtos")
    
        with st.form("form_produto", clear_on_submit=True):
            nome = st.text_input("Nome do Produto")
            quantidade = st.number_input("Quantidade", min_value=0, step=1)
            preco_custo = st.number_input("Preço de Custo", min_value=0.0, step=0.01, format="%.2f")
            preco_venda = st.number_input("Preço de Venda", min_value=0.0, step=0.01, format="%.2f")
    
            if st.form_submit_button("Adicionar Produto"):
                if not nome:
                    st.error("Nome do produto é obrigatório")
                else:
                    cursor.execute(
                        "INSERT INTO produtos (nome, quantidade, preco_custo, preco_venda) VALUES (?, ?, ?, ?)",
                        (nome, quantidade, preco_custo, preco_venda)
                    )
                    conn.commit()
                    st.success("Produto adicionado com sucesso!")
    
        produtos = cursor.execute("SELECT * FROM produtos").fetchall()
        if produtos:
            st.subheader("Produtos Cadastrados")
            for prod in produtos:
                st.write(f"ID: {prod[0]} | Nome: {prod[1]} | Qtd: {prod[2]} | Custo: R${prod[3]:.2f} | Venda: R${prod[4]:.2f}")
                if st.button(f"Excluir Produto {prod[0]}", key=f"excluir_{prod[0]}"):
                    cursor.execute("DELETE FROM produtos WHERE id=?", (prod[0],))
                    conn.commit()
                    st.experimental_rerun()
        else:
            st.info("Nenhum produto cadastrado ainda.")
# Parte 6 - Cadastro de Serviços com limpeza de campos e listagem

    elif menu == "Cadastro Serviços":
        st.subheader("🚗 Cadastro de Serviços")
    
        with st.form("form_servico", clear_on_submit=True):
            nome = st.text_input("Nome do Serviço")
            unidade = st.text_input("Unidade")
            quantidade = st.number_input("Quantidade", min_value=0, step=1)
            valor = st.number_input("Valor", min_value=0.0, step=0.01, format="%.2f")
    
            if st.form_submit_button("Salvar Serviço"):
                if not nome:
                    st.error("Nome do serviço é obrigatório")
                else:
                    cursor.execute(
                        "INSERT INTO servicos (nome, unidade, quantidade, valor) VALUES (?, ?, ?, ?)",
                        (nome, unidade, quantidade, valor)
                    )
                    conn.commit()
                    st.success("Serviço cadastrado com sucesso!")
    
        servicos = cursor.execute("SELECT * FROM servicos").fetchall()
        if servicos:
            st.subheader("Serviços cadastrados")
            for serv in servicos:
                st.write(f"ID: {serv[0]} | Nome: {serv[1]} | Unidade: {serv[2]} | Quantidade: {serv[3]} | Valor: R$ {serv[4]:.2f}")
        else:
            st.info("Nenhum serviço cadastrado ainda.")
# Parte 7 - Agendamento com múltiplos serviços e status

    elif menu == "Agendamento":
        st.subheader("🗓️ Agendamento")
    
        # Listar agendamentos existentes para visualizar e reagendar
        agendamentos = cursor.execute("""
            SELECT a.id, c.nome, a.data, a.hora, a.servicos, a.status
            FROM agendamentos a
            JOIN clientes c ON a.cliente_id = c.id
            ORDER BY a.data, a.hora
        """).fetchall()
    
        if agendamentos:
            agendamento_str = [f"ID {a[0]} - {a[1]} - {a[2]} {a[3]} - Serviços: {a[4]} - Status: {a[5]}" for a in agendamentos]
            selecao = st.selectbox("Selecione um agendamento para reagendar:", agendamento_str)
    
            idx = agendamento_str.index(selecao)
            ag = agendamentos[idx]
    
            st.write(f"Cliente: {ag[1]}")
            st.write(f"Data atual: {ag[2]} {ag[3]}")
            st.write(f"Serviços: {ag[4]}")
            st.write(f"Status atual: {ag[5]}")
    
            st.markdown("---")
            st.subheader("Reagendar Agendamento")
            nova_data = st.date_input("Nova Data", value=datetime.strptime(ag[2], "%Y-%m-%d").date())
            nova_hora = st.text_input("Nova Hora (ex: 14:30)", value=ag[3])
    
            if st.button("Confirmar Reagendamento"):
                # Atualiza data, hora e status
                status_novo = f"Reagendada para {nova_data.strftime('%d/%m/%Y')} {nova_hora}"
                cursor.execute("""
                    UPDATE agendamentos
                    SET data = ?, hora = ?, status = ?
                    WHERE id = ?
                """, (nova_data.strftime("%Y-%m-%d"), nova_hora, status_novo, ag[0]))
                conn.commit()
                st.success(f"Agendamento reagendado para {nova_data.strftime('%d/%m/%Y')} {nova_hora}!")
                st.experimental_rerun()
    
        else:
            st.info("Nenhum agendamento encontrado.")
    
        # Opcional: Criar novo agendamento
        st.markdown("---")
        st.subheader("Novo Agendamento")
    
        clientes = cursor.execute("SELECT id, nome FROM clientes").fetchall()
        servicos = cursor.execute("SELECT id, nome FROM servicos").fetchall()
        cliente_dict = {nome: id for id, nome in clientes}
        servico_dict = {nome: id for id, nome in servicos}
    
        cliente_sel = st.selectbox("Cliente", list(cliente_dict.keys()))
        data_agendamento = st.date_input("Data")
        hora_agendamento = st.text_input("Hora (ex: 14:00)")
        servicos_selecionados = st.multiselect("Serviços", list(servico_dict.keys()))
    
        if st.button("Agendar"):
            if not servicos_selecionados:
                st.error("Selecione ao menos um serviço.")
            else:
                servicos_str = ", ".join(servicos_selecionados)
                cursor.execute("""
                    INSERT INTO agendamentos (cliente_id, data, hora, servicos, status)
                    VALUES (?, ?, ?, ?, ?)
                """, (cliente_dict[cliente_sel], data_agendamento.strftime("%Y-%m-%d"), hora_agendamento, servicos_str, "Pendente"))
                conn.commit()
                st.success("Agendamento realizado com sucesso!")
                st.experimental_rerun()
# Parte 8 - Painel de Vendas com puxar agendamento e nova venda

    elif menu == "Vendas":
        st.subheader("🛒 Painel de Vendas")
    
        opcao_venda = st.radio("Selecione a opção:", ["Usar Agendamento", "Nova Venda"])
    
        clientes = cursor.execute("SELECT id, nome FROM clientes").fetchall()
        cliente_dict = {nome: id for id, nome in clientes}
    
        if opcao_venda == "Usar Agendamento":
            # Buscar agendamentos com status pendente
            agendamentos = cursor.execute("""
                SELECT a.id, c.nome, a.data, a.hora, a.servicos, a.status
                FROM agendamentos a
                JOIN clientes c ON a.cliente_id = c.id
                WHERE a.status IN ('Pendente', 'Reagendada')
                ORDER BY a.data, a.hora
            """).fetchall()
    
            agendamento_str = [f"ID {a[0]} - {a[1]} - {a[2]} {a[3]} - Serviços: {a[4]} - Status: {a[5]}" for a in agendamentos]
    
            if agendamento_str:
                selecao = st.selectbox("Selecione um agendamento para finalizar a venda:", agendamento_str)
                idx = agendamento_str.index(selecao)
                ag = agendamentos[idx]
    
                st.write(f"Cliente: {ag[1]}")
                st.write(f"Data/Hora: {ag[2]} {ag[3]}")
                st.write(f"Serviços: {ag[4]}")
                st.write(f"Status atual: {ag[5]}")
    
                # Parse serviços separados por vírgula para seleção de quantidade
                serv_list = [s.strip() for s in ag[4].split(",") if s.strip()]
    
                # Buscar detalhes de serviços para preços e ids
                servicos_db = cursor.execute("SELECT id, nome, valor FROM servicos").fetchall()
                servicos_dict = {nome: (id, valor) for id, nome, valor in servicos_db}
    
                # Seleção de quantidades para cada serviço do agendamento
                quantidades = {}
                for serv in serv_list:
                    if serv in servicos_dict:
                        id_s, valor = servicos_dict[serv]
                        quantidades[serv] = st.number_input(f"Qtd para {serv}", min_value=1, max_value=100, value=1, key=f"qtd_serv_{id_s}")
                    else:
                        quantidades[serv] = 1  # serviço não cadastrado na base, qtd 1
    
                total = sum(quantidades[s] * servicos_dict[s][1] if s in servicos_dict else 0 for s in serv_list)
                st.info(f"Total: R$ {total:.2f}")
    
                if st.button("Finalizar Venda"):
                    # Inserir venda
                    cliente_id = cliente_dict[ag[1]]
                    data_venda = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    cursor.execute("INSERT INTO vendas (cliente_id, data, total) VALUES (?, ?, ?)", (cliente_id, data_venda, total))
                    venda_id = cursor.lastrowid
    
                    # Inserir itens venda
                    for serv in serv_list:
                        qtd = quantidades.get(serv, 1)
                        if serv in servicos_dict:
                            id_s, valor = servicos_dict[serv]
                            cursor.execute("INSERT INTO venda_itens (venda_id, tipo, item_id, quantidade, preco) VALUES (?, ?, ?, ?, ?)",
                                           (venda_id, "servico", id_s, qtd, valor))
    
                    # Atualizar status do agendamento para Finalizada
                    cursor.execute("UPDATE agendamentos SET status='Finalizada' WHERE id=?", (ag[0],))
                    conn.commit()
                    st.success("Venda finalizada e agendamento marcado como Finalizada!")
    
                    # Opção para reagendar ou cancelar agendamento
                    opc = st.radio("Deseja reagendar ou cancelar o agendamento?", ["Nenhum", "Reagendar", "Cancelar"])
                    if opc == "Reagendar":
                        nova_data = st.date_input("Nova Data")
                        nova_hora = st.text_input("Nova Hora (ex: 14:00)")
                        if st.button("Confirmar Reagendamento"):
                            cursor.execute("UPDATE agendamentos SET data=?, hora=?, status='Reagendada' WHERE id=?", (nova_data.strftime("%Y-%m-%d"), nova_hora, ag[0]))
                            conn.commit()
                            st.success("Agendamento reagendado com sucesso!")
                    elif opc == "Cancelar":
                        if st.button("Confirmar Cancelamento"):
                            cursor.execute("UPDATE agendamentos SET status='Cancelada' WHERE id=?", (ag[0],))
                            conn.commit()
                            st.success("Agendamento cancelado com sucesso!")
    
            else:
                st.info("Nenhum agendamento pendente para venda.")
    
        else:  # Nova Venda
            cliente_sel = st.selectbox("Cliente", list(cliente_dict.keys()))
            produtos = cursor.execute("SELECT id, nome, quantidade, preco_venda FROM produtos").fetchall()
            servicos = cursor.execute("SELECT id, nome, valor FROM servicos").fetchall()
            produto_dict = {nome: (id, qtd, preco) for id, nome, qtd, preco in produtos}
            servico_dict = {nome: (id, valor) for id, nome, valor in servicos}
    
            tipo_venda = st.radio("Tipo de Venda", ["Produtos", "Serviços", "Ambos"])
    
            itens_venda = []
            total = 0.0
    
            if tipo_venda in ["Produtos", "Ambos"]:
                st.markdown("### Produtos")
                produtos_selecionados = st.multiselect("Selecionar produtos", list(produto_dict.keys()))
                for nome in produtos_selecionados:
                    id_p, estoque, preco = produto_dict[nome]
                    qtd = st.number_input(f"Qtd para {nome} (Estoque: {estoque})", min_value=1, max_value=100, value=1, key=f"prod_{id_p}")
                    itens_venda.append(("produto", id_p, qtd, preco))
                    total += preco * qtd
    
            if tipo_venda in ["Serviços", "Ambos"]:
                st.markdown("### Serviços")
                servicos_selecionados = st.multiselect("Selecionar serviços", list(servico_dict.keys()))
                for nome in servicos_selecionados:
                    id_s, valor = servico_dict[nome]
                    qtd = st.number_input(f"Qtd para {nome}", min_value=1, max_value=100, value=1, key=f"serv_{id_s}")
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
            if st.button("Nova Venda"):
                st.experimental_rerun()
# Parte 9 - Cancelar Vendas com atualização do estoque e status

    elif menu == "Cancelar Vendas":
        st.subheader("❌ Cancelar Vendas")
    
        vendas = cursor.execute("""
            SELECT id, data, total FROM vendas WHERE cancelada=0 ORDER BY data DESC
        """).fetchall()
    
        if vendas:
            st.write("Vendas Ativas:")
            for v in vendas:
                st.write(f"ID: {v[0]} | Data: {v[1]} | Total: R$ {v[2]:.2f}")
    
            id_cancelar = st.number_input("ID da venda para cancelar", min_value=1, step=1)
            if st.button("Cancelar Venda"):
                venda = cursor.execute("SELECT * FROM vendas WHERE id=? AND cancelada=0", (id_cancelar,)).fetchone()
                if not venda:
                    st.error("Venda inválida ou já cancelada.")
                else:
                    itens = cursor.execute("SELECT tipo, item_id, quantidade FROM venda_itens WHERE venda_id=?", (id_cancelar,)).fetchall()
                    for tipo, item_id, qtd in itens:
                        if tipo == "produto":
                            cursor.execute("UPDATE produtos SET quantidade = quantidade + ? WHERE id=?", (qtd, item_id))
                    cursor.execute("UPDATE vendas SET cancelada=1 WHERE id=?", (id_cancelar,))
                    conn.commit()
                    st.success(f"Venda {id_cancelar} cancelada com sucesso.")
        else:
            st.info("Não há vendas para cancelar.")
# Parte 10 - Relatórios com filtro e gráficos

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
            ax.set_ylabel("Valor (R$)")
            st.pyplot(fig)
        else:
            st.info("Nenhuma venda encontrada no período selecionado.")

    elif menu == "Sair":
        st.session_state.login = False
        st.experimental_rerun()
    else:
        st.warning("Página não encontrada")

# Parte 11 - Finalizações e observações

# Observação: já usamos clear_on_submit=True em todos os forms para limpar automaticamente os campos após o envio.

# Exemplo: 
# with st.form("form_nome", clear_on_submit=True):
#     ...

# Caso queira personalizar botões com emojis ou estilos, pode usar algo como:
# st.button("🛒 Finalizar Venda")
# Ou customizar com CSS inline via st.markdown (mais avançado).

# Também pode melhorar layout, cores e feedbacks conforme preferir.

# --- FIM DO SISTEMA ---
