import streamlit as st
from datetime import datetime
from config.supabase_client import supabase
from utils.formatters import formatar_data_br

def carregar_agendamentos_para_venda():
    response = supabase.table("agendamentos").select("*").eq("status", "Agendado").order("data", ascending=True).order("hora", ascending=True).execute()
    if response.status_code == 200:
        return response.data
    else:
        st.error("Erro ao carregar agendamentos.")
        return []

def carregar_vendas():
    response = supabase.table("vendas").select("*").order("data", desc=True).execute()
    if response.status_code == 200:
        return response.data
    else:
        st.error("Erro ao carregar vendas.")
        return []

def salvar_venda(venda):
    if "id" in venda and venda["id"]:
        response = supabase.table("vendas").update(venda).eq("id", venda["id"]).execute()
    else:
        response = supabase.table("vendas").insert(venda).execute()
    if response.status_code not in (200, 201):
        st.error("Erro ao salvar venda.")
        return False
    return True

def cancelar_venda(venda_id):
    response = supabase.table("vendas").update({"cancelada": True}).eq("id", venda_id).execute()
    if response.status_code not in (200, 204):
        st.error("Erro ao cancelar venda.")
        return False
    return True

def venda_por_agendamento(agendamento):
    st.write(f"### Venda por Agendamento: {formatar_data_br(agendamento['data'])} - {agendamento['cliente_nome']}")

    produtos = st.session_state.get("venda_produtos", [])
    servicos = agendamento.get("servicos", "").split(", ")

    # Seleção da forma de pagamento
    forma_pagamento = st.selectbox("Forma de pagamento", ["Dinheiro", "Cartão", "Pix", "Cheque", "Outros"], key="fp_agendamento")

    # Adicionar produtos (simulação: aqui só permite texto livre)
    novo_produto = st.text_input("Adicionar produto (nome)", key="novo_produto_agg")
    preco_produto = st.number_input("Preço do produto", min_value=0.0, format="%.2f", key="preco_produto_agg")
    if st.button("Adicionar produto", key="btn_add_prod_agg"):
        if novo_produto and preco_produto > 0:
            produtos.append({"nome": novo_produto, "preco": preco_produto})
            st.session_state["venda_produtos"] = produtos
            st.experimental_rerun()

    total_produtos = sum(p["preco"] for p in produtos)
    total_servicos = 0.0  # ou extrair preço dos serviços se tiver no banco

    st.write("### Produtos adicionados:")
    for i, p in enumerate(produtos):
        col1, col2, col3 = st.columns([6, 2, 1])
        col1.write(p["nome"])
        col2.write(f"R$ {p['preco']:.2f}")
        if col3.button("❌", key=f"remover_produto_{i}_agg"):
            produtos.pop(i)
            st.session_state["venda_produtos"] = produtos
            st.experimental_rerun()

    total_geral = total_produtos + total_servicos
    st.write(f"**Total da venda: R$ {total_geral:.2f}**")

    if st.button("Finalizar venda por agendamento", key="finalizar_agg"):
        venda = {
            "cliente_id": agendamento["cliente_id"],
            "cliente_nome": agendamento["cliente_nome"],
            "data": datetime.now().strftime("%Y-%m-%d"),
            "produtos": produtos,
            "servicos": servicos,
            "total": total_geral,
            "cancelada": False,
            "agendamento_id": agendamento["id"],
            "forma_pagamento": forma_pagamento
        }
        sucesso = salvar_venda(venda)
        if sucesso:
            # Atualiza status do agendamento para "Finalizado"
            supabase.table("agendamentos").update({"status": "Finalizado"}).eq("id", agendamento["id"]).execute()
            st.success("Venda por agendamento finalizada com sucesso!")
            st.session_state.pop("venda_produtos", None)
            st.experimental_rerun()

def nova_venda(clientes):
    st.subheader("Nova Venda")

    clientes_dict = {c['nome']: c for c in clientes}
    cliente_selecionado = st.selectbox("Cliente", [""] + list(clientes_dict.keys()), key="sel_cliente_nova")

    produtos = st.session_state.get("venda_produtos", [])

    # Seleção da forma de pagamento
    forma_pagamento = st.selectbox("Forma de pagamento", ["Dinheiro", "Cartão", "Pix", "Cheque", "Outros"], key="fp_nova")

    novo_produto = st.text_input("Adicionar produto (nome)", key="novo_produto_nova")
    preco_produto = st.number_input("Preço do produto", min_value=0.0, format="%.2f", key="preco_produto_nova")

    if st.button("Adicionar produto nova venda", key="btn_add_prod_nova"):
        if novo_produto and preco_produto > 0:
            produtos.append({"nome": novo_produto, "preco": preco_produto})
            st.session_state["venda_produtos"] = produtos
            st.experimental_rerun()

    st.write("### Produtos adicionados:")
    for i, p in enumerate(produtos):
        col1, col2, col3 = st.columns([6, 2, 1])
        col1.write(p["nome"])
        col2.write(f"R$ {p['preco']:.2f}")
        if col3.button("❌", key=f"remover_produto_nova_{i}"):
            produtos.pop(i)
            st.session_state["venda_produtos"] = produtos
            st.experimental_rerun()

    total_geral = sum(p["preco"] for p in produtos)
    st.write(f"**Total da venda: R$ {total_geral:.2f}**")

    if st.button("Finalizar nova venda", key="finalizar_nova"):
        if cliente_selecionado == "":
            st.error("Selecione um cliente.")
        elif not produtos:
            st.error("Adicione pelo menos um produto.")
        else:
            cliente_obj = clientes_dict[cliente_selecionado]
            venda = {
                "cliente_id": cliente_obj["id"],
                "cliente_nome": cliente_selecionado,
                "data": datetime.now().strftime("%Y-%m-%d"),
                "produtos": produtos,
                "servicos": [],
                "total": total_geral,
                "cancelada": False,
                "agendamento_id": None,
                "forma_pagamento": forma_pagamento
            }
            sucesso = salvar_venda(venda)
            if sucesso:
                st.success("Nova venda finalizada com sucesso!")
                st.session_state.pop("venda_produtos", None)
                st.experimental_rerun()

def historico_vendas():
    st.subheader("📋 Histórico de Vendas")

    vendas = carregar_vendas()

    if not vendas:
        st.info("Nenhuma venda cadastrada.")
        return

    for venda in vendas:
        col1, col2, col3, col4, col5, col6 = st.columns([2, 4, 3, 2, 2, 1])
        with col1:
            st.write(formatar_data_br(venda["data"]))
        with col2:
            st.write(venda["cliente_nome"])
        with col3:
            st.write(f"R$ {venda['total']:.2f}")
        with col4:
            st.write(venda.get("forma_pagamento", "Não informado"))
        with col5:
            st.write("Cancelada" if venda.get("cancelada") else "Ativa")
        with col6:
            if not venda.get("cancelada"):
                if st.button(f"❌ Cancelar {venda['id']}", key=f"cancelar_{venda['id']}"):
                    sucesso = cancelar_venda(venda["id"])
                    if sucesso:
                        st.success("Venda cancelada.")
                        st.experimental_rerun()
