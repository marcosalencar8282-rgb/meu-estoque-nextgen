import sqlite3
from datetime import datetime
import streamlit as st
import pandas as pd

# Configuração da página profissional, leve e estável
st.set_page_config(page_title="CQ Lab", layout="wide", page_icon="🔬")

# --- CONEXÃO BANCO DE DADOS ---
def conectar():
    return sqlite3.connect("sistema_laboratorio_simples.db")

conn = conectar()
cursor = conn.cursor()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS laudos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data_cadastro TEXT,
        nota_fiscal TEXT,
        fornecedor TEXT,
        insumo TEXT,
        lote TEXT UNIQUE,
        data_fabricacao TEXT,
        data_validade TEXT,
        quantidade REAL,
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
# Garante o administrador padrão caso o banco seja novo
cursor.execute("SELECT COUNT(*) FROM usuarios WHERE usuario = 'admin'")
if cursor.fetchone()[0] == 0:
    cursor.execute("INSERT INTO usuarios (usuario, senha, funcao) VALUES ('admin', 'admin123', 'Supervisor')")
    conn.commit()
conn.close()

# --- CONTROLE DE SESSÃO ---
if "logado" not in st.session_state:
    st.session_state["logado"] = False
if "user" not in st.session_state:
    st.session_state["user"] = ""
if "cargo" not in st.session_state:
    st.session_state["cargo"] = ""
if "tela_ativa" not in st.session_state:
    st.session_state["tela_ativa"] = "relatorio"

# --- TELA DE ACESSO (LOGIN) ---
if not st.session_state["logado"]:
    st.title("🔬 LOGIN | CONTROLE DE QUALIDADE")
    u = st.text_input("Usuário:").strip().lower()
    p = st.text_input("Senha:", type="password").strip()
    
    if st.button("Entrar no Sistema", use_container_width=True):
        if u and p:
            conn = conectar()
            cursor = conn.cursor()
            cursor.execute("SELECT senha, funcao FROM usuarios WHERE usuario = ?", (u,))
            dados = cursor.fetchone()
            conn.close()
            
            if dados and dados[0] == p:
                st.session_state["logado"] = True
                st.session_state["user"] = u
                st.session_state["cargo"] = str(dados[1]).strip()
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos.")
        else:
            st.warning("Preencha todos os campos.")
    st.stop()

# --- BARRA SUPERIOR DE INFORMAÇÕES E LOGOUT ---
c_info, c_logout = st.columns([3, 1])
with c_info:
    st.markdown(f"👤 Operador: **{st.session_state['user'].upper()}** | Cargo: **{st.session_state['cargo'].upper()}**")
with c_logout:
    if st.button("Sair do Sistema", use_container_width=True):
        st.session_state.clear()
        st.rerun()

st.markdown("---")

# --- GERENCIAMENTO DE MENUS POR BOTÕES (AUTORIZAÇÃO RÍGIDA) ---
cargo_atual = st.session_state["cargo"]
st.markdown("### 🗂️ Navegação do Sistema")

c1, c2, c3, c4 = st.columns(4)

with c1:
    if cargo_atual in ["Técnico", "Supervisor"]:
        if st.button("📥 1. Entrada de Insumo", use_container_width=True):
            st.session_state["tela_ativa"] = "cadastro"
            st.rerun()

with c2:
    if cargo_atual in ["Analista", "Supervisor"]:
        if st.button("🧫 2. Emitir Laudo Técnico", use_container_width=True):
            st.session_state["tela_ativa"] = "laboratorio"
            st.rerun()

with c3:
    if st.button("📋 3. Ver Relatório de Laudos", use_container_width=True):
        st.session_state["tela_ativa"] = "relatorio"
        st.rerun()

with c4:
    if cargo_atual == "Supervisor":
        if st.button("⚙️ 4. Gerenciar Usuários", use_container_width=True):
            st.session_state["tela_ativa"] = "gerenciar_usuarios"
            st.rerun()

st.markdown("---")

# --- TELA 1: ENTRADA DE INSUMO ---
if st.session_state["tela_ativa"] == "cadastro" and cargo_atual in ["Técnico", "Supervisor"]:
    st.subheader("📥 Registrar Entrada de Material (Quarentena)")
    
    nota_fiscal = st.text_input("Número da Nota Fiscal:")
    fornecedor = st.text_input("Nome do Fornecedor:")
    nome_insumo = st.text_input("Nome do Insumo / Material:")
    num_lote = st.text_input("Número do Lote Único:")
    qtd_insumo = st.number_input("Quantidade Recebida:", min_value=0.0, step=1.0, value=0.0)
    data_fab = st.text_input("Data de Fabricação (Ex: DD/MM/AAAA):")
    data_val = st.text_input("Data de Validade (Ex: DD/MM/AAAA):")
    
    if st.button("Confirmar Entrada", use_container_width=True):
        if nome_insumo and num_lote and nota_fiscal and fornecedor:
            conn = conectar()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM laudos WHERE lote = ?", (num_lote,))
            if cursor.fetchone()[0] == 0:
                data_hoje = datetime.now().strftime("%d/%m/%Y %H:%M")
                cursor.execute("""
                    INSERT INTO laudos (data_cadastro, nota_fiscal, fornecedor, insumo, lote, data_fabricacao, data_validade, quantidade) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (data_hoje, nota_fiscal, fornecedor, nome_insumo, num_lote, data_fab, data_val, qtd_insumo))
                conn.commit()
                conn.close()
                st.success(f"Material {nome_insumo} registrado em quarentena com sucesso!")
            else:
                conn.close()
                st.error("Erro: Este número de lote já existe no sistema.")
        else:
            st.warning("Preencha Nota Fiscal, Fornecedor, Nome do Insumo e Lote.")

# --- TELA 2: EMITIR LAUDO TÉCNICO ---
elif st.session_state["tela_ativa"] == "laboratorio" and cargo_atual in ["Analista", "Supervisor"]:
    st.subheader("🧫 Avaliação de Parâmetros e Liberação de Laudo")
    
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT lote FROM laudos WHERE status = 'Em Quarentena'")
    lotes_pendentes = [item[0] for item in cursor.fetchall()]
    conn.close()
    
    if not lotes_pendentes:
        st.info("Nenhum lote aguardando análise laboratorial no momento.")
    else:
        lote_selecionado = st.selectbox("Selecione o Lote para Analisar:", lotes_pendentes)
        resultado = st.selectbox("Veredito do Controle de Qualidade:", ["Aprovado", "Reprovado"])
        justificativa = st.text_area("Descreva os Parâmetros Analisados (Aprovação/Reprovação):")
        
        if st.button("Gravar Decisão do Laudo", use_container_width=True):
            if justificativa.strip() != "":
                conn = conectar()
                cursor = conn.cursor()
                cursor.execute("UPDATE laudos SET status = ?, analista = ?, parametros = ? WHERE lote = ?", (resultado, st.session_state["user"], justificativa, lote_selecionado))
                conn.commit()
                conn.close()
                st.success(f"O lote {lote_selecionado} foi classificado como {resultado}!")
                st.rerun()
            else:
                st.error("Erro obrigatório: Preencha os parâmetros analisados para emitir o laudo.")

# --- TELA 3: HISTÓRICO / RELATÓRIO GERAL ---
elif st.session_state["tela_ativa"] == "relatorio":
    st.subheader("📋 Histórico Completo de Laudos Emitidos")
    
    conn = conectar()
    df = pd.read_sql_query("""
        SELECT 
            id as ID, 
            data_cadastro as 'Data Entrada', 
            nota_fiscal as 'Nota Fiscal',
            fornecedor as 'Fornecedor',
            insumo as 'Insumo/Material', 
            lote as 'Lote', 
            data_fabricacao as 'Fabricação',
            data_validade as 'Validade',
            quantidade as 'Qtd',
            status as 'Status CQ', 
            analista as 'Analista', 
            parametros as 'Parâmetros Analisados' 
        FROM laudos ORDER BY id DESC
    """, conn)
    conn.close()
    
    if df.empty:
        st.info("Nenhum registro encontrado no banco de dados.")
    else:
        st.dataframe(df, use_container_width=True, hide_index=True)

# --- TELA 4: GERENCIAR USUÁRIOS ---
elif st.session_state["tela_ativa"] == "gerenciar_usuarios" and cargo_atual == "Supervisor":
    st.subheader("⚙️ Gerenciador de Usuários do Laboratório")
    
    st.markdown("### 🆕 Cadastrar Novo Funcionário")
    novo_u = st.text_input("Nome de Usuário:").strip().lower()
    novo_p = st.text_input("Senha Provisória:", type="password").strip()
    nova_f = st.selectbox("Função:", ["Técnico", "Analista", "Supervisor"])
    
    if st.button("Salvar Usuário", use_container_width=True):
        if novo_u and novo_p:
            conn = conectar()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM usuarios WHERE usuario = ?", (novo_u,))
            if cursor.fetchone()[0] == 0:
                cursor.execute("INSERT INTO usuarios (usuario, senha, funcao) VALUES (?, ?, ?)", (novo_u, novo_p, nova_f))
                conn.commit()
                conn.close()
                st.success(f"Usuário {novo_u} cadastrado com sucesso!")
                st.rerun()
            else:
                conn.close()
                st.error("Este nome de usuário já existe.")
        else:
            st.warning("Preencha todos os campos.")
            
    st.markdown("---")
    st.markdown("### 📋 Quadro de Operadores Ativos")
    
    conn = conectar()
    df_users = pd.read_sql_query("SELECT usuario as 'Usuário', funcao as 'Função' FROM usuarios WHERE usuario != 'admin'", conn)
    conn.close()
    
    if df_users.empty:
        st.caption("Nenhum usuário secundário cadastrado.")
    else:
        st.dataframe(df_users, use_container_width=True, hide_index=True)
        user_remover = st.selectbox("Selecione uma conta para remover do sistema:", df_users["Usuário"].tolist())
        if st.button("❌ Deletar Conta Selecionada", use_container_width=True):
            conn = conectar()


