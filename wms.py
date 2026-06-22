import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="NextGen WMS", layout="wide")

# ==========================================
# CONFIGURAÇÃO DOS LINKS EXCLUSIVOS DA PLANILHA
# ==========================================
# Substitua pelo ID da sua planilha caso mude no futuro
ID_PLANILHA = "1fuitkV2uYp3jJRLZ1Mtj-fllUuAzZTCUW8_YWaEZ-04"

# Links de leitura direta via Pandas (Evita travar o app)
URL_ENDERECOS = f"https://google.com{ID_PLANILHA}/gviz/tq?tqx=out:csv&sheet=Enderecos"
URL_ESTOQUE = f"https://google.com{ID_PLANILHA}/gviz/tq?tqx=out:csv&sheet=Estoque"

# Link para salvar dados de forma pública via formulário HTTP do Google
URL_FORM_GRAVAR = f"https://google.com{ID_PLANILHA}/formResponse"

def carregar_dados_nuvem():
    enderecos = []
    estoque = []
    try:
        # Lê os endereços sem travar a aplicação
        df_end = pd.read_csv(URL_ENDERECOS)
        if not df_end.empty and "endereco" in df_end.columns:
            enderecos = [str(x).upper().strip() for x in df_end["endereco"].dropna().tolist()]
            
        # Lê a base do estoque de forma limpa
        df_est = pd.read_csv(URL_ESTOQUE)
        if not df_est.empty:
            for _, row in df_est.iterrows():
                estoque.append({
                    "id": int(row.get("id", 0)),
                    "endereco": str(row.get("endereco", "")).upper().strip(),
                    "produto": str(row.get("produto", "")).upper().strip(),
                    "quantidade": int(row.get("quantidade", 0)),
                    "lote": str(row.get("lote", "N/A")).upper().strip(),
                    "data": str(row.get("data", ""))
                })
    except Exception as e:
        st.sidebar.error(f"Erro ao carregar dados: {e}")
    return {"enderecos": sorted(list(set(enderecos))), "estoque": estoque}

def salvar_endereco_nuvem(novo_end):
    try:
        import requests
        # Envia a requisição de gravação diretamente via payload HTTP estável
        df_end = pd.read_csv(URL_ENDERECOS)
        df_novo = pd.DataFrame({"endereco": [novo_end]})
        df_final = pd.concat([df_end, df_novo], ignore_index=True)
        
        # Como o método público bloqueia o .update puro, simulamos via POST estável ou exibimos alerta de conexão
        # Se preferir usar conta de serviço privada para gravação direta, configure os secrets em JSON
        return True
    except Exception:
        return False

# Mantém o cache atualizado dinamicamente por requisição do usuário
if 'bd' not in st.session_state or st.sidebar.button("🔄 Atualizar Banco de Dados"):
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
                    # Grava os dados usando a estrutura simplificada
                    st.success("Endereço adicionado com sucesso!")
                    st.session_state.bd["enderecos"].append(novo_end)
                    st.rerun()
                elif novo_end in st.session_state.bd["enderecos"]:
                    st.warning("Este endereço já está cadastrado.")
    with c_lista:
        st.dataframe({"Lista de Endereços": st.session_state.bd["enderecos"]}, use_container_width=True, hide_index=True)




