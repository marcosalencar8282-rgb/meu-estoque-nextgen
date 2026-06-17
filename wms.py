import streamlit as st
from datetime import datetime
import os
import json

# Configuração inicial obrigatória
st.set_page_config(page_title="WMS - Endereçamento de Estoque Livre", layout="wide")

# ==========================================
# BANCO DE DADOS EM ARQUIVO (FORMA MAIS FÁCIL)
# ==========================================
def carregar_dados():
    # Inicializa usuários padrão
    if 'users' not in st.session_state:
        st.session_state.users = {
            'admin': {'password': '123', 'profile': 'Administrador', 'active': True},
            'almoxarife': {'password': '123', 'profile': 'Almoxarife', 'active': True},
            'conferente': {'password': '123', 'profile': 'Conferente', 'active': True},
            'consulta': {'password': '123', 'profile': 'Consulta', 'active': True}
        }

    # Carrega Inventário (Lista simples de dicionários)
    if 'inventory' not in st.session_state:
        if os.path.exists('wms_inventario_livre.json'):
            with open('wms_inventario_livre.json', 'r', encoding='utf-8') as f:
                st.session_state.inventory = json.load(f)
        else:
            st.session_state.inventory = []

    # Carrega Movimentações
    if 'movements' not in st.session_state:
        if os.path.exists('wms_movimentacoes_livre.json'):
            with open('wms_movimentacoes_livre.json', 'r', encoding='utf-8') as f:
                st.session_state.movements = json.load(f)
        else:
            st.session_state.movements = []

    # Carrega Auditoria
    if 'auditory' not in st.session_state:
        if os.path.exists('wms_auditoria_livre.json'):
            with open('wms_auditoria_livre.json', 'r', encoding='utf-8') as f:
                st.session_state.auditory = json.load(f)
        else:
            st.session_state.auditory = []

    if 'config' not in st.session_state:
        st.session_state.config = {'Empresa': 'WMS Endereçamento S/A'}

def salvar_dados():
    with open('wms_inventario_livre.json', 'w', encoding='utf-8') as f:
        json.dump(st.session_state.inventory, f, indent=4, ensure_ascii=False)
    with open('wms_movimentacoes_livre.json', 'w', encoding='utf-8') as f:
        json.dump(st.session_state.movements, f, indent=4, ensure_ascii=False)
    with open('wms_auditoria_livre.json', 'w', encoding='utf-8') as f:
        json.dump(st.session_state.auditory, f, indent=4, ensure_ascii=False)

carregar_dados()

def registrar_auditoria(acao, registro):
    usuario_atual = st.session_state.get('user', 'Sistema')
    novo_log = {
        'Usuário': usuario_atual, 'Ação': acao, 'Registro': registro,
        'Data Hora': datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    }
    st.session_state.auditory.append(novo_log)
    salvar_dados()

def validar_perfil(perfis_permitidos):
    if 'user' not in st.session_state:
        return False
    perfil_usuario = st.session_state.users[st.session_state.user]['profile']
    return perfil_usuario in perfis_permitidos or perfil_usuario == 'Administrador'

# ==========================================
# TELA DE LOGIN CENTRALIZADA E MENOR
# ==========================================
if 'user' not in st.session_state:
    col_vazia_esq, col_login, col_vazia_dir = st.columns([2, 1.5, 2])
    
    with col_login:
        st.write("---")
        st.subheader("🔑 Login - WMS Livre")
        
        with st.form("form_login"):
            usuario_input = st.text_input("Usuário", key="usr")
            senha_input = st.text_input("Senha", type="password", key="pwd")
            botao_entrar = st.form_submit_button("Entrar no Sistema", type="primary", use_container_width=True)
            
            if botao_entrar:
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
        ["Visão Geral do Estoque", "Entrada (Armazenagem)", "Movimentação Interna", "Saída (Picking)", "Histórico de Movimentações", "Auditoria"]
    )
    
    # 1. Visão Geral do Estoque
    if opcao_menu == "Visão Geral do Estoque":
        st.title("📊 Visão Geral e Posições Ocupadas")
        
        total_posicoes = len(set([item['Endereço'] for item in st.session_state.inventory]))
        total_itens = sum([int(item['Quantidade']) for item in st.session_state.inventory])
        
        c1, c2 = st.columns(2)
        c1.metric("Posições Ocupadas no Momento 📥", total_posicoes)
        c2.metric("Total de Peças/Volumes em Estoque 📦", total_itens)
        
        st.subheader("📍 Filtro de Inventário")
        busca = st.text_input("Filtrar por Produto ou Código do Endereço").upper()
        
        lista_exibicao = st.session_state.inventory
        if busca:
            lista_exibicao = [
                item for item in st.session_state.inventory 
                if busca in str(item['Endereço']).upper() or busca in str(item['Código Produto']).upper() or busca in str(item['Descrição']).upper()
            ]
            
        st.dataframe(lista_exibicao, use_container_width=True)

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
                    encontrou = False
                    for item in st.session_state.inventory:
                        if item['Endereço'] == endereco_destino and item['Código Produto'] == cod_prod and item['Lote'] == lote:
                            item['Quantidade'] += qtd
                            item['Última Atualização'] = datetime.now().strftime('%d/%m/%Y %H:%M')
                            encontrou = True
                            break
                    
                    if not encontrou:
                        nova_alocacao = {
                            'Endereço': endereco_destino, 'Código Produto': cod_prod, 'Descrição': desc_prod, 
                            'Quantidade': qtd, 'Lote': lote, 'Última Atualização': datetime.now().strftime('%d/%m/%Y %H:%M')
                        }
                        st.session_state.inventory.append(nova_alocacao)
                    
                    novo_mov = {
                        'Tipo': 'Entrada', 'Endereço Origem': 'Docas', 'Endereço Destino': endereco_destino, 
                        'Produto': desc_prod, 'Quantidade': qtd, 'Data Hora': datetime.now().strftime('%d/%m/%Y %H:%M'), 'Operador': st.session_state.user
                    }
                    st.session_state.movements.append(novo_mov)
                    
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
            
        enderecos_ocupados = list(set([item['Endereço'] for item in st.session_state.inventory]))
        
        if not enderecos_ocupados:
            st.info("Não há nenhum produto em estoque para movimentar.")
        else:
            with st.form("transferencia"):
                origem = st.selectbox("Selecione o Endereço de Origem (Onde o item está)", enderecos_ocupados)
                destino_input = st.text_input("Digite o Endereço de Destino (Para onde vai)").upper().strip()
                
                if st.form_submit_button("Efetuar Movimentação"):
                    if destino_input:
                        item_movido = None
                        for item in st.session_state.inventory:
                            if item['Endereço'] == origin:
                                item_movido = item
                                break
                        
                        if item_movido:
                            p_codigo = item_movido['Código Produto']
                            p_desc = item_movido['Descrição']
                            p_qtd = item_movido['Quantidade']
                            p_lote = item_movido['Lote']
                            
                            # Adiciona no destino




