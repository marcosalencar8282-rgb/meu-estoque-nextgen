import streamlit as st
import pandas as pd
from datetime import datetime
import os

# Configuração inicial obrigatória
st.set_page_config(page_title="WMS - Endereçamento de Estoque Livre", layout="wide")

# ==========================================
# SISTEMA DE BANCO DE DADOS PERSISTENTE (JSON)
# ==========================================
def carregar_dados():
    if 'users' not in st.session_state:
        st.session_state.users = {
            'admin': {'password': '123', 'profile': 'Administrador', 'active': True},
            'almoxarife': {'password': '123', 'profile': 'Almoxarife', 'active': True},
            'conferente': {'password': '123', 'profile': 'Conferente', 'active': True},
            'consulta': {'password': '123', 'profile': 'Consulta', 'active': True}
        }

    if os.path.exists('wms_inventario.json'):
        try:
            st.session_state.inventory = pd.read_json('wms_inventario.json')
        except Exception:
            st.session_state.inventory = pd.DataFrame(columns=['Endereço', 'Código Produto', 'Descrição', 'Quantidade', 'Lote', 'Última Atualização'])
    else:
        st.session_state.inventory = pd.DataFrame(columns=['Endereço', 'Código Produto', 'Descrição', 'Quantidade', 'Lote', 'Última Atualização'])

    if st.session_state.inventory.empty:
        st.session_state.inventory = pd.DataFrame(columns=['Endereço', 'Código Produto', 'Descrição', 'Quantidade', 'Lote', 'Última Atualização'])

    if os.path.exists('wms_movimentacoes.json'):
        try:
            st.session_state.movements = pd.read_json('wms_movimentacoes.json')
        except Exception:
            st.session_state.movements = pd.DataFrame(columns=['Tipo', 'Endereço Origem', 'Endereço Destino', 'Produto', 'Quantidade', 'Data Hora', 'Operador'])
    else:
        st.session_state.movements = pd.DataFrame(columns=['Tipo', 'Endereço Origem', 'Endereço Destino', 'Produto', 'Quantidade', 'Data Hora', 'Operador'])

    if os.path.exists('wms_auditoria.json'):
        try:
            st.session_state.auditory = pd.read_json('wms_auditoria.json')
        except Exception:
            st.session_state.auditory = pd.DataFrame(columns=['Usuário', 'Ação', 'Registro', 'Data Hora'])
    else:
        st.session_state.auditory = pd.DataFrame(columns=['Usuário', 'Ação', 'Registro', 'Data Hora'])

    if 'config' not in st.session_state:
        st.session_state.config = {'Empresa': 'WMS Endereçamento S/A'}

def salvar_dados():
    st.session_state.inventory.to_json('wms_inventario.json', orient='records', indent=4)
    st.session_state.movements.to_json('wms_movimentacoes.json', orient='records', indent=4)
    st.session_state.auditory.to_json('wms_auditoria.json', orient='records', indent=4)

carregar_dados()

def registrar_auditoria(acao, registro):
    usuario_atual = st.session_state.get('user', 'Sistema')
    novo_log = pd.DataFrame([{
        'Usuário': usuario_atual, 'Ação': acao, 'Registro': registro,
        'Data Hora': datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    }])
    st.session_state.auditory = pd.concat([st.session_state.auditory, novo_log], ignore_index=True)
    salvar_dados()

def validar_perfil(perfis_permitidos):
    if 'user' not in st.session_state:
        return False
    perfil_usuario = st.session_state.users[st.session_state.user]['profile']
    return perfil_usuario in perfis_permitidos or perfil_usuario == 'Administrador'

# ==========================================
# TELA DE LOGIN
# ==========================================
if 'user' not in st.session_state:
    st.subheader("🔑 Login do Sistema de Endereçamento (WMS)")
    usuario_input = st.text_input("Usuário", key="usr")
    senha_input = st.text_input("Senha", type="password", key="pwd")
    
    if st.button("Entrar no Sistema", type="primary"):
        if usuario_input in st.session_state.users and st.session_state.users[usuario_input]['password'] == senha_input:
            if st.session_state.users[usuario_input]['active']:
                st.session_state.user = usuario_input
                registrar_auditoria("Login efetuado", "Sessão")
                st.rerun()
            else:
                st.error("Acesso bloqueado: Usuário Inativo.")
        else:
            st.error("Credenciais incorretas.")
else:
    st.sidebar.write(f"🏢 **{st.session_state.config['Empresa']}**")
    st.sidebar.write(f"👤 `{st.session_state.user}` ({st.session_state.users[st.session_state.user]['profile']})")
    if st.sidebar.button("Efetuar Logout / Sair"):
        registrar_auditoria("Logout efetuado", "Sessão")
        del st.session_state.user
        st.rerun()
        
    st.sidebar.divider()
    opcao_menu = st.sidebar.radio(
        "Módulos WMS", 
        ["Visão Geral do Estoque", "Entrada (Armazenagem)", "Movimentação Interna", "Saída (Picking)", "Auditoria"]
    )
    
    # 1. Visão Geral do Estoque
    if opcao_menu == "Visão Geral do Estoque":
        st.title("📊 Visão Geral e Posições Ocupadas")
        
        total_posicoes_ocupadas = len(st.session_state.inventory['Endereço'].unique())
        total_itens = int(st.session_state.inventory['Quantidade'].sum()) if not st.session_state.inventory.empty else 0
        
        c1, c2 = st.columns(2)
        c1.metric("Posições Ocupadas no Momento 📥", total_posicoes_ocupadas)
        c2.metric("Total de Peças/Volumes em Estoque 📦", total_itens)
        
        st.subheader("📍 Filtro de Inventário")
        busca = st.text_input("Filtrar por Produto ou Código do Endereço").upper()
        
        df_exibicao = st.session_state.inventory.copy()
        if busca and not df_exibicao.empty:
            df_exibicao = df_exibicao[
                df_exibicao['Endereço'].astype(str).str.upper().str.contains(busca) | 
                df_exibicao['Código Produto'].astype(str).str.upper().str.contains(busca) | 
                df_exibicao['Descrição'].astype(str).str.upper().str.contains(busca)
            ]
            
        st.dataframe(df_exibicao, use_container_width=True)

    # 2. Entrada (Armazenagem)
    elif opcao_menu == "Entrada (Armazenagem)":
        st.title("📥 Guardar Produto (Armazenagem Livre)")
        if not validar_perfil(['Almoxarife', 'Conferente']):
            st.error("Acesso negado."); st.stop()
            
        with st.form("armazenagem"):
            st.info("Digite abaixo a identificação do endereço onde o produto está sendo colocado.")
            endereco_destino = st.text_input("Código do Endereço (Ex: RUA-A-01)").upper().strip()
            cod_prod = st.text_input("Código do Produto")
            desc_prod = st.text_input("Descrição do Produto")
            qtd = st.number_input("Quantidade", min_value=1, value=1)
            lote = st.text_input("Lote / Validade", value="N/A")
            
            if st.form_submit_button("Confirmar Armazenagem"):
                if endereco_destino and cod_prod and desc_prod:
                    # Verifica se o endereço já possui esse produto para somar, ou cria nova linha
                    filtro_existente = (st.session_state.inventory['Endereço'] == endereco_destino) & (st.session_state.inventory['Código Produto'] == cod_prod) & (st.session_state.inventory['Lote'] == lote)
                    
                    if not st.session_state.inventory.empty and filtro_existente.any():
                        st.session_state.inventory.loc[filtro_existente, 'Quantidade'] += qtd
                        st.session_state.inventory.loc[filtro_existente, 'Última Atualização'] = datetime.now().strftime('%d/%m/%Y %H:%M')
                    else:
                        nova_alocacao = pd.DataFrame([{'Endereço': endereco_destino, 'Código Produto': cod_prod, 'Descrição': desc_prod, 'Quantidade': qtd, 'Lote': lote, 'Última Atualização': datetime.now().strftime('%d/%m/%Y %H:%M')}])
                        st.session_state.inventory = pd.concat([st.session_state.inventory, nova_alocacao], ignore_index=True)
                    
                    novo_mov = pd.DataFrame([{'Tipo': 'Entrada', 'Endereço Origem': 'Docas', 'Endereço Destino': endereco_destino, 'Produto': cod_prod, 'Quantidade': qtd, 'Data Hora': datetime.now().strftime('%d/%m/%Y %H:%M'), 'Operador': st.session_state.user}])
                    st.session_state.movements = pd.concat([st.session_state.movements, novo_mov], ignore_index=True)
                    
                    salvar_dados()
                    registrar_auditoria(f"Armazenou {cod_prod} no endereço {endereco_destino}", "Inventário")
                    st.success(f"Registrado com sucesso no endereço {endereco_destino}!")
                    st.rerun()
                else:
                    st.warning("Preencha o Endereço, Código e Descrição do Produto.")

    # 3. Movimentação Interna
    elif opcao_menu == "Movimentação Interna":
        st.title("🔄 Transferência entre Endereços")
        if not validar_perfil(['Almoxarife']):
            st.error("Acesso restrito."); st.stop()
            
        enderecos_ocupados = st.session_state.inventory['Endereço'].unique().tolist()
        
        if not enderecos_ocupados:
            st.info("Não há nenhum produto em estoque para movimentar.")
        else:
            with st.form("transferencia"):
                origem = st.selectbox("Selecione o Endereço de Origem (Onde o item está)", enderecos_ocupados)
                destino_input = st.text_input("Digite o Endereço de Destino (Para onde vai)").upper().strip()
                
                if st.form_submit_button("Efetuar Movimentação"):
                    if destino_input:
                        df_item = st.session_state.inventory[st.session_state.inventory['Endereço'] == origem]
                        
                        if not df_item.empty:
                            p_codigo = str(df_item['Código Produto'].values)
                            p_desc = str(df_item['Descrição'].values)


