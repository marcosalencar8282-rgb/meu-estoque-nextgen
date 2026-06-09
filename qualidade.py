import sqlite3
from datetime import datetime
import streamlit as st
import pandas as pd

# Configuração da página padrão, leve e estável
st.set_page_config(page_title="BioQuali | CQ", layout="wide", page_icon="🔬")

# --- CONEXÃO E INICIALIZAÇÃO DO BANCO DE DADOS ---
def conectar():
    return sqlite3.connect("sistema_qualidade_lab.db")

conn = conectar()
cursor = conn.cursor()

# Tabela de Amostras/Lotes e Controle de Qualidade
cursor.execute("""
    CREATE TABLE IF NOT EXISTS laudos (
        id_laudo INTEGER PRIMARY KEY AUTOINCREMENT,
        data_cadastro TEXT,
        documento TEXT,
        fornecedor TEXT,
        item_sku TEXT,
        descricao TEXT,
        lote TEXT UNIQUE,
        data_fab TEXT,
        data_val TEXT,
        status TEXT DEFAULT 'Quarentena',
        analista TEXT DEFAULT 'Pendente',
        data_analise TEXT DEFAULT '-',
        observacoes TEXT DEFAULT '-'
    )
""")

# Tabela de Usuários do Sistema
cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        usuario TEXT PRIMARY KEY,
        senha TEXT,
        perfil TEXT
    )
""")

# Garante a existência e força os privilégios do admin master sem usar try
cursor.execute("SELECT COUNT(*) FROM usuarios WHERE usuario = 'admin'")
existe_admin = cursor.fetchone()[0]
if existe_admin == 0:
    cursor.execute("INSERT INTO usuarios (usuario, senha, perfil) VALUES ('admin', 'admin123', 'administrador')")
else:
    cursor.execute("UPDATE usuarios SET perfil = 'administrador' WHERE usuario = 'admin'")

conn.commit()
conn.close()

# --- CONTROLE DE SESSÃO (STATE) ---
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False
if "usuario_logado" not in st.session_state:
    st.session_state["usuario_logado"] = ""
if "perfil_usuario" not in st.session_state:
    st.session_state["perfil_usuario"] = ""

# --- TELA DE ACESSO (LOGIN) ---
if not st.session_state["autenticado"]:
    st.title("🔬 BIOQUALI | CONTROLE DE QUALIDADE")
    st.write("Acesse o painel laboratorial informando suas credenciais.")
    st.markdown("---")
    
    c_l1, c_l2 = st.columns(2)
    with c_l1:
        u_in = st.text_input("Usuário de Acesso:", key="login_user").strip().lower()
    with c_l2:
        p_in = st.text_input("Senha de Acesso:", type="password", key="login_pass").strip()
        
    if st.button("Autenticar no Sistema", use_container_width=True):
        if u_in and p_in:
            conn = conectar()
            cursor = conn.cursor()
            cursor.execute("SELECT senha, perfil FROM usuarios WHERE usuario = ?", (u_in,))
            registro = cursor.fetchone()
            conn.close()
            
            if registro and registro[0] == p_in:
                st.session_state["autenticado"] = True
                st.session_state["usuario_logado"] = u_in
                st.session_state["perfil_usuario"] = str(registro[1]).strip().lower()
                st.rerun()
            else:
                st.error("Credenciais incorretas ou usuário inexistente.")
        else:
            st.warning("Preencha os campos obrigatórios para prosseguir.")
    st.stop()

# --- MENU LATERAL DE NAVEGAÇÃO NATIVO ---
perf = st.session_state["perfil_usuario"]

st.sidebar.title("🔬 BioQuali CQ")
st.sidebar.markdown(f"👤 **Operador:** `{st.session_state['usuario_logado'].upper()}`\n⚙️ **Função:** `{perf.upper()}`")
st.sidebar.markdown("---")

# Filtra as opções do menu de acordo com o nível de acesso do usuário
opcoes_menu = ["📋 Histórico de Laudos"]
if perf in ["administrador", "recebimento"]:
    opcoes_menu.insert(0, "📥 Entrada de Materiais")
if perf in ["administrador", "analista"]:
    opcoes_menu.insert(1, "🧫 Análise Técnica")
if perf == "administrador":
    opcoes_menu.append("⚙️ Gestão de Contas")

menu_ativo = st.sidebar.radio("Selecione a Tela:", opcoes_menu)

st.sidebar.markdown("---")
if st.sidebar.button("🚪 Sair do Sistema", use_container_width=True):
    st.session_state.clear()
    st.rerun()

# --- INDICADORES RESUMIDOS NO TOPO DA TELA ---
conn = conectar()
cursor = conn.cursor()

cursor.execute("SELECT COUNT(*) FROM laudos")
tot = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM laudos WHERE status = 'Quarentena'")
qua = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM laudos WHERE status = 'Aprovado'")
apr = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM laudos WHERE status = 'Reprovado'")
rep = cursor.fetchone()[0]

conn.close()

c_i1, c_i2, c_i3, c_i4 = st.columns(4)
with c_i1:
    st.info(f"📊 Total Registrado: {tot}")
with c_i2:
    st.warning(f"⏳ Em Quarentena: {qua}")
with c_i3:
    st.success(f"✅ Lotes Aprovados: {apr}")
with c_i4:
    st.error(f"❌ Lotes Reprovados: {rep}")

st.markdown("---")

# --- FUNÇÕES DE RENDERIZAÇÃO DAS TELAS ---

if menu_ativo == "📥 Entrada de Materiais":
    st.subheader("📥 Formulário de Entrada e Triagem")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        doc = st.text_input("Nº NF / Doc:")
    with col2:
        forn = st.text_input("Fornecedor:")
    with col3:
        sku = st.text_input("Part Number / SKU:")
    with col4:
        desc = st.text_input("Descrição do Item:")
        
    col5, col6, col7 = st.columns(3)
    with col5:
        lot = st.text_input("Código do Lote:")
    with col6:
        fab = st.text_input("Fabricação (DD/MM/AAAA):")
    with col7:
        val = st.text_input("Validade (DD/MM/AAAA):")
        
    st.write("")
    if st.button("Registrar em Quarentena", use_container_width=True):
        if doc and forn and sku and desc and lot:
            conn = conectar()
            cursor = conn.cursor()
            
            # Validação manual antes de inserir o lote para evitar erro de integridade
            cursor.execute("SELECT COUNT(*) FROM laudos WHERE lote = ?", (lot,))
            existe_lote = cursor.fetchone()[0]
            
            if existe_lote == 0:
                data_atual = datetime.now().strftime("%d/%m/%Y %H:%M")
                cursor.execute("""
                    INSERT INTO laudos (data_cadastro, documento, fornecedor, item_sku, descricao, lote, data_fab, data_val)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (data_atual, doc, forn, sku, desc, lot, fab, val))
                conn.commit()
                conn.close()
                st.success(f"Lote {lot} inserido na fila de inspeção!")
                st.rerun()
            else:
                conn.close()
                st.error("Impasse: Este identificador de lote já consta no banco.")
        else:
            st.warning("Preencha todos os campos obrigatórios da triagem.")

elif menu_ativo == "🧫 Análise Técnica":
    st.subheader("🧫 Avaliação Laboratorial e Parâmetros Analíticos")
    
    conn = conectar()
    df_abertos = pd.read_sql_query("SELECT id_laudo, lote, descricao, fornecedor, status FROM laudos WHERE status = 'Quarentena'", conn)
    conn.close()
    
    if df_abertos.empty:
        st.info("Nenhuma amostra retida em quarentena técnica no momento.")
    else:
        st.dataframe(df_abertos, use_container_width=True, hide_index=True)
        st.markdown("---")
        
        col_an1, col_an2 = st.columns(2)
        with col_an1:
            lote_alvo = st.selectbox("Selecione o Lote para Avaliação:", df_abertos["lote"].tolist())
        with col_an2:
            veredito = st.selectbox("Veredito de Liberação (Status):", ["Aprovado", "Reprovado"])
            
        obs = st.text_area("Justificativa Técnica / Parâmetros da Aprovação ou Reprevação:", 
                           placeholder="Digite os desvios, ensaios realizados ou referências normativas analisadas...")
        
        if st.button("Garantir e Emitir Laudo Final", use_container_width=True):
            if obs.strip() != "":
                conn = conectar()
                cursor = conn.cursor()
                data_inspecao = datetime.now().strftime("%d/%m/%Y %H:%M")
                cursor.execute("""
                    UPDATE laudos 
                    SET status = ?, analista = ?, data_analise = ?, observacoes = ? 
                    WHERE lote = ?
                """, (veredito, st.session_state["usuario_logado"], data_inspecao, obs, lote_alvo))
                conn.commit()
                conn.close()
                st.success(f"Laudo técnico do lote {lote_alvo} homologado como {veredito}!")
                st.rerun()
            else:
                st.warning("Erro: É obrigatório descrever os parâmetros/observações do veredito.")

elif menu_ativo == "📋 Histórico de Laudos":
    st.subheader("📋 Arquivo Geral de Rastreabilidade e Certificados")
    
    conn = conectar()
    df_geral = pd.read_sql_query("SELECT * FROM laudos ORDER BY id_laudo DESC", conn)
    conn.close()
    
    if df_geral.empty:
        st.info("O arquivo digital está vazio.")
    else:
        df_exibir = df_geral.rename(columns={
            "id_laudo": "ID", "data_cadastro": "Data Entrada", "documento": "Nº Doc/NF",
            "fornecedor": "Fornecedor", "item_sku": "SKU", "descricao": "Descrição Material",
            "lote": "Lote Código", "data_fab": "Fabricação", "data_val": "Validade",
            "status": "Veredito CQ", "analista": "Responsável", "data_analise": "Data Parecer",
            "observacoes": "Parâmetros/Observações Justificadas"
        })
        st.dataframe(df_exibir, use_container_width=True, hide_index=True)

elif menu_ativo == "⚙️ Gestão de Contas":
    st.subheader("⚙️ Painel do Administrador: Gerenciador de Usuários")
    
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        st.markdown("**Adicionar Novo Operador:**")
        u_novo = st.text_input("Novo Usuário:", key="add_u").strip().lower()
        p_novo = st.text_input("Nova Senha:", type="password", key="add_p").strip()
        f_nova = st.selectbox("Função/Perfil:", ["recebimento", "analista", "visualizar"])
        
        if st.button("Cadastrar Novo Usuário", use_container_width=True):

