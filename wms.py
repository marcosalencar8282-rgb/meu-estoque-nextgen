import streamlit as st
import pandas as pd
from datetime import datetime
import os

# Configuração inicial obrigatória
st.set_page_config(page_title="WMS - Endereçamento de Estoque", layout="wide")

# ==========================================
# SISTEMA DE BANCO DE DADOS PERSISTENTE (JSON)
# ==========================================
def carregar_dados():
    # Inicializa usuários padrão se não existirem
    if 'users' not in st.session_state:
        st.session_state.users = {
            'admin': {'password': '123', 'profile': 'Administrador', 'active': True},
            'almoxarife': {'password': '123', 'profile': 'Almoxarife', 'active': True},
            'conferente': {'password': '123', 'profile': 'Conferente', 'active': True},
            'consulta': {'password': '123', 'profile': 'Consulta', 'active': True}
        }
    
    # Carrega Estrutura de Endereços
    if os.path.exists('wms_enderecos.json'):
        st.session_state.locations = pd.read_json('wms_enderecos.json')
    else:
        st.session_state.locations = pd.DataFrame([
            {'Endereço': 'A-01-02-01', 'Rua': 'A', 'Prédio': '01', 'Nível': '02', 'Vão': '01', 'Status': 'Disponível'},
            {'Endereço': 'A-01-02-02', 'Rua': 'A', 'Prédio': '01', 'Nível': '02', 'Vão': '02', 'Status': 'Disponível'},
            {'Endereço': 'B-04-01-01', 'Rua': 'B', 'Prédio': '04', 'Nível': '01', 'Vão': '01', 'Status': 'Disponível'},
        ])

    # Carrega Saldo de Estoque por Endereço
    if os.path.exists('wms_inventario.json'):
        st.session_state.inventory = pd.read_json('wms_inventario.json')
        if st.session_state.inventory.empty:
            st.session_state.inventory = pd.DataFrame(columns=['Endereço', 'Código Produto', 'Descrição', 'Quantidade', 'Lote', 'Última Atualização'])
    else:
        st.session_state.inventory = pd.DataFrame(columns=['Endereço', 'Código Produto', 'Descrição', 'Quantidade', 'Lote', 'Última Atualização'])

    # Carrega Histórico de Movimentações
    if os.path.exists('wms_movimentacoes.json'):
        st.session_state.movements = pd.read_json('wms_movimentacoes.json')
        if st.session_state.movements.empty:
            st.session_state.movements = pd.DataFrame(columns=['Tipo', 'Endereço Origem', 'Endereço Destino', 'Produto', 'Quantidade', 'Data Hora', 'Operador'])
    else:
        st.session_state.movements = pd.DataFrame(columns=['Tipo', 'Endereço Origem', 'Endereço Destino', 'Produto', 'Quantidade', 'Data Hora', 'Operador'])

    # Carrega Auditoria
    if os.path.exists('wms_auditoria.json'):
        st.session_state.auditory = pd.read_json('wms_auditoria.json')
        if st.session_state.auditory.empty:
            st.session_state.auditory = pd.DataFrame(columns=['Usuário', 'Ação', 'Registro', 'Data Hora'])
    else:
        st.session_state.auditory = pd.DataFrame(columns=['Usuário', 'Ação', 'Registro', 'Data Hora'])

    if 'config' not in st.session_state:
        st.session_state.config = {'Empresa': 'WMS Endereçamento S/A'}

def salvar_dados():
    st.session_state.locations.to_json('wms_enderecos.json', orient='records', indent=4)
    st.session_state.inventory.to_json('wms_inventario.json', orient='records', indent=4)
    st.session_state.movements.to_json('wms_movimentacoes.json', orient='records', indent=4)
    st.session_state.auditory.to_json('wms_auditoria.json', orient='records', indent=4)

# Executa a carga dos dados armazenados no disco
carregar_dados()

# Sistema de logs de auditoria
def registrar_auditoria(acao, registro):
    usuario_atual = st.session_state.get('user', 'Sistema')
    novo_log = pd.DataFrame([{
        'Usuário': usuario_atual, 'Ação': acao, 'Registro': registro,
        'Data Hora': datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    }])
    st.session_state.auditory = pd.concat([st.session_state.auditory, novo_log], ignore_index=True)
    salvar_dados()

# Função de verificação de permissões por perfil
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
    # Barra lateral de controle e navegação
    st.sidebar.write(f"🏢 **{st.session_state.config['Empresa']}**")
    st.sidebar.write(f"👤 `{st.session_state.user}` ({st.session_state.users[st.session_state.user]['profile']})")
    if st.sidebar.button("Efetuar Logout / Sair"):
        registrar_auditoria("Logout efetuado", "Sessão")
        del st.session_state.user
        st.rerun()
        
    st.sidebar.divider()
    
    opcao_menu = st.sidebar.radio(
        "Módulos WMS", 
        ["Dashboard Ocupação", "Estrutura de Endereços", "Entrada (Armazenagem)", "Movimentação Interna", "Saída (Picking)", "Consulta de Posições", "Auditoria"]
    )
    
    # 1. Dashboard de Ocupação
    if opcao_menu == "Dashboard Ocupação":
        st.title("📊 Dashboard de Ocupação do Armazém")
        
        total_posicoes = len(st.session_state.locations)
        posicoes_ocupadas = len(st.session_state.locations[st.session_state.locations['Status'] == 'Ocupado'])
        posicoes_livres = total_posicoes - posicoes_ocupadas
        taxa_ocupacao = (posicoes_ocupadas / total_posicoes * 100) if total_posicoes > 0 else 0
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total de Posições", total_posicoes)
        c2.metric("Posições Ocupadas 📥", posicoes_ocupadas)
        c3.metric("Posições Livres 🟢", posicoes_livres)
        c4.metric("Taxa de Ocupação", f"{taxa_ocupacao:.1f}%")
        
        st.subheader("📍 Ocupação Atual Detalhada")
        if not st.session_state.inventory.empty:
            st.dataframe(st.session_state.inventory, use_container_width=True)
        else:
            st.info("O armazém está completamente vazio.")

    # 2. Cadastro Estrutural de Endereços
    elif opcao_menu == "Estrutura de Endereços":
        st.title("🧱 Cadastro de Estrutura Física (Endereços)")
        if not validar_perfil(['Administrador']):
            st.error("Acesso Restrito ao Perfil Administrador.")
            st.stop()
            
        with st.form("c_endereco"):
            st.write("Crie uma nova posição de estoque usando o padrão logístico: **Rua-Prédio-Nível-Vão**")
            rua = st.text_input("Rua / Corredor (Ex: A)", max_chars=2).upper()
            predio = st.text_input("Prédio / Coluna (Ex: 01)", max_chars=3)
            nivel = st.text_input("Nível / Andar (Ex: 03)", max_chars=2)
            vao = st.text_input("Vão / Posição (Ex: 02)", max_chars=2)
            
            if st.form_submit_button("Gerar e Cadastrar Endereço"):
                if rua and predio and nivel and vao:
                    codigo_endereco = f"{rua}-{predio}-{nivel}-{vao}"
                    if codigo_endereco in st.session_state.locations['Endereço'].values:
                        st.error("Este endereço já está cadastrado no sistema.")
                    else:
                        novo_end = pd.DataFrame([{'Endereço': codigo_endereco, 'Rua': rua, 'Prédio': predio, 'Nível': nivel, 'Vão': vao, 'Status': 'Disponível'}])
                        st.session_state.locations = pd.concat([st.session_state.locations, novo_end], ignore_index=True)
                        salvar_dados()
                        registrar_auditoria(f"Cadastrou endereço {codigo_endereco}", "Estrutura")
                        st.success(f"Endereço {codigo_endereco} criado com sucesso!")
                        st.rerun()
                else:
                    st.warning("Preencha todos os níveis hierárquicos do endereço.")
        
        st.subheader("📋 Mapa de Endereços Cadastrados")
        st.dataframe(st.session_state.locations, use_container_width=True)

    # 3. Entrada e Armazenagem Direcionada
    elif opcao_menu == "Entrada (Armazenagem)":
        st.title("📥 Entrada de Produtos por Endereço")
        if not validar_perfil(['Almoxarife', 'Conferente']):
            st.error("Perfil sem autorização para entrada de estoque.")
            st.stop()
            
        enderecos_livres = st.session_state.locations[st.session_state.locations['Status'] == 'Disponível']['Endereço'].tolist()
        
        if not enderecos_livres:
            st.error("❌ Não há endereços vagos disponíveis no armazém. Libere ou cadastre novas posições.")
        else:
            with st.form("armazenagem"):
                endereco_destino = st.selectbox("Selecione o Endereço Vago Destino", enderecos_livres)
                cod_prod = st.text_input("Código do Produto")
                desc_prod = st.text_input("Descrição do Produto")
                qtd = st.number_input("Quantidade", min_value=1, value=1)
                lote = st.text_input("Lote / Validade", value="N/A")
                
                if st.form_submit_button("Confirmar Armazenagem"):
                    if cod_prod and desc_prod:
                        nova_alocacao = pd.DataFrame([{
