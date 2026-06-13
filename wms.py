import streamlit as st
from datetime import datetime
import pandas as pd
import io
import hashlib
import hmac
import json
import os

# Configuração da página profissional e responsiva
st.set_page_config(page_title="WMS Logística Pro", layout="wide", page_icon="📦")

# --- BANCO DE DADOS LOCAL EM ARQUIVO JSON AUTO-GERENCIADO ---
# Cria um arquivo de texto que simula um banco de dados em nuvem estável
ARQUIVO_BANCO = "wms_dados_armazenados.json"

def carregar_dados():
    if not os.path.exists(ARQUIVO_BANCO):
        # Dados iniciais caso o arquivo não exista
        dados_iniciais = {
            "usuarios": [
                {
                    "usuario": "admin",
                    "senha_hash": "63f6955df987e148e42f9ef02b7db5b3fb00234a9b6c93433a0172e7f91c9441", # hash de 334409
                    "cargo": "Supervisor"
                },
                {
                    "usuario": "operador",
                    "senha_hash": "20b411dfa428277a87e597c231713d3d82d4314e3089d79ca8474b7617b0728c", # hash de operador123
                    "cargo": "Operador"
                }
            ],
            "enderecos": [{"posicao": "PRD-01-A-01"}, {"posicao": "PRD-01-A-02"}, {"posicao": "PRD-01-B-01"}],
            "movimentacoes": []
        }
        with open(ARQUIVO_BANCO, "w", encoding="utf-8") as f:
            json.dump(dados_iniciais, f, indent=4)
        return dados_iniciais
    
    try:
        with open(ARQUIVO_BANCO, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"usuarios": [], "enderecos": [], "movimentacoes": []}

def salvar_dados(dados):
    with open(ARQUIVO_BANCO, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=4)

# Inicializa a leitura dos dados do sistema
db = carregar_dados()

# --- FUNÇÕES DE SEGURANÇA NATIVAS ---
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
        usuario_encontrado = None
        for user in db["usuarios"]:
            if user["usuario"] == u:
                usuario_encontrado = user
                break
                
        if usuario_encontrado and verificar_senha(p, usuario_encontrado["senha_hash"]):
            st.session_state["logado"] = True
            st.session_state["usuario_atual"] = u
            st.session_state["cargo_atual"] = usuario_encontrado["cargo"]
            st.success("Autenticado com sucesso!")
            st.rerun()
        else:
            st.error("Usuário ou senha incorretos.")
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

# --- TELA 1: ENTRADA E ENDEREÇAMENTO ---
if tela == "📥 Entrada e Endereçamento":
    st.subheader("📥 Recebimento e Alocação de Mercadoria")
    
    sku_input = st.text_input("Código SKU do Produto:", key="entrada_sku")
    nome_prod = st.text_input("Descrição / Nome do Produto:", key="entrada_nome")
    qtd_input = st.number_input("Quantidade de Itens:", min_value=1.0, step=1.0, value=1.0, key="entrada_qtd")
    
    todos_enderecos = db["enderecos"]
    movimentacoes = db["movimentacoes"]
    
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
            db["movimentacoes"].append({
                "data_registro": data_hoje, "sku": sku_input, "produto": nome_prod,
                "quantidade": qtd_input, "posicao": posicao_estoque, "tipo_movimentacao": "ENTRADA",
                "usuario": st.session_state["usuario_atual"]
            })
            salvar_dados(db)
            st.success(f"Sucesso! {qtd_input} unidades alocadas na posição {posicao_estoque}.")
            st.rerun()
        else:
            st.warning("Preencha todos os campos do produto para registrar.")

# --- TELA 2: SEPARAÇÃO / PICKING ---
elif tela == "📤 Separação e Baixa":
    st.subheader("📤 Processar Separação de Pedidos (Picking)")
    
    movimentacoes = db["movimentacoes"]
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
                db["movimentacoes"].append({
                    "data_registro": data_hoje, "sku": alvo['sku'], "produto": alvo['produto'],
                    "quantidade": qtd_retirar, "posicao": alvo['posicao'], "tipo_movimentacao": "SAÍDA",
                    "usuario": st.session_state["usuario_atual"]
                })
                salvar_dados(db)
                st.success(f"Picking concluído! {qtd_retirar} unidades retiradas de {alvo['posicao']}.")
                st.rerun()

# --- TELA 3: INVENTÁRIO LOGÍSTICO (COM DOWNLOAD EM EXCEL) ---
elif tela == "📋 Posição de Inventário Real" and cargo_do_usuario == "Supervisor":
    st.subheader("📋 Relatório Logístico de Saldos e Ocupação (Kardex)")
    
    movimentacoes = db["movimentacoes"]
    df_mov = pd.DataFrame(movimentacoes)
    
    if df_mov.empty:
        df_ocupado = pd.DataFrame(columns=['Código SKU', 'Descrição do Item', 'Endereço', 'Saldo'])
    else:
        df_mov['qtd_sinal'] = df_mov.apply(lambda r: r['quantidade'] if r['tipo_movimentacao'] == 'ENTRADA' else -r['quantidade'], axis=1)
        saldos = df_mov.groupby(['sku', 'produto', 'posicao'])['qtd_sinal'].sum().reset_index()
        df_ocupado = saldos[saldos['qtd_sinal'] > 0]
        df_ocupado.columns = ['Código SKU', 'Descrição do Item', 'Endereço', 'Saldo']

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df_ocupado.to_excel(writer, index=False, sheet_name='Inventario Real')
    buffer.seek(0)
    
    st.download_button(
        label="📥 Baixar Inventário em Excel (.xlsx)", data=buffer,
        file_name=f"inventario_wms_{datetime.now().strftime('%Y%m%d')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True
    )
    
    st.markdown("### 🔴 Posições Ocupadas Atualmente")
    if df_ocupado.empty:
        st.info("Nenhum saldo armazenado no momento.")
    else:
        st.dataframe(df_ocupado, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.markdown("### 🟢 Endereços Vazios (Disponíveis)")
    todos_enderecos = db["enderecos"]




