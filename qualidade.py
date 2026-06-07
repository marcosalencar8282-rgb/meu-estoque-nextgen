import sqlite3
from datetime import datetime
import streamlit as st
import pandas as pd

# Configuração da página profissional
st.set_page_config(page_title="NextGen | Controle de Qualidade", layout="wide", page_icon="🔬")

# --- CONEXÃO COM O BANCO DE DADOS ---
def conectar():
    return sqlite3.connect("controle_qualidade_forn.db")

# Inicialização das Tabelas no SQLite (Garante o salvamento permanente)
conn = conectar()
cursor = conn.cursor()

# Tabela de Inspeção (Estrutura original preservada)
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

# Tabela de Usuários
cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        usuario TEXT PRIMARY KEY,
        senha TEXT,
        perfil TEXT
    )
""")

# Garante o usuário Administrador padrão
try:
    cursor.execute("INSERT OR IGNORE INTO usuarios (usuario, senha, perfil) VALUES ('admin', 'Master@2026', 'admin')")
except sqlite3.Error:
    pass

conn.commit()
conn.close()


# --- CONTROLE DE SESSÃO / LOGIN ---
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False
if "usuario_logado" not in st.session_state:
    st.session_state["usuario_logado"] = ""
if "perfil_usuario" not in st.session_state:
    st.session_state["perfil_usuario"] = ""


# TELA DE ACESSO (LOGIN / CRIAÇÃO DE CONTA)
if not st.session_state["autenticado"]:
    st.markdown("<h1 style='text-align: center;'>🔬 NEXTGEN | CONTROLE DE QUALIDADE</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #64748B;'>Inspeção de Lotes, Validades e Laudos Laboratoriais</p>", unsafe_allow_html=True)

    aba_login, aba_novo_cadastro = st.tabs(["🔑 Acessar Sistema", "🆕 Criar Minha Conta"])

    with aba_login:
        col_l1, col_l2, col_l3 = st.columns([1, 1.2, 1])
        with col_l2:
            u_input = st.text_input("Usuário / Analista:", key="login_user").strip().lower()
            p_input = st.text_input("Senha:", type="password", key="login_pass").strip()
            
            if st.button("Acessar Módulo CQ", use_container_width=True):
                conn = conectar()
                cursor = conn.cursor()
                cursor.execute("SELECT senha, perfil FROM usuarios WHERE usuario = ?", (u_input,))
                resultado = cursor.fetchone()
                conn.close()
                
                if resultado and resultado[0] == p_input:
                    st.session_state["autenticado"] = True
                    st.session_state["usuario_logado"] = u_input
                    st.session_state["perfil_usuario"] = resultado[1]
                    st.rerun()
                else:
                    st.error("Usuário ou senha incorretos.")
                    
    with aba_novo_cadastro:
        col_c1, col_c2, col_c3 = st.columns([1, 1.2, 1])
        with col_c2:
            st.markdown("### Registrar Novo Analista")
            novo_u = st.text_input("Escolha seu Usuário de Acesso:", key="reg_user").strip().lower()
            novo_p = st.text_input("Crie sua Senha:", type="password", key="reg_pass").strip()
            conf_p = st.text_input("Confirme sua Senha:", type="password", key="reg_conf").strip()
            
            novo_perfil = st.selectbox(
                "Selecione seu Perfil Operacional:", 
                ["cadastro", "laboratorio", "visualizar", "admin"]
            )
            
            if st.button("Cadastrar e Salvar Senha", use_container_width=True):
                if not novo_u or not novo_p:
                    st.warning("Todos os campos devem ser preenchidos.")
                elif novo_p != conf_p:
                    st.error("As senhas informadas não são iguais.")
                elif novo_u == "admin":
                    st.error("O usuário 'admin' é restrito do sistema.")
                else:
                    conn = conectar()
                    cursor = conn.cursor()
                    try:
                        cursor.execute("INSERT INTO usuarios (usuario, senha, perfil) VALUES (?, ?, ?)", 
                                       (novo_u, novo_p, novo_perfil))
                        conn.commit()
                        st.success(f"Usuário `{novo_u}` registrado com sucesso! Use a aba ao lado para logar.")
                    except sqlite3.IntegrityError:
                        st.error("Este nome de usuário já está registrado por outro funcionário.")
                    finally:
                        conn.close()
    st.stop()


# --- BARRA LATERAL (CONTROLE DE MENUS) ---
with st.sidebar:
    st.markdown("### 🧪 ANALISTA LOGADO")
    st.write(f"**Usuário:** `{st.session_state['usuario_logado']}`")
    st.write(f"**Perfil:** `{(st.session_state['perfil_usuario']).upper()}`")
    st.markdown("---")
    
    perfil = st.session_state["perfil_usuario"]
    menus_disponiveis = []
    
    if perfil in ["admin", "cadastro"]:
        menus_disponiveis.append("📥 1. Recepção / Cadastrar Lote")
    if perfil in ["admin", "laboratorio"]:
        menus_disponiveis.append("🧫 2. Painel do Laboratório")
    if perfil in ["admin", "cadastro", "laboratorio", "visualizar"]:
        menus_disponiveis.append("📋 3. Relatório Geral de Laudos")
        
    menu_selecionado = st.radio("Selecione a Tela de Trabalho:", menus_disponiveis)
    
    st.markdown("---")
    if st.button("Sair do Sistema", use_container_width=True):
        st.session_state["autenticado"] = False
        st.session_state["usuario_logado"] = ""
        st.session_state["perfil_usuario"] = ""
        st.rerun()


# --- TELA 1: RECEPÇÃO ---
if menu_selecionado == "📥 1. Recepção / Cadastrar Lote":
    st.subheader("Entrada de Produto para Inspeção")
    
    if "sucesso_cadastro" in st.session_state:
        st.success(st.session_state["sucesso_cadastro"])
        del st.session_state["sucesso_cadastro"]

    with st.form("form_cadastro", clear_on_submit=True):
        q_nf = st.text_input("Número da Nota Fiscal (NF-e):")
        q_for = st.text_input("Nome do Fornecedor / Fabricante:")
        q_cod = st.text_input("Código do Produto (SKU/EAN):")
        q_des = st.text_input("Descrição / Nome do Produto:")
        q_lot = st.text_input("Número do Lote do Fabricante:")
        q_fab = st.text_input("Data de Fabricação (Ex: 01/06/2026):")
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
                st.warning("Preencha todos os campos obrigatórios.")


# --- TELA 2: PAINEL DO LABORATÓRIO ---
elif menu_selecionado == "🧫 2. Painel do Laboratório":
    st.subheader("Análise e Parecer Técnico de Lotes")
    
    if "ultimo_laudo_gerado" in st.session_state:
        st.markdown("### 📄 LAUDO EMITIDO AGORA (SALVO NO HISTÓRICO)")
        st.dataframe(st.session_state["ultimo_laudo_gerado"], use_container_width=True, hide_index=True)
        st.markdown("---")
        if st.button("Fazer Nova Análise"):
            del st.session_state["ultimo_laudo_gerado"]
            st.rerun()
    
    conn = conectar()
    df_analise = pd.read_sql_query("SELECT id_laudo, lote, descricao, fornecedor, status FROM inspeccao WHERE status = 'Em Análise'", conn)
    conn.close()
    
    if df_analise.empty:
        st.info("Não há nenhum lote pendente de análise laboratorial no momento.")
    else:
        st.markdown("#### Lotes Aguardando Parecer Técnico")
        st.dataframe(df_analise, use_container_width=True, hide_index=True)
        
        st.markdown("### Atualizar Status do Lote")
        with st.form("form_laboratorio"):
            lote_selecionado = st.selectbox("Selecione o Lote para dar o Parecer:", df_analise["lote"].tolist())
            novo_status = st.selectbox("Parecer do Laboratório:", ["Aprovado", "Reprovado"])
            concluir_analise = st.form_submit_button("Gravar Decisão no Sistema", use_container_width=True)
            
            if concluir_analise:
                conn = conectar()
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE inspeccao 
                    SET status = ?, responsavel = ? 
                    WHERE lote = ?
                """, (novo_status, st.session_state["usuario_logado"], lote_selecionado))
                conn.commit()
                
                df_resultado = pd.read_sql_query("SELECT * FROM inspeccao WHERE lote = ?", conn, params=(lote_selecionado,))
                conn.close()
