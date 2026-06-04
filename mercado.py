import sqlite3
from datetime import datetime
import streamlit as st
import pandas as pd

# Configuração da página com visual moderno de sistema comercial
st.set_page_config(
    page_title="NextGen Supermercado | Painel Geral", layout="wide", page_icon="🛒"
)

# --- CONTROLE DE SESSÃO / LOGIN ---
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False
if "usuario_logado" not in st.session_state:
    st.session_state["usuario_logado"] = ""
if "carrinho" not in st.session_state:
    st.session_state["carrinho"] = []

# LISTA DE USUÁRIOS DO MERCADO
USUARIOS_PERMITIDOS = {
    "admin": "Master@2026",
    "lucas": "Lucas#Estoque",
    "marcos": "931481",
    "caixa1": "Caixa123"
}

# --- CONEXÃO COM O BANCO DE DADOS ---
def conectar():
    return sqlite3.connect("supermercado_blindado.db")

def inicializar_banco():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS produtos (
        id_produto INTEGER PRIMARY KEY AUTOINCREMENT,
        codigo TEXT UNIQUE NOT NULL,
        nome TEXT NOT NULL,
        preco_venda REAL NOT NULL,
        status TEXT DEFAULT 'Ativo'
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS entradas (
        id_entrada INTEGER PRIMARY KEY AUTOINCREMENT,
        data TEXT NOT NULL,
        nota_fiscal TEXT NOT NULL,
        id_produto INTEGER NOT NULL,
        quantidade INTEGER NOT NULL,
        FOREIGN KEY (id_produto) REFERENCES produtos (id_produto)
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS vendas (
        id_venda INTEGER PRIMARY KEY AUTOINCREMENT,
        data TEXT NOT NULL,
        total REAL NOT NULL,
        operador TEXT NOT NULL,
        forma_pagamento TEXT NOT NULL
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS itens_venda (
        id_item INTEGER PRIMARY KEY AUTOINCREMENT,
        id_venda INTEGER NOT NULL,
        id_produto INTEGER NOT NULL,
        quantidade INTEGER NOT NULL,
        preco_unitario REAL NOT NULL,
        FOREIGN KEY (id_venda) REFERENCES vendas (id_venda),
        FOREIGN KEY (id_produto) REFERENCES produtos (id_produto)
    )
    """)
    conn.commit()
    conn.close()

try:
    inicializar_banco()
except:
    pass

# TELA DE LOGIN
if not st.session_state["autenticado"]:
    st.markdown("<h1 style='text-align: center; color: #FFFFFF;'>🛒 NEXTGEN SUPERMERCADO</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #64748B;'>Autenticação de Operador de Caixa / Gerência</p>", unsafe_allow_html=True)

    col_l1, col_l2, col_l3 = st.columns([1, 1.2, 1])
    with col_l2:
        u_input = st.text_input("Operador:")
        p_input = st.text_input("Senha:", type="password")
        if st.button("Abrir Sistema / Caixa", use_container_width=True):
            if u_input.strip() in USUARIOS_PERMITIDOS and USUARIOS_PERMITIDOS[u_input.strip()] == p_input.strip():
                st.session_state["autenticado"] = True
                st.session_state["usuario_logado"] = u_input.strip()
                st.rerun()
            else:
                st.error("Operador ou senha incorretos.")
    st.stop()

# Estilização CSS para o visual Dark/Cyber de Alta Performance
st.markdown(
    """
    <style>
    .stApp { background-color: #0B0F19; color: #E2E8F0; }
    font-family: 'Inter', sans-serif;
    h1, h2, h3 { color: #FFFFFF; font-weight: 800; letter-spacing: -0.5px; }
    div[data-testid="stFrame"] { background-color: #161B26; border-radius: 12px; padding: 20px; border: 1px solid #242F41; }
    .stButton>button {
        background: linear-gradient(135deg, #10B981 0%, #047857 100%);
        color: white !important;
        border: none;
        padding: 10px 24px;
        font-weight: 700;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.2);
    }
    .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(16, 185, 129, 0.4); }
    input, textarea { background-color: #1E293B !important; color: white !important; border: 1px solid #334155 !important; }
    </style>
""",
    unsafe_allow_html=True,
)

# Topo Branding
st.markdown(
    "<h1 style='margin:0; font-size: 2.2rem;'>🛒 NEXTGEN <span style='color: #10B981;'>|</span> SMART MARKET</h1>"
    "<p style='color: #64748B; margin-top: -5px;'>Módulo de Operação Integrada Contínua</p>",
    unsafe_allow_html=True,
)

if st.button("Sair do Sistema / Deslogar"):
    st.session_state["autenticado"] = False
    st.session_state["usuario_logado"] = ""
    st.session_state["carrinho"] = []
    st.rerun()

st.markdown("---")

# ==========================================
# SEÇÃO 1: CADASTRO RÁPIDO DE PRODUTO
# ==========================================
st.header("📦 1. Cadastrar Produto na Prateleira")
col_c1, col_c2, col_c3 = st.columns(3)
with col_c1:
    cod_p = st.text_input("Código de Barras ou SKU para cadastrar:", key="c_sku")
with col_c2:
    nome_p = st.text_input("Nome do Produto (Ex: Coca-Cola):", key="c_nome")
with col_c3:
    preco_p = st.number_input("Preço de Venda (R$):", min_value=0.01, step=0.05, value=4.50, key="c_preco")

if st.button("Gravar Produto no Catálogo", use_container_width=True):
    if not cod_p or not nome_p:
        st.warning("Preencha todos os campos para cadastrar.")
    else:
        conn = conectar()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO produtos (codigo, nome, preco_venda, status) VALUES (?, ?, ?, 'Ativo')", (cod_p.strip(), nome_p.strip(), preco_p))
            conn.commit()
            st.success(f"Sucesso: '{nome_p}' cadastrado!")
            st.rerun()
        except Exception as e:
            st.error(f"Erro ao salvar: Verifique se esse código já existe.")
        finally:
            conn.close()

st.markdown("---")

# ==========================================
# SEÇÃO 2: ENTRADA DE NOTA FISCAL (ABASTECER)
# ==========================================
st.header("🧾 2. Entrada de Nota Fiscal (Abastecer Estoque)")
col_n1, col_n2, col_n3 = st.columns(3)
with col_n1:
    nf_e = st.text_input("Número da Nota Fiscal (NF-e):", key="n_num")
with col_n2:
    sku_e = st.text_input("Código de Barras / SKU do Produto que vai abastecer:", key="n_sku")
with col_n3:
    qtd_e = st.number_input("Quantidade recebida:", min_value=1, step=1, value=50, key="n_qtd")

if st.button("Processar Entrada de Estoque", use_container_width=True):
    if not nf_e or not sku_e:
        st.warning("Preencha os campos da Nota Fiscal.")
    else:
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT id_produto FROM produtos WHERE codigo = ?", (sku_e.strip(),))
        prod = cursor.fetchone()
        if prod:
            id_prod = prod[0]
            cursor.execute("INSERT INTO entradas (data, nota_fiscal, id_produto, quantidade) VALUES (?, ?, ?, ?)",
                           (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), nf_e.strip(), id_prod, qtd_e))
            conn.commit()
            st.success(f"Sucesso: +{qtd_e} unidades adicionadas ao estoque!")
            st.rerun()
        else:
            st.error("Erro: Esse código de barras NÃO está cadastrado na Seção 1.")
        conn.close()

st.markdown("---")

# ==========================================
# SEÇÃO 3: FRENTE DE CAIXA (PDV)
# ==========================================
st.header("💻 3. Frente de Caixa (Vender)")
col_p1, col_p2 = st.columns([1, 1.5])

with col_p1:
    st.markdown("#### Bipar Item")
    sku_venda = st.text_input("Código de Barras / SKU do Item:", key="v_sku")
    qtd_venda = st.number_input("Quantidade Comprada:", min_value=1, step=1, value=1, key="v_qtd")
    
    if st.button("Adicionar ao Carrinho", use_container_width=True):
        if not sku_venda:
            st.warning("Insira o código.")
        else:
            conn = conectar()
            cursor = conn.cursor()
            cursor.execute("SELECT id_produto, nome, preco_venda FROM produtos WHERE codigo = ?", (sku_venda.strip(),))
            prod = cursor.fetchone()
            if prod:
                id_p, nome_p, preco_p = prod
                
                # Validação rápida de estoque
                cursor.execute("SELECT COALESCE(SUM(quantidade), 0) FROM entradas WHERE id_produto = ?", (id_p,))
                ent = cursor.fetchone()[0]
                cursor.execute("SELECT COALESCE(SUM(quantidade), 0) FROM itens_venda WHERE id_produto = ?", (id_p,))
                sai = cursor.fetchone()[0]
                saldo = ent - sai
                
                if qtd_venda > saldo:
                    st.error(f"Erro: Estoque insuficiente! Saldo atual é de apenas {saldo} unidades.")
                else:
                    st.session_state["carrinho"].append({
                        "id": id_p,
                        "codigo": sku_venda.strip(),
                        "nome": nome_p,
                        "quantidade": qtd_venda,
                        "preco": preco_p,
                        "subtotal": preco_p * qtd_venda
                    })
                    st.success(f"'{nome_p}' adicionado à lista!")
                    st.rerun()
            else:
                st.error("Erro: Produto não localizado no catálogo (Seção 1).")
            conn.close()

with col_p2:
    st.markdown("#### Lista de Compras Atual")
    if st.session_state["carrinho"]:
        df_cart = pd.DataFrame(st.session_state["carrinho"])
        st.dataframe(df_cart[["codigo", "nome", "quantidade", "preco", "subtotal"]], use_container_width=True, hide_index=True)
        
        total_compra = df_cart["subtotal"].sum()
        st.markdown(f"<h3 style='color: #10B981;'>VALOR TOTAL: R$ {total_compra:.2f}</h3>", unsafe_allow_html=True)
        
        forma_pagto = st.selectbox("Pagamento:", ["Dinheiro", "PIX", "Cartão"])
        if st.button("Confirmar e Finalizar Venda", use_container_width=True):
            conn = conectar()
            cursor = conn.cursor()

