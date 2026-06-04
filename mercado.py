import sqlite3
from datetime import datetime
import streamlit as st

# Configuração da página - Menu Lateral robusto
st.set_page_config(
    page_title="NextGen Supermercado | Sistema", layout="wide", page_icon="🛒"
)

# --- CONTROLE DE SESSÃO / LOGIN ---
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False
if "usuario_logado" not in st.session_state:
    st.session_state["usuario_logado"] = ""
if "carrinho" not in st.session_state:
    st.session_state["carrinho"] = []

# LISTA DE USUÁRIOS
USUARIOS_PERMITIDOS = {
    "admin": "Master@2026",
    "lucas": "Lucas#Estoque",
    "marcos": "931481",
    "caixa1": "Caixa123"
}

# TELA DE LOGIN (Se não estiver logado, para o sistema aqui)
if not st.session_state["autenticado"]:
    st.markdown("<h1 style='text-align: center; color: #FFFFFF;'>🛒 NEXTGEN SUPERMERCADO</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #64748B;'>Autenticação Obrigatória de Operador</p>", unsafe_allow_html=True)
    
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

# --- DESIGN DO MENU LATERAL COMPACTO ---
with st.sidebar:
    st.markdown(f"### 👤 OPERADOR: `{st.session_state['usuario_logado']}`")
    st.markdown("---")
    st.markdown("### 🧭 MENU DE NAVEGAÇÃO")
    
    # Caixa de seleção para navegar - Força o desenho dos botões na tela na hora
    menu = st.radio(
        "Ir para a página:",
        [
            "📝 CADASTRAR PRODUTO",
            "💻 FRENTE DE CAIXA (PDV)",
            "🧾 ENTRADA DE NOTA FISCAL",
            "📈 ESTOQUE ATUAL",
            "💰 FLUXO DE CAIXA"
        ]
    )
    
    st.markdown("---")
    if st.button("Fechar Caixa / Sair", use_container_width=True):
        st.session_state["autenticado"] = False
        st.session_state["usuario_logado"] = ""
        st.session_state["carrinho"] = []
        st.rerun()

# --- CONEXÃO COM O BANCO DE DADOS ---
def conectar():
    conn = sqlite3.connect("supermercado_nextgen.db")
    return conn, conn.cursor()

def inicializar_banco():
    conn, cursor = conectar()
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

# --- CARREGAMENTO DAS PÁGINAS COM BASE NO MENU LATERAL ---

# PÁGINA 1: CADASTRAR PRODUTO
if menu == "📝 CADASTRAR PRODUTO":
    st.markdown("## 📦 CADASTRO DE NOVOS PRODUTOS")
    st.markdown("Preencha as informações abaixo para incluir o produto no catálogo do mercado.")
    
    cod_p = st.text_input("Código de Barras ou SKU do Produto:", key="new_sku")
    nome_p = st.text_input("Nome do Produto (Ex: Arroz 5kg):", key="new_name")
    preco_p = st.number_input("Preço de Venda (R$):", min_value=0.01, step=0.05, value=1.99, key="new_price")
    
    if st.button("Gravar Produto no Catálogo", use_container_width=True):
        if not cod_p or not nome_p:
            st.warning("Preencha todos os campos do produto.")
        else:
            conn, cursor = conectar()
            try:
                cursor.execute("INSERT INTO produtos (codigo, nome, preco_venda, status) VALUES (?, ?, ?, 'Ativo')",
                               (cod_p.strip(), nome_p.strip(), preco_p))
                conn.commit()
                st.success(f"Produto '{nome_p}' cadastrado com sucesso!")
            except sqlite3.IntegrityError:
                st.error("Este Código de Barras / SKU já está cadastrado.")
            finally:
                conn.close()

# PÁGINA 2: FRENTE DE CAIXA (PDV)
elif menu == "💻 FRENTE DE CAIXA (PDV)":
    st.markdown("## 💻 FRENTE DE CAIXA")
    col_pdv1, col_pdv2 = st.columns([1, 1.5])
    
    with col_pdv1:
        st.markdown("### 🔍 BIPAR / INCLUIR ITEM")
        sku_bipar = st.text_input("Código de Barras ou SKU do Produto:", key="sku_pdv").strip()
        qtd_bipar = st.number_input("Quantidade:", min_value=1, step=1, value=1, key="qtd_pdv")
        
        if st.button("Adicionar ao Carrinho", use_container_width=True):
            if not sku_bipar:
                st.warning("Insira o código do produto.")
            else:
                conn, cursor = conectar()
                cursor.execute("SELECT id_produto, nome, preco_venda, status FROM produtos WHERE codigo = ?", (sku_bipar,))
                prod = cursor.fetchone()
                
                if prod:
                    id_p, nome_p, preco_p, status_p = prod
                    if status_p == "Inativo":
                        st.error("Produto inativo no sistema!")
                    else:
                        cursor.execute("SELECT COALESCE(SUM(quantidade), 0) FROM entradas WHERE id_produto = ?", (id_p,))
                        ent = cursor.fetchone()[0] if cursor.fetchone() else 0
                        cursor.execute("SELECT COALESCE(SUM(quantidade), 0) FROM itens_venda WHERE id_produto = ?", (id_p,))
                        sai = cursor.fetchone()[0] if cursor.fetchone() else 0
                        estoque_disponivel = ent - sai
                        
                        qtd_no_carrinho = sum(item['quantidade'] for item in st.session_state["carrinho"] if item['id'] == id_p)
                        
                        if (qtd_bipar + qtd_no_carrinho) > estoque_disponivel:
                            st.error(f"Estoque insuficiente! Disponível: {estoque_disponivel} un.")
                        else:
                            st.session_state["carrinho"].append({
                                "id": id_p,
                                "codigo": sku_bipar,
                                "nome": nome_p,
                                "quantidade": qtd_bipar,
                                "preco": preco_p,
                                "subtotal": preco_p * qtd_bipar
                            })
                            st.success(f"{nome_p} adicionado!")
                            st.rerun()
                else:
                    st.error("Produto não cadastrado. Cadastre o item primeiro.")
                conn.close()

    with col_pdv2:
        st.markdown("### 📋 ITENS DO CUPOM")
        if st.session_state["carrinho"]:
            import pandas as pd
            df_cart = pd.DataFrame(st.session_state["carrinho"])
            st.dataframe(df_cart[["codigo", "nome", "quantidade", "preco", "subtotal"]], use_container_width=True, hide_index=True)
            
            valor_total_compra = df_cart["subtotal"].sum()
            st.markdown(f"## TOTAL: R$ {valor_total_compra:.2f}")
            
            forma_pagto = st.selectbox("Forma de Pagamento:", ["Dinheiro", "Cartão", "PIX"])
            pago_dinheiro = st.number_input("Valor Pago:", min_value=0.0, value=float(valor_total_compra))
            
            if pago_dinheiro > float(valor_total_compra) and forma_pagto == "Dinheiro":
                st.warning(f"Troco: R$ {pago_dinheiro - float(valor_total_compra):.2f}")
            
            c_b1, c_b2 = st.columns(2)
            with c_b1:
                if st.button("❌ Cancelar Cupom", use_container_width=True):
                    st.session_state["carrinho"] = []
                    st.rerun()
            with c_b2:
                if st.button("✅ FINALIZAR VENDA", use_container_width=True):
                    conn, cursor = conectar()
                    data_venda = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    cursor.execute("INSERT INTO vendas (data, total, operador, forma_pagamento) VALUES (?, ?, ?, ?)",
                                   (data_venda, valor_total_compra, st.session_state["usuario_logado"], forma_pagto))
                    id_da_venda_salva = cursor.lastrowid
                    
                    for item in st.session_state["carrinho"]:
                        cursor.execute("INSERT INTO itens_venda (id_venda, id_produto, quantidade, preco_unitario) VALUES (?, ?, ?, ?)",
                                       (id_da_venda_salva, item["id"], item["quantidade"], item["preco"]))
                    conn.commit()
                    conn.close()
                    st.session_state["carrinho"] = []
                    st.success("Venda Finalizada!")
                    st.rerun()
        else:
            st.info("Carrinho de compras vazio.")
              
