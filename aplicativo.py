import streamlit as st
import sqlite3
from datetime import datetime, date
from streamlit_drawable_canvas import st_canvas
import pandas as pd
import matplotlib.pyplot as plt
from PIL import Image
import io

# --- Conexão banco ---
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
        assinatura BLOB,
        data_nasc TEXT,
        instagram TEXT,
        cantor_fav TEXT,
        bebida_fav TEXT,
        fez_cepilacao TEXT,
        alergia TEXT,
        alergia_qual TEXT,
        problemas_pele TEXT,
        tratamento_derm TEXT,
        tipo_pele TEXT,
        hidrata_pele TEXT,
        gravida TEXT,
        usa_medicamento TEXT,
        medicamento_qual TEXT,
        diu_marcapasso TEXT,
        diabete TEXT,
        pelos_encravados TEXT,
        cirurgia_recente TEXT,
        foliculite TEXT,
        foliculite_qual TEXT,
        problema_informar TEXT,
        problema_qual TEXT,
        autoriza_imagens TEXT
    )
    """)
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

# --- CSS menu lateral fixo e estilizado ---
def estilizar_menu():
    st.markdown(
        """
        <style>
        /* Menu lateral largura e fundo */
        [data-testid="stSidebar"] {
            width: 280px;
            background-color: #0D47A1;
            color: white;
        }
        /* Texto menu */
        [data-testid="stSidebar"] .css-1d391kg {
            font-size: 18px;
            font-weight: bold;
            color: white;
        }
        /* Hover itens */
        [data-testid="stSidebar"] .css-1d391kg:hover {
            background-color: #1565C0;
            color: #FFD700;
        }
        /* Esconder radio padrão */
        [data-testid="stSidebar"] input[type="radio"] {
            display: none;
        }
        /* Custom radio labels */
        [data-testid="stSidebar"] label {
            background-color: #1976D2;
            border-radius: 6px;
            padding: 10px 15px;
            margin-bottom: 8px;
            display: block;
            cursor: pointer;
            transition: background-color 0.3s ease;
            color: white;
        }
        /* Label selecionado */
        [data-testid="stSidebar"] input[type="radio"]:checked + label {
            background-color: #FFC107;
            color: #0D47A1;
        }
        </style>
        """, unsafe_allow_html=True
    )

def menu_lateral():
    try:
        st.sidebar.image("logo.png", width=180)
    except:
        st.sidebar.write("**Studio de Depilação**")
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
    ], index=0)
    return menu

# --- Cadastro Cliente com ficha de avaliação e assinatura ---
def cadastro_cliente():
    st.title("Cadastro de Cliente - Ficha de Avaliação")

    with st.form("form_cliente_completo"):
        nome = st.text_input("Nome Completo")
        telefone = st.text_input("Número de Telefone")
        data_nasc = st.date_input("Data de Nascimento")
        instagram = st.text_input("Instagram")
        cantor_fav = st.text_input("Cantor Favorito")
        bebida_fav = st.text_input("Bebida Favorita")

        fez_cepilacao = st.radio("Já fez epilação na cera?", ("Sim", "Não"))

        alergia = st.radio("Possui algum tipo de alergia?", ("Sim", "Não"))
        alergia_qual = ""
        if alergia == "Sim":
            alergia_qual = st.text_input("Qual?")

        problemas_pele = st.radio("Problemas de pele?", ("Sim", "Não"))

        tratamento_derm = st.radio("Está em tratamento dermatológico?", ("Sim", "Não"))

        tipo_pele = st.selectbox("Tipo de pele", ("Seca", "Oleosa", "Normal"))

        hidrata_pele = st.radio("Hidrata a pele com frequência?", ("Sim", "Não"))

        gravida = st.radio("Está grávida?", ("Sim", "Não"))

        usa_medicamento = st.radio("Faz uso de algum medicamento?", ("Sim", "Não"))
        medicamento_qual = ""
        if usa_medicamento == "Sim":
            medicamento_qual = st.text_input("Qual?")

        diu_marcapasso = st.radio("Utiliza DIU ou Marca-passo?", ("DIU", "Marca-passo", "Nenhum"))

        diabete = st.radio("Diabete?", ("Sim", "Não"))

        pelos_encravados = st.radio("Pelos encravados?", ("Sim", "Não"))

        cirurgia_recente = st.radio("Realizou alguma cirurgia recentemente?", ("Sim", "Não"))

        foliculite = st.radio("Foliculite?", ("Sim", "Não"))
        foliculite_qual = ""
        if foliculite == "Sim":
            foliculite_qual = st.text_input("Qual?")

        problema_informar = st.radio("Algum problema que seja necessário nos informar antes do procedimento?", ("Sim", "Não"))
        problema_qual = ""
        if problema_informar == "Sim":
            problema_qual = st.text_input("Qual?")

        autoriza_imagens = st.radio("Autoriza o uso de imagens para redes sociais?", ("Sim", "Não"))

        st.write("Assinatura (use mouse ou touch para desenhar):")
        canvas_result = st_canvas(
            fill_color="rgba(0, 0, 0, 0)",
            stroke_width=2,
            stroke_color="#000000",
            background_color="#eee",
            height=150,
            width=400,
            drawing_mode="freedraw",
            key="canvas_assinatura"
        )

        if st.form_submit_button("Salvar Cliente"):
            if not nome:
                st.error("Nome é obrigatório")
                return
            assinatura_bytes = None
            if canvas_result.image_data is not None:
                img = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
                buffer = io.BytesIO()
                img.save(buffer, format="PNG")
                assinatura_bytes = buffer.getvalue()

            cursor.execute("""
                INSERT INTO clientes (
                    nome, telefone, email, assinatura,
                    data_nasc, instagram, cantor_fav, bebida_fav,
                    fez_cepilacao,
                    alergia, alergia_qual,
                    problemas_pele,
                    tratamento_derm,
                    tipo_pele,
                    hidrata_pele,
                    gravida,
                    usa_medicamento, medicamento_qual,
                    diu_marcapasso,
                    diabete,
                    pelos_encravados,
                    cirurgia_recente,
                    foliculite, foliculite_qual,
                    problema_informar, problema_qual,
                    autoriza_imagens
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                nome, telefone, "", assinatura_bytes,
                data_nasc.strftime("%Y-%m-%d"), instagram, cantor_fav, bebida_fav,
                fez_cepilacao,
                alergia, alergia_qual,
                problemas_pele,
                tratamento_derm,
                tipo_pele,
                hidrata_pele,
                gravida,
                usa_medicamento, medicamento_qual,
                diu_marcapasso,
                diabete,
                pelos_encravados,
                cirurgia_recente,
                foliculite, foliculite_qual,
                problema_informar, problema_qual,
                autoriza_imagens
            ))
            conn.commit()
            st.success("Cliente cadastrado com ficha de avaliação completa!")

# -- Outras funções do sistema (dashboard, vendas, etc) -- Placeholder --

def main():
    st.set_page_config(page_title="Studio Depilação", layout="wide")
    estilizar_menu()

    if not st.session_state["login"]:
        tela_login()
    else:
        menu = menu_lateral()
        if menu == "Cadastro Cliente":
            cadastro_cliente()
        elif menu == "Sair":
            st.session_state["login"] = False
            st.session_state["usuario"] = ""
            st.experimental_rerun()
        else:
            st.title(f"Menu {menu} ainda não implementado.")
            st.info("Funcionalidade em desenvolvimento.")

if __name__ == "__main__":
    main()
