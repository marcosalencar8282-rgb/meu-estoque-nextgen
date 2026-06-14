import streamlit as st
import pandas as pd
from datetime import datetime

# -----------------------------------------------------------------------------
# CONFIGURAÇÃO DA PÁGINA (Deve ser a primeira instrução Streamlit)
# -----------------------------------------------------------------------------
st.set_page_config(page_title="WMS - Sistema de Estoque", layout="wide")

# -----------------------------------------------------------------------------
# BANCO DE DADOS EM MEMÓRIA (INICIALIZAÇÃO)
# -----------------------------------------------------------------------------
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
    st.session_state.config = {'Empresa': 'Minha Empresa S/A', 'Logo': None}

# -----------------------------------------------------------------------------
# FUNÇÕES AUXILIARES (AUDITORIA E PERMISSÕES)
# -----------------------------------------------------------------------------
def log_audit(action, target):
    user = st.session_state.get('user', 'Sistema')
    new_log = pd.DataFrame([{
        'Usuário': user,
        'Ação': action,
        'Tabela/Registro': target,
        'Data Hora': datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    }])
    st.session_state.auditory = pd.concat([st.session_state.auditory, new_log], ignore_index=True)

def check_permission(allowed_profiles):
    if 'user' not in st.session_state:
        return False
    user_profile = st.session_state.users[st.session_state.user]['profile']
    return user_profile in allowed_profiles or user_profile == 'Administrador'

# -----------------------------------------------------------------------------
# TELAS DO SISTEMA
# -----------------------------------------------------------------------------
def render_login():
    st.subheader("🔑 Login do Sistema")
    username = st.text_input("Usuário")
    password = st.text_input("Senha", type="password")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Entrar", type="primary"):
            if username in st.session_state.users and st.session_state.users[username]['password'] == password:
                if st.session_state.users[username]['active']:
                    st.session_state.user = username
                    log_audit("Login efetuado", "Sessão")
                    st.rerun()
                else:
                    st.error("Usuário inativo.")
            else:
                st.error("Usuário ou senha incorretos.")
    with col2:
        if st.button("Recuperar senha"):
            st.info("Contate o administrador do sistema para redefinir sua senha.")

def render_dashboard():
    st.title("📊 Dashboard Executivo")
    total_prod = len(st.session_state.products)
    estoque_baixo = 0
    if total_prod > 0:
        baixo_df = st.session_state.products[st.session_state.products['Saldo Atual'] <= st.session_state.products['Estoque mínimo']]
        estoque_baixo = len(baixo_df)
    
    hoy = datetime.now().strftime('%d/%m/%Y')
    movs_hoje = st.session_state.movements[st.session_state.movements['Data Hora'].str.contains(hoy, na=False)] if len(st.session_state.movements) > 0 else pd.DataFrame()
    entradas_dia = movs_hoje[movs_hoje['Tipo'] == 'Entrada']['Quantidade'].sum() if len(movs_hoje) > 0 else 0
    saidas_dia = movs_hoje[movs_hoje['Tipo'] == 'Saída']['Quantidade'].sum() if len(movs_hoje) > 0 else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total de Produtos", total_prod)
    c2.metric("Estoque Baixo ⚠️", estoque_baixo)
    c3.metric("Entradas do Dia", int(entradas_dia))
    c4.metric("Saídas do Dia", int(saidas_dia))

    st.subheader("🔄 Últimas Movimentações")
    st.dataframe(st.session_state.movements.tail(5), use_container_width=True)

    st.subheader("📈 Gráficos de Estoque")
    if total_prod > 0:
        # Usando o gráfico nativo do Streamlit para evitar erros de dependência externa
        chart_data = st.session_state.products.set_index('Descrição')[['Saldo Atual']]
        st.bar_chart(chart_data, use_container_width=True)
    else:
        st.info("Nenhum produto cadastrado para exibir gráficos.")

def render_cadastro_produtos():
    st.title("📦 Cadastro de Produtos")
    if not check_permission(['Administrador']):
        st.error("Acesso negado."); return
    with st.form("form_produto"):
        cod = st.text_input("Código")
        desc = st.text_input("Descrição")
        cat = st.selectbox("Categoria", ["Matéria-Prima", "Acabado", "Embalagem", "Consumo"])
        un = st.selectbox("Unidade de Medida", ["UN", "KG", "LT", "MT"])
        forn = st.selectbox("Fornecedor", st.session_state.suppliers['Razão Social'].tolist() if len(st.session_state.suppliers) > 0 else ["Nenhum cadastrado"])
        est_min = st.number_input("Estoque Mínimo", min_value=0, value=10)
        loc = st.text_input("Localização")
        if st.form_submit_button("Salvar Produto"):
            if cod and desc:
                if cod in st.session_state.products['Código'].values:
                    st.error("Código já cadastrado.")
                else:
                    new_p = pd.DataFrame([{'Código': cod, 'Descrição': desc, 'Categoria': cat, 'Unidade de medida': un, 'Fornecedor': forn, 'Estoque mínimo': est_min, 'Localização': loc, 'Saldo Atual': 0}])
                    st.session_state.products = pd.concat([st.session_state.products, new_p], ignore_index=True)
                    log_audit(f"Cadastrou produto {cod}", "Produtos")
                    st.success("Produto cadastrado!")
            else:
                st.warning("Preencha Código e Descrição.")

def render_cadastro_fornecedores():
    st.title("🏢 Cadastro de Fornecedores")
    if not check_permission(['Administrador']):
        st.error("Acesso negado."); return
    with st.form("form_forn"):
        razao = st.text_input("Razão Social")
        cnpj = st.text_input("CNPJ")
        cont = st.text_input("Contato (Nome)")
        email = st.text_input("E-mail")
        tel = st.text_input("Telefone")
        if st.form_submit_button("Salvar Fornecedor"):
            if razao and cnpj:
                new_f = pd.DataFrame([{'Razão Social': razao, 'CNPJ': cnpj, 'Contato': cont, 'E-mail': email, 'Telefone': tel}])
                st.session_state.suppliers = pd.concat([st.session_state.suppliers, new_f], ignore_index=True)
                log_audit(f"Cadastrou fornecedor {razao}", "Fornecedores")
                st.success("Fornecedor cadastrado!")
            else:
                st.warning("Preencha Razão Social e CNPJ.")

def render_recebimento_nf():
    st.title("🧾 Recebimento de Notas Fiscais")
    if not check_permission(['Conferente']):
        st.error("Acesso negado."); return
    if len(st.session_state.products) == 0:
        st.warning("Cadastre produtos antes de receber uma NF."); return
    num_nf = st.text_input("Número da Nota")
    forn = st.selectbox("Fornecedor", st.session_state.suppliers['Razão Social'].tolist() if len(st.session_state.suppliers) > 0 else ["Não Informado"])
    prod = st.selectbox("Produto Recebido", st.session_state.products['Descrição'].tolist())
    qtd = st.number_input("Quantidade", min_value=1, value=1)
    if st.button("Processar Recebimento NF"):
        new_nf = pd.DataFrame([{'Número da Nota': num_nf, 'Fornecedor': forn, 'Data': datetime.now().strftime('%d/%m/%Y'), 'Produtos recebidos': prod, 'Quantidades': qtd, 'Usuário que recebeu': st.session_state.user}])
        st.session_state.invoices = pd.concat([st.session_state.invoices, new_nf], ignore_index=True)
        st.session_state.products.loc[st.session_state.products['Descrição'] == prod, 'Saldo Atual'] += qtd
        new_mov = pd.DataFrame([{'Tipo': 'Entrada', 'Produto': prod, 'Quantidade': qtd, 'Motivo/Setor': f"NF: {num_nf}", 'Data Hora': datetime.now().strftime('%d/%m/%Y %H:%M'), 'Responsável': st.session_state.user}])
        st.session_state.movements = pd.concat([st.session_state.movements, new_mov], ignore_index=True)
        log_audit(f"Recebeu NF {num_nf}", "Notas Fiscais")
        st.success("Nota Fiscal processada!")

def render_entrada_estoque():
    st.title("📥 Entrada Avulsa de Estoque")
    if not check_permission(['Almoxarife']):
        st.error("Acesso negado."); return
    if len(st.session_state.products) == 0:
        st.warning("Nenhum produto cadastrado."); return
    prod = st.selectbox("Produto", st.session_state.products['Descrição'].tolist())
    qtd = st.number_input("Quantidade", min_value=1, value=1)
    motivo = st.text_input("Motivo da Entrada")
    if st.button("Registrar Entrada"):
        st.session_state.products.loc[st.session_state.products['Descrição'] == prod, 'Saldo Atual'] += qtd

