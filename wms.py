import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="NextGen WMS", layout="wide")

# ==========================================
# CONEXÃO DO STREAMLIT COM GOOGLE SHEETS
# ==========================================
conn = st.connection("gsheets", type=GSheetsConnection)

def carregar_dados_nuvem():
    enderecos = []
    estoque = []
    
    # Lendo a aba Enderecos de forma segura
    try:
        df_end = conn.read(worksheet="Enderecos", ttl=0)
        if not df_end.empty and "endereco" in df_end.columns:
            enderecos = [str(x).upper().strip() for x in df_end["endereco"].dropna().tolist()]
    except Exception:
        pass
        
    # Lendo a aba Estoque de forma segura
    try:
        df_est = conn.read(worksheet="Estoque", ttl=0)
        if not df_est.empty and "id" in df_est.columns:
            for _, row in df_est.iterrows():
                estoque.append({
                    "id": int(row.get("id", 0)),
                    "endereco": str(row.get("endereco", "")).upper().strip(),
                    "produto": str(row.get("produto", "")).upper().strip(),
                    "quantidade": int(row.get("quantidade", 0)),
                    "lote": str(row.get("lote", "N/A")).upper().strip(),
                    "data": str(row.get("data", ""))
                })
    except Exception:
        pass
        
    return {"enderecos": sorted(list(set(enderecos))), "estoque": estoque}

def salvar_endereco_nuvem(novo_end):
    try:
        # Busca o que já existe na nuvem para não apagar dados anteriores
        try:
            df_atual = conn.read(worksheet="Enderecos", ttl=0)
        except Exception:
            df_atual = pd.DataFrame(columns=["endereco"])
            
        if df_atual.empty or "endereco" not in df_atual.columns:
            df_atual = pd.DataFrame(columns=["endereco"])
            
        df_novo = pd.DataFrame({"endereco": [str(novo_end).upper().strip()]})
        df_final = pd.concat([df_atual, df_novo], ignore_index=True)
        
        # Envia a atualização definitiva para a nuvem
        conn.update(worksheet="Enderecos", data=df_final)
        return True
    except Exception:
        return False

def salvar_entrada_nuvem(end, prod, qtd, lote):
    try:
        data_atual = datetime.now().strftime('%d/%m/%Y %H:%M')
        try:
            df_est = conn.read(worksheet="Estoque", ttl=0)
        except Exception:
            df_est = pd.DataFrame(columns=["id", "endereco", "produto", "quantidade", "lote", "data"])
            
        if df_est.empty or "id" not in df_est.columns:
            df_est = pd.DataFrame(columns=["id", "endereco", "produto", "quantidade", "lote", "data"])
            
        novo_id = int(df_est["id"].max()) + 1 if not df_est.empty else 1
        nova_linha = pd.DataFrame([{"id": novo_id, "endereco": end, "produto": prod, "quantidade": int(qtd), "lote": lote, "data": data_atual}])
        df_final = pd.concat([df_est, nova_linha], ignore_index=True)
        
        conn.update(worksheet="Estoque", data=df_final)
        return True
    except Exception:
        return False

# Inicialização da sessão
if 'bd' not in st.session_state:
    st.session_state.bd = carregar_dados_nuvem()

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

if st.sidebar.button("🔄 Sincronizar com Nuvem", use_container_width=True):
    st.session_state.bd = carregar_dados_nuvem()
    st.success("Dados sincronizados!")
    st.rerun()

opcao = st.sidebar.radio("Módulos", ["Visão Geral", "Cadastrar Endereço", "Entrada de Mercadoria", "Saída de Mercadoria"])

st.sidebar.write("---")
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
    m2.metric("Vagas Ocupadas", len(set([i["endereco"] for i in st.session_state.bd["estoque"] if int(i["quantidade"]) > 0])))
    m3.metric("Volume Total de Itens", sum([int(i["quantidade"]) for i in st.session_state.bd["estoque"]]))
    
    busca = st.text_input("Filtrar por endereço ou produto...").upper()
    tabela = []
    for i in st.session_state.bd["estoque"]:
        if (not busca) or (busca in str(i["endereco"]).upper() or busca in str(i["produto"]).upper()):
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
            novo_end = st.text_input("Código do Endereço").upper().strip()
            if st.form_submit_button("Confirmar Cadastro", type="primary", use_container_width=True):
                if novo_end and novo_end not in st.session_state.bd["enderecos"]:
                    if salvar_endereco_nuvem(novo_end):
                        st.success("Gravado com sucesso no Google Sheets!")
                        st.session_state.bd = carregar_dados_nuvem()
                        st.rerun()
                    else:
                        st.error("Erro ao enviar dados para a planilha.")
                elif novo_end in st.session_state.bd["enderecos"]:
                    st.warning("Este endereço já está cadastrado.")
    with c_lista:
        st.dataframe({"Lista de Endereços": st.session_state.bd["enderecos"]}, use_container_width=True, hide_index=True)

# ==========================================
# 3. ENTRADA DE MERCADORIA
# ==========================================
elif opcao == "Entrada de Mercadoria":
    st.markdown("## Recebimento e Alocação")
    if not st.session_state.bd["enderecos"]:
        st.error("Cadastre pelo menos um endereço antes de realizar a entrada.")
    else:
        with st.form("form_entrada", clear_on_submit=True):
            end = st.selectbox("Endereço de Destino", st.session_state.bd["enderecos"])
            prod = st.text_input("Código do Produto").upper().strip()
            qtd = st.number_input("Quantidade", min_value=1, value=1)
            lote = st.text_input("Lote", value="N/A").upper().strip()
            
            if st.form_submit_button("Confirmar Entrada", type="primary", use_container_width=True):
                if prod:
                    if salvar_entrada_nuvem(end, prod, qtd, lote):
                        st.success("Entrada registrada com sucesso na nuvem!")
                        st.session_state.bd = carregar_dados_nuvem()
                        st.rerun()
                    else:
                        st.error("Erro ao gravar entrada na nuvem.")
                else:
                    st.error("Informe o código do produto.")

# ==========================================
# 4. SAÍDA DE MERCADORIA
# ==========================================
elif opcao == "Saída de Mercadoria":
    st.markdown("## Separação e Baixa de Itens")
    st.info("Módulo pronto para homologação física.")




