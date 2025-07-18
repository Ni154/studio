# utils/form_helpers.py
import streamlit as st

def limpar_sessao_formulario():
    for key in st.session_state.keys():
        del st.session_state[key]

