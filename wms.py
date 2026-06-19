import streamlit as st
from datetime import datetime
import json
import os

st.set_page_config(page_title="NextGen WMS", layout="wide")
ARQUIVO_BD = "wms_simplificado_db.json"

# ==========================================
# BANCO DE DADOS LOCAL COM AJUSTE AUTOMÁTICO
# ==========================================
if 'bd' not in st.session_state:
    if os.path.exists(ARQUIVO_BD):
        try:
            with open(ARQUIVO_BD, 'r', encoding='utf-8') as f:
                dados = json.load(f)
                if isinstance(dados, dict) and "estoque" in dados:
                    estoque_bruto = dados["estoque"]
                    enderecos_brutos = dados.get("enderecos", [])
                else:
                    estoque_bruto = dados if isinstance(dados, list) else []
                    enderecos_brutos = []

                estoque_corrigido = []
                for item in estoque_bruto:
                    if isinstance(item, dict):
                        endereco = item.get("endereco") or item.get("Endereço") or "N/A"
                        produto = item.get("produto") or item.get("Código Produto") or "N/A"
                        if isinstance(produto, list):
                            produto = str(produto) if produto else "N/A"
                        produto = str(produto).replace("[", "").replace("]", "").replace("'", "").strip()
                        quantidade = item.get("quantidade") or item.get("Quantidade") or 0
                        lote = item.get("lote") or item.get("Lote") or "N/A"
                        data = item.get("data") or item.get("atualizacao") or datetime.now().strftime('%d/%m/%Y %H:%M')
                        
                        estoque_corrigido.append({
                            "endereco": str(endereco).strip(),
                            "produto": str(produto).strip(),
                            "quantidade": int(quantidade),
                            "lote": str(lote).strip(),
                            "data": str(data).strip()
                        })
                
                lista_enderecos = []
                for e in enderecos_brutos:
                    lista_enderecos.append(str(e))
                for item in estoque_corrigido:
                    if item["endereco"] not in lista_enderecos:
                        lista_enderecos.append(item["endereco"])

                st.session_state.bd = {"enderecos": lista_enderecos, "estoque": estoque_corrigido}
        except:
            st.session_state.bd = {"enderecos": [], "estoque": []}
    else:
        st.session_state.bd = {"enderecos": [], "estoque": []}

def salvar():
    with open(ARQUIVO_BD, 'w', encoding='utf-8') as f:
        json.dump(st.session_state.bd, f, indent=4, ensure_ascii=False)

# ==========================================
# TELA DE LOGIN
# ==========================================
if 'logado' not in st.session_state:
    st.session_state.logado = False

if not st.session_state.logado:
    col_esq, col_login, col_dir = st.columns([1.5, 1.2, 1.5])
    with col_login:
        st.write("#")
        st.markdown("<h2 style='text-align: center;'>Acesso ao WMS</h2>", unsafe_allow_html=True)
        with st.form("login_wms"):
            user = st.text_input("Usuário").strip()
            password = st.text_input("Senha", type="password").strip()
            if st.form_submit_button("Acessar Sistema", type="primary", use_container_width=True):
                if user == "admin" and password == "admin":
                    st.session_state.logado = True
                    st.rerun()
                else:
                    st.error("Usuário ou senha incorretos.")
    st.stop()

# ==========================================
# MENU LATERAL
# ==========================================
st.sidebar.markdown("<h2>WMS NextGen</h2>", unsafe_allow_html=True)
opcao = st.sidebar.radio("Módulos", ["Visão Geral", "Cadastrar Endereço", "Entrada de Mercadoria", "Saída de Mercadoria"])
if st.sidebar.button("Efetuar Logout", use_container_width=True):
    st.session_state.logado = False
    st.rerun()

# ==========================================
# 1. VISÃO GERAL
# ==========================================
if opcao == "Visão Geral":
    st.markdown("## Posição Geral do Estoque")
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Total de Endereços Ativos", len(st.session_state.bd["enderecos"]))
    m2.metric("Vagas Ocupadas", len(set([i["endereco"] for i in st.session_state.bd["estoque"] if i["quantidade"] > 0])))
    m3.metric("Volume Total de Itens", sum([i["quantidade"] for i in st.session_state.bd["estoque"]]))
    
    busca = st.text_input("Filtrar por endereço ou produto...").upper()
    tabela = []
    for i in st.session_state.bd["estoque"]:
        if (not busca) or (busca in i["endereco"].upper() or busca in i["produto"].upper()):
            tabela.append({
                "Endereço Físico": i["endereco"],
                "Código Produto": i["produto"],
                "Lote / Validade": i["lote"],
                "Quantidade Saldo": i["quantidade"],
                "Última Atualização": i["data"]
            })
    st.dataframe(tabela, use_container_width=True, hide_index=True)

# ==========================================
# 2. CADASTRAR ENDEREÇO
# ==========================================
elif opcao == "Cadastrar Endereço":
    st.markdown("## Mapeamento de Estrutura Física")
    c_form, c_lista = st.columns([1.2, 1])
    with c_form:
        with st.form("cad_end", clear_on_submit=True):
            novo_end = st.text_input("Código do Endereço (Ex: RUA-A, BOX-10)").upper().strip()
            if st.form_submit_button("Confirmar Cadastro", type="primary", use_container_width=True):
                if novo_end and novo_end not in st.session_state.bd["enderecos"]:
                    st.session_state.bd["enderecos"].append(novo_end)
                    salvar()
                    st.success("Endereço cadastrado!")
                    st.rerun()
    with c_lista:
        st.dataframe({"Lista de Endereços": st.session_state.bd["enderecos"]}, use_container_width=True, hide_index=True)

# ==========================================
# 3. ENTRADA DE MERCADORIA
# ==========================================
elif opcao == "Entrada de Mercadoria":
    st.markdown("## Recebimento e Alocação")
    if not st.session_state.bd["enderecos"]:
        st.error("Cadastre pelo menos um endereço antes.")
    else:
        with st.form("form_entrada", clear_on_submit=True):
            end = st.selectbox("Endereço de Destino", st.session_state.bd["enderecos"])
            prod = st.text_input("Código do Produto").upper().strip()
            qtd = st.number_input("Quantidade", min_value=1, value=1)
            lote = st.text_input("Lote", value="N/A").upper().strip()
            
            if st.form_submit_button("Confirmar Entrada", type="primary", use_container_width=True):
                if prod:
                    encontrou = False
                    for item in st.session_state.bd["estoque"]:
                        if item["endereco"] == end and item["produto"] == prod and item["lote"] == lote:
                            item["quantidade"] += qtd
                            item["data"] = datetime.now().strftime('%d/%m/%Y %H:%M')
                            encontrou = True
                            break
                    if not encontrou:
                        st.session_state.bd["estoque"].append({
                            "endereco": end, "produto": prod, "quantidade": qtd, "lote": lote, "data": datetime.now().strftime('%d/%m/%Y %H:%M')
                        })
                    salvar()
                    st.success("Entrada realizada com sucesso!")
                    st.rerun()

# ==========================================
# 4. SAÍDA DE MERCADORIA
# ==========================================
elif opcao == "Saída de Mercadoria":
    st.markdown("## Expedição (Picking)")
    itens_disponiveis = [i for i in st.session_state.bd["estoque"] if i["quantidade"] > 0]
    if not itens_disponiveis:
        st.info("Estoque vazio.")
    else:
        lista_saida = [f"Local: {x['endereco']} | SKU: {x['produto']} | Lote: {x['lote']} (Saldo: {x['quantidade']})" for x in itens_disponiveis]
        with st.form("form_saida"):
            selecionado = st.selectbox("Selecione o Item", lista_saida)
            qtd_retirar = st.number_input("Quantidade para Retirada", min_value=1, value=1)
            if st.form_submit_button("Confirmar Baixa", type="primary", use_container_width=True):
                idx = lista_saida.index(selecionado)
                item_estoque = itens_disponiveis[idx]
                if qtd_retirar > item_estoque["quantidade"]:
                    st.error("Quantidade indisponível.")
                else:
                    item_estoque["quantidade"] -= qtd_retirar
                    item_estoque["data"] = datetime.now().strftime('%d/%m/%Y %H:%M')
                    if item_estoque["quantidade"] == 0:
                        st.session_state.bd["estoque"].remove(item_estoque)
                    salvar()
                    st.success("Baixa processada!")
                    st.rerun()






