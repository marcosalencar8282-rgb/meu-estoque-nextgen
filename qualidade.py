import sqlite3
from datetime import datetime
import streamlit as st
import pandas as pd

# Configuração da página profissional, leve e estável
st.set_page_config(page_title="NextGen | CQ", layout="wide", page_icon="🔬")

# --- CONEXÃO BANCO DE DADOS ---
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
cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        usuario TEXT PRIMARY KEY,
        senha TEXT,
        perfil TEXT
    )
""")
try:
    cursor.execute("INSERT OR IGNORE INTO usuarios (usuario, senha, perfil) VALUES ('admin', 'Master@2026', 'admin')")
except sqlite3.Error:
    pass
conn.commit()
conn.close()

# --- CONTROLE DE SESSÃO ---
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False
if "usuario_logado" not in st.session_state:
    st.session_state["usuario_logado"] = ""
if "perfil_usuario" not in st.session_state:
    st.session_state["perfil_usuario"] = ""
if "tela_ativa" not in st.session_state:
    st.session_state["tela_ativa"] = "relatorio"

# --- TELA DE ACESSO (LOGIN / CADASTRO) ---
if not st.session_state["autenticado"]:
    st.title("🔬 NEXTGEN | CONTROLE DE QUALIDADE")
    
    op_acesso = st.radio("Selecione uma opção:", ["🔑 Fazer Login", "🆕 Criar Nova Conta"], horizontal=True)
    st.markdown("---")
    
    if op_acesso == "🔑 Fazer Login":
        u_in = st.text_input("Usuário:", key="l_user").strip().lower()
        p_in = st.text_input("Senha:", type="password", key="l_pass").strip()
        if st.button("Entrar no Sistema", use_container_width=True):
            if u_in and p_in:
                conn = conectar()
                cursor = conn.cursor()
                cursor.execute("SELECT senha, perfil FROM usuarios WHERE usuario = ?", (u_in,))
                res = cursor.fetchone()
                conn.close()
                
                if res and res[0] == p_in:
                    st.session_state["autenticado"] = True
                    st.session_state["usuario_logado"] = u_in
                    st.session_state["perfil_usuario"] = str(res[1]).strip().lower()
                    st.rerun()
                else:
                    st.error("Usuário ou senha incorretos.")
            else:
                st.warning("Preencha todos os campos.")
                
    else:
        new_u = st.text_input("Escolha seu Usuário:", key="r_user").strip().lower()
        new_p = st.text_input("Escolha sua Senha:", type="password", key="r_pass").strip()
        new_perfil = st.selectbox("Selecione sua Função:", ["cadastro", "laboratorio", "visualizar"])
        if st.button("Salvar Novo Analista", use_container_width=True):
            if new_u and new_p:
                if new_u == "admin":
                    st.error("Nome de usuário restrito.")
                else:
                    conn = conectar()
                    cursor = conn.cursor()
                    try:
                        cursor.execute("INSERT INTO usuarios (usuario, senha, perfil) VALUES (?, ?, ?)", (new_u, new_p, new_perfil))
                        conn.commit()
                        st.success("Conta criada! Selecione 'Fazer Login' acima para entrar.")
                    except sqlite3.IntegrityError:
                        st.error("Este usuário já existe.")
                    finally:
                        conn.close()
            else:
                st.warning("Preencha todos os campos.")
    st.stop()

# --- BARRA SUPERIOR DE INFORMAÇÕES E LOGOUT ---
c_info, c_logout = st.columns([3, 1])
with c_info:
    st.markdown(f"👤 Analista: **{st.session_state['usuario_logado']}** | Perfil: **{st.session_state['perfil_usuario'].upper()}**")
with c_logout:
    if st.button("Sair do Sistema", use_container_width=True):
        st.session_state.clear()
        st.rerun()

st.markdown("---")

# --- GERENCIAMENTO DE MENUS (FORMATO LINEAR SEGURO) ---
perf = st.session_state["perfil_usuario"]
st.markdown("### 🗂️ Navegação do Sistema")

if perf in ["admin", "cadastro"]:
    if st.button("📥 1. Cadastrar Novo Lote", use_container_width=True):
        st.session_state["tela_ativa"] = "cadastro"

if perf in ["admin", "laboratorio"]:
    if st.button("🧫 2. Painel do Laboratório", use_container_width=True):
        st.session_state["tela_ativa"] = "laboratorio"

if perf in ["admin", "cadastro", "laboratorio", "visualizar"]:
    if st.button("📋 3. Ver Relatório de Laudos", use_container_width=True):
        st.session_state["tela_ativa"] = "relatorio"

st.markdown("---")

# --- TELA 1: CADASTRO DE LOTE ---
if st.session_state["tela_ativa"] == "cadastro" and perf in ["admin", "cadastro"]:
    st.subheader("📥 Entrada de Lote para Inspeção")
    
    nf = st.text_input("Número da Nota Fiscal:")
    forn = st.text_input("Nome do Fornecedor:")
    cod = st.text_input("Código do Produto (SKU):")
    desc = st.text_input("Descrição do Produto:")
    lot = st.text_input("Número do Lote:")
    fab = st.text_input("Data de Fabricação:")
    val = st.text_input("Data de Validade:")
    
    if st.button("Confirmar Entrada", use_container_width=True):
        if nf and forn and cod and desc and lot:
            conn = conectar()
            cursor = conn.cursor()
            try:
                data_atual = datetime.now().strftime("%d/%m/%Y %H:%M")
                cursor.execute("INSERT INTO inspeccao (data_chegada, nota_fiscal, fornecedor, codigo, descricao, lote, fabricacao, validade) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (data_atual, nf, forn, cod, desc, lot, fab, val))
                conn.commit()
                st.success(f"Lote {lot} enviado para o laboratório com sucesso!")
            except sqlite3.IntegrityError:
                st.error("Erro: Este número de lote já existe no sistema.")
            finally:
                conn.close()
        else:
            st.warning("Preencha todos os campos obrigatórios.")

# --- TELA 2: PAINEL DO LABORATÓRIO ---
elif st.session_state["tela_ativa"] == "laboratorio" and perf in ["admin", "laboratorio"]:
    st.subheader("🧫 Avaliação Técnico de Lotes")
    
    conn = conectar()
    df_pendentes = pd.read_sql_query("SELECT id_laudo, lote, descricao, fornecedor, status FROM inspeccao WHERE status = 'Em Análise'", conn)
    conn.close()
    
    if df_pendentes.empty:
        st.info("Nenhum lote aguardando análise no momento.")
    else:
        st.dataframe(df_pendentes, use_container_width=True, hide_index=True)
        st.markdown("---")
        
        lote_sel = st.selectbox("Selecione o Lote para dar o parecer:", df_pendentes["lote"].tolist())
        novo_status = st.selectbox("Resultado da Análise:", ["Aprovado", "Reprovado"])
        
        if st.button("Gravar Decisão do Laudo", use_container_width=True):
            conn = conectar()
            cursor = conn.cursor()
            cursor.execute("UPDATE inspeccao SET status = ?, responsavel = ? WHERE lote = ?", (novo_status, st.session_state["usuario_logado"], lote_sel))
            conn.commit()
            conn.close()
            st.success(f"O lote {lote_sel} foi updated para {novo_status}!")
            st.rerun()

# --- TELA 3: RELATÓRIO GERAL (CONCLUÍDO E REESCRITO) ---
elif st.session_state["tela_ativa"] == "relatorio":
    st.subheader("📋 Histórico Completo de Laudos Emitidos")
    
    conn = conectar()
    df_geral = pd.read_sql_query("SELECT * FROM inspeccao ORDER BY id_laudo DESC", conn)
    conn.close()
    
    if df_geral.empty:
        st.info("Nenhum laudo encontrado no banco de dados.")
    else:
        df_formatado = df_geral.rename(columns={
            "id_laudo": "ID Laudo",
            "data_chegada": "Data Chegada",
            "nota_fiscal": "Nota Fiscal",
            "fornecedor": "Fornecedor",
            "codigo": "Código SKU",
            "descricao": "Descrição",
            "lote": "Lote",
            "fabricacao": "Fabricação",
            "validade": "Validade",
            "status": "Status",
            "responsavel": "Responsável"
        })
        st.dataframe(df_formatado, use_container_width=True, hide_index=True)


