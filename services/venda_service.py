def vendas():
    st.title("💰 Painel de Vendas")
    st.markdown("---")

    opcao_venda = st.radio("Escolha o tipo de venda:", ["Venda por Agendamento", "Nova Venda"])

    # Carregar dados do supabase
    clientes = supabase.table("clientes").select("id,nome").execute().data
    clientes_dict = {c["nome"]: c["id"] for c in clientes} if clientes else {}

    produtos = supabase.table("produtos").select("id,nome,quantidade,preco_venda").gt("quantidade", 0).execute().data
    produtos_dict = {p["nome"]: p for p in produtos} if produtos else {}

    servicos = supabase.table("servicos").select("id,nome,quantidade,valor").gt("quantidade", 0).execute().data
    servicos_dict = {s["nome"]: s for s in servicos} if servicos else {}

    if opcao_venda == "Venda por Agendamento":
        # Buscar agendamentos com status 'Agendado'
        agendamentos = supabase.table("agendamentos")\
            .select("id,cliente_id,data,hora,servicos,status")\
            .eq("status", "Agendado")\
            .order("data", ascending=True).order("hora", ascending=True).execute().data

        if not agendamentos:
            st.info("Nenhum agendamento disponível para venda.")
            return

        # Montar dicionário para selectbox
        agend_dict = {
            f"{formatar_data_br(a['data'])} {a['hora']} - {clientes_dict.get(a['cliente_id'], 'Cliente Desconhecido')}": a
            for a in agendamentos
        }

        agendamento_selecionado = st.selectbox("Selecione o agendamento", [""] + list(agend_dict.keys()), key="agendamento")

        if agendamento_selecionado:
            ag = agend_dict[agendamento_selecionado]
            cliente_id = ag["cliente_id"]

            # Exibir dados do agendamento
            st.markdown(f"""
                **Cliente:** {list(clientes_dict.keys())[list(clientes_dict.values()).index(cliente_id)]}  
                **Data:** {formatar_data_br(ag['data'])}  
                **Hora:** {ag['hora']}  
                **Serviços Agendados:** {ag['servicos']}
            """)

            # Itens iniciais da prevenda - os serviços agendados
            servicos_agendados = [s.strip() for s in ag["servicos"].split(",") if s.strip()]
            itens_venda = []
            for serv_nome in servicos_agendados:
                if serv_nome in servicos_dict:
                    s = servicos_dict[serv_nome]
                    itens_venda.append({
                        "tipo": "servico",
                        "id": s["id"],
                        "nome": serv_nome,
                        "quantidade": 1,
                        "preco": s["valor"]
                    })

            # Adicionar produtos e serviços extras
            st.markdown("---")
            st.markdown("### ➕ Adicionar Itens Extras")

            col1, col2 = st.columns(2)
            with col1:
                produtos_selecionados = st.multiselect("Produtos", list(produtos_dict.keys()), key="produtos_ag")
                for p in produtos_selecionados:
                    if not any(item["nome"] == p for item in itens_venda):
                        pr = produtos_dict[p]
                        itens_venda.append({
                            "tipo": "produto",
                            "id": pr["id"],
                            "nome": p,
                            "quantidade": 1,
                            "preco": pr["preco_venda"]
                        })
            with col2:
                servicos_selecionados = st.multiselect(
                    "Serviços", 
                    [s for s in servicos_dict.keys() if s not in servicos_agendados], 
                    key="servicos_ag")
                for s_nome in servicos_selecionados:
                    if not any(item["nome"] == s_nome for item in itens_venda):
                        sv = servicos_dict[s_nome]
                        itens_venda.append({
                            "tipo": "servico",
                            "id": sv["id"],
                            "nome": s_nome,
                            "quantidade": 1,
                            "preco": sv["valor"]
                        })

            # Exibir itens com opção de alterar quantidade
            st.markdown("---")
            st.markdown("### 🧾 Itens da Venda")
            total = 0
            for i, item in enumerate(itens_venda):
                qtd = st.number_input(f"{item['nome']} ({item['tipo']})", min_value=1, value=item["quantidade"], step=1, key=f"qtd_ag_{i}")
                itens_venda[i]["quantidade"] = qtd
                total += qtd * item["preco"]

            forma_pagamento = st.selectbox("Forma de pagamento", ["Dinheiro", "Cartão", "Pix"], key="fp_ag")

            st.success(f"Total: R$ {total:.2f}")

            if st.button("✅ Finalizar Venda", key="finalizar_ag"):
                if total > 0:
                    data_venda = date.today().strftime("%Y-%m-%d")

                    # Inserir venda
                    res = supabase.table("vendas").insert({
                        "cliente_id": cliente_id,
                        "data": data_venda,
                        "total": total,
                        "forma_pagamento": forma_pagamento,
                        "cancelada": False
                    }).execute()
                    venda_id = res.data[0]["id"]

                    # Inserir itens da venda
                    for item in itens_venda:
                        supabase.table("venda_itens").insert({
                            "venda_id": venda_id,
                            "tipo": item["tipo"],
                            "item_id": item["id"],
                            "quantidade": item["quantidade"],
                            "preco": item["preco"]
                        }).execute()

                        # Atualizar estoque para produtos
                        if item["tipo"] == "produto":
                            supabase.table("produtos").update({
                                "quantidade": supabase.table("produtos").select("quantidade").eq("id", item["id"]).execute().data[0]["quantidade"] - item["quantidade"]
                            }).eq("id", item["id"]).execute()

                    # Atualizar status do agendamento para 'Finalizado'
                    supabase.table("agendamentos").update({"status": "Finalizado"}).eq("id", ag["id"]).execute()

                    st.success("🎉 Venda por agendamento realizada com sucesso!")
                    st.experimental_rerun()

    else:  # Nova Venda
        cliente_selecionado = st.selectbox("Selecione o cliente", [""] + list(clientes_dict.keys()), key="cliente_nv")
        if cliente_selecionado:
            cliente_id = clientes_dict[cliente_selecionado]

            produtos_selecionados = st.multiselect("Produtos", list(produtos_dict.keys()), key="produtos_nv")
            servicos_selecionados = st.multiselect("Serviços", list(servicos_dict.keys()), key="servicos_nv")

            itens_venda = []
            for p in produtos_selecionados:
                pr = produtos_dict[p]
                itens_venda.append({
                    "tipo": "produto",
                    "id": pr["id"],
                    "nome": p,
                    "quantidade": 1,
                    "preco": pr["preco_venda"]
                })
            for s in servicos_selecionados:
                sv = servicos_dict[s]
                itens_venda.append({
                    "tipo": "servico",
                    "id": sv["id"],
                    "nome": s,
                    "quantidade": 1,
                    "preco": sv["valor"]
                })

            st.markdown("---")
            st.markdown("### 🧾 Itens da Venda")
            total = 0
            for i, item in enumerate(itens_venda):
                qtd = st.number_input(f"{item['nome']} ({item['tipo']})", min_value=1, value=item["quantidade"], step=1, key=f"qtd_nv_{i}")
                itens_venda[i]["quantidade"] = qtd
                total += qtd * item["preco"]

            forma_pagamento = st.selectbox("Forma de pagamento", ["Dinheiro", "Cartão", "Pix"], key="fp_nv")

            st.success(f"Total: R$ {total:.2f}")

            if st.button("✅ Finalizar Venda", key="finalizar_nv"):
                if total > 0:
                    data_venda = date.today().strftime("%Y-%m-%d")
                    res = supabase.table("vendas").insert({
                        "cliente_id": cliente_id,
                        "data": data_venda,
                        "total": total,
                        "forma_pagamento": forma_pagamento,
                        "cancelada": False
                    }).execute()
                    venda_id = res.data[0]["id"]

                    for item in itens_venda:
                        supabase.table("venda_itens").insert({
                            "venda_id": venda_id,
                            "tipo": item["tipo"],
                            "item_id": item["id"],
                            "quantidade": item["quantidade"],
                            "preco": item["preco"]
                        }).execute()

                        if item["tipo"] == "produto":
                            atual_qtd = supabase.table("produtos").select("quantidade").eq("id", item["id"]).execute().data[0]["quantidade"]
                            supabase.table("produtos").update({
                                "quantidade": atual_qtd - item["quantidade"]
                            }).eq("id", item["id"]).execute()

                    st.success("🎉 Venda realizada com sucesso!")
                    st.experimental_rerun()
        else:
            st.warning("Selecione um cliente para continuar.")

    # --- Histórico de Vendas ---
    st.markdown("---")
    st.subheader("📋 Histórico de Vendas")

    vendas = supabase.table("vendas")\
        .select("id, cliente_id, data, total, forma_pagamento, cancelada")\
        .order("data", descending=True)\
        .execute().data

    if not vendas:
        st.info("Nenhuma venda registrada.")
        return

    # Obter nomes dos clientes para exibir
    clientes_info = supabase.table("clientes").select("id,nome").execute().data
    clientes_map = {c["id"]: c["nome"] for c in clientes_info}

    for v in vendas:
        nome_cliente = clientes_map.get(v["cliente_id"], "Cliente Desconhecido")
        col1, col2, col3, col4, col5 = st.columns([3, 3, 2, 2, 1])
        with col1:
            st.write(nome_cliente)
        with col2:
            st.write(formatar_data_br(v["data"]))
        with col3:
            st.write(f"R$ {v['total']:.2f}")
        with col4:
            st.write(v["forma_pagamento"])
        with col5:
            if not v["cancelada"]:
                if st.button(f"❌ Cancelar {v['id']}", key=f"cancelar_{v['id']}"):
                    # Atualizar venda para cancelada = True
                    supabase.table("vendas").update({"cancelada": True}).eq("id", v["id"]).execute()
                    st.success("Venda cancelada!")
                    st.experimental_rerun()
            else:
                st.write("Cancelada")

