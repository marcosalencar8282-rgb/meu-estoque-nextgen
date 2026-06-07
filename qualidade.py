import sqlite3
from datetime import datetime
import streamlit as st
import pandas as pd

# Configuração da página
st.set_page_config(page_title="NextGen | Controle de Qualidade", layout="wide", page_icon="🔬")

# --- CONEXÃO COM O BANCO DE DADOS ---
def conectar():
    return sqlite3.connect("controle_qualidade_forn.db")

# Inicialização do Banco de Dados
conn = conectar()
cursor = conn.cursor()

# Tabela de Inspeção de Lotes
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

# Tabela de Usuários Autorizados
cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        usuario TEXT PRIMARY KEY,
        senha TEXT,
        perfil TEXT
    )
""")

# Garante o Administrador padrão do sistema
try:
    cursor.execute("INSERT OR IGNORE INTO usuarios (usuario, senha, perfil) VALUES ('admin', 'Master@2026', 'Administrador')")
except sqlite3.Error:
    pass

conn.commit()
conn.close()


# --- CONTROLE DE SESSÃO (ESTADO DO STREAMLIT) ---
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False
if "usuario_logado" not in st.session_state:
    st.session_state["usuario_logado"] = ""
if "perfil_usuario" not in st.session_state:
    st.session_state["perfil_usuario"] = ""


# --- TELA DE ACESSO (LOGIN / AUTO-CADASTRO) ---
if not st.session_state["autenticado"]:
    st.markdown("<h1 style='text-align: center;'>🔬 NEXTGEN | CONTROLE DE QUALIDADE</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #64748B;'>Inspeção de Lotes, Validades e Laudos Laboratoriais</p>", unsafe_allow_html=True)
    st.markdown("---")

    aba_login, aba_novo_cadastro = st.tabs(["🔑 Acessar Sistema", "🆕 Criar Minha Conta (Auto-Cadastro)"])

    # 1. Fluxo de Login
    with aba_login:
        col1, col2, col3 = st.columns([1, 1.2, 1])
        with col2:
            st.markdown("### Entrar no Sistema")
            u_input = st.text_input("Usuário / Analista:", key="login_user").strip().lower()
            p_input = st.text_input("Senha:", type="password", key="login_pass").strip()
            
            if st.button("Acessar Módulo CQ", use_container_width=True):
                if u_input and p_input:
                    conn = conectar()
                    cursor = conn.cursor()
                    cursor.execute("SELECT senha, perfil FROM usuarios WHERE usuario = ?", (u_input,))
                    resultado = cursor.fetchone()
                    conn.close()
                    
                    # Extração correta do valor da tupla do SQLite
                    if resultado and resultado[0] == p_input:
                        st.session_state["autenticado"] = True
                        st.session_state["usuario_logado"] = u_input
                        st.session_state["perfil_usuario"] = resultado[1]
                        st.rerun()
                    else:
                        st.error("Usuário ou senha incorretos.")
                else:
                    st.warning("Preencha todos os campos para entrar.")
                    
    # 2. Fluxo de Auto-Cadastro de Novos Usuários
    with aba_novo_cadastro:
        col1, col2, col3 = st.columns([1, 1.2, 1])
        with col2:
            st.markdown("### Criar Novo Usuário")
            novo_u = st.text_input("Escolha seu Usuário:", key="reg_user").strip().lower()
            novo_p = st.text_input("Crie sua Senha:", type="password", key="reg_pass").strip()
            conf_p = st.text_input("Confirme sua Senha:", type="password", key="reg_conf").strip()
            
            novo_perfil = st.selectbox(
                "Selecione sua Função Operacional:", 
                ["Recepção (Cadastros)", "Laboratório (Análises)", "Consulta (Relatórios)", "Administrador"]
            )
            
            if st.button("Gravar e Ativar Conta", use_container_width=True):
                if not novo_u or not novo_p or not conf_p:
                    st.warning("Todos os campos de cadastro devem ser preenchidos.")
                elif novo_p != conf_p:
                    st.error("As senhas informadas não coincidem.")
                elif novo_u == "admin":
                    st.error("O nome de usuário 'admin' é exclusivo do sistema.")
                else:
                    conn = conectar()
                    cursor = conn.cursor()
                    try:
                        cursor.execute("INSERT INTO usuarios (usuario, senha, perfil) VALUES (?, ?, ?)", 
                                       (novo_u, novo_p, novo_perfil))
                        conn.commit()
                        st.success(f"Conta `{novo_u}` criada como **{novo_perfil}**! Vá para a aba ao lado e faça seu login.")
                    except sqlite3.IntegrityError:
                        st.error("Este nome de usuário já está sendo utilizado por outro analista.")
                    finally:
                        conn.close()
    st.stop()


# --- BARRA LATERAL (PAINEL DO USUÁRIO LOGADO) ---
with st.sidebar:
    st.markdown("### 🧪 CONTA ATIVA")
    st.write(f"**Usuário:** `{st.session_state['usuario_logado']}`")
    st.write(f"**Acesso:** `{st.session_state['perfil_usuario']}`")
    st.markdown("---")
    if st.button("Sair do Sistema", use_container_width=True):
        st.session_state["autenticado"] = False
        st.session_state["usuario_logado"] = ""
        st.session_state["perfil_usuario"] = ""
        st.rerun()


# --- TELA PRINCIPAL - CONTROLE DE ABAS AUTORIZADAS ---
st.title("🔬 Módulo Integrado de Controle de Qualidade")

perfil = st.session_state["perfil_usuario"]
abas_autorizadas = []

# Mapeamento estrito de permissões por perfil
if perfil in ["Administrador", "Recepção (Cadastros)"]:
    abas_autorizadas.append("📥 1. RECEPÇÃO / CADASTRAR LOTE")
if perfil in ["Administrador", "Laboratório (Análises)"]:
    abas_autorizadas.append("🧫 2. PAINEL DO LABORATÓRIO")
if perfil in ["Administrador", "Recepção (Cadastros)", "Laboratório (Análises)", "Consulta (Relatórios)"]:
    abas_autorizadas.append("📋 3. RELATÓRIO GERAL DE LAUDOS")
if perfil == "Administrador":
    abas_autorizadas.append("⚙️ GERENCIAR CONTAS")

# SOLUÇÃO DO BUG: Se a lista estiver vazia por algum problema de registro, adiciona uma aba de aviso padrão
if not abas_autorizadas:
    abas_autorizadas.append("⚠️ SEM PERMISSÃO")

# Renderização segura das abas mapeadas em dicionário
dicionario_abas = {nome: objeto for nome, objeto in zip(abas_autorizadas, st.tabs(abas_autorizadas))}


# --- TRATAMENTO SE O USUÁRIO ESTIVER SEM ABAS ---
if "⚠️ SEM PERMISSÃO" in dicionario_abas:
    with dicionario_abas["⚠️ SEM PERMISSÃO"]:
        st.error("Seu perfil atual não possui permissões associadas. Entre em contato com o Administrador.")

# --- TELA 1: RECEPÇÃO / CADASTRAR LOTE ---
if "📥 1. RECEPÇÃO / CADASTRAR LOTE" in dicionario_abas:
    with dicionario_abas["📥 1. RECEPÇÃO / CADASTRAR LOTE"]:
        st.subheader("Entrada de Matéria-Prima / Produto para Inspeção")
        
        if "sucesso_cadastro" in st.session_state:
            st.success(st.session_state["sucesso_cadastro"])
            del st.session_state["sucesso_cadastro"]

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
                    st.session_state["sucesso_cadastro"] = f"Lote {q_lot.strip()} registrado com sucesso!"
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("Erro: Este número de Lote já consta no banco de dados!")
                finally:
                    conn.close()
            else:
                st.warning("Preencha todos os campos obrigatórios para registrar o lote.")


# --- TELA 2: PAINEL DO LABORATÓRIO ---
if "🧫 2. PAINEL DO LABORATÓRIO" in dicionario_abas:
    with dicionario_abas["🧫 2. PAINEL DO LABORATÓRIO"]:
        st.subheader("Análise e Parecer Técnico Laboratorial")
        
        conn = conectar()
        df_analise = pd.read_sql_query("SELECT id_laudo, lote, descricao, fornecedor, status FROM inspeccao WHERE status = 'Em Análise'", conn)
        conn.close()
        
        if df_analise.empty:
            st.info("Nenhum lote pendente de análise laboratorial no momento.")
        else:
            st.dataframe(df_analise, use_container_width=True, hide_index=True)

