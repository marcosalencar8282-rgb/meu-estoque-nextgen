import sqlite3
from datetime import datetime
import streamlit as st
import pandas as pd

# Configuração estável e leve da página
st.set_page_config(page_title="CQ Lab", layout="wide", page_icon="🔬")

# --- CONEXÃO DIRETA COM O BANCO DE DADOS ---
def conectar():
    return sqlite3.connect("sistema_laboratorio_simples.db")

conn = conectar()
cursor = conn.cursor()

# Criação da tabela base caso não exista
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

# --- ATUALIZAÇÃO AUTOMÁTICA DA TABELA ---
novas_colunas = {
    "nota_fiscal": "TEXT",
    "fornecedor": "TEXT",
    "data_fabricacao": "TEXT",
    "data_validade": "TEXT",
    "quantidade": "REAL"
}

for coluna, tipo in novas_colunas.items():
    try:
        cursor.execute(f"ALTER TABLE laudos ADD COLUMN {coluna} {tipo}")
    except sqlite3.OperationalError:
        pass

# Criação da tabela de usuários
cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        usuario TEXT PRIMARY KEY,
        senha TEXT,
        funcao TEXT
    )
""")

# Garante o usuário administrador master no sistema com o perfil correto de Supervisor
cursor.execute("SELECT COUNT(*) FROM usuarios WHERE usuario = 'admin'")
if cursor.fetchone()[0] == 0:
    cursor.execute("INSERT INTO usuarios (usuario, senha, funcao) VALUES ('admin', 'admin123', 'Supervisor')")
    conn.commit()

conn.close()

# --- CONTROLE DE SESSÃO (STATE) ---
if "logado" not in st.session_state:
    st.session_state["logado"] = False
if "user" not in st.session_state:
    st.session_state["user"] = ""
if "cargo" not in st.session_state:
    st.session_state["cargo"] = ""

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
            
            # Desempacota corretamente os índices da tupla do banco de dados
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

# --- PAINEL PRINCIPAL (LOGADO) ---
st.title("🔬 SISTEMA DE QUALIDADE E LAUDOS")
st.write(f"👤 Operador: **{st.session_state['user'].upper()}** | Cargo: **{st.session_state['cargo'].upper()}**")

if st.button("🚪 Sair do Sistema"):
    st.session_state["logado"] = False
    st.session_state["user"] = ""
    st.session_state["cargo"] = ""
    st.rerun()

st.markdown("---")

# --- CONTROLE DE AUTORIZAÇÃO POR FUNÇÃO (MENU DINÂMICO RÍGIDO) ---
cargo_atual = st.session_state["cargo"]

# O Histórico de Laudos (Relatório) é visível para todos os cargos cadastrados
opcoes_autorizadas = ["📋 3. Histórico de Laudos"]

# Técnico e Supervisor acessam o Cadastro/Entrada
if cargo_atual == "Técnico" or cargo_atual == "Supervisor":
    opcoes_autorizadas.insert(0, "📥 1. Entrada de Insumo")

# Analista e Supervisor acessam a Emissão de Laudos
if cargo_atual == "Analista" or cargo_atual == "Supervisor":
    opcoes_autorizadas.insert(1, "🧫 2. Emitir Laudo Técnico")

# Apenas o Supervisor enxerga o painel de gerenciamento de usuários
if cargo_atual == "Supervisor":
    opcoes_autorizadas.append("⚙️ 4. Gerenciar Usuários")

# Renderiza as opções validadas na barra lateral do painel
tela = st.sidebar.radio("Navegação Autorizada:", opcoes_autorizadas)

st.markdown("---")

# --- TRAVA DE SEGURANÇA INTERNA DE DUPLA CAMADA ---
if tela == "📥 1. Entrada de Insumo" and cargo_atual not in ["Técnico", "Supervisor"]:
    st.error("Acesso negado. Sua função não possui autorização para cadastrar entradas.")
    st.stop()

if tela == "🧫 2. Emitir Laudo Técnico" and cargo_atual not in ["Analista", "Supervisor"]:
    st.error("Acesso negado. Sua função não possui autorização para emitir laudos laboratoriais.")
    st.stop()

if tela == "⚙️ 4. Gerenciar Usuários" and cargo_atual != "Supervisor":
    st.error("Acesso negado. Apenas o Supervisor pode gerenciar contas corporativas.")
    st.stop()

# --- TELA 1: ENTRADA DE INSUMO ---
if tela == "📥 1. Entrada de Insumo":
    st.subheader("📥 Registrar Entrada de Material (Quarentena)")
    
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
        
    if st.button("Enviar para Inspeção", use_container_width=True):
        if nome_insumo and num_lote and nota_fiscal and fornecedor:
            conn = conectar()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM laudos WHERE lote = ?", (num_lote,))
            existe_lote = cursor.fetchone()[0]
            
            if existe_lote == 0:
                data_hoje = datetime.now().strftime("%d/%m/%Y %H:%M")
                cursor.execute("""
                    INSERT INTO laudos (data_cadastro, nota_fiscal, fornecedor, insumo, lote, data_fabricacao, data_validade, quantidade) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (data_hoje, nota_fiscal, fornecedor, nome_insumo, num_lote, data_fab, data_val, qtd_insumo))
                conn.commit()
                conn.close()
                st.success(f"Material {nome_insumo} registrado em quarentena!")
                st.rerun()
            else:
                conn.close()
                st.error("Erro: Este número de lote já existe no sistema.")
        else:
            st.warning("Preencha Nota Fiscal, Fornecedor, Nome do Insumo e Lote para prosseguir.")

# --- TELA 2: EMITIR LAUDO TÉCNICO ---
elif tela == "🧫 2. Emitir Laudo Técnico":
    st.subheader("🧫 Avaliação de Parâmetros e Liberação de Laudo")
    
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT lote FROM laudos WHERE status = 'Em Quarentena'")
    registros_lotes = cursor.fetchall()
    conn.close()
    
    lotes_pendentes = [item[0] for item in registros_lotes]
    
    if not lotes_pendentes:
        st.info("Nenhum lote aguardando análise laboratorial no momento.")
    else:
        lote_selecionado = st.selectbox("Selecione o Lote para Analisar:", lotes_pendentes)
        resultado = st.selectbox("Veredito do Controle de Qualidade:", ["Aprovado", "Reprovado"])
        justificativa = st.text_area("Descreva os Parâmetros Analisados (Aprovação/Reprovação):", placeholder="Digite as especificações, ensaios ou desvios encontrados...")
        
        if st.button("Homologar Laudo Definitivo", use_container_width=True):
            if justificativa.strip() != "":
                conn = conectar()
                cursor = conn.cursor()
                cursor.execute("UPDATE laudos SET status = ?, analista = ?, parametros = ? WHERE lote = ?", (resultado, st.session_state["user"], justificativa, lote_selecionado))
                conn.commit()
                conn.close()
                st.success(f"O lote {lote_selecionado} foi classificado como {resultado}!")
                st.rerun()
            else:
                st.error("Erro obrigatório: Você precisa preencher os parâmetros analisados para emitir o laudo.")

# --- TELA 3: HISTÓRICO DE LAUDOS ---
elif tela == "📋 3. Histórico de Laudos":
    st.subheader("📋 Arquivo de Laudos Registrados")
    
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

# --- TELA 4: GERENCIAR USUÁRIOS (BLOCO BLINDADO) ---
elif tela == "⚙️ 4. Gerenciar Usuários":
    st.subheader("⚙️ Gerenciador de Usuários do Laboratório")
    
    # Formulário Isolado para Cadastrar Funcionário
    with st.form("cadastro_usuario_form"):
        st.markdown("### 🆕 Cadastrar Novo Funcionário")
        novo_u = st.text_input("Nome de Usuário:").strip().lower()
        novo_p = st.text_input("Senha Provisória:", type="password").strip()
        nova_f = st.selectbox("Função:", ["Técnico", "Analista", "Supervisor"])
        salvar = st.form_submit_button("Salvar Usuário", use_container_width=True)
        
        if salvar:
            if novo_u and novo_p:
                conn = conectar()
                cursor = conn.cursor()


