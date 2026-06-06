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

# --- CONEXÃO COM O BANCO DE DADOS ---
def conectar():
    return sqlite3.connect("controle_qualidade_forn.db")

# Inicialização das Tabelas no SQLite
conn = conectar()
cursor = conn.cursor()

# Tabela de Inspeção (Mantida idêntica à sua estrutura original)
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

# Tabela para salvar os usuários que criarem suas próprias contas e senhas
cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        usuario TEXT PRIMARY KEY,
        senha TEXT,
        perfil TEXT
    )
""")

# Carga Automática: Insere seus usuários antigos caso a tabela seja nova
usuarios_iniciais = [
    ("admin", "Master@2026", "admin"),
    ("marcos", "931481", "cadastro"),
    ("laboratorio", "LabCQ2026", "laboratorio"),
    ("visitante", "123", "visualizar")
]

for usr, psw, prf in usuarios_iniciais:
    try:
        cursor.execute("INSERT INTO usuarios (usuario, senha, perfil) VALUES (?, ?, ?)", (usr, psw, prf))
    except sqlite3.IntegrityError:
        pass

conn.commit()
conn.close()

# TELA DE ACESSO (LOGIN / CRIAÇÃO DE SENHA PROPRIA)
if not st.session_state["autenticado"]:
    st.markdown("<h1 style='text-align: center;'>🔬 NEXTGEN | CONTROLE DE QUALIDADE</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #64748B;'>Inspeção de Lotes, Validades e Laudos Laboratoriais</p>", unsafe_allow_html=True)

    aba_login, aba_novo_cadastro = st.tabs(["🔑 Acessar Sistema", "🆕 Criar Minha Conta"])

    # --- SUB-TELA 1: LOGIN ---
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
                
                # Validação correta pegando os índices da linha do banco de dados
                if resultado and resultado[0] == p_input:
                    st.session_state["autenticado"] = True
                    st.session_state["usuario_logado"] = u_input
                    st.session_state["perfil_usuario"] = resultado[1]
                    st.rerun()
                else:
                    st.error("Usuário ou senha incorretos.")
                    
    # --- SUB-TELA 2: AUTO-CADASTRO (CRIAR PRÓPRIA SENHA) ---
    with aba_novo_cadastro:
        col_c1, col_c2, col_c3 = st.columns([1, 1.2, 1])
        with col_c2:
            st.markdown("### Registrar Novo Analista")
            novo_u = st.text_input("Escolha seu Usuário de Acesso:", key="reg_user").strip().lower()
            novo_p = st.text_input("Crie sua Senha:", type="password", key="reg_pass").strip()
            conf_p = st.text_input("Confirme sua Senha:", type="password", key="reg_conf").strip()
            
            novo_perfil = st.selectbox(
                "Selecione seu Perfil Operacional:", 
                ["cadastro", "laboratorio", "visualizar"]
            )
            
            if st.button("Cadastrar e Salvar Senha", use_container_width=True):
                if not novo_u or not novo_p:
                    st.warning("Todos os campos devem ser preenchidos.")
                elif novo_p != conf_p:
                    st.error("As senhas informadas não são iguais.")
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

# BARRA LATERAL (LOGOFF E INFORMAÇÕES)
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
            lista_opcoes = []
            mapeamento_lotes = {}
            
            for item in lotes_pendentes:
                lote_id = str(item[0])
                desc_prod = str(item[1])
                nf_num = str(item[2])
                forn_nome = str(item[3])
                
                texto_exibicao = f"Lote: {lote_id} | Prod: {desc_prod} | Forn: {forn_nome} | NF: {nf_num}"
                lista_opcoes.append(texto_exibicao)
                mapeamento_lotes[texto_exibicao] = lote_id
            
            lote_selecionado_txt = st.selectbox("Selecione o Lote Pendente para Emitir o Laudo:", lista_opcoes)
            lote_final = mapeamento_lotes[lote_selecionado_txt]
            
            st.markdown("---")
            st.markdown("#### ⚖️ Decisão do Laboratório:")
            
            col_btn1, col_btn2 = st.columns(2)
            
            with col_btn1:
                if st.button("🟢 APROVAR LOTE", use_container_width=True):
                    conn = conectar()
