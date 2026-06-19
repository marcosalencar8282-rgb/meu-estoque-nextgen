import streamlit as st
from datetime import datetime
import json
import os

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="WMS Global - Cadastro e Endereçamento", layout="wide")

# ==========================================
# 2. BANCO DE DADOS EM ARQUIVO (JSON PURO)
# ==========================================
ARQUIVO_BD = "wms_global_db.json"

def carregar_dados():
    if 'bd' not in st.session_state:
        if os.path.exists(ARQUIVO_BD):
            try:
                with open(ARQUIVO_BD, 'r', encoding='utf-8') as f:
                    st.session_state.bd = json.load(f)
            except Exception:
                st.session_state.bd = {"usuarios": [{"usuario": "admin", "senha": "admin"}], "produtos": [], "enderecos": [], "estoque": []}
        else:
            st.session_state.bd = {
                "usuarios": [{"usuario": "admin", "senha": "admin"}], # Usuário padrão inicial
                "produtos": [],     
                "enderecos": [],    
                "estoque": []       
            }
    
    # Garante que a chave de usuários exista caso o arquivo seja antigo
    if "usuarios" not in st.session_state.bd:
        st.session_state.bd["usuarios"] = [{"usuario": "admin", "senha": "admin"}]

def salvar_dados():
    try:
        with open(ARQUIVO_BD, 'w', encoding='utf-8') as f:
            json.dump(st.session_state.bd, f, indent=4, ensure_ascii=False)
    except Exception as e:
        st.error(f"Erro ao salvar dados: {e}")

carregar_dados()

# ==========================================
# 3. CONTROLE DE FLUXO DE AUTENTICAÇÃO
# ==========================================
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    # Interface Centralizada de Login
    col_esq, col_centro, col_dir = st.columns([1, 1.2, 1])
    with col_centro:
        st.write("#")
        st.write("#")
        st.title("🔐 Acesso ao Sistema WMS")
        with st.form("login_form", clear_on_submit=False):
            usuario_input = st.text_input("Usuário").strip()
            senha_input = st.text_input("Senha", type="password").strip()
            
            if st.form_submit_button("Entrar", type="primary", use_container_width=True):
                # Valida as credenciais direto na lista de usuários do JSON
                valido = any(u["usuario"] == usuario_input and u["senha"] == senha_input for u in st.session_state.bd["usuarios"])
                
                if valido:
                    st.session_state.autenticado = True
                    st.session_state.usuario_atual = usuario_input
                    st.rerun()
                else:
                    st.error("Usuário ou senha incorretos.")
    st.stop() # Bloqueia o carregamento do restante da página caso não logado

# ==========================================
# 4. NAVEGAÇÃO / MENU LATERAL (SÓ APARECE LOGADO)
# ==========================================
st.sidebar.title("📦 WMS Corporativo")
st.sidebar.write(f"👤 Usuário: `{st.session_state.usuario_atual}`")

if st.sidebar.button("Sair / Logout", type="secondary", use_container_width=True):
    st.session_state.autenticado = False
    st.session_state.usuario_atual = None
    st.rerun()

st.sidebar.markdown("---")
opcao_menu = st.sidebar.radio(
    "Navegação do Sistema", 
    [
        "📊 Painel Geral (Estoque)", 
        "📦 Cadastro de Produtos", 
        "🧱 Cadastro de Endereços", 
        "📥 Entrada & Armazenagem", 
        "📤 Saída & Picking"
    ]
)

# ==========================================
# 5. MÓDULO: PAINEL GERAL (ESTOQUE)
# ==========================================
if opcao_menu == "📊 Painel Geral (Estoque)":
    st.title("📊 Posição de Estoque e Ocupação")
    
    total_prods = len(st.session_state.bd["produtos"])
    total_ends = len(st.session_state.bd["enderecos"])
    ends_ocupados = len(set([item["endereco"] for item in st.session_state.bd["estoque"] if item["quantidade"] > 0]))
    taxa_ocupacao = (ends_ocupados / total_ends * 100) if total_ends > 0 else 0
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Produtos Cadastrados", total_prods)
    c2.metric("Endereços Cadastrados", total_ends)
    c3.metric("Taxa de Ocupação", f"{taxa_ocupacao:.1f}%")
    
    st.subheader("🔍 Consulta Rápida")
    busca = st.text_input("Filtrar por Endereço, Código ou Descrição").upper()
    
    linhas_tabela = []
    for item in st.session_state.bd["estoque"]:
        desc = next((p["descricao"] for p in st.session_state.bd["produtos"] if p["codigo"] == item["codigo_produto"]), "Não Cadastrado")
        
        if (not busca) or (busca in item["endereco"].upper() or busca in item["codigo_produto"].upper() or busca in desc.upper()):
            linhas_tabela.append({
                "Endereço": item["endereco"],
                "Cód. Produto": item["codigo_produto"],
                "Descrição": desc,
                "Qtd": item["quantidade"],
                "Lote": item["lote"],
                "Últ. Movimentação": item["atualizacao"]
            })
            
    st.dataframe(linhas_tabela, use_container_width=True)

# ==========================================
# 6. MÓDULO: CADASTRO DE PRODUTOS
# ==========================================
elif opcao_menu == "📦 Cadastro de Produtos":
    st.title("📦 Cadastro de Itens e SKUs")
    
    with st.form("cad_produto", clear_on_submit=True):
        col1, col2 = st.columns(2)
        codigo = col1.text_input("Código do Produto (SKU / EAN)").upper().strip()
        descricao = col2.text_input("Descrição Completa do Item")
        
        col3, col4 = st.columns(2)
        categoria = col3.selectbox("Categoria", ["Matéria-Prima", "Produto Acabado", "Embalagem", "Outros"])
        unidade = col4.selectbox("Unidade de Medida", ["UN", "KG", "CX", "PCT", "L"])
        
        if st.form_submit_button("Salvar Produto", type="primary"):
            if codigo and descricao:
                if any(p["codigo"] == codigo for p in st.session_state.bd["produtos"]):
                    st.error("Este código de produto já está cadastrado!")
                else:
                    st.session_state.bd["produtos"].append({
                        "codigo": codigo, "descricao": descricao, "categoria": categoria, "unidade": unidade
                    })
                    salvar_dados()
                    st.success(f"Produto {codigo} cadastrado com sucesso!")
                    st.rerun()
            else:
                st.warning("Preencha os campos obrigatórios (Código e Descrição).")
                
    st.subheader("Itens Cadastrados")
    st.dataframe(st.session_state.bd["produtos"], use_container_width=True)

# ==========================================
# 7. MÓDULO: CADASTRO DE ENDEREÇOS
# ==========================================
elif opcao_menu == "🧱 Cadastro de Endereços":
    st.title("🧱 Cadastro de Endereço Único")
    
    with st.form("cad_endereco", clear_on_submit=True):
        cod_completo = st.text_input("Código do Endereço (Ex: A-01, PRATELEIRA-2, BOX-A)").upper().strip()
        
        if st.form_submit_button("Cadastrar Endereço", type="primary"):
            if cod_completo:
                if any(e["completo"] == cod_completo for e in st.session_state.bd["enderecos"]):
                    st.error("Este endereço já existe no sistema!")
                else:
                    st.session_state.bd["enderecos"].append({"completo": cod_completo})
                    salvar_dados()
                    st.success(f"Endereço '{cod_completo}' criado com sucesso!")
                    st.rerun()
            else:
                st.warning("Por favor, digite o código do endereço.")
                
    st.subheader("Endereços Ativos no Sistema")
    st.dataframe(st.session_state.bd["enderecos"], use_container_width=True)

# ==========================================
# 8. MÓDULO: ENTRADA & ARMAZENAGEM
# ==========================================
elif opcao_menu == "📥 Entrada & Armazenagem":
    st.title("📥 Entrada de Mercadoria por Validação")
    
    if not st.session_state.bd["produtos"] or not st.session_state.bd["enderecos"]:
        st.warning("⚠️ Para dar entrada, você precisa ter ao menos 1 Produto e 1 Endereço cadastrados nas abas anteriores.")
    else:
        lista_prods = [f"{p['codigo']} - {p['descricao']}" for p in st.session_state.bd["produtos"]]
        lista_ends = [e["completo"] for e in st.session_state.bd["enderecos"]]
        
        with st.form("mov_entrada", clear_on_submit=True):
            prod_selecionado = st.selectbox("Selecione o Produto Cadastrado", lista_prods)
            end_selecionado = st.selectbox("Selecione o Endereço de Destino", lista_ends)
            
            c1, c2 = st.columns(2)
            qtd = c1.number_input("Quantidade", min_value=1, value=1)
            lote = c2.text_input("Lote / Validade", value="N/A").upper()
            
            if st.form_submit_button("Executar Entrada"):
                # Captura apenas o código (posição 0) da string separada
                cod_prod = prod_selecionado.split(" - ")[0].strip()
                
                encontrou = False
                for item in st.session_state.bd["estoque"]:
                    if item["endereco"] == end_selecionado and item["codigo_produto"] == cod_prod and item["lote"] == lote:
                        item["quantidade"] += qtd
                        item["atualizacao"] = datetime.now().strftime('%d/%m/%Y %H:%M')
                        encontrou = True
                        break
                
                if not encontrou:
                    st.session_state.bd["estoque"].append({
                        "endereco": end_selecionado, 
                        "codigo_produto": cod_prod, 
                        "quantidade": qtd, 
                        "lote": lote, 
                        "atualizacao": datetime.now().strftime('%d/%m/%Y %H:%M')
                    })


