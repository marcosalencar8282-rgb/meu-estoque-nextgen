import streamlit as st
from datetime import datetime
import os
import json

# Configuração inicial obrigatória
st.set_page_config(page_title="WMS - Estoque e Endereçamento", layout="wide")

# ==========================================
# BANCO DE DADOS EM ARQUIVO EM FORMATO SEGURO
# ==========================================
def carregar_dados():
    if 'users' not in st.session_state:
        st.session_state.users = {
            'admin': {'password': '123', 'profile': 'Administrador', 'active': True},
            'almoxarife': {'password': '123', 'profile': 'Almoxarife', 'active': True},
            'conferente': {'password': '123', 'profile': 'Conferente', 'active': True},
            'consulta': {'password': '123', 'profile': 'Consulta', 'active': True}
        }

    if 'inventory' not in st.session_state:
        st.session_state.inventory = []
        if os.path.exists('wms_inventario_livre.json'):
            try:
                with open('wms_inventario_livre.json', 'r', encoding='utf-8') as f:
                    dados = json.load(f)
                    if isinstance(dados, dict) and 'Endereço' in dados:
                        chaves = list(dados['Endereço'].keys())
                        for c in chaves:
                            st.session_state.inventory.append({
                                'Endereço': str(dados['Endereço'].get(c, '')),
                                'Código Produto': str(dados['Código Produto'].get(c, '')),
                                'Descrição': str(dados['Descrição'].get(c, '')),
                                'Quantidade': int(dados['Quantidade'].get(c, 0)),
                                'Lote': str(dados['Lote'].get(c, 'N/A')),
                                'Última Atualização': str(dados['Última Atualização'].get(c, ''))
                            })
                    elif isinstance(dados, list):
                        st.session_state.inventory = [i for i in dados if isinstance(i, dict)]
            except Exception:
                st.session_state.inventory = []

    if 'config' not in st.session_state:
        st.session_state.config = {'Empresa': 'WMS Endereçamento S/A'}

def salvar_dados():
    with open('wms_inventario_livre.json', 'w', encoding='utf-8') as f:
        json.dump(st.session_state.inventory, f, indent=4, ensure_ascii=False)

carregar_dados()

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
                        st.rerun()
                    else:
                        st.error("Acesso bloqueado: Usuário Inativo.")
                else:
                    st.error("Credenciais incorretas.")
else:
    st.sidebar.write(f"🏢 **{st.session_state.config['Empresa']}**")
    st.sidebar.write(f"👤 `{st.session_state.user}`")
    if st.sidebar.button("Efetuar Logout / Sair"):
        del st.session_state.user
        st.rerun()
        
    st.sidebar.divider()
    
    # Apenas os módulos solicitados na barra lateral
    opcao_menu = st.sidebar.radio(
        "Módulos WMS", 
        ["Endereçamento (Visão Geral)", "Entrada (Armazenagem)", "Saída (Picking)"]
    )
    
    # 1. MÓDULO ENDEREÇAMENTO (VISÃO GERAL DO ESTOQUE)
    if opcao_menu == "Endereçamento (Visão Geral)":
        st.title("🧱 Consulta de Posições e Endereçamento")
        
        total_posicoes = len(set([str(item.get('Endereço', '')) for item in st.session_state.inventory if isinstance(item, dict)]))
        total_itens = sum([int(item.get('Quantidade', 0)) for item in st.session_state.inventory if isinstance(item, dict)])
        
        c1, c2 = st.columns(2)
        c1.metric("Posições Ocupadas no Momento 📥", total_posicoes)
        c2.metric("Total de Itens Armazenados 📦", total_itens)
        
        st.subheader("🔍 Filtro de Posições")
        busca = st.text_input("Buscar por Endereço ou Produto").upper()
        
        lista_exibicao = [i for i in st.session_state.inventory if isinstance(i, dict)]
        if busca:
            lista_exibicao = [
                item for item in lista_exibicao 
                if busca in str(item.get('Endereço', '')).upper() or busca in str(item.get('Código Produto', '')).upper() or busca in str(item.get('Descrição', '')).upper()
            ]
            
        st.dataframe(lista_exibicao, use_container_width=True)

    # 2. MÓDULO ENTRADA (ARMAZENAGEM)
    elif opcao_menu == "Entrada (Armazenagem)":
        st.title("📥 Entrada de Mercadoria por Endereço")
        if not validar_perfil(['Almoxarife', 'Conferente']):
            st.error("Acesso negado."); st.stop()
            
        with st.form("armazenagem"):
            st.info("Digite o código do endereço onde o produto será armazenado.")
            endereco_destino = st.text_input("Código do Endereço (Ex: PRATELEIRA-A1)").upper().strip()
            cod_prod = st.text_input("Código do Produto")
            desc_prod = st.text_input("Descrição do Produto")
            qtd = st.number_input("Quantidade", min_value=1, value=1)
            lote = st.text_input("Lote / Validade", value="N/A")
            
            if st.form_submit_button("Confirmar Entrada"):
                if endereco_destino and cod_prod and desc_prod:
                    encontrou = False
                    for item in st.session_state.inventory:
                        if isinstance(item, dict) and item.get('Endereço') == endereco_destino and item.get('Código Produto') == cod_prod and item.get('Lote') == lote:
                            item['Quantidade'] = int(item.get('Quantidade', 0)) + qtd
                            item['Última Atualização'] = datetime.now().strftime('%d/%m/%Y %H:%M')
                            encontrou = True
                            break
                    
                    if not encontrou:
                        st.session_state.inventory.append({
                            'Endereço': endereco_destino, 'Código Produto': cod_prod, 'Descrição': desc_prod, 
                            'Quantidade': qtd, 'Lote': lote, 'Última Atualização': datetime.now().strftime('%d/%m/%Y %H:%M')
                        })
                    
                    salvar_dados()
                    st.success(f"Produto guardado com sucesso no endereço {endereco_destino}!")
                    st.rerun()
                else:
                    st.warning("Preencha todos os campos obrigatórios.")

    # 3. MÓDULO SAÍDA (PICKING)
    elif opcao_menu == "Saída (Picking)":
        st.title("📤 Retirada de Estoque (Picking)")
        if not validar_perfil(['Almoxarife', 'Conferente']):
            st.error("Acesso negado."); st.stop()
            
        enderecos_ocupados = list(set([item.get('Endereço', '') for item in st.session_state.inventory if isinstance(item, dict) and item.get('Endereço')]))
        if not enderecos_ocupados:
            st.info("Não há itens registrados em nenhum endereço.")
        else:
            with st.form("picking"):
                endereco_retirada = st.selectbox("Selecione o Endereço de Retirada", enderecos_ocupados)
                
                item_localizado = None
                for item in st.session_state.inventory:
                    if isinstance(item, dict) and item.get('Endereço') == endereco_retirada:
                        item_localizado = item
                        break
                
                if item_localizado:
                    p_desc = item_localizado.get('Descrição', '')
                    p_qtd_max = int(item_localizado.get('Quantidade', 0))
                    p_lote = item_localizado.get('Lote', 'N/A')
                    
                    st.warning(f"📦 Item na posição: {p_desc} | Lote: {p_lote} | Saldo: {p_qtd_max}")
                    qtd_retirar = st.number_input("Quantidade a Retirar", min_value=1, max_value=p_qtd_max, value=p_qtd_max)
                    
                    if st.form_submit_button("Confirmar Baixa/Saída"):
                        if qtd_retirar == p_qtd_max:
                            st.session_state.inventory = [item for item in st.session_state.inventory if isinstance(item, dict) and item.get('Endereço') != endereco_retirada]
                        else:
                            for item in st.session_state.inventory:
                                if isinstance(item, dict) and item.get('Endereço') == endereco_retirada:
                                    item['Quantidade'] = int(item.get('Quantidade', 0)) - qtd_retirar
                                    break
                        
                        salvar_dados()
                        st.success("Picking concluído e saldo atualizado!")
                        st.rerun()





