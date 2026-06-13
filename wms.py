import streamlit as st
from st_supabase_connection import SupabaseConnection
from datetime import datetime
import pandas as pd
import bcrypt
import io

# Configuração da página profissional e responsiva
st.set_page_config(page_title="WMS Logística Pro", layout="wide", page_icon="📦")

# --- CONEXÃO COM O BANCO DE DADOS EM NUVEM ---
# O Streamlit gerencia a conexão automaticamente através dos Secrets
conn = st.connection("supabase", type=SupabaseConnection)

# --- FUNÇÕES DE SEGURANÇA E USUÁRIO ---
def gerar_senha_hash(senha):
    return bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verificar_senha(senha, senha_hash):
    return bcrypt.checkpw(senha.encode('utf-8'), senha_hash.encode('utf-8'))

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
        # Busca usuário no banco em nuvem
        resposta = conn.table("usuarios").select("senha_hash, cargo").eq("usuario", u).execute()
        
        if resposta.data and len(resposta.data) > 0:
            dados_usuario = resposta.data[0]
            if verificar_senha(p, dados_usuario["senha_hash"]):
                st.session_state["logado"] = True
                st.session_state["usuario_atual"] = u
                st.session_state["cargo_atual"] = dados_usuario["cargo"]
                st.success("Autenticado com sucesso!")
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos.")
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
    
    # Lógica em nuvem para buscar endereços vazios
    todos_enderecos = conn.table("enderecos").select("posicao").execute().data
    movimentacoes = conn.table("movimentacoes").select("posicao, tipo_movimentacao, quantidade").execute().data
    
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
            conn.table("movimentacoes").insert({
                "data_registro": data_hoje, "sku": sku_input, "produto": nome_prod,
                "quantidade": qtd_input, "posicao": posicao_estoque, "tipo_movimentacao": "ENTRADA",
                "usuario": st.session_state["usuario_atual"]
            }).execute()
            st.success(f"Sucesso! {qtd_input} unidades alocadas na posição {posicao_estoque}.")
            st.rerun()
        else:
            st.warning("Preencha todos os campos do produto para registrar.")

# --- TELA 2: SEPARAÇÃO / PICKING ---
elif tela == "📤 Separação e Baixa":
    st.subheader("📤 Processar Separação de Pedidos (Picking)")
    
    movimentacoes = conn.table("movimentacoes").select("sku, produto, posicao, tipo_movimentacao, quantidade").execute().data
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
                conn.table("movimentacoes").insert({
                    "data_registro": data_hoje, "sku": alvo['sku'], "produto": alvo['produto'],
                    "quantidade": qtd_retirar, "posicao": alvo['posicao'], "tipo_movimentacao": "SAÍDA",
                    "usuario": st.session_state["usuario_atual"]
                }).execute()
                st.success(f"Picking concluído! {qtd_retirar} unidades retiradas de {alvo['posicao']}.")
                st.rerun()

# --- TELA 3: INVENTÁRIO LOGÍSTICO (COM DOWNLOAD EM EXCEL) ---
elif tela == "📋 Posição de Inventário Real" and cargo_do_usuario == "Supervisor":
    st.subheader("📋 Relatório Logístico de Saldos e Ocupação (Kardex)")
    
    movimentacoes = conn.table("movimentacoes").select("sku, produto, posicao, tipo_movimentacao, quantidade").execute().data
    df_mov = pd.DataFrame(movimentacoes)
    
    if df_mov.empty:
        df_ocupado = pd.DataFrame(columns=['Código SKU', 'Descrição do Item', 'Endereço', 'Saldo'])
    else:
        df_mov['qtd_sinal'] = df_mov.apply(lambda r: r['quantidade'] if r['tipo_movimentacao'] == 'ENTRADA' else -r['quantidade'], axis=1)
        saldos = df_mov.groupby(['sku', 'produto', 'posicao'])['qtd_sinal'].sum().reset_index()
        df_ocupado = saldos[saldos['qtd_sinal'] > 0].rename(columns={'sku': 'Código SKU', 'produto': 'Descrição do Item', 'posicao': 'Endereço', 'qtd_sinal': 'Saldo'})

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
    todos_enderecos = conn.table("enderecos").select("posicao").execute().data
    posicoes_ocupadas = df_ocupado['Endereço'].tolist() if not df_ocupado.empty else []
    df_livres = pd.DataFrame([e for e in todos_enderecos if e['posicao'] not in posicoes_ocupadas]).rename(columns={'posicao': 'Endereço Livre'})
    
    if df_livres.empty:
        st.warning("Todos os endereços cadastrados possuem saldo ativo.")
    else:
        st.dataframe(df_livres, use_container_width=True, hide_index=True)

# --- TELA 4: HISTÓRICO DE AUDITORIA ---
elif tela == "🕵️ Histórico de Auditoria" and cargo_do_usuario == "Supervisor":
    st.subheader("🕵️ Linha do Tempo e Log de Auditoria")
    
    logs = conn.table("movimentacoes").select("data_registro, usuario, tipo_movimentacao, sku, produto, quantidade, posicao").execute().data
    df_logs = pd.DataFrame(logs)
    
    if df_logs.empty:
        st.info("Nenhuma movimentação registrada no histórico.")
    else:



