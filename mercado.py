import sqlite3
from datetime import datetime
import streamlit as st
import pandas as pd

# CONFIGURAÇÃO DE PÁGINA
st.set_page_config(page_title="NextGen Supermercado", layout="wide", page_icon="🛒")

# --- CONTROLE DE SESSÃO / LOGIN ---
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False
if "usuario_logado" not in st.session_state:
    st.session_state["usuario_logado"] = ""
if "carrinho_compras" not in st.session_state:
    st.session_state["carrinho_compras"] = []
if "tela_ativa" not in st.session_state:
    st.session_state["tela_ativa"] = ""

# LISTA DE OPERADORES PERMITIDOS
USUARIOS_PERMITIDOS = {
    "admin": "Master@2026",
    "lucas": "Lucas#Estoque",
    "marcos": "931481"
}

# --- CONEXÃO COM O BANCO DE DADOS ---
def conectar():
    return sqlite3.connect("mercado_modelo_normal.db")

conn = conectar()
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS produtos (codigo TEXT UNIQUE, nome TEXT, preco REAL)")
cursor.execute("CREATE TABLE IF NOT EXISTS estoque (data TEXT, nota_fiscal TEXT, codigo TEXT, nome TEXT, quantidade INTEGER)")
cursor.execute("CREATE TABLE IF NOT EXISTS vendas (data TEXT, codigo TEXT, nome TEXT, quantidade INTEGER, total REAL, pagamento TEXT, troco REAL)")
conn.commit()
conn.close()

# TELA DE LOGIN
if not st.session_state["autenticado"]:
    st.markdown("<h1 style='text-align: center;'>🛒 NEXTGEN SUPERMERCADO</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #64748B;'>Autenticação Obrigatória de Operador</p>", unsafe_allow_html=True)

    col_l1, col_l2, col_l3 = st.columns([1, 1.2, 1])
    with col_l2:
        u_input = st.text_input("Operador:")
        p_input = st.text_input("Senha:", type="password")
        if st.button("Abrir Sistema / Caixa", use_container_width=True):
            if u_input.strip() in USUARIOS_PERMITIDOS and USUARIOS_PERMITIDOS[u_input.strip()] == p_input.strip():
                st.session_state["autenticado"] = True
                st.session_state["usuario_logado"] = u_input.strip()
                
                # Define a tela inicial padrão baseada no operador para não dar erro
                if u_input.strip() == "lucas":
                    st.session_state["tela_ativa"] = "🧾 Entrada de Estoque (NF)"
                else:
                    st.session_state["tela_ativa"] = "💻 Frente de Caixa (PDV)"
                    
                st.rerun()
            else:
                st.error("Operador ou senha incorretos.")
    st.stop()

# BARRA LATERAL COM PARÂMETROS DE PERMISSÃO POR OPERADOR
usuario = st.session_state["usuario_logado"]

with st.sidebar:
    st.markdown("### 🛒 OPERAÇÃO DE CAIXA")
    st.write(f"Operador ativo: `{usuario}`")
    
    if usuario == "admin":
        st.info("Acesso: **Administrador Geral**")
    elif usuario == "lucas":
        st.info("Acesso: **Controle de Estoque**")
    elif usuario == "marcos":
        st.info("Acesso: **Operador de Caixa (PDV)**")
        
    st.markdown("---")
    st.markdown("### 🛠️ SELECIONE A TELA:")
    
    # Restrição de botões baseada estritamente no tipo de usuário logado
    if usuario == "admin":
        if st.button("💻 1. Frente de Caixa (PDV)", use_container_width=True): st.session_state["tela_ativa"] = "💻 Frente de Caixa (PDV)"
        if st.button("📝 2. Cadastrar Produto", use_container_width=True): st.session_state["tela_ativa"] = "📝 Cadastrar Produto"
        if st.button("🧾 3. Entrada de Estoque (NF)", use_container_width=True): st.session_state["tela_ativa"] = "🧾 Entrada de Estoque (NF)"
        if st.button("📊 4. Relatório de Vendas", use_container_width=True): st.session_state["tela_ativa"] = "📊 Relatório de Vendas"
        if st.button("📈 5. Histórico de Entradas", use_container_width=True): st.session_state["tela_ativa"] = "📈 Histórico de Entradas"
        
    elif usuario == "lucas":
        if st.button("🧾 1. Entrada de Estoque (NF)", use_container_width=True): st.session_state["tela_ativa"] = "🧾 Entrada de Estoque (NF)"
        if st.button("📈 2. Histórico de Entradas", use_container_width=True): st.session_state["tela_ativa"] = "📈 Histórico de Entradas"
        
    elif usuario == "marcos":
        if st.button("💻 1. Frente de Caixa (PDV)", use_container_width=True): st.session_state["tela_ativa"] = "💻 Frente de Caixa (PDV)"
        
    st.markdown("---")
    if st.button("Fechar Caixa / Sair", use_container_width=True):
        st.session_state["autenticado"] = False
        st.session_state["usuario_logado"] = ""
        st.session_state["carrinho_compras"] = []
        st.rerun()

# --- EXECUÇÃO VISUAL DAS TELAS ---
tela = st.session_state["tela_ativa"]
st.title(f"🛒 {tela}")

if tela == "💻 Frente de Caixa (PDV)":
    col_v1, col_v2 = st.columns([1, 1.5])
    with col_v1:
        st.markdown("#### 🔍 Registrar Item")
        v_cod = st.text_input("Código do Produto Vendido:", key="v1")
        v_qtd = st.number_input("Quantidade Vendida:", min_value=1, value=1, key="v2")
        if st.button("Adicionar ao Carrinho"):
            if v_cod:
                conn = conectar()
                cursor = conn.cursor()
                cursor.execute("SELECT nome, preco FROM produtos WHERE codigo = ?", (v_cod.strip(),))
                prod = cursor.fetchone()
                if prod:
                    nome_p, preco_p = prod
                    st.session_state["carrinho_compras"].append({"codigo": v_cod.strip(), "nome": nome_p, "quantidade": v_qtd, "total": (preco_p * v_qtd)})
                    st.success(f"'{nome_p}' adicionado!")
                    st.rerun()
                else:
                    st.error("Produto não cadastrado!")
                conn.close()

    with col_v2:
        st.markdown("#### 📋 Cupom Fiscal / Carrinho")
        if st.session_state["carrinho_compras"]:
            df_cupom = pd.DataFrame(st.session_state["carrinho_compras"])
            st.dataframe(df_cupom[["codigo", "nome", "quantidade", "total"]], use_container_width=True, hide_index=True)
            soma_total = float(df_cupom["total"].sum())
            st.markdown(f"### VALOR TOTAL: R$ {soma_total:.2f}")
            v_pag = st.selectbox("Forma de Pagamento:", ["Dinheiro", "Cartão de Crédito", "Cartão de Débito", "PIX"], key="v3")
            valor_recebido = st.number_input("Valor Pago pelo Cliente (R$):", min_value=0.0, value=soma_total, step=1.0)
            
            if (valor_recebido - soma_total) > 0:
                st.markdown(f"<p style='color:#F59E0B; font-weight:bold; font-size:20px;'>Troco: R$ {(valor_recebido - soma_total):.2f}</p>", unsafe_allow_html=True)
            
            c1, c2 = st.columns(2)
            with c1:
                if st.button("❌ Cancelar Tudo"):
                    st.session_state["carrinho_compras"] = []
                    st.rerun()
            with c2:
                if st.button("✅ Confirmar Venda"):
                    conn = conectar()
                    cursor = conn.cursor()
                    data_v = datetime.now().strftime("%d/%m/%Y %H:%M")
                    for item in st.session_state["carrinho_compras"]:
                        cursor.execute("INSERT INTO vendas VALUES (?, ?, ?, ?, ?, ?, ?)", (data_v, item["codigo"], item["nome"], item["quantidade"], item["total"], v_pag, max(0.0, valor_recebido - soma_total)))
                    conn.commit()
                    conn.close()
                    st.session_state["carrinho_compras"] = []
                    st.toast("🛒 Venda finalizada com sucesso!")
                    st.rerun()
        else:
            st.info("O carrinho de compras está vazio. Registre itens na coluna ao lado.")

elif tela == "📝 Cadastrar Produto":
    c_cod = st.text_input("Código do Produto:", key="c1")
    c_nom = st.text_input("Nome do Produto:", key="c2")
    c_pre = st.number_input("Preço de Venda (R$):", min_value=0.1, value=5.0, key="c3")
    if st.button("Gravar Produto"):
        if c_cod and c_nom:
            conn = conectar()
            cursor = conn.cursor()
            try:
                cursor.execute("INSERT INTO produtos VALUES (?, ?, ?)", (c_cod.strip(), c_nom.strip(), c_pre))
                conn.commit()
                st.success(f"Produto '{c_nom}' cadastrado!")
            except:
                st.error("Este código já existe!")
            conn.close()
        else:
            st.warning("Preencha o código e o nome.")

elif tela == "🧾 Entrada de Estoque (NF)":
    e_nf = st.text_input("Número da Nota Fiscal (NF-e):", key="e_nf")
    e_cod = st.text_input("Código do Produto para Abastecer:", key="e1")
    e_qtd = st.number_input("Quantidade que está Entrando:", min_value=1, value=10, key="e2")
    if st.button("Confirmar Entrada"):
        if e_nf and e_cod:
            conn = conectar()
            cursor = conn.cursor()
            cursor.execute("SELECT nome FROM produtos WHERE codigo = ?", (e_cod.strip(),))
            prod = cursor.fetchone()
            if prod:
                # CORREÇÃO EFETIVA: Extrai o texto puro de dentro da tupla usando [0] para não salvar como ('Arroz',)
                nome_p = prod[0]
                data_e = datetime.now().strftime("%d/%m/%Y %H:%M")
                cursor.execute("INSERT INTO estoque VALUES (?, ?, ?, ?, ?)", (data_e, e_nf.strip(), e_cod.strip(), nome_p, int(e_qtd)))
                conn.commit()
                st.success(f"Estoque abastecido via NF {e_nf} com +{e_qtd} unidades de '{nome_p}'!")
                st.rerun()
            else:
                st.error("Código não encontrado! Cadastre o produto com uma conta Admin primeiro.")
            conn.close()
        else:
            st.warning("Digite a Nota Fiscal e o código do produto.")

elif tela == "📊 Relatório de Vendas":
    conn = conectar()
