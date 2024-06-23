from streamlit.components.v1 import html
import streamlit as st
import psycopg2
import time
import uuid
from datetime import datetime
import matplotlib.pyplot as plt
import locale

# Conectar ao banco de dados PostgreSQL
conn = psycopg2.connect(
    host="seulixo-aws.c7my4s6c6mqm.us-east-1.rds.amazonaws.com",
    database="postgres",
    user="postgres",
    password="#SEUlixo321"
)

#cria a tabela caso tenha novo cadastro e ela não exista
def create_empresa(nome_empresa):
    try:
        with conn.cursor() as cur:
            # Verificar se a tabela da empresa já existe
            cur.execute("SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_schema = 'Dados de coleta' AND table_name = %s);", (nome_empresa,))
            exists = cur.fetchone()[0]
            if not exists:
                # Criar a tabela da empresa com colunas para cada tipo de resíduo
                cur.execute(f"""
                    CREATE TABLE IF NOT EXISTS "Dados de coleta".{nome_empresa} (
                        id SERIAL PRIMARY KEY,
                        data DATE NOT NULL,
                        mes INTEGER NOT NULL,
                        ano INTEGER NOT NULL,
                        volume DECIMAL(10, 2) NOT NULL,
                        nome_coletor VARCHAR(100) NOT NULL,
                        plastico INTEGER DEFAULT 0,
                        vidro INTEGER DEFAULT 0,
                        papel INTEGER DEFAULT 0,
                        papelao INTEGER DEFAULT 0,
                        aluminio INTEGER DEFAULT 0,
                        aco INTEGER DEFAULT 0,
                        residuos_eletronicos INTEGER DEFAULT 0,
                        pilhas_baterias INTEGER DEFAULT 0,
                        folhas_galhos INTEGER DEFAULT 0,
                        tetrapak INTEGER DEFAULT 0,
                        pneus INTEGER DEFAULT 0,
                        oleo_cozinha INTEGER DEFAULT 0,
                        cds_dvds INTEGER DEFAULT 0,
                        cartuchos_tinta INTEGER DEFAULT 0,
                        entulho_construcao INTEGER DEFAULT 0,
                        madeira INTEGER DEFAULT 0,
                        paletes INTEGER DEFAULT 0,
                        serragem INTEGER DEFAULT 0,
                        produtos_quimicos INTEGER DEFAULT 0,
                        medicamentos INTEGER DEFAULT 0,
                        lampadas_fluorescentes INTEGER DEFAULT 0,
                        materia_organica INTEGER DEFAULT 0,
                        cobre INTEGER DEFAULT 0
                    );
                """)
                conn.commit()
            else:
                st.warning(f"A tabela para a empresa '{nome_empresa}' já existe.")
    except psycopg2.Error as e:
        st.error(f"Não foi possível criar a tabela para a empresa '{nome_empresa}': {e}")

#adiciona novo usuário na tabela users, podendo ser empresa ou coletor
def add_user(username, email, password, função, empresa):
    try:
        if not email:
            raise ValueError("Por favor, insira um endereço de e-mail.")
        if len(username) < 5:
            raise ValueError("O nome de usuário deve ter no mínimo 5 caracteres.")
        if len(password) < 5:
            raise ValueError("A senha deve ter no mínimo 5 caracteres.")
        if função not in ["Coletor", "Empresa"]:
            raise ValueError("Função inválida. Escolha entre 'Coletor', 'Empresa'.")
        if função == "Empresa" and not empresa:
            raise ValueError("Por favor, insira o nome da empresa.")
        
        with conn.cursor() as cur:
            # Verifica se o nome de usuário ou e-mail já existem na base de dados
            cur.execute("SELECT * FROM users WHERE username = %s OR email = %s;", (username, email))
            existing_user = cur.fetchone()
            if existing_user:
                raise ValueError("Usuário ou e-mail já cadastrados. Por favor, altere ou utilize os já existentes.")
            
            # Verifica se a senha já existe na base de dados
            cur.execute("SELECT * FROM users WHERE password = %s;", (password,))
            existing_password = cur.fetchone()
            if existing_password:
                raise ValueError("Por favor, escolha uma senha mais segura.")
            
            # Convertendo a empresa para minúsculo se a função for "Empresa"
            empresa_lower = empresa.lower() if função == "Empresa" else None
            
            cur.execute("INSERT INTO users (username, email, password, função, empresa) VALUES (%s, %s, %s, %s, %s);",
                        (username, email, password, função.capitalize(), empresa_lower))
            
            # Verifica se já existe uma tabela com o nome da empresa em "Dados de coleta"
            if função.lower() == "empresa":
                cur.execute("SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_schema = 'Dados de coleta' AND table_name = %s);", (empresa_lower,))
                table_exists = cur.fetchone()[0]
                if not table_exists:
                    # Se a tabela não existe, cria ela
                    create_empresa(empresa_lower)
        conn.commit()
    except ValueError as e:
        st.error(str(e))
    except Exception as e:
        st.error("Erro ao cadastrar usuário. Por favor, tente novamente mais tarde.")

#para saber se o usuário ta online ou não
def on_session_state_changed():
    if st.session_state.is_session_state_changed:
        if st.session_state.is_session_state_changed:
            # Atualiza o status de login do usuário para False quando a sessão é encerrada
            update_user_login_status(st.session_state.username, False)

# Define a função on_session_state_changed como callback
st.session_state.on_session_state_changed = on_session_state_changed

# Função para atualizar o status de login do usuário
def update_user_login_status(username, is_logged_in):
    try:
        with conn.cursor() as cur:
            cur.execute("UPDATE users SET acesso = %s WHERE username = %s;", (is_logged_in, username))
        conn.commit()
    except Exception as e:
        st.error("Erro ao atualizar o status de login do usuário.")

# Função para verificar se o usuário existe no banco de dados usando nome de usuário ou e-mail
def check_user(username_or_email, password):
    with conn.cursor() as cur:
        # Verificar se o nome de usuário ou o e-mail corresponde a um registro no banco de dados
        cur.execute("SELECT * FROM users WHERE username = %s OR email = %s;", (username_or_email, username_or_email))
        return cur.fetchone() is not None

def register():
    st.markdown("<h1 style='color: #38b6ff;'>Cadastro de Usuário</h1>", unsafe_allow_html=True)
    username = st.text_input("Nome de Usuário").lower()
    email = st.text_input("Endereço de E-mail")
    password = st.text_input("Senha", type="password")
    função = st.selectbox("Função", ["Coletor", "Empresa"])
    empresa = None
    if função == "Empresa":
        empresa = st.text_input("Nome da Empresa").lower()

    if st.button("Cadastrar"):
        add_user(username, email, password, função, empresa)
# Chamar a função register para exibir o formulário de cadastro na aba 2
register()

#ve se a tabela já existe e se tiver vai add os dados e se não tiver vai criar tabela com base na função create_empresa
def check_table_existence(senha_empresa, username, dia, mes, ano, volume):
    try:
        # Abrir um cursor para executar consultas SQL
        with conn.cursor() as cur:
            # Consulta SQL para verificar se a senha existe na tabela users e obter o ID e a empresa
            cur.execute("SELECT id, empresa FROM public.users WHERE password = %s;", (senha_empresa,))
            empresa_info = cur.fetchone()
            if empresa_info:
                user_id, empresa = empresa_info
                
                # Verificar a existência da tabela
                cur.execute("SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_schema = 'Dados de coleta' AND table_name = %s);", (empresa,))
                table_exists = cur.fetchone()[0]
                if table_exists:
                    # Insere os dados na tabela existente
                    cur.execute(f"""
                        INSERT INTO "Dados de coleta".{empresa} (data, mes, ano, volume, nome_coletor)
                        VALUES (%s, %s, %s, %s, %s);
                    """, (f'{ano}-{mes}-{dia}', mes, ano, volume, username))
                    conn.commit()
                    return f"Dados inseridos na tabela '{empresa}'."
                else:
                    return f"A tabela '{empresa}' não existe."
            else:
                return "Senha da empresa não encontrada."
    except psycopg2.Error as e:
        return f"Erro ao conectar ao banco de dados: {e}"

# Adiciona a imagem de plano de fundo e o estilo para ocupar toda a tela
st.markdown(
    f"""
    <style>
    .stApp {{
        background: url("https://lh3.googleusercontent.com/pw/AP1GczMmpHRnbB_1-qEmLsLsuMQgL7-D3V91nrCKM_WlU4cA4yrPKO2vP8Pj3I_MssP3dlsv7HSLLwDh73kltLTLRm7aX3B5DALLaFlMNMXoCjPa8jhLFWw1vUfJcxqKCo5DK7gawaB45eueEkyEVUmizvVn=w1366-h768-s-no-gm?authuser=0");
        background-size: cover;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }}
    </style>
    """,
    unsafe_allow_html=True
)
collection_form()



