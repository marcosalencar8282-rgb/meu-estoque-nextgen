import streamlit as st
import sqlite3
import hashlib
import pandas as pd

st.set_page_config(page_title="Sistema de Qualidade", layout="wide")

def conectar():
    return sqlite3.connect("qualidade.db")

def criar_banco():
    conn = conectar()
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS usuarios(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        usuario TEXT UNIQUE,
        senha TEXT,
        perfil TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS notas(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        numero TEXT,
        fornecedor TEXT,
        produto TEXT,
        quantidade INTEGER
    )
    """)

    senha_master = hashlib.sha256("master123".encode()).hexdigest()

    c.execute("""
    INSERT OR IGNORE INTO usuarios
    (id,nome,usuario,senha,perfil)
    VALUES
    (1,'Administrador Master','master',?,'MASTER')
    """,(senha_master,))

    conn.commit()
    conn.close()

criar_banco()

def criptografar(texto):
    return hashlib.sha256(texto.encode()).hexdigest()

if "logado" not in st.session_state:
    st.session_state.logado = False

if not st.session_state.logado:

    st.title("Login")

    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")

    if st.button("Entrar"):

        conn = conectar()
        c = conn.cursor()

        c.execute(
            "SELECT * FROM usuarios WHERE usuario=?",
            (usuario,)
        )

        user = c.fetchone()
        conn.close()

        if user and user[3] == criptografar(senha):
            st.session_state.logado = True
            st.session_state.usuario = user[2]
            st.session_state.perfil = user[4]
            st.rerun()
        else:
            st.error("Usuário ou senha inválidos")

else:

    st.sidebar.success(
        f"Logado: {st.session_state.usuario}"
    )

    menu = st.sidebar.selectbox(
        "Menu",
        [
            "Dashboard",
            "Notas",
            "Cadastrar Nota",
            "Usuários"
        ]
    )

    if menu == "Dashboard":
        st.title("Sistema de Qualidade")

    elif menu == "Cadastrar Nota":

        st.title("Nova Nota")

        numero = st.text_input("Número")

        fornecedor = st.text_input("Fornecedor")

        produto = st.text_input("Produto")

        quantidade = st.number_input(
            "Quantidade",
            min_value=1
        )

        if st.button("Salvar"):

            conn = conectar()
            c = conn.cursor()

            c.execute("""
            INSERT INTO notas
            (numero,fornecedor,produto,quantidade)
            VALUES(?,?,?,?)
            """,
            (
                numero,
                fornecedor,
                produto,
                quantidade
            ))

            conn.commit()
            conn.close()

            st.success("Nota cadastrada")

    elif menu == "Notas":

        conn = conectar()

        df = pd.read_sql_query(
            "SELECT * FROM notas",
            conn
        )

        conn.close()

        st.dataframe(df)

    elif menu == "Usuários":

        if st.session_state.perfil != "MASTER":
            st.error("Acesso negado")
            st.stop()

        st.title("Gerenciamento de Usuários")

        nome = st.text_input("Nome")

        usuario = st.text_input("Usuário Novo")

        senha = st.text_input(
            "Senha",
            type="password"
        )

        perfil = st.selectbox(
            "Perfil",
            ["ADMIN","USUARIO"]
        )

        if st.button("Cadastrar Usuário"):

            try:

                conn = conectar()
                c = conn.cursor()

                c.execute("""
                INSERT INTO usuarios
                (nome,usuario,senha,perfil)
                VALUES(?,?,?,?)
                """,
                (
                    nome,
                    usuario,
                    criptografar(senha),
                    perfil
                ))

                conn.commit()
                conn.close()

                st.success("Usuário criado")

            except:
                st.error("Usuário já existe")

        conn = conectar()

        df = pd.read_sql_query(
            "SELECT id,nome,usuario,perfil FROM usuarios",
            conn
        )

        conn.close()

        st.dataframe(df)

    if st.sidebar.button("Sair"):
        st.session_state.clear()
        st.rerun()
