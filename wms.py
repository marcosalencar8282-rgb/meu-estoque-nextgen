import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="NextGen WMS", layout="wide")

# ==========================================
# CONEXÃO OFICIAL COM GOOGLE SHEETS
# ==========================================
conn = st.connection("gsheets", type=GSheetsConnection)

def carregar_dados_nuvem():
    enderecos = []
    estoque = []
    try:
        df_end = conn.read(worksheet="Enderecos", ttl=0)
        if not df_end.empty and "endereco" in df_end.columns:
            enderecos = [str(x).upper().strip() for x in df_end["endereco"].dropna().tolist()]
            
        df_est = conn.read(worksheet="Estoque", ttl=0)
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
    except Exception:
        pass
    return {"enderecos": sorted(list(set(enderecos))), "estoque": estoque}

def salvar_endereco_nuvem(novo_end):
    try:
        df_atual = conn.read(worksheet="Enderecos", ttl=0)
        df_novo = pd.DataFrame({"endereco": [novo_end]})
        df_final = pd.concat([df_atual, df_novo], ignore_index=True)
        conn.update(worksheet="Enderecos", data=df_final)
        return True
    except Exception:
        return False

def salvar_entrada_nuvem(end, prod, qtd, lote):
    try:
        data_atual = datetime.now().strftime('%d/%m/%Y %H:%M')
        df_est = conn.read(worksheet="Estoque", ttl=0)
        
        if not df_est.empty:
            df_est["quantidade"] = df_est["quantidade"].astype(int)
            df_est["id"] = df_est["id"].astype(int)
            
            filtro = (df_est["endereco"].str.upper() == end.upper()) & \
                     (df_est["produto"].str.upper() == prod.upper()) & \
                     (df_est["lote"].str.upper() == lote.upper())
            
            if filtro.any():
                df_est.loc[filtro, "quantidade"] += int(qtd)
                df_est.loc[filtro, "data"] = data_atual
            else:
                novo_id = int(df_est["id"].max()) + 1
                nova_linha = pd.DataFrame([{"id": novo_id, "endereco": end, "produto": prod, "quantidade": int(qtd), "lote": lote, "data": data_atual}])
                df_est = pd.concat([df_est, nova_linha], ignore_index=True)
        else:
            df_est = pd.DataFrame([{"id": 1, "endereco": end, "produto": prod, "quantidade": int(qtd), "lote": lote, "data": data_atual}])
            
        conn.update(worksheet="Estoque", data=df_est)
        return True
    except Exception:
        return False

def salvar_saida_nuvem(item_id, nova_qtd):
    try:
        data_atual = datetime.now().strftime('%d/%m/%Y %H:%M')
        df_est = conn.read(worksheet="Estoque", ttl=0)
        
        if not df_est.empty:
            df_est["id"] = df_est["id"].astype(int)
            if int(nova_qtd) <= 0:
                df_est = df_est[df_est["id"] != int(item_id)]
            else:
                df_est.loc[df_est["id"] == int(item_id), "quantidade"] = int(nova_qtd)
                df_est.loc[df_est["id"] == int(item_id), "data"] = data_atual
                
            conn.update(worksheet="Estoque", data=df_est)
            return True
        return False
    except Exception:
        return False

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
                    if salvar_endereco_nuvem(novo_end):
                        st.success("Endereço salvo permanentemente no Google Sheets!")
                        st.rerun()
                    else:
                        st.error("Erro ao gravar dados na planilha Google.")
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
        st.error("Cadastre pelo menos um endereço antes.")
    else:
        with st.form("form_entrada", clear_on_submit=True):
            end = st.selectbox("Endereço de Destino", st.session_state.bd["enderecos"])
            prod = st.text_input("Código do Produto").upper().strip()
            qtd = st.number_input("Quantidade", min_value=1, value=1)
            lote = st.text_input("Lote", value="N/A").upper().strip()
            
            if st.form_submit_button("Confirmar Entrada", type="primary", use_container_width=True):
                if prod:
                    if salvar_entrada_nuvem(end, prod, qtd, lote):
                        st.success("Entrada registrada com sucesso no Google Sheets!")
                        st.rerun()
                    else:
                        st.error("Erro ao registrar entrada na planilha.")
                else:
                    st.warning("Insira o código do produto.")

# ==========================================
# 4. SAÍDA DE MERCADORIA
# ==========================================
elif opcao == "Saída de Mercadoria":
    st.markdown("## Expedição e Baixa")
    itens_estoque = [f"{i['id']} - {i['produto']} (Lote: {i['lote']}) | End: {i['endereco']} | Qtd: {i['quantidade']}" 
                     for i in st.session_state.bd["estoque"] if i["quantidade"] > 0]
    
    if not itens_estoque:
        st.info("Não há mercadorias disponíveis em estoque para dar saída.")
    else:
        with st.form("form_saida", clear_on_submit=True):
            item_selecionado = st.selectbox("Selecione o Item para Saída", itens_estoque)
            qtd_saida = st.number_input("Quantidade de Saída", min_value=1, value=1)
            
            if st.form_submit_button("Confirmar Saída", type="primary", use_container_width=True):
                partes_texto = item_selecionado.split(" - ")
                item_id = int(partes_texto[0])
                
                dados_item = next(i for i in st.session_state.bd["estoque"] if i["id"] == item_id)
                
                if qtd_saida > dados_item["quantidade"]:
                    st.error(f"Quantidade indisponível. Saldo atual: {dados_item['quantidade']}")
                else:
                    nova_qtd = dados_item["quantidade"] - int(qtd_saida)
                    if salvar_saida_nuvem(item_id, nova_qtd):





