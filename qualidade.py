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
    conn = sqlite3.connect("controle_qualidade_forn.db")
    conn.row_factory = sqlite3.Row  # Configuração para ler colunas por nome
    return conn

# Inicialização Limpa das Tabelas
conn = conectar()
cursor = conn.cursor()

# 1. Tabela de Inspeção de Produtos
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

# 2. Tabela de Usuários Cadastrados
cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        usuario TEXT PRIMARY KEY,
        senha TEXT,
        perfil TEXT
    )
""")

# Usuários padrão do sistema
usuarios_padrao = [
    ("admin", "Master@2026", "admin"),
    ("marcos", "931481", "cadastro"),
    ("laboratorio", "LabCQ2026", "laboratorio"),
    ("visitante", "123", "visualizar")
]

for usr, psw, prf in usuarios_padrao:
    try:
        cursor.execute("INSERT INTO usuarios (usuario, senha, perfil) VALUES (?, ?, ?)", (usr, psw, prf))
    except sqlite3.IntegrityError:
        pass

conn.commit()
conn.close()


# --- INTERFACE DE BLOQUEIO (LOGIN / CADASTRO) ---
if not st.session_state["autenticado"]:
    st.markdown("<h1 style='text-align: center;'>🔬 NEXTGEN | CONTROLE DE QUALIDADE</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #64748B;'>Gerenciamento de Acessos e Laudos Técnicos</p>", unsafe_allow_html=True)

    aba_entrar, aba_cadastrar = st.tabs(["🔑 Acessar Painel", "🆕 Criar Novo Usuário"])

    # FORMULÁRIO DE LOGIN
    with aba_entrar:
        col_l1, col_l2, col_l3 = st.columns([1, 1.2, 1])
        with col_l2:
            campo_usuario = st.text_input("Usuário / Analista:", key="txt_usr").strip().lower()
            campo_senha = st.text_input("Senha de Acesso:", type="password", key="txt_pwd").strip()
            
            if st.button("Autenticar no Sistema", use_container_width=True):
                conn = conectar()
                cursor = conn.cursor()
                cursor.execute("SELECT senha, perfil FROM usuarios WHERE usuario = ?", (campo_usuario,))
                dados_usuario = cursor.fetchone()
                conn.close()
                
                if dados_usuario:
                    senha_banco = dados_usuario.get("senha")
                    perfil_banco = dados_usuario.get("perfil")
                    
                    if senha_banco == campo_senha:
                        st.session_state["autenticado"] = True
                        st.session_state["usuario_logado"] = campo_usuario
                        st.session_state["perfil_usuario"] = str(perfil_banco)
                        st.rerun()
                    else:
                        st.error("Credenciais incorretas ou usuário inexistente.")
                else:
                    st.error("Credenciais incorretas ou usuário inexistente.")

    # FORMULÁRIO DE AUTO-CADASTRO
    with aba_cadastrar:
        col_c1, col_c2, col_c3 = st.columns([1, 1.2, 1])
        with col_c2:
            st.markdown("### Solicitar Novo Acesso")
            reg_usuario = st.text_input("Defina o Nome de Usuário:", key="new_usr").strip().lower()
            reg_senha = st.text_input("Defina a Senha:", type="password", key="new_pwd").strip()
            reg_confirma = st.text_input("Confirme sua Senha:", type="password", key="new_pwd_conf").strip()
            
            reg_perfil = st.selectbox(
                "Nível de Autorização de Tela:",
                options=["cadastro", "laboratorio", "visualizar"],
                help="Define a qual departamento ou aba este usuário terá acesso exclusivo."
            )
            
            if st.button("Salvar e Ativar Conta", use_container_width=True):
                if not reg_usuario or not reg_senha:
                    st.warning("Preencha obrigatoriamente usuário e senha.")
                elif reg_senha != reg_confirma:
                    st.error("As senhas informadas estão divergentes.")
                else:
                    conn = conectar()
                    cursor = conn.cursor()
                    try:
                        cursor.execute("INSERT INTO usuarios (usuario, senha, perfil) VALUES (?, ?, ?)", 
                                       (reg_usuario, reg_senha, reg_perfil))
                        conn.commit()
                        st.success(f"Conta `{reg_usuario}` criada! Use a aba de Acesso ao lado para logar.")
                    except sqlite3.IntegrityError:
                        st.error("Este nome de usuário já está sendo utilizado por outro colaborador.")
                    finally:
                        conn.close()
    st.stop()


# --- AMBIENTE LOGADO (SISTEMA NEXTGEN) ---
with st.sidebar:
    st.markdown("### 🧪 PERFIL CONECTADO")
    st.write(f"Analista: `{st.session_state['usuario_logado']}`")
    st.write(f"Permissão: `{st.session_state['perfil_usuario'].upper()}`")
    st.markdown("---")
    if st.button("Desconectar e Sair", use_container_width=True):
        st.session_state["autenticado"] = False
        st.session_state["usuario_logado"] = ""
        st.session_state["perfil_usuario"] = ""
        st.rerun()

st.title("🔬 NextGen | Controle de Qualidade")

# --- REGRAS DE AUTORIZAÇÃO DE TELA POR PERFIL ---
meu_perfil = st.session_state["perfil_usuario"]

abas_permitidas = []
if meu_perfil in ["admin", "cadastro"]:
    abas_permitidas.append("📥 1. RECEPÇÃO / CADASTRAR LOTE")
if meu_perfil in ["admin", "laboratorio"]:
    abas_permitidas.append("🧫 2. PAINEL DO LABORATÓRIO")
if meu_perfil in ["admin", "cadastro", "laboratorio", "visualizar"]:
    abas_permitidas.append("📋 3. RELATÓRIO GERAL DE LAUDOS")

abas_sistema = st.tabs(abas_permitidas)
ponteiro_aba = 0


# --- TELA 1: RECEPÇÃO (CADASTRAR LOTE) ---
if "📥 1. RECEPÇÃO / CADASTRAR LOTE" in abas_permitidas:
    with abas_sistema[ponteiro_aba]:
        ponteiro_aba += 1
        st.subheader("Entrada de Produto para Inspeção")
        
        with st.form("form_cadastro_lote", clear_on_submit=True):
            f_nf = st.text_input("Número da Nota Fiscal (NF-e):")
            f_forn = st.text_input("Nome do Fornecedor / Fabricante:")
            f_cod = st.text_input("Código do Produto (SKU/EAN):")
            f_desc = st.text_input("Descrição / Nome do Produto:")
            f_lote = st.text_input("Número do Lote do Fabricante:")
            
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                f_fab = st.text_input("Data de Fabricação (Ex: 01/06/2026):")
            with col_d2:
                f_val = st.text_input("Data de Validade (Ex: 01/12/2026):")
                
            botao_salvar_lote = st.form_submit_button("Dar Entrada para Análise", use_container_width=True)
            
        if botao_salvar_lote:
            if f_nf and f_forn and f_cod and f_desc and f_lote:
                conn = conectar()
                cursor = conn.cursor()
                try:
                    data_hora_atual = datetime.now().strftime("%d/%m/%Y %H:%M")
                    cursor.execute("""
                        INSERT INTO inspeccao (data_chegada, nota_fiscal, fornecedor, codigo, descricao, lote, fabricacao, validade) 
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (data_hora_atual, f_nf.strip(), f_forn.strip(), f_cod.strip(), f_desc.strip(), f_lote.strip(), f_fab.strip(), f_val.strip()))
                    conn.commit()
                    st.session_state["msg_sucesso"] = f"Lote {f_lote.strip()} enviado para a fila de análise!"
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("Atenção: Este número de Lote já encontra-se cadastrado no sistema!")
                finally:
                    conn.close()
            else:
                st.warning("Preencha os campos obrigatórios: Nota Fiscal, Fornecedor, Código, Descrição e Lote.")

    if "msg_sucesso" in st.session_state:
        st.success(st.session_state["msg_sucesso"])
        del st.session_state["msg_sucesso"]


# --- TELA 2: PAINEL DO LABORATÓRIO (APROVAR E REPROVAR) ---
if "🧫 2. PAINEL DO LABORATÓRIO" in abas_permitidas:
    with abas_sistema[ponteiro_aba]:
        ponteiro_aba += 1
        st.subheader("Painel de Julgamento Laboratorial")
        
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT lote, descricao FROM inspeccao WHERE status = 'Em Análise'")
        lotes_esperando = cursor.fetchall()
        conn.close()
        
        if lotes_esperando:
            lista_selecao = []
            mapeamento_lotes = {}
            
            for item in lotes_esperando:
                lote_id = item.get("lote")
                desc_prod = item.get("descricao")
                texto_exibicao = f"Lote: {lote_id} | Produto: {desc_prod}"
                lista_selecao.append(texto_exibicao)
                mapeamento_lotes[texto_exibicao] = lote_id
                
            escolha_lote_txt = st.selectbox("Selecione o Item Pendente para Emitir Parecer:", lista_selecao)
            lote_alvo = mapeamento_lotes.get(escolha_lote_txt)
