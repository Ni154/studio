import streamlit as st

def limpar_formulario(form_key: str):
    """Limpa os inputs de um formulário Streamlit identificando por key"""
    for key in st.session_state.keys():
        if key.startswith(form_key):
            del st.session_state[key]
