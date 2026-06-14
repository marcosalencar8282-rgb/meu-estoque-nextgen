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

# Processamento de Saldos para os DataFrames
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

# --- INTERFACE CENTRAL COM ABAS SEPARADAS INDIVIDUALMENTE ---
cargo = st.session_state["cargo_atual"]

if cargo == "Supervisor":
    aba1, aba2, aba3, aba4, aba5, aba6 = st.tabs([
        "📥 Entrada e Alocação", "📤 Separação e Baixa", "📋 Kardex e Inventário", 
        "🛠️ Gestão de Endereços", "🏷️ Gestão de Produtos", "👤 Gestão de Usuários"
    ])
    
    with aba1:
        st.write("### 📥 Recebimento de Mercadorias")
        skus_cadastrados = [prod["sku"] for prod in st.session_state["db_produtos"]]
        if not skus_cadastrados:
            st.warning("Nenhum produto cadastrado no catálogo atualmente.")
        else:
            sku_sel = st.selectbox("Selecione o SKU:", skus_cadastrados, key="aba1_sku")
            desc_sel = next(prod["nome"] for prod in st.session_state["db_produtos"] if prod["sku"] == sku_sel)
            st.info(f"Produto selecionado: **{desc_sel}**")
            qtd = st.number_input("Quantidade de Volumes:", min_value=1.0, step=1.0, value=1.0, key="aba1_qtd")
            ocupados = []
            if not df_mov_geral.empty:
                saldos_pos = df_mov_geral.groupby('posicao')['qtd_sinal'].sum()
                ocupados = saldos_pos[saldos_pos > 0].index.tolist()
            livres = [pos for pos in st.session_state["db_enderecos"] if pos not in ocupados]
            if livres:
                pos_sel = st.selectbox("Selecione a Posição Física:", livres, key="aba1_pos")
                if st.button("Confirmar Entrada (MATA250)", key="aba1_btn", use_container_width=True):
                    st.session_state["db_movimentacoes"].append({
                        "data": datetime.now().strftime("%d/%m/%Y %H:%M"), "sku": sku_sel, "produto": desc_sel,
                        "qtd": qtd, "posicao": pos_sel, "tipo": "ENTRADA", "operador": st.session_state["usuario_atual"]
                    })
                    st.success(f"Alocação concluída na posição {pos_sel}!")
                    st.rerun()
            else:
                st.error("Sem posições livres disponíveis no armazém.")

    with aba2:
        st.write("### 📤 Separação de Pedidos (Picking)")
        if df_mov_geral.empty:
            st.info("Nenhum material estocado no armazém atualmente.")
        else:
            disponiveis = saldos_calculados[saldos_calculados['qtd_sinal'] > 0].to_dict('records')
            if not disponiveis:
                st.info("Nenhum saldo disponível para separação.")
            else:
                opcoes = [f"SKU: {i['sku']} | {i['produto']} | Posição: {i['posicao']} (Saldo: {int(i['qtd_sinal'])})" for i in disponiveis]
                item_sel = st.selectbox("Selecione a Carga Alvo:", opcoes, key="aba2_item")
                indice = opcoes.index(item_sel)
                alvo = disponiveis[indice]
                qtd_retirar = st.number_input("Quantidade a Retirar:", min_value=1.0, max_value=float(alvo['qtd_sinal']), step=1.0, key="aba2_qtd")
                if st.button("Confirmar Saída (MATA260)", key="aba2_btn", use_container_width=True):
                    st.session_state["db_movimentacoes"].append({
                        "data": datetime.now().strftime("%d/%m/%Y %H:%M"), "sku": alvo['sku'], "produto": alvo['produto'],
                        "qtd": qtd_retirar, "posicao": alvo['posicao'], "tipo": "SAÍDA", "operador": st.session_state["usuario_atual"]
                    })
                    st.success("Picking processado com sucesso!")
                    st.rerun()

    with aba3:
        st.write("### 📋 Kardex e Inventário")
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df_inventario_real.to_excel(writer, index=False, sheet_name='Inventário Real')
        buffer.seek(0)
        st.download_button(label="📥 Exportar Planilha para Excel (.xlsx)", data=buffer, file_name="inventario.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key="aba3_btn")
        st.write("#### Saldos Físicos")
        st.dataframe(df_inventario_real, use_container_width=True, hide_index=True)

    with aba4:
        st.write("### 🛠️ Gestão de Endereços Físicos")
        col_cad_end, col_exc_end = st.columns(2)
        with col_cad_end:
            st.write("#### 📍 Adicionar Novo Endereço")
            nova_pos = st.text_input("Identificação do Endereço (Ex: EST-01-A-03):", key="aba4_txt").strip().upper()
            if st.button("Gravar Endereço", key="aba4_btn", use_container_width=True):
                if nova_pos:
                    if nova_pos in st.session_state["db_enderecos"]:
                        st.error("Esta posição já existe no mapa.")
                    else:
                        st.session_state["db_enderecos"].append(nova_pos)
                        st.success(f"Posição {nova_pos} gravada com sucesso!")
                        st.rerun()
        with col_exc_end:
            st.write("#### 🗑️ Remover Endereço do Mapa")
            if not st.session_state["db_enderecos"]:
                st.info("Nenhum endereço disponível para exclusão.")
            else:
                end_para_excluir = st.selectbox("Selecione o endereço para remover:", st.session_state["db_enderecos"], key="aba4_sel_exc")
                com_saldo = []
                if not df_inventario_real.empty:
                    com_saldo = df_inventario_real['Posição Física'].tolist()
                if st.button("🔴 Excluir Endereço Definitivamente", key="aba4_btn_exc", use_container_width=True):


