import streamlit as st
from datetime import datetime
import pandas as pd
import io
import hashlib
import hmac
import json
import os

# Configuração da página profissional e responsiva
st.set_page_config(page_title="WMS NextGen | Protheus Style", layout="wide", page_icon="📦")

# --- CUSTOMIZAÇÃO VISUAL ESTILO PROTHEUS ---
st.markdown("""
    <style>
    .stApp { background-color: #F4F6F9; }
    h1, h2, h3 { color: #003366 !important; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; font-weight: 700; }
    div.stButton > button:first-child {
        background-color: #003366; color: white; border-radius: 4px; border: none;
        padding: 0.5rem 1rem; font-weight: bold; transition: all 0.3s ease;
    }
    div.stButton > button:first-child:hover { background-color: #0055a5; color: white; }
    div[data-testid="stMetricValue"] { color: #003366; font-size: 24px; font-weight: bold; }
    .stTextInput>div>div>input { background-color: #FFFFFF; border: 1px solid #CCD4DC; border-radius: 4px; }
    </style>
""", unsafe_allow_html=True)

# --- NOVO ARQUIVO DE BANCO DE DADOS ATUALIZADO (V3) ---
ARQUIVO_BANCO = "wms_database_v3.json"

def gerar_hash_limpo(senha):
    return hashlib.sha256(senha.encode('utf-8')).hexdigest()

def carregar_banco():
    if not os.path.exists(ARQUIVO_BANCO):
        dados_iniciais = {
            "usuarios": [
                {"usuario": "admin", "senha_hash": gerar_hash_limpo("334409"), "cargo": "Supervisor"},
                {"usuario": "operador", "senha_hash": gerar_hash_limpo("operador123"), "cargo": "Operador"}
            ],
            "enderecos": [{"posicao": "A-01-01"}, {"posicao": "A-01-02"}, {"posicao": "B-01-01"}],
            "produtos_cadastro": [{"sku": "SKU001", "nome": "Produto Exemplo A"}],
            "movimentacoes": []
        }
        with open(ARQUIVO_BANCO, "w", encoding="utf-8") as f:
            json.dump(dados_iniciais, f, indent=4)
        return dados_iniciais
    try:
        with open(ARQUIVO_BANCO, "r", encoding="utf-8") as f:
            conteudo = json.load(f)
            if "usuarios" not in conteudo: conteudo["usuarios"] = []
            if "produtos_cadastro" not in conteudo: conteudo["produtos_cadastro"] = []
            if "enderecos" not in conteudo: conteudo["enderecos"] = []
            if "movimentacoes" not in conteudo: conteudo["movimentacoes"] = []
            return conteudo
    except Exception:
        return {
            "usuarios": [{"usuario": "admin", "senha_hash": gerar_hash_limpo("334409"), "cargo": "Supervisor"}],
            "enderecos": [{"posicao": "A-01-01"}], "produtos_cadastro": [], "movimentacoes": []
        }

def salvar_banco(dados):
    with open(ARQUIVO_BANCO, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=4)

db = carregar_banco()

# --- PORTAL DE ACESSO ---
if "logado" not in st.session_state:
    st.session_state["logado"] = False
if "usuario_atual" not in st.session_state:
    st.session_state["usuario_atual"] = ""
if "cargo_atual" not in st.session_state:
    st.session_state["cargo_atual"] = ""

if not st.session_state["logado"]:
    st.markdown("<h1 style='text-align: center; color: #003366;'>TOTVS WMS | Portal Logístico NextGen</h1>", unsafe_allow_html=True)
    st.write("<p style='text-align: center;'>Insira suas credenciais logísticas para acessar o terminal do armazém.</p>", unsafe_allow_html=True)
    
    # 🌟 CORREÇÃO TÉCNICA: Passando o número 3 para criar as três colunas de layout
    col1, col2, col3 = st.columns(3)
    with col2:
        with st.container(border=True):
            u = st.text_input("Usuário / Matrícula:", key="login_u").strip().lower()
            p = st.text_input("Senha Corporativa:", type="password", key="login_p").strip()
            
            if st.button("Entrar no Terminal", use_container_width=True):
                user_validado = next((user for user in db.get("usuarios", []) if user["usuario"] == u), None)
                if user_validado and hmac.compare_digest(gerar_hash_limpo(p), user_validado["senha_hash"]):
                    st.session_state["logado"] = True
                    st.session_state["usuario_atual"] = u
                    st.session_state["cargo_atual"] = user_validado["cargo"]
                    st.rerun()
                else:
                    st.error("Acesso negado. Matrícula ou senha inválidas.")
    st.stop()

# --- PAINEL PRINCIPAL OPERACIONAL ---
st.markdown(f"<h2 style='margin-bottom: 0px;'>📦 TOTVS WMS - Módulo de Gestão de Estoques</h2>", unsafe_allow_html=True)
st.write(f"👤 Matrícula: **{st.session_state['usuario_atual'].upper()}** | Perfil Corporativo: **{st.session_state['cargo_atual'].upper()}**")

if st.sidebar.button("🚪 Desconectar / Sair"):
    st.session_state["logado"] = False
    st.session_state["usuario_atual"] = ""
    st.session_state["cargo_atual"] = ""
    st.rerun()

st.sidebar.markdown("---")

cargo = st.session_state["cargo_atual"]
opcoes_menu = ["📥 Recebimento e Alocação", "📤 Separação e Baixa"]
if cargo == "Supervisor":
    opcoes_menu.extend(["📋 Kardex e Inventário", "🛠️ Cadastro de Endereços", "🏷️ Cadastro de Produtos", "👤 Gestão de Usuários"])

menu = st.sidebar.radio("Navegação do Sistema:", opcoes_menu)
st.markdown("---")

# --- PROCESSO LINEAR DE DATA FRAMES ---
movimentacoes_lista = db.get("movimentacoes", [])
df_mov_geral = pd.DataFrame(movimentacoes_lista)

if df_mov_geral.empty:
    df_inventario_real = pd.DataFrame(columns=['Código SKU', 'Descrição do Produto', 'Posição Física', 'Saldo Atual'])
else:
    df_mov_geral['qtd_sinal'] = df_mov_geral.apply(lambda r: r['qtd'] if r['tipo'] == 'ENTRADA' else -r['qtd'], axis=1)
    saldos_calculados = df_mov_geral.groupby(['sku', 'produto', 'posicao'])['qtd_sinal'].sum().reset_index()
    df_inventario_real = saldos_calculados[saldos_calculados['qtd_sinal'] > 0]
    if not df_inventario_real.empty:
        df_inventario_real.columns = ['Código SKU', 'Descrição do Produto', 'Posição Física', 'Saldo Atual']
    else:
        df_inventario_real = pd.DataFrame(columns=['Código SKU', 'Descrição do Produto', 'Posição Física', 'Saldo Atual'])

# --- TELA 1: RECEBIMENTO E ALOCAÇÃO ---
if menu == "📥 Recebimento e Alocação":
    st.subheader("📥 Recebimento de Mercadorias e Endereçamento Direto")
    
    skus_cadastrados = [prod["sku"] for prod in db.get("produtos_cadastro", [])]
    if not skus_cadastrados:
        st.warning("⚠️ Nenhum produto cadastrado no sistema ainda. Acesse a aba 'Cadastro de Produtos' primeiro.")
    else:
        sku_sel = st.selectbox("Selecione o SKU do Produto:", skus_cadastrados)
        desc_sel = next(prod["nome"] for prod in db["produtos_cadastro"] if prod["sku"] == sku_sel)
        st.info(f"📋 Descrição Automática: **{desc_sel}**")
        
        qtd = st.number_input("Quantidade de Volumes:", min_value=1.0, step=1.0, value=1.0)
        
        if not df_mov_geral.empty:
            saldos_pos = df_mov_geral.groupby('posicao')['qtd_sinal'].sum()
            ocupados = saldos_pos[saldos_pos > 0].index.tolist()
        else:
            ocupados = []
            
        livres = [e["posicao"] for e in db.get("enderecos", []) if e["posicao"] not in ocupados]
        
        if livres:
            pos_sel = st.selectbox("Selecione a Posição Física Disponível:", livres)
            if st.button("Confirmar Entrada (MATA250)", use_container_width=True):
                db["movimentacoes"].append({
                    "data": datetime.now().strftime("%d/%m/%Y %H:%M"), "sku": sku_sel, "produto": desc_sel,
                    "qtd": qtd, "posicao": pos_sel, "tipo": "ENTRADA", "operador": st.session_state["usuario_atual"]
                })
                salvar_banco(db)
                st.success(f"Alocação concluída com sucesso na posição {pos_sel}!")
                st.rerun()
        else:
            st.error("🚨 Sem posições de estocagem livres. Cadastre novos endereços primeiro.")

# --- TELA 2: SEPARAÇÃO E BAIXA (PICKING) ---
elif menu == "📤 Separação e Baixa":
    st.subheader("📤 Separação de Pedidos e Picking de Expedição")
    
    if df_mov_geral.empty:
        st.info("Nenhum material estocado no armazém atualmente.")
    else:
        disponiveis = saldos_calculados[saldos_calculados['qtd_sinal'] > 0].to_dict('records')
        
        if not disponiveis:
            st.info("Nenhum saldo físico disponível para separação.")
        else:
            opcoes = [f"SKU: {i['sku']} | {i['produto']} | Posição: {i['posicao']} (Saldo: {int(i['qtd_sinal'])})" for i in disponiveis]
            item_sel = st.selectbox("Selecione a Carga Alvo para Baixa:", opcoes)
            
            indice = opcoes.index(item_sel)
            alvo = disponiveis[indice]
            
            qtd_retirar = st.number_input("Quantidade a Retirar:", min_value=1.0, max_value=float(alvo['qtd_sinal']), step=1.0)
            
            if st.button("Confirmar Saída (MATA260)", use_container_width=True):
                db["movimentacoes"].append({
                    "data": datetime.now().strftime("%d/%m/%Y %H:%M"), "sku": alvo['sku'], "produto": alvo['produto'],
                    "qtd": qtd_retirar, "posicao": alvo['posicao'], "tipo": "SAÍDA", "operador": st.session_state["usuario_atual"]
                })
                salvar_banco(db)
                st.success(f"Picking processado! {qtd_retirar} volumes expedidos de {alvo['posicao']}.")
                st.rerun()

# --- TELA 3: KARDEX E INVENTÁRIO ---
elif menu == "📋 Kardex e Inventário" and cargo == "Supervisor":
    st.subheader("📋 Relatório Kardex de Posições e Ocupação Real")
    
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df_inventario_real.to_excel(writer, index=False, sheet_name='Inventário Real')
    buffer.seek(0)






