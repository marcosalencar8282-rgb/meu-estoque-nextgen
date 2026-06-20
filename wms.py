import streamlit as st
from datetime import datetime
import pandas as pd
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="NextGen WMS", layout="wide")

# ==========================================
# CONEXÃO COM O BANCO DE DADOS (GOOGLE SHEETS)
# ==========================================
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception:
    st.error("Erro ao conectar ao banco de dados. Verifique os Secrets.")
    st.stop()

def carregar_dados_nuvem():
    try:
        df_estoque = conn.read(worksheet="estoque", ttl=0)
        df_estoque = df_estoque.dropna(how="all")
        if not df_estoque.empty:
            df_estoque['quantidade'] = pd.to_numeric(df_estoque['quantidade'], errors='coerce').fillna(0).astype(int)
            df_estoque = df_estoque.fillna("N/A")
            estoque = df_estoque.to_dict(orient='records')
        else:
            estoque = []
    except Exception:
        estoque = []

    try:
        df_end = conn.read(worksheet="enderecos", ttl=0)
        df_end = df_end.dropna(how="all")
        if not df_end.empty and "endereco" in df_end.columns:
            enderecos = df_end['endereco'].astype(str).tolist()
        else:
            enderecos = []
    except Exception:
        enderecos = []

    return {"enderecos": enderecos, "estoque": estoque}

def salvar_na_nuvem():
    try:
        # Força a conversão correta dos dados antes de enviar para a planilha
        df_est = pd.DataFrame(st.session_state.bd["estoque"])
        if not df_est.empty:
            df_est['quantidade'] = df_est['quantidade'].astype(int)
            df_est = df_est[['endereco', 'produto', 'quantidade', 'lote', 'data']]
        else:
            df_est = pd.DataFrame(columns=['endereco', 'produto', 'quantidade', 'lote', 'data'])
            
        df_end = pd.DataFrame({"endereco": st.session_state.bd["enderecos"]})
        
        # Limpa linhas vazias e envia de forma limpa
        conn.update(worksheet="estoque", data=df_est)
        conn.update(worksheet="enderecos", data=df_end)
    except Exception as e:
        st.error(f"Erro ao salvar dados no banco: {e}")

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
            novo_end = st.text_input("Código do Endereço (Ex: RUA-A, BOX-10)").upper().strip()
            if st.form_submit_button("Confirmar Cadastro", type="primary", use_container_width=True):
                if novo_end and novo_end not in st.session_state.bd["enderecos"]:
                    st.session_state.bd["enderecos"].append(novo_end)
                    salvar_na_nuvem()
                    st.success("Endereço salvo permanentemente no banco!")
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
                        if str(item["endereco"]) == str(end) and str(item["produto"]) == str(prod) and str(item["lote"]) == str(lote):
                            item["quantidade"] = int(item["quantidade"]) + int(qtd)
                            item["data"] = datetime.now().strftime('%d/%m/%Y %H:%M')
                            encontrou = True
                            break
                    if not encontrou:
                        st.session_state.bd["estoque"].append({
                            "endereco": end, "produto": prod, "quantidade": int(qtd), "lote": lote, "data": datetime.now().strftime('%d/%m/%Y %H:%M')
                        })
                    salvar_na_nuvem()
                    st.success("Entrada salva permanentemente no banco!")
                    st.rerun()

# ==========================================
# 4. SAÍDA DE MERCADORIA
# ==========================================
elif opcao == "Saída de Mercadoria":
    st.markdown("## Expedição (Picking)")
    itens_disponiveis = [i for i in st.session_state.bd["estoque"] if int(i["quantidade"]) > 0]
    if not itens_disponiveis:
        st.info("Estoque vazio.")
    else:
        with st.form("form_saida", clear_on_submit=True):
            opcoes_saida = [f"Local: {x['endereco']} | SKU: {x['produto']} | Lote: {x['lote']} (Saldo: {x['quantidade']})" for x in itens_disponiveis]
            item_selecionado_texto = st.selectbox("Selecione o item para dar saída", opcoes_saida)
            qtd_saida = st.number_input("Quantidade de Saída", min_value=1, value=1)
            
            if st.form_submit_button("Confirmar Saída", type="primary", use_container_width=True):
                idx_selecionado = opcoes_saida.index(item_selecionado_texto)
                item_estoque = itens_disponiveis[idx_selecionado]
                
                if int(qtd_saida) > int(item_estoque["quantidade"]):
                    st.error(f"Quantidade indisponível. Saldo atual: {item_estoque['quantidade']}")
                else:
                    item_estoque["quantidade"] = int(item_estoque["quantidade"]) - int(qtd_saida)
                    item_estoque["data"] = datetime.now().strftime('%d/%m/%Y %H:%M')
                    salvar_na_nuvem()
                    st.success("Saída salva permanentemente no banco!")
                    st.rerun()





