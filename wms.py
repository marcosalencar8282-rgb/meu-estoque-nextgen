import streamlit as st
from datetime import datetime
import httpx

st.set_page_config(page_title="NextGen WMS", layout="wide")

# ==========================================
# CONEXÃO DIRETA COM O BANCO DE DADOS (SUPABASE)
# ==========================================
SUPABASE_URL = "https://supabase.co"
SUPABASE_KEY = "sb_publishable_82728LoQTsjuchp13yEZgQ_tkAWAP"

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

def carregar_dados_nuvem():
    estoque, enderecos = [], []
    try:
        with httpx.Client() as client:
            r_end = client.get(f"{SUPABASE_URL}enderecos?select=*", headers=headers)
            if r_end.status_code == 200:
                enderecos = [str(item["endereco"]).upper().strip() for item in r_end.json() if "endereco" in item]
            
            r_est = client.get(f"{SUPABASE_URL}estoque?select=*", headers=headers)
            if r_est.status_code == 200:
                for item in r_est.json():
                    estoque.append({
                        "id": item.get("id"),
                        "endereco": str(item.get("endereco", "")).upper().strip(),
                        "produto": str(item.get("produto", "")).upper().strip(),
                        "quantidade": int(item.get("quantidade", 0)),
                        "lote": str(item.get("lote", "N/A")).upper().strip(),
                        "data": str(item.get("data", ""))
                    })
    except Exception:
        pass
    return {"enderecos": sorted(list(set(enderecos))), "estoque": estoque}

def salvar_endereco_nuvem(novo_end):
    try:
        with httpx.Client() as client:
            payload = {"endereco": novo_end}
            res = client.post(f"{SUPABASE_URL}enderecos", headers=headers, json=payload)
            if res.status_code == 201 or res.status_code == 200:
                return True
            return False
    except Exception:
        return False

def salvar_entrada_nuvem(end, prod, qtd, lote):
    try:
        with httpx.Client() as client:
            url_busca = f"{SUPABASE_URL}estoque?endereco=eq.{end}&produto=eq.{prod}&lote=eq.{lote}"
            r_busca = client.get(url_busca, headers=headers)
            data_atual = datetime.now().strftime('%d/%m/%Y %H:%M')
            
            if r_busca.status_code == 200 and len(r_busca.json()) > 0:
                item_atual = r_busca.json()[0]
                novo_total = int(item_atual["quantidade"]) + int(qtd)
                payload = {"quantidade": novo_total, "data": data_atual}
                res = client.patch(f"{SUPABASE_URL}estoque?id=eq.{item_atual['id']}", headers=headers, json=payload)
                return res.status_code == 200
            else:
                payload = {"endereco": end, "produto": prod, "quantidade": int(qtd), "lote": lote, "data": data_atual}
                res = client.post(f"{SUPABASE_URL}estoque", headers=headers, json=payload)
                if res.status_code == 201 or res.status_code == 200:
                    return True
            return False
    except Exception:
        return False

def salvar_saida_nuvem(item_id, nova_qtd):
    try:
        with httpx.Client() as client:
            data_atual = datetime.now().strftime('%d/%m/%Y %H:%M')
            payload = {"quantidade": int(nova_qtd), "data": data_atual}
            res = client.patch(f"{SUPABASE_URL}estoque?id=eq.{item_id}", headers=headers, json=payload)
            return res.status_code == 200
    except Exception:
        return False

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
                    if salvar_endereco_nuvem(novo_end):
                        st.session_state.bd = carregar_dados_nuvem()
                        st.success("Endereço salvo permanentemente no Supabase!")
                        st.rerun()
                    else:
                        st.error("Erro ao salvar no banco de dados.")
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
                        st.session_state.bd = carregar_dados_nuvem()
                        st.success("Entrada armazenada com sucesso!")
                        st.rerun()
                    else:
                        st.error("Erro ao registrar entrada no banco.")

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
                    nova_qtd = int(item_estoque["quantidade"]) - int(qtd_saida)
                    if salvar_saida_nuvem(item_estoque["id"], nova_qtd):
                        st.session_state.bd = carregar_dados_nuvem()
                        st.success("Saída processada com sucesso!")
                        st.rerun()
                    else:


