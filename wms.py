import sqlite3
from datetime import datetime
import streamlit as st
import pandas as pd

# Configuração da página profissional e responsiva
st.set_page_config(page_title="WMS Logística", layout="wide", page_icon="📦")

# --- CONEXÃO COM O BANCO DE DADOS ---
conexao = sqlite3.connect("wms_dados_sistema.db")
cursor = conexao.cursor()

# Tabela 1: Cadastro Físico de Endereços do Armazém (Criados por Você)
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
        tipo_movimentacao TEXT,
        responsavel TEXT
    )
""")

# Tabela 3: Controle de Usuários
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
    opcoes_menu.append("⚙️ Configurações e Equipe")

tela = st.sidebar.radio("Operações Disponíveis:", opcoes_menu)
st.markdown("---")

# --- TELA 1: ENTRADA E ENDEREÇAMENTO ---
if tela == "📥 Entrada e Endereçamento":
    st.subheader("📥 Recebimento e Alocação de Mercadoria")
    
    # Busca apenas os endereços cadastrados que estão vazios no momento
    cursor.execute("""
        SELECT posicao FROM enderecos WHERE posicao NOT IN (
            SELECT posicao FROM movimentacoes 
            GROUP BY sku, posicao 
            HAVING SUM(CASE WHEN tipo_movimentacao = 'ENTRADA' THEN quantidade ELSE -quantidade END) > 0
        ) ORDER BY posicao ASC
    """)
    enderecos_vazios = [item[0] for item in cursor.fetchall()]
    
    c1, c2 = st.columns(2)
    with c1:
        sku_input = st.text_input("Código SKU do Produto:")
        nome_prod = st.text_input("Descrição / Nome do Produto:")
    with c2:
        qtd_input = st.number_input("Quantidade de Itens:", min_value=1.0, step=1.0, value=1.0)
        if enderecos_vazios:
            posicao_estoque = st.selectbox("Selecione um Endereço Vazio Disponível:", enderecos_vazios)
        else:
            st.error("🚨 Sem posições livres! Cadastre novos endereços na tela de Configurações.")
            posicao_estoque = None
        
    if st.button("Confirmar Entrada de Material", use_container_width=True) and posicao_estoque:
        if sku_input and nome_prod:
            data_hoje = datetime.now().strftime("%d/%m/%Y %H:%M")
            cursor.execute("""
                INSERT INTO movimentacoes (data_registro, sku, produto, quantidade, posicao, tipo_movimentacao, responsavel)
                VALUES (?, ?, ?, ?, ?, 'ENTRADA', ?)
            """, (data_hoje, sku_input, nome_prod, qtd_input, posicao_estoque, st.session_state["usuario_atual"]))
            conexao.commit()
            st.success(f"Sucesso! {qtd_input} unidades foram alocadas em {posicao_estoque}.")
            st.rerun()
        else:
            st.warning("Preencha os dados do produto para registrar.")

# --- TELA 2: SEPARAÇÃO / PICKING ---
elif tela == "📤 Separação e Baixa":
    st.subheader("📤 Processar Separação de Pedidos (Picking)")
    
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
        
        indice = opcoes_selecao.index(item_selecionado)
        sku_alvo = itens_disponiveis[indice][0]
        nome_alvo = itens_disponiveis[indice][1]
        posicao_alvo = itens_disponiveis[indice][2]
        saldo_maximo = itens_disponiveis[indice][3]
        
        qtd_retirar = st.number_input("Quantidade a Retirar:", min_value=1.0, max_value=float(saldo_maximo), step=1.0, value=1.0)
        
        if st.button("Confirmar Retirada e Expedição", use_container_width=True):
            data_hoje = datetime.now().strftime("%d/%m/%Y %H:%M")
            cursor.execute("""
                INSERT INTO movimentacoes (data_registro, sku, produto, quantidade, posicao, tipo_movimentacao, responsavel)
                VALUES (?, ?, ?, ?, ?, 'SAÍDA', ?)
            """, (data_hoje, sku_alvo, nome_alvo, qtd_retirar, posicao_alvo, st.session_state["usuario_atual"]))
            conexao.commit()
            st.success(f"Picking concluído! {qtd_retirar} unidades retiradas de {posicao_alvo}.")
            st.rerun()

# --- TELA 3: INVENTÁRIO LOGÍSTICO (OCUPADOS VS VAZIOS) ---
elif tela == "📋 Posição de Inventário Real":
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📋 Posições Ocupadas (Saldo Real)")
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
            st.info("Nenhum saldo ocupado no momento.")
        else:
            st.dataframe(df_ocupado, use_container_width=True, hide_index=True)

    with col2:
        st.subheader("🟢 Endereços Totalmente Vazios")
        df_livres = pd.read_sql_query("""
            SELECT posicao as 'Endereço Disponível' FROM enderecos WHERE posicao NOT IN (
                SELECT posicao FROM movimentacoes 
                GROUP BY sku, posicao 
                HAVING SUM(CASE WHEN tipo_movimentacao = 'ENTRADA' THEN quantidade ELSE -quantidade END) > 0
            ) ORDER BY posicao ASC
        """, conexao)
        
        if df_livres.empty:
            st.info("Nenhum endereço vazio disponível. Cadastre novos endereços!")
        else:
            st.dataframe(df_livres, use_container_width=True, hide_index=True)

# --- TELA 4: CONFIGURAÇÕES DO ARMAZÉM E EQUIPE ---
elif tela == "⚙️ Configurações e Equipe":
    st.subheader("⚙️ Painel de Controle Administrativo")
    
    tab1, tab2 = st.tabs(["🗺️ Cadastrar Endereços", "👥 Gerenciar Equipe"])
    
    with tab1:
        st.markdown("### 🆕 Adicionar Nova Posição no Armazém")
        novo_endereco = st.text_input("Digite o código do novo endereço (Ex: PREDIO1-A01, PALLET-05):").strip().upper()
        
        if st.button("Salvar Nova Posição Estrutural", use_container_width=True):
            if novo_endereco:
                try:
                    cursor.execute("INSERT INTO enderecos (posicao) VALUES (?)", (novo_endereco,))
                    conexao.commit()
                    st.success(f"Endereço **{novo_endereco}** adicionado ao mapa do galpão!")
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("Erro: Esse endereço já está cadastrado no sistema.")
            else:
                st.warning("Por favor, digite um nome válido para a posição.")
                
        st.markdown("---")
        st.markdown("### 📋 Mapa de Todos os Endereços Cadastrados")
