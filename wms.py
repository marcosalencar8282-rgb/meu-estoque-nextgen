import streamlit as st
import pandas as pd
from datetime import datetime

# Configuração inicial obrigatória
st.set_page_config(page_title="WMS - Sistema de Estoque", layout="wide")

# Inicialização segura do banco de dados em memória
if 'users' not in st.session_state:
    st.session_state.users = {
        'admin': {'password': '123', 'profile': 'Administrador', 'active': True},
        'almoxarife': {'password': '123', 'profile': 'Almoxarife', 'active': True},
        'conferente': {'password': '123', 'profile': 'Conferente', 'active': True},
        'consulta': {'password': '123', 'profile': 'Consulta', 'active': True}
    }
if 'products' not in st.session_state:
    st.session_state.products = pd.DataFrame(columns=['Código', 'Descrição', 'Categoria', 'Unidade de medida', 'Fornecedor', 'Estoque mínimo', 'Localização', 'Saldo Atual'])
if 'suppliers' not in st.session_state:
    st.session_state.suppliers = pd.DataFrame(columns=['Razão Social', 'CNPJ', 'Contato', 'E-mail', 'Telefone'])
if 'invoices' not in st.session_state:
    st.session_state.invoices = pd.DataFrame(columns=['Número da Nota', 'Fornecedor', 'Data', 'Produtos recebidos', 'Quantidades', 'Usuário que recebeu'])
if 'movements' not in st.session_state:
    st.session_state.movements = pd.DataFrame(columns=['Tipo', 'Produto', 'Quantidade', 'Motivo/Setor', 'Data Hora', 'Responsável'])
if 'auditory' not in st.session_state:
    st.session_state.auditory = pd.DataFrame(columns=['Usuário', 'Ação', 'Tabela/Registro', 'Data Hora'])
if 'config' not in st.session_state:
    st.session_state.config = {'Empresa': 'Minha Empresa S/A'}

# Sistema de logs de auditoria
def registrar_auditoria(acao, tabela):
    usuario_atual = st.session_state.get('user', 'Sistema')
    novo_log = pd.DataFrame([{
        'Usuário': usuario_atual, 'Ação': acao, 'Tabela/Registro': tabela,
        'Data Hora': datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    }])
    st.session_state.auditory = pd.concat([st.session_state.auditory, novo_log], ignore_index=True)

# Função de verificação de permissões por perfil
def validar_perfil(perfis_permitidos):
    if 'user' not in st.session_state:
        return False
    perfil_usuario = st.session_state.users[st.session_state.user]['profile']
    return perfil_usuario in perfis_permitidos or perfil_usuario == 'Administrador'

# Tela de Login Integrada
if 'user' not in st.session_state:
    st.subheader("🔑 Login do Sistema Integrado de Estoque")
    usuario_input = st.text_input("Usuário", key="usr")
    senha_input = st.text_input("Senha", type="password", key="pwd")
    
    col_log1, col_log2 = st.columns(2)
    with col_log1:
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
    with col_log2:
        if st.button("Recuperar Senha"):
            st.info("Entre em contato com o suporte ou o administrador da TI para redefinir as credenciais.")

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
        "Módulos do Sistema", 
        ["Dashboard", "Cadastro de Produtos", "Cadastro de Fornecedores", "Recebimento de NFs", "Entrada de Estoque", "Saída de Estoque", "Consulta de Estoque", "Inventário Rotativo", "Relatórios", "Gestão de Usuários", "Auditoria", "Configurações"]
    )
    
    # 1. Módulo Dashboard
    if opcao_menu == "Dashboard":
        st.title("📊 Dashboard")
        total_p = len(st.session_state.products)
        baixo_e = len(st.session_state.products[st.session_state.products['Saldo Atual'] <= st.session_state.products['Estoque mínimo']]) if total_p > 0 else 0
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total de Produtos", total_p)
        c2.metric("Estoque Baixo ⚠️", baixo_e)
        c3.metric("Entradas do Dia", int(st.session_state.movements[st.session_state.movements['Tipo'] == 'Entrada']['Quantidade'].sum() if len(st.session_state.movements) > 0 else 0))
        c4.metric("Saídas do Dia", int(st.session_state.movements[st.session_state.movements['Tipo'] == 'Saída']['Quantidade'].sum() if len(st.session_state.movements) > 0 else 0))
        
        st.subheader("🔄 Últimas Movimentações")
        st.dataframe(st.session_state.movements.tail(5), use_container_width=True)
        st.subheader("📈 Gráfico Balanceado")
        if total_p > 0:
            st.bar_chart(st.session_state.products.set_index('Descrição')[['Saldo Atual']], use_container_width=True)
        else:
            st.info("Nenhum dado cadastrado.")

    # 2. Módulo Cadastro de Produtos
    elif opcao_menu == "Cadastro de Produtos":
        st.title("📦 Cadastro de Produtos")
        if not validar_perfil(['Administrador']):
            st.error("Acesso Restrito ao Perfil Administrador."); st.stop()
        with st.form("c_prod"):
            c_cod = st.text_input("Código")
            c_desc = st.text_input("Descrição")
            c_cat = st.selectbox("Categoria", ["Matéria-Prima", "Acabado", "Embalagem", "Consumo"])
            c_un = st.selectbox("Unidade de Medida", ["UN", "KG", "LT", "MT"])
            c_forn = st.selectbox("Fornecedor", st.session_state.suppliers['Razão Social'].tolist() if len(st.session_state.suppliers) > 0 else ["Padrão"])
            c_min = st.number_input("Estoque Mínimo", min_value=0, value=5)
            c_loc = st.text_input("Localização")
            if st.form_submit_button("Cadastrar"):
                if c_cod and c_desc:
                    if c_cod in st.session_state.products['Código'].values:
                        st.error("Código em uso.")
                    else:
                        novo_p = pd.DataFrame([{'Código': c_cod, 'Descrição': c_desc, 'Categoria': c_cat, 'Unidade de medida': c_un, 'Fornecedor': c_forn, 'Estoque mínimo': c_min, 'Localização': c_loc, 'Saldo Atual': 0}])
                        st.session_state.products = pd.concat([st.session_state.products, novo_p], ignore_index=True)
                        registrar_auditoria(f"Cadastrou produto {c_cod}", "Produtos")
                        st.success("Salvo com sucesso!")
                else:
                    st.warning("Preencha os campos obrigatórios.")

    # 3. Módulo Cadastro de Fornecedores
    elif opcao_menu == "Cadastro de Fornecedores":
        st.title("🏢 Cadastro de Fornecedores")
        if not validar_perfil(['Administrador']):
            st.error("Acesso Restrito ao Perfil Administrador."); st.stop()
        with st.form("c_forn"):
            f_raz = st.text_input("Razão Social")
            f_cnpj = st.text_input("CNPJ")
            f_cont = st.text_input("Contato")
            f_em = st.text_input("E-mail")
            f_tel = st.text_input("Telefone")
            if st.form_submit_button("Salvar Fornecedor"):
                if f_raz and f_cnpj:
                    novo_f = pd.DataFrame([{'Razão Social': f_raz, 'CNPJ': f_cnpj, 'Contato': f_cont, 'E-mail': f_em, 'Telefone': f_tel}])
                    st.session_state.suppliers = pd.concat([st.session_state.suppliers, novo_f], ignore_index=True)
                    registrar_auditoria(f"Cadastrou fornecedor {f_raz}", "Fornecedores")
                    st.success("Fornecedor Registrado!")
                else:
                    st.warning("Insira a Razão Social e CNPJ.")

    # 4. Módulo Recebimento de Notas Fiscais
    elif opcao_menu == "Recebimento de NFs":
        st.title("🧾 Recebimento de Notas Fiscais")
        if not validar_perfil(['Conferente']):
            st.error("Perfil de Acesso Exclusivo para Conferente."); st.stop()
        if len(st.session_state.products) == 0:
            st.warning("Cadastre itens no estoque previamente."); st.stop()
        nf_num = st.text_input("Número do Documento (NF)")
        nf_forn = st.selectbox("Fornecedor Responsável", st.session_state.suppliers['Razão Social'].tolist() if len(st.session_state.suppliers) > 0 else ["Não Informado"])
        nf_prod = st.selectbox("Item Vinculado", st.session_state.products['Descrição'].tolist())
        nf_qtd = st.number_input("Quantidade Registrada", min_value=1, value=1)
        if st.button("Processar Entrada via NF"):
            nova_nf = pd.DataFrame([{'Número da Nota': nf_num, 'Fornecedor': nf_forn, 'Data': datetime.now().strftime('%d/%m/%Y'), 'Produtos recebidos': nf_prod, 'Quantidades': nf_qtd, 'Usuário que recebeu': st.session_state.user}])
            st.session_state.invoices = pd.concat([st.session_state.invoices, nova_nf], ignore_index=True)
            st.session_state.products.loc[st.session_state.products['Descrição'] == nf_prod, 'Saldo Atual'] += nf_qtd
            nova_mov = pd.DataFrame([{'Tipo': 'Entrada', 'Produto': nf_prod, 'Quantidade': nf_qtd, 'Motivo/Setor': f"NF N° {nf_num}", 'Data Hora': datetime.now().strftime('%d/%m/%Y %H:%M'), 'Responsável': st.session_state.user}])
            st.session_state.movements = pd.concat([st.session_state.movements, nova_mov], ignore_index=True)
            registrar_auditoria(f"Recebimento de NF: {nf_num}", "Notas Fiscais")
            st.success("Estoque incrementado e Nota Fiscal Processada!")

    # 5. Módulo Entrada de Estoque
