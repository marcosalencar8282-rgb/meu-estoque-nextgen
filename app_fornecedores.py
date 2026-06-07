import streamlit as st
import sqlite3
import xml.etree.ElementTree as ET
from datetime import datetime
import pandas as pd

# CONFIGURAÇÃO DE INTERFACE
st.set_page_config(page_title="Recebimento & Devolução", page_icon="🏢", layout="wide")

def conectar_bd():
    conn = sqlite3.connect('controle_fornecedores.db')
    cursor = conn.cursor()
    # Criar tabelas adaptadas com foco no Fornecedor
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS nfe_recebimento (
            id_recebimento INTEGER PRIMARY KEY AUTOINCREMENT,
            chave_acesso TEXT UNIQUE NOT NULL,
            numero_nota INTEGER NOT NULL,
            cnpj_fornecedor TEXT NOT NULL,
            nome_fornecedor TEXT NOT NULL,
            data_emissao TEXT NOT NULL,
            data_recebimento TEXT NOT NULL,
            valor_total REAL NOT NULL,
            status TEXT DEFAULT 'Recebido'
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS nfe_devolucao_fornecedor (
            id_devolucao INTEGER PRIMARY KEY AUTOINCREMENT,
            id_recebimento_origem INTEGER NOT NULL,
            chave_devolucao TEXT UNIQUE NOT NULL,
            numero_nota_devolucao INTEGER NOT NULL,
            motivo_devolucao TEXT NOT NULL,
            data_envio TEXT NOT NULL,
            FOREIGN KEY (id_recebimento_origem) REFERENCES nfe_recebimento (id_recebimento)
        )
    ''')
    conn.commit()
    return conn

# PROCESSADOR AUTOMÁTICO DE XML DO FORNECEDOR
def processar_xml_fornecedor(arquivo_xml):
    ns = {'ns': 'http://portalfiscal.inf.br'}
    try:
        tree = ET.parse(arquivo_xml)
        root = tree.getroot()

        infNFe = root.find('.//ns:infNFe', ns)
        chave_acesso = infNFe.attrib['Id'][3:] if infNFe is not None else None
        
        numero_nota = root.find('.//ns:ide/ns:nNF', ns).text
        cnpj_fornecedor = root.find('.//ns:emit/ns:CNPJ', ns).text
        nome_fornecedor = root.find('.//ns:emit/ns:xNome', ns).text
        data_emissao = root.find('.//ns:ide/ns:dhEmi', ns).text[:10]
        valor_total = float(root.find('.//ns:total/ns:ICMSTot/ns:vNF', ns).text)
        data_atual = datetime.now().strftime('%Y-%m-%d')

        conn = conectar_bd()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO nfe_recebimento (chave_acesso, numero_nota, cnpj_fornecedor, nome_fornecedor, data_emissao, data_recebimento, valor_total)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (chave_acesso, numero_nota, cnpj_fornecedor, nome_fornecedor, data_emissao, data_atual, valor_total))
        
        conn.commit()
        conn.close()
        return True, f"Nota Fiscal nº {numero_nota} do fornecedor '{nome_fornecedor}' recebida com sucesso!"
    except sqlite3.IntegrityError:
        return False, "Esta Nota Fiscal já foi importada no sistema anteriormente."
    except Exception as e:
        return False, f"Falha na leitura do XML do fornecedor: {str(e)}"

# REGISTRO DE DEVOLUÇÃO PARA FORNECEDOR
def emitir_devolucao_fornecedor(id_origem, num_nota_origem, chave_dev, num_dev, motivo):
    conn = conectar_bd()
    cursor = conn.cursor()
    data_atual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    try:
        cursor.execute('''
            INSERT INTO nfe_devolucao_fornecedor (id_recebimento_origem, chave_devolucao, numero_nota_devolucao, motivo_devolucao, data_envio)
            VALUES (?, ?, ?, ?, ?)
        ''', (id_origem, chave_dev, num_dev, motivo, data_atual))

        cursor.execute('''
            UPDATE nfe_recebimento SET status = 'Devolvida ao Fornecedor' WHERE id_recebimento = ?
        ''', (id_origem,))

        conn.commit()
        conn.close()
        return True, f"Devolução referente à Nota nº {num_nota_origem} concluída com sucesso!"
    except sqlite3.IntegrityError:
        return False, "A chave ou número da nota de devolução já existe no histórico."
    except Exception as e:
        return False, f"Erro operacional: {str(e)}"

# CONSTRUÇÃO DA TELA WEB
st.title("🏭 Portal Fiscal: Recebimento e Devolução para Fornecedores")

aba_painel, aba_novo_recebimento, aba_nova_devolucao = st.tabs([
    "📋 Painel de Controle", 
    "📥 Receber Nota de Fornecedor", 
    "↩️ Devolver para Fornecedor"
])

# ---- ABA 1: PAINEL DE CONTROLE ----
with aba_painel:
    st.subheader("Gerenciamento de Fluxo de Mercadorias")
    
    conn = conectar_bd()
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**📦 Notas de Recebimento (Entrada)**")
        df_rec = pd.read_sql_query("SELECT numero_nota AS [Nº Nota], nome_fornecedor AS [Fornecedor], data_recebimento AS [Data Rec.], valor_total AS [Valor R$], status AS [Status] FROM nfe_recebimento", conn)
        st.dataframe(df_rec, use_container_width=True, hide_index=True)
        
    with col2:
        st.markdown("**🚚 Notas de Devolução Despachadas**")
        df_dev = pd.read_sql_query('''
            SELECT d.numero_nota_devolucao AS [Nº Nota Dev], r.nome_fornecedor AS [Fornecedor Destinatário], 
                   d.data_envio AS [Data Envio], d.motivo_devolucao AS [Motivo]
            FROM nfe_devolucao_fornecedor d
            JOIN nfe_recebimento r ON d.id_recebimento_origem = r.id_recebimento
        ''', conn)
        st.dataframe(df_dev, use_container_width=True, hide_index=True)
    conn.close()

# ---- ABA 2: RECEBER NOTA DE FORNECEDOR ----
with aba_novo_recebimento:
    st.subheader("Dar Entrada em Mercadoria por XML")
    st.info("Faça o upload do arquivo XML enviado pelo seu fornecedor para validar os dados.")
    
    xml_fornecedor = st.file_uploader("Selecione o arquivo XML da NF-e", type=["xml"], key="upload_forn")
    
    if xml_fornecedor is not None:
        if st.button("Confirmar Entrada no Estoque"):
            sucesso, msg = processar_xml_fornecedor(xml_fornecedor)
            if sucesso:
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)

# ---- ABA 3: DEVOLVER PARA FORNECEDOR ----
with aba_nova_devolucao:
    st.subheader("Emitir Devolução de Mercadoria")
    
    conn = conectar_bd()
    notas_ativas = pd.read_sql_query("SELECT id_recebimento, numero_nota, nome_fornecedor FROM nfe_recebimento WHERE status = 'Recebido'", conn)
    conn.close()
    
    if not notas_ativas.empty:
        opcoes = {f"Nota {row['numero_nota']} - Fornecedor: {row['nome_fornecedor']}": row for _, row in notas_ativas.iterrows()}
        selecionada = st.selectbox("Selecione qual nota de recebimento será devolvida:", list(opcoes.keys()))
        
        dados_origem = opcoes[selecionada]
        
        with st.form("form_devolucao_forn"):
            col_n, col_c = st.columns([1, 3])
            with col_n:
                num_nota_dev = st.number_input("Nº da Nota de Devolução:", min_value=1, step=1)
            with col_c:
                chave_dev = st.text_input("Chave de Acesso da Devolução (44 dígitos):", max_chars=44)
                
            motivo = st.text_area("Descreva o motivo da devolução para o fornecedor (Ex: defeito, avaria no transporte, pedido incorreto):")
            
            botao_enviar = st.form_submit_button("Registrar Saída da Devolução")
            
            if botao_enviar:
                if len(chave_dev) != 44 or not chave_dev.isdigit():
                    st.error("A chave de acesso precisa conter exatamente 44 caracteres numéricos.")
                elif not motivo.strip():
                    st.error("É obrigatório preencher o motivo da devolução.")
                else:
                    sucesso, msg = emitir_devolucao_fornecedor(
                        dados_origem['id_recebimento'],
                        dados_origem['numero_nota'],
                        chave_dev,
                        num_nota_dev,
                        motivo
                    )
                    if sucesso:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
    else:
        st.warning("Não existem mercadorias em estoque disponíveis para devolução no momento.")
