
import streamlit as st
from utils.banco import (
    criar_banco,
    buscar_usuario,
    contar_notas,
    contar_usuarios
)

from utils.seguranca import verificar_senha

st.set_page_config(
    page_title="Sistema de Qualidade",
    page_icon="📋",
    layout="wide"
)

# ==========================================
# BANCO
# ==========================================

criar_banco()

# ==========================================
# SESSÃO
# ==========================================

if "logado" not in st.session_state:
    st.session_state.logado = False

if "usuario" not in st.session_state:
    st.session_state.usuario = ""

if "perfil" not in st.session_state:
    st.session_state.perfil = ""

if "nome" not in st.session_state:
    st.session_state.nome = ""

# ==========================================
# LOGIN
# ==========================================

def tela_login():

    col1, col2, col3 = st.columns([1,2,1])

    with col2:

        st.title("📋 Sistema de Qualidade")

        st.markdown("---")

        usuario = st.text_input(
            "Usuário",
            placeholder="Digite seu usuário"
        )

        senha = st.text_input(
            "Senha",
            type="password",
            placeholder="Digite sua senha"
        )

        entrar = st.button(
            "Entrar",
            use_container_width=True
        )

        if entrar:

            if not usuario or not senha:
                st.error("Preencha usuário e senha")
                return

            dados = buscar_usuario(usuario)

            if not dados:
                st.error("Usuário não encontrado")
                return

            senha_ok = verificar_senha(
                senha,
                dados["senha"]
            )

            if not senha_ok:
                st.error("Senha inválida")
                return

            st.session_state.logado = True
            st.session_state.usuario = dados["usuario"]
            st.session_state.perfil = dados["perfil"]
            st.session_state.nome = dados["nome"]

            st.rerun()

# ==========================================
# LOGOUT
# ==========================================

def logout():

    st.session_state.logado = False
    st.session_state.usuario = ""
    st.session_state.perfil = ""
    st.session_state.nome = ""

    st.rerun()

# ==========================================
# DASHBOARD
# ==========================================

def dashboard():

    st.title("📊 Dashboard")

    c1, c2 = st.columns(2)

    with c1:
        st.metric(
            "Total de Notas",
            contar_notas()
        )

    with c2:
        st.metric(
            "Total de Usuários",
            contar_usuarios()
        )

    st.markdown("---")

    st.subheader("Bem-vindo")

    st.info(
        f"Usuário logado: "
        f"{st.session_state.nome}"
    )

    st.write(
        f"Perfil: {st.session_state.perfil}"
    )

# ==========================================
# MENU LATERAL
# ==========================================

def menu_lateral():

    with st.sidebar:

        st.title("📋 Qualidade")

        st.success(
            f"Usuário: "
            f"{st.session_state.usuario}"
        )

        st.write(
            f"Perfil: "
            f"{st.session_state.perfil}"
        )

        st.markdown("---")

        paginas = [
            "Dashboard",
            "Notas"
        ]

        if st.session_state.perfil == "MASTER":
            paginas.append("Usuários")

        escolha = st.radio(
            "Menu",
            paginas
        )

        st.markdown("---")

        if st.button(
            "Sair",
            use_container_width=True
        ):
            logout()

        return escolha

# ==========================================
# TELA NOTAS
# ==========================================

def tela_notas():

    st.title("📦 Notas Fiscais")

    st.info(
        "A página completa de notas "
        "será criada no arquivo "
        "pages/notas.py"
    )

# ==========================================
# TELA USUÁRIOS
# ==========================================

def tela_usuarios():

    st.title("👥 Usuários")

    st.info(
        "A página completa de usuários "
        "será criada no arquivo "
        "pages/usuarios.py"
    )

# ==========================================
# APP
# ==========================================

if not st.session_state.logado:

    tela_login()

else:

    opcao = menu_lateral()

    if opcao == "Dashboard":
        dashboard()

    elif opcao == "Notas":
        tela_notas()

    elif opcao == "Usuários":
        tela_usuarios()
```

