import streamlit as st
from datetime import datetime
import json
import os

# Configuração de Layout e Identidade Visual do WMS
st.set_page_config(page_title="NextGen WMS", layout="wide", initial_sidebar_state="expanded")

ARQUIVO_BD = "wms_simplificado_db.json"

# ==========================================
# BANCO DE DADOS LOCAL
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
# TELA DE LOGIN CENTRALIZADA E REDUZIDA
# ==========================================
if 'logado' not in st.session_state:
    st.session_state.logado = False

if not st.session_state.logado:
    col_esq, col_login, col_dir = st.columns([1.5, 1.2, 1.5])
    
    with col_login:
        st.write("#")
        st.write("#")
        st.markdown("<h2 style='text-align: center;'>🔐 Painel WMS</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: gray;'>Insira suas credenciais corporativas</p>", unsafe_allow_html=True)
        
        with st.form("login_wms"):
            user = st.text_input("Usuário").strip()
            password = st.text_input("Senha", type="password").strip()
            botao_entrar = st.form_submit_button("Acessar Sistema", type="primary", use_container_width=True)
            
            if botao_entrar:
                if user == "admin" and password == "admin":
                    st.session_state.logado = True
                    st.rerun()
                else:
                    st.error("🔒 Usuário ou senha incorretos.")
    st.stop()

# ==========================================
# MENU LATERAL DESIGN CORPORATIVO
# ==========================================
st.sidebar.markdown("<h2 style='margin-bottom:0px;'>📦 WMS NextGen</h2>", unsafe_allow_html=True)
st.sidebar.markdown("<p style='color: gray; font-size:13px;'>Ambiente Logístico Ativo</p>", unsafe_allow_html=True)
st.sidebar.write(f"👤 Operador: `admin`")

st.sidebar.markdown("---")
opcao = st.sidebar.radio(
    "Navegação de Módulos", 
    ["📊 Visão Geral", "🧱 Cadastrar Endereço", "📥 Entrada de Mercadoria", "📤 Saída de Mercadoria"]
)
st.sidebar.markdown("---")

if st.sidebar.button("Efetuar Logout", type="secondary", use_container_width=True):
    st.session_state.logado = False
    st.rerun()

# ==========================================
# 1. VISÃO GERAL
# ==========================================
if opcao == "📊 Visão Geral":
    st.markdown("## 📊 Posição Geral e Indicadores de Estoque")
    st.markdown("Consulte os saldos consolidados e localizações físicas em tempo real.")
    st.write("#")
    
    total_enderecos = len(st.session_state.bd["enderecos"])
    posicoes_ocupadas = len(set([i["endereco"] for i in st.session_state.bd["estoque"] if i["quantidade"] > 0]))
    total_pecas = sum([i["quantidade"] for i in st.session_state.bd["estoque"]])
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Total de Endereços Ativos", total_enderecos)
    m2.metric("Vagas Ocupadas no Pátio", posicoes_ocupadas)
    m3.metric("Volume Total de Itens", total_pecas)
    
    st.write("#")
    st.markdown("### 🔍 Filtro Avançado de Posições")
    busca = st.text_input("Digite o endereço ou o código do produto para buscar...").upper()
    
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
            
    if tabela:
        st.dataframe(tabela, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum saldo localizado para os critérios informados.")

# ==========================================
# 2. CADASTRAR ENDEREÇO
# ==========================================
elif opcao == "🧱 Cadastrar Endereço":
    st.markdown("## 🧱 Mapeamento de Estrutura Física")
    st.markdown("Adicione novas localizações, box, prateleiras ou paletes ao sistema.")
    st.write("#")
    
    c_form, c_lista = st.columns([1.2, 1])
    
    with c_form:
        with st.form("cad_end", clear_on_submit=True):
            st.markdown("#### Informar Nova Localização")
            novo_end = st.text_input("Código do Endereço (Ex: RUA-A, PRATELEIRA-02, BOX-10)").upper().strip()
            
            if st.form_submit_button("Confirmar Cadastro", type="primary", use_container_width=True):
                if novo_end:
                    if novo_end not in st.session_state.bd["enderecos"]:
                        st.session_state.bd["enderecos"].append(novo_end)
                        salvar()
                        st.success(f"✅ Endereço '{novo_end}' integrado com sucesso!")
                        st.rerun()
                    else:
                        st.error("⚠️ Este código de endereço já consta na base do sistema.")
                else:
                    st.warning("Preencha o campo de endereço.")
                    
    with c_lista:
        st.markdown("#### Endereços Ativos")
        if st.session_state.bd["enderecos"]:
            st.dataframe({"Lista de Endereços Cadastrados": st.session_state.bd["enderecos"]}, use_container_width=True, hide_index=True)
        else:
            st.info("Nenhuma malha logística cadastrada até o momento.")

# ==========================================
# 3. ENTRADA DE MERCADORIA
# ==========================================
elif opcao == "📥 Entrada de Mercadoria":
    st.markdown("## 📥 Recebimento e Alocação de Mercadoria")
    st.markdown("Dê entrada direta informando o produto e o endereço de destino.")
    st.write("#")
    
    if not st.session_state.bd["enderecos"]:
        st.error("🛑 Erro operacional: Cadastre pelo menos um endereço na aba ao lado antes de levantar movimentações.")
    else:
        col_form_entrada, _ = st.columns([1.5, 1])
        with col_form_entrada:
            with st.form("form_entrada", clear_on_submit=True):
                st.markdown("#### Dados do Documento de Entrada")
                end = st.selectbox("Endereço de Destino", st.session_state.bd["enderecos"])
                prod = st.text_input("Código/SKU do Produto").upper().strip()
                
                c1, c2 = st.columns(2)
                qtd = c1.number_input("Quantidade de Volumes", min_value=1, value=1)
                lote = c2.text_input("Número do Lote / Série", value="N/A").upper().strip()
                
                if st.form_submit_button("Confirmar Entrada no Pátio", type="primary", use_container_width=True):
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
                        st.success(f"✅ Sucesso: {qtd} un do item {prod} alocados na posição {end}.")
                        st.rerun()
                    else:
                        st.warning("Preencha o código do produto.")

# ==========================================
# 4. SAÍDA DE MERCADORIA
# ==========================================
elif opcao == "📤 Saída de Mercadoria":
    st.markdown("## 📤 Expedição e Separação de Pedidos (Picking)")
    st.markdown("Dê baixa nos saldos armazenados. Itens zerados somem automaticamente da malha de estoque.")
    st.write("#")
    
    itens_disponiveis = [i for i in st.session_state.bd["estoque"] if i["quantidade"] > 0]
    
    if not itens_disponiveis:
        st.info("📭 Estoque zerado. Não há saldos físicos disponíveis para expedição no momento.")
    else:
        col_form_saida, _ = st.columns([1.5, 1])
        with col_form_saida:
            lista_saida = [f"📍 Local: {x['endereco']} | 📦 SKU: {x['produto']} | 🏷️ Lote: {x['lote']} (Saldo Atual: {x['quantidade']})" for x in itens_disponiveis]
            
            with st.form("form_saida"):
                st.markdown("#### Dados de Separação")
                selecionado = st.selectbox("Selecione o Item Alocado", lista_saida)
                qtd_retirar = st.number_input("Quantidade para Retirada", min_value=1, value=1)
                
                if st.form_submit_button("Confirmar Baixa do Estoque", type="primary", use_container_width=True):
                    idx = lista_saida.index(selecionado)
                    item_estoque = itens_disponiveis[idx]
                    
                    if qtd_retirada > item_estoque["quantidade"]:
                        st.error(f"❌ Erro operacional: Quantidade solicitada é maior que o saldo real ({item_estoque['quantidade']}).")
                    else:
                        item_estoque["quantidade"] -= qtd_retirada






