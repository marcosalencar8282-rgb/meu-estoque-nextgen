import sqlite3
from datetime import datetime
import streamlit as st
import pandas as pd

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
    return sqlite3.connect("supermercado_final_v8.db")

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

# SISTEMA DE ABAS
aba_pdv, aba_fluxo, aba_estoque, aba_cadastro, aba_nota = st.tabs([
    "💻 FRENTE DE CAIXA (PDV)",
    "💰 FLUXO DE CAIXA",
    "📈 ESTOQUE ATUAL",
    "📝 CADASTRAR PRODUTO",
    "🧾 ENTRADA DE NOTA FISCAL"
])

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
                        cursor.execute("SELECT COALESCE(SUM(quantidade), 0) FROM entradas WHERE id_produto = ?", (id_p,))
                        ent = cursor.fetchone()[0]
                        cursor.execute("SELECT COALESCE(SUM(quantidade), 0) FROM itens_venda WHERE id_produto = ?", (id_p,))
                        sai = cursor.fetchone()[0]
                        estoque_disponivel = ent - sai
                        
                        qtd_no_carrinho = sum(item['quantidade'] for item in st.session_state["carrinho"] if item['id'] == id_p)
                        
                        if (qtd_bipar + qtd_no_carrinho) > estoque_disponivel:
                            st.error(f"Estoque insuficiente! Disponível: {estoque_disponivel} un. Lance uma Nota Fiscal.")
                        else:
                            st.session_state["carrinho"].append({
                                "id": id_p,
                                "codigo": sku_bipar,
                                "nome": nome_p,
                                "quantidade": qtd_bipar,
                                "preco": preco_p,
                                "subtotal": float(preco_p * qtd_bipar)
                            })
                            st.success(f"{nome_p} adicionado!")
                            st.rerun()
                else:
                    st.error("Produto não cadastrado.")
                conn.close()

    with col_pdv2:
        st.markdown("### 📋 ITENS DO CUPOM COMPRADO")
        if st.session_state["carrinho"]:
            df_cart = pd.DataFrame(st.session_state["carrinho"])
            st.dataframe(df_cart[["codigo", "nome", "quantidade", "preco", "subtotal"]], use_container_width=True, hide_index=True)
            
            valor_total_compra = float(df_cart["subtotal"].sum())
            st.markdown(f"<h2 style='text-align: right; color: #10B981;'>TOTAL: R$ {valor_total_compra:.2f}</h2>", unsafe_allow_html=True)
            
            st.markdown("---")
            c_fechar1, c_fechar2, c_fechar3 = st.columns(3)
            with c_fechar1:
                forma_pagto = st.selectbox("Forma de Pagamento:", ["Dinheiro", "Cartão de Crédito", "Cartão de Débito", "PIX"])
            with c_fechar2:
                pago_dinheiro = st.number_input("Valor Pago (Dinheiro):", min_value=0.0, value=float(valor_total_compra))
            with c_fechar3:
                troco = pago_dinheiro - float(valor_total_compra)
                if troco > 0 and forma_pagto == "Dinheiro":
                    st.markdown(f"<p style='color:#F59E0B; font-weight:bold; font-size:18px;'>Troco: R$ {troco:.2f}</p>", unsafe_allow_html=True)
            
            c_btn1, c_btn2 = st.columns(2)
            with c_btn1:
                if st.button("❌ Cancelar Cupom", use_container_width=True):
                    st.session_state["carrinho"] = []
                    st.rerun()
            with c_btn2:
                if st.button("✅ FINALIZAR VENDA", use_container_width=True):
                    conn = conectar()
                    cursor = conn.cursor()
                    data_venda = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    cursor.execute("INSERT INTO vendas (data, total, operador, forma_pagamento) VALUES (?, ?, ?, ?)",
                                   (data_venda, valor_total_compra, st.session_state["usuario_logado"], forma_pagto))
                    id_da_venda_salva = cursor.lastrowid
                    
                    for item in st.session_state["carrinho"]:

