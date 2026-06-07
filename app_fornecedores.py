import streamlit as st
import sqlite3
from datetime import datetime
import pandas as pd
import hashlib

# CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Sistema Fiscal Pro", page_icon="🔒", layout="wide")

# CONEXÃO E CRIAÇÃO DAS TABELAS DO BANCO DE DADOS
def inicializar_banco():
    conn = sqlite3.connect('sistema_fiscal.db')
    cursor = conn.cursor()
    
    # Tabela de Usuários (Senha salva com Hash por segurança)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id_usuario INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL
        )
    ''')
    
    # Tabela de Recebimento de Notas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS recebimentos (
            id_recebimento INTEGER PRIMARY KEY AUTOINCREMENT,
            numero_nota INTEGER NOT NULL,
            fornecedor TEXT NOT NULL,
            data_recebimento TEXT NOT NULL,
            descricao_produto TEXT NOT NULL,
            quantidade REAL NOT NULL,
            valor_total REAL NOT NULL,
            status TEXT DEFAULT 'Recebido'
        )
    ''')
    
    # Criar um usuário padrão caso a tabela esteja vazia (User: admin / Senha: admin123)
    cursor.execute("SELECT COUNT(*) FROM usuarios")
    if cursor.fetchone()[0] == 0:
        senha_hash = hashlib.sha256("admin123".encode()).hexdigest()
        cursor.execute("INSERT INTO usuarios (usuario, senha) VALUES ('admin', ?)", (senha_hash,))
        
    conn.commit()
    conn.close()

# Inicializa o banco de dados antes de carregar a interface
inicializar_banco()

# CONTROLE DE SESSÃO DE LOGIN
if 'logado' not in st.session_state:
    st.session_state['logado'] = False

def realizar_login(usuario, senha):
    senha_hash = hashlib.sha256(senha.encode()).hexdigest()
    conn = sqlite3.connect('sistema_fiscal.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM usuarios WHERE usuario = ? AND senha = ?", (usuario, senha_hash))
    usuario_valido = cursor.fetchone()
    conn.close()
    
    if usuario_valido:
        st.session_state['logado'] = True
        st.session_state['usuario_atual'] = usuario
        st.rerun()
    else:
        st.error("Usuário ou senha incorretos.")

def realizar_logout():
    st.session_state['logado'] = False
    st.session_state['usuario_atual'] = None
    st.rerun()

# --- TELA DE LOGIN ---
if not st.session_state['logado']:
    st.markdown("<h2 style='text-align: center;'>🔒 Acesso ao Sistema Fiscal</h2>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        with st.form("form_login"):
            usuario_input = st.text_input("Usuário:")
            senha_input = st.text_input("Senha:", type="password")
            botao_entrar = st.form_submit_button("Entrar no Sistema")
            
            if botao_entrar:
                realizar_login(usuario_input, senha_input)
        st.info("💡 Credenciais padrão para teste:\nUsuário: admin\nSenha: admin123")

# --- TELA PRINCIPAL (APÓS LOGIN) ---
else:
    # Barra Superior com informações do Usuário
    col_titulo, col_usuario = st.columns([4, 1])
    with col_titulo:
        st.title("🏢 Painel de Recebimento de Notas")
    with col_usuario:
        st.write(f"👤 **{st.session_state['usuario_atual']}**")
        if st.button("Sair / Logout", key="btn_logout"):
            realizar_logout()

    # Abas de Navegação do Sistema
    aba_lista, aba_cadastro = st.tabs(["📋 Notas Recebidas", "📥 Cadastrar Recebimento Manual"])

    # ABA 1: LISTAGEM DE NOTAS
    with aba_lista:
        st.subheader("Histórico de Notas em Estoque")
        
        # Abrimos a conexão para ler os dados mais recentes do banco
        conn = sqlite3.connect('sistema_fiscal.db')
        df_notas = pd.read_sql_query('''
            SELECT numero_nota AS [Nº Nota], fornecedor AS [Fornecedor], 
                   data_recebimento AS [Data Recebimento], descricao_produto AS [Produto], 
                   quantidade AS [Qtd], valor_total AS [Valor R$], status AS [Status] 
            FROM recebimentos
            ORDER BY id_recebimento DESC
        ''', conn)
        conn.close()

        if not df_notas.empty:
            # Exibe a tabela com os dados reais salvos
            st.dataframe(df_notas, use_container_width=True, hide_index=True)
        else:
            st.info("Nenhuma nota fiscal foi cadastrada manualmente ainda. Vá na aba ao lado para cadastrar.")

    # ABA 2: FORMULÁRIO DE PREENCHIMENTO DOS CAMPOS
    with aba_cadastro:
        st.subheader("Formulário de Entrada Manual de Nota Fiscal")
        
        with st.form("form_cadastro_nota", clear_on_submit=True):
            col_1, col_2 = st.columns(2)
            
            with col_1:
                num_nota = st.number_input("Número da Nota Fiscal:", min_value=1, step=1, value=1, key="f_num")
                fornecedor = st.text_input("Nome/Razão Social do Fornecedor:", key="f_forn")
                data_rec = st.date_input("Data de Recebimento:", datetime.now(), key="f_data")
                
            with col_2:
                desc_produto = st.text_input("Descrição do Produto:", key="f_desc")
                qtd_produto = st.number_input("Quantidade Recebida:", min_value=0.0, step=1.0, format="%.2f", key="f_qtd")
                valor_total = st.number_input("Valor Total da Nota (R$):", min_value=0.0, step=0.01, format="%.2f", key="f_val")
                
            botao_salvar = st.form_submit_button("💾 Gravar Recebimento")
            
            if botao_salvar:
                # Validação básica de campos obrigatórios
                if not fornecedor.strip():
                    st.error("Por favor, preencha o nome do fornecedor.")
                elif not desc_produto.strip():
                    st.error("Por favor, preencha a descrição do produto.")
                elif qtd_produto <= 0:
                    st.error("A quantidade do produto deve ser maior que zero.")
                elif valor_total <= 0:
                    st.error("O valor total da nota deve ser maior que zero.")
                else:
                    # Salva os dados digitados diretamente no banco SQLite
                    conn = sqlite3.connect('sistema_fiscal.db')
                    cursor = conn.cursor()
                    
                    data_formatada = data_rec.strftime('%Y-%m-%d')
                    
                    cursor.execute('''
                        INSERT INTO recebimentos (numero_nota, fornecedor, data_recebimento, descricao_produto, quantidade, valor_total)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (num_nota, fornecedor, data_formatada, desc_produto, qtd_produto, valor_total))
                    
                    conn.commit()
                    conn.close()
                    
                    # Mensagem de sucesso e comando para forçar a atualização imediata da tabela
                    st.success(f"Sucesso! Nota Fiscal Nº {num_nota} registrada no banco de dados.")
                    st.rerun()
