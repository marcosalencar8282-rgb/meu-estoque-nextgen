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

# Credenciais de acesso
USUARIO_CORRETO = "admin"
SENHA_CORRETA = "1234"


def realizar_login():
    if (
        st.session_state["usuario_input"] == USUARIO_CORRETO
        and st.session_state["senha_input"] == SENHA_CORRETA
    ):
        st.session_state["autenticado"] = True
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

# --- TOPO BRANDING ARROJADO ---
col_logo, col_titulo, col_logout = st.columns([1, 4, 1])
with col_titulo:
    st.markdown(
        "<h1 style='margin:0; font-size: 2.2rem;'>⚡ NEXTGEN <span style='color: #38BDF8;'>|</span> INVENTORY</h1>"
        "<p style='color: #64748B; margin-top: -5px;'>Gestão de Fluxo de Materials e Notas Fiscais</p>",
        unsafe_allow_html=True,
    )

with col_logout:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Sair (Logoff)"):
        st.session_state["autenticado"] = False
        st.rerun()

# --- SISTEMA DE ABAS ---
aba_painel, aba_cadastro, aba_entrada, aba_saida = st.tabs([
    "📈 DASHBOARD & SALDOS",
    "📦 NOVO PRODUTO",
    "🧾 ENTRADA DE NOTA FISCAL",
    "🚀 ORDEM DE SAÍDA",
])

# --- ABA 1: DASHBOARD & SALDOS ---
with aba_painel:
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

        df = pd.DataFrame(dados, columns=[
            "SKU",
            "Produto",
            "Descrição",
            "Entradas",
            "Saídas",
        ])
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
        st.subheader("Painel de Posição de Inventário")
        st.dataframe(df, use_container_width=True, hide_index=True)
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
                    data_atual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    cursor.execute(
                        "INSERT INTO entradas (data, nota_fiscal, id_produto, quantidade) VALUES (?, ?, ?, ?)",
                        (data_atual, nf.strip(), prod[0], qtd_ent),
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
    with st.form("saida_form", clear_on_submit=True):
        cx1, cx2 = st.columns(2)
        with cx1:
            cod_sai = st.text_input("Código SKU para Baixa:")
        with cx2:
            qtd_sai = st.number_input("Quantidade Requisitada:", min_value=1, step=1)

        if st.form_submit_button("Confirmar Saída"):
            if not cod_sai:
                st.warning("Insira o código SKU.")
            else:
                conn, cursor = conectar()
                cursor.execute(
                    "SELECT id_produto FROM produtos WHERE codigo = ?",
                    (cod_sai.strip(),),
                )
                prod = cursor.fetchone()

                if prod:
                    id_p = prod[0]
                    # Validando o saldo real antes de retirar
                    cursor.execute(
                        "SELECT COALESCE(SUM(quantidade), 0) FROM entradas WHERE id_produto = ?",
                        (id_p,),
                    )
                    ent = cursor.fetchone()[0]
                    
                    cursor.execute(
