import sqlite3
from datetime import datetime
import streamlit as st
import pandas as pd

# Configuração da página
st.set_page_config(
    page_title="NextGen Supermercado | PDV & Estoque", layout="wide", page_icon="🛒"
)

# --- CONTROLE DE SESSÃO / LOGIN ---
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False
if "usuario_logado" not in st.session_state:
    st.session_state["usuario_logado"] = ""
if "carrinho_compras" not in st.session_state:
    st.session_state["carrinho_compras"] = []

# LISTA DE USUÁRIOS PERMITIDOS
USUARIOS_PERMITIDOS = {
    "admin": "Master@2026",
    "lucas": "Lucas#Estoque",
    "marcos": "931481",
    "caixa1": "Caixa123"
}

# --- CONEXÃO DIRETA COM O BANCO ---
def conectar():
    return sqlite3.connect("mercado_troco_v11.db")

conn = conectar()
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS produtos (codigo TEXT UNIQUE, nome TEXT, preco REAL)")
cursor.execute("CREATE TABLE IF NOT EXISTS estoque (data TEXT, nota_fiscal TEXT, codigo TEXT, quantidade INTEGER)")
# ATUALIZAÇÃO: Adicionado o campo de troco na tabela de vendas
cursor.execute("CREATE TABLE IF NOT EXISTS vendas (data TEXT, codigo TEXT, nome TEXT, quantidade INTEGER, total REAL, pagamento TEXT, troco REAL)")
conn.commit()
conn.close()

# TELA DE LOGIN (Bloqueia o sistema se não estiver autenticado)
if not st.session_state["autenticado"]:
    st.markdown("<h1 style='text-align: center;'>🛒 NEXTGEN SUPERMERCADO</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #64748B;'>Área Restrita - Autenticação de Operador</p>", unsafe_allow_html=True)

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

# --- BARRA LATERAL COM BOTÃO DE LOGOFF ---
with st.sidebar:
    st.markdown("### 🛒 OPERAÇÃO DE CAIXA")
    st.write(f"Operador ativo: `{st.session_state['usuario_logado']}`")
    st.markdown("---")
    if st.button("Fechar Caixa / Sair", use_container_width=True):
        st.session_state["autenticado"] = False
        st.session_state["usuario_logado"] = ""
        st.session_state["carrinho_compras"] = []
        st.rerun()

st.title("🛒 Sistema de Vendas e Estoque")

# --- CRIAÇÃO DAS ABAS SIMPLES ---
aba1, aba2, aba3, aba4 = st.tabs([
    "📝 1. CADASTRAR PRODUTO", 
    "🧾 2. ENTRADA DE ESTOQUE (NF)", 
    "💻 3. FRENTE DE CAIXA (PDV)", 
    "📊 4. RELATÓRIO DE VENDAS"
])

# --- ABA 1: CADASTRAR PRODUTO ---
with aba1:
    st.subheader("Cadastro de Prateleira")
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

# --- ABA 2: ENTRADA DE ESTOQUE ---
with aba2:
    st.subheader("Abastecer Prateleiras por Nota Fiscal")
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
                data_entrada = datetime.now().strftime("%d/%m/%Y %H:%M")
                cursor.execute("INSERT INTO estoque VALUES (?, ?, ?, ?)", (data_entrada, e_nf.strip(), e_cod.strip(), e_qtd))
                conn.commit()
                st.success(f"Estoque abastecido via NF {e_nf} com +{e_qtd} unidades!")
            else:
                st.error("Código não encontrado! Cadastre o produto na aba 1 primeiro.")
            conn.close()
        else:
            st.warning("Digite o número da Nota Fiscal e o código do produto.")

# --- ABA 3: FRENTE DE CAIXA (PDV COM CARRINHO E TROCO) ---
with aba3:
    st.subheader("Frente de Caixa - Vendas")
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
                    valor_total = preco_p * v_qtd
                    
                    st.session_state["carrinho_compras"].append({
                        "codigo": v_cod.strip(),
                        "nome": nome_p,
                        "quantidade": v_qtd,
                        "total": valor_total
                    })
                    st.success(f"'{nome_p}' colocado no carrinho!")
                    st.rerun()
                else:
                    st.error("Produto não cadastrado!")
                conn.close()
            else:
                st.warning("Digite o código do produto.")

    with col_v2:
        st.markdown("#### 📋 Cupom Fiscal / Carrinho")
        if st.session_state["carrinho_compras"]:
            df_cupom = pd.DataFrame(st.session_state["carrinho_compras"])
            st.dataframe(df_cupom[["codigo", "nome", "quantidade", "total"]], use_container_width=True, hide_index=True)
            
            soma_total_compra = float(df_cupom["total"].sum())
            st.markdown(f"### VALOR TOTAL: R$ {soma_total_compra:.2f}")
            
            st.markdown("---")
            st.markdown("#### 💰 Fechamento de Valores")
            v_pag = st.selectbox("Forma de Pagamento:", ["Dinheiro", "Cartão de Crédito", "Cartão de Débito", "PIX"], key="v3")
            
            # Campo de entrada para quanto o cliente entregou em dinheiro
            valor_recebido = st.number_input("Valor Pago pelo Cliente (R$):", min_value=0.0, value=soma_total_compra, step=1.0)
            
            # Cálculo automático do troco na tela
            troco_calculado = valor_recebido - soma_total_compra
            if troco_calculado > 0:
                st.markdown(f"<p style='color:#F59E0B; font-weight:bold; font-size:20px;'>Troco a Devolver: R$ {troco_calculado:.2f}</p>", unsafe_allow_html=True)
            elif troco_calculado < 0:
                st.markdown(f"<p style='color:#EF4444; font-weight:bold; font-size:16px;'>Falta pagar: R$ {abs(troco_calculado):.2f}</p>", unsafe_allow_html=True)
            
            c_b1, c_b2 = st.columns(2)
            with c_b1:
                if st.button("❌ Cancelar Tudo"):
                    st.session_state["carrinho_compras"] = []
                    st.rerun()
            with c_b2:
                # Bloqueia a confirmação se o valor pago for menor que o total da compra
                if troco_calculado < 0:
                    st.button("✅ Confirmar Venda", disabled=True, help="O valor pago é menor que o total.")
                else:
                    if st.button("✅ Confirmar Venda"):
                        conn = conectar()
                        cursor = conn.cursor()
                        data_venda = datetime.now().strftime("%d/%m/%Y %H:%M")
                        
                        # Salva a venda incluindo o troco correspondente
                        for item in st.session_state["carrinho_compras"]:
                            cursor.execute("INSERT INTO vendas VALUES (?, ?, ?, ?, ?, ?, ?)", 
                                           (data_venda, item["codigo"], item["nome"], item["quantidade"], item["total"], v_pag, max(0.0, troco_calculado)))
                        
                        conn.commit()
                        conn.close()
                        st.session_state["carrinho_compras"] = []
                        st.success("Venda finalizada com sucesso!")
                        st.rerun()
        else:
            st.info("Carrinho vazio. Adicione o primeiro item ao lado.")

# --- ABA 4: RELATÓRIO DE VENDAS ---
with aba4:
    st.subheader("Histórico de Vendas Realizadas")
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT data, codigo, nome, quantidade, total, pagamento, troco FROM vendas ORDER BY rowid DESC")
    dados = cursor.fetchall()
    conn.close()
    
    if dados:
        df = pd.DataFrame(dados, columns=["Data/Hora", "Código", "Produto", "Qtd", "Total R$", "Forma de Pagamento", "Troco R$"])
        st.metric(label="FATURAMENTO TOTAL ACUMULADO", value=f"R$ {df['Total R$'].sum():.2f}")
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhuma venda realizada ainda.")


