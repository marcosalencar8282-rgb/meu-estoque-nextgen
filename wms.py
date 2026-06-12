import sqlite3
from datetime import datetime
import streamlit as st
import pandas as pd

# Configuração da página profissional e responsiva
st.set_page_config(page_title="WMS Logística", layout="wide", page_icon="📦")

# --- CONEXÃO COM O BANCO DE DADOS ---
conexao = sqlite3.connect("wms_dados_sistema.db")
cursor = conexao.cursor()

# Tabela 1: Registro de Movimentações do Armazém
cursor.execute("""
    CREATE TABLE IF NOT EXISTS movimentacoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data_registro TEXT,
        sku TEXT,
        produto TEXT,
        quantidade REAL,
        posicao TEXT,
        tipo_movimentacao TEXT,
        responsavel TEXT
    )
""")

# Tabela 2: Controle de Usuários
cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        usuario TEXT PRIMARY KEY,
        senha TEXT,
        funcao TEXT
    )
""")

# Garante o usuário Administrador padrão no sistema
cursor.execute("SELECT COUNT(*) FROM usuarios WHERE usuario = 'admin'")
if cursor.fetchone()[0] == 0:
    cursor.execute("INSERT INTO usuarios (usuario, senha, funcao) VALUES ('admin', 'admin123', 'Supervisor')")
    conexao.commit()

# --- SESSÃO DE AUTENTICAÇÃO (LOGIN) ---
if "logado" not in st.session_state:
    st.session_state["logado"] = False
if "usuario_atual" not in st.session_state:
    st.session_state["usuario_atual"] = ""
if "cargo_atual" not in st.session_state:
    st.session_state["cargo_atual"] = ""

if not st.session_state["logado"]:
    st.title("🔑 PORTAL DE ACESSO | WMS LOGÍSTICA")
    st.write("Identifique-se com suas credenciais logísticas para acessar o armazém.")
    st.markdown("---")
    
    u = st.text_input("Usuário:").strip().lower()
    p = st.text_input("Senha:", type="password").strip()
    
    if st.button("Entrar no Sistema", use_container_width=True):
        if u and p:
            cursor.execute("SELECT senha, funcao FROM usuarios WHERE usuario = ?", (u,))
            dados_usuario = cursor.fetchone()
            
            if dados_usuario and dados_usuario[0] == p:
                st.session_state["logado"] = True
                st.session_state["usuario_atual"] = u
                st.session_state["cargo_atual"] = str(dados_usuario[1]).strip()
                st.rerun()
            else:
                st.error("Credenciais inválidas.")
        else:
            st.warning("Preencha todos os campos.")
    st.stop()

# --- PAINEL DO USUÁRIO LOGADO ---
st.title("📦 SISTEMA DE GESTÃO DE ESTOQUE | WMS")
st.write(f"👤 Operador: **{st.session_state['usuario_atual'].upper()}** | Função: **{st.session_state['cargo_atual'].upper()}**")

if st.button("🚪 Sair do Turno"):
    st.session_state["logado"] = False
    st.session_state["usuario_atual"] = ""
    st.session_state["cargo_atual"] = ""
    st.rerun()

st.markdown("---")

# --- MENUS DINÂMICOS CONFORME O CARGO LOGÍSTICO ---
nivel_cargo = st.session_state["cargo_atual"]
opcoes_menu = ["📋 Posição de Inventário Real"]

if nivel_cargo in ["Operador", "Supervisor"]:
    opcoes_menu.insert(0, "📥 Entrada e Endereçamento")

if nivel_cargo in ["Analista", "Supervisor"]:
    opcoes_menu.insert(1, "📤 Separação e Baixa")

if nivel_cargo == "Supervisor":
    opcoes_menu.append("👥 Equipe e Acessos")

tela = st.sidebar.radio("Operações Disponíveis:", opcoes_menu)
st.markdown("---")

# --- TELA 1: ENTRADA E ENDEREÇAMENTO ---
if tela == "📥 Entrada e Endereçamento":
    st.subheader("📥 Recebimento e Alocação de Mercadoria")
    
    c1, c2 = st.columns(2)
    with c1:
        sku_input = st.text_input("Código SKU do Produto:")
        nome_prod = st.text_input("Descrição / Nome do Produto:")
    with c2:
        qtd_input = st.number_input("Quantidade de Itens:", min_value=1.0, step=1.0, value=1.0)
        posicao_estoque = st.text_input("Posição de Destino (Ex: CORREDOR-A1):").strip().upper()
        
    if st.button("Confirmar Entrada de Material", use_container_width=True):
        if sku_input and nome_prod and posicao_estoque:
            data_hoje = datetime.now().strftime("%d/%m/%Y %H:%M")
            cursor.execute("""
                INSERT INTO movimentacoes (data_registro, sku, produto, quantidade, posicao, tipo_movimentacao, responsavel)
                VALUES (?, ?, ?, ?, ?, 'ENTRADA', ?)
            """, (data_hoje, sku_input, nome_prod, qtd_input, posicao_estoque, st.session_state["usuario_atual"]))
            conexao.commit()
            st.success(f"Sucesso! {qtd_input} unidades do SKU {sku_input} foram alocadas em {posicao_estoque}.")
            st.rerun()
        else:
            st.warning("Preencha todos os campos para registrar a entrada.")

# --- TELA 2: SEPARAÇÃO / PICKING ---
elif tela == "📤 Separação e Baixa":
    st.subheader("📤 Processar Separação de Pedidos (Picking)")
    
    # Lista apenas os itens que possuem saldo positivo real na posição
    cursor.execute("""
        SELECT sku, produto, posicao, SUM(CASE WHEN tipo_movimentacao='ENTRADA' THEN quantidade ELSE -quantidade END) as saldo 
        FROM movimentacoes GROUP BY sku, posicao HAVING saldo > 0
    """)
    itens_disponiveis = cursor.fetchall()
    
    if not itens_disponiveis:
        st.info("Nenhuma mercadoria com saldo disponível para dar baixa.")
    else:
        opcoes_selecao = [f"SKU: {item[0]} | Item: {item[1]} | Posição: {item[2]} (Saldo: {item[3]})" for item in itens_disponiveis]
        item_selecionado = st.selectbox("Selecione a carga alvo para o Picking:", opcoes_selecao)
        
        # Resgata o índice para achar os dados corretos no banco
        indice = opcoes_selecao.index(item_selecionado)
        sku_alvo = itens_disponiveis[indice][0]
        nome_alvo = itens_disponiveis[indice][1]
        posicao_alvo = itens_disponiveis[indice][2]
        saldo_maximo = itens_disponiveis[indice][3]
        
        qtd_retirar = st.number_input("Quantidade a Retirar:", min_value=1.0, max_value=float(saldo_maximo), step=1.0, value=1.0)
        
        if st.button("Confirmar Retirada e Expedição", use_container_width=True):
            data_hoje = datetime.now().strftime("%d/%m/%Y %H:%M")
            
            # Adiciona o registro de SAÍDA correspondente no histórico logístico
            cursor.execute("""
                INSERT INTO movimentacoes (data_registro, sku, produto, quantidade, posicao, tipo_movimentacao, responsavel)
                VALUES (?, ?, ?, ?, ?, 'SAÍDA', ?)
            """, (data_hoje, sku_alvo, nome_alvo, qtd_retirar, posicao_alvo, st.session_state["usuario_atual"]))
            conexao.commit()
            
            st.success(f"Picking concluído! {qtd_retirar} unidades do SKU {sku_alvo} retiradas de {posicao_alvo}.")
            st.rerun()

# --- TELA 3: INVENTÁRIO LOGÍSTICO ---
elif tela == "📋 Posição de Inventário Real":
    st.subheader("📋 Relatório de Saldos e Ocupação por Posição")
    
    # Calcula dinamicamente o saldo atual (Entradas - Saídas) agrupado por posição
    df = pd.read_sql_query("""
        SELECT 
            sku as 'Código SKU',
            produto as 'Descrição do Item',
            posicao as 'Endereço/Posição',
            SUM(CASE WHEN tipo_movimentacao = 'ENTRADA' THEN quantidade ELSE -quantidade END) as 'Qtd Disponível'
        FROM movimentacoes 
        GROUP BY sku, posicao 
        HAVING "Qtd Disponível" > 0
        ORDER BY posicao ASC
    """, conexao)
    
    if df.empty:
        st.info("O armazém está completamente vazio neste momento.")
    else:
        st.dataframe(df, use_container_width=True, hide_index=True)

# --- TELA 4: GERENCIAMENTO DA EQUIPE ---
elif tela == "👥 Equipe e Acessos":
    st.subheader("👥 Cadastro e Controle de Usuários do Armazém")
    
    novo_u = st.text_input("Matrícula / Novo Login:").strip().lower()
    novo_p = st.text_input("Senha:", type="password").strip()
    nova_f = st.selectbox("Perfil Operacional:", ["Operador", "Analista", "Supervisor"])
    
    if st.button("Homologar Novo Colaborador", use_container_width=True):
        if novo_u and novo_p:
            try:
                cursor.execute("INSERT INTO usuarios (usuario, senha, funcao) VALUES (?, ?, ?)", (novo_u, novo_p, nova_f))
                conexao.commit()
                st.success(f"Funcionário {novo_u.upper()} cadastrado com sucesso como {nova_f}!")
                st.rerun()
            except sqlite3.IntegrityError:
                st.error("Este usuário já se encontra ativo no banco de dados.")
        else:
            st.warning("Informe o login e a senha para efetuar o cadastro.")
            
    st.markdown("---")
    df_usuarios = pd.read_sql_query("SELECT usuario as 'Usuário Logístico', funcao as 'Perfil Atribuído' FROM usuarios", conexao)
    st.dataframe(df_usuarios, use_container_width=True, hide_index=True)

# FECHAMENTO SEGURO DA CONEXÃO
conexao.close()
