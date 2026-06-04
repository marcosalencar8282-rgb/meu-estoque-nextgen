import sqlite3
from datetime import datetime
import streamlit as st

# Configuração da página com visual moderno e arrojado
st.set_page_config(
    page_title="NextGen | Controle de Estoque", layout="wide", page_icon="⚡"
)

# --- CONTROLE DE SESSÃO / LOGIN ---
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False
if "usuario_logado" not in st.session_state:
    st.session_state["usuario_logado"] = ""

# LISTA DE USUÁRIOS
USUARIOS_PERMITIDOS = {
    "admin": "Master@2026",
    "lucas": "Lucas#Estoque",
    "marcos": "931481",
    "gerente": "Logistica123"
}


def realizar_login():
    usuario_digitado = st.session_state["usuario_input"].strip()
    senha_digitada = st.session_state["senha_input"].strip()
    
    if usuario_digitado in USUARIOS_PERMITIDOS and USUARIOS_PERMITIDOS[usuario_digitado] == senha_digitada:
        st.session_state["autenticado"] = True
        st.session_state["usuario_logado"] = usuario_digitado
        st.success("Acesso autorizado!")
    else:
        st.error("Usuário ou senha incorretos.")


# TELA DE LOGIN (Bloqueia o sistema se não estiver autenticado)
if not st.session_state["autenticado"]:
    st.markdown(
        "<h1 style='text-align: center; color: #FFFFFF; font-family: Inter;'>⚡ NEXTGEN SYSTEM</h1>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='text-align: center; color: #64748B;'>Área Restrita - Autenticação Obrigatória</p>",
        unsafe_allow_html=True,
    )

    col_l1, col_l2, col_l3 = st.columns([1, 1.2, 1])
    with col_l2:
        with st.form("form_login"):
            st.text_input("Usuário:", key="usuario_input")
            st.text_input("Senha:", type="password", key="senha_input")
            st.form_submit_button("Entrar no Sistema", on_click=realizar_login)
    st.stop()

# Estilização CSS para o visual Dark/Cyber (Apenas após o login)
st.markdown(
    """
    <style>
    .stApp { background-color: #0B0F19; color: #E2E8F0; }
    font-family: 'Inter', sans-serif;
    h1, h2, h3 { color: #FFFFFF; font-weight: 800; letter-spacing: -0.5px; }
    div[data-testid="stFrame"] {
        background-color: #161B26;
        border-radius: 12px;
        padding: 20px;
        border: 1px solid #242F41;
    }
    button[data-baseweb="tab"] { font-size: 14px !important; font-weight: 600 !important; color: #94A3B8 !important; }
    button[aria-selected="true"] { color: #38BDF8 !important; border-bottom-color: #38BDF8 !important; }
    .stButton>button {
        background: linear-gradient(135deg, #38BDF8 0%, #0369A1 100%);
        color: white !important;
        border: none;
        padding: 10px 24px;
        font-weight: 700;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(56, 189, 248, 0.2);
    }
    .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(56, 189, 248, 0.4); }
    input, textarea { background-color: #1E293B !important; color: white !important; border: 1px solid #334155 !important; }
    </style>
""",
    unsafe_allow_html=True,
)


# --- CONEXÃO COM O BANCO DE DADOS ---
def conectar():
    conn = sqlite3.connect("estoque_arrojado.db")
    return conn, conn.cursor()


def inicializar_banco():
    conn, cursor = conectar()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS produtos (
        id_produto INTEGER PRIMARY KEY AUTOINCREMENT,
        codigo TEXT UNIQUE NOT NULL,
        nome TEXT NOT NULL,
        descricao TEXT
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS entradas (
        id_entrada INTEGER PRIMARY KEY AUTOINCREMENT,
        data TEXT NOT NULL,
        nota_fiscal TEXT NOT NULL,
        id_produto INTEGER NOT NULL,
        quantidade INTEGER NOT NULL,
        FOREIGN KEY (id_produto) REFERENCES produtos (id_produto)
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS saidas (
        id_saida INTEGER PRIMARY KEY AUTOINCREMENT,
        data TEXT NOT NULL,
        id_produto INTEGER NOT NULL,
        quantidade INTEGER NOT NULL,
        FOREIGN KEY (id_produto) REFERENCES produtos (id_produto)
    )
    """)
    conn.commit()
    conn.close()


inicializar_banco()

# --- BARRA LATERAL ---
with st.sidebar:
    st.markdown("### ⚡ SESSÃO ATIVA")
    st.write(f"Usuário atual: `{st.session_state['usuario_logado']}`")
    st.markdown("---")
    if st.button("Sair (Logoff)", use_container_width=True):
        st.session_state["autenticado"] = False
        st.session_state["usuario_logado"] = ""
        st.rerun()

# --- TOPO BRANDING ARROJADO ---
st.markdown(
    "<h1 style='margin:0; font-size: 2.2rem;'>⚡ NEXTGEN <span style='color: #38BDF8;'>|</span> INVENTORY</h1>"
    "<p style='color: #64748B; margin-top: -5px;'>Gestão de Fluxo de Materiais e Notas Fiscais</p>",
    unsafe_allow_html=True,
)
st.markdown("<br>", unsafe_allow_html=True)

# --- SISTEMA DE ABAS ---
aba_painel, aba_cadastro, aba_entrada, aba_saida = st.tabs([
    "📈 DASHBOARD & SALDOS",
    "📦 NOVO PRODUTO",
    "🧾 ENTRADA DE NOTA FISCAL",
    "🚀 ORDEM DE SAÍDA",
])

# --- ABA 1: DASHBOARD & SALDOS ---
with aba_painel:
    st.subheader("Painel de Posição de Inventário")
    
    conn, cursor = conectar()
    query = """
    SELECT 
        p.codigo AS [SKU], 
        p.nome AS [Produto], 
        p.descricao AS [Descrição],
        COALESCE((SELECT SUM(e.quantidade) FROM entradas e WHERE e.id_produto = p.id_produto), 0) AS [Entradas],
        COALESCE((SELECT SUM(s.quantidade) FROM saidas s WHERE s.id_produto = p.id_produto), 0) AS [Saídas]
    FROM produtos p
    """
    cursor.execute(query)
    dados = cursor.fetchall()
    conn.close()

    if dados:
        import pandas as pd
        import io

        df = pd.DataFrame(dados, columns=["SKU", "Produto", "Descrição", "Entradas", "Saídas"])
        df["Estoque Atual"] = df["Entradas"] - df["Saídas"]

        # Cartões de Métricas no Topo
        m1, m2, m3 = st.columns(3)
        with m1:
            st.metric(label="Total de Itens Cadastrados", value=len(df))
        with m2:
            st.metric(label="Volume Total em Giro", value=int(df["Entradas"].sum()))
        with m3:
            st.metric(label="Produtos com Estoque Crítico (Menos de 3 un.)", value=len(df[df["Estoque Atual"] < 3]))

        st.markdown("<br>", unsafe_allow_html=True)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # FUNÇÃO EXCEL: Transforma a tabela em arquivo de planilha na memória
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Estoque_Atual')
        
        # Cria o botão de download físico do arquivo .xlsx
        st.download_button(
            label="📥 Exportar Relatório para Excel",
            data=buffer.getvalue(),
            file_name=f"relatorio_estoque_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.info("Nenhum item em estoque. Comece cadastrando um produto.")

# --- ABA 2: CADASTRO DE PRODUTOS ---
with aba_cadastro:
    st.subheader("Registrar Novo Item no Sistema")
    with st.form("cadastro_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            cod = st.text_input("Código SKU Interno:")
            nome = st.text_input("Nome Comercial:")
        with c2:
            desc = st.text_area("Ficha / Descrição Técnica:", height=108)

        if st.form_submit_button("Salvar no Catálogo"):
            if not cod or not nome:
                st.warning("SKU e Nome são obrigatórios.")
            else:
                conn, cursor = conectar()
                try:
                    cursor.execute(
                        "INSERT INTO produtos (codigo, nome, descricao) VALUES (?, ?, ?)",
                        (cod.strip(), nome.strip(), desc.strip()),
                    )
                    conn.commit()
                    st.success(f"'{nome}' integrado ao catálogo com sucesso!")
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("Este código SKU já pertence a outro produto.")
                finally:
                    conn.close()

# --- ABA 3: ENTRADA DE NOTA FISCAL ---
with aba_entrada:
    st.subheader("Lançamento de Entrada por Documento Fiscal")
    with st.form("entrada_form", clear_on_submit=True):
        cc1, cc2, cc3 = st.columns(3)
        with cc1:
            nf = st.text_input("Número / Chave da NF-e:")
        with cc2:
            cod_ent = st.text_input("Código SKU do Produto:")
        with cc3:
            qtd_ent = st.number_input("Quantidade da Nota:", min_value=1, step=1)

        if st.form_submit_button("Efetivar Entrada Fiscal"):
            if not nf or not cod_ent:
                st.warning("Preencha todos os campos do documento.")
            else:
                conn, cursor = conectar()
                cursor.execute(
                    "SELECT id_produto FROM produtos WHERE codigo = ?",
                    (cod_ent.strip(),),
                )
                prod = cursor.fetchone()

                if prod:
                    id_produto_encontrado = prod[0]
                    data_atual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    cursor.execute(
                        "INSERT INTO entradas (data, nota_fiscal, id_produto, quantidade) VALUES (?, ?, ?, ?)",
                        (data_atual, nf.strip(), id_produto_encontrado, qtd_ent),
                    )
                    conn.commit()
                    st.success(f"NF {nf} processada. {qtd_ent} unidades adicionadas!")
                    st.rerun()
                else:
                    st.error("SKU não localizado. Faça o cadastro do item primeiro.")
                conn.close()

# --- ABA 4: ORDEM DE SAÍDA ---
with aba_saida:
    st.subheader("Requisição / Baixa Logística de Estoque")
