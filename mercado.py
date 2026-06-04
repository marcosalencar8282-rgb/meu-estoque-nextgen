import sqlite3
from datetime import datetime
import streamlit as st
import pandas as pd

st.title("🛒 Sistema de Vendas e Estoque Simplificado")

# --- CONEXÃO DIRETA COM O BANCO ---
def conectar():
    return sqlite3.connect("mercado_carrinho_simples.db")

conn = conectar()
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS produtos (codigo TEXT UNIQUE, nome TEXT, preco REAL)")
cursor.execute("CREATE TABLE IF NOT EXISTS estoque (codigo TEXT, quantidade INTEGER)")
cursor.execute("CREATE TABLE IF NOT EXISTS vendas (data TEXT, codigo TEXT, nome TEXT, quantidade INTEGER, total REAL, pagamento TEXT)")
conn.commit()
conn.close()

# --- CONTROLE DE MEMÓRIA DO CARRINHO ---
if "carrinho_compras" not in st.session_state:
    st.session_state["carrinho_compras"] = []

# --- CRIAÇÃO DAS ABAS SIMPLES ---
aba1, aba2, aba3, aba4 = st.tabs([
    "📝 1. CADASTRAR PRODUTO", 
    "🧾 2. ENTRADA DE ESTOQUE", 
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
    st.subheader("Abastecer Prateleiras")
    e_cod = st.text_input("Código do Produto para Abastecer:", key="e1")
    e_qtd = st.number_input("Quantidade que está Entrando:", min_value=1, value=10, key="e2")
    
    if st.button("Confirmar Entrada"):
        if e_cod:
            conn = conectar()
            cursor = conn.cursor()
            cursor.execute("SELECT nome FROM produtos WHERE codigo = ?", (e_cod.strip(),))
            prod = cursor.fetchone()
            
            if prod:
                cursor.execute("INSERT INTO estoque VALUES (?, ?)", (e_cod.strip(), e_qtd))
                conn.commit()
                st.success(f"Estoque abastecido com +{e_qtd} unidades!")
            else:
                st.error("Código não encontrado! Cadastre o produto na aba 1 primeiro.")
            conn.close()
        else:
            st.warning("Digite o código do produto.")

# --- ABA 3: FRENTE DE CAIXA (PDV COM CARRINHO) ---
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
                    
                    # Guarda na memória temporária do carrinho
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
            
            soma_total_compra = df_cupom["total"].sum()
            st.markdown(f"### VALOR TOTAL: R$ {soma_total_compra:.2f}")
            
            v_pag = st.selectbox("Forma de Pagamento:", ["Dinheiro", "Cartão de Crédito", "Cartão de Débito", "PIX"], key="v3")
            
            c_b1, c_b2 = st.columns(2)
            with c_b1:
                if st.button("❌ Cancelar Tudo"):
                    st.session_state["carrinho_compras"] = []
                    st.rerun()
            with c_b2:
                if st.button("✅ Confirmar Venda"):
                    conn = conectar()
                    cursor = conn.cursor()
                    data_venda = datetime.now().strftime("%d/%m/%Y %H:%M")
                    
                    # Salva todos os itens do carrinho um por um no banco de dados
                    for item in st.session_state["carrinho_compras"]:
                        cursor.execute("INSERT INTO vendas VALUES (?, ?, ?, ?, ?, ?)", 
                                       (data_venda, item["codigo"], item["nome"], item["quantidade"], item["total"], v_pag))
                    
                    conn.commit()
                    conn.close()
                    st.session_state["carrinho_compras"] = []
                    st.success("Venda finalizada com sucesso!")
                    st.rerun()
        else:
            st.info("Carrinho vazio. Adicione o primeiro item ao lado.")

# --- ABA 4: RELATÓRIO DE VENDAS ---
with aba_4:
    st.subheader("Histórico de Vendas Realizadas")
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT data, codigo, nome, quantidade, total, pagamento FROM vendas ORDER BY rowid DESC")
    dados = cursor.fetchall()
    conn.close()
    
    if dados:
        df = pd.DataFrame(dados, columns=["Data/Hora", "Código", "Produto", "Qtd", "Total R$", "Forma de Pagamento"])
        st.metric(label="FATURAMENTO TOTAL ACUMULADO", value=f"R$ {df['Total R$'].sum():.2f}")
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhuma venda realizada ainda.")

