import sqlite3
from datetime import datetime
import streamlit as st

# Configuração da página com visual moderno e arrojado
st.set_page_config(
    page_title="NextGen | Controle de Estoque", layout="wide", page_icon="⚡"
)

# Estilização CSS para um visual Dark/Cyber Arrojado (Estilo SaaS Moderno)
st.markdown(
    """
    <style>
    /* Fundo geral e fontes */
    .stApp { background-color: #0B0F19; color: #E2E8F0; }
    font-family: 'Inter', sans-serif;
    
    /* Customização dos Títulos */
    h1, h2, h3 { color: #FFFFFF; font-weight: 800; letter-spacing: -0.5px; }
    
    /* Cartões / Containers */
    div[data-testid="stFrame"] {
        background-color: #161B26;
        border-radius: 12px;
        padding: 20px;
        border: 1px solid #242F41;
    }
    
    /* Abas superiores */
    button[data-baseweb="tab"] {
        font-size: 14px !important;
        font-weight: 600 !important;
        color: #94A3B8 !important;
        background-color: transparent !important;
    }
    button[aria-selected="true"] {
        color: #38BDF8 !important; /* Azul Neon */
        border-bottom-color: #38BDF8 !important;
    }
    
    /* Botões Arrojados */
    .stButton>button {
        background: linear-gradient(135deg, #38BDF8 0%, #0369A1 100%);
        color: white !important;
        border: none;
        padding: 10px 24px;
        font-weight: 700;
        border-radius: 8px;
        transition: all 0.3s ease;
        box-shadow: 0 4px 12px rgba(56, 189, 248, 0.2);
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(56, 189, 248, 0.4);
    }
    
    /* Inputs */
    input, textarea {
        background-color: #1E293B !important;
        color: white !important;
        border: 1px solid #334155 !important;
        border-radius: 8px !important;
    }
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
col_logo, col_titulo = st.columns([1, 11])
with col_titulo:
    st.markdown(
        "<h1 style='margin:0; font-size: 2.2rem;'>⚡ NEXTGEN <span style='color: #38BDF8;'>|</span> INVENTORY</h1>"
        "<p style='color: #64748B; margin-top: -5px;'>Gestão de Fluxo de Materiais e Notas Fiscais</p>",
        unsafe_allow_html=True,
    )

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
        # Exibe tabela interativa com busca integrada
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
                        "SELECT COALESCE(SUM(quantidade), 0) FROM saidas WHERE id_produto = ?",
                        (id_p,),
                    )
                    sai = cursor.fetchone()[0]
                    saldo = ent - sai

                    if qtd_sai > saldo:
                        st.error(f"Operação Recusada! Saldo disponível insuficiente ({saldo} unidades).")
                    else:
                        data_atual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        cursor.execute(
                            "INSERT INTO saidas (data, id_produto, quantidade) VALUES (?, ?, ?)",
                            (data_atual, id_p, qtd_sai),
                        )
                        conn.commit()
                        st.success(f"Baixa efetuada! {qtd_sai} unidades retiradas do sistema.")
                        st.rerun()
                else:
                    st.error("Produto não localizado no sistema.")
                conn.close()
