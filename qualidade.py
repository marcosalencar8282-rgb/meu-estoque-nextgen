import sqlite3
from datetime import datetime
import streamlit as st
import pandas as pd

# Configuração estável e leve da página
st.set_page_config(page_title="CQ Lab", layout="wide", page_icon="🔬")

# --- CONEXÃO DIRETA COM O BANCO DE DADOS ---
conn = sqlite3.connect("sistema_laboratorio_simples.db")
cursor = conn.cursor()

# Criação das tabelas necessárias
cursor.execute("""
    CREATE TABLE IF NOT EXISTS laudos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data_cadastro TEXT,
        insumo TEXT,
        lote TEXT UNIQUE,
        status TEXT DEFAULT 'Em Quarentena',
        analista TEXT DEFAULT 'Pendente',
        parametros TEXT DEFAULT '-'
    )
""")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        usuario TEXT PRIMARY KEY,
        senha TEXT,
        funcao TEXT
    )
""")

# Garante o usuário administrador padrão no sistema
cursor.execute("SELECT COUNT(*) FROM usuarios WHERE usuario = 'admin'")
if cursor.fetchone()[0] == 0:
    cursor.execute("INSERT INTO usuarios (usuario, senha, funcao) VALUES ('admin', 'admin123', 'Administrador')")
    conn.commit()

# --- ESTRUTURA DE LOGIN SIMPLES ---
if "logado" not in st.session_state:
    st.session_state["logado"] = False
if "user" not in st.session_state:
    st.session_state["user"] = ""

if not st.session_state["logado"]:
    st.title("🔬 LOGIN | CONTROLE DE QUALIDADE")
    u = st.text_input("Usuário:").strip().lower()
    p = st.text_input("Senha:", type="password").strip()
    
    if st.button("Entrar no Sistema", use_container_width=True):
        cursor.execute("SELECT senha FROM usuarios WHERE usuario = ?", (u,))
        dados = cursor.fetchone()
        if dados and dados[0] == p:
            st.session_state["logado"] = True
            st.session_state["user"] = u
            st.rerun()
        else:
            st.error("Usuário ou senha incorretos.")
    st.stop()

# --- PAINEL PRINCIPAL (LOGADO) ---
st.title("🔬 SISTEMA DE QUALIDADE E LAUDOS")
st.write(f"👤 Operador ativo: **{st.session_state['user'].upper()}**")

if st.button("🚪 Sair do Sistema"):
    st.session_state["logado"] = False
    st.rerun()

st.markdown("---")

# --- BARRA LATERAL PARA MUDAR DE TELA ---
tela = st.sidebar.radio("Navegação do Sistema:", ["📥 1. Entrada de Insumo", "🧫 2. Emitir Laudo Técnico", "📋 3. Histórico de Laudos", "⚙️ 4. Gerenciar Usuários"])

st.markdown("---")

# --- TELA 1: ENTRADA DE INSUMO ---
if tela == "📥 1. Entrada de Insumo":
    st.subheader("📥 Registrar Entrada de Material (Quarentena)")
    
    c1, c2 = st.columns(2)
    with c1:
        nome_insumo = st.text_input("Nome do Insumo / Material:")
    with c2:
        num_lote = st.text_input("Número do Lote Único:")
        
    if st.button("Enviar para Inspeção", use_container_width=True):
        if nome_insumo and num_lote:
            cursor.execute("SELECT COUNT(*) FROM laudos WHERE lote = ?", (num_lote,))
            if cursor.fetchone()[0] == 0:
                data_hoje = datetime.now().strftime("%d/%m/%Y %H:%M")
                cursor.execute("INSERT INTO laudos (data_cadastro, insumo, lote) VALUES (?, ?, ?)", (data_hoje, nome_insumo, num_lote))
                conn.commit()
                st.success(f"Material {nome_insumo} (Lote {num_lote}) registrado com sucesso!")
            else:
                st.error("Erro: Este número de lote já existe no sistema.")
        else:
            st.warning("Preencha todos os campos do formulário.")

# --- TELA 2: EMITIR LAUDO TÉCNICO ---
elif tela == "🧫 2. Emitir Laudo Técnico":
    st.subheader("🧫 Avaliação de Parâmetros e Liberação de Laudo")
    
    # Busca apenas os lotes que ainda estão em quarentena
    cursor.execute("SELECT lote FROM laudos WHERE status = 'Em Quarentena'")
    lotes_pendentes = [item[0] for item in cursor.fetchall()]
    
    if not lotes_pendentes:
        st.info("Nenhum lote aguardando análise laboratorial no momento.")
    else:
        lote_selecionado = st.selectbox("Selecione o Lote para Analisar:", lotes_pendentes)
        resultado = st.selectbox("Veredito do Controle de Qualidade:", ["Aprovado", "Reprovado"])
        justificativa = st.text_area("Descreva os Parâmetros Analisados (Aprovação/Reprovação):", placeholder="Digite as especificações, ensaios ou desvios encontrados...")
        
        if st.button("Homologar Laudo Definitivo", use_container_width=True):
            if justificativa.strip() != "":
                cursor.execute("UPDATE laudos SET status = ?, analista = ?, parametros = ? WHERE lote = ?", (resultado, st.session_state["user"], justificativa, lote_selecionado))
                conn.commit()
                st.success(f"O lote {lote_selecionado} foi classificado como {resultado}!")
                st.rerun()
            else:
                st.error("Erro obrigatório: Você precisa preencher os parâmetros analisados para emitir o laudo.")

# --- TELA 3: HISTÓRICO DE LAUDOS ---
elif tela == "📋 3. Histórico de Laudos":
    st.subheader("📋 Arquivo de Laudos Registrados")
    
    df = pd.read_sql_query("SELECT id as ID, data_cadastro as 'Data Entrada', insumo as 'Insumo/Material', lote as 'Lote', status as 'Status CQ', analista as 'Analista Responsável', parametros as 'Parâmetros Analisados' FROM laudos ORDER BY id DESC", conn)
    
    if df.empty:
        st.info("Nenhum registro encontrado no banco de dados.")
    else:
        st.dataframe(df, use_container_width=True, hide_index=True)

# --- TELA 4: GERENCIAR USUÁRIOS ---
elif tela == "⚙️ 4. Gerenciar Usuários":
    st.subheader("⚙️ Gerenciador de Usuários do Laboratório")
    
    g1, g2 = st.columns(2)
    with g1:
        st.markdown("**Cadastrar Novo Funcionário:**")
        novo_u = st.text_input("Nome de Usuário:").strip().lower()
        novo_p = st.text_input("Senha Provisória:", type="password").strip()
        nova_f = st.selectbox("Função:", ["Técnico", "Analista", "Supervisor"])
        
        if st.button("Salvar Usuário"):
            if novo_u and novo_p:
                cursor.execute("SELECT COUNT(*) FROM usuarios WHERE usuario = ?", (novo_u,))
                if cursor.fetchone()[0] == 0:
                    cursor.execute("INSERT INTO usuarios (usuario, senate, funcao) VALUES (?, ?, ?)" if False else "INSERT INTO usuarios (usuario, senha, funcao) VALUES (?, ?, ?)", (novo_u, novo_p, nova_f))
                    conn.commit()
                    st.success(f"Usuário {novo_u} cadastrado com sucesso!")
                else:
                    st.error("Este nome de usuário já existe.")
            else:
                st.warning("Preencha usuário e senha.")
                
    with g2:
        st.markdown("**Usuários Cadastrados:**")
        df_users = pd.read_sql_query("SELECT usuario as 'Usuário', funcao as 'Função' FROM usuarios WHERE usuario != 'admin'", conn)
        
        if df_users.empty:
            st.caption("Nenhum usuário secundário cadastrado.")
        else:
            st.dataframe(df_users, use_container_width=True, hide_index=True)
            user_remover = st.selectbox("Selecione para remover do sistema:", df_users["Usuário"].tolist())
            if st.button("❌ Deletar Conta"):
                cursor.execute("DELETE FROM usuarios WHERE usuario = ?", (user_remover,))
                conn.commit()
                st.success(f"Conta de {user_remover} removida.")
                st.rerun()

