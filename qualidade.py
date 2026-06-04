import sqlite3
from datetime import datetime
import streamlit as st
import pandas as pd

# Configuração da página leve
st.set_page_config(page_title="NextGen | Controle de Qualidade", layout="wide", page_icon="🔬")

# --- CONTROLE DE SESSÃO / LOGIN ---
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False
if "usuario_logado" not in st.session_state:
    st.session_state["usuario_logado"] = ""

# LISTA DE USUÁRIOS PERMITIDOS
USUARIOS_PERMITIDOS = {
    "admin": "Master@2026",
    "marcos": "931481",
    "laboratorio": "LabCQ2026"
}

# --- CONEXÃO COM O BANCO DE DADOS ---
def conectar():
    return sqlite3.connect("controle_qualidade_forn.db")

conn = conectar()
cursor = conn.cursor()
# ATUALIZAÇÃO: Adicionada a coluna fornecedor na tabela de inspeção
cursor.execute("""
    CREATE TABLE IF NOT EXISTS inspeccao (
        id_laudo INTEGER PRIMARY KEY AUTOINCREMENT,
        data_chegada TEXT,
        nota_fiscal TEXT,
        fornecedor TEXT,
        codigo TEXT,
        descricao TEXT,
        lote TEXT UNIQUE,
        fabricacao TEXT,
        validade TEXT,
        status TEXT DEFAULT 'Em Análise',
        responsavel TEXT DEFAULT 'Pendente'
    )
""")
conn.commit()
conn.close()

# TELA DE LOGIN
if not st.session_state["autenticado"]:
    st.markdown("<h1 style='text-align: center;'>🔬 NEXTGEN | CONTROLE DE QUALIDADE</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #64748B;'>Inspeção de Lotes, Validades e Laudos Laboratoriais</p>", unsafe_allow_html=True)

    col_l1, col_l2, col_l3 = st.columns([1, 1.2, 1])
    with col_l2:
        u_input = st.text_input("Usuário / Analista:")
        p_input = st.text_input("Senha:", type="password")
        if st.button("Acessar Módulo CQ", use_container_width=True):
            if u_input.strip() in USUARIOS_PERMITIDOS and USUARIOS_PERMITIDOS[u_input.strip()] == p_input.strip():
                st.session_state["autenticado"] = True
                st.session_state["usuario_logado"] = u_input.strip()
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos.")
    st.stop()

# BARRA LATERAL (LOGOFF)
with st.sidebar:
    st.markdown("### 🧪 ANALISTA LOGADO")
    st.write(f"Usuário: `{st.session_state['usuario_logado']}`")
    st.markdown("---")
    if st.button("Sair do Sistema", use_container_width=True):
        st.session_state["autenticado"] = False
        st.session_state["usuario_logado"] = ""
        st.rerun()

st.title("🔬 Controle de Qualidade e Liberação de Lotes")

# CRIAÇÃO DAS ABAS DO CQ
aba1, aba2, aba3 = st.tabs([
    "📥 1. RECEPÇÃO / CADASTRAR LOTE", 
    "🧫 2. PAINEL DO LABORATÓRIO", 
    "📋 3. RELATÓRIO GERAL DE LAUDOS"
])

# --- ABA 1: RECEPÇÃO / CADASTRAR LOTE ---
with aba1:
    st.subheader("Entrada de Produto para Inspeção")
    
    # Inclusão dos campos de identificação comercial
    q_nf = st.text_input("Número da Nota Fiscal (NF-e):", key="q_nf")
    q_for = st.text_input("Nome do Fornecedor / Fabricante:", key="q_for")
    q_cod = st.text_input("Código do Produto (SKU/EAN):", key="q1")
    q_des = st.text_input("Descrição / Nome do Produto:", key="q2")
    q_lot = st.text_input("Número do Lote do Fabricante:", key="q3")
    
    c_f1, c_f2 = st.columns(2)
    with c_f1:
        q_fab = st.text_input("Data de Fabricação (Ex: 01/06/2026):", key="q4")
    with c_f2:
        q_val = st.text_input("Data de Validade (Ex: 01/12/2026):", key="q5")
        
    if st.button("Dar Entrada para Análise"):
        if q_nf and q_for and q_cod and q_des and q_lot:
            conn = conectar()
            cursor = conn.cursor()
            try:
                dt_atual = datetime.now().strftime("%d/%m/%Y %H:%M")
                cursor.execute("""
                    INSERT INTO inspeccao (data_chegada, nota_fiscal, fornecedor, codigo, descricao, lote, fabricacao, validade) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (dt_atual, q_nf.strip(), q_for.strip(), q_cod.strip(), q_des.strip(), q_lot.strip(), q_fab.strip(), q_val.strip()))
                conn.commit()
                st.success(f"Lote {q_lot} da NF {q_nf} enviado para o Laboratório com status 'Em Análise'!")
            except:
                st.error("Erro: Este número de Lote já está cadastrado no sistema!")
            finally:
                conn.close()
        else:
            st.warning("Por favor, preencha a Nota Fiscal, Fornecedor, Código, Descrição e o Lote.")

# --- ABA 2: PAINEL DO LABORATÓRIO (APROVAR OU REPROVAR) ---
with aba2:
    st.subheader("Painel de Julgamento Laboratorial")
    
    conn = conectar()
    cursor = conn.cursor()
    # Puxa o lote, descrição, nota fiscal e fornecedor para a análise do laboratório
    cursor.execute("SELECT lote, descricao, nota_fiscal, fornecedor FROM inspeccao WHERE status = 'Em Análise'")
    lotes_pendentes = cursor.fetchall()
    conn.close()
    
    if lotes_pendentes:
        # Exibe as informações completas na caixa de seleção
        lista_opcoes = [f"Lote: {row[0]} | Prod: {row[1]} | Forn: {row[3]} | NF: {row[2]}" for row in lotes_pendentes]
        lote_selecionado_txt = st.selectbox("Selecione o Lote Pendente para Emitir o Laudo:", lista_opcoes)
        
        # Extrai o índice correto para dar baixa no lote selecionado
        lote_final = lotes_pendentes[lista_opcoes.index(lote_selecionado_txt)][0]
        
        st.markdown("---")
        st.markdown("#### ⚖️ Decisão do Laboratório:")
        
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            if st.button("🟢 APROVAR LOTE", use_container_width=True):
                conn = conectar()
                cursor = conn.cursor()
                cursor.execute("UPDATE inspeccao SET status = 'APROVADO', responsavel = ? WHERE lote = ?", 
                               (st.session_state["usuario_logado"], lote_final))
                conn.commit()
                conn.close()
                st.success(f"Lote {lote_final} LIBERADO para uso/comercialização com sucesso!")
                st.rerun()
                
        with col_btn2:
            if st.button("🔴 REPROVAR LOTE", use_container_width=True):
                conn = conectar()
                cursor = conn.cursor()
                cursor.execute("UPDATE inspeccao SET status = 'REPROVADO', responsavel = ? WHERE lote = ?", 
                               (st.session_state["usuario_logado"], lote_final))
                conn.commit()
                conn.close()
                st.error(f"Lote {lote_final} BLOQUEADO E REPROVADO pelo controle de qualidade!")
                st.rerun()
    else:
        st.info("Excelente! Nenhum lote pendente de análise no laboratório no momento.")

# --- ABA 3: RELATÓRIO GERAL DE LAUDOS ---
with aba3:
    st.subheader("Histórico Analítico de Controle de Qualidade")
    
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT data_chegada, nota_fiscal, fornecedor, codigo, descricao, lote, fabricacao, validade, status, responsavel 
        FROM inspeccao ORDER BY id_laudo DESC
    """)
    dados_cq = cursor.fetchall()
    conn.close()
    
    if dados_cq:
        df_cq = pd.DataFrame(dados_cq, columns=[
            "Data Chegada", "Nota Fiscal", "Fornecedor", "Código SKU", "Produto", "Lote", "Fabricação", "Validade", "Resultado CQ", "Responsável"
        ])
        
        m1, m2, m3 = st.columns(3)
        with m1:
            st.metric(label="Total de Lotes Inspecionados", value=len(df_cq))
        with m2:
            aprovados_qtd = len(df_cq[df_cq["Resultado CQ"] == "APROVADO"])
            st.metric(label="Lotes Aprovados", value=aprovados_qtd)
        with m3:
            reprovados_qtd = len(df_cq[df_cq["Resultado CQ"] == "REPROVADO"])
            st.metric(label="Lotes Reprovados (Descarte)", value=reprovados_qtd)
            
        st.markdown("<br>", unsafe_allow_html=True)
        st.dataframe(df_cq, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum registro de laudo emitido no banco de dados ainda.")

