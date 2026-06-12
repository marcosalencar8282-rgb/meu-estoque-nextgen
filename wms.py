import sqlite3
from datetime import datetime
import streamlit as st
import pandas as pd

# Configuração da página profissional e responsiva
st.set_page_config(page_title="WMS Logística", layout="wide", page_icon="📦")

# --- CONEXÃO COM O BANCO DE DADOS ---
conexao = sqlite3.connect("wms_dados_sistema.db")
cursor = conexao.cursor()

# Tabela 1: Cadastro Físico de Endereços do Armazém
cursor.execute("""
    CREATE TABLE IF NOT EXISTS enderecos (
        posicao TEXT PRIMARY KEY
    )
""")

# Tabela 2: Registro de Movimentações do Armazém
cursor.execute("""
    CREATE TABLE IF NOT EXISTS movimentacoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data_registro TEXT,
        sku TEXT,
        produto TEXT,
        quantidade REAL,
        posicao TEXT,
        tipo_movimentacao TEXT
    )
""")
conexao.commit()

# --- SESSÃO DE AUTENTICAÇÃO ---
if "logado" not in st.session_state:
    st.session_state["logado"] = False
if "usuario_atual" not in st.session_state:
    st.session_state["usuario_atual"] = ""
if "cargo_atual" not in st.session_state:
    st.session_state["cargo_atual"] = ""

if not st.session_state["logado"]:
    st.title("🔑 PORTAL DE ACESSO | WMS LOGÍSTICA")
    st.write("Insira suas credenciais logísticas corporativas para acessar o armazém.")
    st.markdown("---")
    
    u = st.text_input("Usuário / Matrícula:", key="login_usuario").strip().lower()
    p = st.text_input("Senha de Acesso:", type="password", key="login_senha").strip()
    
    if st.button("Autenticar no Sistema", use_container_width=True):
        # 💡 MUDE AS SENHAS AQUI: Altere os valores de 'admin123' ou 'operador123' para as senhas que você quiser!
        if u == "marcos" and p == "334409":
            st.session_state["logado"] = True
            st.session_state["usuario_atual"] = "admin"
            st.session_state["cargo_atual"] = "Supervisor"
            st.rerun()
        elif u == "operador" and p == "operador123":
            st.session_state["logado"] = True
            st.session_state["usuario_atual"] = "operador"
            st.session_state["cargo_atual"] = "Operador"
            st.rerun()
        else:
            st.error("Usuário ou senha incorretos.")
    st.stop()

# --- PAINEL DO USUÁRIO LOGADO ---
st.title("📦 SISTEMA DE GESTÃO DE ESTOQUE | WMS")
st.write(f"👤 Conectado: **{st.session_state['usuario_atual'].upper()}** | Perfil: **{st.session_state['cargo_atual'].upper()}**")

if st.button("🚪 Encerrar Turno (Sair)"):
    st.session_state["logado"] = False
    st.session_state["usuario_atual"] = ""
    st.session_state["cargo_atual"] = ""
    st.rerun()

st.markdown("---")

# --- CONSTRUÇÃO DO MENU CONFORME PERMISSÕES ---
cargo_do_usuario = st.session_state["cargo_atual"]

if cargo_do_usuario == "Supervisor":
    opcoes_menu = [
        "📥 Entrada e Endereçamento", 
        "📤 Separação e Baixa", 
        "📋 Posição de Inventário Real",
        "🗺️ Cadastrar Novos Endereços"
    ]
else:
    opcoes_menu = [
        "📥 Entrada e Endereçamento", 
        "📤 Separação e Baixa"
    ]

tela = st.sidebar.radio("Navegação Operacional:", opcoes_menu)
st.markdown("---")

# --- TELA 1: ENTRADA E ENDEREÇAMENTO ---
if tela == "📥 Entrada e Endereçamento":
    st.subheader("📥 Recebimento e Alocação de Mercadoria")
    
    sku_input = st.text_input("Código SKU do Produto:", key="entrada_sku")
    nome_prod = st.text_input("Descrição / Nome do Produto:", key="entrada_nome")
    qtd_input = st.number_input("Quantidade de Itens:", min_value=1.0, step=1.0, value=1.0, key="entrada_qtd")
    
    # 🌟 CORREÇÃO TÉCNICA: Entrada manual validada por texto para evitar quebras do selectbox
    posicao_estoque = st.text_input("Digite a Posição de Destino (Ex: BOX-01):", key="entrada_pos").strip().upper()
        
    if st.button("Confirmar Entrada de Material", use_container_width=True):
        if sku_input and nome_prod and posicao_estoque:
            cursor.execute("SELECT COUNT(*) FROM enderecos WHERE posicao = ?", (posicao_estoque,))
            if cursor.fetchone()[0] > 0:
                data_hoje = datetime.now().strftime("%d/%m/%Y %H:%M")
                cursor.execute("""
                    INSERT INTO movimentacoes (data_registro, sku, produto, quantity, posicao, tipo_movimentacao)
                    VALUES (?, ?, ?, ?, ?, 'ENTRADA')
                """, (data_hoje, sku_input, nome_prod, qtd_input, posicao_estoque))
                conexao.commit()
                st.success(f"Sucesso! {qtd_input} unidades alocadas na posição {posicao_estoque}.")
                st.rerun()
            else:
                st.error("🚨 Erro: Essa posição não existe no mapa do armazém. Cadastre-a primeiro!")
        else:
            st.warning("Preencha todos os campos do produto e o endereço para registrar.")

# --- TELA 2: SEPARAÇÃO / PICKING ---
elif tela == "📤 Separação e Baixa":
    st.subheader("📤 Processar Separação de Pedidos (Picking)")
    
    cursor.execute("""
        SELECT sku, produto, posicao, SUM(CASE WHEN tipo_movimentacao='ENTRADA' THEN quantidade ELSE -quantidade END) as saldo 
        FROM movimentacoes GROUP BY sku, posicao HAVING saldo > 0
    """)
    itens_disponiveis = cursor.fetchall()
    
    if not itens_disponiveis:
        st.info("Nenhuma mercadoria com saldo disponível no armazém para dar baixa.")
    else:
        opcoes_selecao = [f"SKU: {linha[0]} | Item: {linha[1]} | Posição: {linha[2]} (Saldo: {int(linha[3])})" for linha in itens_disponiveis]
        item_selecionado = st.selectbox("Selecione a carga alvo para o Picking:", opcoes_selecao, key="baixa_selecao")
        
        indice = opcoes_selecao.index(item_selecionado)
        sku_alvo = itens_disponiveis[indice][0]
        nome_alvo = itens_disponiveis[indice][1]
        posicao_alvo = itens_disponiveis[indice][2]
        saldo_maximo = itens_disponiveis[indice][3]
        
        qtd_retirar = st.number_input("Quantidade a Retirar:", min_value=1.0, max_value=float(saldo_maximo), step=1.0, value=1.0, key="baixa_qtd")
        
        if st.button("Confirmar Retirada e Expedição", use_container_width=True):
            data_hoje = datetime.now().strftime("%d/%m/%Y %H:%M")
            cursor.execute("""
                INSERT INTO movimentacoes (data_registro, sku, produto, quantidade, posicao, tipo_movimentacao)
                VALUES (?, ?, ?, ?, ?, 'SAÍDA')
            """, (data_hoje, sku_alvo, nome_alvo, qtd_retirar, posicao_alvo))
            conexao.commit()
            st.success(f"Picking concluído! {qtd_retirar} unidades retiradas de {posicao_alvo}.")
            st.rerun()

# --- TELA 3: INVENTÁRIO LOGÍSTICO ---
elif tela == "📋 Posição de Inventário Real":
    st.subheader("📋 Relatório Logístico de Saldos e Ocupação (Kardex)")
    
    st.markdown("### 🔴 Posições Ocupadas Atualmente")
    df_ocupado = pd.read_sql_query("""
        SELECT 
            sku as 'Código SKU',
            produto as 'Descrição do Item',
            posicao as 'Endereço',
            SUM(CASE WHEN tipo_movimentacao = 'ENTRADA' THEN quantidade ELSE -quantidade END) as 'Saldo'
        FROM movimentacoes 
        GROUP BY sku, posicao 
        HAVING "Saldo" > 0
        ORDER BY posicao ASC
    """, conexao)
    
    if df_ocupado.empty:
        st.info("Nenhum saldo armazenado no momento.")
    else:
        st.dataframe(df_ocupado, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.markdown("### 🟢 Endereços Vazios (Disponíveis)")
    df_livres = pd.read_sql_query("""
        SELECT posicao as 'Endereço Livre' FROM enderecos WHERE posicao NOT IN (
            SELECT posicao FROM movimentacoes 
            GROUP BY sku, posicao 
            HAVING SUM(CASE WHEN tipo_movimentacao = 'ENTRADA' THEN quantidade ELSE -quantidade END) > 0
        ) ORDER BY posicao ASC
    """, conexao)
    
    if df_livres.empty:
        st.warning("Aviso: O armazém não possui nenhuma posição vazia livre no mapa atual.")
    else:
        st.dataframe(df_livres, use_container_width=True, hide_index=True)

# --- TELA 4: CADASTRO DE ENDEREÇOS ---
elif tela == "🗺️ Cadastrar Novos Endereços":
    st.subheader("🗺️ Mapeamento e Cadastro Estrutural de Endereços")
    
    st.markdown("### 🆕 Adicionar Nova Posição Física no Galpão")
    novo_endereco = st.text_input("Código da Posição (Ex: BOX-01, PRATELEIRA-A, PALLET-10):", key="end_input").strip().upper()
    
    if st.button("Salvar Nova Posição Fisiográfica", use_container_width=True, key="btn_salvar_endereco"):
        if novo_endereco:
            cursor.execute("SELECT COUNT(*) FROM enderecos WHERE posicao = ?", (novo_endereco,))
            if cursor.fetchone()[0] == 0:
                cursor.execute("INSERT INTO enderecos (posicao) VALUES (?)", (novo_endereco,))
                conexao.commit()
                st.success(f"Sucesso! Endereço **{novo_endereco}** adicionado à malha do galpão.")
                st.rerun()
            else:
                st.error("Erro: Este endereço já existe na base de dados.")
        else:
            st.warning("Digite um código válido para a posição.")
            
    st.markdown("---")
    st.markdown("### 📋 Mapa Geral de Todos os Endereços Cadastrados")
    df_todos_end = pd.read_sql_query("SELECT posicao as 'Todos os Endereços Cadastrados' FROM enderecos ORDER BY posicao ASC", conexao)
    st.dataframe(df_todos_end, use_container_width=True, hide_index=True)

conexao.close()


