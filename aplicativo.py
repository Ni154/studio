# app.py
import streamlit as st
import sqlite3
from datetime import datetime
import base64
import io
from PIL import Image
from streamlit_drawable_canvas import st_canvas

# --- Banco ---
conn = sqlite3.connect('studio_beauty.db', check_same_thread=False)
cursor = conn.cursor()

# Função para criar tabelas - corrigido para garantir criação antes do uso
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
        preco REAL,
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
    conn.commit()

# --- Correção: criar tabelas antes de buscar usuário ---
criar_tabelas()

def verificar_login(usuario, senha):
    cursor.execute("SELECT senha FROM usuarios WHERE usuario = ?", (usuario,))
    res = cursor.fetchone()
    return res is not None and res[0] == senha

def criar_usuario_padrao():
    cursor.execute("SELECT * FROM usuarios WHERE usuario = 'admin'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO usuarios (usuario, senha) VALUES (?, ?)", ('admin', 'admin123'))
        conn.commit()

criar_usuario_padrao()

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

def salvar_servico(nome, descricao, duracao, valor):
    cursor.execute("INSERT INTO servicos (nome, descricao, duracao, valor) VALUES (?, ?, ?, ?)", (nome, descricao, duracao, valor))
    conn.commit()

def carregar_servicos():
    cursor.execute("SELECT id, nome, descricao, duracao, valor FROM servicos")
    return cursor.fetchall()

def salvar_produto(nome, descricao, preco, quantidade):
    cursor.execute("INSERT INTO produtos (nome, descricao, preco, quantidade) VALUES (?, ?, ?, ?)", (nome, descricao, preco, quantidade))
    conn.commit()

def carregar_produtos():
    cursor.execute("SELECT id, nome, descricao, preco, quantidade FROM produtos")
    return cursor.fetchall()

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
        SELECT a.id, c.nome, s.nome, a.data_hora, a.status
        FROM agendamentos a
        JOIN clientes c ON a.cliente_id = c.id
        JOIN servicos s ON a.servico_id = s.id
        WHERE a.status = ?
        ORDER BY a.data_hora DESC
    ''', (status,))
    return cursor.fetchall()

def cancelar_agendamento(agendamento_id):
    cursor.execute("UPDATE agendamentos SET status = 'cancelado' WHERE id = ?", (agendamento_id,))
    conn.commit()

def salvar_venda_servico(cliente_id, servico_id, valor, forma_pagamento):
    data = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('''
        INSERT INTO vendas (cliente_id, servico_id, valor, forma_pagamento, data)
        VALUES (?, ?, ?, ?, ?)
    ''', (cliente_id, servico_id, valor, forma_pagamento, data))
    conn.commit()

def salvar_venda_produto(cliente_id, produto_id, quantidade, forma_pagamento):
    cursor.execute("SELECT preco, quantidade FROM produtos WHERE id = ?", (produto_id,))
    res = cursor.fetchone()
    if not res:
        return False, "Produto não encontrado"
    preco, estoque = res
    if estoque < quantidade:
        return False, f"Estoque insuficiente: disponível {estoque}"
    valor_total = preco * quantidade
    data = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute('''
        INSERT INTO vendas (cliente_id, produto_id, quantidade, valor, forma_pagamento, data)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (cliente_id, produto_id, quantidade, valor_total, forma_pagamento, data))

    cursor.execute("UPDATE produtos SET quantidade = quantidade - ? WHERE id = ?", (quantidade, produto_id))
    conn.commit()
    return True, "Venda registrada com sucesso"

def carregar_vendas(ativos=True):
    status = 'ativo' if ativos else 'cancelado'
    cursor.execute('''
        SELECT v.id, c.nome, s.nome, p.nome, v.quantidade, v.valor, v.forma_pagamento, v.data, v.status
        FROM vendas v
        LEFT JOIN clientes c ON v.cliente_id = c.id
        LEFT JOIN servicos s ON v.servico_id = s.id
        LEFT JOIN produtos p ON v.produto_id = p.id
        WHERE v.status = ?
        ORDER BY v.data DESC
    ''', (status,))
    return cursor.fetchall()

def cancelar_venda(venda_id):
    cursor.execute("UPDATE vendas SET status = 'cancelado' WHERE id = ?", (venda_id,))
    conn.commit()

# --- Formulário Ficha Avaliação (para cadastro externo) ---
def formulario_ficha_avaliacao():
    st.title("Ficha de Avaliação - Studio Beleza")

    with st.form("form_ficha", clear_on_submit=True):
        nome = st.text_input("Nome completo", max_chars=100)
        telefone = st.text_input("Número de telefone")
        data_nasc = st.date_input("Data de Nascimento")
        instagram = st.text_input("Instagram")
        cantor_fav = st.text_input("Cantor favorito")
        bebida_fav = st.text_input("Bebida favorita")

        epilacao_cera_sim = st.checkbox("Já fez epilação na cera? SIM")
        epilacao_cera_nao = st.checkbox("Já fez epilação na cera? NÃO")

        alergia_sim = st.checkbox("Possui algum tipo de alergia? SIM")
        alergia_nao = st.checkbox("Possui algum tipo de alergia? NÃO")
        alergia_qual = st.text_input("Qual?")

        problema_pele_sim = st.checkbox("Problemas de pele? SIM")
        problema_pele_nao = st.checkbox("Problemas de pele? NÃO")

        tratamento_derma_sim = st.checkbox("Está em tratamento dermatológico? SIM")
        tratamento_derma_nao = st.checkbox("Está em tratamento dermatológico? NÃO")

        tipo_pele = st.radio("Tipo de pele", ["SECA", "OLEOSA", "NORMAL"])

        hidrata_pele_sim = st.checkbox("Hidrata a pele com frequência? SIM")
        hidrata_pele_nao = st.checkbox("Hidrata a pele com frequência? NÃO")

        gravida_sim = st.checkbox("Está grávida? SIM")
        gravida_nao = st.checkbox("Está grávida? NÃO")

        med_uso_sim = st.checkbox("Faz uso de algum medicamento? SIM")
        med_uso_nao = st.checkbox("Faz uso de algum medicamento? NÃO")
        med_qual = st.text_input("Qual?")

        diu = st.checkbox("Utiliza DIU")
        marcapasso = st.checkbox("Utiliza Marca-passo")
        nenhum_diu_mp = st.checkbox("Nenhum")

        diabete_sim = st.checkbox("Diabete? SIM")
        diabete_nao = st.checkbox("Diabete? NÃO")

        pelos_encravados_sim = st.checkbox("Pelos encravados? SIM")
        pelos_encravados_nao = st.checkbox("Pelos encravados? NÃO")

        cirurgia_recente_sim = st.checkbox("Realizou alguma cirurgia recentemente? SIM")
        cirurgia_recente_nao = st.checkbox("Realizou alguma cirurgia recentemente? NÃO")

        foliculite_sim = st.checkbox("Foliculite? SIM")
        foliculite_nao = st.checkbox("Foliculite? NÃO")
        foliculite_qual = st.text_input("Qual?")

        problema_procedimento_sim = st.checkbox("Algum problema que seja necessário informar antes do procedimento? SIM")
        problema_procedimento_nao = st.checkbox("Algum problema que seja necessário informar antes do procedimento? NÃO")
        problema_procedimento_qual = st.text_input("Qual?")

        autoriza_imagens_sim = st.checkbox("Autoriza o uso de imagens para redes sociais? SIM")
        autoriza_imagens_nao = st.checkbox("Autoriza o uso de imagens para redes sociais? NÃO")

        st.markdown("Assinatura digital:")
        canvas_result = st_canvas(
            fill_color="rgba(0, 0, 255, 0.3)",
            stroke_width=2,
            stroke_color="#000000",
            background_color="#eee",
            height=150,
            width=400,
            drawing_mode="freedraw",
            key="canvas_ficha",
        )
        foto = st.file_uploader("Upload de foto / selfie (jpg, png)", type=['jpg','jpeg','png'])

        submit = st.form_submit_button("Enviar")

        if submit:
            if not nome.strip():
                st.error("Nome é obrigatório!")
                return
            if canvas_result.image_data is None:
                st.error("Assine no campo abaixo!")
                return

            img = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
            buffered = io.BytesIO()
            img.save(buffered, format="PNG")
            assinatura_b64 = base64.b64encode(buffered.getvalue()).decode()

            foto_bytes = foto.read() if foto else None

            anamnese = f'''
Data de Nascimento: {data_nasc.strftime("%d/%m/%Y")}
Instagram: {instagram}
Cantor Favorito: {cantor_fav}
Bebida Favorita: {bebida_fav}

Já fez epilação na cera? SIM: {epilacao_cera_sim} | NÃO: {epilacao_cera_nao}
Possui alergia? SIM: {alergia_sim} | NÃO: {alergia_nao} | Qual: {alergia_qual}
Problemas de pele? SIM: {problema_pele_sim} | NÃO: {problema_pele_nao}
Tratamento dermatológico? SIM: {tratamento_derma_sim} | NÃO: {tratamento_derma_nao}
Tipo de pele: {tipo_pele}
Hidrata a pele com frequência? SIM: {hidrata_pele_sim} | NÃO: {hidrata_pele_nao}
Está grávida? SIM: {gravida_sim} | NÃO: {gravida_nao}
Faz uso de medicamento? SIM: {med_uso_sim} | NÃO: {med_uso_nao} | Qual: {med_qual}
Utiliza DIU? {diu} | Marca-passo? {marcapasso} | Nenhum? {nenhum_diu_mp}
Diabete? SIM: {diabete_sim} | NÃO: {diabete_nao}
Pelos encravados? SIM: {pelos_encravados_sim} | NÃO: {pelos_encravados_nao}
Cirurgia recente? SIM: {cirurgia_recente_sim} | NÃO: {cirurgia_recente_nao}
Foliculite? SIM: {foliculite_sim} | NÃO: {foliculite_nao} | Qual: {foliculite_qual}
Problema antes do procedimento? SIM: {problema_procedimento_sim} | NÃO: {problema_procedimento_nao} | Qual: {problema_procedimento_qual}
Autoriza uso de imagens? SIM: {autoriza_imagens_sim} | NÃO: {autoriza_imagens_nao}
'''

            salvar_cliente(nome, telefone, "", anamnese, bebida_fav, cantor_fav, assinatura_b64, foto_bytes)
            st.success("Ficha enviada com sucesso! Obrigado.")

# --- Página de Login ---
def pagina_login():
    st.title("Login Studio Beleza")
    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if verificar_login(usuario, senha):
            st.session_state['login'] = True
            st.session_state['usuario'] = usuario
            st.experimental_rerun()
        else:
            st.error("Usuário ou senha inválidos")

# --- Menu lateral ---
def menu_lateral():
    st.sidebar.title("Menu")
    pagina = st.sidebar.radio("Navegar", [
        "Cadastro Cliente",
        "Cadastro Serviço",
        "Cadastro Produto",
        "Agendamento",
        "Vendas",
        "Relatórios",
        "Clientes Cancelados",
        "Sair"
    ])
    return pagina

# --- Página cadastro cliente admin (simplificado) ---
def pagina_cadastro_cliente_admin():
    st.header("Cadastro Cliente (Admin)")
    with st.form("form_cliente_admin", clear_on_submit=True):
        nome = st.text_input("Nome completo")
        telefone = st.text_input("Telefone")
        email = st.text_input("Email")
        anamnese = st.text_area("Anamnese (informações médicas)")

        bebida = st.text_input("Bebida favorita")
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
            key="canvas_admin",
        )
        foto = st.file_uploader("Upload de foto / selfie (jpg, png)", type=['jpg','jpeg','png'])

        submit = st.form_submit_button("Salvar Cliente")
        if submit:
            if not nome.strip():
                st.error("Nome é obrigatório")
            elif canvas_result.image_data is None:
                st.error("Assine no campo")
            else:
                img = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
                buffered = io.BytesIO()
                img.save(buffered, format="PNG")
                assinatura_b64 = base64.b64encode(buffered.getvalue()).decode()

                foto_bytes = foto.read() if foto else None

                salvar_cliente(nome, telefone, email, anamnese, bebida, gosto_musical, assinatura_b64, foto_bytes)
                st.success("Cliente salvo com sucesso")

# --- Página cadastro serviço ---
def pagina_cadastro_servico():
    st.header("Cadastro Serviço")
    with st.form("form_servico", clear_on_submit=True):
        nome = st.text_input("Nome do serviço")
        descricao = st.text_area("Descrição")
        duracao = st.number_input("Duração (minutos)", min_value=1, step=1)
        valor = st.number_input("Valor (R$)", min_value=0.0, step=0.01, format="%.2f")

        submit = st.form_submit_button("Salvar Serviço")
        if submit:
            if not nome.strip():
                st.error("Nome obrigatório")
            else:
                salvar_servico(nome, descricao, duracao, valor)
                st.success("Serviço salvo")

    servicos = carregar_servicos()
    st.subheader("Serviços cadastrados")
    for s in servicos:
        st.write(f"{s[0]} - {s[1]} - R$ {s[4]:.2f}")

# --- Página cadastro produto ---
def pagina_cadastro_produto():
    st.header("Cadastro Produto")
    with st.form("form_produto", clear_on_submit=True):
        nome = st.text_input("Nome do produto")
        descricao = st.text_area("Descrição")
        preco = st.number_input("Preço (R$)", min_value=0.0, step=0.01, format="%.2f")
        quantidade = st.number_input("Quantidade em estoque", min_value=0, step=1)

        submit = st.form_submit_button("Salvar Produto")
        if submit:
            if not nome.strip():
                st.error("Nome obrigatório")
            else:
                salvar_produto(nome, descricao, preco, quantidade)
                st.success("Produto salvo")

    produtos = carregar_produtos()
    st.subheader("Produtos cadastrados")
    for p in produtos:
        st.write(f"{p[0]} - {p[1]} - R$ {p[3]:.2f} - Estoque: {p[4]}")

# --- Página agendamento ---
def pagina_agendamento():
    st.header("Agendamento")
    clientes = carregar_clientes()
    servicos = carregar_servicos()
    clientes_dict = {c[1]: c[0] for c in clientes}
    servicos_dict = {s[1]: s[0] for s in servicos}

    cliente_nome = st.selectbox("Selecione o cliente", list(clientes_dict.keys()))
    servico_nome = st.selectbox("Selecione o serviço", list(servicos_dict.keys()))
    data_hora = st.datetime_input("Data e Hora")

    if st.button("Agendar"):
        cliente_id = clientes_dict[cliente_nome]
        servico_id = servicos_dict[servico_nome]
        salvar_agendamento(cliente_id, servico_id, data_hora.strftime("%Y-%m-%d %H:%M:%S"))
        st.success("Agendamento realizado")

    agendamentos = carregar_agendamentos()
    st.subheader("Agendamentos ativos")
    for a in agendamentos:
        st.write(f"{a[0]} - Cliente: {a[1]} | Serviço: {a[2]} | Data: {a[3]}")

# --- Página vendas ---
def pagina_vendas():
    st.header("Vendas")
    clientes = carregar_clientes()
    servicos = carregar_servicos()
    produtos = carregar_produtos()

    clientes_dict = {c[1]: c[0] for c in clientes}
    servicos_dict = {s[1]: s[0] for s in servicos}
    produtos_dict = {p[1]: p[0] for p in produtos}

    venda_tipo = st.radio("Tipo de venda", ["Serviço", "Produto"])

    cliente_nome = st.selectbox("Cliente", list(clientes_dict.keys()))

    if venda_tipo == "Serviço":
        servico_nome = st.selectbox("Serviço", list(servicos_dict.keys()))
        valor = st.number_input("Valor (R$)", min_value=0.0, step=0.01, format="%.2f")
        forma_pagamento = st.selectbox("Forma de pagamento", ["Dinheiro", "Cartão", "Pix"])

        if st.button("Registrar venda serviço"):
            cliente_id = clientes_dict[cliente_nome]
            servico_id = servicos_dict[servico_nome]
            salvar_venda_servico(cliente_id, servico_id, valor, forma_pagamento)
            st.success("Venda de serviço registrada")

    else:
        produto_nome = st.selectbox("Produto", list(produtos_dict.keys()))
        quantidade = st.number_input("Quantidade", min_value=1, step=1)
        forma_pagamento = st.selectbox("Forma de pagamento", ["Dinheiro", "Cartão", "Pix"])

        if st.button("Registrar venda produto"):
            cliente_id = clientes_dict[cliente_nome]
            produto_id = produtos_dict[produto_nome]
            sucesso, msg = salvar_venda_produto(cliente_id, produto_id, quantidade, forma_pagamento)
            if sucesso:
                st.success(msg)
            else:
                st.error(msg)

# --- Página relatórios ---
def pagina_relatorios():
    st.header("Relatórios")

    vendas = carregar_vendas()
    st.subheader("Vendas recentes")
    for v in vendas:
        st.write(f"{v[0]} - Cliente: {v[1]} | Serviço: {v[2]} | Produto: {v[3]} | Quantidade: {v[4]} | Valor: R$ {v[5]:.2f} | Pagamento: {v[6]} | Data: {v[7]}")

# --- Página clientes cancelados ---
def pagina_clientes_cancelados():
    st.header("Clientes Cancelados")
    clientes = carregar_clientes(ativos=False)
    for c in clientes:
        st.write(f"{c[0]} - {c[1]} - {c[2]}")

# --- Página inicial após login ---
def pagina_inicial():
    st.title(f"Bem-vindo, {st.session_state.get('usuario', '')}")
    st.write("Use o menu lateral para navegar pelas funcionalidades.")

# --- Main ---
if 'login' not in st.session_state:
    st.session_state['login'] = False

if not st.session_state['login']:
    pagina_login()
else:
    pagina = menu_lateral()

    if pagina == "Cadastro Cliente":
        pagina_cadastro_cliente_admin()
    elif pagina == "Cadastro Serviço":
        pagina_cadastro_servico()
    elif pagina == "Cadastro Produto":
        pagina_cadastro_produto()
    elif pagina == "Agendamento":
        pagina_agendamento()
    elif pagina == "Vendas":
        pagina_vendas()
    elif pagina == "Relatórios":
        pagina_relatorios()
    elif pagina == "Clientes Cancelados":
        pagina_clientes_cancelados()
    elif pagina == "Sair":
        st.session_state['login'] = False
        st.experimental_rerun()

# --- Rodar formulário ficha avaliação pelo link (se desejar) ---
# para criar uma rota diferente (não coberta aqui, mas pode ser implementado com query params)
