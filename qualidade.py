import sqlite3
from datetime import datetime
import streamlit as st
import pandas as pd

# Configuração da página padrão, leve e estável
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
        c_log1, c_log2 = st.columns(2)
        with c_log1:
            u_in = st.text_input("Usuário:", key="l_user").strip().lower()
        with c_log2:
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
        c_cad1, c_cad2, c_cad3 = st.columns(3)
        with c_cad1:
            new_u = st.text_input("Escolha seu Usuário:", key="r_user").strip().lower()
        with c_cad2:
            new_p = st.text_input("Escolha sua Senha:", type="password", key="r_pass").strip()
        with c_cad3:
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
c_info, c_logout = st.columns(2)
with c_info:
    st.markdown(f"👤 Analista: **{st.session_state['usuario_logado'].upper()}** | Perfil: **{st.session_state['perfil_usuario'].upper()}**")
with c_logout:
    if st.button("Sair do Sistema", use_container_width=True):
        st.session_state.clear()
        st.rerun()

st.markdown("---")

# --- PAINEL DE RESUMOS COMPACTO ---
conn = conectar()
cursor = conn.cursor()

cursor.execute("SELECT COUNT(*) FROM inspeccao")
total_lotes = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM inspeccao WHERE status = 'Em Análise'")
analise_lotes = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM inspeccao WHERE status = 'Aprovado'")
aprovados_lotes = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM inspeccao WHERE status = 'Reprovado'")
reprovados_lotes = cursor.fetchone()[0]

conn.close()

# Exibição das métricas simplificadas na tela
c_m1, c_m2, c_m3, c_m4 = st.columns(4)
with c_m1:
    st.info(f"📋 Total de Lotes: {total_lotes}")
with c_m2:
    st.warning(f"⏳ Em Análise: {analise_lotes}")
with c_m3:
    st.success(f"✅ Aprovados: {aprovados_lotes}")
with c_m4:
    st.error(f"❌ Reprovados: {reprovados_lotes}")

st.markdown("---")

# --- GERENCIAMENTO DE MENUS ---
perf = st.session_state["perfil_usuario"]
st.markdown("### 🗂️ Navegação do Sistema")

c1, c2, c3, c4 = st.columns(4)
with c1:
    if perf in ["admin", "cadastro"]:
        if st.button("📥 1. Cadastrar Novo Lote", use_container_width=True):
            st.session_state["tela_ativa"] = "cadastro"
            st.rerun()
with c2:
    if perf in ["admin", "laboratorio"]:
        if st.button("🧫 2. Painel do Laboratório", use_container_width=True):
            st.session_state["tela_ativa"] = "laboratorio"
            st.rerun()
with c3:
    if perf in ["admin", "cadastro", "laboratorio", "visualizar"]:
        if st.button("📋 3. Ver Relatório de Laudos", use_container_width=True):
            st.session_state["tela_ativa"] = "relatorio"
            st.rerun()
with c4:
    if perf == "admin":
        if st.button("⚙️ 4. Gerenciar Usuários", use_container_width=True):
            st.session_state["tela_ativa"] = "gerenciar_usuarios"
            st.rerun()

st.markdown("---")

# --- FUNÇÕES DE RENDERIZAÇÃO DAS TELAS ---

def tela_cadastro():
    st.subheader("📥 Entrada de Lote para Inspeção")
    cl1, cl2, cl3, cl4 = st.columns(4)
    with cl1:
        nf = st.text_input("Nº NF:")
    with cl2:
        forn = st.text_input("Fornecedor:")
    with cl3:
        cod = st.text_input("SKU:")
    with cl4:
        desc = st.text_input("Descrição:")
        
    cl5, cl6, cl7 = st.columns(3)
    with cl5:
        lot = st.text_input("Lote:")
    with cl6:
        fab = st.text_input("Fabricação:")
    with cl7:
        val = st.text_input("Validade:")
        
    st.write("")
    if st.button("Confirmar Entrada", use_container_width=True):
        if nf and forn and cod and desc and lot:
            conn = conectar()
            cursor = conn.cursor()
            try:
                data_atual = datetime.now().strftime("%d/%m/%Y %H:%M")
                cursor.execute("""
                    INSERT INTO inspeccao (data_chegada, nota_fiscal, fornecedor, codigo, descricao, lote, fabricacao, validade) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (data_atual, nf, forn, cod, desc, lot, fab, val))
                conn.commit()
                st.success(f"Lote {lot} enviado com sucesso!")
                st.rerun()
            except sqlite3.IntegrityError:
                st.error("Erro: Este lote já existe.")
            finally:
                conn.close()
        else:
            st.warning("Preencha os campos obrigatórios.")

def tela_laboratorio():
    st.subheader("🧫 Avaliação Técnico de Lotes")
    conn = conectar()
    df_pendentes = pd.read_sql_query("SELECT id_laudo, lote, descricao, fornecedor, status FROM inspeccao WHERE status = 'Em Análise'", conn)
    conn.close()
    
    if df_pendentes.empty:
        st.info("Nenhum lote aguardando análise.")
    else:
        st.dataframe(df_pendentes, use_container_width=True, hide_index=True)
        st.markdown("---")
        
        cl_lab1, cl_lab2 = st.columns(2)
        with cl_lab1:
            lote_sel = st.selectbox("Selecionar Lote:", df_pendentes["lote"].tolist())
        with cl_lab2:
            novo_status = st.selectbox("Resultado:", ["Aprovado", "Reprovado"])
            
        if st.button("Gravar Decisão", use_container_width=True):
            conn = conectar()
            cursor = conn.cursor()
            cursor.execute("UPDATE inspeccao SET status = ?, responsavel = ? WHERE lote = ?", (novo_status, st.session_state["usuario_logado"], lote_sel))
            conn.commit()
            conn.close()
            st.success("Status atualizado!")
            st.rerun()

def tela_relatorio():
    st.subheader("📋 Histórico Completo de Laudos Emitidos")
    conn = conectar()
    df_geral = pd.read_sql_query("SELECT * FROM inspeccao ORDER BY id_laudo DESC", conn)
    conn.close()
    
    if df_geral.empty:
        st.info("Nenhum laudo encontrado.")
    else:
        st.dataframe(df_geral, use_container_width=True, hide_index=True)

def tela_gerenciar_usuarios():
    st.subheader("⚙️ Gerenciar Analistas Cadastrados")
    conn = conectar()
    df_usuarios = pd.read_sql_query("SELECT usuario, perfil FROM usuarios WHERE usuario != 'admin'", conn)
    conn.close()
    
    if df_usuarios.empty:
        st.info("Nenhum usuário operacional cadastrado.")
    else:
        st.dataframe(df_usuarios, use_container_width=True, hide_index=True)
        st.markdown("---")
        
        user_remover = st.selectbox("Selecione para remover:", df_usuarios["usuario"].tolist())

