import sqlite3
from datetime import datetime
import streamlit as st

# Configuração da página com visual moderno de sistema comercial
st.set_page_config(
    page_title="NextGen Supermercado | PDV & Estoque", layout="wide", page_icon="🛒"
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
    return sqlite3.connect("supermercado_final_v6.db")

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

inicializar_banco()

# --- TELA DE LOGIN ---
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
    button[data-baseweb="tab"] { font-size: 14px !important; font-weight: 600 !important; color: #94A3B8 !important; }
    button[aria-selected="true"] { color: #10B981 !important; border-bottom-color: #10B981 !important; }
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

# Barra Lateral
with st.sidebar:
    st.markdown("### 🛒 OPERAÇÃO DE CAIXA")
    st.write(f"Operador: `{st.session_state['usuario_logado']}`")
    st.markdown("---")
    if st.button("Fechar Caixa / Sair", use_container_width=True):
        st.session_state["autenticado"] = False
        st.session_state["usuario_logado"] = ""
        st.session_state["carrinho"] = []
        st.rerun()

# Topo Branding
st.markdown(
    "<h1 style='margin:0; font-size: 2.2rem;'>🛒 NEXTGEN <span style='color: #10B981;'>|</span> SMART MARKET</h1>"
    "<p style='color: #64748B; margin-top: -5px;'>Módulo Integrado de Vendas, Fluxo de Caixa e Controle de Estoque</p>",
    unsafe_allow_html=True,
)
st.markdown("<br>", unsafe_allow_html=True)

# Sistema de Abas
aba_pdv, aba_fluxo, aba_estoque, aba_cadastro, aba_nota = st.tabs([
    "💻 FRENTE DE CAIXA (PDV)",
    "💰 FLUXO DE CAIXA",
    "📈 ESTOQUE ATUAL",
    "📝 CADASTRAR PRODUTO",
    "🧾 ENTRADA DE NOTA FISCAL"
])

# --- ABA 4: CADASTRAR PRODUTO ---
with aba_cadastro:
    st.markdown("### 📦 CADASTRO DE NOVOS PRODUTOS")
    cod_p = st.text_input("Código de Barras ou SKU do Produto:", key="new_sku")
    nome_p = st.text_input("Nome do Produto (Ex: Arroz 5kg):", key="new_name")
    preco_p = st.number_input("Preço de Venda (R$):", min_value=0.01, step=0.05, value=1.99, key="new_price")
    
    if st.button("Gravar Produto no Catálogo", use_container_width=True):
        if not cod_p or not nome_p:
            st.warning("Preencha todos os campos do produto.")
        else:
            conn = conectar()
            cursor = conn.cursor()
            try:
                cursor.execute("INSERT INTO produtos (codigo, nome, preco_venda, status) VALUES (?, ?, ?, 'Ativo')",
                               (cod_p.strip(), nome_p.strip(), preco_p))
                conn.commit()
                st.success(f"Produto '{nome_p}' cadastrado com sucesso!")
                st.cache_data.clear()
                st.rerun()
            except sqlite3.IntegrityError:
                st.error("Este Código de Barras / SKU já está cadastrado.")
            finally:
                conn.close()

# --- ABA 5: ENTRADA DE NOTA FISCAL ---
with aba_nota:
    st.markdown("### 🧾 ENTRADA DE NOTA FISCAL (ABASTECER ESTOQUE)")
    nf_e = st.text_input("Número da Nota Fiscal (NF-e):", key="nf_compra")
    sku_e = st.text_input("Código de Barras / SKU do Produto:", key="nf_sku")
    qtd_e = st.number_input("Quantidade de Itens Recebidos:", min_value=1, step=1, value=10, key="nf_qtd")
    
    if st.button("Processar Entrada de NF-e", use_container_width=True):
        if not nf_e or not sku_e:
            st.warning("Preencha todos os campos da nota fiscal.")
        else:
            conn = conectar()
            cursor = conn.cursor()
            cursor.execute("SELECT id_produto, status FROM produtos WHERE codigo = ?", (sku_e.strip(),))
            prod = cursor.fetchone()
            
            if prod:
                id_produto_encontrado, status_prod = prod
                if status_prod == "Inativo":
                    st.error("Operação Recusada! Este produto está inativo.")
                else:
                    data_entrada = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    cursor.execute("INSERT INTO entradas (data, nota_fiscal, id_produto, quantidade) VALUES (?, ?, ?, ?)",
                                   (data_entrada, nf_e.strip(), id_produto_encontrado, qtd_e))
                    conn.commit()
                    st.success(f"Estoque do produto {sku_e} abastecido com +{qtd_e} unidades!")
                    st.rerun()
            else:
                st.error("Código de barras não localizado no sistema. Cadastre o item na aba ao lado primeiro.")
            conn.close()

# --- ABA 1: FRENTE DE CAIXA (PDV) ---
with aba_pdv:
    st.subheader("Registrar Compra (Cupom Fiscal)")
    col_pdv1, col_pdv2 = st.columns([1, 1.5])
    
    with col_pdv1:
        st.markdown("### 🔍 BIPAR / INCLUIR ITEM")
        sku_bipar = st.text_input("Código de Barras ou SKU do Produto:", key="sku_pdv").strip()
        qtd_bipar = st.number_input("Quantidade:", min_value=1, step=1, value=1, key="qtd_pdv")
        
        if st.button("Adicionar ao Carrinho", use_container_width=True):
            if not sku_bipar:
                st.warning("Insira o código do produto.")
            else:
                conn = conectar()
                cursor = conn.cursor()
                cursor.execute("SELECT id_produto, nome, preco_venda, status FROM produtos WHERE codigo = ?", (sku_bipar,))
                prod = cursor.fetchone()
                
                if prod:
                    id_p, nome_p, preco_p, status_p = prod
                    if status_p == "Inativo":
                        st.error("Produto inativo no sistema!")
                    else:
                        # CORREÇÃO CRÍTICA: Desempacotamento seguro tratando None como 0
                        cursor.execute("SELECT COALESCE(SUM(quantidade), 0) FROM entradas WHERE id_produto = ?", (id_p,))
                        res_ent = cursor.fetchone()
                        ent = res_ent[0] if res_ent else 0
                        
                        cursor.execute("SELECT COALESCE(SUM(quantidade), 0) FROM itens_venda WHERE id_produto = ?", (id_p,))
                        res_sai = cursor.fetchone()
                        sai = res_sai[0] if res_sai else 0
                        
                        estoque_disponivel = ent - sai

