import streamlit as st
import pandas as pd
from datetime import datetime
import os
import io

st.set_page_config(page_title="NextGen WMS", layout="wide")

# ==========================================
# GERENCIAMENTO LOCAL VIA BANCO DE DADOS CSV
# ==========================================
ARQUIVO_ENDERECOS = "wms_enderecos.csv"
ARQUIVO_ESTOQUE = "wms_estoque.csv"

def carregar_dados_locais():
    """Carrega as tabelas dos arquivos CSV locais."""
    enderecos = []
    estoque = []
    
    # Carrega endereços
    if os.path.exists(ARQUIVO_ENDERECOS):
        try:
            df_end = pd.read_csv(ARQUIVO_ENDERECOS)
            if not df_end.empty and "endereco" in df_end.columns:
                enderecos = [str(x).upper().strip() for x in df_end["endereco"].dropna().tolist()]
        except Exception:
            pass
            
    # Carrega estoque
    if os.path.exists(ARQUIVO_ESTOQUE):
        try:
            df_est = pd.read_csv(ARQUIVO_ESTOQUE)
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

def salvar_dados_locais(dados):
    """Grava as listas de endereços e estoque dentro dos arquivos CSV."""
    try:
        df_end = pd.DataFrame({"endereco": dados["enderecos"]})
        df_end.to_csv(ARQUIVO_ENDERECOS, index=False)
        
        df_est = pd.DataFrame(dados["estoque"])
        if df_est.empty:
            df_est = pd.DataFrame(columns=["id", "endereco", "produto", "quantidade", "lote", "data"])
        df_est.to_csv(ARQUIVO_ESTOQUE, index=False)
        return True
    except Exception:
        return False

def gerar_csv_download(tipo):
    """Gera um arquivo CSV em formato de texto para download imediato."""
    dados = st.session_state.bd
    if tipo == "enderecos":
        df = pd.DataFrame({"endereco": dados["enderecos"]})
    else:
        df = pd.DataFrame(dados["estoque"])
        if df.empty:
            df = pd.DataFrame(columns=["id", "endereco", "produto", "quantidade", "lote", "data"])
    
    # Exporta usando ponto e vírgula como separador para abrir direto no Excel em português
    return df.to_csv(index=False, sep=";").encode('utf-8-sig')

# Inicialização do banco de dados local
if 'bd' not in st.session_state:
    st.session_state.bd = carregar_dados_locais()

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
# MENU LATERAL E BOTÕES DE DOWNLOAD
# ==========================================
st.sidebar.markdown("<h2>WMS NextGen</h2>", unsafe_allow_html=True)
opcao = st.sidebar.radio("Módulos", ["Visão Geral", "Cadastrar Endereço", "Entrada de Mercadoria", "Saída de Mercadoria"])

st.sidebar.markdown("---")
st.sidebar.markdown("### Exportar Dados (Excel)")

# Botão para baixar planilha de Endereços
csv_enderecos = gerar_csv_download("enderecos")
st.sidebar.download_button(
    label="🗺️ Baixar Planilha Endereços",
    data=csv_enderecos,
    file_name=f"wms_enderecos_{datetime.now().strftime('%d_%m_%Y')}.csv",
    mime="text/csv",
    use_container_width=True
)

# Botão para baixar planilha de Estoque de Produtos
csv_estoque = gerar_csv_download("estoque")
st.sidebar.download_button(
    label="📦 Baixar Planilha Estoque",
    data=csv_estoque,
    file_name=f"wms_estoque_{datetime.now().strftime('%d_%m_%Y')}.csv",
    mime="text/csv",
    use_container_width=True
)

st.sidebar.markdown("---")
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
                    st.session_state.bd["enderecos"].append(novo_end)
                    if salvar_dados_locais(st.session_state.bd):
                        st.success("Endereço salvo localmente com sucesso!")
                        st.rerun()
                    else:
                        st.error("Erro interno ao gravar dados.")
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
                    data_atual = datetime.now().strftime('%d/%m/%Y %H:%M')
                    estoque_atual = st.session_state.bd["estoque"]
                    
                    item_existente = next((i for i in estoque_atual if i["endereco"] == end and i["produto"] == prod and i["lote"] == lote), None)
                    
                    if item_existente:
                        item_existente["quantidade"] += int(qtd)
                        item_existente["data"] = data_atual
                    else:
                        novo_id = max([i["id"] for i in estoque_atual], default=0) + 1
                        estoque_atual.append({
                            "id": novo_id,
                            "endereco": end,
                            "produto": prod,
                            "quantidade": int(qtd),
                            "lote": lote,
                            "data": data_atual
                        })
                    
                    if salvar_dados_locais(st.session_state.bd):
                        st.success("Entrada armazenada com sucesso!")
                        st.rerun()
                    else:
                        st.error("Erro ao processar gravação no arquivo.")
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






