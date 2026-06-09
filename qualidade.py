import sqlite3
from datetime import datetime
import streamlit as st
import pandas as pd

# Configuração da página profissional, leve e estável
st.set_page_config(page_title="CQ Lab", layout="wide", page_icon="🔬")

# --- CONEXÃO DIRETA COM O BANCO DE DADOS ---
conn = sqlite3.connect("sistema_laboratorio_definitivo.db")
cursor = conn.cursor()

# Criação da tabela de laudos e insumos com todos os campos necessários
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

# Criação da tabela de controle de acesso de usuários
cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        usuario TEXT PRIMARY KEY,
        senha TEXT,
        funcao TEXT
    )
""")

# Garante a existência do Administrador Master do laboratório
cursor.execute("SELECT COUNT(*) FROM usuarios WHERE usuario = 'admin'")
if cursor.fetchone()[0] == 0:
    cursor.execute("INSERT INTO usuarios (usuario, senha, funcao) VALUES ('admin', 'admin123', 'Supervisor')")
    conn.commit()

# --- ESTRUTURA DE AUTENTICAÇÃO (LOGIN) ---
if "logado" not in st.session_state:
    st.session_state["logado"] = False
if "user" not in st.session_state:
    st.session_state["user"] = ""
if "cargo" not in st.session_state:
    st.session_state["cargo"] = ""

if not st.session_state["logado"]:
    st.title("🔬 LOGIN | CONTROLE DE QUALIDADE")
    st.write("Insira suas credenciais corporativas para acessar o laboratório.")
    st.markdown("---")
    
    u = st.text_input("Nome de Usuário:").strip().lower()
    p = st.text_input("Senha de Acesso:", type="password").strip()
    
    if st.button("Autenticar no Sistema", use_container_width=True):
        if u and p:
            cursor.execute("SELECT senha, funcao FROM usuarios WHERE usuario = ?", (u,))
            dados_usuario = cursor.fetchone()
            
            if dados_usuario and dados_usuario[0] == p:
                st.session_state["logado"] = True
                st.session_state["user"] = u
                st.session_state["cargo"] = str(dados_usuario[1]).strip()
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos.")
        else:
            st.warning("Por favor, preencha todos os campos de login.")
    st.stop()

# --- PAINEL PRINCIPAL LOGADO ---
st.title("🔬 BIOLAB | SISTEMA DE CONTROLE DE QUALIDADE")
st.write(f"👤 Usuário: **{st.session_state['user'].upper()}** | Cargo: **{st.session_state['cargo'].upper()}**")

if st.button("🚪 Encerrar Sessão (Sair)"):
    st.session_state["logado"] = False
    st.session_state["user"] = ""
    st.session_state["cargo"] = ""
    st.rerun()

st.markdown("---")

# --- MENU LATERAL DE NAVEGAÇÃO AUTORIZADA ---
cargo_atual = st.session_state["cargo"]
opcoes_menu = ["📋 Histórico Geral de Laudos"]

if cargo_atual == "Técnico" or cargo_atual == "Supervisor":
    opcoes_menu.insert(0, "📥 Registrar Entrada de Insumo")

if cargo_atual == "Analista" or cargo_atual == "Supervisor":
    opcoes_menu.insert(1, "🧫 Avaliação e Parecer Técnico")

if cargo_atual == "Supervisor":
    opcoes_menu.append("⚙️ Gerenciador de Usuários")

tela = st.sidebar.radio("Menu de Telas Disponíveis:", opcoes_menu)
st.markdown("---")

# --- TELA 1: ENTRADA DE INSUMO ---
if tela == "📥 Registrar Entrada de Material":
    st.subheader("📥 Formulário de Recebimento e Triagem (Quarentena)")
    
    c1, c2, c3 = st.columns(3)
    with c1:
        nota_fiscal = st.text_input("Número da Nota Fiscal:")
        fornecedor = st.text_input("Nome do Fornecedor:")
    with c2:
        nome_insumo = st.text_input("Nome do Insumo / Material:")
        num_lote = st.text_input("Número do Lote Único:")
    with c3:
        qtd_insumo = st.number_input("Quantidade Recebida:", min_value=0.0, step=1.0, value=0.0)
        data_fab = st.text_input("Data de Fabricação (Ex: DD/MM/AAAA):")
        data_val = st.text_input("Data de Validade (Ex: DD/MM/AAAA):")
        
    if st.button("Salvar Registro e Reter em Quarentena", use_container_width=True):
        if nome_insumo and num_lote and nota_fiscal and fornecedor:
            cursor.execute("SELECT COUNT(*) FROM laudos WHERE lote = ?", (num_lote,))
            if cursor.fetchone()[0] == 0:
                data_hoje = datetime.now().strftime("%d/%m/%Y %H:%M")
                cursor.execute("""
                    INSERT INTO laudos (data_cadastro, nota_fiscal, fornecedor, insumo, lote, data_fabricacao, data_validade, quantidade) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (data_hoje, nota_fiscal, fornecedor, nome_insumo, num_lote, data_fab, data_val, qtd_insumo))
                conn.commit()
                st.success(f"Sucesso! Material {nome_insumo} (Lote {num_lote}) enviado para análise.")
                st.rerun()
            else:
                st.error("Impasse: Este número de lote já está cadastrado na base de dados.")
        else:
            st.warning("Campos Obrigatórios: Preencha Nota Fiscal, Fornecedor, Insumo e Lote.")

# --- TELA 2: EMITIR LAUDO TÉCNICO ---
elif tela == "🧫 Avaliação e Parecer Técnico":
    st.subheader("🧫 Controle de Qualidade Laboratorial")
    
    cursor.execute("SELECT lote FROM laudos WHERE status = 'Em Quarentena'")
    lotes_disponiveis = [item[0] for item in cursor.fetchall()]
    
    if not lotes_disponiveis:
        st.info("Excelente! Nenhum material retido em quarentena aguardando análise.")
    else:
        lote_selecionado = st.selectbox("Selecione o Lote Alvo para Análise:", lotes_disponiveis)
        resultado = st.selectbox("Veredito Final da Inspeção:", ["Aprovado", "Reprovado"])
        justificativa = st.text_area("Parâmetros Analisados / Justificativa Técnica do Laudo:", 
                                   placeholder="Descreva obrigatoriamente os ensaios executados, desvios detectados ou referências normativas...")
        
        if st.button("Homologar Parecer e Emitir Laudo", use_container_width=True):
            if justificativa.strip() != "":
                cursor.execute("UPDATE laudos SET status = ?, analista = ?, parametros = ? WHERE lote = ?", (resultado, st.session_state["user"], justificativa, lote_selecionado))
                conn.commit()
                st.success(f"Laudo emitido! O lote {lote_selecionado} foi classificado como {resultado}.")
                st.rerun()
            else:
                st.error("Erro Impeditivo: Descreva os parâmetros avaliados para poder fechar o laudo.")

# --- TELA 3: HISTÓRICO DE LAUDOS ---
elif tela == "📋 Histórico Geral de Laudos":
    st.subheader("📋 Arquivo de Rastreabilidade Técnico-Digital")
    
    df = pd.read_sql_query("""
        SELECT 
            id as ID, 
            data_cadastro as 'Data Entrada', 
            nota_fiscal as 'Nota Fiscal',
            fornecedor as 'Fornecedor',
            insumo as 'Material/Insumo', 
            lote as 'Lote Código', 
            data_fabricacao as 'Fabricação',
            data_validade as 'Validade',
            quantidade as 'Vol/Qtd',
            status as 'Status CQ', 
            analista as 'Analista Responsável', 
            parametros as 'Parâmetros / Justificativa' 
        FROM laudos ORDER BY id DESC
    """, conn)
    
    if df.empty:
        st.info("Nenhum registro localizado no banco de dados.")
    else:
        st.dataframe(df, use_container_width=True, hide_index=True)

# --- TELA 4: GERENCIAR USUÁRIOS ---
elif tela == "⚙️ Gerenciador de Usuários":
    st.subheader("⚙️ Controle e Gerenciamento de Acessos")
    
    st.markdown("### 🆕 Cadastrar Novo Colaborador")
    novo_u = st.text_input("Nome de Usuário (Login):").strip().lower()
    novo_p = st.text_input("Senha Inicial Provisória:", type="password").strip()
    nova_f = st.selectbox("Perfil / Função:", ["Técnico", "Analista", "Supervisor"])
    
    if st.button("Concluir Cadastro do Funcionário", use_container_width=True):
        if novo_u and novo_p:
            cursor.execute("SELECT COUNT(*) FROM usuarios WHERE usuario = ?", (novo_u,))
            if cursor.fetchone()[0] == 0:
                cursor.execute("INSERT INTO usuarios (usuario, senha, funcao) VALUES (?, ?, ?)", (novo_u, novo_p, nova_f))
                conn.commit()
                st.success(f"Conta do usuário '{novo_u}' cadastrada com sucesso como {nova_f}!")
                st.rerun()
            else:
                st.error("Erro: Este nome de usuário já está sendo utilizado por outro operador.")
        else:
            st.warning("Preencha o nome de usuário e a senha para efetuar o cadastro.")
            
    st.markdown("---")
    st.markdown("### ❌ Quadro de Operadores Ativos e Exclusão")
    
    df_users = pd.read_sql_query("SELECT usuario as 'Usuário', funcao as 'Função' FROM usuarios WHERE usuario != 'admin'", conn)
    
    if df_users.empty:
        st.caption("Nenhum funcionário secundário cadastrado no servidor.")
    else:
        st.dataframe(df_users, use_container_width=True, hide_index=True)
        user_remover = st.selectbox("Selecione uma conta para deletar definitivamente:", df_users["Usuário"].tolist())
        
        if st.button("Excluir Conta Selecionada", use_container_width=True):
            cursor.execute("DELETE FROM usuarios WHERE usuario = ?", (user_remover,))
            conn.commit()
            st.success(f"Sucesso! A conta do operador '{user_remover}' foi apagada.")
            st.rerun()


