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
if "perfil_usuario" not in st.session_state:
    st.session_state["perfil_usuario"] = ""

# LISTA DE USUÁRIOS PERMITIDOS E SEUS PERFIS/FUNÇÕES (ORIGINAL)
USUARIOS_PERMITIDOS = {
    "admin": {"senha": "Master@2026", "perfil": "admin"},
    "marcos": {"senha": "931481", "perfil": "cadastro"},
    "laboratorio": {"senha": "LabCQ2026", "perfil": "laboratorio"},
    "visitante": {"senha": "123", "perfil": "visualizar"}
}

# --- CONEXÃO COM O BANCO DE DADOS ---
def conectar():
    return sqlite3.connect("controle_qualidade_forn.db")

conn = conectar()
cursor = conn.cursor()
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

# TELA DE LOGIN (ORIGINAL)
if not st.session_state["autenticado"]:
    st.markdown("<h1 style='text-align: center;'>🔬 NEXTGEN | CONTROLE DE QUALIDADE</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #64748B;'>Inspeção de Lotes, Validades e Laudos Laboratoriais</p>", unsafe_allow_html=True)

    col_l1, col_l2, col_l3 = st.columns([1, 1.2, 1])
    with col_l2:
        u_input = st.text_input("Usuário / Analista:").strip()
        p_input = st.text_input("Senha:", type="password").strip()
        
        if st.button("Acessar Módulo CQ", use_container_width=True):
            if u_input in USUARIOS_PERMITIDOS and USUARIOS_PERMITIDOS[u_input]["senha"] == p_input:
                st.session_state["autenticado"] = True
                st.session_state["usuario_logado"] = u_input
                st.session_state["perfil_usuario"] = USUARIOS_PERMITIDOS[u_input]["perfil"]
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos.")
    st.stop()

# BARRA LATERAL (LOGOFF E INFORMAÇÕES - ORIGINAL)
with st.sidebar:
    st.markdown("### 🧪 ANALISTA LOGADO")
    st.write(f"Usuário: `{st.session_state['usuario_logado']}`")
    st.write(f"Perfil: `{(st.session_state['perfil_usuario']).upper()}`")
    st.markdown("---")
    if st.button("Sair do Sistema", use_container_width=True):
        st.session_state["autenticado"] = False
        st.session_state["usuario_logado"] = ""
        st.session_state["perfil_usuario"] = ""
        st.rerun()

st.title("🔬 Controle de Qualidade e Liberação de Lotes")

# --- GERENCIAMENTO DE ABAS POR PERFIL ---
perfil = st.session_state["perfil_usuario"]

abas_disponiveis = []
if perfil in ["admin", "cadastro"]:
    abas_disponiveis.append("📥 1. RECEPÇÃO / CADASTRAR LOTE")
if perfil in ["admin", "laboratorio"]:
    abas_disponiveis.append("🧫 2. PAINEL DO LABORATÓRIO")
if perfil in ["admin", "cadastro", "laboratorio", "visualizar"]:
    abas_disponiveis.append("📋 3. RELATÓRIO GERAL DE LAUDOS")

abas = st.tabs(abas_disponiveis)
aba_index = 0

# --- ABA 1: RECEPÇÃO / CADASTRAR LOTE ---
if "📥 1. RECEPÇÃO / CADASTRAR LOTE" in abas_disponiveis:
    with abas[aba_index]:
        aba_index += 1
        st.subheader("Entrada de Produto para Inspeção")
        
        with st.form("form_cadastro", clear_on_submit=True):
            q_nf = st.text_input("Número da Nota Fiscal (NF-e):")
            q_for = st.text_input("Nome do Fornecedor / Fabricante:")
            q_cod = st.text_input("Código do Produto (SKU/EAN):")
            q_des = st.text_input("Descrição / Nome do Produto:")
            q_lot = st.text_input("Número do Lote do Fabricante:")
            
            c_f1, c_f2 = st.columns(2)
            with c_f1:
                q_fab = st.text_input("Data de Fabricação (Ex: 01/06/2026):")
            with c_f2:
                q_val = st.text_input("Data de Validade (Ex: 01/12/2026):")
                
            enviar = st.form_submit_button("Dar Entrada para Análise", use_container_width=True)
            
        if enviar:
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
                    
                    st.session_state["sucesso_cadastro"] = f"Lote {q_lot.strip()} cadastrado com sucesso!"
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("Erro: Este número de Lote já está cadastrado no sistema!")
                finally:
                    conn.close()
            else:
                st.warning("Por favor, preencha a Nota Fiscal, Fornecedor, Código, Descrição e o Lote.")

    if "sucesso_cadastro" in st.session_state:
        st.success(st.session_state["sucesso_cadastro"])
        del st.session_state["sucesso_cadastro"]

# --- ABA 2: PAINEL DO LABORATÓRIO (APROVAR OU REPROVAR) ---
if "🧫 2. PAINEL DO LABORATÓRIO" in abas_disponiveis:
    with abas[aba_index]:
        aba_index += 1
        st.subheader("Painel de Julgamento Laboratorial")
        
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT lote, descricao, nota_fiscal, fornecedor FROM inspeccao WHERE status = 'Em Análise'")
        lotes_pendentes = cursor.fetchall()
        conn.close()
        
        if lotes_pendentes:
            # Lista as opções de forma limpa extraindo os dados da tupla nativa do SQLite
            lista_opcoes = [f"Lote: {row[0]} | Prod: {row[1]} | Forn: {row[3]} | NF: {row[2]}" for row in lotes_pendentes]
            lote_selecionado_txt = st.selectbox("Selecione o Lote Pendente para Emitir o Laudo:", lista_opcoes)
            
            # Obtém o lote exato da opção que o usuário escolheu
            lote_final = lotes_pendentes[lista_opcoes.index(lote_selecionado_txt)][0]
            
            st.markdown("---")
            st.markdown("#### ⚖️ Decisão do Laboratório:")
            
            # Divide os dois botões perfeitamente lado a lado
            col_btn1, col_btn2 = st.columns(2)
            
            with col_btn1:
                if st.button("🟢 APROVAR LOTE", use_container_width=True):
                    conn = conectar()
                    cursor = conn.cursor()
                    cursor.execute("UPDATE inspeccao SET status = 'APROVADO', responsavel = ? WHERE lote = ?", 
                                   (st.session_state["usuario_logado"], lote_final))
                    conn.commit()
                    conn.close()
                    st.rerun()
                    
            with col_btn2:
                if st.button("🔴 REPROVAR LOTE", use_container_width=True):
                    conn = conectar()
                    cursor = conn.cursor()
                    cursor.execute("UPDATE inspeccao SET status = 'REPROVADO', responsavel = ? WHERE lote = ?", 
                                   (st.session_state["usuario_logado"], lote_final))
                    conn.commit()
                    conn.close()
                    st.rerun()
        else:
            st.info("Excelente! Nenhum lote pendente de análise laboratorial.")

# --- ABA 3: RELATÓRIO GERAL DE LAUDOS ---
if "📋 3. RELATÓRIO GERAL DE LAUDOS" in abas_disponiveis:
    with abas[aba_index]:
        aba_index += 1
        st.subheader("Histórico Geral de Inspeções")
        
        conn = conectar()
        df = pd.read_sql_query("SELECT * FROM inspeccao ORDER BY id_laudo DESC", conn)
        conn.close()
        
        if not df.empty:
            df.columns = [
                "ID Laudo", "Data Chegada", "Nota Fiscal", "Fornecedor", 
                "Código", "Descrição", "Lote", "Fabricação", "Validade", 
                "Status", "Responsável"
            ]
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("Nenhum registro encontrado no banco de dados até o momento.")
