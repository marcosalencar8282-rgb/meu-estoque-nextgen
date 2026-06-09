import sqlite3
from datetime import datetime
import streamlit as st
import pandas as pd

# Configuração da página profissional, limpa e moderna
st.set_page_config(page_title="NextGen | Quality Control", layout="wide", page_icon="🔬")

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

# --- TELA DE ACESSO (LOGIN / CADASTRO) ---
if not st.session_state["autenticado"]:
    st.title("🔬 NEXTGEN | CQ")
    st.caption("Sistema Integrado de Gestão e Controle de Qualidade de Insumos")
    
    op_acesso = st.radio("Acesso ao Sistema", ["🔑 Fazer Login", "🆕 Criar Nova Conta"], horizontal=True)
    st.markdown("<br>", unsafe_html=True)
    
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

# --- HEADER PREMIUM ---
c_info, c_logout = st.columns([3, 1])
with c_info:
    st.title("🔬 NEXTGEN | Controle de Qualidade")
    st.markdown(f"👤 Analista ativo: **{st.session_state['usuario_logado'].upper()}** &nbsp;|&nbsp; Perfil de Acesso: `{st.session_state['perfil_usuario'].upper()}`")
with c_logout:
    st.markdown("<br>", unsafe_html=True)
    if st.button("🚪 Sair do Sistema", use_container_width=True):
        st.session_state.clear()
        st.rerun()

st.markdown("---")

# --- CORES E METRICAS DE SUPORTE NO TOPO ---
conn = conectar()
total_lotes = pd.read_sql_query("SELECT COUNT(*) as qtd FROM inspeccao", conn)["qtd"]
analise_lotes = pd.read_sql_query("SELECT COUNT(*) as qtd FROM inspeccao WHERE status = 'Em Análise'", conn)["qtd"]
aprovados_lotes = pd.read_sql_query("SELECT COUNT(*) as qtd FROM inspeccao WHERE status = 'Aprovado'", conn)["qtd"]
reprovados_lotes = pd.read_sql_query("SELECT COUNT(*) as qtd FROM inspeccao WHERE status = 'Reprovado'", conn)["qtd"]
conn.close()

m1, m2, m3, m4 = st.columns(4)
m1.metric("Total de Lotes Recebidos", int(total_lotes.iloc[0]))
m2.metric("Aguardando Análise", int(analise_lotes.iloc[0]))
m3.metric("Lotes Aprovados", int(aprovados_lotes.iloc[0]))
m4.metric("Lotes Reprovados", int(reprovados_lotes.iloc[0]))

st.markdown("<br>", unsafe_html=True)

# --- NAVEGAÇÃO MODERNA POR ABAS (TABS) ---
perf = st.session_state["perfil_usuario"]

# Criando abas dinâmicas conforme a permissão do usuário logado
abas_disponiveis = []
if perf in ["admin", "cadastro"]: abas_disponiveis.append("📥 Entrada de Lote")
if perf in ["admin", "laboratorio"]: abas_disponiveis.append("🧫 Painel Laboratório")
abas_disponiveis.append("📋 Histórico & Laudos")
if perf == "admin": abas_disponiveis.append("⚙️ Gestão de Usuários")

abas = st.tabs(abas_disponiveis)

# Mapeamento do conteúdo de cada aba de acordo com as permissões reais
index_aba = 0

# 1. ABA DE CADASTRO DE LOTE
if perf in ["admin", "cadastro"]:
    with abas[index_aba]:
        st.markdown("### Registrar Entrada de Insumo")
        st.caption("Insira os dados do documento fiscal e lote físico do fabricante.")
        
        with st.form("form_cadastro", clear_on_submit=True):
            c_f1, c_f2 = st.columns(2)
            with c_f1:
                nf = st.text_input("Número da Nota Fiscal:")
                forn = st.text_input("Nome do Fornecedor:")
                cod = st.text_input("Código do Produto (SKU):")
                desc = st.text_input("Descrição Completa do Insumo:")
            with c_f2:
                lot = st.text_input("Número do Lote (Identificador Único):")
                fab = st.text_input("Data de Fabricação (Ex: DD/MM/AAAA):")
                val = st.text_input("Data de Validade (Ex: DD/MM/AAAA):")
            
            st.markdown("<br>", unsafe_html=True)
            if st.form_submit_button("Confirmar Recebimento e Enviar p/ CQ", use_container_width=True):
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
                        st.success(f"Sucesso! Lote '{lot}' registrado e integrado à fila do laboratório.")
                    except sqlite3.IntegrityError:
                        st.error("Erro crítico: Este número de lote já existe na base de dados.")
                    finally:
                        conn.close()
                else:
                    st.warning("Preencha todos os campos obrigatórios marcados para validação.")
    index_aba += 1

# 2. ABA DO PAINEL DO LABORATÓRIO
if perf in ["admin", "laboratorio"]:
    with abas[index_aba]:
        st.markdown("### Fila Técnico-Analítica")
        st.caption("Liberação ou reprovação de lotes retidos em quarentena técnica.")
        
        conn = conectar()
        df_pendentes = pd.read_sql_query("SELECT id_laudo, lote, descricao, fornecedor, status FROM inspeccao WHERE status = 'Em Análise'", conn)
        conn.close()
        
        if df_pendentes.empty:
            st.info("Parabéns! Fila limpa. Nenhum lote aguardando análise laboratorial.")
        else:
            st.dataframe(df_pendentes, use_container_width=True, hide_index=True)
            
            st.markdown("<br>", unsafe_html=True)
            st.markdown("**Registrar Parecer Técnico (Laudo)**")
            c_l1, c_l2 = st.columns(2)
            with c_l1:
                lote_sel = st.selectbox("Selecione o Lote Alvo:", df_pendentes["lote"].tolist())
            with c_l2:
                novo_status = st.selectbox("Veredito do Controle de Qualidade", ["Aprovado", "Reprovado"])
                
            if st.button("Emitir Laudo Definitivo", use_container_width=True):
                conn = conectar()
                cursor = conn.cursor()
                cursor.execute("UPDATE inspeccao SET status = ?, responsavel = ? WHERE lote = ?", (novo_status, st.session_state["usuario_logado"], lote_sel))
                conn.commit()
                conn.close()
                st.success(f"Laudo gravado! Status do lote {lote_sel} updated para {novo_status}.")
                st.rerun()
    index_aba += 1

# 3. ABA DO HISTÓRICO GERAL (VISUALIZAÇÃO DE LAUDOS)
with abas[index_aba]:
    st.markdown("### Registro Geral de Qualidade (RGL)")
    st.caption("Histórico imutável de rastreabilidade de todas as inspeções realizadas.")
    
    conn = conectar()
    df_geral = pd.read_sql_query("SELECT * FROM inspeccao ORDER BY id_laudo DESC", conn)
    conn.close()
    
    if df_geral.empty:
        st.info("Nenhum registro localizado na base do laboratório.")
    else:
