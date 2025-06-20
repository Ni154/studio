import os
import shutil
import streamlit as st
import sqlite3
from datetime import datetime, date
from streamlit_drawable_canvas import st_canvas
from PIL import Image
import io
import pandas as pd
import plotly.express as px

# Configuração da página
st.set_page_config(page_title="Studio de Depilação", layout="wide", initial_sidebar_state="expanded")

# Caminhos para banco e backup
DB_PATH = "studio.db"
BACKUP_DIR = "backups"
BACKUP_LOG = "backup_log.txt"

# Função para backup automático a cada 15 dias
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

# Inicializa banco
if not os.path.exists(DB_PATH):
    # Cria banco vazio se não existir
    open(DB_PATH, 'a').close()

checar_backup()
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
cursor = conn.cursor()

# Criação de tabelas principais (simplificado, pode adicionar mais campos e tabelas conforme necessário)
cursor.execute("""
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY, usuario TEXT UNIQUE, senha TEXT
)""")
cursor.execute("INSERT OR IGNORE INTO usuarios (id, usuario, senha) VALUES (1, 'admin', 'admin')")

cursor.execute("""
CREATE TABLE IF NOT EXISTS clientes (
    id INTEGER PRIMARY KEY, nome TEXT, telefone TEXT, data_nascimento TEXT, instagram TEXT,
    cantor_favorito TEXT, bebida_favorita TEXT, assinatura BLOB
)""")

conn.commit()

# Estilo geral (tema clínico)
st.markdown("""
<style>
body, .block-container {
    background-color: #f8fafc;
    color: #004466;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}
.menu-btn {
    background-color: #e6f0f8;
    border: 2px solid #3399ff;
    border-radius: 4px;
    color: #004466;
    font-weight: 600;
    padding: 10px 20px;
    margin-bottom: 10px;
    width: 100%;
    cursor: pointer;
    transition: background-color 0.3s ease;
    text-align: left;
}
.menu-btn:hover {
    background-color: #cce6ff;
    color: #00264d;
}
.menu-btn-selected {
    background-color: #3399ff;
    color: white;
}
.login-container {
    max-width: 400px;
    margin: 50px auto;
    padding: 30px;
    background-color: white;
    border-radius: 10px;
    box-shadow: 0 0 15px rgba(0,102,153,0.3);
    text-align: center;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    color: #004466;
}
.login-container h2 {
    margin-bottom: 25px;
}
.login-image {
    margin-bottom: 15px;
    border-radius: 10px;
}
</style>
""", unsafe_allow_html=True)

# Função menu lateral com botões
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

# Login
if "logado" not in st.session_state:
    st.session_state.logado = False

if not st.session_state.logado:
    st.markdown(
        """
        <div class="login-container">
            <img class="login-image" src="https://images.unsplash.com/photo-1576765607924-99f97cae02a9?auto=format&fit=crop&w=300&q=80" alt="Estética" width="300" />
            <h2>Login - Studio de Depilação</h2>
        </div>
        """, unsafe_allow_html=True)
    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        cursor.execute("SELECT * FROM usuarios WHERE usuario=? AND senha=?", (usuario, senha))
        resultado = cursor.fetchone()
        if resultado:
            st.session_state.logado = True
            st.experimental_rerun()
        else:
            st.error("Usuário ou senha inválidos.")
    st.stop()

# Menu lateral
menu_opcoes = [
    "Início", "Clientes", "Agendamentos", "Serviços",
    "Produtos", "Vendas", "Despesas", "Relatórios",
    "Importação", "Sair"
]

with st.sidebar:
    st.image("https://images.unsplash.com/photo-1588776814546-cded238c6846?auto=format&fit=crop&w=400&q=80", width=200)
    st.markdown("### Studio de Depilação")
    st.markdown("---")
    menu = menu_lateral_botao(menu_opcoes, "menu_selecionado")

# Páginas
if menu == "Início":
    st.title("🌿 Bem-vinda ao Studio de Depilação")
    st.image("https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=800&q=80")
    st.markdown("Use o menu ao lado para navegar no sistema.")

elif menu == "Clientes":
    st.title("👩 Cadastro de Clientes + Ficha de Avaliação")
    with st.form("form_cadastro_cliente"):
        col1, col2 = st.columns(2)
        with col1:
            nome = st.text_input("Nome completo")
            telefone = st.text_input("Telefone")
            data_nascimento = st.date_input("Data de nascimento", value=date(1990,1,1), max_value=date.today())
            instagram = st.text_input("Instagram")
        with col2:
            cantor = st.text_input("Cantor favorito")
            bebida = st.text_input("Bebida favorita")

        st.markdown("### ✍️ Assinatura Digital")
        canvas_result = st_canvas(
            fill_color="rgba(255,255,255,0)", stroke_width=2,
            stroke_color="#000", background_color="#fff", height=150,
            drawing_mode="freedraw"
        )
        assinatura_bytes = None
        if canvas_result.image_data is not None:
            img = canvas_result.image_data
            buffered = io.BytesIO()
            Image.fromarray((img[:, :, :3]).astype('uint8')).save(buffered, format="PNG")
            assinatura_bytes = buffered.getvalue()

        # Exemplo simplificado do botão salvar cadastro
        if st.form_submit_button("Salvar Cadastro"):
            if not nome.strip():
                st.error("O nome do cliente é obrigatório.")
            else:
                cursor.execute(
                    """INSERT INTO clientes (nome, telefone, data_nascimento, instagram, cantor_favorito, bebida_favorita, assinatura)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (nome, telefone, str(data_nascimento), instagram, cantor, bebida, assinatura_bytes)
                )
                conn.commit()
                st.success("Cadastro salvo com sucesso!")

elif menu == "Agendamentos":
    st.title("📆 Página de Agendamentos")
    st.info("Aqui você pode implementar a funcionalidade de agendamentos.")

elif menu == "Serviços":
    st.title("📝 Página de Serviços")
    st.info("Aqui você pode implementar a funcionalidade de serviços.")

elif menu == "Produtos":
    st.title("📦 Página de Produtos")
    st.info("Aqui você pode implementar a funcionalidade de produtos.")

elif menu == "Vendas":
    st.title("💳 Página de Vendas")
    st.info("Aqui você pode implementar a funcionalidade de vendas.")

elif menu == "Despesas":
    st.title("📉 Página de Despesas")
    st.info("Aqui você pode implementar a funcionalidade de despesas.")

elif menu == "Relatórios":
    st.title("📊 Página de Relatórios")
    st.info("Aqui você pode implementar a funcionalidade de relatórios.")

elif menu == "Importação":
    st.title("📥 Importação de Dados")
    st.warning("⚠️ Ao importar um arquivo de banco, o banco atual será substituído completamente. Faça backup antes!")
    uploaded_file = st.file_uploader("Selecione o arquivo de backup (.db)", type=["db"])
    if uploaded_file is not None:
        if st.button("Importar backup"):
            with open(DB_PATH, "wb") as f:
                f.write(uploaded_file.getbuffer())
            st.success("Backup importado com sucesso! Reinicie o sistema para aplicar as mudanças.")
            st.stop()

elif menu == "Sair":
    st.session_state.logado = False
    st.experimental_rerun()
