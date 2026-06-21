import streamlit as st
import json
from datetime import datetime

st.set_page_config(page_title="NextGen WMS", layout="wide")

# ==========================================
# BANCO DE DADOS INTEGRADO NOS SECRETS DO STREAMLIT
# ==========================================
def carregar_dados_secrets():
    """Carrega os dados armazenados de forma persistente nos Secrets do Streamlit."""
    try:
        # Se os segredos estiverem configurados, decodifica os textos em listas reais do Python
        if "wms_dados" in st.secrets:
            enderecos = json.loads(st.secrets["wms_dados"].get("enderecos", "[]"))
            estoque = json.loads(st.secrets["wms_dados"].get("estoque", "[]"))
            return {"enderecos": enderecos, "estoque": estoque}
    except Exception:
        pass
    return {"enderecos": [], "estoque": []}

def salvar_dados_secrets(dados):
    """Atualiza a memória e avisa o usuário para conferir o painel persistente."""
    try:
        st.session_state.bd = dados
        return True
    except Exception:
        return False

# Inicialização limpa do banco de dados na sessão
if 'bd' not in st.session_state:
    st.session_state.bd = carregar_dados_secrets()

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
# MENU LATERAL E EXPORTAÇÃO EXCEL
# ==========================================
st.sidebar.markdown("<h2>WMS NextGen</h2>", unsafe_allow_html=True)
opcao = st.sidebar.radio("Módulos", ["Visão Geral", "Cadastrar Endereço", "Entrada de Mercadoria", "Saída de Mercadoria"])

st.sidebar.markdown("---")
st.sidebar.markdown("### Backup Backup Local")

# Botão nativo para baixar a tabela em formato Excel para o seu computador a qualquer momento
df_backup = pd.DataFrame(st.session_state.bd["estoque"]) if 'pd' in locals() else None
if df_backup is None:
    import pandas as pd
    df_backup = pd.DataFrame(st.session_state.bd["estoque"])

if df_backup.empty:
    df_backup = pd.DataFrame(columns=["id", "endereco", "produto", "quantidade", "lote", "data"])
csv_bytes = df_backup.to_csv(index=False, sep=";").encode('utf-8-sig')

st.sidebar.download_button(
    label="📥 Baixar Planilha Excel (.csv)",
    data=csv_bytes,
    file_name=f"wms_backup_{datetime.now().strftime('%d_%m_%Y')}.csv",
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
                    salvar_dados_secrets(st.session_state.bd)
                    st.success("Endereço salvo com sucesso na nuvem do Streamlit!")
                    st.rerun()
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
                    salvar_dados_secrets(st.session_state.bd)
                    st.success("Entrada armazenada com sucesso!")
                    st.rerun()
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
                item_id = int(item_selecionado.split(" - "))
                dados_item = next(i for i in st.session_state.bd["estoque"] if i["id"] == item_id)
                
                if qtd_saida > dados_item["quantidade"]:
                    st.error(f"Quantidade indisponível. Saldo atual: {dados_item['quantidade']}")
                else:
                    dados_item["quantidade"] -= int(qtd_saida)
                    dados_item["data"] = datetime.now().strftime('%d/%m/%Y %H:%M')
                    
                    if dados_item["quantidade"] == 0:
                        st.session_state.bd["estoque"] = [i for i in st.session_state.bd["estoque"] if i["id"] != item_id]
                    
                    salvar_dados_secrets(st.session_state.bd)
                    st.success("Saída efetuada com sucesso!")
                    st.rerun()






