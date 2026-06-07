import sqlite3
from datetime import datetime
import streamlit as st
import pandas as pd

# Configuração básica inicial
st.set_page_config(page_title="NextGen Supermercado", layout="wide", page_icon="🛒")

# --- CONTROLE DE SESSÃO / LOGIN ---
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False
if "usuario_logado" not in st.session_state:
    st.session_state["usuario_logado"] = ""
if "carrinho_compras" not in st.session_state:
    st.session_state["carrinho_compras"] = []

# LISTA DE OPERADORES E SENHAS ORIGINAL
USUARIOS_PERMITIDOS = {
    "admin": "Master@2026",
    "lucas": "Lucas#Estoque",
    "marcos": "931481"
}

# --- BANCO DE DADOS BLINDADO ---
def conectar():
    return sqlite3.connect("banco_mercado_final.db")

# Criação das tabelas de forma limpa e direta
conn = conectar()
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS produtos (codigo TEXT UNIQUE, nome TEXT, preco REAL)")
cursor.execute("CREATE TABLE IF NOT EXISTS estoque (data TEXT, nota_fiscal TEXT, codigo TEXT, quantidade INTEGER)")
cursor.execute("CREATE TABLE IF NOT EXISTS vendas (data TEXT, codigo TEXT, nome TEXT, quantidade INTEGER, total REAL, pagamento TEXT, troco REAL)")
conn.commit()
conn.close()

# TELA DE LOGIN (SEM ERROS)
if not st.session_state["autenticado"]:
    st.markdown("<h1 style='text-align: center;'>🛒 NEXTGEN SUPERMERCADO</h1>", unsafe_allow_html=True)
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

# BARRA LATERAL SIMPLES (MENU DE SELEÇÃO POR BOTÕES)
with st.sidebar:
    st.markdown(f"👤 Operador: `{st.session_state['usuario_logado']}`")
    st.markdown("---")
    st.markdown("### 🛠️ SELECIONE A TELA:")
    
    if "tela_atual" not in st.session_state:
        # Define a tela inicial correta baseado no seu parâmetro de usuário
        if st.session_state["usuario_logado"] == "lucas":
            st.session_state["tela_current"] = "Estoque"
        else:
            st.session_state["tela_current"] = "PDV"

    usuario = st.session_state["usuario_logado"]

    # Exibe os botões baseados estritamente nas permissões do operador
    if usuario == "admin":
        if st.button("💻 1. Frente de Caixa (PDV)", use_container_width=True): st.session_state["tela_current"] = "PDV"
        if st.button("📝 2. Cadastrar Produto", use_container_width=True): st.session_state["tela_current"] = "Cadastro"
        if st.button("🧾 3. Entrada de Estoque (NF)", use_container_width=True): st.session_state["tela_current"] = "Estoque"
        if st.button("📊 4. Relatório de Vendas", use_container_width=True): st.session_state["tela_current"] = "Relatorio"
        if st.button("📈 5. Histórico de Entradas", use_container_width=True): st.session_state["tela_current"] = "Historico"
    elif usuario == "lucas":
        if st.button("🧾 1. Entrada de Estoque (NF)", use_container_width=True): st.session_state["tela_current"] = "Estoque"
        if st.button("📈 2. Histórico de Entradas", use_container_width=True): st.session_state["tela_current"] = "Historico"
    elif usuario == "marcos":
        if st.button("💻 1. Frente de Caixa (PDV)", use_container_width=True): st.session_state["tela_current"] = "PDV"

    st.markdown("---")
    if st.button("Fechar Caixa / Sair", use_container_width=True):
        st.session_state["autenticado"] = False
        st.session_state["usuario_logado"] = ""
        st.session_state["carrinho_compras"] = []
        st.rerun()

# --- CARREGAMENTO RÍGIDO DAS TELAS INDEPENDENTES ---
tela = st.session_state["tela_current"]

if tela == "PDV":
    st.title("💻 Frente de Caixa - Vendas")
    col_v1, col_v2 = st.columns([1, 1.5])
    
    with col_v1:
        st.markdown("#### 🔍 Registrar Item")
        v_cod = st.text_input("Código do Produto:", key="v1")
        v_qtd = st.number_input("Quantidade:", min_value=1, value=1, key="v2")
        if st.button("Adicionar ao Carrinho"):
            if v_cod:
                conn = conectar()
                cursor = conn.cursor()
                cursor.execute("SELECT nome, preco FROM produtos WHERE codigo = ?", (v_cod.strip(),))
                prod = cursor.fetchone()
                if prod:
                    st.session_state["carrinho_compras"].append({"codigo": v_cod.strip(), "nome": prod[0], "quantidade": v_qtd, "total": (prod[1] * v_qtd)})
                    st.success(f"'{prod[0]}' adicionado!")
                    st.rerun()
                else:
                    st.error("Produto não encontrado!")
                conn.close()

    with col_v2:
        st.markdown("#### 📋 Cupom Fiscal / Carrinho")
        if st.session_state["carrinho_compras"]:
            df_cupom = pd.DataFrame(st.session_state["carrinho_compras"])
            st.dataframe(df_cupom, use_container_width=True, hide_index=True)
            soma_total = float(df_cupom["total"].sum())
            st.markdown(f"### TOTAL COMPRA: R$ {soma_total:.2f}")
            
            v_pag = st.selectbox("Forma Pagamento:", ["Dinheiro", "Cartão", "PIX"])
            valor_recebido = st.number_input("Valor Pago Cliente:", min_value=0.0, value=soma_total)
            if (valor_recebido - soma_total) > 0:
                st.warning(f"Troco: R$ {(valor_recebido - soma_total):.2f}")
            
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
                    st.toast("🛒 Venda Concluída!")
                    st.rerun()
        else:
            st.info("Carrinho de compras vazio.")

elif tela == "Cadastro":
    st.title("📝 Cadastrar Produto na Prateleira")
    c_cod = st.text_input("Código do Produto:")
    c_nom = st.text_input("Nome do Produto:")
    c_pre = st.number_input("Preço de Venda (R$):", min_value=0.05, value=2.50)
    if st.button("Gravar Produto"):
        if c_cod and c_nom:
            conn = conectar()
            cursor = conn.cursor()
            try:
                cursor.execute("INSERT INTO produtos VALUES (?, ?, ?)", (c_cod.strip(), c_nom.strip(), c_pre))
                conn.commit()
                st.success(f"'{c_nom}' gravado!")
            except:
                st.error("Esse código já existe!")
            conn.close()

elif tela == "Estoque":
    st.title("🧾 Entrada de Estoque por Nota Fiscal")
    e_nf = st.text_input("Número da Nota (NF-e):")
    e_cod = st.text_input("Código do Produto:")
    e_qtd = st.number_input("Quantidade Abastecida:", min_value=1, value=10)
    if st.button("Confirmar Entrada de Nota"):
        if e_nf and e_cod:
            conn = conectar()
            cursor = conn.cursor()
            cursor.execute("SELECT codigo FROM produtos WHERE codigo = ?", (e_cod.strip(),))
            if cursor.fetchone():
                data_e = datetime.now().strftime("%d/%m/%Y %H:%M")
                # Salva apenas o código e a quantidade de forma limpa, sem risco de tupla quebrada
                cursor.execute("INSERT INTO estoque VALUES (?, ?, ?, ?)", (data_e, e_nf.strip(), e_cod.strip(), int(e_qtd)))
                conn.commit()
                st.success("Estoque alimentado com sucesso!")
            else:
                st.error("Código não cadastrado!")
            conn.close()

elif tela == "Relatorio":
    st.title("📊 Relatório de Faturamento Comercial")
    conn = conectar()
    df_v = pd.read_sql_query("SELECT data AS [Data/Hora], codigo AS [Cód], nome AS [Produto], quantidade AS [Qtd], total AS [Total R$], pagamento AS [Pagamento] FROM vendas ORDER BY rowid DESC", conn)
    conn.close()
    if not df_v.empty:
        st.metric("Faturamento Bruto Total", f"R$ {df_v['Total R$'].sum():.2f}")
        st.dataframe(df_v, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhuma venda realizada.")

elif tela == "Historico":
    st.title("📈 Histórico de Entrada de Mercadorias")
    conn = conectar()
    # SOLUÇÃO REAL DO HISTÓRICO: O banco cruza o código da tabela estoque com a tabela produtos e traz o nome perfeito na tela
    df_e = pd.read_sql_query('''
        SELECT e.data AS [Data Entrada], e.nota_fiscal AS [Nota Fiscal], e.codigo AS [Cód], 
               p.nome AS [Produto], e.quantidade AS [Qtd Entrada]
        FROM estoque e
        JOIN produtos p ON e.codigo = p.codigo
        ORDER BY e.rowid DESC
    ''', conn)
    conn.close()
    if not df_e.empty:
        st.dataframe(df_e, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhuma nota fiscal de entrada foi registrada.")
