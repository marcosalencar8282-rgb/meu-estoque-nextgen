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
    
    # 1. Tabela de Usuários
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id_usuario INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL
        )
    ''')
    
    # 2. Tabela de Recebimento de Notas
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

    # 3. Tabela de Histórico de Devoluções
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS devolucoes (
            id_devolucao INTEGER PRIMARY KEY AUTOINCREMENT,
            id_recebimento_origem INTEGER NOT NULL,
            data_devolucao TEXT NOT NULL,
            motivo TEXT NOT NULL,
            FOREIGN KEY (id_recebimento_origem) REFERENCES recebimentos (id_recebimento)
        )
    ''')
    
    # Criar um usuário padrão caso a tabela esteja vazia (User: admin / Senha: admin123)
    cursor.execute("SELECT COUNT(*) FROM usuarios")
    if cursor.fetchone() == 0:
        senha_hash = hashlib.sha256("admin123".encode()).hexdigest()
        cursor.execute("INSERT INTO usuarios (usuario, senha) VALUES ('admin', ?)", (senha_hash,))
        
    conn.commit()
    conn.close()

# Inicializa o banco antes de carregar o visual
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
    
    # Linha corrigida com o número 3 para evitar o erro de TypeError
    col1, col2, col3 = st.columns(3)
    
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
    col_titulo, col_usuario = st.columns(2)
    with col_titulo:
        st.title("🏢 Painel Fiscal de Fornecedores")
    with col_usuario:
        st.write(f" 👤 **{st.session_state['usuario_atual']}**")
        if st.button("Sair / Logout", key="btn_logout"):
            realizar_logout()

    # Abas de Navegação
    aba_lista, aba_cadastro, aba_devolucao = st.tabs([
        "📋 Notas Recebidas", 
        "📥 Cadastrar Recebimento Manual",
        "↩️ Registrar Devolução"
    ])

    # ABA 1: LISTAGEM DE NOTAS
    with aba_lista:
        st.subheader("Histórico Geral de Notas em Estoque")
        
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
            st.dataframe(df_notas, use_container_width=True, hide_index=True)
        else:
            st.info("Nenhuma nota fiscal cadastrada no sistema.")

    # ABA 2: FORMULÁRIO DE CADASTRO MANUAL
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
                if not fornecedor.strip():
                    st.error("Por favor, preencha o nome do fornecedor.")
                elif not desc_produto.strip():
                    st.error("Por favor, preencha a descrição do produto.")
                elif qtd_produto <= 0:
                    st.error("A quantidade do produto deve ser maior que zero.")
                elif valor_total <= 0:
                    st.error("O valor total da nota deve ser maior que zero.")
                else:
                    conn = sqlite3.connect('sistema_fiscal.db')
                    cursor = conn.cursor()
                    data_formatada = data_rec.strftime('%Y-%m-%d')
                    
                    cursor.execute('''
                        INSERT INTO recebimentos (numero_nota, fornecedor, data_recebimento, descricao_produto, quantidade, valor_total)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (num_nota, fornecedor, data_formatada, desc_produto, qtd_produto, valor_total))
                    
                    conn.commit()
                    conn.close()
                    
                    st.success(f"Sucesso! Nota Fiscal Nº {num_nota} registrada no banco de dados.")
                    st.rerun()

    # ABA 3: CONTROLE DE DEVOLUÇÕES
    with aba_devolucao:
        st.subheader("Processar Devolução para Fornecedor")
        
        conn = sqlite3.connect('sistema_fiscal.db')
        notas_ativas = pd.read_sql_query("SELECT id_recebimento, numero_nota, fornecedor, descricao_produto FROM recebimentos WHERE status = 'Recebido'", conn)
        conn.close()
        
        if not notas_ativas.empty:
            opcoes_devolucao = {
                f"Nota Nº {row['numero_nota']} - Fornecedor: {row['fornecedor']} ({row['descricao_produto']})": row 
                for _, row in notas_ativas.iterrows()
            }
            
            nota_selecionada_txt = st.selectbox("Escolha a Nota Fiscal que deseja devolver:", list(opcoes_devolucao.keys()))
            dados_nota_origem = opcoes_devolucao[nota_selecionada_txt]
            
            with st.form("form_processa_devolucao"):
                motivo_dev = st.text_area("Descreva o motivo da devolução:")
                data_dev = st.date_input("Data da Devolução:", datetime.now())
                
                botao_confirmar_dev = st.form_submit_button("↩️ Confirmar Saída por Devolução")
                
                if botao_confirmar_dev:
                    if not motivo_dev.strip():
                        st.error("Por favor, preencha o motivo da devolução antes de confirmar.")
                    else:
                        conn = sqlite3.connect('sistema_fiscal.db')
                        cursor = conn.cursor()
                        data_dev_formatada = data_dev.strftime('%Y-%m-%d')
                        
                        cursor.execute('''
                            INSERT INTO devolucoes (id_recebimento_origem, data_devolucao, motivo)
                            VALUES (?, ?, ?)
                        ''', (dados_nota_origem['id_recebimento'], data_dev_formatada, motivo_dev))
                        
                        cursor.execute('''
                            UPDATE recebimentos 
                            SET status = 'Devolvido' 
                            WHERE id_recebimento = ?
                        ''', (dados_nota_origem['id_recebimento'],))
                        
                        conn.commit()
                        conn.close()
                        
                        st.success("Nota devolvida com sucesso!")
                        st.rerun()
        else:
            st.warning("Não há notas com status 'Recebido' disponíveis para devolução no momento.")
