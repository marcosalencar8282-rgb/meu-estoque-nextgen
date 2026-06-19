import streamlit as st
from datetime import datetime
import json
import os

st.set_page_config(page_title="WMS Simplificado", layout="wide")
ARQUIVO_BD = "wms_simplificado_db.json"

# ==========================================
# BANCO DE DADOS SIMPLES
# ==========================================
if 'bd' not in st.session_state:
    if os.path.exists(ARQUIVO_BD):
        try:
            with open(ARQUIVO_BD, 'r', encoding='utf-8') as f:
                st.session_state.bd = json.load(f)
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
    st.title("🔑 Acesso ao WMS")
    with st.form("login"):
        user = st.text_input("Usuário").strip()
        password = st.text_input("Senha", type="password").strip()
        if st.form_submit_button("Entrar", type="primary"):
            if user == "admin" and password == "admin":
                st.session_state.logado = True
                st.rerun()
            else:
                st.error("Incorreto.")
    st.stop()

# ==========================================
# MENU LATERAL
# ==========================================
st.sidebar.title("WMS Simplificado")
if st.sidebar.button("Sair / Logout"):
    st.session_state.logado = False
    st.rerun()

opcao = st.sidebar.radio("Módulos", ["Visão Geral", "Cadastrar Endereço", "Entrada", "Saída"])

# ==========================================
# 1. VISÃO GERAL
# ==========================================
if opcao == "Visão Geral":
    st.title("📊 Posição do Estoque")
    busca = st.text_input("Buscar por Endereço ou Produto").upper()
    
    tabela = []
    for i in st.session_state.bd["estoque"]:
        if (not busca) or (busca in i["endereco"] or busca in i["produto"]):
            tabela.append(i)
            
    st.dataframe(tabela, use_container_width=True)

# ==========================================
# 2. CADASTRAR ENDEREÇO
# ==========================================
elif opcao == "Cadastrar Endereço":
    st.title("🧱 Cadastrar Novo Endereço")
    with st.form("cad_end", clear_on_submit=True):
        novo_end = st.text_input("Código do Endereço (Ex: A-01, BOX-2)").upper().strip()
        if st.form_submit_button("Salvar Endereço", type="primary"):
            if novo_end:
                if novo_end not in st.session_state.bd["enderecos"]:
                    st.session_state.bd["enderecos"].append(novo_end)
                    salvar()
                    st.success(f"Endereço {novo_end} salvo!")
                else:
                    st.error("Já existe.")

# ==========================================
# 3. ENTRADA DE MERCADORIA
# ==========================================
elif opcao == "Entrada":
    st.title("📥 Entrada Direta no Estoque")
    if not st.session_state.bd["enderecos"]:
        st.warning("Cadastre pelo menos um endereço primeiro.")
    else:
        with st.form("form_entrada", clear_on_submit=True):
            end = st.selectbox("Selecione o Endereço", st.session_state.bd["enderecos"])
            prod = st.text_input("Código do Produto").upper().strip()
            qtd = st.number_input("Quantidade", min_value=1, value=1)
            lote = st.text_input("Lote", value="N/A").upper().strip()
            
            if st.form_submit_button("Confirmar Entrada", type="primary"):
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
                    st.success("Entrada realizada!")
                    st.rerun()

# ==========================================
# 4. SAÍDA (PRODUTO SOME QUANDO ZERA)
# ==========================================
elif opcao == "Saída":
    st.title("📤 Saída de Mercadoria")
    
    # Filtra apenas o que tem saldo maior que zero
    itens_disponiveis = [i for i in st.session_state.bd["estoque"] if i["quantidade"] > 0]
    
    if not itens_disponiveis:
        st.info("Nenhum produto com saldo no estoque.")
    else:
        lista_saida = [f"Endereço: {x['endereco']} | Prod: {x['produto']} | Lote: {x['lote']} (Saldo: {x['quantidade']})" for x in itens_disponiveis]
        
        with st.form("form_saida"):
            selecionado = st.selectbox("Selecione o Item para Retirada", lista_saida)
            qtd_retirar = st.number_input("Quantidade a Retirar", min_value=1, value=1)
            
            if st.form_submit_button("Confirmar Saída", type="primary"):
                idx = lista_saida.index(selecionado)
                item_estoque = itens_disponiveis[idx]
                
                if qtd_retirada > item_estoque["quantidade"]:
                    st.error("Saldo insuficiente.")
                else:
                    item_estoque["quantidade"] -= qtd_retirada
                    item_estoque["data"] = datetime.now().strftime('%d/%m/%Y %H:%M')
                    
                    # LOGICA SOLICITADA: Se o produto zerar, ele é deletado do banco e some da tela
                    if item_estoque["quantidade"] == 0:
                        st.session_state.bd["estoque"].remove(item_estoque)
                        
                    salvar()
                    st.success("Baixa processada!")
                    st.rerun()








