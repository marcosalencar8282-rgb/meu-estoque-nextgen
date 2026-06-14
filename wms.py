import streamlit as st
from datetime import datetime
import pandas as pd
import io
import hashlib
import json

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

# --- BANCO DE DADOS EM MEMÓRIA SEGURO ---
if "db_usuarios" not in st.session_state:
    st.session_state["db_usuarios"] = [
        {"usuario": "admin", "senha": "334409", "cargo": "Supervisor"},
        {"usuario": "operador", "senha": "operador123", "cargo": "Operador"}
    ]
if "db_enderecos" not in st.session_state:
    st.session_state["db_enderecos"] = ["A-01-01", "A-01-02", "B-01-01"]
if "db_produtos" not in st.session_state:
    st.session_state["db_produtos"] = [{"sku": "SKU001", "nome": "Produto Exemplo A"}]
if "db_movimentacoes" not in st.session_state:
    st.session_state["db_movimentacoes"] = []

# --- SESSÃO DE AUTENTICAÇÃO ---
if "logado" not in st.session_state:
    st.session_state["logado"] = False
if "usuario_atual" not in st.session_state:
    st.session_state["usuario_atual"] = ""
if "cargo_atual" not in st.session_state:
    st.session_state["cargo_atual"] = ""

if not st.session_state["logado"]:
    st.markdown("<h1 style='text-align: center; color: #003366;'>TOTVS WMS | Portal Logístico NextGen</h1>", unsafe_allow_html=True)
    st.write("<p style='text-align: center;'>Insira suas credenciais logísticas para acessar o terminal do armazém.</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col2:
        u = st.text_input("Usuário / Matrícula:", key="login_u").strip().lower()
        p = st.text_input("Senha Corporativa:", type="password", key="login_p").strip()
        
        if st.button("Entrar no Terminal", use_container_width=True):
            user_validado = None
            for user in st.session_state["db_usuarios"]:
                if user["usuario"] == u and user["senha"] == p:
                    user_validado = user
                    break
            
            if user_validado:
                st.session_state["logado"] = True
                st.session_state["usuario_atual"] = u
                st.session_state["cargo_atual"] = user_validado["cargo"]
                st.rerun()
            else:
                st.error("Acesso negado. Matrícula ou senha inválidas.")
    st.stop()

# --- PAINEL PRINCIPAL OPERACIONAL ---
st.markdown(f"<h2>📦 TOTVS WMS - Módulo de Gestão de Estoques</h2>", unsafe_allow_html=True)
st.write(f"👤 Matrícula: **{st.session_state['usuario_atual'].upper()}** | Perfil Corporativo: **{st.session_state['cargo_atual'].upper()}**")

if st.sidebar.button("🚪 Desconectar / Sair"):
    st.session_state["logado"] = False
    st.session_state["usuario_atual"] = ""
    st.session_state["cargo_atual"] = ""
    st.rerun()

st.sidebar.markdown("---")

# Processamento de Saldos Logísticos para os DataFrames
df_mov_geral = pd.DataFrame(st.session_state["db_movimentacoes"])
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

# --- 🌟 ALTERAÇÃO CRUCIAL: MENU POR CAIXA DE SELEÇÃO PROTHEUS STYLE ---
cargo = st.session_state["cargo_atual"]
opcoes_menu = ["📥 Entrada e Alocação", "📤 Separação e Baixa"]
if cargo == "Supervisor":
    opcoes_menu.extend(["📋 Kardex e Inventário", "🛠️ Gestão de Endereços", "🏷️ Gestão de Produtos", "👤 Gestão de Usuários"])

# Usando selectbox em vez de radio para forçar a seleção do primeiro item automaticamente
tela = st.sidebar.selectbox("Selecione o Módulo Operacional:", opcoes_menu, index=0, key="menu_navegacao_principal")
st.markdown("---")

# --- TELA 1: ENTRADA E ALOCAÇÃO ---
if tela == "📥 Entrada e Alocação":
    st.subheader("📥 Recebimento de Mercadorias e Endereçamento")
    skus_cadastrados = [prod["sku"] for prod in st.session_state["db_produtos"]]
    
    if not skus_cadastrados:
        st.warning("⚠️ Nenhum produto cadastrado no catálogo atualmente.")
    else:
        with st.form("form_entrada"):
            sku_sel = st.selectbox("Selecione o SKU do Produto:", skus_cadastrados, key="t1_sku")
            qtd = st.number_input("Quantidade de Volumes:", min_value=1.0, step=1.0, value=1.0, key="t1_qtd")
            
            ocupados = []
            if not df_mov_geral.empty:
                saldos_pos = df_mov_geral.groupby('posicao')['qtd_sinal'].sum()
                ocupados = saldos_pos[saldos_pos > 0].index.tolist()
                
            livres = [pos for pos in st.session_state["db_enderecos"] if pos not in ocupados]
            
            if livres:
                pos_sel = st.selectbox("Selecione a Posição Física Disponível:", livres, key="t1_pos")
                btn_envio = st.form_submit_button("Confirmar Entrada (MATA250)", use_container_width=True)
                if btn_envio:
                    desc_sel = next(prod["nome"] for prod in st.session_state["db_produtos"] if prod["sku"] == sku_sel)
                    st.session_state["db_movimentacoes"].append({
                        "data": datetime.now().strftime("%d/%m/%Y %H:%M"), "sku": sku_sel, "produto": desc_sel,
                        "qtd": qtd, "posicao": pos_sel, "tipo": "ENTRADA", "operador": st.session_state["usuario_atual"]
                    })
                    st.success(f"Sucesso! Volumes alocados na posição {pos_sel}.")
                    st.rerun()
            else:
                st.error("🚨 Sem posições de estocagem livres disponíveis.")

# --- TELA 2: SEPARAÇÃO E BAIXA ---
if tela == "📤 Separação e Baixa":
    st.subheader("📤 Processar Separação de Pedidos (Picking)")
    if df_mov_geral.empty:
        st.info("Nenhum material estocado no armazém atualmente.")
    else:
        disponiveis = saldos_calculados[saldos_calculados['qtd_sinal'] > 0].to_dict('records')
        if not disponiveis:
            st.info("Nenhum saldo disponível para separação.")
        else:
            with st.form("form_picking"):
                opcoes = [f"SKU: {i['sku']} | {i['produto']} | Posição: {i['posicao']} (Saldo: {int(i['qtd_sinal'])})" for i in disponiveis]
                item_sel = st.selectbox("Selecione a Carga Alvo para Picking:", opcoes, key="t2_item")
                qtd_retirar = st.number_input("Quantidade a Retirar:", min_value=1.0, step=1.0, value=1.0, key="t2_qtd")
                btn_picking = st.form_submit_button("Confirmar Saída (MATA260)", use_container_width=True)
                
                if btn_picking:
                    indice = opcoes.index(item_sel)
                    alvo = disponiveis[indice]
                    if qtd_retirar > float(alvo['qtd_sinal']):
                        st.error("Quantidade superior ao saldo disponível!")
                    else:
                        st.session_state["db_movimentacoes"].append({
                            "data": datetime.now().strftime("%d/%m/%Y %H:%M"), "sku": alvo['sku'], "produto": alvo['produto'],
                            "qtd": qtd_retirar, "posicao": alvo['posicao'], "tipo": "SAÍDA", "operador": st.session_state["usuario_atual"]
                        })
                        st.success("Picking processado com sucesso!")
                        st.rerun()

# --- TELA 3: KARDEX E INVENTÁRIO ---
if tela == "📋 Kardex e Inventário":
    st.subheader("📋 Relatório Kardex de Posições e Ocupação Real")
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df_inventario_real.to_excel(writer, index=False, sheet_name='Inventário Real')
    buffer.seek(0)
    st.download_button(label="📥 Exportar Planilha para Excel (.xlsx)", data=buffer, file_name="inventario.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key="t3_btn")
    
    t1, t2 = st.tabs(["📊 Saldos em Estoque", "🕵️ Histórico de Logs"])
    with t1:
        if df_inventario_real.empty:
            st.info("Nenhum material registrado em estoque.")
        else:
            st.dataframe(df_inventario_real, use_container_width=True, hide_index=True)
    with t2:
        if df_mov_geral.empty:
            st.info("Nenhuma movimentação realizada.")
        else:
            df_logs = df_mov_geral[['data', 'operador', 'tipo', 'sku', 'produto', 'qtd', 'posicao']].copy()
            df_logs.columns = ['Data/Hora', 'Operador Responsável', 'Operação', 'SKU', 'Produto', 'Qtd', 'Posição']
            st.dataframe(df_logs, use_container_width=True, hide_index=True)

# --- TELA 4: GESTÃO DE ENDEREÇOS ---
if tela == "🛠️ Gestão de Endereços":
            


