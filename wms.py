import streamlit as st
from datetime import datetime
import pandas as pd
import io
import hashlib
import hmac

# Configuração da página profissional e responsiva
st.set_page_config(page_title="WMS Logística Pro", layout="wide", page_icon="📦")

# --- CONEXÃO NATIVA COM O BANCO DE DADOS DO STREAMLIT ---
# Tenta conectar ao banco oficial do Streamlit, se não achar, roda em modo demonstração
try:
    conn = st.connection("postgresql", type="sql")
    banco_configurado = True
except Exception:
    banco_configurado = False

# --- FUNÇÕES DE SEGURANÇA NATIVAS DO PYTHON ---
def gerar_senha_hash(senha):
    salt = b"wms_logistica_secret_salt_2026"
    return hmac.new(salt, senha.encode('utf-8'), hashlib.sha256).hexdigest()

def verificar_senha(senha, senha_hash):
    return hmac.compare_digest(gerar_senha_hash(senha), senha_hash)

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
        if banco_configurado:
            try:
                # Busca o usuário de forma segura no banco nativo
                query = "SELECT senha_hash, cargo FROM usuarios WHERE usuario = :u"
                dados_usuario = conn.query(query, params={"u": u}, ttl=0)
                
                if not dados_usuario.empty:
                    senha_db = dados_usuario.iloc[0]['senha_hash']
                    cargo_db = dados_usuario.iloc[0]['cargo']
                    
                    if verificar_senha(p, senha_db):
                        st.session_state["logado"] = True
                        st.session_state["usuario_atual"] = u
                        st.session_state["cargo_atual"] = cargo_db
                        st.success("Autenticado com sucesso!")
                        st.rerun()
                    else:
                        st.error("Usuário ou senha incorretos.")
                else:
                    st.error("Usuário ou senha incorretos.")
            except Exception:
                st.error("Tabelas do banco não encontradas. Ative o banco no painel do Streamlit.")
        else:
            # Login de Administrador de teste caso o banco não esteja ligado
            if u == "admin" and p == "334409":
                st.session_state["logado"] = True
                st.session_state["usuario_atual"] = "admin"
                st.session_state["cargo_atual"] = "Supervisor"
                st.rerun()
            else:
                st.error("Modo de teste ativo. Use o usuário admin para entrar.")
    st.stop()

# --- PAINEL DO USUÁRIO LOGADO ---
st.title("📦 GESTÃO DE ESTOQUE | WMS MULTI-USUÁRIO")
st.write(f"👤 Conectado: **{st.session_state['usuario_atual'].upper()}** | Perfil: **{st.session_state['cargo_atual'].upper()}**")

if st.button("🚪 Encerrar Turno (Sair)"):
    st.session_state["logado"] = False
    st.session_state["usuario_atual"] = ""
    st.session_state["cargo_atual"] = ""
    st.rerun()

st.markdown("---")

cargo_do_usuario = st.session_state["cargo_atual"]
opcoes_menu = ["📥 Entrada e Endereçamento", "📤 Separação e Baixa"]
if cargo_do_usuario == "Supervisor":
    opcoes_menu.extend(["📋 Posição de Inventário Real", "🕵️ Histórico de Auditoria", "🗺️ Cadastrar Recursos"])

tela = st.sidebar.radio("Navegação Operacional:", opcoes_menu)
st.markdown("---")

if not banco_configurado:
    st.warning("⚠️ Sistema rodando temporariamente sem banco de dados na nuvem.")

# --- TELA 1: ENTRADA E ENDEREÇAMENTO ---
if tela == "📥 Entrada e Endereçamento":
    st.subheader("📥 Recebimento e Alocação de Mercadoria")
    
    sku_input = st.text_input("Código SKU do Produto:", key="entrada_sku")
    nome_prod = st.text_input("Descrição / Nome do Produto:", key="entrada_nome")
    qtd_input = st.number_input("Quantidade de Itens:", min_value=1.0, step=1.0, value=1.0, key="entrada_qtd")
    
    if banco_configurado:
        todos_enderecos = conn.query("SELECT posicao FROM enderecos", ttl=0).to_dict(orient="records")
        movimentacoes = conn.query("SELECT posicao, tipo_movimentacao, quantidade FROM movimentacoes", ttl=0).to_dict(orient="records")
    else:
        todos_enderecos = [{"posicao": "A-01"}, {"posicao": "A-02"}]
        movimentacoes = []
    
    df_mov = pd.DataFrame(movimentacoes)
    if not df_mov.empty:
        df_mov['qtd_sinal'] = df_mov.apply(lambda r: r['quantidade'] if r['tipo_movimentacao'] == 'ENTRADA' else -r['quantidade'], axis=1)
        saldos_pos = df_mov.groupby('posicao')['qtd_sinal'].sum()
        posicoes_ocupadas = saldos_pos[saldos_pos > 0].index.tolist()
    else:
        posicoes_ocupadas = []
        
    enderecos_vazios = [e['posicao'] for e in todos_enderecos if e['posicao'] not in posicoes_ocupadas]
    
    if enderecos_vazios:
        posicao_estoque = st.selectbox("Selecione um Endereço Vazio Disponível:", enderecos_vazios, key="entrada_pos")
    else:
        st.error("🚨 Sem posições livres no mapa! Solicite ao Supervisor o cadastro de novos endereços.")
        posicao_estoque = None
        
    if st.button("Confirmar Entrada de Material", use_container_width=True) and posicao_estoque:
        if sku_input and nome_prod:
            data_hoje = datetime.now().strftime("%d/%m/%Y %H:%M")
            if banco_configurado:
                with conn.session as s:
                    s.execute(
                        "INSERT INTO movimentacoes (data_registro, sku, produto, quantidade, posicao, tipo_movimentacao, usuario) VALUES (:data, :sku, :prod, :qtd, :pos, 'ENTRADA', :user)",
                        {"data": data_hoje, "sku": sku_input, "prod": nome_prod, "qtd": qtd_input, "pos": posicao_estoque, "user": st.session_state["usuario_atual"]}
                    )
                    s.commit()
            st.success(f"Sucesso! {qtd_input} unidades alocadas na posição {posicao_estoque}.")
            st.rerun()
        else:
            st.warning("Preencha todos os campos do produto para registrar.")

# --- TELA 2: SEPARAÇÃO / PICKING ---
elif tela == "📤 Separação e Baixa":
    st.subheader("📤 Processar Separação de Pedidos (Picking)")
    
    if banco_configurado:
        movimentacoes = conn.query("SELECT sku, produto, posicao, tipo_movimentacao, quantidade FROM movimentacoes", ttl=0).to_dict(orient="records")
    else:
        movimentacoes = []
        
    df_mov = pd.DataFrame(movimentacoes)
    
    if df_mov.empty:
        st.info("Nenhuma mercadoria com saldo disponível no armazém para dar baixa.")
    else:
        df_mov['qtd_sinal'] = df_mov.apply(lambda r: r['quantidade'] if r['tipo_movimentacao'] == 'ENTRADA' else -r['quantidade'], axis=1)
        saldos = df_mov.groupby(['sku', 'produto', 'posicao'])['qtd_sinal'].sum().reset_index()
        itens_disponiveis = saldos[saldos['qtd_sinal'] > 0].to_dict('records')
        
        if not itens_disponiveis:
            st.info("Nenhuma mercadoria com saldo disponível no armazém para dar baixa.")
        else:
            opcoes_selecao = [f"SKU: {i['sku']} | Item: {i['produto']} | Posição: {i['posicao']} (Saldo: {int(i['qtd_sinal'])})" for i in itens_disponiveis]
            item_selecionado = st.selectbox("Selecione a carga alvo para o Picking:", opcoes_selecao, key="baixa_selecao")
            
            indice = opcoes_selecao.index(item_selecionado)
            alvo = itens_disponiveis[indice]
            
            qtd_retirar = st.number_input("Quantidade a Retirar:", min_value=1.0, max_value=float(alvo['qtd_sinal']), step=1.0, value=1.0, key="baixa_qtd")
            
            if st.button("Confirmar Retirada e Expedição", use_container_width=True):
                data_hoje = datetime.now().strftime("%d/%m/%Y %H:%M")
                if banco_configurado:
                    with conn.session as s:
                        s.execute(
                            "INSERT INTO movimentacoes (data_registro, sku, produto, quantidade, posicao, tipo_movimentacao, usuario) VALUES (:data, :sku, :prod, :qtd, :pos, 'SAÍDA', :user)",
                            {"data": data_hoje, "sku": alvo['sku'], "prod": alvo['produto'], "qtd": qtd_retirar, "pos": alvo['posicao'], "user": st.session_state["usuario_atual"]}
                        )
                        s.commit()
                st.success(f"Picking concluído! {qtd_retirar} unidades retiradas de {alvo['posicao']}.")
                st.rerun()

# --- TELA 3: INVENTÁRIO LOGÍSTICO (COM DOWNLOAD EM EXCEL) ---
elif tela == "📋 Posição de Inventário Real" and cargo_do_usuario == "Supervisor":
    st.subheader("📋 Relatório Logístico de Saldos e Ocupação (Kardex)")
    
    if banco_configurado:
        movimentacoes = conn.query("SELECT sku, produto, posicao, tipo_movimentacao, quantidade FROM movimentacoes", ttl=0).to_dict(orient="records")
    else:
        movimentacoes = []
        
    df_mov = pd.DataFrame(movimentacoes)
    
    if df_mov.empty:
        df_ocupado = pd.DataFrame(columns=['Código SKU', 'Descrição do Item', 'Endereço', 'Saldo'])
    else:
        df_mov['qtd_sinal'] = df_mov.apply(lambda r: r['quantidade'] if r['tipo_movimentacao'] == 'ENTRADA' else -r['quantidade'], axis=1)
        saldos = df_mov.groupby(['sku', 'produto', 'posicao'])['qtd_sinal'].sum().reset_index()
        df_ocupado = saldos[saldos['qtd_sinal'] > 0]



